# Build: Slice 3 — cross-spec residue + foreign-citation repair (spec-032)

Spec reference: `docs/SPECS/spec-032-full_relay-0_0_9.md` (whole file; 707 lines before this pass, 710 after)
Status: final-accepted

Worker-1-only spec-custody slice per the build plan's `## Dispatch shape`: no Worker 2 build pass and no
Worker 3 per-slice review (the Worker 3 pass over the whole spec diff runs next). This artifact carries one
combined Plan + Final-verification block. **Seven `.py` files were touched, comment/docstring text only, and
each one carries a mechanical proof that its executable bytes are unchanged (Verification 5).**

## Plan + Final verification (Worker 1)

### Spec status-line re-verification

Read spec lines 1-11 (title, shipped-in header, `Status:`, Owner, Predecessors, the Slice-0 deliberative-layer
pointer) before acting. **No edit was owed this pass**, and that is a result rather than a skipped step: the
three corrections this slice makes (`Meta.cursor_field` shipped, `max_page_size` bounds a connection page,
`033` shipped and discharged the pre-`033` posture) were each searched for in the header's own vocabulary.
The header's only version claims are already scoped (`the on-disk version is still 0.0.8 at spec-authoring
time`; `Current state` explicitly describes the repo `before the build`), the `Status:` line's Slice-4
summary names the conformance suite without naming any page bound, and Slice 2's `siblings` -> per-relation
rewrite still reads correctly. Recorded because Slice 2 found a finding here and an unrun check is
indistinguishable from a passing one.

### DRY analysis

**Helper inventory checked.** Not applicable to source: this slice writes no Python logic and proposes no
helper. Recorded rather than skipped so a later pass can see the question was asked. The three *instruments*
this pass wrote (census classifier, anchor checker, inverse prover) live in the session scratchpad outside the
repo and are quoted here in full effect, never committed.

- **Existing patterns reused.** Slices 1 and 2's shapes, unchanged: `**Post-ship:**` bullets under a
  companion Decision's `### Changes this Decision underwent`; `**Item N ...**` paragraphs prepended to the
  companion's `## Risks and open questions` body; in-spec corrections that state the contract directly and
  never narrate a chronology. The anchor checker is Slice 2's design with two slugger bugs fixed (below).
- **New helpers justified.** None.
- **Duplication risk avoided.** The `TODO-BETA-062` products-deferral correction has **seven** prose homes.
  Writing the full correction into all seven would have been seven near-copies drifting apart on the next
  edit. The correction is written **once** in `### Decision 12` — the normative home — and the other six
  carry a one-clause scope qualifier pointing at it. That is the same reason the spec states one contract in
  five homes and the same reason a half-fix is worse than none.

### Findings re-verified against source

Every finding was re-opened at `HEAD` before a word was changed. **No code defect was found**, so the
escalation path in the slice brief was not taken.

| # | Verdict | Symbol-qualified evidence |
| --- | --- | --- |
| B4 (`Meta.cursor_field` shipped) | **Confirmed** | `django_strawberry_framework/types/base.py` #"cursor_field" sits in `ALLOWED_META_KEYS` (line 73 of the literal), validated at class creation by `::_validate_cursor_field` (shape + Relay-Node gate, delegating column references to `keyset.py::validate_cursor_field_references`) and at finalization by `keyset.py::validate_cursor_field_columns`; the slot is carried on the definition (`types/base.py` #"cursor_field: tuple[str, ...] \| None"). The subsystem is the net-new `django_strawberry_framework/keyset.py`, whose module docstring opens "Keyset (value-encoded) stable cursors - the ``Meta.cursor_field`` opt-in" and names "The BACKLOG ``stable_cursor_field`` contract". Provenance measured: `git log -S 'cursor_field' -- django_strawberry_framework/types/base.py` returns `62ae8404` and `51421e54`; `git log --diff-filter=A -- django_strawberry_framework/keyset.py` returns exactly `51421e54` (2026-07-10, "feat(relay): keyset value-encoded cursors via Meta.cursor_field (idea #3 / BACKLOG-39)"). Post-ship, and it is BACKLOG item 39 sub-feature 3 by the commit's own subject line. |
| Sibling: `max_page_size` bounds a connection page | **Confirmed** | `django_strawberry_framework/resource_policy.py` #"max_page_size: int = 100", documented in the same class docstring as "Ceiling on a connection's effective ``relay_max_results``". Enforced through `django_strawberry_framework/utils/connections.py::resolve_relay_max_results` #"return effective_bound(policy_from_info(info).max_page_size, cap)", whose own comment states "The request policy is a CEILING over whichever cap won above, never a replacement for it: a connection can be narrower than the policy and can never be wider" and that the clamp is the seam **both** the plan-time walker and the resolve-time window read. Consumed at `django_strawberry_framework/connection.py` #"max_results = resolve_relay_max_results(info, max_results)", whose comment pins the ordering: resolved "once here, before any window or slicing path reads it", attributed in-source to spec-047. So the spec's "consumers raise it via `strawberry_config(relay_max_results=...)`" is **actively false** above the policy value. |
| spec-033 foreign citation | **Confirmed, and the CLAIM re-verified, not just the link** | `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` #"Revision 6 P2 established that nothing implements strictness for connections". The claim was checked against the target text rather than assumed: the companion's `### Changes this Decision underwent` under Decision 12 carries "**Revision 6 P2** - the strictness-mode claim described behavior nothing implements ... `connection.py` never consults the strictness sentinels, so the synthesized connection resolver's nested access is silent", and the companion's `## Revision history` entry names both sentinels literally (`DST_OPTIMIZER_STRICTNESS` / `DST_OPTIMIZER_PLANNED`), which is the spelling `spec-033` uses. The "assigned the wiring here" half is confirmed by spec-032's `## Non-goals`, which places strictness-mode interaction in `033`. |
| `.py` Revision-7 citations | **Confirmed, and both target contracts confirmed present in the spec** | `tests/test_relay_node_field.py` #"(spec-032 Revision 7 P1)" (the malformed-base64 parametrize comment) and #"Discriminating (spec-032 Revision 7 P2)" (a test docstring). Both re-cited as Decision citations only after reading the Decisions: `### Decision 4`'s **Argument spelling** bullet carries the `strawberry.ID`-not-`relay.GlobalID` contract with the `convert_argument` mechanism, and `### Decision 5`'s format-failure bullet carries "**Catch scope is narrow:** the `try` / `except ConfigurationError` -> convert wraps the `decode_global_id` call **only**" plus the `SyncMisuseError`-must-never-be-mislabeled rule. Contract citations survive a rationale move by construction, which is why this is the correct repair rather than a companion deep link. |
| `ItemType.properties` | **Confirmed nonexistent** | `examples/fakeshop/apps/products/models.py` #"related_name=\"properties\"" is on `Property.category = ForeignKey(Category, ...)`, so `properties` is a reverse FK on **`Category`**. `examples/fakeshop/apps/products/schema.py`'s `CategoryType.Meta` comment gets it right ("``properties`` deliberately stays on the default"); `ItemType.Meta.fields` carries no `properties` entry. Load-bearing beyond tidiness: Slice 2 wrote `CategoryType.properties` into the spec's Slice-6 checklist as the live proof of the connection-only default, so the two must agree. |
| `.py` `"both"`-default comments | **Confirmed — and the routed list of three was five** | See `### Beyond the handed list` item 1. |
| Decision 8's six diagnostics | **Confirmed message-for-message; no edit owed** | `django_strawberry_framework/types/base.py` #"_RELAY_NON_INTERFACE_HELPERS" read row by row against the spec's six numbered messages. `relay.GlobalID` -> "a scalar-like id wrapper, not an interface; Relay-Node-shaped types get `id: GlobalID!` automatically from `relay.Node`"; `relay.NodeID` -> "an annotation helper for custom id fields (`id: relay.NodeID[int]`), not an interface"; `relay.Connection` and `relay.ListConnection` -> the shared `_RELAY_CONNECTION_HELPER_DESCRIPTION`, matching the spec's "same remediation as `Connection`"; `relay.Edge` -> "a generic output type the connection machinery instantiates; not consumer-declarable"; `relay.PageInfo` -> "a generated pagination type; not an interface". `_RELAY_NON_INTERFACE_REMEDIATION` matches the spec's "what they probably meant (`relay.Node`)". The fires-first claim holds: the helper loop in `::_validate_interfaces` runs **before** `if not isinstance(entry, type)`, so the `typing.Annotated` `NodeID` is named. All six spec-named tests exist in `tests/types/test_base.py` (`test_interfaces_rejects_relay_globalid_named` through `..._pageinfo_named`). |
| Decision 9's always-concrete `_connection_type_for` | **Confirmed; no edit owed** | `django_strawberry_framework/connection.py::_connection_type_for` docstring opens "Always returns a generated concrete ``<TypeName>Connection`` subclass"; the non-`total_count` branch calls `_generate_connection_class(...)` rather than returning the alias, and its in-source comment reproduces the spec's mechanism ("handing the schema a generic ALIAS loses the package's ``resolve_connection`` override"), including the SDL-parity detail that the description is read from the parent's strawberry definition rather than copied as a literal. `_guard_first_and_last(first, last)` is called inside the override. |
| Decision 12's pre-`033` posture | **Confirmed as case (c), and its sibling deferral is case (a)** | `docs/SPECS/spec-033-connection_optimizer-0_0_9.md`'s header names spec-032's "Decision 12 pinned the pre-`033` posture this card retires", and its `Status:` line reads `**SHIPPED (0.0.9)**` with all seven slices final-accepted. Products: `examples/fakeshop/apps/products/schema.py::Query` is four `DjangoConnectionField`s (#"all_categories: DjangoConnection[CategoryType] = DjangoConnectionField(CategoryType)" and its three siblings), and `KANBAN.md` records `TODO-BETA-062-0.1.5` as re-scoped to "the `node` / `nodes` entry points plus the `totalCount` opt-in". |
| Decision 13 | **Confirmed; no edit owed** | Every claim is scoped to this card's diff ("No slice edits `pyproject.toml` ...") or to the joint cut, and none states a present-tense on-disk version outside the already-scoped header. |

