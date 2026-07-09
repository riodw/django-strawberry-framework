# Spec-042 Implementation Review (adversarial pass)

## Scope

Reviewed the current on-disk Spec-042 implementation against
[`docs/SPECS/spec-042-debug_toolbar-0_0_14.md`][spec-042]: the production middleware, the GraphiQL
bridge template, the shared soft-dependency helper, the tests, and the Slice-2 doc wrap. Load-bearing
claims were verified against the installed `django-debug-toolbar` 7.0.0 and fakeshop settings, not
just by inspection.

The Python middleware is a faithful, well-documented port of the upstream borrow with three
deliberate, spec-tracked divergences (the two middleware robustness guards + the template hardening).
Its structure is sound and I found no reason to unwind `process_view`, `_postprocess`, or
`_get_payload`. The real issues are one correctness bug in the injected JavaScript and one
completion-state contradiction in the spec, plus smaller items.

## Bottom line

No P1. Two things to fix before treating the card as wrapped:

- **P2.1** — the bridge's null-DOM fallback skips the payload scrub, leaking the server-only
  `debugToolbar` key back into GraphiQL. This is the exact case the Revision-7 hardening was added to
  cover, so the guard is present but mis-ordered.
- **P2.2** — the spec simultaneously says `COMPLETE` and `Planned … WIP-ALPHA-042`, with every
  checklist box unchecked. The canonical design record contradicts itself.

Everything else is P3.

## P2 — fix before wrap

### P2.1 — the bridge leaks `debugToolbar` when the toolbar handle is absent

References:

- [debug_toolbar.html][template] line 12 `#"if (djDebug === null) return data;"`
- [debug_toolbar.html][template] line 38 `#"delete data.debugToolbar;"`
- [middleware/debug_toolbar.py][mw] lines 243-247 (`_postprocess` HTML append)

`update(data)` returns early on `djDebug === null` **before** it reaches `delete
data.debugToolbar`, so in that path the payload is handed back to the caller with the server-only
`debugToolbar` key still attached. Because `update` is installed as a global monkeypatch over
`JSON.parse` and `Response.prototype.json`, that leak applies to every JSON parse on the page while
GraphiQL is open — the blast radius is the whole IDE, not one panel.

This is reachable, and it is precisely the case the hardening claims to handle. `djDebug` is captured
once at script execution. It is non-null on a normally-rendered page (the stock handle is inserted
before `</body>`, ahead of the appended bridge). It is **null** when the stock handle was not
inserted — `is_processable_html_response` returned false (a `Content-Encoding` set upstream, or the
configured `INSERT_BEFORE` marker missing from a customized GraphiQL page) — yet the override still
appended the bridge, because its HTML branch is gated only on `is_html and is_graphiql and
status_code == 200` ([mw][mw]:243), never on whether the stock insert actually happened. In that
state the scrubber silently stops scrubbing.

Scrub first, then treat the DOM update as best-effort:

```javascript
const toolbar = data.debugToolbar;
delete data.debugToolbar;      // mandatory: the response contract
if (djDebug === null) return data;

// read toolbar.panels / toolbar.requestId below this point (DOM work is best-effort)
```

Spec-042's Revision 7 already frames the template as "the third documented divergence — tolerate a
missing handle while still acting as the scrubber." The fix makes the code match that stated intent.

### P2.2 — the spec says COMPLETE but still reads as an unstarted plan

References:

- [spec-042][spec-042] line 3 `#"Planned for \`0.0.14\` (card \`WIP-ALPHA-042-0.0.14\`)"`
- [spec-042][spec-042] line 54 `#"Status: **COMPLETE (card \`DONE-042-0.0.14\`)"`
- [spec-042][spec-042] lines 381, 497 (Slice 1 / Slice 2 headers)

The card is `DONE-042-0.0.14` in [KANBAN.md][kanban] and the spec Status line reads `COMPLETE`, but
the opening paragraph still says `Planned for 0.0.14 (card WIP-ALPHA-042-0.0.14)` and **all 35**
checklist items — the two slice blocks and the `D1`/`D2`/… decision-conformance boxes — remain
`- [ ]` (zero checked). That is internally contradictory in the document that is supposed to be the
satisfied design record, and it makes an audit read as "only partially implemented."

Reconcile it: update the opening line to the final card id/status and either tick the boxes that the
implementation and this review confirm, or mark the checklist explicitly as the historical plan of
record. (I would not silently delete it — the DoD tracking lives in KANBAN, but the spec's boxes are
useful provenance.)

## P3 — cleanups

