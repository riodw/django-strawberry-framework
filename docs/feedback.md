# Review — `docs/spec-035-optimizer_hardening-0_0_10.md`

Deep pass after staging `TODO(spec-035 Slice N)` anchors across the optimizer,
tests, and docs. The spec is directionally good for G2, but G3 currently rests on
a production-reachability claim that does not match the live optimizer entry path.

## Findings

### P1 — G3's claimed production trigger is not optimized today

The spec says the G3 failure mode is consumer-constructible today via an
`@strawberry.interface` implemented by multiple `DjangoType`s and exposed as a
queryset-returning field, and that the optimizer would mis-walk that abstract
selection. Current code does not appear to reach the walker for that shape.

`django_strawberry_framework/optimizer/extension.py::_resolve_model_from_return_type`
unwraps `info.return_type`, looks up the Strawberry definition by GraphQL type
name, then calls `registry.model_for_type(origin)`. For an interface or union
origin, `origin` is not a registered `DjangoType`, so `model_for_type(...)`
returns `None` and `_optimize` passes the queryset through unchanged. That means
the sibling-concrete-type N+1 / over-planning behavior is not currently a
production optimizer bug for abstract root fields; pure
`tests/optimizer/test_walker.py` calls would be testing a planner state the
extension cannot currently produce.

Necessary spec correction: choose one path before coding.

- If G3 is meant to ship in this card, expand Slice 3 to include the missing
  production entry contract for abstract return types. That is a larger design:
  how to resolve target model(s), origin type, plan-cache identity, and possible
  concrete types for interface / union returns without violating the spec's
  "registry-only, no per-request graphql-core introspection" rule.
- If that larger abstract-entry work is out of scope, defer G3 to the future
  `polymorphic_interface_connections` / abstract-optimizer card and revise this
  spec to say G3 is preparatory only, not a fix for a currently optimized
  consumer path.

The existing planned live `allLibraryGenresConnection { ... on GenreType { ... } }`
test is still useful as no-regression coverage for a matching concrete fragment,
but it does not prove the sibling-fragment bug because that concrete field cannot
legally select sibling concrete fragments.

### P1 — Decision 5's FK-id-elision safety argument misses consumer `.only()`

Decision 5 keeps FK-id elision enabled under non-`QUERY` operations because G2
suppresses optimizer-owned `.only()`, so "the full source row loads." That is not
always true. The consumer can return a queryset that already has `.only(...)`;
`django_strawberry_framework/optimizer/plans.py::diff_plan_for_queryset` preserves
the consumer projection and drops optimizer `only_fields` under the B8
consumer-wins rule.

If a mutation resolver returns `Item.objects.only("name")` and the selection asks
for `{ category { id } }`, the plan can still carry an FK-id elision for
`category`, but `category_id` is deferred by the consumer projection.
`django_strawberry_framework/types/resolvers.py::_build_fk_id_stub` reads
`getattr(root, field_meta.attname)`, which would trigger a deferred-column fetch
per row. Worse, because the relation was recorded as planned, strictness may not
surface the fallback as an unplanned N+1.

Necessary spec correction:

- Add a G2/G5 edge case for consumer-provided `.only(...)` under both `QUERY` and
  non-`QUERY` operations.
- Amend Decision 5: FK-id elision stays enabled only when the source FK column is
  guaranteed loaded by either the optimizer plan or the consumer projection.
- Add an implementation rule for the consumer-projection case. The clean fix is
  not just "drop all elisions" after diffing, because the elision branch did not
  also record a `select_related` fallback. The spec should define whether the
  plan stores enough metadata to restore a join, or whether resolver-time elision
  checks fall back loudly when the FK attname is absent from `root.__dict__`.

### P2 — G3 omits the walker's second fragment-inlining consumer

The spec names `walker.py::_walk_selections` as the G3 classifier call site, but
`django_strawberry_framework/optimizer/walker.py::_selected_scalar_names` also
calls `_included_field_selections(...)`. That helper decides whether FK-id
elision is safe for `{ relation { id } }` selections.

