# Rationale: spec-047 — Execution resource policy (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-047-resource_policy-0_0_14.md`][spec-047]. The spec is the
contract and states only what is currently true; everything that explains **how it got there**
lives here: the alternatives each decision rejected and why each lost, the derivations that do
not change how a decision is implemented, every change a decision has undergone with the round
that caused it, and every claim a decision once made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass. **The move
happened after the release, not before the build.** The shipped cycle skipped it; this pass
supplies it. Text marked *Moved* below was cut out of the spec, not copied: it exists here and
nowhere else.

## How to read this file

- **One entry per spec decision**, named by the decision's own heading and linked to its anchor.
  A decision whose text did not move has no entry here — that is not an omission, it means the
  whole decision is contract.
- **Who reads it.** Worker 3 reads it during review; Worker 1 owns it; Worker 2 never reads it.
  A reader looking for what the package *does* wants the spec, not this file.
- **Round attribution.** This card ran a build round and then a **remediation round**
  (`docs/builder/bld-047-remediation.md`). Where a decision changed, the entry names which.
- **What deliberately stayed in the spec, and why.** The bounds table, the public API, the
  rejection envelope, the compatibility promise, goals, non-goals, edge cases, the test plan and
  the DoD are all contract. So are three passages that read like deliberation and are not:
  Decision 3's two contractual consequences (structural depth, and leaving a malformed document
  to the real parser), Decision 6's ordering constraint against the visibility hook, and the
  whole of Decision 13 — whose boundary entries and audited exclusions are instructions to a
  future builder ("must not be re-derived", "a later pass must not fix"), not a record of
  thinking. Only Decision 13's upstream forensics moved.

## Provenance of this record

- **Moved** — cut from the spec by this pass. The five `Alternatives rejected` paragraphs, the
  Borrowing posture's declined-borrowings list, four derivation passages inside Decisions 4, 8,
  9 and 11, Decision 13's upstream `except`-clause forensics, and the Risks section's fallback
  positions.
- **Reconstructed** — rebuilt from the shipped code, the release commit, and
  `docs/builder/bld-047-remediation.md`. The whole of the change record below. The build cycle
  produced no per-round review documents for this card, so the remediation catalog is the only
  contemporaneous round artifact and is the source for every attribution that names it.
- **Deleted, recorded nowhere** — the spec's original Decision 12 premise and the Status block
  that depended on it. Both were falsified by the release rather than superseded by an argument,
  and prose a current decision has falsified belongs in neither file. What replaced them is in
  the change record's first entry.

## Change record

### The version cut this card predicted it would own

**Falsified, then withdrawn.** The spec's original Decision 12 read *"This card is the only
non-Done `0.0.16` card, so it owns the bump"*, and a Version boundary paragraph at the head of
the spec repeated it. Both were true of the board at authoring time and neither survived.

Each of cards 046, 047, 048 and 049 ran the same board scan at its own authoring moment, and
each concluded — correctly, in isolation — that it was the only non-Done card at its patch
version and that the [Joint version cut][glossary-joint-version-cut] rule therefore did not
apply. The maintainer then retargeted **all four** cards to `0.0.14`, the patch cards 041-045
already occupied. `0.0.15`, `0.0.16` and `0.0.17` were never the version of a released
artifact; `__version__` never held any of them.

So the bump this decision claimed does not exist to be owned. The quintet reads `0.0.14`, the
card targets `0.0.14`, and Slice 5 folds documentation in and nothing else. The spec's
Decision 12 now states that directly, and the `Joint version cut` entry in its
`## Key glossary references` was correspondingly reversed: it was listed as "the release rule
this card is explicitly NOT subject to" and is now the rule the card is subject to.

**The lesson worth keeping.** A single-card board scan cannot establish that a card owns a
version cut, because it cannot see what the other cards on the program will be retargeted to.
The rule already says the last card of a shared line to land owns the wording; a card that
scans the board and concludes it owns a cut of its own is predicting a release shape an
authoring-time scan cannot know.

### The identity memo the value walker no longer uses

