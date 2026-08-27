# Build: Slice 2 — relation-as-Connection reconciliation (spec-032)

Spec reference: `docs/SPECS/spec-032-full_relay-0_0_9.md` (whole file; 689 lines before this pass, 707 after)
Status: final-accepted

Worker-1-only spec-custody slice per the build plan's `## Dispatch shape`: no Worker 2 build pass and no
Worker 3 per-slice review (a Worker 3 pass over the whole spec diff runs after Slice 3). This artifact carries
one combined Plan + Final-verification block. **Zero executable bytes changed — no `.py` file was touched.**

## Plan + Final verification (Worker 1)

### Spec status-line re-verification

Read spec lines 1-11 (title, shipped-in header, `Status:`, Owner, Predecessors, the Slice-0 deliberative-layer
pointer) before acting. Ten of the eleven still describe the build's current state. **One was edited**: the
`Status:` line's Slice-3 summary described the deliverable as "the Phase-2.5 synthesis of `<field>_connection`
**siblings**", which is the pre-`0.0.14` shape — under today's default there is no sibling, the connection
*replaces* the list. Rewritten to "the Phase-2.5 synthesis of a `<field>_connection` for every many-side
relation whose target is Relay-Node-shaped". The card is still `DONE-032-0.0.9`, `Status:` still reads
`**SHIPPED (`0.0.9`)**`, every predecessor doc exists at its cited path, and the companion pointer resolves.

That edit is worth naming as a finding rather than a formality: **the per-spawn status-line check caught a
site the finding sweep would have missed**, because the header states the contract in a vocabulary
(`siblings`) that neither the `"both"` sweep nor the behavior sweep searched for.

### DRY analysis

**Helper inventory checked.** Not applicable, and deliberately so: this slice writes no Python and proposes no
helper. Recorded rather than skipped so a later pass can see the question was asked.

- **Existing patterns reused.** Slice 1's shapes, unchanged: `**Post-ship:**` / `**Build finding (Slice N,
  commit `<sha>`)**` bullets under a companion Decision's `### Changes this Decision underwent`; in-spec
  corrections that state the contract directly and never narrate a chronology; a `**Item N ...**` paragraph
  prepended to the companion's `## Risks and open questions` body for a falsified item.
- **New helpers justified.** None.
- **Duplication risk avoided.** The hazard in a reconciliation slice is a **partial** fix. The default-shape
  claim is restated in five designed-redundant homes plus eight more, and a spec with three of thirteen
  corrected is worse than one with zero, because the reader cannot tell which half is current. The population
  was enumerated mechanically before the first edit and re-swept after the last (Verification 4).

### Findings re-verified against source

Each finding was re-opened at `HEAD` before a word of the spec was changed. All four confirm; **no code defect
was found**, so the escalation path in the slice brief was not taken.

