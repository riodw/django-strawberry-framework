# Review: `django_strawberry_framework/_cross_web_patches.py`

Status: verified

## Understanding

One replacement of one property. `apply()` installs `_patched_body` - `return self.request.body`,
the async adapter's contract - over `cross_web.DjangoHTTPRequestAdapter.body`, whose upstream getter
is a bare `self.request.body.decode()` performed inside a property. Two module globals hold all the
state: `DjangoHTTPRequestAdapter` (import-time, `None` sentinel on `ImportError`) and
`_original_body_fget` (import-time capture of the genuine upstream getter, `None` sentinel when the
symbol or a readable `body` property is absent). Nothing else is mutable, and the installed getter
never calls the captured one - calling it would put the decode back inside the property.

Trigger and lifecycle. The only production caller is
`apps.py::DjangoStrawberryFrameworkConfig.ready`, third of three `apply()` calls, so a consumer gets
it by `INSTALLED_APPS` alone. The gate is `conf.py::upstream_patches_enabled("cross_web")`, read once
per `apply()`, i.e. at app load: `False` globally or `{"cross_web": False}` for this dependency, with
the whole mapping shape validated on every read. `apply()` only ever installs - it has no
un-install arm - so flipping the setting after `ready()` changes nothing, which is a property the
verification below had to establish rather than assume. Order inside `apply()` is gate, shape
validation, installed check, install; validation therefore re-runs on a re-entrant call, which is
cheap and keeps a reshaped upstream loud even when the patch is already in place.

Idempotence and self-healing. `_patch_is_installed()` compares the live descriptor's `fget` against
`_patched_body` by identity, so a repeated `ready()` is a no-op and a third-party revert is
re-installed. `_validate_upstream_shape()` inspects the **captured** getter, not the live descriptor:
a missing capture refuses to install even when the live `body` is a perfectly shaped property, which
is what keeps the shape assertion authoritative rather than self-referential
(`tests/test_cross_web_patches.py::test_apply_fails_loudly_when_original_getter_was_never_captured`).

Blast radius, measured rather than assumed. In the installed dependency set exactly one reader
consumes this property: `strawberry/http/sync_base_view.py::SyncBaseHTTPView.parse_http_body`
#"data = self.parse_json(request.body)". `cross_web/request/__init__.py::HTTPRequest.body` re-exposes
it for a direct `cross_web` consumer, within upstream's own declared `Union[str, bytes]` return type.
Nothing in `strawberry`, `cross_web`, or `debug_toolbar` reads a sync Django adapter's `body`
anywhere else - the GET path goes through `parse_query_params`, and multipart through `post_data`.

Who the patch is still for. Not the package: `views.py::_RawBodyRequestAdapter` is a one-property
subclass of the patched class installed through upstream's `request_adapter_class` seam, so a package
mount reaches `views.py::_RequestBodyBoundaryMixin.parse_json` with undecoded bytes in every state of
this setting. What remains is a consumer who mounts `strawberry.django.views.GraphQLView` directly:
installed, an undecodable body's `UnicodeDecodeError` moves out of the property and into
`parse_json`, where `_strawberry_patches.py::_patched_parse_json` translates it to `400`;
un-installed, it is the unhandled `500` that is the upstream defect. The patch decodes nothing and
widens no success set - it moves the raise into a scope that can answer with a response.

Upstream, re-read rather than trusted. `cross_web/request/_django.py` at the installed 0.7.0 still
has the sync `body` bare-decoding and `AsyncDjangoHTTPRequestAdapter.get_body` returning raw bytes,
so the asymmetry the module documents is live; 0.7.0 is still PyPI's latest release, so the module's
"Upstream status" claim holds unchanged.

