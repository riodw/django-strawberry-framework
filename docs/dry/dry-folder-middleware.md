# DRY review: folder `middleware/`

Status: verified

## System trace

`middleware/` is the package's Django HTTP-middleware home. Today it is two
modules with one public contract:

- `middleware/__init__.py` — import-clean package marker. Imports nothing
  optional so `import django_strawberry_framework.middleware` (and whole-package
  walkers) succeed without `django-debug-toolbar`. Deliberately re-exports
  nothing; the consumer-facing surface is the full leaf dotted path in
  `MIDDLEWARE`.
- `middleware/debug_toolbar.py` — sole implementation leaf.
  `DebugToolbarMiddleware` subclasses stock
  `debug_toolbar.middleware.DebugToolbarMiddleware`, tags Strawberry Django
  views in `process_view`, and in `_postprocess` appends the GraphiQL bridge
  template / injects the `debugToolbar` JSON payload (skipping
  `IntrospectionQuery`). Soft-dependency opt-in is leaf import:
  `require_debug_toolbar()` then an `apps.is_installed("debug_toolbar")` gate
  before the toolbar imports. Template lives under
  `templates/django_strawberry_framework/debug_toolbar.html`.

Callers and contracts examined:

- Fakeshop wiring (`examples/fakeshop/config/settings.py`) lists the leaf
  dotted path, replacing the stock toolbar entry.
- Package tests (`tests/middleware/test_debug_toolbar.py`) and live HTTP
  acceptance (`examples/fakeshop/test_query/test_debug_toolbar_api.py`).
- Soft-dependency primitive
  `utils/imports.py::require_optional_module` and sibling guards
  `rest_framework/__init__.py::require_drf`, `routers.py::require_channels`.
- Sibling debug surface `extensions/debug.py::DjangoDebugExtension` (in-response
  `extensions["debug"]`) and `extensions/__init__.py` (eager re-export of a
  hard-dependency class) — intentional counterpart, not a parallel middleware
  owner.
- Glossary / TREE entries for Debug-toolbar middleware confirm the leaf-path
  opt-in and the no-package-re-export rule.

Folder-level ownership is already sharp: the package marker owns the
import-clean / no-re-export boundary; the leaf owns install-hint strings,
`INSTALLED_APPS` gating, view tagging, and response mutation. No second
helper layer, registry, or alternate public flavor exists inside the folder.

## Verification

- Item-scoped baseline diff
  (`git diff 22c1ce273648dd5a2909847f1d3777cf62ba660f -- django_strawberry_framework/middleware/`)
  is empty before this pass.
- Searched package-wide for `_is_graphiql`, `debugToolbar`, `_get_payload`,
  `IntrospectionQuery`, `require_debug_toolbar`, and
  `DebugToolbarMiddleware`: production ownership is only
  `middleware/debug_toolbar.py` (+ its template). No competing injector or
  tagger.
- Compared soft-dep shapes: `rest_framework/` guards at package `__init__`
  because many submodules need DRF; `middleware/` has one leaf, so
  guard-on-leaf + empty package marker is the correct dual of that pattern,
  not a drift to unify.
- Compared `extensions/` vs `middleware/`: extensions eagerly re-export a
  hard-dependency `SchemaExtension`; middleware refuses re-export to keep the
  soft dependency behind `import_string` of the leaf. Same English word
  "debug" / "opt-in", different seams and dependency laws — must not share a
  facade.
- Within-leaf `Content-Length` refresh appears on both HTML-append and
  JSON-rewrite arms of `_postprocess`. Same two-line header update, two
  distinct mutation paths; extracting a helper would not move a shared
  *policy* and is outside folder-boundary duplication.

## Opportunities

None — the folder already encodes one responsibility per module, with the
soft-dependency install/app gates and GraphQL response policy sited once in
the leaf. The package marker's docstring restates the no-re-export rule that
the leaf's docstring also mentions; that is boundary documentation for two
arrival paths (package import vs `MIDDLEWARE` wiring), not duplicated
executable policy. Cross-package soft-dep raising already owns one primitive
(`require_optional_module`); thin per-feature wrappers remain correctly local.

## Judgment

