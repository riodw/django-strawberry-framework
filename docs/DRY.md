# Review: `django_strawberry_framework/optimizer/_context.py`

Status: verified

## DRY analysis

- Existing patterns reused: `_context.py` centralizes context keys and the read/write helpers used by the optimizer write side and resolver read side; `DjangoOptimizerExtension._publish_plan_to_context` calls `stash_on_context` for every optimizer sentinel at `django_strawberry_framework/optimizer/extension.py:448-466`, while relation resolvers call `get_context_value` for FK elision and strictness at `django_strawberry_framework/types/resolvers.py:55-61` and `django_strawberry_framework/types/resolvers.py:127-144`.
- New helpers a fix might justify: none. The single responsibility already belongs in `stash_on_context`; the fix should make its dispatch order match `get_context_value` instead of adding another abstraction.
- Duplication risk in the current file: the read/write shape dispatch is duplicated and has drifted. `get_context_value` deliberately handles `dict` before attribute access at `django_strawberry_framework/optimizer/_context.py:50-56`, but `stash_on_context` tries `setattr` before mapping assignment at `django_strawberry_framework/optimizer/_context.py:76-82`.

---

# Review: `django_strawberry_framework/optimizer/extension.py`

Status: verified

## DRY analysis

- Existing patterns reused: `extension.py` delegates the optimizer/resolver context hand-off to `_context.stash_on_context` and shared sentinel keys at `django_strawberry_framework/optimizer/_context.py:34-38` and `django_strawberry_framework/optimizer/_context.py:59-97`; it delegates registry lookups to `registry.model_for_type`, `registry.iter_types`, and `registry.get` at `django_strawberry_framework/registry.py:100-122`; it delegates plan construction and relation decisions to `plan_optimizations` / `plan_relation` at `django_strawberry_framework/optimizer/walker.py:26-62`; it delegates queryset reconciliation and path extraction to `diff_plan_for_queryset`, `lookup_paths`, and `runtime_path_from_info` at `django_strawberry_framework/optimizer/plans.py:147-174` and `django_strawberry_framework/optimizer/plans.py:292-416`.
- New helpers a fix might justify: a single cache-key helper that renders the selected operation together with the fragment definitions reachable from it would serve `_build_cache_key` and keep the directive-variable walk aligned with the planner's fragment expansion; a small root-selection flattener would serve `_optimize` by converting all `info.field_nodes` into one child-selection list instead of hard-coding `selections[0]`.
- Duplication risk in the current file: `_walk_directives` already walks named fragments for cache-key variable extraction at `django_strawberry_framework/optimizer/extension.py:90-136`, but `_build_cache_key` separately renders only `info.operation` at `django_strawberry_framework/optimizer/extension.py:530-546`; those parallel views of the same GraphQL document can drift because the planner sees expanded fragment contents while the cache key does not. The static helper was run with `python scripts/review_inspect.py django_strawberry_framework/optimizer/extension.py --output-dir docs/review/shadow --stdout`; it also surfaced one repeated private literal, `_strawberry_schema`, but that access is already centralized in `_strawberry_schema_from_schema` / `_strawberry_schema_from_info` at `django_strawberry_framework/optimizer/extension.py:176-193`.

---

# Review: `django_strawberry_framework/optimizer/field_meta.py`

Status: verified

## DRY analysis

- Existing patterns reused: `DjangoType.__init_subclass__` builds the canonical field map once from selected Django fields and mirrors it for current optimizer readers at `django_strawberry_framework/types/base.py:90-142`; `DjangoTypeDefinition.field_map` is the definition-backed storage slot at `django_strawberry_framework/types/definition.py:14-27`; invalid optimizer-shape failures use the package optimizer exception declared at `django_strawberry_framework/exceptions.py:37-43`.
- New helpers a fix might justify: add one `FieldMeta.nullable` or `FieldMeta.relation_nullable` attribute that owns "GraphQL relation may be null" semantics and serves the anchored readers in `django_strawberry_framework/types/converters.py:222-234` and `django_strawberry_framework/types/base.py:604-624`. If this stays as a raw-Django `null` flag instead, a small method/property should still combine it with reverse-OneToOne nullability for callers.
- Duplication risk in the current file: the module claims to be the single source of truth for "relation cardinality + nullable + attname" at `django_strawberry_framework/optimizer/field_meta.py:3-17`, but the dataclass has no nullable field at `django_strawberry_framework/optimizer/field_meta.py:93-103` and `from_django_field` never captures `field.null` at `django_strawberry_framework/optimizer/field_meta.py:130-142`. The exact same nullable derivation remains duplicated in `django_strawberry_framework/types/converters.py:229-234` and `django_strawberry_framework/types/base.py:616-624`.

