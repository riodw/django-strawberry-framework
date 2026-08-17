# Review: `django_strawberry_framework/exceptions.py`

Status: verified

## Understanding

`exceptions.py` is the dependency-free bottom of the import graph. It owns the package base
exception, the configuration family (`ConfigurationError`, `PathResolutionError`, and
`LookupValidationError`), the optimizer family (`OptimizerError`), safe rendering helpers, and
the call-time `str` / `repr` protection that keeps GraphQL-core's `located_error` from replacing
a typed framework exception when a message argument is hostile. `SyncMisuseError` is defined in
`utils/querysets.py` as a multiple-inheritance `ConfigurationError` / `RuntimeError` marker, and
`ResourceLimitExceeded` is intentionally owned by `resource_policy.py` because it also carries
GraphQL wire extensions.

The target has no scoped changes relative to baseline `e10d44ee8d95e45c09383d1783eb7a37f475debf`.
Production callers import the target classes directly: configuration and schema/type/finalizer
paths raise `ConfigurationError`; strict relation classification raises `PathResolutionError`;
the lookup-validation utility defines `LookupValidationError` (currently without a shipped
production caller); optimizer planning and strictness guards raise `OptimizerError`; sync
pipelines raise `SyncMisuseError`. GraphQL execution preserves these exceptions through
`original_error`, while the separate error-policy extension masks only unexpected
non-`GraphQLError` failures.

## Verification

- `git --no-pager diff e10d44ee8d95e45c09383d1783eb7a37f475debf -- django_strawberry_framework/exceptions.py tests/test_exceptions.py` is empty.
- Read `tests/test_exceptions.py` in full. Its focused cases pin inheritance, GraphQL `original_error`
  identity, lazy/recomputed rendering, mutable `.args`, pickle round-trips, delayed stateful
  failures, `BaseException`-raising dunders, hostile metaclass names, and `SyncMisuseError` MRO.
- `uv run pytest tests/test_exceptions.py tests/utils/test_relations.py --no-cov` passed 114 tests
  before this zero-edit result was recorded.
- A disposable experiment under `docs/review/temp-tests/exceptions/constructor_contract.py`
  confirmed that direct constructors with hostile model/terminal metadata can raise the hostile
  `BaseException`. This does not represent a reachable package contract: production
  `PathResolutionError` and `LookupValidationError` callers pass Django-owned model/field
  descriptors, and malformed relation/lookup descriptors fail in their traversal methods before
  either constructor is reached. The shared base's public hostile-message contract is separately
  covered through real Strawberry GraphQL execution.
- Traced resource, error-policy, permission, validation, optimizer, and sync/async callers.
  `ResourceLimitExceeded` remains a deliberate separate GraphQL error owner, and
  `UnwindowableConnection` remains an internal control-flow sentinel rather than a surfaced
  framework exception.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The exception hierarchy has one owner, typed configuration/path/optimizer contracts are
consistently imported by callers, and the lookup-validation utility has a direct typed contract.
The call-time rendering safeguards preserve exception identity across sync, async, and GraphQL
conversion. No accepted root-cause finding was found; the scoped result is zero-edit.

## Implementation (Worker 1)

None — zero-edit cycle.

- Changed files: none. The target and its existing focused tests are already identical to the
  scoped baseline.
- Permanent tests: no additions; existing `tests/test_exceptions.py` and
  `tests/utils/test_relations.py` cover the reachable contracts described above.
- Scratch/focused verification: the constructor-boundary experiment is recorded under
  `docs/review/temp-tests/exceptions/constructor_contract.py`; focused tests passed 114/114.
- Formatter/linter: not run because no files were edited.
- Rejected finding: hardening direct `PathResolutionError` / `LookupValidationError` construction
  against hostile metadata would be defensive API expansion outside the package's actual caller
  boundary. The production path owns the Django model/field descriptors, and the malformed-shape
  failures occur before construction; no typed contract is lost in reachable usage.
- Changelog: no entry warranted for a zero-edit review.

## Independent verification (Worker 2)

The target is byte-identical to the scoped baseline: `git show e10d44ee8d95e45c09383d1783eb7a37f475debf:django_strawberry_framework/exceptions.py | cmp - django_strawberry_framework/exceptions.py` returned exit code 0, and both the baseline-scoped and current-worktree diffs for `django_strawberry_framework/exceptions.py` are empty.

Caller and boundary trace:

- `DjangoStrawberryFrameworkError` is the dependency-free base. `ConfigurationError` is raised at settings/schema/type/finalizer, mutation/form/serializer, filter/order, permission/cascade, and visibility-boundary validation seams. `OptimizerError` is raised by optimizer input metadata, strict N+1 resolvers, window planning, and row-preserving predicate guards. `SyncMisuseError` is the `ConfigurationError`/`RuntimeError` marker from sync visibility, list/connection source, permission, and cascade boundaries; its async twin intentionally runs the same sync walk in one worker and therefore preserves the same typed failure.
- `PathResolutionError` is constructed only by `utils/relations.py::classify_path`. The production filter candidate builder calls that strict classifier only for framework-generated leaves; declared/consumer-origin leaves are excluded, and expanded relation-prefix failures fail closed as an optimization miss. `path_traverses_to_many` catches the strict error and preserves the legacy lenient boolean contract.
- `LookupValidationError` is the typed contract of `utils/relations.py::validate_lookup_expr`; grep of the production package found no shipped caller beyond its definition, while the utility's direct tests cover scalar, relation, transform, empty, and invalid expressions. This is a dormant utility seam, not a reachable exception-construction boundary, and does not justify changing the zero-edit target.
- `ResourceLimitExceeded` remains owned by `resource_policy.py`, where it subclasses both `GraphQLError` and the package base and carries `extensions.code = "RESOURCE_LIMIT_EXCEEDED"`. Resource document/value/deadline/collection guards raise it across sync HTTP, async HTTP, and WebSocket execution; `UnwindowableConnection` remains a private optimizer control-flow sentinel.
- GraphQL-core's `located_error` keeps framework exceptions in `original_error`; the production error-policy extension masks only non-`GraphQLError` originals under `DEBUG=False`, while deliberate `GraphQLError` rejections (including resource limits) remain unchanged. Sync, async, completion, and pre-execution policy tests all passed.
- Settings/configuration, permission/cascade, resource-policy, optimizer, and sync/async focused paths were traced to their owning validators. No exception is converted to an unrelated raw error at a reachable boundary.

Verification commands and results:

- `uv run pytest tests/test_exceptions.py tests/utils/test_relations.py --no-cov` — 114 passed.
- `uv run pytest tests/test_error_policy.py tests/test_resource_policy.py tests/optimizer/test_predicates.py tests/utils/test_querysets.py --no-cov` — 388 passed.
- Hostile configuration cases in `tests/test_views.py` — 18 passed; hostile factory/window cases in `tests/test_routers.py` — 15 passed.
- `uv run python docs/review/temp-tests/exceptions/constructor_contract.py` reproduced `KeyboardInterrupt` for both deliberately hostile direct constructors. The experiment is not a reachable package contract: actual strict callers supply Django-owned model/field metadata, and malformed descriptors fail during traversal before either constructor is entered. The shared base's hostile message rendering is separately proven through real Strawberry GraphQL execution.

No High, Medium, or Low finding remains. The zero-edit result is independently verified.
