# Build: Slice 8 — repair the `spec-032` citations the **spec-030** rationale move relocated

Spec reference: `docs/SPECS/spec-032-full_relay-0_0_9.md` (the repaired file; an archived, shipped spec).
Cause: the **spec-030** residual cycle (2026-08-25, commit `6b3e1c82`) — the MOVE of `spec-030`'s
deliberative layer into `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md`. Not this
cycle's damage; the maintainer authorized repairing it here because `spec-032` is in fence and
already open.
Build plan: `docs/builder/build-031-globalid_encoding-0_0_9.md`
(`### Fence amendment (maintainer, post-final-gate)`, **Third authorization**).
Predecessor slice: `docs/builder/bld-031-slice-6-spec_032_citation_repair.md` (same file, same defect
class, `spec-031`'s move). This diff is strictly additive to Slice 6's; nothing of Slice 6's was
reverted or altered.
Status: final-accepted

Closed by **procedural closure** ([`BUILD.md`][build-md] `### Procedural-closure slices`): the change is
confined to one spec file, so this is one Worker 1 pass with a combined Plan + Final-verification block
and `Status: final-accepted` set directly. No Worker 2, no Worker 3.

## Plan (Worker 1)

### The defect class

Identical in shape to Slice 6's and different in origin. `spec-032` cites `spec-030` through one
fragment-less reference definition, `[spec-030]: spec-030-connection_field-0_0_9.md`. The spec-030
cycle MOVED that spec's `Revision history` block and every Decision's justification and rejected
alternatives into the companion. The link still **resolves** — the file exists and the def never
pointed at a fragment — so every link checker in the repo reports these clean **by construction**.
What broke is the truth of each line's claim about the target's *content*.

Structural facts, re-measured rather than accepted from the handed brief:

```shell
$ grep -c '^- \*\*Revision [0-9]' docs/SPECS/spec-030-connection_field-0_0_9.md            # 0
$ grep -c '^- \*\*Revision [0-9]' docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md  # 23
$ grep -c 'Alternatives considered' docs/SPECS/spec-030-connection_field-0_0_9.md          # 0
$ grep -c 'Alternatives considered' docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md  # 15
$ grep -c '^- \*\*Revision [0-9]' docs/SPECS/spec-032-full_relay-0_0_9.md                  # 8 (its OWN)
```

So both the revision history and every rejected alternative moved; the Decisions (1-14) and their
contract prose stayed. `spec-030`'s Decision **justifications** moved too — the brief did not say so,
and one finding turns on it (`:440`).

### DRY analysis

- **Helper inventory checked.** Not applicable in the package sense — this slice writes no Python into
  the package. The documentation-side equivalent was run: `spec-030`'s own working link definitions
  were read out of its `<!-- LINK DEFINITIONS -->` block (`docs/SPECS/spec-030-connection_field-0_0_9.md`,
  the `[rationale-d1]`…`[rationale-d14]` / `[rationale-risks]` / `[spec-030-rationale]` set) so the new
  `spec-032` definitions **reuse that file's already-proven anchor strings** rather than re-deriving
  slugs by hand. Shapes searched for: `rationale`, `appx/`, `#decision-`, `#revision-history`.
- **Existing patterns reused.** Slice 6's shape, verbatim: namespaced `[spec-030-rationale-*]` keys
  (a bare `[rationale-d3]` in `spec-032` would read as `spec-032`'s own), placed in the
  `<!-- docs/SPECS/ -->` group alphabetically between `[spec-030]` and `[spec-031]`, mirroring how
  Slice 6 seated `[spec-031-rationale-*]` between `[spec-031]` and `[spec-032]`.
- **New helpers justified.** Two link definitions, no more: `[spec-030-rationale-d3]` and
  `[spec-030-rationale-revisions]`. A bare `[spec-030-rationale]` def was **not** added, and neither
  was a `[spec-030-rationale-d9]` — nothing used them, and an unused def is an orphan defect.
  Definitions for the other twelve Decisions were not added because no repaired claim points at them.
- **Duplication risk avoided.** The naive repair re-words each broken sentence to drop the fact. Two of
  the three facts are still true verbatim; only their address changed. Repointing preserves them.

### Dispatched findings checklist

- [x] Re-derive the full population of `spec-030` citations independently; treat the handed line list
      as a candidate set only.
- [x] Grade **every** candidate, distinguishing `spec-030`'s revisions from `spec-032`'s OWN.
- [x] Look for citations the `spec-030`-substring grep could miss (line-break-spanning sentences,
      the connection spec named without the token).
- [x] Repair every broken citation, preferring a repoint at the companion over rewording away the fact.
- [x] Split any conjoined clause that is only half-broken.
- [x] Add only the link definitions actually used, in the `<!-- docs/SPECS/ -->` group, alphabetically.
- [x] `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-032-full_relay-0_0_9.md`.
- [x] `uv run python scripts/check_citations.py`.
- [x] `uv run python scripts/check_trailing_commas.py --check` and `git diff --check`.
- [x] Link-scaffold check on `spec-032`, **proved failable** before its PASS was accepted.
- [x] Before/after broken-citation census against a pristine pre-slice copy, command quoted.
- [x] State which candidates were rejected as fine, with proof for each.
- [x] Record any pre-existing (non-move-induced) defect separately, proved with `git show`.

---

## Final verification (Worker 1)

### Re-derived population

`grep -n 'spec-030' docs/SPECS/spec-032-full_relay-0_0_9.md` returns **21** lines: 20 citing lines plus
the link definition at `:752`. The 20 citing lines match Worker 0's candidate set exactly
(`:9 :40 :64 :87 :97 :98 :101 :139 :186 :192 :281 :367 :385 :433 :440 :493 :518 :531 :581 :602`).

**But the line set is not the claim set.** Grading is per claim, and three lines carry more than one:

- `:9` (the Predecessors line) makes **four** separate claims about `spec-030` — Decisions 4, 6, 7, 9.
- `:433` conjoins **two** — `spec-030`'s Revision 2 *and* its Edge cases language.

The graded population is therefore **24 claims across 20 lines**, not 20.

**Two completeness sweeps the substring grep cannot do, both run:**

1. **Line-break-spanning citations.** `spec-032` hard-wraps nothing — every prose paragraph is a single
   physical line (verified: no short non-list line lacking terminal punctuation outside fenced code).
   A sentence therefore cannot straddle two lines, so the grep population is complete.
2. **`spec-030` named without the token.** `grep -n '030' … | grep -v 'spec-030'` returns eight lines,
   all naming the **kanban card** `DONE-030-0.0.9` or the bare card number `030` (`:3 :51 :125 :288
   :294 :442 :491 :623 :632`). None makes a claim about the *spec file's* content — `:288` describes
   what the shipped card delivered, `:442` is `spec-032`'s **own** rejected alternative (it has no
   companion; its alternatives stay in-file), `:294` cites the card's dependency list. No ninth
   finding. Also swept: `connection spec`, `connection-field spec`, `the connection card`,
   `rationale companion` — no untokenized reference.

### The false-positive trap, disarmed mechanically

`spec-032` has **8** of its own `- **Revision N` entries and no companion. Its **Revision 3 P2** made
bare `Revision N Pn` its house citation convention for its own history:

> Every normative citation now points at the revision-history entry (the stable, self-contained
> record): "Revision 2 P1/P2".

`grep -on 'Revision [0-9][^,.)]*'` finds **31** `Revision N` references in normative sections; every one
is `spec-032`'s own except where the text attaches it to `spec-030` with a possessive. Decisive
corroboration that a bare `Revision 2 P1` cannot be `spec-030`'s: **`spec-030`'s Revision 2 P1 is not
about cursors at all.** Its four P1s were the optimizer-plan hook, the `totalCount` per-target class,
the missing `first`+`last` guard, and the sidecar-argument mechanism; the stale-`after` correction was
its Revision 2 **P3**. So the four sites citing "Revision 2 P1" about cursor semantics (`:101 :433-tail
:518 :581`) are self-references by content as well as by convention.

### Graded population — the full table

`spec` = the claim resolves against `docs/SPECS/spec-030-connection_field-0_0_9.md`; `companion` = the
text it names now lives in `appx/spec-030-connection_field-0_0_9-rationale.md`.

| Claim | Load-bearing token | Lives in | Verdict |
|---|---|---|---|
| `:9` D4 | `Decision 4 — `DjangoConnection[T]` base plus per-target concrete connection classes` | spec | fine |
| `:9` D6 | `Decision 6 — Sidecar-derived arguments via a synthesized resolver signature` | spec | fine |
| `:9` D7 | `Decision 7 — Composition pipeline` | spec | fine |
| `:9` D9 | `Decision 9 — Cursor encoding delegated to Strawberry` | spec | fine |
| `:40` | `**Revision 2** — first feedback pass (review of rev1)` | companion | **BROKEN** |
| `:64` | `Decision 11 — The connection field owns its optimizer cooperation point` | spec | fine |
| `:87` | `Decision 8 — `Meta.connection` opt-in key, stored on the definition` | spec | fine (but see below) |
| `:97` | ``NOT a [`DEFERRED_META_KEYS`][base] promotion`` | spec | fine |
| `:98` | `_connection_type_for(target_type)` | spec | fine |
| `:101` | `offset-cursor stability under *concurrent mutation* is **not guaranteed**` | spec | fine |
| `:139` | `This card writes no cursor scheme of its own` | spec | fine |
| `:186` | `ListConnection` | spec | fine |
| `:192` | `Decision 9 — Cursor encoding delegated to Strawberry` | spec | fine |
| `:281` | `DjangoConnectionField` | spec | fine |
| `:367` | `_connection_type_for(target_type)` | spec | fine |
| `:385` | ``NOT a [`DEFERRED_META_KEYS`][base] promotion`` | spec | fine |
| `:433` rev half | `**Revision 2** — first feedback pass (review of rev1)` | companion | **BROKEN** |
| `:433` edge half | `the query does **not** error, but offset cursors encode a position` | spec | fine |
| `:440` | `duplicate correct engine behavior` | companion | **BROKEN** |
| `:493` | ``Decision 13 — Version bumps are owned by the joint `0.0.9` cut`` | spec | fine |
| `:518` | `offset-cursor stability under *concurrent mutation* is **not guaranteed**` | spec | fine |
| `:531` | `dispatch-frozen at build time` | spec | fine |
| `:581` | `test_genre_connection_first_zero_empty_edges` | spec | fine |
| `:602` | `test_genre_connection_full_round_trip` | spec | fine |

**3 broken of 24.** Fewer than Slice 6's eight, and the reason is structural: `spec-032` reuses
`spec-030` as *machinery* — Decisions, factory pieces, pipeline steps, error contracts — where it
reused `spec-031` as *history* (deferrals, revisions, naming precedents). Contract citations survive a
rationale move by construction; history citations do not.

### How the graded population differed from the candidate set

1. **The candidate line set was exactly right; the claim population was not.** 20 lines, 24 claims.
   Worker 0's list could not have shown the `:9` fan-out or the `:433` conjunction.
2. **`:433` is Slice 6's trap #1 again — a conjoined clause, half broken.** `(its Revision 2 / Edge
   cases language)` names two things at once. The Revision 2 half moved; the Edge cases half is still
   in `spec-030` (`:460`, the surviving stale-`after` bullet). A blanket repoint of the parenthetical
   at the companion would have made the Edge-cases half *newly* false. The repair splits it.
3. **`:440` is a finding the brief's own framing would have missed.** The brief said the revision
   history and the rejected alternatives moved. `spec-030`'s Decision **justifications** moved too, and
   `:440` cites one ("the explicit rationale that hand-rolling pagination math is engine duplication").
   That is neither a Revision nor a rejected alternative, so neither of the brief's two broken-shapes
   would have caught it.
4. **Four sites the brief warned about were exactly the trap it described, and all four are fine.**
   `:101 :433`-tail `:518 :581` cite `Revision 2 P1` — `spec-032`'s own, proved twice over above.
5. **One claim is false but is NOT this slice's to fix.** `:87`, below.

### The finding that is false at HEAD and deliberately NOT edited: `:87`

`:87` reads: *"`Meta.connection` on a non-Relay-Node type is rejected with the
add-`relay.Node`-or-remove-the-key remediation ([`spec-030`][spec-030] Decision 8)."*

The **citation** resolves — `spec-030`'s Decision 8 does state that rejection, and it never moved. The
**remediation wording is wrong about the shipped diagnostic**: `"or remove the key."` is the
`Meta.relation_shapes` gate's tail, not `Meta.connection`'s.

```shell
$ grep -n '_RELAY_NODE_GATE_INHERIT_TAIL' django_strawberry_framework/types/base.py
# 261-262: f"{...}.Meta.connection {_RELAY_NODE_GATE_LEAD} " f"{_RELAY_NODE_GATE_INHERIT_TAIL}"
# _RELAY_NODE_GATE_INHERIT_TAIL = "or inherit `relay.Node` directly."
# 361-362: f"{...}.Meta.relation_shapes {_RELAY_NODE_GATE_LEAD} " "or remove the key."
```

`spec-032`'s own `:389` states the correct pairing (`Meta.relation_shapes` … "or remove the key").
`types/base.py` `#"the relation_shapes gate appends the spec-pinned"` says so as well.

