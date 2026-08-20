# Rationale: spec-026 — Scalar conversion end-to-end coverage in the fakeshop example (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-026-scalar_conversion_fakeshop-0_0_7.md`][spec-026]. The spec is the contract and states only what holds; everything that explains **how it got there** lives here — the alternatives each decision rejected, every change a decision has undergone, and every claim a decision once made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass, run late: the original `026` cycle never performed pre-flight step 7, so this file did not exist until the residual-completion cycle described below.

## How this file is keyed to the spec

**Every entry names the spec decision or section it belongs to by heading and anchor.** An entry naming no decision cannot be looked up and is worthless however well argued ([`docs/builder/BUILD.md`][build] `## Spec rationale extraction`). Each entry below therefore opens with the spec heading it keys to and carries, for that decision:

- the text as the spec carried it, quoted, when this pass cut it out;
- the alternatives rejected, and the one-line reason each lost;
- every change the decision has undergone;
- any claim the decision once made and may no longer make, stated as a claim rather than as prose the reader must infer is dead.

Entries are titled by the finding id the cycle's verification pass assigned (`D4`, `D5`, …), because those ids are how the cycle's artifacts address them. The id is an address, never the content: each entry is readable without the artifact that numbered it.

## Ship provenance

The card shipped in the joint `0.0.7` cut across **four** commits, all dated 2026-05-27, each attributed in its message to the **pre-renumber** card id `DONE-048-0.0.7` (the 2026-07-30 board renumber moved the card to `026` in [`KANBAN.md`][kanban], so `git log --grep 'DONE-026'` finds none of them). Two of the four carry the `Part of DONE-048-0.0.7.` formula and are the substrate:

| Commit | Subject | Shape |
| --- | --- | --- |
| `2701eb88` | Add apps.scalars with paired-model converter coverage substrate | 10 files, +753/-1 |
| `cae2d5a3` | Add Patron.lifetime_fines_cents BigInt to the library example | 4 files, +58/-1 |