| # | Verdict | Symbol-qualified evidence |
| --- | --- | --- |
| B1 | **Confirmed** | `django_strawberry_framework/types/base.py` #"DEFAULT_RELATION_SHAPE = "connection"". The comment block directly above states the reason verbatim: a raw many-side list "has no cursor and therefore no page of its own, so emitting one BESIDE the bounded connection hands a client a way around the connection's cap by selecting the sibling", and the raw list is now an explicit `Meta.relation_shapes` opt-in that is row-bounded via `resource_policy.py::bounded_rows`. Attributed in-source to **spec-047 Decision 5**. Provenance measured, not assumed: `git log -S 'DEFAULT_RELATION_SHAPE = "connection"' -- django_strawberry_framework/types/base.py` returns exactly `567cc6d0` (2026-08-04, the `0.0.14` security card); the complementary `git log -S 'DEFAULT_RELATION_SHAPE = "both"'` returns `567cc6d0` (removal) and `d418e649` (2026-06-11, the spec-032 build's own introduction). `RELATION_SHAPE_VALUES` is unchanged at `frozenset({"list", "connection", "both"})` — the vocabulary did not change, one member was promoted. `resource_policy.py::bounded_rows` exists and is consumed by `list_field.py` and `types/resolvers.py`. |
| B5 | **Confirmed** | `types/finalizer.py::_synthesize_relation_connections`, read end to end. `finalizer.py` #"_SYNTHESIZED_RELATION_CONNECTION_MARKER = "_dst_synthesized_relation_connection"" is stamped at attach and read on re-entry; the re-entrant branch calls `_suppress_relation_list_form(type_cls, name)` again for a `"connection"` shape **and** `_record_relation_connection(definition, generated, name)` before its `continue`. `types/finalizer.py::_record_relation_connection` lazily initializes and writes `DjangoTypeDefinition.relation_connections` (the slot exists at `types/definition.py` #"relation_connections: dict[str, str] \| None = None"), cited in-source to spec-033 Decision 3. `types/finalizer.py::_register_relation_connection_teardown` registers an identity-safe inverse via `registry.register_type_teardown`, matching only `field_obj` or `field_obj.base_resolver.wrapped_func` and restoring a suppressed annotation only when its slot is still absent. The resolver is built by `connection.py::_build_relation_connection_resolver(target_type, accessor_name, relation_field_name, declaring_type)` — signature read directly — and the call site passes `instance_accessor(field)`, `name`, and the iterated `type_cls`. `utils/relations.py::instance_accessor` documents the `ForeignObjectRel.name` vs `get_accessor_name()` divergence. |
| B7 | **Confirmed, with one correction to the dispatched description** | `examples/fakeshop/apps/library/schema.py`: `GenreType.Meta` #"relation_shapes = {"books": "both"}" (with the in-source comment `explicit raw-list opt-in`), `BookType.Meta` #"relation_shapes = {"genres": "both"}" (its comment states the `0.0.14` default flip outright), `GenreType.Meta` #"interfaces = (relay.Node, Named)", and `LoanType.Meta` #"if getattr(settings, "FAKESHOP_TEST_LOAN_CONNECTION", False):" adding `interfaces = (relay.Node,)` + `connection = {"total_count": True}`, whose class docstring names `test_book_loans_relation_stays_list_only` as the contract it preserves. **The dispatched list says the third `relation_shapes` entry is on `IssueType`; it is on `PeriodicalType`** (`examples/fakeshop/apps/library/schema.py` #"relation_shapes = {"issues": "connection"}", inside `class PeriodicalType`). `IssueType` carries `cursor_field` / `connection` / `orderset_class` and no `relation_shapes` at all. Provenance per key: `"books"`/`"genres"` -> `567cc6d0`; `"issues"` -> `51421e54` (2026-07-10, the keyset-cursor card); `FAKESHOP_TEST_LOAN_CONNECTION` -> `027e653c` (2026-07-23); `Named` -> `0a48ae8c` (2026-06-26). All post-ship. |
| B8 | **Confirmed by reading each body against the sentence it is cited for** | Both dispatched names are absent tree-wide (`grep -rn --include="*.py"` returns nothing for either). `tests/test_relay_connection.py::test_default_connection_only_drops_the_reverse_fk_list_sibling` asserts `"items: [ItemType" not in sdl` **and** `"itemsConnection(" in sdl` — the absence assertion is the load-bearing half and is what the old single test could not have carried. `::test_explicit_both_restores_the_reverse_fk_list_sibling` declares `meta_extra={"relation_shapes": {"items": "both"}}` and asserts `"items: [ItemType" in sdl`. `::test_default_connection_only_covers_both_m2m_directions` asserts the absence + presence pair for `books` (reverse M2M) and `genres` (forward M2M). `tests/types/test_base.py::test_relation_shapes_on_consumer_annotated_relation_raises` passes `namespace_extra={"__annotations__": {"items": "list[str]"}}`; `::test_relation_shapes_on_consumer_assigned_relation_raises` passes a `strawberry.field(resolver=...)`; both assert `"names consumer-authored relation 'items'"` and `"owns that field's shape"`. Every other spec-named Slice-3 and Slice-6 test in the `## Test plan` was checked for existence in the same sweep — all present, no further rename. |

### The `"both"`-default sweep, measured

The default-shape claim is the largest finding in the cycle and it is spelled three different ways, so the
population was derived mechanically rather than from the dispatched list.

**Literal sweep.** `"both"` (with quotes) occurs **16 times** in the pre-pass spec, across 15 lines (one line
carries two). Classified by hand against the surrounding sentence:

| Class | Occurrences | Disposition |
| --- | --- | --- |
| The `{"list", "connection", "both"}` vocabulary enumeration | 3 | Valid, untouched — the vocabulary did not change |
| A legitimate mention of the explicit `"both"` request or value | 3 | Valid, untouched (the explicit-request rejection clause; `test_non_node_target_explicit_raises`; the code sample's own `{"books": "both"}` value, which matches shipped fakeshop) |
| **Asserts or assumes `"both"` is the default** | **10** | **All rewritten** |

**Positive sweep — the claim spelled without the literal.** Three further sites, invisible to the sweep above:

- `## Test plan` Slice 3's `test_default_both_synthesizes_connection_sibling`. The token is `_both_`, not
  `"both"`, and `\bboth\b` does not match either because an underscore is a word character. **A literal sweep
  and a word-boundary sweep both miss it; only reading the section finds it.**
- `## Problem statement` — "gives … a `<field>Connection` **sibling** (with the `Meta.relation_shapes`
  **opt-out**)". No `both` token at all; the whole claim is carried by two nouns.
- `## Edge cases and constraints` — the entry **titled** "Relation shape `"connection"` removing the list
  field". Framing `"connection"` as the exception is itself the falsified claim.

**Total population: 13 sites**, plus the `Status:`-line `siblings` site the status re-verification found
independently = **14**. Post-pass re-sweep in Verification 4.

### Spec sites changed, by content