### The citation census, closed as an anchor measurement

The brief's requirement was an **anchor** measurement, not a distance one: enumerate every occurrence of the
shortest distinctive token and classify each, rather than sampling the hits a citation-shaped phrase matches.

**Instrument.** A scratchpad classifier walks `docs/`, `django_strawberry_framework/`, `tests/`, `examples/`
and `scripts/`, finds every `spec-032` / `spec_032` occurrence, and classifies it on a +/-90-character window.
`.venv/` and `.git/` are outside the walk.

**The instrument was asserted against known-good and known-bad inputs before its numbers were believed, and
the fixtures found a real bug.** Eight fixtures, one per class plus the two near-misses:

```
$ uv run python <scratch>/fixture.py
FAIL want=A-contract           got=D-identity           :: (spec-032 Decisions 6/7): for every
fixtures: 7 / 8 pass
EXIT=2
```

The `Decision\s+\d+` pattern was blind to the **plural, slash-joined** spelling `Decisions 6/7`, which had
mis-filed a live `django_strawberry_framework/types/finalizer.py` citation as a bare identity mention. Widened
to `Decisions?\s+\d+`, all 8 pass and the contract class grows 100 -> 102. **Same failure as Slice 0's
`Revision N PN` miss, one order of magnitude smaller and one pass later:** a census's population is the id
plus *every spelling* of the citation grammar, and the only way to learn the spellings is to make the
classifier fail on one first.

```
$ uv run python <scratch>/fixture.py
ok   want=B-chronology         got=B-chronology         :: (spec-032 Revision 7 P1): a relay.GlobalID
ok   want=B-chronology         got=B-chronology         :: cites spec-032 Revision 6 P2 established that
ok   want=A-contract           got=A-contract           :: (spec-032 Decisions 6/7): for every
ok   want=A-contract           got=A-contract           :: per spec-032 Goal 2 the default
ok   want=C-prearchive-path    got=C-prearchive-path    :: ``docs/spec-032-full_relay-0_0_9.md`` Decision 11
ok   want=A-contract           got=A-contract           :: ``docs/SPECS/spec-032-full_relay-0_0_9.md`` Decision 11
ok   want=D-identity           got=D-identity           :: the bug spec-032 uncovered. The non-opted path
ok   want=D-identity           got=D-identity           :: # spec-032 - cursor-contract conformance
fixtures: 8 / 8 pass
EXIT=0
```

**Result: 369 occurrences across 54 files.**

| Class | Occurrences | Survives the rationale move? |
| --- | --- | --- |
| **A — contract citations** (`Decision N` / `Decisions N/M` / `Goal N` / `Edge cases` / `DoD` / `Non-goals` / `Slice N` / `Test plan`) | **102** | Yes, by construction — the Decisions and those sections stayed in the spec |
| **B — chronology citations** (`Revision N`, `P1`/`P2`/`P3`, `Q4`) | **12** | **No** — the text they cite moved to the companion |
| **C — pre-archive `docs/spec-032-…` path spellings** | **13** | Separate rot class; no gate sees it (the link *defs* resolve relatively) |
| **D — bare identity mentions** (filenames, link defs, `(spec-032)` provenance tags with no citation grammar) | **242** | Yes — nothing to break |

**Class B, all 12 occurrences, by owner:**

| Site | Occurrences | Disposition |
| --- | --- | --- |
| `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md` (lines 32, 364) | 2 | **Self-owned** — this file IS the revision history. No action. |
| `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` line 371 | 2 (one line: link text + ref-id) | **Repaired this slice** (task 2). |
| `tests/test_relay_node_field.py` (the parametrize comment, the `SyncMisuseError` docstring) | 2 | **Repaired this slice** (task 3). |
| `docs/builder/bld-032-slice-0-*.md`, `build-032-*.md`, `worker-memory/worker-1.md` | 6 | Per-cycle scratchpads describing the finding; `START.md` exempts them and they close with the cycle. No action. |

So the live population outside this cycle's own scratchpads is **four occurrences at three sites**, all now
repaired. One near-miss re-confirmed rather than inherited: `spec-033` line 410 matches a case-insensitive
`revision` grep but is `spec-033`'s **own** Revision 4, a self-reference. And `spec-033` line 420's
`Justification: the exact precedent [spec-032] Decision 13` is class A and needs nothing.

