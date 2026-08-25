# DRY review: `django_strawberry_framework/types/definition.py`

Status: verified

## System trace

`django_strawberry_framework/types/definition.py` implements `DjangoTypeDefinition`, the canonical dataclass capturing metadata for collected `DjangoType` classes ([spec-011][spec-011], [spec-030][spec-030], [spec-031][spec-031], [spec-032][spec-032], [spec-033][spec-033], [spec-034][spec-034]).

It owns the following architectural responsibilities:

1. **GraphQL Naming Validation & Regex:**
   - [`_GRAPHQL_NAME_RE`][types-definition] (`django_strawberry_framework/types/definition.py::_GRAPHQL_NAME_RE`): Regex validating GraphQL type identifier grammar.

2. **DjangoTypeDefinition Dataclass:**
   - [`DjangoTypeDefinition`][types-definition] (`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`): Canonical metadata structure containing:
     - [`DjangoTypeDefinition.origin`][types-definition]
     - [`DjangoTypeDefinition.model`][types-definition]
     - [`DjangoTypeDefinition.name`][types-definition]
     - [`DjangoTypeDefinition.description`][types-definition]
     - [`DjangoTypeDefinition.fields_spec`][types-definition]
     - [`DjangoTypeDefinition.exclude_spec`][types-definition]
     - [`DjangoTypeDefinition.selected_fields`][types-definition]
     - [`DjangoTypeDefinition.field_map`][types-definition]
     - [`DjangoTypeDefinition.optimizer_hints`][types-definition]
     - [`DjangoTypeDefinition.has_custom_get_queryset`][types-definition]
     - [`DjangoTypeDefinition.consumer_authored_fields`][types-definition]
     - [`DjangoTypeDefinition.consumer_annotated_relation_fields`][types-definition]
     - [`DjangoTypeDefinition.consumer_annotated_scalar_fields`][types-definition]
     - [`DjangoTypeDefinition.consumer_assigned_relation_fields`][types-definition]
     - [`DjangoTypeDefinition.consumer_assigned_scalar_fields`][types-definition]
     - [`DjangoTypeDefinition.primary`][types-definition]
     - [`DjangoTypeDefinition.interfaces`][types-definition]
     - [`DjangoTypeDefinition.filterset_class`][types-definition]
     - [`DjangoTypeDefinition.orderset_class`][types-definition]
     - [`DjangoTypeDefinition.fields_class`][types-definition]
     - [`DjangoTypeDefinition.connection`][types-definition]
     - [`DjangoTypeDefinition.cursor_field`][types-definition]
     - [`DjangoTypeDefinition.relation_shapes`][types-definition]
     - [`DjangoTypeDefinition.relation_connections`][types-definition]
     - [`DjangoTypeDefinition.globalid_strategy`][types-definition]
     - [`DjangoTypeDefinition.effective_globalid_strategy`][types-definition]
     - [`DjangoTypeDefinition.finalized`][types-definition]
     - [`DjangoTypeDefinition._related_target_cache`][types-definition]
     - [`DjangoTypeDefinition._custom_id_resolver_cache`][types-definition]
     - [`DjangoTypeDefinition.graphql_type_name`][types-definition]: Centralized property computing and validating the emitted GraphQL type name.
     - [`DjangoTypeDefinition.related_target_for`][types-definition]: Resolves `(target_definition, model_field)` with post-finalization memoization.
     - [`DjangoTypeDefinition.has_custom_id_resolver_for`][types-definition]: Memoized custom id resolver predicate.

3. **Custom ID Resolver Detection:**
   - [`origin_has_custom_id_resolver`][types-definition] (`django_strawberry_framework/types/definition.py::origin_has_custom_id_resolver`): Shared MRO and `NodeID` inspection logic for custom id resolvers.
   - [`_normalize_pk_name`][types-definition] (`django_strawberry_framework/types/definition.py::_normalize_pk_name`): Normalizes primary key name strings.
   - [`_resolves_id_off_pk`][types-definition] (`django_strawberry_framework/types/definition.py::_resolves_id_off_pk`): Detects Relay `NodeID` annotations pointing away from the primary key column.
   - [`_class_has_custom_id_resolver`][types-definition] (`django_strawberry_framework/types/definition.py::_class_has_custom_id_resolver`): Checks individual class dictionaries for custom resolver methods.
   - [`_is_framework_relay_id_resolver`][types-definition] (`django_strawberry_framework/types/definition.py::_is_framework_relay_id_resolver`): Distinguishes consumer id resolvers from framework-installed Relay defaults.

