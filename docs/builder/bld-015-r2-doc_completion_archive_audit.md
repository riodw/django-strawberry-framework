# Build: R2 — documentation completion and archive audit (spec-015)

Spec reference: `docs/SPECS/spec-015-relay_interfaces-0_0_5.md` (whole file)
Status: final-accepted

Procedural-closure shape per `docs/builder/BUILD.md` `### Procedural-closure slices`: dispatched to
Worker 1 alone — no Worker 2 build, no Worker 3 review — because no code item exists (the plan's
verification pass found no code defect, and this item's writable set contains no package source and
no test). This artifact therefore carries a combined Plan + Final-verification block.

This pass is the **adversarial re-derivation over R1's output**. R1's spec and rationale were treated
as claims to be checked. R1's own record is at
`docs/builder/bld-015-r1-rationale_and_spec_reconciliation.md`, read-only; every correction to it is
recorded here rather than by editing it.

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable and deliberately not run, on the same ground R1
  recorded: this item writes two Markdown files and one CSV row, adds no package source, and proposes
  no helper, shared constant, validation branch, or test helper.
  `docs/builder/worker-1.md` `### Package-wide helper inventory before helper planning` gates *helper
  planning*, and there is none. Package source was read extensively — read-only, from `HEAD` — as the
  subject of the spec's claims, never as a reuse surface.
- **Existing patterns reused.** The appended rationale section follows the file's own established
  entry shape (`Bears on [Decision N][…]`, italic *Moved* / *Deleted, not moved* / *Claims the spec no
  longer makes* markers) rather than inventing a second shape inside one document. The added terms-CSV
  row copies the column grammar and the `notes` string every existing row uses.
- **New helpers justified.** None.
- **Duplication risk avoided.** One shape, and it drove a disposition: the fourth broken substring
  anchor (below) could have been repaired by copying the moved risk-register sentence back into the
  spec. That would have put the same deliberative sentence in both files — the two-sources-of-truth
  failure `## Spec rationale extraction` exists to prevent — so the sentence is quoted **only** in the
  companion and the spec keeps its own normative wording.

### Implementation steps

1. Re-derive F13's link-versus-CSV comparison against the **current** spec (not R1's or the plan's
   figures), then add the missing row in the one-row-per-anchor shape.
2. Re-verify F14's population at `HEAD` by substring, carry it to the deferred-work catalog, fix
   nothing.
3. Audit every link definition in the spec and the rationale: on-disk target, and for anchored refs a
   real heading — checking what each relative path **resolves to**, not merely that something exists
   there.
4. Verify F16 independently against `HEAD` blobs of the durable docs.
5. Adversarially re-derive R1: did the MOVE move; does the spec narrate history; is every rationale
   entry keyed to a decision; does every reconciled sentence hold at `HEAD`; are R1's counts
   re-derivable.
6. Repair what is repairable inside the writable set; catalog the rest.

### Test additions / updates

None. This item writes no code and no test. Per the plan's declarations and
`docs/builder/BUILD.md` `## Coverage is the maintainer's gate`, no `pytest` run is owed and none was
made; no `--cov*` flag was used anywhere in this pass.

### Implementation discretion items

- **Whether to repair the broken substring anchors in the spec or only catalog them. Decided, not
  delegated:** repair the three whose restoration reintroduces nothing false, catalog the fourth. The
  spec is in the writable set and shipped source is not, so the spec-side restoration is the only
  repair available in this cycle, and it is the correct one anyway — the source citations were right
  and the spec's wording moved out from under them.
- **Whether to correct R1's miscounts in the rationale in place or only append.** Decided: correct the
  three purely numeric statements in place **and** list every correction in the appended addendum, so
  nothing changes silently. `docs/builder/worker-1.md` rule 4's append-only discipline protects prior
  deliberation from being rewritten; it does not require a durable record to keep a number that does
  not re-derive. No entry, argument, or disposition was rewritten or removed.

### Dispatched findings checklist

- [x] **F13** — the terms CSV is one row short of the spec's glossary links. Re-derived against the
  current spec: **19** `[glossary-*]` link definitions, **19** distinct anchors, **18** CSV rows;
  `public-exports` missing. Row added.
- [x] **F14** — the `[spec-011]` renumber cluster. Re-verified at `HEAD`: **8 sites in 4 files**.
  Recorded in the deferred-work catalog, not fixed, not partial-fixed.
- [x] **F15** — the archive move is already done; the audit is what is owed. Every link definition in
  both files resolves to an on-disk target, every anchored ref to a real heading, both blocks carry
  all ten canonical group headers in order, no undefined refs and no orphaned defs in either file.
- [x] **F16** — the durable docs are already complete. Verified independently against `HEAD` blobs.
  No durable-doc edit is owed; none was made.
- [x] **Adversarial re-derivation of R1** — performed; four findings and four count corrections
  below. Three findings were repaired inside the writable set; one is catalogued.

---

## Final verification (Worker 1)

### Summary

