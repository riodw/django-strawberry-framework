# DRY review: `django_strawberry_framework/utils/write_transaction.py`

Status: verified

## System trace

Cycle-safe owner of the 0.0.14 mutation write-hardening seam (~957 lines):
one database discipline for the three write flavors (model / form /
serializer) plus delete and model-less plain form. Public surface:

1. **Managed write gate** — `_MANAGED_WRITE_ALIAS` ContextVar;
   `managed_write_transaction` (publish only); `require_managed_write`
   (fail-before-write if a plain `strawberry.Schema` is serving). Does
   **not** open `transaction.atomic`; schema (or a direct-pipeline test)
   opens the atomic, then publishes the alias.
2. **Router write alias** — `resolve_write_alias` (once per operation,
   model-less → `DEFAULT_DB_ALIAS`); `pin_write_queryset` (fail closed on
   hook `.using(other)`); `check_instance_write_alias` (instance-sensitive
   router divergence after locate).
3. **Write pipeline context** — `WriteAliasContext` + `write_pipeline` /
   `current_write_pipeline` / `require_write_pipeline`; snapshots
   (`authorized_pk`, `target_state` via `snapshot_target_state` /
   `assert_no_target_drift`); phase flags (`pipeline_write_phase`,
   `authorization_phase` + `_enforce_read_only_barrier`);
   `pipeline_alias_guard` (cross-alias reject + pinned-alias read-only
   lexical discipline via `is_read_only_sql`).
4. **Row locks** — `base_locked_queryset` (base-manager `FOR UPDATE` +
   visibility pk subquery); `pipeline_scoped_queryset` (pin + conditional
   lock for shared relation-visibility helpers).
5. **Conflicts / pk identity** — `conflict_error`,
   `not_updated_exceptions`, `forced_update_conflict_errors`;
   `canonical_pk` / `pks_match`.

Connected surfaces examined (fresh, not seeded from prior DRY artifacts):

- `schema.py::DjangoMutationExecutionContext` — opens
  `transaction.atomic(using=alias)` then `managed_write_transaction(alias)`;
  completion-error `set_rollback` on the **outer** window (sync + async
  worker choreography). Independently re-checked from this module's side:
  this file only publishes/requires the alias; it never owns completion.
- `mutations/resolvers.py::run_write_pipeline_sync` — model-backed create /
  update skeleton: nested `transaction.atomic` + `write_pipeline`,
  `error_payload_builder` soft `set_rollback`, locate / auth / guard /
  decode / write / refetch. Delete + `forced_save_or_field_errors` keep
  local orchestration but call the same helpers.
- `forms/resolvers.py` — ModelForm rides the shared skeleton; plain form
  owns a model-less twin that still calls `require_managed_write`,
  `write_pipeline`, `pipeline_alias_guard`, `authorization_phase`,
  `pipeline_write_phase` + local soft `set_rollback`.
- `rest_framework/resolvers.py` — rides the shared skeleton; relation
  queryset scoping composes author qs ∧ visibility then
  `pin_write_queryset` / `base_locked_queryset`; save savepoint +
  `assert_no_target_drift` / `pipeline_write_phase`.
- `utils/querysets.py` — `stringified_pks_present` /
  `visible_related_object(s)` consume `pipeline_scoped_queryset`;
  visibility seal pins via `pin_write_queryset` when a pipeline is
  active.
- `auth/mutations.py` — rides `run_write_pipeline_sync` unchanged.
- Meta `select_for_update` validation lives in `mutations/sets.py`
  (`validate_select_for_update`); flavors only store the bool and pass
  `lock=` into `write_pipeline`.
- Tests: `tests/mutations/test_write_transaction.py` (module contract);
  flavor resolver tests cover locate lock opt-out and pipeline soft
  rollback.

Item baseline `eb0651a116e3d7342f546bf4cccaaca0f42e4048`: target matched
baseline (957 lines, empty item-scoped diff). No production edit this
pass.

## Verification

Package-wide leftover searches (concepts + identifiers):

- **`select_for_update()`** — sole production attach is
  `base_locked_queryset`. Optimizer fetch rejectors only *detect*
  locking querysets; no write-flavor attaches `FOR UPDATE` to a consumer
  queryset.
- **`pin_write_queryset` / `base_locked_queryset` /
  `pipeline_scoped_queryset`** — locate, serializer relation scoping,
  and queryset membership helpers all call these owners; no parallel
  pin+lock implementation.
