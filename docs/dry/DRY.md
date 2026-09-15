# DRY: one owner per rule

Every rule, shape, name grammar, lifecycle the package enforces = exactly one authoritative
definition. Every other site composes it by name. Change the rule → one edit; the system follows by
construction, not by someone remembering every copy.

Failure prevented: drift. Two copies correct on day one; first change lands on one; nothing fails
(each copy still works alone); divergence surfaces later as an unrelated-looking bug. Humans do it
under time pressure; agents do it because the cheapest correct output for "add a feature" is a
fresh copy of the nearest working code.

Population: package source under `django_strawberry_framework/`; tests + docs are its media.
Consumer business rules (app-side model constraints, validators, policies) = different population,
out of scope.

Two roles. **Construction discipline**: "Design principles" bind every builder plan /
implementation / review ([BUILD.md][build]). **Consolidation flow**: the cycle below hunts rules
that grew a second owner. Reading the principles never starts a cycle; Rio starts one by name
([START.md][start] Agentflows). [AGENTS.md][agents] governs safety, tests, formatting, commits.

## Vocabulary

Four site populations; only the first must count one:

- **Authoritative definition** — independently maintained implementation/declaration of the rule.
  Two = duplication, shared token or not.
- **Consumer / enforcement site** — invokes or derives from the definition where the rule must
  hold; stays at its boundary. Five flavors each opening `pipeline_write_phase()` around their own
  persist call = five enforcement sites, not five copies.
- **Independent oracle** — externally specified expectation that can contradict a broken owner. A
  test expecting `iContains` spells it; never reads
  [filters/inputs.py][filters-inputs]`::LOOKUP_NAME_MAP`. Map changes → test fails, not oracle
  updates.
- **Explanation / projection** — prose, generated doc, rendered artifact. Describes; never owns.

Intentional contract change legitimately moves production + oracles + docs together ≠ fixing four
independent implementations. Count definitions separately from the other three, every finding.

Textual difference ≠ independence. Costly duplication shares no tokens: one rule spelled two ways,
sync/async twin, contract restated in a test or doc. Clone detection + literal counts find only the
cheap cases → clean audit = orientation, never verdict.

Similar-looking ≠ duplication. Consolidate only when sites encode one responsibility, one contract,
same reasons to change.

## Design principles

Bind new code and consolidations alike. Each = the shape to build + the boundary past which the
same move makes things worse.

1. **Declare the variation, share the meaning.** Family = one validated record type + one driver
   owning the lifecycle. New member of a supported kind = declaration, not method. New KIND =
   extend the driver once, w/ validation + tests. Driver contract closed: validated records,
   explicit defaults, enumerated variants, loud unsupported path. Absent hook = no-op only where
   the contract says absence means "nothing to do"; absent permission hook never = "permitted".
2. **One owned translation.** Two systems agreeing on a name → one grammar/table produces it, both
   read it. `LOOKUP_NAME_MAP` (Django lookup → GraphQL spelling);
   `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` (the one set-family naming rule).
   Target = ONE translation, not zero. Structural relationships declared w/ stable identifiers,
   never parsed out of display text.
3. **Give the odd case the common shape.** One member differs → record w/ default, not a branch at
   every consumer. Only when the contract is the same; two decisions agreeing today w/ separate
   reasons to change stay separate.
4. **Derive once, w/ a stated lifetime.** One implementation of a derivation: required. One cached
   result for every context: not. Every stored derivation names owner, validity key, publish
   point, who may mutate, when invalidated. Pure derivation says "not cached". Anti-duplication
   never mandates new shared state.
5. **Share the lifecycle, keep the adapters.** Shared process = one body; genuinely different work
   = named adapters the body calls, never a mode flag adding a branch no real path reaches.
   Sync/async ≠ automatic twins: share pure decisions first, then per pair decide one body w/
   execution adapters vs two machines, preserving await points, cancellation, thread affinity,
   ORM execution, cleanup. Same axis, opposite correct answers in this package: write pipeline =
   one sync body in one `sync_to_async` boundary (ORM work must not interleave w/ awaits inside a
   transaction); `connection.py` = two colored bodies (must await consumer `async def` hooks),
   sharing only pure decisions. Record the contrast at both owners.