**20 prose sites plus two link definitions.** Grouped by finding; every site is named by what it says, never
by line number. The 14-site default-shape population measured above accounts for 13 of the B1 entries plus one
that lands under B8 (the `## Test plan` test name, which carried the claim in its own identifier); the
remaining 6 are B5's, B7's, and B8's second entry, which the default sweep never had reason to find.

**B1 — the default relation shape is `"connection"` (11 sites)**

1. `Status:` line, the Slice-3 summary — "`<field>_connection` **siblings**" -> "a `<field>_connection` for
   every many-side relation whose target is Relay-Node-shaped".
2. `## Key glossary references`, the [Relation handling] entry — "the `"both"` default keeps the `list[T]`
   field, so nothing shipped changes shape" was **true when written and falsified by shipped code**. Replaced
   by the current contract: the connection counterparts **replace** the list, and the raw list returns only via
   an explicit `"both"`, row-bounded by `bounded_rows`.
3. `## Slice checklist`, Slice 3's synthesis sub-bullet — the three-shape clause reordered default-first and
   restated; "sibling" -> "field" in the same sentence, because the word was carrying the old contract.
4. `## Problem statement` — "gives … a `<field>Connection` sibling (with the `Meta.relation_shapes` opt-out)"
   -> "**converts** … to a `<field>Connection` (with `Meta.relation_shapes` narrowing per relation)". Both
   nouns were wrong: it is not a sibling and the key is no longer an opt-out.
5. `## Goals` goal 2 — "expose a `<field>Connection` sibling by default (`"both"`) … narrowing per relation to
   `"list"` / `"connection"`" -> the default is `"connection"` (the generated `list[T]` is removed, so the
   connection's page cap is the only way in), narrowed by `"list"` or **widened** by `"both"`. The
   narrow/widen direction is the part a reader most needs and the old sentence had it backwards.
6. `## User-facing API` -> `### Relation-as-Connection upgrade`, the **code sample's inline comment** —
   `# Optional narrowing; "both" is the default …` -> `"connection"` is the default and `"both"` is the
   explicit opt-in that keeps the raw list. The sample's `relation_shapes = {"books": "both"}` **value is
   kept**: it is exactly what shipped fakeshop declares, so the sample now teaches the opt-in rather than
   misnaming the default.
7. The prose beneath that sample — rewritten to say *why* `GenreType` exposes both fields (because it declares
   `"both"`), and what happens without the entry (`books` leaves the SDL entirely). "An eligible relation
   defaults to `"both"`" -> `"connection"`.
8. `### Decision 6`, the lead-in — "synthesizes connection **siblings**" -> "synthesizes the relation
   connections"; "`Meta.relation_shapes` entry, else `"both"`" -> "else `"connection"`".
9. `### Decision 6`, the three shape bullets — reordered default-first, each restated, and a new
   **implementation-relevant** paragraph added beneath them: *why* the default suppresses the list (the cap
   bypass), that `"both"`'s list is row-bounded, and the closing warning that implementing this step as "add a
   connection beside the list" reintroduces the bypass while every test about the connection still passes.
   This stays in the spec under `worker-1.md`'s "the why that changes HOW a thing is built" carve-out — a
   builder who reads only the bullets writes the vulnerability back.
10. `### Decision 7`, the `None`-absent row — "every eligible relation defaults to `"both"` at synthesis time"
    -> `"connection"`.
11. `### Decision 7`, the consumer-authored bullet's closing sentence — "The **implicit** `"both"` default
    continues to silently skip …" -> "The **implicit** default continues to silently skip …, whatever that
    default is". The rule was never about the value; hard-coding the value is what made it rot.

