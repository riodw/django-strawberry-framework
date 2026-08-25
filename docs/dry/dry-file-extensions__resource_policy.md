# DRY review: `django_strawberry_framework/extensions/resource_policy.py`

Status: verified


## System trace

`django_strawberry_framework/extensions/resource_policy.py` is the request-time enforcement engine for the framework's execution resource policy subsystem ([spec-047][spec-047] Decisions 2–4, 7–11, 13). It defines [`DjangoResourcePolicyExtension`][extensions-resource-policy], a Strawberry [`SchemaExtension`][strawberry-extension] that applies lexical, structural, and value-cardinality budgets across incoming GraphQL operations before any resolver, database query, or ORM transaction executes.

The module owns the following core responsibilities:

- **Pre-parse document text scan (spec-047 Decision 3):**
  [`scan_document_text`][extensions-resource-policy] performs a single lexical sweep over raw document text in [`DjangoResourcePolicyExtension.on_operation`][extensions-resource-policy] using `graphql.language.lexer.Lexer` before `graphql-core`'s recursive-descent parser runs.
  - Token budget: Charges [`ResourcePolicy.max_document_tokens`][resource-policy] per lexical token read.
  - Structural depth: Charges [`ResourcePolicy.max_depth`][resource-policy] by maintaining a running balance of opening delimiter kinds ([`_OPEN_TOKEN_KINDS`][extensions-resource-policy] = `BRACE_L`, `PAREN_L`, `BRACKET_L`) and closing delimiter kinds ([`_CLOSE_TOKEN_KINDS`][extensions-resource-policy] = `BRACE_R`, `PAREN_R`, `BRACKET_R`) derived from [`_STRUCTURAL_DELIMITER_PAIRS`][extensions-resource-policy].
  - Parser protection: Stops deeply nested or oversized text attacks from exhausting the Python interpreter stack during parse or validation.
  - Syntax error preservation: Swallows `GraphQLSyntaxError` so that malformed documents receive accurate syntax diagnostics from `graphql-core` rather than premature resource limit errors, unless the token or depth budget was already exceeded prior to the malformed token.
- **Context lifecycle and deadline management (spec-047 Decisions 2, 9):**
  [`DjangoResourcePolicyExtension.on_operation`][extensions-resource-policy] coordinates the operation lifecycle:
  - Policy resolution: Calls [`DjangoResourcePolicyExtension._resolved_policy`][extensions-resource-policy] to retrieve the effective [`ResourcePolicy`][resource-policy] from an explicit instance passed to [`DjangoResourcePolicyExtension.__init__`][extensions-resource-policy], from `schema.resource_policy`, or falling back fail-closed to [`DEFAULT_RESOURCE_POLICY`][resource-policy].
  - Deadline initialization: If `policy.execution_deadline_seconds` is configured, calculates a monotonic deadline timestamp (`time.monotonic() + policy.execution_deadline_seconds`) and stores it under [`DST_RESOURCE_DEADLINE`][resource-policy].
  - Context stashing and restoration: Stashes the active policy under [`DST_RESOURCE_POLICY`][resource-policy] via [`stash_resource_policy`][resource-policy]. It records previous context entries using [`_MISSING_CONTEXT_VALUE`][extensions-resource-policy] as a missing sentinel and restores the exact previous state in `finally` via [`DjangoResourcePolicyExtension._restore_context_value`][extensions-resource-policy]. This ensures nested inner schema executions (sync or async) cleanly restore outer schema policies and deadlines without leaking or widening bounds.
