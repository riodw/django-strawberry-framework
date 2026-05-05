# 0.0.4 spec archive consolidation review

## Goal
Archive all existing `docs/spec-*.md` files by moving the completed, still-useful information into a shorter `docs/README.md`, rewriting source/test comments so they stand alone without spec references, and condensing `CHANGELOG.md` so it no longer points readers at archived specs.

## Spec files reviewed
- `docs/spec-django_type_contract.md`
- `docs/spec-django_types.md`
- `docs/spec-optimizer.md`
- `docs/spec-optimizer_beyond.md`
- `docs/spec-optimizer_nested_prefetch_chains.md`
- `docs/spec-public_surface.md`

## Proposed `docs/README.md` shape
Keep the README concise and current-state oriented. Suggested sections:

1. `# django-strawberry-framework`
2. `## Goal`
3. `## Current shipped surface`
4. `## DjangoType contract`
5. `## Optimizer contract`
6. `## Current package layout`
7. `## Settings, errors, and implementation notes`
8. `## Testing layout`
9. `## Deferred work`
10. `## Public-surface rules`

Avoid implementation-slice history in the README. Keep only behavior that is true today, constraints users must know, and named deferred work that affects current usage.

## Consolidations for `docs/README.md`
### 1. Goal and positioning
Pull from current `docs/README.md` and `spec-django_types.md`:

- DRF-shaped Django integration for Strawberry GraphQL.
- Public configuration uses nested `Meta` classes, not stacked Strawberry decorators.
- Strawberry is the GraphQL engine; the consumer API should feel like DRF / django-filter.
- Current shipped foundation is Layer 1 + Layer 2: shared infrastructure, `DjangoType`, and optimizer.
- Layer 3 remains planned: filters, orders, aggregates, `FieldSet`, `DjangoConnectionField`, permissions, app config, schema export, queryset helpers.

Do not keep the long historical comparison with upstream libraries unless condensed to one short paragraph.

### 2. Current shipped surface
Pull from `spec-public_surface.md`, `spec-django_types.md`, and `spec-optimizer.md`:

Top-level exports today:

- `DjangoType`
- `DjangoOptimizerExtension`
- `OptimizerHint`
- `auto`
- `__version__`

State explicitly that `DjangoOptimizerExtension` and `OptimizerHint` are top-level exports because the optimizer is effective end-to-end after O1-O6 and B1-B8.

Keep the rule that future names are promoted to `django_strawberry_framework.__all__` only when implementation, tests, docs, and alpha-stable naming are all present. Drop the spec vocabulary details unless needed; a short rule is enough.

### 3. DjangoType contract
Pull from `spec-django_type_contract.md` and `spec-django_types.md`.

Keep these current guarantees:

