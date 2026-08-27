# Build: Slice 1 — `Meta.globalid_strategy` net-new key + `RELAY_GLOBALID_STRATEGY` read + the precedence resolver

Spec reference: `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` (`## Slice checklist` Slice 1, lines 56-60;
`## Definition of done` items 2-3, lines 547-548; Decisions 5 / 6 / 7, lines 288-311; `## Implementation plan`
row 1, line 414; `## Test plan` `### Slice 1`, lines 440-447 — all line numbers as read at the start of this
pass, before the spec edits recorded below)
Status: final-accepted

Procedural-closure slice per `docs/builder/BUILD.md` `### Procedural-closure slices`: one Worker 1 pass, a
combined Plan + Final-verification block, no Worker 2 and no Worker 3. The authorizing clause is
`docs/builder/build-031-globalid_encoding-0_0_9.md` `## Dispatch rule for this cycle` — "**Empty CODE GAP
list** -> the slice closes by procedural closure" — and the CODE GAP audit below is empty.

This is a **residual reconciliation** cycle over already-shipped work (`DONE-031-0.0.9`), not a feature build.
Nothing in this pass writes source or tests. Where the shipped code and the spec disagreed, the code is the
truth and the spec was rewritten to state the current contract directly; the reasoning behind each change is
appended to `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md`, which is the only place this
cycle's chronology is allowed to live.

## Plan (Worker 1)

### Working-tree baseline (re-read at the start of this pass)

`git status --short` at HEAD `5ebcfe9c`:

- ` M docs/SPECS/spec-031-globalid_encoding-0_0_9.md` — this cycle's own Slice-0 output
- `?? docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md` — this cycle's own Slice-0 output
- `?? docs/builder/bld-031-slice-0-rationale_extraction.md` — this cycle's own artifact
- `?? docs/builder/build-031-globalid_encoding-0_0_9.md` — this cycle's own build plan

The build plan's `### Concurrent work` list (`consumers.py`, `utils/sessions.py`, `db.sqlite3`,
`tests/test_consumers.py`) **has moved**: the concurrent session committed that work as `0e5044da` /
`5ebcfe9c`, so none of the four is dirty any more. Nothing outside this cycle's own files is dirty, so this
pass had no `AGENTS.md` rule-34 exclusions to respect beyond leaving the committed work alone.

### DRY analysis

- **Helper inventory checked.** Refreshed package-wide (`django_strawberry_framework/`, not just `utils/`) into
  `docs/shadow/helper-inventory.md` — 1,953 lines. Shapes searched: `globalid`, `strategy`, `snapshot`,
  `validate_callable`, `async_callable`. Relevant existing candidates, all already the shipped Slice-1 surface:
  `conf.py::relay_globalid_strategy_setting`, `types/base.py::_validate_globalid_strategy` /
  `::_validate_globalid_callable`, `types/relay.py::_validated_globalid_setting` /
  `::_resolve_globalid_strategy`, `utils/typing.py::is_async_callable`. **No new helper is proposed** — this
  pass writes no code — so the inventory served only to confirm that no second copy of the strategy-validation
  or setting-read shape exists anywhere in the package.
- **Existing patterns reused.** None newly; the audit confirms the shipped code already reuses the intended
  ones: `_validate_globalid_strategy` is structurally modeled on `types/base.py::_validate_connection` and
  shares its Relay-Node gate text through `_RELAY_NODE_GATE_LEAD` / `_RELAY_NODE_GATE_INHERIT_TAIL`; the
  strategy vocabulary is single-sourced through `STRING_GLOBALID_STRATEGIES` / `DEFAULT_GLOBALID_STRATEGY`;
  the sync-ness probe delegates to the package-wide `utils/typing.py::is_async_callable` rather than a local
  `inspect.iscoroutinefunction`.
- **New helpers justified.** None. This pass produces two `.md` edits and one artifact.
- **Duplication risk avoided.** The one duplication risk this slice could carry is the strategy string set or
  the settings key being re-typed at a second site. Both are already constants
  (`STRING_GLOBALID_STRATEGIES`, `DEFAULT_GLOBALID_STRATEGY`, `conf.py::RELAY_GLOBALID_STRATEGY_KEY`), and the
  spec now names them so a future reader is pointed at the source rather than at a literal to copy.

### `scripts/review_inspect.py`

**Skipped, with reason.** `docs/builder/BUILD.md` `### When to run the helper during build` requires it when
the plan *adds logic* to an existing 150+-line `.py` file or to anything under `types/` / `optimizer/`. This
plan adds no logic to any `.py` file — the maintainer's fence forbids Worker 1 from editing source or tests in
any cycle, and the CODE GAP audit came back empty, so no Worker 2 pass will either. The package-wide AST
inventory above covers the read-only structural need this pass actually had.

### Implementation steps

No source implementation steps: the CODE GAP audit is empty, so this slice ships no code. The pass's own steps
were:

1. Enumerate every surface Slice 1 contracts from the spec's `## Slice checklist` Slice 1, DoD items 2-3,
   Decisions 5 / 6 / 7, `## Implementation plan` row 1, and `## Test plan` `### Slice 1`.
2. Prove each one at HEAD by reading the shipped symbol, not by accepting the pre-verified list — see
   `### CODE GAP audit`.
3. Compare the exact shapes (signatures, arity, ordering, error text, snapshot timing, test names and
   locations) against the spec's claims, and record every divergence.
4. Rewrite the spec to state the current contract directly, and append the reasoning to the rationale
   companion — see `### Spec changes made (Worker 1 only)`.
5. Re-run `check_spec_glossary.py`, the in-page-anchor / link-def resolution check, and the markdown-scaffold
   check over both edited files.

### Test additions / updates

None. No test file is edited, created, or deleted by this pass. The audit's finding about the *location* of two
shipped Slice-1 assertions is a spec correction, not a test move: nothing changed on disk under `tests/`.

### Implementation discretion items

None to delegate — there is no Worker 2 pass. The two judgement calls this pass made itself, both assessed
rather than deferred:

- Whether the four shipped-but-unnamed Slice-1 tests should be contracted by the spec or left unowned. Decided:
  **contract all of them** (see the audit's divergence D5) — each pins a consequence a Decision already states,
  so naming them costs nothing and un-owning them invites a future pass to read them as scope creep.
- Whether to move the two finalization-scoped setting tests into `tests/types/test_base.py` to match the spec.
  Decided: **no** — they need a real `finalize_django_types()` run, and `docs/TREE.md`'s one-to-one mirror rule
  puts a finalization behavior in the mirror of the module that performs it. The spec was wrong, not the tests.
  (Moving them would be a source edit and outside the fence in any case.)

### Boundary count

**Zero new boundaries.** This pass introduces no guard, cap, rejection path, or validation branch, so no
failability proof is owed (`docs/builder/BUILD.md` `### What needs a proof, and what does not`). The split
question is answered: the slice is one unit because it produces no diff under `django_strawberry_framework/`
or `tests/` at all.

### Hot-path declaration

`none`. Confirmed rather than inherited: the empty CODE GAP list means no Worker 2 pass is dispatched, so
neither the `resolve_typename` install closure (per-node `id` resolution) nor
`filters/base.py::_decode_and_validate_global_id` (per filter value) is touched by this slice. Had the audit
found a gap, the plan preamble's re-declaration clause would have applied.

### Floor-verification scope

`none`. Same reason: `types/base.py`, `types/relay.py`, `types/finalizer.py`, and `filters/base.py` are
Strawberry type-construction seams, but this slice lands no change in any of them. Nothing is executed at the
floor, and nothing is claimed about it. The shared `.venv`'s own versions are deliberately not stated — this
pass had no reason to read them, and `docs/builder/BUILD.md` `## Floor verification` forbids stating them from
memory.

### Ownership partition

`none; sequential slices` (inherited from the build plan, and unchanged: this slice writes one spec file the
later slices also write).

### Spec slice checklist (verbatim)

The spec's nested Slice-1 sub-bullets from `## Slice checklist`, copied verbatim. **Copied post-edit**: the
edits this same pass made are recorded under `### Spec changes made (Worker 1 only)`, and the boxes are audited
against HEAD, so the checklist reads as the contract the shipped code was proven against rather than as a
superseded one.

- [x] Slice 1: `Meta.globalid_strategy` net-new key (validated + stored on the definition) + `RELAY_GLOBALID_STRATEGY` settings read + the precedence resolver (per [Decision 5](#decision-5--precedence-metaglobalid_strategy--relay_globalid_strategy--package-default-model) / [Decision 6](#decision-6--metaglobalid_strategy-is-a-net-new-allowed_meta_keys-key-stored-on-the-definition) / [Decision 7](#decision-7--the-relay_globalid_strategy-setting-and-the-settings-key-discipline))
  - [x] [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] grows `"globalid_strategy"` (net-new public key — NOT a [`DEFERRED_META_KEYS`][base] promotion, mirroring [`spec-030`][spec-030] [Decision 8][spec-030] and [`spec-029`][spec-029] [Decision 6][spec-029]). A `_validate_globalid_strategy` helper (called from [`_validate_meta`][base], structurally modeled on `_validate_connection`) accepts `"model"` / `"type"` / `"type+model"` or a callable; an unknown string or wrong type raises [`ConfigurationError`][glossary-configurationerror]; a callable is **validated for arity and sync-ness** via `inspect.signature` (must accept the three positional `_GLOBALID_CALLABLE_PARAMS`, `(type_cls, model, root)`) and the shared [`utils/typing.py::is_async_callable`][relay-utils-typing] guard (via `_validate_globalid_callable`; must be sync), so a wrong-arity or `async def` encoder fails at type creation rather than as a raw `TypeError` / coroutine per request, and a callable the inspection itself cannot read (a `__signature__` or `__call__` descriptor that raises) is contained into the same [`ConfigurationError`][glossary-configurationerror] rather than leaking the descriptor's exception; the key is gated to a Relay-Node-shaped type via the precomputed `relay_shaped` bool (`_is_relay_shaped(cls, interfaces)`). The valid string vocabulary and the package default are the named constants [`STRING_GLOBALID_STRATEGIES`][base] / [`DEFAULT_GLOBALID_STRATEGY`][base] in [`types/base.py`][base] — the single source the validator's typo-guard text, the precedence resolver, the encoder, and the decode-shape enforcement all read.
  - [x] The normalized value is **stored on [`DjangoTypeDefinition`][definition]** (a new `globalid_strategy` slot, populated in [`__init_subclass__`][base] like the `connection` / `filterset_class` / `orderset_class` slots) so the Phase-2.5 injection reads the per-type opt-in from the definition, not by re-parsing `Meta`.
  - [x] `_validated_globalid_setting()` reads the schema-wide setting through [`conf.py::relay_globalid_strategy_setting()`][conf] (a `getattr(settings, "RELAY_GLOBALID_STRATEGY", None)` helper delivering "absent → package default", NOT a bare `conf.settings.RELAY_GLOBALID_STRATEGY` access, which raises `AttributeError` on the missing key) and validates it through the **same** `_validate_globalid_strategy(None, value, relay_shaped=True, source="setting")` rule the `Meta` path uses (unknown string, wrong-arity callable, or `async def` callable → [`ConfigurationError`][glossary-configurationerror] naming `RELAY_GLOBALID_STRATEGY`), since [`conf.py`][conf] is a thin reader that does not validate domain values. The finalizer snapshots the validated result on `registry._globalid_setting_snapshot` **unconditionally before the Relay loop** (so an invalid setting raises even with zero Relay types / all-override) and passes it into `install_globalid_typename_resolver`; the slot starts at the [`registry.py::GLOBALID_SETTING_UNSET`][registry] sentinel so "not yet computed" is distinguishable from a computed `None` (the absent-setting result), which is what makes the retry comparison exact; a mid-lifecycle setting change on a finalization retry raises [`ConfigurationError`][glossary-configurationerror] naming `registry.clear()` (which resets the slot to the sentinel). The pure two-arg `_resolve_globalid_strategy(definition, globalid_setting)` then applies the precedence — `definition.globalid_strategy` (the `Meta` override) → the passed-in `globalid_setting` snapshot → the `"model"` package default — reading no setting and validating nothing.
  - [x] Package coverage: [`tests/types/test_base.py`][test-types-base] gains the `"globalid_strategy"`-in-`ALLOWED_META_KEYS` / not-in-`DEFERRED_META_KEYS` assertion, the `_validate_globalid_strategy` failure modes (unknown string, non-Relay type, wrong type, **callable wrong-arity — the dropped-`info` four-arg shape included — `async def` callable in all three spellings, and an un-inspectable callable**), the `definition.globalid_strategy` storage assertion for both a set and an absent key, and the three-tier precedence of the pure two-arg resolver. The **finalization-scoped** setting assertions — the unconditional unknown-setting `ConfigurationError` and the mid-lifecycle-change retry rejection — need a real `finalize_django_types()` run and therefore live beside the install step in [`tests/types/test_relay_interfaces.py`][test-relay-interfaces].

Every box is ticked because every contract landed at ship time; the per-box evidence is the CODE GAP audit
below. No box is deferred.

## CODE GAP audit

**Verdict: the CODE GAP list is EMPTY.** Every surface Slice 1 contracts exists at HEAD `5ebcfe9c`, and every
shape claim the spec makes about it — signature, arity, purity, snapshot timing, sentinel handling — holds.
Nothing the spec planned for Slice 1 was skipped, dropped, or forgotten. Stating that explicitly rather than
leaving it implied: **no CODE GAP was found, and no Worker 2 dispatch is owed for this slice.**

Worker 0's pre-verified list was treated as a claim and re-derived symbol by symbol
(`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`); every row below was
read in the shipped source during this pass.

### Contracted surfaces (source)

| Contracted surface | Verdict | Evidence at HEAD |
| --- | --- | --- |
| `"globalid_strategy"` in `ALLOWED_META_KEYS` | PRESENT | `django_strawberry_framework/types/base.py::ALLOWED_META_KEYS` — the frozenset literal carries `"globalid_strategy"` |
| Not in `DEFERRED_META_KEYS` | PRESENT | `django_strawberry_framework/types/base.py::DEFERRED_META_KEYS` — exactly `{"aggregate_class", "fields_class", "search_fields"}` |
| `STRING_GLOBALID_STRATEGIES` | PRESENT | `django_strawberry_framework/types/base.py::STRING_GLOBALID_STRATEGIES` — `frozenset({"model", "type", "type+model"})` |
| `DEFAULT_GLOBALID_STRATEGY` | PRESENT | `django_strawberry_framework/types/base.py::DEFAULT_GLOBALID_STRATEGY` — `"model"` |
| `_GLOBALID_CALLABLE_PARAMS` | PRESENT | `django_strawberry_framework/types/base.py::_GLOBALID_CALLABLE_PARAMS` — `("type_cls", "model", "root")` |
| `_validate_globalid_strategy` with the spec's exact signature | PRESENT, shape matches | `django_strawberry_framework/types/base.py::_validate_globalid_strategy` — `(meta, value, relay_shaped, *, source="meta")`, byte-for-byte the spec's `(meta, value, relay_shaped, *, source="meta")` |
| …called from `_validate_meta` | PRESENT | `django_strawberry_framework/types/base.py::_validate_meta` #"globalid_strategy = _validate_globalid_strategy(" — called positionally with `(meta, getattr(meta, "globalid_strategy", None), relay_shaped)`, so the `Meta` path takes the `source="meta"` default |
| …Relay-Node gate on the precomputed `relay_shaped` | PRESENT | `django_strawberry_framework/types/base.py::_validate_meta` #"relay_shaped = _is_relay_shaped(cls, interfaces)" feeds the same bool to `_validate_connection`, `_validate_cursor_field`, `_validate_globalid_strategy`, `_validate_relation_shapes` |
| `_validate_globalid_callable` (arity + sync-ness) | PRESENT | `django_strawberry_framework/types/base.py::_validate_globalid_callable` — `is_async_callable(value)` then `inspect.signature(value).bind(*_GLOBALID_CALLABLE_PARAMS)` |
| The `__init_subclass__` store | PRESENT | `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` #"globalid_strategy=validated.globalid_strategy" — threaded into the `DjangoTypeDefinition(...)` construction alongside `connection` / `filterset_class` / `orderset_class` |
| `DjangoTypeDefinition.globalid_strategy` slot | PRESENT | `django_strawberry_framework/types/definition.py::DjangoTypeDefinition` #"globalid_strategy: str | Callable[..., str] | None = None" |
| `conf.py::RELAY_GLOBALID_STRATEGY_KEY` | PRESENT | `django_strawberry_framework/conf.py::RELAY_GLOBALID_STRATEGY_KEY` — `"RELAY_GLOBALID_STRATEGY"` |
| `conf.py::relay_globalid_strategy_setting()` | PRESENT, thin reader | `django_strawberry_framework/conf.py::relay_globalid_strategy_setting` — a single `getattr(settings, RELAY_GLOBALID_STRATEGY_KEY, None)`; no domain validation, as Decision 7 requires |
| `registry.GLOBALID_SETTING_UNSET` | PRESENT | `django_strawberry_framework/registry.py::GLOBALID_SETTING_UNSET` — a module-level `object()` sentinel |
| `registry._globalid_setting_snapshot` | PRESENT | `django_strawberry_framework/registry.py::TypeRegistry.__init__` #"self._globalid_setting_snapshot: Any = GLOBALID_SETTING_UNSET" |
| …its reset in `clear()` | PRESENT | `django_strawberry_framework/registry.py::TypeRegistry.clear` #"self._globalid_setting_snapshot = GLOBALID_SETTING_UNSET" — resets to the sentinel, not to `None` |
| `types/relay.py::_validated_globalid_setting()` | PRESENT, routes as specified | `django_strawberry_framework/types/relay.py::_validated_globalid_setting` — reads `conf.relay_globalid_strategy_setting()`, short-circuits `None`, else `_validate_globalid_strategy(None, setting, relay_shaped=True, source="setting")` |
| `types/relay.py::_resolve_globalid_strategy(...)` **pure two-arg** | PRESENT, claim holds | `django_strawberry_framework/types/relay.py::_resolve_globalid_strategy` — `(definition, globalid_setting)`; the body is three returns (`definition.globalid_strategy` / `globalid_setting` / `DEFAULT_GLOBALID_STRATEGY`). It reads no setting and calls no validator — verified by reading the whole body, not by trusting the docstring |
| Snapshot computed **unconditionally before the Relay loop** (Rev-7 delta (a)) | PRESENT, claim holds — and stronger than stated | `django_strawberry_framework/types/finalizer.py::finalize_django_types` #"current_globalid_setting = _validated_globalid_setting()" sits after the `registry.is_finalized()` entry guard and **before `_audit_primary_ambiguity`**, i.e. before Phase 1, well before the Phase-2.5 Relay loop at #"install_globalid_typename_resolver(". It is unconditional — no Relay-type count, no per-type branch guards it |
| The snapshot is threaded into the install step | PRESENT | `django_strawberry_framework/types/finalizer.py::finalize_django_types` #"registry._globalid_setting_snapshot," passed as the third argument to `install_globalid_typename_resolver` |
| Mid-lifecycle-change rejection naming `registry.clear()` | PRESENT | `django_strawberry_framework/types/finalizer.py::finalize_django_types` #"RELAY_GLOBALID_STRATEGY changed between finalization attempts" — the message ends "Call registry.clear() first, then rebuild under the new value." |

### Contracted surfaces (`## Test plan` Slice 1)

Every test the Slice-1 test list names exists and asserts what the spec says it asserts. Two of them are
recorded here with the divergence they carry.

| Spec-named test | Verdict | Evidence at HEAD |
| --- | --- | --- |
| `test_meta_globalid_strategy_in_allowed_meta_keys` | PRESENT, asserts as specified | `tests/types/test_base.py::test_meta_globalid_strategy_in_allowed_meta_keys` — asserts both the `in ALLOWED_META_KEYS` and the `not in DEFERRED_META_KEYS` halves |
| `test_meta_globalid_strategy_unknown_string_raises` | PRESENT | `tests/types/test_base.py::test_meta_globalid_strategy_unknown_string_raises` — `globalid_strategy = "modle"`, matches `"unknown strategy"` |
| `..._non_relay_type_raises` | PRESENT | `tests/types/test_base.py::test_meta_globalid_strategy_non_relay_type_raises` — no `interfaces`, matches `"relay.Node"` |
| `..._wrong_type_raises` | PRESENT | `tests/types/test_base.py::test_meta_globalid_strategy_wrong_type_raises` — `globalid_strategy = 42`, matches `"must be one of"` |
| `test_meta_globalid_strategy_callable_accepted` | PRESENT under a **wider name** | `tests/types/test_base.py::test_meta_globalid_strategy_callable_accepted_and_stored` — accepts a three-arg encoder AND asserts `definition.globalid_strategy is encode`. Divergence D4 |
| `..._callable_wrong_arity_raises` | PRESENT | `tests/types/test_base.py::test_meta_globalid_strategy_callable_wrong_arity_raises` — a two-arg encoder, matches the `(type_cls, model, root)` shape text |
| `..._async_callable_raises` | PRESENT | `tests/types/test_base.py::test_meta_globalid_strategy_async_callable_raises` — an `async def` encoder, matches `"must be sync"` |
| `test_meta_globalid_strategy_stored_on_definition` | PRESENT | `tests/types/test_base.py::test_meta_globalid_strategy_stored_on_definition` — asserts `definition.globalid_strategy == "model"` |
| `test_resolve_globalid_strategy_precedence` — the three tiers | PRESENT, asserts all three | `tests/types/test_base.py::test_resolve_globalid_strategy_precedence` — `Meta` beats the snapshot, the snapshot beats the default, and `(no_meta_def, None) == "model"` |
| …the unknown-setting `ConfigurationError` naming the setting | PRESENT in the same test | same node — `settings.DJANGO_STRAWBERRY_FRAMEWORK = {"RELAY_GLOBALID_STRATEGY": "nonsense"}` then `pytest.raises(ConfigurationError, match="RELAY_GLOBALID_STRATEGY")` |
| …raised **unconditionally at finalization** (zero Relay types / all-override) | PRESENT, in a **different file** | `tests/types/test_relay_interfaces.py::test_invalid_setting_raises_with_zero_relay_types` (parametrized invalid-string / wrong-arity-callable), `::test_invalid_async_callable_setting_raises_with_zero_relay_types`, `::test_invalid_setting_raises_when_only_type_has_resolve_typename_override`. Divergence D4 |
| …the mid-lifecycle change on a retry naming `registry.clear()` | PRESENT, in a **different file** | `tests/types/test_relay_interfaces.py::test_retry_lifecycle_rejects_setting_change_no_mixed_strategy` — drives a real Phase-3 failure, asserts the stamped strategy survives, then asserts `match="changed between finalization attempts"` on the retry and a clean rebuild after `registry.clear()`. Divergence D4 |

### Divergences found (code is the truth; the spec was rewritten)

**D1 — `_validate_globalid_callable` contains its own inspection.** Decision 6 stated only the arity bind and
the `is_async_callable` sync-ness guard. Shipped
`django_strawberry_framework/types/base.py::_validate_globalid_callable` wraps **both** probes in
`except BaseException` arms (beyond the ordinary `(TypeError, ValueError)` arity arm) and re-raises
`ConfigurationError` "could not be inspected", so a `__signature__` property or a `__call__` descriptor that
raises cannot escape `DjangoType.__init_subclass__` untyped. Pinned by
`tests/types/test_base.py::test_globalid_callable_wraps_non_signature_inspection_errors` and
`::test_meta_globalid_callable_hostile_descriptor_is_typed`. Worker-0 pre-verified; **confirmed by reading
both `except` arms and both tests.** Spec now states it.

**D2 — `registry.GLOBALID_SETTING_UNSET` was unnamed.** The spec named `registry._globalid_setting_snapshot`
but never the sentinel that initialises and resets it. Confirmed load-bearing rather than cosmetic: an absent
setting validates to `None`, so a `None`-initialised slot could not distinguish "no snapshot taken yet" from
"snapshot taken, no override configured" — the finalizer's
`if registry._globalid_setting_snapshot is GLOBALID_SETTING_UNSET` branch would re-stamp on every retry and the
mid-lifecycle guard would never fire for a project that added the setting between a failed finalize and its
retry. Worker-0 pre-verified; **confirmed by reading the branch and `clear()`'s reset target.** Spec now names
it at Decision 5, Decision 7, the Slice-1 checklist, the error shapes, and DoD item 3.

**D3 — the non-Relay gate's error text (NEW — not on Worker 0's list).** Decision 6 quoted the message as
ending "…add `relay.Node` to `Meta.interfaces` **or remove the key**". The shipped message is composed from the
shared `types/base.py::_RELAY_NODE_GATE_LEAD` + `::_RELAY_NODE_GATE_INHERIT_TAIL` constants and ends
"…**or inherit `relay.Node` directly.**" — a different remediation, and the correct one, since direct
`relay.Node` inheritance is the second shape `_is_relay_shaped` accepts. The constants are shared with the
`Meta.connection` gate and `testing/relay.py::global_id_for`, so the three gates state the remediation
identically. Spec corrected.

**D4 — two shipped Slice-1 test facts the spec described wrongly (NEW).** (a) `test_meta_globalid_strategy_
callable_accepted` shipped as `..._callable_accepted_and_stored`, folding in the definition-slot assertion.
(b) The Slice-1 Test-plan heading files the whole slice under `tests/types/test_base.py`, but the two
finalization-scoped setting assertions cannot live there — they need a real `finalize_django_types()` run —
and shipped in `tests/types/test_relay_interfaces.py`. The spec's own wording carried the tell
("**unconditionally at finalization**" filed under a unit-test module). Spec corrected at the Slice-1
checklist, plan-table row 1, the Test plan, and DoD item 3; **nothing moved on disk.**

**D5 — six shipped Slice-1 tests with no owning spec sentence.** Treated as findings of the same class as a
missing surface, and decided per case; all six are now contracted because each pins a consequence a Decision
already states:

- `tests/types/test_base.py::test_meta_globalid_strategy_callable_old_four_arg_signature_rejected` — the
  dropped-`info` four-arg encoder is wrong-arity under Decision 4's Rev-7 delta (b). **Contract it.**
- `::test_meta_globalid_strategy_async_callable_object_raises` and
  `::test_meta_globalid_strategy_partial_wrapped_async_callable_raises` — the two spellings Decision 6 already
  names as the reason for preferring `is_async_callable` over `inspect.iscoroutinefunction`. **Contract them.**
- `::test_meta_globalid_strategy_absent_leaves_definition_none` — Decision 6's "`None` (absent) → returns
  `None`" and the slot default the precedence resolver falls through on. **Contract it.**
- `::test_globalid_callable_wraps_non_signature_inspection_errors` and
  `::test_meta_globalid_callable_hostile_descriptor_is_typed` — the tests for D1. **Contract them.**

**D6 — error text renders through `exceptions.py::_safe_arg_repr` (NEW).** The typo-guard and wrong-type
messages name the offending value through the shared containment helper rather than a bare `repr`, so a hostile
`__repr__` cannot escape while the error is being assembled. The spec's "naming the offending value" contract
is unchanged in substance; the mechanism is now named at Decision 6.

**D7 — `conf.py::RELAY_GLOBALID_STRATEGY_KEY` was unnamed (NEW).** The spec spelled the key inline both as the
settings key and as the error subject. The shipped code uses the one constant at both roles —
`types/base.py` imports it, and
`tests/types/test_relay_interfaces.py::test_setting_error_subject_is_the_conf_key` asserts the error subject
*is* `conf.RELAY_GLOBALID_STRATEGY_KEY` rather than a matching string. Spec now names it at Decision 7.

**D8 — the spec-032 borrowing did not alter the `031` surface (Worker-0 item, checked).**
`django_strawberry_framework/types/base.py::RELATION_SHAPE_VALUES` / `::DEFAULT_RELATION_SHAPE` are a parallel
pair whose comment cites the `STRING_GLOBALID_STRATEGIES` / `DEFAULT_GLOBALID_STRATEGY` precedent, and
`_validate_relation_shapes` reuses `_RELAY_NODE_GATE_LEAD` with its **own** tail ("or remove the key.") rather
than the globalid tail. The `031` constants' values, types, and readers are untouched by the borrowing. The one
thing the shared-constant hoist did change on the `031` surface is D3's gate tail, recorded above. **No further
`031` surface change from spec-032.**

## Final verification (Worker 1)

Combined with the plan above per `### Procedural-closure slices`.

- **Spec slice checklist:** every box is `- [x]`, each backed by a row in the CODE GAP audit. No box is
  deferred and none is over-ticked — the ticks assert the contract landed at ship time, which the audit proves
  symbol by symbol.
- **CODE GAP:** empty. No Worker 2 dispatch is owed.
- **DRY check across this slice and prior accepted slices:** Slice 0 moved text; this slice edited two `.md`
  files. No duplication is introduced — the corrections were written once in the spec (contract) and once in
  the rationale companion (reasoning), which is the intended split, not a copy. The rationale bullets state
  *why* and the spec states *what*; neither restates the other.
- **Existing tests:** none run, and none needed — this pass changed no `.py` file, so there is no behavior to
  confirm. Stating that rather than running a pytest invocation whose result could not be attributed to this
  pass.
- **`uv run ruff format .` / `uv run ruff check --fix .`:** deliberately **not run**. `AGENTS.md` rule 16 is the
  standing post-edit command pair, but this pass edited only `.md` files, which ruff neither formats nor lints;
  running them would only churn files owned by other work.
- **Verification commands actually run:**
  - `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-031-globalid_encoding-0_0_9.md` →
    `OK: 31 terms - all have glossary entries and at least one spec link.` (unchanged from the pre-pass
    reading, so no CSV term was orphaned by the edits)
  - In-page anchor + link-def resolution over **both** edited files: missing in-page anchors `[]`, undefined
    refs `[]`, unused defs `[]`, broken def paths `[]`. Two new defs were added to the rationale companion
    (`[registry]`, `[tree]`) because the appended bullets cite them; both resolve on disk.
  - `uv run python scripts/check_trailing_commas.py --check` over both edited files → clean (no output).
- **Fail-open shapes:** none introduced — no code changed. The audit did read for the catalogued shapes in the
  Slice-1 surface and found the opposite posture: D1's un-inspectable-callable containment is a fail-*closed*
  answer to "the check blew up", and D2's sentinel is precisely the fix for a truthiness/absence conflation.
- **Relocation / promotion claims:** none made by this slice.
- **Failability proofs:** not applicable; zero new boundaries.
- **Final status:** `final-accepted`.

### Summary

Slice 1 shipped complete at `DONE-031-0.0.9` and nothing was skipped: every surface the slice contracts —
the `ALLOWED_META_KEYS` entry, the two strategy constants, `_validate_globalid_strategy` at its exact
`(meta, value, relay_shaped, *, source="meta")` signature, `_validate_globalid_callable`, the
`__init_subclass__` store, the `DjangoTypeDefinition.globalid_strategy` slot,
`conf.RELAY_GLOBALID_STRATEGY_KEY` + `relay_globalid_strategy_setting()`, `GLOBALID_SETTING_UNSET` +
`_globalid_setting_snapshot` + its reset in `clear()`, `_validated_globalid_setting()`, the pure two-arg
`_resolve_globalid_strategy`, the unconditional pre-Relay-loop snapshot, and every named test — exists at HEAD
and behaves as contracted. The slice's whole output is spec reconciliation: eight divergences, all of them the
spec being narrower or wrong about shipped behavior rather than the code being wrong.

### Spec changes made (Worker 1 only)

All edits are in `docs/SPECS/spec-031-globalid_encoding-0_0_9.md`, triggered by Slice 1. Line ranges are the
pre-edit positions; the spec never narrates its own history, so each edit states the current contract directly
and the reasoning is appended to the rationale companion.

1. **Slice-1 checklist, first sub-bullet (line 57).** Added the un-inspectable-callable containment clause,
   named `_GLOBALID_CALLABLE_PARAMS`, and named `STRING_GLOBALID_STRATEGIES` / `DEFAULT_GLOBALID_STRATEGY` as
   the vocabulary's single source. Reason: divergences D1 and D6/D7's constant-naming class.
2. **Slice-1 checklist, third sub-bullet (line 59).** Named the `GLOBALID_SETTING_UNSET` sentinel and stated
   why the distinction is what makes the retry comparison exact; `registry.clear()` now correctly described as
   resetting to the sentinel. Reason: divergence D2.
3. **Slice-1 checklist, fourth sub-bullet (line 60).** Rewrote the coverage claim: the extra callable-rejection
   cases, the absent-key storage case, and the split that puts the two finalization-scoped setting assertions
   in `tests/types/test_relay_interfaces.py`. Reason: divergences D4 and D5.
4. **`## User-facing API` → Error shapes (after line 231).** Added an error-shape bullet for an un-inspectable
   callable encoder. Reason: divergence D1.
5. **Error shapes, the mid-lifecycle bullet (line 235).** Named the sentinel in the "already-computed" test.
   Reason: divergence D2.
6. **Decision 5 (line 290).** Added the sentinel paragraph (why `None` cannot serve as the un-stamped state)
   and named `DEFAULT_GLOBALID_STRATEGY` as the tier-3 default. Reason: divergences D2 and D7's constant class.
7. **Decision 6 (lines 296-303).** Four edits: the typo-guard bullet now names the constants and
   `_safe_arg_repr`; the callable bullet now names the four-arg rejection and states the inspection
   containment with its principle ("a validator that cannot read a value has not validated it"); the
   Relay-Node gate bullet now quotes the shipped message and names the shared
   `_RELAY_NODE_GATE_LEAD` / `_RELAY_NODE_GATE_INHERIT_TAIL` composition. Reason: divergences D1, D3, D5, D6.
8. **Decision 7 (line 309).** Named `conf.py::RELAY_GLOBALID_STRATEGY_KEY` as the one constant serving both the
   read key and the error subject. Reason: divergence D7.
9. **`## Implementation plan`, Slice-1 row (line 414).** Added `GLOBALID_SETTING_UNSET` to the `registry.py`
   cell and corrected the New-tests cell for the un-inspectable case, the absent-key storage case, and the
   two finalization-scoped tests' actual file. Reason: divergences D2, D4, D5.
10. **`## Test plan` → `### Slice 1` (lines 444-447).** Corrected `test_meta_globalid_strategy_callable_
    accepted` to its shipped name, added the four-arg / async-object / partial-wrapped / absent-key /
    two un-inspectable-callable rows, and added the closing paragraph naming the four finalization-scoped
    tests and the file they live in. Reason: divergences D4 and D5.
11. **`## Definition of done` item 2 (line 547).** Added the un-inspectable-callable rejection, named
    `STRING_GLOBALID_STRATEGIES`, and stated the `None`-on-absent slot value. Reason: divergences D1, D5, D7.
12. **`## Definition of done` item 3 (line 548).** Named the sentinel and `DEFAULT_GLOBALID_STRATEGY`, and
    replaced "`tests/types/test_base.py` covers the slice" with the accurate two-file split. Reason:
    divergences D2, D4, D7.

**Rationale companion entries appended** to
`docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md` (append-only, keyed by Decision heading and
anchor, per `docs/builder/BUILD.md` `## Spec rationale extraction`):

- Decision 5 → two `**Post-ship:**` bullets: the `GLOBALID_SETTING_UNSET` sentinel (with the concrete failure a
  `None`-initialised slot would produce) and the `DEFAULT_GLOBALID_STRATEGY` constant.
- Decision 6 → three `**Post-ship:**` bullets: the inspection containment and its principle; the shared
  vocabulary / gate-text constants including the retired "or remove the key" quotation; and the dropped-`info`
  four-arg rejection as a named consequence of Decision 4's delta (b).
- Decision 7 → one `**Post-ship:**` bullet: the `RELAY_GLOBALID_STRATEGY_KEY` constant and the test that pins
  the error subject to it.
- `## Non-Decision deliberation` → two bullets: where the Slice-1 setting tests actually live and why the
  Test plan's own wording carried the tell; and the stale `types/definition.py` docstring handed to Slice 2.

No claim in the companion was edited or removed — every addition is new text at the end of the section it
belongs to.

### Handed forward

- **To Slice 2 (a source edit, out of Worker 1's fence).**
  `django_strawberry_framework/types/definition.py::DjangoTypeDefinition` #"the filter falls back to
  node-id-only validation" — the `effective_globalid_strategy` docstring still describes the pre-`0.0.14`
  node-id-only fallback for a known-`None` strategy. The shipped
  `django_strawberry_framework/filters/base.py::_decode_and_validate_global_id` fails **closed** on that case
  before `::_accepted_globalid_type_names` is consulted (that helper's own docstring says so), which is what
  Decision 13 contracts. The spec is right; the source comment is stale. Not a Slice-1 CODE GAP — Decision 13
  is Slice 2's contract — but it is a real code-vs-code inconsistency and needs a Worker 2 dispatch when
  Slice 2 opens.
- **To Slice 2 (an unowned shipped surface).**
  `django_strawberry_framework/types/finalizer.py::_warn_model_label_secondary_collapse` — a
  multi-type-model warning with no sentence in Decision 8 or Decision 10, which own the model-label-routing
  audit. Surfaced by this pass's package-wide helper inventory; audit and contract it there.
- **From Slice 0, still open and not this slice's:** the `install_globalid_typename_resolver` arity
  contradiction in the Slice-2 checklist (owner: Slice 2); DoD item 1's stale CSV claim and Decision 1's
  pre-archival `docs/spec-031-…` path (owner: Slice 5); the two `spec-032` cross-references into moved text
  (owner: maintainer / a future `032` cycle).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

[glossary-configurationerror]: ../GLOSSARY.md#configurationerror

<!-- docs/SPECS/ -->

[spec-029]: ../SPECS/spec-029-consumer_dx_cleanup-0_0_9.md
[spec-030]: ../SPECS/spec-030-connection_field-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

[base]: ../../django_strawberry_framework/types/base.py
[conf]: ../../django_strawberry_framework/conf.py
[definition]: ../../django_strawberry_framework/types/definition.py
[registry]: ../../django_strawberry_framework/registry.py
[relay-utils-typing]: ../../django_strawberry_framework/utils/typing.py

<!-- tests/ -->

[test-relay-interfaces]: ../../tests/types/test_relay_interfaces.py
[test-types-base]: ../../tests/types/test_base.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
