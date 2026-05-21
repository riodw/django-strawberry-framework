# Build: Slice 2 — Validation

Spec reference: `docs/spec-016-list_field-0_0_7.md` (lines 134-138, Slice 2 checklist bullets; Decision 5 — Validation & error shapes at spec lines 542-566; Test plan validation cluster at spec lines 728-735; rev3 M3 anchor at spec line 548 pinning the `__django_strawberry_definition__` assignment site at `django_strawberry_framework/types/base.py:245`)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - `ConfigurationError` — `django_strawberry_framework/exceptions.py:24-34`. This is the single error class Decision 5 names; every validation site in the package raises it (registry collisions, unknown `Meta` keys, optimizer-hint validation, the new `Meta.interfaces` / `Meta.primary` guards shipped in 0.0.5 / 0.0.6, the rev6 `id`-on-Relay-Node guards at `types/base.py:192-213`). Slice 2 imports the class from `django_strawberry_framework.exceptions` — NOT from `django_strawberry_framework` (the top-level `__init__.py:28-37` `__all__` deliberately does NOT re-export it; consumers and tests reach into `.exceptions`). Slice 1 deferred this import to avoid F401; Slice 2 lands it.
  - `DjangoType` — `django_strawberry_framework/types/base.py:140` (defined) / `django_strawberry_framework/types/__init__.py:25,28` (re-exported as `from .base import DjangoType` + `__all__ = ("DjangoType", "finalize_django_types")`) / `django_strawberry_framework/__init__.py:24` (top-level public surface). Slice 2 needs `issubclass(arg, DjangoType)` per spec line 547. Pick the import path that avoids the top-level `django_strawberry_framework` package (which imports `list_field.py` itself, so importing back through `django_strawberry_framework` from inside `list_field.py` is a self-import). The canonical sibling import is `from django_strawberry_framework.types import DjangoType` (parallels existing intra-package imports such as the `from .types.relay import _apply_get_queryset_async, _apply_get_queryset_sync` already at `list_field.py:18`).
  - `__django_strawberry_definition__` discriminator — `django_strawberry_framework/types/base.py:245` (`cls.__django_strawberry_definition__ = definition`). Verified at HEAD via `grep -n "__django_strawberry_definition__" django_strawberry_framework/types/base.py`; spec line 548 (rev3 M3) cites the same line. The assignment is **inside** the `if meta is None: return` early-out at `types/base.py:156-158`, so abstract `DjangoType` bases without a `Meta` pass through `__init_subclass__` WITHOUT the attribute landing. `hasattr(arg, "__django_strawberry_definition__")` is therefore a sufficient discriminator for "registered concrete `DjangoType`" vs "abstract `DjangoType` base or `DjangoType` itself" — the same reasoning the spec uses.
  - Error-message shape — spec line 555 pins the pattern as `<Symbol> <constraint>; got <repr>.` The shape pattern is **stylistic** (single-line, leading symbol name, trailing semicolon + `got <repr>.`). The spec's parenthetical at line 555 names `types/base.py:_format_unknown_fields_error` as the "style" anchor, NOT as a function to literally call — `_format_unknown_fields_error` at `django_strawberry_framework/types/base.py:395-403` returns `f"{model.__name__}.Meta.{attr} names unknown fields: ..."` which is **shape-pattern adjacent** (named symbol, named constraint, single-line) but signature-incompatible with `DjangoListField`'s validation needs (the helper requires a model class and a Meta-attribute name; `DjangoListField` is not validating a Meta key). The right move is to write inline `f"..."` strings following the same single-line `<Symbol> <constraint>; got <repr>.` cadence; Decision 5 itself (spec lines 546-549) pins the four exact-text strings.
  - `inspect.isclass(...)` — `inspect` is already imported in `list_field.py:9` (used by `inspect.iscoroutinefunction(user_resolver)` in the consumer-resolver wrapper branch). No new import.

- **New helpers justified.** None. Decision 5 (spec lines 542-566) describes three narrow inline checks (class-ness + `issubclass` + `__django_strawberry_definition__` for `target_type`, plus `callable(resolver)` for the keyword-only `resolver=`); each is a one-liner raise. Extracting `_validate_target_type(...)` / `_validate_resolver(...)` module-scope helpers is the obvious DRY candidate, but spec lines 557-561 explicitly justify keeping the validation **at the constructor site** ("Failing at the construction site means the error appears at the line that wrote `DjangoListField(...)`, which is easier to debug than a delayed `finalize_django_types()` error. Symmetric with how `OptimizerHint`-related Meta validation fires at type creation today."). The four raise sites are tightly co-located inside the factory's first few lines; extracting them would burn a line + an extra frame in the traceback without recouping any duplication (the four sites do not share enough body to warrant a helper). Worker 2 may, at their discretion, extract a single `_validate_target_type(target_type)` helper if the three target-type checks read cleaner as one named call — see Implementation discretion items — but the spec leans toward inline.

- **Duplication risk avoided.** Two near-copies a naive implementation could introduce:
  1. **Re-implementing `_format_unknown_fields_error`'s style at the new sites.** The spec is clear that the SHAPE PATTERN (single-line `<Symbol> <constraint>; got <repr>.`) is what's reused, not the function. The plan pins the exact error-message strings from Decision 5 (spec lines 546, 547, 548, 549) verbatim so Worker 2 cannot drift the wording. If a future slice grows a fifth Meta-validator site that needs the SAME-shape error against a different symbol, that's the moment a shared helper becomes justified; not now.
  2. **Re-checking the `__django_strawberry_definition__` discriminator differently from `types/base.py:245`'s assignment site.** Two near-shapes are equivalent at the consumer level today: `hasattr(arg, "__django_strawberry_definition__")` (used by spec Decision 5) vs `getattr(arg, "__django_strawberry_definition__", None) is not None` (used by `types/base.py:279` to detect a registered subclass). Both work for now; `hasattr` is simpler and matches spec line 548 verbatim. Worker 2 MUST use `hasattr` (not `getattr ... is not None`) to keep the discriminator wording identical to the spec, preventing a future grep-divergence.

