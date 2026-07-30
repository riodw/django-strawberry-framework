# Build: Slice 3 — S9: one UTF-8 wire contract

Spec reference: `docs/spec-046-transport_security-0_0_15.md` — Slice 3 checklist lines 159-170;
Decision 9 (lines 1016-1073), Decision 10 (1075-1098), Decision 13's "Inverted" paragraph
(1277-1282) and Placement (1284-1294); User-facing API — Consumer-visible behavior's non-UTF-8
bullet (597-598) and Error shapes' non-UTF-8 bullet (636-638); Helper-reuse obligations' UTF-8
bullet (1408-1410); Edge cases' GET/bodyless bullet (1465-1467); Test plan S9 rows 19-24
(1548-1556); Implementation plan row 3 (1367) and the sequencing note (1371-1376); Definition of
done lines 1721-1725.
Status: final-accepted

## Plan (Worker 1)

### Static inspection record

Run this pass, per `BUILD.md` #"When to run the helper during build" (both files carry logic this
slice touches and `_strawberry_patches.py` is well past 150 source lines):

- `uv run python scripts/review_inspect.py django_strawberry_framework/_strawberry_patches.py --output-dir docs/shadow`
  -> `docs/shadow/django_strawberry_framework___strawberry_patches.overview.md` (+ `.stripped.py`).
  6 imports, 5 symbols, **0 Django/ORM markers**, 0 TODOs, 3 control-flow hotspots
  (`_validate_upstream_shape` 61 lines / 9 branches; `_patched_parse_json` 47 / 5;
  `_patched_parse_query_params` 42 / 4), calls of interest `isinstance` x3 / `tuple` x2 / `len` x2 /
  `dict` x1, repeated literals `variables` x3, `extensions` x3, `parse_json` x2,
  `parse_query_params` x2 (all four are upstream key/method names, not package literals — no
  constant is justified).
- `uv run python scripts/review_inspect.py django_strawberry_framework/_cross_web_patches.py --output-dir docs/shadow`
  -> the sibling pair. `_patched_body` is a one-statement function; the slice adds **no logic**
  there, only docstring text.

