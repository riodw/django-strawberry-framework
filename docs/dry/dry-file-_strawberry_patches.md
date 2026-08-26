# DRY review: `django_strawberry_framework/_strawberry_patches.py`

Status: verified

## System trace

The module owns defensive monkeypatches for three upstream Strawberry HTTP-view defects,
applied once from `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`
and self-gated by `django_strawberry_framework/conf.py::upstream_patches_enabled("strawberry")`:

1. gap 1 - `_patched_parse_json` widens upstream's `except json.JSONDecodeError` with a
   `UnicodeDecodeError -> HTTPException(400)` translation;
2. gap 2 - the same wrapper rejects non-object JSON bodies and non-object batch elements;
   because that guard would wrongly fire on GET query params, `_patched_parse_query_params`
   reimplements `BaseView.parse_query_params` routing its nested parses through the captured
   original (the reimplementation is pinned to upstream's body by `_validate_upstream_shape`);
3. gap 3 - sync/async `parse_multipart` delegates translate malformed multipart `map`
   traversals to 400, scoped by provenance through `_raised_inside_the_upload_utility`.

Lifecycle plumbing: import-time capture (`_captured_upstream_method`, reload-safe via the
owner/original sentinel attributes), fail-loud validation (`_validate_upstream_shape`),
install-state check (`_patch_is_installed`), and idempotent install (`apply`).

Consumers and connected behavior examined:

- `views.py::_RequestBodyBoundaryMixin.parse_json` delegates through `super().parse_json`,
  so package views ride the envelope guard while keeping the strict UTF-8 wire contract
  ungated in their own boundary (`_RawBodyRequestAdapter` supplies undecoded bytes);
  `views.py::_JSON_PARSE_REASON` deliberately re-states upstream's parse-failure literal.
- Siblings `_django_patches.py` / `_cross_web_patches.py`: same skeleton shape, different
  dependency contracts; `conf.py::UPSTREAM_PATCH_DEPENDENCIES` names all three.
- Tests pinning it: `tests/test_strawberry_patches.py` (unit rows for every member),
  `tests/test_apps.py` (ready() dispatch, reload safety), `tests/test_views.py`
  (wire-reason identity pin, patch-state matrix),
  `examples/fakeshop/test_query/test_transport_api.py` (live opt-out and multipart-map rows).
- Installed upstream read directly at `.venv/.../strawberry/http/base.py`,
  `sync_base_view.py`, `async_base_view.py` to verify the docstring's defect claims still
  hold on the shipped version.

## Verification

All five axes discharged:

1. **Cross-flavor policy mirroring - searched.** The three flavors of "defensive upstream
   patch" are the sibling modules; the gate itself is single-owned in `conf.py`
   (grep: only definition + the three `apply()` callers). Grep for the sentinel names
   (`_PATCH_OWNER_ATTRIBUTE` / `_PATCH_ORIGINAL_ATTRIBUTE`) shows definitions and internal
   uses in exactly the three modules, no cross-module reader anywhere. Single-edit-site test:
   rename `_cross_web_patches`' sentinel -> exactly 1 site, behavior correct (each module
   matches only its own `_PATCH_OWNER` stamp); add a fourth patch module -> additive copies,
   zero edits to existing sites. Count came back **one** twice: no lockstep coupling exists.
   A shared skeleton module was rejected (see rejected candidates).
2. **Sync/async twins - searched.** One genuine pair: `_patched_sync_parse_multipart` /
   `_patched_async_parse_multipart`, bodies differing only by the `await`. Compared by
   behavior: both transports have positive malformed-map rows and server-bug-scoping rows
   (`tests/test_strawberry_patches.py`), so drift is caught on both sides; they share
   `_MULTIPART_TRAVERSAL_ERRORS` and the provenance helper. `parse_json` needs no twin -
   both views inherit the single `BaseView` method. The GET shield has no async variant
   because query params arrive as `str` on both transports.
3. **Derived rather than repeated knowledge - searched.** The reason literals are copies of
   upstream literals (not derivations); grep shows the envelope-guard shapes
   (`isinstance(parsed, dict)`, `all(isinstance(item, dict) ...)`) exist nowhere else, and
   the batch enablement/size policy is deliberately left to upstream's
   `_validate_batch_request`. No fact is reconstructed by a second mechanism inside the
   package; the findings below are about copy fidelity, not derivation.
4. **Inverse/round-trip pairs - ruled inapplicable.** The module only parses inbound request
   bodies toward GraphQL request data; it ships no serializer, encoder, or outbound-shaping
   half (greps for the rejection literals and decode counterparts find no counterpart site),
   so no encode/decode grammar pair can exist on this surface.