6. **Compose by name, never restate.** Higher layer calls the lower rule. Never inlines the
   predicate, re-derives the field set from `_meta`, rebuilds the name by concatenation, recomputes
   the default from settings.
7. **Choose the owner by responsibility.** State contract + real consumers; record reads, effects,
   lifetime, enforcement authority. Prefer an existing owner w/ that responsibility. Else the
   narrowest cohesive owner every legitimate consumer can depend on w/o reversing a dependency or
   importing a sibling flavor for its machinery. Distinct decisions stay at adapters; share only
   the common mechanism. "Narrowest" vs "no reversed dependency" conflict → dependency direction
   wins (an owner its consumers can't import isn't one); host-module size ≠ criterion. "Lowest
   valid owner" = shorthand for this decision, not a ladder read off field counts: a transport
   module can own a transport-only rule; a table can belong to one adapter.
8. **Behavior-preserving = observable behavior.** Short-circuit order, exceptions raised, query +
   transaction effects, cancellation, the point where actor/time/state are observed. Not Boolean
   agreement on a happy input. Splitting a predicate ≠ automatically safe; hoisting a check out of
   the boundary that makes it valid changes its meaning.
9. **Enforce sameness mechanically when one body is impossible.** One owner holds the canonical
   form; a check proves every copy against it under an independently enumerated population,
   per-region identity + cardinality, rejected parse failures, negative controls (missing,
   duplicated, truncated, renamed, omitted). Passing count ≠ completeness.
   `scripts/check_trailing_commas.py`, `build_tree_md.py --check` = this shape.
10. **Write the grammar at the owner.** Convention living only in code gets bypassed by the next
    capable person, who sees custom logic, not a rule. Each grammar + each intentional separation
    stated in prose where owned ([sets_mixins.py][sets-mixins] module docstring; `"__all__"` note
    in [filters/sets.py][filters-sets]`::FilterSet.get_fields`). That prose = projection, not
    definition: verify every stated reason against the body before designing on it. Wrong stated
    reason < none; the next author honors it.
11. **Ask whether the abstraction should exist.** Deletion = first-class outcome: indirection w/
    one real caller, helper w/ no readers, token whose only job is being checked. What breaks if
    removed + inlined? Constant/helper pair can be dead code → delete, don't extract. One
    legitimate "nothing breaks, keep": the wrapper is the only site stating a pairing/separation
    in words; keep it, record the keep on it so the question isn't re-raised.

Measurement follows the rule. Primary evidence: fewer independently maintained definitions.
Secondary: net source change over a fixed baseline + population, counting added drivers / tables
/ adapters; relocating code or deleting independent oracles ≠ reduction. Consolidation may ADD
lines to remove a change obligation; near-zero net on a security/authorization rule = good result.
Finding relieving no change obligation ≠ finding, whatever it moves. None of this permits
machinery: a helper obscuring ownership, coupling independent domains, or needing mode flags makes
the system less DRY.

## Worked example

[sets_mixins.py][sets-mixins]`::SetLifecycleAttrs`.

- **Before.** Each set family reset binding state under three class attrs (owner, expansion cache,
  reentry guard). Expansion path spelled the names; `registry.clear()` path spelled them again. A
  fourth attr = remember both spellings; filter family's metadata snapshot could survive a clear
  that rebuilt its filters.
- **After.** Family declares ONE `SetLifecycleAttrs` on its set class (`_lifecycle` on
  [filters/sets.py][filters-sets]`::FilterSet`, [orders/sets.py][orders-sets]`::OrderSet`).
  `binding_attrs` derives the reset population incl. `extra`. `sets_mixins.py::expanded_once`
  consumes cache + guard names; [utils/inputs.py][utils-inputs]`::clear_generated_input_namespace`
  consumes `binding_attrs`. Neither path spells a slot.
