# Review: `django_strawberry_framework/utils/typing.py`

Status: verified

## DRY analysis

- None — the module is the single source for three orthogonal type-introspection contracts (partial/`__call__`-aware async-callable detection, full graphql-core `of_type`-stack peel, single-layer Strawberry/`list[T]` unwrap). The two unwrap helpers deliberately differ in contract (recursive-all-layers vs one-layer, with `unwrap_return_type` checking `of_type` *before* `list` origin) and share no liftable body; `is_async_callable` is a wholly distinct concern. Folding any pair would couple independently-evolvable contracts for negative gain.

## High:

None.

## Medium:

None.

## Low:

### `unwrap_return_type` has no first-party caller — public-but-orphaned helper

`unwrap_return_type` is exported through `utils/__init__.py` (`from .typing import unwrap_graphql_type, unwrap_return_type` and `__all__`) but has zero first-party call sites in `django_strawberry_framework/` (grep across source + examples). It once had a caller in the optimizer extension; commit `32b7e033` ("Refactor DjangoOptimizerExtension … type-tracing for querysets") moved the optimizer onto `unwrap_graphql_type` instead, leaving `unwrap_return_type` reachable only through its own `tests/utils/test_typing.py`. The function is correct, tested branch-by-branch, and its docstring frames it as a portability helper for callers that need single-layer Strawberry/`list[T]` unwrapping — so this is not dead code in the delete-it sense, but a public surface kept alive by tests alone.

Correct as-is today (intentional public portability helper; removing it would be an API change and lose the tested `list`/`typing.List`/`of_type`-first behavior). Defer: re-evaluate when either (a) a first-party consumer lands that needs single-layer list unwrapping — then this is simply the right helper, finding closes; or (b) a future API-surface-trimming pass decides the package should not export helpers without an internal consumer — then drop it from `__all__` and the `utils/__init__.py` re-export and relocate the test, in the same change.

### `is_async_callable` re-export asymmetry vs the two unwrap helpers

`utils/__init__.py` re-exports `unwrap_graphql_type` and `unwrap_return_type` at package root (and lists both in `__all__`) but not `is_async_callable`; the three first-party `is_async_callable` consumers (`connection.py:83`, `list_field.py:27`, `types/base.py:57`) all import it submodule-direct via `from .utils.typing import is_async_callable`. The package docstring at `utils/__init__.py:11` names all three together ("… plus `is_async_callable`"), so a reader could expect `is_async_callable` at package root too.

Correct as-is and consistent across every call site (mirrors the `instance_accessor` submodule-direct-vs-package-root asymmetry already accepted in `rev-utils__relations.md`): the asymmetry itself is not a finding, only drift between `__all__`, the docstring, and the call sites would be. Here the docstring prose is descriptive ("home to these helpers"), not a re-export promise, and every consumer agrees on submodule-direct import. Defer: only act if a consumer begins importing `is_async_callable` from the package root, at which point add it to the re-export + `__all__` for consistency.

## What looks solid

### DRY recap

- **Existing patterns reused.** `is_async_callable` is the single shared predicate consumed by the connection consumer-resolver branch (`connection.py:1005`), the list-field resolver dispatch (`list_field.py:176`), and the GlobalID-callable validator path (`types/base.py:363`) — the 0.0.9 DRY-pass Major-4 consolidation it documents in the module docstring. `unwrap_graphql_type` is the single `of_type`-stack peeler consumed by the optimizer extension at `extension.py:525,612`.
- **New helpers considered.** A unified `unwrap(rt, *, recursive)` collapsing the two unwrap helpers was considered and rejected: the two differ in three independent dimensions (recursion depth, `of_type`-before-`list` ordering, and the `list`/`typing.List`/bare-`list` → `Any` sentinel logic that only `unwrap_return_type` carries). A flag-parametrized merge would re-entangle them; the depth-bounded `unwrap_graphql_type` and single-layer `unwrap_return_type` are correctly separate.
- **Duplication risk in the current file.** Both unwrap helpers read `of_type` (via `hasattr` then attribute access in one, `getattr(rt, "of_type", None)` in the other). This is the same Strawberry/graphql-core wrapper contract surfaced at two abstraction levels (loop-to-leaf vs peek-one-layer), not a liftable duplicate — extracting a shared `_of_type(x)` accessor would save nothing and obscure that one path bounds a loop while the other does a single defaulted read.

### Other positives

