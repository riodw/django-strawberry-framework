# Review: `django_strawberry_framework/optimizer/plans.py`

Status: verified

## DRY analysis

- Existing patterns reused: `OptimizationPlan` centralizes the plan shape that `django_strawberry_framework/optimizer/walker.py:17-24` imports for construction-time mutation and that `django_strawberry_framework/optimizer/extension.py:56-56` imports for queryset diffing, lookup introspection, and runtime-path cache keys. The file already centralizes brittle Django internals behind helpers: `_lookup_path` owns `Prefetch.prefetch_to` access in `django_strawberry_framework/optimizer/plans.py:241-248`, `_consumer_prefetch_lookups` owns `_prefetch_related_lookups` access in `django_strawberry_framework/optimizer/plans.py:251-259`, and `_flatten_select_related` owns `query.select_related` flattening in `django_strawberry_framework/optimizer/plans.py:177-207`.
- New helpers a fix might justify: a same-lookup prefetch merge helper with one responsibility: combine compatible `Prefetch` querysets for repeated planning of the same lookup path instead of dropping the later entry. It would serve `append_prefetch_unique` in `django_strawberry_framework/optimizer/plans.py:227-238` and the generated/hint prefetch call sites in `django_strawberry_framework/optimizer/walker.py:295-336`.
- Duplication risk in the current file: repeated literal access to Django private/semiprivate lookup attributes is already centralized, and the static helper only surfaced `prefetch_to` and `queryset` twice. The remaining DRY risk is behavioral rather than literal: the path-only dedupe policy in `append_prefetch_unique` repeats the same "same path means same work" assumption for generated plans and explicit hint plans even though generated fragment branches can carry different projection/nested-subtree requirements.

## High:

None.

## Medium:

### Duplicate generated prefetch paths can drop later fragment projections

`append_prefetch_unique` dedupes every prefetch by lookup path alone. That is safe for identical re-walks and explicit hint objects, but it is too lossy for generated `Prefetch` entries from separate fragment walks: two fragments can select the same relation with different child fields, and the second generated `Prefetch` is silently discarded. The surviving child queryset then carries only the first branch's `only()` projection, so the later branch's scalar fields are deferred and can lazy-load per related row. Merge compatible generated `Prefetch` entries for the same lookup path, or move the dedupe decision earlier so repeated fragment selections are combined before the child queryset is built. Add coverage for two fragment branches selecting the same many relation with different child scalar fields and assert the final child queryset includes both projected columns.

```django_strawberry_framework/optimizer/plans.py:227:238
def append_prefetch_unique(values: list[Any], prefetch: Prefetch) -> None:
    """Append ``prefetch`` unless a lookup for the same path already exists.

    Compares lookup paths via ``_lookup_path`` so a hint-supplied
    ``Prefetch(obj)`` and a walker-generated ``Prefetch`` for the same
    Django lookup are recognised as duplicates regardless of queryset
    identity.
    """
    lookup_path = _lookup_path(prefetch)
    if any(_lookup_path(value) == lookup_path for value in values):
        return
    values.append(prefetch)
```

```django_strawberry_framework/optimizer/walker.py:116:124
        if _is_fragment(sel):
            _walk_selections(
                sel.selections,
                model,
                plan,
                prefix=prefix,
                info=info,
                runtime_prefixes=runtime_prefixes,
            )
```

## Low:

### Finalized plan field types do not match the dataclass annotations

`finalize()` deliberately returns tuples for every list-shaped plan field, and tests already treat those tuples as the post-handoff invariant. The dataclass annotations still promise mutable `list[...]` fields, and several helper signatures repeat that mutable shape. This is a small but real contract drift for the optimizer's internal API: callers reading the annotations see appendable lists even though finalized/cached plans intentionally expose immutable tuples. Update the annotations to express the two-phase shape, for example with `Sequence[...]` for stored plan fields and mutable sequence/list types only on construction-time mutator helpers.