- **Iterative document AST walk and structural budgets (spec-047 Decisions 4, 8):**
  [`charge_document`][extensions-resource-policy] walks the validated AST in [`DjangoResourcePolicyExtension.on_execute`][extensions-resource-policy] using an explicit stack (`_Frame`) rather than recursion:
  - Root type resolution: Identifies the root `GraphQLObjectType` for the requested operation (`query`, `mutation`, `subscription`) via [`_root_type`][extensions-resource-policy].
  - Fragment expansion: Maps document fragment definitions once and expands fragment spreads at every spread site, tracking the spread path on the stack to ensure cyclic fragment sets terminate safely.
  - Selection and alias budget: [`_DocumentBudget`][extensions-resource-policy] (initialized in [`_DocumentBudget.__init__`][extensions-resource-policy]) charges field selections against [`ResourcePolicy.max_selections`][resource-policy] and aliased fields against [`ResourcePolicy.max_aliases`][resource-policy] via [`_DocumentBudget.charge_selection`][extensions-resource-policy]. Directives (such as `@skip` or `@include`) change what is returned but do not evade selection accounting.
  - Multiplicative collection cost: [`_DocumentBudget.charge_collection`][extensions-resource-policy] calculates compounding collection costs across nested collections against [`ResourcePolicy.max_collection_cost`][resource-policy]. It computes collection rows via [`_collection_rows`][extensions-resource-policy] and [`_page_bound`][extensions-resource-policy], exempting Relay connection `edges` fields via [`_is_connection_type`][extensions-resource-policy] checking [`_CONNECTION_MARKER_FIELD`][extensions-resource-policy] (`"edges"`) and [`_EDGE_MARKER_FIELDS`][extensions-resource-policy] (`{"node", "cursor"}`).
  - Introspection field resolution: [`_field_definition`][extensions-resource-policy] resolves standard fields and introspection meta-fields ([`_SCHEMA_META_FIELD`][extensions-resource-policy] = `"__schema"`, [`_TYPE_META_FIELD`][extensions-resource-policy] = `"__type"`, [`_TYPENAME_META_FIELD`][extensions-resource-policy] = `"__typename"`) to `SchemaMetaFieldDef`, `TypeMetaFieldDef`, and `TypeNameMetaFieldDef`, ensuring introspection query trees are properly budgeted rather than exempted.
- **Value cardinality and input budget walker (spec-047 Decision 4):**
  [`_ValueBudget`][extensions-resource-policy] (initialized in [`_ValueBudget.__init__`][extensions-resource-policy]) bounds variable payloads and literal argument trees:
  - Mutation lifecycle: [`_ValueBudget.begin_mutation_field`][extensions-resource-policy] resets per-mutation counters before each top-level mutation selection is charged.
  - Iterative value traversal: [`_ValueBudget.charge`][extensions-resource-policy] traverses input value graphs iteratively using an explicit stack of `_ValueEntry` items, enforcing [`ResourcePolicy.max_value_depth`][resource-policy] from ancestor path depth.
  - Rejection handler: [`_ValueBudget._reject`][extensions-resource-policy] raises [`ResourceLimitExceeded`][resource-policy] on budget overruns.
  - Container and cycle management: [`_ValueBudget._charge_container`][extensions-resource-policy] charges container width against [`ResourcePolicy.max_container_width`][resource-policy]. It checks ancestor object identity using [`_closes_a_cycle`][extensions-resource-policy] to terminate cycles without suppressing duplicate charges across non-cyclic references.
  - Input list classification: [`_ValueBudget._charge_list_family`][extensions-resource-policy] classifies list types by GraphQL type definition:
    - Nested input object lists are charged against [`ResourcePolicy.max_nested_rows`][resource-policy].
    - `ID` lists in mutations (recognized via [`_ID_SCALAR_NAME`][extensions-resource-policy] = `"ID"`) are charged against [`ResourcePolicy.max_relation_ids_per_mutation`][resource-policy] and [`ResourcePolicy.max_relation_ids_total`][resource-policy].
    - `ID` lists under query fields with argument name [`_NODE_IDS_ARGUMENT`][extensions-resource-policy] (`"ids"`) are charged against [`ResourcePolicy.max_node_ids`][resource-policy].
    - All other typed list arguments are charged against [`ResourcePolicy.max_membership_items`][resource-policy].
  - Leaf and scalar budget: [`_ValueBudget._charge_leaf`][extensions-resource-policy] charges scalar values against [`ResourcePolicy.max_scalar_bytes`][resource-policy] (measuring byte length for `str`, `bytes`, `bytearray`, and `memoryview` using `nbytes`).
  - Upload handling: When [`_UPLOAD_SCALAR_NAME`][extensions-resource-policy] (`"Upload"`) is detected, [`_ValueBudget._charge_upload`][extensions-resource-policy] enforces [`ResourcePolicy.max_upload_count`][resource-policy], single-file byte size against [`ResourcePolicy.max_upload_file_bytes`][resource-policy], and cumulative upload bytes against [`ResourcePolicy.max_upload_total_bytes`][resource-policy].