---

# Review: `django_strawberry_framework/optimizer/hints.py`

Status: verified

## DRY analysis

- Existing patterns reused: `OptimizerHint` uses the package-wide `ConfigurationError` for consumer configuration mistakes, matching the bottom-of-graph exception contract in `django_strawberry_framework/exceptions.py:24-34`. It is validated as the only accepted `Meta.optimizer_hints` value shape in `django_strawberry_framework/types/base.py:396-443`, consumed through the central `hint_is_skip` helper by the schema audit in `django_strawberry_framework/optimizer/extension.py:601-638`, and dispatched by the walker in `django_strawberry_framework/optimizer/walker.py:298-366`. The top-level consumer import path promised in the module docstring is present in `django_strawberry_framework/__init__.py:20-32`.
- New helpers a fix might justify: none for `hints.py`; the four flag-conflict checks are localized to `OptimizerHint.__post_init__`, and the only cross-call-site helper needed today is already `hint_is_skip`.
- Duplication risk in the current file: no repeated string literals surfaced in the static helper. The dispatch-priority wording appears in both `django_strawberry_framework/optimizer/hints.py:74-82` and `django_strawberry_framework/optimizer/walker.py:313-321`, but the source of truth is intentionally split: construction rejects invalid shapes and the walker documents consumption order.

---

# Review: `django_strawberry_framework/optimizer/plans.py`

Status: verified

## DRY analysis

- Existing patterns reused: `OptimizationPlan` centralizes the plan shape that `django_strawberry_framework/optimizer/walker.py:17-24` imports for construction-time mutation and that `django_strawberry_framework/optimizer/extension.py:56-56` imports for queryset diffing, lookup introspection, and runtime-path cache keys. The file already centralizes brittle Django internals behind helpers: `_lookup_path` owns `Prefetch.prefetch_to` access in `django_strawberry_framework/optimizer/plans.py:241-248`, `_consumer_prefetch_lookups` owns `_prefetch_related_lookups` access in `django_strawberry_framework/optimizer/plans.py:251-259`, and `_flatten_select_related` owns `query.select_related` flattening in `django_strawberry_framework/optimizer/plans.py:177-207`.
- New helpers a fix might justify: a same-lookup prefetch merge helper with one responsibility: combine compatible `Prefetch` querysets for repeated planning of the same lookup path instead of dropping the later entry. It would serve `append_prefetch_unique` in `django_strawberry_framework/optimizer/plans.py:227-238` and the generated/hint prefetch call sites in `django_strawberry_framework/optimizer/walker.py:295-336`.
- Duplication risk in the current file: repeated literal access to Django private/semiprivate lookup attributes is already centralized, and the static helper only surfaced `prefetch_to` and `queryset` twice. The remaining DRY risk is behavioral rather than literal: the path-only dedupe policy in `append_prefetch_unique` repeats the same "same path means same work" assumption for generated plans and explicit hint plans even though generated fragment branches can carry different projection/nested-subtree requirements.

---

# Review: `django_strawberry_framework/optimizer/walker.py`

Status: verified

## DRY analysis

- Existing patterns reused: `plan_optimizations` returns the shared `OptimizationPlan` from `django_strawberry_framework/optimizer/plans.py:38-116`; relation dispatch reuses `relation_kind` from `django_strawberry_framework/utils/relations.py:32-58`; field metadata is read through the cached `_optimizer_field_map` written by `django_strawberry_framework/types/base.py:90-142`; selection normalization now reuses `_included_field_selections` and `_merge_aliased_selections` in `django_strawberry_framework/optimizer/walker.py:112-115` and `django_strawberry_framework/optimizer/walker.py:367-382`.
- New helpers a fix might justify: a single hint-planning helper that first applies the shared relation-safety rules (`custom_get_queryset`, relation cardinality, and current `prefix` / `full_path`) and then dispatches to select, generated prefetch, or explicit `Prefetch` handling. It would serve `_apply_hint` in `django_strawberry_framework/optimizer/walker.py:288-356` and remove the need for hint branches to duplicate relation bookkeeping from `_plan_select_relation` / `_plan_prefetch_relation`.
- Duplication risk in the current file: relation setup is repeated across `_plan_select_relation`, `_plan_prefetch_relation`, and the explicit-prefetch hint branch (`django_strawberry_framework/optimizer/walker.py:220-234`, `django_strawberry_framework/optimizer/walker.py:258-285`, `django_strawberry_framework/optimizer/walker.py:315-326`). The drift is already visible: default dispatch consults `plan_relation` before selecting, generated prefetches use `full_path`, but hint dispatch can skip both safeguards.

