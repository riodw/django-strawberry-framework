# Foundation slice review — round 4 (post phases 7 / 9 / 10 / 12)

Re-reviewed against `docs/spec-foundation.md` and the prior round's `docs/feedback.md`. Test suite: **326 passed, 1 skipped, 0 failed** under `uv run pytest tests --no-cov -q`. The slice is in a release-candidate state for 0.0.4: the spec's phased order is essentially complete, with one missing release artifact (`CHANGELOG.md`) and one spec-vs-implementation drift to reconcile.

## Previous-round status

### Round 3 P1/P2/P3 items: all addressed

- **P1-1 / P1-2 / P1-3** — confirmed still passing in round 4 (tests landed in dedicated files; see Phase 9 below).
- **P2-1 through P2-6** — unchanged from round 3 confirmation.
- **P3-2 (sentinel repr via metaclass)** — pinned end-to-end now: `tests/types/test_definition_order_schema.py:77-98` (`test_manual_strawberry_type_before_finalization_surfaces_sentinel_repr`) constructs a real `strawberry.Schema(...)` and asserts the `TypeError` body contains `"Unexpected type"` and `"finalize_django_types()"`. This closes round 3's N-3.
- **P3-5 / N-5 (`discard_pending` regression)** — **fixed.** `django_strawberry_framework/registry.py:125-128` now uses `resolved_set = set(resolved)` and filters in O(N+M):
```python path=/Users/riordenweber/projects/django-strawberry-framework/django_strawberry_framework/registry.py start=125
    def discard_pending(self, resolved: Iterable[PendingRelation]) -> None:
        """Drop pending records that have been resolved successfully."""
        resolved_set = set(resolved)
        self._pending = [pending for pending in self._pending if pending not in resolved_set]
```

### Round 3 still-open items

- **P3-1 (README "most common production failure mode" wording)** — README still uses alternate phrasing ("The most common 0.0.4 failure mode is forgetting to import a module that contains a related type before finalization."). Substantively the same content; safe to close.
- **P3-3 (`_resolved_relation_annotation_from_pending` vs `resolved_relation_annotation`)** — still drift between spec wording (`docs/spec-foundation.md:354`) and the actual function name (`django_strawberry_framework/types/converters.py:212`). Trivial; spec edit only. Recommend folding into the next docs pass.
- **P3-4 (finalizer imports from converters)** — still imports `resolved_relation_annotation` from `.converters`. Forward-compat hint, not a blocker.

## Phased order: where the slice landed

### Phase 7 — cardinality fixture: done

`tests/fixtures/cardinality_models.py` ships `User`, `Profile(OneToOneField(User))`, `Author`, `Tag`, `Book(ForeignKey(Author), tags=ManyToManyField(Tag))`. Each has `app_label = "tests_cardinality"` and `managed = False`. The reverse-relation discovery requirement is met by registering `tests.fixtures.apps.TestsCardinalityConfig` in `examples/fakeshop/fakeshop/settings.py:51-52` and re-exporting the models from `tests/fixtures/models.py:3`.

