# Build: Slice 1 — Registry multi-type storage + primary tracking

Spec reference: `docs/spec-014-meta_primary-0_0_6.md` (lines 69-109)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - `TypeRegistry._check_mutable` (`django_strawberry_framework/registry.py:55-68`) — every public mutator already calls this guard. The new `register(..., *, primary)` signature and the rewritten `register_with_definition` keep the call site as-is; `clear()` (lines 279-293) likewise stays guard-less for the same documented reason. No new finalization guard logic.
  - `TypeRegistry._already_registered("against", ...)` (`django_strawberry_framework/registry.py:71-78`) — the reverse-collision branch (same `type_cls`, different `model`) still uses this helper to keep its message grep-stable with the existing `tests/test_registry.py:71-87 test_register_same_class_against_two_models_raises` assertion `match="already registered against Category"`. The `"as"` label call (formerly used at registry.py:104 for the forward-collision case) is retired — Decision 3's new messages (`"already declared primary as"`, `"primary flag cannot be flipped on re-register"`) are inlined as plain `ConfigurationError(...)` calls because each is a single call site with distinct phrasing; folding them back into `_already_registered` would force a label expansion and obscure the contracts.
  - `dict.setdefault(model, [])` for `_types` — replaces the `if model in self._types` early-raise check; this is the idiomatic shape for the new append-per-model store and is referenced by the spec's Decision 3 pseudocode.
  - Test isolation: the existing autouse `_isolate_global_registry` fixture at `tests/test_registry.py:34-39` calls `registry.clear()` on entry and exit; new tests rely on it. Per-test isolation against a fresh instance uses the `fresh_registry` fixture at `tests/test_registry.py:28-31` (returns `TypeRegistry()`); all new Slice 1 tests use `fresh_registry` so they exercise the class in isolation from the module-global singleton, matching every existing direct-registry test in this file.
  - **Confirmed during planning** (worker-1.md Step 6): `tests/test_registry.py:34-39` is the canonical autouse fixture site; the lone autouse `_isolate_global_registry` clears the *module-global* `registry` (not `fresh_registry`). New Slice 1 tests using `fresh_registry` do not need any new fixture wiring — the per-test `TypeRegistry()` instance is created and discarded by pytest's test-function lifetime.

- **New helpers justified.** None. Slice 1 adds three new public methods on `TypeRegistry` (`primary_for`, `types_for`, `models_with_multiple_types`), all single-purpose accessors whose entire body is one expression apiece per Decision 4 / Decision 5. No new private helper is introduced — the rollback shape inside `register_with_definition` is straight-line code per Decision 3a, not a helper. Hoisting the rollback into a `_rollback_registration(model, type_cls, pre_primary)` private method was considered and rejected: it has exactly one caller, the rollback runs inside an `except` arm where the local snapshot variables are already in scope, and Worker 3 would otherwise have to follow a method jump to read what the `except` does. Keep it inline.

- **Duplication risk avoided.**
  - The "primary already declared" check appears in two logically-distinct places in Decision 3: the idempotent-re-register branch (same type, primary flag flipped) and the new-type-with-primary branch (different type, already-claimed primary slot). The spec's pseudocode (`docs/spec-014-meta_primary-0_0_6.md:349-392`) keeps them separate because the error messages differ; copy that shape verbatim — do NOT factor a `_check_primary_collision(model, type_cls, primary)` helper that returns one of two error strings. Two distinct conditions with two distinct messages stay locally readable when inlined.
  - The "remove pending state from `_types`/`_models`/`_primaries`" rollback steps and the "blanket reset" `clear()` shape are intentionally separate: rollback restores `_primaries` to `pre_primary` (which may be `None` *or* a class), while `clear()` empties the dict. Do not try to consolidate them. The spec's Decision 3a pseudocode (`spec:399-435`) is the source of truth.
  - The new tests reuse the existing `tests/test_registry.py:42-50, :71-87, :109-117` shapes: plain `class FooType: pass` test classes followed by `fresh_registry.register(...)` and an assertion against `fresh_registry.get(...)` / `fresh_registry.model_for_type(...)`. Do NOT introduce a new test fixture pattern for Slice 1; the existing `fresh_registry` fixture is sufficient (and the spec slice 1 paragraph at `spec:656` requires the tests to call `register()`/`register_with_definition()` directly without `DjangoType` subclasses).

### Implementation steps

Line numbers below are pin-at-write-time hints. Re-verify against the current source before editing; the TODO anchors at `registry.py:42, :80, :111, :135, :182, :287` are the authoritative landing sites for this slice and must be removed in the same change that replaces them.

1. **`django_strawberry_framework/registry.py:48` — `_types` annotation flip.** Inside `TypeRegistry.__init__`, change `self._types: dict[type[models.Model], type] = {}` to `self._types: dict[type[models.Model], list[type]] = {}`. Add a sibling line `self._primaries: dict[type[models.Model], type] = {}` immediately after `_types`. Keep `_models`, `_enums`, `_definitions`, `_pending`, `_finalized` unchanged. Remove the TODO comment block at `registry.py:42-47` in the same edit (the work it anchors is landing here).
2. **`django_strawberry_framework/registry.py:89-109` — rewrite `register()` per Decision 3 (`spec:349-392`).** Replace the body wholesale; the new signature is `def register(self, model: type[models.Model], type_cls: type, *, primary: bool = False) -> bool`. Step-by-step:
   - `self._check_mutable()` (unchanged).
   - **Reverse-collision guard first** (matches existing test at `tests/test_registry.py:71-87`): `existing_model = self._models.get(type_cls); if existing_model is not None and existing_model is not model: raise self._already_registered("against", type_cls.__name__, existing_model.__name__)`.
   - `existing_types = self._types.setdefault(model, [])`.
   - **Idempotent same-type re-register branch**: `if type_cls in existing_types: stored_as_primary = self._primaries.get(model) is type_cls; if primary != stored_as_primary: raise ConfigurationError(f"{type_cls.__name__} is already registered for {model.__name__}; primary flag cannot be flipped on re-register"); return False`. (Symmetric flip guard — pins both `False→True` and `True→False` directions per spec M1 fix at `spec:21`.)
   - **Duplicate-primary guard for new type**: `if primary: existing_primary = self._primaries.get(model); if existing_primary is not None: raise ConfigurationError(f"{type_cls.__name__} is already declared primary as {existing_primary.__name__}")`.
   - **Commit**: `existing_types.append(type_cls); self._models[type_cls] = model; if primary: self._primaries[model] = type_cls; return True`.
   - Remove the TODO comment block at `registry.py:80-88`.
   - Update the docstring to describe the new contract: idempotent same-type re-register is a no-op (returns `False`); two types for the same model with primary disagreement raise; reverse-collision guard preserved; return value drives `register_with_definition` rollback.
