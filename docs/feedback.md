# Review: spec-050 implementation (`89ee8ac5`)

Scope reviewed: every package file in the commit (`list_field.py`, `_strawberry_patches.py`,
`orders/sets.py`, `resource_policy.py`, `utils/querysets.py`, `optimizer/extension.py`,
`__init__.py`), the ten changed test modules, the spec/rationale/glossary/README/board edits, and
the builder artifacts. Read against `docs/spec-050-list_field_arguments-0_0_15.md` and `AGENTS.md`.

Verdict: **the code is close and the contract is implemented; not Done-ready until B1 and B2 are
resolved.** The pipeline order, the four-field argument record, the seal extensions, the adapter,
the optimizer unwrap/rewrap, the error vocabulary and the live matrix all match the spec. What
does not match is the spec itself: the build shipped an executor monkeypatch the spec never
decided, and the spec/board state still reads "in flight" while the card DoD is fully ticked.

What I ran (worktree clean apart from this file, so these measure HEAD): `ruff format --check`
and `ruff check` clean; `check_trailing_commas.py --check` on every changed `.py`/`.md` clean;
`check_citations.py --check` 970 resolve; every generator `--check` up to date; kanban anchors OK;
`check_spec_glossary.py --spec` 43 terms OK; zero `TODO(spec-050` outside `docs/builder/`; zero
new `pragma: no cover`; zero `path:NN` introduced; zero `feedback` in `.py`/board/DB. Pytest was
not run (AGENTS.md 15).

## Blocking

### B1. The graphql-core executor patch is load-bearing and the spec does not know it exists

`_strawberry_patches.py::_patched_complete_list_value` monkeypatches
`graphql.execution.execute.ExecutionContext.complete_list_value`. I reproduced the defect it
fixes outside Django: on graphql-core 3.2.8 a resolver returning an `AsyncIterable` whose
children have awaitable resolvers yields `data["items"] == <coroutine get_completed_results>`
plus "never awaited" warnings; with `apply()` the rows come back. So the patch is a correct
root-cause fix (AGENTS.md 5), and the adapter design cannot ship without it.

The problems are all about where that fact lives:

- Spec Decision 5 says the adapter rides graphql-core's `AsyncIterable` branch as shipped. It
  does not. `bld-final.md` records the patch as a gate re-loop remediation of a failing
  connection test; the spec, the rationale and the adapter's glossary entry were not amended.
  This card's own rule (Decision 9: "a spec may not silently redefine ... while the board still
  demands the opposite") applies to itself.
- The patch rides the `strawberry` kill-switch key. A consumer who disables the Strawberry
  view hardening now silently loses async list completion for every `DjangoListField` with
  awaitable children. The module docstring admits this; the glossary kill-switch entry mentions
  it; nothing else does, and it is a semantic change to a shipped setting.
