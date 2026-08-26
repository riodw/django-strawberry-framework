# Review: `django_strawberry_framework/extensions/resource_policy.py`

Status: verified


## Understanding

`django_strawberry_framework/extensions/resource_policy.py` implements the request-side execution resource budget enforcement engine (`DjangoResourcePolicyExtension`, `spec-047`). It evaluates and enforces the immutable `ResourcePolicy` budget across three distinct request lifecycle phases before database work or resolvers can execute:

1. **Pre-Parse Text Scan (`scan_document_text` in `on_operation`):**
   - Single linear lexer sweep (`graphql.language.lexer.Lexer`) over the raw document text.
   - Evaluates token count (`max_document_tokens`) and structural bracket nesting balance (`max_depth`) across braces (`{}`), parentheses (`()`), and brackets (`[]`).
   - Runs strictly before AST parsing to prevent recursive-descent parser stack exhaustion.
   - Swallows syntax errors if within token/depth limits to let graphql-core report precise syntax errors; rejects with `ResourceLimitExceeded` if size or depth limits are breached before malformed tokens.
2. **Iterative Document Budget Walk (`charge_document` in `on_execute`):**
   - Single iterative, fragment-expanding AST traversal over the validated GraphQL document.
   - Evaluates named operations (or all operations if unnamed), populating variable defaults when variables are omitted.
   - Expands fragment spreads at every spread site and tracks ancestor fragment spread paths (`frozenset[str]`) to terminate cyclic fragment graphs safely without recursion.
   - Handles inline fragments with or without type conditions.
   - Charges expanded field selections (`max_selections`) and aliased selections (`max_aliases`).
   - Resolves introspection meta-fields (`__schema`, `__type`, `__typename`) to ensure introspection queries cannot evade selection, depth, or collection bounds.
   - Calculates multiplicative collection row costs (`_collection_rows`, `max_collection_cost`) across nested collections and connection fields (`_page_bound`), exempting a connection's own `edges` list to avoid double-charging the page.
3. **Iterative Value Budget Walk (`_ValueBudget` in `on_execute`):**
   - Iterative stack-based walk over all field arguments (literals, variables, and spliced variable trees).
   - Cycle-guarded against the value's ancestor path using object identity (`is`), preventing infinite loops on self-referential input structures while correctly charging multi-referenced containers once per reference.
   - Bounds total input nodes (`max_input_nodes`), nesting depth (`max_value_depth`), and container widths (`max_container_width`).
   - Classifies list inputs by item type:
     - `GraphQLInputObjectType` -> `max_nested_rows`
     - `GraphQLID` in mutations -> `max_relation_ids_per_mutation` and `max_relation_ids_total`
     - `GraphQLID` under `ids` argument in queries -> `max_node_ids`
     - Other lists -> `max_membership_items`
   - Charges synthetic single-item containers on scalar-to-list coercion.
   - Bounds scalar payload byte length (`max_scalar_bytes`) for string (UTF-8) and binary (`bytes`, `bytearray`, `memoryview` via `nbytes`) leaves.
   - Validates and bounds file uploads (`max_upload_count`, `max_upload_file_bytes`, `max_upload_total_bytes`), strictly rejecting unmeasurable, negative, boolean, or non-integral file sizes.
4. **Extension Lifecycle (`DjangoResourcePolicyExtension`):**
   - Subclasses Strawberry's `SchemaExtension`.
   - `_resolved_policy()` resolves explicit policy > schema policy > `DEFAULT_RESOURCE_POLICY`.
   - `on_operation()` saves prior context values (`DST_RESOURCE_POLICY`, `DST_RESOURCE_DEADLINE`), stashes the resolved policy and monotonic deadline on `context`, runs `scan_document_text`, yields to execution, and restores prior context state in `finally`.
   - `on_execute()` runs `charge_document` when a parsed document is present.

## Verification

1. **Traced connections across callers and consumers:**
   - `django_strawberry_framework/__init__.py`: exports `DjangoResourcePolicyExtension`.
   - `django_strawberry_framework/extensions/__init__.py`: re-exports `DjangoResourcePolicyExtension`.
   - `django_strawberry_framework/schema.py`: installs `DjangoResourcePolicyExtension` automatically in `_with_resource_policy_extension`, deduplicating consumer-supplied entries.
   - `django_strawberry_framework/resource_policy.py`: defines `ResourcePolicy`, context threading (`stash_resource_policy`), deadlines (`DST_RESOURCE_DEADLINE`), and `ResourceLimitExceeded`.
2. **Examined existing test suites:**
   - `tests/test_resource_policy.py` (111 tests): covers pre-parse scan (token/depth limits, delimiter families, malformed docs), AST walk (operations, fragment cycles, inline fragments, introspection fields, connection shape detection), value budget (untyped containers, scalar list coercion, shared/equal containers, cycles, value depth, upload bounds, binary scalars, variable defaults), and extension lifecycle (explicit vs schema policy, missing document, context cleanup).
   - `examples/fakeshop/test_query/test_resource_policy_api.py` (37 tests): live HTTP `/graphql/` acceptance tests verifying pre-parse scan, expanded AST bounds, variable value budget, introspection, collection bounds, deadline rejections, zero ORM work on rejection, and transport error formatting.
