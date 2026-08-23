# Bug hunt: 0.0.14

Status: complete
Mode: autonomous
Baseline commit: `bda1d18e283af3708a66f30c1e7043b9c17a0645`

## Package questions

No maintainer-authored probing questions were supplied. Explore the live source freely; shadow inputs are orientation only.

## How to hunt one file
Each item uses one source file as its entry point into the live system. The
target is narrow; the investigation and root-cause fix may cross files.

- Read the shadow overview and stripped source for baseline orientation, then
  read the complete live target. Shadow markers and stripped line numbers are
  never authoritative.
- Trace callers, dependencies, state, framework hooks, tests, examples, and
  public contracts far enough to understand the target's real behavior. Clean
  layers often fail only when several reasonable assumptions stack together;
  hunt those interactions, not only suspicious local lines.
- Break things, break things, break things. Write messy scratch test files and
  be maximally destructive inside disposable scratch scope: mutate throwaway
  state, force hostile sequences, interrupt lifecycles, and try to make every
  connected layer fail.
- For every extreme, test the opposite extreme and then combine them across
  layers. Try to disprove every candidate and record only confirmed defects.
- Do not clean up scratch probes or disposable state. Report every path and
  leave it intact so Worker 0 can independently verify it and clean it up only
  after the item passes.
- Implement the root-cause fix at the layer that owns the broken invariant,
  including connected files when required. Add a permanent behavioral test for
  every production fix at the strongest tier required by `AGENTS.md`.
- After edits run `uv run ruff format .` and `uv run ruff check --fix .`.
- Report evidence, changed files, tests, and validation to Worker 0. Do not edit
  this progress file; Worker 0 independently verifies fixes and advances it.

## Hunt items

- [x] django_strawberry_framework/_boundary_ordering.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework___boundary_ordering.stripped.py
    - docs/shadow/current/django_strawberry_framework___boundary_ordering.overview.md
    - Prompt:
        - Use django_strawberry_framework/_boundary_ordering.py as the entry point. Read docs/shadow/current/django_strawberry_framework___boundary_ordering.stripped.py and docs/shadow/current/django_strawberry_framework___boundary_ordering.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 18 adversarial scenarios including hostile view callbacks, descriptor exceptions, corrupted prepared-view tuples, ContextVar sync/async thread isolation, and CSRF ordering transitions.
    - Verification: Passed. Evidence: Independent scratch probe suite executed with 18/18 adversarial tests passing.
    - Cleanup: Removed docs/bug_hunt/temp-tests/_boundary_ordering/; unrelated work preserved.

- [x] django_strawberry_framework/_cross_web_patches.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework___cross_web_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___cross_web_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_cross_web_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___cross_web_patches.stripped.py and docs/shadow/current/django_strawberry_framework___cross_web_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 15 adversarial tests covering non-bytes request bodies, encoding/BOM matrices, malformed signatures, descriptor corruption, multithreaded apply concurrency, and settings variations.
    - Verification: Passed. Evidence: Independent scratch probe suite executed with 15/15 adversarial tests passing.
    - Cleanup: Removed docs/bug_hunt/temp-tests/_cross_web_patches/; unrelated work preserved.

- [x] django_strawberry_framework/_django_patches.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework___django_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___django_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_django_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___django_patches.stripped.py and docs/shadow/current/django_strawberry_framework___django_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 10 adversarial tests covering descriptor shape inspection, invalid signatures, database failure wrapper isolation, setting permutations, reload resilience, and teardown safety.
    - Verification: Passed. Evidence: Independent scratch probe suite executed with 10/10 adversarial tests passing.
    - Cleanup: Removed docs/bug_hunt/temp-tests/_django_patches/; unrelated work preserved.

- [x] django_strawberry_framework/_request_body.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework___request_body.stripped.py
    - docs/shadow/current/django_strawberry_framework___request_body.overview.md
    - Prompt:
        - Use django_strawberry_framework/_request_body.py as the entry point. Read docs/shadow/current/django_strawberry_framework___request_body.stripped.py and docs/shadow/current/django_strawberry_framework___request_body.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 27 adversarial tests covering negative/zero limits, unreadable/non-bytes chunks, unseekable streams, chunk boundary offsets, mid-stream read failures, and fail-closed safety.
    - Verification: Passed. Evidence: Independent scratch probe suite executed with 27/27 adversarial tests passing.
    - Cleanup: Removed docs/bug_hunt/temp-tests/_request_body/; unrelated work preserved.

- [x] django_strawberry_framework/_strawberry_patches.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework___strawberry_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___strawberry_patches.overview.md
    - Prompt:
        - Use django_strawberry_framework/_strawberry_patches.py as the entry point. Read docs/shadow/current/django_strawberry_framework___strawberry_patches.stripped.py and docs/shadow/current/django_strawberry_framework___strawberry_patches.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 133 adversarial tests covering scalar JSON bodies, malformed multipart maps, invalid UTF-8/BOM byte sequences, GET param query shielding, frame provenance traversal, and setting opt-outs.
    - Verification: Passed. Evidence: Independent scratch probe suite executed with 133/133 adversarial tests passing.
    - Cleanup: Removed docs/bug_hunt/temp-tests/_strawberry_patches/; unrelated work preserved.

- [x] django_strawberry_framework/apps.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__apps.stripped.py
    - docs/shadow/current/django_strawberry_framework__apps.overview.md
    - Prompt:
        - Use django_strawberry_framework/apps.py as the entry point. Read docs/shadow/current/django_strawberry_framework__apps.stripped.py and docs/shadow/current/django_strawberry_framework__apps.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 14 adversarial tests covering class invariants, raw instantiation, unbound execution, synthetic patch failures, omitted/null settings, concurrent ready() calls, and import isolation.
    - Verification: Passed. Evidence: Independent scratch probe suite executed with 14/14 adversarial tests passing.
    - Cleanup: Removed docs/bug_hunt/temp-tests/apps/; unrelated work preserved.

