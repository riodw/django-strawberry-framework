# Rationale: spec-047 — Execution resource policy (deliberation and rejected alternatives)

Deliberative companion to [`spec-047-resource_policy-0_0_14.md`][spec-047]. The spec is the
contract; this file holds the alternatives each decision rejected and the derivations that do
not change how a decision is implemented. A decision with no entry here has nothing beyond its
contract.

## Decision entries

### Decision 1 — One immutable frozen dataclass, validated at construction

Spec: [Decision 1][spec-047-d1].

*Alternatives rejected.* A settings-dict read per bound (unrelated settings reads scattered
across resolvers, each validating on its own terms). A mutable dataclass with a `freeze()` call
(the unfrozen window is the bug). Pydantic (a new hard dependency for one object).

### Decision 2 — Armed for the operation, published on the request context

Spec: [Decision 2][spec-047-d2].

*Alternatives rejected.* The context stash as the sole authority: it is visible to the
consumer's context object and reuses the package's one context seam, but `info.context` is
writable by every resolver in the request, so a design that reads a bound back out of it lets
any resolver widen that bound or clear its own deadline. The keys stay published as a mirror,
and the shape-agnostic dispatch stays the one shared seam; enforcement reads neither. A
thread-local (wrong under async): a `ContextVar` is per-task under asyncio and propagates
across the `sync_to_async` boundary a Django resolver actually crosses.

*Why the context dispatch is shared rather than copied.* The shape-agnostic read / write /
delete dispatch handles the four context shapes and is the single place a new shape lands, so
a second copy beside the policy helpers would be the first place the optimizer and the policy
could drift on which shapes they accept. It lives in `utils/context.py`; the optimizer module
keeps its keys and its reset and re-exports the helpers.

### Decision 3 — The document text scan runs BEFORE the parse

Spec: [Decision 3][spec-047-d3].

*Alternatives rejected.* `parse_options["max_tokens"]` (loses the typed code; see the
Borrowing posture entry below). A `ValidationRule` for depth (runs after the parse). A regex or
`str.count` over the document (a brace inside a string literal is not a brace; the lexer knows
the difference).

### Decision 4 — The document and value budgets are one iterative walk

Spec: [Decision 4][spec-047-d4].

*Alternatives rejected.* A `ValidationRule` (no access to variables, which is where most of an
input payload arrives). Charging only variables and ignoring literals (a literal object is a
value too). Recursion with a depth guard (a depth guard on a walker that exists to bound depth
is circular).

*Why the walk keeps no `id()`-keyed charge-once cache.* One request-lifetime set of
already-charged `id()` values would serve as both cycle guard and charge-once cache, and it
fails at both jobs:

- **An `id()` is unique only among LIVE objects.** The values this walk reads are temporaries;
  freeing one list lets the next same-sized list reuse its address, so an `id()`-keyed set
  reports a *fresh* container as already charged. graphql-core's `value_from_ast_untyped`
  builds fresh same-size lists whose ids recycle through CPython's free list, so thousands of
  relation ids would be charged as dozens.
- **Charge-once is not the contract.** One variable spliced into two mutation fields resolves
  to the same Python list both times, so charge-once would make the second field's relation ids
  free and the aggregate bound would never fire.

A cycle guard needs ancestor-scoped lifetime and owning references; a charge-once cache needs
neither, and charging once is not wanted at all. The ancestor path is the same shape the
document walk uses for fragment spreads (a `path` carried on the stack), with object identity
in place of fragment names.

### Decision 5 — `DEFAULT_RELATION_SHAPE` becomes `"connection"`: a clean alpha break

Spec: [Decision 5][spec-047-d5].

*Alternatives rejected.* A one-release deprecation warning while still emitting both (keeps the
bypass, and a warning nobody reads is not a mitigation). A settings flag to restore the old
default (a global switch that re-opens a security default is the worst of both — it is
invisible in the schema, unlike a `Meta` key). Leaving the default and relying on the row bound
alone (bounding the sibling is not the same as not having it: the sibling has no cursor, so a
client can only ever read the first N rows of it, which is a worse API *and* still unbounded
across aliases).

*The derivation.* Every argument for a shim is an argument for keeping the bypass reachable on
schemas that never asked for it, and a shim that emits both shapes *is* the insecure default
under another name. The migration is one line per relation and it is discovered at schema
build rather than at runtime.

### Decision 8 — `max_collection_cost` is a SHAPE bound, and its default says so

Spec: [Decision 8][spec-047-d8].

*Why the default is `1_000_000_000`.* A legitimate four-level document that leaves every page
unspecified already charges `10**8`, and a bound that rejects ordinary documents is a bound the
first deployment to meet it raises to infinity. The generous default keeps the bound credible;
the row promise is carried by `max_page_size` and `max_list_rows`, which the spec states.

### Decision 9 — The execution deadline is cooperative, and says so

Spec: [Decision 9][spec-047-d9].