Existing description of the behavior: `tests/test_cross_web_patches.py` (the getter's raw-bytes
contract, the gate's two spellings, the three shape-validation refusals, idempotence), the patch-state
rows at the end of `examples/fakeshop/test_query/test_transport_api.py`, the encoding rows in
`examples/fakeshop/test_query/test_products_api.py`, and `docs/TREE.md`.

## Verification

Scratch: `docs/review/temp-tests/_cross_web_patches/test_probe.py`, three rows, all green, driving
fakeshop through `django.test.Client` with a scratch URLconf that mounts Strawberry's own view
alongside `config.urls`.

- The module docstring's documented re-check - `{"cross_web": False}` in settings, then
  `test_products_api.py -k "invalid_utf8 or raw_binary or utf16_json"` - measured:
  `_patch_is_installed()` is still `True` inside the override, and the three bodies answer
  `400 / 400 / 400`. So the procedure neither un-installs the patch nor produces the `500` it
  predicts.
- The same three bodies with the half **genuinely** un-installed (upstream's property restored by
  identity, Strawberry's patch left on): still `400 / 400 / 400` on the package mount. The package
  mount is indifferent by construction, so no row posted there can diagnose this module.
- The same three bodies on Strawberry's own mount: `500 / 500 / 500` with the half un-installed and
  `400 / 400 / 200` with it installed. That mount discriminates; the `200` is the BOM'd UTF-16 body
  upstream auto-detects once the raw bytes reach `json.loads`, so it is not a diagnostic shape
  either.
- The docstring's probe 2, run verbatim: `UnicodeDecodeError` out of `_original_body_fget`, i.e.
  "STILL NEEDED". Installed `cross-web` 0.7.0, and `https://pypi.org/pypi/cross-web/json` reports
  `0.7.0` as latest, so nothing about the upstream status has drifted.

Existing tests read rather than trusted. `tests/test_cross_web_patches.py` pins the getter's return
value and the gate/validation matrix, and its two end-to-end rows follow the bytes into
`DjangoGraphQLView.parse_json` - i.e. into the *package* view, whose `400` is the wire contract's,
not this patch's. `test_transport_api.py::test_only_the_package_mount_answers_the_same_way_in_both_patch_states`
does reach the upstream mount, but with **both** halves off and with a body upstream accepts when
patched, so it pins `500` and `200` and never the `400` this module exists to produce.
`test_transport_api.py::_every_upstream_patch_opted_out` is the only live simulation that touches
this half, and it always moves both halves together.

## Improvements

### High

None.

### Medium

**1. The module's own retirement procedure inverts its verdict: followed literally it deletes a live
production patch.**

- Observation: the "Re-checking whether upstream fixed this" section told a maintainer to set
  `{"cross_web": False}` and run three `test_products_api.py` rows, reading `500`s as "still needed"
  and `400`s as "upstream fixed it, delete this module". Both halves of that instruction are wrong.
- Evidence: measured, not reasoned. (a) The setting alone un-installs nothing - the patch installs
  from `AppConfig.ready()`, long before collection, and `_patch_is_installed()` is `True` throughout
  the recommended run; `test_transport_api.py::_strawberry_patch_opted_out`'s own docstring already
  states this for the sibling half. (b) Those rows post to fakeshop's `/graphql/`, a **package**
  mount, which owns its body source (`views.py::_RawBodyRequestAdapter`) and its strict decode, so
  they answer `400` with the half installed, with the setting overridden, and with the property
  genuinely restored - all three states measured above. The reader therefore always sees `400`, i.e.
  always reads "retirable".
- Impact: the failure mode is a deleted production hardening. The module is the only thing standing
  between a consumer who mounts Strawberry's own sync view and an unhandled `500` on any undecodable
  body, and the document that exists to decide its retirement recommends retiring it today. It is
  also the exact inversion `_strawberry_patches.py` already corrected for its own gap 1 ("reading one
  into the suite inverts the verdict... or mount `strawberry.django.views.GraphQLView` directly"),
  which is what makes this a stale twin rather than a judgement call.
- Recommendation: the diagnostic has to name a mount of Strawberry's own view, and has to say that a
  package mount cannot express the question. Fakeshop already keeps that mount
  (`test_transport_api.py` #"upstream-graphql/"), so the corrected section points at a standing row
  over it, states both mis-readings (the switch is not a simulation; only a body neither the property
  decode nor `json.loads` can decode discriminates), and keeps probe 2 unchanged - it was verified
  working.
- Proof: `examples/fakeshop/test_query/test_transport_api.py::test_the_cross_web_half_turns_upstreams_own_500_into_a_400`,
  which is both the corrected procedure's target and Medium 2's fix.

**2. What this module buys was unpinned at every tier, so its own contract could not fail.**

- Observation: no test anywhere asserted the patch's stated outcome - an undecodable body on
  Strawberry's own view answering a controlled `400` because the bytes reached `parse_json` - nor
  isolated the `{"cross_web": False}` member behaviorally.
- Evidence: the package tier stops at the getter's return value and then follows the bytes into the
  *package* view; the one live row that reaches `/upstream-graphql/` moves both patch halves at once
  and uses a body upstream accepts when patched (`200`). Per-dependency opt-out is pinned only as an
  install-state assertion (`tests/test_cross_web_patches.py::test_apply_no_ops_when_cross_web_dependency_opted_out`).
- Impact: the whole remaining value of a production monkey-patch had no regression detector. A change
  that made `_patched_body` decode again, or that dropped the install from `ready()` for this half
  alone, would leave every existing row green - including the rows whose subject is the wire
  contract, because those are the rows that are indifferent to it by design.
- Recommendation: earn it at the live tier, on the mount that can express it, with one switch member
  moved and the companion half asserted still installed so the delta is attributable to this module.
- Proof: the row named in Medium 1, parametrized over the two bodies that discriminate, with a
  valid-UTF-8 control in the un-installed state so the `500` cannot be a broken mount.

### Low

None.

### Rejected findings

- **`_patched_body` and `views.py::_RawBodyRequestAdapter.body` are the same one-line expression.**
  Not duplication: spec-046 Decision 9 splits them by lifecycle on purpose and they must *not* change
  together - this one retires when upstream stops decoding eagerly, the other is permanent package
  policy that must hold with every patch off. Consolidating would also break `_patch_is_installed`,
  which is an identity comparison against this function, and would couple the package view to the
  kill switch.
- **The patch flips `cross_web.HTTPRequest.body`'s return type process-wide for a non-Strawberry
  `cross_web` consumer.** True and within contract: upstream declares `Union[str, bytes]` and the
  module docstring already records that `strawberry-graphql` is the only distribution depending on
  `cross_web`, so there is no realistic second consumer to warn.
- **Shape validation refuses a compatible reshape.** A positional-only `def body(self, /)` upstream
  would fail `_validate_upstream_shape`'s `POSITIONAL_OR_KEYWORD` check. Deliberate: the module's
  documented stance is that a shape change fails loudly so the patch is re-audited or retired
  deliberately, the message names the opt-out, and the sibling patch modules validate identically.
- **`apply()` never un-installs when the gate is off.** Consistent with both sibling modules and with
  what the package tier documents; a runtime un-install would give a workaround a second lifecycle
  and a second failure mode without buying a consumer anything, since the gate's audience sets it
  before app load.
- **A double import under a second module name would make probe 2 lie.** The second copy would
  capture the already-installed `_patched_body` as "upstream's getter", so the probe would report
  RETIRABLE. Production behavior is unchanged (both getters return raw bytes) and Django's app
  loading reaches the module by one dotted path, so this is contrived rather than latent.
- **Upstream-status drift.** Checked rather than assumed: `cross-web` 0.7.0 is both installed and
  PyPI's latest, and the sync getter still bare-decodes. No edit earned.

## Summary

The code is right and the document about it was wrong in the one way that matters for a module whose
whole job is to be deleted later. `apply()`, the gate, the capture, the shape validation, and the
idempotence all behave exactly as written, and the getter's contract is sound - it moves a raise out
of a property instead of decoding defensively inside one. What the review found is that the module's
retirement diagnostic pointed at rows that became blind to it when spec-046 gave the package view its
own body source, so the recommended check now always reads "retirable", and that the patch's actual
outcome had no test at any tier. One live row on Strawberry's own mount fixes both: it is the
corrected procedure and the missing regression detector.

## Implementation (Worker 1)

Changed files:

- `django_strawberry_framework/_cross_web_patches.py` - the "Re-checking whether upstream fixed this"
  section's item 1 only. It now names the mount that discriminates, states that a package mount cannot
  diagnose this module and why, names the standing row, and calls out the two verdict-inverting
  mis-readings (the switch is not a simulation; a BOM'd multi-byte body is accepted and a BOM-less or
  UTF-8-BOM body is refused in both states, so neither is a diagnostic shape). Item 2 (the captured-
  getter probe) is unchanged - it was run verbatim and works. **No executable line of the module
  changed**, which is the honest root cause: the defect was in the maintainer-facing retirement
  contract, not in the getter.
- `examples/fakeshop/test_query/test_transport_api.py` - the new `_cross_web_patch_opted_out()`
  helper, the `_UNDECODABLE_BODIES` parameter set, the new row, and one sentence in the module
  docstring's description of the final section. Named here as the deliberate cross-file expansion:
  the target's fix is a diagnostic, and a diagnostic that is not executed is the same class of defect
  as the one being fixed, so the row has to live where the `/upstream-graphql/` mount and the
  patch-state helpers already are.

Permanent tests:

- `examples/fakeshop/test_query/test_transport_api.py::test_the_cross_web_half_turns_upstreams_own_500_into_a_400`,
  parametrized over an invalid-UTF-8-in-JSON body and a raw-binary body. Pins `500` with this half
  un-installed against `400` with it installed, on Strawberry's own mount, plus a valid-UTF-8 `200`
  control in the un-installed state. The helper restores upstream's property by identity and asserts
  `cross_web_patches._patch_is_installed() is False` **and**
  `strawberry_patches._patch_is_installed() is True` inside the block, so the delta cannot be credited
  to the Strawberry half or to a patch that quietly stayed installed. Live tier, which `AGENTS.md`
  requires for anything a real request can earn - and this one can, because the behavior is a status
  code on a mounted view.

Verification:

- Scratch: `docs/review/temp-tests/_cross_web_patches/test_probe.py`, 3 passed. See Verification above
  for what each row proved. Untracked and disposable.
- Failability of the new row is intrinsic rather than argued: it measures both patch states in one
  body, and the scratch rows show the un-installed state answering `500` on that mount, so a change
  that put the decode back inside the getter moves the installed arm to `500` and the row fails on
  `patched.status_code == 400`. The bodies were chosen by measurement, not by inspection - the
  raw-binary body is refused because `json.detect_encoding` guesses `utf-16-be` for its leading
  `00 01` and that decode raises, which is why the BOM'd UTF-16 body (accepted, `200`) is deliberately
  excluded.
- Focused runs, all `--no-cov -n0`:
  `examples/fakeshop/test_query/test_transport_api.py -k "cross_web_half or patch_states or kill_switch or opted_out or every_upstream_patch"`
  - 12 passed (the 2 new rows plus the 10 neighbouring patch-state rows);
  `tests/test_cross_web_patches.py tests/test_apps.py` - 20 passed. No full suite run.
- `uv run ruff format .` - 418 files unchanged. `uv run ruff check --fix .` - clean.
  `scripts/check_trailing_commas.py --check` - clean on both changed files.

Rejected findings: evidence under `### Rejected findings` above, each naming the caller, upstream
source, sibling decision, or scratch measurement that contradicts it.

Changelog: no entry earned and none written. Nothing a consumer can observe moved - the production
change is a docstring, and the behavioral change is a test that pins existing behavior.

## Independent verification (Worker 2)

Re-traced from source rather than from the artifact: `apply()`'s four-step order, the import-time
capture, `_validate_upstream_shape`'s use of the **captured** getter, `_patch_is_installed`'s identity
compare, `apps.py::DjangoStrawberryFrameworkConfig.ready` (this is the third of three `apply()` calls,
so a consumer gets it from `INSTALLED_APPS` alone), and `conf.py::upstream_patches_enabled`'s
validate-the-whole-mapping-on-every-read behavior. `apply()` has no un-install arm, confirmed by
reading and then measured live. Upstream re-read at the installed version: `cross_web/request/_django.py`
still bare-decodes in the sync `body` property and still declares `Union[str, bytes]`, while
`AsyncDjangoHTTPRequestAdapter.get_body` returns raw bytes; `cross-web` 0.7.0 is both installed and
PyPI's latest (`https://pypi.org/pypi/cross-web/json`). Blast radius re-measured by grep over the
installed tree: exactly two readers, `strawberry/http/sync_base_view.py` #"data = self.parse_json(request.body)"
and `cross_web/request/__init__.py::HTTPRequest.body`, and `strawberry-graphql` is the only
distribution that requires `cross-web`.

Scratch (mine, independent of Worker 1's): `docs/review/temp-tests/_cross_web_patches/test_w2_verify.py`,
which mounts Strawberry's own sync view next to fakeshop's package mount and measures **eight** body
shapes x two mounts x two patch states, asserted as a fixed matrix so a drift fails rather than
prints. Measured (up = `/w2-upstream/`, pkg = `/graphql/`; OFF = this half restored to upstream by
identity with the Strawberry half asserted installed):

- invalid-UTF-8-in-JSON and raw-binary: up 500 -> 400, pkg 400 in both states.
- BOM'd UTF-16 and UTF-32: up 500 -> **200**, pkg 400 in both states.
- BOM-less UTF-16-LE / UTF-32-LE and UTF-8-BOM: up 400 -> **200**, pkg 400 in both states.
- valid UTF-8: 200 everywhere.

That reproduces and confirms the accepted findings' factual core: the package mount is blind to this
half in every state (so the retired procedure's `test_products_api.py` selector could only ever read
"retirable"), and Strawberry's own mount is the only surface where the half is observable. The
documented command runs and selects the new row: `test_transport_api.py -k cross_web_half` - 2 passed.
Probe 2 verbatim raises `UnicodeDecodeError` out of `_original_body_fget` ("STILL NEEDED"). A separate
scratch row confirms the switch is not a simulation: inside `{"cross_web": False}`,
`_patch_is_installed()` is still `True` and a stray `apply()` inside the override leaves it installed.
Neighbouring suites re-run green: the 12-row `-k "cross_web_half or patch_states or kill_switch or
opted_out or every_upstream_patch"` selection, and `tests/test_cross_web_patches.py tests/test_apps.py`
(20 passed). `ruff format --check` and `ruff check` clean on both changed files. The scoped diff
against `9d8bb305` touches only the docstring's retirement item 1 and the new test material - no
concurrent work absorbed, no executable package line changed.

Every rejected finding independently confirmed, not taken on trust: the non-duplication is real and
load-bearing (`views.py::_RawBodyRequestAdapter` is permanent package policy reached through
upstream's `request_adapter_class` seam and must hold with every patch off, which the pkg columns
above measure; consolidating would also break the identity compare in `_patch_is_installed`); the
process-wide return-type flip is inside upstream's own declared `Union[str, bytes]` and has no second
dependent distribution; the positional-only reshape refusal is real and matches both sibling modules;
the missing un-install arm is real and consistent; the double-import probe hazard is contrived.
Upstream-status drift: none.

The new row is at the strongest reachable tier (live HTTP on a mounted view) and cannot pass for the
wrong reason: its second block asserts this half installed, so dropping the install from `ready()`
for this half alone fails it, and the un-installed arm's 500 is measured above, so a getter that
decoded again would move the installed arm to 500 and fail `patched.status_code == 400`.

### Blocking: two mechanism claims contradicted by measurement

The code is correct and untouched; the cycle's *only* production change is a maintainer-facing
decision procedure, and it repeats the defect class it set out to fix - a stated mechanism that
measurement contradicts, guarding exactly the shape that inverts the verdict.

**W2-1. The corrected retirement section's "non-diagnostic shapes" sentence is false on the mount the
section is scoped to, and the shape it dismisses is a verdict-inverter under the section's own rule.**
The section says a BOM-less UTF-16 / UTF-32 body or a UTF-8-BOM body "answers `400` in both states
through `json.loads`'s own refusal of the decoded `str`" and that "neither shape says anything about
upstream". On `/upstream-graphql/` those three shapes measure **400 un-installed / 200 installed** (up
column above): in the installed state `json.loads` receives *bytes*, auto-detects `utf-16-le` /
`utf-32-le` / `utf-8-sig`, and *accepts* the document. "400 in both states" is true only on the
**package** mount, which the same paragraph has just declared unable to diagnose this module. The
consequence is the inversion Medium 1 exists to prevent: the section's rule is "a `400` in the
un-installed state is what says upstream stopped decoding eagerly and this module can be deleted", and
a maintainer who reaches for a BOM-less UTF-16 body sees exactly that `400` while upstream is still
decoding eagerly - it simply decoded *successfully*. The lead-in criterion is imprecise for the same
reason: `json.loads` *can* decode both dismissed shapes and the raw-binary body; what actually
discriminates is a body upstream's property decode rejects **and** the raw-bytes JSON path will not
accept. Reproduce: `docs/review/temp-tests/_cross_web_patches/test_w2_verify.py::test_w2_matrix`.

**W2-2. The new row's stated mechanism is wrong for one of its two parameters, and so is the
Verification note that justified choosing it.** The row docstring says the installed arm's `400`
is "the same `UnicodeDecodeError` one frame later - inside `parse_json`, where
`_strawberry_patches.py::_patched_parse_json` translates it", the `_UNDECODABLE_BODIES` comment says
neither the property decode nor `json.loads` "can decode" these bodies, and Verification above says
the raw-binary body is refused because the detected `utf-16-be` "decode raises". For
`bytes(range(256)) * 4` all three are false: `json.loads` decodes bytes as
`s.decode(detect_encoding(s), 'surrogatepass')`, so the illegal-surrogate sequence is passed through
and the refusal is a `JSONDecodeError` - upstream's *own* `except`, not the Strawberry half's
translation. Measured directly: with the `cross_web` half installed and the Strawberry half restored
to upstream, raw-binary still answers `400` while invalid-UTF-8-in-JSON answers `500`
(`test_w2_verify.py::test_w2_attribution_the_other_half_alone`), and
`json.loads(bytes(range(256)) * 4)` raises `JSONDecodeError`, not `UnicodeDecodeError`. The row's own
verdict logic still holds for both parameters and the 500 -> 400 delta is still attributable to this
half, so this is a comment/evidence defect rather than a broken test - but only one parameter
exercises the described path, and the artifact claims the selection was made by measurement.

What would clear both: state the un-installed/installed pair each dismissed shape actually produces on
`/upstream-graphql/` (400/200) and say plainly that a `400` there is a *false* retirable, so the
discriminating criterion reads "undecodable as UTF-8 **and** unacceptable to the raw-bytes JSON path";
and describe the raw-binary parameter's installed `400` as upstream's own `JSONDecodeError` under
`surrogatepass`, distinct from the invalid-UTF-8 parameter that does exercise the translation. No
source behavior, permanent-test assertion, or tier needs to change.

## Iterations

### Revision 1 (Worker 1): W2-1 and W2-2 both accepted and fixed

Both claims reproduced independently before editing, in
`docs/review/temp-tests/_cross_web_patches/test_revision_probe.py` (2 passed) plus a direct `json`
layer check, rather than taken from the report:

- W2-1 reproduced: BOM-less UTF-16-LE, BOM-less UTF-32-LE, and UTF-8-BOM bodies on
  `/upstream-graphql/` measure `[400, 400, 400]` with this half un-installed and `[200, 200, 200]`
  with it installed (`test_w2_1_dismissed_shapes_are_false_retirables_on_the_upstream_mount`). My
  original scratch never posted those shapes to that mount - only the BOM'd UTF-16 body - so the
  "400 in both states" sentence was an inference from the package-mount measurement, projected onto
  the mount the section is scoped to. Exactly the defect class the cycle set out to fix.
- W2-2 reproduced: `json.detect_encoding(bytes(range(256)) * 4)` is `utf-16-be` and the decode
  SUCCEEDS (`json.loads` decodes `bytes` with `errors="surrogatepass"`); `json.loads` on those bytes
  raises `JSONDecodeError`, not `UnicodeDecodeError`. Attribution measured with the halves swapped
  (`test_w2_2_raw_binary_400_is_upstreams_own_not_the_translation`): with the `cross_web` half
  installed and the Strawberry half restored to upstream, raw-binary still answers `400` (upstream's
  own `except`) while invalid-UTF-8-in-JSON answers `500` (the translation genuinely missing). So the
  row's raw-binary parameter never exercises the Strawberry translation, and the Verification note
  above ("that decode raises") is wrong - superseded here, left in place per the no-erasure rule. The
  invalid-UTF-8 parameter does exercise it: `utf-8` is detected and `surrogatepass` cannot represent
  `0xFF`, so that decode raises and `_patched_parse_json` translates.

The row's verdict logic, assertions, parameters, and tier all survive both findings - the 500 -> 400
delta is attributable to this half on both routes, and covering both routes is now stated as the
reason for the pair - so the fix is to the stated mechanisms, not to any behavior:

- `django_strawberry_framework/_cross_web_patches.py` (docstring only, again): the retirement
  section's discriminating criterion now reads "a body upstream's property decode rejects AND the
  raw-bytes JSON path does not accept - i.e. only a body whose un-installed answer is the 500"; the
  dismissed shapes now carry their measured 400-un-installed / 200-installed pair and are named as a
  false "retirable"; the `surrogatepass` behavior and the two installed-400 mechanisms are stated.
  The "Who this patch is for" installed bullet made the same overclaim (every undecodable body's 400
  credited to the Strawberry translation) and was tightened in the same pass.
- `examples/fakeshop/test_query/test_transport_api.py`: the `_UNDECODABLE_BODIES` comment now states
  the real selection criterion and the per-parameter mechanism (translation vs upstream's own
  `JSONDecodeError`), and the row docstring's installed-arm bullet describes both routes and cites
  the swapped-halves measurement. No assertion changed.

Validation re-run after the edits: the 12-row focused selection
(`test_transport_api.py -k "cross_web_half or patch_states or kill_switch or opted_out or
every_upstream_patch"`) and `tests/test_cross_web_patches.py tests/test_apps.py` (20) all pass,
`--no-cov -n0`; `uv run ruff format .` and `uv run ruff check --fix .` clean;
`scripts/check_trailing_commas.py --check` clean on both changed files. Scoped diff vs `9d8bb305`
still touches only the module docstring and the live-test material.

## Independent verification (Worker 2, pass 2)

Final verdict: complete and verified. I re-traced the import-time capture, the four-step
`apply()` order (gate, captured-shape validation, installed check, install), the identity-based
self-healing check, and the third `ready()` dispatch from `INSTALLED_APPS`. `apply()` has no
un-install arm: a setting override alone leaves the property installed, and a re-entrant
`apply()` inside `{"cross_web": False}` remains installed. The gate still validates the whole
mapping on every read. The package view's `_RawBodyRequestAdapter` shadows this class and its
strict decoder, so the package mount is intentionally indifferent to this half; Strawberry's own
sync mount is the only live surface that can observe it.

I ran the retirement procedure verbatim:
`uv run pytest --no-cov -n0 examples/fakeshop/test_query/test_transport_api.py -k cross_web_half`
(2 passed). The independent scratch matrix
`docs/review/temp-tests/_cross_web_patches/test_w2b_verify.py` (2 passed) measured the complete
documented set on `/upstream-graphql/`, with this half genuinely restored to upstream for OFF and
the Strawberry half asserted installed: invalid-UTF-8-in-JSON and raw binary are `500 -> 400`;
BOM'd UTF-16/UTF-32 are `500 -> 200`; BOM-less UTF-16/UTF-32 and UTF-8-BOM are `400 -> 200`
(false-retirable traps); valid UTF-8 is `200 -> 200`. Thus the corrected criterion (“property
decode rejects AND raw-byte JSON rejects”) and every dismissed-shape warning match measurement.
`json.loads(bytes(range(256)) * 4)` independently raises `JSONDecodeError`, so the raw-binary
installed `400` is upstream's own rejection under `surrogatepass`, while invalid UTF-8 takes the
Strawberry translation route. The corrected module docstring, the live row's body comment and
docstring, and the artifact's revision evidence now agree with those mechanisms.

The accepted findings are closed: the procedure names the discriminating upstream mount and
warns that a setting switch is not a simulation; the live row isolates this member and pins its
`500 -> 400` outcome at the live HTTP tier with a valid-UTF-8 `200` control. The row cannot pass
for the wrong reason because its helper asserts this half OFF/ON and the Strawberry half ON.
The package-level 20-test target/AppConfig run and the 14-row focused live selection both passed
with `--no-cov -n0`.

I independently confirmed every rejected finding. The two raw-body one-liners are not
duplication: `_RawBodyRequestAdapter` is permanent package policy and the package columns above
stay `400` in every patch state, while this class is a gated process-wide upstream workaround.
The return-type flip remains within cross-web's declared `Union[str, bytes]`; installed metadata
shows only `strawberry-graphql` declares `Requires-Dist: cross-web`. Positional-only getter
reshaping raises the documented loud `RuntimeError` (direct probe), as intended. The missing
un-install arm is real and measured, and the app loads this module through one canonical dotted
path, making the second-module-name probe hazard contrived rather than a production path.
Upstream status has not drifted: installed and PyPI both report cross-web `0.7.0`, and its sync
getter still calls `.decode()` while the async getter returns raw bytes.

The scoped baseline audit lists only `_cross_web_patches.py`, the deliberate
`test_transport_api.py` expansion, and this artifact; AST comparison after removing the module
docstring is equal, so no executable production line changed and no concurrent work was absorbed.
No permanent test or source file was edited during this pass. Item 2 is ready to be checked.
