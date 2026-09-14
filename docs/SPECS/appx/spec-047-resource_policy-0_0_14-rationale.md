# Rationale: spec-047 — Execution resource policy (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-047-resource_policy-0_0_14.md`][spec-047]. The spec is the
contract and states only what is currently true; everything that explains **how it got there**
lives here: the alternatives each decision rejected and why each lost, the derivations that do
not change how a decision is implemented, every change a decision has undergone with the round
that caused it, and every claim a decision once made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass. **The move
happened after the release, not before the build.** The shipped cycle skipped it; this pass
supplies it. Text marked *Moved* below was cut out of the spec, not copied: it exists here and
nowhere else.

## How to read this file

- **One entry per spec decision**, named by the decision's own heading and linked to its anchor.
  A decision whose text did not move and which has not changed since the release has no entry
  under `## Decision entries` — that is not an omission, it means the whole decision is
  contract and always was. A decision that changed *after* the release is keyed from
  [the post-release change register](#the-post-release-change-register) instead, and carries a
  pointer entry below so a reader arriving at the decision finds it either way.
- **Who reads it.** Worker 3 reads it during review; Worker 1 owns it; Worker 2 never reads it.
  A reader looking for what the package *does* wants the spec, not this file.
- **Round attribution.** This card ran a build round, then a **remediation round**, then —
  long after the release — a **reconciliation round** that brought the spec back into
  agreement with what had shipped and with the 313 commits of later change that separate the
  release from `63a132be`. Where a decision changed, the entry names which round or which
  commit changed it.
- **Where the remediation round's own artifact went.** It was a per-cycle
  `docs/builder/bld-*.md` artifact and was deleted with its cycle, so it is not on disk at any
  current revision. One pointer reaches it —
  `git show 99696bac^:docs/builder/bld-047-remediation.md` — and one is enough: the blob is
  byte-identical at the commit that added it and at the parent of the commit that deleted it,
  so there is no earlier stale copy to reach for separately.
- **What deliberately stayed in the spec, and why.** The bounds table, the public API, the
  rejection envelope, the compatibility promise, goals, non-goals, edge cases, the test plan and
  the DoD are all contract. So are three passages that read like deliberation and are not:
  Decision 3's two contractual consequences (structural depth, and leaving a malformed document
  to the real parser), Decision 6's ordering constraint against the visibility hook, and the
  whole of Decision 13 — whose boundary entries and audited exclusions are instructions to a
  future builder ("must not be re-derived", "a later pass must not fix"), not a record of
  thinking. Only Decision 13's upstream forensics moved.

## Provenance of this record

- **Moved** — cut from the spec by this pass. The five `Alternatives rejected` paragraphs, the
  Borrowing posture's declined-borrowings list, four derivation passages inside Decisions 4, 8,
  9 and 11, Decision 13's upstream `except`-clause forensics, and the Risks section's fallback
  positions.
- **Reconstructed** — rebuilt from the shipped code, the release commit, and the remediation
  round's own catalog (reachable only through the `git show` pointer above). The whole of the
  change record below. The build cycle produced no per-round review documents for this card,
  so that catalog is the only contemporaneous round artifact and is the source for every
  attribution that names it.
- **Re-derived against a pinned revision** — the post-release change register at the end of
  the change record. Every entry in it was read against the source at `63a132be` before it was
  written, and every commit named in it was confirmed a descendant of the release commit
  `567cc6d0`. The revision is named because the register is a claim about a moving tree, and a
  claim about a moving tree that does not say when it was taken cannot be re-checked.
- **Deleted, recorded nowhere** — the spec's original Decision 12 premise and the Status block
  that depended on it. Both were falsified by the release rather than superseded by an argument,
  and prose a current decision has falsified belongs in neither file. What replaced them is in
  the change record's first entry.

## Change record

### The version cut this card predicted it would own

**Falsified, then withdrawn.** The spec's original Decision 12 read *"This card is the only
non-Done `0.0.16` card, so it owns the bump"*, and a Version boundary paragraph at the head of
the spec repeated it. Both were true of the board at authoring time and neither survived.

Each of cards 046, 047, 048 and 049 ran the same board scan at its own authoring moment, and
each concluded — correctly, in isolation — that it was the only non-Done card at its patch
version and that the [Joint version cut][glossary-joint-version-cut] rule therefore did not
apply. The maintainer then retargeted **all four** cards to `0.0.14`, the patch cards 041-045
already occupied. `0.0.15`, `0.0.16` and `0.0.17` were never the version of a released
artifact; `__version__` never held any of them.

So the bump this decision claimed does not exist to be owned. The quintet reached `0.0.14`
ahead of this card's first slice, the card targets `0.0.14`, and Slice 5 folds documentation
in and nothing else. Later cards moved the quintet past `0.0.14` on their own lines; what
`__version__` reads at any given revision is a fact about whichever card is current, never
about this one. The spec's Decision 12 now states that directly, and the
`Joint version cut` entry in its `## Key glossary references` was correspondingly reversed:
it was listed as "the release rule this card is explicitly NOT subject to" and is now the
rule the card is subject to.

**The lesson worth keeping.** A single-card board scan cannot establish that a card owns a
version cut, because it cannot see what the other cards on the program will be retargeted to.
The rule already says the last card of a shared line to land owns the wording; a card that
scans the board and concludes it owns a cut of its own is predicting a release shape an
authoring-time scan cannot know.

