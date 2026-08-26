# DRY review: `django_strawberry_framework/_django_patches.py`

Status: verified

## System trace

The module owns the **unwrap-time half** of the package's defense against Django Trac #37064
(`AttributeError: 'function' object has no attribute 'wrapped'` in
`SimpleTestCase._remove_databases_failures` teardown). Its rules and lifecycle:

- **Gate** — `apply` #"if not upstream_patches_enabled" reads
  `django_strawberry_framework/conf.py::upstream_patches_enabled("django")`; the setting's name,
  shapes (bool / per-dependency mapping), and validation are owned entirely by `conf.py`.
- **Capture** — `_original_remove_databases_failures` is taken once at import via
  `_captured_upstream_descriptor`, recovering the true upstream descriptor from a previously
  installed replacement after `importlib.reload` (stamp attributes
  `_PATCH_OWNER_ATTRIBUTE` / `_PATCH_ORIGINAL_ATTRIBUTE` written onto
  `_patched_remove_databases_failures` at module level).
- **Validate** — `_validate_upstream_shape` pins the private symbol (`_DatabaseFailure`), the
  classmethod descriptor, the `(cls)` arity, and the captured body's membership in
  `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES` (two audited upstream bodies: class-attribute
  shape ≤6.0.x, connection-feature-flag shape 6.1). Drift raises a targeted `RuntimeError`
  naming the `{"django": False}` escape hatch.
- **Discriminate** — `_disallowed_connection_methods` maps the validated source string to the
  matching `(name, operation)` read path; the raise-on-unvalidated branch keeps a future shape
  loud instead of guessed.
- **Install** — `_patch_is_installed` plus `apply` give idempotent, self-healing installation;
  a foreign revert of the class attribute is healed over (validation uses the import-time
  capture, never the live slot).

Consumers: `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` dispatches
it first among the three appliers; `django_strawberry_framework/testing/_wrap.py::safe_wrap_connection_method`
imports `_is_database_failure` (the wrap-time half shares this predicate);
`tests/test_django_patches.py` (behavior), `tests/test_apps.py` (ready() dispatch + double-reload
recovery), `tests/base/test_conf.py` (gate shapes); `examples/fakeshop/apps/kanban/constants.py`
lists the path in a generated tracked-file allowlist. Siblings `_strawberry_patches` /
`_cross_web_patches` mirror the lifecycle skeleton but deliberately differ in validation depth:
they delegate where upstream changes may flow through and pin bodies only where they reimplement;
this module always reimplements (the isinstance guard must sit *inside* upstream's loop, so
delegation cannot carry the fix) and therefore pins bodies.

Lockstep edits: a third audited upstream body forces the audited-source constant, a
`_disallowed_connection_methods` branch, a patched-loop compatibility audit, and tests — the
documented "widening is an audit" workflow. Nothing else in the package names Django's private
symbols (verified by search), so no other lockstep partner exists.

## Verification

All five axes discharged; searches were `grep -rn` over production, example, and test trees.

