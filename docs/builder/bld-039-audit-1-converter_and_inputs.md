# Build: Slice 1a — audit of the Slice 1 contracts (serializer converter + generated inputs)

Spec reference: `docs/SPECS/spec-039-serializer_mutations-0_0_13.md`
Status: review-accepted

This artifact carries **one combined audit section** in place of the build/review split
(`docs/builder/build-039-serializer_mutations-0_0_13.md` `## What this cycle is`, step 2).
This pass is **read-only**: no source, no tests, no spec edit, no mutation of any kind.
Spec edits are Worker 1's alone and are surfaced under
`### Notes for Worker 1 (spec reconciliation)`.

---

## Audit (Worker 3)

### What was graded against

Every file in this audit's scope was verified **byte-identical to `HEAD`** before grading,
so the working tree *is* `HEAD` for all of them and no scratch copy was needed:

```shell
for f in django_strawberry_framework/rest_framework/serializer_converter.py \
         django_strawberry_framework/rest_framework/inputs.py \
         django_strawberry_framework/utils/converters.py \
         django_strawberry_framework/utils/inputs.py \
         django_strawberry_framework/mutations/inputs.py \
         tests/rest_framework/test_converter.py tests/rest_framework/test_inputs.py; do
  git show HEAD:$f > /tmp/dsf-039-head/$(echo $f | tr '/' '_'); diff -q ...
done
# -> CLEAN(==HEAD) for all seven.
```

`git stash` / `git checkout` / `git restore` / `git worktree` were not used (banned:
a concurrent maintainer session is live in this tree). The dirty files reported by
`git status --short` at audit time (`utils/querysets.py`, `list_field.py`, `conf.py`,
`apps.py`, `orders/sets.py`, `resource_policy.py`, `_strawberry_patches.py`, the rendered
docs, `db.sqlite3`, the `spec-050` pair) are the concurrent `spec-050` cycle's and are out
of scope. `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` itself is dirty — that is
**this** cycle's own Slice 0 rationale extraction, so the working-tree spec is the contract
graded (its rationale companion `docs/SPECS/appx/spec-039-…-rationale.md` was read alongside).

Line counts read at audit time: `serializer_converter.py` 1060, `rest_framework/inputs.py`
1812, `utils/converters.py` 191, `utils/inputs.py` 1823, `mutations/inputs.py` 976,
`tests/rest_framework/test_converter.py` 1389 (76 test defs),
`tests/rest_framework/test_inputs.py` 1860 (94 test defs).

### Population

**71 contract rows**, enumerated before any was graded, drawn from the five homes the
spec keeps for Slice 1:

| Home | Rows | Ids |
| --- | --- | --- |
| `## Slice checklist` → Slice 1, `serializer_converter.py` sub-bullet | 10 | A1–A10 |
| `## Slice checklist` → Slice 1, `inputs.py` sub-bullet | 10 | B1–B10 |
| `## Slice checklist` → Slice 1, package-coverage sub-bullet | 12 | C1–C12 |
| `## Slice checklist` → Slice 1, `**DRY / reuse**` sub-bullet | 6 | D1–D6 |
| `### Decision 7` clauses (not already covered above) | 15 | E1–E15 |
| `### Import manifest` rows for the two modules | 2 | F1–F2 |
| `## Definition of done` item 2 | 2 | G1–G2 |
| `## Edge cases and constraints` bearing on input generation / field conversion | 14 | H1–H14 |
| **Total** | **71** | |

The `## Cross-flavor reuse and DRY obligations` rows the dispatch names (`P1.3`, `P1.4`,
`P2.1`, `P2.2`, `P2.3`) are graded as D4, D1, D2, D3, D5 respectively — the Slice-1
`**DRY / reuse**` sub-bullet states each of them verbatim, so grading them twice would be a
double count, and the two homes were cross-checked for agreement (they agree; the
divergence is between BOTH of them and `HEAD`, recorded at D5 / F1 / F2).

### Grade counts

| Grade | Count |
| --- | --- |
| BUILT-CONFORMANT | 61 |
| SPEC-STALE | 9 |
| DEVIATED | 0 |
| SUPERSEDED | 0 |
| **DROPPED** | **1** |
| **Total** | **71** |

### Grade table

#### A — `rest_framework/serializer_converter.py` (slice checklist)

| # | Contract | Grade | Evidence |
| --- | --- | --- | --- |
| A1 | `convert_serializer_field(field)` registry returning the Strawberry annotation + required-ness, graphene-parity shape | BUILT-CONFORMANT | `django_strawberry_framework/rest_framework/serializer_converter.py::convert_serializer_field` returning `::SerializerFieldConversion` |
| A2 | The scalar table (`CharField`→`str`, `ChoiceField`→`str` base + enum at the build site, `IntegerField`, `BooleanField`, `FloatField`, `DecimalField`, date/time natives, `UUIDField`, `JSONField`) | BUILT-CONFORMANT | `serializer_converter.py #"_BUILTIN_SCALAR_CONVERTERS"`; build-site enum upgrade at `::_serializer_only_scalar_annotation` |
| A3 | `ListField` → `list[<scalar child>]`; relation / nested-serializer child raises `ConfigurationError` | BUILT-CONFORMANT | `serializer_converter.py::_list_child_conversion` (recurses the child through the same registry; three distinct raises) |
| A4 | `PrimaryKeyRelatedField` → target id; `many=True` / `ManyRelatedField` → `list[<id>]` | BUILT-CONFORMANT | `serializer_converter.py::convert_serializer_field #"(serializers.ManyRelatedField, _relation_multi)"`; annotation finalized at `::resolve_serializer_field` / `::serializer_only_relation_annotation` |
| A5 | `FileField` / `ImageField` → `Upload` | BUILT-CONFORMANT | `serializer_converter.py::convert_serializer_field #"(serializers.FileField, _CONVERT_FILE)"`; `::resolve_serializer_field #"annotation = Upload"` |
| A6 | Fail-loud dispatch: MRO walk over individually-registered classes, **raising** fallthrough, NOT `singledispatch` + `serializers.Field → String` | BUILT-CONFORMANT | `django_strawberry_framework/utils/converters.py::convert_with_mro` ends in `raise fallthrough_error_factory(field)`; the factory is `serializer_converter.py::_unsupported_serializer_field`. **No** `serializers.Field` key exists in `_BUILTIN_SCALAR_CONVERTERS`, so the MRO walk cannot shadow the raise. Proven by run, not by reading: `tests/rest_framework/test_converter.py::test_unknown_custom_field_subclass_raises` and `::test_unregistered_custom_field_raises_then_registered_maps` |
| A7 | Reuse the read-side scalar / choice-enum registry at the build site, keyed on the backing `models.Field` resolved via `source` | BUILT-CONFORMANT | `serializer_converter.py::_model_backed_scalar_annotation` calls `types/converters.py::convert_scalar` / `::scalar_for_field`; the column comes from `::backing_model_field` which resolves through `field.source` |
| A8 | Reverse map `input_attr → (serializer_field_name, source, kind)`, `kind ∈ {scalar, relation_single, relation_multi, file}` | **SPEC-STALE** | `HEAD` records nine axes, not three, and two more kinds. `utils/inputs.py::InputFieldSpec` carries `input_attr / graphql_name / target_name / kind / source / related_model / nested_specs / annotation_repr / required`; `serializer_converter.py #"NESTED_SINGLE: str"` / `#"NESTED_MULTI: str"` add two kinds beyond the spec's four |
| A9 | Omitted / one-segment `source` supported; dotted `source` / `source="*"` rejected for a model-column-converting field | BUILT-CONFORMANT | `serializer_converter.py::require_one_segment_source`, called from `::backing_model_field`; `tests/rest_framework/test_converter.py::test_dotted_source_on_model_column_field_raises`, `::test_star_source_on_model_column_field_raises` |
| A10 | The whole module behind the DRF soft-import guard | BUILT-CONFORMANT | `django_strawberry_framework/rest_framework/__init__.py::require_drf` is invoked at package import, so no `rest_framework/` submodule can load DRF-absent |

