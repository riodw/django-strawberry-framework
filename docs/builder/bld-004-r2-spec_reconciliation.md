# Build: R2 — Reconcile the spec with HEAD (spec-004)

Spec reference: `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` (whole file; this pass rewrote lines 9, 13, 15, 19-39, 47-65, 69-83, 89-107, 115-121, 127-141, 147-153, 159-169, 187-189, 194 of the post-R1 file)
Rationale file (owned, appended): `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md`
Status: final-accepted

**Shape note.** Per `docs/builder/build-004-optimizer_beyond-0_0_3.md` `### Deviation 2`, R2 has no Worker 2 pass: `BUILD.md` `## Spec reconciliation` and `worker-1.md` `## Scope` make Worker 1 the only role that may mutate the spec, and R2's entire deliverable is spec edits. So the `## Build report (Worker 2)` section of `docs/builder/ARTIFACT.md` is not applicable and the performance record lives under `## Reconciliation report (Worker 1)` below, carrying the fields Worker 3 would otherwise read from a build report. `Status:` is `planned` on return, which Worker 0 reads as "dispatch Worker 3" for this item.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable, and deliberately so. `worker-1.md` `### Package-wide helper inventory before helper planning` gates *helper-like logic*; R2 changes no package source and adds no helper, shared constant, validation branch, coercion utility, or test helper. The build plan's `## Build-wide context flags` declares package source, `tests/`, and `examples/` read-only for the whole cycle. No inventory was refreshed and none was needed.
- **Existing patterns reused.** The reconciled voice is taken from the immediate precedent rather than invented: `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` went through this same residual R2 the day before, and its `## Plan shape` paragraph #"Those belong to" is the exact shape this pass needed eleven times over — state the behaviour that holds in one clause, name the owning spec by path in a code span, restate none of its rules. Its sibling-spec citations are **code-span paths, not reference-style links** (`docs/SPECS/spec-033-connection_optimizer-0_0_9.md`), which is also what spec-004's own surviving `## Problem statement` and `## Non-goals` already do; following it kept the link-definition block at its existing 11 entries and left `check_trailing_commas` untouched. The rationale's new section follows the entry shape R1 established in the same file (`Spec:` line with a resolving anchor, italic *Changed* / *Alternative rejected* leads, a closing claims block).
- **New helpers justified.** None; no code was written.
- **Duplication risk avoided.** Three live risks, each handled by a decided rule rather than by judgement per sentence:
  - **Against `spec-033` / `spec-035` / `spec-029` / `spec-032` / `spec-018` / `spec-023` / `spec-047` / `spec-016` / `spec-003`.** The build plan's `**The scope trap specific to this spec.**` names rows D4, D7, D11, D14, D18, D25, D26 as where the pull is strongest. The rule applied to every one: **one clause of behaviour plus the owning spec's path, and no rule of theirs reproduced.** Nine sibling specs are now named in the spec; not one of their contracts is restated. Measured after the last edit, counting occurrences of the token `docs/SPECS/spec-0NN` rather than matching lines (`grep -o 'docs/SPECS/spec-0[0-9][0-9]' <spec> | sort | uniq -c`): **21 occurrences across 9 distinct siblings** — spec-035 ×6, spec-033 ×5, spec-002 ×2, spec-003 ×2, spec-018 ×2, and spec-023 / spec-029 / spec-032 / spec-047 ×1 each — and every one sits inside a sentence stating what spec-004's own surface does. Two of the twenty-one (`spec-002`, `spec-003` in `## Current state`) name the foundation rather than an extension.
  - **Against the rationale.** The spec states the contract; the rationale states why it now reads that way. No `*Changed —*` explanation appears in the spec and no normative rule was moved out of the spec into the rationale by this pass.
  - **Against the spec's own sections.** Two claims were at risk of being said twice: the "static queries collapse to one cache entry" sentence lived in both `**Directive-variable extraction.**` and `**Cache invalidation.**` (the duplicate in `**Cache invalidation.**` was dropped, the surviving one corrected to the five-component key), and the plan-immutability requirement is stated once in B1 and once in B8 — deliberately, because each states a different half (B1 that no invalidation is needed, B8 that the reconciliation must not mutate) and both name the same owning spec for the enforcement.

### Implementation steps

Line numbers are pin-at-write-time, against the **post-R1** spec (216 lines) unless stated.

1. `## Problem statement` — retense the second paragraph's schedulability claim; leave the maintainer-ruled first paragraph byte-identical (spec:9). Done.
2. `## Current state` — restate the mid-build snapshot as the standing foundation relationship, preserving both glossary links (spec:13). Done.
3. Rename `## Proposed improvements` to `## The eight improvements` (spec:15), then re-point the rationale's `[spec-004-improvements]` definition and its nine link texts. Done.
4. `### B1` — rewrite `**Mechanism.**` to the five-component key with the printed-AST reason; add the deferred-conversion thunk; extend `**Directive-variable extraction.**` with the second variable family and the over-collection rule; restate `**Cache storage.**` with the bound, the batch eviction and the singleton-factory pointer; restate `**Cache invalidation.**` with structural immutability and the three further memos; restate `cache_info()` in `**Test surface.**` (spec:19-39). Done.
5. `### B2` — correct the dispatch site; add the projection gate and the ordering invariant; add the composite-PK exclusion; add the router-set stub alias, the identity fan-out, and the loud unsafe-elision fallback; replace "clean fallback" (spec:47-59); drop the "Can be spec'd now" staging clause (spec:65). Done.
6. `### B3` — correct what the report names; state the depth bound; add the third probe and the force-unplanned override; restate `**Strictness API.**` against the shipped constructor; retense the resolver-signature prerequisite (spec:69-83). Done.
7. `### B4` — add the fifth hint member with a pointer, not a transplant; restate `OptimizerHint`'s shape and drop the "when B4 ships" clause; rewrite `**Walker needs registry lookup.**` off the retired mirror; rewrite `**Validation.**` onto `_validate_optimizer_hints` with the excluded/scalar gate and the flag-combination rejection (spec:89-107). Done.
8. `### B5` — restate the stash dispatch and the skip-on-frozen rule; add the shared-utility pointer, the per-execution reset, and the union rule; correct the dict-context test row (spec:115-121). Done.
9. `### B6` — `classmethod` → static method; collapse the three per-field checks to the one that ships; correct what the warning carries; add the union/interface descent and the `(model, field)` dedupe; drop the `check_optimizer` follow-up sentence; restate `iter_types()`. Re-site `metafields` / `metaexclude` inside the rewritten exposed-fields sentence (spec:127-141). Done.
10. `### B7` — move the map's home off `cls._optimizer_field_map` onto the definition's `field_map` in `**Mechanism.**`, `**Walker needs registry lookup.**` and `**Test surface.**`; state `FieldMeta`'s real shape; state the dual contract (spec:147-153). Done.
11. `### B8` — retense the opening paragraph off the package's pre-B8 behaviour; restate the reconciliation as a `(plan, queryset)` pair with the upgrade and prune steps; restate cache-safety as enforced rather than instructed (spec:159-169). Done.
12. `## References` — repoint the dangling graphql-core clause at the deferred conversion; correct the Django clause from B1 to B8 (spec:187-189). Done.
13. `## Implementation checklist` — trim the spike bullet's sequencing parenthetical (spec:194). Done.
14. Rationale — append `## The reconciliation pass — what the spec now states`, one entry per reconciled section, each carrying the changes, the alternatives rejected, and a factual claims block; add the discharge pointer to `## Standing notes`; fix the "locked `0.316.0`" phrasing; add four link definitions. Done.

### Test additions / updates

Not applicable; this cycle changes no code.

### Implementation discretion items

None reserved. R2 has no downstream builder, so nothing is delegable. Every per-row disposition below is decided, not deferred to another pass.

### Dispatched findings checklist

Spec-004 has no `## Slice checklist` and this is not a review round, so per `worker-1.md` planning step 8 and `BUILD.md` `### Dispatched findings checklist` the boxes below stand in that position: one per drift row `D1`-`D28`, one per open handoff item from `docs/builder/bld-004-r1-rationale_move.md` `## Review (Worker 3, pass 7)` `### Notes for Worker 1 (spec reconciliation)`, and one per finding this pass's own sweep added beyond the table (the table is Worker 0's verified floor, not an exhaustive list). Worker 1 both performs and ticks here because Deviation 2 removes the Worker 2 pass; the ticks are audited at Worker 1's own final verification after Worker 3.

**A box is ticked when the row is DISCHARGED — which includes a decided "no spec edit".** Every such row's disposition is recorded in `### Row-by-row disposition` with its reason.

- [x] D1 — the document proposes work it records as complete
- [x] D2 — `## Current state` is a mid-build snapshot
- [x] D3 — the cache key is a 3-tuple over a document hash
- [x] D4 — directive variables are the only collected family
- [x] D5 — the extension-lifecycle statement, deleted at R1 and not replaced
- [x] D6 — "simple bounded-size dict": the bound, the storage, the batch size
- [x] D7 — plan immutability, and the three further cache tiers
- [x] D8 — `cache_info()` "mirrors `lru_cache.cache_info()`"
- [x] D9 — the FK-column append: shared, ordered, gated
- [x] D10 — the fifth applicability exclusion (composite PK)
- [x] D11 — the stub's router alias and the unsafe-elision sentinel
- [x] D12 — B3's pseudo-code (cut at R1); prose re-verified
- [x] D13 — path construction (a) shipped, (b) never needed
- [x] D14 — the lazy-load probe's third arm and `force_unplanned`
- [x] D15 — the fifth `OptimizerHint` member
- [x] D16 — the retired `_optimizer_hints` class-attribute mirror
- [x] D17 — `**Validation.**` attributes its rejections to the wrong symbol
- [x] D18 — one context key became a family
- [x] D19 — `check_schema` iterates the definition field map and dedupes
- [x] D20 — `_collect_reachable_types` and the union / interface descent
- [x] D21 — the `check_optimizer` management command
- [x] D22 — `cls._optimizer_field_map` in the present tense at every site
- [x] D23 — the `_meta` fallback is a documented dual contract
- [x] D24 — B7 / B8 orphaned below the ordering section
- [x] D25 — "B8 last because queryset diffing is a pure polish item"
- [x] D26 — the diff returns a plan; cache-safety as an instruction
- [x] D27 — `## References`' dangling "skip Strawberry conversion" clause
- [x] D28 — `## Priority and ordering`'s mixed tense
- [x] H1 — decide the extension-lifecycle disposition: pointer, not transplant
- [x] H2 — verify D24 is discharged rather than performing it
- [x] H3 — `check_schema` "classmethod" is a one-word correction
- [x] H4 — the `## Implementation checklist` spike parenthetical
- [x] H5 — `## References`' third paragraph still dangling
- [x] H6 — do not "restore" B7's deleted `_meta.get_fields()` claim
- [x] H7 — D25 and D28 are discharged; do not hunt them
- [x] H8 — D6 is exactly three things: bound, storage, batch size
- [x] H9 — the maintainer decision is settled; the `:7` sentence stays byte-for-byte
- [x] H11 — the six `_optimizer_field_map` occurrences across five sites, and their two riders
- [x] H12 — `### B8`'s opening paragraph, which no drift row covers
- [x] H13 — re-run the link-target disk check rather than quoting R1's
- [x] H14 — re-derive the baseline tree state rather than inheriting it
- [x] H15 — state the unit beside every count and re-measure after the last edit
- [x] H17 — the "locked `0.316.0`" phrasing in the rationale
- [x] H18 — do not "fix" the candidates prior passes opened and left
- [x] H19 — do not harmonize the modal block label back to the sibling form
- [x] H20 — do not level the two-spelling per-slice pointer asymmetry
- [x] S1 — `**Strictness API.**` types the parameter `Literal[...]`; HEAD takes a validated `str`
- [x] S2 — B5's stash order: a `dict` goes through the mapping path, not `setattr` first
- [x] S3 — B1's `weakref`-callback / module-level-cache parenthetical describes nothing that exists
- [x] S4 — B3's warning "names the field, the parent type, and the query path"
- [x] S5 — B6's second per-field check (custom-resolver detection) was never built
- [x] S6 — B6's warnings carry "the field path and a suggested fix"
- [x] S7 — `## References` credits the Django `select_related` merge to B1's cache, not B8's diff
- [x] S8 — B7 lists `FieldMeta` as "a lightweight namedtuple or dataclass" with six attributes

---

## Reconciliation report (Worker 1)

### Files touched

- `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` — the reconciliation. Working-tree diff against HEAD is now **73 insertions / 196 deletions** (`git diff --stat`), of which R1 contributed 28 / 171.
- `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` — one new top-level section (`## The reconciliation pass — what the spec now states`, 13 `###` entries), one discharge pointer added to `## Standing notes`, one phrasing correction (H17), nine link texts and one anchor definition re-pointed by the heading rename, four link definitions added.
- `docs/builder/bld-004-r2-spec_reconciliation.md` — this artifact (new).
- `docs/builder/worker-memory/worker-1.md` — memory entry (gitignored).

Nothing else was written. No package source, test, example, sibling spec, terms CSV, `CHANGELOG.md`, `KANBAN*`, `docs/GLOSSARY.md`, `docs/TREE.md`, or DB file was touched.

### Byte and line counts (measured as written, after the last edit)

| | lines | bytes |
|---|---|---|
| spec at HEAD (pre-R1 blob) | 359 | 33,928 |
| spec **before R2** (post-R1) | 216 | 26,436 |
| spec **after R2** | 236 | 35,834 |
| R2 delta | +20 | **+9,398** |
| rationale **before R2** | 819 | 58,828 |
| rationale **after R2** | 1,197 | 84,365 |
| R2 delta | +378 | **+25,537** |

Method: `wc -l -c` on the working files; the HEAD row from `git show HEAD:<path>` into a scratch path **outside** the repo, per `BUILD.md` `## Claims are proven mechanically` (no `git stash`, no `git checkout`). The pre-R2 figures re-derive R1's final-verification report to the byte.

**The reconciled spec is 1,906 bytes larger than the pre-R1 spec, and that is the expected direction.** R1 removed 7,492 bytes of deliberation; R2 added 9,398 bytes of contract — five cache-key components where there was one tuple, a validation paragraph that states four rejections where the old one stated two, a B8 mechanism that describes a two-sided return and two companion steps. A reconciliation that only ever shrank a spec would be deleting contract rather than correcting it.

### Row-by-row disposition

Every row and handoff item carries a disposition. **Re-verified at HEAD by this pass with the symbol-qualified paths given**, not accepted from the table.

