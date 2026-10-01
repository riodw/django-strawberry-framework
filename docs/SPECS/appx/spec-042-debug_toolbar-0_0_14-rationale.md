# Rationale: spec-042 — Debug-toolbar middleware (deliberation and rejected alternatives)

Deliberative companion to [`spec-042-debug_toolbar-0_0_14.md`][spec-042]. The spec is the
contract; this file holds the alternatives each decision rejected and why each lost, and the
derivations that do not change how a decision is implemented.

One entry per spec decision, named by the decision's own heading and linked to its anchor, so a
citation such as "Decision 9's rejected alternatives" resolves to exactly one place. The two spec
sections that carry deliberation without being numbered decisions — `## Borrowing posture` and
`## Risks and open questions` — get their own entries under `## Non-decision entries`. A reader
looking for what the package *does* wants the spec, not this file.

## Decision entries

### Decision 1 — Spec filename and canonical naming

Spec: [Decision 1][d1].

**Alternatives rejected.**

- **`spec-042-debug_toolbar_middleware-0_0_14.md`.** The `_middleware` suffix adds length without
  disambiguation — no other card touches the debug toolbar, and the sibling debug card is named
  by its own distinct subject (response extensions), so `debug_toolbar` alone is unambiguous.
  Precedent favours the shorter slug (`channels_router`, `auth_mutations`).
- **`spec-042-django_debug_toolbar-0_0_14.md`.** The `django_` prefix restates the ecosystem
  every card lives in; the package's own module path (`middleware/debug_toolbar.py`) uses the
  short form.

### Decision 2 — Card-scope boundary

Spec: [Decision 2][d2].

**Alternatives rejected.**

- **Fold both debug cards into one spec.** Different upstreams (🍓-only vs ⚛️-only), different
  mechanisms (a Django HTTP middleware vs a Strawberry `SchemaExtension`), different module homes
  (`middleware/` vs `extensions/`), and the board deliberately tracks them as two cards with
  "distinct from" edges. A joint spec would re-litigate the board.

