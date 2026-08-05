# Build: Round R1b — boundary-recognition contract enactment

Decision reference: `docs/builder/build-046-transport_security-0_0_15.md`,
`# Closeout cycle (card 046)`, `## Maintainer decision M-B` ("what recognition owes a forged
boundary marker") and `## Round R1b — boundary-recognition contract enactment`. M-B is settled;
this round enacts it and nothing else.
Spec reference: `docs/spec-046-transport_security-0_0_15.md` — Decision 18 (where in the request
lifecycle the body boundary runs), Decision 7 (the counted body cap, and the sentence that letting
a foreign object's failure "fall through as an unrelated `500` is the wrong answer at the one seam
this design deliberately centralizes"), Decisions 9 and 10 (the wire refusals the boundary also
carries). **This round writes no spec text**; R2 owns the Decision 18 rewrite and this artifact
hands it the wording under `### Notes for Worker 1 (spec reconciliation)`.
Prior round: `docs/builder/bld-046-r1-remediation_review.md` (`Status: final-accepted`), whose
consolidated hand-off carries this item as **M-B** with its five over-claiming sites.
Status: built

## Round preamble

A **review round** in the `BUILD.md` `## Review rounds` sense, inserted between R1 and R2. Its
input is not a maintainer review document but a maintainer **decision** escalated out of one: two
R1 review passes graded the condition Low on the same reasoning and escalated rather than fixing
it, because the prior question — whether the package owes a controlled response to a callback
forging its private marker at all — is a contract call. Worker 0 escalated it, a research pass ran
over `AGENTS.md` and every document it names plus every `README.md` in the tree, and the maintainer
decided. The full record, including the three rejected candidates and their reasons, is M-B in the
build plan. **No worker re-opens it.** If a *measured* obstacle makes it unimplementable as decided,
that is a stop condition: say so and set `revision-needed` rather than substituting a design.

The full `Status:` chain applies — Worker 1 plans, Worker 2 builds, Worker 3 reviews, Worker 1
verifies.

### The condition, and what closing it means

`middleware/request_body.py::_package_view_instance` recognizes a package view's callback by the
private marker `views.py::_RequestBodyBoundaryMixin.as_view` stamps, then builds the instance from
the callback's `view_class` / `view_initkwargs` the way Django's own `as_view` does. Recognition
ends at *an instance was produced*, not at *an instance carrying the boundary*, so a callback that
forges the marker onto a real, buildable class that is not a package view reaches
`view._enforce_request_boundary(request)` and raises `AttributeError` out of `process_view` — an
unhandled `500` from a hook whose every other outcome is a controlled response, which is a property
that module claims in five places.

M-B's answer: **recognition must reach the boundary itself, probed on the class before any
construction.** A forged marker over a foreign but buildable class then neither reaches
`view._enforce_request_boundary` nor runs that class's `__init__` at all.

### Baseline, measured this pass

- `git status --short`: `_boundary_ordering.py` staged (`A`, authorized by the plan's
  `## Write-set correction W-1`); `_request_body.py`, `middleware/request_body.py`, `views.py`,
  `examples/fakeshop/apps/kanban/constants.py`, `tests/test_routers.py`, `tests/test_views.py` and
  the build plan modified; `docs/builder/bld-046-r1-remediation_review.md` untracked. **All of it
  is R1's landed-but-uncommitted work plus Worker 0's plan section.** Nothing here is reverted,
  stashed, checked out or restored by any pass of this round (`AGENTS.md` #34).
- `uv run pytest tests/test_views.py --no-cov` — **197 passed**. Every failability baseline in this
  round therefore starts green and no mutant's set needs differencing.
- Shared `.venv`, read rather than recalled (`uv pip list`, `.venv/bin/python -V`): **Python
  3.14.2**, **django 6.0.5**, asgiref 3.11.1, strawberry-graphql 0.316.0. Far above the floor,
  which is why `### Floor verification scope` below is owned by a pass and not by the final gate.
- `/tmp/dsf-floor` exists and its versions were **read before being relied on**
  (`/tmp/dsf-floor/bin/python -V`; `uv pip list --python /tmp/dsf-floor/bin/python`): **Python
  3.10.19**, **django 5.2**, **strawberry-graphql 0.316.0**, asgiref 3.12.1, channels 4.3.2,
  daphne 4.2.3, pytest 9.1.1, pytest-django 4.12.0, pytest-asyncio 1.4.0, and
  `django-strawberry-framework 0.0.14` editable against this checkout. So it **is** the floor as
  `BUILD.md` `## Floor verification` states it, and being editable it carries whatever this round
  writes. Re-read it at build time rather than inheriting this reading.
- The shared `.venv` is never installed into: every floor command carries an explicit
  `--python /tmp/dsf-floor/bin/python`, or is invoked as `/tmp/dsf-floor/bin/python -m pytest`.

### Reference copies: for one file the index, not `HEAD`

`_boundary_ordering.py` is **new in R1 and staged**, so it has no `HEAD` version and
`git show HEAD:django_strawberry_framework/_boundary_ordering.py` fails. Its read-only reference is
the index: `git show :django_strawberry_framework/_boundary_ordering.py` into a scratch path outside
the repo. For `middleware/request_body.py` and `tests/test_views.py` a `HEAD` version exists but
predates R1 entirely, so it is not the comparison this round wants either; the reference is the
working tree at R1's close, which is why `scripts/prove_failability.py`'s pre-mutation copy is the
only restore reference and why an empty `git diff` is unachievable. **`git stash`, `git checkout`,
`git restore` and `git worktree` are never part of verifying anything here** — the maintainer runs
concurrent sessions against this tree.

### Spec status-line re-verification (this spawn)

Read: the spec opener still reads "Planned for `0.0.15`" and "Status: **BUILT — all five slices …
The `0.0.15` release itself is the joint cut's, so the version quintet still reads `0.0.14` on
disk.**" That is accurate against `HEAD` (both `pyproject.toml` and `__init__.py` read `0.0.14`) and
this round falsifies none of it. **No spec edit is made or licensed**: R1b's write set names neither
the spec nor its rationale, and the Decision 18 reconciliation the round *does* create work for is
R2's, recorded under `### Notes for Worker 1 (spec reconciliation)`.

### Cycle-wide declarations this round inherits, copied as written

- **Ownership partition: none; sequential rounds.** Each round owns every file it writes; no two
  rounds run concurrently.
- **Version quintet: still not ours.** `pyproject.toml` and `__init__.py` both read `0.0.14`;
  `0.0.15` is uncut and its quintet belongs to the last card of that line to land (spec
  Decision 15). No round in this cycle touches it, and no round edits `CHANGELOG.md`.

### Write set, and what is out of it

**Writable by this round:** `django_strawberry_framework/middleware/request_body.py`,
`django_strawberry_framework/_boundary_ordering.py`, `tests/test_views.py`, this artifact, and
scratch under `docs/builder/temp-tests/r1b/`.

**Explicitly not:** `django_strawberry_framework/views.py`, `_request_body.py`, `consumers.py`,
`tests/test_routers.py`, `examples/fakeshop/apps/kanban/constants.py` (all dirty from R1), the spec
and its rationale (R2's), the build plan (Worker 0's), `docs/builder/bld-046-r1-remediation_review.md`
(closed), `CHANGELOG.md`, the version quintet, `docs/feedback.md` / `docs/feedback2.md`, other
cycles' artifacts, everything under `docs/SPECS/`. **The design below deliberately needs no
`views.py` edit**, which is one of the reasons it is the design (see `### Implementation steps`
step 2 and `### Architectural decision B-2`). If implementation concludes one of those files must
change, that is a write-set correction only Worker 0 may make: record it under
`### Notes for Worker 1 (spec reconciliation)` and stop, rather than widening the set.

Nothing new is staged. `git add` is not run by any pass of this round; the one staged path is
W-1's and stays exactly as it is.

---

## Plan (Worker 1)

### Architectural decision B-1: where the boundary attribute name lives, and its exact form

**Decided: a third module-level constant in `django_strawberry_framework/_boundary_ordering.py`.**
That module's docstring already states this as its charter — the marks and their meanings live
there because the two modules have to agree about them and neither imports the other — so the
method name becomes its third fact and the probe costs **no** import of `views.py`. There is no
upstream symbol for "carries the request-body boundary" (`_enforce_request_boundary` is defined
only in `views.py`), which is why the probe is for the private attribute *name* and why naming it
here is what keeps `middleware/request_body.py`'s deliberate property of importing neither
`views.py` nor anything that imports it.

Current contents of that module, read this pass: `_BOUNDARY_MARKER`, `_BOUNDARY_ENFORCED`,
`_boundary_middleware_request` (a `ContextVar`), `_CsrfOrderingExemption` and the shared
`_CSRF_ORDERING_EXEMPTION` instance; imports are `from __future__ import annotations`,
`contextvars.ContextVar`, and a `TYPE_CHECKING`-only `django.http.HttpRequest`. **The addition adds
no import**, which is the property Worker 2 proves rather than asserts (step 6).

Exact form — a name constant beside the two marks, before the `ContextVar`, so the three
name-carrying facts sit together:

```python
#: The name of the boundary method a package view carries, probed on a marked
#: callback's ``view_class`` by the boundary middleware before it builds anything.
#: Defined by ``views.py::_RequestBodyBoundaryMixin._enforce_request_boundary`` and
#: named here because the middleware has to recognize it without importing that
#: module. A class carrying no callable of this name is not one whose boundary that
#: middleware can run, whatever else it carries.
_BOUNDARY_METHOD = "_enforce_request_boundary"
```

`_BOUNDARY_METHOD` is the name: it sits in the established `_BOUNDARY_*` family, and it says what
the value is (a method name) rather than what one use of it is. The module docstring's title and
its "have to agree about two facts per request" sentence both become false with a third fact and
are rewritten in step 1 — the third fact is **not** per-request, it is a static fact about the view
class, and the docstring must say so rather than fold it into the two marks.

**Rejected: put the constant in `middleware/request_body.py`.** It would work and cost no new
symbol elsewhere, and it is wrong for the reason A-1 established in R1: the fact is shared with
`views.py`, which is where the method is defined, so a mark that lives in the consumer of the
protocol rather than in the protocol module reintroduces exactly the split the third module
removed. It would also leave a future reader of `_boundary_ordering.py` believing the module holds
the whole protocol when it holds two thirds of it.

**Rejected: import the name from `views.py`.** It is the inversion A-1 deleted, and M-B names its
survival as a requirement.

### Architectural decision B-2: how `views.py` and the middleware are kept from drifting apart

A string constant naming a method defined in another module is a coupling, and this is the one
genuinely new risk the change introduces. It has three failure directions, and **all three fail
loudly** — two of them on rows that already exist, one on a row this round adds. Stated as
mechanism, then measured (step 8), never asserted:

1. **`_enforce_request_boundary` is renamed in `views.py` and the constant is not.** The probe then
   fails for a *genuine* mount, so every callback is declined, the chain never runs the boundary and
   never stamps the request. That is exactly the state failability entry 3 measures (make recognition
   answer `None` unconditionally), and it fails **4** rows — the two
   `::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering` rows and the
   two `::test_the_view_does_not_measure_a_body_the_chain_already_measured` rows. It cannot be silent.
2. **The constant is changed and the method is not.** Same 4 rows, plus the coupling row this round
   adds (`### Test additions / updates` T3), which asserts the constant names the mixin's own
   method object.
3. **Both are renamed but `process_view`'s direct call is not.** `process_view` then reads a
   missing attribute off a *recognized* instance and raises `AttributeError` on every genuine
   mount — the loudest of the three, and the same 4 rows plus every positive middleware row.

So the coupling is pinned by rows in `tests/test_views.py`, which is this round's own file, and the
loudness is a measurement Worker 2 records rather than a claim the plan makes.

**Rejected: call the boundary through the constant** — `getattr(view, _BOUNDARY_METHOD)(request)`
in `process_view`, or having `_package_view_instance` return the bound boundary instead of the
instance. Either makes divergence impossible by construction rather than by test, which is
strictly stronger, and both lose: the first hides the call from `grep` and from the
`path::QualifiedName` reference convention `AGENTS.md` requires, for a divergence that three row
sets already catch; the second renames the recognizer's answer, is outside M-B's scope ("exactly
M-B and nothing else"), and would invalidate the labels and anchors of two failability entries that
name `_package_view_instance` as the site of the answer.

**Rejected: an import-time guard in `views.py`** (`if not hasattr(_RequestBodyBoundaryMixin,
_BOUNDARY_METHOD): raise ConfigurationError(...)`). Three reasons: `views.py` is dirty from R1 and
outside this round's write set, so it would need a Worker-0 write-set correction for a guard nobody
asked for; the raise arm is reachable only by a package-internal rename, i.e. it is a production
branch no test can drive without a mutation, and `pragma: no cover` is never the workaround; and
tests are this repo's idiom for pinning an internal identity (`::test_the_view_callback_of_both_views
_carries_the_csrf_exempt_mark` already asserts `as_view.__func__` identity that way).

**Rejected: deriving the constant from the method** (`_BOUNDARY_METHOD =
_RequestBodyBoundaryMixin._enforce_request_boundary.__name__`). The protocol module would have to
import `views.py` to learn it. Same inversion as B-1's second rejection.

### Architectural decision B-3: the exact clause and its position

**Decided: a separate `if` statement, third in the sequence — after the two `isinstance` tests,
before the construction `try`.**

```python
    if not getattr(view_func, _BOUNDARY_MARKER, False):
        return None
    view_class = getattr(view_func, "view_class", None)
    initkwargs = getattr(view_func, "view_initkwargs", None)
    if not isinstance(view_class, type) or not isinstance(initkwargs, dict):
        return None
    if not callable(getattr(view_class, _BOUNDARY_METHOD, None)):        # <- the new clause
        return None
    try:
        return view_class(**initkwargs)
    except TypeError:
        return None
```

Three properties decide the position, and each is a requirement rather than a preference:

- **After the two `isinstance` tests.** An attribute probe of an arbitrary object can execute that
  object's `__getattr__`; after `isinstance(view_class, type)` the read is a class attribute lookup.
  This is the same ordering `middleware/debug_toolbar.py::GraphQLDebugToolbarMiddleware.process_view`
  documents for the same reason (`isinstance(view, type)` in front of `issubclass`, because a
  non-class `view_class` attached by an unrelated decorator must not `TypeError` a `500` out of a
  hook that runs for all global traffic) and the same ordering
  `mutations/fields.py` uses in front of `::_has_mutation_protocol`.
- **Before the construction `try`.** This is M-B's "why the class rather than the built instance":
  probing the instance would close the `500` and still run a foreign class's `__init__`, and the
  suite already carries a row forbidding exactly that.
- **Its own statement, not a third disjunct of the existing `if`.** Folding it in would fold three
  different facts into one decision, and it would destroy the anchor of failability entry 15, whose
  two-line anchor is that statement verbatim and whose row set is the only comparable measurement of
  the two shape clauses. A separate statement gives the new clause its own anchor and therefore its
  own row set, which `### Failability proof set` requires.

**The shape is `callable(getattr(view_class, _BOUNDARY_METHOD, None))`, not `hasattr`.** See
`### Fail-open shapes to read for` for the fail-open argument and the measurement that decides it.

**One limit, stated rather than discovered.** An attribute probe of a *class* consults its
metaclass, so a forged `view_class` whose metaclass defines `__getattr__` still runs that code.
Measured this pass (`docs/builder/temp-tests/r1b/test_w1_probe_answers.py`): the probe records one
`__getattr__("_enforce_request_boundary")` invocation on such a class and answers `False`. That is
strictly less than running `__init__`, it is unavoidable for any attribute probe (Django's own
`as_view` and the debug-toolbar recognizer consult the metaclass identically), and forging the
package's private marker remains outside the threat model — the spec-045 stance that no walk inside
the same interpreter is a trust boundary against a party already running code in the process. The
probe is not added to defend against the forger; it is added so the hook's every outcome is a
controlled response. Worker 2 states this in the docstring; nothing defends against it.

### Architectural decision B-4: the construction guard stays

**Decided: the `try` / `except TypeError` arm stays exactly as it is.** With a class-level probe
ahead of it the arm narrows to classes that carry a callable `_enforce_request_boundary`, and what
still reaches it is not empty:

- **A genuine package class with `view_initkwargs` it rejects.** The existing fixture
  `tests/test_views.py::_marked_callback_with_initkwargs_the_class_rejects` is exactly this —
  `view_class = DjangoGraphQLView`, `view_initkwargs = {"not_a_view_kwarg": 1}` — and R1 measured the
  raise it produces: `BaseView.__init__() missing 1 required positional argument: 'schema'`. That
  class passes the probe (measured this pass: the probe answers `True` for `DjangoGraphQLView`,
  `AsyncDjangoGraphQLView` and `_RequestBodyBoundaryMixin`), so route 3 reaches the construction arm
  after the change exactly as before it. **Removing the arm would restore an unhandled `500` for a
  route the suite already pins.**
- **A genuine consumer subclass whose `__init__` raises `TypeError` of its own.** R1 measured this
  one at the wire on both chains: identical exception type, identical message, and `0`
  `MultiPartParser.parse` calls installed and uninstalled — so the arm moves such a failure's
  **site** and never its **loudness**, because Django's own `as_view` closure would construct the
  same class with the same kwargs for the same request.

So the arm is not made redundant, and it is also not weakened: nothing about it changes, its
docstring paragraph is corrected only to name what now reaches it.

### DRY analysis

**Helper inventory checked.** Refreshed for the **whole package** this pass — the `worker-1.md`
AST inventory over `django_strawberry_framework/**` into `docs/shadow/helper-inventory.md`, 1,700
lines — and grepped for the shapes this round needs: `recogni`, `probe`, `carries`, `hasattr`,
`view_class`, `callable`, `boundary`, `enforce`. Three candidates came back and each was read at
source:

- **`mutations/fields.py::_has_mutation_protocol`** — "Return whether a class carries the
  duck-typed mutation / form-mutation protocol", and its body is
  `callable(getattr(mutation_cls, "resolve_sync", None)) and …`, called behind
  `if not isinstance(mutation_cls, type) or not _has_mutation_protocol(mutation_cls)`. This is the
  package's established idiom for a class-level protocol probe, **shape and position both**, and it
  is why the clause in B-3 is idiom rather than invention. **Reuse rejected**: it answers a
  four-attribute mutation protocol in an unrelated subsystem; generalizing it to "does this class
  carry attribute X" would produce a helper thinner than its own call site.
- **`middleware/debug_toolbar.py::GraphQLDebugToolbarMiddleware.process_view`** — the standing
  precedent for recognizing a package view from a middleware: it reads `view_class` and tests
  `isinstance(view, type) and issubclass(view, BaseView)` against an **upstream** import, and
  declines quietly. Cited as the position precedent. **A shared recognizer is deliberately not
  built here**: R1's hand-off item D-6 records it as a now-*decidable* question (A-1 removed the
  import constraint that foreclosed it) whose justifying condition is a **third** middleware needing
  the same recognition, or the two needing to agree about one callback. R1b is neither, and a
  security-fix round is not where that consolidation belongs. Non-owner status recorded so the next
  reader sees it was decided, not missed.
- **`_boundary_ordering.py`'s two existing marks** — the constant-plus-`#:`-comment shape the third
  fact copies, so the module reads as one protocol rather than two conventions.

**Existing patterns reused.**

- The name-constant shape in `_boundary_ordering.py` (`_BOUNDARY_MARKER`, `_BOUNDARY_ENFORCED`) —
  B-1's addition is the third instance, not a new convention.
- `tests/test_views.py`'s recording-fixture idiom: a module-level list plus a fixture whose
  docstring states that *recording* is the contract (`_VIEW_CLASS_FACTORY_CALLS` /
  `_view_class_factory`, whose docstring says it "records rather than merely returning, because the
  contract is that nothing but a class is ever *called*"). The new foreign-class fixture mirrors it
  exactly.
- The existing parametrized decline test, which the fifth route joins rather than duplicating.
- `docs/builder/temp-tests/r1/test_w2p3_hotpath_recognizer.py`'s two-arms-one-process shape for the
  hot-path number, and `…/test_w3p3_decline_arm.py`'s in-chain observing-CSRF-subclass shape for the
  fallback-equivalence measurement.

**New helpers justified: none.** One constant, one two-line clause, one recording foreign class,
one callback fixture, one urlpattern, three test rows and one fixture attribute. Nothing here has a
second call site, and a helper wrapping a single `callable(getattr(...))` would be a name in front
of an expression.

**Duplication risk avoided.**

- **A second spelling of the method name.** The whole point of B-1: one constant, one definition
  site, and `process_view`'s direct call is the only other place the name appears in the package —
  measured, `view._enforce_request_boundary(request)` occurs exactly once in
  `middleware/request_body.py`. A naive implementation would have written the literal
  `"_enforce_request_boundary"` into the middleware.
- **A second "is this one of ours?" recognizer.** D-6's condition is named above and is not met.
- **A second recording-fixture convention.** Named above; Worker 2 mirrors the existing one.
- **A second decline test.** The fifth route joins
  `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed`'s parametrization,
  as M-B and the plan's `## Round R1b` both specify.

### Implementation steps

Line anchors are pin-at-write-time navigational hints; verify against the current source before
editing.

0. **Record SHA-256 of the three writable files before the first edit** (`shasum -a 256
   django_strawberry_framework/middleware/request_body.py
   django_strawberry_framework/_boundary_ordering.py tests/test_views.py`) and quote them in the
   build report. It is what lets Worker 3 confirm the production delta is exactly this plan's rather
   than accepting the claim, and it is free.

1. **`_boundary_ordering.py` — the third fact plus its docstring seam.**
   - Add `_BOUNDARY_METHOD` in B-1's exact form, after `_BOUNDARY_ENFORCED` and before
     `_boundary_middleware_request`.
   - Rewrite the module docstring's title (`#"The two marks the request-body boundary's ordering is
     negotiated with"`) and its `#"have to agree about two facts per request"` sentence: the module
     holds **two per-request marks and one static fact about the view class**, and the third is not
     per-request. Add a `The protocol` paragraph for `_BOUNDARY_METHOD` in the same voice as the two
     existing ones, saying what it is (a method name), who defines it (`views.py`), who reads it
     (the boundary middleware, on the `view_class`, before constructing anything), and why it lives
     here (so recognizing the boundary costs no import of the view classes).
   - **Add no import.** The module still imports nothing but the standard library, which its
     docstring claims and step 6 proves.

2. **`middleware/request_body.py` — the clause.**
   - Extend the existing `from django_strawberry_framework._boundary_ordering import (...)` block
     with `_BOUNDARY_METHOD` (ruff's ordering puts it after `_BOUNDARY_MARKER` and before
     `_boundary_middleware_request`).
   - Insert B-3's clause in `::_package_view_instance`, third, as its own statement.
   - Nothing else in the module's executable surface changes. `process_view`'s
     `view._enforce_request_boundary(request)` call stays a direct call (B-2), and neither
     `__call__`, `__acall__`, `__init__` nor `_require_boundary_before_csrf` is touched.

3. **`middleware/request_body.py` — the docstring sites, made true rather than narrowed.** Each
   bullet names the sentence and the fact it must now state. Wording is Worker 2's
   (`### Implementation discretion items`); the facts are not.
   - **`::_package_view_instance` #"The recognition is one decision and it ends at the instance,
     because the instance is the answer"** — **false now, and the load-bearing rewrite.**
     Recognition ends at *the boundary on the class*; the instance is built only from a class that
     carries it. The enumeration that follows gains the probe as its third clause with its own
     reason: a `view_class` can be a real, buildable class and still be no package view, and the
     boundary is what `process_view` runs, so the boundary is what recognition has to establish.
   - **`::_package_view_instance` #"a hook whose every other outcome is a controlled response"** —
     keep verbatim. It **becomes true** with this change; that is the point of the round.
   - **`::_package_view_instance` #"The two ``isinstance`` tests stay ahead of the construction"** —
     keep, and extend: they stay ahead of the **probe** as well, so the attribute read is a class
     attribute lookup rather than an arbitrary object's `__getattr__`.
   - **`::_package_view_instance`'s `TypeError` paragraph** — keep its argument, correct its scope
     to what now reaches it (B-4's two inputs, named).
   - **`::_package_view_instance` — one new sentence for B-3's stated limit** (a class attribute
     probe consults the metaclass; forging the private marker is outside the threat model; the probe
     exists so every outcome is a controlled response).
   - **Module docstring #"so no non-package view is touched"** — now true in the strong sense, and
     the sentence around it (`#"It recognizes a package view by the marker attribute stamped on the
     callback and by building the instance from the view_class / view_initkwargs bookkeeping behind
     it"`) must state the boundary probe and that the boundary's *name* is reached through
     `_boundary_ordering.py`, which is what keeps this module importing neither `views.py` nor
     anything that imports it.
   - **`::process_view` #"reached through an instance built the way ``View.as_view`` builds one"** —
     add that the instance is built only after the class is known to carry the boundary.
   - **Class docstring #"at the cost of one ``getattr`` in ``process_view``"** — **do not change.**
     It is scoped to a request that is *not* a package view's, and the marker test is still first
     and still the only read such a request pays. Recorded so it is neither churned nor flagged.

4. **`tests/test_views.py` — fixtures.**
   - Add a foreign but buildable view class that records its constructions, mirroring
     `_VIEW_CLASS_FACTORY_CALLS` / `_view_class_factory`: a module-level list, a class whose
     `__init__` appends to it, and a docstring stating that recording is the contract because the
     property under test is that the class is never constructed at all. It must **not** carry
     `_enforce_request_boundary`.
   - Add the marked callback for it (marker + `view_class` = that class + `view_initkwargs = {}`),
     returning a `"marked, …"` body so it satisfies the parametrized test's existing
     `startswith("marked, ")` assertion, and a urlpattern for it.
   - **`_view_class_factory` gains the boundary attribute** — `setattr(_view_class_factory,
     _BOUNDARY_METHOD, <a callable>)` beside the existing `setattr` block, plus one docstring
     sentence saying why: with the probe in place, a callable non-class that carries **no** boundary
     is refused by the probe, so the input that still distinguishes the two `isinstance` clauses is a
     callable non-class that *does* carry it. **This is what keeps failability entry 15 out of the
     weakly-pinned band** — measured this pass: the probe answers `True` for a function carrying the
     attribute and `False` for one that does not. Do not remove or weaken the existing
     `isinstance` clauses to accommodate it.
   - Import `_BOUNDARY_METHOD` from `_boundary_ordering` in the existing import block.

5. **`tests/test_views.py` — rows and prose.** The three new rows and the two docstring rewrites are
   specified in `### Test additions / updates`. Tick this step only when both prose sites are
   rewritten, not only when the rows pass.

6. **Prove the no-import property mechanically, do not assert it.** Three readings, all cheap, all
   quoted in the build report:
   - `grep -n 'import' django_strawberry_framework/_boundary_ordering.py` — still only
     `__future__`, `contextvars`, and the `TYPE_CHECKING` `django.http` block.
   - Neither of the two modules imports the other:
     `grep -c 'middleware.request_body\|middleware import' django_strawberry_framework/views.py`
     and `grep -c 'from django_strawberry_framework.views\|framework import views'
     django_strawberry_framework/middleware/request_body.py` — **both 0**.
   - By execution, since a grep cannot see a transitive import: import
     `django_strawberry_framework._boundary_ordering` in a fresh interpreter after
     `django.setup()` and difference `sys.modules` — no `django_strawberry_framework.views` and no
     `strawberry.django.views` entry appears on its account. R1's pass-2 report used the same
     `sys.modules`-difference method for the sibling claim; reuse the method, take your own reading.

7. **Confirm a genuine mount passes the probe by construction, at both transports.** Row T3 covers
   it permanently; the build report also states the reading. Measured this pass on Python 3.14.2:
   the probe answers `True` for `DjangoGraphQLView`, `AsyncDjangoGraphQLView` and
   `_RequestBodyBoundaryMixin`, and `False` for `dict` (M-B's own measured forgery), for a
   recording foreign class, for `types.MappingProxyType`, and for a `DjangoGraphQLView` subclass
   that sets `_enforce_request_boundary = None`. Re-take these at the floor (step 9), because a
   plan-time reading on the newer interpreter is not a floor reading.

8. **Measure the drift-loudness claim rather than asserting it (B-2).** Transiently rename
   `views.py::_RequestBodyBoundaryMixin._enforce_request_boundary` and record which rows fail. Do it
   through `scripts/prove_failability.py` with a **separate auxiliary manifest**
   (`docs/builder/temp-tests/r1b/proofs-drift.json`, one entry, `--output …/proofs-drift.md`) so the
   restore is byte-proved by the runner rather than by hand, and because `views.py` is outside this
   round's write set: a transient, byte-proved mutation is a measurement, a surviving edit is a
   write-set violation. The anchor **must be the full `def` line**
   (`    def _enforce_request_boundary(self, request: HttpRequest) -> None:`) — measured this pass,
   the shorter `    def _enforce_request_boundary` prefix matches **2** lines
   (`_enforce_request_boundary_once` is the other) and the runner aborts an entry whose anchor
   matches other than once. Expect the 4 rows of entry 3 plus T3; report the node ids. If the run
   exits 3, read the marker it leaves before doing anything else — `views.py` is uncommitted
   maintainer-relevant work.

9. **Floor run** — `### Floor verification scope`.

10. **Hot-path number** — `### Hot-path budget`.

11. **Failability manifest** — `### Failability proof set`.

12. **Staleness sweep** (`BUILD.md` `### Test staleness a focused run cannot see`). No model field
    and no wire shape changes here, so the sweep is a correctness read, not a red-test hunt. Measured
    this pass, to be re-taken: `grep -rn '_enforce_request_boundary' tests examples --include='*.py'`
    returns **6 hits, all in `tests/test_views.py`** and none in `examples/**`; the live tier's probe
    wrapper (`examples/fakeshop/test_query/test_transport_api.py`) copies `csrf_exempt` and the
    `view_class` / `view_initkwargs` bookkeeping but **not** the marker, so it is declined at the
    first clause and this change cannot move it. Also `grep -rn 'view_class' tests examples
    --include='*.py'` and read the hits, then run
    `uv run pytest tests/test_views.py examples/fakeshop/test_query/test_transport_api.py --no-cov`
    and record both totals.

13. **`uv run ruff format` and `uv run ruff check --fix` scoped to this pass's own files, never
    `.`**, then `git status --short` and confirm every modified path is one of the three plus the
    artifact and `docs/builder/temp-tests/r1b/**`. Anything else is a stop-and-report, never a
    revert. `docs/builder/` is excluded from the markdown link-scaffold check, so this artifact owes
    no link-definition block. ASCII-only applies to the two `.py` files.

### Test additions / updates

Permanent rows in `tests/test_views.py`. Each names what fails if the contract is lost, because a
row whose failure mode is unnamed is a row nobody can tell is non-distinguishing.

- **T1 — the fifth decline route joins the existing parametrization.** Add the new route to
  `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed`'s `route` list. It
  asserts the parent test's unchanged `200` plus `startswith("marked, ")`. Without the probe the
  foreign class is constructed and `process_view` reads the boundary off it, so the row fails on an
  unhandled `500` — which is the condition M-B is about, reached at the wire.
  - Its docstring is rewritten: **five** routes, not four; the fifth's mechanism named (a
    `view_class` that **is** a class and **is** buildable and carries no boundary, which only the
    boundary probe tells apart from a real mount); and the subject widened honestly — the fifth is a
    callback the recognizer *declines to build* rather than one it *cannot* build. **The node-id stem
    is kept.** M-B and the plan's `## Round R1b` both name this test as the fifth route's home, and
    renaming it would break the identity two failability entries and four passes of records refer to,
    for a gain in title accuracy the widened docstring already delivers. Recorded so Worker 3 sees a
    decision rather than an oversight.
- **T2 — a new unit row, `test_a_view_class_without_the_boundary_is_never_constructed`.** Asserts
  `_package_view_instance(<the new callback>) is None` **and** that the recording list is unchanged
  across the call. **A new row is owed rather than an extension of
  `::test_a_callable_view_class_that_is_not_a_class_is_never_called`:** that row's subject is the
  *class* test and its fixture is a callable non-class, while this one's subject is the *boundary
  probe* and its fixture is a real class. Folding them together would make one failure ambiguous
  between two clauses and would collapse the row separation that lets failability entries 15 and 16
  pin different answers. The existing row is otherwise unchanged — its second assertion (the factory
  recorded no call) is the only thing in the suite separating "nothing but a class is ever called"
  from a construct-first-then-validate refactor, and R1 measured that; do not touch it.
- **T3 — the coupling row, `test_the_probed_boundary_method_is_the_one_the_package_views_define`.**
  Asserts that `getattr(views_module._RequestBodyBoundaryMixin, _BOUNDARY_METHOD)` **is**
  `views_module._RequestBodyBoundaryMixin._enforce_request_boundary`, and that the probe's own
  predicate answers true for both package view classes — i.e. a genuine mount passes by
  construction. This is B-2's guard: a rename on either side of the constant fails here, by name,
  rather than silently turning every recognition into a decline.
- **T4 — the fixture change** in `### Implementation steps` step 4 (`_view_class_factory` gains the
  boundary attribute, plus its one docstring sentence). It is a test-fixture change with a
  measurement behind it, not a cosmetic one: without it, failability entry 15 measures **0** rows
  and the acceptance rule forbids the entry.

**Temp tests** under `docs/builder/temp-tests/r1b/` (gitignored; kept or promoted at review close):

- `test_w1_probe_answers.py` — **already written by this pass**, and the source of every
  probe-answer reading quoted above. Re-run it unmodified in `.venv` and at the floor rather than
  inheriting its numbers.
- A fallback-equivalence probe for the new decline route, adapted from
  `docs/builder/temp-tests/r1/test_w3p3_decline_arm.py`: drive the foreign-buildable callback
  through `[boundary, observing CSRF subclass]` and through `[observing CSRF subclass]` alone and
  confirm the two answers are **identical** (status, the `_BOUNDARY_ENFORCED` stamp as read from
  inside the chain, and the callback's own `csrf_exempt` as the chain read it). That equivalence —
  not any single value — is what says the middleware is never what dropped a check for the newly
  declined shape. See `### Non-weakening checks` item 3.
- The hot-path snippet (`### Hot-path budget`).

### Failability proof set

**Owner: Worker 2 performs and records every entry; Worker 3 audits every record and independently
re-runs a subset** (`BUILD.md` `### Who performs it`, and the plan's `## Worker-0 dispatch decision
D-1`, which settled this split for R1 after a plan assigned all ten entries to the reviewer). Use
`scripts/prove_failability.py`; its `--help` and module docstring own the manifest schema and the
flags, and this plan does not restate them.

Manifest: `docs/builder/temp-tests/r1b/proofs.json`; emitted block
`docs/builder/temp-tests/r1b/proofs.md`. Derive it **programmatically** from
`docs/builder/temp-tests/r1/proofs-pass4.json` rather than retyping, so the entries that must stay
comparable stay character-identical. Run `--check-anchors-only` **first and separately** (it is the
only step that can tell its own reference is already mutated), then the whole set in **one**
invocation. Scope for every entry: `tests/test_views.py`.

**Scope of the manifest: the two files this round writes.** Eight entries — the five whose targets
are `middleware/request_body.py` or `_boundary_ordering.py` and whose anchors are untouched, plus
the two the change moves, plus the new one.

| # | Boundary | Status in this round | Expected direction |
| --- | --- | --- | --- |
| 3 | `middleware/request_body.py::_package_view_instance #"if not getattr(view_func, _BOUNDARY_MARKER, False)"` | anchor untouched | **set-equal** to R1's 4 rows; a difference here is contamination, not improvement |
| 4 | `_boundary_ordering.py::_CsrfOrderingExemption.__bool__` (`return True`) | anchor untouched; only the module docstring and a new constant change in that file | **set-equal** (3 rows) |
| 5 | the same, opposite direction (`return False`) | anchor untouched | **set-equal** (13 rows) |
| 6 | `middleware/request_body.py::_require_boundary_before_csrf` | anchor untouched | **set-equal** (3 rows) |
| 13 | `_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (the per-request key)` | anchor untouched | **set-equal** (7 rows) |
| 12 | `::_package_view_instance` (the whole recognition after the two `getattr`s) | **anchor invalidated** by the insertion — re-anchor to the whole block including the new clause; replacement stays `    return view_class(**initkwargs)` | **GROW** — R1's 5 rows plus T1 and T2; measure, do not assume |
| 15 | `::_package_view_instance #"if not isinstance(view_class, type)"` | **anchor byte-identical and must still match exactly once**, but the measurement moves: with the probe standing, deleting the two shape clauses no longer *calls* a boundary-less factory | **STAY at its 2 rows, and only because of T4.** Without T4 it measures 0 and is `revision-needed` |
| 16 | `::_package_view_instance` — the boundary probe (new) | **new entry**; anchor is the new two-line clause, `delete: true` | at least T1 and T2 — measure |

- **0 or 1 failing rows is `revision-needed`**, and the fix is more or better-targeted rows, never a
  weaker boundary and never a recorded exception. Entry 15 is the live risk and T4 is its answer; if
  it still measures inside the band, say so and route it back rather than deleting the entry.
- Every entry records the fields `BUILD.md` `### What gets recorded` requires: the mutation as
  applied, the **listed** failing node ids (never a count), collection/setup errors **separately**
  (a valid count needs 0), the pre-mutation state of the same scope, and the revert proved by byte
  comparison. On any zero-row result name which case it is — weakly pinned, or harness-impossible —
  in those words.
- **Compare node-id *sets*, not counts**, against `docs/builder/temp-tests/r1/proofs-pass4.md` for
  the six inherited entries. R1's own lesson: the tool re-measured seven boundaries at identical
  scope and four disagreed with a reviewer's recorded counts purely because rows had landed in
  between.
- **`docs/builder/temp-tests/r1/proofs.json` (the pass-1 record) is superseded and not runnable** —
  four of its anchors match zero times. Cite `proofs-pass4.json` as the operative generation and
  never that file.

**Seven R1 entries are deliberately NOT re-run, and this is the reason.** Entries 1, 2, 7, 8 and 14
target `views.py` and `_request_body.py`; entries 9, 10 and 11 target `consumers.py`. All three files
are outside this round's write set and dirty with R1's uncommitted work, so putting them under a
mutation for a stability check trades a real risk (a failed restore on uncommitted work) for a
measurement this round can obtain otherwise. What could move their sets is only a **new row that
exercises their boundary**, and the three rows this round adds do not: T1 drives a `GET` to a route
the recognizer declines, T2 and T3 read attributes and call the recognizer directly, and none of
them posts a body, declares a charset, opens a socket or reaches the cap. Worker 2 states that
per-entry rather than in aggregate, and their unmutated green state is already recorded eight times
over as the pre-mutation baseline of the entries above. **Worker 3 may re-run any of them under its
own source carve-out if it distrusts the argument** — that is the right place for the distrust, and
the carve-out exists for it. The step-8 drift measurement mutates `views.py` once, by the same
byte-proved mechanism, because no other measurement can establish loudness.

### Fail-open shapes to read for

Read for the shape; a fail-open expression is not a branch, so a green suite says nothing about any
of these (`BUILD.md` `### Fail-open shapes`). My plan-time read is given so Worker 3 can disagree
with something specific.

- **`callable(getattr(view_class, _BOUNDARY_METHOD, None))` — the new clause, and the one the round
  owes an argument for.** A `getattr` default is in the catalogue ("a `getattr` default standing in
  for an attribute whose absence is meaningful"), so the shape needs the answer test, not a
  reassurance. It passes it: the **answer** `process_view` consumes is *a callable boundary it can
  run*, and this expression is that answer's negation, in the fail-**closed** direction. Both
  spellings of "no runnable boundary" — the attribute absent, and the attribute present but not
  callable — reach the same `return None`, and **no** incoherent input reaches a permit branch. That
  is the distinction `BUILD.md` draws: a guard written against an input spelling is a guess, a guard
  written against the answer is a boundary.
  - **Why not `hasattr`**, which would be the smaller expression: it establishes presence, not
    runnability. Measured this pass — a `DjangoGraphQLView` subclass that sets
    `_enforce_request_boundary = None` passes `hasattr` and fails `callable(getattr(..., None))`.
    Under `hasattr` that class would be recognized and `process_view` would then call `None`,
    i.e. an unhandled `500` from the very hook this round is closing one for. The failure is loud in
    the view's own path too (`::_enforce_request_boundary_once` calls the same attribute with the
    middleware uninstalled), so the recognizer is not what breaks such a mount — but it must not be
    what turns it into an uncontrolled `500` either.
  - **Why the fold into one expression is right here**, where `_CsrfOrderingExemption.__bool__`
    deliberately writes two clauses instead: that docstring's reason is that "no boundary middleware
    is handling this request" and "one is, and it has not run the boundary" are **different facts**
    that happen to want the same answer, so folding them hides the answer once a third case appears.
    Absent and not-callable are not two facts; they are one fact — *this class carries no boundary I
    can run* — with two spellings. There is no third case that wants a different answer, and the
    package's own `mutations/fields.py::_has_mutation_protocol` writes this exact shape for this
    exact question.
- **`getattr(view_func, _BOUNDARY_MARKER, False)`** (unchanged, first clause) — R1 measured its
  direction: the default converts "this callback lost its marks" into "not ours, pass through", and
  after R1's High fix that lands the request on the view-local arrangement rather than on neither.
  Unchanged here; confirm the clause's position and default are untouched.
- **`getattr(view_func, "view_class", None)` / `getattr(view_func, "view_initkwargs", None)`** —
  `None` defaults refused by the `isinstance` pair, deliberately with no `or {}`: an absent attribute
  means "not ours", never "ours, with nothing configured". Unchanged; do not "simplify" them.
- **`except TypeError`** — R1 judged this against the catalogue and by execution and found it is not
  the catalogued bare-except shape (it names the one type both mechanisms raise, the function's
  answer *is* the instance so a failure to produce one is the negative answer rather than a check
  that blew up, and the arm enforces more rather than less). B-4 keeps it; re-read it against the
  narrowed input set rather than re-deriving the verdict.
- **The probe's metaclass reach** — B-3's stated limit. Not a fail-open shape (the answer is
  `False` either way, measured); a transparency obligation.

### Non-weakening checks

Each is a contract a prior pass already accepted, which this change could trade away silently.

1. **The four tested decline routes still answer exactly as they did.** All four parametrizations of
   `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed` keep passing, and
   route 3 (`/marked-rejected-initkwargs/`) still reaches the construction arm rather than being
   refused earlier — that is B-4's whole justification, and its evidence is that entry 12's row set
   still contains all four routes and entry 16's does not contain route 3.
2. **The `_CsrfOrderingExemption` contract is untouched: a declined callback degrades the CSRF
   *class*, never the *ordering*.** Proof is threefold — entries 4, 5 and 13 set-equal to R1's;
   `::test_a_declined_callback_still_gets_a_complete_csrf_check[sync|async]` and
   `::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[sync|async]` unchanged
   and still in entries 5 and 13's sets; and a diff of `_boundary_ordering.py` against its **index**
   copy (`git show :django_strawberry_framework/_boundary_ordering.py`) showing the change confined
   to the module docstring and the new constant, with no line of `__bool__`, the `ContextVar` or
   `_CSRF_ORDERING_EXEMPTION` moved.
3. **The newly declined shape inherits the same fallback, and that is measured, not inferred.** The
   fifth route is now a declined callback, so it must land where the other four land: the view
   supplies the ordering and exactly one complete CSRF check runs. Measure it as the adapted temp
   test in `### Test additions / updates` does — the installed and uninstalled chains must answer
   **identically**. R1's lesson here is precise: reading a forged callback's own
   `csrf_exempt = False` as "declining loosens nothing" is a property of the fixture, not of the
   code; the *equivalence* of the two chains' answers is the property.
4. **Exactly one complete CSRF check, in both arrangements, still holds** — installed, the
   configured class runs and the view's continuation becomes a no-op through
   `csrf_processing_done`; uninstalled, the callback is exempt from the chain and the continuation
   *is* the check. Neither zero nor two. Nothing in this diff touches either path; confirm by the
   unchanged row sets of entries 5, 13 and 14 rather than by re-deriving it.
5. **A genuine mount is recognized at both transports.** T3 plus step 7's readings, re-taken at the
   floor. This is the check that would catch the change's worst failure mode — a probe that declines
   everything — and it is the one a suite full of decline rows would not notice on its own.
6. **The public surface does not move.** `git diff -- django_strawberry_framework/__init__.py` empty;
   `middleware/request_body.py`'s `__all__` still the single-name tuple, so the documented
   `MIDDLEWARE` string is unchanged; `_BOUNDARY_METHOD` is private, underscore-prefixed, in a private
   module, re-exported nowhere.

### Boundary count and the split question

Answered rather than assumed. **New boundaries: one** — the class-level boundary probe. Re-anchored
existing boundary: one (entry 12). Re-measured existing boundary: one (entry 15). Stability re-runs:
five. Plus one constant, seven docstring sites across two files, three new rows, one fixture
attribute and one route.

**Decided: one cohort, one pass.** One new boundary is far below `BUILD.md` `### Slice splitting`'s
"roughly five" prompt, and the partition question is moot in any case: all three writable files are
one cohort's and every test change lands in the single file `tests/test_views.py`, so no two cohorts
could run concurrently even if the work were split. The clauses in `_package_view_instance` are also
not separable — they are one recognition with one answer, ordered by dependency (marker →
bookkeeping shape → boundary → buildable), which is what makes them one unit rather than four.

One complexity note, since the static helper flags it: `scripts/review_inspect.py` reports
`::_package_view_instance` at 43 lines and **5** branch nodes, and this change makes it 6. Judged and
accepted rather than left implicit — most of the span is docstring, the four decline clauses are
flat and each answers the same `None`, and splitting the function would produce two halves neither of
which is "the answer the hook branches on" while invalidating two failability anchors. Worker 3 is
free to disagree with that judgement; it is not free to be surprised by it.

### Hot-path budget

**Declared hot-path, inherited from R1** as the plan's `## Round R1b` directs: the recognizer runs
once per marked callback in `process_view`, i.e. per request to a package mount. The probe adds one
`getattr` and one `callable()` on the recognized path and **nothing** on the path a non-package
request takes (the marker clause is still first).

**The metric is R1's recognizer micro-benchmark, reproduced.** Copy
`docs/builder/temp-tests/r1/test_w2p3_hotpath_recognizer.py` to
`docs/builder/temp-tests/r1b/test_r1b_hotpath_recognizer.py` and keep its shape exactly: both arms
in **one** process over the identical body, `timeit`, **200,000** iterations, the "before" arm a
local copy of the pre-change recognizer body (marker, two `getattr`s, the `isinstance` pair, the
`try` / `except`) and the "after" arm the shipped `_package_view_instance`. That shape is why the
before arm needs no capture ahead of the edit, and it is the same experiment R1 recorded rather than
a second one.

Run it as `uv run pytest docs/builder/temp-tests/r1b/test_r1b_hotpath_recognizer.py -s -o
addopts="" --no-cov`, at least **two** runs in `.venv` and **one** at the floor, and record metric,
exact command, iteration count, statistic, before, after, delta per call.

**R1's numbers, read from its artifact rather than restated from memory, as the comparison band:**
the standing figure is a worst reading of **~15 ns per request** against a ~314 us request; the
pass-4 readings of this identical snippet were **-0.0487 us** and **+0.0017 us** in `.venv` and
**-0.0087 us** at the floor, all inside pass 3's recorded band of **-0.0206 to +0.0295 us** per
call. Absolute per-call readings there ran 1.2-2.6x above pass 3's 0.50-0.53 us band on both
interpreters and that was the machine, not the code — which is exactly why the **delta between two
arms measured in one process** is the number and the absolute is not.

**Metric 1, R1's 400-iteration request median, is deliberately not re-captured**: both the R1 plan
and two review passes recorded that it cannot resolve a change of this size against ~313 us of
request. Say that rather than answering "not applicable", because the declaration is inherited and
an empty answer reads the same as an unmeasured one. Whether the cost is acceptable is the
maintainer's call and no worker's; no correctness boundary is weakened to buy a number back.

### Floor verification scope

**Scope: `tests/test_views.py`.** The change is on the request-lifecycle path, which is a Django
integration seam. **Owner: Worker 2's build pass.** The `## Final test-run gate` is the backstop
that confirms it happened, never a second owner, and a planned floor run no pass performed is
`revision-needed`.

Floor facts are `BUILD.md` `## Floor verification`'s, taken from there and never restated from
memory: the supported floor is **Django 5.2.0 on Python 3.10 with strawberry-graphql 0.316.0**.
`/tmp/dsf-floor` exists; **read its resolved versions before reusing it** and cite the reading — this
plan's reading is in `### Baseline, measured this pass` and is a plan-time reading, not a build-time
one. Never mutate the shared `.venv`: `uv pip install` ignores `UV_PROJECT_ENVIRONMENT` and hits
`.venv` unless every invocation carries `--python /tmp/dsf-floor/bin/python`. No `--cov*` flags.

Beyond the green focused sweep, three questions this round creates that only execution answers:

1. **`callable(getattr(<class>, name, None))` answers identically at 3.10.** Every probe reading in
   step 7 was taken on Python 3.14.2. Re-run `docs/builder/temp-tests/r1b/test_w1_probe_answers.py`
   at the floor and record the answers, including the `_enforce_request_boundary = None` subclass and
   the metaclass case.
2. **The five rows this round's subject rests on pass at the floor, named individually rather than
   hidden inside a green aggregate**: all five parametrizations of
   `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed`, plus
   `::test_a_callable_view_class_that_is_not_a_class_is_never_called`, plus T2 and T3.
3. **The hot-path delta at the floor**, per `### Hot-path budget`.

Record the scratch venv path, the resolved versions as read by
`uv pip list --python /tmp/dsf-floor/bin/python`, the focused scope run, and pass/fail.

### Implementation discretion items

Assessed and decided to belong to Worker 2:

- The **wording** of every docstring rewrite in steps 1 and 3 and in T1/T4, provided each states the
  fact this plan names.
- The names of the new fixtures, the recording list, the callback and the route string, and where in
  the fixture block they sit.
- Whether T3's two assertions are one row or two, and whether it reaches
  `_RequestBodyBoundaryMixin` through the existing `from django_strawberry_framework import views as
  views_module` idiom or a direct import.
- What callable `_view_class_factory` carries as its boundary attribute (a `lambda`, a module-level
  stub, or the mixin's own function object), provided the fixture's docstring says why it carries one.
- Iteration counts and run counts **above** the floors in `### Hot-path budget`, and whether to
  rebuild `/tmp/dsf-floor` or use a fresh scratch venv path.
- The order of the two new unit rows in the file, and whether the fallback-equivalence temp test is
  promoted to a permanent row (it is not required; item 3 of `### Non-weakening checks` is satisfied
  by the measurement).

**Nothing architectural is delegated.** B-1 through B-4 are decided above. If implementation reveals
that the probe cannot hold as specified — a *measured* obstacle, not a preference — that is a
plan-level question: set `revision-needed` naming the structural-drift pause and route it back to
Worker 1, and if the obstacle is that a file outside the write set must change, record it under
`### Notes for Worker 1 (spec reconciliation)` and stop rather than widening the set.

### Prose discipline in the diff (both `.py` files)

The docstring and test-prose rewrites state the **invariant**, never how the change came to be.
Nothing in the diff carries: a severity label; a review-round, pass or slice index; the name of any
`bld-*.md` artifact or of this round; any mention of `docs/feedback.md` or `docs/feedback2.md`
(`AGENTS.md` #4 — forbidden in code, commits and the DB alike); or a raw `path:NN` reference. A spec
Decision pointer (`spec-046 Decision 18`) is fine and is the idiom the surrounding docstrings
already use, as is naming a runtime seam or rule. Symbol references use
`path::QualifiedName` / `path::QualifiedName #"unique substring"`.

### Dispatched findings checklist

One box per finding or contract clause dispatched to this cohort. Boxes stay `- [ ]` at planning.
Worker 2 ticks `- [x]` only a box whose contract actually landed in its diff, and states any
deferral in the build report rather than ticking. Worker 1 audits every tick at final verification.

- [x] "`::_package_view_instance`'s rewritten docstring claims a property the code does not have":
      `middleware/request_body.py::_package_view_instance` #"a hook whose every other outcome is a
      controlled response" is false, because "recognition ends at *an instance was produced*, not at
      *an instance carrying the boundary*, so a callback that forges the marker onto a
      buildable-but-unrelated class reaches `view._enforce_request_boundary(request)` on a foreign
      object" (measured with `view_class = dict`, `view_initkwargs = {}`, identically at the floor).
      Closed by making the claim **true**, not by narrowing it.
- [x] "The docstring rewritten this pass claims the four routes are **the** four ways, and a fifth
      way exists and is not refused":
      `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed`
      #"The four routes are the four ways a callback". Closed by the fifth route joining the
      parametrization and the docstring becoming five.
- [x] M-B: `middleware/request_body.py::_package_view_instance` declines unless the callback's
      `view_class` itself carries the boundary method, **tested by attribute on the class, before any
      construction**; only a class that passes is constructed (B-3).
- [x] M-B: the boundary attribute name becomes the third fact `_boundary_ordering.py` holds, so the
      probe needs **no** import of `views.py` and `middleware/request_body.py` goes on importing
      neither `views.py` nor anything that imports it — proved mechanically, not asserted (B-1,
      step 6).
- [x] M-B: the five over-claiming docstring and test-prose sites R1 inventoried become **true**
      rather than narrowed, and every sentence describing the old recognition is rewritten (step 3,
      T1).
- [x] M-B: a foreign but buildable class's `__init__` is never called — pinned permanently by T2's
      recording assertion, not only by the wire answer.
- [x] The new clause carries a failability entry of its own, entries 12 and 15 are re-measured rather
      than inherited, and no entry lands in the 0-or-1-row band (`### Failability proof set`).

### Notes for Worker 1 (spec reconciliation)

R1b writes no spec or rationale text. Everything below is **R2's**, recorded here so R2's custodian
pass does not re-derive it. It supplements R1's consolidated hand-off items R2-1 through R2-13
rather than replacing them.

1. **Decision 18's rewrite is larger than adding a sentence, and the spec currently forbids what
   shipped.** Its text opens "No package middleware, no reimplemented token validation, no ordering
   system check, and no required `MIDDLEWARE` entry" — false in its first clause, true in its
   second — and its heading still reads "**via view-local CSRF re-entry**", which now names the
   *fallback* only. The rationale companion's `### Decision 18` compounds it: it lists as a
   **rejected** alternative "A narrow package middleware placed before `CsrfViewMiddleware`, plus a
   system check that detects missing or wrong ordering", which is what shipped minus the "required"
   — the withdrawable exemption is what makes the entry optional, and what shipped is a startup
   raise from `__init__`, not a Django system check. R2 either moves that bullet to a keyed change
   record naming the round that adopted it, or keeps it rejected in its *original* form and states
   what the shipped design does differently. This round changes none of it.
2. **The recognition sentence gains a third clause.** Proposed contract wording, for R2 to shape:
   *the boundary middleware runs a package view's boundary only for a callback whose `view_class`
   carries that boundary, tested by attribute on the class before anything is constructed; it never
   calls anything that is not a class to try, and it builds nothing it has not established a
   boundary on. Every other callback is declined and keeps the view-local arrangement.* R1 already
   measured the first two clauses (entry 12 at 5 rows; entry 15 at 2 rows plus two named permanent
   rows); this round measures the third. R1's standing instruction holds: **do not** write the
   `view_initkwargs` `dict` test as a symmetric guard — removing it makes the middleware run the
   boundary for a non-`dict` mapping, so it is a narrowing preference, not a bound.
3. **Record M-B's rejected alternatives beside the decision**, each with its one-line reason, since
   `worker-1.md` `## Review-round custody` requires a settled contract choice to document that it
   was chosen rather than defaulted into: probing the built instance instead of the class (closes
   the `500`, leaves the foreign constructor running, which the suite already forbids); declaring
   the forged marker out of contract (more text than the fix, and an exception to Decision 7's
   no-unrelated-`500` doctrine); refusing it outright (contradicts the accepted state-enumeration
   contract that every unforeseen state answers "no" and falls back).
4. **State the property positively.** With the probe landed, Decision 18 can assert that **every**
   outcome of the boundary middleware's `process_view` is a controlled response — a refusal, a
   stamp, or a decline — rather than carving out a documented gap. That is the sentence the five
   over-claiming sites were over-claiming, and after this round it is simply true.
5. **The probe's limit belongs in the rationale, not as a spec carve-out.** A class attribute probe
   consults the metaclass, and forging the package's private marker stays outside the threat model
   (the spec-045 stance that no in-interpreter walk is a trust boundary against a party already
   running code in the process). The probe exists so the hook's outcomes are controlled, not to
   defend against a forger. Keep those two sentences distinct; conflating them is what would invite
   a future round to over-promise.
6. **No glossary or terms-CSV work is created by this round.** `_BOUNDARY_METHOD` is private and in
   a private module; `docs/GLOSSARY.md`'s `## \`DjangoGraphQLView\``, `## Request-body cap` and
   `## UTF-8 wire contract` entries describe the boundary rather than the recognizer and need no
   change on this account. R3's V1/V5/V6 obligations are unaffected, and `docs/TREE.md`'s
   regenerate already gains its `_boundary_ordering.py` row from R1 (hand-off item R3-6).
7. **Nothing here bears on M-A or on R3's other items.** No `examples/**` path, no doc, no generated
   file and no spec sentence is touched, so R3-2's superseded re-pin estimate, the rationale's
   Decision 18 bullet and R3's live-tier opportunity are all exactly where R1 left them.
8. **For the final gate:** this round's floor run and hot-path number live in the build report's
   `### Floor verification` and `### Hot-path budget`, and the operative failability manifest is
   `docs/builder/temp-tests/r1b/proofs.json` with `docs/builder/temp-tests/r1/proofs-pass4.json` as
   the comparison generation.

---

## Build report (Worker 2)

Everything M-B and the plan specify landed in this one pass; nothing is deferred and no plan-level
architectural call (B-1 through B-4) moved, so this is not a structural-drift pause. Four plan-time
claims were reproduced by my own measurement before being relied on, and two plan-time readings came
out different from the plan's - both recorded below under `### Notes for Worker 1 (spec
reconciliation)` as drift rather than buried here.

**SHA-256 of the three writable files, recorded before the first edit** (`### Implementation steps`
step 0), so the production delta is confirmable rather than asserted:

| File | before this pass | after this pass |
| --- | --- | --- |
| `django_strawberry_framework/middleware/request_body.py` | `6ef3ad5e35ebc9e710f3e79f55b7d9ffdba02c476a821cc511ae729042c9c20c` | `7154891a17fcc10b05165349223f064d7729f159f3f1d919806911d493d357a3` |
| `django_strawberry_framework/_boundary_ordering.py` | `b2c25d9a66a6090c4f5c5198f24b0b4cea3c2007db79f1aece0837e44d23b298` | `7b3d9e51b7fb7ecc4cd578139ad3db2509f638884c20f9c6d637f43645c67bee` |
| `tests/test_views.py` | `b1cfe55d50a6aa631d520b258ccdbddf2dbb1fe1e9b04036ccba04ecad43427a` | `477de139ee5fe8aa8b133d62a431cbc08749f36876447d1d8e719d838eb3bbdc` |

The two "before" values for the production files are the ones the R1 pass-4 review recorded, so the
pass started from exactly the bytes R1 closed on. **The three files R1 left dirty and this round may
not touch are byte-unmoved**, read at the end of the pass and identical to R1's recorded values:
`views.py` `e8aeb156550fc45a...`, `consumers.py` `1bdf298c473fd1a0...`, `_request_body.py`
`2c1fd48618d4b01c...`. `consumers.py` is additionally still **byte-identical to `HEAD`**
(`git show HEAD:...` into a scratch path outside the repo, then `cmp` - exit 0), which is the
property four prior passes recorded and this one preserves.

One SHA in the auxiliary records below will not match the table: the entry-15-without-T4 run and the
first full manifest run were taken while `middleware/request_body.py` was at
`4a3098e1a8c05fd2...`. The only change between that and the shipped `7154891a...` is one docstring
sentence (`### Implementation notes`, last bullet), so **the whole manifest and the drift auxiliary
were re-run against the shipped bytes** and both re-runs reproduced every row set identically. The
records embedded below are the re-runs.

### Files touched

Grounded in `git status --short` taken after the final `ruff format` / `ruff check --fix`
invocations, not from memory:

```
AM django_strawberry_framework/_boundary_ordering.py
 M django_strawberry_framework/_request_body.py
 M django_strawberry_framework/middleware/request_body.py
 M django_strawberry_framework/views.py
 M docs/builder/build-046-transport_security-0_0_15.md
 M examples/fakeshop/apps/kanban/constants.py
 M tests/test_routers.py
 M tests/test_views.py
?? docs/builder/bld-046-r1-remediation_review.md
?? docs/builder/bld-046-r1b-recognition_contract.md
```

Written by this pass:

- `django_strawberry_framework/_boundary_ordering.py` - the third fact. `_BOUNDARY_METHOD =
  "_enforce_request_boundary"` added between `_BOUNDARY_ENFORCED` and
  `_boundary_middleware_request`, in B-1's exact form. The module docstring's title and its "two
  facts per request" sentence rewritten (a third fact makes both false, and the third is *static*,
  not per-request), plus a fourth `The protocol` paragraph for the new constant. **No import added**
  - proved three ways below.
- `django_strawberry_framework/middleware/request_body.py` - the clause and the prose. One import
  name added to the existing `_boundary_ordering` block, and B-3's clause inserted as its own third
  statement in `::_package_view_instance`, after the two `isinstance` tests and before the
  construction `try`. Docstring rewrites at every site the plan's step 3 names. Nothing else in the
  module's executable surface changed: `process_view`'s `view._enforce_request_boundary(request)` is
  still a direct call (B-2), and `__call__`, `__acall__`, `__init__` and
  `::_require_boundary_before_csrf` are untouched.
- `tests/test_views.py` - `_BOUNDARY_METHOD` imported; the recording foreign class, its marked
  callback and its urlpattern added; `_view_class_factory` given the boundary attribute (T4) via a
  named module-level stub; T1's fifth route and docstring rewrite; T2 and T3 added.

**Unchanged and not written by this pass**, listed because a reader of the `git status` above will
see them dirty: `_request_body.py`, `views.py`, `consumers.py`, `tests/test_routers.py`,
`examples/fakeshop/apps/kanban/constants.py` and the build plan are R1's and Worker 0's landed
uncommitted work. Nothing was reverted, stashed, checked out or restored, and **nothing new was
staged** - `_boundary_ordering.py`'s `A` is W-1's authorized staging, now reading `AM` because this
pass wrote to the worktree copy. `git add` was not run.

### Tests added or updated

- `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-foreign-view-class/]`
  (T1) - the fifth route joins the existing parametrization rather than earning a test of its own.
  It pins that a marked callback whose `view_class` is a real class, buildable with exactly the
  keywords its `view_initkwargs` names, and carrying no boundary, is answered `200` with a
  `"marked, "` body instead of raising out of `process_view`. Without the probe it fails on an
  unhandled `500` - measured, it is one of entry 16's two rows. The node-id stem is deliberately
  kept (M-B and the build plan's `## Round R1b` both name this test as the fifth route's home, and
  two failability entries plus four passes of records refer to that identity); the docstring is
  rewritten to five routes and its subject widened honestly to "a callback the middleware cannot run
  a boundary for", since the fifth is one the recognizer *declines to build* rather than one it
  *cannot* build.
- `tests/test_views.py::test_a_view_class_without_the_boundary_is_never_constructed` (T2) - asserts
  `_package_view_instance(<the new callback>) is None` **and** that
  `_FOREIGN_VIEW_CONSTRUCTIONS` is unchanged across the call. A new row rather than an extension of
  `::test_a_callable_view_class_that_is_not_a_class_is_never_called`, because that row's subject is
  the class test and its fixture is a callable non-class while this one's subject is the boundary
  probe and its fixture is a real class: folding them would make one failure ambiguous between two
  clauses and would collapse the separation entries 15 and 16 now measure. As in R1, the
  delta-form assertion (`len(...) == constructions_before`, never `not ...`) is what makes the row
  pin the contract rather than today's execution order - and, stated plainly so no reviewer
  over-reads it, **the construction-count assertion is not what the entry-16 mutant fails on**: with
  the probe deleted the first assertion fails first. The count assertion is the row's guard against
  a future probe-the-instance refactor.
- `tests/test_views.py::test_the_probed_boundary_method_is_the_one_the_package_views_define` (T3) -
  B-2's guard, and the row that would catch the change's worst failure mode (a probe that declines
  everything). Asserts `getattr(mixin, _BOUNDARY_METHOD) is mixin._enforce_request_boundary` and
  that the predicate answers true for both view classes. Measured: it fails, by name, under either
  direction of the drift (the drift auxiliary below).
- `tests/test_views.py::_view_class_factory` (T4) - the fixture now carries the boundary method's
  name, set to a named module-level stub `_boundary_the_factory_carries`, with one docstring
  paragraph stating why. **This is not cosmetic and it is measured:** without it, manifest entry 15
  falls to **0 rows** and the acceptance rule forbids the entry. The 0-row reading was taken
  deliberately, as a separate auxiliary run, before T4 was written (below).

Baseline and totals, every one a `--no-cov` run:

| Scope | before | after |
| --- | --- | --- |
| `uv run pytest tests/test_views.py --no-cov` | **197 passed** (the plan's baseline, re-measured this pass) | **200 passed** |
| `uv run pytest tests/test_views.py examples/fakeshop/test_query/test_transport_api.py --no-cov` | - | **269 passed** |
| `uv run pytest examples/fakeshop/test_query/test_transport_api.py --no-cov` | - | **69 passed** |
| `uv run pytest tests/middleware/ --no-cov` | - | **17 passed** |
| `uv run pytest tests/ --no-cov` (the staleness sweep) | - | **4521 passed, 38 skipped** |

### Validation run

- `uv run ruff format <the three files>` - pass (`3 files left unchanged`, then `1 file left
  unchanged` after the one docstring correction). Scoped to this pass's own files, never `.`.
- `uv run ruff check --fix <the same three files>` - pass (`All checks passed!`). No fix was
  applied; nothing to autofix.
- `git status --short` after both - quoted verbatim under `### Files touched`. Every modified path
  is slice-intended or R1's / Worker 0's landed dirty work; nothing unexpected appeared, so there is
  nothing to stop-and-report and nothing was reverted.
- **`pre-commit` is not installed in this environment**, so its four `language: system` local hooks
  were run individually rather than skipped, as R1's pass 4 established:
  - `kanban-tracked-path-constants` - `uv run python
    scripts/build_kanban_tracked_path_constants.py`, with `examples/fakeshop/apps/kanban/
    constants.py` copied to an outside-the-repo scratch path first and byte-compared after: `cmp`
    exit 0, SHA-256 `6761fadb49c4f285...` on both sides. **This round adds no tracked file, so the
    generated allowlist comes out byte-unchanged**, which is the property that stops the
    maintainer's commit being rolled back.
  - `source-layout` - `uv run python scripts/check_trailing_commas.py --check <the three files>`,
    exit **0**. `docs/builder/` is excluded from the markdown link-scaffold check, so this artifact
    owes no link-definition block.
  - `ruff-format` and `ruff-check` in read-only form over the same three files: `3 files already
    formatted`, `All checks passed!`.
  - ASCII-only re-verified independently of the hook, by byte scan: all three files carry no byte
    above 127.
- `uv run python scripts/review_inspect.py django_strawberry_framework/middleware/request_body.py
  --output-dir docs/shadow` - run because the plan's complexity note turns on its output.
  **`repeated string literals: 0`**, `Django / ORM markers: None`, imports unchanged apart from the
  one name added to the existing first-party block, and `getattr()` now called 4x where it was 3x.

### Failability proofs

**Manifest: `docs/builder/temp-tests/r1b/proofs.json`, 8 entries, derived programmatically from
`docs/builder/temp-tests/r1/proofs-pass4.json`** rather than retyped - the six inherited entries were
copied as JSON objects and re-serialized, and the six were then asserted **character-identical** to
pass 4's by sorted-key JSON comparison, so set-equality below means "nothing moved" rather than
"nothing was mistyped". Two changes:

- **entry 12 re-anchored**, as the plan requires: the insertion invalidated its six-line anchor, so
  the anchor is now the whole eight-line block including the probe, replacement unchanged
  (`    return view_class(**initkwargs)`). Its label and mutation prose were updated to name the
  probe, because a label naming a mutation it is no longer about is the false reading R1's pass-4
  review filed a Medium about.
- **entry 16 added**: the boundary probe, anchored on its own two-line statement, `delete: true`.
  This is the round's one new boundary, and giving the clause its own statement (B-3) is what gives
  it its own anchor.

`--check-anchors-only` was run **first and separately** (**exit 0**: all 8 anchors matched exactly
once *before any copy was taken*, which is also what says no prior pass left a live mutation). The
full set then ran in **one** invocation, **exit 0**: every entry proved, **no boundary weakly
pinned**, **0 collection/setup errors** anywhere, every pre-mutation baseline **200 passed** at exit
0, and every restore proved by `filecmp.cmp(shallow=False)` plus SHA-256 against the runner's
pre-mutation copy. Scratch root outside the repository
(`.../scratchpad/fail-main2`); it holds only `pristine/` and no `ACTIVE-MUTATION.json`.

**Node-id set movement against R1's pass 4, computed by symmetric difference over the parsed lists
rather than by comparing counts:**

| # | pass 4 | R1b | Direction |
| --- | --- | --- | --- |
| 3 | 4 | **4** | **set-equal** - a movement here would be contamination |
| 4 | 3 | **3** | **set-equal** |
| 5 | 13 | **13** | **set-equal** |
| 6 | 3 | **3** | **set-equal** |
| 13 | 7 | **7** | **set-equal** |
| 12 | 5 | **7** | **grew (+2, none lost)** - gained exactly T1's fifth route and T2, as the plan predicted |
| 15 | 2 | **2** | **set-equal**, and only because of T4 - measured at **0** without it |
| 16 | - | **2** | new: T1's fifth route and T2 |

Three readings the sets give that the counts would hide:

- **Entry 15's stability is bought by T4, and that is a measurement, not an argument.** Before T4 was
  written, entry 15 was run as a one-entry auxiliary manifest
  (`docs/builder/temp-tests/r1b/proofs-entry15-without-T4.json`, separate scratch root, separate
  `--output`, exit **1** as expected) and measured **0 rows, 0 errors, pre-mutation baseline 200
  passed**. With the probe standing and the factory carrying no boundary, deleting the two shape
  clauses no longer *calls* the factory - the probe refuses it one line later - so the two rows that
  pinned the clauses stop failing. T4 supplies the one input that still distinguishes them: a
  callable non-class that *does* carry the boundary. With T4 the entry is back to its original two
  rows, the same two node ids pass 4 recorded. **The zero was measured before the fix rather than
  predicted after it**, which is what makes T4's justification a reading instead of a plausible
  story.
- **Entry 12 grew and entry 16 is a strict subset of it, which is the evidence they are not
  redundant.** Entry 12 removes the shape tests, the probe and the construction at once, so all five
  routes plus both unit rows fail under it. Entry 16 removes only the probe, and its two rows are
  exactly the two shapes the probe alone refuses. Decisively, **route 3
  (`/marked-rejected-initkwargs/`) is in entry 12's set and is NOT in entry 16's** - which is B-4's
  whole justification measured rather than argued: that route still reaches the construction arm
  after the change, so removing the arm would restore an unhandled `500` for a route the suite
  already pins.
- **Nothing else moved.** Entries 3, 6, 12, 15 and 16 all mutate `middleware/request_body.py` and
  entries 4, 5 and 13 all mutate `_boundary_ordering.py` - the two files this round writes - and
  every inherited one of them is set-equal, so neither the new constant, the new clause nor seven
  docstring rewrites changed any other boundary's measurement.

**Seven R1 entries were deliberately not re-run, and per the plan this is stated per entry rather
than in aggregate.** Entries 1, 2, 7 and 14 target `views.py`; entry 8 targets `_request_body.py`;
entries 9, 10 and 11 target `consumers.py`. All three files are outside this round's write set and
dirty with R1's uncommitted work, so putting them under a mutation for a stability check trades a
real risk (a failed restore on uncommitted work) for a measurement obtainable otherwise. What could
move their sets is only a new row that exercises their boundary, and none of this round's three rows
does:

- **T1** drives a bare `GET` to `/marked-foreign-view-class/` through
  `[passthrough, boundary, rejecting CSRF]`. No body, no declared charset, no `Content-Type`, no
  multipart envelope, no socket, and the cap is never reached - so entries 1 and 2 (the charset
  declaration guard and its GET/multipart carve-out) cannot see it, entry 7
  (`::_enforce_request_boundary_once`) is never entered because the callback is declined and the
  route's view is a plain function, entry 8 (`_measured_remaining`) needs a measurable body, entry 14
  (the two `csrf_protect` continuations) needs a package mount, and entries 9-11 need a WebSocket.
- **T2** calls `_package_view_instance` directly with no request at all.
- **T3** reads two class attributes and calls `callable()` twice.

Their unmutated green state is recorded eight times over as the pre-mutation baseline of the entries
that were run (**200 passed**, exit 0, each time). Worker 3 may re-run any of them under its own
source carve-out if it distrusts this argument - that is the right place for the distrust.

The emitted record follows verbatim, every measured field filled in by the runner. Nothing in it is
a zero-row entry, so no `why 0` judgement is owed.

Procedure, mechanized by `scripts/prove_failability.py`: the target is copied to a scratch path OUTSIDE the repo before any mutation; the mutation site is located by an exact anchor asserted to match exactly once (any other count aborts the entry without writing); the same focused scope is run unmutated first, so rows already failing before the mutation are differenced out of the count; both runs' pytest exit codes are read, because a run that collected nothing or blew up emits no `FAILED` lines and would otherwise be recorded as a measured zero; both runs use `--no-cov`; the file is restored from the pre-mutation copy in a `finally` and the restore is proved by `filecmp.cmp(shallow=False)` plus a SHA-256 comparison. One boundary at a time, restored before the next. `git` is never invoked - the tree is legitimately dirty, so an empty `git diff` is unachievable and forcing one would destroy the build's own work.

| # | Boundary | File mutated | Mutation applied | Rows failed | Errors | Scope as run | Restore proof |
|---|---|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not getattr(view_func, _BOUNDARY_MARKER, False)"` | `django_strawberry_framework/middleware/request_body.py` | `if not getattr(view_func, _BOUNDARY_MARKER, False):` -> `if True:` - builder's description (unverified prose): the recognition made unconditionally negative: _package_view_instance always answers None, so the chain never runs the boundary and never stamps the request | **4** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 7154891a17fcc10b... == 7154891a17fcc10b... (vs pre-mutation copy) |
| 2 | `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__` | `django_strawberry_framework/_boundary_ordering.py` | `request = _boundary_middleware_request.get() return request is None or not getattr(request, _BOUNDARY_ENFORCED, False)` -> `return True` - builder's description (unverified prose): the withdrawal removed: the exemption is always truthy, so the configured CSRF middleware always skips the callback | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 7b3d9e51b7fb7ecc... == 7b3d9e51b7fb7ecc... (vs pre-mutation copy) |
| 3 | `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (opposite direction)` | `django_strawberry_framework/_boundary_ordering.py` | `request = _boundary_middleware_request.get() return request is None or not getattr(request, _BOUNDARY_ENFORCED, False)` -> `return False` - builder's description (unverified prose): the exemption is always withdrawn, so the view-local arrangement loses its ordering on a chain that does not supply one | **13** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 7b3d9e51b7fb7ecc... == 7b3d9e51b7fb7ecc... (vs pre-mutation copy) |
| 4 | `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf` | `django_strawberry_framework/middleware/request_body.py` | `boundary_index = csrf_index = None` -> `return boundary_index = csrf_index = None` - builder's description (unverified prose): the ordering audit short-circuited before it reads MIDDLEWARE, so a misordered chain is accepted at startup | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 7154891a17fcc10b... == 7154891a17fcc10b... (vs pre-mutation copy) |
| 5 | `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (the per-request key)` | `django_strawberry_framework/_boundary_ordering.py` | `request = _boundary_middleware_request.get() return request is None or not getattr(request, _BOUNDARY_ENFORCED, False)` -> `return _boundary_middleware_request.get() is None` - builder's description (unverified prose): the per-request key removed and the defective predecessor restored: the exemption is withdrawn because a boundary middleware is handling the request, whether or not it ran the boundary for it | **7** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 7b3d9e51b7fb7ecc... == 7b3d9e51b7fb7ecc... (vs pre-mutation copy) |
| 6 | `django_strawberry_framework/middleware/request_body.py::_package_view_instance (the whole recognition after the two getattrs: both bookkeeping-shape tests, the boundary probe and the construction attempt)` | `django_strawberry_framework/middleware/request_body.py` | `if not isinstance(view_class, type) or not isinstance(initkwargs, dict): return None if not callable(getattr(view_cla...` -> `return view_class(**initkwargs)` - builder's description (unverified prose): the whole recognition after the two getattrs deleted - both isinstance clauses, the boundary probe and the construction attempt - so a marked callback's view_class and view_initkwargs are dereferenced and splatted unguarded and any callback the class cannot be built from, or that carries no boundary, becomes an unhandled 500 out of process_view | **7** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 7154891a17fcc10b... == 7154891a17fcc10b... (vs pre-mutation copy) |
| 7 | `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not isinstance(view_class, type)"` | `django_strawberry_framework/middleware/request_body.py` | deleted: `if not isinstance(view_class, type) or not isinstance(initkwargs, dict): return None` - builder's description (unverified prose): the two bookkeeping-shape tests deleted with the construction attempt left standing, so a view_class that is callable and is not a class is CALLED instead of refused and process_view reads the boundary off whatever it answers | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 7154891a17fcc10b... == 7154891a17fcc10b... (vs pre-mutation copy) |
| 8 | `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not callable(getattr(view_class, _BOUNDARY_METHOD, None))"` | `django_strawberry_framework/middleware/request_body.py` | deleted: `if not callable(getattr(view_class, _BOUNDARY_METHOD, None)): return None` - builder's description (unverified prose): the class-level boundary probe deleted, so a marked callback whose view_class is a real, buildable class carrying no body boundary is CONSTRUCTED and process_view then reads the boundary method off a foreign instance | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 7154891a17fcc10b... == 7154891a17fcc10b... (vs pre-mutation copy) |

Verdicts:

1. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not getattr(view_func, _BOUNDARY_MARKER, False)"` - pinned
2. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__` - inside Worker 3's mandatory re-run floor (<= 3 rows)
3. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (opposite direction)` - pinned
4. `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf` - inside Worker 3's mandatory re-run floor (<= 3 rows)
5. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (the per-request key)` - pinned
6. `django_strawberry_framework/middleware/request_body.py::_package_view_instance (the whole recognition after the two getattrs: both bookkeeping-shape tests, the boundary probe and the construction attempt)` - pinned
7. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not isinstance(view_class, type)"` - inside Worker 3's mandatory re-run floor (<= 3 rows)
8. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not callable(getattr(view_class, _BOUNDARY_METHOD, None))"` - inside Worker 3's mandatory re-run floor (<= 3 rows)

Failing node ids, per boundary (the count above is `len()` of this list):

1. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not getattr(view_func, _BOUNDARY_MARKER, False)"`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 4 failed, 196 passed in 1.74s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 200 passed in 1.67s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[sync]`
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[async]`
   - `tests/test_views.py::test_the_view_does_not_measure_a_body_the_chain_already_measured[sync]`
   - `tests/test_views.py::test_the_view_does_not_measure_a_body_the_chain_already_measured[async]`
2. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__`
   - file mutated: `django_strawberry_framework/_boundary_ordering.py`
   - pytest summary: `======================== 3 failed, 197 passed in 1.65s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 200 passed in 1.65s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[sync]`
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[async]`
   - `tests/test_views.py::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`
3. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (opposite direction)`
   - file mutated: `django_strawberry_framework/_boundary_ordering.py`
   - pytest summary: `======================== 13 failed, 187 passed in 1.70s ========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 200 passed in 1.70s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark[sync]`
   - `tests/test_views.py::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark[async]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[sync]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[async]`
   - `tests/test_views.py::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[sync]`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[async]`
   - `tests/test_views.py::test_the_same_two_mounts_parse_nothing_without_the_middleware_either[sync]`
   - `tests/test_views.py::test_the_same_two_mounts_parse_nothing_without_the_middleware_either[async]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[sync]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[async]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[sync]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[async]`
4. `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 3 failed, 197 passed in 1.63s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 200 passed in 1.63s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_chain_that_lists_the_boundary_after_csrf_is_refused_at_startup`
   - `tests/test_views.py::test_a_boundary_subclass_listed_after_csrf_is_refused_at_startup`
   - `tests/test_views.py::test_the_first_csrf_entry_is_the_one_the_ordering_is_measured_against`
5. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (the per-request key)`
   - file mutated: `django_strawberry_framework/_boundary_ordering.py`
   - pytest summary: `======================== 7 failed, 193 passed in 1.68s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 200 passed in 1.65s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[sync]`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[async]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[sync]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[async]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[sync]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[async]`
6. `django_strawberry_framework/middleware/request_body.py::_package_view_instance (the whole recognition after the two getattrs: both bookkeeping-shape tests, the boundary probe and the construction attempt)`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 7 failed, 193 passed in 1.76s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 200 passed in 1.70s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-no-view-class/]`
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-bad-initkwargs/]`
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-rejected-initkwargs/]`
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-callable-view-class/]`
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-foreign-view-class/]`
   - `tests/test_views.py::test_a_callable_view_class_that_is_not_a_class_is_never_called`
   - `tests/test_views.py::test_a_view_class_without_the_boundary_is_never_constructed`
7. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not isinstance(view_class, type)"`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 2 failed, 198 passed in 1.75s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 200 passed in 1.72s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-callable-view-class/]`
   - `tests/test_views.py::test_a_callable_view_class_that_is_not_a_class_is_never_called`
8. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not callable(getattr(view_class, _BOUNDARY_METHOD, None))"`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 2 failed, 198 passed in 1.68s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 200 passed in 1.66s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-foreign-view-class/]`
   - `tests/test_views.py::test_a_view_class_without_the_boundary_is_never_constructed`

A boundary whose removal fails 0 or 1 rows is **weakly pinned** and is `revision-needed` per `docs/builder/BUILD.md` - the fix is more or better-targeted rows, never a weaker boundary. A boundary at 3 rows or fewer is inside Worker 3's mandatory independent re-run floor. A proof carrying collection or setup errors, or whose pytest run exited anything but 0 or 1 (nothing collected, interrupted, internal error, usage error), is not a valid count at all - and a 0 from such a run is not a zero-row result: resolve it and re-run.

Every `<fill in ...>` above is a judgement no tool can make and MUST be replaced by hand before this subsection is submitted: weakly pinned and harness-impossible are the two possible readings of a zero-row result and they prescribe opposite responses (more rows, versus a production-call-site invariant assertion plus a recorded harness limitation), so a record that does not name one reads as self-contradictory.

#### Auxiliary: the drift-guard loudness, measured (B-2)

`### Implementation steps` step 8 asks for the coupling's loudness to be **measured** rather than
asserted, through a transient byte-proved mutation. Manifest
`docs/builder/temp-tests/r1b/proofs-drift.json`, separate scratch root
(`.../scratchpad/fail-drift2`), separate `--output`; anchors checked separately first (**exit 0**,
both matched exactly once), run **exit 0**, both restores byte-proved, no marker left behind.

Two entries rather than the plan's one, because the plan's mutation does not model the drift it
names - see `### Notes for Worker 1 (spec reconciliation)` item 3:

| Direction | Mutation | Rows | Reading |
| --- | --- | --- | --- |
| the constant drifts (B-2 direction 2) | `_BOUNDARY_METHOD = "_enforce_request_boundary"` -> `..._drifted` in `_boundary_ordering.py` | **5** | exactly the plan's prediction: entry 3's four rows plus T3 |
| the `def` line is renamed (the plan's own mutation) | `def _enforce_request_boundary(self, ...)` -> `def _enforce_request_boundary_drifted(self, ...)` in `views.py` | **33** | a strict superset, and *louder* than direction 1 for a reason worth naming |

- **The constant's direction is the faithful one-block model**, and it lands in this round's own
  write set rather than in `views.py`. Its five rows are
  `::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[sync|async]`,
  `::test_the_view_does_not_measure_a_body_the_chain_already_measured[sync|async]` and
  `::test_the_probed_boundary_method_is_the_one_the_package_views_define`. So the probe refusing
  every genuine mount is caught by four behavioural rows *and* named directly by T3. It cannot be
  silent.
- **The `def`-line rename fails 33 rows, and the extra 28 are not the coupling.** Renaming the
  definition alone also orphans the mixin's own internal caller
  (`views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once`
  `#"self._enforce_request_boundary(request)"` - measured, exactly one internal caller) and the
  three direct calls in `tests/test_views.py`, so every view-local request path breaks too. That is
  strictly louder than the drift, which is a fine thing to know and a poor model of it; the constant
  entry is the model, and both are recorded so the reading is not overstated in either direction.
  `views.py` came back **byte-identical**: SHA-256 `e8aeb156550fc45a...` before and after, plus the
  runner's own `filecmp` + SHA proof against its pre-mutation copy.
- Direction 3 of B-2 ("both renamed, `process_view`'s direct call not") needs no separate mutation:
  the `def`-line entry already exhibits an even louder version of it, since a missing attribute on a
  recognized instance is what its 33 rows are mostly made of.

The drift auxiliary's emitted record is at `docs/builder/temp-tests/r1b/proofs-drift.md` (gitignored
scratch, so its table is summarized above rather than reproduced twice); its `run-drift.log` sits
beside it.

#### The no-import property, proved three ways rather than asserted

- **Reading 1 - `grep -n 'import' django_strawberry_framework/_boundary_ordering.py`.** The only
  import statements are `from __future__ import annotations` (line 45), `from contextvars import
  ContextVar` (47), `from typing import TYPE_CHECKING` (48) and the `TYPE_CHECKING`-guarded `from
  django.http import HttpRequest` (51). Standard library plus one type-checking-only Django name;
  **the addition added no import**. The remaining matches are prose in the docstring and the new
  `#:` comment.
- **Reading 2 - neither of the two modules imports the other.**
  `grep -cE '^\s*(from|import)\s+.*views' django_strawberry_framework/middleware/request_body.py`
  -> **0**. The other direction needs a corrected command; see
  `### Notes for Worker 1 (spec reconciliation)` item 1. Measured on import statements only,
  `grep -nE '^\s*(from|import)\s+.*(middleware|request_body)' django_strawberry_framework/views.py`
  returns two lines, and **neither is a middleware import**: `from
  django_strawberry_framework._request_body import body_exceeds_limit` and `from
  django_strawberry_framework.conf import max_request_body_bytes_setting`. `views.py` imports no
  module under `middleware/`.
- **Reading 3 - by execution, since a grep cannot see a transitive import.** A fresh interpreter,
  `django.setup()`, then `sys.modules` differenced across `import
  django_strawberry_framework._boundary_ordering`:

  ```
  modules gained: ['django_strawberry_framework._boundary_ordering']
    django_strawberry_framework.views in sys.modules: False; gained on this account: False
    strawberry.django.views in sys.modules: False; gained on this account: False
  ```

  One module gained, and neither view module is even present. The probe therefore costs no import of
  `views.py`, which is B-1's whole reason and M-B's named requirement.

#### A genuine mount passes the probe by construction, at both transports

`docs/builder/temp-tests/r1b/test_w1_probe_answers.py` re-run **unmodified** rather than inheriting
the plan's numbers, in `.venv` (Python 3.14.2) and at the floor (Python 3.10.19) - **identical
answers on both**:

```
carries_boundary(DjangoGraphQLView) = True
carries_boundary(AsyncDjangoGraphQLView) = True
carries_boundary(_RequestBodyBoundaryMixin) = True
carries_boundary(dict (M-B's measured forgery)) = False
carries_boundary(_ForeignBuildableView) = False
carries_boundary(_DisabledBoundary (attr present, None)) = False
carries_boundary(a function carrying the attribute) = True
carries_boundary(MappingProxyType) = False
_ForeignBuildableView constructions before any build: []
carries_boundary(_MetaProbed) = False
metaclass __getattr__ invocations: ['_enforce_request_boundary']
```

So B-3's stated limit is real and bounded: one metaclass `__getattr__` invocation, answer `False`,
no `__init__`. It is stated in the shipped docstring and nothing defends against it.

#### The `callable` shape versus `hasattr`, reproduced because it changed the design

`docs/builder/temp-tests/r1b/test_w2_hasattr_vs_callable.py`, written this pass, tabulates **both**
predicates over the same candidates and then drives the consequence. Identical in `.venv` and at the
floor:

```
candidate                                  hasattr  callable(getattr(..., None))
DjangoGraphQLView                          True     True
AsyncDjangoGraphQLView                     True     True
_RequestBodyBoundaryMixin                  True     True
dict                                       False    False
_ForeignButBuildableView                   False    False
MappingProxyType                           False    False
_DisabledBoundary (attr present, None)     True     False
```

`_DisabledBoundary` - a `DjangoGraphQLView` subclass setting `_enforce_request_boundary = None` - is
**the only candidate the two predicates disagree on**, and under `hasattr` it would be *recognized*.
The consequence was driven rather than reasoned: calling the recognized-but-uncallable boundary
exactly as `process_view` does raises `TypeError("'NoneType' object is not callable")`, on both
interpreters - the same uncontrolled `500` out of the same hook this round exists to close. So
`callable(getattr(view_class, _BOUNDARY_METHOD, None))` is required and `hasattr` would have
reintroduced the defect in a second spelling. This confirms the plan's fail-open reading: the guard
is written against the **answer** (*a callable boundary I can run*), and both spellings of "no
runnable boundary" reach the same `return None`, so no incoherent input reaches a permit branch.

#### Non-weakening checks, each answered by a measurement

1. **The four previously tested decline routes still answer exactly as they did**, and route 3 still
   reaches the construction arm: all five parametrizations pass, and route 3 is in entry 12's row set
   and absent from entry 16's - the evidence the plan itself nominates for B-4.
2. **The `_CsrfOrderingExemption` contract is untouched.** Entries 4, 5 and 13 set-equal to R1's;
   `::test_a_declined_callback_still_gets_a_complete_csrf_check[sync|async]` and
   `::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[sync|async]` are still
   in both entry 5's and entry 13's sets (verified by parsing the sets, not by re-reading the rows);
   and a `diff -u` of `_boundary_ordering.py` against its **index** copy
   (`git show :django_strawberry_framework/_boundary_ordering.py` into an outside-the-repo scratch)
   shows exactly three hunks - the docstring title/sentence, the new `The protocol` paragraph, and
   the new constant with its comment. **No line of `__bool__`, the `ContextVar` or
   `_CSRF_ORDERING_EXEMPTION` moved.**
3. **The newly declined shape inherits the same fallback, measured on both chains.**
   `docs/builder/temp-tests/r1b/test_w2_fallback_equivalence.py`, adapted from R1's
   `test_w3p3_decline_arm.py`, drives a forged callback carrying its author's **own**
   `csrf_exempt` - the input where "declining loosens nothing" could fail - through
   `[boundary, observing CSRF subclass]` and through `[observing CSRF subclass]` alone:

   ```
   installed:   status=200 observed={'stamp': False, 'callback_exempt': True, 'reached': True}
   uninstalled: status=200 observed={'stamp': False, 'callback_exempt': True, 'reached': True}
   foreign constructions across both chains: []
   ```

   The two answers are **identical**, which is the property - not any single value. The same file
   also measures M-B's own forgery (`view_class = dict`): the recognizer now answers `None` and the
   request returns `200` under `DEBUG_PROPAGATE_EXCEPTIONS=True` with **no exception raised**, where
   R1 measured an `AttributeError`. Three passing rows in `.venv` and at the floor.
4. **Exactly one complete CSRF check, in both arrangements** - confirmed by the unchanged row sets of
   entries 5 and 13 rather than re-derived. Entry 14 was not re-run (`views.py`, argued per entry
   above).
5. **A genuine mount is recognized at both transports** - T3 plus the probe readings, re-taken at the
   floor.
6. **The public surface does not move.** `git diff -- django_strawberry_framework/__init__.py` is
   empty; `middleware/request_body.py`'s `__all__` is still the single-name tuple
   `("GraphQLRequestBodyBoundaryMiddleware",)`, so the documented `MIDDLEWARE` string is unchanged;
   `_BOUNDARY_METHOD` appears in `_boundary_ordering.py`, `middleware/request_body.py` and
   `tests/test_views.py` and nowhere else in the package - re-exported from neither
   `django_strawberry_framework/__init__.py` nor `middleware/__init__.py`.

### Hot-path budget

**Declared hot-path, inherited from R1**: the recognizer runs once per marked callback in
`process_view`, i.e. per request to a package mount. The probe adds one `getattr` and one
`callable()` on the recognized path and **nothing** on the path a non-package request takes, since
the marker clause is still first and still the only read such a request pays.

**Metric: R1's recognizer micro-benchmark, reproduced in the same shape** -
`docs/builder/temp-tests/r1b/test_r1b_hotpath_recognizer.py`, copied from
`docs/builder/temp-tests/r1/test_w2p3_hotpath_recognizer.py` with only the "before" arm re-pointed:
it is now the pre-R1b body (marker, two `getattr`s, the `isinstance` pair, the construction
`try` / `except TypeError`) and the "after" arm is the shipped `_package_view_instance`, so the delta
is the probe and nothing else. Both arms in **one** process over the identical callback,
`timeit`, **200,000** iterations, statistic = total seconds divided by iterations.

Command (identical in both environments, only the interpreter differs):

```shell
uv run pytest docs/builder/temp-tests/r1b/test_r1b_hotpath_recognizer.py -s -o addopts="" --no-cov
/tmp/dsf-floor/bin/python -m pytest docs/builder/temp-tests/r1b/test_r1b_hotpath_recognizer.py -s -o addopts="" --no-cov
```

| Environment | before (per call) | after (per call) | delta per call |
| --- | --- | --- | --- |
| shared `.venv` (Python 3.14.2), run 1 | 0.5142 us | 0.5373 us | **+0.0232 us** |
| shared `.venv` (Python 3.14.2), run 2 | 0.5135 us | 0.5360 us | **+0.0225 us** |
| floor (Python 3.10.19) | 0.5545 us | 0.5932 us | **+0.0387 us** |

Read against R1's numbers, taken from its artifact rather than restated from memory: R1's standing
figure is a worst reading of ~15 ns per request against a ~314 us request, and its pass-4 readings of
the *sibling* snippet were -0.0487, +0.0017 and -0.0087 us inside a recorded band of -0.0206 to
+0.0295 us. **This pass's deltas are positive in all three readings and the floor's is above that
band, and that is the expected shape rather than an anomaly**: R1's band described a zero-cost `try`
whose readings straddled zero, while this pass adds a real attribute lookup plus a `callable()` call,
so a consistent-sign ~23 ns (3.14) / ~39 ns (3.10) is the cost being visible rather than noise. The
absolute per-call figures (0.51-0.59 us) sit inside R1 pass 3's recorded 0.50-0.53 us band on both
interpreters, so the machine is behaving as it did then and the delta is the number.

**Metric 1, R1's 400-iteration request median, is deliberately not re-captured.** Both the R1 plan
and two R1 review passes recorded that it cannot resolve a change of this size against ~313 us of
request; that is stated rather than answered "not applicable", because the declaration is inherited
and an empty answer reads the same as an unmeasured one. Whether ~23-39 ns per package-mount request
is acceptable is the maintainer's call and no worker's; no correctness boundary was weakened to buy
any of it back.

### Floor verification

**This pass owns the run**, per the plan's `### Floor verification scope` (scope: `tests/test_views.py`;
the change is on the request-lifecycle path, a Django integration seam). Floor facts taken from
`BUILD.md` `## Floor verification`, its single canonical statement, never from memory or a number
restated elsewhere: the supported floor is **Django 5.2.0 on Python 3.10 with strawberry-graphql
0.316.0**.

`/tmp/dsf-floor` existed from R1 and was **reused only after reading its resolved versions**:

- `/tmp/dsf-floor/bin/python -V` -> **Python 3.10.19**.
- `uv pip list --python /tmp/dsf-floor/bin/python`, read rather than recalled: **django 5.2**,
  **strawberry-graphql 0.316.0**, asgiref 3.12.1, channels 4.3.2, daphne 4.2.3, pytest 9.1.1,
  pytest-django 4.12.0, pytest-asyncio 1.4.0, and **django-strawberry-framework 0.0.14** editable at
  `/Users/riordenweber/projects/django-strawberry-framework`. So it **is** the floor, and being
  editable against this checkout it carries this pass's change.
- `/tmp/dsf-floor/bin/python -m pytest tests/test_views.py --no-cov` -> **200 passed**. The declared
  scope, green.
- The eight rows this round's subject rests on, named individually rather than hidden inside a green
  aggregate: all five parametrizations of
  `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed`, plus
  `::test_a_callable_view_class_that_is_not_a_class_is_never_called`, plus T2
  (`::test_a_view_class_without_the_boundary_is_never_constructed`) and T3
  (`::test_the_probed_boundary_method_is_the_one_the_package_views_define`) - **8 passed** at the
  floor, each `PASSED` read individually in `-v` output.
- The three floor questions the plan names: **(1)** `callable(getattr(<class>, name, None))` answers
  identically at 3.10 - the probe-answers table above is byte-identical between the two
  interpreters, `_DisabledBoundary` and the metaclass case included; **(2)** the named rows pass,
  above; **(3)** the hot-path delta at the floor is **+0.0387 us**, recorded above. The
  `hasattr`-versus-`callable` table and the fallback-equivalence rows were also re-run at the floor
  and answer identically.
- **The shared `.venv` was never installed into**, read rather than asserted: `uv pip list` reports
  **django 6.0.5**, asgiref 3.11.1, strawberry-graphql 0.316.0, channels 4.3.2, daphne 4.2.2, pytest
  9.0.3, and `.venv/bin/python -V` is **Python 3.14.2** - still far above the floor, so no floor
  install leaked into it. Every floor command was invoked as `/tmp/dsf-floor/bin/python -m pytest` or
  carried an explicit `--python /tmp/dsf-floor/bin/python`, and **no `uv pip install` was run in this
  pass at all**.

### Implementation notes

- **`_BOUNDARY_METHOD` is the name and it sits between the two marks and the `ContextVar`**, in
  B-1's exact form and comment. The docstring's fourth `The protocol` paragraph opens by saying what
  the fact is *not* ("not a mark and not per-request"), because the module's own title and its
  "two facts per request" sentence had to change for it and a reader who skips the title needs the
  distinction anyway.
- **The clause is its own statement, third**, exactly as B-3 specifies, and reads
  `if not callable(getattr(view_class, _BOUNDARY_METHOD, None)): return None`. Not folded into the
  existing `if`: three different facts in one decision would destroy entry 15's anchor and with it
  the only comparable measurement of the two shape clauses.
- **T3 is one row with three assertions, not two rows.** The identity assertion and the
  both-transports predicate assertion fail together under either drift direction (measured), so
  splitting them would buy a second row that cannot fail independently - and `BUILD.md` counts rows,
  not assertions. It reaches the mixin through the file's existing local-import idiom
  (`from django_strawberry_framework import views as views_module` inside the function), the same
  shape `::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark` and
  `::test_the_body_boundary_mixin_stays_private_and_sits_first_in_both_base_lists` already use, so no
  module-level import of a private symbol was added.
- **T4's callable is a named module-level stub, `_boundary_the_factory_carries`**, not a `lambda` and
  not the mixin's own function object. A `lambda` would carry no docstring, and reaching for the
  mixin's function would mean a new module-level import of a private view symbol purely to decorate
  a fixture. The stub's body raises, which is honest: nothing ever calls it (the object a called
  factory returns is what `process_view` would probe, not the factory), and if that ever changes the
  fixture says so loudly instead of passing quietly.
- **Fixture naming mirrors the existing recording idiom rather than inventing a second convention**:
  `_FOREIGN_VIEW_CONSTRUCTIONS` / `_ForeignButBuildableView` /
  `_marked_callback_with_a_foreign_view_class` / `/marked-foreign-view-class/` sit beside
  `_VIEW_CLASS_FACTORY_CALLS` / `_view_class_factory` / `_marked_callback_with_a_callable_view_class`
  / `/marked-callable-view-class/`, and the class's docstring states that *recording* is the
  contract.
- **The fallback-equivalence temp test was not promoted to a permanent row.** The plan leaves that to
  discretion and says non-weakening check 3 is satisfied by the measurement; the wire behaviour it
  asserts is already pinned permanently by T1, and its distinctive input (a forged callback carrying
  its author's own `csrf_exempt`) is a shape no supported seam produces, so a permanent row would
  pin a fixture rather than a contract.
- **One docstring sentence was corrected after the first full manifest run**, which is why the
  shipped `middleware/request_body.py` SHA differs from the one in the auxiliary records: the
  enumeration's closing clause read "a recognition that stopped at the shape of the bookkeeping
  would still turn a foreign callback into an unhandled `500`", which is false for the third listed
  case - a real, buildable, non-package class is stopped by neither the bookkeeping shape nor the
  construction. It now reads "stopped short of the boundary - at the shape of the bookkeeping, or at
  the instance the bookkeeping builds". The whole manifest and the drift auxiliary were re-run after
  it, and every row set reproduced identically.
- **The five over-claiming sites R1 inventoried, and their disposition.** Site 1
  (`::_package_view_instance` `#"a hook whose every other outcome is a controlled response"`) and
  site 3 (`tests/test_views.py::_marked_callback_without_a_view_class`'s docstring, which makes the
  same claim) are **kept verbatim**: they become true with this change, which is the point of the
  round, and rewriting a sentence that has just become true would erase the evidence it was the
  claim at issue. Site 2 (the module docstring's recognition sentence around
  `#"so no non-package view is touched"`), site 4 and site 5 (T1's docstring, including its "the
  four routes are the four ways" exhaustiveness claim) are rewritten. Every other sentence
  describing the old recognition - `::_package_view_instance`'s opening enumeration, its `TypeError`
  paragraph's scope, its `isinstance`-ordering sentence, and `::process_view`'s
  `#"reached through an instance built the way View.as_view builds one"` - is rewritten too. The
  class docstring's `#"at the cost of one getattr in process_view"` is **deliberately unchanged**:
  it is scoped to a request that is not a package view's, and the marker test is still first and
  still the only read such a request pays.
- **Complexity, judged rather than left implicit.** `scripts/review_inspect.py` now reports
  `_package_view_instance` at **68 lines and 6 branch nodes** (the plan predicted 6 branch nodes and
  quoted 43 lines). **55 of the 68 lines are docstring** (the helper's own symbol table puts the
  docstring at lines 212-266 of a function spanning 211-278), so the executable body is 12 lines of
  four flat decline clauses and one `try`. Splitting it would produce two halves neither of which is
  "the answer the hook branches on" while invalidating three failability anchors. Recorded so
  Worker 3 can disagree with the judgement rather than be surprised by it.
- **DRY: no new helper, and the two candidates were re-checked at source.**
  `mutations/fields.py::_has_mutation_protocol` is the package's established shape *and* position for
  a class-level protocol probe (`callable(getattr(cls, "...", None))` behind
  `if not isinstance(cls, type) or not _has_mutation_protocol(cls)`), which is why the clause is
  idiom rather than invention; generalizing it would produce a helper thinner than its call site.
  A shared recognizer with `middleware/debug_toolbar.py` stays unbuilt (R1 hand-off item D-6, whose
  justifying condition - a third middleware, or two needing to agree about one callback - R1b does
  not meet). `repeated string literals: 0` in the refreshed overview, and the boundary method's name
  appears as a literal in exactly one place in the package.

### Notes for Worker 3

- **The failability records live in gitignored scratch**, so the artifact carries the emitted block
  verbatim. The four files to re-run against are
  `docs/builder/temp-tests/r1b/proofs.json` (8 entries, the operative manifest),
  `proofs-drift.json` (2 entries, the loudness auxiliary),
  `proofs-entry15-without-T4.json` (1 entry, the deliberate 0-row reading), and the three temp tests
  `test_w1_probe_answers.py` (W1's, re-run unmodified), `test_w2_hasattr_vs_callable.py` and
  `test_w2_fallback_equivalence.py` (mine), plus `test_r1b_hotpath_recognizer.py`. Every `.log` and
  `.md` the runs emitted sits beside them.
- **The comparison generation is `docs/builder/temp-tests/r1/proofs-pass4.json`.** R1's
  `proofs.json` (its pass-1 record) is superseded and not runnable - four of its anchors match zero
  times.
- **Scratch roots used, all outside the repository:**
  `.../scratchpad/fail-main2` (main manifest), `.../scratchpad/fail-drift2` (drift),
  `.../scratchpad/fail-aux15` (the 0-row reading), plus `fail-main` and `fail-drift` from the
  pre-correction runs. Each holds only `pristine/`; none holds an `ACTIVE-MUTATION.json`.
- **`views.py` was transiently mutated once**, for the drift measurement, through the runner so the
  restore is byte-proved rather than hand-asserted. It is byte-identical at both ends
  (`e8aeb156550fc45a...`), and no other file outside this round's write set was touched at all. If
  you distrust that, the cheapest independent check is `shasum -a 256` against R1's recorded values,
  which are in its pass-4 proof table.
- **Shadow file used:** `docs/shadow/django_strawberry_framework__middleware__request_body.overview.md`
  and its `.stripped.py`, regenerated this pass. Its line numbers are not canonical; every reference
  above cites original source symbols.
- **Where I would look hardest.** (a) T2's construction-count assertion is *not* what entry 16's
  mutant fails on - said plainly above, and worth confirming. (b) Entry 16 sits at 2 rows, above the
  weakly-pinned band but inside your mandatory re-run floor. (c) The plan's step-6 grep prediction
  and its step-12 claim about the live-tier probe wrapper both came out different from the plan;
  both are recorded as drift below rather than silently corrected.

### Notes for Worker 1 (spec reconciliation)

R1b writes no spec or rationale text; the items the plan already recorded for R2 stand unchanged and
are not restated. What follows is new: three plan-time readings this pass could not reproduce, and
one spec-wording confirmation.

1. **Drift - `### Implementation steps` step 6's second reading is wrong as written, and the property
   it checks still holds.**
   - *Where it lives:* `docs/builder/bld-046-r1b-recognition_contract.md`,
     `## Plan (Worker 1)` -> `### Implementation steps`, step 6, second bullet.
   - *Current wording:* "Neither of the two modules imports the other:
     `grep -c 'middleware.request_body\|middleware import' django_strawberry_framework/views.py` and
     `grep -c 'from django_strawberry_framework.views\|framework import views'
     django_strawberry_framework/middleware/request_body.py` - **both 0**."
   - *Measured:* the second command returns **0**; the first returns **5**. All five are docstring
     symbol references of the form ``` ``middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware`` ```
     - the unescaped `.` in the pattern matches the `/`. This is `BUILD.md`
     `## Claims are proven mechanically`'s "a long grep phrase samples a claim's vocabulary rather
     than establishing its population", in the other direction: it over-counts prose.
   - *Recommended replacement:* "Neither of the two modules imports the other, measured on **import
     statements** rather than on any occurrence of the name:
     `grep -cE '^\s*(from|import)\s+.*(middleware|request_body)'
     django_strawberry_framework/views.py` returns 2 and **neither line is a middleware import**
     (`_request_body` and `conf`), and
     `grep -cE '^\s*(from|import)\s+.*views' django_strawberry_framework/middleware/request_body.py`
     returns **0**. Reading 3's `sys.modules` difference is what actually establishes the property;
     the greps only locate it."
2. **Drift - `### Implementation steps` step 12 mis-describes the live tier's probe wrapper**, in the
   safe direction.
   - *Where it lives:* same artifact, `### Implementation steps`, step 12.
   - *Current wording:* "the live tier's probe wrapper
     (`examples/fakeshop/test_query/test_transport_api.py`) copies `csrf_exempt` and the
     `view_class` / `view_initkwargs` bookkeeping but **not** the marker, so it is declined at the
     first clause".
   - *Measured:* `::_carrying_the_packages_csrf_mark` copies **only** `csrf_exempt`; the six
     `view_class` occurrences in that file are all a *parameter* of that name, and no line assigns
     `.view_class` or `.view_initkwargs` onto a wrapper. The conclusion is unaffected - with no
     marker the callback is declined at the first clause and this change cannot move it - and the
     live tier is green (**69 passed**).
   - *Recommended replacement:* "the live tier's probe wrapper
     (`examples/fakeshop/test_query/test_transport_api.py::_carrying_the_packages_csrf_mark`) copies
     `csrf_exempt` and nothing else - neither the marker nor Django's `view_class` /
     `view_initkwargs` bookkeeping - so it is declined at the first clause and this change cannot
     move it."
3. **Drift - step 8's mutation is louder than the drift direction it names, and a faithful one-block
   model exists inside this round's write set.**
   - *Where it lives:* same artifact, `### Implementation steps`, step 8, and
     `### Architectural decision B-2` direction 1.
   - *Current wording:* step 8 - "Transiently rename
     `views.py::_RequestBodyBoundaryMixin._enforce_request_boundary` and record which rows fail. …
     Expect the 4 rows of entry 3 plus T3".
   - *Measured:* **33 rows**, not 5. A `def`-line-only rename also orphans the mixin's own internal
     caller (`::_enforce_request_boundary_once` `#"self._enforce_request_boundary(request)"`, exactly
     one such caller) and three direct calls in `tests/test_views.py`, so every view-local request
     path breaks alongside the recognition. Mutating the **constant** instead
     (`_BOUNDARY_METHOD = "_enforce_request_boundary"` -> `..._drifted`) puts the two names in
     exactly the disagreement B-2 direction 1 and direction 2 both describe, in one block, in this
     round's own write set - and measures **exactly the predicted 5 rows** (entry 3's four plus T3).
     Both were run and both are recorded; the constant is the model and the rename is the superset.
   - *Recommended replacement:* "Measure the loudness from the **constant's** side - one transient
     mutation of `_BOUNDARY_METHOD` in `_boundary_ordering.py`, which is in this round's write set
     and puts the probed name and the defined method in exactly the disagreement B-2 describes. Its
     prediction is entry 3's 4 rows plus T3. A `views.py` `def`-line rename measures a strict
     superset (33 rows) because it also orphans `::_enforce_request_boundary_once`'s call and three
     direct test calls, so it is worth running as corroboration but is not the model of the drift."
   - This is a measurement obstacle in the plan's *proof procedure*, not in B-2 itself: the
     architectural call (pin the coupling by tests rather than by an import-time guard in `views.py`)
     is unchanged and is now measured from both sides.
4. **Spec wording confirmed rather than changed.** The recognition sentence the plan proposes for R2
   under its `### Notes for Worker 1` item 2 is exactly what shipped, and its third clause is now
   measured: entry 16 at 2 rows plus two named permanent rows (T1's fifth route and T2), with entry
   12 at 7 and entry 15 at 2. R1's standing instruction still holds unchanged: **do not** write the
   `view_initkwargs` `dict` test as a symmetric guard. One wording refinement worth carrying into
   Decision 18: the probe establishes *a callable* of that name, not its presence, and the
   difference is reachable (a subclass setting the attribute to a non-callable) - so the contract
   sentence should read "carries that boundary as something callable" rather than "carries that
   boundary", or the spec promises less than the code delivers.
5. **The spec's `Status:` block and opener are untouched and still accurate**, re-read this pass
   against `HEAD`: "Planned for `0.0.15`" and the `BUILT` block hold, both `pyproject.toml` and
   `__init__.py` read `0.0.14`, and this round falsifies none of it. No spec edit was made or is
   licensed here.
6. **No glossary, terms-CSV, `docs/TREE.md`, `docs/README.md` or `examples/**` work is created by
   this round**, confirming the plan's item 6: `_BOUNDARY_METHOD` is private, in a private module,
   re-exported nowhere, and the live tier needed no re-pin (69 passed unchanged). R3's obligations
   are exactly where R1 left them.

---

## Review (Worker 3)

Required reading walked before judging anything, and the **W3** column of `BUILD.md`
`## Required reading per worker` walked myself rather than taken from the dispatch: `AGENTS.md`,
`START.md`, `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, `docs/builder/worker-3.md`,
`docs/README.md`, `examples/fakeshop/test_query/README.md`, the active spec, the active
spec **rationale** (W3 reads it), the active build plan, this artifact, and my own memory file.
The column marks nothing else `yes` for W3 (`GOAL.md`, `docs/GLOSSARY.md`, `CHANGELOG.md` and
`docs/TREE.md` are dashes in the W3 column), so nothing was omitted from the dispatch. The other
workers' memory files were not read.

### Independent re-run: the mutations, declared BEFORE any of them was made

`worker-3.md` requires the mutation to be recorded in this artifact before it is applied, so this
subsection was written and saved to disk first and the runs came after it.

**Re-run set: all eight entries of `docs/builder/temp-tests/r1b/proofs.json`, at the scope Worker 2
recorded (`tests/test_views.py`), plus the drift auxiliary's constant-side entry.** The mandatory
floor (`worker-3.md`, "the independent re-run has a mandatory floor") requires every boundary at
**3 rows or fewer** — table entries 2, 4, 7 and 8 — **and every boundary on a security or
data-isolation decision**, which here is all eight: every one of them is a clause of the CSRF-ordering
or body-cap contract. So the floor is the whole manifest and there was nothing to select.

Mutations applied, quoted from the manifest I parsed rather than from the build report's prose
(`label` -> `mutation`, in manifest order):

1. `::_package_view_instance #"if not getattr(view_func, _BOUNDARY_MARKER, False)"` -> `if True:`
2. `_CsrfOrderingExemption.__bool__` -> `return True`
3. `_CsrfOrderingExemption.__bool__` -> `return False`
4. `::_require_boundary_before_csrf` -> `return boundary_index = csrf_index = None`
5. `_CsrfOrderingExemption.__bool__` -> `return _boundary_middleware_request.get() is None`
6. `::_package_view_instance`, the eight-line block from the first `isinstance` clause through
   `except TypeError: return None` -> `    return view_class(**initkwargs)`
7. `::_package_view_instance`, `if not isinstance(view_class, type) or not isinstance(initkwargs,
   dict): return None` **deleted**
8. `::_package_view_instance`, `if not callable(getattr(view_class, _BOUNDARY_METHOD, None)):
   return None` **deleted**

Auxiliary: `_BOUNDARY_METHOD = "_enforce_request_boundary"` -> `..._drifted` in
`_boundary_ordering.py` (the constant-side drift model). **The `views.py` `def`-line rename is
deliberately NOT re-run by me**: `views.py` is outside this round's write set, dirty with R1's
uncommitted work, and Worker 2's own measurement of it is a corroborating superset rather than the
model — my reasons are in `### The drift coupling` below.

Discipline: `--check-anchors-only` first and separately, one boundary at a time through
`scripts/prove_failability.py` so the order is enforced, scratch roots outside the repository, every
restore byte-proved by the runner, node-id **sets** compared rather than counts. No `git checkout`,
`git restore`, `git stash` or `git worktree` at any point in this pass.

### Re-run result: eight of eight set-equal, nothing weakly pinned

`--check-anchors-only` **exit 0** (all eight matched exactly once *before any copy was taken*, so no
prior pass left a live mutation); the full set in one invocation, **exit 0**; scratch root
`.../scratchpad/w3-fail`, holding only `pristine/` and no `ACTIVE-MUTATION.json`. Record emitted to
`docs/builder/temp-tests/r1b/w3-rerun.md`, log beside it.

Node-id **sets** compared by symmetric difference over the parsed lists, mine against Worker 2's
emitted block (not against its prose table):

| # | boundary | W2 rows | W3 rows | sets |
| --- | --- | --- | --- | --- |
| 1 | `::_package_view_instance #"if not getattr(view_func, _BOUNDARY_MARKER, False)"` | 4 | **4** | set-equal |
| 2 | `_CsrfOrderingExemption.__bool__` -> `True` | 3 | **3** | set-equal |
| 3 | `_CsrfOrderingExemption.__bool__` -> `False` | 13 | **13** | set-equal |
| 4 | `::_require_boundary_before_csrf` | 3 | **3** | set-equal |
| 5 | `_CsrfOrderingExemption.__bool__` (per-request key) | 7 | **7** | set-equal |
| 6 | `::_package_view_instance` (whole recognition after the two `getattr`s) | 7 | **7** | set-equal |
| 7 | `::_package_view_instance #"if not isinstance(view_class, type)"` | 2 | **2** | set-equal |
| 8 | `::_package_view_instance #"if not callable(getattr(view_class, _BOUNDARY_METHOD, None))"` | 2 | **2** | set-equal |

**0 collection/setup errors on all eight**, every pre-mutation baseline `200 passed` at pytest exit
0, `pre-existing failing rows excluded from the count: 0` on all eight, and every restore proved by
`filecmp.cmp(shallow=False)` plus SHA-256 against the runner's own pre-mutation copy (five against
`7154891a17fcc10b...`, three against `7b3d9e51b7fb7ecc...`). After the whole re-run I re-read the
tree: `middleware/request_body.py 7154891a17fcc10b...`, `_boundary_ordering.py 7b3d9e51b7fb7ecc...`,
`tests/test_views.py 477de139ee5fe8aa...`, `views.py e8aeb156550fc45a...` — all identical to the
build report's "after" column, and `git status --short` byte-for-byte what it was at task start (the
eight tracked entries plus the two untracked artifacts), with `git diff --cached --name-status` still
the one authorized staged path.

**No entry lands in the 0-or-1-row band**, so `BUILD.md` `### Acceptance rule` is satisfied, and the
runner's exit 0 says so independently of my reading.

### The manifest, audited entry by entry rather than accepted

- **The "derived programmatically, character-identical" claim is true, and I re-derived it rather
  than accepting it.** Parsing both manifests and comparing sorted-key JSON per entry: the five
  inherited entries (R1's 3, 4, 5, 6, 13) are **byte-identical** objects to
  `docs/builder/temp-tests/r1/proofs-pass4.json`'s, and entry 15's object is byte-identical too —
  which is what makes "the anchor is byte-identical and still matches exactly once" a measurement
  rather than a claim. Only two objects differ from pass 4: entry 12's re-anchor (eight-line block,
  replacement unchanged at `    return view_class(**initkwargs)`) and entry 16, new, `delete: true`.
- **Entry 12 grew by exactly two and lost none**: gained
  `…_declined_not_crashed[/marked-foreign-view-class/]` and
  `::test_a_view_class_without_the_boundary_is_never_constructed`. Nothing else moved.
- **Entry 16 is a strict subset of entry 12** (verified by set containment), and **disjoint from
  entry 15**. Three entries over one function that pin three different answers, nested rather than
  redundant — the same shape R1 used to prove 12 and 15 were not duplicates.
- **Route 3's membership checked directly, not read off the prose.**
  `[/marked-rejected-initkwargs/]` **is** in entry 12's set and **is not** in entry 16's. So B-4's
  justification is measured: with the probe standing, a genuine package class named with kwargs it
  rejects still reaches the construction arm, and deleting that arm would restore an unhandled `500`
  for a route the suite already pins. The arm stays, correctly.
- **Entry 15's zero-without-T4 is a real fix to a real pin, not a test edited to make a mutant
  fail** — and I established the mechanism without touching a permanent test or a production file.
  `docs/builder/temp-tests/r1b/test_w3_predicate_and_consequence.py` runs a *local copy* of entry
  15's mutant body (the two `isinstance` clauses removed) against two recording factories:

  ```
  entry-15 mutant, factory WITHOUT the boundary attribute:
    answer: None | factory calls: []
  entry-15 mutant, factory WITH the boundary attribute:
    answer: object | factory calls: ['with']
  ```

  Identical in `.venv` (3.14.2) and at the floor (3.10.19). So the zero is exactly what Worker 2
  says it is: with the probe standing one line later, a boundary-less factory is refused by the
  probe, the deleted clauses change nothing observable, and the two rows cannot fail. T4 supplies
  the one input that still distinguishes them and **weakens no assertion** — both of
  `::test_a_callable_view_class_that_is_not_a_class_is_never_called`'s asserts are unchanged, and
  the fixture is no more forged than its four siblings (every route in that parametrization forges a
  package-private marker). The fix is a better-targeted input, which is what the acceptance rule
  prescribes; the alternative — accepting a 0-row entry — is what it forbids.
- **The decision not to re-run seven of R1's fifteen entries is right, and I did not take the
  invitation to distrust it.** The argument is falsifiable and I checked its premise rather than its
  conclusion: what could move those sets is a new row that exercises their boundary, and the three
  rows this round adds cannot. Independently confirmed — T1 drives a bare `GET` (no body, no
  `Content-Type`, no multipart envelope, no socket), T2 and T3 never build a request at all, and
  `grep -rn '_BOUNDARY_MARKER\|graphql_request_body_boundary' tests examples --include='*.py'`
  returns hits in **no file but `tests/test_views.py`**, so no other tree gained an input to those
  boundaries either. Their unmutated green state is in the record eight times over as the
  pre-mutation baseline. Mutating three files that are dirty with a closed round's uncommitted work,
  for a stability check obtainable this way, is the worse trade.
- **The one `views.py` mutation Worker 2 did take is byte-proved and the file is where it was:**
  `e8aeb156550fc45a…`, which is the value R1's pass-4 proof table records for that file, read by me
  rather than copied from the build report.

### The clause itself: shape, position and the direction of its failure arm

```django_strawberry_framework/middleware/request_body.py:274:275
    if not callable(getattr(view_class, _BOUNDARY_METHOD, None)):
        return None
```

- **The shape is a `getattr` default, which is in `BUILD.md`'s catalogue, and it passes the answer
  test in the fail-closed direction.** The answer `process_view` consumes is *a callable boundary it
  can run*; this expression is that answer's negation. Both spellings of "no runnable boundary" —
  absent, and present but not callable — reach the same `return None`, and no incoherent input
  reaches a permit branch. It is not the catalogued shape, which converts "cannot determine" into
  "permit".
- **The failure arm's direction is fail-closed twice over, and that is measured rather than
  argued.** A decline leaves the request unstamped, so the exemption stays true and the *view* runs
  the boundary and re-enters CSRF: the body cap is still enforced, and what degrades is the CSRF
  *class*, never the ordering. Entries 2, 3 and 5 (the three `__bool__` directions) are set-equal to
  R1's, `::test_a_declined_callback_still_gets_a_complete_csrf_check[sync|async]` and
  `::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[sync|async]` are still
  in entry 3's and entry 5's sets, and I confirmed by reading the diff against the **index** copy
  that no line of `__bool__`, the `ContextVar` or `_CSRF_ORDERING_EXEMPTION` moved (three hunks
  only: the docstring title/sentence, the new `The protocol` paragraph, the new constant).
- **The position is a requirement, not a preference, and it is the package's own idiom.** After the
  two `isinstance` tests, so the read is a class attribute lookup rather than an arbitrary object's
  `__getattr__`; before the construction `try`, which is M-B's "why the class rather than the built
  instance" and is pinned permanently by T2's recording assertion. Read at source:
  `mutations/fields.py::_has_mutation_protocol` is `callable(getattr(cls, "resolve_sync", None))
  and …` called behind `if not isinstance(mutation_cls, type) or not
  _has_mutation_protocol(mutation_cls)` — the same expression in the same position for the same
  question — and `middleware/debug_toolbar.py::GraphQLDebugToolbarMiddleware.process_view` guards
  `issubclass` with `isinstance(view, type)` for the reason its own docstring gives. Nothing now
  reads a class attribute that should not: the probe reads exactly one name, off an object already
  established to be a `type`, and only when the marker is present.
- **`callable` versus `hasattr`, re-derived rather than re-run.**
  `docs/builder/temp-tests/r1b/test_w3_predicate_and_consequence.py` (mine, written from scratch)
  tabulates both predicates over seven candidates and then drives the consequence at the call site
  under repair:

  ```
  candidate                                  hasattr  callable(getattr(..., None))
  DjangoGraphQLView                          True     True
  AsyncDjangoGraphQLView                     True     True
  _RequestBodyBoundaryMixin                  True     True
  dict                                       False    False
  _ForeignBuildable                          False    False
  MappingProxyType                           False    False
  _DisabledBoundary (attr present, None)     True     False
  disagreements: ['_DisabledBoundary (attr present, None)']
  calling the hasattr-recognized boundary raises: TypeError("'NoneType' object is not callable")
  ```

  Identical in `.venv` and at the floor. So the "exactly one candidate" claim is confirmed, and so
  is the consequence: under `hasattr` a `DjangoGraphQLView` subclass setting
  `_enforce_request_boundary = None` would be **recognized** and `process_view` would then call
  `None` — the same uncontrolled `500` from the same hook, in a second spelling. `callable(...)` is
  required and `hasattr` would have been the smaller expression and the wrong one.

### The drift coupling: which model is right, and whether the recorded pin is the one that matters

**Worker 2's correction is right and the plan's mutation was the wrong model.** I re-ran the
constant-side entry myself (one-entry manifest `docs/builder/temp-tests/r1b/w3-drift-constant.json`,
scratch root `.../scratchpad/w3-drift`, anchors checked separately, exit 0, restore byte-proved,
`_boundary_ordering.py` back at `7b3d9e51b7fb7ecc…`) and measured **5 rows, 0 errors, baseline 200
passed**:

- `::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[sync|async]`
- `::test_the_view_does_not_measure_a_body_the_chain_already_measured[sync|async]`
- `::test_the_probed_boundary_method_is_the_one_the_package_views_define`

i.e. entry 1's four behavioural rows plus T3, exactly as the plan predicted for the direction it
described. The reason this is the faithful model and the `def`-line rename is not: a real rename
renames the definition **and its callers**, so the residual disagreement is between the probed name
and the defined name and nothing else — which is precisely the state the constant mutation
produces. The `def`-line-only rename additionally orphans
`views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once` #"self._enforce_request_boundary
(request)" and the three direct calls at `tests/test_views.py` lines 2177, 2181 and 2222 (counted, 3),
so its 33 rows are mostly "every view-local request path broke", which is a different event. Louder,
and a poor model — Worker 2's own words, and they are the correct reading. Recording both and naming
which one is the model is better than either alone.

**And the recorded pin is the one that matters.** T3 fails *by name* under the drift: it asserts
`getattr(mixin, _BOUNDARY_METHOD) is mixin._enforce_request_boundary`, so a rename on either side
either makes the identity false or makes the direct attribute access raise. Four behavioural rows
catch the consequence (the probe declining every genuine mount, the chain never running the boundary
and never stamping) and T3 names the cause. A silent drift is not available. I agree with B-2's
rejection of an import-time guard in `views.py` — the raise arm would be a production branch no test
can drive without a mutation, and `views.py` is outside this round's write set — and with the
rejection of calling the boundary through the constant, which would hide the call from the
`path::QualifiedName` convention for a divergence three row sets already catch.

### High:

None.

### Medium:

#### The probe's stated limit is measured on one spelling only, and the absolute it re-asserts is false

`BUILD.md` `### Fail-open shapes` is explicit that a guard — and, here, a *claim* about a guard —
written against an input spelling is a guess, and that only naming the answer settles it. The plan's
own fail-open list dismisses the probe's metaclass reach with *"Not a fail-open shape (the answer is
`False` either way, measured)"*, and Worker 2 reproduced that with a metaclass `__getattr__` that
**returns**. There is a second spelling of the same limit and a raising one of the first, and neither
answers `False`: they answer nothing and raise out of the hook.

Measured against the **real** `GraphQLRequestBodyBoundaryMiddleware.process_view` — not a copy —
in `docs/builder/temp-tests/r1b/test_w3_hook_outcome.py`, identically in `.venv` (3.14.2) and at the
floor (3.10.19):

```
  metaclass __getattr__ raises: UNCONTROLLED: ValueError out of process_view: metaclass __getattr__ raised for '_enforce_request_boundary'
  class descriptor __get__ raises: UNCONTROLLED: ValueError out of process_view: descriptor __get__ raised
```

`_package_view_instance` is called outside any `try` in `process_view`, and the `getattr` default
absorbs `AttributeError` only, so any other exception raised while reading the attribute leaves the
hook uncaught. Two shapes reach it: a metaclass `__getattr__`, and a descriptor of that name on the
class itself — the second is not mentioned anywhere in the diff. Separately measured
(`docs/builder/temp-tests/r1b/test_w3_probe_reach.py`): the descriptor case is reached by the
pre-probe recognition as well, so the probe **moves that failure's site and does not change its
loudness** — it is not a regression — while the metaclass case swaps one uncontrolled failure
(`__init__`) for another (the read).

**Why this is a finding and not a nit.** Three sentences the round shipped or hands forward assert
the absolute:

- `middleware/request_body.py::_package_view_instance` #"a hook whose every other outcome is a
  controlled response" — R1's inventoried site 1, which the `### Dispatched findings checklist`'s
  first box ticks as *"Closed by making the claim **true**"*. It is now true for every input the
  recognition itself decides, and false for this one.
- the same docstring's limit paragraph, which concedes the metaclass reach and then, in the next
  clause, re-asserts *"the probe is here so that every outcome of the hook is a controlled
  response"*. Those two sentences are in tension with each other in the shipped file.
- `### Notes for Worker 1` item 4, which proposes that Decision 18 *"can assert that **every**
  outcome of the boundary middleware's `process_view` is a controlled response"*. If R2 writes that
  unqualified, the spec will state a falsehood about a security-adjacent seam — which is the exact
  class of defect this whole closeout cycle exists to clear.

**Recommended change — documentary, in this round's own write set, and NOT the narrowing M-B
rejected.** M-B rejected narrowing *as an alternative to the fix*; the fix landed and the property
is now far stronger than it was. What is asked is that the sentences describe the property that was
achieved: scope the claim to the outcomes the recognition decides (a refusal, a stamp, or a
decline), and state the residual once, naming **both** shapes of attribute machinery a forged class
can supply, and that containing it would mean wrapping the probe in `except Exception` — a
contract-level choice, not a wording one. No test row is owed by the documentary fix: no boundary
changes.

**The code change is a contract-level question and is escalated, not requested** — see
`### Notes for Worker 1 (spec reconciliation)` item 1. If the maintainer takes that path,
`except Exception: return None` around the probe is *not* the catalogued fail-open shape (it
converts "the read blew up" into *decline*, not into *permit*, which is the same direction as the
existing `except TypeError` around the construction), it would make the absolute true, and it would
then be a new boundary owing its own failability entry — and it would also swallow a genuine
descriptor failure on a *package* class, which is the reason it is the maintainer's call and not
mine.

### Low:

#### A test docstring's cited evidence is falsified by this pass's own measurement

`tests/test_views.py::_wrapper_copying_only_csrf_exempt`'s docstring says the fixture *"copies
`csrf_exempt` … plus Django's `view_class` / `view_initkwargs` bookkeeping"* and then offers, as
proof that this is a reachable input, *"the repository itself contains one
(`examples/fakeshop/test_query/test_transport_api.py`'s probe mount)"*. This pass measured that it
does not: `::_carrying_the_packages_csrf_mark` sets `view.csrf_exempt = mark` and nothing else, and I
confirmed independently that no line in that file assigns `.view_class` or `.view_initkwargs` onto a
wrapper (its six `view_class` occurrences are a parameter of that name and `as_view` calls). The
load-bearing half of the claim — marker-dropping wrappers are reachable and one exists in the repo —
is true; the cited wrapper is a *weaker* member of the class than the sentence describes.

Worker 2 found this fact and corrected the **plan** for it (`### Notes for Worker 1` item 2) without
sweeping the sibling site that asserts it in shipped test prose. Recommended change: one clause —
either drop the parenthetical or say the repo's probe mount copies only `csrf_exempt`, i.e. is the
same class of wrapper with less bookkeeping. **Worker 1 may decline this on scope grounds** (the
sentence is R1's, and the plan's scope is "exactly M-B and nothing else"); it is raised because the
falsifying measurement was taken here and because leaving a measured-false sentence in place is the
shape this whole round exists to remove.

#### Two stated numbers in the build report do not reproduce as written

Corrected here as prose, per `ARTIFACT.md`; neither changes any reading and **no change is
requested**.

- `### Implementation notes` records the helper at *"68 lines and 6 branch nodes"* with the docstring
  at *"lines 212-266 of a function spanning 211-278"*. My run of
  `scripts/review_inspect.py … --output-dir docs/shadow` against the shipped bytes reports
  **`_package_view_instance` spans 69 lines and 6 branch nodes**, symbol lines **211-279**, docstring
  **212-267**. The one-line difference is the docstring sentence the report itself says was corrected
  after the earlier readings; the branch-node count, which is the load-bearing half, reproduces
  exactly, as does `repeated string literals: 0`, `Django / ORM markers: None`, and `getattr()` at
  **4x** where it was 3x.
- `### Hot-path budget` says *"The absolute per-call figures (0.51-0.59 us) sit inside R1 pass 3's
  recorded 0.50-0.53 us band on both interpreters."* They do not: 0.59 is outside 0.50-0.53, and my
  own floor readings (0.5594 / 0.5935) are likewise above it. The sentence is inherited loose
  phrasing — R1's own pass-4 review wrote "0.53 / 0.58 … sit back inside pass 3's 0.50-0.53 us band"
  — and it is decoration: the **delta** is the metric, the report states plainly and correctly that
  the floor delta (+0.0387) is *above* R1's -0.0206-to-+0.0295 band, and it explains why (R1's band
  described a zero-cost `try` straddling zero; this adds a real attribute lookup and a call). Nothing
  is hidden.

### DRY findings

None to fix. What I checked, and what I decided:

- **No new helper is justified and none was added.** A function wrapping one
  `callable(getattr(...))` would be a name in front of an expression, and
  `mutations/fields.py::_has_mutation_protocol` — read at source — answers a four-attribute protocol
  in an unrelated subsystem; generalizing it to "does this class carry attribute X" would produce a
  helper thinner than its own call site. Reuse correctly rejected, and the *shape* correctly reused.
- **The existence challenge, asked and answered against evidence.** `_BOUNDARY_METHOD` has two real
  readers (`middleware/request_body.py::_package_view_instance` and three assertions in
  `tests/test_views.py`) and one definition site. Inlining the literal into the middleware is what
  the constant exists to prevent: the name would then be spelled in two modules with no row tying
  them together, which is the split A-1 removed. Measured, the literal
  `"_enforce_request_boundary"` occurs **once** in the package, in `_boundary_ordering.py`; the only
  other package occurrence of the name is `process_view`'s direct
  `view._enforce_request_boundary(request)` call, which B-2 deliberately keeps greppable. I raise no
  deletion challenge here.
- **A shared recognizer with `middleware/debug_toolbar.py` stays unbuilt, correctly.** R1's hand-off
  item D-6 conditions it on a third middleware or on two needing to agree about one callback; R1b is
  neither, and a security-fix round is not where that consolidation belongs. Recorded as decided
  rather than missed.
- **No second convention was invented.** `_FOREIGN_VIEW_CONSTRUCTIONS` / `_ForeignButBuildableView`
  / `_marked_callback_with_a_foreign_view_class` / `/marked-foreign-view-class/` mirror
  `_VIEW_CLASS_FACTORY_CALLS` / `_view_class_factory` / `_marked_callback_with_a_callable_view_class`
  / `/marked-callable-view-class/` position for position, and the recording docstring states that
  recording is the contract. The fifth route joined the existing parametrization rather than earning
  a sixth decline test.
- **Cross-cohort duplication review: not applicable.** One cohort, one pass, `ownership partition:
  none; sequential rounds`. `repeated string literals: None` in both refreshed shadow overviews, so
  the mechanical half returns nothing either.

### Dispatched findings checklist: all seven ticks audited against the landed code

I neither tick nor un-tick. Audit:

1. **The controlled-response claim** — tick **substantially earned and one qualification short**.
   M-B's measured forgery (`view_class = dict`) is closed: the recognizer answers `None` and no
   exception is raised (Worker 2's measurement, and mine — `dict` answers `False` to the probe on
   both interpreters). The claim is *not* absolute, which is the Medium above. The box is not
   over-ticked in the sense `BUILD.md` penalises (there is a real matching fix); the sentence needs
   scoping.
2. **Five routes, not four** — earned. `tests/test_views.py:3196` now reads "The five routes are the
   five ways", the parametrization carries `/marked-foreign-view-class/`, and the docstring names the
   fifth's mechanism and widens the subject to "a callback the middleware cannot run a boundary for".
   Keeping the node-id stem is the right call, and it is recorded as a decision: two failability
   entries and four passes of records resolve through that identity.
3. **The clause declines on the class before any construction** — earned, and pinned twice: T2's
   recording assertion at the unit level and entry 8's two rows at the mutation level.
4. **The name is `_boundary_ordering.py`'s third fact and costs no import** — earned, and I proved it
   rather than reading the proof. `grep -n 'import'` on that module shows only `__future__`,
   `contextvars`, `typing` and the `TYPE_CHECKING`-guarded `django.http`; and by execution in a fresh
   interpreter after `django.setup()`, differencing `sys.modules` across the import:
   `modules gained: ['django_strawberry_framework._boundary_ordering']`, with
   `django_strawberry_framework.views` and `strawberry.django.views` **absent** and gained on this
   account **False**. The plan's step-6 grep is wrong as written and Worker 2 recorded the correction
   (drift 1) — judged below.
5. **The five over-claiming sites** — earned, with the Medium's qualification on sites 1 and 3.
   Walked all five: site 1 kept verbatim and now true except for the measured residual; site 2 (the
   module docstring's recognition sentence) rewritten to name the boundary probe and the route the
   name travels; site 3 (`::_marked_callback_without_a_view_class`) kept verbatim and now true;
   sites 4 and 5 (T1's docstring, including the exhaustiveness claim) rewritten. Everything else
   describing the old recognition is rewritten too, and the class docstring's #"at the cost of one
   ``getattr`` in ``process_view``" is correctly left alone — it is scoped to a request that is not a
   package view's, and such a request still pays exactly the marker read.
6. **A foreign class's `__init__` is never called** — earned. T2 asserts it in the delta form
   (`len(...) == constructions_before`), which is the form that pins the contract rather than
   today's execution order, and Worker 2's volunteered warning is correct and worth confirming: the
   construction-count assertion is **not** what entry 8's mutant fails on (the `is None` assertion
   fails first). Its job is to refuse a future probe-the-instance refactor, which would answer the
   identical `None` and the identical wire `200`. That is the same reasoning R1 accepted for
   `::test_a_callable_view_class_that_is_not_a_class_is_never_called`, and it is right in both places.
7. **A new entry, 12 and 15 re-measured, nothing in the 0-or-1 band** — earned and independently
   reproduced in full above.

### Non-weakening checks, audited

1. **The four previously tested decline routes are unchanged and route 3 still reaches the
   construction arm** — confirmed by set membership rather than by prose (route 3 in entry 12, absent
   from entry 16), and all five parametrizations pass in `.venv` and at the floor.
2. **The `_CsrfOrderingExemption` contract is untouched** — three set-equal `__bool__` entries, the
   four named declined-callback rows still inside entries 3 and 5, and a three-hunk diff against the
   **index** copy of `_boundary_ordering.py` confirming nothing but the docstring and the new
   constant moved. A declined callback still degrades the CSRF *class* and never the *ordering*.
3. **The newly declined shape inherits the same fallback** — Worker 2 measured the installed and
   uninstalled chains answering identically, which is the property rather than any single value. I
   accept the decision **not** to promote that temp test: the property is a property of *declining*,
   not of which clause declined, and it is already pinned permanently for a declined callback by
   `::test_a_declined_callback_still_gets_a_complete_csrf_check[sync|async]` (read at source — it
   drives the marker-dropping wrapper through `_ORDERED_CHAIN` with both a permissive and an
   enforcing client, so it asserts both strictnesses). A per-route copy would pin the fixture.
4. **Exactly one complete CSRF check in both arrangements** — unchanged row sets of entries 3 and 5;
   entry 14 correctly not re-run (`views.py`, argued per entry).
5. **A genuine mount is recognized at both transports** — T3 plus my own probe table: `True` for
   `DjangoGraphQLView`, `AsyncDjangoGraphQLView` and `_RequestBodyBoundaryMixin` on both
   interpreters. This is the check a suite full of decline rows would not make for itself, and it
   exists.
6. **The public surface does not move** — see below.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` and
`git diff --cached -- django_strawberry_framework/__init__.py` are both **empty**: `__all__` and the
re-export list are unchanged. `middleware/request_body.py`'s `__all__` is still the single-name tuple
`("GraphQLRequestBodyBoundaryMiddleware",)`, so the documented `MIDDLEWARE` string is untouched.
`_BOUNDARY_METHOD` is underscore-prefixed, lives in a private module, and — measured tree-wide —
appears only in `_boundary_ordering.py`, `middleware/request_body.py` and `tests/test_views.py`; it
is re-exported from neither package `__init__.py`. No new public export, as the round's Definition of
Done requires.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. Confirmed by `git status --short CHANGELOG.md`
(clean), and the version quintet is where the cycle-wide declaration says it is: `pyproject.toml`
`version = "0.0.14"` and `django_strawberry_framework/__init__.py` `__version__ = "0.0.14"`, neither
touched.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. Verified rather than
assumed: `git status --short` is clean for `docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`,
`KANBAN.md`, the spec, the rationale, the terms CSV and `tests/base/test_init.py`. The only dirty
`.md` in the tree is Worker 0's build plan and the two artifacts.

### Static helper use

`scripts/review_inspect.py … --output-dir docs/shadow` run by me against **both** production files
(`middleware/request_body.py` — 30+ lines of changed logic plus the complexity note the plan turns
on; and `_boundary_ordering.py`, which is not a pure-class-definition module). No skips. Readings are
in the second Low above; every reference in this section cites original source symbols, never shadow
line numbers.

### Hot-path budget verification

The number **exists**, is stated with metric, command, iteration count and statistic, and
**reproduces as recorded** — which is the whole of my obligation; whether the cost is acceptable is
the maintainer's.

Reproduced with the exact recorded command, two runs in `.venv` and one at the floor:

| Environment | before | after | delta per call | Worker 2 recorded |
| --- | --- | --- | --- | --- |
| `.venv` (Python 3.14.2), run 1 | 0.5136 us | 0.5361 us | **+0.0224 us** | +0.0232 us |
| `.venv` (Python 3.14.2), run 2 | 0.5111 us | 0.5288 us | **+0.0176 us** | +0.0225 us |
| floor (Python 3.10.19) | 0.5594 us | 0.5935 us | **+0.0341 us** | +0.0387 us |

Same sign in all three, same order of magnitude, absolutes within noise of the recorded ones. I read
the benchmark rather than only running it: both arms are in one process over the identical callback,
the "before" arm is a local copy of the pre-R1b body and the "after" arm is the shipped
`_package_view_instance`, so the delta is the probe and nothing else — the same experiment R1
recorded, not a second one. The judgement that a consistent-sign ~20-40 ns is the cost becoming
visible rather than noise is sound: this pass adds a real attribute lookup and a `callable()` call
where R1's change added nothing. Declining to re-capture R1's 400-iteration request median is
correct and correctly *stated* rather than answered "not applicable".

### Floor verification audit

The plan assigns the run to Worker 2's build pass; it happened, and I re-ran it rather than reading
it. Versions read, never recalled:

- `/tmp/dsf-floor/bin/python -V` -> **Python 3.10.19**.
- `uv pip list --python /tmp/dsf-floor/bin/python` -> **django 5.2**, **strawberry-graphql
  0.316.0**, asgiref 3.12.1, channels 4.3.2, daphne 4.2.3, pytest 9.1.1, pytest-django 4.12.0,
  pytest-asyncio 1.4.0, and `django-strawberry-framework 0.0.14` editable at this checkout. That is
  the floor `BUILD.md` `## Floor verification` states, and being editable it carries this round's
  bytes.
- `/tmp/dsf-floor/bin/python -m pytest tests/test_views.py --no-cov` -> **200 passed**, the whole
  declared scope.
- The eight rows the round's subject rests on, each `PASSED` read individually in `-v` output at the
  floor: five parametrizations of `::test_a_marked_callback_the_middleware_cannot_build_is_declined
  _not_crashed`, plus `::test_a_callable_view_class_that_is_not_a_class_is_never_called`, plus T2 and
  T3 — **8 passed**.
- The three floor questions the plan names, all re-answered by me: the probe answers identically at
  3.10 (my own table, `_DisabledBoundary` and both raising-machinery cases included), the named rows
  pass, and the floor hot-path delta is above.
- **The shared `.venv` was not mutated**: read, it carries **Python 3.14.2**, django 6.0.5, asgiref
  3.11.1, strawberry-graphql 0.316.0, pytest 9.0.3 — far above the floor. Every floor command in this
  pass was `/tmp/dsf-floor/bin/python -m pytest` or carried `--python /tmp/dsf-floor/bin/python`, and
  I ran no `uv pip install` at all.

### Test staleness sweep, run independently of the round's file list

`BUILD.md` `### Test staleness a focused run cannot see` names two shapes and neither is present: no
example-model field changed and no wire shape converted. Run anyway, against the tree rather than
against `### Files touched`:

- `grep -rn '_BOUNDARY_MARKER\|graphql_request_body_boundary' tests examples --include='*.py'` — hits
  in **`tests/test_views.py` only** (8). Nothing outside it forges the marker, so nothing outside it
  can have changed answer.
- `grep -rn '_package_view_instance' tests examples --include='*.py'` — three hits, all in
  `tests/test_views.py`.
- `grep -rn '_enforce_request_boundary' tests examples --include='*.py'` — **7** hits, all in
  `tests/test_views.py` (the plan's plan-time reading of 6 plus T3's new line), **none in
  `examples/**`**.
- `grep -rn 'view_class' tests examples --include='*.py'` and read: outside `tests/test_views.py` the
  only hits are `tests/middleware/test_debug_toolbar.py`'s rows for the *sibling* recognizer, which
  this change does not touch. The live tier's wrapper carries no marker, so it is declined at the
  first clause — the same conclusion Worker 2 reached by a corrected route.
- Full sweeps: `uv run pytest tests/ --no-cov` -> **4521 passed, 38 skipped**;
  `tests/test_views.py` -> **200 passed**; `tests/middleware/` -> **17 passed**;
  `examples/fakeshop/test_query/test_transport_api.py` -> **69 passed**. Every total the build report
  states reproduces.
- The `197 -> 200` collection change is arithmetic I can close rather than take on trust: three rows
  were added (T1's fifth parametrization, T2, T3) and **no existing node id disappeared** — the
  strongest evidence being that all 33 node ids across the eight re-run entries, including entry 3's
  thirteen, still resolve.

### Lint / hook gate, re-run read-only

`pre-commit` is not installed here, so its four `language: system` local hooks were run individually,
as R1 established:

- `uv run ruff format --check <the three files>` -> `3 files already formatted`;
  `uv run ruff check <the same three>` -> `All checks passed!`.
- `uv run python scripts/check_trailing_commas.py --check <the three files>` -> exit **0**.
- ASCII-only, verified independently of the hook by byte scan: **0** bytes above 127 in all three.
- `git diff --check` -> exit **0**.
- `kanban-tracked-path-constants`, verified **without writing the baseline-dirty file**:
  `uv run python scripts/build_kanban_tracked_path_constants.py --output <outside-the-repo scratch>`,
  then `cmp` against the tracked copy -> **exit 0**, SHA-256 `6761fadb49c4f285…` on both sides. So
  the generated allowlist really is byte-unchanged and the maintainer's commit will not be rolled
  back. One method note rather than a finding: Worker 2 obtained the same answer by running the
  generator against the tracked path and comparing afterwards, which writes a file this round
  declares out of its write set; the `--output`-to-scratch form R1 established never touches it. The
  outcome here was a genuine no-op — this round adds no tracked path and the one new file was already
  staged by W-1 — so nothing follows from it beyond preferring the non-writing form next time.
- **Nothing new is staged.** `git diff --cached --name-status` is still the single authorized path,
  and `git status --short` at the end of this pass is identical to its state at the start.

### Prose discipline in the diff

Checked mechanically over the added lines of all three files (which for the two `HEAD`-based files
covers R1's additions too, so the result is stronger than asked): **no** severity label, no round /
pass / slice index, no `bld-*.md` filename, no `docs/feedback*.md` mention, no `Test-N` index, no
finding number, and no raw `path:NN` reference. Symbol references use `path::QualifiedName` and
`#"unique substring"`. Spec Decision pointers (`spec-046 Decision 7/9/18`) are present and are the
permitted idiom. The docstrings state invariants, not how the change came to be.

### What looks solid

- **The one clause is the whole fix, and its position is load-bearing rather than incidental.** Four
  flat decline clauses ordered by dependency — marker, bookkeeping shape, boundary, buildable — each
  answering the same `None`, each with its own row set. The claim that they are one recognition and
  not four separable units is right, and the three nested failability entries over one function are
  the evidence.
- **The zero was measured before the fix rather than predicted after it.** That is what makes T4 a
  reading instead of a plausible story, and it is the discipline the acceptance rule is trying to buy.
- **Route 3's survival of the construction arm is measured, not argued** — a set-membership fact, not
  a paragraph. B-4 is the kind of "the guard stays" decision that is usually asserted; here it is not.
- **The manifest was derived programmatically and the inherited entries are byte-identical objects.**
  It converts "set-equal" from "nothing was mistyped" into "nothing moved", and it is cheap enough
  that it should be the default for every inherited manifest.
- **Two plan-time claims were corrected rather than quietly satisfied**, both with the measurement
  that forced the correction and the replacement wording written out. A builder correcting its own
  plan in the open is worth more than a plan that looks prescient.
- **T3 is one row with three assertions and the reasoning for that is right**: `BUILD.md` counts
  rows, and assertions that cannot fail independently would buy a second row that measures nothing.
- **The `_boundary_ordering.py` docstring rewrite is honest about the third fact being static rather
  than per-request**, instead of folding it into "two facts per request" and leaving the title false.
  The module still imports nothing but the standard library, proved by execution.
- **The four-`getattr`-per-recognized-request cost is stated and the non-package path is unchanged**
  — the marker clause is still first, so the request that is not a package view's still pays exactly
  one read, which is what the class docstring claims and why leaving that sentence alone was right.

### Temp test verification

Mine, all under the gitignored `docs/builder/temp-tests/r1b/`:

- `test_w3_predicate_and_consequence.py` — `hasattr` vs `callable` over seven candidates plus the
  consequence at the call site, and the local-copy reproduction of entry 15's zero. Both readings
  reproduce Worker 2's. **Disposition: kept as scratch, not promoted** — the permanent rows that
  matter already exist (T3 for the genuine-mount direction, entry 8's two rows for the decline), and
  a permanent row asserting `_DisabledBoundary` is refused would pin a fixture the recognizer's own
  clause already answers.
- `test_w3_probe_reach.py` — how far the probe's read reaches, and whether the pre-probe recognition
  reached it too. This is the file that separates "new failure mode" from "same failure, earlier
  site", and it says the latter for the descriptor case.
- `test_w3_hook_outcome.py` — the Medium's evidence, driving the **real**
  `GraphQLRequestBodyBoundaryMiddleware.process_view`. **Disposition: noted for follow-up.** It
  should become a permanent row *only if* the maintainer takes the code path in
  `### Notes for Worker 1` item 1; if the resolution is documentary, there is no boundary for it to
  pin and a permanent row would assert today's uncontrolled behaviour as contract.
- Re-ran, unmodified, rather than inheriting their numbers: `test_r1b_hotpath_recognizer.py` (two
  `.venv` runs, one floor run).
- Proof records I emitted: `w3-rerun.md` / `.log` (the eight-entry re-run) and
  `w3-drift-constant.json` / `.md` / `.log` (the constant-side drift). Both scratch roots
  (`.../scratchpad/w3-fail`, `.../scratchpad/w3-drift`) are outside the repository, hold only
  `pristine/`, and hold no `ACTIVE-MUTATION.json` or `RESTORE-FAILED.json`.

### Notes for Worker 1 (spec reconciliation)

R1b writes no spec or rationale text and I add none. The plan's items 1-8 and R1's R2-1..R2-13 stand
unchanged and are not restated. New:

1. **Escalated (contract-level): does the package owe a controlled response to a forged `view_class`
   that runs code while its attributes are read?** This is the residual behind the Medium, and it is
   the same question M-B answered for the `dict` forgery, one layer deeper — so it is a contract call
   and not a worker's. Measured evidence: the shipped `process_view` raises `ValueError` for a forged
   class whose metaclass `__getattr__` raises, and for one carrying a descriptor of that name whose
   `__get__` raises, identically at the floor
   (`docs/builder/temp-tests/r1b/test_w3_hook_outcome.py`). Resolution paths:
   **(i) documentary** — the code stays exactly as it is, and the three sentences named in the Medium
   are scoped to the outcomes the recognition decides, with the residual stated once and both shapes
   of attribute machinery named. Cheapest, keeps the probe minimal, and leaves an honest documented
   limit rather than an absolute; it is what I recommend and what the Medium asks for.
   **(ii) close it** — `except Exception: return None` around the probe. This is *not* the catalogued
   fail-open shape (it converts "the read blew up" into *decline*, the same direction as the existing
   `except TypeError` around the construction), and it would make the absolute literally true. Costs:
   a new boundary owing its own failability entry and rows, and it would swallow a genuine descriptor
   failure on a **package** class — masking a real misconfiguration to defend against a forger M-B
   says the probe is not for. If this path is taken it is a new round, not a wording pass.
   Either way, **Decision 18 must not assert the unqualified absolute** the plan's `### Notes for
   Worker 1` item 4 proposes until the path is chosen.
2. **One further wording refinement for Decision 18, beyond Worker 2's item 4.** Worker 2 is right
   that the contract sentence should say "carries that boundary **as something callable**" rather
   than "carries that boundary" — I reproduced the input that makes the difference reachable (a
   `DjangoGraphQLView` subclass setting the attribute to `None`; `hasattr` True, the probe False, and
   under `hasattr` `process_view` would call `None`). Add that the probe reads a **class** attribute,
   before construction, because "on the class" is what the suite's construction-count rows pin and
   what a future probe-the-instance refactor would silently lose.
3. **The Low about `tests/test_views.py::_wrapper_copying_only_csrf_exempt`'s cited evidence is
   yours to allow or decline on scope grounds.** The sentence is R1's, R1 is closed, and this round's
   scope is "exactly M-B and nothing else"; the fact that falsifies it was measured here. If you
   decline it, record the reason so the next reader does not re-derive the measurement.
4. **`middleware/request_body.py`'s module docstring #"so no non-package view is touched" is now
   materially true and is not literally absolute**, for the same reason as item 1: a forged-marker
   callback's class has one attribute read taken off it. R1 flagged this site because a non-package
   class was *instantiated*; that is gone, which is the substance. Named here only so the sentence is
   not lifted into the spec as an absolute.
5. **A record-completeness note, not a finding.** The complexity reading in
   `### Implementation notes` (68 lines / docstring 212-266) was taken before the pass's last
   docstring correction and reads 69 / 212-267 against the shipped bytes. The re-measured manifest
   and drift auxiliary *were* re-run after that correction and reproduce identically, which is the
   part that mattered; a reading taken before the final edit is the one that rots.

### Review outcome

`revision-needed`.

One Medium and two Lows. The Medium is the round's own subject taken one step further than the round
took it: the probe closed the `500` M-B measured, and the sentence the round exists to make true is
still not true for an input the pass's own stated limit predicts and its measurement of that limit
did not cover — the metaclass `__getattr__` was measured in its returning spelling only, and a
raising one, like a raising descriptor of the probed name, leaves `process_view` uncaught on both
interpreters. The recommended change is documentary and inside this round's write set; the code
change is contract-level and escalated with both paths rather than requested.

Everything else in this pass is in good order and most of it is better than it had to be. All eight
failability entries re-ran **set-equal** at Worker 2's recorded scope with 0 collection/setup errors
and every restore byte-proved; entry 12's growth is exactly the two new rows, entry 16 is a strict
subset of it and disjoint from entry 15, and route 3's membership makes B-4 a measurement. Entry 15's
zero-without-T4 is a real fix to a real pin, reproduced by me without touching a permanent test or a
production file, and T4 weakens nothing. The drift model question resolves in Worker 2's favour and
against its own plan, and I re-measured the constant-side five rows to say so. The floor run, the
hot-path number, the no-import property and the `hasattr`-versus-`callable` design measurement all
reproduce independently, in `.venv` and at the floor. The public surface has not moved, the version
quintet is untouched, the generated tracked-path allowlist is byte-unchanged (verified without
writing it), and the tree is exactly as I found it.

---

## Build report (Worker 2, pass 2)

This pass enacts the build plan's `## Maintainer decision M-C` ("the recognition reads are guarded,
the construction guard stays narrow") and closes both Lows. **No plan-level architectural call
moved**: B-1 (the constant's home and form), B-2 (the coupling pinned by rows rather than by an
import-time guard in `views.py`), B-3 (the probe's shape and position) and B-4 (the construction arm
stays) are all exactly as planned and as shipped in pass 1, and M-C is a maintainer decision rather
than builder drift - so this is **not** the structural-drift pause. The write set did not widen:
`middleware/request_body.py` and `tests/test_views.py` were already this round's, as M-C states.

Judged on merits rather than executed as orders. The review recommends the *documentary* path and
escalates the code path; M-C decided the code path and named the documentary narrowing as the
alternative it rejected, so I build M-C. Two things M-C leaves to the builder, decided here and
recorded under `### Implementation notes`: **where** the guard goes (M-C fixes its scope - the
recognition reads and only those - not its shape), and what the docstring may now assert.

**SHA-256 of the two files this pass writes, recorded before the first edit and again after the
last**, so the production delta is confirmable rather than asserted:

| File | before this pass | after this pass |
| --- | --- | --- |
| `django_strawberry_framework/middleware/request_body.py` | `7154891a17fcc10b05165349223f064d7729f159f3f1d919806911d493d357a3` | `5900fb367db8a944583474eae776051de357884b05b630f2e4ef38dc154044a8` |
| `tests/test_views.py` | `477de139ee5fe8aa8b133d62a431cbc08749f36876447d1d8e719d838eb3bbdc` | `abe0406a26fc9c15b11ec7f3c9619e27a2854ad5d1cf2d8ef5aa733cb74192d5` |

The two "before" values are pass 1's recorded "after" values, so this pass started from exactly the
bytes the review examined. **`_boundary_ordering.py` is byte-unmoved by this pass**
(`7b3d9e51b7fb7ecc4cd578139ad3db2509f638884c20f9c6d637f43645c67bee`, pass 1's value): M-C adds no
fact to the protocol module. **The files R1 left dirty and this round may not touch are byte-unmoved
too**, read at the end of the pass: `views.py` `e8aeb156550fc45a...`, `_request_body.py`
`2c1fd48618d4b01c...`, `tests/test_routers.py` `5bf697bbe27b5d66...`,
`examples/fakeshop/apps/kanban/constants.py` `6761fadb49c4f285...`. `consumers.py` is byte-unmoved
*and* still byte-identical to `HEAD` (`git show HEAD:...` into a scratch path outside the repo, then
`cmp` - exit 0), the property five prior passes recorded.

**The production delta is exactly three hunks, proved rather than described.** I reversed this pass's
three edits on a copy of the shipped file taken to an outside-the-repo scratch path, and the result
is byte-identical to pass 1's recorded SHA - the reconstruction printed
`7154891a17fcc10b05165349223f064d7729f159f3f1d919806911d493d357a3` beside it. So the diff against the
bytes the review read is: the limit paragraph extended to name **both** shapes of attribute
machinery, one new paragraph plus the corrected `isinstance`-ordering sentence, and the guard itself.
That reconstruction is also what let me re-measure the first of the two Lows against the bytes it was
stated about, instead of accepting the reviewer's reading of it.

### The clause, as shipped

```django_strawberry_framework/middleware/request_body.py:285:299
    try:
        if not getattr(view_func, _BOUNDARY_MARKER, False):
            return None
        view_class = getattr(view_func, "view_class", None)
        initkwargs = getattr(view_func, "view_initkwargs", None)
        if not isinstance(view_class, type) or not isinstance(initkwargs, dict):
            return None
        if not callable(getattr(view_class, _BOUNDARY_METHOD, None)):
            return None
    except Exception:  # a read that cannot answer has recognized nothing
        return None
    try:
        return view_class(**initkwargs)
    except TypeError:
        return None
```

All four reads sit inside the guard, which is what M-C names; the review measured two of them (the
class's boundary read through a metaclass `__getattr__` and through a class-level descriptor) and the
callback's own three reads are reachable the same way. The construction keeps its narrow
`except TypeError` **outside** the guard - M-C's second half, and what keeps B-4's argument intact: a
class that cannot be built from the kwargs it names is a *determined* answer, and Django's own
`as_view` closure fails identically for the same request, so nothing is newly swallowed there.

### Files touched

Grounded in `git status --short` taken after the final `ruff format` / `ruff check --fix`
invocations, not from memory:

```
AM django_strawberry_framework/_boundary_ordering.py
 M django_strawberry_framework/_request_body.py
 M django_strawberry_framework/middleware/request_body.py
 M django_strawberry_framework/views.py
 M docs/builder/build-046-transport_security-0_0_15.md
 M examples/fakeshop/apps/kanban/constants.py
 M tests/test_routers.py
 M tests/test_views.py
?? docs/builder/bld-046-r1-remediation_review.md
?? docs/builder/bld-046-r1b-recognition_contract.md
```

Character-for-character the list pass 1 recorded: **no path added, none removed, nothing new
staged.** `_boundary_ordering.py`'s `AM` is W-1's authorized staging with a worktree copy this pass
did not write; `git add` was not run, and nothing was reverted, stashed, checked out or restored.

Written by this pass:

- `django_strawberry_framework/middleware/request_body.py` - the guard around the four recognition
  reads, plus the prose it changes: the limit now names **both** shapes of attribute machinery a
  forged class can carry (the class-level descriptor appeared nowhere in pass 1's diff), a new
  paragraph states that every read is guarded and that an undeterminable answer is the decline, and
  the `isinstance`-ordering sentence is corrected where it over-claimed. Nothing else in the module's
  executable surface changed: `process_view`'s `view._enforce_request_boundary(request)` is still a
  direct call (B-2), the import block gained no name, `__all__` is still the single-name tuple, and
  `__call__`, `__acall__`, `__init__` and `::_require_boundary_before_csrf` are untouched.
- `tests/test_views.py` - two fixture classes carrying the two shapes of raising attribute machinery,
  one callback whose own bookkeeping read raises, two urlpatterns, two new routes on the existing
  decline parametrization, one new parametrized unit test, and the corrected sentence in
  `::_wrapper_copying_only_csrf_exempt`'s docstring.

**Unchanged and not written by this pass**, listed because a reader of the `git status` above will
see them dirty: `_boundary_ordering.py`, `_request_body.py`, `views.py`, `consumers.py`,
`tests/test_routers.py`, `examples/fakeshop/apps/kanban/constants.py` and the build plan are R1's,
Worker 0's, or pass 1's landed uncommitted work.

### Tests added or updated

- `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-raising-metaclass/]`
  and `[/marked-raising-descriptor/]` - the two wire rows, joining the existing parametrization
  rather than earning a test of their own, for the reason the plan gave for the fifth route: the
  assertion is identical (`200` plus a `"marked, "` body), so a sibling test would duplicate it.
  Measured, both are rows of the new guard's failability entry - without the guard the request leaves
  `process_view` on the exception the forged class chose.
  - **The docstring rewrite matters more than the rows.** Pass 1's version claimed "the five routes
    are the five ways a callback can carry the marker without a package view behind it, and no two
    are refused by the same test" - an exhaustiveness claim of exactly the shape this round exists to
    remove, and it is now **seven** routes of **two kinds**: five where the recognition *decides* no
    (no two refused by the same clause) and two where it cannot decide at all because a read raised
    (both refused by the guard, and two routes because the two shapes reach that read by different
    mechanisms). "No two are refused by the same test" is scoped to the first five rather than
    restated over seven, because over seven it is false.
- `tests/test_views.py::test_a_read_that_raises_is_declined_rather_than_raised_out_of_the_hook[metaclass|descriptor|callback-bookkeeping]`
  - three unit rows on the recognizer's own answer, one per read the guard covers: the boundary read
  off the class in each of its two shapes, and a bookkeeping read off the callback itself. Each
  asserts `_package_view_instance(<callback>) is None`. The third input is deliberately **not**
  mounted: a callback that raises on arbitrary attribute reads would break the URL resolver and the
  CSRF middleware's own `csrf_exempt` read as well, so a wire row on it would measure its own
  scaffolding rather than the recognition.
- Fixtures, mirroring the file's existing conventions rather than inventing new ones:
  `_BoundaryReadRaisesMeta` / `_ViewClassWhoseMetaclassRaises`, `_RaisingBoundaryDescriptor` /
  `_ViewClassWhoseBoundaryDescriptorRaises`, `_CallbackWhoseBookkeepingReadRaises` (one instance,
  `_CALLBACK_WHOSE_BOOKKEEPING_READ_RAISES`), and the two marked callbacks beside the existing ones.
  The metaclass raises **only** for the probed name and answers `AttributeError` for everything else,
  so a row measures a read of that name rather than some unrelated introspection of the class. Both
  view classes' `__init__` raise `AssertionError`: this is the recording idiom's fail-loud twin -
  the contract is that a class whose boundary cannot even be *read* is never built, so a construction
  is a failure rather than a recorded call.
- `tests/test_views.py::_wrapper_copying_only_csrf_exempt` - **the first Low, closed.** Its docstring
  cited the repository's own probe mount as an instance of a wrapper copying `csrf_exempt` **plus**
  Django's `view_class` / `view_initkwargs` bookkeeping. Re-measured independently here:
  `examples/fakeshop/test_query/test_transport_api.py::_carrying_the_packages_csrf_mark` executes
  `view.csrf_exempt = mark` and nothing else, and `grep -nE '\.view_class|\.view_initkwargs'` over
  that whole file returns **no lines at all**. The load-bearing half (marker-dropping wrappers are
  reachable and the repo contains one) is true, so the fix is one clause: the probe mount is now
  named as "a leaner member of the same class - copies `csrf_exempt` and nothing else". The fixture's
  behaviour is unchanged; only the citation was wrong.

Baseline and totals, every one a `--no-cov` run:

| Scope | before this pass | after this pass |
| --- | --- | --- |
| `uv run pytest tests/test_views.py --no-cov` | **200 passed** (pass 1's total, re-measured here as this pass's baseline) | **205 passed** |
| `uv run pytest tests/test_views.py examples/fakeshop/test_query/test_transport_api.py --no-cov` | 269 passed (pass 1) | **274 passed** |
| `uv run pytest tests/middleware/ --no-cov` | 17 passed (pass 1) | **17 passed** |
| `uv run pytest tests/ --no-cov` (the staleness sweep) | 4521 passed, 38 skipped (pass 1) | **4526 passed, 38 skipped** |

Every delta is exactly this pass's five new rows; no existing row was re-pinned, weakened or moved.
The staleness sweep is a correctness read rather than a red-test hunt (no model field and no wire
shape changed): re-measured, `grep -rn '_enforce_request_boundary' tests examples --include='*.py'`
returns **7 hits, all in `tests/test_views.py`** (6 before this pass, plus T3's second attribute
read - no `examples/**` hit either way), and the live tier is unchanged at **69 passed** inside the
274 above.

### Validation run

- `uv run ruff format django_strawberry_framework/middleware/request_body.py tests/test_views.py` -
  pass (`2 files left unchanged`). Scoped to this pass's own files, never `.`.
- `uv run ruff check --fix <the same two files>` - pass (`All checks passed!`); no fix applied.
  `BLE001` (blind-except) is **not** in this repo's `select` list, so the `except Exception` needs no
  `noqa`; the package's idiom for the shape is a short inline comment naming the direction, which
  `_request_body.py` uses five times (`#"a probe that cannot report a position has not moved one"`
  and siblings), and this one reads `#"a read that cannot answer has recognized nothing"`.
- `git status --short` after both - quoted verbatim under `### Files touched`. Every modified path is
  round-intended or R1's / Worker 0's landed dirty work; nothing unexpected appeared, so there is
  nothing to stop-and-report and nothing was reverted.
- **`pre-commit` is not installed in this environment**, so its four `language: system` local hooks
  were run individually:
  - `kanban-tracked-path-constants` - `uv run python
    scripts/build_kanban_tracked_path_constants.py` (exit 0), with
    `examples/fakeshop/apps/kanban/constants.py` copied to an outside-the-repo scratch path first and
    byte-compared after: `cmp` exit 0, SHA-256 `6761fadb49c4f285...` on both sides. **This pass adds
    no tracked file**, so the generated allowlist comes out byte-unchanged - the property that stops
    the maintainer's commit being rolled back.
  - `source-layout` - `uv run python scripts/check_trailing_commas.py --check` over the two changed
    files plus `_boundary_ordering.py`, exit **0**. `docs/builder/` is excluded from the markdown
    link-scaffold check, so this artifact owes no link-definition block.
  - `ruff-format` and `ruff-check` read-only over the same three files: `3 files already formatted`,
    `All checks passed!`.
  - ASCII-only re-verified independently of the hook, by byte scan: highest byte 125 in
    `middleware/request_body.py` and `tests/test_views.py`, 124 in `_boundary_ordering.py`.
- `uv run python scripts/review_inspect.py django_strawberry_framework/middleware/request_body.py
  --output-dir docs/shadow` - re-run, because the second Low is about its output.
  **`repeated string literals: 0`**, `Django / ORM markers: None`, `getattr()` still **4x** (the
  guard adds no read), imports unchanged.
- **Prose discipline swept mechanically over both changed files**: `grep -nEc` for
  `feedback|bld-|pass [0-9]|round|Medium|High:|Low:|M-C|slice [0-9]|:[0-9]+` returns **0** in each,
  so no severity label, round or pass index, artifact filename, review-file mention or raw `path:NN`
  reference is anywhere in the diff.
- **The tree was re-verified whole after a transient interruption of this pass**: both changed files
  `ast.parse` clean, the focused scope is green at **205 passed**, `git status --short` is unchanged,
  and no `ACTIVE-MUTATION.json` or `RESTORE-FAILED.json` exists under any scratch root. The
  failability record below therefore still describes the bytes on disk: `tests/test_views.py` has not
  been written since the proof run (SHA `abe0406a...` then and now), and every entry's restore proof
  names the shipped `5900fb36...` / `7b3d9e51...`.

### Dispatched findings checklist

**Nothing ticked this pass, and nothing should be.** The checklist was written before M-C existed, so
it carries no box for the read guard, and all seven boxes were earned and ticked in pass 1. This pass
does not un-earn any of them; it makes the first box ("closed by making the claim **true**") true for
one input class more than pass 1 could claim, which is what the review said was missing. Worker 1's
audit should read M-C's enactment out of this report rather than out of a box.

### Failability proofs

**Manifest: `docs/builder/temp-tests/r1b/proofs-pass2.json`, 9 entries, derived programmatically from
this round's own `proofs.json`** rather than retyped - the four entries whose boundary this pass does
not move were carried over as JSON objects and asserted **character-identical** by sorted-key
comparison, so set-equality below means "nothing moved" and not "nothing was mistyped". Four entries
had to change and one is new, and the reasons are mechanical rather than editorial:

- **Entries 1, 7 and 8 re-indented.** The guard indents the recognition by four spaces, so their
  anchors (which carry leading whitespace) no longer matched. The anchor text is re-indented
  mechanically by the derivation script; the mutation each applies is otherwise unchanged, and each is
  expected **set-equal**.
- **Entry 6 re-anchored, second time in this round.** Its subject is the aggregate - everything the
  recognition does after the marker clause and the two `getattr`s - and the guard now wraps that
  aggregate, so a mutation that removes the aggregate has to remove the guard with it. Anchoring it to
  the guarded block only, with the construction replacement inside the `try`, would have made the
  guard **absorb** the very failures the entry exists to produce: predicted, and the reason I did not
  write it that way. Its anchor is now the whole 15-line body and its replacement restates the marker
  clause and the two reads verbatim, so what stays live is exactly what stayed live before. Label and
  mutation prose updated to name the guard, because a label naming a mutation it is no longer about is
  the false reading a prior review filed a finding about.
- **Entry 9 added** - the round's second new boundary, and the one M-C says the manifest owes. Anchor
  is the guarded block; replacement is the same four reads and three clauses **dedented, with the
  `try` / `except Exception` removed** - i.e. exactly pass 1's shipped shape, so the mutation removes
  the boundary and perturbs nothing else.

`--check-anchors-only` was run **first and separately** (**exit 0**: all 9 anchors matched exactly
once *before any copy was taken*, which is also what says no prior pass left a live mutation). The
full set then ran in **one** invocation, **exit 0**: every entry proved, **no boundary weakly
pinned**, **0 collection/setup errors** anywhere, every pre-mutation baseline **205 passed** at exit
0, and every restore proved by `filecmp.cmp(shallow=False)` plus SHA-256 against the runner's own
pre-mutation copy. Scratch root outside the repository (`.../scratchpad/fail-p2`); it holds only
`pristine/` and no `ACTIVE-MUTATION.json`.

**Node-id set movement against pass 1, computed by symmetric difference over the parsed lists rather
than by comparing counts:**

| # | pass 1 | pass 2 | Direction |
| --- | --- | --- | --- |
| 1 (marker clause) | 4 | **4** | **set-equal** - a movement here would be contamination |
| 2 (`__bool__`, always true) | 3 | **3** | **set-equal** |
| 3 (`__bool__`, always false) | 13 | **13** | **set-equal** |
| 4 (`_require_boundary_before_csrf`) | 3 | **3** | **set-equal** |
| 5 (`__bool__`, per-request key) | 7 | **7** | **set-equal** |
| 6 (the aggregate recognition) | 7 | **12** | **grew (+5, none lost)** - exactly this pass's five new rows |
| 7 (the two shape clauses) | 2 | **2** | **set-equal** |
| 8 (the boundary probe) | 2 | **6** | **grew (+4, none lost)** - measured, not intended; read below |
| 9 (the guard around the reads) | - | **5** | new: the two wire routes and all three unit rows |

Four readings the sets give that the counts would hide:

- **Entry 9 sits at 5 rows**, above the 0-or-1 band and above Worker 3's mandatory re-run floor of 3.
  Its rows are the two new wire routes plus all three parametrizations of
  `::test_a_read_that_raises_is_declined_rather_than_raised_out_of_the_hook`. The unit rows are the
  ones that discriminate the *answer* (`None` rather than a raise); the wire rows are the ones that
  discriminate the *outcome the hook produces*, which is the property M-C is about.
- **Entry 8 grew from 2 to 6, and this was not predicted.** Removing the probe means the two new
  forged classes are *constructed*, and their `__init__` raises `AssertionError` - not `TypeError`, so
  the construction arm does not absorb it - and the two matching unit rows fail on the same raise.
  Nothing was lost from its pass-1 set. Worth saying plainly rather than presenting as design: the new
  fixtures strengthen the probe's pin as a side effect, and I did not add them for that.
- **Entry 6's growth is exactly the five new rows and its set strictly contains entry 9's**, which is
  the evidence the two are not redundant: entry 6 removes the shape tests, the probe, the guard and
  the construction at once; entry 9 removes only the guard. Route 3
  (`/marked-rejected-initkwargs/`) remains in entry 6's set and is absent from entries 8 and 9, which
  is B-4's justification still measured rather than argued - that route still reaches the construction
  arm, so removing the arm would restore an unhandled `500` for a row the suite already pins.
- **Nothing else moved.** Entries 1, 4, 6, 7, 8 and 9 mutate `middleware/request_body.py`; entries 2,
  3 and 5 mutate `_boundary_ordering.py`, which this pass did not write. Every inherited entry is
  set-equal, so neither the guard nor three docstring rewrites changed any other boundary's
  measurement.

**Seven R1 entries were again deliberately not re-run, and per the plan this is stated per entry
rather than in aggregate.** Entries 1, 2, 7 and 14 of R1's manifest target `views.py`; entry 8 targets
`_request_body.py`; entries 9, 10 and 11 target `consumers.py`. All three files are outside this
round's write set and dirty with R1's uncommitted work, so mutating them for a stability check trades
a real risk (a failed restore on uncommitted work) for a measurement obtainable otherwise. What could
move their sets is only a new row exercising their boundary, and none of this pass's five does: the
two wire rows drive a bare `GET` with no body, no `Content-Type`, no declared charset, no multipart
envelope and no socket, to a route whose callback is declined and whose view is a plain function - so
R1's charset guard and its GET/multipart carve-out cannot see them, `::_enforce_request_boundary_once`
is never entered, `_measured_remaining` needs a measurable body, the two `csrf_protect` continuations
need a package mount and the consumer entries need a WebSocket; and the three unit rows call
`_package_view_instance` directly with no request at all. Their unmutated green state is recorded nine
times over as the pre-mutation baseline of the entries that did run (**205 passed**, exit 0, each
time). **This pass mutated no file outside its write set at all** - unlike pass 1, it owed no
`views.py` drift measurement, and `views.py`'s SHA is unchanged end to end.

**The emitted record follows verbatim, every measured field filled in by the runner. No entry is a
zero-row entry, so no `why 0` judgement is owed.**

Procedure, mechanized by `scripts/prove_failability.py`: the target is copied to a scratch path OUTSIDE the repo before any mutation; the mutation site is located by an exact anchor asserted to match exactly once (any other count aborts the entry without writing); the same focused scope is run unmutated first, so rows already failing before the mutation are differenced out of the count; both runs' pytest exit codes are read, because a run that collected nothing or blew up emits no `FAILED` lines and would otherwise be recorded as a measured zero; both runs use `--no-cov`; the file is restored from the pre-mutation copy in a `finally` and the restore is proved by `filecmp.cmp(shallow=False)` plus a SHA-256 comparison. One boundary at a time, restored before the next. `git` is never invoked - the tree is legitimately dirty, so an empty `git diff` is unachievable and forcing one would destroy the build's own work.

| # | Boundary | File mutated | Mutation applied | Rows failed | Errors | Scope as run | Restore proof |
|---|---|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not getattr(view_func, _BOUNDARY_MARKER, False)"` | `django_strawberry_framework/middleware/request_body.py` | `if not getattr(view_func, _BOUNDARY_MARKER, False):` -> `if True:` - builder's description (unverified prose): the recognition made unconditionally negative: _package_view_instance always answers None, so the chain never runs the boundary and never stamps the request | **4** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 5900fb367db8a944... == 5900fb367db8a944... (vs pre-mutation copy) |
| 2 | `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__` | `django_strawberry_framework/_boundary_ordering.py` | `request = _boundary_middleware_request.get() return request is None or not getattr(request, _BOUNDARY_ENFORCED, False)` -> `return True` - builder's description (unverified prose): the withdrawal removed: the exemption is always truthy, so the configured CSRF middleware always skips the callback | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 7b3d9e51b7fb7ecc... == 7b3d9e51b7fb7ecc... (vs pre-mutation copy) |
| 3 | `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (opposite direction)` | `django_strawberry_framework/_boundary_ordering.py` | `request = _boundary_middleware_request.get() return request is None or not getattr(request, _BOUNDARY_ENFORCED, False)` -> `return False` - builder's description (unverified prose): the exemption is always withdrawn, so the view-local arrangement loses its ordering on a chain that does not supply one | **13** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 7b3d9e51b7fb7ecc... == 7b3d9e51b7fb7ecc... (vs pre-mutation copy) |
| 4 | `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf` | `django_strawberry_framework/middleware/request_body.py` | `boundary_index = csrf_index = None` -> `return boundary_index = csrf_index = None` - builder's description (unverified prose): the ordering audit short-circuited before it reads MIDDLEWARE, so a misordered chain is accepted at startup | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 5900fb367db8a944... == 5900fb367db8a944... (vs pre-mutation copy) |
| 5 | `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (the per-request key)` | `django_strawberry_framework/_boundary_ordering.py` | `request = _boundary_middleware_request.get() return request is None or not getattr(request, _BOUNDARY_ENFORCED, False)` -> `return _boundary_middleware_request.get() is None` - builder's description (unverified prose): the per-request key removed and the defective predecessor restored: the exemption is withdrawn because a boundary middleware is handling the request, whether or not it ran the boundary for it | **7** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 7b3d9e51b7fb7ecc... == 7b3d9e51b7fb7ecc... (vs pre-mutation copy) |
| 6 | `django_strawberry_framework/middleware/request_body.py::_package_view_instance (the whole recognition after the marker clause and the two getattrs: both bookkeeping-shape tests, the boundary probe, the read guard and the construction attempt)` | `django_strawberry_framework/middleware/request_body.py` | `try: if not getattr(view_func, _BOUNDARY_MARKER, False): return None view_class = getattr(view_func, "view_class", No...` -> `if not getattr(view_func, _BOUNDARY_MARKER, False): return None view_class = getattr(view_func, "view_class", None) i...` - builder's description (unverified prose): the whole recognition after the marker clause and the two getattrs deleted - both isinstance clauses, the boundary probe, the guard around the reads and the construction attempt - so a marked callback's view_class and view_initkwargs are dereferenced and splatted unguarded and any callback the class cannot be built from, that carries no boundary, or whose reads raise, becomes an unhandled 500 out of process_view | **12** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 5900fb367db8a944... == 5900fb367db8a944... (vs pre-mutation copy) |
| 7 | `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not isinstance(view_class, type)"` | `django_strawberry_framework/middleware/request_body.py` | deleted: `if not isinstance(view_class, type) or not isinstance(initkwargs, dict): return None` - builder's description (unverified prose): the two bookkeeping-shape tests deleted with the construction attempt left standing, so a view_class that is callable and is not a class is CALLED instead of refused and process_view reads the boundary off whatever it answers | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 5900fb367db8a944... == 5900fb367db8a944... (vs pre-mutation copy) |
| 8 | `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not callable(getattr(view_class, _BOUNDARY_METHOD, None))"` | `django_strawberry_framework/middleware/request_body.py` | deleted: `if not callable(getattr(view_class, _BOUNDARY_METHOD, None)): return None` - builder's description (unverified prose): the class-level boundary probe deleted, so a marked callback whose view_class is a real, buildable class carrying no body boundary is CONSTRUCTED and process_view then reads the boundary method off a foreign instance | **6** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 5900fb367db8a944... == 5900fb367db8a944... (vs pre-mutation copy) |
| 9 | `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"except Exception:  # a read that cannot answer has recognized nothing"` | `django_strawberry_framework/middleware/request_body.py` | `try: if not getattr(view_func, _BOUNDARY_MARKER, False): return None view_class = getattr(view_func, "view_class", No...` -> `if not getattr(view_func, _BOUNDARY_MARKER, False): return None view_class = getattr(view_func, "view_class", None) i...` - builder's description (unverified prose): the guard around the recognition reads removed, the four reads left standing exactly as they are - so a marked callback whose bookkeeping read, or whose view_class's boundary read, raises instead of answering leaves process_view on that exception, since getattr's default absorbs AttributeError alone and the recognizer is called outside any except | **5** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 5900fb367db8a944... == 5900fb367db8a944... (vs pre-mutation copy) |

Verdicts:

1. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not getattr(view_func, _BOUNDARY_MARKER, False)"` - pinned
2. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__` - inside Worker 3's mandatory re-run floor (<= 3 rows)
3. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (opposite direction)` - pinned
4. `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf` - inside Worker 3's mandatory re-run floor (<= 3 rows)
5. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (the per-request key)` - pinned
6. `django_strawberry_framework/middleware/request_body.py::_package_view_instance (the whole recognition after the marker clause and the two getattrs: both bookkeeping-shape tests, the boundary probe, the read guard and the construction attempt)` - pinned
7. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not isinstance(view_class, type)"` - inside Worker 3's mandatory re-run floor (<= 3 rows)
8. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not callable(getattr(view_class, _BOUNDARY_METHOD, None))"` - pinned
9. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"except Exception:  # a read that cannot answer has recognized nothing"` - pinned

Failing node ids, per boundary (the count above is `len()` of this list):

1. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not getattr(view_func, _BOUNDARY_MARKER, False)"`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 4 failed, 201 passed in 1.70s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 205 passed in 1.63s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[sync]`
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[async]`
   - `tests/test_views.py::test_the_view_does_not_measure_a_body_the_chain_already_measured[sync]`
   - `tests/test_views.py::test_the_view_does_not_measure_a_body_the_chain_already_measured[async]`
2. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__`
   - file mutated: `django_strawberry_framework/_boundary_ordering.py`
   - pytest summary: `======================== 3 failed, 202 passed in 1.65s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 205 passed in 1.60s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[sync]`
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[async]`
   - `tests/test_views.py::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`
3. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (opposite direction)`
   - file mutated: `django_strawberry_framework/_boundary_ordering.py`
   - pytest summary: `======================== 13 failed, 192 passed in 1.66s ========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 205 passed in 1.65s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark[sync]`
   - `tests/test_views.py::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark[async]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[sync]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[async]`
   - `tests/test_views.py::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[sync]`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[async]`
   - `tests/test_views.py::test_the_same_two_mounts_parse_nothing_without_the_middleware_either[sync]`
   - `tests/test_views.py::test_the_same_two_mounts_parse_nothing_without_the_middleware_either[async]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[sync]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[async]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[sync]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[async]`
4. `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 3 failed, 202 passed in 1.67s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 205 passed in 1.67s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_chain_that_lists_the_boundary_after_csrf_is_refused_at_startup`
   - `tests/test_views.py::test_a_boundary_subclass_listed_after_csrf_is_refused_at_startup`
   - `tests/test_views.py::test_the_first_csrf_entry_is_the_one_the_ordering_is_measured_against`
5. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (the per-request key)`
   - file mutated: `django_strawberry_framework/_boundary_ordering.py`
   - pytest summary: `======================== 7 failed, 198 passed in 1.84s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 205 passed in 1.63s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[sync]`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[async]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[sync]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[async]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[sync]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[async]`
6. `django_strawberry_framework/middleware/request_body.py::_package_view_instance (the whole recognition after the marker clause and the two getattrs: both bookkeeping-shape tests, the boundary probe, the read guard and the construction attempt)`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 12 failed, 193 passed in 1.62s ========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 205 passed in 1.78s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-no-view-class/]`
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-bad-initkwargs/]`
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-rejected-initkwargs/]`
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-callable-view-class/]`
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-foreign-view-class/]`
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-raising-metaclass/]`
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-raising-descriptor/]`
   - `tests/test_views.py::test_a_callable_view_class_that_is_not_a_class_is_never_called`
   - `tests/test_views.py::test_a_view_class_without_the_boundary_is_never_constructed`
   - `tests/test_views.py::test_a_read_that_raises_is_declined_rather_than_raised_out_of_the_hook[metaclass]`
   - `tests/test_views.py::test_a_read_that_raises_is_declined_rather_than_raised_out_of_the_hook[descriptor]`
   - `tests/test_views.py::test_a_read_that_raises_is_declined_rather_than_raised_out_of_the_hook[callback-bookkeeping]`
7. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not isinstance(view_class, type)"`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 2 failed, 203 passed in 1.58s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 205 passed in 1.56s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-callable-view-class/]`
   - `tests/test_views.py::test_a_callable_view_class_that_is_not_a_class_is_never_called`
8. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not callable(getattr(view_class, _BOUNDARY_METHOD, None))"`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 6 failed, 199 passed in 1.66s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 205 passed in 1.58s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-foreign-view-class/]`
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-raising-metaclass/]`
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-raising-descriptor/]`
   - `tests/test_views.py::test_a_view_class_without_the_boundary_is_never_constructed`
   - `tests/test_views.py::test_a_read_that_raises_is_declined_rather_than_raised_out_of_the_hook[metaclass]`
   - `tests/test_views.py::test_a_read_that_raises_is_declined_rather_than_raised_out_of_the_hook[descriptor]`
9. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"except Exception:  # a read that cannot answer has recognized nothing"`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 5 failed, 200 passed in 1.59s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 205 passed in 1.57s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-raising-metaclass/]`
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-raising-descriptor/]`
   - `tests/test_views.py::test_a_read_that_raises_is_declined_rather_than_raised_out_of_the_hook[metaclass]`
   - `tests/test_views.py::test_a_read_that_raises_is_declined_rather_than_raised_out_of_the_hook[descriptor]`
   - `tests/test_views.py::test_a_read_that_raises_is_declined_rather_than_raised_out_of_the_hook[callback-bookkeeping]`

A boundary whose removal fails 0 or 1 rows is **weakly pinned** and is `revision-needed` per `docs/builder/BUILD.md` - the fix is more or better-targeted rows, never a weaker boundary. A boundary at 3 rows or fewer is inside Worker 3's mandatory independent re-run floor. A proof carrying collection or setup errors, or whose pytest run exited anything but 0 or 1 (nothing collected, interrupted, internal error, usage error), is not a valid count at all - and a 0 from such a run is not a zero-row result: resolve it and re-run.

Every `<fill in ...>` above is a judgement no tool can make and MUST be replaced by hand before this subsection is submitted: weakly pinned and harness-impossible are the two possible readings of a zero-row result and they prescribe opposite responses (more rows, versus a production-call-site invariant assertion plus a recorded harness limitation), so a record that does not name one reads as self-contradictory.

#### Two auxiliary measurements this pass owed, and one it did not repeat

- **The enactment itself, measured against the real hook rather than a copy.**
  `docs/builder/temp-tests/r1b/test_w2p2_hook_outcome_after_the_guard.py` drives
  `GraphQLRequestBodyBoundaryMiddleware.process_view` - the shipped object, under
  `override_settings(MIDDLEWARE=[])` - over the three inputs, and prints what came back. Identical in
  `.venv` (Python 3.14.2) and at the floor (Python 3.10.19):

  ```
    metaclass __getattr__ raises: controlled: returned None
    class descriptor __get__ raises: controlled: returned None
    callback bookkeeping read raises: controlled: returned None
    a PACKAGE class whose boundary read raises: still loud in the view-local path: ValueError: descriptor __get__ raised
    a genuine mount recognizes as: DjangoGraphQLView
  ```

  The first three are the review's two measured shapes plus the callback-side read, and each is now a
  controlled `None` where the review measured `UNCONTROLLED: ValueError out of process_view`. The
  fourth line is **the docstring claim I would otherwise have asserted**: a genuine package subclass
  whose boundary read raises still raises in
  `views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once`, which is exactly what a
  declined request goes on to run - so the guard moves no package misconfiguration into silence. The
  fifth is the check a suite full of decline rows would not notice on its own: the guard did not turn
  recognition into a blanket decline.
- **The newly declined shapes inherit the same fallback, on both chains.**
  `docs/builder/temp-tests/r1b/test_w2p2_fallback_equivalence_for_a_raising_read.py`, the sibling of
  pass 1's equivalence probe, drives both new shapes through `[boundary, observing CSRF subclass]` and
  through `[observing CSRF subclass]` alone, with a **CSRF-enforcing** client (the default client sets
  `_dont_enforce_csrf_checks`, and my first reading of `200` was measuring the fixture rather than the
  code - recorded because it is the same trap R1's `_csrf_enforcing_client` note names):

  ```
    /w2p2-metaclass-raises/  installed:   (403, {'stamp': False, 'callback_exempt': False, 'reached': True})
    /w2p2-metaclass-raises/  uninstalled: (403, {'stamp': False, 'callback_exempt': False, 'reached': True})
    /w2p2-descriptor-raises/ installed:   (403, {'stamp': False, 'callback_exempt': False, 'reached': True})
    /w2p2-descriptor-raises/ uninstalled: (403, {'stamp': False, 'callback_exempt': False, 'reached': True})
    constructions across every chain: []
  ```

  Identical answers on both chains, at both interpreters: the configured CSRF class runs and refuses
  in both arrangements, the stamp is absent in both, and neither class is ever constructed. The
  equivalence - not any single value - is the property, and pass 1's own equivalence probe still
  reproduces unchanged (`installed`/`uninstalled` both `200` with `callback_exempt True`, no
  constructions).
- **The drift auxiliary was not repeated.** B-2's coupling is untouched by this pass, pass 1 measured
  it from both sides and the review re-measured the constant side itself at 5 rows. Repeating it would
  mean mutating `views.py` - outside the write set - for a claim nothing in this diff bears on.

### Hot-path budget

**Declared hot-path, inherited from R1**: the recognizer runs once per marked callback in
`process_view`. The guard adds one `try` frame around reads that already happened and **no new read**,
on the recognized path only; a non-package request still pays the marker test alone.

**Metric: the same recognizer micro-benchmark, one arm re-pointed** -
`docs/builder/temp-tests/r1b/test_r1b_p2_hotpath_recognizer.py`, copied from this round's pass-1
snippet with the "before" arm now the pass-1 body (marker, two `getattr`s, the `isinstance` pair, the
boundary probe, the construction `try`) and the "after" arm the shipped `_package_view_instance`, so
the delta is the guard and nothing else. Both arms in **one** process over the identical callback,
`timeit`, **200,000** iterations, statistic = total seconds / iterations.

```shell
uv run pytest docs/builder/temp-tests/r1b/test_r1b_p2_hotpath_recognizer.py -s -o addopts="" --no-cov
/tmp/dsf-floor/bin/python -m pytest docs/builder/temp-tests/r1b/test_r1b_p2_hotpath_recognizer.py -s -o addopts="" --no-cov
```

| Environment | before (per call) | after (per call) | delta per call |
| --- | --- | --- | --- |
| shared `.venv` (3.14.2), run 1 | 0.5323 us | 0.6148 us | **+0.0825 us** |
| shared `.venv` (3.14.2), run 2 | 0.5523 us | 0.5515 us | **-0.0008 us** |
| shared `.venv` (3.14.2), run 3 | 0.5383 us | 0.5374 us | **-0.0010 us** |
| shared `.venv` (3.14.2), run 4 | 0.5253 us | 0.5278 us | **+0.0025 us** |
| shared `.venv` (3.14.2), run 5 | 0.5364 us | 0.5293 us | **-0.0071 us** |
| floor (3.10.19), run 1 | 0.5893 us | 0.5915 us | **+0.0023 us** |
| floor (3.10.19), run 2 | 0.6072 us | 0.5942 us | **-0.0129 us** |
| floor (3.10.19), runs 3-5 | - | - | **+0.0009, +0.0023, -0.0016 us** |

**Reading: the guard's cost is below this metric's resolution on both interpreters, and the sign is
not reproducible.** Nine of the ten readings lie in -0.0129 to +0.0025 us and straddle zero; run 1's
+0.0825 us is a first-run outlier whose sign the four later `.venv` runs do not reproduce, and it is
recorded rather than dropped because a discarded reading is an unrecorded one. That is the expected
shape: a `try` that raises nothing is zero-cost on 3.11+, and R1 already measured it at ~15 ns at the
3.10 floor, which is inside this band. **Five readings per environment rather than the two the plan
asks for**, precisely because a single pair would have made run 1 look like the number.

Absolutes are stated as measured and not as a band they sit inside: 0.5253-0.6148 us in `.venv` and
0.5893-0.6072 us at the floor, **above** R1 pass 3's recorded 0.50-0.53 us - see
`#### Corrections to earlier sections of this artifact`, since that is the second Low. R1's own
standing figure is a worst reading of ~15 ns per request against a ~314 us request.

**Metric 1, R1's 400-iteration request median, is deliberately not re-captured**: the R1 plan and two
R1 review passes recorded that it cannot resolve a change of this size against ~313 us of request,
and this change is smaller than the one that could not be resolved. Said rather than answered "not
applicable", because the declaration is inherited and an empty answer reads the same as an unmeasured
one. Whether the cost is acceptable is the maintainer's call and no worker's; no correctness boundary
was weakened to buy any of it back.

### Floor verification

**This pass owns the run**, per the plan's `### Floor verification scope` (scope: `tests/test_views.py`
- the change is on the request-lifecycle path, a Django integration seam). Floor facts taken from
`BUILD.md` `## Floor verification`, its single canonical statement, never from memory or a number
restated elsewhere: the supported floor is **Django 5.2.0 on Python 3.10 with strawberry-graphql
0.316.0**.

`/tmp/dsf-floor` existed and was **reused only after reading its resolved versions**, not after
inheriting pass 1's reading:

- `/tmp/dsf-floor/bin/python -V` -> **Python 3.10.19**.
- `uv pip list --python /tmp/dsf-floor/bin/python`, read this pass: **django 5.2**,
  **strawberry-graphql 0.316.0**, asgiref 3.12.1, channels 4.3.2, daphne 4.2.3, django-filter 26.1,
  django-debug-toolbar 7.0.0, djangorestframework 3.17.1, pytest 9.1.1, pytest-django 4.12.0,
  pytest-asyncio 1.4.0, and **django-strawberry-framework 0.0.14** editable at
  `/Users/riordenweber/projects/django-strawberry-framework`. So it **is** the floor, and being
  editable against this checkout it carries this pass's change.
- `/tmp/dsf-floor/bin/python -m pytest tests/test_views.py --no-cov` -> **205 passed**. The declared
  scope, green.
- The rows this pass's subject rests on, named individually rather than hidden inside a green
  aggregate: all **seven** parametrizations of
  `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed`, all three of
  `::test_a_read_that_raises_is_declined_rather_than_raised_out_of_the_hook`, plus
  `::test_a_callable_view_class_that_is_not_a_class_is_never_called`,
  `::test_a_view_class_without_the_boundary_is_never_constructed` and
  `::test_the_probed_boundary_method_is_the_one_the_package_views_define` - **13 passed**, each
  `PASSED` read individually in `-v` output.
- The floor questions this pass creates, all answered by execution: the three hook outcomes and the
  package-class loudness reading are **byte-identical** between the two interpreters; both
  fallback-equivalence probes answer identically at the floor; pass 1's probe-answer and
  `hasattr`-versus-`callable` tables re-run unmodified and reproduce exactly, `_DisabledBoundary` and
  the metaclass case included; and the hot-path deltas at the floor are the five readings tabulated
  above.
- **The shared `.venv` was never installed into**, read rather than asserted: `uv pip list` reports
  **django 6.0.5**, strawberry-graphql 0.316.0, asgiref 3.11.1, pytest 9.0.3, and `.venv/bin/python
  -V` is **Python 3.14.2** - far above the floor, so no floor install leaked into it. Every floor
  command was invoked as `/tmp/dsf-floor/bin/python -m pytest` or carried an explicit
  `--python /tmp/dsf-floor/bin/python`, and **no `uv pip install` was run in this pass at all**.

### Implementation notes

- **The guard is one `try` inside `_package_view_instance`, not a helper.** M-C fixes the guard's
  scope and not its shape, so this was mine to decide, and the alternative I weighed and rejected was
  extracting the four reads into a `_recognized_boundary_view_class(view_func)` helper and guarding
  the call. It has one real attraction - it leaves entries 7 and 8's anchors byte-identical, because
  nothing is re-indented - and it loses on the plan's own recorded ground: `### DRY analysis` decided
  "new helpers justified: none", `### Boundary count and the split question` decided that splitting
  this function "would produce two halves neither of which is 'the answer the hook branches on'", and
  a helper whose body is the whole recognition and whose caller is three lines is that split under
  another name. Anchor churn in a per-cycle scratch manifest is the cheaper cost, and it is paid once,
  mechanically, by the derivation script.
- **`except Exception`, not `except (AttributeError, TypeError, ValueError)`.** The enumerable list is
  a guard written against input spellings, which `BUILD.md` `### Fail-open shapes` names as a guess;
  the answer being guarded is *did this read produce an answer*, and any exception means it did not.
  It is also not the catalogued bare-except shape: that one converts "the check blew up" into "the
  check passed", and this one converts it into **decline**, the same direction as the existing
  `except TypeError` and the arm that enforces more rather than less. `except BaseException` was
  rejected in the other direction - a `KeyboardInterrupt` or a `SystemExit` raised while reading an
  attribute is not an answer this function should convert into anything.
- **Why the construction stayed outside the guard even though one `try` would read better.** That is
  M-C's second half and the rejected broad alternative, and the code reason survives the decision:
  inside one guard, a package mount whose `__init__` raises something other than `TypeError` - a real
  misconfiguration - would become a silent decline, whereas today it fails exactly as Django's own
  `as_view` closure would for the same request. The docstring now states that asymmetry as the
  invariant rather than as a preference: a class that cannot be built from the kwargs it names is a
  determined answer; a read that raises is no answer at all.
- **The `isinstance`-ordering sentence was over-claiming in the direction the review warned about, and
  is corrected.** It read: the two tests stay ahead so "the attribute read is a class attribute lookup
  rather than an arbitrary object's `__getattr__`". A class attribute lookup *does* consult the
  class's metaclass `__getattr__`, which is the very mechanism M-C turns on, so the sentence implied an
  elimination where the ordering only buys a **narrowing**. It now says the read is taken off a class
  rather than an arbitrary object, "which narrows whose attribute machinery can run, a class's own
  metaclass and descriptors rather than any object's `__getattr__`, and does not eliminate it".
- **The limit paragraph names the second shape.** Pass 1's version named only the metaclass
  `__getattr__`; a class-level descriptor under the probed name is the other shape and appeared nowhere
  in that diff. Both are now named, and the sentence that follows - "the probe is here so that every
  outcome of the hook is a controlled response" - is **kept verbatim**, because M-C's decision is what
  makes it true rather than aspirational.
- **Fixture shapes chosen for what they discriminate, not for coverage.** The metaclass raises only for
  the probed name (everything else answers `AttributeError`), so a row measures a read of that name
  rather than incidental introspection; the two forged classes' `__init__` raise rather than record,
  because "never built" is the contract and a raise is the loudest way to state it - and that choice is
  visible in entry 8's growth, where the raise is what those rows fail on. The callback-side input is
  an instance with the marker in `__dict__` and a raising `__getattr__`, and it is unmounted for the
  reason given under `### Tests added or updated`.
- **The five new rows are two kinds deliberately.** Three unit rows pin the recognizer's *answer*
  (`None`), two wire rows pin the *hook's outcome* (a controlled `200` through a real chain). Entry 9
  fails all five, so neither kind is carrying the entry alone, and the unit rows are the ones that stay
  meaningful if a future refactor changes how the wire renders a decline.
- **Complexity, re-judged rather than left implicit.** `scripts/review_inspect.py` now reports
  `_package_view_instance` at **89 lines and 8 branch nodes**, symbol lines 211-299 with the docstring
  at 212-284 - so **73 of the 89 lines are docstring** and the executable body is 16 lines: four flat
  decline clauses, the read guard, the construction guard. The branch count rises by 2 (the `Try` and
  its `ExceptHandler`) and no clause was added. Judged and accepted for the reason the plan gave and the
  review agreed with: splitting the function would invalidate four failability anchors to produce two
  halves neither of which is the answer the hook branches on. Worker 3 is free to disagree with the
  judgement; it should not be surprised by it.

#### Corrections to earlier sections of this artifact

`ARTIFACT.md` forbids editing a prior section, so the two numbers the review found unreproducible are
corrected here, each by my own re-measurement rather than by repeating the reviewer's reading.

- **The complexity reading in pass 1's `### Implementation notes` ("68 lines and 6 branch nodes",
  "docstring at lines 212-266 of a function spanning 211-278") is wrong by one on all three spans, and
  I measured that against the bytes it was stated about.** The reviewer reported 69 lines / 211-279 /
  212-267 and reproduced the branch count. I reconstructed pass 1's shipped file byte-exactly (the
  reversal described at the head of this report, SHA `7154891a17fcc10b...`) and ran the same span and
  branch-node computation `review_inspect.py` uses over both generations: **pass 1 = span 211-279 (69
  lines), docstring 212-267, 6 branch nodes**; **shipped now = span 211-299 (89 lines), docstring
  212-284, 8 branch nodes**. So the reviewer's correction is right, the load-bearing half (the branch
  count) was right in pass 1, and the cause is the one the reviewer named: the reading was taken before
  that pass's last docstring edit. The current numbers above are the operative ones.
- **The hot-path sentence "The absolute per-call figures (0.51-0.59 us) sit inside R1 pass 3's recorded
  0.50-0.53 us band on both interpreters" is false, and I reproduce the falsity rather than concede
  it.** 0.59 is not inside 0.50-0.53, and my own ten readings this pass run 0.5253-0.6148 us in
  `.venv` and 0.5893-0.6072 us at the floor - **above** that band throughout at the floor. The band
  claim was inherited loose phrasing (R1's own pass-4 review wrote the same shape of sentence) and it is
  decoration in both passes: the **delta measured between two arms in one process** is the metric,
  precisely because the absolutes move with the machine. This report states the absolutes as measured
  and does not place them inside any band.
- Neither correction changes a reading, a verdict or a decision in pass 1's report; both are recorded
  so the next reader does not re-derive them, and so the second one does not propagate a third time.

### Notes for Worker 3

- **The failability records live in gitignored scratch**, so this report carries the emitted block
  verbatim. The operative manifest is `docs/builder/temp-tests/r1b/proofs-pass2.json` (9 entries);
  `proofs.json` in the same directory is pass 1's generation and **four of its anchors no longer
  match** (the three re-indented plus the re-anchored aggregate), so re-running it will abort those
  entries - cite `proofs-pass2.json`. The emitted record is `proofs-pass2.md` and the run log is
  `run-pass2.log`.
- **Temp tests written this pass**: `test_w2p2_hook_outcome_after_the_guard.py` (the enactment,
  against the real hook, plus the package-class loudness reading and the genuine-mount check) and
  `test_w2p2_fallback_equivalence_for_a_raising_read.py` (both chains, CSRF-enforcing client).
  `test_r1b_p2_hotpath_recognizer.py` is the hot-path snippet. Pass 1's `test_w1_probe_answers.py`,
  `test_w2_hasattr_vs_callable.py` and `test_w2_fallback_equivalence.py` were re-run unmodified and
  reproduce. Your own `test_w3_hook_outcome.py` will now **fail** on its final assertion - it asserts
  every outcome is `UNCONTROLLED`, which was true of pass 1's bytes and is the finding; its failure is
  the enactment, not a regression, and I left the file untouched.
- **Scratch root used, outside the repository:** `.../scratchpad/fail-p2`, holding only `pristine/`
  and no `ACTIVE-MUTATION.json`. Pass 1's roots are still beside it.
- **No file outside this round's write set was mutated at all this pass**, transiently or otherwise:
  the four R1-dirty paths and `consumers.py` carry the SHAs listed at the head of this report, and
  `consumers.py` is still byte-identical to `HEAD`.
- **Where I would look hardest.** (a) Entry 6's second re-anchor: I chose to include the guard in the
  aggregate mutation, having predicted and then avoided the shape where the guard absorbs the failures
  the entry exists to produce - the alternative anchoring would have read as a 0-row aggregate, so
  check that you agree the anchor I used is the faithful one. (b) Entry 8's growth from 2 to 6 rows is a
  side effect of the new fixtures raising in `__init__`, not a designed strengthening; it is stated that
  way and worth confirming. (c) The `except Exception` is the widest thing in this diff - its direction
  is decline, and the argument that a package mount's own broken boundary stays loud rests on the
  `_enforce_request_boundary_once` reading, which is cheap to re-drive. (d) The hot-path outlier: run 1
  is the only reading with a visible cost, and I kept it in the table rather than re-running until it
  disappeared.

### Notes for Worker 1 (spec reconciliation)

R1b still writes no spec or rationale text. The plan's items 1-8, pass 1's items 1-6 and the review's
items 1-5 stand except where a measurement here supersedes them. New:

1. **The review's escalated contract question is closed by M-C, so its "do not assert the unqualified
   absolute" caveat is discharged - but the sentence Decision 18 may now carry needs stating
   precisely.** The review's item 1 offered two paths; the maintainer took the code path (its **(ii)**,
   narrowed to the reads). Recommended wording, replacing the wording pass 1's item 4 proposed:
   - *Where it lives:* the spec's `## Decision 18` (the heading that still reads "via view-local CSRF
     re-entry"), and the same sentence the plan's item 4 targets.
   - *Current wording (pass 1's proposal, now superseded):* "Decision 18 can assert that **every**
     outcome of the boundary middleware's `process_view` is a controlled response - a refusal, a stamp,
     or a decline - rather than carving out a documented gap."
   - *Recommended replacement:* "Every outcome of the boundary middleware's `process_view` is a
     controlled response - a refusal, a stamp, or a decline. That holds for **any** callback, including
     one forging the private marker over a class whose attribute machinery raises: the recognition's
     reads are guarded and an answer that cannot be determined is a decline. What the middleware does
     not do is convert a *package* mount's own failure into a decline - a package class that cannot be
     built from its `view_initkwargs`, or whose boundary raises, fails exactly as it would with this
     middleware uninstalled." The last clause is load-bearing: it is what keeps the absolute honest
     without weakening it, and it is measured (the construction arm's narrow `TypeError`, and the
     view-local path's raise on a package class whose boundary read raises).
2. **Decision 18's recognition sentence gains a fourth clause.** Proposed contract wording, for R2 to
   shape: *the boundary middleware runs a package view's boundary only for a callback whose
   `view_class` carries that boundary as something callable, tested by attribute on the class before
   anything is constructed; it never calls anything that is not a class to try, it builds nothing it
   has not established a boundary on, and a read it cannot complete is a decline rather than an
   exception out of the hook. Every other callback is declined and keeps the view-local arrangement.*
   All four clauses are now measured: entry 6 at 12 rows, entry 7 at 2, entry 8 at 6, entry 9 at 5.
   R1's standing instruction still holds unchanged: **do not** write the `view_initkwargs` `dict` test
   as a symmetric guard.
3. **The probe's limit belongs in the rationale, restated for both shapes and for what the guard
   changed.** Pass 1's item 5 said the limit is that a class attribute probe consults the metaclass.
   Two corrections from measurement: the limit has **two** shapes (a metaclass `__getattr__` and a
   class-level descriptor under the probed name), and after M-C the limit is only that such code
   *runs* - not that its outcome escapes. Keep the two sentences distinct, as pass 1 asked: forging the
   private marker stays outside the threat model, and the guard exists so the hook's outcomes are
   controlled, not to defend against a forger.
4. **The rejected alternatives that should be recorded beside the decision** now include M-C's two, as
   `worker-1.md` `## Review-round custody` requires for a settled contract choice: narrowing the three
   absolute sentences instead of guarding (rejected - it is the documentary narrowing M-B already
   rejected one shape over, for a fix of comparable size), and one broad `except Exception` around the
   recognition **and** the construction (rejected - it would replace the narrow `except TypeError`
   whose narrowness R1's review examined and accepted, and it would convert a package mount's own
   non-`TypeError` construction failure into a silent decline).
5. **Nothing else moves.** No glossary term, terms-CSV row, `docs/TREE.md` entry, `docs/README.md`
   paragraph or `examples/**` path is created by this pass: the guard is inside a private function in a
   module already documented as R3's V1 obligation, and the live tier needed no re-pin (69 passed,
   unchanged). M-A, R3's re-pin estimate and the rationale's Decision 18 bullet are exactly where R1
   left them. The spec's `Status:` block and opener were re-read and remain accurate - both
   `pyproject.toml` and `__init__.py` read `0.0.14`, and this pass falsifies nothing in them.
6. **For the final gate:** this pass's floor run and hot-path numbers are above; the operative
   failability manifest is `docs/builder/temp-tests/r1b/proofs-pass2.json`, with this round's
   `proofs.json` (pass 1) and `docs/builder/temp-tests/r1/proofs-pass4.json` as the earlier comparison
   generations.

---

## Review (Worker 3, pass 2)

Required reading walked before judging anything, and the **W3** column of `BUILD.md`
`## Required reading per worker` walked myself rather than taken from the dispatch: `AGENTS.md`,
`START.md`, `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, `docs/builder/worker-3.md`,
`docs/README.md`, `examples/fakeshop/test_query/README.md`, the active spec (Decisions 7, 18 read at
source), the active spec **rationale** (W3 reads it - its `### Decision 18` entry read in full), the
active build plan's whole `# Closeout cycle (card 046)` including `## Maintainer decision M-C`,
`## Maintainer decision M-B` and `## Round R1b`, this artifact, the closed
`bld-046-r1-remediation_review.md`, and my own memory file. Nothing else is marked `yes` for W3, so
nothing was omitted from the dispatch; the other workers' memory files were not read.

**This pass judges the enactment against M-C, not against my own pass-1 recommendation.** M-C chose
neither path my finding offered verbatim - it guards the recognition **reads** and keeps the
construction guard's narrow `except TypeError` - and named my recommended documentary narrowing as
one of the two alternatives it rejected. Nothing below re-argues that choice.

### Independent re-run: the mutations, declared BEFORE any of them was made

`worker-3.md` requires the mutation to be recorded in this artifact before it is applied, so this
subsection was written and saved to disk first and every run came after it.

**Re-run set: all nine entries of `docs/builder/temp-tests/r1b/proofs-pass2.json`**, at the scope
Worker 2 recorded (`tests/test_views.py`). The mandatory floor requires every boundary at **3 rows or
fewer** - entries 2, 4 and 7 - **and every boundary on a security or data-isolation decision**, which
here is all nine: each is a clause of the CSRF-ordering or body-cap contract. So the floor is the
whole manifest and there was nothing to select. Mutations, quoted from the manifest I parsed rather
than from the build report's prose (in manifest order):

1. `::_package_view_instance #"if not getattr(view_func, _BOUNDARY_MARKER, False)"` -> `if True:`
2. `_CsrfOrderingExemption.__bool__` -> `return True`
3. `_CsrfOrderingExemption.__bool__` -> `return False`
4. `::_require_boundary_before_csrf` -> `return boundary_index = csrf_index = None`
5. `_CsrfOrderingExemption.__bool__` -> `return _boundary_middleware_request.get() is None`
6. `::_package_view_instance`, the whole 15-line body -> the marker clause and the two `getattr`s
   restated verbatim plus an unguarded `    return view_class(**initkwargs)`
7. `::_package_view_instance`, the two `isinstance` clauses **deleted**
8. `::_package_view_instance`, the boundary probe **deleted**
9. `::_package_view_instance`, the guarded block -> the same four reads and three clauses
   **dedented with the `try` / `except Exception` removed**

**Plus one mutation of my own, which Worker 2 did not run and which its `### Notes for Worker 3` item
(a) invites**: the *alternative* anchoring of entry 6 that Worker 2 says it predicted and avoided -
anchor the four reads and three clauses **inside** the guard, replacement
`        return view_class(**initkwargs)` **inside the `try`**, so the `except Exception` stays live
around the mutant. One-entry manifest `docs/builder/temp-tests/r1b/w3p2-entry6-absorbing.json`,
separate scratch root, separate `--output`. It is run to measure whether the shape Worker 2 rejected
really would have hidden rows, rather than to accept that it would.

**Not re-run, deliberately:** the seven R1 entries targeting `views.py`, `_request_body.py` and
`consumers.py`, for the reason Worker 2 states per entry and I re-checked below; and the drift
auxiliary, which this pass does not bear on (`_BOUNDARY_METHOD` and
`views.py::_RequestBodyBoundaryMixin._enforce_request_boundary` are byte-unmoved: SHA-256
`7b3d9e51b7fb7ecc...` and `e8aeb156550fc45a...`, read at the start of this pass).

Discipline: `--check-anchors-only` first and separately, then the set through
`scripts/prove_failability.py` so the order is enforced, scratch roots outside the repository, every
restore byte-proved by the runner, node-id **sets** compared rather than counts. No `git checkout`,
`git restore`, `git stash` or `git worktree` at any point in this pass.

**Declared after the first absorbing run and before the second** (the first measured something worth
splitting in two): a **second** variant of the same probe, anchored from the first `isinstance` clause
through the probe's `return None` so the marker clause and the two assignments **survive** -
replacement `        return view_class(**initkwargs)`, still inside the guard. It is the more
charitable reading of "anchored to the guarded block", and it is what separates "the guard absorbs the
aggregate's failures" from "the mutant is unbound and declines everything". Manifest
`docs/builder/temp-tests/r1b/w3p2-entry6-absorbing-narrow.json`, separate `--output`.

### Re-run result: nine of nine set-equal, nothing weakly pinned

`--check-anchors-only` **exit 0** (all nine anchors matched exactly once *before any copy was taken*,
so no prior pass left a live mutation); the full set in one invocation, **exit 0**; scratch root
`.../scratchpad/w3p2-fail`, holding only `pristine/` and no `ACTIVE-MUTATION.json`. Record emitted to
`docs/builder/temp-tests/r1b/w3p2-rerun.md`, log beside it. Node-id **sets** compared by symmetric
difference over the parsed lists - mine against Worker 2's emitted block (`proofs-pass2.md`), not
against its prose table:

| # | boundary | W2 rows | W3 rows | sets |
| --- | --- | --- | --- | --- |
| 1 | marker clause -> `if True:` | 4 | **4** | set-equal |
| 2 | `_CsrfOrderingExemption.__bool__` -> `True` | 3 | **3** | set-equal |
| 3 | `__bool__` -> `False` | 13 | **13** | set-equal |
| 4 | `::_require_boundary_before_csrf` | 3 | **3** | set-equal |
| 5 | `__bool__` (per-request key) | 7 | **7** | set-equal |
| 6 | the aggregate recognition, guard included | 12 | **12** | set-equal |
| 7 | the two shape clauses | 2 | **2** | set-equal |
| 8 | the boundary probe | 6 | **6** | set-equal |
| 9 | the guard around the reads | 5 | **5** | set-equal |

**0 collection/setup errors on all nine**, every pre-mutation baseline `205 passed` at pytest exit 0,
`pre-existing failing rows excluded from the count: 0` on all nine, and every restore proved by
`filecmp.cmp(shallow=False)` plus SHA-256 against the runner's own pre-mutation copy (six against
`5900fb367db8a944...`, three against `7b3d9e51b7fb7ecc...`). **No entry lands in the 0-or-1-row
band.** After every run I re-read the tree: `middleware/request_body.py 5900fb367db8a944...`,
`_boundary_ordering.py 7b3d9e51b7fb7ecc...`, `tests/test_views.py abe0406a26fc9c15...`,
`views.py e8aeb156550fc45a...`, `_request_body.py 2c1fd48618d4b01c...`,
`tests/test_routers.py 5bf697bbe27b5d66...`, `constants.py 6761fadb49c4f285...` - every one identical
to the head of the pass-2 report, and `git status --short` plus `git diff --cached --name-status`
byte-for-byte what they were at task start.

Nesting, computed by set containment rather than read off the prose: **entry 9 is a strict subset of
entry 6** (5 of its 12), **entry 7 is a subset of 6 and disjoint from 9**, **entry 8 is a subset of 6
and overlaps 9 in exactly the four raising rows**, and **route 3
(`[/marked-rejected-initkwargs/]`) is in entry 6 and in neither 8 nor 9** - so B-4 is still measured
rather than argued: that route still reaches the construction arm, and removing the arm would restore
an unhandled `500` for a row the suite already pins.

### Entry 6's second re-anchor: I ran the shape Worker 2 rejected rather than accepting the prediction

This is the report's sharpest claim and the one thing in the pass that a reader cannot check by
reading. Worker 2 says anchoring the aggregate *inside* the guard would have let the guard absorb the
failures the entry exists to produce, that it predicted this, and that the alternative "would have read
as a 0-row aggregate". **The absorption is real and larger than the report's own summary; the "0-row"
characterisation is wrong, in the direction that matters.** Both variants measured, byte-proved, tree
restored:

- **Anchored to the whole guarded block** (`w3p2-entry6-absorbing.json`): **4 rows**, and the set is
  **exactly entry 1's** - `::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the
  _ordering[sync|async]` and `::test_the_view_does_not_measure_a_body_the_chain_already_measured
  [sync|async]`. The replacement leaves `view_class` / `initkwargs` unbound, the `NameError` is
  absorbed by the live `except Exception`, so the recognition declines *everything* and what the entry
  measures is "recognition happens at all", not the aggregate.
- **Anchored so the marker clause and the two assignments survive** (`w3p2-entry6-absorbing-narrow
  .json`), the more charitable reading: **4 rows** -
  `[/marked-callable-view-class/]`, `[/marked-foreign-view-class/]`,
  `::test_a_callable_view_class_that_is_not_a_class_is_never_called`,
  `::test_a_view_class_without_the_boundary_is_never_constructed`. The **eight** rows it absorbs are
  precisely the ones the aggregate exists to produce: `[/marked-no-view-class/]`,
  `[/marked-bad-initkwargs/]`, `[/marked-rejected-initkwargs/]` (the splat's and the class's
  `TypeError`, swallowed), `[/marked-raising-metaclass/]`, `[/marked-raising-descriptor/]` and all
  three `::test_a_read_that_raises_is_declined_rather_than_raised_out_of_the_hook` rows (the forged
  `__init__`'s `AssertionError`, swallowed).

So the decision to anchor the whole body is the faithful one and Worker 2's reasoning is right. The
correction is that the rejected shape would **not** have announced itself as a zero: it measures 4
rows, passes `BUILD.md`'s acceptance rule, and would have read as a pinned aggregate while measuring a
third of the boundary - which is strictly harder to catch than a zero the runner flags. Worth stating
because this cycle has twice been saved by a zero being visible.

### Entry 8 grew 2 -> 6 as an unpredicted side effect, and its meaning did not drift

Checked as a set relation, not as a count: **entry 8's pass-1 set is a subset of its pass-2 set**
(`[/marked-foreign-view-class/]` and `::test_a_view_class_without_the_boundary_is_never_constructed`
both still fail), nothing was lost, and the four new rows are the two raising wire routes plus the two
matching unit rows. The mechanism is the one the report states and I confirmed by reading the
fixtures: with the probe deleted, `_ViewClassWhoseMetaclassRaises` and
`_ViewClassWhoseBoundaryDescriptorRaises` are **constructed**, and their `__init__` raises
`AssertionError`, which the narrow `except TypeError` does not absorb.

Two things follow, and they are why the growth is benign rather than a drift. First, the entry still
pins **the probe** and not the new fixtures: its original two rows are still there, so deleting or
weakening the raising fixtures would return it to 2 - above the band either way. Second, the growth
does not let entry 9 coast: route 3 is absent from both, entry 9's five rows are disjoint from entry
7's, and the two entries answer different questions (probe deleted -> a foreign class is *built*;
guard deleted -> a read *escapes*). Recording the growth as measured-not-designed is the right
disposition; presenting it as a strengthening would have been the wrong one.

### The manifest, audited entry by entry rather than accepted

- **"Derived programmatically, character-identical" is true and I re-derived it.** Parsing both
  manifests and comparing sorted-key JSON per entry: **four** objects are byte-identical to this
  round's `proofs.json` (entries 2, 3, 4, 5). Entries **1, 7 and 8** differ *only* by a four-space
  re-indentation of every anchor and replacement line - `label`, `target`, `mutation`, `scope` and
  `delete` all identical, verified key by key - so the re-indent claim is a measurement rather than a
  description. Entry **1**'s anchor also changed from a bare string to a one-element list, which is
  the same content in the schema's other spelling.
- **Entry 6's re-anchor is faithful.** Anchor = the whole 15-line body; replacement = the marker
  clause and the two `getattr` assignments **restated verbatim** plus an unguarded
  `    return view_class(**initkwargs)`. So what stays live after the mutation is exactly what stayed
  live under pass 1's entry 12/6, and the label and mutation prose name the guard - not the false
  reading a prior round filed a finding about.
- **Entry 9 removes the boundary and nothing else.** Anchor = the guarded block; replacement = the
  same four reads and three clauses dedented with the `try` / `except Exception` gone, i.e. pass 1's
  shipped shape exactly. The construction arm is outside the anchor and is untouched, which is what
  makes 9 a measurement of the guard rather than of the recognition.
- **Seven R1 entries again not re-run: the argument's premise re-checked, not its conclusion.** What
  could move those sets is a new row exercising their boundary. Independently confirmed: the two new
  wire rows drive a bare `GET` with no body, no `Content-Type` and no socket to a declined callback
  whose view is a plain function; the three unit rows call `_package_view_instance` directly with no
  request; and `grep -rln '_BOUNDARY_MARKER\|graphql_request_body_boundary' tests examples
  --include='*.py'` returns **`tests/test_views.py` and nothing else**, so no other tree gained an
  input to those boundaries. Their unmutated green state is in the record nine times over as the
  pre-mutation baseline. Mutating three files dirty with a closed round's uncommitted work for a
  stability check obtainable this way remains the worse trade.
- **No `views.py` mutation this pass, as claimed**: its SHA is `e8aeb156550fc45a...` at both ends of my
  pass too, which is the value R1's pass-4 table records.

### The guard: its shape, its scope, and whether the direction argument actually saves it

```django_strawberry_framework/middleware/request_body.py:285:299
    try:
        if not getattr(view_func, _BOUNDARY_MARKER, False):
            return None
        view_class = getattr(view_func, "view_class", None)
        initkwargs = getattr(view_func, "view_initkwargs", None)
        if not isinstance(view_class, type) or not isinstance(initkwargs, dict):
            return None
        if not callable(getattr(view_class, _BOUNDARY_METHOD, None)):
            return None
    except Exception:  # a read that cannot answer has recognized nothing
        return None
    try:
        return view_class(**initkwargs)
    except TypeError:
        return None
```

M-C's scope is honoured exactly: all four recognition reads inside the guard, the two `isinstance`
tests still ahead of the probe, the construction still on its own narrow `except TypeError`
**outside** it.

**The catalogued shape is "an over-broad `except Exception` wrapped around a check, which converts
'the check blew up' into 'the check passed'", and the operative clause is the conversion, not the
keyword.** I did not take the direction argument on trust, because a direction argument is only as
good as what the safe-looking arm actually does. Three things had to hold, and each is measured:

1. **Nothing legitimate reaches the arm.** Only a callback carrying the package-private marker gets
   past the first clause, so a third-party wrapper with a lazily-raising `view_class` never arrives.
2. **The arm preserves the cap.** A declined callback leaves the request unstamped, so
   `views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once` runs the boundary in the view
   - read at source (`#"if getattr(request, _BOUNDARY_ENFORCED, False): return"` then
   `self._enforce_request_boundary(request)`), and measured: after the hook declines, the stamp is
   absent (`stamped=False`) on every one of the guarded inputs.
3. **The arm preserves the CSRF check.** Worker 2's equivalence probe re-run unmodified: both new
   shapes answer `(403, stamp=False, callback_exempt=False)` **identically installed and
   uninstalled**, on a CSRF-*enforcing* client. The equivalence is the property; declining exempts
   nothing.

**The claim I was told to verify rather than accept - that a package class whose boundary read raises
is still loud downstream - holds, and I drove it in the sequence Django uses** rather than reading the
report's account of it (`docs/builder/temp-tests/r1b/test_w3p2_outcomes_after_the_guard.py`, mine,
identical in `.venv` 3.14.2 and at the floor 3.10.19):

```
  M-C 1  metaclass read raises: controlled: None | stamped=False
  M-C 2  class descriptor read raises: controlled: None | stamped=False
  M-C 3  callback bookkeeping read raises: controlled: None | stamped=False
  package subclass, boundary read raises - hook: controlled: None
  package subclass, boundary read raises - view-local: still loud: ValueError: descriptor read raised
  a genuine mount recognizes as: DjangoGraphQLView
```

So the guard masks no misconfiguration of a package mount: the hook declines it and the view-local
path - which is exactly what a declined request goes on to run - raises on the same read. That is the
crux of M-C's fail-closed argument and it is now measured from both ends. The genuine-mount line is
the check a suite full of decline rows would not make for itself: the guard did not turn recognition
into a blanket decline.

`except Exception` rather than an enumerated tuple is right for the reason the implementation note
gives (an enumeration is a guard against input spellings), and `except BaseException` was correctly
rejected. `BLE001` is genuinely not in this repo's `select` list - read at
`pyproject.toml [tool.ruff.lint]` - so no `noqa` is owed, and the inline-comment idiom is the
package's own.

### The shape choice Worker 2 made on its own: one `try`, not an extracted helper

Judged on merits, and the anchor consideration judged separately.

**The inline form is right.** The alternative - `_recognized_boundary_view_class(view_func)` with the
guard around the call - would create a private symbol whose body is the whole recognition and whose
only caller is the three lines below it, which is the split the plan's `### Boundary count and the
split question` already refused ("two halves neither of which is 'the answer the hook branches on'")
and which my pass-1 section agreed with. It would also move the recognition's answer from *an
instance* to *a class*, quietly re-opening B-2's rejected "rename the recognizer's answer" ground. The
cost of the shipped form is a four-space re-indent and two branch nodes; the cost of the helper is a
permanent second name in production. Nothing here duplicates: one `try`, one call site.

**The anchor consideration was a legitimate input and did not decide it.** That the helper would have
left entries 7 and 8 byte-identical is the *cost side* of the trade, and Worker 2 names it as the
alternative's "one real attraction" and then decides on the plan's recorded ground. That is the right
ordering: `docs/builder/temp-tests/` is per-cycle scratch that `scripts/clean_up.py` clears, while
production shape is permanent, so paying churn there to keep the function whole is the cheap side. And
the churn cost nothing in fidelity - I verified the three re-indented anchors are pure whitespace
shifts with every other field identical, and all three re-ran set-equal. Had the anchor argument
*won*, that would have been a tail wagging a dog; it lost, and was recorded, which is better than not
having been weighed.

### High:

None.

### Medium:

#### The absolute the round keeps verbatim is true of the recognition, not of the hook

M-C's premise was that guarding the reads "leaves the three absolute sentences true as written", and
the pass keeps `#"the probe is here so that every outcome of the hook is a controlled response"`
verbatim on exactly that ground. Measured against the **real** `process_view`, not a copy, identically
in `.venv` (3.14.2) and at the floor (3.10.19)
(`docs/builder/temp-tests/r1b/test_w3p2_outcomes_after_the_guard.py`):

```
  beyond M-C  probe-passing callable boundary that RAISES:
      UNCONTROLLED: ValueError: a forged boundary that raises when it is run | stamped=False
  beyond M-C  probe-passing callable boundary that returns: controlled: None | stamped=True
```

A forged `view_class` that carries a **callable** under the probed name passes the probe by design,
is constructed, and `process_view` then calls it inside `except HTTPException` only - so an exception
of the forged object's choosing leaves the hook uncaught. The guard M-C ordered covers the *reads*;
this is the *call*, one statement later.

**Why it is nonetheless not a code defect, and why I am not asking for another builder pass.** The
failure is indistinguishable in kind from a genuine package mount whose boundary raises something that
is not an `HTTPException` - and the same docstring paragraph, correctly, makes that loudness a stated
invariant. Containing it would mean an `except Exception` around
`view._enforce_request_boundary(request)`, which would swallow the body cap's own errors: strictly
worse than the sentence being imprecise. Two other sites read as exhaustive over inputs they do not
cover, from the same cause: the `TypeError` paragraph's `#"With the probe ahead of it what still
reaches it is"` enumerates package inputs only (a forged class whose accepted `__init__` raises
`TypeError` reaches it too), and `### Notes for Worker 1` item 1's proposed Decision 18 wording asserts
"That holds for **any** callback" while its honesty clause is scoped to "a *package* mount's own
failure".

**Recommended change, one clause per site, and no test is owed** (no boundary moves): scope the
absolute to the outcomes *the recognition* produces - a refusal, a stamp, or a decline - and state
once that running a boundary the recognition accepted is the mount's failure surfacing, not the
recognition's. `#"a hook whose every other outcome is a controlled response"` needs nothing: "every
other" is already scoped.

**Escalated rather than requested**, because the prior question - whether the package owes a
controlled response to a forged class whose *accepted* boundary raises - is the same contract call
M-C answered one layer in, and is not a worker's: see `### Notes for Worker 1 (spec reconciliation)`
item 1, with both resolution paths. The Medium is recorded at the severity my pass-1 section gave the
identical claim shape, and it does not hold the round: the code M-C ordered landed, is correct, and is
independently verified above.

### Low:

#### Three statements in the pass-2 report do not reproduce as written

Corrected here as prose per `ARTIFACT.md`; none changes a reading and **no change is requested**.

- `### Notes for Worker 3` item (a) says the rejected anchoring for entry 6 "would have read as a
  0-row aggregate". Measured, both variants read as **4 rows** (sets above). The substance - the guard
  absorbs the failures the entry exists to produce - is confirmed and is *stronger* than stated,
  because a 4-row entry satisfies `BUILD.md`'s acceptance rule and would have looked pinned, where a
  zero is exactly what the runner grades and a reviewer re-runs.
- `### Validation run` says the inline-comment-on-`except` idiom is one "`_request_body.py` uses five
  times". Measured, that file has **five `except Exception:` clauses of which four carry the inline
  comment** (`grep -cE 'except .*:  #'` -> 4; the fifth, `#"return _measured_by_bounded_read"`'s
  wrapper, logs instead). The claim that the idiom is the package's holds - seven such comments
  package-wide.
- `### Implementation notes`' complexity reading is the one number I could not re-derive by the
  builder's own route, so I re-derived it by mine: `review_inspect.py` against the shipped bytes
  reports `_package_view_instance` at **89 lines and 8 branch nodes, span 211-299, docstring
  212-284** - so 73 docstring lines and a 16-line executable body, exactly as recorded, and
  `repeated string literals: 0`, `Django / ORM markers: None`, `getattr()` **4x** unchanged. This
  bullet records the agreement rather than a discrepancy.

#### The reconstruction method behind the two pass-1 corrections is sound

Recorded here because the prompt for this pass asked it to be judged rather than assumed, and because
the answer is "yes" rather than a finding. Worker 2 reversed its three edits on an outside-the-repo
copy and hashed the result to `7154891a17fcc10b...`. That is a sound proof of two things at once: a
wrong reconstruction cannot collide with a SHA-256, so the reconstructed bytes **are** pass 1's, and
therefore the shipped file differs from pass 1's by exactly the three reversed hunks. The anchor value
is independently attested - `7154891a17fcc10b...` is what **I** read off the tree during pass 1 and
recorded in that section, not a number this pass supplied - and the derived pass-1 figures (span
211-279, docstring 212-267, 6 branch nodes) are the ones I measured then. `git stash` / `checkout` /
`restore` / `worktree` appear nowhere in it.

### The two pass-1 Lows, audited as closed by re-measurement

- **The falsified docstring citation.** Re-measured independently rather than accepted:
  `examples/fakeshop/test_query/test_transport_api.py::_carrying_the_packages_csrf_mark` executes
  `view.csrf_exempt = mark` and nothing else, and `grep -nE '\.view_class|\.view_initkwargs'` over
  that whole file returns **no lines** (exit 1). The new wording - "the repository itself contains a
  leaner member of the same class - ... copies `csrf_exempt` and nothing else" - is true, keeps the
  load-bearing half (marker-dropping wrappers are reachable and the repo contains one), and the
  fixture's behaviour is unchanged. Closed.
- **The two numbers.** Both corrected under `#### Corrections to earlier sections of this artifact`
  by the builder's own re-measurement, with the falsity of the band sentence reproduced rather than
  conceded. Closed; see the Low above for the third statement this pass added.

### Is the hot path a budget finding? No - and that is a measurement, not a concession

The absolutes now sit **above** R1 pass 3's 0.50-0.53 us band, and the report says so instead of
placing them inside it. That is the honest restatement the pass-1 Low asked for, and it is not itself
a budget finding, for a reason that can be measured rather than asserted: **the "before" arm - which
is pass 1's body, code this pass did not write - reads 0.5234-0.5367 us in `.venv` and 0.5772-0.6088
us at the floor in my own runs.** An arm that predates the change under measurement cannot have been
elevated by it, so the elevation is the machine, exactly as both passes say. The number that belongs
to this pass is the delta between two arms in one process, and it is below the metric's resolution.

### DRY findings

None to fix. What I checked, and what I decided:

- **No helper is justified and none was added** - see `### The shape choice Worker 2 made on its
  own`. The existence challenge does not arise: the diff adds no registry, token or indirection layer,
  and `_BOUNDARY_METHOD` (whose existence I challenged and cleared in pass 1) is unchanged.
- **A repeated fixture message, weighed and not flagged.** `#"a class whose boundary cannot be read
  must never be built"` is spelled twice, once in each of the two forged view classes'
  `__init__`. A shared base class would remove one line and add an inheritance edge to two classes
  whose whole point is being foreign to the package, and a shared constant would name a string that
  must never be emitted. The two spellings sit six lines apart and each names its own class's
  contract; consolidating is not the more readable shape. Recorded as decided rather than missed.
- **The two new wire routes joined the existing parametrization** instead of earning a sixth and
  seventh decline test, and the three unit rows are one parametrized row rather than three functions -
  both the file's own idiom.
- **The fixture pair is two mechanisms, not a near-copy**: a metaclass `__getattr__` runs for a name
  the class does *not* have and a descriptor for one it does, which is why one guard on one of them
  would not have been evidence about the other. The docstrings say exactly that.
- **Cross-cohort duplication review: not applicable.** One cohort, one pass, `ownership partition:
  none; sequential rounds`. `repeated string literals: 0` / `None` in both refreshed shadow overviews,
  so the mechanical half returns nothing either.

### Dispatched findings checklist: the decision to tick nothing, audited

I neither tick nor un-tick. **Worker 2's judgement is correct and rests on the right rule.** The
checklist was written at plan time, before M-C existed, so it carries no box for the read guard - and
`BUILD.md` `### Dispatched findings checklist` is explicit that "a maintainer decision the round
escalated is not a checklist box", so no box was owed and inventing one would have been the error.
All seven boxes were earned in pass 1 and I audited every tick then; this pass un-earns none of them,
and it strengthens box 1 rather than weakening it: the claim that box records as "closed by making it
true" is now true for the two read-raising input classes as well, which is what my pass-1 audit said
was missing. Re-walked against the landed code this pass: boxes 2-7 are all still matched by shipped
code (seven routes and a seven-route docstring; the probe ahead of construction with entries 7/8/9
measuring three different answers; `_BOUNDARY_METHOD` still the third fact with no import added -
`grep -n 'import'` on `_boundary_ordering.py` shows only `__future__`, `contextvars`, `typing` and the
`TYPE_CHECKING`-guarded `django.http`; the five over-claiming sites; T2's recording assertion; and a
manifest with no entry in the 0-or-1 band). Box 1 is the one the Medium above qualifies, and it
qualifies the *sentence*, not the fix.

### Non-weakening checks, audited

1. **The five previously tested decline routes answer exactly as they did**, and route 3 still reaches
   the construction arm - by set membership (in entry 6, absent from 8 and 9), not by prose. All seven
   parametrizations pass in `.venv` and at the floor.
2. **The `_CsrfOrderingExemption` contract is untouched.** Entries 2, 3 and 5 set-equal; all four of
   `::test_a_declined_callback_still_gets_a_complete_csrf_check[sync|async]` and
   `::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[sync|async]` still inside
   *both* entry 3's and entry 5's sets (checked by parsing the sets); and `_boundary_ordering.py` is
   byte-unmoved by this pass (`7b3d9e51b7fb7ecc...`) with its diff against the **index** copy still
   exactly three hunks and **no line of `__bool__`, the `ContextVar` or `_CSRF_ORDERING_EXEMPTION`
   changed**. A declined callback still degrades the CSRF *class*, never the *ordering* - and for the
   two newly declined shapes that is measured at `403` on both chains.
3. **The newly declined shapes inherit the same fallback** - the installed and uninstalled chains
   answer identically, which is the property rather than any single value, and the CSRF-enforcing
   client is what makes the reading about the code instead of the fixture. I accept the decision not
   to promote that probe: the property belongs to *declining*, and
   `::test_a_declined_callback_still_gets_a_complete_csrf_check[sync|async]` pins it permanently.
4. **Exactly one complete CSRF check in both arrangements** - unchanged row sets of entries 3 and 5;
   R1's entry 14 correctly not re-run.
5. **A genuine mount is recognized at both transports** - T3, plus my own reading that the shipped
   recognizer answers a `DjangoGraphQLView` for a real mount on both interpreters.
6. **The public surface does not move** - below.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` and
`git diff --cached -- django_strawberry_framework/__init__.py` are both **empty** (0 lines): `__all__`
and the re-export list are unchanged. `middleware/request_body.py`'s `__all__` is still the
single-name tuple `("GraphQLRequestBodyBoundaryMiddleware",)`, so the documented `MIDDLEWARE` string
is untouched. `_BOUNDARY_METHOD` still appears only in `_boundary_ordering.py`,
`middleware/request_body.py` and `tests/test_views.py` (measured tree-wide, excluding scratch), and is
re-exported nowhere. No new public export, as the round's Definition of Done requires.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. Verified rather than assumed:
`git status --short CHANGELOG.md` is clean, and the version quintet is where the cycle-wide
declaration says it is - `pyproject.toml` `version = "0.0.14"` and
`django_strawberry_framework/__init__.py` `__version__ = "0.0.14"`, neither dirty.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. Verified:
`git status --short` is clean for `docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`, `KANBAN.md`,
the spec, its rationale, the terms CSV and `tests/base/test_init.py`. The only dirty `.md` files in
the tree are Worker 0's build plan and the two artifacts.

### Static helper use

`scripts/review_inspect.py … --output-dir docs/shadow` run by me against **both** production files
this round writes (`middleware/request_body.py` - the changed logic plus the complexity claim the
second Low turns on; and `_boundary_ordering.py`, byte-unmoved this pass but re-run so the pair is
current). No skips. Readings are quoted in the Low above; every reference in this section cites
original source symbols, never shadow line numbers.

### Hot-path budget verification

The number **exists**, is stated with metric, exact command, iteration count and statistic, and
**reproduces as recorded** - which is the whole of my obligation. Reproduced with the recorded
command, three runs in `.venv` and two at the floor:

| Environment | before | after | delta per call |
| --- | --- | --- | --- |
| `.venv` (3.14.2), run 1 | 0.5367 us | 0.5391 us | **+0.0024 us** |
| `.venv` (3.14.2), run 2 | 0.5345 us | 0.5341 us | **-0.0005 us** |
| `.venv` (3.14.2), run 3 | 0.5234 us | 0.5390 us | **+0.0156 us** |
| floor (3.10.19), run 1 | 0.6088 us | 0.6088 us | **-0.0000 us** |
| floor (3.10.19), run 2 | 0.5772 us | 0.5768 us | **-0.0004 us** |

Same shape as the ten readings recorded: straddling zero, below the metric's resolution, and **none of
my five reproduced run 1's +0.0825 us** - which is the evidence that keeping it in the table rather
than re-running until it vanished was right, and that taking five readings per environment instead of
the plan's two is what stopped a single pair from making it look like the number. I read the benchmark
rather than only running it: both arms are in one process over the identical callback, the "before" arm
is a local copy of the pass-1 body (probe present, guard absent), so the delta is the guard and
nothing else. Declining to re-capture R1's 400-iteration request median is correct and correctly
*stated* rather than answered "not applicable". Whether the cost is acceptable is the maintainer's
call, and there is no cost visible above noise to weigh.

### Floor verification audit

The plan assigns the run to Worker 2's build pass; it happened, and I re-ran it rather than reading
it. Versions read, never recalled:

- `/tmp/dsf-floor/bin/python -V` -> **Python 3.10.19**.
- `uv pip list --python /tmp/dsf-floor/bin/python` -> **django 5.2**, **strawberry-graphql 0.316.0**,
  asgiref 3.12.1, channels 4.3.2, daphne 4.2.3, django-filter 26.1, pytest 9.1.1, pytest-django
  4.12.0, pytest-asyncio 1.4.0, and `django-strawberry-framework 0.0.14` editable at this checkout.
  That is the floor `BUILD.md` `## Floor verification` states - Django 5.2.0 on Python 3.10 with
  strawberry-graphql 0.316.0 - and being editable it carries this round's bytes.
- `/tmp/dsf-floor/bin/python -m pytest tests/test_views.py --no-cov` -> **205 passed**, the whole
  declared scope.
- The thirteen rows the round's subject rests on, each `PASSED` read individually in `-v` output at
  the floor: all **seven** parametrizations of
  `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed`, all three of
  `::test_a_read_that_raises_is_declined_rather_than_raised_out_of_the_hook`, plus
  `::test_a_callable_view_class_that_is_not_a_class_is_never_called`,
  `::test_a_view_class_without_the_boundary_is_never_constructed` and
  `::test_the_probed_boundary_method_is_the_one_the_package_views_define` - **13 passed**.
- The floor questions this pass creates, all re-answered by me: my own hook-outcome table is
  byte-identical between the two interpreters (the three controlled declines, the package-class
  loudness reading, and the beyond-M-C `UNCONTROLLED` line alike); pass 1's probe-answer and
  `hasattr`-versus-`callable` tables and both fallback-equivalence probes re-run unmodified and
  reproduce; and the floor hot-path deltas are above.
- **The shared `.venv` was not mutated**: read, it carries **Python 3.14.2**, django 6.0.5, asgiref
  3.11.1, strawberry-graphql 0.316.0, pytest 9.0.3 - far above the floor. Every floor command in this
  pass was `/tmp/dsf-floor/bin/python -m pytest` or carried `--python /tmp/dsf-floor/bin/python`, and
  I ran no `uv pip install` at all.

### Test staleness sweep, run independently of the round's file list

`BUILD.md` `### Test staleness a focused run cannot see` names two shapes and neither is present: no
example-model field changed and no wire shape converted. Run anyway, against the tree rather than
against `### Files touched`:

- `grep -rn '_enforce_request_boundary' tests examples --include='*.py'` -> **7 hits, all in
  `tests/test_views.py`**, none in `examples/**`.
- `grep -rln '_BOUNDARY_MARKER\|graphql_request_body_boundary' tests examples --include='*.py'` ->
  **`tests/test_views.py` only**. Nothing else forges the marker, so nothing else can have changed
  answer.
- `grep -rn 'view_class' tests examples --include='*.py'` and read: outside `tests/test_views.py` the
  only hits are `tests/middleware/test_debug_toolbar.py`'s rows for the *sibling* recognizer, and
  `test_transport_api.py`'s `view_class` **parameter** - no `.view_class` / `.view_initkwargs`
  assignment anywhere in that file, so the live tier's wrapper is still declined at the first clause.
- Full sweeps: `uv run pytest tests/ --no-cov` -> **4526 passed, 38 skipped**; `tests/test_views.py`
  -> **205 passed**; `tests/middleware/` -> **17 passed**;
  `examples/fakeshop/test_query/test_transport_api.py` -> **69 passed**. Every total the pass-2 report
  states reproduces.
- The `200 -> 205` collection change is arithmetic I can close rather than take on trust: five rows
  were added (two parametrizations of an existing test, three of one new test) and **no existing node
  id disappeared** - the strongest evidence being that all 45 node ids across the nine re-run entries,
  entry 3's thirteen included, still resolve.

### Lint / hook gate, re-run read-only

`pre-commit` is not installed here, so its four `language: system` local hooks were run individually:

- `uv run ruff format --check <the three files>` -> `3 files already formatted`;
  `uv run ruff check <the same three>` -> `All checks passed!`.
- `uv run python scripts/check_trailing_commas.py --check <the three files>` -> exit **0**.
- ASCII-only, verified independently of the hook by byte scan: **0** bytes above 127 in all three
  (highest 125, 125, 124).
- `git diff --check` -> exit **0**.
- `kanban-tracked-path-constants`, verified **without writing the baseline-dirty file**:
  `uv run python scripts/build_kanban_tracked_path_constants.py --output <outside-the-repo scratch>`,
  then `cmp` against the tracked copy -> **exit 0**, SHA-256 `6761fadb49c4f285…` on both sides. So the
  generated allowlist really is byte-unchanged and the maintainer's commit will not be rolled back.
  Worker 2 again obtained the same answer by running the generator against the tracked path, which
  writes a file this round declares out of its write set; the outcome was a genuine no-op both times,
  so nothing follows beyond preferring the `--output` form.
- **Nothing new is staged.** `git diff --cached --name-status` is still the single authorized path, and
  `git status --short` at the end of this pass is identical to its state at the start.

### Prose discipline in the diff

Checked mechanically over the added lines of all three files (853 added lines, which for the two
`HEAD`-based files covers R1's additions too, so the result is stronger than asked): **no** severity
label, no round / pass / slice index, no `bld-*.md` filename, no `docs/feedback*.md` mention, no
`M-B` / `M-C` reference, no `Test-N` index and no raw `path:NN` reference. Symbol references use
`path::QualifiedName` and `#"unique substring"`; the docstrings state invariants, never how the change
came to be.

### What looks solid

- **The enactment is exactly M-C and it works.** Three inputs that left the hook uncaught in pass 1
  answer a controlled `None` on both interpreters, and the fifth measurement - the genuine mount -
  proves the guard did not buy that by declining everything.
- **The masking question was answered by measurement in the direction that could have gone wrong.**
  "A package mount's own broken boundary stays loud" is the claim that makes a broad `except` defensible
  here, and it is driven at the call site the declined request actually reaches rather than argued.
- **Entry 6's second re-anchor was reasoned about *before* it was written, and the reasoning survives
  execution.** Two anchorings measured; the rejected one absorbs eight of the twelve rows. A builder
  predicting a measurement trap and avoiding it is the opposite of this cycle's two silent zeros.
- **Entry 8's growth is reported as unpredicted.** The cheap move was to present it as a designed
  strengthening; saying "I did not add them for that" is what let me check the meaning instead of the
  count.
- **Five hot-path readings per environment because two would have made an outlier look like the
  number** - and the outlier kept in the table rather than re-run away.
- **Both Lows closed by re-measurement rather than restatement**, including reproducing the falsity of
  a sentence this pass inherited rather than conceding it, and by a reconstruction method that proves
  the pass-1 comparison instead of asserting it.
- **The five new rows are two kinds on purpose** - three unit rows pinning the recognizer's answer,
  two wire rows pinning the hook's outcome - and entry 9 fails all five, so neither kind carries the
  entry alone.
- **The narrow metaclass fixture is load-bearing beyond its own row**: raising only for the probed
  name is what keeps pytest's own class introspection out of the measurement, and it is stated as the
  reason.

### Temp test verification

Mine, all under the gitignored `docs/builder/temp-tests/r1b/`:

- `test_w3p2_outcomes_after_the_guard.py` - the pass's central evidence: M-C's three inputs against
  the real hook, the package-mount loudness question driven in Django's own sequence, and the
  beyond-M-C input behind the Medium. **Disposition: kept as scratch, not promoted.** The three
  controlled declines are already pinned permanently by
  `::test_a_read_that_raises_is_declined_rather_than_raised_out_of_the_hook` and entry 9's five rows;
  the beyond-M-C row must **not** become a permanent row unless the maintainer takes the code path in
  `### Notes for Worker 1` item 1, since it would otherwise assert today's uncontrolled outcome as
  contract.
- `w3p2-entry6-absorbing.json` / `.md` / `.log` and `w3p2-entry6-absorbing-narrow.json` / `.md` /
  `.log` - the two rejected-anchoring measurements. Kept: they are the record of why the shipped
  anchor is the faithful one, and a future pass re-anchoring this entry a third time should read them.
- `w3p2-rerun.md` / `.log` - my nine-entry re-run.
- Re-run **unmodified** rather than inherited: `test_w2p2_hook_outcome_after_the_guard.py`,
  `test_w2p2_fallback_equivalence_for_a_raising_read.py`, `test_w2_fallback_equivalence.py`,
  `test_w1_probe_answers.py`, `test_w2_hasattr_vs_callable.py` (9 passed), and
  `test_r1b_p2_hotpath_recognizer.py` (three `.venv` runs, two floor runs).
- **My own pass-1 `test_w3_hook_outcome.py` now fails, and leaving it untouched was right.** I
  re-derived the outcome rather than trusting either the old assertion or the new report: it prints
  `controlled: returned None` for both shapes and fails on its own
  `assert all("UNCONTROLLED" in outcome …)`. The failure *is* the enactment. Disposition: kept as the
  before-picture; not promoted, for the reason above.
- Scratch roots used, all outside the repository: `.../scratchpad/w3p2-fail`, `.../w3p2-absorb`,
  `.../w3p2-absorb2`. Each holds only `pristine/`; none holds an `ACTIVE-MUTATION.json` or
  `RESTORE-FAILED.json`.

### Notes for Worker 1 (spec reconciliation)

R1b writes no spec or rationale text and I add none. The plan's items 1-8, the build reports' items and
my own pass-1 items 1-5 stand except where a measurement here supersedes them. New:

1. **`Escalated:` (contract-level) - does the package owe a controlled response to a forged
   `view_class` whose *accepted* boundary raises?** This is the Medium above, and it is M-C's own
   question one statement later, so it is a contract call and not a worker's. Measured evidence: a
   forged class carrying a **callable** under the probed name passes the probe, is constructed, and
   `process_view` calls it inside `except HTTPException` only - a `ValueError` from it leaves the hook
   uncaught, identically in `.venv` and at the floor
   (`docs/builder/temp-tests/r1b/test_w3p2_outcomes_after_the_guard.py`). Resolution paths:
   **(i) documentary, and it is what I recommend** - the code stays exactly as it is and three sites
   are scoped by one clause each: `::_package_view_instance` #"the probe is here so that every
   outcome of the hook is a controlled response" (scope to the outcomes the *recognition* produces),
   the same docstring's `TypeError` paragraph #"With the probe ahead of it what still reaches it is"
   (which enumerates package inputs only), and the Decision 18 wording in item 2 below. Cheapest,
   keeps the guard minimal, and leaves an honest limit rather than an absolute.
   **(ii) close it in code** - `except Exception` around `view._enforce_request_boundary(request)` in
   `process_view`. I do **not** recommend it: it would convert a package mount's own boundary failure,
   and any defect inside the body cap itself, into a silent pass-through, which is strictly worse than
   an imprecise sentence and cuts against the invariant the same docstring states. If it is taken it is
   a new round with its own failability entry, not a wording pass.
   Either way, **Decision 18 must not carry the unqualified absolute** until the path is chosen.
2. **The Decision 18 wording the pass-2 report hands you needs one clause.** As proposed it reads
   "Every outcome of the boundary middleware's `process_view` is a controlled response … That holds
   for **any** callback, including one forging the private marker over a class whose attribute
   machinery raises", with an honesty clause scoped to "a *package* mount's own failure". The measured
   input above is a *forged* class whose accepted boundary raises, so "any callback" is false and the
   carve-out does not reach it. Recommended shape: assert the absolute of **the recognition** - every
   recognition outcome is a refusal, a stamp, or a decline, including for a callback whose reads raise
   - and then state that running a boundary the recognition accepted surfaces that mount's own
   failure, package or forged, exactly as it would with this middleware uninstalled. That keeps every
   sentence true without weakening what M-B and M-C bought.
3. **M-C's own rejected alternatives should be recorded beside the decision**, as the pass-2 report's
   item 4 already asks: narrowing the three absolute sentences instead of guarding, and one broad
   `except Exception` around the recognition *and* the construction. I confirm the second one's
   recorded reason by measurement: with the construction inside the guard, a package mount whose
   `__init__` raises anything but `TypeError` becomes a silent decline, and my narrow absorbing probe
   shows the same shape swallowing eight rows' worth of determined answers.
4. **Context, not a finding against this round** (it is the plan's own dispatch note): spec Decision 18
   as written still says "No package middleware … no required `MIDDLEWARE` entry" and the rationale
   still lists a narrow pre-CSRF package middleware as a **rejected** alternative, so the spec
   currently forbids what shipped. R2 owns that, and nothing in this round changes it.
5. **The pass-1 Low about `::_wrapper_copying_only_csrf_exempt`'s cited evidence is closed in code**,
   so the scope question I left you is moot: the sentence was corrected inside this round's own write
   set and I re-measured the correction. No decision needed.
6. **For the final gate:** the operative failability manifest is
   `docs/builder/temp-tests/r1b/proofs-pass2.json` (9 entries); this round's `proofs.json` is pass 1's
   generation and four of its anchors no longer match. My independent records are
   `w3p2-rerun.md` / `.log`, plus `w3p2-entry6-absorbing*.{json,md,log}`. The floor run and the
   hot-path numbers are in the pass-2 report and reproduce as recorded (my readings above). The two
   `.md` doc surfaces this cycle still owes (V1-V7) are untouched by this round.

### Review outcome

`review-accepted`.

M-C's enactment is correct, complete, and independently verified: the guard covers exactly the
recognition reads M-C names, the construction keeps its narrow `except TypeError` outside it, the three
inputs that escaped `process_view` in pass 1 now answer a controlled `None` on both interpreters, a
genuine mount is still recognized, and the argument that makes a broad `except` defensible here - that
a package mount's own broken boundary stays loud in the view-local path the declined request goes on to
run - is measured at that call site rather than asserted. All nine failability entries re-ran
**set-equal** at Worker 2's recorded scope with 0 collection/setup errors, every baseline `205 passed`
and every restore byte-proved; entry 9 sits at 5 rows, entry 6's growth is exactly the five new rows,
entry 8 keeps its pass-1 set inside a larger one, and route 3's membership still makes B-4 a
measurement. The sharpest claim in the report - that the rejected anchoring of entry 6 would have let
the guard absorb the entry's own failures - is confirmed by running both rejected shapes: they absorb
eight of the twelve rows. The floor run, the hot-path readings, the no-import property, the lint and
hook gate and the byte-unchanged tracked-path allowlist all reproduce, the public surface and the
version quintet have not moved, and the tree is exactly as I found it.

One Medium stands, **escalated to Worker 1 rather than held against this round** (`ARTIFACT.md`'s
`review-accepted` clause, and `worker-3.md` "Review artifact requirements"): the absolute sentence M-C
decided to keep verbatim is true of every outcome the *recognition* produces and false for one outcome
the *hook* produces - a forged class whose accepted, callable boundary raises. The code is right there
and the alternative would be worse, so the resolution is a one-clause scoping in three places plus the
Decision 18 wording, and the prior question is the same contract call M-C answered one layer in. One
Low records three statements in the report that do not reproduce as written; none changes a reading and
no change is requested. Nothing in either finding asks Worker 2 for another pass.

---

## Final verification (Worker 1)

Required reading walked before judging anything, and the **W1** column of `BUILD.md`
`## Required reading per worker` walked myself rather than taken from the dispatch: `AGENTS.md`,
`START.md`, `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, `docs/builder/worker-1.md`,
`GOAL.md`, `docs/GLOSSARY.md` (the six card-046 entries), `CHANGELOG.md` (untouched, confirmed
clean), the active spec (Decision 18 read at source in full, plus 7, 9 and 10), the active spec
**rationale** (its `### Decision 18` entry read in full — I own it), the whole
`# Closeout cycle (card 046)` section of the build plan including `## Maintainer decision M-B`,
`## Maintainer decision M-C`, `## Round R1b`, `## Write-set correction W-1` and
`## Worker-0 dispatch decision D-1`, this artifact end to end, the closed
`bld-046-r1-remediation_review.md` including its own final-verification hand-off list, and my own
memory file. Nothing else is marked `yes` for W1, so the dispatch omitted nothing; the other
workers' memory files were not read.

**Nothing below is accepted on the strength of a prior pass's record.** Every number this section
states is one I measured in this pass, and where my reading agrees with the builder's or the
reviewer's, the agreement is between three independent measurements rather than a citation.

### Baseline, write set, and the things that must not have moved — measured this pass

- **`git diff --cached --name-status` is exactly `A django_strawberry_framework/_boundary_ordering.py`
  and nothing else.** `## Write-set correction W-1` authorized exactly that one path; the index is
  still at exactly that one path. `git add` was run by no pass of this round, mine included.
- `git status --short`: the same ten lines every pass of this round recorded, character for character
  — the staged-and-modified protocol module, six paths dirty from R1 and Worker 0, and the two
  untracked artifacts. Nothing was reverted, stashed, checked out, restored or worktree'd at any point
  in this pass.
- **SHA-256 of all eight tracked files, read at the end of my pass**, and every one identical to the
  value the pass-2 report and the pass-2 review recorded:

  | File | SHA-256 | Whose |
  | --- | --- | --- |
  | `django_strawberry_framework/middleware/request_body.py` | `5900fb367db8a944583474eae776051de357884b05b630f2e4ef38dc154044a8` | R1b pass 2 |
  | `django_strawberry_framework/_boundary_ordering.py` | `7b3d9e51b7fb7ecc4cd578139ad3db2509f638884c20f9c6d637f43645c67bee` | R1b pass 1 |
  | `tests/test_views.py` | `abe0406a26fc9c15b11ec7f3c9619e27a2854ad5d1cf2d8ef5aa733cb74192d5` | R1b pass 2 |
  | `django_strawberry_framework/views.py` | `e8aeb156550fc45a2ce09a15284517993ca72e68655756a24d15fd495b34cc98` | R1's, unmoved |
  | `django_strawberry_framework/_request_body.py` | `2c1fd48618d4b01c15ed7fa25a6535b7ba4c821cdf1da24826bc0e51040c70ff` | R1's, unmoved |
  | `django_strawberry_framework/consumers.py` | `1bdf298c473fd1a03b31121d845e1a5f7fa2b8fad5152a4de84ba9b291c5c7ef` | byte-identical to `HEAD` |
  | `tests/test_routers.py` | `5bf697bbe27b5d66dd127ace3703fe2f7ef975d350e3ad19eafcac2e393303ae` | R1's, unmoved |
  | `examples/fakeshop/apps/kanban/constants.py` | `6761fadb49c4f28517a8e30989ac62b09c43d9d5773cd45b55364af59fa46d54` | R1's, unmoved |

- **No live mutation anywhere.** `--check-anchors-only` over the operative manifest exits **0** with
  all nine anchors matching exactly once *before any copy was taken*, which is the one reading that
  can tell its own reference is already mutated; and no `ACTIVE-MUTATION.json` or
  `RESTORE-FAILED.json` exists under any scratch root, mine included.
- **Version quintet untouched**: `pyproject.toml` `version = "0.0.14"` (line 4) and
  `django_strawberry_framework/__init__.py` `__version__ = "0.0.14"` (line 41), neither dirty.
  `CHANGELOG.md` clean. Both cycle-wide declarations hold as copied.
- **Spec status-line re-verification (this spawn).** The opener still reads "Planned for `0.0.15`"
  and the `Status:` block still reads "**BUILT — all five slices … The `0.0.15` release itself is the
  joint cut's, so the version quintet still reads `0.0.14` on disk.**" Both are accurate against
  disk and R1b falsifies neither. No spec edit is made or licensed — R1b's write set names neither
  the spec nor its rationale.

### Independent failability re-run: nine of nine, and the sets are identical three ways

I re-ran **the whole nine-entry operative manifest** (`docs/builder/temp-tests/r1b/proofs-pass2.json`)
rather than a subset, at Worker 2's recorded scope, through `scripts/prove_failability.py`, into my
own scratch root outside the repository, with `--check-anchors-only` first and separately. Record:
`docs/builder/temp-tests/r1b/w1-fv-rerun.md` / `.log`. Exit **0**; every pre-mutation baseline
`205 passed` at pytest exit 0; **0** collection/setup errors on all nine; `pre-existing failing rows
excluded from the count: 0` on all nine; every restore proved by `filecmp.cmp(shallow=False)` plus
SHA-256 against the runner's own pre-mutation copy.

Then the reading that matters, computed as a **symmetric difference over the parsed node-id lists**
of three separate records — Worker 2's emitted `proofs-pass2.md`, Worker 3's `w3p2-rerun.md`, and my
`w1-fv-rerun.md`:

| # | Boundary | W2 | W3 | W1 | W1 vs W2 | W1 vs W3 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | the marker clause | 4 | 4 | **4** | EMPTY | EMPTY |
| 2 | `__bool__` -> `True` | 3 | 3 | **3** | EMPTY | EMPTY |
| 3 | `__bool__` -> `False` | 13 | 13 | **13** | EMPTY | EMPTY |
| 4 | `::_require_boundary_before_csrf` | 3 | 3 | **3** | EMPTY | EMPTY |
| 5 | `__bool__` (the per-request key) | 7 | 7 | **7** | EMPTY | EMPTY |
| 6 | the aggregate recognition, guard included | 12 | 12 | **12** | EMPTY | EMPTY |
| 7 | the two bookkeeping-shape clauses | 2 | 2 | **2** | EMPTY | EMPTY |
| 8 | the boundary probe | 6 | 6 | **6** | EMPTY | EMPTY |
| 9 | the guard around the reads | 5 | 5 | **5** | EMPTY | EMPTY |

**No entry is in the 0-or-1 band**, entry 9 (the round's second new boundary) sits at 5, and entry 8
(the round's first) at 6. Every record required by `BUILD.md` `### What gets recorded` exists for
every entry — mutation as applied, listed node ids, collection/setup errors separately, the
pre-mutation state of the same scope, and the byte-compared revert — and no entry is a zero-row
entry, so no `why 0` judgement is owed by anyone. Nesting re-derived by set containment rather than
read off the prose: entry 9 is a strict subset of 6, entry 7 is a subset of 6 and disjoint from 9,
entry 8 is a subset of 6 overlapping 9 in the four raising rows, and route 3
(`[/marked-rejected-initkwargs/]`) is in 6 and in neither 8 nor 9 — so **B-4 stays a measurement**:
that route still reaches the construction arm, and removing the arm would restore an unhandled `500`
for a row the suite already pins.

**The seven R1 entries deliberately not re-run.** I checked the premise rather than the conclusion,
as the reviewer did and independently of it: nothing this round added can reach those boundaries — the
five new rows are a bare `GET` to declined routes and three direct calls to the recognizer with no
request — and their unmutated green state is in the record nine times over as the pre-mutation
baseline of the entries that did run. Mutating three files dirty with a closed round's uncommitted
work for a stability check obtainable that way remains the worse trade, and it is the trade the plan
argued per entry. Accepted.

### The manifest's two anchor subtleties, and the durable lesson

**Entry 6's second re-anchor is the faithful one, and the reviewer's correction to the builder's
characterisation is the more important half.** The builder predicted that anchoring the aggregate
*inside* the guard would let the guard absorb the failures the entry exists to produce, avoided that
shape, and described the rejected shape as one that "would have read as a 0-row aggregate". The
reviewer ran both variants and measured **4 rows** each — absorbing 8 of the 12 in the charitable
variant, and collapsing to entry 1's own set in the literal one. I accept that measurement (its
manifests, reports and logs are on disk beside the round's own, `w3p2-entry6-absorbing*.{json,md,log}`,
and my own anchors check confirms the tree is unmutated after them) and I record the lesson at the
strength it deserves, because it generalizes past this entry:

> **A row-count acceptance rule cannot see anchor quality, and its dangerous failure mode is a
> PLAUSIBLE count, not a zero.** A 4-row aggregate satisfies `BUILD.md`
> `### Acceptance rule: weakly pinned is revision-needed`, reads as pinned, and would have measured a
> third of its boundary. A zero is graded by the runner and re-run by the reviewer; a plausible number
> is graded by nobody. This cycle has twice been saved by a zero being visible, and this is the first
> time it has been shown what the invisible version looks like.

**Entry 8's growth from 2 to 6 rows is benign and correctly reported as unpredicted.** Re-derived as
a set relation rather than a count: its pass-1 set is a strict subset of its pass-2 set, nothing was
lost, and the four new rows are the two raising wire routes plus their two unit rows, failing because
the deleted probe lets the forged classes be *constructed* and their `__init__` raise `AssertionError`,
which the narrow `except TypeError` does not absorb. The entry therefore still pins the probe and not
the fixtures — deleting the fixtures returns it to 2, above the band either way. Reporting it as
measured-not-designed is the right disposition, and it is what let the growth be checked for meaning
instead of counted.

### The crux, measured myself, and measured in a stronger form than either prior pass

The claim that makes the broad `except Exception` legitimate is that a **package** class whose
boundary read raises is still loud on the path a declined request goes on to run, so the guard masks
no misconfiguration. Both prior passes measured it by calling
`views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once` on a hand-built instance. I
measured it **at the wire, in both chain arrangements**, which is the form that answers the question
the claim is actually about — *does installing this middleware change anything about how loud a broken
package mount is?* (`docs/builder/temp-tests/r1b/test_w1_fv_absolute_and_masking.py`, mine, written
from scratch; identical output in `.venv` Python 3.14.2 / django 6.0.5 and at the floor Python
3.10.19 / django 5.2):

```
Q1 masking crux - a PACKAGE class whose boundary read raises
   hook:                       controlled: None | stamped=False
   wire, boundary installed:   UNCONTROLLED at the wire: ValueError: boundary read raised
   wire, boundary uninstalled: UNCONTROLLED at the wire: ValueError: boundary read raised
Q2 the absolute - a FORGED class whose accepted callable boundary raises
   hook:                       UNCONTROLLED out of process_view: ValueError: a forged boundary that raises when it is run
   wire:                       UNCONTROLLED at the wire: ValueError: a forged boundary that raises when it is run
Q3 the TypeError enumeration - a FORGED __init__ raising TypeError
   hook:                       controlled: None | stamped=False
   wire:                       controlled at the wire: 200
Q4 genuine mounts still recognized
   sync:  DjangoGraphQLView
   async: AsyncDjangoGraphQLView
```

**Q1 settles the crux affirmatively and by identity.** The two wire outcomes are the *same* failure,
so the guard does not merely leave the misconfiguration loud somewhere — it leaves it exactly as loud
as it is with the middleware uninstalled, which is the strongest form of "masks nothing" available.
The stamp is absent after the decline, so the cap is still the view's to run, which is the other half.
**Q4** is the check a suite full of decline rows cannot make for itself: recognition did not become a
blanket decline at either transport. Both accepted.

**Q2 and Q3 are the finding, and they are below.**

### The one finding escalated to me: resolved, and the fix is documentary

`## Review (Worker 3, pass 2)` escalated a Medium rather than holding the round, and directed the
wording question here. I tested its judgement rather than adopting it, and I reach the reviewer's
conclusion on the code and the opposite conclusion on the disposition.

**The measurement, mine (Q2 above).** A forged `view_class` carrying a **callable** under the probed
name passes the probe by design, is constructed, and `process_view` calls that boundary inside
`except HTTPException` **only** — so a `ValueError` from it leaves the hook uncaught, at the hook and
at the wire, on both interpreters. `middleware/request_body.py::_package_view_instance`'s docstring
nonetheless keeps, verbatim, *"the probe is here so that every outcome of the hook is a controlled
response"*. That sentence is true of every outcome **the recognition** decides and **false for one
outcome the hook produces**.

**A second site, also mine (Q3 above), which the reviewer named and I confirmed by execution.** The
`TypeError` paragraph states *"With the probe ahead of it what still reaches it is a package class
named with kwargs it rejects, and a package subclass whose own `__init__` raises"* — an enumeration
presented as complete. A **forged** class that passes the probe and whose accepted `__init__` raises
`TypeError` reaches the same arm and is absorbed: measured, a controlled `None` at the hook and a
`200` at the wire. Same shape of defect as the absolute, one paragraph down.

**Where I agree with the reviewer: this is not a code defect.** I re-derived the cost of closing it
and it is real. Guarding `view._enforce_request_boundary(request)` would apply to a *recognized*
boundary, and the recognition cannot distinguish a package mount from a forged class that carries a
callable of the probed name — that is precisely what M-B decided the probe would and would not buy.
So the guard would sit across the body cap's own failures, and Q1 shows the package-mount case is
deliberately loud and identically loud with the middleware absent. Making the sentence literally true
would cost the invariant the same docstring correctly states. M-C's decision stands and I re-open
nothing: the code M-C ordered landed, is correct, and is independently verified above.

**Where I do not agree: the disposition.** M-C's rationale asserts that guarding the reads "leaves
the three absolute sentences true as written". That premise is *measurably* wrong for one of the
three, which is a fact about the sentence rather than a re-litigation of the decision. And the round's
own record treats the sentence as an assertion rather than a statement of purpose: R1 inventoried it
as one of five **over-claiming** sites, the plan's step 3 directs "keep verbatim. It **becomes true**
with this change; that is the point of the round", and the `### Dispatched findings checklist`'s first
box records it as *"Closed by making the claim **true**"*. Under the round's own reading the sentence
is a promise, and the promise is not kept.

That is the exact shape this closeout cycle exists to remove, and it has now recurred **three times
inside this one round**: M-B existed because a docstring promised a controlled hook the code did not
deliver; M-C existed because the sentence M-B's fix was supposed to make true still was not; and it is
still not. `BUILD.md`'s standing lesson is that a green `Status:` chain does not prove the spec matches
the code, and my role file makes final verification the place that stops. Accepting a fourth iteration
of the same over-claim — in a security-adjacent module, in the sentence R2 is about to lift into
Decision 18 — would be that acceptance. **Two clauses, in a file already in this round's write set, is
the cheapest possible correction and there is no later home for it**: `middleware/request_body.py` is
source, R2's write set is the spec and the rationale only, and R3's is the standing docs. So it is not
deferrable to a documentation round.

I am read-only on source, so this is `revision-needed` with the wording rather than an edit.

**Required amendment A — `middleware/request_body.py::_package_view_instance`, the limit paragraph's
final sentence.** Currently
`#"and the probe is here so that every outcome of the hook is a controlled response, not to defend
against a forger"`. It must state two facts (wording is Worker 2's; the facts are not):

1. the absolute is scoped to what **the recognition** decides — every recognition outcome is a
   refusal, a stamp, or a decline, including for a callback whose reads raise;
2. the residual is stated **once**, positively, as an invariant rather than a gap: running a boundary
   the recognition accepted surfaces that mount's own failure, and a boundary raising anything other
   than an `HTTPException` leaves `process_view` uncaught **deliberately and identically for a package
   mount and for a forged class carrying a callable of the probed name**, because a guard there would
   sit across the body cap's own errors.

A serviceable form, offered so the pass is a wording pass and not a design one: *"Forging the marker is
outside the threat model either way, and the probe is here so that every outcome the recognition
reaches is a controlled response — a refusal, a stamp, or a decline — not to defend against a forger.
Running a boundary the recognition accepted is a different question: a boundary that raises anything
but an `HTTPException` leaves `process_view` uncaught, deliberately and identically for a package
mount and for a forged class carrying a callable of the probed name, because a guard there would sit
across the body cap's own errors."*

**Required amendment B — the same docstring's `TypeError` paragraph.**
`#"With the probe ahead of it what still reaches it is"` must stop reading as an exhaustive
enumeration of package inputs. The fact to state: what reaches the arm is a class that carries a
callable of the probed name and cannot be built from the kwargs it names — a package class named with
kwargs it rejects, a package subclass whose own `__init__` raises, **and equally a forged class whose
accepted `__init__` raises `TypeError`** — and the "hides no misconfiguration" argument that follows is
about a **package** mount, which is where it is load-bearing and where it still holds unchanged.

**No test row is owed, and none should be invented.** No boundary moves; both amendments are
docstring text. I confirmed mechanically that this cannot disturb the manifest: none of the nine
anchors lies inside a docstring, so all nine still match exactly once after a docstring-only edit, and
every row set stays as measured above. A permanent row asserting today's uncontrolled outcome must
**not** be added — the reviewer is right that it would freeze as contract an outcome the maintainer
has not chosen (see hand-off item **D-7**).

**The three "every other outcome" sites: decided, not required, so the next pass does not re-derive
it.** `middleware/request_body.py::_package_view_instance` #"a hook whose every other outcome is a
controlled response", `tests/test_views.py::_marked_callback_without_a_view_class`'s docstring, and
`::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed`'s docstring all use the
`every other` form inside a counterfactual clause about a shorter recognition. Strictly, the input in
Q2 is also "other". I decide they need **no** change: once amendment A states the residual once and
positively, the phrase is doing local counterfactual scoping in a docstring that names its own limit,
which is a different act from an unqualified promise. Recorded as decided rather than missed; a future
pass that disagrees should change all three or none.

### The hot-path judgement, which is mine because the declaration is inherited from a plan I wrote

I agree with the reviewer that the elevated absolutes are an honest restatement and **not** a budget
finding, and I agree for a reason I re-measured rather than accepted. My own readings of the recorded
snippet, recorded command unchanged:

| Environment | before (per call) | after (per call) | delta per call |
| --- | --- | --- | --- |
| `.venv` (Python 3.14.2), run 1 | 0.5565 us | 0.5476 us | **-0.0089 us** |
| `.venv` (Python 3.14.2), run 2 | 0.5468 us | 0.5447 us | **-0.0021 us** |
| floor (Python 3.10.19), run 1 | 0.5935 us | 0.5954 us | **+0.0019 us** |

The **"before" arm is pass 1's body — code this pass did not write — and it reads 0.5468-0.5935 us in
my runs, itself above R1 pass 3's recorded 0.50-0.53 us band.** An arm that predates the change under
measurement cannot have been elevated by it, so the elevation is the machine and the number belonging
to this round is the delta between two arms in one process, which straddles zero and sits below the
metric's resolution on both interpreters. Reporting the absolutes as measured rather than placing them
inside an inherited band is the correction the pass-1 Low asked for and it is discharged. Declining to
re-capture R1's 400-iteration request median is right and is correctly *stated* rather than answered
"not applicable". Keeping run 1's +0.0825 us outlier in the table instead of re-running until it
vanished, and taking five readings per environment instead of the plan's two, are both better than the
plan asked for. Whether the cost is acceptable is the maintainer's call; nothing above noise is
visible to weigh, and no correctness boundary was weakened to buy any of it back.

### Floor verification — re-run by this pass, at the plan's full declared scope

The plan assigns the run to Worker 2's build pass and it happened; the gate is the backstop, so I
re-ran it rather than reading it. Floor facts taken from `BUILD.md` `## Floor verification`, its single
canonical statement: the supported floor is **Django 5.2.0 on Python 3.10 with strawberry-graphql
0.316.0**.

- `/tmp/dsf-floor` existed and its resolved versions were **read before it was relied on**:
  `/tmp/dsf-floor/bin/python -V` -> **Python 3.10.19**;
  `uv pip list --python /tmp/dsf-floor/bin/python` -> **django 5.2**, **strawberry-graphql 0.316.0**,
  asgiref 3.12.1, channels 4.3.2, cross-web 0.7.0, django-filter 26.1, pytest 9.1.1, and
  **django-strawberry-framework 0.0.14** editable at this checkout, so it carries this round's bytes.
  That is the floor as `BUILD.md` states it.
- `/tmp/dsf-floor/bin/python -m pytest tests/test_views.py --no-cov` -> **205 passed**. The plan's
  whole declared scope, green, and the total both prior passes claimed.
  Log: `docs/builder/temp-tests/r1b/w1-floor-run.txt`.
- The floor questions the round creates, re-answered by me at the floor: my own four-question probe
  above is **byte-identical between the two interpreters**, the uncontrolled Q2 line included.
- **The shared `.venv` was not mutated by this pass.** Read rather than recalled: `.venv` carries
  Python 3.14.2, django 6.0.5, strawberry-graphql 0.316.0 — far above the floor. Every floor command
  I ran was `/tmp/dsf-floor/bin/python -m pytest` or carried an explicit
  `--python /tmp/dsf-floor/bin/python`, and I ran no `uv pip install` at all.

### Focused runs, staleness, and the lint / hook gate — all re-run read-only

- `uv run pytest tests/test_views.py examples/fakeshop/test_query/test_transport_api.py tests/middleware/ --no-cov`
  -> **291 passed**, which is exactly the 205 + 69 + 17 the pass-2 report states.
- `uv run pytest tests/ --no-cov` -> **4526 passed, 38 skipped**. Every total reproduces.
- Staleness, run against the tree rather than the file list: neither shape in `BUILD.md`
  `### Test staleness a focused run cannot see` is present (no example-model field changed, no wire
  shape converted); `_enforce_request_boundary` occurs 7 times in `tests/` and `examples/`, all in
  `tests/test_views.py`, none under `examples/**`; nothing outside that file forges the marker.
- `uv run ruff format --check` -> `3 files already formatted`; `uv run ruff check` -> `All checks
  passed!`; `scripts/check_trailing_commas.py --check` -> exit **0**; `git diff --check` -> exit **0**.
- ASCII-only verified independently of the hook by byte scan: **0** bytes above 127 in all three files
  (highest 125 / 124 / 125).
- `kanban-tracked-path-constants` verified **without writing the baseline-dirty file**:
  `--check` exits **0**, and a regenerate to an outside-the-repo `--output` `cmp`s clean against the
  tracked copy at SHA-256 `6761fadb49c4f285...` on both sides. The generated allowlist really is
  byte-unchanged, so the maintainer's commit will not be rolled back by the hook.
- Prose discipline swept mechanically by me over **830 added lines** across the three files (which for
  the two `HEAD`-based files covers R1's additions too): **0** severity labels, **0** round / pass /
  slice / `M-B` / `M-C` / `Test-N` indices, **0** `bld-*.md` filenames, **0** `docs/feedback*.md`
  mentions, **0** raw `path:NN` references. The whole of the new `_boundary_ordering.py` swept the same
  way: **0** on every pattern.
- **Public surface**: `git diff` and `git diff --cached` on
  `django_strawberry_framework/__init__.py` are both **0 lines**; `middleware/request_body.py`'s
  `__all__` is still the single-name tuple, so the documented `MIDDLEWARE` string is unchanged;
  `_BOUNDARY_METHOD` is private, in a private module, re-exported nowhere.
- **DRY across this round and R1**: nothing new. No helper was added and none is justified — the
  reviewer's existence challenge and my own plan-time inventory both landed there, and
  `repeated string literals: 0` in both refreshed shadow overviews. The one deliberately-not-built
  consolidation (a recognizer shared with `middleware/debug_toolbar.py`) keeps its recorded condition
  as hand-off **D-6**; R1b meets neither half of it.

### Plan audit: every step, and the two plan-time readings the build corrected

Every step of `### Implementation steps` (0-13) landed, and every item of `### Test additions /
updates` (T1-T4), `### Non-weakening checks` (1-6), `### Fail-open shapes to read for` and
`### Floor verification scope` is discharged and independently confirmed above. Both builders'
on-disk `### Notes for Worker 1 (spec reconciliation)` lists exist and are discharged: pass 1's
required-amendment content was superseded by M-C, which pass 2 enacted; pass 2's items are folded into
the hand-off below.

Two plan-time readings of **my own plan** did not reproduce, and the build pass found and corrected
both honestly rather than quietly implementing around them. `ARTIFACT.md` forbids editing a prior
section, so I record the corrections here as prose:

- **Step 6's second reading is wrong as written and the property it checks holds.** The plan's
  `grep -c 'middleware.request_body\|middleware import' django_strawberry_framework/views.py`
  predicted 0 and returns 5: the unescaped `.` matches the `/` in five docstring symbol references of
  the form ``middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware``. I reproduced it and
  then established the property the way it should have been established in the first place — **by
  execution**. In a fresh interpreter after `django.setup()`, importing
  `django_strawberry_framework._boundary_ordering` adds exactly `['django_strawberry_framework.
  _boundary_ordering']` to `sys.modules` and nothing else; importing
  `django_strawberry_framework.middleware.request_body` adds only itself and its package, and
  `django_strawberry_framework.views` is **not** in `sys.modules` afterwards. `views.py`'s import
  block contains no middleware import and `middleware/request_body.py`'s contains no `views` import,
  read as statements rather than as occurrences. The no-import property that B-1 exists to preserve
  holds, proved mechanically. This is `BUILD.md` `## Claims are proven mechanically`'s vocabulary trap
  running in the over-counting direction, and the lesson is the one the builder drew: a grep locates
  an import claim, execution establishes it.
- **Step 12's description of the live tier's probe wrapper was wrong in the safe direction.**
  `examples/fakeshop/test_query/test_transport_api.py::_carrying_the_packages_csrf_mark` copies
  `csrf_exempt` and nothing else — neither the marker nor Django's `view_class` / `view_initkwargs`
  bookkeeping. The conclusion is unaffected (with no marker the callback is declined at the first
  clause, so this change cannot move it) and the live tier is unchanged at 69 passed. The build pass
  also corrected the sibling sentence that asserted the same falsified evidence in shipped test prose
  (`::_wrapper_copying_only_csrf_exempt`'s docstring), which closed the pass-1 Low in code and made
  the scope question the reviewer left me moot.

### Dispatched findings checklist audit — all seven ticks stand, none un-ticked, none owed a deferral

Walked against the landed code myself, not against the build reports.

1. **The over-claiming docstring made true rather than narrowed.** The specific condition R1
   inventoried — a marked callback over a real, buildable, non-package class reaching
   `view._enforce_request_boundary` — is closed: measured at the wire as a controlled `200`, and it is
   entry 8's first row. Tick stands. The residual in my Medium is a **different** input class, and it
   qualifies the sentence, not the fix.
2. **Five routes and a five-route docstring.** Landed and superseded upward: **seven** routes of two
   kinds, with the "no two are refused by the same clause" claim correctly scoped to the first five
   rather than restated over seven, where it would be false. Tick stands.
3. **The probe is on the class, before any construction.** Read at source: the probe statement
   precedes the construction `try`. Tick stands.
4. **`_BOUNDARY_METHOD` is the protocol module's third fact and costs no `views.py` import.** Landed;
   the no-import property proved by execution above. Tick stands.
5. **The five over-claiming sites rewritten.** All five read as R1 named them; the two amendments I
   require are a residual on site 1 plus a sixth site the round created, not a failure to sweep the
   five. Tick stands.
6. **A foreign but buildable class's `__init__` is never called** — pinned by T2's delta-form
   recording assertion, which I read at source and which is deliberately *not* what the entry-8 mutant
   fails on (the answer assertion fails first); it is the row's guard against a future
   probe-the-instance refactor. Tick stands.
7. **The new clause has its own entry, 6 and 7 re-measured, nothing in the 0-or-1 band.** Confirmed by
   my own nine-entry re-run. Tick stands, and it now covers two new boundaries rather than one.

No box is `- [ ]`, so no box carries a deferral reason. Nothing was ticked with no matching fix and
nothing landed was left open. Worker 2's decision to tick nothing in pass 2 is correct on the right
rule: the checklist predates M-C, and `BUILD.md` `### Dispatched findings checklist` is explicit that a
maintainer decision the round escalated is not a checklist box.

### Consolidated hand-off for R2 and R3 — R1's authoritative list, updated by R1b

R1's final verification produced one de-duplicated list precisely so R2's planning pass has a single
source. **This section updates that list in place rather than appending a second scattered set: R2
works from R1's `### Consolidated hand-off for R2 and R3` with the amendments below applied.** Every
item keeps R1's key.

**Status changes R1b causes**

- **M-B moves out of "Blocked on the maintainer" and into landed-needs-spec-text.** It is decided
  (build plan `## Maintainer decision M-B`) and enacted here: the recognition declines unless the
  callback's `view_class` itself carries the boundary method, probed on the class before any
  construction. R1's three candidate answers (a-instance / b-narrow / c-refuse) are all now
  **rejected alternatives to record**, not open options. Its "site inventory the decision must sweep
  is five" is discharged in code.
- **M-C is a second decided-and-enacted contract call R1's list does not know about** (build plan
  `## Maintainer decision M-C`): the four recognition reads are guarded so a read that cannot answer
  declines, while the construction keeps its narrow `except TypeError`. Same status as M-B — landed,
  needs spec text — and it has its own rejected alternatives to record.
- **R2-4 is superseded and grows from two clauses to four.** R1's wording (*"only for a callback whose
  bookkeeping it can build that view's instance from, and it never calls anything that is not a class
  to try"*) is now incomplete. Replacement contract wording for R2 to shape: *the boundary middleware
  runs a package view's boundary only for a callback whose `view_class` carries that boundary **as
  something callable**, tested by attribute **on the class, before anything is constructed**; it never
  calls anything that is not a class to try, it builds nothing it has not established a boundary on,
  and a read it cannot complete is a decline rather than an exception out of the hook. Every other
  callback is declined and keeps the view-local arrangement.* All four clauses are measured, at the
  scope `tests/test_views.py`: entry 6 at 12 rows, entry 7 at 2, entry 8 at 6, entry 9 at 5. R1's
  standing instruction is unchanged and still binding: **do not** write the `view_initkwargs` `dict`
  test as a symmetric guard — removing it makes the middleware run the boundary for a non-`dict`
  mapping, so it is a narrowing preference, not a bound.
- **R2-1 and R2-12 stand exactly as R1 wrote them, and R1b confirms both at source.** Decision 18's
  heading still reads "**via view-local CSRF re-entry**", which now names the fallback only; its text
  still opens "No package middleware, no reimplemented token validation, no ordering system check, and
  no required `MIDDLEWARE` entry" — false in its first clause, true in its second, **so the spec
  currently forbids what shipped**. The rationale's `### Decision 18` still lists as a **rejected**
  alternative "A narrow package middleware placed before `CsrfViewMiddleware`, plus a system check
  that detects missing or wrong ordering", which is what shipped minus the "required" — the
  withdrawable exemption is what makes the entry optional, and what shipped is a **startup raise from
  `__init__`**, not a Django system check. The rewrite is therefore larger than a sentence: R2 either
  moves that bullet to a keyed change record naming the round that adopted it, or keeps it rejected in
  its *original* form (middleware **plus** a required entry) and states what the shipped design does
  differently. R1b changes none of it.
- **R2-2, R2-3, R2-5 through R2-11, R2-13 stand unchanged.** No R1b measurement bears on them.
- **R3-1 through R3-7 stand unchanged**, and R1b creates no documentation work: `_BOUNDARY_METHOD` is
  private in a private module, no glossary term or terms-CSV row is created, no `examples/**` path is
  touched, and R3-6's `docs/TREE.md` regenerate is still safe — `_boundary_ordering.py`'s docstring
  gained a fourth `The protocol` paragraph and I re-read it for staging language, of which it carries
  none. M-A, R3-2's reduced re-pin obligation and R3-4's live-first opportunity are exactly where R1
  left them.

**New R2 items from R1b**

- **R2-14. Decision 18 may assert the absolute only in its honest form, and the wording R1b's build
  reports propose is wrong.** The pass-2 report hands R2 *"Every outcome of the boundary middleware's
  `process_view` is a controlled response … **That holds for any callback**, including one forging the
  private marker over a class whose attribute machinery raises"*, with an honesty clause scoped to "a
  *package* mount's own failure". **"any callback" is false and the carve-out does not reach the
  counterexample**: a *forged* class carrying a callable of the probed name passes the probe, is
  constructed, and its raising boundary leaves the hook uncaught — measured by me at the hook and at
  the wire on both interpreters. Corrected wording for R2 to shape: *assert the absolute of the
  **recognition** — every recognition outcome is a refusal, a stamp, or a decline, including for a
  callback whose reads raise — and then state that running a boundary the recognition accepted
  surfaces that mount's own failure, package or forged, exactly as it would with this middleware
  uninstalled.* The last clause is load-bearing and it is measured: with the boundary middleware
  installed and uninstalled, a package mount whose boundary read raises produces the identical
  uncontrolled failure. **This supersedes the plan's item 4 and the pass-2 report's item 1.**
  *Status: open, wording settled here.*
- **R2-15. Record M-B's and M-C's rejected alternatives beside the decision**, each with its one-line
  reason, as `worker-1.md` `## Review-round custody` requires for a settled contract choice.
  M-B's: probing the built instance (closes the `500`, leaves the foreign constructor running, which
  the suite already forbids by a row); declaring the forged marker out of contract (more text than the
  fix, and an exception to Decision 7's no-unrelated-`500` doctrine); refusing it outright
  (contradicts the accepted state-enumeration contract that every unforeseen state answers "no" and
  falls back). M-C's: narrowing the three absolute sentences instead of guarding (the documentary
  narrowing M-B already rejected one shape over, for a fix of comparable size); one broad
  `except Exception` around the recognition **and** the construction (it would replace the narrow
  `except TypeError` whose narrowness R1's review examined and accepted, and would convert a package
  mount's own non-`TypeError` construction failure into a silent decline — a shape R1b measured
  swallowing eight rows' worth of determined answers). *Status: open.*
- **R2-16. The probe's limit belongs in the rationale, in both shapes, and after M-C the limit is only
  that such code *runs*.** A class attribute probe consults the class's own attribute machinery, and
  there are **two** shapes of it: a metaclass `__getattr__` and a class-level descriptor under the
  probed name. Keep two sentences distinct rather than conflating them: forging the package's private
  marker stays outside the threat model (the spec-045 stance that no in-interpreter walk is a trust
  boundary against a party already running code in the process), and the probe plus the read guard
  exist so the hook's outcomes are controlled, not to defend against a forger. Conflating them is what
  would invite a future round to over-promise — which is the failure this round hit twice.
  *Status: open.*

**New deferred item**

- **D-7. Whether the package owes a controlled response to a forged `view_class` whose *accepted*
  boundary raises.** This is M-C's own question one statement later and is a contract call, not a
  worker's. Measured, at the hook and at the wire, identically on Python 3.14.2 / django 6.0.5 and at
  the floor: a forged class carrying a callable of the probed name passes the probe, is constructed,
  and a `ValueError` from that call leaves `process_view` uncaught
  (`docs/builder/temp-tests/r1b/test_w1_fv_absolute_and_masking.py`, and the reviewer's
  `test_w3p2_outcomes_after_the_guard.py`). **Deliberately not resolved here, and the documentary
  amendments this pass requires are chosen so as not to prejudge it**: they state the residual as the
  invariant it currently is rather than as a gap awaiting a fix. If the maintainer ever takes the code
  path, it is `except Exception` around `view._enforce_request_boundary(request)` in `process_view`, it
  is a new round with its own failability entry, and its cost is that it sits across the body cap's own
  errors and across a package mount's broken boundary — which Q1 above shows is deliberately as loud
  with the middleware installed as without it. Both prior passes recommended against the code path and
  so do I. **No permanent test row may assert today's uncontrolled outcome as contract** unless that
  decision is taken; the reviewer's temp test is correctly kept as scratch rather than promoted.
- **D-1 through D-6 stand unchanged.** D-6's condition (a third middleware needing the same
  recognition, or two needing to agree about one callback) is still unmet; R1b is neither.

**For the final gate**

- The operative failability manifest is **`docs/builder/temp-tests/r1b/proofs-pass2.json`, 9 entries**.
  Two earlier generations are on disk and must not be cited: this round's `proofs.json` (pass 1, 8
  entries — four of its anchors no longer match) and `docs/builder/temp-tests/r1/proofs-pass4.json` (R1's 15
  entries, the comparison generation). **R1b renumbered**: R1's entries 3, 4, 5, 6, 13, 12, 15 became
  1, 2, 3, 4, 5, 6, 7, the boundary probe is 8 and the read guard is 9. Independent records:
  `w3p2-rerun.md`, `w1-fv-rerun.md`, and `w3p2-entry6-absorbing*.{json,md,log}`.
- R1b's floor run (`tests/test_views.py`, 205 passed at Python 3.10.19 / django 5.2 /
  strawberry-graphql 0.316.0) and its hot-path numbers are in the pass-2 report and reproduce; both
  are re-recorded above from my own readings.
- The cycle's remaining doc obligations (V1-V7) are untouched by this round and stay R3's.

### Spec changes made (Worker 1 only)

**None.** R1b's write set names neither `docs/spec-046-transport_security-0_0_15.md` nor its
`-rationale.md`, and the plan assigns both to R2, whose authoring pass is the custodian's. Both files
are clean against `HEAD` at the end of this pass, and I re-verified the spec's opener and `Status:`
block against disk rather than editing them. Every spec and rationale item R1b surfaced is merged into
the hand-off above as R2's input rather than enacted here.

No `### Dispatched findings checklist` box is un-ticked, so no box owes a deferral reason. The one item
this pass leaves unresolved by choice is **D-7**, which is a maintainer contract call with a named home
and both paths recorded, and it does **not** drive the verdict — the verdict is driven by the two
documentary amendments, which are inside this round's own write set.

### Summary

R1b enacted two maintainer decisions in sequence and both landed correctly. **M-B**: recognition now
declines unless the callback's `view_class` itself carries a callable boundary method, probed on the
class before any construction, with the method's name joining the two ordering marks in
`_boundary_ordering.py` so the probe costs no import of `views.py` — proved by execution, not asserted.
**M-C**, escalated out of R1b's own review: the four recognition reads are guarded so a read that
cannot answer declines, while the construction keeps its narrow `except TypeError`. Three inputs that
left `process_view` uncaught before the guard now answer a controlled `None` on both interpreters, a
genuine mount is still recognized at both transports, and the argument that makes a broad `except`
defensible — that a package mount's own broken boundary stays loud — is confirmed in its strongest
available form: installed and uninstalled, the failure is *identical*.

The mechanical record is in good order and independently confirmed three ways. Nine failability
entries, node-id sets identical across Worker 2's, Worker 3's and my own runs, 0 collection/setup
errors, every baseline `205 passed`, every restore byte-proved, nothing in the 0-or-1 band, and the two
new boundaries at 6 and 5 rows. The floor run is the plan's full declared scope at the real floor. The
hot-path delta is below the metric's resolution and its elevated absolutes are the machine, checkably
so. The lint, layout, whitespace and ASCII gates pass, the tracked-path allowlist is byte-unchanged
without writing it, the public surface and the version quintet have not moved, `git diff --cached` is
still the single path `W-1` authorizes, and the tree is exactly as I found it.

What holds the round is one wording defect, twice over. The sentence the round exists to make true —
*"every outcome of the hook is a controlled response"* — is true of every outcome the **recognition**
decides and false for one outcome the **hook** produces, and the `TypeError` paragraph beside it
enumerates package inputs as though they were the complete set when a forged class reaches the same
arm. Both are measured, at the hook and at the wire, on both interpreters. Neither is a code defect:
closing them would put a guard across the body cap's own errors, which the same docstring correctly
keeps loud. But this is the third time inside one round that a docstring has promised a property the
code does not keep — M-B existed for it, M-C existed for it — and the sentence is the one R2 is about
to lift into Decision 18. Two clauses in a file already in this round's write set is the cheapest
correction available and there is no later home for it, so it does not defer.

### Final status

`revision-needed`.

Not for the code, which is right, complete and independently verified, and not for the record, which
reproduces everywhere I checked it. For **two documentary amendments** in
`django_strawberry_framework/middleware/request_body.py::_package_view_instance`, specified verbatim
under `### The one finding escalated to me` as amendments A and B: scope the absolute to the outcomes
the recognition decides and state the residual once as an invariant, and stop the `TypeError`
paragraph's enumeration reading as exhaustive over package inputs. No boundary moves, no test row is
owed, and none of the nine manifest anchors lies inside a docstring, so every row set above stays as
measured. I am read-only on source, which is why this is a status rather than an edit. The
Decision 18 hand-off wording that carried the same over-claim into R2 (*"That holds for any
callback"*) is corrected in this section as **R2-14**, which is the half that lives in the artifact
rather than in the spec and is therefore mine to fix in this round.

---

## Build report (Worker 2, pass 3)

`## Final verification (Worker 1)` set `revision-needed` for **two documentary amendments** in
`django_strawberry_framework/middleware/request_body.py::_package_view_instance` and for nothing
else: the code is right, the record reproduces, and no boundary moves. This pass lands exactly those
two amendments and touches nothing else. **No plan-level architectural call moved** — B-1 (the
constant's home and form), B-2 (the coupling pinned by rows), B-3 (the probe's shape and position)
and B-4 (the construction arm stays) are byte-for-byte as they were, so this is **not** the
structural-drift pause. I read amendments A and B at their source in that section rather than from
any restatement.

**Judged before it was enacted, not executed as an order.** I re-derived the two facts myself
against the shipped source before writing a word: `process_view`'s boundary call sits inside a `try`
whose only arm is `except HTTPException`, so a callable of the probed name that raises anything else
escapes the hook; and the construction arm is reachable by a forged class as well as by a package
one, because the probe consumes exactly one attribute and cannot tell the two apart — which is what
M-B decided it would and would not buy. Both amendments are therefore corrections to sentences, and
**the underlying behaviour must stay**: guarding the boundary call would sit across the body cap's
own errors and swallow them, and the same docstring correctly keeps a package mount's broken
boundary loud. I did not "fix" it in code and I record no structural pause, because my own reading
agrees with the two prior passes.

**Required reading walked, and the `BUILD.md` `## Required reading per worker` **W2** column walked
myself rather than taken from the dispatch.** Marked `yes` for W2 and read: `AGENTS.md`, `START.md`,
`docs/builder/BUILD.md` (in full, both pages), `docs/builder/ARTIFACT.md`, `docs/builder/worker-2.md`,
`docs/TREE.md` (in full), the active spec, the active build plan's whole `# Closeout cycle (card 046)`
section including `## Maintainer decision M-B`, `## Maintainer decision M-C`, `## Round R1b` and
`## Write-set correction W-1`, this artifact (the plan's B-1..B-4, both build reports, both reviews,
and the final-verification section end to end), and my own memory file, which was **consolidated
before appending** because it stood at the ~50-line cap. The dispatch omitted nothing. Marked `—` for
W2 and not read: `GOAL.md`, `docs/GLOSSARY.md`, `CHANGELOG.md`, `docs/README.md`,
`examples/fakeshop/test_query/README.md`. Marked **never**: the spec's `-rationale.md`, which I did
not open — the exclusion is absolute and my own docstring wording is derived from the artifact and
from source only. The other workers' memory files were not read.

One deliberate narrowing of a `yes`, stated rather than left as a gap: of the 3657-line active spec I
read **Decision 18 in full** (the decision this round's wording is about, and the one R2 will lift),
its `Status:` block and opener, and the structural outline of every other section. A wording pass
inside one function's docstring bears on Decision 18 and on nothing else in that file, and Worker 1's
own final verification recorded reading the spec the same selective way. Recorded so a reviewer can
disagree with the judgement rather than discover it.

### Files touched

Grounded in `git status --short` taken after the `ruff format` / `ruff check --fix` invocations, not
from memory:

```
AM django_strawberry_framework/_boundary_ordering.py
 M django_strawberry_framework/_request_body.py
 M django_strawberry_framework/middleware/request_body.py
 M django_strawberry_framework/views.py
 M docs/builder/build-046-transport_security-0_0_15.md
 M examples/fakeshop/apps/kanban/constants.py
 M tests/test_routers.py
 M tests/test_views.py
?? docs/builder/bld-046-r1-remediation_review.md
?? docs/builder/bld-046-r1b-recognition_contract.md
```

Character-for-character the list every prior pass of this round recorded: **no path added, none
removed, nothing newly staged.** `git diff --cached --name-status` is still exactly
`A django_strawberry_framework/_boundary_ordering.py`, the one path `## Write-set correction W-1`
authorizes; `git add` was run by no pass of mine, and nothing was reverted, stashed, checked out,
restored or worktree'd at any point.

Written by this pass — **one file, and only its docstring prose**:

- `django_strawberry_framework/middleware/request_body.py` — the two amendments inside
  `::_package_view_instance`'s docstring. Nothing else in the module changed: not a statement, not an
  expression, not a comment, not the import block, not `__all__`, not
  `::_require_boundary_before_csrf`, not `process_view`'s direct
  `view._enforce_request_boundary(request)` call (B-2).

**Unchanged and not written by this pass**, listed because a reader of the `git status` above will see
them dirty: `_boundary_ordering.py` (W-1's authorized staging plus pass 1's worktree copy),
`_request_body.py`, `views.py`, `consumers.py`, `tests/test_routers.py`,
`examples/fakeshop/apps/kanban/constants.py` and the build plan are R1's, Worker 0's, or an earlier
pass's landed uncommitted work. `tests/test_views.py` is pass 2's and this pass did not open it for
writing.

**`django_strawberry_framework/_boundary_ordering.py` and `tests/test_views.py` are in the round's
write set and this pass wrote neither, deliberately.** Neither amendment names a mark, a constant or
an assertion: A scopes a claim about the recognition's outcomes and B corrects an enumeration of what
reaches one arm, and both facts are already measured by entries 6, 8 and 9 and by the five permanent
rows pass 2 added. A test row asserting today's uncontrolled outcome must **not** be written — Worker
1 and Worker 3 both said so, and hand-off item **D-7** is the reason: it would freeze as contract an
outcome the maintainer has not chosen. So there is no work in either file, and if a later pass
disagrees the argument to beat is that one.

**SHA-256 before the first edit and after the last**, so the delta is confirmable rather than
asserted:

| File | before this pass | after this pass |
| --- | --- | --- |
| `django_strawberry_framework/middleware/request_body.py` | `5900fb367db8a944583474eae776051de357884b05b630f2e4ef38dc154044a8` | `eb77f024476165e87c851a3029f32452cbee3e0c9cae2d6ecec260ed9584762e` |

The "before" value is the one the pass-2 report, the pass-2 review **and** Worker 1's final
verification all recorded, so this pass started from exactly the bytes that were verified. Every one
of the other seven tracked files is byte-unmoved, read at the end of the pass and identical to
Worker 1's table: `_boundary_ordering.py` `7b3d9e51b7fb7ecc...`, `tests/test_views.py`
`abe0406a26fc9c15...`, `views.py` `e8aeb156550fc45a...`, `_request_body.py` `2c1fd48618d4b01c...`,
`consumers.py` `1bdf298c473fd1a0...`, `tests/test_routers.py` `5bf697bbe27b5d66...`,
`examples/fakeshop/apps/kanban/constants.py` `6761fadb49c4f285...`. `consumers.py` is also still
byte-identical to `HEAD` — `git show HEAD:django_strawberry_framework/consumers.py` into an
outside-the-repo scratch path, then `cmp`, exit **0** — the property six prior passes recorded.

### The two amendments, as shipped

Amendment **A**, the limit paragraph's final sentence. The absolute is scoped to what the
*recognition* decides, and the residual is then stated once, positively, as an invariant:

```django_strawberry_framework/middleware/request_body.py:248:256
    descriptor under the probed name, still runs that code. Forging the marker is
    outside the threat model either way, and the probe is here so that every
    outcome the recognition reaches is a controlled response - a refusal, a stamp,
    or a decline - not to defend against a forger. Running a boundary the
    recognition accepted is a different question: a boundary that raises anything
    but an ``HTTPException`` leaves ``process_view`` uncaught, deliberately and
    identically for a package mount and for a forged class carrying a callable of
    the probed name, because a guard there would sit across the body cap's own
    errors.
```

Amendment **B**, the `TypeError` paragraph. The enumeration stops reading as exhaustive over package
inputs, and the "hides no misconfiguration" argument is scoped to where it is load-bearing:

```django_strawberry_framework/middleware/request_body.py:275:282
    can run". With the probe ahead of it, what reaches it is a class carrying a
    callable of the probed name that cannot be built from the kwargs it names: a
    package class named with kwargs it rejects, a package subclass whose own
    ``__init__`` raises, and equally a forged class whose accepted ``__init__``
    raises ``TypeError``. It hides no misconfiguration of a *package* mount,
    because Django's own ``as_view`` closure constructs the same class with the
    same kwargs for the same request, so a mount that genuinely cannot be built
    still fails there - as it would with this middleware uninstalled.
```

Both facts Worker 1 required are present and neither is diluted:

- **A.1** — the absolute survives as an absolute, over the outcomes the recognition reaches, with the
  three named (`a refusal, a stamp, or a decline`). The point of the amendment is precision, so the
  scope is narrowed and the force is not: nothing hedges it, and the guarded-reads paragraph one
  paragraph down already says a callback whose reads raise is included.
- **A.2** — the residual is stated **once**, in the positive, as the invariant it currently is:
  `deliberately and identically for a package mount and for a forged class carrying a callable of the
  probed name`, with the reason (`a guard there would sit across the body cap's own errors`). It reads
  as a property of the design, never as a gap awaiting a fix.
- **B** — `a class carrying a callable of the probed name that cannot be built from the kwargs it
  names` is the arm's actual population, the three members follow it as instances rather than as a
  closed set (`and equally a forged class whose accepted __init__ raises TypeError`), and
  `It hides no misconfiguration of a *package* mount` replaces the old `either`, which had counted
  two members and now would be false over three.

**Worded to stay true under either resolution of D-7.** Neither sentence says the residual ought to be
closed and neither says it never will be; both describe the invariant that holds today and the cost
that keeps it. If the maintainer ever takes D-7's code path the sentences become the wrong description
and get rewritten by that round, which is the ordinary consequence of a contract change — not a
prejudgement written in now.

**Three sites deliberately not touched**, because Worker 1 decided them explicitly and a next pass
should not re-derive it: `::_package_view_instance` #"a hook whose every other outcome is a controlled
response", `tests/test_views.py::_marked_callback_without_a_view_class`'s docstring, and
`::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed`'s docstring all use the
`every other` form inside a counterfactual about a shorter recognition, which is local scoping rather
than an unqualified promise. Worker 1's ruling is all three or none; this pass changes none.

### Tests added or updated

**None, and none is owed.** Both amendments are docstring text: no boundary moved, no branch appeared,
no assertion changed meaning. Nothing in the repository asserts on this docstring —
`grep -rn '__doc__' tests/test_views.py` returns nothing, and the only occurrences of either amended
sentence anywhere outside the module are this artifact's own quotations of the prior wording, which
`ARTIFACT.md` forbids me to edit and which are correct as the historical record of what those passes
read.

A permanent row asserting today's uncontrolled outcome was considered and **rejected**, on Worker 1's
and Worker 3's shared reasoning: it would freeze as contract an outcome the maintainer has not chosen
(hand-off **D-7**). Worker 3's temp test stays scratch.

Totals, every one a `--no-cov` run, and every one reproducing the number three prior passes recorded:

| Scope | before this pass | after this pass |
| --- | --- | --- |
| `uv run pytest tests/test_views.py --no-cov` | **205 passed** | **205 passed** |
| `uv run pytest tests/test_views.py examples/fakeshop/test_query/test_transport_api.py tests/middleware/ --no-cov` | **291 passed** | **291 passed** |

The second scope is `worker-2.md` `## Apply-changes verification scope`'s obligation on a re-pass —
the file I fixed plus every test file that imports the changed surface. Measured rather than assumed:
`grep -rnE '^\s*(from|import).*(middleware\.request_body|_boundary_ordering)' tests examples` returns
**three lines, all in `tests/test_views.py`**, and a `grep -rln` for `_package_view_instance` or
`GraphQLRequestBodyBoundaryMiddleware` over `tests examples scripts` returns **that one file**. Both
were run as import statements rather than as occurrences, which is the trap an earlier pass of this
round hit in the over-counting direction. The live transport suite
(69 of the 291) exercises the module over the wire without importing it and `tests/middleware/` (17)
owns the middleware package directory, so both are in the scope even though neither imports the
symbol. No sibling app and no example project imports it at all.

**The test-staleness full sweep is not owed and I did not run it.** `BUILD.md`
`### Test staleness a focused run cannot see` scopes it to a changed example-model field set or a
converted wire shape; this pass changes neither, and the AST-minus-docstrings proof below establishes
that it changes no executable byte at all — which is a stronger statement than "no field and no wire
shape moved". Worker 1's own `uv run pytest tests/ --no-cov` reading of **4526 passed, 38 skipped**
therefore still describes the shipped bytes.

### Validation run

- `uv run ruff format django_strawberry_framework/middleware/request_body.py` — pass
  (`1 file left unchanged`). Scoped to this pass's own file, never `.`. Note that `ruff format` does
  **not** reflow docstring prose, so it cannot be what keeps the paragraph inside the line limit —
  see `### Implementation notes`.
- `uv run ruff check --fix django_strawberry_framework/middleware/request_body.py` — pass
  (`All checks passed!`); no fix applied.
- `git status --short` after both — quoted verbatim under `### Files touched`, and character-identical
  to every prior pass's. Nothing unexpected appeared, so there is nothing to stop-and-report and
  nothing was reverted.
- Line-length gate measured directly rather than inferred: `awk` over the whole file reports the
  longest line at **93 characters** (line 107, a pre-existing message literal) and **no** line above
  88 among the docstring paragraphs this pass rewrote. `line-length = 100`, E501 graced to 110.
- **`pre-commit` is not installed in this environment**, so its four `language: system` local hooks
  were run individually:
  - `kanban-tracked-path-constants` — `--check` exits **0**, and a regenerate to an
    outside-the-repo `--output` `cmp`s clean against the tracked copy, SHA-256
    `6761fadb49c4f285...` on both sides. **The baseline-dirty tracked file was not written**; the
    regenerate went to the scratch path. This round adds no tracked file, so the generated allowlist
    is byte-unchanged — the property that stops the maintainer's commit being rolled back.
  - `source-layout` — `uv run python scripts/check_trailing_commas.py --check`, exit **0** (ASCII-only,
    trailing-comma layout, markdown link scaffold). `docs/builder/` is excluded from the markdown
    link-scaffold check, so this artifact owes no link-definition block.
  - `ruff-format` and `ruff-check` read-only and repo-wide: `407 files already formatted`,
    `All checks passed!`.
  - ASCII-only re-verified independently of the hook by byte scan: **0** bytes above 127 in the
    changed file, highest byte **125**.
- `git diff --check` — exit **0** (no whitespace error, no conflict marker anywhere in the tree).
- `uv run python scripts/review_inspect.py django_strawberry_framework/middleware/request_body.py
  --output-dir docs/shadow` — re-run so the shadow overview describes the shipped bytes. Every
  executable reading is unchanged from the pass-2 review's: **8 branch nodes**, `getattr()` **4x**,
  `Django / ORM markers: None`, **`repeated string literals: 0`**. The only movements are the
  docstring's: the function spans **211-307** (was 211-299) and its docstring **212-292** (was
  212-284), so 81 docstring lines where there were 73, with the 16-line executable region unmoved by
  the same arithmetic the reviewer used. The four `getattr()` line numbers each shifted by exactly
  **+8**, which is the paragraph growth and nothing else.
- **Prose discipline swept mechanically over the diff's 20 added lines**: **0** hits for `feedback`,
  `bld-`, `pass N`, `round`, `Medium` / `High` / `Low`, `M-B`, `M-C`, `slice N`, `Test-N`, `R1b`,
  `review`, or a raw `:NN` reference. The added sentences name only runtime facts and one upstream
  exception type. Worker 1 measured 0 prose-discipline hits over 830 added lines for this round; that
  record is intact at 850.
- **No live mutation anywhere.** No `ACTIVE-MUTATION.json` and no `RESTORE-FAILED.json` exists under
  any scratch root, mine included, and this pass applied no mutation at all — the only proof runner
  invocation was `--check-anchors-only`, which takes no copy and writes no file into the tree.
- **Public surface**: `git status` shows `django_strawberry_framework/__init__.py` clean in both the
  worktree and the index; `__all__` in the changed module is still the single-name tuple, proved by
  the AST comparison below rather than by reading it.

### Failability proofs

**None; this pass introduced no new boundary** — it changed docstring prose in one function and
nothing else. What that claim needs is a measurement rather than an assurance, so it has two,
independent of each other:

**1. The executable bytes are unchanged, proved three ways at once.** A pre-pass copy of the file was
taken to an outside-the-repo scratch path **before the first edit** (SHA-256
`5900fb367db8a944...`, i.e. the verified bytes), and
`docs/builder/temp-tests/r1b/w2p3_docstring_only.py` — written this pass — answers three separate
questions about the pair:

```
1. AST-minus-docstrings identical: True
   dump length before/after: 10215 / 10215
2. comments identical: True (8 of them)
3. changed lines: 12 before / 20 after
   changed lines outside any docstring: none
   docstring owners of every changed line: ['_package_view_instance']
```

Every docstring expression is deleted from both trees and the remainder compared by `ast.dump`, so
equality means no statement, expression, name, constant, annotation or `__all__` member moved.
Comments are compared as their own token stream because they live outside the AST. And every differing
line of the diff is mapped onto a docstring span **by owner name**, so "the diff is docstring-shaped"
is a computed fact rather than a visual impression. `git` is not invoked by any of it.

**2. All nine manifest anchors still match exactly once, so every recorded row set stands.**
`uv run python scripts/prove_failability.py docs/builder/temp-tests/r1b/proofs-pass2.json
--check-anchors-only --scratch-root <outside the repo>` exits **0** with
`anchor matches exactly once` on **9 of 9**. That is the one reading that can tell its own reference
is already mutated, and it is what turns Worker 1's "none of the nine anchors lies inside a docstring,
so all nine still match after a docstring-only edit" from a prediction into a measurement taken
against the shipped bytes. Log: `docs/builder/temp-tests/r1b/w2p3-anchors.log`. No entry was run, no
copy taken and no mutation applied, so the record from the pass-2 report — entries at 4, 3, 13, 3, 7,
12, 2, 6, 5 rows, `0` collection/setup errors, every baseline `205 passed`, every restore
byte-proved — is undisturbed and needs no re-emission. The operative manifest is still
`proofs-pass2.json`, 9 entries.

Which is also why **no new manifest row is owed**: a row is owed for a new boundary, and this pass
adds none. Had I touched anything outside a docstring the manifest would have needed re-running; the
two proofs above are how I know I did not.

### Hot-path budget

**Unchanged by construction, and stated rather than re-measured — with the reason it is safe to
state.** The recognizer runs once per marked callback in `process_view`, so the round inherits R1's
hot-path declaration; but a function's docstring is a definition-time constant, bound once to
`__doc__` when the module executes, and it is never read, evaluated or copied on the call path. The
executable bytes are not merely equivalent, they are **identical**: proof 1 above shows the
docstring-stripped ASTs match exactly (`ast.dump` equal, 10215 characters both sides) and the comment
stream matches, so before and after differ in `__doc__`'s string constant alone. Re-running the
recorded A/B snippet could only re-measure machine noise around a delta that is provably zero, which
is what Worker 1's own reading of this round's numbers already showed (`-0.0089`, `-0.0021`,
`+0.0019` us per call, straddling zero on both interpreters).

The numbers that belong to this round therefore stand unamended in the pass-2 report and in Worker 1's
re-measurement of them. Nothing was weakened to buy a number back, and whether the round's cost is
acceptable remains the maintainer's call on those readings, not on a new one.

### Floor verification

The plan assigns this round's floor run to Worker 2's build pass and pass 2 performed it; a
docstring-only diff needs no fresh floor build. I nonetheless **re-ran the plan's full declared
scope** rather than reasoning about it, because it costs seconds — and I read the environment's
resolved versions before relying on it rather than restating any number from a document or from
memory.

Floor facts taken from `BUILD.md` `## Floor verification`, its single canonical statement: the
supported floor is **Django 5.2.0 on Python 3.10 with strawberry-graphql 0.316.0**.

- Scratch venv, outside the repository: `/tmp/dsf-floor`, already present.
- **Read, not recalled**: `/tmp/dsf-floor/bin/python -V` -> **Python 3.10.19**;
  `uv pip list --python /tmp/dsf-floor/bin/python` -> **django 5.2**, **strawberry-graphql 0.316.0**,
  asgiref 3.12.1, channels 4.3.2, cross-web 0.7.0, django-filter 26.1, djangorestframework 3.17.1,
  pytest 9.1.1, and **django-strawberry-framework 0.0.14** editable at this checkout, so it carries
  this pass's bytes. That is the floor as `BUILD.md` states it.
- `/tmp/dsf-floor/bin/python -m pytest tests/test_views.py --no-cov` -> **205 passed**, pytest exit
  **0**. The plan's whole declared scope, green, and the same total every prior pass measured.
  Log: `docs/builder/temp-tests/r1b/w2p3-floor-run.txt`.
- **The shared `.venv` was not mutated.** I ran no `uv pip install` at all; every floor command was
  `/tmp/dsf-floor/bin/python -m pytest` or carried an explicit `--python /tmp/dsf-floor/bin/python`.
  Read rather than recalled, for the contrast: `.venv` carries django **6.0.5**, strawberry-graphql
  **0.316.0**, channels **4.3.2** — far above the floor, which is why a green `.venv` sweep is not a
  floor result.

### Implementation notes

- **Where the wording came from.** Worker 1 offered a serviceable form and said the wording is
  Worker 2's while the facts are not. I took its form nearly verbatim for amendment A because it is
  already precise, and translated it into this file's conventions: em dashes to ` - ` (ASCII-only
  source), `` `HTTPException` `` to ``` ``HTTPException`` ``` and `process_view` to
  ``` ``process_view`` ``` — the plain double-backtick spelling this same docstring already uses for
  `process_view`, rather than the `:meth:` cross-reference role, which the surrounding paragraphs
  reserve for the class-qualified form. Amendment B's fact was given without a form, so the sentence
  is mine.
- **`what reaches it` in place of `what still reaches it`.** The old phrase and its `is a package
  class … and a package subclass` shape are what made the enumeration read as complete. Dropping
  `still` and leading with the population (`a class carrying a callable of the probed name that
  cannot be built from the kwargs it names`) makes the three members read as instances of a described
  set. `and equally a forged class …` then adds the third member in a form that cannot be read as
  closing the list.
- **`It hides no misconfiguration of a *package* mount` replaces `it hides no misconfiguration of
  either`.** `either` was a count of two, and would have become false the moment a third member
  joined. The emphasis marker matches the identical scoping already used one paragraph up
  (`It masks no misconfiguration of a *package* mount either`), so the two arguments now read as the
  same argument about the same population, which is what they are.
- **Re-wrapping is the whole risk in a docstring pass, and it bit once.** My first edit left one line
  at 100 characters and my first correction merely moved the overflow to the next line, because
  `ruff format` does not reflow docstring prose and cannot catch it. The fix was to re-wrap the
  affected paragraph in one edit at the file's own ~80-column rhythm and then **measure** with an
  `awk length` scan rather than trusting the formatter. Recorded because the same trap sits in front
  of any future prose amendment here.
- **What I did not add.** No hedge ("in general", "normally"), no severity vocabulary, no pointer to
  any artifact or round, and no new symbol reference. `AGENTS.md` #27's `path::QualifiedName`
  convention is satisfied by the references already in the paragraph
  (`views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once`), and neither amendment needed
  a new one.
- **Scratch artefacts kept beside the round's**, all gitignored:
  `docs/builder/temp-tests/r1b/w2p3_docstring_only.py` (the three-way proof script),
  `w2p3-anchors.log`, `w2p3-floor-run.txt`.

### Notes for Worker 3

- **The diff is two docstring hunks in one function.** The cheapest independent audit is to reproduce
  proof 1 — `git show HEAD:` is not the reference here (this file is dirty with R1's and this round's
  work), so use the pre-pass SHA `5900fb367db8a944…`: any copy of the file with my two hunks reversed
  must hash to it. `docs/builder/temp-tests/r1b/w2p3_docstring_only.py` takes two paths and prints all
  three readings; it invokes no `git` and writes nothing into the tree.
- **The claim most worth attacking is the wording, not the mechanics.** Specifically: does amendment
  A's absolute still assert something, or has it been hedged into vagueness? My answer is under
  `### The two amendments, as shipped` (A.1) and it rests on the enumeration `a refusal, a stamp, or a
  decline` doing the work the old `of the hook` was doing. And does amendment B's residual read as an
  invariant rather than as a gap? That is the property that keeps **D-7** unprejudged, and it is the
  one a reviewer should test by reading the paragraph cold.
- **Two things a re-run cannot tell you, so they are stated here.** No test asserts on this docstring
  (`__doc__` appears nowhere in `tests/test_views.py`), and the only other occurrences of the old
  sentences in the repository are this artifact's quotations in prior sections, which are correct as a
  record of what those passes read and which `ARTIFACT.md` forbids editing.
- **The failability record was not re-emitted and should not be expected.** Nine anchors matching
  exactly once after the edit is the evidence that the pass-2 record still describes the shipped
  bytes; re-running the nine entries would re-measure the same sets at a cost of nine mutations of
  three dirty files. If you distrust that, the cheap check is the anchors run, not the mutations.
- **`_boundary_ordering.py` and `tests/test_views.py` are byte-unmoved by choice, with the argument
  under `### Files touched`.** If you conclude a row is owed after all, note that both prior passes
  and Worker 1 explicitly forbade the one row this residual could carry (D-7).

### Notes for Worker 1 (spec reconciliation)

R1b writes no spec or rationale text and this pass adds no new item — everything below is either a
confirmation that your own hand-off survives untouched, or a single narrow observation.

1. **R2-14 stands exactly as you wrote it, and this pass does not restate it.** The Decision 18
   wording that reaches R2 is yours (`assert the absolute of the recognition … then state that
   running a boundary the recognition accepted surfaces that mount's own failure, package or forged,
   exactly as it would with this middleware uninstalled`). The shipped docstring is now the same fact
   in the module's own voice, so R2 can lift the wording without reconciling two versions of it. I
   deliberately wrote no second proposal.
2. **R2-16's two-sentences-kept-distinct instruction is now visible in the code**, which may make it
   easier to shape. The docstring keeps the threat-model sentence (`Forging the marker is outside the
   threat model either way`) and the purpose sentence (`the probe is here so that every outcome the
   recognition reaches is a controlled response`) adjacent but separate, and the residual is a third
   sentence rather than a qualifier on either. That is the shape R2-16 asks the rationale to carry.
3. **D-7 is unprejudged, deliberately.** Both amendments state the residual as the invariant it
   currently is and neither says it should be closed or that it never will be. If the maintainer takes
   the code path, the two sentences are the description that changes with it — no carve-out, no
   documented gap, nothing to retract.
4. **One observation, offered rather than filed.** The `TypeError` paragraph's population sentence is
   now the module's clearest statement of what the probe does and does not buy — a class carrying a
   callable of the probed name is as far as recognition can see. If R2 wants one sentence for
   Decision 18 about the probe's limit, that is the sentence to mirror, and mirroring it costs no new
   contract.
5. **Nothing else moved.** R2-1, R2-2, R2-3, R2-4, R2-5 through R2-13, R2-15, R3-1 through R3-7, M-A,
   D-1 through D-6 and the final-gate items are all exactly where your hand-off left them: no spec
   sentence, no glossary term, no terms-CSV row, no `examples/**` path, no generated file and no
   public symbol is touched by this pass.

### Dispatched findings checklist

**Nothing ticked this pass, and nothing should be.** The checklist predates both maintainer decisions
this round enacted, and its seven boxes were earned and ticked in pass 1 and audited as standing by
your own final verification. This pass un-earns none of them: it makes box 5's "the five over-claiming
sites rewritten" more precisely true by correcting the residual you found on site 1 and the sixth site
the round created, which `BUILD.md` `### Dispatched findings checklist` is explicit is not a box —
a maintainer decision the round escalated, and a final-verification amendment against it, are recorded
in the reports rather than in the list.
