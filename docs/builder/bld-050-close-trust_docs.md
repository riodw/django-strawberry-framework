# Build: Close cycle — Cohort B, the trust and extension contract in the shipped docs

Spec reference: `docs/spec-050-list_field_arguments-0_0_15.md` (Decision 20, lines 1648-1700;
Decision 21, lines 1701-1742; `## Slice checklist` Slice 5, lines 161-183; `## Doc updates`,
lines 2614-2682; `## Definition of done` row "The shipped docs state the trust contract",
lines 2893-2898) — re-pinned at final verification; the plan-time numbers had drifted under the
concurrent cohort's spec edits and this pass's own.
Status: superseded cohort artifact (final-accepted only for its pre-candidate snapshot)

## Plan (Worker 1)

### DRY analysis

**Helper inventory checked.** The package-wide AST inventory was refreshed this pass
(`<scratch>/inspect/helper-inventory.md`, 2,254 lines over every `django_strawberry_framework/**.py`)
and searched for the shapes this cohort could otherwise duplicate in prose: `extension`, `schema`,
`policy`, `runner`, `isolation`, `trusted`. This cohort writes **no Python**; the inventory is
recorded because the planning step is unconditional, and its outcome is that the statements the
docs must make already have exactly one implementation each
(`django_strawberry_framework/schema.py::DjangoSchema`, the per-operation runner in
`django_strawberry_framework/extensions/operation_state.py`), so the docs describe one behavior
rather than summarizing several.

- **Existing patterns reused (prose that already says the right thing and must be pointed at, not
  restated).**
  - `docs/README.md` `### Production error policy`, final paragraph
    (`#"The schema owns both, and "`): already states enforcement as schema configuration —
    `DjangoSchema(resource_policy=..., error_policy=...)`, the authority-instance entry read as
    that same declaration and folded in, and the refusal of a factory that would decide
    enforcement later. **That paragraph is the canonical statement of Decision 21's first part in
    this file.** The quick-start paragraph points at it; it does not re-argue it.
  - `docs/README.md` `## Visibility and permissions` (`#"The hook's return is treated as untrusted
    query state"`): already states the mechanically-validated-result half of Decision 20 for the
    `get_queryset` surface. The new trust-contract subsection references it as the worked example
    rather than re-describing the seal.
  - `docs/README.md` `### Response debug extension` prose: "Pass the **class**, not an instance, so
    Strawberry constructs a fresh one per operation" is already upstream's spelling rule and stays
    as written.
  - `docs/README.md` `### `DjangoListField` — a plain list` (`#"does not build the package's
    runner"`) and `### `DjangoSchema` is required for generated mutations`: both already contrast
    plain `strawberry.Schema` correctly. They are **not** in scope and must not be rewritten.
  - `GOAL.md` `## Trust boundary` is the **owner** of the contract. The README states it in the
    README's own voice, for a deployer, and carries no process provenance (`START.md` "No process
    provenance in code or standing prose"): no round labels, no "as of", no "previously", no spec
    or card ids in the prose.
  - Reference-style links only, one `<!-- LINK DEFINITIONS -->` block (`START.md` "Markdown link
    convention"). `docs/README.md` already defines `[goal]: ../GOAL.md` and
    `[glossary-per-operation-extension-isolation]`, so the likely targets need no new definition;
    any genuinely new cross-file ref goes in the correct group, alphabetically.

- **New shared prose justified.** One new `###` subsection under `## Production security profile`
  carrying Decision 20's trust contract. Single responsibility: naming which parties are bounded
  and which are trusted, so every row in the profile's table reads against a stated boundary
  instead of an implied one.

- **Duplication risk avoided.** Three near-copies a naive pass would introduce:
  1. Restating the enforcement-configuration rule in the quick-start paragraph when
     `### Production error policy` already owns it — the two would drift on the next change.
     **Prevented:** the quick-start paragraph states the isolation guarantee and links onward.
  2. Restating the visibility seal inside the new trust subsection. **Prevented:** the subsection
     names the class of mechanical validation and points at `## Visibility and permissions`.
  3. Copying the trust levels into `README.md` (root) beside its existing production-defaults
     bullet, producing two statements of one contract in two files that are swept separately
     (`START.md` "Sweep both files of a pair"). **Prevented:** root `README.md` keeps its one
     existing sentence; see the step list.

### Shared shapes across the two concurrent cohorts

The partition is `docs/builder/DONE/build-050-list_field_arguments-0_0_15.md`
`## Close cycle (Decision 22)`; Cohort A owns the raw-list seam, its tests and the live probe
module. Three shapes both cohorts could touch, each assigned to exactly one owner:

1. **The documented schema spelling in an executable example.** Owner: **this cohort**. Cohort A
   cites it as reuse — its new live probe builds a `DjangoSchema` and installs the optimizer as a
   class or factory entry — so no example in the tree contradicts another.
2. **The trust-contract prose of Decision 20.** Owner: **this cohort**. Cohort A states behavior
   only and adds no trust prose to code or test docstrings.
3. **The evaluation-carry wording** ("a source that arrives evaluated is windowed from the rows it
   holds"). Owner: **Cohort A** (docstrings under `django_strawberry_framework/`). This cohort
   **does not state it**: no row here asks for it, `docs/README.md`'s list-field section documents
   arguments and bounds rather than evaluation state, and writing it here would make a second home
   for a sentence Cohort A owns.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before
editing — another worker's pass may have shifted the file since this plan was written.

**Before the first edit to any owned file:** `git diff HEAD -- docs/README.md` and
`git diff HEAD -- README.md` must each print nothing. Both were clean at plan time. If one is not,
stop and report it here rather than editing.

1. **Quick-start example, `docs/README.md` (~line 44).** Rewrite `strawberry.Schema(...)` onto
   `DjangoSchema(...)` and add `DjangoSchema` to the example's package import line (~line 18), in
   its existing alphabetical order. Keep `config=strawberry_config()` and
   `extensions=[lambda: _optimizer]` exactly as they are: the singleton-in-a-factory optimizer is
   the documented recipe and stays — what changes is the schema it is installed on, which is the
   only schema the isolation guarantee holds for.
2. **The paragraph under it (~line 53).** Rewrite to Decision 21's **three parts, stated
   separately** because they are not one rule:
   - *Enforcement is configured, not installed.* The resource and error policies are declared
     through `DjangoSchema(resource_policy=..., error_policy=...)`; the schema builds its own
     authority per operation from that record. An exact authority **instance** in `extensions=` is
     a compatibility reading, read once as that declaration; moving such an instance into a
     factory is **not** a migration — a factory or subclass resolving to an authority refuses the
     operation — and the migration is the keyword argument. Point at
     `### Production error policy` for the full statement rather than repeating it.
   - *Ordinary extensions follow upstream's spellings.* A class or a factory; an instance carries
     upstream's `DeprecationWarning` unchanged, because ordinary entries are passed to upstream as
     they were given and no instance-only semantics are defined here. **This replaces the current
     sentence "reserve instance and singleton-factory entries for it"**, which reads as though an
     ordinary instance entry were a `DjangoSchema`-blessed spelling.
   - *Isolation is added for the package's own extensions.* `DjangoSchema` gives every
     package-managed resolved extension — its authorities, its optimizer under a class entry or a
     factory result with the singleton-in-a-factory recipe included, its debug extension — one
     state per operation, which is why `extensions=[lambda: _optimizer]` is safe here where
     upstream says a shared instance is not. State it **as this package's own guarantee**, not as
     upstream behavior and not as a claim about a third-party extension: a stranger's extension
     gets exactly upstream's lifecycle. Keep the existing link to
     [per-operation extension isolation][glossary-per-operation-extension-isolation].
3. **Schema-setup example, `docs/README.md` (~line 96).** Same rewrite onto `DjangoSchema`. The
   sentence above it (~line 87) ends "before `strawberry.Schema(...)` is constructed"; with the
   example rewritten, restate it against the schema generally (the finalize-before-schema rule is
   about construction order, not about which schema class). Do not touch the rest of that
   paragraph or the one after it.
4. **Response debug extension example, `docs/README.md` (~line 720).** Same rewrite onto
   `DjangoSchema`, keeping `extensions=[lambda: _optimizer, DjangoDebugExtension]` and the import
   line above it. Prose around it stays.
5. **New `###` subsection under `## Production security profile` (~line 610), placed BEFORE
   `### What the package already defaults to safe`** so the reader meets the boundary before the
   table of rows that exist for it. It states Decision 20 in the README's own voice:
   - the **wire is untrusted** — every GraphQL document, variable, header, upload and transport
     frame; every bound in this profile exists for that input;
   - **configuration is validated, then trusted** — canonicalized at construction, read back as
     copies, refused when it cannot be read back;
   - **application Python is trusted** — resolvers, `get_queryset` hooks, `OrderSet.apply_*`
     overrides, project `QuerySet` classes, extension factories. The package validates what it can
     establish mechanically about their **results** — shape, model, routing, evaluation state —
     and states the contract each must keep; it does not promise to contain code running inside
     its own process, which is Django's own line (a report is a defect when the code it needs
     could feasibly exist in a project using supported public API);
   - **what this package guarantees beyond upstream it states as its own** — a bounded raw list,
     per-operation isolation of its own extensions, an error masked for the right operation.
   Reference `## Visibility and permissions` as the worked example of mechanical result validation
   and `[goal]` for the owning statement. Keep it short — this is a boundary statement a deployer
   reads once, not a restatement of the decision.
6. **Root `README.md`.** No executable schema example exists there (`grep -n "strawberry\.Schema"
   README.md` returns nothing at plan time; the file's only relevant line is the production-defaults
   bullet `#"Build on plain Strawberry's schema or view and you keep none of these"`, which is
   consistent with both decisions). Re-run that grep, confirm, and **change nothing** unless it
   finds an example this plan did not see; record the grep and its result in the build report. The
   spec's `## Doc updates` line for `README.md` is about the collection-field example enumerating
   list arguments, which is not this cohort's row.
7. **Link scaffold.** After the edits, confirm every `][label]` used has a definition, every
   definition has a use, the ten group headers are present in the single block, and definitions are
   alphabetical within their group. `docs/README.md` already defines `[goal]` and the glossary
   anchors the new prose is likely to need.

**Out of scope, explicitly:** `docs/GLOSSARY.md` and the glossary DB (not in any cohort's writable
set this cycle), `KANBAN.md`, `CHANGELOG.md`, `TODAY.md` (the spec says it is deliberately not
touched and that "a Slice 5 executor must not invent an edit to satisfy a checklist row"), and
every `docs/README.md` paragraph not named above.

### Test additions / updates

None: this cohort ships no executable behavior. Two mechanical checks stand in and both belong in
the build report:

- `grep -n "strawberry\.Schema" docs/README.md README.md` after the edits — every surviving hit is
  prose that deliberately contrasts plain Strawberry (currently lines ~118 and ~198 of
  `docs/README.md`, plus the construction-order sentence if it keeps the spelling), and **no hit is
  inside a fenced example**. State the population, not just the absence of hits.
- The repository's own markdown gates over the two touched files:
  `uv run python scripts/check_trailing_commas.py --check docs/README.md README.md` (link-def
  scaffold) and the link resolution check in step 7.

The examples are executable text, so a builder that changes an import line must confirm the symbol
is exported: `DjangoSchema` is a package-root export
(`django_strawberry_framework/__init__.py`) — verify rather than assume, and do not add an export.

**Temp tests for Worker 3:** none needed. Worker 3's `### Documentation / release sanity` check is
the instrument here, and it should read each rewritten example end to end rather than diffing the
schema call alone.

### Boundary count and the split question

**Zero** new boundaries: no guard, cap, rejection path or validation branch is added. The cohort is
one coherent diff over one file (plus a confirmed no-op on a second), so it is **not split**; the
prose and the examples it describes must land together or the doc contradicts itself between passes.

### Failability

`### Failability proofs` reads `None; this pass introduced no new boundary.` A documentation cohort
introduces no boundary, and the check that its claims are true is Worker 3 reading the rewritten
text against Decisions 20 and 21, not a mutation.

### Hot-path budget

`Not applicable; plan declares no hot path.` The plan's hot-path declaration for this cohort is
`none` (`docs/builder/DONE/build-050-list_field_arguments-0_0_15.md` `## Close cycle (Decision 22)`).

### Floor verification

`Not applicable; the plan's floor-verification scope assigns this cohort no run.` This cohort
touches no Django / Strawberry / channels seam; the full twenty-three-path scope is the final
gate's.

### Implementation discretion items

Assessed and decided to be Worker 2's:

- The heading text of the new trust subsection and its exact position relative to the two settings
  paragraphs already under `## Production security profile`, provided it precedes
  `### What the package already defaults to safe`.
- Whether the three parts of step 2 are three short paragraphs or one paragraph with bolded leads,
  matching the surrounding prose density.
- Whether the quick-start example keeps `import strawberry` (it still needs `@strawberry.type`).
- The exact wording throughout, within the contract each step states.

### Spec slice checklist (verbatim)

- [x] State the trust contract of Decision 20 beside the production security profile in
      [`docs/README.md`][docs-readme], and the extension contract of Decision 21 beside the
      optimizer recipe there: enforcement through `resource_policy=` / `error_policy=`, class
      or factory for ordinary extensions, the instance spelling carrying upstream's
      deprecation unchanged, and per-operation isolation of the package's own extensions -
      the singleton-in-a-factory recipe included - as the guarantee this package adds.
- [x] Correct the executable examples, not only the prose beside them: every quick-start and
      schema-setup example that pairs a plain `strawberry.Schema` with
      `extensions=[lambda: _optimizer]` is rewritten onto `DjangoSchema`, which is the only
      schema the isolation guarantee holds for.
- [x] The shipped docs state the trust contract where a deployer reads it: application Python
      is trusted and its documented result contracts are validated; the wire and configuration
      are the bounded parties; a class or a factory is the documented extension spelling, the
      instance spelling carries upstream's deprecation unchanged, and per-operation isolation
      of the package's own extensions - the singleton-in-a-factory optimizer recipe included -
      is stated as the guarantee this package adds (Decisions 20 and 21).

### Notes for Worker 1 (spec reconciliation)

- The glossary entry `Per-operation extension isolation` was read in full against Decision 21 and
  **no contradiction was found**: it already states enforcement as canonical schema state declared
  through `DjangoSchema(resource_policy=..., error_policy=...)`, the class-and-factory spellings
  for everything that is not an authority, the refusal of a factory resolving to an authority, and
  the optimizer's singleton-in-a-factory staying supported with its cross-request plan cache. It is
  DB-backed and not in this cohort's writable set; no edit is requested.
- The sentence this cohort retires from `docs/README.md` (~line 53), "reserve instance and
  singleton-factory entries for it", is the only shipped-doc statement found that reads as a
  package-defined instance spelling. It is a doc defect against Decision 21 rather than a spec
  defect; no spec edit follows from it.

### Spec changes made (Worker 1 only)

- None in this cohort. The one rationale correction this planning pass made is recorded in the
  sibling artifact `docs/builder/bld-050-close-row_carry.md`, whose cohort caused it.

---

## Build report (Worker 2)

**Precondition.** `git diff HEAD -- docs/README.md README.md` printed nothing before the first
edit (`git diff HEAD --stat` over both paths: empty). Plan step 6's re-run of
`grep -n "strawberry\.Schema" README.md` returned exit 1, no hits: root `README.md` carries no
executable schema example, and its only relevant sentence is the production-defaults bullet
`#"Build on plain Strawberry's schema or view and you keep none of these"`, which contradicts
neither decision. **Root `README.md` is therefore unchanged** — confirmed by the diffstat below,
which names one file.

### Files touched

- `docs/README.md` — seven edits, all inside the plan's named sites:
  1. `## Quick start` import line — `DjangoSchema` added in alphabetical order.
  2. `## Quick start` example — `strawberry.Schema(` → `DjangoSchema(`. `import strawberry`
     kept (the block still uses `@strawberry.type`); `extensions=[lambda: _optimizer]` and
     `config=strawberry_config()` untouched.
  3. The paragraph under it — replaced by Decision 21's three parts as three bolded-lead
     paragraphs under one lead line. The retired sentence "reserve instance and singleton-factory
     entries for it" is gone; the enforcement part points at `### Production error policy` rather
     than restating it; the isolation part keeps the existing
     `[per-operation extension isolation][glossary-per-operation-extension-isolation]` link and
     states the guarantee as this package's own, with a stranger's extension left on upstream's
     lifecycle.
  4. `## Schema setup` — the construction-order sentence now reads "before the schema is
     constructed"; the example's import line gained `DjangoOptimizerExtension` and `DjangoSchema`
     (both symbols the block uses) and the construction became `DjangoSchema(...)`. The paragraph
     after the block is untouched.
  5. `## Production security profile` — new `### The trust boundary`, placed immediately before
     `### What the package already defaults to safe`, stating Decision 20's three levels, the
     Django feasibility line with a reference-style link to Django's security policy, and the
     beyond-upstream guarantees as this package's own, pointing at
     the existing `[goal]` reference as owner and `## Visibility and permissions` as the
     worked example of mechanical result validation.
  6. `### Response debug extension` — `strawberry.Schema(` → `DjangoSchema(`, with
     `from django_strawberry_framework import DjangoSchema, strawberry_config` added above the
     existing extensions import. Prose around it unchanged.
  7. Link definitions — one new External entry, `[django-security-policy]`, alphabetical between
     `[django-deploy-checklist]` and `[django-test-client-csrf]`.

`git status --short` shows `docs/README.md` as the only file added to the baseline-dirty set the
plan records (`docs/builder/DONE/build-050-list_field_arguments-0_0_15.md` `## Close cycle
(Decision 22)`), plus this artifact and `docs/builder/worker-memory/050-worker-2.md`. Nothing
else changed and nothing was reverted.

### Tests added or updated

None. This cohort ships no executable behavior; the executed-example run below and the two
mechanical checks the plan named stand in.

### Executed-example verification

A doc example nobody executed is a claim, so all three rewritten blocks were run as written, with
fakeshop's `apps.library` `Branch` / `Shelf` (a FK pair with a reverse accessor) in place of the
prose's `myapp` `Category` / `Item`.

- Script: `<scratch>/verify_readme_examples.py`. It sets
  `os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")`, calls `django.setup()`,
  then builds each block's schema inside `warnings.catch_warnings()` with
  `warnings.simplefilter("error")`, so any `DeprecationWarning` raises.
- Command, from the repository root:
  `PYTHONPATH=examples/fakeshop uv run python <scratch>/verify_readme_examples.py`
- Result, all four lines:

  ```
  OK  quick start: DjangoSchema built, no DeprecationWarning, {'__typename': 'Query'}
  OK  schema setup: DjangoSchema built, no DeprecationWarning, {'__typename': 'Query'}
  OK  response debug extension: DjangoSchema built, no DeprecationWarning, {'__typename': 'Query'}
  OK  control: instance entry raised DeprecationWarning: Passing an extension instance to
  `extensions=[...]` is deprecated ... https://github.com/strawberry-graphql/strawberry/issues/4369.
  ```

- **Positive control, not optional.** A "no `DeprecationWarning`" assertion passes identically
  when the warning filter is not in force, so the script ends by constructing a plain
  `strawberry.Schema` with an optimizer **instance** entry under the same filter and asserts it
  raises. It does, with upstream's own text. That also exercises the doc's new claim that an
  instance entry carries upstream's deprecation unchanged.
- Each schema answers `{ __typename }`, which reaches no database. Proof the probe writes no
  tracked bytes: `shasum -a 256 examples/fakeshop/db.sqlite3` before and after a full run is
  `563b26d8003c3c41072b7b7bbfc12fec524969aa3c9b258d7cdbac68ed32b52f` both times.
- `DjangoSchema` is a package-root export, verified rather than assumed:
  `django_strawberry_framework/__init__.py` imports it and lists `"DjangoSchema"` in `__all__`.
  No export was added.

### Validation run

- `uv run ruff format` / `uv run ruff check --fix` — **not applicable**: this pass touched no
  Python inside the repository (the verification script lives in the session scratchpad). The
  pre-commit run below reports both ruff hooks as `(no files to check) Skipped` for the same
  reason.
- `uvx pre-commit run --files docs/README.md README.md` — **pass**. `kanban tracked path
  constants` Passed, `source layout` Passed (the link-def scaffold check), `ruff format` Skipped,
  `ruff check` Skipped, `kanban anchors` Passed, `citations resolve` Passed.
- `uv run python scripts/check_citations.py --check` — **pass**:
  `OK: 1101 citations resolve (922 in 448 .py files, 179 in KANBAN.md).`
- Link audit over both files, fenced blocks dropped and code spans stripped **per line** (a
  document-wide `` `...` `` stripper mispairs across an odd backtick and reports false orphans —
  the first run of this audit did exactly that on this artifact): `docs/README.md` has **38** uses
  and **38** definitions, **0** `][label]` uses without a definition and **0** definitions without
  a use; all ten group headers present, every group alphabetical. `README.md`: 21 and 21, 0 orphans
  either way. This artifact: 2 and 2, 0 orphans either way. The two
  new in-page anchors used (`#production-error-policy`, `#visibility-and-permissions`) both name
  live headings, and the new `### The trust boundary` heading has no inbound reference to rot.
- `strawberry.Schema` census, stated as a population rather than an absence: **3** surviving hits
  in `docs/README.md` and **0** in `README.md`. A fence-tracking scan reports all three at prose
  lines (the isolation paragraph, the generated-mutations paragraph, the list-field dispatch
  paragraph) and **0** inside any fenced example — each is a deliberate contrast with plain
  Strawberry and is out of scope per the plan.
- `git status --short` after every edit — every entry is either baseline-dirty per the plan, or
  one of `docs/README.md`, this artifact, `docs/builder/worker-memory/050-worker-2.md` (that
  directory is untracked scratch, so it shows in neither list).
- **One file appeared mid-pass that this cohort did not touch:**
  `django_strawberry_framework/utils/querysets.py` went from clean to `M` between the first and
  last `git status --short` of this pass. It is Cohort A's owned path and is also named by the
  concurrent DRY cycle. Reported, not reverted, not inspected.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; the plan's floor-verification scope assigns this cohort no run.

### Implementation notes

- **Three paragraphs, not one.** The plan left the shape to discretion; Decision 21's parts are
  three different rules with three different consequences (a refusal, an upstream warning, an
  added guarantee), so collapsing them into one paragraph would let a reader carry the refusal
  over to ordinary extensions. One short lead line keeps them read as one contract.
- **Heading text `### The trust boundary`.** It matches what `GOAL.md` calls the same contract, so
  a reader moving between the two files meets one name. Its position immediately before
  `### What the package already defaults to safe` is what lets the trust subsection say "every row
  below reads against them" and have the table be what it points at.
- **Subclass wording.** The new paragraph says a factory **or a subclass that resolves to one**
  refuses the operation with `SCHEMA_CONFIGURATION_UNAVAILABLE`, which is Decision 21's wording.
  `### Production error policy` separately keeps the fuller statement, including the
  construction-time `ConfigurationError` for a subclass that *supplies* a policy; the quick-start
  paragraph deliberately does not repeat it and links there instead.
- **Import lines.** Step 3's block gained `DjangoOptimizerExtension` as well as `DjangoSchema`: it
  already used the optimizer without importing it, and leaving that gap in a block the pass is
  rewriting for executability would contradict the row being ticked. The debug block took a second
  import line rather than merging into the existing `...extensions import` line, because the two
  come from different modules.
- **`import strawberry` kept in the quick start** (discretion item): the block still decorates
  `Query` with `@strawberry.type`, so removing it would break the example.

### Notes for Worker 3

- The executed-example script is at `<scratch>/verify_readme_examples.py` and is re-runnable with
  the command above; it is deliberately outside the repo and is not a test to promote.
- Read each rewritten block end to end rather than diffing the schema call alone — two of the
  three also changed an import line, and the `## Schema setup` prose above its block changed with
  it.
- `README.md` (root) is untouched. Its `<!-- External -->` link-definition group is **not**
  alphabetical at HEAD (`build-image`, `build-url`, `coveralls-*`, `license-*`, `changelog-*`).
  That is pre-existing, the `source-layout` hook passes on it, and this pass made no edit to that
  file, so it was left alone rather than swept.

### Notes for Worker 1 (spec reconciliation)

- No spec amendment is owed by this pass. Decisions 20 and 21 were implementable as written, and
  the doc defect Worker 1's plan flagged (the retired sentence "reserve instance and
  singleton-factory entries for it") is gone.
- One wording choice worth a custodian's eye, recorded because the two homes must agree rather
  than because either is wrong. Spec section **`### Decision 21`**, current wording: "a factory or
  subclass resolving to one refuses the operation". Shipped `docs/README.md`
  `### Production error policy` (unedited by this pass) says something narrower for one of those
  two: "subclassing either extension to supply it, raise `ConfigurationError` at construction".
  The new quick-start paragraph states Decision 21's version verbatim in the README's own voice,
  so both readings are now in one file. **Recommended replacement** (spec, Decision 21, only if
  the custodian judges the two to disagree): "a factory resolving to one refuses the operation,
  and a subclass supplying a policy is refused at construction". No edit is requested from this
  pass — the behavior was not exercised here, so this is a consistency flag rather than a finding.
- `docs/GLOSSARY.md` is DB-rendered and out of this cohort's writable set. Nothing in it was found
  to contradict Decision 21, matching the plan's own reading; no glossary note is owed.

---

## Review (Worker 3)

Diff reviewed: `git diff HEAD -- docs/README.md README.md` — 27 insertions, 7 deletions, one file.
`README.md` (root) is unchanged, as the plan's step 6 and the build report both claim, confirmed
by the diffstat naming one file.

### Independent re-execution

Worker 2's executed-example run was not accepted on its record. A separate script was written
from the shipped text rather than re-run from Worker 2's:
`<scratch>/w3_readme_verify.py`, run from the repository root as
`PYTHONPATH=examples/fakeshop uv run python <scratch>/w3_readme_verify.py`, with
`os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")`, `django.setup()`, and every
schema built inside `warnings.catch_warnings()` + `warnings.simplefilter("error")`. `Branch` /
`Shelf` from `apps.library` stand in for the prose's `myapp` `Category` / `Item`. Every row below
is that run's own output.

```
OK   quick start: {'__typename': 'Query'}
OK   schema setup: {'__typename': 'Query'}
OK   response debug extension: {'__typename': 'Query'}
OK   production mount: {'__typename': 'Query'}
OK   CONTROL plain Schema + instance entry: DeprecationWarning: Passing an extension instance to
     `extensions=[...]` is deprecated ... https://github.com/strawberry-graphql/strawberry/issues/4369.
OK   D21a exact authority instance entry: no DeprecationWarning; schema.extensions == ()
OK   D21b factory resolving to an authority: codes=['SCHEMA_CONFIGURATION_UNAVAILABLE']
OK   D21c subclass CLASS entry: ConfigurationError at CONSTRUCTION
OK   D21d subclass INSTANCE entry: ConfigurationError at CONSTRUCTION
OK   D21e factory resolving to a subclass: codes=['SCHEMA_CONFIGURATION_UNAVAILABLE']
OK   D21f error-policy subclass entry: ConfigurationError at CONSTRUCTION
OK   D21g ordinary instance entry on DjangoSchema: DeprecationWarning (upstream's own text)
```

- **The positive control is what makes the no-warning rows non-vacuous**, and it is this
  reviewer's own, not a re-read of Worker 2's: a plain `strawberry.Schema` with an optimizer
  INSTANCE entry raises under the identical filter. A fourth executable block the pass did not
  touch (`### The production GraphQL mount`) was run too, so the census of executable schema
  blocks is complete rather than sampled.
- **The probe writes no tracked bytes.** `shasum -a 256 examples/fakeshop/db.sqlite3` is
  `563b26d8003c3c41072b7b7bbfc12fec524969aa3c9b258d7cdbac68ed32b52f` both before and after the
  run. Each schema answers `{ __typename }`, which reaches no database.

### High:

#### `docs/README.md` `## Quick start` states a rejection path the code does not have for a subclass entry

`docs/README.md` `## Quick start` #"a factory or a subclass that resolves to one instead refuses
the operation" (the **Enforcement is configured, not installed.** paragraph, README line 55)
claims one answer for two entry shapes the code answers differently, and the subclass half of the
claim names a behavior that cannot occur.

What the code does, measured (rows `D21b`-`D21f` above, and readable at
`django_strawberry_framework/schema.py::_declared_authority` and
`django_strawberry_framework/schema.py::DjangoSchema.get_extensions`):

| entry | when | answer |
|---|---|---|
| exact authority instance | construction | folded into the record, entry dropped, no `DeprecationWarning` |
| **subclass of either authority, as a class OR an instance entry** | **construction** | **`ConfigurationError` — the schema never builds** |
| factory resolving to either authority, subclasses included | operation | `SCHEMA_CONFIGURATION_UNAVAILABLE` |

A directly supplied subclass is refused by `_declared_authority` before `super().__init__` runs, so
it never reaches `get_extensions` and no operation is ever refused for it. There is no
configuration in which a subclass entry produces the code the sentence names. This is also
**self-contradictory inside one file**: `docs/README.md` `### Production error policy`
#"subclassing either extension to supply it, raise `ConfigurationError` at construction" (line 154,
unedited by this pass) states the correct behavior three paragraphs later, and the same paragraph
lists the refusal cases as factories only. The spec's own exact ladder agrees with line 154:
`docs/spec-050-list_field_arguments-0_0_15.md` `### Decision 15` gives
`subclass of an authority | schema construction | ConfigurationError`.