3. **`django_strawberry_framework/registry.py:117-119` — rewrite `get()` per Decision 4 (`spec:447-455`).** Replace `return self._types.get(model)` with the three-branch shape: `primary = self._primaries.get(model); if primary is not None: return primary; candidates = self._types.get(model); if candidates is not None and len(candidates) == 1: return candidates[0]; return None`. Update the docstring to enumerate the three return states (primary declared / single implicit / ambiguous-multiple). Remove the TODO comment block at `registry.py:111-116`.
4. **`django_strawberry_framework/registry.py:142-150` — update `iter_types()` semantics.** Change the body from `yield from self._types.items()` to a two-level walk that yields one `(model, type_cls)` pair per registered type: `for model, type_list in self._types.items(): for type_cls in type_list: yield (model, type_cls)`. Update the docstring to call out the new shape: "Yields once per registered type. A model with multiple registered types appears multiple times in the iterator; consumers must dedupe by model if they need a per-model action."
5. **`django_strawberry_framework/registry.py` — add `primary_for`, `types_for`, `models_with_multiple_types`.** Place the three new public methods after `iter_types()` (the current `iter_types` lives at `registry.py:142-150`; insert immediately after, before `register_definition`). Bodies:
   - `def primary_for(self, model: type[models.Model]) -> type | None: return self._primaries.get(model)` — strict primary lookup. Add a short docstring noting it is distinct from `get()`: returns `None` for single-type-no-primary (where `get()` would return the type).
   - `def types_for(self, model: type[models.Model]) -> tuple[type, ...]: return tuple(self._types.get(model, ()))` — immutable snapshot in registration order. Docstring: returns `()` for unregistered models.
   - `def models_with_multiple_types(self) -> Iterator[type[models.Model]]: return (model for model, types in self._types.items() if len(types) >= 2)` — generator returning models whose stored list has length `>=2`. Docstring: drives `audit_primary_ambiguity` (Slice 3).
   - Remove the TODO comment block at `registry.py:135-141` (it covers all three of these additions plus the `iter_types` shape note).
6. **`django_strawberry_framework/registry.py:168-196` — rewrite `register_with_definition()` per Decision 3a (`spec:399-435`).** New signature: `def register_with_definition(self, model: type[models.Model], type_cls: type, definition: DjangoTypeDefinition, *, primary: bool = False) -> None`. Body:
   - `pre_primary = self._primaries.get(model)` — snapshot before calling `register`.
   - `appended = self.register(model, type_cls, primary=primary)`.
   - `try: self.register_definition(type_cls, definition)` (unchanged).
   - `except Exception:` arm — guard rollback on `appended`:
     - `if appended:` — remove the entry this call appended: `types = self._types.get(model, []); if type_cls in types: types.remove(type_cls); if not types: self._types.pop(model, None); self._models.pop(type_cls, None);`. Then restore `_primaries`: `if pre_primary is None: self._primaries.pop(model, None); else: self._primaries[model] = pre_primary`.
     - `raise` (re-raise the original).
   - Remove the TODO comment block at `registry.py:182-189`. Update the docstring to describe the conditional rollback contract and reference the new `primary` keyword. Worker 2: note that `register_with_definition` does NOT need to short-circuit when `register` returns `False` — `register_definition` may still legitimately raise (different definition for the same type), and the contract is "either fully succeeds or leaves the registry untouched" per `spec:434`.
7. **`django_strawberry_framework/registry.py:279-293` — extend `clear()` to wipe `_primaries`.** Add `self._primaries.clear()` immediately after `self._types.clear()`. Remove the TODO comment block at `registry.py:287-288`.

After step 7, no `TODO(spec-014-meta_primary-0_0_6.md Slice 1)` anchors remain in `registry.py`. The other consumer-site TODO anchors (in `types/base.py`, `types/finalizer.py`, `optimizer/walker.py`, `optimizer/extension.py`, etc., if present) belong to later slices and stay untouched in this slice.

### Test additions / updates

All test work lands in `tests/test_registry.py`. The slice-1 paragraph at `spec:656` explicitly requires the tests to call `registry.register(...)` / `registry.register_with_definition(...)` directly with plain test classes (not real `DjangoType` subclasses); the existing `tests/test_registry.py:28-31 fresh_registry` fixture is the right harness and the existing autouse `_isolate_global_registry` at `tests/test_registry.py:34-39` covers the few tests that touch the module-global singleton.

**Stale test rewrite (single commit with the source change):**