**Changed by the remediation round.** The build shipped `_ValueBudget` with a single
request-lifetime `_seen: set[int]` of already-charged `id()` values, doing double duty as a
cycle guard and as a charge-once cache. The remediation round deleted it and replaced it with an
ancestor-path tuple for termination and **no cache at all** for charging.

Two measured bypasses forced it, and they are the reason the spec now says every reference is
charged:

- **An `id()` is unique only among LIVE objects.** The coerced values this walk reads are
  temporaries; freeing one list lets the next same-sized list reuse its address, so an
  `id()`-keyed set reports a *fresh* container as already charged. Measured on this package's
  own walker: 1,650 relation ids charged as 55, because graphql-core's `value_from_ast_untyped`
  builds fresh same-size lists whose ids recycle through CPython's free list.
- **Charge-once is not the contract.** One variable spliced into two mutation fields resolves to
  the same Python list both times, so charge-once made the second field's relation ids free and
  the aggregate bound never fired — a live request walked past `max_relation_ids_total` and went
  on to decode ids.

A cycle guard needs ancestor-scoped lifetime and owning references; a charge-once cache needs
neither. Conflating the two in one set is what produced both bypasses, which is why they are now
two separate mechanisms.

**A claim the spec may no longer make.** Nothing in the package should describe the value walker
as memoizing containers by identity. That sentence describes the deleted mechanism and, read as
current, promises the exact charge-once behaviour the remediation removed.

### `max_value_depth` was added late, and the glossary never saw it

**Added by the remediation round.** The bound did not exist at build time. It closes a gap
neither document bound could reach: `max_depth` counts brackets in the document *text*, and a
value arriving through a variable has none, so a 10,000-deep nested payload was bounded by
nothing while its node total stayed small.

The remediation catalog recorded that the glossary DB was deliberately left untouched for that
round's scope, so `max_value_depth` shipped with no glossary entry and the `ResourcePolicy`
glossary body enumerated the bounds without it. That debt outlived the round and was carried on
the board until this closeout pass discharged it.

### The introspection blind spot

**Fixed by the remediation round.** The walk originally answered "no field definition" for
`__schema`, `__type` and `__typename`, and the walk ends a branch whose field cannot be
resolved. Introspection was therefore charged as ONE selection and never descended into — making
it the single document shape no depth, selection, or collection bound could see, even though
`__schema` opens a subtree over every type, field, argument and enum value in the schema. The
meta-fields now resolve to graphql-core's own `SchemaMetaFieldDef` / `TypeMetaFieldDef` /
`TypeNameMetaFieldDef`, exactly as that library's executor resolves them.

### Decision 13 was written after the release

The remediation round's deferral catalog was folded into the spec as Decision 13 a day after the
release commit — the only substantive post-release edit to the spec, and purely additive: three
bounds with named seams, three audited exclusions a later pass must not "fix", and the
carried-forward Definition-of-done boxes that tracked the first three.

Those boxes are gone, and the decision no longer calls the three bounds owed. A spec whose
`Status:` line says shipped cannot also hold unticked work: the boxes were a promise the card
had already stopped being able to keep, and every one of the three is a transport-adjacent bound
this walker is the wrong layer to carry — none could be discharged by editing this spec. They are
scope on card `TODO-ALPHA-051-0.0.20` instead, which is where the request-body cap's layer and
the boundary-hardening work already live. Decision 13 keeps the full technical statement of each,
because *where the bound does not reach* is contract a consumer needs; what it no longer claims is
that this card still owes it.

## Decision entries

### Decision 1 — One immutable frozen dataclass, validated at construction

Spec: [Decision 1][spec-047-d1].

*Moved — alternatives rejected.* A settings-dict read per bound (S3's explicit "do not scatter
unrelated settings reads across resolvers"). A mutable dataclass with a `freeze()` call (the
unfrozen window is the bug). Pydantic (a new hard dependency for one object).

### Decision 2 — Threaded through the request context, mirroring the optimizer seam

Spec: [Decision 2][spec-047-d2].

*Moved — alternatives rejected.* A `contextvars.ContextVar` (invisible to the consumer's context
object, and the package already owns a context seam — two would be one too many). A thread-local
(wrong under async).

