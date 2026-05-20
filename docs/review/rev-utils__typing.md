# Review: `django_strawberry_framework/utils/typing.py`

Status: verified

## DRY analysis

- Defer until a second stringified-annotation parse site lands in the optimizer: extend `utils/typing.py` with the `_NODEID_STRING_RE` regex helper currently carried in `worker-memory/worker-1.md`. No second site has landed; the two-function split (`unwrap_graphql_type` peel-all vs `unwrap_return_type` peel-one) stays correct factoring today.

## High:

None.

## Medium:

None.

## Low:

### `unwrap_return_type` has zero production call sites — public surface without a consumer

`unwrap_return_type` is exported via `django_strawberry_framework/utils/__init__.py:19,28` and pinned by four tests at `tests/utils/test_typing.py:7-13, 16-25, 28-37, 59-65`, but a package-wide grep finds zero non-test call sites (the only matches are the definition at `utils/typing.py:21`, the import at `utils/__init__.py:19`, the `__all__` entry at `:28`, and the test file). The module docstring at `utils/typing.py:1-9` justifies the public surface ("both contracts live here so optimizer and schema factories do not grow parallel unwrap loops"), but the optimizer today only consumes `unwrap_graphql_type` — there is no "schema factory" caller in production. Two paths if ever revisited: (a) leave the surface as-is on the rationale that the contract is documented and the one-layer-list-peel is a natural sibling to the graphql-core peel — the prior carry-forward in `worker-memory/worker-1.md` calibrated `runtime_checkable Protocol with no isinstance call sites` as "Low (dead-decorator weight) — always grep before flagging", and this is the same shape (public helper with no in-tree consumer); (b) demote to module-private `_unwrap_return_type` plus a documented future-export note, deferring re-exposure until a real call site lands. Low because the test surface pins the contract and the function is correct on its own terms; flag for the folder pass to confirm against `utils/__init__.py`'s public-vs-private contract.

```django_strawberry_framework/utils/typing.py:21:50
def unwrap_return_type(rt: Any) -> Any:
    """Unwrap **one layer** of list / Strawberry-list-wrapper around the inner type.
    ...
    """
    inner = getattr(rt, "of_type", None)
    if inner is not None:
        return inner
    if get_origin(rt) is list:
        return get_args(rt)[0]
    return rt
```

### `unwrap_graphql_type` defends against `None` only implicitly via `hasattr`

