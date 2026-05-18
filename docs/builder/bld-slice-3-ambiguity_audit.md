# Build: Slice 3 — Cross-type ambiguity audit at finalization

Spec reference: `docs/spec-014-meta_primary-0_0_6.md` (lines 124-135; Decision 5 at lines 479-519; Decision 7 at lines 537-557; spec status header lines 1-7)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - **`finalize_django_types()` host shape.** The audit lands inside `django_strawberry_framework/types/finalizer.py`, the file that already owns the finalize lifecycle. The current `finalize_django_types()` body at `finalizer.py:43-127` is the host — Slice 3 inserts the audit between `finalizer.py:59` (the `is_finalized()` short-circuit ends) and `finalizer.py:70` (the pending-relation collection loop begins). The TODO anchor at `finalizer.py:61-69` already pins the exact insertion site and the pseudocode. Verified post-Slice-1/2 (no shifts in that file).
  - **`ConfigurationError` raise pattern (mirror sibling).** The existing `_format_unresolved_targets_error(unresolved: list[PendingRelation]) -> str` helper at `finalizer.py:20-40` is the exact shape to mirror: build a list of indented `parts` lines from the offender data, then concatenate into a single string passed to `raise ConfigurationError(...)` at the call site (`finalizer.py:85` — `if unresolved: raise ConfigurationError(_format_unresolved_targets_error(unresolved))`). Slice 3's audit follows the same two-step shape: a `_format_ambiguity_error(offenders) -> str` formatter sibling of `_format_unresolved_targets_error`, plus a `raise ConfigurationError(_format_ambiguity_error(offenders))` line inside `audit_primary_ambiguity()`. Co-locating the two formatters at the top of `finalizer.py` matches the docstring convention at `finalizer.py:23-27` ("Sibling convention: `types/base.py:_format_unknown_fields_error` owns the other consumer-surface error strings"). Worker 2 may extend that docstring with one line noting the new ambiguity-error sibling so the formatter pair stays grep-stable.
  - **Registry helpers landed in Slice 1.** `registry.models_with_multiple_types()` (`registry.py:200-206`), `registry.primary_for(model)` (`registry.py:184-191`), and `registry.types_for(model)` (`registry.py:193-198`) are the audit's authority surface. The Slice 1 carry-forward at `docs/builder/worker-memory/worker-1.md:28` is explicit: the audit must call these helpers — never scan `_types` directly, never read `definition.primary`. The Decision 5 pseudocode at `spec:494-512` uses exactly this trio.
  - **Test isolation fixture (`tests/test_registry.py:34-39`).** The autouse `_isolate_global_registry` fixture clears the module-global `registry` on entry/exit. Every new Slice 3 test in `tests/test_registry.py` runs under that fixture without new wiring. The parallel `tests/types/test_definition_order.py:13-18 _isolate_registry` autouse fixture provides the same isolation for tests placed there.
  - **`monkeypatch.setattr` spy pattern.** The existing `test_finalize_is_idempotent` at `tests/test_registry.py:218-237` and `test_finalize_skips_definitions_marked_finalized_when_registry_is_unfinalized` at `tests/test_registry.py:293-320` are the canonical "wrap a registry/finalizer attribute with a counting spy via `monkeypatch.setattr`" shape. The `test_audit_runs_once_per_build` M1 regression test (spec line 135) reuses this exact pattern against `registry.models_with_multiple_types`.

