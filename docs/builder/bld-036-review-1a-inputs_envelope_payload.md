# Build: R1a — conformance audit, input generation / `FieldError` envelope / payload wrapper

Spec reference: `docs/SPECS/spec-036-mutations-0_0_11.md` — Slice 1, Decisions 6 / 7 / 14, `## User-facing API` (input / payload / error shapes), `## Error shapes`, DoD item 2, and the `## Edge cases and constraints` bullets about input shape, generated naming, and the `UNSET` / `null` / value tri-state.
Status: final-accepted

## Plan (Worker 1)

Not applicable to this cohort. R1a is a **read-only conformance audit** dispatched directly by the build plan (`docs/builder/build-036-mutations-0_0_11.md` `## Ownership partition`, cohort R1a); it has no Worker 1 planning pass, no Worker 2 build pass, and no diff of its own. The plan's `## Conformance grading vocabulary` is the contract this pass discharges; the graded inventory below stands in for both the plan's `### Spec slice checklist (verbatim)` and the review section.

---

## Build report (Worker 2)

Not applicable; this cohort lands no source. Files written this pass: this artifact and `docs/builder/worker-memory/worker-3-036.md`.

### Failability proofs

**None performed, and the omission is deliberate.** `docs/builder/BUILD.md` `### Who performs it` licenses a Worker 3 mutation only under the narrow carve-out, and the carve-out's restore is `cp` from a pre-mutation scratch copy of the **live** file. Every source file in this cohort's territory is dirty with a concurrent session's active work in exactly the regions a proof would mutate:

```
django_strawberry_framework/mutations/inputs.py             69 diff lines vs HEAD
django_strawberry_framework/utils/inputs.py                166 diff lines vs HEAD
django_strawberry_framework/utils/errors.py                247 diff lines vs HEAD
django_strawberry_framework/utils/write_values.py           66 diff lines vs HEAD
tests/mutations/test_inputs.py                              16 diff lines vs HEAD
tests/utils/test_inputs.py                                  28 diff lines vs HEAD
tests/utils/test_errors.py                             IDENTICAL to HEAD
```

(measured `diff -q` / `diff | grep -c '^[<>]'` against the `HEAD` snapshot at `7426e7e7d8aa447e89fee75088447d6a506dec12`.)

