# DRY review: `django_strawberry_framework/_cross_web_patches.py`

Status: verified

(fix-implemented proved zero-edit result — independently re-verified below; see Opportunities)

## System trace

The module owns one process-global fact: `cross_web.DjangoHTTPRequestAdapter.body` —
Strawberry's **sync** Django transport adapter — returns raw `self.request.body` bytes
instead of upstream's bare UTF-8 `.decode()` performed inside a property, where a
`UnicodeDecodeError` cannot become a response. Verified against the installed upstream
(`.venv/.../cross_web/request/_django.py`: sync `body` decodes, async `get_body` returns
raw bytes; cross-web 0.7.0 unfixed). Lifecycle pieces, all intra-module:

- capture: `django_strawberry_framework/_cross_web_patches.py::_captured_upstream_body_getter`
  runs at import, recovers the genuine getter across `importlib.reload` via the owner-stamp
  pair (`_PATCH_OWNER_ATTRIBUTE` / `_PATCH_ORIGINAL_ATTRIBUTE`);
- validation: `_validate_upstream_shape` fails loud (adapter symbol present, readable
  property, `(self)` signature) so dependency drift raises instead of silently dropping
  hardening;
- install: `apply` self-gates through
  `django_strawberry_framework/conf.py::upstream_patches_enabled("cross_web")`, then
  short-circuits on `_patch_is_installed` (identity check) and swaps the property.

Consumers and connected behavior traced:

- Dispatch: `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`
  calls the three appliers (`_django_patches`, `_strawberry_patches`, `_cross_web_patches`)
  last; each module's docstring is its own bug inventory by design.
- Companion half: `django_strawberry_framework/_strawberry_patches.py::apply` widens
  `BaseView.parse_json`'s catch and guards the body envelope; the two modules jointly own
  the malformed-body hardening on **Strawberry's own** view (this module routes the sync
  bytes into `parse_json`; that module translates what `json.loads` raises there).
- Package-mount twin: `django_strawberry_framework/views.py::_RawBodyRequestAdapter.body`
  repeats the identical one-line expression `return self.request.body`, ungated and
  permanent, for package views; `views.py::_RequestBodyBoundaryMixin.parse_json` owns the
  strict UTF-8 decode. Documented as deliberately distinct at
  `views.py::_RawBodyRequestAdapter #"Why this is not the cross_web patch again"`.
- Tests pinning it: `tests/test_cross_web_patches.py` (raw-bytes contract, shape-drift,
  opt-outs, capture sentinels), `tests/test_apps.py` (dispatch, refire, reload-recovery),
  `examples/fakeshop/test_query/test_transport_api.py::test_the_cross_web_half_turns_upstreams_own_500_into_a_400`
  (live 500-vs-400 discriminator on the in-test `/upstream-graphql/` mount of Strawberry's
  own view), and `tests/test_views.py` (~2074, un-install/restore scaffolding;
  2101–2104, upstream async-parity pin).

Lockstep surfaces: retiring the module (upstream fix lands) touches apps.py's dispatch,
`conf.py::UPSTREAM_PATCH_DEPENDENCIES`, this module's tests/docs, and the GLOSSARY patch
entry; adding a patch module touches the same registry plus a new module. Inside the file,
nothing else couples outward: `views.py` names `_patched_body` in prose only, never imports it.

## Verification

All five axes discharged on the target's real surface (searches via `grep -rn`; `rg`
unavailable). Target file verified byte-identical to cycle baseline `90eec48` (`git diff`
empty); surrounding dirt is concurrent work, untouched.

1. **Cross-flavor policy mirroring — searched.** `grep -n "request.body\|\.body\.decode()" django_strawberry_framework/**.py`:
   the raw-body rule exists at exactly two package sites, `_cross_web_patches.py::_patched_body`
   and `views.py::_RawBodyRequestAdapter.body`, plus upstream's async `get_body`. Attempted
   disproof succeeded: the sites share syntax but not responsibility — gated, retirable,
   process-wide workaround for someone else's class vs. ungated, permanent body source for
   package mounts. Posited change "upstream ships the minimal fix (sync mirrors async)" →
   the patch module cluster is deleted while `views.py` requires **zero edits**, exactly the
   indifference the live rows assert in both patch states; merging the sites would chain the
   permanent wire contract to a retirable kill switch, the split spec-046 rejected. The
   opt-out/gate policy itself is already single-homed: posited change "flip the default /
   reshape `APPLY_UPSTREAM_PATCHES`" forces **one** site, `conf.py::upstream_patches_enabled`
   (grep confirms the only callers are the three `apply()` gates, each passing its name).
