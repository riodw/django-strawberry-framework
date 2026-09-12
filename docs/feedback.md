# Adversarial implementation re-review: spec 050

Date: 2026-09-11

## Verdict

**Not accepted yet.** The latest remediation closes the earlier routing, integer-subclass,
mutable-capture, wire-name, and live-coverage defects, but two foundational invariants are still
false in executable code:

1. the target definition is not a read-once construction value across either list or connection
   execution; and
2. the normalization-purity handoff loses the normalization that actually drove ordering when a
   valid public `apply_async` override delegates in a child task (and it has the same single-slot
   weakness under nested ordering calls).

There are also three narrower corrections: `trusted_max_rows` is truthy rather than exact-boolean,
the combined-query legacy oracle still compares parsed outcomes rather than response bytes, and the
capture-scope optimization overclaims its no-`OrderSet` direct-call path. The final build record
currently states that the first two are fixed, so the recorded gate cannot be treated as current.

This pass reviewed the full [specification][spec-050], the current production diff, package and live
tests, [AGENTS.md][agents], [GOAL.md][goal], the [live-test guide][live-readme], the Graphene-Django
and Strawberry-Django reference implementations, and the django-graphene-filters cookbook schema.
No pytest invocation was run because [AGENTS.md][agents] permits it only when explicitly requested.
The behavioral evidence below came from focused, non-pytest construction/execution probes. The
working tree also changed concurrently during this pass; no concurrent file was reverted or folded
into a finding without tracing it to the named production symbol.

## Findings

### P1-1 — the “definition exactly once” invariant is still false during construction and execution

The spec says the list field reads its target definition exactly once at construction, and that the
connection factory captures the same returned definition for its signature and pipelines. The list
factory now does capture the validator's result, but only `orderset_class` is threaded. Every default
execution immediately returns to the target attribute through
[`utils/querysets.py::initial_queryset`][querysets] ->
[`utils/querysets.py::model_for`][querysets], and both visibility seals independently call
`model_for` again.

A default `DjangoListField` probe kept a metaclass counter armed for the real schema execution. The
request succeeded, but it recorded:

```text
runtime_definition_reads 3
```

Those reads are the seed model, the visibility source model, and the visibility result model. The
new package test `tests/test_list_field.py::test_list_field_reads_the_target_definition_once_and_dispatches_through_it`
does not detect this: it disarms the counter immediately after `DjangoListField(CountedType)` and
before schema construction or query execution.

Connections are further from the stated invariant. A cold-cache construction probe recorded three
definition reads before any request:

```text
definition_reads 3
```

The call chain is the shared validator, [`connection.py::_connection_type_for`][connection], and
[`connection.py::_generate_connection_class`][connection]. Runtime then rereads through the default
`initial_queryset`, two visibility seals, and
[`connection.py::_finalize_queryset`][connection], where both `model_for(target_type)` and a direct
definition lookup for `cursor_field` remain. The synthesized-relation path already owns
`target_definition` in [`types/finalizer.py::finalize_django_types`][finalizer], but discards it when
calling `_connection_type_for` and then rereads again inside
[`connection.py::_build_relation_connection_resolver`][connection].

This is not merely a counter mismatch. A stateful metaclass can publish `orderBy`, `filter`,
`totalCount`, connection naming, or cursor behavior from one definition while a later read seeds or
seals a different model. That is the exact schema/runtime divergence threat Decision 1 says the
capture prevents.

**Root-cause correction**

- Treat the validator's returned `DjangoTypeDefinition` as the field's sole construction and
  execution dependency.
- Seed defaults with `base_queryset(definition.model)`, not `initial_queryset(target_type)`.
- Give the colored visibility runners a captured-model/definition seam so their source and result
  seals do not reread the class. Keep the generic public callers' existing type-keyed convenience,
  but the field pipelines must use the captured value.
- Thread the same definition into `_finalize_queryset`, `_connection_type_for`,
  `_generate_connection_class`, `_build_total_count_connection`, and the synthesized relation
  resolver. The finalizer must pass its already-resolved `target_definition` rather than asking the
  target again.
- Keep cache identity and connection shape derived from that captured definition; do not “fix” the
  test by narrowing the wording to sidecars while model/cursor reads continue to drift.

**Required proofs**

- Keep the metaclass counter armed through factory construction, schema construction, and a real
  request for default and consumer-resolver list fields.
- Add the same proof for a root connection and a synthesized relation connection, with cold and warm
  connection caches.
- Make the metaclass return a decoy definition after the accepted read and prove that neither the
  decoy model nor its sidecars/cursor are consulted at runtime.
