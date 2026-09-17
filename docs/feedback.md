# Adversarial review — refusal dispatch and contract migration

Date: 2026-09-17

**Verdict: not release-ready yet.** The five findings from the preceding review are fixed on
their reported shapes. Enforcement now comes from the schema's canonical policy record rather
than from the consumer extension graph; direct subclasses and hybrids are refused; a refused
chain retains the resource boundary; hostile factory-exception rendering stays contained; and
the resume registrar restores the caller's exact prior budget after a streamed frame.

I independently reproduced those closures with focused `uv run python` probes. In particular,
the hybrid fails at construction, an authority-producing factory and a malformed document both
return `SCHEMA_CONFIGURATION_UNAVAILABLE`, a hostile `__repr__` / `__str__` exception cannot
escape the refusal, and two frames driven in one task leave `armed_resource_policy()` as `None`
after each frame and after close.

The new pass found two release blockers beyond those rows:

1. A refused request with an invalid, empty, Unicode, or non-string `operation_name` still
   escapes the configuration-refusal boundary. Sync execution raises
   `CannotGetOperationTypeError`; the real sync and async HTTP mounts return `400 text/plain`
   with `Unknown operation named ...`; streaming emits that lookup error instead of the stable
   configuration code.
2. The new authority-factory contract was not migrated through the existing live error-policy
   suite. Production now correctly refuses those factories, while at least nine existing live
   test nodes still require them to mask normally. The same obsolete contract remains in
   module documentation and the live-test catalog.

There is also one lower-severity proof/documentation defect: the refusal path still invokes
graphql-core's parser once per refused request to parse a package constant, while its test spies
on a different module binding and its prose says the parser is never invoked. The dangerous
claim—attacker text is not parsed—is now true; the broader claim is not.

This review follows [AGENTS.md][agents], including its root-cause, live-test placement, and
same-change test rules. I read the current [spec][spec-050], [build record][build-050], changed
implementation, current live suites, and the relevant upstream execution path. I did not run
pytest, coverage, the sharded suite, or the declared floor matrix.

## Confirmed foundation

Do not revert the new ownership model:

- [`_SchemaEnforcement`][schema] owns only canonical resource and error policies plus settlement
  state. [`DjangoSchema.get_extensions`][schema] constructs fresh exact package authorities
  around consumer extensions per operation.
- [`_consumer_extension_entries`][schema] treats direct exact enforcement entries as
  construction-time declarations, and [`_declared_authority`][schema] refuses subclasses and
  both multiple-inheritance base orders before the schema is built.
- A factory is resolved once. If its result claims either package authority, is not a
  `SchemaExtension`, or its call raises, the operation receives a refused chain rather than
  letting consumer behavior decide enforcement.
- [`_refused_chain`][schema] retains both exact package authorities. The raw document still
  meets the resource extension's token/depth scan before the parse stage, while the refused
  operation executes no consumer hook or resolver.
- [`OperationState.rebind_on_resume`][operation-state] transfers a budget token to the active
  resume registrar when the budget is first armed during a frame. Later resumes bind the live
  lease and every resume restores its own caller context. The operation teardown remains the
  sole owner of lease closure.

Those are the correct roots. The remaining work is at the dispatch boundary and in completing
the contract migration around them.

## P1-1 — invalid `operationName` escapes a refused schema

### Evidence

[`_refusal_document`][schema] copies `execution_context.operation_name` into its substitute
document only when it matches GraphQL's `Name` grammar. For any other value it creates an
anonymous substitute but leaves the original `execution_context.operation_name` untouched.
Upstream subsequently asks for the operation type by looking that original name up in the
substitute document. The lookup cannot succeed, so it replaces the already-published refusal.

Focused direct results on one schema whose accepted factory resolves to `7`:

```text
operation_name       execute_sync                                      stream
None                  SCHEMA_CONFIGURATION_UNAVAILABLE                  same code
"missing"             SCHEMA_CONFIGURATION_UNAVAILABLE                  same code
"bad-name"            raises CannotGetOperationTypeError                Unknown operation
""                    raises CannotGetOperationTypeError                Unknown operation
"🔥"                   raises CannotGetOperationTypeError                Unknown operation
0 / object()          raises CannotGetOperationTypeError                not a stable refusal
```

The issue is wire-reachable. Against the real `/iso-chain/` and `/iso-chain-async/` Django
mounts, `operationName` values `"bad-name"`, `""`, and `"🔥"` each returned `400 text/plain`
and echoed the submitted name. The valid-but-absent name control returned HTTP 200 with the
documented configuration code.