3. **Focused test execution:**
   - `uv run pytest tests/test_resource_policy.py --no-cov` passed (111/111 passed).
   - `uv run pytest examples/fakeshop/test_query/test_resource_policy_api.py --no-cov` passed (37/37 passed).
   - Coverage on `django_strawberry_framework/extensions/resource_policy.py` is 100% (192/192 statements).
4. **Scratch verification:**
   - `docs/review/temp-tests/extensions__resource_policy/test_scratch_resource_policy.py` passed (8/8 passed), verifying pre-parse scan edge cases, cycle detection, value budget list family classification, upload/scalar leaves, document budget selection/alias/cost charging, connection shape detection, and extension context preservation.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/extensions/resource_policy.py` provides a comprehensive, non-recursive, and fail-closed request-level resource enforcement engine. It cleanly separates pre-parse text scanning, iterative AST document charging, and value budget evaluation. All bounds are enforced before resolver execution and database work. The extension maintains strict context isolation across operations, with 100% test coverage and robust error handling.

## Implementation (Worker 1)

None — zero-edit cycle.

- **Changed files and necessity:** None (zero-edit cycle). Scoped diff against cycle baseline (`HEAD` = `12779c99`) for `django_strawberry_framework/extensions/resource_policy.py` is empty.
- **Permanent tests and pinned behavior:**
  - `tests/test_resource_policy.py` (111 tests) pins pre-parse scan, fragment expansion and cycle termination, introspection meta-field charging, connection edge exemption, value budget traversal, list family classification, scalar/upload limits, and extension lifecycle.
  - `examples/fakeshop/test_query/test_resource_policy_api.py` (37 tests) pins live HTTP acceptance tests for all resource policy bounds, zero ORM query execution on rejection, and transport error consistency.
- **Scratch or focused verification:**
  - `docs/review/temp-tests/extensions__resource_policy/test_scratch_resource_policy.py` passed (8/8 tests).
  - `tests/test_resource_policy.py` passed (111/111 tests).
  - `examples/fakeshop/test_query/test_resource_policy_api.py` passed (37/37 tests).
- **Formatter and linter results:**
  - `uv run ruff check django_strawberry_framework/extensions/resource_policy.py docs/review/temp-tests/extensions__resource_policy/test_scratch_resource_policy.py` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/extensions/resource_policy.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — zero-edit cycle on production code, existing behavior unchanged.

## Independent verification (Worker 2)

- **Scoped diff confirmation:** Verified that `git diff 12779c99 -- django_strawberry_framework/extensions/resource_policy.py` is empty (zero-edit cycle).
- **Behavioral re-trace & verification:**
  - `scan_document_text`: Verified single-pass lexer sweep (`Lexer(Source(query))`) counting tokens and structural bracket nesting across `{}`, `()`, and `[]`. Rejection triggers immediately on limit breach before malformed tokens; syntax errors within bounds are swallowed to allow GraphQL parser to generate standard diagnostics.
  - `_DocumentBudget` & `charge_document`: Verified non-recursive iterative AST walk expanding fragment definitions and inline fragments with cycle guards tracking fragment spread paths (`frozenset[str]`). Verified expanded selection and alias charging, introspection meta-field resolution (`__typename`, `__schema`, `__type`), and multiplicative collection cost evaluation.
  - Connection bounds & edge exemption: Verified `_is_connection_type` structural edge validation requiring `edges` list of object type carrying `node` and `cursor`. Confirmed connection's own `edges` list is exempted from secondary list charging, and connection page bounds resolve from `first`/`last` arguments clamped to `max_page_size`.
  - `_ValueBudget`: Verified iterative stack-based value walk cycle-guarded via container ancestor path object identity (`is`), charging multi-referenced containers once per reference while preventing loops on cyclic structures. Confirmed list family classification: `GraphQLInputObjectType` -> `max_nested_rows`, `GraphQLID` in mutations -> `max_relation_ids_per_mutation` / `max_relation_ids_total`, `GraphQLID` in query `ids` -> `max_node_ids`, and other lists -> `max_membership_items`. Verified scalar byte bounding on string (UTF-8) and binary types (`nbytes`), and upload validation with strict non-negative integral size enforcement.
  - `DjangoResourcePolicyExtension`: Verified schema extension installation, policy resolution precedence (explicit > schema > default), context threading under `DST_RESOURCE_POLICY` / `DST_RESOURCE_DEADLINE`, and guaranteed context restoration in `finally`.
- **Permanent tests executed:**
  - `tests/test_resource_policy.py` (111 passed).
  - `examples/fakeshop/test_query/test_resource_policy_api.py` (37 passed).
- **Scratch verification:**
  - `docs/review/temp-tests/extensions__resource_policy/test_scratch_resource_policy.py` (8 passed).
- **Outcome:** Verified. No defects, regressions, or contract gaps found.

