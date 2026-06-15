# Build: Cross-slice integration pass — permissions / 0.0.10 (034)

Spec reference: `docs/spec-034-permissions-0_0_10.md`
Build plan: `docs/builder/build-034-permissions-0_0_10.md`
Status: final-accepted

Worker 1 cross-slice integration pass. All five spec slices are `final-accepted`.
This pass walks every prior `bld-slice-*.md` artifact, runs the shadow-overview
cross-scan (repeated literals + imports), and adjudicates the deferred cross-slice
DRY items — chiefly the cascading-schema test-fixture duplication that Slices 2-4
deliberately deferred to this pass once the duplication count was final.

STANDING GUARD honored: every command this pass was a read-only inspection
(`grep` / `Read` / `sed` / the `review_inspect.py` static helper / shadow-overview
reads). No `git checkout` / `restore` / `stash` / `reset`; no source / test / spec edit.
Per the dispatch, this pass made **no spec edit** (no integration finding required one)
and **no source/test edit** (consolidation, if warranted, is a dispatched Worker 2 pass).

---

## 1. Prior-artifact walk (required context — every slice, in order)

Read all five slice artifacts end-to-end (plan + build + review + final-verification,
including re-pass sections). Summary of each slice's outcome and the carry-forwards it
left for this pass:

- **Slice 1 — cascade foundation** (`bld-slice-1-cascade_foundation.md`, `final-accepted`).
  Shipped the only new package module, `django_strawberry_framework/permissions.py`
  (`apply_cascade_permissions` / `aapply_cascade_permissions` + the private `_walk` /
  `_is_cascadable_edge` / `_cascadable_edge_names` / `_validate_fields` / `_cascade_seen`
  ContextVar), exported from `__init__.py`, pinned by new `tests/test_permissions.py`.
  DRY hinges held: ONE `_is_cascadable_edge` predicate feeds both the `fields=None` walk
  and the `fields=` validator; the per-edge hook run delegates to
  `utils/querysets.py::apply_type_visibility_sync` (no second sync-misuse probe); the async
  twin is `sync_to_async(thread_sensitive=True)` around the single sync walk (no fork).
  Final verification made 6 spec edits (scope-predicate `hasattr`→`getattr(...,None) is not None`
  for Django-6 M2M `column=None`, plus status/Current-state refreshes). Carry-forwards left for
  here: (a) the `SyncMisuseError` message in `utils/querysets.py` hardcodes "Relay node
  defaults" — accepted as DRY reuse, integration-pass candidate only if judged misleading;
  (b) the `SyncMisuseError` re-export in `permissions.py`; (c) the test-fixture DRY item begins
  here (fakeshop FKs all non-nullable → synthetic graphs needed).

- **Slice 2 — optimizer cooperation + N+1 audit** (`bld-slice-2-optimizer_cooperation.md`,
  `final-accepted`). ZERO source change — five test pins (3 in `tests/test_permissions.py`,
  2 in `tests/optimizer/test_extension.py`) confirming a cascading hook rides the shipped
  optimizer machinery: `select_related`→`Prefetch` downgrade (with the live-`info` child
  narrowing — the Decision-12 dependency), `cacheable=False`, zero added round-trips
  (absolute query count + `"IN (SELECT"` guard), strictness silence, FK-id-elision fallback.
  Carry-forward recorded explicitly: "if Slice 3 rebuilds the cascading `Entry → Item → Category`
  schema a 3rd+ time, the integration pass should extract a shared cascading-schema fixture."
  (Note: pass-1 reviewer's `git checkout` destroyed the uncommitted Slice-1 `permissions.py`;
  Worker 0 restored byte-exact from transcript, pass-2 re-confirmed green. Recovered; the
  STANDING GUARD in the build plan is the response. Not an integration finding.)