- **Change challenge.** Add a family-specific cached slot → only the declaration gains its
  identity; generic reset discovers it. Independent regression test proves the clear removes the
  new state (a test reading the slot list from the declaration passes whatever it says). New family
  declares its own record, never copies the lifecycle body.
- **Intentional separation.** `FilterSet.get_fields`: per-field `"__all__"` lookup expansion vs
  model-level `"__all__"` sweep share a token, not a contract. Posit a change to either → other
  doesn't move. Recorded at the owner so no cycle re-litigates. Rejections are measured like
  consolidations: name the shared form considered, count how much of the family it would own +
  what the remainder needs, state the change that would move the count.

## Finding a candidate

Unit of work = **responsibility family**: one rule + every site defining, consuming, testing,
describing it. Files = coverage backstop, not unit of reasoning (file-scoped review correctly
reports one owner per file while the rule has three across the package).

### Inventory backstop

Every `.py` under `django_strawberry_framework/` is a plan item. File item discharged when every
rule it defines/enforces is assigned to a named family in the plan's responsibility index, or
recorded file-local w/ no second site after the matrix. No consolidation inside a file item;
consolidation lives in the family item holding all sites. Folder + project items audit the
unassigned remainder + cross-boundary families. Discovery + consolidation in one cycle; no
catalog-only cycle.

Family item sweeps the WHOLE package for the rule's mechanism (dunder, decorator, exception,
sentinel), not the target's neighbours — the second definition is routinely in a module no seed
named. Family item writes every sub-rule it decomposes back to the index as its own row.

### Mandatory probing matrix

Six axes where duplication hides from textual search. Floor of an inventory, not its shape; a
target yielding only matrix hits hasn't been searched. Discharge every axis on every target: a
search, or one line naming why the target has no such surface (`__init__.py` files legitimately
carry no round-trip pair or async twin).

1. **Cross-flavor policy mirroring** — one rule per public surface (types, filters, orders,
   mutations, forms, `rest_framework`), each in local vocabulary. Read sibling flavors before
   calling a concern unique.
2. **Sync/async twins** — separated only by the await boundary; drift silently, no single test
   executes both. Compare by behavior, not shape.
3. **Derived rather than repeated knowledge** — one fact reconstructed by different means (name by
   concatenation, field set from `_meta`, default from settings). Deriving a duplicated fact still
   duplicates it.
4. **Inverse / round-trip pairs** — encode/decode, pack/unpack, build/parse, input/output shaping.
   One grammar, two halves, routinely separated by module.
5. **Contracts restated in another medium** — production code, test expectations, `docs/` prose,
   generated artifact. Count every medium a change forces to move; classify each site by role.
6. **Enforcement by omission** — rule enforced on some family members, not others. Flavors lacking
   the guard = second owner by absence; invisible to every search for a second implementation.
   Enumerate the family, check each member.

### The change challenge

Not "do they look alike" but "how many authoritative definitions must one change touch". Posit a
specific plausible change (new field kind, another error code, different default, one more
relation hop); count definitions that must move together. Exercise the rule's variation axes, not
one convenient change: three axes → three challenges.

Count > 1 = duplication, shared token or not. Count = 1 = independence, even if identical text.
Record each change posited + definitions forced; that count is the evidence. Consumers, oracles,
projections that also move: listed under their own headings, not counted.

[export_dry_review.py][export] `audit` = definitions, importers, references, exact duplicate bodies,
repeated literals, concept matches; its fingerprint hashes a docstring-stripped AST body and
separates sync from async → finds textual twins only. `check` = artifact names every target
definition, not that it reasoned. Orientation tools; never findings, never a gate on judgment.

## Deciding and consolidating