1. **Cross-flavor policy mirroring** — searched: read all three patch modules end to end and
   grepped `APPLY_UPSTREAM_PATCHES` package-wide. The gate→capture→validate→install skeleton
   exists once per dependency flavor. Rejected consolidation: a shared skeleton helper needs mode
   flags to reconcile genuinely different validation depths (delegate-shape vs reimplemented-body)
   and install shapes (classmethod re-wrap vs plain assign vs property), coupling three modules
   whose retirement ("this module can be deleted") and docstring-canonical independence
   (`apps.py` `ready` docstring: each module's docstring is the single source of truth) are
   explicit design goals. `views.py` mentions the setting in prose only — no fourth flavor.
2. **Sync and async twins** — ruled inapplicable: `grep -n "async def\|await "` on the target
   returns nothing; it hardens a sync-only Django test lifecycle hook. The repo's real sync/async
   twin pair (`_patched_sync_parse_multipart` / `_patched_async_parse_multipart`) lives in
   `_strawberry_patches`, not here.
3. **Derived rather than repeated knowledge** — searched: stamp-attribute names, `_PATCH_OWNER`,
   the opt-out hint formula, and the audited sources. Findings below.
4. **Inverse and round-trip pairs** — searched: wrap-time (`testing/_wrap.py`) vs unwrap-time
   (target) already share ONE predicate, `_is_database_failure`, owned at the single
   `_DatabaseFailure` import site — the pair's grammar has exactly one definition. The
   stamp/recover encode-decode pair is symmetric inside this one module. Django's own
   add/remove pair is upstream-owned; the patch preserves its symmetry (declines to unwrap what
   the pair never wrapped).
5. **Contracts restated in another medium** — searched: `37064` package-wide. The full framing is
   canonical in this module's docstring; `testing/__init__.py` and `testing/_wrap.py` link out to
   it rather than restate it; GLOSSARY/KANBAN/CHANGELOG/spec-024 occurrences are glossary and
   archived-spec media governed by repo law, not competing statements. The audited-body string
   constants duplicate Django source **deliberately** — they are the drift detector; the test
   suite proves their fidelity by re-deriving equivalent bodies from freshly written nested
   classes and comparing against the imported constants
   (`tests/test_django_patches.py::test_validation_accepts_every_audited_upstream_body_and_refuses_a_third`),
   so the pin itself is guarded, not merely repeated.

Scratch experiment (`docs/dry/temp-tests/_django_patches/prove_stamp_protocol_is_per_module.py`,
run via `uv run python`, both parts passed):

- **P1** — installed a sibling-stamped function (shared attribute NAME, strawberry's owner VALUE)
  into `SimpleTestCase`'s slot: `_captured_upstream_descriptor` returns it as-is (never
  mis-recovered as our prior replacement), and `apply()` ignores the live foreign stamp entirely,
  validates its import-time capture, and self-heals over it. Cross-module safety comes from the
  per-module owner VALUE comparison, not the shared name.
- **P2** — renamed `_django_patches`' two stamp constants in that module only: capture, recovery,
  `apply()`, and install all stay self-consistent. No second site must move.

Single-edit-site counts (posited changes):

- "Rename the stamp attribute in `_django_patches` alone" → **1 site** (P2 proved).
- "A foreign or sibling replacement occupies the captured slot" → **0 code sites**; behavior
  proven correct by P1 (healed, not mis-validated).
- "Django ships a third `_remove_databases_failures` body" → multiple sites (constant +
  discriminator branch + loop audit + tests), but that spread IS the feature: the fail-loud audit
  workflow documented in the module. Consolidation cannot reduce it without silencing the pin.
- "Add a fourth patch module" → copies the ~10-line pattern; accepted cost. The addition is a
  deliberate audited event gated by `conf.UPSTREAM_PATCH_DEPENDENCIES`.

Strongest rejected candidates:

1. **Shared patch-protocol module** (owner/original constants + generic recover/stamp helper for
   the three patch modules). Disproof: the attribute names have zero readers outside their own
   module (grep; P1 shows the shared name carries no contract — owner VALUES discriminate); the
   three capture helpers differ in genuine ways (descriptor+`__func__` unwrap vs dict-get vs
   property-fget guards) that would force mode flags; P2 shows a rename costs one site. The
   similarity is convention, and the house style is deliberate per-module independence
   (cf. `_strawberry_patches._UPSTREAM_JSON_PARSE_REASON` comment establishing intentional
   cross-module literal repetition for import/deletion independence).
2. **Opt-out hint builder** for the nine `RuntimeError` messages restating
   `Disable this patch with APPLY_UPSTREAM_PATCHES = {"<dep>": False}` (three per module; one
   wraps the sentence differently). Disproof: the fragment renders a stable public setting whose
   rename is inherently repo-wide (every consumer dict, test, and doc moves with it, all found by
   the same literal grep), each message is bespoke to its failure, only
   `tests/test_django_patches.py` pins the rendered form, and interposing a builder obscures
   fail-loud diagnostics for a drift risk (stale advice) that a greppable literal cannot silently
   take.

## Opportunities

None — every apparent duplication was disproved on the target's real surface: the shared
lifecycle skeleton and stamp names across the three patch modules are per-module convention with
single-site change counts (experiments P1/P2); the wrap/unwrap defense pair already owns one
predicate at one site; the audited-body strings and the multi-site widening workflow are the
drift alarm working as designed; prose restatements resolve to one canonical docstring plus
link-out or archive media. The posited per-module rename returned a count of one, and the posited
foreign-stamp intrusion returned zero forced sites, satisfying the proof bar for a zero-edit
result.

## Judgment

The module is the system's root owner for exactly one narrow invariant — unwrapping Django's
disallowed-database wrappers must tolerate a replaced wrapper — and every neighboring site that
could plausibly share that knowledge either imports it (`testing._wrap`), mirrors it deliberately
as an independent fail-loud patch module, or is an archive medium. The heavy-looking repetition
(skeleton, stamps, hint strings) is load-bearing independence, verified by experiment rather than
assumed. No consolidation warranted; pytest run deferred per repository law.

## Independent verification (Worker 2)

Scoped diff vs cycle baseline ef3d0d8 is empty; no concurrent edits touch the target.

Independently re-traced: the target's full lifecycle (gate `conf.py::upstream_patches_enabled`
owns every shape — re-read its validation; gate precedes validation in `apply`, which is what
`test_django_dependency_opt_out_silences_drifted_pin_abort` pins), validation reading only the
import-time capture (never the live slot), `apps.py:41` dispatching it first, `testing/_wrap.py`
importing the single `_is_database_failure` predicate, and all pins in `tests/test_django_patches.py`
including the audited-set fidelity test that re-derives both bodies from freshly written nested
classes.

