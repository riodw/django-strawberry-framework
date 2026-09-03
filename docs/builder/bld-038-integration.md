# Build: cross-slice integration pass

Spec reference: `docs/SPECS/spec-038-form_mutations-0_0_12.md` (whole file) and its
rationale companion `docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md`
(whole file)
Build plan: `docs/builder/build-038-form_mutations-0_0_12.md`
Status: final-accepted

## Artifact shape: one Worker 1 pass, so two template sections are not applicable

`## Build report (Worker 2)` and `## Review (Worker 3)` are **not applicable** here.
[`docs/builder/BUILD.md`][build-md] `## Cross-slice integration pass` assigns the pass
to Worker 1 alone and gives it one output, `bld-integration.md`; a builder is dispatched
only *after* it, and only if it records DRY or divergence findings that need a
consolidation loop. This pass found two divergences and repaired both inside its own
writable surface — the spec and its companion, which
[`docs/builder/BUILD.md`][build-md] `## Spec reconciliation` makes Worker 1's alone — so
there is no source diff for a builder to land and nothing a reviewer could review that is
not itself a spec edit. `### Isolation is non-waivable` is not weakened: it bars the
author of code from approving that code, and nothing here is code. The isolation that
does apply — the spec must not be graded against itself — was discharged by Slice 1,
which graded all 140 corpus rows against `HEAD` under two independent Worker 3 passes.

**Hot-path declaration: none.** No package `.py` changed at any point in this cycle, so
no per-request, per-resolver, per-row, per-connection or per-outbound-message cost can
have been added. Measured rather than asserted: `git status --short` over
`django_strawberry_framework/` shows only the concurrent session's baseline-dirty paths,
and the five files this cycle wrote are two example-app modules and three test modules.

**Floor-verification scope: none for this pass.** The cycle's floor obligation was
declared by Slice 1 (GAP-2 and GAP-3), run by its Worker 2 build pass, re-executed by
Worker 3, and re-executed a third time by Slice 1's final verification. Floor facts,
copied from [`docs/builder/BUILD.md`][build-md] `## Floor verification`: the supported
floor is Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**. Not
load-bearing for any reasoning in this pass, and the shared `.venv` was read, never
stated from memory and never mutated:

```
$ uv pip list | grep -Ei '^(django|strawberry-graphql|django-filter) '
django                      6.1
django-filter               26.1
strawberry-graphql          0.324.0
$ uv run python -c "import sys; print(sys.version.split()[0])"
3.14.2
```

That is the newest supported set, not the floor. No `uv pip install` was issued by this
pass at all.

---

## Plan + Final verification (Worker 1)

### Method

Every count below was measured by the instrument that reports it, as it was written.
Multi-file sweeps ran through a `uv run python - <<'PY'` heredoc with the population
asserted, never a bare `for f in $FILES` (`START.md` "Instruments that lie": zsh
word-splitting makes that one iteration over the whole string). Every sweep prints its
population and carries a **live** control, so a zero is a measurement rather than a
broken instrument. Every claim about a baseline-dirty file is stated against
`git show HEAD:<path>` copied to a scratch path **outside** the repository; no
`git stash`, `git checkout`, `git restore` or `git worktree` was run.

**One instrument fault caught and corrected mid-pass, recorded because it is the class
`START.md` warns about.** My first size measurement read the spec at 175,953 and the
companion at 80,522 and disagreed with Slice 2's recorded 176,965 / 80,892, which read
as a divergence. It was not: Python's `len(Path(...).read_text())` counts **characters**,
and both files are dense with `→`, `—`, `×` and `✓`. Slice 2's figures are bytes and are
correct. Every size in this artifact is `stat -f %z`.

---

## The six mandatory preconditions

### Precondition 1 — read every prior `bld-038-*` artifact in slice order

Discharged, all three in slice order and in full, not "as needed":

| Artifact | Lines | Status read |
|---|---|---|
| `docs/builder/bld-038-slice-0-rationale_extraction.md` | 606 | `final-accepted` |
| `docs/builder/bld-038-slice-1-code_conformance.md` | 3,588 | `final-accepted` |
| `docs/builder/bld-038-slice-2-spec_reconciliation.md` | 855 | `final-accepted` |

Plus the build plan (401), `AGENTS.md`, `START.md`, `docs/builder/BUILD.md` (576),
`docs/builder/ARTIFACT.md`, `docs/builder/worker-1.md`, `GOAL.md`, `docs/GLOSSARY.md`
(skimmed), `CHANGELOG.md`, both spec files, and my own memory file first. No other
worker's memory file was opened.

The reading is load-bearing rather than ceremonial: Slice 0's routed item 7 (the staged
TODO-anchor cell) appears in **no** other routed list, and Slice 1's final-verification
consolidation is the only place the 54 raw routed items are reconciled to the 35 Slice 2
actually worked from.

### Precondition 2 — the static inspection helper ran, or was skipped with a reason, for every Python file with review-worthy logic the cycle touched

Discharged with **zero gaps**. The cycle touched exactly five `.py` files and **no**
package `.py` under `django_strawberry_framework/`. Shadow output verified present on
disk for all five, plus the five package files Slice 1's grading pass ran it on:

| File | Shadow output on disk | Owning pass |
|---|---|---|
| `examples/fakeshop/apps/products/forms.py` | `docs/shadow/examples__fakeshop__apps__products__forms.{overview.md,stripped.py}` | Worker 3, review pass 1 |
| `examples/fakeshop/apps/products/schema.py` | `…apps__products__schema.*` | Worker 3, review pass 1 |
| `examples/fakeshop/test_query/test_products_api.py` | `…test_query__test_products_api.*` | Worker 3, re-review (refreshed after the apply-changes pass) |
| `tests/forms/test_resolvers.py` | `tests__forms__test_resolvers.*` | Worker 3, review pass 1 |
| `tests/forms/test_sets.py` | `tests__forms__test_sets.*` | Worker 3, review pass 1 |
| `django_strawberry_framework/forms/converter.py` | `…forms__converter.*` | Worker 1, Slice 1 grading pass |
| `django_strawberry_framework/forms/inputs.py` | `…forms__inputs.*` | Worker 1, Slice 1 grading pass |
| `django_strawberry_framework/forms/sets.py` | `…forms__sets.*` | Worker 1, Slice 1 grading pass |
| `django_strawberry_framework/forms/resolvers.py` | `…forms__resolvers.*` | Worker 1, Slice 1 grading pass |
| `django_strawberry_framework/mutations/fields.py` | `…mutations__fields.*` | Worker 1, Slice 1 grading pass |

`ls docs/shadow | wc -l` → **20** files, i.e. exactly the `.overview.md` + `.stripped.py`
pair for each of the ten. Every recorded invocation passed `--output-dir docs/shadow`;
the two build passes' deliberate non-invocation is recorded with its reason in each
build report (`### When to run the helper during build` scopes Worker 2's use to "when
the plan or prior review asks for it", and neither did — no new `.py` file, nothing under
`optimizer/` or `types/`, zero lines of new logic under
`django_strawberry_framework/`). **No skip is unrecorded and no file with review-worthy
logic is missing an overview.** This pass ran no new invocation and wrote nothing under
`docs/shadow/`.

**One qualification the shadow output itself does not carry.** `review_inspect.py` reads
the **working tree**, so the three baseline-dirty `forms/` overviews are a superset of
`HEAD`. Measured, not assumed: `forms/inputs.py`'s overview reports `import keyword` and
two `received out-of-vocabulary operation_kind` literals, and `forms/resolvers.py`'s
reports an import of `materialize_relation_id_container` — all three **absent** from the
`HEAD` copies (`grep -c` → 0 at `HEAD`, 1 / 2 / 2 in the working tree; `forms/inputs.py`
is 757 lines at `HEAD` and 799 now). Those are the concurrent session's hunks, and they
are why 2 of the 4 repeated literals the `forms/inputs.py` overview reports are not part
of any shipped contract.

### Precondition 3 — compare the `Repeated string literals` sections across every shadow overview

Discharged, and the instrument had to be replaced to discharge it honestly.

**The shadow sections are truncated, so comparing them directly is a measurement with two
blind spots.** `scripts/review_inspect.py::_render_literals` caps the section at 25
entries; `examples__fakeshop__test_query__test_products_api.overview.md` ends
`- ... (96 more not shown)` and `tests__forms__test_resolvers.overview.md` ends
`- ... (7 more not shown)`. Comparing the ten sections as emitted yields 88 entries, 72
distinct literals and **10** appearing in two or more files — a figure that is wrong by
construction, because 103 entries were never printed. There is no flag to lift the cap
(`--help` carries none).

So the population was re-derived directly, replicating the helper's own rule read out of
its source: `visit_Constant` on `str` values, `strip()`ped, `len >= --literal-min-length`
(default **8**), excluded if in `DEFAULT_MARKERS`, with module / class / function
docstring statements skipped. Over the same ten files:

- **174** distinct literals repeated within their own file
- **11** appearing in two or more files (not 10)

| Files | Occ | Literal | Where |
|---|---|---|---|
| 5 | 57 | `category` | products `forms.py` 3, products `schema.py` 3, `test_products_api.py` 20, `test_resolvers.py` 23, `test_sets.py` 8 |
| 3 | 25 | `form_class` | `forms/sets.py` 10, `test_resolvers.py` 2, `test_sets.py` 13 |
| 3 | 15 | `description` | products `schema.py` 4, `test_products_api.py` 8, `test_resolvers.py` 3 |
| 3 | 12 | `operation` | `forms/sets.py` 2, `test_resolvers.py` 2, `test_sets.py` 8 |
| 2 | 69 | `categoryId` | `test_products_api.py` 47, `test_resolvers.py` 22 |
| 2 | 21 | `updateItem` | `test_products_api.py` 11, `test_resolvers.py` 10 |
| 2 | 20 | `createItem` | `test_products_api.py` 10, `test_resolvers.py` 10 |
| 2 | 14 | `Not authorized` | `test_products_api.py` 11, `test_resolvers.py` 3 |
| 2 | 11 | `injected` | `test_resolvers.py` 5, `test_sets.py` 6 |
| 2 | **10** | **`attachment`** | **`test_products_api.py` 3, `test_resolvers.py` 7** |
| 2 | 9 | `permission_classes` | `test_resolvers.py` 2, `test_sets.py` 7 |

