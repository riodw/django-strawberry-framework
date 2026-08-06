# Adversarial review: spec-046 transport security

This pass reviewed [spec-046][spec-046] from the composition boundary: whether the
new package-owned checks preserve the security policy expressed by the surrounding
Django deployment, and whether the defensive paths remain total when framework-owned
objects return values outside the production happy path. The previously reported
revoked-operation spin and failed-close retry defects are repaired, but four independent
gaps remain.

## Findings

### [P1] A contradictory JSON charset declaration restores the parser differential

`django_strawberry_framework/views.py::_RequestBodyBoundaryMixin.parse_json` strictly
decodes the raw body as UTF-8, but it never validates the `charset` declared on an
`application/json` content type. The only declaration check is
`::_enforce_multipart_form_encoding`, and `::_is_multipart_form_post` deliberately keeps
that check exclusive to multipart POSTs. The package therefore accepts UTF-8 bytes while
the request explicitly tells every other hop that those bytes use another encoding.

This is reachable over the real endpoint, not just by calling `parse_json` directly. A raw
request carrying a valid, non-ASCII UTF-8 JSON document and
`Content-Type: application/json; charset=iso-8859-1` returned `200`, exactly like the same
body without the declaration. The byte sequence `C3 A9`, for example, is `e-acute` to this
view and two Latin-1 characters to a proxy, WAF, audit logger, or signature layer that
honours the declared charset. That is the same one-byte-sequence/two-documents condition
S9 was introduced to remove. The existing package test only proves that the *multipart*
encoding helper is a no-op for JSON; it turns the absence of this boundary into an asserted
behavior without testing the cross-hop consequence.

The root fix is to make the ordinary JSON content type part of the wire boundary before
the body is parsed: an absent declaration or a name that canonicalizes to UTF-8 may pass;
an unknown codec, `utf-8-sig`, or a non-UTF-8 declaration must receive the same controlled
`400` as every other encoding refusal. Add sync and async raw-envelope regressions with a
non-ASCII UTF-8 document, using a driver that does not helpfully re-encode the body from its
declared charset. Pin UTF-8 aliases as successes and contradictory, unknown, and
`utf-8-sig` declarations as refusals.

### [P1] The CSRF reorder bypasses the project's configured CSRF middleware class

`django_strawberry_framework/views.py::_RequestBodyBoundaryMixin.as_view` marks the URL
callback `csrf_exempt`, so the `CsrfViewMiddleware` class actually installed by the project
returns before applying any of its policy. The inner continuation does not re-enter that
configured class: module-level `csrf_protect` is permanently constructed from Django's
stock `CsrfViewMiddleware`. A deployment that subclasses the middleware to strengthen
token binding, tenant checks, logging, or rejection policy silently loses those additions
on the GraphQL endpoint and receives only Django's base implementation.

A direct middleware probe confirms the bypass. A `CsrfViewMiddleware` subclass whose
`_check_token` records entry sees the package callback's `csrf_exempt` flag, returns `None`,
and never enters the override. The view then invokes the separately constructed stock
decorator. This contradicts the architectural claim that Django and the consumer's real
middleware own HTTP security; the body-limit ordering has replaced a deployment policy
rather than merely reordered it.

The root fix needs an ordering mechanism in the actual middleware chain. Put a narrowly
scoped package body-boundary middleware before the configured CSRF middleware (keyed by a
marker on package views), then remove the outer exemption and stock-class re-entry. A
view-local decorator cannot reproduce an arbitrary installed middleware subclass. Add a
regression with a custom `CsrfViewMiddleware` subclass in `MIDDLEWARE`: an over-limit
multipart body must still be refused before parsing, while an under-limit request must
reach and obey the subclass's additional rejection on both view variants.

### [P2] A foreign position object's arithmetic still escapes the fail-closed body gate

`django_strawberry_framework/_request_body.py::_measured_remaining` describes every
operation on a foreign stream as guarded, including the position subtraction. The code,
however, catches only `TypeError` from `end - position`, and performs `remaining <= 0`
outside any guard. A seekable stream can return position objects whose subtraction or
comparison raises any other exception. A minimal stream that restores its starting
position correctly but whose end-position object's `__sub__` raises `RuntimeError`
propagates that exception out of the production helper instead of selecting the bounded
read. At the view boundary that is an unrelated `500`, not the promised controlled,
fail-closed response.

The root fix is to stop executing arbitrary numeric protocols from this foreign object.
Production Django streams report exact built-in integer positions, so accept that measured
shape explicitly; after a verified restore, any other position/end type or unusable result
should be `_Probe.UNMEASURABLE` and take the bounded-read path. If broader numeric support is
intentional, the entire subtraction and comparison must at least be guarded with
`Exception`. Regressions should cover exceptions from both `__sub__` and the ordering
comparison, not only the current `None - int` `TypeError` case.

### [P2] Cancellation of disconnect lets the connection-owned close task outlive the connection

`django_strawberry_framework/consumers.py::_ConnectionRevocation.settle` awaits the close
task through `asyncio.shield`. Shielding protects the close from cancellation, but it does
not make the caller continue awaiting it: cancel `settle()` while the adapter close is
parked and `settle()` finishes with `CancelledError` while the owned attempt remains pending
and the state remains `closing`. A direct production-helper probe produced exactly that
state. `build_revalidating_consumer_class` compounds it because
`GraphQLWebSocketConsumer.disconnect` calls `settle()` only after an unguarded
`await super().disconnect(code)`; cancellation or failure of upstream teardown skips
settlement entirely.

ASGI servers cancel application tasks during shutdown and application-close timeouts, so
this is a real lifecycle boundary rather than a caller misusing a private helper. The
orphaned task retains the adapter, consumer, scope, session, and stale actor, and may remain
parked on a send after the ASGI application has returned. That is the opposite of the
specification's explicit claim that a connection-owned task cannot outlive its connection.

The root fix is to make final teardown the terminal owner, not another shielded waiter.
`disconnect` must enter settlement through `finally`, and cancellation while settling must
cancel and await the owned attempt (or use an equivalent structured-concurrency owner with
a bounded final wait). At that point the socket is already disconnecting, so the earlier
ambiguity about retrying a possibly committed close no longer justifies retaining a task
that has no live connection. Add regressions that cancel `disconnect` with a parked close
and that make `super().disconnect` fail, then assert the close task is done, no task retains
the consumer, and no second close is attempted.

## Verification notes

No pytest suite was run. The findings above were verified with focused, read-only probes
against the installed Django/Channels stack and the production helpers.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

[spec-046]: SPECS/spec-046-transport_security-0_0_14.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