The other two are `a5c89c98` (the live-first package-test retirement) and `45a8f301` (the standing-docs wrap). [`D12`](#d12--the-cards-footprint-is-four-commits-not-two) carries the classification rule, the eight `--grep` candidates it was applied to, and why the other four are not the card's — **a count of commits using the `Part of` formula is not a count of the card's commits**, and reading it as one is what left the card's doc obligations and its test retirement out of the contract.

The spec section that carried the card's claims before the reconstruction was a near-verbatim lift of `2701eb88`'s commit message body (`## Other`, since dissolved — see [`## Key forwarding`](#key-forwarding--the-spec-section-each-earlier-entry-now-keys-to)). That lineage is the direct cause of both entries recorded immediately below: each defect was present in the commit message first and was copied into the spec unexamined.

## Provenance of this record

**This pass performed a MOVE, not a reconstruction.** The block quoted under `### Text as the spec carried it` in the `D4` entry was cut from the spec by this pass; it is not written from memory. The `D5` entry is new material — the original cycle wrote no change record because it never ran this pass — and every number in it is measured against the ship commit, not inherited.

Byte counts, `wc -c` at this working tree, the spec clean against `HEAD` (`ddf8bbaf`) before the cut:

| File | Before the move | After the move | At the integration pass |
| --- | --- | --- | --- |
| `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` | 3,593 | 3,668 | 21,567 |
| `docs/SPECS/appx/spec-026-scalar_conversion_fakeshop-0_0_7-rationale.md` | 0 (did not exist) | 17,340 | 36,728 |

Every figure here was produced by writing this table with fixed-width digit placeholders, running `wc -c` on the files, then substituting equal-width digits, so the substitution cannot move the number it reports. The **After the move** column measures this pass alone; the reconstruction and the entries appended after it are what separate it from the third column, and neither is a second move.

**The spec grew by 75 bytes, and that is the expected result here.** A 3.6KB stub carries one clause of deliberation to move; the one-line pointer the move requires ([`worker-1.md`][worker-1] `### Performing the rationale move` rule 1) plus its link definition cost more than the clause removed. The move's purpose on a stub is that a falsified justification stops being readable as contract, not that the spec shrinks.

**Moved** — cut from the spec by this pass, and now only here:

- the exclusivity justification for the paired-model shape: the phrase `upstream code paths no other example app reaches` and the five-item list that followed it. Recorded under [`D4`](#d4--the-upstream-code-paths-no-other-example-app-reaches-justification).

**Stayed in the spec** — deliberation-shaped text the [`worker-1.md`][worker-1] implementation-relevant carve-out keeps:

- **`The pairing is deliberate (not a single model with paired fields)`**, with the three surviving true fragments of the list. It is why the app has two models rather than one, so a reader who removes it removes the reason the second model exists. Only the exclusivity framing and the two falsified list items left.
- The whole enumerated test list. It is the card's test plan, which is contract, and its defect (`D5`) is an omission rather than a falsehood — the eight bullets present are each true.

**Deleted, not moved** — prose the current facts have falsified, per [`worker-1.md`][worker-1] `### Performing the rationale move` rule 2:

1. "Django's two-`CreateModel` initial migration path" — false as an exclusivity claim on the day it was written (see `D4`) and false as a description now: the initial migration beside [`apps/scalars/models.py`][scalars-models] carries five `CreateModel` operations plus an `AddField`, against two at ship. A builder can implement a sentence like this; it belongs in neither file.
2. "and `SET_NULL` ondelete behavior" as the fifth exclusivity item. The same claim survives in three `.py` sites and is retired there by the cycle's code slice; the reason it is retired is a separate finding and is not this entry's to record.

The falsified sentences are quoted inside the `D4` entry below, where they are unambiguously labelled as claims the spec may no longer make. That is the sanctioned form: a rationale file records a dead claim so the next reader cannot revive it, and the spec carries no trace of it.

## D4 — the "upstream code paths no other example app reaches" justification

**Keys to:** [`## Other`][spec-026-other] in [`spec-026-scalar_conversion_fakeshop-0_0_7.md`][spec-026] — the bullet beginning `The pairing is deliberate`.

**This is the load-bearing entry in this file.** It records a claim the spec made, that the spec may no longer make, and that was *already false on the day it was written* — not drift, but an unmeasured assertion that a later measurement contradicted.

### Text as the spec carried it

> The pairing is deliberate (not a single model with paired fields). It exercises **upstream code paths no other example app reaches**: Django's two-`CreateModel` initial migration path, the registry / `finalize_django_types()` resolving sibling `DjangoType` classes in one app, Strawberry type registration across sibling types in one schema build, the optimizer planning across two managed models in one query, and `SET_NULL` ondelete behavior.

(The two reference-style glossary link ids the spec carried inside this sentence are rendered as plain code spans in the quote, so this file does not inherit two link definitions whose only use is a quotation.)

### Why the exclusivity claim is false, measured at the ship commit itself

`apps/library` was in the tree when `apps/scalars` landed — `git ls-tree --name-only 2701eb88 examples/fakeshop/apps/` lists exactly `library`, `products`, `scalars` — and it already reached four of the five named paths:

| Named path | Measured at `2701eb88` | Instrument |
| --- | --- | --- |
| two-`CreateModel` initial migration | `apps/library/migrations/0001_initial.py` carries **7** `CreateModel` operations | `git show 2701eb88:… \| grep -c 'migrations.CreateModel'` |
| `finalize_django_types()` across sibling `DjangoType` classes in one app | [`apps/library/schema.py`][library-schema] declares **7** sibling `DjangoType` classes in one module | `git show 2701eb88:… \| grep -E '^class '` |
| Strawberry registration across sibling types in one schema build | same 7 types, one schema build | as above |
| optimizer planning across two managed models in one query | [`apps/library/models.py`][library-models] declares **8** models, related through non-null FK chains | `git show 2701eb88:… \| grep -cE '^class .*models\.Model'` |
| `SET_NULL` ondelete | genuinely unique at ship — one non-comment `SET_NULL` in `examples/fakeshop/apps/*/models.py` | `git grep 'SET_NULL' 2701eb88 -- 'examples/fakeshop/apps/*/models.py'` |

`apps/products` reached the same four independently: 4 models and 4 `DjangoType` classes at that commit.

So four of five items were false the moment the sentence was written, and the fifth is false at `HEAD`. The whole claim was **inherited from `2701eb88`'s commit message without measurement**; nothing in the cycle ever counted the sibling app it was implicitly compared against.

### What is true instead, and is still true

What no other example app carries is the **per-column nullable / non-null converter mirror**: an all-nullable twin of an all-required model over an identical column set, so both branches of one `SCALAR_MAP` row — the `NON_NULL` wrapper and the bare `SCALAR` — are exercised by one live round-trip against the same column name.

Measured across the whole example tree at `HEAD` by comparing each model's non-relational column-name set and its per-column `null=True` flags:

```python
import ast, pathlib
REL = {"ForeignKey", "ManyToManyField", "OneToOneField"}
cols, flags = {}, {}
for p in sorted(pathlib.Path("examples/fakeshop/apps").glob("*/models.py")):
    for node in ast.parse(p.read_text()).body:
        if not isinstance(node, ast.ClassDef):
            continue
        names, nulls = [], []
        for st in node.body:
            if isinstance(st, ast.Assign) and isinstance(st.value, ast.Call):
                f = ast.unparse(st.value.func)
                if f.startswith("models.") and f.split(".")[-1] not in REL:
                    names.append(st.targets[0].id)
                    nulls.append(any(
                        k.arg == "null" and getattr(k.value, "value", None) is True
                        for k in st.value.keywords
                    ))
        if names:
            key = f"{p.parts[3]}.{node.name}"
            cols[key], flags[key] = frozenset(names), (all(nulls), not any(nulls))
print("all-nullable models:", [k for k, v in flags.items() if v[0]])
keys = list(cols)
for i, a in enumerate(keys):
    for b in keys[i + 1:]:
        if cols[a] == cols[b]:
            print(a, flags[a], "<->", b, flags[b])
```

Result: of **48** example models carrying concrete columns, `scalars.NullableScalarSpecimen` is the **only** all-nullable one, and `scalars.ScalarSpecimen` <-> `scalars.NullableScalarSpecimen` is the **only** identical-column-set pair (11 columns) whose two halves are all-non-null and all-nullable respectively. The five other identical-column-set pairs in the tree are all-non-null on both sides.

The measurement is written out rather than asserted because the claim it replaces failed for exactly the opposite reason: nobody measured the tree it quantified over.

### Alternatives rejected

- **One model with paired `_required` / `_nullable` columns per scalar.** Lost because the two columns would be *different* `SCALAR_MAP` rows' outputs sitting side by side, not the two branches of one row: nothing in the response would pin that the same converter entry produces `NON_NULL` in one shape and bare `SCALAR` in the other. The mirror-over-identical-column-names shape is what makes the introspection assertions meaningful, and it is the shape the code shipped.
- No further alternative is recoverable from the record. The spec, the two commit messages, and the source carry no trace of a third shape having been weighed, and this entry does not invent one.

### Changes this decision has undergone

1. **At ship (`2701eb88`)** — written as a five-item exclusivity claim, unmeasured.
2. **This pass** — the exclusivity framing and its two falsified items cut from the spec; the three surviving true fragments kept there as the reason the pairing exists; the corrected, measured claim recorded here.

### Claims this decision may no longer make

- That the paired-model shape exercises **upstream code paths no other example app reaches**. It does not, and did not at ship: `apps/library` and `apps/products` both reached four of the five named paths first.
- That `apps/scalars` is the example tree's **two-`CreateModel` initial migration** case. Its initial migration carries five `CreateModel` operations plus an `AddField` at `HEAD`.

## D5 — the enumerated test list is one test short, and was at ship

**Keys to:** [`## Other`][spec-026-other] in [`spec-026-scalar_conversion_fakeshop-0_0_7.md`][spec-026] — the second bullet's `eight live HTTP tests` count and the eight enumerated test bullets that close the section.

### The measurement

`2701eb88:examples/fakeshop/test_query/test_scalars_api.py` shipped **nine** test functions (`git show 2701eb88:… | grep -c '^def test_'` -> `9`):

1. `test_scalar_specimen_every_field_wire_format_over_http`
2. `test_scalar_specimen_bigint_negative_signed_round_trip`
3. `test_scalar_specimen_bigint_zero_serializes_as_string`
4. `test_scalar_specimen_self_referential_parent_children_over_http`
5. `test_scalar_specimen_introspects_bigint_scalar_for_both_fields`
6. **`test_scalar_specimen_introspects_json_scalar_in_both_shapes`** — the one the spec omits
7. `test_nullable_scalar_specimen_all_null_wire_format_over_http`
8. `test_nullable_scalar_specimen_partner_fk_linkage_over_http`
9. `test_scalar_specimen_nullable_partners_reverse_relation_over_http`

The spec's list enumerates eight, and the one absent from it is the JSON-scalar introspection test — the exact sibling of the `BigInt` introspection bullet the spec does carry.

### Where the miscount came from

Not from the spec. `2701eb88`'s own commit message writes the header `Tests in test_query/test_scalars_api.py (8 tests):` and then lists **nine** bullets, including `JSON scalar introspection in both shapes`. The spec lifted the header's count and dropped one bullet from the list, so both halves of the error are inherited: the wrong number came from the commit message verbatim, and the missing bullet was lost in the lift.

This is the same lineage as `D4`, and it is why the `## Other` section cannot be treated as an audited contract: it is a commit message with headings, and the commit message was itself unaudited.

### Scope of the measurement

The nine-test figure describes the **card's** contract at its ship commit. [`test_query/test_scalars_api.py`][scalars-tests] carries **29** test functions at `HEAD`; the twenty added since belong to later cards and are outside this spec's contract. Any future re-derivation of this entry must count at `2701eb88`, not at `HEAD`.

### Alternatives rejected

None. There is no design question here — the count is either right or wrong, and it is wrong.

### Changes this decision has undergone

1. **At ship** — the commit message miscounts nine bullets as eight.
2. **At spec authoring** — the count and eight of the nine bullets copied over; the JSON-introspection bullet dropped.

### Claims this decision may no longer make

- That the card shipped **eight** live HTTP tests. It shipped nine.
- That the enumerated list is the card's complete live-test surface. It is missing `test_scalar_specimen_introspects_json_scalar_in_both_shapes`.

## Entry shape for entries appended after this pass

The residual-completion cycle's verification pass assigned ten finding ids, `D1` through `D10`. Two of them — `D4` and `D5` — are recorded above. The rest are spec-reconstruction findings and append here under the same entry shape, keyed the same way: spec heading and anchor first, then rejected alternatives with the reason each lost, then the change record, then the claims the decision may no longer make. The file is append-only during a build ([`worker-1.md`][worker-1] `### Performing the rationale move` rule 4); an entry added later never edits one already here.

Two constraints hold for every entry appended:

- **Re-derive, do not inherit.** Every count in both entries above was wrong or unmeasured in the source it came from. A number taken from a build plan, a commit message, or an earlier entry of this file is a claim, not a measurement.
- **A measurement outlives its prose.** Each entry states the instrument that produced its numbers, so a later reader can re-run it rather than trust it. `D4`'s central claim failed precisely because it quantified over a population nobody counted.

## Key forwarding — the spec section each earlier entry now keys to

**Keys to:** the whole of [`spec-026-scalar_conversion_fakeshop-0_0_7.md`][spec-026].

The `D4` and `D5` entries above open by keying to the spec's `## Other` section. **That section no longer exists.** It was a lift of one commit message's body under a heading, which is why both of the defects those entries record were invisible to it, and the spec reconstruction dissolved it into the builder-format sections a reader can audit the shipped code against.

The two entries above are not edited to say so — this file is append-only during a build ([`worker-1.md`][worker-1] `### Performing the rationale move` rule 4), and an argument is not improved by being rewritten under a new address. This table is the address change, and it is the authoritative one:

| Entry | Keyed to | Now carried by |
| --- | --- | --- |
| [`D4`](#d4--the-upstream-code-paths-no-other-example-app-reaches-justification) | `## Other`, the bullet beginning `The pairing is deliberate` | `## Architectural decisions` -> `### Decision 1 - Paired models, not one model with paired columns` |
| [`D5`](#d5--the-enumerated-test-list-is-one-test-short-and-was-at-ship) | `## Other`, the `eight live HTTP tests` count and the eight enumerated bullets | `## Test plan` -> the nine-test subsection for `test_query/test_scalars_api.py` |

The `[spec-026-other]` link definition at the foot of this file is left exactly as it stands, for the same append-only reason. Its `#other` fragment no longer resolves; the link still opens the spec, and this table says where to read next. Every entry appended from here on keys to a heading that exists.

## D1 — why the spec has the sections it has

**Keys to:** the whole of [`spec-026-scalar_conversion_fakeshop-0_0_7.md`][spec-026] — its section structure.

### The state being replaced

The spec was a 3,668-byte stub carrying a title, `## Card snapshot`, a `## Planning note` whose entire body was the word `shipped`, and `## Other`. It carried no `## Architectural decisions`, and no `## Slice checklist`, `## Test plan`, `## Doc updates`, or `## Definition of done` either. Its own preamble instructed the reader to "expand it into the full builder-format spec ... before implementation work starts from this file", a precondition the ship commits made moot in May 2026.

The consequence was not cosmetic. A reader auditing the shipped code against this spec had **nothing to audit against**: no statement of what must be true, and therefore no way to answer "was anything skipped?" — which is the question the residual cycle exists to answer.

### The decision

Model the section structure on the nearest peers rather than invent one: [`spec-021-apps-0_0_7.md`][spec-021] for section order and per-section shape (same `0.0.7` cut, same builder era, closest structural match), and [`spec-013-real_m2m_coverage-0_0_4.md`][spec-013] for two specific shapes — the trimmed two-bullet `## Card snapshot`, and the closing paragraph that attributes an example app's later growth to the cards that added it.

Proportionality is part of the decision. This is an example-app coverage card, not a package-surface card: it ships no public symbol, no settings key, and no consumer-visible behavior, so it earns six architectural decisions rather than `spec-021`'s eight, and a thirteen-item definition of done rather than a checklist of forbidden class attributes. A short true spec beats a long one, and padding a coverage card into a surface card's shape would have produced claims nobody measured — the exact failure `D4` records.

### Alternatives rejected

- **Keep `## Other` as a section and add the missing sections around it.** Lost because the section's defect is structural, not editorial: it is a commit message with a heading, so every claim in it inherits whatever the commit message asserted, unaudited. Both `D4` and `D5` entered the spec exactly that way. Retaining it would have preserved the channel that produced them.
- **Leave the stub and record the contract only in the rationale.** Lost because the contract is normative and belongs in the spec by definition ([`worker-1.md`][worker-1] `### Performing the rationale move`, "What STAYS in the spec"). A rationale file is where deliberation lives, not where the auditable statement lives.
- **Reconstruct from the ship commit messages.** Lost on the evidence: the commit message is the source of both inherited defects, and its own test count contradicts its own list. Every statement in the reconstructed spec is measured against `HEAD` or against the named commit's tree, never against a commit message's prose.

### Changes this decision has undergone

1. **At spec creation** — written as a stub to give the card a durable `SpecDoc` FK target, with an explicit note that it was not the real spec.
2. **This pass** — expanded into builder format: `## Key glossary references`, `## Card snapshot`, `## Problem statement`, `## Goals`, `## Non-goals`, `## Slice checklist`, `## Architectural decisions`, `## Test plan`, `## Doc updates`, `## Definition of done`. `## Other`, `## Planning note`, and the stub preamble are gone; the `Status:` line describes the card rather than the file's provenance.

### Claims this decision may no longer make

- That the file is "intentionally lightweight" or that implementation work has not yet started from it. Implementation shipped in May 2026.
- That the file's purpose is to hold a Kanban FK target. That was true of the stub; the file is now the card's contract.

## D2 and D3 — the two census clauses in one sentence

**Keys to:** [`### Decision 3 - The two relation shapes, and what each is for`][spec-026-decision-3] in [`spec-026-scalar_conversion_fakeshop-0_0_7.md`][spec-026].

### Text as the spec carried it

> `NullableScalarSpecimen` — every scalar field nullable (`null=True, blank=True`), exposed via `NullableScalarSpecimenType`. Adds a cross-model FK `partner: ForeignKey(ScalarSpecimen, on_delete=SET_NULL, related_name="nullable_partners")` — **the only `SET_NULL` ondelete in the example tree, and the only cross-model FK in the scalars app**.

One sentence, two false clauses, and they are false for unrelated reasons. That is why they were corrected in a single edit: a fix landing one half leaves a reader unable to tell which half is current, which is worse than an uncorrected sentence.

### Both measurements

**Clause 1, the `SET_NULL` census.** True at the ship commit — `git grep 'SET_NULL' 2701eb88 -- 'examples/fakeshop/apps/*/models.py'` returned exactly one non-comment hit. False at `HEAD`:

```shell
grep -o 'on_delete=models\.SET_NULL' examples/fakeshop/apps/*/models.py | wc -l
# 4  -- apps/kanban/models.py twice, apps/scalars/models.py twice
```

Occurrences, counted with `grep -o | wc -l`, never `grep -c`: `grep -c` counts matching lines, and a line can carry more than one. Two of the four arrived with the docs-as-data `kanban` app, which did not exist at ship (`git ls-tree --name-only 2701eb88 examples/fakeshop/apps/` lists `library`, `products`, `scalars`); one arrived with `ScalarSpecimen.tag`, the optimizer's `Prefetch`-downgrade substrate. One of the four is `kanban`'s self-referential `SET_NULL`, so the ondelete is not even exclusively cross-model in the tree any more.

**Clause 2, the cross-model-FK census.** False, and it was false for a different reason — a second FK inside the same app:

```shell
grep -n 'ForeignKey' examples/fakeshop/apps/scalars/models.py
# 115: parent  -> "self"               (intra-model)
# 129: tag     -> ScalarSpecimenTag    (cross-model)
# 176: partner -> ScalarSpecimen       (cross-model)
```

Two of the app's three foreign keys cross a model boundary, not one.

### Alternatives rejected

Three replacement framings were weighed and all three lost. The first two are false; the third is true and lost anyway, which is the load-bearing part of this entry.

- **"the only cross-model `SET_NULL` under the optimizer"** — false. `ScalarSpecimen.tag` is exactly that.
- **"the only `SET_NULL` exposed through a `DjangoType` relation field"** — false. All four are selected in some `Meta.fields`, `kanban`'s included, and `kanban` composes into the project root `Query`.
- **"the only `SET_NULL` whose detach any test exercises"** — measures **true** at `HEAD`, and was rejected anyway. It is the same *shape* of claim: a corpus census over a population the sentence does not own, falsifiable by growth in an unrelated app. Adopting it buys one rotation of the same defect, not a fix.

**The rule that replaced them, and that the spec's Decision 3 now follows: replace a census with a locally verifiable statement, never with a fresh census.** Decision 3 states what the edge itself does — `SET_NULL` clears `partner_id` and leaves the source row in place — and names the live test that pins it. Nothing outside `apps/scalars` can falsify it, because it quantifies over nothing outside `apps/scalars`.

### Changes this decision has undergone

1. **At ship (`2701eb88`)** — both clauses written into the commit message, clause 1 true at that moment, clause 2 false at that moment (the app already declared `parent` and `partner`; only `tag` was still to come, and clause 2 fails on `partner` alone only if `parent` is miscounted as cross-model — it fails at `HEAD` on `tag`).
2. **At spec authoring** — lifted verbatim from the commit message into `## Other`.
3. **The cycle's code slice** — the same claim was retired from its three `.py` sites in [`apps/scalars/models.py`][scalars-models] and [`test_query/test_scalars_api.py`][scalars-tests], each replaced with a statement verifiable from the file it lives in.
4. **This pass** — retired from the spec, both clauses in one edit, and replaced by Decision 3.

### Claims this decision may no longer make

- That `NullableScalarSpecimen.partner` is the only `SET_NULL` ondelete in the example tree. There are four.
- That it is the only cross-model FK in the scalars app. There are two.
- That any replacement should name a *different* population it is the only member of. The narrowest true form — the only cross-model FK **out of** `NullableScalarSpecimen` — is trivially true of a model with one FK, and is not worth stating.

## D6 — the PostgreSQL-only exclusion, and why it is a non-goal rather than an omission

**Keys to:** [`## Non-goals`][spec-026-non-goals] in [`spec-026-scalar_conversion_fakeshop-0_0_7.md`][spec-026], item 1.

`ArrayField` and `HStoreField` are absent from the coverage models on purpose. Both are PostgreSQL-only, the fakeshop runs on SQLite, and a column the example database cannot create is a column no live `/graphql/` request can reach. Their coverage stays in `tests/` against package-internal fixtures.

The decision was stated twice at ship — in `2701eb88`'s commit message and in [`apps/scalars/models.py`][scalars-models]'s module docstring — and in neither case in the spec, so the one document a reader audits the card against did not carry the card's own scope boundary. That is the defect this entry closes: an exclusion recorded only in source prose reads to the next reader as an oversight to fix.

**Wording, and why it is not "their `SCALAR_MAP` rows".** Neither field has a `SCALAR_MAP` row. Both are dispatched by sentinel-guarded branches in [`converters.py`][converters] `::convert_scalar` that run **before** the table's MRO walk, precisely because neither type can be imported unconditionally. The spec's non-goal says "neither has a `SCALAR_MAP` row of its own" for that reason; the ship commit message's "their converter rows" is the looser phrasing, and it is the one that would send a reader looking for two table entries that do not exist.

### Alternatives rejected

- **Add the two columns and skip the tests off a Postgres marker.** Lost because a model field that cannot be created is not skippable at the test layer — the migration itself fails on SQLite, and the app is in the default `INSTALLED_APPS`. The fakeshop's own PostgreSQL tier is a separate, later concern.
- **Say nothing, since the source docstring says it.** Lost for the reason above: the spec is where scope is audited.

### Claims this decision may no longer make

- That `ArrayField` / `HStoreField` conversion is uncovered. It is covered in `tests/`; what it is not is *live-covered*, and it cannot be.

## D11 — six package tests were retired, not three

**Keys to:** [`### Decision 5 - Superseded package tests are deleted in the same cut`][spec-026-decision-5] in [`spec-026-scalar_conversion_fakeshop-0_0_7.md`][spec-026], and the deletion list in [`## Test plan`][spec-026-test-plan].

### The measurement

The retirement landed in `a5c89c98` ("Migrate BigInt/JSON converter tests to live HTTP; isolate synthetic app_labels", 2026-05-27), whose own message opens "Two related cleanups in tests/types/test_converters.py that fell out of the DONE-048 converter-coverage audit".

```shell
git show a5c89c98 -- tests/types/test_converters.py | grep '^-def test_'
# -def test_big_integer_field_maps_to_bigint_in_schema():
# -def test_big_integer_field_nullable_in_schema():
# -def test_positive_big_integer_field_maps_to_bigint_in_schema():
# -def test_json_field_maps_to_json_scalar_in_schema():
# -def test_json_field_nullable_in_schema():
# -def test_json_field_round_trips_dict_via_schema_execution():
```

**Six**, each carrying a synthetic `managed = False` owner model the real pair supersedes. All six are absent at `HEAD`.

### Where the undercount came from

[`CHANGELOG.md`][changelog]'s `[0.0.7]` entry for this card names three — the `BigInt` half — and omits the three `JSON` ones. The likely lift path is visible in the source: the ship test `test_scalar_specimen_introspects_bigint_scalar_for_both_fields` carries a docstring listing exactly those three as the tests it absorbs, because those three are the ones *that* test replaces. The `JSON` three are absorbed by its sibling, `test_scalar_specimen_introspects_json_scalar_in_both_shapes` — the same test `D5` records the spec as having dropped from its list. **One omission produced two: the test the enumeration lost is the test whose three retirements the changelog lost.**

### Scope of the measurement

Six is the count for `a5c89c98`. A later commit, `b148fde7`, retired further package tests in the same audit-driven style; it is not this card's (see `D12`), and its deletions are not in this card's contract.

### Alternatives rejected

None. The count is either right or wrong, and three is wrong.

### Claims this decision may no longer make

- That the card retired three package tests. It retired six.

## D12 — the card's footprint is four commits, not two

**Keys to:** [`## Slice checklist`][spec-026-slice-checklist] and [`## Doc updates`][spec-026-doc-updates] in [`spec-026-scalar_conversion_fakeshop-0_0_7.md`][spec-026].

### The measurement, and the classification rule

`git log --grep 'DONE-048'` returns **eight** commits, all dated 2026-05-27. Proximity in time does not decide membership; what each message says about the card does:

| Commit | Verdict | The sentence that decides it |
| --- | --- | --- |
| `2701eb88` | card | closes `Part of DONE-048-0.0.7.` |
| `cae2d5a3` | card | closes `Part of DONE-048-0.0.7.` |
| `a5c89c98` | card | "fell out of the DONE-048 converter-coverage audit" — and the card's own changelog entry claims the removals as card content |
| `45a8f301` | card | "closes the standing-docs hygiene piece of DONE-048-0.0.7" |
| `b148fde7` | not the card | "Audit followup batch 2" — a separate migration stream 29 minutes later, whose 231 added lines in `test_scalars_api.py` are among the twenty tests the module grew past this card |
| `0b91a123` | not the card | dates itself relative to the card: "after the DONE-048 audit migrations" |
| `5addc067` | not the card | "caught after the post-DONE-048 hygiene pass" |
| `72f6cd9b` | not the card | "post-DONE-048 follow-up items" |

Two commits use the `Part of DONE-048-0.0.7.` formula. **That is a count of commits using a formula, not a count of the card's commits** — and reading it as the latter is what left the card's doc obligations and its live-first retirement out of the contract until this pass. The `Part of` formula marks the substrate commits; `45a8f301` closes the card's doc wrap and `a5c89c98` closes its test retirement, and both say so.

The consequence in the spec is structural: the `## Slice checklist` carries three slices rather than two, and `## Doc updates` exists at all.

### Scope of the measurement

Four commits, zero of which touch package source: `git show --stat --format= --name-only <commit> | grep -c '^django_strawberry_framework/'` returns **0** for each of the four. That is what makes Decision 6's "no package source change, no new public export" a measurement rather than an assumption.

### Alternatives rejected

- **Take the two `Part of` commits as the card, and treat `a5c89c98` / `45a8f301` as follow-ups.** Lost on the card's own changelog entry, which claims the retirement as card content, and on `45a8f301`'s own sentence, which says it closes a piece of the card.
- **Take all eight `--grep` hits as the card.** Lost because four of them only date themselves against the card. A grep result is a candidate set, never a population.

### Claims this decision may no longer make

- That the card shipped in two commits. It shipped in four.
- That "the ship commits" and "the commits whose message says `Part of`" name the same set.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[changelog]: ../../../CHANGELOG.md
[kanban]: ../../../KANBAN.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-013]: ../spec-013-real_m2m_coverage-0_0_4.md
[spec-021]: ../spec-021-apps-0_0_7.md
[spec-026-decision-3]: ../spec-026-scalar_conversion_fakeshop-0_0_7.md#decision-3--the-two-relation-shapes-and-what-each-is-for
[spec-026-decision-5]: ../spec-026-scalar_conversion_fakeshop-0_0_7.md#decision-5--superseded-package-tests-are-deleted-in-the-same-cut
[spec-026-doc-updates]: ../spec-026-scalar_conversion_fakeshop-0_0_7.md#doc-updates
[spec-026-non-goals]: ../spec-026-scalar_conversion_fakeshop-0_0_7.md#non-goals
[spec-026-other]: ../spec-026-scalar_conversion_fakeshop-0_0_7.md#other
[spec-026-slice-checklist]: ../spec-026-scalar_conversion_fakeshop-0_0_7.md#slice-checklist
[spec-026-test-plan]: ../spec-026-scalar_conversion_fakeshop-0_0_7.md#test-plan
[spec-026]: ../spec-026-scalar_conversion_fakeshop-0_0_7.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md
[worker-1]: ../../builder/worker-1.md

<!-- django_strawberry_framework/ -->
[converters]: ../../../django_strawberry_framework/types/converters.py

<!-- tests/ -->

<!-- examples/ -->
[library-models]: ../../../examples/fakeshop/apps/library/models.py
[library-schema]: ../../../examples/fakeshop/apps/library/schema.py
[scalars-models]: ../../../examples/fakeshop/apps/scalars/models.py
[scalars-tests]: ../../../examples/fakeshop/test_query/test_scalars_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
