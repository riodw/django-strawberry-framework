# Review - spec-032 Full Relay build plan, revision 6 (architecture pass)

Deep critical evaluation performed AFTER staging the `TODO(spec-032-full_relay-0_0_9
Slice N)` anchors across the package, tests, fakeshop, and docs - the hands-on pass
placed every seam the spec names, so this review focuses on whether the contracts
hold once real code flows through them. Scope covers spec-032 and the shipped
spec-031 machinery it consumes (`decode_global_id`, the strategy system,
`registry.py`), per the four review questions: internal/architectural
inconsistencies, missing edge cases, configuration/performance risks, and test/doc
gaps. Everything below is source-verified against the package, the locked
Strawberry `0.316.0` in `.venv`, and the fakeshop suites.

Headline: one P1 (the malformed-id contract is unreachable as specced - Strawberry
parses `GlobalID` arguments before the resolver runs), two P2s (an exception-
hierarchy trap and an unpinned garbage-pk path that leaks ORM internals), and two
P3s. The Q3 configuration/performance premise is largely defused by verification -
the strategy system is finalize-frozen, not lazily read per query - with one
documentation pin proposed. No spec-031-internal contradictions found: its decode
seam is honest at its own boundary; every finding below is about what happens when
spec-032 makes that seam wire-reachable.

## Findings

### P1 - The `GLOBALID_INVALID` contract for malformed ids is unreachable as specced: Strawberry converts `GlobalID` arguments BEFORE the resolver runs

Decision 5 routes "a malformed base64 string, a non-`type:id` payload" - "every
`ConfigurationError` from `decode_global_id`" - through the root-field boundary as
`GraphQLError(..., extensions={"code": "GLOBALID_INVALID"})`, and the Slice-2
checklist has the synthesized resolvers declare `id: relay.GlobalID` /
`ids: list[relay.GlobalID]` arguments. Those two requirements cannot both hold:

- `strawberry/types/arguments.py::convert_argument` special-cases the annotation -
  `if type_ is GlobalID: return GlobalID.from_id(value)` - during **argument
  conversion**, before the resolver is invoked. (The scalar itself is registered
  with `parse_value=lambda v: v` in `schema_converter.py`; the parse happens in
  argument conversion, not scalar coercion - same outcome either way.)
- A malformed base64 string or non-`type:id` payload therefore raises Strawberry's
  `GlobalIDValueError` **upstream of the package resolver**. The wire response
  carries Strawberry's error text with no `GLOBALID_INVALID` extensions code, and
  `decode_global_id`'s string-parsing branch (which exists precisely to wrap
  `from_id`'s `ValueError` - source-verified in `types/relay.py`) is dead code on
  this path.
- Consequently `test_node_malformed_id_graphql_error`, `test_node_malformed_id_live`,
  and `test_nodes_malformed_id_mid_batch` fail as specced for the malformed-base64 /
  bad-shape cases. Only the post-parse decode failures (unresolvable model label /
  type name, strategy-forbidden shape, no recorded strategy, empty slots) reach the
  package boundary and produce `GLOBALID_INVALID`.

**Proposed fix (preferred):** declare the arguments as `strawberry.ID` - `id:
strawberry.ID` / `ids: list[strawberry.ID]` - and feed the raw string to
`decode_global_id`, which already accepts `relay.GlobalID | str` and already wraps
the `from_id` `ValueError` superset. The package then owns EVERY failure shape
uniformly as `GLOBALID_INVALID`, exactly as Decision 5 pins. The SDL is unchanged:
under the modern default (`relay_use_legacy_global_id: bool = False`,
`schema/config.py`) Strawberry renders the `GlobalID` scalar as `ID` anyway, so
`node(id: ID!)` comes out byte-identical - and is the Relay spec's literal
signature. Record the `relay.GlobalID`-annotation form as a rejected alternative
(engine-owned coercion error; the wire contract for malformed ids would hang off
Strawberry's internal error text - an accidental API). Spec edits: Decision 5,
Error shapes, the Slice-2 checklist, Decision 4's argument spellings, and the three
test descriptions. The staged pseudocode in `django_strawberry_framework/relay.py`
currently mirrors the spec's `relay.GlobalID` arguments and should be corrected in
the same revision.

**Fallback:** keep `relay.GlobalID` and split the contract - malformed-shape
failures surface Strawberry's argument-conversion error (pin only that it is an
in-band GraphQL error, never a 500), `GLOBALID_INVALID` covers post-parse decode
failures only. Weaker: two error vocabularies for one client mistake family.