Re-ran Worker 1's scratch (P1/P2 pass) plus wrote my own probes
(`docs/dry/temp-tests/_django_patches/w2_probes.py`, all pass):

- **W2-A** — a sibling-stamped replacement (strawberry's owner VALUE under django's attribute
  NAME) occupying the slot is returned as-is by capture, never mis-validated (validation reads the
  import-time capture), and healed over by `apply()`. Confirms the shared stamp NAME carries no
  cross-module contract; owner VALUES discriminate.
- **W2-B** — drove `_patched_remove_databases_failures` against a synthetic three-alias manager
  under BOTH audited shapes (class-attribute and connection-feature discriminator branches):
  visited wrappers unwrapped, excluded alias untouched, replaced slots left alone; exec'ing each
  pinned upstream body over the same state crashes with `AttributeError ... 'wrapped'`. The patch
  is equivalent to upstream everywhere except exactly the claimed invariant (tolerance of replaced
  wrappers). Also independently exercises both `_disallowed_connection_methods` read paths.

Recounts against my own greps: stamp-attribute names have zero readers outside the three patch
modules (21 matches, all internal) → per-module rename = 1 site, holds. The opt-out hint appears
in exactly 9 raises (django 3 / strawberry 3 / cross_web 3, one wrapped across two string
literals at `_cross_web_patches.py` #"Disable this patch with "); conf.py itself interpolates
`APPLY_UPSTREAM_PATCHES_KEY` into bespoke messages rather than owning message text, so the
rejected hint-builder matches repo precedent. The three-module consolidation remains rejected on
my own comparison of capture shapes (descriptor+`__func__` vs generic dict-get vs property-fget),
validation return contracts (only django's returns the validated source for its discriminator),
install shapes (classmethod wrap vs plain assigns vs property), and installed-checks — a shared
skeleton needs mode flags at four axes while module independence ("this module can be deleted",
docstring-canonical) is stated design. Matrix discharge re-checked against the real surface:
axis 1 via reading all three modules plus an `APPLY_UPSTREAM_PATCHES` sweep (views.py hits are
prose-only); axis 2 ruled out on the file itself (no async surface; the repo's twin pair lives in
`_strawberry_patches`); axes 3-5 searches reproduced (ticket media resolve to canonical docstring,
link-outs, glossary/archive/test media). Verdict: proved zero-edit stands.
