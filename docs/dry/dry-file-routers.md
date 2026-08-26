# DRY review: `django_strawberry_framework/routers.py`

Status: verified

## Independent verification (Worker 2)

Re-traced independently from source at baseline `394e984`; scoped diff
(`git diff 394e984 -- django_strawberry_framework/routers.py`) is EMPTY — no cycle or
concurrent work touched the target.

Confirmed at source: the `"http"` value is the consumer application verbatim (`routers.py:500`);
the `"websocket"` value is the single four-layer composition literal (`routers.py:507-520`);
the public symbol exists only through PEP 562 `__getattr__` (`routers.py:528`) into the
module-global cache (`routers.py:167`), so eviction-simulated absence/degraded-install tests
(`tests/test_routers.py:2938-3100`, `sys.modules` sentinel + strict eviction) exercise real
re-resolution; `consumers.py` delegation imports sit at `routers.py:49-54` and grep over package +
examples shows ZERO production importers of this file (all hits are docstring/comment references;
fakeshop has only `config/wsgi.py`, no `asgi.py`, and `test_query/test_transport_api.py` covers the
live HTTP half). Re-ran the scratch probe myself:
`uv run python docs/dry/temp-tests/dry-file-routers/probe_import_coupling.py` → `routers ADDS: 2`
(`consumers`, `routers`) — the layering-inversion measurement reproduces exactly.