- **New helpers justified.**
  - `audit_primary_ambiguity() -> None` in `types/finalizer.py` — the single new module-level function this slice adds. Single responsibility: walk `registry.models_with_multiple_types()`, collect offenders where `registry.primary_for(model)` is `None`, raise `ConfigurationError` with the actionable fix sentence when the offender list is non-empty. Single caller (`finalize_django_types()`). Justified because (a) the spec at Decision 5 names the helper explicitly (`spec:494`), (b) extracting keeps `finalize_django_types()` body legible (the function is already 85 lines / 15 branches — one of the file's two control-flow hotspots flagged by the inspector), and (c) the helper is the named seam for the M1 monkey-patch spy regression test (spec line 135).
  - `_format_ambiguity_error(offenders) -> str` private helper in `types/finalizer.py` — mirrors `_format_unresolved_targets_error` exactly (line-buildup + concat + return); justified because it (a) keeps `audit_primary_ambiguity()` body small (just call the formatter + raise), (b) makes the canonical error string trivial to test in isolation if Worker 3 wants a focused assertion (e.g., from a temp test), and (c) preserves the sibling-formatter convention documented at `finalizer.py:23-27`.

- **Duplication risk avoided.**
  - **Do not duplicate `models_with_multiple_types()` iteration logic.** A naive implementation could re-derive "models with >= 2 types" from `registry.iter_types()` or by scanning `_types` directly. The Slice 1 helper (`registry.py:200-206`) is the single source of truth; the audit calls it. Decision 8 L3 (`spec:563`) and the Slice 1 worker-memory carry-forward (`worker-1.md:28`) are explicit: "the audit must call `registry.primary_for(model)` … not by scanning `_types` directly."
  - **Do not duplicate the error-format scaffolding.** A naive implementation could inline the `"\n".join(parts)` and `f"  {model.__name__}: {', '.join(...)}"` shape inside `audit_primary_ambiguity()`. The plan's recommendation is the dedicated `_format_ambiguity_error()` formatter sibling — same shape as `_format_unresolved_targets_error` — so the error-string surface stays in one place per finalize-time error and the formatter pair is grep-stable for tests / consumer error matching. Per BUILD.md "Severity definitions" / "DRY violation", multi-site near-copies of the same `"\n".join(f"  {name}: ...")` pattern are exactly the kind of duplication Worker 1 plans against.
  - **Do not duplicate `registry.is_finalized()` short-circuit.** The audit runs INSIDE `finalize_django_types()` AFTER the existing guard at `finalizer.py:58-59`. Do not add a second `if registry.is_finalized(): return` inside `audit_primary_ambiguity()` — the outer guard is the contract (spec line 128 M1 fix; spec L3 fix lines 23, 491). If a future caller invokes the audit directly without going through `finalize_django_types()`, that is a new contract decision, not a defensive-coding addition; do not preemptively design for it.
  - **Two reads of `registry.primary_for(model)` (one per offender candidate) are not duplication.** The audit loop checks `if registry.primary_for(model) is None` for each model in `models_with_multiple_types()`. This is a single iteration with a single per-iteration check, not a duplicated read. Worker 2 should not cache `primary_for` results into a local dict — the lookup is O(1) and the registry is the authority.
  - **`audit_primary_ambiguity()` placement consideration.** The spec (Decision 5 `spec:491`) and the TODO anchor at `finalizer.py:61-69` pin the placement to "inside `finalize_django_types()` after the `is_finalized()` short-circuit and before pending-relation resolution". Worker 2 must place the audit call exactly there; do not move it above the guard (would re-run on every `finalize_django_types()` call — spec L3 fix; the M1 regression test pins this).

### Implementation steps

Line numbers below are pin-at-write-time hints. The TODO anchor at `django_strawberry_framework/types/finalizer.py:61-69` is the authoritative landing site for this slice and must be removed in the same change that replaces it. Re-verify the surrounding line numbers against the current source before editing.

1. **`django_strawberry_framework/types/finalizer.py:20-40` — add `_format_ambiguity_error(offenders)` formatter sibling.** Place the new private helper immediately after the existing `_format_unresolved_targets_error` at lines 20-40, before `finalize_django_types()` at line 43. Mirror the sibling shape exactly:

   ```python
   def _format_ambiguity_error(
       offenders: list[tuple[type[models.Model], tuple[type, ...]]],
   ) -> str:
       """Return the canonical primary-ambiguity error message.

       Sibling of ``_format_unresolved_targets_error`` above; both formatters
       live at the top of this module so the finalize-time error strings stay
       grep-stable for tests and consumer error matching. The fix sentence
       (``Declare Meta.primary = True…``) is the actionable guidance the
       audit's tests pin against (spec lines 127, 133).
       """
       parts = [
           f"  {model.__name__}: {', '.join(t.__name__ for t in types)}"
           for model, types in offenders
       ]
       body = "\n".join(parts)
       return (
           "Models with multiple registered DjangoType subclasses and no primary:\n"
           f"{body}\n\n"
           "Declare Meta.primary = True on exactly one of the registered "
           "DjangoType subclasses."
       )
   ```

   Update the existing `_format_unresolved_targets_error` docstring "Sibling convention" line (currently at `finalizer.py:23-27`) to also name `_format_ambiguity_error` — one line addition, keeps the formatter pair self-referential. Add the matching `from django.db import models` import (currently absent — `finalizer.py` does not import `models` directly; the new type hint `type[models.Model]` requires it). The Decision 5 pseudocode at `spec:495-511` is the source of truth for the formatter shape; copy the string layout verbatim so the test at spec line 133 (`test_finalize_ambiguity_error_message_contains_actionable_fix`) keys on the same substring.

2. **`django_strawberry_framework/types/finalizer.py` — add `audit_primary_ambiguity()` module-level function.** Place immediately after `_format_ambiguity_error` and before `finalize_django_types()`. Body per Decision 5 (`spec:494-511`):

   ```python
   def audit_primary_ambiguity() -> None:
       """Reject models with multiple registered DjangoTypes and no declared primary.

       Walks ``registry.models_with_multiple_types()`` (the Slice 1 helper at
       ``registry.py:200-206``); for each model whose ``registry.primary_for(...)``
       is ``None``, collects the offending registered types via
       ``registry.types_for(model)``. If the offender list is non-empty, raises
       ``ConfigurationError`` with the canonical message built by
       ``_format_ambiguity_error``.

       Runs exactly once per build, inside ``finalize_django_types()`` after the
       ``registry.is_finalized()`` short-circuit and before pending-relation
       resolution (M1 fix per ``docs/spec-014-meta_primary-0_0_6.md:128``).
       """
       offenders: list[tuple[type[models.Model], tuple[type, ...]]] = []
       for model in registry.models_with_multiple_types():
           if registry.primary_for(model) is None:
               offenders.append((model, registry.types_for(model)))
       if not offenders:
           return
       raise ConfigurationError(_format_ambiguity_error(offenders))
   ```

   The function takes no arguments — it reads the module-global `registry` singleton (same shape as `finalize_django_types()` itself). Worker 2 must NOT pass `registry` in as a parameter; the existing convention is process-global singleton access. The function's name is the spec-pinned identifier (`spec:125`); do not rename.

3. **`django_strawberry_framework/types/finalizer.py:58-69` — insert the audit call inside `finalize_django_types()`.** Replace the existing TODO comment block at `finalizer.py:61-69` (9 lines, the Slice 3 anchor with the pseudocode) with a single function call: `audit_primary_ambiguity()`. Concretely:
   - Keep `finalizer.py:58-59` (`if registry.is_finalized(): return`) unchanged.
   - Replace `finalizer.py:61-69` (the TODO block plus the `Pseudo:` body) with the single line `audit_primary_ambiguity()`.
   - The pending-relation resolution loop at `finalizer.py:70+` (currently `unresolved: list[PendingRelation] = []` followed by `for pending in registry.iter_pending_relations():`) stays unchanged.

   Resulting shape of the relevant slice of `finalize_django_types()`:

   ```python
       if registry.is_finalized():
           return

       audit_primary_ambiguity()

       unresolved: list[PendingRelation] = []
       resolved: list[tuple[PendingRelation, type]] = []
       consumer_authored: list[PendingRelation] = []
       for pending in registry.iter_pending_relations():
           ...
   ```

   This placement is the M1-fix contract (spec lines 128, 491): audit runs AFTER the `is_finalized()` guard and BEFORE pending-relation resolution. The L3 contract (spec line 25, second-finalize-call no-op) follows automatically — a second `finalize_django_types()` call hits the `is_finalized()` short-circuit and returns before `audit_primary_ambiguity()` runs. The M1 regression test `test_audit_runs_once_per_build` (step 4d below) pins this.

4. **No source edits outside `django_strawberry_framework/types/finalizer.py`.** Slice 3 does NOT touch `registry.py` (Slice 1 finished it; the helpers it needs already exist), does NOT touch `types/base.py` / `types/definition.py` (Slice 2 finished them; `Meta.primary` already plumbs through to `registry.primary_for`), does NOT touch `types/converters.py` or `optimizer/*.py` (Slice 4 territory), does NOT touch `docs/FEATURES.md` / `CHANGELOG.md` / `KANBAN.md` (Slice 6 territory). Worker 2: stay inside `types/finalizer.py` and the two test hosts.

   After steps 1-3, no `TODO(spec-014-meta_primary-0_0_6.md Slice 3)` anchors remain anywhere in the codebase. The Slice 4 anchors (in `types/base.py:627` and across `optimizer/`) are untouched.

5. **`django_strawberry_framework/types/__init__.py` — public re-export check (no change expected).** The current `types/__init__.py:16-19` re-exports `DjangoType` and `finalize_django_types` only. `audit_primary_ambiguity()` is an internal seam for the M1 monkey-patch test, NOT a new public surface — do NOT add it to `__all__`. Spec Non-goals (`spec:303-310`) and the BUILD.md "Public-surface check" enforce this: Slice 3 ships zero new public exports.

### Test additions / updates

All test work lands in `tests/test_registry.py` and/or `tests/types/test_definition_order.py`. Per spec line 129 and Decision 7 (`spec:543`), both are the existing finalize-test hosts; `tests/types/test_finalizer.py` does NOT exist today and the Slice 3 cluster is comfortably small enough to fit in the existing hosts (six tests at ~10-15 lines each → ~80 added lines split across two files). Worker 1 picks the host per-test based on the closer thematic fit; the breakdown is justified below.

**Test placement decisions (per spec line 129, "Worker 1 picks per-test based on closer thematic fit").**

The six audit tests cluster naturally into three groups. Worker 1's per-test placement decision:

- **`tests/test_registry.py` (idempotency / finalization cluster, currently 1039 lines).** Hosts the three tests whose primary subject is `finalize_django_types()` finalization-lifecycle behavior — error-fired-at-finalize, success-path-at-finalize, regression-on-finalize-internals. The existing `test_finalize_is_idempotent` (`tests/test_registry.py:218-237`), `test_finalize_skips_definitions_marked_finalized_when_registry_is_unfinalized` (`:293-320`), `test_phase_1_failure_is_atomic_and_retryable_after_missing_target_registers` (`:409-436`), and `test_pending_set_is_cleaned_after_success_and_retained_after_phase_1_failure` (`:523-544`) are the existing finalize-lifecycle cluster; the new tests fit alongside them. Specifically:
  - `test_finalize_raises_when_model_has_multiple_types_no_primary` (spec line 130) — sits next to the existing `test_phase_1_failure_is_atomic_*` pattern (raise-at-finalize tests).
  - `test_finalize_ambiguity_error_message_contains_actionable_fix` (spec line 133) — sits next to the same cluster; pins the formatter substring.
  - `test_audit_runs_once_per_build` (M1 regression, spec line 135) — explicitly registry-internal (monkey-patches `registry.models_with_multiple_types`); sits next to `test_finalize_is_idempotent` at `tests/test_registry.py:218-237` which is the canonical "spy on a finalize-time call" pattern. Worker 0 carry-forward at `docs/builder/worker-memory/worker-1.md:28` confirms this placement preference.

- **`tests/types/test_definition_order.py` (post-finalize relation resolution, currently 345 lines).** Hosts the three tests whose primary subject is the audit's interplay with relation resolution and multi-type declarations — i.e. tests that read more naturally as "declare two `DjangoType` subclasses on one model and observe what `finalize_django_types()` does". The existing `test_unresolved_target_raises_with_source_field_and_target` (`tests/types/test_definition_order.py:157-171`) is the closest thematic neighbor (also a finalize-time `ConfigurationError` assertion with a specific message substring). Specifically:
  - `test_finalize_succeeds_when_model_has_multiple_types_one_primary` (spec line 131) — the canonical "happy path" two-types-with-explicit-primary test; the file's existing multi-relation-type tests are the natural neighbors.
  - `test_finalize_succeeds_when_model_has_single_type_no_primary` (spec line 132) — backward-compat path; mirrors the existing `test_reverse_fk_resolves_when_*` shape at `:33-75`.
  - `test_finalize_ambiguity_error_fires_before_unresolved_target_error` (spec line 134) — directly pairs with the existing `test_unresolved_target_raises_with_source_field_and_target` at `:157-171` (it asserts the audit error fires INSTEAD of the unresolved-target error when both conditions hold); placing this assertion adjacent to its complement is the strongest review signal.

Both files have an autouse `registry.clear()` fixture already in place (`tests/test_registry.py:34-39` and `tests/types/test_definition_order.py:13-18`); no new fixture work needed.

**Stale test rewrite check.** Slice 3 does not invalidate any existing test. The closest candidate is `tests/test_registry.py:409-436 test_phase_1_failure_is_atomic_and_retryable_after_missing_target_registers` — but it declares a single `ItemType` for `Item` with no `Category` registered, so the audit walks an empty `models_with_multiple_types()` set, does nothing, and the existing unresolved-target error fires normally. No rewrite.

**New tests (six permanent additions, per spec lines 130-135):**

Each test uses real Django models from the existing fixtures (`Category`, `Item`, etc. from `apps.products.models`) plus plain `DjangoType` subclasses. None of the tests should declare `DjangoType` subclasses module-globally — every subclass is declared inside its test function so the autouse `registry.clear()` fixture isolates them properly (the existing `tests/types/test_definition_order.py` tests follow this exact pattern).

Placement: `tests/test_registry.py` (3 tests). Append at end of file (after `test_models_with_multiple_types_yields_only_models_with_two_or_more` at line 1011).

1. **`test_finalize_raises_when_model_has_multiple_types_no_primary`** (spec line 130, host: `tests/test_registry.py`).
   - Declare two `DjangoType` subclasses on `Item` inside the test function; neither sets `Meta.primary = True`.
   - Call `finalize_django_types()` inside `pytest.raises(ConfigurationError) as exc_info:`.
   - Assert the error message contains: the literal `"Item"` (the offender model name); both class names declared in the test (e.g. `"ItemTypeA"` and `"ItemTypeB"` or whatever Worker 2 picks); and the leading sentence `"Models with multiple registered DjangoType subclasses and no primary"`.
   - The two-class declaration pattern mirrors `tests/test_registry.py:696 test_register_two_types_same_model_without_primary_allows_both_in_types_for`'s shape (Slice 1) but goes through `DjangoType.__init_subclass__` (not bare `register()` calls), so the audit actually fires under the same registry state the Slice 1 test created.

2. **`test_finalize_ambiguity_error_message_contains_actionable_fix`** (spec line 133, host: `tests/test_registry.py`).
   - Same setup as test 1 (two `DjangoType` subclasses on `Item`, neither primary).
   - Assert the error message contains the exact substring `"Declare Meta.primary = True on exactly one of the registered DjangoType subclasses."` — the actionable fix sentence pinned by spec line 127 and the formatter at step 1 above.
   - Worker 2 may fold this assertion into test 1 by adding a third assertion line; if so, Worker 2 must keep both tests as named (the spec lists them as separate items at lines 130 and 133). Recommended: separate test functions for legibility; the spec list at lines 130-135 enumerates six distinct contracts.

3. **`test_audit_runs_once_per_build` (M1 regression)** (spec line 135, host: `tests/test_registry.py`).
   - Use `monkeypatch.setattr` to wrap `registry.models_with_multiple_types` with a counting spy. The existing `test_finalize_is_idempotent` at `tests/test_registry.py:218-237` is the canonical pattern — wrap the attribute with a closure that increments a call-count and delegates to the original.
   - Spy shape (Worker 2 may vary; this is the recommended pattern):

     ```python
     def test_audit_runs_once_per_build(monkeypatch):
         """The ambiguity audit runs exactly once per finalize-cycle build (M1 regression)."""
         calls = []
         original = registry.models_with_multiple_types

         def spy():
             calls.append(None)
             return original()

         monkeypatch.setattr(registry, "models_with_multiple_types", spy)

         class CategoryType(DjangoType):
             class Meta:
                 model = Category
                 fields = ("id", "name")

         finalize_django_types()
         finalize_django_types()  # second call hits is_finalized() guard

         assert len(calls) == 1
     ```

   - The single-`DjangoType` declaration (no offenders) is intentional — the audit's success path must still walk `models_with_multiple_types()` once. The second `finalize_django_types()` call MUST NOT re-invoke the audit (spec line 135: "the spy was invoked exactly once").
   - **Why the spy on `registry.models_with_multiple_types` and not on `audit_primary_ambiguity` directly.** Worker 1's choice: spying on the helper is more robust to implementation rearrangement. If Worker 2 inlines the audit body into `finalize_django_types()` later, the spy still catches the regression because the registry call is the first observable side effect. Spying on `audit_primary_ambiguity` would also work but couples the test to the helper's exact name.
   - **Why no offenders.** The test pins the placement (not the audit's error path). Adding offenders would either (a) require an `try/except` block in the test, complicating the spy assertion, or (b) demand the test pin the error message too — duplicating test 1 / test 2. The success-path spy isolates the placement contract cleanly.

Placement: `tests/types/test_definition_order.py` (3 tests). Append at end of file (after the existing tests).

4. **`test_finalize_succeeds_when_model_has_multiple_types_one_primary`** (spec line 131, host: `tests/types/test_definition_order.py`).
   - Declare two `DjangoType` subclasses on `Item` inside the test: `ItemType` (no `Meta.primary` key — implicit non-primary per Slice 2) and `AdminItemType(Meta.primary=True)`. Worker 2 may pick which is primary; the spec line 122 example puts the primary on the second-declared class, so default to that ordering.
   - Call `finalize_django_types()` outside any `pytest.raises` block.
   - Assert: (a) the call completes without raising; (b) `registry.is_finalized()` is `True`; (c) `registry.primary_for(Item) is AdminItemType` (sanity check that the explicit-primary path is what made the audit succeed).
   - This is the happy-path multi-type test that proves the audit ALLOWS the explicit-primary configuration.

5. **`test_finalize_succeeds_when_model_has_single_type_no_primary`** (spec line 132, host: `tests/types/test_definition_order.py`).
   - Declare exactly one `DjangoType` subclass on `Item` (or any model), no `Meta.primary` key.
   - Call `finalize_django_types()`.
   - Assert: (a) the call completes without raising; (b) `registry.is_finalized()` is `True`; (c) `registry.primary_for(Item) is None`; (d) `registry.get(Item) is ItemType` (the Slice 1 Decision 4 single-type-implicit-primary path).
   - Pins the backward-compat contract: the audit MUST NOT flag single-type-no-primary as an offender. `models_with_multiple_types()` returns an empty iterator for this state, so the audit's `offenders` list stays empty and the function returns without raising.

6. **`test_finalize_ambiguity_error_fires_before_unresolved_target_error`** (spec line 134, host: `tests/types/test_definition_order.py`).
   - Set up BOTH conditions in one test:
     - Two `DjangoType` subclasses on `Item`, neither primary (ambiguity).
     - At least one of them declares a relation to a model that has no registered `DjangoType` (unresolved target). The simplest setup: declare both `ItemType` and `AdminItemType` with `fields = ("id", "name", "category")` — `category` is a forward FK to `Category` and no `CategoryType` is declared. This setup mirrors the existing `tests/types/test_definition_order.py:157-171 test_unresolved_target_raises_with_source_field_and_target` (line 162: `fields = ("id", "name", "category")` and no `CategoryType`).
   - Call `finalize_django_types()` inside `pytest.raises(ConfigurationError) as exc_info:`.
   - Assert the error message is the AMBIGUITY error (contains `"Models with multiple registered DjangoType subclasses and no primary"`), NOT the unresolved-target error (`"Cannot finalize Django types: the following relation targets are unresolved"`).
   - Assert the substring `"no registered DjangoType"` is NOT in the message (the unresolved-target error's distinctive substring at `finalizer.py:32`).
   - Pins the placement contract: the audit runs BEFORE pending-relation resolution (`finalizer.py:70+`), so the ambiguity error wins even when both error conditions are present. Without the audit-before-pending placement, the unresolved-target error would fire first and consumers would chase the wrong root cause.

**Test count summary.** 6 new tests, 3 in each host. No deletes, no renames. `tests/test_registry.py` grows from 1039 → ~1100 lines; `tests/types/test_definition_order.py` grows from 345 → ~430 lines. Both well within comfortable size; no new `tests/types/test_finalizer.py` file is created (spec line 129 L5 fix — "create a new file only if the cluster grows beyond comfortable size in the existing hosts"; six tests at ~10-15 lines each does not push either host past discomfort).

**Temp/scratch tests for Worker 3.** None planned. The audit surface is narrow (one helper + one call site + one formatter). Worker 3 may create temp tests under `docs/builder/temp-tests/slice-3/` if any specific edge case is unclear from the diff — typical candidates would be the empty-offender-list early-return branch (the audit's `if not offenders: return` path at step 2) or the order of offender entries when multiple models hit ambiguity simultaneously. But no temp test is required by the plan; the six permanent tests cover every branch.

### Implementation discretion items

Items where Worker 1 has assessed the design and decided the choice is at Worker 2's discretion. These are stylistic or equivalent-shape preferences, not architectural delegations.

- **Exact line position of `_format_ambiguity_error` definition inside `finalizer.py`.** The plan says "immediately after `_format_unresolved_targets_error` at lines 20-40, before `finalize_django_types()` at line 43". Worker 2 may place either between the two existing siblings or grouped at the top of the formatter block — both read the same. Recommended: directly after `_format_unresolved_targets_error` for visual sibling parity.

- **Exact line position of `audit_primary_ambiguity` definition.** The plan says "after `_format_ambiguity_error` and before `finalize_django_types()`". Functionally, any position above `finalize_django_types()` works (the function is called from inside `finalize_django_types()`). Recommended: directly above `finalize_django_types()` so the call-site reader can scroll up one function to see the audit's definition.

- **Whether `_format_ambiguity_error` accepts `list[tuple[type[models.Model], tuple[type, ...]]]` or a more abstract iterable.** The plan signature uses the explicit `list[tuple[...]]` type to mirror the sibling formatter's `list[PendingRelation]` (the sibling at `finalizer.py:20` accepts a concrete `list`). Worker 2 may relax to `Iterable[tuple[...]]` if the helper is called only with a fresh list (it is); the spec pseudocode at `spec:496` uses `list[tuple[...]]`. Recommended: keep the `list[tuple[...]]` shape for parity.

- **Whether `audit_primary_ambiguity` builds `offenders` via list comprehension or `for`-loop with `append`.** The Decision 5 pseudocode at `spec:497-499` uses a `for`-loop with `append`; a list comprehension `[(model, registry.types_for(model)) for model in registry.models_with_multiple_types() if registry.primary_for(model) is None]` is equivalent. Worker 2 picks whichever reads cleaner under ruff format with line-length 110. Both are acceptable.

- **Whether `test_audit_runs_once_per_build` declares the `DjangoType` subclass before or after the `monkeypatch.setattr` call.** Either order works — `monkeypatch.setattr` only takes effect when the named attribute is read. The recommended order (spy first, then declare type, then finalize) keeps the test readable as "set up the spy, set up the trigger, fire". Worker 2 discretion.

- **Whether tests 1 and 2 share a `setup`-style helper or repeat the two-`DjangoType` declaration.** Each test declares its own classes inside the function body (so the autouse `registry.clear()` fixture isolates them). Folding a helper would couple the two tests' setup; the spec lists them as separate contracts (lines 130 and 133). Recommended: per-test repetition for failure-mode legibility. Worker 2 may extract a small helper if the duplication feels excessive but should not factor across more than these two tests.

These are NOT discretion items — Worker 2 must implement these as specified:

- **`audit_primary_ambiguity()` is the function name.** Spec line 125 pins the identifier; do not rename to `_audit_primary_ambiguity` (the leading-underscore form would conflict with the M1 regression test's monkey-patch path on `registry.models_with_multiple_types` and obscure the spec's named seam).

- **The audit call site is INSIDE `finalize_django_types()` AFTER the `is_finalized()` guard.** Per spec line 128 / Decision 5 M1 fix (`spec:491`). Do not place the audit above the guard (would re-run on every call), do not place after pending-relation resolution (would fire after unresolved-target error), do not extract into a wrapper function called before `finalize_django_types()` (would re-run on every call).

- **Error message starts with `"Models with multiple registered DjangoType subclasses and no primary:"` and ends with the actionable fix sentence `"Declare Meta.primary = True on exactly one of the registered DjangoType subclasses."`.** Per Decision 5 pseudocode (`spec:506-511`) and spec line 127. The tests at spec lines 133, 134 pin these substrings; Worker 2 must not paraphrase.

- **`audit_primary_ambiguity()` is NOT added to `types/__init__.py`'s `__all__`.** Per BUILD.md "Public-surface check" and spec Non-goals at `spec:303-310` — Slice 3 ships zero new public exports.

- **No read of `definition.primary` from this slice's diff.** Decision 8 L3 (`spec:563`) and Slice 1 carry-forward (`worker-1.md:28`) explicit: the audit reads `registry.primary_for(model)` exclusively. Worker 3 must reject any `definition.primary` read introduced by Slice 3.

### Notes for Worker 1 (spec reconciliation)

No conflicts uncovered during planning. The spec's Decision 5 / Decision 7 / Decision 8 are internally consistent for Slice 3 and map cleanly to:

- one new private helper (`_format_ambiguity_error`) mirroring an existing sibling at `finalizer.py:20-40`
- one new module-level function (`audit_primary_ambiguity`) following spec pseudocode at `spec:494-511`
- one call-site insertion inside `finalize_django_types()` replacing the TODO anchor at `finalizer.py:61-69`
- one new import (`from django.db import models` — the type hint requires it)
- six new tests split 3/3 between the two existing finalize-test hosts

The spec status-line re-verification (per `docs/builder/worker-1.md:42-48`) checked spec lines 1-7: status remains accurate (`draft (revision 6, post-TODO-anchor review)`), the predecessors and card line still point at the active surfaces. No edit needed.

The Slice 1 and Slice 2 worker-1 memory carry-forwards explicitly anticipate Slice 3 and pin the right shapes (`worker-1.md:6-7` for `iter_types` semantics and L3 read-site discipline; `worker-1.md:11` for the spec-licensed Slice 2 test rewrite). Both inform this plan and require no spec edit.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/types/finalizer.py` — added `from django.db import models` import; added new private formatter `_format_ambiguity_error(offenders) -> str` directly below the sibling `_format_unresolved_targets_error`; added new module-level `audit_primary_ambiguity() -> None` function; replaced the Slice 3 TODO comment block inside `finalize_django_types()` with a single call to `audit_primary_ambiguity()` (placed after the `is_finalized()` short-circuit and before the pending-relation collection loop, per Decision 5 M1 placement). Updated the sibling-convention paragraph in `_format_unresolved_targets_error`'s docstring to also name `_format_ambiguity_error`.
- `tests/test_registry.py` — appended a Slice 3 banner comment plus 3 new tests (`test_finalize_raises_when_model_has_multiple_types_no_primary`, `test_finalize_ambiguity_error_message_contains_actionable_fix`, `test_audit_runs_once_per_build`).
- `tests/types/test_definition_order.py` — appended a Slice 3 banner comment plus 3 new tests (`test_finalize_succeeds_when_model_has_multiple_types_one_primary`, `test_finalize_succeeds_when_model_has_single_type_no_primary`, `test_finalize_ambiguity_error_fires_before_unresolved_target_error`).

### Tests added or updated

- `tests/test_registry.py::test_finalize_raises_when_model_has_multiple_types_no_primary` — pins that `finalize_django_types()` raises `ConfigurationError` when a model has 2+ registered `DjangoType`s and no `Meta.primary`. Asserts the leading sentence (`"Models with multiple registered DjangoType subclasses and no primary"`), the model name (`"Item"`), and both class names appear in the error string.
- `tests/test_registry.py::test_finalize_ambiguity_error_message_contains_actionable_fix` — pins the exact actionable-fix substring (`"Declare Meta.primary = True on exactly one of the registered DjangoType subclasses."`) per spec line 127.
- `tests/test_registry.py::test_audit_runs_once_per_build` — M1 regression. Wraps `registry.models_with_multiple_types` with a counting spy via `monkeypatch.setattr`; calls `finalize_django_types()` twice (no offenders) and asserts the spy is invoked exactly once, pinning the post-`is_finalized()` placement.
- `tests/types/test_definition_order.py::test_finalize_succeeds_when_model_has_multiple_types_one_primary` — happy-path multi-type test. Declares `ItemType` and `AdminItemType(Meta.primary=True)`; finalize succeeds, `registry.is_finalized() is True`, `registry.primary_for(Item) is AdminItemType`.
- `tests/types/test_definition_order.py::test_finalize_succeeds_when_model_has_single_type_no_primary` — backward-compat. Declares a single `ItemType` (no `Meta.primary`); finalize succeeds, `registry.primary_for(Item) is None`, `registry.get(Item) is ItemType` (the Slice 1 Decision 4 single-type implicit-primary path).
- `tests/types/test_definition_order.py::test_finalize_ambiguity_error_fires_before_unresolved_target_error` — placement contract. Both conditions set up at once (two `DjangoType`s on `Item` neither primary, both reference `category` whose `CategoryType` is unregistered); asserts the ambiguity error wins (its leading sentence is present) and the unresolved-target error does NOT fire (`"Cannot finalize Django types"` and `"no registered DjangoType"` are NOT in the message).

### Validation run

- `uv run ruff format .` — pass (2 files reformatted: `django_strawberry_framework/types/finalizer.py` and `tests/test_registry.py`; the formatter collapsed the `_format_ambiguity_error` list comprehension to one line and consolidated two long-string concatenations in the new tests).
- `uv run ruff check --fix .` — pass on the touched files (`uv run ruff check django_strawberry_framework/types/finalizer.py tests/test_registry.py tests/types/test_definition_order.py` reports `All checks passed!`). The remaining 2 errors (`D301`, `D103` in `scripts/check_spec_glossary.py`) are pre-existing Slice 1 / Slice 2 drift outside the slice scope; left untouched.
- Focused tests: `uv run pytest tests/test_registry.py tests/types/test_definition_order.py --no-cov -q` → 70 passed in 0.14s. No `--cov*` flags used.

### Implementation notes

- **`_format_ambiguity_error` returns the parts as a list comprehension rather than the spec's pseudocode `for`-loop with `append`.** Ruff format collapsed the comprehension to a single line (well within line-length 110); equivalent semantics to the spec pseudocode at `spec:502-505`. The plan's "Implementation discretion items" section explicitly allows this shape.
- **`audit_primary_ambiguity()` builds `offenders` with the `for`-loop / `append` shape from the spec pseudocode (`spec:497-499`).** The function is concise enough that the explicit loop reads slightly clearer than a comprehension when paired with the early-return guard.
- **`_format_unresolved_targets_error` docstring's sibling-convention paragraph extended to also name `_format_ambiguity_error`.** Per the plan ("Worker 2 may extend that docstring with one line noting the new ambiguity-error sibling"). Keeps both formatters self-referential and grep-stable.
- **No public re-export change.** `django_strawberry_framework/types/__init__.py` and `django_strawberry_framework/__init__.py` are untouched. `audit_primary_ambiguity()` stays internal per BUILD.md "Public-surface check" and the spec's Non-goals.
- **Test placement followed the plan's per-test breakdown exactly** — 3 tests in `tests/test_registry.py` (raise-at-finalize cluster + once-per-build M1 regression), 3 tests in `tests/types/test_definition_order.py` (audit-success paths + audit-vs-unresolved ordering test). Both files' existing autouse `registry.clear()` fixtures cover the new tests; no fixture changes.
- **The two "Item with 2 types both selecting `category`" tests in `tests/test_registry.py` (tests 1 and 2) declare `fields = ("id", "name")` only, not `("id", "name", "category")`.** Adding `category` would queue pending relations that the audit's raise would short-circuit anyway — the audit fires before the unresolved-target check — but the simpler shape pins the audit's behavior without leaving incidental pending state hanging in the registry between tests. The 6th test (`test_finalize_ambiguity_error_fires_before_unresolved_target_error` in `test_definition_order.py`) DOES include `category` because pinning the ordering is its sole purpose.

### Notes for Worker 3

- **No shadow file used during build.** `scripts/review_inspect.py` was not invoked; the Slice 3 diff to `finalizer.py` adds 41 source lines (under the 30-line threshold per BUILD.md "When to run the helper during build" applies — Worker 3 should still run the helper for the existing `types/` directory diff per the "touches an existing `.py` file under `optimizer/` or `types/`" rule).
- **Slice 4 TODO anchors are intentionally untouched.** The `types/base.py:627` anchor and the `optimizer/` anchors remain pending Slice 4's H1/H2/H3 fixes; verify by `grep -n "TODO(spec-014-meta_primary-0_0_6.md Slice 4)" django_strawberry_framework/`.
- **The `is_finalized()` guard precedence is preserved.** A second `finalize_django_types()` call short-circuits before `audit_primary_ambiguity()` is called; the spy regression test pins this contract. Worker 3 can re-verify by reading `finalize_django_types()` lines 107-110 in the post-edit `finalizer.py`.
- **Pre-existing `scripts/check_spec_glossary.py` ruff errors (`D301`, `D103`) are out-of-scope drift from Slice 1.** Recorded in the Slice 1 worker-2 memory entry. Not touched by this slice.

### Notes for Worker 1 (spec reconciliation)

No spec gaps, conflicts, or unstated assumptions surfaced during implementation. The plan was followed step-by-step; every Decision-5 contract maps cleanly to the diff. No spec edit required for Slice 3.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

#### Sibling-formatter near-duplication, sub-load-bearing

The two formatters `_format_unresolved_targets_error` (`django_strawberry_framework/types/finalizer.py:21-42`) and `_format_ambiguity_error` (`django_strawberry_framework/types/finalizer.py:45-63`) share the same envelope shape (`<header>\n + body + \n\n + <footer>` with `body = "\n".join(parts)`). The per-line items and the three text segments (header, per-item, footer) all differ, so the only mechanical overlap is the `\n.join + concat-with-blank-line` envelope. A factored helper `_format_finalize_error(header, lines, footer) -> str` would deduplicate that envelope but require each caller to still build its own per-line list and pass three string arguments — net savings ~3-4 lines per caller in exchange for an extra indirection.

```django_strawberry_framework/types/finalizer.py:30-42
    lines = []
    for pending in unresolved:
        lines.append(
            f"  - {pending.source_model.__name__}.{pending.field_name} -> "
            f"{pending.related_model.__name__} (no registered DjangoType)",
        )
    body = "\n".join(lines)
    return (
        "Cannot finalize Django types: the following relation targets are unresolved.\n"
        f"{body}\n\n"
        "Declare a DjangoType for each unresolved target model, or exclude these "
        "relation fields via Meta.exclude / Meta.fields."
    )
```

```django_strawberry_framework/types/finalizer.py:56-63
    parts = [f"  {model.__name__}: {', '.join(t.__name__ for t in types)}" for model, types in offenders]
    body = "\n".join(parts)
    return (
        "Models with multiple registered DjangoType subclasses and no primary:\n"
        f"{body}\n\n"
        "Declare Meta.primary = True on exactly one of the registered "
        "DjangoType subclasses."
    )
```

Recommendation: keep as-is. The "sibling formatters at the top of the module" convention is already documented in both docstrings; the two functions are short, explicit, and read cleanly side-by-side. The DRY analysis in the plan considered the consolidation explicitly. Surfacing as Low so Worker 1 can weigh during the integration pass if any future slice adds a third formatter to the same site (at three formatters the envelope helper starts paying off). Test expectation: none.

### DRY findings

- The pair of `_format_*_error` formatters in `types/finalizer.py` share an envelope shape but not item shape. Already analyzed in the plan; recorded above under Low. Inspector reports `Repeated string literals: None` for the finalizer file, confirming no hard duplication landed.
- The Slice 3 audit calls `registry.primary_for(model)` and `registry.types_for(model)` directly per Decision 8 L3 (`spec:563`) and Slice 1 worker-1 carry-forward (no read of `_types` or `definition.primary`). Grep across `django_strawberry_framework/` confirms no `definition.primary` reads landed in this slice. Spec L3 contract upheld.
- The new tests reuse the existing autouse `_isolate_global_registry` (`tests/test_registry.py:34-39`) and `_isolate_registry` (`tests/types/test_definition_order.py:13-18`) fixtures; no fixture duplication. The spy pattern in `test_audit_runs_once_per_build` (`tests/test_registry.py:1095-1120`) mirrors the canonical shape from `test_finalize_is_idempotent` (`tests/test_registry.py:218-237`) — same intent, different attribute under spy.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py django_strawberry_framework/types/__init__.py` returns nothing. `__all__` in both files is unchanged. `audit_primary_ambiguity()`, `_format_ambiguity_error()`, and the new `from django.db import models` import all stay internal to `types/finalizer.py`. Slice 3 ships zero new public exports per the plan, BUILD.md "Public-surface check", and the spec's Non-goals.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- **Audit placement matches Decision 5 M1 fix exactly.** `finalize_django_types()` body at `django_strawberry_framework/types/finalizer.py:104-107` shows `if registry.is_finalized(): return` → blank line → `audit_primary_ambiguity()` → blank line → pending-relation resolution at line 109. The spec contract at lines 128 and 491 is upheld character-for-character: audit fires AFTER the `is_finalized()` short-circuit and BEFORE pending-relation resolution.
- **Audit-runs-once-per-build pinned by the spy test.** `tests/test_registry.py:1095-1120` wraps `registry.models_with_multiple_types` with a counting spy via `monkeypatch.setattr`, calls `finalize_django_types()` twice (single-`CategoryType` declared, no offenders), and asserts the spy was invoked exactly once. If Worker 2 had placed the audit ABOVE the `is_finalized()` guard, the spy would have been called twice; the test would fail with `assert 2 == 1`. The placement contract is enforceable.
- **Error message shape covers every spec line 484 requirement.** `test_finalize_raises_when_model_has_multiple_types_no_primary` (`tests/test_registry.py:1051-1071`) asserts the error contains the model name (`"Item"`), every registered class name (`"ItemTypeA"`, `"ItemTypeB"`), and the leading sentence. `test_finalize_ambiguity_error_message_contains_actionable_fix` (`:1074-1092`) asserts the verbatim actionable fix sentence (`"Declare Meta.primary = True on exactly one of the registered DjangoType subclasses."`). Two complementary tests, no overlap waste.
- **Audit-before-unresolved-target ordering pinned by `test_finalize_ambiguity_error_fires_before_unresolved_target_error`** (`tests/types/test_definition_order.py:391-415`). Sets up both error conditions (two `DjangoType`s on `Item` neither primary, both selecting `category` whose `CategoryType` is unregistered) and asserts (a) the ambiguity error fires, (b) the unresolved-target error's distinctive substring `"Cannot finalize Django types"` is NOT in the message, (c) `"no registered DjangoType"` is also NOT present. Pins the spec line 487 ordering contract by negative assertion as well as positive.
- **All six spec-required tests (lines 130-135) present in the planned 3/3 split.** Three audit-failure / regression tests in `tests/test_registry.py` (lines 1051, 1074, 1095) sit next to the existing finalize-lifecycle cluster (`test_finalize_is_idempotent`, etc.). Three audit-success / ordering tests in `tests/types/test_definition_order.py` (lines 356, 376, 391) sit next to the existing post-finalize relation-resolution cluster. Placement matches the spec line 129 / Decision 7 L5 guidance and the plan's per-test thematic-fit reasoning. No new `tests/types/test_finalizer.py` file created (the cluster fits comfortably in existing hosts).
- **Both `if not offenders: return` AND `if registry.primary_for(model) is None` branches are exercised.** The early-return branch fires in `test_audit_runs_once_per_build` (single `CategoryType`, no offenders), `test_finalize_succeeds_when_model_has_multiple_types_one_primary` (multi-type with primary set, loop runs but appends nothing), and `test_finalize_succeeds_when_model_has_single_type_no_primary` (single type, loop yields nothing). The `primary_for(model) is None` true branch fires in the two raise-at-finalize tests; the false branch fires in `test_finalize_succeeds_when_model_has_multiple_types_one_primary` (where `AdminItemType` is primary, so `models_with_multiple_types` yields `Item` but `primary_for(Item) is AdminItemType` so the offender is skipped). Both arms of the conditional are pinned.
- **`from django.db import models` import is actually used.** The new import lands at `django_strawberry_framework/types/finalizer.py:6`. It is consumed by the `type[models.Model]` type hint in `_format_ambiguity_error` (`:46`) and in `audit_primary_ambiguity` (`:80`). The static inspector's Imports section lists it as a Django import; the Symbols and signatures confirm both consumption sites. Not a dead import.
- **No drift in `audit_primary_ambiguity` signature or name.** Spec line 125 pins the identifier `audit_primary_ambiguity` (not `_audit_primary_ambiguity`); the implementation respects that and lives at module scope so the M1 spy test can target it directly if a future test prefers that target over `models_with_multiple_types`.
- **Sibling-formatter docstring updated to be self-referential.** `_format_unresolved_targets_error`'s docstring at `:24-28` was updated to also name `_format_ambiguity_error`, keeping the formatter pair grep-stable as planned. Small but exactly the maintenance-friendly touch the plan asked for.
- **TODO anchor for Slice 3 fully removed from `types/finalizer.py`.** `grep -n "TODO(spec-014-meta_primary-0_0_6.md Slice 3)" django_strawberry_framework/` returns no matches; only the Slice 4 anchors in `types/base.py:627` and across `optimizer/` remain pending. No anchor leaks.
- **Validation pass clean.** Worker 2's `uv run ruff format .` and `uv run ruff check` reported clean for the touched files; the pre-existing `scripts/check_spec_glossary.py` ruff drift is out-of-scope from Slice 1 and noted as such. The focused-test run (`uv run pytest tests/test_registry.py tests/types/test_definition_order.py --no-cov -q`) passes 70/70 — reproduced during this review.

### Temp test verification

- No temp tests created. The diff's branch surface is narrow (audit's two conditional branches, the inner-loop append, the early-return) and is fully exercised by the six permanent tests as documented above. The plan's discretion section flagged temp tests as optional ("none planned"); no review-pass concern motivated a temp test.

### Notes for Worker 1 (spec reconciliation)

No spec edit needed. The implementation matches Decision 5 (`spec:479-519`), Decision 7 (`spec:537-557`), Decision 8 L3 (`spec:563`), and the Edge cases section's `finalize_django_types` idempotency note (`spec:699`) line-for-line. The Low DRY finding above is a Worker-1 watch-item for the integration pass (only matters if a third formatter joins `types/finalizer.py`); it is not a defect.

The static inspector's "Repeated string literals: None" output on `types/finalizer.py` is the strongest cross-slice signal that this slice did not introduce hidden duplication. Worker 1 may carry forward that helper-run datum to the integration pass.

### Review outcome

`review-accepted` — every spec-required behavior (Decision 5 placement, Decision 5 message shape, Decision 5 ordering, audit-runs-once-per-build, six tests per spec lines 130-135, no public exports, no `definition.primary` read) is pinned by the diff and the tests. The single Low finding is recorded but does not block the slice; it is a sibling-formatter consolidation candidate that Worker 1 weighs at integration. Setting artifact `Status:` line to `review-accepted`.

---

## Final verification (Worker 1)

- **DRY check across this slice and prior accepted slices: no new duplication.**
  - **Sibling-formatter near-duplication (Worker 3 Low finding).** The two formatters `_format_unresolved_targets_error` (`django_strawberry_framework/types/finalizer.py:21-42`) and `_format_ambiguity_error` (`django_strawberry_framework/types/finalizer.py:45-63`) share a `<header>\n + body + \n\n + <footer>` envelope with `body = "\n".join(parts)`. The per-item shape diverges materially: `_format_unresolved_targets_error` walks `list[PendingRelation]` and emits hyphen-bullet `f"  - {source_model}.{field_name} -> {related_model} (no registered DjangoType)"` lines via a `for`-loop / `append`; `_format_ambiguity_error` walks `list[tuple[Model, tuple[type, ...]]]` and emits comma-separated-types `f"  {model.__name__}: {', '.join(...)}"` lines via a list comprehension. The header strings, footer strings, and item-builder shapes all differ — only the three-piece envelope is mechanically shared. **Decision: leave as separate sibling formatters.** A factored `_format_finalize_error(header, lines, footer) -> str` would save ~3-4 lines per caller but require each caller to still build its own per-line list and pass three string arguments — net wash at N=2 formatters. The Low finding's own recommendation is "keep as-is" and explicitly names a third formatter as the trigger condition for revisiting. The plan's DRY analysis (`bld-slice-3-ambiguity_audit.md` "Duplication risk avoided" bullet 2) considered the consolidation and rejected it for the same reason. Per the verification prompt's "Pick the smaller move" guidance, the consolidation is deferred to the cross-slice integration pass — `docs/builder/bld-integration.md` will re-check whether any Slice 4-6 follow-up introduces a third formatter at this site; if so, the integration pass spawns the consolidation cycle then. No source edit required for Slice 3.
  - **No other duplication detected.** The Slice 3 audit calls `registry.primary_for(model)` and `registry.types_for(model)` directly per Decision 8 L3 and the Slice 1 carry-forward — no read of `_types` or `definition.primary`. The static inspector's "Repeated string literals: None" on `types/finalizer.py` (recorded in Worker 3's review) confirms no string-literal duplication landed. The new tests reuse the existing autouse `_isolate_global_registry` / `_isolate_registry` fixtures with no fixture duplication. The spy pattern in `test_audit_runs_once_per_build` mirrors the canonical `test_finalize_is_idempotent` shape — same intent, different attribute under spy — which is a deliberate reuse, not duplication.
  - **No Slice 1 / Slice 2 surface drift.** The audit reads the Slice 1 helper trio (`models_with_multiple_types`, `primary_for`, `types_for`) unchanged; nothing in Slice 3 modifies `registry.py`, `types/base.py`, or `types/definition.py`. The Slice 4 TODO anchors at `types/base.py:627` and across `optimizer/` are untouched (verified by `grep -n "TODO(spec-014-meta_primary-0_0_6.md Slice 4)"`).

- **Existing tests still pass.** Ran `uv run pytest tests/test_registry.py tests/types/test_definition_order.py tests/types/test_base.py --no-cov` → **128 passed, 1 skipped in 0.12s**. The Slice 1 (`test_registry.py`) + Slice 2 (`test_base.py`) suites pass alongside the new Slice 3 tests (3 in `test_registry.py`, 3 in `test_definition_order.py`). No `--cov*` flags used. The single skip is `tests/types/test_base.py::test_consumer_annotation_overrides_synthesized`, which is pre-existing (out of Slice 3 scope; relates to Slice 4's H1 consumer-authored fields path).

- **Spec reconciliation: no spec edits required.** Walked Decision 5 (`spec:479-519`), the Slice 3 paragraph (`spec:124-135`), Decision 7 test-host guidance (`spec:537-557`), and Decision 8 L3 (`spec:563`). Each contract maps cleanly to the diff:
  - Decision 5 pseudocode (`spec:494-511`) → `audit_primary_ambiguity()` body at `finalizer.py:66-86` mirrors it line-for-line; only stylistic discretion-allowed differences (the spec's combined `parts + "\n".join(...)` concat is split into `_format_ambiguity_error` per the plan's sibling-formatter convention, which is the cleaner DRY shape and is allowed by the plan's "Implementation discretion items").
  - Decision 5 M1 placement (`spec:128, 491`) → audit call lands at `finalizer.py:107`, between `is_finalized()` short-circuit (`:104-105`) and pending-relation loop (`:109+`). Test `test_audit_runs_once_per_build` (`tests/test_registry.py:1095`) pins this with a counting spy.
  - Decision 5 ordering contract (`spec:487`) → `test_finalize_ambiguity_error_fires_before_unresolved_target_error` (`tests/types/test_definition_order.py:391`) sets both error conditions and asserts the ambiguity error wins by both positive (leading-sentence present) and negative (unresolved-target substrings absent) assertion.
  - Decision 7 test-host guidance (`spec:537-557`) → 3 audit-failure / regression tests in `tests/test_registry.py`; 3 audit-success / ordering tests in `tests/types/test_definition_order.py`. No new `tests/types/test_finalizer.py` file (L5 fix respected).
  - Decision 8 L3 (`spec:563`) → audit reads `registry.primary_for(model)` exclusively; `grep -n "definition.primary" django_strawberry_framework/types/finalizer.py` confirms zero reads of `definition.primary` in Slice 3's diff.
  - Worker 2's "Notes for Worker 1 (spec reconciliation)" reported "No spec edits required" and Worker 3's "Notes for Worker 1" reported "No spec edit needed" — both sanity-checked against the diff and the spec. Concur.
  - Spec status-line re-verification (per `docs/builder/worker-1.md:42-48`) checked `spec:1-7`: `Status: draft (revision 6, post-TODO-anchor review)` is current, predecessors / card line unchanged. No edit needed.

- **Final status: `final-accepted`.**

### Summary

Slice 3 shipped the cross-type ambiguity audit at finalization. Added one private formatter `_format_ambiguity_error` and one module-level `audit_primary_ambiguity()` function in `django_strawberry_framework/types/finalizer.py`, called inside `finalize_django_types()` after the `is_finalized()` short-circuit and before pending-relation resolution. Added `from django.db import models` import to support the new type hint. Removed the Slice 3 TODO anchor block from `finalize_django_types()`. Added six new tests pinning Decision 5's contracts: 3 in `tests/test_registry.py` (raise-at-finalize + formatter substring + M1 audit-runs-once-per-build regression via `monkeypatch.setattr` spy), 3 in `tests/types/test_definition_order.py` (multi-type success with declared primary + single-type backward-compat success + ambiguity-fires-before-unresolved-target ordering). No public-surface change (`audit_primary_ambiguity` stays internal). 128 passed / 1 skipped in `tests/test_registry.py` + `tests/types/test_definition_order.py` + `tests/types/test_base.py` after the slice landed.

### Spec changes made (Worker 1 only)

None.
