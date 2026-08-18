# Rationale: spec-018 — Multiple `DjangoType`s per model with `Meta.primary` (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-018-meta_primary-0_0_6.md`][spec-018]. The spec is the contract and states only what holds at `HEAD`; everything that explains **how it got there** lives here: six numbered revisions of review feedback, the alternatives each Decision rejected, the nine risks and how each settled, every claim the spec once made and may no longer make, and the later cards that reshaped what this one landed without ever touching the spec.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass.

## Provenance of this record

**This pass performed a MOVE, not a reconstruction.** Spec-018 carried a full deliberative layer to cut: a 37-line `Revision history` block enumerating six review rounds with their H / M / L sub-items, per-Decision "why the alternative lost" argument paragraphs, a nine-bullet `## Risks and open questions` section, a `## Current state` section describing the pre-card baseline, and a Slice 6 that reproduced a whole KANBAN card body verbatim. Text marked **Moved** below was **cut** out of the spec, not copied: it exists here and nowhere else.

**Measured byte counts, both with `wc -c` at this working tree, taken when both files were final** (re-measured after the review round's apply passes edited both, so these supersede every earlier figure in the round artifact)**:**

| File | Before this pass | After |
|---|---|---|
| `docs/SPECS/spec-018-meta_primary-0_0_6.md` | 123,752 | 92,154 |
| `docs/SPECS/appx/spec-018-meta_primary-0_0_6-rationale.md` | 0 (did not exist) | 54,659 |

`HEAD` at the time of the pass is `de2601e9`. The package is at `0.0.14`; this card shipped at `0.0.6` on 2026-05-19.

**The card shipped as `014`, not `018`.** Every original commit message, build artifact, and in-tree comment from the build names `spec-014-meta_primary-0_0_6.md` — the build commit is `8cec18a3` ("Finish docs/spec-014-meta_primary-0_0_6.md", 2026-05-18). The 2026-07-30 board renumber moved the card from `014` to `018` and rewrote the filename and every card reference with it. Both numbers name one card. A reader chasing `git log` for this spec's history should search `spec-014-meta_primary`, not `spec-018`; in-tree comments that still read `spec-014` (for example the import-order-trap comment in `django_strawberry_framework/types/base.py::_build_annotations`) are pre-renumber survivors, not references to a different card.

**Moved** — cut from the spec by this pass, and now only here:

- the whole `Revision history (kept inline so the spec is self-contained)` block, all six numbered revisions with their H / M / L sub-items (37 lines);
- the whole `## Current state` section, which described the pre-card baseline (a one-to-one `_types` map, `register` raising on a second type, `Meta.primary` rejected as an unknown key) — carried here as a condensation, not verbatim, in the same way as the `Revision history` block below;
- the whole `## Risks and open questions` section, all nine bullets;
- Decision 1's "Why a plain bool, not a tri-state or enum" paragraph;
- Decision 2's "Why a separate `_primaries` map instead of marking the primary inside `_types[model]`" paragraph and its three numbered reasons, plus the L4 parenthetical narrating what `register` did pre-spec;
- Decision 3a's "Why not skip the call to `register()` when the type is already registered" paragraph, and its "What disappears" paragraph quoting the retired `"<model_name> is already registered as <existing_type_name>"` message;
- Decision 9's "Why not extend `registry.get(model)` itself to accept an origin hint" paragraph;
- Slice 6's verbatim `DONE-018-0.0.6` KANBAN card body (67 lines).

**Reconciled in place** — the contract sentence stays in the spec and only its chronology was cut, so the paragraph is neither wholly moved nor wholly kept:

- Decision 4's "Note on `iter_types()`" paragraph. Its chronology ("a previous draft proposed a `primary_or_single_per_model()` helper; a later revision dropped it") was cut and now lives only in this file, under [`### Decision 4 — registry.get semantics`](#decision-4--registryget-semantics). The contract half — the schema audit iterates every reachable type and dedupes, and there is deliberately no "primary or single per model" helper — survives in the spec at its original site, with a one-line pointer here. The dispositions stay mutually exclusive under this fourth label: no *sentence* is in both files, because the spec kept the rule and this file kept the rejected alternative.

**Kept in the spec deliberately, against the pull of this move.** [`worker-1.md`][worker-1]'s carve-out for implementation-relevant rationale is load-bearing here, and three passages exercised it:

- **Decision 4's "Why `None` instead of raise here."** It explains why `registry.get` must fall through rather than raise on the ambiguous state — `__init_subclass__`-time relation binding needs the deferral path, and finalize-time resolution needs the audit to fire first. A builder who never reads it makes `get` raise, and the ambiguity error stops being the one consumers see.
- **Decision 8's "What does NOT read `definition.primary`."** It is a prohibition, not a derivation: `definition.primary` is a denormalization for introspection, and routing an ambiguity decision through it would give the package two authorities for "which type is primary".
- **The Slice 4 call-site split for `_selected_scalar_names`.** The reason that helper keeps `source_type=None` — it is reached only from nested FK-id elision, where the model argument is `django_field.related_model` and never a resolver's root return type — is exactly what stops a later builder "completing" the threading and making a nested step plan against a root return type.

**Deleted outright rather than moved**, per [`worker-1.md`][worker-1] rule 2, because the current contract falsifies them: the `Status: draft (revision 6, post-TODO-anchor review)` line; every carrier of the retired duplicate-primary message `"<new> is already declared primary as <existing>"`; the claim that `types/converters.py::resolved_relation_annotation` reads `target_type = registry.get(...)`; the `#"registry.get(django_field.related_model)"` citation into `walker.py::_walk_selections`; the `#"test_register_collision_raises"` and `#"pre-finalize relation annotation"` citations into test files; the claims that `tests/types/test_finalizer.py` and `tests/types/test_relations.py` "do NOT exist today"; Slice 6's instruction to move `DONE-018-0.0.6` to `DONE-018-0.0.6`; and Slice 6's claim that the spec is yet to be archived. Each is recorded below as a claim the spec may no longer make, and none survives anywhere as live spec text.

**Glossary anchors: fifteen terms, fifteen anchors, all still linked.** Two terms lost their only carrier to this move — `Definition-order independence` (carried only by the revision-5 H1 item) and `Plan cache` (carried only by the revision-2 H2 item). Both were re-homed in reconciled prose: `[definition-order independence][glossary-definition-order-independence]` now sits in the `## Goals` bullet on centralized relation binding, where it is the property the always-defer contract extends, and `[plan cache][glossary-plan-cache]` in the `## Edge cases and constraints` bullet that governs it. `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-018-meta_primary-0_0_6.md` exits 0 after the rewrite with `OK: 15 terms`.

## What the card actually did, and what later cards did to it

`DONE-018-0.0.6` shipped in `0.0.6` on 2026-05-19 (`CHANGELOG.md #"## [0.0.6] - 2026-05-19"`), built in one commit, `8cec18a3`. Five later changes reshaped what it landed, none of which touched this spec:

| Change | Date | What it changed |
|---|---|---|
| commit `13d8dac5` ("Apply feedback") | 2026-05-18 | Renamed `audit_primary_ambiguity` to `_audit_primary_ambiguity` — module-private, the same day the build landed — and removed the `if type_cls in types:` guard from `register_with_definition`'s rollback body. |
| commit `21212a19` ("End Bug Hunt") | 2026-05-20 | Reworded the duplicate-primary error to carry the Django model name. |
| commit `b70c0360`, then `1fb42b04` | 2026-05-19 | Added the public `TypeRegistry.unregister`, then reshaped it. |
| commit `7d892d6f` (spec-031, `0.0.9`) | 2026-06-10 | Gave `_audit_primary_ambiguity` a `multi_type_models` parameter, so `finalize_django_types` materializes the one-shot `models_with_multiple_types()` generator once per build and feeds the same tuple to this Phase-1 audit and to spec-031's Phase-2.5 `_audit_model_label_routing`. |
| commit `36da25b4` | 2026-06-11 | Moved the optimizer's nested relation-target lookup out of `_walk_selections` into `optimizer/walker.py::_resolve_relation_target`, which prefers `DjangoTypeDefinition.related_target_for(...)` and falls back to `registry.get(related_model)`. |

Two further changes touched this card's surface without changing its contract: commit `c3767495` (2026-07-13, "fix(types): harden finalization lifecycle") added `TypeRegistry.register_type_teardown`, and commit `6c7e1a8a` (2026-07-15, "refactor(registry): share type detachment") extracted `TypeRegistry._detach_type_from_model` so `unregister` and `register_with_definition`'s rollback share one implementation of the "`_types` never keeps an empty list" invariant.

### Nothing was skipped in the code

The load-bearing half of this cycle, re-derived in this pass rather than accepted from the dispatch. Every item in the spec's `## Slice checklist`, `## Goals`, `## User-facing API`, `## Test plan` (categories 1-22), and `## Definition of done` was walked, and **no item was found that was never shipped.**

- **The registry surface (Slice 1).** `_types: dict[Model, list[Type]]`, `_primaries`, `register(..., *, primary=False) -> bool` with the symmetric flip guard and the duplicate-primary raise, `register_with_definition`'s snapshot-and-conditional-restore rollback, the three-state `get`, `primary_for`, `types_for`, `models_with_multiple_types`, the per-type `iter_types`, and `clear()` wiping `_primaries` — all present in `django_strawberry_framework/registry.py` at `HEAD`.
- **`Meta.primary` (Slice 2).** `"primary"` is in `ALLOWED_META_KEYS` (`types/base.py`), the bool guard is in `_validate_meta`, and `DjangoTypeDefinition.primary` exists.
- **The audit (Slice 3).** `types/finalizer.py::_audit_primary_ambiguity`, called from `finalize_django_types` after the `is_finalized()` short-circuit and before pending-relation resolution.
- **The consumer sites (Slice 4).** `_build_annotations` always-defers auto-synthesized relations behind the preserved `consumer_authored_fields` short-circuit; `walker.py::_resolve_field_map` takes `source_type` and `_selected_scalar_names` does not; `extension.py::_OriginAndModel` / `_resolve_model_from_return_type` return the pair and `_optimize` guards on `if resolved is None`; `_build_cache_key` carries the fifth `origin` slot; `check_schema` iterates `iter_types()` behind a `set[tuple[type[models.Model], str]]` dedupe.
- **The test names.** The spec names **56 distinct test functions** across its checklist, decisions, and revision history. Each was searched by `grep -rl "def <name>(" tests examples`, one name per search. **All 56 exist in the tree under their own names.** Twelve further `test_*` tokens the same extraction returns are file-name fragments (`test_registry`, `test_base`, `test_converters`, `test_definition_order`, `test_extension`, `test_walker`, `test_init`, `test_finalizer`, `test_relations`, `test_meta_primary`) or names the spec offered and the build did not take (`test_register_two_primaries_raises`, one of two options in a "Worker 1 picks" box), plus `test_register_collision_raises`, the legacy test the card's own checklist ordered deleted.
- **The docs half of Slice 6.** `docs/GLOSSARY.md` carries `Meta.primary` at `shipped (0.0.6)` with the multi-type bullet on `DjangoType` and the flipped index badge; `docs/README.md` and `TODAY.md` mention the key; `CHANGELOG.md` carries the `Added` and `Changed` entries; `KANBAN.md` carries the card in Done linked to the archived spec path.

Three claims needed more than a grep, and all three were re-derived:

- **The nested-relation contract still holds** even though the citation naming it rotted. `optimizer/walker.py::_resolve_relation_target` prefers `DjangoTypeDefinition.related_target_for(django_name)`, and `types/definition.py::DjangoTypeDefinition.related_target_for` resolves its target through `registry.get(target_model)` — so both legs of the fallback land on the primary. Read the docstring at `types/definition.py::DjangoTypeDefinition.related_target_for`: it names `registry.get(target_model)` and the `Meta.primary` honouring explicitly.
- **The audit still runs exactly once per build.** `finalize_django_types` entry-guards on `registry.is_finalized()`, and `_audit_primary_ambiguity` is called once, below that guard, before the unresolved-target collection. `tests/test_registry.py::test_audit_runs_once_per_build` pins it with a spy.
- **The duplicate-primary message reword is documented, not silent.** `CHANGELOG.md` carries it under a later version's `Changed` section, and `docs/GLOSSARY.md`'s `Meta.primary` entry already quotes the corrected string. The spec was the last carrier of the retired one.

**No code defect and no code gap was found, so no code round is opened by this cycle.**

## Entries keyed to the spec

### The `Status:` line

**Deleted.** The line read `Status: draft (revision 6, post-TODO-anchor review).` — a chronology in the header of a spec whose card is `Done`. Deleted rather than moved: the revision count is recoverable from this file, and "draft" was false the moment `0.0.6` cut. Replaced with `Status: shipped in 0.0.6 (2026-05-19).` plus a pointer paragraph naming this file.

### `## Current state`

**Moved.** The whole section, and — like the `Revision history` block — **the full text is not reproduced verbatim**: it is condensed into the paragraph below plus the retraction paragraph that follows, because what a reader needs from a baseline description is the set of facts the current contract replaced, not the prose that framed them. Every load-bearing fact is carried. It described the `0.0.5` baseline: `_types` as a one-to-one `dict[type[models.Model], type]`; `register(model, type_cls)` raising `"<model_name> is already registered as <existing_type_name>"` whenever `model in self._types`; six named `registry.get(model)` call sites all assuming a deterministic lookup; a seven-key `ALLOWED_META_KEYS` with `Meta.primary` in neither the allowed nor the deferred set, so declaring it raised `"Unknown Meta keys: ['primary']"`; and a `DjangoTypeDefinition` with no `primary` field.

**Claims the spec may no longer make:** that `_types` is one-to-one; that `register` raises on a second type for a mapped model; that `Meta.primary` is an unknown key; that `DjangoTypeDefinition` has no `primary` field; that `ALLOWED_META_KEYS` holds seven keys (it holds eighteen at `HEAD`, most of them added by later cards); and that the `registry.get(...)` call-site list it enumerates is current — three of the six have since moved or changed shape.

### `Revision history`, revisions 1-6

**Moved.** The entire block. [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` is explicit that the spec never narrates its own history, and this was a pure instance of it: six numbered rounds of "H1 / M2 / L3 said X, so we changed Y", requiring a reader to apply a chronology to reconstruct what is currently true.

The full text is not reproduced verbatim; what a reviewer needs is the *decision-keyed* residue, distributed through the entries below. The load-bearing content of each round, keyed to what it settled:

- **Rev 1** — initial draft. Proposed a `primary_or_single_per_model()` registry helper to drive the schema audit (Decision 4).
- **Rev 2** — three corrections that shaped the card's three hardest contracts. **H1:** always-defer relation binding (Decision 6, Slice 4), because the eager-bind shortcut froze a relation against a secondary registered before the source. **H2:** thread the resolver's origin type to the walker's root field-map lookup and add it to the plan-cache key (Decision 9), because `registry.get(model)` returns the primary and a root resolver returning a secondary would plan against the wrong `field_map`. **H3:** keep iterating every reachable type in the schema audit and dedupe the warnings, rather than filtering to one type per model — which killed the rev-1 `primary_or_single_per_model()` helper (Decision 4). Plus **M1:** `register()` returns `bool` and `register_with_definition` snapshots `_primaries` so a rollback undoes only what its own call added (Decision 3, Decision 3a).
- **Rev 3** — narrowed rev 2's always-defer language from *every* relation field to every **auto-synthesized** relation field, because the consumer-authored short-circuit had to survive; made the symmetric primary-flip guard symmetric in both directions (Decision 3); and added the explicit "rewrite the stale test" boxes so the behavior change and the test update landed in one commit.
- **Rev 4** — pinned the audit's placement *below* the `is_finalized()` guard (Decision 5); named both `_resolve_field_map` call sites so the root/nested split was an explicit decision rather than an assumption; quoted the live four-element plan-cache tuple; and corrected the retired message's slot order.
- **Rev 5** — retracted a Non-goal that deferred consumer relation overrides to a future card when they already shipped; named `_resolve_model_from_return_type` as the helper that discards the origin; and dropped a false claim that the schema audit and optimizer walker read `definition.primary`.
- **Rev 6** — resolved the `_selected_scalar_names` question by audit rather than by guess (nested-only, stays `source_type=None`); pinned the `_resolve_model_from_return_type` failure contract to "return `None` when either half is unresolvable", which is what stops the three failure-case tests being rewritten into a truthy pair; and scoped the plan-cache `origin` slot to the root-only extension cache.

### Decision 1 — `Meta.primary` shape and validation

**Alternatives rejected, and why each lost:**

- **A tri-state or enum (`PRIMARY` / `SECONDARY` / `UNSET`).** Lost because the contract is binary — "is this type the primary for its model, yes or no" — and a third state would muddy the backward-compatible single-type path, which is "unset" and stays that way.
- **A richer per-context flag** ("primary for queries, secondary for mutations"). Out of scope; it would land as a separate `Meta` key rather than as a widening of this one.

**Changes this decision has undergone:** none in substance — the `Meta.primary` key, the `bool` guard, and the `"Meta.primary must be a bool"` message are at `HEAD` exactly as specified. One presentational reconciliation: the pseudocode comment narrated the guard's placement as "the maintainer's pre-Slice-2 TODO anchor lands the guard here ... pinning the anchor's slot keeps spec and source aligned". That anchor was removed from `django_strawberry_framework/types/base.py` when the card shipped — a tree-wide sweep for `TODO(spec-018` / `TODO(spec-014` / `TODO-<MILESTONE>-018` / `TODO-<MILESTONE>-014` finds none surviving in any source file — so the sentence pointed at something a reader can no longer find, and it was process provenance sitting inside text a builder copies into source. **Reconciled in place:** the placement rule and the reason the two candidate slots are contract-equivalent both stay; only the anchor narration is gone. The landed guard sits exactly where the comment pins it — `_validate_meta` runs the fields/exclude exclusivity check, then the `primary` bool guard, then the `DEFERRED_META_KEYS` check.

### Decision 2 — Registry data model

**Alternatives rejected, and why each lost:**

- **Marking the primary inside `_types[model]`** (a flag on the list entries, or a sentinel position). Lost on three counts, all of which still hold: `_primaries.get(model)` is an O(1) lookup on `registry.get`'s hot path; "no primary declared" is then the absence of a key rather than a sentinel value, which is fewer special cases; and the audit walk reads `_primaries.get(model) is None` against a multi-type model directly, with no scan.

**Changes this decision has undergone:**

- The `_types` / `_primaries` / `_models` shapes are unchanged at `HEAD`. What grew around them is the removal side: commit `6c7e1a8a` extracted `TypeRegistry._detach_type_from_model` as the single implementation of "remove `type_cls` from `_types[model]` and `_models` in lock-step, and never leave an empty list behind", shared by the rollback (Decision 3a) and by the later public `unregister`. Its docstring is explicit that `_primaries` is deliberately *not* its business, because the two callers disagree: `unregister` purges the primary slot unconditionally, and the rollback restores whatever primary predated its own call.

**The claim this decision may no longer make:** that the idempotent same-type re-registration "matches the existing idempotent-import behavior". Revision 5 already corrected it once — pre-spec, `register(Model, T)` twice raised, because the `model in self._types` guard fired before any same-type check — and the L4 parenthetical carrying that correction was itself a chronology. The spec now states the contract as an introduction, with no comparison to a prior behavior no reader can observe.

### Decision 3 — `register` signature and collision rules

**Alternatives rejected, and why each lost:**

- **An asymmetric flip guard.** Revision 2's pseudocode caught only `primary=False -> primary=True` on re-register (`if primary and self._primaries.get(model) is not type_cls: raise`). The reverse — a type stored as primary, re-registered with `primary=False` — returned `False` silently and left the primary in place, contradicting the same contract from the other side. Replaced with the symmetric `requested != stored` comparison, and both directions are pinned by their own tests.

**The claim this decision may no longer make, and where it stood:**

> `ConfigurationError("<new> is already declared primary as <existing>")`

That message is retired. Commit `21212a19` replaced it with:

> `f"Cannot register {type_cls.__name__} as primary for {model.__name__}; {existing_primary.__name__} is already the primary type"`

The reason is the card's own headline change: once one model can carry several `DjangoType`s, an error naming only the two classes forces a stack-trace grep to guess which model the collision is about. The reword is documented in `CHANGELOG.md` and quoted in `docs/GLOSSARY.md`'s `Meta.primary` entry; **the spec was the last carrier of the retired string.**

**The claim occupied eight sites, and all eight are closed.** The population was established before any was edited, by counting *occurrences* of the shortest distinctive token `already declared primary` rather than matching lines: eight. They were Decision 3's pseudocode, Decision 3a's "Collision messages, grep-stable" list, Decision 5's ambiguity table, the Slice 1 checklist's `test_register_two_primaries_for_same_model_raises_configuration_error` box, the Slice 2 checklist's `test_two_primary_types_same_model_raises` box, `## User-facing API`'s error cases, the Slice 6 verbatim KANBAN body, and `## Definition of done`. One (the KANBAN body) left the spec with its section; the other seven were rewritten. `already declared primary` now appears 0 times in the spec.

The two tests that pin the live message assert it by substring, and the spec is now written against what they assert rather than against the retired template: `tests/test_registry.py::test_register_two_primaries_for_same_model_raises_configuration_error` matches `r"Cannot register AdminItemType as primary for Item;.*ItemType is already the primary type"`, and `tests/types/test_base.py::test_registry_collision_raises_configuration_error` matches the same shape through the `__init_subclass__` path. Both pin all three identifiers — the attempted class, the model, and the incumbent primary.

### Decision 3a — `register_with_definition` rollback shape

**Alternatives rejected, and why each lost:**

- **Skipping the `register()` call when the type is already registered.** Lost because `register_definition` may still legitimately raise (a *different* definition for the same type), and the caller needs the contract that `register_with_definition` either fully succeeds or leaves the registry untouched. The snapshot-and-conditional-restore is the simplest shape that satisfies both the idempotent and the rollback paths.
- **An unconditional pop** from `_types[model]` / `_models` / `_primaries` on failure. Lost to the idempotent-`register()` change it shares a card with: a re-registration of an already-stored type is a no-op for `register()`, so an unconditional rollback would tear down *pre-existing* state a failing call never created.

**Changes this decision has undergone:**

- Commit `13d8dac5` removed the `if type_cls in types:` guard from the rollback body — the `appended` flag already establishes that this call appended `type_cls`, so the membership test could not fail.
- Commit `6c7e1a8a` replaced the inline three-statement removal with the shared `TypeRegistry._detach_type_from_model` helper, so the rollback and the public `unregister` cannot drift on the empty-list invariant.

**The rollback CONTRACT is unchanged and correct** — snapshot `_primaries[model]` before `register`, roll back only what this call appended, restore-or-pop the primary slot. Only the code shape moved, and the spec's pseudocode now shows the shape that landed.

**The claim this decision may no longer make:** that `register` still raises a `"<model_name> is already registered as <existing_type_name>"` collision, or that the message merely "disappears". `django_strawberry_framework/registry.py::TypeRegistry._already_registered` is alive and is the shared phrasing for two *other* collisions — `register`'s reverse-collision (same class, different model) and `register_enum`'s `(model, field_name)` collision. The "What disappears" paragraph read as though the helper itself retired with the message, which would mislead anyone grepping for it.

### Decision 4 — `registry.get` semantics

**Alternatives rejected, and why each lost:**

- **A `primary_or_single_per_model()` helper to drive the schema audit.** Proposed in revision 1, dropped in revision 2 by the H3 correction: filtering the audit to one type per model correctly avoids duplicate warnings and silently skips relation fields exposed only on a reachable *secondary* type. The audit keeps full iteration and dedupes the warning sink instead, so the helper has no remaining consumer and was never built. The spec now states the absence as a deliberate design point rather than narrating the proposal.

**Kept in the spec:** the "Why `None` instead of raise here" argument. It is not derivation — it is the reason `get` has three return states rather than two, and it is what stops a later change making the ambiguous state raise from the lookup and pre-empting the audit's actionable error.

### Decision 5 — Ambiguity rules

**Changes this decision has undergone:**

- **Rev 4 pinned the placement.** Rev 3 said to run the audit "at the **start** of `finalize_django_types()`", which read literally could mean above the `if registry.is_finalized(): return` short-circuit — where it would re-run on every call, contradicting the idempotency contract and regressing silently, because a side-effect-free audit against a locked registry raises nothing. Rev 4 rewrote it to "after the existing `is_finalized()` short-circuit but before pending-relation resolution" and added `test_audit_runs_once_per_build`, which spies on `models_with_multiple_types` and asserts one invocation across two `finalize_django_types()` calls.
- **The function is private.** Commit `13d8dac5` renamed `audit_primary_ambiguity` to `_audit_primary_ambiguity` on 2026-05-18, the same day the build landed. The spec carried the public name at **11 occurrences**, counted by the distinctive token `audit_primary_ambiguity` before any were edited; all are now the private name or reworded around it.
- **The signature changed.** Commit `7d892d6f` (spec-031, `0.0.9`) gave the audit a `multi_type_models: tuple[type[models.Model], ...]` parameter. `registry.models_with_multiple_types()` returns a **one-shot generator**, and `finalize_django_types` now runs two audits over the same candidate set — this Phase-1 ambiguity audit and spec-031's Phase-2.5 `_audit_model_label_routing` — so the caller materializes the walk once per finalize and hands the same tuple to both. The audit body also gained a sort by model name, so the error body is deterministic regardless of consumer import order.

**The claim this decision may no longer make: that the audit "is the first work the function does on a non-finalized registry."** At `HEAD` two pure reads precede it inside the guard: the `multi_type_models` materialization the audit itself consumes, and the validated `RELAY_GLOBALID_STRATEGY` snapshot spec-031 added, which can itself raise `ConfigurationError` before the ambiguity audit is reached. The *contract* the sentence was protecting is intact and is what the spec now states: the audit sits below the `is_finalized()` guard and above pending-relation resolution, and only pure reads may precede it, because a read cannot mutate a collected class and so cannot disturb Phase 1's failure-atomic guarantee. `finalize_django_types`'s own comment makes the same argument at the materialization site.

### Decision 6 — Consumer-site routing semantics

**The claim this decision may no longer make, and it was FALSE WHEN WRITTEN.** The Decision 6 table row and the matching Slice 4 checklist bullet both said:

> `django_strawberry_framework/types/converters.py::resolved_relation_annotation` — pre-change `target_type = registry.get(...)`; post-change unchanged.

The helper never called `registry.get`. It has taken `target_type` as a **parameter** since commit `27d62919` (2026-05-07, `0.0.4`) — two releases before this card was written — and at `HEAD` it does nothing but shape the annotation (`list[T]` / `T | None` / `T`) from a `FieldMeta`. The "unchanged" half of the claim was true; the description of what was unchanged was not. Deleted rather than moved, per [`worker-1.md`][worker-1] rule 2: a builder could implement the sentence, and adding a registry lookup inside that helper would put primary resolution in two places. The reconciled row states what the helper actually is — a pure annotation shaper whose caller owns the resolution.

**A citation that rotted, in four places.** The spec cited the nested relation lookup as `optimizer/walker.py::_walk_selections #"registry.get(django_field.related_model)"`. That exact string is **absent from `walker.py` at `HEAD`**: commit `36da25b4` moved the lookup into `optimizer/walker.py::_resolve_relation_target`, which prefers `definition.related_target_for(...)` and falls back to `registry.get(related_model)`. Every occurrence is re-cited to `_resolve_relation_target`. The **contract** is untouched — both legs land on the primary, because `DjangoTypeDefinition.related_target_for` resolves its own target through `registry.get(target_model)`.

**A whole-spec citation sweep ran on top of the dispatched finding**, because a `#"substring"` citation breaks on reflow as well as on reword and one broken instance is evidence of a population, not of an incident. The spec carries twelve distinct `#"..."` citations; each was checked against the tree, and **five were unresolvable**:

| Citation | Occurrences | Disposition |
|---|---|---|
| `walker.py::_walk_selections #"registry.get(django_field.related_model)"` | 4 | Re-cited to `optimizer/walker.py::_resolve_relation_target`. |
| `tests/test_registry.py #"test_register_collision_raises"` | 3 | Deleted. The test is gone — this card's own checklist ordered it deleted, and the surviving boxes name the tests that replaced it. |
| `tests/types/test_base.py #"pre-finalize relation annotation"` | 2 | Deleted. It was never a real substring; it named a concept, and the spec's own bullet admitted as much ("verify against current tree before editing"). |
| `registry.py::TypeRegistry.register #"already_registered"` | 5 | Deleted with the pre-card prose that carried them. The substring still resolves inside `register` at `HEAD`, but only to the reverse-collision raise — it would send a reader to the wrong branch. |
| `types/finalizer.py::finalize_django_types #"target_type = registry.get"` | 6 | **Resolves; kept.** `finalize_django_types` contains `target_type = registry.get(pending.related_model)`. Two sibling assignments in the same module are outside the named symbol and do not shadow it. |

The remaining seven — `#"ALLOWED_META_KEYS"`, `#"if meta is None"`, `#"if resolved is None"`, `#"registry.get_definition(origin)"`, `#"registry.model_for_type(origin)"`, and the two `docs/GLOSSARY.md` entry citations — are **seven distinct citations at ten occurrences** (1 + 1 + 1 + 2 + 3 + 1 + 1), and all resolve inside the symbols they name. Seven distinct plus the five in the table above is the twelve the sweep started from; their ten occurrences plus the table's twenty — fourteen broken, and six for the kept `#"target_type = registry.get"` — is the **thirty** citation occurrences the sweep read.

### Decision 7 — Test strategy

**The claims this decision may no longer make:** that `tests/types/test_finalizer.py` "does NOT exist today", that `tests/types/test_relations.py` "does NOT exist today", that `tests/types/test_converters.py` is "~1455 lines", and the "create the new file only if the cluster outgrows the host" escape hatch built on all three. Both files exist at `HEAD` (created by later cards, not by this one), and `test_converters.py` is 2,210 lines. A shipped spec that poses a create-it-or-not question also reads as unfinished, so the reconciled Decision 7 names the hosts the tests actually landed in and stops there.

The build's own choices, which the spec now records as facts rather than as options: the `Meta.primary` validation tests went to `tests/types/test_base.py` (no `test_meta_primary.py` was created), the audit cluster split across `tests/test_registry.py` and `tests/types/test_definition_order.py`, and the relation-resolution cluster went to `tests/types/test_converters.py`.

### Decision 8 — `DjangoTypeDefinition.primary`

**The claim this decision may no longer make**, retracted by revision 5 and now stated positively rather than as a correction: that `definition.primary` is consumed by "the schema audit, the optimizer walker, future override-semantics work". It is not. The schema audit iterates `registry.iter_types()`; the optimizer's root planning receives the origin by `source_type=` threading; the ambiguity audit calls `registry.primary_for(model)`. The field is a per-type denormalization for introspection, and the prohibition on routing ambiguity decisions through it stays in the spec because it is a contract, not a derivation.

### Decision 9 — Optimizer origin-type propagation

**Alternatives rejected, and why each lost:**

- **Extending `registry.get(model)` to accept an origin hint.** Lost on two counts: the registry should not need to know about Strawberry types beyond the registered set, and the nested-relation path *wants* the primary lookup unchanged — so a parameter only the root path uses would invite call-site confusion. Threading the origin through the walker keeps the contract local to the optimizer subsystem.
- **Threading the origin past `plan_optimizations` into `_walk_selections` directly.** The spec left the call-graph detail open ("`plan_optimizations` may need a new keyword-only `source_type=` argument, or `_walk_selections` may need it threaded one level deeper ... the call-graph detail is an implementation choice"). What landed is the first option: `plan_optimizations` carries the keyword-only `source_type: type | None = None` and passes it into its single root `_walk_selections(...)` call, and `DjangoOptimizerExtension._get_or_build_plan` invokes it as `plan_optimizations(resolved_selections, target_model, info=info, source_type=origin)`. Reaching past `plan_optimizations` lost because it is the walker's public entry point: a caller that skipped it would have to re-derive the root-walk arguments the entry point derives once (`enable_only`, the runtime prefixes, the plan `finalize()` handoff). A shipped spec may no longer pose the choice, so the Slice 4 box now states the landed shape.
- **Threading `source_type` into `_selected_scalar_names` too.** Rejected by the rev-6 audit of the actual call graph, not by preference: that helper is invoked only from `_plan_select_relation`, where the model argument is `django_field.related_model` for nested FK-id elision and never a resolver's root return type. Threading a root origin into it would make a nested step plan against the root's field map. The audit's conclusion, and the regression test that pins the *root* path instead, both stayed in the spec, because this is precisely the "completion" a later builder would attempt.
- **A nested extension-cache path.** Rejected by the rev-6 scope audit: `DjangoOptimizerExtension._plan_cache` is root-only, `_get_or_build_plan` is its sole insertion site, and nested plans are built inside walker recursion without passing through `_build_cache_key`. The `origin` slot's `None` value is reserved for direct or test-only callers, not for a nested production path.

**Changes this decision has undergone:**

- **Rev 5 named `_resolve_model_from_return_type`** as the helper that computed the origin locally and discarded it, which is what made the rest of the threading buildable — a builder could otherwise update the walker and cache-key surfaces and still have no clean way to obtain `origin` at the extension call site.
- **Rev 6 pinned the failure contract**, and it was a correctness fix, not a clarification. Rev 5 told the builder to rewrite all four `_resolve_model_from_return_type` tests to assert a pair. Three of them are *failure* cases asserting `None`; asserting `(origin, None)` there would mean the helper returns a truthy pair on failure, and `_optimize`'s guard would send the walker a `None` model to dereference. The shipped contract is "return `None` whenever **either** half is unresolvable; return the pair only when both resolve", the success test asserts the pair, and the three failure tests still assert `None`.

**The open question this decision is no longer allowed to pose.** The spec deliberately left the return shape to the builder — "named tuple `Origin(origin, model)` or a plain `(origin, model)` tuple". What landed, in the original build commit, is `optimizer/extension.py::_OriginAndModel`, a `NamedTuple` with `origin` and `model` fields, so call sites read `resolved.origin` / `resolved.model` rather than unpacking positionally. The spec now names the landed shape.

### `## Slice checklist` — Slice 6

**Moved — the verbatim `DONE-018-0.0.6` KANBAN body.** Slice 6 reproduced the full card body inline as a fenced drop-in. All of it is moved. `KANBAN.md` is rendered from the fakeshop kanban app's database ([`START.md`][start] "Rendered docs"), so a verbatim copy in a spec drifts against the live card by construction, and the copy in this spec had already drifted: it carried the retired duplicate-primary message. The reconciled Slice 6 states the obligation (the card lands in Done with a body recording the slice-by-slice scope, authored in the DB and regenerated) and points here for the body as shipped:

```markdown
### DONE-018-0.0.6 — Multiple DjangoTypes per model with `Meta.primary`

Slice-by-slice scope (per `docs/spec-018-meta_primary-0_0_6.md`):

- Registry stores multiple types per model (`_types: dict[Model, list[Type]]`).
- New `Meta.primary: bool` flag (default `False`); validated in `_validate_meta`.
- `registry.register(..., *, primary: bool = False) -> bool` and
  `registry.register_with_definition(..., *, primary=...)` accept the flag.
  `register()` now returns `bool` indicating whether state was added; drives
  snapshot-restore rollback in `register_with_definition`.
- New registry surface: `primary_for(model)`, `types_for(model)`,
  `models_with_multiple_types()`.
- `registry.get(model)` returns the primary if declared, else the single
  registered type, else `None`. Multiple types with no primary is an
  ambiguous-pending state that the finalizer audits.
- `finalize_django_types()` runs `audit_primary_ambiguity()` first: any
  model with `>=2` registered types and no primary raises
  `ConfigurationError` naming the model and every registered class plus an
  actionable fix sentence.
- Two primary types for the same model: rejected at registration time
  with message `"<class> is already declared primary as <existing>"`.
- Relation conversion in `types/base.py` defers all **auto-synthesized**
  relation annotations to `finalize_django_types()` (eager-bind shortcut
  removed; eliminates the secondary-registered-before-source-before-
  primary import-order trap). The existing `consumer_authored_fields`
  short-circuit is preserved, so direct relation annotations (`category:
  AdminCategoryType`) and assigned `strawberry.field` resolvers continue
  to bypass synthesis entirely and may target a secondary `DjangoType`.
  `types/converters.py` and `types/finalizer.py` resolve auto-synthesized
  relations to the primary at finalize time.
- Optimizer planning threads the resolved origin Strawberry type from
  `optimizer/extension.py` through `plan_optimizations` to the walker's
  root `_resolve_field_map(model, source_type=origin)` call. Root planning
  uses the resolver's actual return type; nested relation steps continue
  to use `registry.get(related_model)` (the primary). Plan cache key
  includes the origin type so primary-return and secondary-return
  resolvers on the same model do not share a cached plan.
- Schema audit (`optimizer/extension.py`) iterates every reachable
  registered type via `registry.iter_types()` and dedupes warning
  collection. Secondary types whose relation fields the primary does not
  expose are still audited; identical-string duplicate warnings from
  overlapping field maps are collapsed.
- `model_for_type` continues to work for any registered type so
  secondary-type resolvers stay planable.
- `DjangoTypeDefinition` gains `primary: bool = False`.
- 100% coverage across `tests/test_registry.py`, `tests/types/test_base.py`,
  `tests/test_registry.py` / `tests/types/test_definition_order.py`
  (the existing finalize-test hosts), `tests/types/test_converters.py`
  (the existing relation-conversion host), and `tests/optimizer/`.

Design notes carried into `0.0.6`:

- Single-type-no-primary stays backward compatible: `registry.get(model)`
  still returns the lone type without requiring an explicit `primary` flag.
- `Meta.primary` is a per-class declaration, not a registry-level
  `set_primary(Model, Type)` mutation — keeps the contract immutable
  after `__init_subclass__` runs.
- Already-shipped consumer relation overrides (direct annotation
  `category: AdminItemType` and assigned `category = strawberry.field(...)`)
  stay in scope and are preserved by this card via the existing
  `consumer_authored_fields` short-circuit — they may legitimately
  target a secondary `DjangoType` after `Meta.primary` ships. A NEW
  declarative override API (e.g., `Meta.field_types = {...}`) is the
  `DONE-019-0.0.6 — Consumer override semantics` design space and
  is out of scope here.
```

Two of that body's statements are stale at `HEAD` and are recorded here rather than corrected, because it is a historical copy: `audit_primary_ambiguity()` is now `_audit_primary_ambiguity(multi_type_models)`, and the duplicate-primary message is now `"Cannot register <class> as primary for <model>; <existing> is already the primary type"`. The live `KANBAN.md` card is the maintainer's to reconcile, and this cycle's do-not-touch list covers it.

**Both stalenesses are properties of the copy reproduced above, and only one of them reaches the live board** — a distinction added 2026-08-18 after the copy and the board were measured separately. The board's rendering of that bullet is truncated mid-sentence at `#"runs \`audit_primary_ambiguity()\` first: any"`, and the sentence carrying the duplicate-primary message was never imported at all: the substring `declared primary` returns zero `CardItem` and zero `CardReference` rows board-wide. So the copy above is the *fuller* record of what the card once said, and reading it as a description of the live board over-counts the work owed there from two edits to one. Recorded because this file is the surviving copy and the conflation is easy to repeat from it.

**The self-contradicting move instruction.** Slice 6 read `move DONE-018-0.0.6 -> DONE-018-0.0.6`. The 2026-07-30 board renumber rewrote both halves of a `WIP-...-014` -> `DONE-014` status-flip instruction into the same post-renumber string. Deleted, not moved: it instructs nothing. The spec-017 cycle found the identical defect in its own Slice 6, so this is a defect *class* the renumber produced across the card series, not an isolated slip — any spec whose Slice 6 carries a card-status-flip instruction from before 2026-07-30 should be assumed to have it.

**Claims Slice 6 may no longer make:** that the spec is yet to be archived and archival is "the maintainer's call post-merge" (it sits at `docs/SPECS/spec-018-meta_primary-0_0_6.md`, its terms CSV and this file at `docs/SPECS/appx/`, moved by a later spec author's `docs/SPECS/NEXT.md` Step 8 sweep); and that `KANBAN.md` and `docs/GLOSSARY.md` are hand-edited (both render from `examples/fakeshop/db.sqlite3`).

### `## Risks and open questions`

**Moved.** The whole section, nine bullets. Each is settled, superseded, or restated in the spec as a contract:

- **`registry.iter_types()` semantic change.** Accepted and shipped; documented in the `CHANGELOG.md` `Changed` entry, and the in-tree consumer (the schema audit) dedupes rather than filters. No external consumer was known then or now.
- **Auto-synthesized relation binding moves entirely to finalize.** Accepted. The only observable difference is that `cls.__annotations__[field.name]` is `PendingRelationAnnotation` between `__init_subclass__` and `finalize_django_types()`; finalization is the documented synchronization point. Restated in the spec as a Goal and an Edge case rather than as a risk.
- **Multi-type declarations without `primary` are a registration-time silent success.** Accepted: the finalizer is mandatory for any usable schema, and the audit is where the actionable error belongs.
- **`Meta.primary` on a single-type declaration populates `_primaries` for no behavioral change.** Accepted; `primary_for` and `get` are distinct-but-equivalent there, and both are pinned by tests.
- **Concurrent landing with `DONE-019-0.0.6`.** Settled. `DONE-019-0.0.6` shipped in the same `0.0.6` release; the version-bump quintet was the expected no-op.
- **Already-shipped consumer relation override paths stay in scope.** Settled and restated in `## Non-goals` — with the correction that `DONE-019-0.0.6` widened the *annotation-and-assignment* override path to scalar columns rather than adding the `Meta.field_types` key the spec named as its territory. No such key exists on the `Meta` surface at `HEAD`.
- **Plan cache key shape.** Shipped. The key is per-process and re-populates on first use, so the change was forward-only with no invalidation step.
- **Optimizer origin-type plumbing.** Shipped; the call-graph detail the risk left open is pinned in Decision 9 and Slice 4.
- **`Meta.primary` on a `DjangoType` declared inside a test function.** Never a real risk; the autouse `registry.clear()` fixture covers it.

### `docs/FEATURES.md`

**A rationale note, not a spec edit.** The original build commit `8cec18a3` edited `docs/FEATURES.md`. That file no longer exists — a later docs consolidation deleted it (last touched at commit `40c1855f`, "housekeeping: rename files"). The spec's `## Doc updates` and Slice 6 never named it, so nothing in the spec is falsified by the deletion; it is recorded here only so a reader diffing the build commit against Slice 6 is not left wondering which side is wrong.

### The registry surface that grew after the card

**A rationale note, not a spec edit.** `TypeRegistry.unregister` (commit `b70c0360`, reshaped by `1fb42b04`, both 2026-05-19) and `TypeRegistry.register_type_teardown` (commit `c3767495`, 2026-07-13) are not this card's surface, but they share this card's `_primaries` / `_types` invariants, and `unregister` shares the rollback's `_detach_type_from_model` helper. The spec is deliberately **not** grown to describe them: a spec that documents a later card's surface stops being a record of what its own card contracted for, and the reader loses the ability to tell which card owns which behavior. Decision 2's entry above records the one thing a spec-018 reader genuinely needs — that `_detach_type_from_model` is shared, and that `_primaries` is deliberately outside it because the two callers disagree on the primary slot. **No spec sentence was added for this item.**

## Reconciliation record — what the spec now says, and why

The move and the reconciliation ran in one pass, so this file carries both records.

**Strategy.** State the contract that holds at `HEAD`, with no amendment block, no retraction paragraph, and no "as of revision N" hedge — the spec must read as though it had been right from the start ([`docs/builder/BUILD.md`][build] `## Spec rationale extraction`). Where a later card superseded a mechanism, the spec describes the *current* mechanism and this file records the old one. Where the spec posed a question the build answered, the spec now states the answer.

**Section by section — only the reconciliations with no keyed entry above.** The `### Decision N` and `### <spec heading>` entries in `## Entries keyed to the spec` are the record for everything they cover; repeating them here would give a reader two tellings of one change, so the per-Decision, `## Current state`, header, Slice 3 and Slice 4 bullets that used to sit in this list were deleted rather than kept in parallel. What remains is what nothing above records. (Two edits that had no keyed home and would otherwise have been lost with those bullets: Decision 9's heading lost its `(H2 fix)` suffix and the two in-page anchors pointing at it were updated in the same pass; the Slice 4 `_optimize` root-planning box was rewritten from an open implementation choice to the landed `plan_optimizations(..., source_type=origin)` call shape.)

- **`## Key glossary references`.** The `Meta.primary` bullet's `Currently planned for 0.0.6; flipped in Slice 6` framing replaced with `shipped (0.0.6)`. The `Relation handling` bullet rewritten from "today binds … / after this card" to the single contract that now holds.
- **`## Slice checklist` Slice 1.** The duplicate-primary assertion repointed at what the test asserts. The two "Worker 1 picks during planning" boxes rewritten to what landed. The `_already_registered("as", ...)` "message is recycled" note replaced with the contract. `models_with_multiple_types`'s one-shot-generator nature stated, since it is why the finalizer materializes it.
- **Slice 2.** The stale-test box rewritten to the option the build took.
- **Slice 5 and Slice 6.** Authoring-time chronology removed from the version-bump framing; the prior-`0.0.6`-card note corrected to name the four cards that actually share the release; the verbatim KANBAN body replaced by the generated-doc procedure and a pointer here; the archival bullet rewritten to describe where the spec now lives.
- **`## Problem statement`.** The pre-card registry behavior re-framed as what the card lifted, so no sentence in it is false read against `HEAD`.
- **`## Non-goals` / `## Out of scope`.** The two `DONE-019-0.0.6` forward references rewritten: the card shipped, and it shipped a widening of the annotation-and-assignment override path rather than the `Meta.field_types` key the spec named.
- **`## Edge cases and constraints`.** The two round-labelled chronology parentheticals (the plan-cache "L1 fix" and the idempotency "L3 fix") replaced by the contracts they were correcting toward.
- **`## Test plan`.** The `H1` / `H2` / `H3` regression labels renamed to the contract each pins (`Always-defer`, `Root-origin`, `Reachable-secondary`), since the severities they referenced only meant something inside the revision history that has now left the spec.
- **`## Definition of done`.** The audit name and signature, the duplicate-primary message, the nested-lookup symbol, the version-bump chronology, and the KANBAN "verbatim body" phrasing all corrected.
- **Link scaffold.** `[start]` added under `<!-- Root -->`; `[spec-017]` and `[spec-018-rationale]` added under `<!-- docs/SPECS/ -->`; two bare `spec-017-…md` filename mentions converted to reference-style links. One in-page anchor was repaired: `#decision-3a--registerwithdefinition-rollback-shape` did not resolve, because the heading's `register_with_definition` keeps its underscores under GitHub's slug rules. Every remaining in-page anchor resolves against a heading. `check_spec_glossary.py` re-run to exit 0 at `OK: 15 terms`.

### What this cycle deliberately did not fix

- **Any code change.** The audit found no gap and no defect, so no code round was opened.
- **The live `KANBAN.md` card body**, which still carries the public `audit_primary_ambiguity()` name. It renders from the fakeshop kanban DB, which this cycle's do-not-touch list covers; the stale statement is recorded under the Slice 6 entry above. **Corrected 2026-08-18:** this bullet also named the retired duplicate-primary message, which the live board does not carry — that half belongs to the verbatim copy reproduced under Slice 6, not to the board. Homed as one edit, not two, on `TODO-ALPHA-052-0.1.0`.
- **Standing-doc staleness generally** (`docs/GLOSSARY.md`, `CHANGELOG.md`, `docs/README.md`, `TODAY.md`). All four were verified to reflect shipped state for this card and none needed an edit.
- **The `#metaprimary` in-page-shaped link inside Slice 6's glossary drop-in.** It does not resolve against a heading in the spec, and must not: it is text to be written into `docs/GLOSSARY.md`, where the anchor is real. Left verbatim so the drop-in stays character-identical to its destination.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[start]: ../../../START.md

<!-- docs/ -->
[glossary-definition-order-independence]: ../../GLOSSARY.md#definition-order-independence
[glossary-plan-cache]: ../../GLOSSARY.md#plan-cache

<!-- docs/SPECS/ -->
[spec-018]: ../spec-018-meta_primary-0_0_6.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md
[worker-1]: ../../builder/worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
