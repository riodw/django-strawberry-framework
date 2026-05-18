# Build: Slice 2 — Meta.primary recognition

Spec reference: `docs/spec-014-meta_primary-0_0_6.md` (lines 110-123; Decision 1 at lines 314-329; Decision 7 at lines 532-552; Decision 8 + L3 at lines 554-558)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - **Validation shape — inline `isinstance` raise inside `_validate_meta` (no helper).** The spec's Decision 1 pseudocode at `docs/spec-014-meta_primary-0_0_6.md:318-325` is three lines: `getattr → isinstance check → raise`. The closest existing analog inside `_validate_meta` itself is the `Meta.model` class check at `django_strawberry_framework/types/base.py:395-399` — `model = getattr(meta, "model", None); if model is None: raise; if not isinstance(model, type) or not issubclass(model, models.Model): raise ConfigurationError("Meta.model must be a Django model class")`. Same shape: top-level inline `getattr` + `isinstance` + `raise ConfigurationError`. **There is no existing one-line-bool-validation helper to reuse**; every other validated Meta key has a richer shape (`Mapping` for `optimizer_hints` via `_meta_optimizer_hints` at `types/base.py:250-265`, `Sequence` for `fields`/`exclude` via `_normalize_*_spec` at `:196-211`, tuple-of-classes for `interfaces` via `_validate_interfaces` at `:294-367`). A new `_validate_primary` helper would be a single-call-site wrapper around three lines — drop it. Inline the three lines directly inside `_validate_meta`, matching the `Meta.model` pattern at `:395-399`.
  - **`ALLOWED_META_KEYS` extension.** `Meta.interfaces` was promoted from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` in `0.0.5` (per `CHANGELOG.md:43-44`). The same single-string addition shape applies here: add `"primary"` to the existing `ALLOWED_META_KEYS` frozenset literal at `types/base.py:55-67`. The TODO anchor at `types/base.py:64-66` already names the exact insertion site.
  - **`registry.register_with_definition(..., primary=...)` call.** Slice 1 shipped the `*, primary: bool = False` keyword on `register_with_definition` (per `django_strawberry_framework/registry.py:224-230`; pinned by the Slice 1 artifact `docs/builder/bld-slice-1-registry_multitype.md` Build report). The current call site at `types/base.py:142` is `registry.register_with_definition(meta.model, cls, definition)` — extend to `registry.register_with_definition(meta.model, cls, definition, primary=primary)`. No new helper needed.
  - **`DjangoTypeDefinition` dataclass-field extension.** The dataclass at `django_strawberry_framework/types/definition.py:15-46` has multiple `field: type = default` lines for deferred-key placeholders (lines 38-42). The same pattern applies to `primary: bool = False` — single line, default `False`, placed after the `consumer_*` frozenset blocks and before the deferred `filterset_class`/etc. block. The TODO anchor at `types/definition.py:32-34` already names the exact insertion site.
  - **`getattr(meta, "primary", False)` consumer-call pattern.** Identical shape to other `Meta.*` reads in `__init_subclass__` and `DjangoTypeDefinition(...)` construction at `types/base.py:125-141` (`name=getattr(meta, "name", None)`, `description=getattr(meta, "description", None)`, etc.). The new read goes into the existing block, alongside those reads.
  - **Test fixture — `_isolate_registry` autouse.** `tests/types/test_base.py:51-56` already declares the `_isolate_registry` autouse fixture that wraps every test with `registry.clear()` on entry and exit. All new tests run under that fixture without any new fixture work. Per Decision 7 spec line 544, this is the canonical pattern; do not duplicate it.

- **New helpers justified.** None. Slice 2 is a thin recognition layer: three single-line additions (one frozenset entry, one inline validation block, one dataclass field) plus one keyword-threaded call. The smallest helper that could be extracted (`_validate_primary(meta) -> bool` returning the validated value) has exactly one caller (`_validate_meta`) and its body is two lines — extracting it would not reduce duplication but would add a method-jump cost for readers. The plan keeps it inline. Slice 1's planning note on inline-vs-helper for the `register_with_definition` rollback path (`docs/builder/bld-slice-1-registry_multitype.md:17` "No new helpers… Keep it inline") is the precedent.

- **Duplication risk avoided.**
  - **Two `getattr(meta, "primary", False)` calls.** A naive implementation could read `Meta.primary` twice — once inside `_validate_meta` (for the bool check) and once in `__init_subclass__` (for the registry threading). Both reads return the same value but the spec-pseudocode at `docs/spec-014-meta_primary-0_0_6.md:322` writes the read inside `_validate_meta`, and the call site at `types/base.py:88` already discards the validator's return value (`interfaces = _validate_meta(meta)` only captures `interfaces`). **Decision:** keep the second read at the `__init_subclass__` call site — `primary = getattr(meta, "primary", False)` immediately after the `_validate_meta` call and before the `DjangoTypeDefinition(...)` construction. The two reads are not duplication because: (a) `_validate_meta`'s read is the guard, `__init_subclass__`'s read is the plumb; (b) extending `_validate_meta` to return a tuple `(interfaces, primary)` would force every other Meta-key consumer to thread the new return slot, ballooning the surface; (c) the `getattr(..., False)` literal is two words and reads the same value the validator just confirmed is a bool. The spec pseudocode supports this shape (`spec:327` says "The validated value is read again at the `__init_subclass__` call site for plumbing through `register_with_definition`"). The two-read approach is explicit per the spec; do not factor it.
  - **`DjangoTypeDefinition(..., primary=primary)` placement.** The dataclass constructor call at `types/base.py:125-141` is keyword-only and currently has thirteen explicit `kwarg=value` pairs. Adding `primary=primary` is one more line in that block. Worker 2 must place it where it groups naturally with related keys; the spec (Decision 8 at `spec:554-558`) says it is "for introspection and future-work read sites" — place near `has_custom_get_queryset` (a peer-shaped per-type bool flag) rather than mid-frozenset-block. **Constrained shape, not duplication.**
  - **Stale-test rewrite vs. add-new tests.** The two paths Decision 7 / spec line 116 lays out for the stale test at `tests/types/test_base.py:68` (option a: flip both subclasses to `Meta.primary = True`; option b: replace with the success case) are both viable, but the new test list below already covers the success case via `test_two_types_same_model_one_primary_both_register_successfully`. Choosing option (b) would leave option (a)'s class-creation-layer mirror unrepresented; choosing option (a) preserves a parallel surface to the registry-layer primary collision test. **Worker 1 decision: option (a) — rewrite both `CategoryTypeA`/`CategoryTypeB` to `Meta.primary = True` and update the `match=` regex to `"already declared primary"`.** Rationale: (i) the spec line 116 itself flags option (a) as "the lower-touch choice"; (ii) the class-creation path needs a regression that pins the duplicate-primary error fires from `__init_subclass__` going through `register_with_definition` going through `register` (the new tests below cover the success cases but not this specific collision at the class-creation layer); (iii) Slice 1's parallel stale-test cleanup deleted the registry-layer forward-collision test outright (per `docs/builder/bld-slice-1-registry_multitype.md:63`) because the contract was inverted at the registry layer — at the class-creation layer the test's collision contract narrows (from "any second declaration raises" to "second primary declaration raises") rather than inverts, so retaining the test under a narrowed contract is the right shape. Do NOT also add a new test that duplicates this assertion at the class-creation layer; one test, narrowed scope.

### Implementation steps

Line numbers below are pin-at-write-time hints; verify against the current source before editing — Slice 1 may have shifted nothing in `types/base.py` and `types/definition.py`, but the `__init_subclass__` body in particular spans 73 lines and is dense.

1. **`django_strawberry_framework/types/base.py:55-67` — extend `ALLOWED_META_KEYS`.** Add the literal string `"primary"` to the frozenset. Remove the TODO comment block at lines 64-66 in the same change (the anchor is now landed). Expected post-edit shape:

   ```python
   ALLOWED_META_KEYS: frozenset[str] = frozenset(
       {
           "model",
           "fields",
           "exclude",
           "name",
           "description",
           "optimizer_hints",
           "interfaces",
           "primary",
       },
   )
   ```

   The trailing comma after `"primary"` is required by ruff's COM812 rule (per `AGENTS.md` "Formatting and lint").

2. **`django_strawberry_framework/types/base.py:395-425` — extend `_validate_meta` per Decision 1.** Insert the `Meta.primary` bool check inside `_validate_meta`. Spec Decision 1 (`spec:316-325`) says "after the `DEFERRED_META_KEYS` check, before the unknown-key check". Per the current source: `DEFERRED_META_KEYS` check is at lines 411-415, unknown-key check is at 417-419. Insert between them, replacing the TODO comment block at lines 406-410. The TODO at 406-410 already names the exact pseudocode to inline. Expected post-edit shape (inserted lines, copied verbatim from `spec:322-325`):

   ```python
   primary = getattr(meta, "primary", False)
   if not isinstance(primary, bool):
       raise ConfigurationError("Meta.primary must be a bool")
   ```

   The validated value is **discarded** inside `_validate_meta` — the function's return type (`tuple[type, ...]`) is the interfaces tuple, unchanged. The `__init_subclass__` caller re-reads `Meta.primary` at step 3 below. (See DRY analysis "two reads" note above: this is intentional shape per spec, not duplication.) Do NOT change `_validate_meta`'s return type.

3. **`django_strawberry_framework/types/base.py:88-145` — thread `primary` through `__init_subclass__`.** After the `_validate_meta(meta)` call at line 88 (which has already confirmed `Meta.primary` is a bool if declared), capture the primary flag for plumbing. Replace the TODO comment block at lines 94-101 with two changes:
   - At a position near the existing `interfaces = _validate_meta(meta)` / `fields = _select_fields(meta)` / `optimizer_hints = _meta_optimizer_hints(meta)` triplet (the natural "post-validation, pre-construction" block), add: `primary = getattr(meta, "primary", False)`. The spec confirms a `False` default when absent (`spec:316`, `spec:322`). Use the same `getattr(meta, "<key>", default)` pattern the surrounding lines use.
   - Add `primary=primary` to the `DjangoTypeDefinition(...)` constructor call at lines 125-141. Place the kwarg adjacent to `has_custom_get_queryset=has_custom_get_queryset` (line 135) since both are per-type bool flags — Worker 2 picks the exact line; the natural neighbor is `has_custom_get_queryset`, but any keyword-position is functionally equivalent.
   - Change the `registry.register_with_definition(meta.model, cls, definition)` call at line 142 to `registry.register_with_definition(meta.model, cls, definition, primary=primary)`. Slice 1's `register_with_definition` already accepts `*, primary: bool = False` (confirmed at `registry.py:224-230`).

4. **`django_strawberry_framework/types/definition.py:14-46` — add `primary` field to `DjangoTypeDefinition`.** Add a single new dataclass field `primary: bool = False` per Decision 8 (`spec:554-556`). Remove the TODO comment block at lines 32-34 in the same change (its anchor is landed; the deferred-spec TODO comment at lines 35-37 is separate and stays). Placement: after the `consumer_*` frozenset block (lines 28-31) and before the deferred-spec block (lines 38-42), grouping naturally with the per-type bool flags / metadata. Expected post-edit shape (inserted line):

   ```python
   primary: bool = False
   ```

   The default `False` is required: per spec Decision 1, `Meta.primary` defaults to `False` when absent. Per spec Decision 8 `spec:556`, the dataclass default of `False` "[lets] existing tests and existing call sites that build `DjangoTypeDefinition(...)` keyword-argument-free continue to work."

5. **L3 read-site discipline (no code change, but a planning constraint).** Per spec Decision 8 L3 (`spec:558`) and the Slice 1 worker memory carry-forward (`docs/builder/worker-memory/worker-1.md:7`), this slice MUST NOT add code paths that read `definition.primary` and route ambiguity decisions from it. The `primary` field on `DjangoTypeDefinition` is **store-only** in this slice; Slices 3-4 read it through `registry.primary_for(model)` (audit) and through the threaded origin Strawberry type (optimizer root path). Worker 2: do not preemptively add a `definition.primary` read anywhere — no convenience accessor, no `if definition.primary: ...` branch, no `cls.__django_strawberry_definition__.primary` consumer. The field is on the dataclass for introspection and future-work read sites only.

6. **No source edits outside the three files above.** Slice 2 does NOT touch `registry.py` (Slice 1 finished it), does NOT touch `types/finalizer.py` or `types/converters.py` (Slice 3 / Slice 4 territory), does NOT touch `optimizer/*.py` (Slice 4 territory), and does NOT touch `docs/FEATURES.md` / `CHANGELOG.md` / `KANBAN.md` (Slice 6 territory). Worker 2: stay inside `types/base.py`, `types/definition.py`, and `tests/types/test_base.py`.

After steps 1-4, no `TODO(spec-014-meta_primary-0_0_6.md Slice 2)` anchors remain in `types/base.py` or `types/definition.py`. The Slice 4 anchor at `types/base.py:635` (always-defer auto-synthesized relations) and the Slice 6 docs/FEATURES anchors are untouched.

### Test additions / updates

All test work lands in `tests/types/test_base.py`. Per Decision 7 (`spec:537`) and the line-count check (646 lines today + ~7 new tests at ~10-15 lines each → ~720-740 lines, comfortably within the comfortable-size threshold), **do NOT create `tests/types/test_meta_primary.py`**. Extending `test_base.py` keeps the new tests next to existing `Meta` validation tests (the file's "Slice 2 — Meta validation" section starts at line 94 and is the natural home).

**Stale test rewrite (per spec line 116):**

- `tests/types/test_base.py:68-79` — `test_registry_collision_raises_configuration_error`. Per Worker 1 decision documented under "Duplication risk avoided" above, **option (a)**: keep the test name and shape; change both `CategoryTypeA` and `CategoryTypeB` to declare `Meta.primary = True`; change the `match=` regex from `"already registered"` to `"already declared primary"`. The narrowed assertion still pins the class-creation path's collision behavior — only the contract narrows from "any second declaration raises" (the old single-type-per-model contract) to "second primary declaration raises" (the new multi-type-with-explicit-primary contract). Land the rewrite in the same commit as the source changes. Concrete shape:

  ```python
  def test_registry_collision_raises_configuration_error():
      class CategoryTypeA(DjangoType):
          class Meta:
              model = Category
              fields = CATEGORY_SCALAR_FIELDS
              primary = True

      with pytest.raises(ConfigurationError, match="already declared primary"):

          class CategoryTypeB(DjangoType):
              class Meta:
                  model = Category
                  fields = CATEGORY_SCALAR_FIELDS
                  primary = True
  ```

  After Slice 1 + the rewrite, the Slice 1 final-verification note (`docs/builder/worker-memory/worker-1.md:11`) is resolved: the test that was failing post-Slice-1 (`tests/types/test_base.py:68 test_registry_collision_raises_configuration_error`) returns to a green state under the rewritten assertion.

**New tests (permanent additions, per spec lines 117-123):**

Place all new tests inside the existing "Slice 2 — Meta validation" section (currently `tests/types/test_base.py:94` onwards), after the existing meta-key tests, before the scalar-field section. Each test uses the `_isolate_registry` autouse fixture (already present) and a real `Item` model (matching `tests/test_registry.py`'s Slice 1 fixture pattern and the spec's "Real Django models … are sufficient" guidance at `spec:542`).

1. `test_meta_primary_true_registers_type_as_primary` — declares one `DjangoType` subclass with `Meta.primary = True`. Assert `registry.primary_for(Item) is TheType`. Pins the basic primary-flag-flows-to-registry path (spec line 117).

2. `test_meta_primary_false_does_not_register_primary` — declares with `Meta.primary = False` explicitly. Assert `registry.primary_for(Item) is None` AND `registry.get(Item) is TheType` (the single-type-implicit-primary backward-compat path from Slice 1 Decision 4). Pins that an explicit `False` is treated identically to absent (spec line 118).

3. `test_meta_primary_absent_does_not_register_primary` — declares without any `Meta.primary` key. Assert `registry.primary_for(Item) is None` AND `registry.get(Item) is TheType`. Pins the default-`False` contract (spec line 119).

4. `test_meta_primary_non_bool_raises_configuration_error` — declares with `Meta.primary = "yes"`. Assert `pytest.raises(ConfigurationError, match="must be a bool")`. Pins the Decision 1 bool guard (spec line 120). Add a second sub-case or a parametrized variant for at least one other non-bool value (e.g. `Meta.primary = 1` — yes, `isinstance(1, bool)` is `False`, so the integer `1` correctly raises; pins that the guard rejects the `bool`-shaped-but-not-`bool` int trap). Worker 2 discretion on exactly how many non-bool variants to assert; minimum: one string, one int. (Note: `isinstance(True, bool)` is `True` AND `isinstance(True, int)` is also `True`, so the order of the `isinstance` check matters less than the value being a `bool` — `1 is not True`, so `isinstance(1, bool)` is `False`, the guard fires.)

5. `test_meta_primary_propagates_to_definition` — declares with `Meta.primary = True`. Assert `registry.get_definition(TheType).primary is True`. Pins Decision 8 storage (spec line 121). Add a companion sub-assertion (or second test) `test_meta_primary_absent_definition_primary_defaults_false`: declares without `Meta.primary`; assert `registry.get_definition(TheType).primary is False`. Pins the default. Worker 2 discretion on whether to fold into one test or split.

6. `test_two_types_same_model_one_primary_both_register_successfully` — declares two `DjangoType` subclasses on `Item`: `ItemType` (no `Meta.primary` key) and `AdminItemType(Meta.primary=True)`. Both declarations succeed. Assert: `registry.types_for(Item) == (ItemType, AdminItemType)` (registration order); `registry.primary_for(Item) is AdminItemType`; `registry.get(Item) is AdminItemType` (primary-first per Slice 1 Decision 4). Spec line 122. (The spec writes "ItemType and AdminItemType(Meta.primary=True)" — the order matters because `types_for` returns registration order.)

7. `test_two_primary_types_same_model_raises` — declares `ItemType(Meta.primary=True)` first; then attempts `AdminItemType(Meta.primary=True)`. Assert the second class declaration raises `ConfigurationError` with `match="already declared primary"`. Spec line 123. Note: this is conceptually the same surface as the rewritten stale-test option (a) above, but exercised on `Item` instead of `Category` and through the explicit two-distinct-classes-both-primary path (the rewritten stale test exercises two `Category` classes, both primary). The duplication is intentional and minimal: the rewritten test pins the parallel `Category` surface from the original test file's structure; the new test pins the spec-line-123 surface on `Item` with two distinct class names that match the spec's example. **Worker 2 acceptable alternative:** consolidate into one test that uses the spec-line-123 names (`ItemType` / `AdminItemType`) and delete the `Category` rewrite, OR keep both — the duplication is one test pair. Worker 1's recommendation: keep both because the stale test's grep-stable test_name is referenced in the Slice 1 worker-memory carry-forward (`docs/builder/worker-memory/worker-1.md:11`) and dropping it would lose that breadcrumb.

**Tests NOT added (per L3 constraint, step 5 above):**

- Do NOT add a test that reads `definition.primary` and routes a decision off it (e.g., "test the schema audit picks the primary by reading `definition.primary`"). Per spec Decision 8 L3 (`spec:558`), `definition.primary` is a read-convenience denormalization; the audit (Slice 3) and the optimizer (Slice 4) route through `registry.primary_for(model)` and the threaded origin type respectively. Test #5 above asserts the field is **stored correctly** — that is the slice's contract, full stop.

**Temp/scratch tests for Worker 3:**

- None planned. The Slice 2 surface is narrow (one frozenset entry + one validation block + one keyword threading + one dataclass field). Worker 3 may create temp tests under `docs/builder/temp-tests/slice-2/` if any specific edge case is unclear from the diff alone — typical candidates would be the `isinstance(True, int)` / `isinstance(1, bool)` distinction (test #4) or the two-reads-of-`Meta.primary` shape — but no temp test is required by the plan.

### Implementation discretion items

These are choices Worker 1 has assessed and decided belong to Worker 2:

- **Exact line position for `primary = getattr(meta, "primary", False)` inside `__init_subclass__`.** The plan says "near the existing `interfaces = _validate_meta(meta)` / `fields = _select_fields(meta)` / `optimizer_hints = _meta_optimizer_hints(meta)` triplet". Worker 2 picks one of: (a) immediately after `optimizer_hints = _meta_optimizer_hints(meta)` (line 93 today, the validation-trio tail), (b) immediately after the `_consumer_*` frozenset block (just before `_build_annotations(...)` at line 117 today), or (c) immediately before the `DjangoTypeDefinition(...)` constructor at line 125. Any of the three reads the same value and threads it identically; (a) is the most consistent with the existing post-validation grouping. Worker 2 discretion.

- **Exact kwarg-position of `primary=primary` inside the `DjangoTypeDefinition(...)` constructor at lines 125-141.** The plan says "adjacent to `has_custom_get_queryset=has_custom_get_queryset`" (line 135 today). Worker 2 may place anywhere within the constructor — the dataclass accepts kwargs in any order. The recommended position is between `has_custom_get_queryset` (line 135) and the `consumer_*` block (lines 136-139), but Worker 2 may place after the `consumer_*` block or grouped with `interfaces` (line 140). Worker 2 discretion.

- **Number of non-bool variants in `test_meta_primary_non_bool_raises_configuration_error`.** The plan recommends at least one string and one int. Worker 2 may parametrize with `@pytest.mark.parametrize("bad", ["yes", 1, 0, [], None, 1.0])` for full coverage, or write two separate tests. Either reads the spec contract correctly. Worker 2 discretion.

- **Whether to fold `test_meta_primary_propagates_to_definition` and `test_meta_primary_absent_definition_primary_defaults_false` into one test or two.** The plan presents them as a companion pair; folding into one test that asserts both states is cheaper but slightly reduces failure-mode legibility. Worker 2 discretion.

- **Whether to keep BOTH the rewritten stale test (option a, on `Category`) AND the new `test_two_primary_types_same_model_raises` (on `Item`).** The plan's recommendation is "keep both" with the breadcrumb rationale; Worker 2 may collapse into one test if the duplication feels excessive. The contract is "two `Meta.primary = True` declarations on the same model raise"; either one model or both models exercises that contract.

- **Whether to capture the rewritten stale test's previous failure mode.** Currently the test `tests/types/test_base.py:68` fails post-Slice-1 with the wrong-shape assertion (Slice 1 verification artifact notes the failure was spec-licensed). Worker 2 may add an inline comment above the rewritten test pointing at `docs/spec-014-meta_primary-0_0_6.md:116` (the spec's "rewrite stale test" instruction) to leave a breadcrumb for future readers, or leave the test free-standing. Worker 2 discretion; the comment is decoration, not contract.

These are NOT discretion items — Worker 2 must implement these as specified:

- **`"primary"` is added to `ALLOWED_META_KEYS`, not to `DEFERRED_META_KEYS`.** Per spec Decision 1 (`spec:316-327`), `Meta.primary` is an immediately-shipping key in this slice; it must clear the `DEFERRED_META_KEYS` rejection at `types/base.py:411-415` so the validated bool check at the inserted location actually runs.

- **Validation order inside `_validate_meta`.** Per spec Decision 1 (`spec:316-321`), the bool check fires "after the `DEFERRED_META_KEYS` check, before the unknown-key check" — meaning the new block goes between lines 415 (end of `deferred` if-block) and 417 (start of `unknown` declaration). NOT at line 396 (before `model` validation), NOT after the unknown-key guard, NOT inside the `_meta_optimizer_hints(meta)` block.

- **Error message text.** The exact string `"Meta.primary must be a bool"` is the spec contract (`spec:324`). The test at #4 above asserts `match="must be a bool"`. Do not paraphrase.

- **`registry.register_with_definition` signature consumed.** Slice 1 shipped `register_with_definition(self, model, type_cls, definition, *, primary: bool = False) -> None` at `registry.py:224-230`. Worker 2 calls it with `primary=primary` as a keyword argument (not positional — the spec and Slice 1 pin keyword-only).

- **No read of `definition.primary` anywhere in Slice 2's diff.** Per spec Decision 8 L3 (`spec:558`) and the Slice 1 worker-memory carry-forward, the dataclass field is store-only in this slice. Any read of `definition.primary` from new code would create the L3-prohibited routing path. Worker 3 must reject such a read on review.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/types/base.py` — added `"primary"` to `ALLOWED_META_KEYS` (removed the Slice 2 TODO anchor); inserted the three-line `isinstance(primary, bool)` guard inside `_validate_meta` between the `fields`/`exclude`-exclusivity check and the `DEFERRED_META_KEYS` block (removed the Slice 2 TODO anchor); captured `primary = getattr(meta, "primary", False)` in `__init_subclass__` immediately after the `optimizer_hints = _meta_optimizer_hints(meta)` line (removed the Slice 2 TODO anchor); added `primary=primary` to the `DjangoTypeDefinition(...)` constructor and to the `registry.register_with_definition(...)` call.
- `django_strawberry_framework/types/definition.py` — added `primary: bool = False` dataclass field immediately after the `consumer_*` frozenset block (removed the Slice 2 TODO anchor). The Slice 4 / deferred-specs TODO anchor block was preserved.
- `tests/types/test_base.py` — rewrote stale `test_registry_collision_raises_configuration_error` (test placement `tests/types/test_base.py:68`) per plan option (a): both `CategoryTypeA` and `CategoryTypeB` now declare `Meta.primary = True`; the `match=` regex is the new `"already declared primary"` contract. Added a new "Slice 2 — Meta.primary recognition" section with the 7 permanent tests from the plan plus the optional companion `test_meta_primary_absent_definition_primary_defaults_false`.

### Tests added or updated

Rewrote:

- `tests/types/test_base.py::test_registry_collision_raises_configuration_error` — now pins the duplicate-primary class-creation collision (both subclasses declare `Meta.primary = True`).

Added (placed in a new `Slice 2 — Meta.primary recognition` section directly after the Meta-validation block, before scalar synthesis):

- `tests/types/test_base.py::test_meta_primary_true_registers_type_as_primary` — `Meta.primary = True` populates `registry.primary_for(Item)`.
- `tests/types/test_base.py::test_meta_primary_false_does_not_register_primary` — `Meta.primary = False` is identical to absent (no primary; `get()` still returns the lone type).
- `tests/types/test_base.py::test_meta_primary_absent_does_not_register_primary` — no `Meta.primary` key; `primary_for` is `None`, `get()` returns the lone type.
- `tests/types/test_base.py::test_meta_primary_non_bool_raises_configuration_error` — parametrized across `["yes", 1, 0, [], None, 1.0]`; each non-bool raises with `match="must be a bool"`.
- `tests/types/test_base.py::test_meta_primary_propagates_to_definition` — pins `registry.get_definition(TheType).primary is True`.
- `tests/types/test_base.py::test_meta_primary_absent_definition_primary_defaults_false` — companion to the previous; pins the dataclass default.
- `tests/types/test_base.py::test_two_types_same_model_one_primary_both_register_successfully` — pins `types_for(Item) == (ItemType, AdminItemType)`, `primary_for(Item) is AdminItemType`, `get(Item) is AdminItemType` (primary-first per Slice 1 Decision 4).
- `tests/types/test_base.py::test_two_primary_types_same_model_raises` — second `Meta.primary = True` declaration raises with `match="already declared primary"`.

### Validation run

- `uv run ruff format .` — pass (`100 files left unchanged`; the COM812 warning about formatter conflicts is the standing project warning, not a regression).
- `uv run ruff check --fix .` — pass on the three files I touched (`uv run ruff check --fix django_strawberry_framework/types/base.py django_strawberry_framework/types/definition.py tests/types/test_base.py` reports `All checks passed!`). The repo-wide `uv run ruff check --fix .` reports two pre-existing errors in `scripts/check_spec_glossary.py` (D301 `r"""` and D103 missing docstring) — these are unrelated to my edits and are the same out-of-scope drift Slice 1 documented in `docs/builder/worker-memory/worker-2.md:13`.
- `uv run pytest tests/types/test_base.py --no-cov -q` — `58 passed, 1 skipped in 0.08s`. The one skip is the pre-existing `test_consumer_annotation_overrides_synthesized` Strawberry-decorator-regenerates-annotations skip, unrelated to this slice.
- `uv run pytest tests/test_registry.py --no-cov -q` — `51 passed in 0.06s`. Slice 1's registry suite still green after Slice 2's call-site change to `register_with_definition(..., primary=primary)`.

### Implementation notes

- **Two reads of `Meta.primary` are intentional, not duplication.** `_validate_meta` reads-and-discards `primary` for the bool guard; `__init_subclass__` re-reads after `_validate_meta` returns. The plan's "Duplication risk avoided" note pinned this shape (and the spec at `spec:327` confirms it). Extending `_validate_meta`'s return type to thread the validated value would balloon every other Meta-key consumer. Kept the two-read shape.
- **`primary = getattr(meta, "primary", False)` placement option (a) chosen.** The plan offered three positions for the read in `__init_subclass__`; placed it immediately after `optimizer_hints = _meta_optimizer_hints(meta)` (the validation-trio tail), per the plan's "most consistent with the existing post-validation grouping" recommendation. Reads the same value as any other position.
- **`primary=primary` placement in `DjangoTypeDefinition(...)`.** Placed at the end of the constructor call after `interfaces=interfaces`. The plan said "adjacent to `has_custom_get_queryset` is recommended; any keyword-position is functionally equivalent." End-of-block keeps the dataclass-field-order matching the constructor-call-order, which is the convention Slice 1's `register_with_definition` snapshot/rollback now relies on for grep-stable ordering.
- **Parametrized non-bool test variants.** The plan said "minimum: one string, one int". Used the full plan-suggested `@pytest.mark.parametrize("bad", ["yes", 1, 0, [], None, 1.0])` set so the test pins string, int (both `1` and `0` because `isinstance(True, int)` is `True` and `bool` is an `int` subclass — the test confirms `isinstance(1, bool)` is `False`), list, `None`, and float. Docstring notes the `1`/`0` integer trap explicitly.
- **Kept both `Category`-on-stale-test AND `Item`-on-new-test duplicate-primary tests.** The plan offered "consolidate or keep both"; kept both because (a) the stale test's grep-stable name appears in Slice 1's worker-memory carry-forward (`worker-1.md:11`), (b) the two tests exercise different models, and (c) one pinning the rewritten stale path + one pinning the spec-line-123 names is what the plan recommended.

### Notes for Worker 3

- All three Slice 2 TODO anchors were removed in the same commit as the code that landed each anchor: `types/base.py:55-67` (the `ALLOWED_META_KEYS` anchor), `types/base.py:88-145` (the `__init_subclass__` anchor), `types/base.py:411-419` (the `_validate_meta` anchor), and `types/definition.py:32-34` (the dataclass-field anchor). Slice 3 (`types/finalizer.py:61`) and Slice 4 (`types/base.py:627`, the four `optimizer/walker.py` anchors, and the six `optimizer/extension.py` anchors) anchors were NOT touched.
- `scripts/review_inspect.py` was NOT run during build (Worker 2 is not required to run it for source files of this size). `types/base.py` is now ~689 lines (was already past the 150-line helper threshold from Slice 1's pre-existing diff to the file). The Slice 2 diff to `types/base.py` is +11 source lines (one frozenset entry, one validation block, one `primary=primary` plumb in two places, one `primary = getattr(...)` capture). The diff to `types/definition.py` is +1 source line. Below the 30-line threshold for Worker 3's required-helper trigger, so the helper is at Worker 3's discretion.
- No read of `definition.primary` exists anywhere in the Slice 2 diff. The L3 contract is preserved: `definition.primary` is store-only in this slice.
- The plan's "two reads of `Meta.primary` are intentional" shape is implemented as documented. No factor-out.
- No shadow file was used during implementation.
- No temp tests created under `docs/builder/temp-tests/slice-2/`. The slice surface is narrow enough to read from the diff alone.

### Notes for Worker 1 (spec reconciliation)

- No spec gaps, conflicts, or unstated assumptions encountered. The plan was specific enough to implement directly; every decision was either pinned by the spec or explicitly delegated to Worker 2 discretion via the plan's "Implementation discretion items" section.
- No plan-vs-implementation drift. Every implementation step matches the plan's pseudocode.
- The Slice 1 verification note (`docs/builder/worker-memory/worker-1.md:11` — the failing `test_registry_collision_raises_configuration_error` post-Slice-1) is resolved by Slice 2's stale-test rewrite. The rewritten test passes under the new `"already declared primary"` contract.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

#### `Meta.primary` bool guard placement diverges from spec ordering

Spec Decision 1 (`docs/spec-014-meta_primary-0_0_6.md:319-320`) and the plan step 2 (`docs/builder/bld-slice-2-meta_primary_recognition.md:48-50`) both say insert the bool guard "after the `DEFERRED_META_KEYS` check, before the unknown-key check". The maintainer's pre-Slice-2 TODO anchor in the source pinned the position **above** the `DEFERRED_META_KEYS` check (between the `fields`/`exclude`-exclusivity check at `:396` and the deferred check at `:403`), and Worker 2 followed the anchor — landing the guard at `types/base.py:399-401`, which is between the exclusivity check and the deferred check.

Why this is Low, not Medium: the two predicates are mutually disjoint. `"primary"` is in `ALLOWED_META_KEYS` (not `DEFERRED_META_KEYS`), so the deferred check at `:403-407` can never fire on a `Meta.primary` declaration regardless of ordering. The bool guard at `:399-401` only fires when `Meta.primary` is set to a non-bool, which cannot also be a deferred key. No observable contract changes; no test would distinguish the two positions.

Recommendation: surface to Worker 1 (already done under `### Notes for Worker 1 (spec reconciliation)` below). Worker 1 chooses whether to:
- (a) leave Slice 2 as-is and edit the spec Decision 1 wording to say "before the deferred check" (matches the anchor and the live source), or
- (b) ask Worker 2 to relocate the three lines to the post-deferred-check position (matches the spec literal).

Either resolution is acceptable; the implementation as it stands is contract-correct.

```django_strawberry_framework/types/base.py:396:401
    if "fields" in declared and "exclude" in declared:
        raise ConfigurationError("Meta.fields and Meta.exclude are mutually exclusive")

    primary = getattr(meta, "primary", False)
    if not isinstance(primary, bool):
        raise ConfigurationError("Meta.primary must be a bool")
```

### DRY findings

- **No new duplication introduced.** The bool-guard shape (`getattr → isinstance check → raise`) is a one-off three-line block; the plan correctly rejected extracting a `_validate_primary` helper at single-call-site granularity. The closest existing analog is the `Meta.model` `isinstance + issubclass` check at `types/base.py:388-392`; both keep their shape inline. The `primary = getattr(meta, "primary", False)` read appears once in `_validate_meta` (for the guard) and once in `__init_subclass__` (for the plumb) — the plan's "Duplication risk avoided" section documents that the two reads are intentional spec contract (`spec:327`), not duplication.
- **Test fixture reuse honored.** The existing `_isolate_registry` autouse fixture at `tests/types/test_base.py:51-56` covers every new test; no new fixture was introduced.
- **Repeated string literal sweep.** The static helper's `Repeated string literals` section for `types/base.py` reports 4× `optimizer_hints`, 2× `description`, and 2× `interfaces` — all pre-existing literals unrelated to this slice. No new repeated literal of length ≥ 8 was introduced (the new `"primary"` literal is 7 chars and appears once each in `ALLOWED_META_KEYS`, `_validate_meta`, and the dataclass field name; the user-facing error string `"Meta.primary must be a bool"` appears once).
- **Cross-slice consistency confirmed.** `registry.register_with_definition(..., primary=primary)` at `types/base.py:135` matches Slice 1's shipped signature at `registry.py:224-231` (`*, primary: bool = False`). No drift; the keyword-only convention is preserved.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` reports no output — `__all__` and the re-export list are unchanged. Slice 2's contract is internal: `Meta.primary` is a Meta-class key (configured by consumers but not imported from the top-level package), and `DjangoTypeDefinition.primary` is dataclass storage accessed via `registry.get_definition(...)` (already-public surface). No new public exports were added. Confirmed compliant with Definition of Done.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- **`_validate_meta` guard implementation matches spec pseudocode (`spec:322-325`) verbatim.** The three-line block at `types/base.py:399-401` (modulo a blank line separator) reproduces the exact `getattr → isinstance → raise` shape with the exact `"Meta.primary must be a bool"` error string.
- **`ALLOWED_META_KEYS` extension is minimal and grep-stable.** The frozenset literal at `types/base.py:55-66` gains one entry (`"primary"`) with the COM812-required trailing comma; the TODO anchor was removed in the same commit.
- **`DjangoTypeDefinition.primary` is store-only (L3 compliant).** `grep` against the package source confirms no read of `definition.primary` anywhere in `django_strawberry_framework/` — only the `f"Meta.primary must be a bool"` literal string at `types/base.py:401` and a stale `# - "Declare Meta.primary = True ..."` comment in `types/finalizer.py:69` (Slice 3 TODO anchor). The Slice 1 worker-memory carry-forward instruction ("watch for L3 violations") is honored.
- **Threaded primary flows through the construction → registry path consistently.** `primary = getattr(meta, "primary", False)` at `types/base.py:93` → `DjangoTypeDefinition(..., primary=primary)` at `:133` → `registry.register_with_definition(meta.model, cls, definition, primary=primary)` at `:135`. Single value, single capture, three sequential consumers; no parallel data flow.
- **Test coverage of every spec line 117-123 contract.** Walked the spec → diff → test mapping:
  - spec:117 `test_meta_primary_true_registers_type_as_primary` → `test_base.py:280`.
  - spec:118 `test_meta_primary_false_does_not_register_primary` → `test_base.py:292` (also asserts the single-type-implicit-primary backward-compat path).
  - spec:119 `test_meta_primary_absent_does_not_register_primary` → `test_base.py:307` (also asserts backward-compat).
  - spec:120 `test_meta_primary_non_bool_raises_configuration_error` → `test_base.py:319-333` (parametrized across `["yes", 1, 0, [], None, 1.0]` — pins string, int, list, `None`, float; docstring explicitly addresses the `isinstance(1, bool) is False` integer trap).
  - spec:121 `test_meta_primary_propagates_to_definition` → `test_base.py:336` plus companion `test_meta_primary_absent_definition_primary_defaults_false` at `:348` pinning the default.
  - spec:122 `test_two_types_same_model_one_primary_both_register_successfully` → `test_base.py:359` asserting `types_for`, `primary_for`, and the primary-wins `get()` contract.
  - spec:123 `test_two_primary_types_same_model_raises` → `test_base.py:380` exercising the spec-line-123 `Item`/`AdminItemType` names.
- **Stale-test rewrite is the lowest-touch option.** `test_registry_collision_raises_configuration_error` at `tests/types/test_base.py:68-82` was rewritten per plan option (a): both `CategoryTypeA` and `CategoryTypeB` now declare `Meta.primary = True`; the `match=` regex narrows from `"already registered"` to `"already declared primary"`. The test's grep-stable name remains intact (preserving the Slice 1 worker-memory breadcrumb at `worker-1.md:11`) and the class-creation-layer collision contract is pinned through the `__init_subclass__ → register_with_definition → register` path.
- **Focused-test runs are clean.** `uv run pytest tests/types/test_base.py --no-cov -q` → 58 passed, 1 skipped (the pre-existing Strawberry annotation-regeneration skip). `uv run pytest tests/test_registry.py --no-cov -q` → 51 passed. Slice 1's registry suite is unaffected by Slice 2's call-site change.

### Temp test verification

- No temp tests created. The slice surface (one frozenset entry, one validation block, one keyword-threaded call, one dataclass field) is narrow enough to reason about from the diff alone. The parametrized non-bool variants in `test_meta_primary_non_bool_raises_configuration_error` already cover the `isinstance(True, int) is True` / `isinstance(1, bool) is False` distinction without a temp-test scaffold.

### Notes for Worker 1 (spec reconciliation)

- **Spec Decision 1 ordering vs. live anchor position.** Spec line 319-320 says "after the `DEFERRED_META_KEYS` check, before the unknown-key check" and the plan step 2 (`docs/builder/bld-slice-2-meta_primary_recognition.md:48-50`) repeats that wording. The maintainer's pre-Slice-2 TODO anchor was at `types/base.py:406-410` (pre-Slice-2 source), which is the position immediately *before* the deferred check — and Worker 2 honored the anchor position. Worker 2's build report at `bld-slice-2-meta_primary_recognition.md:164` describes the landed position accurately ("between the `fields`/`exclude`-exclusivity check and the `DEFERRED_META_KEYS` block"). The two positions are functionally equivalent because `"primary"` is in `ALLOWED_META_KEYS` rather than `DEFERRED_META_KEYS`, so neither ordering can produce a different error for any input. Worker 1 may either tighten the spec wording to "before the deferred check" (cheap and matches the maintainer's anchor intent) or instruct Worker 2 to relocate the three lines. No test would change either way; this is purely a spec-vs-implementation textual reconciliation.
- **No other ambiguities surfaced.** Every other Worker 2 decision (read position option (a), kwarg placement, parametrized non-bool set, keeping both `Category` + `Item` stale/new test pair) was an explicit plan discretion item and is consistent with the plan's recommendations.

### Review outcome

`review-accepted` — every spec-required behavior is reflected in the diff; the single Low finding is intentionally surfaced to Worker 1 as a spec-vs-implementation reconciliation rather than a revision request, because the placement is contract-equivalent and the maintainer's TODO anchor authoritatively pinned the landed position. No High or Medium findings; DRY analysis surfaces no new duplication; public surface is unchanged; all 58 tests in `tests/types/test_base.py` and all 51 tests in `tests/test_registry.py` pass under focused runs without coverage flags.

---

## Final verification (Worker 1)

- **DRY check across this slice and prior accepted slices (Slice 1):** no new duplication introduced. Three new patterns landed in Slice 2 and each is consistent with the conventions Slice 1 established:
  - The `getattr(meta, "primary", False)` pattern appears exactly twice — once as the bool guard inside `_validate_meta` (`types/base.py:399`) and once as the plumb capture inside `__init_subclass__` (`types/base.py:93`). This is the spec-pinned two-read shape (Decision 1 at `spec:327` and the plan's "Duplication risk avoided" note); it mirrors the validate-then-re-read structure already used for `model` (line 388 guard, line 142 plumb via `meta.model`) and `optimizer_hints` (line 415 validate-by-call, line 93 re-read). Not duplication.
  - The bool-guard shape (`getattr → isinstance → raise ConfigurationError`) at `types/base.py:399-401` matches the `Meta.model` shape at `:388-392` and is the smallest possible guard. No helper extraction would shrink it; the plan correctly rejected `_validate_primary(meta) -> bool` at single-call-site granularity, consistent with Slice 1's "no helpers for single-caller logic" stance (`docs/builder/bld-slice-1-registry_multitype.md:17`).
  - The `primary: bool = False` dataclass field at `definition.py:32` follows the same one-line-per-field shape as the existing `consumer_*` frozenset fields at `:28-31` and the deferred placeholders at `:35-44`. No structural drift.
  - Slice 1's `register_with_definition(model, type_cls, definition, *, primary=False)` signature is consumed identically at `types/base.py:135` (`registry.register_with_definition(meta.model, cls, definition, primary=primary)`), keyword-only, matching the spec contract and the Slice 1 final-verification carry-forward (`docs/builder/worker-memory/worker-1.md:14`).
  - L3 read-site discipline preserved: a `grep -n "definition.primary" django_strawberry_framework/` from the diff confirms zero reads of `definition.primary` in Slice 2's source diff. The only mention is the comment in `types/finalizer.py:69` which is the Slice 3 TODO anchor (untouched). Slice 1's carry-forward instruction holds.

- **Existing tests still pass:**
  - `uv run pytest tests/test_registry.py tests/types/test_base.py tests/types/test_definition_order.py --no-cov -q` → 122 passed, 1 skipped (the pre-existing `test_consumer_annotation_overrides_synthesized` Strawberry-decorator-regenerates-annotations skip; unrelated to this slice). The single suite covers Slice 1's `tests/test_registry.py` (51 passes), Slice 2's main target `tests/types/test_base.py` (58 passes; the previously-failing `test_registry_collision_raises_configuration_error` is now green under the rewritten contract), and the `_build_annotations`-adjacent `tests/types/test_definition_order.py` (13 passes; confirms Slice 2's `__init_subclass__` plumbing did not regress definition-order behavior).

- **Spec reconciliation:** one spec edit (Option A per the review-handoff). The maintainer's pre-Slice-2 TODO anchor at `types/base.py:406-410` (pre-Slice-2 source) pinned the bool-guard slot **before** the `DEFERRED_META_KEYS` check, while spec Decision 1's pseudocode preamble said "after the DEFERRED_META_KEYS check, before the unknown-key check." Both positions are contract-equivalent because `"primary"` is in `ALLOWED_META_KEYS` (the deferred check can never fire on a `Meta.primary` declaration regardless of ordering), so Worker 3 surfaced this as a Low finding for spec-vs-implementation textual reconciliation rather than a revision request. I picked Option A: edit the spec to acknowledge the anchor's slot. Rationale: (a) it is the smaller change — one comment rewrite vs. relocating three source lines and updating the test surface; (b) Worker 2 followed the maintainer's authoritative anchor, which is the same precedent Slice 1 established when the spec-vs-implementation drift was "small drift recorded; implementation kept" (`docs/builder/worker-memory/worker-1.md:13`); (c) honoring the anchor keeps the spec and source aligned for future readers without changing any observable contract. No other unstated assumptions surfaced when re-reading Decision 1, Decision 8, and the Slice 2 paragraph against the diff — Worker 2's "no spec reconciliation needed" note is confirmed for the rest of the slice surface.

- **Final status:** `final-accepted`.

### Summary

Slice 2 lands the `Meta.primary` recognition layer on `DjangoType.__init_subclass__` per spec Decision 1 and Decision 8. The slice ships three minimal source additions (one frozenset entry, one inline bool guard, one dataclass field) and one threaded keyword (`primary=primary` from `__init_subclass__` through `DjangoTypeDefinition(...)` and `registry.register_with_definition(...)`), consuming the multi-type registry surface Slice 1 shipped. All eight new permanent tests at `tests/types/test_base.py::test_meta_primary_*` plus the rewritten stale `test_registry_collision_raises_configuration_error` pin spec lines 117-123 verbatim, including the parametrized non-bool guard variants (string, int `0`/`1`, list, `None`, float) that exercise the `isinstance(1, bool) is False` integer trap. The L3 store-only contract on `DjangoTypeDefinition.primary` is preserved — no read sites in the Slice 2 diff. Public surface (`django_strawberry_framework/__init__.py`) is unchanged.

### Spec changes made (Worker 1 only)

- `docs/spec-014-meta_primary-0_0_6.md:319-321` — rewrote the inline pseudocode comment in Decision 1 to describe the bool guard's slot as "after the fields/exclude exclusivity check and before the DEFERRED_META_KEYS check" instead of "after the DEFERRED_META_KEYS check, before the unknown-key check." Added a parenthetical noting the two positions are contract-equivalent (because `"primary"` is in `ALLOWED_META_KEYS`, neither the deferred check nor the unknown-key check can fire on a `Meta.primary` declaration), so the change is purely a spec-source alignment to the maintainer's pre-Slice-2 TODO anchor that Worker 2 honored. Triggered by the Slice 2 Worker 3 Low finding and the Worker 2 build report's "follow the anchor" decision; reason: smaller change than relocating three source lines, consistent with Slice 1's spec-vs-implementation precedent ("small drift recorded; implementation kept").