---

# Review: `django_strawberry_framework/types/base.py`

Status: verified

## DRY analysis

- Existing patterns reused: `DjangoType.__init_subclass__` builds one selected-field tuple and threads it through annotation synthesis and `DjangoTypeDefinition` in `django_strawberry_framework/types/base.py:86-130`. Consumer-facing typo errors reuse `_format_unknown_fields_error` in `django_strawberry_framework/types/base.py:251-259`, and the interface validator follows the explicit shape-rejection pattern covered in `tests/types/test_relay_interfaces.py:75-144`. Relation metadata is already precomputed once into `FieldMeta` objects in `django_strawberry_framework/types/base.py:90` and stored canonically on `DjangoTypeDefinition.field_map` in `django_strawberry_framework/types/definition.py:18-31`.
- New helpers a fix might justify: one Meta option normalizer with the single responsibility "validate and normalize `Meta.model`, `Meta.fields`, `Meta.exclude`, and `Meta.optimizer_hints` before any registry, `_meta`, `set(...)`, `tuple(...)`, or `.items()` use." It would serve `_validate_meta`, `_select_fields`, `_normalize_fields_spec`, `_normalize_sequence_spec`, and `_validate_optimizer_hints`.
- Duplication risk in the current file: `_record_pending_relation` re-derives relation kind and nullability in `django_strawberry_framework/types/base.py:610-625` even though `FieldMeta` documents itself as the SSoT for that shape in `django_strawberry_framework/optimizer/field_meta.py:3-17` and exposes the normalized `nullable` field in `django_strawberry_framework/optimizer/field_meta.py:81-121`. Sibling duplicates remain in `django_strawberry_framework/types/converters.py:222-234` and `django_strawberry_framework/types/resolvers.py:180-214`; because `KANBAN.md` tracks this as `BACKLOG-013`, keep it as the explicit folder-pass DRY follow-up unless Worker 2 chooses to take the whole anchored consolidation.

---

# Review: `django_strawberry_framework/types/converters.py`

Status: verified

## DRY analysis

- Existing patterns reused: scalar conversion is centralized behind `SCALAR_MAP` and one `convert_scalar` MRO walk in `django_strawberry_framework/types/converters.py:49-126`; choice enum reuse goes through the shared registry cache in `django_strawberry_framework/types/converters.py:195-218` and `django_strawberry_framework/registry.py:44-102`; generated enum type names already reuse `pascal_case` from `django_strawberry_framework/utils/strings.py:46-60`. Relation annotation shape is shared by collection and finalization through `resolved_relation_annotation` in `django_strawberry_framework/types/base.py:609-614` and `django_strawberry_framework/types/finalizer.py:79-84`.
- New helpers a fix might justify: a GraphQL enum member-name normalizer with the single responsibility "turn an arbitrary Django choice value into a GraphQL-safe, non-reserved enum value name, or raise `ConfigurationError` when deterministic sanitization collides." It would serve `_sanitize_member_name` immediately and future `BACKLOG-007` explicit choice-enum naming if explicit enum member names are added.
- Duplication risk in the current file: relation cardinality/nullability is still re-derived in `resolved_relation_annotation` via `relation_kind(field)` plus raw `getattr(field, "null", False)` in `django_strawberry_framework/types/converters.py:222-234`, while `FieldMeta` documents itself as the canonical SSoT in `django_strawberry_framework/optimizer/field_meta.py:1-17` and `KANBAN.md:885-910` tracks the three anchored reader sites. Repeated string literals: none surfaced by `scripts/review_inspect.py`.

---

# Review: `django_strawberry_framework/types/definition.py`

Status: verified

## DRY analysis

- Existing patterns reused: `DjangoTypeDefinition` is built once by `DjangoType.__init_subclass__` after Meta validation, field selection, field-map creation, and optimizer-hint normalization in `django_strawberry_framework/types/base.py:89-145`; it is stored and iterated through the registry boundary in `django_strawberry_framework/registry.py:124-168`; finalization consumes the same definition object for consumer-authored relation skips, resolver attachment, interface injection, Strawberry decoration metadata, and the per-definition `finalized` guard in `django_strawberry_framework/types/finalizer.py:64-116`. Its `field_map` and `optimizer_hints` attributes reuse the dedicated typed metadata objects from `django_strawberry_framework/optimizer/field_meta.py:71-122` and `django_strawberry_framework/optimizer/hints.py:42-128`.
- New helpers a fix might justify: none for the current file. The dataclass is already the shared helper: it gathers the normalized, cross-module metadata that would otherwise be passed around as parallel tuples or class attributes.
- Duplication risk in the current file: the deferred future Meta slots in `django_strawberry_framework/types/definition.py:32-39` mirror the currently rejected key names in `django_strawberry_framework/types/base.py:46-54`; that is an intentional TODO-anchored staging point, but future slices should update the validator constants and definition fields together. `scripts/review_inspect.py` surfaced no repeated string literals in this file.

