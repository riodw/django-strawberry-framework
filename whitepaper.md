# Square-free business logic: computing where a rule belongs, and proving it is stated once

> **Maintaining this file.** The paper states what is, never what was. An update rewrites the sentence it falsifies, in place; it never appends "previously", "the first version", "an earlier draft said" or a dated note beside the live text, and git holds the history. A fixed prototype defect is not paper content: it goes to the commit, and the section that described the behaviour is corrected to the current behaviour. A retracted *position* that a reader of an earlier draft may still hold gets one line in section 14 and no echo elsewhere. Open problems hold only what is open: when one is settled, its result moves into the section that owns it and the problem is deleted. Negative material (what a tool does not do, which gates are one-sided, which readings were wrong) is condensed to the one clause the argument needs. A figure is current or absent: a table whose numbers are known wrong is re-run or removed, never kept under a caveat. No instructions to the paper itself ("the paper must state..."): do what the sentence asks and delete the sentence. Before adding a paragraph, search the file for the claim; if another section holds it, point there instead of restating. Scratch files, agent reports and run scripts are not citable: what they established is stated here with its tag, and their names stay out.

Working draft, the maintainer's design note. Citation tags: [V] verified against a fetched source this cycle, [V via secondary] verified against a source that quotes the original, [A] abstract or docs summary only, [M] from memory, not yet checked, [V, absence] a negative result: the searches run this cycle found no source, which verifies the search and not the absence. Nothing tagged [M] may be cited in a published version without verification.

---

## 0. Origin

I started this package because I am obsessed with forcing things into their proper place and making code as DRY as it can be. The instinct comes from math: primality testing, factoring, reducing a fraction to lowest terms. I wanted a setting in `settings.py` that holds a number, starting high and tuned down the way coverage is tuned up, with a floor of 1. At 1, with no errors thrown, the business logic is maximally reduced.

The examples that started it: "title is required", "max 200 chars", "unique per shelf" belong on the model. "end_date after start_date" is an object looking at itself. "this email can't already have a pending invite" felt like the same thing. Then `cart.allowed_to_checkout = discount.expired == False and discount.region == user.region`, and the idea trailed off, because I was trying to place a composite as if it were atomic.

The hard questions were: what is a Level, what is a Leaf, how do you know a leaf is not a branch in disguise, and how do you enforce that each leaf is unique. This document is the current answer.

## 1. The problem

Large codebases have a failure mode that AI-assisted development made visible: the code is correct, the code is documented, and nobody knows where it goes. Writing a correct function is a local problem. Deciding where it lives is a global one. It needs the map of the whole system in working memory, and that map lives in senior heads, not in the repo. Humans hide the gap behind onboarding time. An AI agent shows it on every session, because it has the local skill at full strength and the global map at zero.

The symptom is misfiled as a DRY failure. It is a discoverability failure: "I did not know that rule already existed, so I wrote a second one." Over-applied DRY makes it worse, because every shared helper is one more thing a contributor must already know exists.

The empirical record says this is not a style complaint:

- Yang et al. (ICSE 2020) [V], 12 Rails applications: constraints live 76% in the DB, 23% in the application, 1% in the front end. 24% of application constraints are missing from the DB. Their checker found about 2,000 "Where" inconsistencies and 133 confirmed fields whose length or numeric limits conflict between app and DB. Their running example is a wiki title accepted by two layers and rejected by `varchar(30)`. A 22-issue sample from three Django apps showed the same distribution.
- Wang et al., EqDAC (ICSE 2023) [V]: of 30,801 industrial data constraints, 11,538 (37%) had an equivalent variant written by someone else and 7,842 (25%) were redundant.
- Juergens et al. (ICSE 2009) [V]: 724 inconsistent clone groups across five systems, 107 confirmed faults. About three quarters of inconsistencies were intentional, which matters for any detector (section 5).
- Bailis et al., Feral Concurrency Control (SIGMOD 2015) [V]: Rails uniqueness validations run as SELECT-then-INSERT and lose integrity under concurrent writes. A set invariant enforced above the database is not merely redundant. It is wrong.

So: the same rule stated in several places, the places disagree, and some of the places cannot enforce the rule correctly at all.

## 2. Thesis

A business rule is reduced when it is authored exactly once, at the owner determined by its footprint and its polarity (section 3), and every other site that needs it composes the named rule or receives a derived copy.

A codebase is reduced when every rule is. A framework whose rule language is restricted enough to be analyzable can compute, for each rule, its footprint, its owner, its multiplicity, and whether a composite is a branch in disguise. It can then enforce a reduction budget as a CI ratchet, the way `fail_under` enforces coverage.

Three things in that sentence are prior art and are cited as such (section 13): "each rule once" (Ross, Halpin, the Business Rules Manifesto, WebDSL), decidable equivalence in a restricted rule language (Cedar, OCL checkers, DMN, EqDAC), and deriving an upper-layer check from a lower-layer declaration (Django 4.1 `validate_constraints`, Hibernate DDL generation). Three things appear to be new: the owner computed from the footprint and the connective the rule enters under, across a ladder that spans DB constraint to workflow, the multiplicity metric with its four duplication kinds and a CI floor, and the two-direction placement rule (section 4).

## 3. Definitions

**Rule.** A named predicate over a footprint, declared in the framework's restricted rule language, with an owner. Not arbitrary Python.

**Footprint F(P).** The minimal set of (object, relation path, field) values and context inputs a predicate must read. The free variables of the rule.

**Owner.** The tightest scope, in the binding order defined under *Scope* below, that covers the entire footprint and whose composition law admits the rule's polarity. Tightest means fewest bindings, not least code governed: the schema binds only the actor, so it is the tightest scope there is, and the lead example (a staff bypass owned by the schema) is a rule at its tightest scope, not an exception. The owner is computed, not chosen.

**Leaf.** A maximal subtree of a rule's canonical form whose operands all compute to one owner. The split is on the operands of the canonical tree, not on a normal form: `A OR (B AND C)` with A actor-only is two leaves, A and `B AND C`, where its conjunctive normal form would state A twice. Two leaves are the same leaf when their canonical forms are equal, whatever site or owner each was authored at: identity is by form, placement is by owner.

**Branch in disguise.** A junction whose operands compute to different owners. The reducer splits it, recursively, and places each operand at its own owner. The original composite survives as a named composition of the leaves, which is legitimate, and it must survive: the leaves are what is authored and counted, the composition is what is enforced, so splitting `active AND (public OR shelf.open)` into its leaves changes nothing the actor sees. A move to the schema does change meaning, in both polarities: a grant moved to the bypasses applies to every type, not only the one that stated it, which is the move the lead example wants, and a restriction moved to the schema's restrictions also holds on every type that never stated it (section 12, the rule-less type). That is why a bypass on one type is stated too low (section 4), and why the gate reports either move rather than performing it.

**Authored copy.** A statement of a rule written by a person. Counts toward multiplicity.

**Derived copy.** A statement generated from an authored one by the framework (a `ValidationError` raised from a `CheckConstraint`, DDL emitted from a validator, an RLS policy compiled from a `Q`, a mixin's rule applied to each concrete model that inherits it). Counts zero. Without this distinction the metric penalizes the best existing practice and contradicts Yang's finding that some DB-plus-app duplication is deliberate. The prototype's audit (section 12) records a mixin rule once, at the declaring class, while the framework enforces it on every inheriting model: one authored copy, N derived ones. On the constraint rung the derivation runs both ways: Django derives the Python check from a `CheckConstraint` (`validate_constraints`), and the prototype's `ChoicesConstraint` derives the `CHECK` from a field's `choices`. A derived copy at the owner places the leaf: the authored site may sit a rung above, and M does not count it.

**Opaque rule.** A rule stated in arbitrary code where the framework can see that a rule exists but not what it reads or says: a hand-written `get_queryset` body, a `clean()` with control flow. It has no footprint, no owner, no canonical form, so it is outside the metric by construction. The opaque count is reported beside the metric and must trend to zero, in the same way an untested line is outside the coverage percentage until it is covered.

**Blessed.** A declared leaf or an opaque body that carries a stated reason. There is one blessing mechanism and it has one meaning: the item leaves the gated counts (R, M and D for a leaf, O for a body) and is counted in B, where it stays visible so the allow-list cannot grow silently. The reasons are three: a rule the fragment can express but which must sit above its footprint owner for cost (section 4, tie-break 3); a rule the fragment cannot express at all, which stays a Python body (a network call); a duplication that is a pattern rather than a defect (Kapser and Godfrey, section 8). B is this metric's `pragma: no cover`.

**Composition.** A rule that references other rules by name. Composition is not duplication. Inlining another rule's predicate is.

### Scope

A scope is a kind of site that can hold a rule. Each scope has a binding set, the terms a rule stated there may read, and a composition law, the connective the scope uses to combine the rules stated in it. The prototype has four kinds:

| Scope | Binds | Law |
|---|---|---|
| schema bypasses | the actor | OR: any rule that holds grants everything |
| schema restrictions | the actor | AND: every rule must hold, or nothing is visible; evaluated above the bypasses |
| model (a concrete model, an abstract base or a multi-table parent) | the actor, the fields the class declares or inherits | AND: every rule must hold for a row to be visible |
| edge `M.r` | the actor, M's fields, the fields of a *visible* row across `r` | AND |

The edge scope binds only rows the target type shows: a root never qualifies through a related row its target type hides. That is the multi-root graph's authorization rule (a visible root cannot qualify through a hidden related row) and spec-060 Decision 12, and it makes an edge rule a test over the target's visible rows, not over the raw relation. The prototype's `evaluate` does not meet it (Appendix A, known holes).

The schema has one scope per law because the two polarities need different homes and the same binding set. The AND-only tier above every grant is the shape of AWS service control policies and permissions boundaries, Cedar's unscoped `forbid`, Cerbos's child scopes that may only restrict, and PostgreSQL's restrictive policies beside its permissive ones [V]. Of the surveyed systems with a deny, all but Ash evaluate it above the grants; Ash lets a passing bypass beat what follows it [V]. The prototype evaluates restrictions first, so a suspended staff user sees nothing whatever the bypass says.

Scopes are ordered by inclusion of binding sets: the two schema scopes (equal sets, one per law) below every base, a base below the model that inherits it, a model below each of its edges. "Tightest" throughout this paper means least in this order. It is the reverse of the order by code governed, in which the schema is the largest scope, and the two orders carry different words: size words (tight, loose) follow bindings, direction words (section 4: stated too low, move up) follow the code a scope governs. The staff bypass is owned by the schema because the schema is the tightest scope that binds `actor.is_staff`, and moving it there from a type moves it up.

A scope *covers* a footprint when every term of the footprint is in its binding set. For a rule declared for one model, the scopes that cover its footprint have a least element: the schema when the footprint has no row term; the class that declares its row terms when it reads one row; the edge of its first hop when it crosses a relation (a footprint whose relation terms leave through two different first hops is refused and must be split; `a__b__c` beside `a__d` is one edge, `a`). No Django rule makes the declaring class unique: a field an abstract base contributes along two inheritance paths is merged silently when the class is built, and the `models.E005` system check covers multi-table parents only [V]. Owner uniqueness rests on the tie-break: the prototype takes the outermost covering class in MRO order, which is a tie-break, not a definition.

The footprint fixes the floor. It does not fix the owner, because the scope's law also has to admit the rule. A leaf's **polarity** is its position in the rule's canonical tree: a *grant* when every connective on the path from the root is OR, a *restriction* when any one of them is AND. A rule that is itself one leaf has no connective, and takes its polarity from the law of the site that holds it: a lone actor rule on a type is a conjunct of that type's rule set, so it restricts, and the same leaf in the schema's bypass list grants. An actor-only grant is a bypass and the schema's OR scope owns it. An actor-only restriction ("suspended users see nothing") has the same footprint and the same floor, and the schema's AND scope owns it. A model owns only leaves that read one of its rows. So the owner is the tightest covering scope whose law admits the leaf's polarity. This is the lazy-code-motion shape of section 4: free variables (the footprint) bound the interval, a second objective (the law) picks the point.

A **rung** is not a scope. Rungs classify footprints by shape (one field, several, a relation, the actor); scopes are the homes. The owner carries both, and two rules at one scope may sit on different rungs.

### The ladder

| Rung | Footprint | Enforcement home | Note |
|---|---|---|---|
| L0 | one column, no context | DB constraint: NOT NULL, CHECK, UNIQUE, partial unique, exclusion | unbypassable by application code |
| L1 | one field's value | a `TextField` `max_length`, validators, `choices` (a `CharField` width is the column's type, section 12) | Django `choices` do not constrain the DB; a `CheckConstraint` companion is the L0 form, and the prototype derives it (`ChoicesConstraint`, section 12) |
| L2 | several fields, one row | `CheckConstraint` (L0 form) or `clean()` | the DB form exists and is preferred |
| L3 | other rows, same model | `UniqueConstraint` with condition, exclusion constraint | if the DB cannot express it, the model layer is the floor; see the ceiling note |
| L4 | a row plus related rows | relation-root rule, cascade through the FK edge | |
| L5 | a named domain object over several models | aggregate rule, composition of L0 to L4 leaves | DDD aggregate boundary |
| L6 | any of the above plus the acting user or request | policy layer; RLS is the DB-side floor for actor-row predicates | |
| L7 | sequencing side effects | workflow / service layer; composes, never restates | |

