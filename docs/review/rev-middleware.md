# Review: `django_strawberry_framework/middleware/`

Status: verified

Cycle baseline: `HEAD` `9ebb4bb0594ccb88c3cf6fbac55bf5883bac7d88`; `git diff HEAD -- django_strawberry_framework/middleware/` is empty.

## Understanding

The folder has a deliberately narrow public surface:

- `middleware/__init__.py` is a docstring-only import-clean marker. It imports no optional dependency and re-exports no middleware class.
- `middleware/debug_toolbar.py` is the leaf opt-in for the soft toolbar dependency and owns toolbar tagging/response rewriting.
- `middleware/request_body.py` is the lifecycle adapter for the package views' body boundary and owns no independent cap, charset, or multipart policy.

The body lifecycle crosses two boundaries without circular imports. `views.py::_RequestBodyBoundaryMixin` owns the request policy and callback marks; `_boundary_ordering.py` owns the shared marker, enforced/prepared state names, boundary method name, ContextVar, and CSRF exemption object; `middleware/request_body.py` consumes that protocol and supplies chain ordering. The toolbar leaf and request-body middleware are independent, and the package marker remains safe for whole-package walkers and toolbar-less consumers.

Test placement is coherent: package tests cover optional-dependency and synthetic lifecycle shapes unreachable from a real request; `examples/fakeshop/test_query/` covers reachable GraphQL HTTP, CSRF, multipart, upload, and toolbar behavior through Django's real client. The folder has no competing injector, tagger, public facade, or lifecycle owner.

## Verification

- Re-read all three folder modules as an integrated component and traced boundaries into `views.py`, `_boundary_ordering.py`, `_request_body.py`, fakeshop settings/URLconf, the extensions debug surface, and soft-dependency siblings.
- `git diff HEAD -- django_strawberry_framework/middleware/` — empty.
- `uv run pytest tests/base/test_init.py tests/base/test_conf.py tests/middleware/test_debug_toolbar.py tests/test_views.py --no-cov -q -n0 -k 'middleware or toolbar or body or csrf or boundary or ordering or setup or import or public or version or setting'` — 125 passed.
- `uv run pytest examples/fakeshop/test_query/test_debug_toolbar_api.py examples/fakeshop/test_query/test_transport_api.py --no-cov -q -n0` — 104 passed (27 toolbar tests were run separately with the same result; the transport file passed 77).
- Searched production ownership for `_is_graphiql`, `debugToolbar`, `_BOUNDARY_MARKER`, `_BOUNDARY_ENFORCED`, `_BOUNDARY_METHOD`, and `GraphQLRequestBodyBoundaryMiddleware`; each has one intentional owner/protocol path.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The folder is cleanly integrated: the optional toolbar leaf does not contaminate package imports, the request-body middleware does not duplicate view policy, and `_boundary_ordering.py` provides the only shared lifecycle vocabulary across the view/middleware boundary. Public surfaces, import behavior, sync/async lifecycle ownership, and package/live test placement require no change.

## Implementation (Worker 1)

None — zero-edit folder cycle.

No source or permanent-test files changed; only these review artifacts were added. The empty scoped diff is the zero-edit proof. No cross-file edit was needed, no changelog entry is warranted, and `CHANGELOG.md` was untouched.

## Independent verification (Worker 2)

The three modules were re-read as one component together with the view/raw-body boundary,
`_boundary_ordering.py`, fakeshop settings/URLconf, the debug-extension sibling, and the
specification/docs. There are no Worker 1 source or permanent-test changes in the current tree:
`git --no-pager status --short` lists only the three review artifacts and
`git --no-pager diff --name-only` is empty.

Folder-level validation passed:

- `uv run pytest tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py --no-cov -q -n0` — 27 passed.
- `uv run pytest tests/test_views.py --no-cov -q -n0 -k 'body or multipart or charset or csrf or ordering or boundary or setup or probe or stream or request_encoding or utf8 or malformed'` — 151 passed, 71 deselected.
- `uv run pytest examples/fakeshop/test_query/test_transport_api.py --no-cov -q -n0` — 77 passed.
- Independent Node execution passed bridge scrubbing/reviver/missing-container checks and reproduced the nested-DOM `TypeError` recorded in the debug-toolbar artifact.
- Independent Python execution passed duplicate boundary idempotence, subclass ordering,
  prepared-view handoff, and async `ContextVar` reset.

The request-body middleware and folder ownership boundaries are coherent, but the integrated
folder cannot be accepted while the bridge's advertised best-effort DOM contract is violated:
`debug_toolbar.html` still throws when a present panel lacks nested title/scroll/content/nav
children. This is a Worker 1 production-template finding, not a request-body or Python
middleware finding.

**Prior verdict:** revision-needed for the folder integration, pending the debug-toolbar template guard
and runtime regression. No production/source/test changes were made by Worker 2.

## Iterations

### Revision pass (Worker 1)

- **Integrated finding accepted:** The folder-level revision was solely the debug-toolbar bridge's nested DOM failure; request-body lifecycle ownership, `_boundary_ordering.py` protocol ownership, public imports, and fakeshop test placement remained sound.
- **Root-cause fix:** The bridge template now guards every nested title/heading/scroll/loader/panel-content/nav lookup before dereferencing it, while preserving unconditional `debugToolbar` scrubbing and reviver forwarding.
- **Permanent proof:** `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence` now pins each nested guard. The live fakeshop debug-toolbar tests remain unchanged and continue to exercise the real served bridge.
- **Independent runtime proof:** Node `v24.10.0` exercised missing title, heading, scroll, loader, panel-content, and nav-small nodes; all six cleaned responses returned without exceptions.
- **Validation:** Complete package/live debug-toolbar selection — 27 passed; template mechanical selection — 1 passed. `uv run ruff format .` and `uv run ruff check --fix .` both passed.
- **Scope:** Only `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` and `tests/middleware/test_debug_toolbar.py` changed in this revision. Request-body files and unrelated concurrent work were preserved. Folder status is restored to `fix-implemented` pending Worker 2's independent re-verification.

## Independent verification (Worker 2)

Re-read the revised bridge and test diff together with `middleware/__init__.py`,
`middleware/debug_toolbar.py`, `middleware/request_body.py`, `_boundary_ordering.py`, the view/raw
body owners, fakeshop settings/URLconf, and the relevant specs/docs. The revision scope contains
only Worker 1's bridge/template test changes plus the plan/artifacts; request-body and unrelated
files remain untouched.

The exact malformed-DOM matrix from the prior folder finding passed independently in Node `v24.10.0`:
missing `panelTitle`, `heading`, `scroll`, `loader`, `panelContent`, and `navSmall` each returned
the scrubbed response without an exception. Focused package/live validation also passed:

- `uv run pytest tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py --no-cov -q -n0` — 27 passed.
- `uv run pytest tests/test_views.py --no-cov -q -n0 -k 'body or multipart or charset or csrf or ordering or boundary or setup or probe or stream or request_encoding or utf8 or malformed'` — 151 passed, 71 deselected.
- `uv run pytest examples/fakeshop/test_query/test_transport_api.py --no-cov -q -n0` — 77 passed.

The request-body lifecycle remains independently verified: duplicate boundary entries are
idempotent, subclass ordering is detected, prepared-view identity is preserved, and async
`ContextVar` state resets after downstream failure. The bridge now satisfies the folder's
best-effort DOM/scrubbing contract as well.

**Verdict:** verified. The folder integration is sound after Worker 1's template revision; no
remaining middleware or folder defect was reproduced.

