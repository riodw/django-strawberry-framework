# Build: R2 — spec reconciliation, plus the Worker 1 final verification of the four R1 cohorts

Spec reference: `docs/SPECS/spec-036-mutations-0_0_11.md` (whole file) and its rationale companion
`docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md` (whole file) — both owned by this pass.
Status: final-accepted

This is a combined pass, the same shape the precedent cycle's R2 took: (1) reconcile the spec against
`HEAD` from the four R1 cohorts' on-disk `### Notes for Worker 1 (spec reconciliation)` sections, and
(2) perform the Worker 1 final verification the four `review-accepted` R1 artifacts are waiting on.
No `.py` source or test file was read-write in this pass; R3 owns the code side and is running
concurrently under the declared partition.

---

## Plan + reconciliation report (Worker 1)

### Files written this pass — the complete list

- `docs/SPECS/spec-036-mutations-0_0_11.md`
- `docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md`
- `docs/builder/bld-036-review-2-spec_reconciliation.md` (this file)
- the `Status:` line plus an appended `## Final verification (Worker 1)` section on each of
  `docs/builder/bld-036-review-1a-inputs_envelope_payload.md`,
  `bld-036-review-1b-base_meta_finalizer.md`, `bld-036-review-1c-resolvers_fields_writeauth.md`,
  `bld-036-review-1d-live_surface_g2_exports.md`
- `docs/builder/worker-memory/worker-1-036.md`

Nothing else. `git status --short` over `tests/`, `examples/`, and `django_strawberry_framework/`
shows only the concurrent session's and R3's work; this pass wrote none of it.

### The split question, answered in writing

**Not split.** The reconciliation was one pass, deliberately, and the precedent cycle's reasoning
holds here with more force rather than less. The headline divergence is **one contract restated at
many sites across several sections**: the `DjangoSchema` requirement spans 6 pre-existing sites in
three cohorts' spec territories, the transaction boundary 3, the M2M visibility clause 4, the
`FieldError` shape 7.
A section-wise split would hand each half a spec in which the other half's sites still contradict it —
precisely the half-reconciled state `docs/builder/worker-1.md` `## Review-round custody` forbids, and
the one failure mode that cannot be reviewed out afterwards, because the reader cannot tell which half
is current. Finding 1 alone is the proof: no single cohort's notes list all six of its sites, so only a
whole-spec pass can close it. The cost is a large single diff — measured, `diff -u` against the
pre-pass copies: **+71 / -38** lines in the spec and **+48 / -4** in the companion — which is a review
cost, not a correctness one.

### Method

- **The spec and the companion are read and written live**; they are this cycle's own uncommitted
  output (Slice 0 created the companion hours ago). Grading them against `HEAD` would route edits to
  line ranges that no longer exist.
- **Every `HEAD` fact was taken from the four R1 artifacts' evidence cells**, which cite the read-only
  snapshot at `7426e7e7d8aa447e89fee75088447d6a506dec12`, plus `git show <commit>:<path>` reads of my
  own where an attribution had to be established (below). No `git stash` / `git checkout` /
  `git restore` / `git worktree` anywhere in this pass.
- **Every edit was applied by an exact-string replacement asserting the match count is 1** before
  writing, so no edit landed at an unintended site and no intended site was silently missed: **62**
  spec replacements and **15** companion replacements, each verified at apply time, plus the Decision-2
  heading rename, applied separately as an asserted-count rewrite of 1 heading-text + 2 slug uses in the
  spec and 2 heading-text + 3 slug uses in the companion.
- **Attribution was checked against the original implementing commit, not only against `HEAD`**, for
  every claim I attributed. `git log -S<symbol>` was used only to *locate* candidates, never to rest a
  negative conclusion on.

### Attribution work, and the five cases where the obvious framing would have been wrong

Recorded here because this is where the pass was most likely to go wrong, and one cohort did.

1. **`FieldError`'s `codes` / `path` — attributed to `DONE-039-0.0.13`, not to the `0.0.14`
   hardening.** R1a and R1d gave conflicting attributions for the same commit. Re-derived:
   `git log -S'codes: list[str] = strawberry.field' -- django_strawberry_framework/mutations/inputs.py`
   returns exactly `951945b7` (2026-07-01); `git show 951945b7:django_strawberry_framework/__init__.py`
   has `__version__ = "0.0.12"`; and `git show 951945b7 --stat` carries
   `docs/spec-039-serializer_mutations-0_0_13.md`. So the owner is the DRF-serializer flavor card, two
   months before `0.0.14`. **R1a is right, R1d's evidence cell is wrong**, and the companion records
   the correction so a later reader does not inherit it.