- `DjangoType` reads `Meta`, synthesizes Strawberry annotations from the Django model, registers the type, and finalizes it as a Strawberry type.
- Subclasses without `Meta` are abstract/intermediate and pass through, allowing shared `get_queryset` bases.
- `Meta.model` is required.
- `Meta.fields` and `Meta.exclude` are mutually exclusive.
- Omitting both behaves like `fields = "__all__"`.
- `Meta.name` and `Meta.description` thread through to Strawberry.
- Unknown `Meta.fields` / `Meta.exclude` names raise `ConfigurationError` naming the model, unknown names, and available fields.
- Unknown Meta keys raise `ConfigurationError`.
- Deferred Meta keys are rejected until implemented end-to-end: `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, `interfaces`.
- `Meta.optimizer_hints` is currently shipped and accepted when values are `OptimizerHint` instances and field names are valid.

Keep these current constraints:

- One `DjangoType` per model is still an alpha constraint. Registering a second type for the same model raises `ConfigurationError`.
- Multiple types per model should be deferred to a future `Meta.primary` design; import-order behavior must not become the contract.
- Consumer annotation override semantics are not guaranteed. The skipped override test remains future work because Strawberry rewrites annotations during finalization.
- Definition-order independence is not shipped. Related `DjangoType`s must currently be registered before relation conversion can target them; `registry.lazy_ref` remains future work.
- M2M conversion branches exist but dedicated real M2M coverage is still deferred because fakeshop has no M2M model field.

### 4. Scalar and choice conversion
Pull from `spec-django_types.md`.

Keep the scalar-conversion summary, not the long implementation pseudocode:

- Text-like fields map to `str`.
- Integer and auto fields map to `int`.
- Boolean, float, decimal, date/time, duration, UUID, binary, file/image fields map to Python-native / Strawberry-compatible types.
- `null=True` widens to `T | None`.
- Unsupported field types raise `ConfigurationError`; they do not silently become `Any`.
- Choice fields generate Strawberry enums, cached by `(model, field_name)`.
- Choice enum names are based on the first `DjangoType` that reads the field.
- Choice enum members are sanitized from stored choice values, not display labels.
- Grouped choices are rejected.

Keep deferred scalar notes short:

- Plain `BigIntegerField` with custom `BigInt`, `ArrayField`, `JSONField`, and `HStoreField` are still deferred.
- Relay `GlobalID` remapping for auto IDs is deferred to the Relay/interface design.

### 5. Relation conversion and resolvers
Pull from `spec-django_types.md`, `spec-optimizer.md`, and `spec-optimizer_nested_prefetch_chains.md`.

Keep the cardinality table:

- Forward FK / OneToOne -> target type, nullable if the field is nullable.
- Reverse FK and M2M -> `list[target_type]`.
- Reverse OneToOne -> target type or `None`.

Keep resolver behavior:

- Relation resolvers are generated for relation fields.
- Forward resolvers return related attributes or FK-id stubs when B2 elision is active.
- Reverse FK / M2M resolvers return lists rather than Django managers.
- Reverse OneToOne missing rows resolve to `None`.
- Resolver strictness and FK-id elision state use branch-sensitive resolver keys based on parent type, field name, and runtime response path, so aliases and sibling branches do not leak state.

### 6. `get_queryset` contract
Pull from `spec-django_types.md`, `spec-django_type_contract.md`, and `spec-optimizer.md`.

Keep:

- `DjangoType.get_queryset(cls, queryset, info, **kwargs)` defaults to identity.
- It is the hook for visibility scoping, tenancy, soft delete, permissions, and future queryset constraints.
- `has_custom_get_queryset()` reports whether a concrete or inherited type overrides the default.
- The optimizer uses this sentinel to decide when a would-be `select_related` must downgrade to `Prefetch` so visibility filters are preserved.

### 7. Optimizer contract: O1-O6
Pull from `spec-optimizer.md` and `spec-optimizer_nested_prefetch_chains.md`.

Keep the optimizer architecture in current-tense, not slice history:

- Users opt in through `strawberry.Schema(..., extensions=[DjangoOptimizerExtension()])`.
- Prefer passing an extension instance, not the class, so plan caching is effective in async mode too.
- Optimization is root-gated: only root resolvers returning Django `QuerySet`s are planned and transformed.
- Non-root resolvers and non-QuerySet results pass through.
- The selection-tree walker builds an `OptimizationPlan` for selected scalars and relations.
- `OptimizationPlan.apply()` applies `select_related`, `prefetch_related`, and `only()`.
- Same-query single-valued chains use nested `select_related` paths and include needed FK connector columns in `only()`.
- Many-side and downgraded branches use `Prefetch` objects with child querysets that carry their own nested optimization.
- Child querysets get connector columns added when `only()` is active so Django can attach prefetched rows correctly.
- Custom target `get_queryset` marks affected plans uncacheable because request context may affect results.

Keep O1-O6 as a short capability list if useful:

- O1 relation resolvers.
- O2 selection-tree walker.
- O3 root-gated resolve hook.
- O4 nested prefetch chains and same-query recursion.
- O5 `only()` projection.
- O6 custom `get_queryset` downgrade to `Prefetch`.

### 8. Optimizer improvements: B1-B8
Pull from `spec-optimizer_beyond.md`.

Keep B1-B8 as concise current behavior:

- B1 AST-cached plans keyed by selected operation AST, directive variables, model, and runtime root path. Fragment-spread directives and multi-operation documents are handled.
- B2 forward-FK-id elision avoids joins for `{ relation { id } }` when safe and resolver stubs can satisfy the relation from the local FK column.
- B3 strictness API supports `"off"`, `"warn"`, and `"raise"` for unplanned lazy relation access.
- B4 `Meta.optimizer_hints` supports `OptimizerHint.SKIP`, `.select_related()`, `.prefetch_related()`, and `.prefetch(Prefetch(...))`.
- B5 the latest `OptimizationPlan` is stashed on `info.context.dst_optimizer_plan` where possible.
- B6 schema-build-time audit reports optimizer warnings for schema-reachable registered types.
- B7 `_optimizer_field_map` precomputes field metadata on `DjangoType` classes to avoid per-request `_meta.get_fields()` walks.
- B8 queryset diffing reconciles framework plans against consumer-applied `select_related`, `prefetch_related`, and `Prefetch` lookups without mutating cached plans.

Avoid copying detailed pseudocode, priority ordering, old dependency notes, or historical “win” sections.

### 9. Current package layout
Pull from current `docs/README.md` and `docs/TREE.md`.

Keep only the current on-disk layout for `django_strawberry_framework/`:

- `__init__.py`, `py.typed`, `conf.py`, `exceptions.py`, `registry.py`
- `types/` with `base.py`, `converters.py`, `resolvers.py`
- `optimizer/` with `extension.py`, `walker.py`, `plans.py`, `hints.py`, `field_meta.py`
- `utils/` with `strings.py`, `typing.py`

Move the target Layer 3 tree out of the README or reduce it to a bullet list under Deferred work. The old side-by-side reference trees are not necessary in the concise README.

### 10. Package implementation surface checklist
Pull from the actual `django_strawberry_framework/` implementation, not only from archived specs. The final README should stay concise, but this review checklist must account for the important functions and code features so consolidation does not drop shipped behavior.

Top-level package files:

- `django_strawberry_framework/__init__.py` re-exports `DjangoType`, `DjangoOptimizerExtension`, `OptimizerHint`, `auto`, and `__version__`; it also defines the package logger and keeps `__all__` aligned with the top-level public surface.
- `django_strawberry_framework/py.typed` marks the distribution as typed.
- `django_strawberry_framework/conf.py` defines `DJANGO_SETTINGS_KEY`, the module-level `settings` instance, `Settings.user_settings`, `Settings.__getattr__`, and `reload_settings`.
- `Settings.user_settings` lazily reads the consumer's `DJANGO_STRAWBERRY_FRAMEWORK` dict from Django settings.
- Missing settings raise `AttributeError`; there are no default placeholder keys.
- `reload_settings` rebuilds the module-level `settings` object when Django's `setting_changed` signal fires for `DJANGO_STRAWBERRY_FRAMEWORK`.
- `django_strawberry_framework/exceptions.py` defines `DjangoStrawberryFrameworkError`, `ConfigurationError`, and `OptimizerError`; these are the framework error hierarchy used by type validation and optimizer planning/strictness failures.

Registry:

- `TypeRegistry.register()` claims one model for one `DjangoType` and raises `ConfigurationError` on duplicates.
- `TypeRegistry.get()` looks up the `DjangoType` for a model.
- `TypeRegistry.model_for_type()` reverse-maps a registered `DjangoType` back to its Django model and returns `None` for missing input.
- `TypeRegistry.iter_types()` exposes registered `(model, type_cls)` pairs without leaking the private dict shape.
- `TypeRegistry.lazy_ref()` is intentionally unimplemented future work for definition-order independence.
- `TypeRegistry.register_enum()` and `TypeRegistry.get_enum()` cache generated choice enums by `(model, field_name)`.
- `TypeRegistry.clear()` clears type and enum registrations for test isolation.
- `registry` is the process-global singleton used by converters, resolvers, optimizer planning, and tests.

`types.base`:

- `DjangoType.__init_subclass__()` is the class-creation pipeline: detect custom `get_queryset`, skip abstract bases with no `Meta`, validate `Meta`, select model fields, precompute optimizer field metadata, stash optimizer hints, synthesize annotations, register the type, attach relation resolvers, and call `strawberry.type()`.
- `DEFERRED_META_KEYS` currently rejects `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, and `interfaces`.
- `ALLOWED_META_KEYS` currently accepts `model`, `fields`, `exclude`, `name`, `description`, and `optimizer_hints`.
- `_validate_meta()` enforces required `Meta.model`, `fields`/`exclude` exclusivity, deferred-key rejection, unknown-key rejection, valid optimizer hint field names, and `OptimizerHint` value types.
- `_select_fields()` implements `fields = "__all__"`, omitted fields/exclude, named `fields`, named `exclude`, unknown-field errors, and Django field-order preservation.
- `_build_annotations()` routes selected Django fields through `convert_scalar()` or `convert_relation()`.
- `DjangoType.get_queryset()` is the default identity visibility hook.
- `DjangoType.has_custom_get_queryset()` reports inherited or concrete overrides using the class-level sentinel flipped during subclass creation.