#### B — `rest_framework/inputs.py` (slice checklist)

| # | Contract | Grade | Evidence |
| --- | --- | --- | --- |
| B1 | Build **two** `@strawberry.input` classes from the serializer's schema-time field set | BUILT-CONFORMANT | `rest_framework/inputs.py::build_serializer_inputs` returns `(create_cls, create_shape, partial_cls, partial_shape)` |
| B2 | Discovery via the overridable `get_serializer_for_schema()`; default no-arg `serializer_class()` then `.fields`; request-varying rejected loudly | BUILT-CONFORMANT | `rest_framework/sets.py::SerializerMutation.get_serializer_for_schema` (the classmethod hook) delegating to `rest_framework/inputs.py::get_serializer_for_schema` (the module default) |
| B3 | Narrowed by `Meta.fields` / `Meta.exclude`; `read_only` / `HiddenField` dropped; `Meta.optional_fields` forced optional | BUILT-CONFORMANT | `inputs.py::resolve_effective_serializer_fields` (drop via `::writable_serializer_fields`, narrow via `utils/inputs.py::resolve_effective_fields`); `inputs.py::resolve_optional_fields` |
| B4 | `<Serializer>Input` (create, requiredness `field.required` minus `optional_fields`) and `<Serializer>PartialInput` (update, all optional) | BUILT-CONFORMANT | `inputs.py::_walk_serializer_fields #"required = False if is_partial else (field.required and name not in optional_fields)"` |
| B5 | `SerializerInputShape` descriptor identity = ordered `(input_attr, annotation, required/default, serializer_field_name, source, kind)` + normalized `optional_fields` | **SPEC-STALE** | `HEAD`'s descriptor carries two axes the spec's enumeration omits, and the annotation axis is not the base annotation. `inputs.py::SerializerInputShape` fields are `serializer_class / operation_kind / field_specs / annotations / descriptions / required_state / optional_fields / type_name`; `annotations` is the **post-nullable-widening** repr (`::_walk_serializer_fields #"annotation_repr = repr(annotation)"`, taken after `optional_input_field`), and `descriptions` is an independent axis. Both are load-bearing: `tests/rest_framework/test_inputs.py::test_allow_null_difference_yields_distinct_descriptor_names`, `::test_description_difference_yields_distinct_descriptor_names` |
| B6 | Canonical `<Serializer>Input` / `<Serializer>PartialInput` for the default full shape; descriptor-derived names for divergent shapes; identical descriptors dedupe; two distinct descriptors on one name → finalize-time `ConfigurationError` | **SPEC-STALE** | The dedupe / divergent-name / collision halves are all conformant (`inputs.py::serializer_input_type_name`, `::dedupe_serializer_input_shape`, `::materialize_serializer_input_class`; `tests/rest_framework/test_inputs.py::test_identical_descriptor_dedupes_via_ledger`, `::test_distinct_descriptors_colliding_on_one_name_raise`). The **canonical-name predicate** is stricter than the spec's: `HEAD` grants the canonical name only when the shape's per-field identity **equals the identity the DEFAULT module-level discovery produces** (`inputs.py::_default_full_shape_identity`, consumed at `::build_serializer_input_class #"is_full_shape = ("`), so a `get_serializer_for_schema()` hook returning a *different* "full" shape does **not** get the canonical name. The spec defines the canonical shape as "all input fields, default requiredness, no `optional_fields`", which a hook-returned full shape satisfies |
| B7 | `guard_create_required_serializer_fields` runs **per declaration, before the descriptor cache lookup** | BUILT-CONFORMANT | `rest_framework/sets.py::SerializerMutation.build_input` defines `_build()` which calls the guard, then `::_serializer_input_shape_for` (which dedupes). `mutations/sets.py::build_and_stash_input` calls `build()` **unconditionally** — there is no pre-`build` cache lookup on this path — so the guard cannot be skipped by a cache hit. `tests/rest_framework/test_inputs.py::test_guard_runs_per_declaration` |
| B8 | `Meta.injected_fields` is the only field-level subtraction; writable on the same schema-time basis; narrowed out of client input; supplied by `get_serializer_injected_data` | BUILT-CONFORMANT | `rest_framework/sets.py #"unknown_injected"` (writable basis) and `#"exposed_injected"` (must be narrowed out); `inputs.py::guard_create_required_serializer_fields` passes `waived=injected_fields` and nothing else; `tests/rest_framework/test_inputs.py::test_injected_fields_subtract_from_create_required_guard`, `::test_dropped_required_not_injected_still_raises` |
| B9 | Reuse `utils/inputs.py::build_strawberry_input_class` + `materialize_generated_input_class`; materialize as module globals for the `strawberry.lazy` forward-ref | BUILT-CONFORMANT | `inputs.py::build_serializer_input_class #"input_cls = build_strawberry_input_class(type_name, triples)"`; `inputs.py #"SERIALIZER_INPUTS_MODULE_PATH"` + `::materialize_serializer_input_class`; `tests/rest_framework/test_inputs.py::test_materialized_input_is_module_global` |
| B10 | Normalize + fail-loud `Meta.fields` / `Meta.exclude` (bare string, duplicates, unknown names, empty effective set) | BUILT-CONFORMANT | `inputs.py::resolve_effective_serializer_fields` → `utils/inputs.py::normalize_field_name_sequence(flavor="SerializerMutation")` + `::resolve_effective_fields`; `tests/rest_framework/test_inputs.py::test_meta_fields_rejects_bare_string`, `::test_meta_fields_rejects_unknown_name`, `::test_meta_exclude_rejects_unknown_name`, `::test_meta_fields_and_exclude_mutually_exclusive`, `::test_empty_effective_field_set_raises` |

#### C — package coverage (slice checklist)

Every row here is BUILT-CONFORMANT; the focused run below confirms the assertions execute
rather than merely exist.