```django_strawberry_framework/optimizer/plans.py:53:70
    select_related: list[str] = field(default_factory=list)
    """Forward FK / OneToOne field names for ``QuerySet.select_related``."""

    prefetch_related: list[str | Prefetch] = field(default_factory=list)
    """Strings or ``Prefetch`` objects for ``QuerySet.prefetch_related``.

    Generated relation plans use ``Prefetch`` objects so child querysets can
    consistently carry projection and nested lookup state. Plain strings are
    still accepted for compatibility with manual plans or defensive fallback
    branches.
    """

    only_fields: list[str] = field(default_factory=list)
    """Scalar column names for ``QuerySet.only``."""
    fk_id_elisions: list[str] = field(default_factory=list)
    """Resolver keys elided because the source row already carries the target id."""
    planned_resolver_keys: list[str] = field(default_factory=list)
```

```django_strawberry_framework/optimizer/plans.py:108:115
        return replace(
            self,
            select_related=tuple(self.select_related),
            prefetch_related=tuple(self.prefetch_related),
            only_fields=tuple(self.only_fields),
            fk_id_elisions=tuple(self.fk_id_elisions),
            planned_resolver_keys=tuple(self.planned_resolver_keys),
        )
```

## What looks solid

- The static helper was run for this optimizer file: `python scripts/review_inspect.py django_strawberry_framework/optimizer/plans.py --output-dir docs/review/shadow --stdout`.
- Queryset cooperation is centralized in `diff_plan_for_queryset`, with focused subtree-aware behavior documented in `django_strawberry_framework/optimizer/plans.py:292-350` and pinned in `tests/optimizer/test_plans.py:226-411`.
- Private Django queryset state is read through small helpers instead of open-coded throughout the optimizer, which keeps future Django compatibility fixes localized.
- `OptimizationPlan.finalize` gives the plan cache a concrete immutability guard, and `diff_plan_for_queryset` derives changed plans with `dataclasses.replace` instead of mutating cached plan instances.

### Summary