Why it matters: a deployer reading line 55 expects a schema that imports cleanly and fails every
request. The truth is the opposite — the process fails at import. That is the difference between
"my endpoint is down, check the error code" and "my deploy will not start", and it is the one
sentence in the new prose a consumer would act on.

Recommended change (splits the clause; needs no spec edit, since Decision 15 already licenses the
exact wording and `### Production error policy` already uses it):

```
... folded into the schema; a factory that resolves to one instead refuses the operation with the
stable `SCHEMA_CONFIGURATION_UNAVAILABLE` code, and a subclass of either extension is refused at
construction with `ConfigurationError`.
```

Expectation after the fix: the two statements in `docs/README.md` agree with each other, with
Decision 15's ladder, and with rows `D21b`-`D21f` above.

### Medium:

#### `docs/GLOSSARY.md` still pairs the singleton-in-a-factory with a plain `strawberry.Schema`

Not a defect in this diff and not fixable by this cohort — recorded because the DoD row being
graded says "the **shipped docs**", and a shipped doc still carries the exact shape the new
README prose says is unsafe there. A fenced census over all 217 tracked `.md` files finds two
consumer-facing examples of the pattern outside the two files this cohort owns:

- `docs/GLOSSARY.md` `## `DjangoOptimizerExtension`` #"schema = strawberry.Schema(query=Query, extensions=[lambda: _optimizer])" — the quick-start recipe.
- `docs/GLOSSARY.md` `## finalize_django_types` #"schema = strawberry.Schema(query=Query, extensions=[lambda: _optimizer])" — the schema-setup recipe.

Both are the spec row's own description ("every quick-start and schema-setup example that pairs a
plain `strawberry.Schema` with `extensions=[lambda: _optimizer]`"), and both contradict the
glossary's own `## Per-operation extension isolation` body, which says a plain
`strawberry.Schema` "is not promised what it cannot be given: there the supported entries are the
class and a factory that builds a fresh extension per call". `docs/GLOSSARY.md` is rendered from
the glossary DB and is outside every cohort's writable set this cycle
(`docs/builder/DONE/build-050-list_field_arguments-0_0_15.md` `## Close cycle (Decision 22)`), so
this is escalated to Worker 1 rather than dispatched to Worker 2. See
`### Notes for Worker 1 (spec reconciliation)`.

(A third hit, `examples/fakeshop/test_query/README.md` #"schema = strawberry.Schema(query=Query, extensions=[lambda: ext])", is a plan-cache test illustration rather than a consumer recipe, and
that file is baseline-dirty from the concurrent session. Named for population completeness; no
action asked.)

### Low:

#### One `Schema(...)` residue under `## Schema setup`

`docs/README.md` `## Schema setup` #"after the `Schema(...)` construction instead builds the
schema" (line 105) kept the bare `Schema(...)` spelling while the sentence above the block was
rewritten to "before the schema is constructed" and the block itself now constructs
`DjangoSchema`. It reads as generic rather than wrong, so it is not a correctness finding; if
Worker 2 is re-passing for the High anyway, "after the schema is constructed" makes the paragraph
one voice. No test expectation.

### DRY findings

- **No restatement of the glossary body.** `docs/GLOSSARY.md` `## Per-operation extension
  isolation` is ~4,900 characters of mechanism (runner, leases, tokens, streamed-frame rebinding).
  The new `## Quick start` paragraph states the guarantee in three clauses and links to it. That is
  the pointer-plus-contract shape the plan committed to; nothing to consolidate.
- **No restatement of `### Production error policy`.** The enforcement paragraph states the
  declaration rule and links onward for the full statement; the retired sentence ("reserve instance
  and singleton-factory entries for it") is gone from the file, confirmed by grep.
- **Observation, not a defect: the trust contract now has two homes.** `GOAL.md` `## Trust
  boundary` and `docs/README.md` `### The trust boundary` carry the same three levels, which
  Decision 20 designs on purpose (GOAL owns it, the docs state it as the package's own). The
  standing hazard is `START.md` "Sweep both files of a pair" — the next edit to either owes the
  other. The README version is not a copy: it drops the four-layer table, adds the
  `## Visibility and permissions` worked-example pointer, and is written for a deployer.
- **Existence challenge:** none raised. This cohort adds no abstraction, no helper, no indirection.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` prints nothing: `__all__` and the re-export
list are unchanged. `DjangoSchema` was already a package-root export, so the three rewritten import
lines add no export. Confirmed independently by importing it in the probe above.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

The slice touches docs, so this ran in full, reading `docs/README.md` end to end.

- **Version strings and shipped statuses.** The pass introduces none. The `Since` column of
  `### What the package already defaults to safe` (`0.0.14` / `0.0.11`) and the `Django>=5.2.16`
  floor sentence are untouched and sit outside the diff.
- **No spec relocation.** The diff moves no `docs/spec-050-*` file.
- **Links.** An independent audit of `docs/README.md` (fenced blocks dropped, code spans stripped
  per line) reports **38** `][label]` uses and **38** definitions, **0** uses without a definition,
  **0** definitions without a use, all ten group headers present in one block, every group
  alphabetical, and every relative target resolving on disk. `README.md`: 21 and 21, 0 orphans;
  its `<!-- External -->` group is not alphabetical, which is pre-existing at HEAD in a file this
  pass did not touch (Worker 2 disclosed it) — not a finding against this cohort.
- **The one new definition.** `[django-security-policy]` sits in `<!-- External -->` between
  `[django-deploy-checklist]` and `[django-test-client-csrf]`, used once, and is byte-identical to
  the definition the spec already carries at
  `docs/spec-050-list_field_arguments-0_0_15.md` #"[django-security-policy]: https".
- **The two new in-page links stay inline**, per `START.md` "Markdown link convention", and both
  name live headings: `#production-error-policy` → `### Production error policy`,
  `#visibility-and-permissions` → `## Visibility and permissions`. The new `### The trust boundary`
  heading has no inbound reference to rot.
- **Gates.** `uvx pre-commit run --files docs/README.md` — pass (tracked-path constants, source
  layout, kanban anchors, citations all Passed; both ruff hooks Skipped, no Python).
  `uv run python scripts/check_citations.py --check` — pass,
  `OK: 1104 citations resolve (925 in 448 .py files, 179 in KANBAN.md).`
- **No process provenance.** A sweep of the added lines for `previously`, `no longer`, `as of `,
  `now`, `round N`, `Decision N`, `Slice N`, `spec-0` returns zero hits. The prose is in the
  README's own voice throughout.
- **No obsolete staging wording** ("coming soon", "planned") in the rewritten region. The slice
  regenerates no script-rendered doc.

### Spec slice checklist walk

All three boxes are `- [x]`, and each tick has a matching change in the diff:

1. *State the trust contract … and the extension contract …* — landed as `### The trust boundary`
   plus the three-paragraph extension contract. The tick stands; the High above is a correctness
   defect **inside** delivered text, not an over-tick.
2. *Correct the executable examples …* — landed. Verified independently, not from the build
   report: a fence-tracking scan of `docs/README.md` finds **3** surviving `strawberry.Schema`
   mentions, at lines 59, 124 and 204, **all in prose** and each a deliberate contrast with plain
   Strawberry; **0** inside any fenced block. `README.md` (root): **0** hits of any kind.
3. *The shipped docs state the trust contract where a deployer reads it …* — landed, subject to the
   High and to the Medium's glossary residual.

No box is silently unaddressed; no box is ticked without a matching change.

### Failability proofs

The build report records `None; this pass introduced no new boundary.` **Audited and agreed:** the
diff adds no guard, cap, rejection path, or validation branch — it is prose and three schema-class
substitutions. The re-run set is therefore empty, which `worker-3.md` permits only when the diff
introduces no boundary meeting the floor; that condition holds here. Boundaries re-run: none.
Boundaries accepted on Worker 2's record: none — there are none to accept.

The claims the diff *does* make are behavioral claims about code the diff does not touch, so they
were verified the way `worker-3.md` "Claim verification" requires — by executing them (rows
`D21a`-`D21g`) and by reading `schema.py::_consumer_extension_entries`,
`schema.py::_declared_authority` and `schema.py::DjangoSchema.get_extensions` — rather than by
reading the build report's account of them. One of the three claims failed that check; it is the
High.

### Hot-path budget verification

Plan declares this cohort `none`, and the diff adds no runtime code. Nothing owed, nothing missing.

### Static helper use

`scripts/review_inspect.py` **skipped, deliberately**: `BUILD.md` `### When to run the helper
during build` triggers on new `.py` files, files under `optimizer/` or `types/`, and line
thresholds of new logic. This diff touches one `.md` file and zero `.py` files, so no trigger
fires.

### Test staleness

Run independently of the artifact's file list, per `worker-3.md`: `grep -rn "docs/README"` across
`tests/`, `examples/` and `scripts/` finds no reader — no test, fixture, or generator asserts this
file's content, so the doc edit strands nothing. No wire-shape or model-field change is in the
diff, so neither shape in `BUILD.md` `### Test staleness a focused run cannot see` applies.

### What looks solid

- **The three-paragraph split of Decision 21 is the right call and is executed well.** A refusal, an
  inherited upstream warning, and an added guarantee genuinely are three rules; one paragraph would
  have let the refusal bleed onto ordinary extensions. Two of the three are exactly right against
  the code.
- **The trust subsection does not overclaim.** It says the package "validates what it can establish
  mechanically about their **results**", which is `GOAL.md`'s own hedge, and it does **not** say
  sidecar results are validated on every surface. That distinction is load-bearing right now:
  `django_strawberry_framework/connection.py::_pipeline_sync` #"qs = set_class.apply_sync(value, qs, info)"
  applies `FilterSet` / `OrderSet` with no re-seal, while
  `django_strawberry_framework/list_field.py::_apply_orderset_sync` #"return _validate_post_orderset_result"
  does re-seal — a per-surface claim would have been false on the day it shipped.
- **`### The trust boundary` is positioned to earn its "every row below reads against them".**
  Placing it before `### What the package already defaults to safe` makes that sentence point at a
  real table rather than at nothing.
- **The import lines were fixed, not just the constructor.** `## Schema setup`'s block used
  `DjangoOptimizerExtension` without importing it at HEAD; rewriting the block for executability and
  leaving that gap would have contradicted the ticked row. It was closed.
- **`README.md` (root) was left alone on evidence.** The grep the plan asked for was re-run and
  re-verified here: zero `strawberry.Schema` hits, zero `extensions=[` hits. A cohort that "swept"
  it anyway would have churned a file for nothing.

### Temp test verification

- No temp test was written under `docs/builder/temp-tests/050/trust_docs/`. The instrument this
  review needed is an executable transcription of shipped doc text, which belongs outside the repo
  and is not a test to promote; it lives at `<scratch>/w3_readme_verify.py` and is re-runnable with
  the command above.
- Disposition: not promoted, not kept in-tree. Nothing it proved is shipped behavior lacking a
  permanent test — every property it exercises is `DjangoSchema` behavior already pinned by the
  package suite; the script's job was to check the *documentation* against it.

### Notes for Worker 1 (spec reconciliation)

- **Escalated: `docs/GLOSSARY.md` carries the residual of the row this cohort ticked.** See the
  Medium. The DoD row says "the shipped docs", and the glossary is one. Resolution paths, in the
  order this reviewer would rank them: (a) card the two glossary bodies for a DB edit + regenerate
  in the close cycle's remaining work, since the fix is two lines in `GlossaryTerm.body` and the
  board DB is already being touched at "Record and card"; (b) declare the row's scope to be
  `docs/README.md` only and record the glossary as deferred with a named owner, which
  `BUILD.md` `### Deferred work catalog` will then carry; (c) leave it, which reopens the "partial
  claim fix" hazard `START.md` names. Not a worker's call — Worker 1 owns it.
- **The Decision 21 / Decision 15 wording gap the build report raised is real, and the doc fix does
  not depend on it.** Decision 21 says "a factory or subclass resolving to one refuses the
  operation"; Decision 15's ladder says a subclass is a construction-time `ConfigurationError`.
  Measured behavior (rows `D21c`, `D21d`, `D21f`) matches Decision 15. Worker 2's recommended spec
  replacement — "a factory resolving to one refuses the operation, and a subclass supplying a policy
  is refused at construction" — reads correct against the code, with one caveat worth the
  custodian's eye: a subclass entry is refused whether or not it *supplies* a policy (row `D21c` is a
  bare class entry that supplies nothing), so "a subclass of either extension is refused at
  construction" is the accurate form. The two Decisions disagreeing is a `START.md` "five homes per
  contract" defect; the README's High is fixable today against Decision 15 either way.
- No other spec amendment is owed by this cohort.

### Review outcome

`revision-needed` — one High. The Medium is escalated (outside every cohort's writable set) and does
not itself hold the unit; the Low is optional and named only because a re-pass is happening anyway.

Re-review will re-run `<scratch>/w3_readme_verify.py` (rows `D21b`-`D21f` are the oracle for the
corrected sentence) and re-walk the link audit.

---

## Build report (Worker 2, pass 2)

Apply-changes pass over Worker 3's review section. Two findings closed: the High (the quick-start
sentence claiming an operation-time refusal for a subclass entry) and the Low (the bare
`Schema(...)` residue under `## Schema setup`). The Medium is `docs/GLOSSARY.md`, DB-rendered and
outside this cohort's writable set; it is untouched and stays escalated to Worker 1.

### Files touched

`git status --short` names one file this pass: `docs/README.md` (plus this artifact and the
untracked `docs/builder/worker-memory/050-worker-2.md`). Two edits:

1. **`## Quick start`, the `**Enforcement is configured, not installed.**` paragraph (High).** The
   clause "a factory or a subclass that resolves to one instead refuses the operation with the
   stable `SCHEMA_CONFIGURATION_UNAVAILABLE` code" is replaced by the admission ladder as the code
   answers it. The sentence now reads:

   > An exact authority instance in `extensions=` is read once as that same declaration and folded
   > into the schema; a factory that resolves to one instead refuses the operation with the stable
   > `SCHEMA_CONFIGURATION_UNAVAILABLE` code, and a subclass of either extension — supplied as a
   > class or as an instance — is refused at construction with `ConfigurationError`.

   "supplied as a class or as an instance" is deliberate over the spec-side phrasing "a subclass
   supplying a policy": the refusal does not depend on the subclass supplying anything (probe row
   `B` is a bare class entry). The two other clauses of the paragraph are untouched, and the
   sentence is now the same ladder `### Production error policy` states three paragraphs later.

2. **`## Schema setup`, the sentence after the block (Low).** "after the `Schema(...)`
   construction" now reads "after the `DjangoSchema(...)` construction", naming the class the block
   above it constructs. Nothing else in that paragraph changed.

### Tests added or updated

None. This cohort ships no executable behavior; the probe and re-runs below stand in.

### Verification of the rewritten sentence against the code

Read first, then executed. `django_strawberry_framework/schema.py::_declared_authority` raises
`ConfigurationError` for any entry whose type is a strict subclass of either authority — it is
called from `schema.py::_consumer_extension_entries`, which runs inside `DjangoSchema.__init__`
before `super().__init__`, so a subclass entry never reaches `get_extensions` and no operation can
be refused for it. `schema.py::DjangoSchema.get_extensions` is where a resolved member claiming
either role is refused, which is the factory case and only the factory case.

- Probe: `<scratch>/p2_ladder.py`, run from the repository root as
  `PYTHONPATH=examples/fakeshop uv run python <scratch>/p2_ladder.py`, with
  `os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")` and `django.setup()`.
  Row `A` is built under `warnings.catch_warnings()` + `warnings.simplefilter("error")`.
- Result, exit 0:

  ```
  OK   A exact authority instance entry: built, no DeprecationWarning, schema.extensions == ()
  OK   B subclass CLASS entry: ConfigurationError at CONSTRUCTION: ResourceSubclass <class '__main__.ResourceSubclass'> subclas...
  OK   C subclass INSTANCE entry: ConfigurationError at CONSTRUCTION: ErrorSubclass <__main__.ErrorSubclass object at 0x109a9b380>...
  OK   D factory resolving to an authority: schema BUILT; operation codes=['SCHEMA_CONFIGURATION_UNAVAILABLE'], data=None
  OK   D2 factory resolving to a subclass: schema BUILT; operation codes=['SCHEMA_CONFIGURATION_UNAVAILABLE']
  ```

  Rows `B` and `C` cover both spellings the rewritten clause names; `D` and `D2` show the factory
  path builds a schema and refuses at the operation, which is what keeps the two halves of the
  sentence distinct. The refusal rows print the package's own server-side log line, which is why
  the transcript above is preceded by two "Refusing every operation on this schema" lines.
- The probe writes no tracked bytes: `shasum -a 256 examples/fakeshop/db.sqlite3` is
  `563b26d8003c3c41072b7b7bbfc12fec524969aa3c9b258d7cdbac68ed32b52f` before and after.

### Executed-example re-verification

Both scripts were re-run against the shipped text after the edits, and both pass unchanged — this
pass edits prose only, so the three fenced blocks are byte-identical to the ones pass 1 executed.

- `PYTHONPATH=examples/fakeshop uv run python <scratch>/verify_readme_examples.py` — exit 0, four
  lines: quick start / schema setup / response debug extension each built with no
  `DeprecationWarning`, and the positive control (plain `strawberry.Schema` + an instance entry)
  raising upstream's own text. Without that control the three OK lines would pass identically with
  the warning filter absent.
- Worker 3's own `<scratch>/w3_readme_verify.py` was re-run as a second instrument — exit 0, all
  twelve rows OK, including `D21b`-`D21f`, which are the oracle the review named for the corrected
  sentence. Its `D21c` / `D21d` / `D21f` rows report `ConfigurationError at CONSTRUCTION` and its
  `D21b` / `D21e` rows `codes=['SCHEMA_CONFIGURATION_UNAVAILABLE']`, matching the rewritten clause
  rung for rung.
- `shasum -a 256 examples/fakeshop/db.sqlite3` unchanged across both runs (same digest as above).

### Validation run

- `uv run ruff format` / `uv run ruff check --fix` — not applicable; this pass touched no Python
  inside the repository. Both hooks report `(no files to check) Skipped` below for the same reason.
- `uvx pre-commit run --files docs/README.md` — **pass**: `kanban tracked path constants` Passed,
  `source layout` Passed, `ruff format` Skipped, `ruff check` Skipped, `kanban anchors` Passed,
  `citations resolve` Passed.
- `uv run python scripts/check_citations.py --check` — **pass**:
  `OK: 1104 citations resolve (925 in 448 .py files, 179 in KANBAN.md).`
- Census, stated as a population: a fence-tracking scan of `docs/README.md` finds **3**
  `strawberry.Schema` occurrences, at lines 59, 124 and 204, **all in prose** and **0** inside any
  fenced block — unchanged by this pass, each a deliberate contrast with plain Strawberry. The same
  scan for a bare `Schema(...)` (excluding `.Schema(...)` and a backticked-qualified form) now
  finds **0** occurrences anywhere in the file; it found one before this pass, which was the Low.
- Links: this pass added and removed no `][label]` use and no definition, so pass 1's audit (38
  uses / 38 definitions, 0 orphans either way, ten group headers, every group alphabetical) still
  describes the file. The in-page `#production-error-policy` link inside the rewritten sentence's
  own paragraph is untouched and still names a live heading.
- `git status --short` — no path outside this cohort's writable set appeared. The entries are the
  plan's baseline-dirty set plus `docs/README.md` and this artifact. Nothing was reverted.
  `django_strawberry_framework/utils/querysets.py`, reported mid-pass in pass 1, is still `M`;
  `tests/utils/test_querysets.py`, `django_strawberry_framework/resource_policy.py`,
  `django_strawberry_framework/types/resolvers.py` and `tests/test_resource_policy.py` are likewise
  not this cohort's. Reported, not touched.

### Failability proofs

None; this pass introduced no new boundary. Both edits are prose inside a documentation file.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; the plan's floor-verification scope assigns this cohort no run.

### Implementation notes

- **Em-dash parenthetical rather than a fourth clause.** "supplied as a class or as an instance"
  sits inside the subclass clause instead of becoming its own sentence, so the paragraph still
  reads as one ladder with three rungs. A fourth sentence would have pulled the construction-time
  half away from the operation-time half it is being contrasted with.
