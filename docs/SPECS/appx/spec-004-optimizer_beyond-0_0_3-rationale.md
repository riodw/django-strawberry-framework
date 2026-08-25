# Rationale: spec-004 — Optimizer beyond strawberry-graphql-django (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-004-optimizer_beyond-0_0_3.md`][spec-004]. The spec is the
contract and states only what holds; everything that explains **how it got there** lives here: the
argument each slice opened with, the implementation shapes each slice proposed and
where the shipped code departed from them, the build order the document once recommended, the
alternatives each decision rejected and why each lost, and every claim the spec once made and may
no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass. **The move
happened long after the release, not before the build.** Card `DONE-004-0.0.3` shipped eleven
patch versions ago and the rule that gates a build on this move did not exist then; this pass
supplies it.

## How to read this file

- **One entry per spec section**, named by the section's own heading. A section this pass cut
  nothing from has no entry here — that is not an omission, it means the whole section is contract.
- **Two labels, two fates, applied to an item by where the bulk of it went.** *Moved* means the
  wording is reproduced here. *Cut* means it is in **neither** file: what follows the label is an
  account of what it said and why it went, and git history is the only record of the wording. Both
  are index entries over whole sections, paragraphs, and clauses, so a cut item can still leave a
  sentence standing in the spec, and a quotation here can be of surviving spec prose the entry is
  discussing rather than of moved text. **Where the index and an item's own entry disagree about
  where a piece of text went, the entry is the accurate one** — that tie-break settles provenance
  and nothing else; whether the spec still *makes* a claim is settled by the spec itself, and
  neither the index nor an entry is an authority on that. `## Provenance of this record` files
  every item under one of those two, plus one for what was deleted with no account kept at all, one
  for the rules restated in the spec, and one for what was deliberately left standing there.
- **What an entry's closing claims block is — and which of the two kinds you are reading.** There
  are two, and the label tells them apart. Entries under `## Entries keyed to the spec` close with
  the modal `**Claims the spec may no longer make.**`, which is a worklist, not a receipt:
  [`BUILD.md`][build] requires every entry to carry "any claim the decision once made and may no
  longer make", and that is what the block holds, in the corpus's own words — a claim is listed
  because the decision is no longer entitled to it, either because the text carrying it was cut or
  because the shipped package falsified it. For those entries it is **not** a record of retractions
  already performed, and it could not have been: the rationale-extraction pass moved the
  deliberation out and deliberately did not reconcile the spec against the package, so it can only
  have retracted what it removed. Several claims it lists were still stated in the spec's surviving
  prose when it closed, and each of those was the reconciliation item's to retract rather than a
  retraction already made — those blocks are where it met them, and `## Standing notes` carries the
  ones a sweep meets first. Entries under `## The reconciliation pass — what the spec now states`
  close with the factual `**Claims the spec no longer makes.**` instead, because that pass **did**
  perform the retractions it lists; the divergence is defined in that section's own
  `**On the label.**` preamble and neither spelling may be levelled to the other. A block whose
  label says more than either has been checked against the spec sentence by sentence and scopes the
  stronger claim in its own words.
- **Who reads it.** The role-by-role answer is [`BUILD.md`][build] `### Who reads it, and when`,
  which is that mechanism's canonical home. A reader looking for what the package *does* wants the
  spec, not this file.
