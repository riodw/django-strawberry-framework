# Pre-BETA review: rest_framework/

Scope: the DRF serializer integration -- `resolvers.py` (serializer-backed
write pipeline + error mapping), `inputs.py`, `serializer_converter.py`, `sets.py`.
DRF (`djangorestframework`) is a soft dependency of the package.

Method: full logic read of `resolvers.py` in `docs/shadow/current/` plus the
diffs since `0.0.13` (this cycle folded the write-value decoders and field-spec
collision detection into the shared `utils/` helpers, and rebased
`SerializerFieldConversion` onto the shared `FieldConversionBase`). Read-only;
no tests run.

Bottom line: a genuinely strong integration -- it scopes DRF's own relation
validation to GraphQL visibility, maps nested serializer errors to faithful
GraphQL field paths, and asserts schema/serializer agreement at build time.
No P0 or P1.

## P0 -- correctness suspicions

None found.

## P1 -- fix before BETA

None found.

## P2 -- polish / hardening

### Resolved: `django_strawberry_framework/rest_framework/resolvers.py::_scope_relation_querysets_to_visibility` instance isolation
This rewrites each relation field's `.queryset` to
`filter(pk__in=visible.values(...))` so DRF's `PrimaryKeyRelatedField`
validation only accepts visible rows. It is safe *because* DRF builds
`serializer.fields` fresh per serializer instance (the declared fields are
deep-copied), so the mutation does not leak across requests.

Hardened: a synchronized concurrent regression now scopes two instances of the
same serializer class under different request visibility, covering both single
and many relation fields. It proves each instance keeps only its request's
visible rows and that the serializer class's declared field querysets remain
untouched, pinning the DRF deep-copy assumption against future changes.

### Resolved: `django_strawberry_framework/rest_framework/resolvers.py` soft-dependency import surface
The module imports `rest_framework` at module top, but the package root never
imports it eagerly. Hardened: a fresh-interpreter regression masks DRF through
the shared `sys.modules[name]=None` sentinel before the package's first import,
then proves both `import django_strawberry_framework` and its star import
succeed without loading the serializer subpackage. Reaching the serializer
surface alone raises the canonical install hint. The in-process boundary tests
now exercise every lazy root serializer export rather than only
`SerializerMutation`.

## API & consistency notes

- Error-path fidelity is excellent: `serializer_errors_to_field_errors`
  recursively flattens DRF's nested dict/list error trees into `FieldError`s
  with correct dotted paths, rekeys DRF source names to GraphQL names via
  `_build_reverse_map`, and maps DRF `non_field_errors` to the package
  `NON_FIELD_ERROR_KEY`. Keep this shape aligned with the forms and mutations
  error envelopes so all three write families emit one error vocabulary.
- `_assert_schema_runtime_agreement` fails loud when the generated GraphQL input
  diverges from the serializer's runtime fields (read-only, `source`, kind,
  related model). This build-time check is a real robustness asset -- keep it.
- Belt-and-suspenders visibility: the decode step resolves relation ids through
  `decode_visible_relation` / `visible_related_objects` *and* the serializer's
  own querysets are visibility-scoped. Redundant but cheap and defensible.

## Verified sound (do not re-flag)

- The serializer write runs as the `write_step` inside
  `mutations/resolvers.py::run_write_pipeline_sync`, so `serializer.save()` is
  inside the pipeline's `transaction.atomic()`; `DRFValidationError` /
  `DjangoValidationError` raised from `save()` are caught and mapped to field
  errors (rollback), never surfaced as a 500.
- `_merged_serializer_kwargs` injects the request into serializer context and
  rejects a conflicting caller-supplied request; `_assert_save_kwargs_no_shadow`
  rejects save kwargs that would silently override input fields.
- Nested serializers (`NESTED_SINGLE`/`NESTED_MULTI`) decode recursively with
  per-index error paths via `join_error_path`.
- Relation multi visibility: `_decode_relation_multi` collects pks then checks
  `pks_all_present(pks, visible_related_objects(...))`, so an id pointing at a
  hidden row is rejected as a field error.

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
