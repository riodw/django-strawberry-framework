# Build: Slice 1 — Helper module + `BigInt` redefinition

Spec reference: `docs/spec-020-scalar_map_helper-0_0_7.md` (lines 38–41 for the slice sub-checks; lines 224–356 for Decisions 2/3/6; pinned-shape code block at spec lines 252–300)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - `django_strawberry_framework/scalars.py::_parse_bigint` and `django_strawberry_framework/scalars.py::_serialize_bigint` stay verbatim. The strict-parser and strict-serializer functions are pure (no Strawberry coupling) and continue to back the migrated `_BIGINT_SCALAR_DEFINITION`. No changes to body, signature, or docstring.
  - `django_strawberry_framework/scalars.py` #`"_BIGINT_STRING_PATTERN"` regex constant stays as-is — referenced by `_parse_bigint` only.
  - `django_strawberry_framework/scalars.py` module docstring (lines 1–11) stays as-is — describes the BigInt wire-format contract, which Decision 3 preserves verbatim.
  - The existing `from typing import Any, NewType` import is preserved (both names remain in use: `Any` annotates `_parse_bigint(value: Any)`, `_serialize_bigint(value: Any)`, and now also `**config_kwargs: Any`; `NewType` builds the bare `BigInt = NewType("BigInt", int)`).
  - The existing `import strawberry` import stays — `strawberry.scalar(name=..., serialize=..., parse_value=...)` is the no-warning overload entry point at `.venv/lib/python3.10/site-packages/strawberry/types/scalar.py::scalar #"if cls is None and name is not None"`.
  - `django_strawberry_framework/__init__.py` already groups scalar re-exports on one line (`from .scalars import BigInt`). The plan widens the existing line rather than adding a new import statement, preserving the file's "one import per source module" convention.
- **New helpers justified.**
  - One new public symbol: `strawberry_config` factory in `django_strawberry_framework/scalars.py`. Single responsibility: build a fresh `StrawberryConfig` instance whose `scalar_map` is the package's defaults merged with the caller's `extra_scalar_map`, while forwarding every non-`scalar_map` kwarg to the upstream `StrawberryConfig(...)` constructor. Call sites: consumer `strawberry.Schema(query=..., config=strawberry_config(), extensions=[...])` invocations (one per consumer schema, plus the fakeshop migration in Slice 3, plus the two Slice 2 integration tests in `tests/test_scalars.py`).
  - One new module-level data structure: `_PACKAGE_SCALAR_MAP: dict[object, ScalarDefinition]`. Single responsibility: the canonical mapping of package-defined scalar `NewType`s (today only `BigInt`) to their `ScalarDefinition`s. The factory reads it; future package scalars (`Upload` in `TODO-ALPHA-028-0.0.11`) join by appending a new entry. Justified because the alternative (inline literal dict inside the factory body) would force a fresh `strawberry.scalar(...)` call per `strawberry_config()` invocation, multiplying `ScalarDefinition` allocations and frustrating the "single source of truth for package scalars" reading.
  - One new module-level definition: `_BIGINT_SCALAR_DEFINITION: ScalarDefinition` produced by the no-warning `strawberry.scalar(name="BigInt", serialize=_serialize_bigint, parse_value=_parse_bigint)` overload. Single responsibility: the canonical `ScalarDefinition` for `BigInt`. Referenced by `_PACKAGE_SCALAR_MAP`. Justified because building the definition inline inside `_PACKAGE_SCALAR_MAP = {BigInt: strawberry.scalar(...)}` would obscure the definition; the named module-level binding makes the symbol greppable.
- **Duplication risk avoided.**
  - The naive implementation could re-wrap `BigInt` via `strawberry.scalar(NewType("BigInt", int), name=..., ...)` (the deprecated overload). Decision 3 forbids this; the spec's pinned shape uses the `cls is None and name is not None` branch at `.venv/lib/python3.10/site-packages/strawberry/types/scalar.py::scalar #"if cls is None and name is not None"`, which returns a `ScalarDefinition` directly without invoking the deprecation-emitting `wrap()` body.
  - The naive implementation could build the merged `scalar_map` by `_PACKAGE_SCALAR_MAP.update(extra)`, which would mutate the module-level dict across calls. The spec's pinned shape (spec lines 297–298) constructs a fresh `merged: dict[object, ScalarDefinition] = dict(_PACKAGE_SCALAR_MAP)` then `merged.update(extra)`, so module state is never mutated and each call returns an independent `StrawberryConfig`. Worker 2 follows the pinned shape verbatim.
  - The naive implementation could leave the `warnings.catch_warnings()` suppression block in place "defensively." Decision 6 forbids this; the block (current `scalars.py` lines 80–103) is removed wholesale, along with the now-unused `import warnings`.
  - The naive implementation could route `extra_scalar_map` through `**config_kwargs` (i.e., accept `scalar_map=` as a kwarg). Decision 2 / Decision 4 require a hard `ValueError` at `if "scalar_map" in config_kwargs`. Worker 2 mirrors the pinned shape's explicit check.
  - The naive implementation could pre-validate the `extra_scalar_map` key shape. Spec edge-cases section (lines 437) and Error shapes (spec lines 200–203) deliberately disclaim this — Strawberry's own `Mapping[object, ScalarDefinition]` contract owns key validation; the helper does not duplicate it.
