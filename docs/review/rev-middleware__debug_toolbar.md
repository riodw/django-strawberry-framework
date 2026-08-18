# Review: `django_strawberry_framework/middleware/debug_toolbar.py`

Status: verified

Cycle baseline: `HEAD` `9ebb4bb0594ccb88c3cf6fbac55bf5883bac7d88`; the target was clean at dispatch and `git diff HEAD -- django_strawberry_framework/middleware/debug_toolbar.py` is empty.

## Understanding

The leaf owns the optional `django-debug-toolbar` opt-in and the two GraphQL-specific hooks. `require_debug_toolbar()` delegates to `utils/imports.py::require_optional_module` before importing toolbar symbols, so root and parent-package imports remain toolbar-free while Django's `MIDDLEWARE` dotted path is the opt-in. The following `apps.is_installed("debug_toolbar")` gate converts the otherwise cryptic `HistoryEntry` model-registration failure into `ImproperlyConfigured`.

`DebugToolbarMiddleware.process_view` tags only callbacks whose `view_class` is a `strawberry.django.views.BaseView` subclass. `_postprocess` chains the stock toolbar first, then preserves streaming and encoded responses, appends the bridge template only to tagged successful HTML responses, and injects the `debugToolbar` payload only into tagged `application/json` responses. `_get_payload` preserves the response object shape, request id, panel titles/subtitles, callable panel metadata, and `TemplatesPanel` exclusion; malformed, undecodable, or non-object JSON is left untouched. Introspection operations are skipped by the request envelope's `operationName`.

The template is the client-side half of the contract: it scrubs the server-only key, updates the toolbar DOM when present, forwards `JSON.parse` arguments, and treats missing DOM nodes as best-effort. `extensions/debug.py::DjangoDebugExtension` is a separate in-response diagnostic surface, not a second owner.

## Verification

- Read the complete leaf, bridge template, `utils/imports.py::require_optional_module`, soft-dependency tests, fakeshop settings/URLconf, the debug-toolbar specification, and the live GraphQL tests.
- `uv run pytest tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py --no-cov -q -n0` — 27 passed.
- Live coverage exercised the real fakeshop GraphiQL HTML response, named JSON SQL operation, introspection skip, JSON GET, panel `requestId` round-trip, ordinary HTML views, and production-inert `DEBUG=False` behavior.
- Package coverage exercised missing toolbar, broken submodule, missing app registration, parent import cleanliness, streaming/encoded responses, malformed response bodies, non-object JSON, non-class `view_class`, content-length refreshes, and template-port invariants.
- Installed `django-debug-toolbar` source inspection confirmed that `super()._postprocess` must run first and renders/stores history before the package's response-specific branches.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The optional import and app-registration gates fail at the intended boundaries, the stock toolbar lifecycle remains the owner of panels/history/headers, and the package response rewrite is scoped to tagged GraphQL view responses without corrupting encoded or unusual bodies. Existing adversarial and live coverage proves the contract; no new root-cause edit is required.

## Implementation (Worker 1)

None — zero-edit cycle.

The scoped production diff is empty for `django_strawberry_framework/middleware/debug_toolbar.py`; no permanent test change is needed because the existing package and live suites cover every reachable branch and the documented optional-dependency matrix. No changelog entry is warranted. No formatter/linter run was required for a source-zero-edit cycle; `CHANGELOG.md` was untouched.

## Independent verification (Worker 2)

The package and live behavior was re-read from the leaf through the stock toolbar, fakeshop's settings/URLconf, the bridge template, the optional-import helper, and the debug-toolbar and transport specifications. The current tree has no Worker 1 source or permanent-test edits: `git --no-pager status --short` lists only these three untracked review artifacts, and `git --no-pager diff --name-only` is empty.

Focused validation passed:

- `uv run pytest tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py --no-cov -q -n0` — 27 passed.
- A Node runtime probe loaded the bridge through `vm`, verified that a missing `#djDebug` handle still scrubs `debugToolbar`, that a `JSON.parse` reviver is forwarded, and that a panel whose content node is absent does not throw.

### Medium

#### Nested toolbar DOM lookups can still throw from the global JSON hooks