Proved **pre-existing, not move-induced**, read-only per [`BUILD.md`][build-md]
`## Claims are proven mechanically, never accepted on prose` (no `stash` / `checkout` / `worktree`):

```shell
$ git show HEAD:docs/SPECS/spec-032-full_relay-0_0_9.md > <scratch outside repo>/spec032-HEAD.md
$ diff <(sed -n '87p' <scratch>/spec032-HEAD.md) <(sed -n '87p' docs/SPECS/spec-032-full_relay-0_0_9.md)
#   -> IDENTICAL (unchanged by Slice 6 and by this slice)
$ grep -c 'remove the key' <scratch>/spec030-premove.md            # 0  (git show 6b3e1c82^:…)
$ grep -c 'remove the key' docs/SPECS/spec-030-connection_field-0_0_9.md          # 0
$ grep -c 'remove the key' docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md  # 0
```

The phrase was never in `spec-030`, before or after the move, so the move did not cause it.

**Why it is NOT edited here, unlike Slice 6's `:281`.** Slice 6 corrected a false clause because that
sentence *had to be repointed anyway* — the correction rode a citation repair. `:87` needs no repoint:
its citation resolves. Editing it would be a contract-prose change to an archived shipped spec beyond
this slice's mandate ("citation repair only; do not change contract prose beyond the minimum needed to
make a repointed sentence true"). **Recorded and routed to the maintainer / a future `032` cycle**, not
silently fixed and not silently dropped.