**The durable number is the ratio, not the count: a rationale move puts roughly 1% of a spec's inbound
references at risk.** That is why an eyeball pass over a 369-occurrence population is not a census, and why
the classification rather than the total is the deliverable a later reader can re-derive.

**Class C, all 13 occurrences.** Seven in the spec's own prose (repaired below), three in `.py` module
docstrings (repaired below), three in this cycle's scratchpads (no action).

### The pre-archive path spelling: a third rot class, wider than the routed list

`docs/SPECS/NEXT.md` Step 8 moved this spec to `docs/SPECS/` and re-pointed its reference-style link
**definitions**, which is why `[spec-032]` / `[spec-032-terms]` resolve today. Prose resolves against nothing,
so the stale spelling is invisible to every gate. Slice 1 routed what it called "five sites", which is **four distinct sites** with `## Definition of
done` item 1 counted as two; the measured population is **five sites / seven occurrences**:

| Site | Occurrences | On the routed list? |
| --- | --- | --- |
| `### Decision 1`, the "lives at" sentence | 1 | yes |
| `## Slice checklist`, Slice 7's KANBAN sub-bullet | 1 | yes |
| `## Doc updates`, the matching KANBAN card-wrap bullet | 1 | **no — missed** |
| `## Definition of done` item 1 | **3** (prose path, the `-terms.csv` companion, the `check_spec_glossary.py` invocation) | routed as "twice" - it is three |
| `## Definition of done` item 11 | 1 | yes |

Plus three `.py` module docstrings: `tests/test_relay_node_field.py`, `tests/test_relay_connection.py`,
`tests/testing/test_relay.py`.

**Measured tree-wide before editing, per the standing rule that a suspected convention violation is counted
before it is called rot:** across `django_strawberry_framework/`, `tests/`, `examples/` and `scripts/` there
are **26** correct `docs/SPECS/spec-<NNN>` spellings against **12** stale `docs/spec-<NNN>` ones, and the two
correct spellings sit in `django_strawberry_framework/relay.py` and `testing/relay.py` — the very modules
whose test mirrors carry the stale form. Rot, not house convention. The nine stale occurrences naming *other*
archived specs (018, 020, 023, 028, 030) are the same class with no owner in this cycle and are routed.

Decision 1's repair is the one that gained rather than lost text: the sentence now names the archived path,
the `appx/` companion location, the `NEXT.md` Step 8 sweep that performed the move, **and** the authoring
location as history. One `docs/spec-032-…` occurrence therefore survives in the spec by design — it is the
subject of a sentence about where the file *was*, not a claim about where it is.

### Spec sites changed, by content

**19 prose sites plus one link definition** - 4 for `Meta.cursor_field`, 4 for the `max_page_size`
ceiling, 6 for Decision 12 and the products deferral, 5 for the pre-archive path - named by what they say
rather than by line number, and grouped by finding. Two further sites were examined and deliberately left
standing; they are listed too, because an unedited site and an unexamined site are indistinguishable in a
diff. The count is enumerated here rather than read off `git diff --stat`: the spec has been dirty since
Slice 0, so its diff against `HEAD` (144 insertions / 228 deletions, 794 -> 710 lines) is the whole cycle's,
not this pass's.

**B4 — `Meta.cursor_field` shipped (4 sites, graded individually because they are not the same case)**

1. `## Edge cases and constraints`, the stale-`after` entry — **case (a)**, the brief's exemplar. "stable
   column-keyed cursors are BACKLOG item 39 sub-feature 3" is an unqualified present-tense claim about the
   package and is false. Rewritten so the *property* is attributed to the offset cursor rather than to the
   package, naming `Meta.cursor_field` / `keyset.py` as the shipped alternative and stating that this card
   neither ships nor exercises it.
2. `### Decision 9`, the closing line — **case (c)**, and the one the brief warns about. "`Meta.cursor_field`
   … stays out of scope **per the card**" is a statement about *this card's scope* and is still true;
   rewriting it into "the package has no keyset cursors" would replace a true claim with a false one. The
   scope subject is made explicit (`is outside this card's scope` … `this Decision ships no cursor code of
   any kind`) and the **placement** half — the part that actually rotted — is corrected beside it. A sentence
   was added recording *why* the shipping cost nothing here: the delegation this Decision chose is what made
   a second cursor vocabulary additive.
3. `## Non-goals`, the "Relay magic" bullet — **case (a) for one member only.** The bullet is a true
   statement of this card's scope, so it is kept; "The post-`1.0.0` differentiators … All live in BACKLOG
   item 39" is false for `Meta.cursor_field` alone. Rewritten to keep the list and the scope claim while
   naming that one member as shipped, with the shipped surface cited.
4. `## Out of scope (explicitly tracked elsewhere)` — same shape. `Meta.cursor_field` is lifted out of the
   item-39 enumeration and given its own clause distinguishing "no longer out of scope for the **package**"
   from "remains out of scope for **this card**".

**Graded case (c) and deliberately LEFT STANDING (2 sites).** Recorded because an unedited site and an
unexamined site are indistinguishable in a diff:

- `## Goals` goal 4 — "without asserting keyset-cursor stability the offset implementation deliberately
  defers". The subject is this card's conformance suite and the offset implementation. Both halves are true
  at `HEAD`: the suite asserts no keyset property, and the offset path still defers stability (keyset is an
  opt-in; a type with no `cursor_field` gets offset cursors byte-identically). Nothing to correct.
- `### Decision 9`'s stale-`after` bullet — "any other keyset-cursor property the implementation deliberately
  defers **to `Meta.cursor_field`**". This sentence reads *better* now than when written: it names the exact
  mechanism that does provide the property, which now exists. Editing it would be churn.

**Sibling check — `max_page_size` bounds a connection page (4 sites)**

5. `## Key glossary references`, the `strawberry_config` entry — "its `relay_max_results` passthrough is
   **the** knob that caps connection page sizes". The definite article makes the claim exclusive and it is
   now false. Rewritten as "the schema-side knob … and it is no longer the only bound", naming
   `ResourcePolicy.max_page_size` as a ceiling.
6. `### Decision 9`'s lead-in — `relay_max_results` "capping page sizes" gained "under the request policy's
   `max_page_size` ceiling" with a pointer to the Edge cases entry, so the Decision body does not state the
   cap without its bound.
7. `## Edge cases and constraints`, the `relay_max_results` entry — the materially false one. "consumers
   raise it via `strawberry_config(relay_max_results=...)`" is untrue above the policy value. **Retitled** so
   the ceiling is in the entry's own name (`**relay_max_results, under the policy's max_page_size ceiling**`)
   rather than buried in its body, and rewritten with the narrower-never-wider rule, the resolve-once-at-the
   -entry-seam ordering, and why that ordering makes plan-time and resolve-time windows agree.
8. `## Edge cases and constraints`, the `nodes(ids:)` entry — its "relay_max_results caps connection *pages*"
   clause is true but, read against the corrected entry above, invited the reader to conclude the policy
   governs the batch and not the page. Gained the ceiling parenthetical and the sentence stating the two
   policy fields are deliberately independent, so raising a page size never raises a batch size.

**Decision 12 — the pre-`033` posture and the products deferral (7 sites, 1 correction)**