Zero-edit folder pass. `middleware/` is a minimal, correctly split component:
import-clean marker + one soft-dep leaf. Strongest rejected candidates are
(1) collapsing `__init__` / leaf soft-dep narrative into a single doc site,
(2) sharing structure or code with `extensions/debug`, and (3) inventing a
shared "soft-dep package" abstraction across `middleware/` and
`rest_framework/` despite their different fan-out. Ready for Worker 2.

## Implementation (Worker 1)

No tracked source changes. Owner remains split as today: package marker for
import-clean / no-re-export; `debug_toolbar.py` for all toolbar behavior and
guards. Item-scoped production diff vs
`ITEM_BASELINE` `22c1ce273648dd5a2909847f1d3777cf62ba660f` stays empty; only
this artifact is new. No changelog. No pytest (not the final gate).

## Independent verification (Worker 2)

Re-traced `middleware/` as one component from source: docstring-only
`__init__.py` (no defs/imports/re-exports), full `debug_toolbar.py` (install
hint, `require_debug_toolbar`, apps gate, `_get_payload`,
`DebugToolbarMiddleware.process_view` / `_postprocess`), bridge template under
`templates/django_strawberry_framework/debug_toolbar.html`, soft-dep siblings
(`rest_framework/__init__.py::require_drf`, `routers.py::require_channels`,
`utils/imports.py::require_optional_module`), hard-dep counterpart
`extensions/__init__.py` + `extensions/debug.py`, fakeshop `MIDDLEWARE` leaf
path, and both toolbar test trees. Did not treat Worker 1 findings as proven.
Did not concatenate the verified file artifacts.

**Scoped diff.** `git diff 22c1ce273648dd5a2909847f1d3777cf62ba660f --
django_strawberry_framework/middleware/` is empty (0 bytes). Folder contents
remain exactly `__init__.py` + `debug_toolbar.py`. No production edits in this
pass.

**Ownership re-check.** Grep for `_is_graphiql`, `debugToolbar`, `_get_payload`,
`IntrospectionQuery`, `require_debug_toolbar`, `DebugToolbarMiddleware`, and
`_DEBUG_TOOLBAR_*`: every production owner sits inside
`middleware/debug_toolbar.py` (+ the HTML asset it appends). Package marker
defines no symbols. No second injector, tagger, registry, or public flavor
inside the folder. Consumers reach the class only via the leaf dotted
`MIDDLEWARE` string.

**Challenged rejected candidates (required).**

1. **Collapse `__init__` / leaf soft-dep narrative into one doc site.** Still
   rejected. Marker docstring owns the package-import arrival contract
   (walkers / toolbar-absent `import …middleware`); leaf docstring owns
   `MIDDLEWARE` `import_string` opt-in, install/app gates, and GraphQL
   mutation policy. Shared English about soft-dep / no-re-export is boundary
   documentation for two arrival paths, not duplicated executable policy.
   Merging docs would hide one arrival seam. Holds.

2. **Share structure or code with `extensions/debug`.** Still rejected.
   Toolbar: soft-dep HTTP middleware → top-level JSON key `debugToolbar`
   (`requestId` + panel metadata) + GraphiQL HTML bridge. Extensions: hard-dep
   `SchemaExtension` → `extensions["debug"]` (SQL / exception wire rows). No
   shared serializers, wire keys, capture lifecycle, or dependency boundary.
   Confirmed independently by the verified extensions folder pass; dual-wiring
   cookbook text would be docs, not a folder merge. Holds.

3. **Shared "soft-dep package" abstraction with `rest_framework/`.** Still
   rejected. `rest_framework/` has six Python modules and guards at package
   `__init__` because package import *is* the consumer opt-in for many
   submodules. `middleware/` has one leaf; Django resolves the class by leaf
   dotted path, so guard-on-leaf + empty marker is the correct dual. A shared
   package template would need a fan-out / opt-in-posture mode flag and would
   break either walkers or DRF's multi-module gate. Thin wrappers over
   `require_optional_module` already share the only common raising primitive.
   Holds.

**Missed folder-level opportunities searched.** None found that meet the DRY
bar. Within-leaf twin `Content-Length` refreshes are two mutation arms of one
`_postprocess`, not cross-module policy. Template living under
`templates/` is Django asset layout, owned by the leaf's `render_to_string`
path — not a second middleware module. Install-hint floor agreement with
`pyproject.toml` / tests is the intentional three-places contract, not
folder-internal duplication. Zero-edit judgment stands.