### P2 - `SyncMisuseError` IS-A `ConfigurationError`: the catch-and-convert boundary must scope ONLY the decode call

`types/relay.py::SyncMisuseError` is declared as `class
SyncMisuseError(ConfigurationError, RuntimeError)`. Decision 5 says every
`ConfigurationError` from decode "is caught at the field boundary and re-raised as
`GraphQLError` `GLOBALID_INVALID`"; DoD item 3 separately requires "the
`SyncMisuseError` pass-through" unchanged. An implementer who reads "field
boundary" as try/except around the whole resolver body satisfies the first sentence
and silently breaks the second: an async `get_queryset` met from a sync context
(a server misconfiguration) would be converted into a client-facing "Invalid
GlobalID" - mislabeled, masked, and wrong in both directions.

**Fix:** one sentence in Decision 5 pinning the scope - the conversion wraps the
`decode_global_id` call ONLY; the `resolve_node` / `resolve_nodes` dispatch runs
outside it - plus a discriminating assertion in the existing Slice-2 sync-misuse
test (`test_node_sync_async_get_queryset_raises_sync_misuse` asserts the surfaced
error is NOT `GLOBALID_INVALID`-coded). The staged `_decode_or_graphql_error`
helper in the relay.py anchor already has the narrow scope; the spec text should
match it.

### P2 - Well-formed id, garbage pk literal: `library.genre:abc` leaks a Django `ValueError` and is pinned nowhere

`decode_global_id` validates payload **shape** only - `library.genre:abc` parses
fine, resolves its candidate, passes strategy enforcement, and returns
`(GenreType, "abc")`. The shipped default then runs
`_apply_node_filter` -> `qs.filter(pk="abc")`, and Django raises
`ValueError: Field 'id' expected a number but got 'abc'` - surfacing as a generic
GraphQL error that leaks ORM internals, on a code path that was unreachable until
this card wires the first caller (the spec's own Current state notes nothing
invokes the decode/resolve pair from the wire today). The spec pins malformed ids
(error) and missing/hidden rows (null) but never this middle case: a
**well-formed id whose node_id cannot coerce to the target's pk type**. Same hole
in the batch path - one garbage entry poisons the whole `pk__in` filter.

**Proposed contract:** existence failure -> `null` (single) / positional `null`
hole (batch). A pk literal that cannot coerce trivially identifies no row; no
query is issued, and the no-existence-oracle property is unaffected (the
equal-query-count pin concerns coercible ids). This also matches graphene-django's
observed behavior (its node resolver swallows resolution exceptions to `None`).
Implementation seam: pre-coerce in `relay.py` via the target's
`model._meta.pk.to_python(node_id)` under try/except
`(ValueError, ValidationError)` - per-id in the batch so the rest still batches.
Spec edits: Decision 5's visibility/existence family, Edge cases, plus
`test_node_uncoercible_pk_returns_null` / `test_nodes_uncoercible_pk_null_hole`
and a live `library.genre:abc`-payload case in Slice 6 (cheap to add next to
`test_node_malformed_id_live`).

### P3 - `nodes(ids:)` is uncapped - record it as a decision, not an omission

