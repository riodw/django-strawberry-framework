# Build: Review round 1, Cohort A — spec reconciliation + rationale extraction (spec-043)

Spec reference: `docs/SPECS/spec-043-test_client-0_0_14.md` (archived; `Status:` line 72)
Build plan: `docs/builder/build-043-test_client-0_0_14.md` (`## Verified finding list`, F1-F8)
Companion authored: `docs/SPECS/appx/spec-043-test_client-0_0_14-rationale.md`
Status: final-accepted

## Plan (Worker 1)

### Recovery context — a prior subagent of this role died mid-run

A prior Worker 1 subagent began **this same pass** and died on a network error; this
artifact records one pass, not two (`BUILD.md` `### Recovery from interrupted subagent
runs` — the on-disk diff is authoritative, no `pass 2` suffix, no second artifact).
Re-derived at pickup rather than accepted from the dispatch note, the state on disk was:

- **Landed by the prior pass:** the rationale companion existed (756 lines, ~50KB) with
  its full section skeleton; the spec's inline `Revision history` and
  `Alternatives considered` blocks were gone (both greps 0); Decisions 1-12 each carried
  a one-line rationale pointer; Decision 9 had been rewritten around the recursive walker;
  Decision 5 carried `_finish_response` and the `is not None` transport selection;
  Decision 7 carried the accessor's `__test__ = False`. Spec 153,065 -> 137,129 bytes.
- **Not landed:** F5 (one false guard string plus a second stale site the dispatch did
  not name), F6 (5 of 7 stale floor mentions), F7 (no scenario 15 existed at all), the
  `D5` helper-reuse item Decision 9 already cited, ten surviving `Revision 3` provenance
  mentions, **15 undefined link references** (every `[rationale*]` pointer the prior pass
  introduced, plus `[build]` and `[exceptions]`), and a **failing**
  `check_spec_glossary.py`.
- **Empty:** `docs/builder/worker-memory/043-worker-1.md`. **Absent:** this artifact.

Two of those were self-falsifying instruments worth naming, because the same shape will
recur:

1. **The dispatch's F3 table read "`list, tuple` returns 0 and `unreadable` returns 0"
   and concluded two behaviour families were unlanded.** Both were already in the spec,
   spelled as prose — "**both lists and tuples**" and "an **array whose length cannot be
   read**". The grep sampled the *code's* vocabulary against a *prose* population
   (`BUILD.md` `## Claims are proven mechanically`: a long grep phrase samples a claim's
   vocabulary rather than establishing its population). F3 needed no new behaviour text.
2. **The dispatch recorded `check_spec_glossary.py` as returning `OK: 22 terms` — its
   pre-flight reading, taken before the prior pass ran.** Re-run at pickup it **failed**:
   moving Decision 3's rejected alternatives to the rationale took the only spec links to
   `DjangoType` and `DjangoConnectionField` with them, stranding two required CSV terms. A
   gate reading that predates the edit is not a reading of the edit.

### Dispatched findings checklist

Carried from `docs/builder/build-043-test_client-0_0_14.md` `## Verified finding list`,
one box per finding, quoted as the plan states it. A box is `- [x]` only where the fix is
on disk at the close of this pass and was re-derived here, never accepted from the
dispatch table.

- [x] **F1 — the `-rationale.md` companion does not exist.** "`docs/SPECS/appx/` carries
      `spec-043-test_client-0_0_14-terms.csv` and **no** `-rationale.md`. … Cohort A
      performs the move retroactively per `BUILD.md` `## Spec rationale extraction` — a
      cut-and-paste, not a copy: text that lands in the rationale **leaves** the spec."
      Landed by the prior pass; audited and extended this pass (see
      `### Rationale audit against the keyed-to-the-spec rule`).
- [x] **F2 — the spec narrates its own history in three inline revisions.**
      "`docs/SPECS/spec-043-test_client-0_0_14.md` #"Revision history (kept inline so the
      spec is self-contained)" runs Revisions 1-3 (≈130 lines …). … the spec must read as
      a clean current contract with no chronology to apply." The block was gone at
      pickup; this pass removed the **ten surviving `Revision 3` / `Revision 3 F<n>`
      attributions** scattered through the Slice checklist, Decision 11, the
      implementation table, four Test-plan scenarios and three DoD rows — review-round
      numbering is banned from standing prose by `START.md` "No process provenance in code
      or standing prose", and the spec's own header already promises the revision names
      live "nowhere here".
