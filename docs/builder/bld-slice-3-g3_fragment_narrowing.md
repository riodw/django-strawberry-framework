# Build: Slice 3 — G3 — fragment type-condition narrowing (DEFERRED — procedural closure)

Spec reference: `docs/spec-035-optimizer_hardening-0_0_10.md` (Slice-3 checklist line 56; Decision 6 lines 223-258; Decision 7 lines 260-272; deferred G3 test plan lines 364-381; DoD items 6-8 lines 443-449; Out-of-scope entry line 416; Revision 3 line 15)
Status: final-accepted

This is a **procedural-closure slice** (BUILD.md "Procedural-closure slices"). The spec's contract for Slice 3 is to **ship nothing in this card**: G3's fragment type-condition narrowing is DEFERRED to the follow-up *abstract-return optimizer entry* card (the `BACKLOG.md` `polymorphic_interface_connections` work, or a dedicated card) because it has no reachable production trigger today. Closed via a single Worker 1 pass that writes this combined Plan + Final-verification block, sets `Status: final-accepted` directly, and cites the spec clauses authorizing the closure. **No Worker 2 build, no Worker 3 review.**

## Plan + Final verification (Worker 1, combined — procedural closure)

### (a) Spec contract for Slice 3 = a DEFERRAL

The spec does not direct any runtime code to land for G3 in spec-035. The deferral is authorized by these clauses, read against the live spec:

- **Slice-3 checklist line (spec line 56), marked `**[deferred]**`** — "Slice 3: G3 — fragment type-condition narrowing — **moved to the abstract-return optimizer entry card; no runtime code in spec-035.**" The spec deliberately uses the `**[deferred]**` marker, **not** a `- [x]` box, because no shipped behavior exists to tick.
- **Decision 6 (spec lines 223-258)** — opens with "**Status: DEFERRED — carry-forward requirements, no runtime code in spec-035.**" A production-reachability review (Revision 3) established the narrowing has no reachable trigger today: an interface / union root field never enters the walker because `extension.py::_resolve_model_from_return_type` resolves the abstract `origin` and `registry.model_for_type(origin)` returns `None`, so `_optimize` passes the queryset through before the walker (and any fragment classifier) runs. The decision is "retained verbatim as the design contract for the follow-up *abstract-return optimizer entry* card." It carries the carry-forward requirements R1-R3 (lines 252-258).
- **Decision 7 (spec lines 260-272)** — opens with "**Status: DEFERRED — carry-forward requirement, no runtime code in spec-035.**" The "Reachability and the deferral decision" paragraph (line 270) records that G3 has "no reachable trigger at all today," and the "**Decision (maintainer, Revision 3): defer G3 entirely from spec-035.**" paragraph (line 272) pins the maintainer's choice and notes "G3 lifts cleanly out of this card without touching G1 / G2 (the seam is independent). spec-035 ships G1 + G2 + the doc wrap."
- **Revision 3 (spec line 15)** — "**Decision (maintainer, this review): G3 ships no runtime code in spec-035.** Slice 3 moves to a follow-up *abstract-return optimizer entry* card … The G3 analysis here … is retained verbatim as **carry-forward requirements**."
- **Out-of-scope entry (spec line 416)** — "**G3 — fragment type-condition narrowing (the audit's third guard)** — deferred to the abstract-return optimizer entry card … No reachable production trigger today … the full design … is retained as that card's carry-forward requirements."
- **DoD items 6-8 (spec lines 443-449), marked `*(deferred)*`** — "Items 6-8 are the **follow-up card's** contract (abstract-return optimizer entry), retained here as carry-forward. spec-035 does **not** need them satisfied to complete."
- **Build-plan flag** (`build-035-optimizer_hardening-0_0_10.md` "Build-wide context flags", "G3 (Slice 3) DEFERRED — ships no runtime code"): "**Slice 3 is a procedural-closure slice**: a single Worker 1 pass sets `Status: final-accepted` directly, citing spec Decision 6/7 and the deferral clause (no Worker 2 build, no Worker 3 review)."

### Spec slice checklist (verbatim — deferred, NOT ticked)

The spec's Slice-3 entry from `## Slice checklist` (spec line 56) is a single `**[deferred]**`-marked bullet, not a `- [ ]` checkbox. Copied verbatim; it is left as deferred (no `- [x]` is ticked, because no shipped behavior exists):

