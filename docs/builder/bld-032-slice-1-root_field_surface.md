# Build: Slice 1 — root-field surface reconciliation (spec-032)

Spec reference: `docs/SPECS/spec-032-full_relay-0_0_9.md` (whole file; 672 lines before this pass, 689 after)
Status: final-accepted

Worker-1-only spec-custody slice per the build plan's `## Dispatch shape`: no Worker 2 build pass and no
Worker 3 per-slice review (a Worker 3 pass over the whole spec diff runs after Slice 3). This artifact carries
one combined Plan + Final-verification block. **Zero executable bytes changed — no `.py` file was touched.**

## Plan + Final verification (Worker 1)

### Spec status-line re-verification

Read spec lines 1-11 (title, shipped-in header, `Status:`, Owner, Predecessors, the Slice-0 deliberative-layer
pointer) before acting. All still describe the build's current state: the card is `DONE-032-0.0.9`, `Status:`
reads `**SHIPPED (`0.0.9`)**`, the seven-slice summary matches the shipped slices, every predecessor doc
exists at its cited path, and the companion pointer resolves. **No status-line edit was owed.**

### DRY analysis

**Helper inventory checked.** Not applicable, and deliberately so: this slice writes no Python and proposes no
helper. Recorded rather than skipped so a later pass can see the question was asked.

- **Existing patterns reused.** The `**Post-ship:**` bullet shape the companion's own header paragraph defines
  ("How later passes append to this file"), and the `### Changes this Decision underwent` home it names. The
  in-spec correction shape is Slice 0's: state the contract directly, never a chronology.
- **New helpers justified.** None.
- **Duplication risk avoided.** The hazard in a reconciliation slice is a **partial** fix — one home of a
  contract corrected, the other four left stating the old claim, which is worse than not correcting at all
  because the reader cannot tell which half is current. Every finding below was swept across all its homes in
  one pass, and the residual sweep in Verification 3 is the proof.

### Findings re-verified against source

Each finding was re-opened at `HEAD` before a word of the spec was changed. All seven confirm; one is
**re-bucketed** (its provenance is not what the pre-dispatch verification recorded).

| # | Verdict | Symbol-qualified evidence |
| --- | --- | --- |
| A1 | **Confirmed** | `django_strawberry_framework/relay.py::_stamp_node_type` stamps the decode-resolved type under `django_strawberry_framework/types/relay.py` #"_NODE_TYPE_HINT_ATTR = "_dsf_node_type_hint""; `types/relay.py::install_is_type_of`'s closure reads the hint and returns `hinted is type_cls` **before** `isinstance(obj, (type_cls, model))`. `_stamp_node_type` shallow-copies via `copy.copy` when the node is an instance of the definition's model, returns `None` unchanged, and wraps the `setattr` in `contextlib.suppress(AttributeError)`. |
| A2 | **Confirmed** | `relay.py::_check_nodes_result` raises `ConfigurationError` naming `resolved_type.__name__` when `len(result) != len(pks)`, after `result = list(result)` for a return with no `__len__`. `relay.py::_interleave` indexes `per_type_results[position[0]][position[1]]` — the within-group position that makes the length check load-bearing. |
| A3 | **Confirmed, and RE-BUCKETED** | `relay.py::DjangoNodeField` and `::DjangoNodesField` both call `utils/querysets.py::reject_async_in_sync_context` with `relay.py` #"_SYNC_RESOLVER_RECOURSE". The helper raises `SyncMisuseError` and closes the orphaned coroutine (`_dispose_sync_awaitable`). **Bucket is wrong in the pre-dispatch list:** `git log -S "reject_async_in_sync_context" -- django_strawberry_framework/relay.py` returns exactly one commit, `dc00f4a6` (2026-08-16, "Guard diagnostic rendering against hostile consumer metadata"), and `git log -S "_SYNC_RESOLVER_RECOURSE"` the same. This is **post-ship (Bucket B)**, not spec-032's own build. See the note below. |
| A4 | **Confirmed** | `relay.py::_coerce_pk_or_none` delegates the field choice to `relay.py::_node_id_slot`, which reads `resolved_type.resolve_id_attr()`, maps `"pk"` to `model._meta.pk`, resolves anything else through `model._meta.get_field`, and returns `None` for a `FieldDoesNotExist` (raw literal passes through). Mechanics are `utils/querysets.py::coerce_field_value_or_none` — `to_python` then `run_validators`. The `"007"` -> `7` -> `code=7` reasoning is in `_coerce_pk_or_none`'s own docstring. |
| B2 | **Confirmed** | `resource_policy.py` #"max_node_ids: int = 200"; `extensions/resource_policy.py` #"_NODE_IDS_ARGUMENT = "ids"" and its `_charge_list_family` branch `if argument == _NODE_IDS_ARGUMENT: self._reject("max_node_ids", width, ...)`. The module docstring states the value budget "runs entirely on coerced-shape input, so no id is decoded and no queryset is built before it either passes or rejects", and `examples/fakeshop/test_query/test_resource_policy_api.py::test_node_refetch_ids_over_the_bound_are_rejected_before_any_id_is_decoded` pins it with `assert captured.captured_queries == []`. |
| B3 | **Confirmed** | `relay.py::DjangoNodeField` calls `check_deadline(info)` **before** `_decode_or_graphql_error(id)`. `relay.py::DjangoNodesField` calls it **after** `if not ids: return []` and before the batch decode. `resource_policy.py::check_deadline` raises `ResourceLimitExceeded` only when a numeric deadline is stashed and has passed. |
| B6 | **Confirmed** | `relay.py` holds `decode_model_global_id`, `DecodeResult`, `GlobalIDDecode`, and `_resolve_real_pk`. Consumers outside the module: `mutations/resolvers.py` (`from ..relay import GlobalIDDecode, decode_model_global_id`), `utils/write_values.py` (function-local import), plus `forms/resolvers.py` / `rest_framework/resolvers.py` / `types/relay.py` docstring references. `_resolve_real_pk`'s docstring states the READ/WRITE asymmetry verbatim. |

