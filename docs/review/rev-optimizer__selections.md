# Review: `django_strawberry_framework/optimizer/selections.py`

Status: verified

## Understanding

`django_strawberry_framework/optimizer/selections.py` provides the single selection-tree traversal substrate across both graphql-core AST nodes and Strawberry converted selection structures:

1. **Core Responsibilities & State**:
   - **AST Adapter**:
     - `ast_child_selections(node)`: Safely extracts child selection nodes from `node.selection_set.selections`, returning `()` on leaf nodes or fragment spreads.
     - `resolve_unvisited_fragment(node, fragments, visited_fragments, *, depth=None)`: Resolves `FragmentSpreadNode` to its `FragmentDefinitionNode`, guarding against circular spreads and duplicate visits. Supports optional `depth` keying `(frag_name, depth)` for depth-sensitive cache-relevant-variable extraction.
     - `directive_variable_names(node)`: Extracts variable names referenced in `@skip` / `@include` directives on AST nodes.
   - **AST-to-Converted-Selections Converter**:
     - `converted_selections_cache`: Per-execution `ContextVar[dict[Any, list[Any]] | None]` memoizing converted selection trees keyed on node ID(s) during `on_execute` lifecycles.
     - `ast_to_converted_selections(info, field_nodes)`: A faithful, anonymous-safe mirror of Strawberry's `convert_selections` that constructs `InlineFragment(type_condition=None)` instead of crashing when `node.type_condition` is missing on anonymous inline fragments (`... { f }`).
     - `prime_selected_fields(info)`: Pre-populates `info.__dict__["selected_fields"]` with anonymous-safe converted selections before Strawberry's cached property can invoke the crashing upstream converter.
   - **Converted-Selection Adapter**:
     - `is_fragment(selection)`: Duck-typed discriminator checking `hasattr(selection, "type_condition")` to identify both Strawberry fragments and walker `SimpleNamespace` clones.
     - `should_include(selection)`: Evaluates live `@skip` / `@include` directive values on converted selections.
     - `response_key(selection)` / `response_keys(selection)`: Determines response key preferring alias over field name, and reads `_optimizer_response_keys` on merged selections.
     - `included_field_selections(selections)`: Inlines fragment bodies and filters unincluded fields, with a fast-path returning the input list unchanged when no fragment or exclusion is present.
     - `named_children(selection, name)`: Direct child lookup by field name, recursing through fragment wrappers.
     - `with_runtime_prefix(selection, runtime_prefixes)` / `node_children_with_runtime_prefix(node_selection, *, runtime_prefixes)`: Deep-clones selections while annotating `_optimizer_runtime_prefixes`.
   - **Connection Vocabulary & Observability Predicates**:
     - `ConnectionFieldNames`: Dataclass capturing schema-resolved field names (`edges`, `node`, `page_info`, `total_count`, `has_next_page`).
     - `_CONNECTION_FIELD_PYTHON_NAMES`: Module-level precomputed tuple of `ConnectionFieldNames` attribute names in dataclass order.
     - `connection_field_names(info)`: Resolves connection vocabulary through `schema.config.name_converter.apply_naming_config`, falling back to `DEFAULT_CONNECTION_FIELD_NAMES` (`auto_camel_case=True`).
     - `connection_node_children(selection, *, runtime_prefixes, names=...)`: Unwraps `edges { node { ... } }` hierarchy and builds node path prefixes for the walker.
     - `direct_child_selected(selection_roots, name)`: Checks direct selection of a field name recursing only through fragment wrappers and gating on `should_include`.
     - `connection_total_count_selected(selection, *, names=...)`: Detects direct selection of `totalCount`.
     - `connection_has_next_page_selected(selection, *, names=...)`: Detects selection of `pageInfo { hasNextPage }`.
     - `connection_count_required(selection, *, names=...)`: Evaluates overall partition total count observability (`totalCount` or `pageInfo.hasNextPage`).

2. **System Role & Boundaries**:
   - Acts as the foundational selection abstraction shared by `optimizer/extension.py` (plan cache keys and reachable fragments), `optimizer/walker.py` (plan construction and field merging), `optimizer/nested_planner.py` (nested connection windows), and `connection.py` (resolve-time count observability and field priming).
   - Prevents drift between plan-time analysis and resolve-time behavior by centralizing fragment unwrapping, directive filtering, and schema naming rules.

## Verification

1. **Existing Permanent Tests**:
   - `tests/optimizer/test_selections.py`: 28 unit tests covering AST child selection, fragment deduplication, directive variable extraction, anonymous inline fragments, memoization lifecycles, connection field name conversions, prefix wrapping, and count observability.
   - `tests/optimizer/test_walker.py`, `tests/optimizer/test_extension.py`, and `tests/test_connection.py`: Integration and end-to-end coverage exercising selection traversal in plan generation, cache key computation, and connection slicing.

2. **Scratch Test Experiments**:
   - `docs/review/temp-tests/optimizer_selections/test_scratch.py` (3 passed in 1.60s):
     - Verified `connection_field_names` with custom `NameConverter.apply_naming_config`.
     - Verified `ast_to_converted_selections` handling of empty node lists with active/inactive memo.
     - Verified nested fragment descent and `@skip` / `@include` evaluation in `named_children`.

3. **Code Inspection**:
   - Identified that `connection_field_names` called `fields(ConnectionFieldNames)` dynamically on every invocation instead of iterating over the precomputed `_CONNECTION_FIELD_PYTHON_NAMES` tuple.

## Improvements

