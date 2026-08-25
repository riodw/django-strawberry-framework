# DRY review: `django_strawberry_framework/optimizer/selections.py`

Status: verified

## System trace

`django_strawberry_framework/optimizer/selections.py` is the unified selection-tree traversal substrate and AST / converted-selection adapter layer for the optimizer subsystem ([spec-002][spec-002], [spec-004][spec-004], [spec-010][spec-010], [spec-016][spec-016], [spec-020][spec-020], [spec-030][spec-030], [spec-033][spec-033], [spec-035][spec-035], [spec-051][spec-051], [spec-063][spec-063]).

The optimizer reads GraphQL selections in two primary representations:
1. graphql-core **AST** nodes ([`optimizer/extension.py`][optimizer-extension] — plan-cache key construction, reachable-fragment collection, cache-relevant variable extraction).
2. Strawberry **converted** selection objects ([`optimizer/walker.py`][optimizer-walker] + [`optimizer/nested_planner.py`][optimizer-nested-planner] + [`connection.py`][connection] — plan building, nested connection windows, count observation).

Both representations address the same core query semantics: child-selection iteration, recursive fragment descent, `@skip` and `@include` directive evaluation, response-key preservation, and `edges { node { ... } }` unwrapping. `optimizer/selections.py` serves as the single source of truth for these operations, deliberately split into two explicit adapters rather than an over-generic polymorphic walker:

1. **AST -> Converted Selection Adapter & Anonymous Fragment Hardening:**
   - [`converted_selections_cache`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::converted_selections_cache`): Task-local [`ContextVar`][stdlib-contextvars] providing per-execution memoization of converted selection trees keyed by field node object IDs, collapsing N per-row conversions to one during fallback connection resolution.
   - [`ast_to_converted_selections`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::ast_to_converted_selections`): Faithful, anonymous-safe mirror of Strawberry's `convert_selections`. For anonymous inline fragments (`... { f }` with `type_condition is None`), it builds [`InlineFragment`][strawberry-nodes] with `type_condition=None` instead of dereferencing `node.type_condition.name.value`, preventing an unhandled `AttributeError` on spec-valid queries. Builds native Strawberry [`SelectedField`][strawberry-nodes], [`FragmentSpread`][strawberry-nodes], and [`InlineFragment`][strawberry-nodes] dataclasses with converted arguments and directives.
   - [`prime_selected_fields`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::prime_selected_fields`): Pre-seeds Strawberry `Info.selected_fields` in `info.__dict__["selected_fields"]` before any resolver reads the cached property, ensuring Strawberry's internal connection routines (`should_resolve_list_connection_edges`) and framework observers receive anonymous-safe converted selections.

2. **AST Adapter (graphql-core Nodes):**
   - [`ast_child_selections`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::ast_child_selections`): Returns an AST node's selection-set children as a tuple or `()` for leaf/spread nodes, centralizing child iteration across AST walkers.
   - [`resolve_unvisited_fragment`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::resolve_unvisited_fragment`): Cycle-safe fragment spread resolver returning [`FragmentDefinitionNode`][graphql-ast]. Supports both document-level fragment collection (keyed by fragment name) and depth-sensitive variable walks (keyed by `(frag_name, depth)`).
   - [`directive_variable_names`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::directive_variable_names`): Extracts variable names referenced in the `if` argument of `@skip` and `@include` directives on AST nodes.

3. **Converted-Selection Adapter & Tree Normalization:**
   - [`is_fragment`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::is_fragment`): Single fragment discriminator duck-typed on `hasattr(selection, "type_condition")`, matching Strawberry fragments and synthesized [`SimpleNamespace`][stdlib-types] shells alike.
   - [`should_include`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::should_include`): Evaluates `@skip(if: true)` and `@include(if: false)` directives on converted selections with an empty-directive fast path.
   - [`response_key`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::response_key`): Resolves the GraphQL response key (`alias` or `name`).
   - [`response_keys`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::response_keys`): Resolves all response keys represented by an aliased or merged selection (`_optimizer_response_keys` or single response key).
   - [`included_field_selections`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::included_field_selections`): Flattens and inlines fragment selection bodies while dropping directive-excluded selections; returns input list unmodified on fast path when no fragments or directive exclusions exist.
   - [`named_children`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::named_children`): Returns included direct children matching `name`, descending recursively through fragment wrappers only.
   - [`with_runtime_prefix`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::with_runtime_prefix`): Clones selection shells, descending through fragments to attach `_optimizer_runtime_prefixes` onto field leaves.
   - [`node_children_with_runtime_prefix`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::node_children_with_runtime_prefix`): Clones included children of a node selection with connection-aware runtime prefixes.