First try to DISPROVE shared responsibility: inputs, outputs, errors, state transitions, timing,
framework hooks, extension points, reasons to change. Read test bodies + public docs; names +
structure ≠ proof. Uncertain behavior → small executable experiment under
`docs/dry/temp-tests/<scope>/` (untracked). Source-mutating experiments run on a COPY there, never
the live tree. Record command + what it proved.

Confirmed family → ownership decision (principle 7), then the shape: reuse/extend an existing
owner; move policy from callers into the owning object/lifecycle; parallel representations → one
canonical record; parameterize genuine variation w/o hiding distinct behavior; delete the obsolete
path instead of abstracting both; reshape tests so setup is shared, behavior explicit.

### The finding record

Every finding, consolidated or rejected:

- **Contract + variation** — the rule; axes it legitimately varies on.
- **Sites + roles** — every site tagged definition / consumer / oracle / projection.
- **Challenges** — each change posited + definition count.
- **Owner + lifetime** — chosen owner w/ responsibility reasoning; principle 4 lifetime fields for
  any stored derivation.
- **Migration** — what each former definition becomes (call, declaration, deletion).
- **Distinct behavior** — what stays separate/compatible; where recorded.
- **Proof** — tests/experiments showing observable equivalence (principle 8), each
  `static-reviewed` | `execution-deferred` | `execution-verified`.
- **Gate** — the oracle that fails on re-divergence + evidence it CAN fail (asserting a name or
  existence passes for a hand-rolled copy). One owner + no oracle able to detect a second = a
  finding; the gate is its deliverable.
- **Coupling** — findings that must land together + why (generated slot collides, import moves).
  Visible to a reviewer reading one finding alone.
- **Freshness** — inputs inspected; any change reopens the finding.

Fields only where they apply; a finding is a decision aid, not a catalog entry. Finding line
estimate = per finding; plan outcomes measure the cycle over the baseline diff; the two need not
agree.

### Rejected candidates

Carry the concrete contract difference + reconsideration trigger (the change that would make the
sites one rule). Durable home = the owner: one plain docstring clause (`FilterSet.get_fields`). Plan
lists the cycle's rejections w/ triggers. Prior rejection = input to the next cycle only as a
trigger to check, never a substitute for a fresh trace; "reviewed once" ≠ permanent.

### Tests

Remove tests of deleted internals only when each distinct behavior demonstrably survives as a case
on the owner. Boundary tests stay at the [AGENTS.md][agents] tier; oracles never rewritten to read
from the owner they check. Owner coverage ≠ every former behavior still runs. Intentional test
repetition stays when it keeps behaviors independently legible. Every oracle a finding relies on
must be shown able to fail for the divergence it guards (`scripts/prove_failability.py`).

### Defects found while tracing

Reading for contract finds non-duplication bugs: docstring contradicting its body, guard one flavor
lacks, layering claim the imports contradict. → `## Defects` in the artifact; never fixed inside the
item; never dropped. Before closeout Worker 0 homes each on a NAMED owning card (unowned deferral
dies).

### Zero-edit result

Legitimate when: matrix discharged, challenges recorded w/ counts, strongest rejections carry
contract differences + triggers, backstop shows nothing unassigned. Token single-owned rule ≠
admission ticket.

## Cycle

### Plan

One plan per release via the planner (inventories current source; refuses to overwrite):

```shell
uv run python docs/dry/export_dry_review.py plan \
  --target-release <X.Y.Z> \
  --mode <autonomous|pause-after-each-item>
```

`docs/dry/dry-<release>.md`: every `.py`, one folder integration item per package folder, project
integration, final test gate. Artifacts: `dry-file-<path>.md` (`/`→`__`, `.py` dropped),
`dry-folder-<path>.md`, `dry-project.md`. Worker 0 appends what the planner doesn't generate:
`## Responsibility index` (family, owner, files covered, holding item, status); `## Families` (one
`dry-rule-<family>.md` item per discovered family, added as found); `## Outcomes` (closeout). Plan
already exists for the release → continue it under a dated `## Run` heading, never replace; reopen
items whose inspected inputs changed since verification.