**The A3 re-bucketing matters beyond bookkeeping.** The finding itself is real and the spec correction is the
same either way, but the pre-dispatch list placed it in Bucket A ("landed in the spec-032-era commits
`3e247237` / `1f16d963`, so they are spec-032's own contract"). It did not: the commit trace is unambiguous
and the two `-S` searches return one commit each. Recording it as spec-032's own would have told a future
reader that `0.0.9` shipped a boundary it did not. The companion carries the correction under Decision 5, and
the spec — which never dates a contract — is identical under either bucket.

### Spec sites changed, by content

**26 prose sites plus one link-definition block.** Grouped by finding; every site is named by what it says,
never by line number.

**A1 — concrete-type routing via a stamp (4 sites + 1 test-plan addition)**

1. `## Key glossary references`, the [Relay Node integration] entry — "nothing about the per-type wiring
   changes" was **false**: `install_is_type_of`'s closure is per-type wiring and it changed. Now names the one
   change and points at Decision 4.
2. `## Current state`, the five struck-through foundation items — "are all shipped and **need no work here**"
   was a plan-time census falsified by the card's own build. Split: four need no work; the fifth (injection)
   stays unconditional but its closure gains the routing stamp. The Current-state description itself is
   untouched, because it is true as of its date.
3. `### Decision 4`, the Bare-form bullet — the claim "`is_type_of` injection (shipped, unconditional) lets
   Strawberry resolve each returned model instance to its concrete GraphQL type" is **insufficient**, not
   merely incomplete: for a model with two registered Relay types plain isinstance answers `True` on both and
   iteration order picks `__typename`. Replaced by the stamp contract, including the shallow copy, the `None`
   pass-through, and the best-effort behavior on a non-model / `__slots__` object.
4. `## Slice checklist`, Slice 2's first sub-bullet — gained the stamp as a stated deliverable.
5. `## Test plan` Slice 2 — the parenthetical "(`is_type_of` dispatch)" removed from
   `test_bare_node_field_resolves_model_label_id`, and a new bullet added naming the five tests that actually
   pin the contract (all verified present in `tests/test_relay_node_field.py`).

**A2 — the `resolve_nodes` override return contract (5 sites)**

6. `### Error shapes` — new bullet: a non-1:1 return raises `ConfigurationError` naming the type, the row
   count, and the id count; a generator/iterator return is materialized first.
7. `### Decision 4`, the `nodes`-semantics bullet — gained the contract and *why* it is one (`_interleave`
   indexes by within-group position), naming the `get_queryset().filter(pk__in=node_ids)` spelling that
   violates it.
8. `## Slice checklist`, Slice 2's first sub-bullet — the batching clause now states the 1:1 requirement.
9. `## Test plan` Slice 2 — new bullet naming `test_nodes_consumer_resolve_nodes_wrong_length_raises`,
   `..._generator_return_accepted`, `test_nodes_async_with_sync_consumer_resolve_nodes_override`.
10. `## Definition of done` item 3 — the `nodes` clause now carries the override contract.

**A3 — the fields reject an awaitable in a sync context themselves (6 sites)**

11. `## Key glossary references`, the [`SyncMisuseError`] entry — "the root fields ... inherit this contract
    unchanged" was **true of the framework default and silent about the consumer override**. Split into the
    inherited half and the field's own half.
12. `### Error shapes` — the single SyncMisuseError bullet became two: the inherited async-`get_queryset`
    source, and the consumer-override source with the actual recourse message quoted from
    `relay.py` #"_SYNC_RESOLVER_RECOURSE".
13. `### Decision 5` — new bullet, "An awaitable in a sync context → `SyncMisuseError`, from either of two
    sources", stating why the coroutine is closed rather than treated as a result, and that both sources sit
    outside the decode catch-convert boundary.
14. `## Edge cases and constraints`, Async end-to-end — the closing "unchanged" sentence now covers both.
15. `## Test plan` Slice 2 — new bullet naming
    `test_node_sync_with_async_consumer_resolve_node_raises_sync_misuse` and the `nodes` sibling.
16. `## Definition of done` item 3 — "the `SyncMisuseError` pass-through unchanged" became "unchanged **plus**
    the field's own rejection".

**A4 — pk pre-coercion is id-slot-aware (7 sites)**

17. `### Error shapes`, the uncoercible bullet — `model._meta.pk.to_python` replaced by the id slot; the
    backend `OverflowError` added to what no longer leaks.
18. `### Decision 5`, the Uncoercible-pk bullet — rewritten with **two nested sub-bullets that stay in the
    spec**: which field it coerces against (with the `"007"` -> `7` -> `code=7` mis-typing, lifted from
    `_coerce_pk_or_none`'s docstring) and `to_python` **then** `run_validators`. Both are implementation-relevant
    rationale under `worker-1.md` "the 'why' that changes HOW a thing is built" — a builder who reads only
    "pre-coerce to the pk type" writes the bug back.
19. `## Slice checklist`, Slice 2's first sub-bullet.
20. `## Implementation plan`, the Slice 2 row — "`strawberry.ID` args + pk pre-coercion" -> "id-slot
    pre-coercion".
21. `## Edge cases and constraints`, "Well-formed id, uncoercible pk literal" -> "uncoercible **id** literal",
    with the full slot rule and both leak classes.
22. `## Test plan` Slice 2 — the `model._meta.pk.to_python` phrase removed from
    `test_node_uncoercible_pk_returns_null`, and a new bullet naming the three id-slot tests
    (`test_node_custom_node_id_attr_resolves`, `..._uncoercible_returns_null`,
    `test_coerce_pk_or_none_passes_raw_string_for_non_field_node_id`).
23. `## Definition of done` item 3.
    (A follow-on coherence fix inside `### Decision 5`'s Format/decode bullet — "the pk pre-coercion above" ->
    "the id-slot pre-coercion above" — is counted with this group.)

**B2 — `nodes(ids:)` is no longer uncapped (2 sites)**

24. `## Edge cases and constraints` — the entry titled "**`nodes(ids:)` is uncapped**" is retitled and
    rewritten: the bound is `ResourcePolicy.max_node_ids` (default `200`), enforced by the resource-policy
    extension on the argument named `ids`, charged over coerced-shape input before any id is decoded, with
    duplicates charged positionally. The old entry's whole justification ("deliberate posture ... parity does
    not force one ... belongs at the consumer's transport layer") is **deleted, not moved** — it argued for a
    posture that no longer exists.
25. `### Error shapes` — new bullet covering the cap and the deadline rejection.

**B3 — the cooperative execution deadline (4 sites)**

26. `### Decision 3` — new paragraph stating both call sites and that **the placement is the contract**.
27. `## Edge cases and constraints` — new entry, "Cooperative execution deadline", with both placements and
    the cooperative-not-preemptive limit stated honestly.
28. `## Edge cases and constraints`, "`nodes(ids: [])`" — "returns `[]` without touching the database" gained
    "and without checking the execution deadline", because the short-circuit-first ordering is exactly what
    the placement buys.
29. `## Slice checklist` Slice 2 + `## Definition of done` item 3.

**B6 — `relay.py`'s widened module scope (1 site)**

30. `### Decision 11`, the Source bullet — the module is now described as the home of the whole
    typed-`GlobalID` consumption contract, naming `decode_model_global_id` / `DecodeResult` / `GlobalIDDecode`
    / `_resolve_real_pk`, and stating the READ/WRITE split and why it lives there (the READ field filters
    `{id_attr: value}` and needs no pk; every WRITE consumer uses the value **as** a pk).

**Link definitions:** two added to the `<!-- django_strawberry_framework/ -->` group, both used —
`[querysets]` (`utils/querysets.py`, cited by Decision 5's coercion sub-bullet) and `[resource-policy]`
(`resource_policy.py`, cited by the corrected Edge case). Alphabetical placement verified.

### Deleted as never-true or falsified, not moved

Graded against the three cases in the method rules:

- **Case (a), was true, later falsified by shipped code — deleted.** The `nodes(ids:)`-is-uncapped entry's
  justification paragraph. Its subject ceased to exist, so re-pointing it would have preserved an argument for
  a contract the package no longer has.
- **Case (b), never true — one site.** `### Decision 4`'s claim that plain unconditional `is_type_of`
  injection "lets Strawberry resolve each returned model instance to its concrete GraphQL type". It was
  **already insufficient when written**, for the two-Relay-types-over-one-model case the spec's own
  `## Edge cases` section describes under "Multi-type models at the root fields". The build shipped the stamp
  precisely because the claim did not hold; the spec never recorded that. Rewritten, not hedged.
- **Case (c), true-then, a forward-looking promise since resolved — three sites.** `## Current state`'s
  "need no work here" quantifier; `## Definition of done` item 1's "intentionally absent from the CSV ...
  Slice 7 adds their glossary entries"; and the [`SyncMisuseError`] glossary reference's "unchanged". Each
  now states the settled outcome.

`## Current state`'s own descriptions were **not** rewritten. That section is explicitly "a true description
of the repo as of this writing, before the build", and every sentence in the root-field half is still true on
its own date — including "No top-level `relay.py` module exists" and the unconditional-injection description.
Only the plan-time claim *about the card's scope* attached to that list was corrected.

### Beyond the handed list

**Worker 0's list was a floor, not a ceiling.** Four items surfaced that it did not carry:

1. **A3's bucket is wrong** (see above). Corrected in the companion, not silently absorbed.
2. **`## Definition of done` item 1 is stale and belongs to no functional slice.** It says the
   `DjangoNodesField` / `Meta.relation_shapes` symbols "have **no** glossary heading yet ... so they are
   intentionally absent from the CSV". Both statements are false at `HEAD`: `docs/GLOSSARY.md` carries
   `## DjangoNodesField` and `## Meta.relation_shapes` as `shipped (0.0.9)` with Index and Browse-by-category
   rows, and `docs/SPECS/appx/spec-032-full_relay-0_0_9-terms.csv` carries a row for each (lines 5 and 12).
   Taken here rather than routed, because the sentence names **one symbol from each of Slice 1's and Slice 2's
   halves** and a half-fix would be the exact defect this cycle exists to avoid. Slice 2 needs no action on it.
3. **`docs/GLOSSARY.md`'s `## DjangoNodesField` entry carries the same falsified uncapped claim** the spec
   did: "The batch is deliberately uncapped in `0.0.9` (parity with both upstreams; request-size limiting
   belongs to the consumer's transport layer)." `docs/GLOSSARY.md` is on this cycle's **do-not-touch** list and
   is DB-generated besides (edit the glossary app's DB, then re-render), so it is **routed, not taken** — see
   the Notes section, where it is given a named owner.
4. **The spec's own path references still spell the pre-archive location.** Decision 1, Definition of done
   items 1 and 11, and the `[spec-032]` / `[spec-032-terms]` link definitions read
   `docs/spec-032-full_relay-0_0_9.md` while the file is at `docs/SPECS/`. The link *definitions* resolve (they
   are relative), so no gate sees it; the prose paths do not. Systematic across the file and shared with sibling
   specs, so it is a one-sweep repair, not a piecemeal one — routed to Slice 3 in the Notes.

### Verification

**1. Glossary gate — exits 0, unchanged term count.**

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-032-full_relay-0_0_9.md
OK: 40 terms - all have glossary entries and at least one spec link.
EXIT=0
```

Same 40 terms Slice 0 measured. Expected: this pass added no new glossary-linked term and removed none.

**2. Markdown scaffold gate — exits 0 on both files.**

```
$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-032-full_relay-0_0_9.md docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md
EXIT=0
```

**3. Anchors, link definitions, and the definition block — checked mechanically on both files.**

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

The checker masks fenced code blocks before extracting anchors and uses, and resolves every cross-file
`#anchor` against the target file's own headings.

**Instrument note — the slugger trap, and one the control caught in itself.** The checker slugs each
whitespace character **individually**, never `re.sub(r'\s+', '-', ...)`: GitHub turns " — " (space, em-dash,
space) into **two** hyphens once the dash is stripped, so a run-collapsing substitution reports a false
dangling on every `decision-N--title` anchor — the exact false pass Slice 0 hit. The slugger is asserted
against three known-good headings before any count is believed. On the first run those assertions **failed**,
because the test inputs still carried their `## ` prefix while the real code path strips it — an instrument
bug, not a finding. Worth recording: the control failing loudly on its own fixture is the only reason its
later "none" is worth anything.

**4. Link-definition alphabetization — one pre-existing convention, not introduced here.** A strict ASCII sort
flags four groups: the spec's `<!-- docs/SPECS/ -->` (`rationale-d13` before `rationale-d1`;
`spec-032-rationale` before `spec-032`) and three in the companion. Every out-of-order pair is a
**longer-ref-before-its-own-prefix** pair authored by Slice 0, none is a definition this pass added, and the
enforcing gate (`check_trailing_commas.py`) passes. Measured tree-wide rather than asserted: **15 of the 56
archived specs carrying a `<!-- LINK DEFINITIONS -->` block have at least one group in the same shape**, so it
is the house convention, not rot. The two definitions this pass added sit in
`<!-- django_strawberry_framework/ -->`, which the strict sort reports clean.

**5. Byte counts.**

| File | Before this slice | After |
| --- | --- | --- |
| `docs/SPECS/spec-032-full_relay-0_0_9.md` | **145,056** bytes / 672 lines | **157,923** bytes / 689 lines |
| `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md` | **75,855** bytes / 429 lines | **85,123** bytes / 439 lines |

Spec `+12,867`, companion `+9,268`. The spec grows because a reconciliation slice adds contract text the spec
never carried (the stamp, the override return contract, the second `SyncMisuseError` source, the id-slot rule,
the cap, the deadline, the widened module scope); only one passage was deleted rather than replaced. This
measures **this pass** — Slices 2 and 3 change both files again, so it is not a claim about either file's size
at any later date.

**6. Tool runs after edits.** `uv run ruff format .` — `434 files left unchanged`. `uv run ruff check --fix .`
— `All checks passed!`. Both are no-ops confirming zero `.py` files were touched. No `pytest` was run, per
`AGENTS.md` and the Worker 1 role file; no `--cov*` flag was used anywhere in this pass.

**7. Working tree.** `git status --short` after the pass:

```
 M docs/SPECS/spec-032-full_relay-0_0_9.md
?? 0_0_14.md
?? docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md
?? docs/builder/bld-032-slice-0-rationale_extraction.md
?? docs/builder/build-032-full_relay-0_0_9.md
```

Exactly the two in-scope spec paths, plus Slice 0's artifact and Worker 0's build plan (both this cycle's, both
still untracked), plus the maintainer's concurrent untracked `0_0_14.md`, which was neither read as
instruction nor touched. Nothing was reverted; no `.py`, no sibling spec, no closeout or agentflow doc was
edited. This artifact itself is the fourth in-scope path and appears once written.

### Companion appends (this pass)

Six bullets and two paragraphs, all appends — no existing companion text was rewritten (the file is
append-only during the cycle):

- **Decision 3** — one `**Post-ship:**` bullet: the deadline, its card (`DONE-047-0.0.14`, commit `567cc6d0`),
  and the placement decision including the rejected one-check-at-the-top alternative.
- **Decision 4** — two `**Build finding (Slice 2)**` bullets: the stamp (`1f16d963`), with the shallow-copy and
  best-effort sub-decisions and what each rejected; and `_check_nodes_result` (`3e247237`), with the rejected
  full-positional-verification alternative.
- **Decision 5** — one build-finding bullet for the id-slot generalization (`3e247237`, plus the post-ship
  `c1f20f49` / `f92c1944` refinements) recording explicitly that the `"007"` reasoning **stays in the spec**
  under the implementation-relevant carve-out; and one `**Post-ship:**` bullet for the consumer-override
  `SyncMisuseError` (`dc00f4a6`) carrying the bucket correction.
- **Decision 11** — one `**Post-ship:**` bullet for the widened module scope (`70d60d4a`, `cf3293cf`), with the
  rejected separate-write-decode-module alternative and why the id-slot rule must be shared.
- **Risks and open questions** — two paragraphs: item 7's **prediction-vs-outcome** (the fallback landed, but
  as a dedicated policy field rather than a reuse of `relay_max_results`, enforced pre-execution rather than in
  the field, and fail-closed rather than opt-in — three ways the prediction missed), and item 1's closure.

### Notes for Worker 1 (spec reconciliation)

1. **`docs/GLOSSARY.md`'s `## DjangoNodesField` entry carries the falsified uncapped claim.** Exact text:
   "The batch is deliberately uncapped in `0.0.9` (parity with both upstreams; request-size limiting belongs to
   the consumer's transport layer)." `resource_policy.py::ResourcePolicy.max_node_ids` falsifies it exactly as
   it falsified the spec's Edge case. `docs/GLOSSARY.md` is **do-not-touch for this whole cycle** and is
   DB-generated (edit the glossary app's DB in `examples/fakeshop/db.sqlite3`, then re-render via
   `scripts/build_glossary_md.py`), so no slice of this cycle can take it. **Named owner: the final gate's
   `### Deferred work catalog`**, as a maintainer follow-up — the `031`-cycle precedent for an out-of-scope
   surface. Recorded with the full replacement text so it cannot be lost: the batch is bounded by
   `ResourcePolicy.max_node_ids` (default `200`), charged pre-execution against the `ids` argument.
2. **The spec's prose still spells the pre-archive path `docs/spec-032-full_relay-0_0_9.md`.** Sites:
   `### Decision 1` (the "lives at" sentence), `## Definition of done` item 1 (twice — the prose path and the
   `check_spec_glossary.py` invocation), `## Definition of done` item 11, and the `## Slice checklist` Slice 7
   KANBAN sub-bullet. The `[spec-032]` / `[spec-032-terms]` link definitions resolve correctly (relative
   paths), so **no gate sees the prose drift**. Sibling specs share the shape, so this is one sweep, not five
   edits. **Named owner: Slice 3** (cross-spec residue + citation repair), which already owns the archive-path
   family.
3. **A3's bucket correction is on record in the companion under Decision 5**, not only in this artifact. The
   pre-dispatch list attributed `reject_async_in_sync_context` in `relay.py` to `3e247237` / `1f16d963`; the
   commit is `dc00f4a6`. No action is owed — the spec never dates a contract — but the Worker 3 pass over the
   whole spec diff should not re-derive it from scratch.
4. **No code defect was found.** Every finding re-verified as a *spec* staleness, not a skipped or dropped
   contract, so the escalation path in the slice brief was not taken and `Status: final-accepted` is set.

### Test additions / updates

None. This slice changes zero executable bytes, adds no source and no test, and runs no `pytest` per
`AGENTS.md`. The `## Test plan` **section of the spec** gained four bullets, every one of which names tests
that **already exist** at `HEAD` in `tests/test_relay_node_field.py` — verified by
`grep -n "def test_"` against that file, not asserted from the spec. No test name was invented.

### Spec slice checklist (verbatim)

Not applicable. This cycle's Slice 1 is a reconciliation slice defined by the build plan, not an entry in the
spec's own `## Slice checklist` (which carries the seven shipped build slices 1-7). There are no verbatim
sub-checks to copy, tick, or audit. Recorded explicitly rather than omitted, so the absence reads as a
decision.

### Implementation discretion items

None. Every choice in a spec-custody pass is the custodian's; nothing was delegated.

### Summary

The root-field half of `spec-032` now states the contract the code actually implements. Seven findings were
re-verified against `HEAD` before any edit — all seven confirm, and one (A3) was re-bucketed from "this card's
own build" to "post-ship" on an unambiguous commit trace. **26 prose sites** across `## Key glossary
references`, `## Slice checklist`, `## Current state`, `### Error shapes`, Decisions 3 / 4 / 5 / 11,
`## Implementation plan`, `## Edge cases and constraints`, `## Test plan`, and `## Definition of done` were
reconciled in one pass, so no contract is left half-corrected. One passage was deleted rather than rewritten
(the uncapped-`nodes` justification, whose subject ceased to exist), one claim was graded **never true** and
replaced rather than hedged (Decision 4's plain-`is_type_of` sufficiency claim), and three forward-looking
promises that have since resolved were restated as settled outcomes. Four items beyond Worker 0's list
surfaced; two were taken here and two routed with named owners. The companion took six append-only bullets and
two Risks paragraphs carrying the deliberation, the provenance commits, and the rejected alternatives. Spec
145,056 -> 157,923 bytes; companion 75,855 -> 85,123. Both gates exit 0, every anchor and link definition in
both files resolves, and zero `.py` files were touched.

### Spec changes made (Worker 1 only)

All within `docs/SPECS/spec-032-full_relay-0_0_9.md` and its companion
`docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md`, all triggered by this cycle's Slice 1. Sites are
named by content per `AGENTS.md`; the per-finding breakdown is in `### Spec sites changed, by content` above
and is not repeated here.

1. **A1 (stamp)** — 4 spec sites + 1 test-plan bullet. Reason: Decision 4's concrete-type-routing claim was
   insufficient as written for a model with two registered Relay types, and the shipped stamp that fixes it
   appeared nowhere in the spec.
2. **A2 (`resolve_nodes` 1:1 return)** — 5 spec sites. Reason: a consumer-facing error shape and a documented
   override contract, absent from `### Error shapes` and from every Decision.
3. **A3 (sync-context awaitable rejection)** — 6 spec sites. Reason: "inherited from the defaults, unchanged"
   described only one of the two sources that now raise `SyncMisuseError` at these fields.
4. **A4 (id-slot pre-coercion)** — 7 spec sites. Reason: `model._meta.pk.to_python` names the wrong field for
   a `relay.NodeID` id slot; the `"007"` mis-typing that makes it wrong is implementation-relevant rationale
   and stays in the spec body rather than moving to the companion.
5. **B2 (`max_node_ids`)** — 2 spec sites, one of them a deletion. Reason: the "uncapped" Edge case and its
   justification were falsified outright by `ResourcePolicy.max_node_ids`.
6. **B3 (execution deadline)** — 4 spec sites. Reason: a pre-query seam both fields sit in, unmentioned; the
   placement is the contract and is stated as such.
7. **B6 (module scope)** — 1 spec site. Reason: Decision 11 described `relay.py` as the root-field factory
   home only.
8. **Beyond the handed list** — `## Definition of done` item 1's glossary/CSV claim corrected (false at `HEAD`
   in both halves; taken here because the sentence straddles Slice 1's and Slice 2's symbols and a half-fix is
   the defect this cycle exists to avoid).
9. **Link definitions** — `[querysets]` and `[resource-policy]` added to the
   `<!-- django_strawberry_framework/ -->` group, both used, both alphabetical.
10. **Companion** — six append-only bullets under Decisions 3 / 4 / 5 / 11 and two paragraphs under
    `## Risks and open questions`. No existing companion text was rewritten.

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