Floor-constant rejection re-probed and it HOLDS. All four sites verified verbatim (`routers.py:75`,
`routers.py:84`, `routers.py:88`, `auth/sessions.py:67`) plus `pyproject.toml:65`
(`channels[daphne]>=4.3.2`) and `pyproject.toml:40` (strawberry floor). No legitimate owner stands
at the source: `utils/imports.py` states the feature-neutral doctrine in its own contract
("deliberately NO ``feature_label`` parameter ... hint strings stay single-sited at the feature
owner", `utils/imports.py::require_optional_module`); `auth/sessions.py → routers` is measured
coupling inversion, not style; and I additionally weighed the option the artifact left unstated —
a NEW tiny leaf module (e.g. `_floors.py`) both sites could import cycle-free — and it is dominated,
not viable: a bump always moves pyproject + spec/GLOSSARY prose + the CI-pinned re-typed test
literals regardless, so the agreement set stays multi-site by design (the "three-places-that-must-
agree" comment, `routers.py:70-72`, enforced via `_HINT_SUBSTRING` re-typing,
`tests/test_routers.py:147`), meaning the leaf module shrinks textual occurrences without reaching
count-1 anywhere while carving an exception into documented doctrine. The intra-module variant
(one private constant interpolating routers' own three hints) is likewise below the bar: three
occurrences in one file are one edit region already, and it adds indirection into pinned contract
strings. The same-named-guard rejection also holds: I read all four `require_*` wrappers — each a
thin call over `utils/imports.py::require_optional_module`, differing only in per-feature hint text.

Counts recounted with my own examples, both hold at 1: (a) posited "insert a rate-limit wrapper
between AuthMiddlewareStack and URLRouter" — only the composition dict literal moves; the unwrap
helpers assert class identity in order (`tests/test_routers.py:585-618`) and fail loudly, no other
module owns any layer. Count **1**. (b) posited default-pattern change — one keyword default
(`routers.py:471`) defines it; `r"^graphql/?$"` is re-typed as drift detector at
`tests/test_routers.py:1409/1562` and fires on change. Count **1**.

Matrix discharge judged against the target's real surface: axis 1 searched across the actual guard
family and BOTH PEP 562 shapes (package root excludes its seven names from `__all__`,
`django_strawberry_framework/__init__.py:109`; routers includes its one name — verified inversion);
axis 2 legitimately inapplicable (zero coroutines defined; the only async tokens are prose inside
hint strings); axis 3 genuinely searched — this was the live axis and it got the deepest work;
axis 4 inapplicable with the compose/unwrap near-miss named rather than hidden; axis 5 searched with
the self-assert rationale for re-typed literals stated. Not shallow, not textual. Verdict:
proved zero-edit, **verified**. Pytest deferred (not authorized).

## System trace

The module owns exactly one lifecycle: the lazy materialization of
`DjangoGraphQLProtocolRouter` behind the soft `channels` dependency, and one composition: the
ASGI protocol mapping whose `"http"` value IS the consumer-supplied `django_application` (no
wrapper, so HTTP runs Django's real middleware) and whose `"websocket"` value is the four-layer
package composition `DjangoWebSocketHostValidator(AllowedHostsOriginValidator(AuthMiddlewareStack(
URLRouter([re_path(pattern, app)]))))` (spec-046 Decisions 2, 3, 4, 6, 11, 19). It implements no
transport policy of its own: the Host validator, the revalidating consumer factory, and the window
resolver live in `consumers.py` and are imported (`routers.py:49-54`); the raising import primitive
is `utils/imports.py::require_optional_module`; error shaping is `exceptions.py`. The public symbol
is never a module global — PEP 562 `__getattr__` (`routers.py:528`) builds the class once into the
module global `_ROUTER_CLASS` under a lock, so evicting the module from `sys.modules` drops the
cache, which the eviction-simulated absence/degraded-install tests rely on;
`build_revalidating_consumer_class(GraphQLWSConsumer)` runs inside the same guarded builder so the
consumer class dies with the cache (`routers.py:366-370`). Construction-time validation rules owned
here: required-callable `django_application` (else the migration-naming `ConfigurationError`), exact-
string + compilable `websocket_url_pattern`, finite non-negative window via consumers'
`resolved_revalidation_window` plus the positive-window/injected-class combination rejection, and
the three-shape consumer injection seam (`None` / subclass / factory) whose factory calling
convention and returned application are pre-checked at construction.

Consumers: no production module imports this file (grep over package + examples); it is a leaf
integration surface reached by a consumer's `asgi.py` and by `tests/test_routers.py` (5695 lines:
composition identity walks, communicator-driven protocol matrices, both subprotocols, absence/
degraded simulations). Fakeshop has **no** `asgi.py` — it runs WSGI-only, so the live tier
(`examples/fakeshop/test_query/test_transport_api.py`) proves the HTTP half through `/graphql/`
over `django.test.Client` and the router half keeps the documented genuinely-unreachable-live
exemption. `tests/auth/test_mutations.py::_channels_router` composes its own harness for
Channels-HTTP auth round trips, which the production router deliberately no longer serves.
Prose carriers: `views.py` docstring (HTTP/WS split), `consumers.py` docstrings (Host boundary,
cache lifetime), spec-041/046, GLOSSARY (`DjangoGraphQLProtocolRouter`, Soft dependency),
README/TODAY migration notes.

## Verification

- **Cross-flavor policy mirroring — searched.** The guard family: `rest_framework/__init__.py::
  require_drf`, `middleware/debug_toolbar.py::require_debug_toolbar`, `routers.py::require_channels`,
  `auth/sessions.py::require_channels` — all four are identical thin wrappers over the ONE primitive
  `utils/imports.py::require_optional_module`; that mirroring is already consolidated, and hint
  strings are per-feature-owner by stated policy (`utils/imports.py` docstring; restated in
  `auth/sessions.py`'s hint comment). The PEP 562 lazy-export shapes differ deliberately: the
  package root resolves seven DRF names through a name-map dict behind `require_drf()` and excludes
  them from `__all__` (star-import stays DRF-free); routers resolves ONE name through a cached class
  builder behind `require_channels()` and INCLUDES it in `__all__` so star-import opts INTO the
  guard (`routers.py:62-67`) — an intentional inversion. Item 1's artifact adjudicated the
  unification request; judged independently here: different guards, different resolution mechanics,
  different star-import policy — a shared helper needs mode flags for all three. Rejected. The
  remaining `__getattr__`s (`conf.py:303`, `consumers.py:1050`, `utils/permissions.py:136`) are
  object-level delegation in unrelated domains.
- **Sync and async twins — ruled inapplicable.** `grep -n "async def\|await "` over routers.py
  matches only prose inside hint strings; the module defines zero coroutines — construction is
  synchronous by design (`_ASYNC_FACTORY_HINT` states why it cannot await). The async behavior lives
  in the composed Channels wrappers, each owned elsewhere once; views.py's sync/async view pair is a
  different transport, not this file's twin.
- **Derived rather than repeated knowledge — searched; strongest candidate examined.** The verified
  floors: `channels>=4.3.2` appears in FOUR production sites (`routers.py:75`, `routers.py:84`,
  `routers.py:88`, `auth/sessions.py:67`) plus the pyproject dev-group row; `strawberry-graphql
  >=0.316.0` in `routers.py:88` plus the pyproject hard-dependency floor. Everything else is
  single-sited: the window default (`_DEFAULT_REVALIDATION_WINDOW` owned by `consumers.py:377`,
  imported at `routers.py:50`, "spelled ONCE" comment), the URL-pattern default (one keyword default,
  `routers.py:471`), close code/reason (consumers-owned), wrapper order (one dict literal).
- **Inverse and round-trip pairs — ruled inapplicable (near-miss named).** No encode/decode grammar:
  `_host_validation_request` projects scope→HttpRequest one way with no reverse site anywhere; the
  closest pair is compose-in-production/unwrap-in-tests (`tests/test_routers.py:585-618` unwrap
  helpers), which pins one code arrangement rather than splitting one grammar across modules.
- **Contracts restated in another medium — searched.** Constructor signature, wrapper order, default
  pattern, floors, and the two-place migration recipe each exist ONCE as code and are described in
  prose media (GLOSSARY/README/TODAY/spec-041/046) and pinned by tests: hint texts via RE-TYPED
  literals (`test_routers.py:147-165`, same discipline in `tests/rest_framework/test_soft_dependency.py:40`
  and `tests/middleware/test_debug_toolbar.py:60` — importing the constants would self-assert, so
  the repetition is the drift detector), composition via isinstance-identity walks. Prose sweeps on
  change are repo-law surface (symbol-path refs, joint-cut rules), not consolidable duplication.

Single-edit-site counts:

1. Posited change "add or reorder a fourth WebSocket wrapper outside the Host check": forced
   production sites = **one** (the mapping literal in `DjangoGraphQLProtocolRouter.__init__`,
   `routers.py:498-521`); test unwrap helpers fail loudly by design; prose follows repo law.
   Count **1** → the composition is correctly single-owned.
2. Posited change "change the default `websocket_url_pattern`": forced code sites = **one**
   (`routers.py:471`); the re-typed test assertions fire as the drift detector. Count **1**.
3. Posited change "bump the verified Channels floor to >=5.0": forced sites = pyproject dev row +
   three feature-owned hint strings + re-typed test literals + GLOSSARY/spec prose (>1). Judged
   intentional (below), not duplication to consolidate.
4. Scratch experiment `docs/dry/temp-tests/dry-file-routers/probe_import_coupling.py`
   (`uv run python ...`): importing `routers` adds exactly `consumers` + `routers` to the
   `auth.sessions` first-party graph — measuring the real cost of the rejected shared-floor-constant
   consolidation below (coupling direction, not weight).

Strongest rejected candidates:

- **One shared channels-floor constant interpolated into every hint.** Sites share the fact and would
  change together (count >1), but there is no legitimate owner: `utils/imports.py` is deliberately
  feature-neutral ("hint strings stay single-sited at the feature owner"); `auth/sessions.py`
  importing `routers` inverts layering (the transport-classification boundary used by
  `request_from_info` would load the WebSocket consumer machinery — measured above); runtime reads of
  pyproject were removed by this cycle's item 1, not added. The multi-place agreement is explicit
  doctrine ("place 2 of the three-places-that-must-agree", `routers.py:70-72`) and actively enforced:
  the re-typed `_HINT_SUBSTRING` literals fail CI on drift. A constant would shrink sites while
  weakening the only enforcement that cannot rot.
- **Unify the two same-named `require_channels` guards.** Different features, different failure
  situations, different advice ("you tried to build the ASGI router without channels" vs "a
  Channels-shaped request reached the auth session boundary without channels"); merging produces a
  worse message for one of the two audiences. The shared part (import-or-raise-with-hint) is already
  the single primitive both call.
- **Extract the twin `ConfigurationError` constructions in `_validated_websocket_url_pattern`**
  (`routers.py:182-184` vs `188-190`): adjacent lines of one function, one edit either way; a local
  closure adds indirection for zero ownership gain.

## Opportunities

None — proved. Every rule the file owns has exactly one implementation site (counts 1 and 2 above);
the only repeated fact family (dependency floors) is an explicit, documented, drift-pinned
multi-owner agreement whose consolidation options all damage ownership (no neutral home, layering
inversion measured at +2 modules, or reintroduced runtime metadata parsing), and the cross-file
policies it could be accused of duplicating (soft-dependency guarding, lazy export, Host validation)
are already consolidated at their true owners (`utils/imports.py::require_optional_module`,
Django's own `HttpRequest.get_host()`, consumers-owned transport policy) with routers.py as pure
composition. Deferred: full pytest run (not authorized this cycle); no tracked edits made, so no
format/lint pass was required.

## Judgment

The file is a boundary stone, not a policy holder: it names and composes pieces owned elsewhere,
fails loudly at construction with messages that carry their own repair recipes, and caches its one
class so simulated-absence tests stay honest. Its apparent duplications dissolve under the
single-edit-site test into either single-site ownership or deliberate multi-medium agreement with
active enforcement. Zero-edit result; the strongest candidate is recorded with the measurements that
rejected it.
