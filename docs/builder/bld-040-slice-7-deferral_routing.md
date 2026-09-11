# Build: Slice 7 — deferral routing (three `bld-040-final.md` catalog entries to their owners)

Spec reference: [`docs/SPECS/spec-040-auth_mutations-0_0_13.md`][spec-040] (archived; shipped in
`0.0.13`). This slice makes **no spec edit** — see `### Verified: no spec edit is owed`.
Status: final-accepted

Build plan: [`docs/builder/build-040-auth_mutations-0_0_13.md`][build-040], `### Scope fence
(maintainer-set)` **including the Slice 7 fence amendment**. Input: [`bld-040-final.md`][bld-final]
`### Deferred work catalog`, entries **1**, **2** and **4** of Block A.

**Planned at `HEAD = d3b91c8d`, measured — not inherited.** The dispatch's opening context named
`301bf450`; `git log --oneline -1` reads `d3b91c8d fix(spec-050): close the second implementation
review and record the green gate`, one commit further on and the concurrent session's. The same
staleness runs through that context's dirty list, which is why `### Baseline-dirty` below was
re-measured from scratch rather than copied.

---

## What this slice is, and what it is not

The cycle reached `final-accepted` and was handed to the maintainer. The maintainer then reviewed
the catalog and ruled that **three** of its entries are routed to owners now rather than left in
the catalog:

| Catalog entry | Kind | Owner | Where the work lands |
|---|---|---|---|
| 4 — bug-hunt round provenance | `.py`, fix in place | this slice | `tests/auth/test_sessions.py`, 2 comment lines |
| 1 — inline `subprocess.run([sys.executable, …])` idiom | board row | `TODO-ALPHA-053-0.0.15` | new `Scope` `CardItem`, order **64** |
| 2 — `docs/GLOSSARY.md` auth entry staleness | board row | `TODO-ALPHA-056-0.0.17` | new `Scope` `CardItem`, order **91** |

**It is not a closeout.** The fence amendment adds card rows; it closes no card, bumps no version,
touches no `CHANGELOG.md`, and leaves [`docs/GLOSSARY.md`][glossary] **out of scope** (separate
generator, concurrently dirty). `scripts/build_glossary_md.py` is **not run** in this slice.

**It is not a spec slice, so it carries a `### Dispatched findings checklist`** rather than a
`### Spec slice checklist (verbatim)`. The input is a maintainer ruling over already-built work, not
a `## Slice checklist` sub-bullet, which is exactly the case [`BUILD.md`][build-md] `## Review
rounds` defines that heading for. One box per routed item, in the position and under the
tick-and-audit discipline the spec-slice checklist would hold.

---

## Corrections of record — `C1` / `C2` written at planning, `C3` added at final verification

Both were re-derived at source during this pass with the population named, per this cycle's own
standing lesson that a supporting tally attached to a conclusion holding at any value is what
reaches a maintainer unchallenged.

### C1. The subprocess population is 8 call sites in 8 files, 9 occurrences — the dispatch's "9 call sites" is wrong in its subject

The dispatch states "**8 files, 9 call sites**" and says the catalog's earlier figure of 8 call
sites was wrong. **It is the other way round.** [`bld-040-final.md`][bld-final] entry 1 said "9
occurrences in 8 files, of which one (`tests/test_scalars.py`) is a docstring mention, so 8 call
sites in 8 files" — both of its figures are right, and they are figures of two different
populations. Re-measured this pass over the git-tracked `tests/` tree:

- bare `sys.executable` token: **9 occurrences in 8 files** — `tests/auth/test_mutations.py`,
  `tests/auth/test_sessions.py`, `tests/base/test_init.py`, `tests/filters/test_finalizer.py`,
  `tests/filters/test_sets.py`, `tests/orders/test_inputs.py`,
  `tests/rest_framework/test_soft_dependency.py` (1 each), `tests/test_scalars.py` (**2**);
- of `tests/test_scalars.py`'s two, `:319` is inside the docstring of
  `::test_package_import_does_not_emit_strawberry_deprecation_warning` (`` ``sys.executable`` is the
  venv's Python under ``uv run pytest`` ``) and `:325` is the call. Read at source, both.
- corroborating instrument: `subprocess.run(` per file gives `tests/test_scalars.py` = **1**, which
  is the same fact measured a second way.

So: **9 occurrences, 8 call sites, 8 files.** This is `START.md`'s "count right in every digit,
wrong in SUBJECT" shape — the fifth instance this cycle has produced — and the bullet text pinned
below states *which* figure each number is, because a bullet that gives one number without naming
its population has already lost the population.

### C2. Catalog entry 3 (`spec-042 Revision N`) is not stranded, and `bld-040-final.md` misclassifies it

Independently re-verified this pass, not inherited:

- `tests/middleware/test_debug_toolbar.py` carries `spec-042 Revision` **5** times, at `:21 :111
  :475 :509 :523`;
- [`docs/SPECS/spec-042-debug_toolbar-0_0_14.md`][spec-042] carries `Revision 5` **9** times,
  `Revision 7` **2**, `Revision 8` **1**;
- `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md` **does not exist**.

Every one of the five citations therefore resolves today. `bld-040-final.md` entry 3 files them as
"same defect class as `F2` (a label vocabulary a rationale extraction stranded)" — `F2`'s defect is
that **this** cycle's rationale move stranded its citations, and no such move has happened to
`spec-042`. The entry is a live style question (round-ordinal provenance in a test comment) but not
a stranded-citation defect, and **nothing is homed for it**. `bld-040-final.md` is a closed record
outside the fence and is not being corrected; the correction lives here.

### C3. The slice's own pinned bullet shipped three figures wrong in their subject — added at final verification, because a run of five is a pattern and not five accidents

`C1` and `C2` were written at planning. Review and the apply-changes pass produced a third of
**exactly the same shape**, and it is recorded here rather than left scattered across four worker
sections, because the pattern is the finding.

- **M1(i)** — the pin said "only four of them configure Django at all"; **five of the six** do.
- **M1(ii)** — the pin named **three** inline re-spellings; there are **four**, which also broke the
  sentence's own arithmetic ("three of them near-identically and one compressed" over a three-item
  list).
- **L1** — the pin said the cycle "collapsed the two copies inside `tests/auth/test_mutations.py`";
  at HEAD that file carries **one** copy. The cycle extracted a helper from the single existing copy
  and routed a newly added second probe through it.
- **L2** — my V7 predicted `check_citations.py` at **980 / 166**; the measured value is **981 / 167**
  because the bullet carries **two** `path::Symbol` citations, not one.

Re-derived independently at final verification, not accepted from the review: `tests/filters/test_sets.py`'s
`child` local is newline-joined and carries the full `sys.path` + `DJANGO_SETTINGS_MODULE` +
`import django` + `django.setup()` prologue, read at source rather than inferred — so the
Django-configuring split is 5/6 with only `tests/base/test_init.py` outside it, and the re-speller
inventory is four files. Positive control that the instrument can return zero where it should:
`tests/test_scalars.py` reads **0** `django.setup()` while reading **2** `sys.executable`.

**Every one of the five is arithmetically correct and wrong in its SUBJECT** — which is now this
cycle's documented dominant failure mode, and the sharpest possible illustration of it: the bullet
these three errors sat in is *itself* the homing of a deferred item about a population that had
already been mis-measured twice (the catalog's first instrument returned 7 files, the dispatch's
"9 call sites" conflated occurrences with call sites). A figure attached to a conclusion that holds
at any value is forced right by nothing downstream. Only re-derivation with the population named
catches it, and here it took three separate passes — planner, reviewer, builder — each re-deriving
rather than reading, to get one 4,037-character bullet correct.

**What makes it a closed defect rather than a live one:** the corrected figures are the evidence
`TODO-ALPHA-053-0.0.15`'s open design question (b) will be decided from, and they now say the
opposite of what the original pin said. At four-of-six a reader concludes the import-isolation probe
kind is split down the middle and needs two helpers; at five-of-six it is near-uniform and one
helper with an opt-out for `tests/base/test_init.py` is the obvious shape. Review caught a figure
that would have outlived the cycle on a card nobody re-measures.

### Verified: no spec edit is owed

Re-derived rather than inherited. `docs/SPECS/spec-040-auth_mutations-0_0_13.md`:
`WIP-ALPHA-040-0.0.13` = **4** occurrences, at `:59`, `:403`, `:496`, `:1842` — the recorded decided
non-edits (`:59` / `:496` / `:1842` quote spec-039's own text, `:403` is the card-wrap checklist
item describing the transition itself). Sweeps: `<fill in` **0**, `as of ` **0**, `previously`
**0**, `Revision [0-9]` **0**, `coming soon` **0**. Header re-verified per
[`worker-1.md`][worker-1] `## Spec status-line re-verification`: line 3 reads "Shipped in `0.0.13`
(card `DONE-040-0.0.13`)", which is still true. **My verification agrees with Worker 0's on every
point.** No spec byte moves this slice.

---

## Plan (Worker 1)

### Declarations

- **Hot path: none.** The `.py` change is two comment lines; the board change is two rows in a
  docs-as-data app. Nothing runs per request, per resolver, per row, per connection or per outbound
  message. **No hot-path number is owed.** ([`BUILD.md`][build-md] `## Hot-path budget`.)
- **Floor verification: none required, declared explicitly rather than left silent.** No Django /
  Strawberry / channels integration seam is touched: a comment carries no behaviour, and
  `manage.py shell` / the two render scripts exercise the example project's own ORM, not a
  version-sensitive package seam. **No floor venv is built.** The confirmation instrument is the
  inverse proof in `### Verification` step V2, not a floor run.
  ([`BUILD.md`][build-md] `## Floor verification` `### When it is required`.)
- **Failability: none owed.** The slice introduces **0** new boundaries, guards, gates or rejection
  paths, and lands **no behavioural test change** — the `.py` diff is comment-only, provably so.
  A comment-only diff cannot be proved by mutation (a comment token cannot move a comment-stripped
  digest), so the obligation inverts: prove **executable identity** against HEAD, with a control
  that can fail. That is step V2.
- **Boundary count: 0.** [`BUILD.md`][build-md] `### Slice splitting` asks for the split question to
  be answered in writing, not for a split: three items, one file plus two independent DB rows, no
  shared shape between them, no review-worthy logic anywhere in the diff. **One unit.** Splitting
  would cost two extra full worker cycles for a 2-line comment edit and two `INSERT`s.
- **Coverage: no `--cov*` flag in any pass.** `pytest.ini` auto-applies `--cov`, so every `pytest`
  invocation this plan names carries `--no-cov`. ([`BUILD.md`][build-md] `## Coverage is the
  maintainer's gate, not a worker's tool`.)
- **Nobody commits.** The maintainer commits. No `git stash` / `checkout` / `restore` / `reset` /
  `worktree` at any point, for any reason including verification.

### DRY analysis

- **Helper inventory checked.** Refreshed **for the whole package** this pass — the AST inventory
  over `django_strawberry_framework/` (2,070 lines, written to the gitignored scratch
  `docs/shadow/helper-inventory-040-slice7.md`; disclosed under `### Files this pass wrote`).
  Shapes searched: `subprocess`, `executable`, `isolat`, `provenance`, `comment`. **No candidate:**
  the only hits are `filters/utils.py`'s `FilterGenerationProvenance` family and unrelated
  `provenance` spellings in `orders/` — nothing in the package launches a child interpreter, and
  nothing should. The subprocess idiom is a **test-tree** concern, which is precisely why entry 1 is
  homed on a card rather than fixed here.
- **Existing patterns reused.** For item 1, the file's own four block-header comments are the
  pattern: `tests/auth/test_sessions.py:56` `# classify_transport -- isinstance-first,
  scope["type"]-second`, `:261` `# Session-engine capability answers`, `:320` `# Lock lifecycle:
  cancellation release, scope-ownership, no global registry`, and the two under repair. Two of the
  four already use the `Topic: detail` colon form, so both replacements below keep the line's
  existing shape and change only what the finding is about. For items 2 and 3, the reused pattern is
  the two target cards' own bullet idiom — bold lead clause, measured population with the instrument
  named, files listed, `Measured/Homed <date> by <cycle>` attribution, and for a glossary row the
  standing "DB-generated - edit the fakeshop glossary app's `GlossaryTerm.body` and re-render with
  `scripts/build_glossary_md.py`, never hand-edit" sentence, which card 56 already carries verbatim
  on three sibling rows.
- **New helpers justified: none.** This slice authors no helper, no shared constant, no validation
  branch, no test helper. The shared subprocess helper entry 1 describes is the *subject* of the
  homed bullet, not work this slice performs; its shape is undecided on purpose and the bullet says
  why (the design question is what deferred it).
- **Duplication risk avoided.** Two risks, both real here. **(a) Re-homing an already-homed item.**
  Catalog entry 5 (`Revision N P<n>` in `examples/fakeshop/test_query/test_library_api.py`) is
  already on `TODO-ALPHA-056-0.0.17` — `KANBAN.md:623` reads "`Revision N` … 5 bare, all in
  `examples/fakeshop/test_query/test_library_api.py`", the same five lines. A second row would be a
  duplicate homing, and the file belongs to the live concurrent `spec-050` session. **Not touched,
  not re-homed.** **(b) Folding either new bullet into an existing one.** Both are new `CardItem`
  rows, not amendments: entry 1's population spans five `tests/` subdirectories plus the `tests/`
  root, so it fits under none of card 53's existing directory-scoped bullets; entry 2 is a distinct
  `GLOSSARY.md` anchor from card 56's `Strictness mode` / `Choice enum generation` /
  `SyncMisuseError` / `FieldError envelope` rows, each of which is one anchor per row.

### Implementation steps

Line numbers are pin-at-write-time navigational hints, measured this pass at `HEAD = 301bf450`.
Verify against current source before editing — this tree is written concurrently.

#### Step 1 — `tests/auth/test_sessions.py`, two block-header comments (catalog entry 4)

The file carries **2** occurrences of `hunt` and **1** of `Revision`, all three inside the two lines
below; it carries **0** occurrences of `spec-` and declares no `Spec:` module-docstring line
(re-verified this pass). So nothing here is a spec decision pointer, a glossary anchor, or an
upstream ticket — the three things [`START.md`][start] `## Style Rio cares about` keeps. Both lines
are block headers over a run of tests, not test docstrings.

**The two questions the dispatch requires answered explicitly:**