9. `### Decision 12`, consequence (b) — the phrase "the products conversion stays at `TODO-BETA-062-0.1.5`,
   per the card's own deferral note" is replaced by the scope-only "is deferred out of this card's diff", and
   **the whole correction is written once** in a new paragraph beneath the three consequences: `033` shipped
   in the joint cut; the SQL-shape assertions, the strictness wiring and the cooperation seam are all
   discharged; the products conversion landed **with `033`**, not at `062`, because the gate this card named
   is exactly what `033` removed; `062` was re-scoped. It closes by telling the reader to read every
   "deferred to `062`" sentence in the spec against that paragraph — the deferral out of *this card* is true,
   the destination is not.
10. `## Non-goals`, the products bullet — destination corrected, scope claim kept, with the one-line reason
    ("the gate, not the calendar, decided the host").
11. `## Out of scope`, the products bullet — same, plus what `062` retains today.
12. `## Goals` goal 6 — "stays deferred to `TODO-BETA-062-0.1.5`" -> "stays out of this card", pointing at
    Decision 12 for where each deferred half landed.
13. `## Definition of done` item 9 — "Products activation remains untouched (`062`)" -> "remains untouched
    **by this card**", with the conversion's actual host named.
14. `## Slice checklist`, Slice 7's `TODAY.md` sub-bullet — "products is **not** activated (deferred to
    `062`)" -> "not activated by this card", naming the same-cut follow-on.
14a. `## Current state`'s products sentence was **not** rewritten. The section is explicitly "a true
    description of the repo as of this writing, before the build", the Slice 2 precedent, and the companion's
    Decision 12 note records that the file has since changed.

**Class C — the pre-archive path (5 sites / 7 occurrences, items 15-19 in this count)**

15-19. `### Decision 1`, `## Slice checklist` Slice 7, `## Doc updates`, `## Definition of done` item 1
    (three occurrences on one line) and item 11, all corrected as described above. The `[spec-032]` / `[spec-032-terms]` link definitions were
    **not** touched — they already resolve — and the inline uses were re-spelled to the short form the
    definition supplies, so no link changed target.

**Link definition:** `[keyset]` added under `<!-- django_strawberry_framework/ -->`, alphabetical between
`[finalizer]` and `[list-field]`, used at four sites. No `[glossary-...]` reference was created for
`Meta.cursor_field`: it has **no** `docs/GLOSSARY.md` heading (a known gap, already carded — see
`### Beyond the handed list` item 3), so inventing one would break the glossary gate.

### Deleted as never-true, or graded and left

- **Case (b), never true — none this slice.** Recorded explicitly because Slice 1 found one and an empty
  result reads like an unrun check otherwise. Every claim corrected here was correct at `0.0.9`.
- **Case (a), true then falsified by shipped code — 12 of the 16 sites.** No sentence was moved to the
  companion; the deliberation behind each is recorded there in the companion's own voice.
- **Case (c), true but since resolved — 4 sites made explicit, 2 left standing untouched**, both named above
  with the reason. Nothing was deleted: a card-scope statement survives the feature it scoped shipping.

### spec-033: the one citation repair

The sentence stops narrating spec-032's revision numbering and gains a reference-style pointer at the
**Decision-keyed** anchor, per Slice 0's recommendation (a Decision citation cannot rot in a future rationale
move; a `#revision-history` citation can):

- Before: `[`spec-032`][spec-032] Revision 6 P2 established that nothing implements strictness for connections — … — and assigned the wiring here.`
- After: `[`spec-032`][spec-032] established that nothing implements strictness for connections — … — and assigned the wiring here. Source-verified and recorded under [its Decision 12][spec-032-rationale-d12].`

One definition added, under the correct group header and alphabetically:

```
<!-- docs/SPECS/ -->
[spec-032]: spec-032-full_relay-0_0_9.md
[spec-032-rationale-d12]: appx/spec-032-full_relay-0_0_9-rationale.md#decision-12--sequencing-against-the-connection-aware-optimizer-and-the-library-first-activation
```

Base-then-suffixed matches this group's own existing ordering (`[spec-030]` before
`[spec-030-rationale-revisions]`; `[spec-031]` before `[spec-031-rationale-d11]`) and is plain alphabetical.
**Nothing else in `spec-033` was changed**, per the slice brief. The anchor was verified to exist and the
claim re-verified against the target text (evidence table above) before the link was pointed at it.

### `.py` sites changed, by content

Seven files, **comment and docstring text only**. Every one is proved unchanged in executable bytes in
Verification 5.

| File | Site | Change |
| --- | --- | --- |
| `tests/test_relay_node_field.py` | the malformed-base64 parametrize comment | `(spec-032 Revision 7 P1)` -> `(spec-032 Decision 4)` |
| `tests/test_relay_node_field.py` | `::test_node_sync_async_get_queryset_raises_sync_misuse` docstring | `Discriminating (spec-032 Revision 7 P2)` -> `(spec-032 Decision 5)` |
| `tests/test_relay_node_field.py` | module docstring | `docs/spec-032-…` -> `docs/SPECS/spec-032-…` |
| `tests/test_relay_connection.py` | module docstring | same path repair |
| `tests/testing/test_relay.py` | module docstring | same path repair |
| `tests/test_relay_connection.py` | the section banner above the three renamed default-shape tests | `# Default "both": connection siblings per eligible relation kind` -> `# Default "connection": the list sibling is dropped; "both" opts it back in` (Slice 2's routed text, verbatim) |
| `tests/types/test_base.py` | `::test_relation_shapes_on_consumer_annotated_relation_raises` docstring | `implicit ``"both"`` default` -> `implicit default … whatever that default's value is` — the rule is value-independent, the same fix applied to the spec's Decision 7 |
| `examples/fakeshop/test_query/test_library_api.py` | `::test_book_loans_relation_stays_list_only` docstring | `implicit ``"both"`` default` -> `implicit default`; the non-Node-target reason clause is correct and stays |
| `tests/test_relay_connection.py` | the `Shelf.books` cardinality-fixture banner **(beyond the routed list)** | "parametrized over the implicit ``"both"`` default and the narrowed ``"connection"`` shape" -> the keyless implicit default and an explicit `"connection"` key, stating that both arms resolve to the same shape and what the pair actually separates |
| `tests/test_relay_connection.py` | `::_shelf_books_connection_schema` docstring **(beyond the routed list)** | said `shape == "both"` "passes no `relation_shapes` key so the implicit default path is the thing tested" — true, but at `HEAD` that default is `"connection"`, so the arm named `"both"` produces no `"both"` shape. Restated to say so |
| `examples/fakeshop/test_query/test_products_api.py` | the nested-connection windowed-prefetch banner **(beyond the routed list)** | "the ``DONE-032-0.0.9`` implicit ``"both"`` default made it" -> the synthesis covers it, with the raw `items` list attributed to `CategoryType.Meta`'s explicit `{"items": "both"}` opt-in |
| `examples/fakeshop/apps/library/schema.py` | `BookType.Meta`'s explicit-opt-in comment | `ItemType.properties` -> `CategoryType.properties` (Slice 2's routed text) |