2. **Decision 8 step 5's `IntegrityError` mapping — wrong when written, not superseded.**
   `git show 4b26b94e:django_strawberry_framework/mutations/resolvers.py` shows
   `_integrity_error_field_errors` keying the `"__all__"` sentinel and carrying
   `del model, provided_attrs  # reserved for a future per-constraint refinement.` in the card's **own**
   shipping commit. The spec sentence ("maps it to the constraint's fields") never described the code.
   A `**Post-ship:**` bullet would have invented a change that never happened; it is recorded as a
   wrong-when-written correction under Decision 8 instead. Same treatment for the `## Edge cases`
   create bullet, which repeated it.
3. **Three rows changed *inside* the `0.0.11` cut, at `c09793ee` (2026-06-18, `__version__` still
   `0.0.10`, before the 2026-06-19 release).** The create-side `full_clean(exclude=...)` parity, the
   explicit-`null` decode rejection, and the coroutine-close half of the authorization-result contract
   are review-round work of this card, not post-ship supersession. They are recorded under
   `### Changes this Decision underwent` as `**Corrected inside the `0.0.11` cut (`c09793ee`,
   pre-release):**` bullets and are deliberately **not** counted in the `**Post-ship:**` census.
4. **The explicit-`null` row needed both framings.** The spec's stated mechanism (`full_clean()`
   catches it) was a fail-open that was never true — at `4b26b94e` such a value slipped past
   `clean_fields` (which skips a `blank=True` field whose value is empty) and failed at `save()` as an
   unattributed `"__all__"` NOT NULL error — and `c09793ee` then made a *different* thing true. Framing
   it as post-ship only would have preserved the false premise, so the companion bullet says both.
5. **Decision 11's `primary_for` citation — wrong when written.**
   `git show 4b26b94e:django_strawberry_framework/mutations/sets.py` already resolved the primary type
   with `registry.get(model)` plus `registry.types_for(model)` for the error split, and has never
   called `primary_for`. Recorded as a wrong-when-written correction, not a rename.
6. **`DONE-037-0.0.11` is the sibling card of the same joint cut**, and its upload mapping landed at
   `66d01b4a` on 2026-06-19 — the day of the `0.0.11` release, after `036`'s own slices closed
   (`4b26b94e`, 2026-06-18). It is recorded as post-ship with that timing stated, rather than as
   in-cut work, because `036` was finished when it landed.
7. **`Item.attachment`** is `731fecd8` (2026-06-23), `DONE-038-0.0.12`. **The M2M / relation visibility
   check** is `DONE-038-0.0.12` too, per `CHANGELOG.md` `## [0.0.12]` #"closing the raw-pk visibility
   gap"; R1c's day-one check confirmed `4b26b94e`'s `_assign_m2m` used the default manager, so the spec
   was right at ship. **`select_for_update`** entered at `951945b7` as a serializer-flavor key and was
   promoted to every model-backed flavor at `1b06c39e` (BETA-055, 2026-07-15).
8. **Where attribution could not be established, the companion says so.** The `DjangoSchema`
   requirement, the completion-spanning transaction, the alias pinning, and the `conflict` envelope
   have **no owning card in any commit message** — their only durable record is
   `CHANGELOG.md` `## [0.0.14]` and `docs/README.md`. The companion names the `0.0.14` cut and that
   record rather than guessing a card number.

### The four High findings, each closed at every site

Sites were established by grep, not by the cohorts' prose, and re-counted after the edits.

**1. The spec instructed a construction that fails loudly.** Before: `DjangoSchema` → 0 occurrences,
`strawberry.Schema` → 6. After: `DjangoSchema` → 6 occurrences, `strawberry.Schema` → 4, and each of
the 4 is now a **negative** statement (what the pipeline refuses), verified individually:

| line | disposition |
|---|---|
| Slice 4 sub-bullet | rewritten to `DjangoSchema(...)`, "never a plain `strawberry.Schema`" |
| `### Error shapes` | **new bullet** — a generated mutation under a plain `strawberry.Schema` raises `ConfigurationError` before any database work |
| Decision 8 | **new paragraph** stating the same, naming `DjangoSchema` as the fix |
| DoD item 4 | rewritten, same clause |
| Key glossary references (`finalize_django_types`) | was a *materialization-ordering* claim and stays true — reworded to "before the schema is constructed" so the class name carries no false implication |
| Slice 2 sub-bullet | same, same treatment |
| `## Current state` set-family bullet | same (it describes `filters/` / `orders/`, not the write surface) |
| `## Current state` products-write-target bullet | rewritten — the falsified prediction now names `DjangoSchema` |
| Decision 12 | same — R1c flagged this site explicitly as one R2 must **not** over-rewrite |