- [x] **F3 — six post-ship code changes to `testing/client.py` are absent from the spec.**
      "Seven commits touched `django_strawberry_framework/testing/client.py` after the
      card's own two … Cohort A folds each into the **Decision that owns it** as
      present-tense contract, and records what changed and why in the rationale." All six
      families verified present against `git diff 653a3841..HEAD` and the current source;
      see `### F3 re-derivation, family by family`. This pass added the missing **D5**
      helper-reuse item for family 3, which Decision 9 already cited by name
      (`## Helper-reuse obligations (DRY)` D5) against a list that had no D5 in it.
- [x] **F4 — `conf.py::testing_endpoint_setting.__test__ = False` is absent from the
      spec.** "The spec names the `__test__ = False` guard in **nine** places, all of them
      on the *class* … none covers the **module-level accessor** … Decision 7 is the
      owning Decision." Present in Decision 7 at pickup; this pass added the matching
      `## Edge cases and constraints` bullet, which the rationale's F4 entry already
      claimed as a second home.
- [x] **F5 — Decision 9 and `## Error shapes` describe a guard the code does not have.**
      "`## Error shapes` says the guard is
      `if files is not None and variables is None: raise AssertionError(...)`. The shipped
      code is `if not files: return body` followed by `if not variables: raise
      AssertionError(...)` — **truthiness on both**. … the **spec text is the defect**."
      Both halves landed this pass; the second, unnamed site is recorded below.
- [x] **F6 — the Strawberry floor the spec names disagrees with `BUILD.md`.** "the spec's
      Slice-1 checklist names `strawberry-graphql==0.262.0` as 'the package's pinned
      floor' … Cohort A corrects the spec's text to name the source rather than restating
      a number that moves." All five survivors rewritten; `grep -c '0\.262\.0'` is now 0
      against 7 at HEAD.
- [x] **F7 — post-ship test-tier additions are absent from the spec's Test plan.** "The
      spec's `## Test plan` numbers scenarios 1-14 and its coverage paragraph claims every
      branch has a named owner; the branches F3 introduced … have owners in the suite but
      **no scenario number**. Cohort A extends the Test plan so the claim stays true."
      Scenario 15 added, naming only rows that exist in the suite; the coverage paragraph
      re-pointed at it.
- [x] **F8 — the spec's own slice checklist and DoD are the completion claim.** "**This is
      not a defect and no cohort ticks them.** … Cohort A's only obligation here is to
      confirm the `Status:` line still reads COMPLETE and still matches the tree after its
      edits." Nothing ticked; `Status:` line 72 is byte-identical to HEAD and reads
      COMPLETE.

---

## Final verification (Worker 1)

### F3 re-derivation, family by family

Source of truth: `git diff 653a3841 HEAD -- django_strawberry_framework/testing/client.py`
plus the current module read end to end. Each family is matched to the spec text that now
states it as present-tense contract — by content, never by the commit's own vocabulary.

| # | Family (commit) | Spec home at close |
| --- | --- | --- |
| 1 | `TestClient._finish_response` extracted (`8bac47be`) | Decision 5, `django_strawberry_framework/testing/client.py::TestClient._finish_response` named in full, with the "factors BELOW the not-calling-`super().query()` decision" qualifier |
| 2 | falsy consumer-supplied client honored (`f7fbead4`) | Decision 5, "honored by identity, never by truthiness", naming `client or Client()` as the fail-open shape the contract forbids |
| 3 | diagnostics through `_safe_arg_repr` (`f7fbead4`) | Decision 9 closing paragraph **and** the new `## Helper-reuse obligations (DRY)` **D5** |
| 4 | tuple variables walked as arrays (`a8f31a2d`) | Decision 9, "`json.dumps` renders dicts as JSON objects and **both lists and tuples** as JSON arrays" — already present at pickup under a prose spelling the dispatch's grep could not see |
| 5 | empty-dotted-segment + unreadable-`__len__` guards (`a8f31a2d`) | Decision 9's five-branch rejection list, bullets 1 and 3 — likewise already present |
| 6 | canonical object-path index validation (`b4d0c8ae`) | Decision 9's five-branch rejection list, bullet 2, carrying the `isdigit()`-vs-`int()` domain reason |

