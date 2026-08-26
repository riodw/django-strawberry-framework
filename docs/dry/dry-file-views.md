# DRY review: `django_strawberry_framework/views.py`

Status: verified

## Independent verification (Worker 2)

Scoped diff `git diff bb21db0 -- django_strawberry_framework/views.py` is empty; concurrent work
touches other files only. Independently re-traced the module end to end: the precedence ladder
(`_resolved_max_request_body_bytes` → `conf.py::max_request_body_bytes_setting`, default declared
once at `conf.py #"return getattr(settings, MAX_REQUEST_BODY_BYTES_KEY, 1_048_576)"`), the
declared-length gate before the counted check, the POST-scoped multipart carve-out through the one
`_is_multipart_form_post` discriminator, the header-only charset/form-encoding guards, the loss
detector ahead of `json.loads`, the strict decode delegating through `super()`, both CSRF
continuations wrapped once at import, and the stamp/consume protocol against
`middleware/request_body.py` and `_boundary_ordering.py` (`as_view` stamps;
`prepared_view` consumes; `process_view` runs `_BOUNDARY_METHOD` and writes `_BOUNDARY_ENFORCED`;
`_CsrfOrderingExemption.__bool__` reads it).

Re-probed the rejected candidates against installed upstream source and this repo:

- **JSON-reason twin.** Upstream's literal confirmed verbatim at
  `.venv/.../strawberry/http/base.py #"Unable to parse request body as JSON"`. The non-import rule
  is real on the patch side (`_strawberry_patches.py #"must stay importable"` / lines 440-442) and
  restated by the pinning test itself (`tests/test_views.py #"- which stay separate so neither
  module has to import the other"`, lines 2143-2145); `views.py` states identity-with-upstream as
  the contract and names that test. Challenged the "no neutral home" premise directly:
  technically one exists (`_strawberry_patches.py` already imports `.conf`; `exceptions.py` is
  already imported here), so consolidation is *possible* — but it buys exactly one announced edit
  on an upstream-rename event (the standing pin
  `tests/test_views.py::test_the_wire_reason_is_upstreams_own_parse_json_literal` compares both
  spellings to upstream's LIVE raise either way, so drift can never be silent), at the cost of
  moving wire text out of both raise-site contexts into an unrelated error-helper/settings module
  and coupling the patch module to yet another first-party import for a value whose whole meaning
  is local ("upstream's own literal"). One fact held twice with a continuous equivalence proof is
  cheaper kept than merged; rejection stands. Minor wording note: "both modules state the
  constraint in place" is generous about `views.py` specifically — the view side documents the
  identity contract and the pin rather than a literal non-import rule — but the substance holds.
- **HTTPException→response pair.** Read installed
  `.venv/.../strawberry/django/views.py`: `dispatch` translates inline in EACH view class
  (`#"except HTTPException as e:"`, twice), no reusable seam; the middleware has exactly one
  `except HTTPException` arm (`middleware/request_body.py #"content_type=\"text/plain\""`). A
  package helper used at that one package site relocates the statement without removing it. Sound.
- **Multipart control fields.** `testing/client.py #'{"operations", "map"} & set(files)'` guards
  the client's OWN envelope spread order (its message says so: "the 'operations' / 'map' fields are
  built by this client"), a different responsibility from the server-side loss-detector list; the
  names are fixed by the frozen GraphQL multipart request specification, and drift fails loudly on
  both sides through existing live rows. Sound.
- **`resolved_revalidation_window`.** Confirmed different failure arms (float/`nan`/`inf`/
  `OverflowError` vs int-exact/`<= 0`/None-sentinel ladder), different domains, shared idiom only;
  `describe_value` is already the consolidated tail renderer (`exceptions.py`). Anti-goal per
  DRY.md. Sound.

Matrix discharged against the real surface: axis 1 re-swept (`text/plain`, `"operations"|"map"`,
`HTTPException(` raise sites — package-wide they exist only in `views.py`,
`_strawberry_patches.py`, and the middleware; no third owner of status/reason policy; `413` absent
from consumers/routers/schema); axis 2 four pairs behavior-compared with the parity pins read
(`tests/test_views.py:2735` asserts coroutine marking, non-identity with the undecorated
functions, and no inner `csrf_exempt`); axis 3 re-derived (`1_048_576` only in `conf.py`;
`_UTF8_CODEC_NAME` derived once via `codecs.lookup`; GET-scope triplication read at all three
sites — three distinct rationales confirmed); axis 4 (`grep graphql_request_body_boundary` shows
both consumers import every mark from `_boundary_ordering.py`, none restates a literal);
axis 5 (reason strings appear raw only where the wire bytes ARE the subject — the live rows whose
docstrings say only the exact reason distinguishes upstream's own refusals; GLOSSARY describes
status/shape and quotes neither string, confirmed by grep).

Single-edit-site recount, own examples: (a) "reword the over-limit wire reason" — production
forced site is exactly `views.py::_BODY_LIMIT_REASON`; `tests/test_views.py` and
`examples/fakeshop/test_query/test_transport_api.py` consume the imported symbol; GLOSSARY and
spec-046 do not quote it. Count 1, holds. (b) "rename the boundary marker attribute value"
(`graphql_request_body_boundary`) — forced site is exactly `_boundary_ordering.py`; every consumer
imports the name. Count 1. The claimed counts reproduce.

Zero-edit result confirmed as proved: search quality adequate, boundaries challenged and held,
counts verified. pytest remains deferred (not requested).

## System trace

`DjangoGraphQLView` / `AsyncDjangoGraphQLView` are the package's thin subclasses of Strawberry's
Django views, mounted by the consumer's URLconf (`examples/fakeshop/config/urls.py`). The module
owns, through the shared `_RequestBodyBoundaryMixin`, the whole raw-request-body boundary on the
HTTP path: the cumulative cap (precedence ladder in
`views.py::_resolved_max_request_body_bytes`, declared-length gate in
`views.py::_declared_content_length`, measurement delegated to `_request_body.py::body_exceeds_limit`),
and the strict UTF-8 wire contract (`views.py::_RequestBodyBoundaryMixin.parse_json`, the header-only
guards `_form_encoding_is_utf8` / `_declared_charset_is_unhonourable` /
`_reject_lossy_multipart_control_fields`, and the sync body source
`_RawBodyRequestAdapter`). `as_view` stamps the ordering marks defined once in
`_boundary_ordering.py`; `middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware` runs the
same boundary object from the chain and writes `_BOUNDARY_ENFORCED`, which withdraws the CSRF
exemption (`_boundary_ordering.py::_CsrfOrderingExemption`) so the project's configured CSRF class
runs behind the gate; without the middleware the view re-enters CSRF itself through the
`csrf_protect`-wrapped continuations. Fakeshop installs the middleware ahead of `CsrfViewMiddleware`
(`config/settings.py`), and `examples/fakeshop/test_query/test_transport_api.py` plus
`test_products_api.py` exercise both transports over live HTTP; `tests/test_views.py` (3999 lines)
owns the unit-tier contract. The WebSocket transport (`consumers.py`) shares no body machinery: a
WebSocket has no request body, and nothing there restates the cap, the statuses, or the reasons.

## Verification

Axis 1 — cross-flavor policy mirroring. Searched: `grep -rn "text/plain"` (package: one producer,
`middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view`; upstream's
`dispatch` is the other — see below), `"operations"|"map"` (three package sites, judged below),
`csrf_exempt|classonlymethod` (one stamping site, the mixin), `CONTENT_LENGTH` (one reader,
`views.py::_declared_content_length`). Read `consumers.py` end to end: the WebSocket flavor carries
no mirrored body/encoding/status policy — its only deliberate parallel is
`consumers.py::resolved_revalidation_window`, whose docstring says it is "shaped after"
`views.py::_resolved_max_request_body_bytes`. Disproved as duplication: different domain (float
seconds vs int bytes), different setting, different failure arms (`nan`/`inf` vs `<= 0`), different
reasons to change; a shared numeric-setting validator would couple two unrelated subsystems, which
DRY.md names as the anti-goal. Extensions layer (`extensions/error_policy.py`,
`extensions/resource_policy.py`) shapes execution results and variable depth, not the transport
boundary — different objects, different timing (after/before execution), no shared contract.

Axis 2 — sync and async twins. Four pairs compared by behavior: the CSRF continuations
(`views.py::_run_after_csrf_check` / `views.py::_async_run_after_csrf_check`), the two `run`
overrides, the two `parse_multipart` overrides, and the middleware's `__call__` / `__acall__`. All
are forced by framework inspection, not habit: upstream's `dispatch` and Django's
`decorator_from_middleware` branch on `iscoroutinefunction`, so one callable cannot serve both
transports (pinned by
`tests/test_views.py::test_each_csrf_continuation_matches_the_transport_it_protects`, stated as
confirmed by execution at the 5.2 floor). The policies themselves are color-free: `parse_json`, the
boundary methods, and `_reject_lossy_multipart_control_fields` each exist once on the mixin
(structurally pinned by
`tests/test_views.py::test_both_package_views_resolve_parse_json_to_the_one_shared_mixin_method`),
and both transports run live under `examples/fakeshop/test_query/test_transport_api.py`. No
drift channel found.

Axis 3 — derived rather than repeated knowledge. Searched: `max_request_body_bytes` outside
`views.py` (policy stays in views; `conf.py::max_request_body_bytes_setting` owns the reading),
`1_048_576` (declared once, `conf.py`; the view never restates it), `_UTF8_CODEC_NAME` (derived once
via `codecs.lookup`, consumed twice), `_BOUNDARY_METHOD` (constant in `_boundary_ordering.py`
against a method defined in `views.py` — the one true cross-module name coupling, pinned in both
directions by `tests/test_views.py::test_the_probed_boundary_method_is_the_one_the_package_views_define`
and `::test_the_middleware_runs_the_boundary_it_probed_the_class_for`). Candidate: the GET-scoping
fact appears as early-returns in `_enforce_request_body_limit` and `_enforce_body_charset_declaration`
plus the POST clause of `_is_multipart_form_post`. Disproved: these are three distinct scope
decisions with distinct rationales (cap skips GET because no body is read; charset guard excludes GET
*and* multipart for different reasons; the multipart discriminator defines multipart-ness itself), and
a merged scope predicate would hide each rationale behind one table.

Axis 4 — inverse and round-trip pairs. The stamp/consume round trips (marks written by
`_RequestBodyBoundaryMixin.as_view`, consumed by `prepared_view`, the middleware, and
`_CsrfOrderingExemption`) share one grammar in `_boundary_ordering.py` — already the root owner, no
second spelling found (`grep -rn _BOUNDARY_` confirms both sides import, none restate). The
raise/translate pair is real: views raises `HTTPException` and something must turn it into the
`text/plain` response. Two translators exist — upstream's `dispatch` (read from the installed
strawberry source: inline in each view class, no reusable seam) and the middleware's `except` arm
(`middleware/request_body.py::process_view #"content_type=\"text/plain\""`). Disproved as a
consolidation target: the middleware must not import `views.py` or anything that imports it (module
contract), upstream exposes no function to call, and a package helper used at exactly one package
site relocates rather than removes the statement. The non-attributability property is enforced by
tests instead, which is the available mechanism.