---

# Review: `django_strawberry_framework/types/finalizer.py`

Status: verified

## DRY analysis

- Existing patterns reused: finalization consumes pending relation records collected by `_build_annotations` in `django_strawberry_framework/types/base.py:536-648`, drains them through the registry's definition and pending-relation APIs in `django_strawberry_framework/registry.py:162-204`, delegates resolver installation to `_attach_relation_resolvers` in `django_strawberry_framework/types/resolvers.py:225-245`, and delegates Relay/interface work to `apply_interfaces`, `_check_composite_pk_for_relay_node`, `implements_relay_node`, and `install_relay_node_resolvers` in `django_strawberry_framework/types/relay.py:41-148` and `django_strawberry_framework/types/relay.py:439-464`.
- New helpers a fix might justify: none for this file-local pass. `finalize_django_types()` is branchy, but each phase already delegates the specialized behavior to sibling modules; splitting the remaining orchestration would mainly obscure the ordering contract between unresolved-target detection, annotation rewrite, resolver attachment, interface mutation, Strawberry decoration, and registry finalization.
- Duplication risk in the current file: no repeated string literals were surfaced by `scripts/review_inspect.py`. `_format_unresolved_targets_error` in `django_strawberry_framework/types/finalizer.py:20-40` intentionally parallels `_format_unknown_fields_error` in `django_strawberry_framework/types/base.py:266-274`, and its docstring explicitly calls out that consumer-facing error formatters should be updated together rather than drifting silently.

---

# Review: `django_strawberry_framework/types/relations.py`

Status: verified

## DRY analysis

- Existing patterns reused: `PendingRelation.relation_kind` reuses the shared `RelationKind` alias from `django_strawberry_framework/utils/relations.py:7-12`; records are built by `_record_pending_relation()` in `django_strawberry_framework/types/base.py:651-680`; finalization consumes the record fields in `django_strawberry_framework/types/finalizer.py:61-85`; registry removal consumes the records through `TypeRegistry.discard_pending()` in `django_strawberry_framework/registry.py:185-196`.
- New helpers a fix might justify: none. The only fix-worthy drift is contract cleanup around whether `PendingRelation` itself needs a hashability probe; no new helper would serve more than this dataclass.
- Duplication risk in the current file: `django_strawberry_framework/types/relations.py:16-19` and `django_strawberry_framework/types/relations.py:30-38` duplicate an obsolete `discard_pending()` hashability contract that has drifted from the identity-based implementation in `django_strawberry_framework/registry.py:185-196`.

---

# Review: `django_strawberry_framework/types/relay.py`

Status: verified

## DRY analysis

- Existing patterns reused: `install_is_type_of()` is installed during `DjangoType.__init_subclass__` in `django_strawberry_framework/types/base.py:76-139`; `apply_interfaces()`, `implements_relay_node()`, `_check_composite_pk_for_relay_node()`, and `install_relay_node_resolvers()` are sequenced by finalization Phase 2.5 in `django_strawberry_framework/types/finalizer.py:96-110`; the resolver paths reuse Django's default manager through `_initial_queryset()` in `django_strawberry_framework/types/relay.py:257-264` and the shared visibility hook through `_apply_get_queryset_sync()` / `_apply_get_queryset_async()` in `django_strawberry_framework/types/relay.py:192-230`.
- New helpers a fix might justify: a single `node_ids` coercion helper for Relay bulk lookup would serve `_apply_node_filter()`, `_resolve_nodes_default()`, and `_resolve_nodes_async()` by materializing any iterable once and converting `relay.GlobalID` values in one place.
- Duplication risk in the current file: Relay ID coercion is repeated in `django_strawberry_framework/types/relay.py:248-253`, `django_strawberry_framework/types/relay.py:399`, and `django_strawberry_framework/types/relay.py:423`; that duplication already creates an iterable-consumption bug in the plural resolver paths.

---

# Review: `django_strawberry_framework/types/resolvers.py`

Status: verified

## DRY analysis