Connected behavior examined:
- [`django_strawberry_framework/resource_policy.py`][resource-policy]: Pure domain model defining `ResourcePolicy`, `DEFAULT_RESOURCE_POLICY`, `resolve_resource_policy`, `stash_resource_policy`, `clear_resource_context`, `policy_from_info`, `check_deadline`, `bounded_rows`, `bounded_rows_async`, `validate_collection_bound`, `effective_bound`, and `ResourceLimitExceeded`.
- [`django_strawberry_framework/schema.py`][schema]: Automatic installation of `DjangoResourcePolicyExtension` via `_with_resource_policy_extension` and validation of `schema.resource_policy` during `DjangoSchema` construction.
- [`django_strawberry_framework/conf.py`][conf]: Settings loading for `DJANGO_STRAWBERRY_FRAMEWORK["RESOURCE_POLICY"]`.
- [`django_strawberry_framework/connection.py`][connection]: Connection pagination ceiling clamping `relay_max_results` via `policy.max_page_size` and cooperative deadline check in `_resolve_connection_fast_path`.
- [`django_strawberry_framework/list_field.py`][list-field]: Raw list field row limiting via `bounded_rows` and `policy.max_list_rows`.
- [`django_strawberry_framework/relay.py`][relay]: Relay node refetching deadline checks and node ID bounds.
- [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers]: Mutation write pipeline deadline check before `transaction.atomic()`.
- [`django_strawberry_framework/utils/context.py`][utils-context]: Shared shape-agnostic context get/set/delete helpers.
- [`django_strawberry_framework/extensions/__init__.py`][extensions-init]: Re-exports `DjangoResourcePolicyExtension`.
- [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init]: Re-exports `DjangoResourcePolicyExtension`, `ResourcePolicy`, `DEFAULT_RESOURCE_POLICY`, `resolve_resource_policy`, `ResourceLimitExceeded`, `bounded_rows`, `bounded_rows_async`, `check_deadline`, `effective_bound`.
- [`tests/test_resource_policy.py`][test-resource-policy]: Unit test suite covering construction, validation, precedence ladder, narrowing, context threading, degenerate inputs, cycle safety, AST meta-fields, and upload size checks.
- [`examples/fakeshop/test_query/test_resource_policy_api.py`][test-fakeshop-resource-policy-api]: Live HTTP acceptance test suite covering the full matrix of resource bounds against live Django GraphQL views over sync and async transports.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/extensions/resource_policy.py --include-constants`):
- Parsed 1 target file, 856 lines, 39 definitions:
  - 12 module constants: [`_STRUCTURAL_DELIMITER_PAIRS`][extensions-resource-policy], [`_OPEN_TOKEN_KINDS`][extensions-resource-policy], [`_CLOSE_TOKEN_KINDS`][extensions-resource-policy], [`_ID_SCALAR_NAME`][extensions-resource-policy], [`_UPLOAD_SCALAR_NAME`][extensions-resource-policy], [`_NODE_IDS_ARGUMENT`][extensions-resource-policy], [`_CONNECTION_MARKER_FIELD`][extensions-resource-policy], [`_EDGE_MARKER_FIELDS`][extensions-resource-policy], [`_SCHEMA_META_FIELD`][extensions-resource-policy], [`_TYPE_META_FIELD`][extensions-resource-policy], [`_TYPENAME_META_FIELD`][extensions-resource-policy], [`_MISSING_CONTEXT_VALUE`][extensions-resource-policy].
  - 8 standalone functions: [`scan_document_text`][extensions-resource-policy], [`_closes_a_cycle`][extensions-resource-policy], [`_root_type`][extensions-resource-policy], [`_field_definition`][extensions-resource-policy], [`_page_bound`][extensions-resource-policy], [`_collection_rows`][extensions-resource-policy], [`_is_connection_type`][extensions-resource-policy], [`charge_document`][extensions-resource-policy].
  - 3 classes: [`_ValueBudget`][extensions-resource-policy], [`_DocumentBudget`][extensions-resource-policy], [`DjangoResourcePolicyExtension`][extensions-resource-policy].
  - 16 methods:
    - [`_ValueBudget.__init__`][extensions-resource-policy], [`_ValueBudget._reject`][extensions-resource-policy], [`_ValueBudget.begin_mutation_field`][extensions-resource-policy], [`_ValueBudget.charge`][extensions-resource-policy], [`_ValueBudget._charge_container`][extensions-resource-policy], [`_ValueBudget._charge_list_family`][extensions-resource-policy], [`_ValueBudget._charge_leaf`][extensions-resource-policy], [`_ValueBudget._charge_upload`][extensions-resource-policy].
    - [`_DocumentBudget.__init__`][extensions-resource-policy], [`_DocumentBudget.charge_selection`][extensions-resource-policy], [`_DocumentBudget.charge_collection`][extensions-resource-policy].
    - [`DjangoResourcePolicyExtension.__init__`][extensions-resource-policy], [`DjangoResourcePolicyExtension._resolved_policy`][extensions-resource-policy], [`DjangoResourcePolicyExtension.on_operation`][extensions-resource-policy], [`DjangoResourcePolicyExtension._restore_context_value`][extensions-resource-policy], [`DjangoResourcePolicyExtension.on_execute`][extensions-resource-policy].

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `DjangoResourcePolicyExtension` and its internal walkers (`scan_document_text`, `charge_document`, `_DocumentBudget`, `_ValueBudget`) enforce a uniform security perimeter across all GraphQL operation flavors:
   - Queries, mutations, and subscriptions executed over sync HTTP, async HTTP, or WebSocket transports all enter `DjangoResourcePolicyExtension.on_operation` and `DjangoResourcePolicyExtension.on_execute`.
   - Mutation write surfaces (`DjangoMutation`, `SerializerMutation`, `DjangoModelFormMutation`) share identical value budget accounting for input objects, nested rows, and relation IDs (`max_relation_ids_per_mutation` and `max_relation_ids_total`).
   - Relay connections and plain `DjangoListField` instances share collection cost accounting during document charging, while their respective runtime resolvers enforce page and row ceilings via `ResourcePolicy.max_page_size` and `ResourcePolicy.max_list_rows`.
   - Rejections raise `ResourceLimitExceeded` (a `GraphQLError` subclass) with code `RESOURCE_LIMIT_EXCEEDED`, rendering identical error structures across all query, mutation, and transport variants.
2. **Sync and async twins:**
   Zero duplication. All extension lifecycle hooks ([`DjangoResourcePolicyExtension.on_operation`][extensions-resource-policy], [`DjangoResourcePolicyExtension.on_execute`][extensions-resource-policy]) are written as synchronous generators (`yield`). Strawberry executes synchronous generator extensions uniformly across both synchronous (`execute_sync`) and asynchronous (`execute`) operations.
   - Context stashing and restoration (`_restore_context_value`) behave identically across sync and async nested executions.
   - Live acceptance tests in `examples/fakeshop/test_query/test_resource_policy_api.py` confirm exact error parity across `DjangoGraphQLView` (sync) and `AsyncDjangoGraphQLView` (async) endpoints.
3. **Derived rather than repeated knowledge:**
   - Single policy definition: [`resource_policy.py::ResourcePolicy`][resource-policy] is the sole definition of all budget fields, types, and defaults. The extension derives all limits directly from the active policy instance.
   - Lexer token classifications: [`_OPEN_TOKEN_KINDS`][extensions-resource-policy] and [`_CLOSE_TOKEN_KINDS`][extensions-resource-policy] derive token kinds from [`_STRUCTURAL_DELIMITER_PAIRS`][extensions-resource-policy] declared once using `graphql.language.token_kind.TokenKind`.
   - Meta-field definitions: [`_field_definition`][extensions-resource-policy] maps introspection fields to `graphql-core`'s canonical definitions (`SchemaMetaFieldDef`, `TypeMetaFieldDef`, `TypeNameMetaFieldDef`), avoiding redundant schema re-definitions.
   - Context dispatch: Shape-agnostic context manipulation delegates to [`utils/context.py`][utils-context] rather than implementing custom attribute/dict access branches.
   - Default fallbacks: [`resource_policy.py::DEFAULT_RESOURCE_POLICY`][resource-policy] is the single authoritative fallback when `schema.resource_policy` is absent.
4. **Inverse and round-trip pairs:**
   - Context stash and restore: [`DjangoResourcePolicyExtension.on_operation`][extensions-resource-policy] stashes `policy` and `deadline` on entry and restores previous context state (or removes keys) in `finally` using [`_restore_context_value`][extensions-resource-policy] with sentinel [`_MISSING_CONTEXT_VALUE`][extensions-resource-policy]. This guarantees clean context restoration for nested schema calls.
   - Pre-parse text scan and post-validation AST walk: [`scan_document_text`][extensions-resource-policy] bounds raw lexical tokens and bracket nesting depth before parsing; [`charge_document`][extensions-resource-policy] bounds expanded selections, aliases, collection costs, and input value graphs after validation. Together they form a complementary two-phase shield protecting against parser stack overflow and AST execution complexity.
5. **Contracts restated in another medium:**
   The resource policy contract, budget defaults, walker algorithms, and fail-closed guarantees are codified across:
   - Code: [`django_strawberry_framework/extensions/resource_policy.py`][extensions-resource-policy], [`django_strawberry_framework/resource_policy.py`][resource-policy], [`django_strawberry_framework/schema.py`][schema], [`django_strawberry_framework/connection.py`][connection], [`django_strawberry_framework/list_field.py`][list-field], [`django_strawberry_framework/relay.py`][relay], [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers], [`django_strawberry_framework/conf.py`][conf];
   - Specifications: [`docs/SPECS/spec-047-resource_policy-0_0_14.md`][spec-047] (Decisions 2–4, 7–11, 13);
   - Test suites: [`tests/test_resource_policy.py`][test-resource-policy], [`examples/fakeshop/test_query/test_resource_policy_api.py`][test-fakeshop-resource-policy-api];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`GOAL.md`][goal].

### The single-edit-site test

- **Posited change 1 (Adding a new token delimiter kind to pre-parse depth tracking):** Support a new syntax delimiter in GraphQL lexer scanning.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/resource_policy.py::_STRUCTURAL_DELIMITER_PAIRS`][extensions-resource-policy].
  - *Site count:* 1.
