# DRY review: `django_strawberry_framework/connection.py`

Status: verified

## System trace

`connection.py` is the execution adapter between a `DjangoType` and Strawberry's Relay connection
protocol. `DjangoConnectionField` validates the target through the shared Relay-shaped
`DjangoType` guard, resolves one generated concrete `<TypeName>Connection` per target, synthesizes
the target's `filter:` / `orderBy:` resolver arguments, and delegates the standard Relay field
arguments and resolver lifecycle to `strawberry.relay.connection`.

The root resolver pipeline has one source-normalization head and one queryset tail. A default field
starts from the target model's default manager; a consumer resolver may return a manager, queryset,
or plain iterable. `utils/querysets.py` owns manager normalization, initial-queryset discovery, and
sync/async `get_queryset` visibility. A plain iterable is accepted only when no queryset sidecar is
supplied, while a pre-sliced queryset is rejected because the connection owns ordering and slicing.
The queryset path then applies visibility, the declared `FilterSet`, the declared `OrderSet`,
deterministic ordering, and `optimizer/extension.py::apply_connection_optimization`. The sync and
async pipelines spell only the I/O-colored hook calls separately; their source preparation and
lazy queryset finalization are shared.

`DjangoConnection.resolve_connection` guards `first` plus `last` before inspecting selections or
data. It then consumes an internal optimized nested-window handoff when present, dispatches
`Meta.cursor_field` types to the package keyset resolver, and otherwise delegates offset cursor,
edge, and `pageInfo` construction to Strawberry's `ListConnection`. Offset-window consumption
reconstructs Strawberry-equivalent cursors and page flags from row-number/count annotations.
Keyset resolution uses the canonical codec and seek vocabulary from `keyset.py`, derives the
effective order (including an explicit `orderBy:`), fetches one probe row beyond the requested
page, reverses backward pages into client order, and computes cursors and page flags without
mixing offset and value-cursor formats.

The generated total-count variant selection-gates `totalCount`, attaches the post-filter,
pre-slice queryset count to that connection instance, and consumes a window annotation instead of
issuing a count query when the nested optimizer supplied one. Non-queryset sources fail with a
field-local `GraphQLError` only when `totalCount` is actually selected. The same generated-class
path serves targets without `totalCount`; a concrete class is required because Strawberry's
generic specialization otherwise loses this package's `resolve_connection` override. The
identity-keyed type cache is cleared through the package registry reset lifecycle.

`types/finalizer.py` synthesizes eligible many-side `<field>Connection` siblings and records their
underlying relation names on `DjangoTypeDefinition`. Their resolver starts from the parent relation
manager rather than the target default manager. It first probes the response-key-specific or
shared optimizer `to_attr`; annotated rows are handed to the connection class, while an ambiguous
empty window invokes the captured per-parent pipeline for exact `pageInfo` and `totalCount`.
Sidecars, unsupported windows, and absent planning fall back to that same pipeline and use the
existing relation-resolver strictness checker rather than a connection-specific error system.

The connected ownership boundaries are already narrow:

- `utils/connections.py` owns resolver/planner argument names, sidecar extraction, Relay max-result
  resolution, offset/keyset bounds, count/probe requirements, and window-range planning.
- `utils/querysets.py` owns query-source and `get_queryset` visibility normalization.
- `optimizer/selections.py` owns selection traversal for `totalCount` and `pageInfo.hasNextPage`.
- `optimizer/plans.py` owns deterministic order and ORM window rendering.
- `keyset.py` owns cursor-column validation, authenticated encoding/decoding, fingerprints, and
  seek predicates.
- `optimizer/walker.py` recognizes generated relation connections from definition metadata and
  chooses whether a nested response key is safely plannable.
- `optimizer/nested_fetch.py` owns the strategy-neutral fetch request; the windowed ORM and
  PostgreSQL lateral modules remain separate renderers behind that seam.
