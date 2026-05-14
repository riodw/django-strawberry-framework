# Review: `django_strawberry_framework/types/base.py`

Status: verified

## DRY analysis

- Existing patterns reused: `DjangoType.__init_subclass__` builds one selected-field tuple and threads it through annotation synthesis and `DjangoTypeDefinition` in `django_strawberry_framework/types/base.py:86-130`. Consumer-facing typo errors reuse `_format_unknown_fields_error` in `django_strawberry_framework/types/base.py:251-259`, and the interface validator follows the explicit shape-rejection pattern covered in `tests/types/test_relay_interfaces.py:75-144`. Relation metadata is already precomputed once into `FieldMeta` objects in `django_strawberry_framework/types/base.py:90` and stored canonically on `DjangoTypeDefinition.field_map` in `django_strawberry_framework/types/definition.py:18-31`.
- New helpers a fix might justify: one Meta option normalizer with the single responsibility "validate and normalize `Meta.model`, `Meta.fields`, `Meta.exclude`, and `Meta.optimizer_hints` before any registry, `_meta`, `set(...)`, `tuple(...)`, or `.items()` use." It would serve `_validate_meta`, `_select_fields`, `_normalize_fields_spec`, `_normalize_sequence_spec`, and `_validate_optimizer_hints`.
- Duplication risk in the current file: `_record_pending_relation` re-derives relation kind and nullability in `django_strawberry_framework/types/base.py:610-625` even though `FieldMeta` documents itself as the SSoT for that shape in `django_strawberry_framework/optimizer/field_meta.py:3-17` and exposes the normalized `nullable` field in `django_strawberry_framework/optimizer/field_meta.py:81-121`. Sibling duplicates remain in `django_strawberry_framework/types/converters.py:222-234` and `django_strawberry_framework/types/resolvers.py:180-214`; because `KANBAN.md` tracks this as `BACKLOG-013`, keep it as the explicit folder-pass DRY follow-up unless Worker 2 chooses to take the whole anchored consolidation.

## High:

None.

## Medium:

### Meta option shape validation leaks raw errors and silently ignores invalid hints

`_validate_meta` only checks that `Meta.model` is present, then later code assumes it is a Django model class. `_select_fields` and the definition normalizers also assume `fields` / `exclude` are iterable specs, and `_meta_optimizer_hints` treats any falsy non-mapping value as unset. Confirmed failure shapes include `Meta.model = "Category"` raising `AttributeError`, `Meta.fields = 123` / `Meta.exclude = 123` raising `TypeError`, and `Meta.optimizer_hints = []` being accepted as `{}`. These are consumer-facing `Meta` configuration errors and should be reported as `ConfigurationError` with the same clarity as unknown fields. Normalize these shapes before use: require `model` to be a `models.Model` subclass, accept only `"__all__"` or non-string sequences for `fields`, accept only non-string sequences for `exclude`, and require `optimizer_hints` to be a mapping when declared.

```django_strawberry_framework/types/base.py:375:393
    if getattr(meta, "model", None) is None:
        raise ConfigurationError("Meta.model is required")

    declared = {k for k in meta.__dict__ if not k.startswith("_")}
...
    return _validate_interfaces(meta)
```

```django_strawberry_framework/types/base.py:472:504
    fields_spec = getattr(meta, "fields", None)
    exclude_spec = getattr(meta, "exclude", None)
...
        unknown = sorted(set(exclude_spec) - valid_names)
```

```django_strawberry_framework/types/base.py:241:248
def _meta_optimizer_hints(meta: type) -> dict[str, Any]:
    """Return ``meta.optimizer_hints`` as a dict, or ``{}`` when unset/empty.
...
    return getattr(meta, "optimizer_hints", None) or {}
```

### `optimizer_hints` accepts selected scalar fields that the walker never reads

`_validate_optimizer_hints` checks hint keys against every selected field, including scalars. The walker, however, reads hints only after the scalar branch has already continued, so `optimizer_hints = {"name": OptimizerHint.SKIP}` is accepted, stored on the definition, and never observed. This is the same silent-dead-intent class as the excluded-field guard already pinned in `tests/types/test_base.py:212-228`. Validate hint keys against selected relation fields, not all selected fields, and add focused coverage for a selected scalar hint raising `ConfigurationError`.

```django_strawberry_framework/types/base.py:415:438
    valid_field_names = {f.name for f in model._meta.get_fields()}
    selected_names = {f.name for f in fields}
...
    bad_values = sorted(k for k, v in hints.items() if not isinstance(v, OptimizerHint))
```

```django_strawberry_framework/optimizer/walker.py:139:166
        if not django_field.is_relation:
            # Scalar projection. When ``django_name == "id"`` and the
...
            continue

        full_path = f"{prefix}{django_name}"
...
        hint = hints_map.get(django_name)
```

## Low:

### `base.py` docstrings describe old Meta keys and relation dispatch

The module docstring lists only `fields`, `exclude`, `name`, and `description`, omitting the shipped `optimizer_hints` and `interfaces` keys. `_build_annotations` says relation fields are routed through `convert_relation`, but the implementation now performs the registry/pending-relation handling inline and imports only `resolved_relation_annotation`. Update these docstrings after the logic findings are settled so the public collection pipeline and function contract match the code.