- **Slice 3 — composition pins** (`bld-slice-3-composition_pins.md`, `final-accepted`).
  ZERO source change — 8 pins across 4 test files (`test_permissions.py` gate/nested,
  `test_connection.py`, `test_relay_node_field.py`, `test_list_field.py`) confirming
  gates / connections / node refetch / nodes batch / list fields all honor a cascading
  `get_queryset` through their existing seams (Decision 11/12). One High (H1) found + fixed
  in pass-2: the gate-composition pins' `narrowed` was built on a no-op
  `apply_cascade_permissions(category_type, Category.objects.all(), _INFO)` (Category is the
  chain top with no cascadable forward FK; the direct call never invokes the type's own hook)
  — rebuilt via the hook-invocation path `category_type.get_queryset(...)`, both gate shapes
  now causally load-bearing. Worker 2's to-many redesign of the nested pin (forward non-null FK
  can't null-resolve → parent-drop; to-many list narrows cleanly) adjudicated sound; one spec
  edge-case bullet added at final verification. **Carry-forward (the central one):** the
  cascading-hook + hiding-target scaffold is now re-declared across all four files; the
  duplication count is FINAL for the build — evaluate the shared-fixture hoist HERE.

- **Slice 4 — products activation + live HTTP** (`bld-slice-4-products_activation.md`,
  `final-accepted`). Source change = uncomment the four `get_queryset` cascade hooks in
  `examples/fakeshop/apps/products/schema.py` PLUS one byte-uniform mechanical fix
  (`info.context.user` → `getattr(getattr(info.context, "request", None), "user", None)` — the
  stock `StrawberryDjangoContext` has no `.user`; the committed commented bodies were dead as
  written). 5 new live cascade tests (real `create_users(1)`) + 12 re-pins (10 live + 2
  in-process) for the activation's anonymous-visibility churn + a real test-isolation fix
  (`project_schema` fresh-reimport fixture). Final verification made 4 spec edits (canonical
  `request.user` pattern + the "Live-suite sensitivity" Risks correction: seeders are NOT
  public-only — Category/Property deterministic `%2`, Item/Entry random). Carry-forward: GOAL.md
  / GLOSSARY still showed the broken `info.context.user` form — handed to Slice 5.

- **Slice 5 — doc updates + card wrap** (`bld-slice-5-doc_wrap.md`, `final-accepted`).
  Doc/DB-only. GLOSSARY flipped `apply_cascade_permissions` → `shipped (0.0.10)` (scope
  corrected to forward-FK/OneToOne, M2M out; canonical `request.user` example), per-field-hooks
  re-statused `0.1.1` + Decision-2 note, public-exports +2 bullets (both anchored
  `#apply_cascade_permissions`); KANBAN card 34 → `DONE-034-0.0.10` via the DB + regenerate;
  hand-edited `docs/README.md` / `docs/TREE.md` / `TODAY.md` / `README.md`; CHANGELOG
  `[Unreleased]` (no `[0.0.10]` promotion — Decision 13); GOAL.md `request.user` fix ratified.
  Resolved a CSV duplicate-anchor blocker (`import_spec_terms` hard-rejects the `aapply_`
  row → collapsed to one row, `check_spec_glossary` `OK: 42`). All three generated docs
  regenerate byte-identical. Version freeze intact. Carry-forwards left for the FINAL gate's
  deferred-work catalog (not integration DRY items): see §6.

**Walk conclusion:** every slice is `final-accepted` with a clean (0/0/0) terminal review.
The only DRY follow-up any slice deferred *to the integration pass specifically* is the
cascading-schema test-fixture duplication (Slices 2/3 memory + DRY-findings + Notes-for-Worker-1).
Every other carry-forward is a doc-accuracy / maintainer follow-up routed to the final gate's
deferred catalog, not a cross-slice DRY consolidation.

---

## 2. Static-inspection-helper coverage

BUILD.md requires the helper to have been run (or recorded-skipped) for every Python file
with review-worthy logic the build touched. The build touched exactly two source-logic files:

- `django_strawberry_framework/permissions.py` (Slice 1, new module) — Worker 3 ran the helper
  at Slice-1 review (recorded). **Re-run this pass** for the cross-slice scan
  (`docs/shadow/django_strawberry_framework__permissions.overview.md`).
- `examples/fakeshop/apps/products/schema.py` (Slice 4, four hook bodies) — Worker 3 ran the
  helper at Slice-4 review (recorded). **Re-run this pass**
  (`docs/shadow/examples__fakeshop__apps__products__schema.overview.md`).

All other build edits are tests (`tests/test_permissions.py`, `tests/optimizer/test_extension.py`,
`tests/test_connection.py`, `tests/test_relay_node_field.py`, `tests/test_list_field.py`,
`examples/fakeshop/test_query/test_products_api.py`, `examples/fakeshop/apps/products/tests/test_schema.py`),
doc files, or the DB-backed generated docs — no helper mandate (no new package-logic file).
Coverage is complete.

---

## 3. Repeated-string-literal cross-scan

Compared the **Repeated string literals** sections across both shadow overviews:

- `permissions.py` — **None.** (No repeated executable string literals at all.)
- `schema.py` — `4x description`, `4x is_private`, `4x created_date`, `4x updated_date`,
  `2x category`.

The `schema.py` literals are model-field names repeated once per the four `DjangoType.Meta`
declarations (the consumer-facing per-type contract — one explicit `Meta` per model) and the
two `category` FK references. They are **not** cross-file or cross-slice duplication: they are
local field-name references inside one example-schema module, exactly as the GOAL.md showcase
declares them per type. No literal appears in ≥2 *files*. **No cross-slice repeated-literal
DRY candidate.**

(Test files are not in the helper's source scope, but the test-fixture duplication is handled
directly in §5 below, which is the substantive repeated-shape finding.)

---

## 4. Import-direction cross-scan (one-way dependency)

Compared the **Imports** sections and grepped reverse imports:

- `permissions.py` imports only: `.exceptions` (`ConfigurationError`), `.registry` (`registry`),
  `.utils.querysets` (`apply_type_visibility_sync` + the `SyncMisuseError as SyncMisuseError`
  re-export), plus stdlib/`asgiref`/`django`. This matches the plan exactly: `permissions.py`
  depends on registry / utils / exceptions, and on nothing else first-party.
- **Reverse check:** the only first-party importer of `permissions.py` is
  `django_strawberry_framework/__init__.py:21` (the package-root re-export — the intended and
  documented consumption point). No `registry` / `types` / `utils` / `optimizer` / `filters` /
  `orders` / `connection` / `relay` / `list_field` module imports `permissions`. The dependency
  is strictly one-way (`permissions.py` is a leaf consumed by `__init__.py` and consumer
  `get_queryset` bodies), with no boundary violation.
- `schema.py` (example project) imports `apply_cascade_permissions` from the package root —
  the public surface, correct direction.

**Import direction is clean; no sibling crosses a documented boundary.**

---

## 5. THE deferred cross-slice DRY item — cascading-schema test fixtures (ADJUDICATED)

### The duplication, counted (final)

The cascading-hook body (`get_queryset` → `apply_cascade_permissions(cls, qs.filter(is_private=False), info)`)
plus a hiding-`Category` target hook (`queryset.filter(is_private=False)`) and the
`Entry → Item → Category` cascading-schema scaffold now recur across four package test files:

- `tests/test_permissions.py` — `_exclude_private` declared **6 times** (5 as the cascading
  hook body, 1 — at `:770` — deliberately the *non-cascading identity* variant
  `return qs.filter(is_private=False)` for the secondary-type comparison test; plus the
  module-level `:1194` definition). Many inline `lambda cls, qs, info: apply_cascade_permissions(...)`
  hooks across the synthetic-graph tests.
- `tests/test_connection.py` — local `_make_cascading_item_node(name: str)` (Relay-Node `Item`
  type + `total_count` + cascading hook) + an inline `CcCategoryType` hiding hook.
- `tests/test_relay_node_field.py` — local `_make_cascading_item_node()` (different signature;
  bundles a `_HidingCategoryType` + returns a Relay-Node `Item`) + `_ITEM_QUERY` / `_ITEMS_QUERY`.
- `tests/test_list_field.py` — inline cascading `Item` `DjangoType` + a `_HidingCategoryType`.

Count of independent cascading-`Item`-node declarations introduced by Slices 3-4: **3**
(`test_connection.py`, `test_relay_node_field.py`, `test_list_field.py` — the two
`_make_cascading_item_node` helpers share a name but are separate per-file declarations with
different signatures and return shapes), on top of the `test_permissions.py` `_exclude_private`
family. This is the count Slices 2/3 said would trigger an integration-pass evaluation.

### Decision: ACCEPT the per-file duplication. Do NOT consolidate. (NOT a blocker.)

I evaluated extracting a shared cascading-schema fixture (a `tests/conftest.py` fixture or a
small shared test-helper module) and judged it the **lower-quality** shape. Rationale, weighing
DRY against test-locality:

1. **The "duplicated" sites are not blind copies — they are per-context variants that a shared
   fixture would have to abstract over, re-introducing the complexity it claims to remove.**
   - The `_exclude_private` at `test_permissions.py:770` has a *different body*
     (`return qs.filter(is_private=False)` — the identity/non-cascading comparison hook for
     `test_secondary_type_never_cascade_target`). A "shared `_exclude_private`" would be wrong here.
   - The two `_make_cascading_item_node` helpers have **different signatures** (`(name: str)` vs
     `()`), **different return shapes** (the connection one needs `connection={"total_count": True}`
     and is wired through `_connection_type_for` + `DjangoConnectionField`; the relay one bundles a
     `_HidingCategoryType` and returns a Relay-Node `Item` for `_schema_with` + `_gid` refetch), and
     each is woven into its **own file's distinct harness** (`_make_sidecar_node_type` / `_field_schema`
     vs `_schema_with` / `_gid` / `_make_hidden_category_node` vs the inline-`DjangoListField` template).
     A shared factory would need ≥4 parameters (model, fields, interfaces, total_count, sidecars,
     hiding-target wiring) to serve all sites — that is *more* surface than the small per-file helpers,
     and it would couple four otherwise-independent test files to one abstraction.