F13 is closed by one CSV row, and `check_spec_glossary` now reports **19 terms** where it reported 18.
F14 is re-verified and catalogued. F15's audit passes clean on both files. F16 is confirmed: no
durable-doc edit is owed.

The adversarial pass earned its keep again. **R1's reconciliation retired four
`spec-015 #"unique substring"` anchors that seven shipped source and test sites quote**, and neither
the dispatched finding list nor R1's own artifact names it. It also carried forward a dead
`::QualifiedName` in the one Decision it otherwise rewrote, and left Decision 3's only code fence
diverging from the shipped guard. Everything R1 asserts about what the code *does* survived
re-reading — including its central `select_related`-versus-`Prefetch` finding, which I re-derived
from the test bodies rather than inheriting.

### Working-tree discipline

`HEAD` = `4c9e4e0dd66f64b6eb3e29dcf481a9bfb4ec6eae` throughout (re-checked at the start and the end of
the pass; unchanged). `git status --porcelain | wc -l` moved **193 → 194** during the pass, all of it
two concurrent sessions' work.

**Every source and test reading was taken read-only from `HEAD` into a scratch path outside the
repository**, per `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on
prose`:

```shell
S=/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/<session>/scratchpad/head
git show HEAD:<path> > $S/src/<flattened-path>
```

taken for `types/relay.py`, `types/base.py`, `types/finalizer.py`, `types/resolvers.py`,
`utils/querysets.py`, `exceptions.py`, `pyproject.toml`, `docs/GLOSSARY.md`, `docs/README.md`,
`docs/TREE.md`, `tests/types/test_relay_interfaces.py`, `tests/optimizer/test_relay_id_projection.py`,
`tests/test_registry.py`, `examples/fakeshop/test_query/test_library_api.py`,
`examples/fakeshop/test_query/test_products_api.py`, `examples/fakeshop/apps/products/schema.py`,
`examples/fakeshop/apps/library/schema.py`, and the `HEAD` blob of the spec itself. No `git stash`,
`git checkout`, `git restore`, or `git worktree` was used. **No database read or write was made** —
`docs/GLOSSARY.md` is DB-generated, so the presence of `## Public exports` in the `HEAD` blob is the
evidence that the `GlossaryTerm` row F13's new CSV row needs already exists; opening
`examples/fakeshop/db.sqlite3` would have risked page churn on a file that is clean at `HEAD`.

This pass touched exactly four paths: the spec, the rationale companion, the terms CSV, and this
artifact (plus `docs/builder/worker-memory/spec-015-worker-1.md`). `git status --porcelain --
docs/SPECS/` shows this cycle's three entries alongside the concurrent cycle's `spec-014-*` pair,
which was neither edited nor reverted. Nothing was committed.

### F13 — the terms CSV, re-derived rather than inherited

The plan's 19/18 figures were **not** taken on trust; both were re-measured against the current spec,
which R1 had rewritten since the plan was written.

