# Build: Review round 1 — Worker 3 over the whole spec-032 reconciliation diff

Spec reference: `docs/SPECS/spec-032-full_relay-0_0_9.md` (shipped record, card `DONE-032-0.0.9`)
Companion: `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md`
Status: final-accepted

## Plan (Worker 1)

Not applicable. The build plan's `## Dispatch shape` records that no Worker 2 is dispatched for this
cycle (every slice is a spec-only edit) and that isolation is preserved instead by **one Worker 3 pass
over the whole diff before the integration pass**. This artifact is that pass. There is therefore no
`### Dispatched findings checklist`, no `## Build report (Worker 2)`, and no failability-proof or
hot-path-budget subsection to audit: the diff changes **zero executable bytes**, so it introduces no
boundary, guard, gate, or rejection path. `docs/builder/worker-3.md` "Acceptance gate" makes an empty
re-run set legal exactly here.

The unit under review is the working-tree diff against `HEAD`:

| File | Change |
| --- | --- |
| `docs/SPECS/spec-032-full_relay-0_0_9.md` | modified, 188,525 -> 170,612 bytes (710 lines) |
| `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md` | **net-new**, 108,497 bytes (471 lines) |
| `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` | modified, +230 bytes (one citation repair + one link def) |
| 7 `.py` files | comment / docstring text only |

---

## Review (Worker 3)

### High:

None.