**B1 — Edge cases and DoD (2 sites, counted with the group above's numbering continued)**

12. `## Edge cases and constraints` — the entry titled "**Relation shape `"connection"` removing the list
    field**" retitled to "**The default shape removes the generated list field**" and rewritten so the removal
    reads as the norm, with the consequence stated plainly: an eligible many-side relation is reachable
    **only** through `<field>Connection` unless the type asks for `"both"`. The consumer-override half of the
    old entry is preserved verbatim in meaning.
13. `## Definition of done` item 6 — the parenthetical shape list rewritten default-first, plus B5's contract
    (see below).

**B5 — the Phase-2.5 synthesis's re-entrancy, walker slot, teardown, and resolver arguments (2 sites)**

14. `### Decision 6` gained two new subsections. **"The resolver is built from three arguments, and each one
    is load-bearing"** names the accessor (with the `ForeignObjectRel.name` vs `get_accessor_name()`
    divergence and why every fakeshop fixture masks it), the relation field name (the walker's window
    `to_attr` key — probing the accessor instead silently never hits the windowed page), and the declaring
    type (`type_cls`, not `registry.get(model)`, so a divergent secondary type's strictness key is not
    aliased onto the primary's). **"The step is re-entrant, and that is a contract"** states the marker
    (including the `"connection"`-shape re-suppression a rerun's Phase 2 makes necessary), the walker-readable
    `relation_connections` slot and why it is re-recorded on the re-entrant path, and the identity-safe
    teardown — with *identity-safe* defined, since the whole value of the mechanism is what it declines to
    restore.
15. `## Edge cases and constraints` — new entry, "**Re-entering Phase 2.5 after a partial finalize**", so the
    contract has a home in the section a reader consults for lifecycle corners.
    (`## Definition of done` item 6 also gained the resolver's three arguments and the re-entrancy +
    teardown clause; counted at site 13.)

**B7 — the fakeshop consequences (3 sites)**

16. `## Slice checklist`, Slice 6's schema sub-bullet — now states that `GenreType.books` and `BookType.genres`
    **each carry an explicit `"both"` key**, names them, says why (keeping live coverage of the
    list-beside-connection shape the default removes), and points at `CategoryType.properties` in the products
    app as the keyless type that covers the connection-only default live. `BookType.loans` restated: `LoanType`
    is non-Node **unless the default-OFF `FAKESHOP_TEST_LOAN_CONNECTION` acceptance flag is set**.
17. `## Test plan` Slice 6, `test_book_loans_relation_stays_list_only` — restated against the test's actual
    assertions (`loans` present, `loansConnection` absent, `genresConnection` as positive control), with the
    settings-gate and the flagged suite's teardown re-assertion named, and the observation that this is the
    one shape the post-`0.0.14` default cannot produce by itself.
18. `## Test plan` Slice 6, `test_genre_books_connection_behavior` and
    `test_book_genres_connection_sidecars_and_total_count` — each gained the sentence naming the `"both"` key
    that makes it a proof of the **opt-in** rather than of the default. Without it a reader takes two live
    tests as evidence for a default the package has not had since `0.0.14`.

**B8 — the two renamed test families (2 sites)**

19. `## Test plan` Slice 3 — `test_relation_shapes_on_consumer_authored_relation_raises` replaced by
    `test_relation_shapes_on_consumer_annotated_relation_raises` /
    `test_relation_shapes_on_consumer_assigned_relation_raises`, with a clause saying why there are two (the
    two corners of the override contract).
20. `## Test plan` Slice 3 — `test_default_both_synthesizes_connection_sibling` replaced by the three
    `tests/test_relay_connection.py` tests, with the split explained as the direct consequence of the default
    flip: one additive assertion became a presence **and** an absence, plus a separate test for the opt-in.

**Link definitions:** two added, both used, both alphabetical —
`[relations]` (`django_strawberry_framework/utils/relations.py`, under
`<!-- django_strawberry_framework/ -->`, between `[registry]` and `[relay-toplevel]`) and
`[fakeshop-products-schema]` (`examples/fakeshop/apps/products/schema.py`, under `<!-- examples/ -->`).
Two `[`spec-033`][spec-033]` references drafted mid-pass were **converted to the file's own idiom**
`[`DONE-033-0.0.9`][kanban]` rather than shipped with a new link definition — that is how every other
reference to the sibling card in this spec is spelled, and one new spelling in one paragraph is drift.

### Deleted as never-true or falsified, not moved

Graded against the three cases in the method rules.

- **Case (a), was true, later falsified by shipped code — 13 of the 14 sites.** Every default-shape claim was
  correct at `0.0.9` and is false at `HEAD`. None was moved to the companion as a sentence; the *deliberation*
  behind them is recorded there in the companion's own voice (what the spec predicted, why it predicted it,
  what overrode it), which is the point of the move — a false sentence belongs in neither file.
- **Case (b), never true — none.** No relation-shape claim in this half was wrong when written. Recorded
  explicitly because Slice 1 found one and an empty result reads like an unrun check otherwise.
- **Case (c), true but a forward-looking promise since resolved — none in this half.** `## Definition of done`
  item 1, the one item straddling this slice's symbols, was already fixed in **both** halves by Slice 1 and
  was left untouched per the slice brief. Re-read to confirm, not assumed.

**One passage deleted outright rather than rewritten:** the `## Key glossary references` clause "so nothing
shipped changes shape". Its subject — the additive, no-consumer-edit-required property — ceased to exist at
`0.0.14`, so there is nothing left for a rewrite to be *about*. The claim's history, including that the spec's
own Risks reasoning rested on it, is in the companion.

`## Current state` was **not** rewritten. Its `GenreType (`interfaces = (relay.Node,)` …)` description is
true as of its stated date (the `Named` interface arrived post-ship at `0a48ae8c`), and the section is
explicitly "a true description of the repo as of this writing, before the build". The companion's Decision 12
note records that the file has since changed, so a reader is not left to discover the divergence alone.

### Beyond the handed list

**Worker 0's list was a floor, not a ceiling.** Five items surfaced that it did not carry — one of which was
this pass's own false finding, kept on the record rather than quietly deleted.

1. **B7's owning type is wrong in the build plan.** The `{"issues": "connection"}` entry is on
   `PeriodicalType`, not `IssueType`. Corrected here in the evidence table; the spec never named either type
   for this, so no spec edit was owed — but a later pass re-deriving B7 from the plan would look in the wrong
   class and conclude the finding was fabricated.
2. **The `Status:` line carried the falsified contract in a vocabulary neither sweep searched.** Found by the
   mandatory per-spawn status-line re-verification, not by the finding sweep. Taken here.
3. **The owning spec was read, and this pass's contract text agrees with it — but the check began as a false
   finding and is recorded that way deliberately.** The first pass at this item asserted that `spec-047` has
   no rationale companion in `docs/SPECS/appx/`, on the strength of having seen `spec-030` / `spec-031` /
   `spec-032` companions there. That was **wrong**: `ls docs/SPECS/appx/` lists
   `spec-047-resource_policy-0_0_14-rationale.md` and `-terms.csv`, and
   `docs/SPECS/spec-047-resource_policy-0_0_14.md` carries
   `### Decision 5 — `DEFAULT_RELATION_SHAPE` becomes `"connection"`: a clean alpha break` in full. **A
   sampled directory listing is not a census** — the same defect this cycle exists to catch, caught in this
   cycle's own artifact before it shipped. What the correct read gives is a **positive cross-check**:
   spec-047's Decision 5 says "A raw many-side list emitted beside a bounded connection is not a convenience,
   it is the bypass", records `"both"` as surviving unchanged as an explicit opt-in whose list is now
   row-bounded by its Decision 6 (`resource_policy.py::bounded_rows`), and names the migration as one line per
   relation discovered at schema build. Every one of those clauses matches what this pass wrote into
   spec-032's Decision 6 and `## Goals`, independently derived from source before spec-047 was opened. **No
   action is owed** and nothing is routed.
4. **Three `.py` comment/docstring sites still spell the pre-`0.0.14` default.** All three are in files this
   slice may not touch (Slice 3 owns `.py` comment repairs), so they are **routed with replacement text**, not
   taken — see the Notes section. They are real: a reader who greps for the default and lands on a test
   docstring gets the wrong answer with no signal that it is stale.
5. **A `.py` comment names a field that does not exist.** `examples/fakeshop/apps/library/schema.py`
   `BookType.Meta` #"``ItemType.properties`` in the products app" — `properties` is a reverse relation on
   **`Category`** (`related_name="properties"` in `examples/fakeshop/apps/products/models.py`), and
   `CategoryType.Meta`'s own comment correctly says `properties` deliberately stays on the default.
   `ItemType` has no `properties` field at all. Routed to Slice 3 with replacement text. Found only because
   the spec edit at site 16 cites that same type as the live default-shape proof, and the citation was
   re-derived instead of copied — **a catalog is a claim; re-derive it before citing it.**

### Verification

**1. Glossary gate — exits 0, unchanged term count.**

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-032-full_relay-0_0_9.md
OK: 40 terms - all have glossary entries and at least one spec link.
EXIT=0
```

Same 40 terms Slices 0 and 1 measured. Expected: this pass added no new glossary-linked term and removed none.
The two link definitions it added point at source files, not `GLOSSARY.md` anchors.

**2. Markdown scaffold gate — exits 0 on both files.**

```
$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-032-full_relay-0_0_9.md \
    docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md
EXIT=0
```

**3. Anchors, link definitions, and the definition block — checked mechanically on both files.**

```
$ uv run python <scratch>/anchorcheck.py docs/SPECS/spec-032-full_relay-0_0_9.md \
    docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md
slugger fixtures: 5/5 pass

=== docs/SPECS/spec-032-full_relay-0_0_9.md: 0 problem(s)

=== docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md: 0 problem(s)
EXIT=0
```

| Check | `spec-032` | `...-rationale.md` |
| --- | --- | --- |
| Dangling in-page `](#...)` anchors | none | none |
| Duplicate link definitions | none | none |
| `[ref-id]` uses with no definition | none | none |
| Definitions never used | none | none |
| Definition paths missing on disk | none | none |
| Definition cross-file anchors missing | none | none |
| `<!-- LINK DEFINITIONS -->` present | yes | yes |
| All 10 canonical group headers, in `START.md` order | yes | yes |

**The slugger trap, guarded the way Slices 0 and 1 learned to guard it.** The checker slugs each whitespace
character **individually** and never `re.sub(r'\s+', '-', ...)`: GitHub turns " — " into **two** hyphens once
the em-dash is stripped, so a run-collapsing substitution reports a false dangling on every
`decision-N--title` anchor. Five known-good headings are asserted before any count is believed, and the script
`sys.exit(2)`s on a fixture mismatch rather than reporting zero problems.

**The control was proved failable, not merely observed passing.** A scratch copy outside the repo was mutated
three ways — one `](#decision-6--...)` anchor pointed at a nonexistent heading, the `[relations]` definition
retargeted at a nonexistent path, and the `<!-- .venv/ -->` group header deleted — and the checker reported
all three by name (`dangling in-page anchor #decision-6--nope`, `definition [relations] -> missing path
.../NOPE.py`, `group headers wrong/missing: [... no '<!-- .venv/ -->' ...]`) and exited 1. The mutant run also
emitted ~77 additional path failures, which are an **artifact of the copy's location** (every relative
definition resolves outside the repo from there), not findings — named here because an unexplained count
difference between the clean run and the failability run is exactly how an instrument bug gets read as a
finding. The scratch tree was deleted after the proof.

