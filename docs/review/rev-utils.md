# Folder review: `django_strawberry_framework/utils/`

Sibling artifacts read for this pass:

- `docs/review/rev-utils__relations.md`
- `docs/review/rev-utils__strings.md`
- `docs/review/rev-utils__typing.md`

## High:

None.

## Medium:

None.

## Low:

### `utils/` is the right home for cross-cutting helpers, but no enforcement

The subpackage docstring documents the convention: focused submodules per concern rather than a single broad `utils.py`. The convention is still policy rather than tooling enforcement. Note for monitoring; do not act yet.

### Per-file Low items are all documentation polish

The older per-file Low items for `strings.py` and `typing.py` were docstring or comment improvements that did not change behavior. They can remain deferred unless the maintainer wants a dedicated comment-polish pass.

## What looks solid

- **Public surface is narrow.** `utils/__init__.py` re-exports the consumer-facing helpers, while `relations.py` is intentionally consumed through its dotted module path by package internals.
- **Bottom of the import graph.** `utils/strings.py` has no imports, `utils/typing.py` imports only `typing`, and `utils/relations.py` imports only `typing`; no circular-import risk back into the package.
- **Single-responsibility per submodule.** `strings` owns case conversion, `typing` owns return-type unwrapping, and `relations` owns Django relation-shape classification.
- **Relation classification now lives at the correct cross-cutting boundary.** It is shared by optimizer and type-system modules without moving caller-specific annotation, resolver, or plan logic into `utils/`.
- **Coverage.** Existing integration tests cover the older utilities, and direct `tests/utils/test_relations.py` coverage pins the new relation helper.

---

### Summary:

Small, well-scoped utils subpackage. No High/Medium issues; the new `relations.py` helper fits the documented focused-submodule convention and removes cross-package relation-shape duplication.

---

### Worker 3 verification

- Closeout DRY fix: `utils/relations.py` now owns shared relation cardinality classification and is covered by direct tests.
- Low items remain monitor-only documentation polish.
- Validation: `uv run ruff format`, `uv run ruff check`, and `uv run pytest -q` passed; tests reported 360 passed, 4 skipped, 100% coverage.
- Checkbox in `docs/review/review-0_0_3.md`: marked `- [x]`.