**`attachment` is the one the truncation hid, and it is this cycle's own.** It is the
`Item` / `MediaSpecimen` file column the GAP-2 rows drive, and it now spans the package
and live tiers. A cross-file literal reaching two tiers is precisely the DRY candidate
this step exists to surface — and it is a candidate that a comparison of the emitted
sections could not see.

**Verdict on all eleven: no DRY finding.** Every one is declarative vocabulary, not
duplicated logic: a model field name inside a `Meta.fields` tuple or an ORM kwarg
(`category`, `description`, `attachment`), a `Meta` key the framework publishes
(`form_class`, `operation`, `permission_classes`), a GraphQL wire name inside a per-row
query string (`categoryId`, `createItem`, `updateItem`), a framework error string the
tests assert on (`Not authorized`), or a test sentinel value (`injected`). Naming a
constant for a `Meta.fields` entry or a wire name would be strictly worse — it hides the
declaration the example app exists to demonstrate — and it is the pattern every one of
the six example apps already follows. Worker 3 reached the same verdict on the subset it
could see; this pass reaches it on the full population.

**There is no production-code DRY scan to run, and that is a measurement, not an
excuse.** `## Cross-slice integration pass`'s literal-comparison step assumes slices that
wrote production code. This cycle wrote **zero** package `.py` bytes: the two package
files whose overviews carry cross-file literals (`forms/sets.py`) contribute them from
code present at `HEAD` and untouched by any pass. Performing a duplicated-helper or
repeated-ORM-pattern scan over that diff would be a scan over an empty set reported as a
clean result, which is the shape `START.md` calls a control that cannot fail.

### Precondition 4 — compare the `Imports` sections across every shadow overview

Discharged. All ten `Imports` sections read; dependency direction is one-way with exactly
one deliberate back-edge.

**The documented boundary holds.** `forms/` depends on `mutations/`, `utils/`, `registry`,
`scalars` and `exceptions`, and on nothing that depends back on it at module level:

- `forms/converter.py` → `..exceptions`, `..utils.converters`, `..utils.inputs`
- `forms/inputs.py` → `..exceptions`, `..mutations.inputs`, `..registry`, `..scalars`,
  `..utils.{inputs,relations,strings}`, `.converter`
- `forms/resolvers.py` → `..mutations.resolvers`, `..utils.{querysets,write_transaction,write_values}`
- `forms/sets.py` → `..exceptions`, `..mutations.{inputs,permissions,sets}`, `..registry`,
  `..utils.inputs`, `.inputs`

**The one back-edge, and the mechanism that makes it legal.** `mutations/fields.py`
carries `from ..forms.sets import iter_form_mutations` — `mutations/` reaching into
`forms/`, the reverse of every edge above. It is a **function-local** import, not a
module-level one, which is exactly how the load cycle is broken: `forms/sets.py` imports
twenty-four names from `mutations/sets.py` at module scope, so a module-level import the
other way would be a hard cycle. `forms/resolvers.py` uses the same device for
`from ..utils.errors import validation_error_to_field_errors`. Both are one-way at import
time and bidirectional only at call time. Recorded rather than flagged: the spec's own
Decision 5 axis 1 states the reason (the field must not `issubclass(DjangoMutation)` or
import a form base), and Slice 1 graded it `BUILT-CONFORMANT`.

**No sibling imports from outside the documented boundary.** The two example-app modules
import only `django`, `strawberry` and the package root's public surface
(`django_strawberry_framework import DjangoFormMutation, DjangoModelFormMutation, …`) —
never a package submodule — which is the consumer-facing shape the example app exists to
demonstrate. The three test modules reach package internals
(`django_strawberry_framework.forms.sets import _cached_build_form_input, …`) as the
package tier is licensed to.

**One import-shape observation, not a finding.** `test_products_api.py` carries four
function-local `from django.contrib.auth.models import Permission` imports beside a
module-level one. All four are pre-existing at `HEAD` and none is in this cycle's added
lines.

### Precondition 5 — walk every accepted artifact's `What looks solid` and `DRY findings` sections for deferred follow-up

Discharged. Four such sections exist across the three artifacts (Slice 0 has neither, being
a procedural-closure slice with no Worker 3 pass; Slice 2 likewise). Every item walked:

| Source | Item | Disposition here |
|---|---|---|
| Review 1 `### DRY findings` | existence challenge on `DefaultCategoryItemModelForm` + `CreateDefaultCategoryItemViaForm` — they earn it; `StampedItemModelForm` could not have carried the case | re-confirmed: `StampedItemModelForm.Meta.fields = ("name", "category")` keeps `category`, so `validate_constraints()` catches the duplicate pre-`save()`. Nothing to delete. No follow-up. |
| Review 1 `### DRY findings` | `UpdateItemWithFileViaForm` earns its existence at near-zero cost | re-confirmed against the diff: three `Meta` lines over the existing `ItemFileModelForm`, and `CreateItemWithFileViaForm`'s `operation = "create"` line is diff **alignment**, not a change. No follow-up. |
| Review 1 `### DRY findings` | the two `get_form_kwargs` overrides in `products/schema.py` are near-identical — considered, not a finding | re-confirmed: the signature is the framework's published hook signature and the example app exists to show consumers the plain override. No follow-up. |
| Review 1 `### DRY findings` | repeated literals across the new example code are `Meta.fields` names | superseded by this pass's full-population re-derivation (precondition 3), which reaches the same verdict over 11 cross-file literals rather than 5. Closed. |
| Review 1 `### DRY findings` | the two GAP-2 package rows are not near-copies; the second is load-bearing | re-confirmed by node-id arithmetic: proof entry 2's three rows are one `Item` row plus two `MediaSpecimen` parametrizations. No follow-up. |
| Review 1 `### DRY findings` | overlap accepted between the `Item` package row's end-to-end leg and the live preserve row | re-confirmed: the package row's primary subject (the direct `_reconstruct_partial_data` dict assertion) is unreachable from a live request, so `AGENTS.md`'s promote-and-delete rule does not bite. No follow-up. |
| Review 2 `### DRY findings` | `_CREATE_DEFAULT_CATEGORY_ITEM_VIA_FORM` is a Medium avoided, placed the way the file places such constants | re-confirmed present and used twice. The pre-existing twice-inlined `createItemWithFileViaForm` string was correctly left alone. No follow-up. |
| Review 2 `### DRY findings` | existence challenge on the positive leg — earns it, decisively | re-confirmed: proof entry 4 fails exactly one row and it is that one. No follow-up. |
| Review 2 `### DRY findings` | the repeated-literal output carries nothing new | qualified by precondition 3: it carried one thing the truncated section could not show (`attachment`). Graded, no finding. |
| Review 2 `### DRY findings` | `create_users(1)` + `seed_data(1)` + `_login_with_perm(...)` repetition is `AGENTS.md` rule 8's mandate | re-confirmed. No follow-up. |
| Review 1 `### What looks solid` | six items (mixed-diff enumeration, the honest negative result, the discretion override, GAP-1 as two node ids, the GAP-3 separation, registry isolation) | none carries deferred follow-up; each is a confirmation. Nothing to land here. |
| Review 2 `### What looks solid` | six items | same. |

**Deferred follow-up that had to land in this pass: none from these sections.** The only
deferrals the chain carried forward are the `TODAY.md` drift (Slice 1 `### Ruling 2`, path
(b), owner the maintainer) and Slice 2's four catalog items, all of which are
`bld-038-final.md`'s and are carried forward verbatim in `### Deferred work catalog`
below. `START.md` warns that a round's self-reported deferral is a claim, so each was
re-derived: see that section.

### Precondition 6 — sweep the whole tree for staged anchors naming this build's spec or card

Discharged. Worker 0's pre-flight figure was **re-derived rather than accepted**, and the
re-derivation partly corrects it.

**The mandated sweep, verbatim, over the whole tree:**

```shell
grep -rEn 'TODO\(spec-038|TODO-(ALPHA|BETA|STABLE)-038' .
```

→ **22 hits, every one in `docs/`, none in source, tests, examples or scripts.**

**The load-bearing half, with the population printed and a live control** (a heredoc, so
no zsh word-splitting):

| Tree | Population | `038` anchors | Live control: `TODO-<MILESTONE>-0NN`, any card |
|---|---|---|---|
| `django_strawberry_framework/` | 112 files / 3,544,603 bytes | **0** | 1 |
| `tests/` | 139 files / 5,525,522 bytes | **0** | 8 |
| `examples/` | 182 files / 2,033,440 bytes | **0** | 21 |
| `scripts/` | 23 files / 400,500 bytes | **0** | 0 |

The control fires 30 times across three of the four trees, so those zeros are
measurements. `scripts/`' control is itself 0, so it gets a second one: 4 of its 23 files
contain the bare token `TODO`, which reads the tree the `038` pattern reads. **A
repo-wide positive control** on the same anchor grammar returns **1,075** occurrences
across `KANBAN.md`, `TODAY.md`, `BACKLOG.md`, `docs/TREE.md`, two `tests/*.py` and ~30
specs — the instrument is not broken.

**Worker 0's pre-flight claim, re-derived at `HEAD`.** Its substantive half holds and I
confirm it independently: zero anchors in source and tests. Its enumeration of the doc
hits is **incomplete**. It records "the only hits are in `docs/dry/dry-0_0_12.md` … and
the spec's own prose". At `HEAD` there are **four** files, not two:

