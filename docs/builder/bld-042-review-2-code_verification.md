# Build: Cohort B — independent code verification (spec-042 debug toolbar)

Spec reference: `docs/SPECS/spec-042-debug_toolbar-0_0_14.md`
Status: revision-needed

## Plan (Worker 1)

Cohort B carries no Worker 1 planning pass: the maintainer's dispatch and
`docs/builder/build-042-debug_toolbar-0_0_14.md` `## Verified finding list` are
the plan. The checklist below is copied from that plan's
`### Cohort B verification questions (V1–V4)`, per `BUILD.md` `## Review rounds`
`### Dispatched findings checklist`.

### Dispatched findings checklist

- [x] **V1 — nothing in the spec's contract was skipped.** Walk the
      `## Definition of done`, the `## Slice checklist`, the `## Test plan`
      (Tests 1–16 incl. 11a, 11b, 14a) and the `## Helper-reuse obligations
      (DRY)` ledger (D1–D4, D-N1–D-N3) against the shipped tree, and report
      every item with no landed counterpart. Worker 0's pre-read found none,
      which is exactly the claim that needs an independent reader.
- [x] **V2 — the three post-ship Python/template hardenings (F7, F8) are
      correct and pinned.** Are the guards written against the *answer* rather
      than one spelling of the bad input (`BUILD.md` `### Fail-open shapes`)?
      Is each pinned by more than one test row (`### Acceptance rule: weakly
      pinned is revision-needed`)?
- [x] **V3 — fail-open shapes in the shipped module.** The `except Exception`
      around `json.loads(request.body)` in `_postprocess` is upstream-verbatim
      and spec-sanctioned as deliberate degradation; confirm that reading and
      check every other clamp / `getattr` default / `or` fallback / truthiness
      test in the module.
- [x] **V4 — the live/package test split holds the coverage contract.** Every
      branch named in the spec's coverage paragraph has a landed owner in one
      tier or the other, and no branch lost its owner when Revision 9 moved the
      present-path tests live.

Every box is walked; V2 is walked and **fails** (M1, M2, M3 below).

### The rationale companion did not exist during this pass

`docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md` is Cohort A's
deliverable and was **not** read (it is being authored concurrently; reading a
half-written file is worse than not reading it). Its absence is already tracked
as F1 and is not raised here. `BUILD.md` `## Spec rationale extraction` makes
the rationale the record the finished implementation is checked against, so in
its place this pass checked the implementation against the spec's own inline
`## Revision history` (Revisions 1–9), which still carries that deliberation,
plus the four post-ship commit messages, which carry the deliberation for
everything the spec never absorbed.

---

## Review (Worker 3)

Diff under review: `6f7335a4`, `d5c3c635`, `d2a9690c`, `312d4121`, `5a74d803`,
`6fa696af`, `9c868016`, `ac69acf5` — restricted to the spec-042 surface. Every
in-scope path is **clean at HEAD** (`git status --short` over the middleware,
the template, both test tiers, `tests/_soft_dependency.py`, the fakeshop
wiring, `utils/imports.py`, `pyproject.toml`, `uv.lock` prints nothing), so no
`git show HEAD:` extraction was needed and none of the 53 baseline-dirty paths
was read as build output.

Static helper: run as required (`BUILD.md` `### When to run the helper during
build` — the reviewed commits add a new `.py` file). Command:
`uv run python scripts/review_inspect.py
django_strawberry_framework/middleware/debug_toolbar.py --output-dir
docs/shadow`, exit 0. **Django / ORM markers: `None`** — no entry to justify.
**Control-flow hotspots:** `_get_payload` (48 lines / 9 branch nodes) and
`_postprocess` (66 lines / 12 branch nodes); both read below at Medium-tier
attention. **Imports:** one first-party cross-folder import
(`django_strawberry_framework.utils.imports`), which is the documented D1
direction (leaf → shared primitive), not a boundary violation; the `debug_toolbar`
/ `strawberry` / `django` imports all sit deliberately below the guard with
`# noqa: E402`. **Repeated string literals:** see `### DRY findings`. No skip
was taken; the template asset is not Python and the helper was not run on it.

### Mutations recorded BEFORE they were made