5. **Contracts restated in another medium - searched; one hit.**
   - The JSON wire-vocabulary parity contract is held in code plus an executable pin:
     `tests/test_views.py::test_the_wire_reason_is_upstreams_own_parse_json_literal` checks
     BOTH package constants against what upstream actually raises.
   - The multipart wire-vocabulary parity contract ("keep the sync and async transports on
     Strawberry's existing multipart parsing vocabulary",
     `_strawberry_patches.py #"Keep the sync and async transports"`) was held ONLY in prose:
     every assertion comparing `_UPSTREAM_MULTIPART_PARSE_REASON` compares the wrapper's own
     output back to the constant itself (`tests/test_strawberry_patches.py` malformed-map
     rows; the live fakeshop rows assert bytes flowing from the same constant). Fixed below.
   - `docs/GLOSSARY.md` / `docs/TREE.md` restate the dispatch/gate inventory in prose; that
     is standing documentation per repo convention, and `apps.py`'s docstring deliberately
     repeats none of the bug inventory.

Verified against the installed dependency, not just prose: upstream `base.py::parse_json`
still catches only `json.JSONDecodeError`; the native multipart-400 literal is raised at
exactly one site, `async_base_view.py::AsyncBaseHTTPView.parse_multipart #"Unable to parse
the multipart body"`, wrapping a `ValueError` from `get_form_data()` - cleanly triggerable
with an adapter stub, which the new pin uses.

Single-edit-site counts for posited changes:

- "Upstream rewords its multipart 400 reason": forces the package constant (to preserve the
  stated parity) - and today NOTHING signals it. Count > 1 outcomes with zero signal = the
  finding.
- "Upstream rewords its JSON parse reason": forces both package constants, and the existing
  pin fails loudly. Correct-by-design; contrast recorded to show the asymmetry.
- "Retire gap 1 once upstream widens its except": touches only this module (its own stated
  lifecycle). Count **one** - independence confirmed, not duplication.

No scratch experiments were needed; installed-source reads resolved every behavioral
question.

Strongest rejected candidates:

- **Unify the three patch modules' skeleton** (capture/mark/validate/install + sentinel
  constants) into a shared helper module. Disproof: zero cross-readers of the sentinels
  (grep above), so no change to one module ever forces another; descriptor kinds genuinely
  differ per dependency (plain method vs classmethod `__func__` vs property `fget`), so a
  generic capture needs descriptor-kind mode flags; and each module is designed to be
  deletable outright once its gaps retire (`#"This module can now"` /
  `conf.py #"one name per patch module"`). Coupling three independently retirable modules
  for two string constants makes the system less DRY, not more.
- **Merge the sync/async multipart twins** behind one await-generic wrapper. Disproof: the
  await boundary is genuine variation (upstream itself keeps separate
  `SyncBaseHTTPView`/`AsyncBaseHTTPView` methods); unification adds an
  `isawaitable` branch no real path needs and obscures which transport runs what. Both twins
  are behavior-tested independently.
- **Import `_JSON_PARSE_REASON` from one owner instead of two copies.** Disproof: the
  non-import is documented at both sites (`views.py #"reproduces the same literal"`,
  `_strawberry_patches.py #"deliberate rather than imported"`): the permanent view surface
  and the deletable patch module must not reach into each other, and drift already fails
  loudly via the live pin in `tests/test_views.py`.
- **Derive `_patched_parse_query_params` from `_UPSTREAM_PARSE_QUERY_PARAMS_SOURCE` via
  exec** so pin and implementation share one artifact. Disproof: exec-derived code trades a
  readable reimplementation for string-exec machinery; the pin's job is to detect UPSTREAM
  drift (which it does at `apply()` time), and the shield's own semantics are pinned
  behaviorally row-by-row (null/scalar/object/malformed/empty-string), so no silent-drift
  surface remains to justify the indirection.

## Opportunities

1. **The multipart wire-vocabulary parity contract had no executable pin.**

   - **Repeated responsibility:** `_UPSTREAM_MULTIPART_PARSE_REASON` reproduces upstream's
     native multipart-400 literal verbatim so the delegates' translated failures are
     indistinguishable on the wire from Strawberry's own multipart rejections - a stated
     duty whose fidelity to upstream was enforced by no medium (prose comment only; all
     assertions were self-referential).
   - **Sites:** origin `strawberry/http/async_base_view.py::AsyncBaseHTTPView.parse_multipart
     #"Unable to parse the multipart body"` (the only native raise; verified the sync parser
     has none); copy `_strawberry_patches._UPSTREAM_MULTIPART_PARSE_REASON`; self-referential
     assertions in `tests/test_strawberry_patches.py` (sync + async malformed-map rows) and
     downstream live rows in `examples/fakeshop/test_query/test_transport_api.py`.
   - **Evidence:** posited change "upstream rewords its multipart reason" forces the package
     constant and moves silently today, while the structurally identical JSON-reason copy
     fails loudly through `tests/test_views.py::test_the_wire_reason_is_upstreams_own_parse_json_literal`.
     Two identical copies of the same kind of knowledge, one pinned, one not - the unpinned
     half was the defect.
   - **Owner:** `tests/test_strawberry_patches.py`, the module's own suite, next to the
     reason assertions it already owns.
   - **Consolidation:** added `test_the_multipart_reason_is_upstreams_own_native_literal`,
     triggering upstream's native raise through the captured original
     (`patches._original_async_parse_multipart` with a `get_form_data` stub raising
     `ValueError`) and asserting status 400 and reason equality with the package constant.
     No production code changed.
   - **Proof:** the new row fails if either side changes the literal; combined with the
     existing delegate rows it transitively pins delegate output == upstream's native
     vocabulary.
   - **Risks / non-goals:** no wire behavior changes; the two reason constants stay
     unmerged and mutually unimported (independent lifecycles, deliberate); the pin uses
     the async original because the sync parser raises this literal nowhere.

