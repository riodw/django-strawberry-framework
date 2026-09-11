# Review 2: spec-050 implementation at `4c483b6b` (adversarial, upstream-referenced)

Scope: `django_strawberry_framework/list_field.py`, `orders/sets.py`, `utils/querysets.py`
(seal, post-OrderSet validator, async adapter), `resource_policy.py` (bounding helpers),
`optimizer/extension.py` (adapter unwrap/rewrap), `_graphql_core_patches.py`, the spec and
rationale, the three test tiers, and the two upstream checkouts named in AGENTS.md L2. Every
behavioral claim below was either executed (probe scripts in the session scratchpad, the seven
recorded failing tests re-run individually) or is cited to a symbol.

**Verdict: not Done-ready.** The contract is implemented and the pipeline order, ceilings,
error payloads, and async completion behave as specified under live execution. The suite is
red (seven failures, six of them wrong assertions and one a package defect), the sharded and
coverage gates have not run, one runtime mechanism leaks state on the common path (H1), the
purity check is identity-dependent (H2), and the spec disagrees with the code in two places
(H3). One row of the gate record I wrote in the previous round misattributes a failure and
must be corrected (B1, row 7).

## Blocking

### B1. Seven failing tests; causes re-derived by running each one

| Test | Actual failure | Class |
| --- | --- | --- |
| `tests/orders/test_sets.py::test_input_has_active_terms_hostile_eq_and_repr` | `_to_inert_order_data` renders a non-`str` path through `_safe_arg_repr`; the default `object.__repr__` embeds the address, so two normalizations of equal-shaped terms compare unequal and a false "not pure" `ConfigurationError` fires. Reproduced standalone: `('<__main__.T object at 0x...>', None)` differs across two calls. | **Package defect** (see H2) |
| `tests/utils/test_querysets.py::test_validate_post_orderset_result_routing_hints_none_vs_empty` | Expects `db='default'`; an unrouted `Category.objects.all()` carries `_db is None` and the message correctly reads `db=None`. | Test expectation |
| `tests/test_list_field.py::test_list_field_direct_call_schema_name_fallback_and_definition_lookup` | The stub `ArgDef` has no `graphql_name`; Strawberry's `NameConverter.from_argument` reads it, raises `AttributeError`, and `_resolve_argument_wire_name` wraps that in `ConfigurationError`, so the `pytest.raises(ListArgumentError)` never sees its error. | Test stub incomplete |
| `tests/test_list_field.py::test_list_field_post_orderset_validator_arms` | Asserts `got evaluated defect`; the seal emits the spec-named code `unevaluated` (see M1 for the naming question). | Test expectation |
| `tests/test_list_field.py::test_list_field_constructor_validation_precedence` | Asserts `got -1.` and `target_type must be a DjangoType subclass, got <class 'object'>`; actual wording is `; got int -1.` (`describe_value`) and `requires a DjangoType subclass; got object.` Both are pre-existing message shapes. | Test expectation |
| `tests/test_list_field.py::test_list_arguments_immutability_and_slots` | First two assertions pass (`FrozenInstanceError` for `offset`/`limit`). The third, assigning an unknown attribute, raises `TypeError: super(type, obj): obj ... is not an instance or subtype of type` from the dataclass-generated `__setattr__`: with `slots=True` the frozen check's captured class is the pre-slots class, so `type(self) is cls` is false and the fallthrough `super(cls, self)` fails. Immutability holds; only the exception type differs. Seven other `frozen=True, slots=True` records in the package share the quirk. | Test expectation (or drop `slots=True`) |
| `examples/fakeshop/test_query/test_list_field_api.py::test_holder_materialized_and_nullable_none_fields` | Asserts `"on branches_materialized" in message`; `_field_label` returns `info.field_name`, the GraphQL wire spelling `branchesMaterialized`. Every `reason` assertion in that test passes. | Test expectation |