**Rule compliance, each checked rather than assumed.** No raw `path:NN` appears in any edit (`AGENTS.md`
rule 27); every source reference is a symbol path or a `spec-NNN Decision N` pointer, which is on the KEEP
list. **No process provenance was written** — no "corrected in the residual cycle", no "was Revision 7", no
commit ids; every replacement states the invariant. The two chronology markers were replaced by Decision
pointers rather than by dates. ASCII-only holds (`scripts/check_trailing_commas.py --check` exits 0 on all
seven, Verification 4). **No line carrying a rule-27 citation was reflowed** — the two citation edits are
in-place token substitutions inside their existing lines, so the wrapped-citation blind spot in
`check_citations.py` cannot have been opened by this pass; the checker's own count is quoted in
Verification 3.

### Beyond the handed list

**The handed list was a floor.** Five items surfaced that no prior slice carried.

1. **The routed `"both"`-default list of three was five.** Slice 2 routed `tests/test_relay_connection.py`'s
   section banner, `tests/types/test_base.py`'s docstring and `test_library_api.py`'s docstring. A sweep for
   the claim rather than for the routed sites found two more: `tests/test_relay_connection.py`'s
   `Shelf.books` fixture banner and `examples/fakeshop/test_query/test_products_api.py`'s nested-connection
   banner. Both taken here. The second is the more consequential — it tells a reader that `CategoryType.items`
   has an `itemsConnection` *because of the implicit default*, when the raw `items` list beside it exists only
   because of an explicit `{"items": "both"}` key three files away.
2. **A parametrize id is now degenerate, and it is not mine to fix.** `tests/test_relay_connection.py`
   `::_shelf_books_connection_schema` passes `relation_shapes` **only** when `shape == "connection"`, so the
   `["both", "connection"]` parametrization's `"both"` arm exercises the package default — which is
   `"connection"`. Both arms therefore resolve to the same shape. **This is not a code defect**: no assertion
   is false, the tests pass, and the two arms still separate default resolution from explicit lookup, which
   is real coverage. But the id `[both]` is a claim, and correcting it is an executable-byte edit this
   cycle's scope does not authorize (there is no code gap). The docstring and banner now state the truth;
   the id is **routed** with replacement text.
3. **`BACKLOG.md`'s `stable_cursor_field` entry still describes the shipped feature in the future tense — and
   it is ALREADY CARDED, so nothing is routed.** The `## Relay` entry's `**What we'd do**` heading reads
   "declarative stable cursors that survive inserts and deletes". Re-derived before routing, per the standing
   rule: `KANBAN.md` carries a bullet that already names this exact site ("A fourth site is stale in the same
   direction: `BACKLOG.md`'s `stable_cursor_field` entry still describes the feature in the future tense …
   although it shipped as item 39 sub-feature 3 in commit `51421e54`"), together with the missing
   `## Meta.cursor_field` glossary heading and the absent CHANGELOG entry, as one undecided
   does-it-owe-a-spec question. **A catalog is a claim; re-deriving it turned a would-be duplicate route into
   a confirmation.** No action, and none owed.
4. **`spec-033` carries a pre-existing dangling in-page anchor at five use sites.** Its `### Decision 9`
   heading is ``The `edges { node }` selection helpers consolidate into the walker``; every reference spells
   the anchor `#decision-9--the-edgesnode-selection-helpers-consolidate-into-the-walker`, collapsing the code
   span's braces *and* its spaces. GitHub drops the braces and turns each remaining space into a hyphen, so
   the resolving anchor is `#decision-9--the-edges--node--selection-helpers-consolidate-into-the-walker`.
   Found only because this pass's slugger was rebuilt to stop stripping code-span punctuation. **Five sites in
   a file this slice may touch for one citation repair only**, so it is routed with replacement text rather
   than fixed. It is the only anchor of this shape in `docs/` (measured).
5. **Nine stale `docs/spec-<NNN>` `.py` docstring paths belong to other specs** (018 x4, 020, 023, 028 x2,
   030). Same rot class as the three repaired here, no owner in this cycle. Routed.

### Verification

**1. Glossary gate — exits 0 on both specs, unchanged term counts.**

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-032-full_relay-0_0_9.md
OK: 40 terms - all have glossary entries and at least one spec link.
EXIT=0

$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-033-connection_optimizer-0_0_9.md
OK: 38 terms - all have glossary entries and at least one spec link.
EXIT=0
```

Same 40 terms Slices 0-2 measured; `spec-033`'s 38 are its own, unchanged by a one-sentence reword plus one
source-file link definition.

**2. Markdown scaffold gate — exits 0 on all three.**

```
$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-032-full_relay-0_0_9.md \
    docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md \
    docs/SPECS/spec-033-connection_optimizer-0_0_9.md
EXIT=0
```

**3. Citation checker — exits 0 tree-wide.**

```
$ uv run python scripts/check_citations.py
OK: 815 citations resolve (731 in 431 .py files, 84 in KANBAN.md).
EXIT=0
```

It accepts the `.py` paths this slice touched (it walks the whole tree). The wrapped-citation blind spot is
handled by construction rather than by luck: **no line containing a rule-27 citation was reflowed** — the two
Decision re-citations are in-place substitutions inside their existing lines.

**4. `.py` tool gates.**

```
$ uv run ruff format .
434 files left unchanged
$ uv run ruff check --fix .
All checks passed!
$ uv run python scripts/check_trailing_commas.py --check <the seven .py files>
EXIT=0
```

`434 files left unchanged` is the affirmative signal here rather than a no-op: the comment and docstring
rewrites already satisfy the formatter, so the formatter introduced no churn of its own on top of a
comment-only pass. No `pytest` was run, per `AGENTS.md` and the Worker 1 role file; no `--cov*` flag was used
anywhere in this pass.

**5. The inverse proof: executable bytes UNCHANGED, all seven files.**

HEAD copies were obtained read-only into a scratch path **outside the repo** —
`git show HEAD:<path> > <scratch>/head/<flattened-name>` for each of the seven — and all seven matched their
working-tree byte counts before editing, confirming a clean baseline with no concurrent writer. **No
`git stash`, `git checkout`, `git restore` or `git worktree` was used at any point.**

The instrument compares two things per file: `ast.dump(ast.parse(src))`, which carries no line numbers, and
`marshal.dumps(compile(tree, ..., optimize=2))` where every AST node's line and column is first **flattened
to 1**. `optimize=2` is CPython's own docstring stripper, so the second comparison is byte-identical iff the
executable content is identical.

**Two earlier versions of this instrument passed their controls and were wrong**, and the record matters more
than the result:

- **v1** marshalled the code object directly. It reported `*** EXECUTABLE BYTES DIFFER ***` for
  `tests/test_relay_connection.py` and `test_products_api.py` — because `co_firstlineno` and `co_linetable`
  shift when a comment or docstring adds a **line**. Its four controls had no line-shift case.
- **v2** skipped the `co_*` line fields and recursed into nested code objects. Still wrong. A recursive leaf
  diff showed every remaining difference was a bare integer, `head = work - 5`, exactly this pass's line
  delta: **Python 3.13 stores a class body's `__firstlineno__` as an ordinary integer CONSTANT inside the
  class-body code object.** Its controls had a line-shift case but no **class**, so it could not see it.
- **v3** flattens positions at the AST level before compiling, which normalizes both at once.

**STANDING: a control set with no line-shift case and no class definition cannot see either of the two ways a
comment-only edit moves the compiled bytes** — and each version's controls passed at the moment its author
believed them. The final control set is ten, three of them deliberate mutations that MUST fail:

```
$ uv run python <scratch>/inverse.py <seven head::work pairs>
ok   unchanged                                    code_same=True  ast_same=True  moved=[]
ok   comment appended (no line shift)             code_same=True  ast_same=True  moved=[]
ok   comment INSERTED before a class (line shift) code_same=True  ast_same=True  moved=[]
ok   docstring reworded, same line count          code_same=True  ast_same=False moved=['f']
ok   docstring reworded AND line count grew       code_same=True  ast_same=False moved=['f']
ok   class docstring reworded and grew            code_same=True  ast_same=False moved=['C']
ok   MUTATED statement                            code_same=False ast_same=False moved=[]
ok   MUTATED constant only                        code_same=False ast_same=False moved=[]
ok   MUTATED class attribute                      code_same=False ast_same=False moved=[]
ok   MUTATED name only                            code_same=False ast_same=False moved=['f', 'g']
controls: 10/10 pass