- **Bounded peel is genuinely defensive, not theater.** `unwrap_graphql_type` caps at `_MAX_TYPE_WRAPPER_DEPTH = 64` (NASA Power-of-Ten Rule 2) and raises a `RuntimeError` naming the ceiling and the likely cause (cyclic/corrupt `of_type` chain) rather than spinning. The cyclic-chain failure and a just-under-the-ceiling success are both pinned (`test_unwrap_graphql_type_raises_on_cyclic_of_type_stack`, `test_unwrap_graphql_type_peels_a_deep_but_finite_stack`).
- **`is_async_callable` traversal is provably depth-1.** The docstring correctly justifies the single `.func` hop: `functools.partial` flattens nested partials at construction (`partial(partial(f)).func is f`), so `.func` is never itself a partial — no loop needed. The `__call__` check is defaulted (`getattr(target, "__call__", None)`) so a non-callable value yields `False` rather than raising. The `noqa: B004` is correctly justified inline (inspecting `__call__`'s async-ness, not testing callability).
- **`unwrap_return_type` edge cases are exhaustively pinned.** The `get_args(rt)` empty-tuple guard (`return args[0] if args else Any`) prevents the historical `IndexError` on bare `typing.List`; the dedicated `rt is list` branch handles bare-builtin `list` (where `get_origin` is `None`); `of_type`-first ordering is tested via `FakeStrawberryList`; single-layer-only is pinned by `test_unwrap_return_type_peels_only_one_layer`. The `None`-passthrough of `unwrap_graphql_type` (relied on by the optimizer's `_walk_gql_type` recursion termination) is pinned by `test_unwrap_graphql_type_passes_through_none`.
- **No reflective-access hazards.** All four calls-of-interest are safe: `isinstance(value, functools.partial)` (type test), `getattr(target, "__call__", None)` (defaulted), `hasattr(gql_type, "of_type")` (loop guard before access), `getattr(rt, "of_type", None)` (defaulted). Zero Django/ORM markers, zero repeated string literals, zero TODOs (static overview confirms).
- **Annotation-introspection scope is correctly narrow.** `get_origin`/`get_args` are used only for the `list` case; `Optional`/`Union`/`Annotated` are intentionally not handled here — those forms do not reach these helpers (Strawberry resolves `Optional`/`Annotated` at type-definition time before the optimizer/factory layers call into this module), so adding speculative `Union`/`Annotated` unwrapping would be unreachable-under-test scope creep.

### Summary

`utils/typing.py` is byte-identical to baseline `14910230` (empty `git log 14910230..HEAD`, empty `git diff HEAD`) and ruff-clean. It is the single source for three orthogonal type-introspection contracts, each branch-by-branch tested in `tests/utils/test_typing.py`. No High or Medium findings. Two forward-looking Lows, both correct as-is and trigger-gated: `unwrap_return_type` is a tested public helper with no current first-party caller (the optimizer migrated to `unwrap_graphql_type` in `32b7e033`), and the `is_async_callable` re-export asymmetry is consistent across all call sites and therefore a non-finding until a consumer imports it via the package root. DRY analysis is `None` (consolidation-point module). No-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format --check django_strawberry_framework/utils/typing.py` — `1 file already formatted` (no changes; COM812-formatter-conflict warning is the standing repo config, not a file issue).
- `uv run ruff check django_strawberry_framework/utils/typing.py` — `All checks passed!`

### Notes for Worker 3
- Shadow overview used: `docs/shadow/django_strawberry_framework__utils__typing.overview.md` (0 control-flow hotspots, 0 Django/ORM markers, 4 calls-of-interest all audited safe, 0 repeated literals, 0 TODOs).
- Low 1 (`unwrap_return_type` orphaned-but-public): forward-looking, two explicit trigger conditions stated (first-party consumer lands → finding closes; API-trimming pass → drop from `__all__` + re-export + relocate test). Grounded in `git log -S 'unwrap_return_type('` showing prior optimizer caller removed by `32b7e033`. No edit this cycle.
- Low 2 (`is_async_callable` re-export asymmetry): forward-looking, non-finding-until-drift per the `rev-utils__relations.md` `instance_accessor` calibration; trigger = a consumer importing it via package root. No edit this cycle.
- No GLOSSARY-only fix in scope — grep of `docs/GLOSSARY.md` for all three symbols + `utils/typing` returned zero hits, so no documented-public-contract prose to correct.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring changes. The module docstring and all three function docstrings accurately describe current behavior (async-callable partial/`__call__` traversal, bounded `of_type` peel, single-layer list unwrap). The `noqa: B004` and `_MAX_TYPE_WRAPPER_DEPTH` rationale comments are accurate and load-bearing. No stale TODOs (static overview confirms zero TODO comments). Note for the comment-quality record: `unwrap_return_type`'s docstring frames it as a caller-portability helper, which remains accurate even with no current first-party caller (Low 1) — no docstring correction warranted.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source, test, GLOSSARY, or any tracked-file edit this cycle (AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_10.md` records no changelog obligation for this item).

---

## Verification (Worker 3)

### Logic verification outcome

Shape #5 (no-source-edit) terminal verify. Zero this-cycle edits confirmed: `git diff HEAD -- django_strawberry_framework/utils/typing.py` empty; `git log 14910230..HEAD -- <target>` empty; last-touch `075f604d` predates HEAD `58ca2def` (prompt baseline `14910230` stale — content-not-identifier, verified by source-read + grep, not SHA).

Type-introspection correctness re-derived from LIVE source (not the artifact):
- `is_async_callable` (typing.py:40-45): `value.func` only when `isinstance(value, functools.partial)`, else `value`; depth-1 hop justified (partial flattens nested partials at construction). `iscoroutinefunction(target) or iscoroutinefunction(getattr(target,"__call__",None))` — defaulted getattr so a non-callable yields `False`, never raises. `noqa: B004` correctly justified (inspecting `__call__` async-ness, not testing callability). Correct.
- `unwrap_graphql_type` (typing.py:75-82): bounded `range(_MAX_TYPE_WRAPPER_DEPTH=64)` loop; `hasattr(gql_type,"of_type")` guard precedes the `.of_type` read; returns `gql_type` on no-wrapper (including `None` passthrough relied on by the optimizer's `_walk_gql_type` termination); raises `RuntimeError` naming the ceiling + cyclic/corrupt cause on overflow. NASA Power-of-Ten Rule 2 cap is genuine, not theater. Correct.
- `unwrap_return_type` (typing.py:109-117): `of_type`-first (`getattr` defaulted) → `get_origin(rt) is list` with the empty-`get_args` → `Any` guard (prevents the historical `IndexError` on bare `typing.List`) → dedicated `rt is list` → `Any` branch (bare builtin where `get_origin` is `None`) → passthrough. Single-layer-only by construction (no loop). Correct.
- Optional/Union/Annotated intentionally NOT handled: those forms are resolved by Strawberry at type-definition time before the optimizer/factory layers call into this module, so adding speculative unwrapping would be unreachable under the 100% gate — scope-creep avoidance, sound.

**Low 1 (`unwrap_return_type` orphaned-but-public) — orphan verdict CONFIRMED, defer is the right call.** Grep across `django_strawberry_framework/` + `examples/` returns zero first-party call sites — only the `def` (typing.py:85), the `utils/__init__.py` re-export (:31), `__all__` membership (:40), the descriptive docstring mention (:11), and `tests/utils/test_typing.py`. The optimizer migration is exactly as claimed: `git show 32b7e033 -- optimizer/extension.py` shows the removed lines `-from ..utils.typing import unwrap_return_type` and `-        target_type = unwrap_return_type(info.return_type)`; the live optimizer now calls `unwrap_graphql_type` at `extension.py:525,612` (import at :50). The function is correct and branch-by-branch tested. Adjudication: an orphaned **public** `__all__` export is correctly a forward-looking Low — removing it from `__all__` + the re-export is a breaking change to potential external consumers (AGENTS.md public-surface framing) and is NOT an act-now removal. This is the OPPOSITE of the orders/sets.py `_verbatim_path` case (a `_`-prefixed PRIVATE symbol → internal hygiene → act-now); a public export is API surface → defer. Worker 1's two explicit trigger conditions (first-party consumer lands → finding closes; API-trimming pass → drop from `__all__`+re-export+relocate test in the same change) are the right gates. Not dead-and-removable.

**Low 2 (`is_async_callable` re-export asymmetry) — forward-looking, non-finding-until-drift, CONFIRMED.** `is_async_callable` is NOT re-exported at package root; all consumers import it submodule-direct (`from ..utils.typing import is_async_callable`). `utils/__init__.py:11` docstring prose names all three together but is descriptive ("home to these helpers"), not a re-export promise — so no `__all__`/docstring/call-site drift exists. Mirrors the `instance_accessor` calibration accepted in `rev-utils__relations.md`. Trigger = a consumer importing via package root, unmet. Sound.

### DRY findings disposition

DRY `None` confirmed sound — consolidation-point module. The two unwrap helpers differ in three independent dimensions (recursion depth, `of_type`-before-`list` ordering, and the `list`/`typing.List`/bare-`list` → `Any` sentinel logic carried only by `unwrap_return_type`); a flag-parametrized `unwrap(rt,*,recursive)` merge would re-entangle independently-evolvable contracts for negative gain. `is_async_callable` is a wholly distinct concern. The shared `of_type` reads sit at two abstraction levels (bounded loop-to-leaf vs single defaulted peek) — extracting a `_of_type` accessor saves nothing. No liftable body; carried forward as `None`.

### Temp test verification

- None — type-introspection correctness was statically decidable from source + the existing branch-by-branch suite in `tests/utils/test_typing.py` (cited in the artifact). No suspicion required a runtime probe; no pytest run performed (shape #5, no test introduced).

### Verification outcome

Shape #5 checklist all met: (a) zero-edit proof per-item (empty `git diff HEAD` + absent from `git log 14910230..HEAD`); (b) all three Worker 2 sections open `Filled by Worker 1 per no-source-edit cycle pattern.`; (c) both Lows forward-looking with explicit triggers, no GLOSSARY-only fix; (d) changelog `Not warranted` cites BOTH AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") AND active-plan silence, and `git diff -- CHANGELOG.md` is empty; (e) ruff format-check (`1 file already formatted`) + check (`All checks passed!`) pass.

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.