**Correction to the gate record.** `docs/builder/bld-final.md`'s failure table attributes the
last row to "the live expectation disagrees with Decision 8". That is wrong: the test's
`queryset_required` and `order_required` expectations all pass; it fails only on the
python-name-vs-wire-name assertion. I wrote that row in the previous round from the summary
line rather than the assertion, and it must be replaced with the cause above. Wire spelling is
the right behavior: `argument` is already documented as the active wire spelling, and the
field label must use the same vocabulary.

Recommended fixes, per rule 5 (root cause, never test-only when the code is wrong):
`_to_inert_order_data` is a code fix (H2); the other six are assertion corrections, with the
`slots=True` row a maintainer choice between widening the expected exception tuple and
dropping `slots=True` from `_ListArguments` (a five-field record gains nothing from slots and
loses `FrozenInstanceError` on unknown names).

### B2. The card's final gate has not been run (carried from round 1)

`docs/builder/build-050-list_field_arguments-0_0_15.md #"Final test-run gate"` is unticked and
the sharded rows (`examples/fakeshop/test_query/test_multi_db.py::test_post_orderset_routing_mismatch_rejected_on_sharded_db`
and its hints sibling) have not been executed under `FAKESHOP_SHARDED=1`. The spec DoD rows for
`fail_under = 100` and the CI-matrix run remain open. Nothing below changes that; B1 must land
first.

## High

### H1. The order-normalization record leaks on the common path and is keyed by a reusable `id()`

`orders/sets.py::_record_applied_normalization` stashes `(cls, id(input_value), data)` on
`info.context`, and `orders/sets.py::OrderSet._input_has_active_terms` is the only consumer.
That consumer runs only from `list_field.py::_check_nonzero_offset_guard`, which returns before
calling it whenever `offset` is `None` or `0`. So every `orderBy`-bearing request without a
positive offset, the ordinary case, leaves the record on the request context. Reproduced: after
`_execute_queryset_pipeline_sync` with `offset=None, order_by=[...]`, `get_context_value(ctx,
_APPLIED_ORDER_NORMALIZATION_KEY)` returns the tuple; after `offset=1` it is `None`. The record
also survives when `_validate_post_orderset_result` rejects the candidate, because the stash
happens inside `_apply_orderings` before the seal runs.

Consequences:

- The docstring's "request-scoped and consumed before checking" is false on the dominant path.
- The key is `id(input_value)` with no strong reference to the input. Within one request (or
  any consumer-supplied long-lived context object; `schema.execute(..., context_value=ctx)` in
  tests and scripts is common), a later alias whose input object reuses the freed id and whose
  OrderSet is the same class compares its fresh normalization against the stale record and
  raises a false "not pure" `ConfigurationError`. Low probability, but it is exactly the
  self-inflicted failure class the purity check exists to catch in consumers.
- Under async execution, two aliases on one context can interleave between stash and consume
  only if a consumer `apply_async` override awaits after delegating; the fallback is the
  two-call path, so this is a perf loss rather than a correctness loss. Worth stating in the
  docstring since the "two calls total" contract in `test_input_has_active_terms_independent_query_and_double_normalization`
  does not hold there.

Root-cause options, in order of preference:

1. Remove the context record. Have `_input_has_active_terms(cls, input_value)` normalize once
   and walk; enforce the `_normalize_input` return contract instead of policing purity (see
   H2). The double-normalization purity check guards an override of an underscore-private
   method; the same guard can be a type check on the returned terms, which needs no request
   state, no identity, and no cleanup. This changes Decision 3's "answered only after public
   apply succeeds" sentence and the call-count tests, so it is a maintainer ruling.
2. If the record stays: store `input_value` itself (strong reference, compare with `is`), and
   have the argument pipeline clear the key in a `finally` around `_apply_orderset_*` plus the
   guard so no path leaves it behind. `utils/context.py::restored_context_keys` already exists
   for exactly this round trip.

### H2. The purity comparison depends on object identity and formats consumer objects

