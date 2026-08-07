# Rationale: spec-048 — Secure output and error defaults (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-048-secure_output_defaults-0_0_14.md`][spec-048]. The spec is
the contract and states only what is currently true; everything that explains **how it got
there** lives here: the alternatives each decision rejected and why each lost, the derivations
that do not change how a decision is implemented, every change a decision has undergone with
the round that caused it, and every claim a decision once made and may no longer make.

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
- **Round attribution.** This card ran a build round, a **remediation round**
  (`docs/builder/bld-048-remediation.md`), and — after the maintainer's release commit — one
  **post-release correction** to the streamed-result seam. Where a decision changed, the entry
  names which.
- **What deliberately stayed in the spec, and why.** The cap table, the opt-in `Meta` key's
  validation contract, the classification table, the replacement error's field list, the two
  fail-closed degrades, goals, non-goals, edge cases, the test plan and the DoD are all
  contract. So is the whole of Decision 13, whose owed-work entries and audited boundaries are
  instructions to a future builder, not a record of thinking.

## Provenance of this record

- **Moved** — cut from the spec by this pass. The nine `Alternatives rejected` blocks
  (Decisions 1, 2, 4, 5, 7, 8, 9, 10, 11), the Borrowing posture's declined-borrowings list,
  Decision 8's allowlist-comparison derivation, and the Risks section's fallback positions.
- **Reconstructed** — rebuilt from the shipped code, the release commit, the remediation
  catalog (`docs/builder/bld-048-remediation.md`), the final-gate artifact
  (`docs/builder/bld-048-final.md`), and the post-release stream-seam commit. The whole of the
  change record below.
- **Deleted, recorded nowhere** — the spec's original `0.0.17` targeting prose and the Status
  block that depended on it. Both were falsified by the program-wide retarget rather than
  superseded by an argument; what replaced them is in the change record's first entry.

## Change record

### The version cut this card predicted it would own

**Falsified, then withdrawn.** The card was authored and built against `0.0.17`, its build plan
declared this card the version-bump owner ("the only non-Done card at `0.0.17`"), and the
original Decision 12 assigned Slice 5 the quintet bump. The maintainer then retargeted the
whole security program — cards 046, 047, 048, and 049 — onto `0.0.14`, the patch cards 041-045
already occupied. `0.0.15`, `0.0.16`, and `0.0.17` were never the version of a released
artifact; `__version__` never held any of them.