The target-definition cross-check maps the remaining private names onto those responsibilities.
Keyset state/order/page work is `_KeysetConnectionState`, `_keyset_connection_context`,
`_keyset_order_ref`, `_resolve_order_path_field`, `_keyset_order_state`, `_KeysetPage`,
`_KeysetPage.has_next_page`, `_KeysetPage.has_previous_page`, and `_resolve_keyset_connection`.
Optimized window handoff is `_WindowedConnectionRows`, `_build_windowed_fallback`,
`_window_edge_class`, `_resolve_from_window`, `_consume_window`, `_consume_fallback`,
`_empty_page_connection`, `_has_next_page_requested`, `_resolve_connection_fast_path`, and
`_window_rows_are_annotated`. Guard/count/class work is `_guard_first_and_last`,
`_total_count_requested`, `_set_total_count`, `_guard_total_count_countable`,
`_attach_count_sync`, `_attach_count_async`, `_generate_connection_class`,
`_build_total_count_connection`, `_connection_type_for`, and `clear_connection_type_cache`.
Resolver/pipeline work is `_guard_sidecar_input_against_non_queryset`,
`_guard_source_not_pre_sliced`, `_prepare_pipeline_source`, `_finalize_queryset`,
`_pipeline_async`, `_synthesized_signature`, `_build_connection_resolver`, and
`_build_relation_connection_resolver`.

## Verification

- Read the complete target and traced its root, generated relation, offset, keyset, total-count,
  sync/async, optimizer, strictness, cache-clear, and failure paths through the production owners
  above. A static audit under `docs/dry/temp-tests/connection/audit.md` scanned 329 Python files
  and found no exact production duplicate body involving `connection.py`; repeated exact bodies
  were predominantly deliberate test fixtures and resolvers.
- `tests/test_connection.py`, `tests/test_keyset_connection.py`, `tests/test_keyset.py`,
  `tests/test_relay_connection.py`, `tests/utils/test_connections.py`, and the connection cases in
  `tests/optimizer/test_walker.py` pin the root and nested pipelines, cursor/pageInfo arithmetic,
  `first`/`last` rejection, count selection gating, malformed inputs, source guards, generated
  classes, response-key windows, fallback behavior, and planner/resolver parity.
- The products and library schemas exercise root and generated relation connections, while
  `examples/fakeshop/test_query/test_keyset_api.py` proves encrypted cursor opacity, forward and
  backward page round trips, insert stability, malformed-cursor errors, and nested keyset parity
  through live GraphQL HTTP. `README.md`, `docs/README.md`, `docs/GLOSSARY.md`, and `docs/TREE.md`
  expose the same high-level pipeline, sidecars, count, relation synthesis, and nested optimizer
  contract. Their terse historic description of the generic base as adding only the guard refers
  to its public connection-field shape; the internal keyset/window dispatch is not a competing
  implementation or a DRY consolidation target.
- Inspected installed Strawberry's `SliceMetadata.from_arguments`,
  `ListConnection.resolve_connection`, `ConnectionExtension.resolve` / `resolve_async`, and
  `should_resolve_list_connection_edges`. Strawberry owns offset slicing, standard cursor
  construction, async materialization, and edge-selection gating; it does not reject
  `first` plus `last` and cannot decode this package's keyset cursors. The sibling
  `strawberry-graphql-django` checkout similarly keeps its Django pagination adapter separate from
  generic Strawberry mechanics; it supplies no owner that can replace this package's visibility,
  sidecar, generated-relation, or keyset contracts.
- `git diff --name-status 8ae3da739a60e680a48b1fb2cbc23e214ab5f058 -- <all traced
  production/test/example/standing-doc paths>` returned empty. Thus the reviewed scoped state
  matches the assigned baseline despite unrelated shared-checkout changes.

Rejected candidates:

- `DjangoListField` and a connection both normalize managers and apply `get_queryset`, but those
  mechanics are already shared in `utils/querysets.py`. A list field deliberately has no Relay
  bounds, deterministic total-order requirement, sidecar contract, count, or pre-slice ownership;
  merging their wrappers would require mode flags around almost every remaining decision.
- Root and generated relation connection resolvers share the pipeline tail, already single-sited
  in `_pipeline_sync`, but not source ownership. The root starts from a default manager or consumer
  resolver and may select an async pipeline at construction; the nested resolver must preserve the
  parent's relation-manager/prefetch cache, optimizer `to_attr`, response-key alias, fallback
  factory, and strictness identity. A generic source callback would hide those cooperation seams
  without removing policy.
