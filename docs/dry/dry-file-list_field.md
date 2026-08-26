# DRY review: `django_strawberry_framework/list_field.py`

Status: verified

## System trace

`DjangoListField(target_type, *, resolver=..., max_rows=..., trusted_max_rows=...)` is the
non-Relay `list[T]` root-Query field factory (spec-020). It owns exactly four responsibilities,
each delegating its mechanics:

1. **Construction guards** — `_validate_djangotype_target` (four shared DjangoType-target checks;
   also imported by `connection.py::DjangoConnectionField` and `relay.py`'s node-target guard via
   `_validate_relay_djangotype_target`) and `resource_policy.validate_collection_bound` for a
   non-positive `max_rows`. Errors name the factory via the interpolated `field=`.
2. **Resolver dispatch** — default resolver (`initial_queryset` → visibility → bound, colored at
   call time by `in_async_context()`) vs consumer-resolver wrappers committed per construction
   (`is_async_callable` → async wrapper; else ONE sync body that classifies the returned value at
   call time). The async-detection asymmetry is intentional and documented.
3. **Composition order** — visibility hook composes onto the UNSLICED source, then the row bound
   applies LAST (`bounded_rows` / `bounded_rows_async`), enforced identically in every wrapper.
4. **Consumer-return contract** — Manager/QuerySet/list pass through
   `utils/querysets.py::post_process_queryset_result_{sync,async}` (Manager coercion, visibility,
   awaitable rejection); async-only iterables complete through `_resolve_async_iterable` or fail
   closed under sync execution via the shared `reject_async_iterable_in_sync_context`.

Consumers: package root export; fakeshop live queries (`test_library_api`,
`test_resource_policy_api`, `test_optimizer_auto_api`, `test_scalars_api`,
`test_glossary_api`); `tests/test_list_field.py` (22 tests); GLOSSARY `DjangoListField` entry
(ordering asymmetry, row bound, async-detection asymmetry). Lockstep surfaces: the shared
querysets contracts, resource_policy bounds, connection.py's mirrored dispatch posture.

## Verification

