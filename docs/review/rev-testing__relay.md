# Review: `django_strawberry_framework/testing/relay.py`

Status: verified

## Understanding

`global_id_for` is the consumer test-suite entry point for minting the exact encoded `GlobalID` emitted by a finalized Relay-Node-shaped `DjangoType`. It reads the finalization-stamped `effective_globalid_strategy` and delegates the deterministic `model`, `type`, and `type+model` payload computation to `types/relay.py::encode_typename`; `callable` and `custom` strategies remain encode-only because their live encoders require a root object. `decode_global_id` is intentionally the exact public re-export of `types/relay.py::decode_global_id`, whose model-label branch resolves through `registry.py::TypeRegistry.get` to the model primary and whose type-name branch resolves through `registry.py::TypeRegistry.definition_for_graphql_name`.

The finalization path stamps strategies in Phase 2.5 before `DjangoTypeDefinition.finalized` flips in Phase 3. The helper therefore gates `finalized` first, preserving the partial-finalization failure contract. Live fakeshop node/refetch tests exercise model-label IDs, type dispatch, batches, malformed IDs, null visibility outcomes, and nested Relay behavior over HTTP.

## Verification

- `uv run pytest tests/testing/test_relay.py --no-cov -q` — 11 passed before the fix; existing helper tests covered model, type, type+model, callable/custom rejection, hostile representations, partial finalization, public decode identity, and secondary-to-primary routing.
- `uv run pytest tests/types/test_relay_interfaces.py -k 'globalid or decode or routing_audit or inherited_framework_closure' --no-cov -q` — 43 passed; strategy encoding/decoding, registry routing, inherited framework closures, malformed IDs, empty slots, and hostile `GlobalID` inputs remain covered.
- `uv run pytest examples/fakeshop/test_query/test_library_api.py -k 'node or global_id or genre_books_connection' --no-cov -q` — 36 passed; live `/graphql/` emission/refetch behavior agrees with helper payloads and dispatch.
- A pre-fix executable probe demonstrated that a finalized `Parent` subclass with no own `Meta` definition inherited the parent's definition and minted an ID, and that the same finalized class still minted after `registry.clear()`. A post-fix smoke probe rejects both states with `ConfigurationError`.
- `uv run ruff format .` reformatted the edited test file; `uv run ruff check --fix .` fixed one lint issue and finished with zero remaining errors.

## Improvements

### High

None.

### Medium

#### Require an active, own registered definition before minting

**Observation:** `global_id_for` previously treated the presence of an inherited `__django_strawberry_definition__` as proof that its argument was a registered finalized type.

**Evidence:** An unregistered `class Child(Parent): pass` inherited the finalized parent definition and produced a model-label ID. A class finalized in a prior lifecycle also produced an ID after `registry.clear()`. Neither class can be the active schema type whose emitted `GlobalID` the helper promises to mirror.

**Impact:** Consumer tests could silently mint IDs for a class that is not registered in the current lifecycle, masking schema registration/finalization errors and violating the helper’s “actual emitted GlobalID” contract.

**Recommendation:** Validate that the argument is a `DjangoType` class, that its definition is the registry’s exact current definition, and that `definition.origin is type_cls` before reading finalization or strategy state.

**Proof:** `tests/testing/test_relay.py::test_global_id_for_rejects_inherited_or_stale_definitions` covers both inherited and post-`registry.clear()` definitions; the post-edit smoke probe confirms both reject with `ConfigurationError`.

### Low

None.

## Summary

Strategy encoding and public decode dispatch matched finalized Relay behavior across package and live fakeshop paths. The helper had one real lifecycle/registration boundary defect; the owning helper now requires the active registry’s own definition, with permanent regression coverage.

## Implementation (Worker 1)

- Changed `django_strawberry_framework/testing/relay.py::global_id_for` to require an active registered `DjangoType` class, exact registry definition identity, and own-definition origin before minting.
- Added `tests/testing/test_relay.py::test_global_id_for_rejects_inherited_or_stale_definitions`.
- No expanded cross-file production ownership; only the prescribed mirrored test changed.

## Independent verification (Worker 2)

- Re-traced `global_id_for` through `registry.get_definition`, `DjangoType.__init_subclass__`, and `finalize_django_types`; the exact-definition plus `definition.origin is type_cls` check rejects inherited-only definitions and definitions left behind by `registry.clear()`, while accepting a fresh class registered in the rebuilt lifecycle.
- `uv run pytest tests/testing/test_relay.py --no-cov -q` — 12 passed.
- `uv run pytest tests/types/test_relay_interfaces.py -k 'globalid or decode or routing_audit or inherited_framework_closure' --no-cov -q` — 43 passed.
- `uv run pytest examples/fakeshop/test_query/test_library_api.py -k 'node or global_id or genre_books_connection' --no-cov -q` — 36 passed.
- Fresh clean-process probe (`PYTHONPATH=examples/fakeshop DJANGO_SETTINGS_MODULE=config.test_settings uv run python - <<'PY' ... PY`) verified: own definitions on a parent/child Relay hierarchy mint model-label IDs; an inherited-only child and finalized class after `registry.clear()` raise `ConfigurationError`; a fresh same-model class after clear mints successfully; a hostile metaclass raising from `__django_strawberry_definition__` / `__name__` / `repr` still produces the typed registration error.
- Existing focused tests and probes cover model, `type`, and `type+model` parity; callable/custom rejection; finalization and phase-3 partial-finalization transitions; public decode identity; primary/secondary routing; malformed and hostile decode inputs; and live node/refetch behavior. No additional issue found.
