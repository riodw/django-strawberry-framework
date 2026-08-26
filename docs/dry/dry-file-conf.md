# DRY review: `django_strawberry_framework/conf.py`

Status: verified

## System trace

`conf.py` owns the package-settings contract: the `DJANGO_STRAWBERRY_FRAMEWORK` top-level dict
(`conf.py::DJANGO_SETTINGS_KEY`), the `Settings` singleton lifecycle (lazy first read from
`django.conf.settings`, in-place mutation on Django's `setting_changed` via
`conf.py::reload_settings` connected at import with a `dispatch_uid`, and live-sync re-derivation
when the key is replaced/deleted without a signal), one shape contract shared by every cache write
(`conf.py::_normalize_user_settings`: `None`→`{}`, non-Mapping→`ConfigurationError`, dict identity
preserved, other Mappings copied), ten key constants, and one thin reader per key plus
`conf.py::upstream_patches_enabled` — the only reader that validates its value's shape.

Consumers, one per key: `filters/inputs.py::_build_input_fields` (`HIDE_FLAT_FILTERS`),
`optimizer/nested_fetch.py::resolve_strategy` (`NESTED_CONNECTION_STRATEGY`; function-local import),
`optimizer/single_parent_fetch.py` (`SINGLE_PARENT_FAST_PATH`),
`types/relay.py::_validated_globalid_setting` (`RELAY_GLOBALID_STRATEGY`; function-local import),
`views.py::_resolved_max_request_body_bytes` (`MAX_REQUEST_BODY_BYTES`),
`resource_policy.py::resolve_resource_policy` (`RESOURCE_POLICY`),
`error_policy.py::resolve_error_policy` (`ERROR_POLICY`), `testing/client.py::TestClient.__init__`
(`TESTING_ENDPOINT`; `AsyncTestClient` subclasses it, so both transports share one resolution site),
and the three patch modules' `apply()` gates (`APPLY_UPSTREAM_PATCHES`). Domain validation lives at
each consumer where the vocabulary lives; `conf.py` deliberately stays a non-validating reader
except for the patch toggle. Fakeshop configures the dict once
(`examples/fakeshop/config/settings.py`); `tests/base/test_conf.py` pins the whole lifecycle,
including an enumeration of every defaulted reader for the signal-less-delete sweep.

Lockstep edits by design: a new key lands as conf constant + reader + consumer + tests (AGENTS.md:
only when the feature lands); a key rename moves the constant plus anything naming it in code,
docs, and tests.

## Verification

All five axes discharged:

1. **Cross-flavor policy mirroring** — searched: `grep -rn` for `_setting(` consumers, direct
   `DJANGO_STRAWBERRY_FRAMEWORK` reads, and `from .conf import settings` across production code.
   Zero modules read the dict or `django.conf.settings` for package keys outside `conf.py`; every
   public surface goes through its single reader. Graphene-django's `TESTING_ENDPOINT` knob is
   namespaced, not mirrored. Ruled out.
2. **Sync and async twins** — searched `AsyncTestClient` / `query_async` in `testing/client.py`:
   the async client inherits `TestClient.__init__`, so endpoint resolution has exactly one site;
   every reader is a synchronous attribute lookup with no await boundary anywhere on this surface.
   Ruled out.
3. **Derived rather than repeated knowledge** — searched every key-name string literal and every
   default literal (`"windowed"`, `"/graphql/"`, `1_048_576`) outside `conf.py`. All hits are
   docstrings/comments except one code hit: `types/base.py::_validate_globalid_strategy`
   hard-codes `"RELAY_GLOBALID_STRATEGY"` as the setting-path error subject while
   `conf.py::RELAY_GLOBALID_STRATEGY_KEY` owns the name — a fact rebuilt by second spelling.
   Found (implemented below). Related coupling checked: `conf.py`'s `"windowed"` getattr default
   must stay a member of `nested_fetch.py`'s strategy registry, but drift there fails loud
   (`resolve_strategy` raises `ConfigurationError`) and is pinned by tests; see rejected candidate.
4. **Inverse and round-trip pairs** — the signal-driven write path (`reload_settings` →
   `_reload_from_django`) and the live-read path (`Settings.user_settings`) are the two halves of
   one cache-coherence mechanism, co-located in this module and funneled through the single
   `_normalize_user_settings`. Already consolidated at the root owner. Ruled out.