- Existing patterns reused: relation resolver attachment consumes `DjangoTypeDefinition.selected_fields` and `consumer_assigned_relation_fields` from the finalizer hand-off in `django_strawberry_framework/types/finalizer.py:87-94`; context reads reuse the shared optimizer/resolver helper and constants in `django_strawberry_framework/optimizer/_context.py:34-82`; resolver identities reuse `resolver_key` / `runtime_path_from_info` from the optimizer planning layer in `django_strawberry_framework/types/resolvers.py:55-61`; relation shape classification reuses `relation_kind` from `django_strawberry_framework/utils/relations.py:32-58`.
- New helpers a fix might justify: none for the confirmed Low finding; accepting or documenting the collapsed N+1 `kind` values can be fixed locally in `_check_n1` without a new abstraction. The broader relation-shape SSoT migration should use the existing `FieldMeta` / `DjangoTypeDefinition.field_map` path documented in `django_strawberry_framework/optimizer/field_meta.py:1-17` and `django_strawberry_framework/types/base.py:117-126`.
- Duplication risk in the current file: `_make_relation_resolver` still re-derives relation kind and `attname` through `relation_kind(field)` plus raw `getattr(field, "attname", None)` in `django_strawberry_framework/types/resolvers.py:180-214`, matching the already-anchored sibling duplication in `django_strawberry_framework/types/converters.py:227-239`; `KANBAN.md:893-918` tracks this as BACKLOG-031, so it remains a folder-pass / backlog follow-up rather than a new file-local defect. The helper surfaced only the repeated literal `reverse_one_to_one`, which is not a meaningful local DRY defect.

---

# Review: `django_strawberry_framework/utils/relations.py`

Status: verified

## DRY analysis

- Existing patterns reused: `relation_kind` is the shared relation-shape classifier consumed by pending relation creation in `django_strawberry_framework/types/base.py:663-680`, annotation conversion in `django_strawberry_framework/types/converters.py:234-237`, generated resolver dispatch in `django_strawberry_framework/types/resolvers.py:189-203`, optimizer relation planning in `django_strawberry_framework/optimizer/walker.py:62-64`, and `FieldMeta` nullability derivation in `django_strawberry_framework/optimizer/field_meta.py:163-167`. The public utility contract is re-exported from `django_strawberry_framework/utils/__init__.py:16-25` and pinned by `tests/utils/test_relations.py:12-58`.
- New helpers a fix might justify: add a single package-owned many-side helper or constant, such as `is_many_side_relation_kind(kind: RelationKind) -> bool` or `MANY_SIDE_RELATION_KINDS`, for the call sites that currently repeat `("many", "reverse_many_to_one")`: `django_strawberry_framework/types/base.py:669-672`, `django_strawberry_framework/types/converters.py:234-237`, `django_strawberry_framework/types/resolvers.py:45-45` and `django_strawberry_framework/types/resolvers.py:191-197`, plus `django_strawberry_framework/optimizer/walker.py:62-64`.
- Duplication risk in the current file: none inside `django_strawberry_framework/utils/relations.py` itself beyond the necessary `RelationKind` literals and return values at `django_strawberry_framework/utils/relations.py:7-12` and `django_strawberry_framework/utils/relations.py:50-58`; the current export shape still forces consumers to duplicate the many-side grouping, which is the Medium finding below.

---

# Review: `django_strawberry_framework/utils/strings.py`

Status: verified

## DRY analysis

- Existing patterns reused: `snake_case` is the shared conversion helper used by the optimizer walker at `django_strawberry_framework/optimizer/walker.py:121-122`, `django_strawberry_framework/optimizer/walker.py:467-468`, and `django_strawberry_framework/optimizer/walker.py:603-604`; it is also reused when `DjangoType` builds optimizer field metadata in `django_strawberry_framework/types/base.py:89-94`. `pascal_case` is reused by choice enum naming in `django_strawberry_framework/types/converters.py:200-204`. The helper behavior is pinned in `tests/utils/test_strings.py:6-19`.
- New helpers a fix might justify: none. The file already centralizes the only two case conversions currently needed by callers.
- Duplication risk in the current file: none. `snake_case` and `pascal_case` intentionally implement opposite directions for different call sites, with no repeated branch structure or shared literal set worth extracting in this module.

---

# Review: `django_strawberry_framework/utils/typing.py`

Status: verified

## DRY analysis

