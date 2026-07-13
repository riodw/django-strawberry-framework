# Review: `django_strawberry_framework/conf.py`

Status: fix-implemented

## Understanding

The module owns the package's entire settings surface: the `Settings` attribute-proxy singleton
over the host project's `DJANGO_STRAWBERRY_FRAMEWORK` dict, the shape contract for every cache
write (`_normalize_user_settings`: `None` -> `{}` per the documented package-wide `None` stance,
non-`Mapping` -> `ConfigurationError`, `dict` identity fast-path, other `Mapping` copied), the
missing-key `AttributeError` contract (AGENTS.md law; `__getattr__` converts only `KeyError`,
with a dunder/internal-name short-circuit against recursive or misleading introspection traces),
the test-time refresh (`setting_changed` receiver connected at import time with a `dispatch_uid`;
`reload_settings` mutates the singleton in place so `from .conf import settings` bindings stay
fresh — import-time wiring is deliberate because consumers import `conf` before app loading), and
three named readers with defaults.

Complete key inventory and consumers (traced package-wide; this is all five):

- `APPLY_UPSTREAM_PATCHES` -> `upstream_patches_enabled()` (conf.py:182-196, default `True`,
  truthiness-coerced) — gates all three patch `apply()`s, gate-first before shape validation
  (_django_patches.py:285-287, _strawberry_patches.py:444-446, _cross_web_patches.py:197-199).
- `NESTED_CONNECTION_STRATEGY` -> `nested_connection_strategy_setting()` (default `"windowed"`) —
  consumed by `optimizer/nested_fetch.py::resolve_strategy` (nested_fetch.py:280-283), which owns
  domain validation (unknown-name `ConfigurationError`) next to the strategy registry.
- `TESTING_ENDPOINT` -> `testing_endpoint_setting()` (default `"/graphql/"`) — consumed by
  `testing/client.py:108` as the low rung of the spec-043 endpoint precedence ladder.
- `HIDE_FLAT_FILTERS` — raw `getattr(settings, "HIDE_FLAT_FILTERS", False)` at
  filters/inputs.py:675 (no conf.py constant or reader).
- `RELAY_GLOBALID_STRATEGY` — raw `getattr(conf_settings, "RELAY_GLOBALID_STRATEGY", None)` at
  types/relay.py:381, validated at the consumer per its documented "conf.py is a thin reader that
  does not validate domain values" stance.

Fail-loud propagation is the module's signature behavior: a malformed (non-mapping) dict raises
`ConfigurationError` from the lazy `user_settings` read, and `__getattr__` deliberately lets it
propagate through `hasattr` / `getattr(default=...)` probes, so even the defaulted readers fail
loud on bad configuration and only a genuinely missing key falls back (verified, exp2).

Tests: `tests/base/test_conf.py` (20 tests, read in full) pins the proxy mechanics — invalid
attribute, lazy load, mapping normalization, non-mapping rejection at both read and `reload()`
sites, signal refresh incl. the bound-reference contract, dunder short-circuit, dispatch-uid
idempotence, two recursion regressions — plus the three bool states of
`upstream_patches_enabled()`. The other two readers have no direct tests (covered through their
consumers under the 100% gate).

Inherited finding ingested: `rev-apps.md` Medium 2 (verified there by Worker 3, explicitly
forwarded here) — the all-or-nothing `APPLY_UPSTREAM_PATCHES` couples the test-only Django
patch's imminent drift abort to the production request hardening. Disposition: owned and refined
as Medium 1 below.

## Verification

Scoped diff vs the cycle baseline is empty
(`git --no-pager diff 1c233430 -- django_strawberry_framework/conf.py tests/base/test_conf.py`
— no output; the full-tree diff vs the baseline stash is also empty, so the target carries no
prior or concurrent edits).

Scratch experiments under `docs/review/temp-tests/conf/test_scratch.py` (7 passed,
`uv run pytest docs/review/temp-tests/conf/ --no-cov -n0 -q`):