- Offset and keyset pagination share normalized bounds through `utils/connections.py`, then must
  diverge. Strawberry's offset cursors encode positions and use slice metadata; keyset cursors
  encode ordered row values, validate an order fingerprint, seek in the queryset, probe for an
  extra row, and reverse backward results. Forcing both through one pagination engine would either
  lose Strawberry parity or add a cursor-mode branch to every operation.
- The resolver, walker, and nested fetch renderer all mention page size and count/probe needs, but
  they consume the shared bound/window model for different phases. In particular,
  `resolve_relay_max_results` has a terminal runtime default of `100`, while the walker's
  optimizer-info reader intentionally returns `None` when configuration is unavailable so
  Strawberry can decide downstream; the optimizer test suite pins that distinction.
- Connection, mutation, auth, filter, and order factories synthesize resolver annotations, but the
  schemas differ. Mutation/auth already share their lazy fixed-field signature builder.
  Connections uniquely need an `Iterable[target]` return, optional Meta-derived filter/order
  sidecars, helper-ledger registration, and Strawberry `ConnectionExtension` compatibility.
  Promoting a universal signature builder would parameterize rather than eliminate those rules.
- Generated connection classes and generated input classes both keep dictionaries, but the
  connection cache memoizes one schema type by target identity and is disposable hygiene on
  registry reset. Filter/order ledgers materialize lazy-reference module globals, track names and
  provenance, and have namespace cleanup obligations. Their values, invalidation triggers, and
  collision policies do not change together.
- The non-queryset sidecar error, selected-count error, pre-sliced-queryset error, malformed keyset
  error, and planner fallback are not one generic failure policy. They occur at construction,
  resolver, connection, or planning phases; some must raise field-local `GraphQLError`, while a
  planner must leave an unsafe shape unplanned so the resolver can remain correct. A shared
  raise-or-fallback helper would erase that phase distinction.
- The windowed ORM and lateral SQL paths duplicate pagination decisions only at the representation
  boundary. `optimizer/nested_fetch.py` already shares the strategy request, and both renderers
  consume the same order/bounds/count contract. Their SQL capabilities, alias routing, supported
  query shapes, and fallback mechanics are intentionally backend-specific.

## Opportunities

None — all confirmed shared policies already reside at their true owners. The remaining parallel
code either represents a different execution phase/backend, preserves a distinct source or cursor
contract, or is explicit test coverage whose independent behavior should remain legible.

## Judgment

No production, permanent-test, example, or standing-document consolidation is warranted.
`connection.py` remains the correct Strawberry/Django adapter while reusable pagination,
queryset, selection, ordering, keyset, and nested-fetch policy stays outside it at the narrowest
shared seams. The zero-edit result is ready for independent Worker 3 verification.

## Independent verification (Worker 3)

Revision needed — the 41-definition coverage check passes, the assigned-baseline scoped diff is
empty, and an independent trace found no missed DRY consolidation or production behavior defect.
The ownership conclusions for root/relation sources, offset/keyset pagination, count/probe
selection, visibility, sidecars, optimizer application, generated types, cache reset, errors, and
sync/async execution are otherwise supported by the connected implementations and upstream
Strawberry 0.316.0.

The review is incomplete because it accepts stale representations of the nested empty-window
contract. `utils/connections.py::window_range_plan` and
`optimizer/plans.py::apply_window_pagination` retain marker rows for `first: 0` and overshot
`after:`; `connection.py::_resolve_from_window` consumes those markers directly. The focused
offset and keyset tests prove a fixed batched-query path with no per-parent fallback. Nevertheless,
the System trace says an ambiguous empty window invokes the per-parent pipeline, and the same
obsolete claim remains in `connection.py::_WindowedConnectionRows`,
`connection.py::_build_windowed_fallback`, `connection.py::_consume_window`,
`connection.py::_consume_fallback`, `connection.py::_resolve_connection_fast_path`,
`connection.py::_window_rows_are_annotated`,
`connection.py::_build_relation_connection_resolver`, and the standing
`docs/GLOSSARY.md` “Connection-aware optimizer planning” entry. The real fallbacks are unsupported
or defensive shapes such as `last: 0`, backward keyset windows, sidecar/unplanned paths, and
missing required annotations. `connection.py::DjangoConnection` also says the guard is the base's
only added behavior although its override dispatches optimized windows and keyset connections; the
Verification section dismisses that contradiction rather than identifying it.

