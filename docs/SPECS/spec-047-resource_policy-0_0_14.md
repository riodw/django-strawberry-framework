# Spec: Execution resource policy — one immutable budget, one value-cardinality walker, bounded collections

Targeted at `0.0.14` (card [`DONE-047-0.0.14`][kanban]). This is **card 2 of the
four-card security-remediation program** derived from the hardening audit in
[`docs/feedback2.md`][feedback2]; it closes that audit's **S3** (no coherent resource
budget for query and response work) and **S4** (unbounded variable-driven input
cardinality). It depends on [`spec-046`][spec-046], which corrected the transports every
bound here is consumed by; cards [`DONE-048-0.0.14`][kanban] (secure output and
error defaults) and [`WIP-ALPHA-049-0.0.14`][kanban] (dependency / CI hygiene) follow.

Deliberation, rejected alternatives, and this spec's change record live in its companion
[`spec-047-resource_policy-0_0_14-rationale.md`][rationale].

**`docs/feedback2.md` is review evidence this spec references, not a substitute for it.**
The audit established the facts; every decision, default number, public-API shape,
compatibility promise, and test row below is this spec's own.

**This card contains an intentional, documented alpha breaking change**
([Decision 5](#decision-5--default_relation_shape-becomes-connection-a-clean-alpha-break)):
the package default for a many-side relation on a Relay-Node-shaped type moves from
`"both"` to `"connection"`, so a schema that relied on the generated raw list sibling must
now ask for it. The package's documented API freeze begins at `1.0.0`, and card 046
already set the precedent that correcting a confirmed security-boundary default during
alpha outranks migration convenience.

Status: **SHIPPED — all five slices are built and released.** The `Status:` line is the
completion source of truth (the shipped-spec convention); the Slice checklist below
records the same state.

**Version boundary** (see
[Decision 12](#decision-12--the-version-bump-belongs-to-the-0014-joint-cut)):
this card targets `0.0.14`, the patch its three program siblings and cards 041-045 also
target. The version quintet already reads `0.0.14`, so there is no bump for this card to
take; the [joint version cut][glossary-joint-version-cut] rule assigns the release wording
to the last card of that shared line to land. Slice 5 folds documentation in only.

Permission caveat: [`AGENTS.md`][agents] prohibits `CHANGELOG.md` edits without explicit
permission. This card's Slice 5 does **not** claim that permission — the release entry is
the maintainer's.

## Key glossary references

Terms this spec relies on (statuses per [`docs/GLOSSARY.md`][glossary]):

- [`DjangoListField`][glossary-djangolistfield] — the raw-list field whose unbounded
  queryset evaluation is half of S3's evidence; it gains a required effective bound.
- [`DjangoConnectionField`][glossary-djangoconnectionfield],
  [Relay Node integration][glossary-relay-node-integration],
  [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] —
  the bounded collection surface the policy becomes a ceiling over.
- [`Meta.relation_shapes`][glossary-metarelation_shapes],
  [Relation handling][glossary-relation-handling] — the vocabulary whose default flips.
- [`DjangoNodesField`][glossary-djangonodesfield] — ships the `ids:` list S4 names, and
  the standing note that request-size limiting belongs to the transport layer; this card
  is what makes cardinality limiting belong to the package.
- [`Upload` scalar][glossary-upload-scalar],
  [Request-body cap][glossary-request-body-cap] — the body ceiling that deliberately does
  **not** measure a multipart body, which is why upload count and bytes are budgeted here.
- [`FilterSet`][glossary-filterset], [`RelatedFilter`][glossary-relatedfilter],
  [`filter_input_type`][glossary-filter_input_type] — the generated `and` / `or` / `in`
  surface the value walker charges.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension],
  [Plan cache][glossary-plan-cache],
  [Strictness mode][glossary-strictness-mode] — the subsystem whose request-context seam
  the policy mirrors.
- [`ConfigurationError`][glossary-configurationerror] — the typed construction-time
  failure for an invalid bound.
- [`SerializerMutation`][glossary-serializermutation],
  [`DjangoMutation`][glossary-djangomutation],
  [`DjangoModelFormMutation`][glossary-djangomodelformmutation] — the write surfaces whose
  relation-id and nested-row payloads the walker charges.
- [`strawberry_config`][glossary-strawberry_config],
  [Strawberry extension lifecycle][glossary-strawberry-extension-lifecycle],
  [Per-operation extension isolation][glossary-per-operation-extension-isolation] — the
  schema-construction and per-request surfaces the enforcement extension plugs into.
- [`TestClient`][glossary-testclient], [Probe URLconf][glossary-probe-urlconf],
  [`seed_data`][glossary-seed_data],
  [Live-first coverage mandate][glossary-live-first-coverage-mandate] — the test tiers and
  disciplines that decide where each regression lives.
- [Joint version cut][glossary-joint-version-cut] — the release rule this card is subject
  to, sharing the `0.0.14` line with cards 041-046, 048 and 049.
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] — the hook whose
  refuse-a-sliced-source contract dictates where the row bound may be applied.

Terms this spec ADDS to the glossary in Slice 5:
[Execution resource policy][glossary-execution-resource-policy] (the capability),
[`ResourcePolicy`][glossary-resourcepolicy] (the budget object),
[`DjangoResourcePolicyExtension`][glossary-djangoresourcepolicyextension] (the enforcement
extension), and [Value-budget walker][glossary-value-budget-walker] (the S4 pass).

## Slice checklist

Each top-level item maps to one commit / PR.

- [x] **Slice 1 — the policy object and its threading**
      `resource_policy.py` ([`ResourcePolicy`][glossary-resourcepolicy], `DEFAULT_RESOURCE_POLICY`,
      `ResourceLimitExceeded`, `resolve_resource_policy`, the context helpers,
      `effective_bound`, `bounded_rows`, `check_deadline`), the `RESOURCE_POLICY` settings
      key, and the shared context dispatch lifted to `utils/context.py`.
- [x] **Slice 2 — the enforcement extension**
      `extensions/resource_policy.py`: the pre-parse text scan, the iterative
      fragment-expanding document walk, and the iterative cycle-safe value walker.
      `DjangoSchema` resolves the policy once and installs the extension.
- [x] **Slice 3 — bounded collections**
      `DjangoListField`'s `max_rows` / `trusted_max_rows`, the generated many-side relation
      resolver's row bound, and the policy ceiling over `relay_max_results`.
- [x] **Slice 4 — the secure relation-shape default**
      `DEFAULT_RELATION_SHAPE` becomes `"connection"`; the example project's explicit
      `"both"` opt-ins; every re-pinned test.
- [x] **Slice 5 — docs fold-in**
      `docs/GLOSSARY.md`, `docs/TREE.md`, and `KANBAN.md`. The version quintet is the
      joint cut's, not this slice's.

## Problem statement

A GraphQL endpoint's cost is not bounded by its schema. Two independent gaps made that
concrete in this package.

**S3 — no coherent budget for query and response work.** Neither the package nor the
example project installed a token, depth, complexity, or selection-count limiter. There
was no page-size ceiling beyond Strawberry's own `relay_max_results`, no raw-list row
bound at all, and no aggregate budget across a request.
[`DjangoListField`][glossary-djangolistfield] evaluated an unrestricted queryset, and
`DEFAULT_RELATION_SHAPE = "both"` emitted a raw many-side list *beside* the bounded
connection — so a client that found the connection capped simply selected the list
sibling. A generated-SDL probe confirmed both shapes present across the example schema,
alongside three root `DjangoListField` surfaces. The optimizer reduces query *count*; it
bounds neither database work, serialized rows, Python memory, nor response bytes. A deeply
nested document can additionally drive graphql-core's recursive parser and the package's
own walkers toward the interpreter's recursion limit.

**S4 — unbounded variable-driven input cardinality.** Document limits do not constrain
values supplied through variables, and a tiny document can carry an enormous payload: an
unlimited `ids:` list through [`DjangoNodesField`][glossary-djangonodesfield] (which
preserves duplicates positionally, so the framework decodes, stores, reassembles and
serializes every position even where the database would collapse the `IN`), unlimited `in`
lookup values, an `and` / `or` filter tree whose depth is capped but whose width and node
count are not, unlimited M2M ids in generated model / form / serializer mutations, wide
nested serializer lists, and multipart uploads with no package-owned count, per-file, or
aggregate byte cap. Such inputs exceed database parameter limits, build very large SQL
statements, hold write locks, and consume memory before the ORM is reached.

The two gaps share one root cause and therefore one correction: **there was no object that
knew what a request was allowed to spend.**

## Current state

Shipped before this card:

- `DjangoConnectionField` respects Strawberry's `relay_max_results` (default 100) and the
  package's window planner honors the same cap on nested connections.
- `views.py` enforces a cumulative request-**body** ceiling
  ([Request-body cap][glossary-request-body-cap], spec-046 Decision 7), with a deliberate
  multipart carve-out: a multipart body is never materialized there, so per-file count,
  per-file size, and aggregate upload size are explicitly out of that cap's scope.
- `optimizer/_context.py` threads plan / elision / strictness state through the request
  context under `DST_OPTIMIZER_*` keys.
- `conf.py` reads a small set of namespaced settings and validates none of their domains —
  each consumer validates its own.

Not shipped, and what this card adds: any notion of a per-request budget; any bound on
document tokens, depth, expanded selections, aliases, or aggregate collection cost; any
bound on raw-list rows; any bound on input cardinality of any kind; any typed rejection
for exceeding one.

## Goals

1. **One immutable object** owns every bound, normalized and validated once at schema
   construction and threaded through the request context — not a scatter of settings reads
   across resolvers.
2. **Rejection before work.** A request that exceeds a bound is refused before any id is
   decoded, any queryset is built, and any row is fetched. **Uploads are the one bound
   charged post-materialization**, and the goal is narrowed accordingly: Django's upload
   handlers have already streamed a multipart body to memory or to a temporary file by the
   time GraphQL-coerced values exist, so the upload bounds refuse before any resolver,
   serializer, validator, or storage backend touches those files — not before the bytes
   were received. Bounding the receipt itself is a transport concern the package
   deliberately does not reach into
   ([Non-goals](#non-goals), spec-046's body cap).
3. **Fail-closed defaults.** Every bound has a package default; there is no spelling that
   disables one; a context with no published policy reads back the package defaults rather
   than "unbounded".
4. **One typed rejection**, identical on sync HTTP, async HTTP, and both WebSocket
   protocols.
5. **Narrowing-only per field**, with the schema-construction policy as the single trusted
   declaration that may widen.
6. **No unbounded collection remains reachable**: connections keep their cap, raw lists
   gain one, and the list-beside-connection bypass is closed at the schema level.

## Non-goals

- **A preemptive timeout.** The optional deadline is cooperative
  ([Decision 9](#decision-9--the-execution-deadline-is-cooperative-and-says-so)); nothing
  in-process can interrupt a query already handed to a database driver.
- **A cost model per field or per resolver.** Field-level cost annotation
  (`@cost(complexity: …)`) is a larger surface with its own directive vocabulary; this card
  charges structure and cardinality, which is what the audit's evidence names.
- **Response-byte accounting.** Bounding serialized output requires a serialization-time
  hook and a partial-response policy; it is out of scope and recorded in
  [Risks and open questions](#risks-and-open-questions).
- **Replacing the transport body cap.** The two are complementary: the JSON body is
  allocated and parsed before GraphQL-coerced values exist, so S2's cap remains necessary.
- **Persisted-query allow-lists**, which are the other way to bound documents and a
  different feature.

## Borrowing posture

Strawberry ships `MaxTokensLimiter`, `MaxAliasesLimiter`, and `QueryDepthLimiter`;
graphene-django ships none of the three. Under the package's
[Single-upstream parity][glossary-single-upstream-parity] rule that makes document limiting
an optional capability — and the audit's finding is precisely that "optional, consumer-
installed, three separate extensions, none installed by default" is the same as absent.

What is borrowed:

- **The mechanism.** Enforcement is a `SchemaExtension` and the rejection is a
  `GraphQLError`, exactly as upstream's limiters do it. That is what buys transport parity
  for free: every transport already renders a `GraphQLError`.
- **`MaxAliasesLimiter`'s fragment-expansion shape.** Counting per spread site, with a
  fragment map built once, is upstream's approach and the correct one.

What is deliberately **not** borrowed: upstream's three-extension shape, its
`parse_options["max_tokens"]` routing, and its AST-measured depth. This package installs
**one** extension from `DjangoSchema` itself, counts tokens itself so the rejection carries
the same typed code as every other bound, and charges depth before the parse
([Decision 3](#decision-3--the-document-text-scan-runs-before-the-parse)). Why each was
declined is in the [rationale][rationale].

Nothing about input cardinality, raw-list rows, or the relation-shape default has an
upstream analogue in either package; those are this package's own.

## User-facing API

### The policy object

```python
from django_strawberry_framework import DjangoSchema, ResourcePolicy

schema = DjangoSchema(
    query=Query,
    mutation=Mutation,
    resource_policy=ResourcePolicy(max_page_size=50, max_depth=12),
)
```

`resource_policy=` also accepts a plain mapping of bound names to values, applied over the
package defaults, so a deployment overrides only what it cares about.

### The setting

```python
DJANGO_STRAWBERRY_FRAMEWORK = {
    "RESOURCE_POLICY": {"max_page_size": 50, "execution_deadline_seconds": 10},
}
```

Precedence, highest first: the `DjangoSchema(resource_policy=…)` argument, the setting, the
package defaults. Both override sources are *trusted declarations* and may widen a default.

### The bounds and their defaults

| Bound | Default | What it charges |
|---|---|---|
| `max_document_tokens` | `4_000` | Lexical tokens in the raw document, before the parse. |
| `max_depth` | `20` | Structural nesting (`{`, `(`, `[`), before the parse. |
| `max_selections` | `500` | Field selections after fragment expansion. |
| `max_aliases` | `100` | Aliased selections after fragment expansion. |
| `max_collection_cost` | `1_000_000_000` | Multiplicative row cost of the document. |
| `max_page_size` | `100` | Ceiling over a connection's effective `relay_max_results`. |
| `max_list_rows` | `100` | Rows a raw (non-Relay) list field may evaluate. |
| `max_input_nodes` | `5_000` | Every scalar / list / object node in the argument values. |
| `max_container_width` | `1_000` | The widest single list or input object. |
| `max_value_depth` | `20` | The deepest chain of nested lists / input objects in one value. |
| `max_membership_items` | `500` | Items in one membership (`in`) list. |
| `max_node_ids` | `200` | Ids in one Relay node-refetch list. |
| `max_relation_ids_per_mutation` | `200` | Relation ids in one mutation field. |
| `max_relation_ids_total` | `1_000` | Relation ids across the whole request. |
| `max_nested_rows` | `200` | Rows in one nested input-object list. |
| `max_upload_count` | `10` | Files in the request. |
| `max_upload_file_bytes` | `10 MiB` | Bytes in the largest single file. |
| `max_upload_total_bytes` | `25 MiB` | Bytes in all files together. |
| `max_scalar_bytes` | `65_536` | UTF-8 bytes in one scalar value. |
| `execution_deadline_seconds` | `None` | Optional cooperative wall-clock budget. |

### The rejection

```json
{
  "data": null,
  "errors": [
    {
      "message": "Request exceeds the max_node_ids resource bound: a node-refetch id list is longer than the policy allows (201 charged, 200 allowed).",
      "extensions": {
        "code": "RESOURCE_LIMIT_EXCEEDED",
        "bound": "max_node_ids",
        "limit": 200,
        "charged": 201
      }
    }
  ]
}
```

`RESOURCE_LIMIT_ERROR_CODE` is exported so a consumer can compare against a constant.
`ResourceLimitExceeded` multiple-inherits `graphql.GraphQLError` and the package base, so
it is catchable both ways.

### The field bound

```python
@strawberry.type
class Query:
    branches: list[BranchType] = DjangoListField(BranchType, max_rows=25)
```

`max_rows=None` (the default) means "the request policy governs", **not** "no bound".
`trusted_max_rows=True` is the explicit widening opt-in.

### The relation-shape default

```python
class CategoryType(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name", "items")
        interfaces = (relay.Node,)
        relation_shapes = {"items": "both"}   # NEW: required to keep the raw list sibling
```

## Architectural decisions

### Decision 1 — One immutable frozen dataclass, validated at construction

`ResourcePolicy` is a frozen dataclass whose `__post_init__` validates every field. Three
properties follow, and each is load-bearing:

- **Validated once.** An invalid deployment fails at schema construction with a
  [`ConfigurationError`][glossary-configurationerror] naming the offending bound, not on
  the first request that reaches the resolver reading it.
- **One gate, not two.** Validation lives in `__post_init__` rather than in the settings
  reader, so a policy built from a mapping, from an explicit instance, or as a narrowed
  copy is validated on identical terms. Two gates drift.
- **Immutable at request time.** A resolver that holds the request's policy cannot widen
  its own budget by mutating it.

`bool` is rejected explicitly at every integer bound. `isinstance(True, int)` is `True`, so
a bound accepting `True` would silently become `1` — a bound so tight it presents as an
unrelated bug.

*Alternatives rejected: see the [rationale][rationale] (a per-bound settings read, a
mutable dataclass with `freeze()`, Pydantic).*

### Decision 2 — Threaded through the request context, mirroring the optimizer seam

The resolved policy is stashed under `DST_RESOURCE_POLICY` at the start of every operation
and read back by `resource_policy.py::policy_from_info`. The keys, the dispatch, and the
end-of-operation clear all mirror `optimizer/_context.py`'s `DST_OPTIMIZER_*` seam, which
the card's architectural posture names directly.

The shape-agnostic read / write / delete dispatch itself moved to `utils/context.py` and is
now shared by both subsystems. It handled four context shapes (`None`, object, `dict`,
frozen) and was already the single place a new shape would land; a second copy in
`resource_policy.py` would have been the first duplicate of it.

**The miss path is fail-closed.** `policy_from_info` returns `DEFAULT_RESOURCE_POLICY`, never
`None`. A frozen context that refused the stash, a plain `strawberry.Schema` that never
installed the extension, and a resolver invoked outside an operation all read back a
*bounded* policy. Returning `None` would have forced every caller to write its own
"no policy means no bound" branch, which is the fail-open shape spelled out in six places.

*Alternatives rejected: see the [rationale][rationale] (a `contextvars.ContextVar`, a
thread-local).*

### Decision 3 — The document text scan runs BEFORE the parse

Token count and structural nesting depth are charged by one lexer sweep over the raw
document string in `on_operation`, before graphql-core parses it.

This is not an optimization. graphql-core's parser is recursive-descent, and so are the
GraphQL validators; a depth bound applied to the parsed AST cannot stop the parse from
exhausting the interpreter's stack, which is exactly the failure S3's evidence names. A
bound that only fires after the thing it protects has already run is not a bound.

Two consequences are contractual and are documented rather than hidden:

- **Depth is structural, not selection-only.** `{`, `(` and `[` all count, so argument and
  input-object nesting counts alongside selection-set nesting. Before the parse there is
  nothing else to count, and the parser recurses on all three.
- **A malformed document is left to the real parser.** A `GraphQLSyntaxError` from the
  lexer is swallowed so the request receives the accurate syntax diagnostic rather than a
  resource rejection. Tokens are charged *as each token is read*, so a document whose size
  or nesting passes its bound BEFORE the malformed token is still rejected on that bound.
  Stated the other way round — which is the honest direction — a document whose garbage
  comes first is not scanned past it at all: it is answered with the syntax error, nothing
  executes, and the tokens the scan never reached are tokens no later pass had to spend.
  The scan is not a promise to measure every malformed document, it is a promise that a
  document too large to parse safely never reaches the parser.
- **`depth` is a running bracket balance**, so it is a true nesting depth for a balanced
  document. An unbalanced one is a syntax error by construction and is answered as one.

*Alternatives rejected: see the [rationale][rationale] (`parse_options["max_tokens"]`, a
depth `ValidationRule`, a regex or `str.count` over the document).*

### Decision 4 — The document and value budgets are one iterative walk

Expanded selections, aliases, collection cost, and every value bound are charged by a
single iterative walk over the validated AST in `on_execute`, before execution.

- **Iterative, with an explicit stack.** The card requires it, and the reason is the same
  one that puts the text scan before the parse: a recursive walker whose job is to bound a
  hostile document must not itself be a recursion target. Python 3.10 compatibility is
  incidental to that, not the reason for it.
- **Fragments expand at every spread site**, with a fragment map built once and the spread
  path carried on the stack. Spreading one fragment ten times therefore costs ten times —
  the evasion of "move the selection set into a fragment" is closed by construction. The
  spread path also makes a cyclic fragment set terminate, which matters because validation
  normally rejects cycles but a schema that disabled validation would hand one straight to
  this walk.
- **Directives change what is RETURNED, never what is charged.** `@skip(if: true)` would
  otherwise be a free pass around every document bound.
- **Aliases are charged per alias.** The same expensive field under twenty aliases is
  twenty selections and twenty aliases.
- **Values are charged in the same pass** because family classification needs the argument's
  own GraphQL input type, which only the field context supplies. Literal arguments,
  variables, and literal objects with variables spliced into them all normalize through
  `value_from_ast_untyped`, so there is one walker rather than one per value source.

**Why after validation.** The walk resolves field and argument definitions against the
schema; running it on an unvalidated document would mean reimplementing validation's
type-resolution error handling. Execution has not begun, so "reject before ORM work" holds
either way. The degenerate inputs an invalid document would present (unknown fragment,
unknown argument, a selection under a leaf, an operation kind the schema lacks) are each
handled and tested regardless, because a schema may disable validation.

**Value families are classified by TYPE, never by argument name.** A list of input objects
is a nested row set; a list of `ID` in a mutation is a relation-id set; a list of `ID` under
an argument named `ids` in a query is a node-refetch set; every other list is a membership
list. The single name-based rule — `ids` — exists because node refetch is a Relay
convention with no distinguishing type, and it is stated once rather than inferred.

**An ancestor-path cycle guard makes the value walk cycle-safe, and every reference is
charged.** Each entry on the walker's stack carries the ANCESTOR PATH of the value it
describes — the tuple of containers that value hangs under, held by strong reference and
compared by `is`. A container that is one of its own ancestors closes a cycle: it is not
charged again and its children are not queued. Every OTHER reference to a container is
charged in full, including a second reference to one already charged elsewhere in the
request, because a container reached twice is two references' worth of work for the
coercer, the walkers and the ORM.

A cycle guard needs ancestor-scoped lifetime and owning references; a charge-once cache
needs neither. They are therefore two separate mechanisms — a path for termination, and no
cache at all for charging. *The identity-keyed cache this replaced, and the two measured
bypasses that forced the change, are in the [rationale][rationale].*

**Value depth is its own bound.** `max_depth` counts brackets in the document TEXT, and a
value arriving through a variable has none: the document `query($p: JSON!) { blob(payload:
$p) }` is three brackets deep however deep `$p` is.
[`max_value_depth`][glossary-max_value_depth] (default `20`) is
charged from the ancestor path's own length during the walk, so a 10,000-deep
list-of-list-of-… payload is bounded even though every level is one node wide and the node
total stays small. It also bounds the identity scan each container performs over its
ancestors, which is what keeps that scan from being a cost of its own.

**Introspection is charged like any other document shape.** `__schema`, `__type` and
`__typename` resolve to graphql-core's own `SchemaMetaFieldDef` / `TypeMetaFieldDef` /
`TypeNameMetaFieldDef`, resolved exactly as that library's executor resolves them
(`__schema` / `__type` only on the query root). This matters because the walk ends a branch
whose field cannot be resolved, and `__schema` opens a subtree over every type, field,
argument and enum value in the schema. *The blind spot this closed is in the
[rationale][rationale].*

*Alternatives rejected: see the [rationale][rationale] (a `ValidationRule`, charging
variables but not literals, recursion with a depth guard).*

### Decision 5 — `DEFAULT_RELATION_SHAPE` becomes `"connection"`: a clean alpha break

**A clean break, with no deprecation shim.** A raw many-side list emitted beside a bounded
connection is not a convenience, it is the bypass. The migration is one line per relation
(`relation_shapes = {"items": "both"}`) and it is discovered at schema build rather than at
runtime.

`"both"` survives unchanged as an explicit opt-in, and the list it produces is now
row-bounded ([Decision 6](#decision-6--every-raw-list-is-bounded-at-one-seam)) rather than
unbounded — so opting in no longer opts out of the cap.

*The derivation, and the alternatives rejected (a one-release deprecation warning, a
settings flag restoring the old default, relying on the row bound alone), are in the
[rationale][rationale].*

### Decision 6 — Every raw list is bounded at one seam

`resource_policy.py::bounded_rows` is the single place a non-Relay list of rows is bounded,
shared by the root [`DjangoListField`][glossary-djangolistfield] and by the generated
many-side relation resolver. Both spellings of "a list of rows with no cursor" therefore
carry the same ceiling, and a future third spelling has an obvious home.

- **The bound is applied by SLICING**, so a `QuerySet` carries it into SQL as a `LIMIT` and
  is never evaluated unbounded. A value that is already materialized (a consumer resolver's
  return, Django's prefetch cache) is truncated in Python — which cannot un-fetch those rows
  but does stop the response from serializing them.
- **A non-subscriptable iterable is bounded through `islice`, not waved through.** The
  alternative to slicing an unsliceable value is not "return it whole"; that would be a
  bound that silently stops applying to exactly the shapes nobody anticipated.
- **Ordering against the visibility hook is a correctness constraint, not a preference.**
  The bound is applied AFTER
  [`get_queryset`][glossary-get_queryset-visibility-hook] and after the consumer-resolver
  post-processing, because a sliced queryset cannot be refiltered or reordered and both the
  hook and the surface compose onto the source. Slicing first turns the bound into a crash
  on every type that declares a hook — which is how the implementation discovered the
  constraint.

`DjangoListField(max_rows=…)` narrows; `trusted_max_rows=True` is the only way a field can
be wider than the request policy. A non-positive `max_rows` raises at the line that
constructed the field, matching the four target guards already there.

### Decision 7 — The policy is a CEILING over `relay_max_results`, never a replacement

`utils/connections.py::resolve_relay_max_results` — the one seam both the plan-time walker
and the resolve-time window read — now returns
`min(<explicit or configured cap>, policy.max_page_size)`. Both `DjangoConnection`
`resolve_connection` entry points resolve it once at the top, so every downstream window,
slicer, and fallback receives an already-clamped integer and the two windows agree by
construction.

This keeps the existing precedence intact (an explicit field `max_results` still beats the
schema config, which still beats Strawberry's default) and adds the policy strictly on top.
A connection can be narrower than the policy and can never be wider. The package default
`max_page_size` is `100`, identical to Strawberry's own `relay_max_results` default, so no
existing schema changes behavior by adopting the default policy.

### Decision 8 — `max_collection_cost` is a SHAPE bound, and its default says so

Every collection selection contributes the product of its own page bound and those of its
ancestors; the sum is the document's collection cost. This is the only bound that grows
with *nesting* rather than with any one collection, and it is what sees
"100 categories x 100 items each".

Its default is `1_000_000_000`, which is deliberately generous and is not a promise about
rows. The rows a request can actually return are bounded per collection by `max_page_size`
and `max_list_rows`; this bound exists to stop the *product* of those from compounding down
a deep document. *Why the default is set where it is, is in the [rationale][rationale].*

Two accounting rules are contractual:

- **An unspecified page charges the full ceiling.** A nested connection with no `first:`
  can return a full page per parent, so charging less would be charging for work the request
  might not do rather than for work it might.
- **A connection's own `edges` list is NOT a second collection.** The connection field above
  it already charged the page; charging the list again would multiply every connection in
  the document by a full page for free. This is the one structural exception, and it is keyed
  on the parent being connection-shaped rather than on the field name alone.

### Decision 9 — The execution deadline is cooperative, and says so

`execution_deadline_seconds` defaults to `None`. When set, the extension stamps a monotonic
deadline on the request context and every seam that is about to hand work to the database
calls `resource_policy.py::check_deadline` first. The seams are enumerated rather than left
to "the collection resolvers", because a seam that charges rows without checking the
deadline is a seam the deadline does not cover:

- `resource_policy.py::bounded_rows` — both raw-list spellings, root field and generated
  many-side relation resolver alike;
- `connection.py::_resolve_connection_fast_path` — the head both `resolve_connection` entry
  points share, so the plain and `totalCount` connections cannot diverge, placed after the
  `first` + `last` guard so a malformed pagination request still answers with its own error;
- `relay.py::DjangoNodeField` / `DjangoNodesField` — before the decode, which is the step
  that makes a visibility-scoped query inevitable (after the empty-`ids` short circuit, so
  a request that asks for nothing is never refused for it);
- `mutations/resolvers.py::run_write_pipeline_sync` and the delete branch of
  `_run_pipeline_sync` — BEFORE `transaction.atomic()` opens, so the refusal never has a
  partial transaction to unwind. The create / update check sits in the shared skeleton, so
  the model, form and serializer flavors all inherit it.

`utils/connections.py` was audited and needs none: every helper there is pure window
arithmetic with no database access.

**The rejection reports the CONFIGURED budget, never the clock.** `limit` is the policy's
own `execution_deadline_seconds` and `charged` is one second past it. The monotonic deadline
and the measured overrun are process-internal timings a client can neither verify nor act
on, and a wire field named `limit` carrying a monotonic timestamp is worse than useless — it
reads as a bound the deployment never configured.

It is **not** a preemptive timeout and does not claim to be one. Nothing in-process can
interrupt a query already accepted by a database driver; a statement timeout is the
database's job and a request timeout is the deployment's. A cooperative deadline that stops
the request from starting *more* work is honest and useful; a `signal.alarm` or a watchdog
thread pretending to cancel SQL is neither.

It is the only optional bound. *Why its default is `None` rather than a number is in the
[rationale][rationale].*

### Decision 10 — Per-field overrides narrow; the schema policy is the trusted declaration

`resource_policy.py::effective_bound` is the whole rule: `None` means "the field declares
nothing, the policy governs"; a declared value narrows to the tighter of the two;
`trusted=True` is the explicit widening opt-in at the call site.

The schema-construction policy IS the trusted declaration S3 asks for — it is the only place
that may widen a package default, and it is the deployment's own deliberate statement.
`ResourcePolicy.narrowed()` enforces the same rule between policies and refuses any override
that loosens a bound, naming both values so the message is actionable.
`execution_deadline_seconds` narrows from `None` to any positive value and downward from
there; restoring `None` is the widest move available and is refused like any other widening.

### Decision 11 — One typed rejection, and no per-transport translation

`ResourceLimitExceeded` multiple-inherits `graphql.GraphQLError` and
`DjangoStrawberryFrameworkError` (the `SyncMisuseError` precedent). Because it *is* a
`GraphQLError`, every transport that renders a pre-execution failure into a response
envelope renders it identically with no translation layer, which is what makes that parity
a structural property rather than three code paths kept in step.

**Where the parity ends, stated rather than assumed.** *Enforcement* is transport-independent:
Strawberry enters the extension's `on_operation` and `on_execute` hooks for HTTP execution
and for a WebSocket subscribe alike, so every pass runs on every operation. *Rendering* is
not. Sync HTTP, async HTTP, and WebSocket **queries and mutations** all route through
Strawberry's `execute`, which converts a pre-execution exception into an ordinary `errors`
entry. Strawberry's `subscribe` path has no such conversion: a rejected WebSocket
**subscription** is refused just as hard — nothing executes — but its client observes the
operation completing without data rather than an error entry carrying `extensions.code`.
That is upstream's shape, not this package's choice, and building a package-owned
subscription error envelope to paper over it is not in this card's scope; the claim is
narrowed to what is true instead.

`extensions.code` is the single constant `RESOURCE_LIMIT_EXCEEDED`; `bound`, `limit`, and
`charged` ride alongside so a client can act on the rejection without parsing prose.

**`DjangoSchema` installs the extension automatically**, as a class rather than an instance,
because Strawberry constructs one instance per request and a shared instance would share
one set of charge counters across every concurrent request. A consumer-supplied entry —
class or instance — suppresses the automatic append, so a consumer who installed the
extension with their own policy does not get a second copy double-charging the same bounds.
*Why installation is automatic rather than documented is in the [rationale][rationale].*

### Decision 12 — The version bump belongs to the `0.0.14` joint cut

This card does **not** move the version quintet. It targets `0.0.14`, sharing that patch
with the three other cards of this security program (046, 048, 049) and with cards 041-045
before them. The quintet — `pyproject.toml [project].version`,
`django_strawberry_framework/__init__.py::__version__`, the `tests/base/test_init.py`
assertion that pins them together, the glossary's package-version line, and the package's
own `uv.lock` entry — already reads `0.0.14`, so there is no bump for this card to take.

Under the [joint version cut][glossary-joint-version-cut] rule the release wording belongs
to the **last** card of a shared line to land, never to an individual card's slices. Slice 5
therefore owns the documentation fold-in only.

*This decision originally claimed a `0.0.16` cut of its own. What it claimed, and why an
authoring-time board scan could not have known better, is in the [rationale][rationale].*

### Decision 13 — What this policy does not bound, and why each boundary is deliberate

**Decision.** The six boundaries below are not oversights and must not be re-derived. Three are
transport-adjacent bounds this walker is the wrong layer to carry, and they are carried as scope
on card `TODO-ALPHA-051-0.0.20`; three are audited exclusions that a later pass must not "fix".
Each is a boundary of the shipped contract rather than a gap in it.

**Not this layer — a package-owned subscription rejection envelope.** Enforcement is not the gap;
**rendering** is. A subscription enters `extensions_runner.operation()` and `executing()` exactly
as a query does, so both the document text scan and the value walk *do* run and a violating
subscription *is* refused. What differs is what the client sees: upstream's non-streaming path
converts a pre-execution exception into an `errors` entry and its streaming path does not, so a
rejected subscription closes with `complete` instead of carrying
`extensions.code == "RESOURCE_LIMIT_EXCEEDED"`. *The `except`-clause asymmetry that produces
this is traced in the [rationale][rationale].*

**State the behaviour, never the private method name.** A fix here must be written against that
broad-versus-narrow `except` asymmetry and must pin no private upstream symbol: the declared floor
is `strawberry-graphql>=0.316.0` with no ceiling, and the seam moves inside that range. Because
the floor is open-ended, whether the asymmetry still holds has to be **re-measured across the
whole range** rather than read off the installed wheel. [`spec-046`][spec-046]'s stop-aware result
source already answers the same instability by wrapping both public names unconditionally rather
than testing a version. *The measured version drift is in the [rationale][rationale].*

Closing this means owning an error envelope for a transport whose lifecycle is upstream's, which
is why [Decision 11](#decision-11--one-typed-rejection-and-no-per-transport-translation) states
the boundary rather than claiming parity it does not have.

**Not this layer — transport-level upload charging.** Uploads are charged post-materialization, which
[Goals](#goals) 2 already narrows to "before any resolver, serializer, validator or storage
backend touches the files". Charging *earlier* is a transport concern: Django's upload handlers
have already streamed a multipart body by the time coerced values exist, so the seam is a
package-owned upload handler or streaming body reader, alongside
[`spec-046`][spec-046]'s request-body cap rather than inside this walker.

**Not this layer — a configured bound on numeric literal size.** CPython's
`sys.get_int_max_str_digits` (4,300) raises during JSON parsing or graphql-core's literal
coercion, so an enormous integer literal *is* refused — but as a malformed-input failure, not as
a typed resource rejection carrying this policy's code. A configured bound means a pre-coercion
scan of the raw variables JSON, which duplicates the body cap's layer; `_charge_leaf` and
[Edge cases](#edge-cases-and-constraints) document the behaviour rather than promising the bound.

**Audited exclusion — `utils/connections.py` gets no `check_deadline` call.** Every function in
it was read: `connection_sidecar_inputs_from_kwargs`, `window_range_plan`, `split_window_rows`,
`derive_connection_window_bounds`, `resolve_relay_max_results`, `derive_keyset_window_bounds` and
the assert helpers are all pure window arithmetic with no database access.
`resolve_relay_max_results` is additionally called at **plan** time, where a deadline check would
fire outside a resolve and against a plan-time `info`, so it is explicitly the wrong seam rather
than a missing one.

**Audited exclusion — `forms/resolvers.py::_run_plain_form_pipeline_sync` gets no deadline
check.** The model-less plain-form flavour has no locate, no relation decode and no model write,
so there is no database seam to guard. The three model-backed flavours all enter
`run_write_pipeline_sync`, which has one.

**Audited exclusion — `_charge_container` is deliberately not memoized.** A diamond-shaped value
(one container referenced from many places) is charged **once per reference**, which is the
contract [Decision 4](#decision-4--the-document-and-value-budgets-are-one-iterative-walk) states.
The work is bounded by `max_input_nodes` without a separate bound, because every reference pops a
stack entry and charges a node before it descends — a value engineered to blow the walk up runs
out of node budget first.

**Why the cycle guard and the charge counter are two mechanisms and cannot be one.** They have
different lifetime requirements — ancestor-scoped and owning, versus request-scoped — and only
one of them is a contract, so one object cannot correctly be both. A path tuple terminates the
walk; **no cache at all** charges it. *The single object that once did both duties, and the two
bypasses it produced, are in the [rationale][rationale].*

**Three constants whose values are decisions, not defaults.** `max_value_depth` is `20`, matching
`max_depth`, because the two bound the same idea on the two sides of the text/variable divide and
a value nested deeper than a document may be is not a shape any legitimate client sends. The
deadline rejection reports `limit = ceil(configured seconds)` and `charged = limit + 1`, reusing
the "exceeded a budget integers cannot express" spelling already used for an unmeasurable upload
rather than putting a monotonic clock reading on the wire; the one branch where `configured is
None` — a hand-written `dst_resource_deadline` context key with no policy behind it — reports
`limit = 0` and the word `unknown`, and still rejects, fail-closed. `_is_connection_type` requires
`node` **and** `cursor` on the edge type, because Strawberry's `ListConnection` edge carries both
and requiring both is what keeps the collection-cost exemption from being claimable by shape
accident.

**The live deadline rows drive the clock, not a sleep.** They set
`execution_deadline_seconds` to `0.000_001`
(`examples/fakeshop/test_query/test_resource_policy_api.py::DEADLINE_SECONDS`), so the deadline has
always passed by the time a resolver runs and the rows are deterministic. A sleep would make them
timing-dependent on CI, and the cooperative contract in
[Decision 9](#decision-9--the-execution-deadline-is-cooperative-and-says-so) is about *where* the
check runs rather than about how long anything takes.

## Implementation plan

| Slice | Files | Delta |
|---|---|---|
| 1 | `resource_policy.py` (new) | `ResourcePolicy`, `DEFAULT_RESOURCE_POLICY`, `ResourceLimitExceeded`, `RESOURCE_LIMIT_ERROR_CODE`, `resolve_resource_policy`, `stash_resource_policy` / `policy_from_info` / `clear_resource_context`, `effective_bound`, `validate_collection_bound`, `bounded_rows`, `check_deadline`. |
| 1 | `utils/context.py` (new), `optimizer/_context.py` | The shape-agnostic dispatch lifted out and shared; the optimizer module keeps its keys and its reset and re-exports the helpers. |
| 1 | `conf.py` | `RESOURCE_POLICY_KEY` and `resource_policy_setting()`, a thin reader that validates nothing. |
| 2 | `extensions/resource_policy.py` (new) | `scan_document_text`, `charge_document`, `_DocumentBudget`, `_ValueBudget` (per-reference charging, `_closes_a_cycle` ancestor-path guard), `_field_definition` (introspection meta-fields), `_is_connection_type` (full edge shape), [`DjangoResourcePolicyExtension`][glossary-djangoresourcepolicyextension]. |
| 2 | `extensions/__init__.py`, `__init__.py` | Exports; the extension is root-exported because it is part of the default recipe. |
| 2 | `schema.py` | `DjangoSchema(resource_policy=…)`, `schema.resource_policy`, `_with_resource_policy_extension`. |
| 3 | `list_field.py` | `max_rows` / `trusted_max_rows`, constructor-site validation, the bound applied after visibility on all three resolver shapes. |
| 3 | `types/resolvers.py` | The generated many-side relation resolver bounds both the prefetched and the manager path. |
| 3 | `utils/connections.py`, `connection.py` | The policy ceiling over `relay_max_results`, resolved once per connection resolve. |
| 3 | `connection.py`, `relay.py`, `mutations/resolvers.py` | The `check_deadline` seams: the shared connection resolve head, both Relay refetch fields, and the write pipelines before their transaction opens ([Decision 9](#decision-9--the-execution-deadline-is-cooperative-and-says-so)). |
| 4 | `types/base.py`, `types/finalizer.py` | `DEFAULT_RELATION_SHAPE = "connection"` and the reconciled synthesis docstring. |
| 4 | `examples/fakeshop/apps/{library,products}/schema.py` | Explicit `"both"` opt-ins where the example's live coverage needs the raw list; `CategoryType.properties` deliberately left on the new default. |
| 4 | `tests/test_relay_connection.py`, `tests/test_connection.py`, `tests/optimizer/test_extension.py` | Re-pinned to the new default, with the `"both"` shape pinned separately. |
| 5 | `docs/GLOSSARY.md` (DB), `docs/TREE.md`, `KANBAN.md` (DB) | Fold-in. |

## Helper-reuse obligations (DRY)

- **`utils/context.py` is the only context dispatch.** No subsystem may grow a second
  `getattr`-then-`__getitem__` ladder; a new context shape lands there.
- **`bounded_rows` is the only raw-list bound.** No resolver may slice a collection with a
  locally-derived limit.
- **`effective_bound` is the only narrowing rule.** No call site may open-code `min(...)`
  against a policy value.
- **`resolve_relay_max_results` is the only connection-cap resolution**, and remains shared
  by the plan-time and resolve-time halves so their windows cannot diverge.
- **`_ValueBudget._reject` is the only rejection constructor** inside the walker, so every
  bound's message, code, and extension payload have one shape.
- **`_is_connection_type` is the only connection detection**, and it matches the whole edge
  SHAPE — an `edges` field that is a list whose item type carries both `node` and `cursor` —
  rather than a `...Connection` name or the presence of a field called `edges`. Matching the
  shape keeps a consumer-renamed connection inside the accounting; matching the *edge* shape
  keeps an ordinary type that happens to expose a field named `edges` OUT of the one
  structural exception the walk grants a connection. That exception makes a list free, so a
  loose test hands a free unbounded list to any type that picked the name.

## Edge cases and constraints

- **A frozen or read-only context** cannot hold the stash; the request runs under
  `DEFAULT_RESOURCE_POLICY` rather than unbounded.
- **A consumer key collision** — some other value stashed under `dst_resource_policy` — is
  ignored, not trusted: `policy_from_info` type-checks before returning.
- **An upload that cannot report its size** (absent, `None`, non-integral, negative, or
  `True`) is *rejected*, not charged as zero bytes. Charging the answer rather than one
  spelling of the missing input is what keeps an unmeasurable stream out of the permit path.
- **Duplicate node ids are charged positionally**, because
  [`DjangoNodesField`][glossary-djangonodesfield] preserves duplicates positionally; the
  database may collapse the `IN`, but the framework still does the work.
- **An empty list charges its container and nothing else**, so `ids: []` is never a
  rejection.
- **A JSON-shaped custom scalar's contents are still charged** as untyped nodes and widths;
  otherwise a `JSON` argument would be a free payload of unlimited size.
- **A scalar supplied where a list is declared** is charged as a one-item list, matching
  GraphQL's own input coercion.
- **`__typename` and the introspection roots** resolve to their graphql-core meta-field
  definitions and are charged like any other field: `__type(name: …)`'s argument value is
  charged as a scalar, and `__schema`'s nested `types { fields { … } }` lists charge
  multiplicatively as nested collections do.
- **A large numeric literal is not measured by `max_scalar_bytes`**, which measures text
  because the superlinear parsers it exists for take text. What bounds a huge integer is
  CPython's own `sys.get_int_max_str_digits` conversion limit (4,300 digits by default),
  which raises while a variable's JSON body is parsed or at the `int()` inside graphql-core's
  literal coercion. The request is refused either way, but as a malformed-input failure
  rather than a typed resource rejection — a bound the package does not own is not a bound
  it promises.
- **A subscription or mutation against a schema that defines no such root** is skipped.
- **Only the named operation is charged** when `operationName` is supplied; a document
  carrying several operations does not pay for the ones it did not run.
- **The example project keeps both relation shapes live**: `CategoryType.items`,
  `ItemType.entries` and `BookType.genres` / `GenreType.books` are explicit `"both"`
  opt-ins so the bounded raw-list surface stays covered, while `CategoryType.properties` is
  left on the new default so the connection-only shape is covered by the same schema.

## Test plan

The live tier (`examples/fakeshop/test_query/test_resource_policy_api.py`, 35 rows) drives
mounts of the package view over probe schemas that each narrow ONE family of bounds and
leave every other bound at its default — so a row that rejects can only have rejected on the
bound it is about.

- **Document text**: under / over the token bound with the exact charge; over the depth
  bound; argument and input-object nesting counted toward depth.
- **Expanded document**: a fragment charged at every spread site; `@skip(if: true)` not
  evading accounting; the same field under many aliases charged per alias; nested
  collections charged multiplicatively; an explicit small `first:` narrowing the charge.
- **Values, tiny document / large variable payload**: node ids under, at, and over the
  bound, with `CaptureQueriesContext` proving **zero** queries after a rejection; duplicate
  ids charged positionally; an empty list accepted; membership items at and over; a wide
  filter tree charged by container width; relation ids over the per-mutation bound; two
  individually-legal mutation fields exceeding the aggregate bound; **one variable spliced
  into two mutation fields charged twice** (the shared-container bypass, and the shape a
  request can actually build over the wire); a deeply nested variable value over and under
  the value-depth bound (the bound the pre-parse text scan structurally cannot supply); a
  scalar over the byte bound; several arguments together exhausting the input-node budget.
- **Introspection**: a nested `__schema { types { fields … } }` document rejected on
  collection cost, proving the meta-fields resolve and their subtree is charged.
- **The cooperative deadline**, one row per seam — connection, raw list, Relay refetch and a
  write — each asserting the typed bound, and **zero** captured queries wherever the seam
  precedes any SQL; plus an unarmed-policy row proving no seam rejects without a configured
  deadline.
- **Uploads**: a multipart request rejected by the policy, with the row stating why the
  transport body cap cannot be what rejected it.
- **Collections**: a raw root list stopping at the maximum; the list sibling bounded so it
  cannot bypass the connection cap; a connection page wider than the policy refused; the
  connection-only default leaving no raw sibling in the SDL to select.
- **Parity**: the sync and async mounts returning byte-identical rejection extensions.

The package tier (`tests/test_resource_policy.py`, 79 rows) covers what a request cannot
express: per-bound validation including the `bool` trap; the precedence ladder and the
settings-shape rejections; the narrowing rule including the deadline's asymmetry; context
threading across object / dict / frozen shapes and the fail-closed miss; the cooperative
deadline armed, unarmed, and passed — the passed row asserting the CONFIGURED seconds in
`limit` and in the message, with a hand-written-key row for the no-policy-behind-it case;
`bounded_rows` on a non-subscriptable iterable and under a trusted widening; the pre-parse
scan on an absent, malformed, and oversized-and-malformed document; and the walker's
degenerate inputs (unnamed operation, missing root type, unknown fragment, fragment cycle,
inline fragment with and without a type condition, unknown argument, leaf parent, untyped
container, unmeasurable upload). The identity rows are the pointed ones: a container
referenced twice charged **twice** at a node budget that separates the two contracts, two
distinct-but-equal containers both charged, a self-referential mapping AND a
self-referential list terminating, a cycle that closes onto a grandparent rather than a
parent, an over-and-under value-depth pair, the introspection meta-fields charged
(selections, and `__type(name:)`'s own argument value), and the connection shape test from
both sides — a type whose `edges` is a list of non-edges, and one whose `edges` is not a
list at all — each asserting the exact charge, since the connection exemption's whole effect
is a charge that does not happen. `tests/test_list_field.py` adds the constructor-site
`max_rows` rejection and the narrowing row.

## Doc updates

- `docs/GLOSSARY.md` (DB-backed): new entries for **Execution resource policy**,
  **`ResourcePolicy`**, **`DjangoResourcePolicyExtension`**,
  **[Value-budget walker][glossary-value-budget-walker]** and
  **[`max_value_depth`][glossary-max_value_depth]**; this card's root exports added to the
  Public exports list; updated bodies for [`DjangoListField`][glossary-djangolistfield],
  [`Meta.relation_shapes`][glossary-metarelation_shapes] and
  [Relation handling][glossary-relation-handling].
- `docs/TREE.md`: regenerated for the three new modules.
- `KANBAN.md` (DB-backed): card 047 to Done.
- `CHANGELOG.md`: **not** touched — see the permission caveat at the top.

## Risks and open questions

*Each risk's fallback position — the answer that would be taken if the preferred one failed —
is in the [rationale][rationale].*

- **`max_collection_cost`'s default is generous by design.** Preferred answer for `0.0.14`:
  the shape-bound framing in
  [Decision 8](#decision-8--max_collection_cost-is-a-shape-bound-and-its-default-says-so),
  with per-collection bounds carrying the row promise.
- **Response-byte accounting is out of scope.** Preferred answer: a future card adding a
  serialization-time budget with a defined partial-response policy.
- **Field-level cost annotation** (`Meta.cost` / a `@cost` directive) is the natural
  successor to `max_collection_cost` and is deliberately deferred; the policy object is the
  place it would attach.
- **The `ids` argument-name rule** is the walker's one name-based classification. Preferred
  answer: keep it, because Relay's node refetch has no distinguishing type.
- **The relation-shape break has no telemetry.** A consumer discovers it at schema build (a
  field vanished from the SDL) rather than through a warning. Accepted: schema-build
  discovery is earlier and louder than a log line.

## Out of scope (explicitly tracked elsewhere)

- Secure output and error defaults — [`DONE-048-0.0.14`][kanban] (S5-S8).
- Dependency and CI hardening — [`WIP-ALPHA-049-0.0.14`][kanban].
- Persisted queries / document allow-listing — not carded.
- Rate limiting per client or per IP — a deployment concern, not a schema one.

## Definition of done

- [x] One immutable `ResourcePolicy` is consumed by `DjangoSchema`, the collection fields,
      the connection cap seam, and (through the shared context) the transports; per-field
      overrides narrow only, and the schema-construction policy is the sole trusted
      declaration that may widen.
- [x] Document tokens and structural depth are charged **before** the parse; expanded
      selections, aliases, and multiplicative collection cost are charged after validation
      and before execution, with fragments, aliases, and directives unable to evade
      accounting.
- [x] One iterative, cycle-safe value walker charges input nodes, container width, value
      nesting depth, membership items, node-refetch ids, per-mutation and aggregate relation
      ids, nested rows, upload count / per-file bytes / aggregate bytes, and scalar byte
      size — charging every REFERENCE, cycle-guarded by the ancestor path rather than by a
      request-lifetime `id()` cache — and rejects before any id is decoded or any queryset is
      built, proven by a zero-query assertion. Uploads are the documented exception to
      "before the work": they are charged post-materialization
      ([Goals](#goals) 2).
- [x] `DEFAULT_RELATION_SHAPE` is `"connection"`; a raw many-side list is an explicit
      `Meta.relation_shapes` opt-in and is row-bounded when opted into.
- [x] `DjangoListField` carries a required effective bound with a narrowing `max_rows` and
      an explicit trusted widening; a non-positive value fails at construction.
- [x] Every rejection is one `ResourceLimitExceeded` carrying
      `extensions.code == "RESOURCE_LIMIT_EXCEEDED"`, identical on the sync and async
      transports.
- [x] Full suite green at `fail_under = 100` for `django_strawberry_framework`; `ruff
      format --check`, `ruff check`, `scripts/check_trailing_commas.py --check`,
      `manage.py check` and `makemigrations --check --dry-run` all clean.
- [x] Docs folded in; the version quintet rides the joint cut with cards 048 and 049
      ([Decision 12](#decision-12--the-version-bump-belongs-to-the-0014-joint-cut)).
- [x] [`max_value_depth`][glossary-max_value_depth] has a glossary entry, and the
      [`ResourcePolicy`][glossary-resourcepolicy] glossary body enumerates it alongside the
      other bounds.
- [x] This card's root exports appear in the glossary's Public exports list —
      `ResourcePolicy` (naming `DEFAULT_RESOURCE_POLICY` the way the `ErrorPolicy` row names
      its own default), `DjangoResourcePolicyExtension`, `ResourceLimitExceeded` and
      `RESOURCE_LIMIT_ERROR_CODE` — and no glossary row points at a `#djangoschema` anchor
      that resolves to nothing.
- [x] The deliberative layer is extracted to
      [`spec-047-resource_policy-0_0_14-rationale.md`][rationale], and every decision the
      release falsified states the corrected contract directly rather than its own history.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[feedback2]: ../feedback2.md
[glossary]: ../GLOSSARY.md
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-connection-aware-optimizer-planning]: ../GLOSSARY.md#connection-aware-optimizer-planning
[glossary-djangoconnectionfield]: ../GLOSSARY.md#djangoconnectionfield
[glossary-djangolistfield]: ../GLOSSARY.md#djangolistfield
[glossary-djangomodelformmutation]: ../GLOSSARY.md#djangomodelformmutation
[glossary-djangomutation]: ../GLOSSARY.md#djangomutation
[glossary-djangonodesfield]: ../GLOSSARY.md#djangonodesfield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangoresourcepolicyextension]: ../GLOSSARY.md#djangoresourcepolicyextension
[glossary-execution-resource-policy]: ../GLOSSARY.md#execution-resource-policy
[glossary-filter_input_type]: ../GLOSSARY.md#filter_input_type
[glossary-filterset]: ../GLOSSARY.md#filterset
[glossary-get_queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-joint-version-cut]: ../GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: ../GLOSSARY.md#live-first-coverage-mandate
[glossary-max_value_depth]: ../GLOSSARY.md#max_value_depth
[glossary-metarelation_shapes]: ../GLOSSARY.md#metarelation_shapes
[glossary-per-operation-extension-isolation]: ../GLOSSARY.md#per-operation-extension-isolation
[glossary-plan-cache]: ../GLOSSARY.md#plan-cache
[glossary-probe-urlconf]: ../GLOSSARY.md#probe-urlconf
[glossary-relatedfilter]: ../GLOSSARY.md#relatedfilter
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: ../GLOSSARY.md#relay-node-integration
[glossary-request-body-cap]: ../GLOSSARY.md#request-body-cap
[glossary-resourcepolicy]: ../GLOSSARY.md#resourcepolicy
[glossary-seed_data]: ../GLOSSARY.md#seed_data
[glossary-serializermutation]: ../GLOSSARY.md#serializermutation
[glossary-single-upstream-parity]: ../GLOSSARY.md#single-upstream-parity
[glossary-strawberry-extension-lifecycle]: ../GLOSSARY.md#strawberry-extension-lifecycle
[glossary-strawberry_config]: ../GLOSSARY.md#strawberry_config
[glossary-strictness-mode]: ../GLOSSARY.md#strictness-mode
[glossary-testclient]: ../GLOSSARY.md#testclient
[glossary-upload-scalar]: ../GLOSSARY.md#upload-scalar
[glossary-value-budget-walker]: ../GLOSSARY.md#value-budget-walker

<!-- docs/SPECS/ -->
[rationale]: appx/spec-047-resource_policy-0_0_14-rationale.md
[spec-046]: spec-046-transport_security-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
