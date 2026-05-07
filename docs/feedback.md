# Foundation slice review — after phases 0–6

Files reviewed: the working-tree diff for `django_strawberry_framework/registry.py`, `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/converters.py`, `django_strawberry_framework/types/resolvers.py`, `django_strawberry_framework/types/__init__.py`, `django_strawberry_framework/types/definition.py` (new), `django_strawberry_framework/types/relations.py` (new), `django_strawberry_framework/types/finalizer.py` (new), `django_strawberry_framework/__init__.py`, `README.md`, `docs/spec-foundation.md`.

## Status against the spec's phased order

The phased order in `docs/spec-foundation.md` is the source of truth; this is what each numbered phase looks like in the working tree right now.

- Phase 0 — Spike gate: **done.** Spike outcome is recorded in `docs/spec-foundation.md` "Spike outcome (Phase 0 complete)" and `README.md` "Schema setup boundary". The throwaway `scripts/spikes/` directory is gone, which matches the spec's "delete only after their conclusions are captured" rule.
- Phase 1 — `DjangoTypeDefinition` + `PendingRelation`: **done.** `types/definition.py` and `types/relations.py` exist. `PendingRelation` is `frozen=True`. `DjangoTypeDefinition` mirrors the spec's slot list, including the forward-reserved Layer 3 slots and `consumer_authored_fields`.
- Phase 2 — `TypeRegistry` extensions: **done.** `register_definition`, `get_definition`, `iter_definitions`, `add_pending_relation`, `iter_pending_relations`, `discard_pending`, `is_finalized`, `mark_finalized`, and the extended `clear()` are all present. The placeholder `lazy_ref` is deleted.
- Phase 3 — `finalize_django_types()`: **done.** `types/finalizer.py` implements phase 1 (resolve), phase 2 (resolver attach), phase 3 (`strawberry.type`), idempotency check, `discard_pending` after phase 1, and the canonical unresolved-targets error message.
- Phase 4 — split `__init_subclass__` into collection only: **done.** `strawberry.type(cls, …)` and `_attach_relation_resolvers` no longer run from class creation. The post-finalization registration guard is in place. `consumer_authored_fields` detection runs from both annotations and class-dict assignments.
- Phase 5 — MRO-aware `_detect_custom_get_queryset`: **done.** The MRO walk stops at `DjangoType` and correctly handles abstract bases that override `get_queryset`. `has_custom_get_queryset()` reads from the definition first and falls back to the legacy class attribute for abstract bases.
- Phase 6 — migrate `_optimizer_field_map` / `_optimizer_hints` / `_is_default_get_queryset` to the definition: **done.** The canonical store is on the definition; class attributes are mirrored in `__init_subclass__` for the documented one-minor-version compat window.
- Phases 7–12: not started. Specifically:
  - Phase 7: `tests/fixtures/cardinality_models.py` does not exist.
  - Phase 8: existing tests have not been rewritten. The current suite hard-fails on the first test that builds a `strawberry.Schema(...)` containing `DjangoType` references because nothing calls `finalize_django_types()` between class definition and schema construction. Full picture below in **F-2**.
  - Phase 9: new acceptance test files (`tests/types/test_definition_order.py`, `tests/types/test_definition_order_schema.py`, `tests/optimizer/test_definition_order.py`) and the `tests/test_registry.py` extensions are missing.
  - Phase 10: docs other than `README.md` (i.e., `docs/README.md`, `docs/FEATURES.md`, `TODAY.md`, `CHANGELOG.md`) have not been updated.
  - Phase 11: export points are partially done (top-level `__init__.py` and `types/__init__.py` re-export `finalize_django_types` and add it to `__all__`). Counts as done early.
  - Phase 12: version metadata still says `0.0.3` in both `pyproject.toml` and `django_strawberry_framework/__init__.py`.

The early/parallel work on phases 10 (README only) and 11 (exports) is not a problem — both are pure additions and they make the manual exploratory testing the user is doing right now actually exercise the new public API.

## P1 — must fix before phase 7 begins

