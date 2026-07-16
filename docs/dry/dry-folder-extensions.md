# DRY review: folder `django_strawberry_framework/extensions/`

Status: verified

## System trace

`extensions/` is the opt-in home for package-supplied Strawberry
`SchemaExtension`s. Today it is a two-module component with a single public
symbol:

- `__init__.py` — structural opt-in surface only: module docstring, eager
  re-export of `DjangoDebugExtension`, `__all__ = ["DjangoDebugExtension"]`.
  No behavior, no soft-dep gate, no lazy `__getattr__`. Package root
  deliberately does not import or root-export the symbol (TODO notes a future
  joint-cut decision; current contract is the subpackage path).
- `debug.py` — sole owner of the response-extensions debug surface: reference-
  counted `_CursorCaptureCoordinator`, SQL / exception serializers, payload
  builder (two-phase diagnostic degrade), and `DjangoDebugExtension`
  (`on_operation` bracket + stash / `get_results` pure read). Wire keys,
  slow-query threshold, capture fidelity limits, and security disclosure all
  live here.

Folder shape after the verified file reviews: one hard-dep eager public import
(`from django_strawberry_framework.extensions import DjangoDebugExtension`)
and one implementation module. There is no second extension, no shared private
helper hub across modules, and no folder-local state outside `debug.py`'s
module-private `_coordinator` plus per-operation instance stash.

Connected behavior re-traced for this folder pass (not inherited as proven):

- `middleware/debug_toolbar.py` + empty `middleware/__init__.py` — sibling
  *developer* surface: soft-dep HTTP middleware injecting top-level
  `debugToolbar` into tagged GraphQL JSON / GraphiQL HTML. Different seam,
  payload, and dependency story from `extensions["debug"]`.
- `optimizer/extension.py::DjangoOptimizerExtension` — the other shipped
  `SchemaExtension`; root-exported default N+1 recipe with singleton-in-a-
  factory lifetime (plan cache). Opposite intentional lifetime from debug's
  per-operation class entry.
- `utils/typing.py::_MAX_TYPE_WRAPPER_DEPTH` — same numeric ceiling (64) as
  `_MAX_ORIGINAL_ERROR_HOPS`, opposite stop policy (raise vs best-effort
  terminal).
- `exceptions.py` render-safety helpers — protect framework exception
  `str`/`repr` for graphql-core wrapping; not graphene wire-row serialization.
- Consumers / proof: live `examples/fakeshop/test_query/test_debug_extension_api.py`
  (+ multi-db holder in `test_multi_db.py`); package `tests/extensions/test_debug.py`;
  fakeshop aggregate `config/schema.py` deliberately omits the extension.
  Toolbar live suite is a separate product surface
  (`test_debug_toolbar_api.py`).

Folder-level axes examined: duplicated policy across modules, state ownership,
competing helper layers, inconsistent public flavors vs sibling opt-in packages,
lifecycle work repeated at several phases.

## Verification

- Item-scoped baseline `a8141a2cc9e7c0f20aceabd080a64697c2626ea1`:
  `git diff a8141a2… -- django_strawberry_framework/extensions/` is empty
  before and after this pass (no production edits). Concurrent dirty paths
  (`auth/mutations.py`, `auth/queries.py`, `docs/GLOSSARY.md`,
  `docs/dry/dry-0_0_13.md`, `docs/dry/dry-file-exceptions.md`,
  `examples/fakeshop/db.sqlite3`, untracked auth/extensions file artifacts and
  `dry-folder-auth.md`) left untouched. Plan checkbox not edited.
- Re-read both extensions sources end-to-end. Grepped the package for
  `DjangoDebugExtension`, `force_debug_cursor`, `isSlow` / `_SLOW_QUERY`,
  `excType`, `original_error` walks, and `queries_log` slicing: production
  ownership of the response-extensions debug contract is entirely inside
  `extensions/debug.py`. `__init__.py` is import-only. No second payload
  builder, coordinator, or wire-row serializer exists elsewhere under
  `django_strawberry_framework/`.
- Compared export postures across `extensions/`, `middleware/`, `auth/`,
  `optimizer/`, and package root: three distinct dependency/product stories
  (hard eager subpackage opt-in; soft empty marker + leaf import; hard root
  default recipe), not one mutable rule misspelled three ways.