All **6** pre-existing `strawberry.Schema` occurrences were addressed, and **3** sites gained a new
`DjangoSchema` statement (the `### Error shapes` bullet, Decision 8's paragraph, DoD item 4). Three of
the nine rows above sit in R1b's or R1d's spec territory, which is why no cohort's notes listed them
all and why the pass was not split.

**2. Decision 8's transaction boundary.** All three sites (Slice 3 sub-bullet, Decision 8's
`**Transaction and async boundary (AR-M4)**` paragraph, DoD item 4) now state the extent
(`locate → snapshot`, the locate inside because it takes the row lock), the owner (nested inside the
completion-spanning transaction the schema's execution context opens for the mutation field), and the
failure surface (a response-completion failure rolls back; every error-envelope return marks the
transaction for rollback before building the payload). The `## Edge cases` async bullet's stale
`(steps 3–6)` extent was corrected in the same pass — a fourth site neither cohort listed.

**3. Decision 8 step 5's M2M contradiction, resolved in favour of what ships.** All four sites
(Decision 8 step 5, DoD item 4, the `## Edge cases` many-to-many bullet, the `## Test plan`
`test_resolvers.py` bullet) now say the related model's primary type's visibility `get_queryset`
confirms the whole set in one `pk__in` query, with the default manager only as the no-registered-primary
fallback. The spec previously asserted this **and** its negation (`## User-facing API` #"a permitted
writer can never attach a row they could not see"); the safe contract is now the only one stated.

**4. `FieldError`'s freeze claim.** The **sharing** is stated positively at every site (exactly one
class, every flavor imports it) and the **freeze** is replaced by the rule that actually holds: the
type may grow only additive, default-empty fields and may never change or remove one. Five sites
carried the shape (preamble, Key glossary references, Slice 1, Decision 5, Decision 7, the SDL block,
DoD item 2 — seven in total), and the SDL block now carries `codes: [String!]!` / `path: [String!]!`
with Decision 7 stating the root-vs-nested `path` rule. Two sites carried the freeze language
(Decision 2's final paragraph, the preamble) plus the parity table's status cell.

**Decision 2's heading was renamed**, from "…the `FieldError` envelope is **frozen** here" to
"…**defined** here", because a heading is a claim and that one was false. The rename was safe and was
proved so before it was made: the exact slug has **5** uses corpus-wide, all inside the two files this
pass owns (2 in the spec, 3 in the companion), and every one was rewritten in the same edit —
`grep -rlo` over `docs/` confirms no sibling spec cites `spec-036`'s Decision-2 slug (the 71 other hits
are other specs' own Decision-2 slugs, different strings). This is the trap Slice 0 hit from the other
side, where a broken Decision-8 slug had 16 dead uses.

### Routable-row ledger: 66 rows in, 56 discharged, 10 deferred

The 66 routable rows are R1's 34 SUPERSEDED + 26 STALE-DESCRIPTION + 6 RENAMED, re-derived below
under `## Final verification (Worker 1)` rather than taken from the plan.

**R1a — 15 routable, 15 discharged.**

| rows | contract | disposition |
|---|---|---|
| 15 / 33 / 49 / 78 | the `FieldError` shape | discharged, 4 sites + 3 more the rows did not list |
| 31 / 32 / 81 | the file/image `NotImplementedError` carve-out | discharged — Decision 6's CR-6 paragraph now states the `Upload` scalar mapping and the shared override skip; the `## Implementation plan` parenthetical is retired |
| 21 | Slice 1's coverage bullet names the wrong file for AR-M2 | discharged — the clause points at `tests/mutations/test_sets.py` |
| 41 | Decision 7's `.field()` fallback (falsified prediction) | discharged — sentence and its dead Risks pointer deleted, contingency kept in the companion |
| 47 / 48 | the `ItemInput` / `ItemPartialInput` SDL blocks omit `attachment` | discharged — both blocks and the prose required/optional list |
| 65 | explicit `null` "caught by `full_clean()`" | discharged — states the decode rejection and why `full_clean()` cannot be the gate |
| 83 / 84 / 85 | the three RENAMED mechanism families | discharged — Decision 4 names `utils/inputs.py` as the shared-mechanics owner, Decision 7 names `utils/errors.py` as the envelope-constructor owner, Decision 8 step 1 names `utils/write_values.py` as the decode owner |

Plus R1a's **N10** (relation overrides are type-locked, not only name-locked) — an *addition* rather
than a divergence, and I took it: Decision 6's AR-M2 paragraph now states both axes, because R1a's own
row 54 grades the no-attach-what-you-cannot-see promise CONFORMS and at `HEAD` that promise rests
partly on this validator. **N6** (should `FieldError` live in `mutations/inputs.py` at all?) is
contract-level and stays escalated, unacted.

**R1b — 12 routable, 12 discharged.**

`A5` (the `Meta` key enumeration gains `select_for_update`, named with its `True` default and the
non-bool rejection — the full lock contract is deferred, below); `A9` (the operation vocabulary now
cites `mutations/operations.py`, 2 sites); `C2` + `C3` (Decision 4's module list is five as the card
shipped, with `operations.py` named); `C4` (the `sets_mixins.py` reuse prediction is rewritten to state
where the substrate actually lives); `C6` + `C7` (the test-module enumeration gains
`test_permissions.py`, which **this card shipped**, and names the two later modules); `C8` (the
lookup-scoping pin's two real paths); `E2` (`primary_for` dropped from Decision 11); `G3` (DoD item 3's
registration / bind split); `H3` (the "byte-unchanged" claim re-tensed to what it contracts). `N11`'s
shared-input-types clarity rewrite was taken as well.

`D5` — the public-symbol-count numeral in the companion's **moved** Decision-5 justification — is
discharged **by a stated reading, with no edit**, and R1b's own note reaches the same conclusion
("no spec-side edit is needed"). R1b recommended repairing the numeral in place; I declined. Moved text
stays verbatim, which is the precedent Slice 0 set deliberately, and the disclosure that already sits
one line below it states exactly the right thing: the argument stands, only the count is wrong, and the
Decision body plus DoD item 8 both say four. Repairing inside moved text buys nothing the disclosure
does not already give and costs the property that makes the companion auditable.

One correction to R1b's evidence: **Decision 5's body carries no `Meta`-key enumeration.**
`grep -c 'optional \`input_class\` / \`partial_input_class\` / \`fields\` / \`exclude\` /
\`permission_classes\`'` over the spec → **1**, the Slice 2 sub-bullet. R1b's N1 describes a second
site in Decision 5 that does not exist. The grade is unaffected.

**R1c — 25 routable, 15 discharged, 10 deferred.**

Discharged: `S3.7` / `D8.T1` / `DoD4.a` (the transaction boundary, 3 sites + the async edge case);
`S3.13` / `D8.A` (the `is_async_callable` asymmetry, 2 sites + the `## Test plan`'s "at construction");
`S3.17` (the plan-shape pin's file); `D8.4b` (`exclude` computed for both operations); `D8.5b` /
`DoD4.c` (the M2M default manager, 4 sites); `D10.1` (Decision 10 describes the composition instead of
pasting an expression); `E3` (the explicit-`null` decode rejection); `X1` / `X2` (the `DjangoSchema`
requirement and the completion-spanning transaction); `R1` (this file's own sibling — the companion's
`_validate_save_assign_refetch_payload` citation now points at the live symbols).

Deferred, with the reason on each — **the maintainer's CORRECT CLAIMS ONLY decision is what defers
them**, since their only home would be new descriptive text about machinery `spec-036` never scoped:

| row | contract at `HEAD` | why deferred |
|---|---|---|
| `X3` (partial) | `Meta.select_for_update`'s full lock semantics — base-manager `SELECT … FOR UPDATE` constrained by the visibility pk subquery, `False` as the weaker-concurrency opt-in surfacing the in-band `conflict` envelope, silent no-op on a backend without `FOR UPDATE` | the **key** is now named in the spec because the closed enumeration was false; the semantics are `0.0.14` machinery |
| `X4` | one router write alias resolved once and pinned across the operation; a re-routing `get_queryset` hook fails closed | no `036` claim touches it |
| `X5` | the retryable in-band `conflict` `FieldError` on `id` (zero-row forced update, zero-target-row delete, vanished post-write re-fetch) | no `036` claim touches it |
| `X6` | the update's `force_update=True` save in its own savepoint | no `036` claim touches it |
| `X7` | the immutable authorized-pk snapshot + canonical `to_python` pk comparison + pk-drift backstop | no `036` claim touches it |
| `X8` | the pipeline is database-read-only outside the write step, with a transactionally-contained authorization phase as the one exception | no `036` claim touches it |
| `X9` (partial) | the strict-`bool` authorization result across all three seams | the coroutine-close half landed **in-cut** and is recorded under Decision 8; the strict-`bool` half and the `user.has_perm` seam are `0.0.14` |
| `X10` | point-in-time authorization; `Meta.permission_classes = []` as the AllowAny opt-out | no `036` claim touches it |
| `X11` | a `PROTECT` / `RESTRICT` delete refusal returns the envelope rather than leaking model and relation names | no `036` claim touches it |
| `X12` | the cooperative resource-policy deadline checked before the transaction opens | owned by `spec-047`; a pointer would be new descriptive text |

`X13` (the pipeline skeleton and resolver-entry pair as promoted shared machinery four flavors ride) is
**partially discharged**: Decision 4 now states that the write-flavor substrate lives in
`mutations/sets.py` and `utils/inputs.py` rather than in `sets_mixins.py`, and Decisions 7 and 8 name
the `utils/` owners. Its ownership question stays escalated (R1c's **L1** / R1b's **N10**).

R1c's **M4** (the `has_permission` / `check_permission` arity) is verified-and-rejected and I did not
re-raise it: two seams, two deliberate arities, all four sources agreeing.

**R1d — 15 routable, 15 discharged.**

`S4.3` (the schema constructor); `D2.b` (the upload seam consumed); `D2.e` (the envelope freeze);
`OS4` (nested writes split from bulk — nested serializer inputs are the serializer flavor's, bulk stays
out); `OS3` + `D2.d` (the two `TODO-ALPHA` card ids flipped to `DONE-039-0.0.13` / `DONE-040-0.0.13`,
and **only** those two — R1d's coordination warning names three sites that stay verbatim as quotations
of other documents' text, and they were left alone); `S5.5` + DoD item 7 (the README section names that
do not exist → `## Status` and `## Today and coming next`); `DoD1.b` (the terms-CSV rationale);
`DoD5.a`; `CS1.b`, `CS3.b`, `CS7.b`, `CS8`, `CS9`. R1d's **note 11** (`TP.9`, the `## Test plan`'s
`transaction.atomic` tier assignment) was taken in the same pass as the Decision-8 boundary, so the two
now agree.

### The two rows needing a stated reading, and the reading applied

- **Decision 13 / DoD item 8's version boundary — read as a HISTORICAL claim about the card.** The
  package is at `0.0.15`, so the live reading is trivially false, while the claim the card was accepted
  against — that no slice of *this card* edited `pyproject.toml`, `__version__`,
  `tests/base/test_init.py::test_version`, or `uv.lock`, and that it promoted no release heading —
  holds. No spec edit follows; the reading is recorded in the companion under Decision 13 so the next
  reader does not re-grade it. **DoD item 6** (suite green at the coverage gate, `ruff` clean, no
  B1–B8 regression) takes the same reading, and is additionally not worker-verifiable in a tree
  carrying a concurrent session's work with coverage flags forbidden. R1d's option (a).
- **DoD item 5's `Category` scope — reworded to match its own slice checklist.** The DoD demanded
  create/update/delete over "at least `Item` **and** `Category`" while the authorizing checklist
  sub-bullet asked for "at least one `Category` write", which is what shipped. R1d's option 1, its
  recommendation: the DoD now states the contract the build was accepted against. Widening the example
  schema (option 2) was rejected — two mutation classes, two `Mutation` fields, and their live rows for
  a contract nothing else asks for.

### `## Current state`, graded clause by clause

Per `docs/builder/BUILD.md` `### \`## Current state\`: observations stand, predictions do not`, and
R1d graded every clause first.

- **Stood (dated observations, licensed by the section's opening line):** no `mutations/` module / no
  write resolvers / no input generation; the products `Query` being four connections with no `Mutation`
  type; the set-family precedent; the shipped G2 gate; the shipped permission seam; the shipped
  `Meta.primary` resolution. Two of these were re-tensed ("as this spec is authored") so they read as
  the dated observations they are, without changing what they observe.
- **Rewritten:** the sibling-card bullet, which made a live claim about another card's board state
  ("planned, not started") that no vintage licence covers; the products-write-target bullet's
  prediction, which named a plain `strawberry.Schema` constructor; and "plain editable Django models",
  falsified by `Item.attachment`.
- **Quotation dropped rather than re-worded:** the `docs/TREE.md` bullet quoted
  `"planned by TODO-ALPHA-036-0.0.11"`, a string that no longer exists in the file it quotes. Silently
  updating the text inside the quotation marks would have manufactured a quotation; the bullet now says
  TREE reserves the paths for this card, with no quoted string.
- **Spelling corrected:** `DEFERRED_META_KEYS = {...}` → the typed `frozenset(...)` declaration that
  is actually there.

### Spec changes made (Worker 1 only)

62 exact-string replacements, each asserted to match exactly once before writing, across:
the preamble; Key glossary references (2 bullets); the Slice checklist (Slices 1, 2, 3, 4, 5 — 9
sub-bullets); `## Goals` item 3; `## Non-goals`; the parity table; `## User-facing API` (the two input
SDL blocks, the `FieldError` SDL block, the required/optional prose); `### Error shapes` (1 new bullet);
Decisions 2, 4, 5, 6, 7, 8 (steps 1, 4, 5, the transaction paragraph, 1 new paragraph), 10, 11, 12;
`## Implementation plan` (the staged-anchor paragraph); `## Edge cases and constraints` (6 bullets);
`## Test plan` (the ownership split, 2 tier bullets); `## Doc updates`; `## Out of scope` (3 bullets);
`## Definition of done` (items 1, 2, 3, 4, 5, 7); the link-definition block (+4 defs:
`mutations-operations`, `utils-errors`, `utils-inputs`, `utils-write-values`); and Decision 2's heading
with all 5 uses of its slug.

Deliberately **not** changed, each with its reason:

- **The 184 review-finding tags** (`AR-H#` / `Major-#` / `Medium-#` / `CR-#` / `DRY-#` / `Low-1` /
  `P1`–`P2`). Slice 0 recorded them as an open maintainer call; they are lookup keys into the companion
  rather than chronology, and both precedent cycles left the shape standing.
- **`docs/SPECS/spec-036-mutations-0_0_11-terms.csv`** — outside this cycle's maintainer-set scope. The
  stale *argument* for the omission was corrected in DoD item 1; the CSV itself is a maintainer call.
- **Every `TODO-ALPHA-*` id that quotes another document's text** — `## Current state`'s TREE quotation
  (dropped entirely instead), Slice 5's card-wrap instruction (true in its own tense), and Decision 2's
  parenthetical quoting the card DoD. R1d's coordination warning, honoured; a board card already owns
  that class corpus-wide.
- **`## Risks and open questions`'s moved body** — it is moved text in the companion and stays
  verbatim; the one falsified premise it carries is corrected where it also appeared as a live DoD
  claim, and recorded in the companion.

### Rationale companion changes made (Worker 1 only)

15 replacements: `**Post-ship:**` bullets appended to nine Decisions' `### Changes this Decision
underwent` sections; 6 `**Wrong when written:**`, 2 `**Falsified prediction:**`, 2 `**Corrected inside
the `0.0.11` cut:**` and 1 `**Reading applied at reconciliation:**` bullet; 8 new bullets under
`## Non-Decision deliberation`; the Decision-2 Revision-1 bullet's "Nothing later reopened it" struck
(R1a's **N11** — a sentence that would otherwise keep certifying the opposite of the record beneath it);
the `## Risks and open questions` preamble's flagged CSV premise moved from *flagged* to *resolved*; and
one new link def (`spec-036-user-facing-api`).

### `**Post-ship:**` census — measured, not asserted

Re-derived by enumerating every indent-0 `- **Post-ship` line against its enclosing `##` heading, after
the file was written:

```shell
# every indent-0 '- **Post-ship' line, keyed to the nearest preceding '## ' heading
```

**21 bullets under 9 Decisions, plus 0 under `## Non-Decision deliberation`.** By Decision: 2 → 3,
4 → 2, 5 → 3, 6 → 3, 7 → 2, 8 → 5, 10 → 1, 12 → 1, 15 → 1. Decisions 1, 3, 9, 11, 13, 14 take none.
The precedent cycle's first count of this was wrong because it counted sections rather than Decisions;
this one keys each line to its enclosing `##` heading and prints the per-Decision breakdown, so the
number is re-derivable rather than asserted.

The 11 non-`Post-ship` correction bullets are counted separately **on purpose** — folding them in would
misattribute five of them. `**Wrong when written:**` → 6 (Decision 4 ×2, Decision 8 ×2, Decision 11,
Decision 12); `**Falsified prediction:**` → 2 (Decisions 7, 8); `**Corrected inside the `0.0.11` cut:**`
→ 2 (Decision 8 ×2); `**Reading applied at reconciliation:**` → 1 (Decision 13).

### Verification run

Every command as run, with its output.

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-036-mutations-0_0_11.md
OK: 38 terms - all have glossary entries and at least one spec link.
exit=0
```

The term population is **unchanged at 38**. Nothing this pass added is a CSV-listed term: the CSV is
the checker's source of truth, and the four symbols this pass newly names in prose (`DjangoSchema`,
`select_for_update`, `codes`, `path`) are not in it. `DjangoSchema` in particular has **no**
`docs/GLOSSARY.md` heading at `HEAD`, which is a deferred item below, not a gate failure — the checker
validates the CSV's terms, not every symbol a spec mentions.

```shell
$ uv run python scripts/check_citations.py            # --help read first: only --check, always read-only
OK: 933 citations resolve (776 in 435 .py files, 157 in KANBAN.md).
exit=0
```

929 before this cycle, 933 now. **The delta is not this pass's**: `docs/` is explicitly out of that
gate's scope ("`docs/` is deliberately out of scope. The spec archive is a historical record reconciled
per-card during a residual cycle"), so no spec edit can move the count. The +4 is the concurrent
session's and R3's `.py` work.

```shell
$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-036-mutations-0_0_11.md \
    docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md
exit=0
```

All 10 canonical group headers present in `START.md`'s exact order on both files, verified
independently of the gate by listing them:
`<!-- Root -->`, `<!-- docs/ -->`, `<!-- docs/SPECS/ -->`, `<!-- docs/builder/ -->`,
`<!-- django_strawberry_framework/ -->`, `<!-- tests/ -->`, `<!-- examples/ -->`, `<!-- scripts/ -->`,
`<!-- .venv/ -->`, `<!-- External -->`.

**Reference-vs-definition parity and in-page anchors** (body scanned outside fenced blocks; headings
slugged the GitHub way):

| file | defs | ref uses | uses with no def | defs never used | in-page anchor uses | unresolved |
|---|---|---|---|---|---|---|
| spec | 102 | 101 | 0 | 1 (`backlog`) | 22 | **0** |
| companion | 51 | 52 | 1 (`0-9`) | 0 | 19 | **0** |

Both leftovers are **pre-existing and benign, and were re-measured on the pre-pass copies to prove
it**: `[backlog]` was already an unused def before this pass, and the companion's `0-9` is my checker
matching `][0-9]` inside the inline code span `grep -on 'Revision [0-9]'`, not a link. Slice 0 repaired
a Decision-8 slug that had 16 dead uses at `HEAD`, so this was re-verified after the edits rather than
assumed — including after the Decision-2 heading rename.

**Cross-file `#anchor` link defs, resolved against the target file's real headings:** spec 54/54,
companion 34/34, 0 dead, 0 missing files. **Every link path disk-exists-checked:** spec 100 on-disk
paths + 2 URLs, companion 51 on-disk paths, 0 missing. The four new `django_strawberry_framework/`
defs were checked individually (`mutations/operations.py`, `utils/errors.py`, `utils/inputs.py`,
`utils/write_values.py` — all present).

**Chronology sweep on the spec** — the six banned tokens, occurrences not matching lines:

| token | count |
|---|---|
| `Post-ship` | 0 |
| `Revision ` | 0 |
| `as of review` | 0 |
| `later changed` | 0 |
| `superseded` | 0 |
| `amendment` | 0 |

A wider sweep for chronology vocabulary the six tokens miss also returns 0: `no longer`, `has since` /
`have since`, `previously`, `used to`, `formerly`, `earlier draft`, `first draft`, `post-ship`,
`review round`, `retract`. That second sweep caught two sites this pass had itself introduced — "later
cards have since added keys" in the `## Edge cases` `Meta`-key bullet, and "the `0.0.13` serializer
flavor added `codes` and `path` that way" in Decision 2 — both rewritten to state the current rule with
no history. The narrow six-token sweep was blind to both, which is the finding worth carrying: a
reconciliation pass can reintroduce chronology in its own corrections and pass its own gate.

**Byte and line counts:**

| file | before | after | delta |
|---|---|---|---|
| `docs/SPECS/spec-036-mutations-0_0_11.md` | 131,777 B / 623 lines | 142,574 B / 638 lines | **+10,797 B / +15 lines** |
| `docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md` | 74,895 B / 428 lines | 102,637 B / 480 lines | **+27,742 B / +52 lines** |

The corpus ratchet (`docs/builder/BUILD.md` `## The corpus ratchet`) does not apply: it binds
`BUILD.md`, `ARTIFACT.md`, and the four `worker-*.md` role files, none of which this cycle edits.

### Notes for Worker 1 (spec reconciliation) — deferred work, routed

The next reader's list. Nothing here was acted on in this pass.

1. **The `0.0.14` write hardening needs an owning spec, and `spec-036` is not it.** Nine specs carry
   the `0_0_14` segment and none scopes the completion-spanning transaction, the `DjangoSchema`
   requirement, `Meta.select_for_update`'s lock semantics, single-write-alias pinning, the retryable
   `conflict` envelope, the immutable authorized-pk snapshot, the phased alias guard, the strict-`bool`
   authorization contract, or the point-in-time authorization rule. Its only durable record is
   `CHANGELOG.md` `## [0.0.14]` and `docs/README.md`. Per the maintainer's **CORRECT CLAIMS ONLY**
   decision this pass corrected every false `036` claim that touches the surface and authored no
   description of it; the 10 deferred rows above are the inventory a future spec author starts from. A
   future author should treat `spec-036`'s corrected Decisions 8, 10, and 15 as the boundary of what
   `036` claims, not as that spec's outline.
2. **Two contract-level ownership escalations stand, unacted.** Whether `FieldError` /
   `NON_FIELD_ERROR_KEY` should live in `mutations/inputs.py` while the flavor-neutral `utils/` layer
   depends upward on it through two function-local imports (R1a **N6**, three resolution paths
   recorded); and whether `mutations/sets.py` should own the cross-flavor write substrate — 25 symbols
   imported out, 4 private-by-name, 6 with zero caller inside `mutations/` (R1b **N10** / R1c **L1**,
   three resolution paths recorded). Both are maintainer calls. This pass's Decision-4 edit deliberately
   states **where the substrate is** rather than where it should be, so the spec no longer predicts
   option 2 while the code does option 1.
3. **Out-of-scope doc surfaces carrying the retired claims.** `docs/GLOSSARY.md` has no `DjangoSchema`
   entry and no mention of `FieldError.codes` / `.path`; `CHANGELOG.md` `## [0.0.12]` still calls the
   envelope "byte-identical"; `spec-036-mutations-0_0_11-terms.csv` omits `DjangoMutationField` and
   `DjangoModelPermission` although both have glossary headings. All three are outside this cycle's
   maintainer-set scope. The `CHANGELOG` line is the most misleading of the three, since it is a
   released note asserting exactly what this pass retired.
4. **A code-side defect this pass found and did not fix**, outside R3's declared file list:
   `django_strawberry_framework/mutations/inputs.py::FieldError`'s own docstring still says "Defined and
   frozen here (spec-036 Decision 7) so the form-based (0.0.12) and DRF-serializer / auth (0.0.13)
   flavor cards reuse the byte-identical type" — three lines above the two additive fields it then
   documents. The spec no longer says that; the docstring does. It is a `.py` file the concurrent
   session is not editing, but it is not in R3's partition, so it needs a dispatch of its own.
   Companion defect from R1c's **N8**: `mutations/resolvers.py::_full_clean_or_field_errors`'s docstring
   still says `exclude=None` for create, which its only caller contradicts.
5. **The Decision-8 anchor defect is live in two sibling specs** — `spec-038` (36 uses) and `spec-039`
   (34 uses) carry the same `optimizer-refetch` slug Slice 0 repaired here. Out of scope for this cycle
   (the plan says so), and now doubly worth doing, because this pass demonstrated the repair is cheap
   when the slug's uses are all in files one pass owns and expensive when they are not.
6. **The AR-M7 package mirror asserts the exact plan state from a hand-built selection** rather than
   through `optimizer/extension.py::mutation_payload_child_selections` (R1d's Medium). A test-quality
   finding, not a SKIPPED contract — the spec's stated contract *is* asserted — so it belongs to
   whichever pass next opens `optimizer/`.
7. **`types/finalizer.py::finalize_django_types` is 326 lines / 29 branches** with phase 2.5 as an
   inline statement sequence (R1b DRY-3). Not `036`'s and not this cycle's; a candidate for a future
   finalizer-decomposition spec.

---

## Final verification (Worker 1) — this artifact

- **Spec reconciliation:** 66 routable rows in, **56 discharged, 10 deferred**, each deferral with a
  one-line reason above and every one of the 10 traceable to the maintainer's CORRECT-CLAIMS-ONLY
  decision rather than to an unfinished edit.
- **Chronology:** 0 occurrences of each of the six banned tokens, plus 0 on a ten-token wider sweep
  that caught two sites this pass had introduced itself.
- **Gates:** `check_spec_glossary` `OK: 38 terms` exit 0; `check_citations` `OK: 933 citations resolve`
  exit 0; scaffold check exit 0 on both files with all 10 group headers in order; 0 unresolved in-page
  anchors and full ref/def parity on both files (both leftovers proved pre-existing against the
  pre-pass copies); 54 + 34 cross-file anchors resolve; every link path disk-exists-checked.
- **Census:** 21 `**Post-ship:**` bullets under 9 Decisions, 0 under `## Non-Decision deliberation`,
  plus 11 deliberately-separate correction bullets in four other grammars.
- **Byte deltas:** spec +10,797 B / +15 lines; companion +27,742 B / +52 lines.
- **Ownership partition held:** this pass wrote 2 spec files, 5 artifacts, and 1 memory file. It edited
  no `.py` source or test, and none of R3's six declared test files.
- Final status: `final-accepted`.

### Summary

`spec-036` now states the contract that ships. The four High findings are closed at every site — the
`DjangoSchema` requirement (all 6 pre-existing sites addressed — 2 rewritten to name `DjangoSchema`, 4
reworded because their claim was about materialization ordering rather than the write surface — plus 3
new statements), the transaction boundary's extent / owner / failure surface (3 sites + a fourth no
cohort listed), the M2M visibility contradiction resolved in favour of the safe contract (4 sites), and
the `FieldError` freeze replaced by the additive-only rule that actually holds (7 sites, including the SDL
block a consumer copies and a heading rename proved safe at 5 slug uses first). `## Current state` was
graded clause by clause: dated observations stand, three falsified predictions were rewritten, and one
quotation of text its source no longer contains was dropped rather than silently re-worded. Two rows
took a stated reading rather than a mechanical fix — Decision 13 / DoD 8 as a historical claim about the
card, DoD 5 reworded to match its own slice checklist. The history landed in the companion as 21
`**Post-ship:**` bullets under 9 Decisions, with five changes deliberately **not** framed that way:
two claims that were false the day they shipped, two corrected inside the `0.0.11` cut's own review
rounds, and one falsified prediction. The `0.0.14` write hardening's 10 unhomed contracts are routed as
deferred work needing an owning spec, per the maintainer's decision, and `spec-036` was not expanded to
describe machinery it never scoped.

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
