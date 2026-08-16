# DRY review: `django_strawberry_framework/utils/errors.py`

Status: verified

## System trace

Flavor-neutral owner of the write-error envelope's leaf construction (promoted
out of `mutations/resolvers.py` so the model resolver is not the utility module
for form / serializer / auth / future write flavors):

1. **`field_error`** — the single `FieldError` leaf ctor. Owns `"__all__"` /
   empty-path normalization against `NON_FIELD_ERROR_KEY`, message/code coercion
   via `_str_list`, and structured `path` segment derivation. The only production
   `FieldError(...)` construction site in the package.
2. **`relation_field_error`** — uniform invalid / hidden / wrong-model relation
   leaf (`Invalid id for relation …`, code `invalid`). Called directly by model /
   form / serializer decode paths and by `utils/write_values.py`
   (`type_check_relation_id`, `decode_visible_relation`).
3. **`validation_error_to_field_errors`** — Django `ValidationError` → envelope
   mapper (`error_dict` / non-dict fallback). Consumed by model
   `_full_clean_or_field_errors`, form `_form_errors_to_field_errors`
   (`ValidationError(form.errors.as_data())`), and serializer save-hook
   Django-`ValidationError` catch.
4. **`join_error_path`** — empty-prefix-safe dotted join for nested write-error
   flatteners. Primary consumer: DRF
   `serializer_errors_to_field_errors` / `_error_node_children`; also used for
   nested relation-intent ledger paths that must stay algebraically identical to
   error paths.

Layering preserved: `FieldError` + `NON_FIELD_ERROR_KEY` stay in
`mutations/inputs.py` (single public type / sentinel). Constructors import them
function-locally so utils never imports mutations at module import time.
`mutations/resolvers.py` re-exports `field_error` /
`relation_field_error` / `validation_error_to_field_errors` for compatibility
(auth and tests still address them through resolvers).

Connected surfaces examined: `mutations/inputs.py`, `mutations/resolvers.py`,
`forms/resolvers.py`, `rest_framework/resolvers.py` (recursive flattener +
`_error_leaf` / `_error_detail_codes` / `_rekey_segment`), `auth/mutations.py`
(failed-login + register password), `utils/write_values.py`,
`utils/write_transaction.py` (`conflict_error`). Mutations folder already
verified — treated as evidence only.

Item baseline `82f53f4ea615ff535f5b38360395da211e92795a`: target matched
baseline; no production edit this pass.

## Verification

Searches:

- `FieldError(` — sole construction is inside `field_error`; no leftover inlined
  envelope construction across write flavors.
- `field_error` / `relation_field_error` / `validation_error_to_field_errors` /
  `join_error_path` call sites — all route through this module (or the
  mutations re-export of the same objects).
- `"Invalid id for relation"` — single message site (`relation_field_error`).
- Dotted-path join `f"{prefix}.{segment}" if prefix else segment` — see rejected
  candidates.
- Django / DRF `ValidationError` → envelope mapping — form reuses the shared
  mapper; DRF nested shape stays in the recursive flattener that still
  terminates at `field_error`.

No scratch experiments required: ownership and call-graph evidence were
decisive.

Strongest rejected candidates:

- **Inlined `f"{path}.{name}" if path else name` in
  `rest_framework/resolvers.py` (runtime ownership / validator-pin labels) and
  `rest_framework/sets.py` (schema ownership paths).** Same string algebra as
  `join_error_path`, different contract: ConfigurationError diagnostic locations
  vs client-visible GraphQL FieldError paths. They do not need to obey the
  root-vs-nested `__all__` rule and should not couple config diagnostics to the
  write-error helper (or pull `utils.errors` into `sets.py`). Intent-ledger
  paths already use `join_error_path` because they must mirror error-path shape.
- **Auth register `validate_password` → `resolvers.field_error("password", …)`
  with hand-extracted `error_list` codes.** Documented deliberate non-reuse
  (D-N2): a list-style `ValidationError` has no `error_dict`, so
  `validation_error_to_field_errors` would key to `"__all__"`, not `password`.
  Adding a `field=` override to the shared mapper would widen its contract for
  one call site and hide an auth-specific keying rule. Codes one-liner stays.
- **Promote per-message helpers (`null_field_error`, integrity / not-found /
  conflict leaves) into `utils/errors.py`.** Those messages are flavor / phase
  policy owned by mutations resolvers or `write_transaction.conflict_error`; they
  already go through `field_error`. Extra wrappers would invent a second helper
  layer without a second independent consumer set.
