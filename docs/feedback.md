# Adversarial implementation re-review: spec 050

Date: 2026-09-13

## Verdict

**Not accepted yet.** The previous ordering-precedence, deadline-source cleanup, captured-model,
and live-seeding findings are closed in the current tree. This pass found one production
lifecycle defect, two material proof gaps, and two lower-priority repository-contract issues.

The reviewed revision is `d727a256` (`fix(spec-050): judge the offset guard on the order Django
compiles, and close a source its own deadline rejects`). The working tree also contains unrelated
dirty `spec-047` / builder documentation; those files were not changed. No pytest command was
run, in accordance with [AGENTS.md][agents]. The behavioral checks below are from source
inspection and small, non-pytest probes; the earlier recorded full-suite figures are not treated
as fresh evidence because this revision changed production code.

The architectural comparison also covered the local Strawberry-Django implementation, the
installed Graphene-Django reference, and the cookbook `recipes/schema.py` shape named by the
project instructions; their cursor/offset behavior is treated as migration context, not as a
substitute for this package's Meta-first contract.

## Findings

### P2-1 — cleanup can swallow task cancellation when a source error is already primary

Location: [`resource_policy.py::_close_async_iterator`][resource-policy] and
[`resource_policy.py::_cleanup_rejected_async_iterable`][resource-policy].

Both helpers catch `BaseException` and, whenever a primary exception already exists, turn the
caught value into a diagnostic note. That includes `asyncio.CancelledError` (and
`KeyboardInterrupt` / `SystemExit`). Consequently, if iteration raises first and cancellation
arrives while `aclose()` is awaiting, the task finishes with the source error, is no longer marked
cancelled, and the cancellation is only a note.

I reproduced this without pytest using an async iterator whose `__anext__` raises `ValueError`
and whose `aclose` waits. Cancelling the task while `aclose` was suspended produced:

```text
ValueError source
notes ['bounded_rows_async iterator cleanup failed: CancelledError()']
cancelled False
```

That is unsafe for an async GraphQL request: a client disconnect or server shutdown can be
silently converted into a field error while cleanup is still incomplete. The same broad catch in
the pre-rejection helper has the analogous risk. Ordinary cleanup failures should remain notes
when a useful primary error exists, but cancellation and process-control exceptions must not be
suppressed.

**Required correction:** preserve the primary-error precedence for ordinary `Exception` cleanup
failures, while re-raising `asyncio.CancelledError` (and other `BaseException` control signals)
after making the best safe cleanup attempt. Add a unit test that cancels during `aclose()` after a
source exception and asserts that cancellation remains observable; keep the existing ordinary
failure-note tests.

### P2-2 — the async deadline regression is timing-racy and does not cross an async resolver await

Location: [`test_async_deadline_rejection_closes_the_source_it_never_advanced`][async-list-tests].

The test sets `_PASSED_DEADLINE_SECONDS = 0.000_001` and uses a synchronous resolver:

```python
def _resolver(root, info):
    it = _ClosableAsyncIterator(branches)
    holder["it"] = it
    return it
```

It therefore relies on the request taking more than one microsecond between policy stashing and
the bounding seam. That is overwhelmingly likely, but it is not a deterministic contract. More
importantly, the specification's claim is that the deadline expires *while the consumer resolver
awaits after obtaining the source*; this test never executes an async resolver or an await after
the iterator is constructed. A regression in the async-await handoff could remain green while
this test still observes the ordinary synchronous-return path.

**Required correction:** make the boundary deterministic. Use a controllable monotonic clock (or
an explicit test-only deadline handoff) and an `async def` resolver that records the iterator,
awaits across the controlled boundary, then returns it. Exercise both the default window and
`limit: 0`, and retain the zero-advance / one-close / complete-extension assertions. The package
unit test already uses a directly expired deadline; the live test needs the same determinism at
the resolver-await boundary.

### P2-3 — async effective-order acceptance has no must-not assertion for dormant randomness

Location: [`test_async_offset_accepts_extra_ordering_over_a_dormant_random_order`][async-list-tests]
and the corresponding requirement in [`spec-050`][spec-050].

The test asserts only that the returned row is `Bravo`. It does not inspect SQL or any equivalent
effective-order state. The random ordering is therefore not proven dormant on the async path: a
regression that leaves `?` effective can still return `Bravo` by chance (the fixture has three
rows), and async SQL capture is normally empty because ORM work runs in a `sync_to_async`
executor thread. The synchronous twin does assert the filtered SQL, but that does not prove the
async pipeline's independent call site.