### P3.1 — `simulated_absence` can strand a `None` sentinel (latent, shared helper)

References:

- [tests/_soft_dependency.py][helper] `simulated_absence` `#"sys.modules[sentinel_name] = None"`
- [tests/_soft_dependency.py][helper] `evicted_modules` `#"for name in list(sys.modules):"`

`simulated_absence` installs `sys.modules[sentinel_name] = None` but never tears it down itself. The
`None` entry is cleaned up only because `evicted_modules`' `finally` deletes keys matching
`prefixes`, and every current caller happens to also list `sentinel_name` inside `prefixes`
(`"debug_toolbar"`, `"rest_framework"`, `"channels"` appear in both positions). That coupling is
undocumented and invisible at the call site.

A future caller that passes a sentinel outside its prefixes — reasonable, since the sentinel is the
third-party top-level while the prefixes are the framework-owned modules to evict — would strand a
`None` entry in that worker's `sys.modules`, poisoning every later import of that name under
`--dist loadscope`. No live bug today, but this is now shared infrastructure whose whole point is to
be the one robust home for the dance. Make it own its teardown:

```python
with evicted_modules(*prefixes, parent=parent, attr=attr) as saved:
    sys.modules[sentinel_name] = None
    try:
        yield saved
    finally:
        if sys.modules.get(sentinel_name) is None:
            del sys.modules[sentinel_name]
```

### P3.2 — the per-panel DOM lookups are unguarded (upstream-parity, but inconsistent with the new posture)

Reference:

- [debug_toolbar.html][template] `#"const content = djDebug.querySelector"`

Inside the panel loop, `content = djDebug.querySelector('#' + id)` then `content.querySelector(...)`,
and the nav branch does `document.getElementById('djdt-' + id).querySelector(...)`. If a panel is in
the payload but its content/nav node is missing from the rendered DOM, these throw *inside* the
patched `JSON.parse` / `Response.json`, breaking the response path rather than skipping one panel.
This is verbatim upstream behavior and a payload/DOM mismatch is unlikely (both derive from the same
server-side `enabled_panels`), so it is lower severity than P2.1 — but once you have diverged to add
the null-handle guard, being defensive the rest of the way is consistent: `forEach` instead of `map`,
skip when `content === null`, update the nav subtitle only when the node exists. Do this only *after*
P2.1's scrub-first fix, so a skipped panel can never re-expose the payload.

### P3.3 — the middleware docstring's divergence count omits the template

Reference:

- [middleware/debug_toolbar.py][mw] `#"Two narrow, deliberate robustness divergences"` … `#"No other behavior differs."`