### The identity memo the value walker no longer uses

**Changed by the remediation round.** The build shipped `_ValueBudget` with a single
request-lifetime `_seen: set[int]` of already-charged `id()` values, doing double duty as a
cycle guard and as a charge-once cache. The remediation round deleted it and replaced it with an
ancestor-path tuple for termination and **no cache at all** for charging.

Two measured bypasses forced it, and they are the reason the spec now says every reference is
charged:

- **An `id()` is unique only among LIVE objects.** The coerced values this walk reads are
  temporaries; freeing one list lets the next same-sized list reuse its address, so an
  `id()`-keyed set reports a *fresh* container as already charged. Measured on this package's
  own walker: 1,650 relation ids charged as 55, because graphql-core's `value_from_ast_untyped`
  builds fresh same-size lists whose ids recycle through CPython's free list.
- **Charge-once is not the contract.** One variable spliced into two mutation fields resolves to
  the same Python list both times, so charge-once made the second field's relation ids free and
  the aggregate bound never fired — a live request walked past `max_relation_ids_total` and went
  on to decode ids.

A cycle guard needs ancestor-scoped lifetime and owning references; a charge-once cache needs
neither. Conflating the two in one set is what produced both bypasses, which is why they are now
two separate mechanisms.

**A claim the spec may no longer make.** Nothing in the package should describe the value walker
as memoizing containers by identity. That sentence describes the deleted mechanism and, read as
current, promises the exact charge-once behaviour the remediation removed.

### `max_value_depth` was added late, and the glossary never saw it

**Added by the remediation round.** The bound did not exist at build time. It closes a gap
neither document bound could reach: `max_depth` counts brackets in the document *text*, and a
value arriving through a variable has none, so a 10,000-deep nested payload was bounded by
nothing while its node total stayed small.

The remediation catalog recorded that the glossary DB was deliberately left untouched for that
round's scope, so `max_value_depth` shipped with no glossary entry and the `ResourcePolicy`
glossary body enumerated the bounds without it. That debt outlived the round and was carried on
the board until this closeout pass discharged it.

### The introspection blind spot

**Fixed by the remediation round.** The walk originally answered "no field definition" for
`__schema`, `__type` and `__typename`, and the walk ends a branch whose field cannot be
resolved. Introspection was therefore charged as ONE selection and never descended into — making
it the single document shape no depth, selection, or collection bound could see, even though
`__schema` opens a subtree over every type, field, argument and enum value in the schema. The
meta-fields now resolve to graphql-core's own `SchemaMetaFieldDef` / `TypeMetaFieldDef` /
`TypeNameMetaFieldDef`, exactly as that library's executor resolves them.

### Decision 13 was written after the release

The remediation round's deferral catalog was folded into the spec as Decision 13 a day after the
release commit — the only substantive post-release edit to the spec, and purely additive: three
bounds with named seams, three audited exclusions a later pass must not "fix", and the
carried-forward Definition-of-done boxes that tracked the first three.

Those boxes are gone, and the decision no longer calls the three bounds owed. A spec whose
`Status:` line says shipped cannot also hold unticked work: the boxes were a promise the card
had already stopped being able to keep, and every one of the three is a transport-adjacent bound
this walker is the wrong layer to carry — none could be discharged by editing this spec. They are
scope on card `TODO-ALPHA-051-0.0.15` instead, which is where the request-body cap's layer and
the boundary-hardening work already live. Decision 13 keeps the full technical statement of each,
because *where the bound does not reach* is contract a consumer needs; what it no longer claims is
that this card still owes it.

### The post-release change register

Everything above this heading happened before or at the release. This section is the chapter
that was missing: what happened to the spec-047 surface **after** `0.0.14` shipped, and what
the spec is therefore no longer allowed to say.

**Scope and method.** The release commit is `567cc6d0`. Measured at `63a132be`, the revision
this register was written against: `git rev-list --count 567cc6d0..HEAD` gives **313**
commits since the release, **63** of which touch one of the **seventeen** package modules this
spec names — the sixteen distinct `.py` paths in its Implementation plan table, plus
`forms/resolvers.py` from Decision 13 — and **20** of those were read against this contract.
Those 20 are the table below, grouped into 16 rows where several commits made one change.
**Sixteen of them, in the table's first 15 rows, change what the contract says; the remaining
four, in its last row, change nothing in it.** The four are carried anyway: a commit that
touched this surface and left the contract alone is a fact worth having measured, and a reader
re-deriving the population from the 63 would otherwise have to work out for themselves why
four of them are absent. That is also what the last row's empty **Bears on** cell means — not
an unfinished entry, but the finding. Each of the 20 was read against the source at that
revision before it was written down, and each was confirmed a descendant of the release
(`git merge-base --is-ancestor 567cc6d0 <sha>`, exit 0 for all 20). The 313 and the 63 move
with every commit anyone lands — the **16** is the figure that matters, and it is the one a
later reader should re-derive rather than trust. Two of spec-047's own source files were dirty
with a concurrent session's uncommitted work throughout, so every reading was taken from a
read-only extraction of that revision whose byte identity with `git show <rev>:<path>` was
proved first, never from the working tree.