Definition 27 requires the effective-order acceptance to be pinned in both colorings and says the
captured SQL carries the deterministic `id` order. Either the async test needs an executor-safe
SQL/state witness (for example, an instrumented apply seam that records the selected
`extra_order_by`/`order_by` state before returning, plus the exact row), or the specification must
explicitly relax its async SQL wording and state the replacement observable. Keep an async
rejection control and a stable-order control so the row cannot be produced by a one-way guard.

### P3-1 — the exported bounding helper trusts unvalidated coordinate arguments

Location: [`resource_policy.py::bounded_rows`][resource-policy] and
[`resource_policy.py::bounded_rows_async`][resource-policy].

The new `requested_limit` / `offset` parameters are documented as “assumed prevalidated by the
caller”, and the helpers are exported from `resource_policy.__all__`. A direct caller can therefore
bypass the request policy:

```text
ResourcePolicy(max_list_rows=2), bounded_rows(range(10), offset=0, requested_limit=10)
=> all ten rows
```

`DjangoListField` correctly validates these coordinates before calling the helpers, so this is not
a current GraphQL-field bypass. It is nevertheless a public-module footgun and makes the helper's
own advertised bound false for callers who import it directly.

**Required correction:** either make the coordinate-bearing seam package-private and remove it
from the public export/documentation, or validate the supplied coordinates against the effective
policy inside the seam (with the same typed error contract). Do not leave a public resource-bound
primitive whose caller can silently widen the bound.

### P3-2 — added/retained tests violate the repository's test-contract rules

Two concrete issues remain under [AGENTS.md][agents] and the live-test manual
[`examples/fakeshop/test_query/README.md`][live-readme]:

- [`tests/test_connection.py::test_the_optimizer_plans_a_relation_without_reading_the_target_class`][test-connection]
  loops over the cold and warm executions in one test body. The manual's one-node rule requires
  explicit assertions or separately identified cases; a failure in the second execution is hidden
  behind one node id and failability cannot remove either state independently.
- [`tests/test_list_field.py`][test-list-field] still claims in its module docstring that it holds
  22 tests (five validation plus 17 behavior), while the current module contains 126 test
  functions and now owns substantially different spec-050 mechanics. That description is not an
  authoritative inventory and conflicts with the repository's “test docstring = invariant” rule.

**Required correction:** spell out the cold and warm assertions without a body loop (or split them
into independently identified tests while preserving the cache transition), and rewrite the stale
module description to describe the actual ownership without frozen test counts.

## Closed checks from the preceding pass

- [`list_field.py::_selected_ordering`][list-field] now follows Django compiler precedence:
  `extra_order_by`, explicit `order_by`, then an enabled model default. Both random-term and
  model-default predicates use that selected state, so dormant random terms no longer reject a
  stable page and random model defaults no longer pass.
- [`resource_policy.py::bounded_rows_async`][resource-policy] routes deadline rejection through
  the shared pre-iteration cleanup helper, including `limit: 0`, while preserving the resource
  error and its extensions when ordinary cleanup fails.
- [`tests/test_connection.py::test_the_optimizer_plans_a_relation_without_reading_the_target_class`][test-connection]
  now runs through `DjangoSchema`, separately exercises list and connection vocabularies, and
  includes a custom visibility hook so the captured model is actually consumed by the planner.
- The new live catalog rows seed through their approved helper as their first executable
  statement; the async suite uses transaction-enabled database markers and does not enable
  `DJANGO_ALLOW_ASYNC_UNSAFE`.

## Verification boundary

The package's prior full/default, sharded, and floor figures are historical: the current revision
changed `list_field.py`, `resource_policy.py`, and their tests after those runs. A fresh gate is
still required after the P2 items are corrected. This review intentionally did not modify the
concurrent `spec-047` or builder files and did not run pytest.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[start]: ../START.md
[goal]: ../GOAL.md

<!-- docs/ -->
[spec-050]: spec-050-list_field_arguments-0_0_15.md
[live-readme]: ../examples/fakeshop/test_query/README.md

<!-- docs/SPECS/ -->
[spec-020]: SPECS/spec-020-list_field-0_0_7.md
[spec-030]: SPECS/spec-030-connection_field-0_0_9.md

<!-- docs/builder/ -->
[build-050]: builder/build-050-list_field_arguments-0_0_15.md

<!-- django_strawberry_framework/ -->
[list-field]: ../django_strawberry_framework/list_field.py
[resource-policy]: ../django_strawberry_framework/resource_policy.py

<!-- tests/ -->
[test-connection]: ../tests/test_connection.py
[test-list-field]: ../tests/test_list_field.py

<!-- examples/ -->
[async-list-tests]: ../examples/fakeshop/test_query/test_list_field_async_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
