# Review - spec-032 Full Relay build plan, revision 5

Reviewed `docs/spec-032-full_relay-0_0_9.md` (Revision 5) against the package
source, the locked Strawberry `0.316.0` in `.venv`, the fakeshop example, and
the governance docs (`AGENTS.md`, `KANBAN.md`, `GLOSSARY.md`,
`docs/SPECS/NEXT.md`, `GOAL.md`, `TODAY.md`, `BACKLOG.md`, spec-029/030/031).

All prior-pass fixes hold: the stale-`after` contract is no-error-only
(Revision 2 P1), the secondary-emitter decode asymmetry and nullable-by-contract
dispatch are pinned (Revision 2 P2s), the consumer-authored explicit-key raise
and the camel-cased collision guard are in Decisions 6/7 with matching tests and
DoD items (Revision 3), and no normative section cites `docs/feedback.md`.

The load-bearing factual claims source-verify clean, including: the
`decode_global_id` signature/uniform-`ConfigurationError` contract and the
in-source "032 will consume" note; the Phase-2.5 step order in
`types/finalizer.py`; the exact `ALLOWED_META_KEYS` / `DEFERRED_META_KEYS`
sets; the twelve package exports with no `relay.py` on disk; the
`registry.clear()` ledger-co-clear precedent; the `connection.py` machinery
names including the `relay.connection(...)` construction and the first+last
`GraphQLError` guard (Strawberry itself accepts the combination — the guard is
genuinely package-owned); Strawberry's `NodeExtension` type-name-lookup
dispatch, `SliceMetadata.from_arguments` `start = int(after) + 1` offset
cursors, `PREFIX = "arrayconnection"`, `relay_max_results` default 100, the
native batch resolver's `required=not is_optional` per-type grouping, and the
index-map duplicate-`GlobalID` collapse (the overwrite is real — Decision 4's
reason to own the batch resolver stands); the `first: 0` overfetch trace
(`hasNextPage` true iff a row exists past the empty window — the planned
`test_first_zero` assertion is correct); the KANBAN card quotes (the exact
no-Node-types message, the `b64("offset:N")` wording, the six-diagnostics
count ambiguity, the card-named test files); the docs-root spec location per
`NEXT.md` ("Spec files live at the root of `docs/`"); the fakeshop current
state (GenreType the lone Relay type, `Book.genres` related_name `"books"`,
`Loan.book` related_name `"loans"`, non-Relay `LoanType`, no existing `genre`
root field to collide with); and the GLOSSARY gaps for `DjangoNodesField` /
`Meta.relation_shapes`.

## Findings

### P2 - Slice 6's live hidden-row test has no eligible type in the planned schema

The Slice-6 checklist and DoD item 9 require `test_node_hidden_row_null_live`
"through a visibility-filtered type", and Goal 1 / Decision 5 make the
hidden-row `null` a headline contract. But no type in the fakeshop project is
both Relay-Node-shaped and `get_queryset`-filtered, and Slice 6's enumerated
schema edits do not create one:

- The only `get_queryset` overrides in the project are `ShelfType`
  (`examples/fakeshop/apps/library/schema.py::ShelfType.get_queryset`, hides
  `topic="secret"`), `BranchType` (same file, hides `city="restricted"`), and
  `ScalarSpecimenTagType` (scalars app) — none declares
  `interfaces = (relay.Node,)`.
- The four products types are Relay-shaped but their `get_queryset` bodies are
  commented out; the kanban Relay type has no hook.
- Slice 6 promotes `BookType` (no `get_queryset`) and adds root fields on
  `GenreType` (no `get_queryset`).