`types.converters`:

- `SCALAR_MAP` covers auto, text-like, integer, boolean, float, decimal, date/time, duration, UUID, binary, file, and image field mappings.
- `convert_scalar()` maps scalar fields, replaces choice fields with generated enums, widens nullable fields to `T | None`, and raises `ConfigurationError` for unsupported field types.
- `_sanitize_member_name()` converts stored choice values into valid enum member names, including digit prefixes and Python keywords.
- `convert_choices_to_enum()` rejects empty or grouped choices, reuses cached enums, builds `<TypeName><PascalCaseFieldName>Enum`, decorates with `strawberry.enum`, and registers the enum.
- `convert_relation()` resolves target `DjangoType`s through the registry, raises when targets are not registered, and maps forward/reverse cardinality to target types, nullable target types, or `list[target_type]`.
- Deferred converter work remains `BigIntegerField`/custom `BigInt`, `ArrayField`, `JSONField`, and `HStoreField`.

`types.resolvers`:

- `_attach_relation_resolvers()` installs a Strawberry field resolver for every selected relation field before `strawberry.type()` finalizes the class.
- `_make_relation_resolver()` generates many-side, reverse OneToOne, and forward relation resolver shapes.
- Many-side resolvers return `list(manager.all())` so Strawberry receives an iterable and Django can use the prefetch cache.
- Reverse OneToOne resolvers catch the related model's `DoesNotExist` and return `None`.
- Forward resolvers return FK-id stubs when `_is_fk_id_elided()` says the optimizer planned a safe id-only elision; otherwise they return the related attribute.
- `_get_context_value()` reads optimizer state from either dict or object contexts.
- `_is_fk_id_elided()` checks branch-sensitive resolver keys against `dst_optimizer_fk_id_elisions`.
- `_build_fk_id_stub()` creates a related model instance from the local FK column, marks it non-adding, and chooses the read database through Django's router.
- `_will_lazy_load()` checks Django relation caches before strictness warnings/errors.
- `_check_n1()` implements strictness behavior by warning or raising `OptimizerError` only for unplanned relation access that would actually lazy-load.