```django_strawberry_framework/types/base.py:10:18
A nested ``Meta`` class declares the model and (optionally) ``fields``,
``exclude``, ``name``, and ``description``. Subclassing
triggers the collection pipeline, which:
...
2. Validates ``Meta`` (required ``model``, ``fields``/``exclude``
   exclusivity, deferred-key rejection).
```

```django_strawberry_framework/types/base.py:519:522
    Field-by-field dispatch: every entry in ``fields`` is routed through
    ``convert_relation`` if ``field.is_relation`` is true, or
    ``convert_scalar`` otherwise. The caller pre-computes the list with
    ``_select_fields(meta)`` so this function does not need ``meta``.
```

## What looks solid

- The static helper was run for this types file: `python scripts/review_inspect.py django_strawberry_framework/types/base.py --output-dir docs/review/shadow --stdout`.
- Registry finalization is guarded before registration mutates state in `django_strawberry_framework/types/base.py:81-88`.
- Interface validation has clear shape checks for strings, non-sequences, non-class entries, non-interface classes, `DjangoType` subclasses, and duplicates in `django_strawberry_framework/types/base.py:302-350`, with focused coverage in `tests/types/test_relay_interfaces.py:52-150`.
- Consumer-authored relation and assigned scalar fields are collected before annotation synthesis and stored on `DjangoTypeDefinition`, preserving resolver overrides through finalization in `django_strawberry_framework/types/base.py:92-130`.
- The direct `relay.Node` inheritance suppression branch in `_build_annotations` is explicit and covered by dedicated Relay tests, avoiding the previously documented `NodeIDAnnotationError` path.

### Summary

`types/base.py` owns the right orchestration boundary for `DjangoType`, and most of the collection pipeline is already centralized. The remaining review-worthy issues are Meta-shape validation gaps that leak raw Python errors or accept dead optimizer intent, plus docstrings that lag behind the current `interfaces` and inline relation-resolution behavior.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/types/base.py` — validated `Meta.model`, normalized `fields` / `exclude` shape before selection/storage, required `optimizer_hints` to be a mapping when declared, and restricted optimizer hint keys to selected relation fields.
- `tests/types/test_base.py` — added focused Meta-shape and scalar-hint rejection coverage.

### Tests added or updated

- `tests/types/test_base.py::test_meta_model_must_be_django_model_class` — pins invalid `Meta.model` as `ConfigurationError`.
- `tests/types/test_base.py::test_meta_field_selectors_must_have_valid_shapes` — pins invalid `fields` / `exclude` shapes as `ConfigurationError`.
- `tests/types/test_base.py::test_meta_optimizer_hints_must_be_mapping_when_declared` — pins declared non-mapping hints, including falsy `[]`, as `ConfigurationError`.
- `tests/types/test_base.py::test_meta_optimizer_hints_for_selected_scalar_field_raises` — pins selected scalar hints as dead optimizer intent.

### Validation run

- `uv run ruff format .` — passed, 92 files unchanged.
- `uv run ruff check --fix .` — passed.
- `uv run pytest tests/types/test_base.py` — assertions passed, then failed the expected single-file coverage gate (`45 passed, 1 skipped`; total coverage 45.36% below `fail_under=100`).
- `uv run pytest tests/types/test_base.py --no-cov` — passed, `45 passed, 1 skipped`.

### Notes for Worker 3

- Static helper output was generated under `docs/review/shadow/django_strawberry_framework__types__base.*`; artifact line references use original source-file line numbers.
- I read the static helper overview before editing and did not edit generated shadow files.
- The pre-existing `_record_pending_relation` nullable / `FieldMeta` SSoT change in `types/base.py` was preserved and worked around, not reverted.
- I left the Low module / `_build_annotations` docstring finding for the later comment/docstring pass. The only docstring wording changed here is `_meta_optimizer_hints`, because the function no longer uses the old broad falsy fallback.

---

## Verification (Worker 3)

### Logic verification outcome

Medium `Meta option shape validation leaks raw errors and silently ignores invalid hints`: addressed. `Meta.model` is checked before any `_meta` access or `meta.model.__name__` error formatting, `fields` / `exclude` are normalized through `collections.abc.Sequence` with explicit string rejection, and declared non-mapping `optimizer_hints` now raises `ConfigurationError` instead of falling through as `{}`.

Medium `optimizer_hints` accepts selected scalar fields that the walker never reads`: addressed. Hint keys are now validated against selected relation fields, with selected scalars rejected as dead optimizer intent. The resulting "Available" set is the selected relation surface, which matches the walker branch that actually consumes hints.

Low docstring/comment finding remains open for the required comment/docstring pass. The module docstring still omits shipped `optimizer_hints` / `interfaces`, and `_build_annotations` still describes relation dispatch as `convert_relation`-based even though relation resolution is now inline.

Outcome: logic accepted; awaiting comment pass.

### DRY findings disposition