- **19** `[glossary-*]` link definitions in the spec's link block, **19** distinct anchors, **21**
  body uses (see the count corrections — R1's "used exactly once" is wrong), **0** undefined refs,
  **0** orphaned defs, **0** inline `](../GLOSSARY.md#…)` refs.
- **18** CSV rows, one per anchor, no duplicates. The single missing anchor is `public-exports`,
  linked from `## Slice checklist` #"No new [public exports]".
- `## Public exports` exists as a heading in the `HEAD` blob of `docs/GLOSSARY.md`, so the
  `GlossaryTerm` row `import_spec_terms` requires exists.

**Row added** as `public exports,public-exports,Backfilled for DONE-card glossary linkage from the
shipped spec body.`, slotted between `OptimizerHint` and `Relay Node integration` — the file's
existing case-insensitive alphabetical-by-`term` ordering, which matters because
`import_spec_terms` compares its `GlossarySpecMention` set **in row order**. The `term` cell follows
the file's convention of quoting the spec's own link label (`choice enum`, `only()`, `FK-id elision`
are the precedents), which is the spec's lowercase `public exports`.

Shape verified directly, not via the lenient gate: 19 rows, `term`/`anchor`/`notes` columns, **no
duplicate anchor** and no duplicate term — the one-row-per-anchor invariant
`docs/builder/worker-0.md` `### DONE-card invariants` requires, since `import_spec_terms` errors on a
duplicate anchor and `check_spec_glossary` cannot see one. The CSV's anchor set and the spec's anchor
set are now **exactly equal in both directions** (`CSV-minus-spec=[]`, `spec-minus-CSV=[]`).

`uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-015-relay_interfaces-0_0_5.md`
→ `OK: 19 terms - all have glossary entries and at least one spec link.` (exit 0), where before this
pass it read `OK: 18 terms`.

**Syncing the card is not in the writable set** and is catalogued below: until
`import_spec_terms` runs, `DONE-015-0.0.5` still renders 18 glossary terms and
`import_spec_terms --check` will report this card's mention set as short by one.

### F14 — the `[spec-011]` cluster, re-verified and left alone

`git grep -n "spec-011" HEAD -- django_strawberry_framework/ tests/ examples/` — **8 textual
occurrences in 4 files**, reproducing Worker 0's measurement exactly:

| File | Occurrences |
|---|---|
| `django_strawberry_framework/types/base.py` | 5 (`::_validate_interfaces` docstring ×2, `::_validate_meta` docstring, `::_build_annotations` docstring + inline comment) |
| `django_strawberry_framework/types/resolvers.py` | 1 |
| `tests/types/test_base.py` | 1 |
| `tests/filters/test_sets.py` | 1 |

The count is occurrences, not matching lines (`git grep -o … | wc -l` reports 9, of which one is
git's `Binary file … matches` line for `db.sqlite3`; the DB's own 12 hits are kanban card text, out
of scope). The dirty worktree carries the same 8, so the concurrent session has not changed the
population.

That these cite spec-**015**'s content was re-proven by substring, independently of the plan: `An
empty tuple is the same as not declaring`, `may be a tuple/list of interface classes`, and `keeps
every selected Django field including the primary key` each resolve **1** time in spec-015 and **0**
times in `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md`, which additionally has **no
`### Decision` headings at all**, so `spec-011 Decision 4` and `spec-011 Decision 7` cannot resolve
there under any reading.

**Not fixed, and not partial-fixed.** It is homed on `TODO-ALPHA-051-0.0.15` with the correct
population and an explicit do-not-widen boundary; every one of the four files is dirty with the
concurrent hardening cycle; and `docs/builder/worker-0.md` #"When a reference is wrong across
multiple surfaces" prescribes cataloguing over a one-surface fix. Carried to the deferred-work
catalog below.

### F15 — the archive audit

Both files were audited by resolving every link definition and comparing the **resolved target** to
the intended one, not merely testing existence — the masking trap where a same-named file one level
up satisfies a wrong-depth path.

| | spec | rationale |
|---|---|---|
| link definitions | 20 | 37 |
| distinct refs used in body | 20 | 37 |
| undefined refs | 0 | 0 |
| orphaned defs | 0 | 0 |
| targets missing on disk | 0 | 0 |
| dead heading anchors | 0 | 0 |
| in-page `](#…)` anchors | 0 | 0 |
| ten canonical group headers, in order | yes | yes |

The rationale sits one level deeper at `docs/SPECS/appx/`, so its paths were the highest-risk set and
the masking trap is live there: `[docs-readme]: ../../README.md` resolves to `docs/README.md` and
`[readme]: ../../../README.md` resolves to the repository-root `README.md`. Both were checked by
resolved path and both are correct and distinct. `[tree]: ../../TREE.md` likewise resolves to
`docs/TREE.md`, not to a root file. Every `../spec-015-…md#<anchor>` def resolves to a heading that
exists in the reconciled spec, including `#out-of-scope-owned-elsewhere` (the retitled section) and
all nine `#decision-N-…` anchors.

`uv run python scripts/check_trailing_commas.py --check` scoped to the three writable files → exit 0.
Run repo-wide it exits 1 on two paths, both outside this cycle's writable set and both baseline:
`django_strawberry_framework/utils/inputs.py` (the concurrent hardening cycle) and a file under
`.claude/`. Neither was touched.

`ruff` was not run: no writable file is Python, and a repo-wide invocation would rewrite a concurrent
session's dirty work.

### F16 — the durable docs, verified independently

Read from `HEAD` blobs, not from the dirty worktree:

- `docs/README.md` — clean at `HEAD` and in the worktree. Carries `### Relay Node` with the
  `Meta.interfaces = (relay.Node,)` example, the `id: GlobalID!` / four-`resolve_*` / `is_type_of`
  sentence, and the cross-reference to the glossary subsection.
- `docs/GLOSSARY.md` — dirty, so read at `HEAD`. Carries `` ## `Meta.interfaces` `` **Status:**
  `shipped (0.0.5)` and `## Relay Node integration` **Status:** `shipped (0.0.5)`. The worktree diff
  against `HEAD` is a single paragraph in the auth entry, unrelated to spec-015.
- `docs/TREE.md` — dirty, so read at `HEAD`. Renders `types/relay.py` as "Internal Relay helpers -
  interface injection, node resolver defaults, and GlobalID strategies", with no staging language.

**Confirmed: no durable-doc edit is owed, and none was made.** No `build_kanban_md.py`,
`build_kanban_html.py`, or `build_glossary_md.py` was run, and no `manage.py shell` was invoked.

### Adversarial re-derivation of R1

#### 1. Did the MOVE actually move? Yes.

| Measure | Value |
|---|---|
| spec bytes, `HEAD` → after R1 | 73,479 → 66,594 (`wc -c`) — R1's figures reproduce exactly |
| `Justification` occurrences, `HEAD` spec → reconciled spec | **34 → 0** — R1's figure reproduces exactly |
| `Justification` occurrences in the companion | 18 |
| top-level `##` sections, `HEAD` → reconciled | 17 → 14 |

The three cut sections (`## Pre-implementation spike outcome`, `## Borrowing posture`, `## Risks and
open questions`) are absent from the spec and present in the companion. Twenty-five distinctive
moved-text probes were counted as occurrences (not matching lines) against the reconciled spec:
`Item.__bases__ = (Base, relay.Node)`, `Explicitly do not borrow`, `Preferred answer`, `Fallback:`,
`A minimal local spike`, `0.262.0`, `is_awaitable`, `acount`, `aiter`, `READY-004`, `NEXT-00`,
`BACKLOG-0`, `BLOCKED-002`, `IN-PROGRESS-001`, `DONE-011`, `spec-relay_interfaces`, `For the current
capability snapshot` — **all 0**. **No duplication and no loss:** the spike section is reproduced
verbatim in the companion (fence included), and the eleven risk bullets are reproduced in substance.

Four mentions survive in the spec, and R1's move verification enumerated only three of them:
`MAP_AUTO_ID_AS_GLOBAL_ID` (Decision 2's own normative sentence), `super(cls, cls)` (Decision 3's
explicit prohibition), `ext.optimize` (Decision 3 naming the upstream step it does not wire), and —
unlisted by R1 — `sync_to_async`, which survives as Decision 9's normative negative "No path wraps a
sync call in `sync_to_async`". All four were read in place; none is move residue.

#### 2. Does the spec narrate its own history? No.

Scanned for `originally`, `previously`, `as of`, `no longer`, `used to`, `was changed`, `amendment`,
`retraction`, `superseded`, `earlier draft`, `formerly`, `historically`, `since then`, `review
round`, `has since`, `revised`, bare `now`, and the F3 shape specifically — a parenthetical opening
with `(historically`, `(actually`, `(in fact`, `(but `, `(though `, `(although `. **Zero matches**
except two that are not chronology:

- `## Out of scope (owned elsewhere)` says `docs/GLOSSARY.md` is "the durable catalog for whether one
  has since shipped" — a pointer to where current status lives, which is the opposite of narrating it
  in place.
- Decision 5 names the two later steps that share the Phase-2.5 window. That describes the finalizer's
  **current** composition, which a reader needs to place this slice's steps; it is not the spec
  recounting its own revisions.

#### 3. Is every rationale entry keyed to a spec decision? Yes.

All 19 `###` entries under `## Entries keyed to the spec` open with either `Spec: [<section>][ref]` or
`Bears on [Decision N][ref]`, and **every one of those anchors resolves to a heading that exists in
the reconciled spec** — checked by slugging the spec's real headings, not by reading the ref names.
The four `###` headings that carry no key sit under `## What the card actually did` and
`## Reconciliation record`; they are process records rather than entries, and the rule does not reach
them.

#### 4. Does every reconciled spec sentence hold at `HEAD`?

Sampled the highest-risk reconciled claims and **read the bodies** — grep located them, reading
cleared them.

| Reconciled claim | Verdict at `HEAD` |
|---|---|
| Four `resolve_*` signatures: `(cls)`, `(cls, root, *, info)`, `(cls, node_id, *, info, required=False)`, `(cls, *, info, node_ids=None, required=False)` | **holds** — `types/relay.py`, all four exact, `info` keyword-only throughout |
| `_resolve_id_attr_default` reads the Phase-2.5 stamp then falls back to `relay.Node.resolve_id_attr.__func__(cls)`, mapping `NodeIDAnnotationError` to `"pk"`; explicitly **not** `super(cls, cls)` | **holds** — the shipped docstring rejects that spelling by name as infinite recursion |
| `_stamp_relay_id_attr` seeds `_id_attr = None` first to blind Strawberry's inherited-cache read | **holds** — `type_cls._id_attr = None` precedes the scan; slot is `_RELAY_ID_ATTR_SLOT = "_dsf_relay_id_attr"` |
| `_resolve_id_default` coerces `"pk"` to `root.__class__._meta.pk.attname`, `__dict__` first then `getattr` | **holds**, including the `root.__class__` (not the definition's model) keying for proxy rows |
| Node defaults seed with `initial_queryset(cls)` and route visibility through `apply_type_visibility_sync` / `_async`; no direct `cls.get_queryset` call | **holds** in all four code paths |
| `node_ids` materialized once so a one-shot iterable survives both the `IN` filter and the ordering pass | **holds** — `_coerce_node_ids` returns a list, which both `_apply_node_filter` and `coerced_keys` consume |
| `required=True` raises the model's `DoesNotExist`, homogeneous with `qs.get()` | **holds** — `_order_nodes` raises `model.DoesNotExist` |
| Composite-pk gate honors the `relay.NodeID[...]` escape hatch; only `NodeIDAnnotationError` raises; asks `relay.Node.resolve_id_attr.__func__(type_cls)` directly | **holds** — and the shipped comment gives the same reason the spec does (a relay-shaped child inheriting the parent's installed default would slip the gate) |
| Detection is `isinstance(model._meta.pk, CompositePrimaryKey)`; the error names the model and proposes the annotation or removing `relay.Node` | **holds**, message read in full |
| Suppression predicate `_is_relay_shaped(cls, interfaces)` = `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)` | **holds** — verbatim |
| What is dropped is `model._meta.pk.name`, compared against `field.name`; the pk stays in `fields` for the optimizer | **holds** — `continue` skips annotation synthesis only; the shipped comment gives the same `OneToOneField(primary_key=True)` `name`/`attname` reason |
| Async: `strawberry.utils.inspect.in_async_context()`, native `aget` / `afirst` / `async for`; no `sync_to_async`, no `acount`, no `aiter` | **holds** — `grep -E "sync_to_async\|acount\|aiter\("` over the `HEAD` blob of `types/relay.py` returns nothing |
| `SyncMisuseError(ConfigurationError, RuntimeError)`, unawaited coroutine closed before the raise | **holds** — defined in `utils/querysets.py`, re-exported from `types/relay.py`; `_dispose_sync_awaitable` calls `value.close()` before `raise` |
| Phase 2.5 order: `apply_interfaces` → `_check_composite_pk_for_relay_node` → `install_relay_node_resolvers` → `install_globalid_typename_resolver`, all before the `strawberry.type(...)` loop | **holds** — `types/finalizer.py`, exact order, with `Meta.cursor_field` validation after |
| `"interfaces"` in `ALLOWED_META_KEYS`; `DEFERRED_META_KEYS == {aggregate_class, fields_class, search_fields}` | **holds** |
| `strawberry-graphql>=0.316.0`, `Django>=5.2.16` | **holds** — `pyproject.toml` |
| Decision 4's eighth rule: six `strawberry.relay` non-interface helpers rejected by identity, before the non-class branch | **holds** — `_RELAY_NON_INTERFACE_HELPERS`, identity comparison `entry is helper` |
| Decision 6's `is_type_of` discriminator is `cls.__dict__` membership | **holds** |
| The `## Current state` glossary quotation matches the glossary's current wording | **holds** — the glossary wraps the sentence across three lines, which is why a naive single-line grep reports zero; the reconciled quotation matches the unwrapped text exactly |
| `README.md #"The public names are stable"` (R1's re-anchor for the retired capability-snapshot citation) | **holds** — resolves once |

**Every test the Test plan names exists at `HEAD`, enumerated rather than ratioed** (see the count
corrections for why R1's "30 of 33" is not re-derivable as stated). Each `grep -c "def <name>("`
returns exactly 1: **30** in `tests/types/test_relay_interfaces.py`, **3** in
`tests/optimizer/test_relay_id_projection.py`, **1** in `tests/test_registry.py`, **3** in
`examples/fakeshop/test_query/test_library_api.py`, **2** in
`examples/fakeshop/test_query/test_products_api.py`. `test_relay_target_relation_planning_unchanged`
returns **0**, which is the retirement R1 documented.

Six bodies were read, not grepped:

- `::test_resolve_id_attr_falls_back_to_pk` asserts `CategoryNode.resolve_id_attr() == "pk"` and
  `_resolve_id_attr_default(CategoryNode) == "pk"` — so R1's correction of the spec's old
  "concrete pk attname" claim is right.
- `::test_node_id_annotation_overrides_default_id_attr` annotates the **target column**
  (`name: relay.NodeID[str]`), subscripted, and its docstring records the bare
  `Annotated[str, relay.NodeID]` trap — both facts now in the spec's `## User-facing API`.
- `::test_products_optimizer_selects_nested_forward_fk_depth_2_over_http` — **R1's central finding
  independently reproduced.** The name says `selects` and the docstring says the opposite: "Before
  spec-034 this query planned a single `select_related("item__category")` JOIN. With the cascade
  hooks active … the optimizer downgrades each forward FK … to a windowed `Prefetch`", and the row
  pins a 3-query Prefetch chain with no inter-products JOIN. The reconciled Decision 7 and Test plan
  make no ORM-verb claim about it, which is correct.
- `::test_products_optimizer_prefetches_nested_reverse_fk_depth_2_over_http` pins 1 categories slice +
  2 prefetches = 3 queries, no COUNT.
- The two live library twins assert exactly what the reconciled Test plan says (`"Node" in
  interface_names` and `NON_NULL(ID)` on `GenreType`; `Node` absent from `ShelfType` and
  `ShelfType.id != ID`), and both docstrings name themselves the live twin of the retired package
  test.

`examples/fakeshop/apps/products/schema.py` carries **4** `interfaces = (relay.Node,)` declarations,
matching the spec's "four Relay-declared `products` types";
`examples/fakeshop/apps/library/schema.py` carries `interfaces = (relay.Node, Named)`, the mixed
Relay / non-Relay case.

#### Finding R2-a (High) — the reconciliation retired four cited `#"substring"` anchors

`AGENTS.md` rule 27 lets shipped source cite a spec as `spec-NNN #"unique substring"`. Eleven distinct
substrings of this spec are quoted from `django_strawberry_framework/types/relay.py` and
`tests/types/test_relay_interfaces.py` (plus three more quoted under the pre-renumber `spec-011`
name). **Rewording a cited sentence retires its anchor exactly the way renaming a symbol retires a
`::QualifiedName`** — and rule 27 makes the grep-sweep part of the same change. R1's rewrite broke
four of the eleven, dangling **seven citation sites across two files**:

| Substring | Was in | Cited from | Why it broke |
|---|---|---|---|
| `is removed from synthesized scalar annotations` | Decision 2 | `tests/…::test_relay_node_strips_django_id_annotation` | rewrite inserted the word "the" |
| `Composite primary keys (Django 5.2+) are explicitly out of scope` | Decision 2 | `types/relay.py::_check_composite_pk_for_relay_node`, `tests/…::test_relay_node_with_composite_pk_raises` | "explicitly" dropped |
| `injection (Decision-1 borrow) is added unconditionally` | Decision 6 | `types/relay.py::install_is_type_of`, `tests/…::test_is_type_of_injected_for_all_djangotypes` | parenthetical dropped as borrowing-posture residue |
| ``surface any `TypeError` as a `ConfigurationError` `` | `## Risks and open questions` | `types/relay.py::apply_interfaces`, `tests/…` (the `ConfigurationError`-wrap row) | the whole section was moved to the companion |

Verified by counting occurrences in the `HEAD` blob of the spec versus the reconciled spec: 1 → 0 for
each of the four; the other seven are 1 → 1.

**Disposition.** The first three are restored in the spec — each sentence is otherwise unchanged, each
remains true at `HEAD`, and restoring costs the reconciliation nothing. The fourth is **not**
restored: putting a moved risk-register sentence back would undo the move and create two sources for
one deliberation, so the bullet is instead quoted **verbatim** in the companion's new addendum, where
the citation resolves inside spec-015's own file family. The ideal repair — re-anchoring that one
source comment at `types/relay.py::apply_interfaces` and its test — is a source edit on files dirty
with the concurrent cycle, and is catalogued.

After the repair, **all 13 substrings resolve**: 11 exactly once in the spec, or (for the moved one)
in the companion.

#### Finding R2-b (Medium) — a dead `::QualifiedName` carried forward in Decision 7

Decision 7's FK-id-elision invariant cited
`django_strawberry_framework/types/resolvers.py::_is_fk_id_elided`. **That symbol does not exist at
`HEAD`** — `git grep "_is_fk_id_elided" HEAD -- django_strawberry_framework/` returns nothing — and it
did not exist when R1 ran either; the citation was inherited verbatim from the `HEAD` spec, in the one
Decision R1 otherwise rewrote. It is a renamed-symbol sweep (`AGENTS.md` rule 27) that never reached
the archived spec.

The resolver-side executor is `types/resolvers.py::_build_fk_id_stub`; the walker-side predicate
`optimizer/walker.py::_can_elide_fk_id` cited in the same parenthesis was always correct. **Fixed** in
the spec. A full sweep of the reconciled spec now resolves **20** `path::Symbol` refs and **18**
`#"substring"` citations against `HEAD` with no dead reference (upstream `strawberry_django/…` and
`django_graphene_filters/…` refs excluded — they name local comparison checkouts, not repo paths).

#### Finding R2-c (Low) — Decision 3's code fence did not match the shipped guard

R1's rationale lists "Decision 3's injection loop" among the things "accurate at `HEAD` and … left
alone". It was not accurate. `types/relay.py::install_relay_node_resolvers` guards with

```python
if existing is None or (existing_func is not None and existing_func is node_func):
```

where the spec's fence compared two `getattr(…, "__func__", None)` results directly — so an existing
attribute with **no** `__func__` (a plain function a consumer assigned) would match a `None` default
and be silently overwritten, losing the consumer's override. That is a contract-relevant divergence,
not cosmetic. **Fixed:** the fence carries the shipped guard, and the sentence below it now attributes
the identity test to strawberry-django and the added clause to this package, so "direct copy" stays
true of the half that is one.

#### Finding R2-d (Low) — two non-unique `#"substring"` anchors, pre-existing

`pyproject.toml #"version ="` matches **2** times and
`types/finalizer.py #"_attach_relation_resolvers"` matches **3**, against rule 27's "unique
substring". Both predate this cycle — present identically in the `HEAD` spec — and both point at the
right place. Recorded, not changed: rewriting a working anchor to buy uniqueness risks the exact
breakage finding R2-a is about.

#### R1's counts, re-derived

`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`: a stated count
reads as measured and propagates. Correcting them here rather than editing R1's artifact.

| R1's claim | Re-measured | Verdict |
|---|---|---|
| spec `73,479 → 66,594` bytes | identical | **exact** |
| rationale `63,860` bytes, `910` lines | identical | **exact** |
| `34` `Justification` passages at `HEAD` → `0` | identical | **exact** |
| `## Risks and open questions` = `5,568` bytes | identical | **exact** |
| Decisions 1, 2, 3, 6, 8 and the header block each carry a rationale pointer | 6 uses of `[spec-015-rationale]`, at exactly those sites | **exact** |
| F14's eight `[spec-011]` sites | identical | **exact** |
| spec `627 → 595` lines | **626** → 595 (`wc -l` and `awk 'END{print NR}'` agree; the file ends with a newline, so no off-by-one to recover) | **off by one on the "before"** |
| `## Borrowing posture` = `6,210` bytes | **6,230**, taking the section as its heading line through the line before the next `## ` | **off by 20**; the measurement convention is not stated, so neither figure is reproducible from the artifact alone |
| "All 19 `[glossary-*]` defs are still used **exactly once** in the body" | 19 defs, **21** uses: `glossary-configurationerror` (Slice 4 checklist + Decision 1) and `glossary-metaprimary` (`## Non-goals` + Decision 8) are each used **twice** | **wrong as stated**; the load-bearing half — every def used at least once, none orphaned — holds |
| "**30 of 33** by name; the other 3 relocated" | the named population is 30 (`test_relay_interfaces.py`) + 3 (projection) + 1 (registry) + 3 (live library) + 2 (live products) present, and 3 retired; no partition of that reproduces 33 as the denominator | **not re-derivable as stated**; the enumeration above replaces the ratio |
| rationale: "the spec keeps **four** fenced blocks — the **three** consumer examples … — and gains none" | **six** fenced blocks (7 before, 6 after): **four** `## User-facing API` examples, Decision 3's loop, and the restated `## Internal helper surface` list, which is a **new** fence | **wrong on three counts**; corrected in place in the companion and listed in its addendum |

Two looseness items, recorded and not treated as defects: the eleven risk bullets are reproduced as a
three-column summary table rather than verbatim, so "*Moved, all eleven bullets*" is true of the
substance and not the wording (the one bullet a source comment cites is now verbatim in the addendum);
and the Test plan's projection bullets illustrate `{ allItems { id } }` / `{ allItems { id
otherScalar } }` where the shipped rows send `{ allCategories { id } }` / `{ allCategories { id
name } }` — the invariant each bullet describes is the one its row asserts, so only the example query
name is off.

### Checklist audit

Every box in `### Dispatched findings checklist` is `- [x]`, each ticked against a re-derived
measurement rather than against the plan's figures or R1's. No box is deferred. F14 is ticked as
**verified and catalogued**, which is what it was dispatched as — the plan states in terms that it is
recorded, not dispatched for repair.

### Staged-anchor sweep

`grep -rEn 'TODO\(spec-015|TODO-(ALPHA|BETA|STABLE)-015' .` outside `KANBAN.md` / `KANBAN.html` /
`BACKLOG.md` / `.git/` → **no matches**. Nothing staged under this spec's or card's name survives in
shipped source, tests, or docs.

### Gates run

| Command | Result |
|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-015-relay_interfaces-0_0_5.md` | `OK: 19 terms …` (exit 0) — was `OK: 18 terms` before this pass |
| `uv run python scripts/check_trailing_commas.py --check <the three writable files>` | exit 0 |
| link / anchor / group-header audit over both Markdown files | 0 problems |
| terms-CSV one-row-per-anchor shape, and set equality with the spec's anchors | 0 problems |
| `spec-015 #"…"` and `path::Symbol` sweep of the spec against `HEAD` | 0 dead references (2 non-unique anchors, finding R2-d) |
| staged-anchor sweep | no matches |

No `pytest` was run: this item's writable set contains no code and no test, the plan declares
floor-verification scope `none`, and the focused-test obligation in `## Final verification job` step 5
has no scope to act on. No `--cov*` flag was used.

### Spec changes made (Worker 1 only)

All in `docs/SPECS/spec-015-relay_interfaces-0_0_5.md`, triggered by item R2's adversarial
re-derivation. Line numbers omitted per `AGENTS.md` rule 27; each change names its section.

| Section | Change | Reason |
|---|---|---|
| Decision 2, pk-suppression bullet | "removed from **the** synthesized scalar annotations" → "removed from synthesized scalar annotations" | R2-a: restores the anchor `tests/…::test_relay_node_strips_django_id_annotation` cites |
| Decision 2, composite-pk paragraph | "are out of scope" → "are **explicitly** out of scope" | R2-a: restores the anchor `types/relay.py::_check_composite_pk_for_relay_node` and its test cite |
| Decision 6, `is_type_of` bullet | restored the "(Decision-1 borrow)" parenthetical | R2-a: restores the anchor `types/relay.py::install_is_type_of` and its test cite |
| Decision 7, FK-id-elision invariant | `types/resolvers.py::_is_fk_id_elided` → `::_build_fk_id_stub` | R2-b: the cited symbol does not exist at `HEAD` |
| Decision 3, injection-loop fence | added the shipped `existing_func is not None` guard; the sentence below now attributes the identity test to strawberry-django and the added clause to this package | R2-c: the fence would have overwritten a consumer override that has no `__func__` |

Spec: **66,594 → 66,926 bytes**, 595 → 596 lines.

Changes to `docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md` (Worker-1-owned; the file's
append-only discipline was kept — no entry, argument, or disposition was rewritten or removed):

- Appended `## Addendum: substring-anchor stability, and four counts re-measured`, keyed to Decisions
  1, 2, 3, 6, and 7, carrying findings R2-a through R2-c, the verbatim `cls.__bases__` risk bullet
  (so the fourth citation resolves inside the companion), and every count correction.
- Corrected three purely numeric statements in place, each also listed in the addendum: `627 → 626`
  spec lines (twice), and the fenced-block accounting ("four" → six, "three consumer examples" →
  four, "gains none" → gains one).

Changes to `docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-terms.csv`:

- Added `public exports,public-exports,Backfilled for DONE-card glossary linkage from the shipped
  spec body.` in the file's existing alphabetical-by-`term` position (F13).

### Notes for Worker 1 (spec reconciliation) — carried to the final gate

R1's four deferred items are all still open and all still correct; this pass closed the fourth (the
terms-CSV gap) on the CSV side only, which splits it. Six items for the
`### Deferred work catalog`, none of them a code defect:

1. **The `DONE-015-0.0.5` card-side glossary sync (new half of plan F13).** The CSV is now complete at
   19 rows; the card still renders 18 terms and `import_spec_terms --check` will report this card's
   mention set short by one until `uv run python examples/fakeshop/manage.py import_spec_terms` runs
   and `build_kanban_md.py` / `build_kanban_html.py` regenerate. That is a database write plus a
   regenerate of two files this cycle is barred from touching (`docs/GLOSSARY.md` and `docs/TREE.md`
   are dirty with concurrent work, and `db.sqlite3` is clean at `HEAD` — a partial write now would
   hand the maintainer a mixed diff). Source artifact: this artifact's F13 section.
2. **Re-anchoring the one source citation the move legitimately stranded (from R2-a).**
   `types/relay.py::apply_interfaces` and the corresponding row in
   `tests/types/test_relay_interfaces.py` cite `spec-015 Risk note #"surface any \`TypeError\` as a
   \`ConfigurationError\`"`, and that section now lives in the rationale companion. The substring is
   quoted verbatim there so the citation resolves inside the file family, but the ideal fix retargets
   the comment at `docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md` or at Decision 1's
   own `ConfigurationError`-wrap sentence. Both files are dirty with the concurrent hardening cycle.
3. **The `[spec-011]` citation cluster (plan F14).** Eight sites in four files, re-verified above;
   homed on `TODO-ALPHA-051-0.0.15`; files dirty. Recorded, not stolen, not partial-fixed. Worth
   folding item 2 into the same batch — it is the same class of defect in the same two files.
4. **The A/B relation-planning row (R1's finding).** No current row asserts that planning across a
   Relay-declared target matches planning across a non-Relay one; the retired
   `test_relay_target_relation_planning_unchanged` was that A/B row, and every products type now
   carries a `get_queryset`, so the live replacements all take the downgrade path. Writing it is a
   test change this cycle is not authorized to make.
5. **A stale cross-reference inside a shipped test docstring (R1's finding, re-confirmed by
   reading).** `tests/types/test_relay_interfaces.py::test_relay_node_strips_django_id_annotation`
   closes with "End-to-end coverage of the same suppression path lives in
   `tests/types/test_definition_order_schema.py`" — the file whose two Relay extensions `be9130e3`
   retired for the live twins. Accurate that end-to-end coverage exists, wrong about where. Test-file
   edit, outside the writable set.
6. **Two non-unique `#"substring"` anchors in the spec (R2-d).** `pyproject.toml #"version ="` (2
   matches) and `types/finalizer.py #"_attach_relation_resolvers"` (3). Pre-existing at `HEAD`, both
   pointing at the right place; a future custodian pass may tighten them, and finding R2-a is the
   reason to sweep the source citations in the same change if it does.

Notes for Worker 0 (the plan is Worker 0's file):

- **The plan's F13 evidence line needs one word.** "The spec body links **19** glossary anchors; the
  terms CSV carries **18**" was correct when written and is correct as history, but the CSV now
  carries 19. The plan's `### R2 findings` table should read as closed.
- **R1's two plan corrections are already folded in** under `## Corrections to this plan, recorded`;
  both re-verified here (V12's evidence sentence, and the `4f4db722` / `be9130e3` row order).
- **The plan's `## Artifact list` and `## Checklist` are otherwise accurate**; R2's box is ready to
  mark `- [x]`.

### Final status

`final-accepted`.

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