### Implementation steps

Line numbers below are pin-at-write-time navigational hints; verify against the current source before editing — Slice 1 has shipped, so all line numbers below reference the HEAD state after Slice 1's final-accepted diff.

1. **Add `ConfigurationError` and `DjangoType` imports to the top of `list_field.py`.** Insert after the existing `from .types.relay import ...` import at `django_strawberry_framework/list_field.py:18`, in alphabetical order within the first-party import group:

   ```python
   from .exceptions import ConfigurationError
   from .types import DjangoType
   ```

   Both imports are first-party and use relative paths consistent with the existing `from .types.relay import ...` line. Confirm no circular import: `django_strawberry_framework/exceptions.py` has zero internal imports (`exceptions.py:1-12` docstring affirms "Lives at the bottom of the import graph — no Django, no Strawberry, no internal package imports — so the exception hierarchy can be raised from anywhere without circulars"); `django_strawberry_framework/types/__init__.py` imports only from `.base` and `.finalizer`, neither of which imports `list_field` (verified via `grep -rn "from.*list_field" django_strawberry_framework/`). The top-level `django_strawberry_framework/__init__.py:20` imports `list_field` BEFORE `optimizer` / `types`, but `list_field`'s own imports of `.exceptions` and `.types` resolve directly to those submodules without round-tripping through the top-level package.

   Spec citation: spec lines 134-137 (Slice 2 checklist bullets); Slice 1 worker-1 memory carry-forward ("Slice 1 defers `ConfigurationError` import to Slice 2 (avoids unused-import lint)").

2. **At the top of `def DjangoListField(target_type, *, resolver=None, ...):` body — currently `list_field.py:52-66`, immediately INSIDE the function but BEFORE the async-detection-asymmetry comment block at `list_field.py:58-65` and the `if resolver is None:` dispatch at line 66** — insert the four validation guards Decision 5 lists. Pin the exact `ConfigurationError` message strings verbatim from spec lines 546-549:

   ```python
   if not inspect.isclass(target_type):
       raise ConfigurationError(
           f"DjangoListField requires a DjangoType class; got {target_type!r}.",
       )
       # Spec line 546 — uses ``{target_type!r}`` (the `<repr>` placeholder).
   if not issubclass(target_type, DjangoType):
       raise ConfigurationError(
           f"DjangoListField requires a DjangoType subclass; got {target_type.__name__}.",
       )
       # Spec line 547 — uses ``{target_type.__name__}`` (the `<name>` placeholder).
   if not hasattr(target_type, "__django_strawberry_definition__"):
       raise ConfigurationError(
           f"DjangoListField target {target_type.__name__} is not a registered DjangoType "
           f"(no __django_strawberry_definition__). This usually means {target_type.__name__}'s "
           "`Meta` is missing a `model` declaration.",
       )
       # Spec line 548 — uses ``{target_type.__name__}`` twice (the two `<name>` placeholders).
   if resolver is not None and not callable(resolver):
       raise ConfigurationError("DjangoListField resolver must be callable.")
       # Spec line 549 — no placeholder.
   ```

   **Pin the ordering** of the three target-type checks as: class-ness FIRST (`inspect.isclass`), then `issubclass(target_type, DjangoType)`, then `hasattr(..., "__django_strawberry_definition__")`. Rationale: each subsequent check assumes the prior one passed (`issubclass` requires its first argument to be a class; `hasattr` is safe on non-classes but the spec's error message for the registered-check assumes `target_type.__name__` exists, which is class-only). The `callable(resolver)` check is independent and runs LAST so it fires only when `target_type` already passed all three guards.

   The four guards land BEFORE the existing async-detection-asymmetry comment (currently `list_field.py:58-65`) because the comment annotates the `if resolver is None: / else:` dispatch immediately below it; running validations before that dispatch keeps the comment co-located with the code it documents.

   Spec citations: spec lines 542-549 (Decision 5 enumerated rules), spec line 555 (error-shape pattern), spec line 548 (`types/base.py:245` discriminator anchor — verified at HEAD).

3. **Verify the line-anchor citation in the artifact's comment is still accurate.** Run `grep -n "__django_strawberry_definition__" django_strawberry_framework/types/base.py` and confirm the `cls.__django_strawberry_definition__ = definition` assignment is still at line 245 (or update the in-source pseudo-comment if Slice 1's diff shifted it). Pre-flight grep result during this planning pass: `245:        cls.__django_strawberry_definition__ = definition` — matches the spec citation at line 548 exactly.

   Spec citation: spec line 548 (rev3 M3 anchor).

4. **Do NOT modify** `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, the `__all__` tuple in `list_field.py:20`, the two `_post_process_consumer_*` helpers at `list_field.py:29-42`, or the resolver-dispatch logic at `list_field.py:66-102`. Slice 2 adds validation **only**; the existing surface and behavior are unchanged.

### Test additions / updates

`tests/test_list_field.py` already exists as a scaffold from Slice 1 (Slice 1 created the file with module docstring + TODO comments at `tests/test_list_field.py:1-195`; the file currently collects ZERO tests and is import-clean per its docstring lines 19-29). Slice 2 replaces the four `# TODO(spec-016, Slice 2):` blocks at lines 56-78 with real test bodies.

