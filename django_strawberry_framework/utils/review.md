# Pre-BETA review: utils/

Scope: shared helpers used by every surface -- `write_values.py`,
`input_values.py`, `inputs.py`, `querysets.py`, `errors.py`, `permissions.py`,
`relations.py`, `converters.py`, `connections.py`, `strings.py`, `typing.py`,
`imports.py`.

Method: full logic read of `write_values.py` and `querysets.py` in
`docs/shadow/current/` plus the diffs since `0.0.13` (this cycle unified the
write-value decoders here so mutations/forms/rest_framework share one relation-
decoding spine, and unified the soft-dependency guards on
`require_optional_module`). The remaining helpers were read at the diff level.
Read-only; no tests run.

Bottom line: the shared write/visibility spine is correct and is what gives the
three write families their uniform IDOR posture. The one thing to surface before
BETA is the visibility fallback for relation targets that are not exposed as
types.

## P0 -- correctness suspicions

None found.

## P1 -- fix before BETA

### `querysets.py::related_visibility_queryset_or_default` -- unregistered relation targets bypass visibility
Confidence: medium (document + decide, likely not a code change). When a related
model has no registered `DjangoType`, `related_visibility_queryset(...)` returns
`None` and this helper falls back to `related_model._default_manager.all()` --
i.e. no GraphQL visibility filtering. `visible_related_object` /
`visible_related_objects` then resolve against that unfiltered manager. The
design intent is defensible (visibility is defined by a type's `get_queryset`;
a model with no type has no such policy), and a custom default manager still
applies. But this is a security-surface boundary that must be an explicit,
documented contract for BETA: "row-level visibility is enforced only for
relation targets exposed as `DjangoType`s; FK/M2M targets to unregistered models
are constrained only by the model's default manager and DB integrity." A
consumer who assumes every FK write is visibility-checked would be surprised.
Verify: write an FK to a valid-but-would-be-hidden row of an *unregistered*
related model and confirm it is accepted (fallback), versus a registered target.

## P2 -- polish / hardening

### `strings.py` case-conversion round-trips -- pin the acronym/digit/underscore edges
Confidence: low (not fully traced -- flagged for a script, not asserted). The
snake/camel/pascal helpers name GraphQL fields, so any input where
`snake -> camel -> snake` is not an identity, or where two distinct Python names
collapse to one camelCase name, is API breakage or a schema-build collision. The
finalizer's `_audit_field_surface` catches same-type camelCase collisions at
build time, which is the important backstop, but the conversion functions
themselves should have property tests over acronyms (`HTTPServer`), trailing
digits (`field2`), and leading underscores.
Verify: property-test `snake_case(camel_case(x)) == x` over a corpus including
acronyms, digits, and leading/trailing underscores.

### UNSET / null sentinel preservation through the decode layers
Confidence: low. `iter_provided_input_fields` is the single gate that
distinguishes provided from `UNSET`, and the write families depend on it to get
absent-vs-null-vs-provided right. Add a focused test that a value passing
through `decode_scalar_leaf` / `decode_visible_relation` / `decode_provided_fields`
never loses the null-vs-absent distinction across the conversion, since a single
sentinel slip here fans out to all three write paths.

## API & consistency notes

- `errors.py` is the single constructor for the typed-error envelope
  (`field_error`, `relation_field_error`, `validation_error_to_field_errors`,
  `join_error_path`). All three write families now build errors through it, so
  the error vocabulary is uniform by construction -- keep new error shapes here
  rather than in a surface module.
- The soft-dependency guards (`imports.py::require_optional_module` and its
  `require_drf` / `require_channels` / `require_debug_toolbar` delegates) were
  unified this cycle onto one shape; the absence tests standardized on the
  `sys.modules[name] = None` sentinel. Good -- keep every new soft dependency on
  this one guard.

## Verified sound (do not re-flag)

- `querysets.py::reject_async_in_sync_context` closes the coroutine it rejects
  (`value.close()`) before raising `SyncMisuseError`, so a mis-colored
  `get_queryset` does not leak an un-awaited coroutine warning.
- `write_values.py::decode_visible_relation` is the shared relation decoder:
  it handles the skip sentinel, decodes GlobalID vs raw pk via
  `type_check_relation_id` (rejecting cross-model ids), resolves through
  `visible_related_object` (visibility-scoped when the target is registered),
  and projects to the caller's key -- one spine for mutations/forms/DRF.
- `write_values.py::coerce_relation_pk_or_none` runs `to_python` + validators and
  returns `None` (not a raise) on a bad pk, so a malformed relation id becomes a
  clean field error.
- `permissions.py::apply_cascade_permissions` (root module, but read here for the
  helper interplay) threads `.using(queryset.db)` and uses a `ContextVar` cycle
  guard -- multi-DB-safe and terminating on circular FK graphs.

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