- **`set_rollback(True)`** — four intentional sites with distinct
  contracts: schema completion errors (outer alias); pipeline /
  plain-form FieldError envelopes (soft no-effect); auth-phase barrier
  aliases (non-pinned auth containment). Not one repeated rule.
- **`transaction.atomic`** — schema outer; pipeline / plain-form /
  delete nested boundary; auth-phase barrier atomics; forced-update and
  serializer-save **savepoints** (exception containment so conflict /
  IntegrityError probes stay healthy). Nested under the outer when
  `DjangoSchema` is serving; required when tests bypass schema with
  `managed_write_transaction` alone.
- **Inline `.using(alias)` on write paths** — only framework-owned
  non-hook queries (post-write refetch by pk, serializer M2M
  attestation). Consumer / visibility querysets go through
  `pin_write_queryset`.
- **Direct `resolve_write_alias` at pipeline entry** — absent; pipelines
  take the managed alias from `require_managed_write` (schema already
  resolved and published). Plain form's model-less default is resolved
  once at schema wrap time.

Scratch experiments: none (ownership and contracts readable from source +
existing `tests/mutations/test_write_transaction.py`).

### Strongest rejected candidates

1. **Merge schema outer atomic with pipeline inner atomic.**
   From this file's side: `managed_write_transaction` is a ContextVar
   publish only; `require_managed_write` does not prove an atomic is open.
   Schema must open/close the atomic around graphql-core **completion**
   (async: enter/exit on the `thread_sensitive` worker across an event-loop
   await). Pipeline must own a sync write boundary for soft FieldError
   rollback and for direct-pipeline tests that wrap atomic + managed
   alias without `DjangoSchema`. Folding completion into `utils/` would
   import graphql-core execution into the wrong layer; dropping the
   pipeline atomic would break schema-bypass tests and remove the nested
   savepoint under the outer. Distinct decision points for
   `set_rollback` (completion errors vs in-band envelopes) are not the
   same as needing one atomic object. **Reject.**

2. **Absorb plain-form / delete orchestration into
   `run_write_pipeline_sync`.** Skeleton already owns model-backed create /
   update. Plain form is model-less (`{ ok errors }`, no locate / refetch);
   delete is snapshot-before-delete. Both already call this module's
   helpers. A shared mega-skeleton would need mode flags for absent
   instance / object slot / refetch. **Reject** — intentional local
   orchestration; discipline is single-sited here.

3. **New `pin_and_maybe_lock` forwarding helper over locate + serializer
   scoping + `pipeline_scoped_queryset`.** Primitives already own the
   rules. Locate takes explicit `alias` / `select_for_update` (callable
   from unit tests without a write-pipeline context — see
   `tests/mutations/test_resolvers.py`). Serializer composes **author qs
   ∧ visibility** before lock — different composition than
   `pipeline_scoped_queryset`'s pin+lock of one queryset. A thin wrapper
   would obscure those differences without removing a second rule.
   **Reject.**

4. **Unify `error_payload_builder` with plain-form inline soft rollback.**
   Same one-line `set_rollback` before envelope; different payload
   construction (`build_payload` + object slot vs `payload_cls(ok=False,
   ...)`). Consolidating couples model-backed and model-less shapes.
   **Reject.**

5. **Merge forced-update / serializer savepoint atomics into the pipeline
   atomic.** Those savepoints exist so a zero-row / IntegrityError
   escaping Django's `savepoint=False` inner write does not poison the
   pipeline transaction before conflict disambiguation or envelope
   mapping. Different lifecycle than the authorize→write boundary.
   **Reject.**

6. **Route locate through `pipeline_scoped_queryset` and drop the
   `select_for_update` parameter.** Would couple locate to
   `WriteAliasContext.lock` and break the existing direct unit-test
   seam. Dual pass of `meta.select_for_update` into `write_pipeline(lock=)`
   and `locate_instance(select_for_update=)` is same-function, same-source
   — not independent drift sites. **Reject.**

## Opportunities

None — write discipline for alias pinning, managed-transaction gating, row
locks, pipeline phases, and conflict envelopes is already owned here;
callers consume the helpers; apparent duplication is nested lifecycle
(outer completion vs inner pipeline vs savepoint vs auth barrier) or
flavor-specific composition (author∧visibility, model-less payload,
snapshot-before-delete), not a second implementation of the same rule.

