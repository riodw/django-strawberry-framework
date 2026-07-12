# Pre-BETA review: mutations/

Scope: Meta-driven CRUD mutations -- `resolvers.py` (the write pipeline),
`inputs.py` (input/payload construction), `permissions.py`, `sets.py`
(`DjangoMutation` declaration + binding), `fields.py`.

Method: full logic read of `resolvers.py` in `docs/shadow/current/` plus the
diffs since `0.0.13` (this cycle extracted the shared write-value plumbing into
`utils/write_values.py` and centralized permission-class execution in
`permissions.py::run_permission_classes`). Read-only; no tests run.

Bottom line: the write path is the strongest part of the package to audit --
atomic, visibility-scoped, IDOR-aware, with correct absent/null/provided update
semantics. No P0 or P1. The notes below are documentation/hardening.

## P0 -- correctness suspicions

None found.

## P1 -- fix before BETA

None found.

## P2 -- polish / hardening

### `resolvers.py::_raw_pk_relation_error` -- raw-pk writes to unregistered related models rely on the DB for existence
Confidence: low (document, not fix). When a relation target model has no
registered `DjangoType`, `related_visibility_queryset(...)` returns `None` and
the raw-pk branch either does an existence check (registered-but-nullable path)
or defers entirely to the eventual `IntegrityError` at `save()`, which
`save_or_field_errors` maps to a generic field error. This is a reasonable
design -- there is no GraphQL visibility policy to enforce on a model that is not
exposed -- but the resulting contract ("relation targets that are not exposed as
types are validated by the database, not the visibility layer") should be stated
in the mutations docs so consumers do not assume row-level visibility applies to
every FK.
Verify: point an FK input at a valid-but-hidden row of an *unregistered* related
model and confirm the write is allowed (by design), versus a registered model
where it is rejected.

### `resolvers.py::_assign_m2m` -- `.set()` is full-replace; make the semantics explicit
Confidence: low (document). Providing an m2m field on an update replaces the
entire membership (`getattr(instance, name).set(pks)`); there is no
add/remove granularity. That is a defensible default, but it is a sharp edge for
API consumers (sending a partial list silently drops the omitted members).
Document it, and consider whether BETA wants an explicit add/remove input shape
before the API freezes.

### `resolvers.py::refetch_optimized` -- payload re-fetch uses the default manager, not the visibility scope
Confidence: low. The post-write payload object is re-fetched via
`initial_queryset(target_type)` (default manager) rather than the
visibility-scoped queryset. For the actor's own just-written row this is benign
and arguably correct (they authored it), but it means an update that moves a row
out of the actor's visibility still returns the row in the payload. Worth a
one-line note confirming this is intended.

## API & consistency notes

- Permission-denied raises a top-level `GraphQLError`
  (`authorize_or_raise`), whereas validation failures return field errors inside
  the payload's `errors` list. This asymmetry is intentional and matches typical
  designs, but document it so consumers know auth failures are *not* in the
  typed-error envelope.
- The three write families (mutations, forms, rest_framework) now share
  `run_write_pipeline_sync` and the `utils/write_values` decoders, so their
  transaction boundary, visibility-scoped instance location, and relation-id
  handling are identical by construction. This is a strong consistency win from
  this cycle's refactor -- keep the shared entry point as the single write spine.

## Verified sound (do not re-flag)

- `run_write_pipeline_sync` wraps decode+write in `transaction.atomic()` and
  calls `transaction.set_rollback(True)` before returning an error payload, so
  validation/decode failures roll back cleanly while still returning a typed
  payload (not raising).
- IDOR posture: update/delete fetch through `locate_instance`, which applies
  `apply_type_visibility_sync` *before* `authorize_or_raise`, so a row hidden by
  the query surface is unlocatable (returns not-found) and object-level
  permission runs on the same visibility seed as queries.
- `select_for_update` is honored inside the atomic block (correct -- Django
  requires an open transaction for row locks), gated on `meta.select_for_update`.
- Absent/null/provided update semantics: `iter_provided_input_fields` yields only
  provided (non-`UNSET`) fields; `_explicit_null_error` rejects null on a
  non-nullable model field; `_unprovided_exclude` excludes untouched fields from
  `full_clean` -- absent leaves untouched, null clears (or errors), provided sets.
- `_unprovided_exclude` keeps validating unprovided members of a unique-constraint
  group when a sibling member is provided, so partial updates cannot skip
  uniqueness checks.
- m2m is assigned after `save()` inside the same atomic block, so a multi-write
  mutation is all-or-nothing.
- GlobalID handling: `_decode_relation_id_set` and `coerce_lookup_id` reject
  cross-model / wrong-type / undecodable ids as field errors, never a 500.
- `_make_aware_if_naive` promotes naive datetimes under `USE_TZ`.

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