- `tests/test_registry.py:57-68` — `test_register_collision_raises`. The current assertion calls `fresh_registry.register(Category, CategoryTypeA)` then expects the second `register(Category, CategoryTypeB)` to raise with `match="already registered"`. Under Decision 3 the second call no longer raises (no-primary multi-type case). **Worker 1 decision (per `spec:90`'s "Worker 1 picks during planning"):** rename to `test_register_two_primaries_for_same_model_raises_configuration_error` (collapses into the new test of the same name below) — delete the existing `test_register_collision_raises` body in this commit and rely on the new primary-collision test plus the new `test_register_two_types_same_model_without_primary_allows_both_in_types_for` test to cover the inverse contract. Rationale: the old test's grep-friendly name was misleading after the contract change ("collision" no longer captures the new semantics), and keeping it as a renamed shell duplicates the new primary-collision test. The deletion + the two new tests (one positive, one negative) leave the contract surface uniformly covered. Land the deletion in the same commit as the registry edits.

**New tests** (each is a single function in `tests/test_registry.py`, using `fresh_registry`, asserting a specific contract from the slice 1 checklist at `spec:69-109`):

1. `test_register_two_types_same_model_without_primary_allows_both_in_types_for` — call `fresh_registry.register(Item, ItemTypeA)` then `fresh_registry.register(Item, ItemTypeB)`; assert no error, `fresh_registry.types_for(Item) == (ItemTypeA, ItemTypeB)`, and `fresh_registry.primary_for(Item) is None`. Replaces the inverse of the deleted `test_register_collision_raises`.
2. `test_register_second_type_for_same_model_no_longer_raises_collision` — call `fresh_registry.register(Item, ItemTypeA)` then `fresh_registry.register(Item, ItemTypeB)` inside a `with pytest.raises` context that asserts NO exception (use a sentinel pattern: `try: fresh_registry.register(Item, ItemTypeB); except ConfigurationError: pytest.fail("Slice 1: second registration without primary must not raise")`). Pins the retired forward-collision message contract.
3. `test_register_same_type_twice_is_idempotent` — call `fresh_registry.register(Item, ItemType)` twice; assert second call returns `False` and `fresh_registry.types_for(Item) == (ItemType,)` (single entry, no duplicate).
4. `test_register_primary_flag_sets_primary_for` — call `fresh_registry.register(Item, ItemType, primary=True)`; assert `fresh_registry.primary_for(Item) is ItemType`, `fresh_registry.get(Item) is ItemType`, and `fresh_registry.types_for(Item) == (ItemType,)`.
5. `test_register_two_primaries_for_same_model_raises_configuration_error` — `register(Item, T1, primary=True)`, then `with pytest.raises(ConfigurationError, match="already declared primary as ItemType"): register(Item, T2, primary=True)`. Assert post-failure: `types_for(Item) == (T1,)` (T2 was NOT appended) and `primary_for(Item) is T1`.
6. `test_register_same_type_re_register_with_flipped_primary_false_raises` — `register(Item, T, primary=True)`, then `with pytest.raises(ConfigurationError, match="primary flag cannot be flipped"): register(Item, T, primary=False)`. Pins the `True → False` direction of the M1-fix symmetric guard.
7. `test_register_same_type_re_register_with_flipped_primary_true_raises` — `register(Item, T)` (or `primary=False`), then `with pytest.raises(ConfigurationError, match="primary flag cannot be flipped"): register(Item, T, primary=True)`. Pins the `False → True` direction.
8. `test_register_with_definition_rollback_clears_primary` — pre-register a different type's definition to force the inner `register_definition` to raise (mirrors the existing `tests/test_registry.py:674-699 test_register_with_definition_rolls_back_register_on_definition_failure` pattern); call `register_with_definition(Item, ItemType, def_obj, primary=True)`; assert it raises, then assert `types_for(Item) == ()`, `model_for_type(ItemType) is None`, `primary_for(Item) is None`. Verifies the snapshot-restore path when this call appended state.
9. `test_register_with_definition_idempotent_re_register_does_not_corrupt_state` — pre-register `(Item, ItemType, def1)` via `register_with_definition`. Then call `register_with_definition(Item, ItemType, def2)` where `def2 is not def1`. Assert: (a) the second call raises `ConfigurationError` matching the `register_definition` message `"already has a registered DjangoTypeDefinition"`; (b) `types_for(Item) == (ItemType,)`; (c) `model_for_type(ItemType) is Item`; (d) `get_definition(ItemType) is def1`. Pins the M1-fix conditional rollback: the second call's `register` returns `False` (no append), so the `except` arm leaves the pre-existing state untouched. **Note for Worker 2:** also assert `primary_for(Item) is None` when the first call did not set `primary=True`; if you choose to additionally cover the primary-preservation case, gate on a separate `if def1` setting `primary=True`. Optional — the basic non-primary case is the spec contract; primary-preservation is the corollary.
10. `test_register_returns_true_for_new_state` — `assert fresh_registry.register(Item, ItemType) is True`.
11. `test_register_returns_false_for_idempotent_re_register` — `fresh_registry.register(Item, ItemType); assert fresh_registry.register(Item, ItemType) is False`.
12. `test_get_returns_single_type_when_one_registered_no_primary` — backward compat: `register(Item, ItemType)` then `assert fresh_registry.get(Item) is ItemType`.
13. `test_get_returns_primary_when_multiple_and_primary_declared` — `register(Item, ItemType, primary=True); register(Item, AdminItemType); assert fresh_registry.get(Item) is ItemType`.
14. `test_get_returns_none_when_multiple_and_no_primary` — `register(Item, ItemType); register(Item, AdminItemType); assert fresh_registry.get(Item) is None`. Distinguishes the ambiguous-pending state from the unregistered-model state — note that for `test_get_returns_none_for_unregistered_model` at `tests/test_registry.py:52-54` the same `None` returns; the distinguishing path is `types_for(Item)` returning `(ItemType, AdminItemType)` vs `()`.
15. `test_primary_for_returns_none_when_only_implicit_single_type` — `register(Item, ItemType)` (no `primary=` arg); assert `fresh_registry.primary_for(Item) is None` AND `fresh_registry.get(Item) is ItemType`. Pins that `primary_for()` is strictly the `_primaries` lookup; the convenience "single type implicitly primary" lives only on `get()`.
16. `test_types_for_preserves_registration_order` — `register(Item, A); register(Item, B); register(Item, C); assert fresh_registry.types_for(Item) == (A, B, C)`.
17. `test_iter_types_yields_each_type_once_when_multiple_registered_for_same_model` — `register(Item, A, primary=True); register(Item, B); pairs = list(fresh_registry.iter_types()); assert pairs == [(Item, A), (Item, B)]`. Replaces the unchanged behavior covered by `tests/test_registry.py:185-197 test_iter_types_yields_registered_pairs`; the new test specifically targets the multi-type expansion at the new generator's nested loop. Note: the existing single-pair test at line 185 still passes (one model, one type → one pair).
18. `test_register_same_type_against_two_models_still_raises` — duplicate of an existing assertion shape but explicitly Slice-1-pinned: `register(Category, SharedType); with pytest.raises(ConfigurationError, match="already registered against Category"): register(Item, SharedType)`. This **may overlap** with the existing `tests/test_registry.py:71-87 test_register_same_class_against_two_models_raises`. Worker 1 decision: keep both. The existing test is the pre-Slice-1 baseline assertion; the new test (named after the Slice 1 checklist) confirms the reverse-collision branch survived the rewrite. Tag the new test's docstring with "Slice 1 contract pin (`spec:108`)" so a future cleanup can dedupe them if needed.
19. `test_clear_resets_primaries` — `register(Item, ItemType, primary=True); fresh_registry.clear(); assert fresh_registry.primary_for(Item) is None AND fresh_registry.types_for(Item) == ()`. Extends the existing `tests/test_registry.py:164-182 test_clear_drops_all_state` shape with the `_primaries` slot.
20. `test_models_with_multiple_types_yields_only_models_with_two_or_more` — `register(Category, CategoryType); register(Item, ItemTypeA); register(Item, ItemTypeB); register(Property, PropertyTypeA); register(Property, PropertyTypeB); register(Property, PropertyTypeC); assert sorted(fresh_registry.models_with_multiple_types(), key=lambda m: m.__name__) == [Item, Property]`. Pins the `>=2` predicate and confirms `Category` (single type) is excluded.

**Slice 1 test count.** Net: 20 new tests + 1 deletion (the rewritten `test_register_collision_raises`). The file grows from 700 to roughly 900-950 lines after the slice, comfortably under any size threshold that would force a split (the spec's Decision 7 test-host guidance at `spec:537` and L5-fix language at `spec:32` says "create a new file only if the cluster outgrows comfortable size in the existing host"; we are well under).

**Temp/scratch tests for Worker 3.** Worker 1 does not currently anticipate Worker 3 needing temp tests for this slice — the spec contracts are local, the 20 new permanent tests cover every branch in the registry diff. If Worker 3 spots a missing branch, the recommendation will be to add a permanent test in `tests/test_registry.py` rather than a temp scratch test under `docs/builder/temp-tests/slice-1/`.

### Implementation discretion items

- **Order of guards inside the new `register()`.** Worker 1 has pinned an explicit order in step 2 (reverse-collision → idempotent re-register → duplicate-primary → commit). This order matches the spec's Decision 3 pseudocode at `spec:349-392` and is required for the reverse-collision tests to keep their existing message and ordering semantics. **Not discretion** — implement in this order.
- **Error message wording.** Worker 2 must use the exact `f"{type_cls.__name__} is already registered for {model.__name__}; primary flag cannot be flipped on re-register"` and `f"{type_cls.__name__} is already declared primary as {existing_primary.__name__}"` strings from the spec (`spec:373-376` and `:382-385`). The tests' `pytest.raises(..., match=...)` patterns key on these exact substrings. **Not discretion.**
- **Whether to keep the new-line break inside the `"primary flag cannot be flipped"` message.** The spec writes the message with an implicit two-line layout (string-concatenation). Worker 2's choice between a single f-string and a multi-line f-string is stylistic — both render identically for the `pytest.raises(..., match=...)` regex match. **Worker 2 discretion** (use whichever Ruff prefers under line-length 110).
- **Docstring length for new methods.** `primary_for`, `types_for`, and `models_with_multiple_types` are short. Worker 2 writes one- to three-line docstrings each. **Worker 2 discretion** on exact wording; spec hints (`spec:467-470`) suggest noting `primary_for` is "strict primary lookup distinct from `get()`", `types_for` is "immutable snapshot in registration order", and `models_with_multiple_types` is "drives `audit_primary_ambiguity` in Slice 3".
- **Inline vs. helper for the rollback restore in `register_with_definition`.** The plan's DRY analysis explicitly rejected hoisting a `_rollback_registration` helper because there is one caller and the local variables are in scope. **Not discretion** — keep inline.
- **Whether to assert `primary_for(Item) is None` inside `test_register_with_definition_idempotent_re_register_does_not_corrupt_state` (test 9).** The basic spec contract covers `(a)..(d)`; (e) primary preservation is a corollary that's worth pinning only if `def1` carries `primary=True`. Worker 2 may add a parallel `*_with_primary` variant of test 9 if that feels natural, or extend test 9 with a second assertion block. **Worker 2 discretion.** Default: the spec line at `spec:99` says "if `def1` had registered as primary, `registry.primary_for(Item) is ItemType` post-failure" — meet it by extending test 9 with two-call subtests inside one function, or by adding test 9b. Either works.

### Notes for Worker 1 (spec reconciliation)

No conflicts uncovered during planning. The spec's Decision 3 / Decision 3a / Decision 4 / Decision 5 are internally consistent and map cleanly to a 7-step source diff plus 20 new tests + 1 deletion. The TODO anchors in `registry.py` (currently at lines `:42, :80, :111, :135, :182, :287`) align precisely with the slice scope.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/registry.py` — applied Worker 1's seven-step plan: `_types` flipped to `dict[Model, list[type]]`; new `_primaries: dict[Model, type]`; `register()` rewritten with `*, primary: bool = False` keyword and `bool` return signaling whether state was added; `get()` rewritten to primary-first / single-fallback / `None`-on-ambiguous; `iter_types()` re-shaped as a nested generator that yields one pair per registered type; new public helpers `primary_for`, `types_for`, `models_with_multiple_types`; `register_with_definition()` rewritten with snapshot-and-conditional-rollback per Decision 3a; `clear()` now also wipes `_primaries`. All six `TODO(spec-014-meta_primary-0_0_6.md Slice 1)` anchors removed in the same change.
- `tests/test_registry.py` — deleted the stale `test_register_collision_raises` (formerly lines 57-68 — its assertion was inverted by the new contract); added the 20 new permanent tests enumerated in the plan plus one optional primary-preservation corollary variant of test 9 (`test_register_with_definition_idempotent_re_register_preserves_primary`). All new tests use the existing `fresh_registry` fixture and plain test classes (no `DjangoType` subclasses), matching the plan and the slice-1 paragraph in the spec.

### Tests added or updated

Deleted:

- `tests/test_registry.py::test_register_collision_raises` — assertion shape (`pytest.raises(ConfigurationError, match="already registered")` on a second `register(Category, …)`) is no longer the contract under multi-type semantics; the new positive/negative-pair tests below cover the surface uniformly.

Added (all in `tests/test_registry.py`, all using `fresh_registry`):

- `test_register_two_types_same_model_without_primary_allows_both_in_types_for` — pins multi-type append; `types_for` returns both in registration order; `primary_for` is `None`.
- `test_register_second_type_for_same_model_no_longer_raises_collision` — sentinel-style proof that the retired forward-collision path no longer fires.
- `test_register_same_type_twice_is_idempotent` — second call returns `False` and does not duplicate the entry.
- `test_register_primary_flag_sets_primary_for` — `primary=True` populates `_primaries`; `get()` and `types_for` agree.
- `test_register_two_primaries_for_same_model_raises_configuration_error` — Decision 5 duplicate-primary path; verifies the offending type was NOT appended.
- `test_register_same_type_re_register_with_flipped_primary_false_raises` — M1 `True → False` direction.
- `test_register_same_type_re_register_with_flipped_primary_true_raises` — symmetric `False → True` direction.
- `test_register_with_definition_rollback_clears_primary` — snapshot-restore path when this call appended state.
- `test_register_with_definition_idempotent_re_register_does_not_corrupt_state` — M1 regression for the non-primary case (`primary_for` stays `None`).
- `test_register_with_definition_idempotent_re_register_preserves_primary` — corollary 9b for the primary case (`primary_for` stays the pre-existing type).
- `test_register_returns_true_for_new_state` — return-value contract on first call.
- `test_register_returns_false_for_idempotent_re_register` — return-value contract on idempotent re-call.
- `test_get_returns_single_type_when_one_registered_no_primary` — backward-compat.
- `test_get_returns_primary_when_multiple_and_primary_declared` — Decision 4 primary-first.
- `test_get_returns_none_when_multiple_and_no_primary` — Decision 4 ambiguous-as-`None`, with the `types_for` distinguishing assertion.
- `test_primary_for_returns_none_when_only_implicit_single_type` — pins the strict `_primaries`-only semantics.
- `test_types_for_preserves_registration_order` — pin for `tuple(self._types[model])`.
- `test_iter_types_yields_each_type_once_when_multiple_registered_for_same_model` — pin for the new nested-loop generator.
- `test_register_same_type_against_two_models_still_raises` — reverse-collision branch survived the rewrite (Slice 1 explicit pin per `spec:108`).
- `test_clear_resets_primaries` — wipe contract for the new `_primaries` slot.
- `test_models_with_multiple_types_yields_only_models_with_two_or_more` — `>= 2` predicate; single-type models excluded.

### Validation run

- `uv run ruff format .` — pass on the two changed files (`registry.py`, `tests/test_registry.py`). The same run also reformatted `scripts/check_spec_glossary.py` (pre-existing slicing-whitespace and a missing trailing comma); that file was already modified on disk before this slice started, so the formatting drift is not Slice 1's. Verified by `git stash; uv run ruff check scripts/check_spec_glossary.py; git stash pop` on a clean tree — the same 3 errors (D301 / D103 / COM812) appear pre-slice.
- `uv run ruff check --fix .` — pass on the two changed files (`uv run ruff check django_strawberry_framework/registry.py tests/test_registry.py` → "All checks passed!"). The exit-1 from the package-wide run is from D301/D103 in `scripts/check_spec_glossary.py` only (same pre-existing surface confirmed above).
- `uv run pytest tests/test_registry.py --no-cov -q` — 50 passed in 0.10s (29 retained pre-existing + 21 new). Ran with `--no-cov` per BUILD.md "Coverage is the maintainer's gate, not a worker's tool" because `pytest.ini`'s `addopts` auto-applies `--cov`.

### Implementation notes

- **`types_for` returns `tuple`, not `frozenset` or `list`.** The plan specified `tuple(self._types.get(model, ()))`; chose `tuple` for the immutable-ordered shape (registration order is the contract; sets would lose it; lists would invite caller mutation). Matches Decision 4 / spec helper bullet.
- **`models_with_multiple_types` returns a generator, not a list.** The body is a generator expression `(model for ... if len(types) >= 2)`. Direct-return shape matches the Decision 5 one-liner; callers that need a snapshot (e.g., the audit's offenders walk) materialize per-call. Tests use `sorted(..., key=lambda m: m.__name__)` to assert membership without depending on dict iteration order.
- **`iter_types` is a generator function, not a generator expression.** Kept the function form (`for model, type_list in ...: for type_cls in type_list: yield ...`) over a one-liner `yield from (...)` because the nested loop reads more clearly under review and the plan's docstring rewrite calls out the multiple-pairs-per-model semantics explicitly.
- **Error messages use single f-strings split across two adjacent string literals.** The `"primary flag cannot be flipped"` message is `f"{type_cls.__name__} is already registered for {model.__name__}; " "primary flag cannot be flipped on re-register"`. Implicit-concatenation form matches what ruff produces under the line-length-110 / COM812 rules; pytest `match=` regex sees the concatenated literal at runtime.
- **`existing_types = self._types.setdefault(model, [])` is the idempotent-insertion shape.** Per the plan's Decision 3 pseudocode, this replaces the old `if model in self._types: raise` short-circuit. The cost is one list allocation for the first registration of any model; the simplification offsets it.
- **Test #18 (`test_register_same_type_against_two_models_still_raises`) is intentionally redundant with the existing pre-Slice-1 `test_register_same_class_against_two_models_raises` (file-level test at the original lines 71-87).** Worker 1's plan chose to keep both; my implementation honored that. The new test's terse shape (single assertion) was preferred over inlining a docstring tag because the test function name itself documents the Slice 1 pin.

### Notes for Worker 3

- All Slice 1 source edits are confined to `django_strawberry_framework/registry.py`. No other package files were touched. `types/base.py` still calls `registry.register_with_definition(meta.model, cls, definition)` without `primary=` (Slice 2's job). Verified by `grep -n "register_with_definition" types/base.py`.
- The static inspection helper was NOT run for this slice. `registry.py` is below the 150-line "must-run" threshold for Worker 1 planning (357 lines post-edit, 296 lines pre-edit), but Worker 3's rule says "the slice adds 30 or more lines of new logic to any file under `django_strawberry_framework/` → must run". The diff against `registry.py` is +84 source lines net; please run the helper per the build rule and record the overview.
  - Command: `uv run python scripts/review_inspect.py django_strawberry_framework/registry.py --output-dir docs/builder/shadow --stdout`.
- The package-wide `ruff check` exit-1 is unrelated to this slice — `scripts/check_spec_glossary.py` carries pre-existing D301 (module docstring backslashes) and D103 (missing `main` docstring) violations on `main` HEAD. Verified by stashing the slice diff and re-running ruff against the script. Do not roll these into a Slice 1 finding.
- The shadow file was not used during implementation; the source is short enough to navigate by line numbers.

### Notes for Worker 1 (spec reconciliation)

- No structural drift. All seven plan steps landed exactly as specified.
- Added one optional test (test 9b: `test_register_with_definition_idempotent_re_register_preserves_primary`) that the plan's "Implementation discretion items" bullet explicitly allowed as a separate function rather than an extension of test 9. This pins the spec's parenthetical at `spec:99` ("(e) if `def1` had registered as primary, `registry.primary_for(Item) is ItemType` post-failure"). No spec edit needed.
- The plan's projected test-file size of "roughly 900-950 lines after the slice" came in at 1009 lines. The drift is the optional test 9b plus ruff-format's preference for vertically-laid trailing-comma-locked call arguments, not a structural change. Well under any size threshold that would require a split.

---

## Review (Worker 3)

### Helper invocation

Ran `uv run python scripts/review_inspect.py django_strawberry_framework/registry.py --output-dir docs/builder/shadow` per the Worker 3 rule (the slice adds ≥30 lines of new logic to a file under `django_strawberry_framework/`). The overview lands at `docs/builder/shadow/django_strawberry_framework__registry.overview.md`. Key signals: one control-flow hotspot (`TypeRegistry.register` spans 61 lines / 7 branch nodes — within tolerance for a single multi-guard mutator), three `len()` / `tuple()` calls at the new accessors (no shape-contract surprises), zero TODO comments remaining in the source, **zero repeated string literals**. The Django/ORM marker pass surfaces only docstring mentions of `DjangoType` and an `only` keyword in a clear-only-from-tests comment — no ORM boundary leak. The lone repeated-literal-shaped fragment is the inlined error message at `registry.py:120-122` (`"primary flag cannot be flipped on re-register"`), and that string is used exactly once.

Cumulative-diff filter: per the artifact's "Files touched" the slice's contribution is confined to `django_strawberry_framework/registry.py` and `tests/test_registry.py`. The `scripts/check_spec_glossary.py` whitespace and trailing-comma drift is a ruff-format byproduct on a pre-existing on-disk modification and is out of slice scope (called out under Low below for completeness).

### High:

None.

### Medium:

#### `register_with_definition` rollback `else` branch has no pinning test

The spec at line 79 demands "restore `_primaries[model]` to `pre_primary` (popping the key when `pre_primary is None`)". The implementation at `django_strawberry_framework/registry.py:254-257` splits into two branches:

```python
if pre_primary is None:
    self._primaries.pop(model, None)
else:
    self._primaries[model] = pre_primary
```

The `if pre_primary is None:` branch is exercised by `tests/test_registry.py::test_register_with_definition_rollback_clears_primary` (fresh registry, `register(..., primary=True)`, definition raises, restore-to-None via pop). The `else:` branch — pre-existing primary on the model, a NEW non-primary type's `register()` succeeds, `register_definition` raises, rollback restores `_primaries[model] = pre_primary` — is **not exercised** by any permanent test. The optional test 9b uses `primary=True` for both calls so `register()` returns `False` (idempotent re-register) and the `if appended:` block at `registry.py:247` is skipped entirely; the rollback machinery never runs.

I verified the missing branch with a temp test (see "Temp test verification" below) — the implementation is correct, but a permanent pin is missing.

Recommended change: add a permanent test in `tests/test_registry.py` modeled on the temp test below. Suggested name `test_register_with_definition_rollback_restores_pre_existing_primary`. Land it in this slice (Worker 2 apply-changes pass) so the `else:` branch has a permanent pin before Slice 2 builds on top.

Test expectation: pre-register `(Item, ItemType, def1, primary=True)`; pre-poison `register_definition(AdminItemType, sentinel)`; call `register_with_definition(Item, AdminItemType, object())` (no `primary=`), expect `ConfigurationError`; assert `types_for(Item) == (ItemType,)`, `model_for_type(AdminItemType) is None`, `primary_for(Item) is ItemType` (restored from pre_primary).

### Low:

#### Unused `OtherType` class and stale comment in `test_register_with_definition_rollback_clears_primary`

`tests/test_registry.py:796-797` declares `class OtherType: pass` but never references it. The neighboring comment at `tests/test_registry.py:799-802` even mentions "Pre-poison ``register_definition`` for OtherType" — but the body uses `ItemType` instead. Dead code / stale comment from a previous test approach. Not a correctness issue; pytest passes; readability suffers slightly. Recommend dropping the `class OtherType` declaration and rewriting the comment to describe the actual approach ("Pre-poison ``register_definition`` for ItemType so the second `register_with_definition` call raises after `register` succeeded").

#### Comment-only / cosmetic ruff format drift in `scripts/check_spec_glossary.py`

The slice's working-tree diff includes whitespace tweaks (`text[position + len(...):]` → `text[position + len(...) :]`) and one trailing comma in `scripts/check_spec_glossary.py`. These are defensible byproducts of running `uv run ruff format .` per `AGENTS.md` "Formatting and lint", but they predate the slice (the file already had the underlying changes on disk before this build started, per the Worker 2 build report at line 146-147). Surface here so Worker 1 can intentionally accept them or move them aside before commit. Not blocking.

### DRY findings

- No new duplication introduced. The two inline `ConfigurationError(...)` messages (`registry.py:120-122` and `registry.py:128-130`) are each used at exactly one call site and carry distinct contracts; the plan's DRY analysis explicitly justified keeping them inline rather than folding back into `_already_registered("as", ...)`. Confirmed by the static helper's empty **Repeated string literals** section.
- The new `types_for(model)` accessor returns `tuple(self._types.get(model, ()))` — same `tuple(... or ())` pattern shape as the existing helpers; the empty-tuple fallback is the idiomatic "unregistered model" sentinel.
- The new tests' per-test `class ItemType: pass` declarations mirror the existing Slice-0 pattern in `tests/test_registry.py` (no new test-fixture pattern introduced); plan's "Duplication risk avoided" bullet at the plan's DRY analysis correctly predicted this. The 21 new tests reuse the existing `fresh_registry` fixture and the existing `_isolate_global_registry` autouse; no new fixtures added.
- No `_rollback_registration(...)` helper was extracted (the plan rejected it; rollback runs inline). Confirmed: the rollback block at `registry.py:247-257` has exactly one caller and the local snapshot variables are in scope; hoisting it would force a method jump for a single consumer.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` returns empty. `__all__` and the re-export list are unchanged. Slice contract per spec line 656 ("pure registry-internal changes; no `DjangoType` subclass touches the new surface yet") is honored. The new helpers (`primary_for`, `types_for`, `models_with_multiple_types`) are class methods on `TypeRegistry` — reachable via `from django_strawberry_framework.registry import registry` but not re-exported through the package root. Future-slice consumers (Slice 3 / Slice 4) will access them via the registry singleton.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- The new `register()` body at `registry.py:75-135` matches Decision 3's pseudocode line-for-line (reverse-collision guard first, then `setdefault`, then idempotent-re-register flip guard, then duplicate-primary guard, then commit). The symmetric flip guard at `registry.py:117-123` correctly pins both `True→False` and `False→True` directions per the M1 fix — tests 6 and 7 exercise both.
- `register_with_definition()` at `registry.py:224-258` matches Decision 3a's pseudocode. The snapshot-conditional rollback only enters its mutation block when `appended is True` — the `appended is False` path is verified by tests 9 and 9b (pre-existing state untouched).
- `get()` at `registry.py:137-156` matches Decision 4's three-branch shape — primary-first, single-fallback, ambiguous-as-None. Tests 12-15 cover all three branches plus the strict `primary_for` distinction.
- `iter_types()` at `registry.py:172-182` correctly yields one pair per registered type via a nested generator. The existing single-pair test at `tests/test_registry.py:171-183` still passes (one model, one type → one pair); the new test at `tests/test_registry.py:943-955` pins the multi-pair behavior. The test at `tests/test_registry.py:182` (`dict(iter_types())`) would collapse multi-type models silently, but its setup registers one type per model so the assertion shape stays correct.
- 20 of the 20 spec-required tests at spec lines 90-109 are present, plus the optional test 9b corollary. Every Slice 1 branch in the diff has at least one exercising assertion (modulo the Medium finding above).
- `clear()` correctly wipes `_primaries` alongside `_types`, `_models`, `_enums`, `_definitions`, and `_pending`. Pinned by `tests/test_registry.py::test_clear_resets_primaries` (line 969).
- The retired `_already_registered("as", ...)` call path is no longer reachable from `register()` but the helper itself is still used by `register_enum()` at `registry.py:326` — no dead helper to remove.
- No TODO anchors remain in `registry.py`. The other consumer-site TODO anchors (in `types/base.py`, `types/finalizer.py`, `optimizer/walker.py`, `optimizer/extension.py`) correctly stay in place for later slices.
- 50/50 tests in `tests/test_registry.py` pass (focused run `uv run pytest tests/test_registry.py --no-cov -q`). The static helper's control-flow hotspot (61 lines / 7 branch nodes in `register()`) is the natural shape of a multi-guard mutator and stays readable.

### Temp test verification

- `docs/builder/temp-tests/slice-1-registry_multitype/test_rollback_pre_primary_restore.py` — created during review to verify the `register_with_definition` rollback `else:` branch behavior (`self._primaries[model] = pre_primary` when `pre_primary` is set to a pre-existing primary). The temp test passes against the current diff, confirming the implementation is correct.
- Disposition: **promote to permanent** under the Medium finding above. Recommended permanent location: `tests/test_registry.py` after `test_register_with_definition_rollback_clears_primary`, named `test_register_with_definition_rollback_restores_pre_existing_primary`. The temp file is gitignored and will be wiped by the next build's pre-flight cleanup.

### Notes for Worker 1 (spec reconciliation)

- **Expected cross-slice test breakage.** Slice 1 in isolation breaks `tests/types/test_base.py::test_registry_collision_raises_configuration_error` (line 68) — the test asserts that declaring two `DjangoType` subclasses on the same model raises, which Slice 1 retires. The spec at line 22 (M2 fix) and the Slice 2 checklist at spec line 116 explicitly defer this test's rewrite to Slice 2. Not a defect; flagged here so Worker 1's final-verification pass for Slice 1 is not surprised by the failure when running broader test scope. Worker 2 correctly did NOT touch `tests/types/test_base.py` per the spec sequencing (and per the Slice 1 paragraph at spec:656).
- **`scripts/check_spec_glossary.py` whitespace drift in the working tree.** This was already present on disk before Slice 1's build pass; ruff format re-formatted it during the slice's validation run. Worker 1 may want to either stage it with this slice's commit or pull it into a separate commit before merging.
- No spec edits indicated. The plan and the spec are internally consistent for Slice 1.

### Review outcome

`revision-needed` — the slice's spec contract is delivered correctly and the implementation is verified correct via temp test, but the Medium finding (missing permanent pin for the `register_with_definition` rollback `else:` branch) needs Worker 2 to promote the temp test to the permanent suite. The two Low findings (unused `OtherType` / stale comment in `test_register_with_definition_rollback_clears_primary`; pre-existing `scripts/check_spec_glossary.py` ruff drift) are also recorded for the same apply-changes pass — the second is intentionally out-of-scope and Worker 1 will weigh its disposition during final verification. No High findings.

After Worker 2's apply-changes pass lands the permanent rollback-else test and trims the dead `OtherType` declaration, the next Worker 3 re-review should accept cleanly.

---

## Build report (Worker 2, pass 2)

### Files touched

- `tests/test_registry.py` — addressed Worker 3's Medium and Low (1) findings.
  - Medium: added `test_register_with_definition_rollback_restores_pre_existing_primary` immediately after `test_register_with_definition_rollback_clears_primary` to pin the `else: self._primaries[model] = pre_primary` branch in `register_with_definition`'s rollback (`django_strawberry_framework/registry.py:256-257`). Test shape mirrors the temp test at `docs/builder/temp-tests/slice-1-registry_multitype/test_rollback_pre_primary_restore.py`: pre-register `(Item, ItemType, def, primary=True)`, pre-poison `register_definition(AdminItemType, sentinel)`, call `register_with_definition(Item, AdminItemType, object())` without `primary=` so `register()` appends state, expect `ConfigurationError`, then assert `types_for(Item) == (ItemType,)`, `model_for_type(AdminItemType) is None`, and `primary_for(Item) is ItemType` (restored from `pre_primary` via the `else:` branch).
  - Low (1): trimmed the dead `class OtherType: pass` declaration (was at lines 796-797) and rewrote the stale comment block (was at lines 799-802) inside `test_register_with_definition_rollback_clears_primary` to describe what the test actually does ("Pre-poison `register_definition` for ItemType so the second `register_with_definition` call raises after `register` succeeded.").

No edits to `django_strawberry_framework/registry.py` were needed — the implementation already covers the `else:` branch correctly; the only gap was the missing permanent pin, which is now closed.

### Tests added or updated

Added:

- `tests/test_registry.py::test_register_with_definition_rollback_restores_pre_existing_primary` — pins the `else: self._primaries[model] = pre_primary` branch of the rollback in `register_with_definition` so a pre-existing primary survives a failed re-register-with-different-definition for a NEW non-primary type. Placed immediately after the related `test_register_with_definition_rollback_clears_primary` rollback test, matching Worker 3's recommendation.

Updated:

- `tests/test_registry.py::test_register_with_definition_rollback_clears_primary` — removed the unused `class OtherType: pass` declaration and rewrote the misleading comment to describe the actual pre-poisoning approach. No assertion shape changed.

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged); no new format drift introduced by this pass.
- `uv run ruff check --fix .` — exit-1 unchanged from prior pass; failures are pre-existing D301 (module docstring backslashes) and D103 (missing `main` docstring) in `scripts/check_spec_glossary.py`, both confirmed unrelated to Slice 1 in the prior review (see Notes for Worker 1 below).
- `uv run pytest tests/test_registry.py --no-cov -q` — 51 passed in 0.10s (50 retained from pass 1 + 1 new permanent test). Ran with `--no-cov` per BUILD.md "Coverage is the maintainer's gate, not a worker's tool".

### Implementation notes

- **Permanent test placement: immediately after the related rollback test.** Placed the new test directly after `test_register_with_definition_rollback_clears_primary` rather than at the end of the file so the two rollback-branch tests sit side by side. Worker 3's review explicitly suggested this position and it makes the rollback contract surface easy to scan in one block.
- **Test name carries the contract verbatim.** Used `test_register_with_definition_rollback_restores_pre_existing_primary` exactly as Worker 3 recommended in the review section. The "restores_pre_existing_primary" suffix grep-pairs with the implementation's `else: self._primaries[model] = pre_primary` branch.
- **Temp test left in place under `docs/builder/temp-tests/`.** The directory is gitignored and the next build's pre-flight cleanup will wipe it; not Worker 2's job to delete review byproducts.
- **Comment rewrite in `test_register_with_definition_rollback_clears_primary`.** Replaced the misleading three-line comment block with a single-sentence comment that accurately describes the pre-poison approach. Kept the same indentation and idiom (`# Pre-poison ...`) so it matches the surrounding test style.

### Notes for Worker 3

- The Medium finding's permanent pin is now in `tests/test_registry.py` as `test_register_with_definition_rollback_restores_pre_existing_primary`. The assertion shape mirrors the temp test you authored; the only delta is one extra blank line between paragraphs and ruff-formatted indentation. The test passes against the current implementation, confirming the `else:` branch runs.
- The dead `class OtherType: pass` declaration was removed and the stale comment rewritten. The `test_register_with_definition_rollback_clears_primary` body is otherwise unchanged.
- No source files in `django_strawberry_framework/` were touched in this pass — the implementation was already correct; only the test surface needed work.
- Temp test at `docs/builder/temp-tests/slice-1-registry_multitype/test_rollback_pre_primary_restore.py` is left in place; the gitignored directory will be wiped by the next build's pre-flight cleanup.

### Notes for Worker 1 (spec reconciliation)

- **`scripts/check_spec_glossary.py` ruff-format drift — decision: leave as-is for Worker 1 to reconcile.** Per AGENTS.md "Run `uv run ruff format .` after every edit", the formatter touched this file during the slice-1 build pass; reverting it would either require a manual edit (risking another format-drift cycle on the next `ruff format` invocation Worker 1 runs) or skipping the post-edit format step (against the standing rule). Worker 3 explicitly recorded this as out-of-slice-scope and noted Worker 1 will weigh its disposition during final verification, and the safest choice per the prompt is option (b): keep the drift and let Worker 1 reconcile. The diff is whitespace-only on two slice expressions plus one trailing comma — all idiomatic ruff outputs under the project's COM812 / line-length-110 config. No spec edit indicated.
- No new spec gaps surfaced in this apply-changes pass. The implementation was already correct; the only work was promoting the temp test and trimming dead code.

---

## Review (Worker 3, pass 2)

### Helper invocation

Skipped per BUILD.md "Worker 3 helper-run rule per BUILD.md: the helper does NOT need to re-run on a pass-2 review if the only changes are localized test additions/deletions." Pass-2 changes are confined to `tests/test_registry.py` (one added test function + a comment/dead-class cleanup in an existing test) plus a Worker 2 build report append. No source under `django_strawberry_framework/` was touched in this pass, so the 30-lines-of-new-logic trigger is not met.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- The newly added `test_register_with_definition_rollback_restores_pre_existing_primary` reuses the same `fresh_registry` fixture, the same `register_definition`-pre-poison pattern, and the same `pytest.raises(ConfigurationError, match="already has a registered DjangoTypeDefinition")` shape as the sibling `test_register_with_definition_rollback_clears_primary` immediately above it (`tests/test_registry.py:790-808` and `:811-843`). The two tests are intentionally parallel — they pin the two branches of the rollback's `if pre_primary is None: ... else: ...` split at `django_strawberry_framework/registry.py:254-257`. Keeping them side-by-side and shape-aligned is correct DRY here (clear branch-by-branch coverage; no opportunity to consolidate without losing the per-branch assertion clarity).
- No repeated literals introduced. The pre-poison sentinel pattern (`sentinel = object()` followed by `register_definition(...)`) appears in both rollback tests and in the older `test_register_with_definition_rolls_back_register_on_definition_failure` at `tests/test_registry.py:660-683`. The sentinel object is a one-line idiom; hoisting it into a fixture would obscure the per-test pre-state setup.
- The pass-2 comment rewrite in `test_register_with_definition_rollback_clears_primary` (now at `tests/test_registry.py:796-797`) is single-sentence and accurate — no further consolidation opportunity.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` returns empty. `__all__` and the re-export list are unchanged. Slice contract (no new public exports) is honored. No deltas in pass 2 — pass-2 changes are tests-only.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- **Medium finding addressed.** `tests/test_registry.py::test_register_with_definition_rollback_restores_pre_existing_primary` at `tests/test_registry.py:811-843` pins the `else: self._primaries[model] = pre_primary` branch at `django_strawberry_framework/registry.py:256-257`. Walked the control flow against the test setup: pre-existing `_primaries[Item] = ItemType` from the initial `register_with_definition(Item, ItemType, ..., primary=True)` (so `pre_primary` is the pre-existing primary, **not** `None`); `register(Item, AdminItemType)` succeeds and returns `True` (`AdminItemType` is new for the model and no `primary=True` is requested, so the duplicate-primary guard does not fire); the pre-poisoned `register_definition(AdminItemType, ...)` raises; the rollback enters the `if appended:` block; `pre_primary is None` is `False`; the `else` arm executes `self._primaries[Item] = pre_primary` (restoring `ItemType`). The post-failure assertions (`types_for(Item) == (ItemType,)`, `model_for_type(AdminItemType) is None`, `primary_for(Item) is ItemType`) confirm exactly that path. Test passes against the current implementation (`uv run pytest tests/test_registry.py::test_register_with_definition_rollback_restores_pre_existing_primary --no-cov -v` → 1 passed). The two rollback-branch tests now form a complete pair: one pins the `pop` arm (pre-primary was `None`), the other pins the `restore` arm (pre-primary was a class).
- **Low (1) addressed.** The dead `class OtherType: pass` declaration is removed from `test_register_with_definition_rollback_clears_primary` (grep for `OtherType` across `tests/test_registry.py` returns no matches). The previously misleading multi-line comment is rewritten to a single-sentence comment at `tests/test_registry.py:796-797` that accurately describes the actual pre-poison-of-`ItemType` approach. The test body is otherwise unchanged and continues to pin the `pop` arm of the rollback.
- **Low (2) deferral recorded.** Worker 2's pass-2 build report under `### Notes for Worker 1 (spec reconciliation)` at `docs/builder/bld-slice-1-registry_multitype.md:310` explicitly flags the `scripts/check_spec_glossary.py` ruff-format drift for Worker 1's final-verification weigh-in, with the rationale ("ruff-format invariant; reverting would create a format-drift cycle" — accurate against AGENTS.md's "Run `uv run ruff format .` after every edit" rule). Deferral is recorded as instructed; Worker 3 has no further action on this Low.
- Focused-pytest re-run: `uv run pytest tests/test_registry.py --no-cov -q` → 51 passed in 0.06s (50 from pass 1 + 1 new permanent rollback test). The full registry test surface is green.
- No new TODO anchors introduced; no removed anchors regressed. The static helper output from pass 1 (zero repeated string literals, zero remaining TODO comments in `registry.py`) is unchanged because the pass-2 diff is tests-only.

### Temp test verification

- `docs/builder/temp-tests/slice-1-registry_multitype/test_rollback_pre_primary_restore.py` — created in pass 1 to verify the missing rollback `else:` branch. **Disposition: promoted to permanent.** The permanent test landed in this pass at `tests/test_registry.py::test_register_with_definition_rollback_restores_pre_existing_primary` with the assertion shape recommended in pass-1's Medium finding. The temp file remains on disk under the gitignored `docs/builder/temp-tests/` directory; per BUILD.md's "Cleanup and closeout" rules, the maintainer's next build will re-seed the directory empty, so no further action is required from Worker 2 or Worker 3 in this pass.

### Notes for Worker 1 (spec reconciliation)

- **`scripts/check_spec_glossary.py` drift remains pending Worker 1's call.** Pass-2 did not touch the file; Worker 2's recorded reason for leaving it (under `Notes for Worker 1 (spec reconciliation)` at the end of the pass-2 build report) reads cleanly against the standing AGENTS.md "Run `uv run ruff format .` after every edit" rule. Suggestion (non-blocking, Worker 1's discretion): either pull the three-line ruff-format diff into Slice 1's commit (it is cosmetic-only and unrelated to Slice 1's contract) or move it to a separate "ruff-format byproduct" commit so the Slice 1 commit stays focused. Either path is correct; the spec does not have a hook for this and no spec edit is indicated.
- No new spec gaps surfaced in pass 2. The expected cross-slice test breakage in `tests/types/test_base.py::test_registry_collision_raises_configuration_error` flagged in pass 1's notes remains pending Slice 2's rewrite per `spec:116`.

### Review outcome

`review-accepted` — every pass-1 finding is addressed or has a recorded reason. The Medium (rollback `else:` branch missing pin) is now closed by the new permanent test at `tests/test_registry.py:811-843`, which pins the right code path against `django_strawberry_framework/registry.py:256-257`. The Low (1) dead-code-and-stale-comment finding is closed by the cleanup in `test_register_with_definition_rollback_clears_primary`. The Low (2) `scripts/check_spec_glossary.py` drift is intentionally deferred to Worker 1's final verification with a recorded rationale in the pass-2 build report. No new High/Medium/Low findings introduced by the pass-2 changes. 51/51 registry tests pass. Slice 1 is ready for Worker 1's final-verification pass.

---

## Final verification (Worker 1)

### DRY check across this slice and prior accepted slices

No new duplication introduced. There are no prior accepted slices in this build cycle, so the scan is single-slice. Reviewed `django_strawberry_framework/registry.py` end-to-end against the three duplication risks Worker 1 flagged in the planning pass:

- **No duplicated logic between `register` and `register_with_definition`.** `register_with_definition` is a thin snapshot-delegate-rollback wrapper that calls `register` once and handles only the rollback path; the registration logic itself is not re-implemented (`registry.py:224-258`).
- **No near-copies of `ConfigurationError` raises.** The four `ConfigurationError` call sites in the slice are each driven by a distinct contract: two inline raises in `register` for the new Slice-1 messages (`registry.py:120-123` "primary flag cannot be flipped" and `:128-130` "already declared primary as"), one factory call via `_already_registered("against", ...)` at `registry.py:115` (reverse-collision, grep-stable with the existing `tests/test_registry.py:71-87` test), and one factory call via `_already_registered("as", ...)` at `registry.py:326` (untouched enum-collision path). The planning pass already justified keeping the two new Slice-1 messages inline rather than folding them back into `_already_registered` — each fires from exactly one site with distinct phrasing, and a label-based factory call would obscure those contracts. Confirmed during final verification.
- **No repeated literals or messages.** `scripts/review_inspect.py` overview at `docs/builder/shadow/django_strawberry_framework__registry.overview.md` reports `Repeated string literals: None.` end-to-end for the whole file post-Slice-1.

Worker 3's pass-1 helper run already pinned this finding. Re-confirmed against the current working tree.

### Existing tests still pass

- `uv run pytest tests/test_registry.py --no-cov` → `51 passed in 0.07s`. The Slice 1 scope is registry-internal, so the full `tests/test_registry.py` is the right scope for the final-verification pass.
- `uv run pytest tests/types/test_base.py --no-cov` → `1 failed, 44 passed, 1 skipped`. The lone failure is `tests/types/test_base.py::test_registry_collision_raises_configuration_error` at line 68 — the test pins the pre-Slice-1 one-`DjangoType`-per-model contract that this card retires. The failure is expected and explicitly licensed by the spec at line 116 (Slice 2 "Rewrite stale test (M2): `tests/types/test_base.py:68`"). Slice 2 owns the fix; Slice 1 must not touch the test per the spec slice-1 paragraph at `spec:656`. Recorded here so the failure is not mistaken for a Slice 1 regression.
- Did NOT run the package-wide `uv run pytest` — Slice 1 is registry-internal and the deferred test failure above would obscure the gate signal.
- Did NOT pass any `--cov*` flag, per BUILD.md "Coverage is the maintainer's gate, not a worker's tool". `--no-cov` opts OUT of the `pytest.ini` `addopts` auto-`--cov`; that is the only permitted coverage-shaped flag.

### Spec reconciliation

No spec edits required. Worker 2 surfaced no spec gaps in either pass-1 or pass-2 `Notes for Worker 1 (spec reconciliation)`:

- Pass-1 build report: "No structural drift. All seven plan steps landed exactly as specified."
- Pass-2 build report: "No new spec gaps surfaced in this apply-changes pass."

Worker 3's pass-1 review explicitly recorded "No spec edits indicated. The plan and the spec are internally consistent for Slice 1." Re-read the relevant spec sections during final verification (Decision 2, Decision 3, Decision 3a, Decision 4, Decision 5, the Slice 1 checklist at `spec:69-109`, and the Slice 1 paragraph at `spec:652-656`). The shipped implementation matches the spec line-for-line; no gap, conflict, or unstated assumption to reconcile.

### `scripts/check_spec_glossary.py` ruff drift

Decision: **leave it.** Reproduced both legs of the diff against a clean checkout:

- `uv run ruff format scripts/check_spec_glossary.py` reproduces the two slice-whitespace edits (`text[position + len(...):]` → `text[position + len(...) :]` at the two call sites).
- `uv run ruff check --fix scripts/check_spec_glossary.py` reproduces the trailing-comma addition at the `print(...)` call (COM812).

Both invocations are mandated by AGENTS.md "Run `uv run ruff format .` and `uv run ruff check --fix .` after every edit". The drift is therefore defensible cleanup that any worker following the project rules would produce on a fresh checkout; the per-Worker-1-prompt instruction is "leave it" in that case. No revert performed. The drift is included in Slice 1's working-tree diff so the maintainer can either fold it into the Slice 1 commit or pull it into a separate "ruff-format byproduct" commit at commit time — both choices are valid per Worker 3's pass-2 closing note.

### Final status

`final-accepted`.

### Summary

Slice 1 ships the registry's multi-type storage and primary-type tracking infrastructure for spec-014. `TypeRegistry._types` flipped from `dict[Model, Type]` to `dict[Model, list[Type]]` with append-on-register and idempotent same-type re-register; a parallel `_primaries: dict[Model, Type]` map tracks explicitly declared primary types. `register(model, type_cls, *, primary=False) -> bool` returns `True` when state was added and `False` for idempotent no-ops, with a symmetric flip guard that raises `ConfigurationError` whenever the `primary` flag disagrees with the stored state in either direction. A new duplicate-primary guard raises before mutation. `get()` returns the primary if declared, the single registered type if exactly one is registered, or `None` for the multi-type-pending-primary state. `register_with_definition()` snapshots `_primaries[model]` and conditionally rolls back only state added by the current call. Three new public accessors (`primary_for`, `types_for`, `models_with_multiple_types`) land on `TypeRegistry` for Slice 3/4 consumers. `clear()` now wipes `_primaries`. `iter_types()` yields one pair per registered type (multi-type models appear multiple times). 21 new tests in `tests/test_registry.py` pin every branch of the new contract (registration order, idempotence, return-value semantics, primary collision, flip-guard symmetry, rollback both branches, `get()` three-state lookup, `iter_types` expansion, multi-type enumeration); the stale `test_register_collision_raises` was deleted in the same commit. Net: 51 registry tests passing (up from 30). No public surface added beyond the registry helpers. Slice 2 owns the `Meta.primary` recognition that wires `__init_subclass__` to the new keyword.

### Spec changes made (Worker 1 only)

None.
