# Folder review: `django_strawberry_framework/utils/`

Sibling artifacts read for this pass:

- `docs/review/rev-utils____init__.md`
- `docs/review/rev-utils__strings.md`
- `docs/review/rev-utils__typing.md`

## High:

None.

## Medium:

None.

## Low:

### `utils/` is the right home for cross-cutting helpers, but no enforcement

The subpackage docstring documents the convention: "focused submodules per concern rather than a single 500-line `utils.py`." Today there are two submodules (`strings`, `typing`) and a documented future `queryset` submodule. There is nothing in the import graph or in the package's tooling that would prevent a future contributor from re-introducing a flat `utils.py` or piling unrelated helpers into one of the existing submodules. Note for monitoring; do not act yet.

### Per-file Low items are all documentation polish

Each per-file artifact's Low items (acronym handling in `snake_case`, underscore-collapse trade-off in `pascal_case`, one-layer-only contract in `unwrap_return_type`, wrapper-vs-origin priority comment) are docstring or comment improvements that do not change behavior. They can be batched into one comment-pass commit if the maintainer prefers; otherwise individual deferrals are fine.

## What looks solid

- **Public surface is narrow.** `utils/__init__.py` re-exports exactly three names (`pascal_case`, `snake_case`, `unwrap_return_type`) — the helpers consumed by the optimizer and the type system. Nothing leaks beyond that.
- **Bottom of the import graph.** `utils/strings.py` has no imports; `utils/typing.py` imports only `typing`. No circular-import risk back into the rest of the package.
- **Single-responsibility per submodule.** `strings` for case conversion, `typing` for return-type unwrapping. No mixing.
- **Convention statement is in the right place.** The subpackage docstring pins the design ("focused submodules per concern") rather than relying on README or contributor docs. New contributors editing the package see the rule immediately.
- **Future-spec hint is anchored.** The deferred `queryset` submodule is mentioned with its trigger ("when queryset-introspection helpers become cross-cutting"), matching AGENTS.md's pattern for staged future work.
- **Coverage.** 100% across the suite via integration tests in the optimizer and types subpackages.

---

### Summary:

Tiny, well-scoped utils subpackage. No High/Medium issues; the Low items are entirely documentation polish on the per-file functions and a monitoring note that the "focused submodules" convention is documented but not enforced.

---

### Worker 3 verification

- No source changes this folder pass. All Low items deferred per the artifact's monitor-only disposition.
- Validation: `uv run pytest -q` -> 353 passed, 4 skipped, 100% coverage.
- Checkbox in `docs/review/review-0_0_3.md`: marked `- [x]`.
