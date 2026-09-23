# Build: `DjangoListField` argument surface (`offset`, `limit`, and `orderBy`)

Spec: [`docs/spec-050-list_field_arguments-0_0_15.md`][spec-050]
Rationale: [`docs/spec-050-list_field_arguments-0_0_15-rationale.md`][spec-050-rationale]
Target release: `0.0.15`
Status: Closed. The gate, the review and the evidence-only follow-up are recorded under
`## Closing record`; this paragraph and `## Final gate record` keep the candidate's own text.
The candidate tree is the implementation commit of spec Decision 22: the
production and test changes, the shipped docs, the board's DONE transition, the spec status and
every generated output are in it, and it is the tree every gate result and review conclusion
must name. The candidate is no longer a single commit: it is the commit carrying this
reconciliation on top of nine that landed after the first candidate tree was written - the one
that canonicalized the default policy path, so a policy taken without a consumer override is
the same object a declared one resolves to, and closed `ErrorPolicy` to exact-type strings; the
one that moved the post-`OrderSet` seal into `utils/querysets.py` and routed the connection
field's order arm through it; the one that refused a sliced child on a plain list relation with
the typed defect under the walker's own child policy; the one that added the `FilterSet` return
seal to card `TODO-ALPHA-053-0.0.15`; the one that stopped the list-field async adapter
test committing its seed rows; the one that sealed the `FilterSet.apply_*` return itself at
both connection pipelines through the same shared post-sidecar seal the `OrderSet` return
answers to, selecting the list field's argument-path visibility policy whenever a sidecar input
is present; the one that carried every sync defect shape across both async sidecar arms,
answering the sync-only awaitable-in-sync row with the two shapes only an async seam can
produce and reading the disposal the seal performs on a residual awaitable rather than
following it; the one that moved the repeated message-fragment assertion loops out of the
parametrized connection malformed-result bodies into two named helpers, one owning the prefix
and fragment checks and one adding the containment clauses the async arms carry under the
error-policy pass-through, leaving the `ids=` matrices and the per-row message prefixes
unchanged; and the one that covered the forward resolver's slow-path visibility re-check with
three live rows - the arm reached when strictness is armed on the execution frame but the walker
planned nothing, so the relation is outside the optimizer's scoped set and a consumer
`select_related` has already loaded the target. They are named by content here because a tracked
record cannot name the commit that contains it; the evidence-only follow-up writes the commit
ids, naming the complete parent chain from the first candidate tree to the gated commit. That
chain also carries another session's concurrent work on this checkout - the optimizer test
tier's app-registry isolation and its relation planning over real board and library models -
named by content under the same convention, although those commits are ancestors this record
could name by id. It is present in whatever tree gets gated, it is not this card's deliverable,
and it is not what a gate result certifies about spec-050. Its gate, review and
evidence-only follow-up are recorded under `## Closing record`. What the gate covers, beyond
the five slices:

- the policy-authority remediation - the object every bound is read from is no longer
  reachable from any consumer-visible name, a policy subclass is canonicalized at schema
  construction, and the two pre-parse document bounds are stated as request-level;
- the accepted-configuration work - a schema's extension entries are authenticated per entry
  rather than by the carrier holding them, and an entry no weak reference can be taken of is
  answered through an interpreter-owned immutable binding;
- the operation-state boundary - one state per resolved framework extension per runner, bound
  by the package runner around the operation, result collection, every streamed frame and
  every resumption of a streamed result;
- the revocable-lease work - every operation-lifetime value a copied context can hold (the
  runner scope, the armed resource budget, the optimizer's execution frame) is reached
  through a lease its scope closes, so a task that outlived its request reads none of them;
- the resolved-chain admission - factory invocation and member typing are one transaction,
  and an invalid population fails closed on the wire with the stable schema-configuration
  code;
- the enforcement-authority ownership - the resource-policy and error-policy extensions are
  built per operation from the schema's construction record rather than resolved out of the
  extension entries, a direct entry of either kind is a declaration folded into that record,
  a subclass of either is refused at construction and a factory resolving to either refuses
  the operation ([`spec-050`][spec-050] Decisions 14 through 16, which also own the
  operation-state and lease lifetimes above);
- the refusal boundary - a refused configuration is published before the parse stage and the
  parse is answered with a package document, a package operation selector and a package
  snapshot of the transport's allowed-operation policy, so a malformed request, an
  `operationName` no document can carry and a one-shot `allowed_operation_types` iterable all
  get the same stable code on the synchronous, awaited and streamed paths; the refused chain
  keeps the package's resource extension so its pre-parse token and depth scan still bounds
  what the schema is sent, and a transport policy that genuinely allows nothing still gets
  upstream's own operation-type refusal ([`spec-050`][spec-050] Decisions 17 and 18);
- the execution-mode ownership - which GraphQL executor drives an operation is carried from
  the entry point into the chain and bound by the runner for the operation's whole lifetime,
  so a synchronous operation started inside an asynchronous one refuses at the field that
  would otherwise have handed the synchronous executor a coroutine, and a plain
  `strawberry.Schema` is stated as retaining ambient dispatch ([`spec-050`][spec-050]
  Decision 19);
- the resume-scoped budget binding - an operation's budget stays armed for the operation and
  bound only while a task is driving it, so between two streamed frames the driving task
  answers from its enclosing operation or from nothing;
- the raw-list row-source ownership - the universal non-Relay row ceiling is applied only to a
  value this package owns the slice of, so an exact queryset keeps its SQL `LIMIT`, a
  `QuerySet` subclass is rebuilt through the shared sealer and sliced there or refused with a
  typed configuration error, and an object that merely claims through `__class__` to be a
  queryset reaches the counting arm instead; the generated many-side relation resolver reaches
  that seam on its no-custom-visibility branch and normalizes the relation cache before reading
  the rows it holds ([`spec-050`][spec-050] Decision 8, with the two new Definition-of-done
  rows it earns).

The predicted files gain
[`examples/fakeshop/test_query/test_resource_policy_api.py`][fakeshop-test-resource-policy] for
the live hostile-relation rows on both transports. The prefetch-seal row is proven live through
a fixture the candidate carries: `BranchNote` in
[`examples/fakeshop/apps/library/models.py`][fakeshop-library-models] with its migration
[`0005_branchnote.py`][fakeshop-library-migration-0005], the `ProxyBranchType` and
`BranchNoteType` surfaces in [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema],
the app-model rows in [`apps/library/tests/test_models.py`][fakeshop-library-test-models], and the
live rows in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library], with
both SQLite databases carrying the migration. The migration is a new tracked path, so the
tracked-path constants and the generated tree move with it and are regenerated on the candidate.
The offset guard's ordering classifier certifies only named forms: transparent compositions,
readable leaves, the `F` and `Q` reference forms, and exact-type approved Django functions,
aggregates, transforms and lookups, with a relation string expanded into the related model's
default and both sides of a predicate read. Which arm a term takes is decided by
`resolve_expression`, the order the compiler dispatches in, and every custom or subclassed
node is refused - a subclass of `F` or of `Q` for the resolution it substitutes, as a subclass
of an approved function is for the SQL it substitutes ([`spec-050`][spec-050] Decision 6).