### F5 — the second site the dispatch did not name

The dispatch named two disagreements. Re-reading
`django_strawberry_framework/testing/client.py::TestClient._build_body` against the whole
spec found the false `variables=None` framing in **two** places, not one: `## Error shapes`
(the quoted `files is not None and variables is None` string) and a second, separately
worded `## Edge cases and constraints` bullet — "guards this with an explicit
`raise AssertionError` when `files` is passed with `variables=None`". Fixing only the
quoted string would have been the partial-claim-fix residual `START.md` catalogues. Both
now state truthiness at both ends (`files={}` posts JSON; `variables={}` raises) and both
name `TestClient._assert_file_placeholders` as the enforcer of the placeholder contract,
so neither can be read as "one guard covers it".

### Work landed beyond the dispatched list

Each of these is a defect the dispatch did not enumerate, found by re-deriving rather than
by reading the table. None is new scope: every one is a consequence of the rationale move
that F1/F2 performed.

- **15 undefined reference-style links in the spec.** The prior pass introduced
  `[rationale]`, `[rationale-d1]`…`[rationale-d12]`, `[build]` and `[exceptions]` as uses
  with **no definitions at all** — `AGENTS.md` rule 28's "every `][label]` has a def".
  Added, `[rationale*]` under `<!-- docs/SPECS/ -->` (alphabetical), `[build]` under
  `<!-- docs/builder/ -->` which was empty, `[exceptions]` under
  `<!-- django_strawberry_framework/ -->`. Every one disk-exists-checked and every
  cross-file anchor checked against the target file's real headings, not assumed.
- **`check_spec_glossary.py` was failing.** Decision 3's moved alternatives were the only
  carrier of the `DjangoType` / `DjangoConnectionField` links their terms-CSV rows require.
  Fixed at the contract level rather than by re-importing deliberation: Decision 3 now
  states the `Django*`-prefix rule normatively (the prefix marks schema-side public API;
  test utilities are namespaced by import path, so `DjangoTestClient` is out of contract),
  which is instruction rather than deliberation and is where both links belong. The
  rationale's Decision 3 entry gained a change record naming the mechanism.
- **Two unused link definitions** (`glossary-djangoconnectionfield`,
  `glossary-djangotype`) — resolved by the same edit, since they now have uses again.
- **`## Risks and open questions` still carried its full preferred-answer / fallback
  weighing** for six of seven bullets, while the rationale's Risks entry asserted the
  weighing had moved. A half-done move is the one state `BUILD.md` calls worse than none.
  Finished: the three risks this card **closed** (the card's `.mutate()` claim, the engine
  base's floor presence, the switchover's breadth) are gone from the spec — their
  normative residue already lives in Decision 6, the Slice-1 gate and Decision 11 — and
  the four still-live constraints stay, stated as constraints with the weighing behind
  them pointed at `[rationale-risks]`.
- **`## Borrowing posture` and `## Current state` had no rationale pointer**, though both
  have rationale entries (`BUILD.md` "Every decision keeps a one-line pointer" — a reader
  who cannot see the deliberation exists re-litigates it). Both added.
- **A `## Current state` prediction never discharged.** "The regenerated tree adds both in
  Slice 3" is a prediction about the build, which the vintage rule says does not stand;
  the rationale already claimed it "now reads as what Slice 3 did". Verified against
  `docs/TREE.md` (both rows present, at two tree renderings) and rewritten to
  "Slice 3's regenerate added both rows." The section's dated **observations** were left
  untouched, graded clause by clause.

### Rationale audit against the keyed-to-the-spec rule

`BUILD.md` `## Spec rationale extraction`: every entry names the spec decision it belongs
to by heading and anchor, and carries the alternatives rejected with why each lost, every
change the decision has undergone with the round that caused it, and any claim it may no
longer make. Audited entry by entry:

- **Keying is sound.** All twelve decision entries open with a `Spec: [Decision N][dN]`
  line resolving to a real spec anchor, and the three non-decision entries
  (`## Borrowing posture`, `## Risks and open questions`, `## Current state`) are keyed the
  same way. Every one of the rationale's own cross-file anchors was mechanically checked
  against the spec's real headings: 0 broken.
