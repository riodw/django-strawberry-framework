# DRY review: `django_strawberry_framework/list_field.py`

Status: verified

## System trace

`list_field.py` owns three responsibilities:

1. **`DjangoListField(target_type, ...)`** - the factory for a non-Relay
   `list[T]` root field. Its default resolver seeds `initial_queryset(target_type)`
   and applies visibility through `apply_type_visibility_sync` / `_async`,
   dispatching per-call on `in_async_context()` (there is no consumer resolver
   to inspect at construction, so the choice can only be made at call time).
   Its consumer-`resolver=` wrap coerces `Manager` -> `QuerySet`, applies
   visibility to a `QuerySet` return, and passes any other iterable through
   unchanged, dispatching sync-vs-async at *construction* time via
   `is_async_callable`.
2. **`_validate_djangotype_target`** - the four constructor-site guards every
   `DjangoType`-target field factory needs (is-a-class, is-a-`DjangoType`
   subclass, carries its *own* `__django_strawberry_definition__`, resolver is
   callable). `_validate_relay_djangotype_target` layers the fifth
   Relay-Node-shaped guard on top via `types/base.py::_is_relay_shaped`.
3. **`_post_process_consumer_sync` / `_post_process_consumer_async`** - named
   module-scope entry points the two `_wrap` closures call; both delegate
   verbatim to `utils/querysets.py::post_process_queryset_result_sync` /
   `_async`.

Connected surfaces traced:

- `connection.py` imports `_validate_relay_djangotype_target` directly
  (`DjangoConnectionField`'s five guards) and mirrors the async-dispatch shape
  in `_build_connection_resolver` (default / sync-consumer / async-consumer),
  but its consumer-return path runs the full composition pipeline
  (`_pipeline_sync` / `_pipeline_async`: visibility -> filter -> orderBy ->
  deterministic order -> optimizer plan), not the list field's plain
  post-process.
- `relay.py::_validate_node_target` is a thin wrapper over
  `_validate_relay_djangotype_target` for `DjangoNodeField` / `DjangoNodesField`
  (no `resolver=` seam, so it always passes `None`).
- `utils/querysets.py` is the canonical owner of
  `post_process_queryset_result_sync/_async`, `apply_type_visibility_sync/_async`,
  `initial_queryset`, and `normalize_query_source` - the substrate this file's
  wrappers and `connection.py`'s pipeline both build on.
- `utils/typing.py::is_async_callable` and `types/base.py::_is_relay_shaped` are
  each single-sited and consumed here by name, not re-implemented.
- `tests/test_list_field.py` (27 test functions / 30 collected cases) pins every branch named above,
  including the four `docs/feedback.md`-era bug fixes (own-class registration,
  async-callable-object detection, `functools.partial` unwrap for both async
  functions and async callable instances) and the sync-coroutine / sync-custom-
  awaitable / sync-future rejection paths.

## Verification

- `git diff fb1ddce171646e4391ccc80ae3cc5e1a8b783737 -- django_strawberry_framework/list_field.py`
  is empty - no concurrent or in-flight change to reconcile.
- `rg "_validate_djangotype_target|_validate_relay_djangotype_target"` across
  `django_strawberry_framework/` confirms exactly one definition site
  (`list_field.py`) and two out-of-file consumers
  (`connection.py #"from .list_field import _validate_relay_djangotype_target"`,
  `relay.py #"from .list_field import _validate_relay_djangotype_target"`) plus
  the internal `_validate_relay_djangotype_target` ->
  `_validate_djangotype_target` delegation - a clean single-owner shape with
  no parallel re-implementation.
- `rg "_post_process_consumer_(sync|async)"` shows both names are private to
  this file (only the module itself and its own tests/docs reference them);
  reading their bodies confirms one-line delegation to
  `utils/querysets.py::post_process_queryset_result_sync/_async` with no logic
  of their own.
- Compared `list_field.py`'s default-resolver async dispatch
  (`in_async_context()` per call) against `connection.py::_build_connection_resolver`'s
  default branch (an unconditional sync `def` returning a lazy queryset) and
  `mutations/fields.py`'s module docstring, which independently states the same
  asymmetry rule ("`is_async_callable` construction-time for a consumer
  `resolver=` / `in_async_context()` runtime for the default generated
  resolver"). The three call sites agree on *why* the split exists (no
  consumer resolver to inspect at construction for a default resolver) and
  none re-derive the rule differently - not a duplicated policy, one
  documented asymmetry cited from three places.
- Compared the four/five-guard validators against two structurally similar
  "is this a registered DjangoType" checks elsewhere:
  - `management/commands/inspect_django_type.py` raises `CommandError` (not
    `ConfigurationError`) for a CLI operator inspecting an arbitrary type name
    at an arbitrary time post-finalization - a different consumer, a different
    error type, and a different lifecycle phase from a field-factory
    constructor guard.
  - `testing/relay.py::global_id_for` raises `ConfigurationError` but checks
    `definition.finalized` and the assigned GlobalID strategy - concerns that
    do not exist yet at `DjangoListField`/`DjangoConnectionField` construction
    time (Phase 3 finalization hasn't run). Reusing `_validate_djangotype_target`
    here would require threading a "skip the finalization check" flag through
    it, which trades one call site for a coupling between two different
    lifecycle phases.
  Both are rejected as sites for the shared validator: same-looking checks,
  different contracts and change reasons.
- Confirmed via `git log --oneline -- django_strawberry_framework/list_field.py`
  that the guard/wrapper consolidations described in the module's own comments
  (rev4 H2, rev5 H2, rev6 H1-H3, the 0.0.9 DRY pass Major 1 / Major 4) are
  real prior commits, not aspirational comments - `connection.py` and
  `relay.py` do import from here today.

## Opportunities

None - three candidates were traced and each is a documented, evidence-backed
non-duplication:

- **Repeated responsibility considered:** the three-way default /
  sync-consumer / async-consumer resolver-dispatch *shape* appears in both
  `DjangoListField` and `connection.py::_build_connection_resolver`.
  **Evidence against consolidating:** the branches share only trivial control
  flow (an `if resolver is None / elif is_async_callable / else`); the bodies
  inside each branch are genuinely different rules - the list field's default
  branch does per-call `in_async_context()` dispatch (no equivalent in the
  connection default, which is deliberately a single sync `def` returning a
  lazy queryset), and the consumer branches call entirely different
  post-processing (`_post_process_consumer_*` vs the multi-step
  `_pipeline_sync`/`_pipeline_async` composition, which the connection also
  feeds through `_synthesized_signature` for the `filter:`/`orderBy:` sidecars
  list fields don't have). A shared helper would need mode flags or injected
  callables for every one of those diverging steps - the DRY guideline's
  named anti-pattern ("a helper that... needs mode flags to reconcile
  different rules"). **Owner:** kept separate, one factory per field kind.
- **Repeated responsibility considered:** the async-detection *asymmetry*
  itself (construction-time `is_async_callable` for a consumer resolver vs
  runtime `in_async_context()` for a package-generated default resolver).
  **Evidence against consolidating:** this is one rule, already single-sourced
  in prose (this file's Decision-2 comment) and cited by name from
  `connection.py` and `mutations/fields.py` rather than re-derived - the
  *code* implementing each half already reuses the single `is_async_callable`
  / `in_async_context` primitives; there is nothing left to hoist because the
  asymmetry is a design decision, not a computation.
- **Repeated responsibility considered:** `_post_process_consumer_sync/_async`
  as wrappers over `utils/querysets.py::post_process_queryset_result_sync/_async`.
  **Evidence against consolidating:** the wrappers add no logic (one-line
  delegation) and exist only to give the `_wrap` closures a `_consumer`-suffixed
  name distinguishing them from the default-resolver path, which never calls
  the querysets.py functions directly because its `qs` is already a known
  `QuerySet` from `initial_queryset(...)`. Inlining the calls at the two `_wrap`
  sites would save two five-line functions at the cost of losing that naming
  signal; this is a readability/naming decision, not a repeated rule - the
  actual contract (`post_process_queryset_result_sync/_async`) already has
  exactly one implementation in `utils/querysets.py`, and nothing else in the
  repository re-implements it.

## Judgment

`list_field.py` is a stable, previously-consolidated file: its two exported
validators are the real cross-module owners `connection.py` and `relay.py`
already import, its post-process wrappers add naming clarity over the single
canonical `utils/querysets.py` implementation with no parallel logic, and the
one structural similarity to `connection.py`'s resolver-building shape does
not survive a contract-level comparison (different pipelines, different
signature needs, one deliberate sync/async asymmetry documented and reused by
name rather than re-implemented). No source change is warranted; the
item-scoped diff from baseline is empty by inspection and confirmed via `git
diff`.

## Independent verification (Worker 2)

Re-traced independently rather than reviewing only the artifact's claims.

- **Zero-edit confirmed.** `git diff fb1ddce171646e4391ccc80ae3cc5e1a8b783737
  -- django_strawberry_framework/list_field.py` is empty. `git log --oneline
  -- django_strawberry_framework/list_field.py` shows the file's last touch is
  `207022e8` ("Finish REVIEW of 0.0.9"), predating the stated baseline - no
  concurrent work to reconcile.
- **Single-owner claim re-verified independently.** `rg` for
  `_validate_djangotype_target|_validate_relay_djangotype_target|_post_process_consumer`
  across the whole repo (not just `django_strawberry_framework/`) returns
  exactly `list_field.py` (definitions),
  `connection.py #"from .list_field import _validate_relay_djangotype_target"`,
  `relay.py #"from .list_field import _validate_relay_djangotype_target"`, plus
  `tests/test_list_field.py` and the spec/DRY docs
  - no third implementation, no re-derivation. `rg "DjangoListField"`
  independently confirms one definition (`list_field.py`), one export
  (`django_strawberry_framework/__init__.py #"from .list_field import DjangoListField"`), and two prose-only mentions in `connection.py` /
  `mutations/fields.py` that cite the async-asymmetry decision by name rather
  than re-implementing it.
- **Connection resolver mirror - re-challenged.** Read `connection.py` in full
  (2095 lines): `_build_connection_resolver`'s three branches call
  `_pipeline_sync` / `_pipeline_async`, which run
  `apply_type_visibility_* -> filterset_class.apply_* -> orderset_class.apply_*
  -> _finalize_queryset` (deterministic order + `apply_connection_optimization`)
  - a materially different, longer pipeline than `list_field.py`'s
  `_post_process_consumer_sync/_async` one-liners, and it additionally threads
  `_synthesized_signature`'s `filter:`/`orderBy:` kwargs that
  `DjangoListField` has no equivalent for. Confirms the artifact: sharing the
  three-way dispatch *shape* would require injecting the entire pipeline
  behind a callable, which is exactly the mode-flag anti-pattern the DRY
  ground rules reject. Rejection upheld.
- **Async asymmetry - re-challenged.** Independently found a *third* site
  restating the same rule: `relay.py::DjangoNodesField._resolve` dispatches
  via `in_async_context()` per call with the comment "no consumer resolver to
  inspect at construction - the deliberate contrast with connection.py's
  committed-at-construction split," and `mutations/fields.py`'s module
  docstring states the identical rule for `DjangoMutationField` ("there is NO
  consumer `resolver=` seam to inspect at construction - so only the runtime
  half applies"). Four call sites (`list_field.py`, `connection.py`,
  `relay.py`, `mutations/fields.py`) now agree on the same documented
  asymmetry, none re-deriving it as new logic - reinforces, not weakens, the
  artifact's rejection.
- **Post-process wrappers - re-challenged.** Read both wrapper bodies and
  their sole callers (the two `_wrap` closures) plus
  `utils/querysets.py::post_process_queryset_result_sync/_async` in full - the
  wrappers add zero branching, and `rg "_post_process_consumer_(sync|async)"`
  confirms both names are private to `list_field.py` (only its own module and
  tests/docs reference them). Rejection upheld: this is a naming decision, not
  a duplicated rule.
- **Inspect/global_id guards - re-challenged.** Read
  `management/commands/inspect_django_type.py` and
  `testing/relay.py::global_id_for` in full. Both genuinely differ from the
  four/five-guard validator contract as the artifact states (different error
  types - `CommandError` vs `ConfigurationError`; different lifecycle
  phases - post-finalization introspection/minting vs constructor-time
  guard; different failure semantics - `global_id_for` gates on
  `definition.finalized` and the stamped GlobalID strategy, neither of which
  exists at `DjangoListField`/`DjangoConnectionField` construction time).
  Rejection upheld.
- **Missed-consolidation search (new finding, not blocking this item).**
  While tracing `list_field.py`'s only external dependency
  `types/base.py::_is_relay_shaped(cls, interfaces)` (`return
  any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls,
  relay.Node)`), found that
  `management/commands/inspect_django_type.py::Command._is_suppressed_relay_pk`
  re-derives the identical boolean expression inline
  (`any(issubclass(i, relay.Node) for i in definition.interfaces) or
  issubclass(definition.origin, relay.Node)`) instead of importing and calling
  `_is_relay_shaped`. This is a genuine duplicate of the predicate `list_field.py`
  itself correctly consumes by reference rather than re-deriving - but the
  duplicate lives in a different file, and its owner is `types/base.py`, not
  `list_field.py` (which has no re-derivation of its own and is not the site
  that needs to change). Recorded here for the `management/commands/inspect_django_type.py`
  and `types/base.py` plan items still open in `docs/dry/dry-0_0_13.md`; does
  not affect this item's zero-edit verdict.
- **Minor accuracy note (non-blocking).** The artifact's System trace states
  "`tests/test_list_field.py` (22 tests)"; an independent count
  (`rg "^(async )?def test_"` plus `pytest --collect-only`) finds 27 test
  functions / 30 collected test cases (one is `@pytest.mark.parametrize`d over
  4 values). Cosmetic - does not change any DRY finding - but the count should
  read 27 functions / 30 cases if this artifact is revised for any other
  reason.
- **Focused test run.** `uv run pytest tests/test_list_field.py -q` -> 30
  passed (coverage gate fails only because this is a single-file subset run,
  not the project-wide invocation; `list_field.py`'s own lines are 92% covered
  in isolation, with the uncovered `_validate_relay_djangotype_target` body
  exercised instead by `tests/test_connection.py` / the relay test tree, per
  the artifact's own connected-surfaces trace).

No revision required. The zero-edit claim, the single-owner claims, and all
four challenged rejected candidates hold under independent re-tracing. The one
new observation (`inspect_django_type.py`'s inline `_is_relay_shaped`
re-derivation) is real but belongs to a different file's item, not this one.
