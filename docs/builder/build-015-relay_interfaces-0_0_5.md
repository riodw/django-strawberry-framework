# Package build plan: relay_interfaces / 0.0.5 (015) — residual-completion cycle

Spec source: `docs/SPECS/spec-015-relay_interfaces-0_0_5.md` (already archived; card `DONE-015-0.0.5`)
Rationale companion: `docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md` — **does not exist**; creating it is this cycle's first obligation.
Terms companion: `docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-terms.csv` (exists, 18 rows, one row per anchor — importable shape; `check_spec_glossary` green — `OK: 18 terms`). One gap: see F13.
Target release: `0.0.5` (shipped; this cycle bumps no version and lands no feature).
Build rule: one item at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every item must justify shared/duplicated patterns before merging.
Ownership partition: none; sequential items. R1 and R2 both write the spec file, so they could not run concurrently even if the rest were disjoint.
Hot-path declaration: none. Both items write Markdown only; no package source and no test is in any item's writable set.
Floor-verification scope: **none.** No item touches a Django / Strawberry / channels integration seam — no item touches executable code at all.
Pre-flight: passed on 2026-08-16 with two recorded deviations (steps 3 and 5, below); baseline: **dirty with concurrent sessions' work — 189 paths, none of them this cycle's**; cleanup: **nothing deleted or cleared** (deviation, below); memory files namespaced per cycle.

## Why this cycle exists

Card `DONE-015-0.0.5` shipped at `0.0.5`, so the code is not in question as *new* work. Three obligations, in the maintainer's framing:

1. **Nothing was skipped in the code.** Everything spec-015 promised must be present at `HEAD`, and anything promised and never delivered is a defect this cycle fixes.
2. **Later work that changed the shipped shape is legitimate — but the spec must say so.** Where a later card corrected, superseded, or completed something spec-015 owns, the spec is rewritten to state the **current** contract directly. It never narrates the change (`docs/builder/BUILD.md` `## Spec rationale extraction`).
3. **The explanation goes in the rationale, not the spec.** What changed, why, which commit caused it, and what the spec may no longer claim — all of it lands in the rationale companion, keyed to the spec section it belongs to.

Spec-015 is the **opposite shape** from its four predecessors in this series. Specs 011-013 were card-snapshot stubs whose rationale had to be *reconstructed* from history; spec-014 was a genuine design record its own implementing commit *destroyed in place*, so its rationale was a *restoration*. Spec-015 is a **complete, intact, 627-line pre-implementation design record that survived** — nine numbered Decisions, a borrowing posture with per-borrow justifications, a pre-implementation spike, an internal helper surface, an eleven-bullet risks-and-open-questions section, and a twelve-item Definition of done. Its rationale companion is therefore the one case in the series that is a **true `## Spec rationale extraction` MOVE** — cut-and-paste out of the spec, exactly as `BUILD.md` specifies for a live build — rather than a reconstruction or a restoration. That fact shapes R1 completely.

## Worker-0 verification pass (performed before any dispatch)

`docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching`. Every finding below was read against `HEAD` (`4c9e4e0d`) before this plan was written; each cites its symbol-qualified path (`AGENTS.md` rule 27) or its commit. A finding is dispatched only if it holds.

Every source and test path this pass read is **dirty with a concurrent session's work**, so every reading was taken from `git show HEAD:<path>` into a scratch path outside the repo, per `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`. Any item needing them does the same.

### What the card actually did — recovered from history

| Commit | What it did for this card |
|---|---|
| `b756e515` "0.0.5 plan spec-relay_interfaces start" | Authored `docs/spec-relay_interfaces.md`. |
| `cc2f0981`, `904fcfa0`, `3982978d`, `9c677b95`, `32dea521` | Spec authoring: slice checklist, content-versioned Node draft (later dropped), kanban tracking, `0.0.5` prep. |
| `e6907fa8` "Finish slice 4" | **The card's implementation.** Authored `types/relay.py`, Phase 2.5, `_build_annotations` suppression, the four `resolve_*` defaults, and every test the Test plan names — including the three later relocated (V11, V12). |
| `e836d72e` "Finish docs/spec-relay_interfaces.md" | Slice 5: promotion, docs, version bump. |
| `a7c8f8ff` / `df13b644` / `40c1855f` / `3ed0bb84` | Spec relocation to `docs/SPECS/`, numbering to `spec-011-relay_interfaces-0_0_5.md`, `path:NN` → symbol-qualified conversion. |
| `81e4704d` "docs: archive prior specs to docs/SPECS/ and renumber per Step 8 pass" | **Renumbered `spec-011-relay_interfaces` → `spec-015-relay_interfaces`.** The source citations were not swept (F14). |

Three later commits changed what spec-015 owns without touching the spec (chronological):

| Commit | Date | What it changed |
|---|---|---|
| `4f4db722` "tests: relocate optimizer behavioral coverage from package tests to live /graphql/ HTTP" | 2026-06-02 | Retired `test_relay_target_relation_planning_unchanged` in favour of live products coverage (V12). |
| `be9130e3` "Migrate package tests to the live /graphql/ fakeshop suite" | 2026-06-13 | Retired the two `test_definition_order_schema.py` schema-construction tests in favour of live twins (V11). |
| `6912ca92` "DRY pass (docs/feedback.md round): query-source, selection, and set-family substrates" | — | Replaced the resolvers' hand-rolled `_default_manager.all()` + `cls.get_queryset(...)` with the shared `initial_queryset` / `apply_type_visibility_*` boundary (V13). |

### V1-V15: nothing was skipped in the code — verified, not assumed

