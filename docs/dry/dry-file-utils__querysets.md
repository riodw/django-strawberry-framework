# DRY review: `django_strawberry_framework/utils/querysets.py`

Status: verified

## System trace

Cycle-safe owner of the package's query-source, field-coercion, sync/async
boundary, and sealed `DjangoType.get_queryset` visibility contracts (~3285
lines). Public surface:

1. **Query-source seed / normalize** — `model_for`, `initial_queryset`,
   `normalize_query_source` (+ private `_coerced_manager_queryset`). Manager →
   QuerySet coercion fails closed on non-queryset `.all()` and on `_db` drift;
   plain iterables stay `is_queryset=False` for caller-owned tails.
2. **Field coercion** — `coerce_field_value_or_none` (`to_python` +
   `run_validators` → `None` on failure). Field selection stays at each caller.
3. **Sync misuse / one-worker boundary** — `SyncMisuseError`,
   `reject_async_in_sync_context`, `_dispose_sync_awaitable`,
   `sync_pipeline_recourse`, `run_in_one_sync_boundary` (the sole production
   `sync_to_async(..., thread_sensitive=True)` invocation outside testing).
4. **Sealed visibility boundary** — `_seal_or_defect` and the defect walkers;
   `_prepared_visibility_source` / `_normalized_visibility_result`; colored
   runners `apply_type_visibility_sync` / `apply_type_visibility_async`. Never
   returns the consumer queryset object.
5. **Relation-visibility composition** — `visibility_scoped_related_queryset`,
   `related_visibility_queryset` / `_or_default`, `visible_related_object` /
   `visible_related_objects`, `stringified_pks_present`, `pks_all_present`.
6. **List/connection source guards** — `reject_awaitable_sync_source`,
   `reject_residual_async_source`, `post_process_queryset_result_sync` /
   `_async` (list-field consumer shape; connection reuses the guards +
   `normalize_query_source` with local sidecar / slice guards).

Connected surfaces examined (callers / re-exports / deliberate non-callers):

- `list_field.py` — default `initial_queryset` + `apply_type_visibility_*`;
  consumer path through `post_process_queryset_result_*`.
- `connection.py` — `normalize_query_source` inside `_prepare_pipeline_source`;
  both reject_* guards; colored visibility; cannot use post_process (filter /
  order / sidecar / pre-slice sit between normalize and return).
- `types/relay.py` — node defaults via `initial_queryset` +
  `apply_type_visibility_*`; re-exports `SyncMisuseError` for back-compat
  (`types/__init__.py` / package `__init__`).
- `optimizer/extension.py` — `normalize_query_source` on root returns;
  `optimizer/walker.py` — prefetch child via related `_default_manager.all()`
  then `apply_type_visibility_sync(..., allow_sliced=True)` (documented, not
  `initial_queryset`).
- `filters/sets.py` — related derive calls colored runners; `apply_async`
  wraps through `run_in_one_sync_boundary`.
- `orders/sets.py`, root `permissions.py` (`aapply_cascade_permissions`),
  `schema.py` atomic enter/exit, `auth/mutations.py`,
  `mutations/resolvers.py::run_pipeline_async` — all
  `run_in_one_sync_boundary`.
- `mutations/resolvers.py` / `forms/resolvers.py` /
  `rest_framework/resolvers.py` / `utils/write_values.py` — relation
  visibility + `sync_pipeline_recourse` / `visible_related_*` /
  `related_visibility_queryset` / membership helpers.
- `mutations/permissions.py` / `utils/permissions.py` —
  `reject_async_in_sync_context` for auth gates (permission-hook recourse
  wording stays local to those modules).
- `consumers.py::_refreshed_actor` — deliberately does **not** wrap
  Channels' `@database_sync_to_async` again.
- `testing/client.py` — `sync_to_async` without `thread_sensitive` for
  test-session login/logout (test harness, not resolution boundary).
- `relay.py` / `filters/base.py` / `utils/write_values.py` —
  `coerce_field_value_or_none` with per-site field choice.

Item baseline `e72fd6d53940ebdf6584eeae202c0827c6a44e92`: target matched baseline
(3285 lines, empty item-scoped diff). No production edit this pass.

## Verification

Package-wide leftover searches (fresh; not seeded from prior DRY/review
artifacts):

- **`sync_to_async(` / `thread_sensitive`** — sole production invocation is
  `run_in_one_sync_boundary`. Every async ORM / permission / mutation / filter /
  order / schema / auth surface either calls that helper or (consumers /
  testing) documents why it must not.
- **`.get_queryset(`** — only the two colored runners invoke
  `type_cls.get_queryset`; django-filter's `super().get_queryset(request)` in
  `filters/base.py` is a different API.
- **`isinstance(..., models.Manager)`** — only `normalize_query_source` and
  `_normalized_visibility_result`, both via `_coerced_manager_queryset`.