5. **Contracts restated in another medium** — counted media for one concrete key
   (`TESTING_ENDPOINT`): reader code, `testing/client.py` + `testing/__init__.py` docstrings,
   `docs/GLOSSARY.md`, `examples/fakeshop/test_query/test_client_api.py`, and the
   `tests/base/test_conf.py` enumeration. Each precedence ladder is implemented once in code
   (`TestClient.__init__`; `_resolved_max_request_body_bytes`); the other media document or pin the
   contract, which is expected. `test_conf.py`'s two enumeration tests are deliberate, documented
   repetition (a key without a row there leaves the stale sweep silent) and stay.

Single-edit-site counts (posited changes):

- Rename settings key `RELAY_GLOBALID_STRATEGY` → forced `conf.py` constant +
  `types/base.py` error label = **2** code sites pre-fix; **1** post-fix (implemented).
- Change `TESTING_ENDPOINT` default `"/graphql/"` → `/gql/` → `conf.py` reader only = **1**
  (thin-reader ownership holds; docs/tests follow by design).
- Rename strategy `"windowed"` → `nested_fetch.py` registry/`name` + `conf.py` getattr default =
  **2**, but rejected: consolidation would need `conf → optimizer` module-top imports (layering
  inversion against the existing lazy `optimizer → conf` edges, whose cycle-dodge comments say "do
  NOT hoist") or lazy imports inside the reader; today's drift fails loudly at the first extension
  construction and is pinned by `tests/base/test_conf.py`.
- Add a new settings key → conf + consumer + tests >1, inherent to landing a feature, not
  duplication (AGENTS.md forbids preemptive keys).

Strongest rejected candidates: the `"windowed"` default (above) and the `None`-coercion stance
shared with `types/base.py`'s `Meta.optimizer_hints` — the module docstring itself marks them as
different contracts ("Do not unify": upstream legitimately allows absent/`None` on reflective
shapes) with different reasons to change.

## Opportunities

**Setting-path error label restated the key name instead of deriving it**

- Repeated responsibility: the name of the `RELAY_GLOBALID_STRATEGY` settings key existed twice in
  code — `conf.py::RELAY_GLOBALID_STRATEGY_KEY` (owner) and the hard-coded error subject in
  `types/base.py::_validate_globalid_strategy` for `source="setting"` (every other
  `ConfigurationError` in `conf.py` already interpolates its own constants, so the validator missed
  the package's own precedent).
- Sites: the two above; tests pinning the framing (`tests/types/test_relay_interfaces.py`,
  multiple `match="RELAY_GLOBALID_STRATEGY"` assertions).
- Evidence: posited rename of the key forced 2 code sites; a rename done only at the constant left
  user-facing errors naming a key that no longer exists — silent contract drift in exactly the
  medium (error text) users copy when fixing configuration.
- Owner: `conf.py::RELAY_GLOBALID_STRATEGY_KEY`.
- Consolidation: `types/base.py` imports the constant (module-top; safe — `conf.py` imports only
  django bits + `exceptions`, and `filters/views/resource_policy/error_policy/testing` already do
  module-top conf imports) and uses it as the `source="setting"` subject. The relay-side lazy
  import convention is untouched (its cycle comment concerns `relay → base`, not `base → conf`).
- Proof: new `tests/types/test_relay_interfaces.py::test_setting_error_framing_tracks_the_conf_key_constant`
  sets the key via the constant and asserts the raised message matches the constant's value — a
  future rename passes only if the label moves with it.
- Risks / non-goals: message bytes are unchanged today, so existing `match=` assertions stay green;
  the `Meta.globalid_strategy` subject framing is untouched; docstrings may keep spelling the key
  in prose.

## Judgment

`conf.py` is itself the package's consolidation: one normalizer, one singleton, one reader per key,
validation pushed to the vocabularies that own it. The five-axis sweep found exactly one fact
spelled twice in code — the globalid settings-key label — now derived from the owning constant;
everything else that looks repeated is either intentional test repetition or fail-loud coupling
with worse consolidation shapes than the duplication.

## Implementation (Worker 1)

- `django_strawberry_framework/types/base.py`: module-top `from ..conf import
  RELAY_GLOBALID_STRATEGY_KEY`; `_validate_globalid_strategy`'s setting-path subject now
  interpolates the constant.
- `tests/types/test_relay_interfaces.py`: added
  `test_setting_error_framing_tracks_the_conf_key_constant` next to the sibling setting-path
  framing tests (no orphan imports; `conf` was already imported).
- Ran `uv run ruff format .`, `uv run ruff check --fix .` (all checks pass) and
  `scripts/check_trailing_commas.py` (0 fixes). Bare-import sanity check confirmed no import cycle.
  Pytest deferred per AGENTS.md (not explicitly requested).

## Independent verification (Worker 2)

Scoped diff vs baseline 7076e03 is exactly the claimed two files: `types/base.py` (module-top
`from ..conf import RELAY_GLOBALID_STRATEGY_KEY` + subject interpolation, nothing else) and
`tests/types/test_relay_interfaces.py` (one added test). All other dirty files are concurrent
work; untouched.

Independently re-traced `conf.py`: ten key constants + `DJANGO_SETTINGS_KEY`, four cache-write
sites all funneled through `_normalize_user_settings`, `__getattr__` KeyError→AttributeError
pinned at `tests/base/test_conf.py:23`, defaulted-reader enumeration pinned at
`tests/base/test_conf.py:414-445`. No import cycle: `exceptions.py` imports nothing from the
package.

**Error-string equivalence: confirmed identical.** Pre-fix subject literal `"RELAY_GLOBALID_STRATEGY"`
== `conf.py::RELAY_GLOBALID_STRATEGY_KEY`'s value (`conf.py:110`); both downstream framings
(unknown-strategy and must-be-one-of) and `_validate_globalid_callable(subject, ...)` consume the
same `subject`, so every raised message is byte-identical today and existing `match=` pins stay
green. Docstring prose keeps spelling the key — allowed non-goal.

**Pin strength: adequate.** The new test drives the real path (pytest-django override → signal →
finalize → setting-source validation) and asserts the message matches the constant's value. It
cannot distinguish derivation from a coincidentally-equal re-hard-code while values agree — no
black-box message test can — but it enforces "error subject == constant value" at every run, so
any divergence (rename at either end, including a latent re-hard-code followed by a later rename)
fails the test. That is exactly the drift class the fix targets. A monkeypatch-the-imported-name
probe would prove mechanism rather than contract; the real-path form matches sibling framing tests.

**Residual literal sweep (correction to Verification axis 3):** my grep found MORE than one code
hit outside `conf.py`: nine RUNTIME strings spelling `APPLY_UPSTREAM_PATCHES` inside raised
`RuntimeError`s (`_django_patches.py:237/245/257`, `_strawberry_patches.py:515/532/544`,
`_cross_web_patches.py:259/266/274`) — the axis-3 sentence "all hits are docstrings/comments
except one" is imprecise as written. Not a missed consolidation, though: those sites belong to the
`_django_patches` item of this same cycle, where the identical candidate ("opt-out hint builder",
same 9-raise recount) was raised and rejected with standing reasons (public-key rename is
inherently repo-wide/greppable; messages bespoke; interpolation obscures fail-loud diagnostics)
and independently verified there; unlike base.py's bare error SUBJECT, these fragments render
opt-out example syntax. All other key-name/default literals outside conf.py are docstrings,
comments, or prose, as claimed. Axis 1 re-verified: every `django.conf.settings` reader outside
conf.py touches only Django's own keys (SECRET_KEY, DEBUG, USE_TZ, MIDDLEWARE,
SESSION_ENGINE, AUTH_USER_MODEL), zero package keys.

Rejected candidates re-probed and upheld: `"windowed"` default couples to `nested_fetch.py`'s
registry (`name = "windowed"` at :344, registry map at :399) but drift raises
`ConfigurationError` at first extension construction and the default is pinned in
`tests/base/test_conf.py`; consolidating needs a `conf → optimizer` edge against the existing
lazy reverse imports. The `None`-coercion stance difference with `Meta.optimizer_hints` is
explicitly documented as "Do not unify" in `conf.py`'s module docstring with distinct reasons to
change. Async twin ruled out on the real surface: `AsyncTestClient.__init__` forwards to
`TestClient.__init__` (`testing/client.py:400`), keeping endpoint resolution at one site.

Recount with my own posited change — rename key to `"RELAY_GID_STRATEGY_V2"`: post-fix forced
code sites = `conf.py:110` only (**1**, grep-confirmed; base.py follows by derivation); pre-fix
would have been **2**. Count holds. Matrix discharged against the real surface on all five axes.
Verdict: verified.