`unwrap_graphql_type` at `utils/typing.py:14-18` is called with `info.return_type` at `extension.py:404` and `getattr(field_obj, "type", None)` (via the `_walk_gql_type` recursion entry at `extension.py:357`). If a future caller hands in `None` (the recursion entry already handles that case at `extension.py:339-340` with `type_name is None`-style early returns, so the `None` is unwrapped to `None`), `unwrap_graphql_type(None)` returns `None` because `hasattr(None, "of_type")` is `False` — fine. The defensive shape is structurally correct (the `while hasattr` predicate is `False` for any input that doesn't carry an `of_type` attribute, including `None` and bare `GraphQLObjectType`), and there is no recommended change. Flagging only because the docstring at `:15` ("Peel all graphql-core / Strawberry ``of_type`` wrapper layers.") does not state the "no-`of_type` passthrough" semantics explicitly the way `unwrap_return_type`'s docstring does at `:43` ("``int`` -> ``int`` (no wrapper to peel)"). A one-sentence parallel ("returns ``gql_type`` itself when no ``of_type`` layer is present") would make the contract symmetric across the two helpers. Comment-pass discretion.

```django_strawberry_framework/utils/typing.py:14:18
def unwrap_graphql_type(gql_type: Any) -> Any:
    """Peel all graphql-core / Strawberry ``of_type`` wrapper layers."""
    while hasattr(gql_type, "of_type"):
        gql_type = gql_type.of_type
    return gql_type
```

### Docstring example block format diverges from sibling `utils/` helpers

`unwrap_return_type`'s `Examples:` block at `utils/typing.py:38-43` uses `→`-style arrow lines with trailing `;` separators (`"list[int]" -> "int";`), matching the format `utils/strings.py:33-36, 64-68` chose. `utils/relations.py:42-56` uses bullet prose. Per `worker-memory/worker-1.md`'s carry-forward ("docstring example-format consistency across relations.py / strings.py / typing.py is worth one unified pass at the folder artifact rather than per-file Lows"), this is the third sibling and should be considered together at the folder pass — not edited in this per-file cycle. Flagging for the folder pass to make the unified-format decision against all three siblings at once; no per-file edit recommended.

```django_strawberry_framework/utils/typing.py:38:43
Examples:
    ``list[int]`` -> ``int``;
    ``list[list[int]]`` -> ``list[int]`` (this helper peels one
    layer; chain calls if you need full unwrapping);
    ``StrawberryList(of_type=int)`` -> ``int``;
    ``int`` -> ``int`` (no wrapper to peel).
```

### `unwrap_graphql_type` is not test-pinned against a `None` input

`tests/utils/test_typing.py:40-56` exercises `unwrap_graphql_type` against a nested `NonNull(List(NonNull(Inner)))` stack — the canonical graphql-core shape — but does not pin the `None`-passthrough behavior (`unwrap_graphql_type(None) is None`). The implementation is correct (the `while hasattr` loop is false on `None`), but the contract is not pinned. The `_walk_gql_type` recursion at `extension.py:336-363` is the only call site that could feed `None` (via `getattr(field_obj, "type", None)` at `:357`), and the `type_name is None` guard at `:339-340` immediately stops the recursion — but that gate runs *after* `unwrap_graphql_type` returns, so the passthrough is load-bearing for the recursion's correctness. Same shape as the `tests/utils/test_relations.py:21-24` and the `rev-utils__strings.md:37-43` "unreachable-branch test pin" idiom. One-line test `assert unwrap_graphql_type(None) is None` would anchor the contract and pin the implicit-`hasattr`-on-`None` semantics. Low because the contract holds in current code and the call site does not actually pass `None` through unguarded (the post-peel `type_name is None` check catches it); the test would only catch a future regression where someone replaces `while hasattr` with `while gql_type is not None and hasattr(...)`.

```django_strawberry_framework/utils/typing.py:14:18
def unwrap_graphql_type(gql_type: Any) -> Any:
    """Peel all graphql-core / Strawberry ``of_type`` wrapper layers."""
    while hasattr(gql_type, "of_type"):
        gql_type = gql_type.of_type
    return gql_type
```

## What looks solid

### DRY recap

- **Existing patterns reused.** The module is the canonical leaf for type-unwrapping in the package — it imports nothing from the project (only `typing.Any`, `typing.get_args`, `typing.get_origin` at `django_strawberry_framework/utils/typing.py:11`) and is reused by, not reusing. `unwrap_graphql_type` is the canonical peel-the-`of_type`-stack helper consumed at `django_strawberry_framework/optimizer/extension.py:44` (import) → `:338` (inside `_walk_gql_type` for `_collect_schema_reachable_types`) and `:404` (inside `_resolve_model_from_return_type` for the `info.return_type` peel). The prior cycle's `rev-optimizer__extension.md` DRY section at `:13` explicitly records this as the reused seam — the optimizer does NOT re-implement the `GraphQLNonNull` / `GraphQLList` peel. `unwrap_return_type` is exported through `django_strawberry_framework/utils/__init__.py:19,28` but has zero production call sites today (only the test surface at `tests/utils/test_typing.py:4,13,25,37,65` exercises it). The package re-export contract at `utils/__init__.py:19,27-28` matches the sibling shape used for `utils/relations.py` (per `rev-utils__relations.md`'s identity-equal export pattern) and `utils/strings.py`.
- **New helpers a fix might justify.** None today. The module is the right home for the responsibility (Strawberry / Python / GraphQL of_type-and-list wrapper peel) and the two-function split (peel-all-of_type vs peel-one-list-or-of_type layer) is correct given the distinct call-site contracts: graphql-core stacks `NonNull(List(...))` so `unwrap_graphql_type` needs the unbounded loop, while a Strawberry return-type annotation peel needs explicit one-layer semantics so callers can branch on what was peeled.
- **Duplication risk in the current file.** None. Static helper's repeated-literal report at `docs/shadow/django_strawberry_framework__utils__typing.overview.md:40-42` returned "None." The two functions share the `of_type`-attribute peel shape at a *concept* level (both branch on `hasattr(x, "of_type")` / `getattr(x, "of_type", None)`), but at the implementation level they diverge sharply: `unwrap_graphql_type` is a `while`-loop on `hasattr`, `unwrap_return_type` is a single `getattr` plus a `get_origin`/`get_args` list-detection branch. The `of_type` literal appears twice (`:16,45`); collapsing both functions through a single helper would lose the distinct semantics (peel-all vs peel-one, no list-branch vs list-branch) and force callers to opt into the longer signature. Two functions, two contracts, two minimal bodies — correct factoring.