**4. Post-pass sweep of the `"both"`-default population.** Re-run after the last edit, same instrument as the
pre-pass count. Every number below was **measured at the moment it was written**, and the first draft of this
subsection got three of the four wrong by predicting them — the counts went **up**, not down, which is the
correct outcome for a pass whose whole job is to say `"both"` is an opt-in in every place it used to say
`"both"` is the default.

- `"both"` now occurs **22 times** in the spec (up from 16). Each occurrence was printed with 110 characters of
  surrounding context and classified: **3** are the `{"list", "connection", "both"}` vocabulary enumeration
  (unchanged from the pre-pass count — the vocabulary never moved), and **19** name `"both"` as the explicit
  opt-in, an explicit request, or a shipped fakeshop key value. **Zero assert or assume it is the default.**
  The 6-occurrence increase is entirely new text this pass wrote (the Decision-6 reasoning paragraph, the
  User-facing-API prose, the Slice-6 checklist's two named keys, and three Test-plan clauses).
- `_both_`: **2**, both inside the current test names `test_explicit_both_restores_the_reverse_fk_list_sibling`
  and `test_default_connection_only_covers_both_m2m_directions`. Zero legacy —
  `test_default_both_synthesizes_connection_sibling` is gone.
- `sibling`: **8 occurrences across 7 lines**, and **zero** carry the relation-shape contract. Six are
  unrelated ("sibling card `DONE-033`" ×2, "typed batch sibling" ×2, "the sibling of the same-shaped
  `connection.py`", and this pass's own "a client selects the sibling instead", which describes the `"both"`
  list correctly); the other two are the literal `..._list_sibling` suffixes inside the two shipped test names.
- `opt-out`: **2**, at `### Error shapes`' collision bullet and Decision 6's collision paragraph. Both name
  `relation_shapes = {"<field>": "list"}`, which genuinely **is** an opt-out — from the connection. Correct as
  written.

**5. Byte counts.**

| File | Before this slice | After |
| --- | --- | --- |
| `docs/SPECS/spec-032-full_relay-0_0_9.md` | **157,923** bytes / 689 lines | **165,828** bytes / 707 lines |
| `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md` | **85,123** bytes / 439 lines | **97,055** bytes / 455 lines |

Spec `+7,905`, companion `+11,932`. **The companion grew more than the spec, and that is the correct shape for
this slice**: B1 is a reversal, and a reversal's spec-side cost is bounded (each falsified sentence is replaced
by one true sentence) while its companion-side cost is not (the superseded justification, the falsified
additive argument, the rejected-alternative-later-adopted, and the falsified Risks item all have to be written
from scratch). Contrast Slice 1, where the spec grew more than the companion because those findings were
*additions* the spec never carried. This measures **this pass** — Slice 3 changes both files again, so it is
not a claim about either file's size at any later date.

