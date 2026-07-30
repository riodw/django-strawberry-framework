# Build: Slice 2 — S2: the cumulative request-body cap

Spec reference: `docs/spec-046-transport_security-0_0_15.md` — Slice 2 checklist lines 143-154;
Decision 7 (lines 850-911), Decision 8 (913-934), Decision 6 (797-848, the seam Slice 1 created),
Decision 13 Placement (1204-1214); User-facing API — the view block lines 501-516, the setting
517-526, Error shapes 563-594; Current state's Django-body bullet 278-290; Helper-reuse obligations
1302-1338; Edge cases 1340-1396; Test plan S2 rows 13-18 (lines 1430-1443); Definition of done
1608-1613.
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Utils inventory checked.** `docs/shadow/utils-inventory.md` refreshed this pass with the
  `worker-1.md` AST script (14 modules). Searched it for size / limit / byte / length / int /
  validation candidates: the only hits are window-pagination shapes
  (`utils/connections.py::window_range_plan`, `::derive_connection_window_bounds` — GraphQL
  pagination arithmetic, unrelated to a transport byte ceiling) and
  `utils/errors.py::validation_error_to_field_errors` (Django `ValidationError` → the GraphQL
  `FieldError` envelope, the wrong error channel for a transport rejection). **No existing utility
  fits, and no new `utils/` module is justified** — a request-body ceiling is a property of the
  HTTP view, so it belongs in `views.py` beside the classes that enforce it, exactly as Decision 6
  reason (a) puts it there. A repo-wide grep for a "must be a positive int" validator found none;
  the package has no such helper to reuse.

- **Static inspection run (BUILD.md obligation — both files this slice adds logic to).**
  - `uv run python scripts/review_inspect.py django_strawberry_framework/views.py --output-dir
    docs/shadow` → `docs/shadow/django_strawberry_framework__views.overview.md`. Quick scan: 2
    imports, 2 symbols, 0 hotspots, 0 Django/ORM markers, 0 calls of interest, **1 TODO** (the
    `TODO(spec-046 Slice 2)` anchor this slice must remove), 0 repeated literals.
  - `uv run python scripts/review_inspect.py django_strawberry_framework/conf.py --output-dir
    docs/shadow` → `docs/shadow/django_strawberry_framework__conf.overview.md`. Quick scan: 5
    imports, 13 symbols, 2 hotspots (`Settings.user_settings`, `upstream_patches_enabled` — both
    untouched by this slice), 0 TODOs, 0 repeated literals. The five shipped one-line accessors
    (`nested_connection_strategy_setting`, `single_parent_fast_path_setting`,
    `testing_endpoint_setting`, `hide_flat_filters_setting`, `relay_globalid_strategy_setting`) are
    the shape the new reader copies.
  - Shadow line numbers are **not** canonical; every citation below is symbol-qualified per
    `AGENTS.md` #"Source references in docs and code comments".

