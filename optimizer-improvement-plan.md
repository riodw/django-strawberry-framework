# Plan: Optimizer improvement program (windowed/lateral nested connections)

> **Status (2026-07-17): shipped and committed.** All workstreams below landed in the
> `feat(optimizer)` commits (fetch-mode axis / generic relations / strategy hints / index
> advisory, then single-parent fast path / lateral visibility scope / recognizer
> hardening). The session-scoped constraint lines below ("do NOT commit", "leave the tree
> dirty", "do NOT run pytest") were authoring-time instructions and are superseded; the
> plan is preserved verbatim as the working record, including its as-shipped corrections.

Derived from a 16-lane competitive recon (Django core sliced Prefetch, strawberry-django,
MrThearMan/graphene-django-query-optimizer, Undine, Prisma, Drizzle, EF Core, Laravel, Rails,
entgql, Hasura/pg_graphql, join-monster/Grafast, SQL-engine literature) followed by a 4-bundle
adversarial verification pass against the local tree. Every claim below was re-derived against
the current code; recon items that verification killed are listed in "Deliberately NOT doing"
with the refutation, so nobody re-chases them.

## Standing constraints (AGENTS.md — do not violate)

- READ AGENTS.md before starting. ASCII-only in `.py` files (no arrows/ellipsis chars).
- `uv run ruff format .` + `uv run ruff check --fix .` after every edit.
- Do NOT commit, branch, or stash. Leave everything dirty for the maintainer.
- Do NOT run pytest or coverage. Write the tests; do not execute them (explicit instruction
  for this program).
- Do not touch KANBAN tables / db.sqlite3, CHANGELOG.md, or GLOSSARY.md.
- Concurrent maintainer work is DIRTY in the tree right now: `mutations/permissions.py`,
  `permissions.py`, `utils/querysets.py`, `connection.py` (staged hunk adding
  `reject_residual_async_source` to `_pipeline_async`, ~L1730-1745), `tests/test_permissions.py`,
  `tests/utils/test_querysets.py`, `docs/dry/*`. WS-A edits `connection.py`: edit ON TOP of the
  dirty state, never revert or re-derive those hunks, and never `git stash`.
- Test placement per AGENTS.md: live tier (`examples/fakeshop/test_query/`) FIRST for any line
  reachable over /graphql; package tier (`tests/`) only for genuinely unreachable branches.
  First line of catalog/auth tests: `seed_data(N)`/`create_users(N)`; library tests use inline
  `Model.objects.create`.
- Source refs in code comments / docstrings: symbol-qualified (`path::QualifiedName`), never
  raw line numbers. Line numbers in THIS file are scratchpad hints; re-derive before editing.

## Sequencing and the feedback2.md interaction

`feedback2.md` (single-parent degenerate fast path) is a fully-verified plan assigned to a
SEPARATE session. Collision analysis (verified):

- feedback2 touches: `lateral_fetch.py::_parent_in_values` (keyword-signature refactor),
  `nested_fetch.py::WindowedPrefetchStrategy.plan` (wrap= hook), `conf.py`, new
  `optimizer/single_parent_fetch.py`.
- THIS plan's WS-C also rewrites the `_extract_parent_ids` / `_parent_in_values` neighborhood.

Resolution: **WS-C Step C1 performs feedback2's Step 1 verbatim** (refactor the current
`_parent_in_values(node, spec)` to `_parent_in_values(node, *, column: str, table: str)` + its 6
call sites), so feedback2's Step 1 becomes a no-op when that session runs. Concurrency guards
(the maintainer runs parallel sessions):

- **Pre-flight:** if `_parent_in_values` already has the keyword signature, feedback2 ran first —
  C1 is a no-op; adapt to what exists.
- **In-flight check:** before starting WS-C, check for `optimizer/single_parent_fetch.py` or
  fresh uncommitted hunks in `lateral_fetch.py`/`nested_fetch.py` you did not write. If present,
  the feedback2 session is mid-flight: STOP WS-C and report; do not merge over it.
- Both plans also edit `tests/optimizer/test_lateral_fetch.py` and
  `tests/test_lateral_pg_parity.py` (merge-level collision beyond Step 1) — same guard applies.