| # | Contract | Grade | Evidence (`tests/rest_framework/…`) |
| --- | --- | --- | --- |
| C1 | Each supported serializer-field class → annotation + required-ness | BUILT-CONFORMANT | `test_converter.py::test_scalar_field_annotations` (parametrized), `::test_expanded_scalar_matrix`, `::test_required_ness_reflects_field_required` |
| C2 | `PrimaryKeyRelatedField` / `ManyRelatedField` id mapping, Relay `GlobalID` vs raw pk by the target's primary `DjangoType` | BUILT-CONFORMANT | `test_converter.py::test_primary_key_related_field_is_relation_single`, `::test_many_related_field_is_relation_multi`, `::test_serializer_only_relation_to_relay_target_uses_globalid`; `test_inputs.py::test_fk_to_non_relay_products_target_uses_raw_pk_id` |
| C3 | Serializer `FileField` → `Upload` | BUILT-CONFORMANT | `test_converter.py::test_file_and_image_fields_are_file_kind`, `::test_resolve_serializer_field_model_backed_file_field`, `::test_resolve_serializer_field_column_less_file_field`; `test_inputs.py::test_file_field_maps_to_upload` |
| C4 | Renamed fields: GraphQL name from the declared name, backing column via `source`, declared name preserved in the reverse map | BUILT-CONFORMANT | `test_converter.py::test_renamed_scalar_resolves_backing_column_via_source`, `::test_renamed_relation_resolves_backing_column_and_id_like_name` |
| C5 | The id-like suffix rule (`category`/`category_id` → `categoryId`, `category_pk` → `categoryPk`, no doubled suffix) | BUILT-CONFORMANT | `test_converter.py::test_id_like_suffix_rule` (parametrized — not a loop, so each row is its own node id), `::test_multi_relation_keeps_plain_name` |
| C6 | Dotted `source` / `source="*"` raises | BUILT-CONFORMANT | `test_converter.py::test_dotted_source_on_model_column_field_raises`, `::test_star_source_on_model_column_field_raises`, `::test_require_one_segment_source_rejects_star_and_dotted` |
| C7 | Unknown serializer-field `ConfigurationError` | BUILT-CONFORMANT | `test_converter.py::test_unknown_custom_field_subclass_raises`, `::test_unsupported_serializer_field_without_field_name_raises_cleanly` |
| C8 | Input shape: schema-time set, requiredness, `read_only` dropped, narrowing, `optional_fields` force-optional, bare-string `"__all__"` rejected, module global | BUILT-CONFORMANT | `test_inputs.py::test_create_input_required_and_optional_shapes`, `::test_partial_input_all_fields_optional`, `::test_read_only_and_hidden_fields_dropped`, `::test_fields_narrowing_omits_dropped_field`, `::test_optional_fields_all_bare_string_rejected`, `::test_materialized_input_is_module_global` |
| C9 | Schema-time hook: kwargs-requiring `__init__` **and** a `get_fields()` reading `self.context` (raising at `.fields`, not construction) both rejected; an override supplying a stable map generates the input | BUILT-CONFORMANT | `test_inputs.py::test_kwarg_requiring_serializer_rejected_loudly`, `::test_context_reading_get_fields_rejected_at_fields_access`, `::test_schema_hook_stable_field_map_generates_input`. The second row is the one that proves the guard wraps `.fields` rather than the constructor |
| C10 | Descriptor identity: differing `optional_fields`, differing annotations / `source` / relation kind diverge; identical descriptors dedupe | BUILT-CONFORMANT | `test_inputs.py::test_differing_annotations_yield_distinct_descriptor_names`, `::test_allow_null_difference_yields_distinct_descriptor_names`, `::test_descriptor_name_distinguishes_relation_target_model`, `::test_identical_descriptor_dedupes_via_ledger`, `::test_descriptor_is_its_own_cache_key` |
| C11 | Create-required guard: dropping a required scalar, a required serializer-only field, or a required relation raises; `read_only` / `HiddenField` outside the writable basis | BUILT-CONFORMANT | `test_inputs.py::test_create_guard_rejects_dropping_required_scalar` (its fixture `_required_field_serializer` is a plain `serializers.Serializer`, so the dropped field **is** the serializer-only case), `::test_create_guard_rejects_dropping_required_relation`, `::test_read_only_field_dropped_before_create_guard`, `::test_excluding_read_only_field_raises_non_writable`. The `HiddenField` arm of the guard's basis is pinned only transitively (via `inputs.py::writable_serializer_fields`, itself pinned by `::test_read_only_and_hidden_fields_dropped`) — noted, not a finding |
| C12 | The guard runs per declaration; one declaration's `Meta.injected_fields` never suppresses a later declaration's guard on the same cached shape | BUILT-CONFORMANT | `test_inputs.py::test_guard_runs_per_declaration` |

#### D — DRY / reuse (slice checklist + the `P*` rows it states)

| # | Contract | Grade | Evidence |
| --- | --- | --- | --- |
| D1 | **P1.4** — `convert_serializer_field` rides the shared fail-loud dispatch **skeleton** promoted to `utils/converters.py`, supplying only its precheck table + scalar registry | BUILT-CONFORMANT | `utils/converters.py::convert_with_mro` has exactly the spec's `(field, isinstance_prechecks, scalar_registry, fallthrough_error_factory) → conversion` signature. Both flavors import it and neither re-spells the walk: `forms/converter.py #"from ..utils.converters import"` and `serializer_converter.py::convert_serializer_field #"result = convert_with_mro("`. Repo-wide users of the symbol: `filters/inputs.py`, `forms/converter.py`, `rest_framework/serializer_converter.py`, its own module, and two test modules — no second copy exists |
| D2 | **P2.1** — the reverse-map field spec is the unified `InputFieldSpec` sited in `utils/inputs.py` (`038` analog + the `source` axis), conversion result a shared shape too | BUILT-CONFORMANT | `utils/inputs.py::InputFieldSpec` and `::FieldConversionBase`; `serializer_converter.py::SerializerFieldConversion` is a `__slots__`-only subclass of the shared base and defines no fields of its own |
| D3 | **P2.2** — the input namespace is the promoted `make_input_namespace(...)` **one-ledger** trio, NOT `clear_generated_input_namespace` | BUILT-CONFORMANT | `utils/inputs.py::make_input_namespace` whose `clear_fn` is `ledger.clear()` only; consumed at `rest_framework/inputs.py #"_materialized_names, _materialize_input, _clear_input_namespace = make_input_namespace("`. `clear_generated_input_namespace` is reached only through `utils/inputs.py::make_set_input_namespace` (the filter / order families), never from `rest_framework/` |
| D4 | **P1.3** — the `SerializerInputShape` cache + clear is the promoted `make_shape_build_cache()` plumbing | BUILT-CONFORMANT | `utils/inputs.py::make_shape_build_cache`, consumed at `rest_framework/inputs.py #"_serializer_shape_build_cache, clear_serializer_shape_build_cache = make_shape_build_cache()"`; the get-or-store itself rides `utils/inputs.py::get_or_store_shape_build` via `inputs.py::dedupe_serializer_input_shape` |
| D5 | **P2.3** — the divergent-shape suffix reuses `mutations/inputs.py::_pascalize_token` | **SPEC-STALE** | The **DRY intent holds** — there is exactly one PascalCase token encoder and `rest_framework/inputs.py` imports it — but the symbol has moved. It now lives at `utils/inputs.py::pascalize_token`; `mutations/inputs.py #"_pascalize_token = pascalize_token"` survives only as a backward-compatible alias, and `rest_framework/inputs.py::_shape_token #"base = pascalize_token(spec.target_name)"` imports it from `utils/inputs.py`, not from `mutations/inputs.py` |
| D6 | "A grep guard that `rest_framework/serializer_converter.py` + `rest_framework/inputs.py` **import** these and do not redefine them is the DoD check." | **DROPPED** | See `### High:` / `### Medium:` below. No such guard exists anywhere in the tree — not as a test under `tests/rest_framework/`, not as a `scripts/` checker, not as a pre-commit hook. Verified by reading, not by a single failing grep: `tests/rest_framework/` contains exactly `test_converter.py`, `test_inputs.py`, `test_resolvers.py`, `test_sets.py`, `test_soft_dependency.py`, and none of the five asserts an import obligation or a non-redefinition. **The contract the guard was to protect does hold at `HEAD`** — I measured it: none of `pascalize_token`, `make_input_namespace`, `make_shape_build_cache`, `build_strawberry_input_class`, `materialize_generated_input_class`, `normalize_field_name_sequence`, `graphql_camel_name` is redefined anywhere under `django_strawberry_framework/rest_framework/`. What is missing is the **ratchet**, not the behavior |

#### E — Decision 7 clauses

