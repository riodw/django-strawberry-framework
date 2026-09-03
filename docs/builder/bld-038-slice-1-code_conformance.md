# Build: Slice 1 — code conformance

Spec reference: `docs/SPECS/spec-038-form_mutations-0_0_12.md` (164,240 bytes post-Slice-0; 14 `### Decision` headings, 5 slices / 14 nested sub-checks, 16 `## Edge cases` bullets, 7 `## Test plan` rows, 8 `## Definition of done` items, 5 `## Implementation plan` rows, 7 `## Out of scope` bullets, 6 `## Non-goals` bullets — every one of those figures measured by an AST/regex pass over the file while writing this line)
Rationale companion: `docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md` (55,325 bytes)
Build plan: `docs/builder/build-038-form_mutations-0_0_12.md`
Status: final-accepted

## Artifact shape: a grading slice

This slice produces **verdicts, not spec edits**. Slice 2 owns the spec rewrite; every stale
statement found here is routed forward under `### Notes for Worker 1 (spec reconciliation)`.
Where a verdict proves a gap, the Plan section below carries the implementation plan and the
status is `planned` so Worker 0 can dispatch Worker 2 to build it and Worker 3 to review it.
Worker 1 wrote no source and no test in this pass (`docs/builder/BUILD.md`
`### Isolation is non-waivable`).

## Grading method

### The HEAD reference (the load-bearing discipline)