**6. Tool runs after edits.** `uv run ruff format .` — `434 files left unchanged`. `uv run ruff check --fix .`
— `All checks passed!`. Both are no-ops confirming zero `.py` files were touched. No `pytest` was run, per
`AGENTS.md` and the Worker 1 role file; no `--cov*` flag was used anywhere in this pass.

**7. Working tree.** `git status --short` after the pass:

```
 M docs/SPECS/spec-032-full_relay-0_0_9.md
?? 0_0_14.md
?? docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md
?? docs/builder/bld-032-slice-0-rationale_extraction.md
?? docs/builder/bld-032-slice-1-root_field_surface.md
?? docs/builder/build-032-full_relay-0_0_9.md
```

Exactly the two in-scope spec paths, plus this cycle's prior artifacts and Worker 0's build plan (all still
untracked), plus the maintainer's concurrent untracked `0_0_14.md`, which was neither read as instruction nor
touched. **The eleven staged `docs/builder/bld-031-*.md` deletions the build plan's pre-flight recorded are no
longer in `git status` — the maintainer committed that cohort during this cycle.** Nothing was reverted; no
`.py`, no sibling spec, no closeout or agentflow doc was edited. This artifact itself is the fourth in-scope
path and appears once written.

### Companion appends (this pass)

Seven bullets and one paragraph, all appends — no existing companion text was rewritten (the file is
append-only during the cycle):

