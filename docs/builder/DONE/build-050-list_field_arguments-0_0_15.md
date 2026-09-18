# Build: `DjangoListField` argument surface (`offset`, `limit`, and `orderBy`)

Spec: [`docs/spec-050-list_field_arguments-0_0_15.md`][spec-050]
Rationale: [`docs/spec-050-list_field_arguments-0_0_15-rationale.md`][spec-050-rationale]
Target release: `0.0.15`
Status: WIP. The prior close record is superseded because it described a tree that is not the
current candidate and treated a future maintainer commit as an existing identity. No current
default, sharded, supported-floor, or adversarial-review result is evidence for this checkout.
The candidate and evidence-only follow-up protocol in spec Decision 22 must run before the card
can close. What the gate covers, beyond the five slices:

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
the live hostile-relation rows on both transports; no new tracked path is added, so neither
generated view moves.

## Pre-flight baseline
- Baseline check: clean (`git status --short` empty at pre-flight).
- Static inspection tool smoke test: passed (`scripts/review_inspect.py django_strawberry_framework/list_field.py --output-dir docs/shadow --stdout`).
- Spec glossary consistency check: passed (43 terms checked, exited 0).
- Spec rationale extraction: completed by Worker 1.
  - Spec byte count before: 147,842 bytes (2,056 lines)
  - Spec byte count after: 141,617 bytes (1,979 lines)
  - Rationale byte count: 20,524 bytes (342 lines)

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
- [ ] **Slice 5 — documentation fold-in**
  - [x] Update the list-field docstring and the shipped-surface descriptions in
        `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, and `README.md` where the new
        arguments are enumerated.
  - [x] Update `ResourcePolicy` and bounding-helper docstrings to distinguish returned/skip
        ceilings from total database rows scanned.
  - [ ] Update the KANBAN database and the current-checkout statements in `TODAY.md` when the
        candidate implementation commit carries the final board transition; the pre-candidate
        generated outputs and milestone statements remain WIP.
  - [x] Leave the version literal, version assertion, package-version glossary row, release
        wording, and `CHANGELOG.md` to card 053's joint cut; `pyproject.toml` and `uv.lock`
        have no duplicate root-package version to bump.
- [x] **Cross-slice integration pass (Worker 1)**
- [ ] **Final exact-commit gate** — the maintainer must create the candidate implementation
      commit, then run the default, sharded, supported-floor, structural and documentation gates
      on that exact candidate.

## Final gate record

No gate is currently recorded. The prior close evidence is superseded because it did not identify
the tree that the full suites and review actually covered, and a tracked record cannot name the
commit that contains the record itself.

The maintainer's next close uses two commits:

1. The candidate implementation commit contains all production and test changes, shipped docs,
   the final board/database transition, the spec status, and generated outputs. The current
   pre-candidate checkout stays WIP; the candidate atomically carries the board's DONE state.
   Its commit id is the exact tree for every default, sharded, supported-floor, structural, link,
   citation, tracked-path and adversarial-review result.
2. After a green gate and a review that admits no finding under Decision 20, an evidence-only
   follow-up commit changes this build record alone. Its parent must be the gated candidate; the
   record must name that parent, list the commands and results, and say that the follow-up's
   structural checks do not turn it into the full-suite tree.

This pre-candidate checkout remains WIP until the candidate commit exists. The candidate's DONE
board state is not treated as closure evidence until the exact-tree gate, review and evidence-only
follow-up are complete. No result from another tree is carried forward as current evidence.

### Board database state

The tracked SQLite file is one binary, so Git cannot stage card-owned tables separately from a
concurrent owner's rows. The earlier reconstruction from `HEAD` therefore was not a safe carve:
it removed the concurrent library data. The workspace now carries that data back in the real
tracked file, rather than leaving the only copy in `/private/tmp`:

- `library_book`: 20 rows and sequence `23`;
- `library_branch`: 7 rows and sequence `10`;
- `library_loan`: 16 rows and sequence `16`;
- `library_patron`: 6 rows and sequence `6`;
- `library_shelf`: 7 rows and sequence `8`.

The concurrent timestamp-only changes in `glossary_glossaryspecmention` and
`kanban_cardglossaryterm` are present as well. Card 050's own glossary bodies remain in
`glossary_glossaryterm` ids `442`, `455`, `459`, `465`, `507`, and `553`; its board state remains
WIP (`kanban_card` id `73`, status WIP, and `kanban_carditem` id `1519`, incomplete). The merged
database passes `PRAGMA integrity_check` and `PRAGMA foreign_key_check`; a semantic comparison
with the dirty source differs only in those two deliberate WIP fields.

This is a WIP workspace state, not a disentangled candidate. Until the concurrent database owner
lands the library change or provides a coordinated merge point, card 050 cannot safely commit
`examples/fakeshop/db.sqlite3` as its own candidate input: the same binary would absorb both
owners' rows, even though the board transition and glossary edits are card-owned. The generated
`KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` therefore remain WIP outputs to regenerate at
the coordinated candidate step. Card 050's final DONE transition belongs in the later candidate
commit; closure is recognized only in the evidence-only follow-up described above.

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
`tests/test_error_policy.py` - and the six live modules
`examples/fakeshop/test_query/test_list_field_api.py`,
`examples/fakeshop/test_query/test_list_field_async_api.py`,
`examples/fakeshop/test_query/test_products_visibility_api.py`,
`examples/fakeshop/test_query/test_keyset_api.py`,
`examples/fakeshop/test_query/test_resource_policy_api.py`,
`examples/fakeshop/test_query/test_error_policy_api.py`.

That is twenty-three paths: seventeen package modules or directories and the six live modules. A
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
- [ ] **Gate on one candidate implementation commit** - default suite at `fail_under = 100`,
      sharded suite, the twenty-three-path floor scope, hooks, citations, tracked-path constants,
      `manage.py check`, and `makemigrations --check --dry-run`.
- [ ] **One review of that exact candidate tree under Decision 20** - record the review conclusion
      only after the candidate gate is complete; a finding meeting the three conditions re-loops.
- [ ] **Evidence-only follow-up and card** - the candidate carries card 050's final DONE state in
      the board DB and generated exports; the follow-up changes this build record alone, names
      its candidate parent, and only then recognizes closure.

## Closing record

No closing gate table exists yet. The close-cycle artifacts remain available as superseded history;
they are not evidence for the candidate or its evidence-only follow-up.

### Deferred work catalog

Every item below left the card under spec Decision 20 or Decision 22 with a named owner;
none is a Definition-of-done row of this card.

- **Connection-field sidecar results are not re-sealed** - `connection.py::_pipeline_sync` /
  `_pipeline_async` apply `FilterSet.apply_*` and `OrderSet.apply_*` with no routing snapshot and
  no post-apply seal, where `list_field.py` does both; a hook's result contract does not depend
  on which field called it, and the row it breaks is spec-030 Decision 7's "later steps can only
  narrow". Owner: `maintainer`, as a new card against that row (rationale, Decision 20 entry).
- **An exact `QuerySet` carrying a foreign `_result_cache` escapes the raw-list ceiling** - only
  in-process application Python can write that slot, so the wire-input condition fails; a
  robustness row. Owner: `maintainer`, `BACKLOG.md` (`bld-050-close-row_carry.md`, final
  verification).
- **Retired "unresolved deferred filter" vocabulary** was identified by the historical review at
  the first-party visibility messages and module boundary. The live sites now name the refused
  condition as **malformed deferred-filter state**; the archived
  `docs/SPECS/spec-045-visibility_boundary-0_0_14.md` and
  `docs/SPECS/spec-034-permissions-0_0_10.md` quotations remain historical records. The seal
  admits Django's well-formed pending predicate and refuses only malformed state.
- **Archived `docs/SPECS/spec-047-resource_policy-0_0_14.md`** states the raw-list slice as a SQL
  `LIMIT` without the evaluated-source case; a dated `0.0.14` record. Owner: `maintainer`.
- **`_UNRECOMPOSED_CHILD_POLICY` has zero production readers** - an existence question for the
  next DRY cycle. Owner: `maintainer`.

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
[fakeshop-test-resource-policy]: ../../../examples/fakeshop/test_query/test_resource_policy_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