### Repairs made

Three, all in `docs/SPECS/spec-032-full_relay-0_0_9.md`. Two are pure repoints. One (`:440`) needed
prose, because the sentence quoted `spec-030`'s Decision-9 rationale in wording the companion no longer
uses.

| Line | Before | After |
|---|---|---|
| `:40` | ``[`spec-030`][spec-030] had already corrected this exact claim in its Revision 2.`` | ``…in [its Revision 2][spec-030-rationale-revisions].`` |
| `:433` | ``already corrected this exact claim (its Revision 2 / Edge cases language)`` | ``already corrected this exact claim ([its Revision 2][spec-030-rationale-revisions] / the spec's own Edge cases language)`` |
| `:440` | ``Decision 9 already delegated cursor mechanics with the explicit rationale that hand-rolling pagination math is engine duplication`` | ``Decision 9 already delegated cursor mechanics, on the [rationale its companion records][spec-030-rationale-d3] that re-implementing cursor math duplicates correct engine behavior`` |

**Why `:40` and `:433` are pure repoints and Slice 6's `:13` was not.** Slice 6 had to reword because
"recorded in full **in** `spec-031` Revision 7" asserted containment *in the spec file* the
`[spec-031]` link resolved to. Here the link text `its Revision 2` carries no file-containment claim —
"spec-030's Revision 2" is a revision **of spec-030** whichever file records it, and the companion
itself frames the block as "the spec's own, verbatim". The link now lands the reader on it.

**Why `:433` is split.** Only the Revision-2 half moved. The Edge-cases half resolves against surviving
`spec-030` text (`:460`, ``the query does **not** error, but offset cursors encode a position``), so the
repoint is scoped to the first half and the second is explicitly attributed to "the spec's own Edge
cases language". The trailing `(Revision 2 P1)` on the same line is `spec-032`'s own and is untouched.

**Why `:440` needed prose, and where its target actually lives.** The claim was true when `spec-032`
was authored: `spec-030`'s original Decision 9 justification read *"delegating to them keeps cursor
behavior the engine's responsibility ([Decision 3])"*. Two things then happened to it, in order:

1. **A later `spec-030` revision narrowed Decision 9's justification**, dropping the
   engine-responsibility clause. Pre-existing at the move, not caused by it:

   ```shell
   $ git show 6b3e1c82^:docs/SPECS/spec-030-connection_field-0_0_9.md > <scratch>/spec030-premove.md
   $ grep -n '^### Decision 9' -A 8 <scratch>/spec030-premove.md
   #   Justification: opaque offset cursors are the Relay-spec-compliant default `ListConnection`
   #   ships; stable cursors are a meaningfully larger design routed to `BACKLOG.md` item 39 …
   $ git show eaaf1385:docs/spec-030-connection_field-0_0_9.md | grep -n '^### Decision 9' -A 8
   #   - Opaque offset cursors are the Relay-spec-compliant default … delegating to them keeps
   #     cursor behavior the engine's responsibility ([Decision 3]).
   ```

2. **The move then relocated whatever justification remained.** The engine-duplication rationale in its
   surviving form — *"Re-implementing cursor math would duplicate correct engine behavior and drift
   from the Relay spec"* — now lives in the companion under **Decision 3**, not Decision 9
   (`appx/spec-030-connection_field-0_0_9-rationale.md` `## Decision 3` → `### Justification (moved from
   the spec)`). So the repoint targets `d3`, and the prose is re-worded to the companion's actual words
   rather than left quoting a phrasing no file carries.

   The nearest surviving `spec-030` sentence, ``We do NOT hand-roll cursor math.`` (`:162`), is in the
   prior-art / Current state section — a statement of what the card does, not Decision 9's rationale —
   so it does not rescue the original claim.

Two link definitions added to the `<!-- docs/SPECS/ -->` group, alphabetically between `[spec-030]` and
`[spec-031]`, both **copied verbatim from `spec-030`'s own working defs** and re-confirmed against the
companion's `##` headings by the scaffold check:

```
[spec-030-rationale-d3]: appx/spec-030-connection_field-0_0_9-rationale.md#decision-3--build-on-strawberrys-native-relay-machinery-but-own-the-first--last-guard
[spec-030-rationale-revisions]: appx/spec-030-connection_field-0_0_9-rationale.md#revision-history
```

Usage: `revisions` × 2 (`:40`, `:433`), `d3` × 1 (`:440`). No orphans.

### Candidates rejected as fine, with proof for each

Every rejection was proved by locating the claim's load-bearing token in `spec-030` **and** confirming
it is absent from — or irrelevant to — the companion, not by reading the sentence and agreeing with it.

- **`:9` D4 / D6 / D7 / D9** — the four Decision headings survive verbatim in `spec-030`
  (`:308 :348 :356 :387`). Decision 9's heading *changed* post-ship
  (`Opaque cursor delegated to Strawberry; Meta.cursor_field deferred` →
  `Cursor encoding delegated to Strawberry; keyset cursors are a separate opt-in`), which is harmless
  here: `[spec-030]` is fragment-less, and "cursor delegation" is still what the Decision says.
- **`:64`** — `spec-030` `### Decision 11 — The connection field owns its optimizer cooperation point`
  is intact, including the `apply_connection_optimization` seam the line calls "its own cooperation
  seam". Nothing moved.
- **`:97` / `:385`** — the net-new-key rule is Decision 8's **opening sentence** in `spec-030`:
  ``lands **directly** in [`ALLOWED_META_KEYS`][base] (NOT a [`DEFERRED_META_KEYS`][base] promotion…)``.
  `grep -cF 'NOT a [`DEFERRED_META_KEYS`][base] promotion' spec-030 → 2`. Contract, not deliberation.
- **`:98` / `:367`** — `_connection_type_for(target_type)` appears **7** times in `spec-030` (Decision 8
  and the implementation plan); the synthesized signature is Decision 6 and the pipeline tail is
  Decision 7. All contract.
- **`:101` / `:518`** — both cite `spec-030`'s *corrected contract*, which is the surviving Edge-cases
  bullet at `spec-030:460`; the accompanying `Revision 2 P1` is `spec-032`'s own (see the trap section).
- **`:139` / `:192`** — Decision 9's body still reads ``This card writes no cursor scheme of its own``
  (`grep -c → 1` in `spec-030`, `0` in the companion). "Delegated cursor mechanics wholesale" resolves.
- **`:186`** — a claim about the machinery `spec-030` describes, not about any moved text; `ListConnection`
  appears 17× in `spec-030`.
- **`:281`** — ``the connection field shipped separately under [`spec-030`][spec-030]`` is a statement
  about what the card shipped. (Slice 6 already edited this line's *`spec-031`* half; that edit was
  read, confirmed correct, and left alone.)
- **`:493`** — ``### Decision 13 — Version bumps are owned by the joint `0.0.9` cut`` is intact in
  `spec-030`.
- **`:531`** — Decision 10's ``**Dispatch shape — the connection field is dispatch-frozen at build
  time, NOT per-call.**`` paragraph survives in `spec-030` in full; only its justification and one
  rejected alternative moved, and `:531` cites neither.
- **`:581` / `:602`** — "the shipped spec-030-era `test_genre_connection_*`" names live test functions;
  both names are still in `spec-030`'s Test plan. No content claim about moved text.
- **`:433`'s Edge-cases half and its trailing `(Revision 2 P1)`** — both deliberately left pointing
  where they were; see the split above.
- **`:87`** — the *citation* is rejected as a finding (Decision 8 states the rejection and never
  moved). The *remediation wording* is a separate, pre-existing falsehood, recorded above rather than
  fixed, because no repoint is needed there.
- **The eight bare-`030` lines** (`:3 :51 :125 :288 :294 :442 :491 :623 :632`) — all kanban-card
  references or `spec-032`'s own rejected alternative; examined as possible findings the substring grep
  could not reach, and rejected.

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

#### Link-scaffold check (hand-rolled), proved failable first

`<scratch>/linkcheck031.py` — every def used, every use defined, every def target resolving on disk with
the fragment stripped, and every fragment (cross-file and in-page) resolving against a real heading in
the target file. The known slugger defects are avoided and each avoidance is commented at its site:
(a) markup is rendered out of a heading **before** slugging, so a heading that is itself a reference
link cannot leak its def key into the slug; (b) whitespace runs are **not** collapsed — each space
becomes its own hyphen, so a double space slugs to `--`; (c) code spans lose their **backticks only**
and keep their content, so ``the joint `0.0.9` cut`` slugs to `joint-009-cut`; (d) `_` is **not**
treated as an emphasis marker, so `resolve_typename` / `relation_shapes` / `metafields_class` survive.

Defect (c) is worth naming: the first build of this instrument masked code-span content to same-length
filler and then dropped it, and that produced **37 false FAILs** — every `docs/GLOSSARY.md` anchor, both
`spec-031-rationale` Decision anchors, and four in-page Decision anchors. It failed loudly rather than
passing silently, which is the only reason it was caught in one run.

```shell
$ uv run python <scratch>/linkcheck031.py docs/SPECS/spec-032-full_relay-0_0_9.md
file: docs/SPECS/spec-032-full_relay-0_0_9.md
defs: 84  used-keys: 84  in-page anchors: 20
PASS all defs used, all uses defined, all targets and fragments resolve
$ echo $?
0
```

**A control that cannot fail reads exactly like a passing proof.** Seven runs against a scratch copy
outside the repo (`--base docs/SPECS` so relative paths still resolve), each mutation applied to a fresh
copy of the real file:

| Probe | Mutation | Result |
|---|---|---|
| 0 (control) | none | `PASS`, exit 0, 0 FAIL lines |
| 1 | both `rationale.md#revision-history` fragments → `…-NOPE` | exit 1, 2 × `FAIL BAD fragment` (`spec-030-rationale-revisions`, `spec-031-rationale-revisions`) |
| 2 | appended `[zz-orphan]: NEXT.md` | exit 1, `FAIL ORPHAN def [zz-orphan]` |
| 3 | use `][spec-030-rationale-d3]` → `][spec-030-rationale-d33]` | exit 1, `FAIL UNDEFINED use` + `FAIL ORPHAN def` |
| 4 | def path → `appx/NOPE-030-…` | exit 1, `FAIL MISSING target` |
| 5 | in-page `(#decision-13--version-bumps-are-owned-by-the-joint-009-cut)` → `(#decision-13--NOPE)` | exit 1, `FAIL BAD in-page fragment` |
| 6 (restore control) | none | `PASS`, exit 0, 0 FAIL lines |

Exit codes were read directly from the interpreter, not through a pipe — a first attempt read `tail`'s
status and reported `exit=0` for every failing probe, which is the same fail-open shape the probes exist
to prevent.

#### Before / after broken-citation census

The defect is a false claim about a **resolving** target, so no link checker can count it.
`<scratch>/census030.py` grades each of the 24 claims by (1) locating the citing line by a probe string,
(2) deciding which file that line sends the reader to **for that claim** — the companion when the
claim's own text sits inside a `[...][spec-030-rationale-*]` label, otherwise `spec-030` via the line's
fragment-less `[spec-030]` def — and (3) asserting the load-bearing token is present in that file.

`before` is the **pristine pre-slice file**, copied aside before the first edit. `git show HEAD:` is the
wrong baseline here: HEAD predates Slice 6, whose repairs to the same file are final-accepted and must
not be re-measured as this slice's. `git stash` is forbidden in this repo.

```shell
$ cp docs/SPECS/spec-032-full_relay-0_0_9.md <scratch>/spec032-preslice8.md   # BEFORE the first edit

$ uv run python <scratch>/census030.py before <scratch>/spec032-preslice8.md \
      docs/SPECS/spec-030-connection_field-0_0_9.md \
      docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
…
mode=before  claims=24  broken=3  stale-probes=0      (exit 1)

$ uv run python <scratch>/census030.py after docs/SPECS/spec-032-full_relay-0_0_9.md \
      docs/SPECS/spec-030-connection_field-0_0_9.md \
      docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
…
mode=after   claims=24  broken=0  stale-probes=0      (exit 0)
```

**Before: 3 broken of 24 claims. After: 0 of 24.** The three that flipped are `:40`, `:433-rev`, and
`:440`; the other 21 report `spec-030 [spec-030] OK` identically in both runs, which is the point — the
census measures the **same** population twice rather than two different ones.

**The census is itself failable, and its stale-probe guard was exercised, not asserted.** Running the
`after` probes against the `before` file must not silently pass:

```shell
$ uv run python <scratch>/census030.py after <scratch>/spec032-preslice8.md <spec-030> <companion>
…
mode=after   claims=24  broken=2  stale-probes=1      (exit 1)
```

The one stale probe is `:440` — the only site whose prose changed, so its locator legitimately differs
between revisions — and the two remaining `broken` are exactly the two Revision-2 claims, unrepaired in
that file. A probe that matched only the "after" text would have shown up here as a stale probe rather
than as a silent pass.

Corroborating measurements, independent of the census table:

```shell
$ grep -c '^- \*\*Revision [0-9]' docs/SPECS/spec-030-connection_field-0_0_9.md          # 0
$ grep -cF 'duplicate correct engine behavior' docs/SPECS/spec-030-connection_field-0_0_9.md   # 0
$ grep -cF 'duplicate correct engine behavior' docs/SPECS/appx/…-rationale.md            # 1
```

`spec-030` carries zero `Revision N` entries, so `:40` and `:433`'s first half could not have resolved.

### Diff shape

```shell
$ diff -u <scratch>/spec032-preslice8.md docs/SPECS/spec-032-full_relay-0_0_9.md | grep -c '^[+-]'
10        # 2 file headers + 3 changed lines (before/after) + 2 added defs

$ git diff --stat -- docs/SPECS/spec-032-full_relay-0_0_9.md
 docs/SPECS/spec-032-full_relay-0_0_9.md | 28 +++++++++++++++++-----------
 1 file changed, 17 insertions(+), 11 deletions(-)      # Slice 6 (8 lines + 4 defs) + Slice 8
```

Exactly the three target lines, plus the two new definitions. The `Status:` line, every checkbox, and
every other line of this archived shipped spec are byte-untouched. **Slice 6's eight repaired lines and
four definitions are present and unmodified** — this diff is strictly additive to theirs.

UTF-8 intact: em-dash count **422** and arrow count **67**, identical before and after (matching the
counts Slice 6 recorded, since neither slice touched an em dash or an arrow). Line count 792 → 794, the
two added defs.

### Fence compliance

- Written: `docs/SPECS/spec-032-full_relay-0_0_9.md` and this artifact. Nothing else.
- `docs/SPECS/spec-030-connection_field-0_0_9.md`, its companion,
  `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` and its companion were **read only**. None needed a
  change and none was touched.
- No `.py`, no `KANBAN.*`, no DB, no `docs/GLOSSARY.md` / `docs/TREE.md` / `CHANGELOG.md`, no
  `docs/builder/BUILD.md` / `ARTIFACT.md` / `worker-*.md`.
- Concurrent paths neither edited nor reverted, per `AGENTS.md` rule 34. The dirty set was re-read at
  slice start rather than taken from the plan (it has moved twice this cycle): `KANBAN.md`,
  `KANBAN.html`, `examples/fakeshop/db.sqlite3` (Slice 7), `django_strawberry_framework/types/definition.py`,
  `django_strawberry_framework/types/relay.py`, `docs/SPECS/spec-031-globalid_encoding-0_0_9.md`, and the
  untracked `0_0_14.md` plus the `031` artifacts. Unchanged at slice close except this artifact and
  `spec-032`.
- All scratch files (`linkcheck031.py`, `census030.py`, the pristine copies, the probe copy) live
  **outside** the repository, under the session scratchpad.
- No `git add`, no commit, no branch. Everything left dirty.
- `AGENTS.md` rule 27: the raw `path:NN` references above sit only inside this `docs/builder/bld-*.md`
  artifact. No raw line reference was introduced into `spec-032`.

### Left unfixed inside the fence

One item, deliberately, and it is recorded rather than dropped:

- **`spec-032:87` attributes the `Meta.relation_shapes` remediation tail ("or remove the key") to the
  `Meta.connection` diagnostic.** False against the shipped code and against `spec-032`'s own `:389`.
  Pre-existing at HEAD, not move-induced, proved above. Not repaired here because the line needs no
  citation repoint and correcting it would be contract-prose surgery on an archived shipped spec beyond
  this slice's mandate. **Owner: the maintainer, or a future `032` cycle.**

Process observation carried forward, extending Slice 6's:

- Slice 6 recorded that a rationale extraction breaks **foreign** specs' citations and that
  `grep -rln 'spec-<NNN>' docs/` before a move is the cheap precondition nobody runs. This slice adds
  the second half of the lesson: **the precondition must be run for the moved spec's Decision
  justifications too, not only its revision history and rejected alternatives.** `:440` was broken by
  a justification move, a shape the third authorization's own framing did not enumerate — and a grep
  vocabulary derived from that framing (`Revision`, `Alternatives`) would have missed it. The population
  is the citing lines, not the moved headings.

### Spec changes made (Worker 1 only)

- `docs/SPECS/spec-032-full_relay-0_0_9.md:40`, `:433` — the two ``its Revision 2`` claims about
  `spec-030` repointed at `[spec-030-rationale-revisions]`, because the spec-030 residual cycle moved
  that revision history into the companion. Pure repoints; the facts and their wording survive.
  On `:433` only the Revision-2 half was repointed: the conjoined "Edge cases language" half still
  resolves against surviving `spec-030` text and a blanket repoint would have made it newly false.
- `docs/SPECS/spec-032-full_relay-0_0_9.md:440` — the Decision-9 rationale citation repointed at
  `[spec-030-rationale-d3]`, where the engine-duplication rationale now lives, with the minimum prose
  change needed to quote the companion's surviving words (``re-implementing cursor math duplicates
  correct engine behavior``) instead of a phrasing no file carries. Recorded separately: `spec-030`
  narrowed Decision 9's justification **before** the move, so the wording drift is pre-existing while
  the address break is move-induced; both are discharged by this one edit.
- `docs/SPECS/spec-032-full_relay-0_0_9.md:752-753` — two `[spec-030-rationale-*]` link definitions
  added to the `<!-- docs/SPECS/ -->` group, alphabetical, anchors copied verbatim from `spec-030`'s own
  working defs. Both are used; neither is an orphan.
- **Not changed:** `:87`'s false remediation attribution (recorded above, routed to the maintainer).
  No `Status:` edit, no checkbox change, no contract prose beyond the one sentence named above.

### Final status

`final-accepted`.

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
