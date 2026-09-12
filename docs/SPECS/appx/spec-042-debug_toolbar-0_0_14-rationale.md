# Rationale: spec-042 — Debug-toolbar middleware (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-042-debug_toolbar-0_0_14.md`][spec-042]. The spec is the
contract and states only what is currently true; everything that explains **how it got there**
lives here: the alternatives each decision rejected and why each lost, the derivations that do
not change how a decision is implemented, every change a decision has undergone with the round
that caused it, and every claim a decision once made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass. **The move
happened long after the release, not before the build.** Card `DONE-042-0.0.14` shipped with no
companion at all — the spec carried its deliberative layer inline, including a nine-entry
`Revision history` whose last entry was a *supersession note* telling the reader to reinterpret
text the spec still carried uncorrected. Four post-ship commits then corrected and extended what
the card shipped while the spec's prose stayed at the ship-time contract. This pass supplies the
companion and reconciles the spec in one custodian judgement, because what a decision now says
and what it used to say are decided together. Text marked *Moved* below was cut out of the spec,
not copied: it exists here and nowhere else.

## How to read this file

- **One entry per spec decision**, named by the decision's own heading and linked to its anchor,
  so a citation such as "Decision 9's rejected alternatives" resolves to exactly one place. An
  entry that named no decision could not be looked up and would be worthless however well
  argued. The two spec sections that carry deliberation without being numbered decisions —
  `## Borrowing posture` and `## Risks and open questions` — get their own entries under
  `## Non-decision entries`, keyed by section heading and anchor the same way.
- **Who reads it.** Worker 3 reads it during review; Worker 1 owns it; Worker 2 never reads it.
  A reader looking for what the package *does* wants the spec, not this file.
- **No timeline.** The spec's nine-entry `Revision history` block moved here and was
  **restructured into per-decision `Change record` blocks**. A reader asking "what did Decision 9
  used to say?" finds the answer under [Decision 9](#decision-9--test-strategy), not by reading a
  chronology and applying it. `## Round vocabulary` below names the rounds once so each block can
  cite one without restating it — and because the names have inbound citers that the move would
  otherwise strand. Measured over the tree rather than enumerated from memory: five, in two
  populations — three sentences in [`spec-043`][spec-043] citing "spec-042 Revision 8" by name for
  the shipped-spec closeout convention it settled, and two in first-party test source
  (`tests/middleware/test_debug_toolbar.py`, both "spec-042 Revision 5", both stating the reason
  they cite in the adjacent clause). Each is anchored to the spec by name, which is what
  [`AGENTS.md`][agents] rule 27's grading asks of a numbered-item citation, so none is a defect;
  what they need is a destination, and this section is it.
- **Three kinds of change are recorded, and they are not the same kind.** A *pre-implementation
  revision* changed a decision before any code existed (Revisions 1-8 are all of this kind). A
  *post-ship change* is the maintainer moving the shipped contract after the card closed
  (Revision 9 is the only one the spec recorded, and it was recorded as prose the reader had to
  apply). A *post-ship correction* is the shipped code having moved while the spec's prose did
  not. `## Post-ship corrections` carries the third kind for the whole spec, keyed by the finding
  numbers the post-ship reconciliation cycle's build plan assigned them, and each decision entry
  cross-links the ones that touch it.
- **Where a change record and the spec disagree, the spec is the contract** and the change record
  is why it moved. A claim the decision may no longer make is named in the record rather than
  deleted silently.
- **What deliberately stayed in the spec even though it reads like deliberation.** Decision 5's
  "the guard runs *before* the `debug_toolbar` imports the class body needs" ordering, Decision
  6's "chain to `super()._postprocess(...)` **first**" ordering and its account of what the stock
  method does in that order, Decision 9's `DEBUG=True` / import-ordering reasoning, the
  `## Edge cases and constraints` reasoning about why `Content-Length` is refreshed only when the
  header is already present, and the `## Test plan`'s note that a non-null `operationName`
  requires a *named* operation document are all instructions to a builder rather than records of
  thinking: a builder who never reads them writes the guard after the imports, skips the
  `super()` chain, or writes a Test 3 that fails GraphQL validation before proving anything.
  When it was unclear whether a sentence was deliberation or instruction, it stayed.

## Round vocabulary

The spec's `Revision history` block named nine revisions. They were not nine of the same thing,
and the distinction is what makes the per-decision records readable:

- **Revision 1** — the initial draft, authored from the `DONE-042-0.0.14` card body via the
  [`docs/SPECS/NEXT.md`][next] flow (2026-07-06). It pinned Decisions 1-10 and carried the
  `_postprocess`-is-private coupling into `## Risks and open questions` rather than reconciling
  it silently.
- **Revisions 2, 3, 4, 5, 6, 7 and 8** — seven successive maintainer-review absorption passes
  (2026-07-06 to 2026-07-08). Revision 2 ran two review rounds in one pass; Revision 4 was
  source-verified against the debug-toolbar `7.0.0` tag; Revision 5 was verified empirically
  before absorbing; Revision 6 was verified against the debug-toolbar `7.0.0` import chain.