**The DB ceiling.** No mainstream DBMS enforces SQL-92 `CREATE ASSERTION` [V]. The database natively holds single-column, single-row, key, FK, partial-unique and exclusion constraints. A same-table set invariant that is not expressible as a conditional unique or exclusion constraint, and every relation invariant, has no declarative home below the model layer except triggers. "Lowest layer" therefore means "lowest layer that can enforce the rule."

**RLS and the ladder.** PostgreSQL row-level security runs integrity checks underneath it: unique, primary key and FK checks bypass RLS [V]. So RLS can move the floor of an actor-row predicate (L6) down to the database. It cannot move anything below L0 integrity. The bottom rungs are fixed; the policy rung is the one with a choice.

The ladder orders rules by the data they can see; Datalog strata order them by computation dependency, a different order that no source equates with this one [V].

## 4. Placement: push to the footprint owner, up or down

A rule moves to its owner in either direction. Three bodies of prior art say so.

**Compilers move code both ways.** Lambda lifting moves a function up to global scope by turning free variables into parameters; lambda dropping is its inverse. Loop-invariant code motion hoists up and out. Lazy code motion computes an interval [Earliest, Latest] of equally correct placements and breaks the tie with a second objective (lifetime) [V]. Free variables bound the legal range; they do not pick a point inside it.

**Query optimizers place by cost, not by depth.** System R's "evaluate predicates as early as possible" is the ancestor of pushdown, and Chaudhuri (PODS 1998) [V] says it is "no longer a sound heuristic" for expensive predicates. Predicate move-around (Levy, Mumick, Sagiv, VLDB 1994) [M] moves predicates up and across query blocks before pushing them down.

**The case study moves up.** In the GOAL.md `astronomy` app with its read side written by hand, both node types' `get_queryset` hooks begin with "if the actor is staff, return everything." That rule's footprint is {actor.is_staff}. It contains no row field. Its owner is not Galaxy or CelestialBody. It is the policy layer, schema-wide. Stating it in each model hook is the misplacement, and the duplication is the symptom. OWASP A01:2021 says the same thing informally: "implement access control mechanisms once and re-use them," in the same list as "enforce record ownership" in the model and "business limits" in the domain model [V]. GRASP Information Expert (Larman) is the design-pattern form: assign the responsibility to the class that has the information [V]. Vernon's "false invariants" in aggregate design [M] are the same defect seen from above: a rule placed at a bigger owner than its footprint needs.

So the rule is: **place at the tightest scope, in the binding order of section 3, that covers the footprint and admits the leaf's polarity.** That scope can be below the current site (a validator restating a CHECK) or above it (a staff bypass restated per model).

### The uniqueness problem

"Unique owner" is an assertion until the tie-break is named. Prime factorization is unique. Rule placement, by the compiler and optimizer evidence above, yields an interval: the scopes above the tightest cover of the footprint. Within the fragment the composition law of section 3 picks the point. For the rungs the fragment does not reach, the tie-break, stated once and used everywhere:

1. Legality: the owner must contain the whole footprint and must dominate every path the rule is meant to guard (the reference-monitor condition: always invoked, tamper-proof).
2. Within the legal interval, prefer the rung the application cannot bypass (L0 over L2, RLS over Python) when the DB can express the rule. This is the Bailis argument: for set invariants, the lower rung is not a preference, it is the only correct one.
3. Where the lower rung cannot express the rule or the predicate is expensive (a network call, an aggregate), the floor is the lowest rung that can, and the rule is blessed with that reason. If the fragment cannot express the rule at all, it stays an opaque body and the same blessing moves it from O to B, so an irreducibly high rule does not leave the codebase permanently unmeasured.

The two cases are not symmetric in what can be proven, and the asymmetry is not about direction. When the computed owner is a scope that always exists (the schema), legality is decidable from the footprint alone: a rule with no row term has nothing to do with any model, so stating it on a type is too low wherever the type is, and a row rule at schema scope is too high before any model is consulted. The prototype refuses the second at construction and reports the first. When the computed owner may not exist yet ("this row rule belongs on a mixin that owns the field"), the finding is a refusal only if the mixin is there, otherwise it is a proposal to create one. So the gate refuses where the owner scope exists and reports where it must first be created.

**The bypass.** A rule whose truth disables every other rule (the staff bypass) is not another leaf on the ladder. It is L6 with the quantifier inverted: a universal rule whose opt-out set is empty, so its only legal scope is the one above every site. The prototype places it on the schema and the trace confirms it short-circuits the type rules and the cascade alike; only a schema restriction, evaluated above it, is not short-circuited. The audit should name bypasses as a class, because a bypass stated on one type is stated too low there and silently absent from every type that forgot it: staff see less than the policy says, and nothing reports it.

Two costs of pushing up are real and must be listed: Saltzer's least common mechanism (a schema-wide point is a shared dependency and a shared failure) and the SoK finding that over-strict global defaults breed workarounds unless there is an explicit, auditable opt-out [V].

### Four placement defects

Direction words are used one way throughout: a defect is *stated too high* or *stated too low* relative to its computed owner, and its remedy *moves down* or *moves up*. "Push up" and "push down" name remedies, never defects.

1. **Stated too high:** a rule at a bigger scope than its footprint; the remedy moves it down. `max_length` checked in a serializer and a form and `clean()` when the field declares it.
2. **Stated too low:** a rule at a smaller scope than its footprint, so it is restated once per instance of that scope; the remedy moves it up. The staff bypass on each model.
3. **Branch in disguise:** a composite stated as a leaf. `allowed_to_checkout` fuses an L1 leaf on DiscountCode with an L6 leaf on the cart-actor pair.
4. **Opt-in universal:** a rule whose applicability set is "every site" but which each site must remember to invoke. The body is DRY. The placement is wrong. Django's CSRF documentation calls the opt-in decorator by itself "a security hole" [V]; the Rails 2012 mass-assignment incident and Hasura's default-deny are the same lesson. The owner of an "every site" rule is the framework default, with a declared opt-out.

Defect 4 is stated for security rules in the literature and nowhere for general business rules. The generalization is the paper's: a rule whose site set is universal has a footprint that names no particular site, so its owner is the level above all sites, and each per-site invocation is a restatement of the quantifier.

## 5. Duplication: four kinds, four remedies

The seed said "enforce that each leaf is unique." The case study and the detection survey show that "unique" has four failure modes, each needing its own detector and remedy.

| Kind | Definition | Example | Detector | Remedy |
|---|---|---|---|---|
| Identical | same predicate, same owner, authored twice | staff bypass in both hooks | canonicalize, hash or tree-isomorphism, SMT fallback (EqDAC) | delete one, compose the name |
| Isomorphic | same predicate shape, different owners | `is_private == False` on Galaxy and on CelestialBody | parameterized match (Baker), anti-unification yields the template and its holes | extract a template (a mixin owning the fields and the rule once); each inheriting model is a derived copy and counts zero. The copies one field template can absorb count toward R (the cost model below); what it leaves over, when that is more than one site, is a pattern counted in I |
| Divergent | copies that drifted | `is_staff` in one hook, `is_superuser` in the other | nothing generic; a hash sees two distinct leaves, each with multiplicity 1 | a named rule declared on two sites with different bodies; the name is the intent marker, and a name carrying more than one body is counted in D |
| Invocation | one shared function every site must call | `apply_cascade_permissions` in every hook | nothing in clone literature; Pundit's `verify_authorized` tripwire, Engler's outlier statistics, Eaddy's scattering metric | make it the default; count required invocation sites as multiplicity |

Three findings from the survey shape this table:

- **Text clone detectors cannot see any of it.** Sonar's floor is 100 tokens over 10 lines [V]. A one-line predicate duplicated six times reads as 0% duplication. Only a predicate-granularity detector over a restricted language sees leaves. EqDAC is the published one: normalize, isomorphism check, counterexample-driven refutation, SMT fallback, polynomial in the common case, 1.2 seconds per new submission, which is a ready ratchet hook.
- **Divergent duplication needs a name.** Juergens found three quarters of clone inconsistencies were intentional. A detector without an intent marker drowns. The firewall-anomaly taxonomy (Al-Shaer and Hamed: equal, subsumes, correlated, disjoint) gives the pairwise relation to compute; "correlated but not equal" is a drift candidate; the declared name decides whether it is a bug. This is why "every rule has a stable name" is load-bearing, not cosmetic.
- **Template versus delete is not automated anywhere.** Anti-unification gives the template and a hole list. No published cost model chooses. The paper's proposal grades a *field template*: an abstract base that owns the footprint fields and the rule, which is the only template section 3's owner accepts (the owner is the field's declaring class, so a base holding the rule over fields its children declare is "stated too high"). Two terms, both read off the footprint rather than the predicate, because the predicate of an isomorphic group is identical across its copies by definition and anti-unifying it yields zero holes every time. The first is whether the field template exists: anti-unify the *declarations* of the footprint fields (Django's `deconstruct()` output, less `verbose_name`, `help_text` and `db_comment`, which name the column rather than shape it). A field on an abstract base takes no parameters, and a child that re-declares it owns it again, with the rule's footprint moving back with it; so a hole in a declaration means that member is outside the template. `related_name` is a hole, not a cosmetic: it is a public reverse accessor, and `%(class)s` interpolation absorbs it only when the names already follow one pattern. The second is what the template costs: where it would live. Copies in one app share a models module; copies spread over apps need a module every one of them imports. The grade is taken on sub-groups, not on the group: every set of copies with identical declarations in one app is a bucket the template absorbs, and the largest bucket is what R counts, so one more copy anywhere can never lower R. Whatever the buckets leave over, when it is more than one site, is a pattern counted once in I (section 8) with the hole or the span that excluded it, and left to blessing. The app term is the paper's own criterion, not the literature's: Kapser and Godfrey's "templating" pattern, boilerplate the language cannot abstract, is the hole term [A]; their argument for leaving a clone alone is independent evolution, which no static count sees. The honest home term is the import edge the base would add: an abstract base needs no `INSTALLED_APPS` entry and no migration dependency, so a cross-app base costs one import edge, which the remedy should name ("an import edge from kanban to glossary") and which grimp and import-linter already price [V]; no shipped tool prices a home, and the nearest rule in the literature puts it at the copies' common ancestor when the group is exactly that ancestor's subclasses and at a new intermediate base otherwise [A]. The prototype counts apps because that is what `_meta` knows. Section 12 measures the model once; what stays open about the home is in problem 5.

## 6. Worked example 1: the six seed rules

| # | Rule | Footprint | Owner | Verdict |
|---|---|---|---|---|
| 1 | title required | {title} | L0 NOT NULL | leaf |
| 2 | max 200 chars | {title} | L0 CHECK / `max_length` | leaf; serializer or form restatement is a derived copy if generated, an authored copy if written |
| 3 | unique per shelf | {title, shelf} | L0 `UniqueConstraint(shelf, title)` | leaf |
| 4 | end after start | {start, end}, one row | L0 `CheckConstraint(end > start)` | leaf; the DB rung is lower than the model and unbypassable |
| 5 | email has no pending invite | {email, other rows where is_invited} | L0 partial unique `UNIQUE(email) WHERE is_invited` | leaf; it reads other rows, and the DB can express it |
| 6 | allowed to checkout | A: {discount.expiry}; B: {discount.region, user.region} | A: L1 on DiscountCode; B: L6 at the checkout boundary | branch in disguise; A was mis-attributed to the cart |

Rule 6 is where the seed trailed off. The footprint analysis is the leaf detector: the composite splits into one misplaced leaf and one irreducible leaf, and `allowed_to_checkout` survives as a named composition of the two.

## 7. Worked example 2: `get_queryset` in the North Star

GOAL.md is the acceptance test for the whole package. Written by hand, its two node types each carry this hook, the same body twice (the census of what GOAL.md itself inlines is below the factoring):

```python
user = getattr(getattr(info.context, "request", None), "user", None)
if user and user.is_staff:
    return queryset
return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)
```

Factored:

```
A  OR  (B  AND  C)
A = actor.is_staff                       footprint {actor}             L6, schema-wide
B = row.is_private == False              footprint {row.is_private}    L1 on the owning model
C = each single-column forward FK or     footprint {row.<fk>,          L4, the FK edge
    O2O whose target has a registered     target visible set}
    type is null (nullable edges only)
    or targets a visible row
```

Three leaves, three footprints, one `OR`/`AND`. A branch in disguise with three of the four duplication kinds present and the fourth one edit away:

- **A is identical duplication and stated too low.** Footprint {actor}, no row field. Owner: policy layer. Multiplicity 2.
- **B is isomorphic duplication.** Same shape, two models. A hash says "different owner, not equal," multiplicity 1 each. Wrong in spirit. In Codd's terms [M] it is a repeated attribute across tables. Remedy: a `Privatable` mixin owning the column and the rule once, instantiated twice.
- **C is invocation duplication.** One function, DRY body, called at N sites, forgetting is silent. Owner: the framework, as an opt-out default. Multiplicity N with zero copied text.
- **Divergent drift is one edit away.** Change one `is_staff` to `is_superuser` and the hash-based detector reports a clean codebase. Only `StaffBypass` as a named rule on two types catches it.

**The two hooks are the sample, not the count.** GOAL.md declares the row visibility (`StaffBypass` on the schema, `Public` on a `Privatable` mixin) and beside those declarations inlines `user.is_staff` six times and `is_private=False` twice. The six are one leaf, `actor.is_staff eq True`, inlined into three different composites: "only staff may filter, order or aggregate by `Galaxy.name`" in three `check_*_permission` methods on a FilterSet, an OrderSet and an AggregateSet; "staff sees this field" in two redaction resolvers; and the top tier of a date-precision rule. Composition is not duplication, inlining is (section 3), and every one of the six inlines the leaf `StaffBypass` names. The two `is_private=False` sites are a `RelatedFilter` queryset that is a scope boundary by its own comment, and a child-queryset helper that filters any target model carrying the column; both inline the leaf `Public` names. R over the file is therefore 7 for the staff leaf and 3 for the private leaf, the declaration included; the factoring above is the worked example, the census is the audit's job. Each site is one line, which is why a text clone detector (section 5) sees none of it.

Runtime duplication too: for a non-staff actor the body cascade re-enters Galaxy's hook, which re-evaluates A. Harmless here because A is actor-only and idempotent. A row-dependent A would make nested evaluation order observable, which is the confluence question in section 10 made concrete.

**Reduced form.** The package already has the shape on the write side: `permission_classes = [DjangoModelPermission]`, a named, composable class. The read side has no equivalent, so it falls into a hand-written method. The asymmetry is the gap. Reduced:

```python
# schema-level, once
DjangoSchema(..., visibility=[StaffBypass])

# models.py
class Galaxy(Privatable, models.Model): ...
class CelestialBody(Privatable, models.Model): ...

# schema.py: no get_queryset body on either node
# cascade through forward FKs: framework default, opt out with Meta.cascade = False
```

Both hook bodies disappear. `get_queryset` remains as the escape hatch for rules the fragment cannot express; each such body is counted in O until it is blessed with a reason, and a non-empty body on a type that could be declarative is itself the warning.

Before and after:

| | before (by hand, over the factoring) | after |
|---|---|---|
| R, max authored multiplicity | 2 (A on each model; B on each model) | 1 |
| M, leaves stated away from their owner | 2 (A, too low on each model) | 0 |
| invocation sites for a universal rule | 2 (C) | 0 |
| O, hand-written visibility bodies | 2 | 0 |

The ecosystem evidence says this is the documented idiom, not a local mistake: graphene-django and strawberry-graphql-django both recommend a per-type `get_queryset`, graphene-django recorded a connection field that forgot to apply it (a visibility leak), and Hasura shipped an advisory where a second code path (computed fields) forgot the row filter [A]. The second site that forgets is the failure this paper predicts.

## 8. The metric

One number, tuned from infinity down to 1, has an elegant reading: treat the rule base as an integer, its prime factorization is the multiset of leaves, and R is the largest exponent. The base is reduced when it is square-free, R = 1.

The honest version is a small vector. One scalar for code quality is the weakest link in any such proposal, and the survey found that every clone metric is parameter-sensitive (clone coverage on one system ranged 19% to 92% by detector settings).