Every sampled contract sentence in the reconciled spec is TRUE at HEAD (see
[What looks solid](#what-looks-solid) for the enumerated verification set). No normative or
implementation-relevant sentence was found in the companion that a builder reading only the spec
would need; no spec sentence was found flipped into a false claim in either direction.

### Medium:

#### M-1 — `docs/GLOSSARY.md` still states the falsified `"both"` default, and no slice routed it anywhere

**What the doc says.** `docs/GLOSSARY.md` `## Meta.relation_shapes` (the entry body, the sentence
beginning "`Meta.relation_shapes` is a `dict[str, str]` with values"):

> `Meta.relation_shapes` is a `dict[str, str]` with values `"list"` / `"connection"` / `"both"`
> (`"both"` is the implicit default): `"connection"` suppresses the `list[T]` field, `"list"`
> suppresses the connection.

**What the source says.** `django_strawberry_framework/types/base.py` #"DEFAULT_RELATION_SHAPE" is
`"connection"`, and `django_strawberry_framework/types/finalizer.py::_synthesize_relation_connections`
resolves an absent key with `shapes.get(name, DEFAULT_RELATION_SHAPE)`, then calls
`_suppress_relation_list_form` for that shape. `"both"` is not the default and has not been since
`0.0.14`.

**Why it matters, and why it is a finding against *this* cycle rather than a stale-doc observation.**
This is the exact defect class Slice 2 existed to close, in the exact vocabulary Slice 2 swept for —
and `docs/GLOSSARY.md` was already established as a carrier of this cycle's falsified claims: Slice 1
found the sibling defect in the same file (`## DjangoNodesField`'s "the batch is deliberately uncapped
in `0.0.9`", falsified by `resource_policy.py` #"max_node_ids") and routed it to the final gate's
`### Deferred work catalog`. Slice 2 then ran its own `"both"`-default census scoped to the spec plus
the `.py` tree and never re-swept the file Slice 1 had just proved was carrying the same rot. The
result is a **half-reconciled standing doc that contradicts itself**: the same file's
`## Relay Node integration` entry (the `**Many-side default (0.0.14, spec-047).**` paragraph) states
the flip correctly, so a reader cannot tell which half is current.

**Corrected sentence** (for whoever discharges the catalog entry — `docs/GLOSSARY.md` is DB-generated,
so the fix is a glossary-DB edit plus a `scripts/build_glossary_md.py` re-render, never a hand edit):

> `Meta.relation_shapes` is a `dict[str, str]` with values `"list"` / `"connection"` / `"both"`
> (`"connection"` is the implicit default since `0.0.14`): the default emits the connection alone and
> suppresses the `list[T]` field, `"both"` is the explicit opt-in that keeps that list beside it, and
> `"list"` suppresses the connection.

**Disposition.** This cycle must **not** edit `docs/GLOSSARY.md` — it is on the plan's do-not-touch
list and is DB-generated. The obligation is that Worker 1 adds it to the final gate's
`### Deferred work catalog` **as a second entry beside the already-routed `## DjangoNodesField`
uncapped item**, so the two GLOSSARY defects are discharged together in one DB edit + re-render rather
than one being fixed and the other left. An unrouted defect does not survive; a routed one does.

Pre-existing at HEAD (verified read-only: `git show HEAD:docs/GLOSSARY.md | grep -c` returns 1). Not
introduced by this cycle.

#### M-2 — Slice 0's routed chronology population is 3; the measured population is 6, and two sit outside the section it named

`docs/builder/bld-032-slice-0-rationale_extraction.md` flagged **three** `recorded at final
verification` phrases in `## Doc updates` and routed the decision here. Re-derived from the spec on
disk, with the enclosing `##` section resolved per site:

| Line | Section | Phrase |
| --- | --- | --- |
| 87 | `## Slice checklist` | `(recorded at final verification)` |
| 463 | `## Test plan` | `the suite did not previously exercise` |
| 524 | `## Doc updates` | `Two coherence fixes recorded at final verification:` |
| 527 | `## Doc updates` | `a planner-authorized coherence extension recorded at final verification` |
| 531 | `## Doc updates` | `(grant extension recorded at final verification)` |
| 533 | `## Doc updates` | `(recorded at final verification)` |

So `## Doc updates` carries **four**, not three; `## Slice checklist` and `## Test plan` carry one
each; the population is **six**. A count reads as measured and every later pass treats it as measured
(`BUILD.md` `## Claims are proven mechanically, never accepted on prose`), and a fix scoped to the
under-counted section would have left two sites standing — the partial claim fix this repo has shipped
before.

**The decision, which this round owes.** All six are removed. `BUILD.md`
`## Spec rationale extraction` is unambiguous: *"The spec stays the heart, and it never narrates its
own history… a reader must never reconstruct what is currently true by applying a chronology to it.
What changed, when, why, and what was rejected live in the rationale file."* Each of these six is a
provenance parenthetical that tells the reader **when in the build a sentence was written**, which is
precisely the chronology the rule bars, and every one of them is a pure deletion: dropping the
parenthetical leaves the surrounding sentence a complete, true statement of the contract.

Prescribed edits (delete the marked text; keep everything else on the line byte-identical):

- L87 — delete ` (recorded at final verification)`.
- L463 — replace ` (the typed-batch surface DoD item 3 ships but the suite did not previously
  exercise)` with ` (the typed-batch surface DoD item 3 ships)`.
- L524 — replace `Two coherence fixes recorded at final verification:` with `Two coherence fixes:`.
- L527 — replace ` — a planner-authorized coherence extension recorded at final verification` with
  ` — a planner-authorized coherence extension`.
- L531 — delete ` (grant extension recorded at final verification)`.
- L533 — delete ` (recorded at final verification)`.

If any of the six is judged to carry a fact worth keeping rather than a timestamp, that fact belongs
in the companion's `### Changes this Decision underwent` for the Decision it touches (Decision 13 for
the two version-heading sites, Decision 8 / Decision 10 for the glossary-entry site), not in the spec.

All six are pre-existing at HEAD (`grep -c 'recorded at final verification'` on
`git show HEAD:docs/SPECS/spec-032-full_relay-0_0_9.md` returns 5, plus the one `previously` site);
this cycle neither introduced nor removed them, which is why the routing was correct and the closure
is owed here.

### Low:

#### L-1 — seven parametrize sites spell an arm `"both"` that resolves to `"connection"`

`tests/test_relay_connection.py` #"@pytest.mark.parametrize(\"shape\", [\"both\", \"connection\"])"
appears at seven sites feeding
`tests/test_relay_connection.py::_shelf_books_connection_schema`, whose body is
`meta_extra={"relation_shapes": {"books": shape}} if shape == "connection" else None`. The `"both"`
arm therefore passes **no** `relation_shapes` key and exercises the `"connection"` default. Fourteen
test ids read `[both]` for rows that do not test `"both"`.

This cycle corrected the two docstrings that described the parametrization (the section banner and
`_shelf_books_connection_schema`'s docstring now both say the two arms resolve to the same shape and
that what the pair separates is default resolution from explicit lookup — verified true against the
source). Renaming the id to something like `"default"` changes executable bytes, which this cycle is
authorized to do only on a finding that the code skipped a spec contract; it did not. **Routing to the
final gate's deferred-work catalog is correct, not a dodge.**

#### L-2 — a comment reflow left a 13-character orphan line

`tests/test_relay_connection.py` #"# WITHOUT the" — the rewritten section banner wraps as
`… These schemas run` / `# WITHOUT the` / `# optimizer (the per-parent pipeline baseline), so …`.
Nothing enforces comment fill width and `ruff format --check` / `check_trailing_commas.py --check`
both pass, so this is cosmetic; it is worth folding the orphan back into the preceding line the next
time that block is touched.

#### L-3 — six companion `### Justification (moved from the spec)` bodies open with a lowercase fragment

The move converted the inline label `Justification: <text>` into a `###` heading and left the body
byte-verbatim, so where the original ran on from the label the body now opens mid-sentence. Sites:
Decisions 2, 7, 10, 11, 12, 13 (e.g. Decision 12's body opens `the card binds the products conversion
to 033 explicitly;`). Byte-verbatim is the stronger property and was the right default; capitalising
the six openers is a follow-up, not a correction.

#### L-4 — `## Current state`'s "as of this writing" duplicates the preamble's own disclosure

Spec line 101 opens `A true description of the repo as of this writing (the plan is written against
it)`, while line 3 already tells the reader `the [Current state](#current-state) section describes the
repo as of this spec's authoring, before the build`. The section-level hedge is redundant with the
disclosed scoping and is the one surviving `as of` in the spec. Deliberation-free deletion of the
three words would leave the sentence true and the disclosure intact. Kept out of M-2 because, unlike
those six, it scopes a section rather than timestamping an edit.

#### L-5 — `TODAY.md` opens its relation-as-Connection paragraph on the retired default

`TODAY.md` #"gains a paginated `<field>Connection` sibling alongside the plain `list[T]` field" leads
with the pre-`0.0.14` shape and corrects itself four sentences later ("Since `0.0.14` the default is
the connection **alone**"). Self-consistent by the end of the paragraph, so not M-1's class, but a
reader who stops at the first sentence gets the retired contract. `TODAY.md` is on this cycle's
do-not-touch list; noted for the catalog, not for action here.

### DRY findings

- **Spec / companion text overlap: measured, and it is not a cut-and-paste failure.** Normalized
  12-gram shingle overlap between the two files is **231 shingles out of 22,229** (~1%), in 50 runs,
  longest run 32 words. The instrument was proved failable first: pasting one real spec paragraph into
  the rationale side raises the overlap 231 -> 308. Exact-sentence overlap (>=90 chars) is **0**.
  Every run inspected falls into one of three legitimate classes: (a) the two files' `<!-- LINK
  DEFINITIONS -->` blocks, which necessarily share targets; (b) `## Decision N — <heading>` strings,
  which the companion must repeat to key itself to the spec; (c) `### Changes this Decision underwent`
  / `### Alternatives considered` entries restating the contract clause in order to say what changed
  about it or why an alternative lost — which `BUILD.md` `## Spec rationale extraction` explicitly
  requires the companion to carry. **No normative sentence lives in both files.**
- **No duplication introduced in the `.py` tree.** The seven files' diffs are comment text only; no
  helper, constant, literal, or branch changed. Nothing to consolidate and nothing to challenge for
  existence.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty**. `__all__` and the re-export
list are unchanged. (For the record the spec's DoD item 3 requires `DjangoNodeField` /
`DjangoNodesField` to be exported, and both are present at
`django_strawberry_framework/__init__.py` #"\"DjangoNodeField\"" / #"\"DjangoNodesField\"" — shipped
long ago, untouched here.)

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

The diff modifies archived specs and their companion, so this subsection applies.

- **Version strings / shipped statuses / card IDs.** The spec's `Status:` line reads
  `**SHIPPED (0.0.9)** — card DONE-032-0.0.9`; `KANBAN.md` carries the card as `DONE-032-0.0.9`; the
  companion's provenance block names the same card and release. Consistent.
- **Anchor and link-definition sweep, all three `.md` files.** Run with a slugger asserted against
  three known-good headings **and** one known-bad rendering before any zero was trusted (the known-bad
  input is the spec-033 `edges { node }` heading, whose in-tree anchor drops the braces *and* their
  surrounding spaces; the assertion requires the checker to reject that spelling). The slugger keeps
  code-span content while dropping backticks, never strips `_`, and drops an em dash while keeping its
  two spaces so ` — ` renders as two hyphens.

  | File | headings | defs | in-page uses | ref uses | broken anchors | undefined refs | unused defs | broken def targets |
  | --- | --- | --- | --- | --- | --- | --- | --- | --- |
  | `spec-032-full_relay-0_0_9.md` | 44 | 100 | 21 | 100 | **0** | **0** | **0** | **0** |
  | `appx/spec-032-full_relay-0_0_9-rationale.md` | 57 | 62 | 13 | 62 | **0** | **0** | **0** | **0** |
  | `spec-033-connection_optimizer-0_0_9.md` | 39 | 75 | 22 | 75 | **1** (5 uses) | **0** | **0** | **0** |

  The `broken def targets` column resolves each definition's file **and** its cross-file `#fragment`
  against the target's own heading set, so the net-new
  `[spec-032-rationale-d12]: appx/spec-032-full_relay-0_0_9-rationale.md#decision-12--sequencing-…`
  definition Slice 3 added to `spec-033` is confirmed to land on a real heading.
- **`docs/GLOSSARY.md` / `KANBAN.md` / `docs/TREE.md` / `CHANGELOG.md` / `TODAY.md`** are untouched by
  this diff, as the plan's scope requires. Their content was read but not written; the one defect
  found there is M-1.

### Verdict on the three deferred-work routings

All three were re-derived from source rather than accepted from the slice artifacts.

1. **Dangling `### Decision 9` anchor, 5 sites in `spec-033` — genuinely out of scope. Confirmed.**
   `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` uses
   `#decision-9--the-edgesnode-selection-helpers-consolidate-into-the-walker` at 5 sites; the heading
   at `### Decision 9 — The \`edges { node }\` selection helpers consolidate into the walker` slugs to
   `…the-edges--node--selection-helpers…` (GitHub drops the braces and keeps their spaces). The
   citation is dead. It is **pre-existing at HEAD** (`grep -c` on the HEAD copy returns 5, identical to
   the working tree) and it is `spec-033`-internal authoring rot that **the rationale move did not
   cause** — this cycle's licence over sibling specs is "sibling spec files whose citations the
   rationale move breaks", which this is not. Correct routing.
2. **Nine stale `docs/spec-<NNN>` docstring paths for other specs — genuinely out of scope. Confirmed,
   and the number is right.** Enumerated tree-wide over `.py`: `tests/test_list_field.py` (spec-020),
   `tests/test_connection.py` (spec-030), `tests/optimizer/test_multi_db.py` (spec-023),
   `examples/fakeshop/test_query/test_glossary_api.py` x2 (spec-028), `scripts/check_spec_glossary.py`
   x4 (spec-018) = 9. Each names a **different** spec, so each belongs to that spec's own residual
   cycle; two of the nine (`test_glossary_api.py`) are asserted **data values** matched against the
   glossary DB and four (`check_spec_glossary.py`) are illustrative usage examples in a docstring, so
   several are not even stale in the sense the routing implies. Correct routing, and correcting them
   here would have changed executable bytes and DB-matched literals on someone else's card.
3. **Degenerate parametrize id — genuinely out of scope. Confirmed.** See L-1.

**One routing is missing**, and that is M-1: the `docs/GLOSSARY.md` `## Meta.relation_shapes` default
claim belongs in the same catalog as the `## DjangoNodesField` uncapped claim Slice 1 already routed.

### What looks solid

Named so the next reader sees the shape of the coverage rather than inferring completeness.

**Contract sentences verified against source, symbol by symbol** (each read in the source body, not
inferred from a symbol name):

- **`relation_shapes` default `"connection"`** — `types/base.py` #"DEFAULT_RELATION_SHAPE" = `"connection"`;
  `types/finalizer.py::_synthesize_relation_connections` (`shapes.get(name, DEFAULT_RELATION_SHAPE)`,
  the `"list"` early `continue`, `_suppress_relation_list_form` under `"connection"`, the non-Node
  target's silent degrade vs. its explicit-request raise, the consumer-authored skip, the two-surface
  camel-case collision guard, the marker-based re-entrancy path, the `_record_relation_connection`
  re-write on rerun, the identity-safe teardown registration). Walked through **every** home the spec
  restates it in — Key glossary (L35), Slice checklist (L65/66/77), Goals (L118), User-facing API
  (L207-212), Error shapes (L229), Decision 6 (L295-320), Decision 7 (L326), Edge cases (L433), Test
  plan (L480/482/513/514), DoD item 6 (L569) — and found no surviving old-default assertion in any of
  them.
- **The `"both"`-default sweep, re-derived independently and by behavior rather than token.** Slice 2's
  16 -> 22 literal count is **correct and consistently instrumented**, which I confirmed by
  reconciling it to HEAD rather than trusting it: HEAD carries **21** `"both"` occurrences on 19 lines,
  and the five that vanish before Slice 2's baseline all sit in blocks Slice 0 moved (L37 revision
  history, L372 x2 `Justification:`, L400 `Alternatives considered:`, L637 `## Risks`), giving exactly
  16. I then ran a **different** sweep from Slice 2's — 23 positively-spelled tokens
  (`sibling`, `beside`, `alongside`, `counterpart`, `keeps the`, `stays list`, `and the list`,
  `implicit upgrade`, `adds a connection`, `as well as`, `widen`/`narrow`, …) over every line of the
  spec, 44 hits read in context — and **zero** assert or assume the retired default. The one hit that
  reads that way at a glance, L112, is inside `## Current state`, which line 3 discloses as an
  authoring-time snapshot.
- **`nodes(ids:)` cap** — `resource_policy.py` #"max_node_ids" (`= 200`) and
  `extensions/resource_policy.py` #"_NODE_IDS_ARGUMENT" (`= "ids"`), charged in
  `_charge_list_family` only when the named type is the `ID` scalar **and** the operation is not a
  mutation, from the `on_execute` hook — so the spec's Edge-cases sentence (L428) is exact on all
  three of its load-bearing clauses: the field, the default, and "refused before a single `GlobalID`
  is decoded". **No surviving sentence calls the batch uncapped** (`grep -c uncapped` on the spec
  returns 0); the retired Risks item that did is in the companion, correctly labelled falsified.
- **`_stamp_node_type` / `_NODE_TYPE_HINT_ATTR`** — `relay.py::_stamp_node_type` (the `None`
  pass-through, the `copy.copy` guarded by `(AttributeError, TypeError, copy.Error)`, the
  `contextlib.suppress(AttributeError)` best-effort `setattr`) and
  `types/relay.py::install_is_type_of` (the hint read inside a `except BaseException` fallback,
  `hinted is type_cls` returned **before** `isinstance(obj, (type_cls, model))`). Decision 4's
  four claims — stamp, honored-before-fallback, shallow copy, best-effort on `__slots__`/non-model —
  all hold.
- **`_check_nodes_result` override contract** — `relay.py::_check_nodes_result` materializes a
  `__len__`-less return before the length check and raises `ConfigurationError` naming the type, the
  rows returned, and the ids requested; `relay.py::_interleave` indexes by within-group position,
  which is what makes the contract load-bearing. Matches both the Decision 4 clause and the
  `### Error shapes` bullet, including "naming the type, the row count returned, and the id count
  requested".
- **pk pre-coercion, including the `"007"` reasoning Slice 1 moved into the spec** —
  `relay.py::_coerce_pk_or_none` delegates to `utils/querysets.py::coerce_field_value_or_none` and its
  *only* job is picking the field, which it takes from `relay.py::_node_id_slot`
  (`resolve_id_attr()`; `"pk"` -> `model._meta.pk`; otherwise `model._meta.get_field`; `None` on
  `FieldDoesNotExist`, whose callers pass the raw literal through). The spec's version of the
  mis-typing reasoning — `"007"` -> `7` -> filters `code=7` — is what the code's own docstring states
  and what the field selection makes true. Verified as implementation-relevant rationale that
  correctly **stayed in the spec** rather than moving.
- **`check_deadline` placement** — `relay.py::DjangoNodeField` calls `check_deadline(info)` as the
  first statement of `_resolve`, **before** `_decode_or_graphql_error`; `relay.py::DjangoNodesField`
  calls it **after** the `if not ids: return []` short circuit and before the batch decode. Decision 3,
  the Edge-cases bullet, and the `nodes(ids: [])` bullet all state this correctly and identically.
- **`Meta.cursor_field`, checked in BOTH directions.** The two case-(c) sites Slice 3 deliberately left
  standing (Goal 4 L120, Decision 9's stale-`after` bullet L356) are card-scope statements about the
  **offset** implementation and remain true; neither was flipped into a claim that the package lacks
  keyset cursors — the failure mode a careless sweep produces here. The three sites that *were*
  rewritten (L130, L361, L544) each disclose that the keyset surface shipped, and the disclosure is
  true: `django_strawberry_framework/keyset.py` exists, `types/base.py` #"cursor_field" is in
  `ALLOWED_META_KEYS` with a `_validate_cursor_field` validator, and
  `connection.py::_keyset_connection_context` routes a declared `Meta.cursor_field` onto the keyset
  path — so L422's "which a connection over an opted-in type uses instead" is exact.
- **The six named-helper diagnostics, message for message.** `types/base.py`
  #"_RELAY_NON_INTERFACE_HELPERS" carries the six entries in the spec's order with the spec's
  descriptions verbatim (`relay.Connection` / `relay.ListConnection` sharing
  `_RELAY_CONNECTION_HELPER_DESCRIPTION`, as Decision 8 item 4 says), matched by **identity**
  (`entry is helper`) and raised **before** the non-class branch so `relay.NodeID` is named —
  exactly the ordering Decision 8's closing paragraph pins.
- **The net-new `ConfigurationError` at finalization** — `types/finalizer.py`
  #"node lookup configured but no Node types registered." is byte-identical to the spec's quoted
  message.
- **The `SyncMisuseError` recourse string** — `relay.py` #"_SYNC_RESOLVER_RECOURSE" is byte-identical
  to the string quoted in Decision 5 and in `### Error shapes`.

**Test claims read as bodies, not names** (`AGENTS.md`/memory: a cited test can keep its name while its
assertion is inverted):

- **Existence census of every spec-named test.** 85 distinct `` `test_*` `` names appear in the spec;
  **81 resolve to a `def` in `tests/` or `examples/`**. The four that do not
  (`test_first_zero`, `test_first_and_last_rejected`, `test_genres_connection_cursor_round_trip`,
  `test_genres_connection_total_count`) are conformance-**matrix row names** that the spec's own
  sentences map onto shipped spec-030-era tests ("satisfied by the shipped … — mapped, not
  duplicated"); each named target does resolve. All four are pre-existing at HEAD.
- **Slice 2's two re-pointed test names -> five replacements, each read against the sentence it now
  pins.** `test_default_connection_only_drops_the_reverse_fk_list_sibling` asserts both
  `"items: [ItemType" not in sdl` **and** `"itemsConnection(" in sdl` (the spec's "SDL assertion on
  both the presence and the absence");
  `test_explicit_both_restores_the_reverse_fk_list_sibling` passes `{"items": "both"}` and asserts the
  list is back; `test_default_connection_only_covers_both_m2m_directions` covers forward **and**
  reverse M2M with the same present/absent pair — so the spec's "in both halves and across all three
  eligible relation kinds" is exact.
  `test_relation_shapes_on_consumer_annotated_relation_raises` and
  `…_assigned_relation_raises` supply an `__annotations__` override and a
  `strawberry.field(resolver=...)` assignment respectively and each asserts both
  `"names consumer-authored relation 'items'"` and `"owns that field's shape"` — the spec's "same
  overrides-own-the-shape message", two corners, two tests.
- **Stamp and override-contract tests** — `test_node_type_hint_does_not_poison_reused_model_instance`
  really exercises the reused-instance path across a primary/secondary pair;
  `test_stamp_node_type_returns_a_model_instance_that_rejects_copying` really asserts
  `_stamp_node_type(...) is node` **and** `not hasattr(node, "_dsf_node_type_hint")`;
  `test_nodes_consumer_resolve_nodes_wrong_length_raises` really returns `[]` from a consumer
  `resolve_nodes` and expects the named `ConfigurationError`.

**Fakeshop claims verified against the example project:**

- `examples/fakeshop/apps/library/schema.py`'s corrected `BookType.Meta` comment now names
  `CategoryType.properties`, and that is right: `examples/fakeshop/apps/products/schema.py`
  #"relation_shapes = {\"items\": \"both\"}" shows `CategoryType` opting `items` back in while
  `properties` carries no key, `PropertyType` is `interfaces = (relay.Node,)`, and
  `Property.category` is a reverse FK with `related_name="properties"` — so `properties` is an
  eligible many-side relation on the default. The pre-fix `ItemType.properties` did not exist
  (`ItemType.Meta.fields` has no `properties`). The spec's matching claim that the connection-only
  default is **covered live** also holds: `examples/fakeshop/test_query/test_resource_policy_api.py`
  #"CategoryType.properties" posts `{ allCategories(first: 1) { edges { node { properties { id } } } } }`
  and asserts `Cannot query field 'properties'`.
- `test_products_api.py`'s rewritten banner is true on both halves: `CategoryType.Meta` does carry the
  explicit `{"items": "both"}` opt-in, and `ItemType`/`CategoryType` are both Relay-Node-shaped.
- `examples/fakeshop/apps/products/schema.py::Query` really is four `DjangoConnectionField`s
  (`all_categories` / `all_items` / `all_properties` / `all_entries`), which is what Decision 12's
  rewritten post-ship paragraph asserts; and `KANBAN.md`'s `TODO-BETA-062-0.1.5` really is re-scoped to
  "the `node` / `nodes` entry points plus the `totalCount` opt-in", which is what the same paragraph
  and the `## Out of scope` bullet assert.

**Rationale-move mechanics:**

- **13 Decisions, 13 pointers.** `Rationale companion — this Decision's …: [Decision N][rationale-dN].`
  appears exactly once under each of Decisions 1-13 (spec L246, 258, 266, 277, 293, 319, 333, 348, 363,
  375, 382, 393, 399), and each names what moved (`its two rejected alternatives`, `its five rejected
  alternatives`, …) rather than pointing blindly.
- **Every companion Decision keys itself back.** Each `## Decision N — <heading>` is immediately
  followed by `Spec: [Decision N — <heading>][spec-032-dN].` — heading **and** anchor, so an entry can
  be looked up from either side. The two non-Decision sections
  (`## Risks and open questions`, `## Non-Decision deliberation`) each state what they belong to and,
  in the Risks case, the spec keeps the heading plus a pointer at it.
- **Nothing normative was found in the companion.** Scanning every `### Justification` body for
  normative markers (`must`, `never`, `always`, `the builder`, `contract is`, …) returns four hits, all
  four of which are the *why* behind an instruction the spec still carries in full — e.g. the companion
  argues the no-Node-types check "must live at finalization … only the finalizer sees the settled
  registry", and the spec's Decision 8 independently states the check raises **at finalization** backed
  by the module-level ledger. A builder handed only the spec builds each of them correctly.
- **The companion's own post-ship entries are true.** Spot-checked Decision 12's five `**Post-ship:**`
  bullets against source: the products `Query` shape, the `TODO-BETA-062` re-scope,
  `PeriodicalType.Meta.relation_shapes = {"issues": "connection"}` (and the correction that this key is
  on `PeriodicalType`, not `IssueType`, which the plan's own finding text had wrong), and the
  `GenreType`/`BookType` `"both"` opt-ins that the `0.0.14` flip made necessary.

**`.py` diff — comment rules:**

- **Rule 27.** No raw `path:NN` reference appears in any of the seven diffs. The two chronology
  citations Slice 3 repaired now read `(spec-032 Decision 4)` and `(spec-032 Decision 5)`, and both
  are **correct**, not merely well-formed: spec Decision 4's `**Argument spelling**` bullet is the home
  of the `strawberry.ID`-not-`relay.GlobalID` contract the first comment cites, and Decision 5's
  `**Catch scope is narrow:**` clause is the home of the `SyncMisuseError`-is-not-`GLOBALID_INVALID`
  discrimination the second cites.
- **No process provenance.** Every rewritten comment states an invariant. The three repaired path
  spellings (`docs/spec-032-…` -> `docs/SPECS/spec-032-…`) point at a file that exists.
- **Wrapped-citation hazard: instrument proved failable, then run.** Using
  `scripts/check_citations.py`'s own `CITATION_RE`, the seven files carry **33** resolvable citations
  at HEAD and **33** in the working tree, and the multisets are identical per file. The instrument was
  first shown failable by injecting a line break into a real citation in
  `tests/test_relay_connection.py` — the count dropped 6 -> 5 — so the 33 == 33 is a measurement, not a
  vacuous zero. (My first attempt at this check was itself vacuous: its control produced no signal
  because the split token still matched per line. It is recorded here because a control that cannot
  fail reads exactly like a passing proof, and the fix was to re-aim it at the gate's own regex.)
- **ASCII-only.** Zero code points `> 127` in any of the seven files.

**Gates re-run independently (not accepted from any slice's record):**

| Command | Result |
| --- | --- |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-032-full_relay-0_0_9.md` | `OK: 40 terms - all have glossary entries and at least one spec link.` exit 0 |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-033-connection_optimizer-0_0_9.md` | `OK: 38 terms - all have glossary entries and at least one spec link.` exit 0 |
| `uv run python scripts/check_citations.py` | `OK: 815 citations resolve (731 in 431 .py files, 84 in KANBAN.md).` exit 0 |
| `uv run ruff format --check .` | `434 files already formatted` exit 0 |
| `uv run ruff check .` | `All checks passed!` exit 0 |
| `uv run python scripts/check_trailing_commas.py --check` | exit 0 (covers ASCII-only `.py` and the `.md` link-def scaffold on both new/edited docs) |
| own anchor / link-def sweep, 3 `.md` files | table above; slugger self-tested against 3 known-good + 1 known-bad first |
| own spec/companion overlap sweep | 231/22,229 shingles; failability control 231 -> 308 |
| own citation-set diff, 7 `.py` files | 33 == 33, sets identical; failability control 6 -> 5 |
| `git diff HEAD -- django_strawberry_framework/__init__.py` | empty |

**Arithmetic re-derived rather than accepted:**

- Slice 3's census `102 + 12 + 13 + 242 = 369` — checks.
- Slice 0's byte accounting `22,034 + 62 + 18,641 + 5,864 + 525 = 47,126`, `+1` for the blank line the
  same sentence names = `47,127` — checks.
- `188,525 - 145,056 = 43,469` — checks.
- Slice 2's `16 -> 22` `"both"` counts — checks, via the HEAD reconciliation described above (this is
  the one number I expected to be a mixed-instrument comparison and it is not).
- Slice 3's "5 sites" for the `spec-033` `### Decision 9` anchor — checks (5 at HEAD, 5 in the working
  tree).
- Slice 3's "nine stale `docs/spec-<NNN>` docstring paths" — checks (enumerated above, 9 occurrences
  in 5 files).
- Slice 0's "three `recorded at final verification` in `## Doc updates`" — **does not check**; see M-2.

### Temp test verification

None written. `docs/builder/temp-tests/032/` was not created: the diff changes zero executable bytes,
so there is no behavior to pin that the shipped suite does not already pin, and every verification this
round needed was a read of source against a sentence or a mechanical sweep. No `pytest` was run and no
`--cov*` flag was used anywhere in this pass.

### Failability proofs

None owed. This pass introduces no new boundary, guard, gate, or rejection path — the diff is spec,
companion, and comment text only. `worker-3.md`'s mandatory re-run floor is therefore satisfied by an
**empty re-run set**, which is legal exactly when the diff introduces no boundary meeting the floor.
The instruments **this review itself** relied on were each proved failable before their result was
believed (the three controls are named in the table above), which is the same discipline applied to the
reviewer's own tools.

### Notes for Worker 1 (spec reconciliation)

- **Escalated: M-1 is a catalog obligation, not a spec edit.** `docs/GLOSSARY.md` is DB-generated and
  on this cycle's do-not-touch list, so the fix cannot land here. Add it to the final gate's
  `### Deferred work catalog` **beside** the `## DjangoNodesField` "deliberately uncapped" entry Slice 1
  already routed, with the corrected sentence given above, so both are discharged in one glossary-DB
  edit plus `scripts/build_glossary_md.py` re-render. Resolution paths: (a) catalog both together —
  recommended; (b) open a card for the pair; (c) judge the GLOSSARY default claim in scope for the
  integration pass and edit the DB there, which contradicts the plan's scope statement and is not
  recommended.
- **M-2 is a spec edit and is Worker 1's to make**, since the spec is custodian-only and the six edits
  are pure deletions. They are listed line by line above.
- **L-5 (`TODAY.md`) is a catalog candidate**, same do-not-touch reasoning as M-1 but a weaker defect
  (the paragraph corrects itself).
- **Lesson worth carrying into the integration pass, stated as a rule rather than an anecdote:** Slice
  1 proved `docs/GLOSSARY.md` carries this card's falsified claims and routed **one** of them. Slice 2
  then ran the largest census of the cycle over a *different* file set and never re-swept the file
  Slice 1 had just implicated. The integration pass's cross-slice job is exactly this seam — **a file
  one slice proved is a carrier should be re-swept by every later slice whose finding class it
  carries**, and the routing destination is not a substitute for the sweep.
- No spec ambiguity was found that blocks review, and no follow-up slice is proposed beyond the two
  catalog entries and the six deletions.

### Review outcome

`review-accepted`, with **M-1 escalated to Worker 1** under `worker-3.md`'s escalation clause: it is a
Medium finding whose resolution needs cycle-scope context this pass does not own (the file is on the
plan's do-not-touch list, so the only correct action here is a catalog entry, and the catalog belongs
to the final gate). **M-2 is likewise handed to Worker 1** because the spec is custodian-only and the
edits are hers to make — the round owed the *decision*, and the decision is recorded above with
line-by-line prescribed text.

Neither finding is a correctness defect in the deliverable this cycle produced. The reconciled spec and
its net-new companion are, on the evidence gathered here, an accurate description of what the code does
at HEAD: every sampled contract sentence traced to source, every designed-redundancy home of the three
priority contracts walked and found consistent, every gate re-run green, and every stated count
re-derived — with one count wrong (M-2) and one sweep short by one file (M-1).

Status set to `review-accepted`.

---

## Final verification (Worker 1)

Worker 3's findings text above is unedited. This section records only what was applied, what was
rejected, and what was routed onward.

### Spec status-line re-verification

Read spec lines 1-11 (title, shipped-in header, `Status:`, Owner, Predecessors, the Slice-0
deliberative-layer pointer) before acting. **No edit was owed**, and that is a measurement rather
than a skipped step: this pass's only content change is the removal of edit-timestamp parentheticals,
and the header carries none — its version claims are already scoped (`the on-disk version is still
0.0.8 at spec-authoring time`), the `Status:` line's per-slice summaries state contracts rather than
dates, and Slice 2's `siblings` -> per-relation rewrite still reads correctly at `HEAD`.

### M-2 — applied, on a re-measured population of SEVEN, not six

Worker 3 measured six; Slice 0 had routed three. **Re-measured before cutting**, sweeping for the
behavior rather than the phrase. Method: (a) the literal `recorded at final verification`; (b) every
occurrence of `final verification` in any spelling; (c) every parenthetical of <=180 characters in the
file, filtered for `record|verif|final|build|pass|wrap|slice-N|later|since|amend|added|extend|correct|fix`;
(d) positively-spelled variants — `The build …`, `the wrap …`, `build-recorded`, `at closeout`,
`during the build`, `was added`, `subsequently`, `previously`.

Worker 3's six confirm. Sweep (d) found a **seventh occurrence, on a line the prescription already
touched**: `## Slice checklist` L87's `one build-recorded \`### Changed\` amendment`. It is the same
behavior in adjectival rather than parenthetical form — it tells the reader that this amendment
entered the record during the build — and it is invisible to every sweep aimed at a parenthetical.
Cut with the rest.

| Line | Section | Text removed | Sentence after the cut |
| --- | --- | --- | --- |
| 87 | `## Slice checklist` | ` (recorded at final verification)` | `… so the two copies stay in lockstep.` |
| 87 | `## Slice checklist` | `build-recorded ` (**found by this pass**) | `The grant also covers one \`### Changed\` amendment: …` |
| 463 | `## Test plan` | ` but the suite did not previously exercise` | `… (the typed-batch surface DoD item 3 ships).` |
| 524 | `## Doc updates` | ` recorded at final verification` | `Two coherence fixes: the same \`DjangoConnectionField\` body edit corrects …` |
| 527 | `## Doc updates` | ` recorded at final verification` | `… — a planner-authorized coherence extension.` |
| 531 | `## Doc updates` | ` (grant extension recorded at final verification)` | `… shared with the \`TODAY.md\` step. No version-heading promotion …` |
| 533 | `## Doc updates` | ` (recorded at final verification)` | `… and fixed the card's two stale \`docs/spec-relay_connection.md\` filename references.` |

Each cut was read back in full, not assumed: all seven leave a grammatical sentence that is true at
`HEAD`. Post-cut residuals: `grep -c 'recorded at final verification'` = **0**, `grep -c 'final
verification'` = **0**, `grep -c 'build-recorded'` = **0**. Spec 170,612 -> **170,378** bytes (-234);
710 lines, unchanged.

**Two sites of an adjacent shape were examined and deliberately LEFT STANDING**, because an unedited
site and an unexamined site are indistinguishable in a diff:

- `## Current state` L105 and `### Decision 9` L357 — `(discovered by the Slice-4 conformance suite …)`
  / `the Slice-4 build discovered the guard was schema-bypassed …`. These timestamp a **discovery
  about the code**, not an edit to this document, and the body each introduces is the load-bearing
  Strawberry generic-specialization mechanism a builder who skips it reintroduces. Slice 0 graded
  L357 explicitly and kept it under `worker-1.md`'s implementation-relevant carve-out; L105 is the
  same finding restated in the section that discloses its own date. Removing either would require a
  rewrite, not a deletion, which is outside M-2's stated shape.
- `## Doc updates` L527's `The build extended …` and L533's `The wrap also …` survive as **subjects**.
  They name *what performed* a recorded doc edit, not *when in the build a sentence was written*.
  `## Doc updates` is a list of the card's doc obligations as discharged; rewriting its subjects is a
  section-level rewrite this pass did not take.

### M-1 — NOT fixed here, routed with Worker 3's corrected sentence

`docs/GLOSSARY.md` is DB-generated and on the plan's do-not-touch list, so no slice of this cycle can
take it. Carried into `bld-032-integration.md` `### Notes for the final gate's deferred-work catalog`
as a **second entry beside the already-routed `## DjangoNodesField` "deliberately uncapped" item**,
with the corrected sentence verbatim. **The two GLOSSARY defects are siblings in one file** — the
same card's falsified claims, in two entries, discharged by one glossary-DB edit plus one
`scripts/build_glossary_md.py` re-render. Splitting them across two discharges is how one gets fixed
and the other does not.

### The five Lows — each decided in writing

- **L-1, seven degenerate `parametrize` ids — REJECTED for this pass, ROUTED.** A parametrize id is an
  executable byte. The cycle's maintainer-set scope authorizes a `.py` edit **only** on a finding that
  the code skipped or dropped a spec contract, and no slice found one (four artifacts, all recording
  `no code defect`). Slice 3 already routed it with replacement text; confirmed, not re-derived from
  the artifact — `tests/test_relay_connection.py::_shelf_books_connection_schema` passes
  `relation_shapes` only when `shape == "connection"`, so the `"both"` arm resolves to the default,
  which is `"connection"`. Named owner: the final gate's `### Deferred work catalog`.
- **L-2, a 13-character orphan comment line — REJECTED for this pass, ROUTED WITH L-1.** Same
  out-of-scope reason (zero `.py` bytes this pass), and cosmetic besides: `ruff format --check` and
  `check_trailing_commas.py --check` both pass over it. It is **routed into the same catalog entry as
  L-1** rather than its own, because both sit in `tests/test_relay_connection.py` and one future edit
  to that file discharges both. A separate entry is how the cheaper of two same-file items gets
  skipped.
- **L-3, six companion `### Justification` bodies opening lowercase — REJECTED, and NOT routed.** Two
  independent reasons, either sufficient. (a) `worker-1.md` `### Performing the rationale move` rule 4
  makes the rationale file **append-only during the build**; rewriting six moved bodies is not an
  append. (b) Byte-verbatim is the property that makes the move auditable — a future reader can diff
  any moved body against the spec's own git history and confirm nothing was reworded, and
  capitalising six openers destroys that for a cosmetic gain. The `###` heading supplies exactly the
  antecedent the inline `Justification:` label supplied, so each body reads as it did in the spec.
  Deliberately not routed: doing it later carries the same cost, so leaving it open invites a future
  audit to "fix" a property that is load-bearing.
- **L-4, `## Current state`'s "as of this writing" — REJECTED.** Worker 3 kept it out of M-2 on the
  correct ground that it scopes a **section** rather than timestamping an edit, and that is precisely
  why it stays. Three passes of this cycle graded sentences inside `## Current state` as true and left
  them standing **on the strength of the section declaring its own date** (Slice 1's five
  struck-through foundation items; Slice 2's `GenreType` description; Slice 3's products sentence),
  and Worker 3's own `"both"`-behavior sweep dismissed its one apparent hit at L112 for the same
  reason. Line 3's disclosure and line 101's are designed redundancy, not rot: deleting the in-section
  half moves the scope one section away from every sentence that depends on it.
- **L-5, `TODAY.md`'s relation-as-Connection paragraph opener — REJECTED for this pass, ROUTED.**
  `TODAY.md` is on the plan's do-not-touch list. Carried to the catalog with the defect stated
  (the paragraph leads with the pre-`0.0.14` shape and self-corrects four sentences later). Named
  owner: the final gate's `### Deferred work catalog`.

### Gates re-run after the edit (not inherited from the review)

| Command | Result |
| --- | --- |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-032-full_relay-0_0_9.md` | `OK: 40 terms - all have glossary entries and at least one spec link.` exit 0 |
| `uv run python scripts/check_citations.py` | `OK: 815 citations resolve (731 in 431 .py files, 84 in KANBAN.md).` exit 0 |
| `uv run python scripts/check_trailing_commas.py --check <spec> <companion>` | exit 0 |
| own anchor / link-def sweep, spec + companion | 0 problems each; slugger asserted against 5 known-good **and** 2 known-bad inputs first, and the checker proved failable by three named mutations |
| `uv run ruff format --check .` | `434 files already formatted` exit 0 |
| `uv run ruff check .` | `All checks passed!` exit 0 |

No `pytest` was run and no `--cov*` flag was used anywhere in this pass. Nothing was committed.

### Final status

`final-accepted`. Both Mediums are discharged — M-2 by the seven cuts above, M-1 by a catalog routing
with a named owner — and all five Lows carry a written decision. Nothing surfaced that this pass could
not close within its own scope.

### Spec changes made (Worker 1 only)

All within `docs/SPECS/spec-032-full_relay-0_0_9.md`, all triggered by review-round finding M-2.

1. **Seven edit-timestamp removals** at `## Slice checklist` (two on one line), `## Test plan`, and
   `## Doc updates` (four), enumerated in the table above. Reason: `BUILD.md`
   `## Spec rationale extraction` — the spec never narrates its own history, and a parenthetical
   telling the reader when in the build a sentence was written is exactly that chronology. Six were
   Worker 3's prescription; the seventh (`build-recorded`) is this pass's own behavior sweep.
2. **No other spec edit was owed**, and the two adjacent sites examined and left standing are named
   above with their reasons.

No source or test file was edited. No sibling spec was edited. The companion was not edited. No
closeout or agentflow doc was edited.
