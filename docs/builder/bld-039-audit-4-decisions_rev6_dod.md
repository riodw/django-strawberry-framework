# Build: Slice 1d — cross-cutting contracts audit (Decisions 1/2/3/4/12/14, the 17 `rev6` items, Slice 0 + Slice 4, User-facing API, Edge cases, Test plan, DoD 1/6/7/8, Non-goals, Out of scope)

Spec reference: `docs/SPECS/spec-039-serializer_mutations-0_0_13.md`
Status: review-accepted

---

## Combined audit (Worker 3)

This pass has no `built` predecessor: `spec-039` shipped, and this is a **read-only**
residual audit of what landed against what the spec still says. No source, no test, and no
spec file was mutated. The failability-proof source carve-out was **not** exercised.

### Grading base and how `HEAD` was obtained

`git status --short` at pass start reported these tracked files dirty (concurrent
maintainer session, `AGENTS.md` rule 34): `KANBAN.html`, `KANBAN.md`,
`django_strawberry_framework/_strawberry_patches.py`, `apps.py`, `conf.py`, `list_field.py`,
`orders/sets.py`, `resource_policy.py`, `utils/querysets.py`, `docs/GLOSSARY.md`,
`docs/SPECS/spec-039-serializer_mutations-0_0_13.md`, `docs/TREE.md`, `docs/feedback.md`,
`docs/spec-050-*`, `examples/fakeshop/db.sqlite3`, and seven `tests/` files.

Of the files this audit grades against, exactly **two** were dirty:
`django_strawberry_framework/utils/querysets.py` and
`django_strawberry_framework/conf.py`. Both were obtained read-only into a scratch path
**outside** the repo and graded there:

```shell
git show HEAD:django_strawberry_framework/utils/querysets.py > <scratch>/utils-querysets-HEAD.py
git show HEAD:django_strawberry_framework/conf.py            > <scratch>/conf-HEAD.py
```

`git stash` / `git checkout` / `git restore` / `git worktree` were **not** used.

The whole `django_strawberry_framework/rest_framework/` subpackage, `__init__.py`,
`mutations/`, `forms/`, `types/base.py`, `pyproject.toml`, `uv.lock`, `pytest.ini`, the
whole `tests/rest_framework/` tree, and `examples/fakeshop/test_query/test_products_api.py`
were **clean at `HEAD`**, so the working tree is `HEAD` for them.

**The spec file itself is dirty** — this cycle's own Slice 0 rationale extraction. Headings
were diffed HEAD-vs-worktree and are **identical** (`diff` of the `^#` line sets is empty;
4354 → 3725 lines, prose only). The audit population is therefore the same either way; the
post-extraction text is quoted, since that is the contract Worker 1 will reconcile.

### Population, measured before grading

Every count below was measured as it was written (`docs/builder/BUILD.md`
`## Claims are proven mechanically, never accepted on prose`).

| Population | Size | How measured |
|---|---|---|
| `### rev6 #N` subsections | **17** | `rg -c '^### rev6 #'` → 17; numbers `1..17` each present exactly once |
| Decisions in this cohort (1, 2, 3, 4, 12, 14) | **6** | of `rg -c '^### Decision '` → 14 total; 5–11 + 13 are sibling cohorts' |
| `## Slice checklist` → Slice 0 boxes | **4** | 1 top-level + 3 nested `- [ ]` in spec lines 489–516 |
| `## Slice checklist` → Slice 4 boxes | **4** | 1 top-level + 3 nested `- [ ]` in spec lines 934–958 |
| `## User-facing API` (prose + SDL contract) | **1** | one section, graded as one contract row |
| `### Error shapes` bullets | **6** | `rg -c '^- '` over lines 1321–1353 |
| `## Edge cases and constraints` rows | **24** | `rg -c '^- \*\*'` over lines 2628–2799 |
| `## Test plan` bullets | **9** | 3 top-level + 6 sub-bullets |
| `## Definition of done` items in this cohort (1, 6, 7, 8) | **4** | of 8 total; 2–5 are sibling cohorts' |
| `## Non-goals` bullets | **7** | `rg -c '^- \*\*'` over lines 1114–1148 |
| `## Out of scope (explicitly tracked elsewhere)` bullets | **8** | `rg -c '^- \*\*'` over lines 3057–3083 |
| `## Current state` bullets | **7** | `rg -c '^- \*\*'` over lines 1013–1069 |
| `## Goals` numbered items | **8** | `rg -c '^[0-9]+\. '` over lines 1071–1112 |

**Total graded rows: 105.**

### Grade counts

Summed from the per-section tables below, one grade per row, and cross-footed against the
105-row population:

| Grade | Count | Which rows |
|---|---|---|
| BUILT-CONFORMANT | **90** | rev6 14 · Decisions 2 · Slice 0 4 · Slice 4 4 · API 1 · Error shapes 6 · Edge cases 23 · Test plan 8 · DoD 3 · Non-goals 5 · Out of scope 6 · Current state 7 · Goals 7 |
| SPEC-STALE | **10** | rev6 #2 · Decisions 1, 2, 4, 12 · Test plan (DRF-absent bullet) · DoD 1 · Non-goals ×2 · Goal 3 |
| SUPERSEDED | **5** | rev6 #14, rev6 #12 · Edge case 11 (`TestClient`) · Out of scope ×2 (`TestClient`, the `0.0.13` bump) |
| DEVIATED | **0** | — |
| DROPPED | **0** | — |

`90 + 10 + 5 = 105`. `OUT-OF-FENCE` is an annotation rather than a grade and is appended to
Slice 4's 4 rows, which are counted once, as BUILT-CONFORMANT.

**No row in this cohort graded DROPPED.** Every contract it owns is implemented at `HEAD`.
The findings are spec-text drift: the package moved three releases past `0.0.13`, five
contracts were superseded by later cards without the spec being re-pointed, and the spec
contradicts itself on one frozen-envelope promise.

---

### The 17 `rev6` items