Optimizer extension:

- `DjangoOptimizerExtension.__init__()` accepts `strictness="off" | "warn" | "raise"`, validates it, and initializes a bounded plan cache.
- `CacheInfo` and `DjangoOptimizerExtension.cache_info()` expose plan-cache hit/miss/size stats.
- `DjangoOptimizerExtension.on_execute()` sets and resets the optimizer-active `ContextVar` for an operation.
- `DjangoOptimizerExtension.resolve()` is root-gated and supports both sync and async resolver results.
- `DjangoOptimizerExtension._optimize()` passes through non-QuerySet results, resolves the Django model from GraphQL return type, converts root field selections, uses the plan cache, stashes plan/debug state on context, diffs against consumer queryset optimizations, and applies the final plan.
- `DjangoOptimizerExtension.check_schema()` audits schema-reachable `DjangoType`s for exposed relation fields whose target model has no registered type, while skipping unreachable orphan types and `OptimizerHint.SKIP` fields.
- `DjangoOptimizerExtension._build_cache_key()` keys cached plans by printed operation AST, `@skip`/`@include` directive variables, target model, and root runtime path.
- `DjangoOptimizerExtension.plan_relation()` is a small public-ish delegation point to the walker relation planner.
- `_stash_on_context()` writes optimizer state to object or dict contexts and silently skips `None`.
- `_collect_directive_var_names()` and `_walk_directives()` find directive variables in operation selections and named fragments so cache keys track only selection-affecting variables.
- `_collect_schema_reachable_types()` walks query/mutation/subscription root types through GraphQL field return types and maps them back to `DjangoType` origins.
- `_resolve_model_from_return_type()` unwraps GraphQL list/non-null wrappers, finds the Strawberry type definition, and reverse-maps it through the registry.