- **Decision 6**, `### Changes this Decision underwent` — five bullets. One `**Post-ship:**` bullet for the
  default flip (`567cc6d0`, spec-047 Decision 5) carrying three sub-records: the superseded justification, the
  falsified additive/non-breaking argument, and the **rejected alternative later adopted**. That last one is
  qualified rather than dropped: the *naming* half of "a `<field>s_connection`-free naming scheme" was **not**
  adopted (the field is still `<field>Connection`), and the removal was adopted on a cap-bypass argument the
  Revision-1 deliberation never weighed — the breaking-change objection was correct and was **overridden**,
  not found wrong. One `**Build finding (Slice 3, `d418e649`)**` bullet for the re-entrancy marker (verified
  present in that commit's `finalizer.py`, so it is the card's own and not post-ship). One `**Post-ship:**`
  bullet for the two obligations the bare marker skip lacked (`c3767495`, naming pass `77d923ab`) with the
  rejected unconditional-restore alternative. One for the resolver's three arguments, splitting `1f16d963`
  (the card's own `instance_accessor` fix) from `75035bdc` (spec-033's field-name + declaring-type + slot).
  One for the B8 renames and why one test became three.
- **Decision 7** — one `**Post-ship:**` bullet recording that the two sentences here carrying `"both"` state
  **rules that are untouched by the flip**; only the value moved, which is why the spec now names the rule
  without hard-coding the value and why the dated Revision-3-P2 sentence above is left as written.
- **Decision 12** — two `**Post-ship:**` bullets: the library activation's two explicit `"both"` keys and why
  they are opt-ins rather than the narrowings they look like, with `CategoryType.properties` named as the
  keyless counterpart; and the `PeriodicalType` / `FAKESHOP_TEST_LOAN_CONNECTION` / `Named` arrivals with
  their commits, including why the loan flag exists (to keep this Decision's own graceful-degradation proof
  intact).
- **Risks and open questions** — one paragraph on item 9, whose preferred answer contained the falsified
  sentence verbatim. Graded honestly: the item's *analysis* was right (removing a generated list relation is
  consumer-visible; the failure is loud at schema build) and its *prediction* was wrong (it assumed
  consumer-visibility would decide the question; a later card decided it on a threat the item did not have in
  view). Same failure shape as item 7, which Slice 1 recorded, from the opposite direction.

### Notes for Worker 1 (spec reconciliation)

1. **Three `.py` comment/docstring sites still spell the pre-`0.0.14` default. Named owner: Slice 3**, which
   already owns this cycle's `.py` comment repairs. Replacement text recorded so it cannot be lost:
   - `tests/test_relay_connection.py` #"# Default "both": connection siblings per eligible relation kind" —
     a section banner directly above the three renamed tests, which now assert the opposite. Replace with
     `# Default "connection": the list sibling is dropped; "both" opts it back in`.
   - `tests/types/test_base.py::test_relation_shapes_on_consumer_annotated_relation_raises` docstring —
     "(The implicit `"both"` default still skips consumer-authored relations silently - only the explicit key
     fails loud.)" Replace `implicit `"both"` default` with `implicit default`; the rule is value-independent,
     which is exactly the fix applied to the spec's Decision 7.
   - `examples/fakeshop/test_query/test_library_api.py::test_book_loans_relation_stays_list_only` docstring —
     "no ``loansConnection`` is synthesized under the implicit ``"both"`` default because the target is not
     Relay-shaped". Replace `implicit ``"both"`` default` with `implicit default`. The reason clause (non-Node
     target) is correct and stays.
2. **A `.py` comment names a field that does not exist. Named owner: Slice 3.**
   `examples/fakeshop/apps/library/schema.py` `BookType.Meta` #"``ItemType.properties`` in the products app is
   deliberately left on the default so the connection-only shape is covered live too." The field is
   `CategoryType.properties` (`Category` is the `related_name="properties"` target in
   `examples/fakeshop/apps/products/models.py`); `ItemType` has no `properties`. `CategoryType.Meta`'s own
   comment already gets it right, so this is a single-site typo in a cross-reference. Replace `ItemType` with
   `CategoryType`. **This matters beyond tidiness**: the spec's Slice-6 checklist now cites
   `CategoryType.properties` as the live proof of the connection-only default, so the two must agree.
3. **The build plan's B7 description names the wrong type** (`IssueType` for `{"issues": "connection"}`; it is
   `PeriodicalType`). Corrected in this artifact's evidence table. No spec edit is owed — the spec names
   neither type for this — but the Worker 3 pass over the whole spec diff should not re-derive it from
   scratch, and the plan is Worker 0's file.
4. **No code defect was found.** All four findings re-verified as *spec* staleness, not a skipped or dropped
   contract, so the escalation path in the slice brief was not taken and `Status: final-accepted` is set.

### Test additions / updates

None. This slice changes zero executable bytes, adds no source and no test, and runs no `pytest` per
`AGENTS.md`. The `## Test plan` **section of the spec** was re-pointed at five tests, every one of which
**already exists** at `HEAD` — verified by `grep -rn "def <name>" --include="*.py"` per name against
`tests/test_relay_connection.py` and `tests/types/test_base.py`, and by reading each body against the
sentence it is now cited for. No test name was invented. Every other spec-named Slice-3 and Slice-6 test was
swept for existence in the same pass; all present.

### Spec slice checklist (verbatim)