## Judgment

Proved zero-edit. `utils/write_transaction.py` is the true owner of the
shared write-hardening invariants; schema / mutation / form / serializer /
queryset surfaces correctly sit on top of it. Strongest rejects: outer vs
inner atomics, absorbing plain-form/delete into the model-backed skeleton,
and inventing a pin+lock forwarding helper. Ready for Worker 2.

Item-scoped diff vs `eb0651a116e3d7342f546bf4cccaaca0f42e4048`: empty for
`django_strawberry_framework/utils/write_transaction.py`; this pass adds
only `docs/dry/dry-file-utils__write_transaction.md`.

## Independent verification (Worker 2)

Re-traced independently. Confirmed item-scoped diff vs
`eb0651a116e3d7342f546bf4cccaaca0f42e4048` for
`django_strawberry_framework/utils/write_transaction.py` is empty.

Schema publisher vs this module's require/pin/lock:

- `schema.py::DjangoMutationExecutionContext` resolves the alias once
  (`resolve_write_alias`), opens `transaction.atomic(using=alias)`, then
  publishes via `managed_write_transaction` only. Completion-error
  `set_rollback` stays on the outer window (sync in-process; async enter/exit
  on the `thread_sensitive` worker across the completion await).
- This module's `require_managed_write` only proves the ContextVar is set — it
  does not open or prove an atomic. Pipeline / plain-form / delete open their
  own nested `transaction.atomic` + `write_pipeline` for soft FieldError
  rollback and for direct-pipeline tests that wrap
  `managed_write_transaction` without `DjangoSchema`.

Challenged rejected candidates with source evidence:

1. **Merge outer/inner atomics — reject stands.** Distinct decision points:
   graphql-core completion errors (schema) vs in-band FieldError envelopes
   (pipeline) vs auth-barrier rollback (`authorization_phase`). Folding
   completion into `utils/` would pull graphql-core execution into the wrong
   layer; dropping the pipeline atomic breaks schema-bypass tests and removes
   the nested savepoint under the outer.
2. **Absorb plain-form / delete into `run_write_pipeline_sync` — reject
   stands.** Plain form is model-less (`{ ok errors }`, no locate/refetch);
   delete is snapshot-before-delete. Both already call this module's helpers;
   a mega-skeleton would need mode flags for absent instance / object slot /
   refetch.
3. **`pin_and_maybe_lock` forwarding helper — reject stands.** Locate takes
   explicit `alias` / `select_for_update` (unit-testable without a pipeline —
   `tests/mutations/test_resolvers.py`). Serializer composes author qs ∧
   visibility (separate pin on each, then lock) — different composition than
   `pipeline_scoped_queryset`'s pin+lock of one queryset. Primitives already
   own the rules.
4. **`error_payload_builder` vs plain-form soft rollback — reject stands.**
   Same `set_rollback` before envelope; different payload construction
   (`build_payload` + object slot vs `payload_cls(ok=False, ...)`).
5. **Forced-update / serializer savepoint atomics — reject stands.**
   Savepoints keep the pipeline transaction healthy for conflict /
   IntegrityError disambiguation; different lifecycle than the
   authorize→write boundary.
6. **Route locate through `pipeline_scoped_queryset` — reject stands.** Would
   couple locate to `WriteAliasContext.lock` and break the direct unit-test
   seam. Dual pass of `meta.select_for_update` is same-function, same-source.

Missed-consolidation search (fresh package-wide):

- **`select_for_update()`** — sole production attach is
  `base_locked_queryset`; optimizer paths only detect locking querysets.
- **`pin_write_queryset` / `base_locked_queryset` / `pipeline_scoped_queryset`**
  — locate, serializer relation scoping, and queryset membership helpers all
  call these owners; no parallel pin+lock implementation.
- **`set_rollback(True)`** — schema completion (outer); pipeline /
  plain-form FieldError envelopes; auth-phase barrier aliases. Distinct
  contracts, not one repeated rule.
- **Inline `.using(alias)` on write paths** — only framework-owned non-hook
  queries (post-write refetch by pk, serializer M2M attestation). Consumer /
  visibility querysets go through `pin_write_queryset`.
- **Direct `resolve_write_alias` at pipeline entry** — absent; pipelines take
  the managed alias from `require_managed_write`.

No further consolidation warranted. Verdict: zero-edit claim stands. Status →
verified; plan checkbox marked.
