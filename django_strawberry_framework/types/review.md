# Pre-BETA review: types/

Scope: Meta-driven Django type definition -- `base.py` (`DjangoType` +
`Meta` processing), `definition.py`, `converters.py`, `finalizer.py`
(schema finalization), `relations.py`, `relay.py`, `resolvers.py`.

Method: full logic read of `finalizer.py` in `docs/shadow/current/` plus the
diffs since `0.0.13` (this cycle added `cursor_field` `Meta` validation in
`django_strawberry_framework/types/base.py::_validate_cursor_field` and touched
`converters.py`/`finalizer.py` for the keyset integration). Coverage of
`converters.py`/`resolvers.py`/`relations.py` is at the diff level. Read-only;
no tests run.

Bottom line: finalization is fail-loud and well-ordered -- unresolved relations,
ambiguous primaries, model-label routing conflicts, and camelCase field
collisions all raise `ConfigurationError` at build time rather than surfacing at
first query. The main BETA theme is the class-mutation / re-finalization
contract (shared with the registry review).

## P0 -- correctness suspicions

None found.

## P1 -- fix before BETA

### [RESOLVED] `django_strawberry_framework/types/finalizer.py::_synthesize_relation_connections` -- finalization mutates consumer classes; pin the re-finalization contract
Confidence: medium (architectural). Synthesizing relation connections does
`type_cls.__annotations__.pop(...)` and `setattr(type_cls, generated, field_obj)`
directly on the consumer's type class, and marks the attached field with
`_SYNTHESIZED_RELATION_CONNECTION_MARKER`. Those class mutations persist across
`registry.clear()` (clear resets the registry, not the class objects). The
idempotency guard (checking the marker) makes a second finalization safe, but the
combination means the framework assumes essentially one finalized schema per
process and leans on the marker + the elaborate `clear()` for test
re-finalization. This is the same boundary called out in the root `registry.py`
review; for BETA it should be a documented contract, and ideally the synthesized
field would be tracked so `clear()` can remove it (rather than relying on the
persistent marker) to keep re-finalization clean.
Verify: finalize, `registry.clear()`, re-register the same type with a different
relation shape, re-finalize, and assert the synthesized connection reflects the
new shape (not the stale first one).

Resolution:
`django_strawberry_framework/registry.py::TypeRegistry.register_type_teardown`
now owns a per-type LIFO teardown ledger consumed exactly once by both
`django_strawberry_framework/registry.py::TypeRegistry.clear` and
`django_strawberry_framework/registry.py::TypeRegistry.unregister`.
`django_strawberry_framework/types/finalizer.py::_register_relation_connection_teardown`
records the exact generated `StrawberryField` and post-decoration resolver
identities, the pre-synthesis annotation mapping, and any list resolver
suppressed by the `"connection"` shape. Teardown removes/restores only those
owned identities, so a same-named consumer replacement is never clobbered. The
marker remains only for partial-finalize retry inside one registry lifecycle;
it no longer persists as the cross-`clear()` mechanism. The same-named
fresh-class, different-shape regression is pinned in
`tests/test_relay_connection.py::test_registry_clear_removes_synthesized_state_before_different_shape_rebuild`.
The intentionally broader one-schema-build-per-process boundary and the narrow
generated-artifact teardown guarantee are documented in the
[finalization phase contract][glossary-finalize].

## P2 -- polish / hardening

### [RESOLVED] `django_strawberry_framework/types/base.py::_validate_cursor_field` -- keep it aligned with `django_strawberry_framework/keyset.py::validate_cursor_field_columns`
Confidence: low. `Meta.cursor_field` is validated in two places: a shape check
in `django_strawberry_framework/types/base.py::_validate_cursor_field` (must be
a non-empty sequence of non-empty strings) and the column-semantics check in
`django_strawberry_framework/keyset.py::validate_cursor_field_columns`
(local/concrete/non-nullable, unique terminal) run at finalization. Two
validators for one field is fine, but keep their messages and rules from
drifting -- a consumer should not pass the shape check and then hit a
differently-worded column check that contradicts it.

Resolution: `django_strawberry_framework/keyset.py::split_order_ref` now owns
entry syntax and contextual messages, while
`django_strawberry_framework/keyset.py::validate_cursor_field_references` owns
whole-sequence emptiness and duplicate detection. Both
`django_strawberry_framework/types/base.py::_validate_cursor_field` and
`django_strawberry_framework/keyset.py::validate_cursor_field_columns` call that
shared validator; only sequence-container normalization remains
class-time-specific and only model column semantics remain
finalization-specific. Repeated direction markers, relation traversal,
duplicate columns, and empty defensive inputs now fail under the same rules at
both layers.

## API & consistency notes

- `_audit_field_surface` runs *after* connection synthesis and sidecar binding,
  so it catches camelCase collisions among declared, auto-converted, and
  synthesized fields together. This ordering is load-bearing -- do not move the
  audit earlier.
- The finalizer is the one place that binds mutations, auth, forms, filtersets,
  and ordersets. That centralization is good, but it makes finalization order a
  contract: keyset validation runs before connection synthesis, which runs before
  the sidecar binds. The exact ordering is now documented in the
  [finalization phase contract][glossary-finalize] so future additions slot in
  correctly.
- Known-intentional (do not "fix"): `BigAutoField -> Int` mapping and the
  permitted duplicate-graphql-name spots are deliberate and load-bearing.

## Verified sound (do not re-flag)

- `finalize_django_types` is idempotent (`registry.is_finalized()` guard +
  per-definition `if definition.finalized: continue`).
- Unresolved pending relations raise `_format_unresolved_targets_error` before
  any resolver is attached; primary ambiguity for multi-type models raises
  before that. Fail-loud ordering is correct.
- `_bind_sidecar_sets` wraps filterset/orderset expansion and converts
  `ImportError` (unresolved lazy ref) and arbitrary expansion failures into
  `ConfigurationError`, and detects orphan sets (referenced but never bound).
- Cursor-field types get `validate_cursor_field_columns` at finalization, so a
  misdeclared keyset config fails at build time.
- Model-label GlobalID routing conflicts across multi-type models raise
  `_audit_model_label_routing`, with a secondary-collapse `logger.warning` for
  the non-primary emitters.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-finalize]: ../../docs/GLOSSARY.md#finalize_django_types

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