- **[deferred]** Slice 3: G3 — fragment type-condition narrowing — **moved to the abstract-return optimizer entry card; no runtime code in spec-035.** The design (tri-state classifier shape, the union interface-name collection, the secondary-type / unknown-composite rules, the `_selected_scalar_names` second-consumer concern, the registry name-resolution + ambiguity contract, and the abstract-return production-entry contract that must exist *first*) is retained as carry-forward requirements in [Decision 6](#decision-6--g3--registry-only-fragment-type-condition-narrowing) / [Decision 7](#decision-7--g3--narrow-do-not-multi-plan) and the [G3 test plan](#slice-3--g3--deferred-carry-forward-requirements-for-the-abstract-return-optimizer-entry-card). Rationale: G3 has no reachable production trigger today — an abstract root field never reaches the walker ([`registry.model_for_type`][registry] returns `None` for the interface / union origin, so [`_optimize`][extension] passes through), so shipping the classifier here would be synthetic-only ([Current state](#current-state); Revision 3 above).

### DRY analysis

Not applicable in the build sense — this slice ships no code, so it introduces no duplication and no new helper. The single relevant DRY observation is preserved as a spec carry-forward (Decision 6 R2): the fragment inliner `selections.py::included_field_selections` has **two** walker consumers (`walker.py::_walk_selections` and `walker.py::_selected_scalar_names`), so the follow-up card's classifier must either thread through both or prove the second only sees concretely-typed child selections. Recording it here keeps the next author from re-discovering the second consumer.

### (b) Final verification — no G3 runtime code shipped; carry-forward preserved

Verified against the live checkout at commit `3c2b0427` ("Remove 034 bld artifacts"). On-disk working tree carries only the G1/G2 build edits (`optimizer/walker.py`, `types/resolvers.py`, the three test files) plus this build's docs/artifacts; none of those touch G3 narrowing.

**1. No G3 narrowing code shipped.**

- `django_strawberry_framework/optimizer/selections.py::included_field_selections` still has the signature `included_field_selections(selections: list[Any]) -> list[Any]` — **no `classifier` parameter, no `fragments_only` parameter**. Its body still inlines every fragment body unconditionally: `if is_fragment(selection): result.extend(included_field_selections(...))` with no type-condition match against any planning type. The tri-state (`INLINE` / `SKIP` / `RECURSE_FRAGMENTS_ONLY`) classifier Decision 6 describes is absent from runtime code.
- `django_strawberry_framework/optimizer/walker.py` has **not** added a type-condition classifier. Both inliner call sites — `walker.py::_walk_selections` (`merged = _merge_aliased_selections(_included_field_selections(selections))`) and `walker.py::_selected_scalar_names` (`for sel in _merge_aliased_selections(_included_field_selections(selections))`) — call the bare inliner with **no narrowing predicate** passed. The tokens `classifier` / `fragments_only` / `RECURSE_FRAGMENTS_ONLY` appear in `walker.py` only inside the `# TODO(spec-035 Slice 3)` comment Pseudocode (lines 322-328 and 839-843), never as executable code.
- `grep -rn "RECURSE_FRAGMENTS_ONLY\|fragments_only\|type_condition" django_strawberry_framework/optimizer/` confirms: `RECURSE_FRAGMENTS_ONLY` and `fragments_only` appear **only** inside `# TODO(spec-035 Slice 3)` Pseudocode comments (`selections.py` line 319, `walker.py` lines 322-328 / 839-843). Every `type_condition` hit is the pre-existing **fragment marker** usage — the inline-fragment shell builder (`selections.py::convert_selection` #"`type_condition=(condition.name.value if condition is not None else None)`" and #"`type_condition=fragment.type_condition.name.value`"), the `is_fragment` duck-type discriminator (`selections.py::is_fragment` #"`return hasattr(selection, "type_condition")`"), the runtime-prefix clone (`selections.py::with_runtime_prefix` #"`type_condition=selection.type_condition`"), and the `extension.py` cache-key adapter comments. **No `type_condition` is matched against a planning type anywhere in the walker** — exactly the "verified absent" state Decision 6 / Current state describe.

**2. Slice-3 source-site TODO anchors are intact.** The two `# TODO(spec-035 Slice 3)` anchors Slice 2's Worker 2/3 deliberately left in place correctly stage the deferred work and name the spec/slice:

- `walker.py::_walk_selections` #"TODO(spec-035 Slice 3): supply a registry-only type-condition classifier" (line 322) — the primary planning-seam anchor. Pseudocode covers the full accept-set design (own GraphQL name + declared/MRO-inherited interface names; skip known sibling concretes; recurse fragments-only for unknown composite/union; never accept the model primary name on model match; no graphql-core introspection). Sits immediately above the live `_included_field_selections(selections)` call at line 329.
- `walker.py::_selected_scalar_names` #"TODO(spec-035 Slice 3): audit this FK-id-elision helper as the walker's second" (line 839) — the R2 second-consumer anchor. Pseudocode pins the R2 choice (share the classifier or prove the helper only sees concretely-typed relation child selections). Sits immediately above the live `_included_field_selections(selections)` call at line 845.
- (Companion anchor, the inliner definition itself) `selections.py::included_field_selections` #"TODO(spec-035 Slice 3): add a tri-state fragment classifier" (line 315) — stages the parameter additions on the primitive, with the default path kept "byte-for-byte unconditional."

All three name `spec-035 Slice 3` and carry NotImplementedError-free Pseudocode (per AGENTS.md, no call path must fail loudly here — the deferred narrowing has no production trigger, so a pass-through is the correct current behavior, not a loud failure).

**3. Carry-forward design preserved in the spec for the follow-up card.**

- Decision 6 R1-R3 (spec lines 252-258): R1 (abstract-return production-entry contract — the precondition), R2 (both walker inliner consumers must use the classifier), R3 (non-Relay name-resolution + ambiguity contract) all present verbatim.
- Decision 7 (spec lines 260-272): narrow-not-multi-plan posture and the maintainer's "defer G3 entirely" decision both present.
- Deferred G3 test plan (spec lines 364-381): present, including the P3a no-regression note on the live `GenreType` test and the R2/R3 test entries (`test_selected_scalar_names_uses_same_classifier`, `test_non_relay_sibling_name_lookup_and_ambiguity`).

**Spec status/header re-verification (per Worker-1 per-spawn duty).** Spec lines 1-9 describe G3 as deferred ("G3 deferred", "ships no runtime code here") and the closure state as "G1 shipped; G2 + the doc wrap remain; G3 deferred." This is accurate relative to the build: G2 (Slice 2) is final-accepted and Slice 4 (doc wrap) genuinely remains. No status-line edit needed.

**Spec edit decision.** No genuine inconsistency found: no G3 runtime code is accidentally present, the deferral is fully and consistently recorded across the Slice checklist, Decisions 6/7, Revision 3, Out-of-scope, and DoD items 6-8, and the carry-forward (R1-R3 + test plan) is intact. **No spec edit was needed.**

### Spec changes made (Worker 1 only)

None. No genuine inconsistency was found; the card correctly ships no G3 runtime code and the carry-forward design is preserved in the spec for the follow-up abstract-return optimizer entry card.

### Summary

Slice 3 (G3 — fragment type-condition narrowing) is closed as a **procedural closure** with `Status: final-accepted` and **no runtime code shipped**, exactly as the spec's deferral contract directs (Slice-3 checklist `**[deferred]**` marker, Decision 6/7 DEFERRED status banners, Revision 3 maintainer decision, the Out-of-scope entry, and DoD items 6-8 marked `*(deferred)*`). Live-checkout verification at commit `3c2b0427` confirms: `selections.py::included_field_selections` still inlines fragments unconditionally with no `classifier` / `fragments_only` parameters; `walker.py` added no type-condition classifier (both inliner call sites pass no predicate); `type_condition` appears only as a fragment marker, never matched against a planning type; the `RECURSE_FRAGMENTS_ONLY` / `fragments_only` tokens live only in `# TODO(spec-035 Slice 3)` Pseudocode. The two Slice-3 source-site TODO anchors in `walker.py` (the `_walk_selections` planning seam and the `_selected_scalar_names` R2 second-consumer) plus the `selections.py` inliner anchor are intact and correctly name the spec/slice. The carry-forward design (Decision 6 R1-R3, Decision 7 narrow-not-multi-plan, the deferred G3 test plan) is preserved verbatim in the spec for the follow-up card. No Worker 2 build or Worker 3 review ran; no spec edit was needed.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[extension]: ../../django_strawberry_framework/optimizer/extension.py
[registry]: ../../django_strawberry_framework/registry.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