| # | Contract | Grade | Evidence |
| --- | --- | --- | --- |
| E1 | The loud-rejection guard wraps the `.fields` materialization, not the constructor | BUILT-CONFORMANT | `rest_framework/inputs.py::get_serializer_for_schema` — `serializer_class()` **and** `serializer.fields` are both inside one `try`, so the lazily-built field map is covered. The distinguishing row is `tests/rest_framework/test_inputs.py::test_context_reading_get_fields_rejected_at_fields_access`, which constructs fine and raises only at `.fields` |
| E2 | Relation / file kinds matched first by `isinstance` (`PrimaryKeyRelatedField` / `ManyRelatedField`, `FileField` / `ImageField`), then the scalar registry MRO walk, then a raising default | **SPEC-STALE** | The three-phase ordering holds, but `HEAD`'s precheck table is longer and stricter than the spec's sentence. `serializer_converter.py::convert_serializer_field #"isinstance_prechecks=["` is, in order: `(BaseSerializer, ListSerializer)` → `ManyRelatedField` → **`RelatedField`** → `FileField` → `ListField` → `MultipleChoiceField`. Two divergences: the nested-serializer reject runs **first** (so a nested serializer is named rather than list-mapped), and the single-relation precheck matches the **broad** `serializers.RelatedField`, with `::_reject_unsupported_relation_field` then raising for any non-`PrimaryKeyRelatedField` (a `SlugRelatedField` / `HyperlinkedRelatedField` / custom writable `RelatedField`). The spec nowhere states that non-PK relation rejection; it is a real, tested contract (`tests/rest_framework/test_converter.py::test_slug_related_field_raises_non_pk_relation`, `::test_many_related_field_non_pk_child_raises`, `::test_model_backed_slug_related_field_raises`) |
| E3 | Expanded rows: `DurationField`→`str`, `DictField`/`HStoreField`→`JSON`, `ModelField`→wrapped column's scalar, `IPAddressField`→`str`, `FilePathField` stays `str` | BUILT-CONFORMANT | `serializer_converter.py #"_BUILTIN_SCALAR_CONVERTERS"` (explicit rows for each) and `::_model_field_converter`; `::_is_enumerable_serializer_choice` excludes `FilePathField` from the enum upgrade. `tests/rest_framework/test_converter.py::test_expanded_scalar_matrix`, `::test_hstore_field_maps_to_json_via_mro`, `::test_model_field_maps_via_wrapped_model_field`, `::test_serializer_only_filepathfield_stays_str_not_enum` |
| E4 | Serializer-only `MultipleChoiceField` → `list[<generated enum>]` (base `list[str]`, upgraded at the build site like `ChoiceField`) | BUILT-CONFORMANT | `serializer_converter.py #"_CONVERT_MULTIPLE_CHOICE"` (base `list[str]`) upgraded at `::_serializer_choice_annotation #"return list[enum_cls]"`; `tests/rest_framework/test_converter.py::test_serializer_only_multiple_choicefield_becomes_list_enum` |
| E5 | Nested `ModelSerializer` / `ListSerializer` → fail-loud by default, unless explicitly opted in via `Meta.nested_fields = {…: NestedSerializerConfig(…)}`; the framework never auto-saves the relation | BUILT-CONFORMANT | `serializer_converter.py::_reject_nested_serializer` (the default raise, also called first inside `::resolve_serializer_field`); `rest_framework/inputs.py::NestedSerializerConfig` + `::_resolve_nested_field` (the opt-in recursion) + `::validate_nested_config_keys`; `tests/rest_framework/test_inputs.py::test_nested_field_without_opt_in_still_rejects`, `::test_nested_single_field_builds_recursive_input` |
| E6 | Serializer-only relation fields resolve their target from `field.queryset.model` (F4); neither a backing column nor a concrete `queryset.model` → `ConfigurationError` | BUILT-CONFORMANT | `serializer_converter.py::serializer_only_relation_annotation` (peels `child_relation` for the many case, reads `queryset`, raises via the `missing=` factory); `tests/rest_framework/test_converter.py::test_serializer_only_relation_resolves_target_from_queryset_model`, `::test_relation_with_no_backing_column_and_no_queryset_raises` |
| E7 | **M3** — a relation target with no registered primary `DjangoType` is a class-creation `ConfigurationError`, stricter than the form fallback, which stays byte-unchanged | BUILT-CONFORMANT | `serializer_converter.py::_require_relation_primary`, threaded as `primary_of=` into both `::serializer_only_relation_annotation` and the model-backed arm of `::resolve_serializer_field`. `tests/rest_framework/test_converter.py::test_relation_target_with_no_registered_primary_raises` |
| E8 | Requiredness = `field.required` minus `optional_fields`; `read_only` + `HiddenField` dropped; `PartialInput` all optional | BUILT-CONFORMANT | `inputs.py::_walk_serializer_fields #"required = False if is_partial else"`; `inputs.py::writable_serializer_fields` |
| E9 | **M2 nullability** — "Annotation nullability follows `field.allow_null`… `allow_null=False` keeps the bare annotation. This is independent of requiredness" | **SPEC-STALE** | `HEAD` widens on **either** axis: `rest_framework/inputs.py::_walk_serializer_fields #"nullable = getattr(field, \"allow_null\", False) or not required"`. So a `required=False, allow_null=False` field emits `T \| None` with an `UNSET` default, not the bare annotation. **`HEAD` is right and the spec sentence is wrong**: the same Decision forbids fabricating a GraphQL default ("the converter does not fabricate a GraphQL default that would shadow DRF's"), and a GraphQL input field that is neither nullable nor defaulted is *required* — so an omittable field must be nullable. The other three M2 bullets are conformant: omitted-vs-explicit-`None` is preserved (`rest_framework/resolvers.py #"UNSET`` stripped"`), `allow_blank` is not encoded (`examples/fakeshop/test_query/test_library_api.py #"allow_blank is NOT a GraphQL concern"`), and no default is fabricated (`tests/rest_framework/test_inputs.py::test_field_with_default_is_optional_no_fabricated_default`) |
| E10 | Two `Meta` namespaces; `Meta.optional_fields` is a no-op on `update` | BUILT-CONFORMANT | `inputs.py::build_serializer_input_class #"optional_fields = frozenset()"` under `if is_partial:`, with the names still validated first; `tests/rest_framework/test_inputs.py::test_serializer_meta_optional_fields_is_not_the_api` |
| E11 | Output direction not adopted; `is_input` accepted-and-ignored with **no** `if not is_input:` branch | BUILT-CONFORMANT | `serializer_converter.py::convert_serializer_field #"del is_input  # graphene-parity, accepted-and-ignored."` — the parameter is deleted before any use, so no branch exists; `tests/rest_framework/test_converter.py::test_is_input_parameter_is_accepted_and_ignored` |
| E12 | Shape identity is the generated field specs, not the field names (the two determinism-breakers) | BUILT-CONFORMANT | `inputs.py::SerializerInputShape` + `::build_serializer_input_class`; `tests/rest_framework/test_inputs.py::test_differing_annotations_yield_distinct_descriptor_names` (hook axis), `::test_descriptor_name_distinguishes_relation_target_model` |
| E13 | Naming + dedupe; no `"__all__"` sentinel for `fields` / `exclude` / `optional_fields` | BUILT-CONFORMANT | `utils/inputs.py::normalize_field_name_sequence` rejects any bare string; `tests/rest_framework/test_inputs.py::test_optional_fields_all_bare_string_rejected`, `::test_meta_fields_rejects_bare_string` |
| E14 | Create-required narrowing guard (bind-time, per declaration); `read_only` / `HiddenField` not dropped-required; update needs no guard | BUILT-CONFORMANT | `inputs.py::guard_create_required_serializer_fields` over `::_required_writable_field_names`; the guard is gated `if operation_kind == CREATE` at `rest_framework/sets.py::SerializerMutation.build_input #"if operation_kind == CREATE:"` |
| E15 | Model-backed relation **cardinality agreement** between the serializer field and its backing column | **SPEC-STALE** | An unspecced hardening that ships and is tested. `serializer_converter.py::_reject_relation_cardinality_mismatch` rejects a `PrimaryKeyRelatedField(many=True, source="category")` over a forward FK (and the inverse), and `::resolve_serializer_field #"if _relation_cardinality(field):"` then re-derives `kind` from the **serializer** field's cardinality so a many field over a `one_to_many` column emits a list id input. Decision 7's relation rows say nothing about either. `tests/rest_framework/test_converter.py::test_model_backed_relation_cardinality_mismatch_raises`, `::test_many_pk_related_field_over_reverse_fk_column_emits_multi`, `::test_many_pk_related_field_over_generic_relation_column_emits_multi`, `::test_single_pk_related_field_over_reverse_o2o_column_emits_single`, `::test_many_over_reverse_o2o_column_is_rejected` |