`worker-3.md` "Scope" requires the carve-out's mutations to be recorded before
they are applied. This cycle has **no Worker 2 build report and therefore no
recorded row counts**, so the mandatory re-run floor (`worker-3.md` "Reading is
necessary, not sufficient") was applied to **every** post-ship boundary rather
than to a subset; nothing here is accepted on a builder's record, because there
is none.

| # | Boundary | Mutation applied |
| --- | --- | --- |
| 1 | `django_strawberry_framework/middleware/debug_toolbar.py::DebugToolbarMiddleware._postprocess` #"if response.get("Content-Encoding", "")" | the two-line guard + `return response` deleted |
| 2 | `django_strawberry_framework/middleware/debug_toolbar.py::_get_payload` #"except (json.JSONDecodeError, LookupError, UnicodeError):" | `try`/`except` dropped, leaving the bare decode + parse |
| 3 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` #"function getDjDebug()" | body collapsed to the pre-`312d4121` light-DOM-only `return document.getElementById("djDebug");` |
| 4 | `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` #"const panelTitle = content.querySelector(".djDebugPanelTitle");" | pre-`ac69acf5` chained, unguarded `content.querySelector(...).querySelector("h3").textContent = panel.title;` restored |

Manifest: `docs/builder/temp-tests/042/proofs.json`; full emitted report:
`docs/builder/temp-tests/042/proofs-report.md`. Scratch root is **outside** the
repository. All four anchors were asserted to match exactly once
(`--check-anchors-only`) before any mutation, which is also what proves the tree
was not already carrying a foreign live mutation. Both mutated files are clean
in `git status --short` after the run, and the scratch directory holds no
`ACTIVE-MUTATION.json`.

### Failability proofs (Worker 3 independent re-run)

Scope, identical for all four:
`uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0
tests/middleware/test_debug_toolbar.py
examples/fakeshop/test_query/test_debug_toolbar_api.py`.
Pre-mutation state of that scope, measured before each mutation: **27 passed,
exit 0** — green, so no pre-existing failing row is inflating any count.
Collection/setup errors: **0** in every run, so every count below is a valid
count.

| # | Boundary | Rows | Failing node ids | Verdict |
| --- | --- | --- | --- | --- |
| 1 | `…debug_toolbar.py::DebugToolbarMiddleware._postprocess` (Content-Encoding bail, `9c868016`) | **1** | `tests/middleware/test_debug_toolbar.py::test_encoded_response_gets_no_package_mutation[graphiql_html_append]` | **WEAKLY PINNED** |
| 2 | `…debug_toolbar.py::_get_payload` (decode/parse bail, `6fa696af`) | **2** | `…::test_malformed_json_body_gets_no_package_rewrite[not json]`, `…::test_malformed_json_body_gets_no_package_rewrite[\xff]` | accepted |
| 3 | `…/debug_toolbar.html` #"function getDjDebug()" (shadow DOM, `312d4121`) | **1** | `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence` | **WEAKLY PINNED** |
| 4 | `…/debug_toolbar.html` #"const panelTitle = content.querySelector" (per-node null guards, `ac69acf5`) | **1** | `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence` | **WEAKLY PINNED** |

Restores, each proved by byte comparison inside the same pass:
`filecmp.cmp(shallow=False) True` plus SHA-256 equality against the pre-mutation
copy — `fc03452179dc4777…` for the Python module (entries 1–2) and
`c7348fdbe876b6a0…` for the template (entries 3–4). Every entry restored before
the next mutation.

No entry returned zero rows, so no `why 0` judgement is owed.

### High:

None.

### Medium:

#### M1 — the `Content-Encoding` bail is weakly pinned, and its second parametrize row is non-distinguishing

`django_strawberry_framework/middleware/debug_toolbar.py::DebugToolbarMiddleware._postprocess`
#"if response.get("Content-Encoding", "")" (`9c868016`).

Removing the guard fails **one** row —
`tests/middleware/test_debug_toolbar.py::test_encoded_response_gets_no_package_mutation[graphiql_html_append]`.
`BUILD.md` `### Acceptance rule: weakly pinned is revision-needed` makes one row
not accepted.

The reason it is one row and not two is the interesting half. The test carries
two parametrize ids and its docstring claims "An already-encoded body reaches
**BOTH** mutation sites and is written by neither" — but the
`[operation_json_injection]` row's body is `b"\x1f\x8bencoded-json"`, which is
not decodable as UTF-8, so `_get_payload`'s own decode bail (the *other* post-ship
boundary, `6fa696af`) returns `None` and the response is left alone whether or
not the encoding guard exists. The row proves the decode bail a second time; it
proves nothing about the encoding guard. Demonstrated, not inferred:
`docs/builder/temp-tests/042/test_encoded_json_row_is_nondistinguishing.py`
(2 passed) shows `_get_payload(...)` returns `None` for exactly that body and
returns an injected payload for `b'{"data": 1}'`.

