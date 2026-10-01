# Rationale: spec-044 — Response-extensions debug middleware (rejected alternatives)

Deliberative companion to [`spec-044-debug_extension-0_0_14.md`][spec-044]. The spec is the
contract; this file holds the alternatives each decision rejected and why each lost, plus the
derivations that do not change how a decision is implemented. A reader looking for what the
extension *does* wants the spec.

## Decision entries

### Decision 1 — Spec filename and canonical naming

Spec: [Decision 1][s44-d1].

Alternatives considered (and rejected):

- **`spec-044-response_extensions_debug-0_0_14.md`.** Rejected: the long
  slug restates the mechanism twice (`response_extensions` + `debug`); the
  established slug style is short subject-first (`debug_toolbar`,
  `channels_router`, `test_client`).
- **`spec-044-debug_middleware-0_0_14.md`.** Rejected: "middleware" is the
  card title's graphene-inherited word, and the shipped shape is a
  `SchemaExtension` — naming the file after the rejected shape would mislead
  every future grep.

### Decision 2 — Card-scope boundary: the extension ships alone — no Django middleware, no schema field, no fakeshop always-on wiring

Spec: [Decision 2][s44-d2].

Justification: each excluded piece has its own owner — the toolbar is its own
card, the schema-field exposure is a rejected alternative, and the fakeshop
activation line item lives on the beta board. Alternative considered (and
rejected): **bundling a fakeshop demo field or dev-settings toggle** — scope
creep that turns a one-module card into an example-project design discussion;
the probe-URLconf tests demonstrate the wiring shape a consumer copies.

### Decision 3 — Exposure: the response-`extensions` map under the `debug` key, not a schema-level `_debug` field

Spec: [Decision 3][s44-d3].

Alternatives considered (and rejected):

- **The graphene schema-level `_debug` field.** Rejected: everything in
  ground 2, plus a mechanism problem — a field resolver cannot know when the
  operation's *other* fields have finished executing, which is why graphene
  needs its promise-chained `get_debug_result()` dance
  ([`middleware.py`][upstream-debug-middleware] `::DjangoDebugContext`); the
  operation hook gets completion for free. The selectivity loss (the map is
  all-or-nothing per enabled schema, where graphene consumers pull only
  `{ _debug { sql } }` per query) is real and recorded in
  [Risks][s44-risks].
- **Both at once.** Rejected: two exposure surfaces for one payload doubles
  the documentation and test matrix for zero new capability; a future card
  can add the field flavor over the same capture core if a consumer asks.

### Decision 4 — Fidelity: Django's own debug cursor via a `force_debug_cursor` bracket, not a cursor-wrap port

Spec: [Decision 4][s44-d4]. The cursor-wrap-port and direct-`CaptureQueriesContext` rejections
stay in the spec because each carries a constraint an implementer must keep.

Alternative considered (and rejected):

- **Read bare `connection.queries` without the bracket.** Rejected: the
  `DEBUG=False` silent-empty trap the spec's Decision 4 and `## Current state`
  both state — a correctness bug dressed as simplicity.

### Decision 5 — Symbol and home: `DjangoDebugExtension` in `extensions/debug.py`, exported from the `extensions` subpackage — never the package root

Spec: [Decision 5][s44-d5].

Alternatives considered (and rejected):

- **Package-root export beside `DjangoOptimizerExtension`.** Rejected per
  ground 2 — and the asymmetry is informative rather than confusing: the
  import path itself signals "this one is not part of the default recipe".
- **`optimizer/debug.py`.** Rejected: the debug extension is not optimizer
  machinery (it reports *all* SQL, planned or not), and the `extensions/`
  subpackage is its natural home.
- **Naming the module `extensions/debug_extension.py`.** Rejected: the
  subpackage already says `extensions`; `debug.py` matches upstream
  strawberry-django's `middlewares/debug_toolbar.py` leaf-naming style the
  package adopted for `middleware/debug_toolbar.py`.

### Decision 6 — Opt-in shape: pass the class — one fresh instance per operation requires Strawberry 0.316.0

Spec: [Decision 6][s44-d6].

Alternatives considered (and rejected):

