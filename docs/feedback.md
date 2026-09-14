# Adversarial implementation re-review: spec 050

Date: 2026-09-13

## Verdict

**Not accepted yet. Two reproducible production defects remain:** the offset guard checks the
wrong ordering state, and a deadline rejection can leave an async iterator unclosed. The previous
canonical-definition, connection-cache provenance, and terminal-ledger defects are fixed. They
are not repeated as open findings.

This review reads the full [specification][spec-050], traces the implementation and its regression
tests, and applies [AGENTS.md][agents], [START.md][start], [GOAL.md][goal], and the
[live-test manual][live-readme]. It also checks the local Graphene-Django and Strawberry-Django
references and the [cookbook schema][cookbook-schema].

The starting HEAD was `974d25b4`, containing the metadata/ledger remediation in `9a9f970c`.
HEAD advanced concurrently to `4746a0fe`. The intervening changes did not alter the reviewed
package source, package tests, live-query tests, or spec 050. Concurrent documentation, kanban
test, and database work was preserved.

Evidence below comes from source inspection and isolated, non-pytest Python probes, including
actual `DjangoSchema` execution. Probe databases were configured in memory; the probes performed
no row writes or row-fetch SQL. SQL shown below was compiled from the resulting querysets.
No pytest, Django system-check, build, or full-suite command was run. The recorded full/default,
sharded, and floor passes are implementation evidence in the [build record][bld-final], not
fresh results from this review.

Two Luna Extra High reviewers were dispatched as requested earlier, but both terminated before
returning findings because the workspace reported no remaining subagent credits. No conclusion
below is attributed to an independent reviewer.

## P2-1 — the positive-offset guard does not inspect the effective ordering

Location:
[`django_strawberry_framework/list_field.py::_has_no_random_terms`][list-field] and
[`django_strawberry_framework/list_field.py::_check_nonzero_offset_guard`][list-field].

The guard accepts active order input when `queryset.ordered` is true and
`_has_no_random_terms(queryset)` succeeds. The latter checks both `query.order_by` and
`query.extra_order_by`, but never model-default terms.

Those are not Django's effective-ordering rules.
[`django/db/models/sql/compiler.py::SQLCompiler._order_by_pairs`][django-compiler] selects
`extra_order_by` first, then explicit ordering, then enabled model defaults. It does not
combine the two explicit collections or omit defaults when they are the selected order.
The mismatch produces both wrong verdicts.

### Random default accepted

A registered type has an OrderSet with an `id` input. A mistaken public
`OrderSet.apply_sync` override returns the supplied queryset unchanged. The model declares
`Meta.ordering = ("?",)`. Calling the actual list-field resolver with active `id: ASC`,
`offset=1`, and `limit=1` succeeds:

```text
accepted_type QuerySet
explicit_order ()
default_order ('?',)
sql ... ORDER BY RAND() ASC LIMIT 1 OFFSET 1
```

The same probe with `Meta.ordering = (Random(),)` also succeeds. Its no-order control raises
`ListArgumentError(reason="order_required")`; its stable `("id",)` control succeeds.
Thus the random default specifically defeats the guard through the active-input branch:
`queryset.ordered` sees the default, while the random check sees two empty collections.

This does not require proving arbitrary override lineage. Decision 5 trusts overrides to
preserve predicates; Decision 6 separately promises a mechanical check that effective ordering
contains no recognized random term. A mistaken override is exactly where that check matters.
Both `"?"` and bare `Random()` are expressly recognized forms, not unspecified SQL volatility.

### Effective deterministic order rejected

A public override returns:

```python
queryset.order_by("?").extra(order_by=["id"])
```

For active `id: ASC` input this is effectively ordered by `id`, because the extra ordering
takes precedence. The compiled SQL confirms it:

```text
effective_sql ... ORDER BY "contenttypes_probemodel"."id" ASC
guard ListArgumentError order_required
```

The guard rejects the dormant `"?"` in `query.order_by`, which Django never executes.
This half also affects an override that honors the supplied order; it cannot be dismissed as
the no-op override's responsibility.

