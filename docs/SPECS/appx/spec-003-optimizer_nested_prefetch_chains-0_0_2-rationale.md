# Rationale: spec-003 — Optimizer O4 nested prefetch chains (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-003-optimizer_nested_prefetch_chains-0_0_2.md`][spec-003]. The
spec is the contract and states only what holds; everything that explains **how it got there**
lives here: the implementation shapes it proposed and where the shipped code departed from each,
the derivations that do not change how a decision is implemented, and every claim the spec once
made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass. **The move
happened long after the release, not before the build.** Card `DONE-003-0.0.2` shipped twelve
patch versions ago and the rule that gates a build on this move did not exist then; this pass
supplies it. Nothing below was copied — every item it classifies left the spec — but the
classification distinguishes two fates, and the distinction matters to anyone trying to find the
original text. **Moved** means the text itself is reproduced here and exists nowhere else.
**Cut** means the text exists in *neither* file: what follows the label is an account of what it
said and why it went, and git history is the only record of the text. `## Provenance of this
record` files every item under one of the two, plus a third for what was deleted with no account
kept at all.

## How to read this file

- **One entry per spec section**, named by the section's own heading and linked to its anchor. A
  section this pass cut nothing from has no entry here — that is not an omission, it means the
  whole section is contract.
- **Who reads it.** The role-by-role answer is [`BUILD.md`][build] `### Who reads it, and when`,
  which is that mechanism's canonical home. A reader looking for what the package *does* wants the
  spec, not this file.
- **This spec has no numbered Decisions.** It predates that convention, so the key is the heading.
  Two entries key to headings that no longer exist in the spec at all (`## Anchor and lint notes`
  and `## Implementation insertion points (O4)`); each names the surviving section its argument
  bears on.
- **This spec is a child document, and its parentage is not retold here.** Why the O4 record was
  extracted out of [`spec-002-optimizer-0_0_2.md`][spec-002] into its own document is
  `spec-002`'s own deliberation and is recorded in [its rationale file][spec-002-rationale] under
  *"`## Purpose` and the former `## O4 extraction`"*. That argument is not duplicated on this side
  of the split. What belongs here is only the O4 design's own deliberation.
- **What the rationale-extraction pass did NOT do.** It did not reconcile the spec against the
  shipped package. This file records where the shipped code *departed* from a proposed shape,
  because that departure is the deliberation — a rejected shape and the one that beat it — but it
  does not decide how the spec's surviving prose should now read. That disposition belongs to the
  reconciliation item, and `## Standing notes` lists what this pass deliberately handed to it.
- **Read `## Standing notes` before editing the spec.** It records the sentences this pass left
  standing on purpose and one clause its own deletions orphaned. All of them are things a passing
  sweep would otherwise "correct" or miss.

## Provenance of this record

- **Moved** — cut from the spec by this pass and reproduced here, so the text exists here and
  nowhere else: the three discharged bullets of `## Documentation updates when O4 ships`, together
  with the discharged half of its fourth. They are quoted in that entry below. This is the only
  category to which "it exists here" applies.
- **Cut, with a prose account kept here** — all **seven** fenced pseudo-code blocks (one quoting
  the pre-O4 dispatch site in `## Current state`, and six proposing an implementation across
  `### Same-query recursion for single-valued paths`,
  `### Prefetch-boundary recursion for many-side and downgraded paths` ×2,
  `### Lookup-path flattening`, and `### Resolver sentinel keys` ×2); the whole of
  `## Implementation insertion points (O4)`; and the whole of `## Anchor and lint notes`. **This
  file carries no code fence at all.** Each entry below *describes* what its proposal did, which
  alternative beat it, and what shipped instead; the proposed text itself survives in neither file,
  so a reader looking for it wants git history, not this document. That is the prescribed
  disposition rather than an economy: proposed code that landed under a different name is prose
  the current decisions have falsified, and [`worker-1.md`][worker-1]
  `### Performing the rationale move` rule 2 deletes rather than moves it — while the *account* of
  a proposal and the shape that beat it is deliberation, which is exactly what this file is for.