Not applicable. This cycle's Slice 2 is a reconciliation slice defined by the build plan, not an entry in the
spec's own `## Slice checklist` (which carries the seven shipped build slices 1-7). There are no verbatim
sub-checks to copy, tick, or audit. Recorded explicitly rather than omitted, so the absence reads as a
decision.

### Implementation discretion items

None. Every choice in a spec-custody pass is the custodian's; nothing was delegated.

### Summary

The relation-as-Connection half of `spec-032` now states the contract the code implements. Four findings were
re-verified against `HEAD` before any edit — all four confirm, **no code defect**, and one (B7) had the wrong
owning type in the dispatched list (`PeriodicalType`, not `IssueType`). The headline is B1: the default
relation shape flipped `"both"` -> `"connection"` at `567cc6d0`, so the connection **replaces** the generated
`list[T]` rather than joining it. The claim's population was measured rather than accepted: 16 literal
`"both"` occurrences of which **10 asserted the old default**, plus 3 sites carrying the claim with no
matching token (a test name using `_both_`, a `sibling`/`opt-out` sentence, and an Edge-case *title*), plus a
14th found by the mandatory status-line re-verification. All 14 rewritten, across `Status:`,
`## Key glossary references`, `## Slice checklist`, `## Problem statement`, `## Goals`,
`## User-facing API` (code comment included), Decisions 6 and 7, `## Edge cases and constraints`,
`## Test plan`, and `## Definition of done`. Two consequences landed as contract rather than history: the
additive/non-breaking argument is gone from the spec (its subject ceased to exist) and Decision 6's rejected
"replace the list wholesale" alternative is qualified in the companion as a **rejection later overridden**,
with the naming half explicitly not adopted. B5 added the re-entrancy contract, the walker slot, the
identity-safe teardown, and the resolver's three arguments to Decision 6 + Edge cases + DoD; B7 corrected the
Slice-6 checklist and three Test-plan bullets so a reader can find the code they describe; B8 re-pointed two
renamed test families after reading each body against its sentence. Five items beyond Worker 0's list
surfaced — two taken here, two routed with named owners, and one that was **this pass's own false finding**
(a claimed missing `spec-047` rationale companion; the file exists, and the correct read turned it into a
positive cross-check that spec-047's Decision 5 and this pass's independently-derived text agree clause for
clause). Spec 157,923 -> 165,828 bytes; companion
85,123 -> 97,055. Both gates exit 0, the anchor checker is clean on both files **and was proved failable**,
and zero `.py` files were touched.

### Spec changes made (Worker 1 only)

All within `docs/SPECS/spec-032-full_relay-0_0_9.md` and its companion
`docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md`, all triggered by this cycle's Slice 2. Sites are
named by content per `AGENTS.md`; the per-finding breakdown is in `### Spec sites changed, by content` above
and is not repeated here.

1. **B1 (default `"both"` -> `"connection"`)** — 13 spec sites, one of them a deletion. Reason:
   `types/base.py::DEFAULT_RELATION_SHAPE` is `"connection"` and has been since `567cc6d0`; the spec stated
   the old default in five designed-redundant homes plus eight more, and a half-reconciled spec is worse than
   an un-updated one.
2. **B1 corollary** — `## Key glossary references`' "so nothing shipped changes shape" deleted rather than
   rewritten. Reason: the additive property it asserts no longer exists, so there is nothing for a
   replacement sentence to be about.
3. **B5 (re-entrancy, walker slot, teardown, resolver arguments)** — 2 spec sites (plus the DoD clause).
   Reason: four consumer- or maintainer-visible mechanisms the spec described nowhere, one of which
   (`finalize_django_types` re-callability) the spec's own predecessor sections rely on.
4. **B7 (fakeshop)** — 3 spec sites. Reason: the Slice-6 checklist and two Test-plan bullets described an
   implicit upgrade where the code now carries explicit opt-in keys, so a reader could not find the code
   they describe.
5. **B8 (test renames)** — 2 spec sites, 2 names replaced by 5. Reason: neither dispatched name exists at
   `HEAD`; each replacement was verified by reading the test body, not by matching the name.
6. **Status-line re-verification** — 1 spec site (the `Status:` line's Slice-3 summary). Reason: it described
   the deliverable as `<field>_connection` **siblings**, the pre-`0.0.14` shape.
7. **Link definitions** — `[relations]` and `[fakeshop-products-schema]` added, both used, both alphabetical;
   two draft `[spec-033]` references converted to the file's own `[`DONE-033-0.0.9`][kanban]` idiom rather
   than shipping a third spelling.
8. **Companion** — seven append-only bullets under Decisions 6 / 7 / 12 and one paragraph under
   `## Risks and open questions`; three link definitions added
   (`[fakeshop-library-schema]`, `[fakeshop-products-schema]`, `[spec-032-current-state]`). No existing
   companion text was rewritten.

No source or test file was edited. No sibling spec was edited. No closeout or agentflow doc was edited.

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
