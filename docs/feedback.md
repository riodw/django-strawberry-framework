# Adversarial review — spec-050 recheck

Review verdict: **request changes; the current dirty tree is not safe to merge.**

This is a fresh review of the present working tree, not a restatement of the previous report. It
covers all tracked modifications and deletions, the untracked spec/build artifacts, and the changed
fakeshop database. I compared the implementation against [`spec-050`][spec-050], its
[rationale][rationale], the shipped list-field contract, the builder evidence, and the repository's
test-placement rules.

No pytest run was performed. The review therefore treats the checked-in build reports as claims to
audit, not as results independently reproduced here.

## High

### 1. Looking up `aclose` can still replace the primary resolver failure

Source: [`resource_policy.py`][resource-policy]
`::_close_async_iterator #"close = getattr(iterator, \"aclose\", None)"`

The helper promises that a source/domain error remains primary and any cleanup failure is attached
as a note. The `try` begins only after `getattr(iterator, "aclose", None)`, however. An async
iterator with a hostile `__getattribute__` that raises while `aclose` is being resolved bypasses the
cleanup-error handler entirely.

That affects both production callers:

- `bounded_rows_async` can catch an iteration failure, enter `finally`, and then replace it with the
  `aclose` lookup failure.
- `list_field.py::_cleanup_rejected_async_iterable` can build the correct `ListArgumentError`, then
  replace it while trying to close a rejected async source.

The tests cover an `aclose()` body that raises, but not acquisition of the `aclose` attribute. The
distinction is load-bearing because the old inline cleanup placed both lookup and invocation inside
the same `try`.

Required fix: move optional-close lookup inside the protected cleanup block and treat lookup and
invocation failures identically. Add one source-error witness through `bounded_rows_async` and one
pre-bound `ListArgumentError` witness through the list-field rejection path where
`__getattribute__("aclose")` raises; in both cases the original error must remain primary and the
cleanup failure must be diagnostic only.

### 2. The OrderSet purity check does not compare the value that was actually applied

Sources:

- [`sets.py`][orders-sets] `::OrderSet._apply_orderings`
- [`sets.py`][orders-sets] `::OrderSet._input_has_active_terms`
- [`test_sets.py`][test-order-sets]
  `::test_input_has_active_terms_independent_query_and_double_normalization`

One request currently normalizes three times: once inside public `apply_sync` / `apply_async`, then
twice inside `_input_has_active_terms`. The helper compares only its own second and third results.
It never compares either result with the first normalization that produced the SQL ordering.

A stateful override returning `A`, then `B`, then `B` therefore passes the alleged purity check. A
concrete bad case is `A = [("name", ASC)]` and `B = []`: the public apply method installs a real
order, the helper certifies its two identical empty results, and a valid positive-offset request is
rejected as unordered. The inverse sequence can make the activity verdict claim terms the public
apply never saw. The tests explicitly pin the count at three, so they institutionalize the gap
instead of detecting it.

This also contradicts [`spec-050`][spec-050], which says an argument-bearing request may normalize
once in public apply and once in the activity helper, and says disagreement between those views must
raise. The promised compatibility constraint is not documented on
`OrderSet._normalize_input` itself either. Finally, `data1 != data2` and the error's `!r` formatting
operate on consumer-override output without containment, so hostile equality or representation can
escape as a raw exception rather than the promised actionable `ConfigurationError`.

Required fix: redesign the seam so the activity verdict is derived from, or compared with, the
same normalized record that the public apply path actually used. A second pair of unrelated calls
cannot prove that. Normalize into validated inert data before equality/rendering, document the
purity obligation on `_normalize_input`, and add the `A/B/B` and `A/A/B` sequences as load-bearing
controls for both execution colors.

### 3. The graphql-core patch is a reimplementation protected only by a signature check

Source: [`_strawberry_patches.py`][strawberry-patches] `::_patched_complete_list_value`

The patch and `_validate_upstream_shape` describe this as a wrapper/delegator whose upstream body
changes flow through the captured original. That is false for the exact branch being fixed. For an
`AsyncIterable`, `_patched_complete_list_value` copies graphql-core's entire async-list branch:
iterable classification, materialization, recursive completion, and await handling. The original is
called only for every other source shape.