## Pre-flight baseline
- Baseline check: clean (`git status --short` empty at pre-flight).
- Static inspection tool smoke test: passed (`scripts/review_inspect.py django_strawberry_framework/list_field.py --output-dir docs/shadow --stdout`).
- Spec glossary consistency check: passed (43 terms checked, exited 0).
- Spec rationale extraction: completed by Worker 1.
  - Spec byte count before: 147,842 bytes (2,056 lines)
  - Spec byte count after: 141,617 bytes (1,979 lines)
  - Rationale byte count: 20,524 bytes (342 lines)
  - Subject of those three figures: the pre-flight tree, measured before any slice ran. They
    are not measurements of the candidate, whose own counts are taken at the candidate parent.

## Slices

- [x] **Slice 1 — argument normalization and typed runtime rejection**
  - [x] `django_strawberry_framework/list_field.py` synthesizes `offset: Int` and
        `limit: Int` on every `DjangoListField`; both are nullable and optional.
  - [x] A package-owned `ListArgumentError` rejects negative and over-ceiling runtime
        values with stable `extensions`; GraphQL's standard `Int` coercion owns wire type
        rejection before the resolver.
  - [x] That class is exported from `django_strawberry_framework/__init__.py`, and
        `tests/base/test_init.py`'s pinned `__all__` tuple, star-import row, and
        export-identity row are updated with it; the version literal and its own assertion
        stay with card 053.
  - [x] Argument wire names are resolved only while building an error, never on a successful
        request.
  - [x] The offset ceiling is `ResourcePolicy.max_list_rows`; no setting key is added.
  - [x] Error payloads derive argument names from the active Strawberry schema rather than
        assuming the default camel-case converter.
- [x] **Slice 2 — Meta-derived `orderBy` and list pipeline**
  - [x] A target carrying `Meta.orderset_class` gains nullable, optional
        `orderBy: [<OrderSet>InputType!]`; a target without that sidecar does not publish a
        meaningless order input.
  - [x] Sync and async paths run visibility, then `OrderSet`, then the offset/order guard,
        then the one raw-list slice.
  - [x] The result of a public `OrderSet.apply_*` override is validated as an unevaluated,
        unsliced, non-projection, non-combined model queryset before the final window; the
        seal gains the new `unevaluated` option, reuses the shipped `reject_combined` one,
        and both new-to-this-boundary codes gain arms at the two visibility message sites.
  - [x] Nonzero offset requires a materially active `orderBy` or still-effective model
        `Meta.ordering` on the post-visibility queryset; no pk tiebreaker and no `DISTINCT`
        are injected.
- [x] **Slice 3 — SQL and unit contracts**
  - [x] `tests/test_list_field.py` pins signature shape, cap arithmetic, direct-call
        runtime errors, helper mechanics, model-ordering state, and no-argument SQL
        parity; wire-reachable sync and async wrapper behavior stays in the live tier.
  - [x] Remove adapter-relevant `DJANGO_ALLOW_ASYNC_UNSAFE` setup from existing package
        tests so it cannot mask a regression in safe async queryset completion; retain an
        override only where a separately named legacy behavior genuinely still requires it.
  - [x] Order input construction continues to use the shipped `OrderSet` factory and orphan
        ledger rather than a list-field-specific input class.
- [x] **Slice 4 — live acceptance**
  - [x] A dedicated `examples/fakeshop/test_query/test_list_field_api.py` drives the sync
        surface over `/graphql/`: ordered offset pages, `orderBy` lists,
        visibility-before-order, limit/cap/error cases, converter naming, and the exceptional
        holder-mounted source shapes. It is the sync counterpart of the async suite rather
        than nineteen more rows inside the broad library application suite.
  - [x] `examples/fakeshop/test_query/test_resource_policy_api.py` pins request-policy
        narrowing over the same field surface.
  - [x] A test-local `AsyncDjangoGraphQLView` mount proves safe async queryset completion,
        configured argument names, async iterable cleanup, and async pipeline parity over
        HTTP without `DJANGO_ALLOW_ASYNC_UNSAFE`.
  - [x] Add the new async live-test path to the card's predicted files, then regenerate the
        tracked-path constants after the path is in the index so governance sees the file.
  - [x] Add the new suite and its shared-helper exemption to
        `examples/fakeshop/test_query/README.md`.
