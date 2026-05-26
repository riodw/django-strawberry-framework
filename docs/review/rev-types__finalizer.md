# Review: `django_strawberry_framework/types/finalizer.py`

Status: verified

## DRY analysis

- **Three-loop iteration over `registry.iter_definitions()` shares the `if definition.finalized: continue` guard verbatim across `finalizer.py:215-222`, `finalizer.py:224-238`, and `finalizer.py:240-244`.** Each loop is a distinct phase (resolvers / interfaces+relay / decoration) with different per-entry work, so collapsing them would muddy the phase boundary the module docstring promises. Defer until a fourth pass is added; then extract a `_for_each_not_yet_finalized(action)` helper that drives the three call shapes off a phase enum. Trigger: any new per-type phase landing between Phase 2 and Phase 3.
- **`_format_unresolved_targets_error` (`finalizer.py:58-79`) and `_format_ambiguity_error` (`finalizer.py:82-100`) are sibling "build a finalize-time error message" formatters with the same shape: header + indented body + remediation footer.** Both author the canonical error string consumers grep against; both are exclusively called from this module. Defer with trigger: when a third finalize-time formatter lands (e.g. cycle detection in interface graph, or Relay-collision-at-finalize), consolidate the three through a shared `_format_finalize_error(header, lines, footer)` helper. The current factoring keeps each error string greppable as a literal block, which is the higher-value property today.

## High:

None.

## Medium:

### Module docstring cites stale line numbers

The module docstring at `finalizer.py:28-31` reads:

```django_strawberry_framework/types/finalizer.py:28:31
The function entry-guards on ``registry.is_finalized()`` (line 108) so a
second call is a no-op. The registry's finalized flag flips only after
every type's Phase 3 call returns (line 176): a raise inside Phase 2,
```

The cited line numbers are wrong against the current file: `is_finalized()` entry-guard is at `finalizer.py:165` (not 108), and `registry.mark_finalized()` is at `finalizer.py:246` (not 176). The docstring's per-phase narrative is otherwise accurate and load-bearing — it is the canonical reference for the failure-atomic / re-entrant contract that `tests/test_registry.py:234-235` (`finalize_django_types()` called twice) and `tests/types/test_definition_order.py:883-908` (audit-before-unresolved ordering) pin. Why it matters: future readers grep these line numbers to confirm the docstring matches the implementation and either patch the docstring on every line shift (high churn) or stop trusting line citations in module docstrings (loss of audit trail). Recommended change: replace the parenthetical line numbers with named references (e.g. "entry-guards on ``registry.is_finalized()`` at the top of ``finalize_django_types()``" and "as the last statement of ``finalize_django_types()``") so the docstring survives file growth without per-cycle docstring patches. Same pattern recurs in the function docstring at `finalizer.py:157-158` ("``registry.mark_finalized()`` runs as the last statement of this function") — that wording is correct; mirror it in the module docstring.

## Low:

### Phase 2 / Phase 2.5 ordering risk is documented but not test-pinned

The block comment at `finalizer.py:208-214` explicitly names a latent ordering risk: "No Strawberry interface currently exposes a same-named ``resolve_<field>`` default for an auto-mapped Django relation, so this is a latent ordering risk, not a live bug. If a future Strawberry interface introduces such a default, swap the loop ordering and pin the consumer-interface-wins behavior in tests." The comment is correct as a forward-looking note but the trigger is grep-discoverable from a Strawberry release-notes scan, not from a failing test. Defer until Strawberry ships an interface with a same-named ``resolve_<field>`` default for an auto-mapped Django relation; at that point add a test that pins consumer-interface-wins behavior and swap the loop ordering if needed. Quote the trigger condition in the comment so the next reviewer can grep for it; current wording is sufficient.

### Defense-in-depth comment at `finalizer.py:179-184` could cite a test

The `consumer_authored_fields` early-continue branch is documented as defense-in-depth against a future `_build_annotations` change. The current call graph (per `types/base.py:818-819` and `types/base.py:851-852`) already skips appending pending records for consumer-authored fields, so this branch is genuinely a no-op today. The comment captures the rationale well; a future reviewer auditing dead-code claims would benefit from a citation to the `consumer_authored_fields` four-corner storage invariant (`rev-types__base.md` M2). Defer until the next cycle that touches the four-corner contract (`types/resolvers.py` or the `types/` folder pass); fold the citation in then.