### Other positives

- **Canonical seam for graphql-core type unwrapping.** `unwrap_graphql_type` is the single in-package implementation of the `GraphQLNonNull(GraphQLList(...))` peel-the-`of_type`-stack contract. The prior cycle's `rev-optimizer__extension.md` DRY section at `:13` explicitly records the two optimizer call sites (`extension.py:338,404`) as reused via this helper rather than reimplemented inline. No parallel `while hasattr(..., "of_type")` loop exists anywhere else in the package — confirmed by repo-wide grep.
- **Strawberry-list vs graphql-core split correctly justified by the docstring.** The module docstring at `utils/typing.py:1-9` enumerates the two distinct contracts (graphql-core's `NonNull`/`List` `of_type` wrapper stacks; Strawberry's `typing.list[T]` vs internal `of_type` wrapper) and pins the rationale ("Both contracts live here so optimizer and schema factories do not grow parallel unwrap loops."). The two helpers' different semantics (peel-all vs peel-one, no list-branch vs list-branch) match the two distinct call-shape contracts.
- **`unwrap_return_type` ordering is deliberate and documented.** The docstring at `:33-36` explicitly explains why `getattr(rt, "of_type", None)` runs before `get_origin(rt) is list`: a hypothetical Strawberry wrapper that *also* presents a list-like origin would yield its declared inner type via `of_type` rather than the generic-args inner type. The ordering is load-bearing and the comment block makes the invariant readable for a future maintainer.
- **Test surface covers every documented branch of `unwrap_return_type`.** `tests/utils/test_typing.py:7-13` pins `list[T]` → `T`; `:16-25` pins `FakeStrawberryList(of_type=Inner)` → `Inner`; `:28-37` pins the one-layer-only semantics (`Outer.of_type = list[Inner]` returns `list[Inner]`, not `Inner`); `:59-65` pins the no-wrapper passthrough (`Inner` → `Inner`). The one-layer-only test at `:28-37` is the structural pin that prevents a future maintainer from "fixing" the helper into a while-loop and breaking the documented chain-calls-if-you-need-full-unwrapping contract at `:39-41`.
- **Module-load-time cost is minimal.** Three stdlib imports (`Any`, `get_args`, `get_origin`); no `re`, no project-internal call, no class definitions, no module-level state. Zero circular-import risk; zero side effects at import time.
- **No Django / ORM markers, no control-flow hotspots.** Static helper overview at `docs/shadow/django_strawberry_framework__utils__typing.overview.md:18-24` reports zero `_meta` / `QuerySet` / `Prefetch` / `_prefetched_objects_cache` / `fields_cache` references and zero functions over the 40-line / 8-branch hotspot threshold. The two functions are 5 lines and 6 lines respectively (excluding docstring). Pure stdlib-only leaf module.
- **Helper ran cleanly despite being optional.** Per `worker-1.md`, the helper is only mandatory under `optimizer/` and `types/`; `utils/` is opt-in. Ran anyway because the file is the canonical seam cited from the optimizer subpackage. Overview confirms zero unexpected markers and "Repeated string literals: None."
- **Identity re-export contract.** `utils/__init__.py:19,27-28` re-exports both symbols and the existing test at `tests/utils/test_typing.py:3-4` imports both forms (`from django_strawberry_framework.utils import unwrap_graphql_type` plus `from django_strawberry_framework.utils.typing import unwrap_return_type`), matching the sibling re-export pattern documented in `rev-utils__relations.md` and `rev-utils__strings.md`.