**Root-cause correction:** classify the terms Django actually selects, once, using its
precedence on the already-sealed queryset. Preserve the separate public-order eligibility
rule: resolver-only ordering must still not authorize positive offset without active input or
an eligible model default. Preserve the grouping and empty-queryset rules. Do not call the
compiler or evaluate rows on the successful request path merely to discover this small state
selection, and do not borrow `effective_connection_order`: that helper intentionally changes
ordering to the connection's total-order contract.

**Required proofs:** sync and async live holder rows for random-default rejection after a
no-op apply, and acceptance when deterministic extra ordering supersedes dormant random
ordering. Include stable-default and effective-random-extra controls. Retain package checks
only for exact precedence mechanics. The current
`tests/test_list_field.py::test_offset_guard_random_term_question_mark` and
`test_offset_guard_random_term_random_function` exercise explicit random terms alone; the
separate model-default predicate checks never exercise this interaction with active input.

## P2-2 — deadline rejection bypasses async-source cleanup

Location:
[`django_strawberry_framework/resource_policy.py::bounded_rows_async`][resource-policy],
reached through [`django_strawberry_framework/list_field.py::DjangoListField`][list-field]'s
`_resolve_async_iterable` closure.

`bounded_rows_async` calls `_raw_list_bound` before acquiring the iterator and before entering
its cleanup-protected region. If the deadline expires while the consumer resolver awaits,
`_raw_list_bound` raises `ResourceLimitExceeded`. The already-returned async source is
abandoned without attempting `aclose`.

A real `DjangoSchema` probe used a custom async iterator with external advance/close counters.
The resolver awaited 80 ms and then returned that retained iterator. The operation was
`{ rows(limit: 0) { id } }`; the deadline case used the schema's normal 50 ms resource policy.
No internal deadline key was modified for this schema-level reproduction.

```text
deadline=None: source_called=True, errors=[], advances=0, closes=1
deadline=0.05: source_called=True, RESOURCE_LIMIT_EXCEEDED, advances=0, closes=0
```

The deadline error's extensions remained correct:
`bound="execution_deadline_seconds", limit=1, charged=2`.
The defect is the missing close, not the deadline rejection or its rounded payload.

This remains an uncovered composition of the existing deadline and cleanup mechanisms;
it was not introduced by the latest metadata remediation. It nevertheless violates this
card's async early-exit guarantee, including its explicit `limit: 0` cleanup promise.
The list wrapper handles capability rejection and even error-construction failure, but
ownership does not end merely because the next failure occurs inside the bounding helper.
An iterator may own an open external resource even before its first item is requested.

**Root-cause correction:** make the shared async bounding seam own cleanup on this pre-iteration
rejection too. Keep the single deadline check in `_raw_list_bound`, before row advancement and
window arithmetic. If it rejects, acquire the source's iterator solely for cleanup, invoke
the existing close mechanism, and preserve the deadline error as primary if acquisition or
closure fails. Move/reuse the existing rejected-source cleanup utility below both callers
instead of duplicating its acquisition, diagnostic-note, and close policy in a second module.
Do not add a second clock check or a list-field-only catch that leaves other callers exposed.

**Required proofs:** a live async request whose resolver crosses the configured deadline after
obtaining its source; zero advances and exactly one close, including `limit: 0`.
Use a deterministic clock-controlled boundary for the retained regression test rather than a
timing-sensitive sleep. Cover a failing close with the complete resource-error extensions
still primary. Exact diagnostic notes belong in `tests/test_resource_policy.py`; retain the
natural-exhaustion control, where the iterator is deliberately not closed. A never-started
async generator's body `finally` is not a valid close witness—use the externally counted
iterator the spec already prescribes.

## P2-3 — the metadata regression proof misses the custom-hook model dependency

Location:
[`tests/test_connection.py::test_the_optimizer_plans_a_relation_without_reading_the_target_class`][test-connection]
and `tests/test_connection.py::_counting_node_type`.

The new counter/decoy test builds its target with only `Meta`; that target has no custom
`get_queryset`. Therefore the test cannot exercise the captured-model dependency in
[`django_strawberry_framework/optimizer/walker.py::_build_child_queryset`][walker].
The live visibility rows exercise custom hooks but use ordinary target metadata, so removing
the forwarded model merely adds class reads there while preserving their rows and SQL.

