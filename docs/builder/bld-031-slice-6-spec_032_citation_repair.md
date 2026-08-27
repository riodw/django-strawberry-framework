# Build: Slice 6 — repair the `spec-032` citations the Slice-0 rationale move relocated

Spec reference: `docs/SPECS/spec-032-full_relay-0_0_9.md` (the repaired file; an archived, shipped spec).
Cause: `docs/builder/bld-031-slice-0-rationale_extraction.md` — the MOVE of `spec-031`'s deliberative
layer into `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md`.
Build plan: `docs/builder/build-031-globalid_encoding-0_0_9.md`
(`### Fence amendment (maintainer, post-final-gate)` item 1, which puts `spec-032` in fence).
Status: final-accepted

Closed by **procedural closure** ([`BUILD.md`][build-md] `### Procedural-closure slices`): the change is
confined to one spec file, so this is one Worker 1 pass with a combined Plan + Final-verification block
and `Status: final-accepted` set directly. No Worker 2, no Worker 3.

## Plan (Worker 1)

### The defect class

`spec-032` cites `spec-031` from 16 lines carrying **19 distinct claims**, all through one
reference-style definition, `[spec-031]: spec-031-globalid_encoding-0_0_9.md` — a bare path with no
fragment. Slice 0 MOVED `spec-031`'s `Revision history` block and every Decision's rejected
alternatives into the rationale companion. The link still **resolves** (the file exists and the def
never pointed at a fragment), so every link checker in the repo reports these clean **by
construction**. What broke is the truth of each line's claim about the target's *content*.

### DRY analysis

- **Helper inventory checked.** Not applicable in the package sense — this slice writes no Python. The
  documentation-side equivalent was run instead: `spec-031`'s own working link definitions were read
  (`docs/SPECS/spec-031-globalid_encoding-0_0_9.md:648-665`) so the new `spec-032` definitions reuse
  that file's already-verified anchor strings rather than re-deriving slugs by hand. Shapes searched
  for: `rationale`, `appx/`, `#decision-`, `#revision-history`.
- **Existing patterns reused.** The repoint shape is `spec-031`'s own: a decision's deliberative half
  is cited through a companion-scoped def (`[rationale-d11]` there). `spec-032` namespaces its
  versions `[spec-031-rationale-*]` because the target is a **foreign** spec's companion and a bare
  `[rationale-d11]` in `spec-032` would read as `spec-032`'s own.
- **New helpers justified.** Four link definitions, no more: `[spec-031-rationale-d1]`,
  `[spec-031-rationale-d11]`, `[spec-031-rationale-d3]`, `[spec-031-rationale-revisions]`. A general
  `[spec-031-rationale]` def was **not** added — nothing needed it, and an unused def is an orphan
  defect.
- **Duplication risk avoided.** The naive repair re-words each broken sentence to drop the fact. The
  facts are all still true; only their address changed. Repointing preserves them and avoids
  re-deriving in `spec-032` deliberation that already has a home.

### Dispatched findings checklist

- [x] Re-derive the full population of broken citations independently; do not assume the handed list
      is complete or correct.
- [x] Repair every broken citation, preferring a repoint at the companion over rewording away the fact.
- [x] Add only the link definitions actually used, in the `<!-- docs/SPECS/ -->` group, alphabetically.
- [x] `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-032-full_relay-0_0_9.md`.
- [x] `uv run python scripts/check_citations.py`.
- [x] Hand-rolled link-scaffold check on `spec-032`, avoiding the four known slugger defects.
- [x] Before/after count of broken citations, with the command quoted.
- [x] State which candidate findings were rejected, with proof.

---

## Final verification (Worker 1)

### Re-derived population

The handed list named eight candidate sites and a set of eight "believed fine" ones. I re-derived the
population from scratch: `grep -n 'spec-031' docs/SPECS/spec-032-full_relay-0_0_9.md` gives 16 citing
lines plus the link definition, and `grep -n '031' … | grep -v 'spec-031'` gives the bare-`031`
references the first grep cannot see. Line 9 carries **three** separate claims about `spec-031`
(Decisions 8, 11, 12), so the claim population is **19**, not 16.

Each claim was graded by locating its load-bearing token in `spec-031` and in the companion. The
census script is `citation_census.py` (below); its verdicts:

| Site | Claim token | Lives in | Verdict |
|---|---|---|---|
| `:9` D8 | `resolve-then-enforce` | spec | fine |
| `:9` D11 (testing/relay) | ``ships [`testing/relay.py`]`` | spec | fine |
| `:9` D11 (top-level `relay.py`) | ``A new top-level `relay.py` now.`` | companion | **BROKEN** |
| `:9` D12 | `owned by the **joint cut**` | spec | fine |
| `:13` | `**Revision 7**` | companion | **BROKEN** |
| `:30` | `TODO(spec-031` | spec | fine |
| `:97` | ``NOT a [`DEFERRED_META_KEYS`][base] promotion`` | spec | fine |
| `:127` | ``no shipped path hits native `resolve_type` `` | spec | fine |
| `:143` | ``A new top-level `relay.py` now.`` | companion | **BROKEN** |
| `:281` | ``Topic slug `relay_globalid` `` | companion | **BROKEN** |
| `:304` | `the forward-looking helper` | spec | fine |
| `:312` | ``Monkeypatch `strawberry.relay.GlobalID` `` | companion | **BROKEN** |
| `:385` | ``NOT a [`DEFERRED_META_KEYS`][base] promotion`` | spec | fine |
| `:452` | ``no shipped `0.0.9` consumer`` | companion | **BROKEN** |
| `:464` | ``A new top-level `relay.py` now.`` | companion | **BROKEN** |
| `:479` | `filter-input tests must ALSO move` | spec | fine |
| `:493` | `owned by the **joint cut**` | spec | fine |
| `:513` | `**Revision 6**` | companion | **BROKEN** |
| `:634` | `filter-input tests must ALSO move` | spec | fine |

**Difference from the handed list.** The count of broken *sites* matched at eight, but the population
was not the one handed over:

1. **`:9` is three claims, not one, and only one third of it was broken.** The handed note read `:9`,
   `:143`, `:464` as one Decision-11 finding each. On `:9` the sentence conjoined two deferrals —
   the top-level `relay.py` module (moved to the companion) and the public `testing/relay` helpers
   (**still in the spec's Decision 11**, which names ``ships [`testing/relay.py`]`` explicitly). A
   blanket repoint of that whole clause at the companion would have made the `testing/relay` half
   *newly* false. The repair splits the clause.
2. **`:281` carries a clause that was false at HEAD, before this cycle touched anything.** Detail
   below; it is the one finding the handed list did not contain.
3. **Every one of the eight "believed good" sites verified good**, including the trap the handed note
   flagged: `spec-031` has exactly **one** `no shipped` occurrence
   (`grep -c 'no shipped' → 1`, at `:109`), and it is the *different* claim about Strawberry's native
   `resolve_type`, not the `:452` quotation. `:452` is therefore genuinely broken and `:127` /`:304`
   are genuinely fine — all three resting on that same line.

### The finding the handed list did not contain: `:281`'s false clause

`:281` read: *"[`spec-031`][spec-031] Decision 1 set the precedent of preferring the convention and
recording the card's older name."*

The second half is false, and was false **before** the Slice-0 move — it is not this cycle's damage.
Proof, taken read-only against pristine HEAD per [`BUILD.md`][build-md]
`## Claims are proven mechanically, never accepted on prose` (no `stash` / `checkout` / `worktree`):

```shell
git show HEAD:docs/SPECS/spec-031-globalid_encoding-0_0_9.md > <scratch outside repo>/spec031-HEAD.md
grep -n '^### Decision 1 ' -A 14 <scratch>/spec031-HEAD.md
grep -on 'docs/spec-[a-z0-9_.-]*' <scratch>/spec031-HEAD.md | sort -u -t: -k2
#   -> docs/spec-031-globalid_encoding-0_0_9-terms.csv
#   -> docs/spec-031-globalid_encoding-0_0_9.md
```

HEAD's Decision 1 records no older card-body filename at all — the only two doc paths it ever named
are its own and its terms CSV. What it recorded was two **rejected topic-slug alternatives**
(`relay_globalid` / `model_globalid`), and that record is exactly what Slice 0 moved. `spec-032`'s
own Decision 1, by contrast, genuinely does reject a card-named file
(`docs/spec-relay_connection.md`) — the sentence appears to have back-projected `spec-032`'s own
situation onto its predecessor.

Because the sentence had to be repointed anyway, the clause was corrected to what `spec-031` actually
did rather than repointed while still false. Recorded here as **pre-existing at HEAD, not
move-induced**.

### Repairs made

All eight in `docs/SPECS/spec-032-full_relay-0_0_9.md`. Seven are pure repoints (the fact and its
wording survive; only the address changes). One (`:13`) needed prose, because "recorded in full **in**
`spec-031` Revision 7" states a containment that is no longer true, and one (`:281`) had the false
clause above.

| Line | Before | After |
|---|---|---|
| `:9` | ``its [Decision 11][spec-031] explicitly deferred the top-level `relay.py` module and the public `testing/relay` helpers to this card`` | ``its [Decision 11][spec-031] explicitly deferred the public `testing/relay` helpers to this card and [reserved the top-level `relay.py` module][spec-031-rationale-d11] for it`` |
| `:13` | ``recorded in full in [`spec-031`][spec-031] Revision 7`` | ``recorded in full in [`spec-031`'s rationale companion][spec-031-rationale-revisions] as Revision 7`` |
| `:143` | ``([`spec-031`][spec-031] Decision 11 explicitly deferred it to this card)`` | ``([`spec-031`][spec-031] [Decision 11][spec-031-rationale-d11] explicitly deferred it to this card)`` |
| `:281` | `…set the precedent of preferring the convention and recording the card's older name.` | `…set the precedent of preferring the convention, with [the naming alternatives it rejected recorded in its rationale companion][spec-031-rationale-d1].` |
| `:312` | ``…patch in [`spec-031`][spec-031] Decision 3)`` | ``…patch in [`spec-031`][spec-031] [Decision 3][spec-031-rationale-d3])`` |
| `:452` | ``([`spec-031`][spec-031] Decision 11 withheld the public export because "no shipped `0.0.9` consumer" existed)`` | ``([`spec-031`][spec-031] [Decision 11][spec-031-rationale-d11] withheld the public export because "no shipped `0.0.9` consumer" existed)`` |
| `:464` | ``the home [`spec-031`][spec-031] Decision 11 explicitly reserved for this card`` | ``the home [`spec-031`][spec-031] [Decision 11][spec-031-rationale-d11] explicitly reserved for this card`` |
| `:513` | `(its Revision 6 swept the stale shipped-slice anchors)` | `(its [Revision 6][spec-031-rationale-revisions] swept the stale shipped-slice anchors)` |