- [x] **Slice 5 — documentation fold-in**
  - [x] Update the list-field docstring and the shipped-surface descriptions in
        `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, and `README.md` where the new
        arguments are enumerated.
  - [x] Update `ResourcePolicy` and bounding-helper docstrings to distinguish returned/skip
        ceilings from total database rows scanned.
  - [x] Update the KANBAN database and the current-checkout statements in `TODAY.md` when the
        candidate implementation commit carries the final board transition; the board moves to
        `done` with its transition row, `TODAY.md` drops the three statements that divergence
        falsified, and the generated exports are rebuilt from the carved database.
  - [x] Leave the version literal, version assertion, package-version glossary row, release
        wording, and `CHANGELOG.md` to card 053's joint cut; `pyproject.toml` and `uv.lock`
        have no duplicate root-package version to bump.
- [x] **Cross-slice integration pass (Worker 1)**
- [x] **Final exact-commit gate** — run against `2c66416e`; the figures are under
      `## Closing record`.

## Final gate record

The gate is recorded under `## Closing record`. The candidate tree now exists - this commit,
standing on the default-policy
canonicalization with its exact-type `ErrorPolicy` strings, the connection `OrderSet` seal, the
plain-list-relation sliced-child refusal, the card-053 `FilterSet` seal row, the list-field
async adapter test that no longer commits its seed rows, the `FilterSet.apply_*` return
sealed at both connection pipelines by the shared post-sidecar seal, with the list field's
argument-path visibility policy selected whenever a sidecar input is present, both async
sidecar arms carrying every sync defect shape with the residual awaitable's disposal read, the
two named helpers the connection rejection assertions now state their claim through, and the
three live
rows over the forward resolver's slow-path visibility re-check - and a tracked record cannot
name the commit that contains the record itself, so the figures, and the commit ids of the nine
it stands on, belong in the follow-up described below and nowhere else; the follow-up names the
complete parent chain from the first candidate tree to the gated commit, including the two
concurrent optimizer commits the chain carries and this card does not own. The prior close
evidence stays superseded because it did not identify the
tree that the full suites and review actually covered.

The close uses two commits:

1. The candidate implementation commit contains all production and test changes, shipped docs,
   the final board/database transition, the spec status, and generated outputs, and it carries
   this record's reconciliation with the six commits above. It atomically carries the board's
   DONE state. Its commit id is the exact tree for every default, sharded,
   supported-floor, structural, link, citation, tracked-path and adversarial-review result, none
   of which has been produced against it.
2. After a green gate and a review that admits no finding under Decision 20, an evidence-only
   follow-up commit changes this build record alone. Its parent must be the gated candidate; the
   record must name that parent, list the commands and results, and say that the follow-up's
   structural checks do not turn it into the full-suite tree.

The candidate's DONE board state is not treated as closure evidence until the exact-tree gate,
review and evidence-only follow-up are complete. No result from another tree is carried forward
as current evidence, and a suite run on the working tree that produced this commit is a run on
another tree.

### Board database state

The tracked SQLite file is one binary, so Git cannot stage card-owned tables separately from a
concurrent owner's rows. The candidate's database is therefore CARVED rather than staged: it is
`HEAD`'s blob with card 050's own rows applied to it and nothing else -

- `kanban_card` id `73`: status `wip` to `done`;
- `kanban_carditem` id `1519`: the last incomplete definition-of-done bullet, complete;
- `kanban_cardtransition`: one new row recording the move, with its uuid-registry row and the
  table's sequence bump;
- `glossary_glossaryterm` ids `583`, `584` and `585`: the three terms this card ships - the
  list-argument rejection, the async queryset completion adapter and the offset order
  precondition - from `planned for 0.0.15` to `shipped`, with the two bodies that read as
  future work restated in the present.

The kanban and glossary tables were identical between `HEAD` and the concurrent working copy
before the carve, so no concurrent row could ride along: a per-table `.dump` comparison against
`HEAD` shows differing lines in those tables alone, and `PRAGMA integrity_check` and
`PRAGMA foreign_key_check` both pass on the result. Card 050's other glossary bodies were
already committed at `HEAD` in `glossary_glossaryterm` ids `442`, `455`, `459`, `465`, `507`
and `553`, so the carve adds nothing there.

The concurrent owner's library, auth, session, products and migration rows stay in the working
copy and are not in this commit. `KANBAN.md`, `KANBAN.html` and `docs/GLOSSARY.md` are
regenerated from the carved database and `docs/TREE.md` re-renders byte-identical; the same
card-owned rows were then applied to the shared working copy, so a render from either database
produces the same bytes and the concurrent owner cannot revert the transition by regenerating
from the checkout they hold.

### Floor-verification scope

[`docs/builder/BUILD.md`][build-md] `## Floor verification` owns the venv recipe and the
floor pins; the scope is this plan's to declare, and it is the set of modules whose seams this
card actually moved - every Strawberry-internals and queryset-compilation boundary it touched:

`tests/base/test_init.py`, `tests/test_list_field.py`, `tests/test_connection.py`,
`tests/test_relay_connection.py`, `tests/test_keyset_connection.py`, `tests/orders/test_sets.py`,
`tests/utils/test_querysets.py`, `tests/optimizer/`, `tests/test_relay_node_field.py`,
`tests/test_registry.py`, `tests/types/`, `tests/test_resource_policy.py`,
`tests/test_graphql_core_patches.py`, the four suites the enforcement, operation-state and
execution-mode architecture added or rewrote - `tests/test_schema.py`,
`tests/extensions/test_operation_state.py`, `tests/utils/test_execution_mode.py`,
`tests/test_error_policy.py` - and the eight live modules
`examples/fakeshop/test_query/test_list_field_api.py`,
`examples/fakeshop/test_query/test_list_field_async_api.py`,
`examples/fakeshop/test_query/test_products_visibility_api.py`,
`examples/fakeshop/test_query/test_keyset_api.py`,
`examples/fakeshop/test_query/test_resource_policy_api.py`,
`examples/fakeshop/test_query/test_error_policy_api.py`,
`examples/fakeshop/test_query/test_connection_pagination_api.py` and
`examples/fakeshop/test_query/test_multi_db.py` - the last two because the post-sidecar
seal now runs at the connection field, so its live malformed-result matrices for both public
sidecar methods, the `OrderSet` one over both pipelines and the `FilterSet` one over the async
pipeline against a real `filter:` argument, and its sharded
routing rejection are this card's rows too - plus the prefetch-seal fixture's two
modules `examples/fakeshop/apps/library/tests/test_models.py` and
`examples/fakeshop/test_query/test_library_api.py`, the second of which also carries the
plain-list-relation sliced-child refusal.

`tests/utils/test_querysets.py` and `tests/optimizer/` already stand in the package half of
this set and are where the shared seal's own rows and the walker's child-policy rows live;
`django_strawberry_framework/utils/querysets.py` is the module those rows cover.

That is twenty-seven paths: seventeen package modules or directories, the eight live modules and
the two fixture modules. A
floor run that narrows this set is not this card's floor verification. The `Schema.stream` rows
in the four architecture suites skip below strawberry-graphql 0.319.0 by their own gate, so a
floor run reports them as skips, not as absent. The shared `.venv` is
read back afterwards and must be unmutated.

### What each proof fails on

A passing row is evidence only where the mutation that breaks it is known. Each entry names the
single change that turns its row red; each was applied, probed, reverted, and the restore
verified by byte compare.

| Row | Fails when |
| --- | --- |
| `tests/test_resource_policy.py::test_bounded_rows_async_lets_a_cancellation_during_cleanup_reach_the_task` | [`django_strawberry_framework/resource_policy.py::_is_cleanup_diagnostic`][resource-policy] answers `True` for every `BaseException`. Observed: the cancelled task finished carrying `ValueError: source failed` with the note `bounded_rows_async iterator cleanup failed: CancelledError()` |
| `tests/test_resource_policy.py::test_cleanup_rejected_async_iterable_lets_a_cancelled_acquisition_through` | the acquisition catch notes a control signal instead of re-raising |
| `tests/test_resource_policy.py::test_the_exported_raw_list_bound_takes_no_client_window` | the coordinate pair is put back on the exported signature |
| `examples/fakeshop/test_query/test_list_field_async_api.py::test_async_deadline_rejection_closes_the_source_it_never_advanced` | the bound's rejection is not routed through the shared cleanup utility. Observed: both window ids reported `aclose=0` while still rejecting |
| `examples/fakeshop/test_query/test_list_field_async_api.py::test_async_offset_accepts_extra_ordering_over_a_dormant_random_order` | the `extra_order_by` branch leaves [`django_strawberry_framework/list_field.py::_selected_ordering`][list-field]. That ONE mutation also flips its control, `::test_async_offset_rejects_extra_random_ordering_over_a_stable_order` - both verdicts from one change |
| `tests/test_connection.py::test_the_optimizer_plans_a_relation_without_reading_the_target_class` | for the hook-bearing ids, [`django_strawberry_framework/optimizer/walker.py::_plan_prefetch_relation`][walker] or [`django_strawberry_framework/optimizer/nested_planner.py::plan_connection_relation`][nested-planner] stops forwarding `target_model`; the two are disjoint, which is why the vocabularies are parametrized apart. For the default-hook ids, either cache-transition tuple is dropped back to a bare second execution |
| the sync and async random-order guard rows | the classifier reads the two explicit collections instead of the selected one, or unions them instead of selecting |
| the planned-visibility rows in `test_products_visibility_api.py` / `test_keyset_api.py` | `_target_has_custom_get_queryset` is forced `False`. Their staff siblings are CONTROLS and stay green under it by design |

One mutation is worth keeping by name. Neutering the offset guard AND making the seal's rebuild
drop `extra_order_by` served the request as `ORDER BY RAND() ASC LIMIT 1 OFFSET 1`, returning
`Alpha` - a page in a re-shuffled order that a row-value assertion alone passes one time in
three. That run is what exposed an instrument defect in the suite's own must-not: Django spells
a random order `RAND()` on SQLite and MySQL and `RANDOM()` only on PostgreSQL
(`django/db/models/functions/math.py::Random`), so an assertion written against the PostgreSQL
spelling cannot fail on the tier the default suite runs. Both suites now read the
vendor-independent prefix through a named constant carrying that reason.

### Sweeps for siblings of the last round's findings

Each finding was swept for the defect class rather than the instance. All five came back clean,
so a later round re-running them is re-deriving a known answer:

