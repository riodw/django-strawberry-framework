# Review - `docs/spec-030-connection_field-0_0_9.md`

## Findings

### P1 - The optimizer plan cannot ride the existing root-gated hook as written

`docs/spec-030-connection_field-0_0_9.md #"Decision 11"` says a root
`DjangoConnectionField` will be planned by the existing flat
`DjangoOptimizerExtension` with no source change because the optimizer sees the
pre-slice queryset. That is not how the current Strawberry pipeline works.

`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve`
calls `_next(...)` and then optimizes only if the returned value is a Django
`QuerySet` (`DjangoOptimizerExtension._optimize`). Strawberry's
`relay.connection()` installs `ConnectionExtension`; its sync/async resolvers
call the user resolver, then immediately call
`connection_type.resolve_connection(...)` and return a connection object. The
schema middleware therefore sees the post-connection result, not the pre-slice
queryset.

This means Slice 3's "no source change" acceptance test is currently specified
to pass through a path that cannot optimize. The root-cause fix is to make
`DjangoConnectionField` own an optimizer cooperation point before Strawberry's
connection slicing, probably by extracting the plan-application logic from
`DjangoOptimizerExtension._optimize` into a reusable internal helper and calling
that helper from a connection field extension that runs inside
`ConnectionExtension`. That helper should take the known `target_type` /
`target_model` directly instead of trying to infer the model from
`info.return_type`, because the root return type is the connection type, not the
node type.

The spec should revise Decision 11, the implementation table, and the DoD:
Slice 3 does need source work unless the connection field's earlier slices
already introduce the custom field extension/helper.

### P1 - A single generic `DjangoConnection[T]` cannot conditionally omit `totalCount`

`docs/spec-030-connection_field-0_0_9.md #"DjangoConnection[T] is a
ListConnection subclass"` requires one generic `DjangoConnection[NodeType]`
subclass whose `totalCount` field is absent unless the wrapped type opts in via
`Meta.connection = {"total_count": True}`. A static Strawberry class cannot make
one field appear or disappear per generic specialization. If `total_count` is
declared on the `DjangoConnection` class, every `DjangoConnection[T]`
specialization exposes it.

The proposed `DjangoConnectionField(..., total_count=...)` override makes this
harder: two fields over the same node type could require different GraphQL
connection shapes, so the spec also needs a naming and caching rule for the
generated connection types.

Root-cause fix: generate concrete connection classes per target shape, for
example a cached `GenreTypeConnection` without `totalCount` and a distinct
cached total-count variant when enabled. Alternatively, drop the per-field
override and make the option strictly per type, but the implementation still
needs conditional concrete classes or a different public contract where
`totalCount` is always in the schema and only count execution is opt-in.

This also means `Meta.connection` needs to be stored on
`DjangoTypeDefinition`, not merely validated on `Meta`; the implementation plan
currently omits `django_strawberry_framework/types/definition.py`.

### P1 - Strawberry 0.316.0 does not reject `first` plus `last`

Multiple sections say Strawberry's `ListConnection` owns a mutually-exclusive
`first` + `last` guard and raises a typed error:

- `docs/spec-030-connection_field-0_0_9.md #"first + last mutually-exclusive"`
- `docs/spec-030-connection_field-0_0_9.md #"Both first: and last:"`
- `docs/spec-030-connection_field-0_0_9.md #"test_genre_connection_first_and_last_rejected"`

The installed Strawberry `0.316.0` source does not contain that guard.
`strawberry.relay.types::SliceMetadata.from_arguments` applies `first` and then
`last`, producing a slice window. It validates negative values and
`max_results`, but not mutual exclusivity.

If this package wants `first` + `last` to be illegal, `DjangoConnectionField`
must implement that validation before delegating to Strawberry. If not, remove
the guard claim and the live HTTP rejection test. Do not leave the spec relying
on upstream behavior that is absent in the locked dependency.

### P1 - Sidecar argument generation needs an explicit Strawberry mechanism

Decision 6 says `filter:` and `orderBy:` are derived by reusing
`filter_input_type(...)` and `order_input_type(...)`. Those helpers return
annotations and write orphan-validation ledgers; they do not add arguments to a
field by themselves.

The spec needs to say how the generated field receives those arguments. Viable
routes are:

- build a resolver with a synthesized `__signature__` containing `filter` and
  `order_by` parameters with the helper annotations;
- or install a custom `FieldExtension.apply(...)` that appends
  `StrawberryArgument`s before Strawberry builds the GraphQL field, then pops
  those values in the extension resolver before applying filter/order.

This is load-bearing because `ConnectionExtension.resolve(...)` forwards
non-pagination `**kwargs` to the inner resolver. Without a concrete argument
injection strategy, the advertised SDL cannot be produced and runtime input
values have nowhere reliable to land.

### P2 - `totalCount` should be selection-gated and carried on the connection instance

The spec says the field resolver computes `.count()` / `.acount()` and stashes
the value on `info.context` when `Meta.connection` opts in. That conflates two
separate choices:

- schema opt-in: whether `totalCount` exists;
- query selection: whether this particular request asked for it.