Four link definitions added to the `<!-- docs/SPECS/ -->` group, alphabetically between `[spec-031]`
and `[spec-032]`, anchor strings copied from `spec-031`'s own working defs and re-confirmed against the
companion's `##` headings:

```
[spec-031-rationale-d1]: appx/spec-031-globalid_encoding-0_0_9-rationale.md#decision-1--spec-filename-and-canonical-naming
[spec-031-rationale-d11]: appx/spec-031-globalid_encoding-0_0_9-rationale.md#decision-11--module-location-encodedecode-in-typesrelaypy-no-public-export-in-009
[spec-031-rationale-d3]: appx/spec-031-globalid_encoding-0_0_9-rationale.md#decision-3--the-encode-seam-a-strategy-parameterized-resolve_typename-default
[spec-031-rationale-revisions]: appx/spec-031-globalid_encoding-0_0_9-rationale.md#revision-history
```

Usage: `d11` × 4, `revisions` × 2, `d1` × 1, `d3` × 1. No orphans.

### Candidate findings rejected

- **`:127` — "`spec-031` flagged exactly this and deferred the consumer to this card."** Rejected as a
  finding; the claim resolves. `spec-031:109` still carries the whole thing: Strawberry's native
  decode "is reached only through a root `node(id:)` field, which is **not shipped until**
  `DONE-032-0.0.9`". Nothing moved.
- **`:304` — the quotation "the forward-looking helper `032` dispatches through."** Rejected;
  `spec-031:109` still reads "the package's own `decode_global_id` is the forward-looking helper
  `` [`DONE-032-0.0.9`][kanban] `` dispatches through". The quote is a faithful paraphrase (link → `032`)
  of surviving spec text.
- **`:30`, `:97`, `:385`, `:479`, `:493`, `:634`** — all verified against surviving spec text:
  `TODO(spec-031 … Slice 4)` appears at two sites in `spec-031`'s Slice checklist and Implementation
  plan; the net-new-`ALLOWED_META_KEYS` rule is Decision 6's opening sentence; the Slice-4 test-churn
  precedent is spelled out in both the Slice-4 checklist and the Slice-4 test plan; the joint-cut
  boundary is Decision 12's body.
- **`:452`'s neighbour `:109`-style trap** — the handed note's caution was correct and is confirmed
  mechanically rather than accepted: `grep -c 'no shipped' spec-031 → 1`, at `:109`, and it is not
  the `:452` claim.