### P1-1. Annotation-only relation override is silently broken for many-side relations
Line references: `django_strawberry_framework/types/base.py:96-104` (consumer-authored detection), `django_strawberry_framework/types/finalizer.py:68-80` (resolver attach skip), `django_strawberry_framework/types/resolvers.py:182-188` (skip filter).
The spec carefully separates two kinds of consumer override (`docs/spec-foundation.md:67-72`):
- **Annotation override** — consumer writes `items: list["ItemType"]`. Collection should skip placeholder synthesis and pending-relation recording. The annotation flows through Strawberry. The finalizer **must still attach a relation resolver** so Strawberry's default `getattr` does not return a Django `RelatedManager` for many-side relations.
- **Field/resolver override** — consumer writes `items: list["ItemType"] = strawberry.field(resolver=custom_items)` or `@strawberry.field def items(...)`. Collection should record the field name. The finalizer **must skip resolver attachment** so the consumer's resolver is not clobbered.
The current implementation collapses both cases into one `consumer_authored_fields` set and the finalizer's phase 2 (`finalizer.py:71-75`) passes that whole set to `_attach_relation_resolvers(..., skip_field_names=...)`. Concretely, this code:
```python path=null start=null
class CategoryType(DjangoType):
    items: list["ItemType"]
    class Meta:
        model = Category
        fields = ("id", "name", "items")
```
ends up with no relation resolver on `items`. After finalization, querying `{ allCategories { items { name } } }` raises Strawberry's "Expected Iterable" error because `getattr(category, "items")` returns the Django `RelatedManager`. The annotation-only escape hatch advertised in the spec does not actually work for any many-side relation field.
Fix direction (pick one):
- Track two sets on the definition: `consumer_annotated_relation_fields` and `consumer_assigned_relation_fields`. Phase 2 should only skip fields in the assigned set; the annotated-only set still needs a resolver attached.
- Keep one `consumer_authored_fields` set, but in phase 2 skip a field only when `field.name in cls.__dict__` AND the value is a Strawberry field-ish object (e.g., `isinstance(getattr(cls, field.name, None), (StrawberryField, FunctionType, classmethod))`).
The first option is cleaner and matches the spec wording. Either way, please add an explicit acceptance test for the annotation-only many-side case (this is the path that breaks today and is not covered by any current test).

### P1-2. The existing test suite is currently broken; phase 8 is not optional
Running `uv run pytest tests --no-cov -x -q` fails at the first test that constructs a Strawberry schema referencing `DjangoType` subclasses, with `TypeError: Query fields cannot be resolved. Unexpected type '<class '…ItemType'>'`. The cause is that `__init_subclass__` no longer calls `strawberry.type(cls)` and the existing tests do not call `finalize_django_types()` between class definition and `strawberry.Schema(...)`.
This is the expected behavior of the slice and is exactly why phase 8 is in the spec, but it has two operational consequences worth flagging:
1. **CI is red right now.** Anyone running the full suite at this point cannot tell whether the slice-0–6 implementation is correct or whether they are hitting expected pre-phase-8 noise. Consider either (a) finishing phase 8 before the next push, or (b) marking phase 8 work as "in progress" in `KANBAN.md` so reviewers know to expect failures.
2. **The failure mode users will hit in their own code is identical** to what the broken tests show: an unhelpful `TypeError: Unexpected type '<class 'PendingRelationAnnotation'>'` (or, when they forget the import boundary, `Unexpected type '<class 'SomeType'>'`). The `README.md` "Schema setup boundary" section helps, but the runtime error is going to be the support-load driver. See P2-3 for a small-cost mitigation.

### P1-3. `_attach_relation_resolvers` clobbers consumer-supplied class attributes when the consumer used a `@strawberry.field` decorator with the same Python name
Line references: `django_strawberry_framework/types/resolvers.py:182-188`, `django_strawberry_framework/types/base.py:96-104`.
The current consumer-authored detection in `__init_subclass__:96-104` checks `field.name in cls.__dict__`. That works for `items: list["ItemType"] = strawberry.field(resolver=...)` because the assignment lives in `cls.__dict__`. It also works for `@strawberry.field def items(self) -> list["ItemType"]: ...` because the decorated method ends up in `cls.__dict__`. Good.
But: `_is_consumer_authored_class_attr` is a one-line check that returns `True` for *any* presence in `cls.__dict__`. It does not check whether the value looks Strawberry-shaped. That means the following also gets treated as consumer-authored:
```python path=null start=null
class CategoryType(DjangoType):
    items = None  # consumer accidentally shadowed the relation name
    class Meta:
        model = Category
        fields = ("id", "name", "items")
```
This silently disables the package's resolver for `items` and leaves `None` as the value, with no error. Tighten the detection: either (a) only treat `cls.__dict__` values that pass an `isinstance(v, (StrawberryField, FunctionType, classmethod))`-style check as overrides, or (b) require the consumer to use `strawberry.field(...)` / `@strawberry.field` explicitly and warn for any other class-attribute shape on a relation field name.
This is the same root cause as P1-1; the cleanest fix addresses both.