- **Posited change 2 (Adjusting collection cost calculation for connection types):** Modify the structural heuristic determining whether an object type qualifies as a Relay connection.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/resource_policy.py::_is_connection_type`][extensions-resource-policy].
  - *Site count:* 1.
- **Posited change 3 (Modifying value depth charge calculation):** Alter how nested value depth is measured across container hierarchies.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/resource_policy.py::_ValueBudget.charge`][extensions-resource-policy].
  - *Site count:* 1.
- **Posited change 4 (Adjusting scalar byte calculation for binary payloads):** Add support for a new binary buffer type in leaf charging.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/resource_policy.py::_ValueBudget._charge_leaf`][extensions-resource-policy].
  - *Site count:* 1.
- **Posited change 5 (Altering context restoration during extension teardown):** Change how previous context attributes/keys are restored in nested execution environments.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/extensions/resource_policy.py::DjangoResourcePolicyExtension._restore_context_value`][extensions-resource-policy].
  - *Site count:* 1.

### Rejected candidates

1. **AST-based depth measurement vs pre-parse lexical depth scan:**
   - Disproved in [spec-047][spec-047] Decision 3. An AST-based depth check runs after `graphql-core`'s parser has already constructed the document AST. Deeply nested documents (e.g. 10,000 opening braces) exhaust CPython's interpreter recursion stack during parsing before any AST validator or extension can inspect the tree. Scanning tokens and bracket balance before parsing with `scan_document_text` protects the parser stack fail-closed.
