# DRY review: `django_strawberry_framework/error_policy.py`

Status: verified

## System trace

The target owns the **policy object** half of the production error policy: the frozen
three-field `ErrorPolicy` (`enabled` / `message` / `correlation_extension_key`) whose
`__post_init__` is the single validation gate for every construction path;
`DEFAULT_ERROR_POLICY`, the fail-closed-by-doing-nothing instance derived from those
field defaults; `resolve_error_policy`, the once-at-schema-construction precedence
ladder (`DjangoSchema(error_policy=...)` argument > `DJANGO_STRAWBERRY_FRAMEWORK
["ERROR_POLICY"]` mapping via `conf.py::error_policy_setting()` — a thin reader that
validates nothing > package defaults), which derives its valid vocabulary from
`fields(ErrorPolicy)` rather than restating it; and `new_correlation_id`, the sole
minter of the per-masked-error `uuid4().hex`.

Consumers, traced end to end: `schema.py::DjangoSchema.__init__` calls
`resolve_error_policy` once, exposes the result as `schema.error_policy`, and PREPENDS
`DjangoErrorPolicyExtension` through `_with_error_policy_extension` unless the consumer
supplied their own entry (class/instance matched by the shared `_extension_entry_matches`;
`get_extensions` later drops only a duplicate produced by an opaque factory).
`extensions/error_policy.py` is the ONE place the rule is enforced: `_is_unexpected`
(structural classifier), `_masked` (replacement + the single log-pairing site),
`_degraded` (fail-closed floor), `masking_is_active` (per-operation exact-bool `DEBUG`
gate), `is_maskable_result` (shape gate), `mask_execution_result`, and
`schema_error_policy` (isinstance-gated read). It is applied at exactly two seams that
share those helpers and restate nothing: the extension's `on_operation` teardown
(queries/mutations) and `consumers.py::_stop_aware_results` (per-event subscription /
streamed frames). `__init__.py` root-exports `DEFAULT_ERROR_POLICY`, `ErrorPolicy`,
and `DjangoErrorPolicyExtension`. Tests: `tests/test_error_policy.py` (construction,
precedence ladder, correlation-id format, install position, standalone fallback,
degrades), `examples/fakeshop/test_query/test_error_policy_api.py` (live `/graphql/`
category matrix), `tests/test_routers.py` (subscription-frame masking rows),
`tests/base/test_init.py` (export gate). Standing prose: GLOSSARY entries
(`ErrorPolicy`, Production error policy, Structural error classification, Correlation
identifier, `DjangoErrorPolicyExtension`, Masking-extension ordering),
`docs/README.md`'s "Production error policy" section + feature-table row, SECURITY.md,
spec-048, TREE.md taglines.

Lockstep surfaces: renaming any exported symbol sweeps `::OldName` references across
schema/consumers/tests/docs; changing the classification rule moves `_is_unexpected`
plus the prose/test media that pin it (counted under axis 5); adding an option moves
only the dataclass + its docs/tests (resolution derives from `fields()`).

## Verification

Axis 1 — cross-flavor policy mirroring (searched). The sibling flavor of the target's
concern is `resource_policy.py`: `resolve_resource_policy` is a near-token twin of
`resolve_error_policy` (same five-step ladder), just as `resource_policy_setting()`
mirrors `error_policy_setting()` in `conf.py` and `_with_resource_policy_extension`
mirrors `_with_error_policy_extension` in `schema.py` (append vs prepend). DISPROVED as
duplication: each resolver's type check, setting reader, default constant, and noun
vocabulary ("option(s)" vs "bound(s)") are self-owned; domain validation lives in each
dataclass's own `__post_init__` (the resolver delegates by constructing); the two
policies shipped under different specs (047 / 048) with independent change axes; the
GLOSSARY `ErrorPolicy` entry pins the mirroring itself as the idiom ("a future third
policy has an obvious shape"). A generic engine needs ~5 parameters (cls, default,
reader, singular/plural nouns) — mode-flag territory per DRY.md ground rules.
Single-edit test: "add option X to `ErrorPolicy`" forces **1** production site, because
`known = {field.name for field in fields(ErrorPolicy)}` derives the vocabulary.
Second mirror probed: the real-bool security-switch rule appears at
`ErrorPolicy.__post_init__` (`enabled`), `DjangoDebugExtension.__init__`
(`allow_unsafe_production`), and the two runtime gates `masking_is_active` /
`debug.py::_disclosure_permitted` — different fields, messages, and compositions
(`enabled AND not-debug` vs `ack OR debug`) governing different disclosures; merged
they would couple two independently-evolving spec-048 deliverables. REJECTED.