A `cp`-and-restore round trip against a file another session is mid-edit would clobber their write if it lands between the copy and the restore, and the restore cannot be distinguished from a revert. The task explicitly permits declining on that ground, and I decline. The weak-pinning finding below (`### Medium:` #1) is established by a **read-level** proof instead — a whole-tree grep showing exactly one site inspects the surface in question and that it makes no assertion capable of failing — which needs no mutation.

### Hot-path budget

Not applicable; plan declares R1 lands no source and declares hot path `none`.

### Floor verification

Not applicable; plan declares floor-verification scope `none` for R1.

---

## Review (Worker 3)

### Method, and which tree each claim measures

Two different trees, deliberately:

- **Source and tests are graded at `HEAD`**, read from the read-only snapshot at
  `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/f4a12072-1e3a-4913-8249-dd800f1972ce/scratchpad/head-036/`
  (commit `7426e7e7d8aa447e89fee75088447d6a506dec12`), per the plan's `### The audit measures HEAD, not the working tree`. No `git stash` / `checkout` / `restore` / `worktree` was used anywhere in this pass.
- **The spec is read from the live working tree** (`docs/SPECS/spec-036-mutations-0_0_11.md`, 623 lines), because Slice 0's rationale extraction is this cycle's own uncommitted output and is the text R2 will edit. Grading against the `HEAD` spec would route R2 to line ranges that no longer exist. Every spec citation below is symbol/substring-qualified so it survives Slice 0's reflow either way.
- No test was run. Running one would exercise the dirty tree and could say nothing about `HEAD`.
- **The rationale companion was read as the instrument `docs/builder/BUILD.md` `### Who reads it, and when` describes it as** — `docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md`, Decisions 2, 6, 7, 14 (Justification, `### Alternatives considered (and rejected)`, `### Changes this Decision underwent`) plus the `## Revision history`. **No finding below re-raises a rejected alternative.** Checked specifically: Decision 6 rejects a single all-optional input, nested-object FK input, and reusing the output type as the input — none of which I propose; Decision 7 rejects the disjoint `Type | OperationInfo` union and raising `GraphQLError` for validation failures — likewise. The companion records **no** alternative about where `FieldError` should *live*, so the escalation at item N6 is a genuinely open question rather than a settled one. The companion also confirmed two of my grades are the spec's deliberate `0.0.11` intent rather than drafting slips: CR-6's `NotImplementedError` was pinned in **Revision 4** (row 31) and the M2M-always-optional carve-out in **Revision 3 (AR-M1)** (row 22).

Inline `path:NN` refs appear as review convenience only (per `AGENTS.md` rule 27's per-cycle-scratchpad carve-out); every graded row cites the symbol-qualified form.

### Graded contract inventory

`SRC` column: `HEAD` unless noted. Rows are grouped by the spec site R2 must edit, so a contract stated at three sites is three rows — R2 authors three edits.

| # | Contract (spec site) | Grade | `HEAD` evidence |
|---|---|---|---|
| 1 | Slice 1 `#"a BFS-free, single-model input factory"` — the generator is single-model, no related-set BFS | CONFORMS | `django_strawberry_framework/mutations/inputs.py::build_mutation_input` walks `mutation_input_shape(...).selected` only; the module docstring states the divergence from the set families explicitly (`mutations/inputs.py #"not a related-set BFS"`) |
| 2 | Slice 1 `#"narrowed by the mutation's own"` — editable set narrowed by the mutation's `Meta.fields` / `Meta.exclude`, **not** the read `DjangoType` selection (Medium-4) | CONFORMS | `mutations/inputs.py::editable_input_fields` takes `fields` / `exclude` kwargs and never consults the registry's read selection |
| 3 | Slice 1 / Decision 6 — `<Model>Input`: a field is required **only when it has no usable default** (no `default`, `null=False`, `blank=False`) — Major-1, explicitly not a blanket "every field required" | CONFORMS | `mutations/inputs.py::input_field_required` — `if field.has_default() or field.null: return False; return not field.blank` |
| 4 | Slice 1 / Decision 6 — `<Model>PartialInput`: every field optional, defaulting to `strawberry.UNSET` | CONFORMS | `mutations/inputs.py::build_mutation_input #"required = is_create and not is_m2m"` → `PARTIAL` never sets `required`; `utils/inputs.py::optional_input_field` supplies `strawberry.UNSET` |
| 5 | Slice 1 — editable selection excludes the **pk** | CONFORMS | `mutations/inputs.py::editable_input_fields #"not getattr(field, \"primary_key\", False)"` (and its docstring notes the auto `AutoField` reports `editable=True`, so `primary_key` is what drops it) |
| 6 | Slice 1 — excludes `auto_now` / `auto_now_add` / `editable=False` columns | CONFORMS | same predicate, `#"getattr(field, \"editable\", False)"` |
| 7 | Slice 1 — excludes reverse relations | CONFORMS | same predicate, `#"hasattr(field, \"column\")"` plus the forward-only M2M arm via `utils/relations.py::is_forward_many_to_many` |
| 8 | Slice 1 / Decision 6 — forward FK / OneToOne become a single `<field>_id` input | CONFORMS | `mutations/inputs.py::relation_input_annotation #"python_attr = field.name if many else f\"{field.name}_id\""` |
| 9 | Slice 1 / Decision 6 — that id is `GlobalID` for a Relay-Node target, else the raw pk scalar | CONFORMS | `mutations/inputs.py::relation_id_scalar` |
| 10 | Slice 1 / Decision 6 — M2M becomes `list[<id>]` | CONFORMS | `mutations/inputs.py::relation_id_annotation #"list[id_scalar] if many else id_scalar"` |
| 11 | Slice 1 / Decision 6 / DoD 2 — the canonical full editable shape takes the stable `<Model>Input` / `<Model>PartialInput` name | CONFORMS | `mutations/inputs.py::mutation_input_type_name` → `utils/inputs.py::name_set_input_type_name #"is_full_shape=frozenset(effective_field_names) == frozenset(full_field_names)"` |
| 12 | Slice 1 / Decision 6 — a narrowed shape takes a **deterministic shape-derived** name | CONFORMS | `utils/inputs.py::generated_input_type_name #"return f\"{base_name}{token}{suffix}\""`, token from `utils/inputs.py::pascalize_token` (injective, one leading capital per field name) |
| 13 | Slice 1 / Decision 6 / Decision 7 — two **distinct** shapes colliding on one generated name raise `ConfigurationError` at finalization, naming both (AR-M6) | CONFORMS | `utils/inputs.py::materialize_generated_input_class #"if existing is not None"` → `utils/inputs.py::duplicate_name_message`; reached only through the phase-2.5 bind |
| 14 | Slice 1 — all materialized as module globals so **identical shapes dedupe** | CONFORMS | `mutations/inputs.py::materialize_mutation_input_class` + `utils/inputs.py::make_input_namespace`; the idempotent `(name, cls)` clause is the dedupe. Shape-level dedupe is `mutations/sets.py::_materialize_input_for #"get_or_store_shape_build"` |
| 15 | Slice 1 `#"The public \`FieldError\` \`@strawberry.type\` (\`field: str\`, \`messages: list[str]\`)"` | **SUPERSEDED** | `mutations/inputs.py::FieldError` has **four** fields at `HEAD`: `field: str`, `messages: list[str]`, `codes: list[str]`, `path: list[str]`. Added by **spec-039 / `0.0.13` serializer mutations** (commit `951945b7`, 2026-07-01, whose diff touches `docs/spec-039-serializer_mutations-0_0_13.md`) |
| 16 | Slice 1 / Decision 7 — `<Name>Payload` puts the mutated object in the uniform slot: `node` for a Relay-Node target, `result` otherwise (AR-H5) | CONFORMS | `mutations/inputs.py::payload_object_slot` |
| 17 | Slice 1 / Decision 7 — that object slot is **nullable** | CONFORMS | `mutations/inputs.py::build_payload_type #"{slot: object_type | None"` |
| 18 | Slice 1 / Decision 7 — plus `errors: list[FieldError]!` (non-null list of non-null) | CONFORMS | `mutations/inputs.py::build_payload_type #"\"errors\": list[FieldError]"` — a bare `list[T]` renders `[T!]!` |
| 19 | Slice 1 sub-bullet 3 — the `spec-010` relation-override contract holds on the input side: a consumer-authored input field is honored, not clobbered | CONFORMS | `mutations/inputs.py::build_mutation_input #"if python_attr in overrides"` (skip), wired from `Meta.input_class` by `mutations/sets.py::_materialize_merged_input` |
| 20 | Slice 1 sub-bullet 4 — the enumerated `tests/mutations/test_inputs.py` matrix (required/optional shapes, FK/O2O/M2M id mapping, pk/auto exclusion, Relay-vs-non-Relay id, stable + shape-derived naming, collision error, `node`/`result` slot) | CONFORMS | present at `HEAD`; e.g. `tests/mutations/test_inputs.py::test_create_input_required_and_optional_shapes`, `::test_fk_to_relay_target_uses_globalid_id`, `::test_fk_to_non_relay_target_uses_raw_pk_scalar`, `::test_m2m_to_relay_target_becomes_list_of_globalid`, `::test_type_name_narrowed_shape_is_deterministic_and_distinct`, `::test_distinct_shapes_colliding_on_one_name_raise_configuration_error`, `::test_payload_node_slot_for_relay_target` |
| 21 | Slice 1 sub-bullet 4 `#"consumer \`input_class\` following the generated scheme (AR-M2)"` — claimed as `tests/mutations/test_inputs.py` coverage | **STALE-DESCRIPTION** | The pins exist but live in the sibling file: `tests/mutations/test_sets.py::test_meta_input_class_diverging_field_names_raises` / `::test_meta_input_class_following_scheme_validates_clean` / `::test_meta_input_class_not_strawberry_input_raises`. `tests/mutations/test_inputs.py` has no `input_class` test (its only `input_class` hits are `materialize_mutation_input_class` / `build_strawberry_input_class` substrings). Slice 2's coverage bullet already claims the same pins correctly |
| 22 | Decision 6 `#"An M2M field is *always* optional even in the create input"` | CONFORMS | `mutations/inputs.py::build_mutation_input #"required = is_create and not is_m2m"`; pinned by `tests/mutations/test_inputs.py::test_m2m_to_relay_target_becomes_list_of_globalid` |
| 23 | Decision 6 `#"A blanket \"every editable field required\" rule was rejected"` — `description` / `isPrivate` stay optional | CONFORMS | `tests/mutations/test_inputs.py::test_input_field_required_rule` pins all three shapes (`name` True, `description` False, `is_private` False) |
| 24 | Decision 6 — `blank` participates for text/char fields | CONFORMS | `mutations/inputs.py::input_field_required #"return not field.blank"` |
| 25 | Decision 6 — scalars map through the **same** read-side scalar / choice-enum / specialized-scalar converters | CONFORMS | `mutations/inputs.py` imports `convert_scalar` / `scalar_for_field` from `types/converters.py`; `mutations/inputs.py::model_column_write_annotation #"convert_scalar(field, type_name, force_nullable=False)"` |
| 26 | Decision 6 — a relation `GlobalID` is type-checked against the relation target at decode, never coerced cross-model | CONFORMS | `utils/write_values.py::type_check_relation_id #"decode_model_global_id(value, related_model)"`; non-`OK` → `utils/errors.py::relation_field_error` |
| 27 | Decision 6 — a generated input's identity is `(model, operation kind, frozenset(effective field names))` | CONFORMS | `mutations/inputs.py::MutationInputShape` / `::mutation_input_shape #"cache_key=(model, operation_kind, effective_field_names)"` |
| 28 | Decision 6 / Edge cases — two narrowings to the *same* effective shape still dedupe to one type | CONFORMS | the `cache_key` is the **effective** frozenset, not the raw `(fields, exclude)` spelling — `mutations/sets.py::_materialize_input_for #"the EFFECTIVE field set, NOT the raw"` |
| 29 | Decision 6 — `Meta.input_class` / `partial_input_class` override **specific** fields and the generator **merges** in the rest | CONFORMS | `mutations/sets.py::_materialize_merged_input` — class inheritance `(consumer, remainder)`, disjoint by construction via `overrides` |
| 30 | Decision 6 — a custom input must use the generated field-naming scheme (AR-M2), else rejected | CONFORMS | `mutations/sets.py::_validate_input_class`; message `#"diverge from the generated naming scheme"` (seam: R1b owns `sets.py`) |
| 31 | Decision 6 `#"File / image columns are the one exception to the merge override (CR-6)"` — `NotImplementedError` for `FileField` / `ImageField` **before** the override set is consulted | **SUPERSEDED** | `HEAD` maps a file column to `Upload`: `mutations/inputs.py::model_column_write_annotation #"if kind == FILE: return Upload"`. The docstring names the change — `mutations/inputs.py::model_column_input_annotation #"spec-037 lifted the spec-036"`. Attribution: **`DONE-037-0.0.11`** (`Upload` scalar + file/image mapping) |
| 32 | Decision 6 (CR-6) `#"a consumer cannot substitute a custom field for a file column via \`input_class\` in \`0.0.11\`"` and `#"a file column is removed from the write surface only via \`Meta.exclude\`"` | **SUPERSEDED** | file columns participate in the override skip like any scalar; pinned by `tests/mutations/test_inputs.py::test_file_field_consumer_override_skips_generated_upload_field`. Attribution: **`DONE-037-0.0.11`** |
| 33 | Decision 7 `#"a public \`FieldError\` \`@strawberry.type\` (\`field: str\`, \`messages: list[str]\`) — graphene-django's \`ErrorType\` shape"` | **SUPERSEDED** | same as row 15 — the type carries `codes` and `path` at `HEAD`. This is the site that also makes the **freeze** promise (`#"reuse the byte-identical type"` in Decision 2 / the spec preamble), which spec-039 broke |
| 34 | Decision 7 — a generated per-mutation `<Name>Payload` carrying the mutated object (nullable) **and** `errors: list[FieldError]!` | CONFORMS | `mutations/inputs.py::build_payload_type`; name `#"type(f\"{mutation_name}Payload\", (), namespace)"` |
| 35 | Decision 7 — on success `errors` empty and the object set; on validation failure the object is `null` and `errors` carries one entry per offending field | CONFORMS | envelope side: `utils/errors.py::validation_error_to_field_errors` emits one leaf per `error_dict` key; `errors` defaults to `[]` via `strawberry.field(default_factory=list)`. Resolver short-circuit is R1c's seam (`mutations/resolvers.py`) |
| 36 | Decision 7 / Error shapes — the model's `NON_FIELD_ERRORS` bucket, and any constraint- or `clean()`-level error not tied to one field, maps to a `FieldError` whose `field` is the `"__all__"` sentinel (AR-M3) | CONFORMS | `utils/errors.py::validation_error_to_field_errors #"path = \"\" if normalized_name == NON_FIELD_ERRORS else normalized_name"` → `utils/errors.py::field_error #"key = normalized_path if normalized_path else NON_FIELD_ERROR_KEY"` |
| 37 | Decision 7 — the sentinel is Django's own `NON_FIELD_ERRORS` value, a stable documented part of the public contract, single-sourced | CONFORMS | `mutations/inputs.py #"NON_FIELD_ERROR_KEY: str = NON_FIELD_ERRORS"`; pinned by `tests/mutations/test_inputs.py::test_non_field_error_key_is_django_all_sentinel` |
| 38 | Decision 7 (AR-H5) — the payload object field is **never** model-derived; **no `property`-named field is ever generated** | CONFORMS | `mutations/inputs.py::build_payload_type` keys the namespace off `slot`, never the model; pinned by `tests/mutations/test_inputs.py::test_payload_slot_never_model_derived_for_property_like_model` |
| 39 | Decision 7 (AR-M6) — two mutations generating the same `<Name>Payload` for **distinct** shapes raise `ConfigurationError` at finalization naming both | CONFORMS | payloads ride the same ledger (`mutations/sets.py #"Payload classes ride the SAME"`); pinned by `tests/mutations/test_sets.py #"Two mutations generating the same \`\`<Name>Payload\`\` for distinct shapes raise."` |
| 40 | Decision 7 — the payload is materialized at phase 2.5, so `DjangoMutationField` is assigned with **no** class annotation and types the field from the payload via a `strawberry.lazy(...)` forward-ref (Major-3) | CONFORMS | `mutations/inputs.py #"INPUTS_MODULE_PATH: str = \"django_strawberry_framework.mutations.inputs\""`; `mutations/fields.py::_lazy_ref` + `::build_lazy_field_signature` (seam: R1c owns `fields.py`) |
| 41 | Decision 7 `#"The \`.field()\`-classmethod form (graphene-django's \`.Field()\`) is the fallback if Strawberry rejects a resolver-typed field with no class annotation"` | **STALE-DESCRIPTION** | A falsified prediction: Strawberry accepts it, the lazy-ref form shipped, and no `.field()` classmethod exists on the mutation base at `HEAD`. It also still points at `#"([Risks](#risks-and-open-questions))"`, whose body Slice 0 moved to the companion |
| 42 | Decision 14 — a single `data: <Model>Input!` (create) / `data: <Model>PartialInput!` (update) argument, not flattened per-field arguments | CONFORMS | `mutations/fields.py::_mutation_arguments #"arguments.append((\"data\", data_ann))"`; docstring `#"create\`\`: \`\`data: <Model>Input!"` |
| 43 | Decision 14 — plus `id: ID!` for update / delete | CONFORMS | `mutations/fields.py::_mutation_arguments #"arguments.append((\"id\", strawberry.ID))"` gated on `operations.py::operation_takes_id` |
| 44 | Decision 14 — no Relay `clientMutationId` | CONFORMS | zero occurrences of `clientMutationId` anywhere in `django_strawberry_framework/` at `HEAD` (grep of the shortest distinctive token `MutationId` → 0 hits) |
| 45 | Decision 14 — `id:` renders `ID!`, the `node(id: ID!)` server-side-decode contract | CONFORMS | `strawberry.ID` annotation; `mutations/fields.py #"the raw \`\`strawberry.ID\`\` string"` |
| 46 | Decision 14 — the resolver decodes + type-checks `id` against the mutation target, `FieldError` on `id` for a malformed / unresolvable / wrong-model id | CONFORMS | `mutations/resolvers.py #"on \`\`id\`\` - identifies no row"` (seam: R1c owns the resolver) |
| 47 | `## User-facing API` SDL block — `input ItemInput { name: String! description: String categoryId: GlobalID! isPrivate: Boolean }` | **STALE-DESCRIPTION** | `Item` carries a fifth editable column at `HEAD`: `examples/fakeshop/apps/products/models.py::Item #"attachment = models.FileField("` (`null=True, blank=True`), added for the form-mutation multipart surface by **`DONE-038-0.0.12`** and mapped to `Upload` by **`DONE-037-0.0.11`**. The real `ItemInput` therefore also carries `attachment: Upload` (optional) |
| 48 | `## User-facing API` SDL block — `input ItemPartialInput { … }` | **STALE-DESCRIPTION** | same omission; `attachment: Upload` is present and optional (`tests/mutations/test_inputs.py::test_partial_input_file_field_always_optional_upload`) |
| 49 | `## User-facing API` SDL block — `type FieldError { field: String! messages: [String!]! }` | **SUPERSEDED** | `codes: [String!]!` and `path: [String!]!` are on the wire at `HEAD` (row 15). This is the block a consumer copies, so it is the highest-visibility of the four `FieldError` sites |
| 50 | `## User-facing API` SDL block — `type CreateItemPayload { node: ItemType errors: [FieldError!]! }` | CONFORMS | rows 16–18 |
| 51 | `## User-facing API` SDL block — `type Mutation { createItem(data: ItemInput!): CreateItemPayload! updateItem(id: ID!, data: ItemPartialInput!): … deleteItem(id: ID!): … }` | CONFORMS | rows 42–45 |
| 52 | `## User-facing API` — `create_item = DjangoMutationField(CreateItem)` assigned with **no** class-attribute annotation | CONFORMS | row 40 |
| 53 | `## User-facing API` prose — `name` / `categoryId` required, `description` / `isPrivate` optional even in the create input | CONFORMS | rows 3, 23 |
| 54 | `## User-facing API` prose — a relation id is type-checked against its target model **and** resolved through that target's visibility `get_queryset`; a relation id for an unseeable row is a `FieldError` on that relation field | CONFORMS | `utils/write_values.py::decode_visible_relation` (single) and `::decode_visible_relation_ids` (batched `pk__in` through the related primary's `get_queryset`); hidden and missing collapse to the same `relation_field_error` |
| 55 | `## User-facing API` — `input_class` overrides specific generated fields; the generator fills the rest | CONFORMS | rows 19, 29 |
| 56 | `## Error shapes` bullet 1 — a bad mutation `Meta` (no resolvable model / bad `operation` / unknown key / non-`@strawberry.input` `input_class`) raises `ConfigurationError` at mutation-class creation, naming the offending key | CONFORMS | `mutations/sets.py::DjangoMutation._validate_meta`, with the arms in `::reject_unknown_meta_keys` / `::resolve_meta_model` / `::require_non_delete_operation` / `::_validate_input_class` (seam: R1b) |
| 57 | `## Error shapes` bullet 2 — a model with no registered / no **primary** `DjangoType` raises `ConfigurationError` at `finalize_django_types` | CONFORMS | `mutations/sets.py` phase-2.5 bind (seam: R1b) |
| 58 | `## Error shapes` bullet 3 — two **distinct** generated input or payload shapes resolving to one schema-global name raise `ConfigurationError` at finalization naming both; identical shapes dedupe and share one type | CONFORMS | rows 13, 14, 39 |
| 59 | `## Error shapes` bullet 4 — a `full_clean()` `ValidationError` is **not** an exception at the GraphQL boundary; it populates `errors: list[FieldError]` and returns a null object; a multi-field-constraint error keys to `"__all__"` | CONFORMS | rows 35, 36 |
| 60 | `## Error shapes` bullet 4 (tail) — a concurrent-race `IntegrityError` at `save()` maps to the **same envelope** as a documented best-effort fallback | CONFORMS | `utils/errors.py::integrity_error_field_errors`; pinned by `tests/utils/test_errors.py::test_integrity_error_field_errors_shape_and_sentinel`. (Decision 8 step 5's narrower claim that it maps *to the constraint's fields* is a separate, wrong sentence — see `### Notes for Worker 1`, item N4; that site is R1c's) |
| 61 | `## Error shapes` bullet 6 — a `<field>_id` that is a well-formed `GlobalID` for the **wrong** target model is a `FieldError` on that relation field: never coerced to a raw pk and looked up cross-model, never a raw `DoesNotExist` (AR-H4) | CONFORMS | `utils/write_values.py::type_check_relation_id` — the `GlobalID` branch decodes **against `related_model`** and returns `relation_field_error` on any non-`OK` status, before any query |
| 62 | `## Error shapes` bullet 7 — an authorization denial is a top-level `GraphQLError`, **not** a field-keyed envelope entry | CONFORMS | no authorization code path constructs a `FieldError` in `utils/errors.py` or `utils/write_values.py`; the denial raise is `mutations/resolvers.py::authorize_or_raise` (seam: R1c) |
| 63 | Edge cases `#"Partial update with \`UNSET\`-vs-\`null\`"` — an omitted (`UNSET`) field leaves the column unchanged | CONFORMS | `utils/inputs.py::iter_provided_input_fields #"if value is strawberry.UNSET: continue"` — the single-sited omitted-field strip all three write flavors share |
| 64 | Edge cases — explicitly passing `null` sets the column `None` **only if the column is nullable** | CONFORMS | `mutations/resolvers.py::_explicit_null_error #"if django_field.null: return None"` (nullable → the `None` is kept as a provided value) |
| 65 | Edge cases `#"else surfaces a \`full_clean()\` \`FieldError\`"` — an explicit `null` on a non-nullable column is caught by `full_clean()` | **STALE-DESCRIPTION** | The contract (a field-keyed `FieldError` on that field) holds, but not by that mechanism: `HEAD` rejects it **at decode**, before any DB work, with `codes="null"` (`mutations/resolvers.py::_explicit_null_error`). The docstring gives the reason the spec's mechanism could not work: `#"Django's \`\`full_clean\`\` SKIPS a \`\`blank=True\`\` empty value"`, so a `TextField(blank=True)` / `blank=True, null=False` FK would have slipped through to a raw DB `NOT NULL` error. Landed in commit `c09793ee` (2026-06-18, `__version__` still `0.0.10` — i.e. **inside the `0.0.11` cut's own review rounds**), and the spec was never reconciled |
| 66 | Edge cases — the `UNSET` / `None` / value **tri-state is distinguished at decode** | CONFORMS | `iter_provided_input_fields` separates `UNSET` (skipped) from an explicit `None` (yielded as provided); the provided-`None` arm then splits nullable-vs-not per row 64. Its docstring states the rule: `utils/inputs.py::iter_provided_input_fields #"distinct from an explicit \`\`None\`\` which is kept as a provided value"` |
| 67 | Edge cases `#"Two mutations over one model share input types — for the same shape"` — both resolve to the same materialized `ItemInput` / `ItemPartialInput` module globals | CONFORMS | rows 14, 28; pinned by `tests/mutations/test_inputs.py::test_identical_shape_dedupes_via_ledger` |
| 68 | Edge cases — two mutations narrowing to *different* shapes get distinct shape-derived names | CONFORMS | row 12; pinned by `tests/mutations/test_inputs.py::test_type_name_narrowed_shape_is_deterministic_and_distinct` and the four boundary tests `::test_type_name_token_boundaries_do_not_collide` / `::test_type_name_digit_boundary_narrowings_stay_distinct` / `::test_type_name_other_legal_boundaries_do_not_collide` |
| 69 | Edge cases — a name clash between distinct shapes is a finalize-time `ConfigurationError` | CONFORMS | row 13 |
| 70 | Edge cases `#"Many-to-many write (package-internal — no fakeshop M2M)"` — products exposes no M2M model, so M2M earns coverage package-internally | CONFORMS | no `ManyToManyField` in `examples/fakeshop/apps/products/models.py` at `HEAD`; the M2M input pins are local synthetic models in `tests/mutations/test_inputs.py::test_m2m_to_relay_target_becomes_list_of_globalid` / `::test_m2m_to_non_relay_target_becomes_list_of_raw_pk` |
| 71 | DoD item 2 clause — `<Model>Input` generated from `Meta.model`'s editable fields, required only when no usable `default` / `blank` / `null` (Major-1) | CONFORMS | rows 3, 5–7 |
| 72 | DoD item 2 clause — `<Model>PartialInput`, editable fields optional and `UNSET`-defaulted | CONFORMS | row 4 |
| 73 | DoD item 2 clause — narrowed by the mutation's own `Meta.fields` / `Meta.exclude`, **not** the read `DjangoType` selection (Medium-4) | CONFORMS | row 2 |
| 74 | DoD item 2 clause — scalars through the read-side converters, relations to id-shaped fields | CONFORMS | rows 8–10, 25 |
| 75 | DoD item 2 clause — canonical name for the full shape, deterministic shape-derived name when narrowed, `ConfigurationError` on a distinct-shape collision (AR-H1 / AR-M6) | CONFORMS | rows 11–13 |
| 76 | DoD item 2 clause — all materialized as module globals | CONFORMS | row 14 |
| 77 | DoD item 2 clause — the `spec-010` relation-override contract holds and a custom `input_class` follows the generated naming scheme (AR-M2) | CONFORMS | rows 19, 29, 30 |
| 78 | DoD item 2 clause — `#"the public \`FieldError\` (\`field\` + \`messages\`)"` exists | **SUPERSEDED** | row 15. A DoD item is a completion claim, so `docs/builder/BUILD.md` `### \`## Current state\`: observations stand, predictions do not` gives it no vintage licence — it must state the four-field shape |
| 79 | DoD item 2 clause — the `<Name>Payload` (uniform `node` / `result` slot + `errors: list[FieldError]!`, AR-H5) exists | CONFORMS | rows 16–18, 34, 38 |
| 80 | `## Implementation plan` Slice-1 row — files touched: `mutations/inputs.py` (new), `mutations/__init__.py` (new), `__init__.py` (`FieldError` export) | CONFORMS | all three exist at `HEAD`; `django_strawberry_framework/__init__.py #"\"FieldError\","` is in `__all__` |
| 81 | `## Implementation plan` `#"the \`Upload\`-input converter seam Slice 1 leaves for"` — a `FileField` / `ImageField` reaching the generator before 037 ships must fail loudly with `NotImplementedError` | **SUPERSEDED** | 037 shipped; zero `NotImplementedError` remains in the generator (the only two hits in the territory are a *docstring mention* of the retired carve-out and an unrelated `utils/inputs.py` family hook). Attribution: **`DONE-037-0.0.11`** |
| 82 | `## Implementation plan` `#"removed in the change that ships the slice"` — the staged `TODO(spec-036 Slice N)` anchor is removed by the slice that ships it | **SKIPPED** | `tests/mutations/__init__.py #"TODO(spec-036 Slice 1)"` is still present at `HEAD` **and** in the live working tree, for a slice that shipped in `0.0.11`. Proof below |
| 83 | Decision 6 / Decision 4 — the input-name and input-construction mechanics are sited at `mutations/inputs.py` | **RENAMED** | At `HEAD` the load-bearing machinery lives in `utils/inputs.py`, which the spec never names: `::pascalize_token` (promoted from `mutations/inputs.py::_pascalize_token`, kept only as an alias), `::name_set_input_type_name`, `::generated_input_type_name`, `::build_strawberry_input_class`, `::materialize_generated_input_class`, `::make_input_namespace`, `::optional_input_field`, `::iter_input_field_collisions`, `::InputFieldSpec`, and the `SCALAR` / `RELATION_SINGLE` / `RELATION_MULTI` / `FILE` kind constants. `mutations/inputs.py` describes itself as `#"a thin domain wrapper"`. Attribution: **spec-039 P2.2 / P2.3 / Md5** (named in the docstrings) |
| 84 | Decision 7 — the `ValidationError` → envelope mapping and the `"__all__"` keying are part of the `036` write pipeline (spec sites Decision 7 and Decision 8 step 4) | **RENAMED** | At `HEAD` they are `utils/errors.py::validation_error_to_field_errors`, `::field_error`, `::relation_field_error`, `::integrity_error_field_errors`, `::join_error_path` — "promoted from `mutations/resolvers.py`" per that module's own docstring. Attribution: **spec-039 integration** (named in `utils/errors.py::relation_field_error`) |
| 85 | Decision 8 step 1 / Decision 6 — the input-decode primitives (relation type-check, `UNSET` strip, per-kind routing) live in the `036` resolver | **RENAMED** | At `HEAD`: `utils/write_values.py::type_check_relation_id`, `::decode_visible_relation`, `::decode_visible_relation_ids`, `::decode_scalar_leaf`, `::decode_provided_fields`, and `utils/inputs.py::iter_provided_input_fields` — again "promoted from `mutations/resolvers.py`". Attribution: **spec-039** |

### Summary counts (re-derived)

Not asserted — counted off this file after the table was written, one grep per grade, matching only the graded **cell** (`| N | … | GRADE |` / `| **GRADE** |`) so the `### Notes for Worker 1` cross-references and this paragraph cannot inflate a total:

```shell
grep -cE '^\| [0-9]+ \|' <this file>                                            # rows
grep -oE "^\| [0-9]+ \|.*\| (\*\*)?<GRADE>(\*\*)? \|" <this file> | wc -l       # per grade
```

| Metric | Count |
|---|---|
| Rows | 85 |
| CONFORMS | 69 |
| SUPERSEDED | 7 |
| STALE-DESCRIPTION | 5 |
| RENAMED | 3 |
| SKIPPED | 1 |
| **Sum of grades** | **85** |

The sum equals the row count: every row carries exactly one grade. My own pre-count estimate was 68 CONFORMS / 4 STALE-DESCRIPTION and was wrong in two places — recorded because `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` says a count asserted alongside the lesson it illustrates is routinely wrong, and this one was.

Where one contract is stated at several spec sites it is several rows, because R2 authors one edit per site: the `FieldError` shape is rows 15 / 33 / 49 / 78, and the `Item` SDL omission is rows 47 / 48. Rows 56–58 grade `## Error shapes` bullets whose implementation lives in R1b's `mutations/sets.py`; they are graded here so the `## Error shapes` enumeration is complete, and R1b's inventory will grade the same behavior from its own files — R2 should expect the overlap rather than read it as a conflict.

**Distribution, read against the plan's expectation.** The plan's `## Cycle shape` warns that `#"The default expectation for this cycle is therefore SUPERSEDED, not CONFORMS"` and that an all-CONFORMS return on the resolver or permission surface has probably graded the spec against itself. This cohort returns 69/85 CONFORMS, and that is the honest reading rather than a missed audit: the input **generator** is the one part of `036` no later card had reason to move — `038` and `039` built *parallel* input paths (form-derived, serializer-derived) and lifted `036`'s mechanics into `utils/` rather than changing them, which is why this cohort's divergences cluster in three places instead of being spread thin. All 7 SUPERSEDED rows are the two shared surfaces later flavors genuinely had to touch (the `FieldError` envelope, 4 sites; the file/image carve-out, 3 sites), all 3 RENAMED rows are the one `utils/` promotion, and the 5 STALE-DESCRIPTION rows are two model-surface omissions plus three claims that were wrong when written.

### High:

None.

### Medium:

#### The frozen-envelope contract is pinned by zero test rows, which is how `spec-039` widened it unnoticed

Severity: Medium. Source: `django_strawberry_framework/mutations/inputs.py::FieldError`, `tests/mutations/test_inputs.py::test_field_error_envelope_shape` (`tests/mutations/test_inputs.py:1285`).

The spec makes the strongest possible promise about this type — Decision 2 `#"reuse the byte-identical type"`, Decision 7's whole framing, and the preamble's `#"defined and frozen here"`. Nothing in the suite can observe a violation. Read-level proof, no mutation required:

```
grep -rn 'FieldError.__strawberry_definition__' <HEAD>/tests <HEAD>/examples <HEAD>/django_strawberry_framework
  -> exactly 1 hit: tests/mutations/test_inputs.py:1287
grep -ro 'FieldError' <HEAD>/tests <HEAD>/examples | wc -l   ->  161 occurrences
```

The single site is:

```tests/mutations/test_inputs.py:1285:1291
def test_field_error_envelope_shape():
    """``FieldError`` has ``field: str`` (non-null) + ``messages: list[str]`` (non-null list)."""
    definition = FieldError.__strawberry_definition__
    fields = {f.python_name: f for f in definition.fields}
    assert fields["field"].type is str
    assert isinstance(fields["messages"].type, StrawberryList)
    assert fields["messages"].type.of_type is str
```

It builds a name→field **dict** and asserts two entries. No `len(definition.fields)`, no set equality, no sorted-name comparison exists anywhere in the tree. So adding a third, fourth, or tenth field to a type three write flavors and every consumer client share fails **0** rows — the `docs/builder/BUILD.md` `### Acceptance rule: weakly pinned is revision-needed` zero-row case, and not a harness-impossible one: the assertion is trivially writable. That is precisely what happened at commit `951945b7`, and the test's own docstring is now false while the test passes.

This is the **weakly-pinned** case, so per the task's framing the contract row grades SUPERSEDED (row 15 — the widening is real and deliberate) and the pinning gap is raised here as its own finding rather than as a SKIPPED row. The repair is one added assertion, not a narrowed envelope:

```python
assert {f.python_name for f in definition.fields} == {"field", "messages", "codes", "path"}
```

so the next flavor card that wants a fifth field has to change the frozen contract **on purpose**. Owning file is `tests/mutations/test_inputs.py`, which is baseline-dirty with the concurrent session's work (16 diff lines vs `HEAD`) — R3 must re-check it live before writing, per the plan's `### The audit measures HEAD, not the working tree`. Routed to R3; also routed to R2, because Decision 7's freeze sentence has to stop claiming what the code no longer delivers.

#### `tests/mutations/__init__.py` still carries a `TODO(spec-036 Slice 1)` anchor for a slice that shipped in `0.0.11`

Severity: Medium (the SKIPPED row 82). Source: `tests/mutations/__init__.py #"TODO(spec-036 Slice 1)"`.

**Where I looked and what would have to exist.** `AGENTS.md` rule 26 and the spec's own `## Implementation plan` `#"removed in the change that ships the slice"` make anchor removal part of the shipping slice's contract, and `docs/builder/BUILD.md` `## Cross-slice integration pass` step 6 makes the sweep an explicit build obligation. At `HEAD`:

```
grep -rn 'TODO(spec-036' <HEAD>                        -> 5 hits
  tests/mutations/__init__.py:3                 <- Slice 1  (this cohort)
  tests/test_permissions.py:43                  <- Slice 3  (R1c's territory, see N5)
  docs/SPECS/spec-036-...md:502, :545           <- the spec describing the convention
  docs/SPECS/spec-037-...md:488                 <- a sibling spec's prose
grep -c 'TODO(spec-036' tests/mutations/__init__.py    -> 1   (live working tree too)
```

The work the anchor stages — `#"add one test module per mutation source module"` — has fully landed: `tests/mutations/` holds `test_inputs.py`, `test_sets.py`, `test_resolvers.py`, `test_fields.py`, `test_permissions.py`, `test_operations.py`, `test_write_transaction.py`. So this is a stale anchor, not staged work.

**Why the absence of a fix is real rather than a search miss.** No gate greps for it: `grep -rln 'TODO(spec-' scripts/` returns nothing. The obligation exists only as a per-cycle worker action in `BUILD.md`'s integration pass, and the `036` cycle's integration pass is the one that missed it — so nothing has re-checked it in four release lines. There is no "test that would have to exist" in the ordinary sense; the pinning artefact that would have to exist is a repo-wide stale-anchor check, and its absence is the mechanism.

**Repair (R3).** Replace the `TODO(spec-036 Slice 1)` block with non-`TODO` provenance (`spec-036` / `DONE-036-0.0.11`) or delete it, per `BUILD.md` step 6's own prescription. `tests/mutations/__init__.py` is **byte-identical to `HEAD`** and is **not** in the plan's baseline-dirty list, so R3 can repair it without touching the concurrent session's work. The sibling `tests/test_permissions.py:43` anchor is R1c's and is routed, not repaired here.

### Low:

#### `mutations/inputs.py` re-exports `to_camel_case` from Strawberry while the module's own rule is to use `graphql_camel_name`

Severity: Low. Source: `django_strawberry_framework/mutations/inputs.py::_audit_mutation_input_surface #"field.graphql_name or to_camel_case(field.python_name)"` vs `::mutation_input_field_specs #"field.graphql_name or graphql_camel_name(python_name)"`.

Two functions in the same module fall back to two *different* camel-casers for the same purpose — reading a Strawberry field's effective GraphQL name. `utils/inputs.py::build_strawberry_input_class` documents at length why the package's own `graphql_camel_name` must win (`#"the package keeps \`\`field_2\`\` distinct from \`\`field2\`\`, while Strawberry's default converter maps both to \`\`field2\`\`"`). Under the generated path this is harmless — every generated field carries a pinned `name`, so the `or` branch is unreachable — but `_audit_mutation_input_surface` runs over **merged** inputs whose consumer-authored fields may carry no explicit `name`, which is exactly the case where the two casers can disagree. The divergence would make the duplicate-name audit reason about a wire name Strawberry will not actually emit.

Not a spec contract, so no inventory row. Recommend `_audit_mutation_input_surface` use `graphql_camel_name` and drop the `to_camel_case` import, matching its sibling. **Already partly in flight**: the concurrent session's live `mutations/inputs.py` is 69 diff lines from `HEAD` and is consolidating this module's naming and narrowing spine — R3 must re-check live before acting.

#### Two spec sites still describe `## Risks and open questions` as carrying a body

Severity: Low. Source: Decision 7 `#"([Risks](#risks-and-open-questions))"` (row 41) — the anchor now resolves to a four-line pointer section, not the fallback deliberation it names. Bundled into row 41's STALE-DESCRIPTION rather than counted separately.

### DRY findings

Helper run: `scripts/review_inspect.py` was run on all four territory source files, read from the **`HEAD` snapshot** (`--root <snapshot>`), with `--output-dir docs/shadow --stdout`. Running it against the live paths would have described the concurrent session's uncommitted state. Sections read: **Repeated string literals** and **Imports**, per `docs/builder/BUILD.md` `### Reading the overview`. No skips.

**1. `utils/` imports `mutations/` — the shared envelope's home is inverted (existence / ownership challenge, escalated).**

The Imports section makes it visible:

```
utils/errors.py       line 33: from ..mutations.inputs import FieldError            (TYPE_CHECKING)
utils/errors.py       line 57: from ..mutations.inputs import NON_FIELD_ERROR_KEY, FieldError   (function-local)
utils/write_values.py line 42: from ..mutations.inputs import FieldError            (TYPE_CHECKING)
```

`utils/` is the neutral layer three write flavors (`036` model, `038` form, `039` serializer) plus `auth` all consume, and it depends **upward** on one flavor's package for the envelope type. The module says so itself: `utils/errors.py #"utils must not import the mutations package at module import time, so each constructor imports them function-locally"`. A function-local import to dodge a cycle is the symptom; the cause is that `FieldError` and `NON_FIELD_ERROR_KEY` are homed in a flavor module while being flavor-neutral in fact. The natural home is `utils/errors.py` (which already owns every constructor that builds one), with `mutations/inputs.py` re-exporting so the public import path and `__all__` are unchanged.

**This is contract-level and therefore not a worker's call** (`docs/builder/BUILD.md` `### Contract-level findings are escalated as maintainer decisions before dispatch`, `docs/builder/worker-3.md` `### The existence challenge`): the spec *deliberately* homes the type in `mutations/inputs.py` (Decision 7), so moving it is a spec decision, and `FieldError` is a public root export whose module identity a consumer may have pinned. Escalated in `### Notes for Worker 1`, item N6. **Not** held at `revision-needed` — an unresolved existence challenge never blocks a unit.

**2. Repeated `codes=` string literals across the envelope constructors — already closed in flight.**

At `HEAD`, `utils/errors.py` spells the structured error codes as bare literals at six sites (`codes="invalid"` ×3, `codes="null"`, `codes="constraint"`, plus `mutations/resolvers.py`'s own `codes="null"` ×2). These are the client-branching contract `FieldError.codes` exists to provide, so a typo is a silent wire-contract break with no gate. **The concurrent session has already fixed this**: the live `utils/errors.py` introduces `FIELD_ERROR_CODE_INVALID` / `FIELD_ERROR_CODE_NULL` / `FIELD_ERROR_CODE_CONSTRAINT` constants plus `null_field_error()` and `coded_error_extensions()`. Reported as already-closed-in-flight per the plan's `#"if the concurrent session has already closed the gap"` rule; **no repair is dispatched.**

**3. `editable_input_fields`' `fields` / `exclude` narrowing duplicates the shared name-set spine — already closed in flight.**

At `HEAD`, `mutations/inputs.py::editable_input_fields` hand-rolls the freeze / mutual-exclusion / unknown-name walk that `utils/inputs.py::resolve_effective_fields` and `::normalize_field_name_sequence` already own for the other flavors — with a real consequence the `HEAD` docstring only half-covers: because it is a **public** generator the auth and form adapters call directly (bypassing `mutations/sets.py::DjangoMutation._validate_meta`), a bare-string `fields="name"` iterates as characters there. The live tree routes it through `resolve_effective_fields` and states exactly that. Already-closed-in-flight; **no repair dispatched.**

**4. Repeated-literal scan — nothing else actionable.**

```
mutations/inputs.py   : 5x many_to_many, 3x DjangoMutation, 3x "DjangoMutation for", 2x editable,
                        2x is_relation, 2x "input for", 2x __annotations__
utils/inputs.py       : 3x __annotations__, 3x "Generated input", 3x description, 2x ": members",
                        2x "Generated set metadata must be a mapping; got",
                        2x "or drop one via Meta.fields / Meta.exclude."
utils/errors.py       : 2x error_list
utils/write_values.py : None.
```

The `many_to_many` / `is_relation` / `editable` repeats are Django attribute-name probes reached through `getattr`, not constants a name could improve. The two `utils/inputs.py` message fragments are already inside single-sited message builders (`iter_input_field_collisions` yields both arms from one body). No finding.

**5. Cross-cohort duplication review.** Deferred by construction, not skipped: `docs/builder/worker-3.md` `### Cross-cohort duplication review` compares cohorts' **additions**, and R1's four cohorts add nothing — every one is read-only. The cross-flavor convergence they would have looked for is the shared `utils/` layer this audit already read end to end, and finding **1** above is its result. The check that does remain owed is the cross-slice literal comparison at `docs/builder/bld-036-integration.md`, whose input is the shadow overviews this pass regenerated.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. The file is one of the few in the mutation surface the concurrent session has not touched, so its `HEAD` content and its live content are the same bytes. `__all__` and the re-export list are unchanged by this cycle, and this cohort adds no export.

For the record, since `FieldError`'s export is this cohort's contract: `django_strawberry_framework/__init__.py` imports `FieldError` (line 30) and lists `"FieldError"` in `__all__` (line 150), alongside `"DjangoModelPermission"`, `"DjangoMutation"`, and `"DjangoMutationField"` — the four Decision 5 symbols. Pinned by `tests/mutations/test_inputs.py::test_field_error_is_public_export`. The Decision-5 *count* dispute the plan flags (three vs four) is R1d's row, not graded here.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. This cohort writes only its own artifact and its own cycle-scoped memory file, and the maintainer-set scope forbids touching every doc surface this subsection covers.

### What looks solid

- **The required-vs-optional predicate is the spec's rule, not the blanket rule the spec warns against.** `input_field_required` is three lines, reads as the DRF rule, and all three of its sub-conditions are exercised (`has_default` via `is_private`, `blank` via `description`, `null` via the `null=True` file-column tests). The M2M carve-out is at the call site with the reason inline, so the predicate stays honest about not applying to M2M.
- **Generated naming is injective and the injectivity is tested at the boundaries that actually break it.** `pascalize_token` escapes underscores and capitals rather than collapsing them, and four separate tests pin the cases that collide under a naive encoder (`a_b`/`ab`, `field2_x`/`field2x`, `fooBar`/`foobar`, digit boundaries). This is the kind of contract that usually ships with one happy-path test.
- **Every relation decode path is visibility-first, and hidden is indistinguishable from missing on all of them.** `decode_visible_relation` and `decode_visible_relation_ids` both funnel a wrong-model id, an uncoercible pk, a hidden row, and a missing row into one `relation_field_error`. The batched form confirms a whole set in one `pk__in` query, so the no-existence-leak property does not cost an N+1.
- **The empty-input-set guard fails at the framework boundary rather than at `Schema(...)`.** `build_mutation_input` raises a named `ConfigurationError` for a `Meta.fields = ()` narrowing instead of letting Strawberry emit a bare `ValueError: Input Object type … must define one or more fields`. Not a spec contract — an addition — and the right kind of addition.
- **The payload builder carries two shapes without forking.** The model-backed and model-less (`ok: bool`) branches share one builder and one ledger, and the model branch is provably unreached by the `None` arm, so `038`'s addition did not disturb `036`'s payload.

### Temp test verification

No temp tests were created. `docs/builder/temp-tests/036/` is unused by this pass. The one behavioral question that would ordinarily justify a temp test — whether anything pins the `FieldError` field set — was answered by a whole-tree grep showing a single inspection site, which is stronger evidence than a temp test would be and costs no write to the tree.

### Notes for Worker 1 (spec reconciliation)

R2 authors the spec edits from this section, so each item carries the **exact wrong text** and **what it should say**. Rows are cited by inventory number.

**N1 — `FieldError` is not frozen; it has four fields (rows 15, 33, 49, 78). Four spec sites.**

Attribution: **spec-039 / `DONE-039-0.0.13`**, commit `951945b7` (2026-07-01).

- *Slice 1 checklist, sub-bullet 2.* Wrong: `The public \`FieldError\` \`@strawberry.type\` (\`field: str\`, \`messages: list[str]\`)`. Should say: `field: str`, `messages: list[str]`, plus the two additive client-ergonomics lists `codes: list[str]` and `path: list[str]`, both defaulting to `[]`.
- *Decision 7, opening sentence.* Wrong: `a public \`FieldError\` \`@strawberry.type\` (\`field: str\`, \`messages: list[str]\`) — graphene-django's \`ErrorType\` shape`. Should state the four-field shape, note that `field` / `messages` are the graphene-django `ErrorType` parity core and `codes` / `path` are additive so a client can branch without parsing localized text or the dotted `field` string, and record the root rule: a **root** non-field error is `field="__all__"` with an **empty** `path`, while a **nested** non-field error keeps its segments.
- *`## User-facing API` SDL block.* Wrong: `type FieldError { field: String! messages: [String!]! }`. Should be `type FieldError { field: String! messages: [String!]! codes: [String!]! path: [String!]! }`. This block is what a consumer copies, so it matters most.
- *DoD item 2.* Wrong: `the public \`FieldError\` (\`field\` + \`messages\`) … exist`. A DoD item is a completion claim and gets no vintage licence — restate as the four-field shape.
- *The freeze promise itself.* Decision 7's framing and Decision 2's `#"reuse the byte-identical type"` are now false as written. The **contract** that survived is real and worth stating plainly: every flavor returns *the same* `FieldError` class, and it may only grow additive, default-empty fields. Decision 2 is **R1d's** spec territory — flagging the sentence, not editing its row. The corresponding `**Post-ship:**` bullet belongs under Decision 7 in the companion.

**N2 — the file/image `NotImplementedError` carve-out is gone (rows 31, 32, 81). Three spec sites.**

Attribution: **`DONE-037-0.0.11`** (`Upload` scalar + file/image mapping), stated in `mutations/inputs.py::model_column_input_annotation #"spec-037 lifted the spec-036"`.

- *Decision 6, final paragraph.* Wrong, in full: `**File / image columns are the one exception to the merge override (CR-6):** the generator raises \`NotImplementedError\` for a \`FileField\` / \`ImageField\` *before* it consults the override set, so a consumer cannot substitute a custom field for a file column via \`input_class\` in \`0.0.11\` (the \`Upload\` seam is deferred to [\`DONE-037-0.0.11\`][kanban]); a file column is removed from the write surface only via \`Meta.exclude\`.` Should say: a `FileField` / `ImageField` maps to the `Upload` scalar as a `SCALAR`-kind input (so its python attr is the plain field name, never `<name>_id`), and it rides the same override-skip, requiredness, and `| None`-widening tail as any other scalar — there is no carve-out.
- *`## Implementation plan`, staged-anchor paragraph.* Wrong: the parenthetical `(e.g. the \`Upload\`-input converter seam Slice 1 leaves for [\`TODO-ALPHA-037-0.0.11\`][kanban] — a \`FileField\` / \`ImageField\` reaching the generator before 037 ships must fail loudly, not silently emit a wrong type)`. The seam is filled and the loud failure is retired; either drop the example or mark it as the historical `0.0.11`-cut state. Note the same paragraph still spells the card as `TODO-ALPHA-037-0.0.11` while it is `DONE-037-0.0.11` elsewhere in this same spec.
- *`## Non-goals` / `## Out of scope`* both say this card `#"leaves a thin converter seam for 037 to plug \`Upload\` into"`. True as history, falsified as a present-tense description of `HEAD`. `## Out of scope` is **R1d's** territory; the `## Non-goals` bullet is flagged here for whichever cohort R2 assigns it.

**N3 — the `ItemInput` / `ItemPartialInput` SDL blocks omit `attachment` (rows 47, 48).**

`Item` gained `attachment = models.FileField(upload_to="product_media/", null=True, blank=True)` for the form-mutation multipart surface (**`DONE-038-0.0.12`**, per the comment above the column), and 037's mapping turns it into `Upload`. Both SDL blocks need the row: `attachment: Upload` in `ItemInput` (optional — `null=True, blank=True`) and in `ItemPartialInput`. The prose immediately below the block enumerates which fields are required and why; it needs `attachment` in the optional list. The products model surface is **R1d's** territory, so R2 should reconcile the SDL from R1d's inventory too rather than from this row alone.

**N4 — Decision 8 step 5 claims an `IntegrityError` mapping that never existed (routed to R1c).**

Not one of my rows — `utils/errors.py` is my file but Decision 8 is R1c's spec territory — and worth naming because it is a **STALE-DESCRIPTION that was wrong on the day the spec shipped**, not a later divergence.

Wrong text, Decision 8 step 5: `the pipeline maps it to the constraint's fields as a **documented best-effort race fallback** (backend-specific)`. `HEAD` keys it to `"__all__"` with a deliberately non-committal message: `utils/errors.py::integrity_error_field_errors #"A database constraint was violated."`, whose docstring says the catch is broad so the message `#"is the honest superset"` rather than over-claiming uniqueness. And the original `036` implementation did the same — `git show 4b26b94e:django_strawberry_framework/mutations/resolvers.py` (the commit whose message is `Finish docs/spec-036-mutations-0_0_11.md`) contains `_integrity_error_field_errors` with `del model, provided_attrs  # reserved for a future per-constraint refinement.` and a docstring stating it keys the sentinel. So the spec sentence has never described the code. It should say: keyed to the `"__all__"` sentinel, because `save()`'s `IntegrityError` carries no reliable cross-backend field mapping. My `## Error shapes` row 60 (`maps to the same envelope`) is CONFORMS and needs no edit.

**N5 — a second live `TODO(spec-036 Slice 3)` anchor, in R1c's territory.**

`tests/test_permissions.py:43` carries `# TODO(spec-036 Slice 3): add the package-level permission pin for mutation update/delete lookups.` with a four-line Pseudocode block, at `HEAD` and live. Decision 4 assigns exactly that pin to that file (`#"[\`tests/test_permissions.py\`][permissions] for the lookup-scoping pin"`). Whether the pin landed elsewhere (`tests/mutations/test_permissions.py` exists) or genuinely never landed is **R1c's** determination — the anchor alone does not settle it, and I did not audit `tests/mutations/test_permissions.py`. Routing so it is not lost between cohorts: if R1c finds the pin present, the anchor is a stale-comment repair like row 82's; if absent, it is a second SKIPPED contract. `tests/test_permissions.py` is **not** in the plan's baseline-dirty list.

**N6 — Escalated (maintainer decision): should `FieldError` / `NON_FIELD_ERROR_KEY` live in `mutations/inputs.py` at all?**

`docs/builder/worker-3.md` `### The existence challenge`, escalated per its own routing rule. Evidence is DRY finding 1: the flavor-neutral `utils/` layer depends upward on one flavor's package for the envelope type, and pays for it with two function-local imports whose stated purpose is dodging an import cycle. Three write flavors plus `auth` consume the type; only `mutations/` owns it.

Resolution paths, for the maintainer:

1. **Leave it.** Decision 7 homes it there deliberately; the function-local imports work; `FieldError` is a public root export and its module identity may be pinned by a consumer's `from django_strawberry_framework.mutations.inputs import FieldError`. Cost: the upward dependency stays, and every future write flavor inherits the function-local-import idiom.
2. **Move the definition to `utils/errors.py`** (which already owns every constructor that builds one) and re-export from `mutations/inputs.py`, keeping both import paths and `__all__` byte-identical. Cost: one spec Decision-7 edit, a `docs/GLOSSARY.md` home change (**out of this cycle's scope**), and a `path::QualifiedName` sweep across the specs that cite `mutations/inputs.py::FieldError`.
3. **Move it to a new neutral module** (e.g. `django_strawberry_framework/errors.py`) so neither `utils/` nor a flavor owns the public type. Highest churn; cleanest layering.

I did **not** act on any of these, and this cohort is not held at `revision-needed` over it.

**N7 — the RENAMED cluster: three whole mechanism families the spec sites in modules that no longer hold them (rows 83, 84, 85).**

These are the rows most likely to mislead a future reader of `spec-036`, because the spec reads as a complete account of `mutations/inputs.py` and `mutations/resolvers.py`. Attribution throughout: **spec-039** (`P2.2` / `P2.3` / `Md5` / "spec-039 integration", each named in the moved code's own docstrings).

- **Input construction and naming → `utils/inputs.py`.** Decisions 4 and 6 site this at `mutations/inputs.py`; at `HEAD` `pascalize_token`, `name_set_input_type_name`, `generated_input_type_name`, `build_strawberry_input_class`, `materialize_generated_input_class`, `make_input_namespace`, `optional_input_field`, `iter_input_field_collisions`, `InputFieldSpec`, and the four decode-kind constants live in `utils/inputs.py`. `mutations/inputs.py` calls itself `#"a thin domain wrapper"`. Recommend Decision 4's module bullet name `utils/inputs.py` as the shared mechanics owner and say what stays domain-local (the editable-column selector, the required rule, the relation naming scheme, the payload builder, `FieldError`).
- **Envelope construction → `utils/errors.py`.** `field_error`, `relation_field_error`, `validation_error_to_field_errors`, `integrity_error_field_errors`, `join_error_path` — "promoted from `mutations/resolvers.py`" per that module's docstring. Decision 7 should name the constructor owner.
- **Input decode → `utils/write_values.py`.** `type_check_relation_id`, `decode_visible_relation`, `decode_visible_relation_ids`, `decode_scalar_leaf`, `decode_provided_fields` (+ `utils/inputs.py::iter_provided_input_fields`). Decision 8 step 1 is **R1c's** site; flagged so the two cohorts' RENAMED rows reconcile to one spec edit rather than two conflicting ones.

**N8 — Slice 1's coverage bullet names the wrong file for AR-M2 (row 21).**

Wrong text, Slice 1 sub-bullet 4: `consumer \`input_class\` following the generated scheme (AR-M2)` listed among `tests/mutations/test_inputs.py` coverage. The pins are `tests/mutations/test_sets.py::test_meta_input_class_diverging_field_names_raises` / `::test_meta_input_class_following_scheme_validates_clean` / `::test_meta_input_class_not_strawberry_input_raises`, and Slice 2's coverage bullet already claims them correctly. Fix: drop the clause from Slice 1's bullet (Slice 2 keeps it), or re-point it at `test_sets.py`. Cheap, and it is the kind of false coverage claim that sends the next reader to an empty file.

**N9 — a falsified prediction in Decision 7 (row 41).**

Wrong text: `The \`.field()\`-classmethod form (graphene-django's \`.Field()\`) is the fallback if Strawberry rejects a resolver-typed field with no class annotation ([Risks](#risks-and-open-questions)).` Strawberry accepted it; the `strawberry.lazy` forward-ref form shipped; no `.field()` classmethod exists on the mutation base at `HEAD`. Per `docs/builder/BUILD.md` `### \`## Current state\`: observations stand, predictions do not`, a falsified prediction is rewritten rather than dated — delete the sentence and let the companion carry the contingency under Decision 7's `### Changes this Decision underwent`. The trailing `[Risks](#risks-and-open-questions)` link should go with it: Slice 0 moved that section's body to the companion, so the anchor now lands on a pointer.

**N10 — AR-M2 is narrower than what `HEAD` enforces: relation overrides are also type-locked (routed to R1b).**

Decision 6's AR-M2 paragraph constrains a custom `input_class` on one axis only — `#"a custom input must use the **same field-naming scheme the generator emits**"` — and spells out the three naming rules. `HEAD` enforces a **second** axis the spec does not mention: `mutations/sets.py::_validate_relation_override_types` type-locks a relation override's annotation, so a consumer cannot re-declare `category_id` as a raw pk when the generated shape says `GlobalID` (or the reverse). Landed in commit `70d60d4a`, `Type-lock relation overrides in mutation input_class to GlobalID`.

This is an **addition**, not a divergence — my rows 19, 29, and 30 all still CONFORM, because a naming-conformant override is still honored and a scheme-diverging one is still rejected. Two reasons it is worth a spec sentence anyway:

- Decision 6's AR-M2 paragraph reads as the complete statement of what a custom input must satisfy, and it is now incomplete: a consumer following it to the letter can still hit a `ConfigurationError`. The override must keep both the generated `relay.GlobalID` **core type** and its **container shape** (scalar for FK / OneToOne, one-level `list` for M2M).
- The validator is a **security boundary**, not polish, and it protects a guarantee the spec *does* make. Its docstring enumerates what a name-only check let through: `#"\`\`category_id: int\`\` (raw pk core) - the value is seen as a non-\`\`GlobalID\`\` raw pk and passed through, bypassing both the type-check and the visibility contract (attach-by-raw-pk to an unseeable row)"`. That is exactly the `## User-facing API` promise my row 54 grades CONFORMS — `#"a permitted writer can never attach a row they could not see"` — so at `HEAD` that promise rests partly on a validator the spec never names.

`mutations/sets.py` is **R1b's** file, so R1b should grade the validator itself, and the validator's own docstring attributes it to `#"spec-036 Decision 10"` (R1c's territory) while the sentence that needs widening is Decision 6's AR-M2 paragraph (mine). R2 should reconcile all three inputs into one edit rather than three, and decide which Decision owns the shape lock.

**N11 — the rationale companion itself carries a sentence the envelope widening falsified.**

The companion is hours old, so this is Slice 0's text rather than inherited drift, and it is the one place a reader would go to check whether the freeze ever moved. `docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md`, Decision 2, `### Changes this Decision underwent`, first bullet, ends: `#"and froze the \`FieldError\` envelope here for the downstream flavors. Nothing later reopened it."`

`spec-039` reopened it (item N1). The correct shape is a `**Post-ship:**` bullet under Decision 2 **and** Decision 7 recording that `0.0.13` added `codes` and `path` as additive default-empty fields, plus striking `Nothing later reopened it` — a sentence that will otherwise keep certifying the opposite of the record it sits in. Decision 2 is R1d's spec territory but the companion is Worker 1's to edit either way, so it is routed here rather than split.

**N12 — the R1a↔R1c seams, stated so neither cohort assumes the other covered them.**

Rows where the *contract* is mine and the *implementation* is R1c's, graded on the envelope/decode side only: 35 (resolver short-circuit to a null-object payload), 40 (`DjangoMutationField`'s lazy payload ref), 46 (`id` decode + type-check), 62 (the authorization denial is a top-level `GraphQLError`), 63–66 (the `full_clean(exclude=...)` half of the `UNSET` tri-state). Rows 56–58 are the mirror case with R1b (`mutations/sets.py`) and are excluded from my grade total for that reason. The `"__all__"` sentinel splits cleanly: I graded the **constructor** (rows 36, 37); R1c owns the resolver that populates it.

### Review outcome

`review-accepted`.

`docs/builder/worker-3.md` `### Acceptance gate`, applied to a read-only audit cohort: there is no diff to reject, and the two findings this pass raises are both **inventory output routed onward** rather than defects in work under review — the SKIPPED anchor (row 82) routes to R3 as this cycle's code repair, and the weak `FieldError` pinning routes to R3 for the assertion and to R2 for the spec sentence. Neither is a Worker 2 revision, and holding the cohort at `revision-needed` would stall R2's spec reconciliation behind work R2 does not own.

Escalated to Worker 1 at Medium-or-higher: **N6** (the `FieldError` home — contract-level, maintainer's call, never a worker's) and the **N1** freeze sentence, whose resolution needs the spec context Worker 1 owns. Both carry their resolution paths above.

Per the plan's `#"A SKIPPED grade is checked against the live working tree before it becomes work"`, I confirmed row 82 against the live tree myself: `grep -c 'TODO(spec-036' tests/mutations/__init__.py` → `1`, and the file is byte-identical to `HEAD`. The concurrent session has **not** closed it, so it is real work for R3.

---

## Final verification (Worker 1)

Performed in the R2 pass, `docs/builder/bld-036-review-2-spec_reconciliation.md`, which combines spec
reconciliation with this cohort's final verification — the same combined role the precedent cycle's R2
performed. The audit's own contract is `docs/builder/build-036-mutations-0_0_11.md` `## Conformance
grading vocabulary`; there is no `### Spec slice checklist (verbatim)` and no diff to audit, because
every R1 cohort is read-only over source and tests.

**Counts re-derived, not accepted.** Each cohort's grade tally was recomputed by parsing this file's
own inventory table row by row (row-id pattern per cohort, grade cell normalized), off the rendered
table rather than from the summary paragraph:

```
rows=85  CONFORMS=69  SUPERSEDED=7  STALE-DESCRIPTION=5  RENAMED=3  SKIPPED=1
```

Matches this file's stated table exactly, and 69+7+5+3+1 = 85 = the row count.

**Grades spot-checked against source, and one attribution confirmed correct against a sibling cohort's
contradiction.** Row 15's `codes` / `path` attribution — `951945b7`, `spec-039` / `DONE-039-0.0.13` —
was re-derived independently: `git log -S'codes: list[str] = strawberry.field'` returns exactly that
commit, `git show 951945b7:django_strawberry_framework/__init__.py` reads `__version__ = "0.0.12"`, and
`git show 951945b7 --stat` carries `docs/spec-039-serializer_mutations-0_0_13.md`. **R1a is right and
R1d's evidence cell for the same commit is wrong** (it attributes the widening to the `0.0.14` write
hardening). Row 65's day-one framing was likewise confirmed: the spec's `full_clean()` mechanism was
never true, and `c09793ee` — inside the `0.0.11` cut — then made a different thing true. Both are
recorded in the companion with both framings, because a `**Post-ship:**` bullet alone would have
preserved the false premise.

**N4 was correct and load-bearing.** `git show 4b26b94e:django_strawberry_framework/mutations/resolvers.py`
confirms `_integrity_error_field_errors` keyed the `"__all__"` sentinel and carried
`del model, provided_attrs` in this card's own shipping commit, so Decision 8 step 5's
constraint-fields claim never described the code. Recorded as wrong-when-written, not post-ship.

**N10 was taken** — Decision 6's AR-M2 paragraph now states the relation-override **type** lock as
well as the name lock, because this cohort's own row 54 grades the no-attach-what-you-cannot-see
promise CONFORMS and at `HEAD` that promise rests partly on that validator.

**N6 stays escalated, unacted** (the `FieldError` home is contract-level, three resolution paths
recorded). Holding this cohort at `revision-needed` over an unresolved existence challenge would be
wrong twice over: the cohort produced no diff, and the escalation is not a worker's to close.

**The SKIPPED row (82) is real and routes to R3**, live-tree re-checked by this cohort itself. All 15
routable rows are discharged in the spec.


**Method audited and accepted.** Every grade cites the read-only `HEAD` snapshot at
`7426e7e7d8aa447e89fee75088447d6a506dec12` or a `git show HEAD:<path>` read; no `git stash` /
`git checkout` / `git restore` / `git worktree` appears anywhere in the pass; the decision to decline a
failability mutation on baseline-dirty territory files is recorded with its reason rather than skipped
silently, and is the right call under `AGENTS.md` rule 34 — a `cp`-and-restore round trip spanning a
pytest run would have reverted any concurrent write landing inside the window.

**Every routable row reached R2 on disk** under `### Notes for Worker 1 (spec reconciliation)`, with the
pre-fix spec text and a recommended replacement — which is the obligation
`docs/builder/BUILD.md` `### Cohorting, naming, and closure` records two prior builders as having
missed. Nothing had to be re-derived from a return report.

Final status: `final-accepted`.