Reproduce with:

- `tests/test_relay_connection.py::test_fast_path_ambiguous_empty_served_from_marker_row` (both
  `first: 0` and overshot `after:` assert two queries and optimizer-on/off parity);
- `examples/fakeshop/test_query/test_keyset_api.py::test_nested_keyset_first_zero_serves_flags_from_markers`;
- `examples/fakeshop/test_query/test_keyset_api.py::test_nested_keyset_marker_distinguishes_pre_cursor_only_parents`;
- `tests/test_relay_connection.py::test_fast_path_last_zero_quirk_parity_via_fallback` for the
  contrasting genuine fallback.

Focused validation: the connection/keyset utility suites plus those marker/fallback cases passed
(`155 passed` with `--no-cov`). The same partial selection with normal coverage collection passed
its tests but exited nonzero at the repository-wide 100% coverage gate, as expected for a partial
suite. Route this incomplete zero-edit review back to Worker 1; leave `connection.py` open in the
plan until the artifact and standing/source documentation accurately describe the shipped
contract.

## Iterations

### Worker 1 revision after independent verification

The production DRY judgment remains unchanged: no runtime consolidation is warranted. The
zero-edit conclusion does not. The executable marker/fallback contract is represented again in
source docstrings/comments and generated consumer documentation, and those prose representations
have drifted from the single implementation.

**Repeated responsibility.** The nested-window resolver contract—what an annotated marker row can
serve, what requires a per-parent fallback, and what behavior `DjangoConnection.resolve_connection`
adds over Strawberry—is described by the executable planner/resolver path and repeated in
`connection.py` prose plus the generated glossary. Those representations must change together.

**Sites.** The executable owners are `utils/connections.py::window_range_plan`,
`optimizer/plans.py::apply_window_pagination`, `connection.py::_resolve_from_window`, and
`connection.py::DjangoConnection.resolve_connection`. The stale `connection.py` representations
are:

- the module docstring's `DjangoConnection` “guard and nothing else” claim;
- `_WindowedConnectionRows` and `_build_windowed_fallback`, which say the carried callable exists
  for `first: 0` / overshot-`after:` ambiguity;
- `_consume_window`, `_consume_fallback`, and `_resolve_connection_fast_path`, which call those
  marker shapes per-parent fallbacks;
- `DjangoConnection`'s class docstring and `resolve_connection` summary, which call the guard its
  only behavior and imply unconditional `ListConnection` delegation;
- `_build_total_count_connection`'s docstring and generated resolver comment, which describe only
  queryset count-and-delegate behavior and still cite a nonexistent first-zero-fallback test;
- `_window_rows_are_annotated`, which classifies an empty window as possibly ambiguous even though
  planned marker shapes now make it conclusive;
- `_build_relation_connection_resolver`'s handoff docstring and inline marker comment, which say
  the fallback factory is consumed for those formerly ambiguous empty pages; and
- `_total_count_requested`'s “once nested connections land” wording plus
  `_has_next_page_requested`'s blanket count-annotation description, which predate shipped nested
  connections and the count-free n+1 probe.

The generated documentation copies the same contract from tracked
`examples/fakeshop/db.sqlite3`: glossary row 445 (“Connection-aware optimizer planning”) says
`first: 0` and overshot `after:` fall back and describes every served window as count-annotated;
row 449 (“`DjangoConnection`”) says the base adds nothing beyond the guard. `docs/GLOSSARY.md` is
their generated projection, not an independent editing site. No matching false marker/fallback
claim appears in `README.md`, `docs/README.md`, or `docs/TREE.md`.

**Evidence.** `window_range_plan` marks zero-limit and overshot-offset shapes for preservation;
`apply_window_pagination` retains each partition's absolute first row; and
`_resolve_from_window` removes that marker from the edge page while consuming the selected-count
annotation or count-free probe needed to derive `pageInfo`. A physically empty planned window
therefore proves that parent has no rows; a marker-only window proves rows exist but none belong to
the requested page. The rerun