`plans.py` is doing the right kind of centralization for optimizer plan shape, Django private queryset contracts, and queryset diffing. The main review finding is that the prefetch dedupe helper is too path-centric for generated fragment branches and can lose later child projections; the smaller follow-up is to make the type annotations match the finalized tuple invariant the code and tests already rely on.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/optimizer/plans.py` — changed finalized plan fields to `Sequence[...]` and construction-time mutator helpers to `MutableSequence[...]`/`Iterable[...]` so annotations match the list-to-tuple lifecycle.
- `django_strawberry_framework/optimizer/walker.py` — inlined included fragment selections before alias/relation merging, so repeated same-relation fragment branches are combined before generated child `Prefetch` querysets are built.
- `tests/optimizer/test_walker.py` — added regression coverage for two fragment branches selecting the same many relation with different child scalar fields.

### Tests added or updated

- `tests/optimizer/test_walker.py::test_plan_merges_fragment_branches_before_prefetch_queryset_creation` — pins that a single generated `Prefetch("items", queryset=...)` includes both child scalar projections (`name`, `description`) plus the connector column.

### Validation run

- `uv run ruff format .` — failed only on unrelated generated scratch files under `docs/review/new/*.stripped.py` with invalid placeholder syntax; it reformatted 2 files before failing.
- `uv run ruff check --fix .` — failed only on unrelated generated scratch files under `docs/review/new/` with invalid placeholder syntax/lint noise.
- `uv run ruff format django_strawberry_framework/optimizer/plans.py django_strawberry_framework/optimizer/walker.py tests/optimizer/test_walker.py` — passed.
- `uv run ruff check --fix django_strawberry_framework/optimizer/plans.py django_strawberry_framework/optimizer/walker.py tests/optimizer/test_walker.py` — passed.
- `uv run pytest tests/optimizer/test_walker.py::test_plan_merges_fragment_branches_before_prefetch_queryset_creation` — assertion passed, then failed the expected focused-run coverage gate.
- `uv run pytest tests/optimizer/test_walker.py::test_plan_merges_fragment_branches_before_prefetch_queryset_creation --no-cov` — passed.
- `uv run pytest tests/optimizer/test_walker.py --no-cov` — passed, 65 tests.
- `uv run pytest tests/optimizer/test_plans.py --no-cov` — passed, 45 tests.

### Notes for Worker 3

- Read the existing shadow overview at `docs/review/shadow/django_strawberry_framework__optimizer__plans.overview.md`; no shadow files were edited.
- Medium finding was fixed by combining repeated included fragment selections before child queryset creation, not by merging `Prefetch` querysets. This keeps explicit hint `Prefetch` semantics unchanged because `append_prefetch_unique` still dedupes hint objects by first-seen lookup path.
- Low finding was fixed by widening stored plan annotations/signatures to immutable-compatible sequence types while keeping construction-time helper parameters mutable.

---

## Verification (Worker 3)

### Logic verification outcome

- High: none.
- Medium addressed: Worker 2 fixed the duplicate generated prefetch projection loss by inlining included fragment selections before `_merge_aliased_selections` runs in `django_strawberry_framework/optimizer/walker.py`. That combines repeated same-relation fragment branches before `_plan_prefetch_relation` builds the child queryset, so the final `Prefetch("items", queryset=...)` carries both fragment scalar projections. Directive filtering is preserved because `_included_field_selections` applies `_should_include` to both fragment nodes and nested field nodes before merge. Alias behavior is preserved because the existing `_merge_aliased_selections` response-key accumulation still runs after inlining.
- Low addressed: Worker 2 changed stored `OptimizationPlan` fields and diff helper inputs to immutable-compatible `Sequence[...]` while keeping construction-time mutator helpers on `MutableSequence[...]`/`Iterable[...]`, matching the list-to-tuple lifecycle.

### DRY findings disposition

- The Medium fix resolves the behavioral DRY issue by moving duplicate generated relation handling to the shared selection-normalization path instead of adding another prefetch-queryset merge path.
- Existing centralized helpers in `plans.py` remain unchanged for explicit hint `Prefetch` dedupe and queryset diffing, so this pass does not duplicate Django private-state handling.

### Temp test verification

- Temp test files used: none.
- Disposition: permanent regression coverage exists in `tests/optimizer/test_walker.py::test_plan_merges_fragment_branches_before_prefetch_queryset_creation`.

### Verification outcome

`logic accepted; awaiting comment pass`.

Validation run by Worker 3:

- `uv run pytest tests/optimizer/test_walker.py::test_plan_merges_fragment_branches_before_prefetch_queryset_creation --no-cov` — passed.
- `uv run ruff format --check django_strawberry_framework/optimizer/plans.py django_strawberry_framework/optimizer/walker.py tests/optimizer/test_walker.py` — passed.
- `uv run ruff check django_strawberry_framework/optimizer/plans.py django_strawberry_framework/optimizer/walker.py tests/optimizer/test_walker.py` — passed.
- `uv run pytest tests/optimizer/test_walker.py tests/optimizer/test_plans.py --no-cov` — passed, 110 tests.

Top-level `Status:` remains `fix-implemented`; the `plans.py` checklist item remains unchecked until comment/docstring review and changelog disposition are recorded.

---

## Comment/docstring pass

### Files touched

- `django_strawberry_framework/optimizer/plans.py` — updated module/class docstrings and `append_prefetch_unique` wording to describe the construction-time mutable sequence to finalized tuple lifecycle and the final first-seen `Prefetch` dedupe behavior after fragment branches have already been merged.
- `django_strawberry_framework/optimizer/walker.py` — updated selection-normalization docstrings to state that included fragments are flattened before alias/relation merging, so duplicate relation branches combine before child `Prefetch` querysets are built.

### Tests added or updated

- None. Comment/docstring-only pass; no behavior changed.

### Validation run

- `uv run ruff format django_strawberry_framework/optimizer/plans.py django_strawberry_framework/optimizer/walker.py` — passed, 2 files unchanged.
- `uv run ruff check django_strawberry_framework/optimizer/plans.py django_strawberry_framework/optimizer/walker.py` — passed.

### Notes for Worker 3

- Top-level `Status:` remains `fix-implemented`.
- Checklist item remains unchecked.
- `CHANGELOG.md` was not edited; changelog disposition is not reached until Worker 3 accepts this comment/docstring pass.

---

## Changelog disposition

- Changelog edit: warranted as a maintainer release-note candidate because this cycle fixes generated optimizer plans for duplicate fragment relation branches, preventing lost child projections and avoiding related-row lazy loads.
- What was done: no `CHANGELOG.md` edit was made. `AGENTS.md` forbids changelog edits unless explicitly instructed, and the active review plan does not authorize Worker 2 to edit `CHANGELOG.md` for this cycle item.
- Disposition: defer the release-note wording to the maintainer or a separately authorized changelog pass. Top-level `Status:` remains `fix-implemented` for Worker 3 final verification.

---

## Iteration log

Each Worker 2 re-pass appends a `## Fix report (Worker 2, pass <N>)` section here. Each Worker 3 re-verification appends a `## Verification (Worker 3, pass <N>)` section here. Do not edit prior entries; append.

## Verification (Worker 3, pass 2)

### Comment/docstring verification outcome

`comments accepted; awaiting changelog disposition`.

Worker 2's comment/docstring pass now describes the final behavior:

- `django_strawberry_framework/optimizer/plans.py` documents the construction-time mutable sequence fields and the finalized tuple-backed handoff/cache invariant.
- `django_strawberry_framework/optimizer/plans.py` documents that `append_prefetch_unique` remains a first-seen path dedupe helper after generated duplicate selections have already been merged.
- `django_strawberry_framework/optimizer/walker.py` documents that included fragment bodies are flattened before alias/relation merging, so duplicate relation branches combine before generated child `Prefetch` querysets are built.

### Changelog disposition check

Changelog disposition is still missing. The `## Changelog disposition` section still contains the workflow template text rather than a Worker 2 decision that a changelog edit was warranted or intentionally not warranted.

### Verification outcome

Top-level `Status:` remains `fix-implemented`; the `plans.py` checklist item remains unchecked until Worker 2 records the changelog disposition and Worker 3 performs final verification.

Validation run by Worker 3:

- `uv run ruff format --check django_strawberry_framework/optimizer/plans.py django_strawberry_framework/optimizer/walker.py` — passed.
- `uv run ruff check django_strawberry_framework/optimizer/plans.py django_strawberry_framework/optimizer/walker.py` — passed.

## Verification (Worker 3, pass 3)

### Final verification outcome

`cycle accepted; verified`.

Logic remains accepted: the Medium fragment-branch projection loss is addressed by flattening included fragment selections before alias/relation merging, and the Low plan-field typing drift is addressed with `Sequence[...]` stored fields plus mutable construction-time helper parameters.

DRY remains accepted: duplicate generated relation handling is centralized in the walker selection-normalization path, without adding a parallel `Prefetch` merge path or duplicating Django private-state helpers in `plans.py`.

Comments/docstrings remain accepted: `plans.py` documents the mutable-to-finalized tuple lifecycle and first-seen `Prefetch` dedupe semantics after generated duplicate selections have been merged; `walker.py` documents fragment flattening before relation merge and child queryset creation.

Changelog disposition accepted: Worker 2 recorded that a changelog note is warranted as a maintainer release-note candidate, but did not edit `CHANGELOG.md` because `AGENTS.md` forbids changelog edits without explicit instruction.

### Validation run

- `uv run pytest tests/optimizer/test_walker.py::test_plan_merges_fragment_branches_before_prefetch_queryset_creation --no-cov` — passed.
- `uv run ruff format --check django_strawberry_framework/optimizer/plans.py django_strawberry_framework/optimizer/walker.py tests/optimizer/test_walker.py` — passed.
- `uv run ruff check django_strawberry_framework/optimizer/plans.py django_strawberry_framework/optimizer/walker.py tests/optimizer/test_walker.py` — passed.
- `uv run pytest tests/optimizer/test_walker.py tests/optimizer/test_plans.py --no-cov` — passed, 110 tests.