The module docstring enumerates "two … divergences … No other behavior differs," but Spec-042
Revision 7 and [Test 16][test] treat the template hardening as a third documented divergence. The
Python behavior claim is technically scoped to this module, but the middleware module is where a
reader looks for the divergence inventory, so note the template-side one too (e.g. "two Python-side
divergences; the injected template adds a third, defensive, template-side").

### P3.4 — `_get_payload`'s `json.loads` is unguarded, asymmetric with the P2.3 non-object bail

Reference:

- [middleware/debug_toolbar.py][mw] `_get_payload` `#"payload = json.loads(content"`

The P2.3 divergence guards a non-object decoded body (`if not isinstance(payload, dict): return
None`), but the `json.loads` above it is not itself wrapped — a non-JSON body would raise
`JSONDecodeError` out of `_postprocess`. Unreachable in practice (only tagged `application/json`
Strawberry responses reach here, and those are always valid JSON) and it matches upstream, so this is
a nit: if the intent of P2.3 was "never 500 on an odd body," malformed JSON is the same class of risk
and could fold into the same bail.

### P3.5 — the `fail_under = 100` gate is line coverage only

Reference:

- [pyproject.toml][pyproject] `#"[tool.coverage.run]"`

`branch` is not enabled, so "100%" is line coverage. In this unusually branch-dense module several
negative directions execute but are never asserted — the `"Content-Length" in response` false path on
both refresh blocks, the `status_code == 200` false path (a tagged non-200 HTML response), and the
`content_type != "application/json"` disjunct for a tagged non-HTML/non-JSON response. Not a defect;
flag only so the "100%" claim is read for what it guarantees. If branch coverage is ever enabled,
expect these first.

## Adversarial checks that held (verified non-findings)

- **The `INSTALLED_APPS` gate fires correctly.** With `"debug_toolbar"` importable but absent from
  `INSTALLED_APPS`, importing the leaf raises `ImproperlyConfigured` (message contains
  `INSTALLED_APPS`) at [mw][mw]:111, before the `debug_toolbar.middleware` import — so Test 11b holds
  in both worker states, keying on `apps.is_installed` rather than model-registration order.
  `debug_toolbar` 7.0.0 does define `HistoryEntry(models.Model)`, so the gate genuinely replaces the
  cryptic app-label `RuntimeError`.
- **Test 11a (broken install).** A `sys.modules["debug_toolbar.middleware"] = None` sentinel makes
  the statement-import raise a `ModuleNotFoundError` whose message contains `debug_toolbar.middleware`,
  carries no install hint, and has `__cause__ is None` — all three assertions hold.
- **Test 13 (streaming) cannot crash the stock pass.** `is_processable_html_response` checks
  `not getattr(response, "streaming", False)` first, so `super()._postprocess` never touches
  `.content` on a `StreamingHttpResponse`.
- **`_FakeToolbar` protocol is sufficient.** Every unit entering `_postprocess` (13, 15) uses the
  default `enabled_panels=()`, so the stock stats/headers loop is empty and never calls a method
  `_FakePanel` lacks; populated panels only ever reach `_get_payload` directly. Correct, but fragile —
  a future test handing populated panels to `_postprocess` would need `_FakePanel` to grow the stock
  methods.
- **Content-Length stays consistent** on both the HTML append and the JSON re-encode (guarded by
  `"Content-Length" in response`, recomputed from `len(response.content)`).

## Resolved since the previous review

Auditable delta — each was a prior finding, each is now addressed:

- Template `JSON.parse`/`hasOwnProperty` unsafety → fixed (arg-forwarding wrapper + null/prototype-safe
  membership test); [Test 16][test] pins it. (The ordering leak in **P2.1** is a *new*, narrower issue
  introduced by the null-handle guard, not the old one.)
- `evicted_modules` `__getattr__` footgun → fixed with a `missing` sentinel via `vars()`.
- Stale `require_drf()` "statement import" docstring → fixed; all three guards now document
  `require_optional_module`.
- `tests/_soft_dependency.py` untracked → now staged (`git status` shows `A`).
- Docs "planned / no slice built" → wrapped: [KANBAN.md][kanban] `DONE-042-0.0.14`, README/TREE/
  [GLOSSARY.md][glossary] bodies carry the implemented contract. The GLOSSARY status-table cell
  `planned for 0.0.14` is **not** stale — it is the joint-version-cut convention (the already-landed
  `DONE-041` entries show the identical cell), since the `0.0.14` release has not cut. (This is
  separate from **P2.2**, which is the spec *body's* self-contradiction.)
- `examples/fakeshop/db.sqlite3` dirty → **not** a Spec-042 side effect; do not revert as part of this
  card. The toolbar tests run under `@pytest.mark.django_db` against a separate in-memory database and
  never touch the tracked file; that diff is concurrent kanban work.

## Verification performed

- Read the current middleware, template, test module, shared helper, `require_optional_module`, the
  DRF/router refactors, `pyproject.toml`, and the wrapped docs. This review is against the on-disk tree
  (an earlier context snapshot was stale).
- `ruff check` on the changed package + test files — clean.
- Inspected installed `debug_toolbar` 7.0.0 (`middleware._postprocess`, `models.HistoryEntry`,
  `utils.is_processable_html_response`) for the stock contract the subclass and units rely on.
- Probed the leaf import under fakeshop settings with `"debug_toolbar"` absent from `INSTALLED_APPS`,
  confirming the `ImproperlyConfigured(...INSTALLED_APPS...)` raise at import time.
- Did **not** run pytest, per repo instruction. The behavioral tests (1–8) drive real `/graphql/`
  traffic and read plausible but are unverified here; run `pytest tests/middleware/test_debug_toolbar.py`
  for a second gate before the joint cut.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: ../KANBAN.md
[pyproject]: ../pyproject.toml

<!-- docs/ -->
[glossary]: GLOSSARY.md
[tree]: TREE.md

<!-- docs/SPECS/ -->
[spec-042]: SPECS/spec-042-debug_toolbar-0_0_14.md

<!-- django_strawberry_framework/ -->
[mw]: ../django_strawberry_framework/middleware/debug_toolbar.py
[template]: ../django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html
[imports]: ../django_strawberry_framework/utils/imports.py

<!-- tests/ -->
[test]: ../tests/middleware/test_debug_toolbar.py
[helper]: ../tests/_soft_dependency.py

<!-- examples/ -->
[db]: ../examples/fakeshop/db.sqlite3
