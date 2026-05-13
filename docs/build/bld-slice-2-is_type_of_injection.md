# Build: Slice 2 — is_type_of injection

Spec reference: `docs/spec-relay_interfaces.md` (lines 30-34 Slice 2 checklist; lines 159, 343-351 Decision 6 / borrow note; lines 380-397 internal helper surface for `install_is_type_of`; lines 435-436 implementation-plan step 2; line 499 `test_is_type_of_injected_for_all_djangotypes` test plan entry)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - The TODO anchor at `django_strawberry_framework/types/base.py:84-86` — already named in Slice 1's plan as a Slice 2 anchor — pins the **exact** insertion site for the `install_is_type_of(cls)` call inside `DjangoType.__init_subclass__`. The anchor reads "call `types.relay.install_is_type_of(cls)` here for every DjangoType subclass while preserving consumer-declared `is_type_of`." Slice 2 replaces the anchor with the call in the same change (per `AGENTS.md` line 10: anchors are paired with the code that ships and are removed in that same change).
  - `django_strawberry_framework/types/relay.py:1-25` is the empty-shell module created during Slice 1's wave of TODO anchors. The module docstring "Internal Relay/interface helpers for the 0.0.5 Relay foundation slice." is unchanged. Slice 2 replaces the top of that module's TODO anchor at lines 5-7 (the `install_is_type_of` anchor) with a concrete function. The four other TODO anchors at lines 9-24 (Slice 4's `apply_interfaces`, `implements_relay_node`, `install_relay_node_resolvers`, the four `_resolve_*_default` defaults) remain untouched.
  - The existing `tests/types/test_relay.py:1-10` is a single-function placeholder whose only assertion is the module docstring (it exists purely so the empty-shell `types/relay.py` does not regress the package coverage gate, per `pyproject.toml`'s `fail_under = 100`). Slice 2 deletes that placeholder file in the same change that adds real coverage for `install_is_type_of`. Justification: keeping a docstring-only test alongside a real test of the same module is dead weight, and the docstring assertion is brittle (any rephrasing of the module docstring would break it). The real coverage comes from the new `test_is_type_of_injected_for_all_djangotypes` test in `tests/types/test_relay_interfaces.py`.
  - `tests/types/test_relay_interfaces.py:1-188` already exists with Slice 1's validation tests and the autouse `_isolate_registry` fixture at lines 24-29. Slice 2 appends a new "Slice 2 — `is_type_of` injection" section under the existing "Slice 1 — validation + storage" section divider (line 38-40). The fixture re-use is automatic; no new fixture is required.
  - The strawberry-django borrow site is **`/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py:203-211`** (confirmed via direct read of the local source path that `docs/TREE.md:80-158` cites). The exact pattern is:
    ```
    if "is_type_of" not in cls.__dict__:
        def is_type_of(obj, info):
            if (type_cast := get_strawberry_type_cast(obj)) is not None:
                return type_cast is cls
            return isinstance(obj, (cls, model))
        cls.is_type_of = is_type_of
    ```
    Spec Decision 6 line 351 ("matching `strawberry_django/type.py:204-211`") and the borrowing-posture section at spec line 159 are both anchored to this exact upstream block. The borrow is the `if "is_type_of" not in cls.__dict__:` consumer-preservation gate plus the closure that captures `cls` and `model`.
  - Strawberry's `get_strawberry_type_cast` helper is part of `strawberry.types.cast` (it is the lookup `strawberry_django` uses to honor `strawberry.cast(SomeType, instance)` overrides). Our package does not currently import from `strawberry.types.cast`. We **do not** need to mirror that branch in our borrow — see "Duplication risk avoided" below for the rationale.
  - The `cls.__django_strawberry_definition__` slot is the canonical source of the Django model. It is set on every `DjangoType` subclass with a `Meta` at `django_strawberry_framework/types/base.py:145`. Strawberry-django reads `model` from a kwarg in their decorator path; we read it from the just-built `DjangoTypeDefinition.model` attribute instead (per spec line 314, which already does this for `_resolve_node_default` in Slice 4). One-way data flow: every later slice that needs the model reads `cls.__django_strawberry_definition__.model`; Slice 2 establishes that convention by reading it from the local `definition` variable that is already in scope inside `__init_subclass__` at the call site.

- **New helpers justified.**
  - One new function: `install_is_type_of(type_cls: type) -> None` in `django_strawberry_framework/types/relay.py`. Single responsibility: borrow the strawberry-django `is_type_of` virtual-subclass pattern. The function is called from exactly one site (`DjangoType.__init_subclass__`). Justification for a function rather than inlining the four-line closure into `__init_subclass__`: (a) the spec's internal helper surface (lines 396-397) names `install_is_type_of(type_cls)` as part of the planned `types/relay.py` module — Slice 4 will populate the same module with `apply_interfaces`, `implements_relay_node`, `install_relay_node_resolvers`, and the four `_resolve_*_default` defaults; consolidating the Relay/interface borrows into one module keeps the strawberry-django cribbing visible in one place. (b) the function captures a small but non-trivial DRY contract: "preserve consumer-declared `is_type_of` via `__dict__` membership check" — that contract should appear in exactly one site, not duplicated at `__init_subclass__` and again at Slice 4's finalizer step. (c) inlining would put four lines of Relay-borrow logic inside `__init_subclass__`, which is already at 71 lines / 4 branches per the static helper output (`docs/build/shadow/django_strawberry_framework__types__base.overview.md:46`); the function shape moves the borrow out of the hotspot.
  - The function signature is `install_is_type_of(type_cls: type) -> None` per the spec's helper sketch at line 396. The function reads the Django model off `type_cls.__django_strawberry_definition__.model` (single-source-of-truth pattern; see "Risk 4" below). It returns `None`; mutation is via `setattr(type_cls, "is_type_of", ...)`.
  - **No second helper for `get_strawberry_type_cast`.** Justification under "Duplication risk avoided" — Slice 2 ships the smaller, exact borrow the spec licenses (Decision 6 line 351 cites `strawberry_django/type.py:204-211` verbatim, which is the minimal "isinstance against `(cls, model)`" form, not the broader `get_strawberry_type_cast` form). The wider form is reserved for a follow-up slice if real-world adopters hit `strawberry.cast(...)` cases.

- **Duplication risk avoided.**
  - **Risk 1: re-reading `Meta.interfaces` to decide whether to inject.** Decision 6 line 351 is explicit: `is_type_of` is injected **unconditionally** for every `DjangoType`, Relay or not. The plan therefore does **not** consult `definition.interfaces` or `Meta.interfaces`. The call to `install_is_type_of(cls)` runs once per `DjangoType` subclass with a `Meta`, with no `relay.Node`-aware branching. Slice 4's `install_relay_node_resolvers` (per spec line 392) is where the `relay.Node`-only branching belongs.
  - **Risk 2: duplicating the `cls.__dict__` consumer-preservation check.** Strawberry-django uses `if "is_type_of" not in cls.__dict__:` (verified at the upstream source path). Slice 2 mirrors that exact line — not `if not hasattr(cls, "is_type_of")` (which would also skip inherited Strawberry defaults) and not `if getattr(cls, "is_type_of", None) is None` (which lies about ownership). The `__dict__` membership check appears in exactly one place inside `install_is_type_of`. Slice 4's `install_relay_node_resolvers` uses a different discriminator (`__func__` identity test against `relay.Node`'s defaults, per spec lines 296-308 / Decision 3); the two checks are intentionally not unified because they answer different questions. Worker 2 must not collapse them.
  - **Risk 3: copying the strawberry-django line byte-for-byte vs. an idiomatic rewrite.** The spec's borrowing posture (line 150: "borrow patterns, not implementations") and the dispatcher's prompt explicitly flag this: the spec licenses the borrow but does not require duplication. Slice 2 ships the minimal idiomatic form — a closure that captures `cls` and `model` and returns `isinstance(obj, (cls, model))`. The `get_strawberry_type_cast` branch from upstream is **omitted** because (a) our package does not yet expose `strawberry.cast(...)` integration anywhere else, so the branch would be dead code on every present consumer path; (b) reintroducing it would couple Slice 2 to a strawberry surface we have not yet committed to elsewhere; and (c) if a future adopter hits the `strawberry.cast(...)` case, that branch can be added in a focused follow-up slice without churn to the rest of the Relay machinery. The omission is documented inline in the `install_is_type_of` docstring as a deliberate scope decision with a pointer to the upstream borrow path.
  - **Risk 4: scattering the "where do we read the Django model from?" answer.** Spec line 314 commits the package to reading the model from `cls.__django_strawberry_definition__.model` for Slice 4's `_resolve_node_default`. Slice 2 establishes the same convention for `install_is_type_of` so every later Relay helper reads the model from the same single source. The call site at `__init_subclass__` invokes `install_is_type_of(cls)` **after** `cls.__django_strawberry_definition__ = definition` is set at `types/base.py:145`, so the helper can read the definition off the class. The alternative — passing `model` as a second argument — would couple every call site to model resolution and would not match the spec's helper signature at line 396. Worker 2 must place the call **after** the `__django_strawberry_definition__` assignment.
  - **Risk 5: triggering `is_type_of` on intermediate abstract bases.** `DjangoType.__init_subclass__` short-circuits at `types/base.py:89-91` (`if meta is None: return`) for intermediate bases that do not declare their own `Meta`. Those classes have no `__django_strawberry_definition__`, so `install_is_type_of` cannot read a model from them anyway. The plan therefore places the `install_is_type_of(cls)` call **after** the `meta is None` short-circuit and **after** the `cls.__django_strawberry_definition__ = definition` assignment. Spec line 33's "every `DjangoType` subclass (Relay or not)" wording means "every concrete `DjangoType` that registers a definition", not "every Python class in the `DjangoType` MRO": intermediate abstract bases are explicitly out of scope per the existing `DjangoType` docstring at `types/base.py:14-16` ("Intermediate abstract subclasses without `Meta` are skipped so consumers can layer their own bases on top of `DjangoType`."). Worker 2 must not move the call before the `meta is None` short-circuit.
  - **Risk 6: ordering relative to the `__init_subclass__` body's other steps.** The existing body of `__init_subclass__` (`types/base.py:81-151`) builds the `DjangoTypeDefinition`, registers it, and assigns `cls.__django_strawberry_definition__`. The `install_is_type_of(cls)` call must run **after** the assignment at line 145 (so the helper can read `cls.__django_strawberry_definition__.model`) and **before** the `_optimizer_field_map` / `_optimizer_hints` mirror writes at lines 150-151 (so the body stays grouped by "class metadata" vs. "optimizer mirror"). Insertion at line 146 (immediately after the `__django_strawberry_definition__` assignment, before the optimizer-mirror block) is the cleanest. **Alternative considered:** placing the call at the very end of `__init_subclass__` (after line 151). Rejected because it puts the borrow site farther from the metadata it consumes; the immediate-after-assignment placement keeps data flow local.
  - **Patterns expected to recur in later slices.** Slice 4 will add three more entry points to `install_*` (per spec lines 384-397: `apply_interfaces`, `implements_relay_node`, `install_relay_node_resolvers`) plus the four `_resolve_*_default` functions. Slice 2 establishes the "small, single-responsibility helper named `install_*` that mutates `type_cls` and returns `None`" shape; Slice 4 reuses it. The plan does **not** preempt a generic `install(type_cls, *, attr, value, override_check)` helper now — premature, and the override checks differ (Slice 2 uses `__dict__` membership; Slice 4 uses `__func__` identity). Worker 2 must not introduce such a helper in Slice 2.

### Implementation steps

1. **Remove the TODO anchor at `django_strawberry_framework/types/base.py:84-86`.** The three-line `# TODO(0.0.5 relay interfaces; ...)` comment block (the one that reads "call `types.relay.install_is_type_of(cls)` here for every DjangoType subclass while preserving consumer-declared `is_type_of`.") is removed in the same change that adds the call site. Per `AGENTS.md` line 10. The TODO anchors at `types/base.py:54-57` (Slice 5 promotion) and `types/base.py:575-578` (Slice 3 id-suppression) remain untouched.

2. **Remove the TODO anchor at `django_strawberry_framework/types/relay.py:5-7`.** The three-line `# TODO(0.0.5 relay interfaces; ...)` comment block at the top of the module (the one that reads "implement `install_is_type_of` using strawberry-django's virtual subclass pattern, preserving any consumer-declared `is_type_of`.") is removed in the same change that adds the real function. The TODO anchors at `types/relay.py:9-24` (the four Slice 4 anchors for `apply_interfaces`, `implements_relay_node`, `install_relay_node_resolvers`, and the resolver defaults) remain untouched.

3. **Add `install_is_type_of` to `django_strawberry_framework/types/relay.py`.** Insert the function definition after the module docstring at line 1, after the `from __future__ import annotations` import at line 3, and before the remaining Slice 4 TODO anchors. The function shape:

   ```
   def install_is_type_of(type_cls: type) -> None:
       """Borrow strawberry-django's ``is_type_of`` virtual-subclass behavior.

       Direct port of ``strawberry_django/type.py:203-211``. Strawberry's
       interface dispatch uses ``is_type_of`` to identify the concrete type
       for a returned ORM instance. Without this borrow, an interface field
       that returns a Django model can fail Strawberry's isinstance check
       and surface as "Cannot determine type for object of model X" at
       runtime (spec Decision 6, line 351).

       Preserves a consumer-declared ``is_type_of`` via the ``cls.__dict__``
       membership check (the same discriminator strawberry-django uses).

       The upstream ``get_strawberry_type_cast`` branch is intentionally
       omitted — our package does not yet expose ``strawberry.cast(...)``
       integration anywhere else, and adding it now would couple this slice
       to a Strawberry surface we have not committed to. If a future adopter
       needs ``strawberry.cast(...)`` support, a focused follow-up slice can
       add the branch without churn to the rest of the Relay machinery.
       """
       if "is_type_of" in type_cls.__dict__:
           return
       model = type_cls.__django_strawberry_definition__.model

       def is_type_of(obj: object, info: object) -> bool:
           return isinstance(obj, (type_cls, model))

       type_cls.is_type_of = is_type_of
   ```

   The function imports nothing new beyond what is already in the module (currently nothing — the module imports `from __future__ import annotations` and that is enough since the function body uses only `isinstance` and `setattr` via attribute assignment). `from __future__ import annotations` at `types/relay.py:3` already lets us reference type hints as strings; no additional imports are required.

4. **Add the `install_is_type_of` call inside `DjangoType.__init_subclass__`** in `django_strawberry_framework/types/base.py`. Place the call **after** the `cls.__django_strawberry_definition__ = definition` assignment at line 145, **before** the `_optimizer_field_map` mirror block at lines 150-151. The exact insertion point is line 146 (the new line lands immediately after `cls.__django_strawberry_definition__ = definition`):

   ```
   cls.__django_strawberry_definition__ = definition
   install_is_type_of(cls)
   ```

   This placement satisfies Risk 5 (after the `meta is None` short-circuit at lines 89-91 means intermediate abstract bases are skipped) and Risk 6 (after the definition assignment means the helper can read `cls.__django_strawberry_definition__.model`).

5. **Add the import at `django_strawberry_framework/types/base.py:40`.** Append `from .relay import install_is_type_of` to the local-imports block. The current block has `from .converters import convert_scalar, resolved_relation_annotation` at line 37, `from .definition import DjangoTypeDefinition` at line 38, `from .relations import PendingRelation, PendingRelationAnnotation` at line 39. The new import lands at line 40 in alphabetical order after `.relations`. **No** circular-import concern: `types/relay.py` does **not** import from `types/base.py`; it reads `type_cls.__django_strawberry_definition__` reflectively at call time, not at import time. `types/relay.py:3` (`from __future__ import annotations`) plus the type hint being `type` (a builtin) confirms no static circular reference.

6. **Delete `tests/types/test_relay.py` (the placeholder file).** The single-function `test_relay_module_imports_for_future_slice_anchor` at lines 1-10 only asserts the `types/relay.py` module docstring. Slice 2 adds real coverage for the same module via `test_is_type_of_injected_for_all_djangotypes` and the consumer-preservation test in `tests/types/test_relay_interfaces.py`; the placeholder is dead weight. Per `AGENTS.md` line 21: "Sweep all three test trees for orphan imports when you remove code." There are no other importers of `tests/types/test_relay.py`; pytest discovery is the only reader. The file delete is captured in the same change as the new tests so the package coverage gate stays at 100%.

7. **Add new tests in `tests/types/test_relay_interfaces.py`.** Append a new section divider and the new tests below the existing Slice 1 block (the existing file ends at line 188). The section header mirrors the existing Slice 1 header style (`# ----...---\n# Slice N — <title>\n# ----...---`). The new tests use the already-autouse `_isolate_registry` fixture (lines 24-29) and the `_meta(**attrs)` helper (lines 32-35) where useful.

### Test additions / updates

All Slice 2 tests live in `tests/types/test_relay_interfaces.py`. The new section heading is added below the existing Slice 1 block at line 188:

```
# ---------------------------------------------------------------------------
# Slice 2 — is_type_of injection
# ---------------------------------------------------------------------------
```

Tests (each pinned to `tests/types/test_relay_interfaces.py::<test_name>`):

- `test_is_type_of_injected_for_all_djangotypes` — the canonical spec test (spec line 499). The test defines two concrete `DjangoType` subclasses with `Meta`, asserts that `is_type_of` is present in each `cls.__dict__` (not just inherited), and verifies the injected callable returns `True` for a real model instance and `False` for an unrelated instance. The first subclass omits `Meta.interfaces` entirely (non-Relay); the second is a different `DjangoType` over a different Django model that also omits `Meta.interfaces`. Asserting on `cls.__dict__` not `getattr(cls, "is_type_of", None)` is load-bearing — the spec's Decision 6 line 351 is that injection happens **on the class itself**, not via inheritance. Assertion shape:

  ```
  class CategoryNode(DjangoType):
      class Meta:
          model = Category
          fields = ("id", "name")

  assert "is_type_of" in CategoryNode.__dict__
  category_instance = Category(...)  # in-memory, no save
  assert CategoryNode.__dict__["is_type_of"](category_instance, info=None) is True
  unrelated = object()
  assert CategoryNode.__dict__["is_type_of"](unrelated, info=None) is False
  ```

  Note: the `info` argument is passed as `None` in unit tests because the injected closure does not read from `info`. The closure signature accepts `info` to match Strawberry's `is_type_of(obj, info)` expectation.

  The test uses `apps.products.models.Category` for the first type (matching the Slice 1 file's import style at line 14) and a second model from the same module (`Item` or another available model) for the second type. The autouse `_isolate_registry` fixture handles cleanup.

  **Two assertion modes in one test, per the dispatcher's prompt:** the test covers both the Relay and non-Relay `DjangoType` paths within a single function. Spec line 499 explicitly groups both into one test name. To satisfy the "both Relay and non-Relay" coverage:

  - Subtype A: `Category`-backed `DjangoType`, no `interfaces` declared.
  - Subtype B: `Item`-backed `DjangoType`, `interfaces` not declared (because `"interfaces"` is still in `DEFERRED_META_KEYS` after Slice 2; the Slice 5 promotion is what enables real Relay declaration end-to-end). The "Relay path" assertion is therefore: "even without `Meta.interfaces`, `is_type_of` is still injected" — which is precisely Decision 6 line 351's "unconditionally for every `DjangoType`, not only Relay-declared ones." The test names this contract in its docstring so future readers see why `interfaces` does not appear in the test.

  When Slice 5 lands and `"interfaces"` is in `ALLOWED_META_KEYS`, Slice 4's `test_relay_node_injects_default_resolvers` (spec line 483) will assert the Relay-Node specific behavior; Slice 2's test asserts only the unconditional injection contract.

- `test_consumer_declared_is_type_of_is_preserved` — covers the `__dict__` membership consumer-preservation case from Decision 6 line 351's "If the consumer declares their own `is_type_of`, we do not overwrite it, matching `strawberry_django/type.py:204-211`." The test declares a `DjangoType` subclass that explicitly assigns `is_type_of = staticmethod(...)` (or a plain `def is_type_of(...): ...` in the class body) and asserts that, after class creation, `cls.__dict__["is_type_of"]` is the consumer's callable, not the framework default. Assertion shape:

  ```
  sentinel = object()

  def consumer_is_type_of(obj, info):
      return sentinel

  class CustomNode(DjangoType):
      is_type_of = consumer_is_type_of

      class Meta:
          model = Category
          fields = ("id", "name")

  assert CustomNode.__dict__["is_type_of"] is consumer_is_type_of
  assert CustomNode.__dict__["is_type_of"](Category(...), info=None) is sentinel
  ```

  The sentinel-return path is what proves the consumer's function survives the `__init_subclass__` pass intact, not just that "some callable named `is_type_of` is on the class."

  Justification for splitting this case into its own test instead of folding it into `test_is_type_of_injected_for_all_djangotypes`: the spec's Slice 2 checklist (line 33) lists "Preserve consumer-declared `is_type_of` (do not overwrite when present)" as a separate sub-bullet from "Invoke from `DjangoType.__init_subclass__` ... for every `DjangoType` subclass". Two contracts → two tests, so a future regression in either contract surfaces independently.

- **Temp tests for Worker 3:** Worker 3 may construct a `DjangoType` that simulates a strawberry-typed-instance-return path (e.g. inheriting from a `@strawberry.type`-decorated class that overlays an unrelated model) to verify the `isinstance(obj, (cls, model))` path is what strawberry's interface dispatch will exercise. Temp test files land at `docs/build/temp-tests/slice-2-is_type_of/` per `BUILD.md` line 354. Disposition (promote / keep / delete) is Worker 3's call; the plan flags this here so Worker 3 knows the path is worth exercising even though the unit-level assertion is small.

**Existing test impact:** Deleting `tests/types/test_relay.py` removes one test from the suite. The coverage previously contributed by that file (one statement: the import of `django_strawberry_framework.types.relay`) is now covered by the new `test_is_type_of_injected_for_all_djangotypes` because that test imports from `types.relay` indirectly (via the `__init_subclass__` call site). No other test file imports from `tests/types/test_relay.py`. Worker 2 must run `uv run ruff format .` and `uv run ruff check --fix .` after the deletion in case any ruff-tracked module marker drifts.

### Open questions for Worker 2

1. **Should the injected closure's `info` parameter be typed?** Strawberry's `is_type_of(obj, info)` signature passes the `Info` instance. Our `install_is_type_of` does not read `info`. The plan's pseudo-code uses `info: object` as a permissive type hint that matches strawberry-django's signature shape without binding to `strawberry.types.Info`. Worker 2 may tighten to `strawberry.types.Info` if that does not introduce an import circle (it should not — `types/relay.py` does not import from `types/base.py`). Either is acceptable; the plan does not prescribe.

2. **Should the helper accept `model` explicitly or read it from `__django_strawberry_definition__`?** The plan reads from `__django_strawberry_definition__.model` to match the spec helper signature (line 396: `install_is_type_of(type_cls)`) and to establish a one-way data-flow convention for later slices. If Worker 2 hits a discoverable issue (e.g. the definition is not yet set at the call site because the `__init_subclass__` flow surprises us), Worker 2 may pass `model` as a second argument and document the deviation in the Build report. This would be a Worker-1-flag-worthy spec ambiguity rather than a fail-the-pass condition.

3. **Should the `install_is_type_of` docstring cite the upstream source path?** The plan's pseudo-code docstring includes "Direct port of `strawberry_django/type.py:203-211`." This is consistent with the borrow-citation style the rest of the package uses for strawberry-django borrows. Worker 2 should keep the citation.

4. **Should the placeholder `tests/types/test_relay.py` delete be a separate commit?** No. Per `BUILD.md` "Build artifact template" the Build report section captures the file-deletion alongside the new file additions in one Worker 2 pass. The maintainer commits the whole slice as one diff.

5. **Does the closure need to handle `obj is None`?** Strawberry's `is_type_of` is called with a real returned object; `None` is not a normal input. `isinstance(None, (cls, model))` returns `False`, which is the correct behavior anyway. The plan does not add an explicit `if obj is None: return False` branch. Worker 2 may add one if a coverage gap is found, but the default `isinstance` semantics should suffice.

6. **`get_strawberry_type_cast` omission documentation.** The plan documents the omission inline in the `install_is_type_of` docstring (see step 3). If Worker 2 wants to add an inline comment at the call site instead, that is acceptable. The omission must be visible at exactly one site (docstring **or** call-site comment) so a future reader does not silently re-add the branch as part of an "alignment with strawberry-django" cleanup.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/types/relay.py` — replaced the top `install_is_type_of` TODO anchor (formerly lines 5-7) with the real helper. The four remaining Slice 4 TODO anchors are untouched. The helper preserves a consumer `is_type_of` via `cls.__dict__` membership and otherwise installs a closure that does `isinstance(obj, (type_cls, model))`. The model is read from `type_cls.__django_strawberry_definition__.model` per spec helper signature. The docstring documents the deliberate omission of the upstream `get_strawberry_type_cast` branch (Risk 3 / Open Q 6 — single-site documentation requirement).
- `django_strawberry_framework/types/base.py` — added `from .relay import install_is_type_of` in the local-imports block; removed the three-line `install_is_type_of` TODO anchor that previously sat above `_detect_custom_get_queryset`; inserted `install_is_type_of(cls)` immediately after `cls.__django_strawberry_definition__ = definition` and before the optimizer-mirror block. This satisfies Risk 5 (after `meta is None` short-circuit so intermediate abstract bases are skipped) and Risk 6 (after the definition assignment so the helper can read the model). The two other TODO anchors in this file (Slice 5 promotion at the old line 54-57 region, and Slice 3 id-suppression near `_build_annotations`) are intentionally untouched.
- `tests/types/test_relay.py` — deleted (was a docstring-only placeholder that only asserted the `types.relay` module docstring; per the plan, the new `test_is_type_of_injected_for_all_djangotypes` covers the same import path via real exercise, and the brittle docstring-equality assertion is removed in the same change).
- `tests/types/test_relay_interfaces.py` — added the new "Slice 2 — is_type_of injection" section under the existing Slice 1 block; imports `Item` alongside `Category` so the test can show injection on two different `DjangoType` subclasses backed by two different Django models. The autouse `_isolate_registry` fixture from Slice 1 is reused unchanged.

### Tests added or updated

- `tests/types/test_relay_interfaces.py::test_is_type_of_injected_for_all_djangotypes` — pins the unconditional-injection contract (spec line 499 / Decision 6 line 351). Defines two concrete `DjangoType` subclasses (`CategoryNode`, `ItemNode`), asserts `"is_type_of" in cls.__dict__` for each, and exercises the injected callable: model instance of the correct backing model returns `True`, an instance of the other model returns `False`, and a bare `object()` returns `False`. Uses `info=None` because the closure does not read from `info`. The two-model loop covers Subtype A (`Category`-backed) and Subtype B (`Item`-backed) per the plan's "two assertion modes in one test" note.
- `tests/types/test_relay_interfaces.py::test_consumer_declared_is_type_of_is_preserved` — pins the consumer-preservation contract. Declares `CustomNode` with `is_type_of = consumer_is_type_of` in the class body (so it lands in `cls.__dict__` before `__init_subclass__` runs), then asserts `cls.__dict__["is_type_of"] is consumer_is_type_of` and that calling it returns the sentinel object. The sentinel-identity check proves the consumer's exact callable survived `__init_subclass__` — not merely that "some callable named `is_type_of`" is present.
- `tests/types/test_relay.py` — deleted (placeholder).

### Validation run

- `uv run ruff format .` — pass (`91 files left unchanged`; the COM812-vs-formatter warning is pre-existing config noise, not a Slice 2 introduction).
- `uv run ruff check --fix .` — pass (`All checks passed!`).
- No `pytest` run per `START.md` rules.

### Notes for Worker 3

- The `install_is_type_of` helper reads the Django model from `type_cls.__django_strawberry_definition__.model`. The call site in `__init_subclass__` places the call **after** the `cls.__django_strawberry_definition__ = definition` assignment, so the read is safe by construction. Intermediate abstract `DjangoType` bases without `Meta` short-circuit at `meta is None` before either the assignment or the helper call, so they never trigger the helper and never need a model.
- The plan licensed `info: object` or `strawberry.types.Info` as the type hint. I kept `info: object` to avoid introducing a new strawberry import in `types/relay.py` (the module currently only imports `from __future__ import annotations`); this matches the plan's pseudo-code shape exactly.
- The `get_strawberry_type_cast` branch from upstream is **omitted by design**, documented inline in the helper docstring. Worker 3 should not re-add the branch as an "alignment with strawberry-django" cleanup — see Risk 3 in the plan.
- No shadow file was used. The slice changes are small and the static-helper output for `types/base.py` from Slice 1 (`docs/build/shadow/django_strawberry_framework__types__base.overview.md`) is still current for the surrounding file; the Slice 2 diff adds one import + one call inside an existing method.
- The deletion of `tests/types/test_relay.py` is intentional and authorized by the plan (Risk-N/A — the placeholder's only assertion was a docstring equality on `types.relay.__doc__`; the new tests cover the module via real import-and-exercise paths). No other test files reference `tests/types/test_relay.py`.
- The `_isolate_registry` autouse fixture in `tests/types/test_relay_interfaces.py` already cleans the registry between tests, so the two new `DjangoType` subclasses defined inside the Slice 2 tests do not leak into other tests.

### Notes for Worker 1 (spec reconciliation)

None.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- The `__dict__` consumer-discriminator in `install_is_type_of` (`django_strawberry_framework/types/relay.py:28`) and the `__func__` identity discriminator that will land in Slice 4's `install_relay_node_resolvers` answer two structurally different questions: "did the consumer write their own `is_type_of` from scratch on this class?" (no Strawberry-supplied inherited default exists for `is_type_of`) versus "did the consumer override one of the four `resolve_*` methods, distinct from `relay.Node`'s defaults inherited via the interface?". Verified directly against `strawberry_django/type.py:203-224`: upstream uses the same split (`__dict__` membership at line 204, `__func__` identity at line 223-224). Worker 2's deliberate decision to keep the two discriminators separate (Risk 2 in the plan) is correct; collapsing them into a generic override-detection helper would require parameterizing the discriminator and would obscure the reason each shape is the right one. Recommend Worker 1 carry this observation into the cross-slice integration pass: when Slice 4 lands, confirm the two discriminators remain independent.
- The new helper `install_is_type_of(type_cls)` shape (small, single-responsibility, mutates `type_cls`, returns `None`, reads `model` off `__django_strawberry_definition__.model`) establishes the `install_*` template that Slice 4 will reuse for `apply_interfaces`, `implements_relay_node`, and `install_relay_node_resolvers` per the spec helper sketch at lines 384-397. No premature generalization in Slice 2; the helper is exactly the spec-licensed shape.
- No new shared constants or repeated literals across `types/base.py` and `types/relay.py`. The static helper's "Repeated string literals" section for `relay.py` reports `None`. No DRY violations to address.

### What looks solid

- **Spec contract correctness (Decision 6, spec line 351).** `install_is_type_of` is invoked unconditionally for every concrete `DjangoType` subclass with a `Meta` (`django_strawberry_framework/types/base.py:144`). The helper preserves a consumer-declared `is_type_of` via `cls.__dict__` membership (`django_strawberry_framework/types/relay.py:28`), exactly mirroring `strawberry_django/type.py:204`. The closure body `isinstance(obj, (type_cls, model))` (`django_strawberry_framework/types/relay.py:33`) is the minimal idiomatic borrow from `strawberry_django/type.py:208`, with the `get_strawberry_type_cast` branch deliberately omitted per the plan (Risk 3) and that omission documented inline in the docstring at `django_strawberry_framework/types/relay.py:21-26`.
- **Call-site placement.** The `install_is_type_of(cls)` call is placed after `cls.__django_strawberry_definition__ = definition` at `django_strawberry_framework/types/base.py:143` (line 144), satisfying the helper's read dependency on `__django_strawberry_definition__.model`. The call is also after the `meta is None` short-circuit at line 88-89, so intermediate abstract `DjangoType` bases without `Meta` are correctly skipped — verified by inspection of `types/base.py:82-144` and confirmed against the plan's Risk 5. Placement is before the `_optimizer_field_map` / `_optimizer_hints` mirror block at lines 149-150, keeping the "definition" group together.
- **TODO anchor discipline.** The three-line `install_is_type_of` TODO anchor at the old `types/base.py:84-86` is removed in the same change that ships the call (per `AGENTS.md` line 10). The matching TODO anchor at the old `types/relay.py:5-7` is removed in the same change that ships the helper. The four remaining Slice 4 anchors in `types/relay.py:38-53` are untouched, as are the Slice 3 anchor at `types/base.py:574-575` and the Slice 5 promotion anchor at `types/base.py:55-58`.
- **Boundary discipline.** The diff does not touch `_build_annotations` (Slice 3 work — verified by `git diff -- django_strawberry_framework/types/base.py`), does not mutate `cls.__bases__` (Slice 4), does not inject `apply_interfaces` or any of the four `resolve_*` defaults (Slice 4), and does not enforce the composite-pk constraint (Slice 4). Surgical scope.
- **Test correctness.** `test_is_type_of_injected_for_all_djangotypes` (`tests/types/test_relay_interfaces.py:195-228`) covers both the Relay-eligible-but-not-yet-injected case and the plain non-Relay case via two concrete `DjangoType` subclasses (`CategoryNode` and `ItemNode`), asserts injection on `cls.__dict__` (load-bearing per Decision 6), and exercises the closure for matching, non-matching, and bare-object inputs. `test_consumer_declared_is_type_of_is_preserved` (`tests/types/test_relay_interfaces.py:231-254`) declares `is_type_of = consumer_is_type_of` in the class body so the attribute lands in `cls.__dict__` before `__init_subclass__` runs, then asserts identity (`is consumer_is_type_of`) plus the sentinel return — proving the consumer's exact callable survived rather than just "some callable named `is_type_of`".
- **Coverage.** Focused coverage run (`uv run pytest tests/types/test_relay_interfaces.py --cov=django_strawberry_framework.types.base --cov=django_strawberry_framework.types.relay --cov-report=term-missing`) reports `types/relay.py` at 100% (8/8 statements). The new lines in `types/base.py` (the import at line 40 and the call at line 144) do not appear in the missing-lines list for `types/base.py`, confirming the new code is exercised by the new tests. The package-wide coverage gate (`fail_under = 100`) is the build-closing concern, not a per-slice review concern.
- **Strawberry-django borrow fidelity.** Direct read of `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py:200-211` confirms the upstream `if "is_type_of" not in cls.__dict__:` gate and the `isinstance(obj, (cls, model))` shape. Worker 2's port matches upstream exactly minus the `get_strawberry_type_cast` branch (deliberate omission, documented in-line).
- **Validation.** `uv run ruff format --check` reports `3 files already formatted`. `uv run ruff check` reports `All checks passed!`. The COM812-vs-formatter warning is pre-existing config noise per Worker 2's note and is not a Slice 2 introduction.

### Temp test verification

No temp tests were created. The plan flagged a Strawberry-typed-instance-return path as an optional Worker 3 exercise; on inspection, the two permanent tests already pin the injection contract (presence on `__dict__`, closure behavior for matching/non-matching/bare-object inputs) and the consumer-preservation contract (sentinel-identity check). Adding a temp test that overlays a `@strawberry.type`-decorated class onto an unrelated model would exercise Strawberry's interface dispatch, which is Strawberry's own contract — not a behavior Slice 2 introduces. Disposition: not needed.

### Notes for Worker 1 (spec reconciliation)

- No spec edits required for this slice. The implementation lands exactly on Decision 6 (spec line 351) and the helper signature at spec line 396.
- Cross-slice carry-forward (for the integration pass): the `__dict__`-vs-`__func__` discriminator split between Slice 2 (`is_type_of`) and Slice 4 (`resolve_*` defaults) is intentional and structurally justified. Confirm during integration that Slice 4's `install_relay_node_resolvers` does not collapse the two checks into a single generic override-detector — that would be a DRY false positive.
- The single-source-of-truth pattern `type_cls.__django_strawberry_definition__.model` established by Slice 2 (`django_strawberry_framework/types/relay.py:30`) is the same pattern spec line 314 commits Slice 4 to using for `_resolve_node_default`. Slice 2 reads the model from the same slot via the same access path, so the integration pass should confirm Slice 4 follows suit.
- The static inspection helper ran on both `django_strawberry_framework/types/base.py` and `django_strawberry_framework/types/relay.py`; overviews are at `docs/build/shadow/django_strawberry_framework__types__base.overview.md` and `docs/build/shadow/django_strawberry_framework__types__relay.overview.md`.

### Review outcome

`review-accepted`. The diff implements Decision 6 (spec line 351) faithfully and surgically: `install_is_type_of` is invoked unconditionally for every concrete `DjangoType`, preserves consumer-declared `is_type_of` via `cls.__dict__` membership matching `strawberry_django/type.py:204`, and the helper signature matches the spec's internal-surface sketch at line 396. Boundary discipline is clean (no Slice 3/4 work has crept in), the two new tests pin both contracts (unconditional injection and consumer preservation), and the deletion of `tests/types/test_relay.py` is authorized by the plan with no remaining imports. Focused coverage confirms 100% on `types/relay.py` and exercise of the new lines in `types/base.py`. Ruff format and check pass.

---

## Final verification (Worker 1)

- **DRY check across this slice and prior accepted slices.** No new cross-slice duplication. Slice 1's footprint (`_validate_interfaces` module-local validator, `_INTERFACES_SHAPE_ERROR_LEAD_IN` + `_interfaces_shape_error` shape-rejection scaffold, normalized-tuple thread-through `_validate_meta(meta) -> tuple[type, ...]` into `DjangoTypeDefinition.interfaces`) and Slice 2's footprint (`install_is_type_of(type_cls)` in `types/relay.py`, one import + one call site in `types/base.py`'s `__init_subclass__`) do not share any literals, error scaffolding, or class-mutation helpers — they cannot, because they operate at structurally different layers (Meta-value validation at collection-time vs. ORM-instance type dispatch attached per-class). The single shared coupling point is `cls.__django_strawberry_definition__.model` (`types/relay.py:30`), which Slice 1 populates and Slice 2 reads — that is the intended single-source-of-truth data flow, not duplication. Worker 3's flagged discriminator distinction is correctly preserved: Slice 2's `__dict__` membership check (`types/relay.py:28`) asks "did the consumer write their own `is_type_of` from scratch on this class?" — there is no Strawberry-supplied inherited default for `is_type_of` to gate against, so `__dict__` is exactly the right discriminator. Slice 4's future `__func__` identity check against `relay.Node`'s inherited defaults answers a structurally different question and must remain separate; upstream `strawberry_django/type.py:204` and `:223-224` use the same split for the same reasons. Recording the carry-forward: when Slice 4 lands, confirm `install_relay_node_resolvers` does not collapse the two discriminators into a generic override-detector.
- **Focused tests still pass.** `uv run pytest tests/types/ --cov=django_strawberry_framework.types.base --cov=django_strawberry_framework.types.relay --cov-report=term-missing` reports `109 passed, 2 skipped` (skips: the Slice-4 composite-pk placeholder reserved by Slice 1, and a pre-existing environment-tied skip). `types/relay.py` covers 100% (8/8). `types/base.py` covers 97% with the missing-line residue at pre-existing sites (`91`, `430`, `448-450`) that Slice 1's final-verification memory entry already accounted for — none of the missing lines are Slice 2 additions. The 76% total coverage failure printed by the focused command is expected (one test tree cannot cover the whole package); the package-level `fail_under = 100` gate runs at build close, not per-slice. Slice 1's validation and storage tests in `tests/types/test_relay_interfaces.py` still pass alongside Slice 2's two new tests.
- **Spec reconciliation.** No spec edit needed. The Worker 2 and Worker 3 "Notes for Worker 1" both record no spec issues. The deliberate omission of the upstream `get_strawberry_type_cast` branch is documented inline in the helper docstring at `django_strawberry_framework/types/relay.py:21-26`; spec line 150 ("borrow patterns, not implementations") and Decision 6 at spec line 351 ("matching `strawberry_django/type.py:204-211`") both license the minimal-form borrow without requiring the cast-aware branch. Adding a sentence to the spec to retroactively pin "omit `get_strawberry_type_cast`" would over-constrain a follow-up slice that may legitimately add the branch when a real adopter hits `strawberry.cast(...)` integration; the omission is correctly captured at the helper itself.
- **Final status.** `final-accepted`.

### Summary

Slice 2 lands the strawberry-django `is_type_of` virtual-subclass borrow as a small module-local helper, `install_is_type_of(type_cls)`, in the previously empty `django_strawberry_framework/types/relay.py`. The helper installs a closure that returns `isinstance(obj, (type_cls, model))` (reading the Django model off `type_cls.__django_strawberry_definition__.model`, the single-source-of-truth slot Slice 1 populated), preserves a consumer-declared `is_type_of` via the same `cls.__dict__` membership discriminator strawberry-django uses, and is invoked unconditionally from `DjangoType.__init_subclass__` immediately after the definition assignment so intermediate abstract bases without `Meta` short-circuit before the call. The TODO anchors at the call site (`types/base.py:84-86` pre-edit) and the helper site (`types/relay.py:5-7` pre-edit) are removed in the same change; the four remaining Slice 4 anchors in `types/relay.py` are untouched. Coverage of `types/relay.py` shifts from the brittle docstring-equality placeholder (`tests/types/test_relay.py`, deleted) to two real tests in `tests/types/test_relay_interfaces.py`: `test_is_type_of_injected_for_all_djangotypes` pins the unconditional-injection contract across two `DjangoType` subclasses backed by two different Django models, and `test_consumer_declared_is_type_of_is_preserved` pins the consumer-preservation contract via a sentinel-identity check that proves the consumer's exact callable survived `__init_subclass__`. The slice intentionally does not consult `definition.interfaces` or `Meta.interfaces` — Decision 6 makes the injection unconditional — leaving the Relay-specific branching to Slice 4's `install_relay_node_resolvers`.

### Spec changes made (Worker 1 only)

No spec edits.

### Final status

`final-accepted`.