#### F — `### Import manifest — the DRY contract per rest_framework/ module`

| # | Contract | Grade | Evidence |
| --- | --- | --- | --- |
| F1 | `serializer_converter.py` row: the shared dispatch skeleton (**P1.4**), the unified conversion / field-spec dataclass (**P2.1**), `utils/inputs.py::graphql_camel_name`, `utils/relations.py::{relation_kind, is_forward_many_to_many, is_many_side_relation_kind}`, `Upload`, `types/converters.py::{convert_scalar, scalar_for_field, convert_choices_to_enum}`, `exceptions.ConfigurationError` | **SPEC-STALE** | Three named symbols are wrong and four real imports are unnamed. Wrong: `graphql_camel_name` lives at `utils/strings.py::graphql_camel_name`, not `utils/inputs.py`; `utils/relations.py::{relation_kind, is_forward_many_to_many, is_many_side_relation_kind}` are **not imported at all** (the relation classification runs through `mutations/inputs.py::model_column_write_kind` instead); `types/converters.py::convert_choices_to_enum` is not imported — `::build_enum_from_choices` is (the shared enum core it and the read side both call). Unnamed but real: `mutations/inputs.py::{annotate_queryset_relation, model_column_write_annotation, model_column_write_kind}`, `registry::{register_subsystem_clear, registry}`, `utils/strings.py::pascal_case`, `utils/inputs.py::{FieldConversionBase, InputFieldSpec, SCALAR, RELATION_SINGLE, RELATION_MULTI, FILE}` |
| F2 | `inputs.py` row: `utils/inputs.py::{build_strawberry_input_class, materialize_generated_input_class, normalize_field_name_sequence, graphql_camel_name}`, the input-namespace trio (**P2.2**), the shape-build cache (**P1.3**), the build/stash core (**P1.7**), `mutations/inputs.py::{_pascalize_token, build_payload_type, payload_object_slot, relation_input_annotation}` | **SPEC-STALE** | `HEAD` imports only `{CREATE, PARTIAL}` from `mutations/inputs.py`; `build_payload_type`, `payload_object_slot` and `relation_input_annotation` are **not** imported here (payload construction lives in `rest_framework/sets.py`), and `_pascalize_token` is imported from `utils/inputs.py` (D5). `graphql_camel_name` comes from `utils/strings.py`. The build/stash core (**P1.7**) is imported by `rest_framework/sets.py`, not by `inputs.py`. Eight further `utils/inputs.py` symbols the manifest omits are real imports: `generated_input_type_name`, `get_or_store_shape_build`, `guard_dropped_required`, `iter_input_field_collisions`, `optional_input_field`, `resolve_effective_fields`, `InputFieldSpec`, `make_input_namespace`/`make_shape_build_cache`; plus `registry::register_subsystem_clear` and seven symbols from `.serializer_converter` |

#### G — Definition of done item 2

| # | Contract | Grade | Evidence |
| --- | --- | --- | --- |
| G1 | Converter half: `convert_serializer_field` with a fail-loud, no-`String`-catch-all dispatch, the read-side converter reuse, and the reverse map with the id-like-suffix rule + `source` handling | BUILT-CONFORMANT | Composite of A1, A6, A7, A8, A9, C5. The single caveat is the reverse map's shape (A8), which is a spec-description defect, not a delivery gap |
| G2 | Inputs half: both inputs from the schema-time field set via the hook, `read_only`/`HiddenField` dropped, `optional_fields` forced optional, `SerializerInputShape` identity, canonical / descriptor-derived names + dedupe + collision error, the per-declaration create-required guard before the cache lookup, `Meta.injected_fields` its only subtraction, normalized fail-loud selectors, module globals | BUILT-CONFORMANT | Composite of B1–B10; the caveats are B5 and B6, both spec-description defects |

#### H — `## Edge cases and constraints` bearing on input generation / field conversion

| # | Edge case | Grade | Evidence |
| --- | --- | --- | --- |
| H1 | Serializer-only fields (no model column) become input fields validated by the serializer | BUILT-CONFORMANT | `serializer_converter.py::resolve_serializer_field` `else:` arm (`backing_model_field` returns `None`); `tests/rest_framework/test_inputs.py::test_serializer_only_field_included` |
| H2 | Serializer-only RELATION fields (F4) resolve via `field.queryset.model`; declared name preserved in `provided_data` | BUILT-CONFORMANT | Same evidence as E6; the declared name is `InputFieldSpec.target_name` (`::resolve_serializer_field #"target_name=field_name"`) |
| H3 | Relation target with no registered primary `DjangoType` (M3) → class-creation `ConfigurationError`, not a default-manager fallback | BUILT-CONFORMANT | Same evidence as E7 |
| H4 | Renamed serializer fields (`source`): GraphQL name from the declared name under the id-like rule, backing column from `source`, `provided_data` key the declared name | BUILT-CONFORMANT | `serializer_converter.py::serializer_field_graphql_name`, `::backing_model_field`, `::resolve_serializer_field #"source = field.source if"` |
| H5 | Dynamic / kwargs-requiring serializers at schema time: the hook, the guarded `.fields`, loud rejection | BUILT-CONFORMANT | Same evidence as B2 / E1 / C9 |
| H6 | `read_only` / `HiddenField` dropped from the input | BUILT-CONFORMANT | `inputs.py::writable_serializer_fields`; `tests/rest_framework/test_inputs.py::test_read_only_and_hidden_fields_dropped` |
| H7 | File / image serializer fields map to `Upload`, value lands in the serializer's `data` | BUILT-CONFORMANT | Same evidence as A5 / C3; the `data`-not-`files` routing is `rest_framework/resolvers.py #"FILE`` -> the ``Upload`` value, routed into ``data``"` |
| H8 | `many=True` related fields are a `ManyRelatedField` wrapper; target / id type read off `field.child_relation`, not `field` | BUILT-CONFORMANT | `serializer_converter.py::serializer_only_relation_annotation #"related_field = field.child_relation if kind == RELATION_MULTI else field"`; `::_reject_unsupported_relation_field` also peels `child_relation`. `tests/rest_framework/test_converter.py::test_many_related_field_is_relation_multi`, `::test_serializer_only_many_related_field_maps_to_globalid_list` |
| H9 | A nested writable serializer field NOT opted in fails loud | BUILT-CONFORMANT | Same evidence as E5; `tests/rest_framework/test_converter.py::test_nested_serializer_field_raises`, `::test_list_serializer_field_raises`, `::test_resolve_serializer_field_rejects_nested_over_relation_column` |
| H10 | Two distinct generated serializer inputs colliding on one GraphQL name always raise at finalize; only identical descriptors dedupe | BUILT-CONFORMANT | `inputs.py::materialize_serializer_input_class` (delegating to the `utils/inputs.py` ledger raise, then enriching the message with `::describe_serializer_input`); `tests/rest_framework/test_inputs.py::test_distinct_descriptors_colliding_on_one_name_raise`, `::test_materialize_collision_message_enriched_with_shape_description` |
| H11 | Two serializer fields colliding on one generated GraphQL input name (M-edge) raise before materialization, naming both | BUILT-CONFORMANT | `inputs.py::_collect_input_attr_collision_messages` over `utils/inputs.py::iter_input_field_collisions`, folded into the walk at `::_walk_serializer_fields`; `tests/rest_framework/test_inputs.py::test_relation_id_attr_collision_is_fail_loud`, `::test_camel_case_graphql_name_collision_is_fail_loud` |
| H12 | Two writable serializer fields sharing one `source` raise; a `read_only` field sharing a `source` with a writable one is fine | BUILT-CONFORMANT | The `source_of` arm of `::_collect_input_attr_collision_messages`, plus the runtime pair `inputs.py::writable_source_collisions` / `::writable_star_sources` / `::raise_writable_source_ownership_errors`; `tests/rest_framework/test_inputs.py::test_two_writable_fields_sharing_one_source_raise`, `::test_read_only_field_sharing_source_with_writable_is_accepted` |
| H13 | Same serializer, same field names, different shape → different descriptors → distinct deterministic names | BUILT-CONFORMANT | Same evidence as C10 / E12 |
| H14 | Create narrowing dropping a required serializer field is a bind-time `ConfigurationError`; `read_only`/`HiddenField` outside the writable basis; `Meta.injected_fields` the only subtraction; update unaffected | BUILT-CONFORMANT | Same evidence as B7 / B8 / E14 / C11 / C12 |