| File at `HEAD` | Hits | Grade |
|---|---|---|
| `docs/dry/dry-0_0_12.md` | 4 | a closed cycle's scratchpad describing the anchors' removal. Per-cycle scratch, exempt. Correct. |
| `docs/SPECS/spec-038-form_mutations-0_0_12.md` | 4 | see below |
| `docs/SPECS/spec-036-mutations-0_0_11.md` | 1 | **not named by Worker 0** |
| `docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md` | 1 | **not named by Worker 0** |

`KANBAN.md`, `KANBAN.html` and `BACKLOG.md` carry **zero** — the fence's exclusion of
them was precautionary rather than load-bearing, because card 038 is now
`DONE-038-0.0.12` and its board id no longer matches the `TODO-` grammar.

**The spec's four `HEAD` hits are now two, and Slice 2's item 32 is confirmed
discharged.** Occurrence counts, not matching lines:

| Token | `HEAD` spec | spec now | Companion now |
|---|---|---|---|
| `TODO-ALPHA-038-0.0.12` | 3 | **1** | 2 |
| `TODO(spec-038` | 1 | **1** | 0 |
| `TODO-ALPHA-039` | 3 | **0** | 1 |
| `TODO-ALPHA-040` | 3 | **0** | 1 |
| `TODO-ALPHA-043` | 1 | **0** | 0 |

Slice 0 retired the revision-history occurrence; Slice 2 retired the `## Doc updates`
card-wrap occurrence and all seven sibling-card citations. `grep -c 'TODO-anchor only'`
over the spec → **0**, so the discharged anchor Slice 1's routed item 32 flagged in the
`## Implementation plan` Slice-2 cell **is** gone. Confirmed independently:
`def _input_type_name` does not exist package-wide at `HEAD`.

**The two survivors in the spec are both correct.** `## Current state` #"planned by
`TODO-ALPHA-038-0.0.12`" is a dated observation quoting a `docs/TREE.md` state (Slice 2's
note N2 diffed the quotation both ways: 2 occurrences at `731fecd8^`, 0 in the current
render — true on its own date, so the observation framing carries it), and the spec's own
prose describing the anchor discipline (#"a source-site `TODO(spec-038 Slice N)` comment
naming") is the rule's statement, not an anchor. The companion's four are Revision-1
provenance, a record that the citations **were** replaced, and the quotation being graded.

**The two `spec-036` hits are a real residue, and they are outside this cycle's writable
surface.** `docs/SPECS/spec-036-mutations-0_0_11.md` #"reused unchanged by
`TODO-ALPHA-039-0.0.13`, `TODO-ALPHA-038-0.0.12`" and its companion's #"lists
`TODO-ALPHA-037` / `TODO-ALPHA-038` / `TODO-ALPHA-039`" name three cards that have all
since shipped. This is the same class Slice 2 retired **inside** `spec-038` (items 16,
17, 15) — a parallel site in a sibling archived spec, which is the partial-claim signature.
My writable surface is `spec-038` and its companion only, so it is routed to
`### Deferred work catalog` rather than edited.

---

## The divergence inventory

`START.md` "Past mistakes": *a reconciliation slice introduces contradictions it cannot
see; the integration pass owes the divergence INVENTORY, not the consistency of its own
discharging text.* Slice 2 rewrote 33 items across a spec with **five homes per
contract** — Decision, `## Slice checklist`, `## Edge cases and constraints`,
`## Test plan`, `## Definition of done` — and cross-checking those five is the one
instrument no single slice runs, least of all the slice doing the rewriting.

### The instrument

The spec was sliced on its heading structure into the five homes (14 Decision bodies
68,182 bytes; `## Slice checklist` 19,096; `## Edge cases` 8,944; `## Test plan` 7,546;
`## Definition of done` 18,953 — the last figure includes the trailing link-definition
block, which carries no `##` heading and therefore falls inside that slice; that artifact
of the slicer is graded below rather than left to distort a count). For each of **26**
contract classes Slice 2 touched, two matrices were run over the five homes:

- a **retired-spelling matrix** — the shortest distinctive phrase of the *pre-rewrite*
  claim, counted as occurrences; any non-zero is a divergence candidate;
- a **shipped-spelling matrix** — the distinctive token of the *rewritten* claim; a zero
  in a home the contract has says that home did not receive the statement.

Then the six highest-risk multi-home contracts (the pipeline step order, the two
narrowing guards, the plain-form authorization posture, the three reconstruction shapes,
the two allowed-key sets, the reverse-map record) were read home by home, because a
token matrix cannot see a home that agrees in vocabulary and disagrees in subject — which
is exactly where the one real defect was.

### Result: 2 divergences, both repaired; 20 apparent residues graded and dismissed

Raw retired-spelling residue: **9 non-zero cells** across 26 contracts × 5 homes. Graded:

**Divergence 1 — the reverse-map record's OWNERSHIP disagreed across four homes. Repaired.
This is the inventory's worst item.**

Slice 2's item 3 rewrote the reverse-map record from the spec's
`(input_attr, graphql_name) → (form_field_name, kind)` tuple "retained" by
`forms/inputs.py` to the shipped truth: the record type is the shared
`utils/inputs.py::InputFieldSpec`, and `forms/converter.py` "owns the constants and not
the record type". It applied that in **two** homes — Decision 7's body and the
`## Slice checklist` Slice-1 sub-check — and its artifact records exactly those two.
**Three further homes went on saying the old thing, and two of them contradicted the
corrected Decision rather than merely lagging it:**

- **`## Definition of done` item 2**, whose grammatical subject is
  `forms/converter.py`, read "… hits the **raising** default →
  `ConfigurationError` **and the reverse-map `InputFieldSpec` record** (…)". It attributes
  the record to the module Decision 7 now says does not own it — the same sentence, two
  homes, opposite answers.
- **`## Implementation plan` Slice-1 cell** read "`forms/converter.py` (new;
  `convert_form_field` fail-loud dispatch + the `input_attr → (form_field_name, kind)`
  reverse map)". Same contradiction, plus the retired tuple spelling.
- **`## Test plan` `test_converter.py` row** read "**the
  `input_attr → (form_field_name, kind)` reverse map**" — the retired spelling, in the
  row Slice 2's note N1 deliberately left in place on placement grounds.

Occurrence count of the retired tuple phrase: **4 at `HEAD`, 3 still live after Slice 2,
0 now.** This is the same class Slice 2 *did* catch for the Slice-2 cell (`registry.py`)
and the Slice-3 cell (the helper locations) — and missed for the Slice-1 cell, which is
the partial-claim-fix signature Slice 2's own carry-forward names: *the routed list's
anchor is a sample of the population, not the population.* The routed item said "both
homes"; the population was five.

Repaired in all three, recorded under `### Spec changes made (Worker 1 only)`. The
`test_converter.py` row keeps its tier — N1's grading that the clauses are correctly
pinned in `tests/forms/test_inputs.py` stands and is not reopened — and only its record
spelling changed.

**Divergence 2 — Decision 8 cites another enumeration's step ordinal inside the Decision
that owns its own step numbering. Repaired.**

Slice 2's largest edit renumbered Decision 8's seven steps into the shipped
**locate → authorize → decode → construct/validate → write → re-fetch → return** and
swept the step citations. Its own new preamble sentence then read:

> The order is single-sited in `mutations/resolvers.py::run_write_pipeline_sync`, whose
> own docstring **states it as step 3**, #"authorize BEFORE decode", and which every
> write flavor rides.

The ordinal is true of `run_write_pipeline_sync`'s **own** six-item docstring list, where
authorize is third (1 open atomic, 2 locate, 3 authorize, 4 decode, 5 write, 6 tail) —
read out of `git show HEAD:django_strawberry_framework/mutations/resolvers.py`. It is
false in the only enumeration a reader of this Decision has: three lines below, **step 3
is the Decode**. Two enumerations, one bare ordinal, in adjacent sentences — and the
routed item that commissioned the renumber (item 22) said in terms *"Cite by **content**,
never by ordinal, in the rewrite"*. The rule was applied to the old text and not to the
replacement.

It is also the residue of a repair Slice 2 records making: it found that a reflowed line
had put `#"authorize BEFORE decode"` at column 0, where a leading `#` renders as an H1,
and reflowed it mid-line. The reflow is what produced the sentence.

Repaired: the citation is now by content with no ordinal. Postcondition measured — `step
\d` occurrences in the spec went 11 (`HEAD`) → 10 (post-Slice-2) → **9**, and every one
of the nine was read against Decision 8's renumbered list and resolves:

| Line's claim | Resolves to |
|---|---|
| "carried to step 4 as the `instance=` kwarg" ×2 | 4 Construct + validate ✓ |
| "gate (step 3, which runs before the form regardless)" | 3 Decode ✓ |
| "mapper reused per step 5" | 5 Write ✓ |
| "validation-error mapper reused per step 4" | 4 Construct + validate ✓ |
| "relation-decode spine of step 3" | 3 Decode ✓ |
| "step 5 stays a single `form.save()`" | 5 Write ✓ |
| "pipeline step 6" (Decision 9) | 6 Re-fetch ✓ |
| "Decision 8 step 1" (Decision 11) | 1 Locate ✓ |

Slice 2's own disposition arithmetic also closes: 11 at `HEAD`, 3 deleted with the
Ordering-correction paragraph, 2 new ones written by the rewrite → 10, minus this
pass's 1 → 9.

### The 20 apparent residues, each graded