Axis 2 — sync and async twins (searched, ruled out). `grep -n "async def\|await"` over
both target modules: zero hits. Package-wide search for mask/classify/unexpected
definitions finds the masking implementation exactly once, synchronous
(`extensions/error_policy.py:76-274`); the teardown is one synchronous generator the
engine enters on both execution colors, and the async per-event seam
(`consumers.py:1010-1011`) calls the same sync `mask_execution_result` /
`is_maskable_result` / `masking_is_active` rather than re-deriving them. Sync/async
parity is additionally pinned end-to-end by
`examples/fakeshop/test_query/test_error_policy_api.py::test_the_sync_and_async_transports_produce_the_same_masked_entry`.
No color-specific branch exists anywhere on this surface.

Axis 3 — derived rather than repeated knowledge (searched; one hit, fixed). Clean
sites: the valid-option vocabulary derives from `fields(ErrorPolicy)`;
`DEFAULT_ERROR_POLICY` derives from the dataclass defaults; the correlation id is
minted at one site (`new_correlation_id`) and logged at one site (`_masked`); the
degrade floors construct from the passed-in policy. FOUND: the package-default masked
message literal `"An unexpected error occurred."` was spelled TWICE in production —
`error_policy.py:81` (the owner, the dataclass default behind `DEFAULT_ERROR_POLICY`)
and `extensions/error_policy.py:163` (`_degraded`'s `getattr(policy, "message", ...)`
fallback). Posited change "reword the default masked message" forced **2** production
sites; worse, drift would be SILENT, because the fallback arm is unreachable for every
admitted policy — `schema_error_policy` isinstance-gates to real `ErrorPolicy`
instances or `DEFAULT_ERROR_POLICY`, whose `message` `__post_init__` guarantees a
non-empty string. Became the finding below.

Axis 4 — inverse and round-trip pairs (ruled inapplicable). `grep` for
`asdict|to_mapping|export|serialize` across `error_policy.py`,
`extensions/error_policy.py`, and `resource_policy.py`: zero hits. Resolution is
one-way (mapping → validated frozen instance); nothing serializes, exports, or parses
a policy back out anywhere in the package, so there is no grammar split across an
encode/decode pair on this target's surface.

Axis 5 — contracts restated in another medium (searched; counted, no drift). The
classification + wire contract is held in: production code (`_is_unexpected`,
`_masked`), two module docstrings, six GLOSSARY entries, `docs/README.md`'s
production-error-policy section and feature-table row, SECURITY.md's disclosure
paragraphs, spec-048 (Decisions 7–11), and three test tiers (unit matrix, live HTTP
matrix including the parse/validation/deliberate/completion rows, router subscription
rows). Posited change "also mask a `GraphQLError` whose `original_error` is `None`"
would force 1 production site + ≥2 test trees + ≥3 standing docs + the spec archive.
That spread is documentation doing its job, not consolidatable duplication — the DRY
requirement it produces is that exactly ONE production statement of the rule exists,
which holds. Spot-checked the GLOSSARY "Structural error classification" entry against
present-day `_is_unexpected`: they agree (shape-keyed, `None` → untouched,
`GraphQLError` original → untouched, else masked); no medium diverges from the code.

Single-edit-site counts (posited changes):
- "Add an `ErrorPolicy` option" → `error_policy.py` only (+ its own tests/docs): **1**
  production site.
- "Reword the default masked message" → **2** production sites before this review's
  fix (`error_policy.py:81`, `extensions/error_policy.py:163`); **1** after.
- "Change what counts as unexpected" → `_is_unexpected` only: **1**.
- "Change where the automatic extension installs" → `_with_error_policy_extension`
  only (**1**); suppression matching is already shared through
  `_extension_entry_matches`.
