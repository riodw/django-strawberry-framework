# Review: `django_strawberry_framework/utils/typing.py`

Status: verified

## DRY analysis

- None — the module is the single source for three orthogonal type-introspection contracts (partial/`__call__`-aware async-callable detection in `is_async_callable`, full graphql-core `of_type`-stack peel in `unwrap_graphql_type`, single-layer Strawberry/`list[T]` unwrap in `unwrap_return_type`). The two unwrap helpers deliberately differ in contract — recursive-all-layers vs one-layer, with `unwrap_return_type` checking `of_type` *before* the `list` origin — and share no liftable body; `is_async_callable` is a wholly distinct concern. Folding any pair would couple independently-evolvable contracts for negative gain. Each helper is single-sourced and imported by every consumer (`unwrap_graphql_type` → `optimizer/extension.py`; `unwrap_return_type` → `mutations/sets.py`; `is_async_callable` → `connection.py`/`list_field.py`/`types/base.py`), so the module IS the resolution, not a candidate.

## High:

None.

## Medium:

None.

## Low:

### `is_async_callable` re-export asymmetry vs the two unwrap helpers

`django_strawberry_framework/utils/__init__.py #"from .typing import unwrap_graphql_type, unwrap_return_type"` re-exports `unwrap_graphql_type` and `unwrap_return_type` at the `utils` package root (both listed in its `__all__`) but does **not** re-export `is_async_callable`; the four first-party `is_async_callable` consumers — `connection.py::resolve_connection #"elif is_async_callable(resolver)"`, `list_field.py #"if is_async_callable(user_resolver)"`, `types/base.py #"if is_async_callable(value)"` — all import it submodule-direct via `from .utils.typing import is_async_callable`. The `utils/__init__.py` package docstring names all three helpers together ("… `unwrap_return_type`) plus `is_async_callable`"), so a reader could expect `is_async_callable` at the package root too.

Correct as-is and consistent across every call site (mirrors the `instance_accessor` submodule-direct-vs-package-root asymmetry already accepted in `rev-utils__relations.md`): the asymmetry itself is not a finding — only drift between `__all__`, the docstring, and the call sites would be. The docstring prose is descriptive ("Includes, among others: … `typing` … plus `is_async_callable`"), not a re-export promise, and every consumer agrees on submodule-direct import. Defer: act only if a consumer begins importing `is_async_callable` from the `utils` package root, at which point add it to the re-export + `__all__` for consistency.

## What looks solid

### DRY recap

- **Existing patterns reused.** `is_async_callable` is the single shared predicate consumed by the connection consumer-resolver branch (`connection.py #"elif is_async_callable(resolver)"`), the list-field resolver dispatch (`list_field.py #"if is_async_callable(user_resolver)"`), and the GlobalID-callable / sync-ness validator path (`types/base.py #"if is_async_callable(value)"`) — the 0.0.9 DRY-pass Major-4 consolidation the module docstring documents. `unwrap_graphql_type` is the single `of_type`-stack peeler consumed by the optimizer extension at two sites (`optimizer/extension.py #"gql_type = unwrap_graphql_type(gql_type)"` and `#"rt = unwrap_graphql_type(info.return_type)"`).
- **New helpers considered.** A unified `unwrap(rt, *, recursive)` collapsing the two unwrap helpers was considered and rejected: they differ in three independent dimensions (recursion depth, `of_type`-before-`list` ordering, and the `list`/`typing.List`/bare-`list` → `Any` sentinel logic that only `unwrap_return_type` carries). A flag-parametrized merge would re-entangle them; the depth-bounded `unwrap_graphql_type` and single-layer `unwrap_return_type` are correctly separate. A shared `_of_type(x)` accessor was also rejected — see below.
- **Duplication risk in the current file.** Both unwrap helpers read `of_type` (via `hasattr` then attribute access in `unwrap_graphql_type`, `getattr(rt, "of_type", None)` in `unwrap_return_type`). This is the same Strawberry/graphql-core wrapper contract surfaced at two abstraction levels (loop-to-leaf vs peek-one-layer), not a liftable duplicate — extracting a shared `_of_type(x)` accessor would save nothing and obscure that one path bounds a loop while the other does a single defaulted read.

### Other positives

