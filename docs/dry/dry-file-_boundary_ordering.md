# DRY review: `django_strawberry_framework/_boundary_ordering.py`

Status: verified

## System trace

The module is the shared vocabulary of the request-body boundary's ordering (spec-046
Decision 18). It owns, and nothing else may spell:

- four marks — `_BOUNDARY_MARKER` (callback carries a package view's mount),
  `_BOUNDARY_ENFORCED` (request whose body a chain participant measured),
  `_BOUNDARY_MOUNT` (per-mount token), `_BOUNDARY_PREPARED_VIEW` (`(mount, view)`
  handoff on the request);
- one name — `_BOUNDARY_METHOD`, the boundary method the middleware probes for and
  invokes;
- one carrier — `_boundary_middleware_request`, the `ContextVar` publishing the
  request the boundary middleware is handling;
- one answer — `_CsrfOrderingExemption` (the `_CSRF_ORDERING_EXEMPTION` singleton)
  whose `__bool__` withdraws the callback's CSRF exemption exactly when both the
  ContextVar and the enforced stamp say the chain supplied this request's ordering.

It exists because `views.py` (which owns the boundary itself) and
`middleware/request_body.py` (which owns where it runs in the lifecycle) must agree
per request in both directions yet must not import each other. Every writer/reader
pair of every mark straddles those two modules and meets only here.

Consumers traced end to end: `views.py::_RequestBodyBoundaryMixin.as_view` stamps
MARKER/MOUNT and installs the exemption on the returned callback, and its
`prepared_view` closure consumes PREPARED_VIEW before dispatch;
`views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once` reads ENFORCED;
`middleware/request_body.py::_package_view_instance` recognizes via MARKER +
`view_class`/`view_initkwargs` + a callable METHOD probe, `process_view` runs
setup then the METHOD-named boundary and writes MOUNT-derived PREPARED_VIEW plus
ENFORCED, and `__call__` / `__acall__` set/reset the ContextVar around the
downstream chain. Tests: `tests/test_views.py` (recognition declines, startup
misordering refusal, exemption states, prepared-instance handoff, duplicate-entry
idempotence) and `examples/fakeshop/test_query/test_transport_api.py` (live chain:
shipped `MIDDLEWARE` supplies the ordering, the marker survives `ensure_csrf_cookie`,
a setup-derived cap binds through the prepared instance). Prose media restating the
behavior: spec-046 Decision 18, the GLOSSARY `DjangoGraphQLView` /
`GraphQLRequestBodyBoundaryMiddleware` entries, `docs/TREE.md`'s one-liner. Lockstep
surface: renaming any mark or the boundary method moves owner + writer + reader
sides, which is precisely what the constants and two identity-pin tests hold
together.

## Verification

Axis discharge:

1. **Cross-flavor policy mirroring** — searched sibling recognitions of "is this our
   view": `middleware/debug_toolbar.py::DebugToolbarMiddleware.process_view`
   recognizes by upstream `BaseView` subclass; the boundary middleware recognizes by
   marker + bookkeeping + boundary probe. Different questions with different failure
   economics (a lost dev-tool tag vs a lost ordering or an uncontrolled 500), so no
   rule exists to mirror; no third consumer of either recognition exists. A package
   sweep of `csrf` shows only `views.py` and `middleware/request_body.py` own it.
2. **Sync and async twins** — everything this module defines is colorless by design:
   the exemption answers from a per-request fact and the `ContextVar` was chosen over
   thread-locals so the async chain sees it. The only await-boundary twins live
   downstream in other files (`request_body.__call__` / `__acall__`, the two
   `as_view` closures), differ in reset timing and dispatch shape rather than policy,
   and are exercised per transport. No twin of anything owned here.
3. **Derived rather than repeated knowledge** — repo-wide grep for the raw attribute
   spelling `graphql_request_body_boundary`: exactly two sites existed, the owning
   constant and one stray literal inside
   `tests/test_views.py::test_middleware_ignores_an_unreadable_optional_mount_handoff`
   (fixed below; see Opportunities). `_BOUNDARY_METHOD` duplicating the mixin
   method's name is irreducible without importing `views.py` — the exact coupling the
   module exists to prevent — and is pinned bidirectionally by
   `tests/test_views.py::test_the_probed_boundary_method_is_the_one_the_package_views_define`
   and `tests/test_views.py::test_the_middleware_runs_the_boundary_it_probed_the_class_for`.
4. **Inverse and round-trip pairs** — every mark has writer and reader halves in
   different modules and all five pairs are unified through this module's constants,
   which is the module's whole reason to exist. The residual grammar restatement is
   the `(mount, view)` payload shape: packed at the writer, arity/type/token-checked
   at the reader. That check is verification of untrusted content on a shared request
   bag against the reader's own mount token, so it cannot be deleted by co-locating a
   container; drift is loud (handoff tests plus the fakeshop setup-limited live row).
5. **Contracts restated in another medium** — prose media describe behavior but hold
   no parallel machine-readable contract; generated artifacts that mention the module
   (`examples/fakeshop/apps/kanban/constants.py` path allowlist,
   `scripts/review_inspect.py` token markers) are unrelated domains or mere path
   listings.

Single-edit-site counts:

- *Rename the marker value* (e.g. shorten or version `graphql_request_body_boundary`):
  before this review's fix, 2 sites — the constant here plus the stray test literal,
  whose failure would misdirect the renamer toward a mount-handoff subject; after the
  fix, 1 site.
- *Stamp becomes a per-run token instead of `True`*: writer plus all three readers
  move regardless, because each reader encodes its own policy (duplicate-entry
  idempotence, view-local skip, exemption withdrawal); a shared read predicate saves
  nothing and couples three independent reasons to change — rejected.
- *Rename the mixin's boundary method*: def site plus the constant value move, call
  sites read the constant, and the identity-pin test forces awareness — count 2 in
  production with a loud guard, accepted as the floor under the no-import constraint.
- *Prepared-view payload gains a third element*: pack site plus reader arity check,
  2 sites in one change joined by the constant's documented shape — the validation
  contract itself, not removable knowledge.

Strongest rejected candidates: the three-reader ENFORCED access idiom (flag usage,
not duplicated knowledge — the flag has one writer, one canonical name, and readers
with disjoint reasons to change); the reproduced Django setup-failure message in
`process_view` (upstream-parity contract, pinned by
`tests/test_views.py::test_the_middleware_preserves_djangos_setup_super_call_invariant`,
same pattern as `views._JSON_PARSE_REASON`); a shared pack/unpack owner for the
prepared-view tuple (adds protocol surface, deletes no knowledge).

## Opportunities

**Repeated responsibility:** the marker mark's attribute-name string, stated once as
the protocol constant and once more as a raw class-body literal in a test.

**Sites:** `django_strawberry_framework/_boundary_ordering.py::_BOUNDARY_MARKER`
(owner) and the literal in
`tests/test_views.py::test_middleware_ignores_an_unreadable_optional_mount_handoff`.
Every other forged callback in the file — nine `setattr(..., _BOUNDARY_MARKER, True)`
sites — already reaches the constant, and the same test body used the `_BOUNDARY_MOUNT`
constant for its interceptor while stamping the marker literally.

**Evidence:** posited change = rename the marker value. Forced sites before the fix:
owner + literal (count 2). The literal adds no independence: if only the constant's
value changed, every constant-following client keeps working and the literal alone
breaks, failing a test whose subject is the guarded mount read — noise, not signal.

**Owner:** the constant, already imported into the test file alongside the other four
marks.

**Consolidation:** stamp the forged callback via
`setattr(Callback, _BOUNDARY_MARKER, True)` — the file's own convention — instead of
an in-class literal.

**Proof:** the existing rows remain the proof; execution paths are unchanged (class
attribute vs post-definition `setattr`), including the guard arm the interceptor
exercises. No new test needed for a de-duplicated spelling; pytest deferred per
repository rules.

**Risks / non-goals:** none behavioral. Forged `def _enforce_request_boundary`
methods in tests keep their literal names — Python def syntax admits no alternative,
and the central identity-pin test holds that pair together.

## Judgment

This module is itself the consolidation the cycle looks for: it takes five
writer/reader agreements out of two mutually non-importing modules and states each
once. The system around it is single-sourced — recognition, ordering refusal,
exemption states, and handoff all trace back to these constants, and prose media add
description rather than parallel contract. One real defect surfaced off-axis from the
target itself: a test spelled the marker name literally against the file's own
nine-site convention, giving a rename a second forced site and a misleading failure
mode. Fixed at the only root owner a test literal has — the import. Everything else
examined survived disproof.

## Implementation (Worker 1)

- `tests/test_views.py::test_middleware_ignores_an_unreadable_optional_mount_handoff`:
  replaced the raw `graphql_request_body_boundary = True` class-body literal with
  `setattr(Callback, _BOUNDARY_MARKER, True)` after the class definition, matching the
  file's established convention; the constant was already imported.
- `uv run ruff format .` and `uv run ruff check --fix .` run (tree clean of findings in
  scope; two auto-fixes landed in concurrently-edited files owned by other workers).
- pytest deferred — not authorized for this item.

## Independent verification (Worker 2)

Re-traced the connected behavior from source, not from the artifact. All five
writer/reader agreements confirmed where claimed: MARKER written
(`views.py::as_view`, `setattr(view, _BOUNDARY_MARKER, True)`) and read
(`middleware/request_body.py::_package_view_instance`); ENFORCED with one writer
(`process_view`, after the boundary) and three readers with disjoint policies
(idempotence guard at the top of `process_view`, once-guard in
`_enforce_request_boundary_once`, exemption withdrawal in `_CsrfOrderingExemption.__bool__`);
MOUNT written beside the marker and read into the handoff; PREPARED_VIEW packed as
`(mount, view)` and unpacked behind the tuple-arity/mount-token check in
`prepared_view`; METHOD defined once on the mixin, its name read twice by the
middleware (probe + invoke) through the constant. The ContextVar is set/reset around
the downstream chain in both transports.

Scoped-diff verification: `git diff d2d85d5 -- tests/test_views.py` shows exactly the
claimed hunk pair (raw class-body literal removed, `setattr(Callback, _BOUNDARY_MARKER,
True)` added); the target module, `views.py`, and `middleware/request_body.py` have
zero diff against the cycle baseline. Repo-wide sweeps find every raw mark string
(`graphql_request_body_boundary*`) only inside the owning constants, and ten forged-callback
stamp sites in `tests/test_views.py` all go through the constant — the nine recorded plus
the converted one. Semantics preserved: same attribute name via the constant's value,
same truthiness, installed before the probe runs, and the `__getattribute__`
interceptor still raises on the MOUNT read so the guarded-handoff arm is exercised;
assertions unchanged.

Independent single-edit-site counts, posited fresh:

- Rename the mixin's boundary method: def site + constant value = 2 production sites;
  call sites read the constant; the bidirectional identity-pin test forces awareness.
  Matches the recorded floor under the no-import constraint.
- Change the marker string value: 1 site (the constant) — grep-confirmed.
- Prepared-view payload gains a third element: pack site + reader arity check = 2 sites,
  joined by the documented shape. Matches.

Axis challenges: the debug-toolbar sibling recognition genuinely answers a different
question (`issubclass(view_class, BaseView)` tagging vs marker + bookkeeping +
callable-probe + buildable-instance recognition) with different failure economics; a
csrf sweep shows no third production owner beyond `views.py` and
`middleware/request_body.py`; sync/async twins live downstream in other files and are
each file's own review; prose media hold description, not a machine-readable parallel
contract. One further derivation candidate probed and rejected: the four mark strings
share a textual prefix, but each token is an independent contract name already spelled
exactly once — deriving suffixes from a prefix would couple four freely-evolving names
while deleting no repeated fact. Over-derivation, not missed consolidation.

Matrix discharged on the real surface; counts hold; the single edit is genuine,
minimal, and semantics-preserving. Verified.
