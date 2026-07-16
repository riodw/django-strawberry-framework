# DRY review: `django_strawberry_framework/middleware/__init__.py`

Status: verified

## System trace

The target is an 11-line docstring-only package marker. It defines no names,
imports, guards, or re-exports. Owned responsibility:

- keep `import django_strawberry_framework.middleware` import-clean so whole-
  package walkers (`docs/TREE.md` renderer, coverage collection) and toolbar-
  absent machines never pull `django-debug-toolbar`;
- refuse re-export so the consumer-facing surface stays the full leaf dotted
  path in a `MIDDLEWARE` settings string
  (`…middleware.debug_toolbar.DebugToolbarMiddleware`);
- document that leaf import is the soft-dependency opt-in (spec-042 Decisions
  3/4/5).

Connected behavior examined:

- `middleware/debug_toolbar.py` — owns `require_debug_toolbar()`, install hint,
  `INSTALLED_APPS` gate, and `DebugToolbarMiddleware`. Sibling file item still
  open; traced only as the leaf that must stay off this marker.
- Soft-dep siblings with *different* opt-in boundaries:
  - `rest_framework/__init__.py` — package import *is* the opt-in (`require_drf()`
    at import time);
  - `routers.py` — module import stays clean; PEP 562 `__getattr__` +
    `require_channels()` fires on symbol access;
  - this marker — package import stays clean; leaf import is the opt-in
    (Django `import_string` on the `MIDDLEWARE` dotted path).
- Shared primitive: `utils/imports.py::require_optional_module` (already the
  single raising owner; thin wrappers stay at feature owners).
- Hard-dep contrast: `extensions/__init__.py` eagerly re-exports
  `DjangoDebugExtension` — no soft dep to defend.
- Empty namespace marker: `management/__init__.py` (Django management package
  marker, no optional dep) — same emptiness shape, unrelated change axis.
- Tests: `tests/middleware/test_debug_toolbar.py::test_package_and_middleware_imports_stay_clean_without_toolbar`
  asserts parent import under toolbar absence; leaf raise / restore / apps-gate
  tests hang off `_PARENT` / `_LEAF` constants.
- Consumers: `examples/fakeshop/config/settings.py` and standing docs use the
  leaf dotted path only; nothing imports symbols from the package marker.
- Baseline `git diff e6fbddb32902503acfc46c1deb65ba9558870bed -- …/middleware/__init__.py`
  is empty; working tree matches baseline for this file.

## Verification

Searches:

- `django_strawberry_framework.middleware` / `DebugToolbarMiddleware` /
  `require_debug_toolbar` across package, tests, examples, docs — production
  consumers hit the leaf path; the parent package is only imported for the
  import-clean contract and two-sided restore.
- Package `__init__.py` files for eager `__all__`, PEP 562 `__getattr__`, and
  empty soft-dep markers — three soft-dep opt-in postures (package-raise,
  symbol-lazy, leaf-import) plus hard-dep eager re-export; each tied to how
  the consumer reaches the feature.
- Concept search for “middleware package surface” / “import-clean by design” —
  only this file owns that marker contract for debug-toolbar.

Rejected / deferred candidates (tried to disprove shared ownership):

1. **Move `require_debug_toolbar()` onto this `__init__` (mirror
   `rest_framework/__init__.py`).** Disproved: DRF package import *is* the
   consumer opt-in; middleware consumers reach the class via Django
   `MIDDLEWARE` `import_string` of the *leaf*. Guarding the parent would break
   walkers and `test_package_and_middleware_imports_stay_clean_without_toolbar`,
   and erase spec-042 Decisions 3/4/5.
2. **Re-export `DebugToolbarMiddleware` from this package (mirror
   `extensions/__init__.py`).** Disproved: extensions has no soft dependency;
   an eager re-export here would import the leaf and fire the toolbar guard on
   any parent import. Canonical consumer path is already the leaf dotted string.
3. **PEP 562 lazy export of the middleware class from this package (mirror
   `routers.py`).** Disproved: Django middleware wiring is a settings *string*
   resolved by `import_string`, not `from … import Name`. A lazy package export
   would not serve the primary consumer path and would add a second public
   surface for the same class.
4. **Shared “empty soft-dep package marker” helper / template with
   `management/__init__.py`.** Disproved: shared emptiness is a packaging
   idiom, not a mutable rule. Management has no optional dependency; merging
   markers would couple unrelated namespaces.