- **Claims-no-longer-permitted are present** where they are owed — Decision 5 (the
  `client=` seam by truthiness), Decision 9 (twice: the `operationName` truthiness gate,
  and `files is not None` as the multipart switch), Decision 11 (that any package-tier test
  in this card drives a request).
- **Repaired this pass:** the Decision 3 entry carried alternatives and derivation but no
  change record, while the move had in fact changed that decision — it forced the
  prefix rule from a rejected alternative into normative spec text. Added, with the
  general lesson (a rejected alternative can be the sole carrier of a gated
  cross-reference; the gate is the instrument that says so, so run it *after* the move).
- **Claims the rationale made that the spec did not yet honor are now true.** Four were
  false at pickup and are true at close: F3's "folded into … `## Helper-reuse obligations
  (DRY)` list as **D5**"; F4's "Folded into Decision 7 **and** the spec's
  `## Edge cases and constraints`"; F6's "The spec now names the source in every one of
  those places"; F7's "The spec grew scenario 15". This is the F1-companion failure mode
  worth naming: **a rationale written in the same pass as the spec edit can describe an
  edit that did not finish landing, and reads as a record either way.**
- **`AGENTS.md` rule 4 holds.** `grep -ci feedback` is **0** in both the spec and the
  rationale; the moved Revision 2 entry describes the maintainer follow-up review without
  naming any file.
- No entry names a decision that does not exist, and no decision lacks an entry.

### F7 — what scenario 15 actually names

Written from the suite, not from the finding text. Every node id below was read in
`tests/testing/test_client.py` before being cited:
`::test_files_placeholder_tuple_arrays_walk_and_map_like_lists`,
`::test_files_placeholder_empty_segment_raises_instead_of_emitting`,
`::test_files_placeholder_noncanonical_list_index_raises` (+
`::test_files_placeholder_out_of_range_list_index_raises`),
`::test_files_placeholder_hostile_len_container_fails_closed`,
`::test_files_placeholder_cannot_descend_into_a_scalar_raises`,
`::test_files_placeholder_present_but_not_none_raises` (+ the two missing-key rows),
`::test_files_placeholder_hostile_repr_keeps_assertion_error_boundary`,
`::test_empty_files_dict_is_a_plain_json_post`,
`::test_clients_preserve_an_explicit_falsy_transport`.

One family deliberately gets **no** row and says so in the spec: `_finish_response` sits on
the only path either color's `query()` takes, so every live request-driving scenario
exercises it in both colors, and a row asserting it is *called* would pin observability
rather than behaviour (`BUILD.md` `### Query-shape tests must pin the load-bearing
property, not observability`). Naming an invented row here would have been worse than the
gap it filled.

### Verification run