2. **Sync/async twins — ruled inapplicable with evidence.** The target installs exactly one
   replacement, a sync property (`_patched_body`, one statement, no await anywhere in the
   module). Its async counterpart is upstream's own `AsyncDjangoHTTPRequestAdapter.get_body`,
   which already satisfies the desired contract and is pinned at
   `tests/test_views.py #"assert await adapter.get_body() == raw"`. There is no second half
   in package code to drift from. (The genuine sync/async twins — the multipart delegates —
   live in the sibling `_strawberry_patches`, outside this target.)
3. **Derived rather than repeated knowledge — searched.** (a) `_PATCH_OWNER` literals equal
   each module's `__name__` but nothing derives meaning from that equality: the stamp is only
   ever compared by the module that wrote it, so a stale literal stays functional; deriving
   via `__name__` buys nothing behavioral. (b) The stamp-unwrap core
   (`getattr(x, _PATCH_OWNER_ATTRIBUTE, None) == _PATCH_OWNER → return original`) appears
   three times, embedded in descriptor-kind-specific extractors (property `.fget` here,
   plain function in `_strawberry_patches`, classmethod `.__func__` in `_django_patches`).
   Single-edit-site: rename the stamp attribute → 3 sites move only by convention; moving one
   alone breaks nothing cross-module (each capture trusts only its own owner string), and the
   per-module suites would catch any local mistake. A shared constants/helper module for a
   two-line core would add import coupling between three modules whose documented lifecycle
   is independent retirement. Rejected.
4. **Inverse/round-trip pairs — searched.** Capture-at-import / recover-after-reload /
   install / probe form one closed loop inside this module, single implementation, exercised
   twice over by `tests/test_apps.py::test_ready_reinstalls_patches_after_their_modules_reload`.
   The restore-by-identity blocks in four test files are save/restore scaffolding around a
   global mutation — intentional repetition that keeps each test independently legible
   (DRY.md preserves this). The strict-decode half (`views.py`) and the no-decode half (this
   module) compose rather than mirror: one grammar's two owners, not an encode/decode pair
   restated.
5. **Contracts restated in another medium — searched.** The "is it still needed?" criterion
   exists as (a) the docstring probe script, (b) the live discriminating row in
   `test_transport_api.py`, (c) the `_original_body_fget` sanity assertion in
   `tests/test_cross_web_patches.py #"upstream still \"succeeds\" into a str"`. These are
   complementary media by repository convention (a human retirement diagnostic plus CI
   regression pins); an upstream behavior change *should* trip several independent probes.
   Executable truths are single-homed per concern: gate semantics in `conf`, install in
   `apply`, parity facts in tests. The three-module `apply()` skeleton was quantified rather
   than assumed: shared residue is the 4-line gate→validate→short-circuit→install sequence
   plus two stamp constants, while the middle differs structurally — `_django_patches.apply`
   consumes `_validate_upstream_shape`'s returned source and records it *before* the
   short-circuit (ordering `_validate_upstream_shape #"return source"` depends on), the
   others ignore it. A generic `apply_patch(gate, validate, is_installed, install)` needs
   callable indirection plus a flag to express that ordering — exactly the mode-flag helper
   and line-count optimization DRY.md forbids. Rejected.

Single-edit-site counts recorded above; several came back **one** (gate reshape → 1;
upstream-fix retirement → 0 edits on the package-mount half; response-reason wording on the
companion half → confined to `_strawberry_patches`, this file untouched).

Scratch experiments: none needed — every behavioral question was answered by an existing
pinned test cited above, and no tracked edit was made, so no ruff pass was due. Pytest run
deferred per AGENTS.md (no authorization in this cycle; nothing edited).

## Opportunities

None — every apparent duplication was disproved on responsibility, lifecycle, or change
axis, and the search produced multiple count-of-one proofs that the target's real policies
already have single homes:

- Strongest rejected candidate: the three-module patch scaffold (gate/validate/idempotence/
  capture across `_cross_web_patches`, `_strawberry_patches`, `_django_patches`). Evidence
  against: shared residue is two constants and a four-line sequence; validation depths differ
  (delegator arity-pin vs. source-pinned reimplementation vs. property-shape pin);
  `_django_patches` orders validate-record-before-short-circuit and consumes the validated
  body; each module documents an independent retirement lifecycle and trusts only its own
  owner stamp, so the "shared" literals are a naming convention without a cross-module
  failure mode. Consolidation would trade ~8 duplicated lines for a callable/flag-plumbing
  helper and inter-module coupling.