`orders/sets.py::_to_inert_order_data` claims to shield the comparison from hostile `__eq__` /
`__repr__`, but for any non-`str` path or non-`Ordering` direction it falls back to
`_safe_arg_repr`, and the default `object.__repr__` includes the id. Two independent
normalizations therefore never compare equal, which is the B1 row-1 failure. Two more holes in
the same vicinity:

- `orders/sets.py::OrderSet.get_flat_orders` builds `f"{prefix}{field_path}"`, so a consumer
  path object with a raising `__format__` / `__str__` escapes as a raw exception from the
  pipeline (the hostile test never reaches it only because the purity check fires first).
- `_resolve_order_expressions` already rejects a non-`Ordering` direction with a typed error;
  a non-`str` path has no equivalent gate and reaches `classify_path`.

Root cause: `_normalize_input` has a declared return type, `list[tuple[str, Ordering | None]]`,
and nothing enforces it. Enforce it once at the boundary (`_apply_orderings` and
`_input_has_active_terms`): a term that is not a 2-tuple of `str` and `Ordering | None` raises
`ConfigurationError` naming `_normalize_input`. With the terms proven primitive, the comparison
is a plain tuple equality and `_to_inert_order_data` can be deleted. The hostile-`__eq__` test
then expects the typed rejection rather than `True`, which is the honest contract: a
`_normalize_input` returning arbitrary objects is a defect, not an input to be laundered.

### H3. Spec text disagrees with the shipped code in two places

- `docs/spec-050-list_field_arguments-0_0_15.md #"holds `offset`, `limit`,"` and the "window
  fields" sentence in Decision 3 both say the record carries `effective_ceiling`. The field was
  removed from `_ListArguments` in the review response (correctly; it was dead state). The
  spec is the contract and must describe the five-field record that ships.
- Decision 5 step 1, `#"Derive the active wire names and validate/normalize"`, says wire names
  are derived up front; Decision 3 and the code resolve them lazily on the error path only, and
  a test pins zero converter calls on success. Reword step 1 to "validate/normalize `offset` /
  `limit` from `info`" so the two decisions agree.

START.md "Five homes per contract": two disagreeing homes is a defect regardless of which one
is right.

## Medium

### M1. The `unevaluated` defect code names the requirement, not the state

Every sibling code names the defective state: `sliced`, `combined`, `projection`, `untrusted`,
`routing`. `unevaluated` names the requirement that was violated, so the rendered message reads
"got unevaluated defect (the result cache is populated)", which contradicts itself to a schema
author, and the slice-3 test author expected `evaluated`. The spec chose the spelling, so this
is a ruling: rename to `evaluated` in the seal, both visibility arms, `_validate_post_orderset_result`,
the spec's canonical-order sentence, and the tests, or keep it and fix the test. Renaming is the
consistent choice and touches no consumer surface (the code never reaches a wire payload).

### M2. Three identical argument-normalization blocks and a duplicated async tail in `list_field.py`

`_default`, the async `_wrap`, and the sync `_wrap` each spell the same 8-line
`_normalize_list_arguments(field_name, info, max_rows, trusted_max_rows, offset=, limit=,
order_by=)` call after the same `_resolver_root_and_info` / `_field_label` pair. The async
`_wrap`'s non-queryset tail is byte-for-byte the body of `_resolve_async_iterable`, which the
sync `_wrap` already calls. `_apply_orderset_sync` and `_apply_orderset_async` duplicate the
"has no orderset_class configured" rejection. `_handle_non_queryset_rejections_sync` is a
one-line wrapper around `_build_non_queryset_rejection_error`. One `_argument_record(info,
args, kwargs, ...)` helper and reusing `_resolve_async_iterable` removes roughly 40 lines
without changing a branch.

### M3. Migration divergences from both upstreams need to be stated where consumers will read them

Verified against the checkouts:

- `graphene_django/fields.py::DjangoListField.list_resolver` forwards `**args` into the
  consumer resolver and substitutes `default_manager` when the resolver returns `None`. This
  package forwards nothing (Decision 1) and keeps `None` as `None`, then rejects `orderBy` /
  positive `offset` over it (Decision 8). A graphene migrant with `resolve_x(self, info,
  **kwargs)` returning `None` gets a different response under every argument.
