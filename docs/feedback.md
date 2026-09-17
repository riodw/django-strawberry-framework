# Adversarial review: raw-list QuerySet admission and release evidence

Date: 2026-09-17

Reviewed tree: `HEAD 92e4efeb` plus the current working-tree changes

Scope: [`spec-050`][spec-050], [`build-050`][build-050], the implementation, and the
repository rules in [`AGENTS.md`][agents]. I used focused runtime probes with the installed
fakeshop; I did not run pytest because the repository rule reserves it for an explicit request.

## Verdict

Do not mark this card DONE yet. The policy-authority, runner-owned extension state, refusal,
executor-mode, and stream-lease claims reviewed in the preceding rounds appear structurally
fixed. A new, independent boundary failure remains: the universal raw-list ceiling trusts a
consumer `QuerySet` subclass's `__getitem__` implementation. The failure is reachable through a
real `DjangoListField` relation over a package `DjangoSchema`, so it is a release blocker rather
than a package-only curiosity.

The implementation currently has no safe admission rule between “this value is a QuerySet” and
“call its slice.” The shared visibility sealer already has the right architectural idea (rebuild
a framework-owned plain queryset), but the raw-list bounding seam and the no-visibility relation
resolver do not use it.

## P1 — a QuerySet subclass can return every row past `max_list_rows`

### Reproduction

[`django_strawberry_framework/resource_policy.py::_bounds_by_its_own_slice`][resource-policy]
classifies every `isinstance(result, QuerySet)` value as slice-bounded. It then calls
`result[start:stop]` in [`resource_policy.py::_windowed_rows`][resource-policy]. A consumer
subclass owns that `__getitem__` call and can ignore the slice:

```text
ResourcePolicy(max_list_rows=1)
Evil(QuerySet).__getitem__(slice) -> list(self)
bounded_rows(evil_queryset, info)        -> 75 rows
bounded_rows_async(evil_queryset, info)  -> 75 rows
```

The same seam accepts a non-QuerySet object whose `__class__` property reports `QuerySet`:

```text
isinstance(fake, QuerySet)               -> True
bounded_rows(fake, info)                 -> 50 rows
```

That is not only a direct-helper issue. The generated many-side resolver in
[`django_strawberry_framework/types/resolvers.py::_make_relation_resolver`][types-resolvers]
does this on the no-custom-visibility path:

1. call the relation manager's consumer-overridable `.all()`;
2. optionally read `_result_cache` from the returned object;
3. pass the resulting object straight to `bounded_rows` / `bounded_rows_async`.

There is no visibility seal on this path because the target has no custom hook. I patched a
reverse-FK manager to return the hostile queryset, mounted a real `DjangoListField` over a
`DjangoSchema` with `ResourcePolicy(max_list_rows=1)`, and posted through a real GraphQL view.
The response contained four related `Loan` rows for one patron, not one:

```json
{"data":{"patrons":[{"name":"evil-probe2",
  "loans":[{"note":"e0"},{"note":"e1"},{"note":"e2"},{"note":"e3"}]}]}}
```

The same result occurs in direct `execute_sync` and in the exported sync/async bounding helpers.
This contradicts Decision 8 and the Definition of done: a raw list is supposed to have one
unconditional ceiling, and the spec says that a QuerySet slice is the package-owned operation
that carries the limit into SQL. A consumer subclass is not package-owned merely because
`isinstance` returns true.

### Root-cause fix (required)

Create one shared package-private “raw-list source normalization” seam and make both the
exported helpers and the generated relation resolver use it. Keep the public signatures of
`bounded_rows` and `bounded_rows_async` unchanged.

The seam must:

1. Inspect the actual class with `type(value)` (never an `isinstance` check that can consult a
   hostile `__class__` property). An exact framework `models.QuerySet` may retain the SQL-slice
   fast path.
2. Treat a `QuerySet` subclass as untrusted execution state, not as an object whose methods can
   enforce the ceiling. Normalize it through the existing sealed-queryset rebuild machinery
   (or a smaller shared rebuild primitive with the same guarantees) into a plain
   framework-owned `models.QuerySet`, then slice that rebuilt object. If its state cannot be
   faithfully rebuilt, fail closed with a typed `ConfigurationError`; never fall back to the
   subclass's `__getitem__`.
3. Preserve model, query graph, routing, iterable shape, and prefetch state according to the
   existing seal contract. Do not use “exact type then `islice`” as the whole fix: that would
   restore the row-count ceiling but lose the SQL `LIMIT` guarantee for a legitimate, sealable
   project QuerySet subclass.
4. Make the admission test in the reused sealer itself identity-safe. Its current initial
   `isinstance(candidate, models.QuerySet)` can execute a hostile `__class__` property; the
   following probe currently escapes as a raw `RuntimeError`:

   ```text
   _seal_or_defect(BombWithRaisingClass(), Patron, None)
       -> RuntimeError("class bomb")
   ```

   A failed shape proof must remain a typed, fail-closed defect.