- **Documenting the optimizer's singleton-in-a-factory shape.** Rejected:
  there is no cross-request cache to preserve. A shared entry is still
  answered per operation under a `DjangoSchema`, through the package runner's
  operation state, but on a plain `strawberry.Schema` a shared instance is
  outside the isolation guarantee — so the class (or a fresh factory) is the
  one documented spelling.
- **A floor below `0.316.0` with the class form.** Rejected: those releases
  cache the resulting sync instance, so class syntax alone does not provide
  isolation.
- **Guard against shared instances at runtime** (e.g. detect a second
  concurrent `on_operation` on one instance and raise). Rejected: the
  engine already owns instance lifecycle and deprecation signaling for the
  bare-instance form; a package-side tripwire would fire only in the
  misuse case it documents away, and false-positive risk (serialized
  sequential operations on one instance are harmless) outweighs the catch.

### Decision 7 — Hook shape: one sync `on_operation` generator, assembly at teardown, `get_results` returns the stash

Spec: [Decision 7][s44-d7].

Alternatives considered (and rejected):

- **Assemble inside `get_results`.** Rejected per ground 2: on the
  early-error paths it would read a bracket that has not restored yet, and
  it would need its own idempotence guard for the paths where the engine
  calls it after teardown anyway.
- **`resolve`-hook accumulation (graphene's mechanism).** Rejected: the
  per-resolver hook exists for per-field concerns; SQL is per-operation and
  exceptions already accumulate on the result. A `resolve` implementation
  would also put the extension on the engine's per-field hot path
  (`_implements_resolve` adds the middleware wrapper) for pure overhead.
- **An `async def on_operation` twin class** for async schemas. Rejected:
  ground 1 makes it unnecessary; the async-color SQL fidelity gap is a
  thread-locality property, not a hook-color property
  ([Edge cases][s44-edge-cases]), so an async hook would not close it anyway.

### Decision 8 — The SQL row shape: graphene's wire names, narrowed to what Django's log supports

Spec: [Decision 8][s44-d8]. The casing-helper rejection below is also an instruction in the
spec's DRY D4 (the six wire keys spelled as literals) and in its Test plan's
independent-literals rule.

Alternatives considered (and rejected):

- **snake_case keys** (the Python-side names). Rejected: the payload is
  wire, not Python; a migrant's existing DevTools formatter reads `isSlow`.
- **Carrying `startTime` / `stopTime` measured by the extension around the
  whole operation.** Rejected: per-operation stamps on per-query rows would
  be actively misleading — worse than absent.
- **A `time` string field mirroring Django's raw log entry.** Rejected:
  duplicates `duration` in a worse type; anyone needing Django's exact
  string can reformat.
- **Deriving the camelCase keys through `utils/strings.graphql_camel_name`.**
  Rejected: the six keys are a **wire contract** — a graphene migrant's
  existing DevTools formatter parses these exact bytes — so they must not be
  a function of a casing helper's future acronym/underscore behavior. They
  are spelled as literals inside the one row serializer
  ([DRY D4][s44-dry]), and the mechanics tests
  re-spell them as independent literals for the same reason
  ([Test plan][s44-test-plan]).

### Decision 9 — Exception capture: the result's `original_error` chain, serialized like graphene's `wrap_exception` — no resolver wrapping

Spec: [Decision 9][s44-d9].

Alternatives considered (and rejected):

- **A `resolve` hook capturing exceptions per field.** Rejected per
  ground 1.
- **Serializing every outer result `GraphQLError`** (no `original_error`
  gate). Rejected per ground 2 — it would spam the list with validation
  entries the standard `errors` array already carries. This is distinct from
  retaining a terminal `GraphQLError` reached through a non-`None` original
  link, which proves it was raised during resolver execution.
- **Capturing exceptions the resolvers swallowed** (graphene cannot either).
  Out of scope by construction: only errors that reached the result exist
  to report.

### Decision 10 — Multi-database capture: every alias in `connections.all()`, one bracket each

Spec: [Decision 10][s44-d10].

Alternatives considered (and rejected): **bracketing only
`connections["default"]`** — rejected, silently blind on sharded setups;
**lazily bracketing on first use via the `connection_created` signal** —
rejected, misses the common case of aliases whose connections already exist
from prior requests, and signal (dis)connection per operation is its own
leak surface.

### Decision 11 — Test strategy: split live HTTP behavior from package-tier mechanics

Spec: [Decision 11][s44-d11].

Alternatives considered (and rejected):

- **Enable the extension in fakeshop's shipped schema so tests go live.**
  Rejected in [Decision 2][s44-d2] — every acceptance response pays body
  weight and capture cost, and the example stops modeling the off-by-default
  posture.
- **Put all scenarios in the card's predicted `tests/extensions/` path.**
  Rejected: a live `/graphql/` request belongs to `test_query/` under the
  explicit repository rule. Predicted paths guide planning; they do not
  authorize a placement exception.
- **In-process `schema.execute_sync` instead of HTTP.** Rejected for the
  request-driving group (HTTP exercises the serialization of `extensions`
  into the response body — JSON round-trip included); retained where it is the
  *point* — the async-color scenario drives in-process async execution
  precisely because Django's async test client cannot change the
  thread-locality story the scenario documents.

### Decision 12 — This card completes the joint `0.0.14` cut and owns the version bump

Spec: [Decision 12][s44-d12].

Alternatives considered (and rejected):

- **Defer to yet another card.** Rejected: no later `0.0.14` card existed; a
  deferral would have orphaned the cut the three predecessors were waiting on.
- **Bump in Slice 1.** Rejected: the version moves only after the feature and
  docs are complete, and a Slice-1 bump would have published `0.0.14`
  identity while `044`'s own surface was mid-flight.

## Risks and open questions

Spec: [Risks and open questions][s44-risks].

**The async SQL-capture follow-on must be decided against a real ASGI-request prototype, not
prose.** Routing the bracket through `sync_to_async(thread_sensitive=True)` is not ruled out by
the claim that thread-sensitive work always shares one process-wide thread: that is only
asgiref's *fallback*. Django's ASGI handler wraps each HTTP request in a
`ThreadSensitiveContext`, which selects a per-request single-thread executor, so worker-thread
bracketing **may be viable** for normal ASGI HTTP inside the inherited request context. It is
still not universal — direct `schema.execute()`, batching, a generated mutation's transaction
window (which runs on a private thread of its own,
`django_strawberry_framework/schema.py::DjangoMutationExecutionContext`), and work escaping that
context lack the per-request executor. The shipped "async SQL is typically empty" limitation
stands either way.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[s44-d1]: ../spec-044-debug_extension-0_0_14.md#decision-1--spec-filename-and-canonical-naming
[s44-d10]: ../spec-044-debug_extension-0_0_14.md#decision-10--multi-database-capture-every-alias-in-connectionsall-one-bracket-each
[s44-d11]: ../spec-044-debug_extension-0_0_14.md#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics
[s44-d12]: ../spec-044-debug_extension-0_0_14.md#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump
[s44-d2]: ../spec-044-debug_extension-0_0_14.md#decision-2--card-scope-boundary-the-extension-ships-alone--no-django-middleware-no-schema-field-no-fakeshop-always-on-wiring
[s44-d3]: ../spec-044-debug_extension-0_0_14.md#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field
[s44-d4]: ../spec-044-debug_extension-0_0_14.md#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port
[s44-d5]: ../spec-044-debug_extension-0_0_14.md#decision-5--symbol-and-home-djangodebugextension-in-extensionsdebugpy-exported-from-the-extensions-subpackage--never-the-package-root
[s44-d6]: ../spec-044-debug_extension-0_0_14.md#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160
[s44-d7]: ../spec-044-debug_extension-0_0_14.md#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash
[s44-d8]: ../spec-044-debug_extension-0_0_14.md#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports
[s44-d9]: ../spec-044-debug_extension-0_0_14.md#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping
[s44-dry]: ../spec-044-debug_extension-0_0_14.md#helper-reuse-obligations-dry
[s44-edge-cases]: ../spec-044-debug_extension-0_0_14.md#edge-cases-and-constraints
[s44-risks]: ../spec-044-debug_extension-0_0_14.md#risks-and-open-questions
[s44-test-plan]: ../spec-044-debug_extension-0_0_14.md#test-plan
[spec-044]: ../spec-044-debug_extension-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-debug-middleware]: ../../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/middleware.py