I checked this with a process-local diagnostic change that drops `target_model` at the
child-builder call. No repository file was changed. A real `DjangoSchema` planned both the
list relation and its connection sibling:

| Target hook | Captured model forwarded | Target-definition reads |
| --- | --- | --- |
| Default | Yes | 0 |
| Default | No | 0 |
| Custom | Yes | 0 |
| Custom | No | 4 |

All four requests completed without errors. This demonstrates why the default-hook test
cannot detect loss of the model-forwarding part of the fix. The recorded failability mutation
instead drops the entire child definition; it breaks earlier metadata decisions too and does
not isolate this dependency.

**The current production forwarding is correct.** The needed correction here is the proof,
not another metadata abstraction: add an instrumented custom-hook target through the real
optimizer pipeline, with its decoy armed after construction. Exercise list and connection
paths separately so one cannot hide the other's regression. Require the hook to run and
require zero definition reads. Remove only the forwarded-model dependency during the
subsequent authorized failability run.

Keep the default-hook cache case and assert its cache transition explicitly. My unmodified
probe measured `(hits=0, misses=1, size=1)` then `(1,1,1)`; custom hooks correctly measured
`(0,1,0)` then `(0,2,0)`, because their plans must not enter the cross-request cache.
Calling a second execution “warm” without checking reuse would still pass if caching stopped.
The committed test uses plain `strawberry.Schema`; the spec specifically calls for
`DjangoSchema`, which the diagnostic probes show can exercise this contract.

These identity/read-count assertions legitimately stay package-side. Preserve the new live
anonymous/staff visibility and keyset-window rows; they prove the consumer consequence and are
not redundant copies of the metadata test.

## P3-1 — four new catalog tests do not follow the explicit first-statement seed rule

Location: [`examples/fakeshop/test_query/test_products_visibility_api.py`][live-visibility]:

- `test_anonymous_planned_list_relation_omits_the_targets_private_rows`;
- `test_staff_planned_list_relation_keeps_every_row`;
- `test_anonymous_planned_relation_connection_window_omits_the_targets_private_rows`;
- `test_staff_planned_relation_connection_window_keeps_every_row`.

Each starts with `_hide_one_parents_items()`. That helper calls `services.seed_data(2)`
internally. The data does use the approved service, but [AGENTS.md][agents] and the
[live-test manual][live-readme] explicitly require the seed call as the test's first executable
statement.

Move `services.seed_data(2)` to the start of each test and leave the shared helper responsible
only for arranging privacy and deriving expected identities. Do not seed twice or replace the
service with hand-built catalog rows. The current exact-membership comparisons, hidden-row
witnesses, table-filtered query count, and staff controls are useful and should remain.

## P3-2 — several current instructions still contradict the implemented contract

These are small corrections, not grounds to reopen the resolved architectural findings:

- `django_strawberry_framework/list_field.py::_check_nonzero_offset_guard` says an empty
  queryset with “no active orderset or model ordering is accepted.” Its implementation and
  Decision 6 reject that shape. Only the eligible active-order case can rely on the
  empty-queryset behavior. Correct the docstring when repairing P2-1.
- The spec's “Caps and error table” introduces `ListArgumentError` as “one internal type,”
  then explicitly declares it public, catchable, and root-exported. Remove “internal” from
  the introduction; the implementation correctly exports it.
- The [build plan][build-050]'s status says the sixth gate passed, but its final gate item
  still instructs a rerun after remediation; the [build record][bld-final]'s sixth-review
  heading still says “gate pending” above its completed gate results. Reconcile those
  current instructions with the status. Keep superseded historical results identified as
  historical. This does **not** mean the recorded sixth-review runs failed.

## Prior findings verified as resolved

- **Canonical target acceptance:** focused probes supplied both a fabricated same-origin
  object and a copied real definition to `DjangoListField`, `DjangoConnectionField`,
  `DjangoNodeField`, and `DjangoNodesField`. All eight constructions raised
  `ConfigurationError`. The shared validator compares against the registry's exact object;
  the new dropped-registration test also reaches that same guard.