tests/test_relay_node_field.py
  line-flattened optimize=2 code object identical: True   -> EXECUTABLE BYTES UNCHANGED
  ast.dump identical: False   -> docstring-only (2 reworded)
    docstring reworded: <module>
    docstring reworded: test_node_sync_async_get_queryset_raises_sync_misuse
tests/test_relay_connection.py
  line-flattened optimize=2 code object identical: True   -> EXECUTABLE BYTES UNCHANGED
  ast.dump identical: False   -> docstring-only (2 reworded)
    docstring reworded: <module>
    docstring reworded: _shelf_books_connection_schema
tests/types/test_base.py
  line-flattened optimize=2 code object identical: True   -> EXECUTABLE BYTES UNCHANGED
  ast.dump identical: False   -> docstring-only (1 reworded)
    docstring reworded: test_relation_shapes_on_consumer_annotated_relation_raises
tests/testing/test_relay.py
  line-flattened optimize=2 code object identical: True   -> EXECUTABLE BYTES UNCHANGED
  ast.dump identical: False   -> docstring-only (1 reworded)
    docstring reworded: <module>
examples/fakeshop/test_query/test_library_api.py
  line-flattened optimize=2 code object identical: True   -> EXECUTABLE BYTES UNCHANGED
  ast.dump identical: False   -> docstring-only (1 reworded)
    docstring reworded: test_book_loans_relation_stays_list_only
examples/fakeshop/test_query/test_products_api.py
  line-flattened optimize=2 code object identical: True   -> EXECUTABLE BYTES UNCHANGED
  ast.dump identical: True   -> comment-only (AST identical)
examples/fakeshop/apps/library/schema.py
  line-flattened optimize=2 code object identical: True   -> EXECUTABLE BYTES UNCHANGED
  ast.dump identical: True   -> comment-only (AST identical)