Axis 1 — cross-flavor policy mirroring (searched): compared against `DjangoConnectionField`
(`connection.py::_build_connection_resolver`) and the many-side relation resolvers
(`types/resolvers.py`, both colors of `bounded_rows`). The connection field deliberately runs ONE
sync body for plain-`def` AND declared async-generator resolvers ("ONE sync body serves the
remaining three shapes", with runtime classification); the list field still carried an older
THREE-arm shape whose dedicated `is_async_generator_callable` branch duplicated the sync body's
runtime route verbatim (`grep -rn "is_async_generator_callable" django_strawberry_framework` →
only `list_field.py` + definition). Bound policy mirrors correctly through the single
`effective_bound` owner (`grep bounded_rows` → list_field, types/resolvers, utils/connections).

Axis 2 — sync/async twins (searched): `_default`'s two arms and the wrapper pair are color twins
routing through the same shared runners (`apply_type_visibility_*`, `post_process_queryset_result_*`,
`bounded_rows{,_async}`); behavior compared via `tests/test_list_field.py` Groups B/D/E which run
both arms under both execution shapes. No unowned twin remains in this file after the fix below.

Axis 3 — derived rather than repeated knowledge (searched): the "async-only" classification is
derived once by `is_async_only_iterable`; the bound once by `effective_bound`; the model once by
`model_for`. The factory-name literals (`field="DjangoListField"`, `flavor_noun=`) are per-factory
error wording, not derived facts. No reconstruction found.

Axis 4 — inverse/round-trip pairs (ruled inapplicable): the target packs a resolver and applies a
one-way pipeline; it encodes no grammar decoded elsewhere (cursor encode/decode lives in keyset.py,
owned by the connection surface).

Axis 5 — contracts restated in another medium (searched): the ordering contract, row-bound
contract, and async-detection asymmetry appear in module/factory docstrings, GLOSSARY, spec-020/
spec-047, and are pinned by tests. Each medium states the shipped rule without re-implementing it;
no drift found (`grep -n "DjangoListField" docs/GLOSSARY.md`).

Equivalence experiment (pre-fix): calling any shape the dedicated branch caught (bare async-gen fn,
`partial(agen fn)`, `partial(async-gen __call__` instance`) always yields an AsyncIterable-only,
non-awaitable value (`uv run python -c ...` probe) — so the sync body's runtime route classifies it
identically to the declared-shape branch, including the SyncMisuseError message under
`execute_sync`.

Single-edit-site counts: "change how an async-only source completes" → 1 site
(`_resolve_async_iterable`) before and after; "change the async-only classification" → 1 site
(`is_async_only_iterable`) — already consolidated by earlier cycle items 9/13; "change the sync
wrapper's orchestration for async-only returns" → 2 sites before the fix (dedicated branch + sync
body's async-only arm), **1** after; "delete the now-unused declared-shape predicate" → 1 owner +
its 3 test-tree references, swept in the same change.

Strongest rejected candidates: `_post_process_consumer_sync/_async` one-line wrappers (named seam
entry points referenced by test anchors and the module contract comment — indirection, not
duplicated responsibility); `_bounded_async` (single-caller helper carrying the load-bearing
bound-LAST ordering rationale); moving `_validate_relay_djangotype_target` out of this module
(single-sited today; relocation is churn without duplication).

## Opportunities

**Repeated responsibility:** the consumer-resolver dispatch for async-only sources was spelled twice
— once per declared shape (`is_async_generator_callable` branch: guard + `_resolve_async_iterable`)
and once per returned value (sync body's `is_async_only_iterable` arm: identical guard + identical
completion). Both sites encoded "an async-only return completes through the async bound under async
execution, fails closed under sync execution."

**Sites:** `django_strawberry_framework/list_field.py` (two branches of the same factory);
orphaned enabler `django_strawberry_framework/utils/typing.py::is_async_generator_callable`
(sole production caller was the deleted branch; stale docstrings claimed it was shared with the
connection field, whose present-day code does not import it); test pins asserting the predicate in
`tests/test_list_field.py`, `tests/test_connection.py`, `tests/utils/test_typing.py`.

**Evidence:** posited change "adjust what the sync wrapper does between classifying and completing
an async-only source" forced 2 edits pre-fix, 1 post-fix. The connection sibling made the identical
collapse deliberately (one sync body, runtime classification), so the three-arm shape was cross-flavor
structural drift. Behavioral equivalence proven by the probe above plus the surviving end-to-end
tests: declared/partial-wrapped async-generator resolvers stay bounded on the async path
(`test_djangolistfield_async_generator_resolver_is_bounded`,
`test_djangolistfield_partial_async_generator_resolver_is_bounded`) and raise the unchanged
SyncMisuseError under sync execution
(`test_djangolistfield_sync_async_generator_resolver_raises_sync_misuse`,
`test_connection_partial_async_generator_resolver_raises_sync_misuse`).

**Owner:** value classification at resolve time — `utils/querysets.py::is_async_only_iterable`
consumed by the ONE sync wrapper body; declared-shape detection deleted as the obsolete path.

**Consolidation:** removed the `is_async_generator_callable` branch from `DjangoListField`
(two arms remain: awaited-coroutine wrapper vs one sync body); deleted
`utils/typing.py::is_async_generator_callable` and updated the module/`_callable_inspection_target`/
`is_async_callable` docstrings and the `utils/__init__.py` bullet; dropped the orphaned imports and
predicate-only asserts from the three test trees while keeping every end-to-end behavior pin.

**Proof:** permanent tests listed under Evidence run unchanged (except the two deleted
predicate-classification asserts); pytest run deferred per AGENTS.md — record for the final gate.

**Risks / non-goals:** the async-CALLABLE arm must stay construction-time (Strawberry freezes
sync-vs-async handling at schema build; only an `async def` wrapper gets awaited directly) — that
asymmetry is intentional and untouched. Spec-020's prose describes the historical three-arm shape;
completed specs are point-in-time records and were not rewritten. Generated `docs/shadow/` will
regenerate; concurrent maintainer edits observed mid-task (`filters/sets.py`,
`optimizer/predicates.py` spec-number updates) were left untouched.

## Judgment

The file's real duplication lived one level up from its text: the guard/completion mechanics had
already been single-sited into `utils/querysets.py` and `resource_policy.py` by earlier cycle items,
leaving a redundant declared-shape dispatch branch whose twin the connection field had already
deleted. Collapsing to the value-classified sync body removes the last two-site orchestration,
retires an orphaned predicate, and aligns both read-field flavors on one documented posture. All
five axes discharged; every remaining near-duplicate is either shared-owner delegation or
intentional colored symmetry.

## Implementation (Worker 1)

Tracked changes (vs cycle baseline `2585bad3`):

- `django_strawberry_framework/list_field.py`: dropped the dedicated async-generator branch and the
  `is_async_generator_callable` import; documented the collapsed sync body's value-classification
  posture at the branch.
- `django_strawberry_framework/utils/typing.py`: deleted `is_async_generator_callable`; updated
  module docstring, `is_async_callable`, and `_callable_inspection_target` docstrings to point the
  async-generator shape at the runtime route.
- `django_strawberry_framework/utils/__init__.py`: typing bullet now names one predicate.
- `tests/test_list_field.py`, `tests/test_connection.py`: removed orphaned imports and the two
  predicate-only asserts; rewrote those tests' docstrings to pin the surviving end-to-end behavior.
- `tests/utils/test_typing.py`: removed the predicate's section, fixtures, parametrized cases, and
  cyclic-stack assertion.

Post-edit: `uv run ruff format .` (1 file reformatted) and `uv run ruff check --fix .` (all checks
passed); `py_compile` clean on all six files. Pytest deferred (not authorized this item).

## Independent verification (Worker 2)

**Scope:** `git diff 2585bad` on the six claimed files matches the recorded change exactly — branch
removal in `list_field.py` (import narrowed to `is_async_callable`, collapsed-shape comment added),
verbatim predicate deletion plus docstring updates in `utils/typing.py`, one-bullet `utils/__init__.py`
edit, and orphan-import/predicate-assert removal from the three test trees with every end-to-end pin
retained (`test_djangolistfield_async_generator_resolver_is_bounded`,
`test_djangolistfield_partial_async_generator_resolver_is_bounded`,
`test_djangolistfield_sync_async_generator_resolver_raises_sync_misuse`,
`test_connection_partial_async_generator_resolver_raises_sync_misuse`; the connection-side
sync-misuse/async-path twins at tests/test_connection.py:1040/1061/1081 also survive). Baseline
comparison confirms the deleted branch's body was byte-identical to the sync body's
`is_async_only_iterable` arm; only the gate moved from declared shape to returned value.

**Shape enumeration (probe `docs/dry/temp-tests/list_field/probe_async_gen_shapes.py`,
reconstructing the deleted predicate verbatim):** eight shapes the old branch caught — bare
async-gen fn, `partial(agen fn)`, nested `partial(partial(agen fn))`, async-gen `__call__` instance,
`partial(instance)`, `staticmethod(agen fn)` descriptor, `staticmethod(partial(instance))`, bound
async-gen method — every one yields an async-only non-awaitable value when called and routes through
the identical arm. A callable satisfying BOTH predicates is impossible: both predicates unwrap via
the same `_callable_inspection_target` and read the same `__call__`, whose coroutine/async-gen flags
are mutually exclusive, so removing the elif ordering cannot change any routing. The only divergent
input family found is passing a class OBJECT whose `async def __call__` is an async-gen function
(calling runs `__init__`, returning a plain instance); that is outside the documented resolver
contract and the old path was equally broken there — it fed the non-iterable instance to
`_resolve_async_iterable` unconditionally — so no supported behavior regressed.
`SyncMisuseError` wording/timing re-proved live: same message with `flavor_noun="DjangoListField"`,
raised after resolver invocation and before consumption, no-op under async execution.

**Orphan sweep:** repo-wide search (package, all three test trees, examples/, scripts/) finds zero
remaining code references to `is_async_generator_callable`; hits are confined to point-in-time docs
(spec-020 prose, rationale, review artifacts, this cycle's files), which repository policy keeps as
historical records. Standing media checked for drift: GLOSSARY's async-iterable paragraph states the
value-level rule flavor-neutrally and needs no edit.

**Rejected candidates re-probed:** `effective_bound` remains one definition
(`resource_policy.py::effective_bound`) consumed by both colored appliers — no second owner exists;
`_post_process_consumer_{sync,async}` stay justified as named seams carrying substring-pinned test
anchors (tests/test_list_field.py:382/473/767) and a live-query-tier reference
(examples/fakeshop/test_query/test_library_api.py:723) over the single-sited querysets contracts.

**Single-edit-site recount:** posited change "alter what happens between classifying an async-only
return and completing it" — baseline forced edits at two sites (deleted branch + sync-body arm,
verified byte-identical in `git show 2585bad`), current tree forces one. Count 2→1 confirmed by
inspection, not taken on faith. Matrix axes re-checked against the target's real surface: all five
discharged as recorded; axis 5's media sweep independently repeated above.

**Pytest:** deferred per AGENTS.md; routed to the final gate.

Verdict: consolidation is equivalent on every reachable input, the orphan removal is complete, and
the recorded counts hold. Status set to `verified`.