Accepted for this logic pass. Worker 2 reused `_meta_optimizer_hints` and the existing `_format_unknown_fields_error` shape instead of adding parallel ad hoc validation, and centralized selector shape checks in `_normalize_fields_spec` / `_normalize_sequence_spec` for validation, selection, and stored definition specs. The pre-existing `_record_pending_relation` nullable / `FieldMeta` SSoT change was preserved; it remains an anchored follow-up rather than an accidental broadening of this cycle.

### Temp test verification

- Temp test files used: none.
- Disposition: not needed; focused permanent tests cover both Medium findings.

### Verification outcome

Focused validation passed:

- `uv run pytest tests/types/test_base.py --no-cov` — passed, `45 passed, 1 skipped`.
- `uv run ruff format --check django_strawberry_framework/types/base.py tests/types/test_base.py` — passed.
- `uv run ruff check django_strawberry_framework/types/base.py tests/types/test_base.py` — passed.

Top-level `Status:` remains `fix-implemented`; checklist remains unchecked until comment/docstring review and changelog disposition are complete.

---

## Comment/docstring pass

Worker 2 completed the Low docstring finding after Worker 3 accepted the logic pass.

### Files touched

- `django_strawberry_framework/types/base.py` — updated the module docstring to include shipped `Meta.optimizer_hints` and `Meta.interfaces`, clarified the current Meta validation pipeline, and updated `_build_annotations` to describe inline relation handling with `resolved_relation_annotation` / `PendingRelation` plus scalar `convert_scalar` dispatch.

### Nearby comment/docstring updates

- `django_strawberry_framework/types/base.py::_meta_optimizer_hints` — removed stale "unset/empty" wording that could imply falsy non-mapping declarations still collapse to `{}`.
- `django_strawberry_framework/types/base.py::_validate_meta` — documented Django-model-class validation and shape validation before field selection / hint validation.
- `django_strawberry_framework/types/base.py::_validate_optimizer_hints` — documented the selected-relation-only hint surface and corrected the error-formatting note so value errors are not described as unknown-field errors.

### Validation run

- `uv run ruff format django_strawberry_framework/types/base.py` — passed, 1 file left unchanged.
- `uv run ruff check django_strawberry_framework/types/base.py` — passed.

### Notes for Worker 3

- This pass changed comments/docstrings only. No accepted logic, tests, checklist items, `CHANGELOG.md`, or commits were changed.

---

## Verification (Worker 3, comment/docstring pass)

### Comment/docstring verification outcome

Comments accepted. The module docstring now lists shipped `Meta.optimizer_hints` and `Meta.interfaces`, and the collection pipeline describes Django-model-class validation, supported option shapes, relation-only optimizer hints, and interface validation. `_build_annotations` now describes the actual scalar `convert_scalar` path plus inline relation handling through `resolved_relation_annotation` / `PendingRelation`, instead of the obsolete `convert_relation` dispatch.

Nearby updated docstrings are also consistent with the final behavior: `_meta_optimizer_hints` no longer implies falsy non-mapping declarations collapse to `{}`, `_validate_meta` documents the pre-selection shape checks, and `_validate_optimizer_hints` names the selected-relation-only hint surface while separating field-name errors from value errors.

### Verification outcome

comments accepted; awaiting changelog disposition

Top-level `Status:` remains `fix-implemented`; checklist remains unchecked until Worker 2 records the changelog disposition.

---

## Changelog disposition

Changelog edit warranted: yes. The accepted fix changes consumer-facing `DjangoType.Meta` validation by converting raw Python errors and silently ignored invalid `optimizer_hints` declarations into explicit `ConfigurationError` failures, and it rejects selected scalar optimizer hints that the walker cannot observe. That is release-note-worthy API behavior for pre-alpha consumers.

What was done: no `CHANGELOG.md` edit was made. `AGENTS.md` forbids changelog edits unless explicitly instructed, and the active review plan does not authorize Worker 2 to edit `CHANGELOG.md` for this cycle. The changelog entry is deferred to the maintainer or a separately authorized changelog pass.

Worker 2 set top-level `Status:` to `fix-implemented` for Worker 3's final verification.

---

## Verification (Worker 3, final)

### Final verification outcome

Logic, DRY, comments/docstrings, validation, and changelog disposition are accepted. The two Medium findings are covered by focused permanent tests, the Low docstring drift now matches the final behavior, and the changelog disposition correctly records that the consumer-facing validation change is release-note-worthy but deferred because `CHANGELOG.md` edits were not authorized.

### Validation run

- `uv run pytest tests/types/test_base.py --no-cov` — passed, `45 passed, 1 skipped`.
- `uv run ruff format --check django_strawberry_framework/types/base.py tests/types/test_base.py` — passed.
- `uv run ruff check django_strawberry_framework/types/base.py tests/types/test_base.py` — passed.

### Verification outcome

cycle accepted; verified

---

## Iteration log

Each Worker 2 re-pass appends a `## Fix report (Worker 2, pass <N>)` section here. Each Worker 3 re-verification appends a `## Verification (Worker 3, pass <N>)` section here. Do not edit prior entries; append.