2. **Registry-isolation lifecycle is per-file and load-bearing.** Each file relies on its own
   autouse registry-isolation fixture and `finalize_django_types()` lifecycle; the synthetic
   `DjangoType` subclasses are declared inside each test's own isolation scope. A cross-file
   conftest fixture that declares `DjangoType`s would have to thread that lifecycle across files,
   which is precisely the kind of shared mutable-registry coupling the per-file `registry.clear()`
   autouse fixtures exist to avoid. (Slice-4's `project_schema` isolation fix and the documented
   `tests/conftest.py` async-sqlite ResourceWarning machinery both show how sensitive this suite
   is to cross-test state — adding shared schema-building fixtures into that surface is a net risk.)

3. **`tests/conftest.py` has a single, heavily-documented, fragile responsibility** (the
   async-sqlite `ResourceWarning` close-at-source fix under `-W error`; my standing memory flags it
   as never-to-weaken). Injecting cascading-schema fixtures there dilutes that single responsibility
   and puts unrelated schema scaffolding next to connection-lifecycle plumbing.

4. **Test-locality is the higher value here.** Each pin reads top-to-bottom as a self-contained
   scenario: a reader of `test_connection.py::test_connection_over_cascading_type_narrows_edges_and_total_count`
   sees the cascading `Item` node, the hiding `Category`, the seeding, and the assertion in one place.
   A shared fixture would force the reader to jump to a conftest to understand what "the cascading
   schema" is — for a 2-3-line hook body that is trivially re-readable inline. AGENTS.md's test
   philosophy ("each app carries its OWN coverage", self-contained tests) and the repeated Worker-3
   judgments ("collapsing them into a shared constant would couple unrelated tests and reduce
   readability") both favor locality for fixtures this small.

5. **The genuine DRY pressure is already relieved at the right altitude.** The *production* DRY
   levers (one `_is_cascadable_edge` predicate, one sync walk, the `apply_type_visibility_sync`
   reuse, the `sync_to_async` wrap) are all in `permissions.py` — the place where duplicated logic
   would be a real defect. The remaining duplication is test *scaffolding* of a 2-line hook, which is
   the cheapest, most-readable thing to repeat.

**Therefore: the per-file duplication is acceptable, recorded here with rationale, and is NOT a
blocker.** No Worker 2 consolidation pass is dispatched. (Had I decided the other way, the protocol
was: record the exact findings for Worker 2 + report back to Worker 0 — I am explicitly *not* doing
that, by decision.)

Within-file, Worker 2/3 already confirmed each pin reuses its own file's existing harness rather
than re-deriving ad-hoc scaffolding — so there is no *in-file* near-copy to fix either.

---

## 6. Other cross-slice items — dispositions

- **`SyncMisuseError` generic "Relay node defaults" message on the cascade path (Slice-1
  carry-forward).** The cascade reuses `utils/querysets.py::apply_type_visibility_sync`, whose
  `SyncMisuseError` message names "the Relay node defaults" and a sync-`get_queryset`-rewrite
  recourse — accurate-but-generic on the cascade surface; it does not name `aapply_cascade_permissions`.
  **Disposition: ACCEPT the reuse; do NOT generalize the message.** The reuse is the explicit
  Decision-10 DRY instruction and the data-leak-routing rule in the `utils/querysets.py` docstring
  (one place runs a sync `get_queryset` and rejects an async hook). The message still names the
  offending target type and a valid recourse. Generalizing it would touch shared source serving three
  surfaces (Relay defaults, list-field defaults, cascade) for a message-specificity gain — the
  Slice-1 test pins the type-name + `SyncMisuseError` + closed-coroutine, not the recourse wording, so
  nothing is mis-pinned. Not misleading enough to justify a shared-source edit + Worker 2 pass. **Not
  a blocker.** (Recorded as a possible future polish in the final gate's deferred catalog, not an
  integration consolidation.)

- **`SyncMisuseError` re-export in `permissions.py` (Slice-1 carry-forward).** `permissions.py:57`
  does `from .utils.querysets import SyncMisuseError as SyncMisuseError` — the established
  `types/relay.py:41` redundant-alias convention, required for the `tests/test_permissions.py` import
  header to resolve. **Disposition: ACCEPT.** It adds no new package-root public name (`SyncMisuseError`
  is already in `__all__` via `types`), the `X as X` form is ruff-recognized as an intentional
  re-export (no `# noqa` needed), and it matches the existing convention. No drift, no action.

- **Import-direction sanity.** Resolved clean in §4 — `permissions.py` is a one-way leaf;
  no sibling imports it. No action.

- **Naming / error-handling consistency across slices.** Cascade errors use the package's existing
  exception vocabulary uniformly: `ConfigurationError` for `fields=` validation (unknown /
  non-cascadable / bare-string), `SyncMisuseError` for async-hook-from-sync (reused, not redefined),
  `GraphQLError` for the shipped gate denials (Slice 3, unchanged). The four products hook bodies are
  byte-uniform except the `view_<model>` codename — the intended per-type consumer contract, not a DRY
  violation (Worker-3 Slice-4 confirmed). Consistent.

- **Misplaced responsibilities.** None. The cascade lives in its own `permissions.py` module; the
  optimizer cooperation is unchanged shipped machinery (Slice 2 added zero source); the composition
  is unchanged shipped pipelines (Slice 3 added zero source); the activation is example-project-only
  (Slice 4). No responsibility leaked across a module boundary.

- **Public-surface / export drift.** The only `__all__` growth is the two Slice-1 cascade symbols
  (`apply_cascade_permissions`, `aapply_cascade_permissions`), spec-authorized (Decision 4) and pinned
  in `tests/base/test_init.py`. The version constant in that file is untouched (`0.0.9`, Decision 13).
  Slices 2-5 added no export. No drift.

- **Comments tell one coherent story.** The cascade is described consistently as a call-time,
  depth-1, single-column-forward-FK/OneToOne walk with the four invariants, across `permissions.py`'s
  docstring, the GLOSSARY entry, the CHANGELOG `[Unreleased]` bullet, and the products hook bodies.
  The Slice-4 `request.user` reconciliation is now consistent across the fakeshop hooks, GOAL.md,
  and the GLOSSARY example (the two genuinely-generic teaching examples Slice 5 left as-is are
  out-of-scope non-cascade `get_queryset` demos — recorded for the final gate's deferred catalog,
  not a cross-slice inconsistency in the cascade story).

---

## 7. Items for the final gate's `### Deferred work catalog` (NOT integration DRY items)

Surfaced here so the final-test-run gate (`bld-final.md`) can catalog them; none is a
consolidation loop, none blocks integration:

1. **Pre-build committed-DB-vs-committed-GLOSSARY divergence** — 8 shipped glossary entry bodies
   + the `testing.relay` public-exports line were out of sync between the committed `db.sqlite3`
   and `docs/GLOSSARY.md` before this build (a concurrent-sweep artifact); Slice 5 reconciled them
   INTO the DB byte-clean. Surface to the maintainer (Slice-5 Notes-for-Worker-1 item A).
2. **`docs/TREE.md` generator staleness** — `build_tree_md.py --check` reports not-up-to-date due
   to earlier-spec docstring/file drift a full regenerate would sweep in; Slice 5's targeted
   hand-edit was the right call. Recommend a separate maintainer doc-regeneration follow-up
   (Slice-5 item F).
3. **FieldSet card `044` → `046` cross-surface cluster** — the card-34 body's open-question prose
   quotes the older FieldSet card `044` while the live card is `TODO-BETA-046-0.1.1`; left per the
   no-partial-multi-surface-fix rule (Slice-5 item E / final-verification).
4. **Residual `docs/spec-permissions.md` card-body refs** — DoD order=8 inner clause + two
   scope/other bullets still cite the pre-convention spec filename; left per the same rule (Slice-5
   item E).
5. **Two genuinely-generic `info.context.user` teaching examples** — GLOSSARY `get_queryset`
   visibility-hook entry (shipped `0.0.1`, generic single-type demo) and `TODAY.md`'s `ItemType`
   demo; judged out-of-named-scope generic teaching examples, left as-is. A holistic cleanup is a
   maintainer follow-up (Slice-5 final-verification).
6. **`SyncMisuseError` cascade-message polish** (§6) — optional future generalization of the
   shared `utils/querysets.py` message; accepted reuse for now.

---

## Review outcome

**final-accepted.** The cross-slice integration pass is clean: no duplicated production helper,
no inconsistent naming/error-handling, no misplaced responsibility, no repeated cross-file literal,
no public-export drift, one coherent comment story, one-way import direction. The single DRY item
deliberately deferred to this pass — the cascading-schema test fixtures — is **adjudicated as
acceptable per-file duplication** (test-locality + genuine per-context variance outweigh DRY for a
2-line hook; the production-side DRY is already at the right altitude in `permissions.py`), recorded
with rationale and explicitly **NOT a blocker**. No consolidation loop is dispatched. The other
cross-slice items (`SyncMisuseError` generic message; the `permissions.py` re-export; import
direction) are each ACCEPTED with rationale. Proceed to the final test-run gate (`bld-final.md`),
which owns the deferred-work catalog seeded in §7.

### Memory

Appended to `docs/builder/worker-memory/worker-1.md`.