The repository's own patch discipline distinguishes delegators, which may pin signatures, from
reimplementations, which must pin the body they supersede. With only a six-parameter signature
check, a supported graphql-core release can change async iteration error handling, cancellation,
cleanup, or completion semantics without changing the signature, and this package will silently
replace that new behavior with the copied old branch.

There is a simpler true-delegation shape: call the captured original for the `AsyncIterable`, await
its returned awaitable, then await the one residual awaitable produced by the upstream bug. If that
cannot preserve the required semantics, the copied upstream branch must be source-pinned and
version-tested as a reimplementation rather than documented as delegation.

The ownership boundary also needs reconciliation. `_strawberry_patches` now mutates a graphql-core
execution method process-wide under the `"strawberry"` kill-switch key, while the standing glossary
still says there is one patch module per third-party dependency and describes this module only as
Strawberry HTTP-view hardening. Disabling the documented Strawberry patch group now also disables a
mechanism on which the advertised async `DjangoListField` completion path depends. Either split the
graphql-core concern into truthful ownership/configuration or explicitly document the transitive
engine patch and the consequence of opting out.

## Medium

### 4. The required client-window SQL test still tests Django slicing, not DjangoListField

Sources:

- [`test_list_field.py`][test-list-field] `::test_list_field_no_argument_sql_parity`
- [`test_list_field.py`][test-list-field] `::test_list_field_window_low_high_marks`
- [`test_list_field_api.py`][test-list-field-api]
  `::test_shipped_branches_staff_ordered_offset_limit`
- [`test_list_field_api.py`][test-list-field-api]
  `::test_shipped_branches_offset_alone_bounds`

The no-argument parity test is improved: it now executes the field path, captures SQL, and compares
omitted arguments with explicit nulls. Its docstring still claims low/high-mark assertions it does
not make, but it at least observes production SQL.

The supplied-window test remains disconnected. It constructs
`Category.objects.all().order_by("id")`, manually slices it to `[0:5]` and `[3:8]`, then verifies
Django's own `low_mark`, `high_mark`, `LIMIT`, and `OFFSET`. Removing client limit/offset plumbing
from `DjangoListField`, `bounded_rows`, or either execution pipeline would leave this test green.

The live ordered `offset + limit` case asserts only returned names. The offset-only live case
captures `LIMIT 100 OFFSET 2`, but no field-path test proves that a smaller supplied limit changes
the final high mark or produces exactly one `LIMIT`/`OFFSET` pair. The only `LIMIT 5`, `OFFSET 3`,
and corresponding mark assertions in the dirty tests are on the manually sliced queryset.

Required fix: observe the final queryset or captured SQL produced by the real field pipeline for
limit-only and offset-plus-limit requests. The witness must fail if either client coordinate stops
reaching the bounding seam and must assert a single composed window, not merely response length.

### 5. The final-accepted evidence does not establish the repository's 100% gate

Sources:

- [`bld-final.md`][bld-final] `#"Command ran with --no-cov"`
- [`bld-integration.md`][bld-integration]
  `#"all six Python files modified during Card 050"`
- [`KANBAN.md`][kanban] `#"Full suite green under fail_under = 100"`

The card is marked Done with the 100% coverage Definition-of-Done box checked, but the final report
explicitly ran `uv run pytest --no-cov` and says coverage was not inspected or asserted. The only
recorded 100% run is an earlier Slice 2 run, before later test/source slices and before the final
graphql-core patch remediation. It cannot establish coverage for the final tree.

The integration report also says static inspection covered all six changed production Python files.
There are now seven: `_strawberry_patches.py` was added to the dirty source set after that pass. The
final floor command omits `tests/test_strawberry_patches.py`, even though the newly added patch reads
private graphql-core behavior and the spec explicitly requires supported-version coverage for list
completion. Thus the most version-sensitive late production change is neither in the recorded
integration inspection inventory nor in the explicit dependency-floor patch suite.