**Three classes, kept apart on purpose.** A **correction** changed what the code does and
therefore what the contract says. A **refactor** moved or renamed a seam with the behavior
preserved exactly, so the contract is unchanged and only the spec's citation of it was stale.
A **later feature** is a different card extending a surface this one owns, which changes what
this card's bound promises even though this card did not do it.

#### What changed, by commit

| Commit | What it did to the 047 surface | Class | Bears on |
|---|---|---|---|
| `292c7411` | `derive_connection_window_bounds` narrows through `resolve_relay_max_results` before building the slice metadata. **At the release the policy ceiling reached the offset window unclamped** — a real hole in the shipped ceiling, not a tidy-up. Also made `utils/context.py::get_context_value` fall through to its default on a hostile descriptor. | correction | [D7][spec-047-d7], Edge cases |
| `6013cda6` | Folded delete and the plain form onto `run_write_pipeline_sync`, deleting the delete branch's own `check_deadline`. | refactor | [D9][spec-047-d9], [D13][spec-047-d13] |
| `18550f5d` | `_with_resource_policy_extension` stopped normalizing `extensions` through truthiness, so a `__bool__`-overriding container cannot be consulted before Strawberry sees its entries; the class-or-instance test became `schema.py::_extension_entry_matches`. | correction | [D11][spec-047-d11] |
| `de2601e9` | Retired `connection.py::_resolve_connection_fast_path` (readable only at `git show de2601e9^:django_strawberry_framework/connection.py`); the two `resolve_connection` overrides collapsed into one reading a `_resolves_total_count` class flag. Behavior preserved exactly. | refactor | [D7][spec-047-d7], [D9][spec-047-d9] |
| `ba15c767` | (i) Replaced the end-of-operation **clear** with a snapshot-and-restore. (ii) Made the scalar-where-a-list-is-declared coercion **actually** charge a container plus one level of value depth — the Edge case was aspirational before. (iii) An upload whose `size` **raises on access** became a rejection, a sixth unmeasurable spelling. | correction | [D2][spec-047-d2], [D4][spec-047-d4], Edge cases |
| `597dbbb4` | (i) **Operation variable defaults are charged** — a `$p: Int = 5000` default was a free payload. (ii) Bytes-like scalars charge against `max_scalar_bytes`. (iii) `_charge_list_family` is reached only for a real list. (iv) `ResourceLimitExceeded` gained `detail` and `__reduce__`. | correction | [D4][spec-047-d4], [D11][spec-047-d11], bounds table |
| `2d94b89e` | `_STRUCTURAL_DELIMITER_PAIRS` single-sources the three bracket families; the open and close token sets derive from it. Zero behavioral change. | refactor | [D3][spec-047-d3] |
| `dc00f4a6` | Added the public `bounded_rows_async`; added a **finiteness** check to `execution_deadline_seconds` (`inf` was previously accepted); restructured `narrowed()` to compare the constructed copy's values; dropped "and the delete branch" from the seam docstring. | correction | [D6][spec-047-d6], [D9][spec-047-d9], [D10][spec-047-d10] |
| `a8f31a2d` | The largest post-release change. (i) **A mutation's bind-time `RELATION_MULTI` spec now outranks the `ID`-scalar test**, so a raw-pk `[Int!]` relation list is charged as relation ids where the release charged it as a membership list. (ii) `scan_document_text` declines a non-`str` query. (iii) The context round trip moved to `utils/context.py::restored_context_keys` plus a public `MISSING`. (iv) `check_deadline` fails closed on a hostile stashed deadline. (v) `bounded_rows` catches `KeyError` beside `TypeError`. (vi) Extensions are built through `utils/errors.py::coded_error_extensions`. | correction | [D2][spec-047-d2], [D3][spec-047-d3], [D4][spec-047-d4], [D9][spec-047-d9], [D11][spec-047-d11] |
| `9894410f` | The precedence ladder was extracted to `utils/policies.py::resolve_policy`; `resolve_resource_policy` **kept its name, signature and contract** and delegates. New shared `_require_positive_int` and `_raw_list_bound`. | refactor | [D1][spec-047-d1], DRY |
| `03538f36` | `assert_relay_pagination_bound` gives the over-cap error one owner **for the keyset fork only** — its two call sites are `utils/connections.py::derive_keyset_window_bounds` and `connection.py::_resolve_keyset_connection`. The **offset** window takes its over-cap error from Strawberry's `SliceMetadata.from_arguments`; the helper exists because a keyset cursor is not an offset and cannot be run through that engine, and it reproduces `SliceMetadata`'s messages so the two forks agree by message-mirroring rather than by a shared owner. | refactor | [D7][spec-047-d7] |
| `ddd5dbb9`, `841e56d6` | The generated many-side relation resolver bounds at **five** call sites in `types/resolvers.py` — **three** `bounded_rows` and **two** `bounded_rows_async`, counted by `grep -nE 'bounded_rows(_async)?\(' django_strawberry_framework/types/resolvers.py` — all after per-relation visibility. | later feature | [D6][spec-047-d6] |
| `89ee8ac5` | spec-050. `bounded_rows` / `bounded_rows_async` gained `offset` / `requested_limit`; **`max_list_rows` changed meaning** to an accepted-coordinate and returned-row ceiling, explicitly disclaiming the "rows evaluated" promise; `DjangoListField` publishes `offset` / `limit` / conditional `orderBy`; new public `ListArgumentError`. | later feature | [D6][spec-047-d6], bounds table |
| `aadca5a2` | spec-050. **`effective_bound`'s widening test changed from `if trusted:` to `if trusted is True:`** — the release accepted any truthy value. New constructor-site `validate_trusted_flag`. | correction | [D10][spec-047-d10] |
| `63a132be` | spec-050. (i) **`offset` / `requested_limit` came off the exported `bounded_rows` / `bounded_rows_async`** — an importer could have widened the one primitive whose contract is that nothing a caller passes can widen it — and onto the package-private `_windowed_rows` / `_windowed_rows_async`, which `list_field.py` calls directly; the export delegates with no window, `_raw_list_bound` is unchanged as the single derivation, and `list_field.py::_normalize_list_arguments` owns the ceiling check on the coordinates. The spec may no longer say the exported seam accepts client coordinates. (ii) New `_attach_cleanup_note` / `_is_cleanup_diagnostic`: a cleanup error becomes a `__notes__` entry on the primary error only when it is an `Exception`; a `BaseException` such as `asyncio.CancelledError` propagates from both async cleanup seams. spec-050 Decisions 5 and 8 own that contract's text; spec-047's test-plan phrase "a cleanup failure that must not mask the source error" stays true. | correction | [D6][spec-047-d6], DRY, Test plan |
| `4c483b6b`, `d3b91c8d`, `9a9f970c`, `4d98ad98` | spec-050 review fixes and scaffolding; `_close_async_iterator` gained a `caller` label. | later feature | — |
| *(uncommitted at the time of writing)* | spec-050 review fixes. (i) **The request context stopped being the authority for the budget.** `begin_resource_budget` / `end_resource_budget` arm a module-private `ContextVar`; `policy_from_info` reads it and ignores `DST_RESOURCE_POLICY` entirely while it is armed, and `check_deadline` takes the tighter of the armed deadline and `DST_RESOURCE_DEADLINE` (`_effective_deadline`), so the mirror can narrow and can no longer widen or clear. At the release a resolver could widen `max_list_rows`, the `offset` ceiling and `max_page_size`, or buy unlimited wall clock, by writing its own `info.context`. (ii) A numeric deadline that is **not finite** is refused rather than read as a distant future. (iii) **The bound domain became the EXACT built-in type** for every integer bound and for the deadline: a numeric SUBCLASS that compares normally was accepted and STORED at the release, and its `__format__` / `__ceil__` / reflected `__radd__` then reached the rejection message, `math.ceil`, and the `time.monotonic() + seconds` derivation — the last of which could return `nan` and silently disarm an accepted policy's deadline. | correction | [D1][spec-047-d1], [D2][spec-047-d2], [D9][spec-047-d9], Edge cases |