4. **Connection Vocabulary & Observability Predicates:**
   - [`ConnectionFieldNames`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::ConnectionFieldNames`): Immutable frozen dataclass holding schema-rendered names for `edges`, `node`, `page_info`, `total_count`, and `has_next_page`.
   - [`DEFAULT_CONNECTION_FIELD_NAMES`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::DEFAULT_CONNECTION_FIELD_NAMES`): Constant default vocabulary matching Strawberry's standard camelCase naming.
   - [`_CONNECTION_FIELD_PYTHON_NAMES`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::_CONNECTION_FIELD_PYTHON_NAMES`): Constant tuple `("edges", "node", "page_info", "total_count", "has_next_page")` defining the python attribute names transformed by `NameConverter`.
   - [`connection_field_names`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::connection_field_names`): Resolves connection field names through `schema_config_from_info(info).name_converter.apply_naming_config` or falls back to `DEFAULT_CONNECTION_FIELD_NAMES`.
   - [`connection_node_children`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::connection_node_children`): Unwraps `edges { node { ... } }` hierarchy across aliased branches and fragments, accumulating response-key runtime prefixes for child fields.
   - [`direct_child_selected`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::direct_child_selected`): Evaluates whether a named field is selected as a direct child, recursing through fragment wrappers only and filtering via `should_include`.
   - [`connection_total_count_selected`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::connection_total_count_selected`): Evaluates whether `totalCount` is selected as a direct child of a connection selection.
   - [`connection_has_next_page_selected`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::connection_has_next_page_selected`): Evaluates whether `pageInfo { hasNextPage }` is selected under a connection selection.
   - [`connection_count_required`][optimizer-selections] (`django_strawberry_framework/optimizer/selections.py::connection_count_required`): Unified count-observability predicate combining `connection_total_count_selected` or `connection_has_next_page_selected`.