| # | Title (spec) | Grade | Evidence at `HEAD` |
|---|---|---|---|
| 11 | Public serializer-field converter registry | BUILT-CONFORMANT | `rest_framework/serializer_converter.py::_SERIALIZER_FIELD_CONVERTERS` seeded from `::_BUILTIN_SCALAR_CONVERTERS`; `::register_serializer_field_converter` carries `*, override: bool = False` and raises on re-registration without it; `utils/converters.py::convert_with_mro` walks it; `SerializerFieldConversion` + `register_serializer_field_converter` both in `__init__.py::_DRF_SOFT_EXPORTS` and absent from `__all__` |
| 7 | Expanded DRF scalar capability matrix (no catch-all) | BUILT-CONFORMANT | `_BUILTIN_SCALAR_CONVERTERS` holds explicit rows `serializers.DictField → strawberry.scalars.JSON`, `IPAddressField → str`, `FilePathField → str`, `DurationField → str`, `ModelField → _model_field_converter`; `serializer_converter.py::_model_field_converter` routes the wrapped `model_field` through the read-side walk and raises with no wrapped field. No base-`Field` row exists |
| 6 | Generated enums for serializer-only `ChoiceField` | BUILT-CONFORMANT | `serializer_converter.py::_serializer_choice_annotation` calls the shared `types/converters.py::build_enum_from_choices`; enum name `f"{type_name}{pascal_case(field.field_name)}Enum"`; `serializers.FilePathField` explicitly excluded (its own `str` registry row) |
| 8 | Model-backed serializer type-override conflict policy | BUILT-CONFORMANT | `serializer_converter.py::_model_backed_scalar_annotation` #"disagrees with the backing model" raises naming field, `source`, and both scalars; the consumer-declared `ChoiceField` (rev2 P2) branch runs first |
| 9 | Thread DRF field metadata into the SDL | BUILT-CONFORMANT | `serializer_converter.py::serializer_field_description` returns `str | None` from `help_text` + the `min_length`/`max_length`/`min_value`/`max_value`/`allow_blank`/`allow_empty` summary; threaded by `_walk_serializer_fields` |
| 5 | Aggregate schema-time diagnostics | BUILT-CONFORMANT | `rest_framework/inputs.py` #"schema-time problem(s):" builds ONE `ConfigurationError` from the collected messages; the single-problem verbatim path is preserved; `_collect_input_attr_collision_messages` is the message collector (the spec's named `_guard_serializer_input_attr_collisions` is correctly gone — 0 occurrences package-wide) |
| 1 | Runtime schema/runtime serializer agreement guard | BUILT-CONFORMANT | `rest_framework/resolvers.py::_assert_schema_runtime_agreement` defined and called from the write step before `is_valid()`; per-field body `::_assert_field_agreement`, relation `::_assert_relation_agreement`, nested `::_assert_nested_agreement` |
| 16 | Golden SDL coverage for representative serializer inputs | BUILT-CONFORMANT | `examples/fakeshop/test_query/test_library_api.py::test_n_sdl_library_schema_hook_serializer_input` and `::test_n_sdl_products_serializer_input`, introspecting the one aggregate `/graphql/` schema. See the placement note below |
| 15 | Schema-shape debug/introspection registry | BUILT-CONFORMANT | `rest_framework/inputs.py::_SERIALIZER_SHAPE_REGISTRY` written at the build site and cleared by `::clear_serializer_input_namespace`; `::describe_serializer_input` is a `_DRF_SOFT_EXPORTS` entry |
| **14** | **Optional row locking for update mutations (`Meta.select_for_update`)** | **SUPERSEDED** | **See High-1.** `mutations/sets.py::validate_select_for_update` #"select_for_update = getattr(meta, \"select_for_update\", True)" — the default is **`True`**, not `False`; `mutations/resolvers.py::locate_instance` signature is `select_for_update: bool = True`; `mutations/sets.py::model_backed_permission_and_lock` applies it to the **model and form flavors too**. Code comments attribute the change to "the 0.0.14 concurrency hardening" |
| **12** | **`get_serializer_save_kwargs`** | **SUPERSEDED** | **See High-2.** Shipped signature is `(self, info, *, data, hook_context)`, not the spec's `(info, data, instance=None)`; a **second** guard `resolvers.py::_assert_save_kwargs_not_model_fields` now refuses **any** save kwarg naming a model field, which rejects the spec's own canonical example `owner=request.user` and its own live-test claim |
| 3 | Visibility-scoped + query-efficient relation validation | BUILT-CONFORMANT | `utils/querysets.py::visible_related_objects` (graded at `HEAD` from the scratch copy) is the batched `pk__in` confirm; `resolvers.py::_type_check_relation_id` is the no-DB pre-check; `resolvers.py::_scope_relation_querysets_to_visibility` composes rather than replaces and is called before `is_valid()` |
| 2 | Explicit injection contract (`Meta.injected_fields`) | SPEC-STALE | Behavior all present: `sets.py` normalizes + validates `Meta.injected_fields` against the writable basis and stashes `_injected_field_specs`; `resolvers.py::_injected_serializer_data` enforces the exact-key match. **But `_assert_injected_field_agreement` does not exist** — 0 occurrences package-wide; runtime acceptance is proven inside `_assert_schema_runtime_agreement`, which walks the unified `resolvers.py::_write_surface_specs` list (GraphQL input + injected specs). See Medium-1 |
| 10 | Fingerprint `get_serializer_for_schema()` for determinism | BUILT-CONFORMANT | `rest_framework/inputs.py::serializer_schema_fingerprint`; `rest_framework/sets.py::_checked_schema_field_map` is the one guarded path both `build_input` and `input_type_name` read; `_ValidatedMutationMeta.schema_fingerprint` captured at class validation |
| 4 | Preserve DRF `ErrorDetail.code` in the error envelope | BUILT-CONFORMANT (and a Non-goals breach — see High-3) | `mutations/inputs.py::FieldError` #"codes: list[str] = strawberry.field(default_factory=list)"; `resolvers.py::_error_detail_codes` feeds it |
| 13 | Structured error `path` in addition to the dotted `field` | BUILT-CONFORMANT (same breach) | `mutations/inputs.py::FieldError` #"path: list[str] = strawberry.field(default_factory=list)"; derived inside the shared `field_error` leaf ctor; the `__all__`-sentinel/empty-path root rule is documented on the type |
| 17 | Explicit opt-in nested serializer input support | BUILT-CONFORMANT | `rest_framework/inputs.py::NestedSerializerConfig` (frozen dataclass, a `_DRF_SOFT_EXPORTS` entry); `_NESTED_MAX_DEPTH = 5` with the depth raise; `serializer_converter.py::_reject_nested_serializer` is the un-opted fail-loud; `sets.py` #"the serializer MUST override the write method" enforces the create/update override at class creation; live-earned by `createBranchWithNestedShelves` in `test_library_api.py`. One undocumented refinement — see Low-1 |

**rev6 #17 was flagged in dispatch as the likeliest surprise. It is not one: it shipped in
full, including the two review follow-ons the spec text already folds in.** The surprise is
**#14**, which shipped and was then **inverted** by a later card.

---

### Decisions 1, 2, 3, 4, 12, 14

| Decision | Grade | Evidence |
|---|---|---|
| **1** — Spec filename and canonical naming | SPEC-STALE | The spec is at `docs/SPECS/spec-039-serializer_mutations-0_0_13.md`; `ls docs/spec-039*` returns no match. Decision 1's "lives at **`docs/spec-039-…md`**, at the `docs/` top level" and "the Step 8 archive sweep **leaves it there** (it is the only / active spec at `docs/` top-level)" are both false — a later spec's Step 8 sweep archived it, exactly as `AGENTS.md` prescribes. Companions are at `docs/SPECS/appx/` |
| **2** — Card-scope boundary; frozen `036` contracts reused unchanged | SPEC-STALE (partly self-contradictory) | Ships-what-it-said: ✓ (`SerializerMutation`, converter, pipeline, products live surface all present). Auth stays out: ✓ (card 040, `fa704722`). `DjangoMutationField` unedited: ✓ (`git log 60dbf469~15..60dbf469 -- django_strawberry_framework/mutations/fields.py` is **empty**). **But "This card adds **no** field to `FieldError`" is false** — rev6 #4/#13 in this same spec add `codes` and `path`. See High-3 |
| **3** — `class Meta` surface, not graphene's `MutationOptions` | BUILT-CONFORMANT | `rest_framework/sets.py::_ALLOWED_SERIALIZER_META_KEYS` = `MODEL_BACKED_WRITE_META_KEYS | {"serializer_class", "optional_fields", "injected_fields", "nested_fields"}`, validated through `mutations/sets.py::reject_unknown_meta_keys`. `rg -c 'model_operations|lookup_field'` over the package → **0**: no graphene options flow, no `ClientIDMutation` lineage |
| **4** — Module and test locations | BUILT-CONFORMANT with two stale symbol/path names (SPEC-STALE on the "Shared-helper homes" paragraph) | Source: `rest_framework/{serializer_converter,inputs,sets,resolvers}.py` all present (plus two net-new modules `__init__.py` guard + `hook_context.py`). Tests: `tests/rest_framework/{test_converter,test_inputs,test_sets,test_resolvers}.py` all present (plus `test_soft_dependency.py`); live extends `test_products_api.py` ✓. Helper homes: `utils/converters.py::convert_with_mro` ✓ (P1.4), `mutations/sets.py::reject_unknown_meta_keys` ✓ (P2.7), `mutations/sets.py::clear_mutation_shape_build_cache` ✓ (P1.3), `mutations/resolvers.py::run_write_pipeline_sync` ✓ (P1.5), `register_subsystem_clear` seam ✓ (P1.6). **Two names are wrong:** the promoted relation-decode core is `utils/querysets.py::visible_related_object` (public, no leading underscore; `types/resolvers.py::_visible_related_object` is a *different*, read-side helper), and the non-delete ops constant landed in a net-new `mutations/operations.py::NON_DELETE_OPERATION_INPUT_KIND` / `::NON_DELETE_WRITE_OPERATIONS`, not in `mutations/sets.py` or the hypothesised `mutations/bind_helpers.py` (which does not exist). See Medium-2 |
| **12** — Soft `djangorestframework` dependency and the 100%-coverage strategy | SPEC-STALE on item 3 only; the rest BUILT-CONFORMANT | The four-row import table holds exactly (see the Public-surface check). One shared `rest_framework/__init__.py::require_drf` owns the hint and delegates to `utils/imports.py::require_optional_module`; no memoization in `__init__.py::__getattr__` (no `globals()[…] = …`), pinned by `tests/rest_framework/test_soft_dependency.py::test_successful_lookup_does_not_memoize`. **Item 3's simulation mechanism is wrong** — see High-4 |
| **14** — Version bumps owned by the joint `0.0.13` cut | BUILT-CONFORMANT | At `60dbf469` ("Finish spec-039"): `git show 60dbf469:django_strawberry_framework/__init__.py` → `__version__ = "0.0.12"`, and `git show 60dbf469:uv.lock` → `name = "django-strawberry-framework"` / `version = "0.0.12"`. The `0.0.12 → 0.0.13` bump landed in `fa704722` ("Finish spec-040"), the sibling joint-cut card. `uv.lock` DRF entries **did** change in the gate. Today's `__version__ = "0.0.15"` is a later release and says nothing about this claim |

---

### `## Slice checklist` → Slice 0 (the DRF floor gate) — 4 boxes

| Box | Grade | Evidence |
|---|---|---|
| Slice 0 (pre-Slice-1 dependency gate) | BUILT-CONFORMANT | The gate landed before Slice 1 code: `uv.lock` carries the DRF entries and `[dependency-groups].dev` carries the pin |
| Verify the floor + record the exact pinned floor | BUILT-CONFORMANT | The recorded floor is `djangorestframework>=3.17.0`, stated in Decision 12 and reproduced in the guard |
| The floor check is an explicit acceptance artifact; three places must agree | BUILT-CONFORMANT | **All three read `>=3.17.0`** — see the three-place table below |
| Wire the dev dependency (`[dependency-groups].dev` + `uv lock` + any `ignore::`) | BUILT-CONFORMANT | `pyproject.toml` line 55 `"djangorestframework>=3.17.0"` under `[dependency-groups]`; **absent** from `[project].dependencies`; `uv.lock` carries `{ name = "djangorestframework", specifier = ">=3.17.0" }` and resolves to `3.18.0`; `pytest.ini` carries **no** `ignore::` line — conformant, since the spec says "add **any** targeted DRF-origin `ignore::` line … the verified release **still needs**", and Decision 12 records "with **no** `ignore::` line needed" |

