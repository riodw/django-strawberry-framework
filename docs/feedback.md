# Adversarial implementation re-review: spec 050

Date: 2026-09-13

## Verdict

**Not accepted.** The latest remediation fixes the previously reported list/connection factory
re-reads, child-delegated order attestation, exact-boolean trusted bound, and combined raw-response
oracle. Three architectural defects remain:

1. the nested-connection optimizer still asks the target class for its definition during every
   request, including on the visibility decision that can determine whether `get_queryset` runs;
2. the shared field validator accepts a fabricated, non-registry definition, and the connection
   cache can consequently return a class built from different metadata than the field that uses
   it; and
3. closing the order-normalization ledger merely empties it, so a child task holding a copied
   context can repopulate and claim invocation state after the owning resolution has ended.

The first two are foundational metadata-integrity failures. They invalidate the specification's
one-definition dependency and registered-target claims, and they must be corrected before any
secondary cleanup or gate rerun. The third is a real lifecycle failure against the ledger contract,
although it does not by itself expose one request's ledger to a different request.

This pass reviewed the full [specification][spec-050], the relevant production implementation and
tests, [AGENTS.md][agents], [GOAL.md][goal], the [live-test guide][live-readme], Graphene-Django,
Strawberry-Django, and the django-graphene-filters [cookbook schema][cookbook-schema]. The reviewed
snapshot had `96b9e047` at `HEAD`; the card-050 remediation is in its `aadca5a2` ancestor. Unrelated
files changed concurrently during the review and were not reverted or included as card-050 work.

No pytest command was run: [AGENTS.md][agents] permits pytest only when explicitly requested. The
behavioral evidence below comes from focused, non-pytest construction and real-schema execution
probes, plus direct production-dataflow inspection.

## Blocking findings

### P1-1 — the nested optimizer violates the one-definition invariant and can skip visibility

Decision 1 says the accepted target definition is the field's sole construction and execution
dependency. It expressly says a synthesized relation connection receives its definition from
[`types/finalizer.py::finalize_django_types`][finalizer] and never asks the target class for it.
That is true for the resolver built by finalization, but false for the optimizer that plans the same
field at request time.

[`optimizer/walker.py::_resolve_relation_target`][walker] already receives the parent definition.
Its `related_target_for(...)` answer contains the child `DjangoTypeDefinition`, but the helper
discards that object and returns only `target_definition.origin`. The nested planner then performs
fresh class-mediated reads:

- [`optimizer/nested_planner.py::plan_connection_relation`][nested-planner] calls the injected
  [`optimizer/walker.py::_target_has_custom_get_queryset`][walker];
- that helper calls [`types/base.py::DjangoType.has_custom_get_queryset`][type-base], which reads
  `__django_strawberry_definition__` again;
- the planner calls [`keyset.py::resolve_declared_cursor_state`][keyset], which independently reads
  the same attribute; and
- when the first read says a custom hook exists,
  [`optimizer/walker.py::_build_child_queryset`][walker] calls the visibility runner without its
  captured-model seam, causing a further definition read inside
  [`utils/querysets.py::_captured_model`][querysets].

A real `DjangoSchema` probe enabled `DjangoOptimizerExtension`, selected a nested
`itemsConnection(first: 1)`, armed a metaclass definition-read counter only for execution, and used
a no-SQL root source. The request succeeded and recorded:

```text
errors None
request_definition_reads 2 ['__django_strawberry_definition__',
                            '__django_strawberry_definition__']
```

That is the minimum default-hook case. A custom visibility hook adds the visibility runner's model
read. This is not a harmless accounting mismatch. A stateful or replaced target definition can
answer `has_custom_get_queryset=False`; `_build_child_queryset` then skips
`apply_type_visibility_sync` entirely and constructs the optimized prefetch from the unscoped
default manager. The resolver consumes that planned window rather than re-running the per-parent
visibility pipeline. The very threat Decision 1 cites—metadata changing after acceptance—therefore
reaches a row-visibility decision.