Axis 5 — contracts restated in another medium. The wire reasons exist in four media:
`views.py::_BODY_LIMIT_REASON` / `views.py::_JSON_PARSE_REASON` (owners),
`examples/fakeshop/test_query/test_transport_api.py` (imports the symbols; a few raw-byte asserts),
`docs/GLOSSARY.md` (prose describes status/shape, never quotes the reason strings — verified by
`grep "Request body exceeded"`: hits only in spec-046 and `views.py`), and spec-046 (historical
record). Behavior + behavioral pin + shipped-behavior doc + design history is the canonical quartet;
a wire change SHOULD move them together, so this is intentional repetition, preserved per DRY.md.
The one intra-package restatement worth recording is below.

Single-edit-site counts (posited changes):

1. "Reword the over-limit wire reason": forces exactly one production site
   (`views.py::_BODY_LIMIT_REASON`); the live tests consume the imported symbol and follow
   automatically; GLOSSARY does not quote it. **Count 1** — the constant is the true single owner.
2. "Upstream renames its `parse_json` rejection message": forces
   `views.py::_JSON_PARSE_REASON`, `_strawberry_patches.py::_UPSTREAM_JSON_PARSE_REASON`, and the
   pinning test. **Count 2 (+pins)** — adjudicated below.
3. "The multipart request specification adds a third control document":
   forces `views.py::_MULTIPART_CONTROL_FIELDS` and `testing/client.py`'s reserved set
   (`testing/client.py #"'{\"operations\", \"map\"} & set(files)"`). **Count 2** — adjudicated below.