| Sweep | Population | Result |
| --- | --- | --- |
| Swallowing `except BaseException` in an async function | 120 swallowing handlers package-wide | all 31 in async code already carry an `except (asyncio.CancelledError, KeyboardInterrupt, SystemExit): raise` guard; the other 89 are sync hostile-input hardening with no await point |
| Query-capture instruments inside async tests | every async `test_*` in the repo | none besides the row under review; no other async SQL assertion was silently reading an empty capture |
| Module docstrings carrying a frozen test count | every docstring in the four test trees | `tests/test_list_field.py` was the only one |
| `for` loop over asserted states in a test body | 17 in this card's six modules | 16 are censuses over equivalent inputs; one sequential loop whose second iteration depended on the first, now spelled apart through `tests/test_connection.py::_planned_relation_request` |
| The 1-microsecond deadline idiom | `examples/fakeshop/test_query/test_resource_policy_api.py`, `tests/forms/test_resolvers.py` | both sync, both separated from the seam by a full parse-and-validate rather than one resolver return, so the "never crosses an await" defect does not apply to either |

### Definition reads, measured

The read-once contract was measured with a metaclass counter armed across factory construction,
schema construction and a real request, with the target switched to a DECOY definition over
another model the moment the accepted read is taken - so a residual read shows up as rows of the
wrong table, not merely as a tally.

| Path | Construction | Schema build | Request |
| --- | --- | --- | --- |
| default `DjangoListField` | 1 | 0 | 0 |
| consumer-`resolver=` `DjangoListField` | 1 | 0 | 0 |
| root `DjangoConnectionField`, cold cache | 1 | 0 | 0 |
| root `DjangoConnectionField`, warm cache | 1 | 0 | 0 |
| synthesized relation connection | 0 | 0 | 0 |

The relation row's zero is not an absence of reads during finalization: the one read counted
there is the finalizer's own Relay composite-pk gate
([`django_strawberry_framework/types/relay.py::_check_composite_pk_for_relay_node`][relay]),
which runs over every Relay type and is not this field. A future counter that sees it should not
treat it as a regression.

### A recorded gate figure that did not reproduce

An earlier round of this cycle recorded `7601 passed, 40 skipped` as a green full sweep. Re-run
over the same worktree it reported `7 failed, 7629 passed, 40 skipped`. The seven also failed at
the implementation commit itself, so the remediation pass introduced none of them: the recorded
line was WRONG rather than stale, and a gate figure in a build record is a claim like any other.

Attributing them took a method worth keeping. Run the failing selection in a detached
`git worktree` checkout of the commit under test, with that checkout forced onto `PYTHONPATH` -
without it the editable install resolves the package back to the dirty main checkout and the
comparison measures the tree you were trying to exclude.


## Close cycle (Decision 22)

Opened 2026-09-17 against the spec's Decision 22, which names the owed work as finite: the
evaluation-state carry of Decision 8 with its query-count controls at both tiers, the Slice 5
statements of Decisions 20 and 21 with the shipped examples corrected, and the widened floor
scope above (already declared). The cycle runs the builder worker cycle per cohort, then one gate
on one identified tree, then one review of that tree under Decision 20, then the record.

- Session scratchpad `<scratch>`:
  `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/87545721-0f0a-4259-b47e-4e5f7c9a1695/scratchpad`
- Pre-flight: index empty; no `docs/builder/bld-050-*` artifact exists; worker memory seeded at
  `docs/builder/worker-memory/050-worker-{0,1,2,3}.md`; temp tests under
  `docs/builder/temp-tests/050/`.
- Baseline-dirty out-of-scope files at the start of this close cycle (concurrent session; workers
  neither edit nor revert):
  `START.md`, `docs/bug_hunt/HUNT.md`, `docs/bug_hunt/bug_hunt-0_0_15.md` (deleted),
  `docs/bug_hunt/bug_hunt-0_0_1555.md`, `docs/bug_hunt/worker-1.md`, `docs/bug_hunt/worker-2.md`,
  `docs/dry/DRY.md`, `docs/dry/export_dry_review.py`, `docs/dry/worker-0.md`,
  `docs/dry/worker-1.md`, `docs/dry/worker-2.md`, `docs/dry/dry-0_0_15.md`,
  `docs/dry/dry-file-utils__querysets.md`, `docs/feedback.md`, `examples/fakeshop/db.sqlite3`
  (library seed rows differed from HEAD; kanban and glossary tables were identical to HEAD before
  the card-owned carve recorded above),
  `tests/test_export_dry_review.py`; joined mid-cycle by the same session: `docs/GLOSSARY.md`,
  `docs/TREE.md`, `examples/fakeshop/test_query/README.md`,
  `examples/fakeshop/test_query/test_debug_toolbar_api.py`, `tests/middleware/__init__.py`,
  `tests/middleware/test_debug_toolbar.py`. A concurrent DRY cycle names `utils/querysets.py`: a
  builder confirms `git diff HEAD -- <path>` is empty for every file it owns before its first
  edit and stops if it is not.
