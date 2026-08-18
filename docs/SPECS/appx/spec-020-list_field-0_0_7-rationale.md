# Rationale: spec-020 — `DjangoListField` (non-Relay list) (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-020-list_field-0_0_7.md`][spec-020]. The spec is the contract and states only what holds at `HEAD`; everything that explains **how it got there** lives here: six numbered revisions of review feedback, the alternatives each of the ten Decisions rejected, the four surviving risks and the four that were folded away, and every claim the spec once made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass.

## Provenance of this record

**This pass performed a MOVE, not a reconstruction.** Spec-020 carried an unusually heavy deliberative layer: a 56-line inline `Revision history (kept inline so the spec is self-contained)` block enumerating six review rounds with their H / M / L sub-items, 119 `(revN Xn)` attribution parentheticals outside that block - one on very nearly every normative sentence in the spec (checklist, decisions, implementation plan, edge cases, test plan, doc updates, definition of done), a `Justification:` block under seven of the ten Decisions, an `Alternatives considered (and rejected):` list under eight of them, and a four-item `## Risks and open questions` section written as preferred-answer / fallback pairs.

**Measured byte counts, `wc -c` at this working tree:**

| File | Before this pass | After |
|---|---|---|
| `docs/SPECS/spec-020-list_field-0_0_7.md` | 151,236 | 85,576 |
| `docs/SPECS/appx/spec-020-list_field-0_0_7-rationale.md` | 0 (did not exist) | see note below |

The spec shed 65,660 bytes. This file is smaller than that, and the difference is not a copy that went missing: it is the `(revN Xn)` attributions themselves (they are attributions, not arguments — an entry recording *what* a round changed carries the round once, not once per touched sentence), the sentences that only repeated a contract stated elsewhere in the spec, and the handful of passages the current contract falsifies, which were **deleted** rather than moved per [`worker-1.md`][worker-1] rule 2. A byte count of this file written by the pass that is still writing it would be a guess, so the figure is left to the measurement the pass reports to Worker 0 rather than asserted here.

`HEAD` at the time of the pass is `8a80218e`. The package is at `0.0.14`; this card shipped at `0.0.7` on 2026-05-27 (`CHANGELOG.md #"## [0.0.7] - 2026-05-27"`).

**The card shipped as `016`, not `020`.** The spec was authored as `docs/spec-016-list_field-0_0_7.md`; the scaffolding landed in commit `6adbe630` ("Ready for docs/spec-016-list_field-0_0_7.md", 2026-05-20) and the build in `7e8632f6` ("Start …", 2026-05-20) and `06c8df92` ("Finish …", 2026-05-21), with `e01873ae` ("Archive 016", 2026-05-21) moving it under `docs/SPECS/`. The 2026-07-30 board renumber moved the card from `016` to `020` and renamed the spec; `CHANGELOG.md`'s tracking label still reads `016-djangolistfield_non_relay_list-0.0.7`, and `KANBAN.md` still carries a `[spec-016]` reference id pointing at the `020` filename. Both numbers name one card. Do not chase `git log` for "spec-020".

**Moved** — cut from the spec by this pass, and now only here:

- the whole `Revision history (kept inline so the spec is self-contained)` block, all six revisions with their H / M / L sub-items;
- every `(revN Hx)` / `(revN Mx)` / `(revN Lx)` / `(Rev3 M2: …)` / `(rev6 post-Slice-0 reconciliation …)` attribution parenthetical in the spec body — the change each one records is now in this file under the decision it touched;
- the `Justification:` block under Decisions 1, 2, 4, 5, 6, 7, 9 and 10, and the equivalent `Justification:` clauses inside `## Non-goals`, `## Borrowing posture` and `## User-facing API`;
- the `Alternatives considered (and rejected):` list under Decisions 1, 2, 3, 4, 5, 6, 8, 9 and 10;
- Decision 1's paragraph on the two rev1 mechanisms that do not survive contact with the installed Strawberry;
- Decision 3's `Option A` / `Option B` weighing of helper placement;
- Decision 5's `Why not validate at type-decoration / finalization time:` block;
- Decision 9's `Card-text departure` paragraph;
- the whole `## Risks and open questions` section, its four items and the rev3 L2 note explaining how eight items became four;
- `## Current state`'s historical-citation parenthetical about the pre-ship `__all__` tuple and its deliberation about why `library`, not `products`, hosts the example;
- the dropped `## Slice checklist` sub-check and the dropped `## Test plan` test that rev2 H2 retired.

**Reconciled in place** — the contract sentence stays in the spec and only its chronology was cut:

- **Slice 0's stub bullet.** The reason a bare `lambda root, info: ...` cannot verify the class-body-discovery contract (`strawberry.field(resolver=...)` raises `MissingArgumentsAnnotationsError` at call time, before `@strawberry.type`'s class-body walk runs) is implementation-relevant and stays; the framing that it was "originally pinned here" and later reconciled is gone.
- **Slice 1's `resolver=` bullet and Decision 2's pseudo-code.** The absence of a runtime-coroutine fallback is now stated as a property of the contract, not as a record of the round that removed the branch.
- **Decision 4's two-test paragraph.** The distinction between the return-shape contract and the end-to-end contract stays, because it is why both tests exist; the reviewer-flagged-duplication narration is gone.
- **Decision 9's opening sentence.** The `order_by("id")` dependency that makes replacement unsafe stays; the "rev1 picked `all_library_branches` for replacement" chronology is gone.

**Kept in the spec deliberately, against the pull of this move.** [`worker-1.md`][worker-1]'s carve-out for implementation-relevant rationale is load-bearing here, and five passages exercised it:

- **Decision 2's "Async-detection asymmetry — intentional, not a harmonization candidate".** It exists precisely to stop a future maintainer harmonizing the two detection mechanisms. Moving it out would leave the spec showing two mechanisms with no reason, which is an invitation.
- **Decision 2's module-scope-helpers comment**, including why `_default` bypasses `_post_process_consumer_*` and why the `_consumer` suffix is in the names. A builder who never reads it either re-indents the helpers into the factory body or "fixes" the asymmetry.
- **Slice 1's N802 note.** Why the per-line `noqa` beats a per-file ignore is a build instruction, not deliberation.
- **The `functools.partial` edge case with both code blocks.** The silent-skip mechanism and the rewrap-in-`async def` workaround are what a consumer debugging the symptom needs; only the "rev5 chose YAGNI" framing was cut.
- **Decision 5's registration-guard anchor.** That the attribute is assigned only when a `DjangoType` subclass carries a `Meta` with a `model` is what makes the check non-arbitrary; without it the check looks like superstition. The passage was kept for that reason and its `hasattr` framing was **false at `HEAD`** — the shipped guard is deliberately stricter. R1 corrected it; see [Decision 5](#decision-5--validation--error-shapes) below for the correction and for why a "kept deliberately" list is not a verified list.

**In-page anchors in this file slug the heading's rendered text, not its source.** The decision headings here are reference-style - a bracketed link label followed by its ref-id - so the rendered heading - and therefore the anchor - is the link text alone: `#decision-5--validation--error-shapes`. R1's first pass appended the ref-id to three of them, two inside `## Verified against the shipped code`, the section whose whole job is lookup; all three are corrected. The postcondition that catches this is the whole-file anchor sweep run over **this** file and not only the spec. Two shapes it exists to catch: a heading whose text ends in a ref-id, whose slug covers the label only, and a heading whose text is a code span beginning with `##`, whose slug keeps a leading hyphen (`#-definition-of-done`).

**Deleted outright rather than moved**, per [`worker-1.md`][worker-1] rule 2, because the current contract falsifies them:

- `Status: draft (revision 6, post-rev5 scaffolding review).` — the card shipped in `0.0.7` and the spec is archived. Replaced with the shipped status line.
- The Predecessors line's `(was DONE-020-0.0.7 until Slice 5's column move)` — a renumber artifact that named the same id on both sides of "was".
- **Definition of done item 1's claim that the field carries "the runtime `inspect.iscoroutine` fallback per rev4 H2".** Revision 5 H1 deleted that fallback from the design; the DoD item was never reconciled and shipped contradicting Decision 2, the Slice 1 checklist and the Edge cases section. It is a claim the decision may no longer make — see [Claims the spec may no longer make](#claims-the-spec-may-no-longer-make).
- `## Current state`'s "(Historical citation: before `DjangoListField` shipped in `0.0.7`, this re-export tuple did NOT include `DjangoListField` …)". The bullet already describes a pre-card baseline; the parenthetical asserted the ship in a spec whose own status line said "draft".
- The three Slice checklist bullets' "spec-016 scaffold TODOs" wording, reduced to "the scaffold TODOs at this site". The number was the card's pre-renumber identity, and the file list beside it is unambiguous; keeping a `016` in a `020` spec reads as a cross-spec dependency that never existed. The identity is recorded once, above.
- Decision 5's `(Rev2 H2: nullable_list= is NOT a constructor argument …)` parenthetical and Definition of done item 7's `(Rev2 H2: no nullable_list= argument …)` trailer. Both were records of a removal; the constructor signature in Decision 5 and the argument list in Decision 2 already show no such parameter.

**Glossary anchors: twenty-four terms, twenty-four anchors, all still linked** (`scripts/check_spec_glossary.py` exits 0 before and after). Two terms lost their only carrier to this move and were re-homed in reconciled prose:

- **`DjangoConnection`** was carried only by the revision-2 L1 item, which quoted the stale `docs/TREE.md` line `connection.py # [alpha] DjangoConnectionField + DjangoListField`. Re-homed on Decision 8's boundary bullet, which now reads "returns a `DjangoConnection` (`Connection[T]`)" with the reference-style glossary link on the symbol.
- **`plan cache`** was carried only by Decision 6's second `Justification:` bullet. Re-homed as a normative sentence in Decision 6: two `DjangoListField`s pointed at two types on one model produce two distinct plan-cache entries, because plan-cache keys include the resolver's origin Strawberry type.

## Entries keyed to the spec

Every entry below names the spec section or Decision it belongs to. An entry that names no decision cannot be looked up.

### The `Status:` line

Shipped as `Status: draft (revision 6, post-rev5 scaffolding review).` and stayed that way through archival. The line was falsified twice over: by the `0.0.7` release on 2026-05-27, and by `e01873ae` moving the file under `docs/SPECS/`. Revision 4 M2 had already corrected this line once — it read `draft (revision 1, initial)` while the body carried revisions through rev3 — which is evidence that a status line narrating a revision number is a line that goes stale silently. The replacement names the release, the date, the archival and the card, and carries no revision number.

### `Revision history`, revisions 1-6

The spec's own framing was "kept inline so the spec is self-contained". Six rounds, each an adversarial review of the prior draft; two of them (rev3, rev5) reviewed against a `feedback2.md` scratch file that no longer exists.

**Revision 1 — initial draft.** Pinned module location (`list_field.py`), symbol shape (a field-descriptor **class** with `__call__` semantics returning a `StrawberryField`), the default-resolver contract (`Meta.model._default_manager.all()` → `cls.get_queryset(qs, info)`), sync + async `get_queryset` cooperation mirroring spec-011 Decision 9, consumer-resolver override semantics, optimizer cooperation by root-gating with no new walker code, the `Meta.primary` interaction, public-export discipline, test placement across `tests/test_list_field.py` and `examples/fakeshop/test_query/test_library_api.py`, and a library-app boilerplate-**removal** proof.

**Revision 2 (post-feedback review)** — three high, three medium, two low:

1. **H1** — rev1 said a consumer-supplied `resolver=` owns the queryset completely and `cls.get_queryset(...)` is NOT applied, claiming graphene-django parallelism. The graphene-django source does the opposite: `graphene_django/fields.py::DjangoListField.list_resolver` calls `maybe_queryset(django_object_type.get_queryset(queryset, info))` on any `QuerySet`, not only the default-manager fallback. Flipped the contract to parity; a consumer who wants the bypass returns an already-evaluated Python `list`, which the field detects the same way `optimizer/extension.py::DjangoOptimizerExtension._optimize #"if not isinstance(result, models.QuerySet):"` does. Retired `test_djangolistfield_consumer_resolver_override_bypasses_default`; added `test_djangolistfield_consumer_resolver_queryset_return_gets_get_queryset_applied`.
2. **H2** — rev1's "subclass `strawberry.field`" mechanic is not implementable: `strawberry.field` is a function, not a class, in the installed Strawberry. Rev1 also had `DjangoListField` returning a `StrawberryField` from `__set_name__`, which cannot replace the already-assigned class attribute. Rewrote Decisions 1 and 2 around one mechanism — a **factory function** returning `strawberry.field(resolver=..., …)`. The constructor lost `nullable_list=`; outer nullability moved to the consumer's class-attribute annotation. Dropped `test_djangolistfield_nullable_list_toggle_renders_nullable_outer`; added `test_djangolistfield_nullable_outer_via_consumer_annotation` and `test_djangolistfield_non_nullable_outer_default_via_consumer_annotation`.
3. **H3** — rev1's `def _default_resolver(type_cls, info)` passed the target `DjangoType` as the first argument, but Strawberry calls a resolver with the GraphQL root value. `type_cls.__django_strawberry_definition__` would have been looked up on the `Query` root instance and failed. `target_type` moved to closure capture.
4. **M1** — rev1 replaced `all_library_branches`, which carries `order_by("id")` that `test_library_relation_override_shapes_http_response_data` depends on ("Override" before "Override East"), and `Branch` has no `Meta.ordering`. Three options: (a) keep the existing resolver and **add** a sibling `all_library_branches_via_list_field`; (b) replace it with `DjangoListField(BranchType, resolver=…)` preserving the ordering; (c) add `class Meta: ordering = ("id",)` to `Branch`. Picked **(a)** — zero blast radius, and the new field exercises the default-resolver path without the ordering coupling.
5. **M2** — rev1's live HTTP test was to assert `cls.get_queryset` had been applied, which would have required a custom `get_queryset` on the real `BranchType` and thereby changed every `BranchType` path in the library schema, nested `book → shelf → branch` selections included. Moved all `get_queryset` coverage to package-internal tests with isolated fixtures; the HTTP test proves only the end-to-end pipeline and the optimizer plan.
6. **M3** — rev1 promised "root and nested fields", but the optimizer extension is root-gated on `info.path.prev is None`. Narrowed the `0.0.7` contract to **root list fields only**, added the scope-narrowing paragraph to Decision 4, and pinned it with `test_djangolistfield_at_root_position_is_optimized`.
7. **L1** — the doc-updates section added `list_field.py` to the `docs/TREE.md` target layout without removing the stale `DjangoListField` mention on the `connection.py # [alpha] DjangoConnectionField + DjangoListField` line, which would have advertised two homes for one symbol.
8. **L2** — the CHANGELOG entry said "root and nested fields"; after M3 that over-promised. Narrowed to "**root** Query fields".

**Revision 3 (post-rev2 review against `feedback2.md`)** — the reviewer audited the rev1 draft rather than the rev2 update, so three feedback items were already pre-empted: feedback2 H1 (the `order_by` loss — pre-empted by rev2 M1), feedback2 H4 (annotation-vs-`nullable_list=` ambiguity — pre-empted by rev2 H2), and feedback2 L1 + L4 (the `__call__` wording and the `nullable_list` bool-check test recipe — pre-empted by rev2 H2). Feedback2 L2 was a confirmation that the test counts were internally consistent, not a defect. The rest landed as one high, six medium, two low:

1. **H1 (feedback2 H3)** — rev2 H2 pinned the factory-function shape but nothing had demonstrated it end-to-end in this codebase; every example, test and slice rested on `@strawberry.type` picking up the factory's return value. Added **Slice 0 — Pre-implementation verification**, a throw-away spike that must confirm the shape before Slice 1 touches `list_field.py`, with the `StrawberryField`-constructed-directly fallback named as the escape hatch.
2. **M1 (feedback2 H2)** — the spec repeatedly said "the joint `0.0.7` cut card", inviting a reader to look in `KANBAN.md` for a sixth card that does not exist. Reworded five sites to "**the last `0.0.7` card to ship**". The Decision 10 heading kept "Joint `0.0.7` cut" because it names a policy, not a card. Adding a real release-cut card was ruled a separate `KANBAN.md` edit, out of this spec's boundary.
3. **M2 (feedback2 M1)** — the preamble carried a `Card line:` block quoting the `DONE-020-0.0.7` card. The quoted sentence was not verbatim from the card body, which has Why-it-matters bullets, Verified-in-upstream, Definition of done and Files-likely-touched, and no one-line summary matching it. The block was removed and the card cited by ID only. (The removal note itself — `(Rev3 M2: the Card line: block that previously appeared here was removed …)` — survived in the spec until this pass, which is the same defect one layer up: a spec narrating its own deletion.)
4. **M3 (feedback2 M2)** — Decision 5's "registered DjangoType" check needed a code anchor, so the assignment site `types/base.py::DjangoType.__init_subclass__ #"cls.__django_strawberry_definition__ = definition"` was cited to show `hasattr` is a sufficient discriminator.
5. **M4 (feedback2 M3)** — several line-number citations were off by one or two. Verified against `HEAD`: `_apply_get_queryset_sync`'s start was one line off, `_apply_get_queryset_async`'s likewise, `_optimize`'s was correct and the reviewer's claim about it was wrong, and `_resolve_model_from_return_type` was being cited as if its call site were its definition. All were converted to symbol-qualified paths.
6. **M5 (feedback2 M4)** — `CHANGELOG.md` already had a `[0.0.7]` section from earlier commits in the same patch, so the doc-updates bullet was tightened to **append**, never create a second heading.
7. **M6 (feedback2 M5)** — Decision 4 mandated an optimizer test in `tests/test_list_field.py` while Slice 4 routed the same coverage through the live HTTP test, which reads as duplication against `AGENTS.md`'s test-through-real-usage rule. The duplication is intentional and was justified explicitly: the package test pins the return-shape contract, the HTTP test pins the end-to-end contract.
8. **M7 (feedback2 M6)** — pinned `from strawberry.utils.inspect import in_async_context` as the import, verified against `types/relay.py`, so no reader has to grep for it and no fork appears.
9. **L1 (feedback2 L3)** — Decision 9's "21 lines for cosmetic gain" was arithmetically loose: replacing seven three-line resolvers with seven one-line attributes is roughly a **-14** line delta, not **+21**. Reworded to "churn that doesn't pin the contract any harder than one addition does".
10. **L2 (feedback2 L5)** — the Risks section had eight items, several of which restated Decisions. Folded three into their owning Decision's alternatives ("ergonomics of the explicit-target shape" and the `for_model` sugar → Decision 6; `null=True` on the item type → Decision 2) and trimmed the section to four genuinely open items.

**Revision 4 (post-rev3 review, the second adversarial pass)** — three high, two medium, one low:

1. **H1** — every resolver signature used `def resolver(root, info, **kwargs)` with `info` unannotated. On the installed Strawberry both halves fail schema construction: unannotated `info` raises `MissingArgumentsAnnotationsError`, and an annotated `**kwargs: Any` is treated as a GraphQL argument named `kwargs` and later fails with `Unexpected type 'typing.Any'`. Rewrote every signature to `(root: Any, info: Info)` and dropped `**kwargs` entirely; GraphQL arguments belong to the Layer-3 filter/order cards, each of which adds its own named, typed parameters.
2. **H2** — `_wrap` checked `isinstance(result, (Manager, QuerySet))` against the **immediate** return of `user_resolver(root, info)`. For an `async def` consumer resolver that immediate return is a coroutine, the check is False, the coroutine passes through, Strawberry awaits it downstream, and `target_type.get_queryset(...)` is silently skipped — breaking the rev2 H1 parity contract for exactly the consumers least likely to notice. The factory now inspects `inspect.iscoroutinefunction(user_resolver)` at construction time and builds an `async def _wrap` that awaits **before** the isinstance check. Added `test_djangolistfield_async_consumer_resolver_queryset_return_gets_get_queryset_applied` and `test_djangolistfield_async_consumer_resolver_python_list_return_passes_through`; Slice 3 went from 11 to 13 tests. Rev4 also specified a runtime `inspect.iscoroutine(result)` fallback for detection misses, which **rev5 H1 removed** (below).
3. **H3** — the add-only posture no longer satisfied the card's Definition of done, which said "Live HTTP coverage **replacing** one of the hand-rolled `all_library_*` resolvers". Three options: (a) reverse to replacement via `DjangoListField(BranchType, resolver=lambda root, info: Branch.objects.order_by("id"))`, which works under rev2 H1 but stops exercising the **default**-resolver path — the whole reason rev2 M1 chose to add; (b) keep add-only and record the departure explicitly, updating the card body at Done; (c) keep add-only and additionally replace one of the other six, which carry the same `order_by("id")` risk. Picked **(b)**.
4. **M1** — the Borrowing posture attributed the `Manager → QuerySet` coercion entirely to `DjangoOptimizerExtension._optimize`, contradicting the Decision 2 pseudo-code. The **field wrapper** must coerce before calling `get_queryset`, or the visibility hook receives a `Manager` where a `QuerySet` is expected for every `Model.objects` return. Both coercions co-exist: one for visibility-hook correctness inside the field, one as a downstream safety net at the extension boundary for non-`DjangoListField` root resolvers.
5. **M2** — the `Status:` line still said `draft (revision 1, initial)`, and the implementation-plan prose said "ships as five commits" while the table had six rows. Both corrected.
6. **L1** — two add-vs-replace residues survived rev2 M1: `TODAY.md`'s bullet said "if the new resolver replaces a hand-rolled one", and `## Current state` said "where one resolver-replacement is enough to pin the contract end-to-end". Both rewritten to add-only language.

**Revision 5 (post-rev4 review against the second pass of `feedback2.md`)** — three high, four medium, three low; precision and grounding work, no architectural backtracking:

1. **H1** — rev4 H2's runtime-fallback branch (`if inspect.iscoroutine(result):` inside the sync `_wrap`) is reachable (a `functools.partial`-wrapped async resolver reaches it) but was pinned by no test, so it would fail the `fail_under = 100` gate. Three options: (a) drop the fallback as YAGNI; (b) keep it and add a 14th behavior test; (c) `# pragma: no cover`, which the repo reserves for genuinely unreachable branches. Picked **(a)** — the sync `_wrap` calls the post-processing helper directly, and a consumer with a partial rewraps it in `async def`, which the Edge cases section documents.
2. **H2** — Decision 2 carried two async-detection mechanisms with no explanation, and a future maintainer could "harmonize" them and break the design. Added the asymmetry paragraph: the default body dispatches **per-call**, the consumer wrapper **per-construction**, and harmonizing either loses sync-callability or adds a coroutine layer per call.
3. **H3** — `from strawberry.types import Info` was asserted as canonical but not grounded; Strawberry also exposes `strawberry.Info`, and module paths shift between minor versions. Added a Slice 0 checkbox that verifies the import against the installed Strawberry, with `strawberry.Info` (or, less likely, a version bump) as the fallback.
4. **M1** — Slice 3's delta-table prose double-counted "default resolver" / "sync `get_queryset` invocation" (one test) and under-counted `Meta.primary` (two tests). The "13" total was right by accident. Rewritten to match the named methods one-to-one.
5. **M2** — rev3 M4's sweep had over-wide spans for `_apply_get_queryset_async` (the next symbol starts immediately after) in both Decision 3 and `## Current state`. Replaced with symbol-qualified paths.
6. **M3** — `test_djangolistfield_async_get_queryset_is_awaited` pins an `async def get_queryset`, but not the dual-execution case the runtime `in_async_context()` branch depends on: `in_async_context()` True with a **sync** `get_queryset`. Added `test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution`; Slice 3 went 13 → 14 and the file total 17 → 18.
7. **M4** — the post-processing helpers were written as module-level functions whose bodies referenced `info`, a name that exists only in the wrapper's parameter list. Pasting the pseudo-code verbatim gives `NameError: name 'info' is not defined` on the first call. `target_type` and `info` became explicit parameters.
8. **L1** — `def DjangoListField(...)` is PascalCase and `pyproject.toml` selects `N` (pep8-naming), so N802 would fail the `ruff check` gate. The PascalCase is intentional graphene-django parity, so a per-line `# noqa: N802` with a stated reason was added. A per-file ignore was considered and rejected: `list_field.py` has exactly one PascalCase definition, and a file-wide exception would hide future violations.
9. **L2** — the rev3 M4 history entry listed before/after citation pairs that read as identical, because it was describing what rev3 had landed rather than what rev3 changed. Trimmed to the citations that genuinely shifted.
10. **L3** — the Test-plan heading descriptor was trimmed to match `AGENTS.md`'s more compact "package tests, system-under-test is `django_strawberry_framework`" framing.