All read-only; this pass wrote no `.py` file and ran no `pytest` (`AGENTS.md` rule 15 — no
code changed). No coverage-shaped flag was used anywhere.

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-043-test_client-0_0_14.md`
  -> `OK: 22 terms - all have glossary entries and at least one spec link.` (exit 0).
  **Was failing at pickup** on `DjangoType` / `DjangoConnectionField`; this is the reading
  that matters, not the pre-flight one.
- `uv run python scripts/check_citations.py --check` -> `OK: 994 citations resolve (824 in
  441 .py files, 170 in KANBAN.md).` Whole tree, no pre-existing failure to attribute.
- `uv run python scripts/check_trailing_commas.py docs/SPECS/spec-043-test_client-0_0_14.md
  docs/SPECS/appx/spec-043-test_client-0_0_14-rationale.md --check` -> exit 0. Explicit
  paths only; the repo-wide default would auto-fix the concurrent session's files.
- **Link / anchor audit**, scripted into the session scratchpad and run over both files:
  reference uses vs definitions, in-page `](#…)` anchors vs real headings, cross-file
  anchors vs the target file's real headings, and disk-existence of every definition path.
  **0 problems in both files** at close, against 17 in the spec at pickup. Code spans and
  fenced blocks are stripped before sweeping, so a backticked `res.data["edges"]` does not
  read as a reference.
- `grep -rn 'spec-043' docs/` -> 77 hits, walked. The two that quote spec text still
  resolve: `docs/builder/DONE/build-006-public_surface-0_0_3.md` cites
  `spec-043 #"The family stays under"` (present, untouched), and
  `docs/builder/DONE/build-038-form_mutations-0_0_12.md` cites `spec-043 scenario 4`
  (still `login()` scoping — scenario 15 was **appended**, so no ordinal moved).
  Two inbound claims are now stale and are recorded under
  `### Notes for Worker 1 / Worker 0` below rather than silently fixed, both in files this
  cycle's fence makes non-writable.
- **In-page anchor sweep after the Decision-heading question:** no Decision heading was
  rewritten this pass, so no `](#decision-N--…)` link was stranded; the audit above
  confirms it mechanically rather than on that reasoning.

### Byte counts, measured

| File | HEAD | At pickup | At close |
| --- | --- | --- | --- |
| `docs/SPECS/spec-043-test_client-0_0_14.md` | 153,065 | 137,129 | **142,356** |
| `docs/SPECS/appx/spec-043-test_client-0_0_14-rationale.md` | (did not exist) | 50,346 | **51,290** |

`git diff --stat` on the spec at close: 282 insertions, 444 deletions. The spec grew
5,227 bytes against the pickup state because this pass **added** contract (scenario 15,
the D5 reuse item, the accessor edge case, the Decision 3 naming rule, 16 link
definitions) while removing the residual weighing; net against HEAD it is 10,709 bytes
smaller, and the deliberation it shed is 51,290 bytes of companion that did not exist
before.

### Hot-path budget

Not applicable; plan declares no hot path. Restated from the plan's own ground rather than
from "no executable code changed": `django_strawberry_framework/testing/client.py` is a
consumer *test* utility whose every symbol runs inside a test process — never per request,
per resolver, per row, per connection, or per outbound message in a deployed schema.

### Floor verification

Not applicable; plan declares floor-verification scope `none`. This pass edited prose only.
F6 is a **text** correction and owes no floor run: the floor-presence question the Slice-1
gate covers (`strawberry.test.BaseGraphQLTestClient` importable) is settled by the module
importing successfully at HEAD, and the corrected text now names
`pyproject.toml` and `docs/builder/BUILD.md` `## Floor verification` as the source instead
of restating a number that moves.

### Failability proofs

None; this pass introduced no new boundary. No `.py` file was written.

### Spec changes made (Worker 1 only)

Every edit to `docs/SPECS/spec-043-test_client-0_0_14.md` this pass, with the finding that
triggered it. Cited by section and symbol, never by line number — the file was rewritten
under itself several times over.

1. **`## Key glossary references`, the soft-dependency bullet** — F6. "hard
   `strawberry-graphql>=0.262.0` dependency" -> names the `strawberry-graphql>=` pin in
   `pyproject.toml`.
2. **`## Slice checklist`, Slice 1's Strawberry test-module gate** — F6. The pinned
   `==0.262.0` and the "Presence at the installed strawberry 0.316.0" sentence -> the gate
   now names `pyproject.toml` for the lower bound and `BUILD.md` `## Floor verification`
   for the policy point, and says outright that the floor is not restated "because it
   moves".
3. **`## Slice checklist`, `tests/testing/test_client.py` sub-check** — F2. `(Revision 3)`
   attribution dropped.
4. **`## Current state`, the engine-base bullet** — F6. Same source-naming rewrite.
5. **`## Current state`, the `docs/TREE.md` bullet** — the undischarged prediction;
   rewritten to past tense against the real render.
6. **`## Current state`, section tail** — F1/F2. One-line pointer to
   `[rationale-current-state]`, stating the vintage rule that its observations stand.
7. **`### Explicitly do not borrow`, section tail** — F1/F2. One-line pointer to
   `[rationale-borrowing]`.
8. **`### Error shapes`, the `files=`/`variables` bullet** — F5. The false
   `if files is not None and variables is None` guard -> the shipped truthiness at both
   ends, plus the walker named as the placeholder-contract enforcer.
9. **`### Decision 3`** — the glossary-gate repair. New paragraph stating the
   `Django*`-prefix rule as contract, carrying the `DjangoType` /
   `DjangoConnectionField` links.
10. **`## Implementation plan` table, `tests/testing/test_client.py` row** — F2.
    `— Revision 3 F2` dropped.
11. **`## Helper-reuse obligations (DRY)`** — F3 family 3. New **D5** item for the
    `exceptions.py::_safe_arg_repr` reuse, which Decision 9 already cited against a list
    that had no D5.
12. **`## Edge cases and constraints`** — F4. New bullet for the module-level accessor's
    `__test__ = False`, beside the existing class-level one.
13. **`## Edge cases and constraints`, the `files=` placeholder bullet** — F5, the second
    site. Truthiness at both ends; the walker named.
14. **`## Test plan` preamble, scenario 2, scenario 3, scenario 10b** — F2. Four
    `Revision 3` attributions dropped; scenario 3's "(Revision 3 corrected the earlier
    'fails GraphQL-side' premise)" removed entirely, since the corrected premise is
    already stated and the correction's history is the rationale's Decision 11 entry.