## P2 — should fix during phases 7–9

### P2-1. `_attach_relation_resolvers` docstring is stale
File: `django_strawberry_framework/types/resolvers.py:174-181`. The docstring still says:
> The caller (``DjangoType.__init_subclass__``) computes ``base._select_fields(meta)`` once and passes the result here so the field walk is not duplicated …
The actual caller is now `finalize_django_types()` and the input is `definition.selected_fields`. Update the docstring to point at the finalizer and mention the new `skip_field_names` parameter.

### P2-2. Duplicate registry lookup in the relation collection path
File: `django_strawberry_framework/types/base.py:389-398` and `django_strawberry_framework/types/converters.py:248-252`.
`_build_annotations` does `registry.get(field.related_model) is None` to decide whether to record a pending relation, then `convert_relation(field)` independently does another `registry.get(field.related_model)` to decide whether to return `PendingRelationAnnotation`. Both calls return the same value in the same iteration; we just walk the registry twice per relation field for no functional reason.
Cleanest fix: inline the resolved-vs-placeholder split inside `_build_annotations`:
```python path=null start=null
target_type = registry.get(field.related_model)
if target_type is None:
    pending.append(_record_pending_relation(cls, source_model, field))
    annotations[field.name] = PendingRelationAnnotation
else:
    annotations[field.name] = resolved_relation_annotation(field, target_type)
```
`convert_relation` can stay as a public helper for any external caller that wants the same dispatch logic. Minor perf, but it also removes a confusing "two functions doing the same registry check" surface from the migration story.

### P2-3. Confusing failure mode when `finalize_django_types()` is forgotten
When a consumer constructs a `strawberry.Schema(...)` before calling `finalize_django_types()`, Strawberry raises `TypeError: Unexpected type '<class 'PendingRelationAnnotation'>'`. That is technically fail-loud, but the error message gives no hint about the missing finalizer call.
Two cheap mitigations either of which would close the support-load gap from P1-2:
- Subclass `PendingRelationAnnotation` from a base whose `__repr__` says `"<unfinalized DjangoType relation; call finalize_django_types() before constructing strawberry.Schema>"`. Strawberry's `TypeError` message includes the repr.
- Add a one-line check in `DjangoOptimizerExtension.on_execute` (or in a `check_schema` warning) that asserts `registry.is_finalized()` is `True` and raises a clear "you forgot to call finalize_django_types()" error if not. The optimizer is opt-in, so this only fires when the consumer has already wired up the extension.
The first option is implementation-cheap and improves the no-extension path too.

### P2-4. `_is_default_get_queryset` is set twice in `__init_subclass__`
File: `django_strawberry_framework/types/base.py:80` and `:132`. Both lines compute and assign `cls._is_default_get_queryset = not has_custom_get_queryset` from the same value. The line-80 assignment is needed for the abstract-base early-return path; the line-132 assignment is redundant for concrete types. Either remove the line-132 mirror, or fold both into a single assignment that runs after the meta-is-None opt-out. Not a bug, just dead code.

### P2-5. `_select_fields(meta)` returns a `list[Any]` but `_attach_relation_resolvers` is typed `tuple[Any, ...]`
The collection path passes a list to `_build_annotations`; the finalizer passes `definition.selected_fields` (a tuple) to `_attach_relation_resolvers`. The types are technically compatible (both iterate as Iterable), but the type annotations on the two helpers diverge. Decide on one container shape and use it consistently — `tuple[Any, ...]` is the safer choice because `DjangoTypeDefinition.selected_fields` is the canonical store and is already tuple-shaped.

### P2-6. `convert_relation` no longer documents *what kind* of error a downstream caller will see
The new `convert_relation` docstring says "If the target type is not registered yet, return `PendingRelationAnnotation`." That is correct, but the old docstring documented the immediate `ConfigurationError` consumers would hit. Add one sentence: "Callers must record a `PendingRelation` for any field that returns `PendingRelationAnnotation`; otherwise `finalize_django_types()` will not know to rewrite the annotation and Strawberry will raise on schema construction." This avoids future contributors writing a `convert_relation`-only call site that forgets the pending record.

## P3 — small/optional, do whenever convenient