Counting on every query against a total-count-enabled type is still an
avoidable count query when the client selects only `edges` or `pageInfo`.
`totalCount` should execute only when the field is selected. The test plan
should include a query that omits `totalCount` and asserts no count query runs.

The context stash is also the wrong primary data path. A connection result is
already a per-field, per-alias object; attach the captured count to that
connection instance, or override the generated connection class's
`resolve_connection` to set a private instance attribute. Add a two-alias test
with different filters and different counts; that test should not depend on
path-string keying in `info.context`.

### P2 - Cursor pagination needs a deterministic default ordering

The default resolver path starts from `_initial_queryset(target_type)`, which is
`model._default_manager.all()`. For models without `Meta.ordering`, that is an
unordered queryset. Offset cursors over unordered SQL results are not a
defensible pagination contract.

The spec should define the default ordering rule before slicing. A conservative
shape is: after visibility/filter/order composition, if the queryset is still
unordered, apply `order_by(model._meta.pk.attname)`. If `orderBy` is supplied,
preserve it; if model `Meta.ordering` exists, preserve it. Add tests for the
default path and for a consumer resolver returning an already ordered queryset.

This does not solve stable cursors across inserts/deletes, which the spec
rightly defers, but it does prevent nondeterministic pages from an unordered
database plan.

### P2 - Consumer resolver behavior is underspecified

`DjangoConnectionField` has a `resolver=` escape hatch, but the spec describes
the pipeline as if the resolved value is always a queryset. Existing
`DjangoListField` behavior allows a consumer resolver to return a `Manager`,
`QuerySet`, Python list, or generator; only `Manager` / `QuerySet` get
`get_queryset` post-processing.

For a connection field, this matters because filter/order sidecars can only
apply to querysets. The spec should define the contract explicitly:

- `Manager` is coerced to `QuerySet`;
- `QuerySet` receives visibility/filter/order/optimizer/pagination;
- non-queryset iterables may be paginated only when no `filter:` / `orderBy:`
  input is supplied;
- supplying sidecar inputs with a non-queryset iterable raises a clear GraphQL
  error or configuration error.

Add tests for all four cases. Without this, a custom resolver can silently skip
the advertised Meta-driven behavior.

### P2 - The public export gate conflicts with the live example slice

Decision 14 promotes `DjangoConnectionField` / `DjangoConnection` to
`django_strawberry_framework.__init__` only in Slice 5, after Slice 4's live
HTTP example usage. But the user-facing API section imports both symbols from
the top-level package, and the fakeshop example is consumer-facing usage.

Either promote the symbols before the live fakeshop field is added, or state
that Slice 4 imports from `django_strawberry_framework.connection` temporarily
and Slice 5 rewrites it to the public import. The first option is cleaner:
public export plus live usage should land in the same functional slice that
proves the public surface.

### P3 - `filters=` / `order=` overrides are inconsistent across the spec

The Slice 2 checklist includes
`DjangoConnectionField(target_type, *, filters=..., order=..., total_count=...)`,
Decision 5's signature includes only `total_count=...`, and Decision 6 / Risks
say `filters=` / `order=` are "MAY" be offered. That leaves the API undecided
inside a spec that otherwise presents itself as implementation-ready.

Pick one. My recommendation is to drop `filters=` / `order=` from `0.0.9` and
ship the Meta-only derivation first. If overrides are kept, specify their
validation, precedence over `Meta.*_class`, orphan-ledger behavior, generated
input names, and tests.

### P3 - The opaque-cursor deletion wording overpromises

`docs/spec-030-connection_field-0_0_9.md #"after: cursor for a row that no
longer exists"` says an offset cursor "falls through to the next existing row."
That is too strong. Offset cursors encode a position, not row identity; deletes
or inserts before that position can skip or duplicate rows. `BACKLOG.md` already
describes this as the reason `Meta.cursor_field` exists later.

Revise the edge case to say the query does not error, but offset cursor
stability under concurrent inserts/deletes is explicitly not guaranteed until
the stable-cursor work ships.

### P3 - Spec hygiene issues should be cleaned before build starts

- The glossary-reference bullet for `ConfigurationError` includes the
  mutually-exclusive `first` + `last` case even though that is a query runtime
  validation path, not a type/field construction error.
- The bottom link block defines `glossary-metaconnection` while the body says
  `Meta.connection` intentionally has no glossary heading yet. The companion
  CSV is correct and `scripts/check_spec_glossary.py` passes, but the unused
  broken link definition should be removed until the heading exists.
- The spec says it grants CHANGELOG edit permission. That is fine as process
  prose, but implementation tasks should still mention the CHANGELOG edit
  explicitly in the maintainer prompt for Slice 5 so an agent is not asked to
  infer permission from a standing document.

## What looks solid

The scope boundary against `031` / `032` / `033` is good, and the
visibility -> filter -> order -> slice composition order is the right contract.
The fakeshop `GenreType` is also the right live-HTTP host: it is already
Relay-node-shaped and carries both sidecars, so the acceptance test can focus on
the connection field rather than new model setup.

## Validation run during review

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-030-connection_field-0_0_9.md`
- Strawberry source inspection for `relay.connection`,
  `ConnectionExtension.resolve`, `ListConnection.resolve_connection`, and
  `SliceMetadata.from_arguments`.

I did not run pytest.
