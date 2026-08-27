# Package build plan: globalid_encoding / 0.0.9 (031) — residual reconciliation cycle

Spec source: `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` (already archived; the shipped record)
Rationale companion (to be created this cycle): `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md`
Terms companion (already present): `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-terms.csv`
Target release: `0.0.9` (shipped; the package is at `0.0.14`)
Date created: 2026-08-26
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.

## Cycle shape — this is NOT a feature build

`DONE-031-0.0.9` shipped. This cycle runs the `docs/builder/BUILD.md` process over already-shipped
work with three obligations, in this order:

1. **The rationale companion was never created.** `docs/SPECS/appx/` carries a `-rationale.md` for
   001-030 and 044-048 but not for `031`. Pre-flight step 7 (`## Spec rationale extraction`) is
   therefore the cycle's first substantive action and is performed against a shipped spec:
   Worker 1 MOVES the deliberative layer out of `spec-031-…md` into the companion.
2. **CODE GAP audit — the load-bearing obligation.** For every slice, prove each contracted surface
   exists at HEAD, or record a CODE GAP. The question is whether the build **skipped, dropped, or
   forgot** something the spec planned. A slice with an empty CODE GAP list closes procedurally.
3. **Post-ship reconciliation.** Where later work (the `0.0.14` GlobalID hardening, spec-032's root
   Relay surface, spec-046/047/048, the `0.0.14` bug hunt) **changed or corrected** what `031`
   landed, the spec must state the CURRENT contract directly. `## Spec rationale extraction` is
   canonical: the spec never narrates its own history — the change, its round, and the claim it
   retired go in the rationale companion.

### Scope fence (maintainer-set, overrides the spec's own slice text where they conflict)

- **In fence:** `docs/SPECS/spec-031-globalid_encoding-0_0_9.md`, the new
  `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md`, and `.py` source/test files.
- **Out of fence:** every other documentation surface — `docs/GLOSSARY.md`, `docs/README.md`,
  `docs/TREE.md`, `TODAY.md`, `README.md`, `CHANGELOG.md`, `KANBAN.md`, `KANBAN.html`,
  `examples/fakeshop/db.sqlite3`, and the terms CSV. Slice 5's doc obligations are therefore
  **audited and reported, never edited**: a divergence found there is recorded in
  `### Deferred work catalog`, not fixed.
- **No closeout agentflow edits.** `docs/builder/BUILD.md`, `ARTIFACT.md`, and the four
  `worker-*.md` role files are not edited by this cycle. `## Closeout` is not run.
- **Every file this cycle creates carries `031` in its name.**

### Fence amendment (maintainer, post-final-gate)

Two authorizations were added after `bld-031-final.md` closed, to discharge the two catalog items
that are **damage this cycle itself caused** rather than pre-existing debt:

1. **`docs/SPECS/spec-032-full_relay-0_0_9.md` is in fence.** It is a spec file, and the maintainer's
   fence has always read "spec files and the code `.py` files ONLY". Catalog item 1 recorded its
   owner as "maintainer, or a future `032` cycle" only because the cycle had read `032` as
   out-of-fence; that reading was wrong on the fence's own wording. Slice 6 repairs it here.
2. **Kanban DB edits are authorized.** The Slice-0 rationale move falsified a measured census in
   `TODO-ALPHA-052-0.0.16`'s scope. `KANBAN.md` / `KANBAN.html` are rendered from the DB, so the
   render is the completion of the DB edit, not a separate doc edit. Slice 7 owns both.

Everything else in the fence stands: no closeout agentflow edits, `## Closeout` is not run, and the
remaining doc surfaces stay audited-read-only.

**Third authorization (2026-08-26, after Slice 6).** Slice 6 measured that `spec-032` carries the
same defect class from the **spec-030** residual cycle: `spec-030` now has zero `Revision N` entries
and zero `Alternatives considered` blocks (23 and 15 respectively live in its companion), and
`spec-032` cites both. That is another cycle's damage, deliberately excluded from
`bld-031-final.md`'s catalog as out-of-fence "other work" — the maintainer has now authorized
repairing it here, because `spec-032` is in fence and already open. Slice 8 owns it.

### Concurrent work — never edited, never reverted

Baseline-dirty at pre-flight, owned by a concurrent session (the `0.0.14` bug hunt). `AGENTS.md`
rule 34 applies: out of scope, neither edited nor reverted by any worker in this cycle.

- `django_strawberry_framework/consumers.py` (M)
- `django_strawberry_framework/utils/sessions.py` (M)
- `examples/fakeshop/db.sqlite3` (M — tracked binary, concurrent-writable; see
  `docs/builder/BUILD.md` `### Tracked binary / generated files`)