### P3-1. README's "most common production failure mode" wording does not match the spec exactly
The spec (`docs/spec-foundation.md:64`) requires the README to call this out as "the most common production failure mode in 0.0.4". The README says "The most common 0.0.4 failure mode is forgetting to import a module that contains a related type before finalization." Same idea, slightly different wording. Either is fine, but the spec wording is more specific about *what production looks like*. Optional rename.

### P3-2. `PendingRelationAnnotation` is a bare class, not a sentinel/dataclass
File: `django_strawberry_framework/types/relations.py:26-28`. It is a class with no body. That is fine functionally, but for consistency with `PendingRelation` (`@dataclass(frozen=True)`) and to make `repr` / `isinstance` checks ergonomic, consider one of:
```python path=null start=null
@dataclass(frozen=True)
class PendingRelationAnnotation:
    """Sentinel annotation rewritten before strawberry.type sees the class."""
```
or a single-instance sentinel:
```python path=null start=null
class _PendingRelationAnnotationSentinel:
    def __repr__(self) -> str:
        return "<unfinalized DjangoType relation; call finalize_django_types()>"

PendingRelationAnnotation = _PendingRelationAnnotationSentinel()
```
The second option pairs with P2-3 nicely.

### P3-3. Naming drift between spec and code: `_resolved_relation_annotation_from_pending` vs `resolved_relation_annotation`
The spec pseudocode uses `_resolved_relation_annotation_from_pending(p, target_type)`; the implementation uses `resolved_relation_annotation(pending.django_field, target_type)`. The implementation is cleaner (one helper used by both `convert_relation` and the finalizer). Either rename the helper to match the spec, or update the spec at next pass. Trivial doc/code sync.

### P3-4. `finalizer.py` imports from `.converters` directly
File: `django_strawberry_framework/types/finalizer.py:9`. `from .converters import resolved_relation_annotation` is fine, but it means `finalizer` now depends on `converters` and `resolvers` and `relations`. Not a circular import problem, but worth keeping in mind: if a future refactor introduces a `types/finalizer_helpers.py`, move `resolved_relation_annotation` there so the dependency graph stays one-way (`finalizer` → helpers; `converters` → helpers).

### P3-5. The pending list is a `list[PendingRelation]` but `discard_pending` does identity-based filtering
File: `django_strawberry_framework/registry.py:125-128`. `discard_pending` filters `_pending` by `id(pending)`. `PendingRelation` is `frozen=True` and hashable; an equality-based filter (`set(resolved)`) would be slightly more idiomatic. Identity filtering works because the finalizer hands back the *same* objects it received from `iter_pending_relations()`. Optional cleanup; the current code is correct.

## What to tackle next

In priority order:
1. **P1-1 + P1-3** in one change: split the consumer-authored signal into "annotation-only" and "field/resolver-assigned", tighten the class-dict detection to look at value shape, and add the missing acceptance test for annotation-only many-side relations. This unblocks consumers using the documented escape hatch.
2. **Phase 7** (`tests/fixtures/cardinality_models.py`) — needed to land the OneToOne/M2M acceptance tests in phase 9.
3. **Phase 8** (rewrite the four-or-so existing tests that pinned eager `convert_relation` raises). After this, CI is green again.
4. **P2-3** (better failure message) — small change, big impact on the consumer experience that phase 8 is documenting.
5. **Phase 9** (new acceptance test files), **P1-1**'s annotation-only test naturally lands here.
6. P2-1, P2-2, P2-4, P2-5, P2-6 in any order during phase 9 review.
7. **Phase 10** (docs sweep), **Phase 12** (version bump), P3 items as time allows.

## Things the slice got right

- The lifecycle split is clean: `__init_subclass__` no longer touches Strawberry, and `finalize_django_types()` is the single bottleneck.
- `_detect_custom_get_queryset` correctly walks the MRO and stops at `DjangoType`. The abstract-base inheritance case works.
- The legacy class-attribute mirror (`_optimizer_field_map`, `_optimizer_hints`, `_is_default_get_queryset`) is plain attribute assignment, not a `@property` — exactly as the spec called out.
- The post-finalization registration guard is in the right place (after the meta-is-None opt-out, before `_validate_meta`).
- The unresolved-target error message format matches the spec verbatim, so phase 9 substring assertions will pass without spec drift.
- `discard_pending` is wired in correctly so phase 9's pending-set-cleanup test will pass once the test file is added.
- `__init__.py` and `types/__init__.py` exports look correct; the public API delta in the spec matches the code.