Connected behavior examined:
- [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension]: Uses `ast_child_selections`, `resolve_unvisited_fragment`, and `directive_variable_names` for plan-cache key construction; initializes `converted_selections_cache`; uses `connection_node_children` and `connection_field_names` for root connection optimization; uses `named_children` and `node_children_with_runtime_prefix` for mutation payload extraction.
- [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker]: Uses `included_field_selections`, `is_fragment`, `named_children`, `node_children_with_runtime_prefix`, `response_key`, `response_keys`, `should_include`, and `with_runtime_prefix` for level descent, alias merging, directive filtering, and runtime prefix propagation.
- [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner]: Uses `ConnectionFieldNames`, `connection_field_names`, `connection_node_children`, `connection_total_count_selected`, `connection_has_next_page_selected`, and `response_keys` to plan nested connection prefetch querysets, detect count/probe fetch modes, and unwrap node selections.
- [`django_strawberry_framework/connection.py`][connection]: Calls `prime_selected_fields`, `connection_field_names`, `connection_total_count_selected`, and `connection_has_next_page_selected` to resolve total counts and window slices at runtime.
- [`django_strawberry_framework/utils/typing.py`][utils-typing]: Supplies `schema_config_from_info` consumed by `connection_field_names`.
- [`tests/optimizer/test_selections.py`][test-optimizer-selections]: Dedicated unit test suite verifying AST adapters, converted-selection adapters, memoization, anonymous/named fragments, spreads, priming, directive filtering, and custom schema name converters.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/optimizer/selections.py --include-constants`):
- Parsed 1 target file, 725 lines.
- Inventory of symbols (22 definitions):
  - 2 constants: [`DEFAULT_CONNECTION_FIELD_NAMES`][optimizer-selections], [`_CONNECTION_FIELD_PYTHON_NAMES`][optimizer-selections].
  - 1 class: [`ConnectionFieldNames`][optimizer-selections].
  - 19 functions: [`ast_to_converted_selections`][optimizer-selections], [`prime_selected_fields`][optimizer-selections], [`ast_child_selections`][optimizer-selections], [`resolve_unvisited_fragment`][optimizer-selections], [`directive_variable_names`][optimizer-selections], [`is_fragment`][optimizer-selections], [`should_include`][optimizer-selections], [`response_key`][optimizer-selections], [`response_keys`][optimizer-selections], [`included_field_selections`][optimizer-selections], [`named_children`][optimizer-selections], [`with_runtime_prefix`][optimizer-selections], [`node_children_with_runtime_prefix`][optimizer-selections], [`connection_field_names`][optimizer-selections], [`connection_node_children`][optimizer-selections], [`direct_child_selected`][optimizer-selections], [`connection_total_count_selected`][optimizer-selections], [`connection_has_next_page_selected`][optimizer-selections], [`connection_count_required`][optimizer-selections].
  - Plus module-level [`converted_selections_cache`][optimizer-selections] ContextVar.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `optimizer/selections.py` bridges graphql-core AST nodes, Strawberry converted selections, and custom `SimpleNamespace` shapes.
   - AST vs. Converted Selection Alignment: AST cache-key building in [`optimizer/extension.py`][optimizer-extension] and converted-selection planning in [`optimizer/walker.py`][optimizer-walker] / [`optimizer/nested_planner.py`][optimizer-nested-planner] process identical GraphQL semantics (`@skip` / `@include`, fragments, response keys, `edges { node }` unwrapping). `selections.py` is the single source of truth for both representations, preventing cache-key / execution drift.
   - Schema Naming Configuration (`auto_camel_case`): Dynamic vocabulary resolution in [`connection_field_names`][optimizer-selections] guarantees that connection field matching in plan-time window derivation ([`nested_planner.py`][optimizer-nested-planner]) and runtime resolve execution ([`connection.py`][connection]) share the exact same names across `auto_camel_case=True`, `auto_camel_case=False`, and custom `apply_naming_config` transformations.
   - Relay Connections & Mutation Payloads: Root connection extraction ([`_connection_node_child_selections`][optimizer-extension]), nested connection planning ([`plan_connection_relation`][optimizer-nested-planner]), and mutation payload extraction ([`mutation_payload_child_selections`][optimizer-extension]) share the identical underlying extraction primitives ([`named_children`][optimizer-selections], [`node_children_with_runtime_prefix`][optimizer-selections], [`connection_node_children`][optimizer-selections], [`response_key`][optimizer-selections]). Zero cross-flavor policy duplication.

2. **Sync and async twins:**
   Zero duplication. AST inspection, converted selection transformation, directive evaluation, and tree flattening in `selections.py` are purely synchronous, deterministic, side-effect-free operations.
   - Context Isolation: [`converted_selections_cache`][optimizer-selections] utilizes Python's [`ContextVar`][stdlib-contextvars], guaranteeing thread-safe and task-local memoization across synchronous execution and concurrent asynchronous coroutines.
   - Resolver Protection: [`prime_selected_fields`][optimizer-selections] protects both sync (`resolve_connection`) and async (`a_resolve_connection`) resolvers against Strawberry's internal `AttributeError` on anonymous fragments by pre-populating `info.__dict__["selected_fields"]`.

3. **Derived rather than repeated knowledge:**
   - Response Keys: Derived authoritatively via [`response_key`][optimizer-selections] (`alias or name`) and preserved across merged selections via [`response_keys`][optimizer-selections].
   - Count Observability: [`connection_count_required`][optimizer-selections] derives count requirement dynamically from [`connection_total_count_selected`][optimizer-selections] and [`connection_has_next_page_selected`][optimizer-selections], which in turn derive existence via [`direct_child_selected`][optimizer-selections].
   - Connection Vocabulary: Derived dynamically from `NameConverter` via [`_CONNECTION_FIELD_PYTHON_NAMES`][optimizer-selections] rather than hardcoding string literals across multiple modules.
   - Fragment Classification: [`is_fragment`][optimizer-selections] tests `hasattr(selection, "type_condition")`, unifying typed fragments (`type_condition="TypeName"`) and anonymous fragments (`type_condition=None`) under a single polymorphic contract. No repeated knowledge.

4. **Inverse and round-trip pairs:**
   - AST Conversion vs. Fragment Expansion: [`ast_to_converted_selections`][optimizer-selections] faithfully translates AST node hierarchies into Strawberry dataclass trees, while [`included_field_selections`][optimizer-selections] flattens and inlines fragment selection bodies into linear field lists for walker alias merging.
   - Context Memo Lifecycle: [`converted_selections_cache`][optimizer-selections] is initialized via `set({})` in `DjangoOptimizerExtension.on_execute` and restored via `reset(token)` in `finally`, providing symmetric setup and teardown.
   - Cached Property Priming: [`prime_selected_fields`][optimizer-selections] intercepts lazy evaluation of `info.selected_fields` by seeding the underlying dictionary slot `info.__dict__["selected_fields"]`, ensuring cached property readers receive the sanitized conversion idempotently.

5. **Contracts restated in another medium:**
   The selection traversal and anonymous fragment contracts are codified across:
   - Code: [`django_strawberry_framework/optimizer/selections.py`][optimizer-selections], [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension], [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker], [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner], [`django_strawberry_framework/connection.py`][connection], [`django_strawberry_framework/utils/typing.py`][utils-typing];
   - Specifications: [`docs/SPECS/spec-002-optimizer-0_0_2.md`][spec-002], [`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004], [`docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md`][spec-010], [`docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md`][spec-016], [`docs/SPECS/appx/spec-020-list_field-0_0_7-rationale.md`][spec-020], [`docs/SPECS/appx/spec-030-connection_field-0_0_9-terms.csv`][spec-030], [`docs/SPECS/spec-033-connection_optimizer-0_0_9.md`][spec-033], [`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`][spec-035], [`docs/SPECS/spec-051-boundary_dry_squeeze-0_0_15.md`][spec-051], [`docs/SPECS/spec-063-structural_templates-0_1_6.md`][spec-063];
   - Test suites: [`tests/optimizer/test_selections.py`][test-optimizer-selections] (dedicated unit tests for AST/converted adapters, memoization, anonymous/named fragments, spreads, priming, directive filtering, and custom name converters), [`tests/optimizer/test_extension.py`][test-optimizer-extension], [`tests/optimizer/test_walker.py`][test-optimizer-walker], [`tests/test_relay_connection.py`][test-relay-connection], [`examples/fakeshop/test_query/test_library_api.py`][example-test-library], [`examples/fakeshop/test_query/test_glossary_api.py`][example-test-glossary];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Adding support for a new inclusion directive such as `@includeIf` or `@skipIf`):**
  - *Production ownership count:* 2 sites in [`django_strawberry_framework/optimizer/selections.py`][optimizer-selections] ([`directive_variable_names`][optimizer-selections] for AST inspection and [`should_include`][optimizer-selections] for converted-selection evaluation).
  - *Propagation count:* 0 in production code.