- Put consumer-observable rows through live HTTP; construction-count mechanics remain package-tier.

### P1-2 — immutable `ContextVar` rebinding loses the applied normalization across child delegation

[`orders/sets.py::_CaptureState`][orders-sets] correctly fixes the previous shared-mutable-object
bug: an unrelated descendant can no longer overwrite the parent's binding. That isolation creates
the opposite failure for a legitimate public override, however. A child task's rebinding cannot
publish the normalization back into its parent context.

The focused probe used the supported public override seam:

```python
class ChildDelegatingOrder(OrderSet):
    @classmethod
    async def apply_async(cls, input_value, queryset, info):
        return await asyncio.create_task(super().apply_async(input_value, queryset, info))
```

Its `_normalize_input` produced A for the application and B/B for the two fallback checks. Inside
the list field's capture scope, the observable result was:

```text
parent_record None
outcome accepted active=True
normalizations 3
```

The ordering was built from A in the child. The parent saw an empty capture, compared B with B, and
accepted instead of raising the purity `ConfigurationError` promised by the spec's explicit A/B/B
case. This is a normal `apply_async` override delegating to `super()`, not an unsupported call to a
private helper.

The single record can also be displaced in one context: an outer `OrderSet.apply_*` may delegate to
the base, invoke another `OrderSet` before returning, and leave the nested class's record in the one
slot. `_input_has_active_terms` consumes the mismatched record and falls back to B/B, again losing
the terms that built the returned queryset. The current descendant test proves only that a child
cannot overwrite a parent record after the parent performed the application; it does not execute
the application itself in the child or nest another application between publication and check.

**Root-cause correction**

The handoff needs an explicit, invocation-scoped attestation transport. A rebinding-only
`ContextVar` cannot simultaneously isolate descendants and return a descendant's application result
to its parent. Viable designs include a synchronized append-only ledger of immutable records, with
records tied to the active invocation/input and any disagreement rejected, or an unforgeable
result-carried attestation that returns with the applied queryset. Either design must:

- retain public `apply_sync` / `apply_async` dispatch;
- never put framework state on `info.context`;
- avoid a mutable last-writer-wins slot;
- work through awaited child tasks, copied contexts, worker threads, and nested `OrderSet` calls;
- fail closed if more than one applicable normalization disagrees; and
- reset all invocation state on success and every exceptional exit.

Simply restoring the old mutable `_CaptureState.record` is not acceptable; it reopens the overwrite
race the latest patch correctly closed. Bypassing the public override with a private parallel apply
entry point also contradicts the spec and the project's root-cause rule.

**Required proofs**

- Async holder-schema HTTP test: child-task delegation to `super().apply_async`, A/B/B, exact typed
  rejection.
- Sync/package test: base application followed by a nested different `OrderSet`, then A/B/B on the
  outer class.
- Retain the existing unrelated-child, sibling-task, copied-context, thread, nested-scope,
  exception-reset, and ordinary pure A/A controls.
- Prove that a pure child-delegating override still orders and pages correctly; a rejection-only
  test would not prove the public override remains usable.

### P2-1 — `trusted_max_rows` is not the explicit boolean opt-in the spec describes

[`resource_policy.py::effective_bound`][resource-policy] uses `if trusted:` and
[`list_field.py::DjangoListField`][list-field] performs no domain validation for
`trusted_max_rows`. A focused call demonstrates the consequence:

```text
effective_bound(100, 105, trusted="false") -> 105
```

Thus a common configuration typo widens the request's row policy even though the caller did not
provide the literal `True` repeatedly named by the spec and standing docs. This truthiness behavior
predates card 050, but card 050 makes the widening directly usable through client `limit` and claims
that it is an explicit trusted opt-in. That claim cannot be certified while arbitrary truthy values
enable it.

**Root-cause correction**

- Validate `type(trusted_max_rows) is bool` at field construction and raise the package's typed
  configuration error at the declaration site.
- Harden `effective_bound` itself so only `trusted is True` can widen; the policy primitive must not
  remain unsafe for another internal caller that omits the factory validation.
- Add exact-bool tests for false/true and invalid truthy/falsy values. This is construction-time
  configuration, so package-tier placement is correct.

### P2-2 — the combined legacy oracle still does not prove response-byte parity

`examples/fakeshop/test_query/test_list_field_api.py::test_branches_omitted_and_null_arguments_match_the_legacy_reference`
now correctly mounts the same `branches` field name in two schemas and compares raw
`HttpResponse.content`. The combined-source sibling does not. In
`test_holder_branches_combined_legacy_branch_matches_the_legacy_reference`, both responses are
reduced through `_parity_outcome(response.json(), "branches")`; only parsed rows or normalized error
messages are compared.