**Contract that must hold** (not a prescription of lines): with the
`Content-Encoding` early return removed, the JSON re-encode site and the HTML
append site must **each** produce at least one failing node id at this scope —
i.e. the encoded-JSON row's body must be one the injection path would otherwise
accept (decodable, a JSON object), so that "the guard is what stopped the
rewrite" is what the row measures. Both sites together must leave the boundary
at two or more rows.

#### M2 — both post-ship template boundaries rest on a single test node id

`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
#"function getDjDebug()" (`312d4121`) and #"const panelTitle =
content.querySelector(".djDebugPanelTitle");" (`ac69acf5`).

Every invariant of the asset — the five ported ones and all four documented
divergence families — is asserted inside one test,
`tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence`.
A single node id cannot fail more than once, so removing *any* template boundary
scores exactly 1 row, and removing all of them still scores 1. That is the same
structural blindness `BUILD.md` names for a `for` loop inside one test: widening
the assertion list never raises the failability count. Measured: entries 3 and 4
above, both `1`.

**Contract that must hold:** each independently-removable guard family in the
asset must be separately failable — removing one must fail at least two node ids
without touching the rows that belong to the others. The natural shape is a
parametrized table of (invariant name, predicate over the asset text) so the
failing-row count tracks the number of dropped guards; the fix is more or
better-targeted rows, never a weakened assertion set. See also the escalation in
`### Notes for Worker 1` about what a substring table can and cannot prove.

#### M3 — `update()` guards the shape of `data` but not the shape of `data.debugToolbar`, so a malformed payload throws out of the patched global `JSON.parse`