### `_audit_primary_ambiguity` sort key is `model.__name__` not `(model.__module__, model.__name__)`

`finalizer.py:124` sorts offenders by `model.__name__` for deterministic error output. Two models with the same `__name__` in different apps (legal across Django apps, e.g. `apps.products.Item` vs. `apps.library.Item`) would produce a non-deterministic relative order between the two name-collision rows. This is an edge case that the test suite does not currently exercise (per `tests/test_registry.py:330-460` ambiguity audit tests use distinct `__name__` values). Defer until the test fixtures introduce same-named models in different apps; then tighten the sort key to `(model.__module__, model.__name__)` and add the regression test.

### `definition.finalized = True` write at `finalizer.py:244` is the unique flip site

Confirmed via repo grep: `definition.finalized` is written only at `finalizer.py:244` and read at `finalizer.py:216,225,241` (the three phase-loop guards). The single-writer / three-reader shape is correct and pins the rerun re-entrancy contract. Recap entry, not a finding.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_audit_primary_ambiguity` reuses `registry.models_with_multiple_types()` and `registry.primary_for(...)` (`registry.py:251-257,235-242`) per its docstring at `finalizer.py:106-111`. The pending-relation walk reuses `registry.iter_pending_relations()` and `registry.discard_pending(...)` (`registry.py:324-348`) and identity-matched discard avoids coupling to `PendingRelation`'s hashability. Phase 2.5 delegates the actual base-injection / pk-gate / resolver-installation to `apply_interfaces` / `_check_composite_pk_for_relay_node` / `install_relay_node_resolvers` from `types/relay.py` (`relay.py:86-150,467-492`), so the finalizer owns phase ordering, not interface mechanics. `resolved_relation_annotation` (`types/converters.py`) is the single canonical converter for the resolved-annotation shape — the finalizer never authors annotations directly.
- **New helpers considered.** A `_iter_unfinalized()` generator over `registry.iter_definitions()` was considered to collapse the three `if definition.finalized: continue` heads (`finalizer.py:215-217,224-226,240-242`); rejected because the three phases have semantically distinct entry conditions (Phase 2 always runs the resolver attach, Phase 2.5 gates on `definition.interfaces` then on `implements_relay_node`, Phase 3 always decorates) and the shared continue is the cheapest possible expression of the rerun contract — a generator would hide the per-phase entry condition under a name. Re-triage when a fourth phase lands (cycle detection or post-decoration audit).
- **Duplication risk in the current file.** The two formatter functions at `finalizer.py:58-79` and `finalizer.py:82-100` share the "header + indented body + remediation footer" shape; the duplication is intentional sibling design — each error string is a literal block consumers grep against and the sibling-formatter docstring at `finalizer.py:61-66` already names the convention (sibling of `_format_ambiguity_error`; rename together). The three `for type_cls, definition in registry.iter_definitions(): if definition.finalized: continue` blocks (`finalizer.py:215-217,224-226,240-242`) are the rerun-recovery pattern documented in the function docstring at `finalizer.py:147-152`; the repetition is the contract.

### Other positives

- Phase 1 failure-atomicity is implemented by collecting `unresolved`, `resolved`, and `consumer_authored` into in-memory lists at `finalizer.py:170-193` BEFORE any `__annotations__` mutation at `finalizer.py:199-205`. The `_audit_primary_ambiguity()` call at `finalizer.py:168` runs before the pending walk, so an ambiguity-induced raise leaves every pending record intact and the unresolved-target raise at `finalizer.py:195-196` fires before the annotation-rewrite loop. `tests/types/test_definition_order.py:883-908` pins audit-before-unresolved ordering; `tests/types/test_definition_order.py:178-192` pins the unresolved error format ("Cannot finalize Django types", "Item.category -> Category", "no registered DjangoType").
- Error attribution is precise: `_format_unresolved_targets_error` (`finalizer.py:58-79`) names the source model, the field name, AND the target model on each offender line, so a consumer scan of the error surfaces both "which type fails" and "which target was unresolved." `_format_ambiguity_error` (`finalizer.py:82-100`) names every offending registered type per model and the `Declare Meta.primary = True` remediation footer the audit's tests pin against (per `_format_ambiguity_error`'s docstring at `finalizer.py:90-92`).
- Idempotency: the `if registry.is_finalized(): return` short-circuit at `finalizer.py:165-166` means a second call is a no-op after a successful first call; the partial-failure recovery is supported by the per-entry `if definition.finalized: continue` guards at the head of each phase loop and by `registry.mark_finalized()` running as the last statement at `finalizer.py:246` (so a Phase 2/2.5/3 raise leaves the flag False). The function docstring at `finalizer.py:146-163` is the authoritative narrative of this contract.
- Relay interface wiring composes correctly: `apply_interfaces` runs only when `definition.interfaces` is non-empty (per `finalizer.py:234`), and the `implements_relay_node` MRO check at `finalizer.py:236` independently catches direct `class Foo(DjangoType, relay.Node)` inheritance — the block comment at `finalizer.py:227-233` cites the `feedback.md` § High "Direct relay.Node inheritance bypasses Relay finalization" rationale. Phase 2.5 runs before Phase 3 so `strawberry.type(...)` sees the mutated bases and the four `resolve_*` defaults.
- Abstract-base skipping is handled upstream at `DjangoType.__init_subclass__` (per `types/base.py:16` module docstring "abstract subclasses without ``Meta`` are skipped"); the finalizer only iterates `registry.iter_definitions()`, so abstract subclasses with no `Meta` never enter the registry's definitions dict and the finalizer never sees them. The split-responsibility shape is correct.
- `strawberry.type(type_cls, name=..., description=...)` at `finalizer.py:243` is the only `strawberry.type` decoration site in the package per the module docstring claim at `finalizer.py:5-6` ("the only place ``strawberry.type`` decoration touches a consumer-facing class"); confirmed via repo grep (no other call site exists in `django_strawberry_framework/`).
- `_audit_primary_ambiguity` and the unresolved-target walk read registry state in distinct passes — the audit uses `models_with_multiple_types()` / `primary_for(...)` / `types_for(...)` (registry-keyed by model); the unresolved walk uses `iter_pending_relations()` / `get(...)` / `get_definition(...)` / `discard_pending(...)` (registry-keyed by pending record and source type). The single registry singleton mediates both passes without any shared mutable scratch state inside the finalizer.

### Summary

`types/finalizer.py` is a small, phase-ordered build gate that delegates per-phase mechanics to siblings (`types/relay.py`, `types/converters.py`, `types/resolvers.py`) and owns only the lifecycle: audit, resolve, attach, interfaces+relay, decorate, mark finalized. Phase 1 failure-atomicity, rerun recovery via per-entry `definition.finalized` guards, the ambiguity-audit-before-unresolved-target ordering, and the `apply_interfaces`-before-`strawberry.type` ordering are all correct and pin against existing tests in `tests/types/test_definition_order.py` and `tests/types/test_relay_interfaces.py`. One real Medium: the module docstring cites stale line numbers (108 / 176) for the `is_finalized()` entry-guard and the `mark_finalized()` final-statement positions; replace with named references so the docstring survives file growth. Four trigger-gated Lows, two DRY deferred opportunities.

---

## Fix report (Worker 2)

### Files touched
- `django_strawberry_framework/types/finalizer.py:28-36` — replaced stale parenthetical line citations `(line 108)` / `(line 176)` in the module docstring with named references ("at the top of ``finalize_django_types()``" and "via ``registry.mark_finalized()`` as the last statement of ``finalize_django_types()``"), mirroring the wording already used in the function docstring at `finalizer.py:157-158`. No logic change; docstring narrative is otherwise unchanged. Per-phase wording, the per-entry `if definition.finalized: continue` rerun-recovery sentence, and the `registry.clear()` escape-hatch sentence are preserved verbatim modulo line-length re-wrap to satisfy ruff E501 at 110.

### Tests added or updated
- None. M1 is a pure docstring rewording with zero behavioural surface; existing finalize lifecycle tests in `tests/test_registry.py::test_finalize_django_types_idempotent` (`tests/test_registry.py:234-235`) and `tests/types/test_definition_order.py::test_audit_runs_before_unresolved` (`tests/types/test_definition_order.py:883-908`) already pin the contract the docstring describes (entry-guard idempotency + audit-before-unresolved ordering); no new pin is warranted.

### Validation run
- `uv run ruff format .` — pass (118 files unchanged)
- `uv run ruff check --fix .` — pass (All checks passed)
- No pytest run per AGENTS.md standing rule and START.md "Do not run pytest after every change"; M1 is docstring-only.

### Notes for Worker 3
- Shadow file: not used during fix implementation; the M1 surface is grep-discoverable as the literal strings `(line 108)` and `(line 176)` and Worker 1's artifact already cited the exact original lines (`finalizer.py:28-31`).
- Consolidated single-spawn shape per `worker-2.md` "All Lows are explicitly forward-looking per Worker 1's own prose" + "The artifact's only in-cycle edit is a single trivially-localised docstring sentence with no logic change" — both criteria satisfied (L1-L4 each carry verbatim "defer until ..." prose; M1 is one docstring-paragraph rewording).
- Intentionally-rejected findings: none. M1's premise re-verified at write time — `registry.is_finalized()` entry-guard is at the post-edit line `finalizer.py:167` (artifact cited 165; +2 drift is the M1 docstring re-wrap adding two paragraph lines), and `registry.mark_finalized()` is at the post-edit line `finalizer.py:248` (artifact cited 246; +2 drift from the same docstring re-wrap). This is exactly the per-cycle line-number churn that motivated the named-reference rewrite — the artifact's stale-line-numbers diagnosis is correct.
- Deferred findings — verbatim trigger conditions preserved for Worker 3 cross-check against the artifact body:
  - DRY #1 (three-loop iteration): "any new per-type phase landing between Phase 2 and Phase 3".
  - DRY #2 (sibling error formatters): "when a third finalize-time formatter lands (e.g. cycle detection in interface graph, or Relay-collision-at-finalize)".
  - L1 (Phase 2 / 2.5 ordering risk): "until Strawberry ships an interface with a same-named ``resolve_<field>`` default for an auto-mapped Django relation".
  - L2 (defense-in-depth comment citation): "the next cycle that touches the four-corner contract (`types/resolvers.py` or the `types/` folder pass)".
  - L3 (`_audit_primary_ambiguity` sort key): "until the test fixtures introduce same-named models in different apps".
  - L4 (`definition.finalized = True` unique flip site): Worker 1's own prose "Recap entry, not a finding" — explicit no-edit.

---

## Comment/docstring pass

(Fused with logic pass — M1 IS a docstring edit; per `worker-memory/worker-2.md` pattern 15 "When the M1 fix lands the docstring in the same diff because the docstring IS the contract, the comment pass is structurally a no-op — document this explicitly rather than re-editing.")

### Files touched
- None additional. The docstring rewrite at `finalizer.py:28-36` is the M1 logic edit and the comment-pass edit simultaneously.

### Per-finding dispositions
- Medium 1 (stale line numbers): logic-pass edit IS the docstring edit; nothing remains for the comment pass. Function docstring at `finalizer.py:157-158` was already correct (per Worker 1's prose "that wording is correct; mirror it in the module docstring") and is unchanged.
- Low 1 (Phase 2 / 2.5 ordering): forward-looking; Worker 1's verbatim prose "The comment is correct as a forward-looking note" + "Quote the trigger condition in the comment so the next reviewer can grep for it; current wording is sufficient." No comment edit.
- Low 2 (defense-in-depth comment citation): forward-looking; Worker 1's verbatim prose "Defer until the next cycle that touches the four-corner contract ...; fold the citation in then." No comment edit this cycle.
- Low 3 (`_audit_primary_ambiguity` sort key): forward-looking; Worker 1's verbatim prose "Defer until the test fixtures introduce same-named models in different apps". No comment edit.
- Low 4 (`definition.finalized = True` unique flip site): Worker 1's verbatim prose "Recap entry, not a finding." No comment edit.
- DRY #1 + DRY #2: forward-looking deferrals; trigger conditions cited verbatim above. No comment edit.

### Validation run
- `uv run ruff format .` — pass (no changes; ran as part of the logic pass)
- `uv run ruff check --fix .` — pass (no changes; ran as part of the logic pass)

### Notes for Worker 3
The consolidated-single-spawn shape applies cleanly: M1 is a single trivially-localised docstring rewrite and every Low/DRY entry is explicitly forward-looking per Worker 1's own prose. The post-edit `finalizer.py:167` (is_finalized entry-guard) and `finalizer.py:248` (mark_finalized last statement) lines confirm the named-reference rewrite is exactly the remediation that eliminates per-cycle line-number churn for this contract.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Per `AGENTS.md` line 21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_7.md`'s silence on changelog authorisation for cycle 23. The cycle's only edit is internal: a module-docstring rewrite with zero behavioural surface, zero public API change, zero test surface, and zero consumer-visible effect. This is a textbook `Not warranted` shape per `worker-2.md`'s "internal-only ... docstring polish" enumeration. The twenty-two-deep precedent chain across cycles 1-22 in this release window (every prior cycle closed `Not warranted` for analogous internal-only edits, per `worker-memory/worker-2.md`) reinforces the disposition; chain-depth dominance is the standing argument and this cycle does not break the pattern.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass (no changes)
- `uv run ruff check --fix .` — pass (no changes)