### High

None.

### Medium

None.

### Low

- **Observation:** `connection_field_names` invoked `fields(ConnectionFieldNames)` dynamically on each call rather than using the precomputed `_CONNECTION_FIELD_PYTHON_NAMES` module constant.
- **Evidence:** `_CONNECTION_FIELD_PYTHON_NAMES` was defined as `tuple(f.name for f in fields(ConnectionFieldNames))` at module load, but line 559 called `fields(ConnectionFieldNames)` anew on each resolution.
- **Impact:** Redundant dataclass field introspection and memory allocation per connection resolution, leaving a precomputed constant unused.
- **Recommendation:** Iterate over `_CONNECTION_FIELD_PYTHON_NAMES` in `connection_field_names`.
- **Proof:** Permanent test `test_connection_field_python_names_matches_dataclass_fields` in `tests/optimizer/test_selections.py`.

## Summary

`django_strawberry_framework/optimizer/selections.py` is the unified selection-tree traversal layer. It cleanly abstracts AST and converted selection shapes, handles anonymous inline fragments without upstream crashes, memoizes conversions across fallback connection rows, and aligns schema-driven connection naming. A minor efficiency cleanup was implemented to use the precomputed `_CONNECTION_FIELD_PYTHON_NAMES` constant.

## Implementation (Worker 1)

- **Changed files**:
  - `django_strawberry_framework/optimizer/selections.py`: Iterated over `_CONNECTION_FIELD_PYTHON_NAMES` in `connection_field_names` rather than calling `fields(ConnectionFieldNames)` on each invocation.
  - `tests/optimizer/test_selections.py`: Added `test_connection_field_python_names_matches_dataclass_fields` pinning `_CONNECTION_FIELD_PYTHON_NAMES` against dataclass fields.
- **Permanent tests**:
  - `tests/optimizer/test_selections.py::test_connection_field_python_names_matches_dataclass_fields` pins that `_CONNECTION_FIELD_PYTHON_NAMES` matches `ConnectionFieldNames` field names and order.
  - Full focused suite `tests/optimizer/test_selections.py` (29 passed in 1.54s).
- **Scratch verification**:
  - `docs/review/temp-tests/optimizer_selections/test_scratch.py` (3 passed in 1.60s).
- **Formatter and linter**:
  - `uv run ruff format .` and `uv run ruff check --fix .` ran cleanly (0 errors).
- **Evidence for rejected findings**: None.
- **Changelog**: Does not merit a standalone changelog entry (internal micro-optimization / refactor).

## Independent verification (Worker 2)

- **Behavioral Re-trace**:
  - Re-traced AST adapter functions (`ast_child_selections`, `resolve_unvisited_fragment`, `directive_variable_names`) confirming graceful handling of leaf nodes, cyclic fragments, depth-keyed fragment traversal, and strict filtering of `@skip` / `@include` variable references.
  - Re-traced AST-to-converted-selections converter (`converted_selections_cache`, `ast_to_converted_selections`, `prime_selected_fields`) confirming anonymous inline fragment resilience (`type_condition=None`), caching lifecycle on `ContextVar`, and idempotent priming of `info.__dict__["selected_fields"]`.
  - Re-traced converted-selection adapter utilities (`is_fragment`, `should_include`, `response_key`, `response_keys`, `included_field_selections`, `named_children`, `with_runtime_prefix`, `node_children_with_runtime_prefix`) confirming fragment inlining, directive evaluation, prefix cloning on field leaves, and direct-child lookup recursing through fragments.
  - Re-traced connection vocabulary and count observability (`ConnectionFieldNames`, `_CONNECTION_FIELD_PYTHON_NAMES`, `connection_field_names`, `connection_node_children`, `direct_child_selected`, `connection_total_count_selected`, `connection_has_next_page_selected`, `connection_count_required`) confirming schema-configured name translation, prefix accumulation across `edges { node }`, and directive-gated count observability detection.
- **Code Inspection & Scoped Diff**:
  - Inspected `git diff HEAD -- django_strawberry_framework/optimizer/selections.py tests/optimizer/test_selections.py`.
  - Confirmed the fix accurately replaces `fields(ConnectionFieldNames)` with iteration over precomputed `_CONNECTION_FIELD_PYTHON_NAMES`.
  - Confirmed the new permanent test `test_connection_field_python_names_matches_dataclass_fields` strictly pins `_CONNECTION_FIELD_PYTHON_NAMES` against dataclass field names and ordering.
- **Test Executions**:
  - Permanent test suite: `uv run pytest tests/optimizer/test_selections.py --no-cov` (29 passed in 1.48s).
  - Extended scratch test suite: `uv run pytest docs/review/temp-tests/optimizer_selections/test_scratch.py --no-cov` (8 passed in 1.49s) covering:
    - Custom schema name converter application across all fields.
    - Memoization and empty AST node handling.
    - Deep nested fragment resolution with `@skip` / `@include` directives.
    - Circular fragment resolution and depth-indexed visit caching.
    - Defensive extraction of directive variable names.
    - Response-key prefix accumulation over aliased `edges` and `node` fields.
    - Directive-gated totalCount / hasNextPage selection.
    - Defensive no-op and idempotency of `prime_selected_fields`.
  - Connected consumers integration suite: `uv run pytest tests/optimizer/test_walker.py tests/optimizer/test_extension.py tests/test_connection.py --no-cov` (421 passed in 9.83s).
- **Conclusion**: Target implementation is verified, sound, and fully conformant with all contracts and quality criteria.