- **Connection-cache provenance:** a warm entry rejected a copied definition and still
  returned the original generated class for its canonical definition afterwards.
- **Optimizer definition threading:** unmodified real-schema probes recorded zero
  request-time target-class definition reads for both default and custom hooks, selecting
  both relation vocabularies. Cacheable default-hook plans actually hit the cache on the
  second execution; custom-hook plans were rebuilt. The source now carries the child
  definition through hints, traversal, visibility, and keyset planning. P2-3 concerns the
  committed regression proof, not a remaining production reread.
- **Terminal ledger closure:** delayed task and copied-context worker probes each observed
  `closed=True, records=0, claim=None` after attempting publication. The tombstone and
  close-before-reset ordering are present. The committed task test also checks standalone
  normalization after scope exit.
- **Dead state and glossary:** the removed `_dst_node_type` and
  `resolve_declared_cursor_state` have no remaining references in the searched package,
  package-test, and live-query corpus (287 files). Both relevant glossary entries now describe
  generated concrete connection classes consistently.
- **Verification reporting:** the sixth-review record now reports zero failures and an
  isolated floor run, while explicitly distinguishing the earlier failed invocations from
  passing coverage. This resolves the previous substantive reporting issue; P3-2 is the
  remaining stale current wording.

## Architectural and repository assessment

The implementation remains aligned with GOAL's declarative collection and optimizer direction.
Consumer domain types and OrderSets use nested `Meta`; the cookbook still maps naturally to
connection fields for Relay responses, with list fields as the separate flat response shape.
Graphene-Django's cursor-converting offset and Strawberry-Django's pagination envelope are
deliberately different surfaces, not missing requirements to import here.

Keep the current single owners: signature publication in the field factory, ordering and
normalization in OrderSet, visibility/routing reconstruction in the shared queryset boundary,
and row windows/deadlines in resource policy. The two production repairs above belong at those
existing owners and require no new consumer setting or input system.

The new planned-visibility tests correctly assert distinguishable private rows, staff controls,
and one child-table query across multiple parents. New externally observable order and cleanup
verdicts must likewise be covered through live HTTP. Do not replace them with private-helper
tests or add live twins without retiring redundant stand-ins. Package tests remain appropriate
for construction, cache identity, normalization transport, and exact diagnostic notes.

No production code, tests, settings, release literals, changelog, database rows, or generated
documents were edited by this review. No branch or commit was created. Only this requested
review document was overwritten; concurrent work was preserved.

## Correction order and verification

1. Correct effective-order selection at the existing offset guard and close the deadline
   cleanup gap at the shared async bounding seam, with live regressions in the same change.
2. Strengthen the custom-hook metadata proof and cache assertions; repair the four seed-call
   sites and current contradictory prose.
3. When the maintainer requests test execution, prove each new regression can fail by removing
   its specific boundary, then run the required default, sharded, and floor checks. Preserve
   the passing metadata/ledger fixes. Record the measured tree and exit status.

Review-document validation: `uv run ruff format .` left all 444 files unchanged;
`uv run ruff check --fix .` passed; `git diff --check -- docs/feedback.md` was clean.
All 14 reference links have definitions, with no unused definitions. The source-layout checker
explicitly excludes this review file, so its exit status is not claimed as a layout audit.
No fresh test-suite or coverage acceptance is claimed here.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[goal]: ../GOAL.md
[start]: ../START.md

<!-- docs/ -->
[spec-050]: spec-050-list_field_arguments-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[bld-final]: builder/bld-final.md
[build-050]: builder/build-050-list_field_arguments-0_0_15.md

<!-- django_strawberry_framework/ -->
[list-field]: ../django_strawberry_framework/list_field.py
[resource-policy]: ../django_strawberry_framework/resource_policy.py
[walker]: ../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-connection]: ../tests/test_connection.py

<!-- examples/ -->
[live-readme]: ../examples/fakeshop/test_query/README.md
[live-visibility]: ../examples/fakeshop/test_query/test_products_visibility_api.py

<!-- scripts/ -->

<!-- .venv/ -->
[django-compiler]: ../.venv/lib/python3.14/site-packages/django/db/models/sql/compiler.py

<!-- External -->
[cookbook-schema]: ../../django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py