Required fix: return the card to WIP, refresh integration/static inspection for the actual final
source inventory, include the graphql-core patch tests in floor verification, and run the real
coverage-gated suite before checking the 100% box. Build artifacts should report the resulting
commands and snapshot accurately rather than inheriting an earlier slice's result.

### 6. Mandated live verdicts are missing while weaker package-schema duplicates remain

Sources:

- [`spec-050`][spec-050], “Live-first placement is fixed per branch”
- [`test-list-field`][test-list-field]
- [`test-list-field-api`][test-list-field-api]
- [`test-list-field-async-api`][test-list-field-async-api]

The spec says the final classification of post-OrderSet evaluated, projection, combined, and
wrong-model results must remain live. The sync live suite covers the combined result only. It has no
live evaluated, projection, or wrong-model `apply_sync` result. The async live suite does not cover
the corresponding malformed `apply_async` return shapes either.

At the same time, the package test file adds large real-schema execution blocks for behavior already
covered over HTTP: default/Manager/QuerySet/async list completion, generated SDL, public order and
offset behavior, and serialized sync/async OrderSet errors. This conflicts with the repository's
live-first rule and the build plan's statement that the package tier is for mechanics that HTTP
cannot isolate. It also makes the review surface much larger without closing the exact live rows the
spec named.

Required fix: add the missing public verdicts to the test-local live mounts, then remove redundant
package schema executions. Keep direct helper, protocol, exact call-count, failure-precedence, and
sealed-state mechanics in `tests/`; keep public SDL/request/response behavior in the fakeshop HTTP
tier.

### 7. The normal test suite contains a wall-clock assertion the spec explicitly rejected

Sources:

- [`test_list_field.py`][test-list-field] `::test_list_field_post_apply_seal_benchmark`
- [`bld-slice-3-sql_and_unit_contracts.md`][bld-s3]
  `#"Post-apply seal wall-clock benchmark"`
- [`spec-050`][spec-050], “recording the cost Decision 5 accepts rather than asserting a
  threshold”

The ordinary test performs 20 warmups, measures 200 iterations, and fails when the average exceeds
5,000 microseconds. That is an environment-sensitive performance gate despite the spec requiring a
recorded diagnostic rather than a threshold assertion.

The build artifact does not even describe the code that exists: it reports 1,000 iterations,
22.07 microseconds measured, a target of 100 microseconds, and a test threshold of 50,000
microseconds. None of the iteration or threshold values match the current test. A benchmark that is
both flaky and inaccurately recorded provides negative assurance.

Required fix: remove the wall-clock assertion from the normal correctness suite. Keep structural
and failability assertions there, and put a reproducible, sufficiently sampled diagnostic result in
the build artifact with the exact code/command used. If a hard performance gate is desired, amend
the spec and use a calibrated benchmark mechanism rather than `perf_counter` in a normal pytest row.

### 8. The tracked fakeshop database contains unrelated test-fixture residue

Source: [`fakeshop-db`][fakeshop-db]

The changed SQLite database legitimately carries generated Kanban/glossary state, so reverting the
whole binary would destroy in-scope work. It also contains an unrelated library graph that mirrors
ad hoc test data rather than shipped example content:

- branch `id=6`, name `central`;
- shelf `id=4`, code `A1`, pointing at that branch;
- genre `id=36`, name `fiction`;
- books `id=6..8`, titles `a`, `b`, `c`, on that shelf;
- three book/genre join rows connecting those books to `fiction`.

These rows are not part of spec-050's Kanban/glossary update. Committing them would silently change
the example database and make the binary diff carry non-reproducible fixture pollution.

Required fix: remove only the unrelated library rows, preserving the intended Kanban/glossary
changes, then regenerate the Markdown/HTML views from the clean database and verify the binary's
remaining logical diff.

## Low / documentation blockers

### 9. Several standing descriptions contradict the newly shipped surface

Sources:

- [`spec-050`][spec-050] `#"Status: planned for"`
- [`README.md`][docs-readme] `#"a non-Relay list[T] with no pagination"`
- [`GLOSSARY.md`][glossary] `::DjangoListField #"use cases that do not need pagination"`
- [`GLOSSARY.md`][glossary] `::Upstream patches`
- [`resource_policy.py`][resource-policy] `::bounded_rows`
- [`resource_policy.py`][resource-policy] `::bounded_rows_async`
- [`test_init.py`][test-init] `::test_version`

The consumer guide and glossary still introduce `DjangoListField` as having or needing “no
pagination,” immediately before describing its new ordered offset pagination. The intended contrast
is “no Relay envelope, edges, or page info,” not “no pagination.”

The normative spec still targets `WIP-ALPHA-050-0.0.15` and says the work is “planned,” while the
build plan says `complete`, the final report says `final-accepted`, and the generated Kanban marks
the card `DONE-050-0.0.15`. Leaving the slice checklist unticked can follow this repository's
shipped-spec convention when the status line is the completion source of truth; leaving that source
of truth itself in the planned state cannot. The Slice 5 plan explicitly included ordinary
card/spec-state reconciliation, so its claim that all documentation is aligned is false on the
spec's first four lines.

The upstream-patches glossary entry still inventories only Strawberry HTTP-view behavior under
`_strawberry_patches` and repeats the one-module-per-dependency model, omitting the process-wide
graphql-core executor patch. The bounding-helper docstrings say `requested_limit` is capped by the
effective limit, while the helpers deliberately assume prevalidated coordinates and do not clamp;
the public wrapper rejects an oversized limit. The docs should say “prevalidated” rather than claim
a second cap that does not exist at that seam.

Finally, `test_version` still says this is a version-only change that must not widen root `__all__`,
although the same dirty change intentionally adds the root `ListArgumentError` export. A later
comment was corrected; this earlier one was missed.

Required fix: reconcile the spec's lifecycle line and all standing prose with the actual ownership
and behavior. These are small edits, but leaving contradictions beside a newly closed public API
card guarantees migration and maintenance confusion.

## What is solid in this recheck

The previous review's largest blockers were genuinely addressed and are not findings here:

- `trusted_max_rows` is restored as an explicit public opt-in and no longer inferred from
  `max_rows`.
- collection-bound validation again precedes target/directive processing;
- `_ListArguments` is frozen and slotted;
- runtime errors use the actual field name, converter failures are typed instead of silently
  guessed, and model-default ordering requires exact `True`;
- post-OrderSet routing reads candidate state without re-entering hostile attribute access and
  compares hints without arbitrary value equality or representation;
- the conditional OrderSet import preserves package-root submodule isolation;
- the shared visibility/order/window pipeline, adapter placement, optimizer unwrap/rewrap, and
  explicit no-pk/no-`DISTINCT` contract are directionally coherent.

Those corrections materially improve the implementation. They do not resolve Findings 1–5: the
remaining primary-error masking and normalization-divergence bugs are production defects, and the
late global executor patch plus incomplete final evidence make the current Done/accepted state
premature.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: ../KANBAN.md

<!-- docs/ -->
[docs-readme]: README.md
[glossary]: GLOSSARY.md
[rationale]: spec-050-list_field_arguments-0_0_15-rationale.md
[spec-050]: spec-050-list_field_arguments-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[bld-final]: builder/bld-final.md
[bld-integration]: builder/bld-integration.md
[bld-s3]: builder/bld-slice-3-sql_and_unit_contracts.md

<!-- django_strawberry_framework/ -->
[orders-sets]: ../django_strawberry_framework/orders/sets.py
[resource-policy]: ../django_strawberry_framework/resource_policy.py
[strawberry-patches]: ../django_strawberry_framework/_strawberry_patches.py

<!-- tests/ -->
[test-init]: ../tests/base/test_init.py
[test-list-field]: ../tests/test_list_field.py
[test-order-sets]: ../tests/orders/test_sets.py

<!-- examples/ -->
[fakeshop-db]: ../examples/fakeshop/db.sqlite3
[test-list-field-api]: ../examples/fakeshop/test_query/test_list_field_api.py
[test-list-field-async-api]: ../examples/fakeshop/test_query/test_list_field_async_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