### High:

None.

The one DROPPED row does not violate a behavioral contract: I measured the contract it was
to protect and it holds at `HEAD` (D6). Per `docs/builder/BUILD.md` `## Severity definitions`,
High is reserved for a build that "does not deliver what the spec says"; here the build
delivers the reuse and omits only the mechanism that would keep delivering it.

### Medium:

#### D6 — the DRY import guard the spec makes the DoD check was never built (DROPPED)

`docs/SPECS/spec-039-serializer_mutations-0_0_13.md` `## Slice checklist` → Slice 1 →
`**DRY / reuse**` closes with:

> A grep guard that `rest_framework/serializer_converter.py` + `rest_framework/inputs.py`
> **import** these and do not redefine them is the DoD check.

**What is missing.** No executable guard exists in any of the three places one could live:
`tests/rest_framework/` holds exactly `test_converter.py`, `test_inputs.py`,
`test_resolvers.py`, `test_sets.py`, `test_soft_dependency.py` and none of them asserts an
import obligation; `scripts/` has no such checker; `.pre-commit-config.yaml` has no such hook.
Nothing supersedes it — `scripts/check_citations.py` is `path::Symbol`-resolution only and
cannot see a redefinition, and `fail_under = 100` cannot see one either (a re-spelled helper
is still fully covered).

**Why it matters.** The five promoted symbols (**P1.3**, **P1.4**, **P2.1**, **P2.2**,
**P2.3**) are the entire point of the Slice-1 DRY contract: they exist because
`forms/` had already become the second copy and `rest_framework/` was on track to be the
third. A future edit that inlines `pascalize_token`, hand-mirrors the input-namespace trio,
or re-spells the MRO walk in `rest_framework/` would pass every gate in this repo. The spec
names the guard precisely because prose cannot stop a re-spelling.

**What a fix would have to add.** One package test — the correct tree is `tests/` per
`AGENTS.md` (the property is a package-structure invariant, unreachable from a real
`/graphql` query, so the live tier does not apply). It should, for each of
`django_strawberry_framework/rest_framework/serializer_converter.py` and
`django_strawberry_framework/rest_framework/inputs.py`, assert that the module's binding for
each promoted symbol **is** the shared site's object (`inputs.pascalize_token is
utils.inputs.pascalize_token`, and the same for `convert_with_mro`, `InputFieldSpec`,
`make_input_namespace`, `make_shape_build_cache`, `build_strawberry_input_class`,
`materialize_generated_input_class`, `normalize_field_name_sequence`, `graphql_camel_name`).
An identity assertion is strictly better than a grep: it survives an import-style change and
cannot be satisfied by a same-named local re-definition.

Note for whoever writes it: the symbol list must be taken from `HEAD`, not from the spec's
manifest — F1 and F2 below record that the manifest names symbols that have moved or were
never imported, so a guard written from the spec text would fail on correct code.

### Low:

#### A stale code comment asserts a registration shape the code does not use

`django_strawberry_framework/rest_framework/inputs.py #"The row is a static STRING pair, so"`
sits directly above a `register_subsystem_clear(clear_serializer_input_namespace,
owner="rest_framework.input_namespace", before_bind=True)` call that passes a **callable**,
not a `(module_path, attr)` string pair. The comment is a survivor of the spec's original
**M4** design (see the note for Worker 1 below). Population measured: exactly **1**
occurrence of the phrase across `django_strawberry_framework/`. It states a false invariant
in shipped prose, so it is in the cycle's `.py` fence and cheap to correct; it is Low because
nothing reads it but a human.

#### `_is_consumer_declared` answers "not declared" for an unbound field

`django_strawberry_framework/rest_framework/serializer_converter.py::_is_consumer_declared`
returns `False` when `field.parent is None`. That answer routes the field down the
auto-generated arm of `::_model_backed_scalar_annotation`, which **skips** the
type-override conflict raise. This is a fail-open shape in `docs/builder/BUILD.md`
`### Fail-open shapes`'s sense — a default reached because the input was *incoherent*
(declared-ness unknowable) rather than *absent*, converting "cannot determine" into
"permit the model column to win". It is Low rather than Medium because the reachable
surface is narrow: `rest_framework/sets.py::_validate_schema_field_map` already requires
every hook-returned field to carry a bound `field_name` matching its key, so only a hook
that sets `field_name` without calling `bind()` reaches it. Behavior is pinned as intended
by `tests/rest_framework/test_converter.py::test_unbound_model_backed_field_is_treated_as_auto_generated`,
so if the maintainer wants the strict answer instead, that row changes too.

### DRY findings

- **Duplicated error-message tail (repeated literal).** The sentence
  `". A nested serializer opted in via Meta.nested_fields must expose a stable,
  request-independent no-arg .fields (override get_serializer_for_schema() on the mutation to
  return a stable field map)."` is spelled twice inside
  `django_strawberry_framework/rest_framework/inputs.py` — once in `::_fingerprint_nested`
  and once in `::_resolve_nested_field`. Surfaced mechanically by
  `scripts/review_inspect.py`'s **Repeated string literals** section
  (`2x`, the only multi-word repeat in the file). Per `docs/builder/BUILD.md`
  `## Severity definitions` a repeated error fragment that should be a named constant is
  Medium-tier; it is recorded here rather than under `### Medium:` because it is a
  consolidation opportunity, not a spec row, and this pass introduces no code.
  Recommended shape: one module-level constant, both call sites interpolating it.