This contradicts the new guarantee that a schema whose chain cannot be admitted refuses every
request on one stable, parser-independent path. It also means sync, async, and stream no longer
have the same result shape precisely on hostile request metadata.

### Root fix

The substitute document and the lookup selector must be changed as one operation:

1. When `_RefusedConfiguration.on_parse` installs a package-owned document, also replace
   `execution_context.operation_name` with package-owned lookup state. The simplest honest
   state is `None` plus one anonymous substitute operation. Nothing consumer-supplied should
   remain authoritative for selecting a document the package itself supplied.
2. Continue choosing the substitute operation type from `allowed_operations`, because
   upstream's next check must still see a type that transport allows.
3. Do not sanitize and interpolate the requested name. Even a valid name has no semantic role
   after the consumer document has been discarded, and retaining two coupled dynamic values is
   the source of this defect.
4. Preserve the original query text and operation name only as inert request diagnostics if a
   transport needs them. They must not participate in parsing, operation selection, validation,
   or execution once configuration refusal has taken ownership.

Required regressions belong in both tiers mandated by [AGENTS.md][agents]:

- Package tests: `None`, a valid absent name, invalid punctuation, empty string, Unicode, and a
  non-string direct-API value over `execute_sync`, `execute`, and `stream`. Each row receives one
  stable configuration error and never raises out of the API.
- Live tests: sync and async JSON POST rows for valid absent, invalid punctuation, empty, and
  Unicode `operationName`, each with its own parametrized node ID. All return the same JSON
  envelope and code; none return `text/plain` or echo the operation name.
- Retain an over-token/depth control: the resource rejection still outranks configuration
  refusal before operation selection is normalized.

## P1-2 — the authority-factory migration leaves the live suite red

### Evidence

The production contract now intentionally refuses a factory whose resolved member is
`DjangoErrorPolicyExtension`. The existing [live error-policy suite][live-error] still asserts
the opposite:

- `_error_policy_factory` powers `/ep-factory/`, and
  `test_a_factory_policy_entry_masks_once_so_the_client_id_is_the_logged_id` requires the
  response to be a normally masked resolver failure.
- `ENTRY_SPELLINGS` includes `fresh-factory` and `singleton-factory`.
  `test_a_nested_operation_does_not_unmask_the_outer_failure` and
  `test_an_overlapping_request_does_not_unmask_a_failing_one` each run both spellings over sync
  and async mounts and require the resolver to execute and be masked.

Focused live requests prove the mismatch without invoking pytest:

```text
/ep-factory/                         SCHEMA_CONFIGURATION_UNAVAILABLE
/ep-entry-fresh-factory-sync/        SCHEMA_CONFIGURATION_UNAVAILABLE
/ep-entry-singleton-factory-sync/    SCHEMA_CONFIGURATION_UNAVAILABLE
/ep-entry-class-sync/                resolver runs; unexpected error is masked
/ep-entry-instance-sync/             resolver runs; unexpected error is masked
```

That is at least nine deterministic stale live nodes: the dedicated factory test plus four
factory rows in each of the two spelling/color matrices. It violates the repository rule that
tests change with production behavior and means the unrun default gate cannot be green on this
tree.

### Root fix

Complete the migration; do not weaken the production admission rule to satisfy old tests:

1. Keep class and direct exact-instance declaration rows where they prove normalization to one
   package-owned masker.
2. Move fresh-factory and singleton-factory isolation controls to an unrelated consumer
   extension. Let the schema's automatic exact error authority perform masking. That preserves
   the intended nested/overlap isolation coverage without making consumer code an authority.
3. Repurpose `/ep-factory/` as the live refusal proof, or remove it if the dedicated isolation
   suite already owns the identical sync/async claim. If retained, assert the stable
   configuration code, no resolver execution, no correlation-id mint, and no consumer hook.
4. Sweep all four test trees for the old “factory policy entry suppresses/replaces/deduplicates
   the automatic authority” contract. The package tests have largely moved; the live
   error-policy file has not.
5. Keep one plain `strawberry.Schema` control for the documented standalone factory use. The
   stricter admission rule belongs to `DjangoSchema`; it must not accidentally redefine
   Strawberry's own supported surface.

## P2-1 — the parser proof spies on the wrong binding

### Evidence