- [x] django_strawberry_framework/auth/mutations.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__auth__mutations.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__mutations.overview.md
    - Prompt:
        - Use django_strawberry_framework/auth/mutations.py as the entry point. Read docs/shadow/current/django_strawberry_framework__auth__mutations.stripped.py and docs/shadow/current/django_strawberry_framework__auth__mutations.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. 1. In `_register_decode_step`, replaced direct indexing `excluded_values["password"]` with `.get("password")` to prevent unhandled `KeyError` when password is omitted/UNSET. 2. In `_register_write_step`, added `isinstance(raw_password, str)` check to reject non-string passwords with `codes="invalid"` before `validate_password` / `set_password` crash with `TypeError`/`AttributeError`.
    - Verification: Passed. Evidence: Added `test_register_decode_step_with_unset_password_returns_none_password` and parametrized `test_register_write_step_non_str_password_defense_in_depth` to `tests/auth/test_mutations.py` (103/103 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/auth_mutations/; unrelated work preserved.

- [x] django_strawberry_framework/auth/queries.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__auth__queries.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__queries.overview.md
    - Prompt:
        - Use django_strawberry_framework/auth/queries.py as the entry point. Read docs/shadow/current/django_strawberry_framework__auth__queries.stripped.py and docs/shadow/current/django_strawberry_framework__auth__queries.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. In `_authenticated_actor_or_none` (`auth/mutations.py`) and `consumers.py`, replaced `user.is_authenticated` with `getattr(user, "is_authenticated", False)` to prevent unhandled `AttributeError` when `request.user` is a `SimpleLazyObject(lambda: None)` or unauthenticated actor object.
    - Verification: Passed. Evidence: Added assertions in `tests/auth/test_queries.py` and `tests/auth/test_mutations.py` covering lazy None users and custom actor objects (116/116 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/auth_queries/; unrelated work preserved.

- [x] django_strawberry_framework/auth/sessions.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__auth__sessions.stripped.py
    - docs/shadow/current/django_strawberry_framework__auth__sessions.overview.md
    - Prompt:
        - Use django_strawberry_framework/auth/sessions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__auth__sessions.stripped.py and docs/shadow/current/django_strawberry_framework__auth__sessions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 97 adversarial tests covering transport classification errors, hostile scope mappings, 20-worker concurrent locking stress without deadlocks, session engine matrix (db, cache, cached_db, file, signed_cookies), key cycling on login, fail-closed compensation on save failure, and session destruction on logout.
    - Verification: Passed. Evidence: Independent scratch probe suite executed with 97/97 adversarial tests passing.
    - Cleanup: Removed docs/bug_hunt/temp-tests/auth_sessions/; unrelated work preserved.

- [x] django_strawberry_framework/conf.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__conf.stripped.py
    - docs/shadow/current/django_strawberry_framework__conf.overview.md
    - Prompt:
        - Use django_strawberry_framework/conf.py as the entry point. Read docs/shadow/current/django_strawberry_framework__conf.stripped.py and docs/shadow/current/django_strawberry_framework__conf.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 51 adversarial tests covering non-mapping shape rejections, null vs unset vs empty settings resolution, unknown attribute access, dunder safety, upstream patch opt-out matrix, setting_changed signal cache invalidation, and multithreaded concurrent reads.
    - Verification: Passed. Evidence: Independent scratch probe suite executed with 51/51 adversarial tests passing.
    - Cleanup: Removed docs/bug_hunt/temp-tests/conf/; unrelated work preserved.

- [x] django_strawberry_framework/connection.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__connection.stripped.py
    - docs/shadow/current/django_strawberry_framework__connection.overview.md
    - Prompt:
        - Use django_strawberry_framework/connection.py as the entry point. Read docs/shadow/current/django_strawberry_framework__connection.stripped.py and docs/shadow/current/django_strawberry_framework__connection.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. Hardened `strawberry.UNSET` handling across Relay connection resolution: 1. In `_guard_first_and_last`, guarded against `UNSET` causing false mutual-exclusivity errors. 2. In `has_connection_sidecar_input`, ignored `UNSET` inputs. 3. In `derive_connection_window_bounds` & `derive_keyset_window_bounds`, ignored `UNSET` bounds. 4. In `_resolve_keyset_connection`, `_resolve_from_window`, `_consume_window`, `_pipeline_sync`, and `_pipeline_async`, prevented `UNSET` cursors, seek values, filter inputs, and order inputs from causing false cursor decode and pipeline errors.
    - Verification: Passed. Evidence: Added tests in `tests/utils/test_connections.py`, `tests/test_connection.py`, and `tests/test_keyset_connection.py` (168/168 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/connection/; unrelated work preserved.

- [x] django_strawberry_framework/consumers.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__consumers.stripped.py
    - docs/shadow/current/django_strawberry_framework__consumers.overview.md
    - Prompt:
        - Use django_strawberry_framework/consumers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__consumers.stripped.py and docs/shadow/current/django_strawberry_framework__consumers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across adversarial test matrix covering binary WebSocket frames, unknown subprotocols, duplicate subscription IDs (4409), malformed/null payloads (4400), non-finite / invalid revalidation windows, host header validation edge cases, subscription generator exception masking, and connection revocation state machine.
    - Verification: Passed. Evidence: Added test in `tests/test_routers.py` and ran full router/consumer test suite (166/166 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/consumers/; unrelated work preserved.

- [x] django_strawberry_framework/error_policy.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__error_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__error_policy.overview.md
    - Prompt:
        - Use django_strawberry_framework/error_policy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__error_policy.stripped.py and docs/shadow/current/django_strawberry_framework__error_policy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 55 adversarial tests covering non-mapping configurations, field validation, hostile exception objects (cyclic references, exploding __str__/__repr__, BaseException), zero database/SQL information leakage in production (`DEBUG=False`), and subscription stream masking.
    - Verification: Passed. Evidence: Independent scratch probe suite executed with 55/55 adversarial tests passing.
    - Cleanup: Removed docs/bug_hunt/temp-tests/error_policy/; unrelated work preserved.

- [x] django_strawberry_framework/exceptions.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__exceptions.stripped.py
    - docs/shadow/current/django_strawberry_framework__exceptions.overview.md
    - Prompt:
        - Use django_strawberry_framework/exceptions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__exceptions.stripped.py and docs/shadow/current/django_strawberry_framework__exceptions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. 1. Implemented `__reduce__` on `PathResolutionError` and `LookupValidationError` so pickle/deepcopy serialization succeeds without argument count mismatch errors. 2. Stored `self.detail` and implemented `__reduce__` on `ResourceLimitExceeded`. 3. Sanitized `str` subclasses in diagnostic label and repr helpers (`_safe_model_label`, `_safe_terminal_label`, `_safe_arg_repr`) preventing formatting detonation.
    - Verification: Passed. Evidence: Added tests in `tests/test_exceptions.py` and `tests/test_resource_policy.py` (113/113 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/exceptions/; unrelated work preserved.

- [x] django_strawberry_framework/extensions/debug.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__extensions__debug.stripped.py
    - docs/shadow/current/django_strawberry_framework__extensions__debug.overview.md
    - Prompt:
        - Use django_strawberry_framework/extensions/debug.py as the entry point. Read docs/shadow/current/django_strawberry_framework__extensions__debug.stripped.py and docs/shadow/current/django_strawberry_framework__extensions__debug.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. In `_collect_exceptions`, used `getattr(execution_result, "errors", None)` to safely handle custom/duck-typed execution results without an `errors` attribute.
    - Verification: Passed. Evidence: Hardened duck-typed result errors collection and passed full suite (76/76 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/debug_extension/; unrelated work preserved.

- [x] django_strawberry_framework/extensions/error_policy.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__extensions__error_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__extensions__error_policy.overview.md
    - Prompt:
        - Use django_strawberry_framework/extensions/error_policy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__extensions__error_policy.stripped.py and docs/shadow/current/django_strawberry_framework__extensions__error_policy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. 1. Classified arbitrary non-GraphQLError objects with `original_error is None` as unexpected so they never fail open or disclose internal error data. 2. Cast `result.errors` to a list in `mask_execution_result` before computing replacements, preventing `ValueError` and data destruction on one-shot iterators/generators. 3. Caught exceptions on raising `schema.error_policy` descriptors, falling back fail-closed to `DEFAULT_ERROR_POLICY`. 4. Added exception containment block around `on_operation` teardown to degrade to fail-closed response if context resolution fails.
    - Verification: Passed. Evidence: Added tests in `tests/test_error_policy.py` and passed full suite (72/72 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/ext_error_policy/; unrelated work preserved.

- [x] django_strawberry_framework/extensions/resource_policy.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__extensions__resource_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__extensions__resource_policy.overview.md
    - Prompt:
        - Use django_strawberry_framework/extensions/resource_policy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__extensions__resource_policy.stripped.py and docs/shadow/current/django_strawberry_framework__extensions__resource_policy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. 1. In `_charge_container`, only charged typed `GraphQLList` inputs against family limits (`max_membership_items`), preventing untyped arrays in JSON scalars from false rejections. 2. Bounded binary scalar payloads (`bytes`, `bytearray`, `memoryview`) by their byte length under `max_scalar_bytes` in `_charge_leaf`. 3. Guarded query root meta-field parent type check against `None is None` edge case in `_field_definition`. 4. Handled `variables: Mapping[str, Any] | None = None` safely in `charge_document`.
    - Verification: Passed. Evidence: Added tests in `tests/test_resource_policy.py` and passed full suite (132/132 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/ext_resource_policy/; unrelated work preserved.

- [x] django_strawberry_framework/filters/base.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__filters__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__base.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/base.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__base.stripped.py and docs/shadow/current/django_strawberry_framework__filters__base.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. 1. Reimplemented `resolve_globalid_target_definition` to iteratively walk multi-hop relation paths (`shelf__branch__id`) resolving downstream to terminal target definitions instead of stopping at the first hop. 2. Guarded standalone/unbound `IntegerInFilter.filter` against `parent` or `model_field` being `None`. 3. Enforced sequence check (`list`, `tuple`) in `validate_range` and `IntegerRangeFilter.filter` preventing raw `TypeError`/`IndexError` on non-sequence or single-element inputs. 4. Guarded `coerce_field_value_or_none` with `isinstance(field, models.Field)`. 5. Defensive attribute access in `_relation_uses_non_pk_to_field` and `_marked_pk_field_name`.
    - Verification: Passed. Evidence: Added tests in `tests/filters/test_base.py` and passed full suite (535/535 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/filters_base/; unrelated work preserved.

- [x] django_strawberry_framework/filters/factories.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__factories.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/factories.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py and docs/shadow/current/django_strawberry_framework__filters__factories.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 15 adversarial scenarios covering hostile non-mapping metadata, deep nesting recursion guards (>64 depth), equivalent container shapes deduplication (`list`, `tuple`, `set`, `frozenset`), relation cycles and diamond DAGs in BFS traversal, thread-safe dynamic FilterSet factory caching, and schema compilation.
    - Verification: Passed. Evidence: All 50 focused unit tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/filters_factories/; unrelated work preserved.

- [x] django_strawberry_framework/filters/inputs.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. 1. In `_normalize_range_value`, guarded against `strawberry.UNSET` using `not is_inactive_value(..., unset_sentinel=UNSET)` so unsupplied range axes are omitted from form patches instead of leaking `UNSET` and failing form field validation. 2. Unwrapped `Enum` members on range bounds using `_unwrap_enum_member()`.
    - Verification: Passed. Evidence: Added tests in `tests/filters/test_inputs.py` and passed full suite (537/537 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/filters_inputs/; unrelated work preserved.

- [x] django_strawberry_framework/filters/sets.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/filters/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py and docs/shadow/current/django_strawberry_framework__filters__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. In `FilterSet._normalize_input()`, resolved fallback declared suffixed filter instances (e.g. `name__exact`) by updating `form_key = suffixed_key` so that the normalized dictionary key matches the declared `FilterSet` form field rather than silently omitting the filter.
    - Verification: Passed. Evidence: Updated tests in `tests/filters/test_sets.py` and passed full suite (537/537 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/filters_sets/; unrelated work preserved.

- [x] django_strawberry_framework/forms/converter.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__forms__converter.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__converter.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/converter.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__converter.stripped.py and docs/shadow/current/django_strawberry_framework__forms__converter.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 25+ standard Django form field types, MRO inheritance precedence, precheck dispatches (ModelChoiceField, ModelMultipleChoiceField, FileField, MultipleChoiceField), exact type guards, hostile metaclasses, requiredness/NullBooleanField rules, DurationField model/model-less boundaries, and mutation schema execution.
    - Verification: Passed. Evidence: All 231 unit and integration tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/forms_converter/; unrelated work preserved.

- [x] django_strawberry_framework/forms/inputs.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__forms__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__forms__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. 1. In `_model_column_for`, guarded against non-concrete virtual fields (`GenericForeignKey`, `GenericRelation`) and reverse relations by strictly checking `is_forward_concrete_relation(column)` or `is_forward_many_to_many(column)` or concrete DB columns (`column.column is not None`), preventing schema crash on missing related models and misclassification of extra form fields as relation IDs. 2. Promoted `is_forward_concrete_relation` to `django_strawberry_framework/utils/relations.py`.
    - Verification: Passed. Evidence: Added tests in `tests/forms/test_inputs.py` and `tests/utils/test_relations.py` and passed full suite (317/317 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/forms_inputs/; unrelated work preserved.

- [x] django_strawberry_framework/forms/resolvers.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__forms__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__forms__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. 1. In `_reconstruct_partial_data`, guarded the single `ModelChoiceField` reconstruction branch with `and name in fk_field_names`, preventing extra form fields or reverse relations from crashing with `AttributeError: serializable_value`. 2. Caught `ObjectDoesNotExist` during relation reconstruction so dangling foreign keys do not escape as unhandled 500 errors. 3. Protected `_to_form_key_value` with `FieldDoesNotExist` fallback and `_is_empty_form_value` against unhashable candidate values.
    - Verification: Passed. Evidence: Added tests in `tests/forms/test_resolvers.py` and passed full suite (199/199 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/forms_resolvers/; unrelated work preserved.

- [x] django_strawberry_framework/forms/sets.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__forms__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__forms__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/forms/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__forms__sets.stripped.py and docs/shadow/current/django_strawberry_framework__forms__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. 1. In `mutations/sets.py::reject_unknown_meta_keys`, guarded against non-class `Meta` definitions by raising typed `ConfigurationError` rather than escaping raw `TypeError` on `vars(meta)`. 2. In `mutations/sets.py::require_non_delete_operation` and `DjangoMutation._validate_meta`, added `isinstance(operation, str)` type gates before set membership evaluation preventing unhashable `Meta.operation` inputs from crashing with raw `TypeError`. 3. In `forms/resolvers.py::_decode_form_data`, safely accessed form fields via `form_fields.get(spec.target_name)`.
    - Verification: Passed. Evidence: Added tests in `tests/forms/test_sets.py` and `tests/mutations/test_sets.py` and passed full suite (373/373 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/forms_sets/; unrelated work preserved.

- [x] django_strawberry_framework/keyset.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__keyset.stripped.py
    - docs/shadow/current/django_strawberry_framework__keyset.overview.md
    - Prompt:
        - Use django_strawberry_framework/keyset.py as the entry point. Read docs/shadow/current/django_strawberry_framework__keyset.stripped.py and docs/shadow/current/django_strawberry_framework__keyset.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. In `_decrypt_cursor_payload`, used `getattr(settings, "SECRET_KEY_FALLBACKS", ())` to guard against configurations where Django's `SECRET_KEY_FALLBACKS` setting is not defined.
    - Verification: Passed. Evidence: Added tests and verified all 163 unit and integration tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/keyset/; unrelated work preserved.

- [x] django_strawberry_framework/list_field.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__list_field.stripped.py
    - docs/shadow/current/django_strawberry_framework__list_field.overview.md
    - Prompt:
        - Use django_strawberry_framework/list_field.py as the entry point. Read docs/shadow/current/django_strawberry_framework__list_field.stripped.py and docs/shadow/current/django_strawberry_framework__list_field.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. In `resource_policy.py::bounded_rows`, preserved `None` returns for nullable list field custom sync/async resolvers instead of falling through to `islice(None, limit)` and raising unhandled `TypeError: 'NoneType' object is not iterable`.
    - Verification: Passed. Evidence: Added tests in `tests/test_list_field.py` and `tests/test_resource_policy.py` and passed full suite (145/145 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/list_field/; unrelated work preserved.

- [x] django_strawberry_framework/management/commands/_imports.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__management__commands___imports.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands___imports.overview.md
    - Prompt:
        - Use django_strawberry_framework/management/commands/_imports.py as the entry point. Read docs/shadow/current/django_strawberry_framework__management__commands___imports.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands___imports.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 41 adversarial tests covering relative/empty module paths, invalid schema selectors (`module:symbol`), nested dotted attribute traversal, translation of `ImportError`/`AttributeError` to `CommandError`, and preservation of unrelated exception tracebacks.
    - Verification: Passed. Evidence: All 76 management command tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/management_commands_imports/; unrelated work preserved.

- [x] django_strawberry_framework/management/commands/export_schema.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__management__commands__export_schema.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands__export_schema.overview.md
    - Prompt:
        - Use django_strawberry_framework/management/commands/export_schema.py as the entry point. Read docs/shadow/current/django_strawberry_framework__management__commands__export_schema.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands__export_schema.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 55 adversarial tests covering non-schema symbol rejections, hostile filesystem writes (non-existent directories, permissions, directory targets, broken symlinks), CLI `--path` validations, schema finalization lifecycle, and full live schema exports.
    - Verification: Passed. Evidence: All 55 scratch and existing management command tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/management_commands_export_schema/; unrelated work preserved.

- [x] django_strawberry_framework/management/commands/inspect_django_type.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.overview.md
    - Prompt:
        - Use django_strawberry_framework/management/commands/inspect_django_type.py as the entry point. Read docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 32 adversarial tests covering non-DjangoType targets, dotted path and bare name resolution, unfinalized/abstract types, scalar matrix + MRO traversal, choice enums, forward/reverse FK, M2M, O2O, GenericRelation, connection-only relation shapes, Relay primary key GlobalID overrides, and `--schema` options with custom name converters.
    - Verification: Passed. Evidence: All 72 unit, integration, and command tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/management_commands_inspect_django_type/; unrelated work preserved.

- [x] django_strawberry_framework/middleware/debug_toolbar.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.stripped.py
    - docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.overview.md
    - Prompt:
        - Use django_strawberry_framework/middleware/debug_toolbar.py as the entry point. Read docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.stripped.py and docs/shadow/current/django_strawberry_framework__middleware__debug_toolbar.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 23 adversarial tests covering GraphQL batch requests, streaming/file responses, non-dict payloads, null/empty operation names, dynamic panel callables, Unicode/lazy translation strings, unknown charsets, mock/hostile views, and async request lifecycle with `AsyncGraphQLView`.
    - Verification: Passed. Evidence: All 51 scratch and existing middleware/integration tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/middleware_debug_toolbar/; unrelated work preserved.

- [x] django_strawberry_framework/middleware/request_body.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__middleware__request_body.stripped.py
    - docs/shadow/current/django_strawberry_framework__middleware__request_body.overview.md
    - Prompt:
        - Use django_strawberry_framework/middleware/request_body.py as the entry point. Read docs/shadow/current/django_strawberry_framework__middleware__request_body.stripped.py and docs/shadow/current/django_strawberry_framework__middleware__request_body.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 26 adversarial tests covering seekable ASGI streams (`SpooledTemporaryFile`), non-seekable WSGI streams (`LimitedStream`), socket disconnect / I/O errors (`UnreadablePostError`), stream position restore corruptions, ContextVar scoping under high async concurrency (20 simultaneous requests), nested re-entrant middleware chains, and CSRF ordering validation.
    - Verification: Passed. Evidence: All 26 scratch and existing middleware tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/middleware_request_body/; unrelated work preserved.

- [x] django_strawberry_framework/mutations/fields.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__mutations__fields.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__fields.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/fields.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__fields.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__fields.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across multiple adversarial suites covering non-type targets, property/repr exceptions, incomplete protocol implementations, unfinalized/cleared registry states, empty/null/unset inputs, signature synthesis with `build_lazy_field_signature`, multi-flavor target generalization (Model, ModelForm, Plain Form, DRF Serializer, Auth mutations), and transaction boundary markers.
    - Verification: Passed. Evidence: All mutation field unit, integration, and scratch tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/mutations_fields/; unrelated work preserved.

- [x] django_strawberry_framework/mutations/inputs.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__mutations__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. In `mutations/inputs.py::editable_input_fields`, enforced `getattr(field, "editable", False)` on forward `ManyToManyField` branches, preventing `editable=False` M2M relations from being erroneously included in mutation input types or bypassing non-editable field validation.
    - Verification: Passed. Evidence: Added `test_editable_fields_excludes_non_editable_many_to_many` in `tests/mutations/test_inputs.py` and passed full suite (317/317 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/mutations_inputs/; unrelated work preserved.

- [x] django_strawberry_framework/mutations/permissions.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__mutations__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__permissions.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/permissions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__permissions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 43 adversarial tests covering strict boolean return enforcement (`isinstance(r, bool)`), coroutine/future disposal in sync context (`SyncMisuseError`), missing context/request, anonymous user fail-closed behavior, `ChannelsRequestAdapter` ASGI scopes, hostile permission class iterators, short-circuit evaluation, and permission timing relative to row visibility.
    - Verification: Passed. Evidence: All 129 existing and 43 scratch tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/mutations_permissions/; unrelated work preserved.

- [x] django_strawberry_framework/mutations/resolvers.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__mutations__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) In `mutations/resolvers.py::_model_write_step`, handled safe tuple unpacking (`target, m2m_assignments, exclude = decoded[:3]`) so mutations with `EXCLUDED` specs don't crash with `ValueError: too many values to unpack`. (2) In `_assign_m2m`, contained `IntegrityError` to return `integrity_error_field_errors()`. (3) In `_delete_or_field_errors`, caught `IntegrityError` to return `integrity_error_field_errors()`. (4) In `run_write_pipeline_sync`, added immediate pre-write PK drift backstop via `reject_substituted_row`.
    - Verification: Passed. Evidence: Added tests in `tests/mutations/test_resolvers.py` (75/75 passed) and verified full query test suite (653/653 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/mutations_resolvers/; unrelated work preserved.

- [x] django_strawberry_framework/mutations/sets.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__mutations__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/mutations/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__mutations__sets.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. Hardened `Meta` validation and error message formatting against hostile descriptors, non-string keys, and broken `__repr__` implementations across `require_model_class`, `validate_select_for_update`, `_validate_input_class`, `_validate_permission_classes`, `reject_unknown_meta_keys`, and `DjangoMutation._validate_meta`.
    - Verification: Passed. Evidence: Added regression tests in `tests/mutations/test_sets.py` (101/101 passed) and across all mutation suites (952/952 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/mutations_sets/; unrelated work preserved.

- [x] django_strawberry_framework/optimizer/_context.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__optimizer___context.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer___context.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/_context.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer___context.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer___context.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) Completed `__all__` public export surface with `begin_scoped_relations`, `begin_strictness`, `end_scoped_relations`, and `end_strictness`. (2) Unified fail-closed behavior in `publish_scoped_relations` and `relation_is_optimizer_scoped` on falsy/unhashable arguments.
    - Verification: Passed. Evidence: Added tests in `tests/optimizer/test_extension.py` (166/166 passed) and verified related resolver suites (43/43 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/optimizer_context/; unrelated work preserved.

- [x] django_strawberry_framework/optimizer/extension.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__optimizer__extension.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__extension.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/extension.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__extension.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__extension.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 5 deep scratch suites covering hostile container freezing / variable hashing, cyclic and deeply nested (60+ level) fragment trees, schema reachability audits across unions and interface implementations, `@skip`/`@include` variable evaluation, LRU batch eviction under heavy churn, and async execution concurrency isolation across 8 ContextVars.
    - Verification: Passed. Evidence: All 798 tests in `tests/optimizer/` and 13 scratch tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/optimizer_extension/; unrelated work preserved.

- [x] django_strawberry_framework/optimizer/field_meta.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__optimizer__field_meta.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__field_meta.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/field_meta.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__field_meta.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__field_meta.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) Hardened `_target_pk_name` against unmanaged models, missing/invalid `pk.name` attributes, and hostile descriptors. (2) Routed all relation attribute reads in `FieldMeta._from_field_shape` through `utils.relations` helpers. (3) Added string validation for `field_name` in `from_django_field`.
    - Verification: Passed. Evidence: Added tests in `tests/optimizer/test_field_meta.py` (27/27 passed) and verified full optimizer test suite (803/803 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/optimizer_field_meta/; unrelated work preserved.

- [x] django_strawberry_framework/optimizer/hints.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__optimizer__hints.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__hints.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/hints.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__hints.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__hints.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) Disallowed strategy classes in `nested_fetch.py::resolve_strategy` (`not isinstance(value, type)`) to prevent query-time `TypeError: WindowedPrefetchStrategy.plan() missing 1 required positional argument: 'plan'`. (2) Formatted strategy error messages using `_safe_type_name` to prevent metaclass crashes and uninformative type names.
    - Verification: Passed. Evidence: Added tests in `tests/optimizer/test_hints.py` and `tests/optimizer/test_nested_fetch.py` (56/56 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/optimizer_hints/; unrelated work preserved.

- [x] django_strawberry_framework/optimizer/join_taxonomy.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__optimizer__join_taxonomy.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__join_taxonomy.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/join_taxonomy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__join_taxonomy.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__join_taxonomy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 3 adversarial suites covering arbitrary non-relation objects, synthetic descriptors with failing properties, circular descriptors, hostile truthiness in boolean wrappers (`_safe_getattr`, `_safe_truthy`, `_safe_flag`), MTI parent links, symmetric/asymmetric self-referential relations, custom `through` models with explicit FKs, custom `to_field` targets, `GenericRelation`, and `ForeignObject`.
    - Verification: Passed. Evidence: All 397 tests across optimizer join taxonomy, plans, and walker passed cleanly.
    - Cleanup: Removed docs/bug_hunt/temp-tests/optimizer_join_taxonomy/; unrelated work preserved.

- [x] django_strawberry_framework/optimizer/lateral_fetch.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__optimizer__lateral_fetch.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__lateral_fetch.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/lateral_fetch.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__lateral_fetch.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__lateral_fetch.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) Hardened `_build_lateral_spec` to verify `join.lateral_shape is LateralJoinShape.DIRECT_FK` before constructing `DIRECT_FK` specs, failing closed and returning `None` (downgrading to windowed prefetch) on unsupported shapes instead of silently misclassifying. (2) Verified multi-column keyset seek recognition and parameter bindings.
    - Verification: Passed. Evidence: Added regression tests in `tests/optimizer/test_lateral_fetch.py` (90/90 passed) and full optimizer test suite (808/808 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/optimizer_lateral_fetch/; unrelated work preserved.

- [x] django_strawberry_framework/optimizer/nested_fetch.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_fetch.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_fetch.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/nested_fetch.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__nested_fetch.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__nested_fetch.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 5 adversarial scratch suites covering classifier safety on non-queryset and modified querysets (distinct, combinator, sliced, select_for_update), `RecognizedFetchQuerySet` rebinding, cloning, pickling, deepcopy, and fallback to `super()._fetch_all()`, `NestedConnectionRequest` immutability and contract guards, prefetch attachment deduplication, and strategy resolution with ContextVar isolation.
    - Verification: Passed. Evidence: All 808 optimizer tests in `tests/optimizer/` and scratch probes passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/optimizer_nested_fetch/; unrelated work preserved.

- [x] django_strawberry_framework/optimizer/nested_planner.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_planner.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__nested_planner.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/nested_planner.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__nested_planner.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__nested_planner.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 3 adversarial suites (34 tests) covering nested connection planning pipeline, union merge conflict detection, scalar-only window projection, divergent key window partitioning (`planned`, `malformed`, `fallbacks`), keyset/offset slicing boundaries and codec validation, and B-tree index advisory analysis with backend support fallback.
    - Verification: Passed. Evidence: All 128 tests in focused connection/nested optimizer suites and 34 scratch tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/optimizer_nested_planner/; unrelated work preserved.

- [x] django_strawberry_framework/optimizer/plans.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__optimizer__plans.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__plans.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/plans.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__plans.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__plans.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) Guarded `_flatten_select_related` on non-dict input shapes (`not isinstance(sr, dict)`). (2) Supported bare Django `F` expressions in `order_entry_name_and_direction`. (3) Synchronized `select_path_resolver_keys` when dropping unsupported paths in `prune_unsupportable_select_related`.
    - Verification: Passed. Evidence: Added regression tests in `tests/optimizer/test_plans.py` (117/117 passed) and full optimizer test suite (811/811 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/optimizer_plans/; unrelated work preserved.

- [x] django_strawberry_framework/optimizer/predicates.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__optimizer__predicates.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__predicates.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/predicates.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__predicates.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__predicates.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 4 adversarial scratch suites (36 tests) covering `correlated_inner_root` manager bypassing, custom/composite PK resolution, `_effective_alias_names` namespace collision protection across annotations/aliases/extra/values, `_next_reserved_alias` counter advancing, `attach_exists` runtime guards (same-model, same-db, combinator guard), and non-destructive cloning.
    - Verification: Passed. Evidence: All 302 tests in `tests/optimizer/test_predicates.py` and `tests/filters/test_sets.py` passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/optimizer_predicates/; unrelated work preserved.

- [x] django_strawberry_framework/optimizer/selections.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/selections.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__selections.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__selections.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 2 adversarial scratch suites (24 tests) covering anonymous & nested inline fragments without type conditions, fragment cycle depth tracking, `@skip`/`@include` directive evaluation with boolean / variable / None values, Relay connection node children traversal with multiple aliased edges/nodes under runtime prefix tags, connection field naming conversions, and connection observability predicates.
    - Verification: Passed. Evidence: All 25 tests in `tests/optimizer/test_selections.py` and 24 scratch tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/optimizer_selections/; unrelated work preserved.

- [x] django_strawberry_framework/optimizer/single_parent_fetch.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__optimizer__single_parent_fetch.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__single_parent_fetch.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/single_parent_fetch.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__single_parent_fetch.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__single_parent_fetch.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 3 adversarial scratch suites (20 tests) covering single-parent fast-path spec fail-closed gates, WHERE clause parsing in `_single_parent_where_ids` across complex trees and unhashable/scalar values, parent ID deduplication, execution lifecycle with sentinel row overfetching (`next_page_probe=True`), and graceful fallback under query tampering, annotation injection, or custom managers.
    - Verification: Passed. Evidence: All 48 tests across `tests/optimizer/test_single_parent_fetch.py` and `examples/fakeshop/test_query/test_single_parent_fastpath_api.py` and 20 scratch tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/optimizer_single_parent_fetch/; unrelated work preserved.

- [x] django_strawberry_framework/optimizer/walker.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__optimizer__walker.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__walker.overview.md
    - Prompt:
        - Use django_strawberry_framework/optimizer/walker.py as the entry point. Read docs/shadow/current/django_strawberry_framework__optimizer__walker.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__walker.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 23 adversarial scratch tests covering selection tree descent with duck-types/unregistered models, argument normalization and operation gates (`_enable_only_for_operation`), lossy digit boundary GraphQL name conversions, deeply nested/cyclical relation graphs (up to 20 levels), optimizer hint validation and `get_queryset` downgrade to Prefetch, and FK-ID elisions.
    - Verification: Passed. Evidence: All 811 tests in `tests/optimizer/` and 23 scratch tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/optimizer_walker/; unrelated work preserved.

- [x] django_strawberry_framework/orders/base.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__orders__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__base.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/base.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__base.stripped.py and docs/shadow/current/django_strawberry_framework__orders__base.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 2 hostile scratch test suites (34 tests) covering `RelatedOrder` targets (callables, string lookups, dynamic overrides, invalid types), `OrderSet.Meta.fields` non-string sequences, empty containers, `order_input_type` input validation, explicit null vs unset semantics across nested branches, multi-hop lookup paths, hostile iterators, inheritance / MRO precedence and tombstones, and all 6 `Ordering` directions on scalar and to-many paths.
    - Verification: Passed. Evidence: All 149 tests in `tests/orders/` and 34 scratch tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/orders_base/; unrelated work preserved.

- [x] django_strawberry_framework/orders/factories.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__orders__factories.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__factories.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/factories.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__factories.stripped.py and docs/shadow/current/django_strawberry_framework__orders__factories.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 2 adversarial scratch suites (31 tests) covering `OrderArgumentsFactory` subclassing rejection, `get_orderset_class` model validation, container canonicalization onto shared cache slots, kwarg stripping (`_RESERVED_FACTORY_KEYS`), complex graph topologies (deep linear chains, diamond DAGs, self/mutual cyclic dependencies), empty OrderSet containment, and collision detection across flattened/camelCase lookups.
    - Verification: Passed. Evidence: All 149 tests in `tests/orders/` and 31 scratch tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/orders_factories/; unrelated work preserved.

- [x] django_strawberry_framework/orders/inputs.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__orders__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__orders__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) Configured `unset_sentinel=strawberry.UNSET` in `normalize_input_value` and `OrderSet._permission` to ignore unsupplied/UNSET fields during traversal instead of evaluating them as active and passing UNSET direction tuples to downstream resolvers. (2) Updated `_ensure_field_specs` to build field specs for all `OrderSet` subclasses regardless of whether `Meta.model` is declared. (3) Added validation raising `ConfigurationError` when non-`Ordering` directions are passed to `normalize_input_value` and `_resolve_order_expressions`.
    - Verification: Passed. Evidence: Added regression tests in `tests/orders/test_inputs.py` and `tests/orders/test_sets.py` (154/154 passed in `tests/orders/`).
    - Cleanup: Removed docs/bug_hunt/temp-tests/orders_inputs/; unrelated work preserved.

- [x] django_strawberry_framework/orders/sets.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__orders__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/orders/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__orders__sets.stripped.py and docs/shadow/current/django_strawberry_framework__orders__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) Replaced `model.__name__` with `_safe_type_name(model)` across `_expand_meta_fields` and `_resolve_order_expressions` to prevent unhandled `AttributeError` when `Meta.model` is not a class or lacks `__name__`. (2) In `_expand_meta_fields`, validated that `Meta.fields` is not a bare non-`"__all__"` string or non-iterable type, raising typed `ConfigurationError`. (3) In `_get_concrete_field_names_for_order` in `orders/inputs.py`, validated that `model` has a callable `_meta.get_fields` before reading fields.
    - Verification: Passed. Evidence: Added regression tests in `tests/orders/test_sets.py` (158/158 passed in `tests/orders/`).
    - Cleanup: Removed docs/bug_hunt/temp-tests/orders_sets/; unrelated work preserved.

- [x] django_strawberry_framework/permissions.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__permissions.overview.md
    - Prompt:
        - Use django_strawberry_framework/permissions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__permissions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 21 adversarial scratch tests covering `fields` input validation (rejecting non-iterables, bare strings, bytes, unhashable items), root queryset/model validations, explicit null vs empty container semantics (`fields=None` vs `fields=[]`), custom PK / `to_field` / `OneToOne` / MTI relation traversal, 3-node cycle detection with complete cycle path reporting, acyclic DAG diamond traversals, and sync/async multi-DB isolation across concurrent async tasks.
    - Verification: Passed. Evidence: All tests in `tests/test_permissions.py` and 21 scratch tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/permissions/; unrelated work preserved.

- [x] django_strawberry_framework/registry.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__registry.stripped.py
    - docs/shadow/current/django_strawberry_framework__registry.overview.md
    - Prompt:
        - Use django_strawberry_framework/registry.py as the entry point. Read docs/shadow/current/django_strawberry_framework__registry.stripped.py and docs/shadow/current/django_strawberry_framework__registry.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 2 adversarial scratch suites (17 tests) covering `discard_pending` generator handling, `register_subsystem_clear` and `register_type_teardown` type validation, safe lookup defaults on unhashable/None keys, `primary_for` vs `get` semantics across 0/1/2+ types with primary flip protections, `GLOBALID_SETTING_UNSET` sentinel lifecycle, concurrent multithreaded reader safety, proxy and unmanaged model mapping, LIFO teardown callback execution with retry recovery, and Relay node definition lookups with duplicate detection.
    - Verification: Passed. Evidence: All 80 tests in `tests/test_registry.py` and 17 scratch tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/registry/; unrelated work preserved.

- [x] django_strawberry_framework/relay.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__relay.stripped.py
    - docs/shadow/current/django_strawberry_framework__relay.overview.md
    - Prompt:
        - Use django_strawberry_framework/relay.py as the entry point. Read docs/shadow/current/django_strawberry_framework__relay.stripped.py and docs/shadow/current/django_strawberry_framework__relay.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 2 adversarial scratch suites (48 tests) covering `GlobalID` container/shape mismatches (malformed base64, missing delimiters, invalid UTF-8, null bytes, emojis), encoding strategies (`type`, `model`, `type+model`, custom), PK coercion & custom `relay.NodeID[str]` attributes over non-pk columns, heterogeneous multi-type batching in `DjangoNodesField`, permission/type visibility nullification without existence leaks, and typed `ConfigurationError` definition-time guards.
    - Verification: Passed. Evidence: All 291 tests in Relay test suites and 48 scratch tests passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/relay/; unrelated work preserved.

- [x] django_strawberry_framework/resource_policy.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__resource_policy.stripped.py
    - docs/shadow/current/django_strawberry_framework__resource_policy.overview.md
    - Prompt:
        - Use django_strawberry_framework/resource_policy.py as the entry point. Read docs/shadow/current/django_strawberry_framework__resource_policy.stripped.py and docs/shadow/current/django_strawberry_framework__resource_policy.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 287 adversarial scratch test cases covering `ResourcePolicy` field validations, `narrowed` immutability and widening rejection, empty/comment-only query scanning, cyclic fragments and self-referential value containers (`_closes_a_cycle`), multiplicative collection costs across nested connections and raw lists, directive evasion guards, upload size and scalar byte bounds, context threading, and deadline enforcement.
    - Verification: Passed. Evidence: All 421 tests in `tests/test_resource_policy.py`, `examples/fakeshop/test_query/test_resource_policy_api.py`, and 287 scratch probes passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/resource_policy/; unrelated work preserved.

- [x] django_strawberry_framework/rest_framework/hook_context.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__rest_framework__hook_context.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__hook_context.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/hook_context.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__hook_context.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__hook_context.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) Wrapped `item.name` and `item.content_type` attribute evaluation in `_upload_metadata` with `try...except Exception:` blocks to prevent property descriptors raising non-`AttributeError` exceptions (e.g., `RuntimeError`, `OSError`) from crashing mutation pipelines. (2) In `_merged_serializer_kwargs`, validated that any non-None `context` returned from `get_serializer_kwargs` is a `Mapping` and guarded `dict(raw_context)` materialization to raise `ConfigurationError` rather than leaking raw `TypeError`/`ValueError` into GraphQL.
    - Verification: Passed. Evidence: Added regression tests in `tests/rest_framework/test_resolvers.py` (155/155 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/rest_framework_hook_context/; unrelated work preserved.

- [x] django_strawberry_framework/rest_framework/inputs.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__rest_framework__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) In `build_serializer_inputs`, normalized `optional_fields` via `normalize_field_name_sequence` before building `create` and `partial` input shapes so one-shot iterators/generators are not exhausted on the first pass. (2) In `_resolve_nested_field` (`inputs.py`) and `_assert_schema_source_ownership` (`sets.py`), wrapped child serializer `.fields` evaluation in `try...except Exception as exc:` raising typed `ConfigurationError`. (3) In `normalize_nested_serializer_configs` and `_validate_nested_config_keys`, added strict `isinstance(nested_configs, Mapping)` and `isinstance(config, NestedSerializerConfig)` guards raising `ConfigurationError`. (4) In `resolve_injected_field_specs`, added `name not in field_map` guard raising `ConfigurationError`.
    - Verification: Passed. Evidence: Added regression tests in `tests/rest_framework/test_inputs.py` (86/86 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/rest_framework_inputs/; unrelated work preserved.

- [x] django_strawberry_framework/rest_framework/resolvers.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) In `utils/errors.py::_str_list`, scalar non-string values (int, float, bool) are safely stringified via `_safe_text` rather than calling `list(value)` which raised `TypeError` and yielded `<unprintable>`. (2) In `_decode_nested` and `_decode_input_object`, `None` list items are directly preserved as `None` for DRF `allow_null` validation and non-dataclass inputs return field errors instead of crashing with `AttributeError` on `__strawberry_definition__`. (3) In `serializer_errors_to_field_errors` and `_error_leaf`, guaranteed that empty error dicts/lists or empty messages produce a non-empty `FieldError` envelope with fallback `"Validation failed without error details."`. (4) In `_attest_saved_relations`, skipped non-concrete reverse relation descriptors lacking `attname` (`ManyToOneRel`, etc.) to prevent `AttributeError`.
    - Verification: Passed. Evidence: Added regression tests in `tests/utils/test_errors.py` and `tests/rest_framework/test_resolvers.py` (172/172 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/rest_framework_resolvers/; unrelated work preserved.

- [x] django_strawberry_framework/rest_framework/serializer_converter.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__rest_framework__serializer_converter.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__serializer_converter.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/serializer_converter.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__serializer_converter.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__serializer_converter.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) In `_reject_unsupported_relation_field`, rejected all non-relation serializer fields mapped over relation columns that are not `PrimaryKeyRelatedField` (or `ManyRelatedField` wrapping `PrimaryKeyRelatedField`), raising `ConfigurationError`. (2) In `_model_backed_scalar_annotation`, validated consumer-declared scalar fields over choice columns against `scalar_for_field(column)` so disagreeing scalar types raise `ConfigurationError` rather than silently emitting the model choice enum. (3) In `_list_child_conversion`, added validation for untyped `ListField()` (where child is `None` or `_UnvalidatedField`), raising a clear `ConfigurationError`. (4) In `_unsupported_serializer_field`, safely retrieved field names using try/except fallback.
    - Verification: Passed. Evidence: Added regression tests in `tests/rest_framework/test_converter.py` (87/87 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/rest_framework_serializer_converter/; unrelated work preserved.

- [x] django_strawberry_framework/rest_framework/sets.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__rest_framework__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__rest_framework__sets.overview.md
    - Prompt:
        - Use django_strawberry_framework/rest_framework/sets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__rest_framework__sets.stripped.py and docs/shadow/current/django_strawberry_framework__rest_framework__sets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) In `_assert_schema_source_ownership`, validated multi-level deeper `NestedSerializerConfig.nested_fields` keys with `validate_nested_config_keys` so non-existent fields and scalar non-nested fields raise typed `ConfigurationError` instead of crashing with raw `KeyError` or misleading `.fields` unreadable errors. (2) Guarded `_assert_schema_source_ownership` against unbounded recursion on self-referential or mutual nested serializer cycles using `guard_nested_recursion` with `nested_path=(*nested_path, child_class)`.
    - Verification: Passed. Evidence: Added regression tests in `tests/rest_framework/test_sets.py` (83/83 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/rest_framework_sets/; unrelated work preserved.

- [x] django_strawberry_framework/routers.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__routers.stripped.py
    - docs/shadow/current/django_strawberry_framework__routers.overview.md
    - Prompt:
        - Use django_strawberry_framework/routers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__routers.stripped.py and docs/shadow/current/django_strawberry_framework__routers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 15 adversarial scratch test cases covering websocket pattern validations, malformed regex patterns, invalid ASGI applications, websocket consumer candidate shapes and factories, async factory handling, revalidation window edge cases, and 20-thread concurrency safety during dynamic class creation.
    - Verification: Passed. Evidence: All 166 tests in `tests/test_routers.py` and 15 scratch probes passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/routers/; unrelated work preserved.

- [x] django_strawberry_framework/scalars.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__scalars.stripped.py
    - docs/shadow/current/django_strawberry_framework__scalars.overview.md
    - Prompt:
        - Use django_strawberry_framework/scalars.py as the entry point. Read docs/shadow/current/django_strawberry_framework__scalars.stripped.py and docs/shadow/current/django_strawberry_framework__scalars.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 25 adversarial scratch test cases covering BigInt parsing/serialization with hostile subclasses, 64-bit integer min/max boundaries, regex validation of signed/unsigned decimal strings, `strawberry_config()` custom scalar map collisions, and integration with types/converters, filters, keyset cursor pagination, and live GraphQL HTTP queries.
    - Verification: Passed. Evidence: All 82 tests in `tests/test_scalars.py`, `examples/fakeshop/test_query/test_scalars_api.py`, and 25 scratch probes passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/scalars/; unrelated work preserved.

- [x] django_strawberry_framework/schema.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__schema.stripped.py
    - docs/shadow/current/django_strawberry_framework__schema.overview.md
    - Prompt:
        - Use django_strawberry_framework/schema.py as the entry point. Read docs/shadow/current/django_strawberry_framework__schema.stripped.py and docs/shadow/current/django_strawberry_framework__schema.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) In `DjangoMutationExecutionContext._marked_mutation_class`, guarded against `parent_type is None` when `schema.mutation_type is None` (where `None is not None` evaluated to False, crashing with `AttributeError`), guarded against empty `field_nodes` or missing `.name.value`, and safely extracted `parent_type.fields`. (2) In `execute_field`, safely retrieved model from `getattr(getattr(mutation_cls, "_mutation_meta", None), "model", None)` so custom marked mutation classes without `_mutation_meta` fall back to the default write alias instead of raising `AttributeError`. (3) In `DjangoSchema.__init__`, handled explicit `execution_context_class=None`. (4) In `_extension_entry_matches`, wrapped `issubclass` checks in `try...except Exception: return False` against hostile extension classes.
    - Verification: Passed. Evidence: Added regression tests in `tests/test_schema.py` (14/14 passed) and verified 206 tests in connected write transaction, error policy, and resource policy suites.
    - Cleanup: Removed docs/bug_hunt/temp-tests/schema/; unrelated work preserved.

- [x] django_strawberry_framework/sets_mixins.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__sets_mixins.stripped.py
    - docs/shadow/current/django_strawberry_framework__sets_mixins.overview.md
    - Prompt:
        - Use django_strawberry_framework/sets_mixins.py as the entry point. Read docs/shadow/current/django_strawberry_framework__sets_mixins.stripped.py and docs/shadow/current/django_strawberry_framework__sets_mixins.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. Added `should_cache_expansion` to `__all__` to guarantee complete public export totality.
    - Verification: Passed. Evidence: Added regression tests in `tests/test_sets_mixins.py` (7/7 passed) and verified 289 tests in `tests/filters/test_sets.py`.
    - Cleanup: Removed docs/bug_hunt/temp-tests/sets_mixins/; unrelated work preserved.

- [x] django_strawberry_framework/testing/_wrap.py
    - Status: no-bugs
    - Baseline shadow: none (path excluded from the snapshot by its 'test' path filter, not new)
    - Prompt:
        - Use django_strawberry_framework/testing/_wrap.py as the entry point. No baseline shadow exists; hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 27 adversarial scratch test cases covering hostile callable wrappers, raising `__repr__`/`__str__` dunders, non-callable inputs, synthetic connection wrappers, Django Trac #37064 `_DatabaseFailure` protection and unwrap semantics, multithreaded wrap safety, and end-to-end teardown lifecycle.
    - Verification: Passed. Evidence: All 28 tests in `tests/testing/test_wrap.py`, `tests/test_django_patches.py`, and 27 scratch probes passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/testing_wrap/; unrelated work preserved.

- [x] django_strawberry_framework/testing/client.py
    - Status: no-bugs
    - Baseline shadow: none (path excluded from the snapshot by its 'test' path filter, not new)
    - Prompt:
        - Use django_strawberry_framework/testing/client.py as the entry point. No baseline shadow exists; hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 30 adversarial scratch test cases covering variable mappings and path placeholders, multipart file upload mapping with index parsing and envelope collision protection, response status decoding and transport error containment, `assert_no_errors`/`assert_errors` diagnostics, `login()` authentication context teardown safety via `finally`, and endpoint precedence ladder.
    - Verification: Passed. Evidence: All 51 tests in `tests/testing/` and `examples/fakeshop/test_query/test_client_api.py` plus 30 scratch probes passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/testing_client/; unrelated work preserved.

- [x] django_strawberry_framework/testing/relay.py
    - Status: no-bugs
    - Baseline shadow: none (path excluded from the snapshot by its 'test' path filter, not new)
    - Prompt:
        - Use django_strawberry_framework/testing/relay.py as the entry point. No baseline shadow exists; hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 31 adversarial scratch test cases covering `global_id_for` and `decode_global_id` validation of non-type and unfinalized types, non-string/non-int IDs, delimiter variations, malformed base64 strings, multi-colon payloads, strategy routing across type/model/type+model/callable/custom, and integration with `decode_model_global_id`.
    - Verification: Passed. Evidence: All 13 tests in `tests/testing/test_relay.py` and 31 scratch probes passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/testing_relay/; unrelated work preserved.

- [x] django_strawberry_framework/types/base.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__types__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__base.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/base.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__base.stripped.py and docs/shadow/current/django_strawberry_framework__types__base.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) In `_detect_custom_get_queryset`, guarded against non-type/non-DjangoType inputs to prevent `AttributeError` on missing `__mro__` and return `False` for unrelated classes. (2) In `_meta_optimizer_hints` and `_validate_optimizer_hints`, added key type validation requiring string field names to prevent unhandled `TypeError` during `sorted(...)` over mixed key types. (3) In `_is_relay_shaped`, guarded `issubclass` checks with `isinstance(..., type)`.
    - Verification: Passed. Evidence: Added regression tests in `tests/types/test_base.py` (162/162 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/types_base/; unrelated work preserved.

- [x] django_strawberry_framework/types/converters.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__types__converters.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__converters.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/converters.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__converters.stripped.py and docs/shadow/current/django_strawberry_framework__types__converters.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 14 adversarial scratch test cases covering model field scalar conversions, choice enum identifier sanitization (numbers, booleans, keywords, symbols, collision detection), tri-state `force_nullable` overrides on scalars, file/image outputs, choice enums, postgres array fields, and hostile field descriptor exception containment.
    - Verification: Passed. Evidence: All 76 tests in `tests/types/test_converters.py` and 14 scratch probes passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/types_converters/; unrelated work preserved.

- [x] django_strawberry_framework/types/definition.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__types__definition.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__definition.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/definition.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__definition.stripped.py and docs/shadow/current/django_strawberry_framework__types__definition.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) Added `compare=False` to `DjangoTypeDefinition._related_target_cache` and `_custom_id_resolver_cache` so lazy per-instance memoization caches do not break dataclass equality comparison (`d1 == d2`) or cause cyclic traversal during equality checks. (2) In `_normalize_pk_name`, returned `None` when given an empty string `""` to prevent invalid `resolve_` lookups across MRO and memo cache pollution.
    - Verification: Passed. Evidence: Added regression tests in `tests/types/test_definition_relations.py` (23/23 passed) and verified 519 tests across `tests/types/`.
    - Cleanup: Removed docs/bug_hunt/temp-tests/types_definition/; unrelated work preserved.

- [x] django_strawberry_framework/types/finalizer.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__types__finalizer.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__finalizer.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/finalizer.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__finalizer.stripped.py and docs/shadow/current/django_strawberry_framework__types__finalizer.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. In `_bind_set_owner_common`, moved the model subclass compatibility check (`if set_model is not None and definition.model is not None and not issubclass(definition.model, set_model): raise ConfigurationError(...)`) before the `if previous is None:` branch so secondary owners sharing a `FilterSet` or `OrderSet` across mismatched models are strictly rejected at finalize time even when the sidecar declares no related filters/orders.
    - Verification: Passed. Evidence: Added regression tests in `tests/types/test_finalizer.py` (16/16 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/types_finalizer/; unrelated work preserved.

- [x] django_strawberry_framework/types/relations.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__types__relations.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__relations.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/relations.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__relations.stripped.py and docs/shadow/current/django_strawberry_framework__types__relations.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 23 adversarial scratch test cases covering `_hash_component` guard ladder against unhashable containers, raising `__hash__` dunders, and metaclass hashing; validated `PendingRelation` frozen immutability and equality; tested sentinel annotations under `PendingRelationAnnotation`; and verified self-referential trees, symmetrical/asymmetrical M2M, one-to-one reverse relations, GenericRelations, and primary type disambiguation.
    - Verification: Passed. Evidence: All 28 tests in `tests/types/test_relations.py` and `tests/types/test_definition_relations.py` plus 23 scratch probes passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/types_relations/; unrelated work preserved.

- [x] django_strawberry_framework/types/relay.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__types__relay.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__relay.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/relay.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__relay.stripped.py and docs/shadow/current/django_strawberry_framework__types__relay.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 7 adversarial scratch test cases and comprehensive suites covering `Node` interface dispatch, `_NODE_TYPE_HINT_ATTR` descriptor fallbacks, composite PK verification, `NodeID` column remapping, `GlobalID` strategy precedence (`Meta` override > `RELAY_GLOBALID_STRATEGY` setting > `"model"` default), base64 decoding with empty slots, delimiter variations, multi-colon IDs, non-existent type/model decoding, synchronous/asynchronous node resolution, and `_order_nodes` with `required=False` (null holes) vs `required=True` (`DoesNotExist`).
    - Verification: Passed. Evidence: All 291 connected tests in `tests/types/test_relay_interfaces.py`, `tests/test_relay_node_field.py`, `tests/test_relay_connection.py`, and `tests/testing/test_relay.py` passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/types_relay/; unrelated work preserved.

- [x] django_strawberry_framework/types/resolvers.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__types__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__resolvers.overview.md
    - Prompt:
        - Use django_strawberry_framework/types/resolvers.py as the entry point. Read docs/shadow/current/django_strawberry_framework__types__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__types__resolvers.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) In `many_resolver`, added async context handling when `visibility_type is None` and relation is unprefetched, returning a coroutine awaiting `bounded_rows_async` to prevent `SynchronousOnlyOperation` during async requests. (2) In `forward_resolver`, handled async lazy loading via `sync_to_async(getattr, thread_sensitive=True)` to prevent `SynchronousOnlyOperation` on `ForwardManyToOneDescriptor.__get__`. (3) In `reverse_one_to_one_resolver`, handled async lazy loading via `sync_to_async` and guarded `related_does_not_exist` resolution with `AttributeError` fallback.
    - Verification: Passed. Evidence: Added regression tests in `tests/types/test_resolvers.py` (47/47 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/types_resolvers/; unrelated work preserved.

- [x] django_strawberry_framework/utils/connections.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__utils__connections.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__connections.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/connections.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__connections.stripped.py and docs/shadow/current/django_strawberry_framework__utils__connections.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) In `split_window_rows`, coerced generator/iterator `rows` to `list` to prevent generator exhaustion during two-pass iteration and `TypeError` on `len(rows)`. (2) In `resolve_relay_max_results` and `effective_bound`, guarded against `strawberry.UNSET` to prevent `TypeError` during `min()` comparison. (3) In `connection_sidecar_inputs_from_kwargs` and `has_connection_sidecar_kwargs`, handled `kwargs=None` gracefully without `AttributeError`.
    - Verification: Passed. Evidence: Added regression tests in `tests/utils/test_connections.py` and `tests/test_resource_policy.py` (149/149 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/utils_connections/; unrelated work preserved.

- [x] django_strawberry_framework/utils/context.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__utils__context.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__context.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/context.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__context.stripped.py and docs/shadow/current/django_strawberry_framework__utils__context.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 18 adversarial scratch test cases covering `get_context_value`, `stash_on_context`, and `clear_context_key` across `None`, scalar types, sequences, mappings, Django `QueryDict`, frozen dataclasses, `MappingProxyType`, and objects with hostile descriptors or throwing `__getattr__`/`__getitem__` methods; tested explicit `None` preservation vs fallback defaults; and verified request extraction.
    - Verification: Passed. Evidence: All 4 tests in `tests/utils/test_context.py` and 18 scratch probes passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/utils_context/; unrelated work preserved.

- [x] django_strawberry_framework/utils/converters.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__utils__converters.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__converters.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/converters.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__converters.stripped.py and docs/shadow/current/django_strawberry_framework__utils__converters.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 35 adversarial scratch test cases covering `convert_with_mro` dispatch skeleton, `MRO_CONTINUE` singleton identity, `snake_case`/`pascal_case`/`graphql_camel_name` case transformations, acronym runs, digit boundaries, delimiter extremes, choice enum sanitization with keywords/negative numbers/GraphQL reserved tokens, schema execution, and diamond inheritance.
    - Verification: Passed. Evidence: All 233 tests in `tests/utils/test_converters.py`, `tests/utils/test_strings.py`, `tests/forms/test_converter.py`, `tests/rest_framework/test_converter.py`, and `tests/types/test_converters.py` passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/utils_converters/; unrelated work preserved.

- [x] django_strawberry_framework/utils/errors.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__utils__errors.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__errors.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/errors.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__errors.stripped.py and docs/shadow/current/django_strawberry_framework__utils__errors.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) In `_str_list`, `_validation_messages`, and `validation_error_to_field_errors`, guarded string and byte objects against `list()` / `tuple()` character-by-character decomposition so scalar error strings remain intact. (2) In `_safe_type_name`, `_safe_class_name`, `_safe_model_label`, and `_safe_terminal_label` in `exceptions.py`, guarded `isinstance(value, type)` and attribute inspections with `try/except BaseException` to safely handle hostile `__class__` properties, `__bool__`, and `__repr__` dunders. (3) In `validation_error_to_field_errors`, unified non-dict message extraction using `_validation_messages(exc)`. (4) In `_validation_codes`, handled leaf error objects lacking `.error_list` by falling back to `(error,)` to preserve leaf `.code`.
    - Verification: Passed. Evidence: Added regression tests in `tests/utils/test_errors.py` and `tests/test_exceptions.py` (40/40 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/utils_errors/; unrelated work preserved.

- [x] django_strawberry_framework/utils/imports.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__utils__imports.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__imports.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/imports.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__imports.stripped.py and docs/shadow/current/django_strawberry_framework__utils__imports.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 56 adversarial scratch test cases covering `import_attr_if_importable`, `loaded_attr`, `import_attr`, and `require_optional_module` across scalar/collection type mismatches, hostile `str` subclasses, `sys.modules` `None` sentinels, exploding module properties/descriptors, `SyntaxError`/`RuntimeError` during module execution, chained exception preservation with `install_hint`, non-memoization for test eviction, and caller integrations across optimizer, keyset, auth, and finalizer.
    - Verification: Passed. Evidence: All 9 tests in `tests/utils/test_imports.py` and 56 scratch probes passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/utils_imports/; unrelated work preserved.

- [x] django_strawberry_framework/utils/input_values.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__utils__input_values.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__input_values.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/input_values.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__input_values.stripped.py and docs/shadow/current/django_strawberry_framework__utils__input_values.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. In `iter_active_fields`, wrapped reading `config.unset_sentinel` inside the protective `try...except` block and reused the local `unset_sentinel` variable throughout traversal loops to ensure unreadable/hostile traversal configuration attributes fail closed with typed `ConfigurationError`.
    - Verification: Passed. Evidence: Added regression tests in `tests/utils/test_input_values.py` (17/17 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/utils_input_values/; unrelated work preserved.

- [x] django_strawberry_framework/utils/inputs.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__utils__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__inputs.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/inputs.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__utils__inputs.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. 1. In `iter_provided_input_fields`, safely extracted `__strawberry_definition__` and `.fields` with default fallbacks. 2. In `clear_generated_input_namespace`, guarded `collision_registry` and `_lifecycle` descriptor attribute access against missing attributes. 3. In `GeneratedInputArgumentsFactory`, hardened `related_map` traversal against non-Mapping descriptors.
    - Verification: Passed. Evidence: Added regression tests in `tests/utils/test_inputs.py` and passed full suite (53/53 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/utils_inputs/; unrelated work preserved.

- [x] django_strawberry_framework/utils/permissions.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__utils__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__permissions.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/permissions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__utils__permissions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) In `_request_from_context` and `_channels_request_adapter`, generalized Channels request and WebSocket scope adaptation to handle object contexts (`context.request`) and bare WebSocket consumer contexts into `ChannelsRequestAdapter(request, scope)`. (2) In `run_active_input_permission_checks`, added default `None` fallback to `getattr(related_obj, target_attr, None)` to prevent unhandled `AttributeError` on custom or duck-typed related objects. (3) In `_safe_get_model`, caught `(LookupError, ValueError, TypeError, AttributeError)` from `apps.get_model` when `AUTH_USER_MODEL` is malformed.
    - Verification: Passed. Evidence: Added regression tests in `tests/utils/test_permissions.py` (49/49 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/utils_permissions/; unrelated work preserved.

- [x] django_strawberry_framework/utils/querysets.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__utils__querysets.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__querysets.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/querysets.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__querysets.stripped.py and docs/shadow/current/django_strawberry_framework__utils__querysets.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. In `coerce_field_value_or_none`, added `isinstance(field, models.Field)` check and broadened exception capture to `except Exception: return None` so numeric overflows and custom field errors fail safely.
    - Verification: Passed. Evidence: All 258 tests in `tests/utils/test_querysets.py` and 43 scratch probes passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/utils_querysets/; unrelated work preserved.

- [x] django_strawberry_framework/utils/relations.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__utils__relations.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__relations.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/relations.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__relations.stripped.py and docs/shadow/current/django_strawberry_framework__utils__relations.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. Added single-sourced `is_forward_concrete_relation` helper to classify forward FK/OneToOne with concrete columns consistently across Django versions (handling M2M flag changes between Django 5.2 and 6.x+).
    - Verification: Passed. Evidence: Added regression tests in `tests/utils/test_relations.py` and passed full suite (121/121 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/utils_relations/; unrelated work preserved.

- [x] django_strawberry_framework/utils/sessions.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__utils__sessions.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__sessions.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/sessions.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__sessions.stripped.py and docs/shadow/current/django_strawberry_framework__utils__sessions.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 43 adversarial scratch test cases covering `session_store_class` engine resolution across standard and custom engines (`db`, `cache`, `cached_db`, `file`, `signed_cookies`), `ConnectionActorState` atomic lazy initialization and slots layout, one-way provenance latching, `actor_lease` and `actor_transition` high-concurrency mutual exclusion across 100 concurrent async tasks, cancellation and error containment during logout/session transitions, and transport layer integration.
    - Verification: Passed. Evidence: All 43 scratch probes passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/utils_sessions/; unrelated work preserved.

- [x] django_strawberry_framework/utils/strings.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__utils__strings.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__strings.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/strings.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__strings.stripped.py and docs/shadow/current/django_strawberry_framework__utils__strings.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. In `_snake_case_cached`, added `i > 0 and name[i - 1].isupper()` guard so that `__x<Upper>` is only consumed as an escape marker when preceded by an uppercase segment, preventing identifiers starting with `__x_...` / `___x_...` from having the `x` character and leading underscores erroneously stripped by `snake_case`.
    - Verification: Passed. Evidence: Added regression tests in `tests/utils/test_strings.py` (41/41 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/utils_strings/; unrelated work preserved.

- [x] django_strawberry_framework/utils/typing.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__utils__typing.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__typing.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/typing.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__typing.stripped.py and docs/shadow/current/django_strawberry_framework__utils__typing.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. In `_callable_inspection_target`, replaced unbounded `while` loop with bounded iteration up to `_MAX_TYPE_WRAPPER_DEPTH = 64` (NASA Power-of-Ten Rule 2) raising `RuntimeError` on cycles, preventing infinite CPU hangs on cyclic or corrupt callable wrappers in `is_async_callable` / `is_async_generator_callable`.
    - Verification: Passed. Evidence: Added regression tests in `tests/utils/test_typing.py` (45/45 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/utils_typing/; unrelated work preserved.

- [x] django_strawberry_framework/utils/write_transaction.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__utils__write_transaction.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__write_transaction.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/write_transaction.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__write_transaction.stripped.py and docs/shadow/current/django_strawberry_framework__utils__write_transaction.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. In `_sql_statement_token`, treated leading parentheses `(` as ignorable whitespace and extracted leading alphanumeric/underscore token, correctly classifying parenthesized SQL expressions (e.g. `(SELECT ...)`).
    - Verification: Passed. Evidence: Added tests in `tests/mutations/test_write_transaction.py` and passed full suite (53/53 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/utils_write_transaction/; unrelated work preserved.

- [x] django_strawberry_framework/utils/write_values.py
    - Status: fixed
    - docs/shadow/current/django_strawberry_framework__utils__write_values.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__write_values.overview.md
    - Prompt:
        - Use django_strawberry_framework/utils/write_values.py as the entry point. Read docs/shadow/current/django_strawberry_framework__utils__write_values.stripped.py and docs/shadow/current/django_strawberry_framework__utils__write_values.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: Fixed. (1) In `decode_visible_relation_ids` and `forms/resolvers.py::_decode_form_relation_multi`, added explicit rejection for non-collection sequences (`str`, `bytes`, `bytearray`, `memoryview`, `Mapping`) returning `relation_field_error(graphql_name)` rather than decomposing into character/key lists. (2) In `coerce_relation_pk_or_none`, added safe extraction of `related_model._meta.pk` with `isinstance(field, models.Field)` to prevent `AttributeError` on non-models. (3) In `querysets.py::coerce_field_value_or_none`, broadened exception capture to `except Exception: return None` so numeric overflows and custom field exceptions fail safely. (4) In `decode_provided_fields`, tolerated unmapped attributes via `spec_by_attr.get(python_name)` instead of raising `KeyError`.
    - Verification: Passed. Evidence: Added regression tests in `tests/utils/test_write_values.py` (16/16 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/utils_write_values/; unrelated work preserved.

- [x] django_strawberry_framework/views.py
    - Status: no-bugs
    - docs/shadow/current/django_strawberry_framework__views.stripped.py
    - docs/shadow/current/django_strawberry_framework__views.overview.md
    - Prompt:
        - Use django_strawberry_framework/views.py as the entry point. Read docs/shadow/current/django_strawberry_framework__views.stripped.py and docs/shadow/current/django_strawberry_framework__views.overview.md for baseline orientation, then hunt the connected live system and implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 150 adversarial scratch test cases covering POST request body parsing and strict UTF-8 decoding in `_RequestBodyBoundaryMixin.parse_json` and `_RawBodyRequestAdapter`, GET query parameter parsing and null variable decoding in `_patched_parse_query_params`, HTTP method dispatch and status codes across sync `DjangoGraphQLView` and async `AsyncDjangoGraphQLView`, charset validation and rejection of non-UTF-8 encodings, GraphiQL IDE content negotiation and Accept header routing, multipart/form-data upload validation and lossy control field rejection in `_reject_lossy_multipart_control_fields`/`_enforce_multipart_form_encoding`, and payload size limits and CSRF boundary ordering.
    - Verification: Passed. Evidence: All 222 tests in `tests/test_views.py`, 77 tests in `examples/fakeshop/test_query/test_transport_api.py`, and 150 scratch probes passed.
    - Cleanup: Removed docs/bug_hunt/temp-tests/views/; unrelated work preserved.

- [x] Package integration
    - Status: no-bugs
    - Prompt:
        - Hunt the final live package across boundaries, including public exports and `__init__.py` files; implement every confirmed root-cause fix.
    - Result: No bugs. Evidence: Probed across 17 adversarial scratch test cases covering `__version__` parity (`0.0.14`), dynamic PEP 562 `__getattr__` soft exports, `__all__` consistency and symbol validity across all 108 modules in the package, soft-dependency isolation (`rest_framework`, `channels`, `debug_toolbar`, `cryptography`, `pillow`), registry lifecycle and subsystem clear, and AppConfig `.ready()` idempotency.
    - Verification: Passed. Evidence: Added regression tests in `tests/base/test_init.py` (19/19 passed).
    - Cleanup: Removed docs/bug_hunt/temp-tests/package_integration/; unrelated work preserved.

- [x] Final test gate
    - Status: passed
    - Owner: Worker 0
    - Prompt:
        - Run `uv run pytest`; require a passing suite and 100% configured package coverage.
    - Result: Passed. 6,441 passed, 40 skipped, 0 failed. Required test coverage of 100.0% reached (16,162/16,162 statements, 0 missing lines across all 86 package source modules).

