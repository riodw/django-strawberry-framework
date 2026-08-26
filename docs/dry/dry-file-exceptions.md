# DRY review: `django_strawberry_framework/exceptions.py`

Status: verified

## System trace

The module owns the package's exception hierarchy and the safe-rendering family every typed
diagnostic depends on:

- Hierarchy: `DjangoStrawberryFrameworkError` → `ConfigurationError` → {`PathResolutionError`,
  `LookupValidationError`}, plus `OptimizerError` on the base directly. `utils/querysets.py::
  SyncMisuseError` multiply-inherits `ConfigurationError` + `RuntimeError`. The base overrides
  `__str__` / `__repr__` so GraphQL-core's `located_error` (`str(original_error)` during wire
  wrapping) can never replace a typed exception with a raw error — catchability through the base
  and each subclass survives hostile message args, including delayed/stateful dunder failures and
  `BaseException` from hostile dunders.
- Rendering family: `_safe_type_name`, `_safe_arg_repr`, `_safe_class_name`, `_safe_model_label`,
  `_safe_terminal_label`, `describe_value` — the never-raising diagnostic renderers consumed at
  ~40 rejection sites across types/filters/orders/mutations/forms/rest_framework/auth/conf.
  `describe_value` additionally serves the transport boundary (`views.py` body-cap,
  `consumers.py` revalidation window, `routers.py` factory/consumer rejections) and the
  schema-construction policy modules (`error_policy.py`, `resource_policy.py`,
  `extensions/debug.py`).
- GraphQL translation: the hierarchy itself carries no wire policy. `error_policy.py` /
  `extensions/error_policy.py` classify structurally (non-`GraphQLError` ⇒ masked) — a resolver
  raising a framework exception directly is masked like any accidental escape; the exceptions'
  only wire contract is identity-through-wrapping (above).
