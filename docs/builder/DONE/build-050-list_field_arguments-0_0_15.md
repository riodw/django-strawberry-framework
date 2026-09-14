# Build: `DjangoListField` argument surface (`offset`, `limit`, and `orderBy`)

Spec: [`docs/spec-050-list_field_arguments-0_0_15.md`][spec-050]
Rationale: [`docs/spec-050-list_field_arguments-0_0_15-rationale.md`][spec-050-rationale]
Target release: `0.0.15`
Status: implementation complete through the eighth review's cleanup-precedence and proof-determinism remediation (control signals propagate out of async cleanup instead of becoming notes, the client window seam moved below the exported raw-list bound, a deterministic async deadline handoff, an executor-safe effective-order witness, cold/warm plan-cache assertions spelled apart, module description without frozen counts). The final gate is OWED: these rounds changed production code, so the sixth round's green figures (default 7775 / sharded 7792 / floor 2397, zero failures) describe the tree before them and are kept as history. Scope, figures and the standing evidence are in `## Final gate record` below.

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
- [x] **Slice 5 — documentation fold-in**
  - [x] Update the list-field docstring and the shipped-surface descriptions in
        `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, and `README.md` where the new
        arguments are enumerated.
  - [x] Update `ResourcePolicy` and bounding-helper docstrings to distinguish returned/skip
        ceilings from total database rows scanned.
  - [x] Update the KANBAN database when the implementation card closes; `TODAY.md` is
        deliberately not edited (no waiting entry exists to move - see Doc updates).
  - [x] Leave the version literal, version assertion, package-version glossary row, release
        wording, and `CHANGELOG.md` to card 053's joint cut; `pyproject.toml` and `uv.lock`
        have no duplicate root-package version to bump.
- [x] **Cross-slice integration pass (Worker 1)**
- [ ] **Final test-run gate (Worker 1)** — the sixth round's gate is superseded by the seventh
      round's production changes; rerun format, lint, structural and link checks, the default and
      sharded suites at 100% package coverage, and supported-floor verification on ONE identified
      tree; the floor scope and the last measured figures are in `## Final gate record` below

## Final gate record (folded in from `bld-final.md` before its deletion)

`docs/builder/bld-final.md` and the six per-slice and integration artifacts were deleted at
close on the maintainer's instruction; this plan is the only surviving artifact of the cycle.
All seven are readable at commit `63a132be` (`git show 63a132be:docs/builder/<name>`).

The eight rounds of finding-by-finding remediation, the superseded command tables and the
gate narratives are NOT restated here: every fix they describe is in the commit that landed
it, in one of the spec's five homes, or in the code's own docstrings. What follows is what
nothing else in the tree records.

**The gate is OWED.** No `pytest` invocation has been made since the tree changed. The last
green run measured HEAD `96b9e047` plus that round's working-tree changes: default **7775
passed / 40 skipped / 100.00%**, sharded **7792 passed / 37 skipped / 100.00%**, floor **2397
passed / 2 skipped**. Three later rounds changed production code, so those figures describe a
tree that no longer exists and are kept only as the record of the tier they measured.

### Floor-verification scope

[`docs/builder/BUILD.md`][build-md] `## Floor verification` owns the venv recipe and the
floor pins; the scope is this plan's to declare, and it is the set of modules whose seams this
card actually moved - every Strawberry-internals and queryset-compilation boundary it touched:

`tests/base/test_init.py`, `tests/test_list_field.py`, `tests/test_connection.py`,
`tests/test_relay_connection.py`, `tests/test_keyset_connection.py`, `tests/orders/test_sets.py`,
`tests/utils/test_querysets.py`, `tests/optimizer/`, `tests/test_relay_node_field.py`,
`tests/test_registry.py`, `tests/types/`, `tests/test_resource_policy.py`,
`tests/test_graphql_core_patches.py`, and the four live modules
`examples/fakeshop/test_query/test_list_field_api.py`,
`examples/fakeshop/test_query/test_list_field_async_api.py`,
`examples/fakeshop/test_query/test_products_visibility_api.py`,
`examples/fakeshop/test_query/test_keyset_api.py`.

A floor run that narrows this set is not this card's floor verification. The shared `.venv` is
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

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