The current root-connection read-once tests do not cover this. They build a plain Strawberry schema
without `DjangoOptimizerExtension`, so the nested planner is never entered. A root connection also
cannot prove the synthesized relation path.

Root-cause correction:

- Preserve the child definition returned by `definition.related_target_for(...)`; do not collapse
  it to its `origin` and later reconstruct metadata through the class.
- Thread `(target_type, target_definition)` into the nested planner. Read
  `target_definition.has_custom_get_queryset` directly and call
  [`keyset.py::declared_cursor_state_for_definition`][keyset].
- Thread `target_definition.model` into the visibility runner's existing `model=` seam.
- Keep the registry-only fallback for the unresolved relation case, but have it return the registry
  definition and origin as one answer. A missing definition must degrade or reject according to the
  existing relation-planning contract; it must never trigger a class-attribute lookup.
- Grep the complete planned-connection path and leave no request-time
  `__django_strawberry_definition__` read keyed by the target class.

Required proofs:

- Package-level read counter and decoy-definition proof through a real `DjangoSchema` with
  `DjangoOptimizerExtension`, covering cold and warm optimizer plans.
- A live `/graphql/` row over a shipped synthesized relation whose child `get_queryset` hides a
  distinguishable row; prove the optimized path returns the same visible rows as the unplanned
  fallback. This is consumer-observable and therefore belongs in the live tier under the
  [test guide][live-readme].
- Offset and keyset targets, so both cursor vocabularies are proven to use the captured definition.

### P1-2 — “registered DjangoType” validation is forgeable, and the cache has no provenance check

[`list_field.py::_validate_djangotype_target`][list-field] currently proves only that the target is
a `DjangoType` subclass and that whatever object the class attribute returned has
`origin is target_type`. It does not prove that the object is a `DjangoTypeDefinition`, that the
target is present in [`registry.py::DjangoTypeRegistry`][registry], or that the returned object is
the exact definition registered for that class.

A focused construction probe created an unregistered child of a real `DjangoType`, assigned a
`SimpleNamespace(origin=child, model=Item, orderset_class=None)` as its definition attribute, and
called `DjangoListField(child)`. The result was:

```text
registry_definition_before None
factory_accepted_fabricated_definition True
registry_definition_after None
```

The field advertised by the error text as requiring a registered target therefore accepts a target
the registry has never seen. Schema completion can then fail later with a Strawberry runtime-type
error because the inherited GraphQL type and the fabricated Django model are unrelated. That is a
late engine failure in place of the promised typed construction-site rejection.

The same missing identity check breaks the connection cache's own guarantee.
[`connection.py::_connection_type_for`][connection] keys only on `target_type` and returns a warm
entry without checking which definition produced it. A second probe warmed the cache from a real
definition without `total_count`, then supplied a same-origin replacement definition with
`connection={"total_count": True}`. Validation accepted the replacement, while the cache returned
the first class:

```text
second_definition_total_count {'total_count': True}
cached_connection_fields ['page_info', 'edges']
cache_matches_second_definition False
```

The second field's signature and pipeline are built from its captured replacement, but its return
class is built from the earlier definition. This directly contradicts
`_connection_type_for`'s statement that connection shape and published arguments cannot come from
different answers. It also makes [`connection.py::clear_connection_type_cache`][connection]'s
claim that a stale entry can never be wrong untrue.

The current warm-cache test counts reads but never changes the definition between fields and never
inspects the second field's connection shape. It therefore proves cache reuse, not cache
provenance.

Root-cause correction:

- Make the shared validator compare its one contained class read by identity with
  `registry.get_definition(target_type)`. Accept only the canonical registered
  `DjangoTypeDefinition`; reject a missing, fabricated, inherited, or alternate same-origin object
  with `ConfigurationError` at field construction.
- Keep the hostile-read containment: a raising metaclass must still become the typed unregistered
  target error rather than leak its exception.