4. "Add a response header to every boundary refusal": forces the middleware's local translation arm
   only (view-side refusals ride upstream's `dispatch` untouched). **Count 1 per arrangement** —
   the asymmetry is upstream's shape, not a package fork.

Scratch experiments: none needed beyond reading installed upstream sources
(`strawberry.http.base.BaseView.parse_json`, `strawberry.django.views.GraphQLView.dispatch`,
`cross_web.DjangoHTTPRequestAdapter.body`) to confirm the literals, the eager sync decode, and the
absence of a reusable exception-translation seam. `git diff bb21db06869787fa788a2bffc1cf4587a6d3a887`
shows none of the four boundary files touched by concurrent work.

Strongest rejected candidates:

- **The two JSON-parse-reason constants.** `views.py::_JSON_PARSE_REASON` and
  `_strawberry_patches.py::_UPSTREAM_JSON_PARSE_REASON` spell the same upstream-derived literal, and
  the non-attributability contract (spec-046 Decision 9) makes identity between them load-bearing.
  Tried to disprove the *duplication*: failed — same fact, same change axis, count 2. Tried to
  disprove the *need to consolidate*: succeeded. Both modules state the constraint in place: neither
  may import the other (the patch module must stay independently deletable and reach into no view
  surface; the view must not sit downstream of patch lifecycle), and a third neutral module would
  add a file whose entire content is one string to serve two readers whose agreement is already
  mechanically enforced by
  `tests/test_views.py::test_the_wire_reason_is_upstreams_own_parse_json_literal`, which checks both
  constants against upstream's live raise. Drift cannot happen silently; consolidation buys one
  edit on an upstream-rename event that the test already announces. Deliberate, documented,
  pinned — left as is.
- **Multipart control-field names in `testing/client.py`.** Same protocol fact as
  `views.py::_MULTIPART_CONTROL_FIELDS`, count 2 on the posited spec change. Disproved on warrant:
  the client's set guards its own envelope construction (its error message and docstring are about
  the client's own spread order), the underlying GraphQL multipart specification is frozen across
  every supported dependency version, any real change would fail loudly on both sides through
  existing live rows (a wrong envelope corrupts requests the server rejects; a missed control field
  fails the loss-detector rows), and consolidation requires either a testing→views import (pulling
  `strawberry.django.views` into the test-client import chain) or a new leaf module for one
  2-tuple. Cost of the duplication is lower than cost of the cure.
- **`resolved_revalidation_window` vs `_resolved_max_request_body_bytes`.** Same validation idiom
  (exact-type admission, `describe_value` tail, loud `ConfigurationError`), different domains. A
  shared parameterized validator couples the body-cap domain to the WebSocket-window domain and
  needs mode flags to reconcile their differing rejection arms. Anti-goal per DRY.md.
- **GET-scope triplication.** Covered in axis 3; three decisions, three rationales.

## Opportunities

None — every apparent duplication was either disproved on ownership grounds (the two JSON-parse
reason constants: deliberate, import-direction-constrained, and pinned equal to each other and to
upstream's live raise by one test, so the posited upstream-rename change costs two announced edits
instead of one unannounced risk), disproved on plausibility-and-cure-cost grounds (the multipart
control-field names: frozen external spec, loud failure on drift, cure worse than disease), or
shown to be already consolidated at its root owner (wire reasons owned once by
`views.py::_BODY_LIMIT_REASON` with symbol-consuming tests; boundary marks and the probed method
name owned once by `_boundary_ordering.py` with bidirectional pins; the 1 MiB default owned once by
`conf.py`; sync/async policy owned once by the mixin with structural parity tests). The required
positive control is posited change 1: rewording the over-limit wire reason forces exactly one
production edit, proving the module's own contracts are single-sited.

No tracked changes were made; pytest remains deferred (not requested).

## Judgment

This file is dense but not duplicated against itself or the system. Its apparent twins resolve into
forced framework shapes (transport color, decorator inspection) whose policies live once on the
mixin, its cross-module facts are centralized in `_boundary_ordering.py` and pinned in both
directions, and its wire contract's few repeated literals are deliberate, documented at both sites,
and enforced by tests that compare them to upstream's actual behavior. The remaining two-site facts
(the patch module's reason constant, the test client's reserved field names) are cheaper kept than
merged: each has a stated import-direction or layering constraint, an implausible change axis, and
a standing test that turns drift into a loud failure. Zero-edit result, proved.