- Ownership partition (concurrent dispatch licensed):
  - **Cohort A, row carry** - `django_strawberry_framework/utils/querysets.py`,
    `django_strawberry_framework/resource_policy.py`,
    `django_strawberry_framework/types/resolvers.py`, `tests/test_resource_policy.py`,
    `tests/utils/test_querysets.py`, `examples/fakeshop/apps/library/models.py`,
    `examples/fakeshop/test_query/test_resource_policy_api.py`,
    `examples/fakeshop/test_query/test_library_api.py`,
    `examples/fakeshop/test_query/test_relations_async_api.py`,
    `examples/fakeshop/test_query/test_list_field_api.py`,
    `examples/fakeshop/test_query/test_list_field_async_api.py`,
    `django_strawberry_framework/permissions.py` (the last three folded in at the plan
    revision: the seal's admission change flips their deferred-filter rows and one docstring
    clause, and no other cohort owns them), artifact `docs/builder/bld-050-close-row_carry.md`.
  - **Cohort B, trust docs** - `docs/README.md`, `README.md`,
    `django_strawberry_framework/schema.py` (the `DjangoSchema` class docstring only, folded in
    at re-review: it is the last home of the authority-subclass qualifier the cohort retired),
    artifact `docs/builder/bld-050-close-trust_docs.md`.
  - Spec, rationale and this plan: Worker 1 (spec, rationale) and Worker 0 (plan) only.
- Hot-path declaration: Cohort A touches the generated many-side relation resolver and the
  raw-list seam (per parent row); the number owed is the query count for a prefetched
  `Manager.from_queryset` relation before and after, beside Django's own manager on the same
  request shape. Cohort B: none.
- Floor-verification scope: `### Floor-verification scope` above, in full, owned by the final
  gate (Worker 0 runs it on the identified tree); Cohort A additionally re-runs
  `tests/test_resource_policy.py` and `tests/utils/test_querysets.py` at the floor in its build
  pass.
- One cohort at a time per artifact; DRY first (`BUILD.md`).

### Close-cycle checklist