- **Deleted with no account kept** — the fences' *symbol names, signatures, privacy, and file
  placements*, wherever the shipped code contradicts them, and the line-number framing of
  `## Implementation insertion points (O4)` ("Line numbers below refer to the current O4 starting
  point and are approximate"). What each proposal *meant* is recorded below; what it *spelled* is
  not, except where the spelling is itself the contract (the key format).
- **Restated in the spec, not moved** — six rules that lived only inside a fence and are
  instruction rather than deliberation. Each is called out in its entry below under
  *"Kept in the spec"*: the FK-column-before-elision ordering invariant; the parent-side FK-column
  append at the prefetch boundary; the empty-`only_fields` guard on connector injection; marking
  the parent uncacheable before the child queryset is built; the resolver-key format and its
  no-parent fallback; and the resolver side's membership test against the elision set. A builder
  who never reads this file must still write all six, so all six stayed.
- **Deliberately left in the spec by this pass** — every present-tense status claim about the
  pre-implementation codebase, in `## Problem statement`, `## Current state`,
  `## End-goal context`, `## Desired behavior`, `## Interactions with shipped beyond slices`,
  `## Test plan`, `## Definition of done`, and `` ## Missing `.py` files ``. A status claim moved
  into a rationale file is neither a legitimate entry here nor the deletion the move prescribes for
  falsified prose, and its disposition against the shipped package is the reconciliation item's
  call. Also left: the prose sentences naming now-deleted symbols outside a fence, for the same
  reason.

## Entries keyed to the spec

### `## Current state` — the pre-O4 dispatch block it quoted

Spec: [Plan shape][spec-003-current]. The section was headed `## Current state` when this entry
was written; the reconciliation pass renamed it, and its entry in
`## Reconciliation pass — what the spec now says, and why` below records why.

*Cut — the quoted code.* The section introduced its quote with "Concretely, the same-query
branch's depth-1 behavior is:" and then reproduced the forward-FK / OneToOne arm of
`_walk_selections` as it stood before O4: a `_collect_scalar_only_fields` call over the related
model at `prefix=f"{full_path}__"`, an unconditional `plan.select_related.append(full_path)`, and
the `TODO(spec-003-optimizer_nested_prefetch_chains-0_0_2.md O4)` anchor marking where recursion
was to go.

*Why it went rather than stayed.* Every line of it is a claim about code that no longer exists.
`_collect_scalar_only_fields` has **zero occurrences** package-wide; the append is
`append_unique`; the arm itself was extracted out of `_walk_selections` into a named helper; and
the anchor it quoted survives in no source or test file. The paragraph the quote illustrated
stayed — it says what the pre-O4 walker did and what O4 replaces it with, which is the section's
actual content — so nothing was lost but a snapshot of deleted code.

**Kept in the spec.** Nothing from the fence; the surrounding prose already carried the whole
point ("`_collect_scalar_only_fields` walks scalar children only and silently drops any nested
relation").

**Claims the spec no longer makes.** That the relation-dispatch block carries a `TODO(spec-003…)`
anchor. Nothing else — the section's other claims are untouched and are the reconciliation item's
to judge.

### `### Same-query recursion for single-valued paths` — the proposed else-branch

Spec: [Same-query recursion for single-valued paths][spec-003-samequery].

*Cut — the proposed branch.* The fence proposed the whole `else: # relation_kind == "select"`
arm inline inside `_walk_selections`: compute `runtime_path` from `runtime_prefix` and
`sel.alias or sel.name`, append `f"{prefix}{django_field.attname}"` to `only_fields`, run the
four-part B2 predicate, `continue` on an elision, otherwise
`plan.select_related.append(full_path)` and recurse with `prefix=f"{full_path}__"`.

*Alternative rejected — keep the arm inline in `_walk_selections`.* It lost to extraction. The
same arm at HEAD is a named helper reached through a dispatcher, and the reason is that the
selection walk grew three more arms after O4 (a prefetch boundary, a connection boundary, and a
hint-driven override); a single function carrying all of them is unreadable, and the recursion
this slice introduced is what made the arm count grow. The **semantics** the fence proposed
survived intact — the extraction changed where the code lives, not what it does.

*Alternative rejected — a private per-module `_append_unique`.* The fence spelled the dedup helper
as a walker-private `_append_unique`. It is public and shared at HEAD, because the same
append-if-absent discipline is needed by every producer of a directive list and a second private
copy is the duplication the plan-level list ordering exists to prevent.

**Kept in the spec — the ordering invariant, and it is the one thing here a builder must not get
wrong.** The fence encoded, purely by statement order, that the FK-column append happens
**before** the elision short-circuit. The bullets above the fence listed both steps but described
neither as ordered, so deleting the fence would have deleted the invariant. It is now stated as a
requirement with its reason: an elided branch plans no join, and the resolver that serves the
elision reads the source row's FK column, so appending the column after the short-circuit leaves
it unprojected and silently reintroduces the very N+1 the elision removes. There is **no automated
guard** on this ordering at HEAD — it is documented in the helper's docstring and enforced by
nothing else — which is exactly why the sentence had to survive the move.

**Claims the spec no longer makes.** That the same-query arm is written inline in
`_walk_selections`. That the dedup helper is private to the walker.

### `### Prefetch-boundary recursion for many-side and downgraded paths` — the proposed branch and its two helpers

Spec: [Prefetch-boundary recursion for many-side and downgraded
paths][spec-003-prefetch].

*Cut — two fences.* The first proposed the `if relation_kind == "prefetch":` arm inline: append
the parent FK column, flip `cacheable` on a custom `get_queryset`, build a child queryset, walk
the child selections into a fresh `OptimizationPlan` at `prefix=""`, inject connector columns,
apply the child plan, propagate `cacheable` upward, and append
`Prefetch(full_path, queryset=child_qs)`. The second proposed the two helpers it called —
`_build_child_queryset(field, target_type, info)` and
`_ensure_connector_only_fields(plan, parent_field)` — with full bodies.

*Alternative rejected — keep the arm inline, again.* Same argument and same outcome as the
same-query branch; at HEAD this arm is a named helper plus two child-queryset builders.

*Alternative rejected — `Prefetch(field.name, …)`, the field name as the lookup segment.* The
fence's `Prefetch(full_path, queryset=child_qs)` composes `full_path` out of Django **field
names**, and that is wrong for a reverse relation declared without `related_name`: Django's
`prefetch_related` resolves a lookup by `getattr` on the instance, so a reverse FK whose field
name is `book` is reachable only as `book_set`. The proposed shape raised
`AttributeError: … invalid parameter to prefetch_related()` on every optimized query over such a
relation. The lookup segment is the relation's **instance accessor**; plan keys and resolver
identities stay in field-name vocabulary, and only the string Django consumes uses the accessor.
This is a correctness fix rather than a refactor, and it is a rejected alternative worth recording
precisely because the losing shape is the intuitive one.

*Alternative rejected — the planner calls the target type's `get_queryset` itself.* That is what
the `_build_child_queryset` fence did, with the docstring "Pick the child queryset, honoring O6
visibility filters" and a direct `target_type.get_queryset(qs, info)`. It lost to a shared,
framework-owned visibility boundary that every framework-side invocation routes through, so that
one seam owns sealing, degradation, and the sliced-queryset allowance rather than each caller
re-deciding them. The boundary's own rules are
[`spec-045-visibility_boundary-0_0_14.md`][spec-045]'s and are not restated in this spec.

*Changed — where the three connector rules live.* The fence carried them in
`_ensure_connector_only_fields`'s body. The helper keeps its name and its guard at HEAD, but the
rules themselves moved out to a join-taxonomy module so the nested planner and the walker read one
source of truth; the reverse-one-to-one arm was also added after this spec was written. All three
rules the fence proposed survived unchanged in substance, and the spec still states them as
contract in its bullets — only the body that once held them is gone.

**Kept in the spec — three rules that existed only inside the fences.**

- **The parent-side FK-column append.** The first fence opened by appending
  `f"{prefix}{django_field.attname}"` to the **parent** plan's `only_fields`, under an
  `attname is not None` guard. Nothing outside the fence said so: the section's connector bullet
  is scoped to the *child* plan — a different queryset and a different column — and the
  same-query section states the rule only for the select branch. The guard is what scopes the
  append: the three reverse descriptors — `ManyToOneRel`, `ManyToManyRel`, `OneToOneRel` — carry
  no `attname` attribute at all, which is why HEAD reads it as
  `getattr(django_field, "attname", None)`, so nothing is appended for them; every forward
  relation carries one. The case that makes the append load-bearing is a forward FK or OneToOne
  that reaches this branch instead of the same-query one — downgraded by O6, or forced across by
  a `force_prefetch` hint — whose parent rows Django matches by reading `<field>_id` off each
  parent. Dropping it from the parent projection buys a deferred load per parent row — the N+1
  the slice exists to remove, on the branch the slice added. A forward `ManyToManyField` also
  passes the guard, because Django sets `ManyToManyField.attname` to the field's own name; what
  lands in `only_fields` is then a field name rather than a column, which Django drops from the
  compiled `SELECT`. That is shipped and harmless; whether the spec should say so is the
  reconciliation item's call, and `## Standing notes` records it. At HEAD the append is the shared
  `optimizer/walker.py::_record_relation_access`, which `::_plan_prefetch_relation` calls first,
  exactly as `::_plan_select_relation` does; the spec now states it on both branches instead of
  one. **This rule was missed on the first pass of this move and rescued on the second**, which is
  the sharpest available illustration of why the carve-out is the hard part of the job: five rules
  of identical shape were caught and the sixth was not, because its only in-spec trace was one
  line of a fence that read like a duplicate of the select branch. **Its scope clause was then
  wrong on the second pass and measured on the third**: both the review that drafted the clause
  and the custodian that adopted it reasoned from the guard's semantics instead of introspecting
  the field objects, and a census of the model graph is what showed a forward M2M passing the
  guard and `force_prefetch` reaching the branch.
- **The empty-`only_fields` guard.** `_ensure_connector_only_fields` opened with
  `if not plan.only_fields: return` and the comment "No child only() applied; Django will fetch
  full rows and connectors come for free." Injecting unconditionally would convert a full-row
  fetch into a one-column projection — a data-loss bug wearing an optimization's clothes. The
  guard survives verbatim at HEAD and is now stated in the spec's connector bullet.
- **Marking the parent uncacheable before the child is built.** The fence set
  `plan.cacheable = False` on the custom-`get_queryset` test *before* calling
  `_build_child_queryset`, not after. The bullet below it stated the propagation rule without the
  ordering. The order is load-bearing: a child build that degrades rather than completing must
  still leave the parent plan uncacheable, or a request-scoped visibility result gets cached.

**Claims the spec no longer makes.** That the prefetch arm is written inline in
`_walk_selections`. That the `Prefetch` lookup segment is the relation's field name. That the
planner invokes a target type's `get_queryset` directly. That the three connector rules live in
`_ensure_connector_only_fields`'s body.

### `### Lookup-path flattening` — the proposed helper pair

Spec: [Lookup-path flattening][spec-003-flattening].

*Cut — the fence.* It proposed `lookup_paths(plan) -> set[str]` seeded from
`set(plan.select_related)` and unioned with a recursive
`_prefetch_lookup_paths(entries, prefix="")` that string-tests each entry, reads `entry.prefetch_to`
otherwise, and recurses into `inner._prefetch_related_lookups`.

*Not rejected — this one shipped almost exactly as proposed.* `_prefetch_lookup_paths` keeps the
proposed name and its `(entries, prefix="")` signature, recurses to arbitrary depth, and composes
each nested level onto its parent under the lookup separator. Two things were added: a
short-circuit on a precomputed frozenset once the plan is finalized, and a single named reader for
the Django-private `_prefetch_related_lookups` attribute, so exactly one call site in the package
depends on that contract instead of one per consumer. Both are later hardening
([`spec-035-optimizer_hardening-0_0_10.md`][spec-035]), not a reversal of this design.

*Changed — where the helper sits in the file.* The design section said "Locate it on `plans.py`
next to `OptimizationPlan`"; the insertion-point section said "End of file". They contradicted
each other in the same document. The end-of-file instruction is the one that was followed. Worth
recording because the disagreement is invisible once one of the two sections is deleted, and a
reader of the survivor would conclude the instruction was ignored.

**Kept in the spec.** The two properties a builder needs and the fence was the only carrier of:
the return is the union of `select_related` strings and every flattened prefetch path, and nested
levels join onto their parent under Django's lookup separator. The "arbitrary depth, not one child
level" requirement and the separation from resolver strictness keys were already prose and are
untouched.

**Claims the spec no longer makes.** That the flattening helper reads
`_prefetch_related_lookups` directly. That the helper sits next to `OptimizationPlan`.

### `### Resolver sentinel keys` — the proposed key helpers, on both sides

Spec: [Resolver sentinel keys][spec-003-sentinel], and bears on [Lookup paths vs resolver sentinel
keys][spec-003-lookup-vs-key].

*Cut — two fences.* The first proposed the walker-side append plus a private
`_resolver_key(parent_type, field_name, runtime_path)` in `walker.py`. The second proposed a
mirrored `_is_fk_id_elided(info, field_name, parent_type)` in `resolvers.py`, reading
`dst_optimizer_fk_id_elisions` off the context and testing the reconstructed key against it.

*Alternative rejected — two mirrored private implementations, one per module.* The spec argued for
it explicitly: "The pseudocode anchors now live in both `optimizer/walker.py` and
`types/resolvers.py`, which is intentional", on the reasoning that only the walker can see merged
selections before planning and only the resolver can reconstruct the runtime branch from
`info.path`. That premise is true and survived; the conclusion did not. Two copies of a key
*format* held together by a "keep both sides on the same key format" instruction is a drift bug
waiting for the first edit that touches one side. Both helpers landed **public and shared**, in
the plans module, imported by the walker and the resolvers alike — the asymmetry the spec
identified is real, but it is an asymmetry of *inputs*, not of the function that formats them.

*Alternative rejected — a dedicated `_is_fk_id_elided` predicate on the resolver side.* No such
symbol exists at HEAD, and neither does the `_get_relation_field_name` the documentation section
wanted updated. The elision test is inlined into the forward resolver so a single `info.path` walk
is shared between the B2 elision check and the B3 N+1 check; two predicates would have walked the
same linked list twice per resolved relation field, on the hot path, to save nothing. The
path walk is depth-bounded at HEAD, which the fence's version was not.

*Changed — a single `runtime_path` tuple per selection.* The fences threaded exactly one runtime
path through the walk. One is not enough once a selection can be reached by more than one response
key: HEAD computes the cartesian product of the inherited runtime prefixes and the selection's
response keys and returns a tuple of identities. That fan-out, and the alias preservation on
merged nodes it depends on, belong to [`spec-033-connection_optimizer-0_0_9.md`][spec-033]. Note
that the spec's own text offered exactly this as one of two options — "either preserve the response
aliases on merged nodes or record resolver keys from the original selections before merging" — and
the first option is what shipped; recording which of a spec's two offered options won is the kind
of thing only this file can carry.

**Kept in the spec — the key format, verbatim in substance.** `<ParentType>.<field>@<a.b.c>`, with
the parent type's `__name__`, the Django field name, `@`, and the runtime-path segments joined on
`.`, plus the no-parent-type fallback that drops the prefix. The fence's *spelling* of the format
is the one place where the proposed code is exactly what shipped, so the format is contract and
stayed; only its wrapper's name, privacy, and module went. The resolver side's membership test
against `info.context.dst_optimizer_fk_id_elisions` also stayed, for the same reason: it is the
half of the protocol a builder implementing the resolver end must match.

**Claims the spec no longer makes.** That the key helper is private to `walker.py`. That the
runtime-path helper and the elision predicate live in `types/resolvers.py`. That a symbol named
`_is_fk_id_elided` exists. That one runtime path per selection is sufficient.

### `## Documentation updates when O4 ships` — all four obligations discharged

Spec: [Documentation updates when O4 ships][spec-003-docs].

*Moved — three of four bullets, plus the discharged half of the fourth.* Discharged instructions
are neither contract nor deliberation; they are history, and history is this file's. What each
required, and what discharged it:

1. *"Update `docs/SPECS/spec-002-optimizer-0_0_2.md` current state, visibility status, and
   checklist to mark O4 shipped."* Discharged — and the instruction had itself become false, since
   `spec-002` has no `## Current state` section any more. Its `spec-003` cycle removed it and
   folded what it carried into the sections that already stated the same facts; the reasoning is
   in [that spec's rationale][spec-002-rationale]. `spec-002` now records O4 as shipped in its
   shipped-slices section, its visibility statement, and its implementation checklist.
2. *"Update `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` current state to remove the note that
   O4 is unimplemented **and** the `not yet implemented` rider on the B-slices that depend on
   nested resolver-key sentinels."* Discharged in two steps. The rationale-move pass found the
   current-state note already gone and the rider still standing — the B4 depends-on clause said
   the consumer-supplied-`Prefetch` hint composes with O4 and O6 "once those land", though both
   landed at `0.0.2` — so it was the one bullet that pass left in the spec. The
   documentation-completion pass retired the rider; see the paragraph below.
3. *"Remove or update `TODO(spec-003…)` anchors in source and tests (…). Also update the older
   parent-spec O4 references in `docs/SPECS/spec-002-optimizer-0_0_2.md`."* Discharged on both
   halves — zero anchors survive in any source or test file, and the parent-spec references were
   brought current by the `spec-002` residual cycle, as item 1 above records. The three anchors
   that survived inside spec-003 itself were removed by this pass, since all three rode inside
   text this pass was cutting anyway.
4. *"Update the depth-1-only comment in `resolvers.py:_get_relation_field_name` and
   `_is_fk_id_elided`."* Discharged by deletion: neither symbol exists, and the string `O4` does
   not appear anywhere in the package source.

*Why the section was trimmed rather than deleted.* An instruction with an undischarged obligation
is not history. Deleting the whole section would have deleted the only in-spec license for the
`spec-004` edit that was then still owed, leaving the edit to be justified from a build artifact
that closes with its cycle.

*Changed in the documentation-completion pass, which discharged item 2's remaining half.* The B4
`**Depends on.**` clause in `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` no longer ends "once
those land"; it states that the consumer-supplied-`Prefetch` hint composes with O4 and O6, which
is what holds. The clause was retired rather than rewritten to announce the landing, because the
sibling spec's own `## Current state` already records O4 and O6 as shipped and a second statement
of that fact is the copy that rots. With item 2 closed, the spec's section carries no open
instruction; it keeps its heading and a one-line pointer here rather than being deleted, so this
entry's key still resolves and a reader who scans the spec's headings still learns that the
obligations existed and where their account lives.

*Alternative rejected: delete the section from the spec outright.* It is the tidier end state and
it was the other live option, since a wholly discharged instruction is history and history is this
file's. It lost on link integrity and on discoverability — deleting the heading orphans this
entry's `[spec-003-docs]` key, and a reader of the spec alone would then have no signal that the
section ever declared anything. A one-line pointer is the shape rule 1 of the move prescribes for
exactly this case.

*Changed — the maintainer chose the deletion at closeout (2026-08-07).* The rejected alternative
above is now the shipped state: a spec is done when its features are implemented, no other spec
carries a documentation-obligations section, and a discharged instruction earns no heading. The
section is gone from the spec; this entry is the whole account of what it declared and what
discharged each obligation, and the `[spec-003-docs]` key now points at the spec file rather than
the removed heading.

**Claims the spec no longer makes.** That `spec-002` has a `## Current state` section to update.
That `TODO(spec-003…)` anchors exist to remove. That `resolvers.py` has a
`_get_relation_field_name` or an `_is_fk_id_elided` to update. That any obligation from this
section is still open — item 2's surviving half, the `spec-004` B4 rider, was the last, and it is
discharged.

### The former `## Anchor and lint notes` — a staging convention with no referent left

Spec: bears on [Definition of done][spec-003-dod]. The `## Anchor and lint notes` heading no
longer exists.

*Cut — the whole section.* It read, in full, that the O4 pseudocode anchors "have already been
staged in the relevant source and test files" using
`TODO(spec-003-optimizer_nested_prefetch_chains-0_0_2.md O4)`; that because the anchors carry
pseudo-code, `ruff check .` "may report `ERA001` until O4 is implemented"; and that those findings
should be left in place "while the TODO anchors are serving as implementation guidance".

*Why it went.* Every sentence is false at HEAD. No `TODO(spec-003…)` anchor survives anywhere; no
`ERA001` finding is being tolerated on O4's account; the two TODO comments a static sweep still
reports in the walker belong to a later spec entirely. The convention it describes is real and
standing — `AGENTS.md` carries it, for staged-but-unbuilt slices — but this spec has no staged
slice left, so restating the convention here would be a standing rule copied into a document that
no longer exercises it.

**Kept in the spec.** Nothing. The section was instruction to a builder, with no normative content
about the package's behavior.

**Claims the spec no longer makes.** That O4 pseudocode anchors are staged in source and test
files. That `ERA001` findings are deliberately being tolerated.

### The former `## Implementation insertion points (O4)` — guidance to a builder who has been

Spec: bears on [Implementation design][spec-003-design] and [Definition of done][spec-003-dod].
The `## Implementation insertion points (O4)` heading no longer exists.

*Cut — the whole section, 63 lines across six package modules and four test modules.* It opened
"Line numbers below refer to the current O4 starting point and are approximate; trust the symbols
and nearby comments over exact offsets after edits begin" and then listed, per file, where each
change was to be made.

*Why it went, and why it was the largest single cut.* It is a set of directions to a builder,
addressed to a codebase state that ended when O4 landed. Its opening sentence is falsified by
construction — there is no "current O4 starting point" to refer to. Most of its instructions were
followed at the named site and are therefore invisible; the ones that were not are recorded in the
entries above (the two extractions, the relocation of both key helpers into the plans module, and
the two `types/resolvers.py` symbols that were never written). The rest is a per-file restatement
of design decisions the spec states once already, which is the duplication that lets a document go
stale in one place and not the other.

*Changed — one instruction the package overtook rather than ignored.* "B8 TODO block — leave the
pseudo-code anchor intact." B8 queryset diffing has since shipped, so there is no anchor to leave
intact and the instruction cannot be complied with. Recorded here rather than corrected in place,
because the surviving spec text about B8 is the reconciliation item's to judge.

*Alternative rejected — keep the section and re-point it at the shipped symbols.* That would
convert a build instruction into a second map of the O4 surface, maintained in parallel with the
design sections and with `docs/TREE.md`, and it would have to be re-pointed again every time the
optimizer is refactored — which has happened at least four times since, across the connection,
hardening, visibility, and join-taxonomy work. A spec that publishes a symbol map publishes a
liability; the design sections say what must be true, and the source says where.

**Kept in the spec.** Nothing that was not already stated in the design sections. Two rules that
existed *only* here were checked before the cut and were both already carried elsewhere: the
`prefetch_obj`-is-a-leaf requirement (stated in `### Hints are leaf operations` and again under
B4) and the `lookup_paths`-is-not-for-strictness rule (stated in
`## Lookup paths vs resolver sentinel keys` and in `## Definition of done`).

**Claims the spec no longer makes.** That line numbers in it refer to a current starting point.
That a B8 pseudo-code anchor exists in the extension. That `_build_child_queryset` is the only
place that calls a target's `get_queryset`.

## Standing notes — what this pass deliberately did not do

None of these is a deferral in the sense of unfinished work. They are boundaries this pass drew
on purpose, recorded here because a do-not-touch note is worth nothing in a place nobody reads
before editing.

### The status claims were left standing, and they are the reconciliation item's

This pass cut the *deliberative* layer: proposal code, build instructions, and discharged history.
It did **not** touch the spec's present-tense claims about the pre-implementation codebase, even
where they are demonstrably false at HEAD — the problem statement's "The remaining O-slice is O4",
the current-state field inventory and planner signature, the desired-behavior query counts, the
end-goal context's "future" framing of work that has since shipped. Moving a status claim here
would be neither a legitimate entry (it is not deliberation) nor the deletion the move prescribes
(that is for prose the current *decisions* falsified, not prose the *package* outgrew). Deciding
each one's fate — restated as the contract that holds, handed to the spec that now owns it, or
dropped — is the reconciliation item's job, and it has a verified drift table to work from.

### One clause this pass orphaned

`## Definition of done`'s last bullet ends "…with TODO-anchored pseudo-code findings left
untouched". Its referent was `## Anchor and lint notes`, which this pass deleted. The clause was
already moot before the deletion — there are no such findings and no such anchors — so this is not
a regression introduced here, but it is now a dangling reference as well as a false one, and the
reconciliation item should not have to rediscover it.

### Two scope questions this pass raised and did not answer

Both fall out of measuring the parent-side FK-column append's guard against the model graph, and
both are about how the prefetch-boundary section describes its own population — which is the
reconciliation item's subject, not this pass's.

- **A forward `ManyToManyField` passes the guard.** Django sets `ManyToManyField.attname` to the
  field's own name, so the parent plan gets a field name appended to `only_fields` where a forward
  FK gets a column. Django drops it from the compiled `SELECT`, so nothing is broken; the question
  is whether the spec should document it or whether it is a tidiness item for the maintainer.
- **`force_prefetch` is a second route into this branch, and the section's lead-in names only the
  O6 downgrade.** `### Prefetch-boundary recursion for many-side and downgraded paths`'s opening
  sentence and its connector bullet both frame the forward case as "downgraded by O6", while
  `### B4 optimizer hints` says `force_prefetch` "should follow the same prefetch-boundary
  recursion path". Both sentences predate this pass and were left standing; whether they should
  name the hint route is the reconciliation item's call.

### The design sections' two departures are recorded, not repaired

The entries above name where the shipped code departed from a proposed shape, because a rejected
shape and the one that beat it are exactly what this file is for. They do **not** rewrite the
spec's surviving prose to describe the shipped symbols. Where a departure implicates a sentence
that survived the cut — the child-queryset construction seam, the two mirrored key helpers, the
single runtime path — the sentence is still there and still says what the spec originally said.
That is deliberate: one pass moves, the next reconciles, and a half-reconciled spec is worse than
an un-reconciled one because the reader cannot tell which half is current.

## Reconciliation pass — what the spec now says, and why

The pass above moved the deliberative layer out and deliberately left every present-tense status
claim standing. This section is the second pass's record: what each of those claims was replaced
with, which alternative replacement lost, and what the spec may no longer assert. It is keyed to
spec sections exactly as `## Entries keyed to the spec` is, and the two blocks together are the
whole account — the first for what left the spec, the second for what the surviving prose was
turned into.

**One rule governs every entry below, and it is the reason this section exists at all.** The spec
never narrates its own history ([`BUILD.md`][build] `## Spec rationale extraction`). Every claim
the package falsified was rewritten to state the contract that actually holds, directly, with no
amendment block, no retraction, and no "originally this was X" — so the spec reads as though it had
been right from the start. The chronology is here instead. A reader who has to reconstruct what is
currently true by applying a sequence of corrections is reading a changelog, not a contract.

**The scope line held, and it was the hard part.** This spec is a child document whose subject
matter four later specs extended: [`spec-033`][spec-033] (nested connections and the
runtime-prefix fan-out), [`spec-035`][spec-035] (plan immutability, the projection gate, the
private-attribute reader), [`spec-045`][spec-045] (the sealed visibility boundary), and
[`spec-018`][spec-018] (the resolver's own return type driving the root field map). Reconciling
against HEAD pulls hard toward absorbing all four, because every one of them is visible in the
code this spec designed. Each was resolved the same way: **a pointer to the owning spec, never a
transplanted paragraph.** Where a later spec's surface is not needed to state O4's own contract,
it is not mentioned at all.

### `## Problem statement`

*Claims the spec no longer makes.* That O4 is "the remaining O-slice". That the walker collects
scalar fields through `select_related` paths via a named scalar-only helper. That a `TODO` at the
end of the selection walk is the implementation anchor.

*Alternative rejected — retense the section to "O4 shipped at `0.0.2`".* It reads naturally and it
is what a changelog would say, which is why it lost: the sentence's job is to say what problem the
slice solves, and a reader who needs the ship date has `KANBAN.md` and `CHANGELOG.md`. A spec that
announces its own release status acquires a second thing to keep current for no contract gain.

*Alternative rejected — delete the second paragraph outright.* Both its sentences named deleted
symbols, so deleting looked clean. But stripped of the symbol names it carries a real contract
fact — that the walk threads a Django lookup prefix so a nested entry can name its path from the
root — which nothing else in the spec states, and which the whole `select_related` chain design
rests on. Rewritten rather than cut.

### `## End-goal context`

*Changed — the B7 field-map bullet named a symbol that never existed under that name.* The bullet
asserted `_optimizer_field_map` is re-read at every recursion level. There is no such symbol
package-wide; the field map is the registered type definition's, resolved per entry by the
walker's own field-map resolver. The **property** the bullet exists to protect is real and
load-bearing at HEAD — each recursion resolves the map for the model it is descending into, so a
nested branch plans against its own target's metadata rather than the root's — so the property was
kept and the symbol name dropped. This drift row was not on the verified floor the build plan
handed the pass; it came out of reading the section against source.

*Changed — B8 was "future" work that "will normalize" lookup paths.* It has shipped, and the spec
now states the requirement in the present. The obligation on O4 is identical either way: preserve
stable lookup identities. Only the tense was false.

*Fixed in passing.* The bullet's cross-reference read "see 'Lookup paths vs resolver keys' below";
the heading is `## Lookup paths vs resolver sentinel keys`.

*Changed — the lead-in's quantifier.* The retense of "have shipped **or are designed around** the
current `OptimizationPlan` shape" to "are all built around the `OptimizationPlan` shape" dropped a
disjunct and turned a hedge into a universal, and the universal is false for two of the seven
slices it quantifies over: the schema audit walks the registry, each registered definition's field
map, and its hints, and returns warning strings without ever constructing or reading a plan; the
field-metadata slice is the metadata the walk plans *against*, upstream of any plan. The lead-in
now names the planning **surface** — the plan the walk produces, the planning type's field
metadata it plans against, or both — which is true of all seven and still says the thing the
sentence exists to say: O4 extends the planner without breaking any of them.

*Alternative rejected — name the subset ("B1, B2, B3, and B5 are built around the plan; B6 and B7
are upstream of it").* Accurate, and it turns a one-line premise into a taxonomy the spec would
then owe maintenance on every time a B-slice's relationship to the plan shifts. The bullets below
already say what each slice needs from O4; the lead-in only has to be true.

*Claims the spec no longer makes.* That a symbol named `_optimizer_field_map` exists. That B8 is
future work. That every beyond slice is built around `OptimizationPlan`.

### `## Plan shape` (was `## Current state`)

*Changed — the heading.* `## Current state` announces, by name, that what follows describes the
codebase *before* the change. That framing is the thing that goes stale, and a spec that had been
right from the start would never have carried it. The section now states the plan's shape, which
is a contract that survives every later refactor. The rename is the one edit in this pass that
moves an in-page anchor: the entry above re-points at `#plan-shape`, and no other document links
that section.

*Alternative rejected — keep the heading and retense the body.* It would have left a section named
"Current state" holding no state claim, which is worse than either honest option: a reader trusts
a heading to say what kind of thing is below it.

*Changed — the plan field inventory was five entries; the dataclass carries eleven.* The spec now
lists the **six** bags O4 owns (the original five plus `planned_resolver_keys`, which is O4's own
and which the old `## Current state` could not list because O4 had not added it yet) and points at
[`spec-033`][spec-033] / [`spec-035`][spec-035] for the rest.

*Alternative rejected — enumerate all eleven fields.* This is the strongest pull in the whole
reconciliation, and it loses for two reasons. The five it would add are not O4's contract: the
per-path resolver-key ledgers exist so a B8 consumer-wins drop can de-plan a subtree, and the
frozen membership sets exist because the plan is finalized at handoff — decisions belonging to
[`spec-033`][spec-033] and [`spec-035`][spec-035], each already stated once in its own document.
Restating them here creates two copies of one contract, and a fact told twice goes stale in one of
them. The second reason is structural: an inventory of a dataclass is a symbol map, and this
document has already recorded (under the former `## Implementation insertion points (O4)`) why a
spec that publishes a symbol map publishes a liability.

*Changed — `fk_id_elisions` was "currently relation paths … O4 must migrate this bag".* The
migration is the slice's own delivered work, so the spec states the resulting contract: the bag
holds branch-sensitive resolver keys, and bare relation paths are insufficient.

*Changed — the planner signature was published inline.* The old text spelled
`plan_optimizations(selected_fields, model, info=None)`. Three later slices added keyword
parameters to it, none of them this spec's. The contract-relevant content was never the signature
but the two starting conditions the sentence carried around it: the Django lookup prefix the walk
starts from, and the runtime response path it starts from. Both are stated; the signature is not.

*Alternative rejected — publish the current signature.* It would be accurate today and wrong at
the next keyword argument, and every one of those arguments so far has belonged to another spec.

*Changed — the root runtime response path was stated as empty, and it is not.* The Django half of
the pair is empty at the root; the runtime half is the root field's own response key, because the
planner derives it from `info.path` and that path already includes the field being resolved. The
empty tuple is only the recursive walker's default for a caller with no `info` — a direct or
test-only call — and the planner never takes it. The claim was inherited unexamined from the old
`## Current state` text, where it had been describing an argument default rather than the shipped
planner's behaviour, and it survived the sweep because the Django half beside it is true.

This one mattered more than a wrong noun usually does, which is why the spec now carries the
reason rather than only the fact. `### Resolver sentinel keys` makes the walker/resolver agreement
load-bearing, and the resolver reconstructs `("allEntries", "item")` from `info.path`. A walker
built from "empty runtime path at the root" would emit `EntryType.item@item` against a resolver
asking for `EntryType.item@allEntries.item`: every key would miss, every elision and every
strictness sentinel would silently fail to match, and nothing would raise. The spec is the only
document that states this protocol, so a false starting condition in it is not recoverable from
anywhere else.

*Alternative rejected — drop the runtime half of the clause and leave the whole runtime-path story
to `### Resolver sentinel keys`.* That section says the walk threads the runtime path alongside
the Django prefix, so the two would no longer contradict each other. It loses because the pair is
what makes the sentence worth having: a reader learning that one of the two accumulators starts
empty will assume the other does too, and the section that would have to correct that assumption
is eight headings away.

*Changed — `only_fields` was "root-query scalar paths".* At a prefetch boundary the child plan's
`only_fields` are relative to the **child** queryset, which is the point of the whole boundary
section; calling them root-query paths contradicted it. Now stated as relative to the queryset the
plan applies to.

*Changed — the section's companion pointer named the section's own former content.* It read "the
pre-O4 dispatch block **this section quoted**", which had a referent while the heading was
`## Current state` and the fence was still in living memory, and has none now: `## Plan shape`
quotes nothing. Of the six per-section pointers this was the only one whose subject was the spec's
own past *content* rather than a design it once proposed, which is exactly the shape the
no-self-narration rule exists to keep out. It now names the thing — the pre-O4 dispatch shape, and
where the shipped walker departed from it — which is also what this entry's own heading says.

*Claims the spec no longer makes.* That `OptimizationPlan` holds five things. That
`fk_id_elisions` holds relation paths, or that a migration of it is owed. That the planner takes
exactly `(selected_fields, model, info=None)`. That planning starts from an empty runtime response
path. That the relation-dispatch block carries `TODO` anchors. That `only_fields` are root-query
paths. That this section quotes anything.

### `## Desired behavior`

*Changed — the query counts and the plan shapes are now both qualified.* All three worked examples
state a query count and a `Plan shape:`, and each is exact only where no type on the chain
overrides `get_queryset`. The example project has since grown exactly that shape on the
`Entry -> Item -> Category` chain, and its live test pins three queries where the spec says one.
The counts were being read as unconditional when they were always conditional on the O6
interaction the spec itself specifies two sections later.

*Changed again, in the correcting pass — the qualifier's first wording said the plan shapes survive
the downgrade.* It read "the plan shapes are unchanged, the counts are not", which contradicts the
same sentence's own concession that the downgrade "turns a same-query join into its own round
trip", and is falsified by the very live test the row cites: that test's docstring records the
chain moving from one `select_related("item__category")` JOIN to a `Prefetch` per downgraded link.
A downgraded link leaves the `select_related` chain, so the `Plan shape:` line under it changes
too. What is genuinely invariant is narrower and is what the lead-in now says: **O4's dispatch**.
The relation is planned by the same recursion whichever branch it takes, and the branch is chosen
by the cardinality-and-O6 decision the design section already specifies — which is what "nothing
about O4 changed" was reaching for and stated one abstraction level too high.

*Alternative rejected — say only that the counts are conditional and stay silent on the shapes.*
It would have been true, and it leaves a reader to discover on their own that the three
`Plan shape:` lines carry the same condition as the three count lines directly above them. The
section tabulates both; a qualifier that covers one of the two is the shape of the original defect.

*Alternative rejected — restate the fakeshop counts.* That would import the example project's
cascade configuration into a package spec and make this document wrong the next time the example
changes. The example project is not the contract.

*Alternative rejected — drop the counts.* They are the clearest statement of what "optimized"
means for a nested chain, and the depth-2 reverse-FK count is exact and unqualified in practice.
A qualifier costs one sentence; deleting the counts costs the section its point.

*Changed again, in the final-verification pass — the qualifier is scoped to the single-valued
link.* The correcting pass's wording said "a type that does is downgraded by O6, and that link
leaves the `select_related` chain". Only a single-valued link is ever *in* that chain, so read
strictly over the two many-side worked examples the clause described a move that cannot happen
there. The governing first sentence already scopes the whole block, so nothing a reader codes from
was wrong; the clause is narrowed to the population it is true of rather than left resting on the
sentence above it.

*Alternative rejected — leave it, and carry the imprecision to the deferred-work catalog.* Defensible
on severity, and it is where the review left it. It loses on durability: the spec outlives the
cycle's catalog, the narrowing costs three words, and it changes no contract, so there is nothing
for a later reader to re-litigate.

*Claims the spec no longer makes.* That any of the three query counts holds unconditionally. That
the depth-3 single-valued chain is one query however the types on it are configured. That an O6
downgrade changes only the count and leaves the plan shape alone. That an O6 downgrade moves a
many-side link out of the `select_related` chain.

### `### Same-query recursion for single-valued paths`

*Changed — three "(already done)" parentheticals and a "replacing the current call" instruction.*
Each described the pre-O4 codebase to a builder who no longer exists. The rules they annotate are
unchanged and are now stated as rules. The obsolescence paragraph that followed the bullets
("`_collect_scalar_only_fields` becomes obsolete … and can be deleted once the recursion lands")
was deleted outright under [`worker-1.md`][worker-1] `### Performing the rationale move` rule 2:
the symbol has zero occurrences package-wide, so every clause of it is false, and the one durable
idea inside it — that a scalar-only collection step at this position drops nested relations
silently — was folded into the recursion bullet where a builder needs it.

*Changed — the dispatch lead-in.* `## Implementation design` said the two cases "share the existing
`_walk_selections` entry point". At HEAD both cases are reached through one dispatcher with three
callers: the cardinality verdict and the two hint overrides. That is a strictly stronger version of
what the sentence was trying to guarantee — a relation is planned identically however it was
decided — so the guarantee is stated and the symbol name is not.

*Added — nested Relay connections are named as a third case and handed to [`spec-033`][spec-033].*
A reader of the two-case sentence would conclude a nested connection takes one of these two paths.
It takes neither: it is recognized before the relation branch and planned elsewhere. One clause
naming it and pointing away is the minimum that stops the spec being read as a complete account of
the dispatch; anything more would be summarizing `spec-033` here.

*Claims the spec no longer makes.* That a scalar-only collection helper exists or is called
anywhere. That the two recursion cases are the only cases.

### `### Prefetch-boundary recursion for many-side and downgraded paths`

*Unchanged, deliberately — the parent-side FK-column append bullet.* It is the sixth carve-out
rescue from the previous pass, and it states a requirement about the branch rather than a claim
about the codebase. This pass did not fold it into the reconciliation sweep.

*Changed — "use the target type's `get_queryset(queryset, info)` if O6 requires it".* At HEAD the
hook is never invoked directly from the planner: it runs through the framework's shared visibility
boundary, which owns sealing, degradation, and the sliced-queryset allowance. The spec now states
the boundary as the requirement and points at [`spec-045`][spec-045] for its rules. This is the
same rejected alternative the entry for the `_build_child_queryset` fence records above — the
planner calling the hook itself — now removed from the surviving prose as well as from the fence.

*Alternative rejected — restate the boundary's degrade-to-unplanned rule here.* It is one sentence
and it is tempting, because the degradation is what makes the `allow_sliced` allowance safe. It
lost because that rule has an owner, a decision number, and its own test surface in
[`spec-045`][spec-045]; a second statement of it here would be the copy that rots when the
boundary is next hardened.

*Changed — "Refactor `plan_relation` before wiring this branch".* A build instruction, discharged.
Its residue is a real contract — the relation planner decides a kind and constructs nothing, and
queryset construction belongs to one seam so a custom hook runs exactly once per prefetched
relation — and that is what the bullet now says.

*Changed — `Prefetch(full_path, queryset=child_queryset)`, the field name as the lookup segment.*
This is the one place where the shipped code **corrected** what the spec designed rather than
merely relocating it, and the correction is now the contract: the lookup segment is the relation's
instance accessor. The losing shape is the intuitive one and it is not a style preference — it
raised `AttributeError: … invalid parameter to prefetch_related()` on every optimized query over a
reverse relation declared without `related_name`. The bullet states the rule, the reason Django
requires it, and the boundary of the rule (only the string Django consumes uses the accessor; plan
keys, resolver identities, and `select_related` paths stay in field-name vocabulary), because a
reader who takes the accessor rule too far corrupts the resolver keys.

*Changed — the reverse-FK connector arm now names reverse OneToOne.* The arm was written for
`one_to_many` alone; the shipped connector derivation covers reverse one-to-one on the same arm,
for the same reason (the forward field's `attname` on the child side is what Django matches on).
This is a one-clause correction to a rule this spec owns, not an import from another spec — the
connector rules are spec-003's contract wherever their implementation happens to live now.

*Claims the spec no longer makes.* That the planner may call a target type's `get_queryset`
directly. That `plan_relation` constructs querysets. That the `Prefetch` lookup segment is the
relation's field name. That the reverse connector arm is reverse-FK only.

### `### Hints are leaf operations` and `### B4 optimizer hints`

*Changed — two instructions to a builder.* "The current walker already treats `hint.prefetch_obj`
as a leaf; preserve that" and "Document this explicitly in `hints.py`" are both discharged; the
hint module carries the leaf contract in its own docstring. The rule survives; the instructions do
not.

*Changed — "switch its `_collect_scalar_only_fields` call to `_walk_selections` for parity".* Same
deleted symbol, same discharge. What replaced it is stronger than the parity the instruction asked
for: a hint chooses which of the two paths a relation takes and never changes what that path does.

*Added — two `force_select` facts the spec never stated.* It is rejected outright for a many-side
relation, which Django cannot `select_related` at all; and it yields to O6, so a target type
overriding `get_queryset` crosses the prefetch boundary despite the hint. Both are O4's own
composition question (hints × cardinality × O6 at nested depth), which this section is the only
place in the corpus to answer, and both are silently surprising in the other direction — a reader
of the old bullet would expect `force_select` to force a join.

*Added — `force_prefetch` named as the second route into the prefetch branch.* The section's
lead-in frames the forward case as "O6-downgraded" only, while the hint bullet says
`force_prefetch` follows the same path. The two sentences were consistent but the population was
under-described, which is one of the two questions the previous pass handed forward. Answered here
rather than deferred: the prefetch-boundary bullet already names both routes, and the hint bullet
now says outright that it is the second one.

*The other handed-forward question — a forward `ManyToManyField` passing the `attname` guard — is
deliberately NOT documented in the spec.* Django sets `ManyToManyField.attname` to the field's own
name, so the parent-side append puts a field name rather than a column into `only_fields`; Django
drops it from the compiled `SELECT`, so nothing is broken. Writing it into the spec would document
a harmless implementation artifact as though it were contract, and would invite a future reader to
"fix" the guard into something narrower than HEAD's — which is the guard the append actually needs.
It stays a maintainer-facing note, recorded in `## Standing notes` above and carried to the
deferred-work catalog.

*Fixed in passing — the `OptimizerHint` glossary link opened inside a code span.* The paragraph
wrapped one pair of backticks around the whole of `OptimizerHint`, its reference-style link
brackets, and the trailing `.prefetch(obj)`, so the reference sat *inside* the code span and
rendered as literal text instead of becoming a link. It is pre-existing — the same shape is in the
spec at every commit carrying this paragraph — and it is that anchor's only carrier in the
document, which is why it was worth two characters: `check_spec_glossary.py` counts it today only
because it does not strip code spans, so the eight-anchor set card 3's `import_spec_terms` chain
rebuilds from rests on a checker behaviour rather than on a real link. The backticks now sit inside
the link label and around the trailing method call separately, leaving the reference outside both —
the same shape `check_spec_glossary.py --auto-link` writes when it links a term the spec already
spells in inline code, so the anchor survives any future checker that does strip code spans.

*Alternative rejected — leave it and carry it as a deferred item.* It is not a reconciliation
finding and the prose around it was explicitly not to be disturbed, which is a fair argument for
deferring. It loses on margin: the eight-anchor constraint has none, this is the single carrier for
one of the eight, and the repair moves no link, changes no word of prose, and is verifiable by the
same command the constraint is already gated on. Deferring a two-character markup fix that protects
a chain the cycle is under standing instruction not to break costs more than doing it.

*Claims the spec no longer makes.* That a scalar-only collection helper is called for
`force_select`. That `hints.py` still owes a documentation edit.

### `### Lookup-path flattening`

*Changed — "Locate it on `plans.py` next to `OptimizationPlan`".* Two things were wrong with it.
It is build guidance, not contract; and it contradicted the insertion-point section, which said
"End of file" and is what was followed — a disagreement the entry for this section above preserves
precisely because deleting one of two contradicting sections makes it invisible. The module is
stated, the position is not: where a helper sits in a file is not something a reader should be
able to falsify a spec with.

*Changed — the helper "should recurse through nested `Prefetch.queryset._prefetch_related_lookups`
directly".* At HEAD the recursion goes through a single named reader of that Django-private
attribute. The spec now states the requirement without the mechanism, and the single-reader
discipline is [`spec-035`][spec-035]'s to state.

*Alternative rejected — state the single-reader rule here.* It is a good rule and it is not this
spec's; it was added by a later hardening slice for reasons that have nothing to do with nested
chains, and it is stated once already.

*Claims the spec no longer makes.* That the flattening helper reads the private lookups attribute
itself, or that it sits beside `OptimizationPlan`.

### `### Resolver sentinel keys`

*Changed — "B2 FK-id elision currently works only at depth 1 … There is already a latent leak
today".* The leak is closed; the reasoning that closed it is exactly why the key format is what it
is, so it stays, restated as the standing argument for a branch-sensitive key rather than as a bug
report about a codebase state.

*Changed — "Thread a `runtime_path` tuple through `_walk_selections`", singular.* One runtime path
per selection is insufficient, and the spec's own text offered the fix as one of two options
("either preserve the response aliases on merged nodes or record resolver keys from the original
selections before merging"). The first option is what shipped, so the spec now states it as the
contract and states its direct consequence: a selection reachable under more than one response key
carries one resolver identity per key, never one identity for the merged node. The **prefix**
fan-out that multiplies those identities over nested-connection runtime prefixes is
[`spec-033`][spec-033]'s and is pointed at in one parenthesis, not described.

*Alternative rejected — describe the cartesian product.* It is two sentences and it would make
this section a partial restatement of the connection planner's identity model. The response-key
plurality is O4's, because O4 is what made a merged node represent more than one key; the prefix
plurality is not.

*Changed — "The pseudocode anchors now live in both `walker.py` and `types/resolvers.py`, which is
intentional … Keep both sides on the same key format".* The spec argued for two mirrored private
implementations held in step by an instruction. The premise survived and the conclusion did not:
both helpers landed public and shared in the plans module, imported by the walker and the
resolvers alike. The spec now states the premise (the asymmetry is in what each side can read) and
the corrected conclusion (the formatting is one shared implementation), because an instruction to
keep two copies matching is a drift bug waiting for the first edit that touches one side.

*Changed — `_runtime_path_from_info(info)` and `_attach_relation_resolvers(cls, fields)`.* Neither
name or signature is HEAD's. The behaviours both sentences specified are contract and are stated
without the symbols. The paragraph that argued the `cls`-binding change "is small enough to land
alongside O4" was deleted rather than rewritten: it is sequencing advice to a builder, and the
contract residue (each resolver closure binds its own parent type) was already stated in the
bullet two paragraphs above it. Deleting the second copy is the point.

*Changed — "add a resolver-key collection … This can be a new `planned_resolver_keys` bag … or an
equivalent helper".* The choice was made; the spec states the outcome.

*Claims the spec no longer makes.* That a symbol named `_runtime_path_from_info` or
`_is_fk_id_elided` exists. That the key helpers are private, mirrored, or module-local. That one
runtime path per selection suffices. That B3's resolver-key collection is still a choice between
two shapes.

### `### B1 plan cache`

*Changed — "The propagation in `_walk_selections`'s prefetch branch handles this when it copies
`child_plan.cacheable` upward".* The propagation is real but it is not where the sentence says: a
child plan's cacheability travels with the rest of its resolver metadata in the single absorb step
the parent performs. The spec now states the requirement **and** why it lives in the absorb rather
than at each call site — so a future third absorb site cannot forget it — which is the
implementation-relevant half of the rule and the reason it is worth a clause at all.

*Claims the spec no longer makes.* That the propagation lives in the prefetch branch of the
selection walk, or that any call site copies `cacheable` upward itself.

### `### B8 queryset diffing`

*Changed — "B8 will diff plan output against existing queryset optimization".* B8 ships as a
pre-publish reconciliation against the consumer's own queryset. Retensed and narrowed to what it
actually diffs against; the flattening obligation on O4 is unchanged.

*Claims the spec no longer makes.* That B8 is future work, or that it diffs against optimization
from any source other than the consumer's own queryset.

### `## Test plan`

*Changed — two rows named `tests/optimizer/test_extension.py` for tests that shipped in the live
tier.* Both query-count rows are reachable through a real query against the example project, so
they belong in `examples/fakeshop/test_query/` under [`AGENTS.md`][agents] "Test through real
usage", and a package-level stand-in for a live-reachable row is precisely what a live row
retires. The spec now says where they belong and why, rather than naming node ids that moved.

*Changed — the forward-FK row asserted a flat "1 query".* Same conditionality as
`## Desired behavior`: exact where no type on the chain overrides `get_queryset`, one extra round
trip per O6-downgraded link where one does. The row now says to derive the count from a real run,
which is [`BUILD.md`][build] `### Query-shape tests must pin the load-bearing property`'s own rule
("Derive the absolute count from a real run; never guess it") and is what keeps the row honest
when the example project changes again.

*Changed — the sibling-leak row named one axis and shipped as two.* The elision leak has two
distinct axes — a sibling **root** field and a different **parent type** — and they are pinned by
two different tests in two different tiers. The row now names both, which is also the only place
the spec records that the *sibling-nested-branch* axis under one parent type is covered by the key
format rather than by a dedicated row.

*Changed — the two assertion shapes that named list equality.* `select_related == ["item",
"item__category"]` is a tuple at HEAD, because the plan is finalized before handoff
([`spec-035`][spec-035]). The rows now state coverage rather than container type, which is what
they were pinning anyway and which does not re-break the next time the plan's storage changes.

*Changed — "Update the existing B2 stub/null tests …".* A build instruction, discharged; restated
as the property those tests hold.

*Not changed — every other row.* A per-test existence check against HEAD found each of them
present, most under the exact name the spec gave. Nothing in the test plan was skipped, and the
rows that match are left alone.

*Claims the spec no longer makes.* That the two query-count rows belong in
`tests/optimizer/test_extension.py`. That the depth-2 forward-FK row is one query regardless of
the types on the chain. That `select_related` compares equal to a list. That the elision-leak row
has one axis. That the B2 stub/null tests are still owed an update.

### `## Definition of done`

*Changed — bullet 2 named the deleted scalar-only helper*, and *bullet 8 ended "with TODO-anchored
pseudo-code findings left untouched"*, whose referent was the deleted `## Anchor and lint notes`
section. The previous pass recorded that clause as orphaned as well as false; it is deleted, and
the rest of bullet 8 (run the formatter and the linter) stands as the ordinary
[`AGENTS.md`][agents] obligation it always was.

*Alternative rejected — delete bullet 8 entirely.* Without the false clause it restates a standing
rule, which is a fair argument for cutting it. It stays because a definition of done that omits
the lint gate reads as licensing a build that skips it, and the cost of the bullet is one line.

*Changed — the maintainer chose the deletion at closeout (2026-08-07).* The rejected alternative
above is now the shipped state: the lint gate is [`AGENTS.md`][agents]'s standing repo-wide rule,
equally true of every spec, so restating it in one spec's definition of done adds no contract. The
definition of done now ends at the tests bullet.

*Claims the spec no longer makes.* That any TODO-anchored pseudo-code finding exists to leave
untouched. That running the formatter and linter is part of O4's own definition of done.

### The former `` ## Missing `.py` files ``

*Deleted — the whole section.* It read: "None. Every O4 change lands in an existing module:
`walker.py`, `plans.py`, `extension.py`, `resolvers.py`, `hints.py` … No new subpackage or Python
module needs to be created for O4."

*Why it went.* It is build guidance in the imperative — an answer to "what must the builder
create" — and the builder has been. It is also false as a present-tense map: the O4 surface now
spans a nested-connection planner, a selection-traversal module, a join-taxonomy module, and a
nested-fetch module, none of which existed when the sentence was written. Its one durable fact,
that O4 itself needed no new module, constrains nobody: it is not a rule any future change can
violate.

*Alternative rejected — re-point it at the modules the surface spans today.* This is the same
argument the former `## Implementation insertion points (O4)` entry above lost, and it loses the
same way. It would create a second module map maintained in parallel with `docs/TREE.md` and with
the design sections, needing a rewrite after every optimizer refactor — of which there have been at
least four since. The design sections say what must be true; `docs/TREE.md` says where the modules
are.

*Alternative rejected — keep it, retensed to "O4 introduced no new module".* True, harmless, and
worth nothing: it is a fact about a change, not a property of the package, and a spec section whose
whole content is a historical fact about its own implementation is the narration this document
exists to keep out of the spec.

*Claims the spec no longer makes.* That the O4 surface is confined to five modules.

### What this pass deliberately did not change

- **The `## Documentation updates when O4 ships` section**, whose single surviving bullet is the
  open `spec-004` rider. Discharging it is the documentation item's work, and the in-spec clause is
  what licenses that sibling edit.
- **The parent-side FK-column append bullet**, for the reason its own entry gives.
- **Any sibling spec.** Where an R2 edit makes a sibling's cross-reference read oddly, that is
  recorded as deferred work rather than fixed in place; sibling specs are read-only to this pass.
- **Any package source or test.** The read-only correctness audit that fed this pass found no
  defect in the shipped O4 paths, and four observations, three of which are correct-as-designed
  and one of which — the unguarded ordering invariant between the connector-column append and the
  elision short-circuit — is a maintainer-facing note, not a defect. The spec states that invariant
  as a requirement, which is the strongest form available inside a documentation cycle.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-002]: ../spec-002-optimizer-0_0_2.md
[spec-002-rationale]: spec-002-optimizer-0_0_2-rationale.md
[spec-003]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md
[spec-003-current]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md#plan-shape
[spec-003-design]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md#implementation-design
[spec-003-docs]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md
[spec-003-dod]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md#definition-of-done
[spec-003-flattening]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md#lookup-path-flattening
[spec-003-lookup-vs-key]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md#lookup-paths-vs-resolver-sentinel-keys
[spec-003-prefetch]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md#prefetch-boundary-recursion-for-many-side-and-downgraded-paths
[spec-003-samequery]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md#same-query-recursion-for-single-valued-paths
[spec-003-sentinel]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md#resolver-sentinel-keys
[spec-018]: ../spec-018-meta_primary-0_0_6.md
[spec-033]: ../spec-033-connection_optimizer-0_0_9.md
[spec-035]: ../spec-035-optimizer_hardening-0_0_10.md
[spec-045]: ../spec-045-visibility_boundary-0_0_14.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md
[worker-1]: ../../builder/worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