- Existing patterns reused: `unwrap_return_type` uses Python's standard annotation-introspection APIs, `get_origin` and `get_args`, directly in `django_strawberry_framework/utils/typing.py:12-43`. It is re-exported from the utils package in `django_strawberry_framework/utils/__init__.py:16-26` and pinned by focused tests in `tests/utils/test_typing.py:6-33`.
- New helpers a fix might justify: one shared wrapper-unwrapping helper with an explicit contract for "one Python annotation layer" versus "all Strawberry/graphql-core `.of_type` layers"; the call sites it would serve are `django_strawberry_framework/utils/typing.py:15-43` and the optimizer helper/call sites in `django_strawberry_framework/optimizer/extension.py:299-308`, `django_strawberry_framework/optimizer/extension.py:347-383`, and `django_strawberry_framework/optimizer/extension.py:387-412`.
- Duplication risk in the current file: `django_strawberry_framework/utils/typing.py:5-8` says this helper exists so the optimizer and future factories do not reimplement the same unwrap, but the optimizer currently keeps a parallel `_unwrap_gql_type` loop in `django_strawberry_framework/optimizer/extension.py:299-308`; `rg` found no package source caller of `unwrap_return_type` outside the utils re-export.

---

# Review: `django_strawberry_framework/conf.py`

Status: verified

## DRY analysis

- Existing patterns reused: `DJANGO_SETTINGS_KEY` centralizes the consumer setting name for lazy reads and signal reload filtering at `django_strawberry_framework/conf.py:37-38`; `reload_settings` mutates the module-level singleton instead of rebinding it at `django_strawberry_framework/conf.py:91-101`; package tests already pin lazy `None` coercion, singleton mutation, and dispatch UID idempotence at `tests/base/test_conf.py:42-47`, `tests/base/test_conf.py:54-83`, and `tests/base/test_conf.py:111-120`.
- New helpers a fix might justify: a single user-settings normalizer for "read/replace the top-level settings mapping" would serve both the lazy-load path at `django_strawberry_framework/conf.py:61-63` and the signal/direct reload path at `django_strawberry_framework/conf.py:65-71`; it should preserve the current `None` -> `{}` contract while rejecting non-mapping values clearly.
- Duplication risk in the current file: the normalization contract is split between lazy loading and reload assignment at `django_strawberry_framework/conf.py:61-71`; because only the lazy path applies `or {}`, the two call sites can drift and already differ for truthy non-dict values. No repeated runtime string/key literals need consolidation beyond the existing `DJANGO_SETTINGS_KEY` constant.

---

# Review: django_strawberry_framework/

Status: verified

## DRY analysis

- Existing patterns reused: the top-level public API is intentionally narrow and pinned in `__all__` at `django_strawberry_framework/__init__.py:26-33`, with matching package-surface coverage in `tests/base/test_init.py:30-42`. The canonical logger string lives once at `django_strawberry_framework/__init__.py:10-16` and is re-exported by `django_strawberry_framework/optimizer/__init__.py:21-24`. Settings normalization is centralized in `_normalize_user_settings` and reused by eager construction, lazy reads, and reloads at `django_strawberry_framework/conf.py:50-83` and `django_strawberry_framework/conf.py:89-123`. Registry lifecycle and definition lookup remain the shared boundary for `types/`, `optimizer/`, and future feature slices through `TypeRegistry` methods at `django_strawberry_framework/registry.py:49-72`, `django_strawberry_framework/registry.py:114-168`, and `django_strawberry_framework/registry.py:185-204`. Type finalization delegates relation resolution, resolver attachment, Relay/interface wiring, and Strawberry decoration in ordered phases at `django_strawberry_framework/types/finalizer.py:58-118`; optimizer execution delegates context keys, plan/queryset diffing, and walker planning through the imports and apply path at `django_strawberry_framework/optimizer/extension.py:45-58` and `django_strawberry_framework/optimizer/extension.py:535-547`. Cross-cutting relation and type-unwrapping helpers are centralized in `django_strawberry_framework/utils/relations.py:39-70` and `django_strawberry_framework/utils/typing.py:14-50`.
- New helpers a fix might justify: none for this project pass. The useful package-wide helper candidates from the file/folder cycles are already resolved or explicitly anchored: many-side relation grouping lives in `is_many_side_relation_kind` at `django_strawberry_framework/utils/relations.py:68-70`, GraphQL wrapper unwrapping lives in `unwrap_graphql_type` at `django_strawberry_framework/utils/typing.py:14-18`, settings mapping normalization lives in `_normalize_user_settings` at `django_strawberry_framework/conf.py:50-83`, and queryset/private-prefetch introspection remains local to optimizer plan reconciliation at `django_strawberry_framework/optimizer/plans.py:244-262` until a future `utils/queryset.py` need becomes real.
- Duplication risk in the current project: none unanchored. The real cross-folder duplication is already recorded as backlog context rather than a new finding: relation shape/nullability/attname still has three `TODO(spec-fieldmeta-ssot)` reader sites at `django_strawberry_framework/types/base.py:657-672`, `django_strawberry_framework/types/converters.py:229-239`, and `django_strawberry_framework/types/resolvers.py:181-190`, with `FieldMeta` naming itself as the single source of truth at `django_strawberry_framework/optimizer/field_meta.py:1-17` and `KANBAN.md:1039-1073`. The legacy `cls._optimizer_field_map` / `_optimizer_hints` mirror is also intentionally anchored, with the writer at `django_strawberry_framework/types/base.py:140-145`, reader sites at `django_strawberry_framework/optimizer/walker.py:71-88`, `django_strawberry_framework/optimizer/walker.py:187-192`, `django_strawberry_framework/optimizer/extension.py:351-357`, and `django_strawberry_framework/optimizer/extension.py:615-622`, and backlog tracking at `KANBAN.md:1075-1110`.