- **The provisional input-type name is derived in two places.** The
  `f"{serializer_class.__name__}{'PartialInput' if … else 'Input'}"` expression appears in
  `rest_framework/inputs.py::resolve_injected_field_specs` and
  `::build_serializer_input_class`. The two must agree — `resolve_injected_field_specs`'s
  own docstring explains that an operation-blind provisional would make
  `resolvers.py::_assert_field_agreement` raise on every invocation of a valid update
  declaration — so a divergence between them is a live-failure mode, not cosmetic. It should
  be one helper. (`utils/inputs.py::generated_input_type_name` is the *final*-name deriver
  and does not cover the provisional.) `review_inspect.py` flags the shared `3x 'PartialInput'`
  literal.
- **Existence challenge: none raised.** The five promoted abstractions each have two or more
  real callers, verified: `convert_with_mro` (forms, serializer, filters), `InputFieldSpec`
  (serializer + resolvers + tests), `make_input_namespace` (mutations, forms, serializer, and
  composed into `make_set_input_namespace`), `make_shape_build_cache` (mutations, forms,
  serializer), `pascalize_token` (mutations, forms, serializer). None is a one-caller
  indirection, so there is nothing here for the maintainer to decide.
- **Otherwise clean.** The remaining repeated literals in both shadow overviews are
  diagnostic message *prefixes* (`9x "Serializer field"`, `14x "SerializerMutation"`), which
  are message-composition nouns rather than duplicated logic, and consolidating them would
  make the error strings harder to read at their call sites.

### Static helper use

`uv run python scripts/review_inspect.py <file> --output-dir docs/shadow` was run on both
audited modules (`docs/builder/BUILD.md` `### When to run the helper during build` — both
are well past the 30-line threshold, and neither is a pure-class-definition module):

- `docs/shadow/django_strawberry_framework__rest_framework__serializer_converter.overview.md`
- `docs/shadow/django_strawberry_framework__rest_framework__inputs.overview.md`

Its **Repeated string literals** section is the source of both DRY findings above. No skip
was taken. Shadow line numbers are not cited anywhere in this artifact; every reference is
symbol-qualified per `AGENTS.md` rule 27.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. This pass is read-only and
changes no file; `__all__` and the re-export list are untouched.

### CHANGELOG sanity

Not applicable; this pass did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; this pass did not modify docs/release/KANBAN/archive surfaces. (The only file
it writes is this artifact, which the cycle's plan lists.)

### Failability proofs

`None; this pass introduced no new boundary.` This is a read-only audit — no source, no test,
no transient mutation. The failability-proof source carve-out in `docs/builder/worker-3.md`
`## Scope` does not apply, and the mandatory re-run floor's "empty re-run set is legal only
when the diff introduces no boundary that meets the floor" condition is satisfied
vacuously: the diff is empty.

Where the audit needed to prove a *raising* claim rather than read one, it used the existing
suite as the instrument and ran it (below) instead of asserting the raise from the source —
specifically A6 (the no-catch-all fallthrough), E1 (the guard wrapping `.fields`), and B7
(the guard surviving a cache hit).

### Hot-path budget

Not applicable; the plan declares `none` for Slices 0–1d (no executable change).

### Floor verification

Not applicable; the plan declares floor-verification scope `none` for Slices 0–2.

### Validation run

- `uv run pytest -n0 tests/rest_framework/test_converter.py tests/rest_framework/test_inputs.py --no-cov`
  → **190 passed** in 0.24s (76 + 94 top-level test defs plus parametrized expansions;
  no `--cov*` flag, per `docs/builder/BUILD.md` `## Coverage is the maintainer's gate`).
- `git status --short` after the pass: unchanged from the pre-pass baseline except for this
  artifact and the two gitignored `docs/shadow/` files. No source or test file was touched.

### What looks solid

- **The central promise of Slice 1 — a raising fallthrough with no
  `serializers.Field → String` catch-all — is genuinely there and provably fires.** The
  skeleton's last statement is a `raise`, no base-`Field` key exists in the registry to
  shadow it, and the extension hook (`register_serializer_field_converter`) is the sanctioned
  way to add a mapping rather than a hole in the contract. `utils/converters.py::convert_with_mro`
  even reads the MRO through `type.__dict__["__mro__"]`'s raw getset descriptor so a hostile
  metaclass cannot route a field around the typed unsupported path — that is the
  fail-*closed* instinct, applied where nobody asked for it.
- **The DRY promotions are real, not narrated.** Every one of the five `P*` obligations
  resolves to a single site with multiple importers, and `utils/converters.py` has since
  picked up a third rider (`filters/inputs.py`, per spec-053) — the promotion paid off
  beyond the flavor it was made for.
- **The descriptor identity is stronger than the spec asked for, in the direction that
  matters.** Folding the *post-widening* annotation and the generated description into the
  descriptor closes two silent-cache-reuse holes the spec's enumeration would have left open,
  and both are pinned by their own rows.
- **Diagnostics aggregate.** `::_walk_serializer_fields` collects every per-field conversion
  error and every collision into one `ConfigurationError`, raising a single problem verbatim
  so existing `pytest.raises(match=…)` substrings survive. That is the difference between a
  consumer fixing six fields in one pass and six reruns.
- **The test tier is dense and mostly parametrized rather than looped**, so the node-id count
  tracks the assertion count (`::test_id_like_suffix_rule`, `::test_scalar_field_annotations`,
  `::test_expanded_scalar_matrix` are all parametrized). The M2 axes are split correctly
  between tiers: `allow_blank`-invisible-in-SDL and the two-hooks-differing-only-in-`allow_null`
  case are pinned **live** at `examples/fakeshop/test_query/test_library_api.py`, with the
  package tier carrying the focused descriptor-token backstop.

### Temp test verification

- No temp tests were created. `docs/builder/temp-tests/039-audit-1/` was **not** created and
  does not exist — every claim in this artifact is settled by reading `HEAD` plus one focused
  run of the existing suite, so a scratch test would have proved nothing the suite does not.
- Disposition: n/a — nothing to promote, nothing to delete.

### Notes for Worker 1 (spec reconciliation)

Nine SPEC-STALE rows are owed a spec edit in Slice 2, plus one DROPPED row that escalates to
Slice 3. Every change below states the **corrected contract directly** — no chronology in the
spec (`docs/builder/BUILD.md` `## Spec rationale extraction`); the *explanation* of each
change belongs in `docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md`.

**The three sentences to rewrite first** — these are the ones a reader would act on and be
wrong:

1. **`### Decision 7` → "Nullability and defaults (M2)" → first bullet (E9).** The sentence
   "**Annotation nullability follows `field.allow_null`.** A field with `allow_null=True`
   gets a nullable GraphQL annotation (`T | None` / `Optional[T]`); `allow_null=False` keeps
   the bare annotation. This is independent of requiredness" is false at `HEAD` and cannot be
   made true without contradicting the bullet two lines below it (which forbids fabricating a
   GraphQL default). The corrected contract: *the annotation is nullable when the field is
   `allow_null=True` **or** when it is optional in the generated input, and every nullable
   field carries a `strawberry.UNSET` default so the key is omittable; only a
   `required=True, allow_null=False` field emits the bare non-null annotation with no
   default.* A reader implementing the current sentence would emit non-null optional input
   fields, which GraphQL treats as required. This is the highest-value rewrite in the set.

2. **`### Import manifest — the DRY contract per rest_framework/ module`, both graded rows
   (F1, F2).** The manifest is the spec's own "DoD-checkable summary", and three of its named
   symbols do not exist where it says (`utils/inputs.py::graphql_camel_name` →
   `utils/strings.py::graphql_camel_name`; `types/converters.py::convert_choices_to_enum` →
   `::build_enum_from_choices`; `mutations/inputs.py::_pascalize_token` →
   `utils/inputs.py::pascalize_token`), one group is not imported at all
   (`utils/relations.py::{relation_kind, is_forward_many_to_many, is_many_side_relation_kind}` —
   relation classification runs through `mutations/inputs.py::model_column_write_kind`), and
   three named `mutations/inputs.py` symbols (`build_payload_type`, `payload_object_slot`,
   `relation_input_annotation`) belong to `rest_framework/sets.py`, not `inputs.py`. The
   knock-on is that the **`### Small reuses to pin; deliberately not applicable (P3)`**
   section is stale in the same two ways: it pins `utils/inputs.py::graphql_camel_name`, and
   it declares `utils/strings.py` "deliberately NOT applicable" while telling the reader not
   to conflate `snake_case` with `graphql_camel_name` — but `graphql_camel_name` **is** in
   `utils/strings.py` now, and `serializer_converter.py` imports `pascal_case` from there too.
   Sweep both sections in one edit; they are the pair that falsifies each other.
   This matters operationally: the D6 fix below must be written from `HEAD`, and anyone
   writing it from the manifest would produce a guard that fails on correct code.

3. **`### Decision 7` → the converter dispatch paragraph (E2) and the relation rows.** The
   spec says relation kinds are "matched first by `isinstance` (`PrimaryKeyRelatedField` /
   `ManyRelatedField`, `FileField` / `ImageField`)". The shipped contract is materially
   stricter and the spec is silent on it: the single-relation precheck matches the **broad**
   `serializers.RelatedField` and then **rejects** any non-`PrimaryKeyRelatedField` — a
   `SlugRelatedField`, `HyperlinkedRelatedField`, or custom writable `RelatedField` is a
   `ConfigurationError`, because the package types every relation input as an id that decodes
   to a primary key. A DRF migrant reading the current Decision would reasonably expect a
   `SlugRelatedField` to work. The nested-serializer reject also runs *before* everything
   else in the precheck table (so a nested serializer is named rather than list-mapped),
   which the spec's ordering sentence does not mention.

