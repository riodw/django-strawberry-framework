# Review: `django_strawberry_framework/utils/typing.py`

Status: verified

Supersedes the prior on-disk 0.0.7 artifact (`Status: verified`, refs `review-0_0_7.md`) wholesale. That artifact predated the 0.0.9 additions: it knew nothing of `is_async_callable` (added in the 0.0.9 DRY pass per the module docstring, `docs/feedback.md` Major 4) and described `unwrap_graphql_type` as an **unbounded** `while hasattr(...)` loop. Live source (`utils/typing.py::unwrap_graphql_type`) now runs a **bounded** `for _ in range(_MAX_TYPE_WRAPPER_DEPTH)` peel that raises `RuntimeError` on overrun — so the prior artifact's L3 ("lacks cycle-safety note", recommending a `seen: set[int]` guard) is ALREADY RESOLVED in live source and is NOT re-raised here (the recurring resolved-Low trap). Prior L1/L2/L4/L5 re-triaged against live source below.

## DRY analysis

- None — the module IS the canonical extraction for all three helpers, and each has a distinct termination contract that resists folding.
  - `is_async_callable` is the single partial-aware coroutine-callable predicate; its three production consumers (`connection.py::_resolve` window — import at `connection.py #"from .utils.typing import is_async_callable"`, call at `connection.py #"elif is_async_callable(resolver)"`; `list_field.py::_default` — call at `list_field.py #"if is_async_callable(user_resolver)"`; `types/base.py::_validate_globalid_callable_is_sync` — call at `types/base.py #"if is_async_callable(value)"`) all import the one home; no parallel `iscoroutinefunction`-plus-`__call__` predicate exists elsewhere (full-tree grep of `iscoroutinefunction` returns only this module's body + docstring mentions in tests). Correct single-siting; nothing to consolidate.
  - `unwrap_graphql_type` (deep `of_type` peel) is consumed only by `optimizer/extension.py` (import + two call sites: `extension.py #"gql_type = unwrap_graphql_type(gql_type)"` and `extension.py #"rt = unwrap_graphql_type(info.return_type)"`). No second deep-peel loop in the package.
  - `unwrap_return_type` (one-layer `of_type`-or-`list[T]` peel) has **zero non-test production consumers** today (see L1) — re-exported through `utils/__init__.py` ahead of the schema factory. The act-now/defer axis for any cross-call consolidation is moot until a real consumer lands.
  - A combined `unwrap(x, *, deep=False)` dispatcher folding `unwrap_graphql_type` and `unwrap_return_type` behind a kwarg was considered and rejected: different termination conditions (full peel vs single layer) and different return contracts (`of_type`-only leaf vs `of_type`-or-`list[T]`-or-`Any`-sentinel). Folding loses per-helper docstring contract clarity and forces every caller to thread `deep=`. Not a DRY win.

## High:

None.

## Medium:

None.

## Low:

### L1 — `unwrap_return_type` has zero non-test production call sites; only the re-export and the regression suite exercise it

`grep -rn "unwrap_return_type" django_strawberry_framework/` returns the definition (`utils/typing.py::unwrap_return_type`) and the re-export pair in `utils/__init__.py` (import + `__all__`). No optimizer or schema-factory module calls it. The function exists ahead of its consumer; `utils/__init__.py` docstring (`#"upcoming"` framing is in the wider re-export prose) stages it for the schema factory.

This is intentional pre-landing and documented at the export site, not a contract drift today. Recorded so a future cycle has a paper trail if the schema factory slips multiple releases.

Defer until either (a) the schema-factory consumer lands and the framing is satisfied, or (b) two release boundaries pass without a non-test call site of `unwrap_return_type` landing in `django_strawberry_framework/` — at which point the "exported for the upcoming consumer" framing crystallises from "upcoming" to "speculative API surface" and the export warrants a YAGNI re-evaluation.

### L2 — `unwrap_return_type` docstring is silent on the `Any` element-type sentinel and why both bare-list branches collapse to it

The body returns `Any` as an "unknown element type" sentinel in two distinct branches — `get_origin(rt) is list` with empty `get_args` (bare `typing.List`), and `rt is list` (bare builtin `list`, whose `get_origin` is `None`). Both are pinned with prior-shape rationale at `tests/utils/test_typing.py::test_unwrap_return_type_handles_bare_typing_list` and `::test_unwrap_return_type_handles_bare_builtin_list`. The docstring names the wrappers it peels and the one-layer-only contract but never names the `Any` sentinel or why both untyped-list shapes collapse onto it. A future direct consumer reading only the docstring would not learn the helper deliberately collapses both untyped-list shapes onto `Any` rather than raising or returning `list` itself.

Defer until a non-test consumer of `unwrap_return_type` lands (the staged schema factory); the docstring sentinel note naturally co-lands with the first real call site so the consumer-visible language can name the actual production shape rather than the test-only shape.

### L3 — `unwrap_return_type` "wrapper-first" check treats explicit `of_type = None` as "no wrapper" rather than "untyped wrapper"

`inner = getattr(rt, "of_type", None)` plus `if inner is not None` collapses two cases: the attribute is absent (genuinely no wrapper) versus present-and-`None` (a wrapper declaring it wraps nothing yet). Harmless today — no real Strawberry-list-style wrapper sets `of_type = None` (the prior-art `StrawberryList(of_type=...)` always carries a real inner type); both shapes correctly mean "cannot extract an inner type from a wrapper." The docstring motivates the wrapper-first ordering for the `StrawberryList[list[T]]` precedence case but is silent on this `None`-vs-absent collapse.

Defer until a wrapper that uses sentinel `of_type = None` enters scope (none today); inverting to a `_MISSING`-sentinel `getattr` is premature. Note: `unwrap_graphql_type` uses `hasattr(gql_type, "of_type")` instead, which already distinguishes absent from present-`None` — so the two helpers diverge on this point. This divergence is correct-by-contract (the deep peeler must keep peeling a present-`None`-then-something chain it cannot encounter, the one-layer peeler returns the wrapper) but is undocumented; the same docstring co-land covers it.

### L4 — submodule `__all__` gap (folder-pass-coordinated forward)

`utils/typing.py` exposes three public symbols (`is_async_callable`, `unwrap_graphql_type`, `unwrap_return_type`) and carries no module-level `__all__`. Consumers reach the symbols either through `utils/__init__.py`'s canonical `__all__` re-export tuple (for the two unwrap helpers) or through the direct submodule path `from ...utils.typing import is_async_callable` (the three `is_async_callable` consumers + the test suite). `from django_strawberry_framework.utils.typing import *` is the only path depending on a submodule `__all__`, and is not a documented entrypoint.

Defer with the trigger "sibling `utils/` submodules grow an `__all__`" — the folder pass `rev-utils.md` is the natural site to either land an `__all__` across all `utils/` submodules at once or continue the trio-of-defers. Coordinated, not act-now per-file.

### L5 — `utils/__init__.py` docstring lists `is_async_callable` alongside the two re-exported symbols but `__all__` omits it (forward to folder pass `rev-utils.md`)

`utils/__init__.py` docstring line — `#"plus ``is_async_callable``"` — names `is_async_callable` next to `unwrap_graphql_type`/`unwrap_return_type`, but the `__init__.py` `__all__` tuple and `from .typing import …` line export only the two unwrap helpers (`is_async_callable` is reached via the submodule path by all three consumers). The asymmetry is deliberate (the predicate is an internal-mechanics helper consumed by submodule path, not a re-exported public surface) but the docstring reads as if all three are equally surfaced. `utils/__init__.py` is folder-pass scope, not this file's scope.

Defer to the folder pass `rev-utils.md`: either add `is_async_callable` to the `__init__` re-export `__all__` (making the docstring honest) or reword the docstring line to mark it as submodule-only. Low; non-contract (GLOSSARY carries neither symbol). Recorded here only because the discrepancy is visible from this file's import-graph audit.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module is the canonical home for all three helpers; every production caller imports through it — `is_async_callable` from `connection.py`/`list_field.py`/`types/base.py`, `unwrap_graphql_type` from `optimizer/extension.py`. No parallel `of_type`-peel loop and no parallel `iscoroutinefunction`+`__call__` predicate anywhere else (full-tree grep of `of_type` and `iscoroutinefunction`).
- **New helpers considered.** A combined `unwrap(x, *, deep=False)` dispatcher folding the two unwrap helpers was rejected — different termination conditions and return contracts; folding regresses per-helper docstring contract clarity (mirrors the sibling-pair calibration: load-bearing distinctions are not folded behind a kwarg).
- **Duplication risk in the current file.** None — the three helpers are byte-different in body and contract. The shared `Any` import and the `of_type` literal are one source-site each.

### Other positives

- **`is_async_callable` is a correct superset of `inspect.iscoroutinefunction`.** The two missed shapes are both handled and both test-pinned: an instance whose `__call__` is `async def` (`iscoroutinefunction(instance)` is False; the `getattr(target, "__call__", None)` disjunct catches it — `tests/utils/test_typing.py::test_is_async_callable_sees_through_instances_and_partials` rows `_AsyncCallable()` and `partial(_AsyncCallable())`), and a `functools.partial` around an async instance (`iscoroutinefunction(partial)` unwraps only to `.func`, which for an instance is not a coroutine function — the `target = value.func` hop + `__call__` check catches it). The depth-1 `.func` hop is justified in the docstring by `partial` flattening nested partials at construction (`partial(partial(f)).func is f`), so `.func` is never itself a partial — no loop needed, no unbounded traversal. Verified: `is_async_callable(None)` and any non-callable degrade to `False` without raising (`isinstance(None, partial)` False → `getattr(None, "__call__", None)` is `None` → `iscoroutinefunction(None)` False).
- **Construction-time vs runtime async detection boundary is honest.** `is_async_callable` is the *construction/validation-time* predicate for consumer-supplied resolvers and the GlobalID callable (a different concern from `strawberry.utils.inspect.in_async_context`, the *per-call runtime* probe `list_field.py`/`relay.py`/`types/relay.py` use on their default branches). The task's mention of `in_async_context` as living in this file is a red herring: `grep -rn "in_async_context" django_strawberry_framework` shows it is imported from `strawberry.utils.inspect` at four sites and is **not defined in this module** — stated as a positive rather than manufactured into a finding.
- **`unwrap_graphql_type` is bounded and fails loud.** The `for _ in range(_MAX_TYPE_WRAPPER_DEPTH)` peel (ceiling 64, far above any real wrapper stack) raises `RuntimeError("… likely cyclic or corrupt")` on overrun rather than spinning — the NASA Power-of-Ten Rule 2 fixed-bound rationale is in the inline comment, and the bound is test-pinned three ways: deep-but-finite peel just under the ceiling (`test_unwrap_graphql_type_peels_a_deep_but_finite_stack`), cyclic-property `of_type` raising `RuntimeError` (`test_unwrap_graphql_type_raises_on_cyclic_of_type_stack`), and the leaf-stack happy path (`test_unwrap_graphql_type_peels_all_of_type_layers`). This is the live fix for the prior 0.0.7 artifact's L3 — resolved, not re-raised.
- **`None` passthrough is load-bearing and pinned.** `unwrap_graphql_type(None) is None` (`hasattr(None, "of_type")` is False → immediate return) is pinned by `test_unwrap_graphql_type_passes_through_none`, whose docstring cites the `optimizer/extension.py` recursion feeding `getattr(field_obj, "type", None)` and relying on the passthrough so the downstream `type_name is None` gate terminates cleanly.
- **`unwrap_return_type` wrapper-precedence ordering is explicit, motivated, and pinned.** The `of_type` check runs before the `list[T]` check so a wrapper that also presents a list-like origin yields its declared inner type; the docstring names this and `test_unwrap_return_type_peels_only_one_layer` (`Outer.of_type = list[Inner]` returns `list[Inner]`, not `Inner`) pins it. One-layer-only contract documented with "chain calls if you need full unwrapping."
- **Imports are minimal and standard-library only.** `functools`, `inspect`, and `from typing import Any, get_args, get_origin` — no Strawberry, graphql-core, or Django runtime dependency. All wrapper handling is duck-typed against `of_type`, so the helpers work across Strawberry versions and graphql-core `GraphQLNonNull`/`GraphQLList` shapes without locking either dependency.
- **`noqa: B004` is load-bearing and justified inline.** The `getattr(target, "__call__", None)` plus `iscoroutinefunction` is intentionally not `callable()` (what B004 suggests) — the comment at `is_async_callable` explains B004's suggestion is the wrong tool because the check inspects `__call__`'s async-ness, not callability.

### GLOSSARY drift quick-check

`grep -n "is_async_callable\|unwrap_return_type\|unwrap_graphql_type\|in_async_context\|utils/typing" docs/GLOSSARY.md` returns zero matches. All three symbols are internal mechanics — the consumer contract surface for type-unwrapping and async-callable detection is not exposed in the GLOSSARY (the optimizer surfaces its piece through `DjangoOptimizerExtension`; the field factories surface async-resolver behaviour through their public field surfaces; the schema factory will surface `unwrap_return_type`'s piece through whichever consumer-facing class it produces). Internal-mechanics absence is the correct convention; no GLOSSARY forward.

### Summary

`utils/typing.py` is a three-helper canonical-home utility: `is_async_callable` (the 0.0.9 partial-/`__call__`-aware coroutine-callable predicate shared by `connection`/`list_field`/`types.base`), `unwrap_graphql_type` (bounded deep `of_type` peel for the optimizer), and `unwrap_return_type` (one-layer `of_type`-or-`list[T]` peel staged for the schema factory). The prior 0.0.7 artifact is superseded wholesale: it predated `is_async_callable` and its lone substantive Low (unbounded-loop cycle-safety) is already resolved in live source — the loop is now `range`-bounded with a loud `RuntimeError`, triple-test-pinned — and is NOT re-raised. `is_async_callable` is verified a correct superset of `inspect.iscoroutinefunction` for both missed shapes (async `__call__` instance, partial-around-instance), with depth-1 `.func` traversal justified by partial flattening and full parametrized test coverage. The task's `in_async_context` reference is a red herring (imported from Strawberry, not defined here) — stated as a positive. Zero High, zero Medium, five forward-looking Lows (L1 zero-consumer paper trail; L2 `Any`-sentinel docstring silence; L3 `None`-vs-absent collapse; L4 submodule `__all__` gap; L5 `__init__` docstring/`__all__` asymmetry — L4/L5 forwarded to the `rev-utils.md` folder pass). DRY analysis: none — the module is the canonical extraction. GLOSSARY drift clean. Qualifies as shape #5 (no-source-edit cycle): no High, no behaviour-changing Medium, every Low forward-looking-with-explicit-trigger, no GLOSSARY-only fix; setting bare `fix-implemented` below.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — see Notes below.
- `uv run ruff check --fix .` — see Notes below.

### Notes for Worker 3
- Per-Low dispositions: L1, L2, L3, L4, L5 all forward-looking-without-edit, each gated on an explicit trigger condition quoted verbatim per `worker-1.md` deferral-idiom rules. L4 and L5 are forwarded to the `rev-utils.md` folder pass (submodule `__all__` and `__init__` re-export asymmetry are folder-scope concerns).
- The prior 0.0.7 artifact's unbounded-loop Low is ALREADY RESOLVED in live source (`unwrap_graphql_type` is now `range`-bounded with a loud `RuntimeError`, triple-test-pinned) — NOT re-raised, per the recurring resolved-Low trap.
- No GLOSSARY-only fix in scope — `is_async_callable`, `unwrap_graphql_type`, `unwrap_return_type`, and `in_async_context` are all correctly absent from `docs/GLOSSARY.md` (internal-mechanics-absence calibration); no drift to flag.
- `in_async_context` is NOT defined in this file (imported from `strawberry.utils.inspect` at four sites) — the task's framing was a red herring; confirmed absent and recorded as a positive.

### Validation run results
- `uv run ruff format --check django_strawberry_framework/utils/typing.py tests/utils/test_typing.py` — `2 files already formatted`.
- `uv run ruff check django_strawberry_framework/utils/typing.py tests/utils/test_typing.py` — `All checks passed!`.

---

## Verification (Worker 3)

### Logic verification outcome
Shape #5 no-source-edit cycle, terminal-verify. All three behavioral claims independently re-verified LIVE (`docs/review/temp-tests/utils_typing/probe.py`, config.settings):
- `unwrap_graphql_type` bounded: `_MAX_TYPE_WRAPPER_DEPTH == 64`; 63 wrappers peel to leaf, 64 wrappers raise `RuntimeError` (`"cyclic or corrupt"`), self-referential `of_type` raises, `None`/leaf passthrough. Prior 0.0.7 unbounded-loop Low is RESOLVED in live source (`for _ in range(...)` + loud `RuntimeError`); correctly NOT re-raised.
- Type-unwrapping correctness: `list[int]->int`, `list[list[int]]->list[int]` (one layer), `of_type` precedence over list-origin, bare `typing.List`/builtin `list` -> `Any`, `int`/`Optional[int]` passthrough.
- `is_async_callable` is a correct partial-/`__call__`-aware superset of `inspect.iscoroutinefunction`: both missed shapes (async `__call__` instance, `partial` around async instance) return True where baseline `iscoroutinefunction` returns False; sync forms False; `None`/`int` degrade to False without raising; `partial(partial(af)).func is af` flattening confirmed (depth-1 hop justified).
- `in_async_context` red herring confirmed: `grep -rn` shows it imported from `strawberry.utils.inspect` at list_field/relay/types.relay, ZERO defs in this module. Stated as positive, not a finding — correct.

All 8 cited test names exist at `tests/utils/test_typing.py`. The 3 `is_async_callable` production consumers (connection.py:1005, list_field.py:176, types/base.py:363) all import from `.utils.typing`; `unwrap_graphql_type` consumed by optimizer/extension.py (2 sites); `unwrap_return_type` has zero non-test production consumers (L1 confirmed).

### Shape #5 checks
1. `git diff --stat 0872a20…` for `utils/typing.py` + `tests/utils/test_typing.py` is BYTE-EMPTY. CHANGELOG diff empty. GLOSSARY dirty but every hunk attributes to a CLOSED sibling cycle: `global_id_for`/`decode_global_id` (testing/relay), `DjangoConnection` (connection), `Meta.orderset_class`/`OrderSet` (orders), `RelatedFilter` (filters), `RelatedOrder` (orders/filters), `inspect_django_type` (management). `grep` of this cycle's four symbols (`is_async_callable`/`unwrap_*`/`in_async_context`/`utils/typing`) over GLOSSARY = ZERO. "Files touched: None" holds.
2. Every Worker 2 section opens `Filled by Worker 1 per no-source-edit cycle pattern.` — confirmed.
3. Every Low (L1–L5) forward-looking with explicit verbatim trigger; no GLOSSARY-only fix. L4/L5 forwarded to folder pass `rev-utils.md`.
4. Changelog `Not warranted` cites both `AGENTS.md` #21 and the active plan's silence. Diff empty. Internal-mechanics framing matches (no public-API surface change).
5. Ruff format-check `1 file already formatted`; check `All checks passed!` (COM812 warning standing/expected).

### DRY findings disposition
None to carry — module is the canonical extraction for all three helpers; combined `unwrap(deep=)` dispatcher correctly rejected (distinct termination + return contracts). Re-confirmed via grep: no parallel `of_type`-peel loop, no parallel `iscoroutinefunction`+`__call__` predicate.

### Temp test verification
- `docs/review/temp-tests/utils_typing/probe.py` — all checks PASS (FAILURES: NONE). Gitignored; deleted at cycle closeout by Worker 0. Shipped behavior already pinned by the 8 permanent tests in `tests/utils/test_typing.py`; temp test is corroboration only, not the sole proof.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `utils/typing.py` checklist box.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment or docstring edits in scope — every L2/L3 docstring-silence finding is explicitly forward-looking and deferred until the corresponding consumer or trigger lands; L1/L4/L5 are procedural/forward deferrals with no current edit.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. **Not warranted** — no behaviour change, no public-API change, no consumer-visible surface change. Citations: `AGENTS.md` #21 ("Do not update CHANGELOG.md unless explicitly instructed"); the active review plan is silent on changelog updates for per-file review artifacts.

---

## Iteration log

(none)