Nothing else in this plan touches
`WindowedPrefetchStrategy.plan`, `attach_windowed_prefetch`'s wrap plumbing, or
`single_parent_fetch.py` — the per-field strategy selector (WS-D) attaches at
`nested_planner.py::plan_connection_relation` (`active_strategy()` call, ~L924), which feedback2
does not touch. Leave a note at the top of feedback2.md? NO — do not edit feedback2.md (another
session's input); the maintainer will see Step 1 already applied.

Internal ordering: WS-A, WS-B, WS-D, WS-E are mutually independent. WS-C depends on nothing here
but is the riskiest recognizer surgery — implement it LAST so a partial landing never blocks the
rest.

---

## WS-A — Count-policy overhaul: stop paying `Count(1) OVER (PARTITION BY)` where a probe or a constant answers

> **As-shipped correction (supersedes the `requires_total_count` /
> `wants_next_page_probe` instructions below).** The follow-up root fix did NOT
> preserve those two members — it removed both. The four-mode policy is now a
> single `FetchMode` enum (`COUNTED | PROBED | CONSTANT_FALSE | NONE`) in
> `utils/connections.py`, resolved by `WindowRangePlan.fetch_mode(has_next_selected,
> total_selected)`; the planner maps `COUNTED -> with_total_count` and
> `PROBED -> next_page_probe`, and the resolver reads the mode's shared shape
> predicates (`WindowRangePlan.probe_shape` / `constant_false_shape`) off the
> rows. The dead `requires_total_count` FIELD and the `wants_next_page_probe`
> METHOD are gone (zero repository readers); `tests/test_keyset.py` was migrated
> to the mode API rather than pinned to the removed field. Wherever the text
> below says "keep `requires_total_count`" or "express it inside
> `WindowRangePlan.wants_next_page_probe`", read it as "resolve it through
> `FetchMode` / `WindowRangePlan.fetch_mode`". The decision-table columns remain
> an accurate record of the PRE-change behavior.

### Verified current decision table (forward unless noted)

Derived from `utils/connections.py::window_range_plan` (~L283-304: `ambiguous = keyset_counted
or is_ambiguous_empty_window`; `is_ambiguous_empty_window = not reverse and (offset > 0 or
limit == 0)`; `requires_total_count = ambiguous or limit is None`; probe honored only on
`plain_first_page`) and `nested_planner.py::plan_connection_relation` (~L894-903:
`with_total_count = range_plan.requires_total_count or total_selected or (has_next_selected and
not next_page_probe)`):

| shape | count today | probe | marker | 2nd (reversed) window |
|---|---|---|---|---|
| plain first:N (offset 0) | only if totalCount selected | if hasNext and not totalCount | no | no |
| offset page (offset>0) | ALWAYS (shape-forced) | never | yes (rn==1) | no |
| first:0 (limit==0) | ALWAYS | never | yes | no |
| unbounded (limit None) | ALWAYS | never | offset>0 only | no |
| reverse last:N | only if totalCount OR hasNextPage selected | never | never | always |
| keyset counted seek | always (inherent) | never | abs-first marker | no |

The waste: offset pages pay the count even for edges-only selections; hasNextPage-only beyond
the plain first page forces the count; reverse pays the count for a `hasNextPage` that is
CONSTANTLY False (last-only pages are the partition tail; `reverse+after`/`keyset+reverse` are
unplannable — `derive_connection_window_bounds` raises UnwindowableConnection).

### A0 — Consolidated fetch-mode policy (the design spine)

Introduce one policy derivation with four modes: `counted | probed | constant_false | none`,
given (shape, total_selected, has_next_selected). Express it inside
`utils/connections.py::window_range_plan` + `WindowRangePlan.wants_next_page_probe` (keep it a
pure function of plan-time inputs) and mirror it in `connection.py::_resolve_from_window`'s
physical-shape inference. `assert_window_fetch_mode` (probe XOR count) stays the invariant and
needs no change.

**Settled derivations (landing-verified — do not re-derive):**

- Planner: `with_total_count = total_selected or limit == 0`. This alone reproduces the whole
  A0 table (first:0 counted; keyset counted seek only fires when totalCount is selected —
  keyset after: hasNext-only already yields probe=True/with_total_count=False, unchanged; the
  `requires_total_count` FIELD keeps its current semantics so `tests/test_keyset.py` ~L609
  survives).
- Resolver: classify `probed | constant_false | counted | none` from
  `(next_page_probe, limit is None, reverse, total present)` for the `has_next_page` fork only.
- **Five docstrings/comments become FALSE after A1 and MUST be rewritten in the same change**
  (AGENTS.md forbids leaving them): `utils/connections.py` ~L152-153 and ~L268-270 ("mutually
  exclusive by construction"), ~L376-380 (`split_window_rows` "XOR" contract), `connection.py`
  ~L446-451 ("mutually exclusive by shape"), and the `assert_window_fetch_mode` docstring ~L312
  ("normalized ... to the plain_first_page shape" -> plain-first OR offset-page). State the new
  contract: probe and markers COMPOSE on the offset page; probe XOR count still holds.

New policy:

- plain first page: unchanged (probe when hasNext-only; count when totalCount).
- offset page (offset>0, bounded limit>0): totalCount selected -> counted. Otherwise ->
  **probed + marker composed** (A1). Shape-forced count is DROPPED.
- first:0: keep counted v1 (its marker IS a would-be sentinel; folding is a later refinement —
  document this choice in the policy docstring).
- unbounded (limit None): totalCount selected -> counted. Otherwise -> **constant_false**
  (a served unbounded forward page ends at the partition's last row; hasNextPage is False by
  construction). Markers unchanged (offset>0 unbounded keeps its marker). NOTE the overshoot
  hole (adversarial finding): the marker-only resolver branch must ALSO serve the count-free
  unbounded offset>0 shape — marker-only + unbounded + count-absent => hasNextPage=False (sound:
  any row with rn > offset would be in the unbounded page, so marker-only proves
  total <= offset). Without this edit every overshot unbounded page silently degrades to
  per-parent fallback.
- reverse last:N: totalCount selected -> counted. Otherwise -> **constant_false** (A2).
  hasPreviousPage already derives from the forward rn (`first_rn > 1`), count-free today.
- keyset counted seek: counted (inherent; pre-seek totalCount cannot come from a probe).

### A1 — Offset-page probe+marker composition

Verified sound (empty partition on page 2 -> resolver's empty branch already answers without the
count; overshot `after:` -> marker-only PROVES total<=offset -> no sentinel -> hasNextPage False,
identical to today's `total > offset` arithmetic; partition ending exactly at offset+limit ->
full page, no sentinel -> False, correct).

Touch set (all verified against current tree):

1. `utils/connections.py::window_range_plan` (~L302-303): allow the probe on the offset-page
   shape. Settled predicate (current L303 is `next_page_probe = next_page_probe and
   plain_first_page and not keyset_counted`):
   `probe_shape = plain_first_page or (not reverse and offset > 0 and bounded and limit > 0)`;
   `next_page_probe = next_page_probe and probe_shape and not keyset_counted`.
   **`not keyset_counted` MUST be preserved** (pinned by
   `tests/test_keyset.py::test_window_range_plan_keyset_counted_suppresses_probe` ~L613).
   `fetch_upper_bound`/`fetch_limit` already generalize (`upper_bound + _probe_increment`,
   ~L189-198) — no math change.
2. `utils/connections.py::WindowRangePlan.wants_next_page_probe` (~L212-237): relax the
   `plain_first_page` gate. Settled predicate (pure method, no new inputs):
   `return (self.plain_first_page or (not self.reverse and self.offset > 0 and self.limit is
   not None and self.limit > 0)) and has_next_selected and not total_selected`.
3. `utils/connections.py::split_window_rows` (~L398-405): today the marker branch returns
   `probe_row_seen=False` unconditionally and would misfile a sentinel as a page row. Add the
   combined branch: page = `offset < rn <= upper_bound`; **`probe_row_seen = any(rn ==
   range_plan.fetch_upper_bound)`** (the sentinel IS `rn == upper_bound + 1 ==
   fetch_upper_bound`; equivalently `rn > upper_bound` — verified: `fetch_upper_bound =
   upper_bound + _probe_increment`); marker = `rn == 1`. **Branch ordering: guard the new
   branch `if range_plan.add_marker_rows and range_plan.next_page_probe:` and place it BEFORE
   the plain `if range_plan.add_marker_rows:` branch, else the plain marker branch shadows
   it.** Boundary tests spelled in row-number VALUES: partition of exactly offset+limit rows ->
   hasNextPage False; offset+limit+1 rows -> True.
4. `nested_planner.py::plan_connection_relation` (~L894-903): replace the current expression
   with the settled `with_total_count = total_selected or range_plan.limit == 0` (see A0) —
   use `range_plan.limit`, NOT the loop-local `limit` (the raw bound can be `sys.maxsize`,
   normalized to None only inside `window_range_plan`; `range_plan.limit` is the unambiguous
   spelling). Do NOT change the `requires_total_count` FIELD's semantics — the planner just
   stops consulting it for the count decision (it stays as-is for `tests/test_keyset.py`
   ~L609 and any other readers).
5. `plans.py::apply_window_pagination`: pure renderer of the flags — verified it already
   composes (`fetch_upper_bound` + marker Q, ~L1044-1063). No structural change; keep
   `assert_window_fetch_mode`.
6. `connection.py::_resolve_from_window` — EXACT inference predicates (do not leave the domain
   boundaries to taste; no tests run to catch a misclassification):
   - probed: `add_marker_rows and offset > 0 and limit is not None and limit > 0 and
     count-absent`.
   - constant_false: `count-absent and (limit is None or reverse)` (covers unbounded forward
     AND reverse; keyset-counted marker shapes are excluded because their count is present).
   - `first: 0` (limit == 0) stays counted — a count-absent limit==0 window must NOT be
     classified as probed; let the drift guard fall back defensively as today.
   - probe re-inference (~L397-408) gains the probed signature above (the documented
     "overfetched OR no observer" disjunction ~L387-396 widens; update that comment). Note
     (from anchoring): at this seam `range_plan` was built without `next_page_probe`, and
     `add_marker_rows` is already True for offset>0 shapes — the re-inference must REBUILD the
     plan with `next_page_probe=True` (as the existing plain-first branch does) so
     `split_window_rows` sees the composed flags.
   - marker-only branch (~L459-484) — SETTLED broader form (landing-verified; the narrow
     probed+unbounded-only version leaves an edges-only offset overshoot silently degrading to
     per-parent fallback, an N+1 regression vs today):
     every count-free marker-only FORWARD shape proves `total <= offset`, so:
     `if total is None: if want_count: return None  # genuine drift` else serve
     `_empty_page_connection(..., has_next_page=False, want_count=False, total=0, ...)`.
     This subsumes the probed and constant_false cases AND the edges-only shape.
   - drift guard (~L498-501): the exemption applies ONLY to the `_has_next_page_requested`
     clause — NEVER the `want_count` clause (count-absent + want_count is always genuine
     drift). Settled form:
     `constant_false = total is None and (limit is None or reverse)`;
     `if total is None and (want_count or (_has_next_page_requested(info) and not
     range_plan.next_page_probe and not constant_false)): return None`.
     The non-empty-page `has_next_page` (~L566) already yields False when total is None —
     constant_false falls out for free there.
7. **Lateral dialect mirror (mandatory, with the exact load-bearing edit)**:
   `lateral_fetch.py::build_lateral_sql`'s rn-filter branch currently binds
   `range_plan.upper_bound` (`f"{bound_column} <= %s"` + `params.append(range_plan.upper_bound)`)
   while the ORM renderer binds `fetch_upper_bound` — today they cannot diverge (probe exists
   only on the plain branch, which reads `fetch_limit`), but after A1 the lateral offset page
   would never fetch the sentinel -> hasNextPage constantly False ON PG ONLY, invisible to the
   SQLite tier. **Switch the rn-filter upper bound to `range_plan.fetch_upper_bound`** and
   confirm the marker OR-composition (`(rn > offset AND rn <= fetch_upper) OR rn = 1`) renders
   identically to the ORM Q. The two-dialect no-drift contract is documented at `plans.py`
   (~L947-950); the PG parity test is the only guard for this.
8. **Existing-pin update sweep (mandatory — these pins hard-code the OLD policy and WILL fail
   otherwise; the "maintainer's run passes fail_under=100" claim depends on this step):**
   - `tests/utils/test_connections.py` ~L415-437 (sweep asserting `not (add_marker_rows and
     next_page_probe)` — now composable), ~L328-350 / ~L353-374 (probe only on
     plain_first_page), ~L468-488 (off-shape probe asserted inert; after relaxation
     `assert_window_fetch_mode` raises for that shape — rewrite the pin to the new contract).
   - `tests/optimizer/test_plans.py::test_next_page_probe_ignored_off_the_plain_first_page_shape`
     + the `with_total_count` matrix pins in that file.
   - `tests/test_relay_connection.py::test_count_less_window_with_count_observer_falls_back_defensively`
     (~L2431) — pins the drift guard A2 relaxes; rewrite to the new exemptions.
   - `tests/test_keyset.py` ~L609 (`requires_total_count is True`) — prefer ADDING a mode layer
     over changing `requires_total_count` semantics so this pin survives; if semantics must
     change, update it deliberately.
   - Live count-policy SQL pins in `examples/fakeshop/test_query/test_library_api.py`
     (~L3330-3773).
   - Closing grep before finishing WS-A:
     `grep -rn "next_page_probe\|add_marker_rows\|requires_total_count\|with_total_count" tests/ examples/fakeshop/test_query/`
     and reconcile every hit against the new policy table. Pre-classified extra hits
     (landing-verified): `tests/optimizer/test_nested_fetch.py` ~L71-82 (probe+count still
     raises — SURVIVES unchanged); `tests/test_connection.py` ~L759/L819 (unrelated to count
     policy — benign); `tests/optimizer/_builders.py` ~L40 (builder default, not a pin — add a
     probed-offset variant for the new package tests); `tests/optimizer/test_lateral_fetch.py`
     + `tests/test_lateral_pg_parity.py` (need the NEW probed-offset/constant-false cases;
     review the existing count-free pins ~L200-247 of the parity file against the widened
     probe). CAVEAT: `test_relay_connection.py`'s drift-guard pin is INVISIBLE to this grep
     (its text contains none of the four tokens) — it survives only because it is listed
     explicitly above; do not treat the grep as a complete completeness gate.

### A2 — Reverse and unbounded constant-False hasNextPage

1. `nested_planner.py` (~L899-903): stop forcing the count for reverse/unbounded when only
   hasNextPage is selected (mode = constant_false).
2. `connection.py::_resolve_from_window`: before the drift guard, add: count-absent + reverse +
   planned shape (offset==0 — the only plannable reverse) => has_next_page=False; likewise for
   the count-free unbounded forward page. Keep BOTH RowNumber windows for reverse (deriving
   forward rn as `total - reversed_rn + 1` would reintroduce the count; verified).
3. The relaxed drift guard converts a safety net into a semantic claim — the parity tests below
   are the gate.

### A-tests (live tier FIRST — staff-bracket idiom per feedback2's substrate audit; there is no
get_queryset-free Relay child in fakeshop, so run as staff against `ShelfType.booksConnection`
and assert SQL shape via `CaptureQueriesContext` + `"OVER ("` / `Count` scans)

- offset page, edges-only: NO `Count(1) OVER` in child SQL; correct page + cursors.
- offset page, hasNextPage-only: no count; probe row honored; hasNextPage true/false at the
  boundary (partition ends exactly at offset+limit -> False; one more child -> True).
- offset page overshoot (`after:` past the end): marker-only, hasNextPage False, empty edges.
- UNBOUNDED overshoot (`after:` past the end with no `first:`): marker-only, count-free,
  hasNextPage False, NO per-parent fallback (assert query count — the adversarial finding-2
  hole, pinned).
- EDGES-ONLY offset overshoot (neither hasNextPage nor totalCount selected, `after:` past the
  end): count-free, served page (empty edges), NO per-parent fallback (assert query count —
  the landing-verifier Gap-6b hole, pinned).
- empty partition on page 2: empty connection, no count, no per-parent fallback (assert query
  count).
- last:N hasNextPage-only: no count; hasNextPage False; hasPreviousPage still correct.
- last:N totalCount: count present, unchanged values (regression pin).
- unbounded, edges+hasNextPage: no count; hasNextPage False.
- first:0: counted, unchanged (deliberate v1 pin).
- shared merged alias: edges-only alias + hasNextPage-only alias of the same field/args share
  ONE window; both resolve correctly (the alias-merge soundness case, `walker.py::
  _merge_aliased_selections`).
- PG parity tier (`tests/test_lateral_pg_parity.py`): windowed vs lateral byte-parity for the
  new probed-offset and constant-false shapes.
- Package tier: `split_window_rows` combined-branch unit matrix; `window_range_plan` mode table
  as a parametrized pin (the table above, post-change).

---

## WS-B — GenericRelation: first-class windowed nested connections (replace the load-bearing accident)

### Verified current state

`utils/relations.py::relation_kind` (~L82-85) classifies GenericRelation via the defensive
`'many'` fallback (one_to_many=True, auto_created=False). `join_taxonomy.py::
classify_relation_join` then yields `windowable=True, partition_expr='+'` (the GenericRel hidden
related_query_name), `parent_join_column=None`, `lateral_shape=DIRECT_FK, parent_link_field=None`
(lateral safely refuses). One verifier executed a live windowed prefetch over fakeshop
`Branch.tags` (with a poison cross-content-type row) and observed CORRECT results — the `'+'`
partition happens to compile to Django's content-type-aware reverse join, and
`GenericRelatedObjectManager.get_prefetch_querysets` re-adds the content_type+object_id filter
at fetch time. A second verifier predicted a FieldError from `'+'`. Either way the behavior is
an UNTESTED, UNPINNED coincidence, plus one real defect: `parent_join_column=None` means
`_project_scalar_only_window` omits object_id/content_type_id from `.only()` -> one deferred-
field refetch PER ROW at prefetch-attach (silent N+1).

**Implementers: first write the pin test and observe which verifier was right; then land the
deliberate mechanics below (which make the question moot).**

### Steps

1. `utils/relations.py::relation_kind`: add an explicit `'generic'` kind, detected duck-typed
   (`hasattr(field, 'content_type_field_name') and hasattr(field, 'object_id_field_name')`)
   BEFORE the one_to_many fallback. COMPLETE kind-plumbing touch list (verified consumers):
   - the `RelationKind` Literal itself (4-member today) gains `'generic'`;
   - `MANY_SIDE_RELATION_KINDS` (frozenset `{"many", "reverse_many_to_one"}`) gains
     `'generic'` — omit this and every GenericRelation list resolver AND connection synthesis
     silently vanishes (`is_many_side_relation_kind` feeds `types/finalizer.py` ~L520,
     `walker.py` ~L187/1021, `filters/sets.py` ~L670, `types/resolvers.py` ~L245/335,
     `types/converters.py` ~L644, `types/base.py` ~L1437);
   - `management/commands/inspect_django_type.py::_RELATION_KIND_LABELS`: add a label for
     `'generic'` (this command was just realigned in commit 939cb755 — update any pinned
     command output: `examples/fakeshop/tests/test_inspect_django_type.py` ~L182,
     `tests/management/test_inspect_django_type.py` ~L480). **PREREQUISITE (root-cause, else
     this label is dead code): `FieldMeta` is a frozen slots dataclass whose
     `relation_kind` property calls `relation_kind(self)` — a duck-typed detector sees no
     `content_type_field_name` on FieldMeta and returns `'many'`. Add
     `content_type_field_name: str | None = None` and `object_id_field_name: str | None =
     None` to `FieldMeta`, populate via `getattr(field, ..., None)` in `_from_field_shape`, so
     both call modes (raw field AND FieldMeta) agree on `'generic'`.** (`is_many_side` stays
     True either way, so the core feature works without this — but the classifier must not be
     left inconsistent.);
   - update the pin
     `tests/utils/test_relations.py::test_relation_kind_classifies_one_to_many_as_many`
     (it deliberately pins the fallback today);
   - `tests/types/test_generic_foreign_key.py`'s existing list-shape pin MUST keep passing
     (the plain list path is unaffected; verify by reading, and extend rather than rewrite).
2. `join_taxonomy.py::classify_relation_join`: add a GENERIC branch:
   - `partition_expr = related_model._meta.get_field(field.object_id_field_name).attname`
     (partition by the object_id COLUMN — the morph type is a WHERE constant, never part of the
     partition; Laravel morphMany precedent).
   - `parent_join_column = <same object_id attname>` (fixes the `.only()` projection N+1).
   - windowable=True (deliberate now); lateral refusal SETTLED: **keep
     `parent_link_field=None`** (lateral already refuses at `_build_lateral_spec` ~L804 when
     `parent_link_field is None`; auto degrades to windowed). Do NOT add
     `LateralJoinShape.GENERIC` — it would force new match arms in the lateral SQL builder and
     recognizer for a shape that never reaches them.
   - Update `WINDOWABLE_RELATION_KINDS` (~L66) for the new kind.
3. `nested_planner.py::plan_connection_relation` (NOTE: the underscore-prefixed name is a
   DIFFERENT function in walker.py), after the final `child_queryset` is built (post ~L818 —
   strictly AFTER the `unwindowable_child_queryset_reason` gate, which cannot reject a
   `.filter()` anyway; the generic kind is known from `join = classify_relation_join(...)` at
   ~L772): inject the
   constant morph predicate via
   `ContentType.objects.db_manager(child_queryset.db).get_for_model(parent_model,
   for_concrete_model=field.for_concrete_model)` — MUST honor the field's own
   `for_concrete_model` semantics or MTI parents mispartition, and MUST resolve the ContentType
   on the CHILD QUERYSET'S database (under FAKESHOP_SHARDED's divergent router the default-DB ct
   pk can differ from the execution DB's; a default-DB constant would silently return zero
   rows).