The remaining six, in spec order:

4. **`## Slice checklist` → Slice 1 converter sub-bullet, and `### Decision 7` →
   "**Reverse map**" (A8).** The reverse map is no longer an
   `input_attr → (serializer_field_name, source, kind)` triple with four kinds. It is
   `utils/inputs.py::InputFieldSpec` carrying nine axes
   (`input_attr / graphql_name / target_name / kind / source / related_model / nested_specs /
   annotation_repr / required`), and `kind` has six members — the spec's four plus
   `nested_single` / `nested_multi` (`serializer_converter.py #"NESTED_SINGLE: str"`). Both
   homes state the triple; correct them together.

5. **`## Slice checklist` → Slice 1 inputs sub-bullet, and `### Decision 7` → "**Shape
   identity is the generated field specs…**" (B5).** The descriptor's enumerated tuple omits
   two shipped axes and mis-states a third: `descriptions` is an independent axis (a
   description-only hook divergence must not share a class), and the annotation axis is the
   **post-nullable-widening** repr, not the base annotation — which is exactly what makes a
   `required=True, allow_null=False` vs `required=True, allow_null=True` pair diverge. Both
   are pinned by their own tests, so the spec is describing a weaker identity than shipped.

6. **`### Decision 7` → "**Naming + dedupe**" (B6).** The spec reserves the canonical
   `<Serializer>Input` name for "the default full shape (all input fields, default
   requiredness, no `optional_fields`)". `HEAD` is stricter: the canonical name is granted
   only when the shape's per-field identity **matches the identity the default no-arg
   discovery produces** (`rest_framework/inputs.py::_default_full_shape_identity`), so a
   `get_serializer_for_schema()` hook returning a differently-shaped "full" field set takes a
   descriptor-derived name. Without this, two distinct descriptors would collide on the
   canonical name at materialize. The spec's definition currently licenses the collision.

7. **`### Decision 7` → the model-column overlap paragraph (E15) — a missing contract, not a
   wrong one.** `serializer_converter.py::_reject_relation_cardinality_mismatch` rejects a
   serializer relation whose `many=` shape disagrees with its backing model relation, and
   `::resolve_serializer_field` then re-derives the emitted kind from the **serializer**
   field's cardinality (so a `PrimaryKeyRelatedField(many=True)` over a reverse FK or a
   `GenericRelation` emits a list id input, not the single id the column classifier alone
   would give). Five tests pin it. Decision 7 says nothing about either half. The invariant to
   state: *the generated input must describe the same shape the runtime serializer validates.*

8. **`## Slice checklist` → Slice 1 `**DRY / reuse**`, and `### Cross-flavor reuse and DRY
   obligations` **P2.3** (D5).** Both name `mutations/inputs.py::_pascalize_token`. The
   encoder was promoted to `utils/inputs.py::pascalize_token`;
   `mutations/inputs.py::_pascalize_token` is now only an alias, and `rest_framework/inputs.py`
   imports from the new home. The DRY intent (no third encoder) is intact — only the address
   moved. Note that **P1.3**'s `make_shape_build_cache()` and **P2.2**'s
   `make_input_namespace(...)` both landed exactly as written, so this is the one promotion
   row whose address needs correcting.

9. **Escalated (a `.py` edit, in fence, no spec change): a false comment in shipped source.**
   `rest_framework/inputs.py #"The row is a static STRING pair, so"` describes the **M4**
   seam as the spec originally designed it — `register_subsystem_clear(module_path, attr)`
   with lazily-resolved string rows. `registry.py::register_subsystem_clear` now takes a
   **callable** plus a keyword `owner` and `before_bind`, and `_clear_if_importable` survives
   only for connection-class cache eviction. The comment therefore asserts an invariant the
   line beneath it does not hold. Exactly one occurrence; correcting it is a one-line edit in
   Slice 2 or 3. **The M4 / P1.6 contract row itself belongs to Slice 1b's population**
   (`## Definition of done` item 3 / the Slice 2 finalizer-reset checklist), so I have not
   graded it here — but 1b should expect a SPEC-STALE on the seam's *signature*, since both
   of my files call the new form (`serializer_converter.py #"register_subsystem_clear(clear_serializer_choice_enums"`
   and `inputs.py #"owner=\"rest_framework.input_namespace\""`), and the soft-dependency
   property the spec attributes to lazy string resolution is now carried by a different
   mechanism (only an imported owner can register, so a DRF-absent build registers nothing).

**One row escalates past the spec to a Slice 3 code pass:** D6, above. It is the cycle's only
DROPPED row.

**Cross-references, not findings.** Two shipped surfaces in `serializer_converter.py` are
spec'd under `## Round-6 improvements`, which is Slice 1d's population, so I graded neither:
`::register_serializer_field_converter` (rev6 #11, the public converter registry) and
`::serializer_field_description` (rev6 #9, DRF metadata threaded into the SDL). Both look
built; 1d owns the grade. Likewise `## Round-6 improvements` rev6 #17 (opt-in nested
serializer input) is graded here only as the Decision 7 clause E5 states it, not as its own
rev6 row.

### Review outcome

`review-accepted`.

This pass has no `built` predecessor — it is a read-only audit that hands to Worker 1 for
spec reconciliation (Slice 2) and, for the single DROPPED row, to a Slice 3 code pass.
Every row in the population carries a grade with cited evidence; the one DROPPED row and the
zero DEVIATED rows are recorded above under their severity headings. No finding blocks: the
Medium is a spec-owed gap Worker 1 routes, and both Lows are in-fence one-line corrections.