- **Posited change 2 (Adding a new Relay structural field to schema-configured connection field names, e.g. `total_pages`):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/optimizer/selections.py`][optimizer-selections] (declaring the field with default camelCase value in [`ConnectionFieldNames`][optimizer-selections]). `DEFAULT_CONNECTION_FIELD_NAMES` instantiates `ConnectionFieldNames()` without arguments, and `_CONNECTION_FIELD_PYTHON_NAMES` derives from `dataclasses.fields(ConnectionFieldNames)`.
  - *Propagation count:* 1 site in tests (`tests/optimizer/test_selections.py`).
- **Posited change 3 (Modifying the anonymous inline fragment type condition representation):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/optimizer/selections.py`][optimizer-selections] ([`ast_to_converted_selections`][optimizer-selections]).
  - *Propagation count:* 0 in production code.
- **Posited change 4 (Changing the fragment detection heuristic for converted selections):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/optimizer/selections.py`][optimizer-selections] ([`is_fragment`][optimizer-selections]).
  - *Propagation count:* 0 in production code (all downstream callers in `walker.py`, `extension.py`, `nested_planner.py`, and `connection.py` consume `is_fragment`).
- **Posited change 5 (Altering count observability criteria, e.g. adding a new observer field under `pageInfo`):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/optimizer/selections.py`][optimizer-selections] ([`connection_count_required`][optimizer-selections] or a sibling helper).
  - *Propagation count:* 0 in production code.

### Rejected candidates

1. **Merging AST and converted-selection adapters into a single polymorphic visitor:**
   - Disproved per [spec-035][spec-035] and [spec-051][spec-051]. AST nodes from graphql-core and converted selections from Strawberry exhibit distinct object models, accessor patterns, and lifecycles (AST nodes carry raw token values and location metadata; converted selections carry Python-typed arguments and resolved directives). Maintaining two explicit, decoupled adapters sharing common policy functions keeps the abstraction clear and avoidant of dynamic dispatch overhead.
