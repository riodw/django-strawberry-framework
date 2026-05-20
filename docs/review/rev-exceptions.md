# Review: `django_strawberry_framework/exceptions.py`

Status: verified

## DRY analysis

- Existing patterns reused: the file defines the package's exception root and does not call into anything (zero imports beyond the implicit `Exception`). All sibling modules that need these classes import them from here — `django_strawberry_framework/conf.py:44`, `django_strawberry_framework/registry.py:24`, `django_strawberry_framework/types/converters.py:26`, `django_strawberry_framework/types/finalizer.py:8`, `django_strawberry_framework/types/relay.py:35`, `django_strawberry_framework/types/resolvers.py:29`. No sibling redefines or shadows any of the three names; the canonical-error helper `Registry._already_registered` at `django_strawberry_framework/registry.py:66-73` is built on top of `ConfigurationError` rather than introducing a parallel hierarchy.
- New helpers a fix might justify: none. The file has no logic surface — no constructors, no factory functions, no message templates. Any error-message DRY work (e.g., consolidating "already registered" phrasings) belongs in the modules that *raise*, not here.
- Duplication risk in the current file: none. Three `class` declarations with docstrings only, an `__all__` tuple in alphabetical order, and a module docstring. No repeated literals, no near-copies, no drift against a sibling module.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

- **Static helper deliberately skipped.** Per `docs/review/worker-1.md` ("Worker 1 may skip the helper for: Pure-class-definition modules whose body is only `class` declarations with docstrings (e.g., `exceptions.py`)"), the file is exactly that shape: module docstring, `__all__`, then three empty class bodies whose only content is a docstring. No imports beyond the implicit `Exception` base, no functions, no module-level statements with branching, no reflective access, no ORM markers — there is nothing for the helper to surface beyond what one read of the 45-line file already shows.
- **Documented surface matches the package contract.** `AGENTS.md` line 8 names this file as defining `DjangoStrawberryFrameworkError`, `ConfigurationError`, and `OptimizerError`; `__all__` exposes exactly those three in alphabetical order (`exceptions.py:8-12`) and the class definitions match (`exceptions.py:15`, `:24`, `:37`). No undocumented surface, no missing surface.
- **Hierarchy is the maximally DRY shape for a base + two leaves.** `ConfigurationError` and `OptimizerError` both inherit from `DjangoStrawberryFrameworkError`, which inherits from `Exception`. Consumers can catch one base for blanket handling or either leaf for granular handling; the docstrings call this contract out at `exceptions.py:16-21`.
- **Bottom-of-graph placement is honored.** The module docstring asserts "no Django, no Strawberry, no internal package imports" (`exceptions.py:1-6`) and the file body matches — zero `import` statements, so no circular-import risk and no import-time side effects. Every consumer site uses either `from .exceptions import ...` or `from ..exceptions import ...` (see grep results across `conf.py`, `registry.py`, `types/converters.py`, `types/finalizer.py`, `types/relay.py`, `types/resolvers.py`); nothing redefines or shadows the names.
- **Docstrings already describe consumer-visible constraints.** `ConfigurationError`'s docstring enumerates the four canonical trigger shapes (missing `Meta.model`, `fields`+`exclude` together, deferred-surface key before its spec ships, duplicate model registration) and `OptimizerError`'s docstring frames the typical cause (registry miss for a type that should have been registered by `DjangoType.__init_subclass__`). Comment pass will have nothing to add unless a future slice expands the trigger list.

### Summary

`exceptions.py` is a pure-class-definition module of 45 lines: module docstring, `__all__`, and three class declarations whose only content is a docstring. The helper was skipped per the worker-1 dictum for this shape, and a rigorous read confirms there is no review-worthy logic, branching, or reflective-access surface to flag. The documented hierarchy matches `AGENTS.md`, the `__all__` exposes the three names in alphabetical order, the module imports nothing (preserving its bottom-of-graph placement), and every consumer site across the package imports from here rather than redefining. All severities are `None.`; downstream sections proceed as a skip lifecycle per `REVIEW.md` "Skip artifact for low-surface logic".

---

## Fix report (Worker 2)

### Files touched

- None.

### Tests added or updated

- None.

### Validation run

- `uv run ruff format .` — pass (no changes; 100 files left unchanged).
- `uv run ruff check --fix .` — pass (no changes; all checks passed).

### Notes for Worker 3

Skip artifact; no source changes; no shadow file used. This is a consolidated no-op skip cycle per `REVIEW.md` "Skip artifact for low-surface logic" and "No-op and skip lifecycle" — the Fix report, the comment pass, and the changelog disposition are all recorded together in this single Worker 2 pass.

---

## Verification (Worker 3)

### Logic verification outcome

All severities `None.` — accepted. Re-read `exceptions.py` end-to-end: 45 lines comprising a module docstring, an alphabetically-ordered `__all__` tuple, and three exception classes whose bodies are docstrings only. No imports, no functions, no branching, no reflective access, no ORM markers — nothing the skip artifact's rationale overlooked. Spot-checked the cited line ranges (`exceptions.py:1-6`, `:8-12`, `:15`, `:24`, `:37`) and they match the file.

### DRY findings disposition

All three DRY bullets are accurate. The file calls nothing (no imports beyond the implicit `Exception` base), no new helpers are justified at this site (any error-message DRY belongs in the raising modules), and there is no in-file duplication. Spot-checked the consumer-site imports via grep — all six land on `ConfigurationError` or `OptimizerError` from this module: `conf.py:44`, `registry.py:24`, `types/converters.py:26`, `types/finalizer.py:8`, `types/relay.py:35`, `types/resolvers.py:29`. Accepted.

### Temp test verification

None used. Not warranted for a no-op skip cycle on a pure-class-definition module.

### Verification outcome

cycle accepted; verified

---

## Comment/docstring pass

No-op skip cycle. No comments or docstrings updated; the existing module docstring and the three class docstrings already describe the surface accurately per the artifact's `What looks solid` section.

---

## Changelog disposition

- **Warranted?** Not warranted.
- **Reason:** skip cycle on a pure-class-definition module with no source changes. No user-visible / API / behavioral change. Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed.") and the active plan (no changelog authorization), no `CHANGELOG.md` edit.
- **What was done:** no `CHANGELOG.md` edit. Disposition recorded in this artifact.
- **Validation run:** the two ruff commands recorded once in the Fix report above cover the whole no-op pass (`uv run ruff format .` — pass/no-changes; `uv run ruff check --fix .` — pass/no-changes). `pytest` was not run, per Worker 2 standing rules for no-op skip cycles.

---

## Iteration log

(none)