## Judgment

The module's internal design is already consolidation-shaped: one `parse_json` wrapper
serves both transports from a single inherited method, error vocabularies are named once,
and the reimplemented GET shield is fenced by a source pin plus behavioral rows. Real
duplication risk lived between media, not between code sites: a copied upstream literal
whose parity claim existed only as prose. That is now closed with the missing executable
pin, mirroring the JSON reason precedent. The three-module patch skeleton is intentional
parallel structure - provably independent under the single-edit-site test - and stays
separate. Pytest run deferred per repository law; ruff format/check and the trailing-comma
checker pass.

## Implementation (Worker 1)

- Added `test_the_multipart_reason_is_upstreams_own_native_literal` (+ `_UnformableRequest`
  stub) in `tests/test_strawberry_patches.py`, placed after the async malformed-map rows
  whose assertions it completes. Tracked edit: that file only; no orphan imports introduced
  or created elsewhere. `uv run ruff format .`, `uv run ruff check --fix .`, and
  `uv run python scripts/check_trailing_commas.py` all clean. Concurrent work elsewhere in
  the tree untouched; pytest deferred (not authorized).

## Independent verification (Worker 2)

Scope: `git diff 3f2da56 -- tests/test_strawberry_patches.py django_strawberry_framework/`
shows exactly one hunk in scope, +26 lines confined to `tests/test_strawberry_patches.py`;
`_strawberry_patches.py` has zero hunks (production untouched). Two dirty production files
also present vs baseline — `_request_body.py` (`_lacks_seek`) and
`middleware/request_body.py` (first-boundary-entry fix) — belong to other plan items /
concurrent maintainer work, pre-existing relative to the baseline; left untouched.

Pin drift-detection power independently confirmed by execution (scratch probe under
`docs/dry/temp-tests/dry-file-_strawberry_patches/probe_multipart_reason_pin.py`, plain
python, suite run still deferred): running the new test's exact call sequence raised
`HTTPException(400)` whose reason equals the constant today; the exception's traceback
passes only through upstream's own
`.venv/.../strawberry/http/async_base_view.py` frame — no package frame produces the
reason — proving the left operand comes from executing upstream's genuine code through
the captured original, not a constant-to-constant comparison; perturbing only
`_UPSTREAM_MULTIPART_PARSE_REASON` in memory flips the comparison, so both drift
directions fail the row. Source reads corroborate: upstream awaits
`request.get_form_data()` inside its own `except ValueError` before touching anything
else on the request, so the single-seam `_UnformableRequest` reaches the native raise
without short-circuiting, and grep over the installed strawberry tree confirms
`"Unable to parse the multipart body"` is raised at exactly one site (async parser) —
nowhere in the sync parser. Capture mechanics are order-safe either way: pre-install the
capture takes the genuine method from `AsyncBaseHTTPView.__dict__`; post-install it
recovers via the sentinel attributes.

Rejected candidates re-challenged, all stand: sentinel grep shows definitions plus
internal uses in exactly three modules with zero cross-readers, descriptor kinds genuinely
differ (plain function / property `fget`), and `conf.UPSTREAM_PATCH_DEPENDENCIES` is the
one shared name list — skeleton unification would couple three independently retirable
modules for two string constants. The multipart twins differ by the await alone but each
transport owns positive malformed-map and server-bug-scoping rows, and upstream itself
keeps separate sync/async methods. The JSON-reason non-import stays sound: the live pin at
`tests/test_views.py::test_the_wire_reason_is_upstreams_own_parse_json_literal` anchors
BOTH constants to upstream's actual raise, so no third owner is needed. Matrix axes
re-discharged against the real surface (axis-3 spot check: the envelope-guard shapes exist
at exactly one executable site); axis 4's inapplicability holds — the module wraps inbound
parsing only, with no outbound/serializer half.

Single-edit-site counts re-derived: posited "upstream rewords its multipart reason" forces
exactly one production site (the constant) while the fakeshop wire rows assert bytes
flowing from that same stale copy — blind before the fix, loud after it, which is the
finding as stated. Posited "retire gap 1 once upstream widens its except" touches only
this module; views' strict decode is independent. Count one twice, confirmed.

Verdict: verified. Plan checkbox ticked. Pytest remains deferred per repository law.