- Second rejected candidate: `_patched_body` vs `views.py::_RawBodyRequestAdapter.body`
  (identical expression, opposite ownership: retirable gated workaround vs. permanent
  ungated policy; proven mutually indifferent by the live rows running both states).
- Third rejected candidate: deriving `_PATCH_OWNER` from `__name__` (no consumer of the
  equality; purely informational).

## Judgment

This file is a thin, single-purpose shim whose every policy — gating, shape validation,
idempotence, reload safety — is either implemented once inside the module or delegated to an
existing single owner (`conf.py::upstream_patches_enabled`, upstream's async contract, the
package view's strict decode). The tempting consolidations all dissolve under the
single-edit-site test: similarity without shared responsibility. Zero-edit result is proved,
not assumed; the module's remaining lifecycle question (retire when upstream fixes the bare
decode) is already instrumented end-to-end.

## Independent verification (Worker 2)

Confirmed the scoped diff is empty: `git diff 90eec48 -- django_strawberry_framework/_cross_web_patches.py`
returns nothing (cycle baseline respected; surrounding dirt is concurrent work, untouched).

Independently re-traced and confirmed against real source:

- Upstream defect shape verified in the installed dependency (`.venv/.../cross_web/request/_django.py`):
  sync `body` is `self.request.body.decode()` inside a property; async `get_body` returns raw
  bytes. The patch replaces exactly that one sync property with the async contract
  (`_patched_body #"return self.request.body"`); dispatch is `apps.py::ready` calling all three
  appliers; no `async def`/`await` exists anywhere in the target.
- Gate reshaping recount: grep over package + tests confirms `upstream_patches_enabled`'s only
  production callers are the three `apply()` gates (`_cross_web_patches.py`, `_strawberry_patches.py`,
  `_django_patches.py`), each passing its canonical name — posited reshape forces **one** site.
- Upstream-fix retirement recount: `views.py::_RawBodyRequestAdapter.body` references nothing from
  this module (subclass shadows the class attribute by identity), and
  `tests/test_views.py #"DjangoHTTPRequestAdapter.body = property(cross_web_patches._original_body_fget)"`
  proves the package adapter yields bytes while upstream's own adapter raises in the un-installed
  state — retirement forces **zero** package-mount edits. Async-parity pin re-read at
  `tests/test_views.py #"assert await adapter.get_body() == raw"`.
- Three-module scaffold re-compared by reading all three modules in full. The shared residue is a
  gate line, a two-line short-circuit, two stamp constants, and the ImportError-fallback shape;
  everything else differs in kind, not just text: validation depth (property-shape pin vs. four
  arity pins plus a source-pinned body vs. descriptor-plus-audited-source-set), install target
  (property vs. plain functions vs. classmethod wrapper), capture extractor (`.fget` vs. plain
  method vs. `__func__` unwrap), and `_django_patches.apply` consuming `_validate_upstream_shape`'s
  returned source into a global BEFORE the short-circuit (a runtime input of
  `_disallowed_connection_methods`). A uniform helper needs either a post-validate hook or a
  side-effecting validate for that one module — callable/flag plumbing for ~3 lines per module,
  plus a fourth file that must outlive and be deleted after all three independently-retirable
  modules. Rejection stands.
- Stamp constants recounted: the owner/original attribute literals appear in exactly three files,
  and no test, example, or other module reads them — each capture trusts only its own owner string,
  so deriving `_PATCH_OWNER` from `__name__` buys nothing and renaming moves sites by convention
  only, with no cross-module failure mode. Rejection stands.

Matrix re-discharged on the real surface: axis 1 re-searched (`request.body` / `.body.decode()`
across the package) — the adapter body-source rule has exactly the two named implementations; the
one extra reader my search surfaced (`middleware/debug_toolbar.py::... #"json.loads(request.body)"`,
an operationName peek) consumes Django's raw request rather than implementing the adapter rule and
forces none of the recorded counts. Axis 2 ruled inapplicable with evidence (single sync property;
async half is upstream's own contract, pinned). Axes 3–5 confirmed as recorded, including the live
retirement discriminator at
`examples/fakeshop/test_query/test_transport_api.py::test_the_cross_web_half_turns_upstreams_own_500_into_a_400`
and the upstream-still-decodes sanity assertion in `tests/test_cross_web_patches.py`.

Verdict: **verified** — zero-edit result proved; pytest deferred per AGENTS.md (nothing edited).