- **This spec has no numbered Decisions.** It predates that convention, so the key is the heading.
  The eight slice sub-headings carry an em dash, and the two sluggers in play disagree on how many
  hyphens that produces — the repo's own slugger collapses the whitespace run to one hyphen where
  GitHub emits two — so every slice entry keys to the parent [`## The eight
  improvements`][spec-004-improvements] anchor and names its own heading in the entry title, the
  same disposition [`spec-002`'s rationale][spec-002-rationale] took for the identical hazard. Two
  entries key to headings that no longer exist in the spec at all (`## Priority and ordering` and
  the eight `**The win.**` paragraphs); each names the surviving section its argument bears on.
- **This spec is a member of an optimizer family, and the family's own story is not retold here.**
  Why the optimizer became its own document, and why O4 was then extracted into a document of its
  own, are [`spec-002`][spec-002]'s and [`spec-003`][spec-003]'s deliberation and are recorded in
  [their][spec-002-rationale] [rationale files][spec-003-rationale]. What belongs here is only the
  B-slice designs' own deliberation.
- **What the rationale-extraction pass did NOT do.** It did not reconcile the spec against the
  shipped package. This file records where the shipped code *departed* from a proposed shape,
  because that departure is the deliberation — a rejected shape and the one that beat it — but it
  does not decide how the spec's surviving prose should now read. That disposition belongs to the
  reconciliation item, and `## Standing notes` lists what this pass deliberately handed to it.
- **Read `## Standing notes` before editing the spec.** It records the sentences this pass left
  standing on purpose, two glossary links it re-sited, and one document-structure defect its own
  deletion happened to close. All of them are things a passing sweep would otherwise "correct" or
  miss.

## Provenance of this record

- **Moved** — the sentences and clauses this file reproduces inside quotation marks, quoted rather
  than paraphrased because the exact wording is what is being judged: a rejection's own stated
  reason (`### B3`'s `strict=True` sentence, `### B4`'s untyped-shapes clause) or a claim the
  package has since falsified (`## Priority and ordering`'s "pure polish item" sentence). Most of
  those wordings left the spec and exist here and nowhere else; a few quote spec prose that
  survived, because what the spec still says is the entry's subject. **No section, paragraph, or
  fence was moved whole.** Against the pre-move spec — the 33,928-byte blob this pass started from,
  which git holds unchanged — this file reproduced **192 of its 4,934** eight-word shingles when
  the pass closed, in **41** contiguous runs whose longest is 27 words and whose median is three
  shingles. Method: drop each file's bottom link-definition block, fold every non-alphanumeric run
  to whitespace, lowercase, take distinct 8-word shingles. Both inputs are fixed, so the
  measurement stays re-derivable; a count taken against the *current* spec would not be, and the
  one this bullet first carried was falsified by a single later edit to that spec.
- **Cut, with a prose account kept here** — the eight `**The win.**` paragraphs that opened each
  slice; all **eight** fenced pseudo-code blocks (one per slice); the whole of
  `## Priority and ordering`; the `**Cache lifetime (spike completed 2026-04-30)**` narrative in
  `### B1`; the rejected untyped hint-value shapes in `### B4`; the rejected `strict=True` kwarg in
  `### B3`; the second nested-path-construction approach in `### B3`; the "complementary to B1"
  derivation in `### B7`; and the two sequencing clauses in `### B5`. **This file carries no code
  fence at all.** Each entry below *describes* what its proposal did, which alternative beat it,
  and what shipped instead. That is the prescribed disposition rather than an economy: proposed
  code that landed under a different name is prose the current decisions have falsified, and
  [`worker-1.md`][worker-1] `### Performing the rationale move` rule 2 deletes rather than moves it
  — while the *account* of a proposal and the shape that beat it is deliberation, which is exactly
  what this file is for.
- **Deleted with no account kept** — the fences' *bodies*: their statement sequences, signatures,
  privacy, and file placements. Where naming a proposed symbol is what makes a departure legible,
  the entry below names it (`build_dotted_path`, `_collect_reachable_types`,
  `cls._optimizer_field_map`, and the like); nothing reconstructs how a fence was written. What
  each proposal *meant* is recorded below; what it *spelled* is not, except where the spelling is
  itself the contract (the sentinel context key, the `(name, value)` pair shape, the snake-cased
  field-map key).
- **Restated in the spec, not moved** — five rules that lived only inside cut text and are
  instruction rather than deliberation. Each is called out in its entry below under *"Kept in the
  spec"*: the `(name, value)` pair shape of the cache key's variable frozenset and its
  omit-rather-than-default rule; the `dst_optimizer_planned` context key the strictness sentinel is
  stashed under; the snake-cased keying of the precomputed field map; the plan cache's
  least-recently-used eviction discipline; and the `check_schema` public-API sentence. A builder
  who never reads this file must still write all five, so all five stayed.
- **Deliberately left in the spec by this pass** — every present-tense status claim about the
  pre-implementation codebase and every symbol name outside a fence, however plainly the package
  falsifies them. A status claim moved into a rationale file is neither a legitimate entry here nor
  the deletion the move prescribes for falsified prose, and its disposition against the shipped
  package is the reconciliation item's call. `## Standing notes` enumerates them.

## Entries keyed to the spec

### The eight `**The win.**` paragraphs — a slice-opening argument, not a contract

Spec: bears on [`## The eight improvements`][spec-004-improvements] and
[`## Problem statement`][spec-004-problem]. The `**The win.**` label no longer appears in the spec.

*Cut — one paragraph per slice, eight in all.* Each opened its slice by naming the behaviour it
improves on and why this package would do better — `strawberry-graphql-django`'s in most of them,
this package's own in B5, B7 and B8: "strawberry-graphql-django walks the selection tree on every
request" (B1); it "emits `select_related("category")` anyway, pulling the entire `Category` row
across a JOIN for nothing" (B2); it "assumes consumers will notice N+1 via SQL logs or
django-debug-toolbar. We hand them a smoke alarm instead of a smoke detector" (B3); its
"optimization hints live on per-field decorators … fine for their decorator API, awkward for ours.
DRF teams will reach for this without asking" (B4); the plan on the context "makes the optimizer's
behavior observable instead of magic" (B5); "None of the existing libraries ship this" (B6); the
walker "rebuilds `{f.name: f for f in model._meta.get_fields()}` on every walk" (B7); the
optimizer "blindly stacks another `.select_related("category")` on top" (B8).

*Why they went.* The test [`worker-1.md`][worker-1] `### Performing the rationale move` sets is
whether an implementer needs the sentence to build the thing, and for seven of the eight the answer
is no: every factual claim inside them is restated in the same slice's `**Mechanism.**` paragraph,
which is where a builder reads. What is left once the restatement is subtracted is positioning —
the argument for why the package exists at all, which is [`GOAL.md`][goal]'s and `README.md`'s
subject, not a slice's. It is also the single largest uniform block of deliberation in the
document, and the class most tempting to keep, because it reads well.

*Alternative rejected — keep them and cut only the competitor's name.* It preserves the motivation
and removes the marketing, and it was the other live option. It lost because the motivation without
the comparison is a restatement of `**Mechanism.**`'s first sentence: the comparison is doing all
the work, so removing it leaves a paragraph with nothing of its own to say.

**Kept in the spec — two of the eight paragraphs survived, one whole and one in part.**

- **B8's, whole.** B5's and B7's name no competitor either, so naming none is not what kept it —
  what kept it is the test above: their factual content is restated in their own slices'
  `**Mechanism.**` paragraphs and B8's is not, so cutting it would have left the slice with no
  statement of the problem it solves. It describes the package's own pre-B8 behaviour and why the
  duplicate matters, which is the slice's problem statement rather than positioning. Its
  `**The win.**` label was dropped and not one word else; its present tense is a status claim and
  belongs to the reconciliation item.
- **B6's first sentence, relabelled `**Public API.**`.** It is the only statement anywhere in the
  document of the audit entry point's name, receiver, and argument — `DjangoOptimizerExtension`'s
  `check_schema(schema)` — and public API stays. Cutting the paragraph wholesale would have deleted
  the API from a spec that then specifies its behaviour for four more paragraphs. Only its closing
  positioning went ("Fail-fast at startup instead of N+1-fast in production. None of the existing
  libraries ship this.").

**One further clause was restated rather than cut, from a paragraph that otherwise went whole.**
B1's opened by naming the cache an **LRU**, which was the document's only statement of the plan
cache's eviction discipline — a rule a builder needs, carried into the sweep by a paragraph that
was otherwise positioning. It is now stated in `### B1` `**Cache storage.**`, and this file's
`### B1 — AST-cached plans` entry records why. It is the shape this class was most exposed to and the
reason the class is worth re-reading: a uniform sweep loses a carve-out that happens to sit inside
one member.

**Claims the spec no longer makes as any slice's own argument.** That `strawberry-graphql-django`
ships no schema audit, and that the package's hints are the DRF-shaped analog of a competitor's
per-field opt-out marker — each may well still be true; neither is a slice's to assert. The B1, B2,
and B5 comparisons — the per-request re-walk, the needless JOIN for an id-only FK selection, the
SQL-log-only observability — survive in one compressed sentence in [`## Problem
statement`][spec-004-problem], and that survival is deliberate, not a missed sweep: a problem
statement is the spec's statement of the gap its slices close, which is a goal and stays under
[`worker-1.md`][worker-1] `### Performing the rationale move`, and this document's own H1 makes the
comparison its subject. The sentence was kept whole rather than name-stripped for the same reason
the trim-the-name alternative above lost: the comparison is doing all the work.

### `## Problem statement` — the pointer into the ordering section

Spec: [Problem statement][spec-004-problem].

*Changed — one clause, as a direct consequence of deleting `## Priority and ordering`.* The
sentence read that the eight improvements "can land in any order after O3 … subject to the
cross-dependencies noted in each slice's "Depends on" section and the recommended sequence in
"Priority and ordering"". The second half of that conjunction now names a section that does not
exist, so the clause was re-pointed at this file. The `**Depends on.**` half is untouched: those
paragraphs are the dependency **contract** and stayed in the spec, which is exactly the distinction
the ordering section failed — a dependency is a constraint, a recommended sequence is an opinion.

Nothing else in the section moved. Its first paragraph is the problem the spec exists to solve —
the "But strawberry-graphql-django stopped there" sentence included, kept deliberately over the
eight-paragraph cut (see the `**The win.**` entry above) — and its "This spec covers eight
improvements" framing is a status claim the reconciliation item owns.

**Claims the spec may no longer make.** That a recommended build sequence lives inside the spec.

### `### B1 — AST-cached plans`

Spec: [The eight improvements][spec-004-improvements].

*Cut — the `**Cache lifetime (spike completed 2026-04-30)**` narrative, and this is the entry the
whole file exists for.* The paragraph reported a dated investigation into Strawberry's extension
lifecycle and reached a consumer-facing recommendation from it. What it found: `Schema` carried two
extension accessors, `_sync_extensions` (a `@cached_property`, instantiated once per schema and
reused across all sync requests) and `_async_extensions` (a plain `@property`, fresh instances per
access so concurrent async requests could not share state); and `get_extensions()` passed an
already-instantiated object through unchanged via an `isinstance` check. From that it concluded
that a consumer passing an **instance** got one object reused in both modes while a consumer
passing the **bare class** got fresh instances in async mode and therefore a zero cache-hit rate,
and it recommended in bold that consumers pass `extensions=[DjangoOptimizerExtension()]`, matching
what `strawberry-graphql-django` recommended at the time.

*The claim the decision may no longer make — the recommendation is now inverted, in both halves.*
The `_sync_extensions` / `_async_extensions` split does not exist at the package's declared
`strawberry-graphql>=0.316.0` floor: it was refactored into one per-request accessor,
`Schema.get_extensions`, whose body instantiates any entry that is not already a `SchemaExtension`
and which both `execute()` and `execute_sync()` call **per request**, in both modes. And the
instance form the spike recommended is deprecated upstream — passing it makes `Schema.__init__`
emit a `DeprecationWarning`. [`spec-029`'s rationale companion][spec-029-rationale] carries the
`P1.1 — stale extension-lifecycle model` finding that names spec-004's model as stale, and
[`spec-029`][spec-029]'s Decision 3 is the successor: the supported construction
is a **module-level singleton wrapped in a factory**, `_optimizer = DjangoOptimizerExtension()`
with `extensions=[lambda: _optimizer]`, which is the upstream-recommended callable form yet hands
back one shared instance per request. That is the form [`docs/README.md`][docs-readme] and
[`docs/GLOSSARY.md`][glossary] now document. **The direction of correction runs from spec-029 to
spec-004 and never the other way.**

*Alternatives rejected downstream, recorded here because they are the first three things a reader
will reach for.* The **bare class** and a **constructing lambda** both lose for the reason the
spike itself identified, only now in both modes rather than async alone: 0.316.0 re-instantiates
them per request, so the plan cache is cold every time. **Keeping the instance form** loses on the
deprecation warning alone. **Relocating the cache off the instance** — which would make all three
forms equivalent — was considered and is not needed, because the singleton factory satisfies both
constraints without it; spec-029 records it as explicitly out of scope rather than as a
prerequisite.

*Why the paragraph was cut rather than corrected in place.* Every load-bearing sentence in it is
false, so [`worker-1.md`][worker-1] rule 2 deletes rather than moves. But the *fact that a spike
happened, reached a conclusion, and had that conclusion inverted by an upstream refactor* is
precisely what a rationale file is for: deleting it outright would erase the only record of why
this package ever told consumers to pass an instance, and the next reader of spec-029's Decision 3
would have no way to see what it superseded.

**Kept in the spec — the two rules inside that paragraph the refactor did not touch.** Relabelled
`**Cache storage.**`, because a heading naming a completed spike cannot survive the spike's
removal:

- **The cache lives on the extension instance, as `self._plan_cache`.** Still true at HEAD, and
  load-bearing in a way the spike never anticipated: it is the *reason* the singleton factory is
  the required construction form. A reader who deletes this sentence makes spec-029's Decision 3
  look like an arbitrary style preference.
- **A bounded-size dict, not `functools.lru_cache`.** A rejected alternative that is also an
  instruction: a builder who does not read it reaches for the decorator first. It stays for the
  same reason a guard's reason stays. The *reason* the spec gave for the rejection did not survive
  the reconciliation — it said the key's model class is not hashable by `lru_cache`'s default, and
  a model class is an ordinary hashable Python class — so this bullet no longer reproduces it; the
  structural reason that replaced it is in the `### B1` entry under
  `## The reconciliation pass — what the spec now states`.

**Kept in the spec — the eviction discipline, which lived only in the cut `**The win.**` opening.**
That paragraph opened by naming the cache an **LRU**, and that word was the document's only
statement anywhere of what a bounded plan cache drops when it fills. It is instruction, not
positioning: a bounded cache has to decide what to evict, and clear-all or insert-order eviction
satisfies "bounded-size dict" exactly as well as LRU does, so a builder reading only the survivor
picks a policy from nothing. Worse, with the word gone the surviving `not functools.lru_cache`
rejection reads as a rejection of LRU *semantics* rather than of the stdlib decorator. So
`**Cache storage.**` now states least-recently-used eviction as a rule and rules out only the
decorator. What the shipped cache adds on top of the policy — its bound, and that it evicts a batch
rather than one entry — is a status claim about HEAD and belongs to the reconciliation item, not
here.

*Cut — the fence, which proposed the key construction.* It computed
`skip_include_var_names = collect_directive_vars(info.operation)`, folded them into
`relevant_vars` as `(k, info.variable_values[k])` pairs under an `if k in info.variable_values`
guard, formed `cache_key = (document_hash(info), relevant_vars, target_model)`, and did a
get-or-build against `_plan_cache` with the trailing comment "module-level or self, per lifecycle
spike".

*Alternative rejected — hashing the document.* The fence and the surviving prose both spell the
first component as a hash. The shipped key stores the **printed AST string** instead, together with
the printed definitions of every reachable named fragment. The reason is stated in the extension's
own docstring and is not a micro-optimization in reverse: a hash admits a collision, and a
collision in this key serves one document's optimization plan to a structurally different document,
silently and with no failure mode a test could catch. Storing the printed text removes the class
rather than making it improbable. The cost — a longer key — is paid once per document and memoized.

*Changed — the key grew from three components to five.* `target_model` survived exactly as argued.
Two more were added by later work: a **root runtime path**, so two root fields returning the same
model do not share a plan, and an **origin** discriminator separating a primary-return resolver
from a secondary one. Both are additions to the argument the spec makes, not corrections of it —
the section's own reasoning for `target_model` ("a cache hit from one root field would return the
wrong plan for another") is the same reasoning, applied to two collision classes it did not
enumerate.

*Changed — the collected variable family grew.* The section argues, correctly and for a reason that
still holds, that collecting *all* operation variables would explode the cache cardinality. The
shipped collector adds a second family the spec never mentions: the `first` / `last` / `before` /
`after` variables on **non-root** field nodes, because nested pagination values are baked into
windowed prefetch querysets and so must key the cache, while root pagination stays out because root
slicing happens after the plan is applied. That belongs to [`spec-033`][spec-033], and the
collection is deliberately a syntactic superset — over-collection costs a duplicate cache entry,
under-collection serves wrong data.

**Kept in the spec — the `(name, value)` pair shape, which lived only in the fence.** The prose
above the fence said only "extract just those values from `info.variable_values`", and the shipped
`frozenset` holds pairs. The distinction is not cosmetic: a set of bare names cannot distinguish
two executions of one document that resolved the same directive variable differently, which is the
entire property the component exists to provide. The fence's `if k in info.variable_values` guard
carried a second rule with the same standing — a collected name the operation supplied no value for
is **omitted**, not defaulted — so both were restated as prose in `**Directive-variable
extraction.**`.

**Claims the spec may no longer make.** That `Schema` has separate sync and async extension
accessors. That `get_extensions()` passes instances through unchanged. That consumers should pass
`extensions=[DjangoOptimizerExtension()]`. That the bare class is the only construction form with a
cold cache. That the cache key is built by the sequence the fence spelled.

### `### B2 — Forward-FK-id elision`

Spec: [The eight improvements][spec-004-improvements].

*Cut — the fence, which proposed the elision predicate inline.* It tested
`(field.many_to_one or field.one_to_one) and selected_child_scalars == {target_pk_name}`, returned
to the `select_related` path when `field.target_field != field.related_model._meta.pk` or when
`target_type.has_custom_id_resolver(target_pk_name)`, and otherwise did
`plan.only_fields.add(field.attname)` followed by `mark_fk_id_elided(field.name)`.

*Why it went rather than stayed.* Every rule in it is stated in the section's own prose —
`**Applicability.**` carries the two guards and `**Edge cases.**` carries the custom-resolver
fallback — so the fence was a restatement, and the two things unique to it are both wrong at HEAD.

*Alternative rejected — a flat `field_name`-keyed elision flag.* `mark_fk_id_elided(field.name)`
is that flag, and the spec's own `**Resolver change required.**` paragraph rejects it three
paragraphs later with the query that breaks it: an operation selecting `category { id }` in one
branch and `category { id name }` in another must elide in the first and not the second, which a
bare field name cannot express. The fence and the prose contradicted each other inside one section;
the prose is what shipped, and cutting the fence removes the contradiction. The shipped elision
records a tuple of branch-sensitive resolver identities rather than one name — one identity per
response key the selection is reachable under. That fan-out rule is [`spec-003`][spec-003]'s, which
states it in full; [`spec-033`][spec-033] multiplies it over nested-connection runtime prefixes.

*Changed — the FK-column append is shared, ordered, and gated.* The fence wrote the append inline
and immediately before the elision mark. At HEAD it is a shared helper the select branch and the
prefetch branch both call as their first statement, and the **order** the fence encoded only by
statement position is now a live invariant. [`spec-003`][spec-003] owns
that invariant and states both what it requires and what reversing it costs; naming the departure
is this entry's job, stating the rule is that spec's. The append is additionally gated on a
projection flag added by [`spec-035`][spec-035].

*Changed — a fifth exclusion the section does not name.* Composite primary keys are excluded from
eligibility. This is hardening added after the spec, not a correction of it: the section's four
guards are all present and all still correct.

**Kept in the spec.** Nothing from the fence; the surrounding prose already carried every rule that
survived, and the two that did not survive were the two the prose already contradicted.

**Claims the spec may no longer make.** That the elision flag is keyed by a bare field name. That the
predicate is written inline at the relation-dispatch site.

### `### B3 — N+1 detection in dev mode`

Spec: [The eight improvements][spec-004-improvements].

*Cut — the second approach to nested relation-path construction.* The section offered two: (a)
reconstruct the dotted path from `info.path`, graphql-core's `Path` linked list, walking `.prev`
and snake-casing each segment; or (b) have the extension stash a `(parent_type, field_name) →
full_path` mapping on `info.context` alongside the sentinel, for an O(1) lookup. It weighed them
("(a) is simpler and requires no extra bookkeeping; (b) is faster for deep trees") and instructed
the builder to start with (a) and move to (b) "only if profiling shows `info.path` traversal is
measurable".

*Alternative rejected — (b), the stashed mapping.* It never became necessary and does not exist.
(a) shipped as a pair of public helpers on the plans module, depth-bounded against a pathological
`info.path` chain. A different optimization landed in the place (b) was reserved for: the strictness
check accepts a pre-threaded planned-key set and a precomputed resolver key as keyword-only
arguments, so the forward resolver walks `info.path` **once per row** and shares that one walk
between the B2 elision test and the B3 lazy-load test, rather than once per consumer of the path.
That is a stronger result than (b) proposed, and **no spec owns it** — `git log -S"precomputed_key"`
over the resolver module returns one unrelated permission-consolidation commit, and `spec-035`
carries no threading vocabulary at all. It is stated here without an owner. The
profiling condition the instruction named was therefore never evaluated — which is worth recording,
because a reader finding no (b) in the code would otherwise conclude the instruction was ignored.

*Cut — the rejected `strictness` kwarg shape.* "Mixing a boolean (`strict=True`) with a future
string (`strict="raise"`) in the same kwarg was rejected to avoid a deprecation cycle when the
third level lands." The rejection is sound and the shipped kwarg is the three-valued literal it
chose; the *record* of the rejection is deliberation, and the API it produced stays in the spec as
`**Strictness API.**`.

*Cut — the fence, which proposed the detection loop.* It assigned
`info.context.dst_optimizer_planned = planned_relation_paths(plan)`, then in the resolver computed
`relation_path = build_dotted_path(info.path)`, tested membership, tested `will_lazy_load(root,
field_name)`, and either raised `OptimizerError(f"Unplanned N+1: {relation_path}")` or logged
`"Potential N+1 on %s"`.

*Why it went.* The section's **prose** is correct — the sentinel is a set of resolver keys shaped
`ItemType.category@allItems.category`, combining parent type, snake-cased field name, and the
runtime response path — and the fence contradicts it, keying the membership test on a dotted
**relation path** instead. Neither `build_dotted_path` nor `planned_relation_paths` exists; the
shipped check computes a resolver key from the parent type, the field name, and the runtime path,
and reports the field name plus an optional caller-supplied reason rather than a dotted path. A
fence that restates its own section's prose incorrectly is the worst of both: it is redundant when
right and authoritative-looking when wrong.

*Changed — the lazy-load probe grew a third arm and an override.* The section names two, Django's
instance `__dict__` for a forward FK and `_prefetched_objects_cache` for a many-side relation. A
third probes the windowed `to_attr` a nested connection writes, where a present attribute means the
window already served the page ([`spec-033`][spec-033]); and a force-unplanned flag bypasses the
"key is planned, therefore silent" short-circuit for the unsafe-elision fallback, so a planned key
cannot mask a genuine lazy load ([`spec-035`][spec-035]).

**Kept in the spec — the `dst_optimizer_planned` context key, which lived only in the fence.** The
`**Mechanism.**` paragraph said the sentinel is attached to `info.context` and never said under
what name. The key is exact at HEAD, and it is half of a two-sided protocol: the extension writes
it and the resolvers read it, and a builder implementing either side needs the other side's
spelling. It is now stated in `**Mechanism.**`. The B5 section states its own key the same way,
which is why the omission here read as an oversight rather than a policy.

**Claims the spec may no longer make.** That the strictness membership test is keyed on a dotted
relation path. That symbols named `build_dotted_path` or `planned_relation_paths` exist. That the
resolver may reach (b)'s stashed path mapping. That the lazy-load probe has exactly two arms.

### `### B4 — Meta.optimizer_hints`

Spec: [The eight improvements][spec-004-improvements].

*Cut — the untyped hint-value shapes the typed wrapper beat.* The `**`OptimizerHint` typed
wrapper.**` paragraph opened by naming what it was chosen over: raw strings (`"skip"`), bare
`Prefetch` objects, and dicts (`{"select_related": True}`) sharing one field-value position. Its
argument was that the mixture "works but reads awkwardly and makes `_validate_meta` validation
ad-hoc". The conclusion is contract and stayed, in the shorter form "a small typed class gives
every hint a uniform shape and one validation path"; the enumeration of the losing shapes is
deliberation and is here.

*Alternative rejected — a per-field opt-out marker only.* The cut `**The win.**` paragraph, and the
positioning sentence at the end of the dispatch paragraph, both argued that a boolean
"disable optimization" marker of the kind `strawberry-graphql-django` offers is strictly weaker
than a hint object, because the hint permits **positive** overrides — force a strategy, supply a
specific `Prefetch` — and not only opt-out. The conclusion is visible in the four members the spec
lists; the comparison that produced it is not needed to build them.

*Cut — the fence, which proposed the hint dispatch.* It read the hint with
`getattr(type_cls, "_optimizer_hints", {}).get(field_name)` and then branched in order: `SKIP`,
then `prefetch_obj`, then `force_select`, then `force_prefetch`.

*Why it went.* Its first line reads a class-attribute mirror the package retired: hints are read
from the registered type definition, through the walker's own hint resolver, and no
`cls._optimizer_hints` attribute exists anywhere in the package. That consolidation is
[`spec-016`][spec-016]'s. The branch **order** the fence encoded is moot rather than wrong — the
hint's `__post_init__` rejects every incompatible flag combination at construction, so no hint can
match two arms and no precedence between them is observable.

*Changed — a fifth hint member shipped.* `OptimizerHint.strategy(name)` selects the nested-
connection fetch backend and is validated when `Meta.optimizer_hints` is built. **No spec under
`docs/SPECS/` owns the seam it selects**: `spec-033` names "strategy" once, in passing, and the hint
itself landed well after that card shipped. [`docs/README.md`][docs-readme] "Nested connection
indexing" documents the backends, and that is what the spec cites — the same disposition the B4
entry in the reconciliation section below reaches. The four members this section
specifies are all present and unchanged.

**Kept in the spec.** Nothing from the fence. The four members, the single-import public surface,
the hints-take-precedence rule, and the `ConfigurationError` validation contract are all prose and
were untouched.

**Claims the spec may no longer make.** That hints are read off a `_optimizer_hints` class attribute.
That the hint kinds are dispatched in a defined order.

### `### B5 — Plan introspection via context`

Spec: [The eight improvements][spec-004-improvements].

*Cut — two sequencing clauses.* "B5 should land first so the context-stash pattern is proven before
dependents ship" and, from `**Depends on.**`, "This is an afternoon project." The first is the same
recommendation `## Priority and ordering` made at document scale and is accounted for in that
entry; the second is an effort estimate, which is the purest form of deliberation a spec can carry
— it constrains nothing and it expired on the day the slice landed. What stayed is the fact both
clauses rested on: B2 and B3 ride on this mechanism, which is a dependency and therefore contract.

*Cut — the fence, which proposed the stash.* It called `plan_optimizations`, tried
`setattr(info.context, "dst_optimizer_plan", plan)`, caught `AttributeError` and fell back to
`info.context["dst_optimizer_plan"] = plan`, then applied the plan.

*Why it went, and what the mechanism became.* Every rule in it is in the prose above it — object
context first, dict context as a fallback, the key name spelled out. The mechanism then generalized
twice, in ways that make the fence's three lines misleading rather than merely dated. The optimizer
now owns **five** context keys rather than one; the shape-agnostic read/write/delete dispatch moved
out of the optimizer into a shared utility that the request resource policy also uses
([`spec-047`][spec-047]); the set-valued keys **accumulate** through a union helper rather than
clobbering, with the plan key alone staying last-wins ([`spec-033`][spec-033]); and a
start-of-execution reset clears the whole family so a reused `context_value` cannot leak one
operation's elisions or planned keys into the next — a correctness fix with no spec ancestor at
all.

*Alternative rejected — treat the union rule as B5's contract.* It is tempting, because the
"defensive stash" this section designed is visibly its ancestor. It lost for the reason the whole
family follows: the union rule exists because a nested fallback can stash a second batch of
elisions for the same execution, which is a nested-connection problem this spec has no notion of.
The behaviour is named where a reader of this section would otherwise be misled, and nowhere else.

**Kept in the spec.** The key name `dst_optimizer_plan` and the collision-avoidance reason for it;
the object-then-dict stash order; the frozen-snapshot property. All were prose already.

**Claims the spec may no longer make.** That the spec recommends building B5 first — B2's and B3's
`**Depends on.**` requirement on it is a dependency contract and stayed. That the slice is an
afternoon's work. That the optimizer stashes one key on the context.

### `### B6 — Schema-build-time optimization audit`

Spec: [The eight improvements][spec-004-improvements].

*Cut — the fence, which proposed the audit loop.* It collected `reachable =
_collect_reachable_types(schema)`, iterated `registry.iter_types()`, skipped types not in
`reachable`, and then iterated `model._meta.get_fields()` appending a warning whenever
`registry.get(field.related_model) is None`.

*Why it went, and it is the sharpest example in the document of why a fence is a liability.* The
paragraph **two above it** requires the opposite of what it does: "walk only the relation fields
**exposed by the `DjangoType`** … not the full set from `model._meta.get_fields()`", because
Meta-hidden and `SKIP`-hinted relations are intentionally invisible to the optimizer and must not
be flagged. The fence walks `_meta.get_fields()`. A builder who trusted the fence over the prose
would have shipped false positives for every excluded relation — and the prose is what shipped: the
audit iterates the registered definition's field map and skips `SKIP`-hinted entries. The two
statements contradicted each other inside one section, and only one of them could be right; cutting
the fence removes the contradiction rather than adjudicating it in the spec.

*Changed — the reachability walk descends further than "root types".* It follows union members and
interface implementations as well as object fields. The interface arm is load-bearing rather than
incidental: a registered type reachable only through an interface-typed root field would otherwise
be silently skipped, which is precisely the failure the audit exists to prevent. The reach itself has
no spec owner — it predates [`spec-032`][spec-032] — but the Relay interface surface it protects is
[`spec-015`][spec-015]'s foundation, which spec-032 later extended.

*Changed — warnings are deduped by `(model, field_name)`.* One model may carry several registered
types, and without the dedupe the audit emits one identical warning per type. This is a
multi-registration artifact rather than generic defensiveness, and it follows from
[`spec-018`][spec-018]; the walk still visits every reachable type, because a secondary type may
expose a relation the primary hides.

**Kept in the spec — the `check_schema` public-API sentence**, relabelled `**Public API.**`; see the
`**The win.**` entry above for why that one paragraph survived the class cut. Nothing from the
fence: the reachability rule, the exposed-fields rule, the three per-field checks, the
returns-never-raises contract, and the `registry.iter_types()` prerequisite are all prose.

**Claims the spec may no longer make.** That the audit iterates `model._meta.get_fields()`. That a
symbol named `_collect_reachable_types` exists. That reachability is object fields from the root
types only.

### `### B7 — Precomputed optimizer field metadata`

Spec: [The eight improvements][spec-004-improvements].

*Cut — the "complementary to B1" derivation.* A whole paragraph arguing that B1 caches the plan
*output* while B7 caches the field-metadata *input*, so that "the hot path is: dict lookup for
cached plan → cache hit → return", and concluding "No `_meta.get_fields()` call ever appears in the
request path."

*Why it went.* It changes nothing about how either slice is built — each section already specifies
its own cache — and its closing sentence is contradicted by this same section's own
`**Walker needs registry lookup.**` paragraph, which says that an unregistered model falls back to
`model._meta.get_fields()`. That fallback is still live at HEAD, and it is now a documented dual
contract the walker warns about in place, because the fallback map holds raw Django fields where
the registered map holds field metadata objects. A derivation whose conclusion its own section
qualifies two paragraphs later is not carrying its weight.

*Cut — the fence, which proposed the map and its lookup.* It built
`cls._optimizer_field_map = {snake_case(field.name): FieldMeta.from_django_field(field) …}`, then
in the walker resolved `cached_map = getattr(type_cls, "_optimizer_field_map", None)` with
`field_map = cached_map or {f.name: f for f in model._meta.get_fields()}`, and dispatched on
`field_meta.is_relation`.

*Alternative rejected — the class-attribute mirror.* `cls._optimizer_field_map` is the shape this
slice designed and it is retired: the canonical store is the registered type definition's field
map, and no such class attribute exists anywhere in the package. It lost to single-source
consolidation ([`spec-016`][spec-016]) — a mirror on the class and a map on the definition are two
copies of one fact, and the class attribute was the copy without an owner. The *property* the slice
delivers is untouched: the map is built once at class creation and the walker reads it instead of
re-introspecting per request.

**Kept in the spec — the snake-cased keying, which lived only in the fence and the cut win
paragraph.** `**Mechanism.**` said "build a `dict[str, FieldMeta]`" without saying what the string
is. It is the snake-cased field name, because that is the vocabulary a selection is resolved
against; a map keyed on the raw Django field name misses every camelCase selection the schema
exposes. Both of its carriers were being cut in the same pass, which is the exact shape of the
carve-out this move is most likely to lose, so it was restated in `**Mechanism.**`.

**Claims the spec may no longer make.** That `_meta.get_fields()` never appears in the request path.
That the walker reads a `_optimizer_field_map` class attribute.

### `### B8 — Queryset optimization diffing`

Spec: [The eight improvements][spec-004-improvements].

*Cut — the fence, which proposed the delta.* It flattened `queryset.query.select_related`,
normalized `queryset._prefetch_related_lookups`, built a fresh
`OptimizationPlan(select_related=[…], prefetch_related=[…])` under the comment "do NOT mutate the
original (may be cached by B1)", and returned `delta.apply(queryset)`.

*Alternative rejected — a delta that carries only a plan.* `delta.apply(queryset)` assumes the
queryset the delta is applied to is the one that came in. It is not always: the shipped
reconciliation also **upgrades** a consumer's plain string lookup to the optimizer's `Prefetch`
object, which rewrites the queryset side, so the function has to hand back both halves and its
return is a `(plan, queryset)` pair. A reader of the fence would expect a one-sided `apply()`; the
two-sided contract is the thing that makes the string-upgrade path expressible at all.

*Changed — the cache-safety rule stopped being an instruction.* The fence and its comment asked the
builder to remember not to mutate a plan the cache may be holding. At HEAD the plan is finalized at
handoff — its directive lists become tuples, so a post-handoff append raises — and a merge onto a
finalized plan is rejected outright. **No spec owns that enforcement** — it is un-spec'd hardening,
and the spec names the enforcing symbols instead. Both the requirement and its enforcement stayed in
this document, which is where they belong.

*Changed — the reconciliation also drops what the queryset cannot traverse.* A companion step
removes planned `select_related` paths a consumer projection has deferred, which Django refuses to
traverse, and the dropped paths must stay visible to strictness so a de-planned subtree is not
silently treated as covered. Neither is a correction of the set subtraction this section
specifies; both are what "apply only the delta" turned into once the delta had to survive a
consumer's own projection.

**Kept in the spec.** The cache-safety requirement, the three `query.select_related` states, the
`prefetch_to` comparison rule, and the consumer-wins precedence — all prose, all untouched. The
section's opening paragraph also stayed; see the `**The win.**` entry above.

**Claims the spec may no longer make.** That the diff returns a plan alone. That not mutating the
cached plan is a discipline the builder must maintain by hand.

### The former `## Priority and ordering` — a build order for work released eleven versions ago

Spec: bears on [`## Problem statement`][spec-004-problem] and [`## The eight
improvements`][spec-004-improvements]. The `## Priority and ordering` heading no longer exists.

*Cut — the whole section, nine paragraphs.* It opened with a recommended sequence — B5, then B1,
B7, B3, B4, B2, B6, B8 — and then argued each position: B5 first because B2's and B3's
context-borne flags ride on its stashing mechanism and it is the smallest slice; B1 next because it
is the biggest performance win and depends only on a shipped slice, with the cache-lifetime spike
to precede implementation; B7 after B1 because together they remove all per-request introspection;
B3 after B5 because it consumes B5's pattern, with the `strictness` kwarg shape to be settled
before implementation; B4 after B3 because API-surface work benefits from a well-exercised walker;
B2 after the surrounding foundations because it is subtle — resolver stubs, `only()` interaction,
the visibility guard, field-metadata accuracy, strictness, hints, and custom-id interaction all had
to settle first; B6 late because the audit is ambitious, blocks nothing, and benefits from hints
existing; and B8 last.

*Why it went.* A recommended build order is deliberation by construction — it constrains nothing
about what the code must do — and this one expired when the eighth slice shipped. What it repeated
that *is* contract, the cross-slice dependencies, is stated once per slice in the
`**Depends on.**` paragraphs, which stayed; the ordering section was a second, weaker statement of
the same graph, told as advice rather than as a constraint.

*Alternative rejected — retense the section to past tense and keep it as a build record.* Someone
had already started doing exactly that: seven of the nine paragraphs were prospective while the B2
paragraph alone read "**B2 landed** after the surrounding optimizer foundations". A half-retensed
section is the worst available state, because a reader cannot tell which half is current, and
finishing the retense would have produced a build chronology inside a contract — which is the one
thing [`BUILD.md`][build] `## Spec rationale extraction` says a spec must never carry. The
chronology belongs here.

*The claim the section may no longer make — "B8 last because queryset diffing is a pure polish
item".* The full sentence read that "Django handles duplicates gracefully, so B8 is about debug-log
clarity and principle rather than correctness". The shipped B8 is not a polish item. It performs
subtree-aware reconciliation, it can upgrade a consumer's plain string lookup to the optimizer's
`Prefetch`, it drops planned `select_related` a consumer's projection cannot traverse — which is a
`FieldError` avoided, not a log line tidied — and its consumer-wins precedence is a deliberate
permission-boundary stance that [`spec-035`][spec-035] records as such rather than as an oversight.
The card body for `DONE-004-0.0.3` already says B8 "went beyond the initial simple exact-match
diff". Recorded here rather than corrected in place, because the sentence it appeared in was being
cut anyway and a corrected ordering rationale would still be an ordering rationale.

*A structural defect this deletion closed, as a side effect rather than as a reconciliation.* The
section sat **between** B6 and B7, so two of the eight slices lived below it and a reader working
down the improvements section found six. With the section gone, all eight sit under that heading
in order. No slice text moved to achieve it. `## Standing notes` records this because the
reconciliation item was told to expect the defect and should not go looking for it.

**Kept in the spec.** Nothing. Every cross-slice dependency the section restated is already in a
`**Depends on.**` paragraph, and each of those was checked before the cut.

**Claims the spec may no longer make.** That there is a recommended implementation sequence. That B5
is the smallest slice or B1 the biggest win. That the cache-lifetime spike or the `strictness` API
design is still ahead of implementation. That B8 is a polish item with no correctness content.

## Standing notes — what this pass deliberately did not do

None of these is a deferral in the sense of unfinished work. They are boundaries this pass drew on
purpose, recorded here because a do-not-touch note is worth nothing in a place nobody reads before
editing.

### The status claims were left standing, and they are the reconciliation item's

This pass cut the *deliberative* layer: competitive argument, proposal code, build order, effort
estimates, and a superseded spike. It did **not** touch the spec's present-tense claims about the
codebase, even where the package plainly falsifies them. The ones a sweep will notice first:

**Every item in this list has since been discharged**, by the reconciliation pass recorded under
`## The reconciliation pass — what the spec now states`. The list is kept as the record of what
this pass handed over rather than rewritten, so the spec headings it names are the ones that
existed when it was written; the reconciliation entry for each says what the sentence now reads.

- `## Current state` is a snapshot taken mid-build and never re-taken — it reports two B-slices
  shipped inside a section describing the state *before* the B-slices. It is also the sole carrier
  of two glossary anchors, so it cannot simply be deleted.
- `## Proposed improvements` proposes eight improvements the same document's
  `## Implementation checklist` marks complete.
- `### B1` `**Mechanism.**` still spells the cache key as a three-tuple over a document **hash**.
  The entry above records what shipped and why; the sentence itself was left for the
  reconciliation.
- `cls._optimizer_field_map` survives in the present tense, naming a retired class attribute, at
  **five sites across three sections** — count them rather than trusting this list: `### B4`
  `**Walker needs registry lookup.**`, `### B6`'s exposed-fields paragraph, and three separate
  sites in `### B7` (`**Mechanism.**`, which names it twice; `**Walker needs registry lookup.**`;
  and `**Test surface.**`). The `**Test surface.**` one is the site a sweep working from section
  prose alone misses, and it is absent from the build plan's own drift row. `### B4`'s
  `**Walker needs registry lookup.**` additionally still says the walker reads `_optimizer_hints`
  off the type class. One of the five sites is the sole carrier of two glossary anchors.
- `### B4` `**Validation.**` attributes two rejections to `_validate_meta`. That symbol **does**
  exist and is the `__init_subclass__` entry point, but it only normalizes the hints mapping
  (through `_meta_optimizer_hints`); the unknown-field-name and non-`OptimizerHint` rejections the
  sentence names live in `_validate_optimizer_hints`, called on the next line from the same
  `__init_subclass__` — and the shipped gates reject more than the spec's two rules. A rewrite that
  starts from "the symbol is a phantom" produces a different and wrong correction. It is the sole
  carrier of one glossary anchor.
- `### B6` `**Public API.**` calls `check_schema` a **classmethod**; it ships as a static method.
  This pass kept the sentence verbatim apart from its label precisely so the reconciliation owns
  the word.
- `### B6` `**Test surface.**` names a `check_optimizer` management command as future follow-up
  work. No such command was ever built and no card names it.
- `### B8`'s opening paragraph — the one `**The win.**` paragraph kept whole, with only its label
  dropped — states the package's own **pre-B8** behaviour in the present tense: "the optimizer
  blindly stacks another `.select_related("category")` on top". Shipping B8 is precisely what
  falsified it. The build plan's drift table carries no row for it — its B8 rows name the deleted
  ordering section, the cut fence, and the document-structure defect that deletion closed — so this
  list and the `**The win.**` entry above are the whole of the record the reconciliation item has.
- `## References` says graphql-core's AST node types are relevant to "the 'skip Strawberry
  conversion' optimization noted in B1's implementation". `### B1` notes no such optimization,
  and did not before this pass either — the reference was dangling on arrival.
- `## Implementation checklist` carries "B1 cache-lifetime spike" as a ticked prerequisite. That
  box is the last in-spec trace of the spike whose narrative this pass cut, and a checklist is
  contract scaffolding, so it was left alone.

### Two glossary anchors were re-sited, and neither was re-sited by re-adding narration

The spec's ten glossary anchors are each carried by exactly one link. `import_spec_terms` is what a
Done card's glossary-link set is rebuilt from, and it reads the companion `*-terms.csv`, never the
spec body; `scripts/check_spec_glossary.py` is the gate that every CSV term has a glossary entry
**and at least one spec link**. So dropping the last link for an anchor trips the gate rather than
the import, and the fix is always to re-site the link in surviving contract prose — never to edit
the CSV, which is what removes the term from the card's import chain outright. Two of the ten lived
inside text this pass cut:

- **`djangooptimizerextension`** was carried by the cut cache-lifetime spike. It now sits in the
  surviving `**Cache storage.**` sentence, which is where the extension instance is named as the
  thing the cache lives on — contract prose, not a fragment of the narration kept alive to hold a
  link.
- **`queryset-diffing`** was carried by the cut `## Priority and ordering` section's B8 paragraph.
  It now sits in the `### B8` heading itself, matching what `### B4` already does with
  `metaoptimizer_hints`. The heading's rendered anchor is unchanged, because both the repo's
  slugger and GitHub's render a heading down to its visible text before slugging.

The terms CSV was not opened. The remaining eight anchors were not touched.

### The `## Priority and ordering` deletion closed a document-structure defect

B7 and B8 were orphaned below the ordering section, so the improvements section visibly contained
six of its eight slices. Removing the section restored all eight under one heading without moving a
line of slice text. It is recorded as a consequence rather than claimed as a reconciliation edit,
and the reconciliation item should not spend a pass looking for a defect that is already gone.

### The `**The win.**` cut is the one an over-cut review should test first

Eight paragraphs of one shape were removed in one sweep, and a sweep is how a carve-out gets lost.
What survived it is enumerated once and deliberately not re-tallied here: the class's own survivals
sit in the `**The win.**` entry above under *"Kept in the spec"*, and every rule restated in the
spec — out of this class and out of the fences beside it — is listed in
`## Provenance of this record`. A tally written twice is a tally to keep in step. The test to apply
to each survival is the move's own: read the post-cut spec and ask whether a builder who never sees
this file could still write the code correctly.

The rescue worth studying is the plan cache's least-recently-used eviction discipline, the only one
the sweep initially missed, and where it hid is the point: `### B1`'s was the class's most technical
member, so the uniformity that made a wholesale cut defensible is exactly what buried an instruction
inside it. The generalisable rule is that a class cut uniformly must be read member by member for
the one sentence that is not of its class, and that reading is worth doing twice.

The same characterization was in the spec's own pointer text — the companion-pointer paragraph and
seven of the eight per-slice pointers (`### B8`'s opens on the ordering argument and carried no
such clause), all of them written by this pass — and it was corrected there rather
than handed on, because a pointer that misdescribes what it points at is this pass's own defect
and not the reconciliation item's. The companion paragraph no longer calls the moved class
arguments *against* `strawberry-graphql-django`, and `### B5`'s and `### B7`'s pointers now open
"The opening argument for this slice" where five of the remaining six still open "The competitive
argument",
because B5's and B7's paragraphs name no competitor and the others' do. The asymmetry is
deliberate: a harmonizing sweep must not level it back.

## The reconciliation pass — what the spec now states

The pass above moved the deliberation out and deliberately left every present-tense status claim
standing. This pass is the one that reconciled them: it restated each claim the shipped package
falsifies as the contract that actually holds, handed the surface later specs took over to those
specs by name, and dropped what the package never built. **The spec carries none of this
account** — that is the whole division of labour: the spec states the contract, and why it reads
that way is here.

**On the label.** Each entry below closes with `**Claims the spec no longer makes.**`, factual
rather than modal, because this pass performed the retractions. The entries in
`## Entries keyed to the spec` keep the modal `**Claims the spec may no longer make.**` because
that pass could only *list* what it had no mandate to retract. The two spellings mark two different
kinds of block, and `## How to read this file` defines both; do not level either.

**On restraint.** Spec-004 is the root of the optimizer's post-foundation surface, and three later
specs extended it directly: [`spec-033`][spec-033] (nested connections, the nested-connection
multiplication of the response-key fan-out, the pagination cache-key family),
[`spec-035`][spec-035] (the projection gate, the unsafe-elision fallback, and the record of
consumer-wins as a permission-boundary stance), and [`spec-029`][spec-029] (the extension-lifecycle
correction). Two rules B2 leans on run the other
way, out of the foundation: the response-key fan-out itself and the FK-column ordering invariant are
both [`spec-003`][spec-003]'s. Three things this list once handed to an extension are **not** an
extension's: the ancestry-aware prefetch absorption is B8's own, shipped with this card; plan
immutability is this document's requirement and its structural enforcement is un-spec'd hardening no
document states; and the once-per-row resolver-key threading likewise has no spec owner. The
standing rule for the family is
[`spec-002`][spec-002]'s own — each spec owns the surface it added.
So every one of those extensions is stated in one clause naming the behaviour and the spec that
owns it, and not one of their rules is restated. The temptation ran the other way on seven
paragraphs in particular (B1's variable families and cache tiers, B2's loud fallback, B3's third
probe, B5's key family, B8's pruning and its immutability enforcement); each got a sentence, not a
transplant.

### `## Problem statement`

Spec: [Problem statement][spec-004-problem].

*Changed — the framing sentence.* It read that the spec "covers eight improvements that the
existing libraries do not ship" and that "they can land in any order after O3 … is effective". The
first half is contract and is untouched. The second is a planning claim about unbuilt work: the
eight shipped, so what remains true is the dependency structure, and the sentence now says each
improvement rests on O3 plus whatever its own `**Depends on.**` paragraph names. The pointer at
this file for the recommended build sequence stayed.

*The first paragraph is untouched, by maintainer decision.* Its surviving competitive comparison
was escalated as a contract-level question at the move pass's second review and ruled on before
this pass ran; the decision, its reasoning, and the alternatives it rejected are recorded in
`docs/builder/build-004-optimizer_beyond-0_0_3.md`. That ruling settles the *competitor* sentence
only; the "eight improvements" framing above was always this pass's, and is now discharged.

**Claims the spec no longer makes.** That the eight improvements are still schedulable.

### `## Current state`

Spec: [Current state][spec-004-current-state].

*Changed — the section was a snapshot taken mid-build and never re-taken.* It listed O1–O6 as
"have shipped" and then, inside the same paragraph, reported two B-slices shipped — a state
description of the period before the B-slices that had been half-updated during them. It now states
the standing relationship instead: O1–O6 are the foundation the eight improvements extend,
[`spec-002`][spec-002] and [`spec-003`][spec-003] own that foundation, and the optimizer is
effective end to end on top of it.

*Alternative rejected — delete the section.* A spec whose slices all shipped arguably needs no
"current state" paragraph at all. It lost twice over: the paragraph is the only statement of which
foundation slices the eight rest on, and it is the sole carrier of the `only-projection` and
`fk-id-elision` glossary links, whose loss would break `import_spec_terms` for `DONE-004-0.0.3`.

**Claims the spec no longer makes.** That the state it describes precedes the B-slices.

### `## The eight improvements` — the heading itself

Spec: [The eight improvements][spec-004-improvements].

*Changed — the heading was `## Proposed improvements`.* A section proposing work the same
document's `## Implementation checklist` marks complete is a framing the document falsifies on its
own page. Renaming it is the smallest edit that removes the contradiction, and it moves no slice
text.

*Alternative rejected — keep the heading and fix only the sentences under it.* Cheaper, and it
leaves the first word a reader sees saying the opposite of the checklist. *Alternative rejected —
delete the checklist instead.* That trades a false framing for a lost delivery record, and the
checklist is contract scaffolding.

The rename re-pointed the anchor definition and every link text in this file that named the old
heading. The population is auditable by occurrence rather than by matching line
(`grep -o '\[spec-004-improvements\]' <this file> | wc -l`): **21** occurrences of the reference id,
being **20** body uses plus the one definition, and **all 20** body uses name the heading in their
link text — three spelling it inside a code span with the `##` prefix, 17 bare. One of the 20 was
missed at the rename and re-pointed a round later, and the figure recorded at the time ("nine link
texts") was that same defect seen from the other side: a count of what a pass touched cannot detect
what it did not touch, which is why the population and not the worklist is the number to state. No
other document links a spec-004 heading anchor, verified by grep across the tree.

**Claims the spec no longer makes.** That the eight improvements are proposals.

### `### B1 — AST-cached plans`

Spec: [The eight improvements][spec-004-improvements].

*Changed — the cache key is five components, not three, and the first is not a hash.*
`**Mechanism.**` specified `(hash(document), frozenset(skip_include_vars), target_model)`. The
shipped key stores the **printed** operation AST with the printed definitions of every reachable
named fragment appended, plus the root response path and the resolver's origin type. The reason for
printing rather than hashing is in the `### B1` entry above and is now stated in the spec too,
because it is a rule a builder would otherwise undo. The `target_model` argument the section made
is unchanged and now reads as the third of five bullets; the root-path and origin components close
the same collision class one level in, and several `DjangoType`s over one model — which is what
makes an origin discriminator necessary — is [`spec-018`][spec-018]'s surface.

*Alternative rejected — leave the three-tuple and note the additions in this file only.* It keeps
the spec shorter and leaves the document's central mechanism describing a key the package does not
build. A contract that is wrong about its own key is worse than a long one.

*Changed — the collected variable family, the cache's storage, and the invalidation story.* The
collector gathers nested-pagination variables as well as directive variables ([`spec-033`][spec-033]
owns the windows they feed); the cache is bounded at 256 entries and evicts a least-recently-used
quarter at a time; immutability is now enforced structurally at plan handoff — by named symbols
rather than by a sibling spec's contract — rather than asserted; and three further memos exist
around the plan cache.
Each is one sentence in the spec. The section's own reasoning — cardinality explosion, the
`(name, value)` pair shape, the omit-rather-than-default rule — is unchanged and was left word for
word where it stood. The one piece of it that did **not** survive is the next entry.

*Changed — why `functools.lru_cache` was rejected.* The conclusion held and the reason given did
not. `**Cache storage.**` said the decorator was unusable "since the cache key includes a model
class which is not hashable by `lru_cache`'s default": a Django model class is an ordinary Python
class, `lru_cache`'s key builder takes type objects without special-casing, and
`grep -rn lru_cache django_strawberry_framework/optimizer/` returns nothing, so no source reading
ever backed the sentence. It was HEAD text this pass rewrote the paragraph around and carried
forward unexamined. The reasons that do hold are structural: `lru_cache` caches a *function*, so it
cannot be bound to the extension instance the same paragraph requires, and it evicts one entry at a
time where this cache drops a quarter in one sweep. That is what the spec now states. *Alternative
rejected — drop the causal clause and keep the bare "hand-rolled".* It is the safe edit and the
wrong one: this is the one paragraph a builder reaching for the decorator would consult, so leaving
it with no reason invites the change the sentence exists to prevent.

*Changed — the extension-lifecycle statement the move pass deleted was not restored.* Deleting the
falsified spike left the spec with nothing at all about how the extension is constructed, which
matters precisely because the cache is instance-bound. The spec now carries a pointer:
the supported form is a module-level singleton wrapped in a factory, and [`spec-029`][spec-029]
Decision 3 owns that contract. *Alternative rejected — restate the corrected recommendation here.*
It reads as the helpful option and is the exact failure the family rule exists to prevent: two
documents stating one contract, one of which goes stale. The direction of correction runs from
spec-029 to spec-004, so spec-004 points.

*Changed — `cache_info()`.* The spec said it "mirrors `lru_cache.cache_info()`". It does not: it
returns `hits`, `misses` **and** `size`, its counters are incremented without a lock, and an
execution-memo hit touches neither counter, so `misses` counts walker builds rather than key
misses. A reader who took the mirror claim literally would read the counters as exact. Why the
unlocked counters are an accepted trade rather than a defect belongs here and not in the spec: the
cache can only lose hit rate under a lost increment or a double evict, never return a wrong plan.

*Changed — the deferred selection conversion is now stated.* Converted selections reach the cache
behind a zero-arg callable, so a cache hit never pays for the AST-to-selection conversion. It was
stated nowhere, and `## References` cited it as "the 'skip Strawberry conversion' optimization noted
in B1's implementation" — a reference that dangled from the day it was written.

*Changed — plan immutability is no longer credited to [`spec-035`][spec-035], because that spec
carries none of it.* The reconciliation first wrote the enforcement as spec-035's at both the B1 and
the B8 site. Re-derived three ways: `grep -c immutab` over spec-035 returns 0; its nine Decisions and
its whole slice checklist cover only the evaluated-queryset guard, the operation-type `.only()` gate,
and fragment type-condition narrowing; and `git log -S"def finalize"` over the plans module returns a
single commit predating spec-035's authoring by a month, with `_assert_under_construction` arriving
later still in an unrelated hardening commit. No document under `docs/SPECS/` states the enforcement
— [`spec-033`][spec-033] calls it "the finalize-to-tuple discipline" and points back at spec-004's
own cache-immutability property. The spec now names the two enforcing symbols instead of a sibling.
*Alternative rejected — leave the pointer and let a later pass make it true by editing spec-035.*
That inverts the family rule: the pointer would be the reason a document acquires a contract it never
chose. **The attribution came from the build plan's drift-table owner column** (rows D7, D26, and —
for the once-per-row key threading, corrected in this file's `## Entries keyed to the spec` half —
D13), copied rather than re-derived. It is the same failure the fan-out citation had, in the same
column of the same table; the plan now records that its owner column is weaker evidence than its
HEAD-reality column and that `git log -S` over the symbol is what settles provenance.

**Claims the spec no longer makes.** That the cache key is a three-tuple. That its first component
is a hash. That only `@skip`/`@include` variables key the cache. That `cache_info()` mirrors
`functools.lru_cache`'s. That a `weakref` callback resets a module-level cache — no such mechanism
exists anywhere in the package, and the cache was never module-level. That `functools.lru_cache`
cannot hash a model class. That `spec-035` owns the plan-immutability enforcement.

### `### B2 — Forward-FK-id elision`

Spec: [The eight improvements][spec-004-improvements].

*Changed — the dispatch site, the column append, and its ordering.* The mechanism named
`_walk_selections`; the elision check lives in the select branch (`_plan_select_relation`). The
FK-column append is shared with the prefetch branch, is gated by the operation-wide projection gate
([`spec-035`][spec-035]), and must run **ahead** of the elision short-circuit. That ordering
invariant is [`spec-003`][spec-003]'s and is stated there; the spec now names it and points, because
a reader of B2 alone is exactly who could reverse the two.

*Alternative rejected — restate spec-003's cost argument alongside the pointer.* The sentence first
landed carrying it: the same three moves in the same order as spec-003's own — the invariant, why an
elided branch that returns without planning a join leaves the column unprojected, and the closing
"nothing enforces it but the order itself". Naming the owner does not license reproducing the rule,
and the family's standing rule ([`spec-002`][spec-002]) is that one document states a rule and the
others state the behaviour and point. Two copies of one causal argument in two documents can
diverge, and the one that diverges is the copy. The requirement — the append runs first — is the
half that must be readable from B2 alone, and it stayed; the cost of getting it wrong is one hop
away in the document that owns it.

*Changed — a fifth exclusion, and the fallback is loud rather than clean.* Composite primary keys
are excluded. And the closing "pure performance optimization with a clean fallback" undersold a
fail-loud boundary: when a consumer projection defers the FK column the resolver falls back so that
strictness sees the access, rather than performing the silent per-row lazy load "clean" implies
([`spec-035`][spec-035] Decision 5). The stub also carries a database alias from the read router, so
it is routed like any other loaded instance ([`spec-023`][spec-023]).

*Changed — one identity per response key.* The branch-sensitive keying the section already
specified fans out: a selection reachable under more than one response key records one identity per
key, never one for the merged node. That rule is [`spec-003`][spec-003]'s — it states the fan-out in
full and, in the same sentence, delegates only the nested-connection multiplication of it to
[`spec-033`][spec-033] — so the spec now names spec-003 as the owner and spec-033 for the
multiplication. It was first written here crediting spec-033 alone, taken from the drift table's
owner column rather than from the sibling spec; the correction is the same discipline
`## The reconciliation pass` applied to the root-path cache-key component, arrived at one round
later.

*Alternative rejected — describe the elision record's shipped container.* The record is a tuple of
resolver identities appended through a shared helper. Naming the container would pin an internal
data shape in a contract that only needs the identity rule, which the section already states.

**Claims the spec no longer makes.** That the elision's fallbacks are all silent JOINs. That the
guard list is exhaustive at four. That the FK column reaches the projection unconditionally.

### `### B3 — N+1 detection in dev mode`

Spec: [The eight improvements][spec-004-improvements].

*Verified rather than changed — the sentinel and resolver-key prose is exact at HEAD.* The falsified
half of this slice was the fenced detection loop, cut by the move pass; the surviving prose survives
re-verification against `types/resolvers.py` unchanged.

*Changed — what the report names.* The spec said the warning names "the field, the parent type, and
the query path". It names the field, plus an optional reason a caller can supply. The parent type
and path are in the resolver **key**, which is a different thing from the message, and a test
written against the sentence would have pinned a message the package does not emit.

*Changed — the strictness parameter's declared shape.* The spec typed it
`strictness: Literal["off", "warn", "raise"] = "off"` and called it "a single keyword". The
constructor takes a plain `str` and validates it at construction, raising on an unrecognised value
at the call site. The three levels and their behaviours are unchanged. *Alternative rejected —
state the annotation.* An annotation is not the contract; the accepted values and the
fail-at-construction rule are, and they are what the spec now states.

*Changed — the path walk is bounded, and the probe has a third arm.* The reconstruction from
`info.path` is depth-bounded rather than an unbounded loop. The lazy-load probe grew a third arm
for a windowed connection's `to_attr` ([`spec-033`][spec-033]) and an override that stops a planned
key masking a genuine lazy load in the unsafe-elision case ([`spec-035`][spec-035]).

**Claims the spec no longer makes.** That the warning names the parent type and the query path. That
the constructor parameter is annotated `Literal`. That the lazy-load probe has exactly two arms.

### `### B4 — Meta.optimizer_hints`

Spec: [The eight improvements][spec-004-improvements].

*Changed — a fifth hint member, and the class's shape.* `OptimizerHint.strategy(...)` selects the
fetch backend for one nested Relay connection. The spec lists it and stops there: the backends and
their selection rules are the nested-connection fetch seam's, documented in
[`docs/README.md`][docs-readme], and restating them here would put the seam's rules in a document
that does not own them. `OptimizerHint` is also a frozen dataclass rather than the "small class (or
`enum` + factory methods)" the spec hedged at, and the "when B4 ships" clause on its re-export went
with the hedge.

*Changed — the walker reads hints off the registered definition.* The class-attribute mirror
`cls._optimizer_hints` was retired by [`spec-016`][spec-016]'s single-source consolidation and does
not exist anywhere in the package; the walker resolves the definition and reads `optimizer_hints`
from it.

*Changed — `**Validation.**` attributed its two rejections to the wrong symbol, and understated the
gate.* `_validate_meta` exists and is the `__init_subclass__` entry point, but the unknown-name and
non-`OptimizerHint` rejections live in its sibling `_validate_optimizer_hints`, called from the same
caller one line later. The shipped gate also rejects a hint on an **excluded** field and on a
selected **scalar** field, for a stated reason: the walker only reads hints after entering the
relation branch, so such a hint would silently drop the consumer's intent. `OptimizerHint` rejects
incompatible flag combinations at construction, which is why no dispatch precedence between hint
kinds is observable. *Alternative rejected — write the correction from "the symbol is a phantom".*
The drift table's first version of this row said `_validate_meta` did not exist; it does, and a
correction built on that premise would have deleted a true sentence and named the wrong entry
point. The row was corrected at source before this pass, and re-verified here.

**Claims the spec no longer makes.** That hints are read off a class attribute. That
`_validate_meta` performs the hint-value rejections. That the hint surface is four members. That
`OptimizerHint`'s shape is undecided between a class and an enum.

### `### B5 — Plan introspection via context`

Spec: [The eight improvements][spec-004-improvements].

*Changed — the stash dispatch, and one key became a family.* `setattr`-then-`__setitem__` is not the
whole rule: a `dict` (or `dict` subclass) is written through the mapping path so it round-trips to
the same read, and a context that refuses assignment is skipped rather than aborting the resolver
chain. The dispatch itself moved out of the optimizer into a shared utility
([`spec-047`][spec-047]). The optimizer now owns a family of context keys, cleared at the start of
each execution so a reused `context_value` cannot leak one operation's state into the next — a
correctness fix with no spec ancestor, so the spec states it as its own — and the set-valued keys
accumulate rather than clobber, which a nested-connection fallback needs
([`spec-033`][spec-033]).

*Alternative rejected — enumerate the five keys.* The spec would then carry the elision, planned-key,
lookup-path, and strictness key names, three of which are other slices' internals and one of which
is B3's, already stated in B3. The family property is what a reader needs; the roster is not.

**Claims the spec no longer makes.** That the optimizer stashes one key. That `setattr` is tried
first for every context shape. That a stash cannot be skipped.

### `### B6 — Schema-build-time optimization audit`

Spec: [The eight improvements][spec-004-improvements].

*Changed — `check_schema` is a static method, and it performs one check, not three.* The spec listed
three per-field checks. The audit warns on exactly one condition: an exposed relation whose target
model has no registered `DjangoType`. The "not hidden behind a custom resolver" check was never
built. The third listed check — forward FKs to unregistered targets — is not a separate check but a
narrower spelling of the first, which applies to every relation kind. The spec now states the one
condition and what the warning names, which is the type, the model and the field: not, as it
claimed, a field path and a suggested fix.

*Changed — reachability descends further, and warnings are deduped.* The walk follows union members
and interface implementations as well as object fields, because a `DjangoType` reachable only
through an interface-typed root field would otherwise be skipped silently — the exact failure the
audit exists to prevent; the interface surface it protects is [`spec-015`][spec-015]'s foundation,
extended later by [`spec-032`][spec-032]. Warnings dedupe on `(model, field name)` so a
relation exposed by two registered types over one model warns once ([`spec-018`][spec-018]); the
walk still visits every reachable type, because a secondary may expose a relation the primary hides.

*Dropped — the `check_optimizer` management command.* `**Test surface.**` named it, with
custom-resolver detection, as "future follow-up work within B6". Neither was built; no card names
either; and the package ships `export_schema` and `inspect_django_type` only. A spec is a contract,
not a wish list, so an eleven-version-old promise with no owner was removed rather than restated as
still-pending. *Alternative rejected — keep it and mark it deferred.* A deferral with no card and no
date is indistinguishable from a forgotten obligation, and the deferral is recorded where deferrals
belong: the build cycle's own deferred-work catalog. `inspect_django_type` ([`spec-029`][spec-029])
is the diagnostic that landed instead, and it answers a different question — one type's field
resolution, not the schema's optimizer coverage — so it is not a substitute and is not offered as
one.

**Claims the spec no longer makes.** That the audit detects custom resolvers that bypass the
optimizer. That its warnings carry a suggested fix. That `check_schema` is a classmethod. That a
`check_optimizer` command is coming. That `spec-032` owns the Relay interface surface the audit
must not skip — that foundation is `spec-015`'s, and spec-032 extended it.

### `### B7 — Precomputed optimizer field metadata`

Spec: [The eight improvements][spec-004-improvements].

*Changed — the map's home.* `cls._optimizer_field_map` is retired ([`spec-016`][spec-016]); the
canonical store is the registered `DjangoTypeDefinition`'s `field_map`. This slice's own property is
unchanged: the map is built once at class creation, keyed by the snake-cased field name, and read by
the walker instead of re-introspecting `_meta` per request. `FieldMeta` is a frozen dataclass and
carries more slots than the six the spec listed, so the list now reads as what it is — the
optimizer-relevant core, plus what the later relation work added.

*Changed — the `_meta` fallback is a documented dual contract.* The fallback for an unregistered
model is still live, but the two paths return different value shapes: `FieldMeta` on the registered
path, raw Django field objects on the fallback. The spec now says so, because the defensive
`getattr(..., default)` reads downstream are the only reason the two coexist safely, and a reader who
does not know that writes the read that breaks.

*Not changed — three test names still spell the retired symbol.* They are live code, not prose, and
their rename is carded elsewhere; this cycle writes no test file.

**Claims the spec no longer makes.** That a `_optimizer_field_map` class attribute exists. That
`FieldMeta` might be a namedtuple. That the two field-map sources are interchangeable.

### `### B8 — Queryset optimization diffing`

Spec: [The eight improvements][spec-004-improvements].

*Changed — the opening paragraph stated the package's own pre-B8 behaviour in the present tense.*
"the optimizer blindly stacks another `.select_related("category")` on top" is what shipping B8
falsified. The paragraph now states the condition it addresses — a consumer queryset that already
carries the optimization — and what B8 does about it. This is the one B8 item the drift table
carried no row for; it came out of the move pass's own standing notes.

*Changed — reconciliation returns a pair, and does more than subtract.* `**Mechanism.**` described a
set subtraction and an `apply()`. The subtraction is still the starting point, but the function
returns the delta plan **and** the queryset, because it can upgrade a consumer's plain string lookup
to the optimizer's `Prefetch` — which rewrites the queryset side, and which a one-sided `apply()`
cannot express. A companion step drops planned `select_related` a consumer projection makes
untraversable, and the dropped paths stay strictness-visible so a de-planned subtree is not treated
as covered. Consumer-wins is a permission-boundary stance, which [`spec-035`][spec-035] records as
such; the ancestry-aware absorption is B8's own, shipped with this card, so the spec claims it
rather than pointing at a sibling.

*Changed — cache-safety stopped being an instruction to the builder.* The requirement is the same
and stays in the spec. What changed is that it is now enforced: a plan is finalized at handoff, so a
post-handoff append raises and a merge onto a finalized plan is rejected. The spec names the two
enforcing symbols rather than a sibling spec, because no sibling spec states the enforcement.

*The "pure polish item" claim needed no edit here.* It lived in `## Priority and ordering` and went
with that section at the move pass; the `### The former `## Priority and ordering`` entry above
records the retraction. An eye working from the drift table alone will hunt a sentence that no
longer exists.

**Claims the spec no longer makes.** That the optimizer stacks a duplicate. That the diff is only a
set subtraction. That it returns a plan alone. That not mutating the cached plan rests on the
builder remembering to. That `spec-035` owns the plan-immutability enforcement. That the
ancestry-aware prefetch absorption is `spec-033`'s rather than B8's own.

### `## References` and `## Implementation checklist`

Spec: [References][spec-004-references], [Implementation checklist][spec-004-checklist].

*Changed — one dangling reference and one misattributed one.* The graphql-core entry cited a "skip
Strawberry conversion" optimization "noted in B1's implementation" that `### B1` never noted, before
or after the move. The thing that did land is the deferred conversion, now stated in B1, so the
reference points at something real. The Django entry called the `select_related` dict merge
load-bearing "for B1's cache correctness"; it is B8's reconciliation that depends on it.

*Changed — one parenthetical on the checklist.* The `B1 cache-lifetime spike` box carried
"(10-min investigation, precedes B1 implementation)", a sequencing claim about a prerequisite
eleven versions delivered, pointing at a section that no longer exists. The box stays — it is the
record that the prerequisite was delivered — and the parenthetical went. *Alternative rejected —
delete the box.* The spike happened and gated B1; deleting the box loses that, and this file's
`### B1` entry is what records that its conclusion was later inverted.

**Claims the spec no longer makes.** That B1 notes a "skip Strawberry conversion" optimization. That
the spike is still ahead of implementation.

### What this pass deliberately left for others

- **Three B7 test names spelling `_optimizer_field_map` — DISCHARGED.** They now name
  `DjangoTypeDefinition.field_map`, the store they actually assert against. The rename was a source
  change and so fell outside a documentation cycle; it landed separately.
- **The `_record_relation_access`-before-elision ordering invariant — DISCHARGED.** It was pointed
  at from B2 during reconciliation, which was the most a documentation cycle could do, and the
  guard itself landed separately as a live-tier query-count assertion across two parent
  cardinalities. B2's **Test surface** carries the row. Reversing the two operations fails it, along
  with the plan-shape rows that assert the FK column is projected on the elided branch.
- **The `check_optimizer` management command has no card.** Dropped from the spec, recorded above,
  and routed to the cycle's deferred-work catalog.
- **[`spec-029`][spec-029] calls `0.316.0` "the locked" Strawberry version.** It is the declared
  floor; `uv.lock` resolves higher. This file's own phrasing was corrected in this pass. Spec-029 is
  a read-only sibling here, so its wording is recorded as a deferred item and left alone.
- **[`spec-003`][spec-003] makes the same plan-immutability misattribution this pass corrected
  here — and so does its companion, six more times.** The spec hands the frozen membership sets
  computed at plan finalization to [`spec-033`][spec-033] and [`spec-035`][spec-035]; spec-035
  carries no plan-finalization contract at all (`grep -c immutab` over it returns 0, and
  `git log -S"def finalize" -- django_strawberry_framework/optimizer/plans.py` returns one commit
  dated a month before that spec was authored). **The class is the whole `spec-035` citation
  surface of that pair, not one line**: `grep -n '\]\[spec-035\]\|spec-035-optimizer'` over
  [`spec-003`'s rationale][spec-003-rationale] returns six body uses plus the definition, and every
  one of the six carries the error, in three escalating shapes.
  - **It credits spec-035 with the work.** #"Both are later hardening" hands it both the
    finalize-frozenset short-circuit and the single named reader for `_prefetch_related_lookups`;
    #"the plan is finalized before handoff" hands it the tuple swap;
    #"plan immutability, the projection gate" lists it among that spec's extensions (only the
    projection-gate item on that line is sound — it is [`spec-035`][spec-035] Decision 4).
  - **It asserts spec-035 has already stated it.** #"each already stated once in its own document"
    says so outright, and #"for the rest" points there for the remaining plan fields.
  - **It instructs a future pass to make it true.** #"'s to state", of the single-reader discipline,
    is the strongest form and the one this file's own B1 entry rejects as an alternative: a pointer
    is not a reason for a document to acquire a contract it never chose. Nothing under
    `docs/SPECS/` states that discipline — the only matches for the phrase family are the two
    sentences in that companion — and the reader itself,
    `optimizer/plans.py::_consumer_prefetch_lookups`, is dated 2026-05-06 by `git log -S`, six
    weeks before spec-035 was authored.

  Both files are read-only siblings in this cycle, so the deliverable here is the **enumeration,
  not the edit**: seven sites in all, and whoever fixes them decides for all seven at once, as the
  spec-029 item above asks. Fixing the one line the spec carries and closing the item is the
  failure this bullet exists to prevent.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../../GOAL.md

<!-- docs/ -->
[docs-readme]: ../../README.md
[glossary]: ../../GLOSSARY.md

<!-- docs/SPECS/ -->
[spec-002]: ../spec-002-optimizer-0_0_2.md
[spec-002-rationale]: spec-002-optimizer-0_0_2-rationale.md
[spec-003]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md
[spec-003-rationale]: spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md
[spec-004]: ../spec-004-optimizer_beyond-0_0_3.md
[spec-004-checklist]: ../spec-004-optimizer_beyond-0_0_3.md#implementation-checklist
[spec-004-current-state]: ../spec-004-optimizer_beyond-0_0_3.md#current-state
[spec-004-improvements]: ../spec-004-optimizer_beyond-0_0_3.md#the-eight-improvements
[spec-004-problem]: ../spec-004-optimizer_beyond-0_0_3.md#problem-statement
[spec-004-references]: ../spec-004-optimizer_beyond-0_0_3.md#references
[spec-015]: ../spec-015-relay_interfaces-0_0_5.md
[spec-016]: ../spec-016-fieldmeta_consolidation-0_0_6.md
[spec-018]: ../spec-018-meta_primary-0_0_6.md
[spec-023]: ../spec-023-multi_db-0_0_7.md
[spec-029]: ../spec-029-consumer_dx_cleanup-0_0_9.md
[spec-029-rationale]: spec-029-consumer_dx_cleanup-0_0_9-rationale.md
[spec-032]: ../spec-032-full_relay-0_0_9.md
[spec-033]: ../spec-033-connection_optimizer-0_0_9.md
[spec-035]: ../spec-035-optimizer_hardening-0_0_10.md
[spec-047]: ../spec-047-resource_policy-0_0_14.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md
[worker-1]: ../../builder/worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