`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
#"Object.entries(toolbar.panels).forEach(".

The Revision 7/8 divergence family states the rule the asset is written to:
**payload scrubbing is mandatory and DOM updates are best-effort**, because the
hook is a *global* patch and "a dev-only tool that patches a global must neither
corrupt nor crash unrelated page code". The entry guard implements that for
`data`: `data === null`, `typeof data !== "object"`, and
`Object.prototype.hasOwnProperty.call(data, "debugToolbar")`. It implements
nothing for the *value* under that key:

```django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html:30
      const toolbar = data.debugToolbar;
      delete data.debugToolbar;

      if (djDebug === null) return data;

      Object.entries(toolbar.panels).forEach(([id, panel]) => {
```

A `debugToolbar` value that is `null`, a string, or an object without `panels`
makes `Object.entries(toolbar.panels)` throw a `TypeError` — after the scrub, so
the key is gone, but the exception propagates out of `update`, out of the patched
`JSON.parse` / `Response.prototype.json`, and breaks the caller's parse. That is
precisely the outcome `ac69acf5` and Revision 8 say the family prevents, reached
by a different door. It is the `BUILD.md` `### Fail-open shapes` shape in its
mirror form: the guard enumerates spellings of a bad `data` rather than answering
"is this a usable `debugToolbar` payload?".

Exposure is dev-only and needs a foreign `debugToolbar` key, which is why this is
Medium and not High — but the module already hardens against
`Object.create(null)` and `hasOwnProperty`-shadowing, inputs at least as exotic,
so the omission is inconsistent with its own stated rule rather than a deliberate
scope line.

**Contract that must hold:** `update` returns the scrubbed `data` for *any*
`debugToolbar` value it cannot use, and never throws out of the patched globals.
Pin it with a row that survives the parametrized split M2 asks for.

#### M4 — the "three places that must agree" comment names a population of three; there are five

`django_strawberry_framework/middleware/debug_toolbar.py`
#"place 2 of the three-places-that-must-agree: place 1 is the".

The comment (and the matching `_HINT_SUBSTRING` comment in
`tests/middleware/test_debug_toolbar.py`) tells a future floor bump that the
floor is written in exactly three places: the `[dependency-groups].dev`
specifier, `_DEBUG_TOOLBAR_INSTALL_HINT`, and the re-typed test literal.
Measured with the shortest distinctive token across the tree, excluding
`uv.lock`, `docs/shadow/`, `docs/SPECS/` and this cycle's own artifacts,
`django-debug-toolbar>=7.0.0` occurs at **five** live sites: those three plus
`docs/GLOSSARY.md` (the Debug-toolbar middleware entry body) and
`docs/README.md` #"Install `django-debug-toolbar>=7.0.0`". Nothing compares any
of the five against the others.

This is graded Medium rather than Low because the comment is not decoration: it
is the *instruction* a floor bump follows, and following it leaves two shipped
documents stating a floor the package no longer declares. `START.md`'s "rule
without gate rots" applies — the root-cause fix is a gate, not a re-count.

**Contract that must hold:** the comment states the true population, or the
package stops enumerating it and points at whatever compares the sites. The two
doc sites are outside this cycle's maintainer-set fence (spec files + package
`.py` only), so only the comment is in-scope here; the doc half is routed to
Worker 1 below.

### Low:

#### L1 — the one statement in the asset without a terminating semicolon

`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
#"const origJson = Response.prototype.json". Every other statement in the IIFE
is terminated; this one relies on automatic semicolon insertion. It is safe
(the next line begins a new statement that cannot continue the expression), but
in an asset whose whole test story is "a future edit must not silently change
behavior", a lone ASI dependency is a hazard for the next editor.

#### L2 — `if (panel.subtitle)` never clears a subtitle that became empty

`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
#"if (panel.subtitle) {". A truthiness test on a value that can be legitimately
empty: a panel whose `nav_subtitle` goes from `"3 queries"` to `""` keeps the
stale text in the nav. Upstream-verbatim and cosmetic; recorded so it is not
re-discovered as a defect, **no change recommended** — changing it would diverge
from the borrow for no dev-visible gain.

### DRY findings

- **Repeated literal `Content-Length` (4x)** — the two-line refresh block
  (`if "Content-Length" in response: response["Content-Length"] =
  len(response.content)`) appears twice in
  `…::DebugToolbarMiddleware._postprocess`, once per mutation path. Considered
  and **not** flagged for consolidation: it is upstream-verbatim, the two sites
  refresh after different mutations, and a two-line helper would cost more
  readability than it saves while diverging the borrow. Recorded so the next
  reviewer does not re-derive it.
- **Repeated literal `debugToolbar` (3x)** — the wire key, spelled identically
  in the module, the asset, and both test tiers. It is a protocol constant
  shared with upstream and with GraphiQL; naming it in Python would not reach
  the JavaScript or the tests, so a constant buys nothing. No action.
- **`tests/_soft_dependency.py` is the shared absence helper D3 said not to
  build in this card** — and that is correct, not a violation: D3 deferred the
  extraction to "a dedicated cleanup card" and required it to support **both**
  the block shape and the sentinel shape. The landed helper supports both
  (`evicted_modules` for broken-install composition, `simulated_absence` for the
  `None` sentinel), carries the two-sided restore through `vars(parent)` with a
  `missing` sentinel, and is used by all three soft-dependency suites. The
  toolbar copy has not drifted from the two-sided-restore discipline.
- **No existence challenge raised.** `require_debug_toolbar()` has one
  production caller and its return value is discarded there, which is the shape
  that usually earns a challenge — but it is the third instance of a deliberate
  package-wide convention (`require_drf`, `require_channels`), it is the named
  D1 contract, and its single-sited hint string is the thing the convention
  exists to hold. Deleting it and inlining `require_optional_module(...)` would
  save two lines and break the convention's only visible seam. Not a challenge.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` — empty. `__all__` and
the re-export list are unchanged, and
`tests/middleware/test_debug_toolbar.py::test_package_and_middleware_imports_stay_clean_without_toolbar`
independently pins that `from django_strawberry_framework import *` binds no
`DebugToolbarMiddleware` name. The spec's soft-dependency DoD item requires
exactly that: no new public export.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (This
cohort is review-only and wrote no source, docs, or release metadata. The
`docs/README.md` and `docs/GLOSSARY.md` observations in M4 and in
`### Notes for Worker 1` are read-only findings, not edits.)

### V1 — was anything in the spec's contract skipped?

Walked independently, not confirmed off Worker 0's pre-read. The finding is
that **every behavioral contract landed**, and the only unlanded items are the
spec's own stale text (Cohort A's F3/F6) plus the two named below.

`## Test plan` Tests 1–16, mapped to a landed owner:

| Spec test | Landed owner | Notes |
| --- | --- | --- |
| 1 GraphiQL HTML, both injections | live `…test_debug_toolbar_api.py::TestToolbarPresent::test_graphiql_page_carries_stock_handle_and_bridge_script` | asserts `id="djDebug"` *and* the package marker |
| 2 no-toolbar baseline | live `::test_no_toolbar_baseline_under_shipped_settings` | re-based on `DEBUG=False` inertness, which is the correct re-statement after Revision 9 wired fakeshop |
| 3 named JSON operation | live `::test_named_json_operation_gets_panel_payload` | `SQLPanel` subtitle non-null, `TemplatesPanel` absent, `data` intact — the asserted properties, not just the symbol |
| 4 introspection skip | live `::test_introspection_query_is_skipped` | |
| 5 JSON-`Accept` GET | live `::test_get_with_json_accept_hits_the_operation_name_except_branch` | content type asserted before the body, as the spec requires |
| 6 panel-route round trip | live `::test_injected_request_id_round_trips_to_stored_sql_panel_content` | fallback string absent **and** `products_item` present — both directions |
| 7 HTML detection negatives | live `::test_non_strawberry_html_views_pass_through[/]` and `[/login/]` | package-scoped negative, as specified |
| 8 JSON leak guard | package `tests/middleware/test_debug_toolbar.py::test_unrelated_json_view_body_is_never_mutated` | recast as a `RequestFactory` unit; see the caveat below |
| 9 import surface | package `::test_package_and_middleware_imports_stay_clean_without_toolbar` | |
| 10 hinted `ImportError` | package `::test_leaf_import_raises_install_hint_when_toolbar_absent` | `__cause__` chained, re-typed literal |
| 11 two-sided restore | package `::test_leaf_reimports_after_restore` | asserts `parent.debug_toolbar is leaf` |
| 11a broken install | package `::test_broken_toolbar_install_propagates_raw_import_error` | raw error, hint absent, `__cause__ is None` |
| 11b missing `INSTALLED_APPS` | package `::test_leaf_import_requires_debug_toolbar_in_installed_apps` | |
| 12 guard unit | package `::test_require_debug_toolbar_guard_unit` | |
| 13 streaming early-out | package `::test_streaming_response_gets_no_package_mutation` | |
| 14 `_get_payload` bails | package `::test_get_payload_bails_without_request_id`, `::test_get_payload_panel_title_only_when_has_content`, `::test_get_payload_bails_on_non_object_json_body` | all three sibling cases landed |
| 14a non-class `view_class` | package `::test_process_view_tolerates_non_class_view_class` | |
| 15 `Content-Length` refreshes | package `::test_html_content_length_refresh_branch`, `::test_json_content_length_refresh_branch` | |
| 16 template port | package `::test_template_port_invariants_and_robustness_divergence` | landed as a superset of the spec's five invariants — see M2 for why one node id is not enough |

`## Definition of done`: every item with a code counterpart holds. The module,
the guard, the template asset and its `render_to_string` render, the
replace-the-stock-entry wiring, the view-scoped injection statement, the soft
dependency matrix, `BaseView` detection, the introspection skip, the
`>=7.0.0` dev-group pin with `uv.lock` regenerated (`uv.lock` carries
`django-debug-toolbar` `7.1.1` resolved against `specifier = ">=7.0.0"`), and
the no-version-bump rule are all satisfied in the tree. Two DoD items have no
landed counterpart and **both are spec text, not code** — the `ROOT_URLCONF =
"tests.middleware.debug_toolbar_urls"` clause (that module was deleted by
Revision 9; the live tier uses fakeshop's real `config.urls`) and the
`strawberry-graphql==0.262.0` throwaway-venv gate (the declared floor is now
`0.316.0`). Both are Cohort A's F3 and F6; neither is re-raised here as a code
defect.

`## Helper-reuse obligations (DRY)`: **D1** holds — `require_debug_toolbar()` is
a thin `require_optional_module` wrapper and no fourth import pattern exists.
**D2** holds, with M4's caveat about the enumeration. **D3** holds (see
`### DRY findings`). **D4** holds — no memoization, no class cache; the class is
a plain module global, so `sys.modules` eviction fully resets the module.
**D-N1** holds — the subclass overrides exactly `process_view` and
`_postprocess`, chains `super()._postprocess(...)` first, and re-implements no
panel, request-id, handle-render or history logic. **D-N2** holds — the module
never touches `request_from_info`; it operates on the raw `HttpRequest` /
`HttpResponse` pair. **D-N3** holds — the `operationName` sniff is local and
upstream-shaped.