`relay_max_results` caps every connection page, but a `nodes(ids: [...])` request
with 10,000 ids issues an unbounded decode loop and `pk__in` queries. Both
upstreams share the hole (Strawberry's native batch resolver and graphene-django
impose no cap), so parity does not force a fix - but the spec currently says
nothing, which reads as "covered" when it is "unconsidered". **Fix:** an Edge
cases entry pinning the 0.0.9 posture explicitly (no cap; request-size limiting is
the consumer's transport/rate-limit territory) and, if desired, a BACKLOG note for
a cap reusing `relay_max_results`. One paragraph; no code.

### P3 - Q3 verified: the strategy system is finalize-frozen, not lazily read - pin the one observable consequence

The premise that reading/validating `RELAY_GLOBALID_STRATEGY` in `types/relay.py`
(rather than `conf.py`) introduces per-query overhead or thread-safety risk does
not hold, verified:

- The setting is read exactly once per type, at finalization:
  `install_globalid_typename_resolver` -> `_resolve_globalid_strategy` (the only
  call site) -> the `from ..conf import settings` read. The result is stamped on
  `definition.effective_globalid_strategy` ("frozen at schema-build time", per the
  shipped CHANGELOG entry). The in-function conf import is a documented
  module-cycle dodge, not per-request laziness.
- Request-time work is settings-free on both halves: encode runs an installed
  closure over the already-resolved strategy; `decode_global_id` reads stamped
  strategies plus `registry` dict lookups and the cached `apps.get_model`. The only
  per-request addition spec-032 makes is the typed-form identity check - one `is`
  comparison. No redundant validation, no settings access, no shared mutable state
  beyond the registry the package already owns process-globally.
- The one consequence worth a sentence in the spec (Decision 10 or the Test plan):
  because the strategy freezes at finalize, `@override_settings` AFTER finalize
  changes nothing for already-finalized types - tests must clear + reload (the
  `_reload_project_schema_for_acceptance_tests` pattern already does). Corollary
  worth stating as a feature: `testing.relay.global_id_for` reads the **stamped**
  strategy, so the helper is consistent-by-construction with live emission and can
  never disagree with the schema the way a fresh settings read could.

## Q4 - test/setup risk check: verified, no major rewrite needed

- **Per-app library tests are churn-free.** The unmentioned suite
  `examples/fakeshop/apps/library/tests/test_schema.py` is 46 lines of
  introspection-level assertions (type presence, declaration order) with no book-id
  literals; the BookType promotion does not touch it. The spec's claim that churn
  is confined to `test_query/test_library_api.py` holds - worth one line in the
  Slice-6 checklist recording the per-app suite was checked, so the builder does
  not re-derive it.
- **Staff-bypass infrastructure exists.** `test_library_api.py` already creates
  `is_staff=True` users with `client.force_login` (the ShelfType visibility tests),
  so `test_node_hidden_row_null_live`'s staff half needs no new setup.
- **The pageInfo-only `hasNextPage` test, `test_relay_max_results_cap`
  (strawberry_config passthrough verified), and the live conformance matrix** all
  run on existing fixtures; `test_products_api` and its optimizer SQL-shape suite
  are untouched by this card, as Decision 12 requires.

## Q1 - spec-031 consistency check: clean

No internal spec-031 contradictions found. The decode seam's "uniform
`ConfigurationError`" promise is honest at its own function boundary (input gate
for `None`/`int`/lazy objects, empty-slot rejection, `GlobalIDValueError` wrapping
- all shipped and source-verified), and `registry.get(model)` /
`definition_for_graphql_name` exist with the routing the specs describe. The P1
and both P2s above are spec-032 consumer-boundary issues: what was unreachable
behind the seam becomes wire-reachable when 032 connects it, and the contracts at
that new boundary are where the spec needs the edits proposed above.

## Checks run

- Source verification: `django_strawberry_framework/types/relay.py`
  (`SyncMisuseError` MRO, `decode_global_id` input gate/steps,
  `_apply_node_filter` / `_coerce_node_id`, `_resolve_globalid_strategy` call
  sites), `conf.py`, `registry.py::get`; Strawberry `0.316.0`
  (`types/arguments.py::convert_argument` GlobalID special-case,
  `schema_converter.py` scalar registration + `relay_use_legacy_global_id`
  default, `relay/types.py::GlobalID.from_id` / `GlobalIDValueError`);
  fakeshop (`apps/library/tests/test_schema.py`, staff-login sites in
  `test_query/test_library_api.py`).
- The staged TODO anchors (this session's earlier pass) mirror the CURRENT spec;
  the `relay.py` anchor's `id: relay.GlobalID` argument spelling and the
  malformed-mid-batch test description should be updated together with the spec
  if the P1 preferred fix is adopted.
- No pytest run per repo instructions (`AGENTS.md` "Do not run pytest after
  edits").