**(a) Is the parenthetical pure provenance, or does it carry a claim that must survive?**
**Pure provenance — drop it, both times.** `(hunt 0_0_14)` and `(hunt 0_0_14 rev)` name the pass
that produced the tests and the release it ran against. They state nothing about the code under
test; the technical claim in each line lives entirely in the head clause before the parenthesis and
survives untouched. They are also not a *real pointer*: the record they name,
`docs/bug_hunt/bug_hunt-*.md`, is generated and regenerable
(`AGENTS.md` #"Generated `docs/bug_hunt/bug_hunt.*.md` are regenerable"), so there is nothing for a
reader to look up and nothing to restate as a plain clause. The rule's "preserve the technical claim
and any real pointer" is satisfied by deleting the parenthetical and changing nothing else on
line 465.

**(b) At `:720`, is the comment head itself build-phase provenance?** **Yes — "Revision guards" is
provenance and must be replaced.** "Revision" here is the bug hunt's revision round, not a property
of the code: no revision is guarded, and no invariant is named by the phrase. Decided with the
surrounding block in front of me, not assumed. The block runs `:723`–`:827` and holds eight tests:
three pinning that `classify_transport` contains a hostile `__class__` property (both `isinstance`
branches, plus a happy-path control), four pinning that `require_session` contains a hostile
`transport.value` (raising `value`, hostile `__repr__`, hostile `__class__` inside the `isinstance`),
and one pinning that a successful `require_session` never touches `transport.value` at all. The
invariant common to all eight is **exception containment at two named seams over two hostile
attribute surfaces** — which is the same invariant the `:465` block states over a different pair of
surfaces, so the replacement deliberately mirrors that line's wording. The distinguishing claim
(`hostile __class__` / `hostile transport.value`) is already in the line and stays.

**Pinned replacement bytes — carry these verbatim, do not re-derive:**

| Line | From (exact) | To (exact) |
|---|---|---|
| 465 | `# Exception containment: hostile scope / session / lock (hunt 0_0_14)` | `# Exception containment: hostile scope / session / lock` |
| 720 | `# Revision guards: hostile __class__ and hostile transport.value (hunt 0_0_14 rev)` | `# Exception containment: hostile __class__ and hostile transport.value` |

Both replacements are ASCII-only (`AGENTS.md` rule 17 bans non-ASCII in `.py`), 55 and 70 characters,
inside the 99-character limit, and keep the surrounding `# ---…---` rules and blank lines exactly as
they are. Change nothing else in this file.

#### Step 2 — new `Scope` `CardItem` on card 53 (catalog entry 1)

Verified against the live DB this pass, not inherited: `Card.objects.get(number=53)` → title
`'Boundary hardening and system-wide DRY squeeze'`, `status.key='todo'`, target version `0.0.15`;
its `scope` section holds **64** items with `max(order)=63`; `Section.objects.get(key='scope')` has
label `'Scope'`; `CardItem` is uniquely constrained on `(card, section, order)`. **Next free order:
64.** Re-verify all of it before mutating — a concurrent session writes this DB.

Write it through the **Django ORM**, never raw SQL: a raw `INSERT` skips the `post_save` signal that
creates the `UUIDModel` side-row, and both render scripts run an in-process `/graphql/` query
requesting `uuid { id }`, so a row without its side-row breaks the render.

**Pinned bullet text — one line, no newlines** (the board stores only a bullet's first line), ASCII,
no literal `{{card_ref:N}}`, and `path::Symbol` citations that must resolve (**two** of them; this
line originally said one, corrected at final verification — `### C3`):

> ### SUPERSEDED — do not diff the live row against this block
>
> **This block is the text as pinned at planning, and is no longer what card 53 carries.** Review
> found two wrong figures in it (M1) and one wrong claim (L1), and Worker 2 applied three anchored
> replacements: the row is **4,037** characters where this block is **3,652**, a `+385` divergence
> that is the fix, not drift. **The row's current contract is this block plus the three `FROM` /
> `TO` pins in `## Review (Worker 3)` `#### M1` and `#### L1`** — it is not restated a third time
> here, because a verbatim second copy rots twice and there is already one authoritative copy on
> disk (the DB row) and one derivation (pin + three replacements).
>
> Verified mechanically at final verification, independently of both workers: composing this block
> with those three replacements, each anchor asserted to occur exactly once, reproduces the live
> `CardItem` `pk=1624` text **exactly** (4,037 = 4,037, equality `True`), with a perturbed-token
> control that returns `False`. The block is left unedited so the builder's input stays readable.

```text
**The subprocess-isolation idiom is spelled inline at every site - 8 call sites in 8 files spanning five `tests/` subdirectories plus the `tests/` root, with no shared helper.** Measured 2026-09-11 by the spec-040 residual reconciliation cycle over the git-tracked `tests/` tree, counting occurrences with the population named: the bare `sys.executable` token occurs **9** times in **8** files - `tests/auth/test_mutations.py`, `tests/auth/test_sessions.py`, `tests/base/test_init.py`, `tests/filters/test_finalizer.py`, `tests/filters/test_sets.py`, `tests/orders/test_inputs.py`, `tests/rest_framework/test_soft_dependency.py` (one each) and `tests/test_scalars.py` (two) - of which one of the two in `tests/test_scalars.py` is a docstring mention inside `tests/test_scalars.py::test_package_import_does_not_emit_strawberry_deprecation_warning`, so the **call-site** figure is **8** and the **occurrence** figure is **9**; a reading that states one number without naming which it is has already lost the population, and both spellings of that error are on the record. **State the instrument:** a first-argument match on `subprocess.run(\s*\[\s*sys\.executable` returns only **7** files, because `tests/base/test_init.py` builds its argv into a `cmd` local and calls `subprocess.run(cmd, ...)` - count the bare token instead. Control, files calling `subprocess.run(` at all: **10**; the two extras (`tests/test_bug_hunt.py`, `tests/test_ci_governance.py`) invoke `git` rather than an interpreter, read at source to confirm it. **A working prototype already exists, file-local:** `tests/auth/test_mutations.py::_auth_free_subprocess` builds a fakeshop-`sys.path` + `DJANGO_SETTINGS_MODULE` + `django.setup()` prologue, appends the caller's body verbatim and asserts the child's return code - and `tests/auth/test_sessions.py`, `tests/filters/test_finalizer.py` and `tests/orders/test_inputs.py` each re-spell that same prologue inline, three of them near-identically and one compressed onto a single `import django, os, sys;` clause. **The open design question is what deferred this, and it is why the item is a decision rather than a chore. (a) Which conftest.** No single `tests/` subdirectory contains the population, so a subdirectory `conftest.py` cannot serve it; a root `tests/conftest.py` helper widens a contract every package test inherits; and the existing shared test module `tests/_soft_dependency.py` is the precedent for a non-conftest home, but its stated contract is in-process `sys.modules` absence simulation, not launching a child interpreter. **(b) Whether ONE contract can serve all three probe kinds,** which differ in the child's argv and not only in its body: the **import-isolation** probes (`tests/auth/test_mutations.py`, `tests/auth/test_sessions.py`, `tests/base/test_init.py`, `tests/filters/test_finalizer.py`, `tests/filters/test_sets.py`, `tests/orders/test_inputs.py`) assert a submodule is absent from a fresh `sys.modules` and only four of them configure Django at all; the **soft-dependency** probe (`tests/rest_framework/test_soft_dependency.py`) must run with djangorestframework absent and asserts an install hint; the **warnings** probe (`tests/test_scalars.py`) needs `-W error::DeprecationWarning` on the child argv ahead of `-c`. If the answer to (b) is no, the right shape is two or three named helpers rather than one, and saying so with the reason is the deliverable. Homed here 2026-09-11 by the spec-040 residual reconciliation cycle, whose final gate carries the measurement; that cycle had already collapsed the two copies inside `tests/auth/test_mutations.py` into the file-local helper named above.
```

#### Step 3 — new `Scope` `CardItem` on card 56 (catalog entry 2)

Verified against the live DB this pass: `Card.objects.get(number=56)` → title `'Alpha
documentation-debt discharge'`, `status.key='todo'`, target version `0.0.17`; its `scope` section
holds **91** items with `max(order)=90`. **Next free order: 91.** Same ORM rule as step 2.

Re-verified at source this pass: the `## Auth mutations` entry (5,955 bytes) carries `is_active`
**0** times, `unreachable by construction` **1** time, and reads `the privilege columns (`is_staff`
/ `is_superuser` / `groups` / `user_permissions`) are unreachable by construction`. The corrected
contract is stated **in the bullet**, not pointed at — read from the spec at
`docs/SPECS/spec-040-auth_mutations-0_0_13.md:527` (`## Goals` item 4, the two-layer statement),
`:1132` (Decision 6's `for the stock user model … structurally unreachable`) and `:2048`
(`## Edge cases`, the five-member module-level protected set).

**Pinned bullet text — one line, no newlines, ASCII:**

```text
**`docs/GLOSSARY.md`'s `## Auth mutations` entry still carries the unqualified privilege framing the spec-040 reconciliation retired, and enumerates four of the five protected columns.** Verified at source 2026-09-11 by the spec-040 residual reconciliation cycle: the entry reads "the privilege columns (`is_staff` / `is_superuser` / `groups` / `user_permissions`) are unreachable by construction" - `is_active` occurs **0** times in the whole entry, and the unqualified "unreachable by construction" is the exact claim `docs/SPECS/spec-040-auth_mutations-0_0_13.md` deleted during that cycle, because it is false for a custom user model. **The corrected contract is two layers and the entry must carry both.** The protected set is **five** columns - `is_active` / `is_staff` / `is_superuser` / `groups` / `user_permissions` - and: (1) **for the stock user model** the derived registration tuple `(USERNAME_FIELD, *REQUIRED_FIELDS, "password")` simply never names one of them, so privilege escalation is structurally unreachable there; (2) a **custom** user model that does place one of the five in `USERNAME_FIELD` / `REQUIRED_FIELDS` is refused at declaration with a `ConfigurationError` naming the offending field(s) and the model, because auto-exposing one would turn an unusual model declaration into a public privilege or activation-control input. **The scoped survivor is not part of the defect:** "structurally unreachable" is TRUE once scoped to the stock model and must not be swept away with the unqualified sentence - retiring both would retire the contract. DB-generated - edit the fakeshop glossary app's `GlossaryTerm.body` through the Django ORM and re-render with `scripts/build_glossary_md.py`, never hand-edit the rendered file. **Live hazard, re-verified 2026-09-11:** `docs/GLOSSARY.md` is dirty in the working tree from a concurrent session with **exactly one** unrelated hunk - the `## Django AppConfig` entry's three-appliers to four-appliers rewrite adding `_graphql_core_patches`, 1 insertion / 1 deletion - so this edit must land **on top** of that hunk and never by regenerating over it; re-check the hazard before editing, since it resolves once that session commits. Rides the same ORM edit and render as this card's other glossary items.
```

#### Step 4 — regenerate the two kanban exports

`KANBAN.md` and `KANBAN.html` are **generated** from the kanban tables in
`examples/fakeshop/db.sqlite3` by `scripts/build_kanban_md.py` / `scripts/build_kanban_html.py` and
are not hand-editable source; the next regenerate silently reverts a hand-edit.

```shell
uv run python scripts/build_kanban_md.py
uv run python scripts/build_kanban_html.py
```

**Do not run `scripts/build_glossary_md.py`** — `docs/GLOSSARY.md` is out of fence and
baseline-dirty.

### Test additions / updates

**None, and that is the contract, not an omission.** The `.py` change is comment-only, so no test
can observe it and adding one would assert a comment. The board change is data in the example
project's docs-as-data app; its gates are the render `--check`s and the citation gate, all named in
`### Verification`. No temp tests are appropriate; none are planned for Worker 3.

The one focused run worth having is a collection-level sanity check that the comment edit did not
corrupt the module, which V2's AST parse already proves more cheaply and more completely. If Worker 2
wants the run anyway: `uv run pytest tests/auth/test_sessions.py --no-cov -n0` — never without
`--no-cov`.

### Verification (postconditions — every one of these is a measurement, not a reading)

**V1. Provenance retired to zero, in the file's own vocabulary.**
`grep -c hunt tests/auth/test_sessions.py` → **0** (was 2); `grep -c Revision …` → **0** (was 1).
Both tokens exist today *only* on the two edited lines, verified this pass, so both must read 0
afterwards. Control that the instrument runs at all: the same `grep -c` for `session` on the same
file returns a large non-zero.

**V2. The inverse proof — executable identity against HEAD, with a control that can fail.**
A comment-only edit owes this rather than a failability proof. Compare `ast.dump(ast.parse(...))` of
the worktree file against `git show HEAD:tests/auth/test_sessions.py` written to a scratch path
**outside** the repo; comments are absent from the AST, so `IDENTICAL` proves the diff is
comment-only. **`IDENTICAL` is worthless without a control** — run the same comparator over a file
the concurrent session has changed behaviourally (`django_strawberry_framework/list_field.py`) and
require **`DIVERGES`**. Without the second reading, `IDENTICAL` is indistinguishable from an
instrument that compares nothing. No `git stash` / `checkout` / `restore`; `git show HEAD:<path>` is
the only HEAD reference.

**V3. Board rows landed once, not twice.** Guard both inserts with a **marker-absence assert** so a
re-run cannot duplicate: before creating, assert no existing `CardItem` in that card's `scope`
section contains the row's distinctive substring (`subprocess-isolation idiom is spelled inline` for
card 53; `still carries the unqualified privilege framing` for card 56), and assert the target
`order` is free. After creating, re-read both counts: card 53 `scope` → **65** items,
`max(order)=64`; card 56 `scope` → **92** items, `max(order)=91`.

**V4. Both exports fresh, and stable under a second regenerate.**
`uv run python scripts/build_kanban_md.py --check` and `… build_kanban_html.py --check` both exit
**0**. Then prove no further drift: regenerate a second time and compare hashes of `KANBAN.md` and
`KANBAN.html` across the two runs — byte-identical. `git diff` alone shows the cumulative HEAD diff,
not whether a second regenerate is stable, so it cannot substitute.

**V5. The KANBAN diff contains only the two new bullets.** Baseline, measured this pass **before any
edit**: `build_kanban_md.py --check`, `build_kanban_html.py --check` **and**
`build_glossary_md.py --check` all exit **0**, and `git status --short -- KANBAN.md KANBAN.html`
returns **nothing** — both exports are byte-identical to HEAD, while `examples/fakeshop/db.sqlite3`
is dirty for the concurrent session's single `glossary_glossaryterm` body row alone (already
rendered into the dirty `docs/GLOSSARY.md`, which is why the glossary `--check` is green too). So
every kanban table is byte-identical to HEAD and `git diff -U0 -- KANBAN.md KANBAN.html` must show
**only** the two added bullets. Anything else is a stop-and-report.

**V6. `docs/GLOSSARY.md` untouched.** `git diff --stat -- docs/GLOSSARY.md` still reads exactly
`1 insertion(+), 1 deletion(-)` — the concurrent session's `AppConfig` hunk, unchanged. If this pass
changed it, something ran `build_glossary_md.py`.

**V7. Citation gate green, and the new citations counted.**
`uv run python scripts/check_citations.py --check` exits 0. Baseline this pass: `OK: 979 citations
resolve (814 in 442 .py files, **165** in KANBAN.md)`. A drop in the `.py` figure would mean the
comment edit broke something it should not have touched.

> **Corrected at final verification (`### C3`), by the author of the wrong figure.** This row
> originally predicted **980 / 166** on the premise that the card-53 bullet adds "exactly one
> `path::Symbol` citation". It adds **two** —
> `tests/test_scalars.py::test_package_import_does_not_emit_strawberry_deprecation_warning` and
> `tests/auth/test_mutations.py::_auth_free_subprocess` — so the correct expectation is
> **981 / 167**. Measured independently at final verification: `OK: 981 citations resolve (814 in
> 442 .py files, 167 in KANBAN.md)`, exit 0, with the `.py` half unmoved at 814 in 442 files. The
> baseline figure (979 / 165) was right; only the predicted delta was wrong. Worker 2 measured the
> real value, reported the deviation loudly and did **not** bend the pinned bytes to fit the
> prediction, which is the correct handling of a plan figure a measurement falsifies.

**V8. Django consistency.** `uv run python examples/fakeshop/manage.py check` passes.

**V9. Formatting, scoped.** `uv run ruff format tests/auth/test_sessions.py` and
`uv run ruff check --fix tests/auth/test_sessions.py` — **named paths only, never a bare `.`**,
which on this tree would rewrite another session's files. Then `git status --short`: the only paths
that may be **newly** modified relative to the baseline below are `tests/auth/test_sessions.py`,
`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, this artifact, and Worker 2's own memory
file. Everything already dirty at the baseline — this cycle's seven uncommitted files included —
must have an unchanged diffstat afterwards. Anything else is a **stop-and-report, never a revert**.

### Implementation discretion items

Assessed and decided as Worker 2's:

- The exact shape of the ORM script (a single file piped into `manage.py shell`, one script per card
  or one for both). **Constraint, not discretion:** use a script file piped in, never
  `shell -c '<single-quoted>'` — the pinned bullet texts contain apostrophes, which that form
  mangles into the render.
- Whether the marker-absence asserts of V3 run in the same script as the creates or as a separate
  read-only pass first.
- The scratch path used for V2's HEAD copy, provided it is outside the repository.

Not discretion, and not negotiable: the replacement comment bytes, the two bullet texts, the two
`order` values, and the ban on running `build_glossary_md.py`.

### Dispatched findings checklist

Boxes stay `- [ ]` at planning. Worker 2 ticks **only** a box whose contract actually landed in its
diff, and states any deferral in the build report rather than ticking. Worker 1 audits every tick at
final verification.

- [x] Catalog entry **4** — `tests/auth/test_sessions.py:465` `# Exception containment: hostile scope / session / lock (hunt 0_0_14)` replaced by the pinned bytes, parenthetical dropped as pure provenance, head clause unchanged.
- [x] Catalog entry **4** — `tests/auth/test_sessions.py:720` `# Revision guards: hostile __class__ and hostile transport.value (hunt 0_0_14 rev)` replaced by the pinned bytes; the provenance **head** "Revision guards" replaced by the block's invariant, not only the parenthetical dropped.
- [x] Catalog entry **4** — `hunt` and `Revision` both measure **0** occurrences in that file afterwards (V1), and the diff is proved comment-only by AST identity against HEAD behind a `DIVERGES` control (V2).
- [x] Catalog entry **1** — new `Scope` `CardItem` on `Card.objects.get(number=53)` at `order=64`, carrying the pinned text verbatim, written through the Django ORM. (**"the pinned text" now means Step 2's block *as amended by* the three review pins in `#### M1` / `#### L1`** — Step 2 carries a SUPERSEDED banner; the tick stands, and the reconstruction proving the row is exactly that composition is in `### Final verification` V10.)
- [x] Catalog entry **2** — new `Scope` `CardItem` on `Card.objects.get(number=56)` at `order=91`, carrying the pinned text verbatim, written through the Django ORM.
- [x] Both exports regenerated, `--check` clean on both, second-regenerate byte-stable, and `git diff -U0 -- KANBAN.md KANBAN.html` showing only the two added bullets (V4, V5).
- [x] `docs/GLOSSARY.md` untouched and `scripts/build_glossary_md.py` never run (V6); `check_citations.py` green at 981 / 167 (V7 — **figure corrected at final verification from the plan's wrong prediction of 980 / 166; the tick stands, see `### C3`**); `manage.py check` passes (V8).

### Explicitly out of scope — plan no work for these

- **Catalog entry 3** (`spec-042 Revision N` ×5 in `tests/middleware/test_debug_toolbar.py`). All
  five citations resolve; see `### C2`. **Home nothing; touch nothing.**
- **Catalog entry 5** (`Revision N P<n>` ×5 in `examples/fakeshop/test_query/test_library_api.py`).
  Already homed on `TODO-ALPHA-056-0.0.17` at `KANBAN.md:623`. That file belongs to the live
  concurrent `spec-050` session: **do not open it.**
- **Catalog entries 6, 7 and the whole of Block B (8-12).** Correctly closed or correctly left
  conditional. No action.
- **Any spec or rationale-companion byte.** See `### Verified: no spec edit is owed`.
- **`docs/GLOSSARY.md`, `docs/TREE.md`, `docs/README.md`, `README.md`, `TODAY.md`, `GOAL.md`,
  `CHANGELOG.md`**, and every prior `bld-040-*` artifact — closed records; corrections of record go
  in **this** artifact instead.
- **Closeout.** The fence amendment adds card rows. It closes no card, moves no card status, bumps
  no version.

### Baseline-dirty, attributed by diff content ([`AGENTS.md`][agents] rule 34)

Re-measured at `d3b91c8d` this pass, because **the dispatch's do-not-touch list is stale in both
directions** and a misattributed dirty file outranks a wrong count — this cycle has already had one
review paragraph attribute two of its own files to the other session, which would have dropped two
landed fixes at staging. Attribution is by **diff content**, not by which session touched what.

**This cycle's own uncommitted work — dirty, but ours, and not to be reverted or re-fixed either.**
Seven tracked files, each confirmed carrying `040`-shaped hunks (`D-N<n>` comments, the
`bind_mutations` / `bind_form_mutations` / `bind_write_declarations` rename sweep, the `Revision-7`
marker removal, auth test rows, the spec reconciliation):
`django_strawberry_framework/auth/mutations.py` (+11/-4),
`django_strawberry_framework/mutations/resolvers.py` (+6/-6),
`django_strawberry_framework/mutations/sets.py` (+7/-7),
`docs/SPECS/spec-040-auth_mutations-0_0_13.md` (+693/-876), `tests/auth/test_mutations.py`
(+275/-64), `tests/auth/test_queries.py` (+86/-7),
`examples/fakeshop/test_query/test_auth_api.py` (+6/-6) — plus the untracked rationale companion,
the build plan, and the nine `docs/builder/bld-040-*` artifacts. **This slice changes none of
them**; only `tests/auth/test_sessions.py` (currently clean) joins the set.

**The concurrent `spec-050` session's — never edit, never revert:**
`django_strawberry_framework/list_field.py`, `django_strawberry_framework/orders/sets.py`,
`django_strawberry_framework/utils/querysets.py`, `docs/GLOSSARY.md`,
`docs/builder/bld-final.md`, `docs/builder/bld-slice-3-sql_and_unit_contracts.md`,
`docs/feedback.md`, `docs/spec-050-list_field_arguments-0_0_15.md`,
`examples/fakeshop/test_query/test_list_field_api.py`,
`examples/fakeshop/test_query/test_list_field_async_api.py`,
`examples/fakeshop/test_query/test_multi_db.py`, `tests/orders/test_sets.py`,
`tests/test_list_field.py`, `tests/utils/test_querysets.py`.

**Four files the dispatch lists as dirty are clean at `d3b91c8d`** — `_strawberry_patches.py`,
`resource_policy.py`, `tests/test_graphql_core_patches.py`, `docs/builder/bld-003-final.md`: that
session committed them. **Three it omits are dirty** —
`docs/builder/bld-slice-3-sql_and_unit_contracts.md`, `test_list_field_async_api.py`,
`test_multi_db.py`. Do not open any of them either way; the point of the correction is that the list
must be re-measured, not that the fence moved.

`examples/fakeshop/db.sqlite3` is dirty too, and is the **one** file this slice deliberately writes
on top of a concurrent writer's change: its only delta versus HEAD is a single
`glossary_glossaryterm` body row (the `Django AppConfig` entry), already rendered into the dirty
`docs/GLOSSARY.md`. Apply the two `CardItem` rows **on top** without reverting that state, and hand
the mixed diff to the maintainer — that is [`BUILD.md`][build-md] `### Tracked binary / generated
files` verbatim.

### Files this pass wrote

- `docs/builder/bld-040-slice-7-deferral_routing.md` (this file).
- `docs/builder/worker-memory/worker-1-040.md` (appended; consolidated first, at the cap).
- `docs/shadow/helper-inventory-040-slice7.md` — **disclosed**: outside the dispatch's writable list,
  written because [`worker-1.md`][worker-1] `### Package-wide helper inventory before helper
  planning` makes the refresh mandatory for every planning pass. `docs/shadow/` is gitignored
  regenerable scratch (`.gitignore:174`), the stem is unique to this slice so it can collide with no
  other cycle's overviews, and nothing tracked changed.

### Notes for Worker 3

- The `.py` half is comment-only. Review it as prose against
  [`START.md`][start] `## Style Rio cares about`: does each replacement line state an invariant and
  nothing about how the change came to be? The judgement calls are recorded above as (a) and (b);
  disagree with the reasoning if it is wrong, but note the head at `:720` was decided with the
  eight-test block read in full, not assumed.
- The board half has no code to review. Its review surface is
  [`ARTIFACT.md`][artifact-md] `### Documentation / release sanity`: the bullet texts against this
  plan's pinned blocks **character-for-character by `diff`**, the rendered rows appearing exactly
  once in the target card's `Scope` section, and the `KANBAN.md` / `KANBAN.html` diff containing
  nothing else.
- Two figures in the bullets are re-derivable and worth re-deriving rather than reading: the
  subprocess population (`### C1` — the dispatch's own figure was wrong in its subject) and the
  `is_active`-absent reading of the glossary entry.

### Notes for Worker 1 (spec reconciliation)

No spec gap, conflict or unstated assumption surfaced. The one thing a later pass should know:
`bld-040-final.md` entry 3's misclassification (`### C2`) is corrected **here only**, because that
file is a closed record outside the fence. A reader who reaches the catalog without this artifact
will still read the wrong classification.

---

## Build report (Worker 2)

Built at `HEAD = d3b91c8d`, re-verified at the start of this pass (`git log --oneline -1` →
`d3b91c8d fix(spec-050): close the second implementation review and record the green gate`), so the
plan's baseline still holds. `tests/auth/test_sessions.py` was **clean** in `git status --short`
before the edit and `cmp` against `git show HEAD:tests/auth/test_sessions.py` confirmed it
byte-identical, which is why its diff below is this pass's alone.

### Files touched

Grounded in `git status --short`, not memory. Four paths are **newly** modified relative to the
plan's baseline; everything else in `git status` was already dirty and is untouched (see
`### Churn classification`).

- `tests/auth/test_sessions.py` — 2 comment lines replaced (`2 insertions(+), 2 deletions(-)`), the
  pinned bytes of Step 1 carried verbatim. Nothing else in the file moved.
- `examples/fakeshop/db.sqlite3` — two `kanban_carditem` rows created through the Django ORM
  (`pk=1624` on card 53 `order=64`; `pk=1625` on card 56 `order=91`), each with its `post_save`
  `kanban_uuidmodel` side-row. Written **on top** of the concurrent session's single
  `glossary_glossaryterm` row without reverting it.
- `KANBAN.md` — regenerated: `2 insertions(+), 0 deletions(-)`, the two new bullets.
- `KANBAN.html` — regenerated: the one-line `window.KANBAN_DATA` block, `1 insertion(+), 1
  deletion(-)`.
- `docs/builder/bld-040-slice-7-deferral_routing.md` — this report, the seven checklist ticks, and
  `Status: built`. No prior section rewritten.
- `docs/builder/worker-memory/worker-2-040.md` — appended (gitignored).

`docs/GLOSSARY.md` was **not** touched and `scripts/build_glossary_md.py` was **not** run.

### Tests added or updated

**None, per the plan** — the `.py` change is comment-only and the board change is data in the
example project's docs-as-data app. No temp tests were written.

The plan's optional sanity run was taken: `uv run pytest tests/auth/test_sessions.py --no-cov -n0 -q`
→ **53 passed**. It confirms the module still imports and collects; it is not evidence about the
comment text, which V2 owns.

### Validation run

Every figure below was measured this pass, with the population named.

- `uv run ruff format tests/auth/test_sessions.py` → `1 file left unchanged`. **Pass.**
- `uv run ruff check --fix tests/auth/test_sessions.py` → `All checks passed!`. **Pass.** Named path
  only, never a bare `.`.
- `uv run python scripts/check_trailing_commas.py --check tests/auth/test_sessions.py KANBAN.md
  docs/builder/bld-040-slice-7-deferral_routing.md` → exit 0 (this artifact reports
  `excluded from the source-layout rules -- not checked`, which is the per-cycle-scratch exemption).
- `uv run python scripts/check_kanban_anchors.py` → `OK: 76 card anchors are unique, none collides
  with the 146 glossary anchors, and the KANBAN.md render carries no duplicate id.` **Pass.**
- `git status --short` after both ruff invocations → see `### Churn classification`. No unexpected
  path, nothing reverted.

**V1 — provenance retired to zero, in the file's own vocabulary.** Counted with
`grep -o … | wc -l` (occurrences, never `grep -c`, which counts lines) over
`tests/auth/test_sessions.py`: `hunt` **2 → 0**; `Revision` **1 → 0**. Positive control that the
instrument runs at all, same file, same command shape: `session` = **131** before and after. Also
re-confirmed before editing: `spec-` = **0** occurrences, so neither line was a spec decision
pointer.

**V2 — the inverse proof: executable identity against HEAD, behind a control that can fail.**
`ast.dump(ast.parse(...))` of the worktree file against `git show HEAD:tests/auth/test_sessions.py`
written to a scratch path **outside** the repo
(`<scratchpad>/test_sessions.HEAD.py`) → **`IDENTICAL`**. Comments are absent from the AST, so this
proves the diff is comment-only. Control, same comparator, same pass, over a file the concurrent
session changed behaviourally — `django_strawberry_framework/list_field.py` against
`git show HEAD:django_strawberry_framework/list_field.py` → **`DIVERGES`**. No `git stash` /
`checkout` / `restore` was used, in this step or any other.

**V3 — board rows landed once, not twice.** Both inserts ran behind marker-absence asserts in one
ORM script (`CardItem` text containing `subprocess-isolation idiom is spelled inline` for card 53,
`still carries the unqualified privilege framing` for card 56), plus an assert that the target
`order` was free; every precondition was asserted for **both** cards before either was written.
Read-only pre-check, then post-create re-read:

| Card | Title | Status / target | `scope` items before → after | `max(order)` before → after | marker hits after |
|---|---|---|---|---|---|
| 53 | `Boundary hardening and system-wide DRY squeeze` | `todo` / `0.0.15` | 64 → **65** | 63 → **64** | 1 |
| 56 | `Alpha documentation-debt discharge` | `todo` / `0.0.17` | 91 → **92** | 90 → **91** | 1 |

`Section.objects.get(key="scope")` has label `Scope`. Both rows' `post_save` side-rows were asserted
present at create time by reading `item.uuid.id` → `0cfdc244-e550-4d91-a31d-4e23f64829fe` (card 53)
and `332e2b73-6549-4666-91a8-e2a5000b95da` (card 56). Written through
`uv run python examples/fakeshop/manage.py shell < <script>` — a script file, never
`shell -c '<single-quoted>'`, because both bullets contain apostrophes.

**Bullet text carried verbatim, and proved so.** The two pinned strings were **extracted
programmatically from this artifact's own Step 2 / Step 3 fenced blocks** rather than retyped, so a
transcription error was not available to make: each was asserted single-line and ASCII before
insert. Postcondition, after the render: the two added `KANBAN.md` bullet lines (`+- ` prefix
stripped) `diff` **clean** against the two pinned blocks, character-for-character, 2 lines each side.
Control that the comparison can fail: perturbing one token (`Measured` → `MEASURED`) in the pinned
copy makes the same `diff` report a difference.

**V4 — both exports fresh, and stable under a second regenerate.**
`uv run python scripts/build_kanban_md.py --check` and `… build_kanban_html.py --check` both exit
**0** after the first regenerate. Second regenerate, then `shasum -a 256` across the two runs:

| File | sha256 after regenerate 1 | after regenerate 2 |
|---|---|---|
| `KANBAN.md` | `5babfea37615b823…d69d3c78` | identical |
| `KANBAN.html` | `08cddbaf13138516…0e93e73a` | identical |

**V5 — the export diff contains only the two new bullets.** Baseline re-measured before any edit:
both `--check`s exit 0 and `git status --short -- KANBAN.md KANBAN.html` returned **nothing**.
After: `git diff --stat` → `KANBAN.md | 2 ++` (2 insertions, 0 deletions) and `KANBAN.html | 2 +-`
(the single-line data block). The `KANBAN.html` payload was compared **structurally**, not by eye:
parsing `window.KANBAN_DATA` from both sides and keying every card item by `(card title, item uuid)`
gives **2 added, 0 removed, 0 changed**, and removing exactly those two items makes the two payloads
**equal** — so nothing else in the board moved.

*Instrument note, because it read like a clean result:* the first attempt to count changed export
lines used `git diff -U0 -- KANBAN.md | grep -c '^[+-][^+-]'` and printed **0**. The pattern is
wrong, not the diff — a board bullet's added line begins `+- `, which `[^+-]` excludes. A count of
0 changed lines on a file whose `--stat` says `2 ++` is the giveaway; the structural comparison above
is what the claim actually rests on.

**V6 — `docs/GLOSSARY.md` untouched.** `git diff --stat -- docs/GLOSSARY.md` reads
`1 insertion(+), 1 deletion(-)` — identical to the baseline reading taken before any edit this pass,
i.e. the concurrent session's `AppConfig` hunk, unchanged. `scripts/build_glossary_md.py` was never
invoked.

**V7 — citation gate green; the plan's predicted arithmetic was one short, and the deviation is
mine to report, not to absorb.** `uv run python scripts/check_citations.py --check` exits 0 and
reads `OK: 981 citations resolve (814 in 442 .py files, 167 in KANBAN.md)`. The plan predicted
**980 / 166** on the premise that the card-53 bullet adds "exactly one `path::Symbol` citation". It
adds **two**: `tests/test_scalars.py::test_package_import_does_not_emit_strawberry_deprecation_warning`
and `tests/auth/test_mutations.py::_auth_free_subprocess`, both measured out of the pinned text this
pass (`grep -o` over the extracted bullet: card 53 = **2**, card 56 = **0**). So the correct expected
reading is 981 / 167, the baseline having been 979 / 165 — re-measured this pass before any edit,
and matching the plan's stated baseline exactly. Both new citations resolve (the gate is green) and
the `.py` half is **unchanged at 814 in 442 files**, which is the reading that would have moved had
the comment edit damaged anything. The pinned bytes were **not** altered to fit the prediction.

**V8 — Django consistency.** `uv run python examples/fakeshop/manage.py check` →
`System check identified no issues (0 silenced).` **Pass.**

**V9 — formatting and churn.** Covered by the two scoped ruff runs above and
`### Churn classification` below.

### Churn classification

`git status --short` after every write and both ruff invocations. **Newly** modified relative to the
plan's baseline: `tests/auth/test_sessions.py`, `KANBAN.md`, `KANBAN.html`, and this artifact plus
the gitignored memory file. `examples/fakeshop/db.sqlite3` was already dirty and is the one file this
slice deliberately writes on top of a concurrent writer.

Every other path in `git status` was dirty at the baseline and has an **unchanged** diffstat: this
cycle's own seven uncommitted files (`django_strawberry_framework/auth/mutations.py`,
`mutations/resolvers.py`, `mutations/sets.py`, `docs/SPECS/spec-040-auth_mutations-0_0_13.md`,
`tests/auth/test_mutations.py`, `tests/auth/test_queries.py`,
`examples/fakeshop/test_query/test_auth_api.py`) and the concurrent `spec-050` session's thirteen.
**Nothing was reverted and nothing outside the writable list was opened.**

**The DB delta was proved by content, not by file size.** `sqlite3 .dump | sort` of the worktree DB
against the same dump of `git show HEAD:examples/fakeshop/db.sqlite3` (written to a scratch path
outside the repo): **8 differing lines**, every one accounted for —

- `glossary_glossaryterm` row `448` (`Django AppConfig`), one line each side: the concurrent
  session's, present before this pass and left exactly as found;
- `kanban_carditem` `1624` and `1625`: this pass's two bullets;
- `kanban_uuidmodel` ×2: their `post_save` side-rows;
- `sqlite_sequence` for `kanban_carditem`, `1623 → 1625`.

No other `kanban_*` row moved, which is the same fact the structural `KANBAN.html` comparison
reports from the other end.

### Failability proofs

**None; this pass introduced no new boundary.** The plan declares **0** new boundaries, guards,
gates or rejection paths, and the diff bears it out: two comment lines and two data rows, no
executable change anywhere. The obligation inverts rather than disappearing, and V2 discharges it —
AST identity against HEAD proving the `.py` diff is comment-only, behind a `DIVERGES` control on a
file that really did change. A mutation-based proof is **not available** for a comment-only diff: a
comment token cannot move a comment-stripped digest, so the loop would measure nothing.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **The pinned bullet texts were extracted from this artifact, not retyped.** The plan's Step 2 /
  Step 3 fenced blocks were read out of the file programmatically and written to scratch files that
  the ORM script then read. The plan calls the bullet texts non-negotiable, and this cycle's own
  record has a paraphrase-of-a-pin defect in it; extracting removes the failure mode instead of
  promising to avoid it. Each extracted string was asserted single-line and ASCII before use.
- **One ORM script, two cards, all asserts before any write.** The plan left this to discretion.
  Doing both cards in one script with the full precondition set asserted up front means a
  half-applied state is not reachable: a failed assert aborts having written nothing.
  (`START.md` #"Enumerate, never grep-count, before writing".)
- **Same shape for the comment edit**: both `From` lines were asserted to occur exactly once and
  both `To` lines to occur zero times before either replacement was applied.
- **Scratch paths are all outside the repository**, under the session scratchpad — the HEAD copies of
  `tests/auth/test_sessions.py`, `django_strawberry_framework/list_field.py`, `KANBAN.html` and
  `examples/fakeshop/db.sqlite3`, the two extracted bullet files, and the two dumps.

### Notes for Worker 3

- **The V7 deviation is the one thing in this pass that did not land as planned**, and it is
  arithmetic in the plan's prediction, not a change to the deliverable: the card-53 bullet carries
  **two** `path::Symbol` citations, so the gate reads 981 / 167 rather than the predicted 980 / 166.
  Re-derive it (`grep -o '[A-Za-z0-9_./-]*\.py::[A-Za-z_][A-Za-z0-9_.]*'` over the pinned block)
  rather than reading it here. The seventh checklist box is ticked on that basis: its substantive
  contract — glossary untouched, gate green, no `.py` citation regression, `manage.py check` clean —
  landed in full, and the number it quotes was a prediction the plan made about the measurement.
  Un-tick it if you read the box text as pinning the figure itself.
- **The `.py` half is comment-only and provably so** (V2). Review it as prose: both lines now state
  the invariant of the block below them and nothing about how the change came to be.
- **The board half's review surface is `### Documentation / release sanity`.** The verbatim check and
  the "renders exactly once" check are both already performed above with their controls; the cheapest
  independent re-derivation is the structural `window.KANBAN_DATA` comparison, which needs no trust in
  any count.
- **Instrument warning worth carrying:** `grep -c '^[+-][^+-]'` over a board diff reports **0**
  because bullet lines start with `-`. Recorded under V5.
- No temp tests exist for this slice; none are needed.

### Notes for Worker 1 (spec reconciliation)

- **No spec gap, conflict or unstated assumption surfaced.** No spec byte moved this pass.
- **One plan figure is falsified and the artifact is the only place it is corrected:** the plan's V7
  expected `check_citations.py` reading of **980 / 166** is wrong; the correct expectation for this
  diff is **981 / 167**, because the card-53 pinned bullet carries two `path::Symbol` citations, not
  one. The plan's baseline figure (979 / 165) was right. Nothing else in V7 changed.
- The plan's own `### Notes for Worker 1` point stands: `bld-040-final.md` entry 3's
  misclassification is corrected in this artifact only, since that file is a closed record outside
  the fence.


---

## Review (Worker 3)

Reviewed at `HEAD = d3b91c8d` (`git log --oneline -1`, unchanged from the plan's and the build
report's baseline; `git reflog -10` shows only the concurrent session's commits, no `reset`, no
`checkout`, no new stash entry — the two entries in `git stash list` are dated 2026-06-20 and
`new-037` and predate this cycle). Every figure below was **re-derived this pass**, with the
population named and, where the reading is a zero, a positive control beside it. Nothing in the
build report was accepted on its own record.

### High:

None.

### Medium:

#### M1. The card-53 bullet ships two wrong figures about the duplication population the card exists to consolidate

Both errors have one root cause: `tests/filters/test_sets.py`'s child script was never read, only
counted. The bullet is otherwise accurate — every other figure in it re-derived clean (see
`### What looks solid`) — which is what makes these two dangerous: they sit inside a row whose
surrounding sentences are individually verifiable, and the card's open design question (b) turns on
exactly this data.

**(i) `only four of them configure Django at all` — five of the six do.** Measured over the six
files the bullet names, counting occurrences with `grep -o … | wc -l` (never `grep -c`):

| File | `django.setup()` occurrences | `DJANGO_SETTINGS_MODULE` | configures Django in the child |
|---|---|---|---|
| `tests/auth/test_mutations.py` | 2 (1 code + 1 docstring) | 2 | yes |
| `tests/auth/test_sessions.py` | 1 | 1 | yes |
| `tests/base/test_init.py` | **0** | **0** | **no** |
| `tests/filters/test_finalizer.py` | 1 | 1 | yes |
| `tests/filters/test_sets.py` | 1 | 1 | **yes** |
| `tests/orders/test_inputs.py` | 1 | 1 | yes |

Positive control that the instrument can return zero where it should: `tests/test_scalars.py`
(the warnings probe, which genuinely configures no Django) reads **0**. Read at source, not
inferred from the count: `tests/filters/test_sets.py`'s `child` local is
`"import os, sys\n" … "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')\n"
"import django\n" "django.setup()\n"`, i.e. the same fakeshop-`sys.path` +
`DJANGO_SETTINGS_MODULE` + `django.setup()` prologue the bullet attributes to the helper.

**(ii) The re-speller inventory names three files; there are four.** `tests/filters/test_sets.py`
is a fourth inline re-spelling of the same prologue and the bullet omits it, which understates the
duplication the card must remove by 25%. The omission also breaks the sentence's arithmetic:
`three of them near-identically and one compressed` attributes **four** items to a **three**-item
list. Counting the helper, the true tally is five spellings of one prologue — helper +
`test_finalizer` + `test_inputs` near-identical, `test_sessions` compressed onto
`import django, os, sys;`, `filters/test_sets` newline-joined inside a `child` local.

**Why it matters, and why it is not cosmetic.** Design question (b) — "whether ONE contract can
serve all three probe kinds" — is answered from the Django-configuring split. At four-of-six a
reader concludes the import-isolation kind is itself split down the middle and probably needs two
helpers; at five-of-six the kind is near-uniform and one helper with an opt-out for
`tests/base/test_init.py` is the obvious shape. The figure changes the answer, and it outlives this
cycle on a `TODO` card nobody will re-measure.

**Recommended change** — three anchored replacements in `CardItem` `pk=1624`'s text, each anchor
verified to occur **exactly once** in `KANBAN.md` this pass. Through the Django ORM, then both
render scripts; ASCII only; the row stays one line. None of the three adds or removes a
`path::Symbol`, so the citation gate reading does not move.

1. FROM `and only four of them configure Django at all`
   TO `and five of the six configure Django in the child (only ``tests/base/test_init.py`` does not)`
2. FROM `` and `tests/auth/test_sessions.py`, `tests/filters/test_finalizer.py` and `tests/orders/test_inputs.py` each re-spell that same prologue inline, three of them near-identically and one compressed onto a single `import django, os, sys;` clause. ``
   TO `` and `tests/auth/test_sessions.py`, `tests/filters/test_finalizer.py`, `tests/filters/test_sets.py` and `tests/orders/test_inputs.py` each re-spell that same prologue inline - `tests/filters/test_finalizer.py` and `tests/orders/test_inputs.py` near-identically to the helper, `tests/auth/test_sessions.py` compressed onto a single `import django, os, sys;` clause, and `tests/filters/test_sets.py` newline-joined inside a `child` local - so the helper plus four inline re-spellings is five spellings of one prologue. ``
3. (L1 below, same edit.)

Postcondition to re-measure after the edit, not to assert: `grep -o 'only four of them' KANBAN.md`
→ **0**, with `grep -o 'five of the six' KANBAN.md` → **1** as the control that the file was
actually rewritten; both `--check`s exit 0; the `KANBAN.md` diff is 1 changed line, not 2 added;
`check_citations.py` still reads 981 / 167.

### Low:

#### L1. `that cycle had already collapsed the two copies inside tests/auth/test_mutations.py` — at HEAD there was one copy, not two

Re-derived read-only against HEAD (`git show HEAD:tests/auth/test_mutations.py` into a scratch path
outside the repo; no `stash` / `checkout` / `restore`): `sys.executable` = **1** occurrence,
`subprocess.run(` = **1**, `django.setup()` = **1**. The worktree diff confirms the shape — one
inline block removed (`-` hunk at the old `test_registry_clear_does_not_import_the_auth_subsystem`),
`_auth_free_subprocess` added, and **two** callers, one of which (`driver + _AUTH_UNIMPORTED_ASSERT`)
is new this cycle. So the cycle extracted a helper out of one pre-existing copy and routed a new
second probe through it; it did not merge two existing duplicates. A future reader takes the
sentence as evidence the file was a two-copy site, which HEAD falsifies.

**Recommended change**, folded into M1's single ORM edit (anchor verified unique):
FROM `` that cycle had already collapsed the two copies inside `tests/auth/test_mutations.py` into the file-local helper named above. ``
TO `` that cycle had already extracted the file-local helper named above out of the file's one pre-existing inline copy, so its second probe rides the helper instead of adding a fifth re-spelling. ``

#### L2. Checklist box 7 is ticked against a figure the pass falsified

The box reads `check_citations.py` green at **980 / 166**; the gate reads **981 / 167**. The
substantive contract in that box all landed (glossary untouched, `build_glossary_md.py` never run,
gate green, `.py` half unmoved at 814 in 442 files, `manage.py check` clean), and Worker 2 reported
the deviation loudly rather than absorbing it or bending the pinned bytes to fit — which is the
correct handling. The residue is that a `- [x]` now stands beside a false number in a document the
maintainer reads. **Not `revision-needed` on its own** and no work for Worker 2: routed to Worker 1
under `### Notes for Worker 1` as the tick-auditor and the plan section's owner.

#### L3. The new board row cites a symbol that does not exist at HEAD

`tests/auth/test_mutations.py::_auth_free_subprocess` resolves today only because this cycle's
Slice 6 work is in the working tree; `git show HEAD:tests/auth/test_mutations.py | grep -c
'_auth_free_subprocess'` → **0**. `check_citations.py` is hook 6 and runs **whole-tree**, so a
commit that ships `KANBAN.md` + `examples/fakeshop/db.sqlite3` without
`tests/auth/test_mutations.py` turns the gate red for every later commit by anyone, including the
concurrent session. Nothing to fix in the diff — a staging constraint for the maintainer, recorded
so it is not discovered at the hook.

### DRY findings

- **The slice authors no code, so it introduces no duplication.** The `.py` half is two comment
  lines (AST-identical to HEAD, proved below); the board half is two data rows.
- **No existence challenge is available or owed.** No helper, registry, token or indirection layer
  is created. The one abstraction in play — a shared subprocess-probe helper — is the *subject* of
  the card-53 row, deliberately left undecided, and M1 is precisely a defect in the evidence that
  decision will be made from.
- **No duplicate homing.** Card 53's `Scope` carries exactly **1** row mentioning `subprocess` /
  `sys.executable` (the new one) and card 56's carries exactly **1** matching the new glossary
  marker, measured with `grep -o … | wc -l` over the two sections' line ranges. Catalog entry 5 was
  correctly left alone: `KANBAN.md` already homes it on card 56.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list
are unchanged; no public export moved.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

- **The two pinned comment lines landed byte-for-byte.** Extracted the plan's `| 465 |` / `| 720 |`
  table rows programmatically and compared, never by eye: each `From` string equals
  `git show HEAD:tests/auth/test_sessions.py`'s line and each `To` string equals the worktree's,
  all four comparisons `True`. Lengths 55 and 70, both inside the 99 limit (file max line length is
  under 99 everywhere: **0** lines over 99, **0** over 110). File is ASCII-only — **0** bytes > 127,
  with a 3-byte em dash as the control proving the scan counts what it claims. The eight `# ---`
  rule banners are all still 77 characters and still paired, and the surrounding blank lines are
  untouched (they appear only as context in `git diff`, confirmed on the raw bytes via `od -c`).
  `ruff format --check` → `1 file already formatted`; `ruff check` → `All checks passed!`.
- **V1 re-derived.** `grep -o … | wc -l` over `tests/auth/test_sessions.py`: `hunt` **2 → 0**,
  `Revision` **1 → 0**, `spec-` **0** both sides. Positive control, same instrument, same file:
  `session` = **131** at HEAD and **131** in the worktree, so a zero here is a real zero and not a
  grep that ran on nothing.
- **The two bullets landed verbatim.** Both fenced `````text````` blocks were extracted from this
  artifact by fence position and `diff`ed against the two added `KANBAN.md` lines with the `- `
  prefix stripped: both **exact matches**, 3,652 and 2,268 characters, single-line, ASCII. Control:
  the same comparison against a one-token perturbation of block 0 returns no match.
- **Homed on the right cards, exactly once each.** `KANBAN.md:382` sits inside
  `TODO-ALPHA-053-0.0.15`'s `#### Scope` (opens at `:316`) and `KANBAN.md:657` inside
  `TODO-ALPHA-056-0.0.17`'s (opens at `:564`). Scope bullet counts: card 53 **64 → 65**, card 56
  **91 → 92**, each new row last in its section — matching the build report's V3 table exactly.
  Distinctive-substring occurrence counts in `KANBAN.md`: **1** and **1**.
- **Exports honest, re-derived independently.** `build_kanban_md.py --check` and
  `build_kanban_html.py --check` both exit **0**. Byte-stability proved without writing to the repo:
  two fresh `--md` renders to scratch and two `--html` renders over scratch copies all hash
  `5babfea37615b8234f06b7f99076b2a8cfd979609462e4773a5c7c59d69d3c78` /
  `08cddbaf13138516898696a334596e0b6809063aaa23926f8cb9984b0e93e73a`, identical to the worktree
  files and to the build report's recorded digests. `git status --short -- KANBAN.md KANBAN.html`
  was unchanged by my runs.
- **The `KANBAN.html` payload moved by exactly two nodes.** Parsed `window.KANBAN_DATA` from
  `git show HEAD:KANBAN.html` and from the worktree and keyed every node by its `uuid.id`: HEAD
  **3,718** nodes, worktree **3,720**, **2 added / 0 removed / 0 changed**, and deleting exactly
  those two makes the payloads equal. The two added ids are `0cfdc244-e550-4d91-a31d-4e23f64829fe`
  (`id: 1624, order: 64`) and `332e2b73-6549-4666-91a8-e2a5000b95da` (`id: 1625, order: 91`) — the
  same uuids the build report recorded. Control: perturbing one surviving node makes the equality
  fail. *Instrument note* — my first walker keyed on `uuid` as a string and found **0** nodes on
  both sides, reporting a clean "equal" that measured nothing; `uuid` is a nested `{"id": …}`
  object. The node-count line is what exposed it, which is why it is printed above.
- **The DB delta is exactly 8 lines and every one is accounted for.** `sqlite3 .dump | sort` of the
  worktree DB against the same dump of `git show HEAD:examples/fakeshop/db.sqlite3` (scratch, outside
  the repo): 11,115 → 11,119 lines, `diff` shows **8** `<`/`>` lines — `glossary_glossaryterm` row
  **448** (the concurrent session's `Django AppConfig` body, one line each side), `kanban_carditem`
  **1624** and **1625**, their two `kanban_uuidmodel` side-rows carrying `1624` / `1625`, and
  `sqlite_sequence` for `kanban_carditem` **1623 → 1625**. **No other `kanban_*` row moved.** The
  `post_save` side-rows are real and linked, proved from the other end too: the render's
  `uuid { id }` for both new items resolves to the two uuids above, which a raw-SQL insert could not
  have produced.
- **Fence compliance.** `docs/GLOSSARY.md` diffstat is still exactly `1 insertion(+), 1 deletion(-)`
  and the single hunk is the concurrent session's three-appliers → four-appliers `AppConfig`
  rewrite adding `_graphql_core_patches` — read in full, unrelated to this slice;
  `build_glossary_md.py --check` exits 0 against it. Every one of this cycle's seven baseline-dirty
  files carries the **exact** `--numstat` the plan recorded pre-build
  (`auth/mutations.py` 11/4, `mutations/resolvers.py` 6/6, `mutations/sets.py` 7/7, the spec
  693/876, `tests/auth/test_mutations.py` 275/64, `tests/auth/test_queries.py` 86/7,
  `test_auth_api.py` 6/6), so none moved this pass and **no spec byte changed**. The only newly
  dirty `.py` in the whole tree is `tests/auth/test_sessions.py` at 2/2; every other dirty `.py` is
  the `spec-050` session's. `HEAD` is unmoved, nothing was committed.
- `check_kanban_anchors.py` → `OK: 76 card anchors are unique, none collides with the 146 glossary
  anchors, and the KANBAN.md render carries no duplicate id.` `check_trailing_commas.py --check` on
  the three touched paths → exit 0. `manage.py check` → `System check identified no issues`.

### Declarations audit — hot path, floor, failability

- **Hot path: none.** Agreed, and verified rather than accepted: the `.py` diff is comment-only, so
  nothing executes differently per request, per resolver, per row, per connection or per outbound
  message, and the board rows are data in the example project's docs-as-data app. No number owed.
- **Floor verification: none required.** Agreed. A comment carries no behaviour and the AST-identity
  proof below establishes that as a measurement, not a reading; the render scripts exercise the
  example project's own ORM, not a Django / Strawberry / channels integration seam.
- **Failability: 0 new boundaries, no proof owed — confirmed against the diff in front of me, which
  is the one thing this declaration could have been wrong about.** `git diff -- tests/auth/test_sessions.py`
  is 2 insertions / 2 deletions, both comment lines; **no test row was added, removed, renamed or
  re-parametrized**, so the declaration still holds and there is no boundary to re-run. The
  mandatory independent re-run floor is therefore **empty, legally** — the diff introduces no
  boundary that meets it — and I re-ran no boundary and accepted none on Worker 2's record, because
  there are none to accept.
- **I reproduced the inverse proof independently rather than auditing it.** `ast.dump(ast.parse(…))`
  of `tests/auth/test_sessions.py` against `git show HEAD:tests/auth/test_sessions.py` (scratch,
  outside the repo) → **IDENTICAL**, 69,048 AST characters each side. Control, same comparator, same
  pass, over a file the concurrent session changed behaviourally:
  `django_strawberry_framework/list_field.py` → **DIVERGES** (91,886 vs 87,696). AST identity is
  strictly stronger than the `--collect-only` node-id check this cycle usually reaches for — it
  pins the whole executable content, not just the id set — so I did not run one, and say so rather
  than leaving the absence to be read as an oversight.

### The `:720` wording — the review question the plan asked for, answered against the file

Worker 1 replaced the comment **head** `Revision guards` (not only the parenthetical), leaving `:720`
opening with the same two words as `:465`. Three checks, all against the file:

1. **`Revision guards` really was provenance.** "Revision" names the bug hunt's revision round — the
   same round the dropped `(hunt 0_0_14 rev)` names — not a property of the code. Nothing in the
   block guards a revision and the phrase names no invariant. Replacing it, rather than only
   dropping the parenthetical, is the correct call and the one that actually discharges
   `START.md` #"No process provenance in code or standing prose".
2. **The two headers are genuinely distinguished, and the shape has precedent in this very file.**
   `__class__` as a hostile property occurs at `:727` and `:804` only — both inside the `:720` block
   — and `transport.value` hostility likewise appears nowhere before `:720`, so the distinguishing
   clause is exclusive, not decorative. More to the point, the file already carries two block
   headers sharing a lead token distinguished only by the clause after it: `:58`
   `# classify_transport -- isinstance-first, scope["type"]-second` and `:88`
   `# classify_transport -- channels-absent raises the install hint (soft-dep)`. A reader scrolling
   this file is already reading the clause, not the lead. **No finding.**
3. **It states the invariant its eight rows pin.** Read all eight (`:724`-`:827`, not `:724`-`:816`
   as the dispatch says — the block runs to the end of the file). Six are containment rows: three on
   `classify_transport` with a hostile `__class__` (both `isinstance` branches) and three on
   `require_session` reaching a hostile `transport.value` (raising `value`, hostile `__repr__`,
   hostile `__class__` inside the `isinstance`). The remaining two are the containment machinery's
   own controls — a happy path proving the guard did not swallow the success case, and a row proving
   `require_session` never touches `transport.value` at all on success, i.e. that the containment is
   not paid for on the hot path. Both belong under the head. **No alternative wording to offer.**

### What looks solid

- **Every other figure in both bullets re-derived clean**, each with its population named:
  `sys.executable` **9 occurrences in 8 files** with the file list exact and
  `tests/test_scalars.py` carrying **2**; `:319` read at source as a docstring line inside
  `::test_package_import_does_not_emit_strawberry_deprecation_warning` and `:325` as the call, so
  **8 call sites**; five `tests/` subdirectories plus the root; the first-argument regex returning
  **7** files with `tests/base/test_init.py` excluded because it builds a `cmd` local (read at
  source); **10** files calling `subprocess.run(` with `tests/test_bug_hunt.py` and
  `tests/test_ci_governance.py` invoking `git` (read at source). The dispatch's own "8 files, 9 call
  sites" is wrong in its subject and the plan's `### C1` correction is right.
- **The card-56 bullet is accurate in every claim I could test.** `docs/GLOSSARY.md`'s
  `## Auth mutations` entry: `is_active` **0** occurrences, `unreachable by construction` **1**, the
  quoted sentence present verbatim **1** time, and exactly the four other columns enumerated. The
  corrected two-layer contract matches the spec at `:1130`-`:1141` and `:2048` and the code's
  `django_strawberry_framework/auth/mutations.py` #"_REGISTER_PROTECTED_FIELDS = frozenset" —
  a five-member set. The `DB-generated … never hand-edit` sentence matches the card's other 26
  glossary rows.
- **No parallel live site was left behind.** Swept the tree for the retired framing: `unreachable by
  construction` appears in exactly one standing doc, `docs/GLOSSARY.md`, plus this cycle's own
  artifacts and the new board row. `docs/README.md` #"refuses to auto-expose" already names all five
  columns correctly, and `README.md` / `TODAY.md` carry none of it — so homing the glossary alone is
  the complete fix, not a partial one.
- **The two figures the plan's `### Notes for Worker 3` flagged as worth re-deriving both hold** —
  the subprocess population and the `is_active`-absent reading. It is the third figure, the one the
  notes did not flag, that is wrong.
- **The V5 instrument note is a real finding about a real trap**, correctly disclosed rather than
  quietly replaced: `grep -c '^[+-][^+-]'` over a board diff returns 0 because a bullet's added line
  begins `+- `. Reproduced.
- Worker 2 extracted the pinned bullet texts from the artifact programmatically instead of retyping
  them, ran both inserts behind marker-absence asserts in one all-asserts-first script, and used a
  script file rather than `shell -c` because the bullets carry apostrophes. All three are the shapes
  this cycle's record says get missed.

### Temp test verification

None. No temp test was written this pass and `docs/builder/temp-tests/040-slice-7/` was not created:
every question the review raised was answerable by measurement against the tree, HEAD, and the
rendered exports. Nothing is left resting on a temp test.

### Static helper use

`scripts/review_inspect.py` **not run — skip recorded with its reason.** `BUILD.md`
`### When to run the helper during build` triggers it for Worker 3 on a new `.py` file, a file under
`optimizer/` or `types/`, or 30+/50+ new logic lines. This diff adds **0** lines of logic to **0**
files — it is two comment-line replacements proved AST-identical to HEAD — so no trigger fires and a
shadow overview would describe a file this slice did not change.

### Notes for Worker 1 (spec reconciliation)

- **No spec byte moved and none is owed.** Independently confirmed: the spec's `--numstat` is
  unchanged from the plan's pre-build reading (693/876).
- **L2 is yours, not Worker 2's.** Checklist box 7's text pins `980 / 166`, a prediction this pass
  falsified; the box's substantive contract landed in full. You own both the plan section that
  states the figure and the tick audit. Two clean resolutions: correct the V7 figure and the box
  text in place (you are the plan's author and `BUILD.md` treats a falsified prediction as
  rewritable, unlike a dated observation), or leave both and record the deviation as a one-line
  final-verification note. Either is defensible; leaving a `- [x]` beside an uncorrected false
  number with no note is not.
- **L3 is a staging constraint the maintainer needs before committing**, not a defect: the new
  card-53 row cites `tests/auth/test_mutations.py::_auth_free_subprocess`, which is **absent at
  HEAD**. `KANBAN.md` + `examples/fakeshop/db.sqlite3` must not be committed without
  `tests/auth/test_mutations.py`, or hook 6 goes red whole-tree for everyone.
- The plan's `### C2` correction of `bld-040-final.md` entry 3 stands and I re-derived its core:
  `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md` exists for this spec but
  `spec-042` has no rationale companion, so no rationale move can have stranded its citations.
  Carrying that correction only in this artifact leaves a reader of the catalog with the wrong
  classification; worth one line in the final-verification summary.

### Review outcome

`revision-needed`. One Medium (M1) and one Low (L1) require an edit Worker 3 may not make — both are
`CardItem` text on `pk=1624`, both fixable in a single ORM edit plus one re-render of the two
exports, and both anchored above to substrings verified unique in `KANBAN.md` this pass. L2 and L3
are routed to Worker 1 and the maintainer and need no builder work. Everything else in the slice is
accepted: the two pinned comment lines, the AST-identity inverse proof, the card-56 bullet, the
homing, the exports, the DB delta, and the fence.

---

## Build report (Worker 2, pass 2)

Apply-changes pass after `Status: revision-needed`. `HEAD = d3b91c8d` re-read at the start of this
pass (`git log --oneline -1` → `d3b91c8d fix(spec-050): close the second implementation review and
record the green gate`), unchanged from the plan's, the first build report's and the review's
baseline. **Scope: M1 and L1 only** — three anchored replacements inside one `CardItem`'s `text`,
plus the two renders. No `.py` byte, no spec byte, no `docs/GLOSSARY.md` byte, no `pk=1625` byte.

### M1 / L1 — the figures re-derived before anything was written

The dispatch requires the corrected figures to be re-derived independently rather than carried from
the review, because a wrong count that lands on a `TODO` card outlives the cycle that wrote it.
Measured this pass over the live files with `grep -o … | wc -l` (never `grep -c`, which counts
lines), population named per column:

| File | `django.setup()` | `DJANGO_SETTINGS_MODULE` | `sys.executable` | `subprocess.run(` |
|---|---|---|---|---|
| `tests/auth/test_mutations.py` | 2 | 2 | 1 | 1 |
| `tests/auth/test_sessions.py` | 1 | 1 | 1 | 1 |
| `tests/base/test_init.py` | **0** | **0** | 1 | 1 |
| `tests/filters/test_finalizer.py` | 1 | 1 | 1 | 1 |
| `tests/filters/test_sets.py` | **1** | **1** | 1 | 1 |
| `tests/orders/test_inputs.py` | 1 | 1 | 1 | 1 |
| `tests/rest_framework/test_soft_dependency.py` | 0 | 0 | 1 | 1 |
| `tests/test_scalars.py` | 0 | 0 | **2** | 1 |

**This agrees with Worker 3's M1 table and with Worker 0's re-verification in every cell**, so the
pinned replacement text was carried rather than re-derived into new wording.

Read at source, not inferred from the counts:

- `tests/filters/test_sets.py`'s `child` local is newline-joined and carries the full prologue —
  `"import os, sys\n"`, `sys.path.insert(0, <fakeshop>)`,
  `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')`, `import django`,
  `django.setup()`. So it **does** configure Django in the child: five of the six import-isolation
  files do, and only `tests/base/test_init.py` does not.
- The four inline re-spellings are distinguishable exactly as the replacement says:
  `tests/filters/test_finalizer.py` and `tests/orders/test_inputs.py` reproduce
  `tests/auth/test_mutations.py::_auth_free_subprocess`'s `prologue` clause-for-clause;
  `tests/auth/test_sessions.py` compresses it onto `"import django, os, sys; "`;
  `tests/filters/test_sets.py` newline-joins it inside a `child` local.
- **L1, read-only against HEAD** (`git show HEAD:tests/auth/test_mutations.py` into a scratch path
  **outside** the repo; no `stash` / `checkout` / `restore`): `sys.executable` **1**,
  `subprocess.run(` **1**, `django.setup()` **1**, `_auth_free_subprocess` **0**. Worktree: **1** /
  **1** / **2** / **3**. One pre-existing copy, not two — the cycle extracted the helper out of it
  and routed a newly added second probe through it.
- Positive control that the `django.setup()` instrument can return zero where it should:
  `tests/test_scalars.py` reads **0** while reading **2** for `sys.executable`.

### Files touched

Grounded in `git status --short`. **No path is newly dirty relative to the start of this pass** —
all three were already modified by pass 1; this pass changed their contents, not the dirty set
(36 lines before, 36 lines after, same paths).

- `examples/fakeshop/db.sqlite3` — `CardItem` `pk=1624` (`card=53`, `section='scope'`, `order=64`)
  `.text` updated through the Django ORM, `3652 → 4037` bytes. No `INSERT`, no raw SQL: the row and
  its `kanban_uuidmodel` side-row already existed, and only `text` moved. `pk=1625` re-read after
  the save and unchanged at 2268 bytes.
- `KANBAN.md` — regenerated. Diff **versus the pre-edit worktree state**: exactly **1** line
  replaced (1 `-` / 1 `+`, `3655 → 4040` characters, delta `+385`, matching the DB delta exactly).
- `KANBAN.html` — regenerated. Diff versus pre-edit: the single `window.KANBAN_DATA` line.
- `docs/builder/bld-040-slice-7-deferral_routing.md` — this report and `Status: built`. No prior
  section rewritten; no checklist box touched (see `### Notes for Worker 1`).
- `docs/builder/worker-memory/worker-2-040.md` — appended (gitignored).

`docs/GLOSSARY.md` was **not** touched and `scripts/build_glossary_md.py` was **not** run.

### Tests added or updated

**None.** This pass edits one board row's text and re-renders two generated exports; it touches no
`.py` file, so nothing is testable and the plan's `### Test additions / updates` contract is
unchanged. No temp tests were written.

### Validation run

No `ruff` invocation: this pass modified no `.py` file, so a formatter run would only touch files
outside the pass (and, on this concurrently-written tree, other sessions' work).

- **Three anchors, each exactly once before the write.** `KANBAN.md` counts, `str.count` over the
  whole file: M1-1 `and only four of them configure Django at all` → **1**; M1-2 (the three-file
  re-speller sentence) → **1**; L1 `that cycle had already collapsed the two copies inside …` →
  **1**. The same three asserted `== 1` against `CardItem.text` inside the ORM script, and each
  replacement asserted `== 0` there, **before any write** — a failed assert aborts having written
  nothing.
- **ORM script, piped file, never `shell -c`.**
  `uv run python examples/fakeshop/manage.py shell < <scratch>/edit_1624.py` — the replacement text
  contains an apostrophe (`the file's one pre-existing inline copy`), which `shell -c '<single
  quoted>'` mangles into the render. Post-write asserts inside the same script: re-read equals the
  intended text, `reread.uuid.id` non-empty (the `post_save` side-row), no `\n`/`\r`, all bytes
  `< 128`, no literal `{{card_ref`, and `text.count("::")` **unchanged at 3** across the edit.
- **The replacement bytes were extracted from the review section programmatically, not retyped** —
  the artifact's own `FROM` / `TO` lines parsed and their markdown code-span delimiters stripped —
  so transcription is not a failure mode that exists here. One delimiter judgement is recorded under
  `### Implementation notes`.
- `uv run python scripts/build_kanban_md.py` then `… build_kanban_html.py` — both wrote (74 cards +
  15 board docs; 76 cards, 15 board docs, 11 lookup arrays).
- **Second-regenerate byte-stability**, the check `git diff` cannot make (it shows the cumulative
  HEAD diff, not stability): both scripts run a second time, `shasum -a 256` identical across the
  two runs — `KANBAN.md` `0f926bde…8616`, `KANBAN.html` `99dfc3c7…4f8f`.
- `uv run python scripts/build_kanban_md.py --check` → `is up to date.`, **exit 0**.
  `uv run python scripts/build_kanban_html.py --check` → `is up to date.`, **exit 0**.
- **The `KANBAN.html` diff is structurally confined to one item** — the instrument my own pass-1
  report flagged (`grep -c '^[+-][^+-]'` reads 0 on a board diff, because a bullet line begins
  `+- `) is not used. Instead `window.KANBAN_DATA` was parsed on both sides and flattened to leaves:
  **57483** leaves each side, **0** paths added, **0** removed, **2** changed —
  `/cards/52/items/64/text` and its `/updatedDate`. `cards[52]` re-read as
  `TODO-ALPHA-053-0.0.15` / `Boundary hardening and system-wide DRY squeeze`, item `order=64`,
  section `scope`. Nothing else in the board moved.
- **Postconditions on the rendered file**, measured not asserted: `only four of them` → **0** with
  `five of the six` → **1** as the control that the file was actually rewritten; the other two
  `FROM` strings → **0**, the other two `TO` strings → **1**; controls
  `` newline-joined inside a `child` local `` → **1**, `one pre-existing inline copy` → **1**,
  `_auth_free_subprocess` → **1** (the citation survived). The changed rendered line carries **0**
  non-ASCII characters and **2** `path::Symbol` citations
  (`tests/test_scalars.py::test_package_import_does_not_emit_strawberry_deprecation_warning`,
  `tests/auth/test_mutations.py::_auth_free_subprocess`) — the same two it carried before.
- `uv run python scripts/check_citations.py` → **exit 0**,
  `OK: 981 citations resolve (814 in 442 .py files, 167 in KANBAN.md).` **Measured, not predicted:**
  the figures are unchanged from the reading the review recorded, which is the expected result since
  none of the three replacements adds or removes a citation. The `.py` half is unmoved at 814 in 442
  files.
- `uv run python scripts/check_kanban_anchors.py` → **exit 0**, `OK: 76 card anchors are unique,
  none collides with the 146 glossary anchors, and the KANBAN.md render carries no duplicate id.`
- `uv run python examples/fakeshop/manage.py check` → `System check identified no issues (0
  silenced).`, **exit 0**.
- `git diff --stat -- docs/GLOSSARY.md` → `1 file changed, 1 insertion(+), 1 deletion(-)` —
  **exactly** the concurrent session's `AppConfig` hunk, unchanged. `build_glossary_md.py` was never
  invoked in this pass.
- `git status --short` → **36 lines, the identical path set this pass started with.** Every file
  already dirty at the start of the pass still is; nothing new joined, nothing left. The three paths
  this pass wrote (`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`) were already dirty
  from pass 1. Cumulative diffstat versus HEAD: `KANBAN.html` 1 changed line, `KANBAN.md` 2
  insertions (pass 1's two bullets, one now carrying the corrected text),
  `examples/fakeshop/db.sqlite3` `Bin 4878336 -> 4894720 bytes`.

### Failability proofs

**None; this pass introduced no new boundary.** It touches no `.py` file at all — no guard, gate or
rejection path exists to mutate, and the plan's `### Declarations` (0 boundaries, confirmed by
Worker 3's independent AST-identity proof behind a `DIVERGES` control) is unmoved because the file
that proof covers was not reopened.

### Hot-path budget

Not applicable; plan declares no hot path. Nothing in this pass runs per request, per resolver, per
row, per connection or per outbound message.

### Floor verification

Not applicable; plan declares floor-verification scope `none`. No Django / Strawberry / channels
integration seam is touched — the edit is one text column in the example project's docs-as-data app.

### Implementation notes

- **One delimiter judgement, disclosed rather than absorbed.** Worker 3's M1 replacement 1 is
  written in the review as `` `and five of the six … (only ``tests/base/test_init.py`` does not)` ``
  — a single-backtick markdown code span whose inner backticks are **doubled**, while its two
  sibling pins (M1-2 and L1) use double-backtick delimiters and single backticks inside. Read
  literally the first would store a double-backticked path. I wrote **single** backticks, because
  the target row spells every one of its paths with single backticks and carries **zero** double
  backticks — including `` `tests/base/test_init.py` `` itself, which already appears earlier in the
  same sentence. Both forms render identically as a code span, so this changes no rendered output;
  it is a source-consistency call and it is Worker 3's to overturn if the doubling was literal. No
  other byte of any pinned replacement was altered.
- **The edit is a text update on an existing row, not an insert**, so pass 1's marker-absence /
  free-`order` insert guards do not apply. Their equivalent here is the anchor-count triple
  (`== 1` before, `== 0` after) plus the replacement-absence triple, all asserted before the write:
  a re-run of the script aborts on the first assert having written nothing.
- **`pk=1625` was never opened for write.** The script reads it once, after the save, purely to
  record that its length is unchanged.

### Notes for Worker 3

- The `.py` half of the slice was **not reopened**. `tests/auth/test_sessions.py` is byte-for-byte
  as you verified it; its diffstat versus HEAD is unchanged and nothing in this pass could move it.
- The review surface for this pass is `ARTIFACT.md` `### Documentation / release sanity`: the three
  replacements against your own `FROM` / `TO` lines **character-for-character**, the structural
  `window.KANBAN_DATA` leaf comparison above (which is re-runnable), and the two `--check`s.
- The one thing worth your independent instrument rather than a read: the
  `tests/filters/test_sets.py` reading that drives both halves of M1. Its `child` local is a
  newline-joined string, so an instrument that only greps `subprocess.run(\s*\[\s*sys\.executable`
  or that looks for the `"import django, os, sys; "` spelling will miss it in both directions.

### Notes for Worker 1 (spec reconciliation)

- **No spec byte moved and none is owed.** This pass touched no file under `docs/SPECS/`.
- **No checklist box was touched, in either direction.** All seven `### Dispatched findings
  checklist` boxes were already `- [x]` from pass 1, and this pass landed no new box's contract —
  it corrected the content of work box 4 already covers. In particular **box 7's `980 / 166` is
  still false and still ticked**: the gate reads `981 / 167`, measured again this pass. L2 is yours
  as plan owner and tick-auditor, exactly as Worker 3 routed it; I left it alone deliberately.
- **Box 4's wording now points at a superseded pin.** It reads "carrying the pinned text verbatim",
  and the plan's `#### Step 2` fenced block is no longer what the row carries — Worker 3's three
  anchored replacements are. The box's contract (the row exists, on card 53, at `order=64`, written
  through the ORM) still holds. Worth one line at final verification so a later reader does not
  `diff` the row against the Step 2 block and read the M1 fix as drift.
- **L3 is a staging constraint for the maintainer and must reach the handover.** The card-53 row
  cites `tests/auth/test_mutations.py::_auth_free_subprocess`; that symbol has **0** occurrences at
  HEAD and **3** in the worktree (re-measured this pass, read-only via `git show HEAD:`).
  `scripts/check_citations.py` is pre-commit hook **6** and runs **whole-tree**, so a commit that
  ships `KANBAN.md` + `examples/fakeshop/db.sqlite3` **without** `tests/auth/test_mutations.py` in
  the same commit turns the gate red for every later commit by anyone, this cycle's and the
  concurrent `spec-050` session's alike. The citation is **correct about the tree this cycle hands
  over** — it is not a defect in the bullet and must not be removed. Checked for prior coverage:
  Worker 1's plan does not carry it (`### Verification` V7 reasons only about the citation *count*,
  and `### Baseline-dirty` names `tests/auth/test_mutations.py` as this cycle's own dirty work
  without drawing the staging consequence); it appears only in Worker 3's `#### L3` and its
  `### Notes for Worker 1`. Please carry it into the final-verification summary so it survives into
  the maintainer handover.
- **The `docs/GLOSSARY.md` 1-insertion / 1-deletion hazard the card-56 row records is still live**,
  re-measured at the end of this pass. It resolves when the concurrent session commits.


---

## Review (Worker 3, pass 2)

Re-review of the apply-changes pass. `HEAD = d3b91c8d`, unchanged; `git status --porcelain` is **36**
lines, the identical path set pass 1 ended on; nothing committed, no `stash` / `checkout` /
`restore` / `reset` / `worktree`. Every figure below was re-derived against the live files and the
render — the build report's own table was read after measuring, never before.

**M1 and L1 are discharged. No new finding. `review-accepted`.**

### The instrument: a reconstruction the builder could not have influenced

Rather than checking three replacements one at a time against the build report's account of them, I
rebuilt the row that *should* exist and compared it to the one that does:

1. take Worker 1's `#### Step 2` fenced block — the pass-1 pinned row, **3,652** characters, written
   before either of my passes and untouched by anyone since;
2. parse my own pass-1 `FROM` / `TO` pins out of the `## Review (Worker 3)` section
   programmatically (regex over the numbered and bare forms, markdown code-span delimiters
   stripped) — **3** pairs recovered, FROM 45 / 241 / 125 chars, TO 91 / 515 / 190;
3. assert each `FROM` occurs **exactly once** in the pass-1 text, apply all three, and compare the
   result to the rendered `KANBAN.md` line with its `- ` prefix stripped.

**Reconstruction 4,037 characters; rendered row 4,037 characters; `EXACT MATCH: True`.** Control:
perturbing one token (`five of the six` → `FIVE of the six`) makes the same comparison `False`.

That single result carries four separate claims at once, which is why it is worth more than three
spot checks: all three replacements landed **character-for-character**; **nothing else in the row
moved** (a stray edit anywhere in the other 3,000 characters would break the match); the delta is
**+385**, matching the reported DB delta `3652 → 4037` exactly; and the delimiter judgement below
is settled mechanically rather than by opinion. The builder had no input into any input of this
comparison.

### 1. The delimiter judgement — **ratified**, and the ratification is mechanical

Worker 2 asked explicitly rather than absorbing it, which is the right instinct. It is right on the
merits and I ratify it:

- A **single-backtick markdown code span cannot contain a backtick.** The doubled run inside my
  pin 1 (`` ``tests/base/test_init.py`` `` inside a single-backtick span) is therefore not a literal
  instruction — it is an artifact of my own writing, and the only coherent reading is the one
  Worker 2 took.
- **The row's own convention settles it independently of markdown.** The rendered row carries
  **0** double-backtick sequences and spells every path with single backticks — including
  `` `tests/base/test_init.py` `` itself, which already appears earlier in the same sentence. A
  double-backticked path would have been the row's only one.
- **It is proved, not argued:** my reconstruction above collapses the doubled run to single and then
  matches the render at 4,037 characters. Had the doubling been literal, the match would have failed.

Nothing to change. The correct handling of a pin whose delimiters are ambiguous is exactly what
happened — write the reading the target file's own convention supports, disclose it, and let the
pin's author ratify.

### 2. M1 — the corrected figures, re-derived against the live files

Not read from the build report's table. `grep -o … | wc -l` (never `grep -c`), population named:

| File | `django.setup()` | `DJANGO_SETTINGS_MODULE` | configures Django in the child |
|---|---|---|---|
| `tests/auth/test_mutations.py` | 2 (1 code + 1 docstring) | 2 | yes |
| `tests/auth/test_sessions.py` | 1 | 1 | yes |
| `tests/base/test_init.py` | **0** | **0** | **no** |
| `tests/filters/test_finalizer.py` | 1 | 1 | yes |
| `tests/filters/test_sets.py` | 1 | 1 | yes |
| `tests/orders/test_inputs.py` | 1 | 1 | yes |

**Five of six.** Negative-result control: `tests/test_scalars.py` reads `django.setup()` **0** while
reading `sys.executable` **2** on the same instrument, so a zero here is a real zero.

Retirement and landing, both counted as occurrences over `KANBAN.md`:

| String | count |
|---|---|
| `only four of them configure Django at all` (retired) | **0** |
| `three of them near-identically` (retired) | **0** |
| `collapsed the two copies` (retired) | **0** |
| `five of the six configure Django in the child` | **1** |
| `newline-joined inside a` + backticked `child` + `local` | **1** |
| `five spellings of one prologue` | **1** |
| `one pre-existing inline copy` | **1** |

Controls for the instrument in both directions: `subprocess-isolation idiom is spelled inline` → **1**
(a string that must be present), `ZZZ_NOT_PRESENT_ZZZ` → **0** (a string that must not be).

I also read the three corrected regions **in context**, not just as replaced strings, because a
verbatim landing can still leave a dangling connective or a contradiction with a neighbouring
sentence. All three read coherently: the prototype sentence now enumerates four inline re-spellings
and closes with the arithmetic (`the helper plus four inline re-spellings is five spellings of one
prologue`, 1 + 4 = 5); the probe-kinds sentence still names all six import-isolation files and now
splits them 5/1 with the exception named; and the closing provenance clause is consistent with the
row's own vocabulary (`re-spelling` = inline re-spelling throughout).

### 3. L1 — re-derived read-only against HEAD

`git show HEAD:tests/auth/test_mutations.py` into a scratch path **outside** the repo:

| Token | HEAD | worktree |
|---|---|---|
| `sys.executable` | **1** | 1 |
| `subprocess.run(` | **1** | 1 |
| `django.setup()` | **1** | 2 |
| `_auth_free_subprocess` | **0** | **3** |

One pre-existing inline copy, not two; the helper (1 definition + 2 callers = 3 occurrences) does not
exist at HEAD. The corrected sentence is true and the retired one was not.

### 4. Nothing else moved — the checks that would have caught a fix that overreached

- **pk 1625 / card 56 is byte-identical to Worker 1's `#### Step 3` pin.** Rendered row **2,268**
  characters, `EXACT MATCH: True` against the fenced block, control `False`. Its `updatedDate` in the
  DB dump is still `10:59:48.706186` — pass 1's timestamp, so it was never written.
- **The board moved by exactly the two nodes pass 1 added, and by nothing else — measured against
  HEAD, not against a pre-edit snapshot the builder produced.** `window.KANBAN_DATA` parsed on both
  sides and keyed by `uuid.id`: HEAD **3,718** nodes, worktree **3,720**, **2 added / 0 removed /
  0 changed**; removing exactly those two makes the payloads equal; perturbing one surviving node
  makes the control fail. This is a stronger statement than the build report's pre-edit comparison:
  across **both** passes combined, no pre-existing board node has changed at all.
- **DB delta versus HEAD is still exactly 8 lines**, same composition as pass 1 — `sqlite3 .dump |
  sort` on both sides, 11,115 → 11,119 lines: `glossary_glossaryterm` 448 (the concurrent session's,
  untouched), `kanban_carditem` 1624 and 1625, their two `kanban_uuidmodel` side-rows, and
  `sqlite_sequence` 1623 → 1625. `INSERT INTO` tallies in the diff: 2 glossary, 2 carditem, 2
  uuidmodel, 2 sqlite_sequence — **no other table and no other `kanban_*` row appears.**
  `sqlite_sequence` still reads **1625**, which is the independent proof the pass performed an
  `UPDATE` and not a delete-and-reinsert: a new row would have advanced it.
- **The `.py` half was not reopened.** `tests/auth/test_sessions.py` is still `2 2` by `--numstat`,
  `:465` and `:720` still carry the pinned bytes verbatim, `hunt` **0** / `Revision` **0** with the
  `session` = **131** control unmoved.
- **Fence.** `docs/SPECS/spec-040-auth_mutations-0_0_13.md` still `693 876` — **no spec byte moved**.
  `docs/GLOSSARY.md` still `1 1`, `build_glossary_md.py --check` exits 0 against it. The three
  code-fix files and three auth test files of this cycle all carry their unchanged pass-1 diffstats.
  `git diff -- django_strawberry_framework/__init__.py` empty; no public export moved.
- **Row hygiene:** one line in `KANBAN.md`, **0** non-ASCII characters, no literal `{{card_ref`, no
  embedded newline. `::` occurrences **3**, of which **2** are `path::Symbol` citations
  (`tests/test_scalars.py::test_package_import_does_not_emit_strawberry_deprecation_warning`,
  `tests/auth/test_mutations.py::_auth_free_subprocess`) and the third is `-W error::DeprecationWarning`,
  a warning-filter spec the gate's `.py::` pattern correctly ignores.
- **Gates, re-run by me:** `build_kanban_md.py --check` and `build_kanban_html.py --check` exit **0**;
  two independent regenerates each (to scratch, never writing the repo copies) hash
  `0f926bde0563c2ab…8616` and `99dfc3c7e5552436…4f8f`, identical to each other and to the worktree
  files, matching the build report's digests; `check_citations.py --check` exits 0 at
  **981 / 167 (814 in 442 .py files)** — unchanged, confirming the fix added and removed no citation;
  `check_kanban_anchors.py` green; `check_trailing_commas.py --check` exit 0; `manage.py check` clean.

### 5. L3 — the note as it stands reaches Worker 1; one clause would make it reach the *commit*

Confirmed that Worker 2's coverage check is right: the plan's V7 reasons only about the citation
*count* and `### Baseline-dirty` names `tests/auth/test_mutations.py` without drawing the
consequence, so before pass 1 the constraint existed nowhere. It now sits in three places — my
`#### L3`, my `### Notes for Worker 1`, and Worker 2's `### Notes for Worker 1` — all of which
Worker 1 reads by role. **That is sufficient to reach Worker 1**, and both notes already ask for it
to be carried into the final-verification summary, which is the only path to the maintainer for a
post-final slice with no further gate.

One clause I would add when Worker 1 carries it, because the note currently states the prohibition
without stating *when it fires*, and a hazard whose trigger is unstated reads as a general warning
and gets skimmed:

> The hazard fires **only on a split commit**. `tests/auth/test_mutations.py` is already this
> cycle's own uncommitted Slice 6 work (`### Baseline-dirty`), so committing the cycle as one unit
> is safe and needs no special handling. It goes red only if the board is committed on its own — a
> docs-only or "just the KANBAN rows" commit. The safe minimum unit is `KANBAN.md` + `KANBAN.html` +
> `examples/fakeshop/db.sqlite3` + `tests/auth/test_mutations.py` in one commit.

Recorded as a refinement to an already-adequate note, not as a finding, and it needs no builder pass.

### 6. L2 and box 4 — both Worker 1's, and I do not re-raise either

- **L2 (box 7 ticked against `980 / 166`, gate reads `981 / 167`).** Re-measured this pass: still
  `981 / 167`. `ARTIFACT.md` gives Worker 1 the tick audit at final verification, and Worker 1 wrote
  both the V7 prediction and the box text, so it is the only role that may correct either. Worker 2
  was right to leave it untouched rather than tidy a box whose contract it did not land this pass.
  **Agreed: Worker 1's, not mine, not Worker 2's.**
- **Box 4 now points at a superseded pin.** Independently confirmed: the plan's `#### Step 2` fenced
  block is **3,652** characters and the row carries **4,037**, so a later reader `diff`ing the row
  against the block sees a 385-character divergence and could read the M1 fix as drift. The box's own
  contract (the row exists, on card 53, at `order=64`, written through the ORM) still holds, so this
  is a documentation hazard rather than an over-tick. It is a **good catch by Worker 2** and it is
  Worker 1's to resolve, in the same place and by the same authority as L2 — one line at final
  verification naming this artifact's `## Review (Worker 3)` pins as the row's current contract is
  enough. **Agreed: Worker 1's.**

### High:

None.

### Medium:

None. M1 is discharged.

### Low:

None outstanding. L1 is discharged; L2 and box 4 are routed to Worker 1 by role and are not
Worker 3 findings to hold the unit on; L3 is a maintainer staging note, refined above.

### DRY findings

None new. The pass authors no code, no helper and no constant; it rewrites three clauses of one
`text` column. The row's subject — whether a shared subprocess-probe helper should exist, and in how
many shapes — remains the open decision `TODO-ALPHA-053-0.0.15` owns, and the evidence that decision
will be made from is now correct, which was the whole point of M1.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list
unchanged.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Performed above in full: the verbatim reconstruction at 4,037 characters with a failing control, the
card-56 pin match at 2,268, the retirement/landing occurrence table with both-direction controls, the
uuid-keyed board comparison against HEAD, the 8-line DB dump delta, the two `--check`s, the
byte-stability hashes, and the three gates. Both rows still render exactly once in their target
card's `#### Scope` section, and no other card moved.

### Temp test verification

None. `docs/builder/temp-tests/040-slice-7/` was not created in either pass: every question was
answerable by measurement against the tree, HEAD, the DB dump and the rendered exports. Nothing rests
on a temp test.

### Static helper use

`scripts/review_inspect.py` **not run — skip recorded with its reason.** This pass touches **0**
`.py` files; the diff is one `text` column and two regenerated exports. None of `BUILD.md`
`### When to run the helper during build`'s Worker 3 triggers fires.

### Notes for Worker 1 (spec reconciliation)

- **No spec byte moved across either pass** — `693 876`, re-verified this pass.
- **L2 and box 4 are both yours**, per section 6. Neither blocks `review-accepted`; both should carry
  one line each in your final-verification summary.
- **L3 should reach the maintainer handover with the trigger clause in section 5.** It is the one
  item in this slice whose cost lands on someone outside the cycle.
- The plan's `### C2` correction of `bld-040-final.md` entry 3 still stands and is still recorded only
  in this artifact.

### Review outcome

`review-accepted`. M1 and L1 are discharged, verified by a reconstruction the builder could not
influence and by re-derivation of every corrected figure against the live files. The fix introduced
nothing: no new citation, no other board row, no `.py`, spec or glossary byte, no new dirty path. The
delimiter judgement is ratified. L2, box 4 and L3 are routed to Worker 1 and the maintainer with no
builder work outstanding.

---

## Final verification (Worker 1)

Run at `HEAD = d3b91c8d` (`git log --oneline -1` re-read at the start of this pass, unchanged from
the plan's, both build reports' and both reviews' baseline). `git status --porcelain` = **36** lines,
the identical path set pass 1 ended on. **Nothing was committed.** No `git stash` / `checkout` /
`restore` / `reset` / `worktree` ran, for any reason including verification; every HEAD reference was
`git show HEAD:<path>` into a scratch path **outside** the repository. No `--cov*` flag ran.

**Every figure below was measured by me this pass.** Where a worker had recorded the same figure I
measured first and read theirs afterwards; where the two agree I say so, because agreement between
two independent derivations is the evidence, and agreement produced by copying is not.

### Slice-local checks

| # | Check | Measured this pass | Verdict |
|---|---|---|---|
| V1 | provenance retired, `tests/auth/test_sessions.py` | `hunt` **2 → 0**, `Revision` **1 → 0**; positive control `session` = **131** both sides; `spec-` = **0** | pass |
| V1 | the two pinned lines, read back | `:465` `# Exception containment: hostile scope / session / lock`; `:720` `# Exception containment: hostile __class__ and hostile transport.value` — byte-identical to the plan's pins | pass |
| V2 | inverse proof, AST identity vs HEAD | `IDENTICAL`; control on `list_field.py` (concurrent session's) `DIVERGES`; second control, same file + `x = 1`, `DIVERGES` | pass |
| — | `.py` diffstat | `tests/auth/test_sessions.py \| 4 ++--` = 2 insertions / 2 deletions, exactly the two lines | pass |
| V3 | board rows | card 53 `scope` **65** items / `max(order)` **64**; card 56 **92** / **91**; both rows single-line, ASCII, `uuid` side-row present (`0cfdc244…`, `332e2b73…`); `{{card_ref` = **0** in both | pass |
| V4 | export freshness + stability | all three `--check` exit **0**; I regenerated both exports a third time and `shasum -a 256` is unchanged — `KANBAN.md` `0f926bde…8616`, `KANBAN.html` `99dfc3c7…4f8f`, identical to Worker 2's pass-2 hashes | pass |
| V5 | export diff confined | `KANBAN.md` cumulative `2 insertions`, `KANBAN.html` 1 changed line; each new row renders **exactly once** in `KANBAN.md` (`str.count` over the whole file = 1 for each) | pass |
| V6 | `docs/GLOSSARY.md` untouched | `git diff --numstat` = `1  1` — the concurrent session's `AppConfig` hunk, unchanged since planning; `build_glossary_md.py --check` exit 0 and the script never run by me | pass |
| V7 | citation gate | `OK: 981 citations resolve (814 in 442 .py files, 167 in KANBAN.md)`, exit 0. **The plan's 980 / 166 was wrong; corrected above and in box 7** (`### C3`, L2) | pass, figure corrected |
| V8 | Django consistency | `System check identified no issues (0 silenced).` exit 0 | pass |
| — | `check_kanban_anchors.py` | `OK: 76 card anchors are unique, none collides with the 146 glossary anchors, and the KANBAN.md render carries no duplicate id.` | pass |
| — | DB delta vs HEAD, by content | `sqlite3 .dump \| sort` against `git show HEAD:examples/fakeshop/db.sqlite3`: **8** differing lines — `glossary_glossaryterm` 1 out / 1 in (the concurrent session's row 448, left exactly as found), `kanban_carditem` **2 in / 0 out**, `kanban_uuidmodel` **2 in / 0 out**, `sqlite_sequence` 1 out / 1 in. **No kanban row removed or altered outside the two adds** | pass |
| — | spec untouched | `git diff --numstat -- docs/SPECS/spec-040-auth_mutations-0_0_13.md` = `693  876`, unchanged since planning; the rationale companion untouched | pass |

**V10 — the row is the pin plus the review's three replacements, proved by reconstruction.** This is
the check box 4's wording needed and the one I owed as pin author. Composing the plan's `#### Step 2`
fenced block (3,652 chars) with Worker 3's three `FROM` / `TO` pins — each anchor asserted to occur
**exactly once** in the block before substitution — reproduces the live `CardItem` `pk=1624` text at
**4,037 = 4,037, equality `True`**. Control that the comparison can fail: perturbing one token
(`Measured` → `MEASURED`) returns `False`. Card 56's row is the plan's `#### Step 3` block
**verbatim**, 2,268 = 2,268, `True`. Both blocks were parsed out of this artifact programmatically,
so the comparison uses the artifact's own bytes rather than a retyping of them.

**M1's corrected figures re-derived at source, not accepted.** `tests/filters/test_sets.py`'s `child`
local is newline-joined and carries the full prologue (`import os, sys` / `sys.path.insert(0,
<fakeshop>)` / `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')` / `import django`
/ `django.setup()`), read at source. So **5 of the 6** import-isolation files configure Django in the
child and only `tests/base/test_init.py` does not; the inline re-speller inventory is **4** files.
Positive control: `tests/test_scalars.py` reads **0** `django.setup()` while reading **2**
`sys.executable`. My table agrees with Worker 3's M1 table and Worker 2's pass-2 table in every cell,
derived independently of both. `C1`'s population is unaffected: `sys.executable` is still **9
occurrences in 8 files**, **8 call sites**.

### Checklist audit (`### Dispatched findings checklist`)

All seven boxes `- [x]`. Audited against the diff, not against the reports.

- **Boxes 1-3** (the two comment lines, the zero counts, the inverse proof) — contracts landed;
  re-verified at V1 / V2 above. Both pinned lines are byte-identical to the plan.
- **Boxes 4-5** (the two `CardItem` rows) — landed; re-verified at V3 / V10. **Box 4 amended, not
  un-ticked:** its "carrying the pinned text verbatim" now names the composition (Step 2 + the three
  review pins) that V10 proves, and Step 2 carries a `SUPERSEDED` banner so a later reader cannot
  diff the live row against a stale block and read the M1 fix as drift. The box's contract — the row
  exists, on card 53, at `order=64`, written through the ORM — held throughout and never failed.
- **Box 6** (renders, `--check`s, second-regenerate stability, diff confined) — landed; V4 / V5.
- **Box 7 — L2 decided: the tick STANDS, the figure is corrected.** I took the **substantive
  reading**, and say so explicitly because Worker 2 invited either. The box's contract is a set of
  facts about the tree (`docs/GLOSSARY.md` untouched, `build_glossary_md.py` never run, the gate
  green, the `.py` half unmoved, `manage.py check` clean) and **every one of them landed**. `980 /
  166` was never a contract Worker 2 could land or fail: it was a **prediction I wrote into the plan
  about a measurement**, and it was wrong. Un-ticking would record a builder failure where there was
  none — worse, it would penalise the one handling that was exactly right: Worker 2 measured the real
  value, reported the deviation loudly under `### Notes for Worker 3`, and did **not** bend the
  pinned bytes to make the prediction true. The defect is mine, it is fixed where it lives (V7 and
  the box text), and it is on the record as `### C3`.
- **Nothing is deferred.** No box carries a deferral reason because none is owed.

### Spec reconciliation

**No spec edit is owed, and none was made.** Confirmed by re-derivation, not by inheriting Worker 0's
read: the slice landed two comment lines and two board rows and touched no contract; the spec's
diffstat is unchanged at `693 / 876`; the `### Verified: no spec edit is owed` sweeps re-ran clean at
planning and nothing since has opened the spec. The rationale companion is likewise untouched. The
one item worth naming: `### C3` is a correction of **this artifact's own** figures, not of any spec
claim — the spec never carried them.

### Fail-open and failability confirmations

- **No new boundary exists to pin.** Both passes' `### Failability proofs` read `None`, correctly:
  the diff is two comment lines and two `text` columns. The obligation inverts rather than
  disappearing, and V2 discharges it — AST identity against HEAD behind **two** controls, one of them
  the same comparator returning `DIVERGES` on a file that really changed. Without that second reading
  `IDENTICAL` would be indistinguishable from an instrument comparing nothing.
- **No fail-open shape landed.** Read for the catalogued shapes rather than trusted to a green suite:
  the diff contains no clamp, `getattr` default, `or` fallback, bare `except`, or truthiness test on
  a possibly-absent value — it contains no executable token at all, which V2 proves rather than
  asserts.
- **Declarations held.** Hot path `none` — nothing added runs per request, resolver, row, connection
  or outbound message. Floor verification `none` — no Django / Strawberry / channels seam was
  touched; declared explicitly at planning rather than left silent, and confirmed here by the inverse
  proof rather than by a floor venv, which a comment-only diff cannot justify building.

### For the maintainer handover

Three things leave this slice, and the first is the only one with a cost outside the cycle.

1. **`L3` — a staging constraint, and it fires only on a split commit.** The card-53 row cites
   `tests/auth/test_mutations.py::_auth_free_subprocess`, which has **0** occurrences at HEAD and
   resolves only because this cycle's Slice 6 work is in the working tree. `scripts/check_citations.py`
   is pre-commit hook **6** and runs **whole-tree**, so a board-only commit turns the gate red for
   every later commit by anyone, this cycle's and the concurrent `spec-050` session's alike.
   **The citation is correct about the tree this cycle hands over and must not be removed.**
   `tests/auth/test_mutations.py` is already this cycle's own uncommitted Slice 6 work, so committing
   the cycle as one unit is safe and needs no special handling; the hazard is a docs-only or
   "just the KANBAN rows" commit. **Safe minimum unit: `KANBAN.md` + `KANBAN.html` +
   `examples/fakeshop/db.sqlite3` + `tests/auth/test_mutations.py` in one commit.**
2. **`### C2` is recorded only here.** `bld-040-final.md` entry 3 files the five
   `spec-042 Revision N` citations as stranded; all five resolve (`spec-042` carries `Revision 5` ×9,
   `Revision 7` ×2, `Revision 8` ×1 and has no rationale companion). That file is a closed record
   outside the fence, so the correction lives in this artifact and nowhere else.
3. **The `docs/GLOSSARY.md` hazard the card-56 row records is still live** — one unrelated hunk from
   the concurrent session, `1 insertion / 1 deletion`, re-measured at the close of this pass. It
   resolves when that session commits. Whoever takes the card-56 item lands the glossary edit **on
   top** of that hunk, never by regenerating over it.

**Disclosed:** this pass ran `build_kanban_md.py` and `build_kanban_html.py` in write mode once, to
measure second-regenerate byte stability as the dispatch required. Both files are byte-identical
before and after (hashes above), so no byte moved and no export was changed by me.

### Summary

The slice routed three `bld-040-final.md` deferred-work entries to their owners and nothing else.
`tests/auth/test_sessions.py` lost its two bug-hunt provenance comments — the `:465` parenthetical as
pure provenance, the `:720` head **and** parenthetical because "Revision guards" names a hunt round
rather than an invariant — with the diff proved comment-only by AST identity against HEAD.
`TODO-ALPHA-053-0.0.15` gained a `Scope` row at `order=64` homing the inline
`subprocess.run([sys.executable, …])` idiom with its measured population and the two open design
questions that deferred it; `TODO-ALPHA-056-0.0.17` gained one at `order=91` homing the
`docs/GLOSSARY.md` auth-entry staleness with the corrected two-layer contract stated rather than
pointed at. Catalog entry 3 was **not** homed, because its citations all resolve, and entry 5 was not
re-homed, because card 56 already carries it.

The slice's own lesson is `### C3`: five figures across planning, review and the apply-changes pass
were arithmetically correct and wrong in their subject, inside a bullet that exists to home a
population already mis-measured twice. Three passes re-deriving with the population named is what got
one bullet right, and nothing cheaper would have.

### Spec changes made (Worker 1 only)

**None.** No byte of `docs/SPECS/spec-040-auth_mutations-0_0_13.md` or
`docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md` moved in this slice, in any pass. The
plan's `### Verified: no spec edit is owed` stands re-verified at this gate (`693 / 876`, unchanged).

### Final status

`final-accepted`. Every planned step landed or was intentionally corrected with the reason recorded;
all seven checklist boxes are ticked with their contracts confirmed against the diff; no DRY finding,
no fail-open shape, no unproved claim, and no spec reconciliation outstanding. L2 and box 4 are
resolved here by their owner; L3 carries to the maintainer above.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md

<!-- docs/SPECS/ -->
[spec-040]: ../SPECS/spec-040-auth_mutations-0_0_13.md
[spec-042]: ../SPECS/spec-042-debug_toolbar-0_0_14.md

<!-- docs/builder/ -->
[artifact-md]: ARTIFACT.md
[bld-final]: bld-040-final.md
[build-040]: build-040-auth_mutations-0_0_13.md
[build-md]: BUILD.md
[worker-1]: worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