**Instrument false positives (5).** `froze` matched inside `frozenset(effective field
names)` twice — the shape-identity tuple, which is the *rewritten* text.
`partial_input_class` ×2 sits inside the *rewritten* two-set sentence ("Both add
`form_class` and drop `model` / `input_class` / `partial_input_class`"), correct and
identical in both its homes. And the `## Definition of done` slice's two
frozen-vocabulary hits are the trailing link-definition block (`[rationale-d2]`'s anchor
slug), not DoD prose — the slicer artifact named above.

**Licensed survivors, `## Current state` (4).** `_locate_instance`,
`_authorize_or_raise`, `_refetch_optimized` and `_validation_error_to_field_errors`
each survive exactly once, all four inside `## Current state`'s single sentence
describing what `mutations/resolvers.py` shipped *before* this card. That section's
bullets are **dated observations** and stand under
[`docs/builder/BUILD.md`][build-md] `### `## Current state`: observations stand,
predictions do not`; Slice 2's own carry-forward says so.
**Retirement proof for the class Slice 2 declared:** every underscore name the spec
asserted the *form pipeline calls* is at **0** — `_coerce_lookup_id` 1→0,
`_decode_relation_id_set` 5→0, `_raw_choice_value` 1→0, `_save_or_field_errors` 5→0,
`_refetch_optimized` 2→1, `_locate_instance` 2→1,
`_validation_error_to_field_errors` 5→1 (the three survivors all being the
`## Current state` sentence), `_build_payload` and `_not_found_error` 0 throughout.

**Licensed survivors, the `036`-frozen SLOT (6).** All fourteen
`froze|frozen|byte-identical` matches in the spec were enumerated and read. Six are the
uniform `node` / `result` **slot**, which genuinely is frozen — the finding was about the
**envelope** — in `## Non-goals`, `### Explicitly do not borrow` and Decision 6's
`Meta.return_field_name` paragraph. Slice 2 recorded leaving exactly six; the count
matches exactly.

**Licensed survivors, Decision 2's heading and its anchors (4) and the mapper claim (1).**
Decision 2's heading keeps "the frozen `036` contracts are reused unchanged" by Slice 2's
recorded anchor-count decision, and three of the fourteen matches are that heading's slug
inside in-page links and a link definition. The one surviving `byte-identical` is the
mapper-output claim ("byte-identical to a model `full_clean()` failure"), which is true
and is not the envelope claim — again exactly as Slice 2 recorded.
**Retirement proof for the envelope class: 0 real residue.** `froze for` 2→0,
`frozen \`FieldError\`` 2→0, `` `036`-frozen envelope `` 1→0, `byte-identical` 7→1
(the mapper claim).

### Under-descriptions graded as non-defects, not silently dropped

Two homes carry *less* than their sibling without contradicting it. `START.md`'s rule is
that **two disagreeing** is a defect; redundancy that compresses is not, so both are
recorded and neither is edited.

- **The `## Slice checklist` Slice-3 sub-check omits the three-shapes clause.** Contract
  9 (the reconstruction) has four homes. Decision 8 states it in full ("takes **three**
  forms, single-sited in `forms/resolvers.py::_reconstruct_partial_data`"), and
  `## Edge cases` ("in **three** shapes") and `## Definition of done` item 4 ("in the
  three shapes a provided field decodes to") both carry it. The Slice-3 sub-check carries
  only "the form's **full declared** field set, overlaid by `provided_data`" and points
  at the Decision. Nothing in it is false. Recorded because Slice 2's item 9 describes
  all three siblings as receiving the same sentence and one received half of it.
- **`### Explicitly do not borrow` still says the `036` `FieldError` "is reused
  unchanged".** Decision 2 now *defines* that phrase ("'reused unchanged' is a statement
  about *this* card's own footprint on it, not a promise that the type will never grow"),
  so the bullet is licensed by the home that owns the vocabulary. Occurrence count 4 at
  `HEAD` → 3 now, the three being this bullet, Decision 2's heading, and Decision 2's own
  definition of the phrase.

### Pre-038-state descriptions inside Decision bodies, recorded and not fixed (8)

`_input_type_name` ×6 and `_validate_mutation_meta` ×2 survive in the spec. Neither
symbol exists at `HEAD` (`_validate_mutation_meta` only as a docstring mention in
`mutations/sets.py`; `def _input_type_name` nowhere package-wide — measured). Every
occurrence describes the **pre-`038` baseline the card changed**: Decision 6's
"The shipped `DjangoMutationMetaclass` calls the module function
`_validate_mutation_meta`, whose allowed-key set … has **no** `form_class`" is the
problem statement the Decision then solves, and the Slice-3 cell's "delete the transient
`_input_type_name` twin" is the deletion the card performed. Slice 1 graded the checklist
one explicitly ("a build-time instruction, not a live contract") and routed neither.
They are a **different class** from Slice 2's six — those were names the spec asserted the
form pipeline *calls now* — and grading them would be a contract question about how far a
shipped spec may narrate the state it replaced. Low; recorded so silence is not read as
absence; no edit. `_ALLOWED_MUTATION_META_KEYS`, named in the same sentence, **does**
still exist at `HEAD`.

### The six highest-risk multi-home contracts, read home by home

| Contract | Decision | `## Slice checklist` | `## Edge cases` | `## Test plan` | `## Definition of done` |
|---|---|---|---|---|---|
| shipped step order | D8 steps 1-7 in `locate → authorize → decode → construct/validate → write → re-fetch → return` ✓ | Slice-3 sub-check narrates the same order in prose ✓ (the prose-only site no "step" grep can find) | no ordering to fix — bullets, not a sequence | lists behaviors, not a sequence; its "before the form" clause is true | item 4 narrates `locate → authorize → decode → is_valid() → write → re-fetch → payload` ✓ |
| two narrowing guards | D7 "**There are TWO narrowing guards, keyed on that one waiver**", naming `guard_partial_required_column_less_fields` and why the partial guard is scoped to column-less fields ✓ | — | bullet retitled "**A narrowing that drops a required form field.** Two guards keyed on one waiver" ✓ | — | item 2 "any required field on `create`, a required **column-less** field on `update`" ✓ |
| plain-form authorization | D11 `(DenyAll,)` default + `permission_classes = []` opt-in + `DjangoModelPermission` reject ✓ | — | bullet now states all three, and points at D11 ✓ | — | — |
| three reconstruction shapes | D8 step 4, three named branches, `model_to_dict` ×5 all inside that one bullet ✓ | full declared field set; three-shapes clause omitted (graded above) | "in **three** shapes" ✓ | — | item 4 "in the three shapes a provided field decodes to" ✓ |
| two allowed-key sets | D6 names both by their `*_WRITE_META_KEYS` bases ✓; D10 states the operation split correctly ✓ | names both by their private symbols with the full key sets ✓ | — | — | item 3 ✓ |
| reverse-map record | D7 `utils/inputs.py::InputFieldSpec`, converter owns the constants only ✓ | Slice-1 sub-check ✓ | — | **was retired spelling → repaired** | **was contradicting → repaired** |

---

## Spec ↔ companion coherence sweep

Both files were rewritten this cycle, so `START.md`'s "Sweep both files of a pair" bites
in both directions.

**Structure agrees.** 14 `### Decision N` headings in the spec, 14 `## Decision N`
sections in the companion. **0** `- **Post-ship:** none recorded yet.` placeholders
remain (Slice 2 replaced all 14). 35 `**Post-ship:**` bullets, matching Slice 2's own
per-Decision table exactly (1+2+1+1+1+4+8+9+1+1+2+1+2+1).

**Cross-file anchors resolve both ways.** Every `<file>#<anchor>` definition was resolved
by slugging the target file's own headings under the GitHub rule, not by eye:

| Direction | Anchor uses | Distinct | Unresolved |
|---|---|---|---|
| companion → spec | 14 | 14 | **0** |
| spec → companion | 15 | 15 | **0** |

**Does any `**Post-ship:**` bullet describe a spec statement that no longer exists in
that form?** Instrument: extract every double-quoted phrase of four or more words from
the companion (**20**) and test verbatim resolution in the current spec, whitespace
normalized. Six resolve; **14 do not** — and all 14 grade as **retired by design**. Each
is a quotation of text the companion is *recording as removed* ("settled with its
fallback in Risks", "both failure modes the review names", "`uv.lock` if it carries the
package version", "a duck-typed `_mutation_meta` + `_payload_type_name` check", "this card
must generalize", "Preferred resolution"), or a commit message ("keep null booleans
optional on every path", "materialize one-shot form field declarations before reuse"), or
a rejected alternative, or a `START.md` section title. **None asserts current spec text.**
One (`") is unchanged; the Decision's "`) is my own regex splitting on a nested quote.

**Does the spec assert anything the companion contradicts?** The four contracts whose
rewrite this pass touched or re-graded were read in both files. The companion's
reverse-map bullet ("`forms/converter.py` now owns only the four `kind` constants and
re-exports them from `utils/inputs.py`") is the statement my repair brought the two
lagging spec homes into line with — it was right and the spec was wrong, which is the
reverse of the usual direction and is why the sweep is owed in both directions. The
companion's ordering bullet cites `#"authorize BEFORE decode"` **by content, with no
ordinal** — the discipline the spec's preamble had dropped.

**No self-falsifying byte count in either file.** Every size figure in the companion is a
measurement of `HEAD` or of the Slice-0 move, correctly past-tensed — including the one
Slice 2 had to re-date ("It **stood at** 164,240 bytes … when the move finished (Slice 2's
reconciliation has since edited it)"). The spec carries no byte figure at all. This
matters because the pair has now been edited a third time, and a present-tense count
would be false again.

**Two-way link-definition audit after my edits**, with fenced blocks and inline code spans
stripped before sweeping, every non-URL target resolved from the source file's own
directory (never a bare disk-exists check, which `START.md` calls fail-open):

| File | `][label]` uses | Distinct | Defs | Undefined | Unused | 10 group headers, canonical order | Dangling in-page anchors |
|---|---|---|---|---|---|---|---|
| spec | 511 | 100 | 100 | **0** | **0** | ✓ | **0** (143 uses, 19 distinct) |
| companion | 86 | 45 | 45 | **0** | **0** | ✓ | **0** (54 uses, 17 distinct) |

`[utils-inputs]` — the label my repairs lean on four more times — is defined and now used
14 times. No definition was added or pruned by this pass. **Postcondition sweep for the
defect Slice 2 hit twice:** zero lines in either file begin with `#` and are not a real
heading.

---

## Derived-description spot-check

`START.md` "Instruments that lie": *derived descriptions outlive sources; at a
reconciliation pass the defects are false descriptions of findings, not missed facts.*
Slice 1's verdict tables and Slice 2's change list are derived descriptions of source
that three passes have since read again, so a sample of each was re-measured against live
source with my own instrument.

**Slice 1 — 16 of 16 sampled claims held.**

| Claim | Measured |
|---|---|
| D3: 0 files carry `__init_subclass_with_meta__` / `MutationOptions` / `ClientIDMutation` at `HEAD` | 0 ✓ |
| D7: `_SCALAR_FORM_FIELDS` has 12 rows including `forms.JSONField` | 12 rows, `forms.JSONField: _scalar_converter(strawberry.scalars.JSON)` present ✓ |
| D13: `registry.py` is 610 lines with 0 `clear_form`, and drains `iter_subsystem_clears()` | 610 / 0 / present ✓ |
| D13: `types/base.py` is 1,954 lines with 0 `form_class` | 1,954 / 0 ✓ |
| D6: 0 files carry `return_field_name` package-wide | 0 ✓ |
| population: 300 `.py` files under `tests/` + `examples/fakeshop/` at `HEAD` | 300 ✓ |
| GAP-1: `def get_form(` = 0 occurrences at `HEAD` | 0 ✓ |
| GAP-1 closure: `def get_form(` = 2 now | 2 ✓ |
| GAP-2: `initial` = 0 occurrences under `tests/forms/` at `HEAD` | 0 ✓ |
| GAP-4: `get_form_kwargs` = 19 occurrences in 6 files at `HEAD` | 19 / 6 ✓ |
| D4: `forms/` holds exactly 5 files at `HEAD` | 5 ✓ |

One apparent failure was my own instrument (an AST walk that missed an annotated dict
assignment), re-run by reading the literal — 12 rows, claim confirmed.

**Slice 2 — 34 of 34 sampled claims held.** The full ten-name promoted-helper location
list re-measured with `git grep -l "^def <name>(" HEAD` (7 in `mutations/resolvers.py`,
`validation_error_to_field_errors` in `utils/errors.py`, `raw_choice_value` in
`utils/write_values.py`, `payload_object_slot` in `mutations/inputs.py` — all ten exactly
as recorded); `payload_object_slot` public at `731fecd8^` ✓; `_form_input_hook_identity`,
`make_meta_validating_metaclass`, `resolver_seams(… with_id=False)`, both
`_ALLOWED_*_META_KEYS`, `unset_default=(DenyAll,)`,
`guard_partial_required_column_less_fields` all present ✓; the three
`register_subsystem_clear` owner keys exactly `forms.declarations` /
`forms.input_namespace` / `forms.shape_cache` ✓; `build_payload_type`'s signature
character-for-character ✓; `mutations/operations.py`'s three symbols ✓;
`_validate_mutation_target`'s "does NOT require `_payload_type_name`" docstring ✓;
`pyproject.toml` with no `version` literal and `[tool.hatch.version]` present, `uv.lock`
as `source = { editable = "." }` ✓; `testing/client.py`, `testing/__init__.py`,
`auth/mutations.py`, `test_client_api.py` all present ✓; `make_declaration_registry`
instantiated by exactly `mutations/sets.py`, `forms/sets.py`, `auth/mutations.py` ✓;
products form mutations **8** now and **6** at `HEAD` ✓ (`CreateItemViaForm`,
`UpdateItemViaForm`, `CreateItemWithFileViaForm`, `UpdateItemWithFileViaForm`,
`CreateDefaultCategoryItemViaForm`, `CreateStampedItemViaForm`, `SubmitContact`,
`SubmitPing`). The one apparent failure was my own expectation (I predicted 4 files for
`make_declaration_registry` and measured 3, which is Slice 2's figure).

**Two figures have rotted, and naming them is the point.** The `tests/` +
`examples/fakeshop/` byte total went Slice 1 7,228,146 → Worker 2 7,228,167 → **7,228,146
again** as concurrent commits landed. Worker 3 had called Worker 2's figure the correct
one; both were correct on their own date and neither is now durable. The durable half —
300 files, `def get_form(` 0, `initial`-in-`tests/forms/` 0, `get_form_kwargs` 19/6 — all
re-derive exactly. Worker 3's own Low finding recorded the same rot for the
`unset_sentinel` counts. **A raw byte total of a tree a concurrent session is committing
into is a moving figure by construction; the file count and the zero-counts are what
carry the claim.**

**The ten node ids collect and are the ten claimed.** `uv run pytest --collect-only -n0
--no-cov` over the eight named functions → **10 tests collected**:
`test_get_form_only_override_trips_the_construction_hook_waiver[modelform]` / `[plain_form]`,
`test_get_form_only_override_builds_the_form_and_waives_the_required_guard`,
`test_get_form_kwargs_queryset_scoping_leaves_the_generated_input_shape_unchanged`,
`test_partial_update_omitting_file_field_keeps_it_out_of_the_reconstructed_data`,
`test_partial_reconstruction_excludes_every_file_field_flavor[attachment]` / `[image]`,
`test_update_item_with_file_via_form_omitting_the_file_preserves_it`,
`test_create_default_category_item_via_form_write_time_integrity_error_uses_envelope`,
`test_create_default_category_item_via_form_injects_the_default_category`.

---

## The partial-claim-fix sweep

`START.md`: *partial claim fix = dominant residual defect. One spelling fixed, parallel
site still live → cycle reopens.* Slice 2 itself found three parallel sites the routed
list had missed, so more were assumed to exist. Seven classes of fix, shortest distinctive
phrase, **occurrences** (not matching lines) in both files, `HEAD` spec as the baseline.

| Class | Phrases | `HEAD` spec | Spec now | Companion | Retirement |
|---|---|---|---|---|---|
| A. underscore-prefixed helper names for symbols that no longer exist | 13 | 32 | 11 | 12 | **0** for the pipeline-calls sub-class; 4 licensed in `## Current state`, 8 pre-`038`-state descriptions graded above |
| B. frozen-envelope vocabulary | 5 | 16 | 4 | 7 | **0** real; survivors are Decision 2's defining sentence + the licensed heading + `### Explicitly do not borrow` |
| C. pre-ship card citations for shipped siblings | 3 | 7 | **0** | 2 | **0** |
| D. review-finding labels (`P1`/`P2`/`P3`, `AR-*`, `Medium-1`) | 8 | 61 | **0** | 21 | **0** |
| E. chronology hedges | 10 | 11 | **0** | 8 | **0** |
| F. retired ownership / location claims | 14 | 15 | **0** | 5 | **0** |
| G. reverse-map tuple spelling | 2 | 5 | **0** (was 3) | 1 | **0 after this pass's repair** |

**Every companion hit is correct by design and was individually checked.** The
companion's job is to record what the spec retired, so it necessarily quotes the retired
vocabulary — 21 label occurrences, 8 chronology phrases, 5 ownership claims, all inside
`**Post-ship:**` bullets that name them as removed. Its four card-id mentions are
Revision-1 provenance, a record that the citations *were* replaced, and a quotation being
graded.

**Class D's retirement in the spec is total and its arithmetic closes.** Slice 2 recorded
retiring 62 label occurrences with a post-sweep assertion of `residual label occurrences:
0`. Measured now: `(P1` 21→0, `(P2` 33→0, `(P3` 1→0, `AR-H1` 1→0, `AR-H4` 1→0, `AR-H5`
2→0, `AR-M6` 1→0, `Medium-1` 1→0 = **61 by these anchors**, and **zero** bare `P1`/`P2`/
`P3` tokens anywhere in the spec.

**Class D has a parallel site in shipped source that Slice 2's own sweep falsified, and
it is a NEW defect this cycle created.** Not residue of an old fix — a consequence of a
new one. **11** comment and docstring citations in package `.py` pair a `spec-038`
pointer with a P-label:

```
django_strawberry_framework/forms/converter.py:66   # this module (spec-038 Decision 7 P1).
django_strawberry_framework/forms/converter.py:238  ``String`` - spec-038 Decision 7 P2):
django_strawberry_framework/forms/inputs.py:267     ``base_fields`` (spec-038 Decision 7 P3):
django_strawberry_framework/forms/inputs.py:309     """Return the generated input-class name for a form shape (spec-038 Decision 7 P1).
django_strawberry_framework/forms/inputs.py:561     ``field.required``** (spec-038 Decision 7 P2 - ...
django_strawberry_framework/forms/inputs.py:664     not the built input shape (spec-038 Decision 7 P2, the create-required guard).
django_strawberry_framework/forms/inputs.py:745     **The create-required-narrowing guard (spec-038 Decision 7 P2).** ...
django_strawberry_framework/forms/sets.py:244       (the cache key excludes ``guard_required`` - spec-038 Decision 7 P2).
django_strawberry_framework/forms/sets.py:253       (spec-038 - the P1 decode reverse map).
django_strawberry_framework/forms/sets.py:268       # declaration, not the built input shape (spec-038 Decision 7 P2). ...
django_strawberry_framework/mutations/sets.py:195   load-bearing ordering (spec-038 Decision 7 P2 / spec-039 Decision 7): the
```

Before Slice 2 a reader following one of these opened Decision 7 and found the matching
`(P2 …)` marker. After it, the spec carries **zero** P-label tokens, so all 11 point at a
vocabulary their target no longer contains. The `spec-038 Decision 7` half is a spec
decision pointer and is the "kept" category under `START.md` "Style Rio cares about"; the
trailing label is now orphaned residue. **Ungated:** `scripts/check_citations.py` is
`path::Symbol`-only, so no gate can see it — the exact ungated class `START.md` warns
about for `#"substring"` refs.

Wider population of the same vocabulary in the `038` subsystem: **33** occurrences across
7 files (`forms/inputs.py` 10, `forms/sets.py` 9, `test_products_api.py` 5, products
`forms.py` 4, products `schema.py` 2, `forms/converter.py` 2, `forms/resolvers.py` 1; the
four `tests/forms/` modules carry **0**). All 33 are present at `HEAD` — measured file by
file against the `HEAD` copies, so none is the concurrent session's.

**Fixing it is neither mine nor available.** 22 of the 33 are package `.py` under
`django_strawberry_framework/`, which no pass in this cycle wrote and which
`worker-1.md` `## Scope` bars me from editing. Routed to `### Deferred work catalog`.

**Zero label-carrying lines among the 851 lines the cycle added.** Every added line across
the five files was extracted by unified diff against the `HEAD` copies and swept for six
classes of banned provenance — severity labels, worker / review-round attribution, slice
or DRY-pass numbering, "previously" / "as of `0.0.N`", plan / commit banners and board
residue, review-doc filenames. **0 hits in all six classes.** (Population: products
`forms.py` 34, products `schema.py` 52, `test_products_api.py` 173,
`tests/forms/test_resolvers.py` 356, `tests/forms/test_sets.py` 236. The last two are
**mixed** diffs, so a share of those lines is the concurrent session's; the sweep is clean
either way.)

---

## Comment and docstring coherence across the ten new test rows and the two example-app surfaces

**They tell one story, in the products app's existing idiom, with no process provenance.**

- **`examples/fakeshop/apps/products/forms.py`.** The module docstring's enumeration was
  corrected rather than extended, and the count claim re-derived here: **6** classes, **6**
  docstring bullets, sets identical (`ItemModelForm`, `ContactForm`, `PingForm`,
  `StampedItemModelForm`, `ItemFileModelForm`, `DefaultCategoryItemModelForm`). The
  retired "Four forms cover the spec's Decision-12 live matrix" is now "These forms cover
  …", which is the shape that cannot rot as the list grows.
  `DefaultCategoryItemModelForm`'s docstring states the mechanism, not the provenance:
  why `Meta.fields` narrows `category` away, what Django's
  `_get_validation_exclusions` / `_post_clean` then skip, and why the FK is attached in
  `__init__` rather than later ("before the validation window it is deliberately hidden
  from").
- **`examples/fakeshop/apps/products/schema.py`.** `UpdateItemWithFileViaForm` and
  `CreateDefaultCategoryItemViaForm` both open with a one-line summary and then state the
  invariant. Both explicitly tie back to a sibling: the file mutation names the
  reconstruction contributing "NO key for a file field", the race mutation names
  "the same construction-hook shape `CreateStampedItemViaForm` uses for `user`". That
  cross-reference is what makes the pair read as one story rather than two additions.
- **The eight new test functions.** All present on disk, all docstrings read end to end,
  **0** banned-provenance tokens. Each states the *load-bearing* property rather than the
  action, and each says why the obvious weaker assertion would not do: "the load-bearing
  property is the ABSENCE of the file key … not merely that the stored file happens to
  survive"; "Both halves are asserted because either alone is non-distinguishing"; "the
  coarser `get_form` is the operand that only ever decides for a mutation overriding it
  ALONE". They are the same voice as the rows around them.

**One coherence finding, Low.** Two adjacent enumerations of the same eight-mutation set
disagree in completeness. The `test_products_api.py` section comment names all eight by
wire name and says so ("eight fields in all, the count this comment must keep").
`products/schema.py`'s `Mutation` docstring names **seven**, omitting `submitPing`
entirely — pre-existing (it named five of six at `HEAD`, omitting `submitPing` then too)
and carried forward by the cycle's widening of the paragraph. Not a contradiction, and
the file it lives in is a builder's to edit, not mine. Recorded; routed to
`### Deferred work catalog`.

---

## Duplicated helpers, naming, error handling, exports, responsibilities

The remaining `## Cross-slice integration pass` checks, answered against the cycle's
actual shape rather than performed over an empty diff:

- **Duplicated helpers across slices: none, and none was possible.** Slices 0 and 2 wrote
  Markdown only. Slice 1's builder wrote no helper of any kind — its own plan required
  "New helpers justified: none" and the build report records reusing
  `tests/forms/test_resolvers.py`'s existing `_build_item_form_schema` / `_schema` /
  `_AllowAll` / `_uniq`, and the live tier's `_post_graphql` / `seed_data` /
  `create_users` / `_login_with_perm`. The one new module-level name is a query-string
  constant, `_CREATE_DEFAULT_CATEGORY_ITEM_VIA_FORM`, which replaces a would-be second
  inlined copy.
- **Inconsistent naming or error handling between slices: none.** The new test names all
  follow the tier's `test_<subject>_<property>` shape and name the property, not the
  mechanism. No new error message, exception type or error string was introduced anywhere
  — measured: the added lines contain no `raise` of a new class and no new message
  literal (`ConfigurationError` is referenced, never redefined).
- **Repeated ORM / queryset patterns to centralize: one read, deliberately not
  centralized.** `CreateDefaultCategoryItemViaForm.get_form_kwargs` issues
  `models.Category.objects.order_by("pk").first()` per call of that one example-app
  mutation. It sits in the pipeline's read phase before `pipeline_write_phase()` opens,
  it is acceptance-fixture code outside the coverage gate, and factoring it out would hide
  the consumer-facing override the example exists to demonstrate. Worker 3 recorded the
  same reading.
- **Misplaced responsibilities between modules touched by different slices: none, and the
  one candidate was graded.** The only ownership question the cycle raised is the
  reverse-map record's, and it was a *documentation* misplacement across five spec homes
  rather than a code one — Divergence 1, repaired. The code has been single-sited on
  `utils/inputs.py::InputFieldSpec` since `60dbf469`.
- **Missing or too-broad exports: none.** `git diff -- django_strawberry_framework/__init__.py`
  is empty and the file is not even dirty against `HEAD`; `__all__` and the re-export list
  are untouched. Both Worker 3 passes verified this independently and I re-derived it.
  `django_strawberry_framework/__init__.py` #"from .forms import DjangoFormMutation,
  DjangoModelFormMutation" and both names in `__all__` remain the whole public surface
  this card owns.

---

## Gates run this pass, with results

| # | Command | Result |
|---|---|---|
| 1 | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-038-form_mutations-0_0_12.md` | **PASS** — `OK: 31 terms - all have glossary entries and at least one spec link.`, exit 0. Run **before** and **after** the repairs; same 31 both times. |
| 2 | `uv run python scripts/check_citations.py --check` | **PASS** — `OK: 940 citations resolve (785 in 435 .py files, 155 in KANBAN.md).` (938 at Slice 2, 939 before my edits from a concurrent commit, 940 after — my repairs added one `::Symbol` citation and every one resolves.) |
| 3 | `uvx pre-commit run --files docs/SPECS/spec-038-form_mutations-0_0_12.md docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md` | **PASS**, all six hooks, first run, exit 0. **No hook rewrote either file** — proved rather than assumed: `stat -f %z` is byte-identical before and after (177,321 and 82,413). The two `ruff` hooks report `(no files to check) Skipped`, which is the mechanical confirmation this pass has no source diff. |
| 4 | `uv run ruff format --check .` | **exit 2, and not this cycle's.** It cannot parse `tests/rest_framework/test_sets.py`. Scoped to the five files this cycle wrote: `5 files already formatted`, exit 0. |
| 5 | `uv run ruff check .` | **exit 1, 325 errors, and not this cycle's.** All 325 are in the single file `tests/rest_framework/test_sets.py`. Scoped to the five files this cycle wrote: `All checks passed!`, exit 0. See `### Escalations`. |
| 6 | `git diff --check` | 8 lines, all trailing whitespace in `docs/feedback2.md` — a baseline-dirty maintainer-input file outside this pass's set. The five files this cycle wrote are clean. Same reading both Worker 3 passes recorded. |
| 7 | `uv run pytest --collect-only -n0 --no-cov <the eight new functions>` | **PASS** — `10 tests collected`, the ten node ids named above. |
| 8 | two-way link-definition audit, on-disk path resolution, in-page and cross-file anchor resolution, both files | **PASS** — 0 undefined uses, 0 unused defs, 0 dangling anchors, all 10 canonical group headers present and in canonical order in both files. |
| 9 | `uv pip list` / `python -V` on the shared `.venv` | read, not stated from memory: django 6.1, strawberry-graphql 0.324.0, django-filter 26.1, Python 3.14.2 — the newest supported set, not the floor. Not mutated. |

`pytest` was otherwise neither run nor needed: this pass edits two Markdown files. **No
`--cov*` flag was passed to anything.** The full sweep is the final gate's job, not this
pass's, and `### Escalations` records the one thing standing in its way.

---

### Spec changes made (Worker 1 only)

Every edit is located by **heading and quoted phrase, never a line number**. All were
applied by assert-all-then-write scripts holding an ordered list of
`(old, new, expected_count)` triples that assert `text.count(old) == n` for **every**
triple before applying **any** — so a partial match aborts having written nothing
(`START.md` "Enumerate, never grep-count, before writing").

Byte counts, `stat -f %z`: spec **176,965 → 177,321** (+356); companion **80,892 →
82,413** (+1,521). The **corpus ratchet does not apply** — it binds
`docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md` and the four `worker-*.md` role
files, none of which this pass touched. These figures are this pass's closing measurement,
not a standing claim; the pair is still uncommitted and a later pass may edit either.

| Spec location (heading) | Quoted phrase changed | Reason | Divergence |
|---|---|---|---|
| `## Definition of done` item 2 | `**and the reverse-map `InputFieldSpec` record**` | attributed the record to `forms/converter.py`, the module Decision 7 states does **not** own it — two homes, opposite answers. Rewritten to give `forms/converter.py` the four `kind` constants "it re-exports from `utils/inputs.py` and does not itself define", and to place the per-field record at the `forms/inputs.py` build site the code actually uses | 1 |
| `## Implementation plan` Slice-1 cell | `` `convert_form_field` fail-loud dispatch + the `input_attr → (form_field_name, kind)` reverse map `` | same contradiction plus the retired tuple spelling. The cell now reads "fail-loud dispatch + the four `kind` constants, re-exported from `utils/inputs.py`" and moves "the per-field `utils/inputs.py::InputFieldSpec` reverse-map record" into the `forms/inputs.py` cell | 1 |
| `## Test plan`, `test_converter.py` row | `` **the `input_attr → (form_field_name, kind)` reverse map** `` | the retired tuple spelling. Now `**the utils/inputs.py::InputFieldSpec reverse-map record**`. **The row keeps its tier** — Slice 2's note N1 graded the clauses as correctly pinned in `tests/forms/test_inputs.py` rather than a gap, and that grading is not reopened; only the record's spelling changed | 1 |
| Decision 8 step 3 | `` `input_attr → (form_field_name, kind)` reverse map (`UNSET` stripped) `` | the retired tuple spelling inside the step that consumes the record. Now "the shared `utils/inputs.py::InputFieldSpec` reverse-map record of [Decision 7]", so all five homes speak one vocabulary | 1 |
| Decision 8 preamble | `whose own docstring states it as step 3, #"authorize BEFORE decode", and which every` | the ordinal is true of `run_write_pipeline_sync`'s own docstring list and false in Decision 8's, whose step 3 is the Decode three lines below. Now `whose own docstring pins it (#"authorize BEFORE decode") and which every` — cited by content, no ordinal | 2 |

**Companion changes (same pass, both files swept as a pair).** Two `**Post-ship:**`
additions, each keyed to the Decision that owns it so it can be looked up:

| Companion location | Addition | Reason |
|---|---|---|
| `## Decision 7 …` → `### Changes this Decision underwent`, appended to the `InputFieldSpec` bullet | that the record's **ownership** statement had five homes, not the two the reconciliation reached; which three lagged; that two of them contradicted the corrected Decision rather than merely lagging it; and that the `test_converter.py` row kept its tier | `START.md` "Sweep both files of a pair" — the companion recorded the record's single-siting without recording how many spec homes stated its ownership, so a later reader could not tell the fix had been partial |
| `## Decision 8 …` → `### Changes this Decision underwent`, appended to the ordering bullet | the surviving ordinal, why it was true of one enumeration and false in the other, and that the nine remaining `step N` citations all resolve against the renumbered list | same; and the ordering bullet is where a reader looks to find out what the renumber did and did not reach |

**No other file was touched.** `docs/SPECS/appx/spec-038-form_mutations-0_0_12-terms.csv`
was **not opened for writing** — the glossary gate stays at `OK: 31 terms`, verified
before and after. No definition was pruned or added, so the three CSV-pinned labels
Slice 0 had to hold clauses back for (`glossary-filterset`, `glossary-orderset`,
`glossary-finalize_django_types`) are untouched. Nothing under `docs/shadow/` was written.
No closeout surface, no `docs/builder/BUILD.md`, no `worker-*.md`, no build plan, no prior
`bld-038-*` artifact's sections. **`docs/SPECS/NEXT.md` remains modified and was not
touched** (see `### Deferred work catalog` item 4).

**Deferral reasons owed: none.** Everything this pass found is either repaired above,
graded as a licensed non-defect with the grade recorded, or carried into the catalog below
with a named owner.

---

### Deferred work catalog

Input for `docs/builder/bld-038-final.md` `### Deferred work catalog`, which Worker 1 is
the only author of. Items 1-5 are carried forward from Slice 2's own catalog input
(re-derived, not accepted on its self-report — `START.md`: a round's self-reported
deferral is a claim); items 6-8 are this pass's.

**1. The `TODAY.md` bullet, carried VERBATIM from
`docs/builder/bld-038-slice-1-code_conformance.md` `### Ruling 2`.** Owner: **the
maintainer**. Re-derived before carrying: `TODAY.md` is byte-identical to `HEAD` (42,568
bytes, `git show HEAD:` diffed clean), so nothing was pre-emptively touched, and the
eight-name set is confirmed at 8 classes / 8 `DjangoMutationField` rows.

> - **`TODAY.md` under-enumerates the products form-mutation surface — six named, eight shipped.**
>   Owner: **the maintainer** (no worker may edit it; the build plan's `## Scope fence` puts
>   `TODAY.md` out of scope for this whole cycle and the kanban DB with it, so this bullet is the
>   homing mechanism). Source: `docs/builder/bld-038-slice-1-code_conformance.md` `### Medium:`
>   ("The staleness sweep's population excluded the repo-root standing docs"), escalated again in
>   both review passes' `### Notes for Worker 1 (spec reconciliation)` item 1. Cause: this slice
>   added `updateItemWithFileViaForm` and `createDefaultCategoryItemViaForm` to
>   `examples/fakeshop/apps/products/schema.py::Mutation` under the GAP-2 / GAP-3 escalations —
>   surface the fence did not anticipate. Three homes, each resolving exactly once, each listing
>   six of the eight: `TODAY.md` #"- **Form-based mutation write surface**",
>   `TODAY.md` #"as of `0.0.12` the form-backed mutations",
>   `TODAY.md` #"**Form-backed mutations (`0.0.12`).**". The full set is
>   `createItemViaForm`, `updateItemViaForm`, `createItemWithFileViaForm`,
>   `updateItemWithFileViaForm`, `createDefaultCategoryItemViaForm`, `createStampedItemViaForm`,
>   `submitContact`, `submitPing` — re-derived twice (8 classes, 8 `DjangoMutationField` rows), so
>   no recount is owed. Recommended action: widen the fence by this one file and re-pin the three
>   sentences; measured at three sentences in one file, no generator, no gate. `TODAY.md` is
>   byte-identical to `HEAD` (42,568 bytes, `cmp` clean) — nothing was pre-emptively touched.
>   No licensing spec clause: this is cycle-caused drift, not a spec deferral.

**2. The five working-tree-only hunks, adopted into the spec nowhere.** Owner: **the
concurrent session that authored them**, whose own cycle commits them; no `038` worker
action. Re-derived this pass, not accepted: each is absent from the `HEAD` copies and
present in the working tree (`grep -c` → 0 at `HEAD` vs 1 / 2 / 2 now;
`forms/inputs.py` 757 lines at `HEAD` vs 799).

- `forms/inputs.py` — the `str.isidentifier` / `keyword.iskeyword` field-name guard; the
  guarded `dict(form_class.base_fields)` read; the two out-of-vocabulary `operation_kind`
  raises in `build_form_input_class` / `build_form_inputs`.
- `forms/sets.py` — the typed `BaseException` wrap around the `get_form_fields` hook
  invocation in `_mutation_form_fields`.
- `forms/resolvers.py` — the multi-relation container check lifted to
  `utils/write_values.py::materialize_relation_id_container`.

Recorded in the companion's `## Non-Decision deliberation` as well, so a reader of the
spec's silence does not conclude they do not exist. **They are also why two of
`forms/inputs.py`'s four shadow repeated literals and one of `forms/resolvers.py`'s
imports are not part of any shipped contract** (precondition 2).

**3. Two `forms/inputs.py` guards the spec is deliberately silent about.**
`_guard_input_attr_collisions` (two form fields colliding on a generated input attr or
camelCased GraphQL name) and `_model_less_relation_annotation`'s reject for a
plain-`Form` relation field whose `queryset` is `None` at class definition. Both present
at `HEAD`, both graded as landed contracts by Slice 1 (its D-14 / D-15), both judged too
narrow by Slice 2 to promote into a numbered Decision, and both recorded in the companion
under Decision 7 rather than dropped. Owner: **the next spec author**, to decide whether
either earns a Decision. No worker action owed this cycle.

**4. `docs/SPECS/NEXT.md` is modified in the working tree and was touched by no pass of
this cycle.** Not on any worker's writable list, so per `AGENTS.md` rule 34 it is a
stop-and-report rather than a revert. Reported by Slice 2 and re-confirmed here: still
` M docs/SPECS/NEXT.md`. Its diff is a concurrent session's.

**5. The four full-sweep failures stay with Worker 0.** The concurrent session's
uncommitted `sets_mixins.py` edit (`ActiveInputPermissionAttrs.__init__() got an
unexpected keyword argument 'unset_sentinel'`), not worker-verifiable at `HEAD`, not this
build's work, and explicitly not a deferred-work-catalog item. No `pytest` sweep was run
this pass.

**6. NEW — 11 package-source citations of `spec-038 Decision N P<N>` now point at a
vocabulary the spec no longer contains.** Owner: **Worker 0**, to dispatch a builder
under a widened writable surface, or **the maintainer**. Cause: Slice 2's 62-occurrence
label sweep (its walk item 29), which was correct for the spec and had a parallel site
nobody swept. The 11 are enumerated verbatim under `## The partial-claim-fix sweep`
above, in `forms/converter.py` (2), `forms/inputs.py` (5), `forms/sets.py` (3) and
`mutations/sets.py` (1). The wider vocabulary population in the `038` subsystem is **33**
occurrences across 7 files, 22 of them package `.py`; the four `tests/forms/` modules
carry zero. All 33 are present at `HEAD`, so none is the concurrent session's. The
`spec-038 Decision 7` half of each citation is a spec decision pointer and stays under
`START.md` "Style Rio cares about"; only the trailing orphaned label is the defect.
**Ungated** — `scripts/check_citations.py` is `path::Symbol`-only. Not fixable inside this
pass's writable surface (package `.py`).

**7. NEW — `docs/SPECS/spec-036-mutations-0_0_11.md` and its companion still name three
shipped cards by their pre-ship `TODO-ALPHA-` ids.** Owner: **the next spec author**, or
whoever next reconciles `spec-036`. `spec-036-mutations-0_0_11.md` #"reused unchanged by"
names `TODO-ALPHA-039-0.0.13` and `TODO-ALPHA-038-0.0.12`; the companion's
`## Non-Decision deliberation` names `TODO-ALPHA-037` / `-038` / `-039`. All are
`DONE-` cards now. This is the same class Slice 2 retired inside `spec-038` (its items
15-17) — a parallel site in a sibling archived spec, outside this cycle's writable
surface. It is also the pair Worker 0's pre-flight anchor claim did not name.

**8. NEW — `products/schema.py`'s `Mutation` docstring names seven of the eight form
mutations, omitting `submitPing`.** Owner: **Worker 0**, to fold into a builder pass, or
the maintainer. Pre-existing (five of six at `HEAD`) and carried forward by this cycle's
widening of the paragraph, while the adjacent `test_products_api.py` section comment
names all eight and states the count it must keep. One file, one clause; no generator
reads the paragraph (only the module docstring's **first** line feeds `docs/TREE.md`, and
that line is byte-identical to `HEAD`).

---

### Escalations

**`tests/rest_framework/test_sets.py` does not parse in the working tree, and it blocks
two of the final gate's commands.** Not this cycle's, and not mine to touch.

- `uv run ruff check .` → exit 1, **325 errors, all 325 in that one file**, beginning
  `tests/rest_framework/test_sets.py:1622:7: invalid-syntax`.
  `uv run ruff format --check .` → exit 2, same cause.
- Attributed, not assumed: `git show HEAD:tests/rest_framework/test_sets.py` **parses
  cleanly** (`ast.parse` OK); the working-tree copy raises
  `SyntaxError: unterminated string literal (detected at line 1848)`. The file is
  baseline-dirty (` M`) and in no pass of this cycle's writable set.
- This is the same shape Slice 1's first full sweep hit on
  `tests/utils/test_inputs.py` — a half-written docstring in a file the concurrent
  session then fixed itself. It will also produce a **collection error** in
  `uv run pytest --no-cov`, and `START.md` warns that one broken module drops rows across
  every file its tests build schemas through, so a sweep run while it is broken is not a
  valid sweep.
- Nothing was reverted, fixed or worked around (`AGENTS.md` rule 34, and the plan's fence).
  **Worker 0 should confirm the file parses before the final gate runs its full sweep and
  its whole-tree `ruff` commands**, or record the exception in the plan's preamble.

Scoped to the five files this cycle wrote, both commands are clean: `ruff check` →
`All checks passed!`, `ruff format --check` → `5 files already formatted`.

**The baseline-dirty population has grown into surfaces the scope fence names, and no
worker touched any of them.** `git status --short docs/` at the end of this pass reports
`docs/GLOSSARY.md`, `docs/README.md` and `docs/TREE.md` modified, plus untracked
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/feedback2.md` and four `docs/spec-037-*`
files — none of which any `038` pass wrote, and three of which the plan's `## Scope
fence` puts out of every worker's reach. The plan says in terms that the dirty population
grows while the cycle runs and that the fence covers whatever the concurrent session owns
at the moment a worker reads it. Recorded rather than reverted (`AGENTS.md` rule 34).
**Consequence for the final gate:** `docs/GLOSSARY.md` and `docs/TREE.md` are rendered
from source, and CI's `lint` job runs `--check` on every generator, so the gate should
expect those `--check` runs to reflect a concurrent session's in-flight state rather than
this cycle's output — and `START.md`'s rule applies (a `--check` in a dirty tree measures
the working tree, not `HEAD`).

---

### Failability proofs

`None; this pass introduced no new boundary.` No guard, gate, cap or rejection path was
added — this pass's whole diff is Markdown. The three boundaries the cycle newly pinned
were proved by Slice 1's build pass at **3 / 3 / 2** failing rows, none weakly pinned,
zero collection errors, each revert byte-compared, and each independently re-run by
Worker 3 with zero node-id set difference; Slice 1's final verification confirmed the
records exist with every field `### What gets recorded` requires and that **no zero-row
entry exists anywhere in the chain**, so no `why 0` slot is owed.

### Hot-path budget

`Not applicable; plan declares no hot path.` Re-confirmed against the cycle as a whole:
no package `.py` is in any pass's diff, so no per-request, per-resolver, per-row,
per-connection or per-outbound-message cost can have been added. The two costs that do
exist are neither package cost nor per-request — the two new example-app
`DjangoMutationField`s cost one construction each **at schema build**, and
`CreateDefaultCategoryItemViaForm.get_form_kwargs` issues one
`Category.objects.order_by("pk").first()` read per call **of that one example-app
mutation**, inside the pipeline's read phase before `pipeline_write_phase()` opens.

### Floor verification

`Not applicable; the cycle's floor obligation was discharged and verified in Slice 1.`
Declared there as GAP-2 and GAP-3 in scope, owned by that slice's Worker 2 build pass,
re-executed by Worker 3 and again by Slice 1's final verification — each time at
`/tmp/dsf-floor` outside the working tree, reading django 5.2.16 / strawberry-graphql
0.316.0 / Python 3.10.19, which is exactly the floor
[`docs/builder/BUILD.md`][build-md] `## Floor verification` states. The shared `.venv` was
read as the newest supported set and never mutated, by that chain or by this pass.

### DRY check across this pass and prior accepted slices

No new duplication, no repeated literal and no inconsistent helper shape was introduced
by this pass — it wrote no code and no helper. Across the cycle: the full-population
cross-file literal comparison (11 candidates, all declarative vocabulary), the ten-way
import-direction comparison (one-way, one licensed function-local back-edge), and the
walk of both reviews' `DRY findings` all come back clean, and the one ownership
misplacement the cycle carried was in the spec's prose rather than in code and is
repaired above.

### Summary

The integration pass ran the six mandatory preconditions and found **two divergences,
both inside this pass's own writable surface and both repaired**, plus **three new
deferred items** for the final gate.

The preconditions came back: all three prior artifacts read in slice order; shadow output
present for all ten Python files with review-worthy logic and **zero** unrecorded skips;
the cross-file literal comparison **re-derived** because two shadow sections are truncated
at 25 entries and comparing them as emitted hides 103 of 174 literals — the re-derivation
surfaces 11 cross-file candidates rather than 10, the extra being `attachment`, this
cycle's own; imports one-way with exactly one deliberate function-local back-edge that
breaks the `forms/` ↔ `mutations/` load cycle; every `What looks solid` and `DRY findings`
item walked with nothing owed here; and **zero** `038` staged anchors in source, tests,
examples or scripts over a printed population of 456 files / 11.5 MB with a live control
firing 30 times locally and 1,075 times repo-wide.

The divergence inventory cross-checked 26 contract classes against all five homes with a
retired-spelling and a shipped-spelling matrix, then read the six highest-risk contracts
home by home. Nine raw residue cells resolved to **one real disagreement in three homes**:
the reverse-map record's ownership, which Slice 2 corrected in Decision 7 and the Slice-1
checklist while `## Definition of done` item 2 and the `## Implementation plan` Slice-1
cell went on attributing it to `forms/converter.py` — under a `forms/converter.py`
subject, so they contradicted the corrected Decision rather than merely lagging it — and
the `## Test plan` `test_converter.py` row kept the retired tuple spelling. That is the
partial-claim signature Slice 2's own carry-forward names: the routed item said "both
homes"; the population was five. The second divergence is inside one Decision: its
preamble cited the shared runner's docstring ordinal ("states it as **step 3**") three
lines above its own renumbered list where step 3 is the Decode — the exact
cite-by-content-never-by-ordinal rule the routed item had commissioned, applied to the old
text and not to the replacement. Both repaired; the remaining twenty apparent residues are
graded individually as instrument false positives, `## Current state` observations, the
genuinely-frozen `node` / `result` slot, or pre-`038`-state descriptions, each recorded so
silence is not read as absence.

The derived-description spot-check held at **16 of 16** Slice-1 claims and **34 of 34**
Slice-2 claims against live source; both apparent failures were my own instruments. Two
figures have rotted — the `tests/` + `examples/fakeshop/` byte total, twice — and the
durable halves re-derive exactly. The partial-claim sweep proves retirement at **0** for
all seven classes of fix in the spec, with every companion hit checked as a
record-of-removal rather than a live claim; it also found the one thing the spec sweep
created rather than closed: **11 package-source citations of `spec-038 Decision N P<N>`
now point at a spec carrying zero P-labels**, ungated because `check_citations.py` is
`::Symbol`-only, and outside this pass's writable surface.

Comment and docstring coherence across the ten new node ids and the two example-app
surfaces is clean: **0** banned-provenance tokens across all **851** lines the cycle added,
six pattern classes swept, and the two new schema docstrings each cross-reference a
sibling so the pair reads as one story. Every gate this pass could run is green; the two
whole-tree `ruff` commands fail on a single baseline-dirty file that does not parse in the
working tree and parses cleanly at `HEAD`, escalated to Worker 0 because it will also
break the final gate's full sweep.

### Final status

`final-accepted`

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

[build-md]: BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
