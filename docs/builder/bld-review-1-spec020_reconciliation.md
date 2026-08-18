# Build: Review round 1 — spec-020 reconciliation against shipped code

Spec reference: `docs/SPECS/spec-020-list_field-0_0_7.md` (whole file; the round is a residual closeout, not a slice)
Rationale companion: `docs/SPECS/appx/spec-020-list_field-0_0_7-rationale.md` (Worker 1 owns it)
Build plan: `docs/builder/build-020-list_field-0_0_7.md`
Status: final-accepted

## Plan (Worker 1)

This is a **review round** (`docs/builder/BUILD.md` `## Review rounds`) whose input is already-built, already-shipped work. There is no maintainer review document; the findings are Worker 0's own spec-vs-code verification pass, recorded in the build plan with symbol-qualified paths and verified against source at HEAD before dispatch.

**Cohort R1 is Worker 1 only, and the whole cohort is spec custody.** `docs/builder/BUILD.md` `## Spec reconciliation` makes the spec and its rationale companion custodian-only, and every F1-F12 fix plus the two extra spec defects lands in exactly those two files. So there is no Worker 2 build pass to dispatch for this cohort: the plan and the fix are one pass, and Worker 3 reviews the resulting diff. F13 and F14 belong to R2 and appear in no list here.

### DRY analysis

**Helper inventory checked.** Not applicable in the mechanical sense — this cohort writes no Python and proposes no helper, constant, validation branch, or test helper, so `### Package-wide helper inventory before helper planning` has no candidate to inventory. The package-wide read that *was* required is the inverse one and it was performed: for every symbol the spec cites, confirm the symbol exists at HEAD and the spec's description of it is true. Shapes searched across `django_strawberry_framework/`: `_apply_get_queryset`, `apply_type_visibility`, `initial_queryset`, `post_process_queryset_result`, `normalize_query_source`, `_validate_djangotype_target`, `_validate_relay_djangotype_target`, `is_async_callable`, `is_async_generator_callable`, `validate_collection_bound`, `bounded_rows`, `_resolve_model_from_return_type`, `_format_unknown_fields_error`. Results are in the per-finding notes below.

- **Existing patterns reused.** The spec's own reference-style link-definition block (`START.md` "Markdown link convention") absorbed both ref-id renames with no inline change, which is the convention's entire payoff. The rationale file's existing `### [Decision N — …][spec-020-dN]` entry structure absorbed every change record with no new section shape invented.
- **New shared shapes justified.** One, and it is prose rather than code: the phrase `Changed by R1 (spec-vs-code reconciliation round, 2026-08-18) (F<n>)` opens every change record in the rationale, so a reader can grep one token to find everything this round touched. Its single responsibility is round attribution; it exists because the rationale already had per-round attribution for rev1-rev6 and a new round with no marker would be invisible.
- **Duplication risk avoided.** The obvious naive shape is to state a corrected contract in both the spec and the rationale — the spec because it is the contract, the rationale because the change must be recorded. That produces two copies that drift. The split held throughout: the spec states only what holds, the rationale states only what changed and what was rejected, and where the rationale needs the contract it names the spec section rather than restating it. The second risk is the round's own findings list becoming a third copy; this artifact's checklist quotes each finding once and points at the spec section that now carries the answer.

### Boundary count

Zero. No round in this cohort adds a guard, cap, rejection path, or validation branch — every edit is documentation. No failability proof is owed (`docs/builder/BUILD.md` `## Failability proofs: prove the test can fail`: a proof is owed per new boundary, and there are none). **Split question, answered:** not split. A single custodian writing one contract across two files that must agree sentence-for-sentence is one decision; splitting F1-F12 across two passes would let the spec and the rationale disagree at the seam, which is the exact defect this round exists to close.

### Hot-path declaration

Not applicable; the plan declares hot-path scope `none` for the whole cycle. This cohort touches two `.md` files and no per-request / per-resolver / per-row / per-connection path. The silence is deliberate.

### Floor-verification scope

Not applicable; the plan declares floor-verification scope `none`. This cohort touches no Django / Strawberry / channels integration seam. Where the reconciled prose reasons about version-dependent behavior it names the shipping card (`spec-045`, `spec-047`, `spec-034`) rather than a version floor.

### Implementation steps

1. Sweep the spec for the dead-symbol population rather than trusting the finding's enumeration: `grep -ro '_apply_get_queryset_sync\|_apply_get_queryset_async' django_strawberry_framework/ tests/ examples/ | wc -l` for the code side, then `grep -o` for every occurrence in the spec. Rewrite each to the shipped helper.
2. Rewrite Decision 2's pseudo-code sketch against `django_strawberry_framework/list_field.py::DjangoListField` — imports, signature, three consumer-resolver arms, bound-applied-last ordering.
3. Restate Decision 3 as the shipped placement plus the sealed-boundary contract; restate Decision 5's registration guard as the own-class-origin invariant.
4. Remove every asserted count the shipped tree falsifies, replacing each with the contract it stood in for rather than a re-measured number.
5. Fix the two extra spec defects: the unresolvable in-page anchor and the two pre-renumber link-definition ref-ids.
6. Record each change in the rationale under the entry for the decision it belongs to, with what was rejected while writing it.
7. Resolve every item in the rationale's `## Not verified against the shipped code by this pass` and retitle the section so it cannot survive as an open to-do.
8. Postconditions: `check_spec_glossary.py` exits 0; `check_trailing_commas.py --check` exits 0 on both files; every in-page anchor in both files resolves against a slugged heading; every reference-style ref-id used is defined and every path defined exists on disk.

### Test additions / updates

None. This cohort writes no test and runs no `pytest` — nothing in its diff is executable. The tests it *cites* were verified to exist by name at HEAD; the per-finding notes below record the citations that were wrong.

### Implementation discretion items

None delegated. This cohort has no downstream builder.

### Dispatched findings checklist

One box per finding dispatched to R1, quoting the finding as the build plan states it and citing the symbol-qualified path Worker 0's verification pass recorded. F13 and F14 are R2's and are absent by design.

- [x] **F1 — `types/relay.py::_apply_get_queryset_sync` / `_apply_get_queryset_async` are dead symbols; Decision 3 chose the option that later work reversed.** `grep -rn '_apply_get_queryset_sync\|_apply_get_queryset_async' django_strawberry_framework/` returns **0 occurrences**. The shipped helpers are `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` / `::apply_type_visibility_async`. Decision 3 named its own reversal condition ("Option B becomes the right move when a third call site needs the helpers — likely `DjangoConnectionField` in `DONE-030-0.0.9`"); that condition occurred. Four spec sites cite the dead symbols; two of the four also violate `AGENTS.md` rule 27 with the single-colon `path:Symbol` form. **Tick audit (apply-changes pass 2):** the first pass fixed six of a seven-site population and the tick was premature; the seventh (Goals item 3, which names the module and not the symbol) is fixed in pass 2 under H1, and the tick now holds.
- [x] **F2 — Decision 5's registration guard is documented as `hasattr`, and the shipped guard is deliberately stricter because `hasattr` is insufficient.** `django_strawberry_framework/list_field.py::_validate_djangotype_target` uses `definition is None or getattr(definition, "origin", None) is not target_type`; its docstring gives the reason ("The attribute is inherited via MRO, so `hasattr` would accept a subclass that omits its own `Meta`"). A fifth validation test exists for the hole: `tests/test_list_field.py::test_djangolistfield_rejects_djangotype_subclass_without_own_meta`. The shipped error message also differs from the one Decision 5 quotes.
- [x] **F3 — the constructor signature is missing `max_rows=` / `trusted_max_rows=`, and the `Out of scope` bullet that denies them is superseded.** Shipped: two more keyword arguments and a second error site, `django_strawberry_framework/resource_policy.py::validate_collection_bound` via `django_strawberry_framework/list_field.py::DjangoListField #"validate_collection_bound(max_rows, field=\"DjangoListField max_rows\")"`, pinned by `tests/test_list_field.py::test_djangolistfield_rejects_a_non_positive_max_rows_at_construction` and `::test_djangolistfield_max_rows_narrows_the_request_policy`. **Tick audit (apply-changes pass 2):** the first pass landed the signature, the second error site and the row-bound surface but misstated the guard's position; corrected in pass 2 under M1, and the tick now holds.
- [x] **F4 — the `functools.partial` edge case is documented as broken and is fixed.** Construction-time detection is `django_strawberry_framework/utils/typing.py::is_async_callable`, "the `__call__`/`functools.partial`-aware superset of `inspect.iscoroutinefunction`", and four tests pin the cases the spec says are broken (`tests/test_list_field.py::test_djangolistfield_partial_wrapped_async_resolver_gets_get_queryset_applied`, `::test_djangolistfield_partial_wrapped_async_callable_object_resolver_gets_get_queryset_applied`, `::test_djangolistfield_async_callable_object_resolver_gets_get_queryset_applied`, `::test_djangolistfield_async_staticmethod_resolver_gets_get_queryset_applied`). The spec currently instructs a reader to hand-rewrap a partial that works. **Tick audit (apply-changes pass 2):** the first pass inverted the entry correctly but left the spelling enumeration closed at three across six sites and left Slice 1's retired-predicate fragment standing; both fixed in pass 2 under M2 and M3, and the tick now holds.
- [x] **F5 — async-iterable and async-generator consumer resolvers are shipped and absent from the spec.** `django_strawberry_framework/list_field.py::_require_async_iterable_context`, `::_resolve_async_iterable`, an `is_async_generator_callable` branch, and an `isinstance(source, AsyncIterable) and not isinstance(source, Iterable)` branch in the sync wrapper, rejecting an async-only iterable met from sync execution with `django_strawberry_framework/utils/querysets.py::SyncMisuseError`. Decision 2's two-way sync/async split needs a third arm.
- [x] **F6 — the ordering contract is shipped, documented in the docstring, and absent from the spec.** `django_strawberry_framework/list_field.py::DjangoListField`'s docstring pins it: no row-order guarantee unless the query supplies `orderBy` or the model declares `Meta.ordering`, deliberately asymmetric with `DjangoConnectionField`'s pk tiebreaker. Decision 8's boundary line is where it belongs.
- [x] **F7 — the Test plan's names and DoD 4's count are both stale, and two spec-named tests were deliberately promoted to the live tier.** `tests/test_list_field.py` holds 41 tests, not 18. `test_djangolistfield_default_resolver_returns_queryset_filtered_by_get_queryset` and `test_djangolistfield_nullable_outer_via_consumer_annotation` are absent by design, promoted to `examples/fakeshop/test_query/test_library_api.py::test_branches_via_list_field_default_resolver_applies_get_queryset_live` and `::test_library_branches_via_djangolistfield_nullable_outer_renders_and_resolves`, with the promotion's provenance carried in the test tree. DoD 4's "18 tests" and the Implementation-plan table's "14 behavior tests" are both false. Slice 3's two `- [x]` boxes against `- [ ]` everywhere else is a further inconsistency to resolve one way for the whole file.
- [x] **F8 — the example-app posture landed as three fields, not one, and DoD 5's resolver count contradicts Decision 9's.** `examples/fakeshop/apps/library/schema.py::Query` carries `all_library_branches_via_list_field`, `all_library_branches_via_list_field_nullable` and `all_library_branches_via_list_field_manager_resolver`. DoD 5 says "eight existing `all_library_*` resolvers"; Decision 9 says "seven" twice; neither is true now. State the contract rather than pin a count.
- [x] **F9 — the shared target-validation helpers landed in `list_field.py` and are imported by two siblings, which inverts Decision 1's and Decision 8's expectation.** `django_strawberry_framework/list_field.py::_validate_djangotype_target` and `::_validate_relay_djangotype_target`, imported by `django_strawberry_framework/connection.py #"from .list_field import _validate_relay_djangotype_target"` and `django_strawberry_framework/relay.py::_validate_node_target`. `list_field.py` is now the home of the shared field-target validation contract for three factories, and the spec cannot currently tell a reader that.
- [x] **F10 — Decision 10's bundle is five cards and `0.0.7` shipped seven.** `KANBAN.md #"`0.0.7` shipped 2026-05-27 with seven cards"` — the five plus `DONE-024-0.0.7` and `DONE-026-0.0.7`. The last-card-owns-the-bump policy held; only the enumeration is stale.
- [x] **F11 — Decision 4's optimizer citations drifted one level.** `django_strawberry_framework/optimizer/extension.py::_resolve_model_from_return_type` still exists and is still called from `::DjangoOptimizerExtension._optimize #"resolved = _resolve_model_from_return_type(info)"`, but now returns an `_OriginAndModel | None` pair, and `_optimize`'s `Manager` coercion is delegated to `django_strawberry_framework/utils/querysets.py::normalize_query_source`. Fix the citations, not the reasoning.
- [x] **F12 — the spec-045 sealed-boundary and spec-034 cascade contracts reached this field and the spec does not mention them.** The field's `get_queryset` cooperation is no longer "call the hook" — it is "route the hook's return through the sealed-execution-queryset boundary, which fails closed on an unprovable return". Pinned by `tests/test_list_field.py::test_list_field_default_resolver_applies_cascade`, `::test_djangolistfield_hostile_hook_subclass_serves_only_visible_rows_sync` / `_async`, `::test_djangolistfield_instance_shadowed_all_hook_is_sealed`, `::test_djangolistfield_resolver_manager_degrading_to_list_fails_closed_sync` / `_async` and the alias-drift test. Decision 3 is the home.
- [x] **Extra spec defect 1 — the `## Key glossary references` anchor `#slice-5--promotion--docs--version` resolves to nothing.** Slice 5 is a checklist item, not a heading. Every other in-page anchor in the file resolves (the three `#decision-10--joint-0_0_7-cut` uses were corrected during the extraction, since a dotted version slugs to `007`).
- [x] **Extra spec defect 2 — the link-definition ref-ids `[spec-011]: spec-015-relay_interfaces-0_0_5.md` and `[spec-014]: spec-018-meta_primary-0_0_6.md` name pre-renumber card numbers**, so a reader following the ref-id reaches a different spec than the id implies. `START.md`'s link convention makes the def block the single place a rename lands; these two ids were never re-pointed.

---

## Review (Worker 3)

**How the diff was read.** The concurrent maintainer session has both spec-side files **staged**, and the index happens to hold exactly the post-MOVE / pre-R1 state (`git show :docs/SPECS/spec-020-list_field-0_0_7.md | wc -c` = 85,576; the rationale = 65,445). So plain `git diff -- <path>` is precisely R1's isolated delta and `git diff HEAD -- <path>` is MOVE + R1 combined. Both were read. R1's delta: spec `+172 / -112` (85,576 -> 99,343), rationale `+110 / -18` (65,445 -> 95,982).

**Round-scope declarations, stated rather than left blank.**

- **Failability proofs: none owed, and their absence is not a finding.** The diff adds no boundary, guard, gate, or rejection path — it is two Markdown files (`docs/builder/BUILD.md` `### What needs a proof, and what does not`). Independent re-run set: **empty, legally** — no boundary meets the mandatory floor because there is no boundary. Worker 1's `### Boundary count` of zero is confirmed by reading the diff: every hunk is prose, a link definition, a checkbox, or a fenced illustrative block.
- **Hot-path budget: not applicable.** Plan declares hot-path `none`; nothing in the diff is executable, so there is no per-request / per-resolver / per-row cost to measure. No missing-number finding.
- **Floor verification: not applicable.** Plan declares scope `none`; no Django / Strawberry / channels seam is touched. Where the reconciled prose reasons about later behavior it names cards, not version floors — confirmed by grep: zero `0.0.1[1-9]` occurrences in the spec (the two `0.0.10` hits are pre-existing `DONE-034-0.0.10` card references).
- **`scripts/review_inspect.py`: skipped.** No `.py` file is added or modified by the diff (`git diff --name-only` returns two `.md` paths), so none of the trigger conditions in `docs/builder/BUILD.md` `### When to run the helper during build` fires. Repeated-literal evidence for the DRY findings below was gathered by direct grep instead.
- **Cross-cohort duplication review: not applicable this round.** R1 is a single cohort of one worker; R2 is not yet dispatched. F13 and F14 are R2's and the round is not graded on them.