- **`ConfigurationError` named, not just described.** The factory half already names its stable
  code, so naming the exception the other half raises is what lets a reader tell the two failures
  apart from a log line alone. It is the same exception `### Production error policy` names.
- **`DjangoSchema(...)` over "the schema".** The review's Low suggested either; naming the class
  matches the block directly above the sentence, where `DjangoSchema` is what is constructed, and
  leaves no second bare-`Schema` spelling in the file for a later sweep to find.

### Notes for Worker 3

- The oracle for the rewritten sentence is `<scratch>/p2_ladder.py` (rows `B`, `C`, `D`, `D2`) and
  your own `<scratch>/w3_readme_verify.py` rows `D21b`-`D21f`; both are re-runnable with the
  commands above.
- The diff against HEAD is the whole cohort's, not this pass's: pass 1 is uncommitted. This pass
  changed exactly two lines of it — the `**Enforcement is configured, not installed.**` paragraph
  and the `## Schema setup` sentence after the fenced block.
- `docs/GLOSSARY.md` is untouched, deliberately: it is DB-rendered and outside this cohort's
  writable set, and your Medium is escalated to Worker 1, not dispatched here.

### Notes for Worker 1 (spec reconciliation)

- The doc fix landed against Decision 15's ladder and needs no spec edit. The Decision 21 /
  Decision 15 wording gap you and pass 1 both flagged is unchanged and still yours: spec section
  **`### Decision 21`**, current wording "a factory or subclass resolving to one refuses the
  operation". **Recommended replacement:** "a factory resolving to one refuses the operation, and a
  subclass of either extension is refused at construction". The review's caveat is right and is now
  measured: probe row `B` is a bare subclass CLASS entry that supplies no policy and is still
  refused, so "a subclass supplying a policy" would be narrower than the code.
- `docs/GLOSSARY.md`'s two `strawberry.Schema` + `extensions=[lambda: _optimizer]` recipes remain
  the open residual of the ticked row. No cohort can write it; the decision between carding a DB
  edit, narrowing the row's scope, or deferring with a named owner is yours.

---

## Review (Worker 3, pass 2)

Re-review of the apply-changes pass. The whole cohort diff was re-read, not only the two lines
pass 2 claims: `git diff HEAD -- docs/README.md README.md` — 28 insertions, 8 deletions, one file;
`README.md` (root) is still absent from the diffstat, so the plan's step 6 no-op still holds.

### Independent re-execution (pass 2)

Nothing was accepted on pass 2's record. Both probes were re-run by this reviewer from the
repository root; every row below is this run's own output, not a transcription of the build
report's.

`PYTHONPATH=examples/fakeshop uv run python <scratch>/p2_ladder.py` — exit 0:

```
OK   A exact authority instance entry: built, no DeprecationWarning, schema.extensions == ()
OK   B subclass CLASS entry: ConfigurationError at CONSTRUCTION: ResourceSubclass <class '__main__.ResourceSubclass'> subclas...
OK   C subclass INSTANCE entry: ConfigurationError at CONSTRUCTION: ErrorSubclass <__main__.ErrorSubclass object at 0x10dc9f380>...
OK   D factory resolving to an authority: schema BUILT; operation codes=['SCHEMA_CONFIGURATION_UNAVAILABLE'], data=None
OK   D2 factory resolving to a subclass: schema BUILT; operation codes=['SCHEMA_CONFIGURATION_UNAVAILABLE']
```

`PYTHONPATH=examples/fakeshop uv run python <scratch>/w3_readme_verify.py` — exit 0, twelve rows,
all `OK`: the four executable blocks (`quick start`, `schema setup`, `response debug extension`,
`production mount`) each built under `warnings.catch_warnings()` + `warnings.simplefilter("error")`
and answered `{'__typename': 'Query'}`, so **the executable blocks still build with no
`DeprecationWarning`**; rows `D21a`-`D21g` answered exactly as in pass 1.

- **The no-warning rows are non-vacuous.** The control — a plain `strawberry.Schema` with an
  optimizer INSTANCE entry under the identical filter — raised upstream's own text
  (`Passing an extension instance to `extensions=[...]` is deprecated ... issues/4369`). Row
  `D21g` shows the same warning fires on `DjangoSchema` for an ordinary instance entry, which is
  the second clause of the rewritten paragraph.
- **The probes write no tracked bytes.** `shasum -a 256 examples/fakeshop/db.sqlite3` is
  `563b26d8003c3c41072b7b7bbfc12fec524969aa3c9b258d7cdbac68ed32b52f` before the first probe and
  after the last.

### The High is closed

`docs/README.md` line 53, the `**Enforcement is configured, not installed.**` paragraph, now reads
(shipped text, read from the file rather than from the build report):

> An exact authority instance in `extensions=` is read once as that same declaration and folded
> into the schema; a factory that resolves to one instead refuses the operation with the stable
> `SCHEMA_CONFIGURATION_UNAVAILABLE` code, and a subclass of either extension — supplied as a class
> or as an instance — is refused at construction with `ConfigurationError`.

Each rung was checked against the code by reading and then by execution:

| sentence clause | code | measured |
|---|---|---|
| exact authority instance → folded, no warning | `schema.py::_consumer_extension_entries` folds the declaration and drops the entry | `A`, `D21a` — `schema.extensions == ()`, no `DeprecationWarning` |
| factory resolving to one → operation refused, `SCHEMA_CONFIGURATION_UNAVAILABLE` | `schema.py::DjangoSchema.get_extensions` refuses a resolved member claiming either role | `D`, `D2`, `D21b`, `D21e` |
| subclass, **class or instance** → `ConfigurationError` at construction | `schema.py::_declared_authority` raises on `_extension_entry_matches`, called from `_consumer_extension_entries` inside `__init__` **before** `super().__init__` | `B`, `C`, `D21c`, `D21d`, `D21f` |

`_entry_type` answers a class entry with itself and an instance entry with its type, so one
`issubclass` arm covers both spellings — which is why "supplied as a class or as an instance" is
the accurate parenthetical and why pass 2 was right to prefer it over the spec-side "a subclass
supplying a policy" (row `B` supplies nothing and is still refused). The clause no longer names a
behavior that cannot occur.

**It agrees with `### Production error policy` in the same file** on both rungs: that paragraph
(line 154, unedited) puts the subclass refusal at construction with `ConfigurationError` and lists
the operation-time refusals as factory cases only. One residual narrowness in that older paragraph
is recorded under `### Low:` below; it is not a disagreement about when either failure happens.

### High:

None. The pass-1 High is closed by delivered text and verified against the code twice — by reading
the call path and by executing all five rungs.

### Medium:

#### `docs/GLOSSARY.md` still pairs the singleton-in-a-factory with a plain `strawberry.Schema`

Unchanged and still open, **still escalated to Worker 1, and not raised as blocking here.** Both
hits confirmed still present at re-review: `docs/GLOSSARY.md` lines 752 and 946, each
`schema = strawberry.Schema(query=Query, extensions=[lambda: _optimizer])`. The file is rendered
from the glossary DB and is outside every cohort's writable set this cycle, so no worker can close
it. Resolution paths are in `### Notes for Worker 1 (spec reconciliation)` below, unchanged from
pass 1.

### Low:

#### `### Production error policy` qualifies the subclass refusal with "to supply it"

`docs/README.md` `### Production error policy` #"subclassing either extension to supply it, raise
`ConfigurationError` at construction" (line 154) is narrower than the code: a subclass entry is
refused whether or not it supplies a policy (probe rows `B` and `D21c` are bare class entries that
supply nothing). A reader could take the qualifier to mean a subclass that declares nothing is
admissible.

**Recorded and not held against this unit**, for a stated reason: the line is pre-existing at HEAD,
sits outside this cohort's diff, and this pass neither introduced nor touched it. It is the README
half of the same wording gap the Decision 21 note carries, and the accurate form is identical in
both homes — "a subclass of either extension is refused at construction" — so it is routed to
Worker 1 with that note rather than dispatched as a second re-pass over one clause. No test
expectation.

#### The pass-1 Low is closed

`docs/README.md` `## Schema setup` now reads "after the `DjangoSchema(...)` construction" (line
105), naming the class the block above constructs. **Census, as a population rather than an
absence:** a fence-tracking scan of all 915 lines of `docs/README.md` (fences balanced) finds **0**
occurrences of a bare `Schema(` in the whole file — prose and fenced blocks alike — against **11**
`DjangoSchema(`. The residue is gone.

### DRY findings

- **No new duplication in pass 2.** The pass rewrote one clause and one noun; it added no sentence
  that restates `### Production error policy`, which still owns the full statement and is still
  linked to from the rewritten paragraph.
- **The two-home hazard is unchanged and still by design.** `GOAL.md` `## Trust boundary` and
  `docs/README.md` `### The trust boundary` carry the same three levels (Decision 20 designs that),
  so `START.md` "Sweep both files of a pair" governs the next edit to either.
- **Existence challenge:** none raised. Pass 2 adds no abstraction, helper, or indirection.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` prints nothing: `__all__` and the re-export
list are unchanged. `DjangoSchema` was already a package-root export and both probes import it from
the package root, so no import line in the docs asks for an export that does not exist.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Re-run in full over `docs/README.md`.

- **Gates.** `uvx pre-commit run --files docs/README.md` — **pass** (tracked path constants,
  source layout, kanban anchors, citations all Passed; both ruff hooks `(no files to check)
  Skipped`, no Python in the diff). `uv run python scripts/check_citations.py --check` — **pass**,
  `OK: 1104 citations resolve (925 in 448 .py files, 179 in KANBAN.md).`
- **Link audit, re-run independently** (fenced blocks dropped, code spans stripped per line):
  **38** distinct `][label]` uses over 39 occurrences and **38** definitions, **0** uses without a
  definition, **0** definitions without a use; all ten group headers present in one block and in
  the canonical order; every group alphabetical; every relative definition target resolves on disk.
  The three in-page links (`#production-error-policy`, `#production-security-profile`,
  `#visibility-and-permissions`) all name live headings. Pass 2 added and removed no link, as it
  claims.
- **`strawberry.Schema` census.** **3** surviving occurrences in `docs/README.md`, at lines 59, 124
  and 204, **all in prose**, **0** inside any fenced block — each a deliberate contrast with plain
  Strawberry. `README.md` (root): **0** of any kind.
- **No process provenance introduced.** A case-insensitive sweep of the diff's **added lines** for
  `previously`, `no longer`, `as of `, `round N`, `Decision N`, `Slice N`, `spec-0`, `worker`,
  severity labels (`High:`/`Medium:`/`Low:`/`P0`/`H<n>`) returns **zero** hits. The prose is in the
  README's own voice.
- **Version strings and shipped statuses.** Untouched by this pass and outside the diff. No spec
  file is moved; no script-rendered doc is regenerated; no "coming soon" / "planned" wording is in
  the rewritten region.

### Spec slice checklist walk

All three boxes remain `- [x]` and each tick still has a matching change in the diff. Box 1 (state
the trust and extension contracts) is now delivered by text that is **true** as well as present —
the pass-1 finding was a correctness defect inside a landed row, and it is closed. Box 2 (correct
the executable examples) is re-verified by the census above and by executing all four blocks. Box 3
is landed subject only to the escalated glossary residual. No box is silently unaddressed; no box
is ticked without a matching change.

### Failability proofs

The build report records `None; this pass introduced no new boundary.` **Audited and agreed:** pass
2 changed one clause and one noun inside a Markdown file, adding no guard, cap, rejection path or
validation branch. The mandatory re-run set is therefore empty, which `worker-3.md` permits only
when the diff introduces no boundary meeting the floor; that condition holds. **Boundaries re-run:
none. Boundaries accepted on Worker 2's record: none — there are none to accept.**

The behavioral claims the new prose makes are about code the diff does not touch, so they were
verified the way `worker-3.md` "Claim verification" requires: by tracing `_declared_authority` →
`_consumer_extension_entries` → `DjangoSchema.__init__` and `DjangoSchema.get_extensions`, and by
executing all five rungs. No earlier branch swallows either path — `_consumer_extension_entries`
runs before `super().__init__`, which is precisely why the construction-time half can never reach
`get_extensions`.

### Hot-path budget verification

Plan declares this cohort `none`, and the diff adds no runtime code. Nothing owed, nothing missing.

### Static helper use

`scripts/review_inspect.py` **skipped, deliberately**: `BUILD.md` `### When to run the helper during
build` triggers on new `.py` files, files under `optimizer/` or `types/`, and line thresholds of new
logic. This diff touches one `.md` file and zero `.py` files.

### Test staleness

Re-run independently of the artifact's file list: `grep -rn "docs/README"` across `tests/`,
`examples/` and `scripts/` finds no reader, so no test, fixture or generator asserts this file's
content and the doc edit strands nothing. No wire-shape or model-field change is in the diff.

### What looks solid

- **The fix is a real bound, not a relabelled one.** The sentence now names a different failure
  *time* and a different *exception* for the subclass rung than for the factory rung, and both are
  measured. A reader can tell the two apart from a log line alone, which is what the old single
  clause made impossible.
- **Pass 2 chose the broader accurate form over the spec's own words.** "supplied as a class or as
  an instance" is wider than Decision 21's "a subclass supplying a policy", and row `B` is the
  evidence that the wider form is the correct one. A pass that had copied the spec verbatim would
  have shipped a second, subtler version of the same defect.
- **The Low was fixed by naming the class, not by deleting the sentence.** `DjangoSchema(...)`
  matches the block directly above it and leaves no bare-`Schema` spelling in the file for a later
  sweep to trip on — census 0.
- **Nothing outside the cohort moved.** One file in the diffstat; `__init__.py` clean; the tracked
  sqlite digest identical across four probe runs.

### Temp test verification

- No temp test was written under `docs/builder/temp-tests/050/trust_docs/` this pass either. The
  instrument this review needs is an executable transcription of shipped doc text, which belongs
  outside the repo; `<scratch>/w3_readme_verify.py` and `<scratch>/p2_ladder.py` are both
  re-runnable with the commands above.
- Disposition: not promoted, not kept in-tree. Every property they exercise is `DjangoSchema`
  behavior already pinned by the package suite; their job is to check the *documentation* against
  it.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (unchanged from pass 1): `docs/GLOSSARY.md` carries the residual of the row this
  cohort ticked.** Two hits, `docs/GLOSSARY.md` lines 752 and 946, both
  `strawberry.Schema(query=Query, extensions=[lambda: _optimizer])`, both the spec row's own
  description of the shape to correct. Resolution paths, ranked as before: (a) card the two
  `GlossaryTerm.body` edits + regenerate in the close cycle's remaining work, since the board DB is
  already being touched at "Record and card"; (b) declare the row's scope to be `docs/README.md`
  only and record the glossary as deferred with a named owner for `BUILD.md`
  `### Deferred work catalog`; (c) leave it, which reopens `START.md`'s "partial claim fix" hazard.
  Not a worker's call.
- **Escalated: Decision 21's compressed clause still needs the construction-time refusal spelled
  separately, and the accurate form is now measured.** Spec `### Decision 21` says "a factory or
  subclass resolving to one refuses the operation"; Decision 15's ladder in the same spec says a
  subclass is a construction-time `ConfigurationError`. The code answers with Decision 15 (rows
  `B`, `C`, `D21c`, `D21d`, `D21f`), so **yes — the two halves must be stated separately**, and
  Worker 2's flag is correct. Recommended replacement, as both Worker 2's pass-2 note and this
  review independently reach it: *"a factory resolving to one refuses the operation, and a subclass
  of either extension is refused at construction"*. Do **not** write "a subclass supplying a
  policy": probe row `B` is a bare subclass class entry that supplies nothing and is still refused,
  so that form is narrower than the code. This is a `START.md` "five homes per contract" defect
  between Decisions 15 and 21; the README no longer depends on its resolution either way.
- **The README half of the same gap, for the same sweep.** `docs/README.md`
  `### Production error policy` (line 154) says "subclassing either extension **to supply it**,
  raise `ConfigurationError` at construction". Same narrowness, same accurate form. It is
  pre-existing at HEAD and outside this cohort's diff, so it is recorded as a Low with its
  rejection reason rather than dispatched; if Decision 21 is amended, this clause is the one other
  site that should move with it (`START.md` "Sweep both files of a pair").
- No other spec amendment is owed by this cohort.

### Review outcome