---

## Verification (Worker 3)

### Logic verification outcome
M1 (stale module-docstring line numbers) addressed. `git diff -- django_strawberry_framework/types/finalizer.py` shows a single docstring hunk at lines 28-37 replacing `(line 108)` and `(line 176)` with named references ("at the top of ``finalize_django_types()``" and "via ``registry.mark_finalized()`` as the last statement of ``finalize_django_types()``"), mirroring the function docstring at `finalizer.py:157-158` exactly as Worker 1 recommended. Zero behavioural surface, no other hunks. The per-phase narrative, the `if definition.finalized: continue` rerun-recovery sentence, and the `registry.clear()` escape-hatch sentence are preserved verbatim modulo E501 re-wrap. L1-L4 + DRY-1 + DRY-2 all explicitly forward-looking per Worker 1's verbatim "Defer until …" prose; trigger phrasing confirmed verbatim across artifact body, Worker 2 notes, and (where applicable) the comment-pass per-finding disposition: DRY-1 "any new per-type phase landing between Phase 2 and Phase 3"; DRY-2 "when a third finalize-time formatter lands (e.g. cycle detection in interface graph, or Relay-collision-at-finalize)"; L1 "until Strawberry ships an interface with a same-named ``resolve_<field>`` default for an auto-mapped Django relation"; L2 "the next cycle that touches the four-corner contract (`types/resolvers.py` or the `types/` folder pass)"; L3 "until the test fixtures introduce same-named models in different apps"; L4 "Recap entry, not a finding".