2. **Relying directly on Strawberry's `convert_selections` without the anonymous fragment patch:**
   - Disproved per [spec-035][spec-035] (G3). Strawberry's `InlineFragment.from_node` crashes with `AttributeError` when encountering spec-valid anonymous inline fragments `... { f }` because it unconditionally accesses `node.type_condition.name.value`. Supplying `ast_to_converted_selections` and `prime_selected_fields` guarantees spec compliance without waiting for upstream releases.
3. **Inlining connection structural field name literals (`"totalCount"`, `"hasNextPage"`, `"pageInfo"`) directly in predicates:**
   - Disproved per [spec-033][spec-033] and [spec-051][spec-051]. Hardcoded literals break under `auto_camel_case=False` or custom `NameConverter` implementations, causing count observers to report false negatives and crashing totalCount resolvers. Centralizing vocabulary resolution in `connection_field_names` ensures consistency across the entire framework.
4. **Mutating converted selection lists in-place during fragment inlining in `included_field_selections`:**
   - Disproved per [spec-035][spec-035]. Converted selections may be shared across multiple execution rows or cached in `converted_selections_cache`. Returning a freshly built list during inlining (or passing through the original list when already flat) guarantees immutability and thread safety.

## Opportunities

- **Candidate 1: Colocate default GraphQL names and derive Python field names in `ConnectionFieldNames`**: Implemented. Colocates camelCase default values in `ConnectionFieldNames` dataclass field definitions, defines `DEFAULT_CONNECTION_FIELD_NAMES = ConnectionFieldNames()`, and derives `_CONNECTION_FIELD_PYTHON_NAMES` from `dataclasses.fields(ConnectionFieldNames)`, reducing the production ownership count of adding a connection structural field from 3 to 1.

## Judgment

Verified. `optimizer/selections.py` establishes single authoritative ownership over selection traversal and connection field vocabulary. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold across all posited changes.

## Implementation (Worker 1)

1. Consolidated `ConnectionFieldNames` defaults and derived `_CONNECTION_FIELD_PYTHON_NAMES` via `dataclasses.fields(ConnectionFieldNames)`.
2. Verified permanent unit tests in [`tests/optimizer/test_selections.py`][test-optimizer-selections].
3. Formatted and linted cleanly with `ruff`. Verified full definition coverage with `export_dry_review.py check`.

## Independent verification (Worker 2)

I have independently re-traced the selection-tree traversal substrate and adapter layer in [`django_strawberry_framework/optimizer/selections.py`][optimizer-selections] across its downstream consumers in [`optimizer/extension.py`][optimizer-extension], [`optimizer/walker.py`][optimizer-walker], [`optimizer/nested_planner.py`][optimizer-nested-planner], and [`connection.py`][connection].

### Verification findings and boundary analysis

1. **AST / Converted-Selection Dual Representation:**
   - Evaluated the architectural rationale for separating the AST adapter (`ast_child_selections`, `resolve_unvisited_fragment`, `directive_variable_names`) from the converted-selection adapter (`is_fragment`, `should_include`, `response_key`, `response_keys`, `included_field_selections`, `named_children`, `with_runtime_prefix`, `node_children_with_runtime_prefix`, `connection_node_children`, `direct_child_selected`).
   - Confirmed that unifying the directive rules (`@skip` / `@include`) and fragment traversal policies across both layers prevents cache-key and execution plan drift without resorting to heavy polymorphic walker abstractions.
   - Verified that `resolve_unvisited_fragment` handles both document-level fragment collection (keying by fragment name) and depth-sensitive cache-key walks (keying by `(frag_name, depth)`), preventing infinite cycles while ensuring variable extractions at distinct query depths are preserved.