15. **`## Test plan`, new scenario 15** — F7. The walker's five rejection branches and the
    two selection contracts, one named owner each, plus the explicit reason
    `_finish_response` has none.
16. **`## Test plan`, coverage paragraph** — F7. Re-pointed at scenario 15 so
    "every branch has a named owner" is true as written again.
17. **`## Risks and open questions`** — F1/F2. Three closed risks removed, four live
    constraints kept and restated as constraints, weighing pointed at
    `[rationale-risks]`.
18. **`## Definition of done`, three rows** — F2 and F6. `Revision 3 F1` / `Revision 3 F4`
    / `Revision 3 F2` attributions dropped; the no-new-dependencies row's `==0.262.0` ->
    the source-naming form.
19. **`<!-- LINK DEFINITIONS -->`** — 16 definitions added (`[rationale]`, twelve
    `[rationale-dN]`, `[rationale-borrowing]`, `[rationale-current-state]`,
    `[rationale-risks]`, `[build]`, `[exceptions]`), alphabetical within their groups,
    `[build]` filling the previously-empty `<!-- docs/builder/ -->` header.

Rationale edits (`docs/SPECS/appx/spec-043-test_client-0_0_14-rationale.md`): the
Decision 3 change record described above, and its `[terms]` link definition. Nothing was
retracted — every claim the prior pass wrote is true at close, because the spec caught up
to it.

**Not ticked, per F8:** no Slice-checklist, Helper-reuse, or Definition-of-done box was
touched. The new **D5** item ships `- [ ]` like its eight siblings.

### Notes for Worker 1 / Worker 0 (out-of-fence follow-ups)

No code change is owed by this pass: F5 confirmed the **spec** was the defect and the
shipped truthiness is correct, and every other finding resolved in prose. Cohort C is not
indicated by anything Cohort A found. Three items live outside this cohort's writable set
and are recorded rather than fixed:

1. **`docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md` (line 35) claims "three
   sentences in `spec-043` citing 'spec-042 Revision 8' by name".** That population is now
   **0** in the spec — it travelled into the spec-043 rationale, which is where that same
   sentence predicts it would be found, but the *count* no longer describes spec-043. The
   claim's substance survives; its arithmetic does not. Non-writable this cycle (the
   maintainer's scope fence covers `docs/SPECS/appx/` companions of other specs).
2. **`docs/builder/build-043-test_client-0_0_14.md` (F2) cites
   `spec-043 #"Revision history (kept inline so the spec is self-contained)"`.** That
   substring no longer exists in the spec — correctly, since removing it *was* F2. The
   plan is this cycle's own per-cycle artifact recording the pre-fix state, and `START.md`
   exempts per-cycle scratch from the citation rules, so this needs no repair; recorded so
   a later reader does not mistake it for rot.
3. **The dispatch's F3 measurement method** (grepping code vocabulary against spec prose)
   and **its stale `check_spec_glossary.py` reading** are both worth carrying into the
   cycle's closeout, since both would have shipped a wrong verdict if accepted on prose.

### Summary

This pass finished the spec-043 post-ship reconciliation a prior subagent of this role
began and did not complete. F1-F4 and F8 were verified already landed (F3 in full, once
the dispatch's grep-vocabulary error was corrected); F5, F6 and F7 landed here, together
with four defects the dispatched list did not name — 15 undefined link references, a
**failing** spec-glossary gate, a half-moved Risks section, and an undischarged
`## Current state` prediction — every one of them a consequence of the rationale move
itself. The spec now reads as a clean current contract with no chronology in it, the
rationale is keyed decision by decision with every one of its claims true against the spec
on disk, and all four gates are green.

Final status: **final-accepted**.
