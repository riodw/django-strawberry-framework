# Critical Spec Review: Spec 042 Plus Relay Setting Concern

## Scope note

The active TODO anchors just added are for [`spec-042-debug_toolbar-0_0_14.md`][spec-042]:
the `django-debug-toolbar` middleware, template, and middleware tests.

The prompt's setting-placement question, however, names
[`types/relay.py`][types-relay] rather than the debug-toolbar spec. That anchor
belongs to the shipped Relay GlobalID strategy contract from
[`spec-031-globalid_encoding-0_0_9.md`][spec-031] and the follow-up
[`spec-032-full_relay-0_0_9.md`][spec-032]. I reviewed both surfaces:

- **Spec 042** for architectural soundness before production code.
- **Relay setting placement** for the `RELAY_GLOBALID_STRATEGY` read /
  validation concern.

## Bottom line

Spec 042 is directionally sound and small enough to implement cleanly, but I
would not start production code until the P1 test-contract issue below is fixed
in the spec and TODO anchors. The relay setting placement in
[`types/relay.py::_resolve_globalid_strategy`][types-relay] is sound as long as
the strategy stays finalize-frozen; moving domain validation wholesale into
[`conf.py`][conf] would make the architecture worse, not better.

## P1 - Must Fix Before Implementation

### P1.1 - The soft-dependency absence test mechanism contradicts the guard

Spec 042 correctly requires `require_debug_toolbar()` to be a thin wrapper over
[`utils/imports.py::require_optional_module`][utils-imports]. That primitive uses
`importlib.import_module(...)`.

The same spec says the toolbar-absent fixture should copy the Channels
`builtins.__import__` blocker pattern from [`tests/test_routers.py`][test-routers].
That is not reliable for this guard shape. I verified locally that a
`builtins.__import__` blocker for `channels` does not block
`importlib.import_module("channels")`; the import succeeds and the blocker only
sees internal imports such as `_io`. The DRF guard's own docstring already
records the same limitation for `require_optional_module`.

If Slice 1 adds `django-debug-toolbar>=7.0.0` to the dev environment, an
absence test using only the `builtins.__import__` blocker can import the real
installed top-level `debug_toolbar` package instead of exercising the
hint-carrying absence path. That would either fail for the wrong reason or,
worse, let a false absence test pass through a later submodule failure.

**Spec correction:**

- Replace the "copy the Channels import-block pattern" language with an
  importlib-compatible absence helper.
- Preferred test shape: strict `sys.modules` eviction plus a sentinel:
  `sys.modules["debug_toolbar"] = None` inside the absence context, with all
  `debug_toolbar.*` and `django_strawberry_framework.middleware.debug_toolbar`
  modules evicted before setup and after teardown.
- Alternative: monkeypatch `importlib.import_module` narrowly for the exact
  top-level `"debug_toolbar"` call made by `require_optional_module`.
- Keep the two-sided parent-attribute restore, but make the import-blocking
  mechanism match the actual guard.
- Do not factor a shared absence helper until it supports both direct-import
  guards (`require_drf()`) and importlib guards (`require_channels()` /
  `require_debug_toolbar()`).

The TODO pseudo-code in [`tests/middleware/test_debug_toolbar.py`][test-middleware-debug]
should be updated to say "sentinel/importlib-compatible blocker", not only
"import blocker".

### P1.2 - Present-but-broken install is documented but not actually in the test plan

The Error shapes section says a present top-level `debug_toolbar` package with a
broken submodule import should propagate the raw `ImportError`, and says the
test plan pins that degraded path. The numbered tests do not include that case:
tests 9-12 cover absence and `require_debug_toolbar()` success/absence only.

This matters because the implementation boundary is intentionally split:

1. `require_debug_toolbar()` wraps only the top-level package import.
2. `debug_toolbar.middleware` / `debug_toolbar.toolbar` imports happen after
   the guard and should fail raw if the install is broken.

Without a degraded-install test, an implementation can accidentally wrap too
broadly and misreport a broken toolbar as "not installed".

**Spec correction:**

- Add a numbered test after the absence tests:
  "top-level `debug_toolbar` import succeeds, but importing
  `debug_toolbar.middleware` fails; importing the package leaf raises the raw
  `ImportError` without `_DEBUG_TOOLBAR_INSTALL_HINT`."
- The cleanest setup is a narrow importlib monkeypatch or `sys.modules`
  sentinel for `debug_toolbar.middleware` while leaving a real or fake
  top-level `debug_toolbar` module importable.
- Assert `__cause__` remains the original failing import and the message names
  the broken submodule, not only the floor.

## P2 - Spec Corrections Strongly Recommended

### P2.1 - `process_view` should not assume `view_class` is always a class

The upstream-shaped pseudo-code is:

```python
view = getattr(view_func, "view_class", None)
request._is_graphiql = bool(view and issubclass(view, BaseView))
```