If G3 is implemented only at `_walk_selections`, relation child selections can
still be flattened unconditionally during FK-id-elision analysis. Depending on
the eventual abstract-entry shape, that can make elision decisions from sibling
or unknown composite fragments using different semantics than the main walk.

Necessary spec correction: Decision 6 and the source file list should explicitly
cover `_selected_scalar_names`. Either thread the same classifier into it, or
prove and document that it only receives concretely typed relation child
selections where sibling fragments are GraphQL-invalid.

### P2 — The registry-only classifier needs a concrete name-resolution contract

Decision 6 says "known sibling concrete type" means a registry-known object type
that is neither the planning type nor an implemented interface. The current
registry has `definition_for_graphql_name(...)`, but that helper is Relay-Node
specific and raises on misses/ambiguity; G3 needs a non-Relay lookup across all
registered `DjangoTypeDefinition`s.

The spec also needs to say exactly how interface GraphQL names are collected from
`definition.interfaces` and `origin.__mro__`. For Strawberry interfaces, the
GraphQL name should come from the Strawberry definition metadata, not from the
Python class name, so `Meta.name` / `@strawberry.interface(name=...)` style naming
does not drift.

Necessary spec correction:

- Define the lookup primitive: scan `registry.iter_definitions()` for
  `definition.graphql_type_name` across all registered `DjangoType`s, not only
  Relay-Node types.
- Define ambiguity behavior. Prefer fail-closed as `RECURSE_FRAGMENTS_ONLY` or
  a loud implementation error during tests, but do not leave duplicate GraphQL
  names as an implicit first-match.
- Define interface-name extraction from Strawberry definition metadata for both
  declared interfaces and MRO-inherited interfaces.

### P3 — The live G3 test is coverage/no-regression, not a behavioral proof

The planned live test under `examples/fakeshop/test_query/test_library_api.py`
selects `... on GenreType { books { title } }` under the concrete
`allLibraryGenresConnection` field. That path should already plan today because
the current fragment inliner unconditionally inlines typed fragments. After G3,
it proves matching-type fragments still inline and gives live coverage of the
new classifier branch, but it is not a red/green reproduction of the G3 bug.

Necessary spec correction: label this live test as mandatory live reachability
coverage and matching-type no-regression, not as evidence that G3 closes the
sibling-fragment bug. The actual behavioral proof needs either a real production
abstract optimizer path (see P1) or a clearly synthetic package-internal planner
contract.

### P3 — The configuration concern is not part of spec-035

The prompt asks about a setting read/validation anchor in
`django_strawberry_framework/types/relay.py` instead of `conf.py`. That is not a
spec-035 requirement. This optimizer-hardening spec explicitly says "no settings
key," and none of the staged spec-035 anchors touch `types/relay.py` or `conf.py`.

For the existing Relay setting path, `types/relay.py::_resolve_globalid_strategy`
reads `conf.settings.RELAY_GLOBALID_STRATEGY` and validates it at type
finalization, not during query execution. That does not add per-request runtime
overhead or request-time thread-safety risk; at worst it repeats domain
validation once per finalized Relay type during schema build. `conf.py` remains
the correct thin settings reader, because it should validate mapping shape but
not every feature-specific domain value.

No spec-035 correction is needed for configuration. If the concern is about
spec-031 / GlobalID strategy, review that spec separately.

## Recommended Spec Edits Before Production Code

1. Rework or defer G3. Do not ship synthetic-only G3 under the claim that it
   fixes a current consumer-constructible optimized abstract field until the
   production optimizer can actually enter that path.
2. Add the consumer `.only(...)` + FK-id-elision edge case to G2/Decision 5 and
   define a real fallback that does not silently lazy-load while strictness thinks
   the relation is planned.
3. Include `_selected_scalar_names` in the G3 source and test plan.
4. Define the registry name-resolution helper and ambiguity behavior for G3.
5. Reword the live G3 test as no-regression/coverage, with the real sibling-case
   proof tied to either the expanded production path or explicitly synthetic
   planner tests.