- **Revision 9** — not a review round at all: a **post-ship maintainer change** (2026-07-09,
  commit `4015442d`) that brought forward the fakeshop opt-in Decision 2 had scoped out, and
  moved the toolbar-present tests to the live tier. The spec recorded it as a supersession note
  instructing the reader to reinterpret the ship-time text it named. That note is discharged by
  this pass: its content is reconciled into the spec directly and its record lives in
  [F3](#f3--the-test-urlconf-module-testsmiddlewaredebug_toolbar_urlspy-never-existed) and
  [F4](#f4--fakeshop-ships-the-toolbar) below.

Revisions 1-8 all happened **before implementation**. Nothing in those eight recorded what the
build discovered, which is why moving them costs the spec nothing a builder needed.

## Post-ship corrections

Findings from the spec-custody cohort and from the concurrent code-verification cohort, each
read against source at HEAD before being written down, and each recorded as *what the spec used
to claim* / *what HEAD does* / *which change caused it*. The custody findings (F1-F8, F-minor)
are spec-only: no code change was owed by that pass. The code-verification findings are the ones
that moved the shipped asset as well as the spec — the payload-shape guard
([M3](#m3--the-bridge-guarded-the-shape-of-data-but-not-of-its-debugtoolbar-value)) and, under
the same rule, the selector-safety of the panel key recorded in the
[Borrowing posture entry](#borrowing-posture--the-template-port) — and each entry says which
half is which.

The spec's own `## Current state` section is exempt from two of these by the vintage rule in
[`docs/builder/BUILD.md`][build] `### `## Current state`: observations stand, predictions do not`:
a bullet that dates an observation of the pre-build repo stays even when later work falsified it.
Where one of its bullets carried a *prediction* as well, the prediction was rewritten and the
observation kept — graded clause by clause, never bullet by bullet.

### F1 — the `-rationale.md` companion did not exist

*Claimed:* nothing; the spec simply had no companion, and its `Revision history` block opened
"kept inline so the spec is self-contained".
*HEAD:* `docs/SPECS/appx/` carried only `spec-042-debug_toolbar-0_0_14-terms.csv`, where every
sibling shipped spec from 040 onward carries both files.
*Cause:* the card shipped before [`docs/builder/BUILD.md`][build] `## Spec rationale extraction`
made the move pre-flight step 7. This file is the discharge.

### F2 — the spec narrated its own history

*Claimed:* nine inline revisions, ≈210 lines, the last of them a supersession note.
*HEAD:* the spec carries a one-line pointer to this file and no chronology at all.
*Cause:* as F1. Revision 9 was the acute case: a reader had to apply a post-ship note to four
named sections to learn what was currently true, which is the exact shape
[`docs/builder/BUILD.md`][build] forbids ("a reader must never reconstruct what is currently true
by applying a chronology to it").

### F3 — the test URLconf module `tests/middleware/debug_toolbar_urls.py` never existed

*Claimed:* a shipped file, named in the Slice-1 checklist, the `## Implementation plan` file
table (its own row), Decision 9's fixture contract (the `ROOT_URLCONF` bullet and the
schema-reload paragraph), the `## Test plan` fixture paragraph, Test 8, and the
`## Definition of done`.
*HEAD:* `tests/middleware/` holds `__init__.py` and `test_debug_toolbar.py` only. Fakeshop's own
`examples/fakeshop/config/urls.py` #"urlpatterns += debug_toolbar_urls()" supplies the `djdt`
routes, so no test URLconf is needed; the live fixture reloads `config.urls` inside its
`DEBUG=True` override instead. The JSON-leak negative that lived in that module's probe view was
recast as a `RequestFactory` unit,
`tests/middleware/test_debug_toolbar.py::test_unrelated_json_view_body_is_never_mutated`.
*Cause:* commit `4015442d` (Revision 9) deleted the module in the same change that wired
fakeshop.
*Why it mattered:* the module was named in **both** halves of the redundancy
[`START.md`][start] "Reconciling a spec with the tree" describes — the slice checklist and the
Definition of done are completion claims, so they get no vintage licence, and they disagreed
with the tree and with each other.

### F4 — fakeshop ships the toolbar

*Claimed:* fakeshop's shipped settings deliberately carry no `debug_toolbar` app and no toolbar
middleware — asserted in [Decision 2](#decision-2--card-scope-boundary), `## Current state`,
`## Non-goals`, and load-bearing for [Decision 9](#decision-9--test-strategy)'s whole placement
argument.
*HEAD:* `examples/fakeshop/config/settings.py` carries `"debug_toolbar"` in `INSTALLED_APPS`, the
package middleware's dotted path near the front of `MIDDLEWARE`, and
`INTERNAL_IPS = ["127.0.0.1"]`; `examples/fakeshop/config/urls.py` appends
`debug_toolbar_urls()`. Consequently the toolbar-present tests live at
`examples/fakeshop/test_query/test_debug_toolbar_api.py` and only the paths no live request can
reach stayed in `tests/middleware/test_debug_toolbar.py`.
*Cause:* commit `4015442d` (Revision 9) — the maintainer brought forward the dogfooding opt-in
Decision 2 had deferred to the fakeshop-activation card.
*Graded clause by clause:* `## Current state`'s bullet is a dated observation of the pre-build
repo and **stays**; the sentence inside it that predicted "and this card deliberately keeps it
that way" was a prediction about the outcome and was rewritten. Decision 2, `## Non-goals` and
Decision 9 carry live contract claims and were corrected outright.

### F5 — Decision 7's premise "the package ships no view class" is false, and the detection still works

*Claimed:* "the package ships no view class" at four sites (the opener, `## Current state`,
`## Non-goals`, Decision 7 itself), with "Ship a package `DjangoGraphQLView` and detect that"
rejected as an alternative and a `## Risks` bullet hedging "if a future card ships a package view
class, the one `issubclass` line is that card's to update".
*HEAD:* `django_strawberry_framework/views.py::DjangoGraphQLView` and
`django_strawberry_framework/views.py::AsyncDjangoGraphQLView` ship, and
`examples/fakeshop/config/urls.py` mounts the package's own view rather than Strawberry's.
**The detection resolves unchanged:** `DjangoGraphQLView` is declared
`django_strawberry_framework/views.py` #"class DjangoGraphQLView(_RequestBodyBoundaryMixin, GraphQLView)"
and strawberry's `GraphQLView` subclasses `BaseView`, so `issubclass(view, BaseView)` is true for
the package's own view.
*Cause:* [`spec-046`][spec-046] (transport security) shipped the view for its own reasons —
exactly the escape route Decision 7's rejected alternative named ("if a future card ships a
package view for its own reasons, it subclasses `BaseView` and detection keeps working
unchanged"). The hedge **resolved to no update needed**, which is a fact the spec states rather
than a change it hides.
*The claim these sections may no longer make:* that no package view class exists. The claim that
survives, and is now stated as resolved rather than hedged, is that the detection target stays
engine-owned.

### F6 — the Strawberry floor the spec named is stale

*Claimed:* `strawberry-graphql>=0.262.0` / `==0.262.0` at four sites — the Slice-1 view-class
gate, Decision 7's mechanical notes, the `## Risks` floor bullet, and the
`## Definition of done`.
*HEAD:* [`pyproject.toml`][pyproject] declares `"strawberry-graphql>=0.316.0"`, and
[`docs/builder/BUILD.md`][build] `## Floor verification` is the single canonical statement of the
version a floor run installs.
*Cause:* the floor bump, which no pass reconciled into this spec.
*How it was fixed, and why not with a newer number:* a spec that restates a floor is how the
number rots — this is the second spec in the archive to carry a stale `0.262.0`
([`spec-041`][spec-041]'s rationale records the same finding as its own F5). The spec now states
the **obligation** (the gate confirms `BaseView` importable at the package's declared floor,
read at gate time from [`pyproject.toml`][pyproject] and
[`docs/builder/BUILD.md`][build]) and names no version of its own. A Definition-of-done item is a
completion claim and gets no vintage licence, so the unsatisfiable `0.262.0` throwaway-venv
demand could not be left standing.

### F7 — three post-ship Python hardenings were absent from the divergence ledger

*Claimed:* "two narrow divergences" from the verbatim upstream borrow (the `isinstance(view,
type)` guard and `_get_payload`'s non-object-body bail), and "No other Python behavior differs".
*HEAD:* three, all in
`django_strawberry_framework/middleware/debug_toolbar.py` and all pinned by tests:

1. the `isinstance(view, type)` guard in `process_view` — unchanged since ship;
2. `_get_payload`'s **response-shape bails**, now wider than the non-object case —
   `django_strawberry_framework/middleware/debug_toolbar.py::_get_payload`
   #"except (json.JSONDecodeError, LookupError, UnicodeError):" also bails when a declared-JSON
   body cannot be decoded with its charset or parsed at all (commit `6fa696af`), pinned by
   `tests/middleware/test_debug_toolbar.py::test_malformed_json_body_gets_no_package_rewrite`
   (parametrized over `b"not json"` and `b"\xff"`);
3. the **`Content-Encoding` bail** in
   `django_strawberry_framework/middleware/debug_toolbar.py::DebugToolbarMiddleware._postprocess`,
   which returns a response carrying that header untouched, because appending the bridge script
   to a gzipped body — or re-encoding one as JSON — would corrupt it (commit `9c868016`), pinned by
   `tests/middleware/test_debug_toolbar.py::test_encoded_response_gets_no_package_mutation`
   (parametrized).
*Cause:* two post-ship hardening commits the spec never absorbed.
*The docstring carried the same understatement, and it was a separate write set.* The module
docstring enumerated (1) and (2) and closed "No other Python behavior differs", which understated
(3) exactly as the spec did; being a source-file sentence it could not be fixed in the custody
pass that found it. It was routed to the code cohort and discharged there: the docstring now names
all three by name, points at the template ledger without counting it, and carries no closed-world
closer — see the [Decision 6 change record](#decision-6--subclass-and-override-borrowed-as-is).

### F8 — the template carried two further divergence families

*Claimed:* `## Borrowing posture`'s template-port checklist recorded a **four-guard family**
(reviver preservation, safe membership guard, mandatory scrub before the null-handle bail,
best-effort per-panel DOM).
*HEAD:* six, in two further families:

- **Shadow-DOM handle resolution** (commit `312d4121`) —
  `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
  #"function getDjDebug()". debug-toolbar ≥7 defaults `USE_SHADOW_DOM=True`, so the bare
  `document.getElementById("djDebug")` the port inherited returned `null` and every DOM update
  silently stopped. Nav lookups moved onto the resolved handle.
- **Per-node null guards on the panel render** (commit `ac69acf5`) — every nested
  `querySelector` result (`panelTitle`, `heading`, `scroll`, `panelContent`, `subtitle`) is
  null-checked before assignment; the previous chained form threw a `TypeError` inside the
  patched `JSON.parse` and blanked the toolbar.

Both are pinned by
`tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence`.
*Cause:* two post-ship fix commits.
*Why they belong to the same rule rather than being new exceptions:* the guiding rule the
four-guard family already served — payload scrubbing is mandatory, DOM updates are best-effort —
is exactly what a `null` handle under a shadow root and an absent panel node both test. The
ledger grew; the rule did not change.

### F-minor — two smaller spec/tree disagreements

- *Claimed:* `## Out of scope` said "this card's tests use `django.test.Client` directly".
  *HEAD:* the live tier posts through the package's own
  `django_strawberry_framework.testing::TestClient`
  (`examples/fakeshop/test_query/test_debug_toolbar_api.py` #"TestClient(client=client).query(");
  the package tier drives `RequestFactory` and direct middleware calls. *Cause:*
  [`spec-043`][spec-043] shipped the client, and commit `4015442d` moved the tests onto it.
- *Claimed:* the ship-time `Status:` line and opener described a two-slice build.
  *HEAD:* four post-ship commits extended the shipped contract after the card closed. The
  `Status:` line is the completion source of truth
  ([`docs/builder/BUILD.md`][build]) and now says so. Checkbox state throughout the spec is
  untouched: unticked boxes on a shipped spec are this repo's closeout convention, which is the
  point [`spec-043`][spec-043] cites as "spec-042 Revision 8".

### M3 — the bridge guarded the shape of `data` but not of its `debugToolbar` value

Spec: [Borrowing posture][borrowing], the payload-shape guard;
[Edge cases and constraints][edge-cases], "A `debugToolbar` value the bridge cannot read".

*Claimed:* the template-port family was complete at six diverged forms, "every one of them
serving" the rule that payload scrubbing is mandatory and DOM updates are best-effort.
*HEAD (as shipped):* the entry guard tested `data` three ways and never tested the value under
the key; `Object.entries(toolbar.panels)` and `panel.title` were read unconditionally
(`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
#"Object.entries(toolbar.panels).forEach"), so a `null`, scalar, or `panels`-less
`debugToolbar` value — or a `null` panel entry — threw a `TypeError` out of the globally patched
`JSON.parse` / `Response.prototype.json` after the scrub had already run. The key was gone; the
caller's parse was broken. Upstream carries the identical hole
(`~/projects/strawberry-django-main/strawberry_django/templates/strawberry_django/debug_toolbar.html`
#"Object.entries(data.debugToolbar.panels).map("), so this is the borrow's flaw the divergence
family was created to fix, reached through a door the first six forms did not cover — not a port
regression.
*Cause:* the family grew by fixing each throw as it was found (Revisions 7 and 8, then the two
post-ship commits) and the value under the key was never one of the inputs that threw in front
of anyone. The independent code-verification cohort found it by reading, not by a failing test:
the asset has no executing test, so no row could have.
*Correction:* the spec states a seventh form, the payload-shape guard, and the asset carries it.
Exposure was dev-only and needed a foreign `debugToolbar` key, which is why the finding was
graded Medium rather than High — but the asset already hardened against `Object.create(null)` and
a shadowed `hasOwnProperty`, inputs at least as exotic, so the omission was an inconsistency with
the family's own rule rather than a scope line. Deferring it to a later card was rejected under
the no-defer-the-real-fix rule ([`AGENTS.md`][agents] rule 5): closing the cycle with a spec that
asserts a complete family over a known hole would have manufactured a third instance of the F8
defect this cycle exists to clear. The guard's shape and its rejected alternatives are in the
[Borrowing posture entry](#borrowing-posture--the-template-port) below.

## Decision entries

### Decision 1 — Spec filename and canonical naming

Spec: [Decision 1][d1].

**Alternatives rejected.** *Moved from the spec.*

- **`spec-042-debug_toolbar_middleware-0_0_14.md`.** The `_middleware` suffix adds length without
  disambiguation — no other card touches the debug toolbar, and the sibling debug card is named
  by its own distinct subject (response extensions), so `debug_toolbar` alone is unambiguous.
  Precedent favours the shorter slug (`channels_router`, `auth_mutations`, not
  `channels_asgi_router_module`).
- **`spec-042-django_debug_toolbar-0_0_14.md`.** The `django_` prefix restates the ecosystem
  every card lives in; the package's own module path (`middleware/debug_toolbar.py`) uses the
  short form.

### Decision 2 — Card-scope boundary

Spec: [Decision 2][d2].

**Alternatives rejected.** *Moved from the spec.*

- **Fold both debug cards into one spec.** Different upstreams (🍓-only vs ⚛️-only), different
  mechanisms (a Django HTTP middleware vs a Strawberry `SchemaExtension`), different module homes
  (`middleware/` vs `extensions/`), and the board deliberately tracks them as two cards with
  "distinct from" edges. A joint spec would re-litigate the board.
- **Add the fakeshop `DEBUG`-gated toolbar block now for dogfooding.** It drags a soft dependency
  into the example's runtime path and adds a settings branch the live acceptance suite never
  exercises (tests run `DEBUG=False`); dead weight until a deliberate dogfooding pass owns it.

**Justification, moved because it argues for the boundary rather than stating it.** The card body
pins the boundary itself ("Both mechanisms are useful and not mutually exclusive" on the sibling;
"developer experience" / "Single module + tests" on scope), and the [`START.md`][start] advice
("resist scope creep… don't quietly mix in while-I'm-here extras") applies verbatim.

**Change record — the fakeshop opt-in was brought forward (Revision 9 / [F4](#f4--fakeshop-ships-the-toolbar)).**
The decision scoped the example's settings opt-in OUT and deferred it to the fakeshop-activation
card, on the ground that wiring it "would make the example's `manage.py runserver` path require
an optional package the moment a developer flips `DEBUG`". The maintainer reversed that in commit
`4015442d`: fakeshop now ships the app, the middleware, `INTERNAL_IPS` and `debug_toolbar_urls()`.
**The claim this decision may no longer make:** that the example's runtime path stays free of
this soft dependency. **What survives unchanged:** the in-response `extensions["debug"]` surface
is still the sibling card's, the Channels/ASGI boundary still holds, and no new `Meta` or
settings key exists.
*Why the second rejected alternative above is recorded rather than deleted:* the reversal was the
maintainer's contract call, not a discovery that the reasoning was wrong. A later reader
proposing to un-wire fakeshop needs the argument that was weighed.

**Change record — the heading.** The decision's heading named "fakeshop settings opt-in" as one
of the four things staying out. It was rewritten to the two that still do, because a heading is
the one sentence a reader takes on trust without reading the body.

### Decision 3 — The symbol is `DebugToolbarMiddleware`

Spec: [Decision 3][d3].

**Alternatives rejected.** *Moved from the spec.*

- **A distinctly-ours class name (`DjangoStrawberryDebugToolbarMiddleware`,
  `GraphQLDebugToolbarMiddleware`).** The settings string already carries full provenance; a
  novel class name buys nothing a consumer sees (nobody imports the class) while breaking the
  ecosystem naming convention and making the migration diff noisier than one path segment.
- **Re-exporting from `middleware/__init__.py`.** It would force the `__init__.py` to import the
  guarded module — making `import django_strawberry_framework.middleware` itself raise on a
  toolbar-less machine and breaking whole-package walkers (the [`docs/TREE.md`][tree] renderer,
  coverage collection) for zero consumer benefit; the settings string is typed once either way.

**Derivation, moved because it does not change how the class is built.** The decision looks like
it contradicts [`spec-041`][spec-041] Decision 3's "distinctly-ours symbol name" posture and does
not, because the two surfaces have different identity mechanics: a router class is *imported by
name* in consumer code, so the name is the API; a Django middleware is *referenced by dotted
settings string*, so the module path is the distinctly-ours identity and the class name is a
Django-ecosystem convention (`SessionMiddleware`, `AuthenticationMiddleware`) consumers
pattern-match. Upstream made the same call for the same reason. The card's own definition of done
pre-pinned the name; the decision preserved it and supplied the reasoning.

### Decision 4 — Module, template, and test locations

Spec: [Decision 4][d4].

**Alternatives rejected.** *Moved from the spec.*

- **A top-level `middleware.py` module.** [`docs/TREE.md`][tree]'s planned rows commit to the
  subpackage; the sibling card similarly reserves `extensions/`, and the two debug surfaces
  landing as sibling subpackages keeps the package tree legible; and a top-level module would
  need the router's lazier guard shape to stay walker-safe (see Decision 5's rejected PEP 562
  alternative).
- **Serving the script from `static/` instead of a template.** The asset is injected server-side
  into an already-rendered HTML body by `response.write(...)` — a template rendered to a string
  is the mechanism upstream uses and the only one that needs no URL configuration, no
  `collectstatic` step, and no extra request; a static file would add all three.
- **Inlining the script as a Python string constant.** A ~45-line JS asset inside a Python module
  is unreviewable and unlintable as JS; the template file matches upstream (easing future
  diff-syncs against upstream fixes) and the app-dirs resolution costs nothing given the shipped
  `AppConfig`.

**Change record — the test location half ([F3](#f3--the-test-urlconf-module-testsmiddlewaredebug_toolbar_urlspy-never-existed) / [F4](#f4--fakeshop-ships-the-toolbar)).**
The decision's third paragraph placed *all* tests at `tests/middleware/test_debug_toolbar.py`,
mirroring the source subpackage. Half of that survives — the package tier still mirrors the
source subpackage and still owns the paths no live request reaches — but the toolbar-present
tests moved live. **The claim this decision may no longer make:** that
`tests/middleware/test_debug_toolbar.py` is the sole home. The module and template locations are
untouched.

### Decision 5 — Soft `django-debug-toolbar` dependency

Spec: [Decision 5][d5].

**Alternatives rejected.** *Moved from the spec.*

- **A hard dependency.** The toolbar is a dev-only tool by its own design (it disables itself
  outside `DEBUG` + `INTERNAL_IPS`); taxing every production install with it inverts its purpose.
  Upstream itself ships it as an extra, not a core dependency.
- **A `django-strawberry-framework[debug-toolbar]` extra (upstream's shape).** The DRF and
  channels precedents both rejected extras — an extra changes how consumers *install*, not
  whether the import needs guarding (an extra is advisory; nothing stops an extra-less install
  from listing the middleware), so it adds a second documented thing without removing any code.
  Three soft dependencies with one uniform no-extras contract beats two contracts.
- **The PEP 562 lazy-symbol shape (the `routers.py` pattern).** Rejected for this surface with
  the reasoning made explicit because the two shapes now coexist in the package: (a) the
  consumer's access path is Django's `import_string` on a settings string, which imports the
  module and immediately does `getattr` — the guard fires at the same startup moment either way,
  so laziness buys the consumer nothing; (b) the leaf module has no reason to be importable
  without its dependency — unlike `routers.py` (a top-level module walkers must traverse),
  nothing legitimate imports the leaf except the opt-in; (c) the lazy shape costs a builder
  function, a module-global cache, a `__getattr__`, and a `# noqa: F822` — real complexity the
  router needed and this module does not; and (d) the card's definition of done pre-pinned the
  import-time wording. **The decision rule this leaves behind is normative and stayed in the
  spec:** a top-level module lazies; a dedicated opt-in leaf guards at import.
- **Guarding inside `DebugToolbarMiddleware.__init__` (a stub class).** The class *body* needs
  the import (it subclasses the stock middleware), so a stub would lie about identity — the exact
  rejection [`spec-041`][spec-041] recorded for the router stub, and here the two-phase failure
  would be worse: Django imports middleware at startup, so the error would move from a clean
  startup `ImportError` to a first-request failure.

**Derivation of the `>=7.0.0` floor, moved because it argues for a number the spec simply
states.** Upstream declares `django-debug-toolbar>=6.0.0`. Per
[PyPI metadata][debug-toolbar-pypi], `6.0.0`
(2025-07-25) classifies Django 4.2-5.2 only, while `7.0.0` is the first checked release carrying
the `Framework :: Django :: 6.0` classifier — with `django>=5.2` and `python>=3.10`, matching the
package's own floors. The [`spec-041`][spec-041] single-floor rule is what makes the higher floor
mandatory rather than tidy: the install hint is the error message a deploying consumer follows,
so it must not guide a Django 6.0 user into an unsupported toolbar. The floor's Django coverage
therefore reaches 6.0 and stops short of the 6.1 [`pyproject.toml`][pyproject] also advertises —
a gap recorded deliberately, not an oversight.

**Change record — Revision 6: the second wiring gate.** As drafted, the decision's error model
was pure `ImportError`. Revision 6 traced the `debug_toolbar.middleware` import chain at `7.0.0`
(through `debug_toolbar.toolbar`, `debug_toolbar.store`, then
`from debug_toolbar.models import HistoryEntry`) and found a third failure mode the model did not
cover: a package that is installed while `"debug_toolbar"` is absent from `INSTALLED_APPS` fails
with Django's `HistoryEntry` app-label `RuntimeError`, which never names the missing app and so
is not self-actionable. The `apps.is_installed("debug_toolbar")` gate raising
`ImproperlyConfigured` from `_DEBUG_TOOLBAR_APP_HINT` was added, with Test 11b to pin it. This is
the card's one deliberate step outside the pure-`ImportError` model, and the reason it is not an
inconsistency: an `INSTALLED_APPS` omission is a settings error and `ImproperlyConfigured` is
Django's idiom for it, while the "top-level package only" scope still governs
`require_debug_toolbar()`'s *import* guard — a separate concern from the *wiring* gate.

**Change record — the three-places rule names the gated trio, not the population.** The rule
was written as "the three places that must agree" — the dev-group specifier,
`_DEBUG_TOOLBAR_INSTALL_HINT`, and the re-typed test literal — and the module comment above the
hint repeated it as a closed count. Sweeping the tree for the specifier found the trio plus the
glossary body and the consumer README, none of which anything compares to the others — and then
a looser needle found the changelog's dependency-floor line as well, which the first sweep missed
because it spells the name and the specifier with a backtick between them. That is the whole
lesson twice over: the count was a self-falsifying instrument (right when written, wrong the day
a doc restated the floor), and any replacement count is bounded by the spelling of the needle
that produced it. So the rule now names the gated trio **by mechanism** and tells a floor bump to
sweep the tree rather than trust an enumeration — and names the sweep's own instrument, because
the second half of the lesson is wasted otherwise: the sweep is for the package **name** with each
hit read, never for the `>=` specifier, which is bounded by one spelling and demonstrably misses
the changelog's. A correction that fixes the count and leaves the needle behind reproduces the
defect one level down, in the instruction the bump actually follows. And
the trio was not fully gated either: the package test matched the hint against the literal, but
nothing compared the `pyproject.toml` row to either, so the specifier could move alone. Test 12a
closes that pair with the same regex-over-`pyproject.toml` idiom the suite already uses for the
Channels and Strawberry floors. **Rejected:** correcting the comment to the measured number (the
same instrument with a bigger number, and a number the next needle would have moved again);
moving the literal into a `utils/imports.py` floor constant
interpolated into the hint, the router's shape (the DRY end-state, but `utils/imports.py` and the
governance test module were outside the code cohort's write set, and the hint literal was already
single-sited in the module — the relocation is a refinement whose trigger is a fourth soft
dependency or the DRF hint gaining the same row, recorded so it is not re-raised as duplication);
editing the two doc sites (fenced out of the cycle, and correct today — the defect is that they
are ungated, which a sweep instruction addresses and an edit does not). **The claim this decision
may no longer make:** that the three sites are everywhere the floor is written.

### Decision 6 — Subclass-and-override, borrowed as-is

Spec: [Decision 6][d6].

**Alternatives rejected.** *Moved from the spec.*

- **A from-scratch Django middleware reading `connection.queries`.** Rejected by the card's own
  posture line — that mechanism (lower-fidelity, response-side) is the *sibling card's* design
  space, and re-implementing panel rendering would break every toolbar panel except SQL while
  doubling the maintenance surface.
- **Chaining `super().process_view(...)`.** The stock
  `debug_toolbar.middleware.DebugToolbarMiddleware` defines **no** `process_view` — it is a
  `__call__` / `__acall__`-style middleware in every release across the toolbar's `3.8`-`6.x`
  line (verified against the on-disk toolbar sources), so there is no stock behaviour to preserve
  and nothing for `super().process_view(...)` to reach but the base-class no-op. Upstream's
  override therefore does not chain, and neither does this one; byte-borrowing that choice keeps
  the module diffable against its reference.
- **Injecting into every JSON response (dropping the `_is_graphiql` gate).** The gate scopes
  injection to responses from a Strawberry Django view, so a JSON response from some *other* view
  (a DRF endpoint, an admin AJAX call) never grows a `debugToolbar` key. It does **not** narrow
  injection to the IDE — the gate's job is view-scoping, not IDE-detection. Dropping it entirely
  would leak the key onto unrelated JSON views, which is why it stays even though it is not an
  IDE filter. (The honest statement of what the gate does and does not do is normative and stayed
  in the spec's `## User-facing API`.)

**Change record — Revision 4: what `super()._postprocess(...)` actually does.** The decision
originally described the chain as "call `super()` first" without saying what the stock method
does in that call. Revision 4, source-verified against the `7.0.0` tag, made the order explicit —
per-panel stats and server timing, then an **unconditional** render-and-store for every processed
response ("Always render the toolbar for the history panel"), then headers, then the conditional
HTML handle. That mechanism turned out to be load-bearing three times over: it is why a JSON
operation gets a history row `render_panel` can later serve, why a missing URLconf's
`NoReverseMatch` fires on JSON requests too, and why every tagged JSON operation pays a full
server-side toolbar render in dev. Those three consequences are instructions to a builder and
stayed in the spec.

**Change record — the non-mapping bail became a family ([F7](#f7--three-post-ship-python-hardenings-were-absent-from-the-divergence-ledger)).**
Revision 5 added `_get_payload`'s non-object-body bail as the module's *second* documented
divergence, reasoning that "a valid single GraphQL response is always a JSON object, but a
malformed test view or a future batch-response shape could decode to a list or scalar". Two
post-ship commits generalised the same rule: the bail now also covers a body that cannot be
decoded with its declared charset or parsed as JSON at all (`6fa696af`), and a sibling guard
returns an encoded body untouched (`9c868016`). **The claim this decision may no longer make:**
that the Python middleware carries exactly two divergences and that "no other Python behavior
differs". The module docstring carried the same two-count and the same closing sentence after the
spec had been corrected; it now enumerates the three Python divergences by name and points at
the spec's template ledger without counting it, and the closer is gone rather than renumbered —
a closed-world sentence over a population nothing gates is the shape that had already been false
once.

### Decision 7 — Strawberry-view detection against `BaseView`

Spec: [Decision 7][d7].

**Alternatives rejected.** *Moved from the spec.*

- **Ship a package `DjangoGraphQLView` and detect that.** A view class introduced *so that a
  middleware can `issubclass` it* is surface for surface's sake — it would narrow detection to
  consumers who adopt the new view (breaking every existing `GraphQLView` consumer, including
  fakeshop as it was then wired) and create a public API this card had no other reason to ship.
  The escape route was named in the same breath: if a future card ships a package view for its
  own reasons, it subclasses `BaseView` and detection keeps working unchanged.
- **Path-based detection (`request.path == settings.GRAPHQL_PATH`).** It invents the settings key
  Decision 2 forbids, breaks multi-endpoint schemas, and diverges from upstream's proven
  mechanism for zero gain.
- **Duck-typed detection (`hasattr(view, "schema")`).** Looser than `issubclass` with no
  compensating benefit — any consumer view exposing a `schema` attribute would be silently
  tagged, and the upstream-parity claim ("the same `issubclass` check") would be false.

**Derivation, moved because it records how a card hedge was resolved rather than what the code
does.** The card hedged the detection target: "Our equivalent uses the same `issubclass` check
against whichever view class the package settles on (working name `DjangoGraphQLView`; pinned
during implementation)." Revision 1 resolved the hedge against a repo fact — at authoring time
the package shipped no view class and fakeshop wired Strawberry's `GraphQLView` directly — and
chose the engine-owned target, which is also upstream's. It was recorded under the
[`docs/SPECS/NEXT.md`][next] prefer-the-card rule as a hedge resolving in the direction the
card's own "same `issubclass` check" sentence already pointed, not as a card conflict.

**Change record — the rejected alternative's escape route was taken, and the hedge closed
([F5](#f5--decision-7s-premise-the-package-ships-no-view-class-is-false-and-the-detection-still-works)).**
[`spec-046`][spec-046] shipped `django_strawberry_framework/views.py::DjangoGraphQLView` for
transport-security reasons of its own, and fakeshop now mounts it. Because that view subclasses
strawberry's `GraphQLView`, which subclasses `BaseView`, the `issubclass` line needed **no**
update — the outcome the rejected alternative predicted. **The claim this decision may no longer
make:** that the package ships no view class. **What the decision still decides, unchanged:** the
detection target is engine-owned `BaseView`, not a package-owned class; the rejected alternative
stays rejected, because ship-a-view-to-detect-it remains the wrong reason to ship a view, and
`spec-046` did not ship one for that reason.

**Change record — the heading.** The heading ended "resolving the card's `DjangoGraphQLView`
hedge". With a real `DjangoGraphQLView` in the package that reads as a contradiction rather than
provenance, and [`AGENTS.md`][agents] keeps process provenance out of standing prose in any case;
the clause moved here.

### Decision 8 — The introspection-query skip is preserved, verbatim

Spec: [Decision 8][d8].

**Alternatives rejected.** *Moved from the spec.*

- **Parsing the query text for `__schema` selections.** A GraphQL parse per response on the dev
  hot path, to improve a heuristic whose false positives are cosmetic. Upstream's name check is
  O(1) and proven.
- **Making the skip configurable.** A knob on a dev tool's history hygiene is configuration
  surface nobody asked for; upstream ships none.

**Derivation, moved.** The skip is deliberately name-based rather than content-based, so a
consumer who issues an introspection query under a different `operationName` gets a payload
(harmless) and a consumer who names a data query `IntrospectionQuery` loses its payload (their
choice). Matching upstream exactly here mattered more than closing that cosmetic gap, because the
skip's contract has to be identical for the one-settings-string migration to be
behavior-preserving.

### Decision 9 — Test strategy

Spec: [Decision 9][d9].

**Alternatives rejected.** *Moved from the spec, and two of the four are now historical — see the
change record below.*

- **A live `examples/fakeshop/test_query/` placement with the same settings overrides.** Rejected
  *at the time* because the live suite's charter is consumer-visible GraphQL behaviour through
  the example **as shipped**, and its coverage rule reserves the fall-back for code genuinely
  unreachable from a live request — which these lines were until the example's settings opted in.
  A test that must rewrite `INSTALLED_APPS` / `MIDDLEWARE` before the surface exists asserts
  package-internal wiring, not the example's shipped behaviour. The decision named its own
  reversal condition: "when a future card opts fakeshop's settings into the toolbar for real, the
  covering test moves live and the package stand-in is deleted (the documented promotion rule)."
- **Wiring `debug_toolbar` permanently into fakeshop settings for the tests' benefit.** Rejected
  *at the time* under Decision 2, and additionally because it would put the toolbar's middleware
  into every *other* suite request's path (inert but present) — a blanket change to the whole
  suite's request pipeline for one test file's convenience.
- **Unit-testing the overrides against synthetic `HttpRequest` / `HttpResponse` objects only.**
  Still rejected, and the reason is unchanged: the module exists to compose with the *real*
  toolbar lifecycle (`super()._postprocess` behaviour, `toolbar.request_id` assignment, panel
  enablement) and the *real* Strawberry view (`view_class` through a decorator) — precisely the
  seams synthetic objects would fake. The [`START.md`][start] "coverage is a feature" posture: if
  the composition is wrong, only real traffic notices. What survives of this rejection in the
  shipped tree is narrow and deliberate: the package tier drives fake toolbar / middleware
  objects **only** for branches the real lifecycle cannot expose.
- **Uninstall-based absence testing (a separate no-toolbar CI job).** Still rejected: the DRF and
  channels precedents both chose simulation (one env, one `uv run pytest` gate, no matrix).

**Change record — Revision 2: the fixture's `DEBUG` posture.** The first draft's fixture did not
re-enable `DEBUG`. The maintainer review caught that pytest-django defaults `django_debug_mode`
to `False` and forces `settings.DEBUG = False` for the whole suite, which switches off both the
toolbar's own gate and the `DEBUG`-gated `debug_toolbar_urls()`. The `override_settings(DEBUG=True)`
+ always-true `SHOW_TOOLBAR_CALLBACK` pair, and the cache hygiene beside it, all descend from
that finding. The reasoning is an instruction to anyone writing a toolbar fixture and stayed in
the spec; what moved is only that a review round found it.

**Change record — Revision 5: the absence mechanism was wrong and was verified empirically.** The
draft copied the router/DRF `builtins.__import__` block. That block is a **no-op** for this
guard: `require_debug_toolbar()` is a
[`require_optional_module`][glossary-require-optional-module] wrapper, i.e. an
`importlib.import_module("debug_toolbar")` call, and `importlib` routes through
`importlib._bootstrap._gcd_import` without consulting `builtins.__import__`. Under the block the
guard re-imports the still-installed toolbar and any raise comes from a later hintless
statement-import — so Tests 10 and 12 would have passed for the wrong reason. Corrected to the
`sys.modules["debug_toolbar"] = None` sentinel everywhere the mechanism is prescribed. This
supersedes Revision 3's reasoning that "the leaf always reaches `require_debug_toolbar()` under
the block". **The claim this decision may no longer make:** that the three soft-dependency
absence fixtures share one absence mechanism.

**Change record — the whole placement premise was reversed (Revision 9 / [F3](#f3--the-test-urlconf-module-testsmiddlewaredebug_toolbar_urlspy-never-existed) / [F4](#f4--fakeshop-ships-the-toolbar)).**
The decision placed every test package-internal *because* fakeshop shipped no toolbar. Commit
`4015442d` wired fakeshop, which fired the decision's own promotion rule: the toolbar-present
tests moved to `examples/fakeshop/test_query/test_debug_toolbar_api.py`, driving fakeshop's real
request path with only a `DEBUG=True` override and a `config.urls` reload inside it, and the test
URLconf module was deleted because fakeshop's own `config.urls` supplies the `djdt` routes. What
survived the move intact, and is worth naming because it looks like fixture detail: the
`DEBUG=True` override, the always-true callback, the `show_toolbar_func_or_path.cache_clear()`
and the `DebugToolbar._panel_classes` / `_urlpatterns` save-clear-restore are all still
mandatory — the reasons for them are properties of pytest-django and of debug-toolbar's process
caches, not of the placement. **The claims this decision may no longer make:** that no live
request can reach a `middleware/debug_toolbar.py` line, that fakeshop's shipped settings carry no
toolbar, and that a test URLconf module exists.

**Change record — the schema-reload obligation narrowed with the move.** The decision required
the toolbar-present fixture to call the single-sited
`examples/fakeshop/schema_reload.py` helper first, on setup, because the tests executed the
aggregate fakeshop schema **from inside the package tree** — the tree whose files call
`registry.clear()`. Now that those tests live in the live tier, they inherit the live suite's own
project-schema fixture rather than carrying a package-tier obligation. The underlying
[schema reload discipline][glossary-schema-reload-discipline] is unchanged; only which tier owes
it moved.

### Decision 10 — Version bumps are owned by the joint `0.0.14` cut

Spec: [Decision 10][d10].

**Alternatives rejected.** *Moved from the spec.*

- **Bump to `0.0.14` in Slice 2.** Two siblings still shipped into `0.0.14`; a per-card bump
  races the joint cut and would be reconciled twice over.
- **Defer the lockfile regeneration to the joint cut too.** Slice 1's tests import
  `debug_toolbar`; a dev-dependency without its lock entry breaks the reproducible-env contract
  the moment CI runs `uv sync`.

**Justification, moved.** Per [`docs/SPECS/NEXT.md`][next] Step 3 / Step 6, when multiple cards
target one patch version the bump belongs to the joint cut, not any individual card's spec. Three
non-Done cards remained at `0.0.14` when this one flipped; this card was not the last.

## Non-decision entries

### Borrowing posture — the template port

Spec: [Borrowing posture][borrowing].

**What stayed in the spec, and why it is not deliberation.** The template-port checklist is a
live contract: `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence`
asserts each invariant and each diverged form mechanically. It was graded clause by clause rather
than moved as a block.

**Explicitly-do-not-borrow items, kept in the spec.** All four (the hard `debug_toolbar` import,
the plural `middlewares/` package name, upstream's `>=6.0.0` floor, the
`typing_extensions.override` decorator) state what the package must **not** do and are normative.

**Change record — the divergence family grew twice.** Revision 7 hardened two upstream bugs that
are unsafe once the hook is a *global* patch (a dropped `reviver` argument, a
`data.hasOwnProperty(...)` guard that throws for null-prototype objects) and added the
`djDebug === null` crash guard. Revision 8 found that the Revision-7 guard returned *before*
`delete data.debugToolbar`, so a page whose toolbar DOM did not render leaked the server-only key
back to GraphiQL, and that the per-panel DOM writes assumed every payload panel had a matching
node. Both were fixed under one rule — **payload scrubbing is mandatory and DOM updates are
best-effort** — which is the rule the two post-ship families in
[F8](#f8--the-template-carried-two-further-divergence-families) also serve. The rule stayed in the
spec; the chronology is here.

**Change record — the family grew a third time: the payload-shape guard
([M3](#m3--the-bridge-guarded-the-shape-of-data-but-not-of-its-debugtoolbar-value)).** Every
earlier form guarded either `data` or a DOM node; none guarded the value under the
`debugToolbar` key, and upstream reads it unconditionally. The guard is one record predicate —
`isRecord(value)`, `value !== null && typeof value === "object"`, defined once in the IIFE —
applied at every site that reads keys: the entry guard on `data` (whose `hasOwnProperty.call`
clause stays), the captured `toolbar`, `toolbar.panels`, and each `panel` in the loop. It is
written against the answer the DOM update needs ("can keys be read from this value") rather than
against spellings of bad input, which is the [`docs/builder/BUILD.md`][build]
`### Fail-open shapes` rule: a guard against one spelling leaves the next spelling flowing into
the permit branch. The scrub is unconditional and precedes the guard, so the family's rule —
scrubbing mandatory, DOM best-effort — is preserved exactly, not relaxed. **Rejected:** a
`try` / `catch` around the DOM block (a swallowed exception converts "the check blew up" into
"the check passed" and would hide a real toolbar-DOM bug behind a silent no-op — the bare
`except` shape); an enumeration such as `toolbar === null || typeof toolbar === "string" ||
!("panels" in toolbar)` (three spellings, and the fourth throws); guarding `requestId` as well
(`setAttribute` coerces a non-string value and never throws for one, so a missing `requestId`
degrades to the stock toolbar's own panel-miss fallback rather than a crash — kept
upstream-verbatim and recorded here so it is not re-raised); and the code-verification cohort's
L2 observation that `if (panel.subtitle)` never clears a subtitle that became empty, kept
upstream-verbatim on its own recommendation because the change would diverge from the borrow for
no dev-visible gain. Pinning moved with the guard: the template-port test became one row per
predicate, where the single-test shape had scored exactly one failing node id for any form and
one for all of them together, so the suite could not distinguish a dropped guard from a dropped
family.

**Change record — what the row-per-predicate table is allowed to claim about itself.** The split
first shipped under a claim about *quantity* — every form pinned by at least two rows, one of
them an ordering or absence predicate — and that claim was false of the table that landed: a
majority of the diverged forms were pinned by presence checks alone, and the preserved invariants
sit at one row each by construction. It is the defect this cycle exists to retire — the
[three-places rule's own count](#decision-5--soft-django-debug-toolbar-dependency), the module
docstring's closed-world closer — published by the pass that retired them. The answer was not a corrected number but the rows the claim implied: every
mutation in the record restores *upstream's* spelling, and a presence row cannot see a revert
that restores upstream's shape alongside the port's, so each diverged form gained a row asserting
the upstream spelling it replaced is absent. The claim the spec now makes is **per kind and
carries no count** — a form diverging by spelling carries both halves, a form diverging by
position carries the index, adjacency, nesting and return-count rows (the borrow spells the same
statement, so there is no replaced spelling to assert absent), preserved invariants carry the row
for the write they keep — together with what would falsify it. The kind split is not a hedge: the
mandatory scrub is the positional case, and demanding an absence row of it would demand a needle
that cannot exist. **The measured facts that belong with it** are below, all reusable beyond this
asset (no count: a later pass that adds one should not have to fix a numeral to do it):

- **An absence row whose needle the borrow never spells is inert, and reads exactly like a
  working row.** The row guarding against a `document`-level nav lookup had been written against
  `document.getElementById(...)` as one token; upstream wraps that call across three source
  lines, so the needle occurred **zero** times in the thing it guarded against and could never
  have caught the verbatim paste it named. Tightening it to the fragment upstream actually
  carries is what made it fire. Every absence needle in the table was afterwards counted in both
  assets, occurrences rather than matching lines.
- **"Unconditional" is a property of the answer, not of a spelling, and index comparisons cannot
  see it.** Wrapping a condition around the scrub leaves every ordering row matching, which is
  why the adjacency, own-statement and non-nesting rows exist; but those three are themselves
  three spellings, and an early bail placed *above* the capture reintroduces exactly the leak
  Revision 8 closed while failing none of them. The property that subsumes all three is that
  **nothing returns between the entry guard and the scrub**, and that is what the spec's test
  plan asks for — the same `### Fail-open shapes` lesson the payload-shape guard itself was
  written under, arriving a second time in the test table rather than in the asset. It is also
  why that answer is measured from two anchors: a span opening at the entry guard's own return
  slides down with a bail inserted above it and reads clean, so the second row counts from the
  function opener instead.
- **A rename in the guarded file can narrow an absence needle's reach without making it inert,
  and the row still reads green.** The row asserting upstream's value-returning panel loop is
  absent was needled on that loop's whole head, binding included, and a rename of the port's key
  variable narrowed it to the verbatim paste alone: it stopped matching a revert that restores
  upstream's `.map` while keeping the port's binding, so that partial revert failed one presence
  row where it had failed the absence half too. The needle still occurred in upstream's asset, so
  the row was not inert by the falsifier the spec states, and the verbatim paste it was written to
  catch still failed it; what had moved was its reach over hand edits. It now carries the fragment
  that names only the divergence, and that same partial revert fails it again. The lesson
  generalizes past this row: an absence needle is
  coupled to the port's own spelling wherever it quotes more of the line than the divergence
  itself, so a rename in the port owes a re-count of every absence needle that spans it, and the
  narrower needle — the fragment that names only the divergence — is the one that survives.
- **An absence needle that contains another absence needle in the same table can never fail
  alone, whatever it is counted in.** The same value-returning-panel-loop row was needled on
  `` `.map(([id, panel])` ``, which contained the sibling row's `` `([id, panel])` `` outright, so
  any text failing the longer needle failed the shorter one too and the row added no failing
  node id the table did not already have. Inertness (a needle the borrow never spells) and
  subsumption (a needle another row's needle implies) are different defects with the same
  symptom — a row that reads green forever — and the table is checked for both by different
  instruments: occurrence counts in both assets for the first, pairwise containment across the
  table's own needles for the second. The row now carries `` `.panels).map(` `` — one occurrence
  upstream, none in the port — no absence needle in the table contains another, and the row fails
  on its own: the partial revert that failed one row under the old needle fails two under this
  one, and a value-returning call on the panels map introduced above an otherwise intact port loop
  fails that row alone. The rule is stated for the next editor in the table's own comment: an
  absence needle must occur in the borrow and in no sibling absence needle.

**Change record — the panel key reaches a selector, and that is the best-effort per-panel form,
not an eighth.** After the payload-shape guard landed, one door remained: the loop interpolates
each `panels` key into `#${id}` and `#djdt-${id}` selectors, so a key that is not a valid CSS
identifier raises a `DOMException` out of the patched globals — the failure mode the whole family
exists to prevent, reached by a foreign payload that has already passed every record check. No
payload this package produces can reach it (the middleware keys `panels` by each panel's own
class-derived `panel_id`), which is why it was found by reading rather than by a test, and which
is the same reachability class as the payload-shape hole itself. **Rejected: leaving it as
documented behaviour** — scoping the contract to "we crash on a payload key we cannot parse"
documents a defect as a promise, and the family's rule ("payload scrubbing is mandatory, DOM
updates are best-effort") already promises the opposite for a panel whose node is absent.
**Rejected: recording it as an eighth diverged form** — an id that cannot be *resolved* and a
node that cannot be *found* are one promise, so the guard completes the best-effort per-panel
form and the family's ledger does not grow; a form count that grows for a clause inside an
existing rule is how an enumeration stops describing anything. **Rejected: a `try` / `catch`
around the lookup** (the bare-`except` shape, already rejected above) and **an enumeration of
invalid-identifier spellings** (the guard-the-spelling shape, rejected above for the same
reason): the contract is stated as an answer — the key reaches `querySelector` only through a
form the selector parser always accepts — so the escape makes the selector parseable for every
key but the empty one, whose escape names no identifier and is therefore skipped outright, and
the existing absent-node skip does the rest.

**That last distinction is the one place the guard is not simply "escape it", and it is worth
naming because the obvious prediction was wrong.** The contract was first written expecting the
escape to make the *lookup* total, leaving the existing `content === null` / `nav !== null` skips
to absorb whatever did not resolve. What the domain actually admits is a total **answer**:
`CSS.escape` is defined for every code point and returns a valid identifier for every non-empty
input, and its single non-total case is the empty string, which escapes to the empty identifier —
a `#` with nothing after it, which is not a selector at all rather than a selector that matches
nothing. So the escape covers every key but one and an explicit skip covers that one, and the two
together close the domain. A total lookup and a total answer are not the same property, and only
the second is what [`docs/builder/BUILD.md`][build] `### Fail-open shapes` asks for.

**Landed shape: one escape where the key enters the loop body, not one wrapper per selector.**
The key is escaped once, at the point it is bound, and both `#…` interpolations then read the
escaped value. This was preferred over wrapping each of the two `querySelector` calls for a reason
that is not taste: the two selector expressions stay byte-identical, so the template-port row
pinning the nav lookup's scoping to the resolved handle keeps its needle, and no row already in
the table is silently re-needled by the fix. It also means the property the table can pin is
"asked once, at the key's entry" — the same single-definition shape `isRecord` has.

**Rejected: guarding the escape itself.** `CSS.escape` is the only DOM API in the asset the borrow
does not use, so "what if it is missing or shadowed" is the obvious next question and the answer is
recorded here rather than left to be re-raised. It is not guarded, on three grounds. It cannot be
absent on a page that runs the toolbar: it predates every other API the asset and the stock
toolbar's own scripts already require, so a browser lacking it cannot render the DOM this function
updates. Its failure mode is a different risk class from the ones this family guards — a missing
global breaks the first panel of every update deterministically, in a `DEBUG`-gated developer tool,
where a hostile payload key breaks one page's parse latently. And the guard would itself be the
fail-open shape: a `typeof CSS !== "undefined" ? CSS.escape(key) : key` fallback converts "cannot
tell whether the escape is available" into "let the raw key through", which is exactly the hole
this change closes.

**Change record — Revision 4: the port is byte-identical, not adapted.** The paragraph originally
implied template tags needed adapting. Source-verification against the upstream asset found none
at all — no `{% load %}`, no `{% static %}`, no `{% url %}`, and no header comment — so the claim
was corrected to a byte-identical copy plus the documented divergences. The only renamed path is
the `render_to_string(...)` argument, which lives in the middleware rather than the asset.

### Risks and open questions

Spec: [Risks and open questions][risks].

**The preferred-answer / fallback deliberation, moved.** Each risk the spec carried was recorded
with a preferred posture and a fallback. The constraints themselves stay in the spec; the
weighing is here.

- **`_postprocess` is a private-underscore method.** *Preferred:* accept the coupling — upstream
  carries the identical override (decorated `@override`, so upstream CI notices a rename), the
  archived `django-graphiql-debug-toolbar` did too, and the mechanism has been stable across the
  toolbar's 4.x → 7.x line. *Fallback:* if a toolbar release breaks the hook, the gate that
  catches it (the suite under a refreshed lockfile) also scopes the repair — worst case the floor
  gains a temporary ceiling with a follow-on card.
- **The `7.0.0` floor was metadata-grounded, not suite-verified, at authoring time.**
  *Preferred:* `7.0.0` holds and all naming sites ship with it. *Fallback:* the gate moves all
  three sites together — the dev-group specifier, `_DEBUG_TOOLBAR_INSTALL_HINT`, and the re-typed
  test literal. The floor shipped as preferred; the three-places rule is normative and stayed in
  the spec.
- **App-registry churn from per-test `INSTALLED_APPS` overrides.** *Preferred:* the fixture is
  test-scoped, the suite's existing registry-sensitive files prove the pattern, and any surfaced
  flake is fixed at source, never by weakening the suite's `-W error` posture. *Fallback:*
  promote the overrides to a module-scoped fixture with explicit teardown ordering. **This risk
  is now largely historical:** fakeshop ships the app, so the live tier overrides `DEBUG` only.
- **Schema-registry order-dependence on a shared worker.** *Preferred:* the fixture's
  setup-time whole-project reload — order-independence by reconstruction. *Fallback:* none
  anticipated; a surfaced flake in this class is fixed in the shared helper, at source. Also
  narrowed by the move, per Decision 9's last change record.
- **The async path ships unverified.** *Preferred for `0.0.14`:* ship sync-verified with the
  glossary body claiming exactly that; async verification rides whichever card first gives the
  suite an async request vehicle, with [`spec-043`][spec-043]'s `AsyncTestClient` the natural
  owner. *Fallback:* a dedicated async smoke test is a small follow-on, not a redesign. The
  handoff is live: [`spec-043`][spec-043] records it as a received deferral in its own
  out-of-scope list.
- **The card's view-detection hedge.** Recorded as a risk at authoring time and now closed —
  see [Decision 7](#decision-7--strawberry-view-detection-against-baseview)'s change record and
  [F5](#f5--decision-7s-premise-the-package-ships-no-view-class-is-false-and-the-detection-still-works).
  It closed in the direction the hedge itself pointed, with no code change.
- **The `BaseView`-at-the-floor gate.** *Preferred:* present (the class predates the package's
  floor by a wide margin). *Fallback:* bump the project's Strawberry floor. The spec named a
  version for this gate, which is how the number rotted —
  see [F6](#f6--the-strawberry-floor-the-spec-named-is-stale).

## The `0.0.14` sibling cards named in this pair

The spec names three sibling cards by board id — 043, 044 and 062. The first two shipped and read
`DONE-` in the spec; the fakeshop-activation card is still open and reads with its milestone
prefix. Those are lifecycle prefixes rather than renumbers, so they are not a sweepable numeral
population. The renumberable population in this pair is the `spec-042` stem itself, which appears
in both files and in the sibling specs and rationales that cite this card.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[pyproject]: ../../../pyproject.toml
[start]: ../../../START.md

<!-- docs/ -->
[glossary-require-optional-module]: ../../GLOSSARY.md#require_optional_module
[glossary-schema-reload-discipline]: ../../GLOSSARY.md#schema-reload-discipline
[tree]: ../../TREE.md

<!-- docs/SPECS/ -->
[borrowing]: ../spec-042-debug_toolbar-0_0_14.md#borrowing-posture
[d1]: ../spec-042-debug_toolbar-0_0_14.md#decision-1--spec-filename-and-canonical-naming
[d10]: ../spec-042-debug_toolbar-0_0_14.md#decision-10--version-bumps-are-owned-by-the-joint-0014-cut
[d2]: ../spec-042-debug_toolbar-0_0_14.md#decision-2--card-scope-boundary-the-server-side-toolbar-integration-ships-the-in-response-surface-and-async-verification-stay-out
[d3]: ../spec-042-debug_toolbar-0_0_14.md#decision-3--the-symbol-is-debugtoolbarmiddleware--same-class-name-distinctly-ours-dotted-path
[d4]: ../spec-042-debug_toolbar-0_0_14.md#decision-4--module-template-and-test-locations-a-middleware-subpackage-an-in-package-template-asset-testsmiddleware
[d5]: ../spec-042-debug_toolbar-0_0_14.md#decision-5--soft-django-debug-toolbar-dependency-an-import-time-require_debug_toolbar-guard-the-rest_framework-shape
[d6]: ../spec-042-debug_toolbar-0_0_14.md#decision-6--subclass-and-override-borrowed-as-is-process_view--_postprocess-_get_payload-_html_types
[d7]: ../spec-042-debug_toolbar-0_0_14.md#decision-7--strawberry-view-detection-issubclass-against-strawberrydjangoviewsbaseview-engine-owned
[d8]: ../spec-042-debug_toolbar-0_0_14.md#decision-8--the-introspection-query-skip-is-preserved-verbatim
[d9]: ../spec-042-debug_toolbar-0_0_14.md#decision-9--test-strategy-live-tier-tests-through-fakeshops-shipped-toolbar-package-tests-for-the-paths-no-live-request-reaches-eviction-simulated-absence
[edge-cases]: ../spec-042-debug_toolbar-0_0_14.md#edge-cases-and-constraints
[next]: ../NEXT.md
[risks]: ../spec-042-debug_toolbar-0_0_14.md#risks-and-open-questions
[spec-041]: ../spec-041-channels_router-0_0_14.md
[spec-042]: ../spec-042-debug_toolbar-0_0_14.md
[spec-043]: ../spec-043-test_client-0_0_14.md
[spec-046]: ../spec-046-transport_security-0_0_14.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[debug-toolbar-pypi]: https://pypi.org/pypi/django-debug-toolbar/json