- **exp1 — missing-key vs explicit-`None`.** `Settings({})` missing key raises
  `AttributeError("Invalid setting: ...")`; the three readers default only on a MISSING key. An
  explicit `None` value is returned verbatim (the package `None` stance covers the whole dict,
  not per-key values); a `None` strategy then fails loud at the consumer
  (`resolve_strategy` -> `ConfigurationError` naming `NoneType`). The seam is coherent.
- **exp2 — fail-loud propagation.** With a malformed (list) `DJANGO_STRAWBERRY_FRAMEWORK`,
  `upstream_patches_enabled()` raises `ConfigurationError` (the `getattr` default does NOT
  swallow it) and so does `hasattr`; the failed read leaves no stale cache.
- **exp3 — toggle truthiness.** `{"APPLY_UPSTREAM_PATCHES": "false"}` silently ENABLES the
  patches (truthy string); `0` silently disables. The current coercion accepts wrong shapes the
  module's own `_normalize_user_settings` precedent would reject.
- **exp4 — dict identity fast-path.** Mutating the consumer's own dict after assignment is
  observed through the proxy, as documented.
- **exp5 — the inherited Medium's escape hatch, executable.** With all three patches reverted to
  the captured originals and `{"APPLY_UPSTREAM_PATCHES": False}`, all three `apply()`s no-op:
  silencing the test-only Django patch this way also drops both production request-hardening
  patches (installed states `(False, False, False)`).
- **exp6 — drift/gate ordering.** A drifted Django body pin makes `apply()` raise the targeted
  `RuntimeError` even when the patch is already installed (validation precedes the
  installed-check); the gate precedes validation, so an opt-out at the gate position silences the
  abort — a per-dependency gate at the same position works identically.
- **exp7 — per-dependency shape prototype.** A reader-local prototype of the proposed
  `upstream_patches_enabled(dependency)` semantics: bool back-compat, per-name opt-out with
  missing names defaulting on, `ConfigurationError` on unknown names (typos), non-bool values,
  and non-bool/non-mapping shapes. Semantics are unambiguous and implementable.