**Justification.** The card body pins the boundary itself ("Both mechanisms are useful and not
mutually exclusive" on the sibling; "developer experience" / "Single module + tests" on scope),
and the [`START.md`][start] advice ("resist scope creep") applies verbatim.

### Decision 3 — The symbol is `DebugToolbarMiddleware`

Spec: [Decision 3][d3].

**Alternatives rejected.**

- **A distinctly-ours class name (`DjangoStrawberryDebugToolbarMiddleware`,
  `GraphQLDebugToolbarMiddleware`).** The settings string already carries full provenance; a
  novel class name buys nothing a consumer sees (nobody imports the class) while breaking the
  ecosystem naming convention and making the migration diff noisier than one path segment.
- **Re-exporting from `middleware/__init__.py`.** It would force the `__init__.py` to import the
  guarded module — making `import django_strawberry_framework.middleware` itself raise on a
  toolbar-less machine and breaking whole-package walkers (the [`docs/TREE.md`][tree] renderer,
  coverage collection) for zero consumer benefit; the settings string is typed once either way.

**Derivation.** The decision looks like it contradicts [`spec-041`][spec-041] Decision 3's
"distinctly-ours symbol name" posture and does not, because the two surfaces have different
identity mechanics: a router class is *imported by name* in consumer code, so the name is the API;
a Django middleware is *referenced by dotted settings string*, so the module path is the
distinctly-ours identity and the class name is a Django-ecosystem convention
(`SessionMiddleware`, `AuthenticationMiddleware`) consumers pattern-match. Upstream made the same
call for the same reason.

### Decision 4 — Module, template, and test locations

Spec: [Decision 4][d4].

**Alternatives rejected.**

- **A top-level `middleware.py` module.** The sibling debug card's `extensions/` subpackage and
  this `middleware/` subpackage keep the package tree legible as sibling subsystems, and a
  top-level module would need the router's lazier guard shape to stay walker-safe (see Decision
  5's rejected PEP 562 alternative).
- **Serving the script from `static/` instead of a template.** The asset is injected server-side
  into an already-rendered HTML body by `response.write(...)` — a template rendered to a string
  is the mechanism upstream uses and the only one that needs no URL configuration, no
  `collectstatic` step, and no extra request; a static file would add all three.
- **Inlining the script as a Python string constant.** A JS asset inside a Python module is
  unreviewable and unlintable as JS; the template file matches upstream (easing diff-syncs
  against upstream fixes) and the app-dirs resolution costs nothing given the shipped
  `AppConfig`.

### Decision 5 — Soft `django-debug-toolbar` dependency

Spec: [Decision 5][d5].

**Alternatives rejected.**

- **A hard dependency.** The toolbar is a dev-only tool by its own design (it disables itself
  outside `DEBUG` + `INTERNAL_IPS`); taxing every production install with it inverts its purpose.
  Upstream itself ships it as an extra, not a core dependency.
- **A `django-strawberry-framework[debug-toolbar]` extra (upstream's shape).** The DRF and
  channels precedents both rejected extras — an extra changes how consumers *install*, not
  whether the import needs guarding (an extra is advisory; nothing stops an extra-less install
  from listing the middleware), so it adds a second documented thing without removing any code.
  One uniform no-extras contract across the soft dependencies beats two contracts.
- **The PEP 562 lazy-symbol shape (the `routers.py` pattern).** (a) The consumer's access path is
  Django's `import_string` on a settings string, which imports the module and immediately does
  `getattr` — the guard fires at the same startup moment either way, so laziness buys the
  consumer nothing; (b) the leaf module has no reason to be importable without its dependency —
  unlike `routers.py` (a top-level module walkers must traverse), nothing legitimate imports the
  leaf except the opt-in; (c) the lazy shape costs a builder function, a module-global cache, a
  `__getattr__`, and a `# noqa: F822` — real complexity the router needs and this module does
  not; and (d) the card's definition of done pinned the import-time wording. The decision rule
  this leaves behind is normative and lives in the spec: a top-level module lazies; a dedicated
  opt-in leaf guards at import.
- **Guarding inside `DebugToolbarMiddleware.__init__` (a stub class).** The class *body* needs
  the import (it subclasses the stock middleware), so a stub would lie about identity — the
  rejection [`spec-041`][spec-041] records for the router stub — and the failure would move from
  a clean startup `ImportError` to a first-request failure, since Django imports middleware at
  startup.

**Derivation of the `>=7.0.0` floor.** Upstream declares `django-debug-toolbar>=6.0.0`. Per
[PyPI metadata][debug-toolbar-pypi], `6.0.0` (2025-07-25) classifies Django 4.2-5.2 only, while
`7.0.0` is the first release carrying the `Framework :: Django :: 6.0` classifier — with
`django>=5.2` and `python>=3.10`, matching the package's own floors. The [`spec-041`][spec-041]
single-floor rule is what makes the higher floor mandatory rather than tidy: the install hint is
the error message a deploying consumer follows, so it must not guide a Django 6.0 user into an
unsupported toolbar. The floor's Django coverage therefore reaches 6.0 and stops short of the 6.1
[`pyproject.toml`][pyproject] also advertises — a gap recorded deliberately, not an oversight.

**Why a second wiring gate.** The `debug_toolbar.middleware` import chain reaches
`debug_toolbar.models.HistoryEntry` (through `debug_toolbar.toolbar` and `debug_toolbar.store`),
so a package that is installed while `"debug_toolbar"` is absent from `INSTALLED_APPS` would fail
with Django's `HistoryEntry` app-label `RuntimeError`, which never names the missing app and so is
not self-actionable. The `apps.is_installed("debug_toolbar")` gate raising `ImproperlyConfigured`
is the module's one step outside the pure-`ImportError` model, and it is not an inconsistency: an
`INSTALLED_APPS` omission is a settings error and `ImproperlyConfigured` is Django's idiom for
it, while the "top-level package only" scope still governs `require_debug_toolbar()`'s *import*
guard — a separate concern from the *wiring* gate.

**Why the three-places rule names the gated trio by mechanism, not by count.** The dev-group
specifier, `_DEBUG_TOOLBAR_INSTALL_HINT`, and the re-typed test literal are compared to each other
by the package test; everything else that restates the floor (the glossary body, the consumer
README, the changelog) is compared to nothing. A count of "the places the floor is written" is
right on the day it is written and wrong the day a doc restates the floor, so the rule tells a
floor bump to sweep the tree instead — for the package **name** with each hit read, never for the
`>=` specifier, which is bounded by one spelling and misses a restatement that puts a backtick or
a space between the name and the constraint. **Rejected:** correcting the count to a measured
number (the same instrument with a bigger number, which the next needle would move again).

### Decision 6 — Subclass-and-override, borrowed as-is

Spec: [Decision 6][d6].

**Alternatives rejected.**

- **A from-scratch Django middleware reading `connection.queries`.** Rejected by the card's own
  posture line — that mechanism (lower-fidelity, response-side) is the *sibling card's* design
  space, and re-implementing panel rendering would break every toolbar panel except SQL while
  doubling the maintenance surface.
- **Chaining `super().process_view(...)`.** The stock
  `debug_toolbar.middleware.DebugToolbarMiddleware` defines **no** `process_view` — it is a
  `__call__` / `__acall__`-style middleware — so there is no stock behaviour to preserve and
  nothing for `super().process_view(...)` to reach but the base-class no-op. Upstream's override
  does not chain, and neither does this one; keeping that choice keeps the module diffable
  against its reference.
- **Injecting into every JSON response (dropping the `_is_graphiql` gate).** The gate scopes
  injection to responses from a Strawberry Django view, so a JSON response from some *other* view
  (a DRF endpoint, an admin AJAX call) never grows a `debugToolbar` key. It does **not** narrow
  injection to the IDE — the gate's job is view-scoping, not IDE-detection. Dropping it entirely
  would leak the key onto unrelated JSON views, which is why it stays even though it is not an
  IDE filter. (The statement of what the gate does and does not do is normative and lives in the
  spec's `## User-facing API`.)

### Decision 7 — Strawberry-view detection against `BaseView`

Spec: [Decision 7][d7].

**Alternatives rejected.**

- **Detect the package's own `DjangoGraphQLView`.** It would narrow detection to consumers who
  mount the package view, dropping every consumer who mounts Strawberry's `GraphQLView` directly,
  for no gain: the package views subclass Strawberry's views, which subclass `BaseView`, so the
  engine-owned check already covers them. A middleware that `issubclass`es a package class would
  also make that class public surface for the middleware's sake.
- **Path-based detection (`request.path == settings.GRAPHQL_PATH`).** It invents the settings key
  Decision 2 forbids, breaks multi-endpoint schemas, and diverges from upstream's proven
  mechanism for zero gain.
- **Duck-typed detection (`hasattr(view, "schema")`).** Looser than `issubclass` with no
  compensating benefit — any consumer view exposing a `schema` attribute would be silently
  tagged, and the upstream-parity claim ("the same `issubclass` check") would be false.

### Decision 8 — The introspection-query skip is preserved, verbatim

Spec: [Decision 8][d8].

**Alternatives rejected.**

- **Parsing the query text for `__schema` selections.** A GraphQL parse per response on the dev
  hot path, to improve a heuristic whose false positives are cosmetic. Upstream's name check is
  O(1) and proven.
- **Making the skip configurable.** A knob on a dev tool's history hygiene is configuration
  surface nobody asked for; upstream ships none.

**Derivation.** The skip is deliberately name-based rather than content-based, so a consumer who
issues an introspection query under a different `operationName` gets a payload (harmless) and a
consumer who names a data query `IntrospectionQuery` loses its payload (their choice). Matching
upstream exactly here matters more than closing that cosmetic gap, because the skip's contract
has to be identical for the one-settings-string migration to be behavior-preserving.

### Decision 9 — Test strategy

Spec: [Decision 9][d9].

**Alternatives rejected.**

- **Unit-testing the overrides against synthetic `HttpRequest` / `HttpResponse` objects only.**
  The module exists to compose with the *real* toolbar lifecycle (`super()._postprocess`
  behaviour, `toolbar.request_id` assignment, panel enablement) and the *real* Strawberry view
  (`view_class` through a decorator) — precisely the seams synthetic objects would fake. The
  [`START.md`][start] "coverage is a feature" posture: if the composition is wrong, only real
  traffic notices. The package tier drives fake toolbar / middleware objects **only** for
  branches the real lifecycle cannot expose.
- **Uninstall-based absence testing (a separate no-toolbar CI job).** The DRF and channels
  precedents both chose simulation (one env, one `uv run pytest` gate, no matrix).
- **A `builtins.__import__` block for the absence simulation.** A no-op for this guard:
  `require_debug_toolbar()` is a
  [`require_optional_module`][glossary-require-optional-module] wrapper, i.e. an
  `importlib.import_module("debug_toolbar")` call, and `importlib` routes through
  `importlib._bootstrap._gcd_import` without consulting `builtins.__import__`. Under the block the
  guard re-imports the still-installed toolbar and any raise comes from a later hintless
  statement-import, so Tests 10 and 12 would pass for the wrong reason. The
  `sys.modules["debug_toolbar"] = None` sentinel raises inside `import_module` itself.

**Why the cache hygiene survives the live placement.** The `DEBUG=True` override, the always-true
callback, the `show_toolbar_func_or_path.cache_clear()` and the `DebugToolbar._panel_classes` /
`_urlpatterns` save-clear-restore are properties of pytest-django and of debug-toolbar's process
caches, not of where the tests live, so they hold in the live tier exactly as they would in the
package tier.

### Decision 10 — Version bumps are owned by the joint `0.0.14` cut

Spec: [Decision 10][d10].

**Alternatives rejected.**

- **Bump to `0.0.14` in Slice 2.** Sibling cards shipped into `0.0.14` too; a per-card bump races
  the joint cut and would be reconciled twice over.
- **Defer the lockfile entry to the joint cut too.** Slice 1's tests import `debug_toolbar`; a
  dev-dependency without its lock entry breaks the reproducible-env contract the moment CI runs
  `uv sync`.

**Justification.** Per [`docs/SPECS/NEXT.md`][next], when multiple cards target one patch version
the bump belongs to the joint cut, not to any individual card's spec.

## Non-decision entries

### Borrowing posture — the template port

Spec: [Borrowing posture][borrowing].

**Explicitly-do-not-borrow items stay in the spec.** All three (the hard `debug_toolbar` import,
the plural `middlewares/` package name, upstream's `>=6.0.0` floor) state what the package must
**not** do and are normative.

**One rule behind every diverged form.** Upstream's hook is unsafe once it is a *global* patch: a
dropped `reviver` argument, a `data.hasOwnProperty(...)` guard that throws for null-prototype
objects, a null-handle bail that returned before `delete data.debugToolbar` and so leaked the
server-only key, per-panel DOM writes that assumed every payload panel had a matching node, a bare
`document.getElementById("djDebug")` that resolves to `null` under debug-toolbar 7's default
`USE_SHADOW_DOM=True`, and chained `querySelector` writes that throw on the first absent node.
Each is fixed under one rule — **payload scrubbing is mandatory and DOM updates are best-effort**
— so the ledger can grow without the rule changing.

**The payload-shape guard.** Every other form guards either `data` or a DOM node; the value under
the `debugToolbar` key needs its own guard because upstream reads it unconditionally. The guard
is one record predicate — `isRecord(value)`, `value !== null && typeof value === "object"`,
defined once in the IIFE — applied at every site that reads keys: the entry guard on `data` (whose
`hasOwnProperty.call` clause stays), the captured `toolbar`, `toolbar.panels`, and each `panel` in
the loop. It is written against the answer the DOM update needs ("can keys be read from this
value") rather than against spellings of bad input, which is the [`docs/builder/BUILD.md`][build]
`### Fail-open shapes` rule. The scrub is unconditional and precedes the guard, so the rule is
preserved exactly. **Rejected:**

- a `try` / `catch` around the DOM block — a swallowed exception converts "the check blew up" into
  "the check passed" and would hide a real toolbar-DOM bug behind a silent no-op;
- an enumeration such as `toolbar === null || typeof toolbar === "string" || !("panels" in
  toolbar)` — three spellings, and the fourth throws;
- guarding `requestId` as well — `setAttribute` coerces a non-string value and never throws for
  one, so a missing `requestId` degrades to the stock toolbar's own panel-miss fallback; the write
  stays upstream-verbatim;
- clearing a subtitle that became empty — `if (panel.subtitle)` never clears one, and changing it
  would diverge from the borrow for no dev-visible gain, so it stays upstream-verbatim.

**The panel key is part of the best-effort per-panel form, not an eighth form.** The loop
interpolates each `panels` key into `#${id}` and `#djdt-${id}` selectors, so a key that is not a
valid CSS identifier would raise a `DOMException` out of the patched globals. No payload this
package produces reaches it (the middleware keys `panels` by each panel's own class-derived
`panel_id`); a foreign payload can. An id that cannot be *resolved* and a node that cannot be
*found* are one promise, so the guard completes the existing form and the ledger does not grow.
`CSS.escape` is defined for every code point and returns a valid identifier for every non-empty
input; its single non-total case is the empty string, which escapes to the empty identifier — not
a selector at all — so the escape covers every key but one and an explicit `id === ""` skip covers
that one. **Rejected:**

- leaving it as documented behaviour — scoping the contract to "we crash on a payload key we
  cannot parse" documents a defect as a promise the rule already contradicts;
- a `try` / `catch` around the lookup, or an enumeration of invalid-identifier spellings — the
  same two shapes rejected for the payload-shape guard;
- one wrapper per selector — the key is escaped once, where it is bound, so the two selector
  expressions stay byte-identical and the template-port row pinning the nav lookup's scoping to the
  resolved handle keeps its needle; it also makes the pinned property "asked once, at the key's
  entry", the single-definition shape `isRecord` has;
- guarding `CSS.escape` itself — it predates every other API the asset and the stock toolbar's
  scripts require, so a browser lacking it cannot render the DOM this function updates; and a
  `typeof CSS !== "undefined" ? CSS.escape(key) : key` fallback is the fail-open shape, letting the
  raw key through whenever availability cannot be told.

**Why the template-port test is one row per predicate.** A single test with a list of assertions
scores one failing node id for one dropped guard and one for all of them together, so the suite
could not distinguish a dropped guard from a dropped family. The claim the table makes is per kind
of form and carries no count: a form diverging by spelling carries both halves (the port's
spelling present, upstream's absent — a presence row alone cannot see a revert that restores
upstream's shape alongside the port's); a form diverging by position (the mandatory scrub, which
the borrow spells the same way elsewhere) carries index, adjacency, nesting and return-count rows,
since there is no replaced spelling to assert absent; a preserved invariant carries the row for
the write it keeps.

**Why the scrub's unconditionality is measured by counting returns.** Wrapping a condition around
the scrub leaves every ordering row matching, which is why the adjacency, own-statement and
non-nesting rows exist; but a bail placed *above* the capture reintroduces the leak while failing
none of them. The property that subsumes all three is that **nothing returns between the entry
guard and the scrub**. It is measured from two anchors because a span opening at the entry guard's
own return slides down with a bail inserted above it and reads clean; the second row counts from
the function opener instead.

**The rules an absence needle obeys, and why.** Each violation produces a row that reads green
forever:

- **It must occur in the borrow.** A needle the borrow never spells (for example the
  `document.getElementById(...)` nav lookup as one token, which upstream wraps across three source
  lines) can never catch the verbatim paste it names. Count it in both assets, occurrences rather
  than matching lines.
- **It must contain no sibling absence needle.** A needle containing another absence row's needle
  cannot fail without that row failing too, so it adds no failing node id. The value-returning
  panel loop row is therefore needled on `.panels).map(`, not on the whole loop head with its
  binding.
- **It must be typed as a literal.** A needle derived from a shared constant goes silently inert
  the moment the constant drifts, where a presence row reading the same constant goes red instead.
- **A rename in the port owes a re-count.** A needle that quotes more of the line than the
  divergence itself is coupled to the port's own spelling, so a rename can narrow its reach over
  hand edits without making it inert; the fragment that names only the divergence is the one that
  survives.

### Risks and open questions

Spec: [Risks and open questions][risks].

Each risk the spec carries has a preferred posture and a fallback; the constraints themselves are
in the spec.

- **`_postprocess` is a private-underscore method.** *Preferred:* accept the coupling — upstream
  carries the identical override (decorated `@override`, so a type checker notices a rename), the
  archived `django-graphiql-debug-toolbar` did too, and the mechanism has been stable across the
  toolbar's 4.x → 7.x line. *Fallback:* if a toolbar release breaks the hook, the gate that
  catches it (the suite under a refreshed lockfile) also scopes the repair — worst case the floor
  gains a temporary ceiling with a follow-on card.
- **Schema-registry order-dependence on a shared worker.** *Preferred:* the live tier's
  project-schema fixtures — order-independence by reconstruction through the single-sited
  `examples/fakeshop/schema_reload.py` helper. *Fallback:* none anticipated; a surfaced flake in
  this class is fixed in the shared helper, at source.
- **The async path ships unverified.** *Preferred:* ship sync-verified with the glossary body
  claiming exactly that. [`spec-043`][spec-043] ships `AsyncTestClient` as the vehicle and places
  the toolbar's async smoke in the toolbar's own test module, where its soft-dependency fixture
  lives. *Fallback:* a dedicated async smoke test is a small follow-on, not a redesign.
- **The `BaseView`-at-the-floor gate.** *Preferred:* present (the class predates the package's
  Strawberry floor by a wide margin). *Fallback:* bump the project's Strawberry floor. The spec
  names no version for this gate because a restated floor rots the moment the floor moves.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[pyproject]: ../../../pyproject.toml
[start]: ../../../START.md

<!-- docs/ -->
[glossary-require-optional-module]: ../../GLOSSARY.md#require_optional_module
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
[next]: ../NEXT.md
[risks]: ../spec-042-debug_toolbar-0_0_14.md#risks-and-open-questions
[spec-041]: ../spec-041-channels_router-0_0_14.md
[spec-042]: ../spec-042-debug_toolbar-0_0_14.md
[spec-043]: ../spec-043-test_client-0_0_14.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[debug-toolbar-pypi]: https://pypi.org/pypi/django-debug-toolbar/json