- `apps.py::DjangoStrawberryFrameworkConfig.ready` ("Three patch modules, one per third-party
  dependency"), `_cross_web_patches.py`'s docstring, and the glossary "Upstream patches" entry
  still state one module per dependency. graphql-core is now patched from the Strawberry module.
- Retirement is a comment, not a probe. `tests/test_strawberry_patches.py::
  test_patched_complete_list_value_awaits_async_iterable_with_awaitable_children` passes whether
  or not upstream is fixed, so the day graphql-core awaits the recursion nothing tells you to
  retire the wrapper.

Required: a spec decision (new Decision, or a 5a) recording the defect, the reproduction, the
gate-key ruling, and the retirement condition; a rationale entry; the glossary adapter entry
naming the dependency. Recommend a `_graphql_core_patches.py` with its own `graphql_core` gate key
in `conf.py` (AGENTS.md 20 is satisfied: the feature that needs the key is landing) so the
one-module-per-dependency architecture and the per-dependency kill switch stay true; if you rule
the other way, the three docstrings above must say graphql-core is patched under `strawberry` and
why. Add a sentinel test that calls the captured `_original_complete_list_value` on the bug shape
and asserts it still misbehaves, so an upstream fix fails the suite and forces retirement. The
floor run resolved graphql-core 3.2.12 against a lock of 3.2.8; run the sentinel on both.

### B2. Spec and board state contradict the checked DoD

- Spec `Status: in flight (0.0.15)`; the shipped-spec convention (`spec-036`, `spec-047`) is a
  `Status: SHIPPED ...` line as the completion source of truth, checklist left unticked. The card
  DoD in the KANBAN DB is all `[x]` and `bld-final.md` is `final-accepted`, yet the board still
  renders `WIP-ALPHA-050-0.0.15`. If Done-on-merge is the intent, fine, but the spec Status line
  must move with it.
- The ticked DoD row "Full suite green under `fail_under = 100`" has no evidence anywhere in the
  cycle: `bld-final.md` ran `uv run pytest --no-cov` (per BUILD.md) and states "no line coverage
  was inspected or asserted". The floor run was also `--no-cov`. Either run the coverage gate and
  record it, or untick the row until CI reports it.

## High

### H1. `OrderSet._input_has_active_terms` communicates with `apply_*` through an ambient, never-cleared `ContextVar`

`orders/sets.py::_APPLIED_ORDER_NORMALIZATION` is `.set()` in `OrderSet._apply_orderings` on
every order application (connection fields included, which never read it) and is never reset.
Under WSGI the worker thread's context retains the last request's `input_value` and normalized
data for the life of the thread, and the reuse rule (`applied_cls is cls and (applied_input is
input_value or applied_input == input_value)`) lets a later request be checked against an earlier
request's record. `tests/orders/test_sets.py::test_input_has_active_terms_sequence_controls_sync`
pins the stale record as the mechanism (its third call is only "a second helper call" because the
record survived). The `==` also dispatches consumer `__eq__` on the input, guarded by a broad
`except Exception`, which is exactly the dispatch `_to_inert_order_data` was written to avoid.

The spec asks for the purity check, not for global state. Root-cause fix: scope the record to the
request. `apply_sync` / `apply_async` have `info`; stash `(cls, id(input_value), data)` in
`info.context` the way `stash_resource_policy` already does, have `_input_has_active_terms`
consume and clear it, and delete the `ContextVar`. Add a test that two sequential requests on one
thread do not see each other's record. Fix the docstring's "2-call maximum per request" (a miss is
three calls).

### H2. Routing-intent check re-reads candidate state outside the seal (Decision 5 deviation)

`utils/querysets.py::_validate_post_orderset_result` calls `_seal_or_defect(candidate, model,
None, _ORDERSET_RESULT_POLICY)` with `require_shared_alias=False`, so the alias argument is
inert, then performs a second `object.__getattribute__(post_order_candidate, "__dict__")` to
compare `_db` / `_hints`. The spec required "one added comparison at an already-proven-shape site
rather than a new state read", and the package's own doctrine
(`list_field.py::_validate_djangotype_target` docstring) is that a stateful object can answer the
first guarded read and detonate the second. The seal accepts `QuerySet` subclasses, and a subclass
can install `__dict__` as a class-level descriptor. Move the routing comparison inside
`_seal_or_defect` (extend `_SealPolicy` or generalize the alias parameter to a required
`(_db, _hints)` pair), emit it as a `routing` defect through `_defect_message` with arms at both
message sites, and add a `__dict__`-descriptor row beside
`tests/utils/test_querysets.py::test_validate_post_orderset_result_zero_consumer_dispatch_on_getattribute`.
`_routing_hints_equal` and `_safe_routing_repr` are fine and can move with it.

### H3. `tests/test_list_field.py::test_list_field_post_apply_seal_benchmark` cannot fail

It runs 220 full seals and asserts `iterations == 200` and `avg_micros > 0`. It is neither a test
(no falsifiable claim) nor a benchmark (records nothing; the 22.07 us figure exists only in
`bld-slice-3` prose). The spec's requirement is the recorded number, not a test. Either assert a
generous budget and pin the baseline in the rationale, or delete the test and keep the measurement
in the rationale.

### H4. Duplicate package tests survived the integration DRY pass

Same assertions, two homes:

- `test_normalize_list_arguments_all_boundaries` versus the nine
  `test_normalize_list_arguments_boundary_N_*` rows.
- `test_list_argument_error_pickle_roundtrip` versus `test_list_field_error_pickle_round_trip`.
- `test_synthesized_list_signature_without_and_with_orderset` versus
  `test_list_field_signature_without_orderset` / `_with_orderset`.
- `test_resolve_argument_wire_name_fallback_and_custom` versus
  `test_list_field_direct_call_schema_name_fallback_and_definition_lookup`.
- `tests/test_list_field.py::test_subpackage_isolation_orders_not_imported_at_package_root`
  versus `tests/base/test_init.py::test_orders_submodule_not_imported_at_package_root`: the same
  subprocess spawn twice. Keep the `test_init.py` one (it owns the lazy-export contract).

Keep the parametrized or more precise member of each pair, delete the other. `bld-integration.md`
reports zero DRY findings; it did not look at the test tree.

## Medium

### M1. The sharded live rows never ran in the gate

`examples/fakeshop/test_query/test_multi_db.py::test_post_orderset_routing_mismatch_rejected_on_sharded_db`
and `::test_post_orderset_hints_routing_mismatch_rejected_on_sharded_db` are behind the
module-level `FAKESHOP_SHARDED` skip. `bld-final.md` ran the default invocation (40 skipped) and
records no `FAKESHOP_SHARDED=1 uv run pytest` run. The hint half of the routing invariant is the
part the spec says explicit-alias cases cannot cover. Run it and record it.

### M2. No-argument requests pay for the ceiling before the fast path

`list_field.py::_normalize_list_arguments` calls `policy_from_info` and `effective_bound` on
every request, including the omitted/all-null case, and `bounded_rows` then recomputes the same
value through `_raw_list_bound`. Decision 9 asks for an explicit fast path. Return early when
nothing was supplied (the ceiling only matters once a `limit` exists). `_ListArguments.
effective_ceiling` is write-only after construction (the pipeline never reads it); either use it
in place of the recomputation or drop it from the record.

### M3. `None` source with arguments skips the deadline check that omission performs

Both `_wrap` bodies do `if source is None: return None` before `bounded_rows(_async)`, while the
no-argument path passes `None` through `bounded_rows`, whose first act is `_raw_list_bound` and
therefore `check_deadline`. Decision 3: "an argument-bearing request gets the same clock behavior
as a bare one"; the exemption is for rejections only. `bounded_rows(None, ...)` already returns
`None`; delete the early returns.

### M4. `resource_policy.py::_close_async_iterator` labels every cleanup failure as `bounded_rows_async`

It is now also the cleanup for `list_field.py::_cleanup_rejected_async_iterable`, so a
rejection-path `aclose` failure is attached to the `ListArgumentError` as a `bounded_rows_async`
note. Take the caller label as a parameter.

### M5. `ListArgumentError` accepts an open reason vocabulary and one hard-coded wire name

The `else` arm of `ListArgumentError.__init__` builds a message from any `reason` string, and
`tests/test_list_field.py::test_list_argument_error_properties_extensions_and_repr` pins that
fail-open (`"custom_reason"`). The spec defines exactly five reasons and a stable extensions
payload; reject unknown reasons at construction and pin the rejection. The `order_required` arm
with `order_argument=None` emits a literal `'orderBy'`, contradicting "runtime error payloads
always report the active schema spelling"; every package call site passes `""` or a resolved name,
so drop the `None` arm or make callers resolve.

### M6. Fail-open `getattr` defaults in `list_field.py`

`getattr(info, "field_name", None) or "DjangoListField"` appears five times;
`_resolve_argument_wire_name` reads `get_argument_definition` and `schema` with defaults;
`_orderset_class_for_target` uses `getattr(definition, "orderset_class", None)` while
`_synthesized_list_signature` reads `definition.orderset_class` directly. START.md names the
`getattr(..., default)` shape as one statement coverage cannot see. A real `Info` always has
`field_name`; the defaults exist for `SimpleNamespace` doubles. One `_field_label(info)` helper and
one spelling of the `orderset_class` read.

## Low

- Three inlined copies of the omitted-argument fast path (`_default`, sync `_wrap`, async
  `_wrap`) plus a fourth inside `_execute_queryset_pipeline_async`; the sync pipeline has none.
  Give both pipelines the fast path and call them unconditionally.
- All three wrappers accept and silently discard unknown `**kwargs`; `_default` binds `_root`
  unused; `_handle_non_queryset_rejections_sync` takes an unused `_source`.
- `list_field.py` module docstring still cites only spec-020 / `0.0.7`; add spec-050.
- `list_field.py` imports four underscore-private names (`_LIST_ARGUMENT_VISIBILITY_POLICY`,
  `_dispose_sync_awaitable`, `_validate_post_orderset_result`, `_close_async_iterator`). The
  package already does this elsewhere, so not new, but the spec's "must not import the private
  seal" holds only because the policy constant rather than `_seal_or_defect` crossed the module.
- `_seal_or_defect(..., None, _ORDERSET_RESULT_POLICY)`: the positional `None` is dead under
  `require_shared_alias=False`. Resolves with H2.
- `docs/builder/bld-003-final.md` (spec-003's committed record) is deleted in this commit under
  the message's "board state" bullet. BUILD.md's pre-flight permits it; the message does not say it.

## AGENTS.md compliance

| Rule | Finding |
|---|---|
| 3 Meta-first | `orderBy` derives from `Meta.orderset_class`; no decorator on consumer classes. OK |
| 4 no feedback mention | none in `.py`, board, glossary, tree, spec, or DB; `docs/feedback.md` staged but unnamed. OK |
| 5 root-cause fix | the executor patch is one, and materializing in-coroutine was correctly refused; the fix is undocumented (B1) |
| 7 test placement | package tests in `tests/`, live in `test_query/`, `tests/base/test_init.py` grew as permitted; one test duplicated across trees (H4) |
| 8/9 seeding | library rows via inline `Branch.objects.create`; `_staff_client()` mirrors the existing `test_library_api.py` precedent. OK |
| 10 live-first | every wire-reachable path I traced has a live row; the two sharded rows were never executed (M1) |
| 12/13 coverage | zero new `pragma: no cover`; the 100% gate was not measured in any artifact (B2) |
| 14 same-change tests, orphan sweep | stubs in `test_library_api.py` removed; no orphan imports found |
| 16/17 format, layout, ASCII | clean at HEAD |
| 18 ERA001 pseudo | all `TODO(spec-050` anchors swept from source, tests, standing docs |
| 20 settings keys | none added; B1 asks whether `graphql_core` now needs one |
| 21 CHANGELOG | untouched in this commit |
| 26 spec lifecycle | spec stays in `docs/`, companions present, Slice 5 fold-in done; `Status:` stale (B2) |
| 27 symbol citations | no `path:NN` introduced in code, spec, rationale or plan; `bld-*.md` carry them as permitted |
| 28 link scaffold | spec, rationale, READMEs pass `check_trailing_commas.py --check` |
| 31/32/33 version, attribution, branch | version literal untouched; message has no footer; on `main` |

## Verified as matching the spec (no action)

Decision 1 signature synthesis (empty return annotation, `order_by` conditional, `orders` import
inside the builder, lazy-export pinned). Decision 3 four-field record, `offset` before `limit`,
bool rejected, lazy wire names with the zero-call converter assertion. Decision 4 offset ceiling
`P` regardless of trust. Decision 5 order (visibility with `reject_combined`, apply, post-apply
seal with `unevaluated` before `sliced`, guard, one window), `combined`/`unevaluated` arms at both
message sites, adapter with `__aiter__` only, optimizer `finish()` on all three exits. Decision 6
both predicates, `not query.group_by` falsiness, `"?"` and `Random()` only, `.none()` handled.
Decision 8 precedence (`queryset_required` before `order_required`), `limit: 0` short-circuits
(`qs[k:k]` hits Django's `set_empty`), async rejection cleanup via `aiter` + `aclose` with zero
`__anext__`, sync `close()` declined and pinned. Decision 9 fast-path SQL parity live. Decision 10
coercion left to graphql-core, integral float pinned. Decision 12 no version, changelog, or lock
change. Card DoD Scope and `LIMIT`/`OFFSET` rows amended in the DB and rendered.