EXIT=0
```

Two files show `ast.dump identical: True`, which is the stronger statement — the AST carries docstrings, so
identical means **only `#` comments moved**. The other five are docstring-only, and each names the exact
docstrings that were reworded, keyed by dotted path rather than by line number (keying by line number is what
made v1's report list 131 spurious "changed" docstrings).

**6. Anchors, link definitions, and the definition block — checked mechanically on all three files.**

```
$ uv run python <scratch>/anchorcheck.py \
    docs/SPECS/spec-032-full_relay-0_0_9.md \
    docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md \
    docs/SPECS/spec-033-connection_optimizer-0_0_9.md
slugger fixtures: 10/10 pass

=== docs/SPECS/spec-032-full_relay-0_0_9.md: 0 problem(s)

=== docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md: 0 problem(s)

=== docs/SPECS/spec-033-connection_optimizer-0_0_9.md: 1 problem(s)
  - dangling in-page anchor #decision-9--the-edgesnode-selection-helpers-consolidate-into-the-walker
EXIT=1
```

The single remaining problem is **pre-existing and routed** (`### Beyond the handed list` item 4), not
introduced here: it was present before this slice's edits and lives in a file the brief scopes to one
citation repair.

| Check | `spec-032` | `…-rationale.md` | `spec-033` |
| --- | --- | --- | --- |
| Dangling in-page `](#...)` anchors | none | none | 1 pre-existing (routed) |
| Duplicate link definitions | none | none | none |
| `[ref-id]` uses with no definition | none | none | none |
| Definitions never used | none | none | none |
| Definition paths missing on disk | none | none | none |
| Definition cross-file anchors missing | none | none | none |
| `<!-- LINK DEFINITIONS -->` present | yes | yes | yes |
| All 10 canonical group headers, in `START.md` order | yes | yes | yes |

**The slugger's own fixtures caught two real bugs before any count was believed.** The em-dash trap is
handled the way Slices 0-2 learned to handle it — each whitespace character is slugged **individually**, never
`re.sub(r'\s+', '-', ...)`, because GitHub turns ` — ` into **two** hyphens once the em-dash is dropped. Two
further bugs were new to this pass and would each have produced a false clean run somewhere else:

- **Underscores were being stripped with the emphasis markers.** `## strawberry_config` slugged to
  `strawberryconfig`, so the checker reported `[glossary-strawberry_config]` as a **missing anchor** in three
  files Slices 0-2 had passed clean. GFM disables intraword underscore emphasis, so only a
  boundary-delimited `_` run is emphasis. Fixed, with `## strawberry_config`, `## RELAY_GLOBALID_STRATEGY`
  and ``## `Meta.globalid_strategy` `` added as fixtures.
- **Code-span content was being unwrapped BEFORE emphasis stripping**, so an underscore inside
  ``Meta.relation_shapes`` was eaten as emphasis. Code spans are now stashed behind a placeholder first.

The script `sys.exit(2)`s on any fixture mismatch rather than reporting zero problems, so a broken slugger
cannot present itself as a clean file.

**The control was proved failable, not merely observed passing.** A copy of the spec outside the repo was
mutated four ways and every mutation was reported by name before the run exited 1:

| Mutation | Reported as |
| --- | --- |
| an in-page anchor pointed at a nonexistent heading | `dangling in-page anchor #decision-12--NOPE` |
| the new `[keyset]` definition retargeted at a nonexistent path | `definition [keyset] -> missing path ../../django_strawberry_framework/NOPE.py` |
| the `<!-- .venv/ -->` group header deleted | `group headers wrong/missing: [… no '<!-- .venv/ -->' …]` |
| a **cross-file** definition anchor broken (`#decision-9--` -> `#decision-99--`) | `definition [rationale-d9] -> missing anchor #decision-99--… in appx/…-rationale.md` |

That run also emitted ~83 additional `missing path` failures, which are an **artifact of the copy's location**
(every relative definition resolves outside the repo from a scratch tree), not findings — named here because
an unexplained count difference between the clean run and the failability run is exactly how an instrument
bug gets read as a finding. The scratch tree was deleted after the proof.

**7. Byte counts.**

| File | Before this slice | After | Delta |
| --- | --- | --- | --- |
| `docs/SPECS/spec-032-full_relay-0_0_9.md` | **165,828** / 707 lines | **170,612** / 710 lines | `+4,784` |
| `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md` | **97,055** / 455 lines | **108,497** / 471 lines | `+11,442` |
| `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` | **173,810** | **174,040** | `+230` |
| `tests/test_relay_node_field.py` | 54,637 | **54,637** | `0` |
| `tests/test_relay_connection.py` | 122,916 | **123,238** | `+322` |
| `tests/types/test_base.py` | 91,949 | **91,972** | `+23` |
| `tests/testing/test_relay.py` | 12,780 | **12,786** | `+6` |
| `examples/fakeshop/apps/library/schema.py` | 64,505 | **64,509** | `+4` |
| `examples/fakeshop/test_query/test_library_api.py` | 358,521 | **358,510** | `-11` |
| `examples/fakeshop/test_query/test_products_api.py` | 182,197 | **182,332** | `+135` |

`tests/test_relay_node_field.py` at a **zero** delta is a coincidence worth naming rather than reading as an
unedited file: two `Revision 7 PN` -> `Decision N` substitutions save 3 bytes each and the `docs/` ->
`docs/SPECS/` path repair costs 6. `git status --short` lists it as modified and the inverse proof reports two
reworded docstrings, so the file did change. **A byte count is not a change detector.**

The companion outgrowing the spec 2.4:1 continues Slice 2's pattern and for the same reason: three of this
slice's four findings are cases where a prediction was falsified or a destination was wrong, and recording
*why* a correct prediction failed costs more prose than stating the corrected contract.

**8. Working tree.** `git status --short` after the pass:

```
 M docs/SPECS/spec-032-full_relay-0_0_9.md
 M docs/SPECS/spec-033-connection_optimizer-0_0_9.md
 M examples/fakeshop/apps/library/schema.py
 M examples/fakeshop/test_query/test_library_api.py
 M examples/fakeshop/test_query/test_products_api.py
 M tests/test_relay_connection.py
 M tests/test_relay_node_field.py
 M tests/testing/test_relay.py
 M tests/types/test_base.py
?? 0_0_14.md
?? docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md
?? docs/builder/bld-032-slice-0-rationale_extraction.md
?? docs/builder/bld-032-slice-1-root_field_surface.md
?? docs/builder/bld-032-slice-2-relation_shapes.md
?? docs/builder/build-032-full_relay-0_0_9.md
```

Exactly the nine in-scope paths this slice writes, plus this cycle's prior artifacts and Worker 0's build plan
(all still untracked), plus the maintainer's concurrent untracked `0_0_14.md`, which was neither read as
instruction nor touched. This artifact is the tenth in-scope path and appears once written. **No closeout or
agentflow doc was edited** — `KANBAN.md`, `docs/GLOSSARY.md`, `CHANGELOG.md`, `TODAY.md`, `README.md`,
`GOAL.md`, `docs/TREE.md`, `docs/README.md`, `BACKLOG.md` and `examples/fakeshop/db.sqlite3` are all absent
from the list. No sibling spec beyond the single authorized `spec-033` line was touched, and
`spec-032-full_relay-0_0_9-terms.csv` is unchanged. Nothing was reverted.

### Companion appends (this pass)

Six bullets and two paragraphs, all appends — no existing companion text was rewritten (the file is
append-only during the cycle):

- **Decision 9**, `### Changes this Decision underwent` — two `**Post-ship:**` bullets. One for
  `Meta.cursor_field` shipping, carrying the point that **nothing here was reopened**: the Decision's content
  is *delegate, and pin the conformance contract instead of the bytes*, and a delegation is precisely what
  makes a second cursor vocabulary additive rather than a rewrite. It states the three-case grading in both
  directions and names which sentences were (c) and which were (a), because getting that backwards is the
  live hazard. One for the `max_page_size` ceiling, recording the ordering (resolved once at the entry seam
  so plan-time and resolve-time windows agree) and why `max_page_size` and `max_node_ids` are deliberately
  independent fields.
- **Decision 12** — two `**Post-ship:**` bullets. One records the pre-`033` posture as fully discharged and
  names the case-(c) trap in both directions: deleting the scope clauses erases a correct record, leaving
  them bare invites the reader to think the gap is open, and the fix is one added paragraph rather than a
  rewrite. One records that the products conversion did not land where the Decision sent it, with the
  generalizable lesson: **when a deferral is justified by a condition, record the condition as the
  destination; a card id is a guess about who will satisfy it.**
- **Risks and open questions** — two `**Item N ...**` paragraphs. Item 4 (cursor byte-format wording) is the
  **only item in the list a later release confirmed rather than falsified**, and the note says why: an item
  that reasons about the *property* survives where one that reasons about *who will decide* does not — the
  exact inverse of the items 7 and 9 lesson Slices 1 and 2 recorded. Item 5's "no released version carries
  the gap" is graded case (c) and its unpredicted half named.
- **Non-Decision deliberation** — two bullets closing the foreign-citation census: the full classified count
  with the ~1% at-risk ratio and the plural-`Decisions` classifier bug, and the pre-archive path spelling
  written up as a **third rot class** with its measured population and the 26-vs-12 tree-wide count that
  proves it rot rather than convention.
- **Link definitions** — six added to the companion (`[spec-032-key-glossary]`, `[spec-032-out-of-scope]`,
  `[spec-032-slice-checklist]` under `<!-- docs/SPECS/ -->`; `[base]`, `[keyset]`, `[resource-policy]` under
  `<!-- django_strawberry_framework/ -->`), all used, all alphabetical within their group.

### Notes for Worker 1 (spec reconciliation)

1. **`spec-033`'s `### Decision 9` in-page anchor is dangling at five use sites. Named owner: the final
   gate's `### Deferred work catalog`**, as a maintainer follow-up — the brief scopes this cycle to **one**
   citation repair in that file, and a five-site anchor sweep is not it. Replacement text recorded so it
   cannot be lost: replace every
   `#decision-9--the-edgesnode-selection-helpers-consolidate-into-the-walker` with
   `#decision-9--the-edges--node--selection-helpers-consolidate-into-the-walker`. Sites: the `Status:` line,
   the `## Slice checklist` Slice-1 entry, the `## Current state` selection-unwrap bullet, the
   `### Decision 11`'s build-proper source bullet, and `## Definition of done` item 2. The heading itself is correct
   and must not be changed — GitHub drops the code span's braces and hyphenates each remaining space, so the
   double hyphens are the resolving form. Verified to be the only anchor of this shape under `docs/`.
2. **Nine `docs/spec-<NNN>` pre-archive path spellings in `.py` docstrings name other archived specs. Named
   owner: the final gate's `### Deferred work catalog`.** Sites by spec: `018` x4, `020`, `023`, `028` x2,
   `030`. Replacement is mechanical — insert `SPECS/` after `docs/`. Recorded with the measurement that makes
   it a defect rather than a style call: the tree already carries **26** correct `docs/SPECS/spec-<NNN>`
   spellings against these **12** stale ones (three of which this slice repaired), so the correct form is the
   convention.
3. **A parametrize id in `tests/test_relay_connection.py` is degenerate. Named owner: the final gate's
   `### Deferred work catalog`.** `::_shelf_books_connection_schema` supplies `relation_shapes` only for
   `shape == "connection"`, so the `["both", "connection"]` parametrization's `"both"` arm exercises the
   package default, which has been `"connection"` since `567cc6d0`. Both arms resolve to the same shape.
   **Not a code defect** — every assertion still holds and the pair still separates default resolution from
   explicit lookup — but the id reads as coverage of a `"both"` shape that no longer exists there, and fixing
   it changes executable bytes, which this cycle authorizes only on a code-gap finding. Suggested
   replacement: rename the arm `"default"` (`@pytest.mark.parametrize("shape", ["default", "connection"])`
   with the builder's condition inverted to `if shape == "connection"`), or add a third arm passing an
   explicit `{"books": "both"}` so the matrix regains a genuine `"both"` run. The docstring and section
   banner now state the truth, so the misreading is contained meanwhile.
4. **`BACKLOG.md`'s `stable_cursor_field` entry is stale but ALREADY CARDED — deliberately NOT routed.** Its
   `**What we'd do**` heading still reads "declarative stable cursors that survive inserts and deletes" for a
   feature that shipped at `51421e54`. `KANBAN.md` already carries this exact site, by name, inside the
   undecided "where is the shipped keyset feature documented" bullet, alongside the missing
   `## Meta.cursor_field` glossary heading and the absent CHANGELOG entry. Recorded here only so the next
   reader does not re-route it. `BACKLOG.md` is not on this slice's writable list in any case.
5. **The `docs/GLOSSARY.md` gap for `Meta.cursor_field` is why this slice's cursor edits link to source, not
   to the glossary.** There is no `## Meta.cursor_field` heading, so a `[glossary-...]` reference would fail
   `check_spec_glossary.py`. The four new citations point at `types/base.py` and `keyset.py` instead. Same
   already-carded item as note 4; no action.
6. **No code defect was found.** Every finding re-verified as *spec* or *comment* staleness, never a skipped
   or dropped contract, so the escalation path in the slice brief was not taken and `Status: final-accepted`
   is set.

### Test additions / updates

None. This slice adds no source and no test, and runs no `pytest` per `AGENTS.md`. The `.py` files it touches
change comment and docstring text only, proved mechanically in Verification 5. Every spec-named test in
`## Test plan` Slices 1, 4 and 6 was swept for existence by `grep -rn "def <name>\b" --include="*.py"`, one
search per name, and all **28** are present at `HEAD`, each matching exactly once (the six named-helper rejections plus the two
re-affirmation pins; the live Slice-4 matrix including the three shipped `spec-030`-era tests the spec maps
rather than duplicates; `test_relay_max_results_cap`; and all eleven Slice-6 library tests). No spec-named
test was invented and none needed re-pointing this slice — Slices 1 and 2 had already re-pointed the two
renamed families.

### Spec slice checklist (verbatim)

Not applicable. This cycle's Slice 3 is a reconciliation slice defined by the build plan, not an entry in the
spec's own `## Slice checklist` (which carries the seven shipped build slices 1-7). There are no verbatim
sub-checks to copy, tick, or audit. Recorded explicitly rather than omitted, so the absence reads as a
decision.

### Implementation discretion items

None. Every choice in a spec-custody pass is the custodian's; nothing was delegated.

### Summary

The cross-spec residue of `spec-032` is closed. Four findings re-verified against `HEAD` before any edit; all
confirm, **no code defect**. `Meta.cursor_field` shipped at `51421e54`, and the four spec sites deferring it
were graded individually rather than swept: two are **case (a)** placement claims now false and rewritten, two
are **case (c)** card-scope claims made explicit and kept, and two further sites were examined and
**deliberately left standing** because editing them would have been churn — the failure mode the brief names,
flipping a true card-scope statement into a false claim that the package lacks keyset cursors, was avoided by
grading each sentence's subject rather than its vocabulary. The sibling check confirmed
`ResourcePolicy.max_page_size` is a ceiling over a connection's effective `relay_max_results`, falsifying the
spec's "consumers raise it via `strawberry_config(...)`" at four sites. Decision 12's pre-`033` posture is
**case (c) throughout and stands**, with one added paragraph recording that `033` shipped and discharged all
three consequences — and that the products conversion landed with `033` rather than at `TODO-BETA-062-0.1.5`,
because the Decision had recorded a *gate* and named a *card*; the gate held exactly and the schedule rotted.
The census closed as an anchor measurement: **369 `spec-032` occurrences across 54 files — 102 contract, 12
chronology, 13 pre-archive path, 242 bare identity** — leaving four live chronology occurrences at three
sites, all repaired, and putting the at-risk fraction of a rationale move at roughly **1%**. `spec-033`'s one
foreign citation is re-pointed at the companion's Decision-keyed anchor after the anchor was verified to exist
**and the claim re-verified against the target text**. Seven `.py` files took comment/docstring repairs,
including **two `"both"`-default sites and one degenerate parametrize the routed list of three did not carry**
— and every one carries a mechanical inverse proof that its executable bytes are unchanged, on an instrument
whose first two versions passed their own controls while being blind to line shifts and to Python 3.13's
class-body `__firstlineno__` constant. Four items are routed onward with replacement text and named owners;
one candidate route was withdrawn after re-derivation showed `KANBAN.md` already carries it. Spec 165,828 ->
170,612 bytes; companion 97,055 -> 108,497; `spec-033` +230. All gates exit 0, both mechanical controls were
proved failable by deliberate mutation, and no closeout or agentflow doc was touched.

### Spec changes made (Worker 1 only)

All within `docs/SPECS/spec-032-full_relay-0_0_9.md`, its companion
`docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md`, and the single authorized line in
`docs/SPECS/spec-033-connection_optimizer-0_0_9.md`, all triggered by this cycle's Slice 3. Sites are named by
content per `AGENTS.md`; the per-finding breakdown is in `### Spec sites changed, by content` above and is not
repeated here.

1. **B4 (`Meta.cursor_field` shipped)** — 4 spec sites, 2 more examined and left. Reason: the feature is in
   `ALLOWED_META_KEYS` with its own subsystem module, so every sentence placing it on the BACKLOG as unshipped
   is false about the package; the sentences placing it outside *this card* remain true and were kept.
2. **`max_page_size` ceiling** — 4 spec sites, one of them retitled. Reason: `relay_max_results` is no longer
   the only page bound, and the spec's advice to raise it via `strawberry_config` is inoperative above the
   policy value.
3. **Decision 12 / the products deferral** — 7 spec sites, 1 substantive correction written once in the
   normative home with 6 scope qualifiers pointing at it. Reason: `033` shipped and discharged the posture,
   and the conversion landed with `033` rather than at the card the deferral named.
4. **Pre-archive path spelling** — 6 spec sites / 7 occurrences. Reason: the spec lives at `docs/SPECS/`;
   the link definitions resolve relatively so no gate sees the prose drift. Slice 1 routed five sites and the
   measured population was six.
5. **Link definition** — `[keyset]` added, used at four sites, alphabetical.
6. **`spec-033`** — one sentence reworded to stop citing spec-032's revision numbering, plus one link
   definition (`[spec-032-rationale-d12]`). Nothing else in that file was changed.
7. **Companion** — six append-only bullets under Decisions 9 and 12 and `## Non-Decision deliberation`, two
   `**Item N ...**` paragraphs under `## Risks and open questions`, and five link definitions. No existing
   companion text was rewritten.
8. **Status-line re-verification** — no edit owed; the check ran and is recorded above.

No source or test file was edited beyond comment and docstring text, proved mechanically. No sibling spec
beyond the single authorized `spec-033` line was edited. No closeout or agentflow doc was edited.

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