### High:

#### H1 — `## Non-goals` item 3 still sources the coroutine-in-sync rejection to `types/relay.py` and still calls it a bare `ConfigurationError`. Both halves are false at HEAD.

`docs/SPECS/spec-020-list_field-0_0_7.md`, `## Non-goals`, numbered item 3 (line 144 at time of review):

> Preserve the `cls.get_queryset(...)` cooperation contract from [`spec-015-relay_interfaces-0_0_5.md`][spec-015] ... and the same `ConfigurationError` for coroutine-in-sync mismatch **from `types/relay.py`** fires for `DjangoListField` consumers.

R1 edited this line — it is the site where `spec-011` became `spec-015` — and left the second clause untouched. At HEAD:

- `django_strawberry_framework/types/relay.py` does not own that rejection. It *imports* `apply_type_visibility_async` / `apply_type_visibility_sync` from `django_strawberry_framework/utils/querysets.py` (`types/relay.py #"from ..utils.querysets import ("`, lines 43-44) and re-exports `SyncMisuseError` from the same module purely for import compatibility (`types/relay.py #"from ..utils.querysets import SyncMisuseError as SyncMisuseError"`). The rejection body is `django_strawberry_framework/utils/querysets.py::reject_async_in_sync_context`, called from `::apply_type_visibility_sync`.
- The exception is `SyncMisuseError`, not a bare `ConfigurationError` — which is exactly the correction R1 made in four other places (Decision 3, `## Current state`, `## Test plan`'s sync-rejection entry, Definition of done 9). The spec now contradicts itself on the same fact within one file.

**Why this matters beyond the citation.** This is the **seventh** occurrence of the F1 population, and it is the one that shows why the population was undercounted twice (Worker 0 said four sites, Worker 1 re-derived six). The grep both passes ran was on the dead symbol names `_apply_get_queryset_sync|_apply_get_queryset_async`. This site names the *module* and not the symbol, so it is invisible to that instrument no matter how carefully the grep is re-run. An enumerated population is not greppable by its own vocabulary when part of it is spelled in a different vocabulary.

**Recommended change (Worker 1).** Rewrite the clause to the shipped contract: the coroutine-in-sync rejection is `SyncMisuseError` (a `ConfigurationError` subclass) raised by `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync`, the same rejection every read surface receives. Then re-sweep on the *module* names as well as the symbol names — `grep -n 'types/relay\.py' docs/SPECS/spec-020-list_field-0_0_7.md` returns three hits; the other two (lines 72 and 473, both citing the `in_async_context` import site) are **correct and should stay**, verified at `django_strawberry_framework/types/relay.py #"from strawberry.utils.inspect import in_async_context"`.

### Medium:

#### M1 — Decision 5 calls the row-bound guard "a fifth check" one sentence after asserting the guard order is load-bearing. Shipped, it runs first.

`docs/SPECS/spec-020-list_field-0_0_7.md`, `### Decision 5 — Validation & error shapes`:

> The four checks above are ordered, and the order is load-bearing — each target-type check assumes the previous one passed.
>
> A fifth check guards the row bound: ...

At HEAD the `max_rows` guard runs **before** all four target guards:

```django_strawberry_framework/list_field.py::DjangoListField
    if max_rows is not None:
        validate_collection_bound(max_rows, field="DjangoListField max_rows")
    # Decision 5 validation guards: the four shared DjangoType-target ...
    _validate_djangotype_target(target_type, resolver, field="DjangoListField")
```

It is observable, not cosmetic — proved by temp test (see `### Temp test verification`): `DjangoListField("not-a-class", max_rows=0)` raises `DjangoListField max_rows must be a positive integer; got ...`, **not** `DjangoListField requires a DjangoType class`. A reader who takes "fifth" literally in a paragraph that has just told them ordering is load-bearing will predict the wrong error.

The spec's own Decision 2 sketch, rewritten in this same diff, shows the correct order (`validate_collection_bound` first, then `_validate_djangotype_target`), so the two sections disagree.

**Recommended change.** Drop the ordinal. State that the row-bound guard runs first, ahead of the target guards, and that the load-bearing ordering claim covers the four target checks among themselves.

#### M2 — the async-spelling enumeration is presented as closed at "three" and HEAD supports four; the fourth is the very test F4 cites as evidence.

Four sites added or rewritten by this diff enumerate what `is_async_callable` detects, and all four stop at three spellings:

- `## User-facing API`, **Async consumer resolvers** paragraph — "sees an `async def`, an instance whose `__call__` is `async def`, and a one-hop `functools.partial` around either".
- `### Decision 2`, **Three consumer-resolver arms** paragraph — same three.
- `## Edge cases and constraints`, the rewritten `functools.partial` entry — "**all three** async spellings build the async wrapper" (an explicit count, so this one is a false claim rather than an incomplete list).
- `## Definition of done` item 1 — "(`async def`, an `async def __call__` instance, or a one-hop `functools.partial` around either)".

`django_strawberry_framework/utils/typing.py::_callable_inspection_target` peels `functools.partial` **and `staticmethod`** in a `while` loop, so `is_async_callable` also sees a raw `staticmethod async def` descriptor and arbitrary nestings of the two (its docstring names the staticmethod case as its third motivating shape). That spelling is pinned for this field by `tests/test_list_field.py::test_djangolistfield_async_staticmethod_resolver_gets_get_queryset_applied` — which the build plan's F4 lists as one of its four evidence tests, and which the rationale's own F4 change record names. The reconciliation therefore wrote a closed enumeration that its own evidence falsifies.

Root cause worth recording: Worker 0's F4 characterised the predicate as "the `__call__`/`functools.partial`-aware superset of `inspect.iscoroutinefunction`" — a phrase lifted from `list_field.py`'s inline comment, which is itself an abbreviation, not the predicate's contract. That phrase propagated verbatim into the spec in three places. **The docstring, not a comment quoting it, is the contract.**

**Recommended change.** Either add the `staticmethod` arm to each enumeration, or convert the lists to open form ("including ...") and point at `django_strawberry_framework/utils/typing.py::is_async_callable` as the authority. Fix "all three async spellings" either way — a bare count is what makes this one false rather than merely thin.

#### M3 — the Slice 1 async-detection bullet still says "Same `iscoroutinefunction`/coroutine handling", two lines above the bullet R1 corrected off that predicate.

`docs/SPECS/spec-020-list_field-0_0_7.md`, `## Slice checklist`, Slice 1 (line 72), unchanged by this diff:

> - [ ] Async detection uses the same `in_async_context` hook the Relay defaults use — pin the import as ... **Same `iscoroutinefunction`/coroutine handling.**

The default resolver contains no `iscoroutinefunction` at all — it branches on runtime `in_async_context()` only (`django_strawberry_framework/list_field.py::DjangoListField #"if in_async_context():"`), and the consumer wrapper uses `is_async_generator_callable` / `is_async_callable`. The immediately following bullet, rewritten in this diff, says so. This is the fourth occurrence of the F4 population and it survived for the same reason H1 did: the finding's grep vocabulary was the *replacement* symbol, and this site names only the retired one in a trailing sentence fragment.

**Recommended change.** Delete the trailing sentence, or restate it as the construction-time predicates the following bullet already names.

#### M4 — three of the rationale's seven in-page anchors are dangling, all three introduced by this diff, and two of them are in the resolution table that exists to make items lookup-able.

Re-derived by slugging every heading in `docs/SPECS/appx/spec-020-list_field-0_0_7-rationale.md` and differencing the used anchor set (code fences stripped first, per the known trap):

| Dangling anchor | Where R1 wrote it |
|---|---|
| `#decision-5--validation--error-shapesspec-020-d5` | `## Provenance of this record`, the corrected "kept in the spec deliberately" bullet |
| `#decision-3--get_queryset-and-async-symmetryspec-020-d3` | `## Verified against the shipped code` table, the Decision-3 Option-A row |
| `#decision-9--example-app-migration-posturespec-020-d9` | `## Verified against the shipped code` table, the DoD-5 row |

The rationale's decision headings are `### [Decision N — ...][spec-020-dN]`, so the rendered heading text — and therefore the slug — is the link text alone: `#decision-5--validation--error-shapes`. R1 appended the ref-id to the slug as well. Note this is the *same class* of anchor defect the round was dispatched to fix (extra spec defect 1, and the `#decision-10--joint-0_0_7-cut` -> `007` correction before it): a reference-style heading's slug is not its raw source text.

This is Medium rather than Low because of `docs/builder/BUILD.md`'s requirement that a rationale entry be reachable by heading and anchor. `## Verified against the shipped code` is the section whose whole job is "here is where each deferred item landed", and two of its six rows point at nothing.

**Recommended change.** Drop the `spec-020-dN` suffix from all three anchors, then re-run the whole-file anchor sweep against the **rationale** as well as the spec — the postcondition R1 recorded (`### Implementation steps` step 8) covers both files, but the `## Verified against the shipped code` table's own wording says the sweep was "re-derived by slugging all headings" for *the spec*. The rationale was not swept.

#### M5 (DRY) — the row-bound contract is now stated in full in five places in the spec, and near-verbatim in `docs/GLOSSARY.md`.

Cross-referenced in `### DRY findings` below; carried here because `docs/builder/BUILD.md` `!!IMPORTANT — DRY FIRST!!` puts duplication at the same tier as a defect and the severity mapping for this round makes a duplicated statement Medium.

### Low:

#### L1 — "later cards have added more of them on the same terms" is a change log inside the contract.

`docs/SPECS/spec-020-list_field-0_0_7.md`, `### Decision 9 — Example-app migration posture`, the surrounding-resolvers constraint (line 579), added by this diff:

> The pre-existing `all_library_*` resolvers each carry `order_by("id")` for deterministic test ordering; this card does NOT migrate any of them, **and later cards have added more of them on the same terms.**

The clause is true and it is the only sentence in the reconciled spec that asks the reader to hold a timeline. It also earns nothing: the contract is "this card migrates none", and the count-avoidance rationale for dropping "seven"/"eight" (correctly recorded in the rationale) applies equally to a prose gesture at growth. Not history-narration in the banned sense — it narrates the example app, not the spec's own revisions — which is why it is Low rather than Medium.

**Recommended change.** Cut the trailing clause. If the growth fact is worth keeping it belongs in the rationale, which already carries it with the HEAD measurement.

#### L2 — Decision 3's list of the sealed helpers' consumers reads as closed and is four of about nine.

`docs/SPECS/spec-020-list_field-0_0_7.md`, `### Decision 3`, added by this diff:

> ... the shared sealed-boundary helpers in `django_strawberry_framework/utils/querysets.py`, the single site every recomposing read surface uses — the Relay node defaults, the connection root, this field, and the cascade

`grep -rn 'apply_type_visibility_sync\|apply_type_visibility_async' django_strawberry_framework/` (excluding the defining module) shows call sites in `types/relay.py`, `connection.py`, `list_field.py`, `permissions.py`, `filters/sets.py`, `types/resolvers.py`, `optimizer/walker.py`, and `mutations/resolvers.py`. The leading clause ("the single site every recomposing read surface uses") is true and is the load-bearing half, so the em-dash list reads as illustrative and this is Low. Flagged because the same closed-looking-enumeration shape produced M2 and understated F1 twice in this cycle; making it explicitly open ("e.g. ...") costs two characters.

### DRY findings

**D1 — the row-bound contract, stated five times in the spec and a sixth time near-verbatim in a generated standing doc.** This is the round's largest duplication and every copy but one was added by this diff.

The contract has three clauses: the policy's `max_list_rows` applies unconditionally; `max_rows=` narrows; `trusted_max_rows=True` is the only widening (plus the gloss that `max_rows=None` means "the policy governs", not "no bound"). All three clauses appear in:

1. `## User-facing API` -> `### Row bound` (new subsection, with the worked example) — the natural canonical home.
2. `### Decision 5 — Validation & error shapes`, the row-bound-guard paragraph.
3. `## Non-goals`, the pagination bullet ("Row **limits** are not out of scope and are not optional: every `DjangoListField` is row-bounded").
4. `## Out of scope`, the pagination/limits bullet ("Row **limits** are the opposite of out of scope — every `DjangoListField` is row-bounded via the request's resource policy, narrowed by `max_rows=` and widened only by `trusted_max_rows=True`").
5. `## Definition of done` item 8 ("the request policy's `max_list_rows` applies unconditionally, `max_rows=` narrows it, `trusted_max_rows=True` is the only widening").

Sites 3 and 4 are near-identical to each other and neither adds anything site 1 lacks; each was written for a different finding (F3 twice over) — which is the specific "did one finding's fix restate another's" case, answered yes.

Site 6 is `docs/GLOSSARY.md` `## \`DjangoListField\`` -> `**Row bound (\`0.0.14\`, spec-047).**`, which reads:

> Every `DjangoListField` is bounded: the request's execution resource policy supplies `max_list_rows` whether or not the field says anything, and `max_rows=` narrows it further for this field. There is no unbounded spelling - `max_rows=None` means "the policy governs" ... `trusted_max_rows=True` is the only way a field can be wider than the policy.

against the new spec subsection:

> Every `DjangoListField` is row-bounded. The request's execution resource policy supplies `max_list_rows` whether or not the field says anything; `max_rows=` narrows it further for this field, and `trusted_max_rows=True` is the only way a field can be wider than the policy. There is no unbounded spelling — `max_rows=None` means "the policy governs".

Same sentences, resequenced. Both are in turn near-copies of `django_strawberry_framework/list_field.py::DjangoListField`'s docstring **Row bound** paragraph. `docs/GLOSSARY.md` is DB-generated and R2's to touch, so the spec is the copy that can move: a spec restating a standing generated doc sentence-for-sentence is drift with a delay fuse, and the delay is one glossary regeneration.

**Recommended change.** Keep site 1 as the one full statement and make it the anchor. Reduce 3, 4 and 5 to the one clause each actually needs plus a pointer to `### Row bound` (Non-goals and Out of scope need only "row limits are mandatory, not optional — see [Row bound]"; DoD 8 needs only "the returned queryset is row-bounded per [Row bound]"). Site 2 can keep the guard sentence, which is Decision 5's own subject, and shed the narrowing/widening restatement. On the glossary overlap: state the contract once in the spec and let the glossary entry be the consumer-facing copy — or shorten the spec subsection to the field-facing surface (`max_rows=` / `trusted_max_rows=` and the worked example) and cite `[GLOSSARY.md#djangolistfield][glossary-djangolistfield]`, which the spec already links.

**D2 — the bound-applied-last reasoning, four times.** "A sliced queryset cannot be refiltered or reordered, so slicing first would break every type with a hook" appears in the Slice 1 checklist step 3, the Decision 2 sketch's inline comment, the post-sketch **The row bound is applied last** paragraph, and DoD item 8 — and is a near-verbatim copy of `django_strawberry_framework/list_field.py::_bounded_async`'s docstring. The Decision 2 paragraph is the right home (it is where the async branch's extra coroutine wrapper is justified). The other three should assert the ordering without re-deriving it.

**Existence challenge.** Raised and answered negatively: there is no new abstraction in this diff to challenge — no helper, registry, indirection, or token, and the one new spec structure (`### Row bound`) earns its existence as the canonical home D1 recommends. The reverse challenge is D1 itself: four of the five row-bound statements should not exist.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is empty. `__all__` and the re-export list are unchanged. No new public exports; consistent with Definition of done item 19 ("exactly one new public export", `DjangoListField`, shipped at `0.0.7`).

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. Confirmed independently rather than on the plan's word: `git diff HEAD --name-only` for this round returns only the two spec-side `.md` paths. `CHANGELOG.md`'s `[0.0.7]` `### Added` entry was read and is accurate as to contract; its pre-renumber card labels are the maintainer-escalated cluster and are correctly not touched here.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Applicable — the diff is entirely an archived spec and its companion.

- **Version strings / statuses / card IDs.** `Status: shipped (\`0.0.7\`, 2026-05-27); archived. Card \`DONE-020-0.0.7\`.` unchanged and correct. Decision 10's card enumeration now matches `KANBAN.md #"\`0.0.7\` shipped 2026-05-27 with seven cards"` — all seven verified present by id. No version string was introduced by the diff; `pyproject.toml` / `__init__.py` remain at `0.0.14` and the spec correctly does not claim otherwise.
- **In-page anchors.** Spec: 17 anchors used, 35 headings, **zero dangling** — re-derived, code fences stripped first, dotted-version slug rule applied (`#decision-10--joint-007-cut` resolves; `#decision-10--joint-0_0_7-cut` would not, and does not appear). Extra spec defect 1 is genuinely closed: both `#slice-5--promotion--docs--version` uses now point at `#slice-checklist`, which exists. Rationale: **3 dangling of 7** — M4.
- **Reference-style link convention.** Spec: 40 defs, 40 used, zero undefined, zero unused, zero non-existent paths on disk. Rationale: 13 defs, 13 used, zero undefined, zero unused, zero non-existent. All 10 canonical group headers present and in the prescribed order in both files. Extra spec defect 2 closed: `[spec-011]`/`[spec-014]` are gone, `[spec-015]`/`[spec-018]` resolve to the right files from `docs/SPECS/`, and the `<!-- docs/SPECS/ -->` group is alphabetical after the rename.
  - Pre-existing, **not an R1 finding, do not fix as part of this round**: in strict ASCII order `[glossary]` sorts before `[glossary-*]` in the spec's `<!-- docs/ -->` group, and `[spec-020]` before `[spec-020-d*]` in the rationale's `<!-- docs/SPECS/ -->` group. Both orderings predate R1 (the spec's from the archive, the rationale's from the MOVE) and the `source-layout` hook accepts them.
- **`AGENTS.md` rule 27.** Re-derived: zero single-colon `path:Symbol` forms and zero raw `path:NN` in either file (`grep -oE '[A-Za-z0-9_/.-]+\.(py|md|html|toml):[A-Za-z0-9_]+'` and the `:[0-9]+` variant both return nothing). The two forbidden forms F1 and F2 named (`types/base.py:_format_unknown_fields_error`, twice) are both converted to `::`. The `bld-*.md` artifact's raw refs are permitted by `START.md` "Temp artifact conventions".
- **Obsolete staging wording.** No "planned", "coming soon", or `TODO(` was introduced. Slice 3's two anomalous `- [x]` boxes are now `- [ ]`, so the file is uniformly unticked and the `Status:` line is the only completion signal — the correct resolution for a Done card, and the rationale records why ticking-all was rejected.
- **Verbatim-copy check.** Not applicable; the diff copies no spec text into KANBAN / CHANGELOG / GLOSSARY (that is R2's work). No fenced-code drop-in with matching inner/outer fence counts was added; the two new/edited fences use standard triple backticks with no nested fence.
- **Script-rendered docs.** Not applicable; the diff touches no generated doc and no module docstring.
- **The spec does not narrate its own history — confirmed mechanically and by reading.** Zero `[Rr]ev[0-9]` occurrences (down from 248 at HEAD). Zero occurrences of `as of`, `originally`, `later corrected`, `previously`, `used to be`, `superseded`, `no longer`, `has since`, `retract`, `amend`, `reconcil`, or `R1`. Zero `spec-034` / `spec-045` / `spec-047` attributions — the shipped contracts from those cards are stated as contract, not as later corrections, which is exactly the rule. The only backward-looking sentence is the pre-existing pointer to the rationale companion in the preamble, which is the mechanism, not residue. L1 is the single remaining chronology-flavored clause and it is about the example app, not the spec's drafts. **This, the load-bearing rule of the cycle, is met.**
- **Rationale usable as the review instrument.** Every R1 change record sits under the entry for the decision or section it belongs to (Decisions 1, 2, 3, 4, 5, 8, 9, 10 and the `## Current state`, `## Implementation plan`, `## Slice checklist`, `## Edge cases and constraints`, `## Test plan`, `## Doc updates`, `## Definition of done` entries), each names its finding, each carries what was rejected while writing it, and each closes with a **Claims this decision may no longer make** list that was extended rather than replaced. `## Claims the spec may no longer make` gained 14 rows, matching the report. `## Not verified against the shipped code by this pass` -> `## Verified against the shipped code`: all six of the original items (four claim bullets plus two anchor defects) are present as table rows with outcomes; **none was dropped**, and the section opens by stating it is a record of outcomes and not a to-do. Nothing in either file survives as an open action item. The only defect in the instrument is M4's three dead anchors.

### What looks solid

- **The reconciliation is real, not cosmetic.** Every one of the twelve findings' substance is in the spec, and the two highest-value ones are handled the way they should be: the `functools.partial` DOES-NOT-WORK block is **deleted**, not moved or softened (it was actively instructing consumers to hand-rewrap a resolver that works), and Decision 3's "call the hook and use what comes back" is replaced by the sealed-boundary contract with its five unprovable-return shapes and seven pinning tests. Both were spot-checked against source and both are accurate.
- **Every test name the spec cites exists.** Re-derived rather than accepted: all 20 distinct `test_*` identifiers in the spec resolve to a `def` in `tests/` or `examples/`. This includes the one Worker 0 got wrong — the spec carries `::test_djangolistfield_resolver_manager_alias_drift_fails_closed_sync`, not the finding's `::test_djangolistfield_alias_drift_fails_closed_sync`. The five names in the *rationale* that do not exist on disk (`test_djangolistfield_rejects_non_bool_nullable_list`, `..._nullable_list_toggle_renders_nullable_outer`, `..._consumer_resolver_override_bypasses_default`, and the two promoted ones) are all correctly framed there as authoring-round history or as retired-and-promoted, which is a rationale's job. Not findings.
- **Decision 2's rewritten sketch matches HEAD.** Read line-by-line against `django_strawberry_framework/list_field.py`: the signature, the `_bounded_async` async-default branch, the three-arm dispatch with `is_async_generator_callable` first, the `isinstance(source, AsyncIterable) and not isinstance(source, Iterable)` sync-arm check, and the bound-applied-last placement in all four return paths are all faithful. `_bounded_async`, `_require_async_iterable_context`, `_resolve_async_iterable` and `_validate_djangotype_target` are all module-local to `list_field.py` as the following paragraph claims.
- **Decision 5's quoted error messages are character-accurate** against `_validate_djangotype_target`'s two `ConfigurationError` bodies, including the new "or it inherits a definition from a parent without declaring its own `Meta`" clause. The own-class-origin invariant is stated as the contract with an explicit "`hasattr` is NOT sufficient", which is the right strength — a guard documented as looser than it is invites a later "simplification".
- **F9's import graph is correct as written, not as dispatched.** Verified: `connection.py:71` and `relay.py:65` both import `_validate_relay_djangotype_target` **only**, and reach the four-guard base through it (`_validate_relay_djangotype_target` delegates to `_validate_djangotype_target` then adds `_is_relay_shaped`). `relay.py::_validate_node_target` is the wrapper `DjangoNodeField` / `DjangoNodesField` call. Worker 1 caught Worker 0's error here and wrote the paragraph to the real graph.
- **Every other load-bearing symbol spot-checked and true.** `utils/querysets.py::initial_queryset`, `::apply_type_visibility_sync` (and its `#"reject_async_in_sync_context"` anchor), `::apply_type_visibility_async`, `::post_process_queryset_result_sync` / `_async`, `::normalize_query_source`; `resource_policy.py::bounded_rows` (bound applied by slicing, `result[:limit]`), `::bounded_rows_async`, `::validate_collection_bound` (rejects non-int, `bool`, and `< 1`), `::effective_bound` (confirms `trusted=True` is the only widening and `None` defers to the policy); `optimizer/extension.py::_resolve_model_from_return_type` returning `_OriginAndModel | None` and `_optimize` delegating coercion to `normalize_query_source`; `utils/querysets.py::SyncMisuseError` multiple-inheriting `ConfigurationError` **and** `RuntimeError` exactly as Decision 3 now claims; the coroutine-close-before-raise behavior in `reject_async_in_sync_context`. Count re-derived: `tests/test_list_field.py` holds **41** test functions, matching F7 and the rationale.
- **Postconditions hold.** `scripts/check_spec_glossary.py --spec docs/SPECS/spec-020-list_field-0_0_7.md` exits 0 with 24 terms. `scripts/check_trailing_commas.py --check` exits 0 over both spec-side files and this artifact. The plan's repo-wide baseline exception (an untracked `.claude/` memory file) was not treated as a round finding and was not touched.
- **DRY posture of the split itself is right.** The rationale states what changed and why, and where it needs the contract it names the spec section instead of restating it. D1/D2 are duplication *within* the spec and against the glossary, not across the pair — the seam Worker 1 identified as the main risk held.

### Temp test verification

- `docs/builder/temp-tests/review-1/test_guard_order.py` — one test, run with `uv run pytest ... --no-cov -q`, **passed**, proving M1: with a bad target *and* a bad `max_rows`, the constructor raises the `max_rows` error, so `validate_collection_bound` runs before the four target guards. (Confirms the shipped order; the assertion is written so it would fail if the spec's "fifth check" ordering were the real one.)
- Disposition: **kept as review evidence only, not for promotion.** It pins no new behavior — it distinguishes two orderings of existing guards to settle a documentation claim, and the shipped order is already covered by `tests/test_list_field.py::test_djangolistfield_rejects_a_non_positive_max_rows_at_construction`. The directory is gitignored (`.gitignore:192`). No temp test caught a code defect; no promotion is owed.

### Notes for Worker 1 (spec reconciliation)

**Four corrections to the build plan's finding list, on top of the three Worker 1 already recorded.** Reported rather than worked around, per `docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching`.

1. **F1's population is seven sites, not four (Worker 0) and not six (Worker 1).** The seventh is `## Non-goals` item 3 — H1. Both undercounts came from the same instrument: a grep on `_apply_get_queryset_sync|_apply_get_queryset_async`. This site names `types/relay.py` and no symbol, so no amount of care with that grep finds it. **The generalisable lesson, worth carrying past this cycle:** when a finding is "symbol X is dead", the population is every claim that *depends* on X's location or behavior, and part of that population is always spelled without X's name. Sweep the module path, the exception class, and the behavior sentence too — here, `grep -n 'types/relay\.py'` plus `grep -n 'ConfigurationError.*coroutine'` would each have caught it.
2. **F4's population is four sites, not three.** The fourth is the Slice 1 async-detection bullet's trailing "Same `iscoroutinefunction`/coroutine handling" — M3. Same instrument blindness: the sentence names the retired predicate in a fragment attached to a bullet about a *different* (and correct) mechanism.
3. **F4's characterisation of `is_async_callable` is incomplete and propagated into the spec three times.** "the `__call__`/`functools.partial`-aware superset of `inspect.iscoroutinefunction`" is `list_field.py`'s inline comment, not the predicate's contract; `utils/typing.py::_callable_inspection_target` also peels `staticmethod`, and F4's own fourth evidence test is the staticmethod case — M2. Prefer the docstring over a comment that abbreviates it.
4. **F3 is silent on guard order and the reconciliation guessed wrong.** F3 named the second error site correctly but not that it fires *first*; Decision 5 now says "a fifth check" — M1.

**Escalated: the spec-vs-`docs/GLOSSARY.md` overlap is a contract-level call, not a wording one.** D1 site 6 is a near-verbatim duplicate of a **generated** standing doc's paragraph, and R2 owns that doc. Two resolution paths, and the choice affects what R2 writes:

- **(a) Spec defers.** Shorten the spec's `### Row bound` to the field-facing surface (`max_rows=` / `trusted_max_rows=`, the worked example, the "no unbounded spelling" clause) and cite `[GLOSSARY.md#djangolistfield][glossary-djangolistfield]` for the policy-interaction prose. Cheapest, and it puts the standing doc in charge of a `0.0.14` contract this `0.0.7` spec only inherits.
- **(b) Spec owns, glossary defers.** Keep the spec subsection whole and have R2 trim the glossary's Row-bound paragraph to a pointer. Costs an R2 DB edit and re-render, and makes an archived spec the authority for a later card's contract — which is the shape that produced this whole residual series.

My reading favours (a), but it is Worker 1's and the maintainer's call, not mine.

**One cross-surface inconsistency R2 will meet, flagged now so it is not discovered as a fresh finding.** `docs/GLOSSARY.md` `## \`DjangoListField\`` still says "the sync path rejects an async `get_queryset` with `ConfigurationError`, mirroring the Relay defaults". After this round the spec says `SyncMisuseError` throughout, and the glossary already carries a `SyncMisuseError` entry of its own. This is technically true (`SyncMisuseError` subclasses `ConfigurationError`) so it is not a false claim, but it is looser than the reconciled spec and it is in the entry F14 is already reopening. Fold it into F14's edit rather than leaving the two surfaces at different precisions.

**Not re-opened, deliberately.** The build plan's `### Verified NOT a finding` list (`docs/TREE.md`, `GOAL.md`, `docs/README.md` line 107, `TODAY.md` line 374, `CHANGELOG.md` line 168) was checked for consistency with the reconciled spec and no contradiction surfaced; none is re-litigated here. The two maintainer-escalated reference clusters (`CHANGELOG.md`'s pre-renumber `0.0.7` labels, `KANBAN.md`'s `apps.py` mis-attribution) are correctly untouched, and the rationale's `## Verified against the shipped code` section records them where a later pass will find them. F13 and F14 are R2's and are not graded here; Worker 1's F13 judgement call (satisfy the obligation, restate only the shape) is well-argued and the "Earlier alpha surfaces" target it hands R2 is satisfiable as written.

**Counts re-derived versus counts stated.**

| Claim | Worker 1 stated | Re-derived | Verdict |
|---|---|---|---|
| dangling in-page anchors, spec | 0 | **0** | holds |
| dangling in-page anchors, rationale | 0 | **3** | **false** — M4 |
| undefined ref-ids, spec / rationale | 0 / 0 | 0 / 0 | holds |
| unused link defs, spec / rationale | 0 / 0 | 0 / 0 | holds |
| non-existent def paths, spec / rationale | 0 / 0 | 0 / 0 | holds |
| `check_spec_glossary.py` on the spec | exit 0 | exit 0, 24 terms | holds |
| `check_trailing_commas.py --check`, both files | exit 0 | exit 0 | holds |
| `AGENTS.md` rule-27 violations remaining | 0 | 0 | holds |
| dead `_apply_get_queryset_*` sites fixed | 6 of 6 | 6 fixed, **7 exist** | **incomplete** — H1 |
| `iscoroutinefunction` sites fixed | 3 (implied) | 3 fixed, **4 exist** | **incomplete** — M3 |
| rows appended to `## Claims the spec may no longer make` | 14 | 14 | holds (`git diff \| grep -c '^+|'` = 22 = 14 claim rows + 6 verified rows + that table's 2 header lines) |
| items resolved in the retitled verified section | 6 of 6, none dropped | 6 of 6, none dropped | holds |
| `tests/test_list_field.py` test count | 41 | 41 | holds |
| spec bytes after R1 | 99,343 | 99,343 | holds |
| rationale bytes after R1 | 95,982 | 95,982 | holds |

### Review outcome

`revision-needed`.

One High (H1: a statement that is false at HEAD, which the severity table makes a spec-contract violation) and five Medium findings, none of which carries a recorded rejection reason, so the acceptance gate in `docs/builder/worker-3.md` forbids acceptance. None of the six is a re-litigation of a design choice the rationale already settled, and none requires a code change — every one is a wording fix inside the two files R1 already owns.

**Dispatched-findings checklist audit — all 14 boxes.** Every tick has a matching edit in the diff; none is a phantom, and there are no unrecorded deferrals. Three ticks are matched by an **incomplete** fix rather than no fix:

| Box | Confirmed from the diff | Note |
|---|---|---|
| F1 | partially | six of seven sites — H1 |
| F2 | yes | own-class-origin invariant stated as the contract, `hasattr` explicitly refused, error message accurate |
| F3 | partially | signature, second error site and the row-bound surface all landed; the guard's *position* is misstated — M1 |
| F4 | partially | the DOES-NOT-WORK block is deleted and the entry inverted correctly, but the spelling enumeration is closed at three — M2 — and Slice 1's trailing fragment survives — M3 |
| F5 | yes | third arm named in Decision 2, User-facing API, Slice 1, DoD 1 and 11, with the `SyncMisuseError` sync-execution rejection |
| F6 | yes | Decision 8 boundary line carries both halves plus the reason; User-facing API carries the pointer |
| F7 | yes | counts dropped, two promotions named with their live file, Test-plan preamble scoped, Slice 3 boxes normalised |
| F8 | yes | three fields named in Decision 9, Slice 4 and DoD 5; both competing counts removed |
| F9 | yes | Decision 1 paragraph, written to the verified import graph |
| F10 | yes | seven cards, matching `KANBAN.md` |
| F11 | yes | `_OriginAndModel \| None` and `normalize_query_source` both cited, reasoning untouched |
| F12 | yes | sealed boundary in Decision 3 with seven pinning tests; cascade non-goal reworded |
| Extra 1 | yes | both uses now `#slice-checklist`; zero dangling anchors in the spec |
| Extra 2 | yes | `[spec-015]` / `[spec-018]`, defs re-pointed and the group left alphabetical |

Boxes I could **not** confirm from the diff: none. The three partials above are confirmable-but-incomplete, not unconfirmable.

**What re-review needs.** H1 and M1-M3 are four sentences of spec wording; M4 is three anchor strings plus a re-run of the anchor sweep against the rationale; M5/D1-D2 are a consolidation pass whose shape depends on the escalated (a)/(b) choice. L1 and L2 are optional and may be rejected with a reason. Nothing here reopens a rejected alternative or asks for a code change.

---

## Final verification (Worker 1)

Not performed by this pass. `docs/builder/ARTIFACT.md` `## Status field ownership` routes `review-accepted` to Worker 0, which spawns Worker 3's review; a **fresh** Worker 1 then performs final verification and sets `final-accepted` or `revision-needed`. The pass that authored the spec edits is not permitted to be its own final auditor, so this section stays empty and `Status:` stops at `review-accepted`.

**Superseded:** the pass did run, after Worker 3's pass-2 re-review. Its section is the last one in this artifact, under the same heading; the subsections below this paragraph belong to the reconciliation build report.

### Spec changes made (Worker 1 only)

Every edit below is to `docs/SPECS/spec-020-list_field-0_0_7.md` unless the section name says otherwise. Sections are cited by heading and content, not by line number: the file grew by 60 lines during the pass, so a line number pinned mid-pass would be a false citation by the time it was read (`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`).

| Spec section | Change | Why | Finding |
|---|---|---|---|
| Preamble `Predecessors:` line, and the `<!-- docs/SPECS/ -->` link-definition group | `[spec-011]` → `[spec-015]`, `[spec-014]` → `[spec-018]`, defs re-pointed and re-alphabetized | the ref-ids named pre-renumber card numbers, so the id contradicted its own target | extra defect 2 |
| `## Key glossary references` (two uses) | `#slice-5--promotion--docs--version` → `#slice-checklist` | the anchor resolved to nothing; Slice 5 is a checklist item, not a heading | extra defect 1 |
| `## Slice checklist`, Slice 1 default-resolver body (sync and async) | dead helper names → `initial_queryset` / `apply_type_visibility_sync` / `apply_type_visibility_async`; `return qs` → the `bounded_rows` / `bounded_rows_async` return | the cited helpers do not exist, and the step list omitted the row bound entirely | F1, F3 |
| `## Slice checklist`, Slice 1 `resolver=` bullet | three construction-time arms; `is_async_callable` replaces `inspect.iscoroutinefunction`; async-only-iterable rejection added | the bullet described a two-way split with the wrong predicate | F4, F5 |
| `## Slice checklist`, Slice 1 metadata bullet | gained `max_rows=` / `trusted_max_rows=` | the pass-through list was the field's whole documented kwarg surface and was incomplete | F3 |
| `## Slice checklist`, Slice 2 validation bullet | `arg.__django_strawberry_definition__` exists → carries its **own** registered definition (`definition.origin is arg`, never `hasattr`); `types/base.py:_format_unknown_fields_error` → the `::` form | the guard is stricter than documented, and the citation used the forbidden single-colon form | F2 |
| `## Slice checklist`, Slice 3 (both sub-checks) | `- [x]` → `- [ ]`; the "18 TODO stubs" count dropped; live-tier promotion noted | two ticked boxes in an otherwise-unticked shipped file read as partial completion; the stub count is not re-derivable from disk | F7 |
| `## Slice checklist`, Slice 4 first bullet | one added field → the three that shipped; "other seven `@strawberry.field` resolvers" → "every pre-existing" | the posture landed as three fields and the count was falsified twice over | F8 |
| `## Slice checklist`, Slice 5 `README.md` sub-bullet | shape prescription restated against the file's current `## Status` structure; obligation kept | the prescribed shape describes a `README.md` that no longer exists; the obligation itself is unmet and still owed | F13 (spec half; R2 owns the file) |
| `## Slice checklist`, Slice 5 `TODAY.md` sub-bullet, and `## Doc updates`'s `TODAY.md` bullet | reconciled to the landed shape: named in the capability list, no individual root field spelled | the file was rewritten into a compact list where naming one root field is off-voice | plan's "verified NOT a finding" note |
| `## Problem statement` | "the sync + async `_apply_get_queryset_*` ports from spec-011" → the shipped visibility-hook application, cited to `spec-015` by ref-id | fifth occurrence of the dead symbols, plus a pre-renumber card number in prose | F1 |
| `## Current state`, the visibility-helper bullet | rewritten to name `utils/querysets.py::apply_type_visibility_sync` / `_async` and the `SyncMisuseError` rejection | the bullet defined symbols that do not exist and claimed the field re-uses them verbatim | F1 |
| `## Non-goals`, cascade bullet | states that the cascade rides the type's own `get_queryset` and needs no field-side code, citing the test | the cascade contract reached this field and the spec was silent | F12 |
| `## Non-goals`, pagination bullet | "returns the unbounded queryset" → no pagination arguments and no order tiebreaker, and row limits are mandatory | the sentence was flatly false at HEAD | F3, F6 |
| `## User-facing API`, expected-behavior list | gained the row-bound pointer and an explicit no-order-guarantee bullet | a reader who never reaches Decision 8 is exactly the reader who assumes list order is stable | F3, F6 |
| `## User-facing API`, consumer-resolver and async-consumer paragraphs | `inspect.iscoroutinefunction` → `is_async_callable`; async generator and sync-returning-async-iterable arms named | wrong predicate, missing arm | F4, F5 |
| `## User-facing API`, new `### Row bound` subsection | added, with a worked `max_rows=` / `trusted_max_rows=` example | the field's mandatory row bound had no consumer-facing documentation in the spec at all | F3 |
| Decision 1 | new paragraph: `list_field.py` is the home of the shared field-target validation contract, with both guards and all three importing factories cited | "where does a guard change land" is a fact about the module this spec created and was not derivable from the decision | F9 |
| Decision 2, the pseudo-code sketch | rewritten against `list_field.py`: real imports, the full signature, three arms, bound-applied-last | the sketch imported dead symbols; a sketch that names non-existent helpers is a wrong instruction, not an abstraction | F1, F3, F4, F5 |
| Decision 2, the paragraph after the sketch | three new paragraphs: where each helper lives, the three-arm contract with its six pinning tests, why the bound is applied last | the sketch's new shape needs its contract stated normatively, not inferred from code | F1, F5, F3 |
| Decision 2, async-detection asymmetry bullet | `inspect.iscoroutinefunction(user_resolver)` → `is_async_callable(user_resolver)`, with an explicit statement that `iscoroutinefunction` is **not** used and why | the asymmetry paragraph is the one a maintainer reads before "harmonizing"; it named the wrong half | F4 |
| Decision 3 | rewritten: helpers live in `utils/querysets.py` under their shipped names; new sealed-boundary paragraph with its seven pinning tests; the Option-A/relocation deferral removed | Option A was reversed by the trigger this decision itself named, and the helpers are no longer thin hook-appliers | F1, F12 |
| Decision 4, `_optimize` and walker bullets | `normalize_query_source` named; `_resolve_model_from_return_type`'s `_OriginAndModel \| None` return named | citations drifted one level; the reasoning is intact | F11 |
| Decision 5 | signature gained `max_rows=` / `trusted_max_rows=`; guard 3 rewritten as the own-class-origin invariant with an explicit "`hasattr` is NOT sufficient"; ordering-is-load-bearing note added; fifth (row-bound) guard added; error-site count one → two; `types/base.py:` → `::` | the documented guard was looser than the shipped one, and the constructor's surface was two arguments and one error site short | F2, F3 |
| Decision 8, boundary line | ordering added to both halves — no guarantee for the list, pk tiebreaker for the connection — plus the reason the asymmetry is deliberate | ordering is the other place the two primitives diverge and the boundary line was silent on it | F6 |
| Decision 9 | three added fields named; "the other seven" → "the pre-existing", no count | the posture landed as three fields, and both competing counts are now false | F8 |
| Decision 10 | five cards → the seven that shipped, and the phrasing no longer leads with a number | the enumeration was stale; a leading count invites the same staleness again | F10 |
| `## Implementation plan` table, Slice 2 and Slice 3 rows | "4 validation tests" and "14 behavior tests" counts removed; per-test enumerations kept | five validation tests shipped, and 41 tests live in the file; a count here measures the file's whole history, not this card's slice | F7 |
| `## Edge cases and constraints`, `functools.partial` entry | rewritten as a positive statement that all three async spellings work; the DOES-NOT-WORK code block **deleted** (not moved) and the WORKS block kept and extended; loud-rejection trio added | the entry told a reader to hand-rewrap a partial that works — the round's highest-value single fix | F4 |
| `## Test plan`, section preamble | states the list is the contract pins this card owes, not an inventory of the file | 23 of the file's 41 tests belong to later cards; a spec claiming to enumerate a shared file acquires a false claim per card | F7 |
| `## Test plan`, two promoted entries | now name the live tests and their file, with the reason for the tier and the surviving companion's `NOTE:` block | the two are absent from the package file by design; listing them there reads as a lost test | F7 |
| `## Test plan`, sync-coroutine-rejection entry | `ConfigurationError` → `SyncMisuseError` (a `ConfigurationError` subclass), cited to `apply_type_visibility_sync` | the cited contract site was a dead symbol | F1 |
| `## Out of scope`, pagination/limits bullet | limits split out as explicitly mandatory | "Pagination / limits … not on the roadmap" is false for limits | F3 |
| `## Definition of done` items 1, 4, 5, 7, 8, 9, 11 | each restated to what shipped; the row bound folded into item 8 rather than added as a new item | six items were false as written; a new item would renumber 16-20, which are cited by number from the build plan and the rationale | F1, F2, F3, F5, F7, F8 |

**Rationale-file changes** (`docs/SPECS/appx/spec-020-list_field-0_0_7-rationale.md`, Worker 1 owns it). Every spec change above is recorded there under the entry for the decision or section it belongs to, each with what was rejected while writing it: change records added to Decisions 1, 2, 3, 4, 5, 8, 9 and 10 and to the `## Current state`, `## Implementation plan`, `## Slice checklist`, `## Edge cases and constraints`, `## Test plan`, `## Doc updates` and `## Definition of done` entries; fourteen rows appended to `## Claims the spec may no longer make`; the `## Provenance of this record` "kept in the spec deliberately" bullet for the `hasattr` anchor corrected, because that bullet was itself one of the false claims; and `## Not verified against the shipped code by this pass` **resolved and retitled** to `## Verified against the shipped code`, every one of its six items carrying its outcome and the entry it moved into, so it cannot survive as an open to-do.

**No deferrals.** Every box in `### Dispatched findings checklist` is `- [x]` and every tick has a row above.

### Notes for Worker 1 (spec reconciliation)

**F13's judgement call — decided: satisfy the obligation, restate only the shape. Round 2 inherits an unmet obligation, not a retracted one.**

`grep -n DjangoListField README.md` returns nothing, so `README.md` does not carry the symbol anywhere. The spec's Slice 5 bullet prescribed a shape — surface it "inline at `README.md #\"## Status\"` alongside the version-pin sentence rather than introducing a bullet list that doesn't match the file's voice" — and the file has since been restructured: `## Status` now carries a "**Newest shipped**" block plus an "Earlier alpha surfaces" list running `0.0.13` down to `0.0.8`, with no `0.0.7` entry. The prescription describes a file that no longer exists. The two resolutions were to satisfy the obligation or to retract it.

Reasons for satisfying it:

1. The file's own idiom is now precisely the bullet list the original prescription was steering away from, so "match the file's voice" **today means a list entry**. The prescription's intent survives its letter.
2. The "Earlier alpha surfaces" list stops at `0.0.8` for no stated reason. Nothing in `README.md` says its status prose deliberately declines to reach `0.0.7`, so retracting the obligation would mean inventing a policy in order to excuse a gap.
3. Definition of done item 16 requires the named docs — `README.md` among them — to reflect the shipped state. Retracting the Slice 5 bullet while item 16 stands would half-reconcile the spec, the failure mode `worker-1.md` "Review-round custody" names as worse than not reconciling at all.

Rejected: retract the bullet and record that `README.md`'s status prose no longer reaches back to `0.0.7`. It is the cheaper edit, and it converts a real documentation gap into a documented non-goal — exactly the move a residual-closeout cycle exists to prevent.

**What R2 inherits.** The spec's Slice 5 `README.md` sub-bullet now names a satisfiable target rather than a prescription needing reinterpretation: the `## Status` section's "Earlier alpha surfaces" list, its newest-first ordering, a `0.0.7` entry leading with `DjangoListField` in that list's one-line-per-version voice, and `KANBAN.md #"## Done"` as the authoritative content for the seven-card cut. R2 owns `README.md`; the spec is already reconciled to expect the edit, so R2 needs no spec amendment for F13. The reasoning is recorded in the rationale under `### `## Doc updates``.

**Two related items R2 does not need to act on**, both reconciled here rather than left as doc gaps: `TODAY.md`'s Doc-updates bullet (the file was rewritten into a compact capability list where naming one root field would be off-voice — the bullet now matches the landed shape) and the `## Problem statement` / `## Current state` resolver counts (left as found; both sections are explicitly a pre-card baseline snapshot, so a later card growing the schema does not falsify them the way it falsified Decision 9 and DoD item 5).

**Three corrections to the build plan's finding list**, recorded here because `docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching` treats a wrong verification as worth reporting rather than working around, and because Worker 0 owns the plan file and this custodian may not edit it:

1. **F1 undercounts its own population by one.** The finding enumerates four spec sites citing the dead symbols (Decision 2's sketch, Decision 3's two bullets, the Slice 1 checklist, DoD 9). There is a fifth, in `## Current state`, and a sixth in `## Problem statement` — both found only by re-running the grep the finding was derived from rather than by walking its list. All six are fixed. An enumerated finding's site list is a sample; the population is what the grep returns.
2. **F9 names the wrong import.** The finding says `list_field.py::_validate_djangotype_target` **and** `::_validate_relay_djangotype_target` "are imported by `connection.py` … and by `relay.py`". Only the Relay variant is imported by either: `grep -rn '_validate_djangotype_target\|_validate_relay_djangotype_target' django_strawberry_framework/` shows `connection.py:71` and `relay.py:65` importing `_validate_relay_djangotype_target` alone, which reaches the four-guard base internally. The finding's substance — that `list_field.py` is the home of the shared field-target validation contract for three factories — holds exactly as stated, and the spec paragraph is written to the verified import graph.
3. **F12 cites a test name that does not exist.** The finding names `::test_djangolistfield_alias_drift_fails_closed_sync`; the shipped test is `tests/test_list_field.py::test_djangolistfield_resolver_manager_alias_drift_fails_closed_sync`. The other six names in F12 are exact. The spec cites the real name.

None of the three changes a verdict; each would have propagated as a false citation into the spec had the finding been transcribed rather than re-derived.

---

## Build report (Worker 1, apply-changes pass 2)

Status set: `review-accepted`. This pass fixes H1 and M1-M5 and accepts L1 and L2, all inside the two spec-side files R1 already owns. No source, test, or standing doc was touched; nothing in the diff is executable.

- **Dispatch-routing deviation, mirrored here from the build plan.** `worker-0.md` `## Per-slice dispatch` step 4 routes a Worker 3 `revision-needed` to Worker 2, and on R1 it cannot: the whole diff is `docs/SPECS/spec-020-list_field-0_0_7.md` and its rationale companion, which `docs/builder/BUILD.md` `## Spec reconciliation` makes custodian-only, so dispatching Worker 2 would require Worker 2 to break that rule to do the work. On R1 only, `revision-needed` routes back to Worker 1; Worker 3 re-reviews after this pass and a fresh Worker 1 performs final verification, so the authoring pass is never its own auditor. Recorded in the build plan under `## Dispatch-routing deviation, recorded once for both rounds`; R2 follows the standard routing.

### Findings disposition

| Finding | Disposition | Measured population |
|---|---|---|
| H1 | Fixed. Goals item 3 (Worker 3 cites it as `## Non-goals` item 3; the numbered item 3 is under `## Goals` — `## Non-goals` is a bullet list) now names `utils/querysets.py::apply_type_visibility_sync` and `SyncMisuseError` via `::reject_async_in_sync_context` | `types/relay.py` occurrences in the spec: 3 before, 2 after; the two survivors are the `in_async_context` import-site citations Worker 3 verified as correct |
| M1 | Fixed. The ordinal is gone; the row-bound guard is stated as running first, ahead of the four target checks, which are ordered among themselves | source order re-derived at `list_field.py::DjangoListField`: `validate_collection_bound` then `_validate_djangotype_target` |
| M2 | Fixed. Every enumeration either names the four wrapper shapes or defers to `is_async_callable` outright | **six** sites, not four: the four Worker 3 named plus Slice 1's `resolver=` bullet and Decision 2's async-detection-asymmetry bullet. Found by grepping `aware superset` (2 occurrences, both fixed) and `one-hop` (3 -> 0), not the word "three" |
| M3 | Fixed. The trailing `Same iscoroutinefunction/coroutine handling` fragment is deleted | `iscoroutinefunction` occurrences in the spec: 5 before, 4 after; the 4 survivors are contrastive statements about what the predicate is **not** (Decision 2's asymmetry bullet, the `functools.partial` edge case), each now also naming the `staticmethod` blind spot |
| M4 | Fixed. All three dangling rationale anchors lost the appended ref-id | rationale: 7 anchors used / 3 dangling before, 10 used / **0** dangling after. Spec unchanged at 17 used / 0 dangling |
| M5 / D1 | Fixed by the judgement call below. Five full statements in the spec plus one in the glossary -> one field-facing statement in `### Row bound` plus a clause-and-pointer at each of the other four sites | `max_list_rows` occurrences in the spec: 4 before, 1 after (the deferral clause); `trusted_max_rows=True` prose occurrences: 3 before, 1 after |
| D2 | Accepted in part, rest rejected with a reason (recorded in the rationale under `### `## User-facing API``). DoD 8 no longer restates the narrowing/widening contract | the *derivation* occurs **once** (`refiltered`: 1 occurrence, Decision 2's post-sketch paragraph — D2's own recommended home). The other three sites are one-clause assertions, which is D2's recommended end state; collapsing them to pointers would make a checklist step unfollowable and DoD 8 unverifiable |
| L1 | Fixed. The trailing `and later cards have added more of them on the same terms` clause is cut; the HEAD growth measurement stays in the rationale | 1 occurrence |
| L2 | Fixed. The consumer list is explicitly illustrative (`e.g.`) rather than re-enumerated | 8 call-site modules outside the defining one, as Worker 3 measured; not restated in the spec |

### Spec changes made (Worker 1 only)

Sections cited by heading and content, never by line number — the file grew during the pass.

| File / section | Change | Why | Finding |
|---|---|---|---|
| Spec `## Goals`, item 3 | the coroutine-in-sync clause now names `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync`, `::reject_async_in_sync_context` and `SyncMisuseError` (a `ConfigurationError` subclass) | both halves of the old clause were false at HEAD, and four other sites in the same file already said so | H1 |
| Spec `## Slice checklist`, Slice 1 async-detection bullet | trailing `Same iscoroutinefunction/coroutine handling.` deleted | the default body branches on runtime `in_async_context()` alone; the next bullet already names the construction-time predicates | M3 |
| Spec `## Slice checklist`, Slice 1 `resolver=` bullet | the `__call__`/`functools.partial`-aware superset abbreviation replaced by the wrapper-aware superset plus the shapes it also sees | one of two M2 sites the finding did not name | M2 |
| Spec `## User-facing API`, async-consumer paragraph | four shapes named, and the predicate declared the authority for the list | the enumeration was closed at three and HEAD supports four | M2 |
| Spec `## User-facing API`, `### Row bound` | rewritten to the field-facing surface (`max_rows=` / `trusted_max_rows=` / no unbounded spelling) with the policy-composition half deferred to the glossary entry | the subsection restated a generated standing doc sentence-for-sentence | M5 / D1 |
| Spec `### Decision 2`, three-arms paragraph | arm (b) names the `staticmethod` descriptor and nestings, citing `is_async_callable` and `_callable_inspection_target` | closed enumeration | M2 |
| Spec `### Decision 2`, async-detection-asymmetry bullet | the `iscoroutinefunction` blind-spot list gained the raw `staticmethod` descriptor | second M2 site the finding did not name; a blind-spot list closed at two invites the same "harmonization" the bullet exists to prevent | M2 |
| Spec `### Decision 3`, sealed-helper consumer list | `— the Relay node defaults` -> `— e.g. the Relay node defaults` | the list read closed at four of eight call-site modules | L2 |
| Spec `### Decision 5` | `The four checks above are ordered` -> `The four target checks above are ordered among themselves`; `A fifth check guards the row bound` -> the guard runs **first**, with the observable consequence stated; the narrowing/widening restatement replaced by a pointer to `### Row bound` | shipped, `validate_collection_bound` runs ahead of every target guard, in the one paragraph whose subject is order | M1, D1 |
| Spec `### Decision 9`, surrounding-resolvers constraint | trailing `and later cards have added more of them on the same terms` cut | a timeline the reader must hold, for no contract gain | L1 |
| Spec `## Edge cases and constraints`, `functools.partial` entry | `all three spellings` -> every spelling the predicate covers, with the `staticmethod` descriptor named and its pinning test cited | an explicit count, so this site was a false claim rather than a thin list | M2 |
| Spec `## Non-goals`, pagination bullet | reduced to one clause plus a pointer to `### Row bound` | near-copy of the `## Out of scope` bullet, both written for F3 | D1 |
| Spec `## Out of scope`, pagination/limits bullet | reduced to one clause plus a pointer to `### Row bound` | as above | D1 |
| Spec `## Definition of done` item 1 | the async-callable parenthetical defers to `is_async_callable` | closed enumeration | M2 |
| Spec `## Definition of done` item 8 | row bound asserted by pointer plus the applied-last ordering; policy/narrow/widen restatement dropped | the item must stay checkable, but not by restating a contract stated in full elsewhere | D1, D2 |
| Rationale `## Provenance of this record` | the `Decision 5` anchor de-suffixed; new paragraph on how this file's anchors slug (reference-style headings, and code-span headings keeping a leading hyphen) | one of the three dangling anchors, plus the mechanism that produced all three | M4 |
| Rationale `## Verified against the shipped code`, Decision-3 and DoD-5 rows | anchors de-suffixed | two dangling anchors in the section whose whole job is lookup | M4 |
| Rationale — new `### `## Goals`` entry | H1's record: what was false, why the symbol-name grep could not reach it, what was rejected, and the claims the section may no longer make | every spec change is recorded under the entry for the section it belongs to | H1 |
| Rationale `### `## Non-goals`` | D1's record for the two near-copy bullets | as above | D1 |
| Rationale `### [Decision 2 …]`, `### [Decision 3 …]`, `### [Decision 5 …]`, `### [Decision 9 …]` | change record appended to each, each with what was rejected while writing it, and each decision's `Claims this decision may no longer make` list extended | as above | M2, L2, M1, D1, L1 |
| Rationale `### [Decision 5 …]` | the earlier record's own `F3 added the fifth guard` wording corrected to `the row-bound guard` | the rationale carried the same ordinal error it was recording | M1 |
| Rationale `### `## User-facing API`` | M2's population and instrument lesson; the (a)/(b) glossary decision with its rejected alternative; the D2 measurement and the reason three assertion sites stay | the two judgement calls and the round's measured populations belong keyed to the sections they govern | M2, D1, D2 |
| Rationale `### `## Slice checklist` — the dropped sub-check` | M3's record: deleted rather than restated, and why the fragment was invisible to the sweep | as above | M3, M2 |
| Rationale `### `## Definition of done`` | record for items 1 and 8 | as above | M2, D1 |
| Rationale `## Claims the spec may no longer make` | five rows appended (H1, M1, M2, M3, L2) | the index is the reviewer's instrument for checking the contract against the reasoning | all |
| Rationale link-definition block | `[glossary-djangolistfield]: ../../GLOSSARY.md#djangolistfield` added under `<!-- docs/ -->` | the (a) decision cites the glossary entry from the rationale too; the def path was verified on disk | D1 |

**No deferrals.** Every dispatched finding is either fixed or rejected with the reason recorded in the rationale (D2 in part only).

### Judgement calls decided

1. **The spec-vs-`docs/GLOSSARY.md` row-bound overlap — decided (a): the spec keeps the field-facing surface, the glossary keeps the policy contract.** `docs/GLOSSARY.md` is the standing, generated, consumer-facing doc, and the row bound is a `0.0.14` (spec-047) contract this `0.0.7` spec only inherits; making an archived spec the authority for a later card's contract is the shape this residual series exists to unwind, and (b) would cost a DB edit and a re-render to buy it. The reason and the rejected alternative are recorded in the rationale under `### `## User-facing API``.
2. **The glossary's `rejects … with ConfigurationError` wording** is R2's to tighten; see the note below.

### Notes for Worker 1 (spec reconciliation)

**What Round 2 inherits from the (a) decision.** Nothing new to write, and one thing not to do:

- **Do not trim the glossary's `DjangoListField` -> **Row bound** paragraph.** Under (a) it is the authority for how `max_list_rows` and `max_rows=` compose, and the spec now cites it rather than restating it. R2 owes no glossary edit for D1, and the spec needs no amendment for it either.
- **Required glossary amendment, to fold into F14 rather than land as a second precision.** `docs/GLOSSARY.md`'s `DjangoListField` entry says the sync path "rejects an async `get_queryset` with `ConfigurationError`, mirroring the Relay defaults". After this pass the spec says `SyncMisuseError` at every site, including Goals item 3. The glossary wording is not false (`SyncMisuseError` multiple-inherits `ConfigurationError` and `RuntimeError`) but it is looser than the reconciled spec, the glossary already carries its own `SyncMisuseError` entry, and F14 is reopening this very entry. R2 should name `SyncMisuseError` and, per the glossary's own DB-generated status, make the change in the fakeshop glossary app DB and re-render — never by hand-editing `docs/GLOSSARY.md`.
- **F13 is unchanged by this pass.** The Slice 5 `README.md` sub-bullet still names the satisfiable target recorded in the first pass's notes; no re-reading is needed.

**Two corrections to Worker 3's review, reported rather than worked around.** Worker 3 corrected Worker 0 four times and this custodian three; the reverse is possible and neither of these changes a verdict.

1. **H1's section is `## Goals`, not `## Non-goals`.** The review heading, its body and its checklist row all say `## Non-goals` item 3. The quoted sentence is numbered item 3 of `## Goals`; `## Non-goals` is a bullet list with no numbered items, and its third bullet is the cascade non-goal. The quote and the two false halves are exactly as reported, so the finding is right about everything that matters — but a reader following the section name would edit the wrong list.
2. **M2's population is six sites, not four**, and M2's own root-cause note is what predicts the two extras: it identifies the propagated characterization ("the `__call__`/`functools.partial`-aware superset of `inspect.iscoroutinefunction`") as the vector, and that phrase occurs at two sites the finding's four-site list does not include — Slice 1's `resolver=` bullet and Decision 2's async-detection-asymmetry bullet. Both state the predicate's coverage without stating a count, so a sweep keyed on "three" cannot see them. Same instrument lesson the review itself records, one level in.

**Not re-opened.** The build plan's `### Verified NOT a finding` list, the two maintainer-escalated reference clusters, and every design choice the rationale already settled are untouched. Worker 3's `### What looks solid` items were not re-derived; nothing in this pass contradicts them.

### Gates

| Gate | Result |
|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-020-list_field-0_0_7.md` | **exit 0** — `OK: 24 terms`. Re-run after the row-bound collapse specifically because collapsing prose can strip a term's last carrier; no term lost its only link (`[glossary-djangolistfield]` gained a use, `[glossary-configurationerror]` gained a use) |
| `uv run python scripts/check_trailing_commas.py --check` on the two spec-side files and this artifact | **exit 0**. The repo-wide baseline exception (an untracked, gitignored `.claude/` agent-memory file) was not touched |
| Dangling in-page anchors — spec | **0** (17 anchors used, 35 headings) |
| Dangling in-page anchors — **rationale** (the count that failed last pass) | **0** (10 anchors used, 29 headings; was 3 of 7) |
| Undefined ref-ids — spec / rationale | **0 / 0** |
| Unused link defs — spec / rationale | **0 / 0** |
| Non-existent def paths on disk — spec / rationale | **0 / 0** |
| `AGENTS.md` rule 27 — single-colon `path:Symbol` or raw `path:NN` in either file | **0 / 0** |

The anchor sweep was re-derived with a GitHub-slugger-faithful script over both files: fences stripped, reference-style heading labels reduced to their link text, and **no post-punctuation trim** — that last detail matters, because a heading whose text is a code span beginning with `##` slugs with a leading hyphen (`#-definition-of-done`), and a slugger that trims reports three such live anchors as dangling. A trimming instrument would have produced 6 dangling here and sent Worker 3's 3 back as a disagreement.

### Byte counts

| File | Before this pass | After |
|---|---|---|
| `docs/SPECS/spec-020-list_field-0_0_7.md` | 99,343 | 100,594 |
| `docs/SPECS/appx/spec-020-list_field-0_0_7-rationale.md` | 95,982 | 108,525 |

The spec grew 1,251 bytes net while shedding four full statements of the row-bound contract: H1's clause, M1's guard-position statement and M2's six enumerations each cost more characters than the abbreviation they replace, and a pointer is not free. The rationale carries the pass's explanation, which is where the growth belongs.

### Re-review needs

Worker 3's re-review has three re-derivable claims and one judgement to check: the six-site M2 population (`aware superset` and `one-hop` are the sweep tokens), the `refiltered`-is-one-occurrence basis for the partial D2 rejection, the rationale's zero dangling anchors under a non-trimming slugger, and whether (a) is the right call for the glossary overlap. No code change is requested and no rejected alternative is re-opened.

---

## Review (Worker 3, pass 2 — re-review of the apply-changes pass)

Scope: narrow, as dispatched. Confirm H1, M1, M2, M3, M4, M5/D1, D2, L1 and L2 are closed and that the fix pass introduced nothing new. The reconciliation's accepted substance, the build plan's `### Verified NOT a finding` list, the two maintainer-escalated clusters, and F13 / F14 (Round 2's) are not re-opened.

**How the diff was read.** Both spec-side files are still **staged** by the concurrent maintainer session at exactly the post-MOVE / pre-reconciliation state (`git show :docs/SPECS/spec-020-list_field-0_0_7.md | wc -c` = 85,576; the rationale = 65,445, both copied read-only to a scratch path outside the repo per `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`). Neither `git diff` nor `git diff HEAD` isolates *this* pass, so pass 2 was checked the way the dispatch prescribed: every row of `### Spec changes made (Worker 1 only)` (pass 2 table) walked against the file, plus an independent re-derivation of every stated count. No `git stash` / `checkout` / `restore` / `worktree` was used.

**Round-scope declarations, each with its reason rather than left blank.**

- **Failability proofs: none owed.** The diff introduces no boundary, guard, gate, or rejection path — it is two Markdown files (`docs/builder/BUILD.md` `### What needs a proof, and what does not`). Independent re-run set: **empty, legally** — no boundary meets the mandatory floor because there is none.
- **Hot-path budget: not applicable.** The plan declares hot-path scope `none`; nothing in the diff is executable, so there is no per-request / per-resolver / per-row cost to measure. No missing-number finding.
- **Floor verification: not applicable.** The plan declares scope `none`; no Django / Strawberry / channels integration seam is touched. Re-confirmed: the reconciled prose names cards, not version floors.
- **`scripts/review_inspect.py`: skipped.** No `.py` file is added or modified, so no trigger in `docs/builder/BUILD.md` `### When to run the helper during build` fires.
- **Cross-cohort duplication review: not applicable.** R1 is one cohort of one worker; R2 is not dispatched.
- **Temp tests: none this pass.** The prior pass's `docs/builder/temp-tests/review-1/test_guard_order.py` settled M1 behaviorally and M1's fix was verified this pass by reading source order directly (`django_strawberry_framework/list_field.py::DjangoListField`, `validate_collection_bound` then `_validate_djangotype_target`), so no new temp test was needed. No promotion is owed.

### High:

**None.** H1 is closed.

**H1 — confirmed fixed, and true at HEAD.** `## Goals` item 3 now reads: an async `get_queryset` met on the sync path "is rejected with `SyncMisuseError` — the [`ConfigurationError`][glossary-configurationerror] subclass raised by `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` (via `django_strawberry_framework/utils/querysets.py::reject_async_in_sync_context`)". Verified against source, not inferred from the spec:

- `django_strawberry_framework/utils/querysets.py::SyncMisuseError` is `class SyncMisuseError(ConfigurationError, RuntimeError)`.
- `::reject_async_in_sync_context` is the body that raises it (`#"raise SyncMisuseError("`), after disposing the awaitable.
- `::apply_type_visibility_sync` calls it (`#"result = reject_async_in_sync_context("`) on the hook's return.
- `django_strawberry_framework/types/relay.py` neither owns nor raises it, exactly as the fix now says.

`types/relay.py` occurrences in the spec: **2**, matching the report's 3 -> 2. Both survivors are the `in_async_context` import-site citations (spec lines 72 and 473), verified correct at `django_strawberry_framework/types/relay.py #"from strawberry.utils.inspect import in_async_context"`.

**On the section name: Worker 1 is right and the prior Worker 3 pass was wrong.** The quoted sentence is numbered **item 3 of `## Goals`**. `## Non-goals` is a bullet list with no numbered items (its third bullet is the cascade non-goal). Re-derived by reading both sections. The prior review's heading, body and checklist row all say `## Non-goals`, and a reader following that section name would have edited the wrong list — a real defect in the review record, correctly reported by Worker 1 rather than worked around. The prior section is left as written (it is not mine to rewrite); this paragraph is the correction of record.

### Medium:

**None.** M1-M5 are all closed. Evidence per finding:

- **M1 — fixed.** The ordinal is gone. `### Decision 5` now reads "The four target checks above are ordered among themselves" and, separately, "The row-bound guard runs **first**, ahead of all four target checks", with the observable consequence stated and `tests/test_list_field.py::test_djangolistfield_rejects_a_non_positive_max_rows_at_construction` cited. True at HEAD: `list_field.py` calls `validate_collection_bound` (line 187) before `_validate_djangotype_target` (line 191). Zero occurrences of "fifth check" survive in the spec, and the rationale's own earlier "F3 added the fifth guard" wording is corrected too.
- **M2 — fixed, at all six sites.** Re-derived rather than accepted: every one of `## Slice checklist` Slice 1's `resolver=` bullet, `## User-facing API`'s async-consumer paragraph, `### Decision 2`'s three-arms paragraph, `### Decision 2`'s async-detection-asymmetry bullet, `## Edge cases and constraints`' `functools.partial` entry, and `## Definition of done` item 1 now either names the raw `staticmethod` descriptor and the partial/staticmethod nestings, or defers outright to `django_strawberry_framework/utils/typing.py::is_async_callable` as the authority. The false explicit count ("all three async spellings") is gone. The source claim holds: `::_callable_inspection_target` peels `functools.partial` **and** `staticmethod` in a `while` loop, and `is_async_callable`'s docstring names the raw-`staticmethod` descriptor as its third motivating shape. `tests/test_list_field.py::test_djangolistfield_async_staticmethod_resolver_gets_get_queryset_applied` exists.
- **M3 — fixed.** `grep -c 'Same \`iscoroutinefunction'` on the spec returns **0**; the trailing fragment is deleted, not restated. See the count adjudication below for the four-vs-five question, which is a defect in the report's number and not a residue in the spec.
- **M4 — fixed.** Re-derived with my own github-slugger-faithful sweep (fences stripped, reference-style heading labels reduced to their link text, **no post-punctuation trim**), and the instrument hand-validated first against a heading I could confirm: `### \`## Definition of done\`` slugs to `-definition-of-done` with a leading hyphen, and the anchor actually used in the file is `](#-definition-of-done)` — so the non-trimming rule is the correct one and Worker 1's caveat is right. Result: spec **0 dangling** (35 headings), rationale **0 dangling** (29 headings, 10 anchor uses). All three previously dangling `…spec-020-dN`-suffixed anchors are de-suffixed and resolve.
- **M5 / D1 — fixed, and the cure did not overshoot.** `max_list_rows` occurrences in the spec: **1**. `trusted_max_rows=True` prose occurrences: **1**. The reverse question was asked at each of the four trimmed sites and the answer is no — the spec still states the shipped contract everywhere it matters:
  - `### Row bound` keeps "Every `DjangoListField` is row-bounded", "`max_rows=` narrows", "`trusted_max_rows=True` is the only spelling that lets the field be wider than the request's policy", "no unbounded spelling — `max_rows=None` means the policy governs", plus the worked example. Only the *composition* half is deferred.
  - `## Non-goals` pagination bullet: "Row **limits** are neither out of scope nor optional: every `DjangoListField` is row-bounded, see [Row bound]".
  - `## Out of scope`: "Row **limits** are the opposite of out of scope — every `DjangoListField` is row-bounded (see [Row bound])".
  - `## Definition of done` item 8: "The queryset is row-bounded per [Row bound], and the bound is applied by slicing after the visibility hook and any consumer post-processing" — still checkable on its own.
  - `### Decision 5` keeps only the guard, its position and its two pinning tests.
  **The deferral target was verified to carry what was deferred**, which is the part a pointer can silently get wrong: `docs/GLOSSARY.md` `## \`DjangoListField\`` -> **Row bound** does state that the policy supplies `max_list_rows` whether or not the field says anything, that `max_rows=` narrows further, and that `trusted_max_rows=True` is the only widening. The `[glossary-djangolistfield]` def resolves to `docs/GLOSSARY.md#djangolistfield`, which exists. So (a) leaves no clause homeless.
- **D2 — partial rejection accepted on its merits.** Re-derived: `refiltered` occurs **once** in the spec, in `### Decision 2`'s post-sketch **The row bound is applied last** paragraph, which is D2's own recommended home. The other three sites are one-clause assertions with no re-derivation (`bounded_rows` line 67's "the row bound is applied LAST, after the visibility hook has composed onto the unsliced source"; the sketch's inline comment; DoD 8). That is D2's recommended end state, so the rejection is a measured reason and not a refusal — legitimate under `docs/builder/BUILD.md` `## Subagent dispatch` step 4. The source facts behind the assertion hold: `resource_policy.py::bounded_rows` applies the bound as `result[:limit]` and its docstring says it is applied by SLICING; `::effective_bound` confirms `None` defers to the policy, `trusted=True` returns the declared value, and otherwise `min(...)`.

### Low:

**None outstanding as blockers.** L1 and L2 are closed; two items are recorded below, one escalated.

- **L1 — fixed.** `grep -c 'later cards have added more of them'` on the spec returns **0**; the growth measurement stays in the rationale.
- **L2 — fixed.** `### Decision 3`'s consumer list now reads "— e.g. the Relay node defaults, the connection root, this field, and the cascade", explicitly illustrative. (Re-measured for the record: the call-site population is now **10** modules outside `utils/querysets.py`, not the 8 the prior pass measured — `forms/resolvers.py` and `mutations/sets.py` also call in. That the number moved inside one cycle is itself the argument for the `e.g.`; no spec change is owed.)

#### N1 (NEW, Low, pre-existing at HEAD — escalated, not a blocker) — the spec's one cross-*file* dangling anchor: `TODAY.md#optional-fakeshop-visibility-filtering-today`.

`docs/SPECS/spec-020-list_field-0_0_7.md`, `## Current state` (the `get_queryset`-boilerplate bullet) links `[\`Optional fakeshop visibility filtering today\`][today-optional-fakeshop-visibility-filtering-today]`, defined as `../../TODAY.md#optional-fakeshop-visibility-filtering-today`. `TODAY.md` has no heading that slugs to that anchor; the nearest live heading is `## Visibility filtering via \`get_queryset\`` (`#visibility-filtering-via-get_queryset`).

**Provenance, established read-only:** present verbatim in `git show HEAD:docs/SPECS/spec-020-list_field-0_0_7.md` and in the staged pre-reconciliation copy. **Not introduced by either R1 pass.**

Why it is worth recording rather than dropping: every anchor instrument used in this round — R1's postcondition step 8, the prior review's sweep, and Worker 1's pass-2 gate table — measures *in-page* anchors and *path existence on disk*, and none measures a cross-file link's **fragment**. That blind spot is exactly the shape this cycle keeps meeting. And it is adjacent to work this pass did do: the pass reconciled the `TODAY.md` Doc-updates and Slice 5 sub-bullets *because* `TODAY.md` was rewritten into a compact capability list — the same rewrite that deleted this heading — so the file was in hand when the link broke and stayed unswept.

**Escalated to Worker 1's final verification** rather than held at `revision-needed`: it is outside the dispatched F1-F12 + two-extra-defects population, pre-existing at HEAD, and a third apply-changes pass for one link string is not proportionate. Resolution paths: (i) re-point the def at `../../TODAY.md#visibility-filtering-via-get_queryset` and adjust the link text to that heading, or (ii) drop the link and keep the prose. **Add a cross-file-fragment sweep to the postcondition either way** — in-page-only is what let this survive four instruments.

#### N2 (NEW, Low, artifact-only, corrected here rather than sent back) — two of the build report's stated counts are wrong; both because the sweep token survived its own fix.

Recorded because `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` makes a stated count a claim, and every later pass treats it as measured. Neither error changes a verdict and neither is in the spec; the correct numbers are in the table below and are the record from here.

1. **`iscoroutinefunction`: the report says "5 before, 4 after"; the true post-pass count is 5** (across 3 lines). Mechanism: the pass deleted M3's fragment (one occurrence, 5 -> 4) and then, in the *same* pass, rewrote the `## Edge cases and constraints` entry for M2 in a way that carries three occurrences instead of two. The delta was computed from one edit while a second edit in the same pass moved it. `docs/builder/BUILD.md`'s own warning applies literally: measure as you write the number, and measure after the last edit, not after the edit you were thinking about.
2. **`aware superset`: the report says "2 occurrences, both fixed" (2 -> 0); the token still returns 2.** The replacement wording is `wrapper-aware superset`, which the sweep token `aware superset` matches. The substance is fixed — the defective closed abbreviation `` `__call__`/`functools.partial`-aware superset `` returns **0** — but the number as stated is false, and it is false in the one direction a reader cannot detect: a sweep token that survives its own fix reads as an un-fixed population next time somebody re-runs it.

### DRY findings

**D1 / D2: closed** — see the Medium tier above. The five-plus-one row-bound duplication is now one field-facing statement plus a clause-and-pointer at four sites plus the generated glossary's policy paragraph, with no clause left unstated anywhere. The bound-applied-last derivation occurs once.

**No new duplication introduced.** The pass's additions are one pointer per trimmed site and per-decision rationale records; nothing was copied between the spec and the rationale. Re-checked the seam Worker 1 named as the main risk: where the rationale needs the contract it names the spec section (`### Row bound`, `[Decision 5]`) rather than restating it.

**Existence challenge.** Raised and answered negatively: the pass adds no helper, registry, indirection, or token. The one structure added by the previous pass (`### Row bound`) now earns its keep as the single canonical home — which is the outcome D1 asked for, so the challenge resolves in its favour rather than against it.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is empty. `__all__` and the re-export list are unchanged. No new public exports; consistent with `## Definition of done` item 19.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; the pass did not modify `CHANGELOG.md`. Confirmed independently: `git diff HEAD --name-only` restricted to this round's ownership returns only the two spec-side `.md` paths (every other `docs/SPECS/` entry in that listing is a baseline-dirty out-of-scope file the plan enumerates). The pre-renumber `0.0.7` card labels remain the maintainer-escalated cluster and are correctly untouched.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Applicable — the diff is an archived spec and its companion.

- **In-page anchors.** Spec **0 dangling** / 35 headings; rationale **0 dangling** / 29 headings, 10 uses. Instrument hand-validated against a code-span heading before use (see M4).
- **Cross-file anchor fragments — swept independently this pass, and the one instrument nobody had run.** Every reference-style def with a `#fragment` was resolved against the target file's slugged headings. Spec: **1 dangling** (N1, pre-existing at HEAD). Rationale: **0** — all ten `../spec-020-list_field-0_0_7.md#decision-N--…` defs resolve, including `#decision-10--joint-007-cut`, and the newly added `[glossary-djangolistfield]: ../../GLOSSARY.md#djangolistfield` resolves to a real heading.
- **Reference-style link convention.** Spec: 40 defs / 40 used, zero undefined, zero unused, zero non-existent paths. Rationale: 14 defs / 14 used (13 + the new `[glossary-djangolistfield]`), zero undefined, zero unused, zero non-existent paths. All 10 canonical group headers present and in the prescribed order in both files. The pre-existing strict-ASCII ordering notes from the prior pass are unchanged and still not R1 findings.
- **`AGENTS.md` rule 27.** Re-derived on both files: **0** single-colon `path:Symbol` forms and **0** raw `path:NN`. Every new citation this pass added uses `path::QualifiedName` or `path #"substring"`.
- **The spec does not narrate its own history — confirmed mechanically and by reading, after the fix pass.** Zero occurrences in the spec of `[Rr]ev[0-9]`, `as of`, `originally`, `later corrected`, `previously`, `used to be`, `superseded`, `has since`, `retract`, `amend`, `reconcil`, `\bR1\b`, `pass 2`, or `Worker`; zero `spec-034` / `spec-045` / `spec-047` attributions. The single `no longer` is the pre-existing preamble pointer to the rationale companion, which is the mechanism, not residue. L1's clause — the one chronology-flavoured sentence left last pass — is gone, so the spec now carries none at all. **The load-bearing rule of the cycle is met, and the fix pass did not reintroduce narration.**
- **The rationale's 12,543-byte growth is explanation, keyed by heading, not exiled contract.** Read in full at the changed entries. Every new record sits under the entry for the section it governs (`### \`## Goals\`` for H1, `### \`## User-facing API\`` for M2 / D1 / D2, `### [Decision 5 …]` for M1, `### \`## Slice checklist\` — the dropped sub-check` for M3, `## Provenance of this record` for M4, plus `### \`## Non-goals\``, `### \`## Definition of done\``, `### [Decision 2/3/9 …]`), each names its finding, each records what was rejected while writing it, and each extends rather than replaces its `Claims this decision may no longer make` list. Cross-checked specifically for contract exiled out of the spec: the (a) decision moves the policy-composition clause to `docs/GLOSSARY.md`, **not** into the rationale, and the rationale states only why. `## Verified against the shipped code` still carries all six original items with outcomes and reads as a record, not a to-do. The new `## Provenance of this record` paragraph on how this file's anchors slug is the mechanism that produced M4 and is worth having.
- **Verbatim-copy check.** Not applicable; nothing was copied into `KANBAN.md` / `CHANGELOG.md` / `docs/GLOSSARY.md` — the pass moved *away* from restating the glossary. No nested-fence hazard in the edited fences.
- **Script-rendered docs.** Not applicable; no generated doc and no module docstring touched. The `docs/GLOSSARY.md` change the (a) decision implies is deliberately **not** made here (it is R2's, DB-backed).
- **Obsolete staging wording.** None introduced; no `TODO(`, "planned", or "coming soon".

### Judgement call (1) and what Round 2 inherits — checked, present, actionable, and internally consistent

- **The (a) decision is recorded with its rejected alternative** under the rationale's `### \`## User-facing API\`` and summarised in `### Judgement calls decided`. I agree with it on the merits, and it is the reading the prior pass also favoured: an archived `0.0.7` spec should not become the authority for a `0.0.14` contract it only inherits.
- **The "no glossary trim" half is present and correct** under `### Notes for Worker 1 (spec reconciliation)`: R2 owes no glossary edit for D1, and the spec needs no amendment for it. Verified the premise it rests on — the glossary's **Row bound** paragraph does carry the composition contract the spec now defers to it.
- **The F14 glossary amendment is present and actionable**: it names the exact stale wording ("rejects an async `get_queryset` with `ConfigurationError`, mirroring the Relay defaults"), the replacement (`SyncMisuseError`), why it is loose rather than false, and the correct mechanism (edit `GlossaryTerm.body` in the fakeshop DB and re-render, never a hand edit).
- **The two halves are consistent with each other.** They target different paragraphs of the same entry — the amendment is the entry's first paragraph, the do-not-trim is the separate **Row bound** paragraph — verified by reading the entry. R2 can execute both without either undoing the other.

### Gates re-run

| Gate | Worker 1 stated | Re-derived |
|---|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-020-list_field-0_0_7.md` | exit 0, 24 terms | **exit 0**, `OK: 24 terms` |
| `uv run python scripts/check_trailing_commas.py --check` on both spec-side files and this artifact | exit 0 | **exit 0** |

The plan's repo-wide baseline exception (an untracked, gitignored `.claude/` agent-memory file) was not treated as a finding and not touched.

### Counts re-derived versus Worker 1's stated figures

Occurrences, not matching lines, on the shortest distinctive token, measured after the last edit.

| Claim | Worker 1 stated | Re-derived | Verdict |
|---|---|---|---|
| `types/relay.py` in the spec | 3 -> 2 | **2** | holds; both survivors verified correct |
| `iscoroutinefunction` in the spec | 5 -> 4 | **5** (3 lines) | **false number, finding still fixed** — N2.1; all 5 are contrastive |
| M2 population | 6 sites (not 4) | **6**, all fixed | holds |
| `max_list_rows` in the spec | 4 -> 1 | **1** | holds |
| `trusted_max_rows=True` prose | 3 -> 1 | **1** | holds |
| `aware superset` | 2 -> 0 | **2** | **false number, finding still fixed** — N2.2; the defective abbreviation is 0 |
| `one-hop` | 3 -> 0 | **0** | holds |
| `refiltered` (D2 basis) | 1 | **1**, in Decision 2's post-sketch paragraph | holds; rejection sound |
| dangling in-page anchors, rationale | 3 of 7 -> 0 of 10 | **0 dangling**, 10 uses, 29 headings | holds |
| dangling in-page anchors, spec | 0 (17 used) | **0**, 35 headings | holds |
| undefined ref-ids / unused defs / non-existent def paths, spec / rationale | 0 / 0 each | 0 / 0 each | holds |
| rule-27 violations, spec / rationale | 0 / 0 | 0 / 0 | holds |
| "fifth check" surviving in the spec | 0 implied | **0** | holds |
| `Same \`iscoroutinefunction` fragment | 0 | **0** | holds |
| L1 clause `later cards have added more of them` | 0 | **0** | holds |
| Decision 3 sealed-helper call-site modules | 8 | **10** | list is now `e.g.`; no spec change owed |
| spec bytes | 100,594 | **100,594** | holds |
| rationale bytes | 108,525 | **108,525** | holds |
| every `test_*` name cited in the spec exists on disk | implied | **44 distinct tokens; every test function resolves to a `def`** (3 non-matches are path fragments: `test_query`, `test_registry`, `test_scalars`) | holds |

### Adjudication of the `iscoroutinefunction` 4-vs-5 discrepancy

**The true number is 5 occurrences across 3 lines, and every one is legitimately contrastive. M3 is fixed; the report's "4" is the defect.** Read individually:

- Spec `## Slice checklist` Slice 1 `resolver=` bullet — "`is_async_callable` — the wrapper-aware superset of `inspect.iscoroutinefunction`, which also sees … a raw `staticmethod` descriptor". A statement of what the shipped predicate is a superset **of**.
- `### Decision 2` async-detection-asymmetry bullet — "The predicate is deliberately **not** `inspect.iscoroutinefunction`, which returns `False` for a `functools.partial` …, for a callable object with an `async def __call__`, and for a raw `staticmethod` descriptor". An explicit negation, and the one site whose whole job is to stop a later "harmonization".
- `## Edge cases and constraints` `functools.partial` entry — three occurrences, all negative: two demonstrating the predicate returns `False` for the partial and the callable instance, "which is exactly why neither is the predicate the factory uses", and one naming `is_async_callable` as the wrapper-aware superset.

None asserts that the field *uses* `iscoroutinefunction`. The M3 residue was the Slice 1 fragment "Same `iscoroutinefunction`/coroutine handling", which asserted the retired predicate as the mechanism; it returns 0. For the arithmetic: the staged pre-reconciliation spec carried **9** occurrences, pass 1 brought it to 5, pass 2 deleted one (M3) and its M2 rewrite of the edge-case entry added one back — net 5. So the report's "before 5" is right and its "after 4" was computed from one of the two edits.

### What looks solid

- **Every finding is closed at its cause, not at its symptom.** H1 rewrote the clause *and* re-swept on the module name; M3 deleted the fragment rather than restating it; M4 fixed three anchors *and* documented the slug mechanism in the rationale so the next author cannot repeat it; M2 chose "defer to the predicate" at four of six sites rather than copying a four-item list six times, which is the fix that will not go stale when the predicate grows.
- **The two rejections are both measured, not asserted.** D2's partial rejection cites a re-derivable occurrence count and a reason about followability; the (a) glossary decision cites the generated-doc status and the archived-spec-authority argument. Both survive re-derivation.
- **Worker 1 corrected its reviewer twice and was right both times** — the `## Goals` section name and M2's six-site population. It reported them rather than working around them, and its M2 correction is the *better* instrument lesson: the propagated characterization, not the word "three", was the population's vocabulary.
- **The rationale is now usable as the review instrument it is supposed to be.** Every claim I wanted to check about pass 2's reasoning was findable under the section it governs, with the rejected alternative attached.
- **The Decision-5 rationale entry's self-audit is the most valuable paragraph in the pass**: the record that a MOVE's own "kept in the spec deliberately" list is a genre judgement and not a truth check, and that the false sentence survived three reads because each asked "is this deliberation?" and none asked "is this true?". That generalises past this cycle.

### Notes for Worker 1 (spec reconciliation)

1. **Escalated: N1, the pre-existing cross-file dangling anchor** `../../TODAY.md#optional-fakeshop-visibility-filtering-today` in `## Current state`. Pre-existing at HEAD, outside the dispatched population, so not held at `revision-needed`. Resolution paths in N1. **Independently of the string, add a cross-file-fragment sweep to the postcondition**: four separate anchor instruments in this round measured in-page anchors and path-existence only, and all four were blind to it.
2. **N2, the two miscounted figures**, corrected in the table above. No re-work is requested — the substance is fixed at both sites. The mechanism is worth carrying: **a sweep token that survives its own fix reports the population as un-fixed, and a delta measured against one of a pass's two edits is not a measurement.** Grep the *defective* spelling, not a fragment shared by the defective and corrected spellings.
3. **The prior Worker 3 section's `## Non-goals` mis-naming stands in the record**, corrected in H1 above rather than by rewriting that section. A fresh reader of this artifact should take `## Goals` item 3 as the site.
4. **Not re-opened:** the reconciliation's accepted substance, the build plan's `### Verified NOT a finding` list, the two maintainer-escalated reference clusters, and every alternative the rationale records as rejected. F13 and F14 are R2's and are not graded here; the (a)-decision handoff to R2 is checked above and needs nothing further from R1.

### Review outcome

`review-accepted`.

All seven dispatched findings — H1, M1, M2, M3, M4, M5/D1 and D2 — plus L1 and L2 are closed, each verified against source or re-derived mechanically rather than accepted from the report. No High and no Medium finding remains. Two new Low items are recorded: **N1** is pre-existing at HEAD and outside the dispatched population, escalated to final verification with its resolution paths; **N2** is an artifact-only count defect, corrected in place in the table above, with no re-work requested. Under `docs/builder/worker-3.md` `### Acceptance gate` — every dispatched finding addressed or rejected with a recorded reason, no boundary owed a failability proof, no hot-path number owed, no floor scope, public-surface check clean, both gates green — this is an accept. `Status:` set to `review-accepted`; final verification is a fresh Worker 1's.

**Dispatched-findings checklist audit — all 14 boxes, re-audited after pass 2.** The three ticks the prior pass marked *partially* confirmed are now fully confirmed: **F1** (seven of seven sites — the seventh was H1), **F3** (guard position now correct — M1), **F4** (spelling enumeration open at all six sites and Slice 1's fragment deleted — M2, M3). The other eleven were confirmed in pass 1 and nothing in pass 2 contradicts them; re-spot-checked F2's error-message accuracy, F9's import graph, F10's seven cards and F12's test names, all still true. **No box is a phantom tick, and there are no unrecorded deferrals.**

---

## Final verification (Worker 1)

Performed by a fresh Worker 1 subagent with no memory of the reconciliation pass or the fix pass, after Worker 3's pass-2 re-review. Every claim below was re-derived against the files and against source; the four prior sections were read but not accepted as evidence.

**Status set: `final-accepted`.**

### Round-scope declarations — each recorded with its reason rather than left blank

- **Failability proofs: none owed.** The round introduces no boundary, guard, gate, or rejection path — its whole diff is two Markdown files (`docs/builder/BUILD.md` `### What needs a proof, and what does not`). Confirmed by reading the diff rather than by accepting the plan's `### Boundary count` of zero. Nothing to confirm-the-record-exists for, so `worker-1.md` `### Failability and fail-open checks` has an empty population, legally. **No fail-open shape landed** — there is no executable line in the round to carry one.
- **Hot-path budget: not applicable.** The plan declares hot-path scope `none`; nothing in the round runs per request / per resolver / per row / per connection.
- **Floor verification: not applicable.** The plan declares scope `none`; no Django / Strawberry / channels integration seam is touched. Where the reconciled prose reasons about later behavior it names cards (`spec-034`, `spec-045`, `spec-047`), not version floors.
- **`scripts/review_inspect.py`: skipped.** No `.py` file is added or modified by the round, so no trigger in `docs/builder/BUILD.md` `### When to run the helper during build` fires.
- **Relocation / promotion claims: none in this round.** No body was moved into a seam, no helper promoted, nothing claimed byte-identical — so `worker-1.md` `### Verifying relocation / promotion claims` has no claim to re-prove. The one *test* promotion the round documents (F7) is a fact about the shipped tree from a prior card, not a claim this round's diff makes; both live tests were verified to exist by name.
- **The full `## Final test-run gate` is not this pass's.** It belongs to `docs/builder/bld-020-final.md` after Round 2 and the integration pass. No `uv run pytest` sweep was run here, and no focused test run was owed: the round's diff contains nothing executable, so `## Final verification job` step 5 has an empty scope.
- **Staged-anchor sweep: not owed here** and already discharged in the build plan (`grep -rEn 'TODO\(spec-020|TODO-(ALPHA|BETA|STABLE)-020'` returns only two legitimate prose mentions in a sibling spec's rationale). Re-confirmed that neither file this round writes introduces a `TODO(`.

### Dispatched findings checklist audit — all 14 boxes, audited against the files

Boxes **un-ticked: none.** Boxes **ticked that were left open: none** (all 14 were already `- [x]`). Boxes **still `- [ ]`: none**, so no deferral reason is owed. Each tick was confirmed by reading the spec, not by reading the report.

| Box | Confirmed at | Verdict |
|---|---|---|
| F1 | `grep -c '_apply_get_queryset'` on the spec = **0**; `types/relay.py` occurrences = **2**, both the `in_async_context` import-site citations, verified correct at `django_strawberry_framework/types/relay.py #"from strawberry.utils.inspect import in_async_context"` | holds |
| F2 | `### Decision 5` guard 3 states `definition.origin is arg` and that `hasattr(...)` is **NOT** a sufficient discriminator, with the MRO reason and `tests/test_list_field.py::test_djangolistfield_rejects_djangotype_subclass_without_own_meta`. All four quoted error messages are character-accurate against `django_strawberry_framework/list_field.py::_validate_djangotype_target`'s bodies | holds |
| F3 | signature carries `max_rows=None, trusted_max_rows=False`; two error sites named; `### Row bound` exists; the guard's position is stated as **first**, matching source (`validate_collection_bound` then `_validate_djangotype_target`). `grep -c 'fifth check'` = **0** | holds |
| F4 | `DOES NOT WORK` / `silently skipped` = **0**; `all three async spellings` = **0**; the entry is a positive statement naming the raw `staticmethod` descriptor and arbitrary nestings, deferring to `django_strawberry_framework/utils/typing.py::is_async_callable`, which is what `::_callable_inspection_target`'s `while isinstance(target, (functools.partial, staticmethod))` loop actually does | holds |
| F5 | `### Decision 2`'s three-arm paragraph matches the source dispatch order (`is_async_generator_callable` first, then `is_async_callable`, then the sync arm's `isinstance(source, AsyncIterable) and not isinstance(source, Iterable)` check), and the `SyncMisuseError` rejection is sourced to `::_require_async_iterable_context`, whose body is `if not in_async_context(): raise SyncMisuseError(...)` | holds |
| F6 | `### Decision 8`'s boundary line carries both halves plus the reason; `## User-facing API` carries the **No order guarantee** bullet. Both match `list_field.py::DjangoListField`'s docstring ordering paragraph | holds |
| F7 | no `18 tests` / `14 behavior tests` count survives; `grep -c '^- \[x\]'` on the spec = **0**, so the file is uniformly unticked and the `Status:` line is the only completion signal; both promoted live tests are named with their file and both exist on disk | holds |
| F8 | all three shipped fields named in Slice 4 and `### Decision 9`; `other seven` / `eight existing` = **0** | holds |
| F9 | `### Decision 1`'s shared-home paragraph is written to the **verified** import graph: `connection.py:71` and `relay.py:65` both import `_validate_relay_djangotype_target` only, and reach the four base guards through its delegation | holds |
| F10 | seven cards enumerated by id, matching `KANBAN.md #"\`0.0.7\` shipped 2026-05-27 with seven cards"` id-for-id | holds |
| F11 | `_OriginAndModel \| None` and `normalize_query_source` both cited; confirmed at `optimizer/extension.py::_resolve_model_from_return_type` (returns `_OriginAndModel \| None`) and `::DjangoOptimizerExtension._optimize #"result, is_queryset = normalize_query_source(result)"` | holds |
| F12 | `### Decision 3`'s sealed-boundary paragraph names five unprovable-return shapes and cites five pinning tests including the real `::test_djangolistfield_resolver_manager_alias_drift_fails_closed_sync`; the cascade non-goal cites `::test_list_field_default_resolver_applies_cascade` | holds |
| Extra 1 | `slice-5--promotion` = **0**; both uses are `#slice-checklist`, which resolves | holds |
| Extra 2 | `spec-011]` / `spec-014]` = **0**; `[spec-015]` / `[spec-018]` resolve to the right files from `docs/SPECS/` | holds |

**Builder amendment lists discharged** (`worker-1.md` `## Review-round custody`): R1 had no builder, so the only on-disk `### Notes for Worker 1 (spec reconciliation)` entries are Worker 3's and the custodian's own. All are discharged — N1 fixed below, N2 adjudicated below, the `## Non-goals`-vs-`## Goals` mis-naming left standing in the record with `## Goals` item 3 as the site of record, and nothing in the "not re-opened" list re-opened.

### The round's central claim, checked independently: the spec states only what is true at HEAD

Spot-checked against source rather than against the reports. `django_strawberry_framework/list_field.py::DjangoListField` — signature, docstring ordering contract, the `max_rows`-guard-before-target-guards order, all three consumer arms, bound-applied-last in all four return paths. `::_validate_djangotype_target` — four guards in the documented order, the `definition is None or getattr(definition, "origin", None) is not target_type` invariant, all four message bodies. `utils/querysets.py::apply_type_visibility_sync` (calls `::reject_async_in_sync_context`, which disposes the awaitable then raises `SyncMisuseError`), `::SyncMisuseError` (`class SyncMisuseError(ConfigurationError, RuntimeError)`), `::apply_type_visibility_async`. `resource_policy.py::bounded_rows` (bound applied as `result[:limit]`, i.e. by slicing, unconditional). `utils/typing.py::is_async_callable` and `::_callable_inspection_target` (peels `functools.partial` **and** `staticmethod`; the docstring names the raw-descriptor case). Decision 2's sketch was read line-by-line against the module: imports, signature, both default branches, all three wrapper arms and the `strawberry.field(...)` return are faithful, and the post-sketch paragraph correctly marks `_bounded_async`, `_require_async_iterable_context` and `_validate_djangotype_target` as module-local.

**No statement in either file is false at HEAD.** No new false claim was introduced by the reconciliation, and the two highest-value inversions (the deleted `functools.partial` DOES-NOT-WORK block, and Decision 3's sealed-boundary contract replacing "call the hook and use what comes back") are both accurate.

**Every cited test name exists.** Re-derived mechanically: all `test_*` tokens in both files were matched against every `def test_*` in the repo. Spec: 44 distinct tokens, **6 non-matches, all path fragments** (`tests/base/test_init.py`, `tests/test_list_field.py`, `tests/test_registry.py`, `tests/test_scalars.py`, `examples/fakeshop/test_query/`, `examples/fakeshop/test_query/test_library_api.py`) — every one verified present on disk, and **every test-function name resolves**. Rationale: 24 distinct tokens, 4 path fragments plus **5 names that do not exist on disk** — `test_djangolistfield_rejects_non_bool_nullable_list`, `..._nullable_list_toggle_renders_nullable_outer`, `..._consumer_resolver_override_bypasses_default` and the two promoted ones. Each was read in context and each is correctly framed as authoring-round history (rev2 H1/H2 dropped the first three) or as retired-and-promoted, which is a rationale's job. Not findings. Worker 3's pass-2 figure of "3 non-matches" in the spec is an undercount of the path-fragment class only; no cited test name was wrong in either file.

### N1 — disposition: FIXED, resolution path (i)

`docs/SPECS/spec-020-list_field-0_0_7.md` `## Current state` #"is silently bypassed unless the consumer remembers" linked `../../TODAY.md#optional-fakeshop-visibility-filtering-today`. Confirmed live and dangling: the def is used at exactly that bullet, and `TODAY.md` has no heading slugging to that anchor. The heading carrying that content today is `## Visibility filtering via \`get_queryset\`` — read in full, and it is the same content the bullet cites (the `get_queryset` classmethod boilerplate a consumer writes by hand). So the link was re-pointed rather than dropped:

- def `[today-optional-fakeshop-visibility-filtering-today]: ../../TODAY.md#optional-fakeshop-visibility-filtering-today` -> `[today-visibility-filtering-via-get_queryset]: ../../TODAY.md#visibility-filtering-via-get_queryset`, ref-id renamed with it so the id does not contradict its target (the same defect extra-defect 2 was dispatched for), and the `<!-- Root -->` group left alphabetical;
- link text `[\`Optional fakeshop visibility filtering today\`]` -> `[\`Visibility filtering via get_queryset\`]`, so the prose names a heading that exists.

De-linking was rejected: the cited section still exists under a new name and still lays out exactly the boilerplate the bullet is about, so dropping the link would lose a live pointer to answer a naming change.

**The instrument lesson, recorded in the rationale as well** (`### \`## Problem statement\` and \`## Current state\``, keyed to the section that carried the link): four separate anchor instruments ran over these two files this round — the reconciliation's postcondition step 8, both Worker 3 sweeps, and the fix pass's gate table — and every one measured in-page anchors plus def-path-existence-on-disk. **None resolved a cross-file def's `#fragment` against the target file's headings**, so a whole defect class was invisible to all four. A path that exists is not a link that resolves. The sweep below closes it, and the rationale carries the lesson durably.

### N2 — disposition: both count corrections confirmed; substance fixed, record now accurate

Re-derived independently, occurrences not matching lines, after the last edit:

- **`iscoroutinefunction`: 5 occurrences across 3 lines.** Worker 3's correction is right and the fix pass's "5 before, 4 after" is the defect. All five were read individually and all five are legitimately contrastive — Slice 1's superset-of statement, Decision 2's explicit "deliberately **not** `inspect.iscoroutinefunction`" negation, and three negative occurrences in the `functools.partial` edge case. **None asserts the field uses the predicate.** The M3 residue (the `Same \`iscoroutinefunction\`/coroutine handling` fragment) returns **0**. No residue, no re-work.
- **`aware superset`: 2 occurrences.** Worker 3 is right that the token survives its own fix: the corrected wording is `wrapper-aware superset` (**2**), and the defective closed abbreviation `` `__call__`/`functools.partial`-aware superset `` returns **0**. Substance fixed; the fix pass's "2 -> 0" was false in the one direction a later re-runner cannot detect.

Both are artifact-only stated-count defects of exactly the shape `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` warns about, both already corrected in Worker 3's table, and neither changes a verdict. **The record is now accurate and no re-work is owed.** Carrying the mechanism forward: grep the *defective* spelling, never a fragment shared by the defective and the corrected spellings, and measure after the pass's last edit rather than after the edit you were thinking about.

### What Round 2 inherits — both notes present, actionable, and mutually consistent

- **No glossary trim (judgement call (a)).** Present under the pass-2 `### Notes for Worker 1 (spec reconciliation)`. The premise was re-verified, because a pointer can silently defer to a target that does not carry what was deferred: `docs/GLOSSARY.md` `## \`DjangoListField\`` -> **Row bound** does state that the request's execution resource policy supplies `max_list_rows` whether or not the field says anything, that `max_rows=` narrows further, and that there is no unbounded spelling. **(a) leaves no clause homeless.** The spec keeps the field-facing surface; the generated glossary keeps the policy contract. Correct for an archived `0.0.7` spec that only inherits a `0.0.14` contract.
- **The F14 glossary amendment.** Present and actionable: it names the stale wording ("rejects an async `get_queryset` with `ConfigurationError`, mirroring the Relay defaults"), the replacement (`SyncMisuseError`), why it is loose rather than false, and the DB-backed mechanism (edit `GlossaryTerm.body` in the fakeshop glossary app and regenerate — never a hand edit).
- The two target different paragraphs of the same entry, so R2 can execute both without either undoing the other. **Execution is Round 2's; nothing is pre-empted here.** F13 and F14 were not graded in this round.

### Gates

| Gate | Result |
|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-020-list_field-0_0_7.md` | **exit 0** — `OK: 24 terms - all have glossary entries and at least one spec link.` Re-run after the N1 edit specifically, because renaming a ref-id can strip a term's last link |
| `uv run python scripts/check_trailing_commas.py --check` on both spec-side files, this artifact and `docs/builder/worker-memory/worker-1.md` | **exit 0** |
| Repo-wide `check_trailing_commas.py --check` | not run as a gate; the plan's recorded baseline exception (an untracked, gitignored `.claude/` agent-memory file) makes it exit 1 at baseline. Not repository content, not this cycle's, not touched |

**Link and anchor sweep, re-derived for both files with cross-file `#fragment` resolution added.** The slugger was hand-validated before use against a heading confirmed by reading: `### \`## Definition of done\`` slugs to `-definition-of-done` with a **leading hyphen** (lower -> trim -> strip punctuation -> space-to-hyphen, with no second trim), and the anchor actually used in the rationale is `](#-definition-of-done)`; `### [Decision 10 — Joint \`0.0.7\` cut][spec-020-d10]` reduces to its link text and slugs to `decision-10--joint-007-cut`. A trimming slugger would have reported live anchors as dangling.

| Measure | Spec | Rationale |
|---|---|---|
| dangling in-page anchors | **0** (35 headings, 54 in-page uses) | **0** (29 headings, 10 in-page uses) |
| dangling **cross-file** `#fragment`s | **0** (was 1 — N1, now fixed) | **0** |
| undefined ref-ids | **0** (40 defs, 40 used) | **0** (14 defs, 14 used) |
| unused link defs | **0** | **0** |
| non-existent def paths on disk | **0** | **0** |

`AGENTS.md` rule 27 re-derived on both files: **0** single-colon `path:Symbol` forms and **0** raw `path:NN`. All 10 canonical group headers present and in the prescribed order in both files.

### Spec changes made (Worker 1 only)

| File / section | Change | Why | Finding |
|---|---|---|---|
| Spec `## Current state`, the `get_queryset`-boilerplate bullet, and the `<!-- Root -->` link-definition group | `[today-optional-fakeshop-visibility-filtering-today]: ../../TODAY.md#optional-fakeshop-visibility-filtering-today` -> `[today-visibility-filtering-via-get_queryset]: ../../TODAY.md#visibility-filtering-via-get_queryset`; link text re-pointed to the heading that exists | the anchor named a heading `TODAY.md`'s rewrite deleted, so the one cross-file link in the file resolved to nothing | N1 |
| Rationale `### \`## Problem statement\` and \`## Current state\`` | the N1 change record with its rejected alternative (de-linking), plus the cross-file-fragment instrument lesson | every spec change is recorded under the entry for the section it governs; the lesson outlives the artifact and the artifact does not | N1 |

**No deferrals.** Every dispatched box landed; the one escalated item (N1) is fixed rather than deferred; N2 needed no re-work.

### Byte counts

| File | Before this pass | After |
|---|---|---|
| `docs/SPECS/spec-020-list_field-0_0_7.md` | 100,594 | 100,566 |
| `docs/SPECS/appx/spec-020-list_field-0_0_7-rationale.md` | 108,525 | 109,687 |

The spec shed 28 bytes (the shorter link text and ref-id); the rationale gained 1,162 for the N1 record and the instrument lesson (measured with `wc -c`; a Python `len(str)` is characters, not bytes), which is where explanation belongs.

### Defects found in the four prior sections

Each is a record defect, none changes a verdict, and none is re-worked.

1. **Worker 3 pass 2's "3 non-matches are path fragments"** understates its own class: the spec carries **6** path-fragment tokens (it omits `tests/test_registry.py`, `tests/test_scalars.py` and `examples/fakeshop/test_query/`). The load-bearing half of the claim — every cited *test function* resolves to a `def` — is true, re-derived here.
2. **The pass-1 `## Final verification (Worker 1)` placeholder** sat above the reconciliation build report's own subsections, so `### Spec changes made (Worker 1 only)` and `### Notes for Worker 1 (spec reconciliation)` read as belonging to a final-verification pass that had not happened. A forward pointer was added to the placeholder; the subsections themselves are untouched.
3. **The prior Worker 3 section's `## Non-goals` mis-naming** stands in the record as both later passes decided. `## Goals` item 3 is the site; a fresh reader should take the H1 correction in Worker 3's pass-2 section as authoritative.

Already-known and correctly left alone: the two maintainer-escalated reference clusters (`CHANGELOG.md`'s pre-renumber `0.0.7` card labels, `KANBAN.md`'s `apps.py` mis-attribution on `DONE-020-0.0.7`) are `bld-020-final.md`'s `### Deferred work catalog` material, not this round's; the pre-existing strict-ASCII def-ordering notes in both files are not R1 findings; the build plan's `### Verified NOT a finding` list was not re-opened.

### Round disposition

`Status: final-accepted`. The round's central claim holds: the spec states only what is true at HEAD, the rationale carries the deliberation keyed by heading and anchor, all 14 dispatched boxes landed, no false claim was introduced, and the one escalated defect plus the defect class it exposed are both closed. Round 1 is complete; Round 2 (`docs/builder/bld-review-2-docs_completion.md`) is Worker 0's to dispatch.
