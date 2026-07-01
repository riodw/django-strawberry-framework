# Review: Serializer Mutation Implementation

Scope: final verification pass for [spec-039][spec-039], including the requested full test
run, direct pre-commit hook equivalents, and a renewed review of the serializer mutation lane
against the DRF-first contracts in [the fakeshop query README][fakeshop-readme].

## Verification Results

- `uv run pytest` now passes: `2705 passed, 4 skipped, 4 xfailed`, with total coverage at
  `100.00%`.
- `uvx pre-commit run --all-files` passes. The local hook entries also passed when run
  directly: `uv run python scripts/build_kanban_tracked_path_constants.py`,
  `uv run python scripts/check_trailing_commas.py --fix`, `uv run ruff format .`, and
  `uv run ruff check --fix .`.

## Fixed During Verification

### Unsupported unbound `ModelField` wrapped columns crashed

`django_strawberry_framework/types/converters.py::scalar_for_field` assumed every unsupported
Django field had `field.model`. A manually constructed field wrapped by
`serializers.ModelField` instead raised `AttributeError`, bypassing the intended
`ConfigurationError`.

Fix applied: unsupported fields now format a stable `<unbound>.<field>` label when no model is
attached, preserving the fail-loud converter contract.

### New branches were below the 100% coverage gate

The first full pytest run exposed uncovered branches in the new serializer mutation helpers:
bare `ErrorDetail` code extraction, empty many-relation decode, file/scalar agreement drift,
raw-pk relation queryset scoping, many-relation queryset scoping, debug shape source reporting,
`allow_empty=false` metadata, unbound model-backed fields, non-scalar declared model-backed
fallback, and `visible_related_objects()` without a registered primary type.

Fix applied: focused package tests now cover those branches without duplicating live HTTP
coverage that belongs in `examples/fakeshop/test_query/`.

## Open Findings

### P1: Visibility scoping still replaces serializer relation querysets

`django_strawberry_framework/rest_framework/resolvers.py::_scope_relation_querysets_to_visibility`
reassigns each runtime relation field's queryset to the visibility-scoped queryset. That makes
visibility an alternative source of truth instead of an additional constraint, so a serializer
author's own `PrimaryKeyRelatedField(queryset=...)` restrictions can be erased before
`serializer.is_valid()` runs.

Example failure mode: a serializer intentionally accepts only
`Branch.objects.filter(city="allowed")`, while GraphQL type visibility permits every branch.
The reassignment can allow a visible branch from another city even though DRF's serializer
queryset would have rejected it.

Recommended fix: preserve the runtime field queryset as the base contract and apply visibility
as an additional constraint. In practice, compose the original queryset with the visibility
queryset by primary key, or add a helper that scopes an existing queryset through the related
type's visibility hook without widening it. Add live or package coverage for a
visible-but-serializer-disallowed single relation and many relation.

### P1: `Meta.injected_fields` proves presence, not runtime acceptance

`django_strawberry_framework/rest_framework/resolvers.py::_assert_injected_fields_supplied`
checks that each injected key exists in `serializer.initial_data`, but it does not prove that
the runtime serializer still exposes that field, that the field is writable, or that its source
matches the schema-time field that justified subtracting it from the create guard.

That leaves a drift gap: `Meta.injected_fields` can waive a required schema-time field, the
resolver can inject the key into data, and a runtime serializer can drop or ignore the field.
The guard passes because the key is present, not because DRF will validate or save it.

Recommended fix: validate injected fields at class validation against the schema-time field
map, then validate them again against `serializer.fields` at runtime with the same present,
writable, source, kind, and relation-model checks used for input-exposed fields.

### P2: Hook fingerprint omits schema-affecting state

`django_strawberry_framework/rest_framework/inputs.py::serializer_schema_fingerprint` tracks
broad field identity and flags, but generated SDL now depends on more than that: serializer
choice members, multiple-choice element enums, `help_text`, constraint-summary inputs, list
child conversion, `ModelField` wrapped fields, and relation details can all affect the input
type or validation contract.

Because those values are outside the fingerprint, a nondeterministic schema hook can change
generated GraphQL input types or descriptions without tripping the drift guard.

Recommended fix: fingerprint the derived serializer input shape and SDL metadata inputs, or
expand the raw fingerprint to include every field attribute that can change annotations,
requiredness, descriptions, enum members, relation model, or converter behavior.

### P2: `input_type_name()` re-reads the schema hook outside the guard

`django_strawberry_framework/rest_framework/sets.py::SerializerMutation.input_type_name`
recomputes the serializer field map through `get_serializer_for_schema()` to derive the lazy
input type name. The guarded fingerprint comparison lives in
`SerializerMutation.build_input`, and the type-name path does not obviously reuse the already
materialized shape.

Recommended fix: make `input_type_name()` use the cached/materialized input shape when
available, or run the same fingerprint validation before using a recomputed field map. The
schema-time hook should have one authoritative read path.

### P2: Explicit serializer choices can disappear on model-backed scalar fields

The conflict policy rejects many declared serializer fields whose scalar disagrees with the
backing model column, but a declared `serializers.ChoiceField` over a plain model scalar can
still collapse back to the model scalar path in
`django_strawberry_framework/rest_framework/serializer_converter.py::_model_backed_scalar_annotation`.

If serializer-declared choices are part of the public mutation contract, this should either
emit the generated serializer-only enum or fail loudly as an unsupported model-backed override.
Silently returning `String` loses the contract the consumer declared.

Recommended fix: treat declared serializer `ChoiceField` and `MultipleChoiceField` choices as
schema-affecting overrides even when their `source` maps to a model column. Add a regression
test for `ChoiceField(source="name", choices=...)` over a non-choice model field.

### P3: Standing docs still contain pre-revision behavior

The implementation has moved to serializer-only enums and explicit injected field declarations,
but some standing text still describes older behavior:

- [spec-039][spec-039] still has base text that describes `ChoiceField -> str` and
  `MultipleChoiceField -> list[str]`, while later revision text changes them to generated
  enums.
- `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.get_serializer_kwargs`
  still describes overriding the hook as the create-guard waiver path, even though
  `Meta.injected_fields` is now the auditable primary contract and the hook waiver is legacy.

Recommended fix: rewrite the earlier spec table and local docstrings so the final rule set is
not split between obsolete base text and later revision notes.

## Positive Checks

- The full fakeshop live GraphQL lane passes, including the serializer mutation acceptance
  tests required by `examples/fakeshop/test_query/README.md`.
- The converter registry remains explicit and does not add a base `serializers.Field`
  catch-all.
- `FieldError` codes and paths remain additive on the existing GraphQL shape and preserve
  DRF/Django error metadata.
- The batched many-relation decode path is covered and avoids one visibility query per member.
- `Meta.select_for_update` remains opt-in and reaches the update lookup inside the write
  transaction.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

[spec-039]: spec-039-serializer_mutations-0_0_13.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

[fakeshop-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