### Summary

`utils/typing.py` is a 50-line, two-function canonical leaf module for Strawberry / Python / GraphQL of_type-and-list wrapper peeling. `unwrap_graphql_type` is the single in-package implementation of the graphql-core `NonNull`/`List` peel stack and is reused at `extension.py:338,404` per the prior optimizer cycle's DRY analysis; `unwrap_return_type` is the parallel one-layer peel for Strawberry return-type annotations, currently with zero production call sites but a complete test surface. 0 High / 0 Medium / 4 Low findings: (L1) `unwrap_return_type` is exported public but unconsumed in production — flag for folder-pass review of `utils/__init__.py`'s public-vs-private contract; (L2) `unwrap_graphql_type`'s docstring could mirror `unwrap_return_type`'s explicit no-wrapper-passthrough framing; (L3) docstring example format diverges from sibling `utils/relations.py` (bullet) and matches `utils/strings.py` (arrow + `;`) — defer to the folder pass per the worker-memory carry-forward for a unified three-sibling decision; (L4) `unwrap_graphql_type(None) is None` is not test-pinned despite the recursion at `extension.py:336-363` relying on the passthrough. No DRY duplication in-file, no logic bugs, canonical seam already established and consumed by the optimizer subpackage. The module is a clean reference shape for a small leaf utility paired across two distinct upstream library contracts (graphql-core, Strawberry).

## Fix report (Worker 2) — 2026-05-20 consolidated pass (logic + comment + changelog)

Single consolidated Worker 2 spawn covering the only two actionable Lows (L2 docstring symmetry, L4 `None`-passthrough test pin) plus the two folder-pass deferrals (L1, L3). Logic + comment edits bundled because the L2 edit is itself a docstring change — no separate comment pass needed once the L4 test lands and L2's docstring framing is in place.

### Edits

- **L4 (test pin)** — added `test_unwrap_graphql_type_passes_through_none` at `tests/utils/test_typing.py:68-78` pinning `unwrap_graphql_type(None) is None`. Docstring cites the `optimizer/extension.py` `_walk_gql_type` recursion that relies on the passthrough so a future maintainer who reads the test understands the load-bearing contract. One-line assertion; no fixtures needed.
- **L2 (docstring symmetry)** — expanded `unwrap_graphql_type`'s docstring at `django_strawberry_framework/utils/typing.py:14-29` to mirror `unwrap_return_type`'s explicit no-wrapper-passthrough framing. Added `Examples:` block listing the canonical `NonNull(List(NonNull(Inner)))` peel, the bare-class passthrough, and the `None` passthrough. Behavior unchanged; docstring only.
- **L1 (public surface without consumer)** — deferred to the `utils/` folder pass per the artifact's own "flag for the folder pass to confirm against `utils/__init__.py`'s public-vs-private contract" recommendation. No edit this cycle.
- **L3 (docstring example format)** — deferred to the `utils/` folder pass per the artifact's own "defer to the folder pass per the worker-memory carry-forward for a unified three-sibling decision" recommendation. No edit this cycle.

### Validation

- `uv run ruff format .` — pass (101 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!).
- `uv run pytest tests/utils/ -x` — 17 passed; the new `test_unwrap_graphql_type_passes_through_none` is included. Coverage warning is the repo-wide aggregate from the focused run, not a regression.

### Notes for Worker 3

