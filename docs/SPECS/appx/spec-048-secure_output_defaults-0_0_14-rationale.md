# Rationale: spec-048 — Secure output and error defaults (rejected alternatives)

Deliberative companion to [`spec-048-secure_output_defaults-0_0_14.md`][spec-048]. The spec is
the contract; this file holds the alternatives each decision rejected and why each lost, plus
the derivations that do not change how a decision is implemented. A decision with no entry here
is contract in full. A reader looking for what the package *does* wants the spec.

## Borrowing posture — what was declined, and why

What is deliberately **not** borrowed:

- **`MaskErrors`' all-or-nothing default predicate.** It masks every error including this
  package's own deliberate coded rejections, so a client can no longer tell
  `RESOURCE_LIMIT_EXCEEDED` from a crash ([Decision 8][spec-048-d8]).
- **`MaskErrors`' silence.** It carries no correlation identifier, so a masked error is
  unfindable in the log from the client's report.
- **`Schema.process_errors` as the masking seam.** It is a logging hook; see
  [Decision 9][spec-048-d9]'s entry below.
- **Upstream's `path` field.** `strawberry-graphql-django` ships it on its default file type;
  an upstream default is not a security argument ([Decision 1][spec-048-d1]).

## Decision 1 — `path` leaves the safe default for two composed opt-in types

[Spec decision.][spec-048-d1] Alternatives rejected:

- **Delete `path` entirely.** A real filesystem-path consumer exists (a server-side export job,
  a management surface). Deleting the field forces that consumer to fork the generated type
  wholesale, which loses every future improvement to the file surface and puts a hand-rolled
  `path` resolver — without the storage guard — into consumer code.
- **One type with a nullable `path` that always resolves `None` unless opted in.** The SDL
  still advertises it, introspection still finds it, and a client that sees `path: String` and
  gets `null` files a bug report. Worse, the "unless opted in" branch lives in a resolver,
  which means the security boundary is a runtime condition rather than a schema fact.
- **A global settings flag** (`DJANGO_STRAWBERRY_FRAMEWORK["EXPOSE_FILE_PATHS"] = True`). One
  key silently re-arms every schema, every type, and every column in the process. It is
  invisible in the type's own declaration, so a reviewer reading `DocumentType` cannot tell
  whether `path` is exposed, and there is no per-field audit at all — the same argument
  [`spec-047`][spec-047] makes against a settings flag restoring an unsafe relation-shape
  default.
- **A permission class on the field.** Per-field permission hooks answer "may this requester
  see it", not "should this schema publish it". The path is not sensitive *per requester*; it
  is server-internal for all of them.

## Decision 2 — The opt-in is a per-field `Meta` key

[Spec decision.][spec-048-d2] Alternatives rejected:

- **A schema-wide settings key.** Not per-field, not per-type, not visible in the declaration a
  reviewer reads. See Decision 1's rejection of the same shape.
- **A consumer-authored `strawberry.field`.** Always possible and fully supported — a consumer
  can add their own resolver. Rejected as *the* answer because it is undiscoverable (nothing in
  the package points at it), and because it forces the consumer to re-implement
  `_safe_file_attr`'s storage guard, which they will get wrong: the naive spelling either
  crashes on a remote storage backend that raises `NotImplementedError` for `path`, or swallows
  `SuspiciousFileOperation` along with it.
- **A marker on the model field** (`models.FileField(expose_graphql_path=True)`). Changing a
  Django model to alter a GraphQL surface is the wrong layer. It also makes the opt-in global
  to every `DjangoType` over that model, which defeats the per-type audit, and it puts a
  GraphQL concern into a migration.
- **A `Meta.exclude`-style negative key** (`Meta.hide_filesystem_path`). An opt-*out* means the
  default is unsafe; the whole card is that the default must be safe.

The four rejections are *unknown / non-selected / consumer-authored / non-file*; there is no
distinct relation check, because `_field_output_type_for` answers `None` for a relation and the
non-file check refuses it.

## Decision 4 — The break is justified

[Spec decision.][spec-048-d4] Alternatives rejected: a deprecation release that keeps `path`
and warns (keeps the disclosure, and a deprecation directive nobody reads is not a
mitigation); a settings flag to restore the unsafe default (Decision 1); keeping `path` on
`DjangoFileType` and adding *narrower* types without it (the default stays unsafe, which
inverts the goal).

## Decision 5 — The debug extension fails closed by going inert

[Spec decision.][spec-048-d5] Alternatives rejected:

- **Raise a `GraphQLError` / `ConfigurationError` at operation start.** This converts a
  diagnostics misconfiguration into a total production outage: every operation on that schema
  fails. The fail-closed goal here is **non-disclosure**, and inertness achieves it
  completely — nothing sensitive is published either way. A raising extension is additionally
  a denial-of-service lever: anyone who can get a debug entry into a production schema list can
  take the endpoint down, which is a worse outcome than the disclosure it was meant to prevent.
- **Refuse at schema construction.** `DEBUG` is readable at operation time and can legitimately
  differ per settings override, so a construction-time verdict would be stale for exactly the
  test and multi-settings deployments that need it most; and a plain `strawberry.Schema` builds
  a class entry's instance per operation with no construction hook at all.
- **A global settings key** (`DJANGO_STRAWBERRY_FRAMEWORK["ALLOW_UNSAFE_DEBUG"]`). Broader and
  less auditable than a per-schema constructor argument, and [`AGENTS.md`][agents]'s "add a
  settings key only when the feature needs it" rule applies: this feature does not need one.
- **Gate on something other than `DEBUG`** (a package-owned "production" setting). Django
  already owns the development/production distinction, every deployment already sets it, and
  inventing a second one guarantees the two disagree.
- **Interpret a non-bool acknowledgement by truthiness.** Every string a deployment would
  plausibly pass — `"false"`, `"0"`, an environment variable read straight through — is
  truthy, so the gate would arm the disclosure in the act of refusing it.

## Decision 6 — Deterministic, marked payload caps

[Spec decision.][spec-048-d6] Derivations:

- **The budget counts text, not bytes.** `_MAX_PAYLOAD_TEXT_CHARS` is spent by each admitted
  row's variable-length string values only — not keys, punctuation, or numbers — which is
  what the name states. A "first row already exceeds the budget" fallback does not exist: the
  per-row caps bound one row to about 20K characters against a 262144 budget, and admission
  `break`s at the first row that would exceed the running total.
- **The two collection degrades are asymmetric.** SQL collection keeps the rows serialized
  before a failure (the list grows as it iterates, including partway through the failing
  snapshot); exception collection degrades to `[]`, because it builds its own list and leaves
  nothing to salvage. A degraded exception list hands the whole character budget to SQL.

## Decision 7 — `DjangoSchema` gets a first-class production error policy

[Spec decision.][spec-048-d7] Alternatives rejected:

- **A boolean `DjangoSchema(mask_errors=True)`.** No room for the message or the extension
  key, and every later option becomes another constructor argument.
- **A settings-key-only configuration with no schema argument.** A process running two
  schemas — a public one and an internal one — cannot differ.
- **Validating in the settings reader rather than the dataclass.** Two gates drift; the
  argument [`spec-047`][spec-047] makes for its own policy applies unchanged.
- **Letting a supplied `DjangoErrorPolicyExtension` entry replace the schema's masker.** An
  entry is reachable from every resolver through `info.schema.extensions`, and a subclass or a
  factory can override or swap the one hook that masks while answering every inheritance
  check for it. The masker is therefore built by the schema per operation from its private
  record, a supplied exact entry is a no-op declaration, and a subclass or a factory that
  resolves to the masker is refused.
- **Raising on a wrong-shaped policy instead of guarding the read.** `DjangoSchema` already
  validates at construction; `schema_error_policy`'s `isinstance` guard exists for the
  schemas construction cannot see — a plain `strawberry.Schema` carrying the exported
  extension, or a wrong-typed `error_policy` attribute — and it falls back to the masking
  policy, because an extension whose whole job is to mask must not become a no-op because it
  could not find its configuration.

## Decision 8 — The classification rule is structural

[Spec decision.][spec-048-d8] Why this beats a curated code allowlist: an allowlist of
`extensions.code` values has to be extended by every future rejection site — every new
bound, every new validation, every new mutation guard — and when someone forgets, the allowlist
**fails OPEN**: the new deliberate rejection gets masked, the client sees "An unexpected error
occurred", and the regression is a UX bug nobody attributes to the security card. The
structural rule has the opposite failure mode: a new plain-Python exception anywhere in the
package or in consumer code is masked by default, with no registration step. It fails CLOSED
for exactly the class of thing that is dangerous, and fails open only for something a developer
explicitly typed as client-facing.