That misses envelope ordering, locations, paths, extensions, and serialization differences. It also
contradicts the [final build record][bld-final], which says both named tests compare raw bytes, and
the Definition of Done's all-omitted/all-null byte claim.

**Correction**

- Compare `response.content` with the legacy response bytes for both omitted and all-null current
  requests, while retaining SQL, marks, and visibility-count assertions.
- If a genuinely unstable error field prevents byte equality, make that response deterministic or
  narrow the specification and build claim explicitly. Do not silently substitute a semantic
  projection for a byte-for-byte requirement.

### P3-1 — the capture-scope optimization overclaims the no-`OrderSet` path

[`list_field.py::_order_normalization_scope`][list-field] receives only `_ListArguments`. Therefore
a direct call supplying `order_by` plus positive `offset` to a target with no `OrderSet` opens and
sets the capture before `_require_orderset_class` raises. Its docstring says a target with no
`OrderSet` “must not pay for the scope,” but the helper has no information with which to implement
that condition. The wire cannot publish this argument shape, so this is a bounded direct-call and
micro-overhead issue, not a data error.

**Correction**

Pass the captured `orderset_class` into `_order_normalization_scope` and require it to be non-`None`
before opening the capture. Extend the existing scope test with the direct no-`OrderSet` shape.

### P3-2 — build status and remediation claims are stale

The [build plan][build-050] still says full-coverage and sharded verification are pending, while the
[final build record][bld-final] says default and sharded tiers were rerun green after the fourth
review and only the supported floor was not rerun. More importantly, that same final record claims
that connection/synthesized-relation definition reads and both raw-byte legacy oracles were fixed;
P1-1 and P2-2 reproduce the opposite.

Reconcile the status only after production and test corrections. Preserve the historical command
figures, but mark them as superseded by later code changes and new blocking findings. The final gate
must not be called green until the current tree passes every required tier, including the floor.

## Corrections verified in this pass

The following changes are architecturally sound and should be preserved while fixing the findings:

- **Routing intent is now connection-level.**
  [`utils/querysets.py::_snapshot_routing_intent`][querysets] resolves the effective alias before
  consumer ordering code, copies outer hints, and
  [`utils/querysets.py::_validate_post_orderset_result`][querysets] seals the accepted result onto
  that alias. Mutable nested hint state can no longer redirect the eventual read.
- **Numeric inputs use exact integer boundaries.** `offset` and `limit` reject `bool` and hostile
  `int` subclasses before comparison or formatting hooks run; guarded rendering also preserves the
  typed error for an unprintably large exact integer.
- **Wire names come from the executable schema.** The error path reads the already-published
  `GraphQLField.args` key by Strawberry argument back-reference and does not rerun a consumer name
  converter at request time.
- **Unrelated descendant writes no longer mutate a parent binding.** Frozen `_CaptureState` plus
  rebinding is the correct isolation half of the normalization problem; P1-2 requires a return
  channel, not a return to shared mutation.
- **Post-`OrderSet` results fail closed.** Evaluated, sliced, combined, projected, wrong-model,
  untrusted, and routing-divergent results use the shared sealing boundary, and accepted results are
  normalized into a framework-owned lazy queryset.
- **The async completion adapter remains in the correct layer.** Querysets stay lazy through
  optimization and complete by asynchronous iteration instead of synchronous ORM work on the event
  loop.
- **The ordinary omission oracle is now independent.** The shipped-list parity test uses a genuine
  pre-card composition under the same GraphQL field name and compares raw response bytes.
- **Documentation now states the trusted-row/offset asymmetry.** Trusted `max_rows` may widen the
  returned-row limit, while offset remains bounded by request policy; P2-1 concerns the opt-in's
  type boundary, not that asymmetry.

## Architecture and upstream cross-check

No new public-surface contradiction was found:

- The consumer API remains DRF/Graphene-shaped: `Meta.orderset_class` owns `orderBy`; no stacked
  Strawberry-Django decorators or list-specific consumer input class were introduced.
- Graphene-Django's list field forwards arbitrary arguments and substitutes a default manager when
  a resolver returns `None`. This framework deliberately consumes the synthesized arguments itself
  and preserves its existing `None` semantics. The divergence is explicit and internally coherent.
- Strawberry-Django's pagination helper uses a wrapper input and silently applies window/clamping
  behavior. This framework deliberately keeps a flat `list[T]`, typed rejection, and one resource
  bound. No accidental borrowing of its decorator-first API appears in the implementation.