4. `nested_planner.py::_project_scalar_only_window` (+ `_connector_only_field` seam): include
   BOTH object_id and content_type_id attnames in the scalar-only `.only()` projection for the
   generic kind.
5. Docstring on `plans.py::apply_window_pagination`: document the "window filters, never
   slices" invariant (a sliced-queryset strategy would re-enter Django's
   `_filter_prefetch_queryset` window branch and inherit the upstream duplicate-through-join
   hazard — verified refuted TODAY only because we never slice).

### B-tests

Substrate: fakeshop `Branch.tags = GenericRelation(TaggedItem)` exists
(`apps/library/models.py` ~L42-44); the public schema deliberately does not expose tags
(model comment forbids exposing them), so the live /graphql tier is IMPOSSIBLE here. **Tier
commitment: `examples/fakeshop/apps/library/tests/` in-process (`schema.execute_sync`) with
test-local Node-shaped Branch/TaggedItem types. Do NOT add tags to the public schema to chase
the live tier.** Memory warning: when adding schema modules, grep the whole test tree for
private schema-module tuples and sync every one (recurring cross-test pollution class).

- In-process windowed GenericRelation connection: first:N page + cursors + totalCount
  correct WITH a poison row (same object_id, different content_type) present — the poison row
  excluded (the recon's wrong-data scare, pinned forever).
- hasNextPage probe shape on a generic connection (composes with WS-A).
- Projection pin: scalar-only (pageInfo-only) generic connection triggers NO deferred-field
  refetch per row (assert query count) — the N+1 fix.
- MTI parent variant (for_concrete_model semantics).
- Lateral strategy on a generic connection: degrades to the windowed body (no error), pinned.
- Package tier: `relation_kind` returns `'generic'`; `classify_relation_join` GENERIC descriptor
  fields; updated fallback pin.

---

## WS-C — Lateral strategy: accept single-table visibility WHERE (the biggest real-world coverage win)

> **As-shipped correction (supersedes every `_extract_parent_ids` reference below):**
> the fetch-time recognizer shipped RENAMED as
> `lateral_fetch.py::_recognize_lateral_fetch`, now returning a frozen
> `_RecognizedLateralFetch(parent_ids, visibility_where_sql)` result object (it
> carries the APPROVED compiled visibility `(sql, params)` so the fetch splices the
> exact bytes it proved, with no third recompile). Read every `_extract_parent_ids`
> step below as `_recognize_lateral_fetch`; `_parent_in_values` shipped with the
> keyword `(node, *, column, table)` signature as planned.

### Verified current state

`lateral_fetch.py::_build_lateral_spec` refuses at one combined gate (~L763-771):
`query.where.children or query.select_related or query.annotations or query.extra or
query.extra_tables or query.group_by is not None`. Every fakeshop Relay child type carries a
visibility `get_queryset` (by design), whose filter lands in `query.where.children` — so
**anonymous traffic essentially never gets the lateral strategy today**; it silently rides the
windowed body. Fetch-time Q-to-SQL compilation is available (`build_lateral_sql` runs inside
`_fetch_lateral_rows` with the live connection; the keyset-seek splice at ~L297-314 is the exact
precedent). Plans with a custom get_queryset are already non-cacheable
(`nested_planner.py` ~L808-809: `sub_plan.cacheable = False`), so per-user filter values never
enter the cross-request plan cache.

### Steps

1. **C1 (== feedback2 Step 1, verbatim):** refactor `_parent_in_values(node)` to
   `_parent_in_values(node, *, column: str, table: str)`; update the single production caller in
   `_extract_parent_ids` (~L548) and the five test call sites in
   `tests/optimizer/test_lateral_fetch.py` (~L630-668; the now-dead `spec =
   _build_lateral_spec(...)` assignment at ~L628 goes too).
2. `_build_lateral_spec`: split the combined gate. Allow `query.where.children` ONLY when the
   child WHERE is single-table (inspect the query's alias machinery — refuse when more than the
   base table is used) AND contains no `Exists`/`Subquery`/expression-resolvable quals (an
   alias-count check misses subqueries referencing other tables; refuse them at the SPEC gate in
   v1, not just the recognizer). Also refuse when `query.is_empty()` (a visibility hook
   returning `qs.none()` — plausible "hide all for anonymous" — would otherwise raise
   `EmptyResultSet` at fetch-time compile instead of degrading). Keep refusing select_related,
   annotations, extra/extra_tables, group_by, and expression ordering (v1 scope: plain
   column-qual visibility WHERE only). Carry the pristine filtered child queryset (or a clone of
   its where node + params) on `LateralWindowSpec`.
3. `build_lateral_sql`: compile the carried WHERE via the child query's compiler
   (`query.get_compiler(using=...).compile(where_node)`) and splice `AND (<compiled sql>)` with
   its params into the lateral branch, next to the keyset-seek splice. Wrap the compile in a
   `try/except EmptyResultSet` -> `return None` (degrade to the windowed body) as a second
   safety net behind the spec-time `is_empty()` gate. **Alias gotcha —
   SETTLED (landing-verified):** the child table is aliased `__dst_child` (~L244, ~L276) but
   Django compiles the base quals against the real table name. **Drop the child alias for
   DIRECT_FK**: set the builder's single `child` variable to the real quoted `spec.db_table`
   (unaliased `from_sql`) — every child column ref (select, order, parent-link predicate,
   keyset seek) funnels through that one variable, so everything agrees for free. Do NOT use
   `query.change_aliases` (strictly more surface, alias-bookkeeping drift risk). The
   THROUGH_TABLE branch keeps its alias (needs disambiguation) — v1 visibility WHERE is
   DIRECT_FK-only anyway. **Novel-technique flag:** compiling a WhereNode in isolation via
   `query.get_compiler(...).compile(where_node)` has NO in-repo precedent (the keyset splice
   renders column refs directly); the implementer MUST empirically validate the compiled
   `(sql, params)` references the base table by real name before wiring it in.
4. `_extract_parent_ids`: extend the fail-closed recognizer — the planned windowed body carries
   the same visibility quals in its base WHERE, so match the fetch-time residue structurally
   against the spec-carried expected quals (model on `_keyset_seek_quals_match`, ~L579-641), and
   do NOT double-apply: the spec-side splice renders the quals in the SQL branch, and the
   recognizer consumes (expects exactly once) the matching residue from the ORM tree. ANY qual
   not provably the planned residue -> `return None` (windowed body runs). This is the
   correctness cliff of the whole workstream: matching too loosely can double-apply or drop a
   filter. Strict fail-closed default, no fuzzy matching. **Matching mechanism SETTLED
   (landing-verified — `_keyset_seek_quals_match` is a shape-specific template that does NOT
   generalize to arbitrary column quals): compile BOTH the residual unrecognized nodes and the
   spec-carried planned WHERE via the same compiler (against the unaliased real table name per
   step 3) and require byte-equal `(sql, params)`; consume iff equal, else `return None`. Do
   NOT attempt WhereNode/Lookup `__eq__` (identity-based) or a shape-specific matcher.**
5. Update the module docstring's refusal-matrix documentation.

### C-tests

- Live PG-parity tier: ANONYMOUS fakeshop traffic over a lateral-strategy connection now takes
  the lateral path (SQL scan: `LATERAL` present) and returns byte-identical
  rows/cursors/pageInfo to the windowed strategy (reuse `_assert_parity` /
  `build_strategy_schema` helpers in `tests/test_lateral_pg_parity.py`).
- Visibility semantics pin: anonymous vs staff see different rows through the lateral path
  (filter applied EXACTLY once — a double-apply would be invisible on idempotent filters, so
  pin with a count-sensitive filter if available, else assert the compiled SQL contains the
  predicate once).
- Refusal matrix (package tier): multi-table WHERE (join traversal in get_queryset) -> spec
  refused, windowed body; annotations/select_related/extra still refused; unrecognized fetch-
  time residue -> degradation, correct data.
- `_parent_in_values` keyword-signature units (C1).

---

## WS-D — Strategy ergonomics: per-field strategy override + index advisory

### D1 — Per-field `nested_strategy` optimizer hint

join-monster precedent (per-field strategy knobs); verified seam:

1. `optimizer/hints.py::OptimizerHint`: add `nested_strategy: str | None = None` (frozen
   dataclass; `__post_init__` validates mutual exclusion with skip/prefetch_obj and validates
   the name by routing through `nested_fetch.py::resolve_strategy` (~L273) for typo-loud
   ConfigurationError parity). Add the factory helper matching the existing hint constructors.
2. `nested_planner.py::plan_connection_relation` (~L924): replace `strategy =
   active_strategy()` with a resolver that first consults the connection field's hint. Caveat
   (verified): the walker takes the connection branch (~walker.py L487-501) BEFORE per-field
   hint application, so `plan_connection_relation` must look up
   `hints_map.get(relation_field_name)` itself — **`hints_map` is already a local variable in
   that function** (computed at the `resolve_optimizer_hints(definition)` call, ~L632); no
   threading or re-resolution needed. Add `resolve_strategy` to the existing
   `from .nested_fetch import (...)` block. In `OptimizerHint.__post_init__`, route the name
   validation through a LAZY `from .nested_fetch import resolve_strategy` (matching the
   codebase's lazy cross-module idiom; `__post_init__` runs at Meta-build time, not import
   time). Mutual exclusion: reject combining `nested_strategy` with `skip`, `prefetch_obj`,
   AND `force_select` (a connection is always a prefetch; forcing select is incoherent);
   `force_prefetch` + `nested_strategy` is redundant-but-harmless — allow it.
3. NO plan-cache-key change — the knob is schema-static and the cache is instance-bound
   (extension.py Decision 11). State this in the hint's docstring so reviewers don't
   re-litigate. NEVER let strategy selection depend on request-varying data outside the cache
   key.

### D2 — Composite-index advisory (dev-mode) + docs

Verified: no consumer-facing indexing guidance exists anywhere in docs/README, and the PG tier
memory already recorded "lateral needs a page-order index" empirically.

1. Small helper — SETTLED home: `nested_planner.py` (the call site is anchored at the
   per-window strategy dispatch in `plan_connection_relation`; keeping the helper in the same
   module avoids a new cross-module seam) — called once per planned window
   (plans are cached per extension instance, so once per plan shape): prefix-match
   `related_model._meta.indexes` + field-level `db_index`/FK auto-index for
   `(partition column, order columns...)`; `logger.warning` gated on `settings.DEBUG`, else
   `logger.debug`. Advisory ONLY (DBAs create indexes outside Meta; expression indexes have no
   `.fields` — stay silent on those, never false-positive loudly, never raise).
2. Docs: add a "Nested connection indexing" note — composite `(parent_fk, order columns...,
   pk)` for windowed AND lateral; keyset composite mirroring `keyset.py::keyset_seek_q`'s
   redundant-leading-bound design. Place it in the optimizer module docstring
   (`optimizer/__init__.py` or `nested_fetch.py` module docstring) + a short README section
   WITHOUT cross-file links (avoids the reference-style link ceremony); do NOT touch
   GLOSSARY.md/TREE.md (generated).

### D-tests

- Package tier: hint validation matrix (bad name -> ConfigurationError; mutual exclusion).
- Live tier: a test-local type pinning `nested_strategy="windowed"` on one field under a
  lateral-default extension takes the windowed path (SQL scan) and vice versa.
- Advisory helper: unit matrix (index present/absent/expression-only/FK-auto-index) with
  `caplog`.

---

## WS-E — Small verified hardening

1. **Nullable-unique tiebreaker** (`plans.py::ends_in_unique_column`, ~L782-821): a terminal
   `unique=True` column that is NULLABLE is accepted as a total order today, but SQL UNIQUE
   permits multiple NULLs -> nondeterministic ties. Settled edit (the local var is
   `field_obj`): `return bool((getattr(field_obj, "unique", False) and not field_obj.null) or
   getattr(field_obj, "primary_key", False))`. Grep fakeshop models for any nullable-unique
   terminally-ordered column before assuming no SQL pins churn. Risk (accepted): emitted SQL/cursors change for
   that shape — cursor parity holds because both pipelines share `deterministic_order`; update
   any pinned SQL snapshots that churn.
   Test: model with a nullable unique field ordered terminally -> pk appended (package tier;
   fakeshop has no such column — if none exists, use a test-local model or the existing
   package-tier model fixtures).
2. **Distinct gate pin**: a target `get_queryset` returning `.distinct()` must produce ZERO
   window prefetches (strictness-visible per-parent fallback) — pins the verified
   unreachability that killed the strawberry-django `remove_window_pagination` port.
3. **Keyset projection pin**: nested keyset connection whose node selection does NOT select the
   cursor_field columns -> no lazy-load per edge (pins `_extend_only_projection`, the verified
   already-implemented parity that killed the `annotate_ordering_fields` port).
4. WS-B step 5's invariant docstring rides here if WS-B is somehow descoped.

---

## Deliberately NOT doing (verified refutations — do not re-chase)

| Idea (recon source) | Why dead |
|---|---|
| Port strawberry-django `remove_window_pagination`/distinct count fallback | `.distinct()` can never reach `apply_window_pagination` (gated at `unwindowable_child_queryset_reason`); would be dead code |
| Port MrThearMan/undine `_filter_prefetch_queryset` monkeypatch | Targets Django's SLICED-prefetch path; we window via filters, never slices — unreachable (docstring invariant added in WS-B instead) |
| Port strawberry-django `annotate_ordering_fields` un-defer trick | `_extend_only_projection` + `_project_scalar_only_window` already guarantee it at every seam (pin added in WS-E) |
| undine `should_promote_to_prefetch` | `walker.py::plan_relation` already downgrades ANY relation with a custom get_queryset to Prefetch, force_select included |
| undine single-Q filter collation | Every framework `.filter()` is on local columns/annotations; the single-Q pattern is already house style (`plans.py` range_q) |
| Grafast-style sibling dedup | `_merge_aliased_selections` already merges identical-arg aliases into one window (pagination-normalized comparison) |
| MrThearMan CASE-expression slice bounds | Our nested args are per-field constants; CASE-on-count would FORCE the count onto the count-free reverse shape — regression |
| ent-style plan-time oneNode | Parent cardinality is not visible at the planning seam; feedback2's fetch-time len==1 is the sound owner |
| Accept caller-sliced child querysets | A global slice reinterpreted per-partition is a silent semantics change; honest per-parent fallback is better |
| DISTINCT ON first:1 fast path | Incompatible with the probe (fetch_limit==2); in-branch `ORDER BY ... LIMIT 1` lateral already early-stops on the index |
| PG15 run-condition cost heuristic | Dominant lateral shape is run-condition-independent; untestable branch under fail_under=100 |
| SQLite correlated-JSON third strategy (Drizzle) | Architecture seam is clean but scope is a lateral_fetch-sized module + JSON type-fidelity matrix benefiting only the test backend — own card, not this program |
| JSON-agg terminal strategy (Prisma/Hasura) | Flat annotated rows feed Django model instances natively; JSON costs hydration fidelity; revisit only as an opt-in card |
| Per-instance result caching | MrThearMan removed theirs (60% of request time, issue #86); decisive cautionary tale |
| after+last window enablement | Pulls against the count-reduction program (needs a forced count); separate low-priority idea |
| Backward keyset (`before:`/`last`+`after`) | Real gap but a deliberate feature slice with its own cursor math — own card |
| MTI-aware lateral join | Downgrade is safe today; own card |

## TODO anchors (placed 2026-07-17, comments-only, ruff-clean)

24 `TODO(optimizer-improvement-plan WS-x ...)` anchors are in the source at every seam above —
navigate by `grep -rn "TODO(optimizer-improvement-plan" django_strawberry_framework/`. Each
implementer REMOVES the anchor(s) for a step in the same change that ships the step (AGENTS.md
TODO convention); no anchor may survive the program. Anchoring re-verified every seam against
the tree (zero mismatches) and confirmed the feedback2 session has still not run.

## Verification (final gate for THIS program)

1. `uv run ruff format .` + `uv run ruff check --fix .` after every edit; run
   `scripts/check_trailing_commas.py` mentally via the trailing-comma rules (>=4 items, 2 for
   models.py); ASCII-only in .py.
2. Do NOT run pytest/coverage (explicit instruction). Tests are WRITTEN to the tier map above
   so the maintainer's run should pass fail_under=100: every live-reachable line earned in
   `examples/fakeshop/test_query/`, refusal branches in package tier.
3. NO commit. Leave the tree dirty. Do not touch the maintainer's dirty hunks
   (connection.py `_pipeline_async` region, permissions/querysets files, docs/dry).
4. Sanity greps before finishing: no raw `path:NN` refs in code comments/docstrings; no
   `Co-Authored-By` anywhere; no new settings keys beyond what shipped features read.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