`review-accepted`. The High is closed and verified twice, by reading the call path and by executing
all five rungs; the Low is closed with a census of 0; the pass introduced no boundary, no public
surface change, no process provenance and no link drift, and both markdown gates pass. Two items
leave with Worker 1, neither holding this unit: the `docs/GLOSSARY.md` residual (outside every
cohort's writable set) and the Decision 21 / Decision 15 wording split, with its README twin.

---

## Final verification (Worker 1)

Diff under verification: `git diff HEAD -- docs/README.md README.md` — 28 insertions, 8 deletions,
one file. `README.md` (root) is absent from the diffstat, so the plan's step 6 no-op holds at this
pass too, re-derived rather than read off the build report: `grep -c 'strawberry\.Schema\|extensions=\['
README.md` returns **0**.

Nothing below is accepted on Worker 2's or Worker 3's record. Both prior probes were re-run, and a
third instrument was written for this pass because both of theirs share one weakness: each
TRANSCRIBES the doc's fenced blocks by hand, so both would pass identically against a block whose
shipped bytes differ from the transcription. The new probe extracts the blocks from
`docs/README.md` at run time and executes those.

### Re-derived evidence

`<scratch>/w1_readme_exec.py`, run from the repository root as
`PYTHONPATH=examples/fakeshop uv run python <scratch>/w1_readme_exec.py` — exit 0. It parses
`docs/README.md`, tracks fences, and executes the extracted blocks in a real module registered in
`sys.modules` (a bare dict namespace cannot resolve `list[ItemType]`, and that harness limitation
reads exactly like a doc defect if it is not removed). Only the documented `myapp` Category/Item →
`apps.library` Branch/Shelf stand-in is substituted, and each substitution is applied only where its
exact source string is present.

```
OK   fences balanced: 26 python blocks extracted
OK   schema-constructing block census: 'Quick start'@18; 'Schema setup'@95;
     '`DjangoSchema` is required for generated mutations'@113; 'Production error policy'@139;
     'The production GraphQL mount'@652; 'Response debug extension'@735
OK   no fenced block constructs a plain strawberry.Schema: offenders=[]
OK   quick start block: line 18: DjangoSchema built, no DeprecationWarning, {'__typename': 'Query'}
OK   schema setup block: line 95: DjangoSchema built, no DeprecationWarning, {'__typename': 'Query'}
OK   response debug extension block: line 735: DjangoSchema built, no DeprecationWarning, {'__typename': 'Query'}
OK   CONTROL plain Schema + instance entry: Passing an extension instance to `extensions=[...]` is deprecated and 
```

- **The census is a population, and it is complete rather than sampled:** **six** fenced blocks in
  `docs/README.md` construct a schema, and **zero** of them construct a plain `strawberry.Schema`.
  That is a stronger instrument than a line grep for `strawberry.Schema`, which cannot say whether a
  hit is inside a fence. It also caught its own first version: `re.search(r"\bSchema\(")` matches
  nothing in `DjangoSchema(` — there is no word boundary between `o` and `S` — and reported **0**
  schema blocks, which reads exactly like a finished sweep. Stated because the same regex shape is
  what a later census of this file would reach for.
- **The no-warning rows are non-vacuous.** The control constructs a plain `strawberry.Schema` with
  an optimizer INSTANCE entry under the identical `simplefilter("error")` and raises upstream's own
  text. Without it the three OK rows would pass with the filter absent.
- The three prior probes were re-run unchanged and all exit 0:
  `<scratch>/verify_readme_examples.py` (4 rows), `<scratch>/w3_readme_verify.py` (12 rows,
  `D21a`-`D21g`), `<scratch>/p2_ladder.py` (5 rows, `A`-`D2`).
- **No tracked bytes written.** `shasum -a 256 examples/fakeshop/db.sqlite3` is
  `563b26d8003c3c41072b7b7bbfc12fec524969aa3c9b258d7cdbac68ed32b52f` before the first probe of this
  pass and after the last.

### The authority ladder, re-derived

`<scratch>/w1_ladder.py` was written from the code (`django_strawberry_framework/schema.py::_declared_authority`,
`django_strawberry_framework/schema.py::_consumer_extension_entries`,
`django_strawberry_framework/schema.py::DjangoSchema.get_extensions`), not from either prior probe,
and exits 0:

```
OK   1 exact authority instance entry: built, no DeprecationWarning, schema.extensions=(), data={'ping': 'pong'}
OK   2 subclass CLASS entry (supplies nothing): ConfigurationError: ResourceSub <class '__main__.ResourceSub'> subclasses the pa
OK   3 subclass INSTANCE entry: ConfigurationError: ErrorSub <__main__.ErrorSub object at 0x...> subclasse
OK   4 factory -> exact authority: schema BUILT; operation codes=['SCHEMA_CONFIGURATION_UNAVAILABLE']
OK   5 factory -> authority subclass: schema BUILT; operation codes=['SCHEMA_CONFIGURATION_UNAVAILABLE']
OK   6 ordinary instance entry on DjangoSchema: DeprecationWarning (upstream's own text)
OK   CONTROL plain Schema + instance entry: DeprecationWarning (upstream's own text)
```

Row `2` is the load-bearing one: a bare subclass CLASS entry declaring **nothing** is still refused
at construction, so "a subclass supplying a policy" is narrower than the code in either home. Read
against the source, `_declared_authority` raises on `_extension_entry_matches`, and `_entry_type`
answers a class entry with itself and an instance entry with its type, so one `issubclass` arm
covers both spellings; it is called from `_consumer_extension_entries` at the first statement of
`DjangoSchema.__init__`, before `super().__init__`, so a directly supplied subclass never reaches
`get_extensions` and no operation is ever refused for one.

### Spec slice checklist audit

Every `- [x]` was checked against the diff, not against the build report.

1. *State the trust contract … and the extension contract …* — **stands.** `### The trust boundary`
   carries Decision 20's three levels, the Django feasibility line and the beyond-upstream
   guarantees; the three paragraphs under `## Quick start` carry Decision 21's three parts, each
   clause of the row's enumeration present: the `resource_policy=` / `error_policy=` declaration,
   class-or-factory for ordinary extensions, the instance spelling on upstream's deprecation
   (measured, row `6`), and per-operation isolation with the singleton-in-a-factory recipe named.
2. *Correct the executable examples …* — **stands for the two files this cohort owns**, on the
   fenced census above (six schema blocks, zero plain `strawberry.Schema`) rather than on a line
   grep. The row's own description also matches sites in `docs/GLOSSARY.md`, which no cohort may
   write; those are routed below rather than left as a silent over-tick.
3. *The shipped docs state the trust contract where a deployer reads it …* — **stands.** Each clause
   this row enumerates is delivered in `docs/README.md`. The clause corrected below is not one of
   them; it is the fuller refusal statement in `### Production error policy`, which this row does
   not enumerate but which the file must not contradict.

No box is ticked without a matching change, and no box is left `- [ ]`.

### Planned steps

Steps 1-5 landed at the plan's named sites, verified in the diff. Step 6 (root `README.md` no-op)
was re-derived here and holds. Step 7 (link scaffold) was re-audited independently below. No planned
step was rejected or silently dropped.

### Gates

- `uvx pre-commit run --files docs/README.md` — **pass** (tracked path constants, source layout,
  kanban anchors, citations Passed; both ruff hooks `(no files to check) Skipped`).
- `uv run python scripts/check_citations.py --check` — **pass**,
  `OK: 1104 citations resolve (925 in 448 .py files, 179 in KANBAN.md).`
- Link audit, this pass's own script (fences dropped, code spans stripped **per line**):
  `docs/README.md` **38** distinct `][label]` uses / **38** definitions, 0 missing, 0 unused, 0
  duplicate labels, all ten group headers present in canonical order, every group alphabetical,
  every relative target resolving on disk. All four in-page links (`#production-error-policy` ×2,
  `#production-security-profile`, `#visibility-and-permissions`) name live headings. `README.md`:
  21 / 21, 0 orphans; its `<!-- External -->` group is **not** alphabetical
  (`license-url` → `changelog-image`), which is pre-existing at HEAD in a file this cohort did not
  touch — confirmed by its absence from the diffstat — and is not a finding against this unit.
- Process-provenance sweep over the diff's **added lines** for `previously`, `no longer`, `as of `,
  `round N`, `Decision N`, `Slice N`, `spec-0`, `worker`, severity labels, `coming soon`, `planned`
  — **0** hits.
- Staged-anchor sweep: `grep -rn 'TODO(spec-050' --include='*.py' --include='*.md' .` returns **2**
  hits, both prose about anchors in per-cycle artifacts (`docs/bug_hunt/bug_hunt-0_0_1555.md`, and a
  historical count in `docs/builder/DONE/build-038-form_mutations-0_0_12.md`). **No live
  `TODO(spec-050 slice N)` source anchor exists**, so this slice strands none.
- Focused existing tests: the plan calls for none — this cohort ships no executable behavior — and
  the executed-example and ladder probes above are the instruments in their place. No `pytest`
  invocation was run in this pass and no `--cov*` flag was used anywhere.

### Failability, hot path, floor, DRY

- **Failability proofs.** Both build reports record `None; this pass introduced no new boundary.`
  **Confirmed by reading the diff**, not by trusting the record: it adds no guard, cap, rejection
  path or validation branch — it is prose plus schema-class substitutions in three fenced blocks and
  one new link definition. The obligation is therefore empty rather than sampled.
- **No fail-open shape landed.** There is no expression in the diff to fail open; the diff contains
  no Python.
- **Hot path.** Plan declares `none`; the diff adds no runtime code. Nothing owed.
- **Floor verification.** The plan assigns this cohort no floor run; the twenty-three-path scope is
  the final gate's. Nothing owed here.
- **DRY across accepted units.** The trust contract deliberately has two homes (`GOAL.md`
  `## Trust boundary` owns it; `docs/README.md` `### The trust boundary` states it as the package's
  own for a deployer), which Decision 20 designs. The README version is not a copy — no four-layer
  table, a `## Visibility and permissions` pointer added, deployer voice — so there is nothing to
  consolidate, and the standing obligation is `START.md` "Sweep both files of a pair" on the next
  edit to either. The quick-start paragraphs point at `### Production error policy` rather than
  restating it. No new duplication found against Cohort A's diff, which touches no documentation.

### The one finding that holds this unit

#### `docs/README.md` `### Production error policy` states the subclass refusal narrower than the code

`docs/README.md` `### Production error policy` #"subclassing either extension to supply it, raise
`ConfigurationError` at construction" is **false as written**. The qualifier "to supply it" makes
the refusal conditional on the subclass declaring a policy; measured, a bare subclass class entry
that declares nothing is refused identically (`<scratch>/w1_ladder.py` row `2`), and the code has no
arm that reads what a subclass supplies before refusing it — `_declared_authority` raises on the
`issubclass` result alone. A reader can take the sentence to mean a subclass that declares nothing
is admissible; it is not, and the schema will not build.

Worker 3 recorded this as a Low and did not hold the unit on the grounds that it is pre-existing at
HEAD and outside the diff. That reasoning is sound for a review of a diff and is the wrong frame at
final verification, for two reasons this pass can see and a review pass could not:

1. `docs/README.md` is this cohort's own file, and the new `## Quick start` paragraph now states the
   accurate ladder three paragraphs above it. One file carrying two readings of one contract is the
   `START.md` "Sweep both files of a pair" / "partial claim fix" hazard in its sharpest form, and the
   cohort created the pairing.
2. Decision 21 and Decision 15's ladder were corrected in this pass (below). The shipped doc is the
   other home of the same claim and owes the same move in the same pass, or the spec and the docs
   disagree about which is current.

Worker 1's writable set (`docs/builder/worker-1.md` `## Scope`) does not include `docs/README.md`,
so this is dispatched rather than fixed here. It is one clause with a fixed replacement.

**Exact replacement for Worker 2.** In `docs/README.md` `### Production error policy`, replace:

> Declaring the policy twice, and subclassing either extension to supply it, raise `ConfigurationError` at construction - a subclass can override the hook that does the enforcing while still answering every check for it.

with:

> Declaring the policy twice raises `ConfigurationError` at construction, and so does a subclass of either extension - supplied as a class or as an instance, and whether or not it declares a policy of its own - because a subclass can override the hook that does the enforcing while still answering every check for it.

Nothing else in that paragraph changes; its next sentence already lists the operation-time refusals
as factory cases only, which is correct. The replacement matches the quick-start paragraph's
"supplied as a class or as an instance" and the amended Decision 21, so the file, the spec and the
code then state one ladder.

Expectation after the fix: `<scratch>/w1_ladder.py` rows `2` and `3` are the oracle for the
construction-time half and rows `4` and `5` for the operation-time half; the census of a bare
`Schema(` stays **0**; the link audit is unchanged (the edit adds and removes no link).

### Final status

`revision-needed`. Everything else in this cohort is verified and stands: the three checklist boxes,
the executable examples under a complete fenced census, the trust subsection, the corrected
quick-start ladder, both markdown gates, and an unchanged tracked sqlite digest. One clause in the
cohort's own file is false as written and is dispatched above with its exact replacement.

### Summary

Cohort B rewrote every schema-constructing example in `docs/README.md` onto `DjangoSchema`, replaced
the quick-start extension paragraph with Decision 21's three separate rules, and added
`### The trust boundary` under `## Production security profile` stating Decision 20's three trust
levels in the README's own voice. Root `README.md` is untouched, on evidence. Two items outlive the
cohort: one correction dispatched to Worker 2 (above) and the `docs/GLOSSARY.md` residual routed to
Worker 0 (below).

### Spec changes made (Worker 1 only)

Three edits, all to `docs/spec-050-list_field_arguments-0_0_15.md`, triggered by this cohort's
finding that Decision 21 compressed two different refusals into one clause. Verified against
`django_strawberry_framework/schema.py::_declared_authority` and
`django_strawberry_framework/schema.py::DjangoSchema.get_extensions` and measured by
`<scratch>/w1_ladder.py` before being written. Each is a clean current contract: no chronology, no
amendment block, no record of what the sentence used to say.

1. **`### Decision 21`, the `**Enforcement is configured, not installed.**` paragraph (line 1716
   region).** The clause "and a factory or subclass resolving to one refuses the operation" is
   replaced by the two rungs stated separately: a subclass of either authority is refused at schema
   construction with `ConfigurationError`, supplied as a class or as an instance and whether or not
   it supplies a policy of its own; only a factory is opaque until called, so a factory resolving to
   an authority, subclasses included, is the one spelling refused at the operation, with the stable
   `SCHEMA_CONFIGURATION_UNAVAILABLE` code. Reason: the old clause named a behavior that cannot
   occur (a directly supplied subclass never reaches `get_extensions`) and contradicted Decision 15's
   ladder in the same spec — a `START.md` "five homes per contract" defect.
2. **`### Decision 15`, the admission-ladder table (lines 1541-1542).** Two rungs widened to what
   the code answers: `subclass of an authority, as a class or as an instance` and
   `factory resolving to either authority, subclasses included`. Reason: the table's final rung
   ("any other class, instance or factory … runs between the two authorities") would otherwise
   claim a factory resolving to a SUBCLASS is admitted; row `5` measures it refused, and
   `DjangoSchema.get_extensions` refuses "a member of either enforcement kind … subclasses
   included".
3. **`## Definition of done`, the "No policy object a resolver can name" row (line 2776 region).**
   "and an entry that resolves into one refuses the operation instead" is replaced by "A subclass
   supplied directly, as a class or as an instance, is refused with `ConfigurationError` at
   construction, and an entry that RESOLVES into one refuses the operation instead." Reason: the
   row's own enumeration names a subclass among the things no resolver can reach, then attached the
   operation-time answer to all of them. Found by the five-homes sweep the Decision 21 edit owed.

**Homes swept, and the ones that needed nothing.** `## Slice checklist` Slice 5's two rows and the
Definition-of-done row "The shipped docs state the trust contract" were each read against the code
for the same narrowness and carry **none** — neither enumerates the refusal ladder, so neither
required an edit. `## Edge cases and constraints` and `## Test plan` carry no restatement of it
(`grep -n 'refuses the operation\|resolving to one'` over the spec returns only the three sites
above plus `#"A schema that can no longer read its own configuration back refuses the operation"`,
which is the unrelated unreadable-record case).

**Rationale file: no edit.** `docs/spec-050-list_field_arguments-0_0_15-rationale.md`
`### Decision 21` and `### Decision 15` were read in full. Nothing in either is falsified by these
edits — the rejected package-defined instance semantics, the rejected "move the instance into a
factory" migration, the rejected identity-deduplication and the rejected subclass admission all
read correctly against the corrected contract — and rule 2 of the move forbids relocating prose the
decisions have falsified rather than deleting it, which does not arise. The one-line pointers from
both Decisions still resolve.

**Status-line re-verification.** The spec's opening lines were re-read this spawn. They describe the
build's current state and needed no edit; the header's Decision 21 summary ("the extension contract
is upstream's class-or-factory spelling with per-operation isolation stated as the guarantee this
package adds") is unaffected by the ladder correction.

### Notes for Worker 1 (spec reconciliation)

The escalations routed to this pass, with the custodian's disposition. The two glossary items stay
routed: `docs/GLOSSARY.md` is rendered from the glossary DB and is outside every cohort's writable
set this cycle, so the edits are `GlossaryTerm.body` edits for **Worker 0's "Record and card" step**
(`docs/builder/DONE/build-050-list_field_arguments-0_0_15.md` `## Close cycle (Decision 22)`), which
already touches the board DB and regenerates the four generated docs. Path (a) of Worker 3's ranking
is taken; the row is **not** deferred to another card and **not** narrowed in scope, so no
`### Deferred work catalog` entry is owed and the spec row stands as written.

**The escalation's own census had a blind spot; this is the corrected population.** Worker 3 swept
for the exact fenced string `schema = strawberry.Schema(query=Query, extensions=[lambda: _optimizer])`
and found two hits. A sweep for `strawberry.Schema` across `docs/GLOSSARY.md` finds the row's
described pairing at **four** sites, two of which that instrument could not see: one is an INLINE
code span rather than a fenced block, and one spells the call across multiple lines. Sites that
merely mention `strawberry.Schema` in prose (a deliberate contrast, or the standalone use the
package supports) are out of scope and are listed at the end.

1. **`## `DjangoOptimizerExtension`` body** (rendered line 752). Replace the fenced block

   ```python
   _optimizer = DjangoOptimizerExtension()
   schema = strawberry.Schema(query=Query, extensions=[lambda: _optimizer])
   ```

   with

   ```python
   from django_strawberry_framework import DjangoOptimizerExtension, DjangoSchema

   _optimizer = DjangoOptimizerExtension()
   schema = DjangoSchema(query=Query, extensions=[lambda: _optimizer])
   ```

   The sentence under it ("Use a module-level singleton wrapped in a factory — that preserves the
   instance-bound Plan cache … and emits no deprecation warning") stays true as written and needs no
   edit.

2. **`## `finalize_django_types`` body** (rendered line 946). Replace the fenced block

   ```python
   from django_strawberry_framework import finalize_django_types
   import apps.products.schema  # registers DjangoType subclasses
   import apps.library.schema

   finalize_django_types()

   _optimizer = DjangoOptimizerExtension()
   schema = strawberry.Schema(query=Query, extensions=[lambda: _optimizer])
   ```

   with

   ```python
   from django_strawberry_framework import DjangoOptimizerExtension, DjangoSchema, finalize_django_types
   import apps.products.schema  # registers DjangoType subclasses
   import apps.library.schema

   finalize_django_types()

   _optimizer = DjangoOptimizerExtension()
   schema = DjangoSchema(query=Query, extensions=[lambda: _optimizer])
   ```

   The import line gains `DjangoOptimizerExtension`, which the shipped block uses without importing
   — the same gap Worker 2 closed in `docs/README.md` `## Schema setup`. The sentence above the
   block ends "before `strawberry.Schema(...)` is constructed:"; replace that clause with "before
   the schema is constructed:", matching the construction-order sentence in `docs/README.md`, since
   the rule is about ordering rather than about which schema class is used.

3. **`## BigInt scalar` body** (rendered line 341) — **the site the escalation's census could not
   see**, because the recipe is an inline code span, not a fenced block. Replace

   > Consumers register `BigInt` via the [`strawberry_config`](#strawberry_config) factory on their `strawberry.Schema(...)` call: `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[lambda: _optimizer])`

   with

   > Consumers register `BigInt` via the [`strawberry_config`](#strawberry_config) factory on their schema call: `DjangoSchema(query=Query, config=strawberry_config(), extensions=[lambda: _optimizer])`

   The rest of that sentence — the parenthetical naming the singleton-in-a-factory and pointing at
   `DjangoOptimizerExtension` — is unchanged.

4. **`## strawberry_config` body, its FIRST fenced block** (rendered line 1978) — **a fourth site
   named by neither the escalation nor its ranking**, matching the spec row's description exactly.
   Replace

   ```python
   from django_strawberry_framework import strawberry_config

   _optimizer = DjangoOptimizerExtension()
   schema = strawberry.Schema(
       query=Query,
       config=strawberry_config(),
       extensions=[lambda: _optimizer],
   )
   ```

   with

   ```python
   from django_strawberry_framework import DjangoOptimizerExtension, DjangoSchema, strawberry_config

   _optimizer = DjangoOptimizerExtension()
   schema = DjangoSchema(
       query=Query,
       config=strawberry_config(),
       extensions=[lambda: _optimizer],
   )
   ```

   The lead-in sentence ends "into their `strawberry.Schema(...)` call."; replace that clause with
   "into their schema call.". The body's two OTHER fenced blocks (`extra_scalar_map=` and the
   `auto_camel_case` / `relay_max_results` passthrough) carry **no** `extensions=` entry, so they are
   outside the row's description and are left alone unless the maintainer wants one spelling
   throughout that entry — a decision, not a defect.

**Both replacement shapes were executed, not reasoned.** `DjangoSchema(query=Query,
extensions=[lambda: _optimizer])` and `DjangoSchema(query=Query, config=strawberry_config(),
extensions=[lambda: _optimizer])` were each built under `warnings.catch_warnings()` +
`simplefilter("error")` and answered a query; both exit clean with no `DeprecationWarning`, and
`examples/fakeshop/db.sqlite3` is byte-identical across the run.

**Out of the row's scope in `docs/GLOSSARY.md`, named for population completeness, no action asked:**
prose mentions of `strawberry.Schema` at rendered lines 48, 578, 588, 732, 785, 863, 936, 968, 1228,
1364, 1529, 1863, 1972 — each is either a deliberate contrast with plain Strawberry, a statement of
the standalone use the package supports, or a construction-order sentence. `## Per-operation
extension isolation` (line 1529) was re-read in full against the amended Decision 21 and **agrees
with it**, the subclass refusal included: it already says "a factory returning either enforcement
extension" is what fails closed on the wire, and states the class-and-factory spellings for
everything that is not an authority. No glossary body contradicts the corrected ladder.

`examples/fakeshop/test_query/README.md` #"schema = strawberry.Schema(query=Query, extensions=[lambda: ext])"
is a plan-cache test illustration rather than a consumer recipe, and that file is baseline-dirty from
the concurrent session. Named for completeness; no action asked.

---

## Build report (Worker 2, pass 3)

Apply-changes pass over `### The one finding that holds this unit`. One sentence in
`docs/README.md` `### Production error policy` was replaced with the exact replacement the final
verification dispatched. Nothing else was edited: the glossary residual stays routed to Worker 0's
"Record and card" step, and the spec edits are Worker 1's own and are not this pass's to touch.

### Files touched

`git status --short` names one file this pass: `docs/README.md` (plus this artifact and the
untracked `docs/builder/worker-memory/050-worker-2.md`). One edit, one line.

`docs/README.md` `### Production error policy`, the paragraph beginning #"The schema owns both, and ".
Replaced verbatim from the dispatch:

> Declaring the policy twice raises `ConfigurationError` at construction, and so does a subclass of either extension - supplied as a class or as an instance, and whether or not it declares a policy of its own - because a subclass can override the hook that does the enforcing while still answering every check for it.

The rest of that paragraph is byte-unchanged, including the next sentence listing the operation-time
refusals as factory cases only.

### Tests added or updated

None. This cohort ships no executable behavior; the ladder probe below stands in.

### Verification of the rewritten sentence against the code

Read first, then executed. `django_strawberry_framework/schema.py::_declared_authority` walks the
two authority types and, for each, returns only on an EXACT type match
(#"if _entry_type(entry) is extension_type"); anything that is a strict subclass falls to
#"if _extension_entry_matches(entry, extension_type)" and raises `ConfigurationError` there.
`schema.py::_entry_type` answers a class entry with itself and an instance entry with its type, so
the single `issubclass` arm in `schema.py::_extension_entry_matches` covers both spellings, and the
raise is reached **before** anything reads what the entry declares — `schema.py::_entry_resource_policy`
is called only on the exact-match path, after `_declared_authority` has returned. `_declared_authority`
is called from `schema.py::_consumer_extension_entries`, which runs inside `DjangoSchema.__init__`
before `super().__init__`, so the refusal is construction-time and the schema never builds. There is
no arm that reads a supplied policy before refusing a subclass, which is exactly what the retired
qualifier "to supply it" implied.

- Probe: `<scratch>/p3_subclass_ladder.py`, run from the repository root as
  `PYTHONPATH=examples/fakeshop uv run python <scratch>/p3_subclass_ladder.py`, with
  `os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")` and `django.setup()`.
  Written from the code for this pass, not re-run from an earlier pass's script.
- Result, exit 0:

  ```
  OK   1 resource subclass, CLASS entry, supplies nothing: ConfigurationError at CONSTRUCTION: ResourceSubBare <class '__main__.ResourceSubBare'> subclasses the pack...
  OK   2 resource subclass, INSTANCE entry, supplies nothing: ConfigurationError at CONSTRUCTION: ResourceSubBare <__main__.ResourceSubBare object at 0x...> subcl...
  OK   3 resource subclass, INSTANCE entry, SUPPLIES a policy: ConfigurationError at CONSTRUCTION: ResourceSubSupplying <__main__.ResourceSubSupplying object at 0x...
  OK   4 error subclass, CLASS entry, supplies nothing: ConfigurationError at CONSTRUCTION: ErrorSubBare <class '__main__.ErrorSubBare'> subclasses the package's ...
  OK   5 error subclass, INSTANCE entry, supplies nothing: ConfigurationError at CONSTRUCTION: ErrorSubBare <__main__.ErrorSubBare object at 0x...> subclasses ...
  OK   CONTROL a exact authority INSTANCE entry: built, data={'ping': 'pong'}
  OK   CONTROL b exact error-authority CLASS entry: built, data={'ping': 'pong'}
  OK   CONTROL c unrelated extension CLASS entry: built, data={'ping': 'pong'}
  OK   all rows
  ```

  Rows `1`-`5` are the clause's own enumeration, one row per rung: **either** authority, **class or
  instance**, **supplying a policy or supplying nothing**. Row `3` is the one the retired wording
  got right by accident and rows `1`, `2`, `4`, `5` are the ones it got wrong.
- **The refusal rows are not vacuous.** A test asserting "construction raises" passes identically if
  construction raises for every entry, so the three controls build a schema and answer `{ ping }`:
  an exact authority instance entry, an exact error-authority class entry, and an unrelated
  `SchemaExtension` subclass. All three build under `warnings.catch_warnings()` +
  `simplefilter("error")`, so the entry shapes the sentence does **not** condemn are proved
  admissible on the same instrument.
- The probe writes no tracked bytes: `shasum -a 256 examples/fakeshop/db.sqlite3` is
  `563b26d8003c3c41072b7b7bbfc12fec524969aa3c9b258d7cdbac68ed32b52f` before and after the run,
  matching every earlier pass's digest.

### Validation run

- `uv run ruff format` / `uv run ruff check --fix` — not applicable; this pass touched no Python
  inside the repository (the probe lives in the session scratchpad). Both hooks report
  `(no files to check) Skipped` below for the same reason.
- `uvx pre-commit run --files docs/README.md` — **pass**: `kanban tracked path constants` Passed,
  `source layout` Passed, `ruff format` Skipped, `ruff check` Skipped, `kanban anchors` Passed,
  `citations resolve` Passed.
- `uv run python scripts/check_citations.py --check` — **pass**:
  `OK: 1104 citations resolve (925 in 448 .py files, 179 in KANBAN.md).`
- **Diff delta since the prior build report, stated as the whole cohort diff either side of this
  pass.** `git diff HEAD --stat -- docs/README.md README.md` read 28 insertions / 8 deletions before
  the edit and 29 / 9 after: one line replaced, no other hunk added or removed, and `README.md`
  (root) is still absent from the diffstat. The changed line is the paragraph quoted above, confirmed
  by filtering the diff's `+`/`-` lines for #"Declaring the policy twice".
- **No process provenance in the new sentence.** It carries no `now`, `no longer`, `previously`,
  `as of `, round or worker label, card id or spec id; it states the construction-time refusal as a
  standing rule in the README's own voice. Sweep over the added line for those tokens: 0 hits.
- Census, stated as a population rather than an absence: a fence-tracking scan of `docs/README.md`
  (fences balanced) finds **3** `strawberry.Schema` occurrences, at lines 59, 124 and 204, **all in
  prose** and **0** inside any fenced block; **0** occurrences of a bare `Schema(` anywhere in the
  file, against **11** `DjangoSchema(`. Both figures are unchanged by this pass, which edited prose
  only and touched no fenced block.
- Links: this pass added and removed no `][label]` use and no definition, so the accepted audit (38
  uses / 38 definitions, 0 orphans either way, ten group headers in canonical order, every group
  alphabetical) still describes the file. The edited paragraph contains no link.
- `git status --short` — no path outside this cohort's writable set appeared, and no path that was
  clean at the start of this pass became dirty. The entries are the plan's baseline-dirty set plus
  `docs/README.md` and this artifact. Nothing was reverted. `django_strawberry_framework/utils/querysets.py`,
  `django_strawberry_framework/permissions.py`, `django_strawberry_framework/resource_policy.py`,
  `django_strawberry_framework/types/resolvers.py`, `tests/utils/test_querysets.py`,
  `tests/test_resource_policy.py` and the three `examples/fakeshop/test_query/` modules are the
  concurrent cohort's and the concurrent session's. Reported, not touched.

### Failability proofs

None; this pass introduced no new boundary. The edit is one prose sentence in a documentation file.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; the plan's floor-verification scope assigns this cohort no run.

### Implementation notes

- **The dispatched replacement was written verbatim, not paraphrased.** It already carries the
  parenthetical shape the quick-start paragraph uses ("supplied as a class or as an instance"), so
  the two statements in this file now read as one ladder, and the ASCII hyphen dashes match the
  surrounding paragraph's existing punctuation rather than introducing an em dash into a sentence
  the rest of the paragraph does not use one in.
- **"whether or not it declares a policy of its own" earns its length.** It is the clause that
  retires the false qualifier rather than merely dropping it: a reader who took "to supply it" to
  license a bare subclass gets an explicit answer instead of silence. Probe rows `1`, `2`, `4` and
  `5` are what it is asserting.

### Notes for Worker 3

- No re-review is expected on this pass — the dispatch came from final verification, so this returns
  to Worker 1. The oracle for the rewritten sentence is `<scratch>/p3_subclass_ladder.py`, rows `1`-`5`
  for the refusal and the three controls for the admissible shapes.
- The edit is one line of prose. No fenced block changed, so the executable-block census and every
  executed-example result recorded in the earlier passes still describe the shipped bytes.

### Notes for Worker 1 (spec reconciliation)

- No spec amendment is owed by this pass. The replacement was dispatched with its wording fixed and
  is now the same ladder as the amended `### Decision 21`, `### Decision 15` and the `## Definition
  of done` row, and as `## Quick start` in this file.
- The `docs/GLOSSARY.md` residual is untouched and stays where final verification routed it: the
  four `GlossaryTerm.body` edits are Worker 0's "Record and card" step, outside every cohort's
  writable set.

---

## Review (Worker 3, pass 3)

Re-review of the one-sentence apply pass dispatched by `### The one finding that holds this unit`.
The whole cohort diff was re-read, not only the line pass 3 claims: `git diff HEAD -- docs/README.md
README.md` — **29 insertions, 9 deletions**, one file; `README.md` (root) is still absent from the
diffstat.

### The delta since pass 2 is exactly the dispatched sentence, measured

Not accepted on the build report's diffstat arithmetic. The pass-2-accepted content was
RECONSTRUCTED from the shipped file by substituting the retired sentence back in, and that
reconstruction was diffed against `HEAD`:

- `git diff --no-index --numstat <scratch>/head_README.md <scratch>/pass2_README.md` → **28 / 8**,
  which is the figure both the pass-2 review and the final verification recorded for the accepted
  state. So the pass-3 delta is one replaced line and nothing else — no other hunk was added,
  removed, or reflowed under cover of the edit.
- The shipped sentence is **byte-identical to the dispatched replacement**: both quotations of it in
  this artifact (the final verification's dispatch and the build report's echo) compare equal to the
  file's text, and it occurs exactly once. The retired sentence occurs **0** times in the file and
  **1** time at `HEAD`.
- The rest of that paragraph is byte-unchanged: un-substituting the new sentence for the old one
  reproduces `git show HEAD:docs/README.md`'s line character for character.

### The sentence is true against the code

Read first, then executed, then executed again on an instrument of this reviewer's own.

`django_strawberry_framework/schema.py::_declared_authority` walks the two authority types and
returns a declaration only on an EXACT type identity (#"if _entry_type(entry) is extension_type");
anything else that is a strict subclass falls to #"if _extension_entry_matches(entry,
extension_type)" and raises `ConfigurationError` **there**, before any arm reads what the entry
declares — `schema.py::_entry_resource_policy` is reached only on the exact-match path, after
`_declared_authority` has returned. `schema.py::_entry_type` answers a class entry with itself and
an instance entry with its type, so the single `issubclass` arm in
`schema.py::_extension_entry_matches` covers both spellings. `_declared_authority` is called from
`schema.py::_consumer_extension_entries`, which is the **first statement** of
`DjangoSchema.__init__`, before `super().__init__`, so the refusal is construction-time and the
schema never builds. There is no arm that reads a supplied policy before refusing a subclass, which
is what the retired qualifier "to supply it" implied.

Worker 2's `<scratch>/p3_subclass_ladder.py` was re-run rather than read — exit 0, rows `1`-`5`
refused at construction, controls `a`-`c` built. It was also read before being trusted, and its one
gap is that `refused()` accepts ANY `ConfigurationError`, so a row could in principle be satisfied
by the duplicate-declaration raise rather than the subclass raise. A second probe written from the
code closes that gap and covers the sentence's FIRST clause, which Worker 2's does not:
`<scratch>/w3_p3_verify.py`, run from the repository root as
`PYTHONPATH=examples/fakeshop uv run python <scratch>/w3_p3_verify.py` — exit 0, every refusal row
asserting WHICH raise it hit by message text:

```
OK   1 twice: resource_policy= AND a declaring entry: [A schema's resource policy is declared once...]
OK   2 twice: two declaring entries: [DjangoSchema(extensions=[...]) carries two resource-...]
OK   3 resource subclass, CLASS entry, declares nothing: [RSubBare <class ...> subclasses the ...]
OK   4 resource subclass, INSTANCE entry, declares nothing: [RSubBare <... object at 0x...> s...]
OK   5 resource subclass, INSTANCE entry, DECLARES a policy: [RSubSupplying <... object at 0x...]
OK   6 error subclass, CLASS entry, declares nothing: [ESubBare <class ...> subclasses the ...]
OK   7 error subclass, INSTANCE entry, declares nothing: [ESubBare <... object at 0x...> s...]
OK   8 error subclass, INSTANCE entry, built explicitly: [ESubSupplying <... object at 0x...]
OK   CONTROL a exact resource authority INSTANCE entry: built, data={'ping': 'pong'}
OK   CONTROL b exact resource authority CLASS entry: built, data={'ping': 'pong'}
OK   CONTROL c exact error authority INSTANCE entry: built, data={'ping': 'pong'}
OK   CONTROL d exact error authority CLASS entry: built, data={'ping': 'pong'}
OK   CONTROL e unrelated extension CLASS entry: built, data={'ping': 'pong'}
OK   CONTROL f one declaring entry only: built, data={'ping': 'pong'}
OK   all rows (14)
```

- Rows `1`-`2` are the clause "Declaring the policy twice raises `ConfigurationError` at
  construction", which no earlier pass measured; rows `3`-`8` are the clause's own enumeration,
  **either** authority × **class or instance** × **declares a policy or declares nothing**.
- **The refusal rows are not vacuous.** An assertion that construction raises passes identically if
  construction raises for everything, so six controls build a schema and answer `{ ping }` under
  `warnings.catch_warnings()` + `simplefilter("error")` — both authorities as an exact class AND as
  an exact instance entry, an unrelated `SchemaExtension`, and a single declaring entry. Control `f`
  is the one that separates the two clauses: one declaring entry is admitted, two are refused.
- **No tracked bytes written.** `shasum -a 256 examples/fakeshop/db.sqlite3` is
  `563b26d8003c3c41072b7b7bbfc12fec524969aa3c9b258d7cdbac68ed32b52f` before the first probe of this
  pass and after the last — the same digest every earlier pass recorded.

### It agrees with the amended Decisions and with the same file

| home | subclass rung | factory rung |
|---|---|---|
| `docs/README.md` line 154 (this pass) | `ConfigurationError` at construction, class or instance, whether or not it declares a policy | next sentence: factory cases only, `SCHEMA_CONFIGURATION_UNAVAILABLE` |
| `docs/README.md` line 55 (`## Quick start`, pass 2) | "a subclass of either extension — supplied as a class or as an instance — is refused at construction with `ConfigurationError`" | "a factory that resolves to one instead refuses the operation with the stable `SCHEMA_CONFIGURATION_UNAVAILABLE` code" |
| spec `### Decision 15` ladder (amended) | `subclass of an authority, as a class or as an instance` → schema construction → `ConfigurationError` | `factory resolving to either authority, subclasses included` → `get_extensions` → refused |
| spec `### Decision 21` (amended) | "refused at schema construction with `ConfigurationError` - supplied as a class or as an instance, and whether or not it supplies a policy of its own" | "only a factory is opaque until it is called … the one spelling refused at the operation" |
| measured | rows `3`-`8` above | `<scratch>/p2_ladder.py` rows `D`, `D2` (re-run at pass 2) |

The rationale's `### Decision 21` entry was read in full: it rejects package-defined instance
semantics and the "move the instance into a factory" migration, and states neither refusal's timing,
so nothing in it is falsified by the corrected sentence. The two README paragraphs now read as one
ladder, which is what the finding asked for.

### High:

None.

### Medium:

None. The pass-1/pass-2 Medium (`docs/GLOSSARY.md` pairing a plain `strawberry.Schema` with the
singleton-in-a-factory) was **dispositioned by the custodian at final verification** — path (a), the
`GlossaryTerm.body` edits routed to Worker 0's "Record and card" step, with the population corrected
from two sites to four. It is not re-raised here and it does not hold this unit.

### Low:

#### `django_strawberry_framework/schema.py::DjangoSchema` still carries the retired qualifier in its class docstring

`django_strawberry_framework/schema.py::DjangoSchema` #"twice, or subclassing either enforcement
extension to supply it, is refused" is the **last home of the narrowness this cohort retired
everywhere else**. It is the same false conditional: measured, a bare subclass class entry declaring
nothing is refused identically (rows `3`, `6` above), and `_declared_authority` raises on the
`issubclass` result alone.

Population of that claim across the tree, swept independently of the diff
(`grep -rn "subclassing either\|subclass of either\|subclasses the package"` over `*.py` and `*.md`,
excluding `.venv/`, `docs/SPECS/` and this artifact): **five** homes carry it — `docs/README.md`
lines 55 and 154 (correct), `docs/GLOSSARY.md` line 785 #"a subclass of either is refused at
construction" (correct, unqualified), `docs/builder/DONE/build-050-list_field_arguments-0_0_15.md`
line 32 (correct), and `schema.py` line 715 (narrow). One site, and it is the only one left.

**Recorded and not held against this unit**, with the reason stated: the line is pre-existing at
`HEAD`, sits outside the diff, and is a Python source file no documentation cohort may write
(`worker-3.md` `## Scope`; the close cycle's partition gives package source to Cohort A). The
accurate form is the one already shipped three homes over. Routed below. No test expectation — the
raise it describes is already pinned by `tests/test_schema.py::test_a_subclass_of_an_enforcement_extension_is_refused_at_construction`.

### DRY findings

- **No new duplication.** The pass replaced one sentence with one sentence. `### Production error
  policy` still owns the full statement and `## Quick start` still links to it rather than
  restating it; the two now agree instead of diverging, which is a duplication defect closed, not
  one introduced.
- **The two-home trust contract is unchanged and still by design** (`GOAL.md` `## Trust boundary`
  owns it, `docs/README.md` `### The trust boundary` states it for a deployer). `START.md` "Sweep
  both files of a pair" governs the next edit to either.
- **Existence challenge:** none raised. The pass adds no abstraction, helper, or indirection.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` prints nothing: `__all__` and the re-export
list are unchanged. The pass touched no import line and no fenced block.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

- **Gates.** `uv run python scripts/check_citations.py --check` — **pass**,
  `OK: 1104 citations resolve (925 in 448 .py files, 179 in KANBAN.md).`
  `uvx pre-commit run --files docs/README.md` — **pass** (tracked path constants, source layout,
  kanban anchors, citations all Passed; both ruff hooks `(no files to check) Skipped`).
  **Disclosed:** the FIRST invocation of that hook set reported `citations resolve … Failed - files
  were modified by this hook` while printing the same `OK: 1104 citations resolve` line. `git status
  --short` was captured either side; the entry that moved belongs to the concurrently-worked tree,
  not to this cohort's file, and the immediate re-run passed clean with no intervening edit. Recorded
  rather than silently re-run once.
- **Census, as a population.** A fence-tracking scan of all 915 lines of `docs/README.md` (fences
  balanced) finds **3** `strawberry.Schema` occurrences, at lines 59, 124 and 204, **all in prose**
  and **0** inside any fenced block; **0** occurrences of a bare `Schema(` anywhere in the file
  against **11** `DjangoSchema(`. Both figures match the accepted state — this pass edited prose only.
- **Links.** The changed sentence contains **no** `][label]` use and **no** definition, verified by
  extracting the added lines from the diff, so the accepted audit (38 uses / 38 definitions, 0
  orphans either way, ten group headers in canonical order, every group alphabetical) still describes
  the file unchanged.
- **No process provenance.** A sweep of the changed sentence for `previously`, `no longer`, `as of `,
  `round N`, `Decision N`, `Slice N`, `spec-0`, `worker`, severity labels, `coming soon`, `planned`
  returns **0** hits. It states the refusal as a standing rule in the README's own voice.
- **Version strings, shipped statuses, spec relocation, script-rendered docs.** None touched; the
  diff moves no `docs/spec-050-*` file and regenerates nothing.

### Spec slice checklist walk

All three boxes remain `- [x]`, and each tick still has matching delivered text. Box 3 ("The shipped
docs state the trust contract where a deployer reads it") is the one this pass strengthens: the file
no longer carries two readings of the admission ladder. No box is silently unaddressed; no box is
ticked without a matching change.

### Failability proofs

The build report records `None; this pass introduced no new boundary.` **Audited and agreed:** the
pass replaced one prose sentence in a Markdown file and adds no guard, cap, rejection path or
validation branch. The mandatory re-run set is therefore empty, which `worker-3.md` permits only when
the diff introduces no boundary meeting the floor; that condition holds. **Boundaries re-run: none.
Boundaries accepted on Worker 2's record: none — there are none to accept.**

The sentence's behavioral claims are about code the diff does not touch, so they were verified as
`worker-3.md` "Claim verification" requires: by tracing `_extension_entry_matches` →
`_declared_authority` → `_consumer_extension_entries` → `DjangoSchema.__init__` (and confirming the
exact-match arm is the only path that reaches `_entry_resource_policy`), and by executing all
fourteen rows above on an instrument written for this pass. No earlier branch swallows either path.

### Hot-path budget verification

Plan declares this cohort `none`, and the diff adds no runtime code. Nothing owed, nothing missing.

### Static helper use

`scripts/review_inspect.py` **skipped, deliberately**: `BUILD.md` `### When to run the helper during
build` triggers on new `.py` files, files under `optimizer/` or `types/`, and line thresholds of new
logic. This diff touches one `.md` file and zero `.py` files.

### Test staleness

Re-run independently of the artifact's file list: `grep -rn "docs/README"` across `tests/`,
`examples/` and `scripts/` finds no reader, so nothing asserts this file's content and the edit
strands nothing. No wire-shape or model-field change is in the diff.

### What looks solid

- **The dispatch was applied verbatim rather than paraphrased**, so the shipped bytes, the amended
  Decision 21, the amended Decision 15 ladder and `## Quick start` all state one ladder. A
  paraphrase is where the next divergence would have started.
- **"whether or not it declares a policy of its own" answers the reader the old clause misled**
  instead of merely deleting the qualifier — silence would have left the same question open.
- **The edit is genuinely one line.** Reconstructing the pass-2 state and diffing it against `HEAD`
  reproduces 28/8 exactly, so nothing rode along under a one-sentence description.
- **Punctuation matches its own paragraph.** The ASCII hyphens match the four other dashes in
  `### Production error policy`; the em dashes in `## Quick start` match that paragraph. Neither was
  normalized across the other, which would have churned unrelated bytes.

### Temp test verification

- No temp test was written under `docs/builder/temp-tests/050/trust_docs/`. The instrument this
  review needs is an executable oracle for a documented ladder, which belongs outside the repo;
  `<scratch>/w3_p3_verify.py` (this pass's own) and `<scratch>/p3_subclass_ladder.py` are both
  re-runnable with the commands above.
- Disposition: not promoted, not kept in-tree. Every property they exercise is `DjangoSchema`
  behavior already pinned by the package suite — the subclass raise by
  `tests/test_schema.py::test_a_subclass_of_an_enforcement_extension_is_refused_at_construction` —
  and their job is to check the documentation against it.

### Notes for Worker 1 (spec reconciliation)

- **Escalated: `django_strawberry_framework/schema.py::DjangoSchema`'s class docstring is the last
  home of the retired qualifier.** See the Low. `START.md` "Sweep both files of a pair" and
  "Partial claim fix = dominant residual defect" both point at it: the spec, the glossary and both
  README paragraphs now say class-or-instance-regardless, and one docstring still says "to supply
  it". Resolution paths: (a) dispatch the one-clause docstring fix to whichever cohort owns
  `django_strawberry_framework/schema.py` in the close cycle's partition — it is a comment-only edit
  and owes the inverse proof `START.md` names (AST identity with docstrings stripped); (b) card it
  with a named owner for `BUILD.md` `### Deferred work catalog`. Not a worker's call; no documentation
  cohort may write that file.
- The `docs/GLOSSARY.md` residual stays where final verification routed it (Worker 0's "Record and
  card", four sites); nothing in this pass changes that disposition.
- No spec amendment is owed by this pass. The amended `### Decision 21`, `### Decision 15` and the
  `## Definition of done` row were each re-read against the shipped sentence and against the measured
  rows; all three agree.

### Review outcome

`review-accepted`. The dispatched correction landed verbatim, the delta since pass 2 is provably that
one sentence, and the claim is true on an oracle written for this pass with six building controls.
Two items leave with Worker 1, neither holding the unit: the `schema.py` docstring twin (Low, outside
every documentation cohort's writable set) and the already-routed glossary residual.

---

## Build report (Worker 2, pass 4)

Apply-changes pass over `### Low:` of `## Review (Worker 3, pass 3)`, the escalated docstring twin.
Worker 0 folded `django_strawberry_framework/schema.py` into this cohort's partition so the last
home of the retired qualifier closes in-cycle. One clause of one class docstring was rewritten;
nothing executable changed, and the `docs/GLOSSARY.md` residual stays where final verification
routed it.

**Precondition.** `git diff HEAD -- django_strawberry_framework/schema.py` printed nothing before
the edit (empty output, exit 0), so the file was clean at `HEAD` and the diff below is wholly this
pass's.

### Files touched

`git status --short` adds one path to the baseline-dirty set this pass:
`django_strawberry_framework/schema.py` (plus this artifact and the untracked
`docs/builder/worker-memory/050-worker-2.md`). One edit, inside
`django_strawberry_framework/schema.py::DjangoSchema`'s class docstring, in the
**Both authorities are the schema's, not entries in ``extensions=``.** paragraph. The clause

> and declaring the same policy twice, or subclassing either enforcement extension to supply it,
> is refused here.

now reads

> and declaring the same policy twice is refused here, as is a subclass of either enforcement
> extension - supplied as a class or as an instance, and whether or not it declares a policy of
> its own - because a subclass can override the hook that does the enforcing while still answering
> every check for it.

The paragraph's surrounding structure is unchanged: the same sentence position, the same
declaration-folding clause before it, and the byte-unchanged factory sentence after it
(#"An entry that would decide enforcement later"), which already states the operation-time refusal
as factory cases only. The wording is the docstring's own voice matching the three homes that
already state it — `docs/README.md` `### Production error policy` ("supplied as a class or as an
instance, and whether or not it declares a policy of its own"), the amended `### Decision 21`
("supplied as a class or as an instance, and whether or not it supplies a policy of its own") and
the amended `### Decision 15` ladder rung (`subclass of an authority, as a class or as an
instance`). ASCII only, longest changed line 79 characters against the 99 limit, and no process
provenance: no `now`, `no longer`, `previously`, `as of `, round, worker, card or spec id — a
sweep of the added lines for those tokens returns **0** hits.

### Tests added or updated

None. The edit is a docstring; the behavior it describes is already pinned by
`tests/test_schema.py::test_a_subclass_of_an_enforcement_extension_is_refused_at_construction`.

### Executable identity, the inverse proof a comment-only edit owes

`START.md` "Instruments that lie" requires a docstring-only edit to prove the executable code did
not move, and a docstring token cannot move a docstring-stripped digest, so the digest is the
instrument and a mutation of it is the control.

- Copy taken **before** the edit, proved identical to the file at that moment:
  `shasum -a 256 django_strawberry_framework/schema.py <scratch>/schema_before.py` →
  `16dfcf136a13e2895cd1eb04e71106c22082bb3fecab583dc55618bd953709f8` for both.
- Command, from the repository root:
  `uv run python - <<'PY'` … `PY` — it `ast.parse`s both copies, deletes the leading string
  `Expr` from every `Module` / `ClassDef` / `FunctionDef` / `AsyncFunctionDef` body (substituting
  `Pass` where that empties a body), and compares `ast.dump(..., annotate_fields=True)`.
- Result, exit 0:

  ```
  before sha256: 709b1682db88897b8d4805b0b658e9e6121fdcb27ac440f1ebbfa3e7d0be4e15
  after  sha256: 709b1682db88897b8d4805b0b658e9e6121fdcb27ac440f1ebbfa3e7d0be4e15
  AST identical with docstrings stripped: True
  control (extra statement) differs: True
  docstring text changed: True
  ```

- **Two controls, because an identity assertion is self-satisfying without them.** `control (extra
  statement) differs: True` appends one statement to the parsed post-edit module and shows the dump
  does change, so the comparison is capable of reporting a difference; `docstring text changed:
  True` shows the two files are not byte-identical, so the identity is a real strip rather than a
  no-op read of the same bytes.

### Validation run

- `uv run ruff format django_strawberry_framework/schema.py` — **pass**, `1 file left unchanged`.
- `uv run ruff check --fix django_strawberry_framework/schema.py` — **pass**, `All checks passed!`.
- `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/schema.py` —
  **pass**, exit 0, no output (ASCII-only and trailing-comma layout both clean).
- `uvx pre-commit run --files django_strawberry_framework/schema.py` — **pass**: `kanban tracked
  path constants`, `source layout`, `ruff format`, `ruff check`, `kanban anchors` and `citations
  resolve` all Passed.
- `uv run python scripts/check_citations.py --check` — **pass**:
  `OK: 1104 citations resolve (925 in 448 .py files, 179 in KANBAN.md).`
- `uv run pytest -n0 tests/test_schema.py --no-cov -q` — **pass**, `141 passed in 1.92s`, 0
  collection errors. No `--cov*` flag was used.
- `git diff HEAD --stat -- django_strawberry_framework/schema.py` — 8 insertions, 5 deletions, one
  file, all inside the docstring; the hunk touches no line below `"""`.
- `git status --short` after every command — the only path this pass added is
  `django_strawberry_framework/schema.py`. `django_strawberry_framework/permissions.py`,
  `resource_policy.py`, `types/resolvers.py`, `utils/querysets.py`, `docs/README.md` (this
  cohort's, from passes 1-3), `docs/spec-050-*`, `docs/feedback.md`,
  `docs/builder/DONE/build-050-*`, `examples/fakeshop/db.sqlite3`, the three
  `examples/fakeshop/test_query/` modules, `tests/test_resource_policy.py` and
  `tests/utils/test_querysets.py` are the concurrent cohort's and the concurrent session's.
  Reported, not touched, not reverted.

### Retired-qualifier census

Swept with a Python walker rather than a shell loop, over every readable file in the tree except
`.git/`, `.venv/`, `node_modules/` and caches, printing the population before the hits: **5,827
files scanned**, **15 occurrences** of `to supply it` over 15 lines at the sweep taken immediately
after the source edit (counted per occurrence, not per line, so a doubled line could not read as
one). Positive control: the needle is found at all, so the sweep is not reporting emptiness.

**The count moves because this report is inside the population it counts.** Writing the retired
clause out above adds three occurrences to this artifact, so a re-sweep now returns **18**, and a
reader quoting the clause again would move it again. The figure that is stable, and the one the
finding is about, is the one below the table: **0** in `django_strawberry_framework/` and **0** in
any standing doc or spec.

**Inside this pass's writable set: 0.** `django_strawberry_framework/` carries no hit of the
qualifier at all after the edit — the sole package hit, `schema.py:715`, is the one retired here.

Every remaining hit, with its file, all outside this pass's writable set:

| File | Lines | What it is |
|---|---|---|
| `docs/builder/bld-050-close-trust_docs.md` | 431, 507, 982, 984, 1140, 1309, 1310, 1334, 1592, 1679, 1741, 1813 (+ 3 more added by this report) | 12 hits at the sweep: this artifact's own record of the finding across passes 1-3 — the quoted `docs/README.md` sentence, the Low that named it, the dispatched replacement, and the Worker 3 pass-3 Low that dispatched this pass; this report adds 3 more by quoting the retired clause. Per-cycle scratch, closes with the cycle; no action. |
| `docs/builder/worker-memory/050-worker-1.md` | 50 | Worker 1's memory line recording the same finding. Untracked scratch, another worker's file, forbidden to this role. |
| `docs/builder/worker-memory/050-worker-3.md` | 34 | Worker 3's memory line recording the same finding. Same disposition. |
| `tests/test_sets_mixins.py` | 298 | **Unrelated homonym**, not the retired qualifier: #"a future set family that forgets to supply it fails at" is about a set mixin's own attribute, not about subclassing an enforcement extension. No action. |

A second sweep for the narrower forms the qualifier could hide behind
(`grep -rn "subclassing either\|subclass of either\|either enforcement extension"` over
`django_strawberry_framework/`, `tests/` and `examples/`) returns **3** hits and none is narrow:
`schema.py:715` is this pass's corrected clause,
`django_strawberry_framework/middleware/request_body.py:352` is about middleware subclass
recognition, and `tests/test_views.py:3283` is a docstring about class-comparison in the view
audit.

### Failability proofs

None; this pass introduced no new boundary. The edit is one clause of one class docstring, and the
AST-identity proof above is the evidence that no executable statement moved.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; the plan's floor-verification scope assigns this cohort no run.

### Implementation notes

- **"declares a policy of its own", not "supplies a policy of its own".** The docstring's own
  neighbouring sentence already uses "declaration" / "declared" for what an entry does, so
  `declares` keeps one verb for one concept inside the paragraph; it is the same word
  `docs/README.md` `### Production error policy` uses for the identical clause, and it is the
  broader of the two readings either way.
- **The clause was split off the "declaring twice" rule rather than appended to it.** The retired
  sentence made one predicate ("is refused here") serve two subjects, which is what let the
  qualifier attach to the subclass half unnoticed. Two predicates keep the subclass rung readable
  on its own, matching the shape both README paragraphs now use.
- **ASCII hyphens, not em dashes.** The docstring's existing parenthetical in the same sentence
  (`- the entry is folded into the record rather than kept -`) uses ASCII hyphens, and `.py`
  source is ASCII-only under the `source layout` hook, so the new parenthetical matches rather
  than introducing a second dash style.

### Notes for Worker 3

- The oracle for the rewritten clause is already in the artifact and needs no new instrument:
  `<scratch>/w3_p3_verify.py` rows `3`-`8` (either authority x class-or-instance x
  declares-a-policy-or-nothing) and `<scratch>/p3_subclass_ladder.py` rows `1`-`5`, with the
  building controls that keep the refusal rows non-vacuous. The clause asserts exactly those rows.
- The edit is a docstring. The inverse proof it owes is the AST-identity run above, not a test
  run; `tests/test_schema.py` was run anyway (141 passed) because the file it documents is package
  source.
- `django_strawberry_framework/schema.py` was clean at `HEAD` before this pass, so the whole diff
  on that path is this pass's; the cohort's `docs/README.md` diff is unchanged from pass 3.

### Notes for Worker 1 (spec reconciliation)

- No spec amendment is owed by this pass. The docstring now states the same ladder as the amended
  `### Decision 21`, the amended `### Decision 15` table, the `## Definition of done` row and both
  `docs/README.md` paragraphs; all five were read against the shipped clause before it was written.
- The retired qualifier's remaining homes are per-cycle scratch (this artifact, two worker-memory
  files) and one unrelated homonym in `tests/test_sets_mixins.py`. No standing doc, spec or package
  source carries it. The census is in this report.
- The `docs/GLOSSARY.md` residual is untouched and stays routed to Worker 0's "Record and card"
  step, four sites.

---

## Review (Worker 3, pass 4)

Re-review of the escalated docstring twin. One clause of
`django_strawberry_framework/schema.py::DjangoSchema`'s class docstring.
`git diff HEAD -- django_strawberry_framework/schema.py` — **one hunk, 8 insertions, 5 deletions**,
entirely inside the `**Both authorities are the schema's, not entries in ``extensions=``.**`
paragraph. `docs/README.md` is still **29/9**, byte-identical to the pass-3 accepted state, so this
pass rode nothing along on the cohort's other file.

### The diff is docstring-only, on an instrument of this reviewer's own

Not accepted on the build report's digest. `git show HEAD:django_strawberry_framework/schema.py` was
written to `<scratch>/head_schema.py` (never a checkout — the tree is legitimately dirty with a
concurrent cohort's work) and compared with `<scratch>/w3_ast_identity.py`, which `ast.parse`s both,
deletes the leading string `Expr` from every `Module` / `ClassDef` / `FunctionDef` /
`AsyncFunctionDef` body, and digests `ast.dump(..., annotate_fields=True)`:

```
HEAD   stripped-AST sha256: 709b1682db88897b8d4805b0b658e9e6121fdcb27ac440f1ebbfa3e7d0be4e15
WORK   stripped-AST sha256: 709b1682db88897b8d4805b0b658e9e6121fdcb27ac440f1ebbfa3e7d0be4e15
AST identical with docstrings stripped: True
source bytes differ (edit is real): True
control (extra statement) differs: True
control (error-message literal mutated) found: True differs: True
top-level node lists equal: True count: 55
```

The digest reproduces Worker 2's recorded `709b1682…` from a separately written script.

**Three controls, one of them not in the build report.** Worker 2's control appends a statement,
which proves the comparison can report a *structural* difference. It does not prove the comparison
can see a changed **string literal** — and the paragraph being rewritten sits ~470 lines above an
error message that says nearly the same thing, so a stray edit there is the realistic way this
proof could have passed while executable text moved. The added control mutates
`schema.py::_declared_authority` #"subclasses the package's" in the parsed copy and shows the
stripped digest **does** change, so a non-docstring literal edit was in range of the instrument and
did not happen. `source bytes differ: True` keeps the identity from being a no-op read of one file.

### The clause is true, measured

Read first. `schema.py::_declared_authority` returns a declaration only on exact type identity
(#"if _entry_type(entry) is extension_type"); anything else that is a strict subclass falls to
#"if _extension_entry_matches(entry, extension_type)" and raises `ConfigurationError` **there**,
before `schema.py::_entry_resource_policy` is ever called — so what the entry declares cannot change
the outcome, which is precisely what "whether or not it declares a policy of its own" asserts.
`schema.py::_entry_type` answers a class with itself and an instance with its type, so one
`issubclass` arm in `schema.py::_extension_entry_matches` covers both spellings.
`schema.py::_consumer_extension_entries` is the first statement of `DjangoSchema.__init__`, before
`super().__init__`, so "here" is construction and the schema never builds.

Then executed, on `<scratch>/w3_p4_clause.py`, written for this pass rather than re-run from the
build report — every refusal row asserts **which** raise it hit by message text, so the duplicate
declaration raise cannot satisfy a subclass row:

```
OK   1 twice: resource_policy= + a declaring entry        | [A schema's resource policy is declared once...]
OK   2 twice: two declaring entries                       | [DjangoSchema(extensions=[...]) carries two resource-...]
OK   3 resource subclass, CLASS entry, declares nothing    | [RSubBare <class ...> subclasses the packag...]
OK   4 resource subclass, INSTANCE entry, declares nothing | [RSubBare <... object at 0x...> subclas...]
OK   5 resource subclass, INSTANCE entry, DECLARES a policy| [RSubBare <... object at 0x...> subclas...]
OK   6 resource subclass OVERRIDING the hook, CLASS entry  | [RSubOverriding <class ...> subclasse...]
OK   7 resource subclass OVERRIDING the hook, INSTANCE     | [RSubOverriding <... object at 0x...>...]
OK   8 error subclass, CLASS entry                         | [ESubBare <class ...> subclasses the packag...]
OK   9 error subclass, INSTANCE entry                      | [ESubBare <... object at 0x...> subclas...]
OK   A exact resource authority INSTANCE entry             | built, data={'ping': 'pong'} errors=None
OK   B exact resource authority CLASS entry                | built, data={'ping': 'pong'} errors=None
OK   C exact error authority INSTANCE entry                | built, data={'ping': 'pong'} errors=None
OK   D exact error authority CLASS entry                   | built, data={'ping': 'pong'} errors=None
OK   E ONE declaring entry only                            | built, data={'ping': 'pong'} errors=None
OK   F unrelated extension CLASS entry                     | built, data={'ping': 'pong'} errors=None
OK   G no extensions at all                                | built, data={'ping': 'pong'} errors=None
rows=16 failures=0
```

- Rows `3`-`9` are the clause's own enumeration: **either** authority x **class or instance** x
  **declares a policy or declares nothing**, plus the case the clause's reason names — a subclass
  that actually **overrides** `on_operation`, refused identically to a bare one.
- **The refusal rows are not vacuous.** An assertion that construction raises passes identically if
  construction raises for everything, so seven controls build a schema and answer `{ ping }` under
  `warnings.catch_warnings()` + `simplefilter("error")`. Control `E` is the one that separates the
  sentence's two clauses: one declaring entry is admitted, two are refused.
- The clause's **reason** — "a subclass can override the hook that does the enforcing while still
  answering every check for it" — is not new prose. It is the sentence
  `schema.py::_declared_authority` already puts on the wire in its own error message, and the one
  `docs/README.md` `### Production error policy` already ships. Stating the same thing is what this
  cohort is for.
- **No tracked bytes written.** `shasum -a 256 examples/fakeshop/db.sqlite3` is
  `563b26d8003c3c41072b7b7bbfc12fec524969aa3c9b258d7cdbac68ed32b52f` before the first probe of this
  pass and after the last — the digest every earlier pass recorded.

### It matches the three homes it was aligned to

| home | subclass rung |
|---|---|
| `schema.py::DjangoSchema` (this pass) | `supplied as a class or as an instance, and whether or not it declares a policy of its own` |
| `docs/README.md` `### Production error policy` | `supplied as a class or as an instance, and whether or not it declares a policy of its own` — plus the same `because a subclass can override the hook…` reason |
| spec `### Decision 21` (amended) | `supplied as a class or as an instance, and whether or not it supplies a policy of its own, because what disqualifies it is the override it may carry on the hook that charges or masks` |
| spec `### Decision 15` ladder (amended) | `subclass of an authority, as a class or as an instance` → schema construction → `ConfigurationError` |

`declares` over `supplies` is right for this file: the neighbouring sentences use "declaration" /
"declared" for what an entry does, and it is `docs/README.md`'s word for the identical clause.
The factory sentence after it is byte-unchanged and still names the operation-time rung only, so the
docstring reads as one ladder, same as both README paragraphs.

### High:

None.

### Medium:

None.

### Low:

#### The same sentence still says "the same policy twice", which is narrower than the code

`django_strawberry_framework/schema.py::DjangoSchema` #"and declaring the same policy" (line 714,
unchanged context in this diff) qualifies the duplicate-declaration rung with **same**. Measured,
the refusal does not depend on sameness at all — `<scratch>/w3_p4_same.py`, two policies with
different `max_depth`:

```
policies equal? False | a.max_depth 7 b.max_depth 19
REFUSED  two entries, DIFFERENT policies                  | DjangoSchema(extensions=[...]) carries two resource-policy e
REFUSED  two entries, IDENTICAL policy object             | DjangoSchema(extensions=[...]) carries two resource-policy e
REFUSED  resource_policy= AND an entry, DIFFERENT policies | A schema's resource policy is declared once. This one is dec
REFUSED  resource_policy= AND an entry, SAME policy object | A schema's resource policy is declared once. This one is dec
```

`docs/README.md` `### Production error policy` says "Declaring the policy twice raises
`ConfigurationError` at construction" with no such qualifier, and the error message itself says "A
schema's resource policy is declared once. This one is declared twice" — so this docstring is the
only home carrying it. On the reading "two declarations of the **same** policy", it invites exactly
the inference the cohort just retired from the adjacent clause: that two **different** declarations
might compose. They do not.

**Recorded and not held against this unit**, with the reason stated: the word is pre-existing at
`HEAD`, sits on a context line the diff does not add, and the dispatched finding landed exactly and
verbatim. It is one word, and the alternative reading ("declaring it twice for the same schema") is
available, so this is an ambiguity rather than a false statement — unlike the subclass qualifier,
which was false. Routed below rather than left to stand with the tick. No test expectation: both
raises are already pinned, by
`tests/test_schema.py::test_a_policy_declared_by_an_entry_and_by_the_argument_is_refused` and
`tests/test_schema.py::test_two_entries_declaring_a_policy_of_their_own_are_refused`, and no branch
distinguishes equal from unequal policies, so sameness has no row to add.

### DRY findings

- **No new duplication introduced.** The pass replaced one clause with one clause and adds no
  abstraction, helper, constant or indirection.
- **Observed, not a consolidation target:** the reason sentence now has **three** prose homes —
  the runtime error message in `schema.py::_declared_authority`, this class docstring, and
  `docs/README.md` `### Production error policy` — whitespace-flattened and case-folded, the string
  `subclass can override the hook that does the enforcing while still answering every check for it`
  occurs once in `django_strawberry_framework/schema.py` (the docstring; the error literal is split
  across adjacent source lines so a flat scan reads it as a fourth site only after concatenation)
  and once in `docs/README.md`. Per `docs/dry/DRY.md` "Design principles" this counts **one**
  authoritative definition (the error message the consumer actually receives) plus two projections
  of it, and a projection is not a consolidation target — a docstring cannot interpolate an error
  literal without becoming unreadable, and the five-homes redundancy is the design. **Carry-forward
  hazard, not a finding:** the three copies are byte-identical with no gate over them, so a reword
  of the error message strands two prose copies silently. The sweep vocabulary is
  `override the hook that does the enforcing`.
- **Existence challenge:** none raised. Nothing was added that could be deleted.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` and `git diff HEAD --
django_strawberry_framework/__init__.py` both print **0 lines**: `__all__` and the re-export list are
unchanged. The diff touches no import, no signature and no name.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

- **Gates, re-run independently.**
  `uvx pre-commit run --files django_strawberry_framework/schema.py` — **pass**, all six hooks
  Passed (`kanban tracked path constants`, `source layout`, `ruff format`, `ruff check`, `kanban
  anchors`, `citations resolve`); no hook modified a file, so no re-run was needed.
  `uv run python scripts/check_citations.py --check` — **pass**,
  `OK: 1104 citations resolve (925 in 448 .py files, 179 in KANBAN.md).`
  `uv run pytest -n0 tests/test_schema.py --no-cov -q` — **pass**, `141 passed in 1.80s`, **0
  collection errors**, no `--cov*` flag.
- **ASCII and layout.** `LC_ALL=C grep -n '[^ -~\t]'` over the whole file returns **0** lines, and
  the added lines carry **0** non-ASCII bytes. Longest added line **79** characters against the 99
  limit. The new parenthetical uses ASCII hyphens, matching the one already in the same sentence.
- **No process provenance.** A sweep of the added lines for `previously`, `no longer`, `as of `,
  `round N`, `slice N`, `spec-0`, `worker`, severity labels, `coming soon`, `planned`, `TODO`
  returns **0** hits.
- **Retired-qualifier census, re-derived rather than read.** A Python walker over every readable
  file outside `.git/`, `.venv/`, `node_modules/` and caches — **5,827 files scanned**, positive
  control: each needle is found somewhere, so the sweep is not reporting emptiness:

  | needle | total | where |
  |---|---|---|
  | `to supply it` | 18 | 15 this artifact, 1 each `050-worker-1.md` / `050-worker-3.md` memory, 1 `tests/test_sets_mixins.py` (unrelated homonym: a set family's own attribute) |
  | `subclassing either` | 13 | 10 this artifact, 1 each `050-worker-2.md` / `050-worker-3.md` memory, 1 `tests/test_views.py` (unrelated: view-audit class comparison) |
  | `subclass of either` | 23 | 16 this artifact, 2 `docs/README.md`, 1 each `schema.py` (this pass, correct), `docs/GLOSSARY.md`, `docs/builder/DONE/build-050-*`, `docs/SPECS/spec-046-*` (unrelated), `middleware/request_body.py` (unrelated) |

  **`django_strawberry_framework/` carries 0 occurrences of the retired qualifier in any spelling**,
  and so does every standing doc and spec. The remaining live homes are per-cycle scratch and two
  unrelated homonyms. The instrument counts **occurrences, not lines**, and — the artifact being
  inside its own population — the first two rows move whenever this artifact quotes the clause
  again; the stable figure, and the one the finding is about, is the package/standing-doc **0**.
- **Version strings, KANBAN, spec relocation, script-rendered docs.** None touched. The diff moves
  no `docs/spec-050-*` file, regenerates nothing, and `docs/TREE.md` reads module docstrings, not
  class docstrings, so no render is owed.
- **Inbound citations.** `rg 'DjangoSchema #"'` across the tree (excluding `.venv/` and this
  artifact) returns **0**: nothing cites a substring of this docstring, so the reword strands no
  `path::Symbol #"substring"` reference. The `::Symbol` half is gated and green above.

### Spec slice checklist walk

All three boxes remain `- [x]` with matching delivered text. Box 3 ("The shipped docs state the
trust contract where a deployer reads it") is the one this pass completes: the package source that
documents the contract now states the same ladder as the two README paragraphs, the amended
Decision 15 table and the amended Decision 21. No box is silently unaddressed; no box is ticked
without a matching change.

### Failability proofs

The build report records `None; this pass introduced no new boundary.` **Audited and agreed** — and
the agreement is the AST identity above, not a reading: with docstrings stripped the file is
digest-identical to `HEAD` across all 55 top-level nodes, so no guard, cap, rejection path or
validation branch can have been introduced. The mandatory re-run set is therefore empty, which
`worker-3.md` permits only when the diff introduces no boundary meeting the floor; that condition
holds mechanically here rather than by judgement. **Boundaries re-run: none. Boundaries accepted on
Worker 2's record: none — there are none to accept.**

The clause's behavioral claims are about code the diff does not touch, so they were verified as
"Claim verification" requires: by tracing `_extension_entry_matches` → `_declared_authority` →
`_consumer_extension_entries` → `DjangoSchema.__init__`, confirming the exact-match arm is the only
path reaching `_entry_resource_policy`, and by executing all sixteen rows above plus the four
sameness rows. No earlier branch swallows either path.

### Hot-path budget verification

Plan declares this cohort `none`, and the diff adds no runtime code (AST-identical). Nothing owed,
nothing missing.

### Static helper use

`scripts/review_inspect.py` **skipped, deliberately**, with the reason: `BUILD.md` `### When to run
the helper during build` triggers Worker 3 on a new `.py` file, on a file under `optimizer/` or
`types/`, or on 30+ lines of new logic in `django_strawberry_framework/`. This diff adds a new file
to none of those, and the AST identity proves the new-logic count is exactly **0**.

### Test staleness

Re-run independently of the artifact's file list, not against it: `grep -rn "__doc__"` across
`tests/`, `examples/` and `scripts/` finds no reader of `DjangoSchema.__doc__`, and
`subclasses the package's` appears in exactly one file tree-wide (`schema.py` itself), so no test
asserts either the docstring text or the error-message text this pass echoes. Nothing is stranded.
`tests/test_schema.py` was run in full anyway (141 passed) because the edited file is package source.

### What looks solid

- **The dispatch landed as a bound, not a reword.** The clause names what is refused and enumerates
  the spellings, and rows `3`-`9` show each of them refused; row `5` (an instance that *does* declare
  a policy) is the one the retired qualifier implied would be treated differently, and it is not.
- **The clause was split off the duplicate-declaration rule rather than appended.** One predicate
  serving two subjects is what let the old qualifier attach to the subclass half unnoticed; two
  predicates make the subclass rung readable alone.
- **The reason is the error message's own sentence**, so a consumer who hits the raise reads the
  same words in the traceback and in the class they were configuring.
- **Punctuation and vocabulary match the paragraph rather than the source it was aligned to** —
  ASCII hyphens as the existing parenthetical uses, `declares` as the neighbouring sentences use.
  No byte of the surrounding paragraph was normalized on the way past.

### Temp test verification

- No temp test written under `docs/builder/temp-tests/050/trust_docs/`. The instruments this review
  needed are an AST oracle and two executable ladders, which belong outside the repo:
  `<scratch>/w3_ast_identity.py`, `<scratch>/w3_p4_clause.py` and `<scratch>/w3_p4_same.py`, all
  re-runnable with the commands above.
- Disposition: not promoted, not kept in-tree. Every property they exercise is `DjangoSchema`
  behavior already pinned by the package suite — the subclass raise by
  `tests/test_schema.py::test_a_subclass_of_an_enforcement_extension_is_refused_at_construction`,
  which parametrizes class and instance entries for both authorities and both hybrid orders — and
  their job is to check the documentation against it.

### Notes for Worker 1 (spec reconciliation)

- **Escalated: `django_strawberry_framework/schema.py::DjangoSchema` #"and declaring the same
  policy" is the last narrowing qualifier in that sentence.** See the Low, with the measured rows.
  It is the same shape as the twin this pass just closed, one clause earlier in the same sentence,
  and it is pre-existing at `HEAD` and outside the added lines, so no worker has grounds to widen
  its own dispatch to reach it. Resolution paths: (a) dispatch a one-word docstring fix to this
  cohort — delete `same`, matching `docs/README.md`'s already-shipped "Declaring the policy twice",
  owing the same AST-identity inverse proof; (b) card it with a named owner for `BUILD.md`
  `### Deferred work catalog`. Not a worker's call.
- **No new spec amendment is owed.** The amended `### Decision 21`, the amended `### Decision 15`
  ladder and the `## Definition of done` row were each re-read against the shipped clause and the
  measured rows; all three agree. Decision 21 says "supplies a policy of its own" where the code and
  both other homes say "declares" — a vocabulary difference, not a contract difference, and not
  worth a spec edit on its own.
- The `docs/GLOSSARY.md` residual is untouched by this pass and stays where final verification
  routed it (Worker 0's "Record and card" step, four sites).

### Review outcome

`review-accepted`. The diff is provably docstring-only on a stripped-AST digest with a literal-edit
control the build report did not carry; the rewritten clause is true on sixteen rows with seven
building controls; and every gate the dispatch named is green. One item leaves with Worker 1 and
does not hold the unit: the `same policy twice` qualifier one clause earlier, pre-existing at `HEAD`
and outside the added lines.

---

## Final verification (Worker 1, pass 2)

Diff under verification: `git diff HEAD -- docs/README.md django_strawberry_framework/schema.py` —
**29 insertions / 9 deletions** in `docs/README.md` and **8 insertions / 5 deletions** in
`django_strawberry_framework/schema.py`, two files. `README.md` (root) is absent from the diffstat,
so the plan's step 6 no-op still holds; re-derived rather than read off a prior report:
`grep -c 'strawberry\.Schema\|extensions=\[' README.md` returns **0**.

Nothing below is accepted on Worker 2's or Worker 3's record. Every probe was written for this pass
and run from the repository root; the `<scratch>/w1p2_*.py` scripts are re-runnable with the commands
given.

### The `schema.py` diff is docstring-only, proved by stripped-AST identity

`git show HEAD:django_strawberry_framework/schema.py` was written to `<scratch>/head_schema.py`
(never a checkout — the tree carries a concurrent session's work) and compared by
`<scratch>/w1p2_ast_identity.py`, which `ast.parse`s both, deletes the leading string `Expr` from
every `Module` / `ClassDef` / `FunctionDef` / `AsyncFunctionDef` body and digests
`ast.dump(..., annotate_fields=True)`:

```
HEAD stripped-AST sha256: 709b1682db88897b8d4805b0b658e9e6121fdcb27ac440f1ebbfa3e7d0be4e15
WORK stripped-AST sha256: 709b1682db88897b8d4805b0b658e9e6121fdcb27ac440f1ebbfa3e7d0be4e15
AST identical with docstrings stripped: True
source bytes differ (the edit is real): True
control structural (extra statement) differs: True
control literal needle present: True
control literal mutation differs: True
top-level node counts: 54 54 equal: True
```

Three controls, because an identity assertion is self-satisfying without them: a structural control
(one appended statement) proves the digest can move; a **string-literal** control (mutating
`schema.py::_declared_authority` #"subclasses the package's" in the parsed copy) proves a
non-docstring literal edit would have been in range; `source bytes differ` proves the identity is a
real strip rather than a no-op read of one file. The digest reproduces the one both pass 4 and its
review recorded, from a separately written script.

### The README sentence and the docstring clause, re-derived against the code

Read first. `schema.py::_declared_authority` returns a declaration only on exact type identity
(#"if _entry_type(entry) is extension_type"); any strict subclass falls to
#"if _extension_entry_matches(entry, extension_type)" and raises `ConfigurationError` there, before
`schema.py::_entry_resource_policy` is reached — so what an entry declares cannot change the
outcome, which is what "whether or not it declares a policy of its own" asserts.
`schema.py::_entry_type` answers a class with itself and an instance with its type, so the single
`issubclass` arm in `schema.py::_extension_entry_matches` covers both spellings.
`schema.py::_consumer_extension_entries` is the first statement of `DjangoSchema.__init__`, before
`super().__init__`, so the refusal is construction-time and the schema never builds; only
`DjangoSchema.get_extensions` can refuse an operation, which is the factory rung and only it.

Then executed. `PYTHONPATH=examples/fakeshop uv run python <scratch>/w1p2_ladder.py`, every row
carrying its expected verdict so a row cannot pass by landing in the wrong column:

```
OK  1 subclass CLASS entry, declares nothing     | CONSTRUCTION-REFUSED | RSubBare <class ...> subclasses the packag
OK  2 subclass INSTANCE entry, declares nothing  | CONSTRUCTION-REFUSED | RSubBare <... object at 0x...> subclas
OK  3 subclass INSTANCE entry, DECLARES a policy | CONSTRUCTION-REFUSED | RSubBare <... object at 0x...> subclas
OK  4 subclass OVERRIDING on_operation, CLASS    | CONSTRUCTION-REFUSED | RSubOverriding <class ...> subclasse
OK  5 error-authority subclass CLASS entry       | CONSTRUCTION-REFUSED | ESubBare <class ...> subclasses the packag
OK  6 factory -> exact authority                 | OPERATION-REFUSED    | codes=['SCHEMA_CONFIGURATION_UNAVAILABLE']
OK  7 factory -> authority SUBCLASS              | OPERATION-REFUSED    | codes=['SCHEMA_CONFIGURATION_UNAVAILABLE']
OK  C1 exact authority INSTANCE entry            | BUILT+RAN            | codes=[] data={'ping': 'pong'}
OK  C2 exact authority CLASS entry               | BUILT+RAN            | codes=[] data={'ping': 'pong'}
OK  C3 exact error-authority INSTANCE entry      | BUILT+RAN            | codes=[] data={'ping': 'pong'}
OK  C4 unrelated extension CLASS entry           | BUILT+RAN            | codes=[] data={'ping': 'pong'}
OK  C5 no extensions                             | BUILT+RAN            | codes=[] data={'ping': 'pong'}
rows=12 failures=0 building controls=5
```

**The refusal rows are not vacuous:** five controls build a schema and answer `{ ping }` under
`warnings.catch_warnings()` + `simplefilter("error")`, including both authorities as exact entries,
so the spellings neither sentence condemns are proved admissible on the same instrument. Row `4` is
the one the docstring's stated reason names — a subclass that actually overrides the enforcing hook
— refused identically to a bare one.

**Both homes agree with each other and with the amended Decisions.**

| home | subclass rung | factory rung |
|---|---|---|
| `docs/README.md` `## Quick start` | refused at construction with `ConfigurationError`, class or instance | operation refused, `SCHEMA_CONFIGURATION_UNAVAILABLE` |
| `docs/README.md` `### Production error policy` | same, plus "whether or not it declares a policy of its own" | next sentence: factory cases only |
| `schema.py::DjangoSchema` docstring | same wording as the README's | byte-unchanged factory sentence, operation-time only |
| spec `### Decision 15` ladder | `subclass of an authority, as a class or as an instance` → construction → `ConfigurationError` | `factory resolving to either authority, subclasses included` → `get_extensions` |
| spec `### Decision 21` | construction, class or instance, whether or not it supplies a policy | "only a factory is opaque until it is called" |
| measured | rows `1`-`5` | rows `6`-`7` |

The rationale's `### Decision 21` entry was re-read in full: it rejects package-defined instance
semantics and the "move the instance into a factory" migration and states neither refusal's timing,
so nothing in it is falsified. `declares` (README, docstring) against `supplies` (Decision 21) is a
vocabulary difference, not a contract difference.

### Worker 3's escalated Low, decided: the qualifier is false and is dispatched

`django_strawberry_framework/schema.py::DjangoSchema` #"and declaring the same policy" makes the
duplicate-declaration refusal conditional on the two declarations naming the **same** policy. The
code tests no such thing, and the contradiction is reachable through ordinary configuration.

Measured, `PYTHONPATH=examples/fakeshop uv run python <scratch>/w1p2_twice.py`:

```
policy A == policy B ? False | A.max_depth 7 | B.max_depth 19
1 resource_policy=A + entry declaring B (DIFFERENT)  | REFUSED  | A schema's resource policy is declared once...
2 resource_policy=A + entry declaring A (SAME value) | REFUSED  | A schema's resource policy is declared once...
3 two entries declaring B and A (DIFFERENT)          | REFUSED  | DjangoSchema(extensions=[...]) carries two resource-policy...
4 two entries declaring the SAME object              | REFUSED  | DjangoSchema(extensions=[...]) carries two resource-policy...
C1 one declaring entry only                          | BUILT
C2 resource_policy= only                             | BUILT
C3 bare authority CLASS entry                        | BUILT
C4 bare authority INSTANCE entry (declares nothing)  | BUILT
C5 error-authority CLASS entry                       | BUILT
C6 no extensions at all                              | BUILT
refused rows 1-4: 4/4   building controls: 6/6
```

Two policies with different bounds are refused identically to two of one policy, on both refusing
paths — the `__init__` raise for `resource_policy=` plus a declaring entry, and the
`_consumer_extension_entries` raise for two declaring entries. **Neither refusing body compares the
declarations at all:** over the source of `_consumer_extension_entries` and `DjangoSchema.__init__`,
`==` occurs 0 times, `!=` 0 times, `equal` 0 times and `same` 0 times. Six controls build, so the
refusal rows are not vacuous, and control `C1` is the one that separates the clauses — one
declaration is admitted, two are not.

Worker 3 recorded it as a Low, not held, on the reading that "declaring it twice for the same
schema" is available, making it an ambiguity rather than a false statement. That reading is
available, and it is still the wrong disposition here, for reasons a diff review could not weigh:

1. Under the reading the word `same` actually contributes, the sentence names a condition the code
   never evaluates, and the configuration it misdescribes is the ordinary one — a deployer who wants
   *different* bounds from the ones already declared is exactly who supplies a second declaration.
   The answer is not "the narrower policy wins"; the process does not start. That is the same
   consequence class as the subclass qualifier this cohort retired one clause later in this very
   sentence.
2. It is the **last** home of the narrowing, and every other home already ships the accurate form:
   `docs/README.md` `### Production error policy` says "Declaring the policy twice raises
   `ConfigurationError` at construction" with no qualifier, and the runtime error says "A schema's
   resource policy is declared once. This one is declared twice". Leaving one home narrower is
   `START.md` "Partial claim fix = dominant residual defect" exactly.
3. `django_strawberry_framework/schema.py` is in this cohort's writable set — Worker 0 folded it in
   at pass 4 — so resolution path (a) of Worker 3's own ranking is available with no partition
   change, and it is a two-line edit owing the same AST-identity inverse proof already routine here.

`docs/builder/worker-1.md` `## Scope` does not include package source, so this is dispatched rather
than fixed here.

**Exact replacement for Worker 2.** In `django_strawberry_framework/schema.py::DjangoSchema`'s class
docstring, in the **Both authorities are the schema's, not entries in ``extensions=``.** paragraph,
replace these two lines:

```
    folded into the record rather than kept - and declaring the same policy
    twice is refused here, as is a subclass of either enforcement extension -
```

with these two:

```
    folded into the record rather than kept - and declaring the policy twice is
    refused here, as is a subclass of either enforcement extension -
```

The change is the deletion of the word `same` plus the one-word rewrap that keeps both lines inside
the line-length limit (79 and 68 characters, ASCII). Every other line of the paragraph, the subclass
clause and the factory sentence included, is byte-unchanged; the joined text differs from the
shipped text in exactly that one word, verified by reconstruction. The result is the wording
`docs/README.md` `### Production error policy` already ships.

Expectation after the fix: `<scratch>/w1p2_twice.py` rows `1`-`4` are the oracle (any second
declaration refused, sameness irrelevant) with controls `C1`-`C6` keeping them non-vacuous; the
stripped-AST digest stays `709b1682…`; `uv run pytest -n0 tests/test_schema.py --no-cov -q` stays
green; and a tree-wide census of `same policy` carries **0** hits in
`django_strawberry_framework/` and in every standing doc and spec.

### Five-homes sweep for the same narrowness

Asked as a population, not an absence. A per-occurrence census (not per line: two hits on one line
would otherwise read as one) over `docs/spec-050-list_field_arguments-0_0_15.md`, its
`-rationale.md`, `docs/README.md`, root `README.md`, `docs/GLOSSARY.md`, `GOAL.md` and
`docs/builder/DONE/build-050-list_field_arguments-0_0_15.md`:

| needle | occurrences in those seven files |
|---|---|
| `same policy` | **0** |
| `declared once` | 0 |
| `two declarations` | 0 |
| `declaring the policy` | 1 — `docs/README.md:154`, the accurate form |
| `twice` | 9, of which 1 is this contract (`docs/README.md:154`); the other 8 are unrelated (row caps, a double-read boundary, a toolbar subclass, argument families) |

Widened to the whole tree (1,138 readable files, `.git/`, `.venv/`, caches excluded; positive
control: each needle is found somewhere, so the sweep is not reporting emptiness): `same policy` has
**12** occurrences, and exactly **one** is this contract — `django_strawberry_framework/schema.py:714`,
the clause dispatched above. The rest are this artifact and two worker-memory files (per-cycle
scratch), an unrelated optional-import comment in
`django_strawberry_framework/optimizer/nested_planner.py` with its shadow copy, and two archived
specs about unrelated policies. **No spec, README or glossary states the duplicate-declaration rule
narrowly.** So the dispatch closes the last standing home rather than one of several.

### Spec slice checklist audit

Every `- [x]` re-checked against the diff, not against any build report.

1. *State the trust contract … and the extension contract …* — **stands.** `### The trust boundary`
   carries Decision 20's three levels, the feasibility line and the beyond-upstream guarantees; the
   three `## Quick start` paragraphs carry Decision 21's three parts, each clause of the row's
   enumeration present, and the subclass rung is now true in both README homes and in the docstring
   (rows `1`-`5`).
2. *Correct the executable examples …* — **stands**, on this pass's own fence-tracking census of all
   915 lines of `docs/README.md` (fences balanced, 34 fenced blocks): **6** blocks construct a
   schema, at lines 18, 95, 113, 139, 652 and 735, and **0** construct a plain `strawberry.Schema`.
   **3** prose occurrences of `strawberry.Schema` survive, at lines 59, 124 and 204, each a
   deliberate contrast; **0** bare `Schema(` anywhere against **11** `DjangoSchema(`. Root
   `README.md`: 0 of any kind.
3. *The shipped docs state the trust contract where a deployer reads it …* — **stands** for every
   clause the row enumerates. The clause dispatched above is not one of them; it is the
   duplicate-declaration rung, which the row does not enumerate but which the package source must
   not state more narrowly than the file documenting it.

No box is ticked without a matching change; no box is left `- [ ]`.

### Gates

- `uvx pre-commit run --files docs/README.md django_strawberry_framework/schema.py` — **pass**, all
  six hooks Passed (`kanban tracked path constants`, `source layout`, `ruff format`, `ruff check`,
  `kanban anchors`, `citations resolve`); no hook modified a file.
- `uv run python scripts/check_citations.py --check` — **pass**, exit 0:
  `OK: 1104 citations resolve (925 in 448 .py files, 179 in KANBAN.md).`
- `uv run pytest -n0 tests/test_schema.py --no-cov -q` — **pass**, `141 passed in 1.85s`, 0
  collection errors. No `--cov*` flag was used in this pass.
- Inbound citations into the docstring being reworded: a tree-wide sweep of `#"` citations for
  `declaring the`, `folded into the record` and `Both authorities are the` finds **0** in package
  source, tests and standing docs. The only quotations are inside this per-cycle artifact and two
  worker-memory files, which are exempt from the `path::Symbol` rule and close with the cycle, so
  the dispatched reword strands no citation.
- **No tracked bytes written by any probe.** `shasum -a 256 examples/fakeshop/db.sqlite3` is
  `563b26d8003c3c41072b7b7bbfc12fec524969aa3c9b258d7cdbac68ed32b52f`, the digest every prior pass
  recorded; each probe answers `{ ping }`, which reaches no database.
- `git status --short` carries no path this pass made dirty. The two cohort files plus this artifact
  and the plan's baseline-dirty set are all that appear; the concurrent cohort's and concurrent
  session's paths were read, never written.

### Failability, hot path, floor, DRY

- **Failability proofs.** Every build report records `None; this pass introduced no new boundary.`
  Confirmed mechanically rather than read: the `schema.py` diff is stripped-AST identical to `HEAD`
  across all 54 top-level nodes, so no guard, cap, rejection path or validation branch can have
  entered through it, and the `docs/README.md` diff contains no Python. The obligation is empty, not
  sampled.
- **No fail-open shape landed.** There is no expression in either diff to fail open.
- **Hot path.** Plan declares `none`; neither diff adds runtime code. Nothing owed.
- **Floor verification.** The plan assigns this cohort no floor run; the full scope is the final
  gate's.
- **DRY.** The trust contract's two homes (`GOAL.md` `## Trust boundary` owns it, `docs/README.md`
  `### The trust boundary` states it for a deployer) are Decision 20's design and the README version
  is not a copy, so nothing is consolidatable; `START.md` "Sweep both files of a pair" governs the
  next edit to either. The subclass reason sentence now has three homes — the error message in
  `_declared_authority`, the class docstring and `### Production error policy` — which is one
  authoritative definition plus two projections, not a consolidation target; the carry-forward
  hazard Worker 3 named (an ungated reword of the error message stranding two prose copies, sweep
  vocabulary `override the hook that does the enforcing`) is recorded, not actioned, since no cohort
  owns a gate for prose.

### Final status

`revision-needed`. Everything else in this cohort is verified and stands: the three checklist boxes,
the six-block executable census with zero plain `strawberry.Schema`, the trust subsection, both
corrected README ladder statements, the docstring-only `schema.py` diff under a stripped-AST digest
with a literal-edit control, and all three gates. One qualifier in the cohort's own package-source
docstring is false as written and is dispatched above with its exact two-line replacement.

### Summary

Cohort B rewrote every schema-constructing example in `docs/README.md` onto `DjangoSchema`, replaced
the quick-start extension paragraph with Decision 21's three separate rules, added
`### The trust boundary` under `## Production security profile`, and aligned both the
`### Production error policy` paragraph and `DjangoSchema`'s class docstring onto the admission
ladder the code actually answers. Root `README.md` is untouched, on evidence. What outlives this
pass: one two-line docstring correction dispatched to Worker 2, and the `docs/GLOSSARY.md` residual
still routed to Worker 0's "Record and card" step.

### Spec changes made (Worker 1 only)

**None this pass.** The three edits recorded in the first final verification (`### Decision 21`,
`### Decision 15`'s ladder, the `## Definition of done` row) were re-read at the current spec HEAD
against the code and the measured rows above, and all three still describe what the code does; the
dispatched docstring correction needs no spec change, because no spec home states the
duplicate-declaration rule at all, narrowly or otherwise (see the five-homes sweep). The rationale's
`### Decision 21` and `### Decision 15` entries were re-read in full and nothing in either is
falsified.

**Status-line re-verification.** The spec's opening lines were re-read this spawn. They describe the
build's current state — Decision 21's summary in the `Revision:` block is the extension contract at
the level of the class-or-factory spelling and per-operation isolation, which the ladder correction
does not touch — and needed no edit.

### Notes for Worker 1 (spec reconciliation)

- **The glossary routing is unchanged and still Worker 0's.** The four `GlossaryTerm.body` edits for
  Worker 0's "Record and card" step were re-checked against the **current** rendered
  `docs/GLOSSARY.md` this pass, because a routed replacement block is only valid while the body it
  replaces still reads as quoted: `## DjangoOptimizerExtension` (rendered line 752),
  `## finalize_django_types` (line 946), `## BigInt scalar` (line 341) and `## strawberry_config`'s
  FIRST fenced block (line 1978) all still carry the exact text the replacements were written
  against, including the two lead-in clauses that end "before `strawberry.Schema(...)` is
  constructed:" and "into their `strawberry.Schema(...)` call.". The census holds too: **21**
  occurrences of `strawberry.Schema` over 20 lines in the rendered file, of which those four are the
  row's described pairing and the `## strawberry_config` body's two OTHER blocks (lines 1989, 1998)
  carry no `extensions=` entry and stay out of scope. No replacement block needs rewriting.
- No other escalation is open against this cohort.

---

## Build report (Worker 2, pass 5)

Apply-changes pass over `## Final verification (Worker 1, pass 2)`'s single dispatched item: the
false `same` qualifier in `django_strawberry_framework/schema.py::DjangoSchema`'s class docstring.
The replacement was written verbatim as dispatched, not paraphrased. Nothing else in the cohort was
touched; the `docs/GLOSSARY.md` residual stays routed to Worker 0's "Record and card" step.

**Precondition, checked before the first edit.** `git diff HEAD --
django_strawberry_framework/schema.py` carried exactly the pass-4 docstring hunk and nothing else —
one hunk at the `**Both authorities are the schema's, not entries in ``extensions=``.**` paragraph,
`8 insertions / 5 deletions`, the diffstat the final verification recorded. No second hunk, no
other file.

### Files touched

`git status --short` names one file this pass: `django_strawberry_framework/schema.py` (plus this
artifact and the untracked `docs/builder/worker-memory/050-worker-2.md`). One edit, two lines.

The two lines now written, verbatim:

```
    folded into the record rather than kept - and declaring the policy twice is
    refused here, as is a subclass of either enforcement extension -
```

79 and 68 characters, ASCII-only, both inside the limit. They replace:

```
    folded into the record rather than kept - and declaring the same policy
    twice is refused here, as is a subclass of either enforcement extension -
```

The delta is the deletion of the word `same` plus the one-word rewrap the dispatch specified. Every
other line of the paragraph — the subclass clause, its stated reason and the factory sentence — is
byte-unchanged, which the diffstat below shows as one line in and one line out on top of pass 4's
hunk: `8 insertions / 5 deletions` before this pass, `9 insertions / 6 deletions` after.

### Tests added or updated

None. The edit is a docstring; the package suite already pins the behavior it describes.

### Verification that no sameness is evaluated before the refusal

Read first, at the two symbols the dispatch named, then measured.

- `schema.py::DjangoSchema.__init__` raises on `#"if declared_resource is not None and
  resource_policy is not None"` — a presence conjunction. Nothing between
  `_consumer_extension_entries` returning and the raise reads either policy's value.
- `schema.py::_consumer_extension_entries` raises on `#"if declared is not None"` inside the entry
  loop, after `_entry_resource_policy(entry)` returns a non-`None` policy. The second declaration is
  refused for existing, never for what it holds; the first declaration's value is never compared to
  it.
- Mechanically, over the source of those two bodies only: `==` occurs 0 times, `!=` 0 times,
  `equal` 0 times, `same` 0 times. There is no expression in either body that could evaluate
  sameness, so the retired qualifier named a condition the code cannot test.

Then executed, because reading a body is not the same as the configuration reaching it. Probe
`<scratch>/w2p5_twice.py`, run from the repository root as
`PYTHONPATH=examples/fakeshop uv run python <scratch>/w2p5_twice.py`, with
`os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")` and `django.setup()`; every row
carries its expected verdict so a row cannot pass by landing in the wrong column:

```
policy A == policy B ? False | A.max_depth 7 | B.max_depth 19
OK  1 resource_policy=A + entry declaring B (DIFFERENT)    | REFUSED  | A schema's resource policy is declared once. This one is d...
OK  2 resource_policy=A + entry declaring A (SAME object)  | REFUSED  | A schema's resource policy is declared once. This one is d...
OK  3 two entries declaring B and A (DIFFERENT)            | REFUSED  | DjangoSchema(extensions=[...]) carries two resource-policy...
OK  4 two entries declaring the SAME object                | REFUSED  | DjangoSchema(extensions=[...]) carries two resource-policy...
OK  C1 one declaring entry only                            | BUILT    | data={'ping': 'pong'}
OK  C2 resource_policy= only                               | BUILT    | data={'ping': 'pong'}
OK  C3 bare authority CLASS entry                          | BUILT    | data={'ping': 'pong'}
OK  C4 bare authority INSTANCE entry (declares nothing)    | BUILT    | data={'ping': 'pong'}
OK  C5 error-authority CLASS entry                         | BUILT    | data={'ping': 'pong'}
OK  C6 no extensions at all                                | BUILT    | data={'ping': 'pong'}
refused rows 1-4: 4/4 expected   building controls: 6/6 expected   failures=0
```

Rows `1`-`4` cross the two refusing paths (the `__init__` raise and the
`_consumer_extension_entries` raise) with the two sameness verdicts (different bounds, same object),
and all four are refused identically — which is the claim the reworded line now makes. **The refusal
rows are not vacuous:** six controls build a schema and answer `{ ping }` on the same instrument,
and `C1` is the one that separates the clauses — *one* declaration is admitted, two are not, so the
refusal is about count and not about declaring at all. This probe is written for this pass; the
final verification's `<scratch>/w1p2_twice.py` belongs to another session's scratchpad and was not
re-run.

The probe writes no tracked bytes: `shasum -a 256 examples/fakeshop/db.sqlite3` is
`563b26d8003c3c41072b7b7bbfc12fec524969aa3c9b258d7cdbac68ed32b52f` before and after, the digest
every prior pass recorded. Each schema answers `{ ping }`, which reaches no database.

### The edit is docstring-only, proved by stripped-AST identity

A comment- or docstring-only edit owes the inverse proof, so `git show
HEAD:django_strawberry_framework/schema.py` was written to `<scratch>/head_schema.py` — never a
checkout, this tree carries a concurrent session's work — and compared by
`<scratch>/w2p5_ast_identity.py`, which `ast.parse`s both, deletes the leading string `Expr` from
every `Module` / `ClassDef` / `FunctionDef` / `AsyncFunctionDef` body and digests
`ast.dump(..., annotate_fields=True)`:

```
HEAD stripped-AST sha256: 709b1682db88897b8d4805b0b658e9e6121fdcb27ac440f1ebbfa3e7d0be4e15
WORK stripped-AST sha256: 709b1682db88897b8d4805b0b658e9e6121fdcb27ac440f1ebbfa3e7d0be4e15
AST identical with docstrings stripped: True
source bytes differ (the edit is real): True
control structural (extra statement) differs: True
control literal needle present: True
control literal mutation differs: True
top-level node counts: 54 54 equal: True
```

Three controls, because an identity assertion is self-satisfying without them: a structural control
(one appended statement) proves the digest can move; a **string-literal** control (mutating
`schema.py::_declared_authority` #"subclasses the package's" in the parsed copy) proves a
non-docstring literal edit would have been in range; `source bytes differ` proves the identity is a
real strip rather than a no-op read of one file. The digest is `709b1682…`, the one the final
verification expected the fix to preserve, reproduced from a script written this pass.

### Validation run

- `uv run ruff format django_strawberry_framework/schema.py` — **pass**, `1 file left unchanged`.
- `uv run ruff check --fix django_strawberry_framework/schema.py` — **pass**, `All checks passed!`,
  nothing fixed.
- `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/schema.py` —
  **pass**, exit 0, no output.
- `uvx pre-commit run --files django_strawberry_framework/schema.py` — **pass**, all six hooks
  Passed (`kanban tracked path constants`, `source layout`, `ruff format`, `ruff check`, `kanban
  anchors`, `citations resolve`); no hook modified a file.
- `uv run python scripts/check_citations.py --check` — **pass**, exit 0:
  `OK: 1104 citations resolve (925 in 448 .py files, 179 in KANBAN.md).`
- `uv run pytest -n0 tests/test_schema.py --no-cov -q` — **pass**, `141 passed in 1.68s`, 0
  collection errors. No `--cov*` flag was used in this pass.
- Retired-phrase census, stated as a population rather than an absence. `same policy` over
  `django_strawberry_framework/` (excluding `docs/shadow/`, which is regenerable): **1** occurrence,
  `optimizer/nested_planner.py:84`, the unrelated optional-import comment ("same policy as
  `types/converters.py`'s postgres field classes") the final verification already classified as not
  this contract. **0** in `docs/README.md`, root `README.md`, `GOAL.md`, `docs/GLOSSARY.md`,
  `AGENTS.md`, `START.md` and `docs/spec-050-list_field_arguments-0_0_15.md`. The figure that moves
  is this artifact's own — writing this report adds occurrences to it — so the stable statement is
  the one above: zero in the package's statement of this contract, zero in every standing doc and
  spec.
- `git status --short` after every command — no path outside this cohort's writable set appeared.
  The entries are the plan's baseline-dirty set (`permissions.py`, `resource_policy.py`,
  `types/resolvers.py`, `utils/querysets.py`, the two spec files, `docs/feedback.md`, the board DB,
  the four example/test files, the `DONE/` plan, the deleted hunt file and the two untracked
  concurrent artifacts) plus `docs/README.md`, `django_strawberry_framework/schema.py` and this
  artifact. Nothing was reverted; the concurrent session's and Cohort A's paths were read, never
  written.

### Failability proofs

None; this pass introduced no new boundary. The stripped-AST identity above is the mechanical form
of that claim rather than an assertion of it: with all 54 top-level nodes digest-identical to HEAD,
no guard, cap, rejection path or validation branch can have entered through this diff.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; the plan's floor-verification scope assigns this cohort no run.

### Implementation notes

- **Written verbatim, not paraphrased.** The dispatch carried the exact two lines, so the edit was a
  literal substitution of the quoted old block for the quoted new one. Reconstructing the wrap by
  hand would have risked a second word moving invisibly inside a paragraph nobody diffs word by
  word; the diffstat delta of exactly `+1/-1` on top of pass 4's hunk is what shows only the two
  dispatched lines moved.
- **The rewrap is what keeps the paragraph inside the limit.** Deleting `same` alone would have left
  line 715 short and line 714 unchanged; pulling `twice is` up makes 79 and 68, both under the
  99-character line length, with no other line reflowed — which is what keeps the subclass clause
  and the factory sentence byte-identical and therefore keeps the pass-4 review's reading of them
  valid.

### Notes for Worker 3

- The oracle for the reworded line is `<scratch>/w2p5_twice.py` rows `1`-`4` with controls
  `C1`-`C6`; the inverse proof is `<scratch>/w2p5_ast_identity.py` against
  `<scratch>/head_schema.py`. Both are re-runnable with the commands above and both live outside the
  repo; neither is a test to promote.
- The diff against HEAD is the whole cohort's, not this pass's — every prior pass is uncommitted.
  This pass changed exactly two lines of it, both inside `DjangoSchema`'s class docstring.

### Notes for Worker 1 (spec reconciliation)

- No spec amendment is owed. The five-homes sweep in `## Final verification (Worker 1, pass 2)`
  established that no spec, README or glossary states the duplicate-declaration rule at all, and
  this pass's own census re-derived the same population: the docstring was the last home of the
  narrowing and it is now the accurate form `docs/README.md` `### Production error policy` already
  ships.
- Nothing new surfaced. The `docs/GLOSSARY.md` residual is unchanged and still routed to Worker 0's
  "Record and card" step.

---

## Review (Worker 3, pass 5)

Re-review of the one dispatched item: the `same` qualifier deleted from
`django_strawberry_framework/schema.py::DjangoSchema`'s class docstring, with the one-word rewrap.

### The landed lines are the dispatched replacement, byte-for-byte

Not read side by side. The replacement block was cut out of
`## Final verification (Worker 1, pass 2)` `### Worker 3's escalated Low, decided` by line span
(the second fenced block of that dispatch) into `<scratch>/w1_replacement.txt`, and
`schema.py` lines 714-715 into `<scratch>/work_lines.txt`:

```
3fc80906b8bf694368c0cb53fac19a079e20949bc9e043fdffe54f86da90e1a7  work_lines.txt
3fc80906b8bf694368c0cb53fac19a079e20949bc9e043fdffe54f86da90e1a7  w1_replacement.txt
cmp: identical
```

Same digest, `cmp` silent, including the leading four spaces and both newlines. 79 and 68
characters, both under the 99-character limit; the file carries no non-ASCII byte.

### The pass-5 delta is those two lines and nothing else

The diffstat pair `8/5 → 9/6` is arithmetic, not a population, so the pass-4 content was
reconstructed rather than trusted: substitute the dispatch's OLD two lines back into the working
file (`<scratch>/pass4_recon.py`), which reproduces `8 insertions / 5 deletions` against
`git show HEAD:django_strawberry_framework/schema.py` exactly — the number the pass-4 review was
written against — while the working file is `9 insertions / 6 deletions`. `git diff --no-index`
between the reconstruction and the working file is one hunk of `-2/+2`, the two dispatched lines.
Nothing rode along under a one-line description, and the subclass clause, its stated reason and the
factory sentence are byte-unchanged, so the pass-4 reading of them still holds.

### The diff is docstring-only, proved by stripped-AST identity, with a literal control

`git show HEAD:...` written to `<scratch>/head_schema.py` (never a checkout — this tree carries a
concurrent session's work) and compared by `<scratch>/w3p5_ast.py`, written this pass:

```
HEAD stripped-AST: 709b1682db88897b8d4805b0b658e9e6121fdcb27ac440f1ebbfa3e7d0be4e15
WORK stripped-AST: 709b1682db88897b8d4805b0b658e9e6121fdcb27ac440f1ebbfa3e7d0be4e15
AST identical with docstrings stripped: True
source bytes differ (the edit is real): True
control structural differs: True
control literal nodes mutated: 1 | control literal mutation differs: True
top-level nodes (pre-strip): 55 55
```

The digest is the `709b1682...` the final verification expected the fix to preserve. The literal
control mutates `schema.py::DjangoSchema.__init__` #"is declared once" — a NON-docstring string in
the parsed copy, and the nearest live twin of the sentence under edit — and the digest moves, so a
stray edit to the error message 20 lines below would have been in range. (The `55` here is the
pre-strip count of the same 54 nodes Worker 2 reported after stripping the module docstring.)

### The reworded clause is true, measured on my own instrument

Read first: `DjangoSchema.__init__` raises on a presence conjunction #"if declared_resource is not
None and resource_policy is not None"; `_consumer_extension_entries` raises on #"if declared is not
None" after `_entry_resource_policy` returns non-`None`. Neither body evaluates what either
declaration holds.

Then executed — `<scratch>/w3p5_twice.py`, written this pass, not Worker 2's probe, and carrying a
row its probe and the final verification's both lack:

```
A == B ? False | A.max_depth 7 | B.max_depth 19
OK  1 resource_policy=A + entry declaring B (DIFFERENT)        | REFUSED | A schema's resource policy is declared once...
OK  2 resource_policy=A + entry declaring A (SAME object)      | REFUSED | A schema's resource policy is declared once...
OK  3 two entries declaring B and A (DIFFERENT)                | REFUSED | DjangoSchema(extensions=[...]) carries two...
OK  4 two entries declaring the SAME object                    | REFUSED | DjangoSchema(extensions=[...]) carries two...
OK  5 two entries declaring EQUAL-VALUED distinct objects      | REFUSED | DjangoSchema(extensions=[...]) carries two...
OK  C1 one declaring entry only                                | BUILT   | errors=None data={'ping': 'pong'}
OK  C2 resource_policy= only                                   | BUILT
OK  C3 bare authority CLASS entry                              | BUILT
OK  C4 bare authority INSTANCE entry (declares nothing)        | BUILT
OK  C5 error-authority CLASS entry                             | BUILT
OK  C6 no extensions at all                                    | BUILT
refused rows: 5/5   building controls: 6/6   failures=0
```

Row `5` is the one that matters for a deleted `same`: two DISTINCT `ResourcePolicy` objects of
EQUAL value. "Same" has three available readings — identity, value equality, and "twice for one
schema" — and the refusal is indifferent to all three, so no reading survives in which the word
contributed a true condition. Six controls build and answer `{ ping }`, `C1` separating the clauses
(one declaration admitted, two refused), so the refusal rows are not vacuous. Each row carries its
expected verdict, so a row cannot pass by landing in the wrong column.
`shasum -a 256 examples/fakeshop/db.sqlite3` is `563b26d8...` before and after the probe —
unchanged, the digest every prior pass recorded.

### High:

None.

### Medium:

None.

### Low:

None. The pass-4 escalated Low is closed by this diff: its subject phrase #"and declaring the same
policy" now has 0 occurrences in the file.

### DRY findings

None. The diff adds no logic, no literal and no abstraction; the stripped-AST identity above is the
mechanical form of that. The docstring and `docs/README.md` `### Production error policy` state one
contract in two registers — a consumer page and a class docstring — which is the paired-home shape
this cohort has been aligning, not duplication to consolidate. Their subclass clauses are now
word-for-word parallel ("supplied as a class or as an instance, and whether or not it declares a
policy of its own - because a subclass can override the hook that does the enforcing while still
answering every check for it") and their duplicate-declaration clauses agree with no qualifier.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty; `__all__` and the re-export list are
unchanged.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

The pass touches no rendered doc, no release metadata, no KANBAN row and no archived spec — the one
file is package source. The doc surface it has to agree with was re-checked anyway, since the edit's
whole purpose is agreement: `docs/README.md:154` ships "Declaring the policy twice raises
`ConfigurationError` at construction", the unqualified form, and the docstring now matches it.

Retired-qualifier census, stated as a population and case-insensitively — the lowercase-only needle
has a capital-`D` blind spot that hides the README's own sentence, which is how a "0 hits" sweep
would have read as clean while the paired home was never examined. Over 845 readable files across
`django_strawberry_framework/`, `docs/` (excluding `docs/shadow/`), `tests/`, `examples/`,
`README.md`, `GOAL.md`, `AGENTS.md`, `START.md`, `KANBAN.md`, per occurrence rather than per line:

| needle | occurrences | where |
|---|---|---|
| `same policy` | 19 | 1 unrelated optional-import comment (`optimizer/nested_planner.py`), 2 archived specs on unrelated policies, 16 in per-cycle scratch (this artifact + two worker-memory files) |
| `declaring the policy` | 14 | `schema.py` (this edit), `docs/README.md:154`, 12 in this artifact |
| `declaring the same` | 11 | all per-cycle scratch |

Positive control: every needle is found somewhere, so the sweep is not reporting emptiness. **0
occurrences in any spec, README, glossary or package statement of this contract.** The docstring was
the last standing home and it now carries the accurate form.

### Spec slice checklist walk

Unchanged by this pass. Its boxes were audited at `## Final verification (Worker 1, pass 2)`
`### Spec slice checklist audit`; this pass applies one dispatched wording fix and addresses no
additional box.

### Failability proofs

No re-run set, and that is legal here rather than chosen: the mandatory floor applies to boundaries
the diff introduces, and the stripped-AST identity above proves the diff introduces none — all 54
stripped top-level nodes are digest-identical to HEAD, so no guard, cap, rejection path or
validation branch entered through it. Worker 2's `None; this pass introduced no new boundary.` is
audited and correct. The boundaries the reworded sentence *describes* are pre-existing at HEAD and
were re-measured as behavior above, not as failability.

### Hot-path budget verification

Not applicable; plan declares no hot path.

### Static helper use

`scripts/review_inspect.py` skipped, per `BUILD.md` `### When to run the helper during build`: no
new `.py` file, nothing under `optimizer/` or `types/`, and 0 lines of new logic (AST-identical to
HEAD). There is no repeated-literal or import-boundary evidence for it to produce.

### Test staleness

Swept independently of the diff's file list. No test, script or example reads
`DjangoSchema.__doc__` or asserts on the docstring's text (`__doc__` has 10 occurrences tree-wide in
`.py` files; all are `argparse(description=__doc__)`, a `type()` namespace, a `functools` `assigned`
tuple and one comment — none reaches this docstring). No standing doc cites into the edited
paragraph: of 32 markdown occurrences of `schema.py::DjangoSchema`, the specs and `DONE/` plan cite
the symbol or its methods, never a `#"substring"` of this paragraph. The three `#"and declaring the
same policy"` citations that no longer resolve are all in THIS artifact's prior pass records, which
are per-cycle scratch, exempt from the `path::Symbol` rule and never edited — the expected
consequence of a dispatch being applied, not stranded refs.

### Gates

- `uvx pre-commit run --files django_strawberry_framework/schema.py` — **pass**, all six hooks
  Passed, no hook modified a file.
- `uv run python scripts/check_citations.py --check` — **pass**,
  `OK: 1104 citations resolve (925 in 448 .py files, 179 in KANBAN.md).`
- `uv run pytest -n0 tests/test_schema.py --no-cov -q` — **pass**, `141 passed in 2.11s`, 0
  collection errors. No `--cov*` flag used.
- `git status --short` — identical to this cohort's recorded baseline plus `docs/README.md`,
  `django_strawberry_framework/schema.py` and this artifact. No path outside the writable set
  appeared; nothing was reverted.

### What looks solid

- The edit was applied as a literal substitution of the dispatched block rather than reconstructed,
  which is what makes the byte-for-byte check above decisive instead of approximate.
- The rewrap moved exactly one word. Deleting `same` alone would have left a short line; pulling
  `twice is` up keeps the paragraph inside the limit with no other line reflowed, so every
  previously-reviewed clause stays byte-identical and no prior review's reading is invalidated.
- Worker 2's precondition check — reading the diff for a second hunk BEFORE the first edit — is what
  makes its `+1/-1` delta claim checkable at all.

### Temp test verification

None created. Verification was two scratch scripts outside the repo
(`<scratch>/w3p5_ast.py`, `<scratch>/w3p5_twice.py`) plus two extracted text files; neither is a
test to promote, and the behavior they exercise is already pinned by `tests/test_schema.py`.

### Notes for Worker 1 (spec reconciliation)

- No spec amendment is owed and none is proposed. The five-homes sweep at
  `## Final verification (Worker 1, pass 2)` is re-derived above on a wider and case-insensitive
  population and reaches the same answer: no spec, README or glossary ever stated this rule
  narrowly.
- The `docs/GLOSSARY.md` residual is untouched by this pass and stays routed to Worker 0's
  "Record and card" step.

### Review outcome

`review-accepted`. No High, Medium or Low finding is open; the pass-4 escalated Low is closed by
this diff. The dispatched replacement landed byte-for-byte, the delta is exactly those two lines,
the diff is docstring-only by stripped-AST identity with a literal control, the reworded clause is
true under all three readings of the deleted word, and all four gates are green.

---

## Final verification (Worker 1, pass 3)

Closing pass over Worker 2's pass-5 one-word fix and Worker 3's pass-5 acceptance. Nothing below is
accepted on either record: every instrument was written or re-derived this pass, and the two figures
the dispatch pinned as its expectation (the byte-identity of the landed lines, and the stripped-AST
digest) were reproduced from scripts written here.

Diff under verification: `git diff HEAD --numstat -- docs/README.md django_strawberry_framework/schema.py README.md`
— `29 9 docs/README.md`, `9 6 django_strawberry_framework/schema.py`, two files. `README.md` (root)
is absent from the diffstat and `grep -c 'strawberry\.Schema\|extensions=\[' README.md` returns **0**,
so the plan's step 6 no-op still holds, re-derived rather than read off a prior pass.

### The two docstring lines are byte-identical to the pass-2 dispatch

Not compared by eye. The dispatch's replacement block was cut out of
`## Final verification (Worker 1, pass 2)` `### Worker 3's escalated Low, decided` by line span
(artifact lines 2619-2620) into `<scratch>/w1p3_dispatch.txt`, and `schema.py` lines 714-715 into
`<scratch>/w1p3_shipped.txt`:

```
3fc80906b8bf694368c0cb53fac19a079e20949bc9e043fdffe54f86da90e1a7  w1p3_dispatch.txt
3fc80906b8bf694368c0cb53fac19a079e20949bc9e043fdffe54f86da90e1a7  w1p3_shipped.txt
cmp: IDENTICAL
```

Same digest, `cmp` silent, leading four spaces and both newlines included; 79 and 68 characters, both
under the 99-character limit. The digest reproduces the one Worker 3's pass-5 review recorded, from a
separately taken extraction. `grep -c "declaring the same policy" django_strawberry_framework/schema.py`
returns **0** — the retired qualifier is gone from the file the dispatch named.

### The pass-5 delta is exactly those two lines, and the pass-4 content is unchanged

The diffstat pair `8/5 → 9/6` is arithmetic, not a population, so the pass-4 state was reconstructed
instead of trusted: substituting the dispatch's OLD two lines back into the working file
(`<scratch>/w1p3_pass4_recon.py`) and diffing against `git show HEAD:django_strawberry_framework/schema.py`
reproduces **`8 5`** — the figure the pass-4 review was written against — while the reconstruction
against the working file is **`2 2`**, the two dispatched lines and nothing else. The subclass clause,
its stated reason and the factory sentence are therefore byte-unchanged, and every prior pass's
reading of them still holds.

### Stripped-AST identity vs HEAD, with a structural and a string-literal control

`git show HEAD:django_strawberry_framework/schema.py` was written to `<scratch>/w1p3_head_schema.py`
— never a checkout, the tree carries a concurrent session's work — and compared by
`<scratch>/w1p3_ast_identity.py`, written this pass, which `ast.parse`s both, deletes the leading
string `Expr` from every `Module` / `ClassDef` / `FunctionDef` / `AsyncFunctionDef` body (substituting
`Pass` where that empties one) and digests `ast.dump(..., annotate_fields=True)`:

```
HEAD stripped-AST sha256: 709b1682db88897b8d4805b0b658e9e6121fdcb27ac440f1ebbfa3e7d0be4e15
WORK stripped-AST sha256: 709b1682db88897b8d4805b0b658e9e6121fdcb27ac440f1ebbfa3e7d0be4e15
AST identical with docstrings stripped: True
source bytes differ (the edit is real): True
control structural (extra statement) differs: True
control literal needle present: True (nodes mutated: 1)
control literal mutation differs: True
top-level node counts (pre-strip): 55 55 equal: True
top-level node counts (post-strip): 54 54 equal: True
RESULT: OK
```

Three controls, because an identity assertion is self-satisfying without them: the structural control
proves the digest can move at all; the **string-literal** control mutates
`schema.py::_declared_authority` #"subclasses the package's" in the parsed copy and shows the digest
moves, so a stray edit to a non-docstring literal would have been in range of the instrument and did
not happen; `source bytes differ` proves the identity is a real strip rather than a no-op read of one
file. The digest is the `709b1682…` the pass-2 dispatch named as its expectation, reproduced here
from an independently written script.

### Gates

- `uvx pre-commit run --files docs/README.md django_strawberry_framework/schema.py` — **pass**, all
  six hooks Passed (`kanban tracked path constants`, `source layout`, `ruff format`, `ruff check`,
  `kanban anchors`, `citations resolve`). **Disclosed:** the FIRST invocation reported `kanban
  anchors … Failed - files were modified by this hook` while printing its own
  `OK: 76 card anchors are unique, none collides with the 146 glossary anchors, and the KANBAN.md
  render carries no duplicate id.` That hook reads the board DB, which a concurrent session is
  writing; `git status --short` either side shows the moved path is not one of this cohort's two
  files, and the immediate re-run passed clean with no intervening edit of mine. Recorded rather than
  silently re-run once. Neither cohort file was modified by any hook: `source layout`, `ruff format`
  and `ruff check` all Passed on the first invocation too.
- `uv run python scripts/check_citations.py --check` — **pass**, exit 0:
  `OK: 1104 citations resolve (925 in 448 .py files, 179 in KANBAN.md).`
- `uv run pytest -n0 tests/test_schema.py --no-cov -q` — **pass**, `141 passed in 1.86s`, **0**
  collection errors. No `--cov*` flag was used anywhere in this pass.

### Nothing else in the writable set moved since pass 2

`docs/README.md` is still **29/9**, and its content is re-derived rather than inferred from that
number. `<scratch>/w1p3_readme_census.py` (fence-tracking, code spans stripped **per line**) reports
every figure the pass-2 verification recorded, unchanged:

- 915 lines, fences balanced, 34 fenced blocks;
- **6** schema-constructing blocks, at lines 18, 95, 113, 139, 652 and 735, and **0** constructing a
  plain `strawberry.Schema`;
- **3** prose occurrences of `strawberry.Schema`, at lines 59, 124 and 204, and **0** inside any
  fenced block; **0** bare `Schema(` anywhere against **11** `DjangoSchema(`;
- link audit: **38** distinct `][label]` uses over 39 occurrences / **38** definitions, 0 missing, 0
  unused, 0 duplicate labels, all ten group headers present, every group alphabetical, every relative
  target resolving on disk. Root `README.md`: 21/21, 0 orphans, its `<!-- External -->` group still
  not alphabetical — pre-existing at HEAD in a file this cohort never touched.

`git diff HEAD -- django_strawberry_framework/__init__.py` is empty: `__all__` and the re-export list
are unchanged.

Staged-anchor sweep: `grep -rn 'TODO(spec-050' --include='*.py' --include='*.md' .` returns **4**
hits, all prose *about* anchors — two in this artifact's own pass-2 record, one in
`docs/bug_hunt/bug_hunt-0_0_1555.md`, one a historical count in
`docs/builder/DONE/build-038-form_mutations-0_0_12.md`. **No live `TODO(spec-050 slice N)` source
anchor exists**, so this cohort strands none. (The population grew by two since pass 2 because the
artifact recording that sweep is inside the population it counts.)

`shasum -a 256 examples/fakeshop/db.sqlite3` is
`563b26d8003c3c41072b7b7bbfc12fec524969aa3c9b258d7cdbac68ed32b52f`, the digest every prior pass
recorded — no probe of this pass wrote a tracked byte.

**Paths became dirty during this pass, none of them this cohort's.** `git status --short` was
captured three times across the pass; `examples/fakeshop/test_query/test_products_api.py` appeared
first, then `examples/fakeshop/test_query/test_library_api.py` and
`tests/mutations/test_resolvers.py`. All three are the concurrent session's / Cohort A's, all three
are outside this cohort's writable set, and the set is still growing — stated as a moving population
rather than a closed list. Reported, not touched, not reverted. Every other entry is the plan's
baseline-dirty set plus this cohort's two files and this artifact.

### The three homes of the contract still agree, measured as a population

A line grep cannot see this claim: the docstring wraps the sentence across lines and the error
literal is split across adjacent source lines, so a per-line sweep reads **1** hit and looks finished.
A whitespace-flattened walker over 751 readable `.py`/`.md` files (`.venv/` and `docs/shadow/`
excluded; positive control: the needle is found, so the sweep is not reporting emptiness) finds the
string `subclass can override the hook that does the enforcing while still answering every check for
it` **9** times: **2** in `django_strawberry_framework/schema.py` (the runtime error literal — the one
authoritative definition — and the class docstring), **1** in `docs/README.md`, and **6** in this
per-cycle artifact. One definition plus two projections, all in agreement. The carry-forward hazard
Worker 3 named stands unchanged and is an observation, not a deferred finding: the copies are
byte-identical today, there is no gate over prose, and the sweep vocabulary is
`override the hook that does the enforcing`.

The three spec edits the pass-2 verification made were re-checked at the **current** spec state,
which a concurrent cohort is editing right now: `### Decision 15`'s two widened ladder rungs (lines
1547-1548), `### Decision 21`'s separated construction-time rung (line 1723) and the
`## Definition of done` row's "an entry that RESOLVES into one refuses the operation instead" (line
2787) are all still present and still describe what the code does. No spec edit is owed by this pass,
and none was made — the spec and its rationale are outside this pass's writable set while the
concurrent final-verification pass holds them.

### Spec slice checklist audit

All three boxes remain `- [x]`, and each tick still has matching delivered text in the diff:

1. *State the trust contract … and the extension contract …* — **stands.** `### The trust boundary`
   carries Decision 20's three levels; the three `## Quick start` paragraphs carry Decision 21's three
   parts.
2. *Correct the executable examples …* — **stands**, on this pass's own fenced census: 6 schema
   blocks, 0 plain `strawberry.Schema`, 0 bare `Schema(`.
3. *The shipped docs state the trust contract where a deployer reads it …* — **stands.** With the
   pass-5 edit, the two README paragraphs, the `DjangoSchema` class docstring, the amended Decision 15
   ladder and the amended Decision 21 state one admission ladder, on both rungs and on the
   duplicate-declaration rung.

No box is ticked without a matching change; no box is left `- [ ]`.

### Failability, hot path, floor, DRY

- **Failability proofs.** Every build report records `None; this pass introduced no new boundary.`
  Confirmed mechanically rather than read: the `schema.py` diff is stripped-AST identical to HEAD
  across all 54 post-strip top-level nodes, so no guard, cap, rejection path or validation branch can
  have entered through it; the `docs/README.md` diff contains no Python. The obligation is empty, not
  sampled.
- **No fail-open shape landed.** There is no expression in either diff to fail open.
- **Hot path.** Plan declares `none`; neither diff adds runtime code (AST-identical). Nothing owed.
- **Floor verification.** The plan assigns this cohort no floor run; the full scope is the final
  gate's. Nothing owed here.
- **DRY.** No new duplication across this cohort and Cohort A, which touches no documentation. The
  trust contract's two homes are Decision 20's design and the README version is not a copy; the reason
  sentence's three homes are one definition plus two projections, counted above.

### Open items, each with a named owner

- **`docs/GLOSSARY.md`, four sites** — owner: **Worker 0's "Record and card" step**
  (`docs/builder/DONE/build-050-list_field_arguments-0_0_15.md` `## Close cycle (Decision 22)`), which
  already touches the board DB and regenerates the four generated docs. Path (a) of Worker 3's ranking,
  unchanged: the row is **not** deferred to another card and **not** narrowed, so no
  `### Deferred work catalog` entry is owed. Re-validated below.
- Nothing else is open. Both escalated Lows (the `schema.py` docstring twin, and the `same` qualifier)
  were dispatched and are closed in the diff; no High or Medium survives any pass; no item is routed
  forward without an owner.

### Notes for Worker 1 (spec reconciliation)

**The four routed `GlossaryTerm.body` replacement blocks are still valid.** A routed replacement is
only valid while the body it replaces still reads as quoted, so all four were re-checked verbatim
against the **current** rendered `docs/GLOSSARY.md` this pass (`<scratch>/w1p3_glossary_routing.py`),
not against the render they were written from. Each quoted old text is present and each maps to a
distinct owning term, so Worker 0's per-term DB edits have no ambiguity:

| routed site | owning term heading | rendered line |
|---|---|---|
| 1, fenced quick-start recipe | ``## `DjangoOptimizerExtension` `` (heading line 744) | 752 |
| 2, fenced schema-setup recipe + its "before `strawberry.Schema(...)` is constructed:" lead-in | ``## `finalize_django_types` `` (heading line 930) | 946, lead-in 936 |
| 3, INLINE recipe | ``## `BigInt` scalar`` (heading line 335) | 341 |
| 4, FIRST fenced block + its "into their `strawberry.Schema(...)` call." lead-in | `## strawberry_config` (heading line 1968) | 1978, lead-in 1972 |

The census holds too: **21** occurrences of `strawberry.Schema` over 20 lines in the rendered file, of
which those four are the row's described pairing; the `## strawberry_config` body's two OTHER blocks
(lines 1989, 1998) carry no `extensions=` entry and stay out of scope. No replacement block needs
rewriting.

**Instrument note on that re-check.** The site-1 needle (the two-line `_optimizer = …` /
`schema = strawberry.Schema(…)` pair) matches **twice**, because it is also the tail of site 2's
larger block. That is the needle's ambiguity, not drift — the two hits are the two distinct terms in
the table above. A checker that asserted "exactly one occurrence" would have reported a failure that
does not exist, and one that took the first hit would have edited the wrong term.

**No spec edit is owed, and none was made.** The spec and its rationale are held by the concurrent
Cohort A final-verification pass. The pass-2 edits survive at the current spec state (verified above),
and the five-homes sweep already established that no spec, README or glossary states the
duplicate-declaration rule at all, narrowly or otherwise.

### Final status

`final-accepted`. The dispatched two lines landed byte-for-byte on a digest taken this pass; the
pass-5 delta is provably those two lines with the pass-4 content byte-unchanged; the `schema.py` diff
is docstring-only under a stripped-AST identity carrying a string-literal control; `docs/README.md` is
unchanged at 29/9 with every census figure re-derived; all three gates are green and
`tests/test_schema.py` is 141 passed with 0 collection errors; and the one open item leaves with a
named owner.

### Summary

Cohort B rewrote every schema-constructing example in `docs/README.md` onto `DjangoSchema`, replaced
the quick-start extension paragraph with Decision 21's three separate rules, added
`### The trust boundary` under `## Production security profile` stating Decision 20's three trust
levels in the README's own voice, and brought the `### Production error policy` paragraph and
`DjangoSchema`'s class docstring onto the admission ladder the code actually answers — both rungs and
the duplicate-declaration rung. Root `README.md` is untouched, on evidence. One item outlives the
cohort with a named owner: the four `GlossaryTerm.body` edits for Worker 0's "Record and card" step.

### Spec changes made (Worker 1 only)

**None this pass**, by instruction and by finding: the spec and `-rationale.md` are being edited by the
concurrent Cohort A final-verification pass and are outside this pass's writable set, and no edit was
owed — the three pass-2 corrections are still present at the current spec state and still describe the
code, and the checklist boxes carry no deferral.

**Status-line re-verification.** The spec's opening lines were read this spawn. They describe the
build's current state and needed no edit; the header's Decision 21 summary sits at the level of the
class-or-factory spelling and per-operation isolation, which the ladder wording does not touch.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary-per-operation-extension-isolation]: ../GLOSSARY.md#per-operation-extension-isolation

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