- **Fold DRF `_error_detail_codes` into this module / share with Django
  `leaf.code` extraction.** DRF `ErrorDetail` getattr vs Django
  `ValidationError.error_list` are different input shapes; both already feed
  `field_error(..., codes=...)`. Unifying would need mode flags.
- **Move `FieldError` / `NON_FIELD_ERROR_KEY` into utils.** Would invert the
  established public-type ownership in `mutations/inputs.py` and force every
  consumer of the GraphQL type through utils; the function-local import seam
  already solves the cycle.

## Opportunities

None — the four constructors already own leaf construction, relation-decode
uniformity, Django ValidationError mapping, and write-error path joining.
Call sites across model / form / serializer / auth / write_values /
write_transaction terminate at these owners; remaining similar-looking joins and
the auth password keying are intentional distinct contracts.

## Judgment

Proved zero-edit. `utils/errors.py` is the true owner of the write-error leaf
surface; no leftover inlined `FieldError` construction or parallel ValidationError
mapper remains. Ready for Worker 2.

Item-scoped diff vs `82f53f4ea615ff535f5b38360395da211e92795a`: artifact only
(`docs/dry/dry-file-utils__errors.md`); `django_strawberry_framework/utils/errors.py`
unchanged.

Deferred pytest: none required (no production edit). Existing coverage lives in
`tests/mutations/test_resolvers.py` (mapper / codes / root path),
`tests/rest_framework/test_resolvers.py` (flattener / join / nested `__all__`),
forms / auth relation and envelope tests via real write paths.

## Independent verification (Worker 2)

Re-traced write-error leaf ownership independently against present-day
`utils/errors.py`, flavor call sites (model / form / serializer / auth /
`write_values` / `write_transaction`), and package-wide searches for leftover
`FieldError(...)` construction and parallel ValidationError mappers.

**Zero-edit confirmed.** Item-scoped
`git diff 82f53f4ea615ff535f5b38360395da211e92795a -- django_strawberry_framework/utils/errors.py`
is empty.

**Sole construction + mapper ownership holds.** Package-wide `FieldError(` matches
only `utils/errors.py::field_error`. `"Invalid id for relation"` is single-sited in
`relation_field_error`. Django `ValidationError` → envelope mapping is only
`validation_error_to_field_errors` (forms wrap `form.errors.as_data()` into it;
serializer save-hook Django catch reuses it; DRF nested shape stays in
`serializer_errors_to_field_errors` / `_error_leaf` and terminates at `field_error`).
`mutations/resolvers.py` re-exports the three constructors; auth addresses them
through that compatibility path.

**Rejected candidates challenged and upheld.**

- Inlined `f"{path}.{name}" if path else name` in
  `rest_framework/resolvers.py::_assert_runtime_write_source_ownership` /
  `_pin_validator_querysets` and `rest_framework/sets.py::_assert_schema_source_ownership`:
  same string algebra as `join_error_path`, different contract — ConfigurationError
  diagnostic / validator-owner labels, not client-visible FieldError paths and not
  subject to root-vs-nested `__all__`. Intent-ledger instrumentation already uses
  `join_error_path` because those paths must mirror error-path shape. Pulling
  `utils.errors` into `sets.py` (or inventing a shared join for config diagnostics)
  would couple independent domains for a one-line join.
- Auth register `validate_password` → `resolvers.field_error("password", …)` with
  hand-extracted `error_list` codes (D-N2): list-style `ValidationError` has no
  `error_dict`, so the shared mapper's non-dict branch keys to `""` / `"__all__"`.
  A `field=` override would widen the mapper for one site and hide auth keying.
- Promote null / integrity / not-found / conflict message helpers into
  `utils/errors.py`: each already terminates at `field_error`; messages are flavor /
  phase policy (`mutations/resolvers.py`, `write_transaction.conflict_error`). Extra
  wrappers invent a second helper layer without a second independent consumer set.
- Fold DRF `_error_detail_codes` into utils / share with Django `leaf.code`
  extraction: DRF `ErrorDetail` getattr vs Django `ValidationError.error_list` —
  different input shapes, both already feed `field_error(..., codes=...)`.
- Move `FieldError` / `NON_FIELD_ERROR_KEY` into utils: would invert
  `mutations/inputs.py` public-type ownership; function-local import seam already
  solves the cycle.

**Missed-consolidation search:** no second `FieldError(...)` ctor; no parallel
Django ValidationError mapper; no leftover inlined relation-decode message; error /
intent paths already share `join_error_path` where lockstep matters. Zero-edit
stands.