- Consolidated single Worker 2 spawn (logic + comment + changelog) because the only two actionable Lows were L2 (docstring) and L4 (test), and the artifact explicitly defers L1 and L3 to the folder pass.
- L2 expanded the docstring with a parallel `Examples:` block; `unwrap_return_type`'s existing examples are unchanged. The two helpers now describe symmetric contracts (peel-all vs peel-one) with parallel passthrough framing.
- L4 test cites the `optimizer/extension.py:336-363` recursion as the load-bearing call site so the contract pin is grep-discoverable from either end.
- L1 / L3 dispositions quoted verbatim from the artifact's own folder-pass deferral language; the upcoming `utils/` folder pass should pick both up alongside the L3 carry-forwards already logged in `worker-memory/worker-2.md` for `utils/relations.py` and `utils/strings.py`.

### Changelog disposition

**Not warranted.** No user-visible behavior change. L2 is docstring polish on `unwrap_graphql_type` (additional `Examples:` block, contract framing unchanged). L4 is an additive internal test pinning behavior that already held. L1 and L3 deferred to the folder pass without code changes. Per `AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed" and the active review plan's silence, no `CHANGELOG.md` edit is made this cycle. Same shape as the `utils/relations.py` and `utils/strings.py` consolidated-single-pass dispositions logged earlier in the cycle (`worker-memory/worker-2.md`).

---

## Verification (Worker 3)

### Logic verification outcome

- **L1 (public surface without consumer)** — deferred to the `utils/` folder pass per Worker 1's own "flag for the folder pass to confirm against `utils/__init__.py`'s public-vs-private contract" prose. Accepted as forward-deferred; the folder pass is the documented re-entry trigger.
- **L2 (docstring symmetry)** — addressed at `django_strawberry_framework/utils/typing.py:14-27`. `unwrap_graphql_type`'s docstring now mirrors `unwrap_return_type`'s explicit no-wrapper-passthrough framing with a parallel `Examples:` block enumerating the `NonNull(List(NonNull(Inner)))` peel, the bare-class passthrough, and the `None` passthrough. Diff confirms the expansion is docstring-only (whitespace + new lines inside the triple-quoted body); the `while hasattr(...)` body is untouched. Symmetry against `unwrap_return_type`'s `Examples:` block at `:50-55` confirmed by re-read.
- **L3 (docstring example format)** — deferred to the `utils/` folder pass per Worker 1's "defer to the folder pass per the worker-memory carry-forward for a unified three-sibling decision" prose. Accepted as forward-deferred; the folder pass owns the unified decision against `utils/relations.py` (bullet) + `utils/strings.py` (arrow + `;`) + `utils/typing.py` (arrow + `;`).
- **L4 (`None`-passthrough test pin)** — addressed via new `test_unwrap_graphql_type_passes_through_none` at `tests/utils/test_typing.py:68-77`. One-line `assert unwrap_graphql_type(None) is None` with a docstring citing the `optimizer/extension.py` `_walk_gql_type` recursion as the load-bearing call site. Grep-verified the test name does not collide with any existing test in the suite.

### DRY findings disposition

DRY analysis claimed no in-file duplication and no new-helper candidates; the cycle's edits (docstring expansion + test pin) preserve the two-helper / two-contract split unchanged. The L3 sibling-docstring-format DRY signal is correctly carried forward to the folder pass rather than collapsed here. No new DRY drift introduced.

### Temp test verification

- No temp tests under `docs/review/temp-tests/` were needed. The L4 test landed directly under the permanent suite at `tests/utils/test_typing.py:68-77` per `AGENTS.md` test placement (a parallel-package test path that already exists). Verified `uv run pytest tests/utils/ -x` collects and passes the new test (17 passed, including `test_unwrap_graphql_type_passes_through_none`).

### Verification outcome

`cycle accepted; verified` — every High/Medium/Low finding addressed or intentionally rejected with reason (L1 + L3 forward-deferred to the folder pass per Worker 1's own prose; L2 + L4 addressed in source/tests); logic + comments (L2 is itself a docstring expansion) + validation (ruff format + ruff check + focused `tests/utils/` all pass) + changelog disposition (not warranted, dual citation: `AGENTS.md` ban + active plan's silence) are all accepted. `git diff -- CHANGELOG.md` confirmed empty. Top-level `Status:` advanced to `verified`.