[`_refusal_document`][schema] imports `parse` into `django_strawberry_framework.schema` and
calls it for every refused request. The new
`test_a_refused_schema_never_reaches_the_real_parser` patches
`strawberry.schema.schema.parse`, which is upstream's separate binding. Its `parsed == []`
assertion therefore proves only that Strawberry does not parse the original request after the
hook; it does not prove the test's broader wording that the parser was never invoked.

The security boundary is materially improved: the package parses only its small constant and
never attacker-controlled document text. But current prose in `_refusal_document`, the test,
and the glossary conflates those statements, and reparsing the same three constant documents
on every refused request is avoidable failure-path overhead.

### Root fix

Prefer pre-parsed package documents:

1. Parse one anonymous `query`, `mutation`, and `subscription` refusal document at module load,
   or construct equivalent immutable AST constants once.
2. Select one by allowed operation type and assign it directly in `on_parse`; pair this with
   P1-1's `operation_name = None` normalization.
3. Test the actual local seam. Assert that a refused request never sends its untrusted source
   to a parser. If documents are pre-parsed, patching either runtime parser should observe no
   call at all.
4. If per-request parsing is deliberately retained, narrow every claim and test name to “the
   consumer document is never parsed,” and spy on `django_strawberry_framework.schema.parse`
   to assert that only the fixed package source is accepted. Do not leave a stronger claim than
   the implementation proves.

## Documentation and cleanup required by the new model

The implementation's foundation changed more broadly than its prose sweep:

- [`DjangoErrorPolicyExtension`][error-extension] still says a consumer-supplied policy entry
  replaces the automatic extension and that a bare class and factory entry behave identically.
  Under `DjangoSchema`, a factory now refuses the operation.
- [`DjangoResourcePolicyExtension`][resource-extension] still says an accepted instance remains
  reachable through `info.schema.extensions` and decides the next operation. A direct exact
  instance is now folded into canonical schema state and removed from that graph.
- The module header, helpers, and comments in [the live error-policy suite][live-error] still
  teach factory-owned masking and automatic-entry suppression.
- The header and historical coverage prose in [the live resource-policy suite][live-resource]
  still refer to a factory-supplied bound and dropping the automatic append.
- The [live-test catalog][live-readme] still advertises `/ep-factory/` one-mask behavior and a
  factory-supplied resource bound as current coverage.
- [`Execution resource policy`][glossary-resource] still says the policy an accepted extension
  instance carries remains reachable and governs the next operation. That is the retired
  architecture.
- [`DjangoSchema`][schema] contains the duplicated sentence “schema built through this class is
  therefore bounded with no opt-in.” Remove the duplicate during the documentation sweep.

Use symbol-path references in all standing documentation. Keep the old design only where a
historical build record explicitly describes a historical tree; current package docs and live
suite catalogs must describe the current contract.

## Release conditions

Do not mark spec-050 done until all of these hold on one identified tree:

- The five preceding attacks remain closed under their original probes.
- Every refused request normalizes both the substitute document and its operation selector;
  hostile `operationName` values cannot escape, change media type/status, or replace the stable
  code on sync, async, or stream paths.
- Existing live error-policy tests are migrated to the package-owned-authority model, and the
  old authority-factory contract has no surviving current-doc or current-test claim.
- The parser proof observes the binding actually used and states exactly whether no parser runs
  or only no attacker text is parsed.
- Package mechanics stay in `tests/`; all HTTP-reachable outcomes are covered in
  `examples/fakeshop/test_query/` with explicit IDs and no loop-bundled matrices.
- Standing docs and the build record describe the final authority, refusal, and resumed-stream
  model consistently.
- Formatting, structural scripts, the full default suite with 100% package coverage, the
  sharded suite, and the declared floor matrix all run against that same tree. The current
  build narrative still names an older gated commit, so the present uncommitted tree has no
  release gate yet.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md

<!-- docs/ -->
[glossary-resource]: GLOSSARY.md#execution-resource-policy
[spec-050]: spec-050-list_field_arguments-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build-050]: builder/DONE/build-050-list_field_arguments-0_0_15.md

<!-- django_strawberry_framework/ -->
[error-extension]: ../django_strawberry_framework/extensions/error_policy.py
[operation-state]: ../django_strawberry_framework/extensions/operation_state.py
[resource-extension]: ../django_strawberry_framework/extensions/resource_policy.py
[schema]: ../django_strawberry_framework/schema.py

<!-- tests/ -->

<!-- examples/ -->
[live-error]: ../examples/fakeshop/test_query/test_error_policy_api.py
[live-readme]: ../examples/fakeshop/test_query/README.md
[live-resource]: ../examples/fakeshop/test_query/test_resource_policy_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