Alternatives rejected: a curated `extensions.code` allowlist (fails open; above); a
module-prefix check on `type(original_error).__module__` (`__module__` is spoofable, and it
would mask a consumer's deliberate error while permitting a framework accident); an opt-in
exception base class the consumer must subclass (a registration step, so it fails open the
same way an allowlist does, and `GraphQLError` already *is* that base class).

## Decision 9 — Masking is gated on `DEBUG`; the correlation id is the contract

[Spec decision.][spec-048-d9] Alternatives rejected:

- **Reuse Strawberry's `MaskErrors`.** It masks everything, including this package's own
  deliberate coded rejections, so `RESOURCE_LIMIT_EXCEEDED` and `GLOBALID_INVALID` become
  indistinguishable from a crash. It also carries no correlation id, so a masked error cannot
  be found in the log from a user's report.
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

## Decision 10 — Extension order is load-bearing

[Spec decision.][spec-048-d10] Alternatives rejected: appending the masker for symmetry with
the resource policy (breaks the debug extension's documented contract and does so silently —
the payload simply reports masked errors); documenting the required order and leaving it to
the consumer (consumer-remembered security is absent security); masking in `get_results` or
in the view (per-transport, and there are four transports).

## Decision 11 — Streamed operations and hook failures need their own seams

[Spec decision.][spec-048-d11] Alternatives rejected:

- **Masking inside the transport's frame writer.** Per protocol, and there are two, and the
  frame is already JSON by then.
- **Masking in the schema's own subscribe generator by subclassing the schema.** The schema
  class is the consumer's; a wrapper there is invisible to a consumer who builds their own.
- **Accepting the gap for subscriptions.** The disclosure is identical to the query one, and a
  subscription is exactly the surface where a long-lived client accumulates them.
- **An upper `strawberry-graphql` bound instead of wrapping both dispatch names.** The
  stop-aware wrapper is a delegating object, so an upstream dispatch name it does not define is
  forwarded to the real schema and the protocol keeps working minus the masking and the
  revocation stop — absent, and silently. `graphql-transport-ws` dispatches every operation
  type through `schema.stream` (from strawberry-graphql `0.319.0`), the legacy `graphql-ws`
  handler through `subscribe`. Unlike django-filter's audited range, which gates an optional
  predicate and degrades gracefully, refusing an unaudited Strawberry would refuse the whole
  WebSocket transport, and Strawberry is the package's engine rather than one of its features.
  So the wrapper defines `subscribe` and `stream` through one shared wrapping step, `execute`
  stays delegated because it returns one already-torn-down result and never loops, and
  `tests/test_routers.py` re-derives the read set from the INSTALLED handler modules as a
  partition, so an unaudited new name fails loudly. That tripwire only protects consumers if
  some CI node runs the top of the range, which is why `uv.lock` tracks it
  ([`spec-049`][spec-049] Decision 1).

## Risks and open questions — the fallback positions

The spec keeps each risk and its accepted answer; the pre-planned fallbacks, should a real
consumer need appear, are these:

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

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-047]: ../spec-047-resource_policy-0_0_14.md
[spec-048]: ../spec-048-secure_output_defaults-0_0_14.md
[spec-048-d1]: ../spec-048-secure_output_defaults-0_0_14.md#decision-1--path-leaves-the-safe-default-for-two-composed-opt-in-types
[spec-048-d2]: ../spec-048-secure_output_defaults-0_0_14.md#decision-2--the-opt-in-is-a-per-field-meta-key-validated-exactly-like-the-override-sets
[spec-048-d4]: ../spec-048-secure_output_defaults-0_0_14.md#decision-4--the-break-is-justified-and-carries-a-one-line-migration
[spec-048-d5]: ../spec-048-secure_output_defaults-0_0_14.md#decision-5--the-debug-extension-fails-closed-under-debugfalse-by-going-inert
[spec-048-d6]: ../spec-048-secure_output_defaults-0_0_14.md#decision-6--deterministic-marked-payload-caps-as-module-constants
[spec-048-d7]: ../spec-048-secure_output_defaults-0_0_14.md#decision-7--djangoschema-gets-a-first-class-production-error-policy-shaped-like-the-resource-policy
[spec-048-d8]: ../spec-048-secure_output_defaults-0_0_14.md#decision-8--the-classification-rule-is-structural-not-an-allowlist
[spec-048-d9]: ../spec-048-secure_output_defaults-0_0_14.md#decision-9--masking-is-gated-on-debug-and-the-correlation-id-is-what-reaches-the-client
[spec-048-d10]: ../spec-048-secure_output_defaults-0_0_14.md#decision-10--extension-order-is-load-bearing-and-the-error-policy-is-first
[spec-048-d11]: ../spec-048-secure_output_defaults-0_0_14.md#decision-11--syncasync-parity-comes-from-the-hook-a-streamed-operation-and-a-hook-failure-need-their-own-seams
[spec-049]: ../spec-049-dependency_ci_hardening-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