- Read file-pass deferrals in `dry-file-extensions____init__.md` /
  `dry-file-extensions__debug.md` as *flags only*; re-proved each folder-
  visible candidate from source (below).
- No scratch experiment required: the folder has no cross-module policy body
  to execute; import graph + seam comparison suffice.

### Rejected / kept separate

1. **Split or merge `__init__.py` ↔ `debug.py` responsibilities.** No policy is
   duplicated across the two modules. Moving capture/payload into `__init__`
   would blur the leaf-as-implementation / package-as-import-path split;
   emptying `__init__` to match `middleware/` would break the documented
   canonical import for a hard dependency that has no soft-dep boundary to
   defend. Ownership is already correct.

2. **Unify public opt-in flavor with `middleware/__init__.py` (empty marker).**
   Middleware must stay import-clean so
   `import django_strawberry_framework.middleware` succeeds without
   django-debug-toolbar; the opt-in *is* the leaf dotted path in `MIDDLEWARE`.
   `extensions.debug` has only hard dependencies. Forcing the empty-marker
   shape here would be cargo-culting a soft-dep pattern onto a hard-dep
   surface. Rejected.

3. **Root-export `DjangoDebugExtension` beside `DjangoOptimizerExtension`.**
   Optimizer is the default N+1 recipe (root + `optimizer/` re-export).
   Debug is development-only and off by default; subpackage import is the
   structural opt-in signal (mirrored by `auth/`). Collapsing placements would
   erase that signal. Root TODO already defers any surface change to a
   joint version cut — not a DRY consolidation this folder owns.

4. **Consolidate with `middleware/debug_toolbar.py` as one "debug tooling"
   owner.** Different seams (`SchemaExtension` → `extensions.debug` vs HTTP
   middleware → `debugToolbar`), different payloads (SQL + exception rows vs
   toolbar panel metadata / requestId), different dependency stories (hard
   strawberry vs soft django-debug-toolbar with install/app gates). Module
   docstring "counterpart" language is product framing, not shared
   implementation. No code merge; posture docs already cross-link in
   GLOSSARY. Deferred only if a future *project* pass asks whether standing
   docs need tighter dual-wiring cookbook text — not a folder code finding.

5. **Share `SchemaExtension` lifecycle / registration shape with
   `DjangoOptimizerExtension`.** Opposite intentional lifetimes (plan-cache
   singleton factory vs per-operation class instance). Live tests place
   `lambda: _optimizer` beside `DjangoDebugExtension` precisely to document
   the divergence. Collapsing them would break either the plan cache or
   per-operation isolation. Rejected.

6. **Share `_MAX_ORIGINAL_ERROR_HOPS` with
   `utils/typing.py::_MAX_TYPE_WRAPPER_DEPTH`.** Same Power-of-Ten budget,
   different chains and opposite stop policies (best-effort terminal vs
   `RuntimeError`). Importing the typing constant would falsely imply a
   shared invariant. Local constant stays.

7. **Fold diagnostic exception serialization into `exceptions.py` render
   safety.** `exceptions.py` protects framework exception `str`/`repr` so
   graphql-core wrapping cannot destroy typed catchability. Debug serializes
   *arbitrary* execution exceptions to graphene wire rows via
   `traceback.format_exception`. Different contracts and change axes.
   Rejected.

8. **Replace `_CursorCaptureCoordinator` with Django's
   `CaptureQueriesContext`.** Same underlying debug-cursor mechanism;
   deliberately different connection lifecycle (flag-only, overlap-safe
   restore, no eager `connections[alias]` open). Rejected at file pass;
   nothing folder-level adds a second owner to reconcile.

9. **Shared eager-re-export helper across auth/utils/testing/extensions.**
   Packaging idiom, not a mutable rule with one change axis. A helper would
   add indirection without consolidating policy. Rejected.

10. **Promote live-test probe URLconf / holder pattern** shared with
    `test_multi_db.py`. Spec-044 DRY D3 already records "copied — not
    promoted." Test-placement rules prefer independently legible acceptance
    fixtures. Out of scope for production folder ownership.

## Opportunities

None — the folder already has a single authoritative split: `__init__.py`
owns the hard-dep public import path; `debug.py` owns every rule, payload
shape, capture lifecycle, and security disclosure for
`extensions["debug"]`. No duplicated policy is split across modules, no
competing helper layer exists inside the folder, and the apparent "inconsistent
public flavors" vs middleware/optimizer/auth are intentional product/dependency
boundaries, not drift.