That is fine for normal Django class-based views, but it can crash an unrelated
function view if a decorator or helper attaches a non-class `view_class`
attribute. This is not common, but the middleware is installed globally and
runs for non-GraphQL traffic too.

**Spec correction:**

```python
view = getattr(view_func, "view_class", None)
request._is_graphiql = isinstance(view, type) and issubclass(view, BaseView)
```

This is a harmless robustness improvement over upstream: every legitimate
Strawberry Django view still matches, and unrelated views cannot crash the
toolbar pipeline. Add a negative unit for `view_func.view_class = "not-a-class"`.

### P2.2 - JSON media type should be decided explicitly

The spec only injects into `Content-Type: application/json`. Modern GraphQL over
HTTP also uses `application/graphql-response+json`. If Strawberry starts
returning that media type, the middleware silently stops injecting the toolbar
payload even though the response is still a GraphQL JSON response.

**Spec correction options:**

- Preferred: define `_JSON_TYPES = {"application/json",
  "application/graphql-response+json"}` and test both.
- If strict upstream parity is more important, explicitly document that
  `application/graphql-response+json` is not supported by this card and should
  be a follow-up compatibility card.

Leaving it implicit creates a future compatibility regression that will be hard
to diagnose.

### P2.3 - `_get_payload` should specify what happens for non-object JSON

The spec says every Strawberry-view JSON response gets the `debugToolbar`
payload, but the upstream helper assumes `json.loads(response.content)` returns
a mapping. GraphQL operation responses are normally objects, but edge cases can
exist: malformed test views, future batch response shapes, or a Strawberry
change that emits a JSON list.

**Spec correction:**

- Either narrow the contract to "object-shaped GraphQL JSON responses" and
  leave upstream's failure behavior accepted, or
- Preferably guard:

```python
payload = json.loads(content, object_pairs_hook=collections.OrderedDict)
if not isinstance(payload, dict):
    return None
```

The guard keeps debug tooling from turning an unusual JSON response into a 500.
Add a targeted unit if the guard is accepted.

### P2.4 - CSP / inline-script behavior needs one documentation sentence

The template asset is an inline `<script>` appended to the GraphiQL HTML page.
That matches upstream and the old `django-graphiql-debug-toolbar` lineage, but a
strict Content Security Policy can block it. In that case the server-side
toolbar history may still exist, while the GraphiQL page will not consume and
strip `debugToolbar` from JSON responses.

**Spec correction:**

- Add a GLOSSARY / user-facing note: this is a dev-only toolbar bridge and can
  be blocked by strict CSP; consumers with CSP must allow the toolbar script path
  or accept that GraphiQL DOM updates will not run.

### P2.5 - The dependency-floor text is currently accurate, but should avoid "current release" drift

I checked PyPI during this review. The current stable
[`django-debug-toolbar` metadata][pypi-debug-toolbar-7] reports 7.0.0 and
Django 6.0 support; the [`6.0.0` metadata][pypi-debug-toolbar-6] stops at
Django 5.2. So the spec's `>=7.0.0` floor is justified today.

The brittle part is wording like "current release". The implementation contract
only needs the verified floor, not a future-sensitive claim.

**Spec correction:**

- Rephrase to: "`7.0.0` is the verified floor for this card because it is the
  first checked release whose metadata covers the package's advertised Django
  6.0 range."
- Keep the three-places-that-must-agree rule: dev dependency, install hint, and
  re-typed test literal.

## P3 - Lower-Risk Cleanups

### P3.1 - Factor the toolbar-present fixture locally before making it generic

The spec's toolbar-present fixture has many moving parts: schema reload,
`DEBUG=True`, app registry mutation, URLconf eviction, toolbar callback cache
clearing, and `DebugToolbar` class-cache save/clear/restore. That is too
specific to promote immediately to a package-wide helper.

Keep it local to `tests/middleware/test_debug_toolbar.py` for Slice 1, but name
the inner pieces clearly:

- `_evict_debug_toolbar_urlconf()`
- `_debug_toolbar_cache_state()`
- `_middleware_with_debug_toolbar(real_middleware)`

Only factor later if the response-extensions card actually needs the same
machinery.

### P3.2 - Keep the template-port guard mechanical, not too broad

The template test should assert the five load-bearing invariants named in the
spec and no more. Do not pin the full asset byte-for-byte unless the project
intends to manually re-sync every upstream whitespace-only change.

The right balance is:

- exact substrings for `JSON.parse`, `Response.prototype.json`, deletion of the
  payload, `data-request-id`, and panel title/subtitle updates;
- no full golden-file assertion.

## Relay Setting Placement Review

### Answer to Q3

The setting read / validation placement in [`types/relay.py`][types-relay] is
architecturally sound. It should not be moved wholesale into [`conf.py`][conf].