- **Existing patterns reused.**
  - **The precedence resolver shape** is `optimizer/nested_fetch.py::resolve_strategy`
    (`nested_fetch.py:330-359`) verbatim in structure: one module-level pure function that takes
    the constructor value, falls back to the `conf.py` reader when it is `None`, validates, and
    raises `ConfigurationError` naming the received type. That is the shipped
    `NESTED_CONNECTION_STRATEGY` precedence the spec's Slice-2 bullet names, and it also fixes
    *where validation lives*: with the resolver, never in `conf.py` (which "stays a thin reader
    that does not validate domain values" — `conf.py::relay_globalid_strategy_setting` docstring).
  - **The settings reader** copies `conf.py::nested_connection_strategy_setting` exactly: a
    module-level `*_KEY` constant with a `#` comment block above it, plus a one-line
    `getattr(settings, KEY, <default>)` accessor with a docstring naming the default and the
    consumer of the value. Helper-reuse obligation #"The settings read goes through `conf.py`'s
    existing `Settings` reader" — no local `getattr(django.conf.settings, ...)`.
  - **The typed failure** is `exceptions.py::ConfigurationError`, the package's single typed
    configuration error (Helper-reuse #"The construction-time failure is `ConfigurationError`").
    No new exception class.
  - **The rejection response is upstream's own translation.**
    `strawberry.django.views.GraphQLView.dispatch` / `AsyncGraphQLView.dispatch` already wrap
    `self.run(...)` in `except HTTPException` → `HttpResponse(content=e.reason,
    status=e.status_code, content_type="text/plain")`. Raising
    `cross_web.HTTPException(413, reason)` inside a `run` override therefore produces the spec's
    exact `413` `text/plain` shape with **zero** new response machinery — and byte-identically to
    the `400`s `_strawberry_patches.py::_patched_parse_json` already raises through the same seam.
  - **`cross_web.HTTPException`** is imported plainly (no `try`/`except ImportError` guard):
    `strawberry.django.views` itself imports it, so it is part of the existing hard
    `strawberry-graphql` dependency chain and inside the import set `views.py`'s module docstring
    already declares (`stdlib`, `asgiref`, `cross_web`, `django`, `strawberry.http`). The guarded
    import in `_strawberry_patches.py` exists only so that module can *report* an unsupported
    upstream shape; that reason does not apply here.
  - **Live tier:** `examples/fakeshop/test_query/test_transport_api.py`'s existing module-local
    seams — `_post(client, query, path=..., variables=..., **extra)`,
    `_assert_no_graphql_envelope(response)`, `_TYPENAME` / `_ITEMS` / `_CREATE_CATEGORY`, the
    module-level Probe `urlpatterns` + `override_settings(ROOT_URLCONF=__name__)` pattern, and the
    request-time view construction in `_ide_off_view`. Plus `apps.products.services::seed_data` /
    `::create_users` (AGENTS.md rule 7) and the autouse reload fixtures in
    `examples/fakeshop/test_query/conftest.py`. **No new live harness, no new fixture module, no
    second reload discipline** (Helper-reuse #"uses the existing Probe URLconf pattern rather than
    a new harness").
  - **Package tier:** `tests/test_views.py`'s existing `SCHEMA`, `_VIEW_CLASSES` parametrization
    tuple, and `_ABSENCE_PREFIXES`. `tests/base/test_conf.py`'s accessor-default enumeration.

- **New helpers justified.** Three, all in `django_strawberry_framework/views.py`, all private:
  1. `_RequestBodyLimitMixin` — single responsibility: *own the cap knob and the enforcement
     decision in one place for both views*. It carries the `max_request_body_bytes` class
     attribute (with the precedence contract in its docstring) and one
     `_enforce_request_body_limit(request)` method. Justification: without it the class attribute,
     its docstring, and the whole enforcement body are duplicated on the sync and async classes —
     the single largest duplication this slice risks.
  2. `_resolved_max_request_body_bytes(value)` — module-level **pure** function: the
     constructor > setting > default resolution plus validation. Module-level rather than a mixin
     method so the whole precedence matrix is testable package-tier without constructing a view or
     a request (Decision 13 Placement puts exactly that matrix in `tests/test_views.py`).
  3. `_declared_content_length(request)` — module-level pure function returning `int | None`,
     tolerant of an absent or unparseable `CONTENT_LENGTH`. Justification below (duplication risk
     5): a bare `int(request.META.get("CONTENT_LENGTH"))` raises on both the absent and the garbage
     case, and swallowing that inline inside the enforcement body would bury a real branch.
  Plus one module-level constant for the spec-pinned wire text (`_BODY_LIMIT_REASON`), so the
  string that goes on the wire has one definition that package-tier tests can import while live
  tests assert the literal bytes.
  **Nothing else.** No new module, no new exception, no `utils/` addition, no second settings key
  (the spec authorizes exactly one), no `__init__.py` change, no new soft-dependency guard.

- **Duplication risk avoided.**
  1. **Two copies of the enforcement body (sync + async).** The check is **fully synchronous on
     both transports** — `request.META` is a dict and `HttpRequest.body` is a sync property that
     upstream's *async* adapter also reads synchronously
     (`cross_web/request/_django.py::AsyncDjangoHTTPRequestAdapter.get_body` is
     `return self.request.body`, no thread offload). So exactly **one** shared sync method serves
     both classes. The only irreducible duplication is the two 3-line `run` overrides, which
     differ solely in `async`/`await` — the same irreducible split upstream itself carries in its
     `dispatch` pair. Stated here so Worker 3 reads it as irreducible rather than as a miss.
  2. **Re-implementing upstream's `HTTPException` → response translation.** Avoided by hooking
     `run` (inside `dispatch`'s `try`) rather than `dispatch` (outside it). See "Why `run`" below.
  3. **A second place that knows the default.** The `1 MiB` default is applied **once**, in
     `conf.py`'s accessor. `views.py` never names it; the resolver only knows "`None` means ask
     `conf.py`".
  4. **A local settings read.** Forbidden by the Helper-reuse obligation; the resolver calls the
     `conf.py` accessor.
  5. **Two spellings of "read the declared length".** One helper, called once.
  6. **A parallel live harness for the ASGI-shaped rows.** One module-local `_asgi_post(...)`
     helper drives Django's own `ASGIHandler` for all three ASGI rows (absent `Content-Length`,
     understated `Content-Length`, multi-fragment body); it adds no project file and no second
     reload discipline. See "The ASGI rows" below.
  7. **Re-proving Slice 1's contracts.** This slice adds no row that re-asserts middleware, CSRF,
     headers, cache policy, or routing; those are Slice 1's and stay where they are.

### Upstream, Django, and empirical verification (read and executed, not remembered)

Read in full: `.venv/lib/python3.14/site-packages/strawberry/django/views.py`;
`strawberry/http/sync_base_view.py::SyncBaseHTTPView.run` / `::execute_operation` /
`::parse_http_body`; `strawberry/http/async_base_view.py::AsyncBaseHTTPView.run`;
`cross_web/request/_django.py` (both adapters); `cross_web/exceptions.py`;
`django/http/request.py::HttpRequest.body` + `::_check_data_too_big`;
`django/core/handlers/asgi.py::ASGIHandler.handle` / `::read_body` / `::create_request` +
`ASGIRequest.__init__`; `django/core/handlers/exception.py::response_for_exception`;
`django/test/client.py::RequestFactory.generic` / `AsyncRequestFactory.generic` /
`AsyncClientHandler.__call__`; `django/core/handlers/wsgi.py::LimitedStream`. Both the current
stack (`django 6.0.5` / py3.14) **and the compatibility floor** (`/tmp/dsf-floor-r5`:
`django 5.2.0` / py3.10.19) were read and executed.

**The enforcement hook, named exactly.** `SyncBaseHTTPView.run(self, request, context=UNSET,
root_value=UNSET)` for `DjangoGraphQLView`, and `AsyncBaseHTTPView.run(self, request,
context=UNSET, root_value=UNSET)` (`async def`) for `AsyncDjangoGraphQLView`. Both are called
from exactly one place — their view's `dispatch`, as `self.run(request=request)`, **inside** the
`try/except HTTPException` that produces `HttpResponse(content=e.reason, status=..., content_type=
"text/plain")`. Nothing else in the package, the tests, or the example project calls `.run(`
(grepped). Both `run` bodies do the following before any parse or execution, which is what makes
the top of `run` the earliest correct point: sync `run` → `is_request_allowed` →
`should_render_graphql_ide` → `get_sub_response` / `get_context` / `get_root_value` →
`execute_operation` → `parse_http_body` → `parse_json` → `schema.execute_sync`; async `run` →
`get_root_value` → `is_websocket_request` (always `False` on the Django view) → the same chain.

**Why `run` and not `dispatch`** (Slice 1's staging anchor says `dispatch`; this plan refines it,
and the anchor is deleted in this slice so no stale prose survives). A guard placed in a `dispatch`
override raises **outside** upstream's `try`, so the package would have to author its own
`HTTPException` → `HttpResponse(text/plain)` translation — a near-copy of upstream's four lines, in
two places (sync + async) or in a fourth helper. Hooking `run` reuses the translation the package
*already* depends on for `_patched_parse_json`'s `400`s, which is why the 413 comes out
byte-identical in shape to the shipped 400. Verified by execution, not inference (below).

**Empirical matrix** (scripts kept at
`<scratchpad>/probe_s2.py`, `probe_s2_multipart.py`, `probe_s2_shape.py`; each row run on **both**
`django 6.0.5`/py3.14 and `django 5.2.0`/py3.10.19):

| Probe | Django 6.0.5 | Django 5.2.0 (floor) |
|---|---|---|
| `run` override raising `HTTPException(413, reason)`, sync `Client` | `413`, `text/plain`, exact reason | identical |
| same, `AsyncClient` | `413`, `text/plain`, exact reason | identical |
| same, real `ASGIHandler` + 3 body fragments | `413`, `text/plain`, exact reason | identical |
| over-cap body that is **malformed** JSON | `413` (never the parse's `400`) | identical |
| under-cap body that is malformed JSON | `400 "Unable to parse request body as JSON"` | identical |
| WSGI, `CONTENT_LENGTH` understated to `10` of `100` | app reads **10** bytes (`LimitedStream` truncates) | identical |
| WSGI, `CONTENT_LENGTH` absent | app reads **0** bytes | identical |
| ASGI, no `Content-Length`, 3 x 40-byte fragments | app reads **120** bytes | identical |
| ASGI, `Content-Length: 10`, actual 120 | app reads **120** bytes | identical |
| `DATA_UPLOAD_MAX_MEMORY_SIZE` < body, WSGI **and** `AsyncClient` | **`400`** (SuspiciousOperation; no exception reaches the test client) | identical |
| ASGI seekable spooled stream, `DATA_UPLOAD_MAX_MEMORY_SIZE` < body, no `Content-Length` | **`400`** (the seekable actual-size check fires) | **`200`** — no such check exists at the floor |
| multipart handled by the declared gate only | `request._body` **never** materialized, `request.FILES` / `request.POST` still parse | identical |
| `as_view(max_request_body_bytes=64)` with the attribute inherited from a mixin | binds; lands in `view_initkwargs` | identical |

**Three findings the plan and the tests turn on:**

1. **`ASGIHandler.create_request`'s `except RequestDataTooBig: -> 413` is unreachable for our
   flow.** It wraps only `ASGIRequest(scope, body_file)` construction, and `ASGIRequest.__init__`
   never touches the body (read top-to-bottom). `RequestDataTooBig` is raised lazily from
   `HttpRequest.body`, i.e. inside the view, where `response_for_exception` maps
   `SuspiciousOperation` to **`400`**. So Django's own ceiling answers `400` on **both** transports
   and **both** Django versions. The spec asserts `413` for the ASGI direction twice (Current state
   line 289, Edge cases lines 1347-1351) — recorded as a spec-reconciliation candidate below; the
   tests pin the measured behavior.
2. **At the compatibility floor, Django provides *no* protection against an absent or understated
   `Content-Length`.** `HttpRequest.body`'s seekable actual-size check does not exist in Django
   5.2.0 (only the declared-`CONTENT_LENGTH` check does). The package's counted check is therefore
   the *only* application-level bound there — which is precisely Decision 7's "counted, not
   declared", and the strongest available argument for it. **Test-design consequence (mandatory):**
   no S2 test may lower `DATA_UPLOAD_MAX_MEMORY_SIZE` *and* use the ASGI harness in the same row,
   because that is the one cell where the two Django versions diverge. Keep Django's ceiling out of
   the way in every ASGI row, and exercise it only through the declared-length path (identical on
   both versions). With that rule, row 18's floor parity is bit-identical.
3. **`request.body` is safe to read at the top of `run`.** It caches `_body` and rebinds `_stream`
   to a `BytesIO`, so upstream's later adapter read is the cached value, and `request.POST` /
   CSRF's form-token path still work (probed). The one case where reading it is *harmful* is
   multipart, which the declared-only branch never reads (probed: `_body` stays unmaterialized even
   after `request.FILES` is parsed) — the `Upload`-scalar streaming path is untouched.

### Implementation steps

Line numbers are pin-at-write-time navigational hints; verify against the current source before
editing.

1. **`django_strawberry_framework/conf.py` — one new settings key, one new reader.**
   - After `RELAY_GLOBALID_STRATEGY_KEY` (`conf.py:108`), add `MAX_REQUEST_BODY_BYTES_KEY =
     "MAX_REQUEST_BODY_BYTES"` with the `#` comment block every sibling key carries. The comment
     must state: it is the cumulative request-body ceiling **in bytes** for the GraphQL HTTP path
     served by `views.py`'s two views (spec-046 Decision 7); it is **counted, not declared**; the
     default is `1_048_576`; `None` disables the package cap and leaves only Django's
     `DATA_UPLOAD_MAX_MEMORY_SIZE` **and the deployment-layer cap, which the package requires
     rather than suggests** (Decision 8 — see step 4 for the surface split); and that a GraphQL
     request body is a query document, which is why it does not inherit Django's upload-shaped
     knob.
   - Add `max_request_body_bytes_setting() -> int | None` beside
     `relay_globalid_strategy_setting` (`conf.py:421-432`), one line:
     `return getattr(settings, MAX_REQUEST_BODY_BYTES_KEY, 1_048_576)`. Docstring in the shipped
     shape: what it reads, the default, its consumer
     (`views.py::_resolved_max_request_body_bytes`), and that validation lives there because
     `conf.py` does not validate domain values.
   - **Nothing else in `conf.py` changes.** No new validation branch, no `Settings` change.

2. **`django_strawberry_framework/views.py` — the cap.**
   - **Delete the `TODO(spec-046 Slice 2)` anchor** (`views.py:46-49`, a four-line `#` block above
     the classes) **in this same change**. This slice ships the work it names, so `AGENTS.md`
     #"removed in the same change that ships the slice" applies, and BUILD.md's integration pass
     greps for survivors. Do **not** replace it with another `TODO(`; the new docstrings carry
     `spec-046 Decision 7` / `Decision 8` provenance instead, which `AGENTS.md` keeps.
   - Imports: add `from cross_web import HTTPException`, `from django.http import HttpRequest`
     (typing only — keep it under `TYPE_CHECKING` only if `from __future__ import annotations`
     makes it unused at runtime, which it does), `from django_strawberry_framework.conf import
     max_request_body_bytes_setting`, and `from django_strawberry_framework.exceptions import
     ConfigurationError`. **Still no `channels`, no `.routers`, no `require_*` guard** — the
     module's `channels`-free contract and its docstring paragraph stay true (`conf.py`,
     `exceptions.py`, and `cross_web` reach no `channels`).
   - `_BODY_LIMIT_REASON = "Request body exceeded the configured GraphQL request-body limit."` —
     verbatim from spec Error shapes (line 575-576). Module-level so tests can import it.
   - `_resolved_max_request_body_bytes(value: object) -> int | None` — the precedence + validation,
     in `resolve_strategy`'s shape:
     - `value is None` -> `value = max_request_body_bytes_setting()` (kwarg **not** supplied ->
       the setting; the setting's own default is `conf.py`'s).
     - `value is None` still -> `return None` (**the setting** `None` is the documented "disable
       the package cap" value).
     - `isinstance(value, bool)` or not `isinstance(value, int)` or `value <= 0` ->
       `ConfigurationError` naming the received type/value **and naming `None` as the documented
       way to disable the cap**. Rejecting `0` is deliberate: `0` is the near-universal
       "unlimited" spelling in other libraries, and under `>`-comparison semantics it would
       silently mean "reject every non-empty body" — a fail-loud error is the only reading that
       cannot be misread. `bool` is rejected explicitly because `isinstance(True, int)` is `True`.
     - else `return value`.
   - `_declared_content_length(request) -> int | None` — `int(request.META.get("CONTENT_LENGTH"))`
     inside `except (TypeError, ValueError): return None`. `TypeError` is the absent case
     (`int(None)`), `ValueError` the garbage case (probed: a non-numeric `CONTENT_LENGTH` reaches
     `META` intact). Returning `None` for both is the fail-safe direction: an unmeasurable
     declaration falls through to the counted check rather than being trusted.
   - `class _RequestBodyLimitMixin:` — private, **not** in `__all__`. Class docstring owns the
     whole contract (see step 4 for the required content). Body:
     - `max_request_body_bytes: int | None = None` — **a class attribute is mandatory**, not a
       stylistic choice: `django/views/generic/base.py::View.as_view` raises
       `TypeError("... received an invalid keyword ... as_view only accepts arguments that are
       already attributes of the class")` for any keyword that is not already an attribute
       (`hasattr`, so inheriting it from this mixin satisfies the guard — probed). `None` here
       means "this mount did not override the setting".
     - `_enforce_request_body_limit(self, request) -> None`, in this exact order:
       1. `limit = _resolved_max_request_body_bytes(self.max_request_body_bytes)` — resolve
          (and therefore validate) **first**, so a misconfigured mount fails loud on every request
          including GET.
       2. `if limit is None or request.method == "GET": return` — the cap is disabled, or the
          request carries no body the view will read (spec Edge cases lines 1362-1364; the
          query-param size is card 047 / audit S4, and `_patched_parse_query_params` already
          shields those parses).
       3. `declared = _declared_content_length(request)`; `if declared is not None and declared >
          limit: raise HTTPException(413, _BODY_LIMIT_REASON)` — Decision 7 step 1, rejecting
          **without reading the body** (probed: `_body` stays unmaterialized).
       4. `if request.content_type == "multipart/form-data": return` — Decision 7 step 3 and Edge
          cases lines 1357-1361. `HttpRequest.content_type` is the bare type with parameters split
          off (probed), so equality is correct and `boundary=...` is irrelevant.
       5. `if len(request.body) > limit: raise HTTPException(413, _BODY_LIMIT_REASON)` — Decision 7
          step 2. `>` not `>=`: a body exactly *at* the limit is allowed (Test plan row 13 lists
          "below, at, and above").
   - `class DjangoGraphQLView(_RequestBodyLimitMixin, GraphQLView):` — mixin **first** (the
     conventional, override-capable order; see the test note in step 3 for the one Slice-1
     assertion this changes). Add exactly:
     ```python
     def run(self, request, *args, **kwargs):
         self._enforce_request_body_limit(request)
         return super().run(request, *args, **kwargs)
     ```
     `*args, **kwargs` forwarding avoids importing Strawberry's `UNSET` sentinel just to restate
     upstream's defaults; upstream calls `self.run(request=request)` so the signature binds.
   - `class AsyncDjangoGraphQLView(_RequestBodyLimitMixin, AsyncGraphQLView):` — the `async def`
     twin of the same three lines with `await super().run(...)`.
   - Update both class docstrings: they currently say the class "overrides nothing" / has an
     "identical surface". After this slice each overrides `run` and accepts one package keyword.
     Leave the inherited-upstream-kwarg sentences intact.
   - `__all__` is **unchanged** — `("AsyncDjangoGraphQLView", "DjangoGraphQLView")`. The mixin and
     all three helpers stay private, and `django_strawberry_framework/__init__.py` is not touched
     (Decision 6's leaf-module posture; `tests/test_views.py` already pins both).

3. **Tests** — see "Test additions / updates" for the full matrix. Two *existing* tests need
   deliberate attention and must not be allowed to weaken:
   - `tests/test_views.py::test_views_module_imports_with_channels_absent` asserts
     `module.DjangoGraphQLView.__base__ is not DjangoGraphQLView.__base__` as its proof that
     **upstream's** module body re-executed under the simulated `channels` absence. With the mixin
     first, `__base__` becomes the package's own mixin — the assertion would still pass while
     silently proving nothing about upstream. **Re-aim it** to pin upstream's class identity
     directly: capture the upstream class at module import, and inside the block assert the
     freshly imported `strawberry.django.views.GraphQLView` `is not` the captured one **and** is in
     `module.DjangoGraphQLView.__mro__`. That is strictly stronger than the `__base__` pair and is
     independent of the base list. Keep `module.DjangoGraphQLView is not DjangoGraphQLView`.
   - `tests/base/test_conf.py::test_delattr_clears_stale_cache_and_restores_defaults` enumerates
     every accessor's override value and post-delete default. A new key that is not added there
     leaves the enumeration silently stale, so add the `MAX_REQUEST_BODY_BYTES` row (an override
     value plus `max_request_body_bytes_setting() == 1_048_576` after the delete). `AGENTS.md`
     allows `tests/base/test_conf.py` to grow; no new file in `tests/base/`.

4. **Documentation surface — what Slice 2 writes, and what it hands to Slice 5.** The Slice-2
   checklist box for Decision 8 ("documented as a **co-requirement**, not an alternative") is
   discharged **at the code-documentation layer only**, because Decision 8 itself assigns the
   consumer-facing prose to Slice 5 ("Slice 5's transport guidance states plainly that ...") and
   the spec's Doc updates put every `.md` surface in Slice 5's set.
   - **Slice 2 writes** (shipped source, durable, reviewable in this diff):
     - `conf.py`'s `MAX_REQUEST_BODY_BYTES_KEY` comment block — the key's meaning, the default,
       `None` semantics, and the sentence that the deployment-layer cap is **required alongside**
       this one.
     - `views.py::_RequestBodyLimitMixin`'s class docstring — the full contract: the
       constructor > setting > default precedence; that the count is of received bytes, not of
       `Content-Length`; the multipart bound (declared size plus Django's `MultiPartParser`, and
       explicitly *not* per-file or aggregate limits, which are card 047 / audit S4); that the GET
       path is a no-op; **and the honest boundary** — the view guarantees the application never
       parses, allocates a document from, or executes a schema against an over-limit body, while
       `django.core.handlers.asgi.ASGIHandler.read_body` has already drained the whole request into
       a spooled temporary file before any application cap can run, so a reverse-proxy /
       ASGI-server cap is a co-requirement (Decision 8), not an alternative.
     - `views.py`'s two class docstrings — one sentence each naming the keyword.
   - **Slice 5 writes** (not this slice): the `docs/README.md` transport guidance with the concrete
     directives (`client_max_body_size`, the ASGI-server flags, the Daphne request-buffer note),
     the migration note, the GLOSSARY entries (DB + re-render) for the body cap, the `docs/TREE.md`
     regeneration, and `examples/fakeshop/test_query/README.md`'s new S2 acceptance rows.
   - **Neither slice** touches `CHANGELOG.md` or the version quintet (Decision 15).

5. **Hygiene, in this order.** `uv run ruff format .`; `uv run ruff check --fix .`;
   `uv run python scripts/check_trailing_commas.py <explicit paths only>` — **never** repo-wide,
   whose auto-fix default would rewrite the maintainer's untracked `drys.md` / `vulns.md`. ASCII
   only in every `.py` (the reason string and every docstring stay ASCII). Then `git status
   --short` and classify every modified file per BUILD.md's Validation-run rule. The
   baseline-dirty files (`django_strawberry_framework/filters/sets.py`, `tests/filters/test_sets.py`,
   `docs/feedback.md`, `docs/feedback2.md`, `drys.md`, `vulns.md`,
   `docs/row-preserving-predicates-part1-plan.md`, `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`,
   `examples/fakeshop/db.sqlite3`) are out of scope: do not edit, do not revert.

### Test additions / updates

Every Test-plan row below is mapped to exactly one tier with the reason. Rows 13-16 are
request-shaped and therefore **live** (`AGENTS.md` rule 9 + the live-first coverage mandate);
row 17's exhaustive matrix and the validation branches are **package-tier** because Decision 13
Placement assigns them there and because they are properties of a pure function, not of a request.

**Live tier — `examples/fakeshop/test_query/test_transport_api.py` (extend; do not create a second
file).** Reuse `_post`, `_assert_no_graphql_envelope`, `_TYPENAME`, `_ITEMS`, `_CREATE_CATEGORY`,
and extend the existing module-level `urlpatterns` with the probe mounts below (each building its
view at *request* time, like `_ide_off_view`, so it tracks the per-test schema rebuild):

- `cap-tiny/` — the package view with a small `max_request_body_bytes=` (e.g. 256).
- `cap-spy/` — a module-local `DjangoGraphQLView` subclass with the same small cap that overrides
  `parse_json` to append to a module list and delegate with `super()`. This is the row-15 spy.
- `cap-off/` — the package view with a large `max_request_body_bytes=` (used for the
  Django's-ceiling-fires-first direction).

| Test-plan row | Tier | Shape and why |
|---|---|---|
| 13 declared **below** / **at** / **above** the limit | live | Parametrized over the `cap-tiny/` mount with body sizes padded to `limit-N`, exactly `limit`, `limit+N`. Below/at -> `200` with data; above -> `413`, `text/plain`, exact `_BODY_LIMIT_REASON` literal. Pins `>` not `>=`. |
| 13 **no** `Content-Length` (WSGI colour) | live | `Client()` with `CONTENT_LENGTH=""`: Django's `LimitedStream` gives the app **0** bytes, so the outcome is upstream's `400` malformed-JSON, not a `413`. The row's point is the honest one — on WSGI the declared value cannot *understate* what the application receives (Decision 7 step 2's own claim), so there is nothing for the counted check to catch. Assert `400` + `_assert_no_graphql_envelope` + not-our-reason. |
| 13 no `Content-Length` (ASGI colour) | live, ASGI harness | The interesting colour: the app receives the whole body with no declaration at all, and the **counted** check produces `413`. Only reachable through `ASGIHandler` (see below). |
| 13 declared-small body whose streamed content exceeds it (WSGI) | live | `Client()` with `CONTENT_LENGTH` overridden below the real payload: the app reads only the declared bytes (probed), so `400` malformed JSON. Same honest framing as the row above. |
| 13 declared-small / streamed-larger (ASGI) | live, ASGI harness | `content-length: 10` with a 400-byte body: the app reads 400, the counted check fires -> `413`. This is the row that proves "a `Content-Length` that is absent or lying cannot buy a larger body". |
| 13 **multiple ASGI fragments crossing the boundary** | live, ASGI harness | Three fragments each under the cap, summing over it -> `413`. Plus a control: three fragments summing **under** the cap -> `200` with data, so the harness is proven capable of success and the 413 is attributable to the size. This is the row that earns the word *cumulative*. |
| 14 JSON | live | Covered by row 13's below/at/above parametrization on a real `{ __typename }` / `allItems` operation. |
| 14 malformed JSON | live | Two directions in one test: malformed **under** the cap -> `400 "Unable to parse request body as JSON"` (the shipped behavior, unchanged); the *same* malformed bytes padded **over** the cap -> `413`. The discrimination is itself a parse proof: a `400` could only come from a parse that ran. |
| 14 multipart | live | (a) declared **over** the cap on `cap-tiny/` -> `413`; (b) the un-broken-`Upload`-path proof is the existing `examples/fakeshop/test_query/test_uploads_api.py` multipart rows passing unchanged against fakeshop's default mount (which now carries the 1 MiB default) — Worker 2 must run that file in its focused scope and say so. The "never materialized" witness is package-tier (below), because it is view-internal state a wire response cannot show. |
| 15 early `413` with **proof neither parse nor execution ran** | live | One test, two directions, on the `cap-spy/` mount. Over-limit direction: a **valid** `createCategory` mutation padded past the cap -> `413` + exact reason, **and** the spy's `parse_json` call list is empty, **and** `models.Category.objects.filter(name=...).exists()` is `False` (a real DB witness that the schema never executed — the same negative-witness idiom the shipped row-4 CSRF test already uses). Control direction, same test: the same mutation under the cap -> `200`, the spy recorded exactly one `parse_json` call, and the row exists. **The control is mandatory** — two empty witnesses prove nothing on their own (BUILD.md #"Query-shape tests must pin the load-bearing property"). |
| 16 which ceiling fired, package direction | live | `cap-tiny/` with `DATA_UPLOAD_MAX_MEMORY_SIZE` left at its default -> `413` with **our** reason. |
| 16 which ceiling fired, Django direction | live | `cap-off/` under `override_settings(DATA_UPLOAD_MAX_MEMORY_SIZE=<small>)` -> Django's own **`400`** (not `413`; measured on both Django versions), no GraphQL envelope, and explicitly **not** `_BODY_LIMIT_REASON`. Docstring must record that the spec's Edge-case sentence predicts `413` on ASGI and that the measured behavior is `400` on both transports because `RequestDataTooBig` is raised lazily inside the view. Do **not** combine this override with the ASGI harness (finding 2). |
| 17 kwarg beats setting; setting beats default; `None` disables | live (behavioral) + package (matrix) | Live: one test under `override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"MAX_REQUEST_BODY_BYTES": <large>})` showing the `cap-tiny/` mount still rejects at its own small kwarg while fakeshop's default mount accepts the same body (kwarg beats setting), plus a small **setting** with no kwarg rejecting on the default mount (setting beats default), plus `"MAX_REQUEST_BODY_BYTES": None` accepting a body that the default would reject (disable). Package: the exhaustive pure-function matrix (below). |
| 18 py3.10 / Django 5.2.0 floor parity | maintainer-invoked gate, recorded by Worker 2 | Run the S2 focused scope in the existing isolated floor venv `/tmp/dsf-floor-r5` (`python 3.10.19`, `Django 5.2.0`) — **never** the shared `.venv` (`uv pip install` ignores `UV_PROJECT_ENVIRONMENT`). Every planned row is version-identical **provided** finding 2's rule is honored. Record the invocation and result in the build report. |

**Package tier — `tests/test_views.py` (extend).** Only what a live request cannot express:

- The precedence matrix over `_resolved_max_request_body_bytes` (pure function, no request): kwarg
  int wins; kwarg `None` + setting int -> the setting; kwarg `None` + no setting -> `1_048_576`;
  setting `None` -> `None` (disabled); kwarg int + a *different* setting -> the kwarg. Use
  pytest-django's `settings` fixture or `override_settings` for the setting rungs.
- The validation matrix -> `ConfigurationError`, parametrized: `0`, a negative int, `True`, a
  `str`, a `float`, an object — each asserting the message names the received type and mentions
  `None` as the way to disable. Both rungs (a bad kwarg and a bad setting value) so neither path is
  unvalidated.
- `max_request_body_bytes=` binds through `as_view()` on **both** classes and lands in
  `view_initkwargs` — the class-attribute constraint made explicit. Keep the existing
  four-upstream-kwarg test unchanged (it pins Slice 1's contract) and add this as its own
  parametrized test.
- `_enforce_request_body_limit` against `RequestFactory`-built requests, which is the only way to
  witness view-internal state: (a) a declared-over-limit request raises `HTTPException(413)` **and
  leaves `hasattr(request, "_body")` `False`** (Decision 7 step 1's "without reading the body");
  (b) a **multipart** request whose declared size is under the cap returns without raising and
  **still** leaves `_body` unmaterialized (Decision 7 step 3 / Edge cases #"Multipart must not be
  materialized"); (c) a GET with a hostile `CONTENT_LENGTH` is a no-op; (d) an unparseable
  `CONTENT_LENGTH` falls through to the counted check.
- The mixin stays private: `_RequestBodyLimitMixin` is not in `views.__all__` (the existing exact
  `__all__` assertion already covers it — do not weaken that test).
- The re-aimed `channels`-absence assertion from step 3.

**Package tier — `tests/base/test_conf.py` (extend).** The new accessor's row in the
override/delete enumeration (step 3).

**Coverage map** (so no branch is left unreachable; workers do not run `--cov`): resolver — kwarg
present / kwarg `None` + setting present / both `None` (default) / setting `None` / each invalid
shape; `_declared_content_length` — parseable / absent (`TypeError`) / garbage (`ValueError`);
`_enforce_request_body_limit` — disabled, GET, declared-over, multipart return, counted-over,
counted-under; both `run` overrides — over-limit (raise) and under-limit (delegate). Every one of
those is claimed by a row above.

**Temp/scratch tests:** none planned. Worker 3 may re-derive any table row above under
`docs/builder/temp-tests/slice-2/`; the three probe scripts under the session scratchpad are the
reference implementations (in particular the `ASGIHandler` driver's `receive` shape: queue the
fragments, then await something that never resolves, and let `ASGIHandler.handle` cancel the
`listen_for_disconnect` task — returning `http.disconnect` instead would abort the request).

**The ASGI rows, justified.** Neither `django.test.Client` nor `django.test.AsyncClient` can
present an unmeasured, understated, or fragmented body: both derive `CONTENT_LENGTH` from the
payload, both construct the request object directly, and `AsyncClientHandler` wraps the whole body
in one `LimitedStream` without ever calling `ASGIHandler.read_body` (all read, all probed; passing
a second `content-length` header through `AsyncClient` produces `"100,10"` and a `ValueError`).
Test-plan row 13 requires ASGI fragments, so the plan drives Django's own `ASGIHandler` in-process
against fakeshop's real settings, `MIDDLEWARE`, URLconf, and mounted view. This is **not** the
`tests/`-local ASGI harness the spec's Risks section rejects (that rejection is about the WebSocket
revalidation matrix), and it does **not** add a fakeshop `asgi.py` or touch `channels` — the
spec's non-goal is a shipped ASGI *surface* and a live *Channels* tier, neither of which this
creates. Keep these rows DB-free (`{ __typename }`, no `django_db` marker), mirroring the shipped
`test_the_async_package_view_runs_inside_djangos_middleware_chain` row, so no ORM access happens
from the event loop and no connection teardown hazard is introduced.

**Focused scope for Worker 2** (no `--cov*` flag anywhere; `--no-cov` only):
`uv run pytest tests/test_views.py tests/base/test_conf.py
examples/fakeshop/test_query/test_transport_api.py examples/fakeshop/test_query/test_uploads_api.py
examples/fakeshop/test_query/test_client_api.py --no-cov`. The full sweep is Worker 1's final gate.

### Implementation discretion items

Assessed and delegated — each is a spelling or arrangement choice between equally correct shapes:

1. Whether `conf.py`'s `1_048_576` default is an inline literal in the accessor (matching the five
   shipped accessors exactly) or a named module constant. Fixed contract: it appears **once** in
   production code, and `views.py` never restates it.
2. The private names: `_RequestBodyLimitMixin`, `_resolved_max_request_body_bytes`,
   `_declared_content_length`, `_BODY_LIMIT_REASON` are proposals. Fixed: they stay private and out
   of `__all__`.
3. The exact `ConfigurationError` wording, provided it names the received type and points at `None`
   as the documented disable.
4. The probe mount paths and cap values (`cap-tiny/` at 256, `cap-spy/`, `cap-off/` are
   proposals), and whether the three mounts are three functions or one parametrized factory.
5. Whether row 13's below/at/above trio is one parametrized test or three, and the same for the
   row-17 live precedence directions.
6. The `_asgi_post` helper's exact signature and return shape (a tuple vs a small dataclass), and
   whether it lives beside `_post` or at the bottom of the live module.
7. All docstring wording, subject to the content requirements in step 4.
8. Whether the multipart live rows drive `createMediaSpecimen` (the shipped upload mutation) or a
   simpler multipart POST that never needs to succeed.

**Not discretion — fixed by the spec or by verified upstream/Django behavior, do not vary:** the
hook is `run` on both classes (never `dispatch`, which would force a duplicate response
translation); `max_request_body_bytes` is a **class attribute**; the check order is
resolve/validate -> GET no-op -> declared gate -> multipart return -> counted check; the comparison
is `>`; multipart never reads `request.body`; the reason string is the spec's verbatim sentence;
`413` comes from `HTTPException` through upstream's `dispatch`; the setting key is exactly
`MAX_REQUEST_BODY_BYTES` and it is the **only** settings key this card adds; `None` at the setting
rung disables and `None` at the kwarg rung defers; validation raises `ConfigurationError`; the
`TODO(spec-046 Slice 2)` anchor is deleted in this slice; no `__init__.py` change, no `.md` edits,
no version-quintet or `CHANGELOG.md` movement, no `channels` import in `views.py`, no fakeshop
`asgi.py`.

### Planning-pass spec-reconciliation notes (Worker 1)

Recorded, **not acted on** — the spec is not edited during a planning pass. Worker 1's
final-verification pass decides whether any of these warrants a spec edit.

1. **Django's own ceiling answers `400`, not `413`, on ASGI.** Spec Current state line 289
   ("`ASGIHandler.create_request` converts the resulting `RequestDataTooBig` into a `413`") and
   Edge cases lines 1347-1351 ("ASGI converts it to its own `413`; on WSGI it surfaces as a `400`")
   are both inaccurate against Django 5.2.0 **and** 6.0.5: `create_request`'s `except
   RequestDataTooBig` guards only `ASGIRequest` construction, which never reads the body, so the
   exception is raised lazily inside the view and `response_for_exception` maps it to `400` on both
   transports. Measured on both versions. The *conclusions* the spec draws (both ceilings are
   correct outcomes; the tests assert which fired) are unaffected; only the predicted status code
   for one direction is wrong. **Candidate spec edit** at final verification: correct both
   sentences to "`400` (`SuspiciousOperation`) on both transports". The tests pin the measured
   behavior either way.
2. **The floor's `HttpRequest.body` has no seekable actual-size check.** Spec Current state lines
   283-290 describe the seekable/spooled-size rejection as what "the installed Django" does; it
   exists in 6.0.5 and **not** in the documented compatibility floor 5.2.0. So the sentence is
   version-specific, and at the floor the package's counted check is the only application-level
   bound against an absent or understated `Content-Length`. **Candidate spec edit:** qualify the
   bullet by version. This strengthens rather than weakens Decision 7; no plan change follows
   beyond the mandatory test-design rule (finding 2 above).
3. **The package default for `MAX_REQUEST_BODY_BYTES` is not stated explicitly.** The spec's
   precedence is "constructor > setting > default" and Test-plan row 17 requires "the setting beats
   the default", so a concrete default must exist; the only value the spec names anywhere is
   `1_048_576` in its own settings example (line 524), which also matches Decision 7's rationale
   (a query document is orders of magnitude smaller than Django's upload-shaped 2.5 MB default).
   The plan therefore fixes the default at `1_048_576` as a derivation from the spec, not an
   invention. **Candidate spec edit:** state the default in the setting block. Verified safe
   against the existing suite: no live or package test posts a body within an order of magnitude of
   1 MiB, and the multipart uploads are a few hundred bytes.
4. **`None` means different things at the two precedence rungs**, by the spec's own text: the view
   kwarg's `None` defers to the setting (User-facing API line 506, "None -> the
   MAX_REQUEST_BODY_BYTES setting") while the *setting*'s `None` disables the cap (line 522-523;
   Decision 7 step 4). That is coherent and matches the shipped `NESTED_CONNECTION_STRATEGY` shape
   (kwarg `None` = unspecified), but it means **a single mount cannot disable the cap for itself** —
   only the project-wide setting can. Recorded as a known limitation the mixin docstring must
   state. No spec edit proposed: inverting it would break the documented public API block, and an
   additional sentinel value in a URLconf-facing keyword is worse than the limitation.
5. **The Slice-2 checklist's Decision-8 box spans two slices.** Its prose obligation is assigned to
   Slice 5 by Decision 8 itself and by the spec's Doc updates; only the code-level statement is
   in scope here. Step 4 fixes the split explicitly, and Worker 2 must record the Slice-5 hand-off
   in its build report so Worker 1's box audit sees it rather than inferring a silent deferral.
6. **Spec status line re-verified** (`docs/spec-046-transport_security-0_0_15.md` lines 37-44):
   "Status: **IN BUILD — Slice 1 (S1) is built and accepted; Slices 2-5 remain.**" is accurate at
   the start of this planning pass. It will need Worker 1's edit once Slice 2 is `final-accepted`.
7. **No spec-vs-codebase gap in the symbols this slice names.** Verified on disk:
   `django_strawberry_framework/views.py` with both view classes (Slice 1), `conf.py`'s key block
   and five accessors, `exceptions.py::ConfigurationError`, `cross_web.HTTPException`,
   `strawberry.django.views.{GraphQLView,AsyncGraphQLView}.dispatch`,
   `examples/fakeshop/config/urls.py`'s `DjangoGraphQLView` mount, and
   `examples/fakeshop/test_query/test_transport_api.py`'s `_post` /
   `_assert_no_graphql_envelope` / Probe `urlpatterns`.

### Spec slice checklist (verbatim)

Copied byte-for-byte from `docs/spec-046-transport_security-0_0_15.md` lines 144-154 (the four
sub-bullets of the Slice 2 block), preserving text, nesting, em-dashes, and inline citations. The
anchor links are verbatim from the spec and intentionally resolve only there.

**Post-build divergence, stated rather than hidden** (same handling as Slice 1's seventh box):
box 3's text in the spec was **narrowed** during this slice's final verification to name the two
code-documentation surfaces it actually owns, because Decision 8's own body assigned the
consumer-facing prose to Slice 5 and the checklist contradicted it (final-verification spec change
2). The block below keeps the wording copied at planning time — it is the audited record of what
Worker 2 built and ticked against. The current contract is the spec's; box 3 is ticked against the
narrowed contract, which landed in full. Nothing is deferred and nothing is silently un-ticked.

  - [x] `DjangoGraphQLView` / `AsyncDjangoGraphQLView` enforce a cumulative byte cap
        **before** JSON parsing or schema execution, returning `413`
        ([Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)).
  - [x] One new settings key, `MAX_REQUEST_BODY_BYTES`, in
        `django_strawberry_framework/conf.py`, with a per-mount view-kwarg override
        (constructor > setting > default) — the shipped
        `NESTED_CONNECTION_STRATEGY` precedence shape.
  - [x] The reverse-proxy / ASGI-server hard cap is documented as a **co-requirement**,
        not an alternative
        ([Decision 8](#decision-8--the-deployment-layer-cap-is-a-co-requirement-not-an-alternative)).
  - [x] The full S2 regression matrix earned live over fakeshop's real `/graphql/`.

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short` (below), not memory. `views.py`, `tests/test_views.py`, and
`examples/fakeshop/test_query/test_transport_api.py` are still **untracked** (Slice 1 created them
and the build is uncommitted), so they show as `??` rather than `M`.

- `django_strawberry_framework/conf.py` — one new key constant `MAX_REQUEST_BODY_BYTES_KEY` with
  its `#` comment block (bytes; counted-not-declared; `1_048_576` default; `None` disables; the
  deployment-layer cap is **required alongside**, not an alternative; and why a query document does
  not inherit Django's upload-shaped knob), plus the one-line thin reader
  `max_request_body_bytes_setting()` beside `relay_globalid_strategy_setting`. No `Settings` change,
  no validation branch.
- `django_strawberry_framework/views.py` — **deleted** the four-line `TODO(spec-046 Slice 2)` `#`
  anchor; added `_BODY_LIMIT_REASON`, `_MULTIPART_CONTENT_TYPE`,
  `_resolved_max_request_body_bytes`, `_declared_content_length`, `_RequestBodyLimitMixin` (the cap
  contract in one docstring, including the honest `read_body` boundary), and the two ~3-line `run`
  overrides. Both view docstrings updated from "overrides nothing" to name the one override and the
  one package keyword; module docstring gained the cap paragraph and had its `channels`-free claim
  widened to cover the three new imports. `__all__` unchanged.
- `tests/test_views.py` — re-aimed the `channels`-absence identity assertion (see notes) and added
  the Slice-2 package tier; module docstring updated.
- `tests/base/test_conf.py` — the `MAX_REQUEST_BODY_BYTES` row in the accessor override/delete
  enumeration, plus a docstring sentence stating that every defaulted accessor belongs in it.
- `examples/fakeshop/test_query/test_transport_api.py` — three sync probe mounts + one async probe
  mount, the `_asgi_post` `ASGIHandler` driver, `_post_bytes` / `_sized_body` /
  `_assert_body_limit_response` helpers, the `_ParseSpyView`, and rows 13-17; module docstring
  updated. `_post` was refactored to delegate to `_post_bytes` rather than duplicating the call.

**Not touched, deliberately:** `django_strawberry_framework/__init__.py` (no public-surface change),
`CHANGELOG.md` and the version quintet (Decision 15), every `.md` prose surface (Slice 5), and
every file on the build plan's baseline-dirty list.

### Tests added or updated

**Package tier — `tests/test_views.py`** (+31 collected; file 7 -> 38):

- `::test_views_module_imports_with_channels_absent` — **re-aimed, not weakened.** The old
  `module.DjangoGraphQLView.__base__ is not DjangoGraphQLView.__base__` assertion went vacuous the
  moment the mixin took first place in the bases (`__base__` is now
  `_RequestBodyLimitMixin`, so it would have compared the package's own mixin to itself and passed
  while proving nothing about upstream re-executing). It now pins **upstream's own class identity**
  for both views: the freshly imported `strawberry.django.views.{GraphQLView,AsyncGraphQLView}`
  `is not` the class captured at test-module import, **is** in the fresh package view's `__mro__`,
  and the captured one is **not**. Strictly stronger and independent of the base list. Failability
  proven both ways, see `### Validation run`.
- `::test_the_cap_precedence_ladder_is_kwarg_then_setting_then_default` — 4 params: kwarg beats a
  `None` setting, kwarg beats an int setting, no-kwarg takes the setting, setting `None` disables.
- `::test_no_kwarg_and_no_setting_resolves_to_the_one_megabyte_default` — the default reaches the
  resolver from `conf.py`'s accessor (asserted against an empty dict, i.e. key ABSENT rather than
  `None`), pinning that `views.py` does not restate `1_048_576`.
- `::test_an_invalid_cap_value_raises_configuration_error_on_either_rung` — 6 bad values x 2 rungs
  (kwarg and setting), each asserting the message names the received type AND `None` as the disable.
- `::test_the_declared_length_reader_is_none_for_every_unmeasurable_shape` — 4 params: parseable,
  absent (`TypeError`), garbage (`ValueError`), empty string.
- `::test_the_cap_keyword_binds_through_as_view_on_both_classes` — 2 params: the class-attribute
  default is `None` and `max_request_body_bytes=` lands in `view_initkwargs`. The existing
  four-upstream-kwarg test and the bogus-keyword test are untouched.
- `::test_a_declared_over_limit_request_is_refused_without_reading_the_body` — `413` + exact reason
  + `hasattr(request, "_body") is False`, **with the under-limit control in the same test** showing
  `_body` DOES appear when the counted check has to run (else the negative witness is vacuous).
- `::test_a_multipart_request_under_the_declared_gate_is_never_materialized` — `_body` absent before
  AND after Django's `MultiPartParser` produces `POST`; second half pins that the declared gate
  still applies to multipart.
- `::test_the_cap_is_a_no_op_on_get_even_with_a_hostile_content_length`.
- `::test_the_counted_check_fires_when_no_content_length_is_declared_at_all` — over / at / under
  with `CONTENT_LENGTH` deleted from `META`; the at-vs-over pair pins `>` not `>=`.
- `::test_a_disabled_cap_skips_the_check_entirely` — `_body` never materialized when disabled.
- `::test_a_misconfigured_mount_fails_loud_on_every_request_including_get` — 2 params; pins that
  resolve/validate precedes the GET no-op.
- `::test_the_body_limit_mixin_stays_private_and_sits_first_in_both_base_lists` — not in `__all__`,
  exact `__bases__` on both views, mixin ahead of upstream in the MRO. The existing exact-`__all__`
  test is untouched.

**Package tier — `tests/base/test_conf.py`** (no new test): the `MAX_REQUEST_BODY_BYTES: 4096`
override plus `max_request_body_bytes_setting() == 1_048_576` after the `del`, inside
`::test_delattr_clears_stale_cache_and_restores_defaults`.

**Live tier — `examples/fakeshop/test_query/test_transport_api.py`** (+17 collected; file 11 -> 28):

- `::test_a_declared_body_is_capped_at_the_configured_limit` — row 13/14, 4 params over `cap-tiny/`
  with **byte-exact** bodies: `cap-32` and exactly `cap` -> `200` with data; `cap+1` and `cap*4` ->
  `413`. The `at` / `one-byte-above` pair is what pins `>` rather than `>=`.
- `::test_on_wsgi_a_missing_or_understated_content_length_shrinks_the_body_it_cannot_grow_it` —
  row 13 WSGI colour, 2 params. The honest outcome: `LimitedStream` truncates, so the app receives
  0 bytes (absent) or 10 (understated) and answers upstream's malformed-JSON `400`, explicitly
  **not** our reason. There is nothing for the counted check to catch on WSGI, which is exactly
  Decision 7 step 2's own claim.
- `::test_on_asgi_an_absent_or_lying_content_length_cannot_buy_a_larger_body` — row 13 ASGI colour,
  2 params through `_asgi_post`: no `Content-Length` at all, and `content-length: 10` against a
  4x-oversized body. Both `413` + exact reason. This is the row the counted check exists for.
- `::test_a_body_arriving_in_several_asgi_fragments_is_capped_on_the_cumulative_total` — row 13's
  *cumulative* word: three fragments each `< cap` summing `> cap` -> `413`, **plus** the identical
  three-fragment shape summing under -> `200` with data. The fragment arithmetic is asserted before
  the requests so drift cannot silently weaken it.
- `::test_malformed_json_over_the_cap_gets_413_and_under_it_still_gets_400` — row 14, the same
  malformed bytes on both sides of the cap. The `400`'s exact upstream message under the cap is an
  independent parse witness (a parse message can only come from a parse that ran).
- `::test_a_multipart_request_over_the_declared_cap_is_refused` — row 14 multipart via the declared
  gate. The un-broken direction is `test_uploads_api.py` passing unchanged (run, see below).
- `::test_an_over_cap_mutation_is_rejected_before_any_parse_or_schema_execution` — row 15. A
  **valid** padded `createCategory` -> `413` + exact reason + `_PARSE_CALLS == []` + the row absent;
  **then the mandatory control in the same test**: the same mutation under the cap -> `200`, exactly
  one recorded `parse_json` whose payload contains the name, and the row present.
- `::test_the_two_body_ceilings_are_distinguishable_by_the_response_they_produce` — row 16 both
  directions. Package: `413` + our reason. Django: `DATA_UPLOAD_MAX_MEMORY_SIZE=64` against the
  8 MiB mount -> **`400`**, not `413`, with the docstring recording why the spec's prediction is
  inaccurate. WSGI-only, per finding 2.
- `::test_the_view_kwarg_beats_the_setting_on_a_real_request`,
  `::test_the_setting_beats_the_default_on_a_real_request`,
  `::test_a_none_setting_disables_the_package_cap_that_the_default_would_apply` — row 17's three
  rungs. The last posts a 1 MiB + 64 body twice (key absent -> `413`; key `None` -> `200`), the only
  way "disabled" is demonstrable against a body the default rejects.
- `::test_the_async_package_view_enforces_the_same_body_cap` — the `async def run` colour, over /
  under, DB-free.

### Validation run

1. `uv run ruff format .` — **pass** (`400 files left unchanged`; a prior `--check` dry run
   confirmed zero repo-wide churn before the write run, so no concurrent file was reformatted).
2. `uv run ruff check --fix .` — **pass** (`All checks passed!`, no fixes applied).
3. `uv run python scripts/check_trailing_commas.py django_strawberry_framework/views.py
   django_strawberry_framework/conf.py tests/test_views.py tests/base/test_conf.py
   examples/fakeshop/test_query/test_transport_api.py` — **pass**, `1 file reformatted`
   (`test_transport_api.py`; sub-threshold collapse). Re-run with `--check` on the same explicit
   paths: exit 0. Explicit paths only — the repo-wide auto-fix default would have rewritten the
   maintainer's untracked `drys.md` / `vulns.md`.
4. `git status --short` — every entry classified, **nothing reverted**:
   - *Slice-2 intended:* `django_strawberry_framework/conf.py`, `tests/base/test_conf.py` (both
     `M`); `django_strawberry_framework/views.py`, `tests/test_views.py`,
     `examples/fakeshop/test_query/test_transport_api.py` (all `??`, created by Slice 1);
     `docs/builder/bld-slice-2-body_cap.md` (`??`, this artifact).
   - *Slice-1 intended, still uncommitted:* `django_strawberry_framework/routers.py`,
     `examples/fakeshop/config/urls.py`, `tests/test_routers.py`, `tests/auth/test_mutations.py`,
     `docs/builder/bld-slice-1-protocol_split.md`,
     `docs/builder/build-046-transport_security-0_0_15.md`.
   - *Baseline-dirty / concurrent, untouched:* `django_strawberry_framework/filters/sets.py`,
     `tests/filters/test_sets.py`, `docs/feedback.md`,
     `docs/row-preserving-predicates-part1-plan.md`, `docs/GLOSSARY.md`,
     `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `drys.md`, `vulns.md`,
     `docs/spec-046-transport_security-0_0_15.md` + `-terms.csv`.
   - *Tool churn:* **none.** No `git checkout --` was run.
5. Focused scope (the plan's, no `--cov*` anywhere):
   `uv run pytest tests/test_views.py tests/base/test_conf.py
   examples/fakeshop/test_query/test_transport_api.py examples/fakeshop/test_query/test_uploads_api.py
   examples/fakeshop/test_query/test_client_api.py --no-cov` -> **129 passed**. The uploads file is
   in scope on purpose: it is the un-broken-`Upload`-path half of row 14's multipart contract, and
   it passes unchanged against fakeshop's default mount, which now carries the 1 MiB default.
6. **Canonical full sweep:** `uv run pytest --no-cov` -> **4849 passed, 40 skipped** in 60s.
   Slice 1 ended at 4801 / 40, so the delta is **+48 passed, 0 failed, skips unchanged** — exactly
   the 31 + 17 rows added above. The known invocation-shape trap (`test_kanban_api.py` +
   ~5 `examples/fakeshop/tests/` rows failing under narrowed invocations) did not appear here, as
   expected under the full sweep.
7. **Failability of the re-aimed `channels` assertion, proven both directions** (not asserted from
   reasoning):
   - *Still catches a `channels`-reaching import.* Backed up `views.py` and recorded
     `shasum -a 256`; injected `import channels` above the `cross_web` import;
     `uv run pytest tests/test_views.py::test_views_module_imports_with_channels_absent` ->
     **FAILED**, `ModuleNotFoundError: import of channels halted; None in sys.modules` at
     `views.py:51`. Restored from the backup, `shasum -a 256 -c` -> `OK`, test **passed** again. No
     `git stash` was used (concurrent writers).
   - *The identity half is not vacuous.* With the module cache intact (no eviction),
     `importlib.import_module("strawberry.django.views").GraphQLView is not GraphQLView` is
     **False** — so `assert fresh is not captured` genuinely distinguishes a re-executed upstream
     body from a cached one. The same probe printed `DjangoGraphQLView.__base__.__name__ ==
     "_RequestBodyLimitMixin"`, which is the direct evidence that the OLD `__base__` assertion had
     become self-comparing.
8. **Floor parity (Test-plan row 18)** — isolated `/tmp/dsf-floor-r5` (`Django 5.2`, `python
   3.10.19`); the shared `.venv` was never mutated. Invocation shape:
   `/tmp/dsf-floor-r5/bin/python -m pytest <scope> -p no:cacheprovider -q -o addopts=""` (the
   `-o addopts=""` is required because `pytest.ini`'s `addopts` names `-n` / `--cov`, and the floor
   venv has neither plugin).
   - `tests/test_views.py tests/base/test_conf.py` -> **84 passed**.
   - `examples/fakeshop/test_query/test_transport_api.py` -> **28 passed**.
   - `examples/fakeshop/test_query/test_uploads_api.py` -> **6 passed**.
   - *Provisioning note:* the floor venv was missing `faker` and `pillow`, which the fakeshop
     seed helpers and the `scalars` app need; the first live run failed 23 rows on
     `ModuleNotFoundError: No module named 'faker'`. Fixed with
     `uv pip install --python /tmp/dsf-floor-r5/bin/python faker pillow` (isolated venv only —
     `uv pip install` ignores `UV_PROJECT_ENVIRONMENT` and would otherwise hit `.venv`). `Django
     5.2` was unchanged by the install, re-verified afterwards. Not a code failure.
   - Behaviour is **byte-identical** across the two stacks: an ad-hoc probe of every enforcement
     branch (all four validation rejections, all three precedence rungs, sync / async / ASGI `413`s,
     malformed-over vs malformed-under, the at-limit boundary, the multipart and GET no-ops, the
     ASGI fragment and understated-`Content-Length` shapes) produced identical output on
     `Django 6.0.5 / py3.14.2` and `Django 5.2 / py3.10.19`.
9. **TODO-anchor sweep:** `grep -rn "TODO(spec-046" --include='*.py' --include='*.md' .` returns no
   hit in shipped source or tests — only the spec's generic staging-discipline sentence and the
   per-cycle `bld-*.md` narrative. `grep -rn "TODO("` across all five touched files: no match.

### Implementation notes

One bullet per decision the plan did not pin (the eight discretion items plus what implementation
surfaced). Decisions the plan fixed are not restated.

- **The `1_048_576` default is an inline literal in `conf.py`'s accessor** (discretion 1), matching
  the five shipped accessors exactly rather than introducing a named constant. It appears once in
  production code; `views.py` only knows "`None` means ask `conf.py`", and
  `::test_no_kwarg_and_no_setting_resolves_to_the_one_megabyte_default` pins that from the
  key-absent direction so a duplicated literal could not satisfy it.
- **Kept every private name the plan proposed** (discretion 2) and added one more:
  `_MULTIPART_CONTENT_TYPE`. `"multipart/form-data"` would otherwise be a bare literal at the
  single most security-relevant branch in the module, and the constant's comment is where the "bare
  media type, `boundary=...` split off into `content_params`" fact belongs — that is *why* `==` is
  correct instead of `startswith`.
- **`ConfigurationError` wording** (discretion 3): `"max_request_body_bytes must be a positive int
  of bytes or None to disable the package request-body cap; got {type} {value!r}."` It names the
  received type, the received value, and `None`. The tests match on `"None to disable.*got
  {type}"`, so the two load-bearing halves cannot drift out.
- **Four probe mounts, built by one factory** (discretion 4): `cap-tiny/` at 256, `cap-spy/`,
  `cap-off/` at 8 MiB, and `async-cap-tiny/`. `_capped_view(view_class, limit)` is a factory rather
  than three near-copies. The async mount is spelled out as a plain `async def` instead of being
  produced by the factory — the `await` is the whole difference, only one mount needs it, and that
  mirrors the file's existing `_ide_off_view` / `_async_graphql_view` pair.
- **`_TINY_CAP = 256` is deliberately small** so only ONE row in the whole slice needs a
  megabyte-scale payload (the `None`-disables row, where nothing smaller can demonstrate the
  default being bypassed). Everything else runs on hand-sized bodies.
- **`_sized_body(size)` produces byte-EXACT bodies** rather than "roughly N bytes", which is what
  makes the `at` / `one-byte-above` pair a real boundary test instead of a straddle. It pads an
  inert top-level `"pad"` member with `"y"` (no JSON escaping, so one char is one byte) and asserts
  its own arithmetic before returning.
- **Row 13's trio is one parametrized test, row 17's three rungs are three tests** (discretion 5).
  The trio shares one body-shape and differs only in size, so parametrizing reads better; the row-17
  rungs each need a different `override_settings` block and a different pair of mounts, so
  parametrizing them would have produced a table of unrelated set-ups.
- **`_asgi_post` returns a plain `(status, headers, body)` tuple and lives beside the other helpers**
  (discretion 6), above the rows that use it. A dataclass would have bought nothing at three call
  sites.
- **The ASGI driver mints and echoes a real CSRF token** — implementation-surfaced, and the one
  thing the plan's probe did not predict. The real `ASGIHandler` runs the real middleware chain, so
  `CsrfViewMiddleware` enforces for real (unlike `django.test.Client`) and the first run of all
  three ASGI rows returned `403 CSRF cookie not set`. Rather than exempt the mount, the driver mints
  a token with the public `django.middleware.csrf.get_token` and sends it as both the `csrftoken`
  cookie and the `X-CSRFToken` header — exactly the round trip a browser (and Strawberry's own
  GraphiQL) makes. That is strictly stronger than an exemption: these rows pass Django's CSRF check
  legitimately, so a `413` they report is unambiguously the view's.
- **Row 14's multipart uses a plain oversized multipart POST, not `createMediaSpecimen`**
  (discretion 8). The row's subject is the declared-size gate refusing before any parse, so a
  request that never needs to succeed is the more honest shape; the mutation-succeeds direction is
  already `test_uploads_api.py`'s, which was run and reported above.
- **`_post` was refactored to delegate to the new `_post_bytes`** rather than having the raw-body
  rows duplicate its `client.post(..., content_type="application/json")` call. Behaviour is
  unchanged for every existing S1 row.
- **The parse spy is a subclass, not a monkeypatch.** `parse_json` lives on
  `strawberry.http.base.BaseView` and is already class-patched by the package's own
  `_strawberry_patches`; patching it again in a test would have recorded every other suite's posts
  too and fought the shipped patch. The subclass scopes the recorder to one mount and still
  delegates through `super()`, so the under-cap control exercises the real hardened path.
- **`_capped_view` in `tests/test_views.py` constructs the instance with both keywords**
  (`view_class(schema=..., max_request_body_bytes=...)`) rather than assigning the attribute
  afterwards. `as_view`
  instantiates via `cls(**initkwargs)` and Django's `View.__init__` `setattr`s each keyword, so this
  is the same instance shape a real mount produces. (First attempt used a bare `view_class()` and
  failed on upstream's required `schema` argument.)
- **The module docstring's `channels`-free paragraph was widened, not left alone.** It previously
  said "the single module it imports"; three imports were added (`cross_web`, `conf`, `exceptions`),
  so the sentence would have become false. It now enumerates all of them and states why each is
  `channels`-free — `cross_web` is inside the same existing hard `strawberry-graphql` chain, and
  `conf` / `exceptions` reach only `django.conf` / `django.test.signals` and the standard library
  (verified by reading both import blocks).
- **`_declared_content_length` carries a `# type: ignore[arg-type]`** on `int(request.META.get(...))`
  because passing a possibly-`None` value to `int()` is the *point* of the construct — the
  `TypeError` branch is the absent case. Suppressing at the call site is narrower than widening the
  helper's signature.

### Notes for Worker 3

- **No shadow file was used or re-generated.** The plan's two `review_inspect.py` overviews were
  read as part of the plan; implementation needed nothing beyond the live source.
- **`views.py` grew ~150 lines of new logic**, so BUILD.md's "30 or more lines of new logic to any
  file under `django_strawberry_framework/`" threshold puts `scripts/review_inspect.py` on your
  must-run list for both `views.py` and `conf.py`.
- **Control flow worth reading in order:** `_enforce_request_body_limit` has five steps and the
  ORDER is a contract (resolve/validate -> GET no-op -> declared gate -> multipart return -> counted
  check). Each step has a package-tier row naming it. In particular the resolve is FIRST so a
  misconfigured mount fails on GET too, which
  `::test_a_misconfigured_mount_fails_loud_on_every_request_including_get` pins.
- **The re-aimed `channels` assertion is the one existing test whose assertions changed.** It was
  strengthened, not relaxed — both failability directions are proven in `### Validation run` step 7.
  Please re-derive rather than take my word for it: `__base__` is now the package's own mixin, so
  the previous form was self-comparing.
- **Two witnesses look negative and are not.** Every `hasattr(request, "_body") is False` assertion
  and the `_PARSE_CALLS == []` assertion is paired with a positive control in the SAME test. If you
  re-derive any of them, keep the control — dropping it makes the row vacuous.
- **Do not lower `DATA_UPLOAD_MAX_MEMORY_SIZE` in any row that uses `_asgi_post`.** That is the
  single cell where Django 6.0 (`400`, seekable actual-size check present) and the Django 5.2 floor
  (`200`, no such check) diverge. Every ASGI row leaves Django's knob alone on purpose; row 16's
  Django direction is WSGI-only for the same reason.
- **`_asgi_post`'s `receive` must not return `http.disconnect`.** After the queued fragments it
  awaits something that never resolves and lets `ASGIHandler.handle` cancel its
  `listen_for_disconnect` task; returning a disconnect aborts the request before the view answers.
  The `raise AssertionError` after that await is unreachable and marked `# pragma: no cover` —
  example-tree code, outside the coverage gate, but flagged here so it does not read as dead code.
- **Temp tests:** none created; nothing under `docs/builder/temp-tests/slice-2/`. The ad-hoc probe
  scripts live only in the session scratchpad.

### Notes for Worker 1 (spec reconciliation)

No structural drift from the plan: the hook is `run` on both classes, the keyword is a class
attribute on a mixin placed first, the check order and `>` comparison are as specified, the reason
string is verbatim, the settings key is the only one added, and the `TODO` anchor is gone.

1. **Checklist box 3 (Decision 8) left `- [ ]` deliberately — this is a recorded split, not a silent
   deferral.** What landed in this diff is the **code-documentation layer** the plan's step 4
   assigns to Slice 2: `conf.py`'s `MAX_REQUEST_BODY_BYTES_KEY` comment states the deployment-layer
   cap is *required alongside* this one, and `_RequestBodyLimitMixin`'s docstring carries the full
   honest boundary (`ASGIHandler.read_body` has already spooled the request; the cap bounds what the
   application *processes*, never what the server *accepts*; a proxy / ASGI-server cap is a
   co-requirement, not an alternative). What has **not** landed is the consumer-facing prose the box
   is most naturally read as requiring — `docs/README.md`'s concrete directives
   (`client_max_body_size`, the ASGI-server flags, the Daphne request-buffer note) — which
   Decision 8 itself assigns to Slice 5 and which I am forbidden to write here. Your call whether
   the code layer discharges the box now or it stays open until Slice 5.
2. **Confirmed both of the plan's Django findings by execution on both stacks.** Django's own
   ceiling answers **`400`, not `413`**, on both transports and both versions
   (`RequestDataTooBig` is raised lazily from `HttpRequest.body`, inside the view, where
   `response_for_exception` maps `SuspiciousOperation` to `400`), and the Django 5.2 floor's
   `HttpRequest.body` has **no** seekable actual-size check (read from the floor venv's own source:
   the whole check is a `DATA_UPLOAD_MAX_MEMORY_SIZE is not None and int(CONTENT_LENGTH or 0) >
   ...` conditional, with no `_stream.seekable()` branch). The tests pin the measured behaviour and
   record the discrepancy in
   `::test_the_two_body_ceilings_are_distinguishable_by_the_response_they_produce`'s docstring. The
   spec's two inaccurate sentences (Current state's Django-body bullet, and the Edge case
   "ASGI converts it to its own `413`") are yours to correct or leave.
3. **New finding, not in the plan: a garbage `CONTENT_LENGTH` makes Django's own `request.body`
   raise `ValueError`.** `HttpRequest.body` evaluates `int(self.META.get("CONTENT_LENGTH") or 0)`
   unguarded — line 391 on Django 6.0.5, inside the `DATA_UPLOAD_MAX_MEMORY_SIZE is not None`
   conditional on the 5.2 floor. So on a request declaring `Content-Length: not-a-number`, the
   package's counted check cannot complete: Django raises first, and the response is a `500` rather
   than our `413`. The package's own behaviour is still the fail-safe one the plan specified
   (`_declared_content_length` returns `None` for garbage, i.e. it never *trusts* an unparseable
   declaration), and the failure happens before any parse or execution, so the security property
   holds. But the plan's package-tier row (d) "an unparseable `CONTENT_LENGTH` falls through to the
   counted check" is only *half* testable: I pinned the pure-function half
   (`::test_the_declared_length_reader_is_none_for_every_unmeasurable_shape`, garbage -> `None`) and
   the counted-check half through the **absent**-declaration shape rather than the garbage one
   (`::test_the_counted_check_fires_when_no_content_length_is_declared_at_all`). Asserting a `413`
   for the garbage case would have pinned Django's `ValueError` as though it were ours. Flagging
   rather than working around it: a real WSGI/ASGI server would normally reject such a header before
   Django sees it, and papering over Django's `int()` in the package would mean pre-reading or
   rewriting `META`, both of which Decision 7 rejects by name.
4. **The plan's floor-venv assumption needed one repair.** `/tmp/dsf-floor-r5` existed with the
   right Django and Python but lacked `faker` and `pillow`, so the live tier could not run there at
   all until I installed them into that isolated venv. Worth carrying into Slices 3-5, which will
   want the same floor runs.
5. **`APPEND_SLASH` / `DEBUG` trap re-confirmed as still in force**: nothing in this slice overrides
   `DEBUG`, and all the new rows post to trailing-slash paths, so Slice 1's row-6 constraint is
   untouched.

---

## Review (Worker 3)

Diff obtained independently (`git status --short`, `git diff`, `git diff --stat`), not from
the report's inventory. `views.py`, `tests/test_views.py`, and
`examples/fakeshop/test_query/test_transport_api.py` are `??` (Slice 1 created them,
uncommitted), so they have no git baseline and were read in full; `conf.py` and
`tests/base/test_conf.py` were read as diffs. The inventory is accurate and complete: no
sixth file carries slice content. Every other dirty entry matches
`build-046-transport_security-0_0_15.md`'s baseline-dirty list and was neither read as
in-scope nor touched.

**Static inspection helper — run, as required** (logic added to two files under
`django_strawberry_framework/`):

- `uv run python scripts/review_inspect.py django_strawberry_framework/views.py --output-dir docs/shadow`
  -> `docs/shadow/django_strawberry_framework__views.{stripped.py,overview.md}`. 7 imports,
  8 symbols, 0 control-flow hotspots, 0 Django/ORM markers, 3 calls of interest
  (2x `isinstance`, 1x `len`), **0 TODO comments**, **0 repeated string literals**.
- `uv run python scripts/review_inspect.py django_strawberry_framework/conf.py --output-dir docs/shadow`
  -> same pair for `conf.py`. 5 imports, 14 symbols, 2 hotspots
  (`Settings.user_settings`, `upstream_patches_enabled` - both untouched by this slice),
  0 TODOs, **0 repeated string literals**.
- Shadow line numbers are not canonical; every citation below is symbol-qualified.

### High:

None. No correctness bug, no spec-contract violation, no unauthorized surface change, no
security regression, and no crashed consumer path. Decision 7's four steps, Decision 8's
code-documentation layer, and Decision 6's seam all land as written; evidence under
`### What looks solid`.

### Medium:

None.

### Low:

#### L1 - `_RequestBodyLimitMixin`'s docstring gives a non-operative reason for the mixin-first base order

`django_strawberry_framework/views.py::_RequestBodyLimitMixin` #"Sits first in each view's
bases so ``max_request_body_bytes`` is already a class attribute by the time Django's
``View.as_view`` runs its ``hasattr`` keyword guard". The `hasattr` guard walks the whole
MRO, so the ordering is not what satisfies it. Measured, not inferred - a mixin-**last**
subclass admits the keyword identically:

```text
class MixinLast(GraphQLView, _RequestBodyLimitMixin): pass
hasattr on mixin-LAST                -> True
mixin-LAST as_view(max_request_body_bytes=64) -> {'schema': ..., 'max_request_body_bytes': 64}
```

The operative reason is the one `tests/test_views.py::test_the_body_limit_mixin_stays_private_and_sits_first_in_both_base_lists`'s
docstring already gives correctly - the mixin's attribute and shared method must win over
anything upstream may later define under the same names - plus the "consumer subclass can
override either half" clause, which is true of either order. Prose only, not load-bearing;
the *choice* of first position is correct and defensive. **Recommended change:** re-word the
first paragraph to the precedence rationale and drop the `hasattr`-causality claim (keep the
`hasattr` fact on the class-attribute comment below it, where it *is* the operative point).
No test change. **Recorded reason for not blocking:** non-load-bearing rationale prose in a
private class; routed to Worker 1's final verification, which already owns a wording pass
(the same routing Slice 1's three stale `auth/` strings took, still tracked below).

#### L2 - `conf.py`'s settings-key comment states the counted bound with no multipart carve-out

`django_strawberry_framework/conf.py` #"The bound is on bytes the application actually
RECEIVED, not on the client's ``Content-Length``". For a multipart request that is not true:
`_RequestBodyLimitMixin._enforce_request_body_limit` returns at the
`_MULTIPART_CONTENT_TYPE` branch and the bound is the **declaration alone** plus Django's
`MultiPartParser`. The mixin docstring carries that nuance in full and correctly; the
settings comment - which is the surface a consumer configuring `MAX_REQUEST_BODY_BYTES`
reads - omits it entirely, so the key's comment overstates what the key bounds for the one
content type where the difference matters most. **Recommended change:** one clause pointing
at the multipart carve-out (or at `_RequestBodyLimitMixin` for it). **Test expectation:**
none; behavior is already correct and pinned by
`tests/test_views.py::test_a_multipart_request_under_the_declared_gate_is_never_materialized`
and `test_transport_api.py::test_a_multipart_request_over_the_declared_cap_is_refused`.
**Recorded reason for not blocking:** docstring/comment accuracy, not behavior; routed to
Worker 1 with the additional obligation that Slice 5's `docs/README.md` deployment guidance
carry the carve-out too (a consumer reading only the proxy-cap paragraph would otherwise
believe multipart is byte-counted).

#### L3 - one redundant assertion in the new mixin-privacy test

`tests/test_views.py::test_the_body_limit_mixin_stays_private_and_sits_first_in_both_base_lists`
#"assert mixin.__name__ not in views_module.__all__" is trivially true against the
two-element tuple and is already covered exactly - and more strongly - by
`::test_module_exports_exactly_the_two_view_classes_and_stays_off_the_package_root`'s
`views_module.__all__ == ("AsyncDjangoGraphQLView", "DjangoGraphQLView")`. Redundant, not
wrong; the test's real content (the exact `__bases__` pair on both views plus the MRO index
comparison) is load-bearing and correct. **Recommended change:** drop the first assertion, or
leave it and accept the redundancy. **Recorded reason for not blocking:** zero behavioral
risk; noted so a future slice does not mistake it for the privacy proof and weaken the exact
`__all__` test on the assumption this one covers it.

### DRY findings

- **DRY-1 (live duplication, deferred follow-up).** A **byte-identical** 7-line
  permission-granting block, comment included, appears twice in
  `examples/fakeshop/test_query/test_transport_api.py` - in
  `::test_csrf_is_enforced_on_a_cookie_authenticated_graphql_mutation` (Slice 1) and
  `::test_an_over_cap_mutation_is_rejected_before_any_parse_or_schema_execution` (Slice 2).
  Verified mechanically (`src.count(block) == 2`), not eyeballed:

  ```python
      from django.contrib.auth.models import Permission

      create_users(1)
      user_model = get_user_model()
      user = user_model.objects.get(username="view_category_1")
      user.user_permissions.add(
          Permission.objects.get(codename="add_category", content_type__app_label="products"),
      )
      user = user_model.objects.get(pk=user.pk)  # drop the stale per-request perm cache
  ```

  This is `worker-3.md`'s "near-copies across tests" category and the file's own idiom is to
  name shared scaffolding once (`_post`, `_sized_body`, `_assert_no_graphql_envelope`).
  **Recommended shape:** one module-local `_user_who_can_add_categories()` returning the
  refreshed user - the most readable reusable shape, not an abstraction. **Deferred, with
  reason** (permitted by `worker-3.md`'s acceptance gate #"DRY findings have all been
  addressed or recorded as a deferred follow-up Worker 1 will weigh during final
  verification"): extracting it now edits a Slice-1-accepted test for no behavioral gain,
  and Slices 3-5 each add live rows to this same file that will want the same actor, so one
  extraction at the integration pass is the cheaper and less churn-prone cut. Worker 1 owns
  the call.
- **DRY-2 (verified irreducible - not a finding).** The two three-line `run` overrides.
  Confirmed against upstream source, not the report's prose:
  `.venv/.../strawberry/django/views.py::GraphQLView.dispatch` and
  `::AsyncGraphQLView.dispatch` carry the identical sync/async split for the identical
  reason, and the whole decision body is single-sited in
  `_RequestBodyLimitMixin._enforce_request_body_limit`, which is **synchronous on both**
  transports because `cross_web/request/_django.py::AsyncDjangoHTTPRequestAdapter.get_body`
  is itself `async def ...: return self.request.body` (read, quoted below under
  `### What looks solid`). Nothing further is extractable without a `super()`-dispatch
  trampoline that would be less readable than the duplication.
- **DRY-3 (name collision, no shared shape available).** `_capped_view` exists in both
  `tests/test_views.py` and `examples/fakeshop/test_query/test_transport_api.py` with
  different signatures and genuinely different responsibilities (a view *instance* builder
  for direct `_enforce_request_body_limit` calls vs a request-time-resolving *URLconf view
  factory*). Different test trees, so no shared home exists and consolidating would be the
  wrong abstraction. Recorded as a readability note only; verified-and-rejected as a
  consolidation target.
- **DRY-4 (verified good).** `_post` was refactored to delegate to the new `_post_bytes`
  rather than the raw-body rows duplicating the `client.post(..., content_type=...)` call;
  `_capped_view(view_class, limit)` is one factory instead of three near-copy mounts;
  `_assert_body_limit_response` **composes** `_assert_no_graphql_envelope` instead of
  restating it; `_asgi_post` serves all three ASGI rows; `_MULTIPART_CONTENT_TYPE` and
  `_BODY_LIMIT_REASON` are named once each and the shadow report confirms **0 repeated
  string literals** in both production files.
- **DRY-5 (verified-and-rejected).** `1_048_576` appears exactly **once** in production
  (`conf.py::max_request_body_bytes_setting`); `views.py` never restates it, and
  `tests/test_views.py::test_no_kwarg_and_no_setting_resolves_to_the_one_megabyte_default`
  pins that from the **key-absent** direction so a duplicated literal in `views.py` could
  not satisfy it. The test-tier restatements are independent pins, which is correct.
  `_sized_body(_TINY_CAP * 4)` recurs across six rows but is a per-row size *decision*, not
  a shared literal; naming it would hide what each row is asserting.
- **DRY-6 (checked, no seam missed).** `grep`ed the whole tree for `__base__` / `__bases__` /
  `__mro__` readers: no production module and no test outside `tests/test_views.py`'s own new
  test depends on either view's base-list shape, so the mixin insertion breaks no other
  reader. No wire shape changed in this slice, so `worker-3.md`'s three-tree
  wire-shape sweep does not apply; the behavioral change that *does* reach every tree - the
  1 MiB default now applying to fakeshop's real `/graphql/` - is covered by the green
  canonical sweep (below).

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty**; `__all__` and the
re-export list are unchanged. `views.__all__` is still exactly
`("AsyncDjangoGraphQLView", "DjangoGraphQLView")`; `_RequestBodyLimitMixin`,
`_resolved_max_request_body_bytes`, `_declared_content_length`, `_BODY_LIMIT_REASON`, and
`_MULTIPART_CONTENT_TYPE` are all private and unexported.

Per `build-046-transport_security-0_0_15.md` #"Worker 3's public-surface check must measure
the diff against **spec Decision 5**": Slice 2 breaks nothing. Both additions are strictly
additive - one optional `as_view(max_request_body_bytes=...)` keyword defaulting to `None`
(defer), and one settings key defaulting to `1_048_576`. Verified by probe that upstream's
own keyword surface is untouched:

```text
DjangoGraphQLView.as_view(schema, graphql_ide, allow_queries_via_get,
                          multipart_uploads_enabled, max_request_body_bytes)
  -> combined initkwargs keys ['allow_queries_via_get', 'graphql_ide',
     'max_request_body_bytes', 'multipart_uploads_enabled', 'schema']    (both classes)
mixin surface: ['_enforce_request_body_limit', 'max_request_body_bytes']
GraphQLView MRO collisions:      set()
AsyncGraphQLView MRO collisions: set()
```

The one settings key is exactly one:
`git diff -- conf.py | grep '^+.*_KEY = '` returns a single line,
`MAX_REQUEST_BODY_BYTES_KEY = "MAX_REQUEST_BODY_BYTES"` - satisfying the spec's
#"it is the only settings key this card adds".

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

- **No version-quintet movement.** `git diff -- pyproject.toml
  django_strawberry_framework/__init__.py CHANGELOG.md` is empty, and `git status --short`
  lists none of them. `tests/base/test_init.py` untouched.
- **No `CHANGELOG.md` edit** (Decision 15 / the joint cut, plus the permission this card
  does not hold).
- **No Slice-5-owned prose surface edited.** `git status --short --` on `README.md`,
  `TODAY.md`, `docs/README.md`, `docs/TREE.md`, `examples/fakeshop/test_query/README.md`
  returns nothing.
- **`docs/GLOSSARY.md` dirt is baseline, verified semantically, not by filename.** Its diff
  is a single rewritten paragraph of the row-preserving-predicates FilterSet entry;
  `git diff -- docs/GLOSSARY.md | grep -i "body\|413\|MAX_REQUEST"` returns **zero** hits,
  so no body-cap term leaked in. `KANBAN.md` / `KANBAN.html` /
  `examples/fakeshop/db.sqlite3` likewise carry only the concurrent + card-authoring state
  named in the build plan. Nothing was touched or reverted.
- **`TODO(spec-046 Slice 2)` anchor is gone with no replacement.**
  `grep -rn "TODO(spec-046" --include='*.py' .` -> no hit anywhere in shipped source or
  tests; `grep -n "TODO(" ` across all five touched files -> no match; the shadow overview
  independently reports **TODO comments: none** for `views.py` (the plan's own scan had
  found 1 there before the edit). `AGENTS.md` #"removed in the same change that ships the
  slice" satisfied.
- **Hygiene re-run by me, not relayed.** `ruff format --check` -> `5 files already
  formatted`; `ruff check` -> `All checks passed!`;
  `scripts/check_trailing_commas.py --check <5 explicit paths>` -> exit 0 (explicit paths
  only, so the maintainer's untracked `drys.md` / `vulns.md` were never in range);
  ASCII-only confirmed byte-wise (`0` non-ASCII bytes in each of the five files).

### What looks solid

- **The check is genuinely before parse and before execution, and the `413` is genuinely
  upstream's.** Read at source, both halves: `.venv/.../strawberry/django/views.py`
  `GraphQLView.dispatch` (line 150) and `AsyncGraphQLView.dispatch` (line 210) each contain
  *only* `try: return [await] self.run(request=request)` / `except HTTPException as e:
  return HttpResponse(content=e.reason, status=e.status_code,
  content_type="text/plain")`. The package overrides `run`, i.e. **inside** that `try`, so
  the `413` `text/plain` body is produced by upstream's four lines with **zero** duplicated
  translation - the same seam `_strawberry_patches.py::_patched_parse_json`'s `400`s already
  ride. Both flavors land there; both are pinned live (`_assert_body_limit_response` asserts
  status + `text/plain` + the exact reason bytes, and
  `::test_the_async_package_view_enforces_the_same_body_cap` carries the `async def run`
  colour). Nothing before `run` parses: upstream's `dispatch` calls nothing else, and
  `parse_json` is reached only via `run` -> `execute_operation` -> `parse_http_body`.
- **The row-15 parse/execute proof and its control are real.**
  `::test_an_over_cap_mutation_is_rejected_before_any_parse_or_schema_execution` posts a
  *valid* padded `createCategory` at `/cap-spy/` -> `413` + `_PARSE_CALLS == []` + no
  `Category` row; then, **in the same test, through the same mount and the same client**,
  the same mutation under the cap -> `200`, `len(_PARSE_CALLS) == 1`, the recorded payload
  contains the name, and the row exists. The spy demonstrably records, and the DB
  demonstrably writes, so both empty witnesses are evidence rather than decoration. The spy
  is a subclass delegating through `super()`, so the under-cap control exercises the real
  hardened `_patched_parse_json` path rather than a bypass. Same discipline holds for every
  `hasattr(request, "_body") is False` row - each has its positive control in-test
  (`::test_a_declared_over_limit_request_is_refused_without_reading_the_body` shows `_body`
  DOES appear once the counted check must run).
- **The mixin-first MRO change is safe, and I verified it rather than reading the claim.**
  Live MRO: `DjangoGraphQLView -> _RequestBodyLimitMixin -> GraphQLView -> BaseView ->
  SyncBaseHTTPView -> ABC -> BaseView -> Generic -> View -> object` (async twin identical
  with `AsyncGraphQLView` / `AsyncBaseHTTPView`). The mixin's entire surface is
  `{max_request_body_bytes, _enforce_request_body_limit}` and **neither name collides with
  anything in either upstream MRO** (probe above). It defines no `__init__`, so
  `BaseView.__init__` -> `View.__init__`'s `setattr` chain is untouched:
  `as_view(max_request_body_bytes=4096)` lands in `view_initkwargs` on both classes and
  `cls(**initkwargs)` yields an instance whose attribute is `4096` with `schema` still
  bound. `view_is_async` and `http_method_names` are unchanged, and the async twin's
  `markcoroutinefunction` marking still holds (pinned by the untouched
  `::test_async_view_as_view_is_marked_as_a_coroutine_function`).
- **The re-aimed `channels` assertion is strictly stronger, proven both ways by me.** See
  `### Temp test verification` for the mechanical proof; the summary is that under an
  upstream-cached condition the *new* comparison goes `False` (so the shipped test would
  fail) while Slice 1's `__base__` comparison still passes - the definition of strictly
  stronger. Nothing from Slice 1's version was dropped: the preconditions
  (`sys.modules["channels"] is None`, both module bodies out of the cache,
  `"strawberry.channels" not in sys.modules` after import) and
  `module.DjangoGraphQLView is not DjangoGraphQLView` all survive, and the async colour and
  the two `__mro__` membership assertions are net additions.
- **No test pins Django's behavior as the package's.** Every row that lands on a
  Django-owned outcome says so in its own docstring and asserts the *discrimination*, which
  is precisely what Test-plan row 16 requires ("the tests assert which one fired"):
  `::test_the_two_body_ceilings_are_distinguishable_by_the_response_they_produce` asserts
  Django's `400` **and** `content != _BODY_LIMIT_REASON` **and** records in prose that the
  spec's `413` prediction is inaccurate;
  `::test_on_wsgi_a_missing_or_understated_content_length_shrinks_the_body_it_cannot_grow_it`
  asserts the honest `400`-from-truncation and explicitly **not** our reason. The only exact
  message pinned anywhere (`b"Unable to parse request body as JSON"`) is the *package's* own
  `_patched_parse_json` string, not Django's. Worker 2's decision to pin the
  garbage-`CONTENT_LENGTH` case only at the pure-function rung is the right one - see
  `### Temp test verification`, where I confirmed the raise is Django's and is **not** a
  regression this slice introduces.
- **Honesty of the guarantee holds throughout.** Grepped for over-claiming
  (`prevent.*receiv`, `stop.*bytes`, `never received`, `mid-stream`, `bandwidth`): the only
  two hits are the *negations* -
  `views.py::_RequestBodyLimitMixin` #"What it cannot guarantee is that the bytes were never
  received: ``django.core.handlers.asgi.ASGIHandler.read_body`` has already drained the
  entire request into a spooled temporary file" and #"this cap bounds what the application
  *processes*, never what the server *accepts*", plus `conf.py` #"no application-level
  ceiling can stop the bytes from being received". No test name or docstring claims
  otherwise. Both Django facts Worker 1 probed are re-verified by me at source: Django
  6.0.5's `HttpRequest.body` maps its own ceiling through lazily-raised
  `RequestDataTooBig` -> `SuspiciousOperation` -> `400`, and the **floor's** `body` (read out
  of `/tmp/dsf-floor-r5`, quoted) has *no* `_stream.seekable()` branch at all - only the
  declared check, itself gated on `DATA_UPLOAD_MAX_MEMORY_SIZE is not None`. So at the floor
  the package's counted check really is the only application-level bound, which is the
  strongest available argument for Decision 7's "counted, not declared".
- **Multipart is handled per spec and `Upload` is demonstrably unbroken.** The branch is
  `request.content_type == _MULTIPART_CONTENT_TYPE`, which is **byte-identical to Django's
  own** test (`django/http/request.py` #"if self.content_type == "multipart/form-data":"), so
  there is no divergence window between what the package treats as multipart and what Django
  parses as multipart. Ordering matters and is right: `CsrfViewMiddleware` reads
  `request.POST` on every POST, which for multipart sets `_read_started` without caching
  `_body` - so a `len(request.body)` there would raise `RawPostDataException`. The
  multipart early-return is what avoids it, and
  `::test_a_multipart_request_under_the_declared_gate_is_never_materialized` witnesses
  `_body` absent **before and after** `MultiPartParser` produces `POST`.
  `examples/fakeshop/test_query/test_uploads_api.py`'s 6 rows - including two real
  multipart `SimpleUploadedFile` mutations - pass unchanged against fakeshop's default mount,
  which now carries the 1 MiB default (`34 passed` together with the transport file on the
  floor, and green in the canonical sweep).
- **`_asgi_post`'s CSRF decision is genuinely stronger than an exemption, and masks
  nothing.** It mints a token with the public `django.middleware.csrf.get_token` and sends
  it as both the `csrftoken` cookie and the `X-CSRFToken` header, so `CsrfViewMiddleware`
  unmasks one secret from each side and passes *legitimately*. Two consequences I checked:
  (a) a `413` from these rows is unambiguously the view's, because the request cleared the
  real middleware chain first - an exempted mount would have left "did CSRF or the cap
  answer?" undecidable; (b) Slice 1's CSRF matrix is untouched and still meaningful - it
  runs on a different mount with `Client(enforce_csrf_checks=True)` and a real
  cookie round-trip, and asserts DB side effects in both directions, none of which this
  helper touches. The token mint works because fakeshop sets no `CSRF_USE_SESSIONS`
  (checked). It is the one implementation-surfaced decision in the slice and it was the
  right one.
- **The ASGI rows are correctly DB-free and correctly leave Django's knob alone.** Both
  `_asgi_post` rows post `{ __typename }`, carry no `django_db` marker, and never evaluate
  `request.user` (lazy) - so no ORM access happens off the event loop and no sqlite
  connection is opened in the driver thread, which is the executor-thread teardown hazard
  this repo has hit before. `ASGIHandler()` is constructed **inside** the
  `override_settings` block, so `load_middleware(is_async=True)` reads the overridden
  `ROOT_URLCONF`/`MIDDLEWARE`. And no ASGI row lowers `DATA_UPLOAD_MAX_MEMORY_SIZE` - the
  single cell where 6.0 and the 5.2 floor diverge - with row 16's Django direction kept
  WSGI-only for the same reason. That constraint is honored, and it is why the floor run is
  bit-identical rather than merely green.
- **Branch-by-branch reading finds no uncovered contract** (reading exercise, no `--cov`).
  `_resolved_max_request_body_bytes`: kwarg-present / kwarg-`None`+setting / both-`None`
  (default, asserted from the key-**absent** direction) / setting-`None` (disable) / each of
  six invalid shapes on **both** rungs / the success return - all claimed by a named row.
  `_declared_content_length`: parseable / absent (`TypeError`) / garbage (`ValueError`) /
  empty string. `_enforce_request_body_limit`: disabled-return, GET no-op,
  declared-over-raise, declared-`None` fall-through, declared-under fall-through,
  multipart-return, counted-over-raise, counted-under fall-through - each with a row, and
  the *order* (resolve/validate first) is pinned by
  `::test_a_misconfigured_mount_fails_loud_on_every_request_including_get`, which is the only
  way to prove the resolve precedes the GET short-circuit. Both `run` overrides: raise and
  delegate, live, on both flavors. `conf.py::max_request_body_bytes_setting`: override and
  post-`del` default, in the `tests/base/test_conf.py` enumeration.
- **`tests/base/test_conf.py` row is correct and the docstring closes the drift.** The
  `MAX_REQUEST_BODY_BYTES: 4096` override, the `== 4096` read, and the
  `== 1_048_576` post-`del` assertion sit inside
  `::test_delattr_clears_stale_cache_and_restores_defaults` (46 collected, unchanged count -
  assertions added, no new test, no new file in `tests/base/`, as `AGENTS.md` requires). The
  added sentence #"Every accessor with a default belongs in this enumeration: a key added
  without a row here leaves the sweep silently stale" is exactly the guard that would have
  prevented the omission it is fixing. Precedence itself is tested where it belongs
  (`tests/test_views.py`'s pure-function ladder, four params) rather than duplicated here,
  and the validation matrix (`0`, negative, `bool`, `str`, `float`, `object` x kwarg/setting
  = 12 rows) asserts the message names **both** the received type and `None`-as-disable, so
  neither load-bearing half of the wording can drift out silently.
- **Slice-2 checklist boxes 1, 2 and 4 are ticked with matching implementation** (no
  over-tick). Box 1: cap before parse/execute returning `413` - proven above. Box 2: exactly
  one settings key with the kwarg override and the shipped
  `NESTED_CONNECTION_STRATEGY` precedence *and* its validation-lives-in-the-resolver split.
  Box 4: rows 13-17 all earned live over fakeshop's real `/graphql/` or over a second mount
  of the same package view through the existing Probe URLconf; row 18's floor parity
  independently reproduced by me. The verbatim-copy claim also checks out: the artifact's
  `### Spec slice checklist (verbatim)` matches spec lines 144-154 text, nesting, em-dashes
  and anchors exactly.

### Temp test verification

Two files under `docs/builder/temp-tests/slice-2/` (confirmed gitignored via
`git check-ignore -v` -> `.gitignore:192`). Both are review instruments, not shipped-behavior
proof; **disposition: keep as review artifacts, promote nothing.** Neither caught a bug -
each *confirmed* a Worker 2 claim I was required not to relay.

**1. `test_w3_reaimed_assertion_failability.py` - the re-aimed `channels` assertion.**
Two tests, both passing, which together are the decisive proof:

- `::test_the_old_base_assertion_is_vacuous_while_the_new_one_fails` runs the same
  `simulated_absence` block but **omits** the
  `evicted_modules("strawberry.django", parent=strawberry, attr="django")` guard, so
  `strawberry.django.views` answers from the cache and upstream's body does **not**
  re-execute. Under that condition it asserts
  `(upstream.GraphQLView is not GraphQLView) is False` and the same for the async twin - so
  the shipped test's load-bearing comparison **would fail**, i.e. it is genuinely failable
  and not decoration. In the same block it asserts that Slice 1's superseded shape
  (`module.DjangoGraphQLView.__base__ is not <original __base__>`) still **passes**, with
  both objects named `_RequestBodyLimitMixin` - i.e. the old form survives exactly the
  upstream regression the new form catches. Strictly stronger, mechanically.
- `::test_the_shipped_full_assertion_block_passes_when_upstream_is_evicted` is the control:
  with the two-sided guard in place, all three shipped assertions per view hold
  (`fresh is not captured`, `fresh in package_view.__mro__`,
  `captured not in package_view.__mro__`).

**Injection direction, with restoration proof.** Backed up
`django_strawberry_framework/views.py` and recorded
`shasum -a 256` = `6c05d05167a376af753d4198cfa7de9fb4d50bad54d947339cb96f8821ac6abc`;
injected `import channels  # noqa: F401  W3-REVIEW-PROBE` above the `cross_web` import:

```text
uv run pytest tests/test_views.py::test_views_module_imports_with_channels_absent --no-cov -q -p no:randomly -n0
E   ModuleNotFoundError: import of channels halted; None in sys.modules
django_strawberry_framework/views.py:51: ModuleNotFoundError
1 failed
```

Restored from the backup: `shasum -a 256 -c` -> `django_strawberry_framework/views.py: OK`,
the test **passed** again, and `grep -c "W3-REVIEW-PROBE"` -> `0`. No `git stash` was used
(concurrent writers). No other production or third-party file was ever modified during this
review.

**2. `test_w3_garbage_content_length.py` - Worker 2's new finding 3.** Four tests, all
passing. Confirms Django's `HttpRequest.body` raises `ValueError: invalid literal for int`
on `CONTENT_LENGTH: not-a-number` (source-confirmed: `django/http/request.py` #"
self._check_data_too_big(int(self.META.get("CONTENT_LENGTH") or 0))", unguarded on 6.0.5;
the same unguarded `int()` inside the `DATA_UPLOAD_MAX_MEMORY_SIZE is not None` conditional
on the 5.2 floor). **The decisive addition my probe makes over the report:** the row that
runs against a mount with the cap fully **disabled**
(`MAX_REQUEST_BODY_BYTES = None`, where `_enforce_request_body_limit` returns before ever
touching `request.body`) raises the **identical** `ValueError`. So the raise is
unambiguously Django's own, reached later by
`cross_web/request/_django.py::DjangoHTTPRequestAdapter.body`, and the cap introduces **no
regression** - it only makes the pre-existing failure happen a few frames earlier, still
before any parse or execution, so the security property is intact. That fully vindicates
Worker 2's reasoning and its test-design consequence: asserting a `413` for the garbage case
would have pinned Django's `ValueError` as the package's, and pinning the pure-function half
(`::test_the_declared_length_reader_is_none_for_every_unmeasurable_shape`, garbage -> `None`)
plus the counted half through the **absent**-declaration shape
(`::test_the_counted_check_fires_when_no_content_length_is_declared_at_all`) is the honest
split. No promotion recommended - a shipped test here would pin Django's exception type as a
package contract, which is exactly the trap being avoided. It belongs in the spec's Edge
cases instead (escalated below).

**Test-run gates I ran myself (never relayed, no `--cov*` flag anywhere):**

- **Canonical full sweep:** `uv run pytest --no-cov` -> **4849 passed, 40 skipped** in
  58.19s. Matches Worker 2's report exactly.
- **Delta measured per file, not inferred from the total.** `--collect-only`:
  `tests/test_views.py` **38** (Slice 1: 7, `bld-slice-1` line 1911) = **+31**;
  `examples/fakeshop/test_query/test_transport_api.py` **28** (Slice 1: 11, same line) =
  **+17**; `tests/base/test_conf.py` **46** (unchanged - assertions added, no new test).
  31 + 17 = 48, and 4801 + 48 = 4849 exactly, so the delta closes arithmetically with no
  room for a silent loss elsewhere. Zero failures, skips unchanged at 40. The known
  narrowed-invocation trap (`test_kanban_api.py` + ~5 `examples/fakeshop/tests/` rows) did
  not appear, as expected under the full sweep.
- **Floor parity (Test-plan row 18) independently reproduced** in the isolated
  `/tmp/dsf-floor-r5` (verified in place at `Django 5.2` / `python 3.10.19`); the shared
  `.venv` was never mutated. `tests/test_views.py tests/base/test_conf.py` -> **84 passed**;
  `test_transport_api.py` + `test_uploads_api.py` -> **34 passed** (28 + 6). All three
  numbers match Worker 2's report exactly.
- **Hygiene** re-run on the five explicit paths (results under
  `### Documentation / release sanity`).

### Notes for Worker 1 (spec reconciliation)

Accepted with the items below escalated. None blocks the slice; each needs spec authority
Worker 2 does not have.

1. **Escalated: the Decision-8 checklist box - the spec contradicts itself, and the
   left-unticked split is legitimate.** My judgment on the box: **not an under-tick and not
   an over-tick.** By BUILD.md's own Medium definition the offense is a *silently*
   unaddressed sub-check "with no matching implementation in the diff **and** no recorded
   deferral" - and this box fails both halves of that test. There **is** matching
   implementation at the code-documentation layer (`conf.py`'s
   `MAX_REQUEST_BODY_BYTES_KEY` comment states the deployment cap is *required alongside*,
   never an alternative; `_RequestBodyLimitMixin`'s docstring carries the full
   `read_body`-already-spooled boundary and the processes-vs-accepts distinction), and the
   split **is** recorded twice - pre-declared in the plan's step 4 and re-declared in the
   build report's `### Notes for Worker 1` item 1. Leaving the box open is also the
   conservative direction. The real defect is in the **spec**, not the build: the Slice-2
   checklist assigns this box to Slice 2 while Decision 8's own body says "**Slice 5's**
   transport guidance states plainly that ..." and the spec's Doc updates put every `.md`
   surface in Slice 5's set. Resolution paths, pick one: **(a)** move the box to the Slice-5
   checklist and note in Slice 2's block that the code-doc layer landed here - my preference,
   since it makes the spec self-consistent and keeps one owner per obligation; or **(b)**
   tick it now on the code-doc layer and add a Slice-5 sub-bullet for the consumer prose
   (`client_max_body_size`, the ASGI-server flags, the Daphne request-buffer note). Do not
   leave it ambiguous - the integration pass will re-grep it.
2. **Confirmed independently, not relayed: Django's own ceiling answers `400`, not `413`.**
   Read at source on both stacks. Two spec sentences are factually wrong and are yours to
   correct: Current state's Django-body bullet #"`ASGIHandler.create_request` converts the
   resulting `RequestDataTooBig` into a `413`" and Edge cases #"ASGI converts it to its own
   `413`; on WSGI it surfaces as a `400`". `create_request`'s `except RequestDataTooBig`
   guards only `ASGIRequest(scope, body_file)` construction, which never reads the body;
   `RequestDataTooBig` is raised lazily from `HttpRequest.body` inside the view, where
   `response_for_exception` maps `SuspiciousOperation` to `400` - on both transports and
   both supported releases. The spec's *conclusions* (both ceilings are correct; the tests
   assert which fired) are unaffected. The shipped test already records the discrepancy in
   its docstring, so the tests are correct either way.
3. **Confirmed independently: the compatibility floor has no seekable actual-size check.** I
   read `HttpRequest.body` out of `/tmp/dsf-floor-r5` itself: the whole guard is
   `settings.DATA_UPLOAD_MAX_MEMORY_SIZE is not None and int(META.get("CONTENT_LENGTH") or 0)
   > ...`, with **no** `_stream.seekable()` branch. So Current state lines 283-290 are
   version-specific and should be qualified by version. This *strengthens* Decision 7 - at
   the floor the package's counted check is the only application-level bound against an
   absent or understated declaration - and it is why the "never lower
   `DATA_UPLOAD_MAX_MEMORY_SIZE` in an ASGI row" rule must survive into Slices 3-5.
4. **Escalated: the garbage-`CONTENT_LENGTH` shape deserves a spec Edge-cases sentence.** I
   verified both halves of Worker 2's finding 3 (see `### Temp test verification`): Django's
   `int(META["CONTENT_LENGTH"] or 0)` is unguarded, and - the part the report did not prove -
   the failure is **not** introduced by the cap, because a mount with the cap disabled
   raises identically. Recommended addition to Edge cases: an unparseable `Content-Length`
   is refused by Django before the counted check completes; the package never *trusts* the
   declaration (`_declared_content_length` returns `None` for it), the failure precedes any
   parse or execution, and a conforming server rejects such a header before Django sees it -
   so the package deliberately does not pre-read or rewrite `META` to convert it, both of
   which Decision 7 rejects by name. Also record why no test asserts a status for it.
5. **Escalated: the default `1_048_576` is still not stated in the spec's setting block.**
   Your own planning note 3 flagged it; the value is now shipped in
   `conf.py::max_request_body_bytes_setting` and pinned by three tests. State it in the spec
   so Test-plan row 17's "the setting beats the default" has a named referent.
6. **Slice 5 obligations this slice grew, beyond the spec's current list.**
   `examples/fakeshop/test_query/README.md` currently does not mention
   `test_transport_api.py` at all, so it now owes **S1 and S2** acceptance rows, not just
   the S1/S2/S9 set the spec names - and its line 5 raw-envelope exemption ("Only tests whose
   subject is the raw request envelope (malformed bodies, content-type negotiation) drop to a
   bare `django.test.Client.post(...)`") must widen to cover the hostile-`Host` / `secure=` /
   `enforce_csrf_checks=` / `AsyncClient` rows **and** the in-process `ASGIHandler` driver.
   `docs/TREE.md` still owes `views.py` + `tests/test_views.py`. Plus L1/L2 above as prose
   corrections.
7. **Carry-forward from my Slice-1 review, still outstanding.** The three now-wrong transport
   strings in `django_strawberry_framework/auth/` (`sessions.py::classify_transport`'s
   unrecognized-scope-type message, and both `mutations.py::_login_resolve_body` /
   `::_logout_resolve_body` docstrings) are still uncorrected and still routed to Slice 5.
   Confirm they are discharged before the integration pass closes.
8. **No structural drift from the plan.** The hook is `run` on both classes; the keyword is a
   class attribute on a mixin placed first; the check order (resolve/validate -> GET no-op ->
   declared gate -> multipart return -> counted check) and the `>` comparison are as
   specified; the reason string is the spec's verbatim sentence; exactly one settings key was
   added; the `TODO` anchor is gone; `__init__.py`, `CHANGELOG.md`, the version quintet, and
   every Slice-5 prose surface are untouched. The three items the plan left to discretion
   that changed shape (`_MULTIPART_CONTENT_TYPE` as a fourth private constant, the
   four-mount factory, the CSRF-minting ASGI driver) are each an improvement and each is
   recorded in the build report's `### Implementation notes`.

### Review outcome

**review-accepted.** Zero High, zero Medium. Three Low findings (two docstring/comment
accuracy items and one redundant assertion), each recorded with a reason for not blocking and
routed to Worker 1's final verification; one live DRY duplication (DRY-1) recorded as a
deferred follow-up Worker 1 weighs at the integration pass, which the acceptance gate
permits. Every spec-required Slice-2 behavior is in the diff; the one unticked checklist box
is a recorded split whose real defect is a spec-internal contradiction, escalated above.

What convinced me, in order of weight: (1) the `413` is provably upstream's own
`except HTTPException` translation on both flavors, read at source, with zero duplicated
response machinery - the single largest thing this slice could have got wrong; (2) the
re-aimed `channels` assertion is strictly stronger, proven by making the *new* comparison go
`False` under an upstream-cached condition while the *superseded* one still passed, plus an
injected-import failure with a checksum-verified restore; (3) every negative witness in the
slice - `_body`-unmaterialized, `_PARSE_CALLS == []`, the absent DB row - carries its
positive control inside the same test, so none of them is vacuous; (4) the mixin insertion is
inert against both upstream MROs (measured: zero name collisions, keyword binds on both
classes, `__init__` chain untouched) and no other reader in the tree depends on the old base
shape; (5) no test pins a Django-owned outcome as the package's, and the one place where the
temptation was strongest - the garbage-`CONTENT_LENGTH` case - was correctly declined, which
I confirmed is not even a regression by reproducing the identical raise on a cap-disabled
mount; and (6) the canonical sweep is green at 4849/40 with the +48 delta closed
per-file rather than inferred, and the floor parity reproduced at 84 / 34 in the isolated
venv.

---

## Final verification (Worker 1)

Read end-to-end before acting: this artifact in full (plan, Worker 2's build report, Worker 3's
review), `docs/spec-046-transport_security-0_0_15.md`,
`docs/builder/build-046-transport_security-0_0_15.md`,
`docs/builder/bld-slice-1-protocol_split.md` (the accepted prior slice, for the cross-slice DRY
check and its still-open wording items), `CHANGELOG.md` (read-only, unedited), and
`docs/builder/worker-memory/worker-1.md`. The diff was obtained independently
(`git status --short`) and is exactly the five paths the reports claim -- `conf.py` and
`tests/base/test_conf.py` as `M`, `views.py` / `tests/test_views.py` /
`examples/fakeshop/test_query/test_transport_api.py` as `??` (Slice 1 created them, uncommitted) --
plus this artifact and the spec I edit below. Every other dirty path is on the build plan's
baseline-dirty list and was neither edited nor reverted.

### Spec slice checklist audit (box by box, against the diff)

I am the auditor here, not the ticker. Worker 2 ticked boxes 1, 2 and 4; box 3 was left `- [ ]`
with a recorded split. **Verdict: no over-tick, and box 3 is now `- [x]`** -- see the ruling
below. No box was un-ticked.

- **Box 1** (both views enforce a cumulative byte cap **before** JSON parsing or schema
  execution, returning `413`) -- **LANDED.** Verified without relaying: I read upstream's
  `.venv/.../strawberry/django/views.py::GraphQLView.dispatch` and `::AsyncGraphQLView.dispatch`
  myself -- each body is exactly `try: return [await] self.run(request=request)` /
  `except HTTPException as e: return HttpResponse(content=e.reason, status=e.status_code,
  content_type="text/plain")`. The package overrides `run`, i.e. **inside** that `try`, so the
  `413` `text/plain` response is upstream's four lines with zero duplicated translation, and
  nothing between `dispatch` and the raise parses anything. `views.py::_RequestBodyLimitMixin`
  #"raise HTTPException(413, _BODY_LIMIT_REASON)" fires at two sites (declared gate, counted
  check) ahead of `super().run(...)` on both flavors.
- **Box 2** (one new settings key `MAX_REQUEST_BODY_BYTES` in `conf.py`, per-mount view-kwarg
  override, constructor > setting > default, the `NESTED_CONNECTION_STRATEGY` shape) --
  **LANDED.** `git diff -- conf.py` adds exactly one `*_KEY` constant and one thin accessor; the
  precedence and validation live in `views.py::_resolved_max_request_body_bytes`, mirroring
  `optimizer/nested_fetch.py::resolve_strategy` -- including the split that keeps `conf.py` a
  reader that does not validate domain values.
- **Box 3** (the deployment-layer cap documented as a co-requirement) -- **RULED LANDED, ticked
  by me.** Reasoning as auditor, not as a courtesy to the split: BUILD.md's Medium tier catches a
  sub-check that is *silently* unaddressed -- "no matching implementation in the diff **and** no
  recorded deferral". This box fails both halves. `conf.py`'s `MAX_REQUEST_BODY_BYTES_KEY` comment
  states the deployment cap is "REQUIRED ALONGSIDE this one, never an alternative to it, because
  no application-level ceiling can stop the bytes from being received", and
  `views.py::_RequestBodyLimitMixin`'s docstring carries the full boundary
  (`ASGIHandler.read_body` has already drained the request into a spooled temporary file; the cap
  bounds what the application *processes*, never what the server *accepts*; therefore a
  reverse-proxy / ASGI-server cap is a CO-REQUIREMENT). Both are in this diff; I read them rather
  than taking the report's word. The split was pre-declared in the plan's step 4 and re-declared
  in the build report. **But the split being legitimate is not the same as the box being
  well-formed**, and Worker 3 is right that the underlying defect is spec-internal: the checklist
  assigned the whole obligation to Slice 2 while Decision 8's own body says "Slice 5's transport
  guidance states plainly that ...". A box that two slices can each read as the other's is a spec
  defect whichever slice is standing in front of it, so I fixed the spec rather than the
  bookkeeping (spec changes 2 and 3): box 3 now names the two code-documentation surfaces Slice 2
  ships, Slice 5's guidance bullet now owns the consumer prose with the concrete directives, and
  Decision 8 carries an explicit two-surface split so neither slice can inherit the other's half.
  Against that narrowed contract the box landed in full -- hence `- [x]`.
- **Box 4** (the full S2 regression matrix earned live over fakeshop's real `/graphql/`) --
  **LANDED.** Test-plan rows 13-17 all have live rows in
  `examples/fakeshop/test_query/test_transport_api.py`, over fakeshop's real mount or over a
  second mount of the same package view through the existing Probe URLconf: declared
  below/at/above; the WSGI missing/understated colour; the ASGI absent/lying colour; the
  multi-fragment cumulative row with its under-cap control; malformed-JSON on both sides of the
  cap; multipart over the declared gate; the parse/execute negative witness with its mandatory
  in-test control; both ceiling directions; all three precedence rungs; and the async colour.
  Row 18's floor parity was run twice independently (Worker 2 and Worker 3) in the isolated
  `/tmp/dsf-floor-r5`.

**No `- [ ]` remains, so no deferral reason is owed under this heading.**

### DRY check across Slice 1 + Slice 2

**Verdict: one live duplication, DRY-1, confirmed and deliberately deferred to the integration
pass as a binding obligation. No other new duplication.** Re-derived rather than inherited:

- **DRY-1 confirmed mechanically, not eyeballed.** `src.count(block) == 2` for the 7-line
  permission-granting block (comment included) in
  `examples/fakeshop/test_query/test_transport_api.py`, across
  `::test_csrf_is_enforced_on_a_cookie_authenticated_graphql_mutation` (Slice 1) and
  `::test_an_over_cap_mutation_is_rejected_before_any_parse_or_schema_execution` (Slice 2).
  **Deferral is the right call, and here is why it is not the forbidden kind.** The duplication
  spans an accepted slice's test and this slice's test, so its consolidation is by definition
  cross-slice work -- BUILD.md's integration pass is its designated home ("Worker 1 re-checks DRY
  across slices at the integration pass"), and `worker-3.md`'s acceptance gate explicitly leaves
  the call to me. Pulling it forward is not free: Worker 1 may not edit tests, so it costs a
  `revision-needed` re-loop (Worker 2 pass + Worker 3 re-review) on a slice whose review found
  zero High and zero Medium, in order to add a 7-line test helper -- and it would edit a
  Slice-1-accepted test on a schedule that cannot yet see whether Slices 3 and 4 add rows wanting
  the same actor. Nothing about the deferral is "ship now, fix later": the fix lands inside this
  same build, before the maintainer's first touch point.
  **Binding integration-pass obligation, recorded here so `bld-integration.md` inherits it rather
  than rediscovering it:** extract one module-local `_user_who_can_add_categories()` returning the
  permission-refreshed user, and rewire **both** call sites named above. If a later slice adds a
  third site, it joins the same helper. This is not a suggestion to weigh again -- it is the
  integration pass's work item, and BUILD.md's integration step 5 (walk every accepted artifact's
  `DRY findings`) is the mechanism that surfaces it.
- **DRY-2 (the two three-line `run` overrides) is genuinely irreducible.** I confirmed the
  premise at source rather than accepting it: `cross_web/request/_django.py`'s
  `AsyncDjangoHTTPRequestAdapter.get_body` is `async def ...: return self.request.body`, so the
  whole decision body is legitimately one **synchronous** method serving both flavors, and the
  only split left is the `async`/`await` pair -- the same split upstream's own `dispatch` pair
  carries.
- **`1_048_576` appears exactly once in production** (`conf.py::max_request_body_bytes_setting`);
  `views.py` never restates it, and the default is pinned from the **key-absent** direction, so a
  duplicated literal could not satisfy the test. Verified in the diff.
- **`_capped_view` in two trees** (`tests/test_views.py` vs the live module) is a name collision
  with genuinely different responsibilities (a view *instance* builder vs a request-time URLconf
  view *factory*) in two test trees with no shared home. Verified-and-rejected as a consolidation
  target -- consolidating would be the wrong abstraction, and `worker-1.md` #"Before recommending
  a consolidation ... confirm the duplication is live" applies in reverse here.
- **Cross-slice literal check.** `_BODY_LIMIT_REASON`, `_MULTIPART_CONTENT_TYPE` and the
  `r"^graphql/?$"` triple from Slice 1 are each single-sited in production; the shadow overviews
  report **0 repeated string literals** in both production files this slice touched. No Slice-1
  helper was near-copied: the live module's `_post` was *refactored* to delegate to the new
  `_post_bytes` rather than the new rows duplicating it, which is the correct direction.

### Existing tests still pass

`uv run pytest tests/test_views.py tests/base/test_conf.py
examples/fakeshop/test_query/test_transport_api.py examples/fakeshop/test_query/test_uploads_api.py
tests/test_routers.py --no-cov -q` -> **145 passed**, zero failures (8 workers, 12.37s). No
`--cov*` flag was used anywhere in this pass. Slice 1's router and view contracts are in that
scope on purpose: the mixin insertion changes both views' base lists, and `test_routers.py` is the
sibling whose composition assertions would notice a knock-on.

Per-file collection counts measured myself, not inferred: `tests/test_views.py` **38**,
`examples/fakeshop/test_query/test_transport_api.py` **28**, `tests/base/test_conf.py` **46**
(unchanged -- assertions added, no new test). That reproduces the +31 / +17 / 0 delta exactly, so
the canonical sweep's **4849 passed / 40 skipped** (measured independently by Worker 2 and again
by Worker 3, against Slice 1's 4801/40) closes arithmetically with no room for a silent loss
elsewhere. I cite theirs rather than re-running it; `bld-final.md`'s gate re-runs it as the
backstop.

### Independent verification of the two Django claims the spec edits rest on

I did not relay these. Both were read at source, in both interpreters, because a spec edit that
corrects a factual claim must not itself be hearsay:

- **`ASGIHandler.create_request`'s `413` is unreachable for this flow.** Its `except
  RequestDataTooBig` wraps exactly one expression, `self.request_class(scope, body_file)`, and I
  read `ASGIRequest.__init__` top-to-bottom: it sets `scope` / `path` / `method` / `META` and
  decodes headers, and never touches the body. `RequestDataTooBig` is therefore raised lazily out
  of `HttpRequest.body` inside the view, where `response_for_exception` maps
  `SuspiciousOperation` to `400`. Two workers measured `400` on both transports and both
  releases; the source explains why, which is the part a spec sentence needs.
- **The floor has no seekable actual-size check.** Installed Django 6.0.5's `HttpRequest.body`
  carries `if self._stream.seekable(): stream_size = self._stream.seek(0, os.SEEK_END)` plus
  `_check_data_too_big(stream_size)`. The floor's -- read out of `/tmp/dsf-floor-r5` itself at
  `Django 5.2` -- is a single `DATA_UPLOAD_MAX_MEMORY_SIZE is not None and
  int(META.get("CONTENT_LENGTH") or 0) > ...` conditional with **no** `_stream.seekable()` branch
  at all. So at the floor the package's counted check really is the only application-level bound
  against an absent or understated header, and the "never lower `DATA_UPLOAD_MAX_MEMORY_SIZE` in
  an ASGI-driven row" rule is a genuine correctness constraint on the test matrix, not a
  convention.
- **The garbage-`Content-Length` raise is Django's.** `_check_data_too_big(int(self.META.get(
  "CONTENT_LENGTH") or 0))` is unguarded on 6.0.5, and the same unguarded `int()` sits inside the
  floor's conditional. Worker 3's cap-disabled-mount probe is the decisive half -- the identical
  `ValueError` with the cap off proves the cap introduces no regression -- and I accepted it on
  that evidence rather than on the claim.

### Staged-anchor check

`grep -rn "TODO(spec-046" --include='*.py' --include='*.md' .` and
`grep -rEn 'TODO-(ALPHA|BETA|STABLE)-046' --include='*.py' .` -> **no hit in any shipped source
or test**. The only survivors are the spec's own generic staging-discipline sentence and the
per-cycle `bld-*.md` narrative. Slice 1's `TODO(spec-046 Slice 2)` anchor was this slice's to
discharge and is gone with no replacement -- `views.py`'s provenance is now
`spec-046 Decision 6/7/8` citations, which `AGENTS.md` keeps.

### How Worker 3's three Lows and Slice 1's L2 are routed

All four are prose-only, none load-bearing, and none is a behavior defect. **Routed to Slice 5,
contractually** -- a new checklist sub-bullet, not a note (spec change 6), so Slice 5's planning
pass inherits them as contract items instead of finding them in `bld-final.md`'s catalog.

- **L1** -- I re-derived the finding rather than accepting it: `View.as_view`'s guard is
  `hasattr(cls, key)`, which walks the whole MRO, so a mixin-**last** subclass admits
  `max_request_body_bytes=` identically and the docstring's causal claim ("sits first **so** the
  attribute exists by the time the guard runs") is not operative. The *choice* of first position
  is still correct and defensive; the operative reason is precedence over any same-named
  attribute upstream may later add. Spec sub-bullet names the re-wording.
- **L2** -- confirmed against the diff: `conf.py`'s key comment says "The bound is on bytes the
  application actually RECEIVED" with no multipart carve-out, while
  `_RequestBodyLimitMixin`'s docstring carries the nuance correctly. The settings comment is the
  surface a consumer reads *while configuring the key*, so it is the worse place to overstate.
  Routed with the cross-surface half Worker 3 attached: Slice 5's `docs/README.md` deployment
  guidance must carry the carve-out too, which is now written into that bullet (spec change 3).
- **L3** -- confirmed trivially true and already covered more strongly by the exact-`__all__`
  test. Routed as a deletion, with the reason stated in the spec so a future slice does not later
  weaken the exact-`__all__` test believing this one covers privacy.
- **Slice 1's L2 (the three now-wrong `auth/` transport strings)** -- **still contractually owned
  by Slice 5**, unchanged from my Slice-1 pass: `docs/spec-046-transport_security-0_0_15.md`
  Slice-5 checklist, the sub-bullet naming `sessions.py::classify_transport`'s
  unrecognized-scope-type message and both `mutations.py` resolve-body docstrings. I re-read the
  bullet in place; it survives my edits intact and is now one of five prose obligations Slice 5
  carries. Confirmed, nothing to re-route.

**Why routing rather than `revision-needed`.** Sending the slice back for four prose lines would
re-open a diff with zero High and zero Medium, and it would fix L2 on one of its two surfaces
while the other (Slice 5's `docs/README.md`) is still unwritten -- so the wording would have to be
touched twice. Slice 5 already carries production-string corrections of exactly this shape by my
own Slice-1 ruling, which makes it this build's designated prose pass. Routing is cleaner and it
is now contractual; the integration pass will re-grep the checklist.

### Summary

Slice 2 delivers S2 end-to-end. Both package views now enforce a cumulative request-body ceiling
at the top of `run` -- inside upstream's `except HTTPException` seam, so the `413` `text/plain`
response is upstream's own translation with no duplicated response machinery -- ordered
resolve/validate, GET no-op, declared-length gate (which refuses without reading the body),
multipart early return (which keeps the `Upload` streaming path unmaterialized), then the
**counted** check on real received bytes. `conf.py` gains exactly one settings key,
`MAX_REQUEST_BODY_BYTES`, defaulting to 1 MiB, with validation deliberately sited in the view's
resolver rather than in the thin reader. The whole regression matrix is earned live over
fakeshop's real `/graphql/` and over Probe mounts of the same view, including three rows that
drive Django's own `ASGIHandler` in-process because neither test client can present an
unmeasured, understated, or fragmented body -- and those rows mint a real CSRF token rather than
exempting the mount, which makes a `413` from them unambiguously the view's. Every negative
witness in the slice carries its positive control inside the same test. Two review-side facts
that mattered more than the code: the mixin taking first place in the bases silently voided
Slice 1's `channels`-absence `__base__` assertion, and Worker 2 re-aimed it at upstream's class
identity (strictly stronger, proven failable in both directions); and Django's own
`DATA_UPLOAD_MAX_MEMORY_SIZE` ceiling answers `400`, not the `413` this spec predicted in four
places, all four of which I corrected.

The spec was the thing this slice actually broke, and that is where the reconciliation went: a
checklist box that two slices could each read as the other's, four wrong status-code predictions,
a version-blind claim about `HttpRequest.body`, an unstated default, an undocumented edge case,
and two under-specified Slice-5 obligations. Six edits, no behavior change, glossary checker
green.

**Final status: `final-accepted`.**

### Spec changes made (Worker 1 only)

Six edits to `docs/spec-046-transport_security-0_0_15.md`, all triggered by Slice 2. Verified
after the last one:
`uv run python scripts/check_spec_glossary.py --spec docs/spec-046-transport_security-0_0_15.md`
-> **`OK: 37 terms - all have glossary entries and at least one spec link.` (exit 0)**. Term count
unchanged at 37, so **no new glossary term and no `-terms.csv` row** is owed and
`docs/GLOSSARY.md` is untouched. All **19** in-page anchors re-verified to resolve to real
headings (17 before this pass; the two additions are `#current-state` and
`#edge-cases-and-constraints`). `git diff --check` clean. **Decision 15, the version-boundary
preamble, and the `CHANGELOG.md` prohibition were not touched.**

1. **Status line (line 37).** `IN BUILD - Slice 1 (S1) is built and accepted; Slices 2-5 remain.`
   -> `IN BUILD - Slices 1-2 (S1, S2) are built and accepted; Slices 3-5 remain.` -- required by
   `worker-1.md` #"Spec status-line re-verification".

2. **Slice-2 checklist, box 3 narrowed (lines 151-157).** -- **Reconciliation item 1, resolved.**
   The box now reads "stated as a **co-requirement**, not an alternative, on the two
   **code-documentation** surfaces this slice ships: `conf.py`'s `MAX_REQUEST_BODY_BYTES` key
   comment and the cap-contract docstring in `views.py`", and says the consumer-facing prose is
   Slice 5's. **Path chosen: Worker 3's (b), not (a), and the reason is ownership rather than
   convenience.** Slice 2 is the only slice that edits `conf.py` and `views.py`; moving the whole
   box to Slice 5 would leave shipped documentation in Slice 2's diff that no checklist box names
   -- the exact defect I fixed in Slice 1 by naming the `config/urls.py` swap -- and it would
   license a release in which the settings key's own comment omits the co-requirement. Path (b)
   splits by **surface**, which is what "exactly one slice owns each surface" actually requires.

3. **Slice-5 checklist, deployment-guidance bullet sharpened (lines 185-192)**, and **Decision 8
   gains a "Two surfaces, one per slice" block (after its Decision paragraph).** -- the other half
   of item 1, plus L2's cross-surface obligation. Slice 5's bullet now explicitly owns the
   consumer-facing co-requirement statement with its concrete directives
   (`client_max_body_size`, the ASGI-server equivalents, the Daphne request-buffer note) **and**
   the multipart carve-out, "so a reader of the proxy-cap paragraph alone cannot conclude that
   multipart is byte-counted". Decision 8 now states the split at its source, with the reason
   Slice 2 owns the code layer (a key whose own comment omits the co-requirement for a whole
   release is the misreading the decision exists to prevent). After this, the contradiction Worker
   3 found cannot recur: the checklist and the Decision say the same thing.

4. **Every `413` prediction about Django's own ceiling corrected -- four sites, not the two
   escalated.** -- **Reconciliation items 2 and 3.** (a) **Current state's Django-body bullet
   (lines 307-336)** rewritten: check (a) applies on every supported release, check (b) is
   **Django 6.0 only** and does not exist at the 5.2.0 floor (so at the floor the package's
   counted check is the only application-level bound -- which strengthens Decision 7 and licenses
   the ASGI-row test rule), and whichever check fires the outcome is a **`400`**, because
   `RequestDataTooBig` is raised lazily from `HttpRequest.body` inside the view while
   `create_request`'s `413` branch guards only `ASGIRequest.__init__`, which never touches the
   body. (b) **Edge cases** entry rewritten to `400` on both transports. (c) **Borrowing posture
   (lines 476-480)**, which credited Django with `RequestDataTooBig -> 413`, corrected to the
   version-split size checks surfacing as `400`. (d) **Error shapes' "Body over the cap" bullet**,
   which contrasted the package's `413` with "Django's own `413`", corrected to Django's `400` --
   "the `413` is therefore the package's own signature". Sites (c) and (d) were not in the
   escalation; leaving them would have left the spec disagreeing with itself in the two places a
   reader looks first.

5. **Two new Edge-cases entries.** -- **Reconciliation items 3 and 4.** The **ASGI-row rule**:
   never lower `DATA_UPLOAD_MAX_MEMORY_SIZE` in a row that drives the ASGI handler, because that
   single combination is the one cell where the supported Django range diverges (6.0 rejects on
   the spooled size, the floor succeeds); Django's ceiling is exercised only through the declared
   path, which is identical on both, and that is what makes row 18 bit-identical rather than
   merely green. The **garbage-`Content-Length`** entry: the `ValueError` is Django's unguarded
   `int(META["CONTENT_LENGTH"] or 0)`, not the package's; the package never *trusts* an
   unparseable declaration; the failure still precedes any parse or execution; a cap-disabled
   mount raises identically, so the cap introduces no regression; and no test asserts a status
   for it deliberately, because doing so would pin Django's exception as a package contract while
   the alternatives (pre-reading the stream, rewriting `META`) are both rejected by name in
   Decision 7.

6. **Decision 7 step 4 states the default (lines ~897-906)**, and **two Slice-5 checklist
   sub-bullets added (lines 208-234)**. -- **Reconciliation items 5, 6 and 7.** Step 4 now says
   "**The package default is `1_048_576` (1 MiB)**", with the query-document-vs-upload rationale
   and the note that it is stated once, in `conf.py`'s reader, so Test-plan row 17's "the setting
   beats the default" has a named referent; it also spells out that a `None` *kwarg* defers while
   a `None` *setting* disables. The first new Slice-5 sub-bullet makes
   `examples/fakeshop/test_query/README.md` contractual: the **S1 and S2** acceptance rows (the
   file does not mention `test_transport_api.py` at all today) plus the **widened raw-envelope
   exemption**, since its "malformed bodies, content-type negotiation" wording covers neither
   S1's hostile-`Host` / `secure=` / `enforce_csrf_checks=` / `AsyncClient` rows nor S2's
   in-process `ASGIHandler` driver; the Doc-updates bullet for that file was widened to match. The
   second new sub-bullet routes the three Lows (L1's mixin-first rationale, L2's multipart
   carve-out in the key comment, L3's redundant assertion) **plus one consequence of edit 4 that I
   own**: `::test_the_two_body_ceilings_are_distinguishable_by_the_response_they_produce`'s
   docstring says "the spec's Edge-case sentence predicting a `413` ... is inaccurate", which my
   own correction just made obsolete -- the clause is dropped while the `400` explanation stays,
   since it is why the row asserts what it asserts.

**Not edited, deliberately:** `CHANGELOG.md` and the version quintet (Decision 15, the joint cut);
`docs/GLOSSARY.md` and `-terms.csv` (no new term); every baseline-dirty path; and every source or
test file (Worker 1 does not edit code -- which is exactly why the four prose items are routed to
a slice that can).