| Component | Definition | Target |
|---|---|---|
| R | max over leaves of authored multiplicity: the authored sites carrying that canonical form, whatever their owners, plus required invocation sites of a universal rule; derived copies count 0 | 1 |
| M | count of leaves whose owner holds no copy of them: the authored site is elsewhere and nothing at the owner was derived from it | 0 |
| D | count of rule names that carry more than one canonical body | 0 |
| I | count of isomorphic groups whose copies outside every field template are more than one site: a hole in a footprint field's declaration, or copies spread over more than one app (section 5) | pinned two-sided like the rest, with no target |
| B | count of blessed items: declared leaves and opaque bodies carrying a stated reason | reported, not gated |
| O | count of opaque rules (hand-written bodies the fragment cannot read and nobody has blessed), with the invocation sites of universal rules found inside them | 0; a codebase with R = 1 and O > 0 is not reduced, it is unmeasured |
| ratio | authored leaf instances / distinct leaves (Juergens' redundancy-free size, at predicate granularity) | trend only |

R, M, D and B are defined over declared rules only. O is what makes that honest: it is the size of the part of the rule base the other four cannot see. The opaque snapshot of section 12 scores R = 1, M = 0 and O = 2 on a codebase that is plainly not reduced, which is why O is in the vector and not a footnote. A branch in disguise is not a separate count: splitting it yields at least one leaf whose site is not its owner, and M counts that leaf. Identical copies, and isomorphic copies a template can absorb, both count toward R, because a leaf's identity is its canonical form (section 3) and the remedy exists for both. What the field template of section 5 leaves over is counted in I instead: for a hole, because the remedy the gate would demand does not exist as a field template; for a span, because the remedy is a dependency between apps, which is a design choice the gate should name and not make. A count that reads nine for nine unrelated tables that each want a unique `name` would be ignored, which is worse than a count that reads seven in one app, two left over. I has no target but it is pinned two-sided like the others (`RULE_PATTERN_PIN`, below), because an unpinned I is a hole in the ratchet: one `db_index=True` on one copy, or one model moved to another app, would move a group out of R and into nothing, which rewards the drift D exists to catch. Blessing moves a group from I to B. The verdict is R = 1, M = 0, D = 0, O = 0.

Mechanics drawn from the survey:

- **Two-sided pin,** not a one-sided floor. qntm's ratchet fails when the count is above the pin and when it is below, which forces the team to lower the number; Betterer's `ci` mode, mypy-baseline, ESLint's bulk suppressions, rubocop-gradual's `--check` and import-linter's unmatched-ignore alerting all fail on an improvement the committed file does not yet record [V].
- **Integer multiplicity, exact.** PIT's lesson: integer-percent thresholds hide sub-percent regressions. R and M are exact integers, so no precision knob.
- **Baseline file for adoption.** `database_consistency`'s TODO file and Betterer's committed results file are the precedent: record today's findings, fail on any new one. Only Betterer rewrites the file on improvement, and only outside CI; basedpyright's baseline writes under the same rule (when nothing is worse), and `database_consistency` documents generate-then-check with no stale-entry check [V]. Every one of them puts the category in the key, so a finding that changes category counts as fixed in one and new in the other and nothing nets. A count pin cannot tell a fix from a move: the baseline the pins summarise has to list members (rung, category, canonical form, site), not groups, with a versioned form hash so a change to the canonicaliser is a declared flag day rather than a silent re-key (SARIF's fingerprints are the precedent) [V]. Keyed by group, I reads one whatever the group's size, so a tenth copy and a deviant copy (`db_index=True` on one of seven) are invisible until the baseline lists members.
- **New-code gate.** Sonar gates duplication on new code only. The same split lets a legacy codebase adopt the ratchet without a flag day.
- **Blessing.** Kapser and Godfrey's "cloning considered harmful considered harmful" [A]: some duplication is a pattern, not a defect. The blessing of section 3 is that allow-list: a reason beside the item, the item moved to B, B reported so it cannot silently grow. A blessing is a decision and a baseline entry is debt: RuboCop separates `rubocop:disable`, which `AllowWithReason` can require a reason for, from `rubocop:todo`; Rust's `#[expect(lint, reason = ...)]` errors when the lint no longer fires, and import-linter errors on an unmatched ignore by default, so a stale blessing is an error, not a leftover [V]. Django's `Meta` rejects an unknown attribute, so a reason has to travel as a class attribute read through the MRO, the way `visibility` already does.

Setting shape, mirroring coverage:

```python
DJANGO_STRAWBERRY_FRAMEWORK = {
    # two-sided pins: the gate fails above the pin and below it
    "RULE_MULTIPLICITY_PIN": 1,
    "RULE_MISPLACEMENT_PIN": 0,
    "RULE_DIVERGENCE_PIN": 0,
    "RULE_PATTERN_PIN": 0,
    "RULE_OPAQUE_PIN": 0,
    # one sorted line per member, not per group: a count cannot tell a fix from a move
    "RULE_BASELINE": "rules-baseline.tsv",
}
```

## 9. The rule language and the detector

**The wall.** If rules are arbitrary Python, "are these two rules the same leaf" and "what does this rule read" are undecidable (Rice). You cannot reduce arbitrary code. The entire project rests on a restricted declarative rule language in which footprint analysis, equivalence, and decomposition are decidable. This is the same reason FilterSet, OrderSet, AggregateSet, FieldSet and the optimizer can reason at all: they are data, not callables.

Cedar is the shipped proof that the trade works [V]: a deliberately restricted authorization language with a sound and complete SMT encoding, equivalence and subsumption checks, shadowed-permit and impossible-condition detection, counterexamples, about 75 ms per query, formalized in Lean. Its related-work table records that Rego equivalence is undecidable (Datalog) and that Zanzibar has no deep analysis. Cedar also uses the word "footprint" (of entity constants) in its decidability argument.

**Decidable is not cheap.** Conjunctive-query equivalence is NP-complete (Chandra and Merlin); with inequalities it is Pi2p-complete [V].

**The fragment.** Comparisons over fields and relation paths, boolean structure, constants, enum membership, bounded relation traversal, actor attributes. No user-defined functions in leaves. Named composition of leaves. This is roughly what a Django `Q` already is, which is why `Q` on `Meta.constraints` yielding both DDL and `validate()` is the existing L0 instance of the thesis, shipped in Django 4.1 [V].

**The pipeline,** in order of cost, after EqDAC:

1. Canonicalize the AST: flatten and sort commutative operands, De Morgan to a fixed polarity, double-negation, constant fold, canonical owner path, `lte`/`gte` flips.
2. Hash or tree-isomorphism. Equal means identical duplication.
3. Parameterized match / anti-unification across owners. A match with holes means isomorphic duplication; the anti-unifier is the proposed template.
4. Counterexample-driven refutation for pairs that share a footprint but differ: generate values that satisfy one and not the other. If none is found cheaply, the pair is a correlated candidate.
5. SMT (Z3) fallback for the residue: arithmetic entailment (`a < b and b < c` entails `a < c`), subsumption, correlation versus disjointness.
6. Footprint extraction and owner computation per canonical leaf. An e-graph (egg / egglog, Python bindings exist) is an alternative normalizer whose e-class analysis computes the footprint per class and removes the need for a confluent rewrite system: saturation explores all orderings, extraction picks the minimum.

**Test oracle.** Compile each predicate to `SELECT pk FROM t WHERE ...` and cross-check the canonicalizer against a SQL equivalence prover (VeriEQL and QED reason modulo integrity constraints, which is exactly the case where a Python predicate duplicates a DB constraint). An oracle, not a hot-path dependency.

**What the optimizer already has.** The selection walker computes which relations a GraphQL selection must load, which is a footprint. The spec-004 plan key is the printed AST of the operation with its reachable fragments appended: a stable string of one operation, not a canonical form. It sorts no operands and normalizes no field order, so two selections that differ only in order get two keys. Step 2's keyed lookup exists for selections; step 1's canonicalization does not.

## 10. Open problems

1. **Confluence.** The metric is well-defined only if "reduced" does not depend on rewrite order. Nobody has applied Knuth-Bendix completion to a rule rewriting system [V, absence]. The e-graph route sidesteps it; the term-rewriting route must prove it for the fragment. Either is paper-worthy. Underneath it the fragment has no declared NULL semantics, and the three places that define one disagree: Django adds an `IS NOT NULL` guard to a negated lookup on a nullable column, `evaluate()` folds actor terms in two-valued Python, and a `CHECK` passes UNKNOWN where a filter drops it (Django's `validate()` wraps the condition in `Coalesce(condition, True)`; PostgreSQL's `canonicalize_qual` takes the same `is_check` flag) [V]. Reading every `Q` through Django's own `Query.build_where` gives one tree with the guards materialised, after which flipping a comparison under `Not` is sound on row terms and `ne` and `Not(eq)` stop being two leaves; that is the null-aware normal form the fragment should define, with an SMT tier (about a millisecond per pair in a Kleene encoding; z3 installs on the 3.10 floor) confirming pairs that share a footprint but differ in hash, in EqDAC's order [V]. Only three things in the survey yield a canonical representative, each for a sub-fragment: a reduced ordered decision diagram over field-versus-constant atoms, a BDD over the Boolean skeleton, Calcite's per-expression `Sarg`; everything else is a heuristic normaliser that can be hashed or a pairwise decision [V].
2. **A second ordering.** Bailis's invariant confluence (VLDB 2015) orders invariants by coordination cost, which under replication can disagree with "lowest rung is best." The ladder is a single-database story until this is reconciled.
3. **Expensive predicates.** A leaf whose evaluation needs a network call or an aggregate may belong above its footprint owner for cost reasons. The tie-break in section 4 handles it by blessing; a cost model would handle it properly.
4. **The reverse defect has no literature.** Nobody has measured how often a global rule is restated per model. The case study and the out-of-sample runs of section 12 (four small corpora, then eight application codebases with 571 models) are author-classified. Yang's corpus was twelve Rails applications; no Django counterpart is published [V, absence]. An empirical study over Django and Rails corpora, using Juergens's intentional / unintentional / faulty classification with developer confirmation, is the evaluation this paper needs.
5. **Template versus delete.** Section 5 grades a field template on two terms and section 12 measures it once. Three things stay open. The model grades field templates only: Django also lets a child override a base's field, and lets a base hold the constraint over a field each child declares, so templates with holes exist in the language; section 3's owner rejects them, and whether it should is problem 3's cost question again. The home term counts apps where the cost is an import edge (section 5), and only the developer-confirmed study of problem 4 can say whether a cross-app base is ever the right remedy. The hole alphabet is a choice: which attributes a base can carry is a Django fact, which differences matter is not, and `Unique`'s identity (section 12) draws the same line from the other side; what it lacks is the equality carrier (collation, a case-insensitive field: Yang found nineteen case-sensitivity conflicts on uniqueness) and a ruling on whether `nulls_distinct` can be dropped when every key column is `NOT NULL`.
6. **Derived polarity is unvalidated.** Section 3 reads a leaf's polarity off its position in the tree and, for a lone leaf, off the law of its site. Every surveyed system with two polarities declares the polarity on the leaf instead (ZenStack's `@@allow`/`@@deny`, Cedar's `permit`/`forbid`, PostgreSQL's `PERMISSIVE`/`RESTRICTIVE`, section 13) [V], so any of those corpora is an oracle for the derived reading, and none has been run against it. One case is decided by position rather than by an oracle: a disjunct at the root of a type rule is read as a grant although the type ANDs its rules, so moving it to the bypass list widens it past that type's other conjuncts; the gate reports the move rather than performing it (section 3), and whether that is the reading authors intend is what the oracle would say.
7. **Runtime multiplicity.** Measured, not hypothesized (section 12): a rule authored once was evaluated three times per query, at the root list, inside a cascade edge, and for a nested selection. For an idempotent row-local rule this is a cost, not a correctness problem. For a rule that reads context that differs between those three sites (a per-request counter, a time-of-check), the three evaluations can disagree, and which one wins depends on evaluation order. That is problem 1 at run time. Fragment rules are not context-stable across the three sites: a login or logout mutation changes `request.user` inside one operation, which is why spec-058 Decision 3 re-reads the viewer at each lookup, and a mutation changes row fields part-way through an operation. The paper needs an explain payload that records the cause of each evaluation so disagreement is visible.
8. **Observability as part of the metric.** The static audit and the per-operation trace answer different questions: "where is each rule authored" and "where did each rule run for this actor." Coverage has the same split (a report, and the trace that produced it) and nobody treats the report as the whole feature. The prototype suggests the metric is only trusted when the trace is available to check it against, and that a paper proposing a CI gate should propose its debugging surface in the same breath.

## 11. Roadmap inside the package

Post-1.0 differentiation, not a parity item. Each step is independently useful.

1. **Visibility sidecar.** A declarative, named, composable read-side rule symmetric with `permission_classes`. An eighth file in the North Star layout (`rules.py`) or a `Meta.visibility` entry, with the schema's two actor-only lists (`visibility`, `restrictions`) above it. `get_queryset` stays as the escape hatch and becomes a reported deviation at a tight level.
2. **Cascade default-on.** `apply_cascade_permissions` becomes the framework default for every registered forward FK edge, with `Meta.cascade = False` as the declared opt-out. Removes the invocation-duplication class for the one universal rule the package already owns.
3. **L0 duplicate detector.** Canonicalize and hash over field declarations, `Meta.constraints`, validators, `clean()` where it is declarative, serializer and form fields. Flag an authored restatement of a constraint. Yang's constraint-type catalog (length, numericality, null, uniqueness, inclusion, case) is the test suite; `database_consistency`'s 24 checkers are the feature checklist; no Django equivalent exists [V, absence]. The serializer half is a baseline diff, not a reader: DRF's `ModelSerializer` derives its validators from the model (`build_field`, `fields_for_model`), never calls `full_clean()`, derives no `CheckConstraint`, drops the derived `UniqueValidator` when a field is declared by hand and strips `MaxLengthValidator` from a declared `CharField` [V]. An authored serializer field is a restatement exactly where it differs from what `build_field` would have produced, so the reader is "build the field, diff the declaration", and `Authored` needs a tier marker to say which tier a site is on. `ModelForm` delegates to the model and needs no reading.
4. **Footprint and owner.** Scope analysis over the visibility sidecar and FieldSet. Misplacement gate. Suggest the lower or higher rewrite.
5. **The ratchet.** The two-sided pins of section 8 (`RULE_MULTIPLICITY_PIN`, `RULE_MISPLACEMENT_PIN`, `RULE_DIVERGENCE_PIN`, `RULE_PATTERN_PIN`, `RULE_OPAQUE_PIN`) over a member-keyed baseline file: local runs rewrite it only when nothing is worse, CI requires equality with it, regeneration is a local flag CI refuses.
6. **RLS twin.** Compile a visibility rule to a django-rls policy and prove the Python predicate and the policy equivalent. django-rls documents no such check [A]. Nobody has done this.
7. **Inspector.** Two surfaces mirroring the package's existing `inspect_django_type` command and `DjangoDebugExtension`: a static `inspect_rules` command that prints the audit and gates under `--strict`, and a per-operation `extensions["visibility"]` trace of which rule fired at which site for this actor, with the cause of each evaluation (root, cascade edge, nested selection). The second is what the planned optimizer explain mode needs anyway, since every `select_related` downgrade is a rule firing.

Steps 1, 3, 4 and 7 exist as a prototype on two rungs (section 12). Step 2 exists only for types that declare a rule: a type with neither a rule nor a hook keeps its identity hook and no cascade, so at the type level the cascade is still an opt-in universal. Step 3 reads `Meta.constraints`, `unique`, `max_length`, `choices` and validators, not serializer or form fields. Step 5 has its gate flag (`inspect_rules --strict`) but no baseline file and no pins. Step 6 is untouched.

## 12. Prototype: two rungs, running

Built 2026-10-06 in a worktree (`.claude/worktrees/reduction-demo`, uncommitted) as the smallest thing that shows the owner computation picking the site and an audit reading the difference. First rung: read-side row visibility, the `get_queryset` case of section 7. A second rung, declarative constraints (roadmap step 3), was added on 2026-10-07 to test whether the same fragment and audit work where the rule is not a visibility rule; it has its own subsection below. Everything here is output of the prototype, not design. `examples/reduction_demo/demo.py` reproduces it. Where each piece stands relative to the package's own roadmap, and what it depends on that has not shipped, is Appendix A.

### What was built

**The fragment** (`rules/fragment.py`). Terms `Field("is_private")` and `Actor("is_staff")`, comparisons (`eq ne lt lte gt gte in_ is_true is_false`; `not_in` is in the operator enum and nothing authors it), `&`, `|`, `~`, and `Rule(name, predicate, blessed=None)`. `canonical()` flattens and sorts junctions, drops duplicates and pushes `Not` to the leaves, where it stays: `NOT (rank < 3)` keeps NULL rows and `rank >= 3` drops them, so folding the negation into the operator would make the enforced rule differ from the authored one. `footprint()` is the term set. `owner()` is the ladder restricted to what the fragment can express: no row term means one of the schema's two scopes (L6), the bypasses for a grant and the restrictions for a restriction; row fields mean the class that declares them, found by walking the model MRO for the outermost class, abstract base or multi-table parent, whose `local_fields` cover the footprint (L1 for one field, L2 for several); a `__` path, the edge of its first hop (L4); actor plus row, L6 on the model. `leaves()` splits a canonical junction whose operands compute to different owners (the branch in disguise) and otherwise returns the junction as one leaf. The connective is carried into the split: every operand beneath an AND is a restriction, so an actor-only conjunct is owned by the schema's restrictions, never offered to the bypasses (section 3, polarity). A rule naming a field its model lacks is refused at class definition. `evaluate(pred, actor)` partially evaluates: actor terms fold to constants now, row terms stay symbolic as a `Q`, so the authored rule and the enforced rule are one object.

**Enforcement** (`rules/apply.py`). `DjangoType.get_queryset`'s default body is framework-owned. A type with no declared rule keeps the identity it always had. Before anything else, every type, rules or not, is subject to the schema's restrictions (`DjangoSchema(restrictions=[...])`, actor-only by construction, ANDed: one that fails returns an empty queryset). With rules: schema bypasses next (`DjangoSchema(visibility=[...])`, actor-only by construction), then every rule declared on the type (`Meta.visibility`) or on any model class in its model's MRO (a `visibility = (...)` tuple on a mixin, abstract or concrete; a model *field* of that name is skipped), ANDed, then the forward-FK cascade, on by default for every type that declares a rule, with `Meta.cascade = False` as the opt-out. A type that declares nothing gets no cascade either, which is where roadmap step 2 is still incomplete. Declaring a rule flips `has_custom_get_queryset()` so the optimizer's `select_related` downgrade still fires.

**The placement gate at construction.** `DjangoSchema(visibility=[Public])` and `DjangoSchema(restrictions=[Public])` are refused with "reads row fields `['is_private']`; its footprint is not contained by the schema scope". The schema is the one scope where legality is provable at construction, so that is where the gate lives. A row rule declared on the wrong model is reported, not refused: the field exists on the model or the rule would have been refused at definition, so the finding is a proposal to move the rule to the class that declares the field, and that class may not exist yet (section 4).

**The audit** (`rules/audit.py`). Collects sites: schema bypasses, schema restrictions, type rules, mixin rules (recorded once per declaring class; the second concrete model inheriting it is a derived copy and counts zero). Splits each into leaves, a lone leaf taking its polarity from the site's law. Then: misplaced (M) if the authored site's scope key differs from the owner's; identical duplication if one canonical form appears at two sites with the same owner, isomorphic if at two sites with different owners (sites are types, so two types over one model are two authored sites), the identical kind raises R to the number of sites, the isomorphic kind to the largest set of sites one field template absorbs (section 5), the rest, if more than one, counted in I; divergent (D) if one rule name carries two canonical bodies; opaque (O) if a type overrides `get_queryset`, with or without declared rules beside it (the rules are audited, whatever the body does to them is not), in which case the body is counted and text-scanned for `apply_cascade_permissions(` to count invocation sites. A branch in disguise is a finding, not a count. A blessed rule's leaves are counted in B and excluded from R, M and D; an opaque body with `Meta.blessed = "<reason>"` is counted in B instead of O.

**Two inspector surfaces**, modelled on the package's existing ones (`manage.py inspect_django_type`, the per-field resolution table; `DjangoDebugExtension`, the per-operation `extensions["debug"]` payload with SQL and exception rows, fail-closed under `DEBUG=False`, capped). The static half is `manage.py inspect_rules --schema <selector> [--app <label>] [--strict]`: it prints the audit and exits non-zero under `--strict` when the verdict is NOT REDUCED, so it is the CI gate of section 8 minus the baseline file. The per-operation half is `DjangoVisibilityExplainExtension`: the enforcement body records one event per queryset it scopes (a type scoped three times in one operation records three events), and the operation returns them under `extensions["visibility"]`.

### What it showed

Three snapshot apps of the North Star carry one policy and return identical rows for an anonymous and a staff actor (asserted). The audit answers differently for each:

| snapshot | statement | R | M | opaque | cascade sites | verdict |
|---|---|---|---|---|---|---|
| opaque | the two hand-written hook bodies of section 7 | 1 (declared only) | 0 (declared only) | 2 | 2 | NOT REDUCED |
| declared | `visible := staff OR public` as `Meta.visibility` on both types | 2 | 2 | 0 | 0 | NOT REDUCED |
| reduced | `StaffBypass` on the schema, `Public` on the `Privatable` mixin, no node code | 1 | 0 | 0 | 0 | REDUCED |

The declared snapshot's findings are the section 7 factoring, produced by the machine rather than by hand: branch in disguise on both types; the actor leaf misplaced (stated too low, owner schema) twice and identical across both sites, "author once at schema"; the row leaf isomorphic across `Galaxy` and `CelestialBody`, also multiplicity 2, "one abstract mixin in astronomy_declared owning `['is_private']` and this rule, inherited by each model". M is 2, one per misplaced actor leaf; the two branch splits are findings, not counts. The reduced snapshot's two leaves each sit at their owner: `staff_bypass` at schema, `public` at `Privatable`.

The explain payload for the reduced schema, one query `{ galaxies { name } bodies { name galaxy { name } } }`:

```
anonymous:
  GalaxyNode         rules=[public @ Privatable -> is_private=False]  cascade=framework default
  GalaxyNode         (same)
  CelestialBodyNode  rules=[public @ Privatable -> is_private=False]  cascade=framework default
  GalaxyNode         (same)
staff:
  GalaxyNode         bypass=staff_bypass @ schema
  CelestialBodyNode  bypass=staff_bypass @ schema
  GalaxyNode         bypass=staff_bypass @ schema
```

Two observations fall out of that trace that the prose did not predict:

1. **Runtime multiplicity is visible and larger than authored multiplicity.** `GalaxyNode`'s rule is authored once and evaluated three times per anonymous query: at the root list, inside the cascade from `CelestialBody` across the `galaxy` edge, and again for the nested `galaxy { name }` selection. This is the measurement behind section 7's runtime duplication paragraph. It is harmless here because `public` is idempotent and row-local. The explain payload is the instrument that would catch a non-idempotent or context-dependent rule being re-evaluated with different inputs, which is the confluence question of section 10 made observable. A real version of the payload should record *why* each evaluation happened (root, cascade edge, nested selection), which the prototype does not.
2. **The bypass short-circuits everything below it, including the cascade.** For staff no row rule and no edge is evaluated. That is the correct reading of "staff see everything" but it means a schema bypass is strictly more powerful than any type rule, and the audit should say so: a bypass is a universal rule with an opt-out of zero. The ladder has no rung for "a rule that disables other rules"; it is L6 with the quantifier inverted. The one thing above it is the schema's restriction scope, which the next subsection exercises.

### The inverse of the lead example

The lead example is a universal grant restated per model. Its inverse is a universal restriction restated per model: "suspended users see nothing", `active_only := actor.is_active eq True`. Two snapshot apps (`suspension_restated`, `suspension_reduced`) share two models under a `Privatable` mixin, a staff bypass on the schema, and that one rule, stated on each type in the first and in `DjangoSchema(restrictions=[ActiveOnly])` in the second. Four actors, one query:

| actor | restated | reduced |
|---|---|---|
| anonymous | nothing | nothing |
| member | public rows | public rows |
| staff | everything | everything |
| suspended staff | everything | nothing |

The last row is the finding. In the restated snapshot the bypass runs before the per-type rules, so a passing bypass beats the restriction, which is the Ash order of section 3; the restated form cannot be written correctly, because the type scope has no position above the bypass. In the reduced snapshot the restriction is evaluated first. The audit of the restated snapshot reads `active_only` twice, each copy stated too low with the remedy "move up to schema restrictions", and the pair as identical duplication, "author once at schema restrictions": R 2, M 2. The reduced snapshot is R 1, M 0, REDUCED, with the three leaves at three owners: the bypass at the schema's OR scope, the restriction at its AND scope, `public` at `Privatable`. A rule-less type is subject to the restriction too, so the universal rule has no opt-in sites.

### The second rung: constraints

**What was built** (`rules/constraints.py`, `inspect_rules --rung constraints`). A reader from Django's declarative vocabulary into the fragment: a `CheckConstraint` whose condition is a `Q` of field lookups (`exact gt gte lt lte in isnull regex`, a `__length` transform, an `F` on the right-hand side) becomes a predicate; a `UniqueConstraint` over fields, `unique=True` and `unique_together` become a new leaf kind, `Unique(fields, condition)`, the one leaf that is not row-local, with the identity the engine gives it (SQL-92 files length, precision and scale in the data type and `NOT NULL`, `UNIQUE` and `CHECK` under constraints, deferrability outside the constraint; PostgreSQL 18 holds `NOT NULL` in `pg_constraint`; the duplicate-index test compares key columns, operator class, expressions and predicate, not width, nullability or name [V]), so `Unique` drops deferral, reads `nulls_distinct=True` as the default, and treats the column's nullability as a hole in the footprint's declaration rather than part of the leaf; `max_length`, `choices`, `MinValueValidator`, `MaxValueValidator`, `MinLengthValidator`, `MaxLengthValidator` and `RegexValidator` become predicates on the field. The fragment needed four additions and no change: a `Length` term, `F` values, the `Unique` leaf, and a sorted canonical form for membership sets. `canonical()`, `footprint()` and the declaring-class search are the visibility rung's, unchanged. Each declaration is authored at L0 (anything the DB holds) or L1 (`choices`, a `TextField` `max_length`, a validator); its owner is L0 whenever the DB can express the leaf, which is everything but a regex. A `CharField` `max_length` is not read: it is the column's type, `varchar(n)`, a declaration rather than a rule. A `clean()` body that can raise, a constraint over an expression and a validator the fragment does not know (a plain function) are opaque; a `clean()` that only normalises is read as no rule at all, from its syntax tree (no `raise`, no `ValidationError`, no call to a helper by bare name). `ChoicesConstraint("status", name=...)` is a `CheckConstraint` subclass whose condition is read off the field's `choices` when the model class is prepared and frozen into the constraint's `deconstruct()`, so the membership rule is authored once, the DB copy is derived, and a change to the choices is a change to the constraint that the migration autodetector emits; the audit counts it zero and treats the owner as held. Two residuals: a callable `choices` is frozen as whatever it returned at preparation, and a nullable field gets no NULL branch, which is harmless only because SQL `CHECK` passes NULL. M on this rung is "the owner holds no copy, authored or derived", which section 8 now says for both rungs. D is structurally zero: the database refuses two constraints with one name.

**What it showed on the demo.** One model, four rules, two snapshots. The restated snapshot writes each rule twice (`unique=True` beside a `UniqueConstraint`, `choices` beside a `CheckConstraint(status__in=...)`, `MinValueValidator(0)` beside `CheckConstraint(price__gte=0)`) and the date order once, in `clean()`. The reduced snapshot writes `unique=True`, `choices` plus `ChoicesConstraint`, and one `CheckConstraint` each for the price floor and the date order; no validator, no `clean()`. The script submits four bad rows to both. `full_clean()` refuses all four on both (the reduced one through `validate_constraints`, the derived copy). An `INSERT` that skips `full_clean()` is refused three times on both and accepted once: the restated date rule lives only in `clean()`, and the database has never heard of it. That row is the Bailis argument of section 1 at the smallest possible scale, and the audit predicts it: the restated snapshot scores R = 2 on three leaves (remedy "keep the constraint; the others restate it"), O = 1 for `clean()`; the reduced snapshot scores R = 1, M = 0, O = 0, and `inspect_rules --rung constraints --strict` passes.

**What it showed on a real corpus.** The five fakeshop apps, 71 authored leaves after the field type's own copies and `CharField` widths are excluded:

| | count | what |
|---|---|---|
| R | 7 | `unique=True` on `name` across seven library tables with one declaration (`TextField(unique=True)`): the largest set one field template absorbs |
| M | 2 | `choices` with no `CHECK` beneath it (`Shelf.condition`, `Book.circulation_status`) |
| D | 0 | structural |
| I | 4 | the two `name` copies outside library (kanban, products) and `unique(title)` x2 (glossary, kanban) span apps; `unique(category, name)` x2 differs in `related_name`; `unique(number)` x2 is a `TextField` beside a `PositiveIntegerField` |
| O | 1 | the one-hot link constraint, an expression the fragment does not read |
| identical | 3 | `choices` restated as a `CheckConstraint` over the same keys on three kanban models |
| isomorphic | 8 | five buckets count in R (`name` x7 and `code` x4 in library, `label` x3 in scalars, `key` x2 in kanban, `label <> ''` x2 in glossary); four groups leave a pattern in I; the nullable `label` and glossary's own `LookupBase.key` are single leftovers, which is a leaf at its owner, not a pattern |

Four things the corpus taught that the demo could not:

1. **"Authored" is read off `deconstruct()`.** A `OneToOneField` sets `unique=True` itself, a `UUIDField` sets `max_length=32`, a `FileField` defaults to 100: read off the field objects, the corpus carries thirty-seven leaves nobody wrote. Django's `deconstruct()` returns only what the author wrote, which is the authored/derived line of section 3 drawn by the platform.
2. **The three identical findings are real and the remedy exists.** `choices` plus a hand-written `CHECK` over the same keys is the Yang "inclusion" constraint duplicated across two tiers; the kanban app does it three times, and every one is one `ChoicesConstraint` away from R = 1. The remedy says "derive", not "delete": deleting the `choices` would delete the GraphQL enum they drive. Detection and remedy are separate claims.
3. **Eight of eleven duplication findings are isomorphic `unique(<field>)` across unrelated models, and grading them took the cost model of section 5.** By section 5's definition they are duplication (same canonical form, different owners); by Juergens's finding most such clones are intentional, and R = 9 for `unique(name)` across nine unrelated tables is a number a team would ignore. Anti-unifying the predicates cannot help: an isomorphic group is identical in its predicate by construction and yields zero holes. Graded on the largest identical sub-group in one app, the corpus reads R = 7, I = 4. Five buckets count: `name` x7 and `code` x4 in library, `label` x3 in scalars (the fourth, nullable, is a single leftover and counts nothing), `key` x2 in kanban (its own `LookupBase` and `Label`; glossary's `LookupBase` is the single leftover), `label <> ''` x2 in glossary. Four groups leave a pattern: the two `name` copies outside library, and `title`, span apps; `unique(category, name)` differs in `related_name`, which is a public reverse accessor here; `unique(number)` is a `TextField` beside a `PositiveIntegerField`. Two of the counted buckets are not one-line remedies: `label <> ''` needs a `%(app_label)s_%(class)s` constraint name and each child's `Meta` to merge the base's constraints, which is the invocation kind of duplication of section 5 moved rather than removed. All of this is in-sample: the model was built against the corpus that is grading it, by its author, with no developer confirmation (problem 4), so it is a demonstration that the grade is computable and monotone, not a false-positive rate.
4. **Where the platform owns names, D has no room.** The visibility rung needs the rule name as its intent marker because nothing else holds it. The DB holds constraint names and refuses a second definition under one, so divergence on this rung can only appear as two names for one body, which R and isomorphism already see. Naming as the intent marker is load-bearing exactly where the platform does not already enforce it.

### Out of sample

Every number above is in-sample. The constraint rung reads any Django app, so it was pointed at code the paper was not tuned on: Django's own contrib apps plus DRF's `authtoken` (11 models), strawberry-django's test models (10), graphene-django's test models (8), and the django-graphene-filters cookbook (4 models, the North Star's own shape). The figures are after the two definitional changes the run forced, read by hand below.

| corpus | models | leaves | R | M | D | I | O | findings |
|---|---|---|---|---|---|---|---|---|
| Django contrib + `authtoken` | 11 | 8 | 1 | 1 | 0 | 0 | 1 | `LogEntry.action_flag` `choices` with no `CHECK`; opaque: `Site.domain`'s function validator |
| strawberry-django tests | 10 | 0 | 1 | 0 | 0 | 0 | 1 | opaque: `FruitType.name`'s function validator |
| graphene-django tests | 8 | 8 | 1 | 8 | 0 | 0 | 0 | eight `choices` with no `CHECK` |
| graphene-filters cookbook | 4 | 0 | 1 | 0 | 0 | 0 | 0 | nothing declared: reduced by vacuity |

Read by hand, in Juergens's three classes:

- **Nine `choices` with no `CHECK` (all of M): intentional.** Django's own `LogEntry` does it, and Django's documentation says `choices` are enforced by model validation, which is L1 by the ladder's own reading; ticket #32726 (a `CHECK` from `choices`) was closed wontfix as a cost decision, not a correctness one. The paper's position (section 1, Bailis) is that a vocabulary the database does not hold is bypassable. So the audit is reporting the disagreement between the paper and the platform, not a defect either side would accept as one. On this rung M is a policy count until `ChoicesConstraint` or its equivalent is adopted; a team that declines it pins M at today's value and never moves it, which the baseline file allows and the verdict then has to say.
- **Column widths are not rules.** `name = CharField(max_length=20)` on four fixture models read as isomorphic duplication (R = 4) with a mixin as the remedy, which a reader would reject the tool on. A `CharField` width is `varchar(n)`, a type, graded as a hole like the rest of the footprint's declaration; a `TextField` width reaches no column type and no model validator (Django attaches `MaxLengthValidator` to `CharField` alone), so only the form and serializer fields derive it: a rule authored at L1 with no copy below. That line removes every width leaf on all three corpora and twenty of contrib's twenty-eight; fakeshop uses `TextField` everywhere, so in-sample it never produced a width finding and the line could not have been drawn.
- **A `clean()` that only normalises holds no rule.** `AbstractBaseUser.clean` and `AbstractUser.clean` normalise (the username's case, the email's domain) and never raise. The reader skips a `clean()` whose syntax tree has no `raise`, no `ValidationError` and no call to a helper by bare name; the helper's body is not read, so it is taken to be where the raise went, and on a 16-application Django corpus about one `clean()` in ten delegates its raise [V]. The two function validators are real opaques; a plain function has no deconstruction.
- **Django contrib: R = 1, D = 0, I = 0 on eight leaves.** Django's own apps are reduced on this rung. That is either evidence the rung's definitions are sane or evidence that Django ships almost no declarative constraints beyond `unique`; it is both.

Four corpora, 33 models, 24 leaves, classified by the author: enough to show two false-positive classes the in-sample corpus could not produce, and no duplication finding that survives them. It is not a false-positive rate, and it is not problem 4's study, which needs corpora with business rules in them: test fixtures and contrib apps declare almost none, and the one corpus that does is the one the model was built on. The visibility rung has no out-of-sample corpus in its own fragment, because nothing outside this package declares rules in it; the closest thing is the cookbook's `is_private` columns, which are the North Star's and therefore in-sample. It has a candidate: Hasura's per-table, per-role `filter` metadata is declarative, carries footprints with relation hops and session-variable actor terms, and three public repositories hold about 140 tables and 280 permissions [A]. Read as the lead example, one repository's `service` role has an empty filter on 23 of its 26 tables (R = 23 for the actor-only grant) and another repeats `profile_id = X-Hasura-User-Id` in 21 filters; the reading choice (a role is a dispatch key, not a term, so each role's filter is `Actor(role) == R AND filter`) has to be written down before the run. PostgreSQL's RLS regression suite is the oracle for polarity, since it declares `RESTRICTIVE` where the paper derives it; real applications almost never use that half (112 files against 1.6 million `CREATE POLICY` on GitHub) [A].

**Eight application codebases.** The same runner, with the package import stubbed so only Django is needed and every app's `ready()` made a no-op, pointed at django-helpdesk, healthchecks, django-cms, wagtail, django-oscar, NetBox, Saleor and pretix: 571 models, a few third-party apps their settings install included.

| corpus | models | leaves | R | M | D | I | O |
|---|---|---|---|---|---|---|---|
| django-helpdesk | 21 | 13 | 1 | 9 | 0 | 0 | 3 |
| healthchecks | 12 | 20 | 3 | 10 | 0 | 1 | 0 |
| django-cms | 15 | 9 | 1 | 4 | 0 | 1 | 2 |
| wagtail | 44 | 29 | 2 | 7 | 0 | 0 | 3 |
| django-oscar | 80 | 71 | 4 | 25 | 0 | 3 | 11 |
| NetBox | 162 | 208 | 7 | 78 | 0 | 11 | 100 |
| Saleor | 121 | 177 | 4 | 86 | 0 | 13 | 7 |
| pretix | 116 | 146 | 3 | 81 | 0 | 8 | 18 |

Read by hand, again in Juergens's classes and again without developer confirmation:

- **An inherited `Meta` is a derived copy, in all three of Django's shapes.** `class StockRecord(AbstractStockRecord): pass` carries its base's `unique_together` without writing it (oscar alone has thirteen such classes; wagtail, NetBox, pretix and `social_django` more); `class Meta(Base.Meta)` inherits what it does not name; and a child that adds a constraint must spread `*Base.Meta.constraints`, because Django replaces the option rather than merging it, so the spread members are the base's own objects. A `%(app_label)s_%(class)s` constraint name on an abstract base is one site, interpolated per concrete class. Fakeshop has no abstract base carrying `Meta` options, so none of this was in-sample.
- **M is a policy count here too.** Three hundred `choices` with no `CHECK` across the eight, and a handful of `MinValueValidator` floors with no DB copy (oscar's `priority gte -1`). One shared `STATUSES` tuple drives three fields in healthchecks and reads as M = 3: one authored vocabulary, derived by a constant the audit cannot see.
- **O is not a footnote on a real application.** NetBox keeps its cross-field rules in `clean()`: 96 bodies, O = 100 against 208 leaves, so R and M describe less than the declarative half of its rule base. Pretix 18, oscar 11.
- **The restatements are the study's real material.** Platform-forced: wagtail's `Page` restates `TranslatableMixin`'s `unique_together` and ships a system check (`wagtailcore.E003`) that fails a subclass which drops it, so the audit's "keep the mixin's" remedy would trip it, and that copy is intentional. Unintentional candidates: NetBox's `FrontPort.Meta` restates the `unique(device, name)` constraint `ComponentModel` already holds under a templated name (a new constraint object, where a spread of the base's would have been derived), and `FrontPortTemplate.Meta` does the same to both of its bases' templated constraints; Saleor's four translation models each restate `unique(language_code, slug)` under a per-class name, read as identical duplication whose owner, the abstract base that declares both fields, holds no copy, so `%(class)s` on that base is the remedy; `cc_exp_month` 1..12 on `Payment` and on `TransactionItem`; latitude and longitude validators on NetBox's `Device` and `Site` and pretix's `Event` and `SubEvent`; one regex on `Question.identifier` and `QuestionOption.identifier`. Faulty candidate: Saleor's `Payment.cc_exp_year` has `MinValueValidator(2000)` and `TransactionItem.cc_exp_year` has `MinValueValidator(1000)`. Each bound is its own leaf, so each has multiplicity one and D is zero: section 12's warning about two bodies under two names, realised on a shipped codebase, and the best single data point problem 4 has.
- **`unique(<field>)` across unrelated tables** (healthchecks `unique(code)` on five models, NetBox `unique(name)` in seven groups, Saleor `unique(slug)` on four) is the false-positive class of the fakeshop corpus, at scale.

The candidates above are the developer-confirmation shortlist problem 4 asks for. Larger declarative corpora exist and were not run: PostHog (90 `CheckConstraint`, 336 `UniqueConstraint`), Sentry (21 and 77) and Weblate are where cross-tier restatement would have something to restate; six of the sixteen candidates surveyed declare no `CheckConstraint` at all.

### What it did not do, and what that teaches

- Isomorphism is "same canonical form, different owner" and nothing more. `is_private ne True` and `is_private eq False` are different leaves to the prototype. Section 9 step 3 (anti-unification) and step 5 (SMT) are the fix. Without them, two bodies under one name are caught by D (the name is the intent marker) and two bodies under two names are two unrelated leaves with multiplicity 1 each, so a divergent edit that also renames the rule still reads as a clean codebase, exactly as section 7 warned.
- The ladder is L0, L1, L2, L4 and L6. L0 reads field lookups only: a constraint over an expression (the one-hot link count) is opaque, a regex has no portable DB form and keeps its owner at L1. `Unique` is the only L3 leaf. No L5, no L7. Serializer and form fields, the upper half of roadmap step 3, are not read. `clean()` is opaque even when its body is one comparison, and read as no rule when its tree never raises. Reading it is not unsolved, it is bounded: ConstrOpt lifts Rails custom validators whose guard sits inside a closed grammar (comparisons over fields, `and`/`or`/`not`, a few modelled calls) and leaves the rest, and on a 16-application Django corpus that grammar covers about 30% of model `clean()` bodies and 60% of raise sites, the remainder opaque for four nameable reasons: an ORM query, a loop or `try`, a call the grammar does not model, delegation [V]. The same body run on a proxy `self` that forks at every `bool()` lifts the demo's date rule and a staff-bypass `get_queryset` with no new parser, but it concretises silently on `is None` and `isinstance`, so a lift that is not differentially validated against the real body cannot be published. Pydantic's `model_json_schema()` and drf-spectacular's exporter are the contrast case: both silently drop every validator they cannot read, which is the failure O exists to prevent [V].
- No blessing on the constraint rung: the four patterns in I have no way to move to B, so I cannot reach zero yet, and I has no pin in the prototype (no component has: step 5). I counts groups, so a tenth copy and a deviant copy are invisible to it, and a copy left alone in its bucket is counted nowhere (section 8).
- Owner computation for a row rule finds an existing mixin; it cannot propose one. The isomorphic finding's remedy text is the proposal. Turning that into a refactoring (synthesize the mixin, move the field) is the "forcing" problem of the second early draft, and it stays unsolved.
- The opaque census is a text scan. It counts `apply_cascade_permissions(` in source, which is honest about what it can see and is exactly as fragile as it sounds.
- No baseline file, no settings key, no two-sided pin, no `ratio`. `--strict` is a one-sided floor at R=1, M=0, D=0, O=0, which section 8 argues is insufficient for adoption.
- The explain extension has no cap and no fail-closed gate. `DjangoDebugExtension` is the posture it must copy before it is more than a prototype.

## 13. Related work

Organized by what the paper claims. Tags as in the header.

**Each rule once, as a principle.** Ross, "Rules Normalize!" (1996) [V]: rules normalize to a type in the data model, and normalization "tells you explicitly where the rules should go." The closest single prior claim; no lattice, no actor or workflow rungs, no gate. Ross, "Rule Reduction" (2005) [V]: break rules into atomic, independently reusable rules, which is the branch-in-disguise split done by hand. Business Rules Manifesto (2003) [V]: declarative, separate from process, "a rule is distinct from any enforcement defined for it." Halpin, Object-Role Modeling [V]: constraints declared once on the roles they span, mapped down deterministically, implied constraints are not rules. Groenewegen and Visser, WebDSL (SLE 2009, ICWE 2008) [A]: validation declared on the data model and applied across UI and persistence. Date, What Not How (2000) [A]: the RDBMS as a declarative rule engine.

**Placement by information.** Larman, GRASP Information Expert [V via secondary]: assign responsibility to the class that has the information. Picks the plurality holder; this paper picks the minimal cover. Tsantalis and Chatzigeorgiou (TSE 2009) [A]: automated Move Method from accessed-entity sets, the closest automated misplacement detector for methods. Vernon, "Effective Aggregate Design" (2011) [V]: true invariants define the consistency boundary; false invariants over-scope it. Evans, DDD aggregates [M]. Parnas (1972) [V via secondary]: decomposition by change-driver, a different criterion, cited as a relative. Law of Demeter [A]: caps footprint depth at one hop.

**Compiler and optimizer analogies.** Johnsson, lambda lifting (1985) [A]; Danvy and Schultz, lambda dropping [A]; Knoop, Rüthing, Steffen, Lazy Code Motion (PLDI 1992) [V]; Click, global code motion (PLDI 1995) [M]; Peyton Jones et al., let-floating (ICFP 1996) [A]. Selinger et al. (SIGMOD 1979) [A]; Chaudhuri (PODS 1998) [V]; Hellerstein and Stonebraker, predicate migration (SIGMOD 1993) [A]; Levy, Mumick, Sagiv, predicate move-around (VLDB 1994) [M for mechanism]; Graefe, Cascades [A].

**Decidable rule languages and equivalence.** Cutler et al., Cedar (OOPSLA 2024) and Cedar Analysis [V]. Backes et al., Zelkova (FMCAD 2018) [A]. Eiers et al., Quacky (ICSE 2022) [A]: model counting over policies, a computed number with a repair loop. Fisler et al., Margrave (ICSE 2005) [A]. Queralt and Teniente (ER 2006), Cabot et al. (JSS 2014) [A]: OCL invariant redundancy. Calvanese et al., DMN decision tables (BPM 2016, IS 2018) [A]: overlap, completeness, simplification. Preece and Shinghal (1994) [V]: rule-base anomaly classes. Al-Shaer and Hamed (INFOCOM 2004) [A]: firewall rule relations. Chandra and Merlin (STOC 1977) [A]; Klug 1988, van der Meyden 1992 [M]: containment complexity. Chu, Ilyas, Papotti, denial constraints (PVLDB 2013) [V]: decidable implication and minimal cover for L0 to L3. Rondon, Kawaguchi, Jhala, Liquid Types (PLDI 2008) [A]. Leinberger et al., SHACL containment (ISWC 2020) [A]. Habib et al., JSON Schema subschema (ISSTA 2021) [A]. Apt, Blair, Walker, stratification (1988) [V]: a dependency order, not the ladder's. Date and Darwen, The Third Manifesto [V]: a type constraint defines a type's values and may not read database state; a key is a database constraint. Hibernate Validator's DDL mapping [V]: `@Size` and `@Digits` become column length, precision and scale, `@NotNull` a column flag, `@Min` and `@Max` a `CHECK`, the closest shipped taxonomy to the type-versus-rule line. Libkin, SQL's three-valued logic and certain answers (ICDT 2015) [M]; Calcite `RexSimplify` and `Sarg` [V]; PostgreSQL `prepqual.c` [V]; sqlglot `simplify` [V]: shipped normalisers, none claiming canonicity.

**Cross-tier duplication and lifting.** Yang et al. (ICSE 2020) [V]: counts validations and leaves custom bodies unread (18% of validation functions on average); twelve Rails applications, no Django counterpart. Liu et al., ConstrOpt (PVLDB 2023) [V]: the one published body lifter, an AST pattern match over a closed grammar of `if cond: errors.add`. Near and Jackson, Rubicon (FSE 2012) [A]: symbolic execution by running the real interpreter on proxy objects. Huang et al., CFinder (ASPLOS 2023) [A]. Wang et al., EqDAC (ICSE 2023) [V]: NNF with the comparison flipped under negation (two-valued, so unsound under SQL NULL), AHU isomorphism proving 96.9% of equivalent pairs, Z3 for the rest. Pydantic `model_json_schema()` and drf-spectacular [V]: schema exporters that silently drop every validator they cannot read. Bailis et al., Feral Concurrency Control (SIGMOD 2015) [V] and Coordination Avoidance (VLDB 2015) [V]. Alkhalaf et al., ViewPoints (ISSTA 2012) [A]: client versus server validation as automata. Bocic and Bultan (ICSE 2014) [A]. Zhang et al., Blockaid (OSDI 2022) [V] and Ote (OSDI 2026) [A]: authorization lifted out of Rails code into a DB-level policy. Rizvi et al. (SIGMOD 2004), Guarnieri and Basin (PVLDB 2014) [V]: enforceability frontier for query rewriting. Chlipala (OSDI 2010), Jeeves (POPL 2012), Qapla (USENIX Security 2017) [A]. Ceri and Widom (VLDB 1990) [A]; Nicolas (1982) [A]: declare once, compile enforcement. Tierless languages: Links, Ur/Web, Eliom, Weisenburger et al. survey (CSUR 2020) [A]: one source, several tiers, placement by annotation or performance, no footprint floor. Philips et al., search-based tier assignment (2018) [A].

**Frameworks and products.** PostgreSQL RLS [V]. django-rls [V]: `ModelPolicy(filters=Q(...), permissive=True)` compiled to `CREATE POLICY`, with a `permissive` flag and no consistency check against ORM visibility (`https://django-rls.com/docs/2.1/api-reference`). Supabase database linter [A]: `multiple_permissive_policies`, the nearest shipped policy-redundancy lint. Hasura row permissions [A]: a declarative predicate folded into the query; "permission pushdown" is this paper's phrase, not Hasura's. ZenStack, Payload, Directus, CASL, CanCanCan `accessible_by`, Cerbos query plans, Oso data filtering (deprecated), OPA partial evaluation [A]: one declared rule drives both the object check and the collection filter, always under the restriction that the rule is declarative. On polarity [V]: ZenStack `@@allow`/`@@deny` on the model with deny overriding; Cerbos's scope law `REQUIRE_PARENTAL_CONSENT_FOR_ALLOWS`, a scope that may only restrict; Ash policies, AND across policies with a passing `bypass` beating what follows; AWS service control policies and permissions boundaries, a tier that only restricts; Cedar's unscoped `forbid`; Casbin's `allow and not deny` effect; OPA's `not deny` idiom. django-rules, graphql-shield, Pundit [A]: named composition over opaque callables, two bodies for check and scope, Pundit's `verify_authorized` as the invocation tripwire. django-guardian [A]: single source by storing the rule as data. Django 4.1 `validate_constraints` [V]; django-extra-checks 0.17.0 `field-choices-constraint` [V]: the one Django check that flags a rule above its floor. DRF `ModelSerializer` validator derivation [V]: `UniqueValidator`, `MaxLengthValidator` and `allow_null` from the model, never `full_clean()`, never a `CheckConstraint`. Rails `database_consistency`, `active_record_doctor`, `consistency_fail` [A]: validator-versus-constraint checkers with a baseline file, whose remedy is "add the missing copy." Evans and Fowler, "Specifications" [V]: named composable leaves, atomic one-parameter specifications, subsumption. strawberry-graphql-django, graphene-django, PostGraphile [A].

**Detection and metrics.** Roy and Cordy, clone survey (2007) [A]; Krinke and Ragkhitwetsagul (2025) [A]: Type-4 benchmarks unreliable. Gabel, Jiang, Su (ICSE 2008); Jiang and Su (ISSTA 2009) [A]. Baker, parameterized matching (WCRE 1995) [A]. Bulychev and Minea, anti-unification [A]. Basit and Jarzabek (2005) [A]: templates do not remove all clones. Tsantalis et al., clone refactoring with lambdas (ICSE 2017) [A]. Kapser and Godfrey (2008) [A]. Juergens et al. (ICSE 2009) [V]; Juergens, redundancy-free source size [A]. CP-Miner (OSDI 2004) [A]; DejaVu (OOPSLA 2010) [A]; Dillig, Dillig, Aiken (PLDI 2007) [A]. Engler et al., Bugs as Deviant Behavior (SOSP 2001) [A]; Amann et al. (TSE 2018) [A]: mined missing-call detection is noisy. Eaddy et al. (TSE 2008) [A]: scattering correlates with defects. Tate et al., equality saturation (POPL 2009); Willsey et al., egg (POPL 2021); Zhang et al., egglog (PLDI 2023) [A]. Bryant, ROBDDs (1986) [A]. Cosette (CIDR 2017) [V]; EQUITAS, SQLSolver, QED, VeriEQL [A]. Sonar metric definitions [V]; coverage.py `fail_under` [V]; PIT thresholds [V]; qntm, ratchets [V]; Betterer [V]; mypy-baseline, ESLint bulk suppressions, rubocop-gradual, basedpyright's baseline, Notion's TSV ratchet [V]: two-sided or member-keyed baselines (section 8); Rust `#[expect(lint, reason)]`, RuboCop `AllowWithReason`, SARIF suppressions and fingerprints [V]: reasons and stale-suppression errors; Ford, Parsons, Kua, fitness functions [A]; ArchUnit, dependency-cruiser, Tach [A] and import-linter [V]: structural placement only, import-linter also pricing an import edge.

**Security placement.** Saltzer and Schroeder (1975) [V]: fail-safe defaults, complete mediation, least common mechanism. Anderson, reference monitor (1972) [A]. NIST SP 800-162 [V]: PDP and PEP may be centralized or distributed. OWASP Top 10:2021 A01 [V]. Ruohonen, SoK on safe defaults (2025) [V]. Django CSRF how-to [V]. Rails mass assignment (2012) [A]. Kern, "Securing the Tangled Web" (CACM 2014) [A].

## 14. Retracted positions

Positions an earlier draft stated and a reader of it may still hold. Each is retracted here once; the live text states the current position without echo.

- "Push down" was the placement rule. A rule moves to the owner its footprint and polarity compute, up or down. Section 4.
- "Level" was Datalog stratification. The ladder orders rules by the data they can see. Section 3.
- "Lowest layer" was unconditional. It is the lowest layer that can enforce the rule; the DB ceiling is explicit. Section 3.
- Multiplicity counted every statement. It counts authored copies and required invocation sites; derived copies count zero. Sections 3 and 8.
- "Unique owner" was asserted. It needs the named tie-break. Section 4.
- Seed rule 5 was Level-1 and seed rule 4 had no DB rung. Both are L0. Section 6.
- The actor rung was L4. It is L6, so aggregate composition sits below policy. Section 3.
- The metric was (R, M, B). It is (R, M, D, I, B, O): a snapshot with every rule in opaque Python scored reduced, and isomorphic and divergent copies reached no count. Section 8.
- The placement gate was one thing. It refuses where the owner scope exists and reports where it must first be created. Section 4.
- Defects were named by their remedy in some sections and by their error in others. Defects are stated too high or too low; remedies move down or up. Section 4.
- "Blessed" meant three things. It is one mechanism with three reasons, and it reaches opaque bodies. Sections 3, 4 and 8.
- "Smallest scope" was undefined and "owner from the footprint alone" was the claim. Scope has a binding order, and the owner is the tightest cover whose law admits the leaf's polarity. Sections 2, 3 and 4.
- M was "the authored site is not the owner". It is "the owner holds no copy, authored or derived". Sections 3 and 8.
- Every isomorphic copy raised R. Only the largest sub-group one field template absorbs does; the rest is I. Sections 5 and 8.
- "Permission pushdown" is this paper's phrase, not Hasura's, and Cedar used "footprint" first. Section 13.
- An actor-only restriction was owned by the model it restricted, at L6, and a universal restriction had no home. The schema has a second scope, AND-composed and evaluated above the bypasses, that owns it; a model owns only leaves that read its rows. Section 3.
- The owner search stopped at abstract bases. A multi-table parent is a scope too. Section 3.

## 15. Verification debt

From memory, not fetched, must be checked before citation: Codd 1970/72; Armstrong 1974; Beeri and Bernstein 1979; Klug 1988; van der Meyden 1992; Fagin et al. on the chase (2005); Baader and Nipkow (1998); Click 1995; Evans's aggregate text; Levy-Mumick-Sagiv mechanism; let-floating directions; Fowler's Move Method book text; Larman's own wording (Wikipedia's is verified); Hop (DLS 2006); Suwa, Scott, Shortliffe 1982; Nguyen et al. 1985; Hardy's confused deputy; Miller, "Capability Myths Demolished"; Zelkova first author; the POST 2015 XACML-SMT authors; Stryker threshold semantics.

Fetched at abstract level only, numbers not independently confirmed: CFinder's 210 missing constraints and 78/79% precision/recall; Yang's 22-issue Django sample; EqDAC's solver and constraint tier; Hibernate `apply_to_ddl` mapping details; whether Cedar supports user-defined named predicates. Single runs by research agents, not re-run by the author: the 16-application `clean()` census (175 bodies, 355 raise sites, netbox supplying half), the Hasura permission counts, the z3 pair timings; the eight-corpus audit of section 12 has been run twice by agents and never by the author. Yang's table counts (DB presence 32.9%, length 32.3%) were read from a cached copy lost to a crash.

Not searched: capability-based design and ambient authority; Datalog-containment chase confluence as an adjacent confluence result.

Null results, each resting on a handful of queries: normal forms for invariants across tiers; footprint-computed enforcement level; Knuth-Bendix on rule systems; a formal treatment of Postgres RLS as a lifting target; a multiplicity metric with a CI floor; invocation-site multiplicity; an automatic template-versus-delete cost model; equality saturation on business rules; a Django cross-layer validator-versus-constraint detector; a study of the reverse (global restated per model) defect.

## 16. Candidate titles

- Square-free business logic: normal forms for invariants in a declarative ORM and GraphQL framework
- Every rule has an owner: computing placement from footprint in a restricted rule language
- Reduced: a CI ratchet for business-rule multiplicity and misplacement

## Appendix A. Landing: where each piece of the prototype lives

The prototype is a worktree with no card on the package's board. This appendix records what it stands on, what owns each of those surfaces, and the three places it could be packaged, so that the implementation can be sequenced without rediscovering it. Card numbers are the board's and are quoted with their titles because the numbers rotate on renumber.

### What the prototype touches, and who owns it

| Prototype piece | Surface it stands on | State of that surface | Owner: the spec decision, or the card where no spec is written |
|---|---|---|---|
| framework-owned `get_queryset` body (`rules/apply.py`) | the sealed visibility boundary: `get_queryset` first, then filter, order, optimizer, slice | shipped | spec-045 Decision 1 (hook output rebuilt into a framework-owned queryset) and Decision 3 (no identity fast path on the runners) |
| "does this type filter its rows" (the prototype flips `has_custom_get_queryset()`) | the per-class `has_custom_get_queryset` stamp the optimizer walk reads to decide whether a relation target's hook runs | shipped as a per-class stamp, which cannot vary per schema; one predicate is planned | spec-053 B5, one `scopes_rows(type, definition)` predicate answering under the executing schema |
| visibility across a relation in the optimizer walk | walk-time `Prefetch` queryset construction | shipped at walk time; a bind-time slot is planned | spec-068 Decision 4 (a binding slot on every relation whose target can filter rows, a schema restriction that reaches it included) and Decision 2 (each slot's bound result carries its `RowIdentityProof`) |
| actor fold of a declared rule | the operation-scoped memo | planned | spec-058 Decision 3 (canonical form, footprint and owning scope structural; the fold request-bound, the viewer re-read at each lookup); `docs/multi-root-graph-recreation.md`, "Cache safety" item 3 |
| cascade on by default for rule-bearing types | `apply_cascade_permissions` over forward single-column FK / O2O edges | shipped for those edges; **to-many edges undecided** ("hide the parent, or narrow the list") | spec-034 Decisions 5 and 6 (the walk; row exclusion); the to-many question is card 058's, and spec-058 Decision 7 compiles `EdgeScope` narrow-only onto the child queryset |
| relation terms of a declared rule | `optimizer/predicates.py::related_rows_exist` | shipped primitive; the prototype emits a join `Q` instead | the multiset contract of `docs/row-preserving-predicates-part1-plan.md` (a predicate the framework compiles from a declaration, the framework-owned `get_queryset` body included, is a selection whose relation terms compile through `related_rows_exist` over each hop's visible rows); spec-058 Decision 4 (`PredicatePlan` compiles through those primitives) |
| row narrowing as the enforcement form | `queryset.filter(Q)` | shipped; an opt-in reversal is planned: a `pk=0` sentinel node with `isRedacted` in place of exclusion | card 064 Opt-in node-sentinel redaction tier, which must "reconcile with the cascade"; no spec |
| `Meta.visibility`, `Meta.cascade`, `Meta.blessed` | `ALLOWED_META_KEYS` and `__init_subclass__` validation | shipped as a hand-written list | none; card 062 carries an optional item folding the finalizer's `_bind_filtersets` / `_bind_ordersets` / `_bind_fieldsets` into one table-driven binder, which does not reach key validation |
| `DjangoSchema(visibility=, restrictions=)` | `DjangoSchema.__init__` | shipped; its subclass-friendliness is a pending pin | card 055 Apollo Federation (pins it; routes `_entities` through `get_queryset`, so schema-level rules reach entity fetches only if they stay inside the hook); no spec |
| `DjangoVisibilityExplainExtension` | the response-extension slot | one explain extension is planned (optimizer plan map as JSON) and one shipped debug extension is being moved to a satellite package | spec-068 Decision 6 and its R10 row (a visibility-bindings field in the operation plan map, fed by an operation-scoped sink that root-resolver and cascade hook calls report to); card 069 Optimizer explain mode renders the map; spec-052 moves the debug extension. A visibility trace is that field, not a second extension |
| `inspect_rules` | management-command surface, mirrors `inspect_django_type` | shipped pattern, no owner for this command | none |
| field-level gates | `check_<field>_permission` on a `FieldSet`, raise-only, run after the cascade narrows | planned; the beta carve-out says the beta release ships no per-field read permission | spec-059 Decisions 2 and 11 (gates fed through the field-name to gate mapping, composed by the generated resolver's wrapper) and Decision 9 (cascade first); spec-034 Decision 2 defines the gate; card 057 Beta release carries the carve-out |
| declarative row and field permissions as a capability | none | a `BACKLOG.md` row, `declarative_row_and_field_permissions`, post-1.0; not a card | that row: the Meta and schema shape, rules applied before consumer hooks run, and the order restrictions first, then bypasses, then the type's rules |
| constraints rung (`rules/constraints.py`, `ChoicesConstraint`) | Django model `Meta`, fields, validators; no GraphQL surface | shipped Django; nothing on the board touches `clean()`, validators or constraints as a feature | none |
| serializer and form tier (not built) | `ModelSerializer` and `ModelForm` mutation flavours | shipped | spec-038 Form-based mutations; spec-039 DRF serializer mutations; 053 and 077 edit those modules for consolidation and naming only |

Three consequences. First, the prototype is correct only on the edge shapes the shipped cascade covers; its cascade default inherits 058's answer for to-many edges, and its enforcement form is the one 064 makes optional. Second, that enforcement form, `queryset.filter(Q)` inside the hook, is a consumer-shaped queryset to card 068's row-identity gate, which holds no proof for it; enforcement compiles through 058's `graph.apply`, so the binding slot 068 reads carries a proof. Third, two of the three surfaces it adds to the package have an owner that will restructure the seam they sit in (055's pin for the schema kwargs; spec-053 B5's `scopes_rows`, spec-058's plan objects and spec-068's binding slot for the hook body), and the Meta keys have none, so the prototype is rebuilt on those, not merged ahead of them.

### What depends on Strawberry, and what does not

Read by module, the dependency on the GraphQL package is narrow:

| Module | Depends on | Could stand alone |
|---|---|---|
| `rules/fragment.py` | Django ORM (`Q`, `F`, `Model._meta`) | yes |
| `rules/constraints.py` | Django ORM, `class_prepared` | yes |
| `rules/audit.py` | the type registry (`registry.iter_types()`), `type_rules` | yes behind a site-provider protocol: "give me (model, site label, rules, law, overrides-hook?)" |
| `rules/apply.py` | `info.schema` and the request user, read through the private `_strawberry_schema` and `_request_from_context`; the sync `apply_cascade_permissions` only; `model_for` | no; this is the host adapter. It must read the schema through `utils/typing.py::strawberry_schema_from_info` and the request through `utils/permissions.py::request_from_info`, which fails closed: a context with no resolvable request raises `ConfigurationError` naming the family label the caller passes, where the prototype's `_request_from_context` returns `None` and reads as anonymous. It needs no async twin: the default body is one sync body that `utils/querysets.py::apply_type_visibility_async` calls on the event loop, so actor terms must be plain attributes of the loaded user row |
| `extensions/visibility.py` | `strawberry.extensions.SchemaExtension` | no; host adapter, which must derive from the package's `extensions/operation_state.py::_OperationBoundExtension` base |
| `types/base.py` stamping, `schema.py` kwargs | the package | no; host adapter |
| `inspect_rules` | the two above | the constraints rung already runs with no schema |

So three cuts are available, and the modules sort cleanly into them:

1. **Inside this package** (`rules/`). The enforcement carrier becomes 058's `PredicatePlan`, the type verdict is 053's `scopes_rows`, the trace is the visibility-bindings field of 068's plan map, delivered through its operation-scoped sink and rendered by 069.
2. **A satellite package** beside `django-strawberry-debug` (052) and `django-strawberry-federation` (055): the fragment, the constraints rung, the audit and the command in the satellite; the host adapters stay in this package behind a small protocol (a `get_queryset`-shaped hook, a schema attribute pair, a trace sink). Card 052's pattern does not carry it: 052 extracts a leaf no core module calls, while a rules adapter is called from inside `DjangoType.get_queryset`, so this cut needs a host registration seam, and no card provides one.
3. **A framework-independent package** for any Django project: the constraints rung needs nothing but Django and is the proof that the fragment is not a GraphQL idea; the visibility rung needs one `get_queryset`-shaped seam, which DRF viewsets, graphene-django types, strawberry-graphql-django types and this package all have, so a host adapter is a few dozen lines each, and the audit's site provider is what each adapter implements.

The second and third differ only in where the first adapter lives. Cut 3 is the one the paper's thesis implies, since the ladder, the owner and the metric are stated over Django models and actors, not over a GraphQL schema.

### Known holes in the fragment

Found by reading the fragment against the board and against the rules real codebases carry, and the spec's gap list wherever the work is filed:

- **Ownership.** `row.owner_id == actor.pk` compares a row term to an actor value. `Compare` takes a `Field` or a constant on the right, so the most common visibility rule there is has no footprint, owner or `Q` form. Its footprint is {row.owner_id, actor.pk}, L6 on the model; its `Q` is `Q(owner_id=actor.pk)` after folding the actor.
- **Membership.** `row.team in actor.teams` reads a to-many actor term and compiles to `Q(team__in=<ids>)` or an `EXISTS`; the second most common rule. Actor terms are single attributes today.
- **Relation terms.** `evaluate` emits a raw join `Q` for every relation term, to-one included, so an edge rule tests the raw relation, not the target's visible rows. Under `Meta.cascade = False` a to-one edge rule reads the fields of a target row its type hides, which spec-060 Decision 12 rejects; across a to-many edge the join (`Q(replies__is_private=False)`) also multiplies the rows it filters, and the fragment does not refuse that footprint: `validate_footprint` walks reverse and many-to-many relations as readily as forward ones, and `owner()` gives `Field("replies__is_private")` an edge owner. Every relation term must compile through the package's row-preserving `related_rows_exist` over each hop's visible rows (the multiset contract of the row-preserving Part 1 plan, and the source of spec-058's `PredicatePlan`), so `evaluate()` cannot stay a bare `Q` for a relation term; the bare `Q` is right only for row-local terms.
- **Sentinel mode.** Under 064 a hidden related row surfaces as a sentinel rather than being narrowed out; a `Q`-filter enforcement form does not produce that, so the enforcement body needs a second output shape.
- **Field scope.** 059's `check_<field>_permission` is a rule whose footprint is {actor, one field of one type} and whose law is deny-by-raise. That is a scope the ladder does not have (a field of a type, below the model in bindings) and a rung the fragment does not reach; when it exists, "the same actor predicate on six fields" is the duplication it will measure.

### What the prototype gets wrong

- **Schema restrictions miss rule-less relation targets.** The hook reads them off `info.schema`, and root runners always call the hook (`utils/querysets.py::apply_type_visibility_async` has no identity fast path), but the optimizer walk runs a relation target's hook only when the target reports a custom `get_queryset` (`optimizer/walker.py::_target_has_custom_get_queryset`). That report is a per-class stamp and cannot vary per schema, and a rule-less type keeps the identity default, so across a relation a universal restriction misses exactly the types it exists to cover. The restriction stays on the hook path, with the viewer re-read at each lookup (spec-058 Decision 3); the per-type verdict becomes spec-053 B5's `scopes_rows(type, definition)`, answered under the executing schema, and spec-068 Decision 4 gives every relation a schema restriction reaches a visibility binding slot.
- **A consumer override drops declared rules silently.** The rules run inside the default `get_queryset` body, so an override that does not call `super()` discards every rule declared on the type and its model, with no error and no audit finding. The backlog row requires the opposite order: rules applied before consumer hooks run.
- **Actor terms are unvalidated.** `evaluate` reads an actor attribute with a `None` default, so a misspelled attribute reads `None`, and a negated restriction over it (`NOT actor.is_suspendd`) passes everyone.
- **Cascade on by default meets a cycle at request time.** Every rule-bearing type cascades unless it opts out, and the shipped cascade raises on a forward-FK cycle on each request that walks it. Declaring a rule can turn a working schema into one that fails per request; the cycle must be refused at finalize.
- **"Authored and enforced are one object" holds only for row-local and to-one terms.** `canonical()` pushes `Not` through junctions by De Morgan, which changes Django's quantifier on a multi-valued relation, and each rule is applied by its own `.filter()` call, so different related rows can satisfy different rules. Over a to-many term the enforced predicate is not the authored one.
- **Two words collide with the package's vocabulary.** The schema keyword `restrictions` and the word "bypass" are already spec-060's "visible-row restriction" and "permission bypass", with different meanings. Both need glossary anchoring before either ships as a public name.

### Order of work that respects the board

Reading other codebases is safe; landing is not. The census of real visibility bodies (`get_queryset`, `filter_queryset`, permission scopes in strawberry-graphql-django, graphene-django and DRF projects), graded as expressible, expressible with a named extension, or irreducible, is the research that sizes the fragment and ranks the holes above, and it informs the `BACKLOG.md` row's spec. The prototype's design inputs have owners: a declared rule's structural half and request-bound fold are spec-058 Decision 3; relation terms as row-preserving selections are the Part 1 plan's multiset contract and spec-058 Decision 4; the visibility trace is spec-068 Decision 6's visibility-bindings field, which 069 renders; the Meta and schema shape and the restriction-above-bypass order are the `BACKLOG.md` row `declarative_row_and_field_permissions`. The rebuild happens on top of 058 and 059; the first production consumer runs it once the backlog row is a card.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