- "Change how correlation ids are minted" → `new_correlation_id` only: **1**.

Strongest rejected candidates:
1. Unifying `resolve_error_policy` / `resolve_resource_policy` into a parameterized
   engine — rejected on the axis-1 evidence above: self-owned vocabularies and
   validation, per-spec change axes, 5-parameter mode-flag shape, and the mirroring
   pinned as the package idiom; the ladder is stable and each module stays cohesive
   (policy object + resolution + reader in one file).
2. Merging `masking_is_active` with `debug.py::_disclosure_permitted` behind one
   "is production" predicate — opposite questions, different composition, different
   opt-outs (`policy.enabled` vs `allow_unsafe_production`), each documented with its
   own fail-closed reasoning and pinned by its own malformed-DEBUG rows
   (`test_a_malformed_debug_setting_does_not_disable_production_masking`; the debug
   suite's equivalents). A shared predicate would couple two disclosures that fail in
   different directions for different reasons.
3. Merging `_with_error_policy_extension` / `_with_resource_policy_extension` behind a
   position flag — the prepend-vs-append positions ARE the contract
   (`test_the_error_policy_extension_is_installed_at_index_zero` asserts both
   directions so a tidying refactor fails loud); a flag would hide the lifecycle rule
   the test exists to protect. The genuinely shared part (entry matching without
   invoking factories) is already factored into `_extension_entry_matches`.

Scratch experiments: none needed — every uncertain point (fallback reachability,
import graph, seam sharing) was settled by reading the admitted-shape paths in
`schema_error_policy` / `_policy()` / `on_operation` and the import lines of the three
modules involved.

## Opportunities

### 1. The package-default masked message was restated as a literal at its enforcement site

- **Repeated responsibility:** the default floor message string — one fact owned by
  `ErrorPolicy`'s field default, restated inside the module that applies the policy.
- **Sites:** `django_strawberry_framework/error_policy.py:81` (owner; the dataclass
  default behind `DEFAULT_ERROR_POLICY`) and
  `django_strawberry_framework/extensions/error_policy.py:163` (`_degraded`'s
  `getattr(policy, "message", ...)` fallback).
- **Evidence:** posited change "reword the default masked message" forces both sites
  (count 2); the second is unreachable for every admitted policy
  (`schema_error_policy` admits only real `ErrorPolicy` instances or
  `DEFAULT_ERROR_POLICY`, and `__post_init__` guarantees a non-empty string), so a
  drifted copy could never be caught by a request — pure axis-3 duplication with no
  natural drift detector.
- **Owner:** `error_policy.py` — the dataclass default / `DEFAULT_ERROR_POLICY`.
- **Consolidation:** `_degraded` now falls back to `DEFAULT_ERROR_POLICY.message`
  instead of a second literal. The extension module already imported
  `DEFAULT_ERROR_POLICY` for three other uses, so no import-graph change; the
  `getattr` default argument evaluates eagerly either way, so execution and coverage
  are unchanged and the floor still answers even if handed something policy-shaped
  that lost its message.
- **Proof:** the existing degrade rows pin equality with the owner —
  `tests/test_error_policy.py::test_one_error_that_cannot_be_masked_degrades_to_the_policy_message`
  and `::test_a_result_whose_errors_cannot_be_read_degrades_to_one_policy_message`
  exercise `_degraded` and assert the message equals `DEFAULT_ERROR_POLICY.message`,
  keeping the changed line executed under the 100% gate.
- **Risks / non-goals:** prose that QUOTES the message verbatim (GLOSSARY, README,
  spec examples, docstrings) intentionally restates it as documentation and stays;
  tests asserting the literal do so through `DEFAULT_ERROR_POLICY.message` and follow
  the owner.

## Implementation (Worker 1)

- `django_strawberry_framework/extensions/error_policy.py::_degraded`: replaced the
  duplicated `"An unexpected error occurred."` fallback literal with
  `DEFAULT_ERROR_POLICY.message`, making `error_policy.py` the single production
  spelling of the package-default message.
- No symbols removed; orphan-import sweep not applicable. Tests were already placed at
  the required tiers and needed no addition (see Proof above).
- `uv run ruff format .` + `uv run ruff check --fix .`: clean ("All checks passed!").
- pytest DEFERRED per AGENTS.md (no run without explicit maintainer authorization).

## Judgment

This target sits at the head of a deliberately three-way split — policy object
(`error_policy.py`), response-side enforcement (`extensions/error_policy.py`),
transport application seams (`schema.py` install, `consumers.py` per-event) — and the
split is clean: every rule (classification, replacement, floor, correlation minting,
log pairing, DEBUG gating, shape gating, install position) has exactly one production
statement, and the two application seams share the enforcement module's helpers rather
than restating anything. The one true repetition found was small and quiet: the
package-default message spelled a second time inside an unreachable fallback arm, now
re-pointed to its owner. The resource-policy "structural twin" was examined hardest
and rejected with evidence — it is mirrored idiom with self-owned vocabularies and
validation, not drift bait; a change to either policy still forces exactly one
production site to move.

## Independent verification (Worker 2)

Scope of the cycle diff (baseline `dc5aa6a`): exactly one line —
`extensions/error_policy.py::_degraded` swapped its fallback literal for
`DEFAULT_ERROR_POLICY.message`; `error_policy.py` untouched. Independently
re-traced every path that reaches `_degraded`:

- Extension seam: all four call sites (`mask_execution_result`,
  `_replacement_for`, `_process_result`, the teardown's outer handler) receive
  the policy from `self._policy()` → `schema_error_policy`, which admits only
  `isinstance(policy, ErrorPolicy)` instances or `DEFAULT_ERROR_POLICY`.
- Consumer seam: `consumers.py::_stop_aware_results` resolves through the same
  `schema_error_policy` before calling `mask_execution_result`.

**Degraded-floor semantics proved equivalent.** Every admitted policy is a real
frozen `ErrorPolicy` whose `message` attribute exists and passed `__post_init__`
(non-empty str), so the `getattr` default is never SELECTED on any reachable
path — including a deployment with a custom message, whose degrade answers the
CONFIGURED policy's message both before and after the fix. The default is only
the guard for an out-of-contract object, and even there the two expressions
evaluate to the identical string (`DEFAULT_ERROR_POLICY` is `ErrorPolicy()`, so
`.message` IS the former literal). Eager evaluation of the default argument
cannot raise and keeps line 163 executing under the existing degrade rows, so
coverage is unaffected. No reachable state changes behavior.

Pin coverage re-checked repo-wide: the literal survives in production only at
the owner (`error_policy.py:81`). The single test pinning it verbatim asserts
through `DEFAULT_ERROR_POLICY.message` (`tests/test_error_policy.py::test_the_package_default_is_masking_on_with_the_documented_strings`),
and every degrade assertion — unit rows plus both live HTTP rows in
`examples/fakeshop/test_query/test_error_policy_api.py` — follows the owner, so
owner vs derived sites remain distinguishable and no test pinned the removed
site.

Rejected candidates re-probed at source, all stand: the two resolvers read in
full (self-owned type checks, setting readers `conf.py::resource_policy_setting`
/ `conf.py::error_policy_setting`, defaults, nouns; validation in each
dataclass's own `__post_init__`; separate spec-047/048 axes); `masking_is_active`
(`enabled AND DEBUG is not True`) vs `debug.py::_disclosure_permitted`
(`allow_unsafe_production OR DEBUG is True`) are opposite questions with
opposite fail directions; `schema.py::_with_error_policy_extension` (prepend)
vs `_with_resource_policy_extension` (append) hold lifecycle positions pinned by
`test_the_error_policy_extension_is_installed_at_index_zero` in both
directions, with the genuinely shared matching already factored into
`_extension_entry_matches`.

Single-edit-site count re-derived independently: posited "reword the default
masked message" forces exactly **1** production site today (`error_policy.py:81`;
grep shows zero other production spellings) versus **2** before the fix. Matrix
discharged on all five axes against the target's real surface. Verdict:
**verified**. pytest deferred per AGENTS.md.