- **`coerce_field_value` / `run_validators`** — only the shared primitive
  implements the or-none safety wrapper; three callers pick fields.
- **`__django_strawberry_definition__.model`** — sole live lookup is
  `model_for` (`types/relay.py` mentions the path only in a comment rejecting
  it for proxy id-attr keying).
- **`apply_type_visibility_*` / `normalize_query_source` /
  `run_in_one_sync_boundary` / relation helpers** — every named consumer routes
  through this module; cascade root preparation reuses
  `_prepared_visibility_source`.

Permanent coverage already lives in `tests/utils/test_querysets.py` (~4200
lines), including `test_run_in_one_sync_boundary_is_single_sourced_from_utils`
and seal / Manager / SyncMisuse / post_process pins. No scratch experiment
required: call-graph + leftover searches were decisive. Pytest deferred per
cycle rules (no suite run this pass).

### Strongest rejected candidates

1. **Fold connection / list pipelines into `post_process_queryset_result_*`.**
   Shared pieces (reject_*, `normalize_query_source`, `apply_type_visibility_*`)
   are already owned here. Connection must interleave sidecar / pre-slice /
   filter / order between normalize and return; a shared post_process with mode
   flags would hide distinct tails.

2. **Rename / widen `visibility_scoped_related_queryset` to cover Relay
   defaults and mutation target authorize** (`apply_type_visibility_sync` +
   `initial_queryset`). Same two-call composition, but the helper's contract is
   relation visibility; mutation authorize then pins / locks; Relay keeps the
   default recourse. Collapsing would rename a security-adjacent helper for
   fewer lines without a second change axis.

3. **`canonical_pk` / keyset `_deserialize_cursor_value` vs
   `coerce_field_value_or_none`.** All touch `Field.to_python`, different
   contracts: pk equality (raise / fail-closed match), cursor round-trip
   (re-serialize + GraphQLError), vs "or None / identifies no row" safety.
   Mode-flagging one helper would couple them.