5. Normalize before relation-cache inspection. Reading `_result_cache` with ordinary `getattr`
   on a subclass is another consumer dispatch point; use the framework-owned state read or
   normalize first. The relation manager's `.all()` result must enter the same seam whether it
   came from a warm prefetch cache or an unloaded descriptor.
6. Keep the common exact-queryset path cheap. Do not run the full recursive seal once per parent
   row when the value is already an exact framework queryset; only the subclass/untrusted path
   should pay the rebuild cost. This preserves the spec's accepted SQL behavior and avoids
   turning nested relation lists into an N+1 validation cost.

### Required regression proof

Add independent, named cases (no loop over asserted cases in a live test body, per the live-tier
guide):

- package tests for a hostile QuerySet subclass through `bounded_rows` and
  `bounded_rows_async`, with the private `_windowed_rows` / `_windowed_rows_async` arms also
  covering a zero-width window (the exported helpers must keep their coordinate-free
  signatures);
- a package control for an exact framework QuerySet asserting the SQL `high_mark` remains the
  effective ceiling;
- a package case for a class-spoofing non-QuerySet, proving it cannot select the SQL-slice arm or
  escape as an untyped exception;
- a live sync `/graphql` case with a `DjangoSchema`, `DjangoListField`, a no-custom-visibility
  many-side relation, and a manager returning a QuerySet subclass; `max_list_rows=1` must yield
  one related row;
- the corresponding live async `DjangoSchema`/`AsyncDjangoGraphQLView` case. The existing async
  relation suite uses a plain `strawberry.Schema`, which does not install the package resource
  policy and therefore cannot prove this card's bound;
- a warm-prefetch control and an unloaded-manager control, both through the same normalization
  seam, plus an exact QuerySet control showing SQL limiting is retained.

The live rows belong in [`examples/fakeshop/test_query/`][fakeshop-query]; package mechanics
belong in [`tests/test_resource_policy.py`][test-resource-policy] and, if the shared sealer is
changed, [`tests/utils/test_querysets.py`][test-querysets]. Each row should assert the complete
wire payload and the row count, not merely “no errors.”

## Spec/build correction required with the code fix

Decision 8 currently distinguishes exact built-in sequences from their subclasses, but treats
“QuerySet” as one undifferentiated sliceable category. Amend it to say:

- an exact framework-owned `models.QuerySet` is sliced directly;
- a consumer QuerySet subclass is first sealed/rebuilt to a framework-owned plain queryset, or
  is rejected with a typed configuration error if sealing is impossible;
- no `isinstance`/consumer `__getitem__` result can define the ceiling.

Add the hostile-queryset relation row to the Definition of done, the package/live test plan, and
the build's predicted-file ledger. The current hostile list-subclass rows do not cover this
shape: they exercise the `islice` fallback, while the bug is specifically the QuerySet slice
arm. The current visibility-hook adversary is also insufficient because the visibility boundary
already rebuilds its result before bounding; the no-custom-visibility relation branch is the
uncovered path.

## P1 release gate — the recorded green run is not this tree

[`build-050`][build-050] records the final gate at historical commit `207c7328` and explicitly
says every descendant is ungated. The current `HEAD` is `92e4efeb`, a descendant, and the
working tree also contains uncommitted implementation/test changes. Therefore the recorded
7868/7885/463 figures do not certify this code. Before DONE, run and record on one exact final
tree:

- the full default suite at `fail_under = 100`;
- the sharded suite;
- the complete declared supported-floor scope (not the earlier focused 463-row seam run);
- formatting, lint, structural, link, citation, and tracked-path checks.

Do not copy the historical figures beside new edits. A failing or partial run is evidence that
the gate is still open, not a green record.

## Review conclusion

The operation-state and enforcement ownership design is now the right foundation. The remaining
work is to make the raw-list boundary honor that same ownership rule for QuerySets and for the
relation resolver that bypasses visibility sealing. Until that is fixed and the same-tree gates
are recorded, the package's central promise—every non-Relay list is bounded—has a reproducible
wire-level counterexample.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md

<!-- docs/ -->
[spec-050]: spec-050-list_field_arguments-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build-050]: builder/DONE/build-050-list_field_arguments-0_0_15.md

<!-- django_strawberry_framework/ -->
[resource-policy]: ../django_strawberry_framework/resource_policy.py
[types-resolvers]: ../django_strawberry_framework/types/resolvers.py

<!-- tests/ -->
[test-resource-policy]: ../tests/test_resource_policy.py
[test-querysets]: ../tests/utils/test_querysets.py

<!-- examples/ -->
[fakeshop-query]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