- The cookbook schema exposes its ordered/filterable roots through
  `AdvancedDjangoFilterConnectionField`. The spec correctly treats that as evidence for the
  connection sidecar pipeline and does not pretend the cookbook defines a raw-list pagination API.

## AGENTS.md and live-test-guide assessment

| Rule | Verdict | Evidence |
| --- | --- | --- |
| DRF first, Strawberry second; public configuration through `Meta` | Pass | `orderBy` remains derived from `Meta.orderset_class`; no decorator-first consumer type API was added. |
| Give the root-cause fix; no test-only workaround | **Blocked** | P1-1 and P1-2 require production dataflow changes. Narrower tests or weaker prose would not repair either invariant. |
| Live-first coverage for wire-reachable behavior | Partial | Routing and malformed-result matrices are live. Child-delegated async ordering and the combined raw-byte oracle still need live HTTP proofs. |
| Correct package/live test placement | Pass for reviewed additions | Construction and private mechanics remain in `tests/`; consumer-visible list behavior is in `examples/fakeshop/test_query/`. |
| Fakeshop seed discipline | Pass | No new hand-rolled Category/Item/Property/Entry/User setup was introduced in the reviewed list-field acceptance rows. Library acceptance rows use their app-owned models as allowed. |
| Tests accompany production behavior | Partial | The changed production seams have tests, but the current tests do not exercise the two reproduced failure shapes. |
| No `pragma: no cover` as remediation | Pass | No new coverage suppression was used for card behavior. |
| No pytest unless explicitly requested | Pass for this review | No pytest command was run. Recorded historical runs are not represented here as validation of the current tree. |
| No release/version or changelog work before card 053 | Pass | The package version and changelog remain outside this card's implementation scope. |
| Preserve concurrent work | Pass for this review | Concurrent dirty and newly changing files were not reverted, stashed, or overwritten. |
| Standing-doc source references use symbol paths | Pass in this review | No raw source line-number references are used; file links follow the repository scaffold. |

## Required correction order and gate

1. Make the captured `DjangoTypeDefinition` the sole field-construction and execution dependency
   across list, connection, and synthesized-relation paths.
2. Replace the single-slot ambient normalization handoff with an invocation-scoped attestation that
   survives valid child/nested delegation without permitting last-writer overwrite.
3. Enforce an exact boolean trusted-row opt-in.
4. Strengthen the combined legacy oracle to raw bytes and correct the capture-scope predicate.
5. Reconcile the build artifacts with what is actually implemented.
6. Then run formatting, lint, structural/link checks, the default and sharded full suites with 100%
   package coverage, and the supported-floor verification. Any production change after a recorded
   green run invalidates that run for final acceptance.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md

<!-- docs/ -->
[docs-readme]: README.md
[glossary]: GLOSSARY.md
[spec-050]: spec-050-list_field_arguments-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[bld-final]: builder/bld-final.md
[build-050]: builder/build-050-list_field_arguments-0_0_15.md

<!-- django_strawberry_framework/ -->
[connection]: ../django_strawberry_framework/connection.py
[finalizer]: ../django_strawberry_framework/types/finalizer.py
[list-field]: ../django_strawberry_framework/list_field.py
[orders-sets]: ../django_strawberry_framework/orders/sets.py
[querysets]: ../django_strawberry_framework/utils/querysets.py
[resource-policy]: ../django_strawberry_framework/resource_policy.py

<!-- tests/ -->
[test-connection]: ../tests/test_connection.py
[test-list-field]: ../tests/test_list_field.py
[test-orders-sets]: ../tests/orders/test_sets.py
[test-querysets]: ../tests/utils/test_querysets.py

<!-- examples/ -->
[live-async]: ../examples/fakeshop/test_query/test_list_field_async_api.py
[live-multi-db]: ../examples/fakeshop/test_query/test_multi_db.py
[live-readme]: ../examples/fakeshop/test_query/README.md
[live-sync]: ../examples/fakeshop/test_query/test_list_field_api.py

<!-- scripts/ -->
[check-commas]: ../scripts/check_trailing_commas.py

<!-- .venv/ -->
[strawberry-schema-converter]: ../.venv/lib/python3.14/site-packages/strawberry/schema/schema_converter.py

<!-- External -->
[cookbook-schema]: ../../django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py
[upstream-graphene-fields]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/fields.py
[upstream-strawberry-pagination]: ../../strawberry-django-main/strawberry_django/pagination.py
