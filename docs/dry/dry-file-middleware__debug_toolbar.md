# DRY review: `django_strawberry_framework/middleware/debug_toolbar.py`

Status: verified

ITEM_BASELINE: `e57baab6aba3c3eb7374f90fc7c181b99ef9eb4a`

## System trace

The target owns the package's **soft `django-debug-toolbar` GraphQL bridge**:
import-time opt-in, the two GraphQL-shaped middleware overrides, and the JSON
panel-payload builder. Everything else (panels, request tracking, history,
handle rendering, show-toolbar gating) stays the stock toolbar's.

Owned responsibilities (already single-sited in this leaf):

1. **Soft-dep install gate** — `_DEBUG_TOOLBAR_INSTALL_HINT` +
   `require_debug_toolbar()` wrapping
   `utils/imports.py::require_optional_module`; called at module import time
   so `import django_strawberry_framework` /
   `import django_strawberry_framework.middleware` stay clean while Django's
   `MIDDLEWARE` `import_string` of the leaf dotted path is the consumer opt-in.
2. **Soft-dep apps gate** — `_DEBUG_TOOLBAR_APP_HINT` +
   `apps.is_installed("debug_toolbar")` → `ImproperlyConfigured` before the
   `debug_toolbar.middleware` import defines `HistoryEntry` (unique second
   wiring gate among the package's soft deps; DRF/channels have no model
   registration side effect).
3. **View tagging** — `DebugToolbarMiddleware.process_view` sets
   `request._is_graphiql` when `view_func.view_class` is a class subclassing
   `strawberry.django.views.BaseView`, with the deliberate
   `isinstance(view, type)` guard so a non-class attribute cannot `TypeError`
   unrelated traffic.
4. **Response mutation** — `_postprocess` chains `super()` first, then: HTML
   GraphiQL 200 → append
   `templates/django_strawberry_framework/debug_toolbar.html`; tagged
   `application/json` (non-`IntrospectionQuery`) → re-encode with
   `_get_payload`'s top-level `debugToolbar` object; streaming / untagged /
   non-object / undecodable bodies left alone; `Content-Length` refreshed only
   when already present.
5. **Panel payload shape** — `_get_payload` owns `requestId` + per-panel
   `title` / `subtitle` (callable resolution, `has_content` → `title is None`,
   `TemplatesPanel` skip) using upstream's `OrderedDict` / `DjangoJSONEncoder`
   wire shape.

Connected surfaces traced (evidence, not co-owners of this wire contract):

- **`middleware/__init__.py`** — docstring-only import-clean marker; no
  re-export. Leaf import remains the opt-in (already verified under that file
  item).
- **`utils/imports.py::require_optional_module`** — shared raising primitive
  for all soft deps; this leaf is one thin wrapper among
  `require_drf` / `require_channels` / `require_debug_toolbar`.
- **`rest_framework/__init__.py` / `routers.py`** — sibling soft-dep *postures*
  (package-import raise vs PEP 562 symbol-lazy), not shared GraphQL/toolbar
  behavior; only the install-hint + `require_optional_module` pattern is shared.
- **`extensions/debug.py`** — product-framed "in-response counterpart":
  `SchemaExtension` → `extensions["debug"]` with SQL + exception rows; hard
  strawberry dependency; no toolbar soft-dep, no HTTP middleware, no GraphiQL
  bridge. Different seam, key, and change axis.
- **Bridge template** —
  `templates/django_strawberry_framework/debug_toolbar.html` — client-side
  scrubbing / panel DOM updates; owned as the HTML asset this middleware
  appends (third documented robustness divergence lives there, not in Python).
- **Upstream borrow** —
  `strawberry_django/middlewares/debug_toolbar.py` (~101 lines): same
  `_get_payload` / `_postprocess` skeleton; this package adds the soft-dep
  gates, the `isinstance(view, type)` guard, and `_get_payload`'s decode/parse
  / non-object bails. Content-Length refresh and callable title/subtitle lines
  are upstream-verbatim local repetition kept for re-diffability.
