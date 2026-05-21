# Build: Slice 1 — Module + factory function

Spec reference: `docs/spec-016-list_field-0_0_7.md` (lines 115-133, Slice 1 checklist bullets; cross-references at Decision 1 [lines 354-379], Decision 2 [lines 381-498], Decision 3 [lines 499-518], and Decision 5's `__django_strawberry_definition__` discriminator anchor [line 548]; rev-history entries rev4 H1 [line 37], rev4 H2 [line 38], rev5 H1 [line 44], rev5 H2 [line 45], rev5 H3 [line 46], rev5 L1 [line 51], rev6 H1 [line 55], rev6 H2 [line 56], rev6 H3 [line 57], rev6 M3 [line 60], rev6 L2 [line 65])
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused (mandatory, verbatim imports).**
  - `_apply_get_queryset_sync` at `django_strawberry_framework/types/relay.py:199-222` and `_apply_get_queryset_async` at `django_strawberry_framework/types/relay.py:225-237`. Confirmed against HEAD via `scripts/review_inspect.py docs/shadow/django_strawberry_framework__types__relay.overview.md` — Symbols table lists `lines 199-222: def _apply_get_queryset_sync(cls, qs, info)` and `lines 225-237: async def _apply_get_queryset_async(cls, qs, info)`. These are the helpers Slice 1's default resolver MUST import and call verbatim per Decision 3 Option A (spec lines 508-513). The sync helper carries the coroutine-in-sync `ConfigurationError` rejection (`types/relay.py:215-218`); reusing it gives the field a free "same error message" contract with Relay paths.
  - `in_async_context` at `django_strawberry_framework/types/relay.py:33` — canonical import is `from strawberry.utils.inspect import in_async_context`. Confirmed in the helper output's Imports table. `list_field.py` MUST import from the same site; no fork (spec line 506).
  - `ConfigurationError` at `django_strawberry_framework/exceptions.py:24` — Slice 2 raises this; Slice 1 imports it pre-emptively so the imports block is stable across slices (Worker 2 implementation discretion: import in Slice 1 OR defer to Slice 2 — see Implementation discretion items below).
  - Relay default resolver pattern at `django_strawberry_framework/types/relay.py:283-290` (`_initial_queryset`) and the four `_resolve_node*` / `_resolve_nodes*` defaults already call `_apply_get_queryset_sync` / `_apply_get_queryset_async` per the helper output's Calls of interest (lines 361, 382, 421, 446). Slice 1's `_default` body mirrors that contract exactly — `model._default_manager.all()` → `_apply_get_queryset_*` → return — keeping one shape for "default queryset over a registered `DjangoType`'s model" across the package.
  - The `# noqa: N802` comment pattern is already present in the scaffold file at `django_strawberry_framework/list_field.py:54`; Slice 1 keeps the same shape on the real `def DjangoListField(...)` line. (Scaffold line 54's `# noqa: N802` directive is currently "invalid" — Worker 2's Slice 0 ruff run flagged it because there's no `def` for it to attach to. The scaffold-cleanup pass in this slice rewrites that section into the real definition; the `noqa` then attaches correctly.)

- **New helpers justified.**
  - `django_strawberry_framework/list_field.py` is a new flat single-file Layer-3 module at the package root per `docs/TREE.md`'s convention (spec line 365; Decision 1's "Module location" subsection at spec lines 360-367 names it explicitly and rejects bundling into `connection.py`). One module, one file, one symbol: `DjangoListField`. No subpackage justified (`docs/TREE.md:194-223` reserves subpackages for three-plus-module subsystems).
  - Two new **module-level** helpers `_post_process_consumer_sync(target_type, result, info)` and `_post_process_consumer_async(target_type, result, info)` (rev6 H2 + rev6 H3). Single responsibility: post-process a consumer-resolver return — `Manager → QuerySet` coerce, then conditionally apply `target_type.get_queryset(...)` via the existing helpers, then return; `list` / generator returns pass through. Module-scope placement (not factory-scope) is **mandatory** per rev6 H2 (spec line 56) so the helpers are referentially transparent, unit-testable independently of `DjangoListField(...)`, and don't duplicate target-type closure capture inside the factory body. The `_consumer` suffix is mandatory per rev6 H3 (spec line 57) so the per-consumer-resolver scope is explicit in the name — `_default` bypasses these because `qs` is already a `QuerySet` from `Manager.all()` and no coercion or isinstance branching is needed there.

- **Duplication risk avoided.**
  - **Risk 1: re-implementing the `cls.get_queryset(...)` coroutine guard.** A naive Slice 1 reading "implement the default resolver's sync path" could lead Worker 2 to inline the `inspect.iscoroutine(result)` rejection check from `types/relay.py:215-218` into `list_field.py`'s `_default`. That would (a) duplicate the visibility-hook coroutine-in-sync rejection contract across two source-of-truth sites and (b) break the spec-014 Relay parity Decision 3 promises (spec lines 484, 502-504). The plan pins **import-and-call** as the only acceptable shape: `_default`'s sync branch is exactly one line — `return _apply_get_queryset_sync(target_type, qs, info)`.
  - **Risk 2: re-implementing the `Manager → QuerySet` coercion in two sites within `list_field.py`.** A naive read of "the wrapper itself does the `Manager → QuerySet` coercion (rev4 M1)" could lead Worker 2 to write `result.all() if isinstance(result, Manager) else result` inline in both `_wrap_sync` and `_wrap_async`. Centralizing in `_post_process_consumer_sync` / `_post_process_consumer_async` (module-scope per rev6 H2) keeps the coercion in one place per sync/async dispatch; the two wrappers are then a one-liner each (`return _post_process_consumer_sync(target_type, user_resolver(root, info), info)` for sync; `return await _post_process_consumer_async(target_type, await user_resolver(root, info), info)` for async).
  - **Risk 3: re-deriving the async-detection asymmetry (rev5 H2).** A future-maintainer reading the two different detection mechanisms (per-call `in_async_context()` for `_default`; per-construction `inspect.iscoroutinefunction(user_resolver)` for the consumer wrapper) might "harmonize" them and break the design. Slice 1's implementation MUST include a Decision-2-style comment near the body explaining the asymmetry, pointing the reader at spec Decision 2's "Async-detection asymmetry" subsection (spec lines 472-477) — one paragraph that names the two dispatch sites, not a duplicated explanation.
  - **Risk 4: the `_default` body wrapping `_apply_get_queryset_async` in an inner `async def _async_path():`.** The scaffold (`list_field.py:104-110`) is the rev5 shape with the inner-wrapper. Rev6 H1 (spec line 55) collapsed that to one line. Slice 1 MUST author the one-liner `if in_async_context(): return _apply_get_queryset_async(target_type, qs, info)` — Strawberry's `AwaitableOrValue` dispatch awaits the returned coroutine; an inner `async def` wrapper adds a redundant coroutine layer with no semantic gain (and triggers a Worker 3 finding for unnecessary indirection).
  - **Risk 5: importing `from .exceptions import ConfigurationError` in Slice 1 without using it.** Slice 1 raises no `ConfigurationError`; Slice 2 owns the validation rejections (spec line 135). An unused import would trip `ruff` `F401`. The plan defers `ConfigurationError` import to Slice 2 (Worker 2 implementation discretion to land it earlier with `# noqa: F401` if it simplifies later diffs; default is "defer").

- **Static-helper invocation discipline.** Worker 1's planning pass ran `scripts/review_inspect.py django_strawberry_framework/types/relay.py --output-dir docs/shadow --stdout` because the plan adds logic that reuses helpers in `django_strawberry_framework/types/relay.py` (file is well over 150 lines AND under `types/`, both triggers per `docs/builder/BUILD.md` "When to run the helper during build"). Helper overview captured at `docs/shadow/django_strawberry_framework__types__relay.overview.md`. Worker 1 skipped the helper for `django_strawberry_framework/__init__.py` (47 lines — well under 150; pure re-export hub; not under `optimizer/` or `types/`); skip reason: **low-surface file; pure re-export**. Worker 1 also skipped the helper for `tests/base/test_init.py` (50 lines, plain assertion test, not a `.py` file under `django_strawberry_framework/`); skip reason: **test-tree file; well under thresholds; assertion-only edit**. Worker 1 did NOT run the helper against `django_strawberry_framework/list_field.py` even though it's a new `.py` file; rationale: the scaffolded file is comment-and-pseudo-code only (zero executable logic), so a pre-implementation helper run would inventory the TODO comments and add no signal beyond what the spec itself provides. Worker 3's review pass will run the helper against the post-build `list_field.py` per the Worker 3 trigger ("the slice adds a new `.py` file of any size, unless it is a pure-class-definition module"); the file is a factory function plus two module-level helpers, so the Worker-3 review-time helper run is the right gate.

### Implementation steps

Worker 2 executes the steps below in order. Each step cites the spec line range AND the existing-source file:line anchor. Line numbers are pin-at-write-time navigational hints — verify against HEAD before pasting; the static-helper output captured at `docs/shadow/django_strawberry_framework__types__relay.overview.md` is the authoritative line-number source for `types/relay.py` at Slice-1-planning-time. Slice 1 ships exactly the imports + helpers + factory described below; no validation logic, no behavior tests (Slice 2 owns validation; Slice 3 owns behavior tests).

1. **Open `django_strawberry_framework/list_field.py` and rewrite the entire body.** The file is currently a SCAFFOLD with TODO comments and pseudo-code only (scaffolded under prior groundwork; see `list_field.py:1-25` for the SCAFFOLD docstring). Slice 1 replaces every TODO block with the real implementation; the module docstring's "SCAFFOLD" wording is removed and the docstring becomes the production-shape description: "``DjangoListField`` — non-Relay ``list[T]`` field for root Query fields. Spec: ``docs/spec-016-list_field-0_0_7.md``. Target release: ``0.0.7``." (one or two short lines, NO TODO references in the final shape). Spec citation: `docs/spec-016-list_field-0_0_7.md:116` (the "New flat module" bullet).

2. **Author the import block at the top of the rewritten module.** Imports, in order (mirrors the scaffold's TODO pseudo-code at `list_field.py:33-49` but with the production shape):

   ```python
   from __future__ import annotations

   import inspect
   from typing import Any, Callable

   from django.db import models
   import strawberry
   from strawberry.types import Info
   from strawberry.utils.inspect import in_async_context

   from .types.relay import _apply_get_queryset_async, _apply_get_queryset_sync
   ```

   Pin justifications:
   - `from __future__ import annotations` — keeps callable signature annotations (`Callable | None`) usable on the runtime path; matches `types/relay.py:23`. Worker 2 implementation discretion: include OR omit (the only typing annotation that needs deferred evaluation in Slice 1 is `Callable | None` on the `resolver` parameter; Python 3.10+'s union syntax is fine without `from __future__`, but the helper imports work either way). Default is **include** for consistency with `types/relay.py`.
   - `inspect` — for `inspect.iscoroutinefunction(user_resolver)` at factory construction time (spec lines 38, 442-443; Slice 1 checklist line 129).
   - `from typing import Any, Callable` — `Any` annotates the resolver `root` parameter (rev4 H1 + Slice 0 verified at spec line 99); `Callable` types the `resolver=` constructor argument. The annotation MUST resolve cleanly under `from __future__ import annotations`.
   - `from django.db import models` — provides `models.Manager` and `models.QuerySet` for the `isinstance` checks in `_post_process_consumer_*`. Same import pattern as `types/relay.py:29` (verified via the helper output's Imports table).
   - `import strawberry` — provides `strawberry.field(...)` for the factory's return value. (Top-level shortcut, not `from strawberry import field` — the codebase consistently uses `strawberry.field(...)` everywhere; e.g., the scaffold's pseudo-code at `list_field.py:143`.)
   - `from strawberry.types import Info` — rev4 H1 / rev5 H3; Slice 0 verified `Info.__module__ == 'strawberry.types.info'` and that the import raises no `ImportError` (per `docs/builder/bld-slice-0-preimpl_verification.md`'s Build report, Spike outcomes section).
   - `from strawberry.utils.inspect import in_async_context` — rev3 M7; verified at `types/relay.py:33` per the helper output's Imports table.
   - `from .types.relay import _apply_get_queryset_async, _apply_get_queryset_sync` — Decision 3 Option A (spec lines 508-513); the only sites that re-use these helpers today are inside `types/relay.py` itself (lines 361, 382, 421, 446 per the helper output's Calls of interest), so `list_field.py` is the second consumer. The blast radius is one line; relocation to `utils/get_queryset.py` is deferred per spec line 513 ("Option B becomes the right move when a third call site needs the helpers").

   `ConfigurationError` is NOT imported in Slice 1 (Slice 2 owns validation; see DRY risk 5 above and Implementation discretion items below). Spec citation: `docs/spec-016-list_field-0_0_7.md:117-119` (the Slice 1 checklist's "Implement DjangoListField as a factory function" bullet and the "Capture target_type via closure" bullet, both of which name the import block).

3. **Define module-level `_post_process_consumer_sync(target_type, result, info)` helper at column 0, BEFORE the factory.** Rev6 H2 (spec line 56) + rev6 H3 (spec line 57) + rev5 M4 (spec line 50). One-line comment above the helper documenting the consumer-resolver-only scope and the `_default`-bypass justification:

   ```python
   # Consumer-resolver post-processing helpers (rev6 H2: module-scope placement,
   # rev6 H3: `_consumer` suffix). The default-resolver path bypasses these
   # because ``qs`` is already known to be a QuerySet from ``Manager.all()`` —
   # no Manager-to-QuerySet coercion or isinstance branching is needed there.

   def _post_process_consumer_sync(target_type: type, result: Any, info: Info) -> Any:
       if isinstance(result, models.Manager):
           result = result.all()  # field-wrapper Manager → QuerySet coercion (rev4 M1).
       if isinstance(result, models.QuerySet):
           return _apply_get_queryset_sync(target_type, result, info)
       return result  # Python list / generator — pass through (rev2 H1).
   ```

   The `result.all()` coercion runs BEFORE the isinstance-QuerySet check (rev2 H1 + rev4 M1; spec lines 226, 489-490 — "the field wrapper itself performs the Manager → QuerySet coercion ... BEFORE applying target_type.get_queryset(...)"). After coercion a `Manager` becomes a `QuerySet`, so a `Manager`-shaped consumer return is threaded through `_apply_get_queryset_sync` exactly like a direct `QuerySet`-shaped return. The optimizer extension's own `Manager` coercion at `optimizer/extension.py:582-583` is a downstream safety net for non-`DjangoListField` root resolvers (spec line 226's two-coercion explanation). Spec citation: spec lines 397-410 (Decision 2 pseudocode for `_post_process_consumer_sync`); spec line 122 (Slice 1 checklist's "Default resolver body — sync path" sub-bullet pinning the verbatim port from `types/relay.py:_apply_get_queryset_sync`).

4. **Define module-level `async def _post_process_consumer_async(target_type, result, info)` helper at column 0, immediately after `_post_process_consumer_sync`.** Mirror shape with `await` on the `_apply_get_queryset_async` call:

   ```python
   async def _post_process_consumer_async(target_type: type, result: Any, info: Info) -> Any:
       if isinstance(result, models.Manager):
           result = result.all()
       if isinstance(result, models.QuerySet):
           return await _apply_get_queryset_async(target_type, result, info)
       return result
   ```

   Spec citation: spec lines 413-418 (Decision 2 pseudocode for `_post_process_consumer_async`). Same rationale as step 3.

5. **Define the `DjangoListField` factory function at column 0, after the two helpers.** Signature per spec line 421-428 (Decision 2 pseudocode); the `# noqa: N802` comment is mandatory per rev5 L1 (spec lines 51, 118):

   ```python
   def DjangoListField(  # noqa: N802  # PascalCase for graphene-django parity — consumer usage is `DjangoListField(BranchType)`
       target_type: type,
       *,
       resolver: Callable | None = None,
       description: str | None = None,
       deprecation_reason: str | None = None,
       directives: tuple = (),
   ):
       """Factory for a non-Relay ``list[T]`` root Query field bound to a ``DjangoType``.

       See ``docs/spec-016-list_field-0_0_7.md`` Decision 1 (mechanism) and
       Decision 2 (default-resolver shape) for the design contract.
       """
   ```

   The exact wording of the docstring is Worker 2 discretion — the contract is "one paragraph naming the spec; the spec is the source of truth for the symbol contract." A reference to Decision 2's "Async-detection asymmetry" subsection (spec lines 472-477) may live in the docstring OR as an in-body comment near the `_default` and `_wrap` definitions; the in-body comment is preferred because the asymmetry is a code-shape decision (see step 9 below).

   Spec citation: spec lines 421-428 (signature) and spec line 118 (Slice 1's "Suppress ruff N802 ... # noqa: N802" sub-bullet).

6. **Inside the factory body, branch on `resolver is None`.** If `resolver is None`, build the default resolver `_default` (step 7). Otherwise, build the consumer wrapper `_wrap` choosing sync-vs-async via `inspect.iscoroutinefunction(resolver)` at factory construction time (step 8). Spec citation: spec lines 431-454 (Decision 2 pseudocode); spec line 129 (Slice 1's "Optional `resolver=` constructor argument" sub-bullet pinning `inspect.iscoroutinefunction` at factory construction time per rev4 H2 + rev5 H1).

7. **Default-resolver body — sync first, async branch collapsed per rev6 H1.** Inside the factory's `if resolver is None:` arm, define the `_default` function exactly as below; the async branch is a one-liner per rev6 H1 (spec line 55):

   ```python
   def _default(root: Any, info: Info):
       qs = target_type.__django_strawberry_definition__.model._default_manager.all()
       if in_async_context():
           # rev6 H1: return the coroutine from ``_apply_get_queryset_async`` directly;
           # Strawberry's AwaitableOrValue dispatch awaits it. An inner ``async def``
           # wrapper would add a redundant coroutine layer with no semantic gain.
           return _apply_get_queryset_async(target_type, qs, info)
       return _apply_get_queryset_sync(target_type, qs, info)

   wrapped = _default
   ```

   `target_type` is closed over via the factory's enclosing scope (rev2 H3 + rev4 H1; spec lines 119, 495). The resolver signature is `(root: Any, info: Info)` with NO `**kwargs` (rev4 H1; spec lines 37, 496). The `qs = target_type.__django_strawberry_definition__.model._default_manager.all()` line matches the spec line 122's sub-bullet (and mirrors `types/relay.py:_initial_queryset` at `types/relay.py:283-290`, but is inlined here because the field doesn't need a separate helper).

   Spec citations: spec lines 432-440 (Decision 2 pseudocode `_default` shape after rev6 H1); spec lines 120-127 (Slice 1's "Default resolver body — sync path" and "Default resolver body — async path" sub-bullets).

8. **Consumer-wrapper construction — choose sync vs async at factory construction time per rev4 H2 + rev5 H1.** Inside the factory's `else:` arm:

   ```python
   user_resolver = resolver
   if inspect.iscoroutinefunction(user_resolver):
       async def _wrap(root: Any, info: Info):
           return await _post_process_consumer_async(
               target_type, await user_resolver(root, info), info,
           )
   else:
       def _wrap(root: Any, info: Info):
           return _post_process_consumer_sync(target_type, user_resolver(root, info), info)
   wrapped = _wrap
   ```

   Key contract: the `async def _wrap` `await`s the consumer coroutine BEFORE passing the result to `_post_process_consumer_async`, so the isinstance-QuerySet branch in the helper sees the awaited `QuerySet`, not the coroutine itself (rev4 H2; spec lines 38, 444-450). The `_wrap_sync` calls `_post_process_consumer_sync` directly (rev5 H1's YAGNI choice — no runtime `inspect.iscoroutine(result)` fallback; spec line 44).

   `user_resolver = resolver` is an aliasing rebind that documents the closure capture explicitly; Worker 2 implementation discretion to keep the alias OR close over `resolver` directly. Default is **keep** because the alias matches the spec pseudocode (spec line 442) and reads as "the consumer's resolver" at the call site.

   Spec citations: spec lines 442-454 (Decision 2 pseudocode `_wrap` shape); spec line 129 (Slice 1 checklist's "Optional `resolver=` constructor argument" sub-bullet pinning rev4 H2 + rev5 H1).

9. **Add the Decision-2-style "Async-detection asymmetry" comment near the `_default` / `_wrap` definitions.** One paragraph (rev5 H2; spec lines 472-477). The exact wording is Worker 2 discretion, but the comment MUST:
   - Name the two detection mechanisms: runtime `in_async_context()` in `_default` vs construction-time `inspect.iscoroutinefunction(user_resolver)` in the consumer-wrapper branch.
   - Name the two dispatch sites: `_default` dispatches per-call (same factory output runs under both `schema.execute_sync` and `await schema.execute`); the consumer wrapper dispatches per-construction (Strawberry inspects the resolver signature once at schema construction).
   - Reference the spec's Decision 2 "Async-detection asymmetry" subsection by name (`docs/spec-016-list_field-0_0_7.md` Decision 2, "Async-detection asymmetry — intentional, not a harmonization candidate") so a future maintainer reading the comment can find the longer explanation.
   - Do NOT duplicate the spec text inline; the comment is a one-paragraph pointer, not a copy.

   Spec citation: spec lines 472-477 (Decision 2's "Async-detection asymmetry" subsection).

10. **Return the Strawberry field.** End of factory body:

    ```python
    return strawberry.field(
        resolver=wrapped,
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )
    ```

    The order of `description=` / `deprecation_reason=` / `directives=` in the call is Worker 2 implementation discretion; the spec pseudocode (line 462-467) uses this order and Worker 1 recommends it for consistency, but transposing two adjacent kwargs is benign. Spec citation: spec lines 130, 462-467 (Slice 1's "Optional `description=` / `deprecation_reason=` / `directives=` pass-through" sub-bullet; Decision 2 pseudocode final return).

11. **Remove the SCAFFOLD docstring's "SCAFFOLD" wording and add an explicit `__all__ = ("DjangoListField",)` declaration.** Two cleanup edits at the bottom of `list_field.py`:
    - The module docstring (currently `list_field.py:1-25`) is rewritten to a short production-shape docstring (Worker 2 discretion — one paragraph, no "SCAFFOLD" wording, no TODO references).
    - `__all__ = ("DjangoListField",)` is added at module scope so the module's exported surface is explicit. Worker 2 implementation discretion: include OR omit — the package's `__init__.py` controls the public surface either way; the in-module `__all__` is a convention-aid for IDE introspection. Default is **include** to match the scaffold's TODO directive at `list_field.py:152` ("add a real `__all__ = ("DjangoListField",)` declaration").

    Spec citation: spec line 117 (factory return shape) and spec line 152 of the scaffolded `list_field.py` (the existing TODO directive).

12. **Re-export `DjangoListField` from `django_strawberry_framework/__init__.py`.** Three edits (verify against HEAD before pasting; line numbers per current `__init__.py`):
    - Replace the placeholder TODO block at `__init__.py:25-34` with the real import `from .list_field import DjangoListField  # noqa: E402` placed in alphabetical position immediately after `from .scalars import BigInt` at `__init__.py:22` (the alphabetical position between `BigInt` and `DjangoOptimizerExtension`).
    - Replace the TODO comment at `__init__.py:40` (inside the `__all__` tuple) with the literal string `"DjangoListField"` in alphabetical position between `"BigInt"` and `"DjangoOptimizerExtension"`.
    - The `noqa: E402` directive is required because `from strawberry import auto` at `__init__.py:18` is itself `E402`-suppressed; the new import must follow the same pattern.

    Spec citations: spec line 131 (Slice 1's "Re-export from `__init__.py` in alphabetical order"); Decision 1's public-export-surface subsection (spec lines 369-373).

13. **Update `tests/base/test_init.py`'s pinned `__all__` assertion.** Two edits (verify against HEAD; line numbers per current `test_init.py`):
    - Remove the TODO comment at `test_init.py:36-40` (the "TODO(spec-016, Slice 1 — Decision 1)" block).
    - Replace the TODO placeholder at `test_init.py:43` (inside the assertion tuple) with the literal `"DjangoListField"` in alphabetical position between `"BigInt"` and `"DjangoOptimizerExtension"`.

    The resulting assertion shape (per spec line 132 — "Update `tests/base/test_init.py`'s pinned `__all__` assertion"):

    ```python
    assert django_strawberry_framework.__all__ == (
        "BigInt",
        "DjangoListField",
        "DjangoOptimizerExtension",
        "DjangoType",
        "OptimizerHint",
        "__version__",
        "auto",
        "finalize_django_types",
    )
    ```

    Spec citation: spec line 132 (Slice 1's "Update `tests/base/test_init.py`'s pinned `__all__` assertion").

14. **Remove the spec-016 scaffold TODOs at the three touched sites (rev6 L2).** Per spec line 133 (Slice 1's "Remove the spec-016 scaffold TODOs at this site" sub-bullet). Worker 2 MUST `grep -n "# TODO" django_strawberry_framework/list_field.py django_strawberry_framework/__init__.py tests/base/test_init.py` (or equivalent) and confirm zero remaining `# TODO(spec-016, ...)` markers in the three files at end-of-pass. The Slice 1 grep set:
    - `django_strawberry_framework/list_field.py` — scaffold-era TODOs at lines 27, 52, 67, 78, 96, 136, 151 (verify against HEAD; the file is rewritten end-to-end in step 1, so these naturally disappear if step 1 is followed faithfully).
    - `django_strawberry_framework/__init__.py` — TODOs at lines 25 and 40 (verify against HEAD).
    - `tests/base/test_init.py` — TODOs at lines 36 and 43 (verify against HEAD).

    `ruff`'s `ERA001` (commented-out code) does NOT catch `# TODO:` markers, so the cleanup is a manual grep-and-remove pass (spec line 133's last sentence: "explicit cleanup is the only protection against the scaffold TODOs landing in main"). Worker 2 records the grep output in the Build report's `### Files touched` subsection.

    Spec citation: spec line 133 (Slice 1's TODO-cleanup sub-bullet).

15. **Run `uv run ruff format .` and `uv run ruff check --fix .` after editing.** Per `AGENTS.md` line 14: "Run `uv run ruff format .` and `uv run ruff check --fix .` after every edit." Record both invocations' outcomes in the Build report's `### Validation run` subsection. Note Slice 0's Worker 2 build report observed 40 pre-existing `ERA001` errors against the scaffold-era pseudo-code; rewriting `list_field.py` in step 1 (removing the pseudo-code blocks) will resolve every one of those 40 errors. Worker 2 confirms the `ruff check` post-edit count drops to zero (or names any residual error explicitly).

### Test additions / updates

- **No behavior tests in Slice 1.** Behavior tests live in `tests/test_list_field.py` and are owned by Slice 3 per the spec's Slice checklist (spec lines 139-141). Slice 2 owns validation tests (4 validation tests per spec lines 730-733; spec line 137). Slice 1's contract is the symbol itself — Slice 3's 14 behavior tests exercise it.

- **Pinned `__all__` assertion in `tests/base/test_init.py`.** The only test edit in Slice 1 is the `tests/base/test_init.py::test_public_api_surface_is_pinned` assertion update covered by step 13. The assertion shape is:

  ```python
  assert django_strawberry_framework.__all__ == (
      "BigInt",
      "DjangoListField",
      "DjangoOptimizerExtension",
      "DjangoType",
      "OptimizerHint",
      "__version__",
      "auto",
      "finalize_django_types",
  )
  ```

  Spec citation: spec line 132.

- **Existing tests remain passing after the `__all__` edit.** Worker 2 may run `uv run pytest --no-cov tests/base/test_init.py` once as a focused-test invocation to confirm the assertion still holds and no other test in `tests/base/` regresses. The explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov` per `docs/builder/BUILD.md`'s "Coverage is the maintainer's gate, not a worker's tool" rule (lines 98-109). No `--cov*` flags in any worker pass.

- **No temp tests staged.** The Slice 1 contract is mechanical (add a symbol; re-export; update one pinned assertion). The behavior contract is covered by Slice 3's package-internal tests against the real symbol. If Worker 3's review pass surfaces a missed angle, temp tests under `docs/builder/temp-tests/slice-1/` remain available for the review-loop; the planning pass does not pre-stage one.

### Implementation discretion items

These items are at Worker 2's discretion only because Worker 1 has assessed them and decided either equally valid options exist OR the spec does not pin them:

- **The exact wording of the docstring on `def DjangoListField(...)`.** Spec pseudocode (spec lines 421-428) has no docstring; Worker 1's step 5 above suggests a two-line shape ("Factory for a non-Relay `list[T]` root Query field bound to a `DjangoType`. See `docs/spec-016-list_field-0_0_7.md` Decision 1 (mechanism) and Decision 2 (default-resolver shape) for the design contract."). Worker 2 may rewrite, expand to a longer paragraph, or trim to one sentence — the only constraint is that the docstring NAMES the spec by path (so the symbol is grep-anchored from the spec at review time) and does NOT duplicate the spec's contract in prose form.

- **The order of `description=` / `deprecation_reason=` / `directives=` in the inner `strawberry.field(...)` call.** Spec pseudocode (lines 462-467) uses `resolver=, description=, deprecation_reason=, directives=`. Worker 1 recommends keeping this order for spec-parity but transposing two adjacent kwargs is benign (the kwargs are independent; Strawberry treats them positionally only if you skip `resolver=`). Default is **match the spec pseudocode order**.

- **The variable name `_default` vs `_default_resolver`.** Spec Decision 2 pseudocode uses `_default` (spec line 432). Worker 1's plan uses `_default` per the spec. Worker 2 may rename to `_default_resolver` for clarity (it's the same closure shape). Default is **keep `_default`** for spec-parity.

- **Whether to include `from __future__ import annotations` in `list_field.py`.** Worker 1's step 2 above recommends include for consistency with `types/relay.py:23`. Python 3.10+'s union syntax (`Callable | None`) works without it, but the import is harmless and the codebase convention pattern includes it. Default is **include**.

- **Whether to include an in-module `__all__ = ("DjangoListField",)` declaration.** Worker 1's step 11 recommends include per the scaffold's TODO directive at `list_field.py:152` and to match Layer-3 module convention (`scalars.py` etc. — Worker 2 may verify by reading `scalars.py`). The package's public surface is controlled by `__init__.py`'s `__all__` either way. Default is **include**.

- **Whether to import `ConfigurationError` in Slice 1.** DRY risk 5 above flags this as a Slice 2 concern. Worker 1's recommendation is **defer to Slice 2** to avoid an unused-import lint error. Worker 2 may pre-import in Slice 1 with `# noqa: F401` if the import simplifies the Slice 2 diff; the trade-off is one `# noqa` line in Slice 1's diff vs one import-line addition in Slice 2's diff. Default is **defer**.

- **Whether `user_resolver = resolver` is kept as an explicit alias.** Step 8 above recommends keep for spec-parity. Worker 2 may close over `resolver` directly (one fewer local). Default is **keep the alias**.

These are the **only** discretionary items. Everything else in this slice is pinned:

- The list of imports and their pinned paths (mandatory per Decision 3 Option A + rev3 M7 + Slice 0 verification).
- The module-level placement of `_post_process_consumer_sync` / `_post_process_consumer_async` (mandatory per rev6 H2 — NOT factory-scope).
- The `_consumer` suffix in the helper names (mandatory per rev6 H3).
- The `# noqa: N802` comment on `def DjangoListField(...)` (mandatory per rev5 L1).
- The async-detection asymmetry — runtime `in_async_context()` in `_default` vs construction-time `inspect.iscoroutinefunction(user_resolver)` in the consumer-wrapper branch (mandatory per rev5 H2).
- The collapsed one-liner `if in_async_context(): return _apply_get_queryset_async(target_type, qs, info)` in `_default` — NOT an inner `async def _async_path()` wrapper (mandatory per rev6 H1).
- The `_default`-bypasses-`_post_process_consumer_*`-helpers shape (mandatory per rev6 H3 — `_default` calls `_apply_get_queryset_*` directly because `qs` is already a `QuerySet` from `Manager.all()`).
- The `result.all()`-BEFORE-`isinstance(QuerySet)` order inside `_post_process_consumer_*` (mandatory per rev2 H1 + rev4 M1).
- The `(root: Any, info: Info)` resolver signature with NO `**kwargs` (mandatory per rev4 H1).
- The re-export site (`django_strawberry_framework/__init__.py`) and the alphabetical position between `BigInt` and `DjangoOptimizerExtension` (mandatory per Decision 1).
- The `tests/base/test_init.py::test_public_api_surface_is_pinned` assertion update (mandatory per spec line 132).
- The scaffold-TODO cleanup at all three touched sites (mandatory per spec line 133 / rev6 L2).

### Spec slice checklist (verbatim)

The spec's nested sub-bullets for Slice 1 from `## Slice checklist` (spec lines 115-133), copied verbatim. Every box stays `- [ ]` during this planning pass; the final-verification pass ticks each `- [x]` as the contract lands.

- [x] New flat module `django_strawberry_framework/list_field.py` (placement decision: see [Decision 1](#decision-1--module-location-mechanism--public-export)) housing the `DjangoListField` symbol.
- [x] Implement `DjangoListField` as a **factory function** (rev2 H2 — `strawberry.field` is a function in the installed Strawberry version, not a class, so subclassing it is not viable; and `__set_name__` cannot replace an already-assigned class attribute). The factory returns `strawberry.field(resolver=<wrapped>, description=..., deprecation_reason=..., directives=...)`. Consumer usage is `all_branches: list[BranchType] = DjangoListField(BranchType)` — Strawberry reads the consumer's class-attribute annotation for the outer GraphQL list shape (`list[BranchType]` → `[BranchType!]!`, `list[BranchType] | None` → `[BranchType!]`), so the factory does NOT need to override the annotation.
- [x] Suppress `ruff` rule **N802** on the `def DjangoListField(...)` line with `# noqa: N802  # PascalCase for graphene-django parity — consumer usage is `DjangoListField(BranchType)`` (rev5 L1). The repo's `pyproject.toml` enables `N` (pep8-naming) in `[tool.ruff.lint]` and N802 flags PascalCase function names; the PascalCase shape is intentional graphene-django parity. Per-line `noqa` is preferred over a per-file ignore because `list_field.py` only has one PascalCase definition and a wider exception would hide future violations.
- [x] Capture `target_type` via closure (rev2 H3, rev4 H1 — the resolver signature is the Strawberry-native `(root: Any, info: Info)`, NOT `(type_cls, info)` or `(root, info, **kwargs)`; `target_type` is looked up from the enclosing scope, not from a first positional argument). Imports: `from typing import Any` and `from strawberry.types import Info` at the top of `list_field.py`. Drop `**kwargs` from every resolver signature in this card; Strawberry treats every parameter as a GraphQL argument by default, and this card does not add any.
- [x] Default resolver body — sync path:
  1. `qs = target_type.__django_strawberry_definition__.model._default_manager.all()`
  2. `qs = target_type.get_queryset(qs, info)` — coroutine guard rejected per [Decision 3](#decision-3--get_queryset-and-async-symmetry) (port verbatim from `types/relay.py:_apply_get_queryset_sync` so the same `ConfigurationError` shape covers both Relay and list paths).
  3. `return qs`
- [x] Default resolver body — async path:
  1. `qs = target_type.__django_strawberry_definition__.model._default_manager.all()`
  2. `qs = await _apply_get_queryset_async(target_type, qs, info)` — port verbatim from `types/relay.py`.
  3. `return qs`
- [x] Async detection uses the same `in_async_context` hook the Relay defaults use — pin the import as `from strawberry.utils.inspect import in_async_context` (rev3 M7; verified at `types/relay.py:33`). Same `iscoroutinefunction`/coroutine handling.
- [x] Optional `resolver=` constructor argument that overrides the default body. When supplied, wrap the consumer resolver so a `Manager`/`QuerySet` return value is fed through `target_type.get_queryset(qs, info)` (rev2 H1 — graphene-django parity). Detection: `isinstance(result, (models.Manager, models.QuerySet))`. The wrapper itself does the `Manager → QuerySet` coercion via `result.all()` BEFORE applying `get_queryset` (rev4 M1; the optimizer's downstream `Manager` coercion is a safety net, not a substitute). Async consumer resolvers (rev4 H2): inspect `user_resolver` with `inspect.iscoroutinefunction(...)` at factory construction time; if true, build an `async def` wrapper that `await`s the consumer's coroutine BEFORE the `isinstance` check, so an async resolver returning a `QuerySet` still gets `get_queryset` applied. Python `list` returns from sync OR async resolvers pass through unchanged. (Rev5 H1: the rev4 runtime-fallback branch for `functools.partial`-wrapped async resolvers was dropped as YAGNI — `inspect.iscoroutinefunction` covers normal `async def` resolvers; consumers wrapping an async function in `functools.partial` rewrap in `async def` instead.) Optimizer cooperation still applies because the extension is root-gated against `info.path.prev is None` (`optimizer/extension.py:553`); a consumer resolver returning a `QuerySet` is planned exactly like the default.
- [x] Optional `description=` / `deprecation_reason=` / `directives=` pass-through into the inner `strawberry.field(...)` call so the symbol is feature-comparable to `strawberry.field(...)` at the metadata level.
- [x] Re-export from `django_strawberry_framework/__init__.py` in alphabetical order ([Decision 1](#decision-1--module-location-mechanism--public-export)); add `"DjangoListField"` to `__all__`.
- [x] Update `tests/base/test_init.py`'s pinned `__all__` assertion.
- [x] Remove the spec-016 scaffold TODOs at this site (rev6 L2) — covers `django_strawberry_framework/list_field.py`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`. Ruff's `ERA001` catches commented-out code but not `# TODO:` markers, so explicit cleanup is the only protection against the scaffold TODOs landing in main.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/list_field.py` — rewrote the SCAFFOLD module end-to-end into the production factory. Imports (verified at HEAD against the planning citations): `inspect`, `Callable` from `collections.abc`, `Any` from `typing`, `strawberry`, `django.db.models`, `strawberry.types.Info`, `strawberry.utils.inspect.in_async_context`, and the two `_apply_get_queryset_async` / `_apply_get_queryset_sync` helpers from `.types.relay` (HEAD lines 199 / 225, signatures `(cls, qs, info)`). Module-scope `_post_process_consumer_sync` / `_post_process_consumer_async` helpers per rev6 H2 + rev6 H3 with the `Manager → QuerySet → get_queryset` coercion order per rev2 H1 + rev4 M1. `def DjangoListField(...)` carries the `# noqa: N802` rationale per rev5 L1. The default-resolver async branch is the rev6 H1 one-liner (`return _apply_get_queryset_async(target_type, qs, info)`), not an inner `async def _async_path()`. Consumer-wrapper sync-vs-async is decided at factory construction time via `inspect.iscoroutinefunction(user_resolver)` per rev4 H2 + rev5 H1 (no runtime fallback). An in-body comment near the wrapper dispatch documents the async-detection asymmetry per rev5 H2 and points readers at the spec's Decision 2 "Async-detection asymmetry" subsection. Module-level `__all__ = ("DjangoListField",)` declared. No scaffold TODOs remain.
- `django_strawberry_framework/__init__.py` — added `from .list_field import DjangoListField  # noqa: E402` to the re-export block and inserted `"DjangoListField"` into the `__all__` tuple in alphabetical position between `"BigInt"` and `"DjangoOptimizerExtension"`. The placeholder TODO block at the old lines 25-34 plus the in-tuple TODO at line 40 were removed. The runtime imports follow ruff/isort's source-module ordering (`.list_field` sorts alphabetically before `.optimizer`); the symbol order in `__all__` is independent and matches the spec.
- `tests/base/test_init.py` — updated the `test_public_api_surface_is_pinned` assertion: removed the TODO docstring paragraph above the function body, removed the in-tuple TODO placeholder, inserted the literal `"DjangoListField"` in alphabetical position between `"BigInt"` and `"DjangoOptimizerExtension"`. Assertion now pins the 8-element tuple in spec line 132's shape.

### Tests added or updated

- `tests/base/test_init.py::test_public_api_surface_is_pinned` — pin updated to include `"DjangoListField"`. No behavior tests added in this slice (Slice 3 owns those per the spec's Slice checklist; spec lines 139-141).

### Validation run

- `uv run ruff format .` — pass. First pass formatted 1 file (`list_field.py`); second pass after annotation edits left all 103 files unchanged.
- `uv run ruff check --fix .` — pass. First pass surfaced 4 `ANN201`/`ANN202` (missing return annotations on `DjangoListField` and the inner `_default` / `_wrap` shapes); resolved by annotating each as `-> Any` (the codebase already allows `Any` via the `ANN401` ignore at `pyproject.toml:95`, and `strawberry.field(...)` has no public return-type alias to import). Final ruff check: `All checks passed!`.
- `git status --short` — slice-intended files only: `M django_strawberry_framework/__init__.py`, `M django_strawberry_framework/list_field.py`, `M tests/base/test_init.py`, plus the artifact file (`?? docs/builder/bld-slice-1-module_factory.md`). The pre-existing baseline (`D docs/builder/bld-*.md` from the prior 0.0.6 cycle, `M docs/spec-016-list_field-0_0_7.md`, `?? docs/builder/bld-slice-0-preimpl_verification.md`, `?? docs/builder/build-016-list_field-0_0_7.md`) is preserved unchanged from the cycle baseline. No tool churn to revert.
- `uv run pytest --no-cov tests/base/test_init.py` — pass (4 tests). `test_public_api_surface_is_pinned`, `test_version`, `test_logger_name_is_django_strawberry_framework`, and `test_optimizer_subpackage_reexports_top_level_logger` all green.

### Implementation notes

- **Return-type annotations added per `ANN201`/`ANN202`.** The plan's step 5 docstring suggestion did not include a return annotation. Ruff (with `ANN` selected in `pyproject.toml:81`, only `ANN002/003/401` ignored) requires return-type annotations on public and nested defs. Annotated each as `-> Any`. The factory returns the result of `strawberry.field(...)` for which Strawberry exposes no public type alias; `_default` returns either a `QuerySet` (sync) or a coroutine that yields a `QuerySet` (async), and the consumer wrappers return whatever `_post_process_consumer_*` returns — `Any` is the honest annotation. The repo's `ANN401` ignore at `pyproject.toml:95` permits this.
- **`Callable` imported from `collections.abc`, not `typing`.** Ruff's `UP035` (deprecated-typing-aliases) rewrites `from typing import Callable` to `from collections.abc import Callable` on autofix. Final import block uses `collections.abc.Callable` and reads consistently with `types/relay.py:26` which already does the same.
- **`__all__ = ("DjangoListField",)` declared at module scope.** Per planner's "Default is include" recommendation in the Implementation discretion items. Matches the scaffold's TODO directive at the old `list_field.py:152`.
- **`from __future__ import annotations` retained.** Per planner's "Default is include" recommendation, consistent with `types/relay.py:23`.
- **`user_resolver = resolver` alias retained.** Per planner's "Default is keep" recommendation; reads as "the consumer's resolver" at the call site and matches the spec pseudocode.
- **The inner `_default` and `_wrap` defs are named per the spec pseudocode (`_default` / `_wrap`), not `_default_resolver` / `_wrap_resolver`.** Per planner's "Default is keep `_default`" recommendation.
- **`ConfigurationError` is NOT imported in this slice.** Per planner's "Default is defer to Slice 2" recommendation. The Slice 2 build pass will add the validation import along with the validation logic; this avoids an F401 in the Slice 1 diff.
- **Async-detection-asymmetry comment placed in-body, not in the docstring.** Per the plan's step 9 guidance ("the in-body comment is preferred because the asymmetry is a code-shape decision"). The comment names both detection mechanisms, names both dispatch sites, and references the spec's Decision 2 subsection by name without duplicating the spec text.

### Notes for Worker 3

- The `_post_process_consumer_sync` / `_post_process_consumer_async` helpers are intentionally at module scope per rev6 H2 (spec line 56) — referentially transparent, unit-testable independently of the factory, no closure capture of `target_type` (passed explicitly). Worker 3 should NOT recommend collapsing them into the factory body.
- The async wrapper is selected statically at factory construction time per rev5 H2 (spec lines 472-477) via `inspect.iscoroutinefunction(user_resolver)`. There is no runtime `inspect.iscoroutine(result)` fallback (rev5 H1 dropped that). Worker 3 should NOT recommend adding a runtime fallback — `functools.partial`-wrapped async resolvers are YAGNI per the rev5 H1 disposition.
- The `# noqa: N802` on the `def DjangoListField(...)` line carries an inline rationale per rev5 L1; the per-line shape is intentional (per-file ignore was rejected during planning because `list_field.py` has only one PascalCase definition).
- The `_default` body's async branch is the rev6 H1 one-liner `return _apply_get_queryset_async(target_type, qs, info)`, not an inner `async def _async_path()` wrapper. Strawberry's `AwaitableOrValue` dispatch awaits the returned coroutine directly. Worker 3 should NOT recommend wrapping it back.
- No shadow file was used during this build pass; the planning shadow at `docs/shadow/django_strawberry_framework__types__relay.overview.md` (recorded in the plan's DRY-analysis section) was the only static-helper artifact referenced. Worker 3's review-time helper run against `django_strawberry_framework/list_field.py` is the appropriate next gate per `docs/builder/BUILD.md` ("the slice adds a new `.py` file of any size, unless it is a pure-class-definition module" — this module has logic, so the helper run is required).
- The validation logic (constructor argument-type checks) is intentionally absent in this slice — Slice 2 owns it per the spec. The constructor accepts whatever shape; bad inputs may produce ugly tracebacks until Slice 2 hardens them.

### Notes for Worker 1 (spec reconciliation)

No spec reconciliation needed; the spec's Slice 1 contract maps cleanly onto the implementation. The only deltas from the plan's literal pseudocode are mechanical lint-driven shape adjustments (`Callable` from `collections.abc` rather than `typing` per `UP035`; `-> Any` return annotations to satisfy `ANN201`/`ANN202`; both already permitted by the repo's existing import patterns and the `ANN401` ignore). These are diff-visible and recorded in the Implementation notes above.

---

## Review (Worker 3)

### Static-inspection helper

Ran `uv run python scripts/review_inspect.py django_strawberry_framework/list_field.py --output-dir docs/shadow --stdout`. The file is a new `.py` file with non-class logic (a factory function plus two module-level helpers), so the helper run is mandatory per `docs/builder/BUILD.md` "When to run the helper during build". Overview captured at `docs/shadow/django_strawberry_framework__list_field.overview.md`.

Helper inventory walk:

- **Imports (9 total)**: standard/third-party (`__future__.annotations`, `inspect`, `collections.abc.Callable`, `typing.Any`), strawberry (`strawberry`, `strawberry.types.Info`, `strawberry.utils.inspect.in_async_context`), django (`django.db.models`), local (`.types.relay._apply_get_queryset_*`). Every import is justified by the spec — Decision 3 Option A (relay-helper reuse), rev3 M7 (canonical `in_async_context` site), rev4 H1 (`Info` annotation), rev5 H3 (Slice 0 verified the path). No cross-package or boundary-crossing imports.
- **Symbols (6 total)**: two module-level helpers (`_post_process_consumer_sync` at lines 29-34, `_post_process_consumer_async` at 37-42), the factory `DjangoListField` at 45-109, and three nested closures (`_default`, async `_wrap`, sync `_wrap`). Module-scope placement of the helpers is mandatory per rev6 H2; the nested-closure shape of `_default` / `_wrap` is mandatory per the closure-capture-of-`target_type` design (rev2 H3 + rev4 H1).
- **Control-flow hotspots**: only `DjangoListField` itself triggers, at 65 lines / 2 branch nodes — below the default 8-branch threshold and not actually a hotspot, but the helper flags long-line functions too. The 65 lines include the docstring (5 lines), the async-detection asymmetry comment (8 lines), and three nested-`def` blocks; the executable body is ~30 lines. Not a finding.
- **Django/ORM markers (7 total)**: every entry is justified.
  - Line 18: `from .types.relay import _apply_get_queryset_async, _apply_get_queryset_sync` — Decision 3 Option A reuse (justified).
  - Lines 32, 40: `isinstance(result, models.QuerySet)` — rev2 H1 graphene-django-parity branch (justified).
  - Lines 33, 41: `_apply_get_queryset_sync` / `_apply_get_queryset_async` calls in the consumer post-processing helpers — Decision 3 reuse (justified).
  - Lines 75, 76: `_apply_get_queryset_async` / `_apply_get_queryset_sync` calls in the default-resolver body — Decision 2 default-resolver shape (justified).
  - **No use of `_meta`, `select_related`, `prefetch_related`, `_prefetched_objects_cache`, `Prefetch`, or `OptimizationPlan`** — correct for Slice 1; optimizer cooperation is implicit via "return a QuerySet at root" (Decision 4), not via direct optimizer touchpoints.
- **Calls of interest (8 total)**: 4 `isinstance()` calls (two each in `_post_process_consumer_sync` / `_post_process_consumer_async` — Manager-then-QuerySet check pattern), 2 `_apply_get_queryset_sync()` calls (one in default-resolver sync branch, one in sync consumer helper), 2 `_apply_get_queryset_async()` calls (mirror). The isinstance-Manager-then-QuerySet pattern is the rev4 M1 mandatory order ("Manager → QuerySet coercion BEFORE applying get_queryset"); the implementation honors it at both helpers (line 30 + 32, line 38 + 40).
- **TODO comments**: zero. The rev6 L2 scaffold-TODO cleanup landed cleanly.
- **Repeated string literals**: zero. No repeated-literal DRY signal.

For `django_strawberry_framework/__init__.py` and `tests/base/test_init.py`: helper skipped, **reason: low-surface; pure re-export / pin assertion**, per the slice prompt.

### High

None.

### Medium

None.

### Low

None.

### DRY findings

- The `_post_process_consumer_sync` / `_post_process_consumer_async` helpers share an identical sync/async body shape — `if Manager: result = result.all(); if QuerySet: return [await] _apply_get_queryset_*; return result`. Collapsing the two into a single dispatcher would require a runtime branch on `in_async_context()` inside what the spec's rev5 H2 explicitly pins as a per-construction-static choice for consumer resolvers. The duplication is justified per Decision 2's "Async-detection asymmetry — intentional, not a harmonization candidate" subsection (spec lines 472-477). Not a finding; recorded here so the cross-slice integration pass can confirm the same justification still holds after Slices 3-5 land.
- The factory's nested `_wrap` (sync) and `async _wrap` arms also share post-processing shape with the consumer helpers — but the wrapper has one extra step (`await user_resolver(...)` in the async arm). Inlining the helpers into the wrapper would lose the module-scope-helpers-are-unit-testable property (rev6 H2's stated justification); the current shape keeps the helper layer thin and the wrapper layer one-line-each, which is the maximally DRY readable shape for this dispatch site.
- The `_apply_get_queryset_*` reuse from `types/relay.py` is exactly the kind of DRY win the plan called for (avoiding re-implementing the coroutine-in-sync `ConfigurationError` rejection). Decision 3 Option A's "Option B becomes the right move when a third call site needs the helpers" guidance applies: when `DjangoConnectionField` ships in `0.0.9` and needs the same helpers, the relocation to `utils/get_queryset.py` becomes net-positive. No relocation needed in `0.0.7`.

No new DRY findings.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` adds exactly one symbol: `DjangoListField`. The import line is `from .list_field import DjangoListField  # noqa: E402` placed alphabetically between `from strawberry import auto` and `from .optimizer import DjangoOptimizerExtension`; the `__all__` insertion is `"DjangoListField"` between `"BigInt"` and `"DjangoOptimizerExtension"` (alphabetical). Authorized by spec line 161 ("One new public export (`DjangoListField`) — the only addition to `__all__` in this slice") and Decision 1's public-export-surface subsection at spec lines 369-373. No other additions to `__all__`; no removals; no renames.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- **Rev6 H1 collapsed one-liner.** Line 75's `return _apply_get_queryset_async(target_type, qs, info)` inside the `if in_async_context():` branch — no inner `async def _async_path()` wrapper. Strawberry's `AwaitableOrValue` dispatch awaits the returned coroutine directly. This is the exact post-rev6-H1 shape; future maintainers reading the body should leave it alone.
- **Rev6 H2 module-scope helpers.** `_post_process_consumer_sync` and `_post_process_consumer_async` are defined at column 0 (lines 29 and 37), not nested inside `DjangoListField`. They take `target_type` and `info` as explicit parameters per rev5 M4. Referentially transparent, unit-testable independently of the factory.
- **Rev6 H3 `_consumer` suffix.** The helpers carry the `_consumer` suffix in the name; the one-line comment above the helpers documents the `_default`-bypasses-helpers justification (lines 23-26). A future maintainer asking "why doesn't `_default` use these?" gets the answer from the name and the inline comment together.
- **Rev5 L1 `# noqa: N802` placement.** Line 45 carries `# noqa: N802  # PascalCase for graphene-django parity — consumer usage is `DjangoListField(BranchType)``. Per-line shape (not per-file ignore), with the rationale inline. Ruff's `N802` only suppresses on this single line.
- **Rev5 H2 async-detection-asymmetry comment.** Lines 58-65 in-body comment names both detection mechanisms (`in_async_context()` per-call for `_default`, `inspect.iscoroutinefunction(user_resolver)` per-construction for the consumer wrapper), names both dispatch sites, and references the spec's Decision 2 subsection by name without duplicating the spec text. A future maintainer noticing the asymmetry and tempted to "harmonize" will find the explicit "intentional, not a harmonization candidate" pointer.
- **Rev4 H2 + rev5 H1 async wrapper.** Line 81's `if inspect.iscoroutinefunction(user_resolver):` selects sync-vs-async statically at factory construction time. The async arm at lines 83-92 `await`s the consumer coroutine BEFORE handing the result to `_post_process_consumer_async`, so the isinstance-QuerySet branch in the helper sees the awaited value, not the coroutine. No runtime `inspect.iscoroutine(result)` fallback — rev5 H1's YAGNI choice held.
- **Rev2 H1 + rev4 M1 coercion order.** Inside both `_post_process_consumer_*` helpers, `Manager → QuerySet` coercion (`result = result.all()`) runs BEFORE the isinstance-QuerySet branch. A `Manager`-shaped consumer return is threaded through `_apply_get_queryset_*` exactly like a direct `QuerySet`-shaped return.
- **Alphabetical `__all__` insertion.** `"DjangoListField"` sits between `"BigInt"` and `"DjangoOptimizerExtension"` per the cycle-0 carry-forward and Decision 1's public-export-surface subsection. The runtime import is placed between `from strawberry import auto` and `from .optimizer import DjangoOptimizerExtension` — the import-block sort is by module path (`.list_field` < `.optimizer`), so the alphabetical position is maintained at both the runtime-import block and the `__all__` tuple.
- **Verbatim `_apply_get_queryset_*` reuse.** No re-implementation of the coroutine-in-sync `ConfigurationError` rejection from `types/relay.py:215-218`. The same error shape covers both Relay and list paths, per Decision 3 Option A and the spec's "same `ConfigurationError` shape covers both Relay and list paths" sub-bullet.
- **`__all__ = ("DjangoListField",)` in-module declaration.** Line 20. IDE / static-analyzer signal that the module's exported surface is the single symbol, matching the package-level `__all__`.
- **Zero scaffold TODOs remain.** Grep confirms `django_strawberry_framework/list_field.py`, `django_strawberry_framework/__init__.py`, and `tests/base/test_init.py` are free of `# TODO(spec-016, ...)` markers; the only `spec-016` mentions are intentional spec references in the production docstring and an anchor comment, not TODO scaffolds.

### Temp test verification

- `docs/builder/temp-tests/slice-1/test_factory_smoke.py` — three temp tests run during review:
  - `test_factory_returns_strawberry_field_instance` — confirms the factory's return value is a `strawberry.types.field.StrawberryField` instance, which is what `@strawberry.type`'s class-body walk discovers. Passes.
  - `test_post_process_consumer_sync_coerces_manager_to_queryset` — confirms the `Manager → QuerySet` coercion via `.all()` runs BEFORE the isinstance-QuerySet branch (rev2 H1 + rev4 M1). Passes.
  - `test_post_process_consumer_sync_passes_list_through` — confirms a Python `list` return bypasses `_apply_get_queryset_sync` entirely (rev2 H1 bypass-via-list contract). Passes.

  Disposition: **deleted at end-of-pass**. The factory smoke test's StrawberryField-instance assertion overlaps with the Slice 0 end-to-end introspection verification already recorded in `docs/builder/bld-slice-0-preimpl_verification.md`; the helper coercion / list-passthrough tests overlap with Slice 3's planned behavior tests (`test_djangolistfield_consumer_resolver_queryset_return_gets_get_queryset_applied` and `test_djangolistfield_consumer_resolver_python_list_return_passes_through` per spec lines 139-140). No promotion to permanent suite required; the directory was cleaned at end-of-pass.

### Notes for Worker 1 (spec reconciliation)

- **No spec reconciliation needed for Slice 1.** Every Slice 1 contract sub-bullet at spec lines 115-133 is honored in the diff. The lint-driven shape deltas Worker 2 surfaced (`Callable` from `collections.abc` per `UP035`; `-> Any` return annotations per `ANN201`/`ANN202`) are within the spec's allowed convention pattern (`types/relay.py:26` already imports `Callable` from `collections.abc`; `ANN401` ignore at `pyproject.toml:95` permits `Any`-annotated returns).
- **Forward-looking note for Slice 2 review (carry-forward only).** Slice 2 will add the `ConfigurationError` import and the four constructor validations per Decision 5 (spec lines 542-555). The error-message shape pattern is `<Symbol> <constraint>; got <repr>.` mirroring `types/base.py:_format_unknown_fields_error`; the `__django_strawberry_definition__` discriminator anchor sits at `types/base.py:245` per Decision 5's rev3 M3 anchor (spec line 548). Worker 1's final-verification pass for Slice 1 has no spec-edit to make on Slice 2's behalf.
- **`strawberry.field`'s `directives=` accepts `Sequence[object] | None`, the factory pins `tuple = ()`.** Verified via `inspect.signature(strawberry.field)`. The factory's `tuple = ()` parameter annotation is more restrictive than Strawberry's actual accept-set but does not break anything — consumers passing a tuple work; consumers passing a list also work at runtime (the annotation is not enforced). No finding; recorded only because the spec at line 130 uses the phrase "pass-through" and a future reader might wonder why the factory's narrower annotation does not surface as a type error.

### Review outcome

`review-accepted`. Every Slice 1 spec checklist sub-bullet (spec lines 115-133) is addressed in the diff; the rev6 H1 / H2 / H3 contracts are honored; the rev5 L1 `# noqa: N802` is present with the inline rationale; the rev5 H2 async-detection-asymmetry comment is in place; the rev4 H1 / H2 resolver signatures and async-detection mechanism are pinned; the rev2 H1 / rev4 M1 coercion order is correct; the rev6 L2 scaffold-TODO cleanup is complete at all three sites; the alphabetical `__all__` insertion is correct; the focused `tests/base/test_init.py` suite passes. Public-surface check confirms exactly one symbol added, authorized by spec line 161. No High/Medium/Low findings.

---

## Final verification (Worker 1)

- **Spec slice checklist**: every `- [ ]` in the Plan's `### Spec slice checklist (verbatim)` has been ticked `- [x]`. Walked all twelve sub-bullets against the diff (`django_strawberry_framework/list_field.py:1-110`, `django_strawberry_framework/__init__.py:20,30`, `tests/base/test_init.py:35-44`). Every contract lands; no silent omissions. No deferrals required.
- **DRY check across this slice and prior accepted slices**:
  - Prior accepted slice: Slice 0 (pre-implementation verification spike; no code landed).
  - Slice 1 reuses `_apply_get_queryset_sync` / `_apply_get_queryset_async` from `django_strawberry_framework/types/relay.py:199` / `:225` via `from .types.relay import _apply_get_queryset_async, _apply_get_queryset_sync` at `list_field.py:18`. No re-implementation of the coroutine-in-sync `ConfigurationError` rejection (per Decision 3 Option A).
  - `in_async_context` imported from the canonical `strawberry.utils.inspect` site at `list_field.py:16`, matching `types/relay.py:33` per rev3 M7. No fork.
  - `_post_process_consumer_sync` (line 29) and `_post_process_consumer_async` (line 37) are at module scope (column 0), NOT factory-scope, per rev6 H2. The `_consumer` suffix per rev6 H3 is present in both helper names, and the one-line bypass-justification comment is at lines 23-26.
  - Default-resolver async branch at `list_field.py:70-75` is the rev6 H1 one-liner — `return _apply_get_queryset_async(target_type, qs, info)` — no inner `async def _async_path()` wrapper. Strawberry's AwaitableOrValue dispatch awaits the returned coroutine directly.
  - No new repeated literals, no near-copies of existing helpers, no parallel data flows. The cross-slice helper-reuse posture is exactly what Decision 3 prescribes.
- **Existing tests still pass**: `uv run pytest --no-cov tests/base/test_init.py` — 4 passed in 0.04s. Confirms `test_public_api_surface_is_pinned` accepts the new 8-element `__all__` tuple and the other three `tests/base/test_init.py` tests (`test_version`, `test_logger_name_is_django_strawberry_framework`, `test_optimizer_subpackage_reexports_top_level_logger`) remain green. No `--cov*` flag used per BUILD.md "Coverage is the maintainer's gate, not a worker's tool".
- **Spec reconciliation**: Worker 2's Build report at `Notes for Worker 1 (spec reconciliation)` states no spec edit needed; Worker 3's Review at the same section confirms no spec reconciliation required and includes only a forward-looking carry-forward for Slice 2. Walked both notes against the diff and the spec — no gap, conflict, or unstated assumption surfaced. Spec status line (`docs/spec-016-list_field-0_0_7.md:4`) reads `draft (revision 6, post-rev5 scaffolding review)` — still accurate; rev6 is current; Slice 1 ships within the rev6 contract without triggering a re-revision. No spec edits required for Slice 1.
- **Final status**: `final-accepted`. Every spec sub-checklist sub-bullet ticked; no DRY violations introduced; focused tests pass; no spec reconciliation needed.

### Summary

Slice 1 ships the `DjangoListField` factory function at `django_strawberry_framework/list_field.py` (110 lines) — a closure-capturing factory that returns `strawberry.field(resolver=<wrapped>, description=..., deprecation_reason=..., directives=...)` with two dispatch shapes: a default resolver that pulls `target_type.__django_strawberry_definition__.model._default_manager.all()` and threads it through `_apply_get_queryset_{sync,async}` per the runtime `in_async_context()` branch (rev6 H1 one-liner async path; no inner `async def` wrapper), and a consumer-resolver wrapper that selects sync-vs-async statically at factory construction time via `inspect.iscoroutinefunction(user_resolver)` (rev4 H2 + rev5 H1 — no runtime fallback). Module-scope post-processing helpers (`_post_process_consumer_sync` / `_post_process_consumer_async` per rev6 H2 + rev6 H3) coerce `Manager → QuerySet` BEFORE applying `get_queryset` (rev4 M1), and pass Python lists / generators through unchanged (rev2 H1 graphene-django parity). The factory carries `# noqa: N802` with an inline rationale per rev5 L1 and an in-body comment near the dispatch branch documenting the async-detection asymmetry per rev5 H2. Public surface gains exactly one symbol — `DjangoListField` — re-exported from `django_strawberry_framework/__init__.py:20,30` in alphabetical position between `BigInt` and `DjangoOptimizerExtension`, with the pinned `__all__` assertion in `tests/base/test_init.py:35-44` updated to match. Zero scaffold TODOs remain across the three touched files per rev6 L2.

### Spec changes made (Worker 1 only)

No spec edits required for Slice 1.