2. **Charge-once memoization cache for value containers vs ancestor-path cycle detection:**
   - Disproved in [spec-047][spec-047] Decisions 4 & 13. A global charge-once cache causes variable reuse to evade input budgets: splicing the same list variable into two separate mutation fields would charge the list once, allowing the second field's relation IDs to execute unbudgeted. An ancestor-path cycle guard (`_closes_a_cycle`) terminates true circular object references while ensuring that every distinct reference path is fully charged.
3. **Merging `extensions/resource_policy.py` into `resource_policy.py`:**
   - Disproved. `resource_policy.py` provides the lightweight domain model (`ResourcePolicy`, `DEFAULT_RESOURCE_POLICY`, `resolve_resource_policy`, `check_deadline`, `bounded_rows`), free from GraphQL AST and Strawberry extension dependencies. `extensions/resource_policy.py` encapsulates engine-specific AST traversal and extension hooks. Separating them keeps core utilities decoupled and prevents unnecessary engine imports during schema configuration.
4. **Name-based argument classification vs GraphQL type-based classification:**
   - Disproved in [spec-047][spec-047] Decision 4. Name-based heuristics (e.g. guessing list semantics from argument names) fail open on custom argument names and falsely classify unrelated fields. Value classification in `_ValueBudget._charge_list_family` is strictly driven by the field's GraphQL input type definition in the schema, using argument name matching solely for the Relay node refetch convention (`ids`).