## Judgment

Zero-edit. `extensions/` is a thin, correctly bounded opt-in component: one
export marker, one implementation owner, no cross-module policy to collapse.
Strongest near-duplicates (toolbar middleware, optimizer lifetime, typing
unwrap ceiling, exceptions render safety, Django `CaptureQueriesContext`) were
independently disproved as shared contracts. Ready for Worker 2.

## Implementation (Worker 1)

No source changes. Item-scoped diff against
`a8141a2cc9e7c0f20aceabd080a64697c2626ea1` for
`django_strawberry_framework/extensions/` remains empty. Only new path for
this item is this artifact. No new tests (behavior unchanged; live suite in
`examples/fakeshop/test_query/test_debug_extension_api.py` and package suite
in `tests/extensions/test_debug.py` already cover the contracts traced).
`ruff format` / `ruff check --fix` not run — no production or test edits.
No changelog. Plan checkbox left untouched (Worker 2 closes the item).
Status `fix-implemented` as a proved zero-edit handoff.

## Independent verification (Worker 2)

Re-traced `extensions/` as one component from source (both modules end-to-end),
package root / `auth/` / `middleware/` / `optimizer/` export postures, the two
`SchemaExtension` subclasses in the package, toolbar payload injection, and
consumer import sites. Did not treat Worker 1's rejected list as proven.

**Scoped diff.** `git diff a8141a2cc9e7c0f20aceabd080a64697c2626ea1 --
django_strawberry_framework/extensions/` is empty (0 bytes). Folder contents
remain exactly `__init__.py` + `debug.py`. No production edits in this pass.

**Ownership re-check.** Grep for `DjangoDebugExtension`, `force_debug_cursor`,
`isSlow` / `_SLOW_QUERY`, `excType`, `_CursorCaptureCoordinator`, and
`extensions["debug"]` wire construction: every production owner sits inside
`extensions/debug.py`. `__init__.py` is docstring + eager re-export +
`__all__` only. No second payload builder, coordinator, or wire-row serializer
exists under `django_strawberry_framework/`.

**Challenged rejected candidates (required).**

1. **`middleware/debug_toolbar.py` merge.** Still rejected. Toolbar injects a
   top-level HTTP JSON key `debugToolbar` (`requestId` + panel title/subtitle
   metadata) via soft-dep middleware with install/app gates; debug publishes
   GraphQL `extensions["debug"]` (`sql` / `exceptions` graphene wire rows) via
   hard-dep `SchemaExtension.on_operation` / `get_results`. No shared
   serializers, wire keys, capture lifecycle, or dependency boundary. Docstring
   "counterpart" language is product framing only. Dual-wiring cookbook text,
   if ever wanted, is a project-docs question — not a folder code merge.

2. **`DjangoOptimizerExtension` lifetime / registration shape.** Still
   rejected. Optimizer is the only other `SchemaExtension` in the package; it
   keeps an instance-bound plan cache and must be listed as
   `lambda: _optimizer`. Debug stashes per-operation payload on the instance
   and must be listed as the class so Strawberry constructs a fresh object each
   operation. Shared registration helper or shared lifecycle base would need a
   mode flag and would break either the cache or isolation. Live/docs examples
   that place both side-by-side document the divergence deliberately.

**Other folder-visible rejects re-proved (brief).** Empty-marker `__init__` to
mirror middleware would break the hard-dep canonical import; root-exporting
debug beside the optimizer would erase the structural opt-in signal (root TODO
defers any surface change to a joint cut); `_MAX_ORIGINAL_ERROR_HOPS` vs
`_MAX_TYPE_WRAPPER_DEPTH` share a budget number with opposite stop policies;
`exceptions.py` render safety vs debug wire serialization remain distinct
contracts; `CaptureQueriesContext` still differs on connection open /
overlap-safe restore; eager-re-export helper and live-test probe URLconf
patterns are packaging/test-placement idioms, not mutable folder policy.

**Missed opportunities.** None found. No duplicated policy split across the
two modules, no competing helper layer, no unclear state ownership outside
`debug.py`'s module-private `_coordinator` and per-operation instance stash,
and no inconsistent public flavor that is actually the same rule misspelled.

**Disposition.** Zero-edit stands. Status → `verified`. Plan checkbox for
folder integration `extensions/` marked complete. Unrelated dirty / untracked
paths left untouched. No commit.