`forms/inputs.py`, `forms/resolvers.py` and `forms/sets.py` carry a concurrent session's
uncommitted hunks (the plan's `## Baseline-dirty out-of-scope files`). Every verdict below is
stated against `HEAD`, read out of a scratch path **outside** the repository:

```shell
SCR=/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/6e52bfa0-603e-41a8-bc13-31de50adedd9/scratchpad
mkdir -p $SCR/head
for p in django_strawberry_framework/forms/{__init__,converter,inputs,sets,resolvers}.py \
         django_strawberry_framework/mutations/{sets,fields,inputs,resolvers,permissions,operations}.py \
         django_strawberry_framework/{registry,__init__}.py \
         django_strawberry_framework/types/{finalizer,base}.py \
         django_strawberry_framework/utils/{inputs,converters,errors,write_values,write_transaction}.py; do
  git show HEAD:$p > $SCR/head/$(echo $p | sed 's#/#__#g')
done
```

All 20 paths resolved (line counts recorded: `forms/converter.py` 292, `forms/inputs.py` 757,
`forms/sets.py` 1007, `forms/resolvers.py` 618, `mutations/sets.py` 1606,
`mutations/resolvers.py` 1334, `mutations/fields.py` 309, `registry.py` 610,
`types/base.py` 1954). Test-tree and example-tree reads used `git show HEAD:<path>` directly.
No `git stash`, `git checkout`, `git restore`, or `git worktree` was run.

**The uncommitted guards named in the plan's working-tree-only list are graded as ABSENT.**
Independently confirmed: the `keyword` import and the `str.isidentifier` /
`keyword.iskeyword` field-name guard, the two out-of-vocabulary `operation_kind` raises, the
guarded `dict(form_class.base_fields)` read, the typed `BaseException` wrap around the
`get_form_fields` hook, and `materialize_relation_id_container` appear in the working-tree
`review_inspect.py` overviews and **not** in the `HEAD` copies. None entered a verdict.

### Ship-time attribution

The `038` ship commit is **`731fecd8`** ("Finish spec-038-form_mutations-0_0_12.md"). Whether a
divergence is a ship-time deviation or a later card's deliberate change was settled by reading
the symbol at `731fecd8` (and at `731fecd8^` where the question was "did `038` create this"),
never by inference from a symbol's current shape.

### Populations printed for every sweep

- Package-wide symbol locations: `git grep -n "^def <name>(" HEAD -- 'django_strawberry_framework/**.py'`.
- Test/example sweep: a `uv run python - <<'PY'` heredoc over the `git ls-tree -r --name-only HEAD`
  listing filtered to `tests/` and `examples/fakeshop/` — **population 300 `.py` files,
  7,228,146 bytes read from `HEAD`** — counting *occurrences* per file, not matching lines.
  zsh word-splitting was avoided throughout (no bare `for f in $FILES`).

### Focused run

`uv run pytest tests/forms -n0 --no-cov -q` → **256 passed** in 1.96s (working tree; 187 `def
test_` definitions across the four modules — `test_converter.py` 17, `test_inputs.py` 57,
`test_sets.py` 53, `test_resolvers.py` 60 — so 69 of the 256 node ids come from
`parametrize`). No `--cov*` flag was used in any command this pass.

### Shared-environment versions, as read (never from memory)

`uv pip list` → `django 6.1`, `strawberry-graphql 0.324.0`, `django-filter 26.1`;
`uv run python -c "import sys; print(sys.version)"` → `3.14.2`. The supported floor, copied
verbatim from `docs/builder/BUILD.md` `## Floor verification`, is Django **5.2.16** on Python
**3.10** with strawberry-graphql **0.316.0**. **The shared `.venv` is not the floor** — no
verdict below rests on a floor claim, and the one gap that needs one declares its scope in
`### Floor verification`.

### `review_inspect.py` run record

Every invocation passed `--output-dir docs/shadow` as the process requires. Output is
gitignored, read-only, and its line numbers are not cited anywhere in this artifact.

| File | Run | Result |
| --- | --- | --- |
| `django_strawberry_framework/forms/sets.py` | `uv run python scripts/review_inspect.py django_strawberry_framework/forms/sets.py --output-dir docs/shadow` | exit 0; overview + stripped emitted |
| `django_strawberry_framework/forms/inputs.py` | same form | exit 0; 17 symbols, 7 control-flow hotspots, 4 repeated literals, 1 Django/ORM marker (`model._meta.get_field(name)`) |
| `django_strawberry_framework/forms/resolvers.py` | same form | exit 0; overview + stripped emitted |
| `django_strawberry_framework/forms/converter.py` | same form | exit 0; 8 symbols, 1 hotspot, 0 repeated literals, 0 Django/ORM markers |
| `django_strawberry_framework/mutations/fields.py` | same form | exit 0; overview + stripped emitted |

The helper reads the **working tree**, so for the three baseline-dirty files its overview is a
superset of `HEAD`. It was used to enumerate symbols and hotspots; every property assertion
below was then checked in the `HEAD` copy. That divergence is itself evidence: `forms/inputs.py`'s
overview lists an `import keyword` and a `Django / ORM markers` entry that the `HEAD` copy does
not carry, which is how the working-tree-only list was independently confirmed.

`### When to run the helper during build` requires the helper for any existing `.py` of 150+
source lines the plan adds logic to. No skips were taken.

---

## Plan (Worker 1)

### Verdict summary

**Every figure in this table was measured by a parser over this artifact's own verdict tables
after they were written, not asserted while writing them** — it classifies each row by its
verdict cell and prints the total, so the reader can re-derive it. The unit is a **table row**:
a Decision with several independently-gradable clauses (D5's three axes, D7's thirteen) gets one
row per clause, which is why the row count exceeds the section-item counts in the header.

| Verdict | Rows |
| --- | --- |
| `BUILT-CONFORMANT` (incl. gate-owned / estimate / half-qualified) | 96 |
| `SPEC-STALE` | 21 |
| `BUILT-CONFORMANT` **+** `SPEC-STALE` (contract built, one statement stale) | 9 |
| `DROPPED` (incl. "in part") | 8 |
| `DEVIATED` | 6 |
| **Total verdict rows** | **140** |

Collapsed to the four legal categories by primary verdict: **105 `BUILT-CONFORMANT`** (96 clean
+ 9 whose contract is built and whose only defect is a stale sentence Slice 2 rewrites), **21
`SPEC-STALE`**, **8 `DROPPED`**, **6 `DEVIATED`**. The 8 `DROPPED` rows collapse to **4 distinct
gaps** (GAP-1…GAP-4), because three of them are the same contract asserted in several spec
homes — the `## Test plan` row, the `## Edge cases` bullet, the Decision, and the
`## Definition of done` item each counted where they sit, which is the point of grading all
five homes separately.

`SPEC-STALE` = a later card deliberately changed it; **the code stands and Slice 2 rewrites the
spec.** `DEVIATED` = the two sides disagreed at ship time, or two spec homes disagree with each
other; the "loser" column in each row says which side changes. `DROPPED` = a spec contract with
no counterpart in source or the test trees.

**All four `DROPPED` verdicts are missing test rows, not missing behavior.** In each case the
production code exists at `HEAD` and the contract the spec states is un-pinned — twice in the
specific shape `fail_under = 100` structurally cannot see (an `or` disjunct that is never the
deciding operand under test, `docs/builder/BUILD.md` `### Fail-open shapes`). That is why this
slice sets `planned` rather than `final-accepted`.

### Verdict table — the 14 Decisions

| Contract (heading + quoted phrase) | Verdict | Citation that settles it |
| --- | --- | --- |
| D1 — "The spec file lives at **`docs/SPECS/spec-038-form_mutations-0_0_12.md`**" | BUILT-CONFORMANT | file present at that path; `check_spec_glossary.py` OK 31 terms (plan pre-flight step 6) |
| D2 — "This card adds **no** field to `FieldError`" | BUILT-CONFORMANT | `mutations/inputs.py::FieldError` — no member added by `038`; `731fecd8` diff touches no `FieldError` field |
| D2 — "reuses, **byte-identical**, the contracts `spec-036` **froze**" (envelope) | SPEC-STALE | `mutations/inputs.py::FieldError` #"The type is ADDITIVE, not" — `codes` / `path` were added by a later card, so the envelope is no longer byte-identical to `0.0.11`'s. `038`'s own normative clause still holds; the "frozen / byte-identical" framing does not |
| D2 — "does not re-open the `036` model-column input generator" | BUILT-CONFORMANT | `mutations/inputs.py` retains `build_mutation_input` for model columns; the form generator is `forms/inputs.py::build_form_inputs` |
| D3 — "**not** graphene's `MutationOptions` / `__init_subclass_with_meta__`" | BUILT-CONFORMANT | `git grep -c "__init_subclass_with_meta__\|MutationOptions\|ClientIDMutation" HEAD -- 'django_strawberry_framework/**'` → **0 files**; both bases take a nested `class Meta` (`forms/sets.py::DjangoModelFormMutation._validate_meta`, `forms/sets.py::DjangoFormMutation._validate_meta`) |
| D4 — "`converter.py` … `inputs.py` … `sets.py` … `resolvers.py`" | BUILT-CONFORMANT | `git ls-tree HEAD django_strawberry_framework/forms/` → exactly `__init__.py`, `converter.py`, `inputs.py`, `resolvers.py`, `sets.py` |
| D4 — "new `tests/forms/` mirroring the source modules" | BUILT-CONFORMANT | `tests/forms/{__init__,test_converter,test_inputs,test_resolvers,test_sets}.py` |
| D5 — "Two net-new public symbols, re-exported from `__init__.py` and added to `__all__`" | BUILT-CONFORMANT | `django_strawberry_framework/__init__.py` #"from .forms import DjangoFormMutation, DjangoModelFormMutation"; both present in the `__all__` tuple |
| D5 axis 1 — "generalized to 'a concrete member of the mutation/form family'" | BUILT-CONFORMANT | `mutations/fields.py::_has_mutation_protocol` — `_mutation_meta` + callable `resolve_sync` / `resolve_async` / `input_type_name` + non-`None` `input_module_path`; no `issubclass(DjangoMutation)`, no form-base import |
| D5 axis 1 — "(a shared marker base or a duck-typed `_mutation_meta` + `_payload_type_name` check)" | DEVIATED (spec loses) | `mutations/fields.py::_validate_mutation_target` #"It does NOT require ``_input_class`` / ``_payload_type_name``" — `_payload_type_name` is a *bind* output and the field is constructed at import, so requiring it would be wrong. The parenthetical named an unbuildable option; the shipped protocol set is correct |
| D5 axis 2 — "`_resolve` calls `mutation_cls.resolve_sync` / `resolve_async`" | BUILT-CONFORMANT | `mutations/fields.py` #"return mutation_cls.resolve_sync(info, **call_kwargs)" |
| D5 axis 3 — "consults `mutation_cls.input_type_name(meta)` + `input_module_path`" | BUILT-CONFORMANT | `mutations/fields.py::_synthesized_mutation_signature` #"data_ann = _lazy_ref(mutation_cls.input_type_name(meta), mutation_cls.input_module_path)"; `def _input_type_name` absent package-wide |
| D6 — "`DjangoModelFormMutation` subclasses `DjangoMutation`, overriding `_resolve_model`" | BUILT-CONFORMANT | `forms/sets.py::DjangoModelFormMutation._resolve_model` → `resolve_meta_model(meta, key="form_class", meta_attr="_meta")` |
| D6 — the four hardwired places refactored into seams | BUILT-CONFORMANT | `mutations/sets.py::DjangoMutation._validate_meta` (relocated body), `build_input`, `input_type_name` / `input_module_path`, `resolve_sync` / `resolve_async`; model defaults intact per `tests/mutations/test_sets.py::test_model_flavor_input_seams_produce_today_defaults` and `::test_model_flavor_resolve_seams_delegate_to_resolver_entry_points` |
| D6 — "It is a lighter base (**its own metaclass**)" | SPEC-STALE | at `731fecd8` `forms/sets.py` carried `class DjangoFormMutationMetaclass(type)`; at `HEAD` it is `DjangoFormMutationMetaclass = make_meta_validating_metaclass(register_form_mutation, …)` from `mutations/sets.py`. Shared factory, disjoint ledger — the contract holds, the mechanism changed |
| D6 — "**exactly two fields**: `ok: Boolean!` and `errors: [FieldError!]!`" | BUILT-CONFORMANT | `mutations/inputs.py::build_payload_type` takes `object_type: type \| None`; `forms/sets.py::bind_form_mutations` passes `resolve_object_type=lambda …: None`; `tests/forms/test_sets.py::test_plain_form_bind_materializes_input_and_ok_errors_payload` |
| D6 — "`perform_mutate(self, form, info) -> None`: the default calls `form.save()` when the form exposes it" | BUILT-CONFORMANT | `forms/sets.py::DjangoFormMutation.perform_mutate`; `tests/forms/test_sets.py::test_plain_form_default_perform_mutate_calls_form_save` |
| D6 — "**`Meta.return_field_name` is not adopted**" | BUILT-CONFORMANT | `git grep -c "return_field_name" HEAD -- 'django_strawberry_framework/**'` → **0 files** |
| D7 — the converter enumeration (`CharField`…`MultipleChoiceField → list[str]`) | SPEC-STALE | `forms/converter.py` `_SCALAR_FORM_FIELDS` has **12 rows**, one of which — `forms.JSONField: _scalar_converter(strawberry.scalars.JSON)` — the enumeration omits. Added post-ship by `efb7bda5` ("fix(forms): map JSON fields to JSON"), which is a descendant of `731fecd8` |
| D7 — "`NullBooleanField` → `bool \| None`" | SPEC-STALE | `forms/converter.py::form_field_required` is a three-case rule (exact `NullBooleanField` forced optional; a **subclass** keeps declared requiredness → non-null `bool`; a **non-null-column-backed** field keeps `required=True`). Post-ship (`5737ddda`, "keep null booleans optional on every path"). Pinned by `tests/forms/test_converter.py::test_null_boolean_subclass_with_real_validation_stays_required` + `::test_form_field_required_column_backed_variations` |
| D7 — relation id basis: `column.related_model` / `field.queryset.model` | BUILT-CONFORMANT | `forms/inputs.py::_field_triple_and_spec` (column path) and `::_model_less_relation_annotation` (`field.queryset`) |
| D7 — "reuse the read-side converters" for a column-backed `ModelForm` field | BUILT-CONFORMANT | `forms/inputs.py::_field_triple_and_spec` → `model_column_input_annotation(column, …)`; `tests/forms/test_inputs.py::test_choices_modelform_field_resolves_to_read_side_enum` |
| D7 — "the registry's **fallthrough (unregistered) default RAISES**" / no catch-all | BUILT-CONFORMANT | `forms/converter.py::_bare_form_field` returns `MRO_CONTINUE` for a subclass; `::_unsupported_form_field` is the `fallthrough_error_factory`; `tests/forms/test_converter.py::test_unknown_custom_field_subclass_raises` |
| D7 — "`forms/inputs.py` **retains** … an `(input_attr, graphql_name) → (form_field_name, kind)` metadata record" | SPEC-STALE | the record type is single-sited on `utils/inputs.py::InputFieldSpec` (`target_name` = form field name; plus `related_model`, `source`, `nested_specs`); the four kind constants are defined in `utils/inputs.py` and re-exported by `forms/converter.py`. `forms/inputs.py::_field_triple_and_spec` builds them. Contract intact, ownership moved |
| D7 — "runs its **own** `relation_single` / `relation_multi` decoder" | SPEC-STALE | `forms/resolvers.py::_decode_form_relation_single` is the *form coloring* of the shared `utils/write_values.py::decode_visible_relation` spine (`skip=` + `project=` callbacks); `decode_field_handlers` / `decode_provided_fields` own the kind dispatch. The visibility-on-every-branch contract is intact; "its own decoder" is not |
| D7 — visibility on **both** the Relay and raw-pk branch | BUILT-CONFORMANT | `forms/resolvers.py::_decode_form_relation_single` → `decode_visible_relation`; `tests/forms/test_resolvers.py::test_relation_visibility_raw_pk_single_hidden_rejected` and `::test_relation_visibility_raw_pk_multi_hidden_rejected` |
| D7 — "`obj.serializable_value(field.to_field_name)` when set, else `obj.pk`" | BUILT-CONFORMANT | `forms/resolvers.py::_to_form_key_value`; `tests/forms/test_resolvers.py::test_to_field_name_relation_validates_by_target_field`; live in `examples/fakeshop/test_query/test_library_api.py::test_create_shelf_via_form_visible_branch_resolves_by_to_field_name_and_writes` |
| D7 — "Two generated inputs: create (`field.required`) + partial", non-model extra keeps `field.required` | BUILT-CONFORMANT | `forms/inputs.py::build_form_input_class` #"required = False if (is_partial and column is not None) else field_required"; `tests/forms/test_inputs.py::test_partial_input_model_backed_optional_extra_field_still_required` |
| D7 — identity is "**`(form_class, operation kind, frozenset(effective field names)`)**" | SPEC-STALE | `forms/sets.py::_cached_build_form_input` keys on a **4-tuple**: that triple plus `forms/sets.py::_form_input_hook_identity(mutation_cls)` (`None` unless the mutation overrides `get_form_fields`). Absent at `731fecd8`; post-ship. Conceptual identity unchanged |
| D7 — canonical vs shape-derived names, dedupe, finalize-time collision raise | BUILT-CONFORMANT | `forms/inputs.py::form_input_type_name` → `utils/inputs.py::name_set_input_type_name`; `tests/forms/test_inputs.py::test_narrowed_shapes_get_distinct_names`, `::test_identical_shape_dedupes_via_ledger`, `::test_two_forms_sharing_name_always_collide` |
| D7 — `Meta.fields` / `Meta.exclude` normalized + fail-loud against `base_fields`; empty set raises | BUILT-CONFORMANT | `forms/inputs.py::resolve_effective_form_fields`; `tests/forms/test_inputs.py::test_meta_fields_rejects_bare_string` / `::test_meta_fields_rejects_duplicates` / `::test_meta_fields_rejects_unknown_name` / `::test_empty_effective_field_set_raises` |
| D7 — "A `create` narrowing that drops a required form field is rejected"; waiver on `get_form_kwargs` / `get_form` | BUILT-CONFORMANT | `forms/inputs.py::guard_create_required_fields`; waiver via `forms/sets.py::_form_kwargs_overridden`; `tests/forms/test_inputs.py::test_create_guard_rejects_dropping_required_field_via_fields` / `::test_create_guard_waiver_does_not_raise` |
| D7 — "`update` is exempt" | SPEC-STALE | `forms/inputs.py::guard_partial_required_column_less_fields` rejects an update narrowing that drops a **required column-less** field (`model_to_dict` cannot reconstruct it); dispatched from `forms/sets.py::_cached_build_form_input` #"if operation_kind == PARTIAL". Absent at `731fecd8`; post-ship. There are **two** narrowing guards keyed on one waiver |
| D7 — materialization into the `forms` input namespace + the `data:`-ref seam | BUILT-CONFORMANT | `forms/inputs.py` #"INPUTS_MODULE_PATH: str = \"django_strawberry_framework.forms.inputs\""; `forms/inputs.py::materialize_form_input_class`; `tests/forms/test_inputs.py::test_materialized_input_is_module_global` |
| D7 — "Schema-time field discovery reads `form_class.base_fields`, never an instance" + `get_form_fields(cls)` | BUILT-CONFORMANT | `forms/inputs.py::get_form_fields` #"return dict(form_class.base_fields)"; `forms/sets.py::_default_mutation_get_form_fields`; `tests/forms/test_inputs.py::test_get_form_fields_does_not_instantiate_kwarg_requiring_form` |
| D8 — "**Ordering correction — authorize runs BEFORE the relation decode (post-ship security fix).** … The step numbers below reflect the original draft sequence" | DEVIATED (spec loses) | the shipped order is `locate → authorize → decode → construct/validate → write → re-fetch → return`, single-sited in `mutations/resolvers.py::run_write_pipeline_sync` #"authorize BEFORE decode"; `forms/resolvers.py` module docstring states the same. The spec leaves its seven steps in the **superseded** order behind a chronology the reader must apply — `docs/builder/BUILD.md` `## Spec rationale extraction` forbids exactly that shape. Slice 2 renumbers |
| D8 step 1 — decode to form-field-keyed `provided_data` + separate `provided_files`; `UNSET` stripped; enum unwrap | BUILT-CONFORMANT | `forms/resolvers.py::_decode_form_data`; `tests/forms/test_resolvers.py::test_decode_split_relation_lands_under_form_key_not_id_attr`, `::test_decode_split_upload_lands_in_files_never_data`, `::test_decode_unwraps_choice_enum_to_raw_value` |
| D8 step 2 — locate through `get_queryset`; malformed `id:` is an `id`-keyed `FieldError` before lookup; `id:` is `strawberry.ID` | BUILT-CONFORMANT | `mutations/resolvers.py::run_write_pipeline_sync` #"node_id, id_error = coerce_lookup_id"; `mutations/fields.py` #"arguments.append((\"id\", strawberry.ID))"; `tests/forms/test_resolvers.py::test_update_malformed_id_is_field_error_before_lookup`, `::test_update_hidden_row_is_not_found_no_existence_leak` |
| D8 step 3 — authorize via inherited `check_permission`; denial is a top-level `GraphQLError` | BUILT-CONFORMANT | `mutations/resolvers.py::authorize_or_raise`; `tests/forms/test_resolvers.py::test_write_auth_denial_raises_top_level_error`, `::test_write_auth_runs_before_relation_visibility_decode` |
| D8 step 4 — "`get_form_kwargs(self, info, *, data, files, instance=None) -> dict`" default `{"data":…, "files":…}` (+ `instance` when non-`None`) | BUILT-CONFORMANT | `forms/sets.py::_default_get_form_kwargs` → `mutations/sets.py::construction_kwargs`; `tests/forms/test_resolvers.py::test_get_form_kwargs_override_injects_constructor_kwarg` |
| D8 step 4 — "A `get_form(self, info, *, data, files, instance=None)` hook … is the coarser override for full control" | **DROPPED** (test) | `forms/sets.py::_default_get_form` exists and is called by `forms/resolvers.py::_bound_form_or_field_errors` #"form = holder.get_form(info, data=form_data, files=provided_files, instance=instance)", so the default path is exercised. But `def get_form(` occurs **0 times** across the 300-file / 7,228,146-byte `tests/` + `examples/fakeshop/` population at `HEAD`: **nothing anywhere overrides it.** See GAP-1 |
| D8 step 4 — "an override … to scope a `ModelChoiceField.queryset` **without changing the generated input shape**" | **DROPPED** (test) | no `get_form_kwargs` override in any tier scopes a queryset — the 19 `get_form_kwargs` occurrences live in 6 files and the two overrides in `tests/forms/test_resolvers.py` inject a kwarg and waive the guard. The live `queryset=None`-then-`__init__` idiom in `examples/fakeshop/apps/library/forms.py::ShelfRelationsForm` is the *form's own* `__init__`, not the hook. See GAP-4 |
| D8 step 4 — "`data = {**model_to_dict(instance, fields=<the form's non-file fields>), **provided_data}`" | SPEC-STALE | `forms/resolvers.py::_reconstruct_partial_data` now has **three** reconstruction shapes, not one: `model_to_dict` for scalars and a `to_field_name`-less FK, `_to_form_key_value` per member for a real forward M2M, and `_to_form_key_value` for a `ModelChoiceField` **with** `to_field_name` set. Pinned by `tests/forms/test_resolvers.py::test_partial_update_preserves_unprovided_m2m_with_to_field_name` and `::test_partial_update_preserves_unprovided_fk_with_to_field_name`. Also: reconstruction reads the form's **full** declared set, not the narrowed input (`::test_narrowed_update_preserves_excluded_required_fk_and_validates_constraint`) |
| D8 step 4 — "an omitted file field is preserved by the bound `form_class(instance=…)` via its `initial`, never re-supplied and never cleared" | **DROPPED** (test) | implemented by omission: `forms/resolvers.py::_reconstruct_partial_data` #"if name in provided_data or isinstance(form_field, forms.FileField):". `initial` occurs **0 times** in `tests/forms/`, and every form-backed file mutation in every tier is a **create** (`products::CreateItemWithFileViaForm`, `scalars::CreateMediaSpecimenImageViaForm`, `tests/forms/test_resolvers.py::test_decode_split_upload_lands_in_files_never_data`). Nothing pins the skip. See GAP-2 |
| D8 step 4 — required extra (non-model) field stays required on update | BUILT-CONFORMANT | `forms/inputs.py::build_form_input_class` (column-`None` keeps `field_required`); `tests/forms/test_resolvers.py::test_required_extra_field_omitted_on_update_is_coercion_error` |
| D8 step 4 — `form.errors.as_data()` through the reused `036` mapper; `NON_FIELD_ERRORS` → `"__all__"` | BUILT-CONFORMANT | `forms/resolvers.py::_form_errors_to_field_errors`; `tests/forms/test_resolvers.py::test_non_field_constraint_failure_keys_to_all_sentinel` |
| D8 step 5 — write via `form.save()` / `perform_mutate`, **wrapped by `save_or_field_errors`** | BUILT-CONFORMANT | `forms/resolvers.py::_modelform_write_step` #"write_error = save_or_field_errors(form.save)" and `::_plain_form_write_step`; `tests/forms/test_resolvers.py::test_modelform_save_integrity_error_maps_to_envelope`, `::test_plain_form_perform_mutate_integrity_error_maps_to_envelope` |
| D8 step 6 — re-fetch by pk + optimizer plan | BUILT-CONFORMANT | `mutations/resolvers.py::refetch_optimized`; `tests/forms/test_resolvers.py::test_modelform_refetch_keeps_select_related_and_suppresses_only` |
| D8 step 7 — return the `<Name>Payload` | BUILT-CONFORMANT | `mutations/resolvers.py::run_write_pipeline_sync` tail → `build_payload`; `tests/forms/test_resolvers.py::test_modelform_create_writes_and_returns_node` |
| D8 — "Helper reuse … `_`-prefixed in `mutations/resolvers.py` **today**", promoted "underscore-dropped in place" | DEVIATED (spec loses) + SPEC-STALE | **ship-time error:** `payload_object_slot` was already public in `mutations/inputs.py` at `731fecd8^` — it was never `_`-prefixed and never in `mutations/resolvers.py`, so the sentence was false on its own date (and contradicts the spec's own `## Current state` bullet, which places it in `mutations/inputs.py`). **Later drift:** of the nine named helpers, **seven** are in `mutations/resolvers.py` at `HEAD` (`locate_instance`, `coerce_lookup_id`, `authorize_or_raise`, `refetch_optimized`, `build_payload`, `not_found_error`, `save_or_field_errors`) and **two** moved (`validation_error_to_field_errors` → `utils/errors.py`, `raw_choice_value` → `utils/write_values.py`), all measured with `git grep -n "^def <name>(" HEAD` |
| D8 — "Slice 3 **picks one** and names it" (underscore-drop vs a neutral `mutations/_pipeline.py`) | DEVIATED (spec loses) | an unresolved build instruction left in a shipped spec. Slice 3 picked underscore-drop-in-place; no `mutations/_pipeline.py` exists. The Decision must state where the helpers live |
| D8 — one `transaction.atomic()`; async runs the body in one `sync_to_async(thread_sensitive=True)` | BUILT-CONFORMANT + SPEC-STALE | `forms/resolvers.py` #"resolve_form_sync, resolve_form_async = make_resolver_entries(_run_form_pipeline_sync)"; `tests/forms/test_resolvers.py::test_async_form_create_runs_under_one_sync_to_async`. **Stale addition:** `mutations/resolvers.py::run_write_pipeline_sync` now also opens a managed-transaction gate on one pinned write alias (`open_write_pipeline`, `pipeline_alias_guard`, `check_deadline`) — post-`038` (`0.0.14` atomicity / `spec-047` deadline) |
| D8 — `SyncMisuseError` on an `async def get_queryset` from the sync pipeline | BUILT-CONFORMANT | `forms/resolvers.py` #"_FORM_ASYNC_RECOURSE = sync_pipeline_recourse(\"form mutation\")"; `tests/forms/test_resolvers.py::test_sync_create_meeting_async_get_queryset_raises_sync_misuse` |
| D9 — G2 re-fetch: keep `select_related` / `prefetch_related`, suppress `.only(...)`, **by pk without the visibility filter** | BUILT-CONFORMANT | `mutations/resolvers.py::refetch_optimized` #"by pk, WITHOUT the visibility ``get_queryset`` filter" and its `apply_connection_optimization` call; `tests/forms/test_resolvers.py::test_modelform_refetch_keeps_select_related_and_suppresses_only` |
| D10 — `DjangoModelFormMutation` requires `operation ∈ {create, update}`; plain base **rejects any** `Meta.operation`; `"form"` sentinel | BUILT-CONFORMANT | `forms/sets.py::DjangoModelFormMutation._validate_meta` → `require_non_delete_operation`; `forms/sets.py::DjangoFormMutation._validate_meta` #"if hasattr(meta, \"operation\"):"; `forms/inputs.py` #"FORM: str = \"form\""; `tests/forms/test_sets.py::test_modelform_delete_operation_rejected`, `::test_plain_base_rejects_any_operation`, `::test_plain_base_rejects_inherited_meta_operation`, `::test_plain_form_input_dedupes_via_form_sentinel` |
| D11 — `ModelForm` flavor inherits `DjangoModelPermission` unchanged | BUILT-CONFORMANT | `forms/sets.py::DjangoModelFormMutation._validate_meta` → `model_backed_permission_and_lock`; `tests/forms/test_sets.py::test_modelform_unset_permission_classes_keeps_model_permission_default` |
| D11 — plain form: "an *unset* `permission_classes` on a plain form denies" | BUILT-CONFORMANT | `forms/sets.py::DjangoFormMutation._validate_meta` #"unset_default=(DenyAll,)"; `tests/forms/test_sets.py::test_plain_form_unset_permission_classes_defaults_to_deny_all`; live `examples/fakeshop/test_query/test_products_api.py::test_submit_ping_plain_form_denied_by_default_top_level_error` |
| D11 — silent on an explicitly-set model-permission class | SPEC-STALE | `forms/sets.py::DjangoFormMutation._validate_meta` #"which requires a model to resolve the write" raises at class creation for any `DjangoModelPermission` subclass entry. Absent at `731fecd8`; post-ship. `tests/forms/test_sets.py::test_plain_form_rejects_model_permission_at_class_creation` |
| D12 — "Slice 4 adds `examples/fakeshop/apps/products/forms.py` … and a small plain `Form`" | BUILT-CONFORMANT | `products/forms.py` ships `ItemModelForm` (with `clean_name`), `ContactForm`, `PingForm`, `StampedItemModelForm`, `ItemFileModelForm`; `products/schema.py` exposes 6 form mutations |
| D12 — products as **the** live home ("this spec narrows it to the existing `test_products_api.py`") | SPEC-STALE | the live form surface is now three apps: products (6 mutations), `examples/fakeshop/apps/library/schema.py` (`CreateShelfViaForm`, `UpdateBookViaForm`, `CreateBranchWithShelf`, `CreateBranchPair` — 4), `examples/fakeshop/apps/scalars/schema.py` (`CreateMediaSpecimenImageViaForm` — 1). Faithful when written; a false description of the live surface now |
| D13 — `ModelForm` binds through `bind_mutations` with `build_input` routed through the seam | BUILT-CONFORMANT | `forms/sets.py::DjangoModelFormMutation.build_input`; `tests/forms/test_sets.py::test_modelform_bind_materializes_form_input_into_forms_namespace` |
| D13 — plain form gets its own registry (`register_form_mutation` / `iter_form_mutations`), clear, and `bind_form_mutations()` wired into `types/finalizer.py` phase 2.5 | BUILT-CONFORMANT | `forms/sets.py` #"_form_mutation_declaration_registry = make_declaration_registry(\"DjangoFormMutation\")"; `types/finalizer.py` #"from ..forms.sets import bind_form_mutations" then `bind_form_mutations()` between `bind_mutations()` and `_bind_filtersets()`; `tests/forms/test_sets.py::test_plain_form_registers_in_disjoint_form_registry` |
| D13 — "**`registry.clear()` co-clears THREE form rows**" | SPEC-STALE | all three clears exist and are all reached, but **not by a hard-coded row in `registry.py`**: `grep -c "clear_form" ` over the 610-line `HEAD` `registry.py` → **0**. Each owner announces itself — `forms/inputs.py::clear_form_input_namespace` (`owner="forms.input_namespace"`, `before_bind=True`), `forms/sets.py::clear_form_mutation_registry` (`owner="forms.declarations"`), `forms/sets.py::clear_form_shape_build_cache` (`owner="forms.shape_cache"`) — and `registry.py` #"for clear in iter_subsystem_clears():" consumes them. Mechanism changed, contract intact |
| D13 — "The two ledgers stay separate; the registry *mechanics* are shared … `make_declaration_registry(label)`" | BUILT-CONFORMANT | `make_declaration_registry` present at `731fecd8` in both `mutations/sets.py` and `forms/sets.py` and still so at `HEAD`, now with a third consumer (`auth/mutations.py`) the spec could not have named |
| D13 — "**No change to `DEFERRED_META_KEYS` / `ALLOWED_META_KEYS`**" | BUILT-CONFORMANT | `grep -c "form_class"` over the 1954-line `HEAD` `types/base.py` → **0**; `DEFERRED_META_KEYS` is `{"aggregate_class", "fields_class", "search_fields"}` — no form key. (`ALLOWED_META_KEYS` has grown since, from unrelated cards) |
| D14 — the `0.0.12` cut lands in this card | BUILT-CONFORMANT | `731fecd8` touched `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `docs/GLOSSARY.md`, `uv.lock`, `CHANGELOG.md`; `CHANGELOG.md` #"## [0.0.12] - 2026-06-23". `__version__` is now `0.0.15` — **not** a staleness finding (the release this card closed happened) |

### Verdict table — `## Slice checklist` (5 slices, 14 nested sub-checks)

| Contract | Verdict | Citation |
| --- | --- | --- |
| Slice 1 header — "form-field → Strawberry input mapping + the form-derived input generator" | BUILT-CONFORMANT | `forms/converter.py` + `forms/inputs.py` at `HEAD` |
| S1 sub-check — `forms/converter.py` registry + "Record, per generated input field, the `input_attr → (form_field_name, kind)` reverse map" | SPEC-STALE | enumeration omits `JSONField` (see D7); the record itself is `utils/inputs.py::InputFieldSpec`, not a `forms/converter.py`-owned record — `forms/converter.py` #"This module owns only the kind constants" |
| S1 sub-check — `forms/inputs.py`: two `@strawberry.input` classes, shape identity, canonical/shape-derived names, `utils/inputs.py` core reuse, narrowing fail-loud | BUILT-CONFORMANT (identity tuple SPEC-STALE, see D7) | `forms/inputs.py::build_form_inputs`; `make_input_namespace` wraps `materialize_generated_input_class` |
| S1 sub-check — "Package coverage: `tests/forms/test_converter.py` … And `tests/forms/test_inputs.py`" | BUILT-CONFORMANT (row placement stale) | 17 + 57 test functions. The `ModelChoiceField` id mapping, the `base_fields` discovery, and the reverse map are pinned in `test_inputs.py`, not `test_converter.py` — correctly, since `forms/converter.py::convert_form_field` returns `annotation=None` for relation/file kinds by design |
| Slice 2 header — the two bases + `Meta` validation + the phase-2.5 bind | BUILT-CONFORMANT | `forms/sets.py` |
| S2 sub-check — `mutations/sets.py`: "refactor the class-creation validation into an overridable `DjangoMutation._validate_meta(meta)` … (the model base keeps today's `_validate_mutation_meta` body)" | BUILT-CONFORMANT | `mutations/sets.py::DjangoMutation._validate_meta` #"the 0.0.11 body relocated verbatim from the former module-level"; `tests/mutations/test_sets.py::test_validate_meta_is_the_relocated_classmethod_seam`. `_validate_mutation_meta` was already gone as a symbol at `731fecd8` (2 docstring/comment mentions), so the parenthetical is a build-time instruction, not a live contract |
| S2 sub-check — `forms/sets.py` bases; `ModelForm` checked first on the plain base; check runs **before** `_resolve_model`; `operation` split; "The form allowed-key set adds `form_class` and drops `model` / `input_class` / `partial_input_class`" | DEVIATED (checklist loses) + SPEC-STALE | at `731fecd8` there were already **two** disjoint sets — `_ALLOWED_MODELFORM_META_KEYS` and `_ALLOWED_PLAIN_FORM_META_KEYS` — so the checklist's single sentence was an under-description on its own date; Decision 10 states the split correctly, and the two homes disagree. **Stale addition:** at `HEAD` `_ALLOWED_MODELFORM_META_KEYS = MODEL_BACKED_WRITE_META_KEYS \| {form_class}` = `{fields, exclude, permission_classes, operation, select_for_update, form_class}` while `_ALLOWED_PLAIN_FORM_META_KEYS = COMMON_WRITE_META_KEYS \| {form_class}` = `{fields, exclude, permission_classes, form_class}` — `select_for_update` is a post-`038` (`0.0.14`) row-locking key the plain flavor additionally rejects |
| S2 sub-check — "No change to `DEFERRED_META_KEYS` / `ALLOWED_META_KEYS`" | BUILT-CONFORMANT | see D13 row |
| S2 sub-check — "Package coverage: `tests/forms/test_sets.py` — the `Meta` validation matrix … registration, finalizer binding (both paths), the no-registered-primary-type error … and the model-flavor seam defaults unchanged" | BUILT-CONFORMANT | 53 test functions incl. `::test_modelform_no_registered_primary_type_raises_at_finalize`; model-flavor defaults in `tests/mutations/test_sets.py::test_model_flavor_input_seams_produce_today_defaults` / `::test_model_flavor_resolve_seams_delegate_to_resolver_entry_points` |
| Slice 3 header — resolver pipeline + `DjangoMutationField` exposure | BUILT-CONFORMANT | `forms/resolvers.py`, `mutations/fields.py` |
| S3 sub-check — the sync + async pipeline (decode / locate / authorize / construct / validate / write / re-fetch / return), one `transaction.atomic()`, one `sync_to_async` | BUILT-CONFORMANT + SPEC-STALE | `forms/resolvers.py::_run_form_pipeline_sync` parameterizes the shared `mutations/resolvers.py::run_write_pipeline_sync` (with `pipeline_write_phase` from `utils/write_transaction.py`); the sub-check's own step order is the superseded one (see D8) |
| S3 sub-check — `mutations/fields.py` three axes, "All three keep today's behavior for a `DjangoMutation` target" | BUILT-CONFORMANT | `tests/mutations/test_fields.py::test_generalized_target_accepts_modelform_and_plain_form_family`, `::test_model_flavor_dispatch_unchanged` |
| S3 sub-check — "Package coverage: `tests/forms/test_resolvers.py` — … the `plain-form ok + errors payload + perform_mutate default/override`, the visibility-scoped `update` locate, write-auth denial vs success, sync + async, and the G2 plan-shape" | BUILT-CONFORMANT | 60 test functions; every named row present |
| Slice 4 header — the products live form surface | BUILT-CONFORMANT | `products/forms.py`, `products/schema.py` |
| S4 sub-check — `products/forms.py` (new) + `products/schema.py` gains a `DjangoModelFormMutation` (create + update) and a `DjangoFormMutation`; "If `Item` … needs a file column for the multipart test, add the minimal `FileField` + migration here" | BUILT-CONFORMANT | `examples/fakeshop/apps/products/schema.py::CreateItemViaForm` / `::UpdateItemViaForm` / `::SubmitContact` (+ 3 more); `examples/fakeshop/apps/products/forms.py::ItemFileModelForm` over the `Item.attachment` column |
| S4 sub-check — `test_products_api.py` live rows | BUILT-CONFORMANT | **18** form-flavor live tests of 115 total in the file, covering every clause the sub-check names (this sub-check does **not** name the write-time `IntegrityError`; that clause lives only in `## Test plan` and DoD 5 — see GAP-3) |
| Slice 5 header — docs + the `0.0.12` cut + card wrap | BUILT-CONFORMANT | `CHANGELOG.md` `## [0.0.12]`, `docs/GLOSSARY.md` rows |
| S5 sub-check — "**Version files to `0.0.12`**: `pyproject.toml`, `__version__`, `tests/base/test_init.py::test_version`, the `docs/GLOSSARY.md` package-version line, and `uv.lock` if it carries the package version" | BUILT-CONFORMANT + SPEC-STALE | all five landed in `731fecd8` (`pyproject.toml` #"version = \"0.0.12\"" at that commit, `uv.lock` bumped). At `HEAD` the quintet is a **triplet**: `pyproject.toml` has no `version` literal (`[tool.hatch.version]` derives it) and `uv.lock` carries `source = { editable = "." }` with no version key |
| S5 sub-check — GLOSSARY promotion + README / GOAL / TODAY / TREE / CHANGELOG / KANBAN | BUILT-CONFORMANT | `docs/GLOSSARY.md` — both entries `shipped (`0.0.12`)` in the Index, both in Public exports and the Mutations browse row, and the `DjangoFormMutation` body rewritten to the model-less-sibling shape ("it is **not** a `DjangoMutation` subclass"); `TODAY.md` #"as of `0.0.12` products exposes form-validated mutations"; `docs/TREE.md` `forms/` summary lines present; `GOAL.md` criterion 6 records the `0.0.12` ship; `README.md` #"`0.0.12` — form-based mutations" |

### Verdict table — `## Edge cases and constraints` (16 bullets)

| Contract | Verdict | Citation |
| --- | --- | --- |
| Form-only fields (no model column) | BUILT-CONFORMANT | `forms/inputs.py::_model_column_for` returns `None`; `tests/forms/test_inputs.py::test_plain_form_only_field_included_in_input` |
| `ModelForm` `clean()` / `NON_FIELD_ERRORS` → `"__all__"` | BUILT-CONFORMANT | `tests/forms/test_resolvers.py::test_non_field_constraint_failure_keys_to_all_sentinel`; live `examples/fakeshop/test_query/test_products_api.py::test_create_item_via_form_unique_constraint_envelope_uses_all_sentinel` |
| `update` partial-update preservation — scalar, FK, M2M | BUILT-CONFORMANT | `tests/forms/test_resolvers.py::test_partial_update_preserves_unprovided_fk_and_validates_constraint`, `::test_partial_update_preserves_unprovided_m2m`; live `examples/fakeshop/test_query/test_products_api.py::test_update_item_via_form_partial_update_preserves_category_and_description` |
| … "and any file field (omitted → kept via the bound form's `initial`)" | **DROPPED** (test) | see the D8-step-4 file row and GAP-2 |
| File / image live in this card; **clearing** out of scope | BUILT-CONFORMANT (upload half) | live `examples/fakeshop/test_query/test_products_api.py::test_create_item_with_file_via_form_multipart_upload_over_http` and `examples/fakeshop/test_query/test_uploads_api.py::test_multipart_create_media_specimen_image_via_form_over_http`; no `<field>Clear` input exists, so the deferral holds. The **preserve** half is GAP-2 |
| A `ModelForm` whose `Meta.fields` omits an editable column | BUILT-CONFORMANT | the input derives from `base_fields` (`forms/inputs.py::get_form_fields`); `tests/forms/test_inputs.py::test_fields_narrowing_omits_dropped_field` |
| A `ChoiceField` over model `choices` → the read-side enum; decode unwraps to the raw value | BUILT-CONFORMANT | `tests/forms/test_inputs.py::test_choices_modelform_field_resolves_to_read_side_enum`; `tests/forms/test_resolvers.py::test_decode_unwraps_choice_enum_to_raw_value` |
| Relation visibility is not delegated to the form's queryset | BUILT-CONFORMANT | `forms/resolvers.py::_decode_form_relation_single`; `tests/forms/test_resolvers.py::test_relation_visibility_relay_single_hidden_rejected` + the raw-pk / multi siblings; live `examples/fakeshop/test_query/test_products_api.py::test_create_item_via_form_relation_id_for_hidden_category_is_field_error` |
| A `ModelForm` on the plain base → rejected naming `DjangoModelFormMutation`, checked **first** | BUILT-CONFORMANT | `forms/sets.py::DjangoFormMutation._validate_meta` #"is a \nforms.ModelForm; use DjangoModelFormMutation"; `tests/forms/test_sets.py::test_plain_base_with_modelform_raises_naming_modelform_base` |
| A required extra (non-model) `ModelForm` field on `update` keeps `field.required` | BUILT-CONFORMANT | `tests/forms/test_resolvers.py::test_required_extra_field_omitted_on_update_is_coercion_error` |
| A relation field with `to_field_name` | BUILT-CONFORMANT | `forms/resolvers.py::_to_form_key_value`; single decode pinned package + live. The multi arm shares the same projection function (`_decode_form_relation_multi` maps `_decode_form_relation_single`), so the load-bearing property is single-sited and covered |
| A form whose `__init__` requires constructor kwargs | BUILT-CONFORMANT | `tests/forms/test_inputs.py::test_get_form_fields_does_not_instantiate_kwarg_requiring_form`; live `examples/fakeshop/test_query/test_products_api.py::test_create_stamped_item_via_form_get_form_kwargs_injects_user` |
| A `create` narrowing that drops a required form field | BUILT-CONFORMANT + SPEC-STALE | `forms/inputs.py::guard_create_required_fields`. **Stale:** this bullet is silent on the second, partial-side guard (`guard_partial_required_column_less_fields`). It does **not** contain the "`update` is exempt" clause — see the D-13 grade below, which corrects Worker 0 on that point |
| Write-time `IntegrityError` → the envelope, never a top-level `GraphQLError` | BUILT-CONFORMANT (package) | `tests/forms/test_resolvers.py::test_modelform_save_integrity_error_maps_to_envelope`, `::test_plain_form_perform_mutate_integrity_error_maps_to_envelope`. The live half is GAP-3 |
| Two distinct generated form inputs colliding on one GraphQL name → always raises | BUILT-CONFORMANT | `tests/forms/test_inputs.py::test_two_forms_sharing_name_always_collide`, `::test_distinct_shapes_colliding_on_one_name_raise` |
| "Plain-form write authorization … a plain `DjangoFormMutation` **requires** an explicit `Meta.permission_classes`" | DEVIATED (bullet loses) + SPEC-STALE | at `HEAD` an unset `permission_classes` does not fail configuration — it defaults to `(DenyAll,)` (`forms/sets.py::DjangoFormMutation._validate_meta` #"unset_default=(DenyAll,)"). Decision 11's deny-by-default wording is right; this bullet's "requires" is a weaker, inaccurate restatement, and two spec homes disagree. Also silent on the `DjangoModelPermission` rejection |
| "No `DjangoType` `Meta` key added. `DEFERRED_META_KEYS` / `ALLOWED_META_KEYS` are byte-unchanged" | BUILT-CONFORMANT | 0 `form_class` occurrences in `types/base.py`; `DEFERRED_META_KEYS` carries no form key |

### Verdict table — `## Test plan` (7 rows)

| Row | Verdict | Citation |
| --- | --- | --- |
| **Live, over `/graphql/`** (Slice 4, `test_products_api.py`) | **DROPPED in part** + SPEC-STALE | 17 of the row's 18 named clauses are pinned by the file's 18 form-flavor live tests (happy paths, `clean_<field>` keying, `"__all__"`, `categoryId`-through-form, partial preservation + one-field collision, non-colliding partial, anonymous / missing-perm denial, permitted success, visibility-scoped update, hidden-`Category` `FieldError`, raw multipart upload, `get_form_kwargs`-injects-`user`, plain-form success + failure). The **"Write-time `IntegrityError`"** clause has no live counterpart for the `ModelForm` flavor anywhere — `IntegrityError` occurs 4× in `test_products_api.py`, all in model-driven rows — see GAP-3. **Stale:** the live surface is now three apps (see D12) |
| `test_converter.py` row | BUILT-CONFORMANT (placement stale) | 17 tests; the id-mapping / reverse-map / `base_fields`-discovery clauses are pinned in `test_inputs.py` by design. The fail-loud trio (bare `Field` → `str`, `EmailField` via MRO, `CustomField` raises) is all present |
| `test_inputs.py` row | BUILT-CONFORMANT | 57 tests; every named clause present incl. the always-collide case and the empty-effective-set raise |
| `test_sets.py` row | BUILT-CONFORMANT | 53 tests; every named clause present incl. `"form"`-sentinel dedupe and the no-primary error |
| `test_resolvers.py` row | **DROPPED in part** | 60 tests cover every clause except three: the **`get_form` hook** (GAP-1), the **`get_form_kwargs` queryset-scoping / input-shape-unchanged** clause (GAP-4), and **"omitted file preserved via the bound form's `initial`"** (GAP-2) |
| `tests/mutations/test_fields.py` (extend) row | BUILT-CONFORMANT | `::test_generalized_target_accepts_modelform_and_plain_form_family` constructs a `DjangoMutationField` over both flavors without raising |
| **Cross-cutting — no regression** | BUILT-CONFORMANT (gate-owned) | `uv run pytest tests/forms -n0 --no-cov` → 256 passed. The full-sweep / lint / coverage-gate confirmation is the final gate's, not this slice's |

### Verdict table — `## Definition of done` (items 1-8)

| Item | Verdict | Citation |
| --- | --- | --- |
| 1 — spec + `-terms.csv` exist; `check_spec_glossary.py` reports OK | BUILT-CONFORMANT | `docs/SPECS/appx/spec-038-form_mutations-0_0_12-terms.csv`; `OK: 31 terms` (plan pre-flight step 6, re-confirmed by Slice 0) |
| 2 — converter + both generated inputs + shape identity + guards | SPEC-STALE | contract built; three statements stale — the converter enumeration (no `JSONField`), the 3-tuple shape identity, and the create-guard's silence on the partial guard (see D7 rows) |
| 3 — `mutations/sets.py` seams + `forms/sets.py` bases + the `Meta` matrix + `DEFERRED_META_KEYS` unchanged + both exports | BUILT-CONFORMANT + SPEC-STALE | every clause verified above. Stale: the allowed-key set is two disjoint sets, one of which now also carries `select_for_update` |
| 4 — `forms/resolvers.py` pipeline + `mutations/fields.py` three axes | BUILT-CONFORMANT + SPEC-STALE | every clause verified above. Stale: the decode/pipeline is a shared substrate (`utils/write_values.py`, `mutations/resolvers.py::run_write_pipeline_sync`), the promoted-helper locations moved, and the step order is the superseded one |
| 5 — the products live row set | **DROPPED in part** + SPEC-STALE | 11 of 12 named clauses pinned in `test_products_api.py`. **"a write-time `IntegrityError` returning the `FieldError` envelope (P1)"** has no live counterpart for the `ModelForm` flavor, at ship time or now — verified at `731fecd8` (its `test_products_api.py` carried 3 `IntegrityError` mentions, all model-driven). The nearest live coverage is the plain-form `perform_mutate` case in `examples/fakeshop/test_query/test_library_api.py::test_create_branch_pair_rolls_back_first_write_when_second_conflicts`. See GAP-3 |
| 6 — cross-cutting no regression | BUILT-CONFORMANT (gate-owned) | as the Test-plan cross-cutting row |
| 7 — GLOSSARY / README / GOAL / TODAY / TREE / CHANGELOG / KANBAN | BUILT-CONFORMANT | see the S5 doc sub-check row |
| 8 — the `0.0.12` bump + both symbols in `__all__` | BUILT-CONFORMANT + SPEC-STALE | `731fecd8` touched all five version surfaces; `__all__` carries both symbols at `HEAD`. Stale: the quintet is now a triplet |

### Verdict table — `## Implementation plan` cells (5 slices × 2 cells)

| Cell | Verdict | Citation |
| --- | --- | --- |
| 1 / Files touched — `forms/converter.py`, `forms/inputs.py`, `forms/__init__.py` (all new) | BUILT-CONFORMANT | all three exist; every named symbol (`convert_form_field`, `get_form_fields()`, the two generated inputs) resolves |
| 1 / New-changed tests — "(~36 …)" | BUILT-CONFORMANT (estimate) | actual 74 test functions across the two modules; a planning estimate, not a contract |
| 2 / Files touched — `forms/sets.py`, `mutations/sets.py`, `mutations/inputs.py` "`build_payload_type(object_type=None)`", `types/finalizer.py`, "`registry.py` (THREE form co-clear rows)", "`mutations/fields.py` (TODO-anchor only …; Slice 3 deletes it)", `__init__.py` | SPEC-STALE (3 clauses) | (a) `mutations/inputs.py::build_payload_type` signature is `(mutation_name, *, object_type: type \| None, object_slot: str \| None = None)` — keyword-required, no `None` default; (b) `registry.py` has 0 `clear_form` occurrences (see D13); (c) the `TODO(spec-038` anchor is discharged — `git grep -rn 'TODO(spec-038'` returns nothing in source or tests, and `def _input_type_name` is gone package-wide |
| 2 / New-changed tests — `tests/forms/test_sets.py` + `tests/mutations/test_sets.py` extend | BUILT-CONFORMANT | both files carry the named rows |
| 3 / Files touched — `forms/resolvers.py`; the `mutations/resolvers.py` nine-helper promotion; `forms/sets.py` `resolve_*` / hooks / `guard_required` waiver / `_input_field_specs`; `mutations/fields.py` three axes + delete the `_input_type_name` twin; the docstring `::OldName` sweep in `mutations/sets.py` / `mutations/permissions.py` / `relay.py` | SPEC-STALE (helper list) | every named symbol resolves — `forms/sets.py::_cached_build_form_input` returns `(input_cls, field_specs)`, `_build_and_stash_form_input` stashes `_input_field_specs`, `_form_kwargs_overridden` is the waiver, `mutations/fields.py` #"takes_id = mutation_cls._mutation_meta.operation != \"form\"", and the docstring refs survive (`relay.py` #"``locate_instance``'s ``get(pk=...)``", `mutations/permissions.py` #"the resolver's ``authorize_or_raise``"). Stale only in the helper-location list (7 remain, 2 moved, `payload_object_slot` never there) |
| 3 / New-changed tests — `tests/forms/test_resolvers.py` + `tests/mutations/test_fields.py` extend + the `::OldName` sweep in `tests/mutations/test_resolvers.py` / `test_permissions.py` / `test_products_api.py` | BUILT-CONFORMANT (rename sweep) / DROPPED in part (see the Test-plan row) | promoted-helper name occurrences at `HEAD`: `tests/mutations/test_resolvers.py` 16, `tests/mutations/test_permissions.py` 1, `test_products_api.py` 0 (a later reword; not a contract) |
| 4 / Files touched — `products/forms.py` (new, "+ a minimal file column/migration if needed"), `products/schema.py`, `test_products_api.py` | BUILT-CONFORMANT | all three; `Item.attachment` is the file column |
| 4 / New-changed tests | BUILT-CONFORMANT | 18 form-flavor live tests |
| 5 / Files touched — the doc list + version files | BUILT-CONFORMANT | `731fecd8` `--stat` |
| 5 / New-changed tests — "`test_version` → `0.0.12`" | BUILT-CONFORMANT | pinned at `0.0.12` by `731fecd8`; now `0.0.15` (three later cuts) |

### Verdict table — `## Out of scope` (7) and `## Non-goals` (6)

| Item | Verdict | Citation |
| --- | --- | --- |
| Out of scope — "DRF serializer mutations … `0.0.13` (`TODO-ALPHA-039-0.0.13`)" | SPEC-STALE | shipped: `django_strawberry_framework/rest_framework/`, `examples/fakeshop/apps/products/schema.py::CreateItemViaSerializer` / `::UpdateItemViaSerializer` / `::CreateItemViaRenamedSerializer`, `tests/rest_framework/`. The card is no longer `TODO-ALPHA` |
| Out of scope — "Auth mutations … `0.0.13` (`TODO-ALPHA-040-0.0.13`)" | SPEC-STALE | shipped: `django_strawberry_framework/auth/mutations.py` (a third `make_declaration_registry` consumer), `examples/fakeshop/test_query/test_auth_api.py` |
| Out of scope — "The ergonomic `TestClient` / `AsyncTestClient` helper — `TODO-ALPHA-043-0.0.14`" | SPEC-STALE | shipped: `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/testing/__init__.py`, a `conf.py` setting, and `examples/fakeshop/test_query/test_client_api.py`. This is the clearest third-kind item: an out-of-scope deferral that has since landed |
| Out of scope — "Form `delete` — not shipped" | BUILT-CONFORMANT | `forms/sets.py` #"require_non_delete_operation(\"DjangoModelFormMutation\", name, meta)"; `tests/forms/test_sets.py::test_modelform_delete_operation_rejected` |
| Out of scope — "Field-level read gates (`FieldSet` / Per-field permission hooks) — `0.1.1`" | BUILT-CONFORMANT | `DEFERRED_META_KEYS` still carries `fields_class`; no per-field gate shipped |
| Out of scope — "Clearing a stored file/image on update … a future `<field>Clear: Boolean`" | BUILT-CONFORMANT | no `Clear`-suffixed input or `ClearableFileInput` path anywhere in `django_strawberry_framework/forms/`; the deferral holds |
| Out of scope — "A new `DjangoType` `Meta` key or settings key" | BUILT-CONFORMANT | 0 `form_class` in `types/base.py`; no form settings key in `conf.py` |
| Non-goal — "DRF serializer mutations and auth mutations" | SPEC-STALE | same evidence as the two Out-of-scope rows |
| Non-goal — "Changing the `036` model-driven generator or the `FieldError` envelope" | BUILT-CONFORMANT (for this card) + SPEC-STALE (framing) | see the two D2 rows |
| Non-goal — "The `TestClient` *ergonomic* helper, NOT file-field correctness" | SPEC-STALE | the helper shipped; the file-field-correctness claim this card owns holds (upload half live, preserve half GAP-2) |
| Non-goal — "Form `delete`" | BUILT-CONFORMANT | as above |
| Non-goal — "`Meta.return_field_name`" | BUILT-CONFORMANT | 0 occurrences package-wide |
| Non-goal — "A new `DjangoType` `Meta` key or settings key" | BUILT-CONFORMANT | as above |

### Independent grade of Worker 0's `## Worker-0 verification pass`

Worker 0's findings are observations, not instructions. Each is graded below with its own
evidence; a finding that does not hold still matters, because it says the dispatcher's model of
the code is off.

**Built-and-conformant list.** Independently re-derived and **confirmed in full** — D4 module
layout (5 `forms/` files, 4 mirrored test modules), D5 public surface, D5 axes 1/3 (with the
`_payload_type_name` correction recorded as its own DEVIATED row above), D5 axis 2, D7
fail-loud dispatch, D7 `to_field_name`, D7/D8 raw-pk relation visibility on both cardinalities,
D10/D13 `operation` split + bind wiring, D13 model-less payload from one builder, D13 no
`DjangoType` `Meta` key, D6 `return_field_name` not adopted, D12/DoD-5 live surface (with the
GAP-3 exception below), D14 version cut, and the discharged `TODO(spec-038` anchors. One
addition Worker 0 did not name: `make_declaration_registry`'s third consumer is
`auth/mutations.py`, which Worker 0 did name — confirmed.

| Finding | Grade | Evidence |
| --- | --- | --- |
| **D-1** — 3 of 9 promoted helpers moved | **CORRECTED** | The *substance* is right and I confirm it: `validation_error_to_field_errors` → `utils/errors.py:231`, `raw_choice_value` → `utils/write_values.py:79`, `payload_object_slot` → `mutations/inputs.py:882`. **Two corrections.** (1) Worker 0 writes "**Six** remain in `mutations/resolvers.py`" and then lists **seven** (`locate_instance`, `coerce_lookup_id`, `authorize_or_raise`, `refetch_optimized`, `build_payload`, `not_found_error`, `save_or_field_errors`); I measured seven with `git grep -n "^def <name>(" HEAD`. The count is wrong, the list is right. (2) `payload_object_slot` is **not** a later move: it was already public in `mutations/inputs.py` at `731fecd8^`, i.e. **before** `038`. So Decision 8's sentence was false on its own date, which makes this a ship-time DEVIATED finding as well as a staleness one — a different grading case from the one Worker 0 assigned ("third grading case") |
| **D-2** — the form pipeline is a shared runner, not a per-flavor body | **CONFIRMED** | `forms/resolvers.py` imports `make_resolver_entries`, `run_write_pipeline_sync`, `save_or_field_errors` from `mutations/resolvers.py` and `pipeline_write_phase` from `utils/write_transaction.py`; `::_run_form_pipeline_sync` supplies only `decode_step` / `write_step` |
| **D-3** — the decode primitives moved to `utils/write_values.py` | **CONFIRMED** | `forms/resolvers.py` imports `decode_field_handlers`, `decode_provided_fields`, `decode_visible_relation`, `relation_field_error` from `utils/write_values.py`. (`materialize_relation_id_container`, which the plan lists here, is **working-tree only** — absent at `HEAD`. Worker 0's own working-tree-only list says so; the D-3 body naming it is an inconsistency in the plan, not in the code) |
| **D-4** — the reverse-map record is single-sited on `utils/inputs.py::InputFieldSpec` | **CONFIRMED** | `forms/converter.py` re-exports `SCALAR` / `RELATION_SINGLE` / `RELATION_MULTI` / `FILE` from `utils/inputs.py` and states #"This module owns only the kind constants"; `forms/inputs.py::_field_triple_and_spec` builds `InputFieldSpec(input_attr=…, graphql_name=…, target_name=name, kind=…, related_model=…)` |
| **D-5** — the converter rides a shared dispatch skeleton | **CONFIRMED** | `forms/converter.py` imports `MRO_CONTINUE`, `convert_with_mro`, `finish_field_conversion`, `make_kind_converter`, `make_scalar_converter` from `utils/converters.py`; `FormFieldConversion(FieldConversionBase)` |
| **D-6** — `registry.clear()` no longer carries three hard-coded form rows | **CONFIRMED** | `grep -c "clear_form"` over the 610-line `HEAD` `registry.py` → 0; three `register_subsystem_clear` owners (`forms.input_namespace` with `before_bind=True`, `forms.declarations`, `forms.shape_cache`) consumed by `registry.py` #"for clear in iter_subsystem_clears():" |
| **D-7** — the converter table carries a `JSONField` row the spec omits | **CONFIRMED, and the history question answered** | `efb7bda5` ("fix(forms): map JSON fields to JSON") is a **descendant** of the ship commit `731fecd8` (`git log --oneline -S 'forms.JSONField' -- …/forms/converter.py` names only that commit, and `731fecd8` is the file's oldest commit). So it is a later addition, third grading case — not an unrecorded ship-time inclusion |
| **D-8** — `NullBooleanField` requiredness is a three-case rule | **CONFIRMED** | `forms/converter.py::form_field_required`; the three cases are pinned by `tests/forms/test_converter.py::test_null_boolean_field_is_optional_bool`, `::test_null_boolean_subclass_with_real_validation_stays_required`, `::test_form_field_required_column_backed_variations`. Post-ship (`5737ddda`, "keep null booleans optional on every path") |
| **D-9** — Decision 8 narrates its own history and leaves its steps in the superseded order | **CONFIRMED** | the shipped order is single-sited in `mutations/resolvers.py::run_write_pipeline_sync`; the spec's steps 1-3 read decode → locate → authorize. Highest-value Slice-2 edit; **and note the renumber is not free**: `## Edge cases` and `## Definition of done` both cite "step 2" / "(Decision 8 step 2)" style anchors, and `docs/GLOSSARY.md` and `docs/README.md` cite the Decision by heading |
| **D-10** — the deliberative layer has never been extracted | **DISCHARGED by Slice 0, and its counts re-measured** | Slice 0 moved 14 `Justification:` + 14 `Alternatives` blocks (25 rejected alternatives), the Risks body, D6's cleaned-data-echo rejection, and the inline Revision history; spec 185,851 → 164,240 bytes. I re-measured the post-move spec at **164,240 bytes** and **14** `### Decision` headings. What Slice 0 could **not** discharge is D-9's renumber, which is why D-9 survives as the live item |
| **D-11** — the live surface is wider than Decision 12 / DoD 5 | **CONFIRMED** | `library/schema.py` carries 4 form mutations (`CreateShelfViaForm`, `UpdateBookViaForm`, `CreateBranchWithShelf`, `CreateBranchPair`) over `library/forms.py`'s `ShelfRelationsForm` / `BookGenresModelForm` / `BranchWithShelfForm` / `BranchPairForm`; `scalars/schema.py` carries `CreateMediaSpecimenImageViaForm`. Products carries 6 |
| **D-12** — DoD 5's live `IntegrityError` row is in `test_library_api.py`, not `test_products_api.py` | **CONFIRMED, and the grading question Worker 0 left open is answered: an unpinned live contract, not a relocated row** | The library row (`::test_create_branch_pair_rolls_back_first_write_when_second_conflicts`) exercises the **plain-form `perform_mutate`** path, not the `ModelForm` `form.save()` path DoD 5 names, and it was added long after ship. At `731fecd8` the ship commit's own `test_products_api.py` carried **no** form-flavor `IntegrityError` row, so nothing was relocated — the live half was never built. The `ModelForm` half exists only as a `mock.patch(forms.ModelForm, "save")` package test. See GAP-3 |
| **D-13** — a partial-side required-column-less-field guard exists that the spec says does not | **PARTIALLY REFUTED** | The guard is real and post-ship: `forms/inputs.py::guard_partial_required_column_less_fields`, absent at `731fecd8`, dispatched from `forms/sets.py::_cached_build_form_input` #"if operation_kind == PARTIAL", pinned by `tests/forms/test_inputs.py::test_partial_guard_rejects_dropping_required_column_less_field` and `::test_partial_guard_allows_dropping_model_backed_required_field`. **But Worker 0's second claim does not hold:** it says "Decision 7's create-guard paragraph states '`update` is exempt', **and the `## Edge cases` create-narrowing bullet repeats it**. Both are false at `HEAD`." Only Decision 7 carries that clause; the `## Edge cases` bullet ("A `create` narrowing that drops a required form field (P2)") does **not** contain it — its text ends at the `get_form_kwargs` / `get_form` waiver. So there is **one** false sentence to fix, not two, and the Edge-case bullet's defect is a different one: silence about the second guard |
| **D-14** — an input-attribute collision guard | **CONFIRMED** | `forms/inputs.py::_guard_input_attr_collisions` → `utils/inputs.py::iter_input_field_collisions`, raising on the first collision; two arms (input-attr and camelCase `graphql_name`), the second of which Worker 0 does not mention. Absent at `731fecd8`. Pinned by `tests/forms/test_inputs.py::test_relation_id_attr_collision_is_fail_loud` and `::test_camel_case_graphql_name_collision_is_fail_loud` |
| **D-15** — a plain-`Form` relation field whose `queryset` is `None` is rejected | **CONFIRMED** | `forms/inputs.py::_model_less_relation_annotation` #"whose queryset is None at class definition"; absent at `731fecd8`; pinned by `tests/forms/test_inputs.py::test_model_choice_field_with_none_queryset_is_fail_loud` |
| **D-16** — two allowed-key sets, the plain one additionally dropping `select_for_update` | **CORRECTED** | The `HEAD` reading is right, but the attribution is not: **both** sets already existed at `731fecd8` (`_ALLOWED_MODELFORM_META_KEYS` = `{form_class, operation, fields, exclude, permission_classes}`, `_ALLOWED_PLAIN_FORM_META_KEYS` = `{form_class, fields, exclude, permission_classes}`), with a ship-time comment spelling the split. So the two-set shape is the **shipped** contract and the Slice-2 checklist's one sentence was already an under-description on its own date — a ship-time DEVIATED finding against the checklist, with Decision 10 as the correct home. Only `select_for_update` is the post-`038` (`0.0.14`) addition Worker 0 describes |
| **D-17** — the plain base rejects a `DjangoModelPermission` entry | **CONFIRMED** | `forms/sets.py::DjangoFormMutation._validate_meta` #"which requires a model to resolve the write"; absent at `731fecd8`; `tests/forms/test_sets.py::test_plain_form_rejects_model_permission_at_class_creation`. Also confirmed: `unset_default=(DenyAll,)` |
| **D-18** — the runtime input-shape cache key is a 4-tuple | **CONFIRMED** | `forms/sets.py::_cached_build_form_input` #"_form_input_hook_identity(mutation_cls)" as the fourth element; `_form_input_hook_identity` absent at `731fecd8`; pinned by `tests/forms/test_sets.py::test_modelform_get_form_fields_hook_controls_input_basis` and `::test_plain_form_get_form_fields_hook_controls_input_basis` |
| **D-19** — the metaclass, bind, and resolver seams are shared factories; `mutations/operations.py` owns the operation vocabulary | **CONFIRMED** | at `731fecd8` `forms/sets.py` declared `class DjangoFormMutationMetaclass(type)`; `make_meta_validating_metaclass`, `resolver_seams`, `bind_write_declarations` and `django_strawberry_framework/mutations/operations.py` are all absent at that commit and present at `HEAD`. `bind_form_mutations()`'s whole body is one `bind_write_declarations(...)` call; both flavors' `resolve_*` come from `resolver_seams(...)`, plain with `with_id=False` matching `mutations/fields.py` #"operation != \"form\"" |
| **Working-tree-only list** (5 hunks) | **CONFIRMED, none adopted** | each verified absent from the `HEAD` copies and present in the working tree (visible in the `review_inspect.py` overviews). No verdict rests on one |
| **"Not a finding": `__version__` is `0.0.15`** | **CONFIRMED** | `__init__.py` #"__version__ = \"0.0.15\""; `tests/base/test_init.py` pins `0.0.15`. Decision 14 and DoD 7-8 describe a cut that happened; no worker "updates" them to `0.0.15` |

### The proven code gaps

Four `DROPPED` verdicts, all in the same class: a spec contract whose **production code exists at
`HEAD`** and whose **assertion does not exist in any test tree**. Two of them are the shape
`docs/builder/BUILD.md` `### Fail-open shapes` names explicitly — an `or` disjunct that is never
the deciding operand under test, so `fail_under = 100` executes the statement, reports it green,
and never asks which operand decided.

#### GAP-1 — the `get_form` construction hook has no test anywhere. **Medium.**

**Contract, in four homes.** Decision 8 step 4 ("A `get_form(self, info, *, data, files,
instance=None)` hook (default: `form_class(**self.get_form_kwargs(...))`) is the coarser override
for full control"); Decision 7's create-guard waiver ("waived only when `get_form_kwargs` /
`get_form` is overridden"); the `## Edge cases` create-narrowing bullet (same waiver); the
`## Test plan` `test_resolvers.py` row ("**the `get_form_kwargs` / `get_form` hook**").

**Evidence.** `def get_form(` occurs **0 times** across the 300-file / 7,228,146-byte
`tests/` + `examples/fakeshop/` population at `HEAD`. The default body
(`forms/sets.py::_default_get_form`) is exercised on every form request via
`forms/resolvers.py::_bound_form_or_field_errors`, so the *default* is covered; the *override*
is not. The consequence is a fail-open expression:

```
forms/sets.py::_form_kwargs_overridden
    return _hook_overridden(cls, base, "get_form_kwargs") or _hook_overridden(cls, base, "get_form")
```

Whenever `get_form_kwargs` is overridden the left operand short-circuits; when neither is, both
are `False`. **No test can make the right operand decide.** Deleting
`or _hook_overridden(cls, base, "get_form")` breaks the documented waiver for a `get_form`-only
consumer and no row fails.

**Fix plan (Worker 2).**

- `tests/forms/test_sets.py` — a row asserting `forms/sets.py::_form_kwargs_overridden` is
  `True` for a mutation overriding **only** `get_form`. *Property pinned:* the second disjunct,
  directly.
- `tests/forms/test_resolvers.py` — a `DjangoFormMutation` (cheapest: no primary type needed)
  overriding **only** `get_form`, declared with a `Meta.fields` narrowing that drops a required
  form field. Assert (a) `finalize_django_types()` does **not** raise — the create-required
  guard is waived through the `get_form` disjunct — and (b) the form the pipeline validates is
  the one the override built (capture the instance, or have the override inject a value the
  default cannot supply and assert it reaches `cleaned_data`). *Property pinned:* that the
  waiver is reachable via `get_form` alone, and that `_bound_form_or_field_errors` calls the
  override rather than reconstructing the default.
- **Failability proof owed** (`scripts/prove_failability.py`): mutation = delete
  `or _hook_overridden(cls, base, "get_form")` from `forms/sets.py::_form_kwargs_overridden`.
  Both new rows must fail. Anchor: the full disjunct line, `grep -c` must print exactly 1 first.

#### GAP-2 — the omitted-file-preserve contract is unpinned at every tier. **Medium.**

**Contract, in five homes.** Decision 8 step 4 ("`files = provided_files` **only** — an omitted
file field is preserved by the bound `form_class(instance=…)` via its `initial`, never
re-supplied and never cleared"); the `## Edge cases` partial-update bullet ("any file field
(omitted → kept via the bound form's `initial`)"); the `## Edge cases` file bullet ("The two
supported file actions are **upload** … and **preserve** (omit it on partial update → kept via
the bound `ModelForm(instance=…)`'s `initial`)"); the `## Test plan` `test_resolvers.py` row
("omitted file preserved via the bound form's `initial`"); DoD 5's partial-update-preservation
clause.

**Evidence.** `initial` occurs **0 times** in `tests/forms/`. Every form-backed file mutation
in every tier is a **create**: `examples/fakeshop/apps/products/schema.py::CreateItemWithFileViaForm`,
`examples/fakeshop/apps/scalars/schema.py::CreateMediaSpecimenImageViaForm`,
`tests/forms/test_resolvers.py::test_decode_split_upload_lands_in_files_never_data`. There is no
`update` over a form declaring a file field anywhere. The behavior is implemented by **omission**:

```
forms/resolvers.py::_reconstruct_partial_data
    if name in provided_data or isinstance(form_field, forms.FileField):
        continue
```

The same fail-open `or` shape as GAP-1: the `continue` is taken constantly via the left operand
(every provided field), so the statement is covered, but **no test makes the `FileField`
disjunct decide.** Delete it and `model_to_dict` supplies the stored *relative path string*
into the bound form's `data=` for a field whose value must come from `files=` — a silent
data-loss path (the stored file cleared or the update rejected) that nothing detects. This is
the higher-risk of the two gaps for exactly that reason.

**Fix plan (Worker 2).**

- `tests/forms/test_resolvers.py` — a `DjangoModelFormMutation` `operation = "update"` over a
  `ModelForm` declaring `scalars.MediaSpecimen`'s `attachment` (or `products.Item.attachment`)
  plus a scalar. Seed a row with a stored file, run a scalar-only update, and assert **three**
  things: the payload has no errors, the stored file name and bytes are unchanged after
  `refresh_from_db()`, and — the distinguishing assertion — the reconstructed `data=` the form
  was bound with contains **no** key for the file field (call
  `forms/resolvers.py::_reconstruct_partial_data` directly, as the existing decode tests call
  `_decode_form_data` directly). Without that third assertion the row can pass while the
  reconstruction wrongly supplies the path, because Django may still leave the stored file
  alone. *Property pinned:* the `FileField` exclusion from the reconstructed bound data — not
  merely that the file survived.
- `examples/fakeshop/apps/products/schema.py` + `examples/fakeshop/test_query/test_products_api.py`
  — an `UpdateItemWithFileViaForm` (`operation = "update"` over the existing
  `examples/fakeshop/apps/products/forms.py::ItemFileModelForm`) and one live row: create with a multipart upload,
  then a `name`-only update over `/graphql/`, asserting the stored `attachment` is byte-identical.
  This is the AGENTS.md live-first obligation for a path reachable by a real query.
- **Test-staleness sweep, mandatory** (`docs/builder/BUILD.md` `### Test staleness a focused run
  cannot see`): adding a field to `examples/fakeshop/apps/products/schema.py::Mutation` changes the live SDL. Before
  finishing, `grep -rn "create_item_with_file_via_form\|createItemWithFileViaForm"` across all
  three test trees plus any SDL/introspection snapshot, and re-pin every mutation-field
  enumeration. Verify with the **full parallel** `uv run pytest --no-cov`, never a focused run.
  No new app and no new schema module is added, so no schema-module list needs syncing — but
  confirm that by grep rather than by assumption.
- **Failability proof owed**: mutation = delete `or isinstance(form_field, forms.FileField)`
  from `forms/resolvers.py::_reconstruct_partial_data`. The package row must fail.

#### GAP-3 — DoD 5's live write-time `IntegrityError` row for the `ModelForm` flavor was never built. **Medium. Carries a contract-level question for the maintainer.**

**Contract, in two homes.** The `## Test plan` live bullet ("**Write-time `IntegrityError`** — a
valid `ModelForm.save()` that loses a concurrent-uniqueness race surfaces the **`FieldError`
envelope**, not a top-level GraphQL error (P1)") and DoD item 5 ("**a write-time `IntegrityError`
returning the `FieldError` envelope** (P1)").

**Evidence.** `test_products_api.py` has 4 `IntegrityError` occurrences, all in model-driven
rows. At the ship commit `731fecd8` its `test_products_api.py` had 3, likewise all model-driven —
so nothing was relocated; the live row was never written. The nearest live coverage is
`examples/fakeshop/test_query/test_library_api.py::test_create_branch_pair_rolls_back_first_write_when_second_conflicts`,
which is the **plain-form `perform_mutate`** path. The `ModelForm` `form.save()` half exists only
as `tests/forms/test_resolvers.py::test_modelform_save_integrity_error_maps_to_envelope`, which
reaches it by `mock.patch.object(forms.ModelForm, "save", side_effect=IntegrityError)` — a mock,
permitted under AGENTS.md only when the real path is impossible.

**It is not impossible.** A real, mock-free live driver exists: a `ModelForm` over `Item` whose
`Meta.fields` omits `category` (so Django's `_get_validation_exclusions` drops `category` and
`validate_unique` skips the `(category, name)` `unique_item_per_category` constraint entirely),
with `category` supplied through a `get_form_kwargs` override — exactly the
`StampedItemModelForm` shape products already carries. A duplicate `name` under the injected
category then reaches a genuine `IntegrityError` at `form.save()`.

**Fix plan (Worker 2).**

- `examples/fakeshop/apps/products/forms.py` + `schema.py` — a `ModelForm` narrowing away a
  unique-constraint co-member plus a mutation injecting it via `get_form_kwargs`.
- `examples/fakeshop/test_query/test_products_api.py` — one `@pytest.mark.django_db(transaction=True)`
  row: seed the colliding row, POST the create, assert HTTP 200, `payload["errors"]` absent at
  the GraphQL top level, the payload's object slot `null`, and exactly one `FieldError` keyed to
  `"__all__"`. *Property pinned:* that a **post-validation** database failure returns the
  envelope. The row must also assert `form.is_valid()` passed — otherwise it silently degrades
  into a duplicate of the existing `validate_constraints` row, which is caught **before** save
  and proves nothing about `save_or_field_errors`. Assert it by checking no field-level error is
  present and the collision is the `"__all__"` sentinel from the save-time mapper's own wording.
- Same SDL / mutation-field-enumeration sweep as GAP-2.
- **Failability proof owed**: mutation = replace `save_or_field_errors(form.save)` with a bare
  `form.save()` in `forms/resolvers.py::_modelform_write_step`. The new live row must fail with a
  top-level error.

**Contract-level question to escalate** (`docs/builder/BUILD.md` `### Contract-level findings are
escalated as maintainer decisions before dispatch`): the alternative is to build no test and let
Slice 2 rewrite DoD 5 / the Test-plan live bullet to cite the existing plain-form library live
row plus the package `ModelForm` row. That turns on whether the package's contract is "the
envelope holds at write time, proven live once per flavor" or "proven live for the `ModelForm`
flavor specifically". **Not a worker's call.** My grade, stated for the record: the test is owed,
because the spec names the `ModelForm` flavor explicitly, the row is drivable without a mock,
and the existing package row's mock is the AGENTS.md exception rather than the rule.

#### GAP-4 — no test drives a `get_form_kwargs` override that scopes a `ModelChoiceField.queryset`. **Low.**

**Contract, in two homes.** Decision 8 step 4 ("or to scope a `ModelChoiceField.queryset`
**without changing the generated input shape** (the input is derived from `get_form_fields()`,
independent of `get_form_kwargs`)") and the `## Test plan` `test_resolvers.py` row ("and one
scoping a `ModelChoiceField.queryset` (input shape unchanged), P2").

**Evidence.** `get_form_kwargs` occurs 19 times in 6 files; the two overrides in
`tests/forms/test_resolvers.py` inject a kwarg (`::test_get_form_kwargs_override_injects_constructor_kwarg`)
and exercise the waiver (`::test_get_form_kwargs_override_waives_create_required_guard`). The
live `queryset=None`-then-assign-in-`__init__` idiom in
`examples/fakeshop/apps/library/forms.py::ShelfRelationsForm` is the **form's own `__init__`**,
not the hook. Graded Low rather than Medium because it shares its code path with the
already-pinned kwarg-injection case; what is genuinely unpinned is the *independence* claim.

**Fix plan (Worker 2).** One `tests/forms/test_resolvers.py` row: two mutations over one form,
one with and one without a `get_form_kwargs` override that narrows the relation field's
`queryset`, asserting (a) both `_input_class` objects have the **same** generated name and the
**same** annotation set — the input shape is independent of the hook — and (b) an id outside the
narrowed queryset is rejected by `form.is_valid()` with a field-keyed `FieldError`, i.e. the
override does take effect at runtime. *Property pinned:* the independence of the generated input
from `get_form_kwargs`, plus the runtime effect — either assertion alone is non-distinguishing.
Fold into GAP-1's cohort (same file, same fixtures).

### Slice-split answer (`docs/builder/BUILD.md` `### Slice splitting`)

**Estimated NEW production boundaries: zero.** No gap adds a guard, cap, rejection path, or
validation branch — every boundary the fix pins already exists at `HEAD`. What the pass adds is
5-7 test rows, one example-app `ModelForm`, and two example-app mutation fields.

**Boundaries newly pinned: three** — `forms/sets.py::_form_kwargs_overridden`'s `get_form`
disjunct, `forms/resolvers.py::_reconstruct_partial_data`'s `FileField` disjunct, and
`forms/resolvers.py::_modelform_write_step`'s `save_or_field_errors` wrap at the live tier. Three
failability-proof loops, well under the five that prompts a written split decision — and I am
writing the answer anyway because the rule says a decided answer beats silence.

**They are one unit, and here is what makes them one.** All four gaps write into the same two
files (`tests/forms/test_resolvers.py` and `examples/fakeshop/test_query/test_products_api.py`),
share the same `products` fixtures, and — decisively — GAP-2 and GAP-3 both add a field to
`examples/fakeshop/apps/products/schema.py::Mutation` and therefore both owe the **same** SDL / mutation-field
enumeration sweep. Splitting them would run that sweep twice and serialize two cohorts on one
shared file, which `### Parallel cohorts under a declared ownership partition` says is not a
partition at all. **Do not split.**

**Ownership partition for the fix:** one cohort. Files it may write:
`tests/forms/test_resolvers.py`, `tests/forms/test_sets.py`,
`examples/fakeshop/apps/products/forms.py`, `examples/fakeshop/apps/products/schema.py`,
`examples/fakeshop/test_query/test_products_api.py`, its own artifact, and
`docs/builder/temp-tests/slice-1/proofs.json`. No package `.py` under
`django_strawberry_framework/` is written — every gap is a missing assertion, not missing
behavior. **If the builder concludes a package `.py` change is needed, that is
plan-vs-implementation drift: set `revision-needed` and route to Worker 1, do not widen the
partition.**

### DRY analysis

**Helper inventory checked.** Refreshed for the **whole package** this pass via
`scripts/review_inspect.py` on the five form-subsystem files plus `git grep -n "^def <name>("
HEAD -- 'django_strawberry_framework/**.py'` for the ten promoted pipeline helpers. Shapes
searched: `guard`, `decode`, `convert`, `validate`, `required`, `reconstruct`, `materialize`,
`clear`, `registry`, and the four kind constants. Relevant candidates found and used as the
basis for the verdicts: `utils/inputs.py` (`InputFieldSpec`, `FieldConversionBase`,
`make_input_namespace`, `make_shape_build_cache`, `resolve_effective_fields`,
`guard_dropped_required`, `iter_input_field_collisions`, `name_set_input_type_name`,
`optional_input_field`, `build_strawberry_input_class`), `utils/converters.py`
(`convert_with_mro`, `finish_field_conversion`, `make_scalar_converter`, `make_kind_converter`,
`MRO_CONTINUE`), `utils/write_values.py` (`decode_visible_relation`, `decode_provided_fields`,
`decode_field_handlers`, `raw_choice_value`, `relation_field_error`), `utils/errors.py`
(`validation_error_to_field_errors`), `utils/write_transaction.py` (`pipeline_write_phase`),
`mutations/sets.py` (`make_declaration_registry`, `make_meta_validating_metaclass`,
`resolver_seams`, `bind_write_declarations`, `build_and_stash_input`, `cached_build_input`,
`construction_kwargs`, `_hook_overridden`, the `*_WRITE_META_KEYS` sets),
`mutations/operations.py` (the operation vocabulary), `mutations/resolvers.py`
(`run_write_pipeline_sync`, `make_resolver_entries` and the seven remaining promoted helpers).

- **Existing patterns reused (by the fix).** Every new test row reuses an existing fixture
  builder rather than a new one: `tests/forms/test_resolvers.py`'s `_build_item_form_schema` /
  `_schema` / `_AllowAll` / `_uniq` helpers and its established habit of calling the private
  pipeline functions (`_decode_form_data`, `_reconstruct_partial_data`) directly for the
  distinguishing assertion. Live rows reuse `_post_graphql`, `seed_data` / `create_users`, and
  the multipart harness `::test_create_item_with_file_via_form_multipart_upload_over_http`
  already establishes. GAP-3's form reuses the `StampedItemModelForm` `get_form_kwargs`-injection
  shape rather than inventing a second one.
- **New helpers justified: none.** No gap needs a new production helper or a new test helper.
  The condition that would change that answer: if the file-preserve row needs a storage-cleanup
  fixture that `tests/forms/test_resolvers.py` does not already have, extract **one** fixture
  and note it — do not copy `test_uploads_api.py`'s.
- **Duplication risk avoided.** The naive fix duplicates the existing package
  `test_modelform_save_integrity_error_maps_to_envelope` at the live tier by re-mocking
  `form.save`; the plan forbids that and requires the real narrowed-constraint driver instead.
  The second risk is a second `ModelForm` over `Item` with a file column when
  `examples/fakeshop/apps/products/forms.py::ItemFileModelForm` already exists — GAP-2's live row reuses it and adds
  only the `update` mutation.

### Implementation steps (for Worker 2)

Ordered so the cheapest, package-tier, no-SDL-change work lands and is provable first.

1. **GAP-1, package tier.** Add the `_form_kwargs_overridden` row to `tests/forms/test_sets.py`
   and the `get_form`-only override row to `tests/forms/test_resolvers.py`. Run
   `uv run pytest tests/forms -n0 --no-cov`.
2. **GAP-4, package tier.** Add the queryset-scoping / input-shape-independence row to
   `tests/forms/test_resolvers.py`.
3. **GAP-2, package tier.** Add the update-with-omitted-file row, including the direct
   `_reconstruct_partial_data` assertion that the file key is absent from the reconstructed
   `data=`.
4. **Failability proofs for steps 1 and 3**, via
   `uv run python scripts/prove_failability.py docs/builder/temp-tests/slice-1/proofs.json
   --output <the report block>`. Two entries, the two `or` disjuncts named above. Revert and
   byte-compare each before starting the next (`### Mutations are transient`).
5. **GAP-2, live tier.** Add `UpdateItemWithFileViaForm` to `products/schema.py` over the
   existing `ItemFileModelForm`, then the live name-only-update row.
6. **GAP-3, live tier.** Add the narrowed-constraint `ModelForm` + injecting mutation to
   `products/forms.py` / `products/schema.py`, then the live `IntegrityError` row.
7. **The test-staleness sweep** for steps 5-6: grep all three trees for the new and neighbouring
   mutation field names, re-pin every enumeration, then the **full parallel**
   `uv run pytest --no-cov`.
8. **Failability proof for step 6** (the `save_or_field_errors` wrap).
9. `uv run ruff format <only the files this pass touched>` then
   `uv run ruff check --fix <the same files>` — never `.`, per the artifact contract. Then
   `git status --short`: anything outside the declared ownership list is a **stop-and-report**,
   never a revert; this tree carries a concurrent session's uncommitted work.

Line anchors are deliberately omitted: every path above is symbol-qualified because the three
`forms/` files are concurrently dirty and any line number written here would be wrong by the
time it is read.

### Test additions / updates

Summarized per gap in the plans above. In total: **3 new package rows** in
`tests/forms/test_resolvers.py`, **1** in `tests/forms/test_sets.py`, **2 new live rows** in
`examples/fakeshop/test_query/test_products_api.py`, **1 new `ModelForm`** and **2 new mutation
fields** in `examples/fakeshop/apps/products/`. No temp tests are needed for development; Worker
3 may want one under `docs/builder/temp-tests/slice-1/` to demonstrate that the pre-fix
assertions were non-distinguishing, which is the cleanest way to audit GAP-1 and GAP-2.

### Implementation discretion items

Assessed and decided as Worker 2's:

- **Which model backs GAP-2's package row** — `scalars.MediaSpecimen` (an existing
  `FileField` + `ImageField` model, no migration) or `products.Item.attachment`. Equivalent;
  pick whichever the file's existing imports already reach.
- **Whether GAP-1's two rows live in one test function or two.** Two is preferred (a `for` loop
  inside one test is ONE node id and can never raise the failability count above 1,
  `START.md` "Instruments that lie"), but a `parametrize` is equally acceptable.
- **The exact narrowed-constraint form name** in GAP-3.

Not discretionary, and not delegated: whether a package `.py` under
`django_strawberry_framework/` is edited. It is not (see the ownership partition).

### Spec slice checklist (verbatim)

This cycle's Slice 1 has no spec `## Slice checklist` entry — it is a grading slice of a
residual-reconciliation cycle. The build plan's own Slice-1 line is the contract, copied
verbatim, plus the corpus coverage the dispatch prompt required:

- [x] Slice 1: code conformance — grade every Decision and Definition-of-done item against `HEAD` source and tests; dispatch Worker 2 / Worker 3 only if a real gap is proven -> `docs/builder/bld-038-slice-1-code_conformance.md`
  - [x] All 14 Decisions graded
  - [x] Every `## Slice checklist` sub-check graded (5 slices, 14 nested sub-checks)
  - [x] Every `## Edge cases and constraints` bullet graded (16)
  - [x] Every `## Test plan` row graded (7)
  - [x] Every `## Definition of done` item graded (1-8)
  - [x] Every `## Implementation plan` "Files touched" / "New / changed tests" cell graded (5 × 2)
  - [x] `## Out of scope` (7) and `## Non-goals` (6) graded
  - [x] Worker 0's D-1…D-19 independently graded (2 corrected, 1 partially refuted, 16 confirmed)
  - [x] `review_inspect.py` run on all five named files with `--output-dir docs/shadow`
  - [x] Every claim about a baseline-dirty file stated against `git show HEAD:` into a scratch path outside the repo
  - [x] Gap found -> implementation plan written, `Status: planned`

### Failability proofs

`None; this pass introduced no new boundary.` Worker 1 wrote no source and no test. The three
proofs the **fix** owes are specified per gap above and are Worker 2's obligation, mandatory
rather than sampled.

One observation that belongs here rather than in a proof block: **two of the four gaps are
un-provable-by-reading and un-catchable-by-coverage in exactly the way
`### Fail-open shapes` describes.** Both are `or` expressions whose right operand no test can
make decisive. Neither reading the diff nor a 100% statement-coverage run could have found
them; the population count (`def get_form(` = 0 across 300 files) is what found them. Worker 3
should re-run that count rather than accept it.

### Hot-path budget

`Not applicable; plan declares no hot path.` Re-confirmed for the fix as
`docs/builder/BUILD.md` step 4 requires: the gaps are closed by test rows plus two example-app
mutation fields. Nothing runs per request, per resolver, per row, per connection, or per
outbound message in `django_strawberry_framework/` as a result. **No package `.py` is edited at
all**, so no per-request cost can be added. No before/after number is owed.

### Floor verification

The build plan declares scope `none` by default and instructs Worker 1 to re-declare if a proven
gap sends a builder into a framework seam. **Re-declared: GAP-2 and GAP-3 do.**

- **In scope.** GAP-2 exercises Django's bound-`ModelForm`-with-`instance` `initial` behavior,
  `FileField` storage round-tripping, and the multipart upload path — the "upload or body
  parsing" and "request/response handling" seams `### When it is required` names, and the same
  neighbourhood as the floor section's own cited failure (Python 3.10's `SpooledTemporaryFile`
  having no `seekable` attribute, caught only by executing at the floor). GAP-3 exercises
  Django's `_get_validation_exclusions` / `validate_unique` behavior, which decides whether the
  row reaches `save()` at all and is precisely the kind of thing a minor Django version moves.
- **Out of scope.** GAP-1 and GAP-4 touch only package-level hook-identity comparison and
  generated-input shape; no framework-version-sensitive behavior.
- **Focused scope to re-run at the floor** — not a second full sweep:

  ```shell
  uv venv /tmp/dsf-floor --python 3.10
  uv pip install --python /tmp/dsf-floor/bin/python -e . --group dev
  uv pip install --python /tmp/dsf-floor/bin/python 'django==5.2.16' 'strawberry-graphql==0.316.0'
  /tmp/dsf-floor/bin/python -m pytest tests/forms/test_resolvers.py -k "file or upload or preserve or integrity" --no-cov
  /tmp/dsf-floor/bin/python -m pytest examples/fakeshop/test_query/test_products_api.py -k "with_file or integrity" --no-cov
  ```

- **Owning pass:** the **Worker 2 build pass for this slice**, recording the scratch venv path
  and the resolved versions from `uv pip list --python /tmp/dsf-floor/bin/python`. The final gate
  is the backstop that confirms it happened, not a second owner. **Never install into the shared
  `.venv`** — `uv pip install` ignores `UV_PROJECT_ENVIRONMENT`, so the explicit `--python` is
  what keeps it out, and a mutated `.venv` silently changes the floor for every concurrent
  session on this checkout.

### Notes for Worker 1 (spec reconciliation)

The complete, itemized list Slice 2 works from. It is **additive to** the 9 items Slice 0 routed
forward in `docs/builder/bld-038-slice-0-rationale_extraction.md` — read both; nothing below
duplicates them. Every location is by **heading + quoted phrase**, never a line number: the file
has already shifted once this cycle and will shift again when Slice 2 edits it.

Grading case per item: **(1)** never built — code changes; **(2)** ship-time deviation — the
named side changes; **(3)** a later card deliberately changed it — code stands, spec is
rewritten to state the shipped contract directly, with what changed and why going to the
rationale companion as a `**Post-ship:**` bullet under the owning Decision.

**Case (3) — later cards changed it; rewrite the spec to the shipped contract (21 items).**

1. **`## Architectural decisions` → Decision 7, the converter bullet list** — quoted:
   "text-like (`CharField` / `EmailField` / … / base `Field`) → `str`; `IntegrityField` … `MultipleChoiceField` →
   `list[str]`." **Shipped truth:** the table also carries `forms.JSONField` →
   `strawberry.scalars.JSON`, added post-ship by `efb7bda5` because without the explicit row the
   `CharField` parent silently types JSON payloads as `String`. Same omission in **`## Definition
   of done` item 2** ("every supported form-field class → its Strawberry annotation"). Add the
   row to both.
2. **Decision 7** — quoted: "`NullBooleanField` → `bool | None`". **Shipped truth:**
   `forms/converter.py::form_field_required` is the single requiredness decision across both
   bases and is a **three**-case rule: an exact `NullBooleanField` is forced optional; a
   **subclass** keeps its declared requiredness and so resolves to a non-null `bool`; a
   **non-null-column-backed** field keeps `required=True`. Post-ship (`5737ddda`).
3. **Decision 7, the reverse-map paragraph** — quoted: "`forms/inputs.py` **retains, per generated
   input field, an `(input_attr, graphql_name) → (form_field_name, kind)` metadata record**".
   **Shipped truth:** the record type is `utils/inputs.py::InputFieldSpec` (`target_name` = the
   form field name, plus `related_model` / `source` / `nested_specs`); the four kind constants
   are defined there and re-exported by `forms/converter.py`, which now "owns only the kind
   constants". Same rewrite needed in the **Slice-1 checklist sub-check** ("Record, per generated
   input field, the `input_attr → (form_field_name, kind)` reverse map").
4. **Decision 7, the relation-decoder paragraph** — quoted: "`forms/resolvers.py` runs its **own**
   `relation_single` / `relation_multi` decoder that reuses the `036` *primitives*". **Shipped
   truth:** it is the form *coloring* (an `empty_values` skip plus a `to_field_name` projection)
   of the shared `utils/write_values.py::decode_visible_relation` spine, with
   `decode_field_handlers` / `decode_provided_fields` owning the `UNSET` strip and the kind
   dispatch — a substrate the serializer flavor also rides. The visibility-on-every-branch
   security contract is unchanged and must survive the rewrite verbatim.
5. **Decision 7, the shape-identity paragraph** — quoted: "it is the tuple **`(form_class,
   operation kind, frozenset(effective field names after `Meta.fields` / `Meta.exclude`))`**".
   **Shipped truth:** `forms/sets.py::_cached_build_form_input` keys on a **4-tuple** adding
   `_form_input_hook_identity(mutation_cls)` — `None` unless the mutation overrides
   `get_form_fields`, so two mutations over one form with different overrides cannot dedupe to
   one input. Same 3-tuple appears in **`## Definition of done` item 2** ("under the
   `036`-parallel **shape identity** `(form_class, operation kind, effective field set)`") and in
   the **Slice-2 checklist** ("uses the fixed identity sentinel **`"form"`** for its input-shape
   cache key"). Fix all three; the conceptual identity is unchanged, so say the fourth component
   is a hook discriminator, not a fifth concept.
6. **Decision 7, the create-guard paragraph** — quoted: "`update` is exempt — its reconstruction
   supplies model-backed fields from the instance". **Shipped truth:** there are **two**
   narrowing guards keyed on one waiver. `forms/inputs.py::guard_partial_required_column_less_fields`
   rejects an update narrowing that drops a **required column-less** field, because
   `model_to_dict` cannot reconstruct it, so the bound form would fail required-validation on
   every request while the schema finalized cleanly. Post-ship. The `## Edge cases`
   create-narrowing bullet does **not** repeat the exempt clause (correcting Worker 0's D-13) but
   is **silent** about the partial guard and should gain it.
7. **Decision 8, the "Helper reuse" paragraph** — quoted: "These are **module-private
   (`_`-prefixed) in `mutations/resolvers.py` today**" and "the lighter edit is dropping the
   leading underscore on exactly that subset". **Shipped truth (locations, all measured with
   `git grep -n "^def <name>(" HEAD`):** `locate_instance`, `coerce_lookup_id`,
   `authorize_or_raise`, `refetch_optimized`, `build_payload`, `not_found_error`,
   `save_or_field_errors` — `mutations/resolvers.py`; `validation_error_to_field_errors` —
   `utils/errors.py`; `raw_choice_value` — `utils/write_values.py`; `payload_object_slot` —
   `mutations/inputs.py`. See also case-(2) item 15 below: this paragraph is *also* wrong on its
   own date. The same nine-name list appears in the **`## Implementation plan` Slice-3 cell** and
   needs the same fix.
8. **Decision 8, the pipeline preamble** — quoted: "The whole pipeline runs inside one
   `transaction.atomic()`". **Shipped truth:** the shared skeleton
   `mutations/resolvers.py::run_write_pipeline_sync` also enforces a managed-transaction gate on
   one pinned write alias (`open_write_pipeline`, `pipeline_alias_guard`,
   `check_instance_write_alias`), captures an immutable `authorized_pk` / `target_state`
   snapshot immediately after the locate, and calls `check_deadline(info)` **before** the
   transaction opens. All post-`038` (`0.0.14` mutation atomicity; the `spec-047` cooperative
   deadline). A form mutation inherits every one of them, so a reader taking the spec's
   one-`atomic()` sentence as the whole boundary story is now wrong.
9. **Decision 8 step 4, the update-reconstruction bullet** — quoted: "`data = {**model_to_dict(instance,
   fields=<the form's non-file fields>), **provided_data}`". **Shipped truth:**
   `forms/resolvers.py::_reconstruct_partial_data` has **three** shapes, because an omitted field
   must bind in the same shape a provided one decodes to — `model_to_dict` for scalars and a
   `to_field_name`-**less** FK, `_to_form_key_value` per member for a real forward M2M, and
   `_to_form_key_value` for a `ModelChoiceField` **with** `to_field_name` set. It also reads the
   form's **full** declared set (`get_form_fields`), not the narrowed input, so a
   narrowed-away required FK is still reconstructed. Same one-shape formula appears in the
   **`## Edge cases` update-preservation bullet** and **`## Definition of done` item 4**.
10. **Decision 11, the plain-`Form` paragraph** — quoted: "**Preferred resolution:** the plain
    `DjangoFormMutation` requires the consumer to set `Meta.permission_classes` explicitly".
    **Shipped truth (two changes):** an unset `permission_classes` defaults to `(DenyAll,)` — the
    deny-by-default posture the paragraph goes on to describe, so drop the "Preferred
    resolution" framing (a Slice-0 chronology hedge whose Risks referent is gone) and state the
    default; **and** the plain base now **rejects** any `DjangoModelPermission` subclass entry at
    class creation, because that class resolves the write permission from a model a model-less
    mutation never provides — a request-time `AttributeError` otherwise. Post-ship.
11. **Decision 12** — quoted: "this spec narrows it to the existing `test_products_api.py` inside
    that directory". **Shipped truth:** the live form surface spans three apps —
    `products` (6 form mutations), `library` (`CreateShelfViaForm`, `UpdateBookViaForm`,
    `CreateBranchWithShelf`, `CreateBranchPair`, over `ShelfRelationsForm` /
    `BookGenresModelForm` / `BranchWithShelfForm` / `BranchPairForm`), and `scalars`
    (`CreateMediaSpecimenImageViaForm`). Library specifically earns the non-Relay raw-pk decode,
    the `to_field_name` conversion, the request-scoped-`queryset` idiom, and the plain-form
    `perform_mutate` rollback case. The narrowing was faithful when written; as a standing
    description it is now false. Same in **`## Definition of done` item 5** and the
    **`## Test plan` live bullet**.
12. **Decision 13** — quoted: "**`registry.clear()` co-clears THREE form rows**". **Shipped
    truth:** all three clears exist and are all reached, but `registry.py` names none of them
    (0 `clear_form` occurrences in the 610-line file). Each owning module announces itself with
    `register_subsystem_clear(...)` — `forms.input_namespace` (`before_bind=True`, so the
    `finalize_django_types` pre-bind reset reaches it too), `forms.declarations`,
    `forms.shape_cache` — and `registry.clear()` drains `iter_subsystem_clears()`. Same claim in
    the **`## Implementation plan` Slice-2 cell** ("`registry.py` (THREE form co-clear rows)").
13. **Decision 6** — quoted: "It is a lighter base (**its own metaclass**)". **Shipped truth:**
    `DjangoFormMutationMetaclass = make_meta_validating_metaclass(register_form_mutation, …)` —
    a shared factory over the disjoint plain-form ledger. It shipped as a hand-written
    `class …(type)`; the "own metaclass" *contract* (not `DjangoMutationMetaclass`, not the model
    ledger) is intact, the mechanism is shared. Same in the **Slice-2 checklist** ("the model-less
    sibling — its own metaclass + declaration registry").
14. **Decision 8, "How this pipeline actually fires"** and the **Slice-3 checklist** — quoted:
    "both form flavors override them to delegate **here**". **Shipped truth:** both flavors'
    `resolve_sync` / `resolve_async` come from `mutations/sets.py::resolver_seams(...)`
    (`with_id=False` for the plain flavor, matching `mutations/fields.py` #"operation != \"form\""),
    `bind_form_mutations()`'s whole body is one `bind_write_declarations(...)` call, and a new
    `mutations/operations.py` module owns the operation vocabulary
    (`NON_DELETE_WRITE_OPERATIONS`, `NON_DELETE_OPERATION_INPUT_KIND`,
    `non_delete_operation_error`) the spec spells inline.
15. **`## Out of scope`** — quoted: "**The ergonomic `TestClient` / `AsyncTestClient` helper** —
    `TestClient` (`TODO-ALPHA-043-0.0.14`)". **Shipped truth:** it shipped —
    `django_strawberry_framework/testing/client.py`, `testing/__init__.py`, a `conf.py` setting,
    and `examples/fakeshop/test_query/test_client_api.py`. The clearest third-kind item in the
    section. Same in **`## Non-goals`** ("The `TestClient` *ergonomic* helper, NOT file-field
    correctness"), where the file-field-correctness half of the claim still holds and must survive.
16. **`## Out of scope`** — quoted: "**DRF serializer mutations** … `0.0.13`
    (`TODO-ALPHA-039-0.0.13`)". **Shipped truth:** shipped —
    `django_strawberry_framework/rest_framework/`, `tests/rest_framework/`, and three products
    serializer mutations. Same in **`## Non-goals`** and in **`## Key glossary references`**
    ("the `0.0.13` flavor cards that reuse this card's nothing-new").
17. **`## Out of scope`** — quoted: "**Auth mutations** … `0.0.13` (`TODO-ALPHA-040-0.0.13`)".
    **Shipped truth:** shipped — `django_strawberry_framework/auth/mutations.py`,
    `examples/fakeshop/test_query/test_auth_api.py`. It is also the **third**
    `make_declaration_registry` consumer, which is live evidence for Decision 13's
    shared-mechanics-disjoint-ledgers call and worth citing there.
18. **The spec opener and Decision 2** — quoted: "reuses, **byte-identical**, the contracts
    `spec-036` **froze for exactly this**" (opener) and "This card adds **no** field to
    `FieldError`" (Decision 2). **Shipped truth:** the second sentence is still true of *this
    card*; the first is not true of the envelope's current shape —
    `mutations/inputs.py::FieldError` states #"The type is ADDITIVE, not frozen" and has gained
    `codes` and `path`. Rewrite the "frozen / byte-identical" framing to "additive; `038` adds no
    member", which keeps `038`'s normative claim and stops teaching a false invariant. The same
    "frozen" vocabulary recurs in **`## Key glossary references`**, **`## Problem statement`**,
    the **`### Reference-package parity checkpoint`** table row, and **`## Non-goals`**.
19. **Slice-2 checklist** — quoted: "The form allowed-key set adds `form_class` and drops `model` /
    `input_class` / `partial_input_class`". **Shipped truth:** `_ALLOWED_MODELFORM_META_KEYS` =
    `MODEL_BACKED_WRITE_META_KEYS | {form_class}` = `{fields, exclude, permission_classes,
    operation, select_for_update, form_class}`; `_ALLOWED_PLAIN_FORM_META_KEYS` =
    `COMMON_WRITE_META_KEYS | {form_class}` = `{fields, exclude, permission_classes,
    form_class}`. `select_for_update` is a post-`038` (`0.0.14`) row-locking key the `ModelForm`
    flavor accepts and the plain flavor rejects. (The **two-set split itself** is a case-(2)
    item — see item 20.)
20. **`## Definition of done` item 8 and the Slice-5 checklist** — quoted: "the version quintet"
    / "`pyproject.toml`, `__version__` in `__init__.py`, `tests/base/test_init.py::test_version`,
    the `docs/GLOSSARY.md` package-version line, and `uv.lock` if it carries the package
    version". **Shipped truth:** all five landed in `731fecd8`. At `HEAD` the quintet is a
    **triplet**: `pyproject.toml` carries no `version` literal (`[tool.hatch.version]` derives it
    from `__init__.py`, and `AGENTS.md` rule 31 makes that single-sourcing standing law) and
    `uv.lock` carries `source = { editable = "." }` with no version key, so the trailing
    conditional now resolves to "it does not". **Do not "update" the `0.0.12` figures** — the cut
    this card owned happened; only the *mechanism* description is stale.
21. **`## Implementation plan` Slice-2 cell** — quoted: "`mutations/inputs.py`
    (`build_payload_type(object_type=None)` emits the model-less `{ ok errors }` plain-form
    payload …)". **Shipped truth:** the signature is
    `build_payload_type(mutation_name, *, object_type: type | None, object_slot: str | None = None)`
    — `object_type` is keyword-**required** with no `None` default; `forms/sets.py::bind_form_mutations`
    selects the model-less shape by passing `resolve_object_type=lambda …: None` through
    `bind_write_declarations`. The one-builder-one-ledger contract Decision 6 states is intact.

**Case (2) — ship-time deviation; the named side changes (6 items).**

22. **Decision 8's opening paragraph and its seven numbered steps** — quoted: "**Ordering
    correction — authorize runs BEFORE the relation decode (post-ship security fix).**" and "The
    step numbers below reflect the original draft sequence". **The spec loses.** This is Worker 0's
    D-9, Slice 0's item 1, and the highest-value edit available to Slice 2: the Decision must
    state the shipped order directly — **locate → authorize → decode → construct/validate →
    write → re-fetch → return** — with the supersession narrative moving to the rationale
    companion as a `**Post-ship:**` bullet. `docs/builder/BUILD.md` `## Spec rationale
    extraction` forbids a spec that a reader must apply a chronology to, and leaving the steps in
    the draft order makes this a **false** contract, not merely a stale one. **The renumber is
    not local:** sweep every "step N" citation. Known citers inside the spec:
    Decision 7's decode paragraph, Decision 8's own step-4 cross-references, Decision 9 ("pipeline
    step 6"), Decision 11 ("Decision 8 step 2"), the `## Edge cases` relation-visibility and
    file bullets, `## Definition of done` item 4, and the `## Test plan` `test_resolvers.py` row.
    Cite by **content**, never by ordinal, in the rewrite (`START.md`: a heading rewrite strands
    every ordinal).
23. **Decision 8's "Helper reuse" paragraph** — quoted: "`build_payload` + `payload_object_slot`
    (the uniform-slot envelope)" among helpers "**module-private (`_`-prefixed) in
    `mutations/resolvers.py` today**". **The spec loses, and it was wrong on its own date:**
    `payload_object_slot` was already **public** in `mutations/inputs.py` at `731fecd8^`, i.e.
    before `038` began. The spec's own `## Current state` bullet says so ("`mutations/inputs.py`
    ships … the `build_payload_type` wrapper (the uniform `node` / `result` slot via
    `payload_object_slot`)"), so **two spec homes contradict each other** and `## Current state`
    is the right one. Remove `payload_object_slot` from the promotion list.
24. **Decision 8's "Helper reuse" paragraph** — quoted: "Slice 3 **picks one** and names it;
    'reuses the surrounding steps' is not left to the implementer to re-derive." **The spec
    loses.** An unresolved build instruction has no place in a shipped contract (Slice 0's item
    8). Slice 3 picked underscore-drop-in-place; no `mutations/_pipeline.py` exists. State where
    the helpers live (item 7's measured list) and move the two-options deliberation to the
    rationale companion.
25. **Slice-2 checklist** — quoted: "The form allowed-key set adds `form_class` and drops `model` /
    `input_class` / `partial_input_class`" (one sentence, one set). **The checklist loses.** At
    `731fecd8` there were already two disjoint sets with a ship-time comment spelling the split,
    and **Decision 10** states it correctly ("`DjangoModelFormMutation` validates `operation ∈
    {"create","update"}`, plain `DjangoFormMutation` rejects `operation` outright"). So the
    checklist was an under-description on its own date and the two homes disagree. Rewrite the
    checklist to name both sets (and fold in item 19's `select_for_update`).
26. **`## Edge cases and constraints`, the plain-form authorization bullet** — quoted: "a plain
    `DjangoFormMutation` **requires** an explicit `Meta.permission_classes`". **The bullet
    loses.** An unset `permission_classes` does not fail configuration — it defaults to
    `(DenyAll,)`, which is what Decision 11 actually settles. Two homes disagree and the Edge-case
    bullet is the wrong one. Rewrite it to the deny-by-default posture and the
    `permission_classes = []` opt-out, and add the `DjangoModelPermission` rejection from item 10.
27. **Decision 5, axis 1's parenthetical** — quoted: "(a shared marker base or a duck-typed
    `_mutation_meta` + `_payload_type_name` check)". **The spec loses.** `_payload_type_name` is a
    **bind** output and `DjangoMutationField` is constructed at import, before the bind runs, so a
    check requiring it could never pass — `mutations/fields.py::_validate_mutation_target` says so
    explicitly (#"It does NOT require ``_input_class`` / ``_payload_type_name``"). Replace the
    parenthetical with the shipped protocol: `_mutation_meta` present, plus callable
    `resolve_sync` / `resolve_async` / `input_type_name` and a non-`None` `input_module_path`;
    concreteness is then a separate own-snapshot + current-ledger check.

**Case (1) — never built; code (tests) changes, not the spec (4 items).**

28. **`## Test plan` `test_resolvers.py` row and Decision 8 step 4** — the `get_form` hook. See
    **GAP-1**. Slice 2 changes nothing here; the spec is right and the tests are owed.
29. **`## Test plan` `test_resolvers.py` row, `## Edge cases` (two bullets), Decision 8 step 4,
    DoD 5** — omitted file preserved via the bound form's `initial`. See **GAP-2**. Spec right,
    tests owed.
30. **`## Test plan` live bullet and `## Definition of done` item 5** — the live write-time
    `IntegrityError` for the `ModelForm` flavor. See **GAP-3**, including the contract-level
    question escalated to the maintainer. **If the maintainer chooses the relocate-the-citation
    answer instead**, Slice 2 rewrites both homes to cite
    `examples/fakeshop/test_query/test_library_api.py::test_create_branch_pair_rolls_back_first_write_when_second_conflicts`
    (plain-form) plus `tests/forms/test_resolvers.py::test_modelform_save_integrity_error_maps_to_envelope`
    (package, `ModelForm`) — and must say plainly that the `ModelForm` live half is unproven.
    Slice 2 must **not** make that call itself.
31. **`## Test plan` `test_resolvers.py` row and Decision 8 step 4** — the `get_form_kwargs`
    queryset-scoping / input-shape-unchanged clause. See **GAP-4**. Spec right, test owed.

**Two further notes for Slice 2 that are not spec edits.**

- **Row placement, not staleness (do not "fix" these).** The `## Test plan` `test_converter.py`
  row asks for the `ModelChoiceField` / `ModelMultipleChoiceField` id mapping (Relay-`GlobalID`
  vs raw pk), the reverse map, and `base_fields` discovery **in `test_converter.py`**; all three
  are pinned in `tests/forms/test_inputs.py` instead, and correctly so —
  `forms/converter.py::convert_form_field` deliberately returns `annotation=None` for relation
  and file kinds because the id type is resolvable only at the `forms/inputs.py` build site,
  where the backing column and the related primary `DjangoType` are known. If Slice 2 touches
  the row, move the clauses to the `test_inputs.py` row rather than declaring a gap.
- **`## Current state`, clause-by-clause** (Slice 0's item 9, now graded). All five bullets are
  dated **observations** and stand under `docs/builder/BUILD.md` `### `## Current state`:
  observations stand, predictions do not`: "The mutation foundation is shipped" (true then, and
  its quoted `_resolve_model` docstring naming the `0.0.12` form flavor is still in
  `mutations/sets.py`), "**No `forms/` module exists**" (true then), "**The version line reads
  `0.0.11`**" (true then), "**`0.0.12` has exactly one card**" (true then), "The products write
  surface is live … products has **no** `forms.py` yet" (true then). The borderline clause Slice
  0 flagged — "there is no joint cut to defer the version bump to" — is an **inference** from the
  card set rather than a reading, but the inference held: `038` did own the cut, and
  `CHANGELOG.md` `## [0.0.12] - 2026-06-23` shows it shipped alone. **No edit owed.** One clause
  does need a light touch: the bullet's parenthetical "(both 'planned by
  `TODO-ALPHA-038-0.0.12`')" quotes a `docs/TREE.md` state that has since been replaced by the
  shipped `forms/` summary lines — that is a quotation of a **generated** body, so Slice 2 should
  diff the quotation against the current render before deciding whether the observation framing
  carries it (`START.md`: "Doc quotes a generated body → diff quotation vs render").

---

## Build report (Worker 2)

The four proven gaps closed as Worker 1 sequenced them. **No package `.py` under
`django_strawberry_framework/` is in this diff** — every gap was a missing assertion, and none
turned out to need a behavior change, so the plan-vs-implementation-drift pause was never
reached. No migration was needed: `products.Item.attachment` already carries the file column and
`scalars.MediaSpecimen` already carries both a `FileField` and an `ImageField`
(`uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` -> `No changes
detected`).

### Populations re-derived, not accepted

Worker 1's counts were re-measured with a `uv run python` heredoc over the
`git ls-tree -r --name-only HEAD` listing filtered to `tests/` and `examples/fakeshop/`
(no bare `for f in $FILES`, so no zsh word-splitting), counting **occurrences** per file:

- **population: 300 `.py` files, 7,228,167 bytes read from `HEAD`** (Worker 1 recorded
  7,228,146 — a 21-byte drift from the concurrent session's own commits landing between the two
  reads, not a disagreement about the population).
- `def get_form(` — **0 occurrences in 0 files.** Confirmed exactly as recorded.
- `initial` — **39 occurrences in 21 files, none of them under `tests/forms/`.** Confirms
  Worker 1's `initial` = 0 in `tests/forms/`; the 21 files are migrations, `tests/utils`,
  `tests/test_views.py` and friends.
- `get_form_kwargs` — **19 occurrences in 6 files**, exactly the six Worker 1 named.

### Files touched

Grounded in `git status --short`, not memory:

- `tests/forms/test_sets.py` — imports `_form_kwargs_overridden`; adds the parametrized
  `get_form`-only waiver-detection row (GAP-1, package tier).
- `tests/forms/test_resolvers.py` — imports `django.test.override_settings`; adds the
  `get_form`-only construction row (GAP-1), the `get_form_kwargs` queryset-scoping /
  input-shape-independence row (GAP-4), and two file-preserve rows (GAP-2).
- `examples/fakeshop/apps/products/forms.py` — adds `DefaultCategoryItemModelForm` (GAP-3's
  narrowed-constraint driver); the module docstring's form enumeration is corrected (it said
  "Four forms" while listing four of the then-five, and omitted `PingForm`) and gains the two
  new behaviors. **The docstring's FIRST line is unchanged**, so `docs/TREE.md`'s rendered
  summary for this file is untouched (verified against `git show HEAD:` and the live
  `docs/TREE.md` row).
- `examples/fakeshop/apps/products/schema.py` — adds `UpdateItemWithFileViaForm` (GAP-2 live)
  and `CreateDefaultCategoryItemViaForm` (GAP-3 live) plus their two `Mutation` fields; the
  `Mutation` docstring's form-surface paragraph names both. First docstring line unchanged, same
  `docs/TREE.md` reason.
- `examples/fakeshop/test_query/test_products_api.py` — adds the two live rows.

**Two of these files were already baseline-dirty when this pass started**, which the plan's
`## Baseline-dirty out-of-scope files` names only at the package level: `tests/forms/test_sets.py`
and `tests/forms/test_resolvers.py` both carry the concurrent session's uncommitted test
additions (in `test_resolvers.py` the `_decode_form_relation_multi` one-shot-generator and
hostile-iteration rows; in `test_sets.py` eight hunks including
`test_cached_build_form_input_partial_column_less_guard`). Every edit here was a surgical
`Edit` on top; nothing of theirs was reverted or reformatted away. See
`### Notes for Worker 3` — the diff Worker 3 reads is a **mixed** diff on those two files.

### Tests added or updated

- `tests/forms/test_sets.py::test_get_form_only_override_trips_the_construction_hook_waiver`
  (parametrized `[modelform]` / `[plain_form]`, so **two node ids**, not a `for` loop) — pins
  that `forms/sets.py::_form_kwargs_overridden` is `True` for a mutation overriding **only**
  `get_form`, on each flavor against its own framework base, with the overrides-neither control
  in the same row so the detection cannot pass by being always-`True`. **GAP-1.**
- `tests/forms/test_resolvers.py::test_get_form_only_override_builds_the_form_and_waives_the_required_guard`
  — a `DjangoFormMutation` narrowing a still-required field away with **only** `get_form`
  overridden: `finalize_django_types()` not raising is the waiver-through-the-second-disjunct
  assertion, and the pipeline is proved to validate the override's own form object (sentinel
  value reaching `cleaned_data` **and** identity against the captured instance). **GAP-1.**
- `tests/forms/test_resolvers.py::test_get_form_kwargs_queryset_scoping_leaves_the_generated_input_shape_unchanged`
  — two mutations over one form, one overriding `get_form_kwargs` to pass the request-scoped
  `ModelChoiceField` queryset: the generated input's **name and annotation set are equal** across
  the pair (shape independence), and the scoped mutation rejects an out-of-queryset
  `categoryId` with a `category`-keyed `FieldError` while the unscoped one accepts the same id
  (the override demonstrably takes effect). Either assertion alone is non-distinguishing.
  **GAP-4.**
- `tests/forms/test_resolvers.py::test_partial_update_omitting_file_field_keeps_it_out_of_the_reconstructed_data`
  — calls `forms/resolvers.py::_reconstruct_partial_data` directly (the file's established habit
  for the distinguishing assertion) to pin that **no `attachment` key exists** in the
  reconstructed bound payload while the unprovided required FK and the provided scalar both do,
  then drives the update end to end and asserts the stored `FieldFile` name and bytes are
  unchanged. **GAP-2.**
- `tests/forms/test_resolvers.py::test_partial_reconstruction_excludes_every_file_field_flavor`
  (parametrized `[attachment]` / `[image]`) — the `FileField` and its `ImageField` subclass as
  **separate node ids** over one `scalars.MediaSpecimen` form, which is the property the
  production docstring claims ("the one `isinstance` catches both"). **GAP-2.**
- `examples/fakeshop/test_query/test_products_api.py::test_update_item_with_file_via_form_omitting_the_file_preserves_it`
  — the AGENTS.md rule 10 live tier for the preserve contract: multipart create, then a
  `name`-only JSON update over `/graphql/`, asserting the stored `attachment.name` and its bytes
  survive. **GAP-2.**
- `examples/fakeshop/test_query/test_products_api.py::test_create_default_category_item_via_form_write_time_integrity_error_uses_envelope`
  — DoD 5's missing live row, **mock-free**: `DefaultCategoryItemModelForm` narrows `category`
  out of `Meta.fields`, so Django's `_get_validation_exclusions` drops it and `_post_clean`'s
  `validate_constraints()` never checks `unique_item_per_category`; the mutation injects the
  category through `get_form_kwargs`, and a duplicate `name` passes `form.is_valid()` and fails
  only at the INSERT. The row asserts the save-time mapper's own wording
  (`"A database constraint was violated."`) on the `"__all__"` sentinel and **no field-level
  error**, which is exactly what separates it from the pre-existing validation-time
  `test_create_item_via_form_unique_constraint_envelope_uses_all_sentinel` row. **GAP-3.**

Every catalog / auth live row opens with `create_users(1)` + `seed_data(1)` from
`apps.products.services` (AGENTS.md rule 8); the package rows use inline
`Model.objects.create(...)` as the package tier does.

### Validation run

- `uv run ruff format <the 5 files>` — pass (`5 files left unchanged`).
- `uv run ruff check --fix <the same 5 files>` — pass (`All checks passed!`).
- `uvx pre-commit run --files <the same 5 files>` — first run: `source-layout` **auto-fixed**
  trailing-comma layout in `tests/forms/test_resolvers.py` and `tests/forms/test_sets.py`
  (2 files reformatted, 5 sites); re-run: **all six hooks pass**, `citations resolve` included.
- `git status --short` after both ruff invocations — the five files above are modified as
  intended. Everything else in the 148-path list is the concurrent session's (116 at pre-flight;
  the plan says the population grows while the cycle runs). **Nothing was reverted.** The four
  cycle artifacts (`build-038-*`, `bld-038-slice-0`, `bld-038-slice-1`, the rationale companion)
  are untracked, and `docs/SPECS/spec-038-form_mutations-0_0_12.md` is dirty from Slice 0 — not
  this pass.
- `uv run pytest tests/forms -n0 --no-cov` — **263 passed** (256 before this pass; +7 node ids:
  2 + 1 + 1 + 1 + 2).
- `uv run pytest --no-cov` (the FULL parallel sweep, run twice — once mid-pass for the staleness
  class and once at the end) — **7204 passed, 40 skipped, 4 failed**, all four failures
  pre-existing and unrelated (see `### Pre-existing failures, recorded and escalated`).
- `uv run python examples/fakeshop/manage.py check` — `System check identified no issues (0
  silenced).`
- `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` — `No changes
  detected`.

### The example-schema staleness sweep

GAP-2 and GAP-3 each add a field to `examples/fakeshop/apps/products/schema.py::Mutation`
(`updateItemWithFileViaForm`, `createDefaultCategoryItemViaForm`), so the fakeshop SDL changed.
Per `docs/builder/BUILD.md` `### Test staleness a focused run cannot see` and
`### Example-project schema changes must sync every schema-module list`:

- **Enumeration sweep, population printed.** A `uv run python` heredoc over **302 files**
  (`tests/**/*.py`, `examples/fakeshop/**/*.py`, plus the `.md` files in both trees) counted
  occurrences of every neighbouring products form-mutation wire name
  (`createItemViaForm` 18 / `updateItemViaForm` 12 / `createItemWithFileViaForm` 6 /
  `createStampedItemViaForm` 5 / `submitContact` 9 / `submitPing` 1 / their snake_case twins)
  and of the enumeration shapes (`Mutation.__strawberry_definition__` 1,
  `mutation_fields` 3, `field_names` 109). **Every hit is either the declaration in
  `products/schema.py` or a per-row query string in `test_products_api.py`.** A second regex
  pass over the same 302 files for lines combining a products mutation name with an
  enumeration/count operator (`len(`, `== [`, `== {`, `sorted(`, `set(`, `in {`,
  `assert ...fields`) returned **10 candidate lines, none of which enumerates the products
  `Mutation` field set** (they are per-row payload assertions and two
  `_field_arg_map(schema, "<one field>")` checks). **Nothing needed re-pinning.**
- **SDL / introspection snapshot sweep.** Same 302-file population:
  `"type Mutation"` 1 occurrence (a docstring in `tests/forms/test_resolvers.py`),
  `"Mutation {"` 0, `mutationType` 0, `__schema` 12 across 5 files (all query-shaped, none
  snapshotting the products mutation set), `IntrospectionQuery` 3 (debug-toolbar transport).
  **No SDL snapshot pins the products mutation field list.**
- **Schema-module lists.** No new app and no new schema module was added, and this was
  **confirmed by grep, not assumed**: `apps.products.schema` is already a row in
  `examples/fakeshop/schema_reload.py::_PROJECT_APP_SCHEMA_MODULES` and in
  `examples/fakeshop/tests/test_inspect_django_type.py` `_SCHEMA_MODULES` (the two private lists
  the sweep found). Nothing to sync.
- **Verified with the FULL parallel `uv run pytest --no-cov`**, never a focused run — the only
  instrument that can see this class.

### Pre-existing failures, recorded and escalated

`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` makes a
failing-test claim **not worker-verifiable** (reproducing it needs a clean HEAD tree, and this
one is dirty with 148 paths of another session's work). Recorded with the evidence available,
and **escalated to the maintainer**:

- Failing node ids: `tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key`,
  `tests/orders/test_inputs.py::test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration`,
  `tests/test_sets_mixins.py::test_permission_family_config_stays_on_each_set_class`,
  `tests/test_sets_mixins.py::test_filter_normalizer_honors_a_subclass_unset_sentinel_override`.
- All four raise the same error: `TypeError: ActiveInputPermissionAttrs.__init__() got an
  unexpected keyword argument 'unset_sentinel'`.
- **HEAD content obtained read-only** (`git show HEAD:<path>` into a scratch path outside the
  repo; no `git stash` / `checkout` / `restore` / `worktree` at any point):
  `django_strawberry_framework/sets_mixins.py` at `HEAD` **declares** `unset_sentinel: Any = None`
  on `ActiveInputPermissionAttrs` (7 `unset_sentinel` occurrences); the **working tree** carries
  5 and no such field. So the concurrent session's uncommitted edit to `sets_mixins.py` — a
  baseline-dirty out-of-scope file — removed the field while its tests still pass it.
- **Not in this pass's diff.** The four rows live in `tests/optimizer/`, `tests/orders/` and
  `tests/test_sets_mixins.py`; this diff touches neither those files nor `sets_mixins.py`, and
  the four reproduce **in isolation in 0.18s** with no forms or products code loaded.
- Not reverted, not fixed: AGENTS.md rule 34 and the plan's fence both bar touching that
  session's work.

### Failability proofs

Three boundaries are newly pinned by this pass and all three carry a proof, run through the
mechanized runner (`uv run python scripts/prove_failability.py
docs/builder/temp-tests/slice-1/proofs.json --output docs/builder/temp-tests/slice-1/proofs.md`,
manifest at the mandated path, scratch root
`/private/tmp/claude-501/.../scratchpad/failability` — **outside the repository**). The runner
exited **0**: every entry proved, none weakly pinned, no collection or setup error. The block
below is the runner's own emitted output, with only the zero-row `why 0` slot to fill by hand —
and there is **no zero-row entry**, so nothing was filled in.

Procedure, mechanized by `scripts/prove_failability.py`: the target is copied to a scratch path OUTSIDE the repo before any mutation; the mutation site is located by an exact anchor asserted to match exactly once (any other count aborts the entry without writing); the same focused scope is run unmutated first, so rows already failing before the mutation are differenced out of the count; both runs' pytest exit codes are read, because a run that collected nothing or blew up emits no `FAILED` lines and would otherwise be recorded as a measured zero; both runs use `--no-cov`; the file is restored from the pre-mutation copy in a `finally` and the restore is proved by `filecmp.cmp(shallow=False)` plus a SHA-256 comparison. One boundary at a time, restored before the next. `git` is never invoked - the tree is legitimately dirty, so an empty `git diff` is unachievable and forcing one would destroy the build's own work.

| # | Boundary | File mutated | Mutation applied | Rows failed | Errors | Scope as run | Restore proof |
|---|---|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/forms/sets.py::_form_kwargs_overridden` | `django_strawberry_framework/forms/sets.py` | `return _hook_overridden(cls, base, "get_form_kwargs") or _hook_overridden( cls, base, "get_form", )` -> `return _hook_overridden(cls, base, "get_form_kwargs")` - builder's description (unverified prose): the get_form disjunct deleted, leaving only the get_form_kwargs operand | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/forms/test_sets.py tests/forms/test_resolvers.py -n0` | filecmp.cmp(shallow=False) True; sha256 1a4815ac50fb9624... == 1a4815ac50fb9624... (vs pre-mutation copy) |
| 2 | `django_strawberry_framework/forms/resolvers.py::_reconstruct_partial_data` | `django_strawberry_framework/forms/resolvers.py` | `if name in provided_data or isinstance(form_field, forms.FileField):` -> `if name in provided_data:` - builder's description (unverified prose): the FileField disjunct deleted, so an omitted file field is reconstructed from model_to_dict into the bound data= | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/forms/test_resolvers.py examples/fakeshop/test_query/test_products_api.py -n0` | filecmp.cmp(shallow=False) True; sha256 83079ddaa148d40e... == 83079ddaa148d40e... (vs pre-mutation copy) |
| 3 | `django_strawberry_framework/forms/resolvers.py::_modelform_write_step` | `django_strawberry_framework/forms/resolvers.py` | `write_error = save_or_field_errors(form.save)` -> `form.save() write_error = None` - builder's description (unverified prose): the save_or_field_errors wrap removed, so a write-time IntegrityError propagates instead of mapping to the FieldError envelope | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/forms/test_resolvers.py examples/fakeshop/test_query/test_products_api.py -n0` | filecmp.cmp(shallow=False) True; sha256 83079ddaa148d40e... == 83079ddaa148d40e... (vs pre-mutation copy) |

Verdicts:

1. `django_strawberry_framework/forms/sets.py::_form_kwargs_overridden` - inside Worker 3's mandatory re-run floor (<= 3 rows)
2. `django_strawberry_framework/forms/resolvers.py::_reconstruct_partial_data` - inside Worker 3's mandatory re-run floor (<= 3 rows)
3. `django_strawberry_framework/forms/resolvers.py::_modelform_write_step` - inside Worker 3's mandatory re-run floor (<= 3 rows)

Failing node ids, per boundary (the count above is `len()` of this list):

1. `django_strawberry_framework/forms/sets.py::_form_kwargs_overridden`
   - file mutated: `django_strawberry_framework/forms/sets.py`
   - pytest summary: `======================== 3 failed, 162 passed in 1.71s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 165 passed in 1.64s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/forms/test_resolvers.py::test_get_form_only_override_builds_the_form_and_waives_the_required_guard`
   - `tests/forms/test_sets.py::test_get_form_only_override_trips_the_construction_hook_waiver[modelform]`
   - `tests/forms/test_sets.py::test_get_form_only_override_trips_the_construction_hook_waiver[plain_form]`
2. `django_strawberry_framework/forms/resolvers.py::_reconstruct_partial_data`
   - file mutated: `django_strawberry_framework/forms/resolvers.py`
   - pytest summary: `======================== 3 failed, 199 passed in 25.12s ========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 202 passed in 25.25s =============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/forms/test_resolvers.py::test_partial_reconstruction_excludes_every_file_field_flavor[attachment]`
   - `tests/forms/test_resolvers.py::test_partial_reconstruction_excludes_every_file_field_flavor[image]`
   - `tests/forms/test_resolvers.py::test_partial_update_omitting_file_field_keeps_it_out_of_the_reconstructed_data`
3. `django_strawberry_framework/forms/resolvers.py::_modelform_write_step`
   - file mutated: `django_strawberry_framework/forms/resolvers.py`
   - pytest summary: `======================== 2 failed, 200 passed in 25.00s ========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 202 passed in 25.12s =============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/forms/test_resolvers.py::test_modelform_save_integrity_error_maps_to_envelope`
   - `examples/fakeshop/test_query/test_products_api.py::test_create_default_category_item_via_form_write_time_integrity_error_uses_envelope`

A boundary whose removal fails 0 or 1 rows is **weakly pinned** and is `revision-needed` per `docs/builder/BUILD.md` - the fix is more or better-targeted rows, never a weaker boundary. A boundary at 3 rows or fewer is inside Worker 3's mandatory independent re-run floor. A proof carrying collection or setup errors, or whose pytest run exited anything but 0 or 1 (nothing collected, interrupted, internal error, usage error), is not a valid count at all - and a 0 from such a run is not a zero-row result: resolve it and re-run.

Every `<fill in ...>` above is a judgement no tool can make and MUST be replaced by hand before this subsection is submitted: weakly pinned and harness-impossible are the two possible readings of a zero-row result and they prescribe opposite responses (more rows, versus a production-call-site invariant assertion plus a recorded harness limitation), so a record that does not name one reads as self-contradictory.

**Post-run independent confirmation that no mutation survives.** Beyond the runner's own
`filecmp` + SHA-256 proof: no `ACTIVE-MUTATION.json` and no `RESTORE-FAILED.json` exists in the
scratch root; all three anchors match exactly once again in the working tree
(`grep -c` -> `1`, `1`, `1`); and an explicit `cmp` of each of the three pristine copies against
the live file prints `IDENTICAL` for `forms/sets.py` and for `forms/resolvers.py` against **both**
of its copies. `git diff --stat -- django_strawberry_framework/forms/` shows only the concurrent
session's three-file hunk set, which is what it showed before the proofs ran.

**One measured fact worth carrying forward, because it is the opposite of what the plan
predicted.** The plan expected GAP-2's live row to fail under the `FileField`-disjunct mutation.
It does **not**, and entry 2's node-id list is the measurement:
`test_update_item_with_file_via_form_omitting_the_file_preserves_it` was inside the recorded
scope and passed under the mutation. The reason is Django, not the test: a file widget's
`value_from_datadict` reads `files` only, so a stored path injected into `data=` is ignored and
the bound `ModelForm(instance=...)`'s `initial` preserves the column either way. The three rows
that do fail are the ones asserting the reconstructed payload **directly** — which is precisely
`docs/builder/BUILD.md` `### Harness-impossible interleavings`'s prescription (assert the
invariant at the production call site, not at the wire), arrived at independently because Worker
1 required the direct `_reconstruct_partial_data` assertion. The live row is still owed and kept:
it pins the **contract** the spec states in five homes (omit -> preserved), and it is what would
catch a future reconstruction change that Django's widget *does* read. It is simply not what
pins the disjunct, and the record says so rather than letting a wire-level pass manufacture
confidence.

### Hot-path budget

`Not applicable; plan declares no hot path.` Re-confirmed against the diff as landed: no package
`.py` under `django_strawberry_framework/` is edited at all, so no per-request, per-resolver,
per-row, per-connection or per-outbound-message cost can have been added. The two new
example-app mutation fields cost one `DjangoMutationField` construction each at schema build,
not per request. No before/after number is owed.

### Floor verification

Owned by this pass per the plan's `### Floor verification` re-declaration (GAP-2 and GAP-3 touch
Django's upload / body-parsing and validation seams). Built outside the repo with an explicit
`--python`, so the shared `.venv` was never a target of `uv pip install`:

```shell
uv venv /tmp/dsf-floor --python 3.10
uv pip install --python /tmp/dsf-floor/bin/python -e . --group dev
uv pip install --python /tmp/dsf-floor/bin/python 'django==5.2.16' 'strawberry-graphql==0.316.0'
```

- **Scratch venv path:** `/tmp/dsf-floor` (outside the working tree).
- **Resolved versions, as read by `uv pip list --python /tmp/dsf-floor/bin/python`** (never from
  memory): `django 5.2.16`, `strawberry-graphql 0.316.0`, `django-filter 26.1`,
  `djangorestframework 3.18.0`, `channels 4.3.2`, `pillow 12.3.0`, `pytest 9.1.1`;
  `/tmp/dsf-floor/bin/python -c "import sys; print(sys.version)"` ->
  `3.10.19 (main, Jan 27 2026, 23:32:40) [Clang 21.1.4]`. That is exactly the floor
  `docs/builder/BUILD.md` `## Floor verification` states: Django **5.2.16** on Python **3.10**
  with strawberry-graphql **0.316.0**. Note the pin was load-bearing — `-e . --group dev`
  resolved `django 5.2.17` / `strawberry-graphql 0.327.1` first and the explicit pin stepped
  both down.
- **The shared `.venv` is unchanged**, verified after the floor build by `uv pip list`:
  `django 6.1`, `strawberry-graphql 0.324.0`, `django-filter 26.1` — the newest supported set,
  not the floor. (Recorded as a reading, per the same section's ban on stating it from memory.)
- **Focused scopes and results**, exactly as the plan's block specifies:
  - `/tmp/dsf-floor/bin/python -m pytest tests/forms/test_resolvers.py -k "file or upload or
    preserve or integrity" --no-cov -n0` -> **11 passed, 57 deselected** (`django: version:
    5.2.16` in the header). **PASS.** The selection includes all three new GAP-2 package rows.
  - `/tmp/dsf-floor/bin/python -m pytest examples/fakeshop/test_query/test_products_api.py -k
    "with_file or integrity" --no-cov -n0` -> **3 passed, 131 deselected**. **PASS.** The
    selection includes both new live rows plus the pre-existing multipart upload row.

### Implementation notes

- **GAP-1's two rows are two functions, not one** (`### Implementation discretion items` left
  this to me, preferring two): the `test_sets.py` row is a `parametrize` over the two flavors
  because each detects against a different framework base, and the `test_resolvers.py` row is a
  separate function because it asserts a different thing (the pipeline calling the override).
  A `for` loop over the flavors would have been ONE node id and could never have raised the
  proof above 1 (`START.md` "Instruments that lie").
- **GAP-1's control lives inside the same row.** The overrides-neither assertion is an extra
  line in the parametrized row rather than its own function: on its own it passes with the
  boundary removed, so promoting it to a node id would have inflated the row count without
  pinning anything.
- **GAP-2's package rows use both candidate models, not one.** `### Implementation discretion
  items` offered `scalars.MediaSpecimen` or `products.Item.attachment` as equivalent; they are
  not, once the acceptance rule is applied. `Item.attachment` (nullable, alongside a required FK)
  is the end-to-end row and also proves the FK IS reconstructed while the file is not;
  `MediaSpecimen` carries both a `FileField` and an `ImageField`, which is the only way to drive
  the `ImageField`-subclass half of the one `isinstance` as its own node id. `Item` alone would
  have left the boundary on ONE failing row — weakly pinned.
- **GAP-4 asserts shape equality, not object identity.** The two mutations over one form
  currently dedupe to the same `_input_class` (same shape identity, `_form_input_hook_identity`
  `None` for both), so `is` would pass too — but the load-bearing claim is *shape*
  independence, and an `is` assertion would fail spuriously if a future change legitimately
  split the classes while keeping the shape. Name + `{(python_name, str(type))}` set is the
  property the spec states.
- **GAP-3's driver injects the app's default `Category`, not a request-derived value.** It needs
  a value the generated input cannot carry (the whole point of narrowing `category` out of
  `Meta.fields`) and it must be deterministic for the live row; `Category.objects.order_by("pk")
  .first()` is both, and it reuses `CreateStampedItemViaForm`'s established
  `get_form_kwargs`-injection shape rather than inventing a second one.
- **GAP-3's form attaches the injected FK in `__init__`, on the unsaved instance.** `_post_clean`
  runs `construct_instance` over `Meta.fields` only, so a `category` set in `__init__` survives
  to `save()`; setting it later (in `clean()` or a `save()` override) would work too but would
  put the FK assignment after the validation window it is deliberately hidden from.
- **The GAP-2 live row keeps the raw-multipart create leg and uses a plain JSON POST for the
  update leg.** The create needs the hand-built `{operations, map, "0"}` envelope to attach a
  file at all (the spec-043 raw-multipart exemption the sibling upload row already records); the
  update carries no file, so it goes through `_post_graphql` like every other live row.
- **`products/forms.py`'s docstring enumeration was corrected, not just extended.** It read
  "Four forms cover the spec's Decision-12 live matrix" and listed four of the then-five
  (`PingForm` was missing). It now says "These forms" and enumerates all six. Checked first that
  no `path #"substring"` citation quotes that prose (grep over the repo for the phrase and for
  `products/forms.py` citers: the only hits are the spec's reference-style link definition, this
  artifact, the build plan, and a closed DRY cycle's scratchpad).

### Notes for Worker 3

- **The diff on `tests/forms/test_sets.py` and `tests/forms/test_resolvers.py` is MIXED.** Both
  files were already dirty with the concurrent session's uncommitted rows when this pass began,
  which the plan's `## Baseline-dirty out-of-scope files` records only for the three `forms/`
  package files. This pass's hunks are: in `test_sets.py`, the `_form_kwargs_overridden` import
  and `test_get_form_only_override_trips_the_construction_hook_waiver`; in `test_resolvers.py`,
  the `override_settings` import,
  `test_get_form_only_override_builds_the_form_and_waives_the_required_guard`,
  `test_get_form_kwargs_queryset_scoping_leaves_the_generated_input_shape_unchanged`,
  `test_partial_update_omitting_file_field_keeps_it_out_of_the_reconstructed_data` and
  `test_partial_reconstruction_excludes_every_file_field_flavor`. Everything else in those two
  files' diffs is theirs (notably `test_cached_build_form_input_partial_column_less_guard` and
  the `_decode_form_relation_multi` iteration rows) and is out of scope for this review.
- **Re-run the proofs at the scope the record names**, `-n0` included: entry 2 and entry 3 share
  a scope that spans the live tier and takes ~25 s per run, and dropping the live file from
  entry 3 would drop one of its two rows and grade a correctly-pinned boundary as weakly pinned.
- **Entry 2's most interesting datum is a row that did NOT fail** — the live preserve row. The
  `### Failability proofs` block explains why (Django's file widget reads `files` only). If you
  distrust it, the cheapest independent check is a temp test under
  `docs/builder/temp-tests/slice-1/` that calls `_reconstruct_partial_data` with the disjunct
  present and absent; that is the seam the boundary actually decides at.
- **`scripts/review_inspect.py` was not run by this pass**, and the skip is deliberate rather
  than an omission: `### When to run the helper during build` scopes Worker 2's use to "when the
  plan or prior review asks for it", and the plan asks for none — no new `.py` file, no file
  under `optimizer/` or `types/`, and zero lines of new logic in `django_strawberry_framework/`.
  Worker 1 ran it on all five form-subsystem files during the grading pass and its output is
  still under `docs/shadow/`.
- **No temp tests were created or promoted.** Worker 1 predicted none would be needed for
  development and that held.
- **No `--cov*` flag was used in any command this pass.** Every `pytest` invocation carried
  `--no-cov`, including the two full sweeps and both floor runs, and the proof runner adds it
  itself.

### Notes for Worker 1 (spec reconciliation)

On disk, per `worker-2.md` `### Spec amendments go on disk, not in the return message`. Nothing
below duplicates Worker 1's own 31-item list; these are what **this pass's diff** changes about
it.

1. **The four `DROPPED` verdicts are discharged; case-(1) items 28-31 need no spec edit and
   should be closed with citations rather than rewritten.** Where they live: the Plan's
   `### The proven code gaps` and the `## Test plan` / `## Edge cases` / Decision-8-step-4 /
   DoD-5 rows that carry the `**DROPPED**` cell. Recommended replacement, per gap — re-grade to
   `BUILT-CONFORMANT` citing:
   - GAP-1 ->
     `tests/forms/test_sets.py::test_get_form_only_override_trips_the_construction_hook_waiver`
     and
     `tests/forms/test_resolvers.py::test_get_form_only_override_builds_the_form_and_waives_the_required_guard`;
   - GAP-2 ->
     `tests/forms/test_resolvers.py::test_partial_update_omitting_file_field_keeps_it_out_of_the_reconstructed_data`,
     `::test_partial_reconstruction_excludes_every_file_field_flavor`, and live
     `examples/fakeshop/test_query/test_products_api.py::test_update_item_with_file_via_form_omitting_the_file_preserves_it`;
   - GAP-3 -> live
     `examples/fakeshop/test_query/test_products_api.py::test_create_default_category_item_via_form_write_time_integrity_error_uses_envelope`
     (mock-free), which means **DoD item 5 and the `## Test plan` live bullet stand as written**
     and the escalation's rejected alternative (rewrite the two homes to cite the plain-form
     library row) stays rejected;
   - GAP-4 ->
     `tests/forms/test_resolvers.py::test_get_form_kwargs_queryset_scoping_leaves_the_generated_input_shape_unchanged`.
2. **Decision 12 / DoD 5 / the `## Test plan` live bullet — the products form-mutation count
   moved.** Where it lives: Worker 1's case-(3) item 11 ("**Shipped truth:** the live form
   surface spans three apps — `products` (6 form mutations) ..."). Current wording quoted:
   "`products` (6 form mutations)". Recommended replacement: "`products` (**8** form mutations:
   `createItemViaForm`, `updateItemViaForm`, `createItemWithFileViaForm`,
   `updateItemWithFileViaForm`, `createDefaultCategoryItemViaForm`,
   `createStampedItemViaForm`, `submitContact`, `submitPing`)". The same "6" appears in this
   artifact's D12 row and in the build plan's `## Worker-0 verification pass`; those are
   per-cycle scratch and need no edit, but Slice 2 must not copy the 6 forward.
3. **Decision 8 step 4's file clause is CORRECT and should survive the renumber verbatim, with
   one clause added.** Where it lives: Decision 8 step 4, the `update` sub-bullet. Current
   wording quoted: "`files = provided_files` **only** — an omitted file field is preserved by the
   bound `form_class(instance=…)` via its `initial`, never re-supplied and never cleared."
   Recommended replacement: keep that sentence unchanged and append — "The reconstruction
   therefore contributes **no key at all** for a file field: `model_to_dict` yields the stored
   relative path, which is not a re-bindable `data=` value for a field fed from `files=`." Why:
   this pass measured that a wire-level row **cannot** detect the exclusion's removal (Django's
   file widget reads `files` only), so the exclusion is a data-hygiene boundary whose only
   observable is the reconstructed payload. A reader who takes the current sentence as the whole
   story will believe a live test covers it, and for three patch releases nobody did.
4. **`## Test plan`'s `test_resolvers.py` row asks for the `get_form_kwargs` queryset-scoping
   case in a shape the hook cannot deliver alone.** Where it lives: the `## Test plan`
   `test_resolvers.py` row, and Decision 8 step 4. Current wording quoted: "or to scope a
   `ModelChoiceField.queryset` **without changing the generated input shape**". Recommended
   replacement: "or to pass the request-scoped `ModelChoiceField` queryset the form narrows with
   in its own `__init__` — `get_form_kwargs` returns **constructor kwargs**, so the hook is the
   channel and the form applies it — **without changing the generated input shape**". Why:
   `get_form_kwargs`'s return value is spread into `form_class(**kwargs)`, so it can only scope a
   queryset by handing the form a value the form's `__init__` installs; the current phrasing
   reads as though the hook mutates `field.queryset` itself, which is not a thing it can do. The
   test that now pins the clause implements the kwarg-channel shape.

---

## Final verification (Worker 1)

Not applicable to this pass. This slice's own status is `planned` because it proved a gap; the
final-verification block belongs to the Worker 1 pass that runs after Worker 2 builds the four
gaps and Worker 3 reviews the diff.

What that pass must audit, recorded now so it is not re-derived:

- the three failability proofs the fix owes, each with its byte-compared revert;
- the floor run declared in `### Floor verification`, with the scratch venv path and the resolved
  versions as read;
- the full-parallel sweep behind the SDL / mutation-field-enumeration sweep (a focused run cannot
  see the staleness that sweep exists to catch);
- that no package `.py` under `django_strawberry_framework/` appears in the diff — if one does,
  it is drift and routes back to Worker 1, not through;
- the four `DROPPED` verdicts above, re-graded against the new diff: each should move to
  `BUILT-CONFORMANT` with a test citation, or carry a recorded deferral.

### Summary

Graded `spec-038`'s whole corpus against `HEAD` — every one of the 14 Decisions, 5 slices and 14
nested sub-checks, 16 `## Edge cases` bullets, 7 `## Test plan` rows, 8 `## Definition of done`
items, 10 `## Implementation plan` cells, 7 `## Out of scope` and 6 `## Non-goals` bullets — as
**140 verdict rows: 105 `BUILT-CONFORMANT`** (96 clean plus 9 built-but-with-one-stale-sentence),
**21 `SPEC-STALE`, 8 `DROPPED`** (4 distinct gaps across their spec homes), **6 `DEVIATED`**.
Every figure re-measured by a parser over the tables after writing them. The shipped
form-mutation subsystem delivers every
substantive contract the spec states — both bases, the fail-loud converter, the form-derived
inputs with their shape identity and collision raise, the visibility-on-every-branch relation
decoder, the partial-update reconstruction, the pinned plain-form payload, the phase-2.5 bind,
the three co-clears, the write-auth split, and the `0.0.12` cut. Nothing substantive was
dropped. What the spec no longer describes accurately is *where* things live and *how* they are
mechanized: three later cards consolidated the pipeline into shared substrates
(`utils/write_values.py`, `utils/converters.py`, `utils/inputs.py`, the
`run_write_pipeline_sync` skeleton, the `make_*` factories), moved two promoted helpers,
converted the `registry.clear()` co-clear into a self-announcing subsystem registry, and added
six landed boundaries the spec never names. Those 21 items are Slice 2's.

The four `DROPPED` verdicts are the cycle's real find, and they are all missing assertions rather
than missing behavior: the `get_form` override hook is untested anywhere in a 300-file
population, the omitted-file-preserve contract is unpinned at every tier, DoD 5's live
`ModelForm` write-time `IntegrityError` row was never written, and the `get_form_kwargs`
input-shape-independence clause has no test. Two of them sit behind `or` disjuncts that no test
can make decisive — the exact shape `fail_under = 100` structurally cannot see — which is why a
100%-covered, 256-green subsystem could carry them for three patch releases without anyone
noticing.

One correction worth carrying to the dispatcher: two of Worker 0's nineteen findings had wrong
attribution (D-1 miscounts seven helpers as six and treats a pre-`038` location as a later move;
D-16 reads a shipped two-set split as a post-ship change) and one was partially refuted (D-13's
claim that the `## Edge cases` bullet repeats the "`update` is exempt" clause — it does not).
Sixteen confirmed as stated.

### Spec changes made (Worker 1 only)

None. The spec and its rationale companion were opened read-only. Slice 2 owns every edit, and
the 31-item list plus 2 non-edit notes above is what it works from.

### Final status

`planned`


---

## Review (Worker 3)

### Independent failability re-runs — the three mutations, recorded BEFORE they are made

`docs/builder/worker-3.md` "Reading is necessary, not sufficient" puts **all three** of this
pass's boundaries inside the mandatory re-run floor (recorded rows 3 / 3 / 2, each `<= 3`), so
the re-run set is all three and nothing was accepted on Worker 2's record alone. Each is re-run
at **the scope Worker 2 recorded**, `-n0` included, and compared as a **node-id set**.

Recorded here before any mutation is applied, per the source carve-out (`worker-3.md` "Scope"):

1. `django_strawberry_framework/forms/sets.py::_form_kwargs_overridden` — delete the
   `get_form` disjunct: the five-line
   `return _hook_overridden(cls, base, "get_form_kwargs") or _hook_overridden(cls, base, "get_form",)`
   becomes `return _hook_overridden(cls, base, "get_form_kwargs")`.
2. `django_strawberry_framework/forms/resolvers.py::_reconstruct_partial_data` — delete the
   `FileField` disjunct: `if name in provided_data or isinstance(form_field, forms.FileField):`
   becomes `if name in provided_data:`.
3. `django_strawberry_framework/forms/resolvers.py::_modelform_write_step` — remove the
   mapper wrap: `write_error = save_or_field_errors(form.save)` becomes `form.save()` +
   `write_error = None`.

Every mutation is applied by `scripts/prove_failability.py` (which copies to a scratch root
outside the repo, asserts the anchor matches exactly once, runs the unmutated scope first,
restores in a `finally`, and proves the restore by `filecmp.cmp(shallow=False)` + SHA-256), one
boundary at a time, reverted before the next. Results below.

### Re-run results — node-id SET comparison against Worker 2's record

Runner: `uv run python scripts/prove_failability.py <my own manifest> --output <scratch>` with
`scratch_root` under my own scratchpad (outside the repo), exit **0**. Anchors pre-checked with
`--check-anchors-only`: all three matched **exactly once**, so no prior live mutation was
inherited. Manifest copied from `docs/builder/temp-tests/slice-1/proofs.json` unchanged except
the scratch root, so the scope, anchor and replacement are byte-identical to Worker 2's.

| # | Boundary | W2 rows | W3 rows | Node-id SET | Baseline (same scope) | Collection/setup errors |
|---|---|---|---|---|---|---|
| 1 | `forms/sets.py::_form_kwargs_overridden` (`get_form` disjunct) | 3 | **3** | **identical** | `165 passed`, exit 0 (W2: `165 passed`) | 0 |
| 2 | `forms/resolvers.py::_reconstruct_partial_data` (`FileField` disjunct) | 3 | **3** | **identical** | `202 passed`, exit 0 (W2: `202 passed`) | 0 |
| 3 | `forms/resolvers.py::_modelform_write_step` (`save_or_field_errors` wrap) | 2 | **2** | **identical** | `202 passed`, exit 0 (W2: `202 passed`) | 0 |

The sets, not just the totals:

1. `tests/forms/test_resolvers.py::test_get_form_only_override_builds_the_form_and_waives_the_required_guard`;
   `tests/forms/test_sets.py::test_get_form_only_override_trips_the_construction_hook_waiver[modelform]`;
   `…[plain_form]`.
2. `tests/forms/test_resolvers.py::test_partial_reconstruction_excludes_every_file_field_flavor[attachment]`;
   `…[image]`; `::test_partial_update_omitting_file_field_keeps_it_out_of_the_reconstructed_data`.
3. `tests/forms/test_resolvers.py::test_modelform_save_integrity_error_maps_to_envelope`;
   `examples/fakeshop/test_query/test_products_api.py::test_create_default_category_item_via_form_write_time_integrity_error_uses_envelope`.

Zero set difference on all three. Every mutation genuinely removes its boundary (each anchor
read in the live source: the disjunct deleted, the disjunct deleted, the mapper call replaced by
a bare `form.save()` inside the same `pipeline_write_phase()`); every count is `>= 2`, so
**none is weakly pinned**; every count carries a stated **0** collection/setup errors and a
green same-scope pre-mutation baseline. GAP-1's row is genuinely **two node ids**
(`[modelform]` / `[plain_form]` appear separately above), not a `for` loop.

**Boundaries re-run: all three. Boundaries accepted on Worker 2's record alone: none.** The
mandatory floor (`worker-3.md`, `<= 3` recorded rows) covered all three, so an empty or partial
subset was not available.

**No mutation survives, verified three ways beyond the runner's own proof.** No
`ACTIVE-MUTATION.json` / `RESTORE-FAILED.json` in either scratch root; all three anchors match
exactly once in the live tree after the runs (`grep -c` -> `1`, `1`, `1`); and `cmp` of every
pristine copy in **both** scratch roots (Worker 2's three and my three) against the live file
prints identical for `forms/sets.py` and for `forms/resolvers.py`. `git diff --stat --
django_strawberry_framework/forms/` shows only the concurrent session's three-file hunk set
(`inputs.py` +76/-, `resolvers.py` +21/-, `sets.py` +30/-), whose content I read and matched to
the plan's `## Baseline-dirty out-of-scope files` description (the
`materialize_relation_id_container` lift and the typed `get_form_fields` hook wrap) — no proof
residue. `git stash` / `checkout` / `restore` / `worktree` were never run.

### The GAP-2 live-row question — ruling: keep it, and it is not the worthless case

Worker 2 reports honestly that `test_update_item_with_file_via_form_omitting_the_file_preserves_it`
does **not** fail under entry 2's mutation, and keeps it. `docs/builder/BUILD.md`
`### Harness-impossible interleavings` says a wire-level assertion that still passes with the
invariant removed is worthless. **That sentence does not govern this row**, for three reasons I
established rather than accepted:

1. **It is scoped to the zero-row case, and this boundary is pinned at three rows.** The section
   opens "When a proof shows 0 rows failing and the reason is the harness rather than the tests",
   and its prescription is "assert the invariant at the production call site, not at the wire."
   That prescription is exactly what landed: the three failing rows call
   `forms/resolvers.py::_reconstruct_partial_data` directly. Worker 2 does not offer the live row
   as the pin and says so in the record, so the row manufactures no confidence about the disjunct.
2. **Worker 2's stated reason is correct — I drove it, without mutating source.** Temp test
   `docs/builder/temp-tests/slice-1/test_w3_file_widget_ignores_data_key.py` binds the form the
   way the *mutated* reconstruction would (`data={"name":…, "category":…, "attachment": <stored
   relative path>}`, `files={}`, `instance=item`) and passes: the form validates,
   `cleaned_data["attachment"]` is **not** the injected string, and after `save()` the stored name
   and bytes are unchanged. The exclusion is therefore a data-hygiene boundary whose only
   observable is the reconstructed payload — no wire-level row of any design could detect its
   removal.
3. **The row pins a different contract on a different call path, and one the spec's own
   rationale rejected the alternative to.** The three unit rows pin the *mechanism* (no key in
   `data=`); the live row is the only proof anywhere that the `update`-over-a-file-form path
   exists end to end over HTTP — that `updateItemWithFileViaForm` resolves, that
   `ItemFileModelFormPartialInput` leaves `attachment` omittable, that the multipart-create /
   JSON-update sequence interoperates, and that the column survives a real `form.save()`. That
   is `AGENTS.md` rule 10's mandatory live tier for a package line a real request reaches, and
   `spec-038`'s rationale companion, Decision 12, records
   **"Synthetic-model-only coverage (no live surface). Rejected"** as a considered-and-rejected
   alternative. Deleting the row would re-raise it.

So: **accepted, not split.** It is not the "deleting it loses nothing" case; deleting it would
lose the only end-to-end proof of the preserve outcome and violate rule 10.

### High:

None.

### Medium:

#### GAP-3's live row is not right-path pinned: a broken `get_form_kwargs` injection produces the identical envelope

`examples/fakeshop/test_query/test_products_api.py::test_create_default_category_item_via_form_write_time_integrity_error_uses_envelope`
asserts exactly one error, keyed `"__all__"`, with the message
`examples/fakeshop/test_query/test_products_api.py #"A database constraint was violated."`. That
assertion set correctly separates the row from the pre-existing **validation-time** row
(`::test_create_item_via_form_unique_constraint_envelope_uses_all_sentinel`), and I verified the
separation mechanically rather than on prose: the string is produced by exactly one symbol,
`django_strawberry_framework/utils/errors.py::integrity_error_field_errors`, whose only form-flavor
caller is `django_strawberry_framework/mutations/resolvers.py::save_or_field_errors`, which
`forms/resolvers.py::_modelform_write_step` reaches only *after*
`_bound_form_or_field_errors` returned no errors — so the message is proof that `form.is_valid()`
passed and `save()` ran. `products/models.py::Item.Meta` declares
`UniqueConstraint(name="unique_item_per_category")` with no `violation_error_message`, so a
validation-time failure carries Django's own constraint wording and cannot forge this one.
**That half of the row is sound.**

What the row does **not** pin is the driver it documents. Its docstring and the whole GAP-3
escalation rest on a *uniqueness* race reached by narrowing `category` out of
`examples/fakeshop/apps/products/forms.py::DefaultCategoryItemModelForm`'s `Meta.fields` **and**
injecting it through
`examples/fakeshop/apps/products/schema.py::CreateDefaultCategoryItemViaForm.get_form_kwargs`.
`products/models.py::Item` declares `category` as a non-nullable FK, and the form's
`__init__` guard is `if category is not None:` — so if the injection silently stopped happening,
`save()` still raises an `IntegrityError` (NOT NULL instead of unique), and
`save_or_field_errors`'s deliberately broad `except IntegrityError` maps it to the **same**
`"__all__"` / same-message envelope. The row stays green.

**Failure scenario, driven not argued.** `docs/builder/temp-tests/slice-1/test_w3_gap3_row_is_not_right_path_pinned.py`
instantiates `DefaultCategoryItemModelForm(data={"name": …})` with **no** `category` kwarg:
`form.is_valid()` is `True` and `form.save()` raises `IntegrityError`. Both temp rows pass. So a
regression that broke the `get_form_kwargs` override — the exact hook the mutation exists to
demonstrate — leaves this row passing and its own error assertions satisfied, while the
narrowed-unique-constraint path it claims to exercise goes untested. Compounding it:
`grep -rn "DefaultCategoryItemModelForm\|createDefaultCategoryItemViaForm" tests/ examples/`
returns **11 hits in 3 files, every one either a declaration or this single failure-path row** —
the new mutation has **no happy-path row anywhere**, so nothing in any tree asserts that the
injection works.

This is `docs/builder/BUILD.md` `### Query-shape tests must pin the load-bearing property, not
observability`, "Right-path tests": confirm the test actually exercises the intended path, and
keep it minimal enough that it can only take the path it claims to test. It is Medium, not High:
the boundary the failability proof measures (`save_or_field_errors`) is genuinely pinned at two
rows either way, and no package behavior is wrong.

**Recommended change (Worker 2, one row's worth of work).** Add a positive leg to the same row:
POST a **non-colliding** `name` through `createDefaultCategoryItemViaForm`, assert it succeeds,
and assert the created `Item`'s `category_id` equals the injected default
(`models.Category.objects.order_by("pk").first().pk`). That single addition makes the row
distinguish the uniqueness driver from a NOT-NULL degradation, and gives the new example-app
surface the happy-path coverage it currently lacks. **Test expectation:** with the
`kwargs["category"] = …` line removed from `CreateDefaultCategoryItemViaForm.get_form_kwargs`,
the row must fail.

#### The staleness sweep's population excluded the repo-root standing docs, and this diff staled one of them

`### The example-schema staleness sweep` claims "**Nothing needed re-pinning**" over a
**302-file** population defined as `tests/**` + `examples/fakeshop/**` (`.py` plus the `.md`
files in those two trees). I re-derived that sweep independently and it is **correct for the
population it ran on**: my own 302-file pass finds `updateItemWithFileViaForm` (4 occurrences)
and `createDefaultCategoryItemViaForm` (3) only in `products/schema.py` and
`test_products_api.py`; **0** candidate lines combine a products form-mutation name with an
enumeration operator (`len(` / `== [` / `== {` / `sorted(` / `set(` / `in {` / `.fields` /
`field_names` / `mutation_fields` / `__strawberry_definition__`); `"type Mutation"` = 1 (a
docstring), `"Mutation {"` = 0, `mutationType` = 0, and the 12 `__schema` hits in 5 files are all
query-shaped. I also re-derived the schema-module-list claim over 300 `.py` files: exactly two
private enumerations exist (`examples/fakeshop/schema_reload.py #"_PROJECT_APP_SCHEMA_MODULES = ("`
and `examples/fakeshop/tests/test_inspect_django_type.py #"_SCHEMA_MODULES = ("`), both already
carry `apps.products.schema`, and no new module was added.

The blind spot is the **repo root**, which that population cannot see. `TODAY.md` enumerates the
products form-mutation surface by wire name in **three** places (`TODAY.md`
#"- **Form-based mutation write surface**", #"as of `0.0.12` the form-backed mutations", and
#"**Form-backed mutations (`0.0.12`).**"), and all three now under-enumerate: they list six and
the surface is eight. `git grep`-equivalent over `*.md` outside the two test trees confirms
`TODAY.md` is the only such home (`docs/README.md` names only `CreateItemViaForm` inside an
illustrative code block, which is not an enumeration; `docs/GLOSSARY.md` and `KANBAN.md` carry
none).

**Failure scenario:** a reader takes `TODAY.md`'s "Mutations on products today" section as the
live surface inventory, and it is short by the two fields this pass added — the same
partial-claim residue class that reopens a cycle. No test or gate covers it: `TODAY.md` is not in
the citation gate's `path::Symbol` corpus and no generator renders it.

**This one is NOT Worker 2's to fix**, which is why it is escalated rather than a re-pass item:
the build plan's `## Scope fence` names `TODAY.md` among the closeout surfaces "out of scope and
no worker touches them". The fence was written for a cycle expected to touch only spec files and
package `.py`; it did not anticipate this cycle **adding two live mutation fields**. See
`### Notes for Worker 1 (spec reconciliation)`.

**Recommended change (Worker 2, artifact only):** qualify the "Nothing needed re-pinning" claim
with the population it measured, so the next reader does not read it as repo-wide.

### Low:

#### GAP-4's shape half is an equality-only assertion with no absolute anchor — recorded, not required

`tests/forms/test_resolvers.py::test_get_form_kwargs_queryset_scoping_leaves_the_generated_input_shape_unchanged`
asserts `scoped_name == any_name` and `scoped_fields == any_fields`. Both mutations currently
dedupe to the **same** `_input_class` object (`forms/sets.py::_form_input_hook_identity` returns
`None` for both, so the shape-cache key matches), which makes the comparison a self-comparison
today; `docs/builder/BUILD.md` `### Query-shape tests must pin the load-bearing property` warns
that an equality-only assertion is vacuous without an absolute expectation. A literal anchor
(the field set is exactly `{("category_id", …)}`) would supply one.

**Recorded and intentionally not required.** The only realistic regression is
`get_form_kwargs` becoming part of the input identity, which is **per-mutation** — it could shift
the scoped mutation's shape but not both mutations' shapes identically — so the equality
comparison does cover it, and if the classes split while the name derivation
(`forms/sets.py::_form_input_type_name_for`, which never consults the hook) kept them equal, the
row fails at `_schema(Mutation)` on a duplicate type name. Worker 2's
`### Implementation notes` bullet shows the `is`-vs-shape choice was reasoned, not defaulted, and
the runtime half of the row (out-of-queryset id rejected field-keyed on the scoped mutation,
accepted on the unscoped one) is genuinely distinguishing. Adding the anchor would be an
improvement, not a defect closed.

#### Worker 2's `unset_sentinel` occurrence counts have already rotted — the durable half of the claim holds

`### Pre-existing failures, recorded and escalated` states `sets_mixins.py` carries "7
`unset_sentinel` occurrences" at `HEAD` and "5" in the working tree. Measuring now:
**12 at `HEAD`, 9 in the working tree** — the concurrent session has written the file since. The
**load-bearing** half re-derives exactly: `git show HEAD:django_strawberry_framework/sets_mixins.py`
into a scratch path outside the repo **declares** `unset_sentinel: Any` on
`ActiveInputPermissionAttrs` (1 occurrence of the declaration) and the working tree declares it
**0** times. No change required — a raw occurrence count of a file another session is editing is
a moving figure by construction, and the presence/absence of the declaration is the evidence that
does not rot.

### DRY findings

- **Existence challenge — `DefaultCategoryItemModelForm` + `CreateDefaultCategoryItemViaForm`:
  they earn their existence; `StampedItemModelForm` could NOT have carried the case.** Worker 1's
  plan raised the reuse question, so I checked the source rather than the plan's answer:
  `examples/fakeshop/apps/products/forms.py::StampedItemModelForm` declares
  `Meta.fields = ("name", "category")`. With `category` **in** `Meta.fields`, Django's
  `_get_validation_exclusions` keeps it, `_post_clean`'s `validate_constraints()` checks
  `unique_item_per_category`, and the duplicate is caught **before** `save()` — the row would
  degrade into a second copy of the pre-existing validation-time envelope test and prove nothing
  about `save_or_field_errors`. Narrowing its `Meta.fields` to fix that would break
  `createStampedItemViaForm`'s live row, which posts `categoryId` through the form. Its
  `clean()` (requires an authenticated `user`) and its `save()` (stamps `description`) would also
  have to be entangled with the race. A second form is the smaller change. Nothing to delete.
- **`UpdateItemWithFileViaForm` earns its existence at near-zero cost.** It adds no form: three
  lines of `Meta` over the existing `products/forms.py::ItemFileModelForm`, differing from
  `CreateItemWithFileViaForm` only in `operation`. No `update`-over-a-file-form mutation existed
  anywhere in the trees. (I confirmed the diff's `operation = "create"` line on
  `CreateItemWithFileViaForm` is diff **alignment**, not a change: `git show HEAD:` shows the key
  already present, so no pre-existing surface was altered.)
- **The two `get_form_kwargs` overrides in `products/schema.py` are near-identical (7 lines,
  identical signature, one differing assignment) — considered, not a finding.** It is the app's
  established consumer-facing declaration idiom, and this is its second instance;
  the example app exists to show consumers the plain override shape, so factoring it into a mixin
  would hide the thing being demonstrated. The signature is the framework's published hook
  signature and cannot be shortened.
- **Repeated literals across the new example-app code are `Meta.fields` names.** The shadow
  overviews report `3x category` in `products/forms.py` and `4x description` / `4x is_private` /
  `4x created_date` / `4x updated_date` / `3x category` in `products/schema.py` — every one a
  declarative field name inside a `Meta` tuple, matching the pre-existing pattern across all six
  apps. Naming a constant for a `Meta.fields` entry would be strictly worse. No finding.
- **The two GAP-2 package rows are not near-copies, and the second is load-bearing.** They look
  parallel but differ in what they can prove: the `Item` row is the end-to-end one and also pins
  that the unprovided **required FK IS** reconstructed while the file is not; the
  `MediaSpecimen` row is the only way to drive the `ImageField` subclass half of the single
  `isinstance(form_field, forms.FileField)` as its own node id. Worker 2's
  `### Implementation notes` records that `Item` alone would have left the boundary on **one**
  failing row — weakly pinned — and my re-run confirms the arithmetic: entry 2's three rows are
  one `Item` row plus two `MediaSpecimen` parametrizations.
- **Overlap noted and accepted: the `Item` package row's end-to-end leg shares its subject with
  the live preserve row.** Both prove "omit the file -> stored file survives". `AGENTS.md`'s
  live-first rule ("promoting to live DELETES the package-only stand-in") does not bite, because
  the row is not a stand-in for the live contract — its primary subject, the direct
  `_reconstruct_partial_data` dict assertion, is unreachable from a live request, and the
  six-line end-to-end leg is what anchors that dict assertion to a real pipeline run rather than
  leaving it a claim about a helper's return value. Recorded; no change required.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**: `__all__` and the re-export
list are untouched, and no package `.py` under `django_strawberry_framework/` appears in this
pass's diff at all. I verified the second claim independently rather than accepting it — the only
dirty package files under `forms/` carry exactly the concurrent session's described hunks (read
line by line: the `materialize_relation_id_container` lift in `_decode_form_relation_multi`, and
the typed `ConfigurationError` wrap around the `get_form_fields` hook invocation), with no
residue from this pass.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. Two adjacent checks
were still owed and were performed, because the slice edited two module docstrings:

- **`products/forms.py`'s docstring feeds a script-rendered doc.** `docs/TREE.md`
  #"Consumer Django forms for the products live form-mutation surface (spec-038)." renders the
  module docstring's **first line**, which is byte-identical to `git show HEAD:`'s. The edited
  text is on a later line, so no regenerate is owed (and the fence bars one). Same for
  `products/schema.py`'s `Mutation` docstring.
- **No staging language entered either docstring.** The added prose states shipped behavior; no
  "planned", "Slice N", or `TODO(` appears. The corrected enumeration is now accurate: the
  docstring lists **6** bullets and the module defines **6** classes (measured, both).
- **The corrected sentence was not a citation target.** Worker 2 claims it checked; I re-derived:
  no `path #"substring"` citation anywhere quotes the retired "Four forms cover the spec's
  Decision-12 live matrix" phrasing, and `scripts/check_citations.py --check` reports
  `OK: 938 citations resolve (783 in 435 .py files, 155 in KANBAN.md)`.

### Claims re-derived, not accepted

Every load-bearing figure in the Plan and the Build report, re-measured with my own instrument.
Populations printed; multi-file sweeps run through a `uv run python` heredoc, never a bare
`for f in $FILES` (I hit the zsh single-word collapse once on a scoped `ruff` invocation this
pass and re-ran it with a `files=(…)` array — the failure mode `START.md` "Instruments that lie"
names).

| Claim | Source | My measurement | Verdict |
|---|---|---|---|
| `def get_form(` = 0 across the test + example trees | Plan `#### GAP-1`, Build report | **0 occurrences in 0 files**, population **300 `.py` files / 7,228,167 bytes** read from `HEAD` | confirmed |
| `initial` = 0 in `tests/forms/` | Plan `#### GAP-2`, Build report | **0 occurrences in 0 files** at `HEAD` | confirmed |
| `get_form_kwargs` = 19 in 6 files | Plan `#### GAP-4`, Build report | **19 occurrences in 6 files** | confirmed |
| population 300 files / 7,228,146 (W1) vs 7,228,167 (W2) bytes | both | **7,228,167** — W2's figure exactly; W1's 21-byte deficit is the drift W2 already named | confirmed, W2 right |
| products form mutations 6 -> 8 | Build report `### Notes for Worker 1` item 2 | `^class .*\((DjangoModelFormMutation\|DjangoFormMutation)\):` = **6** at `HEAD`, **8** now; the two new `DjangoMutationField` rows are present | confirmed |
| `uv run pytest tests/forms -n0 --no-cov` = 263 (from 256) | `### Validation run` | **263 passed** | confirmed |
| staleness sweep population 302 files, nothing to re-pin | `### The example-schema staleness sweep` | **302 files**; every wire-name hit in 2 files; **0** enumeration lines; no SDL snapshot — correct **for that population**, see the Medium above | confirmed, scope qualified |
| two private schema-module lists, both already carry `apps.products.schema` | same | confirmed over **300 `.py` files**; exactly two enumerations found | confirmed |
| the 4 pre-existing failures are the concurrent session's | `### Pre-existing failures` | `HEAD` declares `unset_sentinel: Any` on `ActiveInputPermissionAttrs`; the working tree declares it **0** times; none of the 4 rows' files, nor `sets_mixins.py`, is in this pass's diff | confirmed (counts rotted, see Low) |
| verdict rows = 140 (105/21/8/6) | Plan `### Verdict summary` | an independent crude table parser returns **139-141** depending on how three multi-verdict cells are attributed, and the collapse arithmetic is internally consistent (96+9+21+8+6 = 140) | consistent within instrument resolution |
| `manage.py check` / `makemigrations --check` clean | `### Validation run` | `System check identified no issues (0 silenced).` / `No changes detected` | confirmed |
| ruff / source-layout clean on the 5 files | `### Validation run` | `5 files already formatted`; `All checks passed!`; `check_trailing_commas.py --check` exit **0** | confirmed |

### Full-sweep result, and the four pre-existing failures

Run twice, because the first run caught the concurrent session mid-edit. Both runs are recorded
rather than only the clean one — a sweep whose population silently shrank is the failure mode
`START.md` names ("one collection ERROR in one test module drops coverage across every file its
tests build schemas through").

- **Run 1** (`uv run pytest --no-cov -p no:cacheprovider`): **5 failed, 7166 passed, 40 skipped,
  1 error**. The error was `SyntaxError` collecting `tests/utils/test_inputs.py` — a half-written
  docstring opener (`""` for `"""`) in a **baseline-dirty** file this pass never touches — and the
  fifth failure, `tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`,
  traces to the **same** `ast.parse` of that same file (the governance sweep parses every
  committable `.py`). One broken module, two symptoms, plus the ~38-row shortfall from the
  uncollected module. `git show HEAD:tests/utils/test_inputs.py` parses cleanly, so the breakage
  was working-tree-only.
- **Run 2**, after the concurrent session fixed its own file (it now parses): **4 failed, 7231
  passed, 40 skipped, 0 errors, 0 collection errors** — `FAILED
  tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key`,
  `tests/orders/test_inputs.py::test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration`,
  `tests/test_sets_mixins.py::test_permission_family_config_stays_on_each_set_class`,
  `tests/test_sets_mixins.py::test_filter_normalizer_honors_a_subclass_unset_sentinel_override`,
  all four `TypeError: ActiveInputPermissionAttrs.__init__() got an unexpected keyword argument
  'unset_sentinel'`.

**Exactly the four node ids Worker 2 recorded, same error, no new failure.** The passed count is
7231 against Worker 2's 7204 (+27) because the concurrent session added rows in between; the
figure is a moving target on this tree and the node-id **set** is what carries the claim.
`docs/builder/BUILD.md` `## Claims are proven mechanically` makes a failing test at `HEAD`
**not worker-verifiable** (it needs a clean `HEAD` tree), so I record the evidence and leave the
escalation with Worker 0 — no fix, no revert, no workaround attempted. **None of the four, and
neither of run 1's two extra symptoms, is caused by this pass's hunks**: none of the six files
involved is in the declared writable set, and each cause is a concurrent session's uncommitted
edit to a baseline-dirty file.

`git diff --check` over the whole tree reports trailing whitespace only in an untracked
maintainer-input markdown file that is baseline-dirty and outside this pass's set; the five files
this pass touched are clean.

### Floor verification — it happened, and the shared `.venv` was not mutated

Verified as recorded, not accepted on prose. Versions read, never stated from memory:

- `/tmp/dsf-floor` exists outside the working tree.
  `uv pip list --python /tmp/dsf-floor/bin/python` -> `django 5.2.16`,
  `strawberry-graphql 0.316.0`, `django-filter 26.1`, `pillow 12.3.0`;
  `/tmp/dsf-floor/bin/python -c "import sys; print(sys.version.split()[0])"` -> `3.10.19`.
  That is exactly the floor `docs/builder/BUILD.md` `## Floor verification` states: Django
  **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**.
- **Both focused scopes re-run by me at the floor, and both reproduce Worker 2's numbers
  exactly:** `tests/forms/test_resolvers.py -k "file or upload or preserve or integrity"` ->
  **11 passed, 57 deselected**; `examples/fakeshop/test_query/test_products_api.py -k "with_file
  or integrity"` -> **3 passed, 131 deselected**. The second selection contains both new live
  rows; the first contains all three new GAP-2 package rows.
- **The shared `.venv` is unmutated.** `uv pip list` -> `django 6.1`,
  `strawberry-graphql 0.324.0`, `django-filter 26.1`, Python `3.14.2` — the newest supported set,
  not the floor, read after the floor runs. No `uv pip install` was issued without an explicit
  `--python`, by Worker 2's record or by me.
- The plan's floor scope was `none by default`, re-declared by Worker 1 as **GAP-2 and GAP-3 in
  scope, owned by the Worker 2 build pass**. That pass ran it and recorded it. No planned floor
  verification is unrun.

### Hot-path budget verification

The plan declares **none**, Worker 1 re-confirmed it for the fix, and I verified the declaration
holds against the diff as landed: no `.py` under `django_strawberry_framework/` is in this pass's
diff, so no per-request, per-resolver, per-row, per-connection or per-outbound-message cost can
have been added. Correctly `Not applicable`; no number is owed and none is missing. (One
observation, not a finding and not a package cost: `CreateDefaultCategoryItemViaForm.get_form_kwargs`
issues one `Category.objects.order_by("pk").first()` query per call of that one example-app
mutation. It is a read, so it sits inside the pipeline's read phase before
`pipeline_write_phase()` opens, and it costs the package nothing.)

### `review_inspect.py` run record

Run per `docs/builder/BUILD.md` `### When to run the helper during build` — the slice adds 50+
lines to files **outside** `django_strawberry_framework/` (measured: `test_resolvers.py` +297,
`test_sets.py` +202/-6, `test_products_api.py` +111, `products/schema.py` +43/-2,
`products/forms.py` +29/-2 against `HEAD`, the two `tests/forms/` figures being **mixed** with the
concurrent session's rows). Every invocation carried `--output-dir docs/shadow`; no shadow line
number is cited anywhere in this section. **No skips taken.**

| File | Result |
|---|---|
| `examples/fakeshop/apps/products/forms.py` | exit 0; 0 control-flow hotspots, 0 Django/ORM markers, repeated literals = `Meta.fields` names only |
| `examples/fakeshop/apps/products/schema.py` | exit 0; 0 control-flow hotspots; the new `UpdateItemWithFileViaForm` / `CreateDefaultCategoryItemViaForm` / its `get_form_kwargs` all enumerated; every Django/ORM marker is a pre-existing `DjangoType` / `get_queryset` entry in unchanged code |
| `examples/fakeshop/test_query/test_products_api.py` | exit 0; overview + stripped emitted |
| `tests/forms/test_sets.py` | exit 0; overview + stripped emitted |
| `tests/forms/test_resolvers.py` | exit 0; overview + stripped emitted |

Django/ORM marker walk: every entry the helper reports for the two example-app files sits in code
this pass did not touch, so each needs no justification of its own; the new code's only ORM touch
is the `Category.objects.order_by("pk").first()` read noted under `### Hot-path budget
verification`.

### Spec slice checklist walk

The Plan's `### Spec slice checklist (verbatim)` is Worker 1's own grading contract (this cycle's
Slice 1 has no spec `## Slice checklist` entry), all eleven boxes `- [x]`. Walked; no over-tick
found. Spot-verified: the five `review_inspect.py` shadow overviews for the named package files
are on disk; the `HEAD`-reference discipline is reproducible (all 20 paths resolve via
`git show HEAD:`, and I repeated it for the five writable files plus `sets_mixins.py` and
`tests/utils/test_inputs.py`); `D-1…D-19` accounts for 2 corrected + 1 partially refuted + 16
confirmed = **19**; the verdict-category collapse is arithmetically consistent. The final box
("Gap found -> implementation plan written, `Status: planned`") is correctly ticked — the current
`built` is Worker 2's later transition, not a contradiction.

### What looks solid

- **The mixed-diff enumeration in `### Notes for Worker 3` is exactly right, and I verified it
  rather than accepting it.** Diffing both files against `git show HEAD:` into a scratch path
  outside the repo: `test_sets.py` carries this pass's `_form_kwargs_overridden` import and
  `test_get_form_only_override_trips_the_construction_hook_waiver`, with the tuple-vs-list
  `permission_classes` re-pins, the four typed-hook rows, the two zero-arg/staticmethod rows and
  `test_form_shape_build_cache_clears_via_registry_and_direct_clear` belonging to the concurrent
  session; `test_resolvers.py` carries the `override_settings` import and this pass's four
  functions, with the three `_decode_form_relation_multi` rows theirs. Nothing of theirs was
  reverted or reformatted. Grading was confined to this pass's hunks.
- **The honest negative result is the best thing in the build report.** Recording that GAP-2's
  live row does not fail under the mutation, naming Django's widget contract as the reason, and
  saying outright that the row is "not what pins the disjunct" is what let me adjudicate the
  question at all. A pass that had quietly counted the live row would have read as 4 rows and
  invited no scrutiny.
- **Worker 2 overrode a discretion item for the right reason.** Worker 1 offered
  `scalars.MediaSpecimen` **or** `products.Item.attachment` as "equivalent"; they are not, and
  Worker 2 used both — `Item` for the end-to-end + FK-is-reconstructed leg, `MediaSpecimen`
  because it is the only model carrying a `FileField` **and** an `ImageField`, which is what
  turns the `ImageField`-subclass half into its own node id and lifts the boundary off a single
  row. Applying the acceptance rule to a discretion call is the behavior the rule wants.
- **GAP-1 was built as two node ids on purpose**, with the overrides-neither control kept
  *inside* the parametrized row precisely because promoting it would inflate the count without
  pinning anything. Both judgements are recorded and both are right.
- **The GAP-3 row's separation from the pre-existing validation-time row is genuinely
  mechanized**, not asserted: asserting the save-time mapper's own wording is provably reachable
  through exactly one call path, which is a stronger instrument than "no field-level error" alone.
- **Registry isolation holds.** `tests/forms/test_sets.py`'s autouse `_isolate_registry` clears
  before and after every test, so the new `type(...)`-declared mutations cannot leak into a later
  finalize; the full parallel sweep — the only instrument that can see this class — is green on
  that module twice.

### Temp test verification

Two temp tests, both under `docs/builder/temp-tests/slice-1/` (gitignored), written to test
review suspicions rather than to develop the fix.

- `docs/builder/temp-tests/slice-1/test_w3_file_widget_ignores_data_key.py` — 1 row, **passes**.
  Drives Worker 2's stated reason for the GAP-2 live row's non-failure without mutating any
  source. **Disposition: deleted at the end of this pass.** It proves a Django-internal fact
  (a file widget's `value_from_datadict` reads `files` only) that the package neither owns nor
  can regress, and the contract it supports is already pinned by the three direct
  `_reconstruct_partial_data` rows. Not promoted.
- `docs/builder/temp-tests/slice-1/test_w3_gap3_row_is_not_right_path_pinned.py` — 2 rows, both
  **pass**. Demonstrates the Medium finding above: `DefaultCategoryItemModelForm` with no
  `category` kwarg is still `is_valid()`, and `save()` still raises `IntegrityError`, so the live
  row cannot distinguish its documented driver. **Disposition: deleted at the end of this pass,
  and its content folded into the finding's recommended change** — the right permanent home is
  the positive leg on the existing live row, not a package row asserting a broken-fixture
  scenario.

### Notes for Worker 1 (spec reconciliation)

Nothing here duplicates Worker 1's own 31-item list or Worker 2's four items.

1. **`Escalated:` the scope fence has no home for the standing-doc drift this cycle created.**
   `TODAY.md` under-enumerates the products form-mutation surface in three places (six named,
   eight shipped) as a direct consequence of this pass's two new `Mutation` fields, and the build
   plan's `## Scope fence` puts `TODAY.md` out of every worker's reach. The fence was written for
   a cycle expected to touch only spec files and package `.py`; the GAP-3 escalation then
   authorized new example-app surface, which is exactly the change class that stales `TODAY.md`.
   Resolution paths for Worker 1 to pick between: **(a)** ask the maintainer to widen the fence by
   one file and have a Worker 2 pass re-pin the three `TODAY.md` sentences in the same cycle that
   caused the drift; **(b)** leave the fence and carry it into `bld-038-final.md`'s
   `### Deferred work catalog` as a named maintainer follow-up, quoting the three homes; **(c)**
   decide the drift is acceptable because the cycle's own charter excluded closeout surfaces — in
   which case say so explicitly in the artifact, because silence here is how a partial claim fix
   reopens a cycle. My grade: **(a)**, since the drift's cause and its fix are one change and
   `AGENTS.md` rule 14's same-change discipline is the repo's default.
2. **Decision 8 step 4's `get_form` clause is now pinned, and the spec's own step numbering is
   still the superseded draft order.** Worker 1's D-9 already owns the renumber; noting only that
   the two rows landing this pass (`test_get_form_only_override_trips_the_construction_hook_waiver`,
   `::test_get_form_only_override_builds_the_form_and_waives_the_required_guard`) cite the *hook*,
   not a step number, so the renumber cannot rot them.
3. **The `## Edge cases` file bullet needs the clause Worker 2's item 3 proposes, and this pass
   supplies the missing evidence for it.** I measured independently that **no wire-level row of
   any design** can detect the `FileField` disjunct's removal (temp test above: a stray `data=`
   key is inert because the widget reads `files` only). So the spec's "preserved … via its
   `initial`" sentence, read alone, invites a reader to believe a live test covers the exclusion —
   and for three patch releases none did. Worker 2's proposed append ("The reconstruction
   therefore contributes **no key at all** for a file field") is the right correction; this
   footnote is the executed proof behind it.
4. **DoD item 5 and the `## Test plan` live bullet stand as written** — the mock-free live
   `ModelForm` write-time `IntegrityError` row exists now, so the escalation's rejected
   alternative (rewriting both homes to cite the plain-form library row) stays rejected. Subject
   to the Medium above being closed: if the positive leg is not added, the row proves the
   envelope but not the driver, and Worker 1 should weigh whether DoD 5's "write-time" wording
   demands the specific uniqueness race or any post-validation database failure.

### Review outcome

`revision-needed`.

Two Medium findings. One is Worker 2's to close in a re-pass — GAP-3's live row needs the
positive leg that makes it distinguish its documented uniqueness driver from a NOT-NULL
degradation, and gives the new example-app surface its only happy-path assertion. The second is a
one-sentence qualification of the staleness sweep's population in the build report; its
substantive half (the `TODAY.md` drift) is escalated to Worker 1 because the scope fence puts it
beyond any worker. The Low findings are recorded with reasons and require no change.

Everything else clears: all three failability boundaries re-run at Worker 2's own scopes with
**zero node-id set difference**, none weakly pinned, zero collection errors, green same-scope
baselines, and every revert byte-proved twice over; the floor run happened as recorded with the
shared `.venv` untouched; the full parallel sweep shows the same four pre-existing failures and
no new one; the public surface is unchanged and no package `.py` is in the diff; and the GAP-2
live row is accepted with a stated reason it is not the worthless-wire-assertion case.


---

## Build report (Worker 2 — apply-changes pass)

One Worker 3 finding was mine to close and it is closed. **Files this pass modified: exactly
one** — `examples/fakeshop/test_query/test_products_api.py`. No package `.py` under
`django_strawberry_framework/` is in this pass's diff, and no `examples/fakeshop/apps/products/`
source needed a change: the positive leg drives the `get_form_kwargs` injection and the narrowed
`Meta.fields` that the prior pass already landed, so `forms.py` and `schema.py` are byte-identical
to their pre-pass state (proved below, since both were transiently mutated for the measurements).

### Per-finding disposition

| Worker 3 finding | Severity | Disposition |
| --- | --- | --- |
| GAP-3's live row is not right-path pinned | Medium | **Closed.** A positive leg landed as its own node id; the injection now fails a row when it breaks (0 -> 1, measured). |
| The staleness sweep's population excluded the repo-root standing docs (`TODAY.md`) | Medium | **Deferred — not this worker's to fix.** The build plan's `## Scope fence` names `TODAY.md` out of scope for the whole cycle, so no `TODAY.md` byte was touched. Its artifact-only half — qualifying the sweep's population — is discharged in `### The staleness sweep's population, qualified` below (a prior build report is never edited). Escalated to Worker 1 by Worker 3 with three resolution paths; one measured fact added for it under `### Notes for Worker 1 (spec reconciliation)`. |
| GAP-4's shape half is equality-only with no absolute anchor | Low | **Unchanged by design.** Worker 3 recorded it and required no change; the reason it gave (the only realistic regression is per-mutation and equality does catch it) holds and I did not weaken or extend the row. |
| Worker 2's `unset_sentinel` occurrence counts have already rotted | Low | **Unchanged by design.** Worker 3 required no change: a raw occurrence count of a file a concurrent session is writing is a moving figure, and the durable half (the declaration present at `HEAD`, absent in the working tree) re-derives. |

### Worker 3's evidence, re-derived rather than taken on trust

`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`. Worker 3's
temp test is gone (deleted at its own disposition), so nothing of theirs was reused. I measured
the gap **before** writing a line of test code, with the mechanized runner, mutating the exact
line the finding names:

- **Mutation:** `examples/fakeshop/apps/products/schema.py::CreateDefaultCategoryItemViaForm.get_form_kwargs`,
  `kwargs["category"] = models.Category.objects.order_by("pk").first()` **deleted** (anchor
  matched exactly once).
- **Scope:** `uv run pytest --no-cov … examples/fakeshop/test_query/test_products_api.py::test_create_default_category_item_via_form_write_time_integrity_error_uses_envelope -n0`.
- **Pre-mutation:** `1 passed`, exit 0. **Mutant:** `1 passed`, exit 0. **Rows failed: 0.
  Collection/setup errors: 0.** Restore proved: `filecmp.cmp(shallow=False)` True, sha256
  `1211626771da7688…` == `1211626771da7688…`.

So the finding is exact and not a reading of the code: with the injection the row exists to
demonstrate deleted entirely, the row stayed green. The positive leg closes a real gap rather
than decorating one. (Manifest for this preliminary run lived in the session scratchpad **outside
the repo**, not in the cycle's manifest — it measures the pre-fix state and is superseded by
entry 4 below, which carries the same mutation against the post-fix scope.)

### Files touched

Grounded in `git status --short` (151 dirty paths at the end of this pass; every other one is the
concurrent session's or a prior pass's — see `### Validation run`):

- `examples/fakeshop/test_query/test_products_api.py` — adds
  `_CREATE_DEFAULT_CATEGORY_ITEM_VIA_FORM` (the wire contract spelled once, the file's stated
  convention for its form-mutation query strings) and the positive-leg row; points the
  pre-existing negative row at the same constant; corrects two now-false prose statements (the
  negative row's docstring clause "no second row was written", and the section comment's
  enumeration of the products form-mutation surface).

Not touched, deliberately: `examples/fakeshop/apps/products/forms.py` and
`examples/fakeshop/apps/products/schema.py` (the prior pass's surface is sufficient — the row
needed no production or fixture change), `tests/forms/test_resolvers.py`,
`tests/forms/test_sets.py` (available to this pass, unused: the finding is live-tier), and
`TODAY.md` and every other surface the fence names.

### Tests added or updated

- `examples/fakeshop/test_query/test_products_api.py::test_create_default_category_item_via_form_injects_the_default_category`
  — **a separate node id**, not a second assertion block inside the existing row and not a `for`
  loop (`START.md` "Instruments that lie": a loop inside one test is ONE node id and can never
  raise a failability count above 1). It POSTs a non-colliding `name` through
  `createDefaultCategoryItemViaForm` and asserts the payload has no errors, the created `node`,
  and the stored row's `category_id` **equals the injected default**
  (`models.Category.objects.order_by("pk").first().pk`). *Property pinned:* the FK the narrowed
  input cannot carry arrives only through `get_form_kwargs`. The query is the minimal
  `node { name } errors { field messages } }` envelope so the row can only take the path it
  claims to test (`docs/builder/BUILD.md` `### Query-shape tests must pin the load-bearing
  property, not observability`, "Right-path tests").
- **The equality is guarded against being vacuous.** The row first asserts
  `models.Category.objects.exclude(pk=default_category.pk).exists()` — `seed_data` creates one
  `Category` per Faker provider, so the injected default is a real *selection* among many rather
  than the only candidate. Without that line the FK assertion could pass on a one-category
  fixture no matter which category the hook picked (`START.md`: never assert something the
  fixture size can satisfy by accident).
- **The pair is what distinguishes the driver**, which is Worker 3's own prescription: the
  positive leg fails if the injection breaks; the negative leg fails if the save-time mapper
  breaks. Both halves of the documented driver are now measured — see entries 4 and 5 below.
- The existing negative row keeps **every** assertion it had, including
  `messages == ["A database constraint was violated."]` and the `count() == 1` residue check.
  Nothing was weakened, deleted, or relaxed; the only edits to it are the shared query constant
  and the docstring clause its own falsification required.
- `create_users(1)` + `seed_data(1)` open the new row, per `AGENTS.md` rule 8.

### Failability proofs

**No proof is owed for this pass, and the rule that exempts it is
`docs/builder/BUILD.md` `### What needs a proof, and what does not`:** the obligation is scoped to
"every **new boundary, guard, gate, or rejection path** a slice introduces — anything whose job is
to say 'no', hold an invariant, or fail closed." This pass introduces none. It adds one test row;
no package `.py` is edited at all, and the two example-app symbols the row exercises
(`CreateDefaultCategoryItemViaForm.get_form_kwargs`, `DefaultCategoryItemModelForm.Meta`) are
**pre-existing acceptance-fixture wiring** landed by the prior pass — a construction hook whose
job is to hand the form a kwarg, not to reject anything. The one production boundary in this seam,
`django_strawberry_framework/forms/resolvers.py::_modelform_write_step`'s `save_or_field_errors`
wrap, was proved by the prior pass at **2 rows** and independently re-run by Worker 3 with zero
node-id set difference; this pass does not change it. The new row cannot fail under that mutation
(no `IntegrityError` occurs on the happy path), so entry 3's node-id set is unchanged by
construction, and I did not re-run it.

**What is recorded instead is a right-path measurement**, owed by
`### Query-shape tests must pin the load-bearing property, not observability` rather than by the
proof rule. It was run through the same mechanized runner so every field is measured in the
process that made the mutation, appended to the cycle's manifest at the mandated path
(`docs/builder/temp-tests/slice-1/proofs.json`, now 5 entries) and executed with `--only`, so both
emitted blocks are labelled **PARTIAL RECORD**:

```shell
uv run python scripts/prove_failability.py docs/builder/temp-tests/slice-1/proofs.json \
    --only "CreateDefaultCategoryItemViaForm" --output docs/builder/temp-tests/slice-1/proofs-pass2.md
uv run python scripts/prove_failability.py docs/builder/temp-tests/slice-1/proofs.json \
    --only "DefaultCategoryItemModelForm.Meta" --output docs/builder/temp-tests/slice-1/proofs-pass2-narrowing.md
```

Both mutated files are **example-app** files, both anchors matched exactly once, the scratch root
is `…/scratchpad/failability` — **outside the repository** — `git` was never invoked, and each
restore was proved by byte comparison before the next entry.

| # | Site | File mutated | Mutation applied | Rows failed | Errors | Scope as run | Restore proof |
|---|---|---|---|---|---|---|---|
| 4 | `examples/fakeshop/apps/products/schema.py::CreateDefaultCategoryItemViaForm.get_form_kwargs` | `examples/fakeshop/apps/products/schema.py` | deleted: `kwargs["category"] = models.Category.objects.order_by("pk").first()` — the injection removed, so the form is constructed with no `category` kwarg and the narrowed input cannot supply one | **1** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE examples/fakeshop/test_query/test_products_api.py::test_create_default_category_item_via_form_injects_the_default_category examples/fakeshop/test_query/test_products_api.py::test_create_default_category_item_via_form_write_time_integrity_error_uses_envelope -n0` | `filecmp.cmp(shallow=False)` True; sha256 `1211626771da7688…` == `1211626771da7688…` |
| 5 | `examples/fakeshop/apps/products/forms.py::DefaultCategoryItemModelForm.Meta` | `examples/fakeshop/apps/products/forms.py` | `fields = ("name",)` -> `fields = ("name", "category")` — the narrowing undone, so `_get_validation_exclusions` keeps `category` and `_post_clean`'s `validate_constraints()` catches the collision **before** the write | **2** | 0 | same scope as entry 4 | `filecmp.cmp(shallow=False)` True; sha256 `353389ecf425a8d5…` == `353389ecf425a8d5…` |

Failing node ids, per entry (the count is `len()` of the list, never asserted):

4. `examples/fakeshop/apps/products/schema.py::CreateDefaultCategoryItemViaForm.get_form_kwargs`
   - pytest summary: `========================= 1 failed, 1 passed in 2.90s ==========================`; exit code 1
   - pre-mutation state of this scope: `============================== 2 passed in 2.83s ===============================` (exit 0); pre-existing failing rows differenced out: 0
   - collection/setup errors: 0
   - `examples/fakeshop/test_query/test_products_api.py::test_create_default_category_item_via_form_injects_the_default_category`
   - **The row that did NOT fail is the measurement's second finding:** the negative row
     `::…_write_time_integrity_error_uses_envelope` was inside this scope and **passed** under the
     mutation, exactly as Worker 3 predicted and as my pre-fix run showed at 0 rows. That is
     Worker 3's Medium re-derived independently and it is why the positive leg is not decoration.
5. `examples/fakeshop/apps/products/forms.py::DefaultCategoryItemModelForm.Meta`
   - pytest summary: `============================== 2 failed in 2.87s ===============================`; exit code 1
   - pre-mutation state of this scope: `============================== 2 passed in 2.94s ===============================` (exit 0); pre-existing failing rows differenced out: 0
   - collection/setup errors: 0
   - `examples/fakeshop/test_query/test_products_api.py::test_create_default_category_item_via_form_injects_the_default_category`
   - `examples/fakeshop/test_query/test_products_api.py::test_create_default_category_item_via_form_write_time_integrity_error_uses_envelope`

**Reading the runner's `WEAKLY PINNED` verdict on entry 4, stated plainly rather than left for the
reviewer to trip over.** The runner applies `### Acceptance rule: weakly pinned is
`revision-needed`` to every entry it is handed, and at 1 failing row it printed that verdict and
exited 1. It is not a violation here, for a reason the tool cannot see: **the mutated line is not a
boundary.** The acceptance rule and the proof obligation share one subject — "a new boundary,
guard, gate, or rejection path" — and a `get_form_kwargs` override in an example app is
construction wiring that says "no" to nothing. What the rule protects against is a package
invariant resting on a single assertion; what entry 4 measures is that a fixture seam previously
resting on **zero** assertions now rests on one that is exactly targeted at it. The two entries
together are the honest answer to "is the pair right-path pinned?": the driver has two halves, the
**injection** (entry 4, caught by the positive leg) and the **narrowing** (entry 5, caught by
both rows), and each half now fails at least one row when removed. Adding further rows over the
same one hook to move a number would be padding, which is the opposite of what the rule asks for.
No zero-row entry exists in this pass, so no `why 0` slot is owed.

**Independent confirmation that no mutation survives**, beyond the runner's own `filecmp` +
SHA-256: no `ACTIVE-MUTATION.json` and no `RESTORE-FAILED.json` exists under either scratch root;
each anchor matches exactly once again in the working tree (`grep -c` -> `1`, `1`); and an explicit
`cmp` of **every** pristine copy in both scratch roots against its live file prints identical —
`examples/fakeshop/apps/products/schema.py` (against both the preliminary and the entry-4 copy),
`examples/fakeshop/apps/products/forms.py`, and, carried over from the prior pass and re-checked
here, `django_strawberry_framework/forms/sets.py` and
`django_strawberry_framework/forms/resolvers.py` against **both** of its copies. `git diff --stat
-- django_strawberry_framework/forms/` shows only the concurrent session's three-file hunk set,
unchanged.

### The staleness sweep's population, qualified

Worker 3's second Medium asked for a one-sentence qualification of the prior build report's
"Nothing needed re-pinning". A prior build report is never edited (`worker-2.md`
`### Pass-name and status conventions`), so the qualification lands here: **that claim holds for
the population it measured — `tests/**` plus `examples/fakeshop/**` (302 files, `.py` plus the
`.md` files in those two trees) — and for nothing outside it.** The repo root is outside it, and
`TODAY.md` is the one file there that enumerates the products form-mutation surface by wire name.
Worker 3 re-derived the sweep independently over the same population and got the same answer, so
the defect is the population's edge, not the sweep's arithmetic.

**This pass adds no schema field**, so no new staleness of that class is created: the products
`Mutation` field set is unchanged from the state Worker 3 reviewed, the SDL is unchanged, no
example app or schema module was added, and the two private schema-module enumerations
(`examples/fakeshop/schema_reload.py #"_PROJECT_APP_SCHEMA_MODULES = ("`,
`examples/fakeshop/tests/test_inspect_django_type.py #"_SCHEMA_MODULES = ("`) already carry
`apps.products.schema`. Verified by the FULL parallel sweep, not a focused run.

**One enumeration inside the sweep's own population was stale, and it is fixed in this diff.** The
section comment at `examples/fakeshop/test_query/test_products_api.py`
#"# Form-mutation live surface (spec-038 / Decision 12). The products" enumerated the products
form-mutation surface in prose and named **five** of the eight fields — it predates
`updateItemWithFileViaForm` and `createDefaultCategoryItemViaForm` (this cycle's) and had never
named `submitPing` (older). It now names all eight. Two notes on grading it: the prior report's
sentence "every hit is either the declaration in `products/schema.py` or a per-row query string in
`test_products_api.py`" was therefore one category short — a prose enumeration in a comment is
neither — and the count in the corrected comment is **measured, not asserted**: a regex pass over
`products/schema.py` finds 8 classes subclassing `DjangoModelFormMutation` / `DjangoFormMutation`
and 8 `DjangoMutationField(...)` rows wiring exactly those 8 onto `Mutation`. Nothing cites that
comment (`grep` for its distinctive first line over the whole repo: **1 occurrence**, the comment
itself), so no citation rotted.

### Validation run

- `uv run ruff format examples/fakeshop/test_query/test_products_api.py` — pass
  (`1 file left unchanged`). Scoped to this pass's own file, never `.`.
- `uv run ruff check --fix examples/fakeshop/test_query/test_products_api.py` — pass
  (`All checks passed!`).
- `uvx pre-commit run --files examples/fakeshop/test_query/test_products_api.py` — **all six hooks
  pass** on the first run, `citations resolve` included; nothing was auto-fixed, so nothing needed
  re-staging.
- `uv run pytest examples/fakeshop/test_query/test_products_api.py -n0 --no-cov` (focused) —
  **135 passed** (134 before this pass; +1 node id).
- `uv run pytest --no-cov` (**FULL parallel**) — **4 failed, 7240 passed, 40 skipped**,
  **0 collection errors**. The four are the same pre-existing
  `ActiveInputPermissionAttrs.__init__() got an unexpected keyword argument 'unset_sentinel'`
  rows Worker 3 measured (`tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key`,
  `tests/orders/test_inputs.py::test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration`,
  `tests/test_sets_mixins.py::test_permission_family_config_stays_on_each_set_class`,
  `tests/test_sets_mixins.py::test_filter_normalizer_honors_a_subclass_unset_sentinel_override`).
  **No fifth failure and no collection error**, so the population is a valid population: this
  pass adds nothing to the failure set. Not fixed, not reverted, not worked around — they trace to
  the concurrent session's uncommitted `sets_mixins.py`, a baseline-dirty out-of-scope file.
  The passed count moved 7231 -> 7240 across Worker 3's run and mine; +1 is this pass's row and
  the rest is the concurrent session's own additions landing in between, which is why the
  node-id set and not the count is what was compared.
- `uv run python examples/fakeshop/manage.py check` — `System check identified no issues (0
  silenced).`
- `git status --short` after both ruff invocations — **151 paths**. `examples/fakeshop/test_query/test_products_api.py`
  is the only one this pass modified. `examples/fakeshop/apps/products/forms.py`,
  `examples/fakeshop/apps/products/schema.py`, `tests/forms/test_resolvers.py` and
  `tests/forms/test_sets.py` are dirty from the prior build pass (and, for the two `tests/forms/`
  files, mixed with the concurrent session's rows); the cycle's five untracked artifacts are
  present; everything else is the concurrent session's. **Nothing was reverted** — this tree
  carries another session's uncommitted work and `git checkout -- <path>` would destroy it.
- No `--cov*` flag was used in any command this pass. Every `pytest` invocation carried
  `--no-cov`, the runner adds it itself, and the floor run below carries it too.

### Hot-path budget

`Not applicable; plan declares no hot path.` Re-confirmed against the diff as landed: this pass's
diff is one test file. The hot-path declaration carried in the task contract is `none` for the
same reason — no package `.py` is edited, so no per-request, per-resolver, per-row,
per-connection or per-outbound-message cost can have been added. No before/after number is owed.

### Floor verification

Already discharged by the prior build pass for both GAP-2 and GAP-3 scopes and verified by Worker
3 (the shared `.venv` untouched). **The new leg does not change what the GAP-3 focused floor scope
covers** — that scope is `-k "with_file or integrity"` and the new node id
(`…_injects_the_default_category`) matches neither substring, so the prior selection is unchanged
and no re-run was strictly owed.

**I ran it anyway**, because the venv was still present and the new row exercises the same Django
validation / `save()` seam the scope exists for; a cheap execution beats an argument that
execution was unnecessary (`docs/builder/BUILD.md` `## Floor verification`: the floor is executed,
never reasoned). Nothing was installed — no `uv pip install` ran at all this pass, so the shared
`.venv` could not have been a target.

- **Scratch venv path:** `/tmp/dsf-floor` (outside the working tree; built by the prior pass).
- **Resolved versions, as read** by `uv pip list --python /tmp/dsf-floor/bin/python`: `django
  5.2.16`, `strawberry-graphql 0.316.0`, `django-filter 26.1`;
  `/tmp/dsf-floor/bin/python -c "import sys; print(sys.version)"` -> `3.10.19 (main, Jan 27 2026,
  23:32:40) [Clang 21.1.4]`. That is exactly the floor `docs/builder/BUILD.md`
  `## Floor verification` states: Django **5.2.16** on Python **3.10** with strawberry-graphql
  **0.316.0**.
- **Focused scope and result:** `/tmp/dsf-floor/bin/python -m pytest
  examples/fakeshop/test_query/test_products_api.py -k "default_category" --no-cov -n0` ->
  **2 passed, 133 deselected** (`django: version: 5.2.16` in the header). **PASS.** The selection
  is the whole GAP-3 pair, positive leg included.
- **The shared `.venv` is unchanged**, verified after the floor run by `uv pip list`: `django 6.1`,
  `strawberry-graphql 0.324.0`, `django-filter 26.1` — the newest supported set, not the floor.
  (Recorded as a reading; that section bans stating it from memory.)

### Implementation notes

- **A separate node id, not a second assertion block, and not a parametrized case.** Worker 3
  allowed either a separate row or a parametrized case. There is no natural axis to parametrize —
  one hook, one injected value — so a `parametrize` would have been a one-case decoration. A
  second assertion block inside the existing row was ruled out for the reason the contract gives:
  it would leave one node id, and a green negative row would keep masking a broken injection.
- **The row asserts the stored FK, not the wire.** The mutation's `node` selection cannot carry
  `category` (it is narrowed out of the input, and the envelope's `node { name }` is minimal by
  design), so the distinguishing observation is `created.category_id` read back from the DB — the
  production call site's own effect. This is the same lesson the prior pass measured for GAP-2:
  where the wire cannot see the property, assert it where the property lives.
- **Why the existence check on a second `Category` earns its line.** Without it the FK equality
  would be satisfiable by any implementation on a single-category fixture. With it, the row states
  the hook's actual contract: *this* category — the lowest-pk one the override picks — out of many.
- **The query constant, not a third inline copy.** The wire string is now used by two rows;
  `### Severity definitions` grades a repeated literal that should be a named constant as Medium,
  and the file's own comment says each form-mutation wire contract is "spelled once". It is
  defined immediately above its two users rather than in the 700-lines-earlier constant block,
  matching how the file already places `_CATEGORIES_ITEMS_CONNECTION_QUERY` and
  `_MULTIBYTE_CATEGORY_NAME` next to their rows. The pre-existing twice-inlined
  `createItemWithFileViaForm` string was left alone — not this pass's scope.
- **The negative row's docstring clause had to change.** It ended "no second row was written",
  which this pass falsifies; leaving it would ship a false statement about the file's own
  contents. It now states the pair relationship, which is the property a future reader needs.
  `AGENTS.md`'s no-process-provenance rule is respected: the replacement states the invariant, not
  the review round that produced it.

### Notes for Worker 3

- **The diff on `examples/fakeshop/test_query/test_products_api.py` contains this pass's hunks
  only** — it was NOT baseline-dirty from the concurrent session; the prior build pass's two rows
  in it are already in the artifact's record. This pass's hunks are: the section comment's
  enumeration, `_CREATE_DEFAULT_CATEGORY_ITEM_VIA_FORM`,
  `test_create_default_category_item_via_form_injects_the_default_category`, and the two lines the
  negative row changed (its query argument and its docstring clause).
- **`examples/fakeshop/apps/products/forms.py` and `schema.py` are in `git status` but NOT in this
  pass's diff.** Their dirty hunks are the prior pass's. Both were transiently mutated for entries
  4 and 5 and both are byte-identical to their pristine copies now; the `cmp` results are in
  `### Failability proofs`. If you re-run either entry, the anchors are unique and the scope is two
  node ids, so a run costs ~6 s.
- **Re-run entries 4 and 5 at the scope recorded**, `-n0` included, and compare node-id **sets**:
  entry 4's whole point is which of the two rows fails and which does not. Widening the scope to
  the whole file would add rows that cannot fail and shrink nothing but the record's clarity.
- **The runner exits 1 on entry 4** and prints `WEAKLY PINNED`. My ruling on why that is not a
  violation is stated in full in `### Failability proofs` rather than left implicit; if you
  disagree, the disagreement is about whether an example-app construction hook is a "boundary"
  under `### What needs a proof, and what does not`, which is the one question worth settling —
  not about the measurement, which is reproducible either way.
- **No temp tests were created.** Worker 3's own GAP-3 temp test no longer exists on disk (its
  disposition deleted it), so nothing was promoted out of `docs/builder/temp-tests/`; the
  directory now holds only the manifest and the three emitted proof reports.
- **`scripts/review_inspect.py` was not run**, deliberately: `### When to run the helper during
  build` scopes Worker 2's use to "when the plan or prior review asks for it", and neither does —
  no new `.py` file, nothing under `optimizer/` or `types/`, and zero lines of new logic under
  `django_strawberry_framework/`. Worker 1's five overviews from the grading pass are still under
  `docs/shadow/`.

### Notes for Worker 1 (spec reconciliation)

On disk, per `worker-2.md` `### Spec amendments go on disk, not in the return message`. Nothing
here duplicates Worker 1's 31-item list, this pass's predecessor's four items, or Worker 3's four.

1. **The products form-mutation count did NOT move again, and the figure is now measured.** Where
   it lives: the prior build report's `### Notes for Worker 1 (spec reconciliation)` item 2, which
   asks Slice 2 to replace "`products` (6 form mutations)" with **8** and names them. That item
   stands unchanged — this pass added a test row, not a `Mutation` field. Confirming the figure
   mechanically so Slice 2 does not have to: a regex pass over
   `examples/fakeshop/apps/products/schema.py` finds **8** classes subclassing
   `DjangoModelFormMutation` / `DjangoFormMutation` and **8** `DjangoMutationField(...)`
   assignments wiring exactly those onto `Mutation` — `createItemViaForm`, `updateItemViaForm`,
   `createItemWithFileViaForm`, `updateItemWithFileViaForm`,
   `createDefaultCategoryItemViaForm`, `createStampedItemViaForm`, `submitContact`, `submitPing`.
   The deferred `TODAY.md` catalog entry Worker 3 escalated therefore concerns **the same eight
   names**, and no path (a), (b) or (c) needs a recount.
2. **DoD item 5 and the `## Test plan` live bullet now stand without the caveat Worker 3 attached
   to them.** Where they live: DoD item 5 ("**a write-time `IntegrityError` returning the
   `FieldError` envelope** (P1)") and the `## Test plan` live "**Write-time `IntegrityError`**"
   bullet. Worker 3's note 4 made them conditional — "*Subject to the Medium above being closed:
   if the positive leg is not added, the row proves the envelope but not the driver*". The
   positive leg is added and measured, so the condition is discharged and **no wording change is
   owed to either home**: the spec's specific uniqueness race is what the pair drives, not merely
   "any post-validation database failure". Recommended replacement: none — close both with the
   two node ids
   `examples/fakeshop/test_query/test_products_api.py::test_create_default_category_item_via_form_injects_the_default_category`
   and `::test_create_default_category_item_via_form_write_time_integrity_error_uses_envelope`
   cited as a pair, since either alone under-determines the contract.
3. **A one-clause addition worth making where the spec describes the `get_form_kwargs` hook, and
   this pass supplies the executed evidence for it.** Where it lives: Decision 8's
   `get_form_kwargs` step (the same step the prior pass's item 4 proposes rewording). Current
   wording quoted: "or to scope a `ModelChoiceField.queryset` **without changing the generated
   input shape**". Recommended replacement: keep the prior pass's proposed rewording and append —
   "A hook that injects a value the narrowed input cannot carry is only observably working if a
   test asserts the **written row**: the wire envelope of a failed write is identical whether the
   injection ran or not, because a missing non-nullable FK raises `IntegrityError` too and maps to
   the same `"__all__"` envelope." Why: measured here as entry 4 — deleting the injection left
   the write-time row green, and only a positive leg reading back `category_id` distinguishes the
   two. A reader taking the current sentence at face value will believe the negative row covers
   the hook, which is the same class of false confidence the prior pass recorded for the file
   exclusion.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

[build-md]: BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->


---

## Review (Worker 3, pass 2)

### Independent failability re-runs — recorded BEFORE any mutation is applied

`docs/builder/worker-3.md` "Reading is necessary, not sufficient" sets the mandatory floor at
every boundary whose recorded failing-row count is `<= 3`. This pass's two new measurement
entries are recorded at **1** and **2** rows, and entry 3 (the one production boundary in the
seam, recorded at **2**) has a scope that contains **whole files** — including
`examples/fakeshop/test_query/test_products_api.py`, whose population this pass changed by one
row. All three are therefore inside the floor and all three are re-run. Entries 1 and 2 are
untouched by this pass's diff and stay accepted on the prior review's own zero-difference
re-run, per the re-review's declared scope.

Recorded here before anything is mutated, per the source carve-out (`worker-3.md` "Scope"):

1. **Entry 4** — `examples/fakeshop/apps/products/schema.py::CreateDefaultCategoryItemViaForm.get_form_kwargs`:
   the line `kwargs["category"] = models.Category.objects.order_by("pk").first()` is
   **deleted**, so the form is constructed with no `category` kwarg and the narrowed input
   cannot supply one.
2. **Entry 5** — `examples/fakeshop/apps/products/forms.py::DefaultCategoryItemModelForm.Meta`:
   `fields = ("name",)` becomes `fields = ("name", "category")`, undoing the narrowing so
   `_post_clean`'s `validate_constraints()` catches the collision before the write.
3. **Entry 3** — `django_strawberry_framework/forms/resolvers.py::_modelform_write_step`:
   `write_error = save_or_field_errors(form.save)` becomes `form.save()` + `write_error = None`,
   removing the save-time mapper.

**Anchor pre-check, run first and before any copy** (`docs/builder/BUILD.md`
`## Failability proofs`: nothing else in the loop can tell that its own reference is already
mutated). `grep -c` over the live tree for all five manifest anchors printed `1` each —
including entries 1 and 2, which this pass does not re-run — so the tree carried **no** live
mutation inherited from any prior pass or any concurrent session.

Each mutation is applied by `scripts/prove_failability.py` with `--scratch-root` under my own
session scratchpad **outside** the repository, one entry at a time, restored and byte-proved
before the next. `git stash` / `checkout` / `restore` / `worktree` were never run.

### Re-run results — node-id SET comparison

Runner: `uv run python scripts/prove_failability.py <my own manifest> --only <N> --output <scratch>`,
one entry per invocation. My manifest is
`docs/builder/temp-tests/slice-1/proofs.json` copied byte-for-byte except `scratch_root`, so every
anchor, replacement and scope is identical to Worker 2's. All three blocks are labelled
**PARTIAL RECORD** by the tool, correctly — they are an independent re-run of a subset, which is
what `--only` exists for.

| # | Boundary / site | W2 rows | W3 rows | Node-id SET | Baseline (same scope) | Coll./setup errors | Restore sha256 |
|---|---|---|---|---|---|---|---|
| 3 | `django_strawberry_framework/forms/resolvers.py::_modelform_write_step` | 2 (prior pass) | **2** | **identical** | `203 passed`, exit 0 | 0 | `83079ddaa148d40e…` == |
| 4 | `examples/fakeshop/apps/products/schema.py::CreateDefaultCategoryItemViaForm.get_form_kwargs` | 1 | **1** | **identical** | `2 passed`, exit 0 | 0 | `1211626771da7688…` == |
| 5 | `examples/fakeshop/apps/products/forms.py::DefaultCategoryItemModelForm.Meta` | 2 | **2** | **identical** | `2 passed`, exit 0 | 0 | `353389ecf425a8d5…` == |

The sets, not the totals:

3. `tests/forms/test_resolvers.py::test_modelform_save_integrity_error_maps_to_envelope`;
   `examples/fakeshop/test_query/test_products_api.py::test_create_default_category_item_via_form_write_time_integrity_error_uses_envelope`.
4. `examples/fakeshop/test_query/test_products_api.py::test_create_default_category_item_via_form_injects_the_default_category`
   — and the row that did **not** fail is half the measurement: the negative row was inside this
   scope and passed, which is the prior review's Medium re-derived a third time, by me, with the
   injection deleted.
5. `examples/fakeshop/test_query/test_products_api.py::test_create_default_category_item_via_form_injects_the_default_category`;
   `…::test_create_default_category_item_via_form_write_time_integrity_error_uses_envelope`.

**Entry 3 was re-run even though this pass does not change it, and the reason is the scope, not
distrust.** Entry 3's recorded scope is two **whole files**, one of them
`examples/fakeshop/test_query/test_products_api.py`, whose population this pass grew by one row.
A recorded node-id set over a scope whose population has changed is not self-evidently still the
same set, and the recorded count of 2 sits inside the mandatory re-run floor. Measured: the set is
unchanged and the new positive-leg row does **not** fail under the mapper's removal — which is
what Worker 2 argued from the code and is now measured rather than reasoned. The baseline moved
`202 -> 203 passed`, exactly the +1 row.

**Boundaries re-run this pass: entries 3, 4 and 5.** Entries 1 and 2
(`forms/sets.py::_form_kwargs_overridden`, `forms/resolvers.py::_reconstruct_partial_data`) are
**accepted on the prior review's own independent re-run** — zero set difference at Worker 2's
scopes — and are untouched by this pass's diff; the re-review's declared scope keeps them closed.

**No mutation survives, verified four ways.** No `ACTIVE-MUTATION.json` / `RESTORE-FAILED.json`
anywhere under either scratch root or in the repo; all **five** manifest anchors match exactly
once in the live tree after the runs (`grep -c` -> `1` five times); **12 pristine copies across 4
scratch roots** (Worker 2's original, Worker 2's pass-2, the prior review's, and mine) byte-compare
`IDENTICAL` to their live files, 0 differing, via `filecmp.cmp(shallow=False)` over the mangled
copy names decoded back to repo paths — my first attempt at that comparison silently produced
**zero** comparisons because it mis-parsed the runner's `<hash>__a__b__c.py` naming into a path
that does not exist, printed only "no live file for …", and would have read as a clean sweep if I
had not required a per-file `IDENTICAL` line and a nonzero compared-count (`START.md` "Instruments
that lie": always print the population size); and the live `git diff HEAD` for
`products/forms.py` / `products/schema.py` shows `fields = ("name",)` and the
`kwargs["category"] = …` injection both present, i.e. the two mutations' inverses are absent from
the tree. `git stash` / `checkout` / `restore` / `worktree` were never run.

### The failability-exemption ruling — Worker 2's reasoning is accepted

Two questions were open. Both are decided against the rules' own wording, not by deference.

**1. Does `### Acceptance rule: weakly pinned is `revision-needed`` reach entry 4?** **No.** The
rule's subject is a *boundary*: "A boundary is **weakly pinned** when removing it makes 0 or 1 test
rows fail." `docs/builder/BUILD.md` `### What needs a proof, and what does not` defines that
subject and nothing else does — "every **new boundary, guard, gate, or rejection path** a slice
introduces — anything whose job is to say 'no', hold an invariant, or fail closed", and expressly
**not** every changed line. `examples/fakeshop/apps/products/schema.py::CreateDefaultCategoryItemViaForm.get_form_kwargs`
hands a form a constructor kwarg. It refuses no input, holds no invariant, and fails nothing
closed; deleting it does not permit anything that was previously refused. It is acceptance-fixture
construction wiring in an example app, outside the coverage gate. Two independent reasons the rule
does not bind it, and either alone suffices: it is not a boundary, **and** it is not new to this
pass — the prior pass landed it and the prior review accepted it. This pass's diff introduces
zero production code, so `### What needs a proof, and what does not` owes it no proof at all, and
a rule scoped to boundaries cannot be triggered by a measurement voluntarily recorded over a
non-boundary. The runner's `WEAKLY PINNED` verdict and exit 1 are the tool applying the rule to
every entry it is handed, which its own `--help` and report text say it does; that is not a finding
against the pass. Had the rule applied, its stated remedy — "more or better-targeted rows" — has
no target here: one hook, one injected value, no second axis, so further rows would be padding,
which the rule explicitly is not asking for.

**2. Is the two-entry measurement sufficient to close the prior review's Medium?** **Yes, and it is
the right instrument.** The finding was that the negative row is satisfied identically by a
NOT-NULL degradation, so a broken injection leaves it green and nothing anywhere asserts the
injection works. Closing that needs exactly one thing: a row that fails when the injection breaks.
Entry 4 measures it directly — injection deleted, the positive leg fails, the negative row still
passes. Entry 5 covers the other half of the documented driver — narrowing undone, both rows fail,
so the row's claim to be a *post-validation* failure is pinned too. Entry 3 covers the mapper.
Every half of the driver the row documents now fails at least one row when removed, and the two
halves are distinguishable from each other by which rows fail. The pair, not the count, is the
property `### Query-shape tests must pin the load-bearing property, not observability` asks for.

### High:

None.

### Medium:

None.

### Low:

#### The stated reason for the docstring edit does not match what the retired clause said — the assertion it described is intact

`### Implementation notes` says the negative row's docstring "ended 'no second row was written',
which this pass falsifies". Adding a **sibling test function** does not falsify a clause describing
that row's own `assert models.Item.objects.filter(...).count() == 1`, and that assertion is still
present verbatim in the row. The parallel phrase survives untouched one row earlier, at
`examples/fakeshop/test_query/test_products_api.py`
#"`node` is null, exactly one `errors` entry, no second row written." — the pre-existing
validation-time row, which is not in this pass's diff at all.

**No assertion was lost, which is the check that mattered** (`docs/builder/BUILD.md`: a docstring
edit is the cheapest place to lose one). I enumerated the negative row's assertions against the
Plan's `#### GAP-3` fix plan and against the prior review's own description of the row, and all
seven survive: `status_code == 200`; `"errors" not in payload`; `result["node"] is None`;
`len(result["errors"]) == 1`; `field == "__all__"`; `messages == ["A database constraint was
violated."]` (the save-time mapper's own wording, the row's separation from the validation-time
row); and the `count() == 1` residue check. The only executable change to that row is its query
argument becoming the shared constant. The replacement prose is accurate, states the invariant,
and carries no process provenance. **No change required** — the defect is in a per-cycle
artifact's account of an edit, not in the edit or the test.

#### The injection now rests on one row, and that is the honest ceiling here

Entry 4's single row is not a weakly-pinned boundary (ruled above), but it is worth naming that a
refactor retiring `::test_create_default_category_item_via_form_injects_the_default_category` would
return the injection to zero assertions. There is no second row to add that would not be a copy:
the hook has one injected value and the FK read-back is the only observable, since the narrowed
input cannot carry `category` on the wire. Recorded, not required.

### DRY findings

- **The extracted query constant is the right direction, and it is placed the way the file already
  places such constants.** `_CREATE_DEFAULT_CATEGORY_ITEM_VIA_FORM` replaces what would have been a
  second inlined copy of the wire string; `### Severity definitions` grades a repeated literal that
  should be a named constant as Medium, so this is a Medium avoided rather than a finding. Placed
  immediately above its two users, matching `_CATEGORIES_ITEMS_CONNECTION_QUERY` /
  `_MULTIBYTE_CATEGORY_NAME`. Leaving the pre-existing twice-inlined `createItemWithFileViaForm`
  string alone was correct — out of this pass's scope, and the prior review had not raised it.
- **Existence challenge on the positive leg: it earns its existence, decisively.** Its one real
  competitor was a second assertion block inside the negative row, and that is exactly the shape
  the finding it closes forbids — one node id, and a green negative row would keep masking a broken
  injection (`START.md` "Instruments that lie": a `for` loop, or a second block, inside one test is
  ONE node id and can never raise a failability count above 1). Measured proof that the separate
  node id is load-bearing: entry 4 fails **1** row and it is this one. Nothing to delete.
- **The repeated-literal output carries nothing new.** `scripts/review_inspect.py` on the changed
  file reports the file's established live-suite vocabulary (`47x categoryId`, `45x view_item_1`,
  `41x products.category`, `36x add_item`) — all pre-existing across ~140 rows, and the file's own
  idiom. This pass added one new literal used once (`"RaceFormFresh"`) plus the query constant. The
  new row appears in no control-flow-hotspot entry and in no Django/ORM-marker entry (every marker
  the helper reports sits in code this pass did not touch). No finding.
- **`create_users(1)` + `seed_data(1)` + `_login_with_perm("view_item_1", "add_item")` repeated in
  the new row** is `AGENTS.md` rule 8's mandated first line plus the file's permission idiom, not
  duplication to consolidate.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** — the file is not even dirty
against `HEAD` (`git diff --stat HEAD --` prints nothing). `__all__` and the re-export list are
unchanged. Verified independently that no package `.py` is in this pass's diff at all: the pass's
one file is `examples/fakeshop/test_query/test_products_api.py`, and the dirty package files are
the concurrent session's baseline-dirty set.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. Confirmed by byte-compare, not by reading the
dirty list: `CHANGELOG.md` does not appear in `git status --short` at all.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. This pass edited one
docstring clause and one section comment, both inside a test file that feeds no generated doc, so
neither the script-rendered-doc check nor the staging-language check has a target. Checked anyway
because the comment carries a **count**, and a count is a claim:

- **The section comment's "eight fields in all" is re-derived, not accepted.**
  `^class .*\((DjangoModelFormMutation|DjangoFormMutation)\):` over
  `examples/fakeshop/apps/products/schema.py` -> **8** (`CreateItemViaForm`, `UpdateItemViaForm`,
  `CreateItemWithFileViaForm`, `UpdateItemWithFileViaForm`, `CreateDefaultCategoryItemViaForm`,
  `CreateStampedItemViaForm`, `SubmitContact`, `SubmitPing`), and the `Mutation` body carries
  exactly **8** matching `DjangoMutationField(...)` rows. The comment now names all eight by wire
  name; before this pass it named five. Correct, and the widening — not an appended row — is what
  the "count this comment must keep" clause makes maintainable.
- **The comment is not a citation target.** `check_citations.py` covers `path::Symbol` only, but
  the citation gate ran green anyway as part of pre-commit below.

### Independent staleness sweep, run against my own population

`worker-3.md`'s delta is explicit: run the sweep independently, never against the slice's
enumerated file list. Mine is the **whole repository** — 5463 files across `.py` / `.md` / `.html`
/ `.json` / `.graphql` / `.txt` / `.csv` / `.toml` / `.yml` / `.yaml`, excluding only `.git`,
`.venv` and cache dirs — which is a strict superset of the prior sweep's 302-file
`tests/**` + `examples/fakeshop/**` population and of the repo root the prior review named as its
blind spot. All eight products form-mutation wire names, occurrences and files printed:

- The only **enumeration** homes outside `products/schema.py` and `test_products_api.py` are
  `TODAY.md` (3 homes) and `docs/SPECS/spec-038-form_mutations-0_0_12.md` (Slice 2's own job).
- `docs/README.md` carries **zero** occurrences of any of the eight wire names; its
  `### Form mutations` section is an illustrative two-class code block, not an inventory. The prior
  review's read of it is confirmed with a different instrument.
- `docs/SPECS/spec-043-test_client-0_0_14.md` carries one `createItemWithFileViaForm` mention — a
  pre-existing prose reference in an archived spec, not an enumeration, and untouched.
- `docs/shadow/` hits are regenerable helper output, never committed or cited.
- **No SDL or introspection snapshot file anywhere carries these names**, so there is no snapshot
  to re-pin.

**This pass adds no schema field**, so it creates no new staleness of that class: the products
`Mutation` field set, the SDL, the app list and the two private schema-module enumerations are all
identical to the state the prior review already swept. The one enumeration the prior sweep's own
population contained and missed — the section comment — is fixed in this diff, verified above.

### Claims re-derived, not accepted

| Claim | Source | My measurement | Verdict |
|---|---|---|---|
| exactly one file modified this pass | `### Files touched` | `git diff HEAD` on the three products-surface files read hunk by hunk: `test_products_api.py` +173/-3, of which the prior review measured +111/-0, leaving ~62/-3 for this pass; `forms.py` +34/-2 and `schema.py` +52/-2 are the prior pass's, byte-identical to both scratch roots' pristine copies | confirmed |
| `forms.py` / `schema.py` byte-identical to their pristine copies | `### Failability proofs` | `filecmp.cmp(shallow=False)` `IDENTICAL` in **both** Worker 2's and my scratch roots; and the live `git diff HEAD` shows `fields = ("name",)` plus the injection line present, i.e. both mutations' inverses absent | confirmed |
| manifest now 5 entries | `### Failability proofs` | `docs/builder/temp-tests/slice-1/proofs.json` parses to **5** proofs | confirmed |
| the products form-mutation surface is 8 fields | `### Notes for Worker 1` item 1 | 8 classes, 8 `DjangoMutationField` rows, re-derived by regex | confirmed |
| `TODAY.md` under-enumerates: 6 named, 8 shipped | prior review's Medium | the six older wire names appear **3x each** in `TODAY.md`; `updateItemWithFileViaForm` and `createDefaultCategoryItemViaForm` appear **0** times; all three cited homes (`#"- **Form-based mutation write surface**"`, `#"as of \`0.0.12\` the form-backed mutations"`, `#"**Form-backed mutations (\`0.0.12\`).**"`) resolve exactly once | confirmed |
| the FK equality is a real selection, not a fixture accident | `### Tests added or updated` | `products/models.py::Item.category` is a non-nullable `ForeignKey` with **no `default`** and is narrowed out of `Meta.fields`, so no other path can set it; the row's own `exclude(pk=...).exists()` line asserts >= 2 categories exist, making "the lowest pk" a discriminating choice; both entry-4 and entry-5 baselines ran `2 passed`, so the guard holds at runtime | confirmed |
| `manage.py check` clean | `### Validation run` | `System check identified no issues (0 silenced).` | confirmed |
| pre-commit clean on the changed file | `### Validation run` | all **6** hooks `Passed`, citations included, nothing auto-fixed | confirmed |
| full sweep 4 failed / 7240 passed / 40 skipped / 0 collection errors | `### Validation run` | **identical in every figure** (see below) | confirmed |

### Full-sweep result — no fifth failure

`uv run pytest --no-cov` (full parallel, my own run):
**`4 failed, 7240 passed, 40 skipped in 61.84s`**, and a grep for `errors during collection` /
`error collecting` returns **0**. Same four node ids, same error, as Worker 2 recorded and as the
prior review recorded:

- `tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key`
- `tests/orders/test_inputs.py::test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration`
- `tests/test_sets_mixins.py::test_permission_family_config_stays_on_each_set_class`
- `tests/test_sets_mixins.py::test_filter_normalizer_honors_a_subclass_unset_sentinel_override`

all `TypeError: ActiveInputPermissionAttrs.__init__() got an unexpected keyword argument
'unset_sentinel'`. **No fifth failure and no collection error**, so the population is a valid
population and not a silently shrunk one — which is the specific way a smaller failure count can
mean less was measured. None of the four files, nor `sets_mixins.py`, is in this pass's diff.
`docs/builder/BUILD.md` `## Claims are proven mechanically` makes a failing test at `HEAD`
**not worker-verifiable** — reproducing it needs the whole tree at `HEAD` — so the evidence is
recorded and **the escalation stays with Worker 0**. Nothing was fixed, reverted, or worked
around.

The lint/format/diff gate, all read-only: `uv run ruff format --check .` -> `438 files already
formatted`; `uv run ruff check .` -> `All checks passed!`; `uv run python
examples/fakeshop/manage.py check` -> `System check identified no issues (0 silenced).`;
`uvx pre-commit run --files examples/fakeshop/test_query/test_products_api.py` -> all six hooks
`Passed`. `git diff --check` on this pass's file is clean (exit 0, no output); tree-wide it reports
trailing whitespace only in `docs/feedback2.md`, a baseline-dirty maintainer-input file outside
this pass's set, exactly as the prior review recorded.

### Hot-path budget verification

The task contract and the plan both declare **none**, and I verified the declaration holds against
the diff as landed rather than accepting it: this pass's diff is one live test file, and
`django_strawberry_framework/__init__.py` plus every other package `.py` is absent from it, so no
per-request, per-resolver, per-row, per-connection or per-outbound-message cost can have been
added. Correctly `Not applicable`; no number is owed and none is missing.

### Floor verification — the shared `.venv` was not mutated

Discharged by the build passes and already verified once; Worker 2 re-ran the GAP-3 scope anyway.
The one check whose failure would silently change the floor for every concurrent session on this
checkout is the shared environment, so it is read, never stated from memory:

- **Shared `.venv`, as read by `uv pip list`:** `django 6.1`, `strawberry-graphql 0.324.0`,
  `django-filter 26.1`, `pillow 12.3.0`; `uv run python` reports Python `3.14.2`. That is the
  newest supported set, **not** the floor — so no floor pin was installed into it. **Unmutated.**
- **`/tmp/dsf-floor`, as read by `uv pip list --python /tmp/dsf-floor/bin/python`:** `django
  5.2.16`, `strawberry-graphql 0.316.0`, `django-filter 26.1`, `pillow 12.3.0`; Python `3.10.19`.
  Exactly the floor `docs/builder/BUILD.md` `## Floor verification` states (Django **5.2.16** on
  Python **3.10** with strawberry-graphql **0.316.0**), and outside the working tree.
- No `uv pip install` was issued by this pass at all, so the shared `.venv` could not have been a
  target.

### `review_inspect.py` run record

**Run, and owed.** `docs/builder/BUILD.md` `### When to run the helper during build` puts Worker 3
under the helper for "50+ lines to any file outside `django_strawberry_framework/`", and this pass
added ~62 lines to `examples/fakeshop/test_query/test_products_api.py` (measured:
`git diff --numstat HEAD` gives +173/-3 total, of which the prior review measured +111 as the prior
pass's). Worker 2's decision **not** to run it was correct for Worker 2 — its own clause is
permissive ("may re-run") — and does not discharge mine.

| File | Result |
|---|---|
| `examples/fakeshop/test_query/test_products_api.py` | `uv run python scripts/review_inspect.py … --output-dir docs/shadow` exit 0; overview + stripped emitted; the new row enumerated at its own definition and docstring entry; **0** control-flow-hotspot entries for it; **0** Django/ORM markers in it; repeated literals are the file's pre-existing live-suite vocabulary |

Every invocation carried `--output-dir docs/shadow`. No shadow line number is cited anywhere in
this section. **No skips taken.** The prior passes' nine other overviews are still on disk.

### Spec slice checklist walk

The Plan's `### Spec slice checklist (verbatim)` is Worker 1's own grading contract for a grading
slice (this cycle's Slice 1 has no spec `## Slice checklist` entry). All eleven boxes are `- [x]`
and the prior review walked them without finding an over-tick. **Re-walked against this pass's
diff: no box is affected by it** — the diff addresses a review finding, not a checklist item — so
there is no newly-unaddressed box and no new tick to audit. Spot-re-verified the one box with a
durable artifact: all five named `review_inspect.py` shadow overviews are on disk (ten in total
now, including my re-run). No finding.

### Per-finding disposition of the prior review

| Prior finding | Severity | Disposition this pass |
|---|---|---|
| GAP-3's live row is not right-path pinned | Medium | **Closed.** The positive leg landed as its own node id; entry 4 measures the injection at 1 failing row (the positive leg) with the negative row still passing, entry 5 measures the narrowing at 2, and entry 3 measures the mapper at 2 — every half of the documented driver now fails at least one row when removed, and the halves are distinguishable by which rows fail. The FK equality is non-vacuous: `Item.category` is a non-nullable FK with no default and is narrowed off the wire, and the row asserts a second `Category` exists so "the lowest pk" is a real selection. No assertion was weakened or removed in the docstring edit (all seven enumerated and present). |
| The staleness sweep's population excluded the repo-root standing docs (`TODAY.md`) | Medium | **Correctly deferred, and the deferral is honest.** `TODAY.md` is byte-identical to `HEAD` (`cmp` clean, 42568 bytes both sides; absent from `git status`), which the build plan's scope fence requires. Its artifact-only half is discharged under `### The staleness sweep's population, qualified`. The substantive half is on disk under the prior review's `### Notes for Worker 1 (spec reconciliation)` item 1 with an `Escalated:` prefix, three resolution paths, a stated grade, and three `path #"substring"` citations that I confirmed resolve **exactly once each** — so `bld-038-final.md`'s `### Deferred work catalog` can pick it up without re-deriving anything. Worker 2's own `### Notes for Worker 1` item 1 pins the eight names so no path needs a recount. |
| GAP-4's shape half is equality-only with no absolute anchor | Low | **Correctly unchanged.** The prior review recorded it and required no change; Worker 2 neither weakened nor extended the row, and this pass's diff does not touch `tests/forms/test_resolvers.py`. |
| Worker 2's `unset_sentinel` occurrence counts have already rotted | Low | **Correctly unchanged.** A raw occurrence count of a file a concurrent session is writing is a moving figure by construction; the durable half re-derives and the four failing rows are unchanged in my own sweep. |

### What looks solid

- **The measurement Worker 2 ran before writing a line of test code is the best thing in the
  pass.** Mutating the injection against the *pre-fix* scope and recording that **0** rows failed
  turned the prior review's finding from a reading into a measurement, and it is what makes the
  positive leg provably a closure rather than a decoration. I reproduced the post-fix half of it
  (entry 4) and got the identical node-id set.
- **Naming the runner's `WEAKLY PINNED` verdict and exit 1 in the build report, with the ruling
  stated in full rather than left implicit, is exactly the right handling of a tool verdict a
  worker disagrees with.** It made the one genuinely open question findable in one read, which is
  the opposite of how a swallowed exit code behaves.
- **The second-`Category` existence assertion.** The hazard `START.md` names is asserting something
  a fixture size can satisfy by accident; the row forecloses it in one line, and the line is
  self-checking — if the fixture ever shrank to one category the row fails at that assert rather
  than passing vacuously. That is a guard that cannot rot into a lie.
- **Asserting the stored FK rather than the wire.** The narrowed input cannot carry `category` and
  the envelope's `node { name }` is minimal by design, so the DB read-back is the only place the
  property lives — the same lesson the prior pass recorded for the file exclusion, applied without
  being told.
- **Every assertion on the pre-existing negative row survived a docstring rewrite**, including the
  `count() == 1` residue check the retired clause described. The only executable change to that row
  is its query argument.
- **The diff is genuinely as narrow as claimed.** One file, ~62 added lines, no package `.py`, no
  closeout surface, and `django_strawberry_framework/__init__.py` not even dirty.

### Temp test verification

**No temp tests were created this pass.** The prior review's two are gone (their own disposition
deleted them, confirmed: `docs/builder/temp-tests/slice-1/` now holds only the manifest, the three
emitted proof reports and a `__pycache__`). Nothing needed one: both open questions were
measurements over existing rows, and the mechanized runner is the right instrument for a
measurement — a temp test would have added a second, unproved instrument to a question the runner
answers with a byte-proved revert. Nothing to promote.

### Notes for Worker 1 (spec reconciliation)

Nothing here duplicates Worker 1's 31-item list, the two build reports' seven items, or the prior
review's four.

1. **`Escalated:` the `TODAY.md` item still needs a NAMED owner, and the fence is why that is not
   automatic.** The escalation is intact on disk with three resolution paths, and I confirmed all
   three cited homes resolve. What is *not* yet settled is ownership: `START.md` "Past mistakes"
   requires a deferred item to be homed "on a specific card, in DB, before closing", and this
   cycle's scope fence bars the kanban DB. So whichever path Worker 1 picks, the ownership has to be
   made explicit in prose because the usual mechanism is unavailable: path **(a)** names a Worker 2
   pass under a widened fence, path **(b)** names **the maintainer** in
   `bld-038-final.md`'s `### Deferred work catalog`, and path **(c)** is a decision that must be
   *written*, not left as silence. A catalog bullet that says only "`TODAY.md` under-enumerates" and
   names nobody is the shape that dies. My grade is unchanged from the prior review's: **(a)**.
2. **The `get_form_kwargs` clause the prior pass proposed for Decision 8 now has a second,
   independently measured warrant.** Worker 2's `### Notes for Worker 1` item 3 proposes appending
   that a hook injecting a value the narrowed input cannot carry is only observably working if a
   test asserts the written row. Entry 4, re-run by me at Worker 2's scope, is that measurement:
   with the injection deleted the write-time row stays green and only the FK read-back
   distinguishes the two. The proposed clause is correct and the evidence behind it is now
   reproduced by two workers.
3. **No wording change is owed to DoD item 5 or the `## Test plan` live bullet.** The prior
   review's note 4 made them conditional on the positive leg landing; it landed and is measured, so
   the condition is discharged. Both homes close against the pair
   `::test_create_default_category_item_via_form_injects_the_default_category` +
   `::test_create_default_category_item_via_form_write_time_integrity_error_uses_envelope`, cited
   together — either alone under-determines the contract, which is the whole content of the finding
   this pass closed.

### Review outcome

`review-accepted`.

**No unresolved findings.** Both prior Mediums are settled: the GAP-3 right-path Medium is
**closed** by a positive leg whose failability I re-measured at Worker 2's own scope, and the
`TODAY.md` Medium is **correctly deferred** with zero `TODAY.md` bytes changed and the escalation
recorded on disk in a form the final gate can consume. Both prior Lows stand unchanged with their
recorded reasons. My one new Low is an inaccuracy in a per-cycle artifact's account of a docstring
edit, with the load-bearing check — no assertion lost — verified and passing; it requires no
change.

**Worker 2's failability-exemption reasoning is accepted on both questions**, against the rules'
own wording rather than by deference: the acceptance rule's subject is a boundary,
`get_form_kwargs` in an example app is not one and is not new to this pass, and the pair
measurement is the correct instrument for the finding it closes.

Everything else clears: entries 3, 4 and 5 re-run at Worker 2's recorded scopes with **zero
node-id set difference**, zero collection/setup errors, green same-scope baselines, and every
revert proved by byte-comparison twelve copies over across four scratch roots; the full parallel
sweep is `4 failed, 7240 passed, 40 skipped, 0 collection errors` — the same four pre-existing
rows, no fifth failure, escalation left with Worker 0; `manage.py check`, `ruff format --check .`,
`ruff check .`, `git diff --check` on this pass's file, and all six pre-commit hooks are clean; the
public surface is untouched and no package `.py` is in the diff, so the `none` hot-path declaration
holds against the diff as landed; the shared `.venv` reads as the newest supported set and was not
mutated to the floor; and my own repo-wide 5463-file staleness sweep — a strict superset of both
prior populations — finds no home this pass staled.


---

## Final verification (Worker 1)

The `## Final verification (Worker 1)` block earlier in this file is the grading pass's
placeholder ("Not applicable to this pass") and names what this pass must audit. This is that
pass. It read the whole chain — plan, two build reports, two review sections — plus Slice 0's
artifact, and re-derived every load-bearing figure with its own instrument rather than reading
the chain's agreement as corroboration. Four passes deep is the depth at which a number gets
treated as measured because an earlier pass said it.

No source, no test, and no spec byte was written by this pass. Files written: this artifact and
`docs/builder/worker-memory/worker-1.md`.

### Checklist audit

The Plan's `### Spec slice checklist (verbatim)` carries **12** checkbox lines, not the eleven
both review passes counted: one parent (the build plan's own Slice-1 line, copied verbatim) plus
**11** sub-checks. Both reviews walked the 11 sub-checks; the parent went uncounted. Every box is
`- [x]`, and **every tick was set by the grading pass** — no Worker 2 pass set or cleared a box,
which I confirmed by reading both build reports (neither reports a tick) and by the fact that no
box names a fix contract. So the audit is of 12 grading-deliverable ticks, each re-derived:

| Box | Verdict | Instrument |
| --- | --- | --- |
| parent — "Slice 1: code conformance — grade every Decision and Definition-of-done item against `HEAD` … dispatch Worker 2 / Worker 3 only if a real gap is proven" | **stands** | the grading landed (140 rows), a gap was proven, and Workers 2 and 3 were dispatched on it. **Note the asymmetry, deliberately not "fixed":** the same line in `docs/builder/build-038-form_mutations-0_0_12.md` is correctly `- [ ]` — `docs/builder/BUILD.md` `## Required plan structure` makes that box Worker 0's to flip after this pass accepts, and Worker 1 does not mark build-plan checkboxes |
| 1 — All 14 Decisions graded | **stands** | `^### Decision \d` over the spec → **14** headings (D1…D14); the Decisions verdict table carries a row for each, D5 and D7 split per independently-gradable clause |
| 2 — Every `## Slice checklist` sub-check graded (5 slices, 14 nested sub-checks) | **stands** | section `## Slice checklist` (spec L232-454): **5** top-level bullets, **14** nested `- [ ]` sub-bullets. Both figures measured, both match |
| 3 — Every `## Edge cases and constraints` bullet graded (16) | **stands** | section L1675-1775: **16** top-level bullets, 0 nested |
| 4 — Every `## Test plan` row graded (7) | **stands** | section L1776-1872: **3** top-level bullets + **5** nested = 8 lines, of which the "**Package-internal**" top-level bullet is a header for its own 5 nested rows and is not itself gradable → **7** gradable rows, exactly the verdict table's 7 |
| 5 — Every `## Definition of done` item graded (1-8) | **stands** | section L1957-2227: **8** numbered items |
| 6 — Every `## Implementation plan` cell graded (5 × 2) | **stands** | section L1651-1674: **6** table rows = 1 header + **5** slice rows → **10** cells, exactly the verdict table's 10 |
| 7 — `## Out of scope` (7) and `## Non-goals` (6) graded | **stands** | `## Out of scope (explicitly tracked elsewhere)` → **7** bullets; `## Non-goals` → **6** |
| 8 — Worker 0's D-1…D-19 independently graded (2 corrected, 1 partially refuted, 16 confirmed) | **stands** | a parser over the artifact's own grade table: **19** rows, grades classified as **2** CORRECTED (D-1, D-16), **1** PARTIALLY REFUTED (D-13), **16** CONFIRMED-or-DISCHARGED. The parenthetical count is exact |
| 9 — `review_inspect.py` run on all five named files with `--output-dir docs/shadow` | **stands** | all five `django_strawberry_framework__forms__{converter,inputs,resolvers,sets}` + `__mutations__fields` `.overview.md` / `.stripped.py` pairs on disk; **10** overviews total now, the extra five from the review passes' own runs |
| 10 — Every claim about a baseline-dirty file stated against `git show HEAD:` into a scratch path outside the repo | **stands** | reproduced: all 300 `tests/` + `examples/fakeshop/` `.py` blobs read out of `HEAD` into this session's scratchpad, plus `HEAD:TODAY.md`. No `git stash` / `checkout` / `restore` / `worktree` was run by this pass |
| 11 — Gap found -> implementation plan written, `Status: planned` | **stands** | four gaps, a per-gap fix plan, an ownership partition, and the `planned` transition are all on disk |

**Boxes un-ticked: none.** No over-tick survived the audit.
**Boxes newly ticked: none.** No box's contract landed while left open.
**Boxes still `- [ ]`: none**, so no deferral reason is owed under
`docs/builder/ARTIFACT.md`'s rule; the Medium `docs/builder/BUILD.md` `## Severity definitions`
attaches to a silently-unaddressed sub-check has no subject here.

### Claims re-derived, not accepted

Populations printed for every sweep. Every multi-file sweep ran through a `uv run python - <<'PY'`
heredoc, never a bare `for f in $FILES` (`START.md` "Instruments that lie": zsh collapses that to
one iteration and a sweep printing nothing reads as a clean repo).

| Claim | Recorded by | My measurement | Verdict |
|---|---|---|---|
| the four gaps' rows exist as named node ids and are collected | both build reports | `pytest --collect-only` over the eight named functions → **10 node ids, 0 collection errors** (`…_trips_the_construction_hook_waiver[modelform]`/`[plain_form]` and `…_excludes_every_file_field_flavor[attachment]`/`[image]` are the two parametrized pairs); the same ten **run green in 3.27 s** | confirmed |
| population = 300 `.py` files / 7,228,167 bytes at `HEAD` under `tests/` + `examples/fakeshop/` | W2 (W1 recorded 7,228,146) | **300 files / 7,228,167 bytes**, read blob-by-blob out of `HEAD`. W2's figure exactly; W1's 21-byte deficit is the drift W2 named | confirmed, W2 right |
| `def get_form(` = **0** across that population at `HEAD` | plan `#### GAP-1`, W2, W3 | **0 occurrences in 0 files.** Positive control on the same instrument: `def test_` = **6,038 occurrences in 160 files**, so the zero is a measurement and not an empty grep | confirmed |
| the same token is now **non-zero** — i.e. GAP-1 is actually closed | implied by the fix | working tree, same 300-file population (7,532,083 bytes): `def get_form(` = **2 occurrences in 2 files**, `tests/forms/test_resolvers.py` and `tests/forms/test_sets.py`. 0 → 2 | confirmed |
| `initial` = 0 in `tests/forms/` at `HEAD` | plan `#### GAP-2` | **0 occurrences in 0 files** | confirmed |
| `get_form_kwargs` = 19 in 6 files | plan `#### GAP-4` | **19 occurrences in 6 files**, and the six are the six named | confirmed |
| the products form-mutation surface is **8** fields | W2 pass-1 note 2, W2 pass-2 note 1, W3 pass-2 | `^class \w+\((DjangoModelFormMutation\|DjangoFormMutation)\):` over `products/schema.py` → **8** classes; the `Mutation` body carries **8** matching `DjangoMutationField(...)` rows (`create_item_via_form`, `update_item_via_form`, `create_item_with_file_via_form`, `update_item_with_file_via_form`, `create_default_category_item_via_form`, `create_stamped_item_via_form`, `submit_contact`, `submit_ping`). **My first regex for the `Mutation` body returned 0 and I did not publish it** — the class is decorated, so my section-slicing lookahead terminated early; re-derived by reading the body | confirmed |
| `django_strawberry_framework/` carries **no** byte of this cycle's diff | plan, both build reports, both reviews | **69** dirty tracked package paths + **1** untracked (`utils/canonical.py`, a hostile-safe-container-read module imported by the concurrent session's own `utils/inputs.py` / `utils/write_transaction.py` edits). Their combined working-diff is **491,789 bytes**; a 12-token sweep for this cycle's identifiers (`get_form_only_override`, `UpdateItemWithFileViaForm`, `CreateDefaultCategoryItemViaForm`, `DefaultCategoryItemModelForm`, `_CREATE_DEFAULT_CATEGORY_ITEM_VIA_FORM`, `RaceFormFresh`, `bld-038`, …) returns **0 total**. Positive control on the same bytes: `materialize_relation_id_container` = 4, `_safe_text` = 8, `keyword.iskeyword` = 1, so the instrument reads the real diff | confirmed |
| the three `forms/` hunks are the concurrent session's hardening, not this cycle's | plan `## Baseline-dirty out-of-scope files` | read line by line: `resolvers.py` = the `materialize_relation_id_container` lift replacing an inline container check; `sets.py` = the typed `BaseException` wrap around the `get_form_fields` hook plus a `_safe_text` import; `inputs.py` = `import keyword`, the `isidentifier`/`iskeyword` field-name guard, the guarded `dict(form_class.base_fields)` read, and an out-of-vocabulary `operation_kind` raise. Every one hardening-shaped, none gap-shaped | confirmed |
| no proof mutation survives | W2 ×2, W3 ×2 | the manifest at `docs/builder/temp-tests/slice-1/proofs.json` parses to **5** proofs and **all five anchors match exactly once** in the live tree; the inverse of entry 3's mutation (`write_error = None`) occurs **0** times; no `ACTIVE-MUTATION.json` / `RESTORE-FAILED.json` exists under `/tmp` or the session scratchpad; `git diff HEAD` on `products/forms.py` / `products/schema.py` shows `fields = ("name",)` and the `kwargs["category"] = …` injection both present | confirmed |
| the cycle's five-file diff is confined to the declared ownership list | plan `### Slice-split answer` | `git diff --stat` → `products/forms.py` +36, `products/schema.py` +54, `test_products_api.py` +176, `tests/forms/test_resolvers.py` +356, `tests/forms/test_sets.py` +242 (the last two mixed with the concurrent session's rows). `products/schema.py`'s added lines are exactly the two mutation classes, one `get_form_kwargs`, and two `Mutation` fields — nothing else | confirmed |
| full parallel sweep: 4 failed, 7240 passed, 40 skipped, 0 collection errors | W2 pass 2, W3 pass 2 | my own `uv run pytest --no-cov -p no:cacheprovider`: **`4 failed, 7240 passed, 40 skipped in 65.86s`** — identical in every figure. The four are the same node ids and the same `TypeError: ActiveInputPermissionAttrs.__init__() got an unexpected keyword argument 'unset_sentinel'`. **0 collection errors** is pytest's own accounting: its summary line carries an `N errors` term whenever collection failed and this one does not | confirmed |
| the eight named assertions per gap actually exist | both build reports | an AST-free per-function slice printed every `assert` in all eight rows: 4 / 8 / 9 / 2 / 2 / 11 / 7 / 7. The GAP-3 negative row's **seven** assertions are present verbatim, which is the load-bearing half of W3 pass-2's Low; the row's only `mock`-shaped line is the docstring phrase "no mock" | confirmed |
| `TODAY.md` was not touched | W3 pass 2 | `cmp TODAY.md <git show HEAD:TODAY.md>` → **IDENTICAL**, 42,568 bytes both sides, and `git status --porcelain -- TODAY.md` is empty | confirmed |
| `TODAY.md` under-enumerates: six named, eight shipped | W3 pass 1 | the six older wire names occur 3-4× each; `updateItemWithFileViaForm` and `createDefaultCategoryItemViaForm` occur **0** times; all three cited homes resolve **exactly once** each | confirmed |
| the public surface is unchanged | both reviews | `django_strawberry_framework/__init__.py` is **not even dirty** — absent from `git status`, empty `git diff --stat` | confirmed |
| lint / whitespace clean on the cycle's files | W2 ×2 | read-only: `ruff format --check` → `5 files already formatted`; `ruff check` → `All checks passed!`; `git diff --check` on the five → exit 0, no output. No `--fix`, no `.` | confirmed |
| the floor venv is the floor and the shared `.venv` is not | W2 ×2, W3 ×2 | see `### Hot-path and floor declarations` below — read, never stated from memory | confirmed |
| verdict rows = 140 | plan `### Verdict summary` | the section counts above make the row basis reproducible (14 Decisions clause-split, 14+5 checklist, 16 edge cases, 7 test-plan, 8 DoD, 10 implementation-plan cells, 13 out-of-scope/non-goals) and the collapse is internally consistent (96+9+21+8+6 = 140). W3's own crude parser returned 139-141 depending on multi-verdict-cell attribution; I did not improve on that resolution and record the figure as **consistent within instrument resolution**, not as independently re-derived to the unit | consistent, not exact |

One recorded figure I could not re-derive and am **not** treating as measured: the split of
`tests/forms/test_resolvers.py` / `test_sets.py`'s mixed diffs into "this cycle's hunks" versus
"the concurrent session's". Both reviews read it hunk by hunk and agreed; the concurrent session
has written both files since, so the boundary is no longer reconstructible read-only. What *is*
still re-derivable is the claim that matters — that no package `.py` carries this cycle's work —
and that is measured above.

### The four `DROPPED` verdicts, re-graded against the diff as landed

The grading pass's placeholder required this. Each moves to `BUILT-CONFORMANT` with a test
citation; none carries a deferral.

- **GAP-1** (`get_form` construction hook) → **BUILT-CONFORMANT.**
  `tests/forms/test_sets.py::test_get_form_only_override_trips_the_construction_hook_waiver`
  (`[modelform]` / `[plain_form]`) pins the second disjunct of
  `forms/sets.py::_form_kwargs_overridden` directly, with the overrides-neither control in the
  same row; `tests/forms/test_resolvers.py::test_get_form_only_override_builds_the_form_and_waives_the_required_guard`
  pins that the pipeline validates the override's own form object. Boundary measured at **3**
  rows, twice, same node-id set.
- **GAP-2** (omitted-file preserve) → **BUILT-CONFORMANT.**
  `tests/forms/test_resolvers.py::test_partial_update_omitting_file_field_keeps_it_out_of_the_reconstructed_data`
  (`assert "attachment" not in reconstructed`, plus the FK and scalar keys present),
  `::test_partial_reconstruction_excludes_every_file_field_flavor[attachment]` / `[image]`, and
  live `examples/fakeshop/test_query/test_products_api.py::test_update_item_with_file_via_form_omitting_the_file_preserves_it`.
  Boundary measured at **3** rows. The live row is kept and is **not** the pin — recorded as such
  in three places by three workers, which is the honest handling.
- **GAP-3** (live write-time `IntegrityError`, `ModelForm` flavor) → **BUILT-CONFORMANT.**
  `::test_create_default_category_item_via_form_write_time_integrity_error_uses_envelope`
  (mock-free; the save-time mapper's own wording on the `"__all__"` sentinel) paired with
  `::test_create_default_category_item_via_form_injects_the_default_category` (the FK read-back).
  **The pair is the citation** — either alone under-determines the contract, which is exactly the
  finding the apply-changes pass closed.
- **GAP-4** (`get_form_kwargs` queryset scoping, input shape unchanged) → **BUILT-CONFORMANT.**
  `::test_get_form_kwargs_queryset_scoping_leaves_the_generated_input_shape_unchanged` — shape
  equality across the pair plus the runtime rejection of an out-of-queryset id on the scoped
  mutation and its acceptance on the unscoped one.

Consequence for Slice 2: **the spec is right on all four and gains no rewrite here.** Case-(1)
items 28-31 of the grading pass's list close with citations. This is consolidated item 35 below.

### Ruling 1 — the apply-changes pass owed no failability proof. Worker 3's exemption is CONFIRMED.

**Which section governs: `### What needs a proof, and what does not`.** It defines the obligation's
*subject* — "every **new boundary, guard, gate, or rejection path** a slice introduces — anything
whose job is to say 'no', hold an invariant, or fail closed" — and says expressly that it is "**not**
required for every changed line". `### Acceptance rule: weakly pinned is `revision-needed`` opens "A
**boundary** is weakly pinned when removing it makes 0 or 1 test rows fail"; it borrows its subject
from the first section and defines none of its own. So the acceptance rule cannot reach a line that
the first section never brought into scope, and the question is settled by reading what a boundary
is, not by weighing two rules against each other.

**The mutated line is not a boundary, and I read it rather than accepting the description.**
`examples/fakeshop/apps/products/schema.py::CreateDefaultCategoryItemViaForm.get_form_kwargs` is
`kwargs["category"] = models.Category.objects.order_by("pk").first()` — one assignment into a
constructor-kwarg dict in an example app, outside the coverage gate. It refuses no input, holds no
invariant, and fails nothing closed; deleting it permits nothing that was previously refused (the
INSERT still fails, as NOT NULL instead of a unique violation). The second reason stands
independently: the line is **not new to that pass** — it landed in the first build pass, which
recorded it, and the first review accepted it. The apply-changes pass's diff is one live test file
and zero production code.

So the runner's `WEAKLY PINNED` verdict and exit 1 on entry 4 are the tool applying a
boundary-scoped rule to every entry it is handed, which its own report text says it does. Naming
that in the build report instead of swallowing the exit code is the right handling, and the
recorded right-path measurement — owed by `### Query-shape tests must pin the load-bearing
property, not observability` rather than by the proof rule — is the correct instrument for the
finding it closed: entries 4 and 5 make the injection and the narrowing each fail at least one row
when removed, and the halves are distinguishable by *which* rows fail.

**Not overturned; no rows are required; `revision-needed` is not set on this ground.** Had the rule
applied, its own remedy ("more or better-targeted rows") has no target: one hook, one injected
value, one observable. W3 pass-2's Low already names the honest ceiling — retiring that one row
returns the injection to zero assertions — and recording that is the right response, because the
alternative is padding a count.

### Ruling 2 — where the `TODAY.md` deferral is homed

**Decision: path (b), owner named — the maintainer — with path (a) recorded as the recommended
remedy the maintainer can authorize in one move.** Both review passes graded (a) (widen the fence
by one file, have a Worker 2 pass re-pin the three sentences in the cycle that caused the drift). I
agree that (a) is the better *fix* and that `AGENTS.md` rule 14's same-change discipline is the
repo's default. It is nonetheless not available to me: the scope fence is **maintainer-set**, my
own dispatch contract names `TODAY.md` among the surfaces no worker may edit, and no worker can
widen a maintainer's fence. Setting `revision-needed` to force (a) would loop a builder against a
fence it cannot cross, which produces a stalled pass rather than a fix.

Path (c) is rejected outright: the drift is a direct consequence of this cycle's own two new
`Mutation` fields, and calling it acceptable is the partial-claim residue that reopens a cycle
(`START.md`: "Partial claim fix = dominant residual defect").

So (b), and the reason it does not die the death `START.md` "Past mistakes" describes is that the
**owner is named in prose because the usual mechanism is barred.** The kanban DB is inside the
fence, so there is no card to home it on; a catalog bullet naming nobody is exactly the shape that
dies. The bullet below names the maintainer, the file, the three homes by quoted phrase, the two
missing names, and the one-line action — everything a reader needs without re-deriving anything.

**Verbatim, for `docs/builder/bld-038-final.md` `### Deferred work catalog`:**

> - **`TODAY.md` under-enumerates the products form-mutation surface — six named, eight shipped.**
>   Owner: **the maintainer** (no worker may edit it; the build plan's `## Scope fence` puts
>   `TODAY.md` out of scope for this whole cycle and the kanban DB with it, so this bullet is the
>   homing mechanism). Source: `docs/builder/bld-038-slice-1-code_conformance.md` `### Medium:`
>   ("The staleness sweep's population excluded the repo-root standing docs"), escalated again in
>   both review passes' `### Notes for Worker 1 (spec reconciliation)` item 1. Cause: this slice
>   added `updateItemWithFileViaForm` and `createDefaultCategoryItemViaForm` to
>   `examples/fakeshop/apps/products/schema.py::Mutation` under the GAP-2 / GAP-3 escalations —
>   surface the fence did not anticipate. Three homes, each resolving exactly once, each listing
>   six of the eight: `TODAY.md` #"- **Form-based mutation write surface**",
>   `TODAY.md` #"as of `0.0.12` the form-backed mutations",
>   `TODAY.md` #"**Form-backed mutations (`0.0.12`).**". The full set is
>   `createItemViaForm`, `updateItemViaForm`, `createItemWithFileViaForm`,
>   `updateItemWithFileViaForm`, `createDefaultCategoryItemViaForm`, `createStampedItemViaForm`,
>   `submitContact`, `submitPing` — re-derived twice (8 classes, 8 `DjangoMutationField` rows), so
>   no recount is owed. Recommended action: widen the fence by this one file and re-pin the three
>   sentences; measured at three sentences in one file, no generator, no gate. `TODAY.md` is
>   byte-identical to `HEAD` (42,568 bytes, `cmp` clean) — nothing was pre-emptively touched.
>   No licensing spec clause: this is cycle-caused drift, not a spec deferral.

Nothing else in this cycle is deferred to the maintainer on this ground; the four pre-existing
sweep failures are a separate escalation that stays with Worker 0 (below).

### Hot-path and floor declarations, verified against the diff as landed

**Hot path: the plan's build-wide `none` holds, and its stated ground holds.** The ground is "no
package `.py` is edited". Measured above: 0 of 12 cycle tokens in the 491,789-byte package
working-diff with a passing positive control, and `django_strawberry_framework/__init__.py` not
even dirty. Nothing runs per request, per resolver, per row, per connection, or per outbound
message in the package as a result of this cycle. Two costs exist and neither is package cost nor
per-request: the two new example-app `DjangoMutationField`s cost one construction each **at schema
build**, and `CreateDefaultCategoryItemViaForm.get_form_kwargs` issues one
`Category.objects.order_by("pk").first()` read per call **of that one example-app mutation**,
inside the pipeline's read phase before `pipeline_write_phase()` opens. Recorded, not a finding,
and no before/after number is owed.

**Floor: the planned run happened, is recorded with resolved versions, and I re-executed it.**
`docs/builder/BUILD.md` `## Floor verification` makes an unrun planned floor verification grounds
for `revision-needed`; it was run, by the pass the plan named (the Worker 2 build pass for this
slice), after Worker 1 re-declared the scope from the plan's `none by default` to GAP-2 and GAP-3
in scope. The floor is executed, never reasoned, so I executed it again rather than reading the
record:

- `/tmp/dsf-floor` exists outside the working tree. `uv pip list --python /tmp/dsf-floor/bin/python`
  → `django 5.2.16`, `strawberry-graphql 0.316.0`, `django-filter 26.1`, `pillow 12.3.0`;
  `/tmp/dsf-floor/bin/python -c "import sys; …"` → **3.10.19**. That is exactly the floor
  `docs/builder/BUILD.md` `## Floor verification` states: Django **5.2.16** on Python **3.10** with
  strawberry-graphql **0.316.0**.
- `/tmp/dsf-floor/bin/python -m pytest tests/forms/test_resolvers.py -k "file or upload or preserve or integrity" --no-cov -n0`
  → **11 passed, 57 deselected. PASS.** Reproduces the recorded figure exactly.
- `/tmp/dsf-floor/bin/python -m pytest examples/fakeshop/test_query/test_products_api.py -k "with_file or integrity or default_category" --no-cov -n0`
  → **4 passed, 131 deselected. PASS.** I ran the union of the two recorded selections
  (`with_file or integrity` → 3, and the apply-changes pass's `default_category` → 2, overlapping
  on the negative row), so 4 is the consistent union and not a third figure.
- **The shared `.venv` is unmutated**, read after the floor runs, never stated from memory:
  `uv pip list` → `django 6.1`, `strawberry-graphql 0.324.0`, `django-filter 26.1`,
  `pillow 12.3.0`, Python **3.14.2** — the newest supported set, not the floor. No `uv pip install`
  was issued by this pass at all.

### Fail-open read of the diff

`worker-1.md` `### Failability and fail-open checks` requires reading the diff for the catalogued
shapes rather than trusting a green suite. With zero package `.py` in the diff, no production
fail-open shape can have landed. One example-app line is fail-open **shaped** and is worth naming
because its consequence is exactly what the review chain measured:
`examples/fakeshop/apps/products/forms.py::DefaultCategoryItemModelForm.__init__` #"if category is not None:"
converts a missing injection into "construct anyway", which is why a broken
`get_form_kwargs` degraded the write-time row from a unique violation to a NOT NULL violation with
an identical envelope. That is acceptance-fixture code outside the coverage gate, the guard is
correct for a `ModelForm` whose `category` kwarg is optional by construction, and the observability
consequence is closed by the positive leg. **Recorded, not a finding.**

### Failability record completeness

`worker-1.md` requires confirming the record *exists* for every boundary this slice added, with
byte-compared reverts and a `why 0` on any zero-row entry. Confirmed: **three** boundaries newly
pinned, each carrying mutation / scope-as-run / pre-mutation baseline / listed node ids /
collection-error count (0 each) / byte-proved revert, at **3 / 3 / 2** rows — none weakly pinned.
**No zero-row entry exists in the whole chain**, so no `why 0` slot is owed anywhere. Worker 3
re-ran all three at the recorded scopes with zero node-id set difference, then re-ran entry 3 a
second time after the apply-changes pass grew that scope's population by one row — which is the
right instinct, since a recorded node-id set over a scope whose population changed is not
self-evidently the same set. Entries 4 and 5 are right-path measurements over non-boundaries
(Ruling 1) and are labelled `PARTIAL RECORD` by the tool, correctly.

### Pre-existing failures: escalation stays with Worker 0

`docs/builder/BUILD.md` `## Claims are proven mechanically` makes a failing test at `HEAD`
**not worker-verifiable** — reproducing it needs the whole tree at `HEAD`, and this tree carries
151 dirty paths of another session's work. My own full sweep reproduces the same four node ids and
the same `TypeError: ActiveInputPermissionAttrs.__init__() got an unexpected keyword argument
'unset_sentinel'`, with no fifth failure and no collection error. None of the four rows' files, nor
`django_strawberry_framework/sets_mixins.py`, is in this cycle's diff. Nothing was fixed, reverted,
or worked around, and the escalation is left where the review chain left it: **with Worker 0**, for
the maintainer. This is not a deferred-work-catalog item — it is not this build's work.

### Notes for Worker 1 (spec reconciliation)

**This is the consolidated list Slice 2 works from, top to bottom. It replaces the six per-section
lists as the working document** — read this one; the six originals stay on disk as provenance.

Provenance and arithmetic, so the consolidation is auditable rather than asserted. Six sections
routed **54** items forward plus **2** non-edit notes: Slice 0's artifact 9, this artifact's Plan
31 (+2 notes), the first build report 4, the first review 4, the apply-changes build report 3, the
re-review 3. Consolidated to **35 items + 3 non-edit notes**, with all 54 homed and none dropped:

- Slice 0 items 1 and 8 are absorbed by items **22** and **24** (same sentences, better-measured);
  Slice 0 item 9 becomes non-edit note **N2**; Slice 0 items 2-7 survive as items **27-32**, and
  none of them appears anywhere in the Plan's 31 — they are the consolidation's main find.
- The Plan's case-(2) item 25 and its case-(3) item 19 target **the same sentence** (the Slice-2
  checklist's allowed-key clause) with two different defects; merged into item **19**. The Plan's
  own cross-reference there points at "item 20" and means 25.
- The Plan's case-(1) items 28-31 are **discharged by this slice's build** and collapse into item
  **35**, absorbing the first build report's item 1, the first review's item 4, the apply-changes
  report's item 2 and the re-review's item 3, which all say the same thing from four vantage points.
- The first build report's item 2 and the apply-changes report's item 1 (the products count) are
  absorbed by item **11**; item 3 of the first report and item 3 of the first review become item
  **33**; item 4 of the first report, item 3 of the apply-changes report and item 2 of the
  re-review become item **34**; the first review's item 2 is absorbed by item **22**; both reviews'
  item 1 becomes non-edit note **N3**.

Every item carries the spec heading, a quoted phrase **verified to sit on one source line** and
its occurrence count in the current spec, the shipped truth, and its grading case. No line numbers:
the file has already shifted once this cycle and Slice 2 will shift it again. Three anchors the
routed lists used do **not** resolve as quoted because they wrap across two source lines
(`fully-pinned** resolution of the prior`, `not a preferred / fallback branch`,
`the single resolution of the prior contradiction`); each is replaced below by a single-line token.

**Case (3) — a later card deliberately changed it. Code stands; rewrite the spec to state the
shipped contract directly, and put what changed and why in the rationale companion as a
`**Post-ship:**` bullet under the owning Decision (21 items).**

1. **Decision 7, the converter bullet list** — anchor `text-like` (×1); **and `## Definition of
   done` item 2** — anchor `its Strawberry annotation` (×1). Shipped truth: `_SCALAR_FORM_FIELDS`
   carries **12** rows including `forms.JSONField` → `strawberry.scalars.JSON`, added post-ship by
   `efb7bda5` because the `CharField` parent otherwise types JSON payloads as `String`. Add the row
   to both homes.
2. **Decision 7** — anchor `NullBooleanField` (×1). Shipped truth:
   `forms/converter.py::form_field_required` is the single requiredness decision across both bases
   and a **three**-case rule: an exact `NullBooleanField` forced optional, a **subclass** keeping
   its declared requiredness (so a non-null `bool`), and a **non-null-column-backed** field keeping
   `required=True`. Post-ship (`5737ddda`).
3. **Decision 7, the reverse-map paragraph** — anchor `metadata record` (×1); **and the Slice-1
   checklist sub-check** (same rewrite). Shipped truth: the record type is
   `utils/inputs.py::InputFieldSpec` (`target_name` = the form field name, plus `related_model` /
   `source` / `nested_specs`); the four kind constants are defined there and re-exported by
   `forms/converter.py`, which now "owns only the kind constants".
4. **Decision 7, the relation-decoder paragraph** — anchor `runs its **own**` (×1). Shipped truth:
   the form *coloring* (an `empty_values` skip plus a `to_field_name` projection) of the shared
   `utils/write_values.py::decode_visible_relation` spine, with `decode_field_handlers` /
   `decode_provided_fields` owning the `UNSET` strip and the kind dispatch — a substrate the
   serializer flavor also rides. **The visibility-on-every-branch security contract must survive
   the rewrite verbatim.**
5. **Decision 7, the shape-identity paragraph** — anchor `frozenset(effective field names` (×2,
   both homes: Decision 7 and `## Definition of done` item 2); **third home**, the Slice-2
   checklist's `"form"`-sentinel cache-key clause. Shipped truth:
   `forms/sets.py::_cached_build_form_input` keys on a **4-tuple** adding
   `_form_input_hook_identity(mutation_cls)` (`None` unless the mutation overrides
   `get_form_fields`). Say the fourth component is a hook discriminator, not a fifth concept.
6. **Decision 7, the create-guard paragraph** — anchor `is exempt` (×1). Shipped truth: **two**
   narrowing guards keyed on one waiver;
   `forms/inputs.py::guard_partial_required_column_less_fields` rejects an `update` narrowing that
   drops a **required column-less** field, because `model_to_dict` cannot reconstruct it.
   Post-ship. The `## Edge cases` create-narrowing bullet does **not** repeat the exempt clause
   (this corrects Worker 0's D-13, and it is the reason the grep is `is exempt` ×1 and not ×2) but
   is **silent** about the partial guard and should gain it.
7. **Decision 8, the "Helper reuse" paragraph** — anchor `underscore-dropped in place` (×1); **and
   the `## Implementation plan` Slice-3 cell**, same nine-name list. Shipped truth, measured with
   `git grep -n "^def <name>(" HEAD`: `locate_instance`, `coerce_lookup_id`, `authorize_or_raise`,
   `refetch_optimized`, `build_payload`, `not_found_error`, `save_or_field_errors` in
   `mutations/resolvers.py`; `validation_error_to_field_errors` in `utils/errors.py`;
   `raw_choice_value` in `utils/write_values.py`; `payload_object_slot` in `mutations/inputs.py`.
   See item 23 — the same paragraph is *also* wrong on its own date.
8. **Decision 8, the pipeline preamble** — anchor `whole pipeline runs inside one` (×1). Shipped
   truth: `mutations/resolvers.py::run_write_pipeline_sync` also enforces a managed-transaction
   gate on one pinned write alias (`open_write_pipeline`, `pipeline_alias_guard`,
   `check_instance_write_alias`), captures an immutable `authorized_pk` / `target_state` snapshot
   right after the locate, and calls `check_deadline(info)` **before** the transaction opens. All
   post-`038` (`0.0.14` mutation atomicity; the `spec-047` cooperative deadline). A form mutation
   inherits every one, so the one-`atomic()` sentence is no longer the whole boundary story.
9. **Decision 8 step 4, the update-reconstruction bullet** — anchor `model_to_dict` (**×5**, and
   the count is the point: the one-shape formula has **four** normative homes plus one incidental
   mention — Decision 8's own preamble, Decision 8 step 4, the `## Edge cases`
   update-preservation bullet, and `## Definition of done` item 4, with the required-extra bullet
   the fifth mention. **The routed list named three; there are four to fix.**) Shipped truth:
   `forms/resolvers.py::_reconstruct_partial_data` has **three** shapes, because an omitted field
   must bind in the same shape a provided one decodes to — `model_to_dict` for scalars and a
   `to_field_name`-**less** FK, `_to_form_key_value` per member for a real forward M2M, and
   `_to_form_key_value` for a `ModelChoiceField` **with** `to_field_name`. It also reads the form's
   **full** declared set (`get_form_fields`), not the narrowed input.
10. **Decision 11, the plain-`Form` paragraph** — anchor `Preferred resolution` (×1). Shipped truth
    (two changes): an unset `permission_classes` defaults to `(DenyAll,)`, so drop the "Preferred
    resolution" framing — a chronology hedge whose Risks referent left with Slice 0's move — and
    state the default; **and** the plain base now **rejects** any `DjangoModelPermission` subclass
    entry at class creation, because that class resolves the write permission from a model a
    model-less mutation never provides. Post-ship.
11. **Decision 12** — anchor `narrows it to the existing` (×1); **and `## Definition of done`
    item 5 and the `## Test plan` live bullet.** Shipped truth: the live form surface spans three
    apps — **`products` (8 form mutations:** `createItemViaForm`, `updateItemViaForm`,
    `createItemWithFileViaForm`, `updateItemWithFileViaForm`, `createDefaultCategoryItemViaForm`,
    `createStampedItemViaForm`, `submitContact`, `submitPing`**)**, `library`
    (`CreateShelfViaForm`, `UpdateBookViaForm`, `CreateBranchWithShelf`, `CreateBranchPair` over
    `ShelfRelationsForm` / `BookGenresModelForm` / `BranchWithShelfForm` / `BranchPairForm`), and
    `scalars` (`CreateMediaSpecimenImageViaForm`). Library specifically earns the non-Relay raw-pk
    decode, the `to_field_name` conversion, the request-scoped-`queryset` idiom, and the plain-form
    `perform_mutate` rollback case. **The figure is 8, not the 6 the grading pass and the build
    plan wrote** — 6 was true before this slice added two fields; the 8 is re-derived twice
    (8 classes, 8 `DjangoMutationField` rows). Do not copy a 6 forward from any per-cycle artifact.
12. **Decision 13** — anchor `co-clears` (×1); **and the `## Implementation plan` Slice-2 cell**
    ("`registry.py` (THREE form co-clear rows)"). Shipped truth: all three clears exist and are all
    reached, but `registry.py` names none of them (0 `clear_form` occurrences in the 610-line file).
    Each owner announces itself with `register_subsystem_clear(...)` —
    `forms.input_namespace` (`before_bind=True`), `forms.declarations`, `forms.shape_cache` — and
    `registry.clear()` drains `iter_subsystem_clears()`.
13. **Decision 6** — anchor `its own metaclass` (**×3**: Decision 6, the Slice-2 checklist, and one
    further mention; grade all three). Shipped truth:
    `DjangoFormMutationMetaclass = make_meta_validating_metaclass(register_form_mutation, …)` — a
    shared factory over the disjoint plain-form ledger. It shipped as a hand-written
    `class …(type)`; the "own metaclass" **contract** (not `DjangoMutationMetaclass`, not the model
    ledger) is intact and the mechanism is shared.
14. **Decision 8, "How this pipeline actually fires"** — anchor `delegate **here**` (×1); **and the
    Slice-3 checklist.** Shipped truth: both flavors' `resolve_sync` / `resolve_async` come from
    `mutations/sets.py::resolver_seams(...)` (`with_id=False` for the plain flavor, matching
    `mutations/fields.py` #"operation != \"form\""), `bind_form_mutations()`'s whole body is one
    `bind_write_declarations(...)` call, and `mutations/operations.py` now owns the operation
    vocabulary (`NON_DELETE_WRITE_OPERATIONS`, `NON_DELETE_OPERATION_INPUT_KIND`,
    `non_delete_operation_error`) the spec spells inline.
15. **`## Out of scope`** — anchor `AsyncTestClient` (×2, the Out-of-scope bullet and the
    `## Non-goals` bullet). Shipped truth: `django_strawberry_framework/testing/client.py`,
    `testing/__init__.py`, a `conf.py` setting, and
    `examples/fakeshop/test_query/test_client_api.py`. **The file-field-correctness half of the
    `## Non-goals` sentence still holds and must survive the rewrite.**
16. **`## Out of scope`** — anchor `TODO-ALPHA-039` (×3: Out-of-scope, `## Non-goals`,
    `## Key glossary references`). Shipped truth: `django_strawberry_framework/rest_framework/`,
    `tests/rest_framework/`, and three products serializer mutations.
17. **`## Out of scope`** — anchor `TODO-ALPHA-040` (×3). Shipped truth:
    `django_strawberry_framework/auth/mutations.py`,
    `examples/fakeshop/test_query/test_auth_api.py`. It is also the **third**
    `make_declaration_registry` consumer, live evidence for Decision 13's
    shared-mechanics-disjoint-ledgers call and worth citing there.
18. **The spec opener, Decision 2, and every other "frozen" home** — anchor `byte-identical`
    (**×7**) and `froze` (**×26** in the spec, ×13 in the companion). Shipped truth: Decision 2's
    "this card adds **no** field to `FieldError`" is still true of *this card*; the "frozen /
    byte-identical" framing is not true of the envelope's current shape —
    `mutations/inputs.py::FieldError` states #"The type is ADDITIVE, not frozen" and has gained
    `codes` and `path`. Rewrite to "additive; `038` adds no member". **The vocabulary is in the H1
    title itself** ("reusing the frozen `FieldError` envelope"), plus
    `## Key glossary references`, `## Problem statement`, the
    `### Reference-package parity checkpoint` table row, and `## Non-goals`. `CHANGELOG.md`'s
    dated `[0.0.11]` / `[0.0.12]` entries also say "frozen"; those are **observations of their own
    date** in a maintainer-owned, never-edited file and are **not** in scope — I checked so Slice 2
    does not chase them.
19. **Slice-2 checklist, the allowed-key sentence** — anchor `partial_input_class` (×2). **Two
    defects in one sentence, merged from the routed list's items 19 and 25.** (a) Stale content:
    `_ALLOWED_MODELFORM_META_KEYS` = `MODEL_BACKED_WRITE_META_KEYS | {form_class}` =
    `{fields, exclude, permission_classes, operation, select_for_update, form_class}` and
    `_ALLOWED_PLAIN_FORM_META_KEYS` = `COMMON_WRITE_META_KEYS | {form_class}` =
    `{fields, exclude, permission_classes, form_class}`; `select_for_update` is a post-`038`
    (`0.0.14`) row-locking key the `ModelForm` flavor accepts and the plain flavor rejects.
    (b) Ship-time deviation (case 2): **both** sets already existed at `731fecd8` with a ship-time
    comment spelling the split, so the single sentence was an under-description on its own date and
    **Decision 10 states it correctly** — the checklist loses. Rewrite to name both sets.
20. **`## Definition of done` item 8 and the Slice-5 checklist** — anchor `quintet` (×1). Shipped
    truth: all five surfaces landed in `731fecd8`; at `HEAD` the quintet is a **triplet** —
    `pyproject.toml` carries no `version` literal (`[tool.hatch.version]` derives it from
    `__init__.py`, and `AGENTS.md` rule 31 makes that single-sourcing standing law) and `uv.lock`
    carries `source = { editable = "." }` with no version key, so the trailing conditional now
    resolves to "it does not". **Do not "update" the `0.0.12` figures** — the cut this card owned
    happened; only the *mechanism* description is stale.
21. **`## Implementation plan` Slice-2 cell** — anchor `object_type=None` (×1). Shipped truth:
    `build_payload_type(mutation_name, *, object_type: type | None, object_slot: str | None = None)`
    — `object_type` is keyword-**required** with no `None` default;
    `forms/sets.py::bind_form_mutations` selects the model-less shape by passing
    `resolve_object_type=lambda …: None` through `bind_write_declarations`. Decision 6's
    one-builder-one-ledger contract is intact.

**Case (2) — a ship-time deviation, or two spec homes disagreeing. The named side changes
(5 items).**

22. **Decision 8's opening paragraph and its seven numbered steps** — anchor `Ordering correction`
    (×1). **The spec loses**, and this is the highest-value edit available to Slice 2: leaving the
    steps in the draft order behind a chronology the reader must apply makes it a **false**
    contract, not merely a stale one, and `docs/builder/BUILD.md` `## Spec rationale extraction`
    forbids exactly that shape. Renumber to the shipped order — **locate → authorize → decode →
    construct/validate → write → re-fetch → return** — single-sited in
    `mutations/resolvers.py::run_write_pipeline_sync` #"authorize BEFORE decode"; move the
    supersession narrative to the companion as a `**Post-ship:**` bullet.
    **The sweep, measured rather than listed from memory:**
    - `step \d` occurs **11** times in the spec, and every one is inside a Decision: **9** in
      Decision 8 itself (its own step-1/3/4/5 cross-references), **1** in Decision 9
      ("pipeline step 6"), **1** in Decision 11 ("Decision 8 step 2"). `steps \d` occurs 0 times.
    - **The routed list over-enumerated here and it matters.** `## Edge cases and constraints`,
      `## Test plan`, `## Definition of done` and `## Slice checklist` contain the word "step"
      **zero** times, so there are no step citations to fix in any of them; hunting for them
      invites editing something else. What those sections *do* carry is a different defect: the
      **Slice-3 checklist sub-check narrates the pipeline in prose in the superseded order**
      (anchor `dedicated form relation decoder` — decode, then locate, then authorize), and it
      needs the same reordering as the Decision. Grade `## Definition of done` item 4 and the
      `## Test plan` `test_resolvers.py` row for the same prose ordering.
    - **Do not rewrite Decision 8's heading.** Its arrow sequence
      ("instantiate → `is_valid()` → `form.errors` → `save()` → optimizer re-fetch → payload")
      says nothing about decode-versus-authorize, so it survives the renumber untouched — and
      that is load-bearing: **28** in-page `](#decision-8…` links inside the spec plus **14**
      cross-file refs from the rationale companion resolve through it. Rewriting the heading would
      strand all 42 (`START.md`: a heading rewrite strands every ordinal and every prose citation).
    - Cite by **content**, never by ordinal, in the replacement text. The two rows this slice
      landed for the `get_form` hook cite the hook and not a step number, so the renumber cannot
      rot them.
23. **Decision 8's "Helper reuse" paragraph** — anchor `payload_object_slot` (×2). **The spec
    loses, and it was wrong on its own date:** `payload_object_slot` was already **public** in
    `mutations/inputs.py` at `731fecd8^`, i.e. before `038` began. The spec's own `## Current state`
    bullet says so, so **two spec homes contradict each other** and `## Current state` is the right
    one. Remove `payload_object_slot` from the promotion list (item 7 supplies the measured
    locations of the other nine).
24. **Decision 8's "Helper reuse" paragraph** — anchor `picks one` (×1). **The spec loses.** An
    unresolved build instruction ("the lighter edit … the cleaner edit … Slice 3 picks one and
    names it") has no place in a shipped contract. Slice 3 picked underscore-drop-in-place; no
    `mutations/_pipeline.py` exists. State where the helpers live and move the two-options
    deliberation to the companion.
25. **`## Edge cases and constraints`, the plain-form authorization bullet** — anchor
    `requires an explicit` (×1). **The bullet loses.** An unset `permission_classes` does not fail
    configuration — it defaults to `(DenyAll,)`, which is what Decision 11 settles. Rewrite to the
    deny-by-default posture and the `permission_classes = []` opt-out, and add the
    `DjangoModelPermission` rejection from item 10.
26. **Decision 5, axis 1's parenthetical** — anchor `_payload_type_name` (×1). **The spec loses.**
    `_payload_type_name` is a **bind** output and `DjangoMutationField` is constructed at import,
    before the bind runs, so a check requiring it could never pass —
    `mutations/fields.py::_validate_mutation_target` says so explicitly. Replace with the shipped
    protocol: `_mutation_meta` present, plus callable `resolve_sync` / `resolve_async` /
    `input_type_name` and a non-`None` `input_module_path`; concreteness is then a separate
    own-snapshot + current-ledger check.

**Chronology and undecodable-reference residue the move surfaced and could not discharge. These
appear in no other section's list (6 items).**

27. **Three chronology hedges whose referent left the spec with Slice 0's move**, each now
    pointing at deliberation the reader cannot find. Anchors, one line each: Decision 6
    `fully-pinned` (×1) — plus that paragraph's "preferred / fallback" lead-in vocabulary, which
    was the Risks section's; Decision 10 `prior contradiction` (×1); Decision 7
    `This replaces the earlier` (×1). All three are meta-framing with no contract content, so
    trimming changes nothing a builder implements.
28. **Two sentences cite "the review" as an authority the spec no longer carries** — anchor
    `the review names` (×2): Decision 7's shape-identity paragraph ("the two collision cases the
    review names") and Decision 8's required-extra bullet ("both failure modes the review names").
    Neither the review document nor its findings are in the spec or the companion.
29. **The `P1` / `P2` / `P3` priority labels and the bare `#4`-`#8` / `AR-*` / `Medium-1`
    citations are undecodable from the spec** — anchors `AR-H1` (×1) and `Medium-1` (×1); `(P1)`
    occurs 11× and `(P2` 29× in the spec (and 3× / 4× in the companion). The `AR-*` and `Medium-1`
    identifiers belong to `spec-036`'s review, the `#N` ones to `038`'s own. A shipped contract
    keying its own emphasis to an unnamed document is a chronology the reader must reconstruct.
    Slice 2's call whether to resolve them to plain emphasis or to cite the source.
30. **`## Key glossary references` describes a shipped card's closeout in the future imperative** —
    anchors `provisional` (×1) and `Slice 5 promotes both entries` (×1), of a card that shipped
    three patch releases ago. State the shipped ownership without promising future work. Whether
    the `docs/GLOSSARY.md` correction actually landed is out of reach behind the scope fence — the
    grading pass verified the rendered result independently (both entries `shipped (0.0.12)`, both
    in Public exports and the Mutations browse row, the `DjangoFormMutation` body rewritten to the
    model-less-sibling shape), so the promise is discharged and only the tense is wrong.
31. **`## Doc updates` and the `## Definition of done` Slice-5 / Slice-7 / Slice-8 items are
    entirely future tense about shipped work** — anchors `Coming next` (×2: the Slice-5 checklist
    and the `## Doc updates` package-docs bullet) and `TODO-ALPHA-038-0.0.12` (×2: `## Current
    state`, where it is a dated observation that stands, and the `## Doc updates` card-wrap bullet,
    where it names a card that is now `DONE-038-0.0.12` and is therefore stale). Same class as
    item 30, same fence constraint on verifying each landed.
32. **The `## Implementation plan` Slice-2 cell still stages a discharged TODO anchor** — anchor
    `TODO-anchor only` (×1): "`mutations/fields.py` (TODO-anchor only — the `_input_type_name` body
    is now byte-identical to the `input_type_name` seam; Slice 3 deletes it)".
    `grep -rn 'TODO(spec-038'` returns nothing in source or tests and `def _input_type_name` is
    gone package-wide, so the cell describes a staging step that completed. **This item is in no
    other routed list.**

**Spec ADDITIONS this slice's own measurements earned. The spec is not wrong here; it is silent
where silence has now been shown to mislead (2 items).**

33. **Decision 8 step 4's file clause is CORRECT and must survive the renumber verbatim, with one
    clause appended** — anchor `re-supplied` (×1). Keep "`files = provided_files` **only** — an
    omitted file field is preserved by the bound `form_class(instance=…)` via its `initial`, never
    re-supplied and never cleared" unchanged, and append: "The reconstruction therefore contributes
    **no key at all** for a file field: `model_to_dict` yields the stored relative path, which is
    not a re-bindable `data=` value for a field fed from `files=`." **Why, measured twice by two
    workers:** no wire-level row of any design can detect the exclusion's removal, because a file
    widget's `value_from_datadict` reads `files` only, so a stray `data=` key is inert. The
    exclusion is a data-hygiene boundary whose only observable is the reconstructed payload — and a
    reader taking the current sentence as the whole story believes a live test covers it, which for
    three patch releases nobody did.
34. **Decision 8's `get_form_kwargs` step needs a reword and an appended clause** — anchor
    `without changing the generated input shape` (×1); the `## Test plan` `test_resolvers.py` row
    carries the same claim. Reword to: "or to pass the request-scoped `ModelChoiceField` queryset
    the form narrows with in its own `__init__` — `get_form_kwargs` returns **constructor kwargs**,
    so the hook is the channel and the form applies it — **without changing the generated input
    shape**", then append: "A hook that injects a value the narrowed input cannot carry is only
    observably working if a test asserts the **written row**: the wire envelope of a failed write is
    identical whether the injection ran or not, because a missing non-nullable FK raises
    `IntegrityError` too and maps to the same `\"__all__\"` envelope." **Why:** the current phrasing
    reads as though the hook mutates `field.queryset` itself, which it cannot; and the appended
    clause is measured (entry 4, reproduced by two workers — deleting the injection left the
    write-time row green, and only a positive leg reading back `category_id` distinguishes the two).

**Case (1) — planned and never built. DISCHARGED by this slice's build; close with citations, do
not rewrite (1 item).**

35. **The four former `DROPPED` homes** — anchors `get_form(self, info` (×1) and
    `omitted file preserved` (×1), plus the `## Test plan` live `IntegrityError` bullet, the two
    `## Edge cases` file bullets, and `## Definition of done` item 5. All four contracts are now
    pinned; **the spec was right and the tests were owed**. Re-grade each home to
    `BUILT-CONFORMANT` citing the node ids in `### The four DROPPED verdicts, re-graded` above.
    Two specifics Slice 2 must not get wrong:
    - **`## Definition of done` item 5 and the `## Test plan` live bullet stand as written — no
      wording change.** The mock-free live `ModelForm` write-time `IntegrityError` row exists, so
      the GAP-3 escalation's rejected alternative (rewriting both homes to cite the plain-form
      library row) **stays rejected**. Cite the **pair**
      `::test_create_default_category_item_via_form_injects_the_default_category` +
      `::test_create_default_category_item_via_form_write_time_integrity_error_uses_envelope`;
      either alone under-determines the contract.
    - The `get_form` clause and the file clause keep their text; the file clause gains item 33's
      append and nothing else.

**Three notes for Slice 2 that are NOT spec edits.**

- **N1 — row placement, not staleness. Do not "fix" these.** The `## Test plan`
  `test_converter.py` row asks for the `ModelChoiceField` / `ModelMultipleChoiceField` id mapping
  (Relay `GlobalID` vs raw pk), the reverse map, and `base_fields` discovery **in
  `test_converter.py`**; all three are pinned in `tests/forms/test_inputs.py` instead, and
  correctly so — `forms/converter.py::convert_form_field` deliberately returns `annotation=None`
  for relation and file kinds because the id type is resolvable only at the `forms/inputs.py` build
  site, where the backing column and the related primary `DjangoType` are known. If Slice 2 touches
  the row, move the clauses to the `test_inputs.py` row rather than declaring a gap.
- **N2 — `## Current state` is graded, and no edit is owed.** All five bullets are dated
  **observations** and stand under `docs/builder/BUILD.md`
  `### `## Current state`: observations stand, predictions do not`. The borderline clause Slice 0
  flagged — "there is no joint cut to defer the version bump to" — is an **inference** rather than
  a reading, but the inference held (`038` did own the cut, and `CHANGELOG.md`
  `## [0.0.12] - 2026-06-23` shows it shipped alone). One clause needs a light touch: the bullet's
  parenthetical quoting a `docs/TREE.md` state that has since been replaced by the shipped `forms/`
  summary lines is a **quotation of a generated body**, so diff the quotation against the current
  render before deciding whether the observation framing carries it (`START.md`: "Doc quotes a
  generated body → diff quotation vs render").
- **N3 — the `TODAY.md` drift is deferred work, not a spec edit.** Ruled in
  `### Ruling 2` above: path (b), owner **the maintainer**, catalog bullet written out verbatim for
  `docs/builder/bld-038-final.md`. Slice 2 touches nothing for it and must not edit `TODAY.md`.

### Summary

Slice 1 is complete. The grading pass graded `spec-038`'s whole corpus against `HEAD` as 140
verdict rows and proved four gaps, all of them missing assertions rather than missing behavior —
two of them behind `or` disjuncts no test could make decisive, the shape `fail_under = 100`
structurally cannot see. A builder closed all four with **10 new node ids** across two package
test modules and one live module, plus one example-app `ModelForm` and two example-app mutation
fields; a review round added the positive leg that makes the GAP-3 pair distinguish its documented
uniqueness driver from a NOT-NULL degradation. **No package `.py` was edited at any point**, which
I measured rather than accepted (0 of 12 cycle tokens across a 491,789-byte package working-diff,
positive control passing) — so the plan's build-wide hot-path `none` holds on its stated ground,
and the public surface is not even dirty.

Every load-bearing figure re-derived: the ten node ids collect and pass; the 300-file /
7,228,167-byte `HEAD` population and its three zero-counts (with a 6,038-hit positive control);
`def get_form(` 0 → 2, which is GAP-1's closure stated as a measurement; the products
form-mutation surface at **8** (8 classes, 8 `DjangoMutationField` rows); the full parallel sweep
at **4 failed, 7240 passed, 40 skipped, 0 collection errors**, identical in every figure to the
last two passes, the four failures being the concurrent session's uncommitted `sets_mixins.py`
edit and their escalation staying with Worker 0; all five proof anchors matching exactly once with
no mutation marker anywhere; and the floor re-executed at Django 5.2.16 / strawberry 0.316.0 /
Python 3.10.19 with the shared `.venv` read as the newest supported set and unmutated.

Twelve checklist boxes audited, none un-ticked, none newly ticked, none left open. Two judgement
calls decided: Worker 3's failability exemption for the apply-changes pass is **confirmed** —
`### What needs a proof, and what does not` governs and defines the acceptance rule's subject, and
an example-app constructor-kwarg assignment that was not new to that pass is not a boundary; and
the `TODAY.md` deferral is homed on **path (b) with the maintainer named in prose**, because the
fence that bars the file bars the kanban DB with it, with path (a) recorded as the one-move remedy
the maintainer can authorize.

The consolidated Slice-2 list is **35 items plus 3 non-edit notes**, from 54 raw items across six
sections, with the absorption of each raw item recorded so nothing is silently dropped.
Consolidating it was not clerical: it corrected the routed list's step-citation sweep (the four
sections it named carry the word "step" zero times, while the Slice-3 checklist sub-check it did
not name narrates the superseded order in prose), found that the `model_to_dict` formula has four
normative homes rather than three, merged two items that target one sentence, replaced three
quoted anchors that do not resolve because they wrap across source lines, established that
Decision 8's heading survives the renumber and that rewriting it would strand 42 anchor
references, and surfaced six items from Slice 0's artifact that appeared in no other list.

### Spec changes made (Worker 1 only)

**None; Slice 2 owns the spec rewrite.** The spec and its rationale companion were opened
read-only. The spec's status/header lines were re-verified per `worker-1.md`
`## Spec status-line re-verification` and are **not falsified** — "Shipped in `0.0.12` (card
`DONE-038-0.0.12`)" is accurate and the `0.0.12` figures throughout describe a cut that happened.
The one defect in the header is the H1 title's "reusing the frozen `FieldError` envelope", which is
consolidated item 18 and belongs to Slice 2's rewrite of that vocabulary rather than to a
status-line repair.

**Deferral reasons owed for un-ticked checklist boxes: none.** Every box in the Plan's
`### Spec slice checklist (verbatim)` is `- [x]` and every tick survived the audit.

### Final status

`final-accepted`