| # | Claim to verify | At `HEAD` | Evidence |
|---|---|---|---|
| V1 | `"interfaces"` is promoted to `ALLOWED_META_KEYS` and gone from `DEFERRED_META_KEYS` (Slice 5, DoD 1) | both true | `types/base.py #"ALLOWED_META_KEYS: frozenset[str]"` contains `"interfaces"`; `DEFERRED_META_KEYS` is `{"aggregate_class", "fields_class", "search_fields"}` |
| V2 | `_validate_meta` carries the Decision-4 interface validator with all seven rules | all present, **plus** a later addition | `types/base.py::_validate_interfaces` — normalizes tuple/list and a single class, rejects strings, non-sequences, string entries, non-`DjangoType`, non-interfaces, and duplicates. Spec-032 Decision 8 added a named rejection for six `strawberry.relay` non-interface helpers (`_RELAY_NON_INTERFACE_HELPERS`) |
| V3 | the normalized tuple reaches `DjangoTypeDefinition.interfaces` and no new slot was added | true | `types/base.py::_validate_meta` returns it on `_ValidatedMeta.interfaces`; `DjangoType.__init_subclass__` passes `interfaces=validated.interfaces` |
| V4 | `install_is_type_of` exists in `types/relay.py` and is invoked for **every** `DjangoType` (Decision 6) | exists, invoked | `types/relay.py::install_is_type_of`, imported at `types/base.py` module top (`from .relay import install_is_type_of`); `cls.__dict__` discriminator preserves a consumer-declared `is_type_of` |
| V5 | `id` suppression lands in `_build_annotations` (Slice 3, Decision 2) | present, **widened** | `types/base.py::_build_annotations #"suppress_pk_annotation = _is_relay_shaped(cls, interfaces)"` — see F6 for the widening |
| V6 | the pk field survives in `field_map` for the optimizer (Decision 7) | true | the suppression `continue`s past annotation synthesis only; `fields` is untouched — `types/base.py::_build_annotations #"so the optimizer's field map still sees it as a connector"` |
| V7 | `types/relay.py` carries all four `_resolve_*_default` implementations | all four | `_resolve_id_attr_default`, `_resolve_id_default`, `_resolve_node_default`, `_resolve_nodes_default` — but see F7/F8 for signature and body drift |
| V8 | the three named helpers exist | all three | `types/relay.py::apply_interfaces`, `::implements_relay_node`, `::install_relay_node_resolvers` |
| V9 | Phase 2.5 runs between Phase 2 and Phase 3 in the declared order | exact | `types/finalizer.py::finalize_django_types` — `apply_interfaces` → `_check_composite_pk_for_relay_node` → `install_relay_node_resolvers` → (spec-031's `install_globalid_typename_resolver`), all before the `strawberry.type(...)` loop |
| V10 | the composite-pk gate raises `ConfigurationError` naming the model (Decision 2, DoD 4) | raises, **with an escape hatch** | `types/relay.py::_check_composite_pk_for_relay_node` — `isinstance(model._meta.pk, CompositePrimaryKey)`; see F9 |
| V11 | every test the Test plan names exists | **30 of 33 by name; the other 3 relocated, none skipped** | the 30 in `tests/types/test_relay_interfaces.py` and `tests/optimizer/test_relay_id_projection.py` each `grep -c "def <name>("` -> 1. The two `test_definition_order_schema.py` extensions **were built at `e6907fa8`** as `test_relay_declared_type_emits_node_interface_and_global_id` / `test_mixed_relay_and_non_relay_types_introspect_cleanly`, then **relocated at `be9130e3`** to `examples/fakeshop/test_query/test_library_api.py::test_relay_genre_type_emits_node_interface_and_global_id_live` / `::test_mixed_relay_and_non_relay_no_interface_bleed_live`, whose docstrings name themselves "the live twin of" the retired package tests |
| V12 | `test_relay_target_relation_planning_unchanged` (Decision 7's fourth invariant) | **built, then relocated — not skipped** | added at `e6907fa8`, removed at `4f4db722`. The invariant is now pinned live: `tests/optimizer/test_relay_id_projection.py`'s module docstring states "Ordinary relation traversal across Relay-declared fakeshop targets is pinned through live HTTP in `examples/fakeshop/test_query/test_products_api.py`", and that holds — `apps/products/schema.py` carries 4 `interfaces = (relay.Node,)` declarations and the live suite pins forward-FK `select_related` (`::test_products_optimizer_selects_nested_forward_fk_depth_2_over_http`) and reverse-FK `prefetch_related` (`::test_products_optimizer_prefetches_nested_reverse_fk_depth_2_over_http`) across them |
| V13 | the registry-idempotency extension exists (Test plan) | exists | `tests/test_registry.py::test_registry_clear_allows_fresh_relay_declared_type_to_finalize`, asserting `relay.Node in FreshCategoryNode.__mro__` after `clear()` + redefinition |
| V14 | the live HTTP GlobalID round-trip test exists (Slice 4, Test plan) | exists | `examples/fakeshop/test_query/test_library_api.py::test_library_relay_node_global_id_round_trips` |
| V15 | the non-Relay-interface path is exercised in the example project (Decision on generic interfaces) | exercised | `examples/fakeshop/apps/library/schema.py #"interfaces = (relay.Node, Named)"` — a plain `@strawberry.interface` alongside `relay.Node`, and `::test_mixed_relay_and_non_relay_no_interface_bleed_live` plus the `{"Node", "Named"}` introspection assertion pin it live |

**No code defect was found in this cycle's scope. No source or test file is in any item's writable set, so no Worker 2 pass is dispatched** — which is the disposition the maintainer's dispatch instruction anticipated. The one source-level issue this pass found (F14) is verified, already homed on a live card, and catalogued rather than stolen; the reasoning is under F14.

### R1 findings — the spec's own text

Each is a claim later work falsified, or a deliberative layer that never got a home. None is a code defect.

| # | Finding | Evidence |
|---|---|---|
| F1 | **No rationale companion exists, and this is the one spec in the series with a complete, intact deliberative layer to move.** `## Borrowing posture` (with its per-borrow "Justification:" paragraphs), `## Pre-implementation spike outcome`, the nine Decisions' justifications, `## Internal helper surface`, and `## Risks and open questions` are all present and all deliberative. R1 performs a genuine `BUILD.md` `## Spec rationale extraction` **move** — cut, not copy, not summarize. | `ls docs/SPECS/appx/spec-015-*` returns only the terms CSV |
| F2 | `Status:` claims the file is "the merged, canonical result of three superseded drafts (`-1.md`, `-2.md`, and `-3.md`), all of which have been deleted" **and** Slice 5 still carries an unticked cleanup box "Delete `docs/spec-relay_interfaces-3.md`". Both cannot be current; the file is at `docs/SPECS/` and no draft survives. | `ls docs/spec-relay_interfaces*` returns nothing; spec `## Slice checklist` #"Delete `docs/spec-relay_interfaces-3.md`" |
| F3 | `## Current state` says `types/base.py` "keeps `interfaces` in `DEFERRED_META_KEYS`", then parenthetically contradicts itself ("by `0.0.5` the key is already in `ALLOWED_META_KEYS` per the historical comment block"). The parenthetical is a prior reconciliation patched **over** the stale sentence rather than replacing it — precisely the "spec narrates its own history" shape `BUILD.md` forbids. | V1; spec `## Current state` first bullet |
| F4 | Decision 3 sketches `_resolve_id_attr_default` as `super(cls, cls).resolve_id_attr()`. At `HEAD` that spelling is **explicitly rejected in the shipped docstring** as infinite recursion for a relay-shaped child of a relay-shaped parent; the shipped default reads a Phase-2.5 stamp (`_RELAY_ID_ATTR_SLOT`) and falls back to `relay.Node.resolve_id_attr.__func__(cls)`. | `types/relay.py::_resolve_id_attr_default #"Deliberately NOT ``super(cls, cls).resolve_id_attr()``"`; `::_stamp_relay_id_attr` |
| F5 | Decision 9 claims "the new resolvers call `ext.optimize(qs, info=info)` with the same signature the existing root-gated optimizer uses". **They do not** — Decision 3 in the same spec says the optimizer-extension consultation is deferred, and the shipped resolvers consult no extension. The spec contradicts itself and one half is false. | `types/relay.py::_resolve_node_default` / `::_resolve_nodes_default` contain no optimizer call; spec Decision 3 #"is deferred to a follow-up slice" |
| F6 | Decision 2 and Slice 3 both scope suppression to "when `relay.Node` is among `Meta.interfaces`" and to dropping "the `id` key". At `HEAD` it is **wider on both axes**: `_is_relay_shaped(cls, interfaces)` also fires for direct inheritance (`class Foo(DjangoType, relay.Node)`) and for any `@strawberry.interface` subclassing `relay.Node`, and it drops `source_model._meta.pk.name` — the pk field's *name*, not the literal `"id"` — so a renamed or relation primary key is handled. | `types/base.py::_build_annotations #"suppress_pk_annotation = _is_relay_shaped"`, #"pk_name = source_model._meta.pk.name"; `::_is_relay_shaped` |
| F7 | `## Internal helper surface` and Decision 3 pin resolver signatures that **no shipped resolver has**. Spec: `_resolve_id_default(cls, root, info)`, `_resolve_node_default(cls, info, node_id, required=False)`, `_resolve_nodes_default(cls, info, node_ids=None, required=False)`. `HEAD`: `(cls, root, *, info)`, `(cls, node_id, *, info, required=False)`, `(cls, *, info, node_ids=None, required=False)`. The shipped docstring records why: the spec's positional-`info` shape produced "`TypeError: got multiple values for argument 'info'`" from Strawberry's call machinery. This drift is **as-built** (`e6907fa8`), not later churn. | `types/relay.py::_resolve_node_default #"An earlier draft used ``(cls, info, node_id, ...)``"` |
| F8 | Decision 3's `_resolve_node_default` body sketch is `_default_manager.all()` → `cls.get_queryset(qs, info)` → `.filter(...)`. At `HEAD` both halves route through the shared sealed-visibility boundary — `initial_queryset(cls)` and `apply_type_visibility_sync` / `apply_type_visibility_async` — landed by the `6912ca92` DRY pass and hardened by the spec-045 sealed-execution-queryset work. | `types/relay.py::_resolve_node_default`; `utils/querysets.py::apply_type_visibility_sync` |
| F9 | Decision 2 and DoD 4 state the composite-pk case raises unconditionally. At `HEAD` the gate **honors the escape hatch its own error message proposes**: a type declaring an explicit `id: relay.NodeID[...]` passes, and only a `NodeIDAnnotationError` (no annotation) raises. It also asks `relay.Node.resolve_id_attr.__func__` directly rather than `type_cls.resolve_id_attr()`, so a relay-shaped child cannot inherit the parent's `"pk"` fallback and slip the gate. | `types/relay.py::_check_composite_pk_for_relay_node` |
| F10 | Decision 9 names the async-detection mechanism as "Strawberry's `info` carries an `is_awaitable` signal; `asgiref.sync.iscoroutinefunction` is the fallback" and promises `sync_to_async` wrapping plus `aiter`/`acount`. `HEAD` uses `strawberry.utils.inspect.in_async_context()` and Django's native `aget` / `afirst` / `async for` only — no `sync_to_async`, no `acount`. It also ships a contract the spec never mentions: a sync resolver context meeting an async `get_queryset` raises `SyncMisuseError` rather than failing with `AttributeError` on a coroutine. | `types/relay.py::_resolve_node_default`, `::_resolve_node_async`, `::_resolve_nodes_async` |
| F11 | `## Risks and open questions` states the lower bound as `strawberry-graphql>=0.262.0`, and `## Internal helper surface` repeats it. At `HEAD` it is `strawberry-graphql>=0.316.0`; the Django floor is `Django>=5.2.16`. | `pyproject.toml #"strawberry-graphql>=0.316.0"` |
| F12 | Every KANBAN id the spec cites is pre-renumber and now names a different card or nothing: `READY-004`, `READY-002`, `READY-003`, `READY-005`, `NEXT-005`, `NEXT-006`, `NEXT-001`, `NEXT-002`, `BACKLOG-005`, `BACKLOG-007`, `BACKLOG-009`, `BACKLOG-011`, `BACKLOG-012`, `BLOCKED-002`, `IN-PROGRESS-001`, `DONE-011`. Five of the deferrals they name have since shipped (`Meta.primary` `0.0.6`, filters/orders `0.0.8`, `DjangoConnectionField` + `DjangoNodeField` `0.0.9`, cascade permissions `0.0.10`); `FieldSet` and aggregates are still ahead on the `0.1.x` line. **`worker-0.md` #"Verify card/glossary references against the DB" applies: do not partial-fix.** The correct reconciliation states the current contract (what shipped, what is still deferred) rather than renumbering stale ids one by one. | `KANBAN.md`; `docs/README.md` shipped list |

### R2 findings — documentation completion and archive audit

| # | Finding | Evidence |
|---|---|---|
| F13 | The spec body links **19** glossary anchors; the terms CSV carries **18**. `public-exports` — linked at spec `## Slice checklist` #"No new [public exports]" and at DoD 11 — is absent from the CSV, so `DONE-015-0.0.5` renders 18 glossary terms and does not link it. Every other anchor round-trips. | derived by parsing the spec's link-definition block against the CSV; `KANBAN.md` `### [DONE-015-0.0.5 …]` `#### Glossary terms` renders 18 rows |
| F14 | **The `[spec-011]` renumber artifact is spec-015's own identity, and it reaches eight sites.** `81e4704d` renamed `spec-011-relay_interfaces-0_0_5.md` → `spec-015-…` without sweeping the citations, so six shipped-source and two test comments now point at `spec-011-stale_placeholder_cleanup-0_0_4.md`, a different document. Verified by substring: `"An empty tuple is the same as not declaring"`, `"may be a tuple/list of interface classes"`, and `"keeps every selected Django field including the primary key"` each resolve **1** time in spec-015 and **0** times in spec-011. Sites: `types/base.py` x5 (`::_validate_interfaces` docstring x2, `::_validate_meta` docstring, `::_build_annotations` docstring + inline comment), `types/resolvers.py` x1, `tests/types/test_base.py` x1, `tests/filters/test_sets.py` x1. | `git grep -n "spec-011" HEAD -- django_strawberry_framework/ tests/` |
| F15 | The archive move is **already done** — the spec is at `docs/SPECS/`, its terms CSV at `docs/SPECS/appx/`, the link block carries all ten canonical group headers, every `../GLOSSARY.md#…` def resolves, and `check_spec_glossary` is green. What R2 owes is the audit plus the new companion's own link hygiene, not a move. | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-015-relay_interfaces-0_0_5.md` -> `OK: 18 terms` |
| F16 | The durable docs are already complete for this card's work: `docs/README.md` carries the gated `### Relay Node` subsection with the example and the composite-pk cross-reference, `docs/GLOSSARY.md` carries `Meta.interfaces` and `Relay Node integration` both `shipped (0.0.5)`, and `docs/TREE.md` renders `types/relay.py` with its shipped docstring. **No durable-doc edit is owed.** | read at `HEAD` |

**F14 is recorded, not dispatched — and the reason is ownership plus concurrency, not disposition.**

- It is **already homed on a live card.** `KANBAN.md` line 249 (card `TODO-ALPHA-051-0.0.15`, "Boundary hardening and system-wide DRY squeeze") carries the cluster with the correct population, the correct target (`retarget the citations to spec-015`), and an explicit boundary: *"fold into whichever WP batch legitimately opens the file and retarget the citations — widening into a documentation sweep is the error to avoid; the documentation half of the cluster is owned by `TODO-ALPHA-052-0.1.0`."* This cycle's writable set opens none of those files, so it is not such a batch.
- **The files are dirty with a concurrent session's in-flight review work** — `types/base.py` alone is `+154/-…` against `HEAD`, and the concurrent diff rewrites the exact `_validate_interfaces` and `apply_interfaces` bodies that carry four of the eight citations. Editing them now collides head-on with `AGENTS.md` rule 34 and `START.md` `## Concurrent sessions`.
- **`worker-0.md` #"When a reference is wrong across multiple surfaces"** prescribes exactly this: record the cluster as a follow-up and leave all surfaces uniformly consistent rather than partial-fixing one.

So F14 goes to the deferred-work catalog with its verified eight-site population, and **this cycle writes no source and no test.** The measurement is refreshed rather than re-derived: the card's count ("five occurrences in `types/base.py` and one in `types/resolvers.py`, plus `tests/types/test_base.py` and `tests/filters/test_sets.py`") reproduced exactly.

## Baseline-dirty out-of-scope files

`HEAD` at plan time: `4c9e4e0dd66f64b6eb3e29dcf481a9bfb4ec6eae`. `git status --porcelain | wc -l` -> **189**, and **not one of them is this cycle's**. Every path belongs to a concurrent maintainer session (`START.md` `## Concurrent sessions`, `AGENTS.md` rule 34). **No worker edits, reverts, stages, or `git checkout`s any of them.** In particular:

- **A repo-wide hostile-input hardening review cycle is in flight**: ~130 modified source and test files plus ~40 untracked `docs/review/rev-*.md` scratchpads and `docs/review/review-0_0_14.md`. Its edits to `types/relay.py` and `types/base.py` are safe-repr / `BaseException` hardening and change **no** spec-015 contract — verified by reading the diff — but they do rewrite the bodies F14's citations sit in. `AGENTS.md` rule 22 forbids touching `docs/review/` regardless.
- **The spec-014 residual cycle is in flight**: `docs/SPECS/spec-014-testing_shift-0_0_4.md` (modified), its untracked `appx/` rationale, `docs/builder/bld-014-*` (four artifacts), `docs/builder/build-014-testing_shift-0_0_4.md`, and `docs/builder/worker-memory/spec-014-worker-*.md`. Read `spec-014`'s pair as shape precedent — it is this cycle's direct sibling — but never as authority, and never edit either.
- `examples/fakeshop/db.sqlite3` is **clean** at `HEAD`, but `docs/GLOSSARY.md` and `docs/TREE.md` are dirty with concurrent work. **No worker of this cycle runs `scripts/build_kanban_md.py`, `build_kanban_html.py`, or `build_glossary_md.py`, and this cycle makes no database write.** F16 records that no durable-doc edit is owed, so there is nothing this cycle would regenerate for.
- `docs/builder/bld-003-final.md`, `bld-013-final.md`, `build-009-*`, `build-011-*`, `build-013-*` are closed or running cycles' records.

**`docs/SPECS/spec-015-relay_interfaces-0_0_5.md` itself is CLEAN at `HEAD`** — it is not in the dirty list, so this cycle's edits to it are unambiguously attributable. Same for `docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-terms.csv`.

**The list is moving.** Any pass that needs the baseline re-derives it rather than quoting this section.

## Pre-flight deviations, recorded

Two steps of `worker-0.md` `## Pre-flight procedure` did not run as written; both deviations protect concurrent sessions, and both follow the precedent the spec-013 and spec-014 cycles set on this same tree.

- **Step 3 (artifact reset).** **Nothing was deleted.** `docs/builder/bld-003-final.md`, `bld-013-final.md`, the `build-009` / `build-011` / `build-013` plans, and the whole in-flight `bld-014-*` / `build-014-*` set are the committed or running records of closed and active cycles. Deleting a prior cycle's record is the one irreversible pre-flight mistake that step names, and the `bld-014-*` set belongs to a cycle running **right now**. What the step protects — that this cycle overwrites no existing path — was verified directly: all four paths in `## Artifact list` plus the rationale companion were confirmed absent.
- **Step 5 (scratch directories cleared).** **Nothing was cleared.** `docs/builder/worker-memory/` holds six files two concurrent sessions wrote, `docs/shadow/` is live review substrate for the in-flight hardening cycle, and `docs/builder/temp-tests/` holds four in-flight round directories. Clearing any of them would destroy running work. This cycle uses **namespaced** memory files — `docs/builder/worker-memory/spec-015-worker-0.md` and `…/spec-015-worker-1.md` — following the precedent the spec-009, spec-013, and spec-014 sessions set. No worker of this cycle reads or writes any other file in that directory.

Steps 1, 2, 4, 6 ran: the baseline is enumerated above and included per the maintainer's knowing dispatch onto this tree; `scripts/review_inspect.py` smoke-invoked OK against `types/relay.py`; `.gitignore` carries all three scratch paths; `check_spec_glossary --spec docs/SPECS/spec-015-…md` exits 0. Step 7 (rationale extraction) is item R1.

## Artifact list

- `docs/builder/bld-015-r1-rationale_and_spec_reconciliation.md`
- `docs/builder/bld-015-r2-doc_completion_archive_audit.md`
- `docs/builder/bld-015-final.md`

**No `bld-integration.md`.** `docs/builder/BUILD.md` `## Cross-slice integration pass` scans landed source for cross-slice duplication; this cycle lands no source at all, so there is no cross-slice DRY surface. Both of the pass's live obligations are folded into the final gate: the staged-anchor sweep, and the read of every closed artifact. Same disposition, and the same reason, as the spec-011 through spec-014 cycles.

## Checklist

- [x] R1: extract the rationale companion and reconcile the spec against `HEAD` (F1-F12) -> `docs/builder/bld-015-r1-rationale_and_spec_reconciliation.md`
- [x] R2: documentation completion and archive audit (F13-F16) -> `docs/builder/bld-015-r2-doc_completion_archive_audit.md`
- [x] Final test-run gate -> `docs/builder/bld-015-final.md`

Every item closed `final-accepted`.

## Cycle outcome, recorded

**The cycle's committable diff is seven paths**: the reconciled spec, its new rationale companion, one added row in its terms CSV, this plan, and three artifacts. Two `docs/builder/worker-memory/spec-015-worker-*.md` files are gitignored (`.gitignore:188`) and are not part of it. **No package source, no test, and no database write — there is no `.py` anywhere in the diff.**

**Nothing was skipped in the code.** V1-V15 all reproduced when R1 re-derived them independently from `git show HEAD:` copies, and R2 re-read the highest-risk ones a third time. Everything spec-015 promised is present at `HEAD`: `interfaces` is promoted to `ALLOWED_META_KEYS`, the Decision-4 validator carries all seven rules (plus spec-032's six named helper rejections), Phase 2.5 runs `apply_interfaces` -> composite-pk gate -> `install_relay_node_resolvers` in the declared order before Phase 3, all four `resolve_*` defaults and all three helpers exist, `id` suppression preserves the pk in `field_map`, and **30 of the 33 named tests exist under their own names**. The other three were built at `e6907fa8` and relocated to the live `/graphql/` tier at `4f4db722` / `be9130e3` under the repo's live-first policy — proven by the adding and removing diffs, with the live twins' bodies read against their names.

**This spec is the one in the series that got a true rationale MOVE.** Specs 011-013 were card-snapshot stubs needing reconstruction; spec-014's design record was destroyed in place by its own implementing commit and needed restoration. Spec-015's deliberative layer was complete and intact, so R1 performed the cut-and-paste `docs/builder/BUILD.md` `## Spec rationale extraction` actually specifies: spec 73,479 -> 66,594 bytes, a 63,860-byte companion, and 34 `Justification:` passages reduced to zero.

**The two adversarial passes each found drifts the dispatched finding lists did not name — including one in the dispatcher's own evidence.** R1 closed F1-F12 and additionally caught three unnamed drifts (three `README.md` citations for a public-surface promise that paragraph never made; an `id: relay.NodeID[str] = strawberry.field(...)` recourse offered twice that `0.0.6`'s Relay id guard now refuses; a Decision-1 citation of a block comment deleted when the pass landed). R2 — a fresh spawn with no memory of writing any of it — closed F13-F16 and found four more, one **High**: R1's rewording had silently retired four `spec-015 #"substring"` anchors that seven shipped source and test sites quote. Rewording a cited sentence breaks the citation exactly as renaming a symbol breaks a `::QualifiedName`, and `AGENTS.md` rule 27's grep-sweep obligation applies identically — **no spawn prompt in this series has said so, and that is the carry-forward.** R2 restored three and re-homed the fourth in the companion; all quoted substrings resolve across the pair.

**Worker 0's own V12 row was falsified the same way the last two cycles were.** It cleared a live test by name without reading its body; spec-034's cascade had inverted that test from `select_related` to a Prefetch chain. The conclusion held, the cited mechanism did not. Third consecutive residual cycle whose sharpest drift hid behind a surviving test name, and the first where the wrong sentence was the dispatcher's. Recorded under `## Corrections to this plan, recorded`.

**Counts kept being wrong, and only re-derivation caught them.** Five of R1's stated counts did not reproduce; the plan's own F13 figures had to be re-derived against the rewritten spec rather than inherited; R2's nine-path diff figure was corrected to seven at the gate. In every case the fresh-spawn re-measurement is what found it, which is `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` behaving exactly as designed.

**The gate ran clean.** `uv run pytest --no-cov` -> `6085 passed, 40 skipped`, **zero failures and zero errors** — the first cycle in this series with no concurrent-session failures to attribute. `manage.py check`, `makemigrations --check --dry-run`, `ruff format --check`, `ruff check`, `git diff --check`, and `check_spec_glossary` (`OK: 19 terms`, up from 18) all pass. `check_trailing_commas --check` exits 1 on two rows, **neither in this cycle's paths**: one is a concurrent session's uncommitted edit to `utils/inputs.py` (proven not a baseline defect — the script exits 0 against a read-only `git show HEAD:` copy), the other a gitignored `.claude/` file that is not in the repository. Floor-verification scope was `none` and correctly so; the staged-anchor sweep found nothing.

**Eight items are deferred**, catalogued in `bld-015-final.md`. Two matter at commit: **F13 is only half closed** — the `public-exports` CSV row landed, but syncing the card so `DONE-015-0.0.5` renders 19 glossary terms needs `import_spec_terms` plus the two kanban regenerates, which is database work this cycle is barred from while `docs/GLOSSARY.md` and `docs/TREE.md` are dirty. And **F14's `[spec-011]` cluster stays on `TODO-ALPHA-051-0.0.15`** — 8 occurrences across 4 files, re-derived four times, deliberately not stolen for the two reasons under `### R2 findings`.

## Corrections to this plan, recorded

Figures and evidence sentences in `## Worker-0 verification pass` that did not reproduce when R1 measured them, corrected here rather than left standing (`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`). Both were surfaced by R1 and independently re-verified by Worker 0 before being written in.

- **V12's evidence sentence was wrong, and grep is why.** It claimed the live suite "pins forward-FK `select_related` (`::test_products_optimizer_selects_nested_forward_fk_depth_2_over_http`)". That test **kept its name while its assertion was inverted**: spec-034's cascade made `ItemType` and `CategoryType` both declare a custom `get_queryset`, so the optimizer downgrades each forward FK in the `item -> category` chain to a windowed `Prefetch`, and the test now asserts a deterministic 3-query Prefetch chain with **no inter-products JOIN**. Its docstring says so in its first line. V12's *conclusion* — the invariant was relocated to the live tier, not skipped — is unaffected and was independently re-proven by R1; only the named mechanism was wrong. This is the **third consecutive residual cycle** to find its sharpest drift in a test whose name survived its assertion (spec-013, spec-014, now spec-015), and the first in which the wrong sentence was **Worker 0's own**.
- **The commit table listed `be9130e3` before `4f4db722`.** The actual order is `4f4db722` (2026-06-02) then `be9130e3` (2026-06-13); both post-date the implementation at `e6907fa8` (2026-05-13). Corrected in place, with dates added so the ordering is re-derivable.

- **F13's figures were re-derived, not inherited, and moved.** The plan measured 19 spec links against 18 CSV rows *before* R1 rewrote the spec. R2 re-derived against the current file: 19 link definitions, 19 distinct anchors, 18 CSV rows, `public-exports` still the missing one. The finding survived the rewrite unchanged, but the re-derivation was the correct procedure and is the reason it can be trusted.
- **F14's population reproduced exactly** — 8 textual occurrences across 4 files, identical at `HEAD` and in the dirty worktree, matching Worker 0's count file-for-file. R2 additionally re-proved the attribution from the other direction: `spec-011-stale_placeholder_cleanup-0_0_4.md` contains no `### Decision` headings at all, so `spec-011 Decision 4` / `Decision 7` cannot name it under any reading.

R2 additionally found four drifts **no dispatched finding named**, one of them High:

- **(High) R1's reconciliation retired four `spec-015 #"substring"` anchors that seven shipped source and test sites quote.** Rewording a cited sentence breaks the citation exactly the way renaming a symbol breaks a `::QualifiedName`, and `AGENTS.md` rule 27's grep-sweep obligation applies identically. The causes were tiny — an inserted "the", a dropped "explicitly", a dropped parenthetical, and one section legitimately moved to the companion. R2 restored the three whose original wording reintroduces nothing false, and for the fourth (`#"surface any \`TypeError\` as a \`ConfigurationError\`"`, whose `## Risks and open questions` home legitimately left the spec) quoted the sentence verbatim in the companion rather than un-moving deliberation — the citing comment reads `spec-015 Risk note #"…"`, which now names the companion's section. All 11 quoted substrings resolve across the pair.
- **(Medium) A dead `::QualifiedName` carried forward** inside the one Decision R1 otherwise rewrote: Decision 7 cited `types/resolvers.py::_is_fk_id_elided`, absent at `HEAD` and absent when R1 ran. Now `::_build_fk_id_stub`.
- **(Low) Decision 3's code fence did not match the shipped guard** — it lacked `existing_func is not None`, so as written it would overwrite a consumer override carrying no `__func__`. R1's rationale had recorded that same fence as "accurate at `HEAD`".
- **(Low) Two non-unique `#"substring"` anchors**, pre-existing; recorded and deliberately not "fixed".

**Five of R1's counts did not re-derive** and are corrected in R2's artifact rather than by editing R1's closed record: 626 spec lines not 627; six fenced code blocks not four, and the reconciliation gains one rather than none; two `[glossary-*]` refs are used twice, not "exactly once" each; `## Borrowing posture` is 6,230 bytes not 6,210; and "30 of 33 tests" is not re-derivable as stated, replaced with the enumerated population. R1's byte counts, its 34-to-0 `Justification:` count, and the 5,568-byte risk section were exact.

R1 additionally found three drifts **no dispatched finding named** — three `README.md #"For the current capability snapshot"` citations for a public-surface promise that paragraph does not make; a twice-offered `id: relay.NodeID[str] = strawberry.field(...)` recourse that `0.0.6`'s Relay id guard now *refuses*; and a Decision-1 citation of a `types/base.py` block comment removed when the pass landed. All three were closed inside R1's own writable set. They are recorded here because they are evidence that the F1-F12 list Worker 0 handed over was **not** exhaustive, which is the standing argument for the adversarial pass.

## Dispatch record

| Item | Passes dispatched | Why |
|---|---|---|
| R1 | Worker 1 only | The maintainer's standing instruction for this cycle: an item that changes only the spec and its rationale is Worker 1's alone, and both files are Worker 1-owned by `docs/builder/BUILD.md` `## Spec reconciliation` in any case. |
| R2 | Worker 1 only | Its findings are inside the spec and its companions. The one source-shaped finding (F14) is already homed on `TODO-ALPHA-051-0.0.15` and its files are dirty with a concurrent cycle, so it is catalogued rather than built. |
| Final | Worker 1 only | `worker-1.md` `## Final test-run gate` gives the whole gate to Worker 1. |
| (none) | Worker 2 / Worker 3 | The verification pass found no code defect and no code item to build. `### Isolation is non-waivable` binds a pass that writes code; this cycle writes none. |

## Post-gate disposition of the deferred catalog

Performed by Worker 0 after `bld-015-final.md` closed `final-accepted`, on the maintainer's
instruction to home the catalog rather than leave it in an artifact that closeout deletes. Recorded
here because the three `bld-015-*` artifacts are Worker 1's and closed; this file is Worker 0's.

Two preconditions the gate recorded as blocking had cleared by the time this ran, both re-measured
rather than assumed: `examples/fakeshop/db.sqlite3`, `KANBAN.md` and `KANBAN.html` were all committed
clean at `852de2d6`, and the package — briefly un-importable mid-pass while a concurrent session's
`forms/inputs.py` / `forms/sets.py` refactor was in flight — imports again.

### F13 was a false positive, and the CSV row is reverted

**The single load-bearing correction of this pass, and it falsifies both R2's finding and this
plan's own catalog entry.** R2 added a `public exports,public-exports,…` row to
`docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-terms.csv` and reasoned:

> `## Public exports` exists as a heading in the `HEAD` blob of `docs/GLOSSARY.md`, so the
> `GlossaryTerm` row `import_spec_terms` requires exists.

The inference does not hold, and Worker 0 carried it forward into `bld-015-final.md` catalog item 1
without re-deriving it. `docs/GLOSSARY.md` is **rendered from** the glossary DB and carries H2s of two
kinds: term entries, and structural section headings. `## Public exports` is the second kind — it sits
at `:22` among `## Status legend`, `## Index` and `## Browse by category`, above where the
alphabetical term entries begin at `` ## `AggregateSet` ``. There is **no `GlossaryTerm` row anchored
`public-exports`** (probed directly: 142 rows, 0 matching), so the row R2 added named a term that does
not exist.

The two checkers disagreed because they read different things, which is why the gate missed it:
`scripts/check_spec_glossary.py` resolves a CSV anchor against **H2 headings in the rendered
Markdown** and cannot distinguish a section from a term, so it read `OK: 19 terms`;
`import_spec_terms` resolves the same anchor against the **DB** and failed closed with
`Missing GlossaryTerm anchor 'public-exports'`. A green `check_spec_glossary` was never evidence for
the DB-side claim.

The decisive evidence is the convention, not the error message: **seven shipped specs link
`GLOSSARY.md#public-exports` and only spec-015 carried a CSV row for it** — spec-017, spec-020,
spec-025, spec-027, spec-028 and spec-030 all link the section and list no term. The terms CSV is a
*terms* manifest, not a mirror of the spec's glossary links; R2's stated goal of making "the CSV's
anchor set and the spec's anchor set exactly equal in both directions" is a symmetry it invented.

**Row reverted.** The CSV is now byte-identical to `HEAD`, `check_spec_glossary` reads `OK: 18 terms`,
and `import_spec_terms --check` reads `OK: 49 done cards have glossary links` — green across every
done card, card 015 included. **No database write was owed and none was made for F13.** The cycle's
*documentation* diff therefore drops from seven paths to six, and catalog item 1 — the
"load-bearing" open item the gate escalated, with its three-step recipe — is closed as *no change
owed*.

This is the same defect class the cycle's own standing lesson names, arriving one level up: R2 proved
a **symbol** (a heading string) and wrote down a **claim** (a DB row exists). It is also the fourth
consecutive cycle in which the sharpest finding sat inside a sentence asserting its own verification.

### Board edits landed

Three `CardItem` rows appended through `services.append_card_item` (ORM, so the `post_save` side-row
signal fires), then `build_kanban_md.py` and `build_kanban_html.py` regenerated.
`build_glossary_md.py` was **not** run — no `GlossaryTerm` row changed, and `docs/GLOSSARY.md` is
dirty with concurrent work.

| Catalog item | Home | Row |
|---|---|---|
| 2 (stranded Risk-note citation) + 5 (stale test docstring) | `TODO-ALPHA-051-0.0.15` Scope | pk 1361, order 29 |
| 4 (unpinned A/B relation-planning row) | `TODO-ALPHA-051-0.0.15` Scope | pk 1362, order 30 |
| 6 (two non-unique `#"substring"` anchors) | `TODO-ALPHA-052-0.1.0` Scope | pk 1363, order 34 |

Items 2, 4 and 5 went to card 051 because its WP batches already open `types/relay.py` and
`tests/types/`, and because it already carries three items of exactly this shape
(`_optimizer_field_map`, `convert_relation`, `[spec-011]`) under the same boundary: *fold into
whichever WP batch legitimately opens the file; do not widen into a documentation sweep*. Each new row
restates that boundary rather than assuming it carries. Item 6 went to card 052 as a **checker**
requirement, not a repair — matching its two existing siblings there ("Add a source-symbol-citation
check…", "Add an unused-link-definition check…") — and carries the reword-and-reflow lesson, so the
rule lands beside the tool that would enforce it rather than as a fourth restatement in prose.

Item 3 needed no move: the `[spec-011]` cluster is already homed on card 051, doc half on card 052.
Item 8 is a record with no action. Every fact in the three rows was re-derived at `852de2d6` before
being written — the reflow at `types/relay.py:154-155`, the zero Relay coverage in
`test_definition_order_schema.py`, the absent A/B row, and both anchor multiplicities (2 and 3).

### Item 7 fixed in the spec

`## Test plan`'s two projection bullets named `{ allItems { id } }` / `{ allItems { id otherScalar } }`
where `tests/optimizer/test_relay_id_projection.py` sends `{ allCategories { id } }` and
`{ allCategories { id name } }`. Corrected in place. A precondition sweep confirmed no
`#"substring"` citation quotes either sentence, per this cycle's own standing lesson; the rationale
companion's looseness entry now records the correction rather than the deferral, and keeps the two
details that let the error survive four passes — `allItems` really does occur in that module, in a
third row, so a grep returns a plausible hit, while `otherScalar` occurs **nowhere in the repository**
and was the tell.

### Verification

`uv run pytest examples/fakeshop/apps/kanban examples/fakeshop/apps/glossary --no-cov` → **168 passed**.
`manage.py check` → no issues. `git diff --check` → clean. `check_trailing_commas --check` on the three
writable Markdown files → exit 0. Two consecutive regenerates of `KANBAN.md` and `KANBAN.html` hash
identically, and `KANBAN.md` carries zero unresolved `{{…}}` placeholders. The board diff is exactly
`+3 / -0` lines in `KANBAN.md` and one changed data line in `KANBAN.html`. Full suite:
`uv run pytest --no-cov` → **`6085 passed, 40 skipped`, exit 0**, matching the gate's own figure
row for row.

**The cycle's committable diff is now nine paths: six documentation and three board.** Documentation
— the reconciled spec (`+165 / -195`), its rationale companion, this plan, and the three `bld-015-*`
artifacts. Board — `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`. The terms CSV has left
the diff entirely. **Still not one `.py` file**, and the board write is confined to three appended
`CardItem` rows on two To-Do cards.

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