- `uv run pytest --no-cov
  tests/test_relay_connection.py::test_fast_path_ambiguous_empty_served_from_marker_row
  tests/test_relay_connection.py::test_fast_path_last_zero_quirk_parity_via_fallback
  examples/fakeshop/test_query/test_keyset_api.py::test_nested_keyset_first_zero_serves_flags_from_markers
  examples/fakeshop/test_query/test_keyset_api.py::test_nested_keyset_marker_distinguishes_pre_cursor_only_parents`

passed all five parametrized cases. The marker test fixes the offset shapes at two queries and
proves optimizer-on/off byte parity; the two keyset tests prove value-domain flags and pre-seek
totals come from markers; the contrasting `last: 0` case proves the per-parent path preserves
Strawberry's `edges[-0:]` serve-all quirk. Current genuine fallbacks are unplanned sidecars,
unsupported backward keyset windows, `last: 0`, and defensive resolver-plan drift such as missing
required count/seek annotations. A read-only database query located the exact false clauses in
rows 445 and 449. All involved source/database/projection paths match baseline
`8ae3da739a60e680a48b1fb2cbc23e214ab5f058`.

**Owner.** Runtime truth remains at the planner/resolver owners above; it must not move into prose
or a new helper. `connection.py` owns documentation of its internal handoff and dispatch.
Glossary rows 445 and 449 in `examples/fakeshop/db.sqlite3` own the durable consumer wording, with
`scripts/build_glossary_md.py` owning the deterministic `docs/GLOSSARY.md` projection.

**Consolidation.** Worker 2 should make documentation-only source edits:

1. Update every listed `connection.py` docstring/comment to describe marker rows as directly
   serving `first: 0`, overshot offset `after:`, and the corresponding forward keyset empty pages.
   Describe the carried callable as a defensive recovery path for a wrapper that cannot be served,
   not as the normal empty-page path. Name the real unplanned/defensive fallbacks above, preserve
   the distinction between resolver-side refusal and walker-side non-planning, and replace the
   obsolete test citation with the existing marker/fallback pins.
2. Describe `DjangoConnection` as adding the mutual-exclusivity guard, optimized window
   consumption, and keyset dispatch while still adding no `total_count` field; state that only the
   ordinary non-window offset path delegates to Strawberry `ListConnection`. Align the generated
   total-count description with annotation-backed windows and framework-owned keyset counting.
3. Update glossary rows 445 and 449 at their SQLite source. Row 445 should explain conditional
   count annotations/count-free probes, direct marker serving, and the genuine fallback matrix.
   Row 449 should describe all three behaviors in the base override while retaining the
   no-`total_count` public-field distinction. Regenerate `docs/GLOSSARY.md`; do not hand-edit only
   the projection.

No implementation logic or permanent test needs to change.

**Proof.** Keep the existing marker, zero-child, `last: 0`, backward-keyset, sidecar-strictness,
and defensive annotation-drift tests unchanged and run their focused `--no-cov` slices. Grep
`connection.py`, rows 445/449, and `docs/GLOSSARY.md` to prove the false “adds nothing else” and
ambiguous-empty-fallback claims are gone while genuine fallback wording remains. Query both
database rows directly, regenerate the glossary twice to temporary outputs, and compare each with
the tracked projection. Run `git diff --check`, the repository trailing-comma/source-layout check,
`uv run ruff format .`, and `uv run ruff check --fix .`, verifying status snapshots so concurrent
work is preserved.

**Risks / non-goals.** Do not alter marker retention, query counts, cursor bytes, page flags,
selection-gated counts, the `last: 0` compatibility quirk, keyset fallback, sidecar strictness, or
defensive drift guards. Do not delete `_build_windowed_fallback`: it remains the correctness
recovery seam even though normal planned marker pages no longer use it. Do not broaden the
glossary change beyond rows 445/449, hand-edit generated Markdown without its database source, add
a redundant behavior test for prose-only edits, or add a changelog entry for a non-behavioral
correction.