#### Claims the spec may no longer make

Each of these was in the spec and is not any more. They are listed so a reader who remembers
the old sentence can see that it was retired deliberately rather than lost.

- **[Decision 2][spec-047-d2] — "the end-of-operation clear".** There is no clear. The
  extension snapshots both context keys and restores what was there, so a nested schema
  execution hands the outer operation back its own cap and deadline; clearing left the outer
  request with no deadline for the rest of its work. `clear_resource_context` survives as an
  export and is called by nothing in the package — only `tests/test_resource_policy.py` calls
  it — so nothing should describe it as part of the operation lifecycle.
- **[Decision 2][spec-047-d2] — the request context as the place the budget is "read back
  from".** The keys are still published there, and a consumer may still read them and may
  still stash an EARLIER deadline to shorten its own request. What they are not is the value
  any enforcement seam trusts: `info.context` belongs to the consumer, so a design that reads
  a bound back out of it lets every resolver in the request widen that bound. Nothing may
  describe `policy_from_info` or `check_deadline` as reading the operation's budget from the
  context while a budget is armed.
- **[Decision 1][spec-047-d1] — "`bool` is rejected explicitly", as the whole domain rule.**
  The rule is the exact built-in type, and `bool` is one thing it excludes. Describing it as a
  `bool` carve-out reads as though `isinstance` were the test, which is what admitted a
  numeric subclass whose dunders then ran inside the policy.
- **[Decision 4][spec-047-d4] — "classified by TYPE, never by argument name", as a complete
  enumeration.** The type is the second signal, not the first. A mutation's bind-time
  `RELATION_MULTI` spec outranks the `ID`-scalar test, which is the only reason a raw-pk
  relation list typed `[Int!]` is recognized as relation ids at all; charged by type alone it
  was a membership list, so a mutation's relation payload was measured against the wrong bound
  entirely. Nothing may describe the classification as type-driven with one name-based
  exception.
- **[Decision 4][spec-047-d4] — the three value sources.** There are four. An operation
  variable definition's own default is a source in its own right, and a walk that charged only
  the variables map charged nothing for a document that carried its whole payload in a default.
  That was a live bypass, not a gap in the prose.