#### The three-place DRF floor check (all three read, none assumed)

| Place | Value read | Source |
|---|---|---|
| 1. `[dependency-groups].dev` pin | `djangorestframework>=3.17.0` | `pyproject.toml` #"djangorestframework>=3.17.0" |
| 2. `require_drf()` install hint | `djangorestframework>=3.17.0` | `rest_framework/__init__.py::_DRF_INSTALL_HINT` #"pip install 'djangorestframework>=3.17.0'" |
| 3. The spec's own statement | `djangorestframework>=3.17.0` | spec `### Decision 12` #"The verified floor is `djangorestframework>=3.17.0`" |

**They agree.** One caveat: `rest_framework/__init__.py`'s module docstring says "place 3 is
the spec **Risks** note", but the spec's own Slice 0 checklist and Decision 12 both name
**Decision 12** as place 3, and the Risks section moved to the rationale companion at this
cycle's Slice 0. See Low-2.

### `## Slice checklist` → Slice 4 (docs + card wrap) — 4 boxes, all `OUT-OF-FENCE`

| Box | Grade | Evidence |
|---|---|---|
| Slice 4 (doc updates + card wrap) | BUILT-CONFORMANT — `OUT-OF-FENCE` | all three sub-boxes landed |
| Implemented-on-main docs | BUILT-CONFORMANT — `OUT-OF-FENCE` | `docs/TREE.md` carries `rest_framework/` rows for both source and tests; `TODAY.md` mentions the serializer flavor (5 occurrences); `docs/GLOSSARY.md` carries the `SerializerMutation` body, the Public-exports line, the Index line and the Mutations category row; `GOAL.md` #"class CreateCategoryFromSerializer(SerializerMutation):" |
| Joint-cut docs | BUILT-CONFORMANT — `OUT-OF-FENCE` | `docs/GLOSSARY.md` status row reads `shipped (`0.0.13`)`; `README.md` and `docs/README.md` both document the shipped surface (`docs/README.md` #"`SerializerMutation` subclasses `DjangoMutation`") |
| Card wrap | BUILT-CONFORMANT — `OUT-OF-FENCE` | `KANBAN.md` #"`DONE-039-0.0.13`" … "Done" |

Remedies for these rows fall outside the cycle's spec-plus-`.py` fence. Graded, recorded,
not proposed.

---

### `## User-facing API` and `### Error shapes`

| Row | Grade | Evidence |
|---|---|---|
| `## User-facing API` (the `ItemSerializer` / `CreateItemViaSerializer` example + generated SDL) | BUILT-CONFORMANT | `examples/fakeshop/apps/products/schema.py` declares `CreateItemViaSerializer` / `UpdateItemViaSerializer` on this exact shape; the generated names are pinned live by `test_library_api.py::test_n_sdl_products_serializer_input` and exercised by 19 `test_products_api.py` rows. `partial=True` update, `categoryId` reverse-map, `"__all__"` bucket, and inherited `DjangoModelPermission` all confirmed below |
| Error shape 1 — `Meta` misconfiguration raises `ConfigurationError` naming the key | BUILT-CONFORMANT | `rest_framework/sets.py` #"must be a serializers.ModelSerializer with a concrete Meta.model; a plain " ; `"delete"` rejected via the shared `require_non_delete_operation` against `NON_DELETE_WRITE_OPERATIONS`; bare-string / duplicate / unknown / empty via `resolve_effective_serializer_fields` → `utils/inputs.py::normalize_field_name_sequence`; unknown key via `reject_unknown_meta_keys` over `_ALLOWED_SERIALIZER_META_KEYS` |
| Error shape 2 — `is_valid()` failure populates `FieldError`, save-time `ValidationError` maps the same way | BUILT-CONFORMANT | live: `test_products_api.py::test_create_item_via_serializer_validate_field_error_is_field_keyed`, `::test_create_item_via_serializer_object_validate_all_sentinel_and_request_context`; package: the two save-time branches in `tests/rest_framework/test_resolvers.py` |
| Error shape 3 — auth denial is a top-level `GraphQLError`, not a `FieldError` | BUILT-CONFORMANT | `test_products_api.py::test_create_item_via_serializer_anonymous_is_denied_top_level_error_no_write`, `::test_create_item_via_serializer_missing_model_perm_is_denied_no_write` |
| Error shape 4 — hidden relation id is a field-keyed `FieldError`, never an existence leak | BUILT-CONFORMANT | `test_products_api.py::test_create_item_via_serializer_hidden_category_id_is_field_keyed_relation_error` |
| Error shape 5 — sync mutation over an `async def get_queryset` raises `SyncMisuseError` | BUILT-CONFORMANT | `resolvers.py` routes through the shared `utils/querysets.py::reject_async_in_sync_context`; pinned in `tests/rest_framework/test_resolvers.py` |
| Error shape 6 — importing without DRF raises `ImportError` with an install hint | BUILT-CONFORMANT | `tests/rest_framework/test_soft_dependency.py` — all three entry points, parametrized over every `_DRF_SOFT_EXPORTS` name |

---

### `## Edge cases and constraints` — 24 rows

| # | Row | Grade | Evidence |
|---|---|---|---|
| 1 | DRF not installed | BUILT-CONFORMANT | `rest_framework/__init__.py::require_drf` + `__init__.py::__getattr__`; `test_soft_dependency.py` |
| 2 | Serializer-only fields (no model column) | BUILT-CONFORMANT | `_walk_serializer_fields` converts them via the registry with no model lookup |
| 3 | Serializer-only RELATION fields (F4) | BUILT-CONFORMANT | `serializer_converter.py` resolves the target from `field.queryset.model`; neither-column-nor-queryset raises |
| 4 | Relation target with no registered primary `DjangoType` (M3) | BUILT-CONFORMANT, one stale symbol name | `serializer_converter.py` #"which has no registered primary DjangoType. " raises at class creation. The row's comparison to "the promoted `_visible_related_object` helper" names the wrong symbol (Medium-2) |
| 5 | Renamed serializer fields (`source`) | BUILT-CONFORMANT | live `test_products_api.py::test_create_item_via_renamed_serializer_happy_path` + the two wire-name error rows |
| 6 | Dynamic / kwargs-requiring serializers (schema-time) | BUILT-CONFORMANT | `sets.py::_checked_schema_field_map` guards `.fields` materialization and wraps residual failures as `ConfigurationError` |
| 7 | `get_serializer_kwargs` cannot swap the request actor (H3) | BUILT-CONFORMANT | `resolvers.py` #"context['request'] object; the framework owns the request context (the actor "; pinned by `tests/rest_framework/test_resolvers.py::test_merged_kwargs_override_different_request_object_is_configuration_error` |
| 8 | `read_only` / `HiddenField` dropped from the input | BUILT-CONFORMANT | dropped in the writable-basis computation; the live request-context proof is an explicit `validate()` branch as the row requires (`::test_create_item_via_serializer_object_validate_all_sentinel_and_request_context`) |
| 9 | `validate()` / `non_field_errors` → `"__all__"` | BUILT-CONFORMANT | `::test_create_item_via_serializer_unique_together_error_uses_all_sentinel` |
| 10 | `update` partial preservation via `partial=True` | BUILT-CONFORMANT | `::test_update_item_via_serializer_partial_update_preserves_other_fields` |
| 11 | File / image serializer fields | SUPERSEDED | The `Upload` mapping and the value-in-`data` routing shipped and are live-proven (`::test_create_item_via_serializer_multipart_upload_to_attachment`). **The row's "Full multipart HTTP ergonomics still await the `0.0.14` `TestClient`" is stale** — `django_strawberry_framework/testing/client.py` exists (card 043, the `0.0.14` cut). Re-tense, don't re-scope |
| 12 | Relation visibility is not delegated to the serializer's queryset | BUILT-CONFORMANT | decode checks through the related primary `DjangoType.get_queryset` before the serializer sees the id; `::test_create_item_via_serializer_hidden_category_id_is_field_keyed_relation_error` |
| 13 | `many=True` is a `ManyRelatedField` wrapper | BUILT-CONFORMANT | the `relation_multi` branch matches `serializers.ManyRelatedField` and reads `field.child_relation`. The row's own "verify against the installed DRF when Slice 1 lands" is discharged — DRF `3.18.0` resolved |
| 14 | Plain `serializers.Serializer` (no model) rejected | BUILT-CONFORMANT | `sets.py` #"must be a serializers.ModelSerializer with a concrete Meta.model; a plain " |
| 15 | `Meta.operation = "delete"` rejected | BUILT-CONFORMANT | `sets.py` #"(``\"delete\"`` rejected - DRF serializers do not delete, Decision 10) via" → `require_non_delete_operation` |
| 16 | Un-opted nested writable serializer fails loud | BUILT-CONFORMANT | `serializer_converter.py::_reject_nested_serializer`, the FIRST check in `resolve_serializer_field` |
| 17 | Write-time `IntegrityError` → envelope | BUILT-CONFORMANT | routed through the reused `036` `save_or_field_errors`; package-pinned |
| 18 | Write-time `ValidationError` — DRF and Django take different paths (F2/H2) | BUILT-CONFORMANT | two separate branches by exception class; package-pinned in `tests/rest_framework/test_resolvers.py` |
| 19 | Two distinct generated inputs colliding on one GraphQL name | BUILT-CONFORMANT | `materialize_generated_input_class` ledger raise, enriched by the rev6 #15 shape description |
| 20 | Two serializer fields colliding on one generated input name (M-edge) | BUILT-CONFORMANT | now folded into the rev6 #5 aggregate via `_collect_input_attr_collision_messages` |
| 21 | Two serializer fields sharing one writable `source` (M-edge) | BUILT-CONFORMANT | same collector; `read_only`-sharing accepted |
| 22 | Same serializer, same names, different shape | BUILT-CONFORMANT | `SerializerInputShape` descriptor identity |
| 23 | Create narrowing drops a required field | BUILT-CONFORMANT | `guard_create_required_serializer_fields`, run per declaration before the cache lookup |
| 24 | No `DjangoType` `Meta` key added — `DEFERRED_META_KEYS` / `ALLOWED_META_KEYS` byte-unchanged | BUILT-CONFORMANT as a claim about **this card**; SPEC-STALE as present tense | This card added neither. `types/base.py::DEFERRED_META_KEYS` is unchanged. `types/base.py::ALLOWED_META_KEYS` has since gained keys, and the file's own comment attributes every one to another card (`filesystem_path_fields` → spec-048, `nullable_overrides`/`required_overrides` → spec-029, `connection` → spec-030, `globalid_strategy` → spec-031, `relation_shapes` → spec-032). No settings key: `conf.py` at `HEAD` contains **zero** case-insensitive occurrences of "serializer". "byte-unchanged" now reads as a false claim about the file; see Low-3 |

---

### `## Test plan` — 9 bullets

The plan's own enumeration is 3 top-level bullets and 6 sub-bullets. Each is graded on
whether a test exists **and sits in the tier the plan named**.

| Bullet | Grade | Evidence |
|---|---|---|
| Preamble: the package-internal boundary owns exactly six listed categories | BUILT-CONFORMANT | `tests/rest_framework/` holds `test_converter.py` (1389 lines), `test_inputs.py` (1860), `test_sets.py` (2128), `test_resolvers.py` (5266), `test_soft_dependency.py` (163) — the six categories map onto them |
| **Live, over `/graphql/`** (Slice 3, `test_products_api.py`) — every reachable resolver branch | BUILT-CONFORMANT | **19** serializer rows in `examples/fakeshop/test_query/test_products_api.py`, covering every named scenario: happy create/update, wire-name-keyed `validate_<field>`, `"__all__"` for `validate()` and `UniqueTogetherValidator`, the renamed-field error path (F5) on both a scalar and the relation, `categoryId` reverse-map write, partial preservation, unique-together on a one-field change, visibility-scoped update not-found, anonymous + missing-perm denial, hidden-`Category` relation error, authorize-before-decode, multipart `Upload` → `Item.attachment`, request-context `validate()`, and the G2 re-fetch shape (`::test_g2_serializer_mutation_response_keeps_relation_with_bounded_query_count`) |
| `test_converter.py` | BUILT-CONFORMANT | all eleven named scenarios present in `tests/rest_framework/test_converter.py` |
| `test_inputs.py` | BUILT-CONFORMANT | all eleven named scenarios present in `tests/rest_framework/test_inputs.py` |
| `test_sets.py` | BUILT-CONFORMANT | `Meta` matrix, registration, phase-2.5 bind, retry-idempotence, no-primary-type error, model-flavor seam defaults |
| `test_resolvers.py` — genuinely-unreachable internals only | BUILT-CONFORMANT | recursive flattener shapes, raw-pk/non-Relay + many decode, `IntegrityError`, the two save-time `ValidationError` branches, call-once save spy, the `get_serializer_kwargs` precedence matrix incl. H3, sync/async + `SyncMisuseError` |
| **The DRF-absent import guard** | SPEC-STALE | Every asserted **behavior** shipped and is pinned in `tests/rest_framework/test_soft_dependency.py` (all three entry points, star-import stays DRF-free, non-memoization). **The stated mechanism is wrong** — see High-4 |
| `tests/mutations/test_fields.py` (extend) | BUILT-CONFORMANT | the file references `createItemViaSerializer`; the `038`-generalized factory accepts a `SerializerMutation` unchanged, verified rather than edited |
| Cross-cutting — no regression | BUILT-CONFORMANT (partial, by construction) | Read-only checks run this pass: `uv run ruff check django_strawberry_framework/rest_framework/ tests/rest_framework/` → `All checks passed!`; `uv run ruff format --check …` → `12 files already formatted`. **The `fail_under = 100` half is the maintainer's gate and is not worker-verifiable** (`BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`); no `--cov*` flag was run this pass |

**No planned scenario is unrunnable as written**, with one exception outside this section —
DoD item 1's command; see below.

#### Behavior landed, assertion did not — two rows

Recorded separately from the grades above, per the rule that a landed behavior with an
unlanded assertion is graded on the behavior and the missing assertion filed on its own.
Both were re-read in source this pass; neither is a missing *behavior*.

- **The G2 "no `.only(...)`" clause is pinned by a non-distinguishing assertion** (Medium-4).
  `test_products_api.py::test_g2_serializer_mutation_response_keeps_relation_with_bounded_query_count`
  pins the batching half properly — two real `products_item` SELECTs and three
  `products_category` SELECTs, absolute counts derived from a real run. The `.only(...)`
  half is asserted as:

  ```examples/fakeshop/test_query/test_products_api.py:4420
      # G2 NO `.only(...)` projection: the post-write re-fetch selects the full item
      # row (no SQL names a strict deferred column subset), so the row reads back whole.
      assert "SerG2Widget" in models.Item.objects.values_list("name", flat=True)
  ```

  That statement issues a **fresh** query against the table; it is true whether or not the
  re-fetch deferred any column, so it is structurally incapable of failing if a `.only(...)`
  projection were reintroduced on the re-fetch. `BUILD.md` `### Query-shape tests must pin
  the load-bearing property, not observability` is exactly on point. The fix is to assert
  against the captured re-fetch SQL already in scope (`sql` / `item_selects`) — that the
  post-write item SELECT names the full column set rather than a deferred subset — not to
  add another wire-level read.

- **The "same `context["request"]` object is tolerated" arm has no test** (Low-4). The
  spec's Edge case 7 / Test plan both pin the pair: a **different** request object raises,
  the **same** object is tolerated. The raise arm is pinned
  (`tests/rest_framework/test_resolvers.py::test_merged_kwargs_override_different_request_object_is_configuration_error`).
  For the tolerate arm, no test in the tree constructs an override whose returned `context`
  carries the identical request object — the nearest rows
  (`::test_merged_kwargs_merges_override_context_keys_keeping_framework_request` and
  `::test_merged_serializer_kwargs_preserves_custom_context_keys`) return a `context` with
  **no** `"request"` key at all and then assert the framework's request won. So the guard's
  identity check is pinned only on its rejecting side. Low rather than Medium: the unpinned
  side is the permissive one, and a regression there is a false rejection (loud), not a false
  acceptance.

**Not a finding: three planned package-tier assertions that live in the live tier.** The
`Meta.optional_fields` force-optional behavior, the `optional_fields` descriptor-name
divergence axis, and the M2 nullability set (`allow_null` → nullable; `required=True,
allow_null=True` still omittable; `allow_blank` absent from the SDL) are pinned in
`examples/fakeshop/test_query/test_library_api.py` rather than in
`tests/rest_framework/test_inputs.py` where the plan listed them. The plan **licenses exactly
this**: "If a planned `tests/rest_framework/test_resolvers.py` case turns out to be drivable
by a real products query, it **moves to the live suite** — that direction only." Each of the
three is driven over `/graphql/` with SDL introspection. Recorded so a later reader does not
re-raise it as a gap.

**Placement note (not a finding, recorded for Worker 1):** the plan's live tier names
`test_products_api.py`, and the products lane is fully there. But the majority of the
**rev6** live surface — `createShelfViaMetadataSerializer`, `updateBookViaSerializerWithLock`,
`createShelfWithSaveKwargs`, `createShelfViaAltBranchesSerializer`,
`createShelfWithInjectedTopic`, `createBranchWithNestedShelves`, and **both** golden-SDL
rows including the *products* one — lives in
`examples/fakeshop/test_query/test_library_api.py`. That is still the live tier and still
`/graphql/`-driven, so the Coverage rule is satisfied; the spec simply never says so. This
is the START.md "Live-tier README under-enumerates its suites; silence ≠ 'no such suite'"
hazard in spec form.

---

### `## Definition of done` items 1, 6, 7, 8

| Item | Grade | Evidence |
|---|---|---|
| **1** — spec + companion CSV exist; `check_spec_glossary.py --spec docs/spec-039-…md` reports `OK: <N> terms` | SPEC-STALE (the command is **unrunnable as written**) | Both files exist, at `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` and `docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-terms.csv`. Run at the documented path: `error: missing file: docs/spec-039-serializer_mutations-0_0_13.md`. Run at the actual path: `OK: 38 terms - all have glossary entries and at least one spec link.` The **contract holds**; the two path literals do not. See Medium-3 |
| **6** — full suite green at the 100% gate incl. the DRF-absent path; `ruff` clean; `036`/`038` + read side unchanged | BUILT-CONFORMANT on the worker-verifiable half | `ruff check` and `ruff format --check` both clean over `rest_framework/` + `tests/rest_framework/` (commands and output above). The DRF-absent path is covered by `test_soft_dependency.py`. **The coverage half is explicitly the maintainer's gate**; `BUILD.md` forbids a worker from measuring it, so it is recorded as a claim rather than graded. `036`/`038` unchanged: `mutations/fields.py` had **no** commit in the 039 window |
| **7** — the Slice 0 gate + the Slice 4 doc updates | BUILT-CONFORMANT — Slice 4 half `OUT-OF-FENCE` | Gate: verified in the Slice 0 table. Slice 4: verified in the Slice 4 table |
| **8** — no version bump in this card; `SerializerMutation` a named lazy export absent from `__all__` | BUILT-CONFORMANT | **This is a claim about what this card did, not about today's version numbers.** At `60dbf469`, `__version__` and the `uv.lock` package `version` both read `0.0.12`; the bump landed in `fa704722` (card 040, the joint cut). Today the package reads `__version__ = "0.0.15"` — **three** releases past `0.0.13` — which neither confirms nor falsifies item 8. The export half holds exactly at `HEAD`: `__init__.py::_DRF_SOFT_EXPORTS` maps `SerializerMutation` to `.rest_framework.sets`, and `__init__.py::__all__` (35 names, listed) contains **none** of the seven soft exports |

---

### `## Non-goals` (7) and `## Out of scope` (8)

| Row | Grade | Evidence |
|---|---|---|
| Non-goal — Auth mutations | BUILT-CONFORMANT | shipped separately in `fa704722` (card 040), as the row says |
| **Non-goal — "adds no field to `FieldError`"** | **The boundary no longer holds — see High-3** | `mutations/inputs.py::FieldError` carries `codes` and `path`, added by this spec's own rev6 #4/#13. `KANBAN.md` independently records it: #"`FieldError` grew from 2 members to 4 (`codes` and `path` landed with `spec-039` / `DONE-039-0.0.13`), so the type is ADDITIVE, not frozen." |
| Non-goal — does not re-open `mutations/inputs.py` / `forms/inputs.py`; no `mutations/fields.py` edit | SPEC-STALE (first clause), BUILT-CONFORMANT (second) | `mutations/inputs.py` **was** re-opened — that is where `codes`/`path` and the shared `field_error` leaf live. `mutations/fields.py` genuinely unedited |
| Non-goal — model-less plain `Serializer` flavor | BUILT-CONFORMANT | still rejected at class creation |
| Non-goal — Serializer-derived output types | BUILT-CONFORMANT | payload object is the primary `DjangoType` in the frozen `node`/`result` slot. The row already reconciles the nested-write half to rev6 #17 |
| Non-goal — Serializer `delete` | BUILT-CONFORMANT | `require_non_delete_operation` rejects it |
| Non-goal — graphene's `Meta.model_operations` / `Meta.lookup_field` | BUILT-CONFORMANT | `rg -c 'model_operations|lookup_field'` over the package → **0** |
| Non-goal — new `DjangoType` `Meta` key or settings key | BUILT-CONFORMANT for this card | see Edge case 24 |
| Out of scope — Auth mutations | BUILT-CONFORMANT | card 040 |
| Out of scope — model-less plain `Serializer` | BUILT-CONFORMANT | still deferred |
| Out of scope — serializer-derived output types | BUILT-CONFORMANT | still not shipped |
| Out of scope — Serializer `delete` | BUILT-CONFORMANT | still not shipped |
| **Out of scope — the ergonomic `TestClient` / `AsyncTestClient` (`TODO-ALPHA-043-0.0.14`)** | SUPERSEDED | `django_strawberry_framework/testing/client.py` exists; `docs/GLOSSARY.md` records the `0.0.14` joint cut shipping `TestClient` / `GraphQLTestCase`. It shipped **where the row said it would**, so this is a re-tense, not a breach |
| Out of scope — Field-level read gates (`FieldSet`, `0.1.1`) | BUILT-CONFORMANT | still deferred |
| **Out of scope — "The `0.0.13` version bump"** | SUPERSEDED | it happened, in `fa704722`, exactly as the row routes it. Present tense is now wrong |
| Out of scope — new `DjangoType` `Meta` key or settings key | BUILT-CONFORMANT | see Edge case 24 |

---

### `## Current state` and `## Goals` — clause by clause, under `BUILD.md` `### '## Current state': observations stand, predictions do not`

A falsified **observation** stays (the section header dates it); a falsified **prediction**
is rewritten. Verdicts for Worker 1:

| Clause | Kind | Verdict | Action for Worker 1 |
|---|---|---|---|
| CS-1 "The mutation foundation and the form flavor are shipped" + the `_resolve_model` docstring quote | observation | still true (`mutations/sets.py::DjangoMutation._resolve_model` still reads #"the 0.0.13\n        serializer flavor (``Meta.serializer_class.Meta.model``)") | **keep verbatim** |
| CS-2a "The field factory is already generalized … by `spec-038` Slice 3" | observation | true | **keep** |
| CS-2b "This card needs **no** field-factory edit; it verifies the generalization holds" | **prediction** | **held** — `git log 60dbf469~15..60dbf469 -- django_strawberry_framework/mutations/fields.py` is empty | **keep** |
| CS-3 "**No `rest_framework/` module exists** … neither is on disk. The package root exports … but no `SerializerMutation`" | observation | falsified by the build, as intended | **keep — dated observation** |
| CS-4a "`djangorestframework` is not installed and not a dependency" | observation | falsified by the build, as intended | **keep** |
| CS-4b "This card adds DRF to the **dev group only**" | **prediction** | **held** | **keep** |
| CS-5a "The version line reads `0.0.12`" | observation | falsified (now `0.0.15`) | **keep — dated observation** |
| CS-5b "this card does **not** move them" | **prediction** | **held** (`60dbf469`) | **keep** |
| CS-6a "`0.0.13` has two cards … there is a joint cut to defer the version bump to" | observation | true | **keep** |
| CS-6b "(The `KANBAN.md` `## In progress` column is empty as this spec is authored …)" | observation, explicitly self-dating | falsified now | **keep verbatim — it dates itself in-clause** |
| CS-7a "The products write surface is live … products has **no** `serializers.py` yet" | observation | falsified (`examples/fakeshop/apps/products/serializers.py` exists) | **keep — dated observation** |
| CS-7b "a `ModelSerializer` over `Item` surfaces that as a DRF `UniqueTogetherValidator` … the live `"__all__"`-sentinel coverage" | **prediction** | **held** — `::test_create_item_via_serializer_unique_together_error_uses_all_sentinel` | **keep** |
| Goal 1 — ship `SerializerMutation` on the `class Meta` surface | prediction | held | keep |
| Goal 2 — derive the input from the serializer's declared fields | prediction | held | keep |
| Goal 3 — "**Reuse the frozen `FieldError` envelope** … the **byte-identical** `FieldError` envelope `036` defined" | **prediction** | **FALSIFIED** — the envelope is additive, not byte-identical (High-3) | **rewrite**: reuse the shared envelope, which this card extends additively with `codes` / `path` |
| Goal 4 — run the write through the serializer, one `transaction.atomic()`, optimizer re-fetch | prediction | held | keep |
| Goal 5 — compose with the shipped permission + visibility seams | prediction | held | keep |
| Goal 6 — keep DRF a soft dependency | prediction | held | keep |
| Goal 7 — ship the products live serializer surface (folded into Slice 3) | prediction | held | keep |
| Goal 8 — "No slice edits `[project].version` / `__version__` / `test_version` — **these stay `0.0.12` until the joint cut**"; `uv.lock` updated in Slice 0 but its package `version` stays `0.0.12` | **prediction** | **held for this card**, but the present-tense "these stay `0.0.12`" now reads as a claim about today (`0.0.15`) | **re-tense to past/card-scoped**, do not delete |

---

### High:

#### High-1 — `rev6 #14` describes an opt-IN default-`False` lock; the shipped contract is opt-OUT, default-`True`, and applies to all three write flavors

`SUPERSEDED` by the `0.0.14` concurrency hardening. The spec states three things the code
contradicts:

- "`Meta.select_for_update = True` … **opts** the UPDATE locate into a `SELECT … FOR UPDATE`
  row lock" — locking is now the **default**, and `False` is the opt-**out**.
- "`locate_instance(target_type, node_id, info, *, select_for_update=False)`" — the shipped
  signature is `select_for_update: bool = True`.
- "`run_write_pipeline_sync` passes `meta.select_for_update` (**default `False` for the
  model / form flavors**)" — the model and form flavors now default to `True` through the
  shared `mutations/sets.py::model_backed_permission_and_lock`.

```django_strawberry_framework/mutations/sets.py:970
    select_for_update = getattr(meta, "select_for_update", True)
```

```django_strawberry_framework/mutations/resolvers.py:589
    select_for_update: bool = True,
```

The code's own comments attribute it: `mutations/sets.py` #"``Meta.select_for_update``
(expanded by the 0.0.14 concurrency hardening)" and `mutations/resolvers.py`
#"``Meta.select_for_update``, default True since the 0.0.14 concurrency hardening". The
package-level docs already describe the shipped contract — `docs/README.md` #"Every
model-backed flavor locks its target and relation rows by default (`Meta.select_for_update`;
`False` opts out)". **The spec is the only surface still describing the pre-hardening
contract.**

Why it matters: a reader taking `rev6 #14` at face value would believe an un-annotated
serializer update takes no row lock. It does. A `spec-039` consumer reading only the spec
would also be surprised that a `DjangoModelFormMutation` update now locks.

Recommended change (Worker 1): rewrite `### rev6 #14` to state the corrected contract
directly — locking is the default for every model-backed flavor, `Meta.select_for_update =
False` opts out, `locate_instance`'s keyword defaults to `True` — with **no chronology in
the spec**. The "what changed and why" belongs in the rationale companion. Note the section
title "**Optional** row locking" is itself now wrong.

Test expectation: unchanged — `updateBookViaSerializerWithLock` and the `locate_instance`
package rows already pin the shipped behavior.

#### High-2 — `rev6 #12`'s `get_serializer_save_kwargs` signature, its canonical example, and its live-test claim are all superseded

`SUPERSEDED` by the hook-context hardening pass.

1. **Signature.** Spec: `get_serializer_save_kwargs(info, data, instance=None) -> dict`.
   Shipped: `(self, info, *, data, hook_context)` — `instance` was replaced by the frozen
   `SerializerHookContext` (`django_strawberry_framework/rest_framework/hook_context.py`,
   exported through `__init__.py::_DRF_SOFT_EXPORTS`).
2. **A second guard the spec does not mention.** The spec describes only
   `_assert_save_kwargs_no_shadow`. `HEAD` also carries
   `rest_framework/resolvers.py::_assert_save_kwargs_not_model_fields`, which refuses **any**
   save kwarg naming a model field or `attname`.
3. **The spec's own example is now refused.** `rev6 #12` names
   `owner=request.user` as the motivating case. If `owner` is a model field on the target
   model — and in the motivating case it is — that kwarg now raises `ConfigurationError`.
4. **The live-test claim is false.** Spec: "Live-tested (`createShelfWithSaveKwargs` **stamps
   a server-side `topic` at save**)". The shipped hook stamps `{"stamp": "stamped-at-save"}`;
   `topic` is a `Shelf` model field and is the *negative* fixture —
   `examples/fakeshop/apps/library/schema.py::CreateShelfWithModelFieldSaveKwargs` returns
   `{"topic": "smuggled-model-field"}` precisely to prove the raise.