- [x] **Cohort A - evaluation-state carry at the raw-list seam** (spec Decision 8, Slice 3 row
      "The raw-list seam windows a source that arrives evaluated", test plan "The raw-list row
      source", DoD "A source that arrives evaluated"); artifact
      `docs/builder/bld-050-close-row_carry.md`.
- [x] **Cohort B - trust and extension contract in the shipped docs** (spec Decisions 20 and
      21, Slice 5 rows "State the trust contract" and "Correct the executable examples", DoD
      "The shipped docs state the trust contract"); artifact
      `docs/builder/bld-050-close-trust_docs.md`.
- [x] **Spec reconciliation and final verification (Worker 1)** - five homes agree; rationale
      change record; both cohort artifacts are superseded historical records.
- [x] **Gate on one candidate implementation commit** - `2c66416e`; default suite at
      `fail_under = 100`, sharded suite, the twenty-seven-path floor scope, hooks, citations,
      tracked-path constants, `manage.py check`, and `makemigrations --check --dry-run`.
- [x] **One review of that exact candidate tree under Decision 20** - record the review conclusion
      only after the candidate gate is complete; a finding meeting the three conditions re-loops.
- [x] **Evidence-only follow-up and card** - the candidate carries card 050's final DONE state in
      the board DB and generated exports; the follow-up changes this build record alone, names
      its candidate parent, and only then recognizes closure.

## Closing record

Closed 2026-09-22. This commit is the evidence-only follow-up: it changes this build record
alone, and its parent `2c66416e` is the gated candidate. The structural checks run on this
commit (last subsection) do not make it the full-suite tree; every suite figure below belongs to
`2c66416e`. The close-cycle artifacts remain superseded history and are not evidence.

### Gated candidate

- **Gated commit** `2c66416e`, tree `5ce4c799`.
- **Why it is not the tree the record above describes.** That text was written at `39811dab`.
  Two commits landed on it before the gate. `f306459d` is another session's collection guard in
  `tests/conftest.py` (`pytest_collection_modifyitems`) that refuses an async test marked
  `django_db` without `transaction=True`, with the markers it moved. It missed one, so at
  `f306459d` the guard raises `UsageError` at collection; under xdist that is a worker crash,
  and the default and sharded suites both exit 3 before any test runs. `2c66416e` moves that
  last marker
  (`examples/fakeshop/apps/library/tests/test_generic_connection.py::test_generic_connection_planning_does_no_sync_orm_work_under_async`,
  which writes no rows). It is the first tree on `main` that answers the gate. Neither commit is
  this card's deliverable.
- **What changed since the last reviewed tree.** Between `e5914bc4` and `2c66416e` nothing
  under `django_strawberry_framework/`, `examples/fakeshop/apps/` outside that one test module,
  `README.md`, `docs/README.md`, the spec or the rationale changed. The delta is 37 async
  tests in six test modules moved from `django_db` to `django_db(transaction=True)`, with no
  other line of those modules changed; the collection hook; this record; and a maintainer
  review-input document under `docs/` that `39811dab` rewrote.

Parent chain from the first candidate tree to the gated commit, oldest first:

1. `737b971b` fix(list_field): read an ordering term by the form it resolves into
2. `d6bc9f8f` test: restore the claims the live re-tiering dropped and harden their controls
3. `1c45f84b` test(relay): move the model-label GlobalID rows live and spell the floor's UTC
4. `08801efb` Implement code changes to enhance functionality and improve performance
5. `bfaee91d` Fix sequence-dependent GlobalID filter test
6. `1dd7d147` test(kanban): move the mutation wiring rows to the live tier
7. `a01a2ab8` test: move the request-observable rows live and pin the cost each one claims
8. `69a25369` docs: clear a superseded working note
9. `9350eb8d` Canonicalize the default policy path and close ErrorPolicy to str subclasses
10. `fee87ac4` fix(connection): seal the OrderSet return at the connection field
11. `44712901` fix(optimizer): refuse a sliced child on a plain list relation with the typed defect
12. `357e5487` docs(board): card 053 owes the FilterSet return seal at both fields
13. `1f68871a` test(list_field): stop the async adapter test committing its seed rows
14. `ec0d21de` Reconcile the spec-050 records with the connection OrderSet seal and prove it live async
15. `fa6d48f8` docs(spec-034): point the strictness pin at its live row
16. `9fb725c8` test(connection): carry the untrusted row and rewrite routing in place at the package seal
17. `c87f4f98` fix(connection): seal the FilterSet return with the same post-sidecar seal as OrderSet
18. `3c53842f` Drive the async connection OrderSet seal through an async consumer resolver
19. `24e6b4d3` test(querysets): prime the retained-type set before the planted-type growth snapshot
20. `174a109c` test(optimizer): isolate the app registry and plan the ordered window over real board models (concurrent; not this card's deliverable)
21. `29ddc0a8` test(connection): carry every sync defect shape across both async sidecar arms
22. `3ad0dfd6` test(optimizer): plan every relation shape over real library models (concurrent; not this card's deliverable)
23. `5ee86193` test(connection): give the repeated rejection assertion a name
24. `e5914bc4` test(visibility): cover the re-check on a joined but unplanned forward key
25. `39811dab` docs(build-050): name every commit the candidate now stands on
26. `f306459d` test: enforce transaction=True for async tests marked with django_db (concurrent; not this card's deliverable)
27. `2c66416e` test(library): run the async generic-connection planning test under transaction=True

### Gate rows

Every row ran in a `git clone --no-hardlinks` of the repository detached at `f306459d` with
the `2c66416e` hunk applied; `git write-tree` there is `5ce4c799`, equal to
`2c66416e^{tree}`, so the bytes measured are the gated commit's. The clone has its own
`uv sync` environment, `django_strawberry_framework.__file__` resolves inside it, and the
shared `.venv` package list is unchanged (`uv pip list | md5` `3949f759` before and after).

| Row | Command (cwd: the clone) | Result |
|---|---|---|
| Default suite, `fail_under = 100` | `uv run pytest` | 8516 passed, 42 skipped; 18624 statements, 0 missing, 100.00% |
| Sharded suite | `FAKESHOP_SHARDED=1 uv run pytest --no-cov` | 8537 passed, 39 skipped |
| Supported floor, 27 paths | `PYTHONPATH=<clone> <floor venv>/bin/python -m pytest --no-cov <scope>` | 3600 passed, 37 skipped |
| Format | `uv run ruff format --check .` | 454 files already formatted |
| Lint | `uv run ruff check .` | All checks passed |
| Source layout | `scripts/check_trailing_commas.py --check` | exit 0 |
| Citations | `scripts/check_citations.py --check` | 1164 citations resolve |
| Kanban anchors | `scripts/check_kanban_anchors.py` | 76 card anchors unique |
| Tracked-path constants | `scripts/build_kanban_tracked_path_constants.py --check` | exit 0 |
| Generated docs | `build_kanban_md.py`, `build_kanban_html.py`, `build_glossary_md.py`, `build_tree_md.py`, each `--check` | all up to date |
| Whitespace | `git diff --check f306459d` | exit 0 |
| Django system check | `python examples/fakeshop/manage.py check` | no issues |
| Migrations | `python examples/fakeshop/manage.py makemigrations --check --dry-run` | No changes detected |

The floor environment follows [`docs/builder/BUILD.md`][build-md] `## Floor verification`:
Python 3.10.19, Django 5.2.16, strawberry-graphql 0.316.0, over the scope in
`### Floor-verification scope`. Its 37 skips are 34 `Schema.stream landed in
strawberry-graphql 0.319.0` rows (`tests/extensions/test_operation_state.py` 20,
`tests/test_schema.py` 9, `tests/test_resource_policy.py` 4,
`tests/utils/test_execution_mode.py` 1), 2 `psycopg2` import skips in
`tests/types/test_converters.py`, and the module-level `FAKESHOP_SHARDED=1` skip in
`examples/fakeshop/test_query/test_multi_db.py`.

Each suite count is the `5ee86193` gate's count plus exactly the three live visibility rows
`e5914bc4` added (8513, 8534 and 3597 there). The coverage miss that failed that gate,
`django_strawberry_framework/types/resolvers.py::_make_relation_resolver`'s synchronous
forward-relation visibility tail, is covered by those rows.

Figures reported for this cycle by an earlier run (8518, 8539 and 3619) did not reproduce at
`39811dab` or at `2c66416e` and are not evidence.

### Review under Decision 20

One independent adversarial review of `2c66416e`, run after the gate in its own clone of that
commit, admits no finding, which ends the loop.

- **Byte identity.** The tree and blob hashes of `django_strawberry_framework/`, `README.md`,
  `docs/README.md`, the spec, the rationale and the spec's terms file are identical at
  `e5914bc4` and `2c66416e`. The production code was therefore already covered by the
  adversarial review of `e5914bc4`, which found no Decision-20 defect; that review's two process
  findings, the missing exact-tree gate and the unnamed candidate chain, are discharged by this
  record.
- **The 37 re-marked tests.** None relies on rollback, seed rows, the main-thread atomic block
  or a query count, so `transaction=True` changes nothing any of them asserts. The two
  `SynchronousOnlyOperation` proofs stay failable under it: with a plan-time
  `ContentType.objects.get_for_model` injected into
  `django_strawberry_framework/optimizer/nested_planner.py::plan_connection_relation`, both
  `examples/fakeshop/apps/library/tests/test_generic_connection.py::test_generic_connection_planning_does_no_sync_orm_work_under_async`
  and
  `tests/optimizer/test_walker.py::test_generic_connection_planning_does_no_sync_db_io_under_async`
  fail. Not admitted: no Definition-of-done row is broken and no input reaches a test marker.
- **The collection hook.** `tests/conftest.py::pytest_collection_modifyitems` resolves module
  `pytestmark`, class markers with a per-test override, parametrize `marks=`, positional
  `django_db(True)` and `functools.wraps`-wrapped coroutines correctly. It fails closed on
  `reset_sequences=True` and on the `transactional_db` fixture, which pytest-django treats as
  transactional. It fails open on an async test that takes the `db` fixture without a marker
  (none exists among the tree's 470 async test definitions), on a run that does not load
  `tests/conftest.py` (`pytest examples/fakeshop` alone), and on an async fixture writing rows
  for a sync test. Not admitted: the gate runs the full test paths, where the hook loads, and
  none of these reaches a Definition-of-done row or a wire or configuration input. The
  skipped-conftest fail-open is discharged: the guard moved to the root
  `conftest.py::pytest_collection_modifyitems`, which every run loads.
- **Flush side effects.** Each transactional test flushes the database, so a later module on
  the same xdist worker no longer sees rows the kanban and glossary data migrations seeded. That
  predates the delta and the full suites are green. Not admitted on all three conditions.

The review re-measured the default suite at `2c66416e` and reproduced the figures above. It
also checked this record's commit chain, tree id and statements of what changed.

### This follow-up's own checks

This commit's only change is this file. It was checked in a clone of `2c66416e` carrying it:
source layout, citations, kanban anchors and tracked-path constants.

### Deferred work catalog

Every item below left the card under spec Decision 20 or Decision 22 with a named owner;
none is a Definition-of-done row of this card.

- **Connection-field `FilterSet.apply_*` results are re-sealed - discharged** - both public
  sidecar returns are sealed at both fields by the shared entry pairs
  `django_strawberry_framework/utils/querysets.py::apply_orderset_sync` /
  `::apply_orderset_async` and `::apply_filterset_sync` / `::apply_filterset_async`, over one
  body (`::_apply_sidecar_sync` / `::_apply_sidecar_async`) and one
  `_SIDECAR_RESULT_POLICY`. `list_field.py` enters the ordering pair, and both connection
  pipelines - `connection.py::_pipeline_sync` and `connection.py::_pipeline_async` - route both
  sidecar arms through them, so each field freezes the same routing intent before the override
  runs and validates the return on the same result axes: lazy, model rows of the captured model,
  unsliced, uncombined, same alias. A hook's result contract does not depend on which field
  called it, and the row it answers is spec-030 Decision 7's "later steps can only narrow". The
  `FilterSet.apply_*` half was deferred out of this card to `TODO-ALPHA-053-0.0.15` (rationale,
  Decision 20 entry), which carried and discharged it together with the adjacent seal-policy
  asymmetry: a connection request carrying a sidecar input now seals `get_queryset` under
  `_LIST_ARGUMENT_VISIBILITY_POLICY`, the list field's argument-path rule, while a request with
  no sidecar input keeps `_DEFAULT_SEAL_POLICY`.
- **An exact `QuerySet` carrying a foreign `_result_cache` escapes the raw-list ceiling** - only
  in-process application Python can write that slot, so the wire-input condition fails; a
  robustness row. Owner: `maintainer`, recorded in this catalog only: `BACKLOG.md` holds
  scored strategic-differentiation cards, not robustness rows (`bld-050-close-row_carry.md`,
  final verification).
- **Retired "unresolved deferred filter" vocabulary** was identified by the historical review at
  the first-party visibility messages and module boundary. The live sites now name the refused
  condition as **malformed deferred-filter state**; the archived
  `docs/SPECS/spec-045-visibility_boundary-0_0_14.md` and
  `docs/SPECS/spec-034-permissions-0_0_10.md` quotations remain historical records. The seal
  admits Django's well-formed pending predicate and refuses only malformed state.
- **Archived `docs/SPECS/spec-047-resource_policy-0_0_14.md`** states the raw-list slice as a SQL
  `LIMIT` without the evaluated-source case - discharged - `b3458ee8` added that case to its
  `**The bound is applied by SLICING**` bullet, and its rationale records the claim the decision
  no longer makes.
- **`_UNRECOMPOSED_CHILD_POLICY` had zero production readers - discharged** - `4d9f1c3d`
  retired it, and no reference remains under `django_strawberry_framework/`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[spec-050]: ../../spec-050-list_field_arguments-0_0_15.md
[spec-050-rationale]: ../../spec-050-list_field_arguments-0_0_15-rationale.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build-md]: ../BUILD.md

<!-- django_strawberry_framework/ -->
[list-field]: ../../../django_strawberry_framework/list_field.py
[nested-planner]: ../../../django_strawberry_framework/optimizer/nested_planner.py
[relay]: ../../../django_strawberry_framework/types/relay.py
[resource-policy]: ../../../django_strawberry_framework/resource_policy.py
[walker]: ../../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->

<!-- examples/ -->
[fakeshop-library-migration-0005]: ../../../examples/fakeshop/apps/library/migrations/0005_branchnote.py
[fakeshop-library-models]: ../../../examples/fakeshop/apps/library/models.py
[fakeshop-library-schema]: ../../../examples/fakeshop/apps/library/schema.py
[fakeshop-library-test-models]: ../../../examples/fakeshop/apps/library/tests/test_models.py
[fakeshop-test-library]: ../../../examples/fakeshop/test_query/test_library_api.py
[fakeshop-test-resource-policy]: ../../../examples/fakeshop/test_query/test_resource_policy_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