- **[Decision 6][spec-047-d6] — "`bounded_rows` is the single place".** One seam, two
  execution colors. `bounded_rows_async` is public, is in the module's own `__all__`, and is
  awaited by both `list_field.py` and `types/resolvers.py`. What makes them one bound rather
  than two is `_raw_list_bound`, the single body that resolves the limit for both.
- **[Decision 6][spec-047-d6] — "rows a raw list may EVALUATE".** `max_list_rows` bounds the
  rows returned and the skip coordinate accepted. It never bounded the rows a database scans
  to reach an offset, and spec-050's coordinate arguments made the difference visible enough
  that continuing to claim it would have been a promise the seam cannot keep.
- **[Decision 6][spec-047-d6] — "The seam accepts `offset` and `requested_limit` client
  coordinates".** The exported pair accepts neither: `63a132be` moved the pair onto the
  package-private `_windowed_rows` / `_windowed_rows_async` and left `bounded_rows` /
  `bounded_rows_async` delegating with no window, because a coordinate is a claim the seam
  cannot check and a window wider than the request's ceiling would have widened the bound the
  export advertises to every importer. Nothing may describe the exported seam as taking a
  skip or a window; the ceiling those coordinates are checked against is unchanged, and the
  checking belongs to `list_field.py::_normalize_list_arguments`.
- **[Decision 7][spec-047-d7] — "both `resolve_connection` entry points".** There is one. The
  plain and `totalCount` shapes are one body reading a class flag, and
  `_resolve_connection_fast_path` — the head the spec named as the place the clamp and the
  deadline check lived — **no longer exists at any current revision**; it is readable at
  `git show de2601e9^:django_strawberry_framework/connection.py` and nowhere else.
- **[Decision 9][spec-047-d9] — "and the delete branch of `_run_pipeline_sync`".** Delete
  enters the shared write skeleton like every other flavor and inherits the one check. So does
  the plain form. The spec's enumeration of where the seam lives was the stale part; the
  contract never changed.
- **[Decision 10][spec-047-d10] — "`trusted=True` is the explicit widening opt-in", read as
  truthiness.** The test is `trusted is True`. At the release `if trusted:` let any truthy
  value — a non-empty string, a stateful object with a `__bool__` — widen the one primitive in
  the package whose answer may exceed the request policy.
- **[Decision 12][spec-047-d12] — "The version quintet already reads `0.0.14`."** A
  present-tense reading of a file later cards move. The card's own fact is that `0.0.14` was
  already reached before its first slice, which stays true at any later date; what `__version__`
  reads today belongs to whichever card is current.
- **[Decision 13][spec-047-d13] — the audited exclusion for
  `forms/resolvers.py::_run_plain_form_pipeline_sync`.** That function **no longer exists at
  any current revision** — it is readable at
  `git show 6013cda6^:django_strawberry_framework/forms/resolvers.py` and nowhere else. Both
  form flavors share `_run_form_pipeline_sync`, which enters `run_write_pipeline_sync`
  unconditionally, so the plain form now *does* get the deadline check and the stated reason for
  excluding it ("no database seam to guard") no longer describes the arrangement. The decision
  opens with five boundaries and two audited exclusions rather than six and three.
- **The preamble and the Out-of-scope list — "`WIP-ALPHA-049-0.0.14`".** Card 049 shipped;
  the board reads `DONE-049-0.0.14`, and both of this spec's references now do too. Recorded
  because a card id is the one kind of citation that rots without the text around it changing
  a word, so a reader who remembers the old spelling should be able to see that it moved
  rather than assume the spec is describing a different card.
- **Helper-reuse obligations — "`effective_bound` is the only narrowing rule" and
  "`_ValueBudget._reject` is the only rejection constructor".** Both were false as written.
  `extensions/resource_policy.py::_page_bound` open-codes `min(value, policy.max_page_size)`
  inside the document walk, and two `ResourceLimitExceeded` constructions sit in
  `_ValueBudget._charge_upload`'s unmeasurable-size branches with three more in
  `_DocumentBudget`. The repair was to say what each rule governs rather than to append an
  exception list: an obligation stated as an absolute that the code does not honor teaches a
  reader to distrust the whole list.

#### Public symbols the spec did not name