| # | Verified at HEAD | Disposition |
|---|---|---|
| D1 | `## Implementation checklist` marks all eleven boxes `- [x]`; the section heading said "Proposed" | **Restated.** Heading renamed `## The eight improvements`; the schedulability half of the framing sentence retensed to the dependency structure that still holds |
| D2 | Both halves true, taken at different times | **Restated.** Now states the standing foundation relationship; both glossary links preserved in place |
| D3 | `extension.py::DjangoOptimizerExtension._build_cache_key` returns a 5-tuple; component 1 is `print_ast(operation)` + reachable fragment definitions | **Restated** as five bullets. The `target_model` argument kept verbatim; origin pointed at `spec-018`; the root path stated without an owner because the drift table's own attribution (`spec-030/033`) is ambiguous and a wrong citation is worse than none |
| D4 | `extension.py #"_collect_cache_var_families"`, `::_doc_cache_entry`, `::_hashable_variable_value` | **Restated** in one sentence naming the second family, plus the over-collection rule; the windows the values feed pointed at `spec-033` |
| D5 | `docs/README.md #"module-level singleton wrapped in a factory"`; `spec-029` `P1.1` + Decision 3 | **Pointed elsewhere.** One clause: instance-bound cache, therefore singleton-factory, `spec-029` Decision 3 owns it. The corrected recommendation itself is **not** transplanted — H1's instruction and the anti-absorption rule agree |
| D6 | `_MAX_PLAN_CACHE_SIZE = 256`; `OrderedDict`; `move_to_end` under `suppress(KeyError)`; `popitem(last=False)` × `max(1, 256 // 4)` | **Restated.** Exactly H8's three things (bound, ordered-dict storage, quarter batch). The concurrent-eviction `suppress` guard was **dropped to the rationale's existing audit note** — it is a lock-free trade, not a contract |
| D7 | `plans.py::OptimizationPlan.finalize` / `::_assert_under_construction`; `_execution_plan_cache`, `_cache_key_parts_cache` (both set in `::on_execute`), module-level `_doc_key_cache` | **Restated + pointed.** Immutability now stated as structural with `spec-035` named; the three memos named in one paragraph with the nested fallback pointed at `spec-033`. None of their rules restated |
| D8 | `extension.py::CacheInfo` (`hits` / `misses` / `size`); `::cache_info` docstring | **Restated.** The `lru_cache` mirror claim dropped; best-effort counters and the execution-memo exclusion stated |
| D9 | `walker.py::_record_relation_access`, `enable_only` threaded from `::_enable_only_for_operation`, `append_unique_many(plan.fk_id_elisions, ...)` | **Restated + pointed.** Gate pointed at `spec-035`, ordering invariant at `spec-003`. The identity-tuple container deliberately **not** named — the identity *rule* is the contract, the container is an internal shape |
| D10 | `field_meta.py::FieldMeta.from_django_field #"fk_id_elision_eligible=("` ends `and not has_composite_pk(related_model)` | **Restated.** One clause added to `**Applicability.**` |
| D11 | `resolvers.py::_build_fk_id_stub` sets `state.db = router.db_for_read(...)` and returns `_FK_ELISION_UNSAFE`; caller passes `force_unplanned=elision_unsafe` | **Restated + pointed** (`spec-023` for routing, `spec-035` for the loud fallback); "clean fallback" replaced |
| D12 | `resolvers.py::_check_n1` computes `resolver_key(parent_type, field_name, runtime_path_from_info(info))` | **Superseded — no edit owed for the fence** (R1 cut it). The row's own note that the prose is correct **re-verified and confirmed**. The *report shape* the prose got wrong is filed separately as S4 |
| D13 | `plans.py::runtime_path_from_info` → `::runtime_path_from_path`, bounded by `_MAX_PATH_DEPTH`; `_check_n1(..., planned=, precomputed_key=)` | **Partly restated, partly dropped to the rationale.** The depth bound is stated (it is this slice's own surface); the once-per-row key threading is `spec-035`'s optimization and stays in the rationale, where R1 already recorded it |
| D14 | `resolvers.py::_will_lazy_load_single` / `::_will_lazy_load_many`; `kind == "connection_to_attr"`; `force_unplanned` bypasses `key in planned` | **Restated in one paragraph + pointed** (`spec-033`, `spec-035`). Label corrected to "One further probe, and one override" — the second is not a probe |
| D15 | `hints.py::OptimizerHint.strategy`; `__post_init__` flag-combination rejection | **Restated as a bullet + pointed at `docs/README.md`.** No spec owns the strategy seam by name (`spec-046` is transport security; grep finds no `docs/SPECS/` owner), so the doc that documents it is what the spec cites |
| D16 | `walker.py::_resolve_optimizer_hints` reads `definition.optimizer_hints`; zero `cls._optimizer_hints` in the package | **Restated.** The retired mirror is gone from the sentence |
| D17 | `types/base.py::_validate_meta` (line 1073) and `::_validate_optimizer_hints` (1232), called one line apart from `__init_subclass__`; the gate rejects unknown, excluded, and scalar keys plus non-`OptimizerHint` values | **Restated.** Written from the corrected premise, not the retracted one; `configurationerror` link preserved in place |
| D18 | `_context.py` five `DST_OPTIMIZER_*` keys; `::clear_optimizer_context`; `utils/context.py::stash_on_context`; `extension.py::DjangoOptimizerExtension._stash_union` | **Restated + pointed.** The reset is stated as spec-004's own (no sibling owns it); the shared utility points at `spec-047`, the union rule at `spec-033`. The five key names are deliberately **not** enumerated |
| D19 | `check_schema` iterates `definition.field_map`, skips `hint_is_skip`, dedupes on `(_model, field_name)`; message is `f"{type_cls.__name__} ({_model.__name__}.{field_name}) has no registered target DjangoType"` | **Restated + pointed** (`spec-018` for the multi-type artifact). The prose-versus-pseudo-code contradiction the row names was already resolved by R1's fence cut |
| D20 | `extension.py::_collect_schema_reachable_types` descends object fields, union members, interface implementations | **Restated + pointed** (`spec-032`). The symbol name itself lived only in the cut fence, so only the reachability *claim* needed widening |
| D21 | `management/commands/` ships `export_schema` and `inspect_django_type` only | **Dropped from the spec, recorded in the rationale, and deferred.** A promise eleven versions old with no card is not a contract. Routed to the final gate's `### Deferred work catalog` |
| D22 | Zero occurrences of `_optimizer_field_map` in `django_strawberry_framework/`; canonical store is `types/definition.py::DjangoTypeDefinition.field_map`, built at `types/base.py #"field_map = {snake_case(f.name): FieldMeta.from_django_field(f) for f in fields}"` | **Restated at all six occurrences across five sites** — H11's worklist, not the table's four. `metafields` / `metaexclude` re-sited inside the rewritten B6 sentence; B4's same-sentence `_optimizer_hints` rider closed with D16 |
| D23 | `walker.py::_resolve_field_map #"ONLY reason the two coexist safely"` | **Restated.** The fallback claim H6 warns against restoring was **not** restored; what was added is the dual-contract shape. The retirement card is not named — a spec does not cite a board card |
| D24 | All eight `### B` headings now sit under one parent heading, in order | **Discharged by R1 — verified, not performed** (H2) |
| D25 | `plans.py::diff_plan_for_queryset`, `::prune_unsupportable_select_related`, `select_path_resolver_keys` / `prefetch_path_resolver_keys` | **Discharged by R1** for the sentence itself (it died with `## Priority and ordering`, H7). The *shipped behaviour* it mis-describes is restated in B8's mechanism |
| D26 | `diff_plan_for_queryset(plan, queryset) -> tuple[OptimizationPlan, Any]`; `::finalize` swaps lists to tuples; `::_assert_under_construction` | **Restated + pointed** (`spec-035` for the enforcement). The requirement stayed in the spec — a requirement whose enforcement lives elsewhere is still this document's |
| D27 | `extension.py::_get_or_build_plan #"zero-arg callable that produces it"`; `optimizer/selections.py` exists | **Restated at both ends.** The thunk is now stated in B1, which is what makes the `## References` clause point at something real |
| D28 | `## Priority and ordering` is gone | **Discharged by R1 — verified, not performed** (H7) |

**Handoff items.** H1, H3, H4, H5, H8, H11, H12, H17 are actioned as recorded in `### Implementation steps` and the table above. H2 and H7 are verifications, performed. H6, H18, H19, H20 are do-not-do instructions, honoured: B7's deleted `_meta.get_fields()` claim was not restored; not one candidate on H18's list was touched; R1's modal `**Claims the spec may no longer make.**` label is unchanged in every existing entry, with this pass's new blocks using a factual spelling scoped and explained in their own section preamble; and all seven per-slice pointer paragraphs are byte-identical to R1's — five "competitive argument", two "opening argument", B8 carrying none. H9 is settled and was not re-opened; the ruled sentence is **byte-identical to HEAD**, proved below. H13, H14, H15 are method obligations, discharged in `### Validation run`. H10, H16 were closed on arrival.

### The eight findings this pass added beyond the table

The drift table is Worker 0's verified floor and says so; R2 owns the full sweep. Eight claims not on it are false at HEAD, each verified with the path given:

- **S1** — `**Strictness API.**` typed the parameter `Literal["off", "warn", "raise"]` and called it "a single keyword". `extension.py::DjangoOptimizerExtension.__init__` takes `strictness: str = "off"` positionally and validates it with an explicit `ValueError` at construction. Restated as the three accepted levels plus the fail-at-construction rule; the annotation is not the contract.
- **S2** — B5 said `setattr` is tried first for every context. `utils/context.py::stash_on_context` dispatches `dict` (and `dict` subclasses) through the mapping path *first*, so a `QueryDict` or a `dict` subclass round-trips to the branch the reader uses; `setattr`-then-`__setitem__` is the non-dict path. Restated, with the skip-on-frozen rule the same docstring pins.
- **S3** — B1's `**Cache invalidation.**` offered "(or resets the module-level cache via `weakref` callback)". `grep -rn weakref django_strawberry_framework/` finds one hit, in `filters/sets.py`, unrelated; the cache was never module-level. Deleted, and recorded in the rationale's claims block.
- **S4** — B3 said the warning names "the field, the parent type, and the query path". `resolvers.py::_check_n1` emits `"Potential N+1 on %s%s"` / `OptimizerError(f"Unplanned N+1: {field_name}{suffix}")` — the field name and an optional caller-supplied reason. A test written from the sentence would pin a message that is not emitted. Restated, and the matching `**Test surface.**` row corrected.
- **S5** — B6's second per-field check ("the relation is not hidden behind a custom resolver that bypasses the optimizer") does not exist: `check_schema` warns on exactly one condition. The spec's own `**Test surface.**` called custom-resolver detection follow-up work, so the section contradicted itself. Dropped with D21.
- **S6** — B6's output was described as carrying "the field path and a suggested fix". The message carries the type name, the model name, and the field name, and no fix. Restated.
- **S7** — `## References` credited the Django `select_related` dict-merge / `_prefetch_related_lookups` dedup reading to "B1's cache correctness". It is B8's reconciliation that depends on it. Corrected.
- **S8** — B7 described `FieldMeta` as "a lightweight namedtuple or dataclass" with six named attributes. `field_meta.py::FieldMeta` is a `@dataclass(frozen=True, slots=True)` carrying eighteen. Restated as the optimizer-relevant core plus what the later relation work added, so the list reads as illustrative rather than exhaustive.

### The three claims this pass refused to make

Recorded because a decided non-edit is not silence:

- **The root-response-path cache-key component has no owner named in the spec.** The drift table cites "spec-030/033"; `spec-030` is the connection field and `spec-033` the connection optimizer, and I could not establish from source or `CHANGELOG.md` which added the component (the `0.0.8` entry lists it among fixes, before either shipped). A citation that might be wrong is worse than a bare true statement, so the component is stated and unattributed.
- **`OptimizerHint.strategy` is attributed to a doc, not a spec.** The table says "spec-033 / spec-046"; `spec-046` is `transport_security`, and no file under `docs/SPECS/` mentions `nested_connection_strategy` or the lateral backend. `docs/README.md` "Nested connection indexing" is the actual owner and is what the spec cites.
- **The `_record_relation_access`-before-elision ordering invariant is pointed at, not restated.** `spec-003` states both the rule and the cost of reversing it; spec-004 names that it exists, that spec-003 states it, and that nothing enforces it. Adding the automated guard is a source change and is out of scope by the build plan's own rule.

### Validation run

Every command re-run after the last edit (H15), never quoted from an earlier reading (H13).

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` → `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0**, character-identical to the pre-flight baseline. Run **four** times across the pass — after the B1 batch, after the B4 batch, after the B8/References batch, and after the last edit — per the prompt's mid-rewrite instruction.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-004-optimizer_beyond-0_0_3.md docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` → **exit 0** (both files; scaffold and all 10 canonical group headers intact in each).
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` **exit 0**, the baseline both R2 and R3 must not break. Read-only form only; the writing form was never invoked.
- **Anchor carriage.** Each of the ten anchors resolves to exactly **2** occurrences in the spec — one body link plus one definition — so all ten are still single-carrier and none was re-sited by re-adding narration or by touching the CSV. `djangooptimizerextension` survives in `### B1` `**Cache storage.**` and `queryset-diffing` on the `### B8` heading, both re-verified after this pass rewrote the sentence around the first. D5's target sentence, D22's sites, and D25's clause — the three the prompt named highest-risk — all landed with their links intact; `metafields` and `metaexclude` stayed together in the rewritten B6 exposed-fields sentence.
- **Link resolution, both files, re-derived on disk this pass** (never quoted from R1): spec **11/11** definitions resolve, rationale **23/23** resolve, every anchored target's heading confirmed present in the target file, **zero** undefined references and **zero** unused definitions in either file. The four definitions this pass added (`spec-004-checklist`, `spec-004-current-state`, `spec-004-references`, `spec-023`) are included in that count, as is the re-pointed `spec-004-improvements` anchor.
- **No inbound anchor breakage from the heading rename.** `grep -rn "spec-004-optimizer_beyond-0_0_3.md#" --include="*.md"` over the whole tree returns hits in **one** file only — this cycle's own rationale — all of which were re-pointed in the same pass.
- **`AGENTS.md` rule 27:** `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` returns **no match** in either file. All source references are `path::QualifiedName` or `path #"substring"`.
- **Zero fenced code blocks** in both files (`grep -c '^```'` → 0, 0).
- **The spec narrates no history.** `grep -nE 'formerly|no longer|as of review|amendment|retract|previously|used to '` over the spec returns **one** line: `:3`, R1's companion-pointer paragraph, which describes the *rationale file's contents* rather than the spec's own chronology, and which H18/H20 place off-limits.
- **The maintainer-ruled sentence is byte-identical to HEAD**, proved by extracting the HEAD blob read-only to a scratch path outside the repo and `diff`-ing the line: `md5` `a236d060acf135d69af06a01cf43646a` on both sides, `diff` empty. No `git stash`, `git checkout`, or `git restore` was used anywhere in this pass.
- No `pytest` run: `AGENTS.md` rule 15, and this cycle changes no code. No `--cov*` flag was used in any command.
- No `ruff` run: neither file is Python.

### Working-tree state — reported, not reverted (H14)

Re-derived at the start and end of this pass, not inherited. `git status --short` was the same four entries both times:

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
```

(plus this artifact once created). **The concurrent session's churn recorded under the build plan's `### Second`, `### Third`, and `### Fourth` growth entries has landed and cleared**: `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`, `CHANGELOG.md`, `examples/fakeshop/db.sqlite3`, `django_strawberry_framework/optimizer/predicates.py`, the spec-004 terms CSV, and every renumbered live spec are **clean**. `BACKLOG.md`, `TODAY.md`, and the stray root `db.sqlite3` are gone from the list too. R3 should re-derive rather than inherit this reading, but it means the `## Concurrent-writable tracked binary / generated files` premise is once again "clean at the start", for the first time since R1's first review.

`HEAD` is **`346d67312599c0536980969caa39085ab3885ae8`**, re-derived this pass and unchanged from R1's closing reading. It did not sweep this cycle's work: `git log -1 --format=%h -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` still returns **`20a9752f`** and the artifacts are still untracked — the standing hazard check done with `git log`, never `git status` alone. Nothing was reverted and no stray untracked file appeared.

### Notes for Worker 3

- **The rewrite's own hazard is over-absorption, and the cheapest audit of it is the citation count.** Twenty-one sibling-spec citations across nine specs, six of them spec-035's and five spec-033's; the test to apply to each is whether the sentence states spec-004's surface and points, or reproduces the sibling's rule. Rows D4, D7, D11, D14, D18, D25, D26 are the ones the build plan flagged; B1's `**Cache invalidation.**` second paragraph and B8's prune paragraph are the two I would challenge first if I had not written them.
- **Three dispositions are judgement calls, not mechanics**, and each is argued in `### Row-by-row disposition`: dropping B6's `check_optimizer` sentence (D21) rather than marking it deferred in-spec; stating the 256-entry bound and the quarter-batch eviction in a contract (D6); and renaming the section heading (D1), which cost nine link texts in the rationale.
- **The rationale's new section uses a factual claims-block label** where R1's entries use the modal one. That divergence is deliberate, scoped in the new section's own preamble, and is **not** the divergence H19 protects — H19's is spec-004's modal label against the three sibling rationales, and every existing block still carries it.
- Nothing in `### The three claims this pass refused to make` is a hedge for lack of effort; each names what I could not establish and why a wrong citation would be worse.

### Notes for Worker 1 (spec reconciliation)

Carried to R3 and to the final gate:

1. **Deferred, for the final gate's `### Deferred work catalog`:** the `check_optimizer` management command and custom-resolver detection (D21 / S5) — named as B6 follow-up work eleven versions ago, never built, no card. Dropped from the spec by this pass and recorded in the rationale.
2. **Deferred:** the `_record_relation_access`-before-elision ordering invariant still has no automated guard. Carried over unchanged from Worker 0's read-only audit; the spec now points at `spec-003` for the rule, which is the most a docs cycle can do.
3. **Deferred, sibling-spec staleness:** `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` calls `0.316.0` "the locked" Strawberry version; it is the declared floor and `uv.lock` resolves higher. This file's own phrasing was corrected (H17). Sibling specs are read-only in this cycle, so it is recorded, not fixed.
4. **Deferred:** three B7 test names in `tests/optimizer/test_field_meta.py` still spell the retired `_optimizer_field_map`. Live code, carded on `TODO-ALPHA-052-0.1.0`, not this cycle's.
5. **For R3's durable-doc audit:** the spec now names nine sibling specs by path. If R3's cross-reference sweep checks outbound links, note that these are **code-span paths, not reference-style links**, matching `spec-003`'s convention and spec-004's own pre-existing `## Problem statement` / `## Non-goals` style — deliberate, and not a scaffold violation (`check_trailing_commas --check` passes).
6. **For R3:** the section heading `## Proposed improvements` no longer exists. The tree-wide grep for spec-004 heading anchors found no external consumer, but R3's archive audit re-runs its own sweep.

---

## Review (Worker 3)

Reviewed the working-tree diff against pristine `HEAD` (`346d67312599c0536980969caa39085ab3885ae8`,
re-derived this pass) extracted read-only with `git show HEAD:<path>` into a scratch path outside the
repository. No `git stash`, `git checkout`, `git restore`, or `git worktree` at any point.

`git diff --stat -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` → **73 insertions / 196 deletions**,
`wc -l -c` → spec **236 / 35,834**, rationale **1,197 / 84,365**. Every figure in
`### Byte and line counts` that I re-derived reproduced exactly. `git log -1` over the spec still
returns `20a9752f`, so no concurrent commit swept this cycle's work.

### High:

None.

### Medium:

#### M1 — the `## Proposed improvements` rename left the rationale's own front matter stale, and its supporting count is wrong

`docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:49` (in `## How to read this file`):

```docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:48:49
  same disposition ... every slice entry keys to the parent [`## Proposed
  improvements`][spec-004-improvements] anchor and names its own heading in the entry title
```

`### Implementation steps` step 3 records "re-point the rationale's `[spec-004-improvements]`
definition and its **nine** link texts. Done." Measured after the last edit, `grep -n
'\[spec-004-improvements\]'` returns **21 body uses plus the definition**, of which **ten** name the
heading in their link text: `:49`, `:119`, `:203`, `:320`, `:361`, `:422`, `:464`, `:503`, `:543`,
`:584`, `:622`. Nine were re-pointed; `:49` was not. The count is wrong by one and the missing one is
the missed site — the two failures are the same failure, which is exactly why `BUILD.md`
`## Claims are proven mechanically, never accepted on prose` treats a stated count as a claim shape.

This is **not** the same case as `:694`, which also spells `## Proposed improvements` and is correct:
`:686`-`:689` adds a discharge pointer that explicitly scopes that list as historical ("the spec
headings it names are the ones that existed when it was written"). `:49` carries no such scope — it
is a present-tense reading instruction, and its sibling instruction at `:622` **was** updated to
`` `## The eight improvements` ``. The inconsistency inside one file is what makes it a defect rather
than a preserved record.

A second site in the same section is stale for the same reason. `:30`-`:41` defines the closing
claims block and asserts, without qualification, that it "is **not** a record of retractions already
performed, **and it could not be**". After this pass the file carries twelve blocks that are exactly
that. The section's own escape clause (`:39`-`:41`) and the new section's `**On the label.**`
preamble together make it readable one hop later, but `## How to read this file` is the index a
reader consults **first**, and R1's handoff item 19 named that definition specifically: "the file's
own definition at `## How to read this file` is what makes either spelling readable, so that
definition is the thing to keep in step, not the label alone." It was not kept in step.

**Recommended change.** Re-point `:49`'s link text to `` `## The eight improvements` ``, and add one
clause to the `:30` bullet naming the second block kind and where it is defined. Re-measure the
population with `grep -c` after the last edit and state the unit beside the number.

#### M2 — the per-response-key identity fan-out is credited to the wrong sibling in the rationale, and to no sibling at all in the spec

Spec `### B2` `**Resolver change required.**` (`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`
#"records one identity per key rather than one identity for the merged node") states the rule with no
owner named. The rationale's `### `### B2 — Forward-FK-id elision`` entry
(`docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:938`-`:940`) attributes it to
`spec-033`:

> *Changed — one identity per response key.* … a selection reachable under more than one response key
> records one identity per key, never one for the merged node ([`spec-033`][spec-033]).

The rule is **spec-003's**, not spec-033's.
`docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` #"carries one resolver identity per
key" states it in full — "a selection reachable under more than one response key carries one resolver
identity per key, never a single identity for the merged node" — and in the same sentence delegates
to spec-033 only the *multiplication* of that fan-out over nested-connection runtime prefixes.
I grepped spec-033 for `merged node` / `identity per` / `response key`: its only resolver-identity
statement (`#"Resolver keys"`) is about a connection field appending its own identities to
`plan.planned_resolver_keys`, not about the merged-node fan-out. spec-033 does not own the rule.

Both halves are wrong in the same way and for the same reason: the drift table's D9 third column says
"identity fan-out: spec-033", and this row was taken from the table rather than re-verified — the
failure mode the plan's own D17 correction was meant to inoculate against.

This matters against the pass's own stated standard. `### The three claims this pass refused to make`
opens by refusing an attribution because "a citation that might be wrong is worse than a bare true
statement". Here a citation that **is** wrong was made, and the one place the rule genuinely has an
owner the spec could name got no citation at all.

**Recommended change.** In the spec, name `spec-003` on the fan-out sentence (it is the same sibling
the adjacent ordering-invariant sentence already cites, so it costs no new vocabulary). In the
rationale, correct `[spec-033]` to `[spec-003]`, or state both with their actual division —
spec-003 the rule, spec-033 the nested-connection multiplication.

### Low:

#### L1 — the `functools.lru_cache` rejection reason is false as stated

`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` `### B1` `**Cache storage.**`:

```docs/SPECS/spec-004-optimizer_beyond-0_0_3.md:33
The LRU is hand-rolled rather than reached for through `functools.lru_cache`, since the cache
key includes a model class which is not hashable by `lru_cache`'s default.
```

A Django model class is an ordinary Python class and is hashable; `lru_cache`'s `_make_key` handles
type objects without special-casing. There is no "`lru_cache` default" that fails on it. The real
reasons are structural — `lru_cache` decorates a *function*, so it cannot be instance-bound (which
`**Cache storage.**`'s own preceding sentence requires), cannot expose `cache_info()`'s `size`
alongside best-effort counters, and cannot evict a least-recent quarter in one sweep.

`grep -rn lru_cache django_strawberry_framework/optimizer/` returns **zero** hits, so the source
offers no rationale to reconcile against; the claim is the spec's alone.

This clause is HEAD text preserved, and the drift table's D6 blesses it ("The `lru_cache`-is-unusable
reasoning still holds and is worth keeping"). But the *conclusion* holds while the *reason given* does
not, this pass rewrote the sentence carrying it, and the table is the pass's verified floor rather
than its verdict — the same standing the D17 correction established. It sits inside the one paragraph
of the spec a future builder would consult before reaching for `lru_cache`, so a false premise there
is the premise that gets argued against.

**Recommended change.** State the structural reason, or drop the causal clause and keep "hand-rolled".

#### L2 — refusal 2's supporting grep is false as stated (the conclusion is right)

`### The three claims this pass refused to make`, second bullet: "no file under `docs/SPECS/`
mentions `nested_connection_strategy` or the lateral backend."

`grep -n "nested_connection_strategy\|NestedConnectionStrategy" docs/SPECS/*.md` returns **four** hits
in `docs/SPECS/spec-043-test_client-0_0_14.md` (`:359`, `:570`, `:1329`, `:1731`), and
`grep -rln lateral docs/SPECS/*.md` returns `spec-051-boundary_dry_squeeze-0_0_20.md` (`:466`-`:468`).

I re-derived the substance and **the refusal's conclusion is correct**: spec-043 cites
`conf.py::nested_connection_strategy_setting` only as a naming precedent for its own settings key and
owns nothing of the seam; spec-051 names `optimizer/lateral_fetch.py::build_lateral_sql` as a future
DRY-squeeze target at an unshipped `0.0.20`; spec-033 mentions "strategy stamps" once, in passing, in
a finalization bullet. No `docs/SPECS/` spec owns `OptimizerHint.strategy`, and `docs/README.md`
"Nested connection indexing" is the actual owner — the spec cites the right document.

The defect is the recorded evidence, not the decision. A reader re-running the stated grep gets hits
and concludes the refusal was mistaken; the fix is one clause narrowing the claim from "no file
mentions" to "no file owns", with the two incidental mentions named so they are not re-discovered as
a contradiction. Prior passes in this cycle established that a supporting grep is worth re-running;
this one is why.

### DRY findings

- **`### B2`'s ordering-invariant paragraph restates `spec-003`'s rule rather than pointing at it,
  and the pass's own record says it did the opposite.** Both sentences are new in this pass (the
  paragraph is absent from the HEAD blob). Compare
  `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` #"It must run **ahead** of the elision
  short-circuit" against `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` #"must stay
  **ahead** of this short-circuit": the invariant, its causal argument ("an elided branch returns
  without planning a join … the N+1 the elision removes comes straight back" vs "an elided branch
  returns without planning a join … silently reintroduce the N+1 the elision exists to remove"), and
  the closing clause ("nothing enforces it but the order itself" vs "Nothing enforces the order but
  the order itself") are the same three moves in the same order. `docs/SPECS/spec-002-optimizer-0_0_2.md`
  #"each own the surface they added" is the family rule: state the behaviour, name the owner, do not
  restate the rule. Here the owner is named **and** the rule is restated, so the two documents now
  carry one argument and can diverge.

  What makes it a finding rather than a judgement call is the record: `### The three claims this pass
  refused to make`, third bullet, states "the ordering invariant is **pointed at, not restated** …
  spec-004 names that it exists, that spec-003 states it, and that nothing enforces it." That
  describes a one-clause pointer. What landed reproduces spec-003's cost argument too. Either the
  spec drops the causal clause to match the record, or the record is corrected to say the argument
  was deliberately duplicated and why — but the two must agree, because a future harmonizing sweep
  will read the record and not the sentence.

  **Recommended change.** Cut the reproduced cause: "It must run ahead of the elision short-circuit;
  `docs/SPECS/spec-003-…md` states that invariant and the cost of reversing it, and nothing enforces
  it but the order itself." One clause, owner named, no rule reproduced.

- **Examined and NOT flagged: the B1 / B8 double statement of plan immutability.** `### B1`
  `**Cache invalidation.**` and `### B8` `**Cache-safety**` both state that a plan is finalized at
  handoff and both name `spec-035`. `### DRY analysis` argues this is deliberate because each states
  a different half; I re-read both and agree — B1 states *why no invalidation is needed*, B8 states
  *why the reconciliation must copy*, and neither is derivable from the other. Recording it so the
  next pass does not re-open it.

- **Examined and NOT flagged: the twenty-one sibling citations.** Counted by occurrence rather than
  by matching line (`grep -o 'docs/SPECS/spec-0[0-9][0-9]' <spec> | sort | uniq -c`): **21 across 9
  distinct siblings** — spec-035 x6, spec-033 x5, spec-002 x2, spec-003 x2, spec-018 x2, and
  spec-023 / spec-029 / spec-032 / spec-047 x1 each. Reproduces the artifact's figure exactly. I read
  all seven rows the build plan flagged as highest-pull (D4, D7, D11, D14, D18, D25, D26) sentence by
  sentence against the cited siblings; **every one is one clause of behaviour plus a path**, and not
  one sibling rule is reproduced. Detail in `### What looks solid`.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list
are unchanged. `git status --short -- django_strawberry_framework/ tests/ examples/ scripts/` →
**empty**: no package source, test, example, or script file changed in this cycle, as the build plan's
`## Build-wide context flags` requires. No correctness defect in shipped optimizer code was found by
this review, so nothing is escalated under that heading.

### CHANGELOG sanity

Not applicable; item did not modify `CHANGELOG.md`. Confirmed by `git status --short -- CHANGELOG.md`
→ empty. `CHANGELOG.md` was read (never written) as the authority behind D16 / D22 and as one input to
refusal 1.

### Documentation / release sanity

Applies — the diff is an archived spec and its rationale companion.

- **Version strings and card IDs.** The spec carries no version or status line and this item added
  none; `## Implementation checklist` keeps all eleven `- [x]` boxes, matching `DONE-004-0.0.3`. No
  KANBAN card moved and no release metadata changed.
- **The archive is intact.** The spec stays at `docs/SPECS/`, its companions at `docs/SPECS/appx/`.
  `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-terms.csv` is **untouched** — `git status --short
  docs/SPECS/appx/` reports only the new untracked rationale, and `git log -1` on the CSV returns
  `40e4754a`, the archival commit.
- **Every link definition resolves on disk**, re-derived this pass with a parser that partitions each
  file at `<!-- LINK DEFINITIONS -->`, normalizes each target against the file's own directory, and
  diffs used-refs against defined-refs: spec **11 defs / 11 used / 0 undefined / 0 unused**, rationale
  **23 defs / 23 used / 0 undefined / 0 unused**, **34/34 targets exist**. The four definitions this
  pass added (`spec-004-checklist`, `spec-004-current-state`, `spec-004-references`, `spec-023`) and
  the re-pointed `spec-004-improvements` anchor are inside that count. Every in-spec anchor target
  resolves to a real heading: `#problem-statement`, `#current-state`, `#the-eight-improvements`,
  `#references`, `#implementation-checklist` are all present in the spec's heading list.
- **No inbound anchor breakage.** `grep -rn "spec-004-optimizer_beyond-0_0_3.md#" --include=*.md .`
  over the tree hits **only** this cycle's own rationale. The rename stranded no external consumer.
  M1 is an *internal* stale link text, not an inbound break.
- **No obsolete staging wording.** `grep -c "Can be spec'd now"` → 0; `"when B4 ships"` → 0;
  `"Proposed improvements"` → 0 in the spec; `"check_optimizer"` → 0.
- **No script-rendered doc is touched.** `docs/TREE.md`, `docs/GLOSSARY.md`, `KANBAN.md`,
  `KANBAN.html`, and `examples/fakeshop/db.sqlite3` are all clean; no docstring feeds this change.
- **Verbatim-copy check.** This item copies no text from a spec into another document, so the
  character-for-character `diff` obligation reduces to the maintainer-ruled sentence, verified below.

### Re-confirmed invariants — every one re-derived, none quoted

| Check | Command | Result |
|---|---|---|
| Glossary terms | `check_spec_glossary.py --spec <spec>` | `OK: 10 terms - all have glossary entries and at least one spec link.` exit **0** |
| Layout / scaffold | `check_trailing_commas.py --check <spec> <rationale> <this artifact>` | exit **0**, all three |
| Card glossary chain | `manage.py import_spec_terms --check` (read-only form only) | `OK: 49 done cards have glossary links.` exit **0** |
| Fenced blocks | `grep -c '^```'` | **0** in spec, **0** in rationale |
| `AGENTS.md` rule 27 | `grep -nE '[a-zA-Z_/]+\.(py\|md):[0-9]+'` | **no match** in either file |
| Maintainer-ruled sentence | `diff` HEAD `:5` vs working `:7`; `md5` | identical, `a236d060acf135d69af06a01cf43646a` both sides |
| Source / test / example | `git status --short -- django_strawberry_framework/ tests/ examples/` | empty |

**The 10-anchor constraint, re-derived per anchor.** Each of the ten reference ids resolves to exactly
**2** occurrences in the spec — one body link, one definition — so all ten remain single-carrier and
none was duplicated to hedge. I read each carrier in place and confirmed it sits in contract prose
rather than narration re-added to hold the link:

- `djangooptimizerextension` — `### B1` `**Cache storage.**` `:33`, inside the sentence that states
  the cache is an ordered dict *on the extension instance*. That instance-binding is the premise of
  the singleton-factory pointer two sentences later, so the link is load-bearing, not decorative.
- `queryset-diffing` — the `### B8` heading `:157`. Structural; survives any body rewrite.
- `metafields` + `metaexclude` — **together**, `### B6` `:131`, in the rewritten exposed-fields
  sentence ("those that passed `Meta.fields` / `Meta.exclude` filtering and are present in its
  registered definition's field map"). This is the highest-risk site: it is the sentence that also
  carried the retired `cls._optimizer_field_map`, so the rewrite had to replace the symbol and keep
  both links. It did, and the surviving clause is the audit's actual scoping rule.
- `only-projection` + `fk-id-elision` — together, `## Current state` `:13`, the section D2 rewrote
  wholesale. Both survive inside the standing foundation statement.
- `configurationerror` `:105`, `djangotype` + `optimizerhint` `:89`, `metaoptimizer-hints` on the
  `### B4` heading `:87` — all in contract prose; the B4 heading keeps its link form.

`check_spec_glossary` passing is necessary but not sufficient here (it accepts a link anywhere in the
body), which is why the per-anchor placement read above was done by hand.

**The spec narrates no history — re-run with my own alternation, not the artifact's.**
`grep -nEi 'formerly|no longer|as of (review|round)|amendment|retract|previously|used to |originally|once (was|proposed|claimed)|earlier|superseded|at the time|since (renamed|retired|corrected)|has since|was (renamed|retired|replaced|corrected|changed)|now reads|revised|updated to|round [0-9]|this spec (once|previously)|deprecated in favou?r|historical|stale|obsolete|initially|first (proposed|written)|later spec|corrected'`
over the spec returns **one** line: `:3`, R1's companion pointer, which describes the rationale
file's contents and which H18 / H20 place off-limits. Twenty-eight alternates beyond the artifact's
seven, zero additional hits. The spec reads as a clean current contract.

### Correctness against source — what I re-verified, and how

Sampled with symbol-qualified paths against HEAD source, not against the drift table. **The eight
S-findings are all real**; not one is invented, and each restatement matches what the package does:

- **S1** `optimizer/extension.py::DjangoOptimizerExtension.__init__` — signature is
  `strictness: str = "off"` **positional**, no `Literal`; `if strictness not in ("off", "warn",
  "raise"): raise ValueError(...)` at construction. The spec's replacement ("three named levels …
  validated at construction, so an unrecognised value raises at the call site") is exact.
- **S2** `utils/context.py::stash_on_context` — `if not isinstance(context, dict):` guards the
  `setattr` block, so `dict` and `dict` subclasses take the mapping path **first**; the docstring
  names the locked-`QueryDict` case explicitly. The spec's rewrite matches, including the
  skip-on-frozen rule.
- **S3** `grep -rn weakref django_strawberry_framework/` → **one** hit,
  `filters/sets.py` #"provides ``__dict__`` / ``__weakref__``", a comment about scalar subclassing.
  No weakref mechanism, and `self._plan_cache` is an instance attribute. The parenthetical described
  nothing.
- **S4** `types/resolvers.py::_check_n1` — emits `OptimizerError(f"Unplanned N+1: {field_name}
  {suffix}")` and `"Potential N+1 on %s%s"`, where `suffix` is the caller's optional `reason`. The
  parent type and runtime path are components of the resolver **key**, never of the message. A test
  written from the old sentence would have pinned a message the package does not emit.
- **S5** `optimizer/extension.py::DjangoOptimizerExtension.check_schema` — one warning condition,
  `meta.related_model is not None and registry.get(meta.related_model) is None`. No custom-resolver
  detection anywhere in the body.
- **S6** same symbol — the message is
  `f"{type_cls.__name__} ({_model.__name__}.{field_name}) has no registered target DjangoType"`:
  type, model, field, no fix. The spec's "naming the type, the model, and the field" is exact.
- **S7** `## References` at HEAD read "load-bearing for **B1's cache correctness** and B2's elision
  safety"; the reconciled clause reads "B8's reconciliation and B2's elision safety". Correct —
  `optimizer/plans.py::diff_plan_for_queryset` is what consumes the `query.select_related` dict merge
  and `_prefetch_related_lookups`; B1's cache never reads either.
- **S8** `optimizer/field_meta.py::FieldMeta` — `@dataclass(frozen=True, slots=True)` with
  **eighteen** annotated fields, counted from `name: str` through `object_id_field_name`. The spec's
  replacement reads as illustrative ("the optimizer-relevant core … plus the further slots the later
  relation work needed"), which is the honest shape for a list that cannot stay exhaustive.

Spot-checks beyond the S-list, each a rewritten sentence traced to source:

- **D3 / D27** `::_build_cache_key` returns the 5-tuple `(doc_key, relevant_vars, target_model,
  runtime_path_from_info(info), origin)`; the docstring's component 1 says the printed string is
  stored "not its `hash`" for the collision reason the spec now gives. `::_get_or_build_plan`
  #"resolved_selections = selections() if callable(selections) else selections" is the deferred
  thunk, invoked only after both caches miss — so "invoked at most once, and only on the build path"
  holds.
- **D4** `::_collect_cache_var_families` returns `(directive_names, pagination_names)` from one walk;
  `::_collect_nested_pagination_var_names` is documented as "field node at response-path depth >= 1",
  i.e. non-root. Values normalized through `::_hashable_variable_value` "because the name-keyed
  pagination collector deliberately over-collects" — the spec's over-collection rule restated from
  the source's own reasoning, correctly.
- **D6** `_MAX_PLAN_CACHE_SIZE = 256`, `OrderedDict`, `move_to_end` under `suppress(KeyError)`,
  eviction `max(1, _MAX_PLAN_CACHE_SIZE // 4)` via `popitem(last=False)`. Exactly the bound, storage
  and quarter-batch the spec now states. Dropping the `suppress` guard to the rationale is right: it
  is a lock-free trade, not a contract.
- **D7** three memos confirmed and correctly partitioned — `_cache_key_parts_cache` and
  `_execution_plan_cache` are both `ContextVar`s `set()` in `::on_execute` and `reset()` in its
  `finally`; `_doc_key_cache` is a module-level `OrderedDict` whose comment says "this module-level
  LRU carries the far more valuable cross-request reuse". "Two per-execution … and a cross-request
  memo" is exact.
- **D8** `::CacheInfo` is a `NamedTuple` of `hits` / `misses` / `size`; I traced the control flow for
  the counter claim rather than trusting it — the `exec_memo` hit **returns before**
  `self._cache_misses += 1` and after the `_cache_hits` increment's branch, so it genuinely touches
  neither. `misses` does count walker builds.
- **D9** `walker.py::_plan_select_relation` and `::_plan_prefetch_relation` both open with
  `_record_relation_access(..., enable_only=enable_only)`, and the elision `return`s from
  `append_unique_many(plan.fk_id_elisions, resolver_identities)` after it. Shared first step, gated,
  ahead of the short-circuit — all three true. (The prose duplication is the DRY finding above, not
  a correctness one.)
- **D11** `types/resolvers.py::_build_fk_id_stub` — `return _FK_ELISION_UNSAFE` on the deferred-column
  arm, `state.adding = False`, `state.db = router.db_for_read(...)`. Both riders present.
- **D13 / D14** `plans.py::_MAX_PATH_DEPTH = 1024` bounds `::runtime_path_from_path` and raises past
  it; `::_check_n1` carries the `kind == "connection_to_attr"` third arm and the `force_unplanned`
  bypass of `if key in planned`. The label correction ("One further probe, and one override") is
  right — the override is not a probe.
- **D15** `hints.py::OptimizerHint.strategy` exists; `__post_init__` raises `ConfigurationError` on
  non-bool flags, on `skip` combined with anything, and on `force_select and force_prefetch`.
  `OptimizerHint` is `@dataclass(frozen=True)` in `optimizer/hints.py` and is in
  `django_strawberry_framework/__init__.py`'s `__all__` — the spec's re-export claim holds.
- **D16 / D22** `grep -c "_optimizer_field_map"` over the spec → **0**; the only two
  `_optimizer_hints` matches are the real symbols `_validate_optimizer_hints` and
  `_resolve_optimizer_hints`. `walker.py::_resolve_optimizer_hints` reads
  `definition.optimizer_hints`. Both retired mirrors are gone from the prose.
- **D17 — the row the plan corrected once, so I re-derived it from scratch rather than from either
  version.** `types/base.py::_validate_meta` and `::_validate_optimizer_hints` both exist and are
  called one line apart (#"validated = _validate_meta(cls, meta)" then
  #"_validate_optimizer_hints(validated.optimizer_hints, fields, model=meta.model)"). The gate's body
  is exactly three checks: unknown-to-the-model names, names outside `selected_relation_names`, and
  non-`OptimizerHint` values, each raising `ConfigurationError`. **The "hint under an empty field
  selection" case the plan lists as a fourth is not a fourth** — with no selected relations the
  second check catches every key, which is why the spec's "excluded by `Meta.fields`/`Meta.exclude`,
  or selected but scalar" is complete rather than short. The rewrite is correct and was written from
  the corrected premise.
- **D19 / D20 / B6** `check_schema` is a `@staticmethod` (the one-word H3 correction landed);
  dedupe key is `(_model, field_name)`; `::_collect_schema_reachable_types`'s docstring names object
  fields, union members and interface implementations. `registry.py::TypeRegistry.iter_types` yields
  `(model, type_cls)` "once per registered type" with the dedupe-by-model contract in its docstring —
  the spec's sentence matches word for word in substance.
- **D26** `plans.py::diff_plan_for_queryset(plan, queryset) -> tuple[OptimizationPlan, Any]`, its
  docstring naming the string-to-`Prefetch` upgrade as the reason the queryset is returned;
  `::prune_unsupportable_select_related` is the companion step and its docstring names the
  `FieldError` a deferred connector produces. Both halves of the spec's paragraph are exact.
- **B8 opening paragraph (H12)** — HEAD's "the optimizer **blindly stacks** another
  `.select_related(...)` on top" is gone; the paragraph now states the condition and what B8 does
  about it. The one item no drift row covered is discharged.
- **H4** the `B1 cache-lifetime spike` checklist box keeps its tick and lost its parenthetical.
- **B4's hedge** — HEAD's "a small class (or `enum` + factory methods) … re-exported … **when B4
  ships**" is gone in both halves.

**The three refusals, graded.**

1. **Root-response-path component stated unattributed — correct, and I re-derived the
   unestablishability rather than accepting it.** `spec-030` never mentions the plan-cache key.
   `spec-033` #"the target model, the root runtime path, and the origin type" lists the component as
   part of the key it *found*, in a paragraph whose whole point is what spec-033 must still add — it
   claims the component, it does not claim to have added it. `CHANGELOG.md` #"the root response path"
   lists it among a batch of fixes with no card attribution. Nothing establishes an owner. Stating
   the component bare is the right call.
2. **`OptimizerHint.strategy` cited to `docs/README.md` — correct conclusion, defective evidence.**
   Graded in L2 above: I re-derived that no `docs/SPECS/` spec owns the seam, so the citation is
   right; only the supporting grep claim needs narrowing.
3. **The ordering invariant "pointed at, not restated" — the refusal to add a source guard is
   correct; the description of what landed is not.** Declining to add an automated guard is plainly
   right (`## Build-wide context flags` makes source read-only and this is a docs cycle). But the
   sentence that landed reproduces spec-003's causal argument, so the record and the spec disagree.
   That half is the DRY finding above.

### Dispatched findings checklist — walked

All **56** boxes are ticked. I walked every one against the diff and against source; **no box is
ticked without a matching change or a recorded decided non-edit**, and no box the diff addresses was
left open. Spot-verified the ones most easily over-ticked:

- **D24 / D28** ticked as "discharged by R1 — verified, not performed": confirmed. All eight `### B`
  headings sit under `## The eight improvements` in order, and `## Priority and ordering` is absent
  from the heading list. Correctly a verification, not an edit.
- **D12** ticked as "superseded — no edit owed for the fence": correct, and the report-shape half was
  properly re-filed as S4 rather than folded in silently.
- **D21** ticked as a **drop**: `grep -c check_optimizer` → 0 in the spec, and
  `django_strawberry_framework/management/commands/` ships `export_schema` and `inspect_django_type`
  only. Deferral recorded in the rationale and carried to `### Notes for Worker 1`. Discharged.
- **H6 / H18 / H19 / H20** are do-not-do instructions; all four honoured — see the next subsection
  for the two I was told to test specifically.
- **H10 / H16** carry no box because R1's pass-7 list marks them discharged on arrival; both are
  accounted for in prose under `**Handoff items.**`, so all twenty handoff items are covered by
  eighteen boxes plus two recorded closures. Complete, if slightly loose.
- The only checklist item my findings touch is **D1**, whose disposition ("Heading renamed
  `## The eight improvements`") is correct in the spec; M1 is fallout in the *rationale*, which the
  box does not claim.

### The two standing do-not-reverse instructions — both held

- **H19, the modal-label divergence.** `grep -n "Claims the spec"` over the rationale: the ten
  pre-existing entry blocks (`:199`, `:313`, `:356`, `:416`, `:459`, `:497`, `:537`, `:579`, `:616`,
  `:670`) all still read `**Claims the spec may no longer make.**`, and R1's one deliberately-scoped
  stronger label at `:171` is unchanged. **Nothing was levelled to the sibling form.** The twelve new
  blocks use the factual spelling and the divergence is scoped in the new section's own
  `**On the label.**` preamble at `:794`-`:798`, which is the right instinct — my M1 is only that the
  front-matter definition was not extended to match.
- **H20, the five/two per-slice pointer asymmetry.** Read all eight in place: `:41` (B1), `:63` (B2),
  `:81` (B3), `:109` (B4), `:139` (B6) read "The **competitive** argument for this slice"; `:119`
  (B5) and `:151` (B7) read "The **opening** argument for this slice"; `:171` (B8) carries neither,
  because its paragraph stayed in the spec. Five, two, and one — exactly the shape H20 protects, and
  the reason it is correct (B5's and B7's `**The win.**` paragraphs named no competitor) still holds.
  **Nothing was levelled.**

### What looks solid

- **The anti-absorption discipline is the strongest thing in this pass, and it holds under a
  sentence-level read of all seven flagged rows.** D4 names the second variable family and hands the
  windows to `spec-033` without describing a window; D7 states immutability in one clause and hands
  the enforcement to `spec-035`, and hands the nested fallback to `spec-033` without describing the
  fallback; D11 gives `state.db` one clause plus `spec-023` and the loud fallback one clause plus
  `spec-035`; D14 gives the third probe and the override one clause each; D18 hands the shared
  dispatch to `spec-047` and the union rule to `spec-033` while keeping the execution reset as
  spec-004's own (correct — I confirmed no sibling owns `clear_optimizer_context`); D25/D26 name both
  `spec-035`'s stance and `spec-033`'s subtree-awareness and describe neither. Not one of the nine
  cited siblings' rules is reproduced in those seven rows. The two places the report itself
  volunteered as most challengeable (B1's `**Cache invalidation.**` second paragraph, B8's prune
  paragraph) are both clean on this test.
- **The judgement calls are argued rather than asserted, and each has a recorded loser.** Dropping
  D21 rather than marking it deferred in-spec is right on the stated ground — "a deferral with no
  card and no date is indistinguishable from a forgotten obligation" — and the obligation is not
  lost, because it lands in the deferred-work catalog and in `### Notes for Worker 1`. Stating D6's
  256 bound and quarter-eviction in a contract is defensible: they are consumer-observable through
  `cache_info().size`. Deliberately *not* naming the elision record's container while stating the
  identity rule is exactly the right line between contract and internal shape.
- **The `**Cache invalidation.**` de-duplication.** The "static queries collapse to one cache entry"
  claim lived in two paragraphs at HEAD; the duplicate went and the survivor was corrected to the
  five-component key. That is a DRY fix inside the rewrite, found without being asked for.
- **D17 was re-derived, not inherited.** This is the row the plan had already got wrong once, and the
  rewrite is written from the corrected premise — it names `_validate_meta` as real and the
  `__init_subclass__` entry point, puts the rejections in the sibling, and adds the two gates the
  spec never stated. I re-derived the whole gate from source and found the spec's version complete,
  including the empty-field-selection case being subsumed rather than missing.
- **The maintainer-ruled sentence is byte-identical and was proved the right way** — by `diff` and
  `md5` of the *line*, extracted read-only from the HEAD blob, not by the file's byte count. HEAD `:5`
  and working `:7` (the two-line shift is R1's companion pointer) are identical.
- **The counts I re-derived all reproduced**: 73/196 diff stat, 236 lines / 35,834 bytes,
  1,197 lines / 84,365 bytes, 21 sibling citations across 9 specs with the exact per-spec breakdown,
  ten anchors at exactly two occurrences each, 11/11 and 23/23 link definitions. Given this cycle's
  history with counts, that is worth stating explicitly. The one count that did not reproduce is M1's
  "nine link texts".
- **Three residues I could have dressed up as findings and deliberately did not.** (a) The rationale's
  `## How to read this file` bullet 8 ("What the rationale-extraction pass did NOT do") still reads as
  though the reconciliation is pending — but it is scoped to that pass by its own first three words
  and is accurate as history. (b) `### B7`'s `**Test surface.**` keeps "Benchmark (optional)", which
  reads as unbuilt work — but it is marked optional and was never a delivery claim. (c) `## Current
  state` still asserts the optimizer is "effective end-to-end", an unfalsifiable-as-written claim —
  but it is HEAD's own wording, no reader takes a wrong action from it, and rewriting it would be
  scope this item did not open. Recorded so the next pass does not re-derive them and cannot mistake
  silence for an unexamined area.

### Temp test verification

No temp tests were created. `docs/builder/temp-tests/r2/` was not used and remains empty. This item
changes no code and adds no boundary, so there is nothing a test could pin: `BUILD.md`
`### What needs a proof, and what does not` scopes failability proofs to new boundaries, guards,
gates, and rejection paths, and a documentation reconciliation introduces none. Verification here was
read-and-re-derive against source and against the read-only HEAD blob, which is the whole of the
available technique. No `pytest` was run (`AGENTS.md` rule 15), and no `--cov*` flag was used in any
command in this pass.

### Working-tree churn observed during this review — reported, not reverted

**The list grew during this pass, and the growth is a Worker 0 / maintainer matter, not R2's.**
`git status --short` now reports four entries the item's own `### Working-tree state` reading did not:

```
 D docs/builder/bld-003-final.md
 D docs/builder/bld-003-r1-rationale_move.md
 D docs/builder/bld-003-r2-spec_reconciliation.md
 D docs/builder/bld-003-r3-doc_completion_archive.md
```

All four are **committed** files (`git log -1` returns `20a9752f`, the spec-003 cycle's commit) and
all four are now absent from disk — `ls docs/builder/` confirms it. **This cycle's build plan
`### Deviation 1` explicitly preserves them**, naming `bld-003-r3-doc_completion_archive.md` as "the
record of the one sibling-spec edit that landed inside spec-004" and stating that deleting them
"would destroy the record of work this cycle's own reconciliation depends on". The most likely cause
is a concurrent session running `scripts/clean_up.py`, which `### Deviation 3` already notes "also
deletes `docs/builder/bld-*.md`".

**Nothing was reverted** (`AGENTS.md` rule 34, and the deletion is not this item's to undo). Recorded
here so Worker 0 can append it to the plan and the maintainer can decide whether to restore them
before commit. R3 must not read `docs/builder/` as clean.

Everything else is unchanged from the item's own reading: `M docs/SPECS/spec-004-…md` plus the four
untracked cycle files. `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`, `CHANGELOG.md`,
`examples/fakeshop/db.sqlite3`, `django_strawberry_framework/optimizer/predicates.py` and the
renumbered spec set are all **clean**, confirming the item's "clean at the start" reading — though R3
still re-derives rather than inherits it. `HEAD` is `346d6731`, unchanged across this pass.

### Notes for Worker 1 (spec reconciliation)

**This is the complete R3 handoff. Nothing lives only in a closed section**, so items this item
recorded elsewhere are re-issued here in full rather than cross-referenced.

1. **Two Mediums, two Lows and one DRY finding are open and route to Worker 1**, not Worker 2 — the
   build plan's `### Deviation 2` corollary makes the apply-changes pass Worker 1's, setting
   `Status: planned` again. M1 and the DRY finding are rationale/spec edits inside files Worker 1
   already owns; M2 touches both files; L1 is one clause in the spec; L2 is one clause in this
   artifact. None needs maintainer context, so the `review-accepted`-with-escalation carve-out does
   not reach them.
2. **Deferred, for the final gate's `### Deferred work catalog`:** the `check_optimizer` management
   command and custom-resolver detection (D21 / S5) — named as B6 follow-up work eleven versions ago,
   never built, no card names either. Dropped from the spec by this item and recorded in the
   rationale. `inspect_django_type` (spec-029) answers a different question and is explicitly not
   offered as a substitute.
3. **Deferred:** the `_record_relation_access`-before-elision ordering invariant still has **no
   automated guard** in `walker.py::_plan_select_relation`. Carried unchanged from Worker 0's
   read-only audit; adding one is a source change and out of scope for a documentation cycle. The
   spec now points at `spec-003`, which is the most a docs cycle can do — subject to the DRY finding
   above about *how much* of spec-003 it reproduces while pointing.
4. **Deferred, sibling-spec staleness:** `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` calls
   `0.316.0` "the locked" Strawberry version; it is the **declared floor** (`pyproject.toml`
   #"strawberry-graphql>=0.316.0") and `uv.lock` resolves higher. This cycle's own rationale phrasing
   was corrected (H17); sibling specs are read-only with no declared exception, so it is recorded,
   not fixed. R1's handoff item 17 asked that whoever tightens it decide for both documents rather
   than leave them disagreeing — after this item they **do** disagree, which is the state R3 or a
   future spec-029 cycle inherits.
5. **Deferred:** three B7 test names in `tests/optimizer/test_field_meta.py`
   (`::test_optimizer_field_map_populated`, `::test_optimizer_field_map_contains_relations`,
   `::test_optimizer_field_map_respects_fields_filter`) still spell the retired
   `_optimizer_field_map`. Live code, carded on `TODO-ALPHA-052-0.1.0`, not this cycle's; no test file
   is writable here.
6. **For R3's durable-doc audit — the spec now names nine sibling specs by path, as code spans, not
   reference-style links.** Twenty-one occurrences across spec-002, 003, 018, 023, 029, 032, 033, 035,
   047. This matches `spec-003`'s convention and spec-004's own pre-existing `## Problem statement` /
   `## Non-goals` style, keeps the link-definition block at 11 entries, and is **not** a scaffold
   violation — `check_trailing_commas.py --check` passes on both files. R3's cross-reference sweep
   should not "fix" them into reference-style links.
7. **For R3:** the section heading `## Proposed improvements` no longer exists; it is
   `## The eight improvements`, anchor `#the-eight-improvements`. My own tree-wide
   `grep -rn "spec-004-optimizer_beyond-0_0_3.md#" --include=*.md .` confirms **no external consumer**
   links a spec-004 heading anchor — the only hits are this cycle's own rationale. R3 re-runs its own
   sweep, but the answer at this hash is that the rename is externally safe. The two *internal*
   residues are M1 above (`:49`, live and stale) and `:694` (historical and correctly scoped).
8. **For R3, and this one is new:** `docs/builder/bld-003-final.md`,
   `bld-003-r1-rationale_move.md`, `bld-003-r2-spec_reconciliation.md`, and
   `bld-003-r3-doc_completion_archive.md` were **deleted from the working tree during this review**
   (committed at `20a9752f`, now `D`). The build plan's `### Deviation 1` preserves them on purpose.
   Nothing was reverted. Worker 0 should append this to `## Baseline-dirty out-of-scope files`, and
   the maintainer should decide whether to restore before commit; R3 must not treat `docs/builder/`
   as clean.
9. **For R3's re-derivation duties, with expiry noted.** My readings — 34/34 link targets resolve,
   `import_spec_terms --check` green, ten anchors single-carrier, `check_spec_glossary` green,
   `db.sqlite3` clean — are current at `346d6731` and **have an expiry**. R3 re-runs each itself,
   re-runs `import_spec_terms --check` **after** any further concurrent DB write, and attributes any
   dirty `db.sqlite3` by `iterdump()` set-difference rather than by file bytes.
10. **No correctness defect in shipped optimizer code was found.** Everything I traced —
    `_build_cache_key`, `_get_or_build_plan`, `check_schema`, `_check_n1`, `_build_fk_id_stub`,
    `_validate_optimizer_hints`, `diff_plan_for_queryset`, `_plan_select_relation` — behaves as the
    reconciled spec now states. Nothing is escalated to the maintainer under `## Build-wide context
    flags`' read-only-audit rule.

### Review outcome

`revision-needed`.

Two Mediums, two Lows and one DRY finding, none addressed and none intentionally rejected;
`worker-3.md`'s acceptance gate requires every finding to be one or the other. All five are
short, decided edits inside files Worker 1 already owns, and none reopens a settled question:
M1 finishes a rename this item began, M2 corrects one citation and adds one, L1 replaces a false
premise with the true one, L2 narrows one clause of this artifact's own evidence, and the DRY finding
brings the spec sentence and the record of it back into agreement.

**Everything the prompt sent me to grade came back clean apart from those five.** All 28 drift rows
carry an explicit, defensible disposition and the two the plan warned were fallible (D17, D24) were
re-derived rather than inherited. All eight S-findings are real at HEAD and none is invented. Two of
the three refusals are right for the reason given and the third is right in substance. The
ten-anchor constraint held per anchor with each carrier read in place. The chronology sweep, re-run
with twenty-eight alternates beyond the artifact's seven, still returns only `:3`. Both
do-not-reverse instructions held. The anti-absorption discipline survives a sentence-level read of
all seven high-pull rows — which is the hardest thing this item had to do, and it did it.

Per `### Deviation 2`'s corollary this routes to **Worker 1**, which applies the corrections and sets
`Status: planned` again.

---

## Build report (Worker 1, apply-changes pass)

`### Deviation 2`'s corollary routes an R2 `revision-needed` to Worker 1, not Worker 2. This pass
applies Worker 3's five findings and returns `Status: planned`, which Worker 0 reads as "dispatch
Worker 3" for this item. **Every prior section of this artifact is unedited** apart from the
`Status:` line, which is the field's own owner-updated value; L2's correction is stated here rather
than by rewriting the sentence it corrects.

Plan declarations, unchanged from the item's: ownership partition `none; sequential residual items`;
hot-path `none`; floor-verification scope `none`. No `--cov*` flag was used in any command.

### Findings disposition

All five are **fixed**. None was rejected. The reconciliation itself was not reopened: no drift-row
disposition changed, no S-finding was re-argued, and no sentence outside the five findings' own
sites and their same-shape siblings was touched.

| Finding | Disposition | Sites edited |
|---|---|---|
| M1 (stale rename site + wrong supporting count) | Fixed, plus its count restated as a population | rationale `## How to read this file` link text; the same section's claims-block definition; the `## The eight improvements` entry's count sentence |
| M2 (fan-out credited to `spec-033`) | Fixed in both files, **plus two further sites of the same shape** | spec `### B2` `**Resolver change required.**`; rationale B2 reconciliation entry; rationale B2 *move-pass* entry; rationale `**On restraint.**` |
| L1 (false `lru_cache` reason) | Fixed; the conclusion kept, the reason replaced with the structural one, **plus two further sites** | spec `### B1` `**Cache storage.**`; rationale `**Kept in the spec**` bullet; rationale B1 reconciliation entry (new *Changed* paragraph + claims-block line) |
| L2 (refusal 2's grep is false as stated) | Corrected **here**, not in place | this section, `### L2 — the corrected statement of refusal 2's evidence` below |
| DRY (ordering invariant restated while the record says pointed-at) | Fixed **in the spec**, so the record becomes true; the rejected alternative recorded | spec `### B2` column-append paragraph; rationale B2 reconciliation entry (new *Alternative rejected* paragraph) |

### M1 — the rename site, and the count re-derived rather than repaired

**The stale site.** The rationale's `## How to read this file` anchor-keying bullet spelled the link
text `` `## Proposed improvements` ``; it now spells `` `## The eight improvements` ``. Its sibling
instruction later in the file already spelled the new heading, which is what made the pair an
inconsistency rather than a preserved record.

**The count.** The item's "nine link texts" was a count of *what a pass believed it had touched*,
and a count of that shape cannot detect what the pass did not touch — which is why the wrong number
and the missed site were one defect. It is replaced in the rationale by the **population**, stated
with its unit and its command so a reader re-derives it:

- `grep -o '\[spec-004-improvements\]' <rationale> | wc -l` -> **21** occurrences of the reference
  id, counted by occurrence rather than by matching line: **20** body uses plus **1** definition.
- **All 20** body uses name the heading in their link text. **17** are the bare
  `[The eight improvements][spec-004-improvements]` form
  (`grep -o '\[The eight improvements\]\[spec-004-improvements\]' <rationale> | wc -l` -> 17); the
  other **3** spell it inside a code span with the `##` prefix, at the anchor-keying bullet, the
  `**The win.**` entry, and the `## Priority and ordering` entry. (A grep for that code-span form
  returns 4 lines, one of which is the heading-entry's own `###` title rather than a link - a
  matching-line count over-reads the population by one, which is the failure mode this bullet is
  measured to avoid.) 17 + 3 = 20.
- Old-spelling occurrences remaining in the rationale: **2**, both correct as history and both
  verified in place — the `## Standing notes` list entry, scoped historical by the discharge
  pointer four lines above it, and the `*Changed - the heading was ...*` change record, which is a
  quotation of the prior heading. **0** in the spec.

**The claims-block definition.** The bullet asserted, unqualified, that the block "is **not** a
record of retractions already performed, **and it could not be**". Twelve blocks in this file now
are exactly that. The bullet is rewritten to define **both** kinds: the modal
`**Claims the spec may no longer make.**` under `## Entries keyed to the spec` (worklist, scoped to
the rationale-extraction pass, which could only retract what it removed) and the factual
`**Claims the spec no longer makes.**` under `## The reconciliation pass - what the spec now
states` (receipt, because that pass performed its retractions), pointing at that section's
`**On the label.**` preamble as the definition of the divergence and repeating that neither
spelling may be levelled. R1's handoff item 19 asked for the definition to be kept in step with the
label; it now is.

**Label counts re-derived after the last edit** (line-initial block labels only, so prose mentions
of a label do not inflate the count): `grep -c '^\*\*Claims the spec may no longer make\.\*\*'` ->
**10**; `grep -c '^\*\*Claims the spec no longer makes\.\*\*'` -> **12**; plus R1's one
deliberately-scoped stronger label (`**Claims the spec no longer makes as any slice's own
argument.**`). Identical to Worker 3's reading. **H19 held: nothing was levelled.**

### M2 — the attribution, re-derived from source, and swept

**Re-derived, not accepted from the review.**
`docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` #"carries one resolver identity per
key" states the rule in full and, in the same sentence, delegates only the nested-connection
multiplication to `spec-033`. `grep -n "identity per key\|merged node\|response key"` over
`spec-033` returns one resolver-identity statement (#"Resolver keys"), about a connection field
appending its own identities to `plan.planned_resolver_keys` - not the merged-node fan-out.
spec-003 owns the rule.

**Fixed at four sites, not two.** The review named two; the sweep the shape demands (an attribution
taken from the drift table's owner column rather than from source) found two more:

1. **Spec `### B2`** - the fan-out sentence named no owner. It now reads "... rather than one
   identity for the merged node - `docs/SPECS/spec-003-...md` owns that fan-out rule, and
   `docs/SPECS/spec-033-...md` multiplies it over nested-connection runtime prefixes." One clause of
   behaviour plus two paths; neither sibling's rule is reproduced.
2. **Rationale, B2 reconciliation entry** - `([`spec-033`][spec-033])` corrected to the actual
   division, with one sentence recording that the wrong citation came from the drift table's D9
   owner column rather than from the sibling spec.
3. **Rationale, B2 *move-pass* entry (new site)** - #"which is [`spec-033`][spec-033]'s fan-out",
   written a round earlier, carried the identical error. Corrected the same way.
4. **Rationale, `**On restraint.**` (new site)** - listed "alias fan-out" among what `spec-033`
   extended. Narrowed to "the nested-connection multiplication of the response-key fan-out", and a
   sentence added recording that two rules B2 leans on run the other way, out of the foundation:
   the fan-out itself and the FK-column ordering invariant are both `spec-003`'s.

**The rest of the citation surface was swept for the same shape and is sound.** Every sibling
citation in the spec was re-checked against the cited document or against source:
`spec-029` Decision 3 exists and is the singleton-factory ruling (#"Decision 3 - Slice 1 adopts the
singleton-factory `extensions=` form"); `spec-035` Revision 4 names the operation-type `enable_only`
projection gate and its Decision 5 the FK-id-elision loaded-check; `spec-047` is a real second
consumer of the stash - `resource_policy.py` #"from .utils.context import clear_context_key,
get_context_value, stash_on_context" - even though that spec never spells the helper's name;
`spec-033` Decision 7 owns the pagination cache-key component and #"unions
`DST_OPTIMIZER_FK_ID_ELISIONS`" the union rule; `spec-018` owns several types over one model;
`spec-032` owns the Relay interface work; `spec-023` owns multi-database routing. **No further
misattribution found.**

**Citation count re-measured after the last edit**, by occurrence
(`grep -o 'docs/SPECS/spec-0[0-9][0-9]' <spec> | sort | uniq -c`): **23 occurrences across 9
distinct siblings**, up from 21 - spec-033 x6 (was 5) and spec-035 x6, spec-003 x3 (was 2),
spec-002 x2, spec-018 x2, and spec-023 / spec-029 / spec-032 / spec-047 x1 each. The two added
occurrences are M2's single sentence.

### L1 — the false reason, replaced rather than deleted

**Re-derived.** A Django model class is an ordinary Python class. Run against the project
interpreter: an `lru_cache`-decorated function called twice with the same class object reports
`CacheInfo(hits=1, misses=1, ...)`, so the default key builder takes a type object without
special-casing. `grep -rn lru_cache django_strawberry_framework/optimizer/` returns **0** hits, so
no source reading ever backed the claim; the ten hits elsewhere in the package
(`keyset.py`, `permissions.py`, `utils/relations.py`, `utils/permissions.py`) are unrelated
decorated functions. The claim was the spec's alone.

**What the spec now says.** "The LRU is hand-rolled rather than reached for through
`functools.lru_cache` because that decorator caches a *function* and this cache is bound to the
extension instance; it also evicts one entry at a time where this cache drops a quarter in one
sweep." The conclusion is unchanged, the instance-binding premise is the one the same paragraph
already states two sentences earlier, and the batch-eviction half is the bound the same paragraph
states. **The causal clause was replaced, not dropped** - this is the one paragraph a builder
reaching for the decorator would consult, so leaving it reasonless invites the change it exists to
prevent. That alternative is recorded as rejected in the rationale.

**Two further sites of the same claim, both fixed.** The rationale reproduced the false reason in
its `**Kept in the spec**` bullet (as a bolded rule) and listed "the `lru_cache`-cannot-hash-a-model
rejection" among the section's reasoning that was "unchanged and left word for word". The first now
states the rejection without the false cause and points forward; the second drops the item from the
unchanged list and hands it to a new *Changed - why `functools.lru_cache` was rejected* paragraph in
the B1 reconciliation entry, which carries the re-derivation, the structural reasons, and the
rejected alternative. `That functools.lru_cache cannot hash a model class` is appended to that
entry's claims block. `grep -n lru_cache <rationale>` now returns 6 lines, none asserting the false
reason.

### L2 — the corrected statement of refusal 2's evidence

`### The three claims this pass refused to make`, bullet 2, is **left byte-identical** - prior
entries are never edited. Its conclusion stands; its supporting grep does not, and the corrected
statement is here:

> No file under `docs/SPECS/` **owns** `OptimizerHint.strategy`. Two mention the seam incidentally
> and neither claims it: `spec-043-test_client-0_0_14.md` cites
> `conf.py::nested_connection_strategy_setting` four times as a naming precedent for its own
> settings key, and `spec-051-boundary_dry_squeeze-0_0_20.md` names
> `optimizer/lateral_fetch.py::build_lateral_sql` as a future DRY-squeeze target at an unshipped
> `0.0.20`; `spec-033` mentions "strategy stamps" once in passing. `docs/README.md` "Nested
> connection indexing" is the actual owner, and is what the spec cites.

The distinction that matters is **mentions** versus **owns**, and the original wrote the first while
meaning the second. The spec's citation is unchanged because the conclusion was right.

### DRY — the spec was fixed, so the record became true

The item's refusal 3 recorded the ordering invariant as "pointed at, not restated"; the sentence
that landed reproduced `spec-003`'s three moves in `spec-003`'s order. **The spec was the wrong
half**, so the spec was cut rather than the record rewritten:

- Before: "It must run **ahead** of the elision short-circuit: an elided branch returns without
  planning a join, so a column appended after the short-circuit is never projected and the N+1 the
  elision removes comes straight back. `docs/SPECS/spec-003-...md` states that ordering invariant;
  nothing enforces it but the order itself."
- After: "It must run **ahead** of the elision short-circuit;
  `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` states that ordering invariant and
  what reversing it costs, and nothing enforces it but the order itself."

The **requirement** - the append runs first - is what a reader of B2 alone must be able to act on,
and it stayed. The **cost** is one hop away in the document that owns it. `spec-002` #"each own the
surface they added" is the family rule this restores, and the rationale's B2 reconciliation entry
now carries an *Alternative rejected - restate spec-003's cost argument alongside the pointer*
paragraph naming what was reproduced and why two copies of one causal argument is one copy too many.

The B1/B8 double statement of plan immutability, which Worker 3 examined and did not flag, was **not
touched**.

### Spec changes made (Worker 1 only)

Three, all in `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`, all in-place rewrites of sentences
this item had already rewritten (so the file's line count and `git diff --stat` are unchanged). Line
numbers are pin-at-write-time against the current 236-line file. Triggered by R2's review, not by a
new slice.

1. **`### B1` `**Cache storage.**` (spec:33)** - the `functools.lru_cache` rejection's causal clause.
   Reason: the stated reason was false at HEAD (a model class is hashable; zero `lru_cache` in
   `optimizer/`), and the paragraph is the one a builder reaching for the decorator would consult.
   Conclusion preserved; structural reason substituted.
2. **`### B2` column-append paragraph (spec:49)** - dropped the reproduced causal argument, kept the
   requirement and the pointer. Reason: `spec-002` #"each own the surface they added" - the invariant
   and its cost are `spec-003`'s to state, and the item's own record said the spec pointed rather
   than restated.
3. **`### B2` `**Resolver change required.**` (spec:55)** - named `spec-003` as the fan-out rule's
   owner and `spec-033` as the nested-connection multiplication. Reason: the rule had no owner named
   in the spec and a wrong one in the rationale.

No other spec sentence was touched; the maintainer-ruled `## Problem statement` sentence is proved
byte-identical to HEAD below.

### Files touched

- `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` - three sentences: `### B1` `**Cache storage.**`
  (L1), `### B2` column-append paragraph (DRY), `### B2` `**Resolver change required.**` (M2).
- `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` - nine edits: the anchor-keying
  link text and the claims-block definition in `## How to read this file` (M1); the
  `**Kept in the spec**` `lru_cache` bullet and the B2 move-pass fan-out sentence in
  `## Entries keyed to the spec` (L1, M2); `**On the label.**`'s "defines the modal one" ->
  "defines both" and `**On restraint.**`'s fan-out attribution (M1, M2); the heading entry's count
  sentence (M1); the B1 entry's *unchanged* list, its new *Changed* paragraph and its claims block
  (L1); the B2 entry's fan-out paragraph and its new *Alternative rejected* paragraph (M2, DRY).
- `docs/builder/bld-004-r2-spec_reconciliation.md` - `Status:` set to `planned`; this section
  appended. No prior entry edited.
- `docs/builder/worker-memory/worker-1.md` - memory entry (gitignored).

Nothing else was written. No package source, test, example, script, sibling spec, terms CSV,
`CHANGELOG.md`, `KANBAN*`, `docs/GLOSSARY.md`, `docs/TREE.md`, DB file, build plan, or
`bld-004-r1-rationale_move.md` was touched, and the four deleted `bld-003-*.md` files were **not**
restored (`### Fifth change`: the maintainer's call).

### Byte and line counts (measured as written, after the last edit)

| | lines | bytes |
|---|---|---|
| spec at HEAD (pre-R1 blob) | 359 | 33,928 |
| spec before R2 (post-R1) | 216 | 26,436 |
| spec after R2's perform pass | 236 | 35,834 |
| spec **after this pass** | 236 | **35,985** |
| this pass's spec delta | +0 | **+151** |
| rationale after R2's perform pass | 1,197 | 84,365 |
| rationale **after this pass** | 1,247 | **88,739** |
| this pass's rationale delta | +50 | **+4,374** |

`git diff --stat -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> **73 insertions /
196 deletions**, unchanged from the item's reading: all three spec edits are in-place rewrites of
lines the item had already rewritten, so no line was added or removed. **The rationale grew ~29x
more than the spec, which is the expected direction**: three sentences changed in the contract, and
the account of why each changed - including one re-derivation and two rejected alternatives - is
what a rationale file is for. Method: `wc -l -c` on the working files; the HEAD row from
`git show HEAD:<path>` into a scratch path outside the repo. No `git stash`, `git checkout`,
`git restore`, or `git worktree` anywhere in this pass.

### Validation run

Every command re-run after the last edit; nothing quoted from the item's or the review's readings.

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`
  -> `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0**,
  character-identical to the baseline.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-004-optimizer_beyond-0_0_3.md docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md docs/builder/bld-004-r2-spec_reconciliation.md`
  -> **exit 0**, all three.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` ->
  `OK: 49 done cards have glossary links.` **exit 0**. Read-only form only; the writing form was
  never invoked.
- **Anchor carriage, re-derived per anchor.** Each of the ten reference ids resolves to exactly
  **2** occurrences in the spec - one body link, one definition - so all ten remain single-carrier.
  `glossary-djangooptimizerextension` sits in the `### B1` `**Cache storage.**` sentence this pass
  rewrote and survived it; `glossary-fk-id-elision` and the `### B2` sites were untouched by the two
  B2 edits, both of which land after the anchor-bearing clauses.
- **Link resolution, both files, re-derived on disk this pass** with a parser that partitions each
  file at `<!-- LINK DEFINITIONS -->`, strips code spans before scanning uses, normalizes each
  target against the file's own directory, and checks each anchor against the target's real heading
  slugs: spec **11 defs / 11 used / 0 undefined / 0 unused**, rationale **23 / 23 / 0 / 0**,
  **34/34 targets exist and every anchored target's heading is present**. No definition was added or
  removed by this pass.
- **No inbound anchor breakage.** `grep -rln "spec-004-optimizer_beyond-0_0_3.md#" --include="*.md" .`
  -> three files, all this cycle's own: the rationale and the two `bld-004-*` artifacts (per-cycle
  scratchpads, and `bld-004-r1` is closed). No standing doc and no sibling spec links a spec-004
  heading anchor.
- **`AGENTS.md` rule 27:** `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` -> **no match** in either file.
- **Zero fenced code blocks:** a `grep -c` for a line-initial triple backtick returns **0** in the
  spec and **0** in the rationale.
- **The spec narrates no history.** Re-run with the review's own thirty-five-alternate pattern plus
  `did not survive`: **one** line, `:3`, R1's companion pointer, which describes the rationale
  file's contents and which H18 / H20 place off-limits.
- **The maintainer-ruled sentence is byte-identical to HEAD.** HEAD `:5` and working `:7` extracted
  read-only to a scratch path outside the repo: `md5` `a236d060acf135d69af06a01cf43646a` on both
  sides, `diff` empty.
- **Both do-not-reverse instructions re-verified after the edits.** H19: 10 line-initial modal
  blocks, 12 factual, plus R1's one scoped stronger label - unchanged, and the two new mentions of
  each label are inside the definitions that scope them. H20: five "The competitive argument for
  this slice" (`:41`, `:63`, `:81`, `:109`, `:139`), two "The opening argument for this slice"
  (`:119`, `:151`), B8 carrying neither - byte-identical, and no B2/B1 edit is inside one.
- No `pytest` (`AGENTS.md` rule 15; this cycle changes no code). No `ruff` (neither file is Python).
  No `--cov*` flag in any command.

### Working-tree state - reported, not reverted

Re-derived at the end of this pass. `HEAD` is **`346d67312599c0536980969caa39085ab3885ae8`**,
unchanged; `git log -1 --format=%h -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` still returns
**`20a9752f`**, so no concurrent commit swept this cycle's work - the hazard check done with
`git log`, never `git status` alone.

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
 M docs/SPECS/spec-005-django_type_contract-0_0_3.md
 D docs/builder/bld-003-final.md
 D docs/builder/bld-003-r1-rationale_move.md
 D docs/builder/bld-003-r2-spec_reconciliation.md
 D docs/builder/bld-003-r3-doc_completion_archive.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/bld-004-r2-spec_reconciliation.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
?? docs/builder/build-005-django_type_contract-0_0_3.md
```

**Two new entries since the review, both card 005's and both a concurrent session's**:
`?? docs/builder/build-005-django_type_contract-0_0_3.md` appeared partway through this pass and
`M docs/SPECS/spec-005-django_type_contract-0_0_3.md` between this pass's second-to-last and last
`git status`. A concurrent session has opened a build cycle for card 005. Neither is in any residual
item's writable set, nothing in this cycle reads either, and `docs/spec-068-graph_substrate-0_1_1.md`
- the plan's original baseline-dirty entry - has since cleared. Reported, not touched, nothing
reverted; Worker 0 appends both to `## Baseline-dirty out-of-scope files`. **R3 must re-derive this
reading rather than inherit it**: it moved twice inside one short pass.

The four `D docs/builder/bld-003-*.md` deletions persist, unchanged and **not restored** -
`### Fifth change` makes that the maintainer's call and `AGENTS.md` rule 34 bans the `git checkout`
that would do it. `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`, `CHANGELOG.md`,
`docs/GLOSSARY.md`, `docs/TREE.md`, `KANBAN.md`, and `KANBAN.html` are all **clean**.

### Notes for Worker 3

- **The three re-derivations to re-run first**, because they are where this pass could have repeated
  the item's failure: the `[spec-004-improvements]` population (21 occurrences = 20 body uses + 1
  definition; 3 code-span + 17 bare = 20), the sibling-citation count (23 across 9, spec-003 now x3
  and spec-033 now x6), and the block-label counts (10 modal + 12 factual + 1 scoped stronger).
  Each was written by running the grep and pasting the number, never the other order.
- **M2 and L1 were each fixed at more sites than the review named** (four and three), because both
  are shapes rather than sentences. If a further address exists it is most likely in the rationale's
  `## Entries keyed to the spec` half, which this pass read for those two shapes only.
- **The DRY finding was closed by cutting the spec, not by amending the record**, so the item's
  refusal 3 is now an accurate description of what the spec says. The judgement worth challenging
  is whether cutting the cost clause leaves B2 under-instructed; the argument that it does not is in
  the rationale's new *Alternative rejected* paragraph and rests on the requirement itself staying.
- **L2 is corrected in this section only.** The prior bullet is byte-identical by design. If the
  review convention wants the correction adjacent to the error, that is a Worker 0 / maintainer call
  about the never-edit-prior-entries rule, not something this pass may take.
- Nothing in `### The three claims this pass refused to make` was re-opened beyond L2's evidence
  clause, and refusals 1 and 3's conclusions are untouched.

### Notes for Worker 1 (spec reconciliation)

Items 1-5 of the item's own list and items 2-5 and 8-10 of the review's are carried forward
unchanged and are not restated here. Three additions:

1. **New out-of-scope file:** `docs/builder/build-005-django_type_contract-0_0_3.md` appeared
   untracked during this pass. Worker 0 appends it; no worker touches it.
2. **The `## How to read this file` claims-block definition now defines two block kinds.** If a
   future pass adds a third kind of closing block it must extend that bullet in the same edit - the
   defect M1 caught was a definition left behind by a label, and the definition is the index a
   reader consults first.
3. **`bld-004-r1-rationale_move.md` links a dead spec-004 anchor.** It records
   `#proposed-improvements` as resolving; that heading no longer exists. It is a closed per-cycle
   scratchpad, exempt from the symbol-path rule and regenerated by the next cycle, so it is left
   alone - recorded only so R3's cross-reference sweep does not read it as live rot.

---

## Review (Worker 3, pass 2)

Re-reviewed the working-tree diff against pristine `HEAD` (`346d67312599c0536980969caa39085ab3885ae8`,
re-derived this pass) extracted read-only with `git show HEAD:<path>` into a scratch path outside the
repository. No `git stash`, `git checkout`, `git restore`, or `git worktree` at any point.
`git log -1 --format=%h` over the spec still returns `20a9752f`, so no concurrent commit swept this
cycle's work.

**Every reported count re-derived exactly**, each re-run after the apply pass's last edit:
spec `wc -l -c` -> **236 / 35,985**; rationale -> **1,247 / 88,739**; `git diff --stat` over the spec
-> **73 insertions / 196 deletions**; HEAD blob -> **359 / 33,928**; sibling citations by occurrence
(`grep -o 'docs/SPECS/spec-0[0-9][0-9]' <spec> | sort | uniq -c`) -> **23 across 9** with the exact
per-spec breakdown claimed (spec-033 x6, spec-035 x6, spec-003 x3, spec-002 x2, spec-018 x2,
spec-023 / spec-029 / spec-032 / spec-047 x1); block labels -> **10** modal, **12** factual, **1**
scoped stronger. Given this cycle's history with counts, the two that did **not** reproduce are
filed as L3 below, and both are inside this artifact rather than in the spec or rationale.

### High:

None.

### Medium:

#### M3 — the plan-immutability enforcement is credited to `spec-035`, which contains none of it, and the sweep that declared the citation surface clean never covered that claim

`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md:35` (`### B1` `**Cache invalidation.**`) and `:169`
(`### B8` `**Cache-safety**`) both hand the enforcement to `spec-035`:

```docs/SPECS/spec-004-optimizer_beyond-0_0_3.md:169
The requirement is enforced structurally rather than left to discipline - a plan is finalized at
handoff, its directive lists become tuples so a later append raises, and a merge onto a finalized
plan is rejected outright - and `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` owns that
enforcement.
```

`spec-035` owns nothing of it. Re-derived three independent ways:

- **Text.** `grep -c immutab docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` -> **0**.
  `grep -n finalize` -> **4** hits, none a contract: `:14` (a Revision-2 note about the *spec* being
  finalized), `:197` (`plan.finalize()` named only inside a **rejected** alternative for the
  `only_fields` gate), `:247` and `:331` ("finalized definition metadata", G3's registry read).
  Nothing about tuple-swapping, `_assert_under_construction`, or post-handoff mutation.
- **Scope.** `spec-035`'s nine `### Decision` headings and its whole `## Slice checklist` cover G1
  (the `_result_cache` evaluated-queryset guard), G2 (operation-type gating of `.only()`), and G3
  (fragment type-condition narrowing). Its own terms CSV lists no plan-immutability term.
- **Chronology.** `git log -S"def finalize" -- django_strawberry_framework/optimizer/plans.py`
  returns one commit, `c7447e23` ("fix(optimizer): finalize plans and centralize metadata
  validation", **2026-05-11**) - a standalone hardening commit a month before `spec-035` was
  authored (its own Revision 2 is dated 2026-06-16). `::_assert_under_construction` came later still,
  in `991d5120` (2026-07-13, "isolate nested planning"). Neither is `spec-035`'s work.

Nor does any other spec own it: `spec-033:458` calls it "the finalize-to-tuple discipline" and
attributes it to the "**B1 cache-immutability property**" - i.e. back to spec-004 - and no file under
`docs/SPECS/` states the contract. The enforcement is un-spec'd, which is exactly the situation
`### The three claims this pass refused to make` bullet 1 already met and handled correctly for the
root-response-path cache-key component.

**This is M2's defect, in the same column of the same table.** The build plan's `D7` owner cell reads
"(`optimizer/plans.py::OptimizationPlan.finalize` + `::_assert_under_construction`, spec-035)" and
`D26`'s reads "spec-035 (plan immutability)". M2 was the drift table's D9 owner cell taken on trust;
this is D7's and D26's, taken on trust in the same way. `### M2 - the attribution, re-derived from
source, and swept` states "**Every** sibling citation in the spec was re-checked against the cited
document or against source ... **No further misattribution found.**" That universal is false: the
enumerated sweep lists `spec-029` D3, `spec-035` D5 / the projection gate, `spec-047`, `spec-033` D7
/ the union rule, `spec-018`, `spec-032`, `spec-023` - and stops. The two `spec-035` citations that
are *not* the projection gate or the loud fallback were never in it.

I re-checked the whole `spec-035` citation surface against the cited document, since that is the
column the sweep skipped. Four of the spec's six are sound - `:49` (projection gate, `spec-035`
Decision 4), `:57` and `:77` (the loud unsafe-elision fallback, Decision 5), `:167` (consumer-wins as
a permission-boundary stance, stated at `spec-035:104` / `:121` / `:136`). The two immutability ones
are not. The same claim propagates to the rationale at `:611`, `:813` ("`spec-035` (plan
immutability, ...)"), `:909`, and `:1160` - **six sites in total**.

**One further `spec-035` attribution of the same shape**, found while checking that column:
rationale `:387` credits the once-per-row resolver-key threading ("the strictness check accepts a
pre-threaded planned-key set and a precomputed resolver key as keyword-only arguments ... it belongs
to `spec-035`") to that spec too. `grep -n "precomputed\|pre-threaded\|once per row\|keyword-only"`
over `spec-035` -> **no match**, and `git log -S"precomputed_key" -- types/resolvers.py` returns
`1a1f8dc9` (2026-06-15, "Refactor permission checks to consolidate active permission targets"), not
a `spec-035` commit. Same column, same failure.

**Why it matters more than a stale word.** The pointer is doing work: the rationale's own
`:612` argues "a requirement whose enforcement lives in another document is still this document's
requirement", which is the licence for spec-004 not restating the enforcement. If the named document
carries nothing, the spec has exported a rule to a document that does not hold it, and a reader who
follows the pointer to confirm the enforcement finds a spec about three unrelated guards. Worse, a
future harmonizing sweep reading `**On restraint.**`'s list would go **edit `spec-035`** to make the
citation true.

**Recommended change.** Take refusal 1's own disposition - a citation that might be wrong is worse
than a bare true statement. The spec already states the enforcement in full at both sites, so drop
the `spec-035` clause and either leave it unattributed or name the enforcing symbols
(`optimizer/plans.py::OptimizationPlan.finalize` and `::_assert_under_construction`), which
`AGENTS.md` rule 27 permits and which `### B2` / `### B4` already do elsewhere in this spec. Correct
the four rationale sites and `:387` the same way, and record in the rationale that the attribution
came from the drift table's D7 / D26 owner cells rather than from `spec-035` - the same one sentence
M2's fix carries. `spec-003:30` makes the same attribution ("the frozen membership sets computed when
the plan is finalized at handoff ... belong to `spec-033` and `spec-035`"); it is a read-only sibling
this cycle, so it is recorded in `### Notes for Worker 1`, not fixed.

### Low:

#### L3 — two supporting counts inside `### L1` are wrong, both with the right conclusion

`### L1 - the false reason, replaced rather than deleted`, in this artifact:

- "`grep -n lru_cache <rationale>` now returns **6** lines, none asserting the false reason." Re-run
  after the last edit: `grep -n lru_cache <rationale> | wc -l` -> **11** (`:261`, `:264`, `:274`,
  `:914`, `:916`, `:917`, `:918`, `:920`, `:936`, `:950`, `:951`; `grep -o ... | wc -l` -> 11 too, so
  it is not a line-versus-occurrence artifact). I read all eleven: **the conclusion holds** - `:264`
  and `:914`-`:918` state the false reason only as a quotation being retracted, `:951` retracts it in
  a claims block, and none asserts it live.
- "the **ten** hits elsewhere in the package (`keyset.py`, `permissions.py`, `utils/relations.py`,
  `utils/permissions.py`)". `grep -rn lru_cache django_strawberry_framework/` over `.py` files ->
  **13** hits across **five** files; the missing one is `utils/strings.py:22`/`:30`
  (`@functools.lru_cache` over the snake-case memo). **The conclusion holds** - all thirteen are
  unrelated decorated module-level functions, and `optimizer/` still has **0**.

This is the shape the item's own L2 was filed for and the shape the apply pass's `### Notes for
Worker 3` promised was closed ("Each was written by running the grep and pasting the number, never
the other order") - true of the three re-derivations it named, not of these two. Filed Low, not
Medium, because both conclusions survive and the artifact is a per-cycle scratchpad.

**Recommended change.** Restate both as re-derived populations with their unit, or drop the numerals
and keep the qualitative claims, which are the load-bearing halves.

### DRY findings

- **The DRY finding from pass 1 is closed correctly, and closed on the right half.** The spec at
  `:49` now reads "It must run **ahead** of the elision short-circuit;
  `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` states that ordering invariant and
  what reversing it costs, and nothing enforces it but the order itself." I re-read
  `spec-003:70` in place: it carries the invariant, the full causal argument ("an elided branch
  returns without planning a join ... silently reintroduce the N+1 the elision exists to remove"),
  and the same closing clause. **Not one clause of that argument survives in spec-004** - the spec
  now points where it previously reproduced. `spec-002:6` #"each own the surface they added" is
  verified in place as the family rule and names spec-004 / spec-033 / spec-035 explicitly, so it is
  the right authority for the call; cutting the spec rather than amending the record was the correct
  half, because the record's refusal 3 described the *desired* state and the spec was what deviated.
  **B2 is not left under-instructed**: the requirement a B2 reader must act on - the append runs
  first - is stated imperatively, and only the cost of disobeying it moved one hop.
- **No new duplication introduced by this pass.** Three spec sentences changed in place, nine
  rationale edits, no new section, no new link definition, no reproduced sibling rule. I re-read
  M2's new spec sentence at `:55` against `spec-003:123` and `spec-033:282`: it names two owners in
  one clause and reproduces neither document's rule.
- **Examined and NOT flagged: the B1 / B8 double statement of plan immutability.** Untouched by this
  pass, as the report says. Still deliberate: `### B1` states why no invalidation is needed, `### B8`
  why the reconciliation must copy. (M3 is about the *citation* both carry, not the duplication.)
- **Examined and NOT flagged: `**On restraint.**`'s three-extension list.** It now correctly
  separates spec-033's nested-connection multiplication from spec-003's fan-out rule and records that
  two of B2's rules run out of the foundation rather than the extensions. Only its
  "plan immutability" item is wrong, and that is M3.
- No existence challenge to raise: this item creates no abstraction, helper, registry, or
  indirection layer.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty**. `__all__` and the re-export list
are unchanged. `git status --short -- django_strawberry_framework/ tests/ examples/ scripts/` ->
**empty**: no source, test, example, or script file changed, as `## Build-wide context flags`
requires. No correctness defect in shipped optimizer code was found by this pass either, so nothing
is escalated under that heading.

### CHANGELOG sanity

Not applicable; item did not modify `CHANGELOG.md`. Confirmed by `git status --short -- CHANGELOG.md`
-> empty.

### Documentation / release sanity

Applies - the diff is an archived spec and its rationale companion.

- **Version strings and card IDs.** No version or status line exists in the spec and none was added;
  `## Implementation checklist` still carries all eleven `- [x]`, matching `DONE-004-0.0.3`. No
  KANBAN card moved, no release metadata changed.
- **The archive is intact.** Spec at `docs/SPECS/`, companions at `docs/SPECS/appx/`.
  `spec-004-optimizer_beyond-0_0_3-terms.csv` is untouched (`git status --short docs/SPECS/appx/`
  reports only untracked rationale files; `git log -1` on the CSV returns `40e4754a`).
- **Every link definition resolves on disk, re-derived this pass** with my own parser (partitions at
  `<!-- LINK DEFINITIONS -->`, strips code spans before scanning uses, normalizes each target against
  the file's own directory, slugs every heading in each target and checks the anchor against that
  set): spec **11 defs / 11 used / 0 undefined / 0 unused**, rationale **23 / 23 / 0 / 0**,
  **34/34 targets exist and every anchored target's heading is present**. No definition was added or
  removed by this pass.
- **No inbound anchor breakage.** `grep -rln "spec-004-optimizer_beyond-0_0_3.md#" --include="*.md" .`
  hits only this cycle's own files. `## Proposed improvements` survives in the rationale at exactly
  **2** places (`:704`, `:865`) and **0** in the spec; I read both in place and both are correctly
  historical - `:704` sits under a list whose preamble at `:696`-`:699` scopes it ("the spec headings
  it names are the ones that existed when it was written"), and `:865` is a `*Changed - the heading
  was ...*` quotation of the prior heading inside the rename's own entry. Neither is a live pointer.
- **No obsolete staging wording.** `grep -c` in the spec: "Can be spec'd now" **0**, "when B4 ships"
  **0**, "Proposed improvements" **0**, "check_optimizer" **0**.
- **No script-rendered doc touched.** `docs/TREE.md`, `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`,
  `examples/fakeshop/db.sqlite3` all clean; no docstring feeds this change.
- **Verbatim-copy check** reduces to the maintainer-ruled sentence, verified below.

### Re-confirmed invariants — every one re-derived this pass, none quoted

| Check | Command | Result |
|---|---|---|
| Glossary terms | `check_spec_glossary.py --spec <spec>` | `OK: 10 terms - all have glossary entries and at least one spec link.` exit **0** |
| Layout / scaffold | `check_trailing_commas.py --check <spec> <rationale> <this artifact>` | exit **0**, all three |
| Card glossary chain | `manage.py import_spec_terms --check` (read-only form only) | `OK: 49 done cards have glossary links.` exit **0** |
| Fenced blocks | `grep -c '^```'` | **0** in spec, **0** in rationale |
| `AGENTS.md` rule 27 | `grep -nE '[a-zA-Z_/]+\.(py\|md):[0-9]+'` | **no match** in either file |
| Maintainer-ruled sentence | `diff` HEAD `:5` vs working `:7`; `md5` | identical, `a236d060acf135d69af06a01cf43646a` both sides, `diff` empty |
| Source / test / example / script | `git status --short -- django_strawberry_framework/ tests/ examples/ scripts/` | empty |

**The ten anchors, re-derived per anchor.** Each reference id resolves to exactly **2** occurrences
in the spec - one body use, one definition - so all ten remain single-carrier:
`configurationerror` `:105`, `djangooptimizerextension` `:33`, `djangotype` `:89`, `fk-id-elision`
`:13`, `metaexclude` + `metafields` together `:131`, `metaoptimizer-hints` on the `### B4` heading
`:87`, `only-projection` `:13`, `optimizerhint` `:89`, `queryset-diffing` on the `### B8` heading
`:157`. The one at genuine risk this pass was `djangooptimizerextension`: `:33` is the sentence L1
rewrote, and the link survives inside the clause that still binds the cache to the extension
*instance* - which is also the premise the replacement reason and the singleton-factory pointer both
rest on, so it is load-bearing rather than decorative. `check_spec_glossary` passing is necessary but
not sufficient (it accepts a link anywhere in the body), so each carrier was read in place.

**The spec narrates no history - re-run with my own alternation.** Twenty-nine alternates including
`this pass`, `drift`, `reconcil`, `deprecated`, `historical`, `initially`, `now reads`, `revised`.
Hits: `:3` (R1's companion pointer, which describes the *rationale file's* contents and which H18 /
H20 place off-limits) and `:159` / `:165` / `:167` / `:169` / `:187`, all of which are B8's own
domain word "reconciliation" describing the shipped mechanism, not the document's chronology. No
history narration.

**Both do-not-reverse instructions still hold, re-derived after this pass's edits.** H19: `grep -c`
line-initial labels -> **10** `**Claims the spec may no longer make.**`, **12** `**Claims the spec no
longer makes.**`, plus R1's one scoped stronger label at `:177`. Nothing levelled, and the two new
mentions of each label sit inside the `## How to read this file` definition that scopes them. H20:
five "The competitive argument for this slice" (`:41`, `:63`, `:81`, `:109`, `:139`), two "The
opening argument for this slice" (`:119`, `:151`), B8 carrying neither - unchanged, and none of the
three spec edits lands inside one.

### The five closures, graded

1. **M1 - closed, and closed on the population rather than the worklist.** The stale site is fixed:
   `## How to read this file`'s anchor-keying bullet now spells `` `## The eight improvements` ``
   (`:54`-`:55`). **Population re-derived independently**: `grep -o '\[spec-004-improvements\]'
   <rationale> | wc -l` -> **21** on **21** distinct lines, being **20** body uses plus the
   definition at `:1221`; `grep -o '\[The eight improvements\]\[spec-004-improvements\]' | wc -l` ->
   **17**; the remaining **3** are the wrapped/code-span form at `:54`-`:55`, `:125`, `:631`-`:632`.
   17 + 3 = 20. The parenthetical warning that a matching-line grep for the code-span form returns
   4 lines with `:861` being the entry's own `###` title also reproduces exactly. **The two survivors
   are genuinely historical**, both read in place - see `### Documentation / release sanity`. The
   claims-block definition now defines both kinds, names where each lives, points at
   `**On the label.**`, and repeats that neither spelling may be levelled; R1's handoff item 19 asked
   for exactly that and it is now satisfied.
2. **M2 - closed at four sites, and the extra reach is real.** Re-derived the ownership from source
   rather than from the review: `spec-003:123` states the rule in full ("a selection reachable under
   more than one response key carries one resolver identity per key, never a single identity for the
   merged node") and, in the same sentence's parenthetical, delegates only the nested-connection
   multiplication to `spec-033`; `grep -n "identity per key\|merged node\|response key"` over
   `spec-033` returns one resolver-identity statement (`:282`), about a connection field appending
   its own identities, not the merged-node fan-out. All four sites now read correctly - spec `:55`
   (two owners, one clause each, neither rule reproduced), rationale `:984`, `:348` (the move-pass
   entry), `:812`-`:815` (`**On restraint.**`, narrowed to "the nested-connection multiplication of
   the response-key fan-out" and carrying the new sentence that the fan-out and the FK-column
   ordering invariant both run out of the foundation). **The sweep beyond them is where this pass
   fell short - see M3.** Of the sweep's enumerated claims I verified every one and all are true:
   `spec-029:5` names Decision 3 as the singleton-factory ruling; `spec-035` Decision 4 is the
   operation-type `.only()` gate and Decision 5 the FK-id-elision loaded-check with the loud
   fallback; `resource_policy.py:60` really does `from .utils.context import clear_context_key,
   get_context_value, stash_on_context` and calls it at `:347` / `:349`; `spec-033` Decision 7 owns
   the pagination cache-key component and `extension.py::_stash_union` cites `spec-033` Decision 8
   for the union rule; `spec-018` owns several types over one model, `spec-032` the Relay interface
   work, `spec-023` multi-database routing. The sweep is sound on everything it covered.
3. **L1 - the replacement reason is true, verified against the interpreter and the source.**
   `lru_cache` on a class argument: `CacheInfo(hits=1, misses=1, maxsize=4, currsize=1)` on the
   project interpreter, so a model class is an ordinary hashable key and the old premise was false.
   The replacement's two halves both hold: `functools.lru_cache` decorates a *function* and has no
   per-instance form (the same paragraph's preceding clause requires instance binding, and
   `extension.py:859` really does `self._plan_cache: OrderedDict[...]` in `__init__`), and it evicts
   one entry per insertion where `extension.py:1173` drops `max(1, _MAX_PLAN_CACHE_SIZE // 4)` in one
   sweep against `_MAX_PLAN_CACHE_SIZE = 256`. `grep -rn lru_cache django_strawberry_framework/
   optimizer/` -> **0**. Keeping the conclusion and replacing the reason is the right call for the
   reason given: this is the paragraph a builder reaching for the decorator reads first. Fixed at all
   three sites; the two supporting counts around it are L3.
4. **L2 - the handling is correct.** `ARTIFACT.md` `## Re-pass sections` says "never edit prior
   entries" without carve-out, so leaving the bullet byte-identical and stating the correction in the
   appended section is the only compliant route, and the section says so explicitly. The corrected
   statement itself is accurate: I re-ran both greps - `spec-043` cites
   `conf.py::nested_connection_strategy_setting` at `:359`, `:570`, `:1329`, `:1731` (four, all as a
   naming precedent for its own settings key), `spec-051:466`-`:468` names
   `optimizer/lateral_fetch.py::build_lateral_sql` as a DRY-squeeze target at an unshipped `0.0.20`,
   `spec-033:261` mentions "strategy stamps" once in passing, and `docs/README.md:175`
   `## Nested connection indexing` exists and is the actual owner. Mentions-versus-owns is the right
   distinction and the spec's citation was correctly left alone.
5. **DRY - closed on the correct half.** Graded in `### DRY findings` above.

### What looks solid

- **Two of the three "found more sites than the finding named" claims are real reach, not padding.**
  M2's move-pass entry at `:348` and `**On restraint.**` at `:812` each carried the identical error a
  round earlier and neither was in my pass-1 finding; L1's `**Kept in the spec**` bullet at `:264`
  reproduced the false reason as a *bolded rule*, which would have outlived the spec fix. Both were
  found by reading for the shape rather than the sentence, which is the right technique - and it is
  the same technique that would have caught M3 had it been pointed at the `spec-035` column.
- **The record and the spec now agree where pass 1 found them disagreeing.** Refusal 3 said "pointed
  at, not restated" and the spec now points; the heading entry's count is now a population with its
  command; the claims-block definition now describes what the file actually contains. Each of the
  four internal-disagreement findings was closed by moving the *wrong* half, and in the DRY case the
  pass argued which half was wrong from `spec-002`'s family rule rather than defaulting to the
  cheaper edit.
- **The reconciliation itself was not reopened.** No drift-row disposition changed, no S-finding
  re-argued, `git diff --stat` unchanged at 73/196 because all three spec edits are in-place rewrites
  of lines the item had already rewritten, and the B1/B8 double statement I examined and cleared was
  left alone. That is the correct discipline for an apply-changes pass.
- **Sampled correctness against source, beyond the five findings, all clean.**
  `extension.py::DjangoOptimizerExtension.check_schema` is `@staticmethod` with signature
  `(schema: Any) -> list[str]`; `registry.py::TypeRegistry.iter_types` is
  `-> Iterator[tuple[type[models.Model], type]]` and its docstring carries the once-per-registered-
  type / dedupe-by-model contract the spec states; `plans.py::_MAX_PATH_DEPTH = 1024` bounds the
  `info.path` walk; `_context.py:29`-`:33` carries exactly the five `DST_OPTIMIZER_*` keys the spec
  describes as a family, with `dst_optimizer_plan` and `dst_optimizer_planned` spelled as B5 and B3
  state them; `extension.py::__init__` takes `strictness: str = "off"` positionally.
- **Three residues I deliberately did not file.** (a) `## Current state` still calls the optimizer
  "effective end-to-end", HEAD's own unfalsifiable wording - no reader takes a wrong action from it
  and pass 1 already recorded it. (b) `### B7`'s `**Test surface.**` keeps "Benchmark (optional)",
  which reads as unbuilt work but is marked optional and was never a delivery claim. (c) The
  rationale's `## How to read this file` bullet 8 still describes the extraction pass in the past
  tense while the reconciliation is complete - it is scoped to that pass by its own first three words
  and is accurate as history. Recorded so the next pass does not re-derive them and cannot read
  silence as an unexamined area.

### Temp test verification

No temp tests were created. `docs/builder/temp-tests/r2/` was not used and `docs/builder/temp-tests/`
is empty. This item changes no code and introduces no boundary, guard, gate, or rejection path, so
`BUILD.md` `### What needs a proof, and what does not` scopes it out of the failability-proof
mechanism and the mandatory re-run floor is legally empty. The one executable check this pass needed
- whether `functools.lru_cache` accepts a class object as a key - was run directly against the
project interpreter and is recorded under L1's grading. No `pytest` was run (`AGENTS.md` rule 15) and
no `--cov*` flag appears in any command in this pass.

### Working-tree churn observed during this review — reported, not reverted

Re-derived at the end of this pass rather than inherited, as the apply pass asked. `HEAD` is
`346d67312599c0536980969caa39085ab3885ae8`, unchanged. **Three entries are new since the apply pass's
closing reading**, all the card-005 / concurrent cycle's:

```
?? docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md
?? docs/SPECS/spec-063-structural_templates-0_1_6.md
?? docs/builder/bld-005-r1-rationale_move.md
```

The card-005 cycle has run its own R1 rationale move since the last reading, and a new untracked
`spec-063` appeared. **None is in this cycle's writable set, nothing here reads any of them, nothing
was touched.** Worker 0 appends all three to `## Baseline-dirty out-of-scope files`.

The four `D docs/builder/bld-003-*.md` deletions persist and were **not** restored - `### Fifth
change` makes that the maintainer's call and `AGENTS.md` rule 34 bans the `git checkout` that would
do it. `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`, `CHANGELOG.md`,
`docs/GLOSSARY.md`, `docs/TREE.md`, `KANBAN.md`, `KANBAN.html`, and `examples/fakeshop/db.sqlite3`
are all **clean**. The list has now moved in three consecutive passes; R3 must re-derive it.

### Notes for Worker 1 (spec reconciliation)

**This is the complete R3 handoff, re-issued in full. Nothing lives only in a closed section**, so
every item from the item's own list, from pass 1's review, and from the apply pass's notes is
restated here rather than cross-referenced; R3's dispatch is built from this list alone.

1. **One Medium and one Low are open and route to Worker 1**, not Worker 2 - `### Deviation 2`'s
   corollary makes the apply-changes pass Worker 1's and sets `Status: planned` again. M3 touches
   both the spec (2 sites) and the rationale (5 sites); L3 touches this artifact only. Neither needs
   maintainer context, so the `review-accepted`-with-escalation carve-out does not reach them.
2. **Deferred, for the final gate's `### Deferred work catalog`:** the `check_optimizer` management
   command and custom-resolver detection (D21 / S5) - named as B6 follow-up work eleven versions ago,
   never built, and **no card exists for either**. Dropped from the spec by the item and recorded in
   the rationale. `inspect_django_type` (`spec-029`) answers a different question and is explicitly
   not offered as a substitute. Re-verified this pass: `grep -c check_optimizer` -> 0 in the spec, and
   `management/commands/` ships `export_schema` and `inspect_django_type` only.
3. **Deferred:** the `_record_relation_access`-before-elision ordering invariant still has **no
   automated guard** in `walker.py::_plan_select_relation`. Adding one is a source change and out of
   scope for a documentation cycle. The spec now points at `spec-003` for both the rule and its cost,
   which after the DRY fix is the most a docs cycle can do.
4. **Deferred, sibling-spec staleness (1 of 2):**
   `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` calls `0.316.0` "the locked" Strawberry
   version; it is the **declared floor** (`pyproject.toml` #"strawberry-graphql>=0.316.0") and
   `uv.lock` resolves higher. This cycle's own rationale phrasing was corrected (H17); sibling specs
   are read-only here with no declared exception, so the two documents now disagree - the state R3 or
   a future spec-029 cycle inherits. R1's handoff item 17 asked that whoever tightens it decide for
   both documents at once.
5. **Deferred, sibling-spec staleness (2 of 2), and this one is new.**
   `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md:30` makes the same wrong
   attribution M3 catches - "the frozen membership sets computed when the plan is finalized at
   handoff ... belong to `docs/SPECS/spec-033-...md` and
   `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`" - and `spec-035` carries no plan-finalization
   contract at all (`grep -c immutab` -> 0). `spec-003` is read-only in this cycle, so it is
   recorded, not fixed. Whoever fixes M3 should decide for both documents rather than leave them
   disagreeing, exactly as item 4 asks for `spec-029`.
6. **Deferred:** three B7 test names in `tests/optimizer/test_field_meta.py`
   (`::test_optimizer_field_map_populated`, `::test_optimizer_field_map_contains_relations`,
   `::test_optimizer_field_map_respects_fields_filter`) still spell the retired
   `_optimizer_field_map`. Live code, carded on `TODO-ALPHA-052-0.1.0`, not this cycle's; no test file
   is writable here.
7. **For R3's durable-doc audit - the spec names nine sibling specs by path, as code spans, not
   reference-style links.** Twenty-three occurrences across spec-002, 003, 018, 023, 029, 032, 033,
   035, 047 (up from 21; M2's fix added two). This matches `spec-003`'s convention and spec-004's own
   pre-existing `## Problem statement` / `## Non-goals` style, keeps the link-definition block at 11
   entries, and is **not** a scaffold violation - `check_trailing_commas.py --check` passes on both
   files. R3's cross-reference sweep must not "fix" them into reference-style links.
8. **For R3:** the section heading `## Proposed improvements` no longer exists; it is
   `## The eight improvements`, anchor `#the-eight-improvements`. My own tree-wide
   `grep -rln "spec-004-optimizer_beyond-0_0_3.md#" --include="*.md" .` confirms **no external
   consumer** links a spec-004 heading anchor - the only hits are this cycle's own files. R3 re-runs
   its own sweep, but the answer at this hash is that the rename is externally safe. The two
   remaining old-spelling occurrences in the rationale (`:704`, `:865`) are both correctly historical
   and must not be "fixed".
9. **For R3:** `bld-004-r1-rationale_move.md` records `#proposed-improvements` as resolving; that
   heading no longer exists. It is a closed per-cycle scratchpad, exempt from the symbol-path rule
   and regenerated by the next cycle, so it is left alone - recorded only so R3's cross-reference
   sweep does not read it as live rot.
10. **For R3's re-derivation duties, with expiry noted.** My readings - 34/34 link targets resolve,
    `import_spec_terms --check` green, ten anchors single-carrier, `check_spec_glossary` green,
    `db.sqlite3` clean - are current at `346d6731` and **have an expiry**. R3 re-runs each itself,
    re-runs `import_spec_terms --check` **after** any further concurrent DB write, and attributes any
    dirty `db.sqlite3` by `iterdump()` set-difference rather than by file bytes.
11. **New out-of-scope files, for Worker 0's `## Baseline-dirty out-of-scope files`:**
    `docs/builder/build-005-django_type_contract-0_0_3.md`,
    `docs/SPECS/spec-005-django_type_contract-0_0_3.md` (modified),
    `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md`,
    `docs/builder/bld-005-r1-rationale_move.md`, and
    `docs/SPECS/spec-063-structural_templates-0_1_6.md`. Plus the four `D docs/builder/bld-003-*.md`
    deletions, which persist and are the maintainer's call per `### Fifth change`. R3 must not read
    `docs/builder/` or `docs/SPECS/` as clean.
12. **The `## How to read this file` claims-block definition now defines two block kinds.** A future
    pass adding a third kind of closing block must extend that bullet in the same edit - the defect
    M1 caught was a definition left behind by a label, and the definition is the index a reader
    consults first.
13. **No correctness defect in shipped optimizer code was found by either pass.** Everything traced
    this pass - `check_schema`, `iter_types`, `_MAX_PATH_DEPTH`, `_context.py`'s five keys,
    `__init__`'s `strictness`, `_plan_cache`'s bound and quarter eviction,
    `OptimizationPlan.finalize` / `::_assert_under_construction`, `stash_on_context`'s consumers -
    behaves as the reconciled spec states. Nothing is escalated to the maintainer under
    `## Build-wide context flags`' read-only-audit rule.

### Review outcome

`revision-needed`.

One Medium and one Low, neither addressed nor intentionally rejected; `worker-3.md`'s acceptance gate
requires every finding to be one or the other.

**Four of the five closures came back clean and the fifth came back partly clean.** M1, L1, L2 and
the DRY finding are fully closed, each on the correct half and each with its supporting evidence
re-derived rather than restated. M2's own four sites are closed and correct, and every claim in the
sweep it performed is true. What is not closed is the sweep's **universal**: "every sibling citation
was re-checked ... no further misattribution found" is false, and the column it skipped -
`spec-035`'s non-G1/G2/G3 citations - carries the same drift-table-inherited error M2 was filed for,
across six sites for plan immutability plus one for the key threading. That the extra reach was
genuine on M2 and L1 makes the gap sharper, not softer: the shape was being hunted, just not in the
one column where the same cell had already misled the pass once.

L3 is two counts inside this artifact whose conclusions both survive; it is filed rather than waived
because a supporting grep that does not reproduce is the defect this cycle has now met five times,
and because closing M3 requires a pass anyway.

Everything else re-derived exactly: 236 / 35,985 and 1,247 / 88,739, 73/196, 23 citations across 9
with the per-spec breakdown, 21 = 20 + 1 and 17 + 3 = 20, 10 + 12 + 1 labels, ten anchors at two
occurrences each with every carrier read in place, 11/11 and 23/23 link definitions with 34/34
targets and anchors resolving, zero fenced blocks, zero rule-27 violations, the maintainer-ruled
sentence byte-identical at `a236d060acf135d69af06a01cf43646a`, both do-not-reverse instructions
un-levelled, and no source, test, example, or script file changed.

Per `### Deviation 2`'s corollary this routes to **Worker 1**, which applies the corrections and sets
`Status: planned` again.

---

## Build report (Worker 1, apply-changes pass 2)

`### Deviation 2`'s corollary routes an R2 `revision-needed` to Worker 1, not Worker 2. This pass
applies Worker 3's pass-2 findings (M3, L3) and returns `Status: planned`, which Worker 0 reads as
"dispatch Worker 3" for this item. **Every prior section of this artifact is unedited** apart from
the `Status:` line, which is the field's own owner-updated value; L3's correction is stated here
rather than by rewriting the sentences it corrects.

Plan declarations, unchanged: ownership partition `none; sequential residual items`; hot-path
`none`; floor-verification scope `none`. No `--cov*` flag was used in any command.

### Findings disposition

Both are **fixed**. Neither was rejected. The reconciliation was not reopened: no drift-row
disposition changed, no S-finding was re-argued, M1 / M2 / L1 / L2 / the DRY finding were not
touched, and the two do-not-reverse instructions were re-verified rather than adjusted.

| Finding | Disposition | Sites edited |
|---|---|---|
| M3 (plan immutability credited to `spec-035`) | Fixed at all **seven** named sites, **plus four more the mandated whole-file provenance sweep turned up** | spec `### B1` `**Cache invalidation.**`, `### B6` `**Mechanism.**`, `### B8` prune paragraph, `### B8` `**Cache-safety**`; rationale B3 move-pass entry, B4 move-pass entry, B6 move-pass entry, B8 move-pass entry, `**On restraint.**`, B1 reconciliation entry, B6 reconciliation entry, B8 reconciliation entry (x2), plus three claims blocks and one new deferred item |
| L3 (two wrong supporting counts inside `### L1`) | Corrected **here**, not in place; both restated as re-derived populations with their commands | this section, `### L3 — the two counts, re-derived` below |

### M3 — the seven sites, and the sweep the last pass did not run

**Re-derived before anything was edited, three independent ways, none taken from the review.**

- `grep -c immutab docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` -> **0**.
- `grep -n finalize` over the same file -> **4** lines, none a contract: a Revision-2 note about the
  *spec* being finalized, one `plan.finalize()` mention inside a **rejected** alternative for the
  `only_fields` gate, and two "finalized definition metadata" reads in G3. Its nine `### Decision`
  headings (listed by `grep -n '^### Decision'`) cover spec naming, card scope, G1, G2, Decision 5's
  FK-id loaded-check, G3 x2, module locations, and the version cut. Nothing else.
- `git log -S"def finalize" -- django_strawberry_framework/optimizer/plans.py` -> one commit,
  `c7447e23` (**2026-05-11**); `git log -S"_assert_under_construction"` over the same file ->
  `991d5120` (**2026-07-13**). Both symbols exist at HEAD (`plans.py:256`, `plans.py:348`, on
  `class OptimizationPlan` at `:132`). Neither commit is `spec-035`'s, whose own Revision 2 is dated
  2026-06-16.
- `grep -rn "_assert_under_construction" docs/SPECS/` -> **no match** anywhere in the archive. No
  spec states the enforcement.

**What the spec now says, at both immutability sites.** The `spec-035` clause is gone; the two
enforcing symbols are named instead (`optimizer/plans.py::OptimizationPlan.finalize` and
`::_assert_under_construction` — `AGENTS.md` rule 27 form, and the same form `### B2` / `### B4`
already use), followed by "No sibling spec states that enforcement; it and the requirement are both
this slice's." That is refusal 1's own disposition applied to a second un-owned behaviour: a
citation that might be wrong is worse than a bare true statement, and here the true statement is
that the behaviour has no external owner.

**The four rationale sites** (`:611`, `:813`, `:909`, `:1160` as the review numbered them) and the
**seventh, `:387`**, are corrected the same way. `:387` credited the once-per-row resolver-key
threading to `spec-035`; `grep -nE "precomputed|pre-threaded|once per row|keyword-only|planned-key"`
over `spec-035` returns **no match**, and `git log -S"precomputed_key" -- .../types/resolvers.py`
returns `1a1f8dc9` (2026-06-15, a permission-consolidation commit). It is now stated without an
owner, with the re-derivation beside it.

The B1 reconciliation entry carries a new `*Changed*` paragraph holding the three-way re-derivation,
the rejected alternative (*leave the pointer and let a later pass make it true by editing
`spec-035`* — that inverts the family rule: the pointer would be the reason a document acquires a
contract it never chose), and the one sentence recording that **the attribution came from the build
plan's drift-table owner column** (rows D7, D26, D13), copied rather than re-derived. Three claims
blocks gained the retraction.

### The provenance sweep — every claim in both files, settled from source

The last pass's universal ("**Every** sibling citation ... **No further misattribution found**") was
false because its enumerated sweep stopped at seven claims. This pass enumerated the **population**
instead and settled each one, and states the enumeration so a reader can re-derive it rather than
trust it.

**Population, measured after the last edit and stated so a reader re-derives it rather than trusts
it.** Spec: `grep -c 'docs/SPECS/spec-0\|docs/README.md'` -> **16 lines**, carrying **22 citation
occurrences** — `grep -o 'docs/SPECS/spec-0[0-9][0-9]' | wc -l` -> **21** and
`grep -o 'docs/README.md' | wc -l` -> **1**. Rationale, counting reference-*uses* (the `][ref-id]`
form, so definitions do not inflate it): `][spec-0NN]` -> **54**, of which **1** is the self-
reference `[spec-004]`, leaving **53** sibling citations; plus `][docs-readme]` **3**,
`][spec-002-rationale]` / `][spec-003-rationale]` **3**, `][glossary]` **1** — **60 owner-naming
occurrences**. Every one was checked against the cited document's own text, and where the cited text
did not settle it, against `git log -S` over the symbol.

**Sound, and left alone** (cited document's own text quoted or grepped in each case):

- `spec-002` `:6` #"each own the surface they added" — the family rule, verbatim, and it names
  spec-004 / spec-033 / spec-035 explicitly.
- `spec-002` + `spec-003` own O1-O6: `spec-002:58` "O1 through O6 have shipped"; `spec-003`'s title
  is "Optimizer O4 — Nested Prefetch Chains". Both rationale companions exist on disk and
  `spec-002`'s carries `## Whole-document scope — why the optimizer became its own document`, which
  is what spec `:3` points at.
- `spec-003` the fan-out rule (`:123`, states it in full and delegates only the nested-connection
  multiplication to spec-033) and the ordering invariant (`:70`, "must stay **ahead** of this
  short-circuit ... Nothing enforces the order but the order itself").
- `spec-018` — title is "Multiple `DjangoType`s per model with `Meta.primary`".
- `spec-023` — title "Multi-database cooperation contract", and its Revision 1 names
  `types/resolvers.py::_build_fk_id_stub` #"state.db = router.db_for_read" as the cooperation.
- `spec-029` Decision 3 — heading `### Decision 3 — Slice 1 adopts the singleton-factory
  `extensions=` form`; its `P1.1` names spec-004's lifecycle model stale by name;
  `inspect_django_type` is in its title.
- `spec-033` Decision 7 (`### Decision 7 — Plan-cache key hygiene: nested pagination variables hash,
  root pagination arguments do not`), Decision 4 (the package-reserved `to_attr` window), Decision 5
  (the per-parent fallback), Decision 8 (the union rule — and `extension.py:1196` / `:1231` cite
  "spec-033 Decision 8" in source).
- `spec-035` Decision 4 (the operation-type `enable_only` projection gate, named in its Revision 4
  and its Slice-2 checklist) and Decision 5 (the FK-id-elision loaded-check and loud fallback).
- `spec-047` — title "Execution resource policy"; `:99`, `:360`, `:744`, `:760` all state that the
  shape-agnostic context dispatch lifted to `utils/context.py` and that it is the only one.
- `spec-016` — title "`FieldMeta` single-source-of-truth consolidation and mirror retirement";
  `:39` names `cls._optimizer_field_map` and `cls._optimizer_hints` as the retired mirrors.
- `docs/README.md` `## Nested connection indexing` exists at `:175` and documents
  `OptimizerHint.strategy(...)`; `docs/README.md:53` and `docs/GLOSSARY.md:723` both carry the
  module-level-singleton-wrapped-in-a-factory form.

**Not sound — four further misattributions, all the same shape as M3, all fixed:**

1. **`OptimizerHint.strategy` credited to `spec-033`** (rationale B4 move-pass entry). `grep -c
   strategy` over `spec-033` -> **1**, and that one line (`:261`) mentions "strategy stamps" in
   passing inside a finalization bullet. `git log -S"def strategy" --
   django_strawberry_framework/optimizer/hints.py` -> `41008e4c` (**2026-07-17**), and the fetch-
   strategy backend itself is `57cbd32a` (2026-07-07) — both long after `spec-033` shipped at
   `0.0.9`. This also **contradicted the file's own refusal 2 and the spec's own citation**, which
   both name `docs/README.md`. Now states that no `docs/SPECS/` spec owns the seam and points at the
   same document the spec does.
2. **The ancestry-aware prefetch absorption credited to `spec-033`** (spec `### B8` prune paragraph,
   rationale B8 reconciliation entry). `grep -o subtree` over `spec-033` -> **0 occurrences**.
   `git log -S"def diff_plan_for_queryset" -- optimizer/plans.py` -> `5d92272f` (**2026-05-04**), and
   the absorption/ancestry logic is `ee469cbb` + `411b2187` (both 2026-05-04) and
   `git log -S"_prefetch_lookup_paths"` -> `8e17fd6e` (2026-05-01) / `ee469cbb`. `Release 0.0.3` is
   `2c5bfaae`, **2026-05-05** — the day after. This is **B8's own work, shipped with this card**;
   spec-004 was exporting its own surface to a sibling. Both sites now claim it.
3. **Consumer-wins precedence: "`spec-035` owns it"** (spec `### B8` prune paragraph).
   `spec-035:104` / `:121` / `:136` / `:423` all attribute the drop itself to
   "`spec-004` B8" and only *characterize* it as a permission-boundary stance / deliberate
   non-adoption. "Owns" is this spec's surface-ownership verb, so the sentence handed away a
   precedence spec-035 explicitly credits back. Narrowed to "records that stance", which is what
   spec-035's own text supports. The two rationale spellings (`records as such`, and a bare pointer)
   were already correct and were left alone.
4. **"Relay interfaces belong to `spec-032`"** (spec `### B6` `**Mechanism.**`, rationale B6
   move-pass and reconciliation entries). `spec-032:9` names
   `spec-015-relay_interfaces-0_0_5.md` as "the Relay Node integration foundation ... and the
   `Meta.interfaces` validation **this card's diagnostics extend**"; `spec-015`'s own title is
   "Relay Interfaces and Node Foundation" and it carries **27** `Meta.interfaces` mentions against
   spec-032's 16. Separately, the descent arm itself predates spec-032:
   `git log -S"get_implementations" -- optimizer/extension.py` and `git log -S"GraphQLInterfaceType"`
   over the same file both return `f83bb71b` (**2026-05-20**), a hardening commit in the `0.0.5`/
   `0.0.6` window. The spec now names spec-015's foundation and spec-032 as its later extension; the
   rationale additionally records that the reach itself has no spec owner. One new link definition
   (`[spec-015]`) was added to the rationale for the reference-style citations.

**Nothing else in either file makes a provenance claim.** The population above is the enumeration;
this pass makes no universal that is not backed by it.

### L3 — the two counts, re-derived

`### L1 — the false reason, replaced rather than deleted` is **left byte-identical** — `ARTIFACT.md`
`## Re-pass sections` forbids editing a prior entry, so the corrections are stated here. Its
conclusions are untouched and both survive; only the numerals were wrong.

- **"`grep -n lru_cache <rationale>` now returns 6 lines" was wrong.** Re-derived after this pass's
  last edit: `grep -c lru_cache <rationale>` -> **11** lines and `grep -o lru_cache <rationale> |
  wc -l` -> **11** occurrences, so it is 11 either way and not a line-versus-occurrence artifact
  (line numbers `:261 :264 :274 :926 :928 :929 :930 :932 :948 :979 :980`, which have shifted from
  Worker 3's reading because this pass added lines above them). The load-bearing half stands: none
  asserts the false reason live — the `**Kept in the spec**` bullet and the B1 reconciliation
  entry's *Changed* paragraph quote it as a retraction, and the claims block retracts it.
- **"the ten hits elsewhere in the package (four files)" was wrong.** `grep -rn lru_cache
  --include="*.py" django_strawberry_framework/ | wc -l` -> **13** hits, and `grep -rl` -> **5**
  files: `keyset.py`, `permissions.py`, `utils/permissions.py`, `utils/relations.py`, and
  `utils/strings.py` (the one the original missed). The load-bearing half stands: all thirteen are
  unrelated module-level decorated functions, and `grep -rn lru_cache --include="*.py"
  django_strawberry_framework/optimizer/ | wc -l` -> **0**, which is the fact the argument rests on.

Both numbers above were produced by running the command and pasting its output, then re-run after
the last edit in `### Validation run` below. The generalizable form: **a count of "hits in a
directory" must state the include filter and the tool's own output, because a `grep -rn` with no
filter also reads shadow files, artifacts, and caches.**

### Spec changes made (Worker 1 only)

Four, all in `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`, all in-place rewrites of sentences R2
had already rewritten, so the file's line count and `git diff --stat` are unchanged. Line numbers
are pin-at-write-time against the current 236-line file. Triggered by R2's pass-2 review and by the
provenance sweep it mandated, not by a new slice.

1. **`### B1` `**Cache invalidation.**` (spec:35)** — dropped the `spec-035` clause; named
   `optimizer/plans.py::OptimizationPlan.finalize` and `::_assert_under_construction` and stated
   that no sibling spec owns the enforcement. Reason: M3 — `spec-035` contains none of it.
2. **`### B6` `**Mechanism.**` (spec:129)** — "Relay interfaces belong to `spec-032`" replaced by
   spec-015's foundation plus spec-032 as its extension. Reason: spec-032's own predecessors line
   defers the foundation to spec-015, and the descent arm predates spec-032 by a release train.
3. **`### B8` prune paragraph (spec:167)** — "`spec-035` owns it" narrowed to "records that stance";
   the subtree-aware reconciliation reclaimed from `spec-033` as this slice's own. Reason:
   spec-035:104 credits the drop back to spec-004 B8, and the absorption shipped the day before
   `0.0.3`.
4. **`### B8` `**Cache-safety**` (spec:169)** — same correction as (1). Reason: M3.

No other spec sentence was touched; the maintainer-ruled `## Problem statement` sentence is proved
byte-identical to HEAD below.

### Files touched

- `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` — four sentences, listed above.
- `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` — eleven edits: the B3, B4, B6 and
  B8 move-pass entries (M3's `:387`, misattribution 1, misattribution 4, misattribution 2);
  `**On restraint.**`'s extension list (M3 plus the reclaimed items); the B1 reconciliation entry
  (one rewritten clause plus one new `*Changed*` paragraph carrying the re-derivation and the
  rejected alternative); the B6 and B8 reconciliation entries; three claims blocks (B1, B6, B8); one
  new bullet under `### What this pass deliberately left for others` for the read-only `spec-003`
  sibling; and one new link definition, `[spec-015]`.
- `docs/builder/bld-004-r2-spec_reconciliation.md` — `Status:` set to `planned`; this section
  appended. No prior entry edited.
- `docs/builder/worker-memory/worker-1.md` — memory entry (gitignored).

Nothing else was written. No package source, test, example, script, sibling spec, terms CSV,
`CHANGELOG.md`, `KANBAN*`, `docs/GLOSSARY.md`, `docs/TREE.md`, DB file, build plan, or
`bld-004-r1-rationale_move.md` was touched; the four deleted `bld-003-*.md` files were **not**
restored; and `spec-003:30` was **not** edited — it is recorded as a deferred item in the rationale
and in `### Notes for Worker 1` below.

### Byte and line counts (measured as written, after the last edit)

| | lines | bytes |
|---|---|---|
| spec at HEAD (pre-R1 blob) | 359 | 33,928 |
| spec before R2 (post-R1) | 216 | 26,436 |
| spec after R2's perform pass | 236 | 35,834 |
| spec after apply-changes pass 1 | 236 | 35,985 |
| spec **after this pass** | 236 | **36,223** |
| this pass's spec delta | +0 | **+238** |
| rationale after apply-changes pass 1 | 1,247 | 88,739 |
| rationale **after this pass** | 1,286 | **92,426** |
| this pass's rationale delta | +39 | **+3,687** |

`git diff --stat -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> **73 insertions /
196 deletions**, unchanged: all four spec edits are in-place rewrites of lines earlier passes had
already rewritten, so no line was added or removed. Method: `wc -l -c` on the working files; the
HEAD row from `git show HEAD:<path>` into a scratch path outside the repo (`wc -l -c` on that blob
-> **359 / 33,928**, reproduced). No `git stash`, `git checkout`, `git restore`, or `git worktree`
anywhere in this pass.

### Validation run

Every command re-run after the last edit; nothing quoted from an earlier reading.

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`
  -> `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0**,
  character-identical to the baseline.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-004-optimizer_beyond-0_0_3.md docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md docs/builder/bld-004-r2-spec_reconciliation.md`
  -> **exit 0**, all three.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` ->
  `OK: 49 done cards have glossary links.` **exit 0**. Read-only form only; the writing form was
  never invoked. Re-run **after** the concurrent session's `db.sqlite3` write landed (see
  `### Working-tree state` below).
- **Anchor carriage, re-derived per anchor, all ten at exactly 2.** Counted as
  `grep -o "glossary-<anchor>]" <spec> | wc -l` per id — one body use plus one definition:
  `configurationerror` 2, `djangooptimizerextension` 2, `djangotype` 2, `fk-id-elision` 2,
  `metaexclude` 2, `metafields` 2, `metaoptimizer-hints` 2, `only-projection` 2, `optimizerhint` 2,
  `queryset-diffing` 2. All ten remain single-carrier. None of this pass's four spec edits lands in
  an anchor-bearing clause: `### B1`'s carrier is `**Cache storage.**` (`:33`) and this pass edited
  `**Cache invalidation.**` (`:35`); `queryset-diffing` sits on the `### B8` heading (`:157`),
  paragraphs above both B8 edits; and `### B6`'s `metafields` / `metaexclude` pair sits at `:131`,
  two lines *below* the `**Mechanism.**` paragraph edited at `:129`, whose edit is confined to that
  paragraph's closing sentence. Each carrier was re-read in place, not inferred from the count.
- **Link resolution, both files, re-derived on disk this pass** with a parser that partitions each
  file at `<!-- LINK DEFINITIONS -->`, strips code spans before scanning uses, normalizes each
  target against the file's own directory, and slugs every heading in each target to check the
  anchor: spec **11 defs / 11 used / 0 undefined / 0 unused**, rationale **24 / 24 / 0 / 0**,
  **35/35 targets exist and every anchored target's heading is present**. The rationale gained
  exactly one definition this pass (`[spec-015]` -> `../spec-015-relay_interfaces-0_0_5.md`, which
  exists), which is the whole of the 23 -> 24 move.
- **Sibling-citation count re-measured after the last edit**, by occurrence
  (`grep -o 'docs/SPECS/spec-0[0-9][0-9]' <spec> | sort | uniq -c`): **21 occurrences across 10
  distinct siblings**, down from 23 across 9 — spec-033 x5 (was 6), spec-035 x4 (was 6), spec-003
  x3, spec-002 x2, spec-018 x2, and spec-015 / spec-023 / spec-029 / spec-032 / spec-047 x1 each.
  The two spec-035 losses are M3's; the spec-033 loss is misattribution 2; spec-015 is new from
  misattribution 4.
- **`AGENTS.md` rule 27:** `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` -> **no match** in either file.
  The two symbols this pass added to the spec are written `optimizer/plans.py::OptimizationPlan.finalize`
  and `::_assert_under_construction`, the sanctioned form, and both resolve at HEAD
  (`plans.py` `class OptimizationPlan` `:132`, `def finalize` `:256`,
  `def _assert_under_construction` `:348`).
- **Zero fenced code blocks:** `grep -c '^```'` -> **0** in the spec and **0** in the rationale.
- **The spec narrates no history.** Re-run with a 26-alternate pattern including `un-spec`,
  `re-derived`, `this pass`, `drift`, `superseded`, `historical`, `initially`, `now reads`: **one**
  line, `:3`, R1's companion pointer, which describes the *rationale file's* contents and which
  H18 / H20 place off-limits. `reconcil` was checked separately and its five hits (`:159`, `:165`,
  `:169`, `:187`, and `:167`) are all B8's own domain word for the shipped mechanism.
- **The maintainer-ruled sentence is byte-identical to HEAD.** HEAD `:5` and working `:7` extracted
  read-only to a scratch path outside the repo: `diff` **empty**, `md5`
  `a236d060acf135d69af06a01cf43646a` on both sides.
- **Both do-not-reverse instructions re-verified after the edits.** H19: `grep -c` on line-initial
  labels -> **10** `**Claims the spec may no longer make.**`, **12** `**Claims the spec no longer
  makes.**`, plus R1's **1** deliberately-scoped stronger label. Unchanged — this pass appended
  sentences to three existing factual blocks and created none. H20: five "The competitive argument
  for this slice" (spec `:41`, `:63`, `:81`, `:109`, `:139`), two "The opening argument for this
  slice" (`:119`, `:151`), B8 carrying neither. Byte-identical, and none of the four spec edits
  lands inside one.
- No `pytest` (`AGENTS.md` rule 15; this cycle changes no code). No `ruff` (neither file is Python).
  No `--cov*` flag in any command.

### Working-tree state — reported, not reverted

**`HEAD` MOVED during this pass, and the standing hazard check is what says this cycle survived it.**
`HEAD` is now **`ff03c1372365edcad488ff4671389d88ae145276`** — `ff03c137`, 2026-08-08,
"docs(kanban),docs(specs): card the structural-templates and sidecar-batching foundation" — where
every prior section of this artifact read `346d6731`. **It did not sweep this cycle's work**:
`git log -1 --format=%h -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` still returns
**`20a9752f`**, and `git show --stat --format="" HEAD | grep -E 'spec-004|bld-004|build-004'`
returns **empty**. The check was done with `git log` and `git show`, never `git status` alone.

Everything that mattered was re-derived *after* the commit landed, not carried across it:
`git show HEAD:<spec>` into a scratch path outside the repo still gives **359 / 33,928**, and the
maintainer-ruled sentence still `diff`s empty at `md5` `a236d060acf135d69af06a01cf43646a`;
`git diff --stat` over the spec is still **73 / 196**; `import_spec_terms --check` was re-run after
the commit and still returns `OK: 49 done cards have glossary links.`

**Mid-pass the dirty list carried eleven entries that `ff03c137` has now absorbed** — `BACKLOG.md`,
`KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`,
`multi-root-schedule-graph-reproduction.md`, `docs/SPECS/spec-041-channels_router-0_0_14.md`,
`spec-042-debug_toolbar-0_0_14.md`, `spec-043-test_client-0_0_14.md`,
`spec-052-beta_release-0_1_0.md`, `spec-053-graph_substrate-0_1_1.md`, and the untracked
`spec-063-structural_templates-0_1_6-terms.csv`. The DB-backed trio being in there means a
concurrent kanban/glossary write ran and committed inside this pass. **Nothing was touched and
nothing was reverted** (`AGENTS.md` rule 34); they are recorded because the plan's baseline-dirty
list should note that this class of churn appeared and cleared, not because any of it is actionable.

The list as it stands at the end of this pass:

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
 M docs/SPECS/spec-005-django_type_contract-0_0_3.md
 D docs/builder/bld-003-final.md
 D docs/builder/bld-003-r1-rationale_move.md
 D docs/builder/bld-003-r2-spec_reconciliation.md
 D docs/builder/bld-003-r3-doc_completion_archive.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/bld-004-r2-spec_reconciliation.md
?? docs/builder/bld-005-r1-rationale_move.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
?? docs/builder/build-005-django_type_contract-0_0_3.md
```

**R3 must re-derive this list and the `HEAD` hash, not inherit either.** The list has now moved in
four consecutive passes and `HEAD` moved inside this one; a reading taken from an artifact is a
reading about a tree that no longer exists. Re-run `import_spec_terms --check` after any further
`db.sqlite3` write, and attribute a dirty DB by `iterdump()` set-difference rather than by file
bytes.

The four `D docs/builder/bld-003-*.md` deletions persist and were **not** restored — `### Fifth
change` makes that the maintainer's call and `AGENTS.md` rule 34 bans the `git checkout` that would
do it. `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`, `CHANGELOG.md`,
`docs/GLOSSARY.md`, and `docs/TREE.md` are all **clean** —
`git status --short -- django_strawberry_framework/ tests/ scripts/ CHANGELOG.md docs/GLOSSARY.md docs/TREE.md`
returns empty.

### Notes for Worker 3

- **The claim to attack first is this pass's own enumeration.** I replaced a false universal with a
  stated population: 24 provenance claims on 18 spec lines, 55 citation occurrences in the
  rationale. If that population is wrong, every "sound, left alone" line above inherits the error —
  which is exactly how M3 happened. Re-derive the population before re-deriving any member of it.
- **Four misattributions beyond M3's seven.** Two of them (the ancestry-aware absorption, and
  consumer-wins) had the spec **exporting its own surface to a sibling**, which is the mirror image
  of over-absorption and which no prior pass looked for. If a further one exists, the place to hunt
  is any sentence where spec-004 names a sibling for something that shipped at `0.0.3` — the
  release date is `2c5bfaae`, 2026-05-05, and `git log -S` over the symbol against that date is the
  whole test.
- **The `spec-015` citation is new vocabulary and a new link definition.** It is the only addition
  to either file's citation surface; verify the definition resolves and that spec-015 really is the
  interface foundation rather than my having swapped one guess for another. `spec-032:9`'s
  predecessors sentence is the evidence I used.
- **L3 is corrected in this section only.** The prior `### L1` bullet is byte-identical by design
  (`ARTIFACT.md` `## Re-pass sections`). If the convention wants corrections adjacent to their
  errors, that is a Worker 0 / maintainer call about the never-edit-prior-entries rule.
- **Nothing outside M3, L3, and the mandated sweep was touched.** M1, M2, L1, L2 and the DRY finding
  are closed and were not re-opened; the B1 / B8 double statement of plan immutability is still
  deliberate and still un-flagged, and this pass changed only the *citation* both carried.

### Notes for Worker 1 (spec reconciliation)

Items 2-6 and 8-13 of Worker 3's pass-2 list are carried forward unchanged and are not restated.
Four additions and one correction:

1. **`spec-003:30` carries the same wrong `spec-035` plan-immutability attribution and is a
   read-only sibling.** Recorded, not fixed, in both this artifact and the rationale's
   `### What this pass deliberately left for others`. **Deferred to R3 or the next spec author**,
   who should decide for both documents at once — the same shape as the `spec-029` "locked
   `0.316.0`" item. This is the item the dispatch explicitly asked be carried rather than actioned.
2. **The build plan's drift-table owner column has now produced four errors** (D17, D9, D7/D26,
   D13). Worker 0's `**CORRECTION (2026-08-08)**` already records three and states the standing
   remedy — treat an owner cell as a hypothesis and settle it with `git log -S`. This pass applied
   that remedy to the whole citation surface, not just the flagged cells, and it found four more
   misattributions the table never named. **The table is not the population**; the two files are.
3. **Two behaviours in this spec now have no owner anywhere, deliberately.** The plan-immutability
   enforcement and the once-per-row resolver-key threading are both stated with their symbols and
   no citation. If a future spec claims either, spec-004's sentences are the ones to update — and
   `spec-033` #"the B1 cache-immutability property" is the only cross-reference that touches the
   first, and it points *back* at spec-004.
4. **`HEAD` moved inside this pass, to `ff03c137`, and absorbed eleven dirty entries** (the
   DB-backed `KANBAN.md` / `KANBAN.html` / `db.sqlite3` trio, `BACKLOG.md`, five `docs/SPECS/`
   siblings, the `spec-063` terms CSV, and a root `multi-root-schedule-graph-reproduction.md`).
   It did not touch spec-004 or any `bld-004` / `build-004` file, proved with `git log -1` and
   `git show --stat`. Worker 0 should record the hash change on the plan; the standing lesson is
   that **a plan's baseline-dirty list is a snapshot, and this cycle has now watched it move four
   times and watched `HEAD` move under it once.**
5. **Correction to the record, not a new item.** Worker 3's pass-2 note 7 states the spec names
   "nine sibling specs ... twenty-three occurrences". After this pass it is **ten siblings across
   twenty-one occurrences** (spec-015 added, two spec-035 and one spec-033 removed). The convention
   is unchanged: code-span paths, not reference-style links, and the link-definition block stays at
   11 entries. R3's cross-reference sweep must still not "fix" them into reference-style links.

---

## Review (Worker 3, pass 3)

Re-reviewed the working-tree diff against pristine `HEAD`, re-derived this pass as
**`ff03c1372365edcad488ff4671389d88ae145276`** (`ff03c137`) — it moved during the apply pass, as
that pass reported, and it has not moved since. The HEAD blob was extracted read-only with
`git show HEAD:<path>` into a scratch path outside the repository. No `git stash`, `git checkout`,
`git restore`, or `git worktree` at any point. **The commit did not sweep this cycle's work**:
`git log -1 --format=%h -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` still returns `20a9752f`
and all four `bld-004` / `build-004` paths are still untracked.

**Every reported figure re-derived exactly**, each re-run after the apply pass's last edit: spec
`wc -l -c` -> **236 / 36,223**; rationale -> **1,286 / 92,426**; `git diff --stat` over the spec ->
**73 insertions / 196 deletions**; HEAD blob -> **359 / 33,928**; sibling citations by occurrence ->
**21 across 10 siblings** with the exact per-spec breakdown claimed (spec-033 x5, spec-035 x4,
spec-003 x3, spec-002 x2, spec-018 x2, spec-015 / spec-023 / spec-029 / spec-032 / spec-047 x1);
`[spec-004-improvements]` -> **21** = 20 body + 1 definition, **17** bare form; block labels ->
**10** modal, **12** factual, **1** scoped stronger; link definitions -> spec **11/11**, rationale
**24/24**, **35/35** targets and every anchor resolving. **L3's two corrected counts reproduce**:
`grep -c lru_cache` over the rationale -> **11** (and `grep -o | wc -l` -> 11, so not a
line-versus-occurrence artifact, at exactly the eleven line numbers listed); `grep -rn lru_cache
--include="*.py" django_strawberry_framework/` -> **13** hits across **5** files (`keyset.py`,
`permissions.py`, `utils/permissions.py`, `utils/relations.py`, `utils/strings.py`), and
`optimizer/` -> **0**.

**All four new corrections are right, and each is right for the reason given** — graded against
source below, with `git log -S` as the instrument. The sweep's own stated population also
re-derives, in the section that states it. What does not re-derive is the population as restated in
`### Notes for Worker 3`, which is the number that section tells the reviewer to attack first.

### High:

None.

### Medium:

#### M4 — the provenance sweep's population is stated twice with different numbers, and the variant the pass points the reviewer at reproduces under no derivation

`### The provenance sweep — every claim in both files, settled from source` states the population
this way, with its commands:

```docs/builder/bld-004-r2-spec_reconciliation.md:1760
Spec: `grep -c 'docs/SPECS/spec-0\|docs/README.md'` -> **16 lines**, carrying **22 citation
occurrences** ... Rationale ... `][spec-0NN]` -> **54**, of which **1** is the self-reference
... leaving **53** ... plus `][docs-readme]` **3**, `][spec-002-rationale]` /
`][spec-003-rationale]` **3**, `][glossary]` **1** — **60 owner-naming occurrences**.
```

**Every one of those numbers re-derives exactly.** Spec: 16 lines, 21 + 1 = 22 occurrences.
Rationale: `grep -o '\]\[spec-0[0-9][0-9]\]' | wc -l` -> 54, `[spec-004]` self-ref 1,
`][docs-readme]` 3, `][spec-002-rationale]` 2 + `][spec-003-rationale]` 1, `][glossary]` 1;
53 + 3 + 3 + 1 = 60. Confirmed.

`### Notes for Worker 3`, first bullet, restates the same population as a *different* one:

```docs/builder/bld-004-r2-spec_reconciliation.md:2046
**The claim to attack first is this pass's own enumeration.** I replaced a false universal with a
stated population: 24 provenance claims on 18 spec lines, 55 citation occurrences in the
rationale. If that population is wrong, every "sound, left alone" line above inherits the error —
which is exactly how M3 happened. Re-derive the population before re-deriving any member of it.
```

**24 / 18 / 55 reproduces under no derivation I could construct, and no command is given for it.**
The widest honest spec reading is **17 lines / 23 occurrences** — the sweep's 16/22 plus one, the
bare-filename `` `spec-002-optimizer-0_0_2.md` `` at spec `:7`, which the sweep's own grep pattern
misses because it requires the `docs/SPECS/` prefix. There is no 18th line and no 24th occurrence.
For the rationale, 55 is reachable only as `54 + 1 glossary`, i.e. by dropping the six
`docs-readme` / rationale-file uses the sweep's own 60 includes. So the two numbers are not the
same measure taken twice; they are two different measures, one of which is unstated and
unreproducible.

**Why this is a defect rather than a slip.** This bullet is not incidental prose — it is the
pass's own instruction to its reviewer, and it says in terms that the whole "sound, left alone"
list inherits any error in it. A reviewer who follows the instruction re-derives 22 and 60,
gets neither 24 nor 55, and cannot tell whether two citations were missed, whether the sweep used
a wider pattern it did not record, or whether the number was simply written from memory. That is
precisely the ambiguity `BUILD.md` `## Claims are proven mechanically, never accepted on prose`
describes for a stated count, and this cycle has now met it six times. It matters more here than
anywhere else it has appeared, because a population is what replaced the false universal that
caused M3: a wrong denominator is how a survivor stays hidden.

The related half — `:7` sitting outside the stated pattern — is small but real, and it is why the
closing sentence "**Nothing else in either file makes a provenance claim.** The population above is
the enumeration" is not quite backed. `:7` does make a provenance claim (spec-002 owns O1-O6). It
happens to be **true and independently settled** in the sound list (`spec-002:58` "O1 through O6
have shipped", re-derived), and it sits inside the maintainer-ruled byte-identical sentence, so
nothing is owed to the spec. What is owed is that the enumeration say so.

**Recommended change.** Delete or correct the `24 / 18 / 55` restatement so one population stands,
and state it with the command that produces it. If the intent is the widest reading, it is
`grep -c 'spec-0[0-9][0-9]\|docs/README.md'` -> 17 lines / 23 occurrences, with one clause noting
that the 17th is the maintainer-ruled `:7` and is not editable. If the intent is the narrower one
already measured, keep 16 / 22 / 60 and add the one clause naming `:7` as the known exclusion, so
the "nothing else" sentence is backed rather than asserted.

#### M5 — the deferred `spec-003` misattribution names one site of a five-site class, and the companion rationale carries the three strongest

The durable record is correct as far as it goes, and it is durable — I confirmed the item lives in
the **rationale**, not only in this artifact:

```docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:1236
- **[`spec-003`][spec-003] makes the same plan-immutability misattribution this pass corrected
  here.** It hands the frozen membership sets computed at plan finalization to [`spec-033`][spec-033]
  and [`spec-035`][spec-035]; spec-035 carries no plan-finalization contract at all. Spec-003 is a
  read-only sibling in this cycle, so it is recorded rather than fixed — and whoever fixes it should
  decide for both documents at once, as the spec-029 item above asks.
```

`spec-003:30` is verified — it reads "the frozen membership sets computed when the plan is finalized
at handoff. Those belong to `docs/SPECS/spec-033-...md` and `docs/SPECS/spec-035-...md`". Correct,
recorded, and correctly not fixed.

**But `spec-003` is not one site.** `grep -rln 'finalized at handoff' docs/SPECS/` returns four
files, and the fourth is `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md`,
which carries the identical attribution three more times — including the two strongest forms in the
family:

- `:521` — "[`spec-035`][spec-035] (**plan immutability**, the projection gate, the ...)" — the same
  list-item shape as spec-004's own `**On restraint.**` entry that this pass just corrected.
- `:603`-`:604` — "the frozen membership sets exist because the plan is finalized at handoff —
  decisions belonging to [`spec-033`][spec-033] and [`spec-035`][spec-035], each already stated once
  in its own document." The trailing clause is the load-bearing part: it asserts spec-035 **has**
  stated it, which is exactly what `grep -c immutab` -> 0 falsifies.
- `:855` — "discipline is [`spec-035`][spec-035]'s to state." The strongest form of all: not that
  spec-035 states it, but that spec-035 is the document that *ought* to. That is the sentence a
  future harmonizing sweep would act on by editing spec-035 — the exact failure mode M3's own
  rationale entry names when it rejects the alternative "let a later pass make it true by editing
  spec-035".

**Why it matters.** The deferred item's whole imperative is "whoever fixes it should decide for
both documents at once". A reader who follows that imperative opens `spec-003:30`, fixes one line,
and closes the item — leaving three live misattributions in the companion, one of which is a
standing instruction to write the contract into spec-035. The class is five sites (spec-003 `:30`
plus rationale `:521`, `:604`, `:855`, with `:598`'s bare `spec-033 / spec-035` pointer riding
along), and the record enumerates one. This is the same rule M3 was decided under and that this
pass applied correctly everywhere it had write access: when a finding fixes one instance of a
class, the pass owes the **class** — and where the sites are unfixable, the enumeration *is* the
deliverable.

**Recommended change.** Extend the rationale bullet (and the matching `### Notes for Worker 1`
item) to name the companion file and its three sites with the one-line evidence already in hand
(`grep -c immutab` over spec-035 -> 0; `git log -S"def finalize"` -> `c7447e23`, 2026-05-11, a
month before spec-035's Revision 2 of 2026-06-16). No sibling file is edited; only the enumeration
grows. Nothing else about the deferral changes.

### Low:

#### L4 — `### Notes for Worker 1` item 2 under-counts the drift table's owner-column errors as four when this pass's own findings make it eight

```docs/builder/bld-004-r2-spec_reconciliation.md:2077
2. **The build plan's drift-table owner column has now produced four errors** (D17, D9, D7/D26,
   D13).
```

The four new misattributions this pass found are all present in that same column, and the pass
does not connect them:

- **`OptimizerHint.strategy` -> spec-033** is `D15`'s owner cell verbatim: "spec-033 / spec-046".
- **Ancestry-aware absorption -> spec-033** and **consumer-wins -> spec-035 "owns"** are both
  `D25`'s: "spec-033 (subtree awareness) + spec-035 (the stance)".
- **Relay interfaces -> spec-032** is `D20`'s: "spec-032 (Relay interfaces)".

So the column has produced errors on at least **D9, D13, D15, D17, D20, D25, D26 and D7** — eight
rows, not four. The build plan's own `**CORRECTION (2026-08-08)**` says "This is the **third** error
found in this table"; after this pass it is the eighth, and the correction paragraph is what Worker 0
maintains as the table's reliability record.

**The conclusion is unaffected and I am filing this Low for that reason.** The standing remedy the
correction states — "treat an owner cell as a hypothesis and re-derive it; `git log -S` over the
symbol is the instrument that settles it" — is already right, is unchanged by the count, and this
pass applied it to the whole surface rather than to the flagged cells, which is the improvement that
matters. What is wrong is the number a later reader would use to calibrate how far to distrust the
table, in the one note whose job is to carry that calibration to Worker 0.

**Recommended change.** One clause: name D15, D20 and D25 alongside D7 / D9 / D13 / D17 / D26, or
drop the numeral and say "the column has now produced an error on every row this cycle re-derived",
which is the load-bearing claim and needs no arithmetic.

### DRY findings

- **Examined and NOT flagged: `### B1` `**Directive-variable extraction.**` restates
  `spec-033` Decision 7's cache-key-hygiene rule while pointing at something else.** This is the
  closest thing to a fifth misattribution I found, and I decided against filing it. The spec at
  `:29` states the two-family collection, the **non-root** qualifier, why nested pagination must key
  the cache ("bake into windowed prefetch querysets"), and why root pagination stays out ("root
  slicing happens after the plan is applied") — which is, clause for clause,
  `spec-033:343` `### Decision 7 — Plan-cache key hygiene: nested pagination variables hash, root
  pagination arguments do not` plus its first two sub-bullets. The pointer the sentence carries
  aims at the *windows* ("The nested-connection windows those values feed belong to `spec-033`"),
  not at the rule.

  Two prior passes cleared row D4, but both tested a narrower question ("does spec-004 describe a
  *window*?" — it does not). The reason I am recording rather than filing is the standard the pass-1
  DRY finding established and this cycle already applied: the **requirement** a section's reader must
  act on stays, and only the **cost argument** moves one hop. Which variables key B1's cache is B1's
  own contract — a reader of B1 who does not know the second family builds the wrong key — where
  B2's ordering invariant was spec-003's rule that B2 merely consumes. The two causal clauses are
  the arguable half, and they are one sentence, not a transplanted paragraph. Recorded with its
  evidence so the next pass neither re-derives it nor mistakes silence for an unexamined area.

- **Examined and NOT flagged: the two immutability sentences are now byte-identical across `### B1`
  and `### B8`.** Both `:35` and `:169` close with "No sibling spec states that enforcement; it and
  the requirement are both this slice's." — the same sixteen words in two sections. Before this pass
  they carried two different spec-035 phrasings, so the duplication is new. I re-read both in place
  and the standing disposition still holds: `### B1` states *why no invalidation is needed* and
  `### B8` *why the reconciliation must copy*, and neither is derivable from the other. A repeated
  **negative** claim is also the low-risk direction — if a sibling ever does claim the enforcement,
  both sentences become wrong together and a grep for the sentence finds both. No action.

- **The four corrections introduce no new duplication.** Four spec sentences rewritten in place
  (`git diff --stat` unchanged at 73/196, so no line was added or removed), eleven rationale edits,
  one new link definition. I read each new spec sentence against the document it cites:
  `:129`'s Relay clause names spec-015's foundation and spec-032's extension and reproduces neither
  document's validation rules; `:167`'s consumer-wins clause states spec-004's own behaviour and
  hands spec-035 only the recording of the stance; `:35` and `:169` name two symbols and no sibling.
  Not one sibling rule is reproduced by this pass's additions.

- **No existence challenge to raise.** This item creates no abstraction, helper, registry, token, or
  indirection layer; the only structural addition is one link definition with two readers.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty** (0 lines of diff). `__all__` and
the re-export list are unchanged. `git status --short -- django_strawberry_framework/ tests/
examples/ scripts/` -> **empty**: no source, test, example, or script file changed in this cycle, as
the build plan's `## Build-wide context flags` requires. No correctness defect in shipped optimizer
code was found by this pass either, so nothing is escalated under that heading.

### CHANGELOG sanity

Not applicable; item did not modify `CHANGELOG.md`. Confirmed by `git status --short -- CHANGELOG.md`
-> empty.

### Documentation / release sanity

Applies — the diff is an archived spec and its rationale companion.

- **Version strings and card IDs.** The spec carries no version or status line and none was added;
  `## Implementation checklist` still carries all eleven `- [x]`, matching `DONE-004-0.0.3`. No
  KANBAN card moved and no release metadata changed.
- **The archive is intact.** Spec at `docs/SPECS/`, companions at `docs/SPECS/appx/`.
  `spec-004-optimizer_beyond-0_0_3-terms.csv` is untouched — `git status --short docs/SPECS/appx/`
  reports only the two untracked rationale files (spec-004's and the concurrent cycle's spec-005),
  and `git log -1` on the CSV returns `40e4754a`, the archival commit.
- **Every link definition resolves on disk, re-derived this pass** with my own parser (partitions
  each file at `<!-- LINK DEFINITIONS -->`, strips code spans before scanning uses, normalizes each
  target against the file's own directory, slugs every heading in each target and checks the anchor
  against that set): spec **11 defs / 11 used / 0 undefined / 0 unused**, rationale **24 / 24 / 0 /
  0**, **35/35 targets exist and every anchored target's heading is present**.
- **The new `[spec-015]` definition resolves and is correctly placed.** It reads
  `[spec-015]: ../spec-015-relay_interfaces-0_0_5.md`; the target exists (73,479 bytes, title
  `# Spec: Relay Interfaces and Node Foundation`). It sits under the `<!-- docs/SPECS/ -->` group,
  which is right per `START.md`'s closed-list convention (group = where the target lives; an
  eleventh header is not available), and in alphabetical position between `[spec-004-references]`
  and `[spec-016]`. It has **two** readers (`:540`, `:1125`), so it is neither unused nor a
  one-off. It is the only addition to either file's citation surface this pass.
- **No inbound anchor breakage.** `grep -rln "spec-004-optimizer_beyond-0_0_3.md#" --include="*.md" .`
  hits **three** files, all this cycle's own: the rationale and the two `bld-004-*` artifacts. No
  standing doc and no sibling spec links a spec-004 heading anchor. `## Proposed improvements`
  survives in the rationale at exactly **2** places (`:710`, `:876` — shifted from pass 2's `:704` /
  `:865` because this pass added lines above them) and **0** in the spec; I re-read both in place and
  both are still correctly historical.
- **No obsolete staging wording.** `grep -c` in the spec: "Proposed improvements" **0**,
  "Can be spec'd now" **0**, "when B4 ships" **0**, "check_optimizer" **0**.
- **No script-rendered doc touched.** `docs/TREE.md`, `docs/GLOSSARY.md`, `KANBAN.md`,
  `KANBAN.html`, `examples/fakeshop/db.sqlite3` all clean; no docstring feeds this change.
- **Verbatim-copy check** reduces to the maintainer-ruled sentence, verified below.

### Re-confirmed invariants — every one re-derived this pass, none quoted

| Check | Command | Result |
|---|---|---|
| Glossary terms | `check_spec_glossary.py --spec <spec>` | `OK: 10 terms - all have glossary entries and at least one spec link.` exit **0** |
| Layout / scaffold | `check_trailing_commas.py --check <spec> <rationale> <this artifact>` | exit **0**, all three |
| Card glossary chain | `manage.py import_spec_terms --check` (read-only form only) | `OK: 49 done cards have glossary links.` exit **0** |
| Fenced blocks | `grep -c '^```'` | **0** in spec, **0** in rationale |
| `AGENTS.md` rule 27 | `grep -nE '[a-zA-Z_/]+\.(py\|md):[0-9]+'` | **no match** in either file |
| Maintainer-ruled sentence | `diff` HEAD `:5` vs working `:7`; `md5` | `diff` **empty**, `a236d060acf135d69af06a01cf43646a` both sides |
| Source / test / example / script | `git status --short -- django_strawberry_framework/ tests/ examples/ scripts/` | empty |

**The ten anchors, re-derived per anchor.** `grep -o "glossary-<anchor>]" <spec> | wc -l` per id
returns exactly **2** for every one — `configurationerror`, `djangooptimizerextension`, `djangotype`,
`fk-id-elision`, `metaexclude`, `metafields`, `metaoptimizer-hints`, `only-projection`,
`optimizerhint`, `queryset-diffing` — one body use plus one definition, so all ten remain
single-carrier. None of this pass's four spec edits lands in an anchor-bearing clause, which I
checked by reading each carrier in place rather than inferring it from the count: `### B1`'s carrier
is `**Cache storage.**` (`:33`) while the edit is in `**Cache invalidation.**` (`:35`);
`### B6`'s `metafields` / `metaexclude` pair is at `:131`, two lines below the `**Mechanism.**`
paragraph edited at `:129`; `queryset-diffing` sits on the `### B8` heading (`:157`), paragraphs
above both B8 edits. `check_spec_glossary` passing is necessary but not sufficient — it accepts a
link anywhere in the body — which is why the placement read was done by hand.

**The spec narrates no history — re-run with my own alternation.** Thirty-one alternates including
`un-spec`, `re-derived`, `this pass`, `drift`, `superseded`, `historical`, `deprecated`,
`initially`, `now reads`, `revised`, `later spec`, `corrected`. **One** line: `:3`, R1's companion
pointer, which describes the *rationale file's* contents and which H18 / H20 place off-limits. The
`reconcil` hits at `:159` / `:165` / `:167` / `:169` / `:187` are B8's own domain word for the
shipped mechanism, re-read in place. No history narration.

**Both do-not-reverse instructions still hold, re-derived after this pass's edits.** H19: `grep -c`
on line-initial labels -> **10** `**Claims the spec may no longer make.**`, **12** `**Claims the
spec no longer makes.**`, plus R1's **1** deliberately-scoped stronger label at `:177`
("`**Claims the spec no longer makes as any slice's own argument.**`"). Nothing levelled. H20: five
"The competitive argument for this slice" (spec `:41`, `:63`, `:81`, `:109`, `:139`), two "The
opening argument for this slice" (`:119`, `:151`), `### B8` carrying neither. Byte-identical, and
none of the four spec edits lands inside one.

### The four new corrections, graded against source

Each was re-derived from source before I read the pass's account of it, with `git log -S` over the
symbol as the instrument the plan's `**CORRECTION (2026-08-08)**` prescribes. **All four are
correct.**

1. **`OptimizerHint.strategy` -> spec-033: correctly retracted.** `grep -c strategy` over
   `spec-033` -> **1**, and I read that line (`:261`): it is a finalization bullet naming "strategy
   stamps" among Phase-2.5 products written to the definition — it does not claim the seam.
   `git log -S"def strategy" -- django_strawberry_framework/optimizer/hints.py` -> **one** commit,
   `41008e4c` (**2026-07-17**, "fetch-mode axis, generic relations, strategy hints, index
   advisory"), long after spec-033's `0.0.9`. The internal contradiction the pass names is real:
   the file's own refusal 2 and the spec's own `:97` citation both already said `docs/README.md`,
   which I confirmed at `docs/README.md:175` `## Nested connection indexing` and `:177`
   documenting `OptimizerHint.strategy(...)`. The rationale's B4 move-pass entry (`:462`-`:468`)
   now reaches the same disposition as the reconciliation entry, so the file no longer disagrees
   with itself.

2. **Ancestry-aware prefetch absorption -> spec-033: correctly reclaimed. This is the consequential
   one and it holds three ways.** `grep -o subtree docs/SPECS/spec-033-...md | wc -l` -> **0
   occurrences** (and `ancestr|absorb` -> 0 lines). `git log -S"def diff_plan_for_queryset" --
   optimizer/plans.py` -> `5d92272f`, **2026-05-04**; `Release 0.0.3` is `2c5bfaae`, **2026-05-05**
   — the function predates the release by one day. I went further than the record and dated the
   *absorption logic itself* rather than the enclosing function, because a function introduced early
   can acquire ancestry-awareness late: `git log -S"_optimizer_can_absorb" -- optimizer/plans.py` ->
   **`ee469cbb`** (2026-05-04, "implement absorption logic for consumer prefetch entries") and
   `git log -S"ancestry"` over the same file -> **`411b2187`** (2026-05-04). Both symbols are
   still live at HEAD (`plans.py::_optimizer_can_absorb`, and the `prefetch_related` compare
   "by `prefetch_to` with ancestry" contract in `::diff_plan_for_queryset`'s docstring). So the
   ancestry-aware absorption is B8's own, shipped with this card, and the spec was exporting its
   own surface to a spec four releases later. Both sites now claim it.

3. **Consumer-wins "spec-035 owns it" -> "records that stance": correctly narrowed.** I read all
   four spec-035 sites. `:104` and `:423` both read "the package's consumer-wins drop in
   `diff_plan_for_queryset` (`spec-004` B8) is a permission-boundary safety stance, not an
   oversight"; `:121` is the same in a table row; `:136` is the out-of-scope summary. **Every one
   credits the drop back to spec-004 B8 by name and characterizes it.** "Owns" is this family's
   surface-ownership verb (`spec-002:6` #"each own the surface they added"), so the old sentence
   handed away a precedence spec-035 explicitly hands back. "Records that stance" is exactly what
   spec-035's text supports. The two rationale spellings (`:672`, `:1185`, both "records as such")
   were already correct and were correctly left alone.

4. **"Relay interfaces belong to spec-032" -> spec-015 foundation, spec-032 extension: correct.**
   `spec-032:9`'s Predecessors sentence names `spec-015-relay_interfaces-0_0_5.md` as "the Relay
   Node integration foundation ... and the `Meta.interfaces` validation **this card's diagnostics
   extend**" — spec-032 defers the foundation to spec-015 in its own words. `spec-015`'s title is
   `# Spec: Relay Interfaces and Node Foundation`. And the descent arm predates spec-032
   independently: `git log -S"get_implementations"` and `git log -S"GraphQLInterfaceType"` over
   `optimizer/extension.py` both return **`f83bb71b`** (**2026-05-20**), inside the `0.0.5` /
   `0.0.6` window and well before spec-032's `0.0.9`. The spec's replacement at `:129` names
   spec-015's foundation and spec-032's later extension in one clause each and reproduces neither
   document's validation rules; the rationale's B6 entry (`:1122`-`:1128`) and its claims block
   (`:1143`-`:1144`) both carry the retraction. One supporting figure in the record is slightly
   off — the entry cites spec-032's `Meta.interfaces` mentions as 16 where `grep -o` returns **15**
   (spec-015's 27 reproduces) — but it is a colour figure beside two independent proofs, not the
   load-bearing evidence, so I am recording it here rather than filing it.

**M3's own seven sites, re-verified rather than assumed closed.** `grep -c immutab` over spec-035 ->
**0**; `grep -rn '_assert_under_construction' docs/SPECS/` -> hits in **spec-004 only** (`:35`,
`:169`) plus the rationale's own re-derivation line; `git log -S"def finalize" --
optimizer/plans.py` -> `c7447e23` (**2026-05-11**) and `git log -S"_assert_under_construction"` ->
`991d5120` (**2026-07-13**), against spec-035's own Revision 2 dated **2026-06-16** — one symbol a
month early, the other a month late, neither spec-035's. The five rationale sites the review
numbered are all corrected: no `][spec-035]` use in the rationale now credits immutability
(the ten remaining are the projection gate `:357` / `:990`, the unsafe-elision fallback `:419` /
`:1008` / `:1051`, consumer-wins-as-recorded `:672` / `:1185`, the restraint list `:819`, the
retraction itself `:960`, and the deferred spec-003 note `:1238`). `:387`'s once-per-row key
threading is now stated with no owner and its re-derivation beside it.

### The citations left alone, spot-checked against the cited document

A sweep that corrects four and wrongly clears the rest is worse than one that corrects none, so I
re-checked the sound list against the documents rather than against the sweep. **Every one holds.**

- `spec-002:6` — "The same rule governs the rest of the optimizer family — `spec-004`, `spec-033`,
  and `spec-035` **each own the surface they added**." Verbatim, and it names spec-004 explicitly,
  so it is the right authority for every ownership call in this cycle. `spec-002:58` — "O1 through
  O6 have shipped."
- `spec-003` — title `# Spec: Optimizer O4 — Nested Prefetch Chains`; `:123` states the fan-out rule
  in full and delegates only the nested-connection multiplication to spec-033 in the same
  sentence's parenthetical; `:70` states the ordering invariant with the causal argument and
  "Nothing enforces the order but the order itself". Both spec-004 citations are correct and, after
  the pass-1 DRY fix, point without reproducing.
- `spec-016` — title `# Spec: `FieldMeta` single-source-of-truth consolidation and mirror
  retirement`; `:39` names `cls._optimizer_field_map` and `cls._optimizer_hints` as the retired
  mirrors. All four rationale uses (`:458`, `:583`, `:1069`, `:1150`) are the mirror retirement.
- `spec-018` — title `# Spec: Multiple `DjangoType`s per model with `Meta.primary``. Both spec sites
  (`:25` the origin discriminator's premise, `:133` the dedupe's premise) claim only "several types
  over one model is spec-018's surface", which is what the title carries.
- `spec-023` — title `# Spec: Multi-database cooperation contract`. Cited once, for `state.db` from
  the read router.
- `spec-029` — `:327` `### Decision 3 — Slice 1 adopts the singleton-factory `extensions=` form`,
  and `:25` `P1.1 — stale extension-lifecycle model` names spec-004's model stale by name. The
  direction of correction runs spec-029 -> spec-004, so spec-004 pointing is right.
- `spec-032` / `spec-015` — graded above.
- `spec-033` D4 / D5 / D7 / D8 — all four decision headings exist at `:270` / `:293` / `:343` /
  `:363` and carry what they are cited for (the package-reserved `to_attr` window, the per-parent
  fallback, plan-cache key hygiene, strictness-mode wiring for connection paths). The union rule is
  additionally cited in **source**: `optimizer/extension.py:1196` and `:1231` both name "spec-033
  Decision 8" in comments, so the spec and the code agree.
- `spec-035` D4 / D5 — `:186` `### Decision 4 — G2 — operation-type gating of `.only()`` and `:212`
  `### Decision 5 — G2 — FK-id elision stays enabled under non-`QUERY` operations`. The four
  surviving spec-035 citations in the spec (`:49`, `:57`, `:77`, `:167`) map onto exactly these two
  decisions plus the recorded stance. Sound.
- `spec-047` — title `# Spec: Execution resource policy`; `:99`, `:360`, `:744` and `:760` all state
  that the shape-agnostic context dispatch lifted to `utils/context.py` and `:760` that it is the
  only one. `git log --diff-filter=A -- utils/context.py` -> `567cc6d0`, 2026-08-04, the resource
  policy commit. Correct.
- `docs/README.md` — `:175` `## Nested connection indexing` exists and `:177` documents
  `OptimizerHint.strategy(...)`; `:53` carries the module-level-singleton-wrapped-in-a-factory form,
  as does `docs/GLOSSARY.md:723`.

**I also applied the pass's own prescribed fifth-misattribution test rather than only reading its
result** — "any sentence where spec-004 names a sibling for something that shipped at `0.0.3`",
settled by `git log -S` against `2c5bfaae` (2026-05-05). Every sibling-credited symbol postdates the
release: `enable_only` -> 2026-06-16 (the spec-035 cycle), `_FK_ELISION_UNSAFE` and `force_unplanned`
-> 2026-06-16, `_stash_union` -> 2026-06-13 and `connection_to_attr` -> 2026-06-13 (the spec-033
cycle), `utils/context.py` -> 2026-08-04 (spec-047). **No fifth misattribution of that shape
exists.** The one adjacent case — `_collect_cache_var_families` landing 2026-06-13 with spec-033
while B1 states the two-family rule — is the DRY item recorded above, and it runs the *other* way.

### What looks solid

- **The population-based sweep is the right instrument and it found what a worklist sweep
  structurally could not.** Two of the four new misattributions had spec-004 **exporting its own
  surface to a sibling** — the mirror image of the over-absorption every prior pass in this cycle
  hunted, and a direction no dispatch, no drift row, and no review had ever named. Finding 2 in
  particular required dating a symbol against a release commit, which is a technique, not an
  observation. The M3 finding demanded a population; what came back is more than the finding asked
  for.
- **Every correction moved the correct half, and each has a recorded loser.** M3's rejected
  alternative — "leave the pointer and let a later pass make it true by editing spec-035" — is the
  one a future harmonizing sweep would actually reach for, and rejecting it *in writing* with the
  family-rule reason is what stops the round being re-fought. Reclaiming the absorption for B8
  rather than deleting the sentence, and narrowing "owns" to "records" rather than cutting the
  spec-035 citation entirely, are both the smaller and the truer edit.
- **Refusal 1's disposition was applied consistently to two new un-owned behaviours.** Plan
  immutability and the once-per-row key threading are now stated with their symbols and no
  citation, which is the same call the root-response-path cache-key component got in the first
  pass. A spec that says "this is ours and nothing else states it" is auditable; a spec that points
  at a document which carries nothing is not.
- **The record and the files agree everywhere I tested them.** `### Spec changes made (Worker 1
  only)` lists four edits and the spec carries exactly four changed sentences; `### Files touched`
  lists eleven rationale edits and one new link definition, and the definition count moved 23 -> 24
  with `[spec-015]` as the whole of the move; `git diff --stat` is unchanged at 73/196 because all
  four are in-place rewrites, which I confirmed rather than assumed.
- **L3 was closed the only compliant way and both corrected counts reproduce.** `ARTIFACT.md`
  `## Re-pass sections` forbids editing a prior entry, the `### L1` bullet is byte-identical, and
  the correction states its command. The generalizable lesson the pass added — that a count of
  "hits in a directory" must state the include filter, because an unfiltered `grep -rn` also reads
  shadow files and artifacts — is the actual root cause of both wrong numbers and is worth keeping.
- **Three residues I could have dressed up as findings and deliberately did not.** (a) `## Current
  state` still calls the optimizer "effective end-to-end", HEAD's own unfalsifiable wording — no
  reader takes a wrong action from it and two prior passes already recorded it. (b) `### B7`'s
  `**Test surface.**` keeps "Benchmark (optional)", which reads as unbuilt work but is marked
  optional and was never a delivery claim. (c) The rationale's `## How to read this file` bullet 8
  still describes the extraction pass in the past tense while the reconciliation is complete; it is
  scoped to that pass by its own first three words. Recorded so the next pass cannot read silence
  as an unexamined area.

### Temp test verification

No temp tests were created. `docs/builder/temp-tests/r2/` was not used and `docs/builder/temp-tests/`
is empty (`ls` confirms; the directory holds nothing). This item changes no code and introduces no
boundary, guard, gate, or rejection path, so `BUILD.md` `### What needs a proof, and what does not`
scopes it out of the failability-proof mechanism entirely and **the mandatory re-run floor is
legally empty** — the diff introduces no boundary that meets it. Verification here was
read-and-re-derive against source, against the read-only HEAD blob, and against `git log -S` over
each disputed symbol, which is the whole of the available technique. No `pytest` was run
(`AGENTS.md` rule 15) and no `--cov*` flag appears in any command in this pass.

### Working-tree state — re-derived this pass, reported, not reverted

`HEAD` is **`ff03c1372365edcad488ff4671389d88ae145276`**, unchanged since the apply pass moved to it,
and it did not sweep this cycle's work — `git log -1 --format=%h` over the spec still returns
`20a9752f`. **The list is unchanged from the apply pass's closing reading for the first time in this
cycle**, with one clearance: `?? docs/SPECS/spec-063-structural_templates-0_1_6.md` is gone, absorbed
by `ff03c137`. Thirteen entries:

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
 M docs/SPECS/spec-005-django_type_contract-0_0_3.md
 D docs/builder/bld-003-final.md
 D docs/builder/bld-003-r1-rationale_move.md
 D docs/builder/bld-003-r2-spec_reconciliation.md
 D docs/builder/bld-003-r3-doc_completion_archive.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/bld-004-r2-spec_reconciliation.md
?? docs/builder/bld-005-r1-rationale_move.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
?? docs/builder/build-005-django_type_contract-0_0_3.md
```

The four `D docs/builder/bld-003-*.md` deletions persist and were **not** restored — the build
plan's `### Fifth change` makes that the maintainer's call and `AGENTS.md` rule 34 bans the
`git checkout` that would do it. `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`,
`CHANGELOG.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, `KANBAN.md`, `KANBAN.html`, and
`examples/fakeshop/db.sqlite3` are all **clean**. `import_spec_terms --check` was re-run at this
tree state and still returns `OK: 49 done cards have glossary links.`

### Notes for Worker 1 (spec reconciliation)

**This is the complete R3 handoff, re-issued in full. Nothing lives only in a closed section**, so
every item from the item's own list, from all three reviews, and from both apply passes is restated
here rather than cross-referenced; R3's dispatch is built from this list alone.

1. **Two Mediums and one Low are open and route to Worker 1**, not Worker 2 — `### Deviation 2`'s
   corollary makes the apply-changes pass Worker 1's and sets `Status: planned` again. M4 touches
   this artifact only (one restated population); M5 touches the rationale's
   `### What this pass deliberately left for others` bullet and this list's item 5; L4 touches this
   artifact only. **No spec or rationale contract sentence changes.** None needs maintainer context,
   so the `review-accepted`-with-escalation carve-out does not reach them.
2. **Deferred, for the final gate's `### Deferred work catalog`:** the `check_optimizer` management
   command and custom-resolver detection (D21 / S5) — named as B6 follow-up work eleven versions
   ago, never built, and **no card exists for either**. Dropped from the spec by the item and
   recorded in the rationale. `inspect_django_type` (`spec-029`) answers a different question and is
   explicitly not offered as a substitute. Re-verified this pass: `grep -c check_optimizer` -> 0 in
   the spec, and `django_strawberry_framework/management/commands/` ships `export_schema` and
   `inspect_django_type` only.
3. **Deferred:** the `_record_relation_access`-before-elision ordering invariant still has **no
   automated guard** in `walker.py::_plan_select_relation`. Adding one is a source change and out of
   scope for a documentation cycle. The spec points at `spec-003` for both the rule and its cost,
   which after the pass-1 DRY fix is the most a docs cycle can do.
4. **Deferred, sibling-spec staleness (1 of 2):**
   `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` calls `0.316.0` "the locked" Strawberry
   version; it is the **declared floor** (`pyproject.toml` #"strawberry-graphql>=0.316.0") and
   `uv.lock` resolves higher. This cycle's own rationale phrasing was corrected (H17); sibling specs
   are read-only here with no declared exception, so the two documents now disagree — the state R3
   or a future spec-029 cycle inherits. R1's handoff item 17 asked that whoever tightens it decide
   for both documents at once.
5. **Deferred, sibling-spec staleness (2 of 2) — and this is M5, so it is the one item on this list
   that is not yet complete.** `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md:30`
   makes the same wrong `spec-035` plan-immutability attribution M3 caught, and it is recorded in
   the durable rationale at `:1236` (confirmed this pass — it is not artifact-only). **But the class
   is five sites, not one:** the companion
   `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md` carries `:521`
   ("`spec-035` (plan immutability, ...)"), `:603`-`:604` ("decisions belonging to `spec-033` and
   `spec-035`, **each already stated once in its own document**"), and `:855` ("discipline is
   `spec-035`'s to state") — the last being a standing instruction to write the contract into
   spec-035, which is precisely the alternative M3's rationale entry rejects. Both files are
   read-only in this cycle, so the fix is the **enumeration**, not the edit: extend the rationale
   bullet and this item to name the companion and its three sites. Whoever fixes them should decide
   for all five at once.
6. **Deferred:** three B7 test names in `tests/optimizer/test_field_meta.py`
   (`::test_optimizer_field_map_populated`, `::test_optimizer_field_map_contains_relations`,
   `::test_optimizer_field_map_respects_fields_filter`) still spell the retired
   `_optimizer_field_map`. Live code, carded on `TODO-ALPHA-052-0.1.0`, not this cycle's; no test
   file is writable here.
7. **For R3's durable-doc audit — the spec names ten sibling specs by path, as code spans, not
   reference-style links.** **21 occurrences across 10 siblings**, re-derived this pass by
   occurrence: spec-033 x5, spec-035 x4, spec-003 x3, spec-002 x2, spec-018 x2, and spec-015 /
   spec-023 / spec-029 / spec-032 / spec-047 x1 each, plus one `docs/README.md`. (Worker 3's pass-2
   note 7 said nine siblings / 23 occurrences; the apply pass's own correction 5 supersedes it and
   is the reading that re-derives.) This matches `spec-003`'s convention and spec-004's own
   pre-existing `## Problem statement` / `## Non-goals` style, keeps the spec's link-definition
   block at 11 entries, and is **not** a scaffold violation — `check_trailing_commas.py --check`
   passes on both files. R3's cross-reference sweep must not "fix" them into reference-style links.
8. **For R3:** the section heading `## Proposed improvements` no longer exists; it is
   `## The eight improvements`, anchor `#the-eight-improvements`. My own tree-wide
   `grep -rln "spec-004-optimizer_beyond-0_0_3.md#" --include="*.md" .` confirms **no external
   consumer** links a spec-004 heading anchor — the only hits are this cycle's own three files. The
   two remaining old-spelling occurrences in the rationale (`:710`, `:876`) are both correctly
   historical, both re-read in place, and **must not be "fixed"**.
9. **For R3:** `bld-004-r1-rationale_move.md` records `#proposed-improvements` as resolving; that
   heading no longer exists. It is a closed per-cycle scratchpad, exempt from the symbol-path rule
   and regenerated by the next cycle, so it is left alone — recorded only so R3's cross-reference
   sweep does not read it as live rot.
10. **For R3's re-derivation duties, with expiry noted.** My readings — 35/35 link targets resolve,
    `import_spec_terms --check` green, ten anchors single-carrier, `check_spec_glossary` green,
    `db.sqlite3` clean, the working-tree list at thirteen entries — are current at `ff03c137` and
    **have an expiry**. R3 re-runs each itself, re-runs `import_spec_terms --check` **after** any
    further concurrent DB write, and attributes any dirty `db.sqlite3` by `iterdump()`
    set-difference rather than by file bytes.
11. **New out-of-scope files, for Worker 0's `## Baseline-dirty out-of-scope files`:**
    `docs/builder/build-005-django_type_contract-0_0_3.md`,
    `docs/SPECS/spec-005-django_type_contract-0_0_3.md` (modified),
    `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md`, and
    `docs/builder/bld-005-r1-rationale_move.md` — the concurrent card-005 cycle. Plus the four
    `D docs/builder/bld-003-*.md` deletions, which persist and are the maintainer's call per
    `### Fifth change`. `docs/SPECS/spec-063-structural_templates-0_1_6.md` has **cleared**
    (absorbed by `ff03c137`) and should come off the list. R3 must not read `docs/builder/` or
    `docs/SPECS/` as clean.
12. **The `## How to read this file` claims-block definition now defines two block kinds.** A future
    pass adding a third kind of closing block must extend that bullet in the same edit — the defect
    M1 caught was a definition left behind by a label, and the definition is the index a reader
    consults first.
13. **Two behaviours in this spec now have no owner anywhere, deliberately.** The plan-immutability
    enforcement (`optimizer/plans.py::OptimizationPlan.finalize` / `::_assert_under_construction`)
    and the once-per-row resolver-key threading are both stated with their symbols and no citation.
    I confirmed `grep -rn '_assert_under_construction' docs/SPECS/` hits spec-004 only. If a future
    spec claims either, spec-004's sentences are the ones to update — and `spec-033`'s
    "finalize-to-tuple discipline" reference is the only cross-reference that touches the first, and
    it points *back* at spec-004.
14. **`HEAD` is `ff03c137` and has not moved since the apply pass.** Worker 0 should record the hash
    change on the plan. The standing lesson holds: a plan's baseline-dirty list is a snapshot, and
    this cycle has watched it move four times and watched `HEAD` move under it once.
15. **The drift table's owner column has now produced errors on eight rows, not four** (L4): D7, D9,
    D13, D15, D17, D20, D25, D26. The build plan's `**CORRECTION (2026-08-08)**` calls itself "the
    third error" and `### Notes for Worker 1` item 2 says four; both predate this pass's four new
    findings, which trace to D15, D20 and D25. Worker 0 should extend the correction paragraph. The
    **remedy it states is already right and does not change** — treat an owner cell as a hypothesis
    and settle it with `git log -S` over the symbol.
16. **Recorded so it is not re-opened: `### B1` `**Directive-variable extraction.**` restates
    `spec-033` Decision 7's cache-key-hygiene rule while its pointer aims at the windows.** Examined
    at length and deliberately not filed — the reasoning, the evidence, and the standard it was
    judged against are in `### DRY findings` above. If a future pass reaches for it, the question to
    answer first is whether "which variables key the cache" is B1's own contract or spec-033's; I
    concluded B1's, on the same requirement-stays / cost-moves line the pass-1 DRY finding drew.
17. **No correctness defect in shipped optimizer code was found by any of the three passes.**
    Everything traced this pass — `OptimizationPlan.finalize`, `::_assert_under_construction`,
    `diff_plan_for_queryset`, `_optimizer_can_absorb`, `check_schema`'s interface descent,
    `OptimizerHint.strategy`, `stash_on_context`'s consumers — behaves as the reconciled spec now
    states. Nothing is escalated to the maintainer under `## Build-wide context flags`'
    read-only-audit rule.

### Review outcome

`revision-needed`.

Two Mediums and one Low, none addressed and none intentionally rejected; `worker-3.md`'s acceptance
gate requires every finding to be one or the other. **All three are edits to records, not to
contracts**: M4 restates one population inside this artifact, M5 extends one enumeration in the
rationale's deferred-items bullet, L4 corrects one numeral in this artifact's handoff. No spec
sentence and no rationale contract sentence changes, and nothing settled is re-opened.

**Everything the prompt sent me to grade came back clean apart from those three.** All four new
misattributions are real and correctly resolved, each re-derived from source before I read the
account of it: `strategy` (`grep -c strategy` -> 1 in passing; `41008e4c`, 2026-07-17), the
ancestry-aware absorption (`subtree` -> 0 occurrences; `_optimizer_can_absorb` and `ancestry` both
2026-05-04 against `Release 0.0.3` on 2026-05-05 — **B8's own, and the spec was exporting its own
surface**), consumer-wins (all four spec-035 sites credit the drop back to spec-004 B8 by name), and
the Relay foundation (`spec-032:9` defers to spec-015 in its own words; the descent arm is
`f83bb71b`, 2026-05-20). M3's seven sites are all closed and no surviving `spec-035` citation
credits immutability. The sweep's stated population re-derives exactly where it is stated with its
commands — 16 lines / 22 occurrences and 60 owner-naming occurrences — which is why M4 is about the
*restatement* and not about the sweep. Every citation the sweep left alone was re-checked against
the cited document and **all are sound**, including the four a later reader would trust blindest
(`spec-033` D4/D5/D7/D8, `spec-035` D4/D5, `spec-018`, `docs/README.md`), and the union rule is
corroborated in source at `extension.py:1196` / `:1231`. L3's corrected counts reproduce exactly
(11, and 13 across 5 files with `optimizer/` at 0). The new `[spec-015]` definition resolves, sits
in the right group in alphabetical position, and has two readers. `spec-003:30` is confirmed
recorded in the **durable** rationale, not only here — M5 is that the record names one site of five.
And I applied the pass's own prescribed fifth-misattribution test independently: every
sibling-credited symbol in the spec postdates `0.0.3`, so no further export of this slice's own
surface exists.

Every invariant re-derived and held: 236 / 36,223 and 1,286 / 92,426, 73/196, HEAD blob 359 / 33,928,
21 citations across 10 siblings with the per-spec breakdown, 21 = 20 + 1 and 17 + 3 = 20, 10 + 12 + 1
labels, ten anchors at exactly two occurrences each with every carrier read in place, 11/11 and 24/24
link definitions with 35/35 targets and anchors resolving, zero fenced blocks, zero rule-27
violations, the maintainer-ruled sentence byte-identical at `a236d060acf135d69af06a01cf43646a`, both
do-not-reverse instructions un-levelled, `check_spec_glossary` / `check_trailing_commas` /
`import_spec_terms --check` all green, and **no source, test, example, or script file changed**.

Per `### Deviation 2`'s corollary this routes to **Worker 1**, which applies the corrections and sets
`Status: planned` again.

---

## Build report (Worker 1, apply-changes pass 3)

`### Deviation 2`'s corollary routes an R2 `revision-needed` to Worker 1, not Worker 2. This pass
applies Worker 3's pass-3 findings (M4, M5, L4) and returns `Status: planned`, which Worker 0 reads
as "dispatch Worker 3" for this item. **Every prior section of this artifact is unedited** apart
from the `Status:` line, which is the field's own owner-updated value; M4's and L4's corrections are
stated here rather than by rewriting the sentences they correct, exactly as L2 and L3 were.

Plan declarations, unchanged: ownership partition `none; sequential residual items`; hot-path
`none`; floor-verification scope `none`. No `--cov*` flag was used in any command.

### Findings disposition

All three are **fixed**. None was rejected. **No contract sentence changed in either file** — the
spec is byte-identical to its pass-2 state (236 lines / 36,223 bytes, `git diff --stat` still
73/196), and the only durable edit is one widened bullet in the rationale's deferred-items list.
The reconciliation was not reopened: no drift-row disposition changed, no S-finding was re-argued,
M1 / M2 / M3 / L1 / L2 / L3 and the DRY finding were not touched, and both do-not-reverse
instructions were re-verified rather than adjusted.

| Finding | Disposition | Sites |
|---|---|---|
| M4 (population stated twice, with different numbers) | Fixed **here**, not in place: the restatement is retracted rather than repaired, and one population stands with a command that actually reproduces | this section, `### M4` below |
| M5 (deferred `spec-003` item names 1 site of a class) | Fixed in the **durable** file: the rationale bullet now enumerates **seven** sites — the review named five — with its evidence. **No sibling file was edited** | rationale `### What this pass deliberately left for others` (`:1236`-`:1263`); this section |
| L4 (owner-column error count) | Fixed **here**; the numeral is replaced by the enumerated row list, which needs no arithmetic | this section, `### L4` below |

### M4 — the restatement is retracted, not repaired, and the population is stated once

**Why retracted rather than corrected.** The finding asks whether a restated figure needs to exist
at all. It does not. `### The provenance sweep — every claim in both files, settled from source`
states the population with its commands and Worker 3 re-derived it exactly; `### Notes for
Worker 3`'s "24 provenance claims on 18 spec lines, 55 citation occurrences" was a **second
measure of the same thing, taken from memory and stated without a command**. A durable rule this
cycle has now paid for six times: **state a count once and point at it.** So the correction is not
a better second number — it is that the second number should never have been written. `ARTIFACT.md`
`## Re-pass sections` forbids editing the prior entry, so that bullet is **left byte-identical** and
is retracted here: **`24 / 18 / 55` is withdrawn in full. It reproduces under no derivation, it is
backed by no command, and nothing depends on it.**

**The one population that stands**, re-measured after this pass's last edit:

- **Spec — 17 lines carrying 23 provenance-claim occurrences.** The command:
  `grep -cE 'spec-0[0-9][0-9]-[a-z_]+-0_0_[0-9]+\.md|docs/README\.md' <spec>` -> **17**, and the
  same pattern with `-oE ... | wc -l` -> **23**. Matching the *filename* form is what makes it
  re-derivable: it takes both the code-span `docs/SPECS/…` citations and the bare-filename one,
  and it excludes the `[spec-004-rationale]` reference id and its definition, which are not
  citations of a sibling. Breakdown by `| sort | uniq -c`: `spec-033` x5, `spec-035` x4,
  `spec-002` x3, `spec-003` x3, `spec-018` x2, and `docs/README.md` / `spec-015` / `spec-023` /
  `spec-029` / `spec-032` / `spec-047` x1 each.
- **Rationale — 62 owner-naming occurrences** (was 60 before this pass's bullet):
  `grep -o '\]\[spec-0[0-9][0-9]\]' | wc -l` -> **55**, of which **1** is the self-reference
  `[spec-004]`, leaving **54**; plus `][docs-readme]` **3**, `][spec-002-rationale]` /
  `][spec-003-rationale]` **4**, `][glossary]` **1**. 54 + 3 + 4 + 1 = 62. The +2 over the sweep's
  60 is M5's widened bullet, and nothing else moved.

**Worker 3's own suggested command does not reproduce its own figure, and this is worth recording.**
The finding proposes `grep -c 'spec-0[0-9][0-9]\|docs/README.md'` for the widest reading; run
against the spec it returns **27 lines / 34 occurrences**, because it also matches the
`[spec-004-rationale]` reference id at `:3`, `:9`, and every per-slice pointer paragraph, plus the
definition at `:222`. The *figures* it states — 17 / 23 — are right; the pattern is not. The
generalizable form, and the reason this pass wrote a different one: **a citation-population pattern
must match the citation's distinguishing shape (here, a filename), never the bare identifier the
document also uses for its own link ids.**

**The `:7` clause the sweep's closing sentence was missing.** `### The provenance sweep` closes
"**Nothing else in either file makes a provenance claim.** The population above is the enumeration",
and its own narrow pattern (`docs/SPECS/spec-0\|docs/README.md`, 16 lines / 22 occurrences) misses
one: spec `:7` cites `` `spec-002-optimizer-0_0_2.md` `` by bare filename. It **is** a provenance
claim, it **is** true — `spec-002` #"O1 through O6 have shipped" settles it, re-derived this pass —
and it sits inside the maintainer-ruled `## Problem statement` sentence, which is byte-identical to
HEAD and not editable by any pass. So the 17th line is a **known, settled, non-editable** member of
the population, and nothing is owed to the spec. What was owed was that the enumeration say so, and
the 17-line figure above says it.

### M5 — the deferral widened from one site to seven, in the durable file

**The record was durable but under-scoped, and the imperative it carries is what makes that a
defect.** The bullet's instruction is "whoever fixes it should decide for both documents at once".
A reader following it opens `spec-003` #"finalized at handoff", fixes one line, and closes the item
— leaving the companion's copies live, one of which is a standing instruction to write the contract
*into* `spec-035`.

**Re-derived before anything was written, and the class is wider than the review's five.** Worker 3
named `spec-003:30` plus companion `:521`, `:603`-`:604`, `:855` (with `:598` riding along). The
population — `grep -n '\]\[spec-035\]\|spec-035-optimizer'` over
`docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md` -> **7 lines**,
`:253`, `:521`, `:598`, `:604`, `:855`, `:952`, plus the definition at `:1050` — shows **every one
of the six body uses** carries the error. Two were on no list:

- **`:253`** — "a short-circuit on a precomputed frozenset once the plan is finalized, and a single
  named reader for the Django-private `_prefetch_related_lookups` … Both are later hardening
  (`spec-035`)". Both halves are misattributed in one sentence.
- **`:952`** — "`select_related == [...]` is a tuple at HEAD, because the plan is finalized before
  handoff (`spec-035`)". The tuple swap is `OptimizationPlan.finalize`'s, which no spec states.

`:521` is the only partly-sound line: its "the projection gate" item is genuinely `spec-035`
Decision 4; its "plan immutability" item is not.

**The evidence, all re-derived this pass rather than carried from M3.** `grep -c immutab` over
`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` -> **0**;
`git log -S"def finalize" -- django_strawberry_framework/optimizer/plans.py` -> `c7447e23`,
**2026-05-11**, against that spec's own Revision 1 of **2026-06-15**. And for the single-reader
half, which M3 never touched: the reader is
`django_strawberry_framework/optimizer/plans.py::_consumer_prefetch_lookups`, dated by
`git log -S"_consumer_prefetch_lookups"` to `603e1c60`, **2026-05-06** — six weeks before
`spec-035` was authored — and
`grep -rniE 'single[- ](named )?reader|one named reader|exactly one call site|only reader'
docs/SPECS/` returns hits in **that companion only**. No spec under `docs/SPECS/` states the
discipline the companion says is `spec-035`'s to state.

**What landed, and what deliberately did not.** The rationale bullet now names the companion, its
three shapes (credits the work / asserts it is already stated / instructs a future pass to state
it), the six sites by `#"substring"` — `AGENTS.md` rule 27 form, since the rationale is a durable
file where `path:NN` is banned — and the evidence above. **No sibling file was edited**: `spec-003`
and its companion are read-only in this cycle, and M5 is a deferral to record. The bullet closes on
the point the finding is really about: **where the sites are unfixable, the enumeration is the
deliverable**, and fixing one line and closing the item is the failure the bullet exists to
prevent. No new link definition was needed — `[spec-003-rationale]` already existed and now has a
second reader.

### L4 — the numeral replaced by the rows, which need no arithmetic

`### Notes for Worker 1` item 2 of the pass-2 build report says "**four errors** (D17, D9, D7/D26,
D13)". It is **left byte-identical** per `ARTIFACT.md` `## Re-pass sections`; the corrected
statement is here.

**The drift table's owner column has produced errors on eight rows: D7, D9, D13, D15, D17, D20,
D25, D26.** The four the pass-2 sweep found beyond M3 all trace to that column and the pass did not
connect them — `OptimizerHint.strategy` -> `spec-033` is D15's cell, the ancestry-aware absorption
and consumer-wins are both D25's, and Relay interfaces -> `spec-032` is D20's.

Two things this correction deliberately does. First, it states the **rows** rather than a count:
`BUILD.md` `## Claims are proven mechanically` prefers a form the reader can re-derive, and a row
list is checkable against the table while a numeral is only believable. Second, it records that
**Worker 0 has already re-measured the build plan's own paragraph**:
`build-004-optimizer_beyond-0_0_3.md` `**Re-measured 2026-08-08 after R2's pass-3 review**` now
carries the same eight rows and says outright "Do not read the numeral as settled — re-derive it if
you need it." Nothing is owed to the plan, which is Worker 0's file in any case.

**The conclusion is unchanged and this pass changes nothing about it.** The standing remedy — treat
an owner cell as a hypothesis and settle it with `git log -S` over the symbol — was already right,
and pass 2 applied it to the whole citation surface rather than to the flagged cells, which is the
improvement that matters.

### The DRY residue Worker 3 recorded and did not file — read, and agreed with

Worker 3's `### DRY findings` records, without filing, that `### B1`
`**Directive-variable extraction.**` restates `spec-033` Decision 7's cache-key-hygiene rule while
its pointer aims at the windows. **I read its reasoning and both documents in place, and I agree —
no edit.**

The line it draws is the one the pass-1 DRY finding drew and this cycle has applied since: the
**requirement** a section's reader must act on stays; the **cost argument** moves one hop. The two
cases differ on which side of that line the disputed sentence falls, and the difference is real
rather than convenient:

- **B2's ordering invariant was `spec-003`'s rule that B2 merely consumes.** spec-004 added nothing
  to it, so reproducing its causal argument was a second copy of someone else's contract.
- **Which variables key B1's cache is B1's own contract.** The cache key is this slice's surface;
  `spec-033` Decision 7 *extended* it. `spec-002` #"each own the surface they added" therefore runs
  the other way here — a builder reading B1 alone who does not know the second family builds the
  wrong key, and the non-root qualifier is not a cost argument but the rule itself. What the
  sentence hands to `spec-033` is the windows those values feed, which it describes not at all.

The two causal clauses are the arguable half, and they are one clause each against Decision 7's
seven sub-bullets — and L1's lesson cuts against removing them: this is the paragraph a builder
narrowing the collection would consult, and a reasonless rule invites the change it exists to
prevent. Recorded here, and in `### Notes for Worker 1` below, so a future pass neither re-derives
it nor reads silence as an unexamined area.

### Spec changes made (Worker 1 only)

**None.** `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` is byte-identical to its pass-2 state,
proved below by `wc -l -c` (236 / 36,223, unchanged) and `git diff --stat` (73 / 196, unchanged).
All three findings were edits to records; none reached a contract sentence, which is what Worker 3's
own `### Review outcome` predicted. The maintainer-ruled `## Problem statement` sentence is proved
byte-identical to HEAD below.

### Files touched

- `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` — **one** edit: the
  `### What this pass deliberately left for others` `spec-003` bullet, widened from one site to
  seven with its three shapes, its six `#"substring"` citations, and its re-derived evidence
  (`:1236`-`:1263`). No link definition added or removed; no other bullet, section, or claims block
  touched.
- `docs/builder/bld-004-r2-spec_reconciliation.md` — `Status:` set to `planned`; this section
  appended. No prior entry edited.
- `docs/builder/worker-memory/worker-1.md` — memory entry (gitignored).

Nothing else was written. No spec sentence, no package source, test, example, script, sibling spec
(`spec-003` and its companion included), terms CSV, `CHANGELOG.md`, `KANBAN*`, `docs/GLOSSARY.md`,
`docs/TREE.md`, DB file, build plan, or `bld-004-r1-rationale_move.md` was touched, and the four
deleted `bld-003-*.md` files were **not** restored (`### Fifth change`: the maintainer's call).

### Byte and line counts (measured as written, after the last edit)

| | lines | bytes |
|---|---|---|
| spec at HEAD (pre-R1 blob) | 359 | 33,928 |
| spec after apply-changes pass 2 | 236 | 36,223 |
| spec **after this pass** | 236 | **36,223** |
| this pass's spec delta | +0 | **+0** |
| rationale after apply-changes pass 2 | 1,286 | 92,426 |
| rationale **after this pass** | 1,309 | **94,318** |
| this pass's rationale delta | +23 | **+1,892** |

`git diff --stat -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> **73 insertions /
196 deletions**, unchanged, and necessarily so: this pass wrote no spec byte. Method: `wc -l -c` on
the working files; the HEAD row from `git show HEAD:<path>` into a scratch path outside the repo
(`wc -l -c` on that blob -> **359 / 33,928**, reproduced this pass). No `git stash`, `git checkout`,
`git restore`, or `git worktree` anywhere in this pass.

### Validation run

Every command re-run after the last edit; nothing quoted from an earlier reading.

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`
  -> `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0**,
  character-identical to the baseline.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-004-optimizer_beyond-0_0_3.md docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md`
  -> **exit 0**, both files; scaffold and all 10 canonical group headers intact in each.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` ->
  `OK: 49 done cards have glossary links.` **exit 0**. Read-only form only; the writing form was
  never invoked.
- **Anchor carriage, re-derived per anchor, all ten at exactly 2** (`grep -o "glossary-<anchor>]"
  <spec> | wc -l`): `configurationerror`, `djangooptimizerextension`, `djangotype`,
  `fk-id-elision`, `metaexclude`, `metafields`, `metaoptimizer-hints`, `only-projection`,
  `optimizerhint`, `queryset-diffing` — one body use plus one definition each, so all ten remain
  single-carrier. This pass wrote no spec byte, so no carrier could move; the count is the proof
  that none did.
- **Link resolution, both files, re-derived on disk this pass** with a parser that partitions each
  file at `<!-- LINK DEFINITIONS -->`, strips code spans before scanning uses, normalizes each
  target against the file's own directory, and slugs every heading in each target to check the
  anchor: spec **11 defs / 11 used / 0 undefined / 0 unused**, rationale **24 / 24 / 0 / 0**,
  **35/35 targets exist and every anchored target's heading is present**. No definition was added or
  removed by this pass. (The parser's slugger was corrected mid-run: its first pass stripped `_`
  from headings and so mis-reported the pre-existing `../GLOSSARY.md#metaoptimizer_hints` target as
  a missing anchor. The tool was wrong, not the link — `docs/GLOSSARY.md` #"## `Meta.optimizer_hints`"
  is present. Recorded because a false negative in a verification tool is the kind of thing a later
  pass would otherwise re-derive as a defect.)
- **Provenance-claim population, re-measured after the last edit** — spec **17 lines / 23
  occurrences**, rationale **62 owner-naming occurrences**. Stated once, in `### M4` above, with the
  commands; deliberately not restated here, which is the whole of M4's lesson.
- **Sibling-citation count, unchanged at 21 occurrences across 10 siblings** in the spec
  (`grep -o 'docs/SPECS/spec-0[0-9][0-9]' <spec> | sort | uniq -c`): spec-033 x5, spec-035 x4,
  spec-003 x3, spec-002 x2, spec-018 x2, spec-015 / spec-023 / spec-029 / spec-032 / spec-047 x1
  each. (The 23-occurrence figure in `### M4` is the wider filename-form population, which also
  takes `:7`'s bare filename and the one `docs/README.md`; the two measures are different patterns
  over the same file and both are stated with their commands.)
- **`[spec-004-improvements]`, unchanged**: `grep -o | wc -l` -> **21** = 20 body uses + 1
  definition; the bare `[The eight improvements][spec-004-improvements]` form -> **17**.
- **`AGENTS.md` rule 27:** `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` -> **no match** in either file.
  The bullet this pass added cites the companion's lines by `#"unique substring"`, never by number,
  which is the reason that grep still holds after an edit that names six of them.
- **Zero fenced code blocks:** `grep -c '^```'` -> **0** in the spec and **0** in the rationale.
- **The spec narrates no history.** Re-run with a 32-alternate pattern including `this pass`,
  `drift`, `un-spec`, `re-derived`, `superseded`, `historical`, `deprecated`, `initially`,
  `now reads`, `revised`, `later spec`, `corrected`: **one** line, `:3`, R1's companion pointer,
  which describes the *rationale file's* contents and which H18 / H20 place off-limits.
- **The maintainer-ruled sentence is byte-identical to HEAD.** HEAD `:5` and working `:7` extracted
  read-only to a scratch path outside the repo: `diff` **empty**, `md5`
  `a236d060acf135d69af06a01cf43646a` on both sides.
- **Both do-not-reverse instructions re-verified after the edit.** H19: `grep -c` on line-initial
  labels -> **10** `**Claims the spec may no longer make.**`, **12** `**Claims the spec no longer
  makes.**`, plus R1's **1** deliberately-scoped stronger label. Unchanged — this pass created no
  block and levelled nothing. H20: five "The competitive argument for this slice" (spec `:41`,
  `:63`, `:81`, `:109`, `:139`), two "The opening argument for this slice" (`:119`, `:151`),
  `### B8` carrying neither. Byte-identical, and this pass wrote no spec byte.
- No `pytest` (`AGENTS.md` rule 15; this cycle changes no code). No `ruff` (neither file is Python).
  No `--cov*` flag in any command.

### Working-tree state — re-derived this pass, reported, not reverted

`HEAD` is **`ff03c1372365edcad488ff4671389d88ae145276`** (`ff03c137`), unchanged since the pass-2
apply pass moved to it, and it did not sweep this cycle's work:
`git log -1 --format=%h -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` still returns
**`20a9752f`** and all four `bld-004` / `build-004` paths are still untracked. The check was done
with `git log`, never `git status` alone.

**The list is unchanged from Worker 3's pass-3 reading — thirteen entries, the second consecutive
pass without movement:**

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
 M docs/SPECS/spec-005-django_type_contract-0_0_3.md
 D docs/builder/bld-003-final.md
 D docs/builder/bld-003-r1-rationale_move.md
 D docs/builder/bld-003-r2-spec_reconciliation.md
 D docs/builder/bld-003-r3-doc_completion_archive.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/bld-004-r2-spec_reconciliation.md
?? docs/builder/bld-005-r1-rationale_move.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
?? docs/builder/build-005-django_type_contract-0_0_3.md
```

**No new dirty entry appeared during this pass**, and nothing cleared. The four
`D docs/builder/bld-003-*.md` deletions persist and were **not** restored — `### Fifth change` makes
that the maintainer's call and `AGENTS.md` rule 34 bans the `git checkout` that would do it.
`django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`, `CHANGELOG.md`,
`docs/GLOSSARY.md`, `docs/TREE.md`, `KANBAN.md`, `KANBAN.html`, and `examples/fakeshop/db.sqlite3`
are all **clean**. R3 still re-derives rather than inherits: the list moved four times earlier in
this cycle and `HEAD` moved under it once.

### Notes for Worker 3

- **The claim to attack first is M4's replacement population, and the pattern that produces it.**
  17 lines / 23 occurrences in the spec, 62 owner-naming occurrences in the rationale. The
  filename-form pattern is the load-bearing choice: verify it excludes the `[spec-004-rationale]`
  reference id and its definition and still takes `:7`'s bare filename. If the pattern is wrong,
  the retraction in `### M4` swapped one unreproducible number for another, which is the exact
  defect it was filed for.
- **M5's widening is measured, not sampled.** The review named five sites; the population is seven,
  and the two the review did not see (`:253`, `:952`) were found by enumerating the companion's
  `spec-035` citations rather than by following the review's list. Re-run
  `grep -n '\]\[spec-035\]\|spec-035-optimizer'` over that companion and grade each of the six body
  uses independently — `:521` is the one that is only partly wrong, and treating it as wholly wrong
  would be an over-reach in the other direction.
- **The single-reader half of M5 is new evidence, not M3's carried forward.** `spec-035` was
  cleared of the *plan-immutability* contract in pass 2; the claim that it owns the
  `_prefetch_related_lookups` single-reader discipline is a separate one, settled here by
  `_consumer_prefetch_lookups` being dated 2026-05-06 and by no `docs/SPECS/` file stating the
  discipline. Both halves are worth re-deriving.
- **No spec byte changed**, so every spec-side invariant is a stability check rather than a
  re-verification: ten anchors, both do-not-reverse instructions, the maintainer-ruled sentence,
  73/196, 236 / 36,223. If any of them moved, this pass wrote something it did not report.
- **The B1 `**Directive-variable extraction.**` residue was read and agreed with, not re-opened.**
  If you disagree, the question to answer is the one in `### The DRY residue …` above: whether
  "which variables key the cache" is B1's own contract or `spec-033`'s. I concluded B1's, on the
  requirement-stays / cost-moves line, and on B1's cache key being this slice's own surface that
  `spec-033` extended rather than a sibling rule B1 consumes.

### Notes for Worker 1 (spec reconciliation)

Items 2-4, 6-14 and 16-17 of Worker 3's pass-3 list are carried forward unchanged and are not
restated. Three corrections and two additions:

1. **Correction to item 5 (the `spec-003` deferral).** It is now **seven** sites, not five, and the
   record is in the durable rationale: `spec-003` #"finalized at handoff" plus **six** body
   citations of `spec-035` in
   `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md` — `:253`, `:521`,
   `:598`, `:604`, `:855`, `:952`. Every one carries the error; only `:521`'s projection-gate item
   is sound. Both files stay read-only; whoever fixes them decides for all seven at once, the same
   ask as the `spec-029` item.
2. **Correction to item 15 (the owner-column count).** Eight rows: **D7, D9, D13, D15, D17, D20,
   D25, D26**. Worker 0 has already re-measured the build plan's own
   `**Re-measured 2026-08-08 after R2's pass-3 review**` paragraph to the same eight and added
   "Do not read the numeral as settled". Nothing further is owed to the plan.
3. **Correction to the provenance population.** The canonical figures are spec **17 lines / 23
   occurrences** and rationale **62 owner-naming occurrences**, each with its command in `### M4`.
   The pass-2 `### Notes for Worker 3` restatement (`24 / 18 / 55`) is **withdrawn**; the pass-2
   `### The provenance sweep` figures (16 / 22 / 60) remain correct for the narrower pattern they
   state and now carry the `:7` exclusion named explicitly.
4. **New, and it is a standing hazard rather than an item:** a verification tool's own false
   negative reads exactly like a defect in the file under verification. This pass's link-resolution
   parser mis-slugged `#metaoptimizer_hints` and reported a real, resolving glossary anchor as
   broken. The tool was corrected and the anchor is fine. **A pass whose checker disagrees with
   three prior passes should suspect the checker first.**
5. **Nothing new is deferred by this pass.** No contract sentence changed, no citation was added or
   removed, no link definition moved, and the deferred-work catalog inherits exactly the items
   Worker 3's pass-3 list carries, with item 5 widened as above.

---

## Review (Worker 3, pass 4)

Re-reviewed the working-tree diff against pristine `HEAD`, re-derived this pass as
**`ff03c1372365edcad488ff4671389d88ae145276`** (`ff03c137`) — unchanged since the pass-2 apply pass
moved to it. The HEAD blob was extracted read-only with `git show HEAD:<path>` into a scratch path
outside the repository. No `git stash`, `git checkout`, `git restore`, or `git worktree` at any
point. **The commit still has not swept this cycle's work**:
`git log -1 --format=%h -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` returns `20a9752f`, and
all four `bld-004` / `build-004` paths are still untracked.

**Every reported figure re-derived exactly.** Spec `wc -l -c` -> **236 / 36,223**; rationale ->
**1,309 / 94,318**; `git diff --stat` over the spec -> **73 insertions / 196 deletions**; HEAD blob
-> **359 / 33,928**. The spec is byte-identical to its pass-2 state, as the apply pass claims: same
line count, same byte count, same diff stat, and `wc -c` is the only instrument available for a file
whose companion is untracked, so it is the strongest available proof and it holds.

The spec has now been **byte-stable for a full round**, and all three pass-3 findings were record
edits. This review is a grading pass over those three, over the DRY distinction the apply pass
argued, and over the surfaces no prior pass in this cycle has read. It files nothing.

### High:

None.

### Medium:

None.

### Low:

None.

### The three pass-3 findings, graded

1. **M4 — retracted rather than repaired, and the retraction is the better answer.** My finding
   asked whether a restated figure needs to exist at all; the pass concluded it does not and
   withdrew `24 / 18 / 55` in full rather than substituting a third number. That is the right
   disposition on the standard the finding itself argued, and the prior bullet is byte-identical as
   `ARTIFACT.md` `## Re-pass sections` requires.

   **The one surviving population re-derives exactly, breakdown included.**
   `grep -cE 'spec-0[0-9][0-9]-[a-z_]+-0_0_[0-9]+\.md|docs/README\.md'` over the spec -> **17**, the
   same pattern with `-oE ... | wc -l` -> **23**, and `| sort | uniq -c` gives spec-033 x5,
   spec-035 x4, spec-002 x3, spec-003 x3, spec-018 x2, and `docs/README.md` / spec-015 / spec-023 /
   spec-029 / spec-032 / spec-047 x1 each — the claimed breakdown, entry for entry. Rationale:
   `][spec-0NN]` -> **55**, self-reference `[spec-004]` -> **1**, leaving **54**; `][docs-readme]`
   -> **3**; `][spec-002-rationale]` **2** + `][spec-003-rationale]` **2** = **4**; `][glossary]` ->
   **1**. 54 + 3 + 4 + 1 = **62**. Confirmed.

   **The claim about my own recommended command is correct, and I checked it rather than accepting
   it.** `grep -c 'spec-0[0-9][0-9]\|docs/README.md'` over the spec returns **27** lines, and the
   per-line occurrence breakdown shows the surplus is exactly what the pass says it is: the
   `[spec-004-rationale]` reference id at `:3` (x2), `:9`, every per-slice pointer paragraph, and
   the definition at `:222` (x2). My pass-3 *figures* (17 / 23) were right and my *pattern* was
   wrong. The generalizable form the pass extracted — a citation-population pattern must match the
   citation's distinguishing shape, never the bare identifier the document also uses for its own
   link ids — is the correct lesson and is the one I would have missed.

   The `:7` clause is now carried: the 17-line figure includes the bare-filename
   `` `spec-002-optimizer-0_0_2.md` `` inside the maintainer-ruled `## Problem statement` sentence,
   which is settled true (`spec-002` #"O1 through O6 have shipped", re-derived) and not editable by
   any pass. The sweep's "nothing else makes a provenance claim" is now backed rather than asserted.

2. **M5 — closed wider than the finding, and the widening is measured.** I named five sites; the
   population is seven. `grep -n '\]\[spec-035\]\|spec-035-optimizer'` over
   `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md` returns **seven
   lines** — `:253`, `:521`, `:598`, `:604`, `:855`, `:952`, plus the definition at `:1050` — so six
   body uses, and I read all six in place:

   - `:253` "Both are later hardening (`spec-035`)" — misattributes **two** things in one sentence,
     the finalize-frozenset short-circuit and the single named reader. Was on no list.
   - `:521` "`spec-035` (plan immutability, the projection gate, the private-attribute reader)" —
     **partly sound**, exactly as the pass says: the projection gate genuinely is `spec-035`
     Decision 4 (`### Decision 4 — G2 — operation-type gating of `.only()``, verified in place);
     the other two items are not.
   - `:598` "points at `spec-033` / `spec-035` for the rest" — the bare pointer, riding along.
   - `:604` "each already stated once in its own document" — the assertion `grep -c immutab` -> 0
     falsifies.
   - `:855` "discipline is `spec-035`'s to state" — the standing instruction to write the contract
     into spec-035.
   - `:952` "a tuple at HEAD, because the plan is finalized before handoff (`spec-035`)" — the tuple
     swap, which is `OptimizationPlan.finalize`'s. Was on no list.

   The pass's three-shape taxonomy (credits the work / asserts it is already stated / instructs a
   future pass to make it true) is a fair partition of those six, and calling `:521` partly sound
   rather than wholly wrong is the correct non-over-reach.

   **The new single-reader evidence is real and is not M3's carried forward.**
   `git log -S"_consumer_prefetch_lookups" -- django_strawberry_framework/optimizer/plans.py` ->
   `603e1c60`, **2026-05-06**, against `spec-035`'s own authorship (Revision 1, 2026-06-15) — six
   weeks earlier, and a different claim from the plan-immutability one pass 2 settled.
   `git log -S"def finalize"` over the same file still returns `c7447e23`, **2026-05-11**.

   **No sibling file was edited.** `git status --short` over
   `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` and its companion is **empty**,
   and `git log -1` on the companion returns `c62e990a` — untouched by this cycle. The deliverable
   is the enumeration, and the enumeration is where it belongs: the durable rationale
   (`:1236`-`:1263`), not this artifact.

   **The `#"substring"` form is correct and, unusually, verifiable.** The prompt asked me to check
   that a durable file naming six lines of another file does not reach for `path:NN`. It does not:
   the six citations are `#"Both are later hardening"`, `#"the plan is finalized before handoff"`,
   `#"plan immutability, the projection gate"`, `#"each already stated once in its own document"`,
   `#"for the rest"`, and `#"'s to state"`. I ran `grep -c -F` for each against the companion:
   **every one returns 1**, so all six are genuinely unique substrings and resolve to exactly the
   line intended — including the two short ones (`for the rest`, `'s to state`) that looked most
   likely to collide. `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over the rationale still returns **no
   match**, which is the rule-27 proof after an edit that names six line numbers' worth of content.

3. **L4 — the numeral replaced by the rows, and the rows check out.** D7, D9, D13, D15, D17, D20,
   D25, D26. I read the build plan's owner cells for the three the pass-2 sweep did not connect:
   `D15` reads "spec-033 / spec-046" for `OptimizerHint.strategy`, `D25` reads "spec-033 (subtree
   awareness) + spec-035 (the stance)", `D20` reads "spec-032 (Relay interfaces)" — all three are
   the cells the four new misattributions came out of. Worker 0's
   `**Re-measured 2026-08-08 after R2's pass-3 review**` paragraph already carries the same eight
   rows and the "do not read the numeral as settled" clause, so nothing is owed to the plan. A row
   list is checkable and a numeral is only believable; this is the right shape.

### DRY findings

- **The distinction the apply pass drew on the `**Directive-variable extraction.**` residue is
  sound, and `spec-033`'s own text corroborates it in a way the pass did not claim.** The argument
  offered is that B2's ordering invariant was `spec-003`'s rule B2 merely consumes, whereas *which
  variables key B1's cache* is this slice's own surface that `spec-033` Decision 7 extended, so
  `spec-002` #"each own the surface they added" runs the other way. I read Decision 7 end to end
  (`spec-033` `### Decision 7 — Plan-cache key hygiene: nested pagination variables hash, root
  pagination arguments do not`, seven sub-bullets, a justification, three rejected alternatives)
  against spec-004 `:29`, and the distinction holds on two independent grounds:

  - **Direction of ownership.** Decision 7's opening sentence is "`_build_cache_key` **gains**
    pagination-variable collection ... fold those variables' values into the **existing**
    `relevant_vars` frozenset", and its justification closes "preserving B1's 'variable filtering'
    property". Decision 7 describes itself as an addition to a key spec-004 owns. A section that
    states its own key's components is not absorbing.
  - **The asymmetry argument runs spec-004 -> spec-033, not back.** Decision 7's over-collection
    bullet ends "The same asymmetry argument **the directive-variable collection already encodes**"
    — i.e. spec-033 credits that argument to spec-004's B1. So the one paragraph of B1 that most
    resembles Decision 7 is the paragraph Decision 7 says it inherited. That is the mirror of the
    absorption test, and it clears.

  What remains arguable is the two causal clauses ("bake into windowed prefetch querysets", "root
  slicing happens after the plan is applied"), one clause each against Decision 7's seven
  sub-bullets — not a transplanted paragraph, and L1's lesson (a reasonless rule invites the change
  it exists to prevent) cuts against removing them. **Agreed, no edit, and this is now the second
  independent pass to reach that conclusion from the evidence rather than from the other's record.**
  It should not be re-opened without new evidence.

- **Examined and NOT flagged: the two byte-identical immutability sentences at `:35` and `:169`.**
  Unchanged from pass 3's disposition and unchanged by this pass. `### B1` states why no
  invalidation is needed, `### B8` why the reconciliation must copy; a repeated **negative** claim is
  the low-risk direction, and a grep for the sentence finds both if a sibling ever claims the
  enforcement.

- **This pass introduced no duplication because it changed no contract sentence.** One rationale
  bullet widened, no link definition added or removed (24 defs before and after), no new section.

- **No existence challenge to raise.** The item creates no abstraction, helper, registry, token, or
  indirection layer.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty**. `__all__` and the re-export list
are unchanged. `git status --short -- django_strawberry_framework/ tests/ examples/ scripts/` ->
**empty**: no source, test, example, or script file changed in this cycle, as the build plan's
`## Build-wide context flags` requires. No correctness defect in shipped optimizer code was found by
this pass either, so nothing is escalated under that heading.

`scripts/review_inspect.py` was **not run, and the skip is recorded here with its reason**:
`BUILD.md` `### When to run the helper during build` scopes Worker 3's obligation to slices that add
or touch `.py` files, and this cycle's diff contains none. Recorded rather than silent, per that
section's own instruction.

### CHANGELOG sanity

Not applicable; item did not modify `CHANGELOG.md`. Confirmed by `git status --short -- CHANGELOG.md`
-> empty.

### Documentation / release sanity

Applies — the diff is an archived spec and its rationale companion.

- **Version strings and card IDs.** The spec carries no version or status line and none was added;
  `## Implementation checklist` still carries all eleven `- [x]`, matching `DONE-004-0.0.3`. No
  KANBAN card moved and no release metadata changed.
- **The archive is intact.** Spec at `docs/SPECS/`, companions at `docs/SPECS/appx/`.
  `spec-004-optimizer_beyond-0_0_3-terms.csv` is untouched; `git status --short docs/SPECS/appx/`
  reports only the two untracked rationale files (spec-004's and the concurrent cycle's spec-005).
- **Every link definition resolves on disk, re-derived this pass** with my own parser (partitions
  each file at `<!-- LINK DEFINITIONS -->`, strips code spans before scanning uses, normalizes each
  target against the file's own directory, slugs every heading in each target and checks the anchor
  against that set — the slugger keeps `_`, which is what the apply pass's own first draft got
  wrong): spec **11 defs / 11 used / 0 undefined / 0 unused**, rationale **24 / 24 / 0 / 0**,
  **35/35 targets exist and every anchored target's heading is present**, including
  `../GLOSSARY.md#metaoptimizer_hints`. No definition was added or removed by this pass.
- **No inbound anchor breakage.** `grep -rln "spec-004-optimizer_beyond-0_0_3.md#" --include="*.md" .`
  hits only this cycle's own files. `## Proposed improvements` survives in the rationale at exactly
  **2** places and **0** in the spec (`grep -c "Proposed improvements"` -> 0); both survivors are
  correctly historical and must not be "fixed".
- **No obsolete staging wording.** `grep -c` in the spec: "Proposed improvements" **0**, "Can be
  spec'd now" **0**, "when B4 ships" **0**, "check_optimizer" **0**.
- **No script-rendered doc touched.** `docs/TREE.md`, `docs/GLOSSARY.md`, `KANBAN.md`,
  `KANBAN.html`, `examples/fakeshop/db.sqlite3` all clean; no docstring feeds this change.
- **Verbatim-copy check** reduces to the maintainer-ruled sentence, verified below.

### Re-confirmed invariants — every one re-derived this pass, none quoted

| Check | Command | Result |
|---|---|---|
| Glossary terms | `check_spec_glossary.py --spec <spec>` | `OK: 10 terms - all have glossary entries and at least one spec link.` exit **0** |
| Layout / scaffold | `check_trailing_commas.py --check <spec> <rationale> <this artifact>` | exit **0**, all three |
| Card glossary chain | `manage.py import_spec_terms --check` (read-only form only) | `OK: 49 done cards have glossary links.` exit **0** |
| Fenced blocks | `grep -c '^```'` | **0** in spec, **0** in rationale |
| `AGENTS.md` rule 27 | `grep -nE '[a-zA-Z_/]+\.(py\|md):[0-9]+'` | **no match** in either file |
| Maintainer-ruled sentence | `diff` HEAD `:5` vs working `:7`; `md5` | `diff` **empty**, `a236d060acf135d69af06a01cf43646a` both sides |
| Source / test / example / script | `git status --short -- django_strawberry_framework/ tests/ examples/ scripts/` | empty |
| Sibling spec / rationale | `git status --short` over the `spec-003` pair | empty; `git log -1` on the companion -> `c62e990a` |

**The ten anchors, re-derived per anchor.** `grep -o "glossary-<anchor>]" <spec> | wc -l` returns
exactly **2** for every one — `configurationerror`, `djangooptimizerextension`, `djangotype`,
`fk-id-elision`, `metaexclude`, `metafields`, `metaoptimizer-hints`, `only-projection`,
`optimizerhint`, `queryset-diffing`. This pass wrote no spec byte, so the count is a stability
proof rather than a placement re-verification; I re-read the two highest-risk carriers anyway
(`djangooptimizerextension` at `:33`, `metafields` / `metaexclude` together at `:131`) and both sit
in contract prose.

**The spec narrates no history — re-run with my own alternation.** Thirty-one alternates including
`this pass`, `drift`, `re-derived`, `un-spec`, `superseded`, `historical`, `deprecated`, `stale`,
`obsolete`, `initially`, `now reads`, `revised`, `later spec`, `corrected`, `retract`. **One** line:
`:3`, R1's companion pointer, which describes the *rationale file's* contents and which H18 / H20
place off-limits.

**Both do-not-reverse instructions still hold.** H19: line-initial labels -> **10**
`**Claims the spec may no longer make.**`, **12** `**Claims the spec no longer makes.**`, plus R1's
**1** deliberately-scoped stronger label. Nothing levelled. H20, read in the spec rather than
counted from the record: five "The competitive argument for this slice" (`:41`, `:63`, `:81`,
`:109`, `:139`), two "The opening argument for this slice" (`:119`, `:151`), `### B8` carrying
neither. Un-levelled.

### My own sweep — four surfaces no prior pass in this cycle read

Every pass here has found the defect where no prior sweep looked, so I picked surfaces by what the
record shows was never opened rather than by re-walking what was.

1. **The twenty-three closing claims blocks, tested as falsifiable assertions.** Every block asserts
   the spec no longer makes claim X, and no pass has tested them against the spec. I greped the spec
   for each retracted claim's distinctive token: `Literal` **0**, `_optimizer_field_map` **0**,
   `check_optimizer` **0**, `namedtuple` **0**, `weakref` **0**, `skip Strawberry` **0**,
   `lru_cache.cache_info` **0**, `classmethod` **0**, `three-tuple` **0**, `blindly stacks` **0**,
   `Proposed` **0**. The two non-zero tokens are both legitimate: `_optimizer_hints` x2 are the real
   symbols `_validate_optimizer_hints` and `_resolve_optimizer_hints`, and `get_fields()` x3 are
   B6's exposed-fields contrast and B7's dual-contract fallback, which the spec states on purpose.
   `proposal` appears once, at `:3`, inside the companion pointer describing the rationale's
   contents. **Every retraction holds.**

2. **The spec's negative and exclusivity claims, which are the shape a later commit silently
   falsifies.** `:35` / `:169` "No sibling spec states that enforcement" — tested tree-wide, not
   just against `spec-035`: `grep -rn '_assert_under_construction' docs/SPECS/` hits spec-004 only,
   and the one adjacent claim, `spec-033:458`, reads "the finalize-to-tuple discipline ... (**B1
   cache-immutability property**, re-affirmed by the Slice-3 tests)" — it credits back to spec-004
   and states no contract. `:147` "one canonical store, no class-attribute mirror of it anywhere" —
   `grep -rn _optimizer_field_map --include="*.py" django_strawberry_framework/` -> **0**. B4's "The
   API surface is one import" — `OptimizerHint` is imported at `__init__.py:33` and listed in
   `__all__` at `:148`. B6's "`check_schema` always returns warnings — it does not raise" — the body
   appends and returns, and its docstring says the same. B5's "The whole family is cleared at the
   start of each execution" — `extension.py::DjangoOptimizerExtension.on_execute` calls
   `_clear_optimizer_context` **before** it sets any token, and its comment names the leak it
   prevents. **All hold.**

3. **The three sections the reconciliation barely touched and no review has read end to end** —
   `## Non-goals`, `## References`, `## Implementation checklist`. The checklist's eleven boxes all
   name shipped surface. `## References`' three clauses are each correct after S7's and D27's fixes.
   One residue in `## Non-goals`, recorded not filed under `### What looks solid`.

4. **The spec's concrete format claims, spot-checked against source rather than against the record.**
   B3's sentinel example `ItemType.category@allItems.category` matches
   `optimizer/plans.py::resolver_key` exactly (`f"{parent_type.__name__}.{field_name}@{path}"` with
   `path = ".".join(runtime_path)`), and the `parent_type is None` arm produces the bare
   `field@path` form the spec does not claim. **A test written from that sentence pins what the
   package emits** — which is the S4 failure inverted, and it passes.

Nothing in any of the four is actionable.

### What looks solid

- **Retracting `24 / 18 / 55` rather than replacing it is the strongest call in this pass**, and the
  rule it extracted — state a count once and point at it — is the generalizable form of the defect
  this cycle has now met six times. A third number would have been the seventh.
- **M5's widening was measured, not sampled, and it corrected my finding in both directions.** It
  found two sites I missed (`:253`, `:952`) *and* declined to call `:521` wholly wrong when only two
  of its three items are. A pass that only ever widens is not grading; this one did both.
- **The record and the files agree everywhere I tested them.** `### Spec changes made (Worker 1
  only)` says "None" and the spec is byte-identical; `### Files touched` says one rationale edit and
  the definition count is unmoved at 24; `git diff --stat` is unchanged at 73/196 because no spec
  byte was written. Each was confirmed rather than assumed.
- **The `#"substring"` discipline was applied where it is hardest and it survives verification.**
  Naming six lines of another document without a line number is exactly where a pass reaches for
  `path:NN`; this one did not, and all six substrings are unique in the target.
- **Two residues examined at length and deliberately NOT filed**, recorded with the standard I
  judged them against so a later pass neither re-derives them nor reads silence as an unexamined
  area:
  - **`## Non-goals` says Layer-3 features "have their own specs", and aggregates does not have
    one.** Filters (`spec-027`), orders (`spec-028`) and permissions (`spec-034`) do; aggregates is
    still a backlog item with no spec, as `START.md` records for the beta line. This is
    HEAD-preserved text, on no drift row, and never rewritten by this cycle. Not filed because the
    sentence's imperative — "this spec does not cover them" — is true, and no reader takes a wrong
    action from it; the surplus is one clause of colour on a scope statement.
  - **`### M4`'s account of my own pass-3 command says it returns 27 lines / 34 occurrences; it
    returns 27 / 35.** The line figure is right, the load-bearing claim is right (I verified the
    surplus is the `[spec-004-rationale]` reference id), the command is stated so a reader
    re-derives it in one step, and the conclusion — use the filename form — is unaffected by either
    number. Not filed on the same standard pass 3 applied to the `Meta.interfaces` 16-versus-15
    figure: a colour figure beside a verified proof is not a finding, and filing it would buy one
    numeral in a per-cycle scratchpad at the price of a full apply-and-review round.
- **Three residues carried from prior passes, still deliberately unfiled and unchanged:** `## Current
  state`'s "effective end-to-end" (HEAD's own unfalsifiable wording), `### B7`'s "Benchmark
  (optional)" (marked optional, never a delivery claim), and the rationale's `## How to read this
  file` bullet 8 (scoped to the extraction pass by its own first three words).

### Temp test verification

No temp tests were created. `docs/builder/temp-tests/r2/` was not used and `docs/builder/temp-tests/`
is empty (`ls` confirms). This item changes no code and introduces no boundary, guard, gate, or
rejection path, so `BUILD.md` `### What needs a proof, and what does not` scopes it out of the
failability-proof mechanism entirely and **the mandatory re-run floor is legally empty** — the diff
introduces no boundary that meets it, which is the only condition under which an empty re-run set is
legal. Verification here was read-and-re-derive against source, against the read-only HEAD blob, and
against `git log -S` over each disputed symbol. No `pytest` was run (`AGENTS.md` rule 15) and no
`--cov*` flag appears in any command in this pass.

### Working-tree state — re-derived this pass, reported, not reverted

`HEAD` is **`ff03c137`**, unchanged. **One new entry since the apply pass's closing reading**, the
concurrent card-005 cycle's:

```
?? docs/builder/bld-005-r2-spec_reconciliation.md
```

That cycle has opened its own R2 while this one was reviewing. **It is not in this cycle's writable
set, nothing here reads it, and nothing was touched.** Worker 0 appends it. Fourteen entries:

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
 M docs/SPECS/spec-005-django_type_contract-0_0_3.md
 D docs/builder/bld-003-final.md
 D docs/builder/bld-003-r1-rationale_move.md
 D docs/builder/bld-003-r2-spec_reconciliation.md
 D docs/builder/bld-003-r3-doc_completion_archive.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/bld-004-r2-spec_reconciliation.md
?? docs/builder/bld-005-r1-rationale_move.md
?? docs/builder/bld-005-r2-spec_reconciliation.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
?? docs/builder/build-005-django_type_contract-0_0_3.md
```

The four `D docs/builder/bld-003-*.md` deletions persist and were **not** restored — the build
plan's `### Fifth change` makes that the maintainer's call and `AGENTS.md` rule 34 bans the
`git checkout` that would do it. `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`,
`CHANGELOG.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, `KANBAN.md`, `KANBAN.html`, and
`examples/fakeshop/db.sqlite3` are all **clean**. `import_spec_terms --check` was re-run at this tree
state and still returns `OK: 49 done cards have glossary links.`

### Notes for Worker 1 (spec reconciliation)

**This is the complete R3 handoff, re-issued in full and in its current state. Nothing lives only in
a closed section**, so every item from the item's own list, from all four reviews, and from all three
apply passes is restated here rather than cross-referenced; R3's dispatch is built from this list
alone. Items that are finished are marked **CLOSED** and carry what closed them, so a reader can tell
a discharged item from a live one without opening a prior section.

1. **CLOSED — no finding is open.** R2 carried five findings at pass 1, two at pass 2, three at
   pass 3; all ten are fixed, none rejected, and this pass files none. There is nothing for a further
   apply pass to apply. `Status:` is `review-accepted`, which routes to Worker 1's final
   verification, not back to an apply pass.
2. **Deferred, for the final gate's `### Deferred work catalog`:** the `check_optimizer` management
   command and custom-resolver detection (D21 / S5) — named as B6 follow-up work eleven versions
   ago, never built, and **no card exists for either**. Dropped from the spec by the item and
   recorded in the rationale. `inspect_django_type` (`spec-029`) answers a different question and is
   explicitly not offered as a substitute. Re-verified this pass: `grep -c check_optimizer` -> 0 in
   the spec, and `django_strawberry_framework/management/commands/` ships `export_schema` and
   `inspect_django_type` only.
3. **Deferred:** the `_record_relation_access`-before-elision ordering invariant still has **no
   automated guard** in `walker.py::_plan_select_relation`. Adding one is a source change and out of
   scope for a documentation cycle. The spec points at `spec-003` for both the rule and its cost,
   which after the pass-1 DRY fix is the most a docs cycle can do.
4. **Deferred, sibling-spec staleness (1 of 2):**
   `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` calls `0.316.0` "the locked" Strawberry
   version; it is the **declared floor** (`pyproject.toml` #"strawberry-graphql>=0.316.0") and
   `uv.lock` resolves higher. This cycle's own rationale phrasing was corrected (H17); sibling specs
   are read-only here with no declared exception, so the two documents disagree — the state R3 or a
   future spec-029 cycle inherits. R1's handoff item 17 asked that whoever tightens it decide for
   both documents at once. Re-verified live this pass: the phrasing is still there.
5. **Deferred, sibling-spec staleness (2 of 2) — the enumeration is now COMPLETE at seven sites and
   lives in the durable rationale; the FIX is still owed by whoever owns those files.**
   `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` #"finalized at handoff" makes the
   wrong `spec-035` plan-immutability attribution M3 caught, and its companion
   `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md` carries **six**
   body citations of `spec-035` (`:253`, `:521`, `:598`, `:604`, `:855`, `:952`), every one of which
   carries the error; only `:521`'s projection-gate item is sound. I re-derived the population and
   read all six in place this pass. Both files are read-only in this cycle and **were not edited**.
   Whoever fixes them decides for all seven at once, the same ask as item 4.
6. **Deferred:** three B7 test names in `tests/optimizer/test_field_meta.py`
   (`::test_optimizer_field_map_populated`, `::test_optimizer_field_map_contains_relations`,
   `::test_optimizer_field_map_respects_fields_filter`) still spell the retired
   `_optimizer_field_map`. Live code, carded on `TODO-ALPHA-052-0.1.0`, not this cycle's; no test
   file is writable here. Re-verified this pass: all three names are still at those symbols.
7. **For R3's durable-doc audit — the spec names ten sibling specs by path, as code spans, not
   reference-style links.** **21 occurrences across 10 siblings** by the `docs/SPECS/spec-0NN`
   pattern (spec-033 x5, spec-035 x4, spec-003 x3, spec-002 x2, spec-018 x2, and spec-015 /
   spec-023 / spec-029 / spec-032 / spec-047 x1 each). The **wider provenance population**, which
   also takes `:7`'s bare filename and the one `docs/README.md`, is **17 lines / 23 occurrences**
   (`grep -cE 'spec-0[0-9][0-9]-[a-z_]+-0_0_[0-9]+\.md|docs/README\.md'`). Both re-derive; they are
   two patterns over one file and each is stated with its command. The convention is deliberate —
   it matches `spec-003`'s and spec-004's own pre-existing `## Problem statement` / `## Non-goals`
   style, keeps the spec's link-definition block at 11 entries, and is **not** a scaffold violation.
   R3's cross-reference sweep must not "fix" them into reference-style links.
8. **For R3:** the section heading `## Proposed improvements` no longer exists; it is
   `## The eight improvements`, anchor `#the-eight-improvements`. My own tree-wide
   `grep -rln "spec-004-optimizer_beyond-0_0_3.md#" --include="*.md" .` confirms **no external
   consumer** links a spec-004 heading anchor — the only hits are this cycle's own files. The two
   remaining old-spelling occurrences in the rationale are both correctly historical and **must not
   be "fixed"**.
9. **For R3:** `bld-004-r1-rationale_move.md` records `#proposed-improvements` as resolving; that
   heading no longer exists. It is a closed per-cycle scratchpad, exempt from the symbol-path rule
   and regenerated by the next cycle, so it is left alone — recorded only so R3's cross-reference
   sweep does not read it as live rot.
10. **For R3's re-derivation duties, with expiry noted.** My readings — 35/35 link targets resolve,
    `import_spec_terms --check` green, ten anchors single-carrier, `check_spec_glossary` green,
    `db.sqlite3` clean, the working-tree list at fourteen entries — are current at `ff03c137` and
    **have an expiry**. R3 re-runs each itself, re-runs `import_spec_terms --check` **after** any
    further concurrent DB write, and attributes any dirty `db.sqlite3` by `iterdump()`
    set-difference rather than by file bytes.
11. **New out-of-scope files, for Worker 0's `## Baseline-dirty out-of-scope files`:** the concurrent
    card-005 cycle's `build-005-django_type_contract-0_0_3.md`,
    `docs/SPECS/spec-005-django_type_contract-0_0_3.md` (modified),
    `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md`,
    `bld-005-r1-rationale_move.md`, and — **new this pass** —
    `docs/builder/bld-005-r2-spec_reconciliation.md`. Plus the four `D docs/builder/bld-003-*.md`
    deletions, which persist and are the maintainer's call per `### Fifth change`. R3 must not read
    `docs/builder/` or `docs/SPECS/` as clean.
12. **The `## How to read this file` claims-block definition now defines two block kinds.** A future
    pass adding a third kind of closing block must extend that bullet in the same edit — the defect
    M1 caught was a definition left behind by a label, and the definition is the index a reader
    consults first.
13. **Two behaviours in this spec have no owner anywhere, deliberately.** The plan-immutability
    enforcement (`optimizer/plans.py::OptimizationPlan.finalize` / `::_assert_under_construction`)
    and the once-per-row resolver-key threading are stated with their symbols and no citation. I
    re-tested this tree-wide rather than against `spec-035` alone:
    `grep -rn '_assert_under_construction' docs/SPECS/` hits spec-004 only, and `spec-033`'s
    "finalize-to-tuple discipline" line credits the property back to spec-004 B1 rather than
    claiming it. If a future spec claims either, spec-004's sentences are the ones to update.
14. **`HEAD` is `ff03c137` and has not moved across the last two passes.** Worker 0 should record
    the hash change on the plan. The standing lesson holds: a plan's baseline-dirty list is a
    snapshot, and this cycle has watched it move five times and watched `HEAD` move under it once.
15. **CLOSED — the drift table's owner column produced errors on eight rows** (D7, D9, D13, D15,
    D17, D20, D25, D26), and Worker 0's `**Re-measured 2026-08-08 after R2's pass-3 review**`
    paragraph in the build plan already carries the same eight rows plus "Do not read the numeral as
    settled". I verified the three newly-connected cells (D15, D20, D25) against the table itself.
    Nothing further is owed. The remedy is unchanged and correct: treat an owner cell as a
    hypothesis and settle it with `git log -S` over the symbol.
16. **CLOSED — the `### B1` `**Directive-variable extraction.**` DRY residue.** Examined by pass 3,
    re-examined independently by the apply pass, and re-examined a third time here from
    `spec-033` Decision 7's own text. It stays. Two new pieces of evidence are on record for anyone
    tempted to re-open it: Decision 7 describes itself as *gaining* pagination collection on
    spec-004's existing frozenset, and it credits the over-collection asymmetry argument back to
    "the directive-variable collection" — i.e. to B1. **Do not re-open without new evidence.**
17. **No correctness defect in shipped optimizer code was found by any of the four passes.**
    Everything traced this pass — `resolver_key`, `on_execute`'s start-of-execution clear,
    `check_schema`'s return contract, `OptimizerHint`'s re-export, `OptimizationPlan.finalize`,
    `_assert_under_construction`, `_consumer_prefetch_lookups` — behaves as the reconciled spec
    states. Nothing is escalated to the maintainer under `## Build-wide context flags`'
    read-only-audit rule.
18. **Standing hazard, carried from the apply pass and worth keeping:** a verification tool's own
    false negative reads exactly like a defect in the file under verification. The apply pass's
    link-resolution parser mis-slugged `#metaoptimizer_hints` and reported a real, resolving glossary
    anchor as broken. My own parser keeps `_` and resolves it. **A pass whose checker disagrees with
    every prior pass should suspect the checker first.**

### Review outcome

`review-accepted`.

**R2's deliverable is complete.** Worker 1's final-verification pass is confirming a finished item,
not a partially-corrected one: every finding this review round raised — five at pass 1, two at
pass 2, three at pass 3 — is fixed, none was rejected, and this pass files nothing. There is no
open High, Medium, Low, or DRY finding, nothing is escalated under the
`review-accepted`-with-escalation carve-out, and every deferred item in the handoff above is a
recorded deferral rather than an unaddressed one.

**Why this pass files nothing rather than manufacturing a fourth round.** The three pass-3 findings
were all closed on their correct halves and each was re-derived independently here rather than
graded against the record: M4's surviving population reproduces exactly with its stated command
including the per-spec breakdown, and the retraction — deleting a second measure rather than
substituting a third number — is the better answer to the finding than the finding asked for. M5
came back **wider** than I filed it (seven sites, not five) and more precisely (`:521` correctly
called partly sound), lives in the durable rationale rather than in this scratchpad, cites six lines
of a read-only sibling by unique `#"substring"` rather than by line number, and edited no sibling
file — all of which I verified rather than accepted. L4 replaced a numeral with the eight rows, and
Worker 0's plan already carries the same eight. The DRY distinction the apply pass drew is sound and
`spec-033` Decision 7's own text corroborates it twice over.

**And I swept where no prior pass looked.** The twenty-three closing claims blocks, tested as
falsifiable assertions against the spec — every retraction holds. The spec's negative and
exclusivity claims, tested tree-wide rather than against the one sibling each names — all hold. The
three sections the reconciliation barely touched and no review had read end to end. And the spec's
concrete format claims traced to source, where B3's sentinel example matches `resolver_key`'s
`f"{parent_type.__name__}.{field_name}@{path}"` exactly. Two residues came out of that sweep and
both are recorded in `### What looks solid` with the standard they were judged against rather than
filed: `## Non-goals`' "have their own specs" over-claiming for aggregates, and one off-by-one
colour figure inside `### M4`'s own correction. Neither makes a wrong action available to a reader
who follows the sentence's imperative, and nothing durable depends on either.

Every invariant re-derived and held: 236 / 36,223 and 1,309 / 94,318, 73/196, HEAD blob 359 /
33,928, 17 lines / 23 occurrences and 62 owner-naming occurrences, 21 citations across 10 siblings,
21 = 20 + 1 and 17 bare for `[spec-004-improvements]`, 10 + 12 + 1 labels, ten anchors at exactly
two occurrences each, 11/11 and 24/24 link definitions with 35/35 targets and every anchor
resolving, zero fenced blocks, zero rule-27 violations in either durable file, the maintainer-ruled
sentence byte-identical at `a236d060acf135d69af06a01cf43646a`, both do-not-reverse instructions
un-levelled, `check_spec_glossary` / `check_trailing_commas` / `import_spec_terms --check` all
green, **no source, test, example, or script file changed, and no sibling spec or sibling rationale
edited.**

Per `ARTIFACT.md` `## Status field ownership` this routes to **Worker 1** for final verification.

---

## Final verification (Worker 1)

The last pass on this item. Worker 3's pass-4 review set `review-accepted` with zero findings — the
first pass of the round to file nothing — so this pass confirms a finished item rather than a
partially-corrected one. **Every prior section of this artifact is unedited** apart from the
`Status:` line, which is the field's own owner-updated value; the two corrections this pass owes to
prior sections are stated here rather than by rewriting them, exactly as L2, L3, M4 and L4 were.

Plan declarations, unchanged and owed nothing: ownership partition `none; sequential residual
items`; hot-path `none`; floor-verification scope `none`. No `--cov*` flag was used in any command,
and no `pytest` was run.

- **Dispatched findings checklist:** **54** boxes, **54** ticked, **0** left `- [ ]` — so no
  deferral reason is owed under `worker-1.md` `## Final verification job` step 3. Every tick audited
  below; none un-ticked, none over-ticked, and none added (no landed box was left open).
- **Row-by-row disposition:** complete. **28** rows, `D1` through `D28`, each carrying both a
  *Verified at HEAD* cell and a *Disposition* cell. Measured, not eyeballed:
  `sed -n '144,174p' <artifact> | grep -c '^| D'` -> **28**, and the extracted ids are `D1 D2 … D28`
  with no gap and no repeat.
- **DRY check across this item and against R1's output:** clean; nothing new. Detail below.
- **Existing tests still pass:** this cycle changed no code, so the honest form is confirming
  nothing was touched. `git diff --stat -- django_strawberry_framework/ tests/ examples/` -> **empty**
  and `git status --short -- django_strawberry_framework/ tests/ examples/ scripts/` -> **empty**.
  No focused run was owed and none was made; the full sweep is the final gate's job.
- **Spec reconciliation:** the spec needs **no further Worker 1 edit**. Argued below, with R3's
  scope kept separate.
- **Final status:** `final-accepted`.

### The checklist audit — every tick settled against the file, not against the record

Re-derived this pass with the boxes' own tokens rather than by re-reading prior passes' accounts.

**The retractions, tested as falsifiable assertions.** A box claiming a false claim was removed is
disproved by one occurrence. `grep -c` over the spec: `_optimizer_field_map` **0** (D22),
`check_optimizer` **0** (D21, S5), `weakref` **0** (S3), `Literal` **0** (S1), `namedtuple` **0**
(S8), `three-tuple` / `3-tuple` **0** (D3), ``mirrors `lru_cache`` **0** (D8), `cached_property`
**0** (D5), `clean fallback` **0** (D11), `custom resolver that bypasses` **0** (S5), `suggested
fix` **0** (S6), `skip Strawberry` **0** (D27), `blindly stacks` **0** (H12), `Proposed
improvements` **0** (D1), `Can be spec'd now` **0**, `when B4 ships` **0** (D15). The two surviving
`_optimizer_hints` matches are the real symbols `_resolve_optimizer_hints` (`:103`) and
`_validate_optimizer_hints` (`:105`), which is D16 and D17 landing rather than surviving.
`Priority and ordering` returns **1** — `:3`, R1's companion pointer naming the *former* section as
content of the rationale file, which H18 / H20 place off-limits and which is not the heading (D28).
- **H6 held, and it is the one do-not-restore that needed a HEAD comparison rather than a grep.**
  The claim R1 deleted is HEAD `:241`'s "No `_meta.get_fields()` call ever appears in the request
  path"; it is absent from the working spec. The three surviving `get_fields()` mentions (`:131`,
  `:147`, `:149`) are B6's exposed-fields contrast and B7's dual contract, which the spec states on
  purpose (D23). Nothing was restored.

**The additions, read in place.** The five cache-key components are five bullets at `:21`-`:25`
(D3); the deferred-conversion thunk is `:27` (D27); the second variable family and the
over-collection rule are `:29`-`:31` (D4); the 256 bound, ordered-dict storage and quarter eviction
are `:33` (D6) and reproduce in source (`extension.py` `_MAX_PLAN_CACHE_SIZE = 256`,
`self._plan_cache: OrderedDict[...]`, `to_remove = max(1, _MAX_PLAN_CACHE_SIZE // 4)` with
`popitem(last=False)`); structural immutability plus the three further memos are `:35`-`:37` (D7),
and both named symbols resolve (`plans.py` `def finalize`, `def _assert_under_construction`);
`cache_info()`'s three-member tuple and best-effort counters are `:39` (D8); the composite-PK
exclusion is `:53` (D10); the fifth hint member is `:97` (D15); `_validate_optimizer_hints` with the
excluded/scalar gate is `:105` (D17); the union / interface descent and the `(model, field name)`
dedupe are `:129` / `:133` (D19, D20); `field_map` as the one canonical store is `:147`-`:149` (D22,
D23, S8); the `(plan, queryset)` pair with the upgrade and prune steps is `:165`-`:167` (D26); the
three named strictness levels validated at construction is `:79` (S1), matching
`extension.py` `strictness: str = "off"`; `check_schema` as a **static** method is `:127` (H3),
matching the `@staticmethod` at `extension.py:1247`.

**The structural rows, discharged by R1 and verified rather than performed** (H2, H7). The heading
list is `## Problem statement`, `## Current state`, `## The eight improvements`, then `### B1` …
`### B8` in order, then `## Non-goals`, `## References`, `## Implementation checklist`. All eight
B-slices sit under one parent heading (D24) and `## Priority and ordering` is gone as a heading
(D25's carrier clause, D28).

**The method obligations** (H13, H14, H15) are discharged in each pass's `### Validation run` and
re-discharged in this pass's, below: every figure here was produced by running the command and
pasting its output after the last edit, never quoted from a prior pass.

**The two do-not-reverse instructions, and one new piece of evidence for H19.**
- **H19 — the modal-label divergence.** Line-initial counts over the rationale: **10**
  `**Claims the spec may no longer make.**`, **12** `**Claims the spec no longer makes.**`, plus
  R1's **1** deliberately-scoped stronger label at `:177`. Unchanged. **It is recorded durably, in
  the rationale rather than only here** — `## How to read this file` `:30`-`:47` defines both kinds,
  says which section carries which and why, points at the `**On the label.**` preamble at `:810`,
  and states outright that "neither spelling may be levelled to the other". New evidence that the
  record covers the *sibling* direction the instruction was written about, which no prior pass
  measured: `grep -c '^\*\*Claims the spec no longer makes\.\*\*'` over
  `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` and
  `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md` returns **8** in
  each, and the modal form returns **0** in each. **The sibling form IS the factual spelling**, so a
  sweep harmonizing spec-004's modal blocks to the siblings would be levelling the modal to the
  factual — precisely what the durable bullet forbids. The instruction survives without needing the
  siblings named.
- **H20 — the five/two per-slice pointer asymmetry.** Read in the spec, not counted from the
  record: five "The competitive argument for this slice" (`:41`, `:63`, `:81`, `:109`, `:139`), two
  "The opening argument for this slice" (`:119`, `:151`), `### B8` carrying neither. Recorded
  durably in the rationale at `:796`-`:798`: "B5's and B7's paragraphs name no competitor and the
  others' do. The asymmetry is deliberate: a harmonizing sweep must not level it back." Both
  instructions are therefore in the file that outlives the cycle, not only in this scratchpad.

**H9 — the maintainer-ruled sentence.** HEAD `:5` and working `:7`, extracted read-only with
`git show HEAD:<path>` into a scratch path **outside** the repo: `diff` **empty**, `md5`
**`a236d060acf135d69af06a01cf43646a`** on both sides. No `git stash`, `git checkout`, `git restore`,
or `git worktree` anywhere in this pass.

**Two corrections to prior sections, issued here because `ARTIFACT.md` `## Re-pass sections` forbids
editing them.** Both are numerals inside this per-cycle scratchpad; both conclusions stand.

1. **`## Review (Worker 3)` `### Dispatched findings checklist — walked` says "All **56** boxes".
   It is **54**** — 28 `D` rows + 18 `H` items (H1-H9, H11-H15, H17-H20) + 8 `S` findings.
   Measured: `grep -c '^- \[x\]'` over the checklist block -> **54**, `grep -c '^- \[ \]'` -> **0**,
   and the extracted ids enumerate exactly those 54. The review's own load-bearing claim — every box
   ticked, none without a matching change or a recorded decided non-edit — is unaffected, and its
   companion arithmetic in the same section ("eighteen boxes plus two recorded closures" for the
   twenty handoff items) is right. This is the same shape as L3 and M4: a population stated from
   memory beside a conclusion that was actually derived.
2. **`### M4` says Worker 3's pass-3 command returns "27 lines / 34 occurrences". It returns
   27 / 35.** Worker 3's pass-4 `### What looks solid` spotted this and deliberately did not file
   it; I re-derived it rather than accepting either reading:
   `grep -c 'spec-0[0-9][0-9]\|docs/README.md'` over the spec -> **27**, and
   `grep -o … | wc -l` -> **35**. The line figure, the load-bearing claim (the surplus is the
   `[spec-004-rationale]` reference id the pattern also matches), and the conclusion (use the
   filename form) are all unaffected. **Disposition: corrected here and routed nowhere.** It is a
   colour figure in a scratchpad that closes with the cycle, nothing durable depends on it, and it
   is not R3's to act on — R3 does not read this artifact's arithmetic, it reads the handoff list.

### The 18-item R3 handoff — audited as R3's input, item by item

Worker 3's pass-4 `### Notes for Worker 1` is the list R3's dispatch is built from verbatim.
**It is complete and accurate.** Every open item was re-verified live at this tree state; every
`CLOSED` item was tested rather than accepted.

| # | Verdict | Re-derived this pass |
|---|---|---|
| 1 | **CLOSED, correct** | No open finding. Pass 4 files none; all ten (5 + 2 + 3) are fixed and none rejected |
| 2 | Open, real | `grep -c check_optimizer` over the spec -> **0**; `django_strawberry_framework/management/commands/` ships `export_schema.py` and `inspect_django_type.py` only |
| 3 | Open, real | `walker.py::_record_relation_access` is called from `::_plan_select_relation` and `::_plan_prefetch_relation` with no assertion or guard on the ordering |
| 4 | Open, real | `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` #"verified against the **locked Strawberry `0.316.0`**" is still present, at three sites |
| 5 | Open, real, and the enumeration is complete | `grep -c ']\[spec-035\]\|spec-035-optimizer'` over the `spec-003` companion -> **7** lines = 6 body uses + the definition at `:1050`, exactly the six the bullet names; `spec-003` #"finalized at handoff" verified in place. Both files untouched by this cycle |
| 6 | Open, real | All three names live at `tests/optimizer/test_field_meta.py:322`, `:339`, `:362` |
| 7 | Accurate | `grep -o 'docs/SPECS/spec-0[0-9][0-9]' \| sort \| uniq -c` -> **21 across 10**, breakdown entry for entry (spec-033 x5, spec-035 x4, spec-003 x3, spec-002 x2, spec-018 x2, spec-015 / 023 / 029 / 032 / 047 x1). Wider filename-form population -> **17 lines / 23 occurrences**. Both reproduce |
| 8 | Accurate | `grep -rln "spec-004-optimizer_beyond-0_0_3.md#" --include="*.md" .` -> **3** files, all this cycle's own (the rationale and the two `bld-004-*` artifacts). No external consumer |
| 9 | Accurate | `bld-004-r1-rationale_move.md` is one of those three; it is a closed scratchpad and correctly left alone |
| 10 | Accurate, and now re-derived | 35/35 link targets and anchors resolve; `import_spec_terms --check` green; ten anchors single-carrier; `check_spec_glossary` green; `examples/fakeshop/db.sqlite3` clean |
| 11 | Accurate and current | The list is **14** entries, byte-for-byte the list pass 4 recorded. **No new dirty entry appeared during this pass and none cleared** |
| 12 | Accurate | The `## How to read this file` bullet defines both block kinds and names where each lives |
| 13 | Accurate | `grep -rn '_assert_under_construction' docs/SPECS/` hits **spec-004 and its own rationale only** |
| 14 | Accurate | `HEAD` is `ff03c1372365edcad488ff4671389d88ae145276`; `git log -1 --format=%h` over the spec still returns `20a9752f` |
| 15 | **CLOSED, correct** | The build plan's `**Re-measured 2026-08-08 after R2's pass-3 review**` paragraph carries the same eight rows (D7, D9, D13, D15, D17, D20, D25, D26) plus "Do not read the numeral as settled" |
| 16 | **CLOSED, correct** | Three independent passes reached the same disposition from the evidence. No new evidence exists; I did not re-open it |
| 17 | Accurate | Nothing traced in four passes contradicts the reconciled spec; spot-checks this pass (the 256 bound and quarter eviction, `check_schema`'s `@staticmethod`, `strictness: str`, `finalize` / `_assert_under_construction`) all hold |
| 18 | Accurate | A standing hazard, correctly stated. My own link parser reproduces 35/35 with `_` preserved in slugs |

**Nothing R2 surfaced lives only in a closed section, and one clarification about what the list does
not carry.** Five items were examined and deliberately **not filed** across the four reviews, and
none of them appears in the numbered handoff: `## Current state`'s "effective end-to-end", `### B7`'s
"Benchmark (optional)", the rationale's `## How to read this file` bullet 8, and the two residues
graded below. That is **not** a gap in R3's input, because **not one of the five is R3's to act on**
— four are spec or rationale sentences only Worker 1 may edit, and the fifth is arithmetic in a
scratchpad. They are not stranded either: `BUILD.md` `## Final test-run gate` requires the deferred-
work catalog's author to walk every artifact's `What looks solid` **and** `Notes for Worker 1`
sections, which is where all five live. They reach the catalog by the mechanism that already exists.

### The two residues Worker 3 recorded rather than filed — both decided

**1. `## Non-goals` claims Layer-3 features "have their own specs" while aggregates has none.
Verified false in part, and routed to the final gate's `### Deferred work catalog`.** The sentence
(`:181`) names filters, orders, aggregates, and permissions. Three have specs — `spec-027-filters-
0_0_8.md`, `spec-028-orders-0_0_8.md`, `spec-034-permissions-0_0_10.md`, all present on disk — and
**aggregates has none**: no `docs/SPECS/` filename carries the word, and `START.md` #"still defers
`FieldSet`, full-text search, and aggregates" records it as an unwritten beta-line item.

- **Not filed as a blocking defect, and not fixed here.** The sentence's normative half — *this spec
  does not cover them* — is true, and it is the half a reader acts on; the surplus is one descriptive
  clause about the documentation tree. It is HEAD-preserved text on no drift row, examined and
  cleared by two independent Worker 3 passes against a stated standard. Editing it at final
  verification would land an unreviewed change to a contract sentence after a byte-stable round,
  which is a worse trade than the imprecision.
- **Not routed to R3.** R3 cannot act on it: only Worker 1 may edit the spec, and R3's scope is the
  durable-doc audit, the archive cross-reference sweep, the `SpecDoc.path` / terms-CSV verification,
  and the staged-anchor sweep.
- **Routed to the deferred-work catalog**, which is the item's real home: it is an item that
  discharges itself when the deferred work lands. Whoever authors the aggregates spec makes the
  sentence true by existing; if that spec is never written, a future spec-004 custodian narrows the
  clause. Either way the catalog is where the next spec author reads it.

**2. The `34`-where-it-is-`35` occurrence figure.** Graded above under the second correction:
re-derived as **27 lines / 35 occurrences**, corrected in this section, and routed **neither** to R3
nor to the catalog. It is a numeral inside a per-cycle scratchpad, nothing durable depends on it,
and both the claim it supports and the conclusion it serves are unaffected. Putting a scratchpad
numeral in the next spec author's reading list would be noise in the one document whose value is
that everything in it is actionable.

### DRY check — this item, and against R1's output

- **Against R1's output.** R1 wrote `## Entries keyed to the spec`; R2 appended `## The
  reconciliation pass — what the spec now states`. They key to the same headings and carry
  **different classes**: R1's entries record what the move cut and why, R2's record what the
  reconciliation changed and why. Neither restates the other's content, and the one place they could
  have collided — the closing claims block — is disambiguated by two labels whose divergence is
  defined once, in `## How to read this file`, and pointed at from `**On the label.**` rather than
  re-explained. That is the state-it-once shape, not a duplication.
- **Against the spec.** No `*Changed —*` explanation appears in the spec and no normative rule was
  moved out of it into the rationale. The rationale's link surface grew by exactly one definition
  across the whole round (`[spec-015]`, 23 -> 24), and it has two readers.
- **The one live duplication, examined a fourth time and still deliberate.** `### B1` `:35` and
  `### B8` `:169` now close with the identical sentence "No sibling spec states that enforcement; it
  and the requirement are both this slice's." B1 states *why no invalidation is needed*, B8 *why the
  reconciliation must copy*; neither is derivable from the other, and a repeated **negative** claim
  is the low-risk direction — if a sibling ever does claim the enforcement, both sentences become
  wrong together and one grep finds both. No action, and this is now the fourth independent pass to
  reach that disposition.
- **No new duplication and no existence challenge.** This item creates no abstraction, helper,
  constant, or indirection layer; it changed no package source.

### Spec reconciliation — no further Worker 1 edit is needed, and R3's scope is not pre-empted

The spec has been **byte-stable across a full round** (236 lines / 36,223 bytes at pass 2's apply,
at pass 3's apply, at pass 4's review, and now), `git diff --stat` is unchanged at **73 insertions /
196 deletions**, and every claim on the drift table, on the eight-finding sweep, and on the
provenance sweep is settled with its evidence. The two provenance holes the round opened are
deliberately open: plan-immutability enforcement and the once-per-row resolver-key threading are
stated with their symbols and **no** citation, because no `docs/SPECS/` file states either — which
is refusal 1's disposition applied consistently, and is auditable in a way a pointer at a document
carrying nothing is not.

**What I did not do, because it is R3's.** The durable-doc audit (`docs/README.md`, `docs/TREE.md`,
`docs/GLOSSARY.md`, `KANBAN.md`), the archive cross-reference sweep in all three directions, the
`SpecDoc.path` / terms-CSV verification, and the `TODO(spec-004` / `TODO-ALPHA-004` staged-anchor
sweep are R3's item. `worker-1.md` `## Final verification job` step 6 scopes the staged-anchor sweep
to a doc-wrap or final in-spec slice; R2 is neither, and the plan assigns the sweep to R3
explicitly. Nothing here anticipates a finding of R3's.

### Validation run — every command re-run this pass, nothing quoted

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`
  -> `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0**,
  character-identical to the pre-flight baseline.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-004-optimizer_beyond-0_0_3.md docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md docs/builder/bld-004-r2-spec_reconciliation.md`
  -> **exit 0**, all three, re-run **after** this section was appended.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` ->
  `OK: 49 done cards have glossary links.` **exit 0**. Read-only form only; the writing form was
  never invoked in this pass or in any pass of this item.
- **Anchor carriage, per anchor.** `grep -o "glossary-<anchor>]" <spec> | wc -l` returns exactly
  **2** for every one of the ten — `configurationerror`, `djangooptimizerextension`, `djangotype`,
  `fk-id-elision`, `metaexclude`, `metafields`, `metaoptimizer-hints`, `only-projection`,
  `optimizerhint`, `queryset-diffing` — one body use plus one definition, so all ten remain
  single-carrier. No pass since pass 2's apply has written a spec byte, so this is a stability proof;
  I re-read the two highest-risk carriers anyway (`djangooptimizerextension` at `:33`,
  `metafields` / `metaexclude` together at `:131`) and both sit in contract prose.
- **Link resolution, both files, re-derived on disk with my own parser** (partitions at
  `<!-- LINK DEFINITIONS -->`, strips code spans before scanning uses, normalizes each target
  against the file's own directory, slugs every heading in the target **keeping `_`**, and checks
  each anchor against that set): spec **11 defs / 11 used / 0 undefined / 0 unused**, rationale
  **24 / 24 / 0 / 0**, **35/35 targets exist and every anchored target's heading is present**,
  `../GLOSSARY.md#metaoptimizer_hints` included. Handoff item 18's hazard reproduced in the
  predicted direction: the slugger is where a false negative comes from, and keeping `_` resolves it.
- **`AGENTS.md` rule 27:** `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` -> **no match** in the spec and
  **no match** in the rationale, which is the proof that survives an edit naming six lines of a
  sibling companion by `#"unique substring"`.
- **Zero fenced code blocks:** `grep -c '^```'` -> **0** in the spec, **0** in the rationale.
- **The spec narrates no history.** Re-run with a 30-alternate pattern including `formerly`,
  `no longer`, `retract`, `previously`, `superseded`, `historical`, `deprecated`, `stale`,
  `obsolete`, `initially`, `now reads`, `revised`, `later spec`, `corrected`, `this pass`, `drift`,
  `re-derived`, `un-spec`: **one** line, `:3`, R1's companion pointer, which describes the
  *rationale file's* contents rather than the spec's own chronology and which H18 / H20 place
  off-limits.
- **The maintainer-ruled sentence is byte-identical to HEAD**, `diff` empty, `md5`
  `a236d060acf135d69af06a01cf43646a` both sides.
- **Counts, all re-derived after the last edit.** Spec **236 / 36,223**; rationale
  **1,309 / 94,318**; `git diff --stat` over the spec **73 / 196**; HEAD blob **359 / 33,928**;
  sibling citations **21 across 10**; wider provenance population **17 lines / 23 occurrences**;
  rationale owner-naming occurrences **62** (55 `][spec-0NN]` minus 1 self-reference, plus 3
  `][docs-readme]`, 4 rationale-file uses, 1 `][glossary]`); `[spec-004-improvements]` **21** = 20
  body + 1 definition with **17** in the bare form; block labels **10** modal + **12** factual + **1**
  scoped stronger.
- No `pytest` (`AGENTS.md` rule 15; this cycle changes no code). No `ruff` (neither file is Python).
  No `--cov*` flag in any command.

### Working-tree state — re-derived this pass, reported, not reverted

`HEAD` is **`ff03c1372365edcad488ff4671389d88ae145276`** (`ff03c137`), unchanged across the last
three passes. It did not sweep this cycle's work: `git log -1 --format=%h` over the spec still
returns **`20a9752f`** and all four `bld-004` / `build-004` paths are still untracked. The check was
done with `git log`, never `git status` alone.

**The list is byte-for-byte Worker 3's pass-4 reading — fourteen entries, no addition, no
clearance:**

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
 M docs/SPECS/spec-005-django_type_contract-0_0_3.md
 D docs/builder/bld-003-final.md
 D docs/builder/bld-003-r1-rationale_move.md
 D docs/builder/bld-003-r2-spec_reconciliation.md
 D docs/builder/bld-003-r3-doc_completion_archive.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/bld-004-r2-spec_reconciliation.md
?? docs/builder/bld-005-r1-rationale_move.md
?? docs/builder/bld-005-r2-spec_reconciliation.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
?? docs/builder/build-005-django_type_contract-0_0_3.md
```

The four `D docs/builder/bld-003-*.md` deletions persist and were **not** restored — the build plan's
`### Fifth change` makes that the maintainer's call and `AGENTS.md` rule 34 bans the `git checkout`
that would do it. `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`, `CHANGELOG.md`,
`docs/GLOSSARY.md`, `docs/TREE.md`, `KANBAN.md`, `KANBAN.html`, and `examples/fakeshop/db.sqlite3`
are all **clean**. `import_spec_terms --check` was re-run at this tree state and still returns
`OK: 49 done cards have glossary links.`

### Summary

**R2 delivered the reconciliation the maintainer scoped: a spec that states what the package does,
hands each later surface to the document that owns it, and narrates none of its own history.**

The spec went **216 lines / 26,436 bytes** (post-R1) to **236 / 36,223** — 20 lines and 9,787 bytes
of *contract*, against R1's removal of 7,492 bytes of deliberation. **A reconciliation that only
shrank a spec would be deleting contract rather than correcting it**, so both directions are
reported. Twenty-eight verified drift rows, twenty handoff items and eight findings the item's own
sweep added beyond the table were all discharged; four Worker 3 reviews raised ten findings across
three rounds and every one was fixed, none rejected; the fourth review filed nothing.

The round's two hardest results are not on the drift table. The first is the **provenance sweep**: a
false universal ("every sibling citation re-checked, no further misattribution found") was replaced
by a stated population, and settling that population from source found **eight** misattributions the
table never named, on rows the table's owner column had asserted without derivation. The second is
the direction nobody was hunting — two of those eight had spec-004 **exporting its own surface to a
sibling** (the ancestry-aware prefetch absorption, shipped the day before `Release 0.0.3`, credited
to a spec four releases later; and consumer-wins precedence, which spec-035's own text credits back
to spec-004 B8). Where no document owns a behaviour, the spec now names the enforcing symbols and
says so plainly rather than pointing at a document that carries nothing.

Two deferrals leave this item as **enumerations rather than fixes**, because their files are
read-only here: the `spec-029` "locked `0.316.0`" phrasing, and the `spec-003` pair's
plan-immutability misattribution — seven sites, measured, one of which is a standing instruction to
write the contract *into* `spec-035`. Both live in the durable rationale, not only in this artifact,
and both ask whoever fixes them to decide for every site at once.

`Status: final-accepted`. The next item is **R3**, whose dispatch is built verbatim from Worker 3's
pass-4 `### Notes for Worker 1` — audited above and confirmed complete and accurate as R3's input.

### Spec changes made (Worker 1 only)

**This pass made none.** `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` is byte-identical to its
pass-2-apply state (236 lines / 36,223 bytes, `git diff --stat` 73 / 196, all re-derived above), so
final verification found nothing that had to be fixed to accept.

**The cumulative record for the item, one line per change.** All in
`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`; line numbers are pin-at-write-time against the
current 236-line file. The perform pass rewrote whole sentences and paragraphs; every later edit is
an in-place rewrite of a line an earlier pass had already rewritten, which is why `git diff --stat`
has read 73 / 196 since the perform pass.

*Perform pass — thirteen edits, closing the twenty-eight drift rows, the twenty handoff items and
the eight findings the pass's own sweep added:*

1. **`## Problem statement` (`:9`)** — retensed the schedulability claim to the dependency structure
   that still holds (D1). The maintainer-ruled first paragraph was not touched.
2. **`## Current state` (`:13`)** — a mid-build snapshot restated as the standing foundation
   relationship (D2); both glossary links preserved in place.
3. **Section heading (`:15`)** — `## Proposed improvements` -> `## The eight improvements`, because
   the document proposed work its own checklist records as complete (D1).
4. **`### B1` (`:19`-`:39`)** — the 3-tuple-over-a-hash key restated as five components with the
   printed-AST collision reason (D3); the deferred-conversion thunk added (D27); the second variable
   family and the over-collection rule added (D4); "simple bounded-size dict" restated as the 256
   bound, ordered-dict storage, quarter-batch eviction and the singleton-factory pointer (D5, D6);
   invalidation restated as structural, with the three further memos named (D7); `cache_info()`'s
   `lru_cache` mirror claim dropped for the three-member tuple and best-effort counters (D8); the
   `weakref` / module-level-cache parenthetical deleted as describing nothing that exists (S3).
5. **`### B2` (`:47`-`:65`)** — dispatch site corrected; the projection gate and the ordering
   invariant added (D9); the composite-PK exclusion added (D10); the router-set stub alias, the
   identity fan-out and the loud unsafe-elision fallback added, replacing "clean fallback" (D11);
   the "Can be spec'd now" staging clause dropped.
6. **`### B3` (`:69`-`:83`)** — corrected what the warning names, which a test written from the old
   sentence would have pinned wrongly (S4); the depth bound stated (D13); the third probe and the
   `force_unplanned` override added under a corrected label (D14); `**Strictness API.**` restated
   against the shipped constructor, dropping the `Literal[...]` annotation for the three validated
   levels (S1); the resolver-signature prerequisite retensed.
7. **`### B4` (`:89`-`:107`)** — the fifth hint member added as a pointer rather than a transplant
   (D15); `OptimizerHint`'s shape restated and the "when B4 ships" clause dropped;
   `**Walker needs registry lookup.**` rewritten off the retired `_optimizer_hints` mirror (D16);
   `**Validation.**` rewritten onto `_validate_optimizer_hints` with the excluded/scalar gate and
   the flag-combination rejection (D17).
8. **`### B5` (`:115`-`:121`)** — the stash dispatch corrected so a `dict` takes the mapping path
   first, with the skip-on-frozen rule (S2); the shared-utility pointer, the per-execution reset and
   the union rule added (D18); the dict-context test row corrected.
9. **`### B6` (`:127`-`:141`)** — `classmethod` -> static method (H3); the three per-field checks
   collapsed to the one that ships (S5); the warning's contents corrected (S6); the union / interface
   descent and the `(model, field name)` dedupe added (D19, D20); the `check_optimizer` follow-up
   sentence dropped as a promise eleven versions old with no card (D21); `iter_types()` restated;
   `metafields` / `metaexclude` re-sited inside the rewritten exposed-fields sentence (D22).
10. **`### B7` (`:147`-`:153`)** — the map's home moved off `cls._optimizer_field_map` onto the
    definition's `field_map` at three sites (D22); `FieldMeta`'s real shape stated as the
    optimizer-relevant core plus the later relation work's slots, replacing "a lightweight namedtuple
    or dataclass" with six attributes (S8); the fallback stated as a dual contract (D23).
11. **`### B8` (`:159`-`:169`)** — the opening paragraph retensed off "blindly stacks" (H12); the
    reconciliation restated as a `(plan, queryset)` pair with the upgrade and prune steps (D25, D26);
    cache-safety restated as enforced rather than instructed (D26).
12. **`## References` (`:187`-`:189`)** — the dangling "skip Strawberry conversion" clause repointed
    at the deferred conversion (D27); the Django `select_related` clause corrected from B1's cache to
    B8's reconciliation (S7).
13. **`## Implementation checklist` (`:194`)** — the spike bullet's sequencing parenthetical trimmed
    (H4).

*Apply-changes pass 1 — three edits, from Worker 3's pass-1 findings:*

14. **`### B1` `**Cache storage.**` (`:33`)** — the `functools.lru_cache` rejection's causal clause.
    The stated reason was false at HEAD (a model class is an ordinary hashable key; zero `lru_cache`
    in `optimizer/`), and this is the paragraph a builder reaching for the decorator consults, so the
    reason was **replaced** with the structural one rather than deleted (L1).
15. **`### B2` column-append paragraph (`:49`)** — dropped the causal argument reproduced from
    `spec-003`, keeping the requirement and the pointer. `spec-002` #"each own the surface they
    added" is the family rule, and the item's own record already said the spec pointed rather than
    restated (DRY finding).
16. **`### B2` `**Resolver change required.**` (`:55`)** — named `spec-003` as the response-key
    fan-out rule's owner and `spec-033` as its nested-connection multiplication. The rule had no
    owner named in the spec and a wrong one in the rationale (M2).

*Apply-changes pass 2 — four edits, from the pass-2 finding and the whole-file provenance sweep it
mandated:*

17. **`### B1` `**Cache invalidation.**` (`:35`)** — dropped the `spec-035` clause, named
    `optimizer/plans.py::OptimizationPlan.finalize` and `::_assert_under_construction`, and stated
    that no sibling spec owns the enforcement. `spec-035` contains none of it, re-derived three ways
    (M3).
18. **`### B6` `**Mechanism.**` (`:129`)** — "Relay interfaces belong to `spec-032`" replaced by
    `spec-015`'s foundation plus `spec-032` as its later extension; `spec-032`'s own predecessors
    line defers the foundation to `spec-015`, and the descent arm predates `spec-032` by a release
    train.
19. **`### B8` prune paragraph (`:167`)** — "`spec-035` owns it" narrowed to "records that stance",
    which is what `spec-035`'s own text supports; and the subtree-aware ancestry absorption reclaimed
    from `spec-033` as this slice's own, having shipped the day before `Release 0.0.3`.
20. **`### B8` `**Cache-safety**` (`:169`)** — the same correction as (17).

*Apply-changes pass 3 — none. This pass — none.*

**No `- [ ]` box remains on the `### Dispatched findings checklist`, so no deferral reason is owed
under this heading.** The item's deferrals are the six recorded in the R3 handoff plus the two
residues graded above, all routed to the final gate's `### Deferred work catalog` or to the party
that owns the file.

**The maintainer-ruled `## Problem statement` sentence is byte-identical to HEAD.** It was never
edited by any pass of this item: HEAD `:5` and working `:7` `diff` **empty**, `md5`
**`a236d060acf135d69af06a01cf43646a`** on both sides, the HEAD blob extracted read-only into a
scratch path outside the repository.
