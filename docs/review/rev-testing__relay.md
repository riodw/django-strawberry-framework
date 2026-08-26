# Review: `django_strawberry_framework/testing/relay.py`

Status: verified

## Understanding

`django_strawberry_framework/testing/relay.py` provides the public consumer-facing Relay GlobalID testing helpers specified in `spec-032` (Decision 10):
1. `global_id_for(type_cls: type, id: object) -> str`: Mints the base64-encoded `relay.GlobalID` string that a finalized Relay-Node-shaped `DjangoType` emits for a given primary key / identifier. Reads the finalize-stamped `definition.effective_globalid_strategy` and derives the payload using `encode_typename(definition, strategy, type_cls, None)`.
2. `decode_global_id(gid: relay.GlobalID | str) -> tuple[type, str]`: Public re-export of `django_strawberry_framework.types.relay.decode_global_id`, resolving an encoded GlobalID or `relay.GlobalID` instance back to its target `DjangoType` class and parsed id string.

### Key Architectural Invariants & Behavior:
- **Import Seam & Tested-Usage Promotion**: Imported exclusively via the dotted submodule path `django_strawberry_framework.testing.relay` (deliberately not re-exported at `django_strawberry_framework.testing` root) to keep testing root imports lightweight and avoid loading `types` machinery unnecessarily.
- **Strict Registration & Ownership Gate**: Rejects inputs that are not registered `DjangoType` subclasses or whose definition origin does not match `type_cls` (`ConfigurationError`), with exception shielding for hostile `__getattr__` or `__repr__` descriptors.
- **Finalization & Strategy Gates**:
  - Gated on `definition.finalized` first, preventing partially-finalized types from minting ids.
  - Gated on non-`None` `definition.effective_globalid_strategy`, rejecting finalized non-Relay-Node `DjangoType` classes.
  - Gated on `strategy in STRING_GLOBALID_STRATEGIES` (`"model"`, `"type"`, `"type+model"`). Types using `callable` or `custom` strategies raise `ConfigurationError` because their encoders require a live `root` instance that the helper does not have.
- **Asymmetry Contract**: In multi-type model configurations, a secondary type emitter mints the payload it genuinely emits (`app_label.modelname`), while `decode_global_id` routes model-label payloads to the model's primary registered type via `registry.get(model)`.

## Verification

1. **Static and Structural Audit**:
   - Reviewed all 111 lines of `django_strawberry_framework/testing/relay.py` against `spec-032` and the type system finalization lifecycle.
   - Verified that `__all__ = ["decode_global_id", "global_id_for"]`.
2. **Existing Test Suite Audit**:
   - `tests/testing/test_relay.py`: 13 tests covering `model`, `type`, and `type+model` strategies, live schema execution equivalence, callable/custom strategy rejection, unfinalized type rejection, non-node type rejection, hostile `__repr__`/`__getattr__` safety, stale/inherited registry definition rejection, Phase 3 partial finalization failure handling, round-trip decoding, and secondary emitter asymmetry routing.
3. **Scratch Experiments**:
   - Executed `docs/review/temp-tests/testing_relay/test_scratch.py` to probe diverse identifier types (`int`, `str`, `uuid.UUID`) and `relay.GlobalID` instances passed to `decode_global_id`. All passed cleanly.
4. **Permanent Tests & Test Suite Run**:
   - Added permanent test in `tests/testing/test_relay.py`: `test_global_id_for_accepts_various_id_types_and_round_trips`.
   - Focused test run: `uv run pytest tests/testing/test_relay.py --no-cov` (14 passed in 4.92s).
   - Coverage verification: 100% statement coverage (25/25 statements) on `django_strawberry_framework/testing/relay.py`.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/testing/relay.py` is a clean, focused, and robust helper module. It faithfully reflects the type system's effective GlobalID strategies, enforces all validation boundaries with crisp `ConfigurationError` diagnostics, and maintains 100% test coverage.

## Implementation (Worker 1)

- **changed files and why each was necessary:**
  - `tests/testing/test_relay.py`: Added permanent unit test `test_global_id_for_accepts_various_id_types_and_round_trips` verifying that `global_id_for` cleanly coerces diverse identifier types (`int`, `str`, `uuid.UUID`) and round-trips them through `decode_global_id`.
  - `django_strawberry_framework/testing/relay.py`: Zero diff against cycle baseline HEAD (`12779c99`); existing production implementation is correct and complete.
- **permanent tests and the behavior they pin:**
  - `test_global_id_for_accepts_various_id_types_and_round_trips`: Pins that `global_id_for` correctly formats integer, string, and UUID identifiers into Relay GlobalIDs that decode back to the expected target type and string identifier.
- **scratch or focused verification and its result:**
  - Executed scratch test `docs/review/temp-tests/testing_relay/test_scratch.py` (2 passed).
  - Executed focused permanent test suite: `uv run pytest tests/testing/test_relay.py --no-cov` (14 passed).
  - Verified 100% test coverage on `django_strawberry_framework/testing/relay.py`.
- **formatter and linter results:**
  - Executed `uv run ruff format .` and `uv run ruff check --fix .` (all checks passed, 0 errors).
- **evidence for any rejected finding:**
  - No findings were rejected; implementation is robust and fully verified.
- **whether the completed behavior merits a changelog entry:**
  - No (test additions only; zero production code diff).

## Independent verification (Worker 2)

- **Trace validation**:
  - Validated `global_id_for(type_cls, id)` input handling and exception shielding against hostile `__getattr__`/`__repr__` descriptors and unregistered or inherited definitions.
  - Validated strict gating sequence: `definition.finalized` checked before `effective_globalid_strategy` inspection to shield against partial Phase 3 finalization failures.
  - Validated `STRING_GLOBALID_STRATEGIES` whitelist enforcement (`"model"`, `"type"`, `"type+model"`) and clean rejection of callable/custom strategies.
  - Validated payload derivation via `encode_typename` and correct `relay.GlobalID` formatting.
  - Validated `decode_global_id` re-export identity and behavior.
- **Zero-edit check**:
  - `git diff 12779c99 -- django_strawberry_framework/testing/relay.py` confirmed 0 diff (zero-edit).
- **Test execution**:
  - Ran `uv run pytest tests/testing/test_relay.py --no-cov` (14 passed in 3.67s).
  - Ran `uv run ruff check django_strawberry_framework/testing/relay.py tests/testing/test_relay.py` (all checks passed, 0 errors).
- **Conclusion**:
  - Implementation is complete, verified, and adheres to all architectural constraints and specifications. Status is verified.