`conf.py` is intentionally a thin settings reader. It validates only the shape
of `DJANGO_STRAWBERRY_FRAMEWORK` itself: missing/`None` becomes an empty mapping,
non-mapping values raise `ConfigurationError`, and missing keys raise
`AttributeError`. Domain validation belongs where the domain vocabulary lives.
For `RELAY_GLOBALID_STRATEGY`, that vocabulary is in the Relay/type layer:
`model`, `type`, `type+model`, callable arity/sync validation, Relay-shaped
gating, and the recorded effective strategy.

There is no query-time settings overhead under the shipped design:

- `_resolve_globalid_strategy(definition)` runs during finalization.
- The result is stamped on `DjangoTypeDefinition.effective_globalid_strategy`.
- `decode_global_id`, filters, and testing helpers read the stamped strategy,
  not the Django setting.
- An `override_settings(...)` after finalization is intentionally inert until
  the registry/schema is cleared and rebuilt.

That means no repeated query-execution validation, no per-request setting read,
and no new thread-safety risk beyond the existing `conf.settings` singleton
rules. The only redundant work is build-time validation once per finalized type
that falls through to the setting. That is acceptable and keeps the validation
single-sourced through `types/base.py::_validate_globalid_strategy`.

### Relay spec/doc update I would keep

The Relay specs already mostly say this, especially [`spec-032`][spec-032].
If touching the docs again, make sure the same sentence appears in the
`RELAY_GLOBALID_STRATEGY` entry and any strategy-varying test docs:

> `RELAY_GLOBALID_STRATEGY` is schema-build-time configuration. Changing it
> after types finalize does not affect emitted or decoded IDs until the registry
> and schema are rebuilt.

Do not move strategy validation into `conf.py`. If the project wants a named
getter for consistency, it should be a thin default reader only, for example
`relay_globalid_strategy_setting() -> Any | None`, with validation still in the
Relay/type layer.

## Test And Documentation Gaps

### Debug-toolbar tests likely fit the current suite without a rewrite

The spec's test strategy is heavy but compatible with the existing suite:

- root `tests/` can use fakeshop settings because `pytest.ini` already puts
  `examples/fakeshop` on the path;
- the schema reload discipline already exists in `schema_reload`;
- per-test `INSTALLED_APPS` overrides are standard Django test machinery;
- the URLconf dotted-path / `sys.modules` eviction rule is enough to make
  `debug_toolbar_urls()` compute under `DEBUG=True`.

The suite does not need a major rewrite. The main danger is test fixture
fragility, especially import-state leakage. That is why P1.1 matters.

### Add one explicit doc invariant for URLconf failure

The spec correctly corrected the missing-`debug_toolbar_urls()` failure mode to
`NoReverseMatch` on the first toolbar-processed request. Keep this exact
wording in the GLOSSARY update. "Panel click 404" is wrong and should not
survive in any docs.

### Add one explicit doc invariant for view-scoped JSON mutation

The user-facing docs must say plainly that a non-IDE API client can see the
extra top-level `debugToolbar` key while the toolbar is enabled. This is
development-only behavior, but it is observable and can surprise GraphQL clients
that validate response shape strictly.

## Proposed Spec Patch Checklist

- [ ] Change the absence-test fixture from `builtins.__import__` blocker to a
      sentinel/importlib-compatible absence mechanism.
- [ ] Add a present-but-broken-install degraded test.
- [ ] Guard `issubclass` with `isinstance(view, type)`.
- [ ] Decide and document `application/graphql-response+json`.
- [ ] Decide and document/guard non-object JSON responses.
- [ ] Add CSP inline-script caveat to user-facing docs.
- [ ] Reword dependency-floor prose to avoid future "current release" drift.
- [ ] Keep `RELAY_GLOBALID_STRATEGY` validation in the Relay/type layer; only
      add a thin `conf.py` getter if readability needs it.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: ../KANBAN.md
[readme]: ../README.md
[start]: ../START.md

<!-- docs/ -->
[spec-042]: spec-042-debug_toolbar-0_0_14.md

<!-- docs/SPECS/ -->
[spec-031]: SPECS/spec-031-globalid_encoding-0_0_9.md
[spec-032]: SPECS/spec-032-full_relay-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../django_strawberry_framework/conf.py
[middleware-debug-toolbar]: ../django_strawberry_framework/middleware/debug_toolbar.py
[template-debug-toolbar]: ../django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html
[types-relay]: ../django_strawberry_framework/types/relay.py
[utils-imports]: ../django_strawberry_framework/utils/imports.py

<!-- tests/ -->
[test-middleware-debug]: ../tests/middleware/test_debug_toolbar.py
[test-routers]: ../tests/test_routers.py
[test-soft-dependency]: ../tests/rest_framework/test_soft_dependency.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[pypi-debug-toolbar-7]: https://pypi.org/pypi/django-debug-toolbar/json
[pypi-debug-toolbar-6]: https://pypi.org/pypi/django-debug-toolbar/6.0.0/json