- `tests/test_consumers.py` (untracked, new)

None of the four is a spec-031 surface. `db.sqlite3` is the concurrent-writable tracked binary this
cycle must not reset; no slice in this cycle writes the DB (the card wrap is out of fence).

## Pre-flight

Pre-flight: passed on 2026-08-26 with one recorded deviation (step 3).

1. **Working-tree baseline** — `git status --short` clean except the four concurrent paths above.
   Recorded as baseline-dirty out-of-scope. HEAD `bc4ed00a`.
2. **`scripts/review_inspect.py` runs** — smoke invocation against
   `django_strawberry_framework/types/relay.py --output-dir docs/shadow --stdout` exited 0
   (17 imports / 29 symbols / 6 hotspots).
3. **Build artifacts reset — DEVIATION, recorded.** No `build-031*` or `bld-031*` path exists, so
   every path this cycle creates is free. `docs/builder/bld-003-final.md` survives from the
   spec-003 cycle and is **tracked and committed**; deleting it is out of the maintainer's fence
   (`.md`, not a spec or `.py`) and destructive to committed history, so it is **left in place**.
   It cannot collide: every artifact below is `031`-named. `docs/builder/DONE/` holds the prior
   cycles' build plans and is untouched. The spec's `-terms.csv` sibling is tracked and durable and
   is never deleted.
4. **`.gitignore` lists the scratch paths** — `docs/shadow/` (line 174),
   `docs/builder/worker-memory/` (188), `docs/builder/temp-tests/` (192). Confirmed.
5. **Scratch directories cleared** — `docs/builder/temp-tests/` empty;
   `docs/builder/worker-memory/` re-seeded with four empty files; `docs/shadow/` holds only the
   step-2 smoke output.
6. **Spec-doc consistency** — `uv run python scripts/check_spec_glossary.py --spec
   docs/SPECS/spec-031-globalid_encoding-0_0_9.md` → `OK: 31 terms`.
7. **Spec rationale extraction** — NOT yet done; it is this cycle's Slice 0 and gates every later
   dispatch. Spec byte count before the move: **190,961 bytes**.

## Build-wide context flags

- **Joint-cut path.** Decision 12 pins the `0.0.9` version bump to the joint cut with `DONE-029` /
  `DONE-030` / `DONE-032` / `DONE-033`. That cut happened; the package is now at `0.0.14`. No slice
  in this cycle touches `pyproject.toml`, `__version__`, `tests/base/test_init.py::test_version`, or
  `uv.lock`.
- **Post-ship deltas already recorded IN the spec** as Revision 6 / Revision 7 (a/b/c). Those
  revision-log entries are chronology and MOVE to the rationale companion; the contracts they
  describe stay in the spec, stated directly.
- **Known post-ship hardening NOT yet reflected in the spec** (Worker-0 pre-verified, handed to
  Slice 0 / the owning slices rather than re-derived):
  - `types/relay.py::decode_global_id` normalizes hostile `str` subclasses via `str.__str__` on the
    raw input and on both parsed slots, catches `BaseException` around the slot reads, and rejects
    non-`str` slots — none of which the spec's Decision 8 states.
  - `types/base.py::_validate_globalid_callable` wraps non-`signature`-inspectable and hostile
    descriptor callables (`tests/types/test_base.py::test_globalid_callable_wraps_non_signature_inspection_errors`,
    `::test_meta_globalid_callable_hostile_descriptor_is_typed`) — Decision 6 states only the arity
    bind and the sync-ness guard.
  - `filters/base.py` mismatch rejections now carry `extensions={"code": "GLOBALID_INVALID"}`; the
    spec's Decision 13 / `## Current state` still quote the bare
    `GraphQLError("GlobalID type mismatch: …")` string.
  - `registry.py::GLOBALID_SETTING_UNSET` is the sentinel distinguishing "not yet computed" from a
    computed `None`; the spec names `registry._globalid_setting_snapshot` but not the sentinel.
  - `types/base.py::_is_relay_shaped`'s gate tail is shared with `global_id_for` and
    `Meta.relation_shapes` (spec-032 Decision 7), which post-dates `031`.
- **Hot-path declaration:** `none`. No slice in this cycle writes production code by default; if a
  CODE GAP forces a Worker 2 pass on the `resolve_typename` install closure (a per-node `id`
  resolution path) or on `_decode_and_validate_global_id` (per filter value), that slice is
  re-declared hot-path at its planning pass and owes a before/after number.
