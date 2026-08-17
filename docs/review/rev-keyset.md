# Review: `django_strawberry_framework/keyset.py`

Status: verified

## Understanding

`keyset.py` owns the complete `Meta.cursor_field` value-cursor contract: declaration and
finalization validation (`split_order_ref`, `validate_cursor_field_references`,
`validate_cursor_field_columns`), model-field resolution (`cursor_columns_for`), authenticated
opaque AES-SIV encoding/decoding (`encode_keyset_cursor`, `decode_keyset_cursor`), effective-order
fingerprints (`order_fingerprint`), and the dialect-neutral seek plan (`KeysetSeek`,
`KeysetSeekPlan`, `build_keyset_seek_plan`). `keyset_seek_q` is the ORM renderer used by root and
windowed paths; `keyset_seek_sql` is the parameterized renderer used by PostgreSQL lateral fetches.

The declaration path in `types/base.py::_validate_cursor_field` owns shape and Relay-node checks;
`types/finalizer.py::finalize_django_types` invokes the target's final column validation once model
fields and interfaces are settled. `connection.py` caches declared keyset state, derives root
`orderBy:` cursor columns (including annotated forward-single relation paths), and routes root and
per-parent fallback connections through `_resolve_keyset_connection`. Windowed nested connections
decode a shared `KeysetSeek` in `optimizer/nested_planner.py`, while
`optimizer/plans.py::apply_window_pagination` applies the same Q predicate either in the base
WHERE (count-free) or as a filtered running count (counted). The lateral strategy binds adapted
values through each Django field and renders the same seek plan in `optimizer/lateral_fetch.py`.
All visibility/queryset pipeline work happens before the seek, so cursor replay remains scoped to
the current viewer.

## Verification

- The scoped source diff is empty:
  `git diff 34396e42c7d5fff4d9bb15ceca3d5745b7a18475 -- django_strawberry_framework/keyset.py`.
  Permanent keyset sources and tests were untouched by this review.
- Read the complete target and traced its callers through type validation/finalization,
  connection state/order/slicing, nested planning, window pagination, lateral SQL, and the live
  library schema.
- Focused verification passed: `uv run pytest tests/test_keyset.py tests/test_keyset_connection.py
  examples/fakeshop/test_query/test_keyset_api.py --no-cov` — 108 passed.
- Disposable scalar experiment:
  `docs/review/temp-tests/keyset/scalar_roundtrip.py` round-tripped Boolean, float, Decimal,
  date, datetime, time, UUID, signed-bigint, and unsigned-bigint values through the field codec;
  every decoded value matched the source value.
- Existing tests and live HTTP paths cover forward/backward pages, insert/delete stability,
  count-free probes, counted pre-seek totals, empty/marker pages, `last: 0`, permission-aware
  replay, order fingerprints, related-path annotations, tampered/foreign/offset cursors,
  nullable/JSON/non-unique declaration rejection, sync/async callers, and lateral/window parity.

## Improvements

### High

None.

### Medium

None.

### Low

None.

### Rejected findings

- **Cursor payloads are not connection/type scoped.** The contract deliberately fingerprints the
  effective order and authenticates the values, while visibility is reapplied to the receiving
  queryset. Sharing a cursor between two connections with the same field order does not bypass
  visibility or produce an untyped SQL path; adding a model/type scope would be an API change not
  required by the documented keyset vocabulary.
- **The ORM and lateral seek renderers should be merged.** They already share
  `keyset_seek_greater`, `KeysetSeekPlan`, and `build_keyset_seek_plan`; the remaining difference is
  the required representation (portable Django `Q` versus parameterized PostgreSQL SQL), so
  further merging would obscure rather than centralize the invariant.
- **`split_order_ref` should replace the best-effort order parser everywhere.** The callers have
  opposite obligations: declaration-time malformed `cursor_field` entries must raise
  `ConfigurationError`, while query-time `orderBy:` expressions and relation paths must either be
  resolved or produce a field-level GraphQL error/fallback. Their tested syntax and error
  contracts intentionally differ.
- **The codec should be tested by pinning literal cursor bytes.** AES-SIV ciphertext is deliberately
  opaque and key-dependent; tests mint and round-trip cursors, then exercise tamper and prefix
  rejection, which proves the public contract without coupling fixtures to cryptographic bytes.

## Summary

The keyset module has a single codec, a single direction/seek-plan owner, and consistent
validation/error boundaries across root, nested windowed, lateral, fallback, and async paths.
Focused package and live tests pass, and the scalar codec experiment adds evidence beyond the
integer/string fixtures. No accepted root-cause finding was found; this is a zero-edit review.

## Implementation (Worker 1)

None — zero-edit cycle.

- Changed production files: none. `keyset.py` and its permanent callers/tests remain identical to
  the scoped baseline; no unrelated concurrent work was touched.
- Permanent tests: none added because the existing package and live suites already pin every
  reachable keyset behavior described above.
- Scratch verification: `docs/review/temp-tests/keyset/scalar_roundtrip.py` passed for all nine
  scalar families listed in `## Verification`.
- Focused tests: 108 passed with `--no-cov`.
- Formatter/linter: the disposable scratch file passed `uv run ruff format --check`; targeted
  `uv run ruff check --fix` fixed one import-order issue and left zero errors. No production or
  permanent test file was edited.
- Rejected findings and their evidence are recorded above; no production behavior needs a
  workaround or test-only patch.
- Changelog: no entry warranted for a zero-edit review.

## Independent verification (Worker 2)

Status: verified. The target remains a zero-edit cycle: `git --no-pager diff
34396e42c7d5fff4d9bb15ceca3d5745b7a18475 -- django_strawberry_framework/keyset.py` is empty,
and no production or permanent test file was changed.

- Re-read the complete codec and its connected declaration/finalization, connection, nested
  planner/window, lateral SQL, example schema, and test paths. The one `KeysetSeekPlan` direction
  owner feeds the ORM and parameterized SQL renderers; visibility is applied before every seek.
- Re-ran `uv run pytest tests/test_keyset.py tests/test_keyset_connection.py
  examples/fakeshop/test_query/test_keyset_api.py --no-cov`: 108 passed.
- Re-ran `uv run pytest tests/optimizer/test_lateral_fetch.py
  tests/optimizer/test_nested_fetch.py tests/test_lateral_pg_parity.py --no-cov`: 102 passed,
  35 Postgres-marked tests skipped as expected without a Postgres server.
- Re-ran `uv run python docs/review/temp-tests/keyset/scalar_roundtrip.py`: Boolean, float,
  Decimal, date, datetime, time, UUID, signed-bigint, and unsigned-bigint values all round-tripped
  exactly. An additional malformed-ciphertext probe (empty, short, and arbitrary valid-base64
  bodies under the valid `dstcursor` prefix) returned the uniform invalid-cursor `GraphQLError`.
- Independently checked composite-primary-key rejection (`CompositePrimaryKey` is non-concrete),
  nullable/JSON/explicit-NULLS order rejection, mixed forward/backward predicate direction,
  key rotation fallback, count-free versus counted windows, async callers, and SQLite fallback
  behavior. The rejected candidates remain disposed: connection/type scoping is not needed to
  preserve visibility, separate Q/SQL renderers share the seek plan, declaration and query-time
  order parsers have intentionally different error contracts, and literal ciphertext pinning
  would couple tests to a configured secret.

No reproducible correctness, security, portability, or contract issue remains; item 12 is
approved.