5. **Collapse docstring / leaf docstring / glossary / README wording about
   “parent stays clean, leaf is opt-in”.** Disproved for this file: standing
   docs document the public contract; the module docstring states the local
   import-clean invariant; the leaf owns guard/hint text. Not production-code
   duplication this owner can consolidate. Guard/hint ownership stays in
   `debug_toolbar.py` (sibling item).
6. **Policy / middleware behavior living in `__init__.py`.** Absent — all
   runtime policy is in the leaf. Folder integration and the `debug_toolbar.py`
   file pass own any cross-module policy questions.

No scratch experiment required: the file has no executable body; import-graph
contracts and the permanent absence test are sufficient.

## Opportunities

None — the target already is the single authoritative import-clean boundary for
the middleware subpackage. Soft-dep raising, install-hint text, apps wiring,
and middleware behavior correctly live on the leaf. Aligning this marker with
`rest_framework` or `extensions` would erase a deliberate, tested opt-in
posture, not remove duplication.

## Judgment

Zero-edit. Thin, correctly bounded soft-dep package marker; no consolidation
this file owns. Sibling `debug_toolbar.py` and folder `middleware/` remain the
places for guard/behavior and package-integration DRY work. Ready for Worker 2.

## Implementation (Worker 1)

No tracked source edits. Item-scoped diff vs `ITEM_BASELINE`
(`e6fbddb32902503acfc46c1deb65ba9558870bed`) remains empty for the target.
Artifact only. Concurrent dirty paths left untouched. Plan checkbox not
flipped. No ruff run (no Python edits). No pytest. No commit.

## Independent verification (Worker 2)

Scoped diff vs `ITEM_BASELINE`
(`e6fbddb32902503acfc46c1deb65ba9558870bed`) is empty; `cmp` confirms the
working tree matches the baseline blob byte-for-byte for
`django_strawberry_framework/middleware/__init__.py`. No production edits in
this pass.

Re-traced independently:

- Target is still an 11-line module docstring with no symbols, imports,
  `__all__`, guards, or re-exports. Runtime import exposes `public []`, no
  `__all__`, empty non-dunder `vars`.
- Soft-dep opt-in postures re-checked at the three feature owners:
  `rest_framework/__init__.py` raises on package import; `routers.py` uses
  PEP 562 + `require_channels()` on symbol access; this marker stays clean and
  leaves opt-in to the leaf (`debug_toolbar.py` runs `require_debug_toolbar()`
  at import). Hard-dep contrast `extensions/__init__.py` eagerly re-exports —
  no soft boundary to defend.
- Consumers: fakeshop `MIDDLEWARE` and standing docs use only the leaf dotted
  path; `tests/middleware/test_debug_toolbar.py::test_package_and_middleware_imports_stay_clean_without_toolbar`
  locks parent import under toolbar absence; two-sided restore asserts
  `parent.debug_toolbar is leaf`. Nothing imports symbols from this marker.
- `management/__init__.py` is an empty namespace marker without an optional
  dependency — same emptiness shape, unrelated change axis.
- `Import-clean by design` / `deliberately NO re-export` wording appears only
  in this file's production docstring (leaf + glossary restate the contract in
  their own domains; not a second production owner).

Challenges to rejected candidates (all stand):

1. **Move `require_debug_toolbar()` onto this `__init__`.** DRF package import
   *is* the opt-in; middleware consumers reach the class via Django
   `import_string` of the *leaf*. Guarding the parent would break walkers and
   the absence test, and erase spec-042 Decisions 3/4/5.
2. **Re-export `DebugToolbarMiddleware` here (extensions shape).** Extensions
   has no soft dep; an eager re-export would fire the toolbar guard on any
   parent import. Canonical path is already the leaf dotted string.
3. **PEP 562 lazy export from this package (routers shape).** Django middleware
   wiring is a settings string, not `from … import Name`. Lazy package export
   would not serve the primary path and would add a second public surface.
4. **Shared empty soft-dep marker helper with `management/__init__.py`.**
   Packaging idiom only; management has no optional dependency. Merging
   markers would couple unrelated namespaces.
5. **Collapse docstring / leaf / glossary / README wording.** Standing docs and
   the leaf own their surfaces; this marker states the local import-clean
   invariant. Not production-code duplication this file can consolidate.
6. **Policy living in `__init__.py`.** Absent — all runtime policy is on the
   leaf. Folder / `debug_toolbar.py` items own remaining questions.

Missed opportunities searched for (none found): alternate consumer import of
package-level symbols; a fourth soft-dep package-marker posture; shared
install-hint / guard ownership that belongs on this file rather than the leaf;
`TYPE_CHECKING` re-export as a covert second surface (still unused by
`import_string`, still a second API).

**Disposition:** verified. Plan item checked.