Optimizer plans:

- `OptimizationPlan` carries `select_related`, `prefetch_related`, `only_fields`, `fk_id_elisions`, `planned_resolver_keys`, and `cacheable`.
- `OptimizationPlan.is_empty` treats resolver metadata as plan content, not just queryset operations.
- `OptimizationPlan.apply()` applies `only()`, then `select_related()`, then `prefetch_related()`.
- `resolver_key()` builds branch-sensitive relation resolver identities from parent type, field name, and runtime response path.
- `runtime_path_from_info()` and `runtime_path_from_path()` strip list indexes and return GraphQL response paths.
- `_flatten_select_related()` normalizes Django's existing `query.select_related` structure for comparison.
- `diff_plan_for_queryset()` compares optimizer plans against consumer-applied `select_related`, `prefetch_related`, and `Prefetch` entries, drops covered work, absorbs safe plain-string prefetches, rewrites querysets only when needed, and never mutates cached plans.
- `lookup_paths()` and `_prefetch_lookup_paths()` flatten select/prefetch lookup coverage for strictness/debugging.
- `_optimizer_can_absorb()` protects consumer prefetches from being replaced unless the optimizer can preserve the full subtree.

Optimizer walker:

- `plan_optimizations()` creates an `OptimizationPlan` from selected fields, a root model, and optional `info`.
- `plan_relation()` chooses `select` versus `prefetch` based on cardinality and custom target `get_queryset`.
- `_build_child_queryset()` starts from the related model default manager and applies target `get_queryset()` when present.
- `_walk_selections()` handles fragments, skip/include directives, aliases, Strawberry camelCase to Django snake_case conversion, scalar `only_fields`, relation planning, optimizer hints, and recursive traversal.
- `_plan_select_relation()` handles same-query relation paths, FK connector columns, FK-id elision, planned resolver keys, `select_related`, and nested same-query recursion.
- `_plan_prefetch_relation()` handles queryset-boundary relation paths, child plans, connector columns, metadata merging, cacheability, target visibility querysets, and generated `Prefetch` objects.
- `_merge_child_plan_metadata()` propagates child FK-id elisions and planned resolver keys to the root plan.
- `_selected_scalar_names()`, `_can_elide_fk_id()`, `_target_pk_name()`, and `_has_custom_id_resolver()` gate safe FK-id elision.
- `_ensure_connector_only_fields()` injects the columns Django needs to attach prefetched rows under reverse FK, FK/OneToOne, and M2M shapes.
- `_append_unique()`, `_append_unique_many()`, and `_append_prefetch_unique()` deduplicate plan entries while preserving order.
- `_should_include()` evaluates literal `@skip`/`@include` directive values on selection objects.
- `_merge_aliased_selections()`, `_response_key()`, and `_response_keys()` keep alias branches distinct while merging repeated underlying Django fields.
- `_is_fragment()` detects fragment-shaped selections.

Optimizer support modules:

- `FieldMeta.from_django_field()` snapshots optimizer-relevant Django field attributes: relation booleans, related model, FK attname, target field names, reverse connector attname, and auto-created status.
- `OptimizerHint.SKIP` skips a relation entirely.
- `OptimizerHint.select_related()` forces `select_related`.
- `OptimizerHint.prefetch_related()` forces `prefetch_related`.
- `OptimizerHint.prefetch(obj)` installs a consumer-provided `Prefetch` object and treats it as a leaf.
- `optimizer/__init__.py` re-exports `DjangoOptimizerExtension` and `logger`; internal plan/walker helpers intentionally stay at dotted submodule paths.

Utilities:

- `utils.snake_case()` converts Strawberry-style camelCase field names back to Django snake_case.
- `utils.pascal_case()` converts Django snake_case names to PascalCase for generated enum/type names.
- `utils.unwrap_return_type()` unwraps one layer of `list[T]` or Strawberry list-wrapper `of_type`, returning the original value when there is no wrapper.
- `utils/__init__.py` re-exports `snake_case`, `pascal_case`, and `unwrap_return_type`.

### 11. Testing layout
Pull from current `docs/README.md`, `docs/TREE.md`, and AGENTS rules.

Keep:

- `tests/` mirrors package source and gates 100% package coverage.
- `tests/base/` is frozen at `test_init.py` and `test_conf.py`.
- `examples/fakeshop/tests/` covers fakeshop project behavior without HTTP `/graphql/`.
- `examples/fakeshop/test_query/` is for live `/graphql/` HTTP tests.
- Example app tests run but are outside package coverage source.

### 12. Deferred work / 0.0.4+ backlog
Pull from `spec-django_type_contract.md`, `spec-django_types.md`, current `docs/README.md`, and `KANBAN.md` if kept.

Keep only named bullets:

- Definition-order independence / `registry.lazy_ref`.
- Multiple `DjangoType`s per model / `Meta.primary`.
- Stable consumer override mechanism.
- Relay / `Meta.interfaces` / `GlobalID` mapping.
- Deferred scalar conversions: `BigIntegerField`, `ArrayField`, `JSONField`, `HStoreField`.
- Real M2M fixture/test coverage.
- Layer 3: `FieldSet`, filters, orders, aggregates, `DjangoConnectionField`, permissions.
- `apps.py`, schema export management command, and `utils/queryset.py` only when a shipped feature needs them.
- Fakeshop GraphQL schema activation after the required Layer 3/Relay pieces ship.

## Spec references to remove or rewrite
### Source files
Rewrite these comments/docstrings to stand alone without `spec-*.md` anchors:

- `django_strawberry_framework/registry.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/optimizer/plans.py`
- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/field_meta.py`
- `django_strawberry_framework/optimizer/hints.py`

Suggested rewrite style:

- Replace `TODO(spec-... <slice>)` with plain-language TODOs that name the missing behavior directly.
- Replace references like “B2”, “B3”, “O4”, or “spec-optimizer_beyond.md” with a short explanation when the label is not needed for comprehension.
- Keep labels like O1-O6/B1-B8 only in docs if they are still useful release shorthand; source comments should explain behavior, not point to deleted files.

### Tests
Rewrite these test module docstrings/comments:

- `tests/optimizer/test_walker.py`
- `tests/types/test_converters.py`
- `tests/types/test_resolvers.py`

Suggested rewrite style:

- Replace “spec” references with the tested behavior and current deferred reason.
- Keep skipped tests for future work, but make skip reasons self-contained: e.g. “definition-order independence is not implemented; relation targets must be registered first.”

### Docs and project notes
Update or remove spec references in:

- `docs/README.md`
- `docs/TREE.md`
- `CHANGELOG.md`
- `START.md`
- `AGENTS.md`
- `KANBAN.md` if it remains tracked/kept

`docs/TREE.md` can probably be deleted or absorbed if the new README includes a compact current tree. If kept, remove references to deleted specs and make it a static layout reference only.

`START.md` and `AGENTS.md` should stop telling agents to create or update `docs/spec-*.md`; replace that with the new rule for where future design notes belong.

## CHANGELOG condensation
Update `CHANGELOG.md` after README consolidation:

- Keep the 0.0.3 entry focused on the user-visible Layer 2 milestone.
- Remove references such as “tracked in `docs/spec-optimizer.md`”.
- Avoid O/B slice detail unless it remains useful as compact shorthand.
- No links to archived spec files.
- Keep `0.0.2` concise: `DjangoType`, registry, scalar/relation/choice conversion, `get_queryset`, and initial optimizer foundation.
- Keep `[Unreleased]` empty or with a short 0.0.4 placeholder only after actual 0.0.4 work begins.

## Spec archive/delete step
After the README consolidation and reference cleanup are reviewed and accepted, delete:

- `docs/spec-django_type_contract.md`
- `docs/spec-django_types.md`
- `docs/spec-optimizer.md`
- `docs/spec-optimizer_beyond.md`
- `docs/spec-optimizer_nested_prefetch_chains.md`
- `docs/spec-public_surface.md`

Before deletion, run a final grep for `spec-` and `TODO(spec-` to ensure no live references remain.

## Open review questions
- Should `docs/TREE.md` stay as a compact current layout reference, or should it be removed with the specs?
- Should O1-O6 and B1-B8 labels remain in the README as concise release shorthand, or should the README describe only behavior and omit slice labels entirely?
- Should future design work go into `KANBAN.md`, `docs/alpha-review-feedback.md`, GitHub issues, or a new non-spec doc naming convention?