All confirmed at `HEAD`; none is a root package export, so no `__init__.py` `__all__` pin
moves. `resource_policy.py` — `bounded_rows_async`, `validate_trusted_flag`,
`DST_RESOURCE_DEADLINE`, `ResourceLimitExceeded.detail`, `ResourceLimitExceeded.__reduce__`.
`utils/context.py` — `MISSING`, `restored_context_keys`. `utils/policies.py` —
`resolve_policy`. `list_field.py` — `ListArgumentError` (spec-050's, listed here only because
a reader tracing `bounded_rows`'s callers meets it).

#### What did NOT change, measured rather than assumed

A register of changes is only trustworthy beside the population it found unchanged.

- **The bounds table reconciles 20/20** against the shipped `ResourcePolicy` dataclass. Two
  rows were re-worded (`max_list_rows`, `max_scalar_bytes`); **no default was re-valued**, and
  no bound is in the code without a row or in a row without the code.
- **Every scenario the Test plan names has a real test asserting it.** The sweep found no
  spec-named test that does not exist. What was wrong was the arithmetic around them: the live
  tier's published "35 rows" is **56** and the package tier's "79 rows" is **117**, re-derived
  with two independent instruments — `grep -cE '^(async )?def test'` and an `ast` parse
  multiplying every `@pytest.mark.parametrize` cardinality, which agree exactly on the function
  counts and differ only by the transparently computed parametrize expansion (117 functions →
  **185** node ids package, 56 → **56** live, `unresolved_parametrize = 0` on both). The spec
  now says which unit it publishes, because a count whose unit is unstated is a count the next
  reader replaces with a third figure.
- **A count of a population somebody else is editing is a self-falsifying instrument.** The
  package tier read 113 functions at the start of this round and 117 by the end, because a
  concurrent cycle landed four rows mid-pass. Both readings were correct; neither is durable.
  So the spec publishes the figure as a FLOOR with its unit named, which is the only form of
  that number a later reader can act on — a larger count means the file grew, not that the
  plan is wrong.
- **Decisions 1, 3, 5, 8, 11 and 12 hold unchanged** in substance. Decision 3 and Decision 11
  gained clauses for hardening that is contract; Decision 12's conclusion held while its
  present-tense observation did not.
- **Nothing the spec planned was skipped in the code.** Every confirmed finding of this round
  was a spec description that had drifted or a post-release change the spec never recorded —
  never an unimplemented contract. That is why the round changed no source.

**The lesson worth keeping.** `scripts/check_citations.py` gates `path::Symbol` in first-party
source and on the board, and skips `docs/` prose entirely. So a spec's citations rot silently:
`connection.py::_resolve_connection_fast_path` was named in two decisions of a spec whose
`Status:` line says shipped, and the symbol had been deleted by a refactor that touched neither
file. Nothing failed. A spec that cites code owes a citation sweep whenever it is edited,
because no hook will run one for it.

## Decision entries

### Decision 1 — One immutable frozen dataclass, validated at construction

Spec: [Decision 1][spec-047-d1].

*Moved — alternatives rejected.* A settings-dict read per bound (S3's explicit "do not scatter
unrelated settings reads across resolvers"). A mutable dataclass with a `freeze()` call (the
unfrozen window is the bug). Pydantic (a new hard dependency for one object).

### Decision 2 — Armed for the operation, published on the request context

Spec: [Decision 2][spec-047-d2].

*Changed after the release* — the end-of-operation clear became a snapshot-and-restore, in
commits `ba15c767` and `a8f31a2d`; the request context stopped being the AUTHORITY for the
budget and became a mirror beside a `ContextVar`, with the mirror allowed to narrow the
deadline and nothing else. See
[the post-release change register](#the-post-release-change-register).

*Moved — alternatives rejected.* The context stash as the sole authority: it was the shipped
design, and it is the one the register's `_active_budget` row corrects. The reasoning that
chose it — the stash is visible to the consumer's context object, and the package already owned
a context seam, so two would be one too many — weighed visibility and seam count and did not
weigh WRITABILITY. Both of those goods survive: the keys are still published on the consumer's
context, and the shape-agnostic dispatch is still the one shared seam. What could not survive
is reading enforcement state back out of an object every resolver in the request can write. A
thread-local (wrong under async) stays rejected, and for a reason the `ContextVar` does not
share: a `ContextVar` is per-task under asyncio and propagates across the `sync_to_async`
boundary a Django resolver actually crosses.

*Moved — why the context dispatch is shared rather than copied.* The shape-agnostic read / write
/ delete dispatch was the optimizer's before this card, in `optimizer/_context.py`. Slice 1
lifted it to `utils/context.py` rather than writing a second copy beside the policy helpers: it
already handled the four context shapes and was already the single place a new shape would
land, so a copy in `resource_policy.py` would have been the first duplicate of it, and the
first place the two subsystems could drift on which shapes they accept. The optimizer module
kept its keys and its reset and re-exports the helpers.

### Decision 3 — The document text scan runs BEFORE the parse

Spec: [Decision 3][spec-047-d3].

*Changed after the release* — the bracket families were single-sourced and a non-`str` query is
now declined rather than lexed, in commits `2d94b89e` and `a8f31a2d`. See
[the post-release change register](#the-post-release-change-register).

*Moved — alternatives rejected.* `parse_options["max_tokens"]` (loses the typed code; see the
Borrowing posture entry below). A `ValidationRule` for depth (runs after the parse). A regex or
`str.count` over the document (a brace inside a string literal is not a brace; the lexer knows
the difference).

### Decision 4 — The document and value budgets are one iterative walk

Spec: [Decision 4][spec-047-d4].

*Changed after the release* — the bind spec now outranks the type test, operation variable
defaults are charged, and the scalar-where-a-list coercion charges what the Edge case always
claimed, in commits `a8f31a2d`, `597dbbb4` and `ba15c767`. See
[the post-release change register](#the-post-release-change-register).

*Moved — alternatives rejected.* A `ValidationRule` (no access to variables, which is the whole
of S4). Charging only variables and ignoring literals (a literal object is a value too).
Recursion with a depth guard (a depth guard on a walker that exists to bound depth is circular).

*Moved — the derivation of the ancestor-path guard.* The full account of the deleted
`_seen: set[int]`, both measured bypasses, and why one object could not be both a cycle guard and
a charge-once cache is in the change record above, under
[The identity memo the value walker no longer uses](#the-identity-memo-the-value-walker-no-longer-uses).
The ancestor path is the same shape the document walk already uses for fragment spreads (a
`path` carried on the stack), with object identity in place of fragment names.

*Moved — the introspection derivation.* Why answering "no field definition" for the meta-fields
made introspection invisible to every document bound is in the change record above, under
[The introspection blind spot](#the-introspection-blind-spot).

### Decision 5 — `DEFAULT_RELATION_SHAPE` becomes `"connection"`: a clean alpha break

Spec: [Decision 5][spec-047-d5].

*Moved — alternatives rejected.* A one-release deprecation warning while still emitting both
(keeps the bypass, and a warning nobody reads is not a mitigation). A settings flag to restore
the old default (a global switch that re-opens a security default is the worst of both — it is
invisible in the schema, unlike a `Meta` key). Leaving the default and relying on the new row
bound alone (bounding the sibling is not the same as not having it: the sibling has no cursor,
so a client can only ever read the first N rows of it, which is a worse API *and* still unbounded
across aliases).

*Moved — the derivation.* The card left the default open and the spec decided it, the way card
046 decided its own: a clean break with no deprecation shim. Every argument for a shim is an
argument for keeping the bypass reachable for one more release on schemas that never asked for
it, and a shim that emits both shapes *is* the insecure default under another name. The
migration is one line per relation, it is discovered at schema build rather than at runtime, and
the alpha line had already taken a larger break for a smaller reason.

### Decision 6 — Every raw list is bounded at one seam

Spec: [Decision 6][spec-047-d6].

*No alternative was rejected here; the decision changed after the release.* The seam gained a
second execution color (`bounded_rows_async`), a shared limit-deriving body (`_raw_list_bound`),
client `offset` / `requested_limit` coordinates, and a narrower promise for `max_list_rows`.
`63a132be` then moved the coordinates below the export, onto the package-private
`_windowed_rows` / `_windowed_rows_async`, leaving the exported pair windowless. See
[the post-release change register](#the-post-release-change-register), commits `dc00f4a6`,
`ddd5dbb9` / `841e56d6`, `89ee8ac5` and `63a132be`, and the three claims the decision may no
longer make.

### Decision 7 — The policy is a CEILING over `relay_max_results`, never a replacement

Spec: [Decision 7][spec-047-d7].

*No alternative was rejected here; the decision changed after the release.* The shipped ceiling
had a hole — the offset window derived its bounds without the policy clamp — and the two
`resolve_connection` entry points the decision described collapsed into one. See
[the post-release change register](#the-post-release-change-register), commits `292c7411`,
`de2601e9` and `03538f36`.

### Decision 8 — `max_collection_cost` is a SHAPE bound, and its default says so

Spec: [Decision 8][spec-047-d8].

*Moved — why the default is `1_000_000_000`.* A legitimate four-level document that leaves every
page unspecified already charges `10**8`, and a bound that rejects ordinary documents is a bound
the first deployment to meet it raises to infinity. The generous default is therefore a
deliberate choice to keep the bound credible, not an admission that it is weak — the row promise
is carried by `max_page_size` and `max_list_rows`, which the spec states.

### Decision 9 — The execution deadline is cooperative, and says so

Spec: [Decision 9][spec-047-d9].

*Changed after the release* — the seam enumeration collapsed onto one write skeleton and one
connection head, the deadline domain gained a finiteness check, and a hostile stashed deadline
fails closed, in commits `6013cda6`, `de2601e9`, `dc00f4a6` and `a8f31a2d`. See
[the post-release change register](#the-post-release-change-register).

*Moved — why the default is `None`.* A wall-clock deadline a deployment did not choose is a
correctness hazard (it truncates legitimate slow requests), not a safety one — the opposite of
every other bound here, which is why it is the only optional one. Every other bound defaults to
a number because the failure mode of a too-generous bound is a slow request, while the failure
mode of an unchosen deadline is a wrong answer.

### Decision 10 — Per-field overrides narrow; the schema policy is the trusted declaration

Spec: [Decision 10][spec-047-d10].

*No alternative was rejected here; the decision changed after the release.* The widening test
was `if trusted:` at the release and is `if trusted is True:` now, with a constructor-site
`validate_trusted_flag` beside it. The reason it is worth a record rather than a one-line diff:
this is the only primitive in the package whose answer may exceed the request policy, so a
truthiness test on it is a widening any truthy object can claim. See
[the post-release change register](#the-post-release-change-register), commits `aadca5a2` and
`dc00f4a6`.

### Decision 11 — One typed rejection, and no per-transport translation

Spec: [Decision 11][spec-047-d11].

*Changed after the release* — the extensions container is no longer consulted through
truthiness, and the rejection payload is built by the shared coded-extensions helper, in
commits `18550f5d`, `597dbbb4` and `a8f31a2d`. See
[the post-release change register](#the-post-release-change-register).

*Moved — why installation is automatic.* An endpoint whose only limiter is one a consumer
remembered to install is an endpoint with no limiter; that is the audit's finding, and automatic
installation is the answer to it. This is the same reasoning that rejected upstream's
three-extensions shape in the Borrowing posture entry below.

### Decision 13 — What this policy does not bound, and why each boundary is deliberate

Spec: [Decision 13][spec-047-d13].

*Changed after the release* — one audited exclusion was falsified and removed, in commit
`6013cda6`. See [the post-release change register](#the-post-release-change-register).

*Moved — the upstream forensics behind the subscription envelope.* Enforcement is not the gap;
rendering is. A subscription enters `extensions_runner.operation()` and `executing()` exactly as
a query does, so both the document text scan and the value walk run and a violating subscription
is refused. The difference is one `except` clause in upstream's schema: the **non-streaming**
path wraps its whole operation block in a broad `except Exception` that returns a
`PreExecutionError`, so an HTTP or WebSocket query or mutation carries an `errors` entry; the
**streaming** path's only pre-execution `except` names three errors (`MissingQueryError`,
`CannotGetOperationTypeError`, `InvalidOperationTypeError`), so anything an extension raises
escapes it. Upstream's `BaseGraphQLTransportWSHandler.run_operation` then catches that exception,
hands it to `handle_task_exception`, and sends `complete`.

*Moved — the version-drift evidence for "state the behaviour, never the private method name".*
The declared floor is `strawberry-graphql>=0.316.0` with no ceiling, and the seam moves inside
that range: the private implementation is `_subscribe` at the floor and `_stream` at `0.323.2`,
and the **public** attribute a handler dispatches through moved from `subscribe` to `stream` at
`0.319.0` — the same instability [`spec-046`][spec-046]'s stop-aware result source already
answers by wrapping both public names unconditionally rather than testing a version. The
instruction this evidence supports stayed in the spec.

## Deliberation that belonged to no single decision

### Borrowing posture — what was deliberately not borrowed

*Moved.* Strawberry ships `MaxTokensLimiter`, `MaxAliasesLimiter` and `QueryDepthLimiter`; the
spec states what was borrowed from them and that the package declines their shape. The reasons
each was declined are here:

- **Three extensions a consumer must remember.** Optional, consumer-installed, none installed by
  default is the same as absent — which is the audit's finding, not an inference from it. One
  policy object and one extension installed by `DjangoSchema` is the answer.
- **`parse_options["max_tokens"]`.** Upstream routes its token limit into graphql-core's parser,
  which answers with a `GraphQLSyntaxError` carrying no code — indistinguishable to a client from
  a typo. This package counts tokens itself so the rejection carries the same typed code as every
  other bound.
- **Depth measured on the AST.** Upstream's `QueryDepthLimiter` is a validation rule, so it runs
  *after* the parse it would need to protect.

### Risks and open questions — the fallback positions

*Moved.* The spec keeps each preferred answer; the fallbacks it would take if a preferred answer
failed are here.

- **`max_collection_cost`'s default is generous by design.** Fallback if deployments report the
  compounding is still too permissive: a per-level multiplier cap, which bounds nesting directly
  rather than through a product.
- **Response-byte accounting is out of scope.** Fallback: the deployment's reverse proxy, which
  already bounds response size.
- **The `ids` argument-name rule** is the walker's one name-based classification. Fallback: a
  marker on the generated field that the walker reads instead of the argument name.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-joint-version-cut]: ../../GLOSSARY.md#joint-version-cut

<!-- docs/SPECS/ -->
[spec-046]: ../spec-046-transport_security-0_0_14.md
[spec-047]: ../spec-047-resource_policy-0_0_14.md
[spec-047-d1]: ../spec-047-resource_policy-0_0_14.md#decision-1--one-immutable-frozen-dataclass-validated-at-construction
[spec-047-d10]: ../spec-047-resource_policy-0_0_14.md#decision-10--per-field-overrides-narrow-the-schema-policy-is-the-trusted-declaration
[spec-047-d11]: ../spec-047-resource_policy-0_0_14.md#decision-11--one-typed-rejection-and-no-per-transport-translation
[spec-047-d12]: ../spec-047-resource_policy-0_0_14.md#decision-12--the-version-bump-belongs-to-the-0014-joint-cut
[spec-047-d13]: ../spec-047-resource_policy-0_0_14.md#decision-13--what-this-policy-does-not-bound-and-why-each-boundary-is-deliberate
[spec-047-d2]: ../spec-047-resource_policy-0_0_14.md#decision-2--threaded-through-the-request-context-mirroring-the-optimizer-seam
[spec-047-d3]: ../spec-047-resource_policy-0_0_14.md#decision-3--the-document-text-scan-runs-before-the-parse
[spec-047-d4]: ../spec-047-resource_policy-0_0_14.md#decision-4--the-document-and-value-budgets-are-one-iterative-walk
[spec-047-d5]: ../spec-047-resource_policy-0_0_14.md#decision-5--default_relation_shape-becomes-connection-a-clean-alpha-break
[spec-047-d6]: ../spec-047-resource_policy-0_0_14.md#decision-6--every-raw-list-is-bounded-at-one-seam
[spec-047-d7]: ../spec-047-resource_policy-0_0_14.md#decision-7--the-policy-is-a-ceiling-over-relay_max_results-never-a-replacement
[spec-047-d8]: ../spec-047-resource_policy-0_0_14.md#decision-8--max_collection_cost-is-a-shape-bound-and-its-default-says-so
[spec-047-d9]: ../spec-047-resource_policy-0_0_14.md#decision-9--the-execution-deadline-is-cooperative-and-says-so

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