- **`:471` — "`031` already pinned the split."** A *bare* `031` reference (no `[spec-031]` link) that
  the handed list did not mention and that I examined as a possible ninth finding. Rejected: the
  "split" it names is foundation-internals vs. consumer-facing surface, and `spec-031`'s surviving
  Decision 11 draws exactly that line ("the encode helper and `decode_global_id` stay internal to
  `types/relay.py` here … That consumer is the sibling card"). It makes no claim about a top-level
  `relay.py`, so the move did not touch it. Left alone.

### Verification

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-032-full_relay-0_0_9.md
OK: 40 terms - all have glossary entries and at least one spec link.
$ echo $?
0

$ uv run python scripts/check_citations.py
OK: 812 citations resolve (731 in 431 .py files, 81 in KANBAN.md).
$ echo $?
0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-032-full_relay-0_0_9.md
$ echo $?
0

$ git diff --check -- docs/SPECS/spec-032-full_relay-0_0_9.md
$ echo $?
0
```

#### Link-scaffold check (hand-rolled)

`<scratch>/linkcheck031.py` — every def used, every use defined, every def target resolving on disk
with the fragment stripped, and every fragment (in-page and cross-file) resolving against a real
heading in the target file. The four known slugger defects are avoided and each avoidance is
commented at its site: (a) markup is rendered out of a heading **before** slugging, so a heading that
is itself a reference link cannot leak its def key into the slug; (b) whitespace runs are **not**
collapsed — spaces are replaced one at a time, so a double space slugs to `--`; (c) code-span content
is masked to **same-length** filler rather than deleted, so a code-span-only link label cannot
collapse to an empty label and report a false orphan; (d) `_` is **not** treated as an emphasis
marker, so `resolve_typename` and `relay_globalid_strategy` survive.

```shell
$ uv run python <scratch>/linkcheck031.py docs/SPECS/spec-032-full_relay-0_0_9.md
file: docs/SPECS/spec-032-full_relay-0_0_9.md
defs: 82  used-keys: 82  in-page anchors: 150
PASS all defs used, all uses defined, all targets and fragments resolve
$ echo $?
0
```

**The instrument was proved failable before its PASS was accepted** — a control that cannot fail reads
exactly like a passing proof. Six probe runs against a scratch copy outside the repo (`--base
docs/SPECS` so relative paths still resolve), each reverted by re-copying:

| Probe | Mutation | Result |
|---|---|---|
| 0 (control) | none | `PASS`, exit 0 |
| 1 | companion `#decision-11--…` fragment → `#decision-11--NOPE` | `FAIL BAD fragment for [spec-031-rationale-d11]`, exit 1 |
| 2 | appended `[zz-orphan]:` def | `FAIL ORPHAN def [zz-orphan]`, exit 1 |
| 3 | use `[spec-031-rationale-d3]` → `…-d33` | `FAIL UNDEFINED use` + `FAIL ORPHAN def`, exit 1 |
| 4 | def path → `appx/NOPE-…` | `FAIL MISSING target`, exit 1 |
| 5 | in-page `(#decision-13--…)` → `(#decision-13--NOPE)` | `FAIL BAD in-page fragment` × 10, exit 1 |

#### Before / after count of broken citations

The defect is a false claim about a resolving target, so no link checker can count it. The census
script grades each claim by locating its load-bearing token in the file the citing line **sends the
reader to**. `before` is pristine HEAD (`git show HEAD:…`, read-only, into a scratch path outside the
repo), where all 19 claims pointed at `spec-031` through the single fragment-less def.

```shell
$ git show HEAD:docs/SPECS/spec-032-full_relay-0_0_9.md > <scratch>/spec032-HEAD.md
$ uv run python <scratch>/citation_census.py before <scratch>/spec032-HEAD.md \
      docs/SPECS/spec-031-globalid_encoding-0_0_9.md \
      docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md
…
mode=before  sites=19  broken=8      (exit 1)

$ uv run python <scratch>/citation_census.py after docs/SPECS/spec-032-full_relay-0_0_9.md \
      docs/SPECS/spec-031-globalid_encoding-0_0_9.md \
      docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md
…
mode=after   sites=19  broken=0      (exit 0)
```

**Before: 8 broken of 19 claims. After: 0 of 19.** Every locator in the table is a substring present
in **both** revisions, so the two runs measure the same population rather than two different ones —
a probe whose locator only matched the "before" text would report a stale-probe failure rather than
a silent pass.

Corroborating measurement, independent of the census table:
`grep -c 'Revision' docs/SPECS/spec-031-globalid_encoding-0_0_9.md → 0`. The spec carries zero
`Revision N` entries, so `:13` and `:513` could not have resolved.

### Diff shape

```shell
$ git diff --stat -- docs/SPECS/spec-032-full_relay-0_0_9.md
 docs/SPECS/spec-032-full_relay-0_0_9.md | 20 ++++++++++++--------
 1 file changed, 12 insertions(+), 8 deletions(-)

$ git diff -U0 -- docs/SPECS/spec-032-full_relay-0_0_9.md | grep '^@@'
@@ -9 +9 @@      @@ -13 +13 @@     @@ -143 +143 @@   @@ -281 +281 @@
@@ -312 +312 @@  @@ -452 +452 @@   @@ -464 +464 @@   @@ -513 +513 @@
@@ -753,0 +754,4 @@
```

Exactly the eight target lines, plus the four new definitions. The `Status:` line, every checkbox, and
every other line of this archived shipped spec are byte-untouched. UTF-8 is intact — em-dash count 422
and arrow count 67, identical before and after.

### Fence compliance

- Written: `docs/SPECS/spec-032-full_relay-0_0_9.md` and this artifact. Nothing else.
- `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` and
  `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md` were **read only**; both are
  final-accepted this cycle and neither needed a change.
- No `.py`, no `KANBAN.*`, no DB, no `docs/GLOSSARY.md` / `docs/TREE.md` / `CHANGELOG.md`, no
  `docs/builder/BUILD.md` / `ARTIFACT.md` / `worker-*.md`. Slice 7's DB and board surfaces untouched.
- Concurrent paths neither edited nor reverted, per `AGENTS.md` rule 34. The dirty set **moved during
  this pass** and the plan's list is stale, which is why it was re-read rather than trusted: at slice
  start `git status --short` showed `consumers.py`, `utils/sessions.py`, `db.sqlite3` and an untracked
  `tests/test_consumers.py`; at slice close the first two and the untracked test are gone (the
  concurrent bug-hunt session committed), `types/definition.py` and `types/relay.py` are dirty, and
  `KANBAN.md` / `KANBAN.html` / `db.sqlite3` are dirty from the concurrent Slice 7. None was touched
  here.
- No `git add`, no commit, no branch. Everything left dirty.
- `AGENTS.md` rule 27: the raw `path:NN` references above sit only inside this `docs/builder/bld-*.md`
  artifact. No raw line reference was introduced into `spec-032`.

### Nothing left unfixable inside the fence

No finding required a file outside the fence. The one item worth carrying forward is a **process**
observation rather than an unfixed defect, recorded for the next author:

- A rationale extraction breaks **foreign** specs' citations, and nothing in the process looks for
  that. `spec-031`'s own internal citations were repaired by Slice 0 because they were in the file
  being edited; `spec-032`'s were not, because the mover never opened it. The mechanical precondition
  is cheap and was never run: before a move, `grep -rln 'spec-<NNN>' docs/` names every file whose
  claims the move can falsify. The `031` cycle would have found `spec-032` immediately.

### Spec changes made (Worker 1 only)

- `docs/SPECS/spec-032-full_relay-0_0_9.md:9`, `:13`, `:143`, `:281`, `:312`, `:452`, `:464`, `:513` —
  eight citations repointed at `spec-031`'s rationale companion, because the Slice-0 move relocated
  the text each claim describes. Seven are pure repoints; `:13` also took the minimum prose change
  ("recorded in full **in** `spec-031` Revision 7" → "in `spec-031`'s rationale companion … as
  Revision 7"), since the containment the original asserted is no longer true.
- `docs/SPECS/spec-032-full_relay-0_0_9.md:281` — the clause "and recording the card's older name" was
  additionally **false at HEAD**, before this cycle: `spec-031`'s Decision 1 never named a card-body
  filename (proved read-only against `git show HEAD:`), it recorded two rejected topic-slug
  alternatives. Corrected to what `spec-031` actually did, in the same edit that repointed the
  sentence. Pre-existing defect, not move-induced.
- `docs/SPECS/spec-032-full_relay-0_0_9.md:754-757` — four `[spec-031-rationale-*]` link definitions
  added to the `<!-- docs/SPECS/ -->` group; every one is used, none is an orphan.
- No other change: no `Status:` edit, no checkbox change, no contract prose beyond the two sentences
  named above.

### Final status

`final-accepted`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

[spec-031]: ../SPECS/spec-031-globalid_encoding-0_0_9.md

<!-- docs/builder/ -->

[build-md]: BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