```django_strawberry_framework/rest_framework/resolvers.py:1503
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}.get_serializer_save_kwargs returned "
            f"kwarg(s) {offenders!r} that name {model.__name__} model field(s); a save kwarg "
            "bypasses validation and visibility, so model-field injection must go through "
            "Meta.injected_fields + get_serializer_injected_data instead. Save kwargs may "
            "only carry non-model custom arguments.",
        )
```

Why it matters: this is the one row where a consumer following the spec writes code that
**raises at runtime**. The remedy is a spec rewrite, not code — the shipped guard is the
correct, stricter contract, and it is the channel `Meta.injected_fields` exists to replace.

Recommended change (Worker 1): rewrite `### rev6 #12` to the shipped signature, name **both**
guards, replace the `owner=request.user` example with a non-model custom kwarg (the
`serializer.save(notify=True)` shape the guard's own docstring cites), and correct the
live-test sentence to `stamp`. Route model-field injection to `Meta.injected_fields`
explicitly in the same paragraph.

#### High-3 — `## Non-goals`, `### Decision 2`, and Goal 3 all promise a `FieldError` envelope this card demonstrably extended

A spec contract violation, and an internal contradiction: `rev6 #4` and `rev6 #13` — in this
same document, both marked "all seventeen ship in `0.0.13`" — add `codes: [String!]` and
`path: [String!]` to `FieldError`, while three other sections say the card adds none.

```django_strawberry_framework/mutations/inputs.py:157
    codes: list[str] = strawberry.field(default_factory=list)
    path: list[str] = strawberry.field(default_factory=list)
```

The type's own docstring already records the correction (#"frozen - a member may be added
(``codes`` / ``path`` below were), never"), and so does `KANBAN.md` (#"`FieldError` grew
from 2 members to 4 (`codes` and `path` landed with `spec-039` / `DONE-039-0.0.13`), so the
type is ADDITIVE, not frozen"). Only the spec still says otherwise.

Three sites, all in this cohort:

- `## Non-goals` bullet 2 — "this card adds **no** field to
  [`FieldError`][glossary-fielderror-envelope], does not re-open
  [`mutations/inputs.py`][mutations-inputs]". Both clauses are false.
- `### Decision 2` — "This card adds **no** field to
  [`FieldError`][glossary-fielderror-envelope] and does not re-open the `036` / `038` input
  generators".
- `## Goals` item 3 — "the **byte-identical** [`FieldError`][glossary-fielderror-envelope]
  envelope `036` defined".

Why it matters: `docs/builder/BUILD.md` `## Severity definitions` makes a spec contract
violation High, and this one is load-bearing twice over — a reader deriving the `0.0.13`
public surface from Non-goals gets a two-member `FieldError`, and the `036` "frozen" claim
is the thing downstream flavor cards were told to rely on.

Recommended change (Worker 1): rewrite all three to the additive contract — the envelope's
`field` / `messages` shape is reused unchanged and the card **adds** the two default-empty
members `codes` and `path` through the single shared `field_error` leaf, so every flavor
gains them uniformly. State it as the current contract, no chronology.

Test expectation: already pinned — the golden-SDL rows assert `codes` / `path` on
`FieldError`, and `createShelfViaMetadataSerializer` proves a DRF `max_length` code live.

#### High-4 — the DRF-absent simulation mechanism is documented as `builtins.__import__`, which the repo has explicitly banned as a silent pass

`SPEC-STALE`, stated **twice**: `### Decision 12` item 3 ("monkeypatching `builtins.__import__`
so the guarded `import rest_framework` fails") and `## Test plan` ("with DRF's import
simulated-absent (monkeypatched `builtins.__import__`, …)").

The shipped harness uses the `sys.modules[name] = None` sentinel:
`tests/rest_framework/test_soft_dependency.py::_simulate_drf_absent` calls
`tests/_soft_dependency.py::simulated_absence`, whose own docstring records the replacement
— #"which is why it replaces the older ``builtins.__import__`` block and its ``level == 0``
discrimination." `START.md` states the rule directly: "Never patch `builtins.__import__`
(guards use `importlib.import_module`; block silently passes)."

Why it matters: `require_drf()` reaches DRF through
`utils/imports.py::require_optional_module` → `importlib.import_module`. A
`builtins.__import__` patch does not intercept that call, so a suite written to the spec's
letter would **pass without ever exercising the guard** — a self-falsifying instrument, and
the exact fail-open the audit is meant to catch. The behavior is correct; the spec would
teach the next author to break it.

Recommended change (Worker 1): rewrite both sentences to name the sentinel and the shared
helper (`sys.modules["rest_framework"] = None` via
`tests/_soft_dependency.py::simulated_absence`, with the two-sided eviction/restore of both
`rest_framework*` and `django_strawberry_framework.rest_framework*`), and state why the
`builtins.__import__` shape does not work. Keep the eviction-discipline sentences — those
are still exactly right.

### Medium:

#### Medium-1 — `rev6 #2` names `_assert_injected_field_agreement`, a symbol that does not exist

`SPEC-STALE`. `rg -g '*.py' '\b_assert_injected_field_agreement\b'` over
`django_strawberry_framework/`, `tests/` and `examples/` returns **0** occurrences.

The behavior did ship: injected-field runtime acceptance rides the **same** walk as input
fields, through `rest_framework/resolvers.py::_write_surface_specs` ("the top-level
write-surface specs: GraphQL input fields + `Meta.injected_fields`") consumed by
`::_assert_schema_runtime_agreement` → `::_assert_field_agreement`. This is a strictly
better shape than two parallel guards, and it is what `rev6 #1` describes for the input
half — the spec just never merged the two paragraphs.

Recommended change: rewrite `rev6 #2`'s runtime-acceptance sentence to name the unified walk
(`_write_surface_specs` feeding `_assert_schema_runtime_agreement`), and drop the
non-existent symbol. `AGENTS.md` rule 27 makes a `path::Symbol` that cannot resolve a real
defect; `scripts/check_citations.py` did not catch it because the spec names the symbol in
prose without a path prefix.

#### Medium-2 — `### Decision 4`'s "Shared-helper homes" names two symbols/paths that are not where the promotions landed

`SPEC-STALE`, two clauses:

- "the **relation-decode core** (`_visible_related_object`, **P1.1**) is promoted into
  [`utils/querysets.py`][utils-querysets]". The promotion landed as the **public**
  `utils/querysets.py::visible_related_object` (plus the batched
  `::visible_related_objects` that `rev6 #3` adds). The private
  `types/resolvers.py::_visible_related_object` still exists and is a **different**,
  read-side helper — so the spec's name resolves to the wrong function, which is worse than
  not resolving. `## Edge cases` row 4 repeats the same wrong name.
- "the … **non-delete ops constant** (**P1.2**) … land in [`mutations/sets.py`][mutations-sets]
  (or a sibling `mutations/bind_helpers.py`)". They landed in a net-new
  `django_strawberry_framework/mutations/operations.py`, as
  `::NON_DELETE_OPERATION_INPUT_KIND` and `::NON_DELETE_WRITE_OPERATIONS`.
  `mutations/bind_helpers.py` does not exist.

Everything else in that paragraph is exact: `utils/converters.py::convert_with_mro` (P1.4),
`mutations/sets.py::reject_unknown_meta_keys` (P2.7),
`mutations/sets.py::clear_mutation_shape_build_cache` (P1.3),
`mutations/resolvers.py::run_write_pipeline_sync` (P1.5), and the `register_subsystem_clear`
seam (P1.6) — `rest_framework/inputs.py::clear_serializer_input_namespace` is announced
through it, not hand-wired.

Recommended change: repoint both clauses to the shipped symbols and add
`mutations/operations.py` to Decision 4's module list, which currently names only the four
`rest_framework/` modules and so under-enumerates the card's source footprint (it also omits
`rest_framework/__init__.py` — the guard module — and `rest_framework/hook_context.py`).

#### Medium-3 — DoD item 1's verification command is unrunnable as written

`SPEC-STALE`. The item instructs:

```
uv run python scripts/check_spec_glossary.py --spec docs/spec-039-serializer_mutations-0_0_13.md
```

Run this pass, verbatim: `error: missing file:
docs/spec-039-serializer_mutations-0_0_13.md`. Run at the archived path:
`OK: 38 terms - all have glossary entries and at least one spec link.`

Both artifacts exist; only the two path literals are stale, because a later spec's
`docs/SPECS/NEXT.md` Step 8 sweep archived the spec and moved the CSV to
`docs/SPECS/appx/`. Per `START.md`'s unrunnable-test class, this is a **spec finding, not a
missing test**.

Recommended change: repoint both literals in DoD item 1 to
`docs/SPECS/spec-039-serializer_mutations-0_0_13.md` and
`docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-terms.csv`, and record `OK: 38 terms`
as the measured value. The same repoint discharges Decision 1 (its own stale-path claim is
graded above).

#### Medium-4 — the G2 test's "no `.only(...)`" assertion cannot fail if `.only(...)` returns

Full evidence and the recommended replacement are in **"Behavior landed, assertion did not"**
above. In short: `test_products_api.py::test_g2_serializer_mutation_response_keeps_relation_with_bounded_query_count`
closes with a fresh `models.Item.objects.values_list("name", flat=True)` membership check
under a comment claiming it proves the re-fetch used no column deferral. It does not — the
statement queries the table again and is true either way.

Why it matters: `## Definition of done` item 4 and Decision 9 both make "no `.only(...)`" an
explicit G2 contract, and the spec's Test plan names it as a live-tier obligation. The
query-count half of that test is excellent; this one clause is the only non-distinguishing
assertion found in the whole cohort. Under `BUILD.md` `### Query-shape tests must pin the
load-bearing property, not observability` it is a Medium.

Recommended change: assert against the already-captured re-fetch SQL (`sql` / `item_selects`
are both in scope in that test) that the post-write `products_item` SELECT names the full
column set, not a deferred subset. **This is a test edit, not a spec edit** — Worker 1 should
route it to a builder pass rather than absorb it into Slice 2.

Test expectation: with a `.only(...)` reintroduced on the G2 re-fetch, the replacement
assertion must fail; the current one does not.

### Low:

#### Low-1 — `rev6 #17` omits the empty-declaration carve-out the code implements

`rest_framework/sets.py` #"An EMPTY declaration passes no nested data and demands no
override" — a `Meta.nested_fields = {}` does not trigger the mandatory `create()` /
`update()` override. The spec's bullet reads as unconditional ("`Meta.nested_fields`
**REQUIRES** the serializer to override `create()` … `update()`"). Not load-bearing; a
one-clause addition would close it.

#### Low-2 — `require_drf()`'s docstring names the wrong "place 3"

`rest_framework/__init__.py` #"(place 2 of the three-places-that-must-agree: place 1 is the"
continues "place 3 is the spec **Risks** note". Both the spec's Slice 0 checklist and
Decision 12 name **Decision 12** as place 3, and this cycle's Slice 0 moved
`## Risks and open questions` into the rationale companion, so the docstring now points at a
section that is not in the spec. The floor value itself is correct in all three real places.
A `.py` docstring fix is inside the cycle's fence; it belongs to whichever slice Worker 1
routes it to, not to this read-only pass.

#### Low-3 — three present-tense claims now read as assertions about today's tree

Each was true of this card and is false as a present-tense statement. All three want
re-tensing to card scope, not deletion:

- `## Edge cases` row 24 — "`DEFERRED_META_KEYS` / `ALLOWED_META_KEYS` are **byte-unchanged**."
  `ALLOWED_META_KEYS` has since gained `filesystem_path_fields` (spec-048) and others.
- `## Out of scope` — "**The ergonomic `TestClient` / `AsyncTestClient` helper** …
  (`TODO-ALPHA-043-0.0.14`)" and `## Edge cases` row 11's "Full multipart HTTP ergonomics
  still **await** the `0.0.14` `TestClient`." It shipped, where the row said it would.
- `## Out of scope` — "**The `0.0.13` version bump** — owned by the joint `0.0.13` cut." It
  happened (`fa704722`).

#### Low-4 — the "same `context["request"]` object is tolerated" arm is unpinned

Full evidence in **"Behavior landed, assertion did not"** above. The H3 guard's rejecting
side is pinned; its tolerating side is not — no test returns an override `context` carrying
the identical request object. Low because the unpinned side is the permissive one: a
regression there produces a loud false rejection, not a silent false acceptance. A single
row added beside `::test_merged_kwargs_override_different_request_object_is_configuration_error`
closes it. Test edit, not a spec edit.

### DRY findings

No new duplication: this pass added no code. Three observations from reading the shipped
tree side by side, all recorded rather than actioned.

- **The unified write-surface walk is the right shape and the spec should say so.**
  `rest_framework/resolvers.py::_write_surface_specs` is the single list six per-field
  disciplines iterate (schema/runtime agreement, write-source ownership, queryset scoping,
  the relation-intent ledger, the M2M snapshot, the post-save attestation). The spec's
  `rev6 #1` / `rev6 #2` still describe it as two separate guards (Medium-1). Documenting the
  unification protects it: a future author reading the spec would plausibly re-fork a
  second injected-field guard.
- **The soft-dependency guards are already single-sited, and the spec's Decision 12 text
  predates the consolidation.** `rest_framework/__init__.py::require_drf`,
  `routers.py::require_channels`, and `middleware/debug_toolbar.py::require_debug_toolbar`
  are three thin wrappers over one `utils/imports.py::require_optional_module`, and the test
  side is likewise single-sited in `tests/_soft_dependency.py`. Decision 12 describes only
  the DRF wrapper in isolation. Not a defect — worth a pointer when High-4 is rewritten.
- **No existence challenge raised.** Every abstraction this cohort touches has more than one
  real caller: `convert_with_mro` serves both the form and serializer converters,
  `NON_DELETE_OPERATION_INPUT_KIND` serves all three flavors, `require_optional_module`
  serves three soft deps, `field_error` serves both flatteners plus the framework-generated
  errors. `_SERIALIZER_SHAPE_REGISTRY` (rev6 #15) is the thinnest — one public reader
  (`describe_serializer_input`) plus one internal reader (the collision-message enrichment)
  — but the second reader is the one that earns it, so it is not a one-caller indirection.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. The file is clean at
`HEAD`; this pass changed nothing, and no unexpected drift is present.

Read at `HEAD` for the audit: `__all__` is a 35-name tuple containing **none** of the seven
`_DRF_SOFT_EXPORTS` names (`SerializerMutation`, `register_serializer_field_converter`,
`SerializerFieldConversion`, `describe_serializer_input`, `NestedSerializerConfig`,
`SerializerHookContext`, `UploadMetadata`). That is authorized by `### Decision 12` #"and is
**NOT in `__all__`** while DRF is soft" and by DoD item 8.

One note for Worker 1: Decision 12 and DoD item 8 both speak of **`SerializerMutation`** as
"the one net-new public symbol". The shipped soft-export surface is **seven** names — five
added by the rev6 items the spec itself carries (`register_serializer_field_converter` /
`SerializerFieldConversion` from #11, `describe_serializer_input` from #15,
`NestedSerializerConfig` from #17) plus two from the hook-context hardening pass
(`SerializerHookContext`, `UploadMetadata`). The **contract** (lazy, guarded, out of
`__all__`) holds for all seven; only the count is stale. Decision 5 owns that sentence and
belongs to a sibling cohort, so it is surfaced rather than graded here.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

One observation for the record, from `KANBAN.md` rather than from `CHANGELOG.md` itself:
the board carries an open item stating that `CHANGELOG.md`'s `[0.0.12]` entry still calls the
mutation error envelope "byte-identical", which High-3 shows is false. It is already owned
by that card and is `OUT-OF-FENCE` here.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

This pass modified none of those surfaces; the reads below are audit evidence for the Slice 4
row and are recorded as `OUT-OF-FENCE`.

- Version strings / statuses / card ids agree: `docs/GLOSSARY.md` carries
  `| [`SerializerMutation`](#serializermutation) | shipped (`0.0.13`) |` and `KANBAN.md`
  carries `DONE-039-0.0.13 … Done`, consistent with the post-joint-cut state.
- `docs/TREE.md` carries `rest_framework/` rows for both the package and the test tree, and
  their summary text is the module docstring — no staging language ("planned", "Slice N",
  `TODO(`) survives in either.
- `GOAL.md`'s crit-6 example reads `class CreateCategoryFromSerializer(SerializerMutation):`,
  the correction DoD item 7 required.
- No obsolete "coming soon" / "planned" wording for this flavor remains in `README.md` or
  `docs/README.md`; both document the shipped surface.

### What looks solid

- **Nothing this cohort owns was dropped.** All 17 `rev6` items, all six Decisions, both
  slice-checklist blocks, all 24 edge cases, all nine test-plan bullets and all four DoD
  items are implemented at `HEAD`. For a card that shipped three releases ago and was
  reworked by at least two later hardening passes, that is a strong result.
- **The live-first mandate was honored with room to spare.** 19 serializer rows in
  `test_products_api.py` earn every reachable products branch, and the rev6 surface is
  earned by a further seven named operations over `/graphql/` in `test_library_api.py`. The
  package tier really does hold only unreachable residue.
- **The soft-dependency guard reads closed, not open.** `require_drf()` delegates to
  `utils/imports.py::require_optional_module` with no bare `except`, no truthiness test on a
  module that can be `None`, and no `getattr` default; the root `__getattr__` resolves
  through the same guard on every access with no memoization, and returns a plain
  `AttributeError` for every non-soft name. The `sys.modules` sentinel is exactly the
  mechanism `START.md` prescribes. No fail-open shape found on this decision path.
- **The three-place floor genuinely agrees.** All three were read this pass, not assumed.
- **The stricter-than-planned guards are the right direction.**
  `_assert_save_kwargs_not_model_fields` and the default-on row lock both close holes the
  original spec left open; the defect is that the spec was never re-pointed at them, not
  that they exist.

### Temp test verification

- Temp test files used during review: **none**. `docs/builder/temp-tests/039-audit-4/` was
  created and left empty; no scratch test was needed, because every grade rests on reading
  `HEAD` source plus already-shipped test rows.
- Read-only scratch artifacts (outside the repo, in the session scratchpad): the `HEAD`
  copies of `utils/querysets.py`, `conf.py`, and the spec.
- Static helper `scripts/review_inspect.py`: **skipped, deliberately.** `docs/builder/BUILD.md`
  `### When to run the helper during build` triggers it for a slice that *adds* a `.py` file,
  *touches* `optimizer/` or `types/`, or *adds* 30+ lines. This pass adds and touches nothing
  — its diff against `HEAD` is empty by contract — so no trigger fires. Recorded per the
  explicit-skip rule.
- Failability proofs: **none, and none owed.** `BUILD.md` `### What needs a proof, and what
  does not` scopes the obligation to boundaries a pass *introduces*. This pass introduces
  none, so the mandatory re-run floor is satisfied by an empty set — legal exactly because
  the diff introduces no boundary that meets the floor. No production code was mutated at any
  point in this pass.
- Hot-path budget: not applicable; the plan declares `none` for Slices 1a–1d and this pass
  makes no executable change.
- Floor verification: not applicable; the plan declares floor-verification scope `none` for
  Slices 0–2.
- Disposition: `docs/builder/temp-tests/039-audit-4/` is empty and can be removed with the
  cycle's scratch.

### Notes for Worker 1 (spec reconciliation)

Ordered by what a reader gets most wrong. Every item is a **spec edit**; **no code change is
owed by this cohort**, so no `bld-039-slice-3-code_gaps.md` is triggered by Slice 1d.

1. **`### rev6 #14` — rewrite to the shipped lock contract** (High-1). Locking is the default
   for every model-backed flavor; `Meta.select_for_update = False` opts out;
   `locate_instance`'s keyword defaults to `True`. Retitle away from "**Optional** row
   locking". Chronology (the `0.0.14` concurrency hardening) goes in the rationale companion
   under a `rev6 #14` entry, never in the spec.
2. **`### rev6 #12` — rewrite signature, example, and live-test claim** (High-2). Shipped
   signature `(self, info, *, data, hook_context)`; name **both** guards; replace
   `owner=request.user` with a non-model kwarg; the live fixture stamps `stamp`, not `topic`
   (`topic` is the negative fixture). Point model-field injection at `Meta.injected_fields`.
3. **Three sites promising an unextended `FieldError`** (High-3): `## Non-goals` bullet 2,
   `### Decision 2`, `## Goals` item 3. Rewrite to the additive contract. Note bullet 2's
   second clause ("does not re-open `mutations/inputs.py`") is false too.
4. **Two sites naming `builtins.__import__`** (High-4): `### Decision 12` item 3 and the
   `## Test plan` DRF-absent bullet. Replace with the `sys.modules[…] = None` sentinel via
   `tests/_soft_dependency.py::simulated_absence`, and say why the `__import__` patch does
   not intercept `importlib.import_module`.
5. **`### rev6 #2`** — drop `_assert_injected_field_agreement` (0 occurrences) and name the
   unified `_write_surface_specs` → `_assert_schema_runtime_agreement` walk (Medium-1).
6. **`### Decision 4` "Shared-helper homes"** — repoint `_visible_related_object` →
   `utils/querysets.py::visible_related_object`, and the non-delete ops constant →
   `mutations/operations.py::NON_DELETE_OPERATION_INPUT_KIND` /
   `::NON_DELETE_WRITE_OPERATIONS`. Add `mutations/operations.py`,
   `rest_framework/__init__.py`, and `rest_framework/hook_context.py` to Decision 4's module
   list (Medium-2). `## Edge cases` row 4 carries the same wrong symbol name.
7. **DoD item 1 and `### Decision 1`** — repoint the archived spec / companion paths;
   record `OK: 38 terms` (Medium-3).
8. **`## Current state` / `## Goals`** — clause-level verdicts are tabulated above. **Eleven
   observation clauses stay verbatim** (the header dates them, and CS-6b dates itself
   in-clause). **One prediction is falsified and must be rewritten: Goal 3's
   "byte-identical".** **One prediction held but needs re-tensing: Goal 8's "these stay
   `0.0.12`"**, which now reads as a claim about today's `0.0.15`. Every other prediction
   held as written.
9. **Three present-tense claims to re-tense, not delete** (Low-3): Edge case 24's
   "byte-unchanged", the `TestClient` rows in `## Out of scope` + Edge case 11 (it shipped,
   at `0.0.14`, where the row routed it), and `## Out of scope`'s "The `0.0.13` version
   bump" (it happened, in `fa704722`).
10. **Two documentation-only `.py` fixes, inside the fence, for Worker 1 to route** (not this
    pass's to make): `rest_framework/__init__.py`'s "place 3 is the spec Risks note" (Low-2 —
    place 3 is Decision 12, and Risks is now in the companion), and `rev6 #17`'s missing
    empty-declaration carve-out if the spec text is aligned to `sets.py` (Low-1).
11. **`Escalated: public-surface count.** `### Decision 5` and DoD item 8 both call
    `SerializerMutation` "the one net-new public symbol"; the shipped soft-export surface is
    **seven** names. Decision 5 belongs to a sibling cohort, so this is surfaced rather than
    graded. Resolution paths: (a) Worker 1 updates Decision 5 to enumerate all seven, noting
    which arrived with which rev6 item and which with the hook-context hardening; or (b) the
    maintainer decides the extra six are a later card's surface and Decision 5 stays scoped
    to `SerializerMutation` with a pointer. The **contract** (lazy, guarded, out of `__all__`)
    holds for all seven either way.
12. **Two test edits to route to a builder pass, not to absorb into Slice 2** (both are
    missing *assertions*, not missing behavior): Medium-4, the G2 "no `.only(...)`" clause
    pinned by a non-distinguishing fresh query; and Low-4, the unpinned tolerate arm of the
    H3 request-actor guard. Both sit inside the cycle's `.py` fence.
13. **Test-placement observation, no edit required unless Worker 1 wants one.** The
    `## Test plan` names `test_products_api.py` as the live tier. The products lane is fully
    there (19 rows), but the entire rev6 live surface and **both** golden-SDL rows — including
    the *products* one — live in `examples/fakeshop/test_query/test_library_api.py`. Still
    the live tier, still `/graphql/`; the spec is simply silent about it.

### Review outcome

`review-accepted`.

This pass has no `built` predecessor and hands directly to Worker 1. **No row graded
DROPPED**, and no finding names *production* code that must change: all four High findings
and all three of Medium-1/2/3 are spec-text defects whose remedy is Worker 1's alone. The two
remaining findings (Medium-4, Low-4) are missing test assertions over already-correct
behavior; they are inside the cycle's `.py` fence and are routed to Worker 1 to dispatch, not
held against this pass. `revision-needed` would be the wrong signal here — there is no build
to revise.

The four High findings are escalated above with their resolution paths.