So the bump this card claimed does not exist to be owned. The quintet reads `0.0.14`, the card
is `DONE-048-0.0.14`, and Slice 5 folded documentation in and nothing else. The spec's
[Decision 12][spec-048-d12] now states that directly. The lesson is the same one
[`spec-047`'s rationale][spec-047-rationale] records at length: a single-card board scan cannot
establish that a card owns a version cut, because it cannot see what the program's other cards
will be retargeted to.

### The second seam has been rewritten twice

[Decision 11][spec-048-d11] is the decision that moved most, in two distinct rounds.

**Remediation round — masking was bolted to the wrong seam entirely.** The build shipped
`DjangoErrorPolicyExtension` masking only `execution_context.result` at operation teardown. A
subscription delivers one `ExecutionResult` per event through the result source the transport
iterates, and the teardown runs only when the operation *ends* — so every event's raw exception
message reached the wire, and the teardown then rewrote a result nobody read. The remediation
round (finding 1, HIGH) restructured the module into the three shared seams the spec now
documents (`mask_execution_result`, `masking_is_active`, `schema_error_policy`), made
`mask_execution_result` return a masked **copy** (the property that keeps
[Decision 10][spec-048-d10]'s LIFO promise true for extensions reading `original_error`), and
applied it inside `consumers.py::_stop_aware_results`. The masking-helper import there is
function-local because `consumers.py`'s import graph is deliberately `strawberry`-free, so
`routers.py` can import it above its soft-dependency guard.

**Post-release — the seam was an attribute name, and upstream renamed the attribute.** The
stop-aware schema wrapper overrode only `subscribe`. strawberry-graphql **0.319.0** moved the
`graphql-transport-ws` handler's dispatch to `schema.stream` — for *every* operation type — and
the wrapper's `__getattr__` then forwarded that name straight to the real schema. With
`pyproject.toml` declaring `strawberry-graphql>=0.316.0` and no upper bound, a consumer
installing current wheels got a transport where subscription error masking and operation
revocation did not engage — not degraded, **absent, and silently**, because delegation keeps the
protocol working and nothing observable fails except the two guarantees. The legacy
`graphql-ws` handler reads `subscribe` throughout and was never affected. The fix defines
`subscribe` **and** `stream` unconditionally, routed through one shared wrapping step so the two
cannot diverge; `execute` stays delegated because it returns one already-torn-down result and
never loops. Two consequences reshaped the decision's text:

- `stream` is **wider** than `subscribe` — it also runs queries and mutations and yields their
  single result from inside the extension lifecycle — so from 0.319.0 on, a *query's* raw
  exception message reached the wire over `graphql-transport-ws` before the teardown ran.
  The seam is therefore now described as the **streamed-operation** result source, not a
  subscription-only one.
- That width needed one gate. `stream`'s third element type is a raw graphql-core
  incremental-delivery frame (`@defer` / `@stream`) whose errors are nested inside incremental
  payloads; masking one would take the fail-closed degrade, whose value IS an
  `ExecutionResult` — precisely the shape upstream's transport tests for to decide a frame is
  unrenderable and the operation must be rejected — converting a rejection into a malformed
  `next` payload. The gate was extracted as `is_maskable_result` and shared with the
  extension's own teardown, so the two seams cannot drift on the question.

The alternative — an upper bound in `pyproject.toml` — was rejected: unlike django-filter's
audited range, which gates an optional predicate and degrades gracefully, refusing an unaudited
strawberry refuses the whole WebSocket transport, and strawberry is the package's engine rather
than one of its features. Every published wheel from the declared floor to 0.323.2 was read
rather than the one installed version: the union of names the two handler modules take off the
schema they were handed is exactly `{subscribe, stream, execute}`, and no release type-tests
the schema object. The fix also moved `uv.lock` to the top of the range — with the lock at the
floor, every un-pinned CI matrix node is a second floor run and no top-of-range tripwire can
fire — and replaced the transparency row's exact-name-pair assertion with a partition (every
upstream read is either a wrapper-defined name, derived from the class, or an explicitly
reasoned delegation), so a fourth upstream name fails loudly instead of reading as assertion
drift.

### The acknowledgement flag was not validated

**Changed by the remediation round** (finding 2). As built,
`DjangoDebugExtension(allow_unsafe_production="false")` was truthy and **armed** production
disclosure in the act of refusing it. [Decision 5][spec-048-d5]'s non-bool
`ConfigurationError` — `ErrorPolicy.__post_init__`'s rule applied to the same kind of flag,
raised when the engine builds the per-operation instance — was added by the round, not shipped
by the build.

### The degrades and the guarded policy read

**Changed by the remediation round** (finding 3). The build had no degrade path: an exception
raised during masking itself would have escaped, and the policy read was a bare `getattr` whose
default answered only an *absent* attribute — a wrong-shaped `schema.error_policy` (a mapping, a
string, a stray assignment on a consumer subclass) would have been read for truthiness and could
silently disable masking. The round added the two-level fail-closed degrade and the
`isinstance`-guarded `schema_error_policy`, mirroring
`extensions/resource_policy.py::DjangoResourcePolicyExtension._resolved_policy`. Guarding was
chosen over raising at schema construction because `DjangoSchema` already validates there — the
guard exists for a consumer subclass or a stray assignment, which construction cannot see. One
deliberate absence: `_process_result`'s assignment has **no third degrade**, because both
admitted shapes are mutable attribute holders and it cannot fail; an unreachable `try` there
would be untestable coverage.

### Completion-phase classification was verified, not changed

**Remediation round, finding 4.** The round verified that graphql-core wraps every field-phase
exception through `located_error`, so a resolver exception surfaced via value *completion*
(non-null propagation, list-item completion, scalar `serialize`) arrives with `original_error`
set and IS masked. No code change was required; the property was undocumented and untested, so
[Decision 8][spec-048-d8] now states it and two live rows pin it. One test was **deleted** for
pinning a false premise: its docstring claimed a non-nullable-`null` completion error has no
`original_error`, but graphql-core sets it to the completion `TypeError`, so the row asserted a
synthetic object's behavior while claiming to cover a real path. Its replacement drives the
`original_error is None` branch's real traffic — an async validation failure arriving as a
`PreExecutionError`.

### The `Meta`-key normalizer refused a frozenset and misnamed the key

**Changed by the remediation round** (finding 5). `types/base.py::_normalize_sequence_spec`
refused a `frozenset` and reported every rejection against `Meta.exclude`, its original caller.
It now accepts any non-string `Sequence` or `Set` — every key routed through it names an
unordered set of field names, and three of the four normalize to a `frozenset` on the next
line, so refusing the literal a consumer would write for a set would be a shape gate
contradicting its own semantics — and takes the key's name for its message, with all four call
sites passing their own. `str` stays refused (iterable, so one field name would be read as a
sequence of single-character names).

### Payload-cap corrections

**Remediation round, finding 6** (L8 / L10), against [Decision 6][spec-048-d6]:

- `_MAX_PAYLOAD_CHARS` was renamed `_MAX_PAYLOAD_TEXT_CHARS` because the budget counts
  `_row_cost` — the rows' variable-length string values only, not keys, punctuation, or
  numbers — and the old name claimed more than it measured. Value unchanged (262144).
- The spec's original "a payload whose very first row already exceeds the budget admits that
  one row" edge case was **unreachable** — the per-row caps bound one row to ~20K characters
  against a 262144 budget — so it described a fallback the code does not have (the code
  `break`s). The spec now states the unreachability instead.
- The two-phase degrade in `_build_payload` is asymmetric and is now documented truthfully:
  SQL collection keeps the rows serialized before a failure (`list.extend` appends as it
  iterates, including partway through the failing snapshot); exception collection degrades to
  `[]` because `_collect_exceptions` builds its own list and leaves nothing to salvage. A
  degraded exception list hands the whole character budget to SQL.

### Where the opt-in is demonstrated

**Remediation round, finding 6** (L11). The spec's test plan originally demonstrated the
`Meta.filesystem_path_fields` opt-in with a probe type in a probe schema, and named test files
(`test_secure_output_api.py`, `test_debug_gate_api.py`) that do not exist. What ships is the
stronger arrangement and the spec now describes it: `MediaSpecimenWithPathType`
(`primary = False`, naming `attachment` and deliberately not `image`) lives in the **shipped
aggregate schema**, because the per-column claim is only worth anything against a schema where
an un-opted column exists beside an opted-in one. The rows live in
`examples/fakeshop/test_query/test_uploads_api.py`,
`test_debug_extension_api.py`, and `test_error_policy_api.py`.

### Decision 1's fourth bullet claimed GraphQL subtyping

**Remediation round, finding 6** (L12). The bullet originally claimed the Python subclassing
keeps a consumer's fragment on `DjangoFileType` matching an opted-in field. False: Python
inheritance is not GraphQL subtyping, and the four types are four unrelated SDL objects. The
true rationale — one definition of the shared members and their resolvers; future improvements
reach both shapes — replaced it, with the SDL consequence stated and cross-referenced to
[Decision 4][spec-048-d4]'s migration note.

## Borrowing posture — what was declined, and why

*Moved.* What is deliberately **not** borrowed:

- **`MaskErrors`' all-or-nothing default predicate.** It masks every error including this
  package's own deliberate coded rejections, so a client can no longer tell
  `RESOURCE_LIMIT_EXCEEDED` from a crash ([Decision 8][spec-048-d8]).
- **`MaskErrors`' silence.** It carries no correlation identifier, so a masked error is
  unfindable in the log from the client's report.
- **`Schema.process_errors` as the masking seam.** It is a logging hook; see
  [Decision 9][spec-048-d9]'s entry below.
- **Upstream's `path` field.** `strawberry-graphql-django` ships it; continuing to copy it is
  exactly the audit finding ([Decision 1][spec-048-d1]).

### The four rejections Decision 2 named were never the four that shipped

**Corrected by the rationale-extraction pass**, against the shipped code. Decision 2's step 2,
the User-facing API paragraph, and the DoD all listed the opt-in's four
`ConfigurationError`s as *unknown / non-selected / **relation target** / non-file*. The four
`types/base.py::_validate_filesystem_path_targets` actually raises are *unknown /
non-selected / **consumer-authored** / non-file*: there is no distinct relation check — a
relation is refused by the non-file check, because `_field_output_type_for` answers `None`
for it — and the consumer-authored rejection, which the remediation round's own test plan
and `docs/README.md` both describe correctly, was missing from all three lists.

The spec's own Test plan carried the right four throughout, and so did the shipped
`docs/README.md` prose ("...or a column whose annotation or `strawberry.field` you already
own"). That is the standing pattern this repo keeps re-learning: **a downstream doc more
accurate than the spec means the contract moved and the spec did not follow.** Behaviour was
never wrong; three spec passages were.

## Decision 1 — `path` leaves the safe default for two composed opt-in types

[Spec decision.][spec-048-d1] *Moved — alternatives rejected:*

- **Delete `path` entirely.** A real filesystem-path consumer exists (a server-side export job,
  a management surface). Deleting the field forces that consumer to fork the generated type
  wholesale, which loses every future improvement to the file surface and puts a hand-rolled
  `path` resolver — without the storage guard — into consumer code. The audit itself asks for
  "an explicit `Meta` opt-in", not deletion.
- **One type with a nullable `path` that always resolves `None` unless opted in.** The SDL
  still advertises it, introspection still finds it, and a client that sees `path: String` and
  gets `null` files a bug report. Worse, the "unless opted in" branch lives in a resolver,
  which means the security boundary is a runtime condition rather than a schema fact.
- **A global settings flag** (`DJANGO_STRAWBERRY_FRAMEWORK["EXPOSE_FILE_PATHS"] = True`). One
  key silently re-arms every schema, every type, and every column in the process. It is
  invisible in the type's own declaration, so a reviewer reading `DocumentType` cannot tell
  whether `path` is exposed, and there is no per-field audit at all. This is the same argument
  card 047 made against a settings flag restoring the old relation-shape default, and the same
  argument the audit makes against a global debug permission.
- **A permission class on the field.** Per-field permission hooks answer "may this requester
  see it", not "should this schema publish it". The path is not sensitive *per requester*; it
  is server-internal for all of them.

For the change this decision's fourth bullet underwent, see the change record above.

## Decision 2 — The opt-in is a per-field `Meta` key

[Spec decision.][spec-048-d2] *Moved — alternatives rejected:*

- **A schema-wide settings key.** Not per-field, not per-type, not visible in the declaration a
  reviewer reads. See Decision 1's rejection of the same shape.
- **A consumer-authored `strawberry.field`.** Already possible today and still fully
  supported — a consumer can always add their own resolver. Rejected as *the* answer because it
  is undiscoverable (nothing in the package points at it), and because it forces the consumer
  to re-implement `_safe_file_attr`'s storage guard, which they will get wrong: the naive
  spelling either crashes on a remote storage backend that raises `NotImplementedError` for
  `path`, or swallows `SuspiciousFileOperation` along with it.
- **A marker on the model field** (`models.FileField(expose_graphql_path=True)`). Changing a
  Django model to alter a GraphQL surface is the wrong layer. It also makes the opt-in global
  to every `DjangoType` over that model, which defeats the per-type audit, and it puts a
  GraphQL concern into a migration.
- **A `Meta.exclude`-style negative key** (`Meta.hide_filesystem_path`). An opt-*out* means the
  default is unsafe; the whole card is that the default must be safe.

For the normalizer change the round forced, see the change record above.

## Decision 4 — The break is justified

[Spec decision.][spec-048-d4] *Moved — alternatives rejected:* a deprecation release that
keeps `path` and warns (keeps the disclosure, and a deprecation directive nobody reads is not a
mitigation); a settings flag to restore the old default (Decision 1); keeping `path` on
`DjangoFileType` and adding *narrower* types without it (the default stays unsafe, which
inverts the goal).

## Decision 5 — The debug extension fails closed by going inert

[Spec decision.][spec-048-d5] *Moved — alternatives rejected:*

- **Raise a `GraphQLError` / `ConfigurationError` at operation start.** This converts a
  diagnostics misconfiguration into a total production outage: every operation on that schema
  fails. The fail-closed goal here is **non-disclosure**, and inertness achieves it
  completely — nothing sensitive is published either way. A raising extension is additionally
  a denial-of-service lever: anyone who can get a debug entry into a production schema list can
  take the endpoint down, which is a worse outcome than the disclosure it was meant to prevent.
- **Refuse at schema construction.** There is no construction hook on a class entry —
  Strawberry builds the instance per operation, and the class is stored unexamined. Even with a
  hook it would be wrong: `DEBUG` is readable at operation time and can legitimately differ per
  settings override, so a construction-time verdict would be stale for exactly the test and
  multi-settings deployments that need it most.
- **A global settings key** (`DJANGO_STRAWBERRY_FRAMEWORK["ALLOW_UNSAFE_DEBUG"]`). Broader and
  less auditable than a per-schema constructor argument — the audit says so directly, and
  `AGENTS.md`'s "add a settings key only when the feature needs it" rule applies: this feature
  does not need one.
- **Gate on something other than `DEBUG`** (a package-owned "production" setting). Django
  already owns the development/production distinction, every deployment already sets it, and
  inventing a second one guarantees the two disagree.

For the non-bool acknowledgement gate the round added, see the change record above.

## Decision 7 — `DjangoSchema` gets a first-class production error policy

[Spec decision.][spec-048-d7] *Moved — alternatives rejected:* a boolean
`DjangoSchema(mask_errors=True)` (no room for the message or the extension key, and every later
option becomes another constructor argument); a settings-key-only configuration with no schema
argument (a process running two schemas — a public one and an internal one — cannot differ);
validating in the settings reader rather than the dataclass (two gates drift; card 047's
Decision 1 argument applies unchanged).

For the degrades and the guarded read the round added, see the change record above.

## Decision 8 — The classification rule is structural

[Spec decision.][spec-048-d8] *Moved — why this beats a curated code allowlist:* an allowlist
of `extensions.code` values has to be extended by every future rejection site — every new
bound, every new validation, every new mutation guard — and when someone forgets, the allowlist
**fails OPEN**: the new deliberate rejection gets masked, the client sees "An unexpected error
occurred", and the regression is a UX bug nobody attributes to the security card. The
structural rule has the opposite failure mode: a new plain-Python exception anywhere in the
package or in consumer code is masked by default, with no registration step. It fails CLOSED
for exactly the class of thing that is dangerous, and fails open only for something a developer
explicitly typed as client-facing.

*Moved — alternatives rejected:* a curated `extensions.code` allowlist (fails open; above); a
module-prefix check on `type(original_error).__module__` (`__module__` is spoofable, a lesson
this repo already learned in the visibility-boundary work, and it would mask a consumer's
deliberate error while permitting a framework accident); an opt-in exception base class the
consumer must subclass (a registration step, so it fails open the same way an allowlist does,
and `GraphQLError` already *is* that base class).

For the completion-phase verification, see the change record above.

## Decision 9 — Masking is gated on `DEBUG`; the correlation id is the contract

[Spec decision.][spec-048-d9] *Moved — alternatives rejected:*

- **Reuse Strawberry's `MaskErrors`.** It masks everything, including this package's own
  deliberate coded rejections, so `RESOURCE_LIMIT_EXCEEDED` and `GLOBALID_INVALID` become
  indistinguishable from a crash — a direct regression against contracts cards 046 and 047
  just established. It also carries no correlation id, so a masked error cannot be found in the
  log from a user's report.
- **Override `Schema.process_errors`.** It is a **logging** hook: it is handed the errors and
  its return value is discarded. It cannot change what reaches the client, so an implementation
  built on it would have to *also* rewrite the result somewhere else, and then there would be
  two seams.
- **A per-operation single id.** A response carrying two unrelated failures logs two
  exceptions; one id would make the client's report ambiguous about which of them they hit,
  which is the exact question the id exists to answer.
- **Omitting `path` / `locations` from the masked error.** No security gain (the client wrote
  the query), real cost to every client-side error renderer.
- **A monotonic counter or a request-scoped sequence as the id.** Not unique across processes
  or restarts, and a counter leaks traffic volume. A hash of the message or the traceback would
  be an oracle, letting a client distinguish two errors or confirm a guess about the exception
  text — random is the property, not just the convenience.

## Decision 10 — Extension order is load-bearing, and the install prepends

[Spec decision.][spec-048-d10] *Moved — alternatives rejected:* appending for symmetry with the
resource policy (breaks the debug extension's documented contract and, worse, does so
silently — the payload simply reports masked errors); documenting the required order and
leaving it to the consumer (the audit's finding is precisely that consumer-remembered security
is absent security); masking in `get_results` or in the view (per-transport, and there are four
transports).

## Decision 11 — A streamed operation needs a second seam

[Spec decision.][spec-048-d11] *Moved — alternatives rejected:* masking inside the transport's
frame writer (per protocol, and there are two, and the frame is already JSON by then); masking
in the schema's own subscribe generator by subclassing the schema (the schema class is the
consumer's; a wrapper there is invisible to a consumer who builds their own); accepting the gap
for subscriptions (the disclosure is
identical to the query one, and a subscription is exactly the surface where a long-lived client
accumulates them); an upper version bound instead of wrapping the renamed upstream seam (see
the change record — refusing an unaudited strawberry refuses the whole WebSocket transport).

Both rewrites this decision underwent — the remediation round's seam addition and the
post-release `stream` coverage — are in the change record above.

## Risks and open questions — the fallback positions

*Moved.* The spec keeps each risk and its accepted answer; the pre-planned fallbacks, should a
real consumer need appear, were these:

- **`path`-removal migration friction:** a build-time informational log when a type has file
  columns and no `filesystem_path_fields` key — discoverable without re-arming anything.
- **A fragment type condition broken by the SDL type rename:** an interface both types
  implement, which would let a fragment condition survive; deferred because it adds a type to
  every schema for a case no consumer has reported.
- **A real debug-cap ceiling problem:** fold the caps into the `ResourcePolicy` rather than
  adding a second policy object — the resource policy is already the package's one place for
  "what a request may spend".
- **A masked-error log storm:** a policy field capping logged errors per operation, which
  bounds the storm without touching the wire.
- **A `correlationId` key collision:** namespace it under a package-owned sub-object, which is
  uglier for every consumer who does not collide.
- **A consumer re-opening the disclosure via `GraphQLError(str(exc))`:** none; a package that
  second-guesses an explicit `GraphQLError` cannot support deliberate client-facing errors at
  all.

One authoring-time note also lived here and is history rather than contract: no conflict was
found between the card body and the program audit's Step 1 reading; the card's three
architectural-posture bullets carried into the decisions unchanged, and both of the card's open
questions were resolved by the spec (the opt-in shape in [Decision 2][spec-048-d2]; the
correlation-id format, log destination, and message configurability in
[Decision 9][spec-048-d9]).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-047-rationale]: spec-047-resource_policy-0_0_14-rationale.md
[spec-048]: ../spec-048-secure_output_defaults-0_0_14.md
[spec-048-d1]: ../spec-048-secure_output_defaults-0_0_14.md#decision-1--path-leaves-the-safe-default-for-two-composed-opt-in-types
[spec-048-d2]: ../spec-048-secure_output_defaults-0_0_14.md#decision-2--the-opt-in-is-a-per-field-meta-key-validated-exactly-like-the-override-sets
[spec-048-d4]: ../spec-048-secure_output_defaults-0_0_14.md#decision-4--the-break-is-justified-and-carries-a-one-line-migration
[spec-048-d5]: ../spec-048-secure_output_defaults-0_0_14.md#decision-5--the-debug-extension-fails-closed-under-debugfalse-by-going-inert
[spec-048-d6]: ../spec-048-secure_output_defaults-0_0_14.md#decision-6--deterministic-marked-payload-caps-as-module-constants
[spec-048-d7]: ../spec-048-secure_output_defaults-0_0_14.md#decision-7--djangoschema-gets-a-first-class-production-error-policy-shaped-like-the-resource-policy
[spec-048-d8]: ../spec-048-secure_output_defaults-0_0_14.md#decision-8--the-classification-rule-is-structural-not-an-allowlist
[spec-048-d9]: ../spec-048-secure_output_defaults-0_0_14.md#decision-9--masking-is-gated-on-debug-and-the-correlation-id-is-what-reaches-the-client
[spec-048-d10]: ../spec-048-secure_output_defaults-0_0_14.md#decision-10--extension-order-is-load-bearing-and-the-install-prepends
[spec-048-d11]: ../spec-048-secure_output_defaults-0_0_14.md#decision-11--syncasync-parity-comes-from-the-hook-a-streamed-operation-needs-a-second-seam
[spec-048-d12]: ../spec-048-secure_output_defaults-0_0_14.md#decision-12--the-version-bump-belongs-to-the-0014-joint-cut

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