2. **Anonymous Inline Fragment Hardening & Memoization:**
   - Verified [`ast_to_converted_selections`][optimizer-selections]: inspected Strawberry's internal `InlineFragment.from_node` failure mode on `... { field }` (missing `type_condition.name.value`). Confirmed `ast_to_converted_selections` sets `type_condition=None` cleanly and creates Strawberry dataclass instances (`SelectedField`, `InlineFragment`, `FragmentSpread`), ensuring full interoperability with Strawberry internals (`should_resolve_list_connection_edges`).
   - Verified [`prime_selected_fields`][optimizer-selections]: confirmed that intercepting `info.__dict__["selected_fields"]` before `info.selected_fields` is evaluated prevents upstream crashes during connection resolution. Verified idempotency and safe no-ops when field nodes are absent or when `selected_fields` is already populated.
   - Verified [`converted_selections_cache`][optimizer-selections]: confirmed task-local `ContextVar` isolation, single-node group `id` optimization, tuple multi-node hashing, and proper lifecycle management (`set({})` / `reset(token)`) in `DjangoOptimizerExtension.on_execute`.

3. **Connection Vocabulary & Observability:**
   - Verified dynamic schema name resolution in [`connection_field_names`][optimizer-selections]: confirmed that `schema_config_from_info(info).name_converter.apply_naming_config` correctly maps `_CONNECTION_FIELD_PYTHON_NAMES` to schema-rendered field names under `auto_camel_case=False` and custom converters, falling back safely to `DEFAULT_CONNECTION_FIELD_NAMES`.
   - Verified count observability predicates: confirmed that [`connection_total_count_selected`][optimizer-selections], [`connection_has_next_page_selected`][optimizer-selections], and [`connection_count_required`][optimizer-selections] correctly inspect direct children (recursing through fragment wrappers only via `is_fragment` and respecting `should_include`) without traversing into inner connection nodes.

4. **Matrix & Single-Edit-Site Verification:**
   - Re-verified all 5 axes of the mandatory duplication probing matrix (Cross-flavor policy mirroring, Sync/async twins, Derived knowledge, Inverse/round-trip pairs, Restated contracts). All 5 axes are completely discharged.
   - Re-verified single-edit-site counts across all 5 posited change scenarios. All counts hold cleanly.

5. **Test Suite Verification:**
   - Corrected argument dictionary assertion type in `test_ast_to_converted_selections_converts_anonymous_and_named_fragments` in [`tests/optimizer/test_selections.py`][test-optimizer-selections] to reflect AST parser string coercion (`{"id": "1"}`).
   - Executed full test suite `tests/optimizer/test_selections.py` (28/28 tests passing) and all optimizer tests in `tests/optimizer/` (816/816 tests passing).
   - Executed `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/optimizer/selections.py --review docs/dry/dry-file-optimizer__selections.md --include-constants` (22/22 definitions covered).

Status updated to `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-002]: ../SPECS/spec-002-optimizer-0_0_2.md
[spec-004]: ../SPECS/spec-004-optimizer_beyond-0_0_3.md
[spec-010]: ../SPECS/appx/spec-010-foundation-0_0_4-rationale.md
[spec-016]: ../SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md
[spec-020]: ../SPECS/appx/spec-020-list_field-0_0_7-rationale.md
[spec-030]: ../SPECS/appx/spec-030-connection_field-0_0_9-terms.csv
[spec-033]: ../SPECS/spec-033-connection_optimizer-0_0_9.md
[spec-035]: ../SPECS/spec-035-optimizer_hardening-0_0_10.md
[spec-051]: ../SPECS/spec-051-boundary_dry_squeeze-0_0_15.md
[spec-063]: ../SPECS/spec-063-structural_templates-0_1_6.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[optimizer-nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py
[optimizer-selections]: ../../django_strawberry_framework/optimizer/selections.py
[optimizer-walker]: ../../django_strawberry_framework/optimizer/walker.py
[utils-typing]: ../../django_strawberry_framework/utils/typing.py

<!-- tests/ -->
[example-test-glossary]: ../../examples/fakeshop/test_query/test_glossary_api.py
[example-test-library]: ../../examples/fakeshop/test_query/test_library_api.py
[test-optimizer-extension]: ../../tests/optimizer/test_extension.py
[test-optimizer-selections]: ../../tests/optimizer/test_selections.py
[test-optimizer-walker]: ../../tests/optimizer/test_walker.py
[test-relay-connection]: ../../tests/test_relay_connection.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[graphql-ast]: https://graphql-core-3.readthedocs.io/en/latest/modules/language.html#module-graphql.language.ast
[stdlib-contextvars]: https://docs.python.org/3/library/contextvars.html
[stdlib-types]: https://docs.python.org/3/library/types.html#types.SimpleNamespace
[strawberry-nodes]: https://strawberry.rocks