Add a `from django_strawberry_framework import DjangoListField, DjangoType` plus `from django_strawberry_framework.exceptions import ConfigurationError` import block at the top of the file (the placeholder import TODO at lines 32-44 already specifies this exact shape; Slice 2 replaces it with the real imports). Also add `import pytest`.

Pin one test function per Decision 5 check. Function names are flat module-level `test_*` callables (rev5 H3 carry-forward + spec line 730-733 — the spec uses `test_djangolistfield_rejects_*` naming, and the scaffold's TODO blocks at lines 56-78 already pin these names verbatim). Slice 3 will add its own flat module-level `test_djangolistfield_*` behavior callables alongside; using flat functions (not a `class TestListField` wrapper) keeps the door open for Slice 3 to extend without nesting collisions.

Pinned tests (verbatim names from spec lines 730-733 + scaffold lines 56-78):

1. `test_djangolistfield_rejects_non_class_argument` (spec line 730, scaffold line 57)
   - Passing values that are NOT classes: an instance string (`"BranchType"`), an int (`42`), a `DjangoType` *instance* (instantiated, not the class), and `None`. Each call raises `ConfigurationError`.
   - Assertion shape: `with pytest.raises(ConfigurationError, match=r"DjangoListField requires a DjangoType class; got"):` — the `match=` regex pins the leading prefix from spec line 546 but stops before `<repr>` (the repr changes per call; the leading-prefix pin protects the symbol name and the `requires a DjangoType class` constraint phrase).
   - The four parametrized inputs cover the four common non-class shapes a consumer might accidentally pass.

2. `test_djangolistfield_rejects_non_djangotype_class` (spec line 731, scaffold line 63)
   - Define an arbitrary plain class inside the test (`class NotADjangoType: pass`) and pass it to `DjangoListField(...)`. Assert `ConfigurationError` with `match=r"DjangoListField requires a DjangoType subclass; got NotADjangoType"` (spec line 547 verbatim; the `got <name>` substring is pinnable because the class name is known at test-write time).
   - Counterpoint to test #1 — proves `inspect.isclass(...)` passes but the `issubclass(..., DjangoType)` guard catches plain classes.

3. `test_djangolistfield_rejects_djangotype_without_definition` (spec line 732, scaffold line 69)
   - Define `class AbstractBase(DjangoType): pass` (no `Meta`). Per `types/base.py:156-158`, the absence of a `Meta` makes `__init_subclass__` return early WITHOUT setting `__django_strawberry_definition__`, so `hasattr(AbstractBase, "__django_strawberry_definition__")` is `False`. Pass `AbstractBase` to `DjangoListField(...)`; assert `ConfigurationError` with `match=r"DjangoListField target AbstractBase is not a registered DjangoType"` (spec line 548 leading prefix).
   - Confirms the rev3 M3 discriminator anchor (spec line 548 / `types/base.py:245`) is wired correctly.

4. `test_djangolistfield_rejects_non_callable_resolver` (spec line 733, scaffold line 75)
   - Use a registered concrete `DjangoType` (the test may inline a tiny `class _T(DjangoType): class Meta: model = ...` fixture using any small `apps.products` / `apps.library` model, OR import a registered type from the example app — see Implementation discretion items below). Pass `DjangoListField(<concrete type>, resolver="not callable")` and assert `ConfigurationError` with `match=r"DjangoListField resolver must be callable\."` (spec line 549 verbatim, including the trailing period — escaped in the regex).
   - Verifies the `resolver=` guard fires AFTER all three target-type guards pass (otherwise the test would fire one of the target-type errors first).

**Slice 2 must not pull behavior tests forward.** The spec's Test plan partitions tests as "Validation tests (Slice 2)" at lines 728-734 vs "Behavior tests (Slice 3)" at lines 737-752. Slice 2 owns ONLY the four validation tests above. Do NOT add tests for: default-resolver shape, `cls.get_queryset` invocation, async path awaits, sync coroutine rejection, consumer `resolver=` queryset/list-return paths, outer nullability, root-position optimization, FK-id elision, or `Meta.primary` interaction — those are Slice 3's contract (spec line 140 enumerates them and Slice 3's planning pass will turn them into the corresponding scaffold TODO replacements at `tests/test_list_field.py:95-194`).

**Fixture / test-isolation pattern.** Use the same `registry.clear()`-around-each-test pattern as `tests/test_registry.py:34-39`'s `_isolate_global_registry` autouse fixture. Tests #2-#4 declare new `DjangoType` subclasses at function scope; without clearing the registry, those declarations leak into subsequent tests as registered types. The scaffold's docstring at `tests/test_list_field.py:26` already names "fixtures" as Slice 1's responsibility but Slice 1 deferred fixture authoring to the slice that ships the first real test bodies (Slice 2); Slice 2 is therefore the slice that adds the fixture. Borrow the exact shape from `tests/test_registry.py:34-39` so the two test files share one source of truth for the pattern.

**Temp tests.** None required. The four validation tests are straightforward `pytest.raises(...)` assertions; no scaffolding under `docs/builder/temp-tests/<slice>/` is justified.

**Coverage gate impact.** Slice 2's four new validation lines (one `if` + one `raise` per check, times four checks = roughly eight new logic lines) are covered one-to-one by the four `pytest.raises(...)` tests above. No additional positive-path test is needed in Slice 2 because Slice 3 will exercise the positive path (a valid `DjangoListField(SomeRegisteredType)` call) through its behavior tests. If Worker 2 finds during implementation that the four validation lines are NOT covered by Slice 2's four tests alone (e.g., because `issubclass` rejects a non-class with its OWN `TypeError` before the spec's pinned message can fire — which it does not: `inspect.isclass(...)` runs first per step 2's pinned ordering, so the class-ness guard catches non-class inputs), surface that as a planning-vs-implementation drift in `### Notes for Worker 1 (spec reconciliation)`.

### Implementation discretion items

These items are at Worker 2's discretion only because Worker 1 has assessed them and decided either equally-valid options exist OR the spec does not pin them:

- **Inline four checks vs. a single `_validate_target_type(target_type)` module-scope helper for the three target-type checks.** The spec leans inline (Decision 5 spec lines 542-561 reads as four terse raises; no helper is named). Worker 2 may extract `_validate_target_type(target_type)` if the inline shape exceeds about ten lines and starts to crowd the factory body — but the helper MUST live at module scope (above `def DjangoListField`), MUST keep the three error messages identical to spec lines 546-548, and MUST NOT be re-imported from anywhere else (one call site only). The `resolver=` check stays inline either way (one line, no body worth factoring). Worker 1's recommendation: keep all four inline unless ruff or readability objects.

- **Concrete-`DjangoType` fixture model choice for the `resolver=` test (#4).** The test needs ONE registered concrete `DjangoType` to get past the three target-type guards. Options:
  - **(a)** Declare a function-scope `class _T(DjangoType): class Meta: model = apps.products.models.Category` (or any other small `apps.products` model). Self-contained, no cross-app imports.
  - **(b)** Import a `BranchType` from `examples/fakeshop/apps/library/schema` (the type Slice 4 will also exercise via `DjangoListField`). Cross-app import but matches Slice 4's eventual fixture surface.
  - **(c)** Reuse the same `_T(DjangoType)` fixture across tests #3 and #4 if it cuts duplication.
  - Worker 1's recommendation: option (a) at function scope; the registry clears between tests (autouse fixture above), so leak isn't a concern. Use `Category` since `tests/test_registry.py:16` already imports it.

- **Test placement within `tests/test_list_field.py`.** The scaffold's TODO comments at lines 56-78 are in declaration order. Worker 2 may either replace each TODO block in place (preserving the file's existing comment structure) OR consolidate all four tests into one contiguous block followed by the Slice-3-pending TODOs. Worker 1's recommendation: replace in place; the scaffold's comment-block boundaries are valuable navigation aids.

- **Cleanup of the four spec-016 Slice-2 TODO comments at lines 56-78.** Per spec line 141 (rev6 L2 cleanup — but that line targets Slice 3, not Slice 2 — Slice 3 covers "the 18 TODO stubs in `tests/test_list_field.py` as they get replaced with real test bodies"). The Slice 2 spec checklist (lines 134-138) does NOT contain a rev6 L2 cleanup bullet, so the TODO-cleanup obligation for the four Slice 2 TODO blocks at lines 56-78 falls naturally on Slice 2's replacement work (the TODOs are deleted when the four real test bodies replace them) without a separate cleanup checklist item. Worker 2's natural implementation pattern (replace TODO with test body) handles this automatically.

NON-discretionary items (Worker 2 MUST follow these):

- The discriminator MUST be `__django_strawberry_definition__` (spec line 548; no alternative).
- The exception class MUST be `ConfigurationError` (spec line 553; no `TypeError` / `ValueError` substitute).
- Validation tests MUST live in `tests/test_list_field.py` (spec line 137; not under `tests/types/` or `tests/base/`).
- The four error messages MUST match spec lines 546-549 verbatim in their pinned-string portions (`DjangoListField requires a DjangoType class`, `DjangoListField requires a DjangoType subclass`, `DjangoListField target {name} is not a registered DjangoType`, `DjangoListField resolver must be callable.`).
- The four checks MUST run in the pinned order from step 2 above: class → subclass-of-DjangoType → registered → resolver-callable. The first three are dependent (later checks assume earlier ones passed); the fourth is independent and goes last.

### Spec slice checklist (verbatim)

The spec's nested sub-bullets for Slice 2 from `## Slice checklist` (spec lines 134-138), copied verbatim. Every box stays `- [ ]` during this planning pass; the final-verification pass ticks each `- [x]` as the contract lands.

- [x] Constructor validates that the argument is a class AND is `issubclass(arg, DjangoType)` AND is registered (`arg.__django_strawberry_definition__` exists) — per [Decision 5](#decision-5--validation--error-shapes). Errors raise `ConfigurationError` with the same `model.Meta.<key> …` shape pattern (`types/base.py:_format_unknown_fields_error` style) reused for consistency.
- [x] `resolver=`, when supplied, is callable; otherwise `ConfigurationError`.
- [x] Tests for validation cluster live in `tests/test_list_field.py`.
- [x] (rev2 H2: dropped — `nullable_list=` is NOT a constructor argument; outer nullability is driven by the consumer's class-attribute annotation.)

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/list_field.py` — added two top-of-module imports (`ConfigurationError` from `.exceptions`, `DjangoType` from `.types`) and four Decision-5 validation guards at the top of `def DjangoListField(...)` body, before the existing async-detection comment block and the `if resolver is None:` dispatch. Guards run in the order pinned by the plan: `inspect.isclass(target_type)` → `issubclass(target_type, DjangoType)` → `hasattr(target_type, "__django_strawberry_definition__")` → `resolver is not None and not callable(resolver)`. The four `ConfigurationError` message strings are the plan's verbatim pins (spec lines 546-549). A short in-source comment block ahead of the guards documents the load-bearing ordering and the rev3 M3 anchor at `types/base.py:245`.
- `tests/test_list_field.py` — replaced the Slice-1 placeholder import-TODO block and the four Slice-2 TODO blocks with real imports (`pytest`, `apps.products.models.Category`, `DjangoListField` + `DjangoType` from the package root, `ConfigurationError` from `.exceptions`, `registry`), an autouse `_isolate_global_registry` fixture mirroring `tests/test_registry.py:34-39`, and the four validation tests (one parametrized over four non-class shapes, three flat module-level functions). The 14 Slice-3 TODO blocks at lines 95-194 are left intact.

### Tests added or updated

- `tests/test_list_field.py::test_djangolistfield_rejects_non_class_argument` — parametrized over `"BranchType"`, `42`, a `DjangoType()` instance, and `None`. Pins that the first guard catches non-class inputs with the spec line 546 message prefix `DjangoListField requires a DjangoType class; got`.
- `tests/test_list_field.py::test_djangolistfield_rejects_non_djangotype_class` — declares an arbitrary `class NotADjangoType: pass` at function scope. Pins that the second guard (`issubclass(..., DjangoType)`) catches plain classes with the spec line 547 message including `got NotADjangoType`.
- `tests/test_list_field.py::test_djangolistfield_rejects_djangotype_without_definition` — declares `class AbstractBase(DjangoType): pass` (no `Meta`). Pins that the third guard (the `__django_strawberry_definition__` discriminator anchored at `types/base.py:245`) catches abstract `DjangoType` bases with the spec line 548 message prefix `DjangoListField target AbstractBase is not a registered DjangoType`.
- `tests/test_list_field.py::test_djangolistfield_rejects_non_callable_resolver` — registers a concrete `class _T(DjangoType): class Meta: model = Category` at function scope (Worker 1's recommended option (a)), then calls `DjangoListField(_T, resolver="not callable")`. Pins the fourth guard with the spec line 549 verbatim message `DjangoListField resolver must be callable.` (period escaped in the `match=` regex). Confirms the resolver guard fires AFTER the three target-type guards pass.

### Validation run

- `uv run ruff format .` — pass (`103 files left unchanged`; the standing `COM812`/formatter conflict warning is unchanged from prior slices and not introduced by this slice).
- `uv run ruff check --fix .` — pass (`All checks passed!`).
- `git status --short` after both ruff invocations:
  - `M django_strawberry_framework/list_field.py` — slice-intended (Slice 2 imports + guards).
  - `M tests/test_list_field.py` — slice-intended (Slice 2 validation tests + fixture).
  - `M django_strawberry_framework/__init__.py`, `M tests/base/test_init.py`, `M docs/spec-016-list_field-0_0_7.md`, deleted `docs/builder/bld-*` (spec-015 leftovers), and the four `?? docs/builder/bld-slice-0/1/2-*.md` + `?? docs/builder/build-016-*.md` artifacts are pre-existing build state from Slices 0 and 1 plus Worker 0's pre-flight; not introduced by this pass.
  - No unrelated tool churn introduced; nothing reverted with `git checkout --`.
- `uv run pytest --no-cov tests/test_list_field.py` — pass (7 passed in 0.04s). The four logical tests expand to seven pytest items because `test_djangolistfield_rejects_non_class_argument` is parametrized over four non-class inputs.
- (Optional) `uv run pytest --no-cov tests/base/test_init.py` — pass (4 passed in 0.03s). Slice 1's public-surface pin still holds; the new imports inside `list_field.py` did not perturb `__all__`.

### Implementation notes

- **`DjangoType` import path landed.** Used `from .types import DjangoType` (the planner's recommended sibling-import path; matches the canonical consumer-facing dotted path documented in `types/__init__.py:1-23`). Imported the class once at module scope; no circular import surfaced (`exceptions.py` is leaf-level by design; `types/__init__.py` only pulls from `.base` and `.finalizer`, neither of which touches `list_field`).
- **All four guards stayed inline at the top of `DjangoListField`.** Worker 1 recommended inline over a `_validate_target_type(...)` helper; the four checks read cleanly as ~12 lines including the message strings and stay below the readability threshold. No helper extracted.
- **In-source comment block over the four guards.** Added a six-line comment explaining the load-bearing ordering and the rev3 M3 anchor (`types/base.py:245`) so a future maintainer who reads the guards in isolation has the same context Worker 1's plan supplied. The comment is intentionally short (no spec-line citations beyond Decision 5's range) to avoid stale-citation risk.
- **Test fixture pattern.** Mirrored the `_isolate_global_registry` autouse fixture from `tests/test_registry.py:34-39` verbatim (one-to-one — same name, same `registry.clear(); yield; registry.clear()` body). This shares the pattern across the two test files without re-extracting it into a shared `conftest.py`; spec slice-2 contract is two-file (source + this test file), and a shared fixture module is out of scope.
- **Parametrized non-class inputs.** Test #1 covers four non-class shapes (`"BranchType"`, `42`, a `DjangoType()` instance, `None`) via `pytest.mark.parametrize` rather than four separate test functions. This matches the plan's "four parametrized inputs" wording and keeps the rejection contract symmetric. `DjangoType()` (an instance) deliberately appears in the non-class set — instantiating `DjangoType` directly does not run the abstract-base guard at `types/base.py:159` because that guard only fires from `__init_subclass__`, not `__init__`; the resulting instance is a plain object and trips `inspect.isclass(...)` correctly.
- **Concrete-DjangoType fixture for test #4.** Used Worker 1's recommended option (a): a function-scope `class _T(DjangoType): class Meta: model = Category`. `Category` is already imported by `tests/test_registry.py:16` and is a small `apps.products` model. The autouse registry-clear fixture ensures the function-scope registration doesn't leak.
- **`# type: ignore[arg-type]` on the two non-class call sites.** `DjangoListField`'s signature pins `target_type: type` and `resolver: Callable | None`; passing a non-class or a non-callable would otherwise fail static type checks. Suppressing the per-test-call ignore keeps the tests focused on the runtime guard rather than static-type satisfaction.

### Notes for Worker 3

- Behavior tests are deliberately deferred to Slice 3 per the spec's Test plan partition (validation cluster Slice 2, behavior cluster Slice 3). The 14 TODO blocks at `tests/test_list_field.py:95-194` are intentionally left intact for Slice 3's planning pass to turn into real tests.
- The autouse `_isolate_global_registry` fixture is intentionally a near-verbatim copy of the one in `tests/test_registry.py:34-39`. If Slice 3 (or a later slice) introduces a third test file that needs the same pattern, that's the moment to consider centralizing into a shared `conftest.py`; not now.
- Test #4 uses `Category` to anchor a registered concrete `DjangoType`. This is the same fakeshop model already imported by the existing `tests/test_registry.py:16`; the choice is for proximity-to-existing-patterns, not for any per-model property.
- No shadow files were used; `list_field.py` is well under the 150-line threshold and the diff is small enough to review by reading the file directly.
- No temp tests were created under `docs/builder/temp-tests/`; the four pinned tests cover the four pinned guards one-to-one.

### Notes for Worker 1 (spec reconciliation)

No spec reconciliation needed. The four `ConfigurationError` message strings landed verbatim per Decision 5 (spec lines 546-549). The discriminator stayed `hasattr(target_type, "__django_strawberry_definition__")` (spec line 548 wording). The check ordering matches the plan's pin (class → DjangoType-subclass → registered → resolver-callable). The `types/base.py:245` anchor is still accurate at HEAD; no rev3 M3 line-shift to record.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

#### `_isolate_global_registry` fixture is a near-verbatim copy of `tests/test_registry.py:34-39`

The autouse fixture at `tests/test_list_field.py:40-50` mirrors the existing fixture at `tests/test_registry.py:34-39`. Bodies and names match one-to-one; the only difference is the new fixture's expanded docstring. Two-site duplication is acceptable today (the duplication is contained, the pattern is one-line), but a third consumer (Slice 3 will register additional `DjangoType` subclasses in many of the 14 new tests in this same file — see [Notes for Worker 1](#notes-for-worker-1-spec-reconciliation-1) below) does NOT trigger a third site because Slice 3's tests live in the same `tests/test_list_field.py` file and reuse this autouse fixture. The duplication therefore stays bounded at two sites unless a future slice adds a third test file needing the same isolation. The Worker 2 Build report's Notes-for-Worker-3 entry pre-records this rationale, which is the right level of acknowledgement for a non-blocking finding.

```tests/test_list_field.py:40
@pytest.fixture(autouse=True)
def _isolate_global_registry() -> None:
    ...
    registry.clear()
    yield
    registry.clear()
```

Recommended change: none in this slice. Carry forward as a Slice 3 review checkpoint — if Slice 3 adds a fourth fixture site, escalate to a Medium DRY finding with a recommended `conftest.py` consolidation under `tests/`.

### DRY findings

- Two-site duplication of the `_isolate_global_registry` autouse fixture between `tests/test_registry.py:34-39` and `tests/test_list_field.py:40-50` — recorded as a Low finding above; deferred to Slice 3 review as a checkpoint rather than a fix-now action. Both copies share identical bodies and the duplication is acknowledged in the Build report.
- The three `target_type.__name__` interpolations inside the second and third guard message strings (`list_field.py:73, 77, 78`) — these are read once each per failing guard and do not warrant extraction into a named local. Inline f-string interpolations are clearer than introducing a `name = target_type.__name__` line just to reuse the symbol two lines apart.
- The four `ConfigurationError` message strings are unique per guard (no repeated literal across the four), so no module-level constant extraction is justified.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` shows ONLY the Slice 1 addition (`"DjangoListField"` re-export + insertion into `__all__`, with the two TODO comments removed). No Slice 2 contribution to the public surface. The Slice 2 spec checklist (spec lines 134-138) does not authorize any `__all__` change. Pass.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- **Four guards land at the top of `def DjangoListField(...)` body** (`list_field.py:60-82`), before any helper definitions, default-resolver dispatch, or `strawberry.field(...)` return. The early-rejection contract from Decision 5 ("Failing at the construction site means the error appears at the line that wrote `DjangoListField(...)`") is preserved one-to-one.
- **Verbatim message strings.** All four `ConfigurationError` strings match spec lines 546-549 character-for-character with the documented `<repr>` / `<name>` placeholders filled. Verified by reading the spec lines against `list_field.py:67-82`.
- **`ConfigurationError` everywhere.** No `TypeError` / `ValueError` substitute at any guard — Decision 5's exception-class contract holds.
- **Load-bearing ordering** (class → `issubclass(DjangoType)` → registered → callable resolver) is correct. Each subsequent target-type check assumes the prior passed; `issubclass` requires its first argument to be a class, and the spec's error strings for the second and third guards assume `target_type.__name__` exists (class-only). The `callable(resolver)` guard runs last and is independent.
- **Parametrized non-class test** (`test_djangolistfield_rejects_non_class_argument`) covers the four shape categories Decision 5 implicitly enumerates (`str`, `int`, `DjangoType` *instance*, `None`); the `DjangoType()` instance case is a particularly good probe — it confirms the first guard catches "looks like a `DjangoType` shape but is an instance, not a class".
- **All four tests use `pytest.raises(ConfigurationError, match=r"...")`** with substantive message-prefix regexes — assertions are stronger than mere "raises any `ConfigurationError`" and protect against silent message drift.
- **`_isolate_global_registry` autouse fixture** correctly clears registry on both entry and exit; tests #3 (`AbstractBase(DjangoType)`) and #4 (`_T(DjangoType)`) declare `DjangoType` subclasses at function scope, and the autouse pattern guarantees no inter-test leakage.
- **The resolver-callable guard order** is correct — test #4 declares a registered concrete `_T(DjangoType)` to ensure the three target-type guards pass FIRST; the test would silently mis-pin if `_T` itself failed an earlier guard.

### Static inspection helper

Skipped for `list_field.py`. Reason: Slice 2's delta to `list_field.py` is ~18 logic lines (2 imports + 1 six-line block comment + 4 single-line `if` guards + 4 `raise ConfigurationError(...)` bodies of 1-4 lines each). Per `docs/builder/BUILD.md` "When to run the helper during build", Worker 3 MUST run the helper when the slice adds 30+ lines of new logic to a file under `django_strawberry_framework/`. The Slice 2 delta is under the threshold; review proceeded inline against `list_field.py` directly. The pre-existing Slice 1 shadow at `docs/shadow/django_strawberry_framework__list_field.{overview.md,stripped.py}` covers the broader factory body for context but was not refreshed for this pass.

Skipped for `tests/test_list_field.py`. Reason: test files are not part of the package's review-worthy logic surface per Worker 3's role-file note; the static helper is targeted at `django_strawberry_framework/` source modules.

### Temp test verification

No temp tests created. The four pinned validation tests are straightforward `pytest.raises(...)` assertions and were verified by reading the diff plus running the focused `uv run pytest --no-cov tests/test_list_field.py` (7 passed in 0.04s — the four logical tests expand to seven items because the first test is parametrized over four non-class inputs).

The `tests/base/test_init.py` public-surface pin was also re-run as a smoke check (4 passed in 0.03s) to confirm the Slice 1 `__all__` addition was not perturbed; pass.

### Notes for Worker 1 (spec reconciliation)

- **Decision 5 says "is registered"; Slice 2 reads `hasattr(__django_strawberry_definition__)`.** The spec's plain-English "is registered" phrase is operationalized by the `hasattr(...)` discriminator (spec line 548 names this discriminator explicitly). At HEAD, the registry's `register_with_definition(...)` call at `types/base.py:241` runs BEFORE `cls.__django_strawberry_definition__ = definition` at `types/base.py:245`. So the discriminator the spec/code uses is "has its `__django_strawberry_definition__` attribute set", not "is present in the global registry". For Decision 5's purposes the two are equivalent — both fire only after `__init_subclass__` has fully run on a concrete `DjangoType` subclass with a `Meta` carrying `model`. No spec edit needed; the spec's rev3 M3 anchor commentary at line 548 already explains the equivalence. Carry-forward note only.
- **`issubclass(target_type, DjangoType)` and the registered check.** The third guard (`hasattr(__django_strawberry_definition__)`) catches one strictly-narrower case than `issubclass(target_type, DjangoType)` — namely, `DjangoType` itself or any abstract base class that subclasses `DjangoType` but does not provide a `Meta` (because `types/base.py:156-158` returns early without setting the attribute). Both guards are load-bearing; the second catches "plain class" and the third catches "abstract `DjangoType` base". Spec is correct as written; no reconciliation needed.
- **Spec lines 581-585 ("Tests in `tests/test_list_field.py` must cover [`Meta.primary` interaction tests]")** are owned by Slice 3 (the Behavior cluster) per spec lines 751-752, even though they are spec'd inside the Decision 6 prose rather than the Test plan's Slice 3 listing. Slice 2 correctly does NOT pull them forward; Worker 1's final verification of Slice 3 should confirm those two tests land. Carry-forward note for Slice 3 review.

### Review outcome

`review-accepted`. The Slice 2 contract from spec lines 134-138 is implemented faithfully: four `ConfigurationError` guards land at the top of `def DjangoListField(...)`, the four message strings match spec lines 546-549 verbatim, the discriminator matches the rev3 M3 anchor at `types/base.py:245`, and the four validation tests pin one assertion per guard with substantive `match=` regexes. The `nullable_list=` constructor argument is correctly absent (rev2 H2 / spec line 138). No High / Medium findings; one Low finding (fixture duplication) is acknowledged in the Build report and deferred to Slice 3 review as a checkpoint. All four sub-checks from the spec slice checklist are addressed in the diff (Worker 1 ticks `- [x]` at final verification).

---

## Final verification (Worker 1)

- **Spec slice checklist:** all four `- [x]` ticked in the Plan's `### Spec slice checklist (verbatim)` above (constructor class/`DjangoType`-subclass/registered validation; `resolver=` callability; tests in `tests/test_list_field.py`; rev2 H2 dropped-`nullable_list=` confirmation). No silently un-ticked boxes; no deferrals recorded under `### Spec changes made (Worker 1 only)` below.
- **DRY check across this slice and prior accepted slices:**
  - Prior accepted slices in this build: Slice 0 (spike, no code landed) and Slice 1 (factory + module + public re-export + `__all__` pin). Slice 1's source surface in `list_field.py` already covers the factory body, the two module-scope `_post_process_consumer_*` helpers, and the resolver-dispatch branches; Slice 2 layers four constructor-time guards at the top of the factory body and does NOT touch any Slice 1 code path.
  - **Validation-guard duplication check.** Grepped `django_strawberry_framework/types/base.py` and `django_strawberry_framework/types/relay.py` for `inspect.isclass`, `issubclass(..., DjangoType)`, and `requires a DjangoType` shape strings. The only hit is `types/base.py:473` (`if issubclass(entry, DjangoType):` inside the finalization sweep), which is a registry-walk filter, not a consumer-input guard — it cannot be reused at `DjangoListField`'s constructor site (it iterates the registry rather than validating a single argument). No duplication of Slice 2's four guards exists elsewhere; the inline placement is the right shape per Decision 5 spec lines 557-561.
  - **`_isolate_global_registry` autouse fixture duplication** between `tests/test_list_field.py:40-50` and `tests/test_registry.py:35-39` — Worker 3's single Low finding. Verified at HEAD: both bodies are `registry.clear(); yield; registry.clear()`. Two-site duplication is acceptable; the spec partitions Slice 2 vs Slice 3 such that Slice 3 will reuse the same autouse fixture without introducing a third site (the 14 Slice 3 behavior tests all live in `tests/test_list_field.py` and inherit the same autouse). Deferred to Slice 3's planning pass as a checkpoint: if Slice 3 ever adds a third test file needing the same isolation, escalate to a Medium DRY finding with a recommended `tests/conftest.py` consolidation. Recorded in this worker's memory file as a carry-forward note.
  - **Repeated literal `__django_strawberry_definition__`** — appears in `list_field.py:75` (Slice 2's new guard), `types/base.py:245,279` (assignment + registry-lookup discriminator), `types/relay.py` (model lookups consolidated via the `_model_for(cls)` helper this patch). The string is the load-bearing public-facing discriminator name documented at spec line 548; it is the protocol-style attribute Strawberry/this package agree on. Extracting a module-level constant `_DJANGO_DEFINITION_ATTR = "__django_strawberry_definition__"` would technically DRY the four sites but would obscure the directly-greppable contract; the spec's verbiage at line 548 explicitly uses the literal string. Decision: keep inline; no carry-forward.
  - **Repeated `target_type.__name__` interpolation** between the second and third guard message strings in `list_field.py:73,77-78` — Worker 3 already noted this and rejected extraction; concurrence here.
- **Existing tests still pass:**
  - `uv run pytest --no-cov tests/test_list_field.py` → `7 passed in 0.05s`. The four logical validation tests expand to 7 items because `test_djangolistfield_rejects_non_class_argument` is parametrized over `"BranchType"`, `42`, `DjangoType()` (instance), and `None`. All seven items green.
  - `uv run pytest --no-cov tests/base/test_init.py` → `4 passed in 0.05s`. Slice 1's `__all__` pin (and the version assertion) still holds; the new `ConfigurationError` and `DjangoType` imports inside `list_field.py` did not perturb `__all__`.
  - No `--cov*` flags passed (per BUILD.md "Coverage is the maintainer's gate, not a worker's tool").
- **Spec reconciliation:** No spec edit required for Slice 2. The Build report's `### Notes for Worker 1 (spec reconciliation)` says "No spec reconciliation needed." and Worker 3's `### Notes for Worker 1 (spec reconciliation)` flagged only commentary (equivalence of "is registered" vs the `hasattr(__django_strawberry_definition__)` discriminator — already documented at spec line 548 / rev3 M3; the load-bearing relationship between the second guard and the third — both correct as written) and a Slice 3 carry-forward (the two `Meta.primary` interaction tests at spec lines 583-584 are owned by Slice 3 per spec lines 751-752, not Slice 2). None of these justify a spec edit. The spec's status line at spec line 4 (`draft (revision 6, post-rev5 scaffolding review)`) is still accurate — rev6 is current, Slice 2 is shipping under the rev6 contract; no slice-shipped state has flipped that the header must reflect yet. Slices 0/1/2 are now `final-accepted` build-side, but the build plan tracks per-slice progress; the spec status line correctly remains at the drafting revision.
- **Final status:** `final-accepted`.

### Summary

Slice 2 ships four `ConfigurationError` constructor-time guards at the top of `def DjangoListField(...)` in `django_strawberry_framework/list_field.py`, with the message strings pinned verbatim to spec lines 546-549 and the ordering load-bearing (class → `issubclass(DjangoType)` → `hasattr(__django_strawberry_definition__)` → `callable(resolver)`). Two new imports (`ConfigurationError` from `.exceptions`, `DjangoType` from `.types`) land at module scope. The validation tests cluster of four `pytest.raises(ConfigurationError, match=r"...")` cases is wired into `tests/test_list_field.py`, with one parametrized test covering four non-class shapes (string, int, `DjangoType()` instance, `None`) and three flat module-level tests for the remaining guards. An autouse `_isolate_global_registry` fixture mirrors `tests/test_registry.py:35-39`'s pattern so function-scope `DjangoType` subclass declarations do not leak between tests. The 14 Slice 3 behavior-test TODO blocks at `tests/test_list_field.py:141-241` are intentionally left intact for Slice 3's planning pass. No public surface (`__all__`) change, no `CHANGELOG.md` change, no docs/KANBAN change. Coverage gate impact stays one-to-one with the four guards via the four pinned tests.

### Spec changes made (Worker 1 only)

No spec edits required for Slice 2. The Build report's spec-reconciliation notes were "No spec reconciliation needed."; Worker 3's spec-reconciliation notes flagged only commentary already documented in the spec (rev3 M3 at spec line 548) and a Slice 3 carry-forward (Decision 6's `Meta.primary` interaction tests at spec lines 583-584 land in Slice 3, not Slice 2). The Low fixture-duplication finding is deferred to Slice 3's planning pass as a carry-forward, not a spec edit (no spec line authorizes or prohibits the fixture-location choice; this is a test-organization detail). Spec status line at spec line 4 (`draft (revision 6, post-rev5 scaffolding review)`) verified accurate at the start of this pass and left unchanged.