---

# Review: `django_strawberry_framework/optimizer/`

Status: verified

## DRY analysis

- Existing patterns reused: the folder has a clear one-way optimizer dependency shape. `extension.py` orchestrates and delegates to `_context.stash_on_context`, `plans.diff_plan_for_queryset`, `plans.lookup_paths`, `plans.runtime_path_from_info`, and `walker.plan_optimizations` at `django_strawberry_framework/optimizer/extension.py:45-57` and `django_strawberry_framework/optimizer/extension.py:538-552`; `walker.py` builds only the shared `OptimizationPlan` and uses plan mutators from `plans.py` at `django_strawberry_framework/optimizer/walker.py:18-25` and `django_strawberry_framework/optimizer/walker.py:28-46`; `plans.py` owns the plan data shape and Django-private queryset reconciliation helpers at `django_strawberry_framework/optimizer/plans.py:38-116` and `django_strawberry_framework/optimizer/plans.py:244-262`; `_context.py` centralizes context sentinel keys and context read/write shape at `django_strawberry_framework/optimizer/_context.py:34-38` and `django_strawberry_framework/optimizer/_context.py:41-110`; `hints.py` centralizes the consumer hint value object and skip probe at `django_strawberry_framework/optimizer/hints.py:42-155`; the folder `__init__.py` keeps the subpackage export contract narrow at `django_strawberry_framework/optimizer/__init__.py:21-24`.
- New helpers a fix might justify: none for this folder pass. The prior file cycles already centralized the two real helper candidates: relation access bookkeeping now lives in `walker._record_relation_access` at `django_strawberry_framework/optimizer/walker.py:279-289`, and fragment/cache-key traversal shares `_child_selections` plus `_unvisited_fragment_definition` at `django_strawberry_framework/optimizer/extension.py:129-173`. A broader AST visitor or metadata access helper would be premature until the TODO-anchored `DjangoTypeDefinition.field_map` migration ships.
- Duplication risk in the current folder: the static helper was run for every optimizer Python file, including `__init__.py`, with `/Users/riordenweber/.local/bin/uv run python scripts/review_inspect.py <path> --output-dir docs/review/shadow`. Repeated-literal sections showed only localized framework names: `_strawberry_schema` appears twice behind the schema unwrapping helpers at `django_strawberry_framework/optimizer/extension.py:311-328`; `prefetch_to` and `queryset` appear around the queryset-diff helpers at `django_strawberry_framework/optimizer/plans.py:244-262` and `django_strawberry_framework/optimizer/plans.py:422-439`; walker literals such as `prefetch`, `selections`, `directives`, and `arguments` are selection/planning vocabulary around `django_strawberry_framework/optimizer/walker.py:322-426` and `django_strawberry_framework/optimizer/walker.py:551-622`. No repeated literal currently justifies another abstraction.

---

# Review: `django_strawberry_framework/registry.py`

Status: verified

## DRY analysis

- Existing patterns reused: `TypeRegistry._check_mutable()` centralizes post-finalization mutation rejection for every guarded mutator in `django_strawberry_framework/registry.py:49-62`, and `TypeRegistry._already_registered()` centralizes duplicate-registration message construction for type and enum collisions in `django_strawberry_framework/registry.py:64-72`. The collection/finalization path uses this single registry boundary from `django_strawberry_framework/types/base.py:81-134`, `django_strawberry_framework/types/finalizer.py:58-85`, `django_strawberry_framework/types/converters.py:195-219`, and optimizer lookup sites such as `django_strawberry_framework/optimizer/extension.py:260-271`.
- New helpers a fix might justify: none. The file already has the useful shared helpers for mutation-state checks and duplicate-registration errors; the remaining API methods are direct dictionary/list operations with single call-site responsibilities.
- Duplication risk in the current file: none found in executable logic. The static helper reported no control-flow hotspots and no repeated string literals for `django_strawberry_framework/registry.py`; the repeated collision/mutability concerns are already centralized through `_already_registered()` and `_check_mutable()`.