*Why the default is `None`.* A wall-clock deadline a deployment did not choose is a correctness
hazard (it truncates legitimate slow requests), not a safety one — the opposite of every other
bound here, which is why it is the only optional one. The failure mode of a too-generous bound
is a slow request; the failure mode of an unchosen deadline is a wrong answer.

### Decision 11 — One typed rejection, and no per-transport translation

Spec: [Decision 11][spec-047-d11].

*Why enforcement is built by the schema rather than left to the consumer.* An endpoint whose
only limiter is one a consumer remembered to install is an endpoint with no limiter. This is
the same reasoning that rejected upstream's three-extensions shape in the Borrowing posture
entry below. Building the extension from the schema's own record, rather than accepting it as
an entry, is what keeps the object that bounds the next operation out of reach of
`info.schema.extensions`.

### Decision 13 — What this policy does not bound, and why each boundary is deliberate

Spec: [Decision 13][spec-047-d13].

*The upstream forensics behind the subscription envelope.* Enforcement is not the gap;
rendering is. A subscription enters `extensions_runner.operation()` and `executing()` exactly as
a query does, so both the document text scan and the value walk run and a violating subscription
is refused. The difference is one `except` clause in upstream's schema: the **non-streaming**
path wraps its whole operation block in a broad `except Exception` that returns a
`PreExecutionError`, so an HTTP or WebSocket query or mutation carries an `errors` entry; the
**streaming** path's only pre-execution `except` names three errors (`MissingQueryError`,
`CannotGetOperationTypeError`, `InvalidOperationTypeError`), so anything an extension raises
escapes it. Upstream's `BaseGraphQLTransportWSHandler.run_operation` then catches that exception,
hands it to `handle_task_exception`, and sends `complete`.

*The version-drift evidence for "state the behaviour, never the private method name".* The
declared floor is `strawberry-graphql>=0.322.2` with no ceiling, and upstream has moved this
seam between releases: the private implementation was `_subscribe` at `0.316.0` and is
`_stream` at `0.323.2`, and the public attribute a handler dispatches through moved from
`subscribe` to `stream` at `0.319.0`. [`spec-046`][spec-046]'s stop-aware result source wraps
both public names rather than testing a version for the same reason.

## Deliberation that belongs to no single decision

### Borrowing posture — what was deliberately not borrowed

Strawberry ships `MaxTokensLimiter`, `MaxAliasesLimiter` and `QueryDepthLimiter`; the spec
states what was borrowed from them and that the package declines their shape. The reasons each
was declined:

- **Three extensions a consumer must remember.** Optional, consumer-installed, none installed by
  default is the same as absent. One policy object and one extension `DjangoSchema` builds into
  every operation is the answer.
- **`parse_options["max_tokens"]`.** Upstream routes its token limit into graphql-core's parser,
  which answers with a `GraphQLSyntaxError` carrying no code — indistinguishable to a client from
  a typo. This package counts tokens itself so the rejection carries the same typed code as every
  other bound.
- **Depth measured on the AST.** Upstream's `QueryDepthLimiter` is a validation rule, so it runs
  *after* the parse it would need to protect.

### Risks and open questions — the fallback positions

The spec keeps each preferred answer; the fallbacks it would take if a preferred answer failed
are here.

- **`max_collection_cost`'s default is generous by design.** Fallback if deployments report the
  compounding is still too permissive: a per-level multiplier cap, which bounds nesting directly
  rather than through a product.
- **Response-byte accounting is out of scope.** Fallback: the deployment's reverse proxy, which
  already bounds response size.
- **The `ids` argument-name rule** is the walker's one name-based classification. Fallback: a
  marker on the generated field that the walker reads instead of the argument name.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-046]: ../spec-046-transport_security-0_0_14.md
[spec-047]: ../spec-047-resource_policy-0_0_14.md
[spec-047-d1]: ../spec-047-resource_policy-0_0_14.md#decision-1--one-immutable-frozen-dataclass-validated-at-construction
[spec-047-d11]: ../spec-047-resource_policy-0_0_14.md#decision-11--one-typed-rejection-and-no-per-transport-translation
[spec-047-d13]: ../spec-047-resource_policy-0_0_14.md#decision-13--what-this-policy-does-not-bound-and-why-each-boundary-is-deliberate
[spec-047-d2]: ../spec-047-resource_policy-0_0_14.md#decision-2--armed-for-the-operation-published-on-the-request-context
[spec-047-d3]: ../spec-047-resource_policy-0_0_14.md#decision-3--the-document-text-scan-runs-before-the-parse
[spec-047-d4]: ../spec-047-resource_policy-0_0_14.md#decision-4--the-document-and-value-budgets-are-one-iterative-walk
[spec-047-d5]: ../spec-047-resource_policy-0_0_14.md#decision-5--default_relation_shape-becomes-connection-a-clean-alpha-break
[spec-047-d8]: ../spec-047-resource_policy-0_0_14.md#decision-8--max_collection_cost-is-a-shape-bound-and-its-default-says-so
[spec-047-d9]: ../spec-047-resource_policy-0_0_14.md#decision-9--the-execution-deadline-is-cooperative-and-says-so

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