As planned, the live hidden-row test cannot be written — `node(id:)` can only
refetch Relay-shaped types, and every Relay-shaped type is visibility-unfiltered.
The package-internal twin (Slice 2 `test_node_hidden_row_returns_null`) is fine
because package tests build their own fixtures, but the spec's own coverage
rule makes the live copy mandatory ("the live hidden-row and mixed-batch copies
land with Slice 6").

Fix: name the schema edit in Decision 12 / the Slice-6 checklist. Candidates:
give the promoted `BookType` a `get_queryset` filtering on something absent
from the default seed graph (the `ShelfType` "secret"-topic pattern keeps churn
bounded), or promote `ShelfType`/`BranchType` to Relay (note: that triggers
relation-as-Connection synthesis on their many-side relations and widens the
Slice-6 blast radius — if chosen, the synthesis fallout needs its own line in
the churn estimate). Whichever is chosen, the existing-assertions churn note
should cover it.

### P2 - The strictness-mode claim about nested connections describes behavior nothing in the plan implements

The spec asserts twice that strictness `"raise"` surfaces pre-`033`
nested-connection lazy-loads: the Key-glossary-references Strictness-mode
bullet ("a `\"raise\"` run surfaces the pre-`033` unplanned nested-connection
access as an N+1 (no silent cap)") and Decision 12 ("[Strictness mode]
`\"raise\"` correctly surfaces that as an N+1"). The Risks entry leans on this
("the behavior-only test posture plus strictness documentation cover the gap
honestly").

Source-verified: the B3 strictness check
(`types/resolvers.py::_check_n1`) is invoked only from the three generated
relation-resolver call sites in `types/resolvers.py`; `connection.py` never
references `DST_OPTIMIZER_PLANNED` / `DST_OPTIMIZER_STRICTNESS`. Decision 6's
synthesized relation-connection resolver reuses the connection pipeline
(relation-manager seed → visibility → filter → orderBy → optimizer seam →
slice), which never consults the strictness sentinels. So when a consumer
queries `booksConnection`, only the synthesized connection resolver runs — the
list field's `_check_n1` never fires (and under `"connection"` the list
resolver is removed entirely). A strictness-`"raise"` run would be silent for
exactly the access pattern the spec claims it flags — the opposite of "no
silent cap".

Fix one of two ways: (a) wire the N+1 sentinel check into the synthesized
relation-connection resolver in Slice 3 (mirroring the `_check_n1` call shape)
and add a package test pinning `OptimizerError` under `strictness="raise"`
with a planned context; or (b) correct both claims to say strictness does
*not* see nested connections until `033` and hand the wiring to the `033`
card explicitly. Option (b) is smaller but weakens the Risks entry's "covered
honestly" argument, which should then rest on the joint-cut sequencing alone.

### P2 - Typed `DjangoNodesField` ships per the DoD but has zero tests; batch malformed-id semantics are unpinned

Decision 4 ships "`DjangoNodesField(GenreType)` ... the typed batch sibling
with the same per-id check" and DoD item 3 says "`DjangoNodesField` (bare +
typed)". But the test plan never exercises the typed batch form: Slice 2's
typed tests cover only the single-node field
(`test_typed_node_field_resolves_target` / `..._mismatch_raises`), and Slices
4 and 6 add only bare-`nodes` coverage. Under `fail_under = 100` the typed-
batch branch cannot even merge untested, so the gap will surface as unplanned
work mid-Slice-2; the test plan is the contract record and should name the
tests now (e.g. `test_typed_nodes_field_resolves_targets`,
`test_typed_nodes_field_mismatch_raises`).

Adjacent unpinned contract, same surface: what happens when one id in a bare
`nodes(ids:)` batch is *malformed* (as opposed to well-formed-but-missing)?
Decision 5 routes format failures to `GraphQLError`, which for a batch
presumably fails the whole field — and since the documented annotation renders
`[Node]!`, the error nulls the enclosing `data`, not one hole. The Slice-6
batch test mixes only a "bogus-pk" (well-formed) id, so the malformed-mid-batch
path is never specified or tested. Pin the behavior in Decision 5 / Error
shapes (whole-field `GLOBALID_INVALID` is the consistent reading) and add
`test_nodes_malformed_id_mid_batch` to Slice 2; same question for one
wrong-type id under the typed batch form.

### P3 - `test_has_next_page_correct_when_unrequested` asserts an unobservable property as worded

Goal 4, Decision 9, the Slice-4 matrix, and DoD item 7 all pin "`hasNextPage`
is computed correctly even when the consumer did not request it". A GraphQL
response omits unrequested fields, so no live HTTP test can assert anything
about an unrequested `hasNextPage` — as named, the test cannot exist.

The observable (and non-trivial) edge the wording is reaching for is the
inverse selection: `hasNextPage` must be correct when **edges are not
requested** — a pageInfo-only query. That case is real in Strawberry:
`ListConnection.resolve_connection` inspects the selection set (the
selection-walking helper in `strawberry/relay/utils.py`) to decide how much to
fetch, so a pageInfo-only query is exactly where a lazy implementation could
get `hasNextPage` wrong. Reword the four spots and the test name to
"correct when only `pageInfo` is selected (edges unrequested)".

### P3 - The stated async mechanism cannot produce the `nodes` reassembly; pin the dispatch shape

Edge cases says: "the root resolvers return the `resolve_node(s)` defaults'
values, which are coroutines in async context; Strawberry awaits plain-field
coroutines." That pass-through story holds for the single-node field, but not
for `nodes`: Decision 4 requires the synthesized resolver to call
`resolve_nodes` once per distinct type and reassemble results in input order
with `null` holes. In async context each per-type call returns a coroutine
(the defaults dispatch per-call via `in_async_context()` —
`types/relay.py::_resolve_node_default`), so the resolver cannot "return the
defaults' values"; it must itself detect the async context and return a single
coroutine that awaits the per-type results and interleaves them.

That shape is fine for a plain field — unlike `ConnectionExtension`, which only
awaits on async-committed fields (the documented reason
`connection.py::_build_connection_resolver` commits sync/async at
construction), plain-field coroutine returns are awaited by the executor. But
the spec cites the spec-030 committed-at-construction precedent while the root
fields necessarily use the *other* mechanism (per-call `in_async_context()`
detection — there is no consumer resolver to inspect at construction). One
sentence in Decision 4 or the Edge cases entry pinning "per-call
`in_async_context()` dispatch; the bare/typed `nodes` resolver returns a
gathering coroutine on the async branch" would give Slice 2's
`test_nodes_async_context` a defined seam instead of an implied one.

### P3 - GOAL.md's typed showcase uses the non-optional spelling the spec declares unsupported

Decision 4 anchors the typed form on the GOAL.md astronomy shape, and GOAL.md
indeed reads `galaxy: GalaxyNode = DjangoNodeField(GalaxyNode)` — a
non-optional annotation. But Decision 5 / the User-facing API pin the root
fields as nullable-by-contract: a non-optional spelling "does not switch the
resolver onto a raising path — a missing or hidden row then surfaces as
Strawberry's generic non-null violation, so the optional spelling is the
supported shape." The spec is therefore citing, as its own design anchor, an
example it simultaneously declares a trap.

Either add a GOAL.md touch-up to the Slice-7 doc list (flip the showcase to
`GalaxyNode | None`) or record the tension in Risks with an owner — otherwise
the `1.0.0` showcase ships a spelling whose missing-row behavior is a generic
non-null error the package explicitly chose not to support.

## Checks run

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-032-full_relay-0_0_9.md`
  -> `OK: 38 terms - all have glossary entries and at least one spec link.`
- Source verification across `django_strawberry_framework/` (types/relay.py,
  types/base.py, types/finalizer.py, types/definition.py, types/resolvers.py,
  registry.py, connection.py, list_field.py, scalars.py, testing/,
  `__init__.py`), the locked Strawberry `0.316.0` in `.venv`
  (relay/fields.py, relay/types.py, relay/utils.py, schema/config.py),
  `examples/fakeshop/` (library/products schemas, models, test_query/), and
  the governance docs listed above.
- No pytest run per repo instructions (`AGENTS.md` "Do not run pytest after
  edits").