### Decision 3 — The document text scan runs BEFORE the parse

Spec: [Decision 3][spec-047-d3].

*Moved — alternatives rejected.* `parse_options["max_tokens"]` (loses the typed code; see the
Borrowing posture entry below). A `ValidationRule` for depth (runs after the parse). A regex or
`str.count` over the document (a brace inside a string literal is not a brace; the lexer knows
the difference).

### Decision 4 — The document and value budgets are one iterative walk

Spec: [Decision 4][spec-047-d4].

*Moved — alternatives rejected.* A `ValidationRule` (no access to variables, which is the whole
of S4). Charging only variables and ignoring literals (a literal object is a value too).
Recursion with a depth guard (a depth guard on a walker that exists to bound depth is circular).

*Moved — the derivation of the ancestor-path guard.* The full account of the deleted
`_seen: set[int]`, both measured bypasses, and why one object could not be both a cycle guard and
a charge-once cache is in the change record above, under
[The identity memo the value walker no longer uses](#the-identity-memo-the-value-walker-no-longer-uses).
The ancestor path is the same shape the document walk already uses for fragment spreads (a
`path` carried on the stack), with object identity in place of fragment names.

*Moved — the introspection derivation.* Why answering "no field definition" for the meta-fields
made introspection invisible to every document bound is in the change record above, under
[The introspection blind spot](#the-introspection-blind-spot).

### Decision 5 — `DEFAULT_RELATION_SHAPE` becomes `"connection"`: a clean alpha break

Spec: [Decision 5][spec-047-d5].

*Moved — alternatives rejected.* A one-release deprecation warning while still emitting both
(keeps the bypass, and a warning nobody reads is not a mitigation). A settings flag to restore
the old default (a global switch that re-opens a security default is the worst of both — it is
invisible in the schema, unlike a `Meta` key). Leaving the default and relying on the new row
bound alone (bounding the sibling is not the same as not having it: the sibling has no cursor,
so a client can only ever read the first N rows of it, which is a worse API *and* still unbounded
across aliases).

*Moved — the derivation.* The card left the default open and the spec decided it, the way card
046 decided its own: a clean break with no deprecation shim. Every argument for a shim is an
argument for keeping the bypass reachable for one more release on schemas that never asked for
it, and a shim that emits both shapes *is* the insecure default under another name. The
migration is one line per relation, it is discovered at schema build rather than at runtime, and
the alpha line had already taken a larger break for a smaller reason.

### Decision 8 — `max_collection_cost` is a SHAPE bound, and its default says so

Spec: [Decision 8][spec-047-d8].

*Moved — why the default is `1_000_000_000`.* A legitimate four-level document that leaves every
page unspecified already charges `10**8`, and a bound that rejects ordinary documents is a bound
the first deployment to meet it raises to infinity. The generous default is therefore a
deliberate choice to keep the bound credible, not an admission that it is weak — the row promise
is carried by `max_page_size` and `max_list_rows`, which the spec states.

### Decision 9 — The execution deadline is cooperative, and says so

Spec: [Decision 9][spec-047-d9].

*Moved — why the default is `None`.* A wall-clock deadline a deployment did not choose is a
correctness hazard (it truncates legitimate slow requests), not a safety one — the opposite of
every other bound here, which is why it is the only optional one. Every other bound defaults to
a number because the failure mode of a too-generous bound is a slow request, while the failure
mode of an unchosen deadline is a wrong answer.

### Decision 11 — One typed rejection, and no per-transport translation

Spec: [Decision 11][spec-047-d11].

*Moved — why installation is automatic.* An endpoint whose only limiter is one a consumer
remembered to install is an endpoint with no limiter; that is the audit's finding, and automatic
installation is the answer to it. This is the same reasoning that rejected upstream's
three-extensions shape in the Borrowing posture entry below.

### Decision 13 — Three bounds this policy still owes, and three exclusions that are audited rather than forgotten

Spec: [Decision 13][spec-047-d13].

*Moved — the upstream forensics behind the subscription envelope.* Enforcement is not the gap;
rendering is. A subscription enters `extensions_runner.operation()` and `executing()` exactly as
a query does, so both the document text scan and the value walk run and a violating subscription
is refused. The difference is one `except` clause in upstream's schema: the **non-streaming**
path wraps its whole operation block in a broad `except Exception` that returns a
`PreExecutionError`, so an HTTP or WebSocket query or mutation carries an `errors` entry; the
**streaming** path's only pre-execution `except` names three errors (`MissingQueryError`,
`CannotGetOperationTypeError`, `InvalidOperationTypeError`), so anything an extension raises
escapes it. Upstream's `BaseGraphQLTransportWSHandler.run_operation` then catches that exception,
hands it to `handle_task_exception`, and sends `complete`.

*Moved — the version-drift evidence for "state the behaviour, never the private method name".*
The declared floor is `strawberry-graphql>=0.316.0` with no ceiling, and the seam moves inside
that range: the private implementation is `_subscribe` at the floor and `_stream` at `0.323.2`,
and the **public** attribute a handler dispatches through moved from `subscribe` to `stream` at
`0.319.0` — the same instability [`spec-046`][spec-046]'s stop-aware result source already
answers by wrapping both public names unconditionally rather than testing a version. The
instruction this evidence supports stayed in the spec.

## Deliberation that belonged to no single decision

### Borrowing posture — what was deliberately not borrowed

*Moved.* Strawberry ships `MaxTokensLimiter`, `MaxAliasesLimiter` and `QueryDepthLimiter`; the
spec states what was borrowed from them and that the package declines their shape. The reasons
each was declined are here:

- **Three extensions a consumer must remember.** Optional, consumer-installed, none installed by
  default is the same as absent — which is the audit's finding, not an inference from it. One
  policy object and one extension installed by `DjangoSchema` is the answer.
- **`parse_options["max_tokens"]`.** Upstream routes its token limit into graphql-core's parser,
  which answers with a `GraphQLSyntaxError` carrying no code — indistinguishable to a client from
  a typo. This package counts tokens itself so the rejection carries the same typed code as every
  other bound.
- **Depth measured on the AST.** Upstream's `QueryDepthLimiter` is a validation rule, so it runs
  *after* the parse it would need to protect.

### Risks and open questions — the fallback positions

*Moved.* The spec keeps each preferred answer; the fallbacks it would take if a preferred answer
failed are here.

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
[glossary-joint-version-cut]: ../../GLOSSARY.md#joint-version-cut

<!-- docs/SPECS/ -->
[spec-046]: ../spec-046-transport_security-0_0_14.md
[spec-047]: ../spec-047-resource_policy-0_0_14.md
[spec-047-d1]: ../spec-047-resource_policy-0_0_14.md#decision-1--one-immutable-frozen-dataclass-validated-at-construction
[spec-047-d11]: ../spec-047-resource_policy-0_0_14.md#decision-11--one-typed-rejection-and-no-per-transport-translation
[spec-047-d13]: ../spec-047-resource_policy-0_0_14.md#decision-13--three-bounds-this-policy-still-owes-and-three-exclusions-that-are-audited-rather-than-forgotten
[spec-047-d2]: ../spec-047-resource_policy-0_0_14.md#decision-2--threaded-through-the-request-context-mirroring-the-optimizer-seam
[spec-047-d3]: ../spec-047-resource_policy-0_0_14.md#decision-3--the-document-text-scan-runs-before-the-parse
[spec-047-d4]: ../spec-047-resource_policy-0_0_14.md#decision-4--the-document-and-value-budgets-are-one-iterative-walk
[spec-047-d5]: ../spec-047-resource_policy-0_0_14.md#decision-5--default_relation_shape-becomes-connection-a-clean-alpha-break
[spec-047-d8]: ../spec-047-resource_policy-0_0_14.md#decision-8--max_collection_cost-is-a-shape-bound-and-its-default-says-so
[spec-047-d9]: ../spec-047-resource_policy-0_0_14.md#decision-9--the-execution-deadline-is-cooperative-and-says-so

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