**Shadow line numbers are NOT canonical** (`BUILD.md` #"Shadow-file line numbers are NOT
canonical"). Every source reference below uses `path::QualifiedName` or
`path #"unique substring"`.

### DRY analysis

- **Utils inventory checked.** `docs/shadow/utils-inventory.md` refreshed this pass with the
  `worker-1.md` AST script (14 modules). Searched for decode / encode / bytes / utf / json
  candidates. The only hits are input-coercion helpers on the **GraphQL argument** side —
  `utils/inputs.py::decode_scalar_leaf`, `::decode_visible_relation`, `::decode_provided_fields`
  (mutation input routing) and `utils/errors.py::unencodable_text_error` (rejects a *string* that
  cannot be encoded for model storage, i.e. an unpaired surrogate). None of them touches request
  bytes, an HTTP body, or a wire encoding. A repo-wide grep for
  `decode("utf`/`.decode()`/`UnicodeDecodeError`/`errors="strict"` across
  `django_strawberry_framework/` returns hits **only** in the two patch modules this slice edits.
  Conclusion: **no existing transport-decoding utility exists and none is created.**

- **Existing patterns reused.**
  - `django_strawberry_framework/_strawberry_patches.py::_patched_parse_json`'s existing
    `try: ... except UnicodeDecodeError as exc: raise HTTPException(400, "Unable to parse request
    body as JSON") from exc` — the strict decode goes **inside that same `try`**, so the slice adds
    zero new `except` clauses, zero new message literals, and zero new status codes. This is
    exactly the Helper-reuse obligation at spec lines 1408-1410 ("reusing its existing
    `UnicodeDecodeError` -> `HTTPException(400, ...)` translation and its existing
    `_validate_upstream_shape` gate. No new patch module, no second patched method").
  - `_strawberry_patches.py::_patched_parse_query_params` — the GET shield already routes its two
    nested parses through the captured `_original_parse_json`, so the new decode is automatically
    off the GET path with **no change to the shield**. Decision 9 lines 1022-1024 depend on this and
    it already holds.
  - `_strawberry_patches.py::_validate_upstream_shape` — its own docstring fixes the rule
    "delegators pin the call shape, reimplementers pin the body". `parse_json` stays a delegator, so
    the existing `(self, data)` arity pin is still the correct and complete depth. **No new
    validation is added** (see Design resolution 4).
  - `examples/fakeshop/test_query/test_transport_api.py`'s Slice-1 probe scaffolding — the
    `urlpatterns` list, the `/async-graphql/` mount (`::_async_graphql_view`), `AsyncClient`, and
    `override_settings(ROOT_URLCONF=__name__)`, plus the sibling row
    `::test_the_async_package_view_runs_inside_djangos_middleware_chain` as the exact template. The
    async colour of the wire contract reuses all of it and adds **no new mount and no new helper**.
  - `examples/fakeshop/graphql_client.py::post_graphql_raw` — the documented raw-envelope exemption
    the three inverted live tests already use. Unchanged; the new live rows use it too.

- **New helpers justified.** **None.** The production change is one `isinstance` guard and one
  `.decode("utf-8")` call inside an existing `try`. Extracting a helper for two tokens would be
  strictly worse: it would add an indirection whose only caller is the site it came from, and it
  would split the "enforced once, in `_patched_parse_json`" claim (Decision 9's title) across two
  symbols. The condition that would later justify extraction: a **second** enforcement site
  appearing — which Decision 9's "Why the decode belongs in the patch module rather than in the new
  view" paragraph (spec lines 1050-1056) forbids by name.

- **Duplication risk avoided.**
  1. **A second decode site.** The naive implementations are "decode in `views.py`" and "decode in
     `_patched_body`". Both are rejected by name in Decision 9 (lines 1050-1056 and 1066-1067). The
     plan keeps a single decode site and requires the docstrings to say why, so a future reader does
     not "helpfully" add the second one.
  2. **A bespoke encoding sniffer.** Decision 9's second rejected alternative (lines 1068-1070).
     `bytes.decode("utf-8")` is the whole contract; no BOM/NUL pattern check is written.
  3. **A duplicated async mount.** Putting the async parity row in `test_products_api.py` would
     require copying `test_transport_api.py`'s probe URLconf + async view factory into a second live
     module. The row goes where the scaffolding already lives instead.
  4. **A package-tier restatement of the live status matrix.** The package matrix and the live rows
     must not both be "these bytes -> 400". The package matrix's distinguishing subject is
     **which mechanism rejected** (`__cause__` is `UnicodeDecodeError` for the strict decode vs
     `json.JSONDecodeError` for the decodable-but-not-JSON shapes) — the executable form of Decision
     9's "Measured behavior" table and of Decision 10 reason (a). The live rows' subject is that the
     whole Django + view + adapter stack really answers `400` over the wire. Different subjects, not
     a copied assertion. Stated here so Worker 3 can check the distinction rather than read it as a
     duplicated matrix.
  5. **No new message literal.** `"Unable to parse request body as JSON"` already exists once in
     the package and is reused by the existing `raise`. Note that it is *also* upstream's own
     message for `json.JSONDecodeError` (verified: `BaseView.parse_json`'s body), so it must not be
     duplicated into a test as a discriminator either — see Verified fact 2.

### Verified facts (executed or source-read this pass, not remembered)

1. **The measured behavior table is exactly right, and no new rejection branch is needed.** Ran
   strict-decode-then-`json.loads` over ten byte shapes on the installed stack:

   | body | strict `decode("utf-8")` | `json.loads(str)` | outcome |
   |---|---|---|---|
   | plain UTF-8 | ok | ok -> `dict` | **200** |
   | `encode("utf-16")` (BOM) | **UnicodeDecodeError** (invalid start byte) | — | `400` at the decode |
   | `encode("utf-16-le")` | ok | **JSONDecodeError** | `400` at `json.loads` |
   | `encode("utf-16-be")` | ok | **JSONDecodeError** | `400` at `json.loads` |
   | `encode("utf-32")` (BOM) | **UnicodeDecodeError** | — | `400` at the decode |
   | `encode("utf-32-le")` | ok | **JSONDecodeError** | `400` at `json.loads` |
   | `encode("utf-32-be")` | ok | **JSONDecodeError** | `400` at `json.loads` |
   | UTF-8 BOM (`EF BB BF` + JSON) | ok | **JSONDecodeError** ("Unexpected UTF-8 BOM") | `400` at `json.loads` |
   | invalid UTF-8 byte inside JSON | **UnicodeDecodeError** | — | `400` at the decode |
   | raw binary (`bytes(range(256))*4`) | **UnicodeDecodeError** | — | `400` at the decode |

   Both halves of the spec's claim hold: every non-UTF-8 form reaches a `400` through an
   **already-existing** path, so **Decision 10 costs zero production code** — the BOM needs no
   branch, no `utf-8-sig`, no `lstrip`. Decision 10 is therefore a *test* obligation in this slice,
   not a code one. (Decision 9's own enumeration at lines 1058-1061 omits UTF-16-BE, UTF-32-BE, and
   UTF-32-with-BOM; the three omitted shapes behave as their siblings do — see
   spec-reconciliation note 2.)

2. **Upstream's `JSONDecodeError` message is byte-identical to the package's.**
   `strawberry.http.base.BaseView.parse_json` is
   `try: return self.decode_json(data) except json.JSONDecodeError as e: raise HTTPException(400,
   "Unable to parse request body as JSON") from e`, and `BaseView.decode_json` is
   `json.loads(data)`. Consequence for test design: **no test can attribute the rejection by
   message or status** — both mechanisms produce `HTTPException(400, "Unable to parse request body
   as JSON")`. Attribution must be structural (which callable saw what) or via `__cause__`. This is
   why Test-plan row 24 gets a package-tier proof rather than a live message assertion.

3. **Both transports reach `parse_json` with `bytes` for the JSON body.** Read the installed
   sources: sync `SyncBaseHTTPView.parse_http_body` does `data = self.parse_json(request.body)`
   (the `cross_web` adapter property this package patches to return raw bytes); async
   `AsyncBaseHTTPView` does `data = self.parse_json(await request.get_body())` (upstream's async
   adapter already returns raw bytes, unpatched). The multipart `operations` / `map` parses are
   `str` on sync (`request.post_data.get(...)`), and the GET parses are `str` (Django already
   decoded the query string). So the `isinstance(data, bytes)` guard hits exactly the two body
   sites and passes every `str` site through — which is Decision 9's stated shape.

4. **The async transport's behavior genuinely changes in this slice, and nothing pins it today.**
   A repo-wide grep for `utf-16` / `utf-32` / `BOM` across `tests/`, `examples/`, `README.md`,
   `TODAY.md`, `docs/README.md`, `docs/GLOSSARY.md`, and `examples/fakeshop/test_query/README.md`
   finds hits in exactly two test files and the two patch modules; **no async row exists for any of
   these encodings**, and `test_products_api.py` has no async test and no probe URLconf. Before this
   slice, async accepted UTF-16/32 (raw bytes -> `json.loads` RFC 8259 auto-detection); after it,
   async rejects them. An un-pinned async colour would be an unproven behavior change, so the plan
   requires one.

5. **Slice 2's `parse_json` spy does not collide.**
   `examples/fakeshop/test_query/test_transport_api.py::_ParseSpyView.parse_json` appends the
   received `data` to `_PARSE_CALLS` and delegates through `super().parse_json(data)`, which resolves
   up the MRO to the patched `BaseView.parse_json`. The spy therefore records the **pre-decode**
   value (still `bytes`), and its row-15 control asserts
   `under_name.encode() in bytes(_PARSE_CALLS[0])` — a `bytes` membership check that keeps working
   unchanged. Slice 3 changes nothing the spy observes. Row 15 stays green and needs no edit.

6. **The existing envelope guards still behave.** `tests/test_strawberry_patches.py`'s
   `::test_patched_parse_json_rejects_non_object_body_as_400` and
   `::test_patched_parse_json_rejects_batch_with_non_object_elements_as_400` pass `str` bodies, so
   the new `isinstance(data, bytes)` guard is a no-op for them and the parsed-shape checks after
   the delegation are untouched. `tests/test_apps.py`'s three-patch dispatch test only swaps
   attributes and is unaffected.

7. **Installed versions used for every measurement above:** `strawberry-graphql` 0.316.0,
   `cross-web` 0.7.0, Django 6.0.5.

8. **No staged anchors to discharge.** `grep -rEn 'TODO\(spec-046|TODO-ALPHA-046'` over the tree
   (excluding `KANBAN*`/`BACKLOG.md`/`docs/builder/`/the DB) matches only the spec's own prose at
   line 1378. No Slice-3 source anchor was pre-placed.

9. **`docs/TREE.md` renders each module's FIRST docstring line.** `_cross_web_patches.py`,
   `_strawberry_patches.py`, and `tests/test_cross_web_patches.py` all appear there. Their current
   first lines stay accurate under the new contract, so keeping them byte-identical means this slice
   owes TREE.md nothing (Slice 5 owns the regenerate).

10. **`docs/GLOSSARY.md` says nothing about these encodings.** Its only patch-related entry is the
    Django `_remove_databases_failures` one. Nothing to route to Slice 5 from this slice's
    behavior change.

### Design resolutions

**1. Where the decode goes.** As the first statement inside `_patched_parse_json`'s existing `try`,
before the delegation:

```
    try:
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        parsed = _original_parse_json(self, data)
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "Unable to parse request body as JSON") from exc
```

This is the maximally DRY shape: the existing translation is reused verbatim, the existing `except`
becomes the decode's handler, and `str` inputs skip the branch. After the change,
`_original_parse_json` can no longer raise `UnicodeDecodeError` (it only ever sees `str`), so the
`except` is reached exclusively by our own decode — the same 400, from a scope that can translate
it, which is the whole point of Decision 9.

**2. Decision 10 needs no new branch — plan tests, not code.** Verified fact 1 proves a BOM'd body
decodes cleanly and is rejected by upstream's own `json.loads`. Writing any BOM-specific branch
would contradict Decision 10's reason (a) ("rejection needs zero extra code and no lenient branch
whose behavior could drift") and Decision 9's "no new rejection branch to write or cover". **Worker
2 must not add one.** What Decision 10 does buy is a *pinning* obligation: because the rejection is
inherited from `json.loads`, a future stdlib that tolerated a leading U+FEFF would silently turn a
`400` into a `200`. The package matrix therefore asserts the BOM row's `__cause__` is
`json.JSONDecodeError`, so the inherited mechanism is pinned rather than assumed.

**3. `APPLY_UPSTREAM_PATCHES` — resolved from the spec; the gate stays shared.** The spec is **not**
silent: Decision 9 lines 1037-1042 state that both patches "keep their shared
`APPLY_UPSTREAM_PATCHES` gate. A consumer who disables the Strawberry patch therefore opts out of
the strict wire contract along with the malformed-body hardening the pair already jointly owns; the
docs state that consequence rather than splitting the gate." So: **yes, the UTF-8 contract is
unenforced when a consumer sets `{"strawberry": False}` (or `False`), and that is the accepted,
authorized outcome.** Enforcement does **not** move — moving it into `views.py` is rejected by name
at spec lines 1050-1056 (it would miss non-adopters of the package view, miss the async parse path
unless duplicated, and split one contract across two modules).

The four gate cells, worked out so the docstrings can state them accurately:

| `cross_web` | `strawberry` | sync, non-UTF-8 body | async, non-UTF-8 body |
|---|---|---|---|
| on | on | **`400`** for every shape (the shipped contract) | **`400`** for every shape |
| on | off | undecodable -> unhandled `500`; UTF-16/32 **succeeds** (RFC 8259 auto-detection) | same |
| off | on | undecodable -> `500` (upstream's decode raises inside the property, before `parse_json`); UTF-16/32 and the BOM still `400` | unaffected: `400` (the async adapter is not patched) |
| off | off | today's upstream: `500` / silent success | `500` / silent success |

Two things follow, and both are plan requirements rather than notes:

- The opt-out consequence must be stated on **both** module docstrings' existing
  `APPLY_UPSTREAM_PATCHES` paragraphs, which today mention only the malformed-body half of the
  pair's joint ownership. A consumer reading the gate documentation must learn that the wire
  contract travels with it.
- The **retirement** semantics of `_strawberry_patches.py` change, and this is the most consequential
  documentation obligation in the slice. Today the module documents itself as a fix for two upstream
  bugs, retirable when upstream lands them. After S9 it also carries a **package policy** that
  upstream will never "fix": deleting the module once upstream widens its `except` would silently
  restore RFC 8259 auto-detection and re-open the parser differential S9 exists to close. The
  module docstring must therefore distinguish three lifecycles — gap 1 (upstream bug, retirable),
  gap 2 + the GET shield (upstream bug #3398, retirable together), and the strict UTF-8 wire
  contract (**package policy, not retirable with either**).

**4. `_validate_upstream_shape` gains nothing.** Its docstring fixes the delegator-vs-reimplementer
rule: `parse_json` is wrapped and delegated to, so only presence + `(self, data)` arity are pinned,
and upstream body changes flow through the delegated call. That is still exactly true after the
change — we hand the delegate a `str` instead of `bytes`, which is inside its declared
`str | bytes` annotation. Adding a body pin for `parse_json` would contradict the module's own
stated rule and couple us to an upstream body we deliberately do not supersede. **No change.**

**5. Sync/async parity is proven in three layers, not asserted.**
- *Structural (one install site).* A new package test asserts `DjangoGraphQLView.parse_json` and
  `AsyncDjangoGraphQLView.parse_json` both resolve, through their MROs, to
  `_strawberry_patches._patched_parse_json`. This closes the real regression channel: an
  intermediate class (a future upstream `GraphQLView.parse_json`, or a package override in
  `views.py`) shadowing the patched method on one transport only.
- *Behavioral, sync.* The inverted live rows in `test_products_api.py` run over fakeshop's real
  `/graphql/`, which Slice 1 pointed at the sync `DjangoGraphQLView`.
- *Behavioral, async.* A new live row drives `AsyncClient` against `test_transport_api.py`'s
  existing `/async-graphql/` mount. This is the **stronger** colour: the async adapter is *not*
  patched by `_cross_web_patches`, so a `400` there can only come from the wrapper's strict decode —
  the async row is simultaneously the parity proof (row 23) and an independent attribution proof
  (row 24).

**6. Test placement.** Live-first (`AGENTS.md` #"Test through real usage") is satisfied: every
production line this slice adds is executed by the live rows, on both transports. The package-tier
rows exist for the two things a live request cannot report — *which* callable received *what*
(row 24's attribution) and *which* mechanism raised (`__cause__`). No package test here is a
stand-in for an unreachable live line, so nothing is retired under the
"retire the package-only stand-in" rule; the `tests/test_cross_web_patches.py` raw-bytes rows in
particular stay, because a live `400` cannot tell you whether the adapter returned `bytes` or a
`str`.

### Implementation steps

Line anchors below are pin-at-write-time navigational hints; verify against the current source
before editing (`BUILD.md` Implementation steps note). All source references are symbol-qualified.

**Production — `django_strawberry_framework/_strawberry_patches.py`**

1. `::_patched_parse_json` — insert the strict decode as the first statement inside the existing
   `try`, exactly as shown in Design resolution 1. Constraints: no new `except`; no new module-level
   constant for `"utf-8"` (single use); no new message literal; do not touch the `isinstance(parsed,
   dict)` / `isinstance(parsed, list)` envelope checks that follow the delegation.
2. `::_patched_parse_json`'s docstring — restate the hardenings so the decode is item 1's subject
   rather than a side effect. It must say: (a) `bytes` are decoded with strict UTF-8 **here, once**,
   before delegating, and a failure reuses the existing `HTTPException(400, ...)` translation;
   (b) a `str` input is passed through untouched (the GET query-param path Django already decoded,
   and the multipart `operations` / `map` form fields); (c) the consequence — `json.loads`'s RFC 8259
   encoding auto-detection can no longer run, so UTF-16 / UTF-32 (BOM or BOM-less) and a UTF-8 BOM
   are no longer accepted (cite Decision 9 and, for the BOM specifically, Decision 10); (d) the BOM
   and the BOM-less multi-byte encodings are rejected with **no dedicated branch** — they decode and
   then upstream's own `json.loads` rejects them; (e) why the decode lives here and not in the
   adapter property — a raise inside a property escapes `parse_json`'s `except` and surfaces as an
   unhandled `500`; (f) the one-site claim: both views inherit the single `BaseView.parse_json`, so
   one install covers sync and async.
3. Module docstring — four edits, no change to the **first line** (Verified fact 9):
   - the `APPLY_UPSTREAM_PATCHES` paragraph at
     `_strawberry_patches.py #"note the companion ``cross_web`` patch routes the sync transport's bytes into"`
     — widen the stated consequence to include the strict UTF-8 wire contract (Design resolution 3).
   - the `The bug` section's sync bullet
     (`#"On the **sync** view the decode happens in ``cross_web``'s request"`) — it now describes only
     upstream's behavior; add that the package's own strict decode happens in this module for
     **both** transports, and that the `cross_web` patch's job is to stop the adapter decoding
     inside a property.
   - add a short wire-contract passage carrying the measured table's shape (which forms fail at the
     decode vs at `json.loads`) and the "no new rejection branch" statement.
   - `Upstream status` / `Re-checking whether upstream fixed this` — re-derive the recipe. With the
     patches off, `test_post_invalid_utf8_json_body_returns_400_not_500` /
     `::test_post_raw_binary_body_returns_400_not_500` remain the gap-1 discriminators (`500` means
     still needed). The UTF-16/32/BOM rows are **not** upstream probes any more — with the patch off
     a UTF-16 body *succeeds*, which is upstream behavior, not a fix — so the recipe must stop
     implying they diagnose upstream. Add the three-lifecycle statement from Design resolution 3:
     the wire contract does not retire with either upstream bug.

**Production — `django_strawberry_framework/_cross_web_patches.py`** (docstrings only; no logic)

4. `::_patched_body`'s docstring — the rewrite spec box 2 names. It must state: (a) the return
   contract is unchanged — raw `self.request.body`; (b) **why**, in the load-bearing form Decision 9
   lines 1026-1033 give: upstream decodes inside a property, so a `UnicodeDecodeError` raised there
   escapes `parse_json`'s `except` and becomes an unhandled `500`; returning raw bytes moves the
   raise into the one scope that can translate it; (c) the **new** contract — raw bytes no longer
   mean "`json.loads` auto-detects the encoding": `_strawberry_patches.py::_patched_parse_json`
   strict-decodes them, so UTF-16 / UTF-32 and a UTF-8 BOM are `400`s. Sync/async parity is
   preserved, but it is now parity of **rejection**, not of success; (d) **why the patch survives
   S1 and matters more, not less** (Decision 9 lines 1044-1048): it patches
   `cross_web.DjangoHTTPRequestAdapter`, the **Django view's** sync request adapter — precisely the
   path S1 made authoritative — not anything Channels-owned; before S1 a Channels-routed deployment
   never reached that adapter at all.
5. Module docstring — five stale passages, none of which may survive, plus the gate paragraph. No
   change to the **first line**:
   - `#"JSON-decodable UTF-16/UTF-32 (with or without BOM) and UTF-8-with-BOM then parse and the request *succeeds*"`
     — **false**. Those bodies now reach a controlled `400`.
   - the gap-(2) bullet `#"A body that *is* UTF-8-decodable but is not UTF-8 JSON"` — its "while the
     **async** adapter ... already hands Strawberry the raw ``bytes`` that ``json.loads`` accepts per
     RFC 8259" clause no longer describes the package's behavior. Reword: async also hands raw bytes,
     and under the wire contract both transports now reject those encodings at the wrapper's strict
     decode. Keep both numbered gaps as real upstream defects, but state honestly that **under the
     package's wire contract only gap (1) still changes the response** — an eagerly-decoding adapter
     and our strict decode agree on every decodable-but-not-JSON shape (both `400`), so gap (2) now
     survives as the reason the correct fix is "return raw bytes" rather than "decode defensively
     inside the property".
   - `#"calling it would re-introduce the UTF-8-decodable-but-wrong-encoding gap (2) on the success path"`
     — re-base on gap (1): calling upstream's captured getter would re-introduce the property-scope
     raise, i.e. the unhandled `500`.
   - the retirement recipe's `-k "utf8 or binary or utf16_le or bom"` selector and its verdict
     sentence `#"binary or a 400 on ``utf16_le`` / BOM means the patch is still needed"` — **inverted
     under S9**. With `{"cross_web": False}` and the Strawberry patch left on, the discriminating
     rows are the undecodable ones (`utf8` / `binary`): still `500` means upstream still
     bare-decodes. The `utf16_le` / `bom` rows now answer `400` either way and diagnose nothing.
   - the `APPLY_UPSTREAM_PATCHES` paragraph
     (`#"note this patch and the companion Strawberry patch jointly own the sync transport's"`) —
     widen to name the wire contract, matching step 3's edit on the sibling module so the pair tells
     one story.

**Tests** — see the next section. Nothing else in the package changes: no `conf.py` key, no
`__init__.py` export, no `views.py` edit, no `CHANGELOG.md`, no version quintet
(spec Decision 15), no `docs/` prose (Slice 5).

### Test additions / updates

Table is the contract; the "pins" column is the assertion shape Worker 2 must land.

**A. `examples/fakeshop/test_query/test_products_api.py`** (live, sync — the inversions)

| # | Test | Change | Pins |
|---|---|---|---|
| A0 | the section comment block above `::test_post_invalid_utf8_json_body_returns_400_not_500` (`#"encoding (UTF-16/32, with or without BOM, and UTF-8-with-BOM) succeeds"`) | rewritten | The success set is now UTF-8 only; cite Decision 9 / Decision 10. Keep the existing GET-shield sentences (still true). |
| A1 | `::test_post_utf16_json_body_succeeds_like_async_transport` | **inverted + renamed** (name must no longer claim success) | `400`. Docstring **keeps the history** — why BOM'd UTF-16 bytes used to 200 (`json.loads` RFC 8259 auto-detection) — and adds the new contract plus the mechanism: the BOM's `0xFF` is not valid UTF-8, so the wrapper's strict decode raises. |
| A2 | `::test_post_utf16_le_json_body_succeeds_like_async_transport` | **inverted + renamed** | `400`. History kept (BOM-less UTF-16-LE is NUL-padded ASCII, hence UTF-8-decodable); mechanism: decodes fine, `json.loads` rejects the NUL-studded `str`. |
| A3 | `::test_post_utf8_bom_json_body_succeeds_like_async_transport` | **inverted + renamed** | `400`. History kept; mechanism: decodes fine, `json.loads` rejects the leading U+FEFF — Decision 10's zero-branch rejection. |
| A4 | new, parametrized | added | `utf-16-be`, `utf-32`, `utf-32-le`, `utf-32-be` each -> `400`. Completes Test-plan row 19 and DoD line 1721 ("UTF-16 / UTF-32 (BOM and BOM-less)"), which today have **no** UTF-32 coverage at any tier. Docstring notes the three siblings above carry the history for the previously-succeeding shapes. |
| A5 | new | added | **Row 20's non-vacuous positive control:** a valid UTF-8 body carrying a genuine multi-byte character -> `200` with the expected data. Must build the body with `json.dumps(..., ensure_ascii=False).encode("utf-8")` (default `ensure_ascii=True` would emit pure ASCII and prove nothing) and **must assert the request bytes actually contain a byte > `0x7F`** before posting. Proves the contract narrowed to UTF-8, not to ASCII. `.py` stays ASCII-only: write the character as a `\uXXXX` escape. |

`::test_post_invalid_utf8_json_body_returns_400_not_500` and
`::test_post_raw_binary_body_returns_400_not_500` are **unchanged and must stay green** — their
`400` is now reached one frame earlier (our decode instead of `json.loads`), same status, same
message.

**B. `tests/test_cross_web_patches.py`** (package — the re-aim spec box 4 names)

| # | Test | Change | Pins |
|---|---|---|---|
| B0 | module docstring `#"UTF-8-decodable non-UTF-8 JSON (BOM-less UTF-16/32, UTF-8 BOM) on the"` | rewritten | The raw-bytes contract now feeds `_patched_parse_json`'s strict decode; the pair jointly rejects every non-UTF-8 body. Keep the first line byte-identical (TREE.md). |
| B1 | `::test_body_returns_raw_bytes_for_valid_utf8` | unchanged | Async-parity raw-bytes contract. Still exactly true. |
| B2 | `::test_body_returns_raw_bytes_for_invalid_utf8` | assertions unchanged; docstring sharpened | Raw bytes reach `parse_json` so the **strict decode** can `400` it inside the one scope that can translate the raise. |
| B3 | `::test_body_returns_raw_bytes_for_utf8_bom` | **re-aimed** | Keep both existing raw-bytes assertions, then add the new half: feeding those exact bytes to `_strawberry_patches._patched_parse_json(BaseView(), adapter.body)` raises `HTTPException` with `status_code == 400`. Docstring re-based on Decision 10 (the adapter's job is to not raise in the property; the *rejection* is the wrapper's). |
| B4 | `::test_body_returns_raw_bytes_for_utf16_le_without_bom` | **re-aimed** | Same two-part shape as B3. **Keep** the `_original_body_fget(...) -> str` sanity assertion — it is the live proof upstream still bare-decodes, i.e. that the patch is still required — and correct the docstring: upstream's decode succeeding is still the bug shape, but its surviving consequence is gap (1)'s property-scope raise, not a wrong success. |

Notes for Worker 2/3: B3/B4 make this module import `HTTPException`, `BaseView`, and
`_strawberry_patches`. That cross-module reach is **the spec's own instruction** (Decision 13 lines
1280-1282: "the adapter still returns raw bytes ... and the new assertion is that the strict decode
in `_patched_parse_json` is what rejects them"), not a boundary smell — the subject of these rows
becomes the documented **pair's** joint contract. No encoding row is added here; the full matrix
lives in C3 so the two files do not carry parallel matrices.

**C. `tests/test_strawberry_patches.py`** (package — attribution and mechanism)

| # | Test | Change | Pins |
|---|---|---|---|
| C0 | module docstring item 1 (`#"A ``UnicodeDecodeError`` (raised by ``json.loads`` on a non-UTF-8"`) | rewritten | The wrapper now **owns** the decode (strict UTF-8, once, before delegating) rather than only translating a `UnicodeDecodeError` raised by `json.loads`; `str` inputs pass through untouched. |
| C1 | `::test_patched_parse_json_translates_unicode_decode_error` | assertions unchanged; docstring updated (rename optional) | Still `HTTPException(400)`; the raise now originates in our own decode. |
| C2 | new — `parse_json` sees a `str`, always | added | **Test-plan row 24's attribution.** Patch `patches._original_parse_json` with a recorder, call the wrapper with `b'{"a": 1}'`, and assert the delegate received a `str` equal to `'{"a": 1}'`. The crispest possible proof that the decode happens in the wrapper and that `json.loads` never sees bytes again. |
| C3 | new, parametrized — the wire matrix | added | Nine rows (`utf-16`, `utf-16-le`, `utf-16-be`, `utf-32`, `utf-32-le`, `utf-32-be`, UTF-8 BOM, invalid UTF-8, raw binary): each raises `HTTPException` `400` **and** carries the expected `__cause__` type — `UnicodeDecodeError` for the three decode-failures, `json.JSONDecodeError` for the six decode-then-parse failures. This is the executable form of Decision 9's measured-behavior table and of Decision 10 reason (a); it is what stops an inherited-from-`json.loads` rejection from silently becoming a `200`. |
| C4 | new — `str` passes through untouched | added | Decision 9's "A `str` input ... is passed through untouched": the recorder receives the **same object** (identity, not just equality), so no incidental re-encode/decode round trip was introduced on the GET / multipart-form-field path. |
| C5 | `::test_patched_parse_json_passes_through_valid_json` | extended | Add a multi-byte UTF-8 `bytes` body alongside the existing ASCII one, so the package tier also pins "narrowed to UTF-8, not to ASCII". Extending the existing positive test rather than adding a sibling keeps the positive direction single-sited. |
| C6 | new — the one-site parity proof | added | `DjangoGraphQLView.parse_json` **and** `AsyncDjangoGraphQLView.parse_json` both resolve to `patches._patched_parse_json`. Closes the shadowing channel (a future upstream or package override on one transport only). |

Unchanged and must stay green: `::test_patched_parse_json_rejects_non_object_body_as_400`,
`::test_patched_parse_json_rejects_batch_with_non_object_elements_as_400`,
`::test_patched_parse_json_passes_through_list_for_batch_handling`, all five
`parse_query_params` shield tests, and every `apply()` / `_validate_upstream_shape` test
(Verified fact 6).

**D. `examples/fakeshop/test_query/test_transport_api.py`** (live, async — Test-plan row 23)

| # | Test | Change | Pins |
|---|---|---|---|
| D1 | new async row, sited with the existing async twins | added | `AsyncClient().post("/async-graphql/", data=<UTF-16 bytes>, content_type="application/json")` under `override_settings(ROOT_URLCONF=__name__)` -> `400`; **plus a valid-UTF-8 control on the same mount -> `200`** in the same test, so the `400` cannot be a broken-mount artifact. DB-free `__typename` operation, for the same `SynchronousOnlyOperation` reason the two shipped async rows give. Reuses the existing mount and helper — no new scaffolding. |
| D2 | module docstring | one sentence added | Name the S9 async colour (rows 19 / 22 / 23) alongside the existing rows-1-7 and 13-18 inventory, so the file's stated scope matches its contents. |

Why D1 lives here and not in `test_products_api.py`: that module has no async test and no probe
URLconf, so hosting the row there would mean copying this module's `urlpatterns` + async view
factory — the duplication risk named in DRY item 3.

**Temp/scratch tests for Worker 3.** None are needed as scaffolding, but two probes are worth
running as review instruments (under `docs/builder/temp-tests/slice-3/`, gitignored): (i) re-run the
ten-shape decode/parse table from Verified fact 1 to confirm the measured behavior on the reviewer's
own interpreter; (ii) with `DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {"strawberry":
False}}`, confirm a UTF-16 body **succeeds** — the executable form of Design resolution 3's gate
matrix, and the thing that proves the docstrings' opt-out consequence is a true statement rather
than a plausible one.

**Focused scopes** (no `--cov*`, ever):
`uv run pytest tests/test_strawberry_patches.py tests/test_cross_web_patches.py tests/test_apps.py --no-cov`
and
`uv run pytest examples/fakeshop/test_query/test_products_api.py examples/fakeshop/test_query/test_transport_api.py --no-cov`.
No new example-project app or schema module is added, so the schema-module-list sweep in `BUILD.md`
#"Example-project schema changes must sync every schema-module list" does not apply.

### Implementation discretion items

Assessed and decided as Worker 2's call:

- **Exact new/renamed test names**, subject to two constraints: the three inverted names must not
  contain "succeeds" (or any success wording), and each must read as an encoding-rejection row.
- **`data.decode("utf-8")` vs `data.decode("utf-8", errors="strict")`.** Prefer the bare form (strict
  is the default) with the docstring naming strict-by-default; the explicit spelling is acceptable if
  Worker 2 finds it more self-documenting.
- **A5's operation shape** — a multi-byte value in `variables` vs a multi-byte filter argument on a
  real field — provided the `> 0x7F` request-byte assertion and the `ensure_ascii=False` build are
  both present.
- **A4's shape** — one parametrized test (preferred) vs four separate rows.
- **How C3 expresses the `__cause__` expectation** — a third element in the parametrize tuple vs two
  separately-parametrized tests.
- **Whether C1 is renamed** to name the strict decode, or keeps its name with an updated docstring.
- **Ordering of new rows within their sections**, and whether B3/B4's added half is a second
  assertion block in the same test or a `pytest.raises` context at the end.

Not discretionary: the single decode site, the absence of a BOM branch, the absence of any new
`except` / message literal / module constant / upstream-shape pin, the retention of every existing
green assertion listed above, and the presence of the async live row.

### Planning-pass spec-reconciliation notes (Worker 1)

No spec edit is made in this planning pass. Four items recorded for final verification:

1. **Decision 9's "the docs state that consequence" (line 1042) names no surface.** Preferred
   answer, and what this plan enacts: Slice 3's **two module docstrings** — the code-documentation
   surfaces it owns and where the pair's existing joint-ownership consequence is already documented.
   This mirrors Decision 8's own surface split, which Slice 2's final verification wrote into the
   spec after the same ambiguity (code-documentation to the slice that authors the code,
   consumer-facing prose to Slice 5). If the maintainer wants a consumer-facing sentence too, its
   home is Slice 5's transport deployment guidance in `docs/README.md`. Recommend narrowing the
   Decision 9 sentence at final verification the way box 3 was narrowed, rather than at plan time.
2. **Decision 9's "Measured behavior" enumeration (lines 1058-1061) is incomplete, not wrong.** It
   names UTF-16-with-BOM, UTF-16-LE, UTF-32-LE, and the UTF-8 BOM; it omits UTF-16-BE, UTF-32-BE
   (both decode-then-fail, like their LE siblings) and UTF-32-with-BOM (fails at the decode, like
   UTF-16-with-BOM). I verified all seven. DoD line 1721 already requires the full
   "UTF-16 / UTF-32 (BOM and BOM-less)" set, so the plan covers them; a completeness edit to
   Decision 9 is optional polish for final verification.
3. **Slice-3 box 4 is not the full test contract.** Box 4 names only the three inversions and the
   `tests/test_cross_web_patches.py` re-aim, but Test-plan rows 19-24 and DoD lines 1721-1723
   additionally require UTF-32 coverage, sync/async parity, and the row-24 attribution — none of
   which exists today (Verified fact 4). The new rows in A4 / C2 / C3 / C6 / D1 are therefore
   spec-mandated, **not** scope creep. Flagged so no reviewer reads box 4 as a ceiling.
4. **Spec status line re-verified** (spec lines 37-44, this spawn's obligation per `worker-1.md`
   #"Spec status-line re-verification"). "IN BUILD — Slices 1-2 (S1, S2) are built and accepted;
   Slices 3-5 remain" is accurate at planning time; it will need Worker 1's edit at this slice's
   final verification, not now.

No contradictory requirement was found that blocks the slice. The one question that looked like a
gap — whether the wire contract survives `APPLY_UPSTREAM_PATCHES` — is answered in the spec itself
(Design resolution 3).

### Spec slice checklist (verbatim)

Copied byte-for-byte from `docs/spec-046-transport_security-0_0_15.md` lines 160-170 (the four
sub-bullets of the Slice 3 block), preserving text, nesting, and inline citations; verified with
`diff` against a `sed -n '160,170p'` extract. The anchor links are verbatim from the spec and
intentionally resolve only there.

  - [x] `django_strawberry_framework/_strawberry_patches.py::_patched_parse_json` decodes
        `bytes` with **strict UTF-8** before delegating
        ([Decision 9](#decision-9--the-strict-utf-8-wire-contract-is-enforced-once-in-_patched_parse_json)).
  - [x] `_cross_web_patches.py::_patched_body` keeps returning raw bytes; its docstring
        is rewritten to state the new contract and why the patch survives S1.
  - [x] A UTF-8 BOM is **rejected** with the same controlled `400`
        ([Decision 10](#decision-10--a-utf-8-bom-is-rejected)).
  - [x] The three UTF-16/32/BOM **success** tests in
        `examples/fakeshop/test_query/test_products_api.py` are inverted to `400`, and the
        raw-bytes contract tests in `tests/test_cross_web_patches.py` are re-aimed at the
        new contract.

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short` after both ruff invocations. Every other modified path in that
listing is either baseline-dirty (`filters/sets.py`, `tests/filters/test_sets.py`,
the maintainer's incoming review, `docs/row-preserving-predicates-part1-plan.md`, `docs/GLOSSARY.md`,
`examples/fakeshop/db.sqlite3`, `KANBAN.md` / `KANBAN.html`, `drys.md`, `vulns.md`) or Slice 1-2
output (`conf.py`, `routers.py`, `views.py`, `examples/fakeshop/config/urls.py`,
`tests/test_routers.py`, `tests/test_views.py`, `tests/base/test_conf.py`,
`tests/auth/test_mutations.py`). None was touched or reverted by this pass.

- `django_strawberry_framework/_strawberry_patches.py` — **the only executable production change in
  the slice, two lines** (`::_patched_parse_json`):

  ```python
      try:
          if isinstance(data, bytes):
              data = data.decode("utf-8")
          parsed = _original_parse_json(self, data)
      except UnicodeDecodeError as exc:
          raise HTTPException(400, "Unable to parse request body as JSON") from exc
  ```

  No new `except`, no new message literal, no `"utf-8"` module constant, no
  `_validate_upstream_shape` change, no BOM branch, no touch to the envelope checks after the
  delegation. Docstrings: `::_patched_parse_json` restated so the decode is item 1's subject (owns
  the decode; `str` passes through untouched; RFC 8259 auto-detection unreachable; BOM and BOM-less
  multi-byte rejected with **no dedicated branch**; why not the adapter property; the one-site
  claim). Module docstring: the `APPLY_UPSTREAM_PATCHES` paragraph now names the wire contract as
  part of the opt-out; the `The bug` sync bullet reworded to describe *upstream* and to state that
  the `cross_web` patch only moves the raise; a new `The strict UTF-8 wire contract` section carrying
  the measured table, the "no new rejection branch" statement, the `__cause__` split, and the
  message-identity caveat; a new `Three lifecycles, not one` section (bug 1 retirable, bug 2 + GET
  shield retirable together, **wire contract not retirable with either**); the re-checking recipe
  re-derived. First docstring line byte-identical (TREE.md).
- `django_strawberry_framework/_cross_web_patches.py` — **docstrings only, zero logic.**
  `::_patched_body` still `return self.request.body`. Its docstring rewritten into four labelled
  paragraphs: unchanged return contract; **why** raw bytes (property-scope raise escapes
  `parse_json`'s `except` -> unhandled `500`); what raw bytes **no longer** mean (parity of
  *rejection*, not of success); why the patch survives S1 and matters more (it patches the Django
  view's sync adapter, the path S1 made authoritative). Module docstring: the false
  "...then parse and the request *succeeds*" passage removed; the gap-(2) bullet reworded (async
  hands over raw bytes too; under the wire contract only gap (1) still changes the response, and
  gap (2) survives as the reason the fix is "hand over raw bytes" not "decode defensively");
  the captured-getter sentence re-based on gap (1); the `APPLY_UPSTREAM_PATCHES` paragraph widened
  to name the wire contract, matching the sibling; the retirement recipe **inverted** (see
  Implementation notes). First docstring line byte-identical.
- `examples/fakeshop/test_query/test_products_api.py` — section comment block rewritten; three
  inversions; two new rows.
- `tests/test_cross_web_patches.py` — module docstring rewritten; two rows re-aimed two-part; one
  docstring sharpened.
- `tests/test_strawberry_patches.py` — module docstring item 1 rewritten + attribution caveat added;
  four new rows; two extended/updated.
- `examples/fakeshop/test_query/test_transport_api.py` — one new async row; one module-docstring
  paragraph.

### Tests added or updated

**A. `examples/fakeshop/test_query/test_products_api.py`** (live, sync)

- A0 — the section comment above `::test_post_invalid_utf8_json_body_returns_400_not_500`: the
  "a JSON-decodable encoding ... succeeds exactly as on the async transport" sentence is gone. It now
  states the success set is UTF-8 and UTF-8 only, names both rejection routes, says no dedicated
  branch exists, points at the async colour and the mechanism matrix, and keeps the GET-shield
  sentences verbatim.
- A1 `::test_post_utf16_json_body_is_rejected_as_400` (was `..._succeeds_like_async_transport`) —
  `400`. Docstring keeps the history (why it used to `200` via RFC 8259 auto-detection) and adds the
  mechanism: the BOM's `0xFF` is not a valid UTF-8 start byte, so the strict decode raises before
  `json.loads` is reached.
- A2 `::test_post_utf16_le_json_body_is_rejected_as_400` — `400`. History kept (NUL-padded ASCII is
  UTF-8-decodable, which is why the BOM'd sibling never covered this gap); mechanism: decodes
  cleanly, `json.JSONDecodeError` refuses the NUL-studded `str`.
- A3 `::test_post_utf8_bom_json_body_is_rejected_as_400` — `400`. History kept; Decision 10's
  reasoning (differential, zero cost) recorded in the docstring.
- A4 `::test_post_multibyte_encoded_json_body_is_rejected_as_400[utf-16-be-no-bom | utf-32-with-bom
  | utf-32-le-no-bom | utf-32-be-no-bom]` — new, parametrized. Completes test-plan row 19 / DoD line
  1721's "UTF-16 / UTF-32 (BOM and BOM-less)"; UTF-32 had **zero** coverage at any tier before this.
- A5 `::test_post_multibyte_utf8_json_body_round_trips_the_non_ascii_value` — new, row 20's
  non-vacuous positive control. Builds the body with `json.dumps(..., ensure_ascii=False)`, asserts
  `max(body) > 0x7F` **before** posting (a default `ensure_ascii=True` body is pure ASCII and would
  pass under an `"ascii"` codec), then round-trips the value out through `createCategory`'s
  `node { name }` echo **and** the stored row. Proves the contract narrowed to UTF-8, not to ASCII.
- Unchanged and green: `::test_post_invalid_utf8_json_body_returns_400_not_500`,
  `::test_post_raw_binary_body_returns_400_not_500` (their `400` is now reached one frame earlier),
  the scalar / batch-element rows, and both GET-shield rows.

**B. `tests/test_cross_web_patches.py`** (package — the re-aim, no parallel matrix)

- B0 module docstring — the raw-bytes contract is unchanged; what changed is where the bytes go. States
  the joint pair contract and explicitly routes the per-encoding matrix to
  `tests/test_strawberry_patches.py` so the two files do not both carry one.
- B2 `::test_body_returns_raw_bytes_for_invalid_utf8` — assertions unchanged; docstring sharpened to
  the property-scope-raise reason.
- B3 `::test_body_returns_raw_bytes_for_utf8_bom` — **two-part.** Both original raw-bytes assertions
  kept, then `pytest.raises(HTTPException)` -> `status_code == 400` feeding
  `strawberry_patches._patched_parse_json(BaseView(), adapter.body)` those exact bytes.
- B4 `::test_body_returns_raw_bytes_for_utf16_le_without_bom` — same two-part shape. The
  `_original_body_fget(...) -> str` sanity assertion is **kept** (it is the live proof upstream still
  bare-decodes); the docstring re-bases the surviving consequence on gap (1).
- Module now imports `HTTPException`, `BaseView`, and `_strawberry_patches` — the spec's own
  instruction (Decision 13), not a boundary leak.

**C. `tests/test_strawberry_patches.py`** (package — mechanism and attribution)

- C0 module docstring item 1 rewritten (the wrapper **owns** the decode); a new closing paragraph
  records the attribution constraint: upstream's message is byte-identical, so no test may attribute
  by status or message.
- C1 `::test_patched_parse_json_translates_unicode_decode_error` — name kept, docstring updated
  (the raise now originates in our decode).
- C2 `::test_patched_parse_json_hands_the_delegate_a_str_for_a_bytes_body` — new. Row 24's
  attribution: recorder patched over `patches._original_parse_json`, wrapper called with
  `b'{"a": 1}'`, delegate asserted to have received the `str` `'{"a": 1}'`.
- C3 `::test_patched_parse_json_rejects_every_non_utf8_wire_shape[...]` — new, **9 rows**, each
  asserting `400`, the exact `reason` literal, and `type(__cause__)`: `UnicodeDecodeError` for
  `utf-16-with-bom`, `utf-32-with-bom`, `invalid-utf8-byte`, `raw-binary`; `json.JSONDecodeError`
  for `utf-16-le-no-bom`, `utf-16-be-no-bom`, `utf-32-le-no-bom`, `utf-32-be-no-bom`, `utf-8-bom`.
- C4 `::test_patched_parse_json_passes_a_str_body_through_without_reencoding` — new. Delegate
  receives the **same object** (`is`), ruling out an incidental encode/decode round trip on the GET
  and multipart-form-field paths.
- C5 `::test_patched_parse_json_passes_through_valid_json` — extended with a multi-byte UTF-8 `bytes`
  body (asserts `max(...) > 0x7F` first), so the package tier also pins "UTF-8, not ASCII".
- C6 `::test_both_package_views_resolve_parse_json_to_the_one_patched_wrapper` — new. Both
  `DjangoGraphQLView.parse_json` and `AsyncDjangoGraphQLView.parse_json` are
  `patches._patched_parse_json`, **and** `BaseView` is the sole MRO owner of `parse_json` on each,
  which is the assertion that fails if a future intermediate class shadows the method on one
  transport only.
- Unchanged and green: the two envelope-guard rows (they pass `str`, so the new `isinstance` branch
  is a no-op for them), the batch pass-through, all five `parse_query_params` shield rows, and every
  `apply()` / `_validate_upstream_shape` row.

**D. `examples/fakeshop/test_query/test_transport_api.py`** (live, async — row 23)

- D1 `::test_the_async_package_view_enforces_the_same_utf8_wire_contract` — new. `AsyncClient`
  against the existing `/async-graphql/` mount under `override_settings(ROOT_URLCONF=__name__)`:
  UTF-16 -> `400`, UTF-8 BOM -> `400`, valid UTF-8 control -> `200` with data in the same test so
  the rejections cannot be a broken-mount artifact. DB-free `__typename`. No new mount, no new
  helper. This closes a real gap: `_cross_web_patches` patches only the **sync** adapter, so before
  this slice async accepted UTF-16 with nothing pinning it, and a `400` here can only come from the
  wrapper's strict decode (rows 23 **and** 24 together).
- D2 module docstring — one paragraph naming the S9 async colour (rows 19 / 22 / 23) and why it is
  sited here rather than in `test_products_api.py`.

Slice 2's `_ParseSpyView` / `_PARSE_CALLS` witness and its `bytes(...)` membership control are
untouched and green (the spy records the pre-decode value, which is still `bytes`).

### Validation run

In the prescribed order:

1. `uv run ruff format .` — **pass** (`400 files left unchanged`; the standing COM812 warning only).
2. `uv run ruff check --fix .` — **pass** (`All checks passed!`).
3. `uv run python scripts/check_trailing_commas.py <6 explicit paths>` — **pass** (`Fixed 0 file(s).`),
   then the same 6 paths with `--check` — **pass**, exit 0. Explicit paths only, never repo-wide.
4. `git status --short` — **classified, no churn to revert.** See `### Files touched`; the six
   slice-intended paths are exactly the ones listed there, every other entry is baseline-dirty or
   Slice 1-2 output. Re-ran after the full sweep: byte-identical listing, so the sweep produced no
   new churn (`examples/fakeshop/db.sqlite3` was already baseline-dirty and did not change status).
5. Focused, then the canonical full sweep — all `--no-cov`, never a `--cov*` flag:
   - `uv run pytest tests/test_strawberry_patches.py tests/test_cross_web_patches.py tests/test_apps.py --no-cov`
     -> **65 passed**.
   - `uv run pytest examples/fakeshop/test_query/test_products_api.py examples/fakeshop/test_query/test_transport_api.py --no-cov`
     -> **147 passed**.
   - `uv run pytest --no-cov` -> **4867 passed, 40 skipped** in 62.08s. Slice 2 closed at
     4849 / 40, so the delta is **+18 passed, 0 skipped**, which reconciles exactly with the rows
     added: A4 (4) + A5 (1) + C2 (1) + C3 (9) + C4 (1) + C6 (1) + D1 (1) = 18. No renamed row
     changed the count. The known narrowed-invocation trap
     (`test_kanban_api.py::test_select_board_docs_and_lookup_roots_for_static_dashboard` plus the
     `examples/fakeshop/tests/` rows) did not appear — the full sweep is green.

Two documentation claims were **executed rather than asserted**, because a wrong `-k` selector in a
retirement recipe is a defect:

- `-k "invalid_utf8 or raw_binary or non_object"` (the Strawberry module's recipe) collects exactly
  9 tests / 4 functions — the two gap-1 rows and both gap-2 rows, and **no** encoding row.
- `-k "invalid_utf8 or raw_binary or utf16_json"` (the `cross_web` module's re-derived recipe)
  collects exactly the 3 undecodable-body rows.
- The RFC 8259 half of the gate matrix was re-measured directly: `json.loads` accepts raw
  `utf-16`, `utf-16-le/-be`, `utf-32`, `utf-32-le/-be`, and BOM'd UTF-8 **bytes**, which is why the
  opt-out consequence documented on both `APPLY_UPSTREAM_PATCHES` paragraphs ("a UTF-16 body
  silently succeeds") is a measured statement, not a plausible one.

### Implementation notes

Deltas the plan did not pin.

- **`data.decode("utf-8")`, bare.** Chose the plan's preferred form over
  `errors="strict"`; the docstring names strict-by-default instead. Rebinding the `data` parameter
  rather than introducing a second local keeps the delegation line byte-identical to what it was.
- **`-k` selectors re-derived, not just re-worded.** The plan said the `cross_web` recipe's verdict
  was inverted; the selector itself was also wrong for a second reason once the tests were renamed.
  `utf8` matches `test_post_utf8_bom_...`, so the old token would have pulled a now-`400`-either-way
  row back into a recipe that reads `400` as "still needed". Both modules' selectors now use
  `invalid_utf8` / `raw_binary` (plus `utf16_json` for the `cross_web` one, whose BOM'd UTF-16 row is
  also undecodable and therefore discriminating). Both were collected to confirm.
- **C3 asserts the `reason` literal as well as `__cause__`.** One extra assertion per row, and it
  earns its place: it is the executable form of "no test can attribute by message", so a future
  reader cannot reintroduce a message-based discriminator without this row contradicting them.
- **C3's cause check is `type(...) is cause`, not `isinstance`.** `json.JSONDecodeError` subclasses
  `ValueError` and `UnicodeDecodeError` also subclasses `ValueError`; an `isinstance` check against
  either would go partly vacuous. Exact-type identity keeps each row discriminating.
- **C6 also asserts sole MRO ownership.** `view_class.parse_json is _patched_parse_json` alone would
  already fail on a shadowing class, but the `owners == [BaseView]` assertion states *why* the row
  exists and localizes the failure to the shadowing class rather than to "the patch is missing".
- **A5 uses `createCategory` rather than a filter argument.** Both were offered as discretion. The
  mutation echoes the value back in `node { name }` *and* persists it, so the control asserts a real
  round trip; a filter argument on Faker-generated ASCII data could only ever assert an empty result
  set, which a mis-decode would also produce.
- **A5's and C5's multi-byte literals are written as `\uXXXX` escapes** in the source
  (`_MULTIBYTE_CATEGORY_NAME = "zzz_live_caf\u00e9_\u00fcber"` and
  `{"a": "caf\u00e9"}`), per the ASCII-only `.py` rule — both files verified to contain zero
  bytes above `0x7F`. `_MULTIBYTE_CATEGORY_NAME` carries a comment naming the runtime value
  (e-acute, u-umlaut) so a reader is not left decoding escapes, and the assertions still prove
  the *encoded* body carries a `> 0x7F` byte.
- **B3/B4's added half is a `pytest.raises` block at the end of the same test**, not a separate row.
  The plan left this to discretion; keeping it in the same function is what makes the "two halves of
  one joint contract" framing legible and guarantees the two halves see the *same* byte string.
- **`_patched_body`'s docstring is organized under four bolded labels** rather than as continuous
  prose, because the plan required four distinct statements and one of them ("what raw bytes no
  longer mean") reverses what the previous docstring said. Labels make the reversal impossible to
  skim past.

### Notes for Worker 3

- No shadow file was used or refreshed this pass; the plan's `review_inspect.py` output was already
  in `docs/shadow/` and the production change is two lines, so nothing warranted a re-run.
- The production diff to `_strawberry_patches.py` is **two executable lines**; everything else in
  both patch modules' diffs is docstring text. `git diff -- django_strawberry_framework/` will look
  large for that reason — `grep '^[+-]' | grep -v '"""'`-style filtering is misleading here, better
  to read the `::_patched_parse_json` body directly.
- The distinction the plan asked you to check rather than read as duplication: the **package** matrix
  (C3) subject is *which mechanism refused which byte shape* (`__cause__`); the **live** rows'
  subject is that the whole Django + view + adapter stack answers `400` over the wire. Neither
  asserts the other's property. The `tests/test_cross_web_patches.py` rows carry no encoding matrix
  at all — only the two shapes that already had rows there, now with the joint-contract half added.
- Nothing was retired under the "retire the package-only stand-in" rule: no package test here was a
  substitute for an unreachable live line. In particular a live `400` cannot report whether the
  adapter returned `bytes` or a `str`, which is why B1-B4 stay.
- The two review probes the plan suggested under `docs/builder/temp-tests/slice-3/` were **not**
  created as files. Their content was executed inline instead and the outputs are recorded verbatim
  in `### Validation run` (the ten-shape table and the RFC 8259 `json.loads`-over-bytes measurement).
  Re-run them yourself if you want them on your own interpreter; nothing in the diff depends on them.
- No `pytest.ini` / `pyproject.toml` / `conf.py` / `__init__.py` / `views.py` change, no new settings
  key, no new public export, no `CHANGELOG.md` edit, no version movement.

### Notes for Worker 1 (spec reconciliation)

1. **The plan's C3 row count arithmetic is off by one group; the row *set* is right.** The plan
   describes the 9 rows as "`UnicodeDecodeError` for the three decode-failures,
   `json.JSONDecodeError` for the six decode-then-parse failures". Measured on the installed stack
   the split is **4 / 5**: `utf-16`-with-BOM, `utf-32`-with-BOM, an invalid UTF-8 byte, and raw
   binary fail at the decode; `utf-16-le`, `utf-16-be`, `utf-32-le`, `utf-32-be`, and the UTF-8 BOM
   decode and then fail at `json.loads`. The plan's own Verified-fact-1 table already says exactly
   this (4 `UnicodeDecodeError` rows, 6 `JSONDecodeError` rows counting plain UTF-8's success row as
   neither), so this is a transcription slip in the prose, not a design question. The test carries
   the measured 4 / 5 split. No spec text is affected — Decision 9's own enumeration is silent on
   which group each shape lands in beyond the four it names.
2. **Spec `## Current state` still names the three live tests by their pre-inversion names** (spec
   lines 363-365: `::test_post_utf16_json_body_succeeds_like_async_transport` and siblings). That
   section describes the state the card *found*, so it is arguably still correct as history, but a
   reader grepping those names now finds nothing. Recommend deciding at final verification whether
   to leave them as historical record or add "(now `::test_post_utf16_json_body_is_rejected_as_400`)"
   — I could not do either. The new names are
   `::test_post_utf16_json_body_is_rejected_as_400`,
   `::test_post_utf16_le_json_body_is_rejected_as_400`,
   `::test_post_utf8_bom_json_body_is_rejected_as_400`.
3. **`docs/review/rev-_cross_web_patches.md` and `docs/dry/dry-file-_*.md` assert the old contract**
   as live behavior ("the request now **succeeds**", "sync UTF-16 JSON gains parity with async",
   "patched: invalid=400, utf16=200"). Those are closed per-cycle scratchpads from earlier REVIEW /
   DRY cycles, exempt from standing-doc rules and not this slice's to edit, so I left them. Flagging
   only so nobody reads them during the integration pass as a contradiction of the shipped
   behavior. `docs/bug_hunt/bug_hunt-0_0_13.md` has the same shape and the same disposition.
4. **Plan spec-reconciliation note 1 is enacted as the plan proposed.** Decision 9's "the docs state
   that consequence" (spec line 1042) is discharged on **both module docstrings'**
   `APPLY_UPSTREAM_PATCHES` paragraphs, each naming the wire contract and the UTF-16-succeeds
   consequence explicitly. If you want the Decision 9 sentence narrowed to name that surface (the way
   Decision 8's split was narrowed at Slice 2's final verification), the text is in place to cite.
5. **Plan spec-reconciliation note 2 (Decision 9's incomplete enumeration) is now covered by tests
   at both tiers** — UTF-16-BE, UTF-32-BE, and UTF-32-with-BOM have live rows (A4) and package rows
   (C3). The optional completeness edit to Decision 9's "Measured behavior" paragraph is unblocked if
   you want it; the measured split is in note 1 above.
6. **No staged anchor discharged or added.** `grep -rEn 'TODO\(spec-046|TODO-ALPHA-046'` over the
   tree still matches only the spec's own prose; this slice pre-placed nothing and removed nothing.

---

## Review (Worker 3)

Reviewed the working-tree diff directly (`git diff` per path plus the untracked
`examples/fakeshop/test_query/test_transport_api.py`), not the reported inventory. The six
slice-intended paths in the diff match `### Files touched` exactly; every other dirty path is
baseline-dirty (build plan lines 25-38) or Slice 1-2 output, and none was touched or reverted by
this review (`git status --porcelain` byte-identical before and after my pass).

### Static inspection record

Re-run this pass with `--output-dir docs/shadow` (recorded, not cited by line - shadow line numbers
are NOT canonical):

- `uv run python scripts/review_inspect.py django_strawberry_framework/_strawberry_patches.py --output-dir docs/shadow`
  -> 6 imports, 5 symbols, **0 Django/ORM markers**, 0 TODOs, 9 calls of interest, repeated
  literals `variables` x3 / `extensions` x3 / `parse_json` x2 / `parse_query_params` x2 - the same
  four upstream key/method names the plan recorded, so **no new repeated literal was introduced**
  (in particular `"utf-8"` appears once and `"Unable to parse request body as JSON"` still once in
  executable code). `_patched_parse_json` moved from 5 to 6 branch nodes: the one added `if`.
- `uv run python scripts/review_inspect.py django_strawberry_framework/_cross_web_patches.py --output-dir docs/shadow`
  -> 4 imports, 4 symbols, **0 control-flow hotspots, 0 repeated literals**. `_patched_body` is
  still a one-statement function.

### Verification performed (executed this pass, not read)

1. **The production delta is mechanically two lines, and `_cross_web_patches.py` has *zero*
   executable change.** `docs/builder/temp-tests/slice-3/probe_ast_delta.py` parses each module at
   `HEAD` and in the working tree, strips every docstring, and diffs `ast.dump`:
   `_cross_web_patches.py` -> **0 AST deltas**; `_strawberry_patches.py` -> **17 AST lines, all one
   node**: `If(test=Call(isinstance, [data, bytes]), body=[Assign(data, data.decode("utf-8"))])`.
   Nothing else executable moved in either module - the envelope / batch / non-object checks after
   the delegation, `_validate_upstream_shape`, `_patched_parse_query_params`, `_patch_is_installed`
   and `apply()` are byte-equivalent at AST level. The added `if` is the first statement **inside**
   the pre-existing `try`, exactly as Design resolution 1 specifies.
2. **The Decision 10 measured-behavior table re-measured independently, all ten shapes**
   (`probe_encoding_table.py`, CPython 3.14.2 / this interpreter). **Every cell matches** the plan's
   Verified fact 1 and the spec:

   | body | strict `decode("utf-8")` | `json.loads(str)` | outcome |
   |---|---|---|---|
   | plain UTF-8 | ok | ok -> `dict` | **200** |
   | `utf-16` (BOM) | **UnicodeDecodeError** | - | 400 at the decode |
   | `utf-16-le` | ok | **JSONDecodeError** | 400 at `json.loads` |
   | `utf-16-be` | ok | **JSONDecodeError** | 400 at `json.loads` |
   | `utf-32` (BOM) | **UnicodeDecodeError** | - | 400 at the decode |
   | `utf-32-le` | ok | **JSONDecodeError** | 400 at `json.loads` |
   | `utf-32-be` | ok | **JSONDecodeError** | 400 at `json.loads` |
   | UTF-8 BOM (`EF BB BF`) | ok | **JSONDecodeError** ("Unexpected UTF-8 BOM") | 400 at `json.loads` |
   | invalid UTF-8 byte | **UnicodeDecodeError** | - | 400 at the decode |
   | raw binary | **UnicodeDecodeError** | - | 400 at the decode |

   So the zero-BOM-handling-code justification holds on this interpreter, and the real `__cause__`
   split is **4 `UnicodeDecodeError` / 5 `json.JSONDecodeError`** - which is exactly what the shipped
   C3 parametrize encodes (`utf-16-with-bom`, `utf-32-with-bom`, `invalid-utf8-byte`, `raw-binary`
   vs the four BOM-less multi-byte rows plus `utf-8-bom`). Worker 2's correction of the plan's prose
   "3 / 6" is right; the plan's own table was already 4 / 5.
3. **The `type(...) is cause` choice holds and is discriminating.** `json.JSONDecodeError` and
   `UnicodeDecodeError` are both `ValueError` subclasses and neither subclasses the other
   (measured), so an `isinstance(..., ValueError)` check would be vacuous; exact-type identity also
   fails on a `__cause__` of `None` (an unchained re-raise) and on a subclass substitution. A
   mechanism flip in either direction fails the row.
4. **The `APPLY_UPSTREAM_PATCHES` opt-out consequence both docstrings now state is *measured*, not
   plausible** (`probe_gate_optout.py` + three settings shims, real `django.test.Client` posts to
   the live `/graphql/` under three different app-load gates):
   - all patches on: plain UTF-8 -> `200`; `utf-16` / `utf-16-le` / UTF-8 BOM -> `400 "Unable to
     parse request body as JSON"`.
   - `{"strawberry": False}` (cross_web patch still installed): `utf-16`, `utf-16-le` **and** the
     UTF-8 BOM all -> **`200` with data**. The docstrings' "a UTF-16 / UTF-32 request body silently
     succeeds" is literally true.
   - `{"cross_web": False}` (Strawberry patch on): `utf-16` (BOM) raises an unhandled
     `UnicodeDecodeError` that `django.test.Client` re-raises, while `utf-16-le` and the UTF-8 BOM
     answer `400` either way. That is precisely the re-derived `cross_web` retirement verdict, and
     it confirms the *inverted* old verdict was a real defect.
   This run doubles as the **attribution proof for the sync live rows**: the identical bytes over the
   identical URL go `400` with the wrapper installed and `200` without it.
5. **Both re-derived retirement `-k` selectors select what their docstrings claim** (`--collect-only`
   `--no-cov`, scoped to `test_products_api.py` as the recipes are):
   - `-k "invalid_utf8 or raw_binary or non_object"` (Strawberry module) -> **9/118 collected**:
     `test_post_invalid_utf8_json_body_returns_400_not_500`,
     `test_post_raw_binary_body_returns_400_not_500`,
     `test_post_non_object_json_body_returns_400_not_500[json-string|json-number|json-boolean|json-null]`,
     `test_post_batch_with_non_object_elements_returns_400_not_500[array-of-numbers|array-of-null|mixed-batch]`
     - both gap-1 rows and both gap-2 halves, and **no encoding row**, as the docstring promises.
   - `-k "invalid_utf8 or raw_binary or utf16_json"` (`cross_web` module) -> **3/118 collected**:
     the two gap-1 rows plus `test_post_utf16_json_body_is_rejected_as_400`. All three bodies are
     genuinely undecodable (`b'...\xff\xfe\xfa...'`, `bytes(range(256))*4`, `encode("utf-16")`), so
     all three discriminate, and the bare `utf8` token that would have re-selected the renamed
     `test_post_utf8_bom_...` row is gone. Confirmed against the renamed rows, not the plan's names.
6. **C6 genuinely closes the shadowing channel** (`probe_c6_shadowing.py`). Baseline: both
   assertions pass. Injecting `parse_json` onto the intermediate `strawberry.django.views.GraphQLView`
   in-process makes **both** halves fail for `DjangoGraphQLView`
   (`identity assert FAILED`, `owners == ['GraphQLView', 'BaseView']`) while `AsyncDjangoGraphQLView`
   stays green - i.e. it catches exactly the one-transport-only un-patching it claims to. Restored
   with `del`; the mutation never touched disk (`git status` file set unchanged, and
   `views.py` declares no `parse_json`, so `owners == [BaseView]` is true by construction today).
7. **The async row genuinely exercises the async adapter.** `/async-graphql/` resolves through
   `::_async_graphql_view` -> `AsyncDjangoGraphQLView.as_view(...)`, awaited by Django;
   `_cross_web_patches.apply()` installs on `cross_web.DjangoHTTPRequestAdapter.body` (the **sync**
   adapter) only, so the async body arrives from upstream's own unpatched
   `AsyncDjangoHTTPRequestAdapter.get_body`. The `400`s are therefore attributable to the wrapper
   alone, and the in-test control is real, not vacuous: the third request on the same client/mount
   asserts `200` **and** `data == {"__typename": "Query"}`.
8. **No coverage deleted.** Diff-wide grep for removed `def test_` finds exactly four: the three
   renamed inversions and one same-name rewrite. `tests/test_cross_web_patches.py` keeps every
   original assertion, including B4's `_original_body_fget(...) -> str` sanity proof
   (`::test_body_returns_raw_bytes_for_utf16_le_without_bom`) and both of B3's raw-bytes
   assertions; the only removals anywhere are A1-A3's now-impossible `response.json()["data"]`
   lines. Row-15's `_ParseSpyView` witness and its `bytes(_PARSE_CALLS[0])` membership control are
   untouched - and note `bytes(str)` is a `TypeError`, so that control fails loudly rather than
   silently if the decode ever moves ahead of the spy.
9. **No performance regression from the moved decode.** `json.loads` already did
   `s.decode(detect_encoding(s), 'surrogatepass')` for `bytes` input (read from the installed
   stdlib), so decoding in the wrapper and handing over `str` is the same single pass, not an extra
   one.
10. **Canonical sweep reproduced.** `uv run pytest --no-cov` -> **4867 passed, 40 skipped** in
    58.87s, exit 0 - identical to Worker 2's report and **+18 / +0** on Slice 2's 4849 / 40. The
    delta reconciles against the diff itself, not just the total: the diff adds six test functions
    and no test function is deleted, so A4 (4 params) + A5 (1) + C2 (1) + C3 (9 params) + C4 (1) +
    C6 (1) + D1 (1) = **18**. The renames are count-neutral. The known narrowed-invocation trap
    (`test_kanban_api.py::test_select_board_docs_and_lookup_roots_for_static_dashboard` + the
    `examples/fakeshop/tests/` rows) did not appear under the full sweep.
11. **Hygiene, read-only, explicit paths only.** `ruff format --check` (6 paths) -> `6 files already
    formatted`; `ruff check` (6 paths) -> `All checks passed!`;
    `scripts/check_trailing_commas.py --check` on the same 6 explicit paths -> exit 0 (never
    repo-wide - the auto-fix default would touch the maintainer's untracked `drys.md` / `vulns.md`);
    all six files carry **0 bytes above `0x7F`**, so the `\uXXXX` escapes in A5 / C5 respect the
    ASCII-only `.py` rule.

### Spec slice checklist audit (all four boxes)

| box | verdict |
|---|---|
| `_patched_parse_json` decodes `bytes` with strict UTF-8 before delegating | **landed** - AST-proven single `if`/`decode` inside the existing `try`; no new `except`, message, constant or `_validate_upstream_shape` pin. Tick correct. |
| `_patched_body` keeps returning raw bytes; docstring rewritten for the new contract + why it survives S1 | **landed** - 0 AST deltas in the module; the docstring states the unchanged return contract, the property-scope-raise reason, "what raw bytes no longer mean" (parity of *rejection*), and the S1 paragraph (it patches the Django view's sync adapter). Tick correct. |
| A UTF-8 BOM is rejected with the same controlled `400` | **landed** - live `::test_post_utf8_bom_json_body_is_rejected_as_400`, package C3 row `utf-8-bom` (with `__cause__` pinned to the *inherited* `json.JSONDecodeError`), and the async row's second request. No BOM branch exists, correctly. Tick correct. |
| The three live success tests inverted; `tests/test_cross_web_patches.py` re-aimed | **landed** - three inversions renamed with no success wording and history retained; B3/B4 two-part with every original assertion kept. Tick correct. |

Test-plan rows 19-24 and DoD 1721-1725 are all pinned: row 19 now covers all seven non-UTF-8
shapes live (`utf-16` BOM, `-le`, `-be`, `utf-32` BOM, `-le`, `-be`, UTF-8 BOM) where UTF-32 had
zero coverage at any tier before; row 20 by A5 + C5; row 21 by the two untouched green rows; row 22
above; row 23 by the async row; row 24 by C2 + B3/B4 + the async attribution.

### High:

None.

### Medium:

None.

### Low:

#### 1. `test_transport_api.py`'s module-docstring FIRST line still scopes the file to Slices 1-2

The plan's D2 item exists so "the file's stated scope matches its contents". The added paragraph
does that, but the headline the file leads with does not, and that first line is what
`scripts/build_tree_md.py` renders - Slice 5 owns the `docs/TREE.md` regenerate for exactly these
new test modules, so left alone it publishes a stale scope claim for a file that now carries an S9
row.

```examples/fakeshop/test_query/test_transport_api.py
"""Live ``/graphql/`` transport-boundary acceptance tests (spec-046 Slices 1-2).
```

Recommended change: `... (spec-046 Slices 1-3)`. Cheap and free of TREE.md consequences right now
because the file is still untracked and has never been rendered. No test expectation is affected.
Disposition: routed to Worker 1 (below) to assign to this slice or to Slice 5's TREE pass; it must
not reach `docs/TREE.md` unfixed.

#### 2. The async row's attribution sentence over-claims for one of its two rejections

```examples/fakeshop/test_query/test_transport_api.py::test_the_async_package_view_enforces_the_same_utf8_wire_contract
    A 400 here can therefore only come from the strict decode in
    ``_strawberry_patches.py::_patched_parse_json`` ...
```

True for the `utf-16` request; for the UTF-8-BOM request in the same test the `400` is raised by
upstream's `json.loads` on the decoded `str` (`__cause__` is `json.JSONDecodeError`, which C3 pins
deliberately). The decode is still the but-for cause - without it those bytes parsed - so the
conclusion is sound, but the sentence as written contradicts the mechanism split the slice is
otherwise careful to document. Recommended wording: "can only come from the wrapper's strict decode
having replaced the raw-bytes path - either the decode itself refusing the bytes or the
`json.loads` it now feeds a `str`". Not load-bearing; no assertion changes.

#### 3. The inverted sync rows dropped from status+payload to status-only, with no live control on that colour

A1-A4 now assert `response.status_code == 400` and nothing else, so a `400` produced anywhere else
in the stack (a future middleware, a host/CSRF rejection) would keep them green while the wire
contract was gone. The async row got an in-test `200` control for exactly this reason; the sync
colour did not. Mitigations are real - A5 is a live `200` positive control in the same section, C3
pins the mechanism at package tier, and my gate probe (verification 4) shows these exact bytes over
this exact URL go `200` with the wrapper off - which is why this is Low, not Medium. Cheapest
strengthening, matching the shape already used one tier over in
`test_transport_api.py #"assert under.content == b\"Unable to parse request body as JSON\""`: assert
the response body literal on at least one of A1/A2/A3. That is not the forbidden
message-as-discriminator (both mechanisms share the message; asserting it on every row is what C3
already does), it is an "it was *this* rejection, not some other 400" check.

#### 4. (Artifact prose, not code) the `type(...) is` rationale in `### Implementation notes` does not hold as written

"`json.JSONDecodeError` subclasses `ValueError` and `UnicodeDecodeError` also subclasses
`ValueError`; an `isinstance` check against either would go partly vacuous." Measured: neither class
subclasses the other, so `isinstance(cause, UnicodeDecodeError)` on a `JSONDecodeError` is `False`
and vice versa - `isinstance` against either *specific* class would still discriminate the two
candidates. Only `isinstance(..., ValueError)` is vacuous. **The choice is still correct and
strictly stronger** (verification 3), so nothing in the diff changes; recorded only so Worker 1 does
not carry the reasoning forward as stated.

### DRY findings

- **No second decode site, no encoding sniffer, no duplicated async mount, no parallel matrix - all
  four plan-declared risks verified closed.** The repo-wide grep for `decode("utf` / `.decode()` /
  `UnicodeDecodeError` inside `django_strawberry_framework/` still hits only the two patch modules,
  and only one of them decodes. D1 reuses the existing `/async-graphql/` mount and
  `override_settings(ROOT_URLCONF=__name__)`; `urlpatterns` gained nothing. The 9-row mechanism
  matrix exists once (C3); `tests/test_cross_web_patches.py` carries no encoding matrix, only its
  two pre-existing shapes with the joint-contract half appended.
- **The live tier necessarily repeats the encoding list (A1-A3 individually + A4 parametrized +
  D1's two), but with a different subject** (wire outcome vs which mechanism refused). Folding
  A1-A3 into A4's parametrize would delete the per-encoding history docstrings Decision 13 requires
  be kept, so the near-duplication is spec-mandated. No change recommended.
- **`"Unable to parse request body as JSON"` now appears in two test files** (C3's `reason` assert
  and Slice 2's `test_transport_api.py` malformed-body row) plus once in executable production code.
  Two test-tier uses with distinct subjects; extracting a shared constant would have to cross the
  `tests/` <-> `examples/` tree boundary. Observed and rejected as a consolidation target.
- **Deferred to the integration pass (new):** `test_transport_api.py` now has six inline
  `await client.post(path, data=..., content_type="application/json")` blocks across three async
  rows (two of them Slice 3's) while the module's own `::_post_bytes` helper already expresses that
  shape and would work unchanged under `await`. Slice 3 correctly followed the local convention
  Slices 1-2 established rather than diverging mid-file; the consolidation (an `_async_post_bytes`,
  or awaiting `_post_bytes`) belongs with the Slice-2 permission-block DRY item at the integration
  pass.
- **Prose duplication to watch, not to fix now:** the measured table / rejection-route explanation
  now appears in four places (both module docstrings, `test_products_api.py`'s section comment,
  C3's docstring). Each addresses a different reader and two of the four are explicit spec box
  items, so this is justified - but Slice 5 should point its consumer-facing prose at the contract
  rather than restate the table a fifth time.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**: `__all__` and the re-export list
are unchanged, so the DoD's "no new public exports" holds. `views.py`'s
`__all__ = ("AsyncDjangoGraphQLView", "DjangoGraphQLView")` is unchanged from Slice 1 (this slice
does not touch `views.py`; it only *imports* both classes into `tests/test_strawberry_patches.py`
for C6). Both patch modules remain private (`_`-prefixed) and neither is exported. Spec Decision 5's
authorized break belongs to Slice 1 and is not re-measured here - this slice changes no public
signature at all.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. Verified rather than
assumed: `git status --porcelain` reports **no modification** to `pyproject.toml`, `CHANGELOG.md`,
`README.md`, `TODAY.md`, `docs/README.md`, `docs/TREE.md`, `django_strawberry_framework/__init__.py`
or `tests/base/test_init.py`, so the version quintet has not moved (spec Decision 15 / build plan's
joint-cut flag) and no Slice-5-owned prose surface was pre-empted. `docs/GLOSSARY.md`, `KANBAN.md`,
`KANBAN.html` and `examples/fakeshop/db.sqlite3` are dirty **from the baseline list only**; their
diffs carry the concurrent row-preserving work, and a grep of the two baseline-dirty package/test
files for `utf-8` / `parse_json` / `decode(` returns nothing, so this slice did not leak into them.
Both patch modules' **first docstring lines are byte-identical** to `HEAD`, so the pending TREE.md
regenerate is unaffected by them (see Low 1 for the one first line that is not).

### What looks solid

- The production change is the smallest thing that could implement Decision 9, and it is provably
  the *only* executable change in either patch module. Reusing the existing `try` / `except
  UnicodeDecodeError` / existing message means the slice added zero new branches, statuses, message
  literals, module constants and upstream-shape pins - and after the change that `except` is
  reachable *only* from the package's own decode, which is the tidiest possible reading of "the
  raise lives in the one scope that can translate it".
- Decision 10 really did cost zero production code, and the slice noticed the obligation that
  creates: because the BOM rejection is *inherited* from `json.loads`, C3 pins it by `__cause__`, so
  a future stdlib that tolerated U+FEFF turns a green suite red instead of silently turning a `400`
  into a `200`. That is the right instinct applied to an inherited behavior.
- Attribution discipline is consistent everywhere it matters: no test anywhere attributes by
  message, C0 records *why* (upstream's literal is byte-identical), C2 proves the delegate receives
  a `str`, C4 proves a `str` input is the **same object** (so no incidental re-encode landed on the
  GET / multipart paths), and C3 asserts the shared `reason` across all nine rows - which makes the
  non-attributability itself executable.
- C6 is the highest-value new package row: it is the only thing in the suite that would catch a
  future intermediate class un-patching one transport, and it fails for the right class with the
  right message when I inject that exact regression.
- The async live row is the strongest single test in the slice - unpatched adapter, so the `400` can
  only be the wrapper's; DB-free `__typename` to avoid `SynchronousOnlyOperation`; and a real
  in-test `200`-with-data control on the same client and mount.
- A5 is a properly non-vacuous positive control: `ensure_ascii=False`, an `assert max(body) > 0x7F`
  *before* the post, and a round trip through both the mutation echo and the stored row. It pins
  "narrowed to UTF-8, not to ASCII", which a naive positive test would have missed entirely.
- Both retirement recipes were treated as executable documentation and re-derived, not re-worded -
  and my own three-gate measurement shows the *old* verdicts were genuinely inverted, so this was a
  real defect closed rather than a tidy-up.

### Temp test verification

Four probes plus three settings shims under `docs/builder/temp-tests/slice-3/` (gitignored):

- `probe_encoding_table.py` - the independent ten-shape re-measurement (verification 2) and the
  `json.loads`-over-raw-bytes / subclass-relationship checks.
- `probe_ast_delta.py` - the docstring-stripped AST diff of both patch modules against `HEAD`
  (verification 1). This is the instrument that turns "the production change is two lines" from a
  claim into a proof; worth keeping as a technique.
- `probe_gate_optout.py` + `w3_settings_all_on.py` / `w3_settings_strawberry_off.py` /
  `w3_settings_crossweb_off.py` - the three-gate live measurement (verification 4).
- `probe_c6_shadowing.py` - the C6 strength injection (verification 6).

**Disposition: none promoted, none needed.** No probe caught a behavior bug. C6 already ships the
property `probe_c6_shadowing.py` exercises. The gate-matrix probe proves a *documentation* claim and
needs a separate app-load per gate (the patches install in `AppConfig.ready`), so it is not
expressible as an in-process pytest row without a subprocess harness - out of proportion to a
docstring, and the module docstrings carry the procedure. Files left in place for the closeout
cleanup. **No probe wrote to any production or third-party file:** the only in-process mutation was
`strawberry.django.views.GraphQLView.parse_json` in `probe_c6_shadowing.py`, deleted in a `finally`
and re-verified green in the same run, and `git status --porcelain` is byte-identical to the pre-review
listing.

### Notes for Worker 1 (spec reconciliation)

1. **Escalated: Low 1 - `test_transport_api.py`'s first docstring line still says "Slices 1-2".**
   Resolution paths: (a) let Worker 2 fix it in a Slice-3 re-pass now (one word, zero test impact,
   and free while the file is still untracked and unrendered); or (b) fold it into Slice 5's
   `docs/TREE.md` regenerate, which must touch this file's rendered entry anyway. Either is
   defensible; what is not is regenerating TREE.md from a first line that under-claims the file's
   scope. My preference is (a), because the file is Slice 3's to edit today and Slice 5's checklist
   does not name it.
2. **Escalated: Lows 2 and 3 are single-sentence / single-assertion changes** in
   `test_transport_api.py` and `test_products_api.py`. Neither blocks; both are cheap enough that a
   Slice-3 re-pass is the natural home if you want them, rather than a Slice-5 prose sweep (Low 3 is
   an assertion, which Slice 5 has no mandate to add).
3. **Worker 2's `Notes for Worker 1` item 1 is confirmed by independent measurement.** The
   `__cause__` split is 4 / 5, not the plan prose's 3 / 6, and the plan's own Verified-fact-1 table
   already said 4 / 5. Transcription slip in the plan, correctly implemented in the test. If you
   take the optional completeness edit to Decision 9's "Measured behavior" paragraph (its
   enumeration omits UTF-16-BE, UTF-32-BE and UTF-32-with-BOM), the full ten-row table above is
   re-measured on this interpreter and safe to cite.
4. **Decision 9 line 1042's "the docs state that consequence" is discharged, and I verified the
   statement is true rather than plausible** (verification 4): with `{"strawberry": False}` a UTF-16
   body really does answer `200`. If you narrow the Decision 9 sentence to name the two module
   docstrings the way Decision 8's split was narrowed, the text it would cite is measured-accurate.
5. **Worker 2's item 2 (spec `## Current state` still names the pre-inversion test names) is real
   and I would take the parenthetical.** A reader grepping `::test_post_utf16_json_body_succeeds_like_async_transport`
   now finds nothing anywhere in the tree; the new names are in that note. Historical-record framing
   is defensible, but the spec is also the card's own navigational index.
6. **Worker 2's item 3 (closed per-cycle scratchpads under `docs/review/` and `docs/dry/` assert the
   old success contract) - agreed disposition, leave them.** They are `START.md`-exempt per-cycle
   artifacts. Worth one line in `bld-integration.md` so the integration pass does not read them as a
   contradiction of shipped behavior.
7. **No staged anchor outstanding.** Independently re-swept
   `grep -rEn 'TODO\(spec-046|TODO-ALPHA-046'`: matches only the spec's own prose line 1378.
8. **DRY item routed to the integration pass:** the six inline `await client.post(...)` blocks in
   `test_transport_api.py` (see `### DRY findings`), alongside the Slice-2 permission-block item.

### Review outcome

`review-accepted`. No High and no Medium findings; the four Lows are recorded above with concrete
recommendations, and Lows 1-3 are transparently escalated to final verification (item 1-2) rather
than left dangling - Low 4 is artifact prose with no diff consequence. What convinced me: the
executable delta is *mechanically* proven to be one `if` + one `decode` with zero change to
`_cross_web_patches.py` and zero change to the envelope guards; my own re-measurement of all ten
byte shapes reproduces the table the zero-BOM-code decision rests on, cell for cell, including the
4 / 5 `__cause__` split the shipped matrix encodes; the async row demonstrably drives the *unpatched*
async adapter with a real in-test control, so it is the attribution proof it claims to be; both
re-derived retirement selectors collect exactly what their docstrings say and my three-gate live
measurement shows the previous verdicts were genuinely inverted; C6 fails for the right class when I
inject the shadowing regression it exists to catch; nothing was dropped from
`tests/test_cross_web_patches.py` and no test function was deleted anywhere; and the canonical
`uv run pytest --no-cov` sweep reproduces 4867 passed / 40 skipped with the +18 reconciled against
the diff's own six added functions rather than only against the total.

---

## Final verification (Worker 1)

Read the full artifact (plan / build report / review), the working-tree diff per path
(including the untracked `examples/fakeshop/test_query/test_transport_api.py`), both accepted
sibling artifacts, and the spec sections Slice 3 cites. Every measurement below I executed
myself; where it reproduces a worker's number I say so rather than citing theirs.

### Spec slice checklist audit (all four boxes, against the diff)

All four `- [x]` ticks are **correct**; none is un-ticked, and no box was left `- [ ]`, so no
deferral is owed on the checklist itself.

| box | verdict from the diff |
|---|---|
| `::_patched_parse_json` decodes `bytes` with strict UTF-8 before delegating | **landed.** My own docstring-stripped `ast.dump` diff vs `git show HEAD:` (re-derived, not Worker 3's relayed run) reports **17 dumped lines forming exactly one node** - `If(test=Call(isinstance,[data,bytes]), body=[Assign(data, data.decode("utf-8"))])` - as the first statement inside the pre-existing `try`. No new `except`, message literal, `"utf-8"` module constant, or `_validate_upstream_shape` pin; the envelope / batch guards after the delegation are byte-equivalent at AST level. |
| `_patched_body` keeps returning raw bytes; docstring rewritten for the new contract + why the patch survives S1 | **landed.** Same instrument: **0** docstring-stripped AST deltas in `_cross_web_patches.py`, so the module's executable behavior is provably untouched, and `return self.request.body` still stands. The docstring's four labelled paragraphs carry the unchanged return contract, the property-scope-raise reason, "what raw bytes no longer mean" (parity of *rejection*), and the S1 paragraph. |
| A UTF-8 BOM is rejected with the same controlled `400` | **landed** at all three tiers - live `::test_post_utf8_bom_json_body_is_rejected_as_400`, the async row's second request, and C3's `utf-8-bom` row pinning `__cause__` to the **inherited** `json.JSONDecodeError`. No BOM branch exists anywhere, which is Decision 10's point. |
| the three live success tests inverted; `tests/test_cross_web_patches.py` re-aimed | **landed.** Three renames with no success wording and the history retained in each docstring; B3/B4 are two-part with **every** original assertion kept, including B4's `_original_body_fget(...) -> str` proof that upstream still bare-decodes. |

Test-plan rows 19-24 and DoD lines 1777-1781 are all pinned; row 19's UTF-32 coverage did not
exist at any tier before this slice.

### Independent verification of the two claims the Lows turn on

1. **The `type(...) is cause` reasoning, corrected (Worker 3's Low 4 - see below).** Measured:
   `json.JSONDecodeError.__mro__` is `(JSONDecodeError, ValueError, ...)`,
   `UnicodeDecodeError.__mro__` is `(UnicodeDecodeError, UnicodeError, ValueError, ...)`, and
   `issubclass` is `False` in **both** directions.
2. **The inverted rows' status-only assertion is not vacuous - the but-for proof (Low 3).**
   `json.loads` over the **raw bytes** of all seven non-UTF-8 shapes
   (`utf-16`/`-le`/`-be`, `utf-32`/`-le`/`-be`, UTF-8-BOM) returns the valid envelope
   `{'query': '{ __typename }'}`. So the regression these rows exist to catch - the strict
   decode being removed or un-installed - flips every one of A1-A4 from `400` to **`200`**, not
   to a different `400`. That is a stronger discrimination proof than a response-body literal
   would have been, and it reproduces the outcome of Worker 3's three-gate live probe from a
   pure measurement.

### Spec slice checklist deferrals

None. Every box landed; nothing is deferred from the checklist.

### DRY check across Slices 1-3

**Verdict: no new duplication introduced by Slice 3. Two live cross-slice items stay deferred
to the integration pass, both binding.**

- **Slice 2's DRY-1 stays deferred, and is unchanged in scope.** Re-measured, not inherited:
  `src.count(block) == 2` for the 7-line permission-granting block in
  `examples/fakeshop/test_query/test_transport_api.py`. Slice 3 added **no third site** (A5
  needed the same actor but lives in `test_products_api.py`, where it correctly reused that
  module's existing `_login_with_perm` helper rather than copying the block across trees).
  Binding integration-pass work item, unchanged: extract one module-local
  `_user_who_can_add_categories()` and rewire both call sites.
- **Worker 3's new item - the six inline `await ....post(...)` blocks - stays deferred, and is
  now equally binding.** Counted myself: **6** matches for `await \w+\(?\)?\.post\(` in
  `test_transport_api.py`, across three async rows (Slice 1's middleware row, Slice 2's
  async-cap row, Slice 3's wire-contract row). `::_post_bytes` already expresses the shape and
  needs no change to be awaited, since `AsyncClient.post` returns the awaitable.
  **Integration-pass work item:** await `_post_bytes` from the async rows (or add a two-line
  `_async_post_bytes` if the `await` reads better at the call site), rewiring all six.
- **Why neither is pulled forward.** Both duplications *span* accepted slices, so both are
  cross-slice work by definition and BUILD.md's integration pass is their designated home. More
  concretely: Worker 1 may not edit tests, so pulling either forward costs a `revision-needed`
  re-loop (Worker 2 pass + Worker 3 re-review) on a diff with **zero High and zero Medium**, in
  order to add a test helper - and it would edit Slice-1- and Slice-2-accepted rows before
  Slice 4 has had its chance to add a fourth async row wanting the same helper. Nothing here is
  "ship now, fix later": both land inside this same build, before the maintainer's first touch
  point, and both are recorded as obligations `bld-integration.md` inherits rather than
  rediscovers.
- **No new repeated literal, no second decode site.** `"utf-8"` appears once in production and
  `"Unable to parse request body as JSON"` still once in executable code; the repo-wide grep for
  `decode("utf` / `UnicodeDecodeError` inside `django_strawberry_framework/` still hits only the
  two patch modules, and only one of them decodes. The 9-row mechanism matrix exists once (C3);
  `tests/test_cross_web_patches.py` carries no parallel matrix. `test_products_api.py`'s live
  encoding rows repeat the encoding list with a *different subject* (wire outcome vs which
  mechanism refused) and folding A1-A3 into A4's parametrize would delete the per-encoding
  history Decision 13 requires be kept - verified-and-rejected as a consolidation target, as
  Worker 3 recommended.

### Existing tests still pass (focused scope, `--no-cov` only)

Run by me this pass; no `--cov*` flag anywhere:

- `uv run pytest tests/test_strawberry_patches.py tests/test_cross_web_patches.py tests/test_apps.py --no-cov -q` -> **65 passed** (1.59s).
- `uv run pytest examples/fakeshop/test_query/test_products_api.py examples/fakeshop/test_query/test_transport_api.py --no-cov -q` -> **147 passed** (35.08s).

Both reproduce Worker 2's and Worker 3's focused numbers exactly. The canonical sweep at
**4867 passed / 40 skipped** was measured independently by Worker 2 and again by Worker 3, and
each reconciled the **+18 / +0** delta off Slice 2's 4849 / 40 **row by row against the diff's
own six added functions** (A4 4 + A5 1 + C2 1 + C3 9 + C4 1 + C6 1 + D1 1 = 18, renames
count-neutral) rather than only against the total. I cite that rather than re-running it a third
time; `bld-final.md`'s gate re-runs it as the backstop.

### Staged-anchor check

`grep -rEn 'TODO\(spec-046|TODO-ALPHA-046'` over the tree: **no source or test anchor
anywhere** - the only matches are the spec's own prose describing the convention and the
`bld-*.md` per-cycle narrative. Slice 3 pre-placed none and discharged none, correctly (Slice
1's single anchor was Slice 2's and is gone).

### The four Lows, decided

- **Low 1 (first docstring line still says `Slices 1-2`) - routed to Slice 5, contractually**,
  as a new checklist sub-bullet (spec change 6a), **not** `revision-needed`. Worker 3 preferred
  the re-pass on the grounds that Slice 5's checklist does not name the file; that premise is
  false - Slice 5 already owes a docstring correction *in this same file* (the obsolete "the
  spec predicts 413" clause, routed there at Slice 2), so the routing adds a second correction
  to an existing pass rather than inventing one. Two further reasons decide it. (i) A
  `revision-needed` on a zero-High / zero-Medium diff costs a full Worker 2 + Worker 3 re-loop
  to change one number, which is out of all proportion. (ii) Pinning `Slices 1-3` **now would
  itself be a guess**: Slice 4 can still add a row to this file, and the number only has to be
  true at the moment `scripts/build_tree_md.py` reads it - which is inside Slice 5's own pass.
  The spec bullet therefore requires the correction **before** the `docs/TREE.md` regenerate in
  that slice, which closes the only consequence Worker 3 was protecting against. Its warning
  is respected in full: the stale line must not reach `docs/TREE.md`, and now it contractually
  cannot.
- **Low 2 (the async row's attribution sentence over-claims for the BOM request) - routed to
  Slice 5 with the same bullet** (spec change 6b), with Worker 3's wording named in the spec so
  the correction cannot drift into a re-litigation. Not rejected: the sentence is genuinely
  wrong about mechanism for one of its two rejections, and the sentence sits in a slice that is
  otherwise scrupulous about the `UnicodeDecodeError` / `json.JSONDecodeError` split. But the
  conclusion is sound (the decode is the but-for cause of both `400`s, which item 2 of my
  verification proves from `json.loads` over raw bytes), no assertion depends on it, and it is a
  docstring in the same file as Low 1 - so the same prose pass should own both.
- **Low 3 (the inverted rows are status-only, sync colour has no in-test control) - accepted as
  adequate coverage; no control required.** Verified-and-rejected as a strengthening target, so
  the integration pass does not re-open it. Four reasons, the first of which is mine and is
  decisive: (i) the regression the rows exist to catch cannot produce a *different* `400` -
  `json.loads` accepts the raw bytes of all seven shapes as a valid envelope, so removing or
  un-installing the strict decode flips A1-A4 to **`200`** and every one of them fails loudly;
  (ii) the two pre-existing rows in this same section
  (`::test_post_invalid_utf8_json_body_returns_400_not_500`,
  `::test_post_raw_binary_body_returns_400_not_500`) have asserted status-only since before this
  card, so A1-A4 follow the section's own established idiom rather than weakening it - and
  hardening only the new rows would leave the section internally inconsistent; (iii) the module
  carries **71** live `status_code == 200` assertions over the same `/graphql/`, so the
  "a future middleware returns 400 for everything" scenario is not survivable by the suite;
  (iv) C3 pins the mechanism per shape at package tier and the async row carries its own in-test
  `200`-with-data control. Adding a response-body literal would guard a hypothesis the suite
  already excludes, at the cost of a re-loop Worker 1 cannot perform directly.
- **Low 4 (the `type(...) is` rationale in Worker 2's `### Implementation notes`) - record
  corrected here** rather than by editing that section, which is a prior pass's entry and stays
  as written (BUILD.md #"do not edit prior entries"). **The accurate reasoning:** neither
  `json.JSONDecodeError` nor `UnicodeDecodeError` subclasses the other (measured above), so
  `isinstance` against either *specific* class would still discriminate the two candidates -
  only `isinstance(..., ValueError)` is vacuous, since both derive from it. `type(...) is` is
  still the right choice and is strictly stronger: it also fails on a `__cause__` of `None`
  (an unchained re-raise) and on a subclass substitution. Nothing in the diff changes. Carried
  into `worker-1.md` so the wrong version is not repeated in a later slice.

### Historical scratchpads: confirmed untouched, and why that is not a contradiction

Worker 2 and Worker 3 both flagged that `docs/review/rev-_cross_web_patches.md`,
`docs/dry/dry-file-_*.md`, and `docs/bug_hunt/bug_hunt-0_0_13.md` assert the old "UTF-16
succeeds" contract as live behavior. **Agreed disposition: leave every one of them untouched,
and this is the record so the integration pass does not read them as a contradiction of shipped
behavior.** They are per-cycle artifacts of closed REVIEW / DRY / bug-hunt cycles, explicitly
exempt from the standing-doc rules (`AGENTS.md` #"Source references in docs and code comments"
names `docs/review/review-<X>.md`, `docs/review/rev-*.md`, `docs/dry/dry-<X>.md` and
`docs/builder/bld-*.md` as the closing-scratchpad tier), `AGENTS.md` forbids bulk-editing under
`docs/review/`, and rewriting a closed cycle's findings would destroy the evidence trail that
justified the patch pair in the first place. A scratchpad that describes the behavior *at its
own cycle's HEAD* is doing its job. Carried to `bld-final.md`'s deferred-work catalog as a
"do not act" entry.

### Summary

Slice 3 delivers S9 in the smallest shape that could implement Decision 9: one `isinstance`
guard and one `.decode("utf-8")` as the first statement inside `_patched_parse_json`'s existing
`try`, reusing the existing `UnicodeDecodeError` -> `HTTPException(400, ...)` translation. I
proved that mechanically rather than reading it - **0** docstring-stripped AST deltas in
`_cross_web_patches.py` and exactly **one** added `If` node in `_strawberry_patches.py` - so the
"docstrings only" and "two lines" claims are measurements, not prose. After the change that
`except` is reachable only from the package's own decode, which is the tidiest available reading
of "keep the raise in the one scope that can translate it". Decision 10 cost zero production
code, and the slice correctly noticed the obligation that creates: five of the nine rejections
are *inherited* from `json.loads`, so C3 pins them by `__cause__` and a future stdlib that
tolerated a leading U+FEFF turns the suite red instead of silently turning a `400` into a `200`.
Coverage is earned live-first on both transports, with the async row driving the **unpatched**
async adapter - the strongest single test in the slice, because a `400` there is attributable to
the wrapper by construction.

Where I differed from the review: I accepted Low 3 rather than asking for a control, because
`json.loads` accepts the raw bytes of every rejected shape as a valid envelope, which means the
status-only rows flip to `200` - not to some other `400` - the moment the contract regresses;
and I routed Lows 1 and 2 to Slice 5 rather than re-looping the slice, because Slice 5 already
owes a docstring correction in that very file and because the first line only has to be true at
the moment `docs/TREE.md` renders it. Six spec edits: the status line, two incomplete
"measured behavior" enumerations (one of which is now the single ten-row table both sites point
at, recording the authoritative 4 / 5 `__cause__` split), the pre-inversion test names in
`## Current state`, the unpinned "the docs state that consequence" surface in Decision 9, and
the two routed prose corrections written into Slice 5's checklist as contract items. Glossary
checker green at 37 terms, all 19 anchors resolve, no `-terms.csv` row owed, `docs/GLOSSARY.md`
untouched.

**Final status: `final-accepted`.**

### Spec changes made (Worker 1 only)

Six edits to `docs/spec-046-transport_security-0_0_15.md`, all triggered by Slice 3. Verified
after the last one:
`uv run python scripts/check_spec_glossary.py --spec docs/spec-046-transport_security-0_0_15.md`
-> **`OK: 37 terms - all have glossary entries and at least one spec link.` (exit 0)**. Term
count unchanged at 37, so **no new glossary term and no `-terms.csv` row** is owed and
`docs/GLOSSARY.md` is untouched (its dirty state is the baseline-listed concurrent
row-preserving work). All **19** in-page anchors re-verified to resolve to real headings - I
introduced no new anchor target, only reused three existing ones. `git diff --check` clean. No
`.py` file was touched by this pass, so no `check_trailing_commas.py` run is owed (Worker 2 and
Worker 3 each ran it on the six explicit slice paths). **Decision 15, the version-boundary
preamble, and the `CHANGELOG.md` prohibition were not touched.**

1. **Status line (line 37).** `IN BUILD - Slices 1-2 (S1, S2) are built and accepted; Slices
   3-5 remain.` -> `IN BUILD - Slices 1-3 (S1, S2, S9) are built and accepted; Slices 4-5
   remain.` - required by `worker-1.md` #"Spec status-line re-verification"; the header would
   otherwise describe an accepted slice as unbuilt for the rest of the cycle.

2. **Decision 9's "Measured behavior" paragraph replaced by the complete ten-row table (now
   lines 1094-1116).** - **Escalated item 6, and the plan's own reconciliation note 2.** The
   prose enumerated four of the nine rejected shapes and omitted UTF-16-BE, UTF-32-BE, and
   UTF-32-with-BOM, leaving a reader to infer a sibling's behavior from a named one. All ten
   shapes are now enumerated as a table with the mechanism per row, and the paragraph after it
   records the **authoritative split as 4 `UnicodeDecodeError` / 5 `json.JSONDecodeError`**,
   why (BOM'd forms carry an invalid leading byte; BOM-less forms decode into NUL-studded text
   only the parser refuses), and why `__cause__` is the only thing that can record it (status
   and message are identical by design). This is the number the shipped C3 matrix encodes; the
   plan's *prose* said "3 / 6" while the plan's own table said 4 / 5, and both Worker 2 and
   Worker 3 re-measured 4 / 5 independently, as did my own `json.loads`-over-raw-bytes run. The
   spec now carries the measured value once, so no future reader inherits the transcription
   slip.

3. **`## Current state`'s "The encoding matrix was measured" bullet (lines 368-378) completed
   and de-duplicated.** The same omission appeared here - my memory's standing pattern is that
   an escalation names fewer sites than exist, so I grepped the wrong claim rather than fixing
   only the escalated site. The bullet now states the raw-bytes success set completely
   (UTF-16 / UTF-32, BOM and BOM-less, LE **and** BE) and defers the mechanism table to
   Decision 9 rather than restating it, so the two sites cannot drift apart again.

4. **`## Current state`'s "Three live tests" bullet (lines 379-390) gains the post-inversion
   names.** - **Escalated item 5, decided: both, not either.** The pre-inversion names stay,
   because that section documents the state the card *found* and deleting them would erase why
   the inversion was a card obligation; but `AGENTS.md` #"Source references in docs and code
   comments" requires that renaming a symbol be met with a grep-sweep for `::OldName`
   references **in the same change**, and a spec is a standing doc, not a per-cycle scratchpad.
   A reader grepping the old names previously found nothing anywhere in the tree. The bullet now
   says the three names are the found state and that Slice 3 inverted them, and gives the three
   current names, noting the `tests/test_cross_web_patches.py` rows kept their names and were
   re-aimed in place.

5. **Decision 9 gains a "Which docs, by surface" block (lines 1067-1080).** - **Escalated item
   7, and the plan's reconciliation note 1, enacted as the plan proposed.** The Decision said
   "the docs state that consequence" and named no surface, which is the same ambiguity Decision
   8 had at Slice 2 and which I resolved there by splitting on **surface**. The block now pins
   it: the code-documentation surface belongs to the slice that authors the code, so Slice 3
   discharges it on the `APPLY_UPSTREAM_PATCHES` paragraph of **both** patch module docstrings -
   and it states why *both* rather than one (the consequence differs per half: without the
   `cross_web` half an undecodable body is an unhandled `500`; without the Strawberry half the
   wire contract is absent and a UTF-16 / UTF-32 body silently succeeds, which Worker 3
   measured live rather than assumed). Any consumer-facing restatement is named as Slice 5's
   deployment guidance, not a third code surface. **No new Slice-3 checklist box was added:**
   the work has already landed and been verified, a post-hoc fifth box would diverge from this
   artifact's audited verbatim block for no reader benefit, and Decision 8's precedent puts the
   surface split *at the Decision*, which is where a future slice will look.

6. **Slice-5 checklist gains a "Slice-3 prose corrections" sub-bullet (lines 232-246).** -
   Worker 3's escalated **Low 1** and **Low 2**, routed as contract items rather than notes, so
   Slice 5's planning pass inherits them instead of finding them in `bld-final.md`'s catalog.
   (a) the module docstring's first line in
   `examples/fakeshop/test_query/test_transport_api.py`, with the ordering constraint stated
   explicitly - correct it **before** the `docs/TREE.md` regenerate in that same slice, because
   that first line is what `scripts/build_tree_md.py` renders - and with the reason the number
   is not pinned here (Slice 4 can still add a row to the file); (b) the async row's attribution
   sentence, with Worker 3's replacement wording named. Both are prose only; no assertion
   changes and the accepted rows stay exactly as they are.

### The accumulating Slice-5 prose obligations, as the spec now enumerates them

Re-read in place this pass, not remembered. Slice 5's checklist now carries **ten**
sub-bullets; **four** of them (the `auth/` strings, `examples/fakeshop/test_query/README.md`,
the Slice-2 prose corrections, and the new Slice-3 prose corrections) carry the **eight**
discrete prose-correction obligations accumulated across Slices 1-3, enumerated here so the
integration pass can grep each one rather than trust a count:

1. **Slice 1's L2** - the three now-wrong transport strings in
   `django_strawberry_framework/auth/`: `sessions.py::classify_transport`'s
   unrecognized-scope-type `ConfigurationError` message, and the
   `mutations.py::_login_resolve_body` / `::_logout_resolve_body` docstrings describing "the
   package router's async consumer".
2. **Slice 2's L1** - `views.py`'s cap-contract docstring re-worded from the non-operative
   `View.as_view`-guard claim to the operative reason (precedence over a same-named attribute
   upstream may later add).
3. **Slice 2's L2** - `conf.py`'s `MAX_REQUEST_BODY_BYTES` comment gains the multipart
   carve-out, and the `docs/README.md` deployment guidance carries it too.
4. **Slice 2's L3** - the trivially-true `mixin.__name__ not in __all__` assertion in
   `tests/test_views.py` dropped, leaving the exact-`__all__` test as the single privacy proof.
5. **Slice 2's obsolete `413` clause** -
   `test_transport_api.py::test_the_two_body_ceilings_are_distinguishable_by_the_response_they_produce`'s
   docstring drops the "the spec's Edge-case sentence predicting a `413` is inaccurate" clause,
   which Slice 2's own spec correction made obsolete; the `400` explanation stays.
6. **`examples/fakeshop/test_query/README.md`** - the **S1 and S2** acceptance rows (the file
   does not mention `test_transport_api.py` at all today) alongside S9's, **plus** the widened
   raw-envelope exemption covering the hostile-`Host` / `secure=` / `enforce_csrf_checks=` /
   `AsyncClient` rows S1 added and the in-process `ASGIHandler` driver S2 added.
7. **Slice 3's Low 1** (new this pass) - `test_transport_api.py`'s module-docstring **first
   line**, corrected to the file's actual slice scope **before** the `docs/TREE.md` regenerate.
8. **Slice 3's Low 2** (new this pass) - that module's
   `::test_the_async_package_view_enforces_the_same_utf8_wire_contract` attribution sentence,
   re-worded so it does not claim the strict decode raised for the UTF-8-BOM request.

Plus the non-prose Slice-5 bullets already in the checklist: the migration note, the transport
deployment guidance (with the co-requirement, the concrete directives, and the multipart
carve-out), the `spec-041` amendment, the `docs/GLOSSARY.md` DB + re-render and `docs/TREE.md` /
`README.md` / `TODAY.md` fold-in, the card flip + KANBAN regeneration, and the standing
"no version quintet movement, no `CHANGELOG.md` edit". **Slice 5 is a large pass; it is
enumerated, not remembered.** The two cross-slice DRY items (Slice 2's DRY-1 and the six inline
`await ....post(...)` blocks) are the **integration** pass's, not Slice 5's, and are recorded
above.