- `strawberry_django/fields/field.py::StrawberryDjangoField.get_result` strips only the
  pagination/order/filter kwargs the consumer resolver does not accept
  (`_need_remove_argument`); a resolver that declares `pagination` receives it. Here it never
  does.
- `strawberry_django/pagination.py::StrawberryDjangoPagination.get_queryset` injects
  `order_by("pk")` whenever `not queryset.ordered`; `_resolve_limit` treats a negative limit as
  unbounded unless `PAGINATION_MAX_LIMIT` silently clamps it. Both are refused here.

The rationale's Borrowing section records the refusals; the consumer-facing migration note the
card owes (Decision 11) must carry the `None`-fallback and argument-forwarding differences
explicitly, since they change response data, not just SDL.

### M4. `_normalize_list_arguments` accepts any `order_by` value

`object()` passes the normalizer with `order_by_supplied=True` (probe). GraphQL coercion makes
this unreachable through a schema, so it is a direct-call gap only, but the failure then
surfaces from `orders/inputs.py::normalize_input_value` / `iter_active_fields` with whatever
those raise for a non-list, non-dataclass value rather than from the argument owner. Either
reject a non-`list`/`tuple` order input with `ListArgumentError(reason="non_integer")`'s
sibling wording, or state in the normalizer docstring that `order_by` shape is delegated to
`OrderSet` and is a schema-coercion guarantee.

## Low

- L1. `bounded_rows` with `offset`/`requested_limit` extends two pre-existing shapes without
  comment: a `str`/`bytes` source returns a `str` slice (`bounded_rows("abc", offset=1,
  requested_limit=1)` is `"b"`), and a mapping pages over its keys. Neither is new, but the
  docstring now says "skipped and returned items" as if every source were a row sequence.
- L2. `list_field.py::ListArgumentError.__init__` validates `reason` against an inline set
  literal; `_DEFAULT_WIRE_NAMES` is a module constant. Hoist the reason set beside it so a
  future reason lands in one place.
- L3. `_strawberry_patches.py #"There used to be a third entry"`: standing docstring narrating
  module history ("used to be"), the provenance form START.md bans. Pre-existing, not
  introduced by this card; flag only because the paragraph was edited in this round.
- L4. Glossary anchors for the adapter, `ListArgumentError`, and the offset precondition read
  `planned for 0.0.15` while the code ships. That is the joint-cut convention (card 053 flips
  them); confirm 053's checklist names these three anchors so they do not stay "planned"
  after the cut.
- L5. `_check_nonzero_offset_guard`'s explicit branch uses `queryset.ordered`, which is
  vacuously `True` for an `EmptyQuerySet`. The spec accepts this deliberately; noting that
  `strawberry_django` relies on the same property and therefore has the same quirk.

## Upstream comparison (what was checked, what holds)

| Concern | graphene-django | strawberry-graphql-django | This package | Reading |
| --- | --- | --- | --- | --- |
| Argument shape | flat `offset: Int` on every connection | `pagination: OffsetPaginationInput {offset, limit}` | flat `offset` / `limit` on the list field only | Matches card; connections untouched |
| Omitted limit | none on `DjangoListField`; `max_limit` on connections | `PAGINATION_DEFAULT_LIMIT`, `None` = unbounded | policy `max_list_rows` always | Stronger; spec Decision 4 |
| Negative / over-max limit | assert-based rejection on connections | negative = unbounded; `PAGINATION_MAX_LIMIT` silently clamps | typed `ListArgumentError` both directions | Matches spec; no clamp |
| Unordered offset | accepted on connections | injects `order_by("pk")` when `not qs.ordered` | `order_required` unless `orderBy` active or model default still effective | Matches Decision 6 |
| Consumer resolver args | forwards `**args` | strips only what the resolver cannot accept | never forwards | Matches Decision 1; migration note owed (M3) |
| `None` from resolver | falls back to default manager | n/a | stays `None`; arguments still validated | Matches Decision 8; migration note owed (M3) |
| Async completion | n/a | `sync_to_async` + materialize in resolver (`default_qs_hook`) | lazy queryset through `_AsyncQuerySetRows`; optimizer unwraps/rewraps | Matches Decision 5; three exits pinned in `tests/optimizer/test_extension.py` |
| Nested offset paging | n/a | window functions (`apply_window_pagination`) | connections only | Non-goal held |
| Order term sequence | n/a | re-reads `info._raw_info.field_nodes` to recover input order | list-of-inputs, order explicit | Cleaner than upstream |

