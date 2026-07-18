# Adversarial code review: `get_queryset` visibility boundary

## Verdict

**Not ready to commit or push.** The staged implementation centralizes most of
the intended contract, but three security-relevant paths still violate it. Two
are direct visibility-boundary escapes and one can silently move a read to a
different database alias. The staged set also omits the required governing
decision and contains an unrelated optimizer plan.

Review target: the staged diff against `01828f61a9e7`.

## Findings

### [P1] A nested awaitable still skips visibility on async connection fields

Affected symbols:

- `django_strawberry_framework/connection.py::_build_connection_resolver`
- `django_strawberry_framework/connection.py::_pipeline_async`
- `django_strawberry_framework/utils/querysets.py::post_process_queryset_result_async`

The staged residual-awaitable guard protects async list-field consumer
resolvers only. `DjangoConnectionField` has a separate pipeline: its async
wrapper awaits the consumer resolver once and passes that value directly to
`_pipeline_async`. `_pipeline_async` calls `_prepare_pipeline_source` without
first rejecting a residual awaitable. With no `filter:` or `orderBy:` input,
the awaitable is treated as a legitimate non-queryset source and returned
unchanged, so `apply_type_visibility_async` is never called.

The implemented behavior therefore contradicts the documented invariant that
an already-awaited async list **or connection** resolver resolving to another
awaitable fails closed.

Required fix:

- Put the residual-awaitable rejection in a shared async source guard used by
  both list and connection consumer pipelines.
- Call it in `django_strawberry_framework/connection.py::_pipeline_async`
  before `_prepare_pipeline_source`.
- Add a real `DjangoConnectionField` regression whose async consumer resolver
  returns a second coroutine and assert `ConfigurationError` before visibility
  can be skipped. Test the no-sidecar shape, because that is the bypass.
- Retain the cleanup checks for native coroutines and futures.

### [P1] The concrete-table check accepts cross-model combined querysets

Affected symbols:

- `django_strawberry_framework/utils/querysets.py::_visibility_defect`
- `django_strawberry_framework/utils/querysets.py::_prepared_visibility_source`
- `django_strawberry_framework/utils/querysets.py::_normalized_visibility_result`

`_visibility_defect` validates only `QuerySet.model`. That is not sufficient to
prove which model tables can contribute result rows. Django permits a combined
queryset whose outer model is the registered model while a `UNION` branch reads
another model. The boundary accepts this because the outer queryset still says
`Category`.

A read-only probe against the staged implementation produced:

```text
accepted Category union
branch_models ['Category', 'Item']
SELECT ... FROM "products_category"
UNION SELECT ... FROM "products_item"
```

Using compatible projections such as `.only("id", "name")`, Django can
materialize rows contributed by the `Item` branch as `Category` instances.
That defeats the boundary's wrong-model rejection and can expose records from
the wrong table through read surfaces. Some downstream tails reject combined
querysets later (cascade does so explicitly, and write lookup filtering may
raise), but the shared boundary itself promises to fail closed before any
surface-specific behavior can diverge.

The same validation trusts mutable `QuerySet.model` without checking
`QuerySet.query.model`; a queryset can report the expected public model while
its SQL query still targets another model table.

Required fix:

- Validate both the queryset model and the underlying query model against the
  registered concrete model.
- Recursively validate every `query.combined_queries` branch that can
  contribute result rows. Do not rely on the outer queryset model.
- Apply the same graph validation to sources, hook returns, and every
  post-clone revalidation.
- Add regressions for a cross-model `UNION` as both source and hook return, a
  same-table proxy union, and a queryset whose public `model` disagrees with
  `query.model`.

### [P1] Evaluated-result refresh can change the hook-selected database alias

Affected symbols:

- `django_strawberry_framework/utils/querysets.py::_normalized_visibility_result`
- `django_strawberry_framework/utils/querysets.py::_revalidated_visibility_clone`
- `django_strawberry_framework/utils/querysets.py::_visibility_defect`

When the input source is unpinned, `required_alias` remains `None`, correctly
allowing the hook to choose an explicit read alias. If that hook result is
evaluated, normalization calls its consumer-overridable `.all()` and then
revalidates with the original `required_alias=None`. In strict mode, `None`
currently means "do not validate the alias", so `.all()` can silently change
the hook's chosen alias and still pass.

A read-only hostile-subclass probe against the staged code started with a hook
result pinned to `chosen`; its `.all()` returned an unevaluated queryset on
`elsewhere`. The boundary accepted the result:

```text
hook_alias chosen accepted_alias elsewhere cache None
```