4. **Cascade / optimizer / filter child bases using
   `related_model._default_manager...all()` instead of `initial_queryset`.**
   Cascade needs `.using(state.alias)`; optimizer documents prefetch keyed on
   `field.related_model` (not the type's default manager via `model_for`);
   filter derive builds `child_base` with parent_db pinning. Different seeds,
   same visibility runner afterward — correct.

5. **Permission-hook recourse strings
   (`_PERMISSION_ASYNC_RECOURSE` / `_GATE_ASYNC_RECOURSE` / cascade
   `_ASYNC_RECOURSE`) into `sync_pipeline_recourse`.** Docstring already
   excludes them: write-pipeline recourse is about async `get_queryset` inside
   a sync ORM pipeline; permission / cascade wordings name different hooks and
   surfaces. Ownership of those strings is not this file.

6. **`run_pipeline_async` / list `_post_process_consumer_*` thin wrappers.**
   Named domain entries over already-owned primitives; deleting them only
   shortens call sites.

7. **Wrap `consumers.py` / `testing/client.py` in `run_in_one_sync_boundary`.**
   Consumers would double-wrap Channels' `database_sync_to_async` and drop
   `close_old_connections`; testing login is harness session IO without
   resolution boundary discipline.

8. **Internal seal walkers as "duplication" to collapse further.** The sealed
   boundary's defect taxonomy is one responsibility already local to this
   file; further merging would obscure fail-closed codes, not remove a second
   system owner.

## Opportunities

None — query-source normalization, Manager coercion, field or-none coercion,
SyncMisuse disposal, the one-worker sync boundary, the sealed visibility
runners, and relation-visibility composition already have one authoritative
implementation here. Call sites either consume those owners or intentionally
differ (connection pipeline tail, cascade/optimizer seeds, permission recourse
wording, Channels/testing sync bridges).

## Judgment

Proved zero-edit. Prior consolidations into this module hold under a fresh
leftover walk: no second `get_queryset` router, no leftover
`thread_sensitive=True` resolution boundary, no parallel Manager→QuerySet
coerce, no parallel `coerce_field_value_or_none`. Strongest lookalikes are
intentional forks (connection vs list post_process, to_python equality/cursor
vs or-none, related-manager seeds with alias/prefetch constraints). Ready for
Worker 2.

## Implementation (Worker 1)

Zero-edit. No production, test, export, or doc changes.

Item-scoped diff vs `e72fd6d53940ebdf6584eeae202c0827c6a44e92`:

```text
# empty for django_strawberry_framework/utils/querysets.py
# this artifact only: docs/dry/dry-file-utils__querysets.md (new)
```

Deferred pytest: existing `tests/utils/test_querysets.py` (and list /
connection / mutation / filter / permissions pins) remain the permanent
proof; suite not run this pass. No changelog candidate.

## Independent verification (Worker 2)

**Outcome:** verified. Zero-edit claim holds. Plan checkbox marked `[x]`.

**Item-scoped diff:**
`git diff e72fd6d53940ebdf6584eeae202c0827c6a44e92 -- django_strawberry_framework/utils/querysets.py`
is empty (3285 lines match baseline).

**Re-trace (independent):** Full present-day `utils/querysets.py`. Query-source
(`model_for` / `initial_queryset` / `normalize_query_source` /
`_coerced_manager_queryset`), `coerce_field_value_or_none`, SyncMisuse disposal
(`reject_async_in_sync_context` / `_dispose_sync_awaitable` /
`sync_pipeline_recourse`), `run_in_one_sync_boundary`, sealed visibility
(`_seal_or_defect` / `_prepared_visibility_source` /
`_normalized_visibility_result` / colored runners), relation-visibility
composition, and list post-process + shared reject_* guards all sole-own here.
Consumers route through those owners; connection keeps its interleaved
sidecar / pre-slice / filter / order tail locally after shared normalize +
guards + visibility.

**Independent leftover search:**

- `sync_to_async(` production invocation: only
  `run_in_one_sync_boundary` (`thread_sensitive=True`). Other hits are
  docs/comments, `testing/client.py` login/logout without
  `thread_sensitive`, and Channels `@database_sync_to_async` in
  `consumers.py` (explicitly must not re-wrap).
- `.get_queryset(`: only the two colored runners invoke
  `type_cls.get_queryset`; `filters/base.py` `super().get_queryset(request)`
  is django-filter's API.
- `isinstance(..., models.Manager)`: only `normalize_query_source` and
  `_normalized_visibility_result`, both via `_coerced_manager_queryset`.
- `coerce_field_value_or_none` / `run_validators` or-none wrapper: sole body
  here; callers are `relay.py`, `filters/base.py`, `utils/write_values.py`.
- `__django_strawberry_definition__.model` live lookup: only `model_for`
  (`types/relay.py` mentions the path in a comment rejecting it for proxy
  id-attr keying).
- Permanent pin
  `tests/utils/test_querysets.py::test_run_in_one_sync_boundary_is_single_sourced_from_utils`
  still asserts mutations re-export identity.

**Challenges to rejected candidates (source evidence):**

1. **Fold connection into `post_process_queryset_result_*`.** Connection
   `_pipeline_sync` / `_pipeline_async` already share reject_*,
   `normalize_query_source` (via `_prepare_pipeline_source`), and
   `apply_type_visibility_*`, then run filter / order / `_finalize_queryset`
   between normalize and return. List post_process returns after visibility
   (or plain iterable). A shared post_process with mode flags would hide
   distinct tails — reject stands.

2. **Widen `visibility_scoped_related_queryset`.** Helper docstring owns
   relation-visibility composition. Mutation target authorize
   (`mutations/resolvers.py`) re-spells the same two calls then
   `pin_write_queryset` / `base_locked_queryset`; Relay node defaults keep
   default recourse + id filter. Using the relation-named helper for
   non-relation authorize would misuse ownership; renaming for fewer lines
   has no second change axis — reject stands.

3. **`canonical_pk` / keyset `_deserialize_cursor_value` vs
   `coerce_field_value_or_none`.** `write_transaction.py::canonical_pk` is
   pk `to_python` that raises; `pks_match` maps failure to inequality.
   `keyset.py::_deserialize_cursor_value` re-serializes and raises
   `GraphQLError`. Or-none is identify-no-row safety with validators. Same
   `to_python` surface, three contracts — reject stands.

4. **Cascade / optimizer / filter seeds via `initial_queryset`.** Cascade
   uses `field.related_model._default_manager.using(state.alias).all()`;
   optimizer walker documents prefetch keyed on `field.related_model` then
   `apply_type_visibility_sync(..., allow_sliced=True)`; filter derive pins
   `child_manager.using(parent_db).all()`. Different seeds, same visibility
   runner afterward — reject stands.

5. **Permission / cascade recourse into `sync_pipeline_recourse`.**
   `sync_pipeline_recourse` docstring excludes them: write-pipeline wording
   is about async `get_queryset` inside a sync ORM pipeline.
   `_PERMISSION_ASYNC_RECOURSE` / `_GATE_ASYNC_RECOURSE` name permission
   hooks; cascade `_ASYNC_RECOURSE` names cascade walk / `fields=` —
   reject stands.

6. **Wrap Channels / testing in `run_in_one_sync_boundary`.**
   `consumers.py::_refreshed_actor` documents double-wrap would drop
   `close_old_connections`. `testing/client.py` is harness session IO
   without resolution-boundary discipline — reject stands.

**Missed-consolidation search:** No second sealed `get_queryset` router, no
leftover `thread_sensitive=True` resolution boundary, no parallel
Manager→QuerySet coerce for consumer sources, no parallel or-none field
coerce. DRF `relation.queryset.all()` before pin+visibility AND is author
queryset normalize, not the sealed Manager coerce. Ready for Worker 0.