**Revision 6 (post-rev5 scaffolding review against `feedback2.md`)** — three high, six medium, three low; all surfaced during hands-on scaffolding contact with the rev5 pseudo-code:

1. **H1** — `_default` wrapped the `_apply_get_queryset_async` call in an inner `async def _async_path()` whose only job was to await it. `_apply_get_queryset_async` is already `async def`, so calling it returns a coroutine that Strawberry's `AwaitableOrValue` dispatch awaits directly; the wrapper added a coroutine layer per invocation for nothing. Collapsed to `return _apply_get_queryset_async(target_type, qs, info)`.
2. **H2** — the pseudo-code was internally contradictory about helper placement: the leading comment said "Module-scope post-processing helpers" while the indentation put them inside `def DjangoListField(...)`. An implementer pasting it would pick one and lose the other. Pinned module scope — referentially transparent, unit-testable independently of the factory, and the `_apply_get_queryset_*` imports are already importable at module load under Decision 3's Option A.
3. **H3** — the helpers were named `_post_process_sync` / `_post_process_async`, implying they handle every queryset return, when `_default` bypasses them entirely. The bypass is justified (`_default` knows `qs` came from `Manager.all()`, so no coercion and no isinstance branching is needed) but the names hid it. Renamed to `_post_process_consumer_sync` / `_post_process_consumer_async`, with a comment recording the bypass.
4. **M1** — the Risks section claimed Strawberry picks up the factory's return value "via `__set_name__`". Mechanically wrong: discovery happens in `@strawberry.type`'s decorator-time class-body walk, which iterates `cls.__dict__` and converts annotated attributes and `StrawberryField` instances into the type's field list. `__set_name__` is the descriptor-protocol hook and is not what Strawberry uses. Corrected to the class-body-walk wording.
5. **M2** — Slice 0's "confirm the field is picked up" left the verification mechanism unspecified, inviting `print(schema)` or SDL substring assertions, both fragile across Strawberry minor versions. Pinned an introspection query with the exact `kind` / `ofType` assertions at each depth.
6. **M3** — the User-facing API's "Custom resolver override" showed only the sync shape, so a consumer reading it as the one-stop reference would conclude async is unsupported. Added an `async def` example using `asgiref.sync.sync_to_async`, since Django's sync-by-default ORM is the typical case.
7. **M4** — the `functools.partial` workaround was compressed into a single inline phrase. Replaced with two code blocks, the broken shape and the working one, because a reader debugging a silent skip needs the before/after.
8. **M5** — the `GOAL.md` doc-update bullet said "update the migration shape sections … when relevant", which is unfalsifiable. Verified that `GOAL.md #"### Coming from \`graphene-django\`"` is the migration subsection and that the Success-criteria mention is already accurate, then named the specific heading and the specific one-line addition.
9. **M6** — `test_djangolistfield_at_root_position_is_optimized` is the single regression net for the root-only contract, but its assertion shape was unpinned; `assertNumQueries(2)`, `assertNumQueries(<= 5)` and SQL-string sniffing measure different things, and a permissive bound lets a per-query-count change slide past. Pinned the exact count, with the derivation (one base SELECT plus one per prefetched relation) documented in the test docstring.
10. **L1** — the rev5 H3 Slice 0 bullet asked to confirm `Info.__module__ == 'strawberry.types.info'` "(or the path the installed Strawberry uses)", which makes the equality non-falsifiable: any module path passes. Dropped the equality; kept import resolution as the criterion and the module path as a recorded observation.
11. **L2** — the rev5 scaffolding pass left `# TODO:` comments in six touched files (`django_strawberry_framework/list_field.py`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `tests/test_list_field.py`, `examples/fakeshop/apps/library/schema.py`, `examples/fakeshop/test_query/test_library_api.py`). Ruff's `ERA001` catches commented-out code but not `# TODO:` markers, so explicit cleanup sub-bullets were added to Slices 1, 3 and 4.
12. **L3** — the Slice 3 line-delta estimate still read `+260 / -0` after the rev5 M3 test was added; refreshed to `+280 / -0`. A rename of the column to "order-of-magnitude line delta" was considered and not adopted, on the grounds that revisions 1-5 all used the precise-looking shape.

### [Decision 1 — Module location, mechanism, & public export][spec-020-d1]

**Rejected alternatives.**