One V1 caveat worth the next reader's attention, graded Low because the claim
still composes: the spec's Test 8 exists because "an implementation that injected
`debugToolbar` into *every* JSON response would still pass Tests 1–7", and its
answer was a live non-Strawberry JSON probe view. That view died with
`tests/middleware/debug_toolbar_urls.py`. The landed replacement hand-plants
`request._is_graphiql = False` and drives `_postprocess` directly, so the
composite claim is now proved by two halves that never meet: that `process_view`
computes `False` for a real non-`BaseView` class is pinned by the live `/login/`
row (an erroneous `True` there would fire the HTML append and put the template
marker in the body), and that `_postprocess` injects nothing when the flag is
`False` is pinned by the unit. The halves do compose; no code change is needed.
Routed to Worker 1 because the spec still describes the live probe.

### V3 — fail-open shapes, module and asset

The `except Exception` around `json.loads(request.body)` is **confirmed against
the code** and confirmed as deliberate, not accepted on the spec's word. Reading
it: the answer it converts is "which operation is this?", and "cannot tell"
becomes "not `IntrospectionQuery`", i.e. inject. Two facts make this a
degradation rather than a fail-open defect. First, the decision behind it is
cosmetic — the introspection skip exists so IDEs that poll introspection do not
evict older toolbar history (Decision 8), not to enforce a limit or a permission.
Second, the degradation is **load-bearing for a supported path**: the live
JSON-`Accept` GET row (`::test_get_with_json_accept_hits_the_operation_name_except_branch`)
reaches the injection *through* this except, because a GET has an empty body.
Making it fail closed would silently stop instrumenting every GET query. The
`RawPostDataException` case the spec names for multipart uploads lands in the
same arm with the same result.

Every other suspect shape in the module resolves **fail-closed**, checked one by
one: `response.get("Content-Type", "")` → `""` → neither HTML nor
`application/json` → passthrough; `getattr(request, "_is_graphiql", False)` →
no injection; `getattr(view_func, "view_class", None)` → `isinstance(None, type)`
is `False` → untagged; `if not toolbar.request_id` → `None`; the
`(json.JSONDecodeError, LookupError, UnicodeError)` catch → `None` → no
injection; `if not isinstance(payload, dict)` → `None`.
`response.get("Content-Encoding", "")` defaulting to `""` is correct rather than
fail-open: an absent header genuinely means "not encoded", and the truthiness
test is behaviourally identical to stock's `content_encoding == ""` in
`debug_toolbar/utils.py::is_processable_html_response`, which is also the
verification of the comment's claim that "the stock postprocess refuses encoded
bodies" — read, not assumed.
No clamp (`max`/`min`) and no `or` fallback exists anywhere in the module.

In the asset, the one fail-open shape is M3. `if (rootEl !== null &&
rootEl.shadowRoot)` is a correct truthiness test (an unattached shadow root is
genuinely absent), and `if (panel.title)` is the spec's own protocol — `null`
title means "do not touch this panel's content area".

### V4 — does the live/package split still hold the coverage contract?

Answered by reading the diff against the spec's coverage paragraph, with no
coverage tooling run (`BUILD.md` `## Coverage is the maintainer's gate`).
`pyproject.toml` `[tool.coverage.run]` declares `source` only and **not**
`branch`, so the contract is statement coverage; each statement below has a
named owner in one tier or the other, and **no branch lost its owner in the
Revision 9 move**:

- guard success path → every present-path row; guard raise path → package Tests
  10/12; `apps.is_installed` raise → package Test 11b; raw broken-install
  propagation → package Test 11a.
- `_postprocess` streaming early-out → package Test 13.
- `_postprocess` HTML append → live Test 1; its `Content-Length` refresh →
  package Test 15 (HTML).
- `_postprocess` non-GraphiQL / non-JSON early return → live Test 7 (HTML arm)
  and package `::test_unrelated_json_view_body_is_never_mutated`
  (`not is_graphiql` arm).
- `operationName` except arm → live Test 5; introspection skip → live Test 4.
- `_postprocess` JSON re-encode → live Test 3; its `Content-Length` refresh →
  package Test 15 (JSON).
- `payload is None` early return → package
  `::test_malformed_json_body_gets_no_package_rewrite`.
- `_get_payload` no-`request_id`, `has_content`-false, `TemplatesPanel` skip,
  callable title/subtitle, non-object bail, decode/parse bail → package Test 14
  family plus the malformed-body rows; the `has_content`-true and
  `TemplatesPanel`-skip paths additionally ride live Test 3.
- `process_view`: non-class → package Test 14a; class-and-`BaseView` → live
  Tests 1/3/5/6 through the real
  `ensure_csrf_cookie(DjangoGraphQLView.as_view(...))` mount; class-and-not-`BaseView`
  → live Test 7's `/login/` row.