### DRY findings disposition
DRY-1 + DRY-2 both deferred with verbatim trigger conditions preserved (see above). One-implementation-with-logic scale; helper extraction correctly rejected for this cycle.

### Temp test verification
None used. M1 is docstring-only with zero behavioural surface; no temp tests warranted.

### Changelog disposition verification
`git diff -- CHANGELOG.md` empty. Disposition cites both AGENTS.md line 21 and the active plan's silence on changelog authorisation for cycle 23, plus the 22-cycle precedent chain. Internal-only framing matches the actual diff scope (a single module-docstring rewording, zero public-API surface). Three legs cleared.

### Comment-pass verification
Bundled-with-logic-pass shape per worker-memory pattern 15 ("the docstring IS the contract"). Worker 2's per-finding disposition cites the bundled shape and Worker 1's verbatim "that wording is correct; mirror it in the module docstring" prose. No additional comment edits warranted; function docstring at `finalizer.py:157-158` already correct (used as the mirror source for M1). Re-reading the diff confirms the docstring delta is exactly the named-reference rewrite Worker 1 recommended.

### Validation
- `uv run ruff format --check django_strawberry_framework/types/finalizer.py` — pass (1 file already formatted)
- `uv run ruff check django_strawberry_framework/types/finalizer.py` — pass (All checks passed)

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` and marks `docs/review/review-0_0_7.md:120`.

---

## Iteration log

(No re-passes; terminal acceptance on first verification.)