- Make cache provenance explicit. Store the canonical definition identity beside the generated
  class and verify it on every warm hit, or key the cache by an identity pair while separately
  enforcing the one-canonical-definition rule. Silently returning the first shape is not safe.
- Use the same canonical validator for list, connection, and Relay node field entry points so the
  definition of “registered target” cannot drift by factory.

Required proofs:

- An unregistered subclass with an inherited definition remains rejected.
- A fabricated same-origin object and a real `DjangoTypeDefinition` copy with the same origin are
  both rejected.
- A warm cache presented with alternate same-origin metadata fails at construction rather than
  returning the old shape.
- Ordinary list, root connection, synthesized relation connection, and node fields still consume
  the registry's exact object with the existing one-read counters armed.

This correction matches the project references. Graphene-Django binds a model and connection once
on canonical `_meta` during type construction and registers that type; its fields consume `_meta`
rather than accept a caller-swapped lookalike. Strawberry-Django similarly resolves an attached
Django definition for the field/type it is processing. The cookbook uses only declarative
`class Meta` declarations and `AdvancedDjangoFilterConnectionField(Type)`. None of these surfaces
ask consumers to manage or replace framework metadata objects. [GOAL.md][goal] likewise promises
Meta-driven declarations and loud failure for unregistered targets.

### P2-1 — a closed normalization ledger can be reopened by a copied context

[`orders/sets.py::_NormalizationLedger.close`][orders-sets] clears `_records` and `_claimed`, but
the object has no closed state. A task created while the scope is live receives that same ledger
object through its copied `ContextVar`. After the parent exits and calls `close()`, the child can
resume, call the public `OrderSet.apply_*`, append a new record, and claim it from its retained
context.

A focused delayed-child probe produced:

```text
after_scope_before_child 0
child_after_closed_scope (1, True, 1)
parent_binding None
```

The parent binding is correctly reset, so this does not make the next request inherit the old
ledger. The object nevertheless regains invocation records after its advertised terminal state,
can retain the input object for the lifetime of the child context, and can reduce a later active
term check inside that orphan context from the standalone double-normalization path to an
attested one. That contradicts both the implementation docstring and the spec's promise that
emptying the ledger prevents a child that outlives the resolution from carrying invocation state.

Existing tests prove a new scope starts empty and that child/worker publication works while the
owning scope remains live. Neither test delays the descendant until after scope exit, which is the
boundary the prose claims.

Root-cause correction:

- Add a lock-protected `_closed` tombstone.
- Make `close()` atomically set `_closed=True` and clear both collections.
- Make `publish()` after close a no-op, matching publication outside an active scope, and make
  `claim()` after close return no attestation. A closed ledger must be terminal.
- In `capture_applied_order_normalization`, guarantee both operations with nested `try/finally`.
  Close before resetting the parent binding so descendants observe the tombstone immediately and
  a reset failure cannot skip closure.

Required proofs:

- A task captures the scope, waits until after exit, then calls public `apply_async`; the ledger
  remains empty and its active-term check takes the standalone double-normalization path.
- The same delayed-after-close proof through `contextvars.copy_context()` and a worker thread.
- Retain the live child-delegating success and A/B/B rejection rows while the scope is open; the
  tombstone must not regress the valid transport the remediation added.

## Documentation, test, and maintenance findings

### P2-2 — the recorded verification state is internally contradictory and is not current

The [specification][spec-050] header says full and sharded verification are pending. The final
Definition-of-Done checkbox remains open. The [build plan][build-050] status instead says both
default and sharded tiers were rerun green at 100% on the fifth review, while its final gate item
still instructs a rerun after remediation.

The [final build record][bld-final] repeats the “rerun green” characterization, but the fifth-review
figures explicitly record one failing governance test in each invocation:

- default: `7719 passed, 40 skipped`, plus one failure;
- sharded: `7736 passed, 37 skipped`, plus the same one failure; and
- floor verification: not run.