- **Observation:** The bridge claims that DOM updates are best-effort, but after finding a panel container it dereferences `.djDebugPanelTitle`, its `h3`, `.djdt-scroll`, and `.djDebugPanelContent` without checking them; the subtitle branch likewise dereferences a missing `small` element. The guards at `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html:35-56` cover only the panel/nav container, not these nested nodes.
- **Evidence:** An independent Node `vm` probe loaded the exact template, returned a fake `#djDebug` from `document.getElementById`, returned a fake `#SQLPanel` whose `querySelector` always returned `null`, then called the patched `JSON.parse` with a valid `debugToolbar` payload. It reproduced `TypeError: Cannot read properties of null (reading 'querySelector')` from the title update at `debug_toolbar.html:40-42`. The same shape is reachable for the scroll, loader/content, and nav-small lookups at `:44-56`.
- **Impact:** The server-only key is deleted first, but the global `JSON.parse` and `Response.prototype.json` hooks still reject the response when toolbar markup is partial, customized, or changes across a debug-toolbar release. GraphiQL's response path can therefore break instead of receiving the scrubbed data, contradicting the documented "payload scrubbing mandatory, DOM updates best-effort" contract.
- **Recommendation:** Worker 1 should guard every nested query before dereferencing it (or isolate each panel's DOM update in a narrow failure-safe helper), while preserving the unconditional `debugToolbar` deletion. Add a JavaScript-runtime regression covering missing title, heading, scroll, panel-content, and nav-small nodes; the production owner is the bridge template, not the Python middleware or the review tests.
- **Proof:** The Node reproduction above is a failing proof on the current tree; the existing Python substring test does not execute these DOM branches. The fix is complete only when the same malformed DOM returns the cleaned GraphQL object without throwing.

### High

None.

### Low

None.

### Other verified paths

The optional-dependency absence and broken-install gates, the `INSTALLED_APPS` gate, non-class callback recognition, streaming and encoded-response early exits, content-length refreshes, introspection skip, ordinary-view JSON isolation, panel metadata/callable handling, and the stock-toolbar-first ordering all passed the focused suite. The documented replacement-only contract for duplicate stock/package toolbar entries was left unchanged; duplicate-entry idempotence is owned by the request-body middleware item.

**Prior verdict:** revision-needed. The Python middleware behavior was sound, but the template defect was consumer-visible in the GraphiQL global hooks and returned to Worker 1.
## Iterations

### Revision pass (Worker 1)

- **Finding accepted:** Worker 2's Node reproduction showed that the bridge scrubbed `debugToolbar` but still threw when a present panel omitted a nested `.djDebugPanelTitle`, `h3`, `.djdt-scroll`, `.djdt-loader`, `.djDebugPanelContent`, or nav `small` node. This violated the documented rule that payload scrubbing is mandatory while DOM updates are best-effort.
- **Root-cause fix:** Updated `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` so every nested lookup is stored and checked before property access or mutation. Scrubbing remains before all DOM work, `JSON.parse` argument forwarding is unchanged, and existing panel/container guards remain intact.
- **Permanent proof:** Extended `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence` with mechanical assertions for the title, heading, scroll, loader, panel-content, and nav-subtitle guards. This is the package tier used for the JavaScript asset because the repository has no JavaScript test harness; the existing live suite still proves the real bridge asset is served on fakeshop GraphiQL responses.
- **Independent runtime proof:** Replayed the malformed-DOM matrix in Node `v24.10.0` against the exact template for each missing nested node. Every patched `JSON.parse` call returned the cleaned GraphQL object without throwing, and the `debugToolbar` key was absent.
- **Validation:** `uv run pytest tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py --no-cov -q -n0` — 27 passed; template-only selection — 1 passed. `uv run ruff format .` left 423 files unchanged; `uv run ruff check --fix .` passed.
- **Scope:** Changed only the bridge template and its package-tier mechanical test. `request_body.py`, `_boundary_ordering.py`, `views.py`, and unrelated dirty files were untouched. No changelog entry is warranted.

## Independent verification (Worker 2)

Re-read Worker 1's template/test diff and the complete bridge contract, then replayed the exact
failure shape from the prior finding rather than relying on the new substring assertions. At
dispatch for this revision, `git --no-pager status --short` showed only the expected revision
changes (`debug_toolbar.html`, `test_debug_toolbar.py`, the plan, and the three review artifacts);
no request-body or unrelated source files were modified.

Validation:

- `node` `vm` matrix against the exact template, with one nested node omitted per case:
  `panelTitle`, `heading`, `scroll`, `loader`, `panelContent`, and `navSmall` — all six returned
  the cleaned GraphQL object without throwing, and `debugToolbar` was absent.
- `uv run pytest tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py --no-cov -q -n0` — 27 passed.
- `uv run pytest tests/test_views.py --no-cov -q -n0 -k 'body or multipart or charset or csrf or ordering or boundary or setup or probe or stream or request_encoding or utf8 or malformed'` — 151 passed, 71 deselected.
- `uv run pytest examples/fakeshop/test_query/test_transport_api.py --no-cov -q -n0` — 77 passed.

The prior Node reproduction (`#djDebug` present, `#SQLPanel` present, nested `querySelector`
returning `null`) now returns cleanly. Every revised nested lookup is guarded before property
access, while scrubbing remains before all DOM work; reviver forwarding, missing-toolbar
scrubbing, encoded/streaming response isolation, introspection skipping, ordinary-traffic
isolation, optional dependency/app gates, and stock-toolbar ordering remain green.

**Verdict:** verified. The prior nested-DOM defect is fixed at its template owner, the permanent
mechanical guard covers each nested lookup, and no remaining debug-toolbar defect was reproduced.