Connected behavior examined:
- [`django_strawberry_framework/types/base.py`][types-base]: Construction of `DjangoTypeDefinition` during `DjangoType.__init_subclass__`.
- [`django_strawberry_framework/types/finalizer.py`][types-finalizer]: Type finalization and relation connection synthesis.
- [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker]: Reads `field_map`, `optimizer_hints`, and `relation_connections`.
- [`django_strawberry_framework/registry.py`][registry]: Definition indexing and lifecycle management.
- [`tests/types/`][tests-types]: Test coverage for definitions, metadata caching, and resolver detection.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/types/definition.py --include-constants`):
- Parsed 1 target file, 458 lines.
- Complete inventory across all 37 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `types/definition.py` centralizes all type metadata contracts. `graphql_type_name` provides the single authority for deriving the public GraphQL schema name from type options or class name. `origin_has_custom_id_resolver` is shared between `DjangoTypeDefinition.has_custom_id_resolver_for` and optimizer fallback routines.

2. **Sync and async twins:**
   Metadata access and resolution helpers (`related_target_for`, `has_custom_id_resolver_for`) are synchronous operations aligned with Python introspection.

3. **Derived rather than repeated knowledge:**
   `related_target_for` derives the relation target definition dynamically via `registry.get` and caches the result post-finalization. `graphql_type_name` normalizes type name derivation in one place.

4. **Inverse and round-trip pairs:**
   `relation_connections` maps synthesized connection attribute names back to underlying model relation names (`{"books_connection": "books"}`), providing an inverse lookup for selection walkers.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/types/definition.py`][types-definition], [`django_strawberry_framework/types/base.py`][types-base], [`django_strawberry_framework/types/finalizer.py`][types-finalizer], [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker], [`django_strawberry_framework/registry.py`][registry];
   - Specifications: [`docs/SPECS/spec-011-interfaces-0_0_4.md`][spec-011], [`docs/SPECS/spec-030-connection_sidecar-0_0_9.md`][spec-030], [`docs/SPECS/spec-031-globalid_strategies-0_0_9.md`][spec-031], [`docs/SPECS/spec-032-full_relay-0_0_9.md`][spec-032], [`docs/SPECS/spec-033-relation_connections-0_0_10.md`][spec-033], [`docs/SPECS/spec-034-schema_finalization_refactor-0_0_10.md`][spec-034];
   - Test suites: [`tests/types/`][tests-types];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adding a new metadata field to `DjangoTypeDefinition`):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/definition.py`][types-definition] ([`DjangoTypeDefinition`][types-definition]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Adjusting GraphQL type name validation rules or regex):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/definition.py`][types-definition] ([`DjangoTypeDefinition.graphql_type_name`][types-definition] / [`_GRAPHQL_NAME_RE`][types-definition]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Modifying framework default Relay id resolver identification):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/definition.py`][types-definition] ([`_is_framework_relay_id_resolver`][types-definition]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Duplicating GraphQL type name derivation across `finalizer.py` and `filters/base.py`:**
   - Disproved per [spec-034][spec-034]. Factoring into `DjangoTypeDefinition.graphql_type_name` guarantees consistent naming across all schema generation paths.
2. **Inlining custom id resolver checks into the optimizer:**
   - Disproved per [spec-011][spec-011] / [spec-032][spec-032]. Shared `origin_has_custom_id_resolver` ensures optimizer elision and type definitions share identical detection logic.

## Opportunities

None — `django_strawberry_framework/types/definition.py` is fully consolidated at root owners.

## Judgment

Verified. `types/definition.py` exhibits zero duplicate code and complete policy consolidation across type metadata representation, GraphQL name derivation, and custom resolver detection. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/types/definition.py --review docs/dry/dry-file-types__definition.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/types/definition.py`][types-definition] and Worker 1's DRY review.

1. **Canonical Type Metadata & Lookup Cache:**
   - Confirmed `DjangoTypeDefinition` maintains clean invariants across optimizer, registry, and finalization subsystems.
   - Confirmed `graphql_type_name`, `related_target_for`, and `has_custom_id_resolver_for` centralize critical schema derivations.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/types/definition.py --review docs/dry/dry-file-types__definition.md --include-constants`. 100% coverage across all 37 definitions / constants.

Confirmed: `django_strawberry_framework/types/definition.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-011]: ../SPECS/spec-011-interfaces-0_0_4.md
[spec-030]: ../SPECS/spec-030-connection_sidecar-0_0_9.md
[spec-031]: ../SPECS/spec-031-globalid_strategies-0_0_9.md
[spec-032]: ../SPECS/spec-032-full_relay-0_0_9.md
[spec-033]: ../SPECS/spec-033-relation_connections-0_0_10.md
[spec-034]: ../SPECS/spec-034-schema_finalization_refactor-0_0_10.md

<!-- package source -->
[optimizer-walker]: ../../django_strawberry_framework/optimizer/walker.py
[registry]: ../../django_strawberry_framework/registry.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-definition]: ../../django_strawberry_framework/types/definition.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py

<!-- tests -->
[tests-types]: ../../tests/types/