- Raise/catch topology: `PathResolutionError` raises only from `utils/relations.py::
  classify_path`; catchers translate (`orders/sets.py` wraps into `ConfigurationError`) or use it
  as the strict/lenient boundary signal (`filters/sets.py`, `path_traverses_to_many`). All
  `OptimizerError` raises sit in optimizer/*, `types/resolvers.py`, `utils/connections.py`.
- Consumers: 64 package files import these names; `tests/test_exceptions.py` pins the lattice,
  rendering safety, hostile-metadata constructors, and pickle/copy fidelity;
  docs/GLOSSARY.md documents `ConfigurationError` / `OptimizerError` / `SyncMisuseError`
  contracts in prose.

Concurrent work honored: the maintainer's in-flight hunks wrap `DjangoStrawberryFrameworkError.
__str__` / `__repr__` renders in `str.__str__(...)`; reviewed present-day state, edited only
regions outside those hunks, reverted nothing.

## Verification

- **Cross-flavor policy mirroring — searched.** Grepped every importer of the five public names
  (64 files): each rejection site owns distinct validation prose; what they share is exactly the
  rendering helpers and the typed classes. Then grepped for local twins of the rendering rule:
  found two orphan bodies — `utils/errors.py::_safe_text` + `_unprintable` (write-error envelope)
  and `types/converters.py::_safe_text` (field labels) — same contract, different modules, and
  already drifted (converters lacked the hostile-str-subclass strip errors.py had). Consolidated
  (see Opportunities). `utils/querysets.py::_safe_class_name` inspected and REJECTED as a twin:
  its stricter non-string fallback (degrade to metaclass label, never repr-dispatch) is a
  documented deliberate divergence for sealed-boundary rejects; merging would need a mode flag.
- **Sync and async twins — ruled inapplicable on the target, searched at the seam.** The target
  is pure hierarchy + sync rendering functions; there is no await surface to twin. The GraphQL
  translation seam is explicitly single-path (`extensions/error_policy.py` module docstring:
  "Sync and async execution share one implementation"; `mask_execution_result` is the one masking
  body applied at two seams). No color-specific branch exists to drift.
- **Derived rather than repeated knowledge — searched.** Grepped raw `type(...).__name__` /
  `__class__.__name__` inside package messages: ~30 sites re-derive the type label
  `_safe_type_name` owns (see recorded finding). Closest miss: `filters/sets.py` logical-branch
  rejection guards the value with `_safe_arg_repr(element)` yet extracts the type raw on the same
  f-string — half-hardened, proving the drift risk is live. Not swept here: the sites span many
  flavors/files (several currently dirty from concurrent work) and the target's own docstring
  fences routing them as a separate change with its own surface.
- **Inverse and round-trip pairs — searched.** The only round-trip grammar on this surface is
  `__init__` ↔ `__reduce__` on `PathResolutionError` / `LookupValidationError`; both halves are
  colocated per class body and pinned by `test_path_resolution_error_pickle_and_copy_fidelity` /
  `test_lookup_validation_error_pickle_and_copy_fidelity`. Single edit site per change. No
  encode/decode pair is split across modules here.
- **Contracts restated in another medium — searched.** Media counted for a hypothetical "new
  OptimizerError raise condition": code site, `OptimizerError` docstring inventory, GLOSSARY
  entry, executable pin where behavior warrants — accepted as the repository's intentional
  documentation layering, not consolidated. One real drift found and fixed: `describe_value`'s
  "Scope, stated exactly" paragraph enumerated only the transport-boundary callers while
  `error_policy.py`, `resource_policy.py`, and `extensions/debug.py` also route through it.

Single-edit-site tests:

- Posited "change the standalone `<unprintable T>` placeholder spelling": before this review it
  forced 4 sites (`_safe_arg_repr` fallback, `__str__` single-arg branch, `errors._unprintable`,
  converters inline); after consolidation it forces 2 — the new shared `_unprintable` plus the
  inline branch inside `DjangoStrawberryFrameworkError.__str__`, left byte-for-byte intact
  because that method is under the maintainer's concurrent edit (its output is pinned by their
  own fresh tests). Both residual sites live in exceptions.py.
- Posited "extend hostile-str-subclass stripping to converter field-label rendering" (exactly the
  maintainer's current hardening campaign applied to `types/converters.py`): before, 2 sites and
  already drifted; after, count came back **one** — `exceptions.py::_safe_text`.
- Rejected-candidate check (strongest): merging `utils/querysets.py::_safe_class_name` into the
  shared `_safe_class_name` — disproved by contract divergence (repr-dispatch avoidance on
  sealed-boundary input), confirmed by its own docstring and the exceptions.py side's matching
  note; parameterizing would add a branch no real path distinguishes today.

Scratch probes (no tracked artifacts): `uv run python -c` import + behavior probe confirmed
`field_error("name", [Hostile()]).messages == ["<unprintable H>"]` and converter label fallback
rendering post-rewiring.

## Opportunities

### Consolidate the orphan safe-str renderers into `exceptions.py` (IMPLEMENTED)

- **Repeated responsibility:** "render an arbitrary value to a plain base `str` without ever
  raising; empty render degrades to a caller-named fallback; raising dunder degrades to the
  standalone `<unprintable {T}>` placeholder" — one rule spelled twice outside its owner, plus
  the placeholder grammar itself spelled four ways.
- **Sites:** `django_strawberry_framework/utils/errors.py` (local `_safe_text` + `_unprintable`,
  hardened), `django_strawberry_framework/types/converters.py` (local `_safe_text`, unhardened —
  the drift), owner `django_strawberry_framework/exceptions.py`.
- **Evidence:** identical inputs (consumer-influenced metadata/messages assembled into error
  envelopes), identical outputs on all benign paths (existing suites pass unchanged), same change
  axis (the hostile-dunder hardening convention — converters had already missed one iteration).
  Posited hardening change forces 1 site after, 2 drifted sites before.
- **Owner:** `exceptions.py` — bottom of the import graph, already host of the family; both
  consumers already imported from it.
- **Consolidation:** added `exceptions._unprintable` (placeholder grammar, one home) and
  `exceptions._safe_text(value, fallback="")` (hardened body adopted from utils/errors);
  deleted both local bodies and imported the shared ones; `_safe_arg_repr`'s except branch now
  routes through `_unprintable` (byte-identical output). `describe_value` keeps its deliberately
  different fragment spelling — documented, not unified.
- **Proof:** `tests/test_exceptions.py::test_safe_text_is_the_shared_str_renderer` pins
  strip/fallback/render/degrade; `test_safe_text_is_single_sourced_across_consumer_modules` pins
  module wiring so a twin cannot silently return; existing `tests/utils/test_errors.py` and
  `tests/types/test_converters.py` hostile-metadata pins now exercise the shared body (coverage
  continuity). Pytest run DEFERRED per repository rules.
- **Risks / non-goals:** `DjangoStrawberryFrameworkError.__str__` / `__repr__` bodies untouched
  (concurrent maintainer edit region); `describe_value` fragment grammar preserved;
  `querysets._safe_class_name` stays separate by contract.

### Recorded, not implemented: raw type-label derivations bypassing `_safe_type_name`

- **Repeated responsibility:** the "type label must survive hostile metaclass metadata" rule,
  re-derived inline at ~30 sites via raw `type(x).__name__` / `__class__.__name__` inside
  rejection messages (conf.py settings gates, filters/sets.py input rejections,
  auth/sessions.py, rest_framework/resolvers.py, mutations/permissions.py, write_transaction.py,
  forms/inputs.py, middleware/request_body.py, …).
- **Evidence:** posited "make every type label hostile-metaclass-proof" forces ~30 edits; the
  half-hardened `filters/sets.py` message proves partial application is the observed failure
  mode.
- **Owner / consolidation:** route label extraction through `_safe_type_name` (or
  `_safe_arg_repr` where a repr belongs) per site; the owner already exists and needs no change.
- **Why not here:** the sites span many flavors and files — several currently dirty from the
  maintainer's concurrent session working this exact convention — and the target's own
  `describe_value` scope paragraph fences the routing as a separate change with its own surface
  and test matrix. Recorded so a dedicated sweep item can take it whole.
- **Risks:** wire-input values are JSON-derived (plain types), so urgency varies by site;
  deployment-/consumer-object-valued sites (settings gates, serializer classes) are the
  motivated subset.

## Judgment

The file's ownership boundaries are sound: one hierarchy, one rendering family, translation
policy correctly delegated to the error-policy seam, strict/lenient path classification correctly
delegated to `classify_path`. The one genuine duplication was the rendering family's str-based
renderer living as two drifting copies outside its owner — now consolidated with drift-guard
tests. Remaining duplication on this surface is either intentional (documentation media,
deliberately divergent `querysets._safe_class_name`, the documented two-spelling placeholder
grammar) or belongs to a dedicated cross-flavor sweep (raw type-label derivation).

## Implementation (Worker 1)

Tracked changes (scoped against cycle baseline `0d68e08`):

- `django_strawberry_framework/exceptions.py`: added `_unprintable` and `_safe_text`; routed
  `_safe_arg_repr`'s fallback through `_unprintable`; corrected `describe_value`'s
  "stated exactly" caller inventory and sibling-spelling comment. No edits inside
  `DjangoStrawberryFrameworkError.__str__` / `__repr__` (concurrent-edit region; maintainer hunks
  intact).
- `django_strawberry_framework/utils/errors.py`: deleted local `_safe_text` / `_unprintable`;
  imports the shared pair.
- `django_strawberry_framework/types/converters.py`: deleted local `_safe_text`; imports the
  shared renderer (gains hostile-str-subclass stripping).
- `tests/test_exceptions.py`: two permanent tests appended + import additions.
- `uv run ruff format .` / `uv run ruff check --fix .` clean; `scripts/check_trailing_commas.py`
  clean; import smoke green. Pytest deferred (not authorized this cycle).

## Independent verification (Worker 2)

Attribution: the maintainer's `__str__` / `__repr__` hardening sits INSIDE the cycle baseline
(`HEAD→0d68e08` touches only `exceptions.py`'s two dunder bodies and adds 49 test lines), so
`0d68e08→worktree` on all four files contains exactly Worker 1's claimed hunks and nothing else;
no additional file was edited by this item.

Equivalence:

- `utils/errors.py` pair → shared: bodies byte-identical; the only signature delta
  (keyword-only `fallback` → positional-or-keyword) is a pure widening and every call site uses
  keyword form or the default. `_unprintable` output identical. Equivalent on all inputs.
- `types/converters.py` local → shared: identical on every input class except hostile ``str``
  subclasses (old raised into the placeholder; new reads base content). Strictly safer, adopts the
  convention `utils/errors.py` already carried (the recorded drift), and pinned at the owner by
  `test_safe_text_is_the_shared_str_renderer`. No caller depends on the old divergent behavior:
  `_field_label` output feeds `ConfigurationError` prose, where truthful content strictly beats a
  placeholder. `_safe_arg_repr`'s fallback swap is provably byte-identical.
- Import direction: `exceptions.py` imports only `__future__.annotations`; both consumers already
  imported from `..exceptions` before this change. Layering preserved, no cycle.

Tests: `tests/test_exceptions.py` is the right package tier — the wiring assertions
(`_errors_module._safe_text is _safe_text`, converters counterpart) are structural facts
unobservable through live GraphQL, so no stronger tier exists for them; behavior of the shared body
stays covered by the pre-existing hostile pins in `tests/utils/test_errors.py` and
`tests/types/test_converters.py` (both re-read: they exercise strip and degrade through the real
envelope/converter paths now hitting the shared body). A re-grown local copy fails the identity
assertions; weakening the strip fails the `_HostileStrStr` pin. Nit, non-blocking:
`_errors_module._unprintable` is pinned via `__module__` rather than identity — still catches
regrowth.

Independent twin sweep beyond Worker 1's search: grepped every `str.__str__` normalizer in the
package (~15 further sites) and probed each — `strings._plain_text` (raises on non-str),
`write_transaction._sql_statement_token` (may raise; no fallback/degrade),
`querysets._normalized_str` (pure normalizer), `write_values`/`input_values`/`imports`
normalizers (no degrade path). None shares the never-raise + fallback + degrade contract; the
consolidation missed nothing.

Rejected candidates re-probed: `querysets._safe_class_name` divergence is real (non-string
`__name__` degrades to the metaclass label there vs repr dispatch in the shared renderer;
documented on both sides) — merging would need a mode flag, rejection stands. The
`describe_value` fragment grammar serves 17 mid-prose call sites vs the standalone placeholder —
stands. The `describe_value` scope fix was factually checked against grep: `error_policy.py`,
`resource_policy.py`, `extensions/debug.py` all route through it.

Matrix discharged independently: mirroring searched (64 importers + the twin sweep above);
async twins inapplicable (zero await surface in the target; translation seam single-path);
derived knowledge — the ~30 raw type-label derivations are real (grep-confirmed across flavors)
and correctly fenced to a dedicated sweep while several host files are concurrently dirty;
round-trip pairs colocated with fidelity tests at `test_path_resolution_error_pickle_and_copy_fidelity`
/ `test_lookup_validation_error_pickle_and_copy_fidelity`; media contracts inventoried with the one
live drift fixed. Single-edit-site recount: posited respelling of `<unprintable {T}>` forces
exactly 2 executable sites (`_unprintable` + the `__str__` inline branch), both in
`exceptions.py`; posited hardening extension forces 1 (`_safe_text`). Both claims hold. Pytest
remains deferred per repository rules.