This violates both sides of the contract: an unpinned read hook may choose its
alias, and every consumer-overridable clone must preserve and revalidate the
effective alias. In a sharded application this can serve rows from the wrong
database.

Required fix:

- Distinguish "no alias requirement has been selected yet" from "the clone
  must remain unrouted"; a plain `None` parameter cannot represent both.
- Once a valid hook-result queryset exists, capture its effective explicit
  `_db` choice before any refresh and require `.all()` to preserve it.
- Apply the same preservation rule to manager coercion where the manager has
  an explicit `_db`.
- Add hostile `.all()` regressions for chosen-alias-to-other-alias,
  chosen-alias-to-unrouted, and unrouted-to-routed transitions, on both sync
  and async runners.

### [P1] The required security decision and standing documentation are absent

Affected staged documentation:

- `docs/README.md`
- `get_queryset-visibility-boundary-plan.md` (replaced by this review)

The implementation changes accepted return shapes, alias behavior, evaluated
queryset identity/query-count behavior, and error messages. The approved plan
explicitly required a dedicated KANBAN card/spec because those changes conflict
with the behavior-freeze and byte-preserved-error decisions in Spec 046.

No dedicated `docs/spec-<NNN>-...md`, KANBAN card, or staged
`docs/GLOSSARY.md` update exists. Replacing the plan with this review leaves no
governing decision for the new runtime contract. The new `docs/README.md`
source reference also uses the abbreviated `utils/querysets.py` text instead
of the repository's symbol-qualified, reference-style standing-doc form.

Required fix:

- Add the dedicated card/spec authorizing the security, error, query-count,
  identity, and alias changes.
- Update `docs/GLOSSARY.md`, `docs/README.md`, and the card/spec cross-references
  in the same documentation slice.
- Use symbol-qualified source references and the required reference-style
  Markdown link-definition block.

### [P2] The staged commit contains unrelated optimizer work

Affected staged files:

- `feedback2.md`
- `django_strawberry_framework/mutations/permissions.py`

`feedback2.md` is a 327-line plan for a single-parent nested-connection
optimizer fast path. It is unrelated to the `get_queryset` visibility boundary
and should not ship in this commit. The mutation-permissions diff contains only
formatting/comment changes unrelated to this implementation and should also be
removed from this commit unless it belongs to a separately named change.

Required fix: unstage/split the unrelated files before creating the visibility
boundary commit. Do not delete concurrent maintainer work from the worktree.

### [P2] The promised representative integration coverage was not added

Affected staged tests:

- `tests/utils/test_querysets.py`
- `tests/test_permissions.py`

The new tests exercise the shared helpers and cascade integration, but the
approved test plan also required representative propagation tests for list and
connection fields, Relay, related filters, optimizer child prefetches, mutation
lookup, and shared form/DRF relation decoding. None of those integration files
is staged. This is not merely a completeness concern: the missing connection
test is why the P1 residual-awaitable bypass survived despite the list helper's
unit regression.

The unit matrix also says it covers a custom iterable but parametrizes a plain
`object()`, and it does not cover future cancellation, hostile clone model
changes, or hostile clone alias changes when the source is unpinned.

Required fix:

- Add one behavioral regression at each distinct propagation boundary from
  the approved plan instead of duplicating the entire unit matrix.
- Add the missing custom-iterable, future cleanup, cross-model combined-query,
  and alias-changing clone cases to `tests/utils/test_querysets.py`.
- Keep executed non-default-database coverage behind `FAKESHOP_SHARDED=1`.

## What is sound in the current implementation

- Framework-owned direct `get_queryset` calls remain single-sited in
  `apply_type_visibility_sync` and `apply_type_visibility_async`; the similarly
  named django-filter method is a different contract.
- Normal queryset/manager return coercion, wrong outer-model rejection,
  evaluated cache refresh, pinned-source precedence, explicit divergent-alias
  rejection, one-await async semantics, and sync misuse cleanup are centralized
  coherently.
- Cascade permissions retain their local slice, combinator, grouping,
  field-specific distinct, annotation-shadow, and `extra()`-shadow checks while
  using the shared boundary for result shape and alias handling.
- Cascade `ContextVar` token reset remains exception-safe.
- `git diff --cached --check` passed before this review file was replaced.

## Review method and limits

- Inspected every staged source, test, and documentation diff.
- Traced all package-owned `get_queryset` invocations and every
  `apply_type_visibility_sync` / `apply_type_visibility_async` call site.
- Ran read-only Django probes for cross-model combined querysets, public-model
  versus query-model disagreement, and alias-changing evaluated clones.
- Did not run pytest, in accordance with the repository instruction that
  pytest runs require explicit maintainer authorization.

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