- **exp8 — collection trap (found by accident, then pinned).** The first run of the scratch file
  imported `testing_endpoint_setting` unaliased; pytest collected it (name matches the default
  `test*` function pattern), it returned a `str`, and the run FAILED via
  `PytestReturnNotNoneWarning` under the repo's `filterwarnings = error` (pytest.ini:25-26). A
  separate probe confirmed `__test__ = False` on a function suppresses collection ("no tests
  ran").

## Improvements

### High

None.

### Medium

- **Observation:** `APPLY_UPSTREAM_PATCHES` is all-or-nothing, coupling three patches with
  different risk classes behind one boolean: the TEST-ONLY Django teardown patch
  (`_django_patches`, `SimpleTestCase` cleanup) and the two PRODUCTION request-hardening patches
  (`_strawberry_patches` / `_cross_web_patches`, malformed-body 400s). The Django patch's
  fail-loud body pin has imminent drift (Django `main` already moved the pinned body per
  `rev-_django_patches.md`; `pyproject.toml` pins `Django>=5.2` with no ceiling), and that drift
  aborts EVERY process type at `ready()` — including production servers where the patched code
  can never run — while the only escape today silently drops the production hardening too.
  (Inherited from `rev-apps.md` Medium 2, verified there; ownership accepted here — the toggle's
  granularity is `conf.py`'s design, not `ready()`'s dispatch.)
  **Evidence:** conf.py:49-53 ("Toggle for every defensive patch") and conf.py:182-196 (one
  boolean, three gates); exp5 (global `False` leaves installed states `(False, False, False)` —
  the escape drops the hardening); exp6 (a drifted pin raises even when installed, and the gate
  position silences it); rev-apps.md exp4c (a consumer's `django.setup()` fails outright on the
  drifted pin, with the `RuntimeError` text itself steering consumers to the all-or-nothing
  `APPLY_UPSTREAM_PATCHES` hatch — e.g. _django_patches.py:188-193); exp3 (the current
  `bool()` coercion also silently accepts wrong value shapes like `"false"` -> enabled).
  **Impact:** consumers upgrading Django ahead of the package will have production deployments
  refuse to boot over a test-teardown patch, and the escape the error message tells them to reach
  for reverts non-UTF-8 and scalar-body requests to upstream 500s — the silent-drop failure mode
  the fail-loud redesign exists to prevent, reintroduced through toggle coarseness.
  **Recommendation:** root-cause fix in `conf.py` (the toggle's owner), with the gate call sites
  following: accept `bool | Mapping[str, bool]` for `APPLY_UPSTREAM_PATCHES`. `True`/`False`
  keep today's global semantics; a mapping keyed by the canonical dependency names — a
  `conf.py`-owned constant, e.g. `UPSTREAM_PATCH_DEPENDENCIES = frozenset({"django",
  "strawberry", "cross_web"})`, matching the one-module-per-dependency organizing rule — opts
  out per dependency, missing names defaulting to `True` (opt-out stance preserved). Change
  `upstream_patches_enabled()` to `upstream_patches_enabled(dependency: str)` (internal API;
  not exported from the package `__init__`, all three call sites are the patch modules), each
  `apply()` passing its own name. Shape violations fail loud with `ConfigurationError`: unknown
  dependency names (typo protection — a misspelled name must not silently keep patching),
  non-bool mapping values, and non-bool/non-mapping top-level values (this also closes exp3's
  silent `"false"` -> enabled coercion, aligning the toggle with the module's own
  `_normalize_user_settings` fail-loud precedent). Update the three drift `RuntimeError`
  messages to name the per-dependency escape (e.g. `{"APPLY_UPSTREAM_PATCHES": {"django":
  False}}`) — the message is the exact surface where the trap currently fires — and the three
  module docstrings' opt-out sentences; document in `conf.py` that strawberry+cross_web jointly
  own one fix (disabling one alone is safe but leaves the sync transport unfixed). The
  settings-key rule is satisfied: the key's new shape lands with the feature that needs it.
  Expanded ownership named per REVIEW.md: `conf.py` (reader + constant + shape validation), the
  three `_*_patches.py` gate lines / docstrings / error messages, `tests/base/test_conf.py`, and
  the three patch-module suites. If the project pass later lands the three-module `apply()`
  scaffold DRY (`rev-apps.md`'s fallback note), the per-dependency gate rides that scaffold; the
  setting's shape contract stays here.
  Considered and rejected: catching/downgrading in `ready()` (silent drop at the wrong layer,
  already rejected in `rev-apps.md`); a collection-of-names shape (ambiguous — enabled-set vs
  disabled-set — where a mapping is explicit); keeping the loose `bool()` coercion for mapping
  values (a `{"django": "false"}` typo would invert intent).
  **Proof:** package tests (the reverted-patch and drifted-pin states are unreachable from a live
  query): with `{"django": False}` and a drifted Django pin, `apply_django()` no-ops while
  `apply_strawberry()` / `apply_cross_web()` still install (the inherited scenario resolved —
  exp5/exp6 are the templates); bool back-compat tests stay green
  (tests/base/test_conf.py:176-189); new `ConfigurationError` tests for unknown names, non-bool
  values, and non-bool/non-mapping shapes (exp7 is the semantics template).

### Low

- **Observation:** `testing_endpoint_setting` is collected as a test by pytest whenever a test
  module imports it unaliased: the name matches pytest's default `test*` function pattern, and
  the function returns a `str`, which fails the run via `PytestReturnNotNoneWarning` under the
  repo's `filterwarnings = error` posture (and warns/fails on modern pytest generally).
  **Evidence:** exp8 — the first run of this item's own scratch file failed exactly this way
  (collected as `test_scratch.py::testing_endpoint_setting`, "returned <class 'str'>");
  pytest.ini:4 does not constrain `python_functions`, pytest.ini:25-26 sets
  `filterwarnings = error`; the package already guards this hazard class one consumer up —
  `TestClient.__test__ = False` at testing/client.py:101-105 exists because `Test*` names
  trip collection "a hard failure under the repo's `-W error` posture". No in-repo test imports
  the bare name today (grep: only testing/client.py:42), so the trap is armed, not sprung.
  **Impact:** the reader's natural audience is test code — the first package or consumer test
  module that imports it unaliased (e.g. the natural direct test for this very function, which
  `tests/base/test_conf.py` currently lacks) gets a spurious collected "test" that fails the
  suite with a message pointing at pytest documentation instead of the actual cause.
  **Recommendation:** own in `conf.py`: set `testing_endpoint_setting.__test__ = False`
  immediately after the definition, with a comment mirroring the client.py collection-guard
  precedent. Rejected alternative: renaming the reader — it breaks the `TESTING_ENDPOINT` /
  `testing/` naming symmetry and an existing import for a problem the established `__test__`
  idiom solves in place. Verified viable: a probe function with `__test__ = False` is not
  collected ("no tests ran").
  **Proof:** a permanent test in `tests/base/test_conf.py` that imports
  `testing_endpoint_setting` UNALIASED and asserts `__test__ is False` — self-proving: if the
  guard is ever dropped, that very import makes the suite fail at collection again.
- **Observation:** the package's five settings keys split across two access idioms: three have
  `conf.py` key constants + named readers with documented defaults; two are raw string-literal
  `getattr` reads at their consumer sites (`HIDE_FLAT_FILTERS` at filters/inputs.py:675,
  `RELAY_GLOBALID_STRATEGY` at types/relay.py:381), invisible from `conf.py`.
  **Evidence:** conf.py:46-67 declares constants for exactly three keys; enumerating the real
  key inventory for this review required a package-wide grep because `conf.py` — whose module
  docstring presents it as the package-settings home — does not name two of them.
  **Impact:** bounded maintainability: no single supported-keys inventory for consumers or
  re-audits; a typo'd key literal at a consumer site silently returns the default (the exact
  failure mode named readers exist to prevent); a second consumer of either key could restate a
  drifting default.
  **Recommendation:** own in `conf.py`: add the two key constants and thin named readers
  (`hide_flat_filters_setting()` defaulting `False`, `relay_globalid_strategy_setting()`
  defaulting `None`), consumers importing them; domain validation stays at the consumers per the
  established "thin reader" stance (types/relay.py:356-357), and the in-function import at
  types/relay.py:372 imports the reader the same cycle-safe way it imports `settings` today.
  Not preemptive population (the AGENTS.md rule): both features shipped long since; this moves
  existing reads to the established idiom.
  **Proof:** grep sweep — no `getattr(settings, "<KEY>"` literal remains outside `conf.py`;
  existing filter/relay consumer tests stay green unchanged.

## Summary

The proxy core is sound and well-tested: the missing-key `AttributeError` contract, the
normalization shape contract at all three cache-write sites, in-place signal refresh, dunder
short-circuiting, and — the module's best property — `ConfigurationError` refusing to hide
behind `hasattr`/`getattr` defaults were all confirmed executably. The one genuine design flaw is
the inherited toggle-granularity Medium, owned here: one boolean couples a test-only patch's
imminent, fail-loud drift abort to the production request hardening, and the abort's own error
message steers consumers into silently dropping that hardening; the per-dependency mapping shape
(exp7) is the root-cause fix and also tightens the toggle's silently-loose truthiness. Two Lows:
a pytest-collection trap on `testing_endpoint_setting` (reproduced live during this review;
one-line ``__test__`` guard with in-repo precedent) and consolidating the two raw settings reads
into the named-reader idiom so `conf.py` actually is the key inventory it documents itself to
be. Needs Worker 2 for the Medium and both Lows.

## Implementation (Worker 2)

All three accepted findings verified before editing (the scoped diff vs the item baseline
`1c233430` was empty for every ownership file; the 7 scratch experiments under
`docs/review/temp-tests/conf/` re-ran green pre-fix, 7 passed). All three implemented; none
rejected or deferred.

### Changed files and why

- `django_strawberry_framework/conf.py` - the root-cause owner.
  - Medium 1: `upstream_patches_enabled()` -> `upstream_patches_enabled(dependency)` accepting
    `bool | Mapping[str, bool]`; new conf.py-owned `UPSTREAM_PATCH_DEPENDENCIES =
    frozenset({"django", "strawberry", "cross_web"})` (its comment documents the
    strawberry+cross_web joint ownership of the malformed-body fix). Fail-loud
    `ConfigurationError` on unknown mapping names (the WHOLE mapping is validated on every read,
    so a typo raises regardless of which gate reads first), non-bool mapping values, and
    non-bool/non-mapping top-level values - the last closes exp3's silent `"false"`-is-truthy
    coercion. Plain `True`/`False` keeps byte-identical global semantics (back-compat). One
    addition beyond the Recommendation's letter, at the same layer: a `dependency` argument
    outside the constant raises `ValueError`, so a future patch module whose gate passes an
    unlisted name cannot be silently un-opt-out-able (the constant stays authoritative; the
    internal-API contract is documented in the docstring).
  - Low 1: `testing_endpoint_setting.__test__ = False` immediately after the definition, comment
    mirroring the `testing/client.py::TestClient` precedent.
  - Low 2: new `HIDE_FLAT_FILTERS_KEY` / `RELAY_GLOBALID_STRATEGY_KEY` constants and thin named
    readers `hide_flat_filters_setting()` (default `False`) / `relay_globalid_strategy_setting()`
    (default `None`); domain validation stays at the consumers per the thin-reader stance.
- `django_strawberry_framework/_django_patches.py`, `_strawberry_patches.py`,
  `_cross_web_patches.py` - each `apply()` gate passes its own canonical name; every
  `RuntimeError` escape-hatch tail (3 + 4 + 3 messages) now names the per-dependency form
  (`APPLY_UPSTREAM_PATCHES = {"<name>": False}`) - the drift message is the exact surface where
  the trap fires; module docstrings' opt-out sentences updated, with the joint-fix caveat on the
  strawberry/cross_web pair.
- `django_strawberry_framework/filters/inputs.py` - imports `hide_flat_filters_setting` instead
  of `settings` (its only conf use); the `bool()` truthiness coercion stays at the consumer.
- `django_strawberry_framework/types/relay.py` - the in-function conf import (cycle-safe, per the
  existing comment) now imports `relay_globalid_strategy_setting`; the raw `getattr` read is gone.
- `tests/base/test_conf.py`, `tests/test_django_patches.py`, `tests/test_strawberry_patches.py`,
  `tests/test_cross_web_patches.py` - permanent tests below.

Not changed: `apps.py` (its "global False gets none of them" sentence stays true and it defers
patch-toggle detail to the module docstrings); `docs/GLOSSARY.md` / `docs/README.md` /
`README.md` mentions of the toggle stay accurate for the bool shape (back-compat) and are
outside this item's ownership - the GLOSSARY is DB-rendered and both docs are touched by
concurrent sessions.

### Permanent tests and the behavior they pin

`tests/base/test_conf.py` (package tier - the reverted-patch/drifted-pin/malformed-config states
are unreachable from a live query):

- bool back-compat parametrized over all three dependency names (default-on missing key, `True`,
  `False` - the pre-mapping semantics preserved).
- `{"django": False}` disables exactly `django`; `strawberry`/`cross_web` stay `True` (the
  inherited Medium's contract); empty mapping == missing key; a non-dict `Mapping`
  (`MappingProxyType`) accepted.
- `ConfigurationError`: unknown mapping name (raised even when the *requested* dependency is
  spelled correctly), non-bool mapping value (`{"django": "false"}`), non-bool/non-mapping
  top-level (`"false"`, `0`, `1`, `None`) - exp3's silent coercion closed.
- `ValueError` on an unknown `dependency` argument (constant/call-site lockstep).
- `test_testing_endpoint_setting_carries_pytest_collection_guard` asserts `__test__ is False`
  AND the module imports `testing_endpoint_setting` UNALIASED - self-proving: dropping the guard
  fails the suite at collection again (exp8's trap, now permanently armed against regression).

Patch suites (each gate reads its own name; production hardening survives the django opt-out):

- `tests/test_django_patches.py::test_apply_no_ops_when_django_dependency_opted_out` -
  `{"django": False}` declines to install; `{"strawberry": False}` installs normally.
- `tests/test_django_patches.py::test_django_dependency_opt_out_silences_drifted_pin_abort` -
  the inherited scenario end to end (exp6 template): a drifted body pin raises the targeted
  `RuntimeError` whose text is asserted to name `{"django": False}`, and that per-dependency
  setting then silences the abort without the global `False`.
- `tests/test_strawberry_patches.py::test_apply_no_ops_when_strawberry_dependency_opted_out` and
  `tests/test_cross_web_patches.py::test_apply_no_ops_when_cross_web_dependency_opted_out` -
  each module's own opt-out no-ops it, while `{"django": False}` leaves it installing (exp5's
  silent-drop failure mode resolved).

### Verification run and results

- Pre-fix: `uv run pytest docs/review/temp-tests/conf/ --no-cov -n0 -q` - 7 passed (findings
  reconfirmed executably before editing).
- Post-fix: `uv run pytest tests/base/test_conf.py tests/test_django_patches.py
  tests/test_strawberry_patches.py tests/test_cross_web_patches.py tests/test_apps.py --no-cov
  -n0 -q` - 103 passed (includes the untouched apps-dispatch and bool-toggle regression tests).
- Consumer suites for Low 2: `uv run pytest tests/filters/test_inputs.py
  tests/types/test_relay_interfaces.py --no-cov -n0 -q` - 185 passed, unchanged.
- Live tier for Low 2: `uv run pytest examples/fakeshop/test_query/test_library_api.py -k "hide
  or flat" --no-cov -n0 -q` - 6 passed (the `HIDE_FLAT_FILTERS` live regressions through
  `/graphql`).
- Grep sweep (Low 2 proof): no `HIDE_FLAT_FILTERS` / `RELAY_GLOBALID_STRATEGY` string-literal
  read remains outside `conf.py`; the sole remaining literal is
  `types/base.py::_validate_globalid_strategy`'s error-text subject, which is message framing,
  not a read.
- Note: the Worker 1 scratch file is now stale by design - exp1/2/3/5/6 call the reader with the
  OLD no-arg signature, and exp3 asserts the pre-fix coercion this change removes. It is
  disposable pre-fix evidence; the post-fix contracts are pinned by the permanent tests above.

### Formatter / linter

`uv run ruff format .` - 352 files left unchanged (the edits were written format-clean);
`uv run ruff check --fix .` - all checks passed.

### Changelog-worthiness

Yes (not edited, per instruction): `APPLY_UPSTREAM_PATCHES` now additionally accepts a
per-dependency `{"django"|"strawberry"|"cross_web": bool}` mapping, and previously-silent wrong
shapes (`"false"`, `0`/`1`, typo'd names) now raise `ConfigurationError` - a consumer relying on
truthy/falsy non-bool values will now fail loud at app load. The plain `True`/`False` bool shape
is fully backward-compatible. The two new named readers and the `__test__` guard are internal
and need no note.

## Independent verification (Worker 3)

Scope re-confirmed: `git --no-pager diff 1c233430 --stat` is exactly the 10 files named above;
concurrent maintainer work untouched. Re-traced independently: the settings flow (dict identity
fast-path, per-read whole-mapping validation, `setting_changed` refresh), gate-before-validation
ordering in all three `apply()`s, the reader's internal-API status (not exported from the package
`__init__`; the only callers are the three gates, each passing its own canonical name), and the
key inventory (no raw `HIDE_FLAT_FILTERS` / `RELAY_GLOBALID_STRATEGY` read remains outside
`conf.py` - the residual grep hits in `orders/inputs.py`, `utils/inputs.py`,
`types/definition.py`, and `types/base.py` are comments/docstrings/error framing, not reads -
and `apps.py`'s "global `False` gets none of them" sentence stays true).

Scratch experiments: `docs/review/temp-tests/conf/test_w3_verify.py` (10 passed,
`uv run pytest docs/review/temp-tests/conf/test_w3_verify.py --no-cov -n0 -q`; Worker 1's stale
pre-fix scratch left untouched and excluded from the run):

- **w3_exp1 - the inherited rev-apps.md scenario, end to end.** All three patches reverted to
  captured originals + a drifted Django body pin: bare `apply()` raises the targeted
  `RuntimeError` whose text names `{"django": False}`; with that mapping configured, the
  `apps.py` dispatch order leaves installed states `(False, True, True)` - the abort silenced,
  both production hardenings installed. The inherited Medium is genuinely closed.
- **w3_exp2 - mapping mutated after load.** Mutations of the consumer's own mapping are observed
  on the next read (the documented live-dict seam), and a typo or non-bool value added AFTER a
  successful read still fails loud - validation truly runs per read.
- **w3_exp3 - `MappingProxyType`** accepted for the toggle; a proxy with an unknown name raises.
- **w3_exp4 - `override_settings` mid-process.** Nested enter/exit both refresh the singleton
  for the mapping shape; inner-exit restores the outer override, outer-exit the project default.
- **w3_exp5 - unknown name beside a valid requested entry** raises (whole-mapping validation).
- **w3_exp6 - the flagged `ValueError` addition, assessed and ACCEPTED.** The guard precedes the
  settings read entirely (fires under global `False` and even under a malformed settings dict),
  uses the right exception class for a programmer error at an internal API (vs
  `ConfigurationError` for consumer config), and is permanently tested. Right layer, keeps the
  constant authoritative; no revision required for it.
- **w3_exp7 / w3_exp7b - pathological mapping keys.** `{1: False}` gets the clean
  `ConfigurationError`; mixed unorderable keys do not - the finding below.
- **w3_exp8 - repeated `ready()`** under `{"django": False}` stays a no-op; the production
  patches stay installed.
- **w3_exp9 - the two named readers byte-match the old raw reads**: default only on the missing
  key, verbatim values (including explicit `None` and truthy non-bools - coercion stays at the
  consumer), and `ConfigurationError` propagation through the `getattr` defaults.

Focused permanent runs (independent re-run): `tests/base/test_conf.py` + the three patch suites
+ `tests/test_apps.py` - 103 passed; consumer suites `tests/filters/test_inputs.py` +
`tests/types/test_relay_interfaces.py` - 185 passed, unchanged; live tier
`examples/fakeshop/test_query/test_library_api.py -k "hide or flat"` - 6 passed. All with
`--no-cov -n0`. Fail-without-fix confirmed structurally: every new reader test calls the one-arg
signature (pre-fix `TypeError`), the drift test asserts message text that did not exist pre-fix,
and the collection-guard test's UNALIASED import is self-proving (this run's clean collection of
`test_conf.py` is itself the live proof the guard works).

### Revision required (returns to Worker 2)

- **Observation:** `upstream_patches_enabled`'s unknown-name error framing crashes with a raw
  `TypeError` instead of the documented `ConfigurationError` when the unknown mapping keys are
  of mixed unorderable types.
  **Evidence:** w3_exp7b - `{"APPLY_UPSTREAM_PATCHES": {1: False, "x": False}}` then
  `upstream_patches_enabled("django")` raises `TypeError: '<' not supported between instances
  of 'str' and 'int'` from `sorted(unknown)` at conf.py:263, evaluated while building the
  `ConfigurationError` message.
  **Impact:** still fail-loud at the same raise site, but the reader's docstring promises
  `ConfigurationError` for "any other shape" and the valid-names guidance never materializes;
  the in-repo precedent for this exact hazard
  (`django_strawberry_framework/types/base.py::_validate_relation_shapes` #"keys must be
  relation field name strings") guards key types before formatting, so the new code falls short
  of the house standard it sits beside.
  **Recommendation:** fix at the same site - make the unknown-name framing key-type-robust
  (e.g. `sorted(unknown, key=repr)` / repr-based rendering, or a string-key shape check ahead of
  the membership check per the `_validate_relation_shapes` precedent).
  **Proof:** a permanent `tests/base/test_conf.py` test pinning `ConfigurationError` (not
  `TypeError`) for a mixed-type unknown-keys mapping; w3_exp7b is the repro template.

Everything else verified clean; on the revision pass only this item and its new test need
re-checking. The plan checkbox stays unmarked.

## Iterations

### Revision pass (Worker 2)

Single revision item (w3_exp7b) reproduced first, then fixed.

- **Repro:** wrote the permanent test before touching production code; pre-fix run failed with
  exactly the reported `TypeError: '<' not supported between instances of 'str' and 'int'` from
  `sorted(unknown)` at conf.py:263 (`uv run pytest
  tests/base/test_conf.py::test_upstream_patches_enabled_rejects_non_string_mapping_key
  --no-cov -n0 -q` - 1 failed, TypeError at conf.py:263).
- **Fix (`django_strawberry_framework/conf.py`):** chose the string-key shape check ahead of the
  membership check - the `types/base.py::_validate_relation_shapes` key-guard precedent Worker 3
  named - over the `sorted(unknown, key=repr)` rendering patch: a non-string key is a wrong
  SHAPE, not a candidate name, so it earns its own framing (`` `APPLY_UPSTREAM_PATCHES` keys
  must be dependency name strings; got 1. ``) instead of being folded into a repr-sorted
  unknown-names list. The guard loop runs first inside the `Mapping` branch; after it, every
  key is a string, so the existing `sorted(unknown)` framing (and its valid-names guidance) is
  structurally safe - no rendering workaround needed. A comment at the guard names the hazard
  and the precedent. The docstring's shape-violation list now includes the non-string-key case,
  keeping the "any other shape raises ConfigurationError" promise accurate.
  Behavior note: a pure non-string-key mapping like `{1: False}` (w3_exp7) previously took the
  unknown-name path; it now gets the key-type framing - still `ConfigurationError`, and the
  message now states the actual problem (wrong key type) rather than listing `1` beside
  valid dependency names.
- **Permanent test:**
  `tests/base/test_conf.py::test_upstream_patches_enabled_rejects_non_string_mapping_key` pins
  `ConfigurationError` (match `"dependency name strings"`) for the mixed-type
  `{1: False, "x": False}` mapping - w3_exp7b's exact repro shape. Fail-without-fix proven
  above (the pre-fix run IS the repro).
- **Focused run:** `uv run pytest tests/base/test_conf.py --no-cov -n0 -q` - 40 passed (the 39
  prior tests unchanged plus the new pin; the unknown-name, non-bool-value, and top-level-shape
  contracts all still hold).
- **Formatter / linter:** `uv run ruff format .` - 352 files left unchanged; `uv run ruff check
  --fix .` - all checks passed.
- **Scope:** only `conf.py` and `tests/base/test_conf.py` touched this pass; all concurrent
  dirty work preserved. Changelog-worthiness unchanged from the main pass (the new guard is a
  sub-case of the already-noted fail-loud shape validation).
