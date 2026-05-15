# Review: `django_strawberry_framework/types/resolvers.py`

Status: verified

## DRY analysis

- Existing patterns reused: relation resolver attachment consumes `DjangoTypeDefinition.selected_fields` and `consumer_assigned_relation_fields` from the finalizer hand-off in `django_strawberry_framework/types/finalizer.py:87-94`; context reads reuse the shared optimizer/resolver helper and constants in `django_strawberry_framework/optimizer/_context.py:34-82`; resolver identities reuse `resolver_key` / `runtime_path_from_info` from the optimizer planning layer in `django_strawberry_framework/types/resolvers.py:55-61`; relation shape classification reuses `relation_kind` from `django_strawberry_framework/utils/relations.py:32-58`.
- New helpers a fix might justify: none for the confirmed Low finding; accepting or documenting the collapsed N+1 `kind` values can be fixed locally in `_check_n1` without a new abstraction. The broader relation-shape SSoT migration should use the existing `FieldMeta` / `DjangoTypeDefinition.field_map` path documented in `django_strawberry_framework/optimizer/field_meta.py:1-17` and `django_strawberry_framework/types/base.py:117-126`.
- Duplication risk in the current file: `_make_relation_resolver` still re-derives relation kind and `attname` through `relation_kind(field)` plus raw `getattr(field, "attname", None)` in `django_strawberry_framework/types/resolvers.py:180-214`, matching the already-anchored sibling duplication in `django_strawberry_framework/types/converters.py:227-239`; `KANBAN.md:893-918` tracks this as BACKLOG-031, so it remains a folder-pass / backlog follow-up rather than a new file-local defect. The helper surfaced only the repeated literal `reverse_one_to_one`, which is not a meaningful local DRY defect.

## High:

None.

## Medium:

None.

## Low:

### `_check_n1` documents a `relation_kind` contract it does not fully honor

`_check_n1` says its `kind` argument is the field's `relation_kind`, but the implementation only treats the collapsed value `"many"` as many-side. A caller following that docstring with the real classifier output `"reverse_many_to_one"` would fall into the single-valued cache path and could incorrectly skip strictness when `root.__dict__` happens to contain the relation name. The generated resolver currently avoids the bug by passing `kind="many"` for both many-side shapes, so normal schema execution is not broken; this is a local private-helper contract drift. Either update the docstring to name the collapsed values `_check_n1` accepts, or make `_check_n1` recognize both `"many"` and `"reverse_many_to_one"` as many-side.

```django_strawberry_framework/types/resolvers.py:121:137
    ``kind`` is the ``relation_kind`` of the field being resolved
    (``"many"``, ``"reverse_one_to_one"``, ``"forward"``). When it is
    ``None`` (legacy direct calls in tests), the function falls back to
    the single-valued cache check, which is the conservative shape that
    used to be the only branch.
    """
    context = getattr(info, "context", None)
    planned = _get_context_value(context, DST_OPTIMIZER_PLANNED)
    if planned is None:
        return
    key = resolver_key(parent_type, field_name, runtime_path_from_info(info))
    if key in planned:
        return
    if kind == "many":
        lazy = _will_lazy_load_many(root, field_name)
    else:
        lazy = _will_lazy_load_single(root, field_name)
```

```django_strawberry_framework/types/resolvers.py:187:193
    kind = relation_kind(field)

    if kind in ("many", "reverse_many_to_one"):

        def many_resolver(root: Any, info: Info) -> Any:
            _check_n1(info, root, field_name, parent_type, kind="many")
            return list(getattr(root, field_name).all())
```

## What looks solid

- Generated relation resolvers preserve the shipped cardinality behavior: many-side fields materialize a list, reverse OneToOne absence collapses to `None`, and forward relations return either a related instance or an FK-id stub.
- Strictness checks reuse the shared context helper instead of duplicating dict/object context dispatch in this module.
- Consumer-authored relation fields are skipped during resolver attachment, preserving explicit Strawberry resolver overrides.
- FK-id elision is branch-sensitive through `resolver_key(parent_type, field_name, runtime_path_from_info(info))`, matching the optimizer plan identity shape.

### Summary

The resolver module is cohesive and largely follows the optimizer/type hand-off contracts. I found one low-severity private-helper contract drift around `_check_n1(kind=...)`; the broader `FieldMeta` SSoT duplication is already anchored and should be judged in the upcoming `types/` folder pass rather than fixed piecemeal here.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/types/resolvers.py`
- `tests/types/test_resolvers.py`
- `docs/review/rev-types__resolvers.md`
- `docs/review/worker-memory/worker-2.md`

### Tests added or updated

- Updated `test_check_n1_many_kind_treats_consumer_set_attribute_as_lazy` into a parameterized
  many-side contract test covering both collapsed `"many"` and real `relation_kind(field)` output
  `"reverse_many_to_one"`.

### Validation run

- `uv run pytest tests/types/test_resolvers.py -k check_n1 --no-cov` — passed:
  10 passed, 11 deselected.
- `uv run ruff format django_strawberry_framework/types/resolvers.py tests/types/test_resolvers.py` —
  passed, 2 files left unchanged.
- `uv run ruff check --fix django_strawberry_framework/types/resolvers.py tests/types/test_resolvers.py` —
  passed, all checks passed.
- Attempted `uv run ruff format` including the touched Markdown review/memory files; Ruff rejected
  Markdown formatting without preview mode, so validation was rerun against the touched Python files.

### Notes for Worker 3

- `_check_n1` now treats `_MANY_SIDE_KINDS = {"many", "reverse_many_to_one"}` as the many-side cache path.
- `_make_relation_resolver` now passes the actual `relation_kind(field)` value to `_check_n1` for
  many-side and forward resolvers instead of collapsed resolver-kind literals.
- Comment/docstring disposition: updated the `_check_n1` docstring to describe the broadened
  `relation_kind(field)` contract and many-side cache split.
- Changelog disposition: not warranted; this is a private-helper contract correction with no
  user-visible API change, and changelog edits are not authorized for this pass.

---

## Verification (Worker 3)

### Logic verification outcome

Accepted. `_check_n1` now documents that `kind` accepts the real `relation_kind(field)` output, and `_MANY_SIDE_KINDS` sends both `"many"` and `"reverse_many_to_one"` through `_will_lazy_load_many`. `_make_relation_resolver` passes the actual `relation_kind(field)` value for many-side and forward resolvers, while reverse one-to-one still passes the coherent `"reverse_one_to_one"` value. Forward and reverse-one behavior remained unchanged in the implementation and passed the full resolver test file.

### DRY findings disposition

Accepted. The fix is intentionally local: one shared `_MANY_SIDE_KINDS` constant removes the duplicated many-side predicate for this helper without expanding the existing `FieldMeta` SSoT migration, which remains a folder-pass/backlog concern.

### Temp test verification

- None used; permanent focused coverage was sufficient.

### Verification outcome

Verified. Worker 2's fix report, comment/docstring disposition, changelog disposition, and validation notes are complete. Changelog remains unchanged because this is a private-helper contract correction with no authorized release-note pass.

Validation run:

- `uv run pytest tests/types/test_resolvers.py -k check_n1 --no-cov` — passed, 10 passed / 11 deselected.
- `uv run pytest tests/types/test_resolvers.py --no-cov` — passed, 21 passed.
- `uv run ruff format --check django_strawberry_framework/types/resolvers.py tests/types/test_resolvers.py` — passed, 2 files already formatted.
- `uv run ruff check django_strawberry_framework/types/resolvers.py tests/types/test_resolvers.py` — passed.