A run with a failing test is not green, even when the failure is attributed to concurrent work.
Furthermore, the repository has advanced beyond those runs and currently has unrelated dirty
files, so neither historical invocation certifies the present tree. The build documents should
record one coherent state: coverage reached 100% in those attempted runs, both processes still
failed, floor verification is absent, later production fixes will supersede the attempts, and the
final gate is not green.

After the foundational corrections, run the current tree through formatting, lint, structural and
link checks, default pytest with `fail_under=100`, sharded pytest, and the supported-version floor.
Record command, exit status, counts, coverage, and exact tree/commit state. Passing coverage while
a test fails is evidence about coverage only, not a passing suite.

### P3-1 — `_dst_node_type` is dead state with a false ownership comment

[`connection.py::_generate_connection_class`][connection] writes `_dst_node_type` and says the
optimizer's window handoff reads it. A repository-wide search finds no reader in production or
tests; the only package occurrence is the write, plus a later comment comparing another private
attribute to it. The keyset reader was correctly changed to consume `_dst_keyset_state` fixed at
class generation, and the nested planner receives `target_type` independently.

Remove `_dst_node_type` and the false comments unless a real, reviewed consumer is intended. Dead
per-class state is small, but retaining it obscures the actual definition dataflow and makes future
reviewers believe the optimizer and generated connection share an identity channel that does not
exist.

### P3-2 — the glossary describes two incompatible no-`totalCount` return types

The [`DjangoConnection` glossary entry][glossary] correctly says every target receives a generated
concrete `<TypeName>Connection` and that `DjangoConnectionField` never hands Strawberry the generic
base. The [`Meta.connection` entry][glossary] later says a false opt-in uses `DjangoConnection[T]`
without the field. Production always uses the concrete generated subclass, so the latter sentence
is stale.

Correct the glossary through its database-first documentation workflow and regenerate the rendered
file; do not hand-edit over the current concurrent glossary/database work. Add or retain one
construction-tier test for concrete-class identity and leave wire shape to the existing live
connection tests, exactly as the [live-test guide][live-readme] prescribes.

## Corrections verified in this pass

The following changes are sound and should be preserved:

- `DjangoListField` captures the validated definition's model and `orderset_class`; its default
  seed, both visibility seals, post-`OrderSet` seal, signature, and resolver dispatch use those
  captured values rather than rereading the class.
- Root `DjangoConnectionField` and synthesized relation resolvers thread the captured/registry
  definition through their signature, pipeline, total-order, keyset, and generated-class paths.
  P1-1 is specifically the optimizer's parallel request-time path; P1-2 is the missing canonicality
  check before either factory trusts the captured object.
- `trusted_max_rows` is now validated as an exact `bool`, and the policy primitive widens only for
  literal `True`.
- The append-only normalization ledger correctly transports child-task and worker-thread
  applications while the owning scope is live, matches by class and input identity, and rejects
  disagreeing applicable attestations. P2-1 adds terminal closure; it does not call for returning to
  a mutable last-writer-wins slot.
- The no-`OrderSet` scope predicate now receives the captured sidecar and stays inert.
- Both legacy omission/null oracles, including the combined source, compare raw
  `HttpResponse.content` rather than parsed projections.
- Exact integer validation, routing-intent freeze/pin, post-order sealing, async iterator cleanup,
  wire-name lookup, and visibility-before-order composition remain aligned with the specification.
- The public API remains DRF/Graphene-shaped: consumer types configure sidecars through nested
  `Meta`; no stacked Strawberry-Django decorators or list-specific consumer input type were added.
- No card-050 code uses a test-only workaround, new `pragma: no cover`, raw standing-document line
  references, or a source comment naming this review file.

## AGENTS.md and GOAL.md assessment