- **Prior orphan-Low is now CLOSED by its own trigger — not re-flagged.** The previous (`verified`) artifact carried a forward-looking Low "`unwrap_return_type` has no first-party caller — public-but-orphaned helper" with deferral trigger "(a) a first-party consumer lands that needs single-layer list unwrapping — then this is simply the right helper, finding closes." That trigger has fired: `mutations/sets.py::_is_relay_id_annotation #"return unwrap_return_type(annotation) is relay.GlobalID"` now calls it to peel the M2M `list[relay.GlobalID]` wrapper before the GlobalID core compare (landed in commit `ee1afb58`, "Route remaining inline re-derivations through utils helpers"). The helper is no longer reachable-only-by-tests; the finding is resolved per its own gate and correctly does not reappear.
- **Bounded peel is genuinely defensive, not theater.** `unwrap_graphql_type` caps at `_MAX_TYPE_WRAPPER_DEPTH = 64` (NASA Power-of-Ten Rule 2) and raises a `RuntimeError` naming the ceiling and the likely cause (cyclic/corrupt `of_type` chain) rather than spinning. The cyclic-chain failure and a just-under-the-ceiling success are both pinned (`tests/utils/test_typing.py::test_unwrap_graphql_type_raises_on_cyclic_of_type_stack`, `::test_unwrap_graphql_type_peels_a_deep_but_finite_stack`).
- **`is_async_callable` traversal is provably depth-1.** The docstring correctly justifies the single `.func` hop: `functools.partial` flattens nested partials at construction (`partial(partial(f)).func is f`), so `.func` is never itself a partial — no loop needed. The `__call__` check is defaulted (`getattr(target, "__call__", None)`) so a non-callable value yields `False` rather than raising. The `noqa: B004` is correctly justified inline (inspecting `__call__`'s async-ness, not testing callability). All seven shapes pinned by the parametrized `::test_is_async_callable_sees_through_instances_and_partials` (async fn, sync fn, async `__call__` instance, sync `__call__` instance, partial-around-async-fn, partial-around-async-instance, partial-around-sync-fn).
- **`unwrap_return_type` edge cases are exhaustively pinned.** The `get_args(rt)` empty-tuple guard (`return args[0] if args else Any`) prevents the historical `IndexError` on bare `typing.List`; the dedicated `rt is list` branch handles bare-builtin `list` (where `get_origin` is `None`); `of_type`-first ordering is tested via `FakeStrawberryList`; single-layer-only is pinned by `::test_unwrap_return_type_peels_only_one_layer`. The `None`-passthrough of `unwrap_graphql_type` (relied on by the optimizer's `_walk_gql_type` recursion termination) is pinned by `::test_unwrap_graphql_type_passes_through_none`.
- **No reflective-access hazards.** All four calls-of-interest are safe: `isinstance(value, functools.partial)` (type test), `getattr(target, "__call__", None)` (defaulted), `hasattr(gql_type, "of_type")` (loop guard before access), `getattr(rt, "of_type", None)` (defaulted). Zero Django/ORM markers, zero repeated string literals, zero TODOs, zero control-flow hotspots (static overview confirms).
- **Annotation-introspection scope is correctly narrow.** `get_origin`/`get_args` are used only for the `list` case; `Optional`/`Union`/`Annotated` are intentionally not handled here — those forms do not reach these helpers (Strawberry resolves `Optional`/`Annotated` at type-definition time before the optimizer/factory layers call into this module), so adding speculative `Union`/`Annotated` unwrapping would be unreachable-under-test scope creep.

### Summary

`utils/typing.py` is byte-identical to the cycle baseline `8adcf1b0` (empty `git log 8adcf1b0..HEAD -- <target>`, empty `git diff HEAD -- <target>`; last touch `075f604d` predates the baseline) and ruff-clean. It is the single source for three orthogonal type-introspection contracts, each branch-by-branch tested in `tests/utils/test_typing.py`. No High or Medium findings. The prior cycle's `unwrap_return_type`-orphan Low is now **closed** — `mutations/sets.py::_is_relay_id_annotation` (commit `ee1afb58`) is a genuine first-party caller, firing that Low's own "first-party consumer lands → finding closes" trigger. One forward-looking Low remains: the `is_async_callable` re-export asymmetry, consistent across all four call sites and therefore a non-finding until a consumer imports it via the `utils` package root. DRY analysis is `None` (consolidation-point module). No-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, "289 files left unchanged".
- `uv run ruff check --fix .` — pass, "All checks passed!".

### Notes for Worker 3
- Both `git diff 8adcf1b0ec64deb7fc13b8cf56576524568db6af -- django_strawberry_framework/utils/typing.py` and `git diff HEAD -- django_strawberry_framework/utils/typing.py` are empty; `git log baseline..HEAD -- <target>` returns nothing. Source byte-identical to baseline.
- Prior artifact was `verified` (overwritten cleanly, old Worker 3 banner dropped).
- Low #1 disposition: forward-looking, trigger-gated (`is_async_callable` re-export asymmetry) — act only if a consumer imports `is_async_callable` from the `utils` package root.
- The prior cycle's second Low (`unwrap_return_type` public-but-orphaned) is **resolved, not carried** — `mutations/sets.py::_is_relay_id_annotation` (`return unwrap_return_type(annotation) is relay.GlobalID`, commit `ee1afb58`) is now a first-party caller, firing that Low's own closing trigger. Recorded in `### Other positives`, not re-flagged.
- No GLOSSARY-only fix in scope. GLOSSARY prose at `#djangolistfield` and `#djangomutationfield` describes `is_async_callable`'s partial-aware / `__call__` / one-hop contract accurately — verified against the docstring and implementation, no drift. `is_async_callable` carries no symbol-level GLOSSARY entry and is absent from `utils/__init__.py.__all__` (submodule-direct-import-by-convention) — absence correct.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits — source byte-identical to baseline; logic correct; comments and docstrings accurate (the `is_async_callable` depth-1 justification, the `_MAX_TYPE_WRAPPER_DEPTH` NASA Power-of-Ten rationale, the `noqa: B004` inline justification, and the `of_type`-before-`list` ordering note in `unwrap_return_type` all match the implementation).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source edits this cycle (zero tracked-file changes). AGENTS.md: "Do not update CHANGELOG.md unless explicitly instructed." The active plan `docs/review/review-0_0_11.md` is silent on changelog entries for this item.

---

## Verification (Worker 3)

### Logic verification outcome
No-source-edit cycle (shape #5) — zero High / zero Medium / one forward-looking Low, all independently confirmed against live source:

- **Zero-edit proof.** `git diff 8adcf1b0 -- django_strawberry_framework/utils/typing.py`, `git diff HEAD -- <target>`, and `git log 8adcf1b0..HEAD -- <target>` all empty; owned-paths `git diff --stat 8adcf1b0 -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty (no sibling-cycle attribution needed). Source byte-identical to baseline. Each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle pattern." — #5 gate satisfied.
- **Low (re-export asymmetry) genuine + forward-looking.** Confirmed `is_async_callable` is absent from `utils/__init__.py.__all__` (re-exports only `unwrap_graphql_type`, `unwrap_return_type`); every consumer imports submodule-direct (`connection.py:84`, `list_field.py:27`, `types/base.py:57`). The package docstring (`utils/__init__.py:11`) names it descriptively ("… plus `is_async_callable`"), not as a re-export promise. No consumer imports it from the package root → asymmetry harmless, finding correctly deferred with a real trigger (act only if a consumer reaches for the package-root import).
- **`is_async_callable` partial-aware contract verified vs source (typing.py:40-45).** `.func` hop guarded by `isinstance(value, functools.partial)`; depth-1 justified (partial flattens nested partials at construction); `__call__` checked defaulted via `getattr(target, "__call__", None)`; `noqa: B004` inline-justified (inspecting `__call__` async-ness, not callability). Matches docstring.
- **Optional/list unwrapping verified.** `unwrap_return_type` reads `of_type` first (Strawberry-wrapper-before-`list` ordering, typing.py:109-111), then `get_origin(rt) is list` with the `args[0] if args else Any` empty-tuple guard (no `IndexError` on bare `typing.List`), then the bare-`list` → `Any` branch. `unwrap_graphql_type` bounded peel at `_MAX_TYPE_WRAPPER_DEPTH = 64` with a `RuntimeError` naming the ceiling.
- **`unwrap_return_type` first-party caller confirmed.** `mutations/sets.py:830 #"return unwrap_return_type(annotation) is relay.GlobalID"` inside `_is_relay_id_annotation` peels the M2M `list[relay.GlobalID]` wrapper before the GlobalID core compare; commit `ee1afb58` ("Route remaining inline re-derivations through utils helpers") exists. The prior cycle's "public-but-orphaned" Low's own closing trigger ("first-party consumer lands → finding closes") genuinely fired — correctly recorded in `### Other positives`, not re-flagged.
- **No GLOSSARY drift (genuine #5, not missed #4).** `is_async_callable` is private-by-convention (no `__all__` membership, no symbol-level entry) — absence correct. Contract-level prose at `#djangolistfield` (GLOSSARY.md:364) and `#djangomutationfield` (GLOSSARY.md:396) describes the partial-aware / `__call__` / one-hop-`functools.partial` contract accurately vs the live implementation; both untouched vs baseline.

Minor cosmetic note (not a rejection trigger, content-not-identifier per AGENTS.md #27): the Low's prose says "the four first-party consumers" but enumerates and greps to three call sites (`connection.py:1036`, `list_field.py:176`, `types/base.py:363`). The miscount is in descriptive prose only; the load-bearing claim (no consumer imports from the package root → asymmetry harmless) is correct.

### DRY findings disposition
DRY-None confirmed — the module IS the single source for three orthogonal type-introspection contracts (partial/`__call__`-aware `is_async_callable`, full `of_type`-stack `unwrap_graphql_type`, one-layer `unwrap_return_type`). Each is single-sourced and imported by every consumer; folding any pair would re-entangle independently-evolvable contracts (recursion depth, `of_type`-before-`list` ordering, `list`/`typing.List`/bare-`list` → `Any` sentinel). No liftable body. Nothing carried forward.

### Temp test verification
None — no behavior suspicion to prove; source byte-identical to baseline and every branch already named-test-pinned in `tests/utils/test_typing.py`.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `utils/typing.py` checklist box. Changelog "Not warranted" cites both AGENTS.md and active-plan silence (both citations present); changelog diff empty.