- **Helper not required for this planning pass.** `scripts/review_inspect.py` is **skipped**: `django_strawberry_framework/scalars.py` is 103 source lines (verified via `wc -l`), below the 150-line threshold pinned in `docs/builder/BUILD.md` "When to run the helper during build"; the file is not under `django_strawberry_framework/optimizer/` or `django_strawberry_framework/types/`. The threshold criterion governs Worker 1's planning helper requirement; both conditions miss, so the helper is not required. Worker 3 will run the helper at review time per its own threshold rules (30+ new logic lines in any file under `django_strawberry_framework/`).

### Implementation steps

Line numbers below are pin-at-write-time navigational hints against the current source. Verify against the file before editing — Worker 2 should grep for the cited substring rather than seek by raw line number.

1. **`django_strawberry_framework/scalars.py` — add imports.**
   - Replace the existing `import re`, `import warnings`, `from typing import Any, NewType`, `import strawberry` block (current `scalars.py` lines 13–17) with the new import set, preserving the file's import-style convention (stdlib first, then `collections.abc`, then `strawberry` subpackages).
   - Final import shape after the edit, per the pinned code at spec lines 256–261:
     - `import re` — retained (used by `_BIGINT_STRING_PATTERN` only).
     - `from collections.abc import Mapping` — **added** (annotates `extra_scalar_map: Mapping[object, ScalarDefinition] | None`).
     - `from typing import Any, NewType` — retained (`Any` annotates `_parse_bigint`, `_serialize_bigint`, `**config_kwargs`; `NewType` builds `BigInt`).
     - `import strawberry` — retained (no-warning `strawberry.scalar(name=..., ...)` overload entry point).
     - `from strawberry.schema.config import StrawberryConfig` — **added** (the factory's return type and constructor target).
     - `from strawberry.types.scalar import ScalarDefinition` — **added** (annotates `_BIGINT_SCALAR_DEFINITION` and `_PACKAGE_SCALAR_MAP`).
     - `import warnings` — **removed** (no remaining use after Step 4 below).
   - Discretion: Worker 2 chooses the in-block ordering of the four `strawberry`-rooted imports (the package convention is alphabetical, but spec's pinned code at lines 256–261 lists `strawberry` before its submodule imports; either is consistent with the existing file).

2. **`django_strawberry_framework/scalars.py` — redefine `BigInt` as a bare `NewType`.**
   - Replace the current `with warnings.catch_warnings(): ... BigInt = strawberry.scalar(NewType("BigInt", int), name="BigInt", serialize=_serialize_bigint, parse_value=_parse_bigint)` block (current `scalars.py` #`"with warnings.catch_warnings()"` through the closing `)`, lines 80–103) with the pinned shape from spec lines 267–273:
     - `BigInt = NewType("BigInt", int)` — bare `NewType`, no `strawberry.scalar(...)` wrapper.
     - `_BIGINT_SCALAR_DEFINITION: ScalarDefinition = strawberry.scalar(name="BigInt", serialize=_serialize_bigint, parse_value=_parse_bigint)` — the no-warning overload (`cls is None and name is not None` branch at `.venv/lib/python3.10/site-packages/strawberry/types/scalar.py::scalar #"if cls is None and name is not None"`).
   - The redefinition replaces the suppression block in-place. Per Decision 6, no replacement comment "documents the removed suppression" — code is the source of truth.

3. **`django_strawberry_framework/scalars.py` — add `_PACKAGE_SCALAR_MAP`.**
   - Immediately after `_BIGINT_SCALAR_DEFINITION`, add the module-level dict per spec lines 275–277:
     - `_PACKAGE_SCALAR_MAP: dict[object, ScalarDefinition] = {BigInt: _BIGINT_SCALAR_DEFINITION}`.
   - The annotation `dict[object, ScalarDefinition]` matches the upstream `Mapping[object, ScalarDefinition]` shape at `.venv/lib/python3.10/site-packages/strawberry/schema/config.py::StrawberryConfig #"scalar_map: Mapping[object, ScalarDefinition]"`.

4. **`django_strawberry_framework/scalars.py` — add the `strawberry_config` factory.**
   - At module scope after `_PACKAGE_SCALAR_MAP`, define the factory verbatim per spec's pinned code at lines 280–299:
     ```python
     def strawberry_config(
         *,
         extra_scalar_map: Mapping[object, ScalarDefinition] | None = None,
         **config_kwargs: Any,
     ) -> StrawberryConfig:
         if "scalar_map" in config_kwargs:
             raise ValueError(
                 "strawberry_config() owns scalar_map; pass consumer scalars with extra_scalar_map=..."
             )
         extra = dict(extra_scalar_map) if extra_scalar_map else {}
         collisions = _PACKAGE_SCALAR_MAP.keys() & extra.keys()
         if collisions:
             raise ValueError(
                 "strawberry_config(extra_scalar_map=...) cannot redeclare package-defined scalars: "
                 f"{', '.join(sorted(getattr(k, '__name__', repr(k)) for k in collisions))}. "
                 "Define a Strawberry custom scalar of a different NewType / class to register under a separate key."
             )
         merged: dict[object, ScalarDefinition] = dict(_PACKAGE_SCALAR_MAP)
         merged.update(extra)
         return StrawberryConfig(scalar_map=merged, **config_kwargs)
     ```
   - Worker 2 also adds a function docstring summarizing the contract (one short paragraph naming the keyword-only `extra_scalar_map`, the `**config_kwargs` passthrough, the `scalar_map=` rejection, and the collision policy from Decision 4). The docstring body is at Worker 2's discretion — see `Implementation discretion items` below.

5. **`django_strawberry_framework/scalars.py` — remove the `warnings.catch_warnings()` block and `import warnings`.**
   - Already covered by Step 1 (remove `import warnings`) and Step 2 (replace the `with warnings.catch_warnings(): ...` block with the bare `NewType` + `_BIGINT_SCALAR_DEFINITION` pair).
   - Also remove the 12-line explanatory comment at `scalars.py` #`"Strawberry emits"` (current lines 80–91) — the comment described the suppression block being removed; it is dead documentation post-migration. Per Decision 6 alternatives-rejected list ("Replace the suppression with a comment. Rejected: code is the source of truth"), no replacement comment is added.

6. **`django_strawberry_framework/__init__.py` — widen the `from .scalars import` line.**
   - At `django_strawberry_framework/__init__.py` #`"from .scalars import BigInt"` (current line 23), change the import to `from .scalars import BigInt, strawberry_config  # noqa: E402`. The `noqa: E402` marker is preserved (the existing line carries it because the logger declaration at the top of the file places this import after non-import code).

7. **`django_strawberry_framework/__init__.py` — append `"strawberry_config"` to `__all__`.**
   - At `django_strawberry_framework/__init__.py` #`"__all__"` (current lines 28–37), append `"strawberry_config"` as the **last** element, immediately after `"finalize_django_types"`. The resulting tuple, per spec line 448, is `("BigInt", "DjangoListField", "DjangoOptimizerExtension", "DjangoType", "OptimizerHint", "__version__", "auto", "finalize_django_types", "strawberry_config")`. Justification for trailing position: Python's default `sorted()` for the tuple is ASCII case-sensitive (uppercase 66–90 → underscore 95 → lowercase 97–122); `"strawberry_config"` (`s` = 115) sorts after `"finalize_django_types"` (`f` = 102). The existing tuple is sorted by that convention and the new element follows it.
   - Preserve trailing comma per `AGENTS.md` line 17 (COM812 — trailing comma on multi-line tuples).

8. **Formatting sweep.** After the edits, Worker 2 runs `uv run ruff format .` and `uv run ruff check --fix .` per `AGENTS.md` line 15 / `START.md` line 26. The 110-line line length (AGENTS.md line 16) applies; the longest line in the spec's pinned code is the `ValueError(...)` string-formatted message, which fits at 110 if the f-string spans two `+`-concatenated lines as in the spec — ruff format may rewrap; either shape is acceptable.

### Test additions / updates

**Slice 1 ships zero new tests.** Per the spec's Slice checklist (spec lines 42–48), all test work — the 13 factory tests, the 2 integration tests, the `tests/base/test_init.py::test_public_api_surface_is_pinned` `__all__` update, and the 10 schema-construction migrations in `tests/types/test_converters.py` — is owned by **Slice 2**. Worker 2 for Slice 1 MUST NOT add or modify tests; doing so violates the spec's slice-boundary contract.

A practical consequence: the existing `tests/base/test_init.py::test_public_api_surface_is_pinned` exact-tuple assertion will FAIL after Slice 1 lands (because `__all__` now carries `"strawberry_config"` but the pinned assertion does not). This is expected — Slice 2 is the immediate next slice in the build order and updates that assertion in lockstep with the rest of the test additions. Worker 2 for Slice 1 records the expected test failure in the build report's `### Notes for Worker 3` so the reviewer is not surprised.

Per `docs/builder/BUILD.md` "Coverage is the maintainer's gate, not a worker's tool", no `pytest --cov*` invocation appears in this slice. If Worker 2 chooses to run a focused test invocation during Slice 1 (e.g., to confirm the package still imports), the invocation MUST include `--no-cov` to opt out of `pytest.ini`'s auto-applied `--cov`. The plan does not require a test run for Slice 1; `uv run ruff format .` and `uv run ruff check --fix .` are the only required commands.

### Implementation discretion items

These are choices Worker 1 has assessed and decided are at Worker 2's discretion. None are architectural questions; each has two (or more) equally valid shapes and the spec does not pin one over the other.

1. **Exact wording of the `_PACKAGE_SCALAR_MAP` initializer.** Either `_PACKAGE_SCALAR_MAP: dict[object, ScalarDefinition] = {BigInt: _BIGINT_SCALAR_DEFINITION}` (matching spec lines 275–277) or the equivalent `dict(...)` constructor form is acceptable. The spec's pinned shape uses the brace literal; matching it is the lowest-friction choice but not load-bearing.
2. **Exact wording of the merged-dict construction inside the factory.** Either `merged: dict[object, ScalarDefinition] = dict(_PACKAGE_SCALAR_MAP); merged.update(extra)` (matching spec line 297–298) or `merged: dict[object, ScalarDefinition] = {**_PACKAGE_SCALAR_MAP, **extra}` is acceptable. Both produce a fresh `dict` per call and neither mutates `_PACKAGE_SCALAR_MAP`. The spec uses the constructor + `.update(...)` form; matching it is the lowest-friction choice.
3. **`strawberry_config(...)` function docstring body.** Worker 1 has decided the factory MUST carry a docstring (the file's other public functions — `_parse_bigint`, `_serialize_bigint` — carry docstrings; consistency demands one for the new public factory). The wording is at Worker 2's discretion. A short paragraph naming (a) the keyword-only `extra_scalar_map` and its merge semantics, (b) the `**config_kwargs` passthrough to `StrawberryConfig(...)`, (c) the `scalar_map=` rejection per Decision 2, and (d) the collision-raises policy per Decision 4 covers the contract. Linking to the relevant `docs/GLOSSARY.md` entry (`#strawberry_config`, planned in Slice 4) is optional — the entry doesn't exist yet during Slice 1, so a forward link would be a dangling reference. Recommend Worker 2 omits the link and lets Slice 4 land the GLOSSARY entry independently.
4. **Per-import-line ordering of the four `strawberry`-rooted imports.** The spec's pinned code (spec lines 256–261) lists `import strawberry` before `from strawberry.schema.config import StrawberryConfig` and `from strawberry.types.scalar import ScalarDefinition`. Ruff's import sorter (the package uses ruff format) may rewrite the block on save. Whatever shape ruff format settles on is acceptable; the spec's ordering is a hint, not a contract.
5. **Inclusion of an inline comment near `_BIGINT_SCALAR_DEFINITION` pointing at the no-warning overload location at `.venv/lib/python3.10/site-packages/strawberry/types/scalar.py`.** Optional. A short comment ("# `strawberry.scalar(name=..., ...)` is the no-warning overload — returns a ScalarDefinition directly.") helps a future reader understand why the call shape lacks a class argument; the comment is not required. Worker 2's discretion.
6. **Format of the `ValueError` collision message's joined-names list.** The spec pins `', '.join(sorted(getattr(k, '__name__', repr(k)) for k in collisions))` — comma-separated, sorted, `__name__` with `repr` fallback. Matching this form verbatim is recommended because the Slice 2 test `test_strawberry_config_collision_with_package_scalar_raises_value_error` will assert on the exact message substring. Any deviation here would force a parallel change in Slice 2. Worker 2's discretion to choose a different separator or sort order, but if they do, they MUST note it in `### Notes for Worker 1 (spec reconciliation)` so Slice 2's test assertions get updated.

### Spec slice checklist (verbatim)

- [x] Slice 1: Helper module + `BigInt` redefinition
  - [x] [`django_strawberry_framework/scalars.py`](../django_strawberry_framework/scalars.py): redefine `BigInt` as a bare `NewType("BigInt", int)` (the deprecation-prone wrapping in `strawberry.scalar(NewType, ...)` is removed); add a module-level `_BIGINT_SCALAR_DEFINITION: ScalarDefinition` built via the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload (the `cls is None and name is not None` branch at [`.venv/lib/python3.10/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`](../.venv/lib/python3.10/site-packages/strawberry/types/scalar.py) returns a `ScalarDefinition` directly without emitting `DeprecationWarning`); add a module-level `_PACKAGE_SCALAR_MAP: dict[object, ScalarDefinition]` mapping the `BigInt` `NewType` to the definition; add the public `strawberry_config(*, extra_scalar_map: Mapping[object, ScalarDefinition] | None = None, **config_kwargs: Any) -> StrawberryConfig` factory per [Decision 2](#decision-2--helper-api-shape-and-module-location) (keyword-only `extra_scalar_map`; arbitrary `**config_kwargs` forwarded to `StrawberryConfig(...)`; `scalar_map=` rejected with `ValueError`); remove the `with warnings.catch_warnings(): warnings.filterwarnings("ignore", message="Passing a class to strawberry.scalar", ...)` block at the bottom of the file per [Decision 6](#decision-6--remove-the-warningscatch_warnings-suppression-block).
    - Import surface changes inside `scalars.py`: ADD `from collections.abc import Mapping`, `from strawberry.schema.config import StrawberryConfig`, `from strawberry.types.scalar import ScalarDefinition`. KEEP `from typing import Any, NewType` (`Any` is already used by `_parse_bigint(value: Any)` / `_serialize_bigint(value: Any)` and now also annotates `**config_kwargs: Any` on the helper; `NewType` is the bare-redefinition path). REMOVE `import warnings` (no remaining use after the suppression block is dropped per [Decision 6](#decision-6--remove-the-warningscatch_warnings-suppression-block)).
  - [x] [`django_strawberry_framework/__init__.py`](../django_strawberry_framework/__init__.py): add `strawberry_config` to the explicit re-export list immediately after `BigInt` (the import line stays in the existing `from .scalars import BigInt` group, widened to `from .scalars import BigInt, strawberry_config`); append `"strawberry_config"` to `__all__` as the **last** element, after `"finalize_django_types"`. Python's default `sorted()` for the tuple is ASCII case-sensitive (uppercase 66–90 → underscore 95 → lowercase 97–122), so `"strawberry_config"` (`s` = 115) sorts AFTER `"finalize_django_types"` (`f` = 102); the existing tuple is sorted by that rule (verified at [`django_strawberry_framework/__init__.py #"__all__"`](../django_strawberry_framework/__init__.py)) and the new element follows the same convention. `BigInt` stays in `__all__` (consistent with the recommended "BigInt as a direct annotation" usage pattern from the card body).

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/scalars.py` — rewrote the module per spec Decision 3's pinned shape: removed `import warnings`, added `from collections.abc import Mapping`, `from strawberry.schema.config import StrawberryConfig`, `from strawberry.types.scalar import ScalarDefinition`; redefined `BigInt` as a bare `NewType("BigInt", int)`; added module-level `_BIGINT_SCALAR_DEFINITION` built via the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload; added module-level `_PACKAGE_SCALAR_MAP`; added the public `strawberry_config(*, extra_scalar_map=None, **config_kwargs) -> StrawberryConfig` factory with the `scalar_map=` rejection branch and the collision-raises branch; removed the `warnings.catch_warnings()` suppression block (and the 12-line explanatory comment above it) per Decision 6. `_parse_bigint`, `_serialize_bigint`, the `_BIGINT_STRING_PATTERN` regex, and the module docstring are unchanged.
- `django_strawberry_framework/__init__.py` — widened the existing `from .scalars import BigInt` line to `from .scalars import BigInt, strawberry_config`; appended `"strawberry_config"` to `__all__` as the last element after `"finalize_django_types"` (ASCII-sort: `s` = 115 sorts after `f` = 102). Trailing comma preserved per COM812.

### Tests added or updated

None — Slice 2 owns test edits per the spec slice checklist (spec lines 42–48) and the plan's `### Test additions / updates` directive ("Slice 1 ships zero new tests").

### Validation run

- `uv run ruff format .` — pass (118 files left unchanged; the COM812 conflict warning is a standing project notice, not a new issue).
- `uv run ruff check --fix .` — pass (All checks passed). First invocation flagged one E501 (line 125 of `scalars.py` at 113 > 110) on the long collision-error message; resolved by splitting the trailing recourse sentence onto a second adjacent string-literal line. Re-running ruff format and ruff check after the split passes cleanly.
- `git status --short` after both ruff invocations:
  - ` M django_strawberry_framework/__init__.py` — slice-intended (widened `from .scalars import` + appended `__all__`).
  - ` M django_strawberry_framework/scalars.py` — slice-intended (pinned-shape rewrite per Decision 3).
  - `?? docs/builder/bld-slice-1-helper_module_and_bigint_redefinition.md` — pre-existing untracked plan artifact (this file), out of scope for revert.
  - `?? docs/builder/build-020-scalar_map_helper-0_0_7.md` — pre-existing untracked build-plan artifact, out of scope for revert.
  - No unrelated tool churn; nothing to revert.
- No focused `pytest` run performed (the plan does not require one for Slice 1; Slice 2 owns all test work).

### Implementation notes

- **Collision-error message line wrap.** Spec's pinned shape at lines 290–296 keeps the `ValueError(...)` recourse sentence on one trailing string-literal line; that line came in at 113 characters in the local source (E501 against the 110-char `AGENTS.md` limit), so the recourse sentence was split into two adjacent implicit-concatenation string literals (`"Define a Strawberry custom scalar of a different NewType / class "` + `"to register under a separate key."`). The runtime message text is character-identical to the spec's pinned `f`-string output (the split lives only in source layout). The discretion item at the plan's `Implementation discretion items` #6 flagged that any deviation from the spec's joined-names format would require a Slice 2 test update; this is a layout-only deviation, not a content one, so the Slice 2 collision-message assertion can match the spec's text verbatim. No Slice 2 update required.
- **No comment near `_BIGINT_SCALAR_DEFINITION`.** Plan discretion item #5 made the inline comment optional; omitted. The function name plus the no-class call shape make the no-warning overload's identity self-documenting against the spec's reference at `.venv/lib/python3.10/site-packages/strawberry/types/scalar.py::scalar #"if cls is None and name is not None"`.
- **`strawberry_config` docstring.** Plan discretion item #3 required a docstring; included a short paragraph naming (a) the keyword-only `extra_scalar_map` and merge semantics, (b) the `**config_kwargs` passthrough, (c) the `scalar_map=` rejection (Decision 2), (d) the collision-raises policy (Decision 4). No forward link to `docs/GLOSSARY.md#strawberry_config` (that anchor lands in Slice 4).
- **Import ordering.** Plan discretion item #4 left the `strawberry`-rooted import block order to ruff format; the formatter settled on `import strawberry` followed by the two `from strawberry.<sub> import ...` lines in alphabetical-by-module order (`schema.config` then `types.scalar`), matching the spec's pinned shape at lines 256–261.
- **Brace-literal dict construction.** Both `_PACKAGE_SCALAR_MAP` (discretion #1) and the `merged` dict inside the factory (discretion #2) use the brace-literal / `dict(...)` + `.update(...)` form pinned by the spec — lowest-friction match against Decision 3's pinned shape.

### Notes for Worker 3

- **Expected test failure post-Slice-1.** Per the plan's `### Test additions / updates` section, `tests/base/test_init.py::test_public_api_surface_is_pinned` will fail until Slice 2 updates the exact-tuple assertion to include `"strawberry_config"`. This is the spec's documented sliced-test posture, not a Slice 1 defect.
- **`scripts/review_inspect.py` recommended for Worker 3 review.** Per `docs/builder/BUILD.md` "When to run the helper during build", Worker 3's threshold (30+ new logic lines under `django_strawberry_framework/`) is met: the Slice 1 diff adds ~50 source lines of new logic to `scalars.py` (factory + `_BIGINT_SCALAR_DEFINITION` + `_PACKAGE_SCALAR_MAP` + the docstring). Suggest `uv run python scripts/review_inspect.py django_strawberry_framework/scalars.py --output-dir docs/shadow --stdout` during review.
- **Untouched scalar behavior.** `_parse_bigint`, `_serialize_bigint`, `_BIGINT_STRING_PATTERN`, and the module docstring are byte-identical to their `0.0.6` form. The diff against those is empty.
- **Public surface delta.** `__init__.py` `__all__` widens by exactly one name (`"strawberry_config"`), appended at the end. The widening is authorized by spec DoD item 18 and the plan's Spec slice checklist (verbatim).
- No shadow file was used during build.

### Notes for Worker 1 (spec reconciliation)

- **Layout-only deviation from the pinned collision-error message string layout.** Spec's pinned shape at lines 290–296 keeps the recourse sentence on a single trailing string literal; the local 110-char line-length budget required splitting that string across two adjacent implicit-concatenation literals. The concatenated runtime text matches the spec character-for-character; the deviation is source-layout only. No spec edit needed unless Worker 1 wants the spec's pinned-shape code block to reflect the line-wrap (low-value cosmetic).
- No other spec gaps, conflicts, or unstated assumptions surfaced during Slice 1 implementation. The pinned shape at spec lines 252–300 implemented cleanly modulo the cosmetic wrap above.

---

## Review (Worker 3)

Helper invocation: `uv run python scripts/review_inspect.py django_strawberry_framework/scalars.py --output-dir docs/shadow`. Threshold met (Slice 1 adds ~50 lines of new logic to `django_strawberry_framework/scalars.py`, exceeding the 30-line gate). Overview at `docs/shadow/django_strawberry_framework__scalars.overview.md`: 3 symbols, 0 control-flow hotspots, 0 Django/ORM markers, 0 TODOs, 0 repeated string literals. Calls of interest: 5 `isinstance` (all in legacy `_parse_bigint`/`_serialize_bigint`), 2 `dict(...)` (the `extra = dict(...)` and `merged = dict(_PACKAGE_SCALAR_MAP)` calls in the new factory — both load-bearing for caller-dict isolation per Edge cases line 438), 1 `getattr` (the `getattr(k, '__name__', repr(k))` defensive fallback per Edge cases line 447). Nothing review-worthy surfaces from the overview that is not already covered by the checklist walk below.

Diff scope verification: `git status --short` shows only `M django_strawberry_framework/__init__.py`, `M django_strawberry_framework/scalars.py`, plus the two untracked `docs/builder/*.md` artifacts. No drift outside the slice contract. `git diff --stat django_strawberry_framework/` reports `+54/-26` across the two files — within the spec's expected `+30/-25` Slice 1 budget once the new factory docstring and the line-wrapped collision message are factored in.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- No duplicated logic introduced. The factory routes through the single `_PACKAGE_SCALAR_MAP` constant (the only source of truth for package-defined scalars) and the spec already pins how `Upload` (`TODO-ALPHA-028-0.0.11`) will extend it (append a new entry, no API change). The `dict(_PACKAGE_SCALAR_MAP)` + `.update(extra)` shape avoids the alternative `{**_PACKAGE_SCALAR_MAP, **extra}` form but both are equivalent; Worker 2 matched the spec's pinned shape (discretion item #2), which is correct.
- The `getattr(k, '__name__', repr(k))` fallback in the collision-error message is the only place that pattern appears in the diff; there is no parallel site to consolidate with. The spec's Edge cases line 447 documents this as defensive-only.
- The `dict(...)` defensive copy at line 119 (`extra = dict(extra_scalar_map) if extra_scalar_map else {}`) and the `merged = dict(_PACKAGE_SCALAR_MAP)` at line 128 both build fresh dicts — they look superficially similar but serve distinct purposes (caller-dict isolation vs module-state preservation). No collapse opportunity.
- No repeated string literals (helper output confirms 0). The `"strawberry_config"` symbol name appears in the docstring, the error message, and `__all__`, but each occurrence is load-bearing — collapsing them to a `__name__` reference would only obscure the contract.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` widens exactly one import (`from .scalars import BigInt` → `from .scalars import BigInt, strawberry_config`) and appends exactly one entry (`"strawberry_config"`) to `__all__` as the trailing element after `"finalize_django_types"`. The final tuple reads `("BigInt", "DjangoListField", "DjangoOptimizerExtension", "DjangoType", "OptimizerHint", "__version__", "auto", "finalize_django_types", "strawberry_config")` — character-identical to the spec's pinned tuple at spec line 448. The widening is authorized by the active spec's Slice 1 sub-checklist (spec lines 39 + Edge cases line 448) and Decision 2 (the helper API shape). ASCII-sort ordering holds (`s`=115 > `f`=102). No other surface changes; the `auto`, `DjangoListField`, `DjangoOptimizerExtension`, `OptimizerHint`, `DjangoType`, `finalize_django_types` re-exports are untouched.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- **No-warning overload usage is correct.** Verified against `.venv/lib/python3.10/site-packages/strawberry/types/scalar.py:254` (`if cls is None and name is not None: return ScalarDefinition(...)`) — the `strawberry.scalar(name="BigInt", serialize=_serialize_bigint, parse_value=_parse_bigint)` call at `scalars.py:84–88` lands on that branch and never reaches the deprecation-emitting `wrap()` body at the upstream's `cls is not None` path. Decision 3 contract satisfied.
- **`BigInt = NewType("BigInt", int)` is bare** at `scalars.py:82` — no `strawberry.scalar(NewType(...), ...)` wrapping. Decision 3 contract satisfied; the symbol stays usable as a direct annotation (`id: BigInt`) at the consumer site because `NewType` is transparent at runtime.
- **`_PACKAGE_SCALAR_MAP` keys on the `NewType` (the exported symbol), not a string or class.** `scalars.py:90–92` maps `BigInt` → `_BIGINT_SCALAR_DEFINITION`. This is the same key Strawberry will look up at schema-construction time when resolving consumer annotations. Decision 3 contract satisfied.
- **Caller-dict isolation is correct.** `extra = dict(extra_scalar_map) if extra_scalar_map else {}` at `scalars.py:119` defensively copies the caller's mapping before any merge logic; `merged = dict(_PACKAGE_SCALAR_MAP)` at line 128 builds a fresh dict from the package map; the `StrawberryConfig` at line 130 receives `merged`, not the caller's input. The `test_strawberry_config_extra_scalar_map_does_not_mutate_caller_dict` test Slice 2 will write should pass cleanly.
- **`scalar_map=` rejection fires before merge.** `scalars.py:115–118` checks `"scalar_map" in config_kwargs` and raises BEFORE any work on `extra_scalar_map`; the early-rejection contract from Decision 2 / Error shapes (spec line 201) is preserved.
- **Collision branch raises with `"cannot redeclare"` and names colliding keys** at `scalars.py:121–127`. The `sorted(...)` ordering keeps the message deterministic for the Slice 2 assertion on `"BigInt"` substring. Decision 4 contract satisfied.
- **`warnings.catch_warnings()` block and `import warnings` both removed.** `grep -n "warnings" django_strawberry_framework/scalars.py` returns nothing — Decision 6 contract satisfied. The pre-existing 12-line explanatory comment that described the suppression is also gone, matching the plan's Step 5 directive (code is the source of truth).
- **Docstring landed on the new factory** per discretion item #3, naming the four contract elements (keyword-only `extra_scalar_map`, `**config_kwargs` passthrough, `scalar_map=` rejection, collision policy). No forward link to the `docs/GLOSSARY.md#strawberry_config` anchor (lands in Slice 4) — that omission is correct; a dangling forward link would be worse than no link.
- **Spec Slice 1 checklist coverage is complete.** Both `- [ ]` boxes in `### Spec slice checklist (verbatim)` are addressed by the diff: (1) `scalars.py` carries the bare `NewType`, `_BIGINT_SCALAR_DEFINITION`, `_PACKAGE_SCALAR_MAP`, `strawberry_config` factory with all four sub-contracts (keyword-only signature, `**config_kwargs` passthrough, `scalar_map=` rejection, collision raise), and the suppression-block removal; (2) `__init__.py` widens the import line and appends `"strawberry_config"` as the trailing `__all__` element. The import-surface paragraph inside the first sub-bullet (ADD `Mapping`, `StrawberryConfig`, `ScalarDefinition`; KEEP `Any, NewType`; REMOVE `warnings`) is exactly what the diff does at lines 13–19.
- **Expected Slice-2 test failure is flagged.** Worker 2's `### Notes for Worker 3` correctly anticipates that `tests/base/test_init.py::test_public_api_surface_is_pinned` will fail until Slice 2 lands; that is the spec-documented slice boundary, not a Slice 1 defect.

### Temp test verification

None used; no temp tests required. The static review of the diff plus the upstream Strawberry source inspection at `.venv/lib/python3.10/site-packages/strawberry/types/scalar.py:254` confirmed the no-warning overload path; no behavioral question required a temp-test reproduction. Slice 2 owns all permanent test additions per the spec slice boundary.

### Notes for Worker 1 (spec reconciliation)

- Worker 2's "Layout-only deviation from the pinned collision-error message string layout" (recourse sentence split across two adjacent implicit-concatenation literals for the 110-char line budget) produces a runtime message character-identical to the spec's pinned `f`-string output; the deviation is source-layout only and does not require a spec edit. If Worker 1 wants the spec's pinned-shape code block (spec lines 290–296) to reflect the on-disk wrap for future-cycle clarity, that is a low-value cosmetic edit; skipping it preserves spec brevity. No action required.
- The factory docstring at `scalars.py:100–114` describes the contract but does not link to the `docs/GLOSSARY.md#strawberry_config` anchor (which lands in Slice 4). Once Slice 4 ships, Worker 1 may want to consider whether the docstring should be retro-fitted with a forward link in a polish pass; this is not a Slice 1 blocker.

### Review outcome

`review-accepted` — every Slice 1 sub-check in the Plan's `### Spec slice checklist (verbatim)` is addressed by the diff, the public surface widening is authorized by the spec, the no-warning overload usage is correct against the upstream source, the suppression block is fully removed, the factory's three behavioral branches (`scalar_map=` rejection, collision raise, merge) match the spec's pinned shape, and the caller-dict isolation contract that Slice 2's pending test will pin is satisfied by construction. No High, Medium, Low, or DRY findings. Artifact `Status:` line set to `review-accepted`.

---

## Final verification (Worker 1)

- **Spec slice checklist:** every `- [ ]` in the Plan's `### Spec slice checklist (verbatim)` is now `- [x]`. Both top-level sub-checks landed: (1) `django_strawberry_framework/scalars.py` carries the bare `NewType("BigInt", int)`, `_BIGINT_SCALAR_DEFINITION` built via the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload, `_PACKAGE_SCALAR_MAP`, the `strawberry_config` factory with all four sub-contracts (keyword-only `extra_scalar_map`, `**config_kwargs` passthrough, `scalar_map=` rejection, collision raise), and the suppression block is removed (verified `grep -n "warnings" django_strawberry_framework/scalars.py` returns nothing); the nested import-surface elaboration (ADD `Mapping`, `StrawberryConfig`, `ScalarDefinition`; KEEP `Any, NewType`; REMOVE `warnings`) holds exactly as written in `scalars.py:13–19`. (2) `django_strawberry_framework/__init__.py` widens `from .scalars import BigInt` to `from .scalars import BigInt, strawberry_config` and appends `"strawberry_config"` as the trailing `__all__` element after `"finalize_django_types"`; the final tuple matches the spec's pinned shape at spec line 448 character-for-character.
- **DRY check across this slice and prior accepted slices:** Slice 1 is the first slice of this build, so the comparison is internal to the diff. No duplication introduced — the factory routes through the single `_PACKAGE_SCALAR_MAP` constant (the only source of truth for package-defined scalars); the `getattr(k, '__name__', repr(k))` defensive fallback appears once in the diff with no parallel site to collapse; the two `dict(...)` defensive copies (`extra = dict(extra_scalar_map)` and `merged = dict(_PACKAGE_SCALAR_MAP)`) serve distinct purposes (caller-dict isolation vs module-state preservation) and are not a collapse opportunity. The `"strawberry_config"` symbol-name string appears in the factory docstring, the `scalar_map=` rejection error message, and `__all__`, but each occurrence is load-bearing and naming-them-via-`__name__` would only obscure intent. Worker 3's helper output confirmed 0 repeated string literals.
- **Existing tests still pass (focused scope):** `uv run pytest --no-cov tests/test_scalars.py tests/base/test_init.py` — exit code 1; 31 passed, 1 failed. The single failure is `tests/base/test_init.py::test_public_api_surface_is_pinned`, which is **expected-failing per spec Decision 7 / DoD item 6**; the failure is the slice handoff to Slice 2 (Slice 1 widens `__all__` by `"strawberry_config"`; Slice 2 widens the pinned tuple to match), not a defect. The other 22+ scalar tests in `tests/test_scalars.py` (parser/serializer contract, `test_bigint_is_importable_from_top_level`, and the deprecation-suppression regression `test_package_import_does_not_emit_strawberry_deprecation_warning`) all pass — the latter notably confirms the no-warning `strawberry.scalar(name=..., ...)` overload at `scalars.py:84–88` does not emit `DeprecationWarning` under the `-W error::DeprecationWarning` subprocess (Decision 6 contract intact post-migration). The `--no-cov` flag opted out of `pytest.ini`'s auto-applied `--cov` per BUILD.md "Coverage is the maintainer's gate, not a worker's tool".
- **Spec reconciliation:** the spec needed one edit — the top-level `Status:` line at spec line 4 still said "Slice 1 unstarted at the time of writing" after Slice 1 shipped; per Worker 1's role file "Spec status-line re-verification (every Worker 1 spawn)" rule, that stale wording was updated to reflect post-Slice-1 reality. Worker 2's `### Notes for Worker 1 (spec reconciliation)` flagged the `ValueError` collision-message line-wrap (single 113-char literal in the spec's pinned shape → two adjacent implicit-concatenation literals in `scalars.py:123–126`); decision: NO spec edit. Posture (a) — the spec's pinned shape is a contract on behavior, not source layout. Decision 3 (spec lines 304–306) pins "the wire format, parser, and serializer logic are preserved verbatim" but does not legislate source-layout for the `ValueError` message text; the runtime message is character-identical, only source layout differs. Touching the spec's pinned-shape code block for a cosmetic line-wrap would obscure the architectural intent the block is communicating with no behavioral payoff. Worker 3 reached the same posture in their `### Notes for Worker 1 (spec reconciliation)`.
- **Final status:** `final-accepted`. Every Spec slice checklist sub-check landed; DRY clean; focused tests pass except the documented Slice 2 handoff failure; spec reconciliation done (one stale-status-line edit; no edit needed for the cosmetic line-wrap). The artifact's top-level `Status:` line is set to `final-accepted`.

### Summary

Slice 1 shipped the architectural core of spec-020: `BigInt` was redefined as a bare `NewType("BigInt", int)` (the `strawberry.scalar(NewType, ...)` deprecation-prone wrap is gone), the canonical `ScalarDefinition` is built via the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload, and the public `strawberry_config(*, extra_scalar_map=None, **config_kwargs) -> StrawberryConfig` factory now lives in `django_strawberry_framework/scalars.py` with the spec's four contract elements intact (keyword-only `extra_scalar_map` merge semantics, `**config_kwargs` passthrough to `StrawberryConfig(...)`, `scalar_map=` rejection, and the hard `ValueError` for `_PACKAGE_SCALAR_MAP` collisions). The `warnings.catch_warnings()` suppression block and the now-unused `import warnings` are removed; `_parse_bigint` / `_serialize_bigint` / `_BIGINT_STRING_PATTERN` / the module docstring are byte-identical to their `0.0.6` form. The package's `__all__` widens by exactly one name (`"strawberry_config"` appended after `"finalize_django_types"`). Slice 2 will land the 15 new pytest items + the `tests/base/test_init.py` `__all__` update + the 10 `tests/types/test_converters.py` schema-construction migrations.

### Spec changes made (Worker 1 only)

- `docs/spec-020-scalar_map_helper-0_0_7.md` line 4 — updated the `Status:` line from "in flight — Slice 1 unstarted at the time of writing." to "in flight — Slice 1 shipped (helper module + `BigInt` redefinition); Slices 2–5 remain." Reason: per Worker 1's role file "Spec status-line re-verification (every Worker 1 spawn)" rule, the spec's status header must reflect post-build reality; Slice 1 has now landed `final-accepted`, so the prior "unstarted" wording is stale.