- **Bundle into `connection.py` from `DONE-030-0.0.9`.** Rejected: forces `0.0.7` to author a module whose primary tenant ships in `0.0.9`; `connection.py`'s API will be substantially richer (edges / pageInfo) and bundling leaks naming ambiguity.
- **Inline into `__init__.py`.** Rejected: `__init__.py` is a re-export hub today, not a module body; a definition there violates the existing convention.
- **A `fields/` subpackage with `fields/list_field.py`.** Rejected: the target layout in `docs/TREE.md #"## django_strawberry_framework (current on-disk layout)"` reserves subpackages for Layer-3 subsystems with three or more modules; a single file is a flat module.
- **Subclass `strawberry.field`** (rev1's mechanism). Not viable: `strawberry.field` is a function in the installed Strawberry, not a class.
- **Return a `StrawberryField` from `__set_name__`** (rev1's mechanism). Not viable: `__set_name__` cannot replace the already-assigned class attribute with its return value.

**The positive arguments for `list_field.py`** (the moved `Justification:` block): the card's "Files likely touched" entry named `list_field.py` and `connection.py` as alternatives; `docs/TREE.md` documents flat single-file Layer-3 modules at the package root (`fieldset.py`, `permissions.py`, `connection.py`) as the canonical placement; `DjangoConnectionField` is the future tenant of `connection.py`, so bundling would force either two unrelated symbols in one module or a later rename; and the `docs/TREE.md #"tests/test_<module>.py (flat, at the root)"` mirror rule pairs `tests/test_list_field.py` with `list_field.py` automatically.

**Changes, with the round that caused each.** rev2 H2 replaced the whole mechanism (descriptor class → factory function) and is the reason the spec's consumer-facing shape survived unchanged while its internals were rewritten. rev5 L1 added the N802 `noqa` requirement. rev5 H3 grounded the `Info` import and gave Slice 0 the verification bullet.

**Changed by R1 (spec-vs-code reconciliation round, 2026-08-18) (F9).** The decision's placement conclusion held, and Decision 8's rejected-alternatives block had predicted the factoring that followed: "the better factoring is shared helpers ... both fields use the same helpers without an inheritance relationship". What actually landed puts those helpers in the module Decision 1 argued should stay narrowly focused. `list_field.py::_validate_djangotype_target` and `::_validate_relay_djangotype_target` are now the single site for field-target validation, imported by `connection.py` and by `relay.py` (both take the Relay-shaped variant; the four-guard base is reached through it). The spec gained a paragraph saying so, because "where does a guard change land" is a fact about the module this spec created and a reader cannot derive it from the decision as written. **Rejected while writing it:** relocating the guards to `utils/` and pointing the spec there instead — three factories already import them from `list_field.py`, so the spec would then describe code that does not exist, which is the defect this round is closing.

**Claims this decision may no longer make:** that `DjangoListField` is a class; that `__call__` or `__set_name__` participates in the mechanism; that the factory owns or overrides the consumer's annotation; that `list_field.py` holds only the list field's own concerns.

### [Decision 2 — Default resolver shape][spec-020-d2]

**Rejected alternatives.**

- **Default resolver returns a Python `list` after `qs.all()` evaluation.** Rejected: the root-resolver `_optimize` hook checks `isinstance(result, models.QuerySet)` (`optimizer/extension.py::DjangoOptimizerExtension._optimize #"if not isinstance(result, models.QuerySet):"`), so a `list` return breaks N+1 cooperation outright.
- **Skip `cls.get_queryset` application on consumer-resolver returns** (rev1's contract). Rejected by rev2 H1: graphene-django applies `get_queryset` to consumer-resolver `QuerySet` returns too, so rev1 both weakened the visibility hook and misdescribed the package it claimed parity with. The corrected contract keeps an explicit bypass — return a Python `list` — without making the bypass the default.
- **`nullable_list=` constructor argument** (rev1's design). Rejected by rev2 H2: Strawberry already reads the class-attribute annotation, so the kwarg would either fight it or silently override it, and honoring it would mean constructing a `StrawberryField` directly instead of going through `strawberry.field(...)` — a real complexity bump for something the consumer expresses with one extra `| None`.
- **First-positional `(type_cls, info)` resolver signature** (rev1's pseudocode). Rejected by rev2 H3: Strawberry calls resolvers with `(root, info)`. The target type must come from closure — the same shape as graphene-django's `partial(self.list_resolver, django_object_type, …)`.
- **Catch-all `**kwargs` in the resolver signature** (used defensively in the rev1, rev2 and rev3 pseudocode). Rejected by rev4 H1: Strawberry treats every parameter as a GraphQL argument, so an annotated `**kwargs: Any` becomes an argument named `kwargs` and fails schema construction with `Unexpected type 'typing.Any'`, while an unannotated one fails earlier with `MissingArgumentsAnnotationsError`. Filter/order/search arguments land in `DONE-027-0.0.8` / `DONE-028-0.0.8` / `TODO-BETA-047-0.1.2` with named, typed parameters.
- **Accepting `null=True` on the item type** (folded in from the rev2 Risks list by rev3 L2). Rejected for `0.0.7`: Django querysets never yield `None` rows, so `list[T | None]` is meaningless at the resolver layer. Revisit only if a Layer-3 filter returning sparse results needs it.
- **A runtime `inspect.iscoroutine(result)` fallback** in the sync wrapper (rev4 H2's design). Removed by rev5 H1 as YAGNI and as an uncoverable branch under `fail_under = 100`; the two alternatives weighed against dropping it were adding a 14th behavior test for the partial case and a `# pragma: no cover`, the latter against the repo's convention that the pragma is for genuinely unreachable branches.
- **An inner `async def _async_path()` wrapper** inside `_default` (rev5's shape). Removed by rev6 H1: `_apply_get_queryset_async` is already a coroutine function, so the wrapper only added a redundant coroutine layer.
- **Factory-scope placement of the post-processing helpers** (ambiguous in rev5's pseudo-code). Rejected by rev6 H2 in favor of module scope: referentially transparent, independently unit-testable, and the imports are available at module load.

**The positive arguments for the shape** (the moved `Justification:` block): `model._default_manager.all()` matches both graphene-django (`graphene_django/fields.py::DjangoListField.get_manager`) and the package's own Relay default (`types/relay.py::_initial_queryset`); `cls.get_queryset(qs, info)` is the load-bearing visibility hook, so the field must apply it to **every** queryset-shaped return, default or consumer; returning a `QuerySet` rather than a `list` is what lets the shipped root-gated optimizer plan apply; and reusing the Relay helpers keeps one source of truth for sync/async detection rather than shipping a second mechanism.

**Changes, with the round that caused each.** rev2 H1 (apply `get_queryset` to consumer returns), rev2 H2 (factory shape, annotation-driven nullability), rev2 H3 → rev4 H1 (signature), rev4 H2 (async consumer wrapper), rev4 M1 (the wrapper owns the `Manager → QuerySet` coercion), rev5 H1 (fallback removed), rev5 H2 (asymmetry documented), rev5 M4 (`target_type` / `info` as explicit helper parameters), rev6 H1 (no inner async wrapper), rev6 H2 (module-scope helpers), rev6 H3 (`_consumer` names).

**Changed by R1 (spec-vs-code reconciliation round, 2026-08-18) (F1, F3, F4, F5).** Four independent drifts, all in the pseudo-code sketch and the paragraphs around it:

- **F1 — the helper names were dead symbols.** The sketch imported `_apply_get_queryset_sync` / `_apply_get_queryset_async` from `types/relay.py`; `grep -ro '_apply_get_queryset_sync\|_apply_get_queryset_async' django_strawberry_framework/ tests/ examples/ | wc -l` returns **0**. The shipped helpers are `utils/querysets.py::apply_type_visibility_sync` / `::apply_type_visibility_async`, plus `::initial_queryset` for the seed and `::post_process_queryset_result_sync` / `_async` for the consumer coercion. The sketch's imports and every call site in it were rewritten.
- **F3 — the constructor signature was missing the row bound.** `max_rows=` / `trusted_max_rows=` shipped with spec-047, and with them a second constructor error site (`resource_policy.py::validate_collection_bound`). The sketch, the User-facing API section (which gained a `### Row bound` subsection), the Slice 1 metadata bullet and Definition of done item 8 all now carry it.
- **F4 — the async predicate was the wrong one.** The sketch and the asymmetry paragraph both named `inspect.iscoroutinefunction`. The shipped predicate is `utils/typing.py::is_async_callable`, and the spec now says explicitly that `iscoroutinefunction` is **not** used and why (it returns `False` for a `functools.partial` around an `async def` and for an `async def __call__` instance). This is the retraction that mattered most to a reader: the Edge cases section was instructing consumers to hand-rewrap a partial that works.
- **F5 — a third arm.** Async generator resolvers, and sync resolvers returning an async-only iterable, are both supported and bounded; an async-only iterable met from sync execution raises `SyncMisuseError` via `list_field.py::_require_async_iterable_context`. The two-way sync/async split the decision described is now a three-way one.

**Rejected while writing it:** keeping the sketch at its authored level of abstraction and describing the drift in prose beside it. A sketch that names helpers which do not exist is not an abstraction, it is a wrong instruction, and a builder reading it writes the import that fails. **Also rejected:** expanding the sketch to the shipped file verbatim — the module is 283 lines and the sketch's job is the shape, so it carries the three arms, the bound-applied-last ordering and the real symbol names without the docstrings.

**Changed again by R1's apply-changes pass (M2).** The three-arms paragraph and the async-detection-asymmetry bullet both enumerated `is_async_callable`'s coverage closed at three spellings. Both now defer to the predicate and name the `staticmethod` descriptor; the sweep blindness that produced the closed lists, and the reason no site re-enumerates the shapes, are recorded once under [`## User-facing API`](#-user-facing-api).

**Claims this decision may no longer make:** that `is_async_callable` sees exactly three async spellings; that a consumer resolver's return bypasses `get_queryset`; that `nullable_list=` exists; that the resolver takes `**kwargs`, or takes the target type first; that a runtime coroutine check backs up the construction-time detection; that the helpers are named `_post_process_sync` / `_post_process_async` or live in the factory body; that the visibility helpers live in `types/relay.py` under `_apply_get_queryset_*` names; that `inspect.iscoroutinefunction` is the construction-time predicate; that a consumer resolver is either sync or `async def` and nothing else; that the field returns an unbounded queryset.

### [Decision 3 — `get_queryset` and async symmetry][spec-020-d3]

**The placement question, weighed and deferred.** Two options were considered for `_apply_get_queryset_sync` / `_apply_get_queryset_async`:

- **Option A** — leave them in `django_strawberry_framework/types/relay.py` and import them into `list_field.py`.
- **Option B** — relocate them to a shared `django_strawberry_framework/utils/get_queryset.py` so both modules import from a neutral site.

`0.0.7` picked **Option A**: Option B is a refactor with a wider blast radius (the `types/relay.py` tests are extensive and reference the helpers by name), the helpers are not public surface, and the cross-module import is one line. Option B becomes the right move at the third call site — likely `DjangoConnectionField` in `DONE-030-0.0.9` — at which point that card owns the relocation. The same question is the third item in the moved Risks section, with the same answer and "relocate; blast radius is one import update" as its fallback.

**Rejected alternatives.**

- **Inline copies of `_apply_get_queryset_*` in `list_field.py`.** Rejected: two sources of truth for the coroutine-in-sync rejection contract, so a future change to the message has to touch both.
- **A `list_field.py`-local async-detection mechanism.** Rejected: forks the in-tree `in_async_context()` usage and makes the suite validate one contract twice.

**Changes, with the round that caused each.** rev3 M7 pinned the `in_async_context` import path. rev3 M4 and rev5 M2 corrected the helper citations (the `_apply_get_queryset_async` span was over-wide in both the original spec and rev3's correction of it).

**Changed by R1 (spec-vs-code reconciliation round, 2026-08-18) (F1, F12) — Option A was reversed, exactly as this decision predicted.** The decision named its own reversal condition: "Option B becomes the right move at the third call site — likely `DjangoConnectionField` in `DONE-030-0.0.9`". That condition occurred, and the relocation went further than Option B's `utils/get_queryset.py` sketch: the helpers now live in `utils/querysets.py` as `apply_type_visibility_sync` / `apply_type_visibility_async`, shared by the Relay node defaults, the connection root, this field and the cascade. The spec's Decision 3 was rewritten to state that placement as the contract, with no chronology; the Risks item "Async helper relocation" is thereby resolved and stays retired here.

The same rewrite absorbed **F12**, and it is a contract change rather than a citation fix. The helpers are no longer thin hook-appliers. spec-045's sealed-execution-queryset hardening rebuilt them into a validating boundary: the source and the hook's result are each sealed into a fresh framework-owned `QuerySet` rebuilt from validated query state, and every unprovable return fails closed — a `Manager` degrading to a non-queryset, a silently re-routed database, a `.values()` projection on a read surface, an instance-shadowed `all`, a sliced result a later recomposition would reorder. So "call the hook and use what comes back" is no longer a true description of this field's `get_queryset` cooperation, and the spec now says what actually holds, naming the seven `tests/test_list_field.py` tests that pin it. spec-034's cascade reaches the field through the same seam and needs no field-side code, which is why the cascade **non-goal** was reworded rather than deleted.

**Rejected while writing it:** leaving Decision 3 as a placement decision and homing the sealed boundary in Decision 4 (optimizer cooperation) instead. The seal is a property of the visibility-hook application, not of the optimizer, and splitting them would leave a reader who consults Decision 3 for the hook contract with the pre-spec-045 answer.

**Changed again by R1's apply-changes pass (L2).** The sealed-helper consumer list read closed at four - the Relay node defaults, the connection root, this field, the cascade - where `apply_type_visibility_sync` / `apply_type_visibility_async` have call sites in eight modules outside the defining one (`types/relay.py`, `connection.py`, `list_field.py`, `permissions.py`, `filters/sets.py`, `types/resolvers.py`, `optimizer/walker.py`, `mutations/resolvers.py`). The load-bearing clause is the one before the list - that this is the single site every recomposing read surface uses - so the list is now explicitly illustrative rather than completed. **Rejected:** enumerating all eight. A spec-side census of consumers is a count that goes stale on the next read surface to ship, and the closed-enumeration shape is what produced M2 and undercounted F1 twice in this one cycle.

**Claims this decision may no longer make:** that the sealed visibility helpers have four consumers; that the helpers live in `types/relay.py`; that they are named `_apply_get_queryset_sync` / `_apply_get_queryset_async`; that the relocation is deferred; that a `get_queryset` override's return value is used as returned; that the sync-path rejection raises a bare `ConfigurationError` rather than the named `SyncMisuseError` subclass.

### [Decision 4 — Optimizer cooperation][spec-020-d4]

**Rejected alternatives.**

- **Bypass the root gate for `DjangoListField`.** Rejected: there is nothing to bypass — the gate already fires at the root.
- **Extend the optimizer hook to recognize nested `DjangoListField` and plan there too.** Rejected: an optimizer change is out of scope for `0.0.7`, and the connection card has the same need, which makes it the right home for the broader nested-optimization design.
- **Add a `DjangoListField`-specific marker on `info.context`** so the optimizer can recognize the field. Rejected: unnecessary — the existing return-type machinery already identifies the target type, and no marker improves the plan.

**The positive argument** (the moved `Justification:` line): the optimizer's contract is "give me a `QuerySet` at the root; I'll walk the selection tree once", so a primitive that produces a `QuerySet` inherits every shipped optimizer feature for free.

**Changes, with the round that caused each.** rev2 M3 added the root-only scope narrowing and `test_djangolistfield_at_root_position_is_optimized`. rev3 M6 supplied the justification for keeping both the package-internal and the HTTP test, replacing the earlier "this is the regression net against accidentally returning a `list`" wording with the two-contract framing. rev3 M4 corrected `_resolve_model_from_return_type` from reading as a definition site to naming the call site and the definition separately. rev6 M6 pinned the exact-count assertion.

**Changed by R1 (spec-vs-code reconciliation round, 2026-08-18) (F11) — citations, not reasoning.** `optimizer/extension.py::_resolve_model_from_return_type` still exists and is still called from `::DjangoOptimizerExtension._optimize`, so the decision's contract ("give me a `QuerySet` at the root") is intact. Two details drifted: the resolver now returns an `_OriginAndModel | None` pair rather than a bare model, and `_optimize`'s `Manager` coercion is delegated to the shared `utils/querysets.py::normalize_query_source`. Both citations were corrected in place and nothing in the reasoning moved.

**Claims this decision may no longer make:** that the contract covers nested non-root positions; that a permissive query-count bound is acceptable for the root-optimization test; that `_resolve_model_from_return_type` returns a model; that `_optimize` carries its own `Manager` coercion.

### [Decision 5 — Validation & error shapes][spec-020-d5]

**Why validation fires in the constructor** (the moved `Why not validate at type-decoration / finalization time:` block): the rules are local to the constructor and need no cross-class state; failing at construction puts the error on the line that wrote `DjangoListField(...)`, which is easier to localize than a delayed `finalize_django_types()` error; and it is symmetric with `OptimizerHint`-related `Meta` validation firing at type creation.

**Rejected alternatives.**

- **Defer validation to `finalize_django_types()`.** Rejected: a consumer does not necessarily call `finalize_django_types()` before expecting `DjangoListField(...)` to work or fail, and delayed errors are harder to localize.
- **Accept a model class instead of a `DjangoType`.** Rejected: with `Meta.primary` shipped, model → `DjangoType` lookup is ambiguous when several types share a model. Requiring the explicit type side-steps it entirely (see Decision 6).

**Changes, with the round that caused each.** rev2 H2 removed the `nullable_list` bool check and its test `test_djangolistfield_rejects_non_bool_nullable_list`. rev3 M3 added the `__init_subclass__` assignment-site anchor behind the `hasattr` discriminator.

**Changed by R1 (spec-vs-code reconciliation round, 2026-08-18) (F2, F3) — and the `hasattr` anchor this move deliberately KEPT in the spec was the false one.** The provenance section above records `Decision 5's hasattr(arg, "__django_strawberry_definition__") anchor` under "Kept in the spec deliberately", on the reasoning that it is what makes the check look non-arbitrary. The reasoning was sound and the sentence was false: the decision asserted "abstract `DjangoType` bases without that condition pass through `__init_subclass__` without the attribute, so `hasattr(...)` is a sufficient discriminator", and the shipped guard is deliberately stricter for exactly the reason the assertion overlooked. `list_field.py::_validate_djangotype_target` uses `definition is None or getattr(definition, "origin", None) is not target_type`, and its docstring gives the hole: **the attribute is inherited via MRO**, so `hasattr` would accept a subclass that omits its own `Meta` and bind the field to a target whose definition, `Meta.primary` state and model all belong to the parent. A fifth validation test exists for it (`tests/test_list_field.py::test_djangolistfield_rejects_djangotype_subclass_without_own_meta`), and the shipped error message differs from the one the decision quoted. The spec now states the own-class-origin identity as the invariant and says in terms that `hasattr` is NOT sufficient.

F3 added the row-bound guard to the same decision: a non-positive `max_rows` is rejected by `resource_policy.py::validate_collection_bound` at the constructing line, so the decision's "one new error site" became two.

**The lesson worth carrying: a rationale move's own "kept deliberately" list is not a verified list.** It records why a passage was not moved, which is a judgement about its genre, not a check of its truth. This one passage was read three times in one cycle — once when deciding to keep it, once when writing the keep down as a considered choice, once in the sentence claiming the anchor is what makes the check coherent — and its falsity survived all three, because every read was asking "is this deliberation or instruction?" and none was asking "is this true?".

**Rejected while writing it:** softening the spec to "`hasattr` is broadly sufficient, and the shipped guard is stricter". A guard documented as looser than it is invites a later reader to "simplify" it back and silently re-open the parent-definition binding.

**Changed again by R1's apply-changes pass (M1, D1).** The first pass wrote that guard up as "a fifth check", one sentence after asserting that guard order is load-bearing, and shipped it runs **first**: `django_strawberry_framework/list_field.py::DjangoListField` calls `validate_collection_bound` before `django_strawberry_framework/list_field.py::_validate_djangotype_target`, so `DjangoListField("not-a-class", max_rows=0)` reports the `max_rows` error and never reaches the target guards. An ordinal is a claim about order, made in the one paragraph whose subject is order, so the decision states the position directly: the row-bound guard first, the four target checks ordered among themselves. The narrowing/widening restatement is gone from this decision and replaced by a pointer to `### Row bound`, which leaves Decision 5 with only its own subject - the guard.

**Rejected while writing it:** keeping "a fifth check" and appending "(which runs first)". Two orderings in one clause is how a reader who takes the ordinal literally gets produced in the first place.

**Claims this decision may no longer make:** that the row-bound guard is a fifth check running after the target guards; that the constructor validates a `nullable_list` argument; that `hasattr(arg, "__django_strawberry_definition__")` is a sufficient registration discriminator; that the constructor has one error site; that the constructor signature ends at `directives=()`.

### [Decision 6 — `Meta.primary` interaction][spec-020-d6]

**Rejected alternatives.**

- **Accept a model class and look up the primary `DjangoType`.** Rejected: needs a registry call at construction time and makes the field implicitly subject to `Meta.primary` reordering, which is brittle.
- **Default to the primary when an ambiguous model is passed.** Rejected: same brittleness; the explicit target is unambiguous.
- **Add a `DjangoListField.for_model(Model)` classmethod sugar** (folded in from the rev2 Risks list by rev3 L2). Rejected for `0.0.7`: `DjangoListField(MyType)` is the canonical form and matches both graphene-django's `DjangoListField(_type)` and the existing relation-side `category: AdminCategoryType` annotation-override path. Revisit only if real `Meta.primary` adopters report ergonomic pain.

**The positive argument** (the moved `Justification:` bullets): the explicit-target shape is what the existing relation-resolver paths already do for multi-type-per-model targets — annotation overrides and assigned `strawberry.field` relation resolvers can name a secondary type unchanged; and the optimizer's plan-cache keys include the resolver's origin Strawberry type, so a primary-return and a secondary-return field never share a cached plan. The second half of that argument was re-homed into the spec as a normative sentence, because it was the only carrier of the `plan cache` glossary link.

### [Decision 7 — Scope boundary vs relation list fields][spec-020-d7]

**The positive argument** (the moved `Justification:` line): relation many-side resolvers ship today and are well tested, so rewriting them under `DjangoListField` is a refactor with no consumer-visible benefit and a non-trivial blast radius. The two primitives coexist cleanly because they target different call sites — a root `Query` attribute versus a generated relation resolver.

No alternatives were enumerated under this Decision; the unification question is explicitly handed to the connection spec (`DONE-030-0.0.9`), and that hand-off stays in the spec because it assigns ownership.

### [Decision 8 — Out-of-scope boundary with `DjangoConnectionField`][spec-020-d8]

**Rejected alternatives.**

- **A single `DjangoField` symbol with a `connection=True/False` argument.** Rejected: the two return shapes differ (`list[T]` versus `Connection[T]`), so one symbol would carry two return-type contracts selected by a boolean, fragmenting the annotation story.
- **Inherit `DjangoConnectionField` from `DjangoListField`.** Rejected: the connection field's output machinery (edges, pageInfo) does not compose as a subclass; the better factoring is shared helpers — `_apply_get_queryset_sync` / `_apply_get_queryset_async` today, a future `_optimizer_root_gate` helper — used by both fields without an inheritance relationship.

**Changed by R1 (spec-vs-code reconciliation round, 2026-08-18) (F6, and the shared-helper prediction under F9).** The boundary line listed only pagination, edges, `pageInfo` and Relay arguments; it was silent on **ordering**, which is the other place the two primitives deliberately diverge. `list_field.py::DjangoListField`'s docstring already pinned it: a `DjangoListField` guarantees no row order unless the query supplies `orderBy` or the model declares `Meta.ordering`, while `DjangoConnectionField` appends a pk tiebreaker because its positional cursors require a total order. The spec's boundary line now carries both halves plus the reason the asymmetry is deliberate (a flat list has no cursors an unstable order could invalidate), and the User-facing API section's expected-behavior list carries a pointer, because a reader who never reaches Decision 8 is exactly the reader who assumes list order is stable.

The rejected alternative above also **came true in its positive half**: the shared helpers exist and both fields use them without an inheritance relationship. Where they live is F9's subject, recorded under Decision 1.

**Claims this decision may no longer make:** that the boundary between the two primitives is only about pagination shape; that the helpers named in the rejected alternative still carry those names.

### [Decision 9 — Example-app migration posture][spec-020-d9]

**The card-text departure** (rev4 H3), moved here whole. The KANBAN card `DONE-020-0.0.7`'s Definition of done said "Live HTTP coverage **replacing** one of the hand-rolled `all_library_*` resolvers". The add-only posture chosen by rev2 M1 is a deliberate departure from that wording: the test-determinism win from leaving the ordered resolvers untouched is load-bearing, and the replacement alternative would stop exercising the default-resolver path, which is the one the example exists to cover. The consequence for the build is a live obligation and stays in the spec — the Slice 5 `KANBAN.md` bullet and Definition of done item 17 both require the past-tense Done body to say "added `all_library_branches_via_list_field`", so a reader consulting the card after Done sees the add-only language rather than the original "replacing".

**Rejected alternatives.**

- **Replace `all_library_branches` with `DjangoListField(BranchType)`** (rev1's posture). Rejected by rev2 M1: drops `order_by("id")` and breaks `test_library_relation_override_shapes_http_response_data`'s ordering assertions.
- **Replace it with `DjangoListField(BranchType, resolver=lambda: Branch.objects.order_by("id"))`.** Rejected: legal under the rev2 H1 contract, but the field would then exercise the consumer-override path instead of the default path — and the override path is already covered package-internally.
- **Add `class Meta: ordering = ("id",)` to `Branch`.** Rejected: a model-level ordering change touches every `Branch` query in the suite (admin, services, schema-execute, HTTP), far beyond this card.
- **Replace all seven non-`prefetched` resolvers.** Rejected: churn that doesn't pin the contract any harder than one addition does. (This is where rev3 L1's arithmetic correction landed — the original "21 lines for cosmetic gain" was wrong in sign and magnitude; the real delta is about -14, which is still churn.)
- **Replace one of the `products` resolvers instead.** Rejected: the `products` schema's documented future shape is Relay-shaped throughout (`relay.ListConnection[CategoryType] = DjangoConnectionField(CategoryType)`), so `DjangoListField` is not its natural home. The `library` app is.

**The positive argument for adding a sibling** (the moved `Justification:` bullets 1 and 2): a sibling field leaves the existing seven resolvers and their HTTP-test dependencies untouched while exercising the default resolver in isolation. Bullet 3 — that `all_library_prefetched_books` must stay hand-rolled to keep exercising the optimizer's queryset-diffing path — was kept in the spec, because it is a prohibition a later builder could otherwise "tidy" away.

**Changed by R1 (spec-vs-code reconciliation round, 2026-08-18) (F8).** The add-only posture held and its predicted risk never materialized, but the shape landed as **three** new fields rather than one: `all_library_branches_via_list_field` (default resolver), `all_library_branches_via_list_field_nullable` (the nullable-outer rendering the Test plan promoted to the live tier under F7), and `all_library_branches_via_list_field_manager_resolver` (the consumer-`Manager`-return path). Decision 9, Slice 4 and Definition of done item 5 all now name the three.

Separately the spec contradicted itself on the untouched-resolver count — Definition of done item 5 said "eight", Decision 9 said "seven" twice — and **both are now wrong**, because later cards grew the schema (measured at HEAD: 15 `def all_library_*` resolvers plus three unconditional connection fields and a fourth behind `FAKESHOP_TEST_LOAN_CONNECTION`). Every one of those counts was replaced with the contract it was standing in for: the pre-existing resolvers were not replaced. **Rejected:** re-pinning the count at 15. A count of a file later cards keep growing is a claim that goes stale on a schedule nobody owns, and the number was never what the requirement meant.

**Changed again by R1's apply-changes pass (L1).** The surrounding-resolvers constraint gained "and later cards have added more of them on the same terms" in the first pass. Cut: the contract is that this card migrates none of them, and a prose gesture at later growth is a timeline the reader must hold for no gain - the same reason the competing "seven"/"eight" counts were dropped rather than re-measured. The HEAD growth measurement stays here, above, where a later reader finds it without the spec carrying a chronology.

**Claims this decision may no longer make:** that any existing `all_library_*` resolver is replaced; that the card's "replacing" wording describes what shipped; that the card adds one field; that seven (or eight) `all_library_*` resolvers surround it.

### [Decision 10 — Joint `0.0.7` cut][spec-020-d10]

**Rejected alternatives.**

- **Each card bumps independently.** Rejected: the five cards' commits land in arbitrary order, so the bump would point at whichever merged last — fragile and surprising.
- **Block all five cards on a single integration commit.** Rejected: the cards lose independence, the review surface balloons, and the value of slicing disappears.

**The positive argument** (the moved `Justification:` bullets): each card lands self-contained code, tests and docs; the bump is the joint cut-over signal, and doing it per card would produce five overlapping bumps competing for `0.0.7`; and the `[0.0.7]` `### Added` entries accumulate across the five cards' Slice 5s under one heading.

**Changes, with the round that caused each.** rev3 M1 replaced "the joint `0.0.7` cut card" with "the last `0.0.7` card to ship" at five sites, because no such card exists in `KANBAN.md`; the heading kept the policy name. The same item is the fourth entry in the moved Risks section, whose fallback was an explicit `TODO-ALPHA-XXX-0.0.7 — 0.0.7 release cut` card added by a separate `KANBAN.md` edit this spec does not author.

**Changed by R1 (spec-vs-code reconciliation round, 2026-08-18) (F10).** The decision enumerated five cards; `0.0.7` shipped **seven**. `KANBAN.md #"`0.0.7` shipped 2026-05-27 with seven cards"` is the record: the five plus `DONE-024-0.0.7` (Django Trac #37064 hardening) and `DONE-026-0.0.7` (scalar conversion end-to-end coverage). The last-card-owns-the-bump policy itself held unchanged; only the enumeration was stale, and the spec's phrasing dropped "five" so a further late addition could not falsify it again.

**Claims this decision may no longer make:** that a "joint cut card" exists; that the `0.0.7` bundle is five cards.

### `## Problem statement` and `## Current state`

The problem statement's argument — that seven of the `library` app's eight root resolvers are the same three lines with the model swapped, that graphene-django migrants lose a primitive they already know, and that `cls.get_queryset` is silently bypassed unless every hand-rolled resolver threads it — stays in the spec, because it is the scope boundary rather than deliberation.

Moved from `## Current state`:

- the **historical-citation parenthetical** stating that the `__all__` tuple did not include `DjangoListField` before `0.0.7`. It asserted the ship inside a spec whose status line said "draft", and the bullet already reads as a pre-card baseline;
- the **deliberation about why `library` hosts the example**: that the `products` schema's documented future shape jumps straight from `@strawberry.field` resolvers to `relay.ListConnection[…] = DjangoConnectionField(…)` because products is Relay-shaped by design, and that a single new sibling root field in `library` is enough to pin the default-resolver contract end-to-end. The spec keeps the factual half and points at Decision 9 for the posture.

rev4 L1 rewrote this section's "where one resolver-replacement is enough to pin the contract end-to-end" into add-only language; the pre-rev4 phrasing is recorded here and appears nowhere else.

**Changed by R1 (spec-vs-code reconciliation round, 2026-08-18) (F1).** This section and `## Problem statement` carried the **fifth and sixth** occurrences of the dead `_apply_get_queryset_*` symbols, neither of them in the four sites the finding enumerated (Decision 2's sketch, Decision 3's two bullets, the Slice 1 checklist, Definition of done 9). `## Current state`'s bullet described `types/relay.py` as defining them and the `DjangoListField` default resolver as re-using them verbatim; it now names `utils/querysets.py::apply_type_visibility_sync` / `::apply_type_visibility_async` and the `SyncMisuseError` rejection. `## Problem statement`'s closing paragraph called them "the sync + async `_apply_get_queryset_*` ports from spec-011", which was wrong twice over — dead symbols and a pre-renumber card number — and now names the shipped visibility-hook application, cited to `spec-015` by ref-id. The `## Problem statement`'s "seven non-`prefetched` resolvers" and this section's "eight hand-rolled root list resolvers" were **left as found**: both sections are explicitly a snapshot of the pre-card baseline, so a later card growing the schema does not falsify them the way it falsified Decision 9 and Definition of done item 5, which are statements about the shipped result.

**The lesson: an enumerated finding's list of sites is a sample, not a population.** Four sites were cited with symbol-qualified paths and were all real; the fifth was found only by re-running the grep the finding was derived from. Re-derive the population before treating an enumeration as complete.

**Changed by R1 final verification (2026-08-18) — the cross-file dangling link this section carried.** The `get_queryset`-boilerplate bullet linked a `TODAY.md` section heading that `TODAY.md`'s rewrite had deleted (`../../TODAY.md#optional-fakeshop-visibility-filtering-today`). The def is re-pointed at the heading that carries that content today, `../../TODAY.md#visibility-filtering-via-get_queryset`, with the link text and the ref-id renamed to match; de-linking the phrase was rejected because the cited section still exists under a new name and still lays out exactly the boilerplate the bullet is about.

**The lesson: a link has two halves and this round's instruments only checked one.** Four separate anchor instruments ran over these two files — the reconciliation's own postcondition, both review sweeps, and the fix pass's gate table — and every one measured in-page anchors plus def-path-existence-on-disk. None resolved a cross-file def's `#fragment` against the target file's headings, so a whole defect class was invisible to all four. A path that exists is not a link that resolves; the sweep must slug the target file's headings too.

### `## Goals`

**Changed by R1's apply-changes pass (H1).** Goal 3 sourced the coroutine-in-sync rejection to `types/relay.py` and called it a bare `ConfigurationError`. Both halves were false at HEAD, and R1's first pass had already corrected the same fact in four other places (Decision 3, `## Current state`, the `## Test plan` sync-rejection entry, Definition of done item 9), so the spec contradicted itself inside one file. The goal now names `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` and the `SyncMisuseError` it raises through `django_strawberry_framework/utils/querysets.py::reject_async_in_sync_context`. `types/relay.py` neither owns nor raises that rejection: it imports the two visibility helpers and re-exports `SyncMisuseError` for import compatibility.

**Why the first pass missed it.** The dead-symbol population was swept on the symbol names `_apply_get_queryset_sync` / `_apply_get_queryset_async`. This site names the module and the exception class and no symbol at all, so no amount of care with that grep reaches it. A claim that depends on a symbol's location belongs to that symbol's population even when it never spells the symbol - so the module path, the exception class, and the behaviour sentence are each their own sweep. The identical blindness left the retired-predicate fragment in Slice 1 standing (see [`## Slice checklist`](#-slice-checklist--the-dropped-sub-check)).

**Rejected while writing it:** naming `types/relay.py` as the re-export site in the goal, for continuity with a reader who remembers the old location. The goal states a contract the field must preserve; where a symbol may also be imported from is not part of it, and naming the module twice in one clause is what made the original sentence readable as a source attribution.

**Claims this section may no longer make:** that `types/relay.py` owns the coroutine-in-sync rejection; that the rejection is a bare `ConfigurationError`.

### `## Non-goals`

One `Justification:` clause moved: that `DjangoConnectionField` shipping in `0.0.9` rather than `0.0.7` is a deliberate sequencing decision, gated on connection-aware optimizer planning (`DONE-033-0.0.9`) and justified by the connection field's much larger API surface (edges / pageInfo / pagination arguments / connection-aware planning). The non-goal itself, and the card it is tracked under, stay in the spec.

**Changed by R1's apply-changes pass (D1).** This section's pagination bullet and `## Out of scope`'s pagination/limits bullet were near-copies of each other, both written for F3 by the first pass and each restating the whole row-bound contract. Each is now one clause - row limits are mandatory, not optional - plus a pointer to `### Row bound`. Neither section's job is to state a contract; both exist to say what is absent, and a full contract statement inside a "not in scope" bullet is the least discoverable place it could live.

### `## Borrowing posture`

The posture — borrow patterns from `graphene-django`, not implementations, and borrow nothing from `strawberry-graphql-django`, whose decorator-based `strawberry_django.field()` contradicts the `class Meta` posture — stays in the spec, as do the four borrow decisions and the three explicit non-borrows. Moved:

- **The symbol-name justification**: migrants searching for the primitive they already use should find it under the same import name.
- **The default-resolver justification**: the manager → visibility-hook contract is exactly what a reader expects from "list field for a `DjangoType`". The one adaptation — our `get_queryset` is a `classmethod`, not a `staticmethod` — was kept in the spec, being implementation-relevant.
- **The item-non-null justification**: Strawberry already reads the class-attribute annotation, so a `nullable_list=` toggle would fight or silently override it. (Decision 2 keeps the same sentence; this was the duplicate.)
- **The `maybe_queryset` bullet's rev-attribution and justification**: that rev1 misdescribed graphene-django's behavior and claimed `DjangoListField` would skip `get_queryset` on consumer returns, when the visibility-hook contract is too load-bearing to drop silently; and that the parity holds regardless of whether the consumer's resolver is sync or `async def`. The both-coercions-coexist contract (field wrapper for visibility-hook correctness, optimizer extension as a downstream safety net) stays in the spec — it is rev4 M1's actual finding and a builder who misses it degrades the hook for every `Model.objects` return.

### `## User-facing API`

Moved: the field-metadata justification — that `description` / `deprecation_reason` / `directives` pass-through makes the symbol feature-comparable with `strawberry.field(...)`, so a consumer never has to fall back to a hand-rolled `@strawberry.field` just to attach a description.

rev6 M3 added the async-resolver example block; rev4 H1 rewrote every signature in this section. The `# Async-resolver example` comment inside the block kept its content and lost its round label.

**Changed by R1's apply-changes pass (M2, D1).** Two things.

**The async-spelling enumerations were closed at three and HEAD supports four.** `django_strawberry_framework/utils/typing.py::_callable_inspection_target` peels `functools.partial` **and** `staticmethod` in a `while` loop, so `is_async_callable` also sees a raw `staticmethod async def` descriptor and any nesting of the two wrapper kinds - pinned for this field by `tests/test_list_field.py::test_djangolistfield_async_staticmethod_resolver_gets_get_queryset_applied`, itself one of the four tests F4 cited as its own evidence. The measured population is **six** spec sites, not the four the finding named: this section's async-consumer paragraph, [Decision 2](#decision-2--default-resolver-shape)'s three-arms paragraph and its async-detection-asymmetry bullet, the `## Slice checklist` Slice 1 `resolver=` bullet, the `## Edge cases and constraints` `functools.partial` entry, and Definition of done item 1. The two extra sites were found by grepping the shortest distinctive fragment of the characterization - `aware superset` - rather than the word "three": both stated the predicate's coverage without stating a count, so a count-shaped sweep could not see them.

**The characterization was the vector.** "the `__call__`/`functools.partial`-aware superset of `inspect.iscoroutinefunction`" is `django_strawberry_framework/list_field.py`'s inline comment, an abbreviation; `is_async_callable`'s docstring is the contract and names the `staticmethod` descriptor as its third motivating shape. **Rejected:** re-enumerating the four shapes at all six sites. A local enumeration is a copy that goes stale the next time the predicate grows, so five sites defer to the predicate and the shapes are spelled out only where a consumer needs to recognize their own code - this section and the `functools.partial` edge-case entry.

**The `### Row bound` subsection versus `docs/GLOSSARY.md` - decided: the spec keeps the field-facing surface, the glossary keeps the policy contract.** The subsection the first pass added restated the `DjangoListField` glossary entry's **Row bound** paragraph sentence-for-sentence, only resequenced, and both are near-copies of `django_strawberry_framework/list_field.py::DjangoListField`'s docstring. The alternative - keep the spec's statement whole and have the glossary defer to it - was **rejected**: `docs/GLOSSARY.md` is the standing, generated, consumer-facing doc, and the row bound is a `0.0.14` (spec-047) contract this `0.0.7` spec only inherits, so making an archived spec the authority for a later card's contract is the exact shape this residual series exists to unwind. It also costs a DB edit and a re-render to buy nothing. So the spec states what the field's own two constructor arguments do, and cites [the glossary entry][glossary-djangolistfield] for how bound and policy compose. The duplication went from five full statements in the spec plus one in the glossary to one field-facing statement plus a clause-and-pointer at each of the other four sites.

**On the bound-applied-last reasoning (D2), measured rather than assumed.** The derivation - a sliced queryset cannot be refiltered or reordered, so slicing first would break every type with a hook - occurs **once** in the spec, in Decision 2's post-sketch paragraph, which is where D2 asks for it (`refiltered` returns exactly one occurrence). The other three sites assert the ordering in one clause each without re-deriving it, which is D2's recommended end state: a Slice 1 checklist step a builder follows, the sketch's inline comment explaining why the async branch needs its own coroutine wrapper, and Definition of done item 8, which must be checkable on its own. **Rejected:** collapsing those three to pointers. A checklist step that cannot be followed without a jump, and a DoD item that cannot be verified without one, cost more than the clause they save.

### `## Implementation plan` — the slice table's estimates

The table stays; its per-revision narration moved. Slice 3's row went from 11 tests (`+220 / -0`, rev4) to 13 (rev4 H2's two async-consumer tests) to 14 (`+260 / -0`, rev5 M3's dual-execution test) to `+280 / -0` (rev6 L3, which caught that the estimate had not tracked the addition). Slice 2's row lost the `nullable_list` bool test at rev2 H2. Slice 4's row was rewritten from replacement to addition at rev2 M1. Slice 0's row was added by rev3 H1 with a zero delta, and rev4 M2 corrected the prose that still said "ships as five commits" against a six-row table.

The `~530 lines` total is an estimate that was never re-derived after the row-level changes above; nothing in the spec claims it was measured.

**Changed by R1 (spec-vs-code reconciliation round, 2026-08-18) (F7).** The table's two hard test counts were removed: Slice 2's "4 validation tests" (five shipped — the own-`Meta` guard added a fifth) and Slice 3's "14 behavior tests". The per-test enumeration beside each stays, because it names contracts rather than counting rows. The `~530 lines` estimate is left as an estimate the spec never claimed to have measured. **Rejected:** re-pinning both rows at the shipped numbers. `tests/test_list_field.py` holds 41 tests at HEAD, most of them added by later cards against this same module, so a count in this table would measure the file's whole history rather than this card's slice.

### `## Slice checklist` — the dropped sub-check

Slice 2 carried a checklist item whose entire content was a record of a removal: "(rev2 H2: dropped — `nullable_list=` is NOT a constructor argument; outer nullability is driven by the consumer's class-attribute annotation.)" It was an unticked box that could never be ticked. Deleted from the spec; the contract it describes is in Decisions 2 and 5.

Slice 3's two boxes shipped **ticked** (`- [x]`) while every other box in the file is unticked, including the boxes for slices whose code demonstrably landed.

**Changed by R1 (spec-vs-code reconciliation round, 2026-08-18) (F7).** The move pass left them alone, on the reasoning that for a Done card the `Status:` line is the source of truth and the boxes are noise. That reasoning is right about which line a reader should trust and wrong about what to do with the other one: two ticked boxes in a file of 60-odd unticked ones read as a partial-completion signal, and a reader who does not already know the card shipped will conclude Slice 3 is the only finished slice. The whole file is now uniformly `- [ ]`, which carries no signal at all, and the `Status:` line carries the truth. Slice 3's second box also dropped its "18 TODO stubs" count, which described the scaffolding commit's stub tally and is not re-derivable from anything on disk.

**Rejected:** ticking every box instead. The boxes would then assert per-slice completion this round did not verify slice-by-slice — it verified the Definition of done against source — and an over-tick is the failure mode the checklist discipline exists to prevent.

**Changed by R1's apply-changes pass (M3, M2).** Slice 1's async-detection bullet ended "Same `iscoroutinefunction`/coroutine handling", two lines above the `resolver=` bullet the first pass had rewritten off that predicate. **Deleted rather than restated:** the default body branches on runtime `in_async_context()` alone, and the next bullet already names the construction-time predicates, so the fragment had no surviving referent to restate. It was the fourth occurrence of the F4 population and the second site in this cycle - with Goal 3 - that a grep on the *replacement* symbol could not reach, because it names only the retired one. The same bullet list's `resolver=` entry carried one of the two extra M2 sites and now defers to `is_async_callable` instead of abbreviating it.

### `## Edge cases and constraints`

The `functools.partial` entry stays in the spec with both code blocks (rev6 M4). Moved: the "rev5 H1 chose YAGNI here over keeping a branch that would be hard to cover under the 100% gate" framing, which is the decision record rather than the contract. The spec now states the absence of the fallback as a property.

**Changed by R1 (spec-vs-code reconciliation round, 2026-08-18) (F4) — the highest-value single fix in the round, because the entry was actively misinstructing.** The block's code comment read "DOES NOT WORK as expected", asserted `get_queryset` is "silently skipped" for a `functools.partial`-wrapped async resolver, and offered a hand-rewrap in `async def` as the workaround. All three are false at HEAD: construction-time detection is `utils/typing.py::is_async_callable`, described in `list_field.py`'s own comment as "the `__call__`/`functools.partial`-aware superset of `inspect.iscoroutinefunction`", and four tests pin the cases the spec called broken (`::test_djangolistfield_partial_wrapped_async_resolver_gets_get_queryset_applied`, `::test_djangolistfield_partial_wrapped_async_callable_object_resolver_gets_get_queryset_applied`, `::test_djangolistfield_async_callable_object_resolver_gets_get_queryset_applied`, `::test_djangolistfield_async_staticmethod_resolver_gets_get_queryset_applied`). The entry is now a positive statement that all three async spellings work, with the WORKS block kept and the DOES-NOT-WORK block deleted rather than moved (rule 2 — the current contract falsifies it), plus the loud-rejection trio for a sync-detected resolver that returns a coroutine, a custom awaitable or a `Future`.

**Why this one was worth a code block rather than a sentence:** the workaround it replaced was a specific piece of consumer code, and a reader who had already written it needs to see that the plain form is now correct. **Rejected:** deleting the entry entirely as no-longer-an-edge-case. `inspect.iscoroutinefunction` returning `False` for a partial is still the trap; the entry now explains why the field does not use that predicate, which is the fact a maintainer "simplifying" `is_async_callable` away would need.

### `## Test plan`

Moved: the note recording that `test_djangolistfield_rejects_non_bool_nullable_list` was dropped at rev2 H2, and every per-test round attribution. The test list itself, the assertion shapes, and the derivation note on `assertNumQueries(N)` stay.

The full round-by-round test-count record: rev1's list minus rev2 H2's `nullable_list` toggle test and minus rev2 H1's `test_djangolistfield_consumer_resolver_override_bypasses_default`, plus rev2 H1's queryset-return and list-return pair, plus rev2 H2's two annotation-rendering tests, plus rev2 M3's root-optimization test, plus rev4 H2's two async-consumer tests (11 → 13 behavior tests), plus rev5 M3's dual-execution test (13 → 14). With the four validation tests that is the 18 the Definition of done named.

**Changed by R1 (spec-vs-code reconciliation round, 2026-08-18) (F7) — two spec-named tests were promoted to the live tier, and it is a promotion, not a loss.** Measured at HEAD: `tests/test_list_field.py` holds **41** test functions (`grep -o 'def test_[a-z_0-9]*' tests/test_list_field.py | wc -l`), and exactly two of the 18 the spec named are absent — `test_djangolistfield_default_resolver_returns_queryset_filtered_by_get_queryset` and `test_djangolistfield_nullable_outer_via_consumer_annotation`. Both live in `examples/fakeshop/test_query/test_library_api.py` as `::test_branches_via_list_field_default_resolver_applies_get_queryset_live` and `::test_library_branches_via_djangolistfield_nullable_outer_renders_and_resolves`, and **the promotion carries its own provenance in the test tree**: the live docstrings name the retired package tests ("The live twin of…", "Live counterpart of the (removed) package test…") and `tests/test_list_field.py` carries a `NOTE:` block above the surviving non-nullable companion explaining why the pair split across tiers. That is the standing live-first rule in `AGENTS.md` ("Test through real usage") applied to two paths reachable from a real `/graphql/` query.

The spec's Test-plan entries for those two now name the live tests and their file, and the section gained a sentence saying the list is the contract pins this card owes rather than an inventory of the file — because the other 23 tests belong to spec-034, spec-045 and spec-047, and a spec that claims to enumerate its test file acquires a false claim every time a later card adds a test to it.

**Rejected:** listing all 41 in the Test plan. That makes this spec the index of a shared file and guarantees the same staleness again. **Also rejected:** deleting the two promoted entries. A reader looking for the default-resolver `get_queryset` pin would then find nothing and conclude it is unpinned.

### `## Doc updates`

Moved: the CHANGELOG bullet's trailing change record — that rev2 L2 narrowed "root and nested fields" to "root Query fields", rev2 H2 removed the `nullable_list=True` constructor-toggle phrasing, and rev2 H1 added the consumer-resolver `get_queryset` parity phrasing. The append-don't-create-a-second-`[0.0.7]`-heading instruction stays, being a live build obligation; so does the `docs/TREE.md` `connection.py`-line removal (rev2 L1) and the `GOAL.md` heading rev6 M5 named.

**Changed by R1 (spec-vs-code reconciliation round, 2026-08-18): the `README.md` bullet is RESTATED as to shape and KEPT as to obligation; the `TODAY.md` bullet is reconciled to the landed shape.**

`README.md` (F13, the round's one genuine judgement call). `grep -n DjangoListField README.md` returns nothing, so the obligation is unmet, and the file has since been restructured out from under the bullet's prescription: `## Status` now carries a "**Newest shipped**" block plus an "Earlier alpha surfaces" list running `0.0.13` down to `0.0.8`, and the bullet's instruction — surface the symbol "inline … alongside the version-pin sentence rather than introducing a bullet list that doesn't match the file's voice" — describes a file that no longer exists. The two available resolutions were to satisfy the obligation or to retract it. **Chosen: satisfy it, and restate only the shape.** Three reasons. First, the file's own idiom is now exactly the bullet list the original prescription was avoiding, so "match the file's voice" today *means* a list entry — the prescription's intent survives its letter. Second, the "Earlier alpha surfaces" list stops at `0.0.8` for no stated reason; nothing in `README.md` says the status prose deliberately declines to reach `0.0.7`, so retracting the obligation would be inventing a policy to excuse a gap. Third, Definition of done item 16 requires the named docs to reflect the shipped state, and `README.md` is in that list; retracting the Slice 5 bullet while leaving item 16 standing would half-reconcile the spec, which is the failure mode `worker-1.md` "Review-round custody" names as worse than not reconciling at all. **Rejected: retract the bullet** — it is the cheaper edit and it converts a real documentation gap into a documented non-goal, which is exactly the move a residual-closeout cycle exists to stop. R2 owns the `README.md` edit; the spec's bullet now names the "Earlier alpha surfaces" list, its newest-first ordering and `KANBAN.md`'s Done column as the authoritative content for the cut, so R2 has a satisfiable target rather than a prescription it must reinterpret.

`TODAY.md`. The bullet asked for the specific root-field name `all_library_branches_via_list_field` in the `library` summary line. The file has since been rewritten into a compact capability list that names `DjangoListField` among the `library` app's demonstrated capabilities and names no individual root field for any of them; spelling one field there would be off-voice against every sibling entry. The bullet is restated to the landed shape — `DjangoListField` absent from the wait-for list, named in the capability list, no field-level naming — and the obligation is satisfied rather than outstanding. **Rejected:** asking R2 to add the field name. It would be the only field name in the list, which makes the list inconsistent to satisfy a sentence whose purpose (prove the example demonstrates the primitive) is already met.

### `## Risks and open questions`

The whole section moved. It was written as preferred-answer / fallback pairs, and by the time the card shipped every pair had resolved. rev3 L2 had already trimmed it from eight items to four, folding the restatements into their owning Decisions' alternatives; the four survivors were:

1. **Slice 0 outcome — does the factory-function shape survive contact with `@strawberry.type`?** Preferred answer: yes — the factory returns the result of `strawberry.field(resolver=..., ...)`, and Strawberry picks that return value up in `@strawberry.type`'s decorator-time class-body walk, which iterates `cls.__dict__` and converts annotated attributes and `StrawberryField` instances into the type's field list, exactly as `field = strawberry.field(...)` is discovered today. Fallback: construct a `StrawberryField` directly with explicit `python_name` / `type_annotation`, promote that into Decision 1, and reauthor Slice 1. The spec called this **the only risk whose outcome is genuinely unknown until implementation contact**, which is why rev3 H1 added Slice 0 to discharge it. rev6 M1 corrected this item's mechanism claim from "via `__set_name__`" to the class-body walk.
2. **The `get_queryset`-on-consumer-resolver-returns contract** (rev2 H1, already pinned). Preferred answer: graphene-django parity — apply `target_type.get_queryset(qs, info)` to any `Manager`/`QuerySet` a consumer resolver returns; Python `list` returns pass through. Fallback: if real consumers report the application is a foot-gun, an `apply_get_queryset=False` toggle in a follow-up; the default stays "apply", because dropping it silently weakens the visibility hook.
3. **Async helper relocation** (Decision 3's Option B). Preferred answer for `0.0.7`: keep the helpers in `types/relay.py`. Fallback: relocate to `utils/get_queryset.py`; the blast radius is one import update.
4. **Last-card-to-ship version bump policy** (rev3 M1). Preferred answer: the last of the five `0.0.7` WIP cards to merge owns the bump. Fallback: if merge sequencing turns out unclear, a separate `KANBAN.md` edit adds an explicit release-cut card — an edit this spec deliberately does not author.

### `## Definition of done`

Moved: every round attribution on items 1, 4, 5, 6, 7, 11, 12, 13, 16, 17 and 18, plus item 7's `(Rev2 H2: no nullable_list= argument …)` trailer.

**Deleted, not moved:** item 1's clause "with the `inspect.iscoroutinefunction`-driven wrapper choice and the runtime `inspect.iscoroutine` fallback per rev4 H2". The fallback was removed from the design by rev5 H1 and the DoD item was never reconciled, so the shipped spec's completion criteria contradicted its own Decision 2, Slice 1 checklist and Edge cases section. The item now states the construction-time choice and the absence of a fallback.

Item 17's cross-reference to Decision 9's "Card-text departure" paragraph was rewritten to state the requirement directly, since that paragraph now lives here.

**Changed by R1 (spec-vs-code reconciliation round, 2026-08-18) (F1, F2, F3, F5, F7, F8).** Six items were false as written and are now statements of what shipped: item 1 (the construction-time predicate is `is_async_generator_callable` then `is_async_callable`, three consumer-resolver arms, and a loud rejection where the deleted runtime fallback used to be hypothesised), item 4 (no "18 tests" count; the two live-tier promotions are named as exceptions), item 5 (three added fields, no count of the untouched ones), item 7 (the own-registration guard plus the `max_rows` guard), item 9 (`SyncMisuseError` from `utils/querysets.py::apply_type_visibility_sync`, not a bare `ConfigurationError` from a dead `types/relay.py` symbol), and item 11 (the async-iterable arm).

The row bound was folded into **item 8** rather than added as a new item. **Rejected: a new item.** The list is 20 items and items 16-20 are cited by number from the build plan and from this file, so inserting or renumbering would break those citations; an out-of-band "15a" was drafted and discarded for the same reason, since a list that numbers 15, 15a, 16 reads as a patch rather than a contract. Item 8 already owned the return-shape contract ("returns a `QuerySet`, not a Python `list`"), and the bound is a property of that same returned queryset — applied by slicing, after the hook, so it reaches SQL as a `LIMIT` — which makes it the correct home rather than merely the convenient one.

**Changed again by R1's apply-changes pass (M2, D1).** Item 1's async-callable parenthetical was one of the six closed enumerations and now defers to `is_async_callable`. Item 8 keeps the row bound folded in and now asserts it by pointer to `### Row bound` plus the applied-last ordering, which the item needs to stay checkable, instead of restating the policy / narrow / widen contract a third time.

## Claims the spec may no longer make

An index of the retractions above, for a reviewer checking the implementation against the reasoning that produced it. Every row is a claim some revision of this spec asserted and a later revision (or the ship itself) falsified.

| Claim once made | Where it lived | What holds instead | Retired by |
|---|---|---|---|
| `DjangoListField` is a class; `__call__` / `__set_name__` return the `StrawberryField` | Decisions 1 and 2 | a factory function returning `strawberry.field(...)` | rev2 H2 |
| a consumer-supplied `resolver=` owns the queryset and bypasses `cls.get_queryset` | Decision 2, User-facing API, Borrowing posture | `get_queryset` applies to any `Manager`/`QuerySet` return; a Python `list` is the explicit bypass | rev2 H1 |
| `nullable_list=` is a constructor argument | Decisions 2 and 5, Slice 2, Test plan | the consumer's class-attribute annotation drives outer nullability | rev2 H2 |
| the resolver signature is `(type_cls, info)` | Decision 2 | `(root: Any, info: Info)`, target type via closure | rev2 H3 |
| the resolver signature carries `**kwargs` | Decision 2, User-facing API, Slice 1 | no `**kwargs`; arguments belong to the Layer-3 cards | rev4 H1 |
| the contract covers root **and nested** fields | Goals, Decisions 2 and 4, CHANGELOG, Definition of done | root list fields only in `0.0.7` | rev2 M3 |
| the card replaces a hand-rolled `all_library_*` resolver | Decision 9, Slice 4, Slice 5, Definition of done, the KANBAN card body | a sibling field is **added**; nothing is replaced | rev2 M1, recorded as a departure by rev4 H3 |
| a runtime `inspect.iscoroutine(result)` fallback backs up construction-time detection | Decision 2, Slice 1, Definition of done item 1 | construction-time `inspect.iscoroutinefunction` only | rev5 H1 (Definition of done item 1 was left unreconciled and is deleted by this pass) |
| the post-processing helpers are `_post_process_sync` / `_post_process_async` and may sit in the factory body | Decision 2 | `_post_process_consumer_sync` / `_post_process_consumer_async` at module scope | rev6 H2, rev6 H3 |
| `_default` wraps the async application in an inner `async def` | Decision 2 | it returns the coroutine directly for `AwaitableOrValue` dispatch | rev6 H1 |
| Strawberry discovers the field "via `__set_name__`" | Risks item 1 | `@strawberry.type`'s decorator-time class-body walk | rev6 M1 |
| a "joint `0.0.7` cut card" exists in `KANBAN.md` | Decision 10, Slice 5, Risks, Definition of done | the last `0.0.7` card to ship owns the bump | rev3 M1 |
| the card's quoted `Card line:` is verbatim from the KANBAN body | preamble | the card is cited by ID only | rev3 M2 |
| replacing seven resolvers costs "21 lines for cosmetic gain" | Decision 9 alternatives | roughly a -14 line delta, and still churn | rev3 L1 |
| `Status: draft (revision 6, post-rev5 scaffolding review)` | preamble | shipped in `0.0.7` on 2026-05-27; archived | the ship, and `e01873ae` |
| the sync/async visibility helpers are `types/relay.py::_apply_get_queryset_sync` / `_async` | Decisions 2 and 3, Current state, Slice 1, Definition of done 9 | `utils/querysets.py::apply_type_visibility_sync` / `::apply_type_visibility_async`, shared by four surfaces | R1 (F1); the relocation trigger Decision 3 itself named |
| the sync path's coroutine rejection raises a bare `ConfigurationError` | Decision 3, Definition of done 9, Test plan | `SyncMisuseError`, a `ConfigurationError` subclass that also inherits `RuntimeError` | R1 (F1) |
| a `get_queryset` override's return value is used as returned | Decision 3 | the source and the result are sealed into a fresh framework-owned `QuerySet` and every unprovable shape fails closed | R1 (F12); spec-045 |
| `hasattr(arg, "__django_strawberry_definition__")` is a sufficient registration discriminator | Decision 5, Slice 2 | `definition.origin is arg` — the attribute is inherited via MRO, so `hasattr` accepts a subclass with no `Meta` of its own | R1 (F2) |
| the constructor signature ends at `directives=()`, with one error site | Decision 5, Decision 2's sketch, User-facing API | `max_rows=` / `trusted_max_rows=` too, and a second error site (`validate_collection_bound`) | R1 (F3); spec-047 |
| `DjangoListField` returns the unbounded queryset; limits are out of scope | Non-goals, Out of scope | every `DjangoListField` is row-bounded; there is no unbounded spelling | R1 (F3); spec-047 |
| `inspect.iscoroutinefunction` is the construction-time async predicate, and a `functools.partial`-wrapped async resolver silently skips `get_queryset` | Decision 2, Slice 1, User-facing API, Edge cases | `utils/typing.py::is_async_callable`; the partial, the `async def __call__` instance and the async staticmethod all work | R1 (F4) |
| a consumer `resolver=` is either sync or `async def` | Decision 2, User-facing API, Definition of done 11 | three arms — async generator, any async callable, sync callable — with an async-only iterable rejected from sync execution via `SyncMisuseError` | R1 (F5) |
| the list/connection boundary is only about pagination shape | Decision 8 | ordering is the other deliberate divergence: the list guarantees no order, the connection appends a pk tiebreaker | R1 (F6) |
| `tests/test_list_field.py` contains the 18 named tests (4 + 14) | Definition of done 4, Test plan, Implementation plan | 41 tests, two of the 18 promoted to the live `/graphql/` tier | R1 (F7) |
| the card adds one root field, and seven (or eight) `all_library_*` resolvers surround it unchanged | Decision 9, Slice 4, Definition of done 5 | three added fields; the pre-existing resolvers are unchanged and are not counted | R1 (F8) |
| `list_field.py` holds only the list field's own concerns | Decision 1 | it is the single home of the shared field-target validation guards, imported by `connection.py` and `relay.py` | R1 (F9) |
| the `0.0.7` bundle is five cards | Decision 10 | seven cards, per `KANBAN.md`'s release line | R1 (F10) |
| `_resolve_model_from_return_type` returns a model, and `_optimize` carries its own `Manager` coercion | Decision 4 | it returns an `_OriginAndModel \| None` pair; the coercion is `utils/querysets.py::normalize_query_source` | R1 (F11) |
| `types/relay.py` owns the coroutine-in-sync rejection, and it is a bare `ConfigurationError` | Goals item 3 | `utils/querysets.py::apply_type_visibility_sync` raises `SyncMisuseError` through `::reject_async_in_sync_context` | R1 (H1) |
| the row-bound guard is a fifth check, running after the four target guards | Decision 5 | it runs first, ahead of every target guard | R1 (M1) |
| `is_async_callable` sees three async spellings | User-facing API, Decision 2 (twice), Slice 1, Edge cases, Definition of done 1 | four wrapper shapes and any nesting of them; the predicate is the authority for the list | R1 (M2) |
| the default resolver shares the Relay defaults' `iscoroutinefunction` handling | Slice 1 | runtime `in_async_context()` only; the construction-time predicates apply to a consumer `resolver=` | R1 (M3) |
| the sealed visibility helpers have four consumers | Decision 3 | call sites in eight modules; the spec's list is illustrative | R1 (L2) |

## Verified against the shipped code

**Every item the extraction pass left open is resolved.** The pass that performed the MOVE deliberately deferred verification and enumerated four spec claims plus two anchor defects for the following round; `R1 (spec-vs-code reconciliation round, 2026-08-18)` closed all six. Nothing here is outstanding, and this section is a record of outcomes rather than a to-do list — if a future pass needs a to-do list, it writes its own with its own heading.

| Left open by the extraction pass | Outcome | Recorded under |
|---|---|---|
| The three "Remove the scaffold TODOs at this site" checklist items name six files; whether every TODO was removed is unverified | **Discharged.** `grep -n TODO` over all six named files returns exactly one hit, `TODO(spec-035)` in the live test, which belongs to another card. The repo-wide staged-anchor sweep for this card (`TODO(spec-020`, `TODO-(ALPHA\|BETA\|STABLE)-020`) returns only two prose mentions in `spec-017`'s rationale, which are legitimate history of a rejected renumber | no spec change needed; the checklist items stand, minus the un-derivable "18 TODO stubs" count |
| Definition of done item 4's "18 tests" and the Test plan's 4 + 14 split are estimates from revision arithmetic, not a count of the shipped file | **False as written; corrected.** 41 tests at HEAD; five validation tests, not four; two of the 18 promoted to the live tier | [`## Test plan`](#-test-plan), [`## Implementation plan`](#-implementation-plan--the-slice-tables-estimates), [`## Definition of done`](#-definition-of-done) (F7) |
| Definition of done item 5's "the eight existing `all_library_*` resolvers are unchanged" predates several later cards | **False as written, and so was Decision 9's competing "seven"; both counts removed.** Three fields shipped, not one | [Decision 9](#decision-9--example-app-migration-posture) (F8) |
| Decision 3's Option-A placement may have been superseded by the connection card, which the spec named as the trigger | **Superseded, and further than Option B sketched.** The helpers moved to `utils/querysets.py`, were renamed, and were rebuilt into a sealed validating boundary by spec-045 | [Decision 3](#decision-3--get_queryset-and-async-symmetry) (F1, F12) |
| The `#slice-5--promotion--docs--version` anchor has no matching heading; left as found because inventing a heading is a structural edit | **Resolved without a structural edit.** Both uses now point at `#slice-checklist`, the heading that actually contains Slice 5. Every in-page anchor in the spec resolves, re-derived by slugging all headings and differencing the used set | this pass; the whole-file anchor sweep is the postcondition |
| The three `#decision-10--joint-0_0_7-cut` uses never resolved (a dotted version slugs to `007`) | **Already corrected by the extraction pass**, and re-confirmed here by the same whole-file sweep | the extraction pass; re-verified by R1 |

Two further verifications R1 performed with no spec change attached, recorded so a later pass need not re-derive them:

- **`docs/TREE.md`, `GOAL.md`, `docs/README.md` and `CHANGELOG.md` all carry the shipped contract already.** `docs/TREE.md` lists `list_field.py` in both the current and target layouts and carries no `DjangoListField` on the `connection.py` bullet (the Slice 5 removal is satisfied); `GOAL.md` carries the graphene-django migration bullet Slice 5 asked for; `docs/README.md` carries the shipped contract including the `0.0.14` row bound; `CHANGELOG.md`'s `[0.0.7]` `### Added` entry is accurate.
- **Two multi-surface reference clusters were escalated to the maintainer rather than partially fixed**: `CHANGELOG.md`'s `[0.0.7]` section labels every card by its pre-renumber number (uniformly, across seven labels, with link definitions that still resolve because they are slug-based), and `KANBAN.md`'s `DONE-020-0.0.7` card lists `django_strawberry_framework/apps.py`, which is `DONE-021-0.0.7`'s subject, under `#### Package files` (DB-backed and replaced wholesale by `manage.py import_card_files`). Neither is this spec's to fix, and a spec-only correction diverging from un-editable copies is worse than uniformly-wrong.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-djangolistfield]: ../../GLOSSARY.md#djangolistfield

<!-- docs/SPECS/ -->
[spec-020-d1]: ../spec-020-list_field-0_0_7.md#decision-1--module-location-mechanism--public-export
[spec-020-d10]: ../spec-020-list_field-0_0_7.md#decision-10--joint-007-cut
[spec-020-d2]: ../spec-020-list_field-0_0_7.md#decision-2--default-resolver-shape
[spec-020-d3]: ../spec-020-list_field-0_0_7.md#decision-3--get_queryset-and-async-symmetry
[spec-020-d4]: ../spec-020-list_field-0_0_7.md#decision-4--optimizer-cooperation
[spec-020-d5]: ../spec-020-list_field-0_0_7.md#decision-5--validation--error-shapes
[spec-020-d6]: ../spec-020-list_field-0_0_7.md#decision-6--metaprimary-interaction
[spec-020-d7]: ../spec-020-list_field-0_0_7.md#decision-7--scope-boundary-vs-relation-list-fields
[spec-020-d8]: ../spec-020-list_field-0_0_7.md#decision-8--out-of-scope-boundary-with-djangoconnectionfield
[spec-020-d9]: ../spec-020-list_field-0_0_7.md#decision-9--example-app-migration-posture
[spec-020]: ../spec-020-list_field-0_0_7.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md
[worker-1]: ../../builder/worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