### Baseline

Per item Worker 0 records `ITEM_BASELINE=$(git stash create)` (empty → compare w/ `HEAD`) +
`git status --short` + untracked files under the package. Stash object = tracked changes only;
listings = the rest. Baseline-dirty files = concurrent work: never edited, reverted, tidied.
Item-scoped diff = `git diff <baseline> -- <paths the item touched>`.

### Workers

Fresh workers per item; author never approves own change. No worker reads another's
`docs/dry/worker-memory/`; artifact + item-scoped diff carry everything. Role files
[worker-0.md][worker-0], [worker-1.md][worker-1], [worker-2.md][worker-2] = role delta only; this
doc is canonical.

1. **Worker 1** traces the family/target system-wide, tries to disprove each candidate, writes the
   artifact; confirmed consolidation → implements at the owner w/ permanent tests in the same
   change. `Status: fix-implemented` for edited AND proved zero-edit results. No edit rights
   (design pass) → `Status: designed`: findings complete + unapplied, proofs ≤ `static-reviewed`;
   Worker 0 routes to a Worker 1 w/ edit rights or to Rio.
2. **Worker 2** re-traces independently; challenges equivalence + ownership; confirms matrix
   discharged against the target's REAL surface (claimed inapplicability judged on its reason);
   confirms definition counts; zero-edit item → searches for a real consolidation before
   accepting. `verified` or `revision-needed` w/ concrete named candidates.
3. Revisions → Worker 1. Worker 2 alone completes a plan item. Verification stale (item reopens)
   when any input its freshness field names changes.

Worker 0 coordinates + preserves baseline; never reviews, implements, approves. Cross-file changes
expected when a family reveals a package-owned rule. Unrelated cleanup out of scope.

After an edit: `uv run ruff format .`, `uv run ruff check --fix .`. Pytest only on Rio's explicit
authorization; worker prose never converts dispatch into it; a proof needing a run it didn't get =
`execution-deferred`. Changelog edits need explicit authorization. Only Rio commits.

### Artifact

```text
# DRY review: `<family or path>`

Status: investigating | designed | fix-implemented | revision-needed | verified

## System trace

What the target owns, sites found, connected behavior examined.

## Verification

### Matrix

Each axis searched or ruled inapplicable, for the family as a whole.

### Challenges

Each rule in the family: changes posited, definition counts; experiments w/ commands + proof status.

## Findings

One finding record per rule, consolidated or rejected.

## Defects

Non-duplication defects found while tracing, each w/ the owner it routes to.

## Judgment

Short overall conclusion.
```

Worker 1 appends `## Implementation (Worker 1)` on tracked changes; Worker 2 appends
`## Independent verification (Worker 2)`; later passes append `## Iterations`. Nobody erases prior
reasoning. No inventories, copied tool output, empty placeholders.

### Final gate and closeout

All file/family/folder/project items verified → Worker 1 asks Rio to authorize `uv run pytest`
(unless already given). Passes only when the suite passes + package coverage stays 100%. Record
failures, coverage, skips, xfails; route each failure to its owning item. Package source change
after the gate invalidates it.

Worker 0 fills `## Outcomes` BEFORE deleting anything: families whose definition count dropped
(before/after owners); machinery deleted; rejections w/ triggers; families left open; coupling
introduced; net source change over baseline; test result; concurrent work untouched. Item artifacts
= per-cycle scratch; their evidence survives only here. Then remove only this run's
`docs/dry/temp-tests/<scope>/` dirs + `docs/dry/worker-memory/` contents, by explicit path. Never
recursively clear `docs/dry/`; never delete another run's scratch.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->
[export]: export_dry_review.py
[worker-0]: worker-0.md
[worker-1]: worker-1.md
[worker-2]: worker-2.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build]: ../builder/BUILD.md

<!-- django_strawberry_framework/ -->
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