---

# Review: django_strawberry_framework/types/

Status: verified

## DRY analysis

- Existing patterns reused: `DjangoType.__init_subclass__` builds one `DjangoTypeDefinition` containing selected fields, `field_map`, optimizer hints, consumer-authored field sets, interfaces, and lifecycle state in `django_strawberry_framework/types/base.py:117-145`; finalization consumes that same definition object for pending-relation rewrites, generated resolver attachment, interface/Relay work, and Strawberry decoration in `django_strawberry_framework/types/finalizer.py:64-118`; relation resolvers reuse the optimizer context helpers and `resolver_key` / `runtime_path_from_info` plan identity instead of carrying a separate resolver-state channel in `django_strawberry_framework/types/resolvers.py:29-40` and `django_strawberry_framework/types/resolvers.py:48-146`; Relay helpers centralize the four default resolver method names in one table in `django_strawberry_framework/types/relay.py:437-473`.
- New helpers a fix might justify: none for this folder pass. The only cross-file DRY candidate is already assigned to the existing `FieldMeta` single-source-of-truth path: `FieldMeta` documents the target ownership in `django_strawberry_framework/optimizer/field_meta.py:3-17`, and `KANBAN.md:893-916` tracks the three anchored reader sites.
- Duplication risk in the current folder: relation cardinality/nullability/attname is still re-derived in `_record_pending_relation`, `resolved_relation_annotation`, and `_make_relation_resolver` via `relation_kind(...)` plus raw `getattr(...)` reads in `django_strawberry_framework/types/base.py:657-680`, `django_strawberry_framework/types/converters.py:227-239`, and `django_strawberry_framework/types/resolvers.py:182-216`. This is a real folder-level DRY concern, but it is already source-anchored with `TODO(spec-fieldmeta-ssot)` and tracked as `BACKLOG-031-0.0.6` in `KANBAN.md:893-916`, so this pass records it as context rather than duplicating it as a new finding.

---

# Review: django_strawberry_framework/utils/

Status: verified

## DRY analysis

- Existing patterns reused: `utils.__init__` exposes the currently shared helper surface from the focused submodules at `django_strawberry_framework/utils/__init__.py:17-29`. Relation-shape classification and many-side grouping are centralized in `relation_kind` and `is_many_side_relation_kind` at `django_strawberry_framework/utils/relations.py:39-70`, then reused by type collection, conversion, resolver generation, and optimizer planning at `django_strawberry_framework/types/base.py:663-680`, `django_strawberry_framework/types/converters.py:234-239`, `django_strawberry_framework/types/resolvers.py:188-194`, and `django_strawberry_framework/optimizer/walker.py:62-64`. String conversion is centralized in `snake_case` / `pascal_case` at `django_strawberry_framework/utils/strings.py:19-60` and reused by optimizer/type/converter code at `django_strawberry_framework/optimizer/walker.py:121-122`, `django_strawberry_framework/types/base.py:89-94`, and `django_strawberry_framework/types/converters.py:204-204`. GraphQL wrapper unwrapping is centralized in `unwrap_graphql_type` at `django_strawberry_framework/utils/typing.py:14-18` and reused by optimizer return-type/schema tracing at `django_strawberry_framework/optimizer/extension.py:336-390`. Utility re-export contracts are pinned by `tests/utils/test_relations.py:46-58` and `tests/utils/test_typing.py:40-56`.
- New helpers a fix might justify: none for this folder pass. The previous sibling findings already added the shared many-side relation helper and recursive GraphQL unwrap helper. The remaining relation-cardinality/nullability consolidation belongs to the existing `FieldMeta` SSoT backlog, which is source-anchored at `django_strawberry_framework/types/base.py:657-672`, `django_strawberry_framework/types/converters.py:229-239`, and `django_strawberry_framework/types/resolvers.py:181-190` rather than needing a new `utils/` helper.
- Duplication risk in the current folder: none unanchored. Static helper runs on `__init__.py`, `relations.py`, `strings.py`, and `typing.py` showed no cross-sibling repeated literals or control-flow hotspots. The repeated relation-kind literals inside `relations.py` are the defining `RelationKind` contract at `django_strawberry_framework/utils/relations.py:7-19` plus classifier return values at `django_strawberry_framework/utils/relations.py:57-65`, not duplicated implementation logic.