| Rule | Verdict | Evidence |
| --- | --- | --- |
| DRF first, Strawberry second; consumer configuration through `Meta` | Pass | The public type/list/connection surface retains the cookbook and GOAL shape. |
| Unregistered targets fail loudly | **Fail** | P1-2 accepts a fabricated same-origin definition with no registry entry. |
| Root-cause repair, never a test-only workaround | **Blocked** | P1-1, P1-2, and P2-1 require production dataflow/lifecycle changes. |
| Live-first for query-reachable behavior | Partial | Most list behavior is live; the optimizer visibility boundary in P1-1 lacks a live synthesized-relation proof. |
| Test placement follows ownership | Pass with one required addition | Construction/cache and ledger mechanics belong in `tests/`; optimized row visibility belongs in `examples/fakeshop/test_query/`. |
| Fakeshop data discipline | Pass | Reviewed catalog/auth live tests use the prescribed seed helpers; no new hand-rolled rows were introduced by card 050. |
| Coverage remains package-only at `fail_under=100` | Configuration passes; gate does not | Historical runs reached 100%, but both recorded fifth-review invocations still had a failure and do not cover later fixes. |
| No pytest unless explicitly requested | Pass for this review | No pytest command was run. |
| Run formatting and lint after edits | Pass | `uv run ruff format .` changed no files; `uv run ruff check --fix .` passed. |
| Preserve concurrent work | Pass for this review | Unrelated dirty files and commits were inspected only as needed and not reverted or folded into this review. |

## Required correction order and acceptance gate

1. Establish one canonical metadata source: make the shared validator accept only the registry's
   exact definition and make connection-cache entries prove their definition provenance.
2. Carry that canonical definition through the nested optimizer, including visibility and keyset
   decisions, with zero request-time target-class definition reads.
3. Make ledger closure terminal under copied tasks and threads without regressing live child
   delegation while the scope is active.
4. Remove the dead generated-class slot and reconcile the glossary/build records through their
   proper ownership workflows.
5. Add the missing package and live proofs, demonstrate that each fails when its production
   boundary is removed, and delete any weaker stand-in that duplicates a promoted live claim.
6. Only then rerun every required gate on one identified tree: format, lint, structural/link checks,
   default and sharded full suites at 100% package coverage, and supported-floor verification.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[goal]: ../GOAL.md
[start]: ../START.md

<!-- docs/ -->
[glossary]: GLOSSARY.md
[spec-050]: spec-050-list_field_arguments-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[bld-final]: builder/bld-final.md
[build-050]: builder/build-050-list_field_arguments-0_0_15.md

<!-- django_strawberry_framework/ -->
[connection]: ../django_strawberry_framework/connection.py
[finalizer]: ../django_strawberry_framework/types/finalizer.py
[keyset]: ../django_strawberry_framework/keyset.py
[list-field]: ../django_strawberry_framework/list_field.py
[nested-planner]: ../django_strawberry_framework/optimizer/nested_planner.py
[orders-sets]: ../django_strawberry_framework/orders/sets.py
[querysets]: ../django_strawberry_framework/utils/querysets.py
[registry]: ../django_strawberry_framework/registry.py
[type-base]: ../django_strawberry_framework/types/base.py
[walker]: ../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-connection]: ../tests/test_connection.py
[test-list-field]: ../tests/test_list_field.py
[test-orders-sets]: ../tests/orders/test_sets.py

<!-- examples/ -->
[live-async]: ../examples/fakeshop/test_query/test_list_field_async_api.py
[live-readme]: ../examples/fakeshop/test_query/README.md
[live-sync]: ../examples/fakeshop/test_query/test_list_field_api.py

<!-- scripts/ -->
[check-commas]: ../scripts/check_trailing_commas.py

<!-- .venv/ -->
[upstream-graphene-fields]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/fields.py
[upstream-graphene-types]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/types.py

<!-- External -->
[cookbook-schema]: ../../django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py
[upstream-strawberry-field]: ../../strawberry-django-main/strawberry_django/fields/field.py