## AGENTS.md compliance

| Rule | Status | Evidence |
| --- | --- | --- |
| 3 Meta-first surface | Pass | `Meta.orderset_class` drives `orderBy`; no consumer decorator introduced |
| 5 Root-cause fixes, no test-only fixes | **Open** | B1 row 1 needs a code fix (H2); rows 2-7 are assertion corrections and must not be "fixed" by loosening the production messages |
| 7 Test placement | Pass | new `tests/test_graphql_core_patches.py` is a package test; `tests/base/` untouched beyond `test_conf.py` |
| 10 Live-first | Pass | argument matrix, ordering, visibility, async completion live in `test_query/`; package tier holds helper mechanics and unconstructable states |
| 12 `fail_under = 100` | **Open** | not measured this cycle (B2) |
| 14 Tests in same change | Pass | every new arm in `list_field.py` / `querysets.py` has a pinning test in the same commits |
| 15 No pytest after edits | Pass (review run) | seven targeted tests re-run to attribute failures; no edits made |
| 17 Line length / ASCII | Pass | `ruff` and `source-layout` passed at commit |
| 20 No pre-emptive settings | Pass | offset ceiling derives from `max_list_rows`; `graphql_core` key lands with its patch |
| 21 No CHANGELOG | Pass | untouched |
| 26 Staged-slice anchors | Pass | no `TODO(spec-050 ...)` remains in the reviewed package files |
| 27 Symbol-path citations | Pass | code comments and this file cite `path::Symbol` / `path #"substring"` |
| 28 Reference-style links | Pass | scaffold present below |
| 32 / 33 Commit and branch discipline | Pass | `4c483b6b` on `main`, no footer, no branch |
| 34 Concurrent files | Pass | spec-039 files left dirty and unstaged |

## Verified as matching the spec (no action)

- Pipeline order and SQL: `orderBy + offset: 1` with no limit emits one `ORDER BY ... LIMIT
  100 OFFSET 1` after the visibility `WHERE`; the manager-resolver field emits the same shape
  with `LIMIT 1 OFFSET 1` (probe).
- `orderBy: []` and `orderBy: [{ name: null }]` with `offset: 1` on `Branch` (no
  `Meta.ordering`) both return `order_required` (probe).
- Anonymous `orderBy: [{ city: ASC }], offset: 1` succeeds; the `name` gate is not touched.
- `offset: 2147483647` returns `over_ceiling` with `ceiling: 100`; introspection shows all
  three arguments with `defaultValue: null` (probe).
- `limit: 0` with an active order performs zero row queries (live test).
- `bounded_rows` arithmetic: list beyond length yields `[]`; iterator honours `islice(start,
  stop)`; zero window never constructs `islice` (probe, tests).
- The routing check lives inside `_seal_or_defect`, renders `db=None` correctly, and has arms
  at all three message sites; the sharded live rows exist and assert `expected db='shard_b'`.
- `_graphql_core_patches.py` is gated by its own key, validates upstream shape, and
  `test_captured_upstream_still_returns_a_residual_awaitable` fails the suite when upstream
  fixes the bug.
- `DjangoOptimizerExtension._optimize` rewraps on all three exits.
- `apps.py` applies four modules; `UPSTREAM_PATCH_DEPENDENCIES` carries `graphql_core`.

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