## Opportunities

None — `django_strawberry_framework/extensions/resource_policy.py` is a clean, 856-line, highly disciplined implementation. It cleanly separates pre-parse lexer scanning, AST structural charging, and iterative value-budget traversal with zero redundant logic, robust cycle detection, and complete fail-closed error handling.

## Judgment

Zero-edit review. `extensions/resource_policy.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked changes needed. Target file is clean and fully consolidated at root owners. Verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/extensions/resource_policy.py --review docs/dry/dry-file-extensions__resource_policy.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independently reviewed and verified Worker 1's DRY analysis of [`django_strawberry_framework/extensions/resource_policy.py`][extensions-resource-policy]:

1. **Resource policy enforcement boundaries and contract verification:**
   - Re-traced the execution enforcement pipeline across [`django_strawberry_framework/extensions/resource_policy.py`][extensions-resource-policy], [`django_strawberry_framework/resource_policy.py`][resource-policy], [`django_strawberry_framework/schema.py`][schema], [`django_strawberry_framework/connection.py`][connection], [`django_strawberry_framework/list_field.py`][list-field], [`django_strawberry_framework/relay.py`][relay], [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers], and [`django_strawberry_framework/utils/context.py`][utils-context].
   - Validated that [`scan_document_text`][extensions-resource-policy] performs a single pre-parse lexer sweep over raw document text in [`DjangoResourcePolicyExtension.on_operation`][extensions-resource-policy], enforcing [`ResourcePolicy.max_document_tokens`][resource-policy] and tracking bracket balances across [`_OPEN_TOKEN_KINDS`][extensions-resource-policy] and [`_CLOSE_TOKEN_KINDS`][extensions-resource-policy] against [`ResourcePolicy.max_depth`][resource-policy], while correctly deferring malformed document syntax diagnostics to `graphql-core`.
   - Validated context lifecycle management in [`DjangoResourcePolicyExtension.on_operation`][extensions-resource-policy]: active policy and execution deadlines are stashed on entry and faithfully restored in `finally` using [`_MISSING_CONTEXT_VALUE`][extensions-resource-policy] and [`_restore_context_value`][extensions-resource-policy], guaranteeing clean context isolation during nested schema executions.
   - Validated that [`charge_document`][extensions-resource-policy] performs an iterative AST walk in [`DjangoResourcePolicyExtension.on_execute`][extensions-resource-policy]:
     - Resolves root types for Queries, Mutations, and Subscriptions via [`_root_type`][extensions-resource-policy].
     - Expands fragments at every spread site with stack-tracked spread paths terminating cyclic fragment definitions safely.
     - Budgets field selections and aliases via [`_DocumentBudget`][extensions-resource-policy] against [`ResourcePolicy.max_selections`][resource-policy] and [`ResourcePolicy.max_aliases`][resource-policy].
     - Multiplies collection costs across nested collections via [`_collection_rows`][extensions-resource-policy] and [`_page_bound`][extensions-resource-policy], correctly exempting Relay connection `edges` lists via full structural shape validation in [`_is_connection_type`][extensions-resource-policy].
     - Resolves introspection fields via canonical graphql-core definitions in [`_field_definition`][extensions-resource-policy], ensuring introspection queries are budgeted rather than exempted.
   - Validated input value graph traversal in [`_ValueBudget`][extensions-resource-policy]:
     - Enforces [`ResourcePolicy.max_input_nodes`][resource-policy] and ancestor-path depth against [`ResourcePolicy.max_value_depth`][resource-policy].
     - Detects cyclic object references via [`_closes_a_cycle`][extensions-resource-policy] without suppressing distinct reference paths.
     - Accurately classifies input lists by GraphQL input type definition via [`_ValueBudget._charge_list_family`][extensions-resource-policy] across nested input objects, mutation relation IDs, query node refetch IDs, and membership items.
     - Budgets string and binary scalar bytes via [`_ValueBudget._charge_leaf`][extensions-resource-policy] and validates upload count, per-file size, and total size via [`_ValueBudget._charge_upload`][extensions-resource-policy], failing closed on unmeasurable file payloads.

2. **Probing matrix & single-edit-site verification:**
   - Verified that all 5 axes of the mandatory probing matrix are fully discharged with concrete evidence and domain justification.
   - Verified single-edit-site counts across all 5 posited change scenarios; each requires editing exactly 1 authoritative site.

3. **Coverage & test validation:**
   - Ran `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/extensions/resource_policy.py --review docs/dry/dry-file-extensions__resource_policy.md --include-constants`: confirmed all 39 target definitions are covered.
   - Ran test suite across [`tests/test_resource_policy.py`][test-resource-policy] and [`examples/fakeshop/test_query/test_resource_policy_api.py`][test-fakeshop-resource-policy-api]: all 140 resource policy tests passed.

Confirmed zero-edit review. Updated `Status: verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../GOAL.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-044]: ../SPECS/spec-044-debug_extension-0_0_14.md
[spec-046]: ../SPECS/spec-046-transport_security-0_0_14.md
[spec-047]: ../SPECS/spec-047-resource_policy-0_0_14.md
[spec-048]: ../SPECS/spec-048-secure_output_defaults-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../../django_strawberry_framework/conf.py
[connection]: ../../django_strawberry_framework/connection.py
[consumers]: ../../django_strawberry_framework/consumers.py
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[extensions-debug]: ../../django_strawberry_framework/extensions/debug.py
[extensions-error-policy]: ../../django_strawberry_framework/extensions/error_policy.py
[extensions-init]: ../../django_strawberry_framework/extensions/__init__.py
[extensions-resource-policy]: ../../django_strawberry_framework/extensions/resource_policy.py
[list-field]: ../../django_strawberry_framework/list_field.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[relay]: ../../django_strawberry_framework/relay.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py
[schema]: ../../django_strawberry_framework/schema.py
[utils-context]: ../../django_strawberry_framework/utils/context.py
[views]: ../../django_strawberry_framework/views.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-error-policy]: ../../tests/test_error_policy.py
[test-extensions-debug]: ../../tests/extensions/test_debug.py
[test-resource-policy]: ../../tests/test_resource_policy.py
[test-routers]: ../../tests/test_routers.py

<!-- examples/ -->
[test-fakeshop-error-policy-api]: ../../examples/fakeshop/test_query/test_error_policy_api.py
[test-fakeshop-resource-policy-api]: ../../examples/fakeshop/test_query/test_resource_policy_api.py

<!-- scripts/ -->

<!-- .venv/ -->
[strawberry-extension]: ../../.venv/lib/python3.14/site-packages/strawberry/extensions/base_extension.py

<!-- External -->