This is a **deviation from the spec's `docs/spec-foundation.md:476` constraint** ("No `tests/conftest.py` and no `apps.get_app_config(...)` mutation by default … If reverse-relation discovery requires an additional Django app to be registered, prove it in a small spike before adding"). Strictly the implementation does not call `apps.get_app_config(...)` — it registers the test app via `INSTALLED_APPS` in the example project's settings, which is a different mechanism. But it has the same practical effect (the test fixture is loaded by Django's app registry whenever fakeshop is imported, including under `manage.py runserver` in production-like setups), and there is no recorded spike in the spec or in `docs/feedback.md`. See **N-2** below for the exact concern and recommendation.

### Phase 9 — new acceptance test files: done

All four files exist:

- `tests/types/test_definition_order.py` — 11 tests covering reverse-FK both orders, OneToOne forward + reverse, M2M forward + reverse, multi-cycle, unresolved-target error format, annotation-only override, assigned-field override, decorator override, class-attribute shadowing rejection, same-module string forward reference. The shadowing and the three override cases were correctly migrated out of `tests/types/test_base.py`. Good.
- `tests/types/test_definition_order_schema.py` — 3 tests: a DB-backed nested query through fakeshop, an unmanaged-M2M schema-shape introspection, and the end-to-end sentinel-repr `TypeError` test.
- `tests/optimizer/test_definition_order.py` — 5 tests: cyclic plan-relation decisions across all five cardinalities, custom `get_queryset` downgrade, `check_schema()` no-warnings, definition-vs-legacy field-map mirror, and the optimizer + annotation-only-override interaction (closes round 3's N-4).
- `tests/test_registry.py` — extended with `test_finalize_is_idempotent`, `test_registering_concrete_type_after_finalization_raises`, `test_registry_clear_allows_fresh_type_classes_to_finalize_again`, `test_phase_1_failure_is_atomic_and_retryable_after_missing_target_registers`, `test_phase_3_failure_leaves_registry_unfinalized_and_requires_fresh_classes`, `test_pending_set_is_cleaned_after_success_and_retained_after_phase_1_failure`, and `test_clear_does_not_remove_mutation_from_previously_finalized_classes`.

The spec at `docs/spec-foundation.md:506-515` lists six idempotency / isolation acceptance requirements. All six are pinned. Good coverage.

### Phase 10 — docs sweep: mostly done, CHANGELOG.md is the gap

- `docs/README.md` — updated. Quick-start uses `finalize_django_types()`; "Today" section lists the new public symbol; Status reads "0.0.4".
- `docs/FEATURES.md` — updated. Lists `finalize_django_types` in public exports, has a dedicated "Definition-order independence" subsection, lists supported relation cycles and supported forward-reference shapes, and pins the version at 0.0.4.
- `TODAY.md` — updated. Fakeshop snippet now calls `finalize_django_types()` before `strawberry.Schema(...)`.
- `README.md` — updated (already addressed in round 3): lists `finalize_django_types`, has a "Schema setup boundary" section with both correct and wrong-order examples, and the "most common 0.0.4 failure mode" framing.
- **`CHANGELOG.md` — not yet updated.** Still has only an `[Unreleased]` section with: "Consolidated completed design-doc content into the user-facing docs, added code-first onboarding, and archived the completed spec files." There is no `## [0.0.4]` release entry, no "Added: `finalize_django_types`", no mention of the foundation slice's new public API, no description of the lifecycle or import-boundary contract. See **N-1** below for the recommended diff.

`grep -rn "TODO(spec-foundation 0.0.4)"` returns zero hits in production code, source modules, and shipped docs — only this `feedback.md` file references the marker. The marker scrub is complete.

### Phase 12 — version bump: done

- `pyproject.toml:4` — `version = "0.0.4"`.
- `django_strawberry_framework/__init__.py:14` — `__version__ = "0.0.4"`.
- `tests/base/test_init.py:7` — assertion updated.
- `uv.lock` — synced.
- `KANBAN.md` — `RELEASE-002` updated to reflect the bump (`pyproject.toml version is 0.0.4`).
- `docs/review/REVIEW.md` — review-cycle examples updated to `0.0.4` / `0_0_4`.

## New observations after this round

### N-1. CHANGELOG.md is the only remaining release artifact

Below is the suggested entry. The wording mirrors `docs/FEATURES.md`'s "Definition-order independence" subsection so the changelog and the capability catalog stay aligned.

```markdown path=null start=null
## [0.0.4] - 2026-05-DD

### Added
- `finalize_django_types()` resolves pending relations, attaches generated relation
  resolvers, and finalizes each collected `DjangoType` with `strawberry.type`. Re-exported
  from both `django_strawberry_framework` and `django_strawberry_framework.types`.
- Definition-order-independent relation finalization: `DjangoType` subclasses can declare
  cyclic relations (forward FK / reverse FK / forward + reverse OneToOne / forward + reverse
  M2M, plus multi-cycle graphs) in any order. `finalize_django_types()` resolves the pending
  set after every module that defines `DjangoType` classes has been imported.
- `DjangoTypeDefinition` (stashed at `cls.__django_strawberry_definition__`) as the canonical
  per-type metadata object consumed by the optimizer and future subsystems.
- Manual relation override contract for relation fields: a consumer-supplied annotation
  on a relation field name suppresses placeholder synthesis and pending-relation recording;
  a consumer-supplied `strawberry.field(resolver=...)` / `@strawberry.field` suppresses the
  generated relation resolver. Both shapes are pinned by acceptance tests.
- Fail-loud unresolved-target finalization error that names the source model, source field,
  and target model.

### Changed
- `DjangoType.__init_subclass__` no longer calls `strawberry.type(cls)`; finalization runs
  in `finalize_django_types()`. Existing setups must call the finalizer once during
  single-threaded schema setup, after every `DjangoType` module has been imported and
  before constructing `strawberry.Schema(...)`.
- `convert_relation` no longer raises on a missing target type; instead it returns the
  `PendingRelationAnnotation` sentinel and the caller records a `PendingRelation`.
- `TypeRegistry.clear()` resets the new `_definitions`, `_pending`, and `_finalized`
  state in addition to the existing maps.
- `_optimizer_field_map`, `_optimizer_hints`, and `_is_default_get_queryset` remain on the
  class as legacy mirrors for one minor version; canonical storage is now
  `DjangoTypeDefinition.field_map` / `.optimizer_hints` / `.has_custom_get_queryset`.

### Removed
- `TypeRegistry.lazy_ref` placeholder. The pending-relation API supersedes it.
```

If you want the wording tighter, drop the second-and-third "Added" bullets and lean on the doc cross-reference. Either way the file needs the version anchor before the slice is shippable.

### N-2. `tests/fixtures/apps.py` is loaded via fakeshop's `INSTALLED_APPS`, not via a test-only mechanism

`examples/fakeshop/fakeshop/settings.py:51-52` adds `"tests.fixtures.apps.TestsCardinalityConfig"` to `INSTALLED_APPS`. Two concerns:

1. **Spec drift.** `docs/spec-foundation.md:476` says "No `tests/conftest.py` and no `apps.get_app_config(...)` mutation by default — the existing tests work without either … If reverse-relation discovery requires an additional Django app to be registered, prove it in a small spike before adding `apps.get_app_config(...)` calls." The chosen mechanism (registering via `INSTALLED_APPS`) is technically distinct from `apps.get_app_config(...)` mutation, but it has the same effect for the tests — the fixture models become discoverable by Django's app registry — and there is no spike record. The spec needs an entry under "Spike outcome (Phase 0 complete)" or a new sentence under Phase 7 that says "the cardinality fixture is registered via `INSTALLED_APPS` in the example project's settings; this was the lightest mechanism we found, and removing it breaks reverse-relation discovery on the M2M and OneToOne models."

2. **Layering.** The fakeshop example project now imports test code through Django's app registry — `tests.fixtures.apps` is a non-example, non-package module that the example's runtime now references. If a downstream consumer copies fakeshop's `settings.py` as a starting point, they inherit a phantom `tests.fixtures` app reference. This is an example-project hygiene issue rather than a slice blocker. Two cheap mitigations:
   - Move the fixture app's `INSTALLED_APPS` registration into a test-scoped settings file (`examples/fakeshop/fakeshop/settings_test.py` or a `pytest.ini` `DJANGO_SETTINGS_MODULE` override) so the example project's production-shaped settings stay clean.
   - Or, leave it but add a comment in `examples/fakeshop/fakeshop/settings.py:50-52` explaining the line is test-scoped and load-bearing for `tests/fixtures/cardinality_models.py`. This is the lower-cost option for a single-maintainer pre-1.0 package.

I would **not** block 0.0.4 on this — the tests pass and the example still runs. But the spec should acknowledge the deviation, and at minimum the `INSTALLED_APPS` line needs a comment.

### N-3. Override tests couple to Strawberry internals

`tests/types/test_definition_order.py:189-193`:

```python path=/Users/riordenweber/projects/django-strawberry-framework/tests/types/test_definition_order.py start=189
    finalize_django_types()

    items_field = _strawberry_field(CategoryType, "items")
    assert items_field.base_resolver is not None
    assert items_field.base_resolver.wrapped_func.__name__ == "resolve_items"
```

`base_resolver.wrapped_func` is a Strawberry-internal attribute path on `StrawberryField`. The same shape is used in `test_assigned_relation_field_override_keeps_consumer_resolver` (asserts `__qualname__.endswith("CategoryType.items")`) and the same-module string-forward-reference test. If Strawberry renames or wraps `base_resolver` in a minor release, three tests fail at once with an `AttributeError` rather than a useful assertion message.

Two options:
- **Cheapest**: add a comment above `_strawberry_field` documenting the Strawberry-internal coupling so a future debugger doesn't have to git-blame to understand the failure.
- **More durable**: route an in-memory query through a `strawberry.Schema(query=Query)` (the way the decorator-override test at line 226 already does) and assert side effects of resolver execution — e.g., that the consumer's resolver runs vs. the generated one. The decorator-override test is already a good template; the annotation-only and assigned-field tests can be promoted to the same shape later. Not blocking.

### N-4. `test_pending_set_is_cleaned_after_success_and_retained_after_phase_1_failure` only exercises the single-pending case

`tests/test_registry.py:339-360` declares one `ItemType` whose single pending relation (`category`) is unresolved, asserts the pending list is `["category"]`, then resolves and asserts it empties. The phase-1 atomicity contract at `docs/spec-foundation.md:512-514` is broader: with a multi-pending graph where some pendings would resolve and one would not, **none** of the resolved pendings should have their annotations rewritten before the failure raises (the loop separates the lists first; the rewrite loop runs only after the unresolved check). The current finalizer (`finalizer.py:42-57`) does this correctly, but no test pins it. A second test that declares two registered targets, one unregistered target, and three pending relations across them — and asserts that after the failure none of the source classes have their annotation rewritten yet — would close the spec coverage gap. Cheap addition; not a blocker.

### N-5. `discard_pending` correctness now hinges on `PendingRelation` hashability

The fixed implementation relies on `PendingRelation` being hashable (it is — `frozen=True` at `django_strawberry_framework/types/relations.py:13`). If a future change adds a non-hashable field (e.g., a `list[str]` of intermediate field names) to `PendingRelation` without removing `frozen=True`, the dataclass will silently become unhashable and `set(resolved)` will raise `TypeError`. Worth a one-line dataclass-level comment ("Fields must be hashable; `TypeRegistry.discard_pending` requires `set(resolved)`.") so a future contributor doesn't bisect.

### N-6. `test_consumer_annotation_overrides_synthesized` is still skipped

`tests/types/test_base.py:265-287`. The skip reason describes a Strawberry-decorator behaviour for **scalar** annotation override: `@strawberry.type` regenerates `cls.__annotations__` from its own field metadata after the framework's merge. This is **scalar override**, which `docs/spec-foundation.md:79` explicitly defers ("Manual override on scalar fields continues to follow the existing implementation-detail caveat at `base.py:151-159` and is not pinned in this slice.").

Recommendation: rename the test or its skip reason so the link to the deferred scalar-override caveat is explicit, and add a note that this is unrelated to the foundation slice's relation-override contract. Otherwise a contributor coming in cold reads "Slice 2 known issue" and assumes the foundation has an unaddressed bug.

## Recommended order from here

1. Add the `[0.0.4]` entry to `CHANGELOG.md` (N-1). Mandatory for the release.
2. Decide on the `INSTALLED_APPS` deviation (N-2): either annotate the spec + add an inline comment in `settings.py:50-52`, or move the fixture app to a test-scoped settings file. The first is the lighter touch.
3. Add the multi-pending phase-1 atomicity test (N-4). One small test in `tests/test_registry.py`.
4. Add the hashability comment on `PendingRelation` (N-5). One line in `django_strawberry_framework/types/relations.py`.
5. Optional polish: clarify the skip reason in `test_consumer_annotation_overrides_synthesized` (N-6) and decide whether to leave the Strawberry-internal coupling note (N-3) as a comment or upgrade the override tests to schema-level.
6. Optional spec sweep: address the trailing P3-3 / P3-4 items (`_resolved_relation_annotation_from_pending` rename and the finalizer→converters import boundary).

## Things this round got right

- The spec's phased order is essentially complete in implementation. Phase 0 ships, phases 1–6 ship, phase 7 ships (with the deviation noted in N-2), phase 9 ships in dedicated test files, phase 10 ships except `CHANGELOG.md`, phase 12 ships.
- `discard_pending` is correctly back to O(N+M) with a hash-set lookup.
- The end-to-end sentinel-repr test in `test_definition_order_schema.py:77-98` is the cleanest possible pin for the previously-flagged N-3 from round 3 — it constructs a real `strawberry.Schema(...)` and asserts the user-visible `TypeError` body contains `"finalize_django_types()"`.
- The optimizer + manual-override interaction is now covered by `test_annotation_only_relation_override_still_plans_prefetch` (`tests/optimizer/test_definition_order.py:146-167`), closing round 3's N-4.
- The override tests were correctly relocated from `test_base.py` to `test_definition_order.py`; `test_base.py` is now focused on Meta validation, scalar synthesis, and the relation conversion unit tests.
- Test count went 303 (round 3) → 326 (round 4), with skipped count going from 4 → 1. Three previously-deferred placeholders (the M2M skip in `test_extension.py:2167-2170`, the missing OneToOne / reverse OneToOne / M2M acceptance cases) became real tests once the cardinality fixture landed.
- `KANBAN.md`, `docs/review/REVIEW.md`, and `tests/base/test_init.py` were all kept in sync with the version bump — the kind of small-scale plumbing that's easy to forget on a single-maintainer release.