- **Floor-verification scope:** `none` by default — no slice is expected to change production code.
  `types/base.py`, `types/relay.py`, `types/finalizer.py`, and `filters/base.py` are Strawberry
  type-construction seams, so **any** slice that ends up dispatching Worker 2 against them
  re-declares the scope at its planning pass (focused `tests/types/` + `tests/filters/` at the floor
  in an isolated venv, owned by that slice's Worker 1 final-verification pass).
- **Ownership partition:** `none; sequential slices`. Slices 1-4 all reconcile one spec file, so
  every cohort would own it — one shared file is enough to serialize (`docs/builder/BUILD.md`
  `### Parallel cohorts under a declared ownership partition`).

## Dispatch rule for this cycle

Per the maintainer: run the BUILD.md process, but **do not dispatch every worker**. Each slice opens
with a Worker 1 pass that performs the CODE GAP audit and the spec reconciliation.

- **Empty CODE GAP list** → the slice closes by **procedural closure**
  (`docs/builder/BUILD.md` `### Procedural-closure slices`): one Worker 1 pass, combined
  Plan + Final-verification block, `Status: final-accepted` set directly. No Worker 2, no Worker 3.
- **Non-empty CODE GAP list** → Worker 1 sets `Status: planned` and returns; Worker 0 dispatches the
  full Worker 2 → Worker 3 → Worker 1 cycle for that slice, and that slice re-declares hot-path and
  floor-verification scope.

`### Isolation is non-waivable` still holds: if Worker 2 runs, Worker 3 runs as a separate spawn.

## Artifact list

- `docs/builder/bld-031-slice-0-rationale_extraction.md` — pre-flight step 7, the rationale move
- `docs/builder/bld-031-slice-1-meta_key_setting_precedence.md` — Slice 1
- `docs/builder/bld-031-slice-2-encode_seam.md` — Slice 2
- `docs/builder/bld-031-slice-3-decode_seam.md` — Slice 3
- `docs/builder/bld-031-slice-4-live_http.md` — Slice 4
- `docs/builder/bld-031-slice-5-docs_wrap.md` — Slice 5 (audit-only; the doc surfaces are out of fence)
- `docs/builder/bld-031-integration.md` — cross-slice integration pass
- `docs/builder/bld-031-final.md` — final test-run gate
- `docs/builder/bld-031-slice-6-spec_032_citation_repair.md` — Slice 6 (post-final: the Slice-0 move's link rot in `spec-032`)
- `docs/builder/bld-031-slice-7-card_052_companion_census.md` — Slice 7 (post-final: the board census the companion falsified)
- `docs/builder/bld-031-slice-8-spec_032_spec_030_citations.md` — Slice 8 (post-final: the SAME defect class from the spec-030 cycle, in the same file)
- `docs/builder/bld-031-slice-9-card_052_homing.md` — Slice 9 (post-final: home the two artifact-only open items on card 052 before the cycle's artifacts are deleted)

## Checklist

- [x] Slice 0: Spec rationale extraction (pre-flight step 7) -> `docs/builder/bld-031-slice-0-rationale_extraction.md`
- [x] Slice 1: `Meta.globalid_strategy` net-new key (validated + stored on the definition) + `RELAY_GLOBALID_STRATEGY` settings read + the precedence resolver -> `docs/builder/bld-031-slice-1-meta_key_setting_precedence.md`
- [x] Slice 2: the encode seam — strategy-parameterized `resolve_typename` injection + the four encoders + the default flip to `model` (+ strategy-aware `GlobalID` filter validation) -> `docs/builder/bld-031-slice-2-encode_seam.md`
- [x] Slice 3: the decode seam — `decode_global_id` dispatch + encoder/decoder symmetry + transitional `type+model` -> `docs/builder/bld-031-slice-3-decode_seam.md`
- [x] Slice 4: live HTTP coverage on a Relay-Node-shaped fakeshop type -> `docs/builder/bld-031-slice-4-live_http.md`
- [x] Slice 5: doc updates + card-completion wrap (AUDIT ONLY — out of fence) -> `docs/builder/bld-031-slice-5-docs_wrap.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-031-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-031-final.md`
- [x] Slice 6: repair the eight `spec-032` citations into text the Slice-0 rationale move relocated -> `docs/builder/bld-031-slice-6-spec_032_citation_repair.md`
- [x] Slice 7: correct the card-052 rationale-companion census this cycle falsified, and re-render the board -> `docs/builder/bld-031-slice-7-card_052_companion_census.md`
- [x] Slice 8: repair `spec-032`'s citations into text the **spec-030** rationale move relocated -> `docs/builder/bld-031-slice-8-spec_032_spec_030_citations.md`
- [x] Slice 9: home the two open items that live only in this cycle's artifacts onto card 052, and re-render -> `docs/builder/bld-031-slice-9-card_052_homing.md`