## Implementation (Worker 2)

Reproduction confirmed the executable planner/resolver path as the owner: retained marker rows
directly serve `first: 0`, overshot offset `after:`, and corresponding forward keyset empty pages,
while the per-parent callable remains a correctness seam for an unservable wrapper. The five
pre-edit marker/fallback cases passed, so no runtime or permanent-test change was warranted.

Updated only the inventoried docstrings/comments in
`django_strawberry_framework/connection.py`. They now describe conditional counts and count-free
probes, direct marker serving, defensive recovery for `last: 0`, a backward keyset wrapper, and
missing required count/seek annotations, plus resolver-side sidecar refusal versus walker-side
non-planning. `DjangoConnection` now documents all behavior its override adds: the mutual-
exclusivity guard, optimized-window consumption, and keyset dispatch; only an ordinary non-window
offset source delegates to Strawberry `ListConnection`. The generated total-count prose now
distinguishes annotation-backed windows, framework-owned keyset counting, and ordinary queryset
count attachment.

Updated only `glossary_glossaryterm` rows 445 and 449 in
`examples/fakeshop/db.sqlite3`, then regenerated `docs/GLOSSARY.md` with
`scripts/build_glossary_md.py`. A table-by-table logical comparison against
`8ae3da739a60e680a48b1fb2cbc23e214ab5f058` found no database difference outside those two rows.
Two isolated temporary renders were byte-identical to one another and to the tracked projection.

Behavior deliberately remains separate: sidecar and unsupported backward selections are normally
left unplanned; `last: 0` stays per-parent to preserve Strawberry's serve-all quirk; backward
keyset fallback stays codec-aware; and handed-off annotation drift still recovers defensively.
Marker retention, cursor bytes, query counts, page flags, count selection, strictness, and fallback
logic are unchanged.

Verification:

- Focused pre-edit reproduction: 5 passed with `--no-cov`.
- Focused post-edit marker/zero-child/`last: 0`/sidecar/annotation-drift/keyset matrix: 12 passed
  with `--no-cov`.
- `uv run python scripts/check_trailing_commas.py --check`: passed.
- `git diff --check`: passed.
- `uv run ruff format .`: 352 files unchanged.
- `uv run ruff check --fix .`: all checks passed.
- Before/after status and SHA-256 comparison found no ruff collateral in any out-of-scope Python
  file; concurrent dirty and untracked work remained present and untouched.

This documentation-only correction does not merit a changelog entry.

## Iterations

### Worker 3 final verification after implementation

Verified. The implementation resolves every revision finding without changing executable
connection behavior. A baseline/current AST comparison after removing module, class, function,
and async-function docstrings is identical; the `connection.py` diff contains only docstrings and
comments. Its current prose consistently describes direct marker serving for `first: 0`,
overshot offset `after:`, and forward keyset empty pages; conditional counts and count-free probes;
and the distinct genuine recovery paths for `last: 0`, backward keyset wrappers, sidecars, and
required-annotation drift. The `DjangoConnection` and generated-total-count descriptions now name
window consumption and keyset dispatch while preserving ordinary offset delegation to Strawberry.
The earlier System trace and Independent verification wording remains as chronological review
history and is explicitly superseded by the revision and implementation sections.

A table-by-table logical comparison of `examples/fakeshop/db.sqlite3` against
`8ae3da739a60e680a48b1fb2cbc23e214ab5f058` found exactly one changed table:
`glossary_glossaryterm`. Exactly rows 445 (“Connection-aware optimizer planning”) and 449
(“`DjangoConnection`”) differ, and only their `body` columns changed. Two isolated
`scripts/build_glossary_md.py` renders were byte-identical to each other and to the tracked
`docs/GLOSSARY.md`, whose diff contains only those two generated entries.

The focused marker, zero-child, fallback, sidecar, count/seek-drift, backward-keyset, and live
nested-keyset matrix passed all 12 parametrized cases with `--no-cov`. The 41-definition artifact
check, trailing-comma check, Ruff format/lint, and final diff checks pass. No permanent test,
runtime implementation, example schema, changelog, branch, or commit change was added, and
unrelated shared-checkout work remains outside this item.