- **Tests** — live
  `examples/fakeshop/test_query/test_debug_toolbar_api.py` (GraphiQL HTML,
  named JSON inject, introspection skip, panel `requestId` round-trip,
  non-Strawberry HTML negatives under fakeshop's shipped wiring) and package
  `tests/middleware/test_debug_toolbar.py` (absence / apps gate / streaming /
  Content-Length branches / non-class `view_class` / template-port invariants)
  via `tests/_soft_dependency.py`.
- **Baseline** —
  `git diff e57baab6aba3c3eb7374f90fc7c181b99ef9eb4a -- django_strawberry_framework/middleware/debug_toolbar.py`
  is empty; working tree matches the item baseline for the target.

## Verification

Searches / reads (concepts and names):

- Full read of the target, `extensions/debug.py`, `utils/imports.py`,
  `middleware/__init__.py`, both toolbar test trees, the bridge template, and
  upstream `strawberry_django/middlewares/debug_toolbar.py`.
- Package-wide: `require_debug_toolbar` / `require_optional_module` /
  `DebugToolbarMiddleware` / `_is_graphiql` / `debugToolbar` / `requestId` /
  `IntrospectionQuery` / `Content-Length` / `_HTML_TYPES` / `TemplatesPanel` /
  `nav_subtitle` / `_TEMPLATE_MARKER` / install-hint floor
  `django-debug-toolbar>=7.0.0`.
- Soft-dep siblings and shared absence helper: `require_drf`,
  `require_channels`, `tests/_soft_dependency.py`.
- Cursor-tracking cousins (`testing/_wrap.py`, `_django_patches.py`) that
  cite toolbar's `wrap_cursor` as inspiration — SQL-tracking seams, not
  middleware injection.

Rejected / deferred candidates (tried to disprove shared ownership):

1. **Consolidate with `extensions/debug.py` as one "debug tooling" module.**
   Re-traced fresh (not inherited from the extensions file/folder artifacts).
   Middleware: soft-dep HTTP subclass, top-level `debugToolbar` panel metadata +
   GraphiQL bridge, import-time install/apps gates. Extension: hard-dep
   `SchemaExtension`, `extensions["debug"]` SQL + exception rows, per-operation
   cursor coordinator. Module docstring's "counterpart" language is product
   framing only. Merging would couple unrelated dependency boundaries and wire
   contracts behind mode flags. **Rejected.** Folder/project passes may still
   cite posture cross-links; this file does not own a merge.

2. **Extract a shared `_refresh_content_length(response)` (or package-wide
   helper) for the two identical header-present blocks in `_postprocess`.**
   Same local rule, same method, also verbatim in upstream. Extracting would
   save two lines and diverge the borrow skeleton from the upstream re-diff
   surface without clarifying ownership — `_postprocess` already owns both
   mutation paths. DRY.md's "do not optimize for fewer lines" / avoid
   convenience helpers that obscure the borrow applies. **Rejected.**

3. **Further collapse `require_debug_toolbar` / `require_drf` /
   `require_channels` into a shared factory beyond `require_optional_module`.**
   The raising primitive is already one owner; each feature keeps its own hint
   string and opt-in posture (leaf-import vs package-import vs `__getattr__`).
   A meta-factory would hide those posture differences. The apps gate is unique
   to this leaf. **Rejected.**

4. **Share `_TEMPLATE_MARKER` / `_HINT_SUBSTRING` across live + package tests
   (or import the production hint).** Intentional three-places-that-must-agree
   / drift-catch literals (pyproject pin, production hint, re-typed test
   substring) and independent test-tree markers. Consolidating would defeat
   the drift detectors. **Rejected** (AGENTS intentional test repetition).

5. **Unify callable title/subtitle resolution with
   `optimizer/extension.py` / `connection.py` callable-or-value sites.**
   Same Python idiom, different domains (toolbar panel properties vs selection
   / lazy connection values) and change axes. **Rejected.**

6. **Treat `testing/_wrap.py` / `_django_patches.py` cursor wrapping as
   middleware duplication.** Those seams instrument Django cursors for the
   test client / patch layer; this leaf never opens cursors or reads
   `queries_log`. Shared only as documentary citation of upstream toolbar
   SQL tracking. **Rejected.**

7. **Move install/apps gates or re-export onto `middleware/__init__.py`.**
   Disproved under the sibling `__init__` item and re-confirmed: parent must
   stay import-clean; Django resolves the class via leaf `import_string`.
   **Rejected.**

No scratch experiment under `docs/dry/temp-tests/` — contracts are pinned by
the live HTTP suite plus the package absence/branch units, and every candidate
failed on ownership / change-axis comparison without ambiguous runtime
behavior.

## Opportunities

None — the leaf already sits at the true owners for its soft-dep gates (via
`require_optional_module` + local hint/apps strings), view tagging, JSON panel
payload, and GraphiQL HTML append. Apparent siblings (`extensions/debug.py`,
other soft-dep wrappers, Content-Length twin lines, test drift literals) were
disproved as shared responsibilities that should change together.

## Judgment

Zero-edit. `middleware/debug_toolbar.py` is a deliberate soft-dep borrow of
strawberry-django's GraphQL toolbar bridge with three documented robustness
divergences and a unique `INSTALLED_APPS` gate; system-wide search found no
second production owner of its injection contract. Ready for Worker 2.

## Independent verification (Worker 2)

Scoped diff vs `ITEM_BASELINE` `e57baab6aba3c3eb7374f90fc7c181b99ef9eb4a`:

```shell
git diff e57baab6aba3c3eb7374f90fc7c181b99ef9eb4a -- django_strawberry_framework/middleware/debug_toolbar.py
```

empty (working tree matches baseline for the target).

Re-traced ownership independently:

- Soft-dep install gate → `require_debug_toolbar` →
  `utils/imports.py::require_optional_module` (shared raising primitive only).
- Unique apps gate → `apps.is_installed("debug_toolbar")` before
  `debug_toolbar.middleware` import (no sibling soft-dep has this).
- View tagging / HTML append / JSON `debugToolbar` inject / `_get_payload`
  panel shape — sole production owners in this leaf; template asset is the
  HTML counterpart, not a second Python policy site.
- `middleware/__init__.py` stays import-clean (no re-export); leaf
  `import_string` remains the opt-in.

Challenged rejected candidates:

1. **Merge with `extensions/debug.py`.** Re-read both modules and wire keys.
   Middleware: soft-dep HTTP subclass, top-level `debugToolbar` panel metadata
   + GraphiQL bridge. Extension: hard strawberry `SchemaExtension`,
   `extensions["debug"]` with `sql` / `exceptions` rows, cursor coordinator.
   Docstring "counterpart" is product framing only — different seam, key,
   dependency boundary, and change axis. Merge would need mode flags.
   **Rejection stands.**

2. **Extract `_refresh_content_length`.** Package-wide search: the twin
   `if "Content-Length" in response` blocks exist only in this `_postprocess`
   (nowhere else under `django_strawberry_framework/`). Upstream
   `strawberry_django/middlewares/debug_toolbar.py` carries the same two
   lines verbatim. A helper saves two lines, diverges the borrow skeleton,
   and does not clarify ownership — `_postprocess` already owns both mutation
   paths. **Rejection stands.**

3. Soft-dep meta-factory / test-marker share / callable-or-value unify with
   optimizer-connection / cursor-wrap cousins / move gates onto
   `middleware/__init__.py` — re-confirmed as intentional posture or domain
   differences; none share a contract that should change together.

Missed consolidation search (names + concepts): `debugToolbar`,
`_is_graphiql`, `IntrospectionQuery`, `Content-Length`, `_HTML_TYPES`,
`TemplatesPanel`, `require_debug_toolbar`, `require_optional_module`,
response `write`/`content=` mutation, `render_to_string` of the bridge
template. No second production owner of the injection contract; no stale
bypass. Zero-edit judgment holds.

Disposition: **verified.** Plan item checked.
