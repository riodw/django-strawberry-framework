# Spec: Beta release — cleanup, verification, and the alpha → beta cut-over to `0.1.0`

Planned for `0.1.0` (card `TODO-ALPHA-047-0.1.0`); **this card is the only
card at `0.1.0` and owns the version bump**
([Decision 3](#decision-3--lone-card-at-010--the-release-slice-owns-the-version-cut)).
Number conventions in this spec: bare three-digit numbers (`045` / `046` /
`047` / `062`) are **kanban card numbers**, dotted numbers (`0.0.15` /
`0.0.16` / `0.1.0` / `1.0.0`) are **package versions** — card `047` is the
card that cuts version `0.1.0`.
This card is a **release / verification card**: it ships no new subsystem and
no new consumer-facing symbol
([Decision 1](#decision-1--verification-only--the-consumer-surface-is-frozen)).
Its purpose is to make the alpha → beta milestone explicit and give the
cleanup / verification work a single named slice, instead of letting the
transition dissolve into an unstructured handful of doc tweaks and version
bumps spread across the last few patches. Concretely it does five things in
sequence:

1. **Gate on the Alpha queue.** Every other Alpha card must be `DONE` before
   this card's release slice may run — including the two cards the card
   body's stale `DONE-013`–`DONE-044` range predates
   ([Decision 2](#decision-2--the-gating-set-is-the-whole-alpha-queue-not-the-cards-stale-done-range)):
   `TODO-ALPHA-045-0.0.15` ([`spec-045`][spec-045]) and
   `TODO-ALPHA-046-0.0.16` ([`spec-046`][spec-046]).
2. **Run the parity audit.** Every ⚛️ (`graphene-django`) and 🍓
   (`strawberry-graphql-django`) finding from the two upstream audits is
   either `DONE` or explicitly deferred with a recorded reason
   ([Decision 6](#decision-6--the-parity-audit-is-a-disposition-ledger-not-a-re-audit)) —
   `0.1.0` is, by definition, the feature-parity milestone.
3. **Verify the matrix.** A full test pass under each supported
   `(Python, Django, Strawberry)` combination, with package coverage held at
   100% ([Decision 5](#decision-5--matrix-verification-rides-the-existing-ci-matrix-plus-isolated-venvs)).
4. **Do the milestone doc work.** `0.1.0` is a minor-version rollover, so the
   cut carries more than a version bump
   ([Decision 4](#decision-4--a-milestone-0-cut-carries-more-than-the-version-quintet)):
   the `alpha constraint` status tags in [`docs/GLOSSARY.md`][glossary] are
   lifted or re-worded, the board's `## Progress to 1.0.0` section advances,
   the alpha-status prose in `README.md` / `GOAL.md` / `TODAY.md` /
   `docs/README.md` flips to beta, the PyPI Development-Status trove
   classifier moves off `1 - Planning`, and a fresh `## [0.1.0]` entry is
   written atop `CHANGELOG.md`'s patch entries with the cumulative alpha history
   ([Decision 7](#decision-7--the-changelog-010-entry-covers-the-whole-shipped-alpha-line)).
5. **Cut, tag, publish.** The version quintet moves to `0.1.0`, the release
   is tagged in git, and the build is published to PyPI — with the
   tag-and-publish actions maintainer-executed
   ([Decision 8](#decision-8--tag-and-publish-are-maintainer-executed-actions)).

Status: **PLANNED — no slice built yet.**
Five slices: Slice 1 (**queue gate + parity audit**), Slice 2 (**matrix
verification + release-readiness checklist**), Slice 3 (**doc status
cross-check** against the actual shipped surface), Slice 4 (**milestone doc
chores + the `CHANGELOG.md` `0.1.0` entry**), Slice 5 (**the `0.1.0` version cut +
tag + PyPI publish + card wrap**).

Permission caveat: [`AGENTS.md`][agents] prohibits `CHANGELOG.md` edits
without explicit permission; this spec's Slice 4 grants that permission for
writing the fresh `[0.1.0]` entry, and no earlier slice touches it.

---

## Key glossary references

Terms this spec relies on (statuses per [`docs/GLOSSARY.md`][glossary]):

- [`DjangoType`][glossary-djangotype],
  [`finalize_django_types`][glossary-finalize_django_types],
  [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — the core
  read-side surface the doc cross-check verifies against reality.
- [`DjangoConnectionField`][glossary-djangoconnectionfield],
  [`DjangoNodeField`][glossary-djangonodefield],
  [`DjangoNodesField`][glossary-djangonodesfield],
  [`DjangoListField`][glossary-djangolistfield],
  [Relay Node integration][glossary-relay-node-integration] — the Relay
  surface whose parity claims the audit re-verifies.
- [`FilterSet`][glossary-filterset], [`OrderSet`][glossary-orderset] — the
  shipped query-side sidecars counted toward parity.
- [`DjangoMutation`][glossary-djangomutation],
  [`DjangoFormMutation`][glossary-djangoformmutation],
  [`DjangoModelFormMutation`][glossary-djangomodelformmutation],
  [`SerializerMutation`][glossary-serializermutation],
  [Auth mutations][glossary-auth-mutations],
  [`FieldError` envelope][glossary-fielderror-envelope] — the three write
  flavors plus session auth, the largest parity block the audit closes out.
- [`Upload` scalar][glossary-upload-scalar],
  [`DjangoFileType`][glossary-djangofiletype],
  [`DjangoImageType`][glossary-djangoimagetype] — the file/image wire
  contract listed in the shipped-surface cross-check.
- [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter],
  [Debug-toolbar middleware][glossary-debug-toolbar-middleware],
  [`TestClient`][glossary-testclient],
  [`GraphQLTestCase`][glossary-graphqltestcase],
  [Response-extensions debug middleware][glossary-response-extensions-debug-middleware],
  [`DjangoDebugExtension`][glossary-djangodebugextension] — the `0.0.14`
  joint-cut surfaces, the last parity features to land before this card.
- [Visibility boundary][glossary-visibility-boundary],
  [Sealed execution queryset][glossary-sealed-execution-queryset],
  [`apply_cascade_permissions`][glossary-apply_cascade_permissions] — the
  hardened permission seams whose GLOSSARY status lines the cross-check
  re-verifies.
- [Joint version cut][glossary-joint-version-cut] — the release rule this
  card inverts: as the lone card at `0.1.0` it owns the cut itself.
- [Soft dependency][glossary-soft-dependency],
  [Hard dependency][glossary-hard-dependency],
  [`require_optional_module`][glossary-require_optional_module] — the
  dependency posture the published `0.1.0` wheel must preserve (import
  innocence with extras absent).
- [Live-first coverage mandate][glossary-live-first-coverage-mandate],
  [Strictness mode][glossary-strictness-mode],
  [Plan cache][glossary-plan-cache],
  [Schema audit][glossary-schema-audit] — verification-tier vocabulary the
  test plan cites.
- [Cookbook parity][glossary-cookbook-parity],
  [Single-upstream parity][glossary-single-upstream-parity] — the two
  parity disciplines the Slice 1 audit applies.
- [Cross-subsystem invariants][glossary-cross-subsystem-invariants] — the
  `1.0.0`-scoped goals the beta docs must keep pointed at the beta queue,
  not claim early.
- [`FieldSet`][glossary-fieldset], [`Meta.fields_class`][glossary-metafields_class],
  [`Meta.search_fields`][glossary-metasearch_fields],
  [`AggregateSet`][glossary-aggregateset],
  [`Meta.aggregate_class`][glossary-metaaggregate_class],
  [`Meta.choice_enum_names`][glossary-metachoice_enum_names] — the beta-line
  (`0.1.x`) surfaces this card explicitly does NOT ship; the doc flips must
  keep them `planned`.
- [`ConfigurationError`][glossary-configurationerror] — cited by the
  alpha-constraint re-wording work (the surviving constraints raise it).

## Slice checklist

Each top-level item maps to one commit / PR. **Five slices.** The card is an
M: no new code, but the verification and doc breadth is real and each slice
is a distinct gate.

- [ ] **Slice 1 — Queue gate + parity audit**
  - [ ] Verify every other Alpha card is `DONE`: the card body's
        `DONE-013-0.0.4` … `DONE-044-0.0.14` range (plus `DONE-024-0.0.7` and
        the later 0.0.14-line `DONE-064-0.0.14` sealed-visibility-boundary card)
        AND the later-added `TODO-ALPHA-045-0.0.15` /
        `TODO-ALPHA-046-0.0.16` ([Decision 2](#decision-2--the-gating-set-is-the-whole-alpha-queue-not-the-cards-stale-done-range)).
        If either is not `DONE`, this card stops here.
  - [ ] Run the parity-disposition audit
        ([Decision 6](#decision-6--the-parity-audit-is-a-disposition-ledger-not-a-re-audit)):
        every ⚛️ / 🍓 card from the two upstream audits is `DONE` or
        explicitly deferred with a recorded reason (a beta card, a
        `BACKLOG.md` row, or a named non-goal). The output is a disposition
        ledger appended to this spec (or a sibling audit note) — one row per
        finding, no silent omissions.
  - [ ] Verify no stale skipped tests refer to already-shipped slices
        (board release-readiness item; `rg -n "skip" tests/ examples/` sweep
        with each hit dispositioned).
- [ ] **Slice 2 — Matrix verification**
  - [ ] Full-matrix CI run (workflow_dispatch on
        `.github/workflows/django.yml` — the full matrix including the
        sharded `FAKESHOP_SHARDED=1` rows) green.
  - [ ] Local floor/ceiling spot-checks in **isolated** venvs (never the
        shared `.venv`): the pinned floor row
        (`Django==5.2.0`, `strawberry-graphql==0.316.0`, Python 3.10) and
        the newest row (Django 6.0 line, Python ≥ 3.12)
        ([Decision 5](#decision-5--matrix-verification-rides-the-existing-ci-matrix-plus-isolated-venvs)).
  - [ ] `uv run pytest` green with package coverage at 100%
        (`fail_under = 100`), `uv run ruff format .` and
        `uv run ruff check --fix .` clean — the board's release-readiness
        checklist discharged item by item.
- [ ] **Slice 3 — Doc status cross-check**
  - [ ] `README.md`, `docs/README.md`, `docs/GLOSSARY.md`, `docs/TREE.md`
        cross-checked against the actual shipped surface: every `shipped`
        marker names a real, tested capability; every `planned` marker names
        a live beta card; the README top-level export list matches
        `django_strawberry_framework/__init__.py::__all__`.
  - [ ] GLOSSARY edits go through the glossary **DB** + re-render
        (`scripts/build_glossary_md.py`), never hand-edits; `docs/TREE.md`
        via `scripts/build_tree_md.py`.
- [ ] **Slice 4 — Milestone doc chores + the `CHANGELOG.md` `0.1.0` entry**
  - [ ] Lift or re-word every `alpha constraint` status tag in
        [`docs/GLOSSARY.md`][glossary]: a constraint the alpha line actually
        resolved is lifted; a constraint that survives into beta (e.g.
        [`DjangoType`][glossary-djangotype]'s deferred manual
        relation-cardinality validation) is re-worded so it no longer claims
        the alpha phase ([Decision 4](#decision-4--a-milestone-0-cut-carries-more-than-the-version-quintet),
        [Risks](#risks-and-open-questions)).
  - [ ] Flip the milestone-status prose: `README.md` "Status" section,
        `GOAL.md` / `TODAY.md` alpha framing, `docs/README.md` "Today and
        coming next" (the `0.1.0` row moves from coming-next to shipped),
        and the GLOSSARY status-legend / package-version lines.
  - [ ] Advance the board's `## Progress to 1.0.0` section — via the kanban
        DB + `scripts/build_kanban_md.py` / `build_kanban_html.py` regen,
        never a hand edit of the generated exports.
  - [ ] Move the PyPI trove classifier off
        `Development Status :: 1 - Planning`
        ([Decision 4](#decision-4--a-milestone-0-cut-carries-more-than-the-version-quintet)).
  - [ ] Write a fresh `CHANGELOG.md` `## [0.1.0] - YYYY-MM-DD` entry atop the
        existing `## [0.0.x]` patch entries (the repo keeps no `[Unreleased]`
        block), with a one-paragraph release summary plus cumulative
        Added / Changed / Fixed / Removed sections covering the shipped
        alpha line ([Decision 7](#decision-7--the-changelog-010-entry-covers-the-whole-shipped-alpha-line);
        permission granted by this slice).
- [ ] **Slice 5 — The `0.1.0` cut + tag + publish + card wrap**
  - [ ] The version quintet: `pyproject.toml` `[project].version`,
        `django_strawberry_framework/__init__.py::__version__`,
        `tests/base/test_init.py`, the GLOSSARY package-version row, the
        root package entry in `uv.lock`.
  - [ ] `uv build`; maintainer tags the release and runs `uv publish`
        ([Decision 8](#decision-8--tag-and-publish-are-maintainer-executed-actions));
        post-publish, a `pip install django-strawberry-framework==0.1.0`
        smoke check in an isolated venv imports cleanly with no extras.
  - [ ] Card flip to Done + `KANBAN.md` / `KANBAN.html` regeneration from
        the DB; `import_spec_terms` run against this spec.

## Problem statement

Alpha's stated exit criterion has always been feature parity with the two
upstreams — the board's To-Do-Alpha column header says so, and
[`docs/GLOSSARY.md`][glossary] pins `0.1.0` as "beta release: feature parity
with `graphene-django` and `strawberry-graphql-django` (alpha → beta
cut-over)". Every parity feature card in the alpha queue is done or
scheduled ahead of this card; what has no home is the cut-over itself. When
every other Alpha card is `DONE`, this card is the only thing left between
the current state and the beta release, and without it the transition
becomes an unstructured handful of doc tweaks and version bumps spread
across the last few patches: the parity audit never happens on a named
slice, the full matrix pass never blocks anything, the `alpha constraint`
glossary tags and the "alpha-quality" README prose go stale the moment
`0.1.0` ships, and the `0.1.0` release notes never get a single coherent
entry of their own. Tracking the release as its own card forces all of that
to happen once, in order, with evidence.

## Current state

- The package sits at `0.0.14` (the four-card joint alpha cut). Two Alpha
  cards remain ahead of this one: `TODO-ALPHA-045-0.0.15` (the
  [`DjangoDebugExtension`][glossary-djangodebugextension] extraction,
  [`spec-045`][spec-045]) and `TODO-ALPHA-046-0.0.16` (boundary hardening +
  DRY squeeze, [`spec-046`][spec-046]). Both are sequenced before this card
  and both are lone-card cuts that own their own patch versions.
- The card body's Definition-of-done range ("every other Alpha card
  `DONE-013-0.0.4` through `DONE-044-0.0.14` plus `DONE-024-0.0.7`")
  predates the addition of cards 045 / 046 to the alpha queue — a genuine
  card-text staleness this spec resolves by Decision 2 and records in
  [Risks](#risks-and-open-questions).
- The supported matrix per `pyproject.toml`: Python `>=3.10,<4.0`
  (classifiers 3.10–3.14), `Django>=5.2` (classifiers 5.2 / 6.0),
  `strawberry-graphql>=0.316.0`, `django-filter>=25.2`. CI
  (`.github/workflows/django.yml`) carries the pinned floor row
  (`Django 5.2.0` / Python 3.10 / `strawberry 0.316.0`) through the newest
  rows, each in single-DB and sharded (`FAKESHOP_SHARDED=1`) variants; the
  full matrix runs on `workflow_dispatch`.
- The board carries its own `## Release readiness checklist` (version sites
  match, README matches exports, docs agree on shipped/planned state, no
  stale skips, mirrored tests, ruff clean, pytest at 100%) — this card is
  where that checklist is actually executed.
- The PyPI trove classifier still says `Development Status :: 1 - Planning`,
  which was stale even for alpha and is flatly wrong for a beta.
- `CHANGELOG.md` has never had a minor-version promotion; every entry so far
  is a `0.0.x` patch entry gated behind the maintainer-permission rule.
  One 0.0.14-line hardening — the sealed `get_queryset` visibility boundary
  (card `DONE-064-0.0.14`) — shipped after the `## [0.0.14]` entry was written
  and has no CHANGELOG coverage yet; the `0.1.0` aggregation is where it lands.
- The two upstream parity audits (the ⚛️ `graphene-django` audit and the 🍓
  `strawberry-graphql-django` audit) produced the card set that became the
  alpha queue; the "Alpha cards must claim upstream parity" board decision
  (2026-06-09) forced each shipped card to ground its claim in a specific
  upstream `path::symbol`. What has never been produced is the closing
  disposition ledger — the proof that no audit finding was silently
  dropped.

## Goals

- The alpha → beta cut is a single, evidence-backed event: queue verified
  empty, parity findings dispositioned, matrix green, docs truthful, version
  cut, tag pushed, wheel published.
- `0.1.0` is installable from PyPI and imports cleanly with no optional
  extras present (the [soft dependency][glossary-soft-dependency] import
  innocence holds on the published artifact, not just the repo tree).
- Every status surface — README, `docs/README.md`, GLOSSARY, TREE, GOAL,
  TODAY, the board — agrees the package is a beta, and none of them claims
  anything the shipped surface cannot do.
- The `alpha constraint` vocabulary is retired from
  [`docs/GLOSSARY.md`][glossary]: lifted where the constraint fell, re-worded
  where it survives into beta.
- The `CHANGELOG.md` `[0.1.0]` entry is the readable summary of the whole
  alpha line — a new consumer can learn what the package is from that one
  entry.

## Non-goals

- **No new subsystem, symbol, or behavior change.** The predicted package
  delta is exactly the version string (and the trove classifier). Anything
  discovered mid-verification that needs code gets its own card
  ([Decision 1](#decision-1--verification-only--the-consumer-surface-is-frozen)).
- **No API freeze.** Strict SemVer begins at `1.0.0`
  (`TODO-STABLE-062-1.0.0`), not here. Beta may still break pre-`1.0`
  contracts with documented migrations, exactly as alpha did.
- **No beta-line feature pull-forward.** [`FieldSet`][glossary-fieldset] /
  [`Meta.fields_class`][glossary-metafields_class] (`0.1.1`),
  [`Meta.search_fields`][glossary-metasearch_fields] (`0.1.2`),
  [`AggregateSet`][glossary-aggregateset] /
  [`Meta.aggregate_class`][glossary-metaaggregate_class] (`0.1.3`), and
  [`Meta.choice_enum_names`][glossary-metachoice_enum_names] (`0.1.4`) stay
  `planned`; the doc flips must not soften their status.
- **No migration-guide authoring.** Migration and adoption guides are
  `TODO-BETA-058-0.1.6`.
- **No CI matrix redesign.** The matrix is exercised as it exists; adding
  rows or version floors is not this card.

## Borrowing posture

There is nothing to borrow: this card ships process, not code. The card's
board labels pin it as "release / verification card — gates the alpha → beta
cut; not an upstream-parity feature", so the board's "Alpha cards must claim
upstream parity" decision does not bind it (no `ParityClaim`, no
`Verified in upstream` section — the card body carries neither). The
upstreams enter this card only as the **object** of Slice 1's audit: the two
parity audits' ⚛️ / 🍓 findings are dispositioned against the shipped
surface, applying the established
[single-upstream parity][glossary-single-upstream-parity] rule (a surface
only one upstream ships claims parity with that one, recording the other's
absence plainly) and the [cookbook parity][glossary-cookbook-parity]
obligation (migration claims validate against the working
`django-graphene-filters` cookbook, not a hypothetical app).

## User-facing API

None. The consumer-visible changes are exactly:

- `django_strawberry_framework.__version__` == `"0.1.0"` (and the matching
  `[project].version`).
- The PyPI Development-Status trove classifier moves off `1 - Planning`
  ([Decision 4](#decision-4--a-milestone-0-cut-carries-more-than-the-version-quintet)).
- The published release notes (`CHANGELOG.md` `[0.1.0]`) and the beta-status
  documentation set.

Every import path, symbol, wire format, and error contract is byte-identical
to the last shipped alpha patch (the 046 cut, planned `0.0.16`).

## Architectural decisions

### Decision 1 — Verification only — the consumer surface is frozen

**Decision**: this card ships no code beyond the version-quintet sites (the
card's predicted files are `django_strawberry_framework/__init__.py` and
`tests/base/test_init.py`, plus `pyproject.toml` / `uv.lock`). Every
verification failure discovered by Slices 1–3 is dispositioned as either
(a) a doc fix (in scope — Slice 3/4 own doc truthfulness), or (b) a code
defect, which **blocks the cut and gets its own card** rather than being
absorbed here. A release card that quietly grows a bug-fix payload defeats
its purpose: the cut must certify the queue that already shipped, not smuggle
one more change past the per-card review discipline.

**Alternative rejected**: folding small fixes into the release card
("while I'm here") — the repo's standing scope-creep rule
([`START.md`][start]) and the audit trail both argue for a clean cut; a
blocking defect at this stage is precisely the signal that the alpha queue
was not actually done.

### Decision 2 — The gating set is the whole Alpha queue, not the card's stale `DONE` range

**Decision**: the Slice 1 gate is "**every other non-Done Alpha card is
`DONE`**" — concretely `TODO-ALPHA-045-0.0.15` and `TODO-ALPHA-046-0.0.16`
at authoring time — in addition to the card body's enumerated
`DONE-013-0.0.4` … `DONE-044-0.0.14` (plus `DONE-024-0.0.7`) range — and the
later 0.0.14-line `DONE-064-0.0.14`, which shipped after the card body was
written — all verified as already satisfied.

**Rationale**: the card's Definition-of-done range was written before cards
045 / 046 entered the queue (the card predates the renumber that
[`spec-046`][spec-046]'s Out-of-scope section records: "the beta-release
cleanup card (now `TODO-ALPHA-047-0.1.0` after the renumbers)"). The board
column's own framing — "The final card in this column is the `0.1.0` release
itself" — is the intent; a literal reading of the stale range would let this
card cut `0.1.0` while `0.0.15` / `0.0.16` sit unshipped, which would strand
two lone-card cuts behind a minor version that already passed them. Per the
authoring flow's conflict rule the card text is preferred where it decides
scope, but here the card text and the board column conflict with each other;
this Decision resolves toward the column and the conflict is recorded in
[Risks](#risks-and-open-questions).

**Alternative rejected**: cutting `0.1.0` immediately after `0.0.14` and
re-versioning cards 045 / 046 onto the `0.1.x` line — both are
maintainability cards, not beta features; renumbering the queue again costs
more than holding the milestone until the alpha line drains, and the
maintainer sequenced them into alpha deliberately (extraction before the
boundary card, both before beta).

### Decision 3 — Lone card at `0.1.0` — the release slice owns the version cut

Per the Step 3 scan, this card is the **only** non-Done card at `0.1.0`: its
alpha-queue neighbors are `0.0.15` (the lone extraction card 045 owns that
cut) and `0.0.16` (the lone boundary card 046 owns that cut), and the next
column starts the `0.1.x` beta line. So this spec mirrors the lone-card
shape ([`spec-046`][spec-046] Decision 11, spec-038 Decision 14): Slice 5
carries the version quintet — `pyproject.toml` `[project].version`,
`django_strawberry_framework/__init__.py::__version__`,
`tests/base/test_init.py`, the GLOSSARY package-version row, the root
package entry in `uv.lock` — and no earlier slice moves any of the quintet.
The [joint version cut][glossary-joint-version-cut] rule is satisfied
trivially: a queue of one is its own last card. Unusually for the shape,
this quintet is a **minor**-version move, which is why Decision 4 expands
what rides the cut.

### Decision 4 — A milestone (`.0`) cut carries more than the version quintet

**Decision**: because `0.1.0` is a minor-version rollover — the board's
`## To Do - Alpha (0.1.0)` header names it as the column's release target —
the cut carries the milestone-completion chores as **first-class Slice 4
deliverables**, not afterthoughts:

- **`alpha constraint` tags in [`docs/GLOSSARY.md`][glossary]**: each is
  dispositioned. A constraint the alpha line resolved is lifted. A
  constraint that survives (at authoring time, the known survivor is
  [`DjangoType`][glossary-djangotype]'s "manual override validation for
  relation cardinality is deferred; the package trusts relation-field
  annotations supplied by the consumer") is **re-worded, not lifted** — this
  card ships no code, so it cannot resolve a real constraint; the wording
  simply stops claiming the alpha phase (e.g. "current constraint" /
  "deferred to the beta line"). The status-legend definition of
  `alpha constraint` itself is updated or retired to match. All via the
  glossary DB + re-render.
- **`## Progress to 1.0.0`**: the board section advances (Alpha row to
  48/48, overall percentage recomputed) — via the kanban DB + regen.
- **Milestone-status prose**: `README.md`'s "Status" section
  ("`0.0.14`, single-maintainer, alpha-quality") becomes the beta framing;
  `docs/README.md`'s "Today and coming next" moves the `0.1.0` row from
  coming-next to shipped; `GOAL.md` / `TODAY.md` alpha references flip;
  the GLOSSARY's "Current package version / Alpha-quality" line becomes the
  beta line.
- **The trove classifier**: `Development Status :: 1 - Planning` →
  `Development Status :: 4 - Beta` in `pyproject.toml` `classifiers` — the
  one place the published index itself encodes the milestone. (`4 - Beta` is
  the exact trove term for this phase; `3 - Alpha` was never set, which is
  recorded as accepted staleness, not retro-fixed.)

**Alternative rejected**: treating the milestone chores as ordinary Slice 5
doc fold-in — the authoring flow pins milestone cuts as a distinct, expanded
obligation precisely because these items are invisible to the routine
patch-cut checklist and rot silently when skipped.

### Decision 5 — Matrix verification rides the existing CI matrix plus isolated venvs

**Decision**: the "full test pass under each supported
`(Python, Django, Strawberry)` combination" requirement is discharged by
(a) a full-matrix CI run — `workflow_dispatch` on
`.github/workflows/django.yml`, which runs every row including the pinned
floor (`Django==5.2.0` / Python 3.10 / `strawberry-graphql==0.316.0`) and
the sharded `FAKESHOP_SHARDED=1` variants — and (b) two local spot-checks in
**isolated** venvs (`uv venv /tmp/... && uv pip install --python <path>`):
the floor row and the newest row (the Django 6.0 line, which requires
Python ≥ 3.12). The shared `.venv` is never mutated for matrix testing —
`uv pip install` ignores `UV_PROJECT_ENVIRONMENT` and would corrupt the
concurrent sessions' environment.

**Rationale**: CI is the authoritative matrix (it already encodes the
supported combinations and the two database topologies); local isolated
runs exist to make the floor and ceiling reproducible without a CI
round-trip and to smoke the built wheel. Defining the matrix in this spec
would duplicate — and eventually contradict — the workflow file.

**Alternative rejected**: a local tox/nox matrix harness — new tooling for a
one-card need; the CI matrix plus two spot rows covers the same evidence.

### Decision 6 — The parity audit is a disposition ledger, not a re-audit

**Decision**: Slice 1 does not re-run the upstream audits. It takes the
existing ⚛️ / 🍓 finding set — the audit-derived cards on the board plus each
shipped card's `Verified in upstream` claims — and produces a **disposition
ledger**: one row per finding, each marked `DONE` (naming the shipping
card), `deferred` (naming the beta card or `BACKLOG.md` row and the recorded
reason), or `rejected` (naming the decision that rejected it). The
[single-upstream parity][glossary-single-upstream-parity] rule applies to
findings only one upstream ships; the
[cookbook parity][glossary-cookbook-parity] rule governs any migration-claim
row. A finding with **no** disposition is a cut blocker: either a card is
created (and the cut waits, per Decision 1) or a deferral is recorded with
maintainer sign-off.

**Rationale**: the parity claim is `0.1.0`'s entire semantic content — the
version means "parity reached". The claim is only as good as the proof that
nothing fell off the queue between the audits (which produced the cards) and
the cut (which certifies them). A fresh re-audit of both upstreams would be
a much larger card and would re-litigate settled deferrals; the ledger
closes the loop at the right cost.

**Alternative rejected**: full upstream re-audit against current upstream
HEADs — upstream moved during alpha (new upstream features are future
findings, not alpha debt); the parity target was always the audited surface,
and chasing a moving target makes the milestone undefinable.

### Decision 7 — The CHANGELOG `0.1.0` entry covers the whole shipped alpha line

**Decision**: a fresh `## [0.1.0] - YYYY-MM-DD` heading is authored atop the
existing patch entries (the repo keeps no `[Unreleased]` block), carrying
(a) a one-paragraph release summary — the
package's positioning sentence plus the parity statement — and (b)
cumulative `Added` / `Changed` / `Fixed` / `Removed` sections covering the
shipped alpha line **from `0.0.6` through the last alpha patch actually
shipped** (at authoring time that is expected to be `0.0.16`, after cards
045 / 046 land). The card text says "covering `0.0.6` through `0.0.14`"
because it predates the 045 / 046 queue additions — the same staleness
Decision 2 resolves; the extended range is the card's evident intent (the
cumulative history of the line being released). One 0.0.14-line change never
received its own CHANGELOG entry — the sealed `get_queryset` visibility
boundary (card `DONE-064-0.0.14`), which landed after the `## [0.0.14]`
heading was written — so the aggregation must capture it (in `Changed` /
`Fixed`) rather than assume the existing patch headings already cover the
whole line. Breaking wire-format changes
that shipped mid-alpha (the `0.0.6` `PositiveBigIntegerField` → [`BigInt`][glossary-bigint-scalar]
switch, the `0.0.9` model-anchored `GlobalID` default, the `0.0.11`
file/image structured output) are called out explicitly in `Changed` — a
`0.0.5`-era consumer upgrading straight to `0.1.0` must be able to find
every wire break in one entry.

**Alternative rejected**: a thin `[0.1.0]` entry that just links the patch
entries — this entry is the one place the alpha line gets a coherent
narrative; a link farm defers the reading cost to every future consumer.

### Decision 8 — Tag and publish are maintainer-executed actions

**Decision**: Slice 5's terminal actions — the release commit, the git tag,
and `uv publish` — are executed by the maintainer. The executing agent
prepares everything up to that boundary (the quintet edits, `uv build`, the
built-artifact smoke check, the exact commands per [`CONTRIBUTING.md`][contributing]'s
publish flow) and stops. This follows the repo's standing authorization
rules ([`AGENTS.md`][agents]: no commits without an explicit ask, never
branch/tag without authorization) and the practical one: `uv publish`
requires the maintainer's PyPI token, which the agent must never handle.
Post-publish, the agent-side verification resumes: an isolated-venv
`pip install django-strawberry-framework==0.1.0` must import cleanly with
no extras installed and report `__version__ == "0.1.0"`.

**Alternative rejected**: automating tag + publish behind a CI release
workflow — worth considering for the beta line, but building release
automation is new scope (Decision 1) and this card's job is to cut one
release, not to ship a release pipeline.

## Implementation plan

Per-slice delta table (this card's weight is verification breadth; the code
delta is the quintet):

| Slice | Work | Files touched | Risk profile |
|---|---|---|---|
| 1 | Queue gate + parity disposition ledger + stale-skip sweep | this spec (ledger); none in-package | LOW — read-only audit; blockers stop the card |
| 2 | Full-matrix CI dispatch + isolated floor/ceiling venv runs + release-readiness checklist | none (verification only) | MEDIUM — a red row blocks the cut |
| 3 | Doc status cross-check | `README.md`, `docs/README.md`, `docs/GLOSSARY.md` (DB+regen), `docs/TREE.md` (regen) | LOW — doc-only |
| 4 | Milestone chores + the CHANGELOG `0.1.0` entry | GLOSSARY DB+regen, kanban DB+regen, `README.md`, `GOAL.md`, `TODAY.md`, `docs/README.md`, `pyproject.toml` (classifier), `CHANGELOG.md` | MEDIUM — permission-gated file; generated-file discipline |
| 5 | Version quintet + build + tag + publish + card wrap | `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `uv.lock`, GLOSSARY version row, kanban regen | MEDIUM — the irreversible step is maintainer-executed |

Sequencing constraints: Slice 1 gates everything (Decision 2). Slice 2 runs
against the tree after the last alpha patch lands (the 046 cut, planned
`0.0.16`), not before. Slices 3 and 4 may interleave
(both are doc passes) but Slice 4's CHANGELOG entry lands last among the
doc edits so the release date is real. Slice 5 moves the quintet only after
Slices 1–4 are green — the version string is the last thing to change, so an
aborted cut leaves no half-released state.

## Helper-reuse obligations (DRY)

This card introduces no helpers. Its obligation is the inverse — reuse the
existing release machinery rather than re-spelling it: the glossary DB +
`scripts/build_glossary_md.py` for every GLOSSARY edit, the kanban DB +
`scripts/build_kanban_md.py` / `scripts/build_kanban_html.py` for the board
(both are generated exports; hand edits decay), `scripts/build_tree_md.py`
for `docs/TREE.md`, the [`CONTRIBUTING.md`][contributing] publish flow
(`uv build` / `uv publish`) verbatim, and `scripts/check_spec_glossary.py`
plus `import_spec_terms` for this spec's own term hygiene at card wrap.

## Edge cases and constraints

- **Concurrent sessions**: the maintainer runs parallel sessions against
  this tree. Slice 2's verification runs must be coordinated — a full-suite
  gate is meaningless over a tree carrying another session's half-landed
  work, and the fakeshop `db.sqlite3` must not be reset while a concurrent
  card-wrap is active. Reconcile the working-tree state with the maintainer
  before treating any red as this card's blocker.
- **Generated files**: `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` /
  `docs/TREE.md` are DB- or script-rendered; every Slice 3/4 edit goes
  through the source and re-render, and the resulting diff is checked to
  contain only the intended change.
- **`uv.lock` scope**: the quintet touches only the root package's own
  `version` entry; dependency entries move with dependency-gate cards, never
  with a release cut.
- **Trove classifier wording**: the classifier list is validated by PyPI at
  upload — `Development Status :: 4 - Beta` is the exact registered string;
  a typo fails at publish time, so the built wheel's metadata is checked
  before the maintainer publishes.
- **Isolated-venv discipline**: matrix and smoke installs never touch the
  shared `.venv` (`uv pip install --python /tmp/<venv>/bin/python`); the
  Django 6.0 rows require Python ≥ 3.12.
- **ASCII-only applies to `.py` sources**; the doc flips may keep existing
  typography. Ruff format/check run after any edit that touches Python
  (here: `tests/base/test_init.py`, `__init__.py`).

## Test plan

- **No new test surface**: the card adds no code, so the only test edit is
  `tests/base/test_init.py::test_version` moving to `0.1.0` in the same
  commit as the quintet (the [live-first coverage
  mandate][glossary-live-first-coverage-mandate] is untriggered — there is
  no new line to cover).
- **Gate 1 (Slice 2)**: full-matrix CI dispatch green — every
  `(Python, Django, Strawberry)` row, single-DB and sharded — plus the two
  isolated-venv spot rows. Package coverage at 100% (`fail_under = 100`).
- **Gate 2 (Slice 2)**: the board's release-readiness checklist executed
  item by item: version sites match, README matches
  `__init__.py::__all__`, docs agree on shipped/planned state, no stale
  skipped tests, mirrored tests for all source modules, `ruff format` /
  `ruff check` clean.
- **Gate 3 (Slice 5)**: built-artifact verification — `uv build`, then in an
  isolated venv: install the wheel, `import django_strawberry_framework`
  with no extras present (import innocence holds on the artifact),
  `__version__ == "0.1.0"`, and one minimal `DjangoType` +
  [`finalize_django_types`][glossary-finalize_django_types] schema build.
  Post-publish, the same smoke against the PyPI artifact.
- **Suite-run discipline**: per [`AGENTS.md`][agents], full-suite runs
  happen at the maintainer-invoked gates above, not after every edit.

## Doc updates

- Slice 3 (truthfulness pass): `README.md`, `docs/README.md`,
  `docs/GLOSSARY.md` (DB + re-render), `docs/TREE.md` (regen).
- Slice 4 (the milestone set): `docs/GLOSSARY.md` `alpha constraint`
  dispositions + status legend + package-version row (DB + re-render);
  `README.md` Status section; `GOAL.md` / `TODAY.md` milestone prose;
  `docs/README.md` "Today and coming next"; `KANBAN.md` / `KANBAN.html`
  `## Progress to 1.0.0` (DB + regen); `pyproject.toml` classifiers;
  `CHANGELOG.md` (permission granted by Slice 4).
- Slice 5: the version quintet's doc member (the GLOSSARY package-version
  row) plus the card flip and board regen; `import_spec_terms` against this
  spec at wrap.

## Risks and open questions

- **Card-text staleness (gating range and CHANGELOG range)**: the card's
  DoD names `DONE-013`–`DONE-044` and a CHANGELOG range ending at `0.0.14`,
  both predating cards 045 / 046. This spec resolves both toward the
  board-column intent (Decisions 2 and 7) — the conflict is recorded here
  per the authoring flow's prefer-the-card rule, because in this instance
  the card conflicts with the board's own column framing and with
  [`spec-046`][spec-046]'s sequencing decisions rather than with repo docs.
  Preferred answer: gate on 045 + 046 and cover the CHANGELOG through the
  last shipped alpha patch. Fallback: if the maintainer re-orders the queue
  (e.g. drops 046 from alpha), the gate set follows the queue, not this
  spec's snapshot.
- **Blocking defects found by verification**: a red matrix row or a parity
  finding with no disposition stops the cut (Decision 1). Preferred answer:
  card the defect, land it as its own patch, then re-enter this card at
  Slice 2. Fallback: none — a release card that ships around a known red
  defeats its purpose.
- **Surviving `alpha constraint` wording**: the known survivor
  ([`DjangoType`][glossary-djangotype]'s deferred relation-cardinality
  validation) needs a beta-appropriate status word; the glossary legend
  currently defines only `alpha constraint`. Preferred answer: re-tag the
  survivor(s) as plain current-behavior constraints with a deferral pointer
  (no new legend term), and drop `alpha constraint` from the legend once no
  entry uses it. Fallback: rename the legend term to a phase-neutral
  `constraint` and keep the tag. Resolve with the maintainer at Slice 4; the
  full inventory (`rg -n "alpha constraint" docs/GLOSSARY.md`) is taken at
  execution time, not trusted from this spec's snapshot.
- **`Development Status` classifier step**: `4 - Beta` is proposed
  (Decision 4); the maintainer may prefer to hold `3 - Alpha` semantics one
  more cycle. Preferred answer: `4 - Beta` — the version number and the
  README will both say beta, and the classifier should not contradict them.
  Fallback: any value except the current `1 - Planning`, which is wrong
  under every reading.
- **Publish mechanics**: [`CONTRIBUTING.md`][contributing] documents
  `uv build` + `uv publish --token`; whether the tag or the publish comes
  first, and the tag name format (`v0.1.0` vs `0.1.0`), are unpinned
  repo-wide. Preferred answer: tag `v0.1.0` on the release commit, publish
  from that tag's tree; recorded here so the beta line inherits a
  convention. Fallback: the maintainer's existing habit wins — the git tag
  history at execution time is the tiebreaker.
- **Upstream drift during alpha**: features either upstream shipped after
  the audits are not alpha debt (Decision 6) — but Slice 1 should note any
  obvious new upstream surface it trips over as candidate `BACKLOG.md`
  rows, without letting that grow into a re-audit.

## Out of scope (explicitly tracked elsewhere)

- The debug extraction and the boundary/DRY squeeze — cards 045
  ([`spec-045`][spec-045]) and 046 ([`spec-046`][spec-046]); this card gates
  on them and absorbs none of their scope.
- The beta feature line: [`FieldSet`][glossary-fieldset] (`0.1.1`),
  [`Meta.search_fields`][glossary-metasearch_fields] + Postgres full-text
  primitives (`0.1.2`), the aggregation subsystem
  ([`AggregateSet`][glossary-aggregateset], `0.1.3`), Layer-3 Meta-key
  promotion (`0.1.3`), redaction tier + stable enum naming (`0.1.4`),
  fakeshop activation + Layer-3 HTTP tests (`0.1.5`), mutation
  idempotency + migration guides (`0.1.6`), the adversarial
  suite / explain mode / filter-key namespace (`0.1.7`).
- The API freeze and stable cut-over — `TODO-STABLE-062-1.0.0`.
- Release-pipeline automation (CI-driven tag/publish) — raised and rejected
  in Decision 8; a future card if the beta cadence warrants it.
- The [Cross-subsystem invariants][glossary-cross-subsystem-invariants]
  (`1.0.0`-scoped) — the beta docs keep pointing at them; this card does not
  claim them.

## Definition of done

- [ ] Every other Alpha card is `DONE` — the card body's
      `DONE-013-0.0.4` … `DONE-044-0.0.14` range (plus `DONE-024-0.0.7` and the
      later 0.0.14-line `DONE-064-0.0.14`)
      verified, AND `TODO-ALPHA-045-0.0.15` / `TODO-ALPHA-046-0.0.16`
      shipped (Decision 2).
- [ ] The parity disposition ledger exists: every ⚛️ / 🍓 audit finding is
      `DONE`, `deferred`-with-reason, or `rejected`-with-decision; zero
      undispositioned rows (Decision 6).
- [ ] Full-matrix CI run green across every supported
      `(Python, Django, Strawberry)` row including the sharded variants;
      floor and ceiling isolated-venv spot runs green; package coverage at
      100% (`fail_under = 100`).
- [ ] The board's release-readiness checklist discharged item by item; no
      stale skipped tests referring to shipped slices.
- [ ] Doc truthfulness pass complete: `README.md`, `docs/README.md`,
      `docs/GLOSSARY.md`, `docs/TREE.md` match the actual shipped surface;
      shipped/planned markers correct.
- [ ] Milestone chores landed: `alpha constraint` tags dispositioned in the
      glossary DB + re-rendered; `## Progress to 1.0.0` advanced via the
      kanban DB + regen; alpha-status prose flipped to beta in `README.md`,
      `GOAL.md`, `TODAY.md`, `docs/README.md`; trove classifier moved off
      `1 - Planning` (Decision 4).
- [ ] `CHANGELOG.md` gains a fresh `## [0.1.0] - YYYY-MM-DD` entry
      with the release summary and cumulative Added / Changed / Fixed /
      Removed sections covering the shipped alpha line, wire breaks called
      out (Decision 7).
- [ ] Version quintet at `0.1.0`: `pyproject.toml`,
      `django_strawberry_framework/__init__.py::__version__`,
      `tests/base/test_init.py`, the GLOSSARY package-version row, the root
      package entry in `uv.lock`.
- [ ] Release tagged in git and published to PyPI by the maintainer
      (Decision 8); post-publish isolated-venv smoke green (clean import
      with no extras, `__version__ == "0.1.0"`).
- [ ] Card flipped Done, `KANBAN.md` / `KANBAN.html` regenerated from the
      DB, `import_spec_terms` green against this spec.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[contributing]: ../CONTRIBUTING.md
[kanban]: ../KANBAN.md
[start]: ../START.md

<!-- docs/ -->
[glossary-aggregateset]: GLOSSARY.md#aggregateset
[glossary-apply_cascade_permissions]: GLOSSARY.md#apply_cascade_permissions
[glossary-auth-mutations]: GLOSSARY.md#auth-mutations
[glossary-bigint-scalar]: GLOSSARY.md#bigint-scalar
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-cookbook-parity]: GLOSSARY.md#cookbook-parity
[glossary-cross-subsystem-invariants]: GLOSSARY.md#cross-subsystem-invariants
[glossary-debug-toolbar-middleware]: GLOSSARY.md#debug-toolbar-middleware
[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield
[glossary-djangodebugextension]: GLOSSARY.md#djangodebugextension
[glossary-djangofiletype]: GLOSSARY.md#djangofiletype
[glossary-djangoformmutation]: GLOSSARY.md#djangoformmutation
[glossary-djangographqlprotocolrouter]: GLOSSARY.md#djangographqlprotocolrouter
[glossary-djangoimagetype]: GLOSSARY.md#djangoimagetype
[glossary-djangolistfield]: GLOSSARY.md#djangolistfield
[glossary-djangomodelformmutation]: GLOSSARY.md#djangomodelformmutation
[glossary-djangomutation]: GLOSSARY.md#djangomutation
[glossary-djangonodefield]: GLOSSARY.md#djangonodefield
[glossary-djangonodesfield]: GLOSSARY.md#djangonodesfield
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-fielderror-envelope]: GLOSSARY.md#fielderror-envelope
[glossary-fieldset]: GLOSSARY.md#fieldset
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-finalize_django_types]: GLOSSARY.md#finalize_django_types
[glossary-graphqltestcase]: GLOSSARY.md#graphqltestcase
[glossary-hard-dependency]: GLOSSARY.md#hard-dependency
[glossary-joint-version-cut]: GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: GLOSSARY.md#live-first-coverage-mandate
[glossary-metaaggregate_class]: GLOSSARY.md#metaaggregate_class
[glossary-metachoice_enum_names]: GLOSSARY.md#metachoice_enum_names
[glossary-metafields_class]: GLOSSARY.md#metafields_class
[glossary-metasearch_fields]: GLOSSARY.md#metasearch_fields
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-plan-cache]: GLOSSARY.md#plan-cache
[glossary-relay-node-integration]: GLOSSARY.md#relay-node-integration
[glossary-require_optional_module]: GLOSSARY.md#require_optional_module
[glossary-response-extensions-debug-middleware]: GLOSSARY.md#response-extensions-debug-middleware
[glossary-schema-audit]: GLOSSARY.md#schema-audit
[glossary-sealed-execution-queryset]: GLOSSARY.md#sealed-execution-queryset
[glossary-serializermutation]: GLOSSARY.md#serializermutation
[glossary-single-upstream-parity]: GLOSSARY.md#single-upstream-parity
[glossary-soft-dependency]: GLOSSARY.md#soft-dependency
[glossary-strictness-mode]: GLOSSARY.md#strictness-mode
[glossary-testclient]: GLOSSARY.md#testclient
[glossary-upload-scalar]: GLOSSARY.md#upload-scalar
[glossary-visibility-boundary]: GLOSSARY.md#visibility-boundary
[glossary]: GLOSSARY.md
[spec-045]: spec-045-debug_extraction-0_0_15.md
[spec-046]: spec-046-boundary_dry_squeeze-0_0_16.md

<!-- docs/SPECS/ -->
[spec-038]: SPECS/spec-038-form_mutations-0_0_12.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