Two statements the spec's coverage paragraph does not name because they post-date
it — the `Content-Encoding` early return and the `_get_payload` decode/parse
bail — do have landed owners (M1, entry 2 above); their *strength* is M1's
finding, not their existence. That gap in the paragraph is Cohort A's F7.

### What looks solid

- **The detection target resolves for the package's own view, verified
  independently.** `django_strawberry_framework/views.py::DjangoGraphQLView`
  subclasses `strawberry.django.views.GraphQLView`, which subclasses `BaseView`;
  executed rather than reasoned:
  `issubclass(DjangoGraphQLView, BaseView)` → `True`,
  `issubclass(AsyncDjangoGraphQLView, BaseView)` → `True`, and
  `DjangoGraphQLView.as_view().view_class` is the class itself, so the
  `functools.wraps`-copied attribute survives `ensure_csrf_cookie`.
  `examples/fakeshop/config/urls.py` mounts that view, so live Tests 1/3/5/6 are
  the positive-detection proof running through the package's own view class. The
  spec's Risks hedge ("if a future card ships a package view class, the one
  `issubclass` line is that card's to update") resolved to **no update needed**.
- **The shadow-DOM fix is correct, including its timing.** The one-shot
  `const djDebug = getDjDebug()` at IIFE evaluation would be a defect if the
  shadow root were attached by the toolbar's own JavaScript — the toolbar's
  `toolbar.js` is `type="module" async`, so it has not run when the appended
  bridge script executes. It is not: debug-toolbar 7.1.1's
  `debug_toolbar/templates/debug_toolbar/base.html` uses **declarative** shadow
  DOM (`<template shadowrootmode="open">`), which the HTML parser attaches while
  parsing, before any script runs. `USE_SHADOW_DOM: True` is confirmed as the
  7.1.1 default in `debug_toolbar/settings.py`, and `getDjDebug()` mirrors stock
  `debug_toolbar/static/debug_toolbar/js/utils.js::getDebugElement` exactly,
  including the light-DOM fallback. The nav-lookup move to
  `djDebug.querySelector(\`#djdt-${id}\`)` matches stock's own
  `djDebug.querySelector(\`#djdt-${panelId}\`)`, and the panel ids the payload
  carries are the ids `debug_toolbar/templates/debug_toolbar/includes/panel_content.html`
  renders, so `#${id}` resolves in whichever tree the toolbar lives in.
- **The scrub-before-bail ordering is real and pinned in the right direction.**
  The asset captures and deletes `debugToolbar` before `if (djDebug === null)
  return data;`, and the test asserts the ordering by index comparison rather
  than by presence — one of the few assertions in that file that could catch a
  reordering.
- **The guard chain reads correctly end to end.** Top-level import guard →
  `apps.is_installed` wiring gate → the `# noqa: E402` statement imports, in that
  order, with the leaf module import as the opt-in boundary. The `toolbar_leaf`
  fixture makes the first `debug_toolbar.middleware` import in a process happen
  with the app installed, which is what keeps these rows order-independent under
  `--dist loadscope` — a real hazard handled, not a theoretical one.
- **The live tier tests the real gate rather than bypassing it.** The fixture
  sets `DEBUG=True` *and* an always-true `SHOW_TOOLBAR_CALLBACK`, and saves /
  clears / restores `show_toolbar_func_or_path` and
  `DebugToolbar._panel_classes` / `_urlpatterns` — the leak the spec's Decision 9
  hygiene contract names, closed.
- **Test 6 pins the load-bearing property, not observability.** It asserts the
  miss-fallback string is absent *and* a seeded-operation SQL marker is present,
  so a broken store round-trip fails instead of passing on shape.

### Temp test verification

- `docs/builder/temp-tests/042/test_encoded_json_row_is_nondistinguishing.py` —
  two rows, both pass, demonstrating that the `[operation_json_injection]`
  parametrize case cannot distinguish the `Content-Encoding` guard (M1).
- `docs/builder/temp-tests/042/proofs.json` and `proofs-report.md` — the
  failability manifest and the tool's emitted report.
- **Disposition:** all three are scratch and stay under `temp-tests/`. The
  probe's *content* is not promoted as-is; what M1 asks for is a corrected
  parametrize row inside the existing permanent test, which is Worker 2's to
  land. No temp test here caught a production bug on its own — M3 is the only
  production-code finding and was found by reading.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (contract-level): the asset has no executing test of any kind.**
  Every template assertion is a substring check over the file's text, so the
  suite can prove the guards are *written* and can never prove they *work* —
  and three of the four documented divergence families exist specifically to
  survive runtime inputs (null-prototype objects, absent DOM nodes, a shadow
  root). M2's parametrized split raises the failability count and is the
  in-scope fix, but it does not change what is being proved. Whether this
  package should carry a JavaScript runtime for one 89-line asset is a
  contract-level call, not a worker's (`BUILD.md` `### Contract-level findings`).
  Resolution paths: (a) accept text-identity pinning permanently and say so in
  the spec, so the next reviewer does not re-raise it; (b) add a minimal DOM
  harness for this asset alone; (c) narrow the asset so less of it needs
  guarding. This pass does **not** hold the cohort at `revision-needed` for this
  item — M1/M2/M3 are what do.
- **M4's doc half is outside this cycle's fence.** `docs/GLOSSARY.md` and
  `docs/README.md` both name `django-debug-toolbar>=7.0.0`, and the maintainer
  fenced this cycle to spec files and package `.py`. Worker 1 should decide
  whether the spec records the true site population (five) and whether a gate is
  owed, and route the doc edits to a card.
- **The spec's Test 8 still describes a live JSON probe view that no longer
  exists** (`tests/middleware/debug_toolbar_urls.py`, deleted by Revision 9).
  Cohort A's F3 already covers the file's nine naming sites; this adds *why* the
  Test 8 text specifically needs rewriting rather than just deleting the file
  name — its stated rationale ("an implementation injecting into every JSON
  response would still pass Tests 1–7") is still true and still discharged, but
  by a `RequestFactory` unit composed with a live HTML negative, not by a live
  probe. The replacement's weaker shape should be the recorded contract.
- **The spec's coverage paragraph predates two branches.** The
  `Content-Encoding` early return and `_get_payload`'s decode/parse bail both
  have owners (V4 above), but the paragraph names neither, and the divergence
  ledger still says "two narrow divergences" / "No other Python behavior
  differs". Cohort A's F7; recorded here with the owner names so the
  reconciliation does not have to re-derive them.
- **Hot-path declaration `none`: agreed, with one clarification for the record.**
  This cycle changes no code, so `none` is trivially right for the cycle. The
  *shipped* middleware does sit on a per-request path — `process_view` runs for
  every request the toolbar processes and `_postprocess` for every response —
  but the stock `show_toolbar` gate returns `False` whenever `DEBUG` is false, so
  the cost is dev-only by construction and the package adds one attribute write
  per request over the stock middleware it replaces. No number is owed.
- **Floor-verification scope `none`: agreed, and the F6 question answered.** The
  only Strawberry touchpoint in the module is `from strawberry.django.views
  import BaseView`. `pyproject.toml` declares `strawberry-graphql>=0.316.0` and
  `django_strawberry_framework/utils/imports.py::STRAWBERRY_FLOOR` carries the
  same `0.316.0`, and `BaseView` resolves in the shared environment (read:
  `uv pip list` → `strawberry-graphql 0.324.0`, `django 6.1`,
  `django-debug-toolbar 7.1.1`). **No code behavior depends on whether the floor
  is `0.262.0` or `0.316.0`** — the import either resolves or the module fails at
  import time, and it resolves at the declared floor's successor. F6 is therefore
  purely a spec-text correction, exactly as the plan assumed; nothing in the
  module needs a floor run to discharge it.

### Review outcome

`revision-needed`.

Three of the four post-ship boundaries are weakly pinned at one failing row each
(M1, M2 ×2), which `BUILD.md` `### Acceptance rule: weakly pinned is
revision-needed` does not permit as a recorded exception, and one of them (M1)
additionally carries a parametrize row whose docstring claims a coverage it
demonstrably does not have. M3 is a real residual hole in the very guard family
the post-ship commits were extending. M4 mis-states a population a future floor
bump will follow.

Nothing here says the shipped behavior is wrong: the guards are correct, the
detection target resolves, the coverage contract survived the Revision 9 move
intact, and the fail-open audit found exactly one degradation, which is
deliberate and load-bearing. What is missing is that the suite could not tell
you if three of these guards disappeared — and that is the claim a review has to
make mechanically or not at all.

For a Worker 2 pass the contracts to satisfy are stated in M1, M2, M3 and M4;
each states the property that must hold, not the lines to type.
