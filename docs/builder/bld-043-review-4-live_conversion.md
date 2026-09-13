# Build: Review round 043 / cohort D — live-tier conversion of the 9 unconverted raw posts

Spec reference: `docs/SPECS/spec-043-test_client-0_0_14.md` (archived), Slice-2 checklist and Decision 11 — **read-only for this cohort**
Build plan: `docs/builder/build-043-test_client-0_0_14.md` `### Decision 3` + `## Ownership partition — correction applied`
Investigation behind the cohort: `docs/builder/bld-043-escalation-3-exemption_declarations.md`
Write set: `examples/fakeshop/test_query/test_error_policy_api.py`, `test_products_visibility_api.py`, `test_relations_async_api.py`, `test_resource_policy_api.py`; this artifact; `docs/builder/worker-memory/043-worker-{1,2,3}.md`
Hot-path declaration: **none** (live test files; nothing runs per request in a deployed schema)
Floor-verification scope: **none** (no Django / Strawberry / channels integration seam changes shape; the conversion moves call sites onto an already-shipped client)
Status: final-accepted

## Plan (Worker 1)

### Census — re-derived, instrument first

Cohort B's V2 and escalation 3 both counted before me. I re-derived rather than
inherited, because a census that samples a vocabulary is the failure this cycle
has already committed twice (`build-043-…md` `## The cycle's instrument
failures`).

**Instrument.** `<scratchpad>/census4.py`, AST over the four owned files (no
grep, no shell loop): every `ast.Call` whose callee is an `ast.Attribute` with
`attr` in `{post, get, put, patch, delete, head, options, trace, generic,
request, login, force_login, logout}`, receiver source segment recorded and
printed for **every** hit — the non-HTTP ones (`payload.get`,
`Model.objects.get`) printed too, so the exclusions are visible rather than
silent. The verb set deliberately includes `generic` (escalation 3's second
blind spot: a raw multipart POST spelled `client.generic("POST", ...)` that no
`.post(` grep can see) and `get` (an operation can ride a GET). A second pass
over the same files greps `CaptureQueriesContext` / `assertNumQueries` /
`captured`, because a query-count block downstream of a converted call is the
one thing a call-site census does not surface.

**Results, per file — HTTP-receiver calls only:**

| File | `.post(` | `.generic(` | `.get(` on a client | other HTTP verbs |
| --- | --- | --- | --- | --- |
| `test_error_policy_api.py` | 2 | 0 | 0 | 1 (`client.force_login`, L514) |
| `test_products_visibility_api.py` | 4 | 0 | 0 | 1 (`client.force_login`, L332) |
| `test_relations_async_api.py` | 1 | 0 | 0 | 0 |
| `test_resource_policy_api.py` | 2 | 0 | 0 | 1 (`client.force_login`, L1020) |
| **total** | **9** | **0** | **0** | 3 |

**The nine are confirmed**, and no tenth spelling exists in these four files:
no `.generic(`, no operation riding a GET, no `RequestFactory`, no
`client.request(`. The three `force_login` calls are credential setup, not
requests, and stay as they are (the live-tier README names
`Client().force_login(user)` as the house form; `TestClient.login()` is a
bracket, not a replacement for a client the test then hands to a helper).

Local helpers wrapping a post — the spelling a call-site count under-reports —
are enumerated rather than counted: `test_error_policy_api.py::_post` (**17**
callers), `test_products_visibility_api.py::_post_async_visibility_query` (1),
`::_post_visibility_query` (5), `test_relations_async_api.py::_post_async` (3),
`test_resource_policy_api.py::_multipart` (1). All five are the
per-file hand-rolled post helper Slice 2 says to delete or route through the
client.

**Corrected at final verification: `::_post` has 17 callers, not the 15 this
paragraph first published.** Worker 3 caught it; I re-derived it rather than
accepting the correction, with an `ast.Call` → `Name("_post")` enumeration over
both `git show HEAD:` and the working tree, which agree: 17 call sites in each
(`test_error_policy_api.py` at HEAD L284, 310, 325, 340, 366, 392, 405, 425,
444, 459, 478, 516, 551, 579, 592, 607, 616). The sentence claiming these
helpers were "enumerated rather than counted" was false of itself — it published
five bare numbers and no member list, which is exactly the shape `BUILD.md`
`## Claims are proven mechanically` says to prefer a re-derivable form over. The
substance is unaffected: no caller changed, and the same enumeration shows 15 of
the 17 pass no `variables` at all and 2 pass a non-empty dict, so the conversion
posts a byte-identical body at every one.

**One correction to escalation 3, measured.** It records "84 test nodes to
re-run (`17 + 8 + 3 + 56`)". The collected node count is **85**:

```
uv run pytest --no-cov -n0 -q --collect-only <each file>
→ 18, 8, 3, 56   (85 together)
```

`test_error_policy_api.py` carries 17 test *functions* but 18 *nodes* —
`::test_an_exception_surfaced_through_value_completion_is_masked_too` is
parametrized into `non-null-completion` / `list-completion`. Any later pass
quoting 84 is quoting a function count as a node count.

**And that total is a self-falsifying instrument: it moved while this plan was
being written.** Between the census above and the end of this pass the
concurrent spec-050 session appended two rows (93 lines, all after L383) to
`test_products_visibility_api.py`, taking it from 8 nodes to **10** and the
four-file total from 85 to **87**. Neither new row posts raw — both drive
`assert_graphql_success`, which already routes through `TestClient` — so the
**nine conversion sites are unchanged** and every line anchor above is
unaffected (the appended rows sit past the last one). The lesson is the count,
not the sites: **Worker 2 re-derives the collected counts with `--collect-only`
at build time and records its own reading**, using the numbers here only as the
plan-time baseline they are. A count of a population someone else is editing is
evidence for the minute it was taken.

**Query-count blocks in the four files (7 `CaptureQueriesContext` sites):**
exactly **one** sits downstream of a site this cohort converts —
`test_products_visibility_api.py::_nested_connection_item_queries` wraps
`_post_visibility_query` (site D5) and feeds
`::test_nested_connection_costs_one_query_per_parent_without_the_optimizer`'s
`== 2` / `== 5` assertions. The other six
(`test_products_visibility_api.py` L336, L366;
`test_resource_policy_api.py` L477, L1076, L1085, L1186/L1200/L1210) wrap
`assert_graphql_success` or `_post` → `graphql_payload`, both of which already
route through `TestClient` at HEAD and are untouched here. Verification plan in
`### Test additions / updates`.

**No exemption survives re-examination.** I re-checked each of the nine against
the spec's four exemption classes (Slice-2 checklist, spec lines 318-325): (a)
hand-built multipart `operations` / `map` assertions, (b) malformed-body
negatives, (c) content-type negotiation, (d) `test_multi_db.py` custom-view
plumbing. None of the nine posts a malformed body or probes a content type;
class (d) has no surviving exemplar (`test_multi_db.py` posts through
`TestClient(client=client).query(...)` at HEAD); and the one class-(a) candidate,
`test_resource_policy_api.py::_multipart`, asserts nothing about labels or map —
see D8, where the map *targets* come out byte-identical. **Zero of the nine are
genuinely exempt.** The governing sentence is the spec's own: a raw post stays
only "when the raw envelope is the test's subject", and "if a conversion would
weaken one, that test takes the exemption instead" — no conversion below weakens
an assertion, so no site earns the carve-out.

### DRY analysis

**Helper inventory checked.** Refreshed package-wide this pass —
`django_strawberry_framework/` in full, not `utils/` — via the `worker-1.md`
AST script, written to `<scratchpad>/helper-inventory.md` (2,080 lines) and
grepped for the shapes this cohort needs: `post(`, `def query`, `multipart`,
`files`, `client`, `graphql_payload`, `TestClient`. Relevant candidates, all
existing, none new: `testing/client.py::TestClient.query`,
`::TestClient.request`, `::TestClient._build_body`,
`::TestClient._assert_file_placeholders`, `::AsyncTestClient.query`,
`::TestClient.login`, `::GraphQLTestMixin.query`. Nothing in the package needs
adding, and nothing in the package is duplicated by this cohort.

**Existing patterns reused.**

- `examples/fakeshop/graphql_client.py::post_graphql(query, *, client=None,
  variables=None, url=None)` — the live tier's shared sync JSON post. It already
  *is* the package client (`result = TestClient(client=client).query(...,
  assert_no_errors=False, url=url)`) and returns the raw `HttpResponse` the
  client stashed on `Response.response`, which is exactly the return contract
  every sync site here wants. Used for **D1, D3, D5**.
- `django_strawberry_framework.testing.AsyncTestClient` — used directly for
  **D2, D4, D6, D7, D9**. `graphql_client.py` is synchronous by construction
  (its own module docstring, and the live-tier README's `Async` bullet), so
  there is no shared async helper to route through.
- `django_strawberry_framework.testing.TestClient` with the path-keyed `files=`
  contract — used for **D8**, the multipart site; `graphql_client.py` carries no
  multipart helper.
- **In-file precedent:** `test_resource_policy_api.py::_post` already delegates
  to `graphql_client.py::graphql_payload`. One of the four files already routes
  its ordinary rows this way; D1/D3/D5 make the other two match it.

**New helpers justified: none.** Every shape these nine sites need already
exists, in the package or in the live tier's own shared module.

**Duplication risk avoided.** The naive conversion — the one escalation 3's
drafts sketch — constructs `TestClient(...)` inside each surviving per-file
helper. That would stand up a third and fourth private copy of the
post-then-decode boilerplate `graphql_client.post_graphql` already owns, in two
files that import from `graphql_client` anyway, and would leave
`test_resource_policy_api.py::_post` (which goes through the shared helper)
inconsistent with its three siblings. Routing every **sync** JSON site through
`post_graphql` keeps one edit site for the live tier's sync post shape; direct
`TestClient` / `AsyncTestClient` use is reserved for the two shapes the shared
module does not cover (async, multipart). Recording the decision here rather
than leaving it to the builder is the point: an undecided shared shape becomes
two copies by construction.

**Cross-cohort shared shapes (Cohorts C and D run concurrently).** Cohort D
authors **no** shape Cohort C needs, and cites `TestClient` / `AsyncTestClient` /
`post_graphql` as **reuse only** — it writes no package source. One real
dependency in the other direction, checked rather than assumed: Cohort C's
Decision-1 respell changes `TestClient._build_body`'s empty-`variables` guard
from `if not variables:` to `if "variables" not in body:`. D8 is this cohort's
only `files=` call and it passes a non-empty
`variables={"d": {"label": "l", "attachment": None, "image": None}}`, so
**neither spelling of that guard can reject it** — the cohorts do not collide
through `client.py` either.

**Variables-truthiness check — corrected at final verification; the original
claim was measured with an instrument that could not see its population.**
`django_strawberry_framework/testing/client.py::TestClient._build_body` emits the
`variables` member under **truthiness** (`if variables:`), so it and an
`is not None` forwarder differ for exactly one input, `variables={}`. Exactly
**one** helper in the four files forwards under `is not None`:
`test_error_policy_api.py::_post` at HEAD (`if variables is not None:
body["variables"] = variables`) — the one D1 converts. The paragraph originally
said "two helpers" and reported a grep of `variables={}` / `variables = {}` /
`variables=dict()` across the four files as **0 occurrences**; both figures are
wrong, and the second is wrong in the way `BUILD.md` `## Claims are proven
mechanically` names — a keyword spelling sampled the vocabulary, not the
population, and an argument passed **positionally** is invisible to it.

Re-derived with an AST enumeration of every empty-`ast.Dict` argument, keyword
or positional, at every call in the four files, run against `git show HEAD:`
copies and the working tree alike. Both readings return **one** occurrence:

```examples/fakeshop/test_query/test_resource_policy_api.py:522
    extensions = _rejection(_post("/rp-values/", query, {}))
```

`test_resource_policy_api.py::_post`'s signature is
`(mount, query, variables=None, *, client=None)`, so that bare `{}` is
`variables`. **Consequence nil, and for a reason the corrected instrument shows
rather than argues:** that helper already delegated to
`graphql_client.py::graphql_payload` → `::post_graphql` → `TestClient` at HEAD,
byte-identically to the working tree, so truthiness has governed that call since
before this cohort existed — which is also what the row wants, its subject being
a variable **omitted** from the envelope
(`::test_variable_default_value_in_operation_header_is_rejected_when_omitted`).
The nine converted sites are unaffected: the 17 callers of the converted
`test_error_policy_api.py::_post` pass `None` (15 of them) or a non-empty dict
(2), and D8 / D9 pass non-empty dicts, so every converted site posts a
byte-identical body.

### Boundary count and the split question

**New boundaries introduced: 0.** This cohort adds no guard, cap, rejection
path, or validation branch; it moves nine call sites onto an already-shipped
client and deletes one local helper. `BUILD.md` `### Slice splitting` asks the
question anyway: **no split.** The nine sites are one decision — the same
conversion rule applied four times — three of the four files are under 630
lines, and splitting would cost four artifacts and four full worker cycles to
review nine mechanical edits. Worker 2's `### Failability proofs` subsection
reads `None; this pass introduced no new boundary.`

### Implementation steps

Line numbers are pin-at-write-time navigational hints — verify against the
current source before editing; a concurrent session is active in this tier
(`test_products_visibility_api.py` and `test_resource_policy_api.py` were
committed by it on 2026-09-12, and it appended two more rows to the first of
those **during this planning pass**).

**Three of the four files were clean against HEAD at census time;
`test_products_visibility_api.py` is now dirty with the concurrent cycle's
appended rows** (93 lines after L383, none of them a raw post). A dirty file is
therefore **not** by itself a stop-and-report here — that rule would deadlock
the cohort against an active session. The rule is narrower: before editing each
file, write `git show HEAD:<path>` into the session scratchpad and diff it, and
**stop and report only if the working tree differs from HEAD inside a region
this plan converts**. Someone else's appended rows elsewhere in the file are
out-of-scope work to leave exactly alone (`AGENTS.md` rule 34) — never revert,
never `git checkout`, never `git stash`.

**Baseline-dirty reading at plan time, and it has grown since the build plan's.**
`git status --short` shows 15 modified paths plus the cycle's own untracked
artifacts. Beyond the six the build plan recorded, the concurrent spec-050 cycle
is now dirty in `django_strawberry_framework/connection.py`, `keyset.py`,
`list_field.py`, `optimizer/nested_planner.py`, `optimizer/walker.py`,
`orders/sets.py`, `tests/test_connection.py`, `tests/test_keyset_connection.py`,
and Cohort C is dirty in `docs/SPECS/spec-043-test_client-0_0_14.md`. **None of
the four owned files is among them.** Worker 2's post-ruff
`git status --short` check will therefore show a long list it did not cause:
that is expected and is neither a stop-and-report nor anything to revert — the
check is that no file *outside* `### Files touched` changed **because of this
pass**. Attribute by diff content, never by the dirty list, and never
`git checkout` any of them.

Three rules govern every step below:

1. **No assertion changes.** Not the text, not the operator, not the value, not
   which line owns it. If a conversion cannot land without touching one, stop
   and report — that is the site taking the exemption, and it is a plan-level
   call, not a builder's.
2. **`assert_no_errors=False` everywhere.** `TestClient.query()` defaults to
   `True` and *raises* `AssertionError(response.errors)` on a GraphQL `errors`
   key. Most rows in these files expect an error envelope, so a default-`True`
   conversion turns a passing row into a raise. Even where no error is expected
   (D3, D4, D7), `False` is still required: the row already carries its own
   `assert payload.get("errors") is None, payload`, and letting the client raise
   first would silently relocate that assertion into the helper and change what
   a failure reports. `post_graphql` hard-codes `assert_no_errors=False`, so
   D1/D3/D5 pass nothing; D2/D4/D6/D7/D8/D9 pass it explicitly.
3. **Every call names its mount with `url=`.** Never rely on the client's
   default endpoint. `conf.py::testing_endpoint_setting` defaults to
   `"/graphql/"` and fakeshop sets no `TESTING_ENDPOINT`, so the default would
   *work* for the two `/graphql/` sites — and would couple a row that mounts its
   own `ROOT_URLCONF` to a project-wide setting it never names. Per-call `url=`
   is Decision 7's mechanism for exactly a one-call test mount.

#### `examples/fakeshop/test_query/test_error_policy_api.py` (18 nodes)

**D1 — `::_post` (L223-240), 17 call sites** (corrected at final verification
from 15; see `### Census`). Replace the body's three lines
(`body = {...}` / `if variables is not None` / `response = (client or
Client()).post(...)`) with one call; keep the signature, the docstring, the
status assert **with its `, response.content` message**, and the
`(response, payload)` return tuple, so all 17 callers are untouched:

```python
    response = post_graphql(query, client=client, variables=variables, url=mount)
    assert response.status_code == 200, response.content
    return response, response.json()
```

- `client=` forwards a caller's pre-configured Django client unchanged
  (`::test_a_field_error_envelope_is_untouched_because_it_is_data_not_an_error`
  passes a `force_login`-ed `Client()`, L513-528); `post_graphql` hands it to
  `TestClient(client=client)`, so session state rides along.
- `response.json()` is **load-bearing** and must not become `res.data` /
  `res.errors`: L530 asserts `"errors" not in payload`, which is a statement
  about a *decoded dict key*. The typed `Response` always carries an `errors`
  attribute, so rebuilding the payload from it would silently invert that
  assertion.
- Add `from graphql_client import post_graphql`; drop `AsyncClient` from the
  `django.test` import once D2 lands (`from django.test import Client` — `Client`
  survives at L513).
- **Module docstring, L5:** "over ``django.test.Client`` against mounts of the
  package's own Django GraphQL view" is falsified by this diff — after D1/D2 the
  module drives no bare `django.test.Client` at all. Restate it to name the
  package's own test client (which posts *over* `django.test.Client`). This is
  the live tier's authoritative per-module description, so a false clause here
  is a real defect, not a cosmetic one.

**D2 — `::test_the_sync_and_async_transports_produce_the_same_masked_entry`
(L554-559).** The async half of a parity row: subject is the masked *entry*, not
the envelope. `AsyncClient().post(...)` produces a coroutine handed to
`_await_response` (`asyncio.run`); `AsyncTestClient().query(...)` is a coroutine
the same way, so the surrounding shape is unchanged:

```python
    async_response = _await_response(
        AsyncTestClient().query(
            "{ boom fine }",
            assert_no_errors=False,
            url="/ep-async/",
        ),
    )
    async_payload = json.loads(async_response.response.content)
```

- Keep `json.loads(...content)` rather than `.json()`: identical result, one
  fewer edited token, and `json` stays imported for L594 / L621 regardless.
- `_await_response`'s docstring (L261) says "Run one ``AsyncClient`` coroutine";
  after this site it awaits an `AsyncTestClient.query` coroutine. Restate it to
  describe what it now runs.
- Add `from django_strawberry_framework.testing import AsyncTestClient`.
- Test posture unchanged: `@pytest.mark.django_db`, sync test body,
  `asyncio.run` inside `_await_response` — the conversion introduces no new
  event-loop interaction.

#### `examples/fakeshop/test_query/test_products_visibility_api.py` (8 nodes)

**D3 — `::test_unoptimized_relation_hides_private_child_over_http` (L61-65).**
Inline sync post against the module's own `/graphql/` holder mount, inside
`override_settings(ROOT_URLCONF=__name__)`:

```python
            response = post_graphql(
                "{ categories { items { name } } }",
                url="/graphql/",
            )
```

The document text is the same string the hand-spelled JSON body carried. L66-69
(`status_code`, `payload.get("errors") is None`, the exact `data` equality) are
untouched.

**D4 — `::_post_async_visibility_query` (L95-108), 1 caller.** Keep the helper's
contract — it returns a raw `HttpResponse` and its caller (L112-118) asserts
`status_code` then `.json()` — so the caller needs no edit:

```python
            res = await AsyncTestClient().query(
                "{ categories { items { name } } }",
                assert_no_errors=False,
                url="/graphql-async/",
            )
            return res.response
```

The `await` stays **inside** the `override_settings` / `clear_url_caches`
bracket, as today: the mount only resolves while the override is active. The
`try` / `finally` that resets `_CURRENT["schema"]` is untouched.

**D5 — `::_post_visibility_query` (L121-136), 5 callers.** One-line body swap;
the status assert stays outside the `with` block where it is now, and
`response.json()` stays the return:

```python
            response = post_graphql(query, url="/graphql/")
```

- Callers untouched, including
  `::test_forward_fk_target_visibility_holds_with_the_optimizer_installed`,
  which asserts on `optimized["errors"]` message text and on
  `optimized["errors"] == unoptimized["errors"]` — both read the decoded dict,
  both preserved.
- **This is the query-count site.** `::_nested_connection_item_queries` wraps
  this helper in `CaptureQueriesContext` and its caller asserts exactly 2 and
  exactly 5 `products_item` queries at two parent cardinalities. The client adds
  no query — `TestClient()` construction builds a `django.test.Client` and
  touches no database — but that is a reading, and the assertion is the
  cardinality-pair shape `BUILD.md` `### Query-shape tests must pin the
  load-bearing property` exists to protect. Execute it (see
  `### Test additions / updates`) and record the counts before and after.

**D6 — `::test_async_forward_fk_target_visibility_hides_a_private_target_over_http`
(L250-254).** Inline async post; assign inside the bracket, assert after the
`finally`, exactly as now:

```python
            res = await AsyncTestClient().query(
                "{ items { name category { name } } }",
                assert_no_errors=False,
                url="/graphql-async/",
            )
            response = res.response
```

L258-263 (`status_code`, `data is None`, the exact
`"Cannot return null for non-nullable field ItemType.category."` message list)
are untouched.

**Imports after D3-D6:** add `post_graphql` to the existing
`from graphql_client import assert_graphql_success` line; add
`from django_strawberry_framework.testing import AsyncTestClient`; drop
`AsyncClient` from the `django.test` import (`Client` survives at L331,
`override_settings` throughout); **delete `import json`** — L129 and L252 were
its only module-level uses (L67 / L116 / L133 / L259 are
`response.json()` method calls, not the module). Ruff's `F401` will confirm.

#### `examples/fakeshop/test_query/test_relations_async_api.py` (3 nodes)

**D7 — `::_post_async` (L89-104), 3 callers.** The module's only request site:

```python
            res = await AsyncTestClient().query(
                query,
                assert_no_errors=False,
                url="/graphql-async/",
            )
        assert res.response.status_code == 200
        return res.response.json()
```

- The module docstring is explicit that `errors is None` plus an exact `data`
  match **is** the regression assertion and that "weakening either half to a
  bare status check discards the point of the suite". All three callers keep
  both halves; `assert_no_errors=False` is what makes that possible.
- Posture already correct for an async live row: every test is
  `@pytest.mark.django_db(transaction=True)` and native-async, matching the
  live-tier README's `Async` bullet.
- Imports: `from django.test import AsyncClient, override_settings` →
  `from django.test import override_settings`; **delete `import json`** (L97 was
  its only module-level use; L101 is a method call); add
  `from django_strawberry_framework.testing import AsyncTestClient`.
- Module docstring needs no change: it describes the mount and the visibility
  constraints, and names no client.

#### `examples/fakeshop/test_query/test_resource_policy_api.py` (56 nodes)

**D8 — `::_multipart` (L905-919) deleted; its one caller rewritten
(L936-944).** The spec requires the local helper **deleted** where the client's
contract covers it, and here it does: `TestClient`'s path-keyed `files=` builds
the `operations` / `map` envelope the helper hand-rolled.

```python
    res = TestClient().query(
        _SPECIMEN,
        variables={"d": {"label": "l", "attachment": None, "image": None}},
        files={
            "d.attachment": SimpleUploadedFile("attachment.bin", b"z" * 200),
            "d.image": SimpleUploadedFile("image.bin", b"z" * 200),
        },
        assert_no_errors=False,
        url="/rp-uploads/",
    )
    assert res.response.status_code == 200, res.response.content
    extensions = _rejection(res.response.json())
```

Why the row's outcome is preserved, stated so review can check it rather than
take it:

- **The `map` targets come out byte-identical.** The hand-rolled envelope mapped
  labels `"0"` / `"1"` to `["variables.d.attachment"]` /
  `["variables.d.image"]`. `TestClient._build_body` emits
  `map[key] = ["variables." + key]` for each `files` key, so
  `"d.attachment"` → `["variables.d.attachment"]` and `"d.image"` →
  `["variables.d.image"]`. Only the multipart **field label** changes; what the
  server binds, and where, does not.
- **The bound is label-agnostic.** `extensions/resource_policy.py::_ValueBudget.
  _charge_upload` charges each file *value* as the variable tree is walked —
  count, then per-file `size`, then the aggregate. The mount's bounds are
  `max_upload_count=1`, `max_upload_file_bytes=64`,
  `max_upload_total_bytes=96`; two 200-byte files trip
  `max_upload_file_bytes` on the first value charged, before and after. The
  assertion is `bound in {max_upload_count, max_upload_file_bytes,
  max_upload_total_bytes}`, which holds on any of the three.
- **Placeholders are already correct:** `variables["d"]["attachment"]` and
  `["image"]` are `None`, which is what `_assert_file_placeholders` walks to.
- **This is the one row escalation 3 could not settle from evidence**
  ("unverified by execution"). It is a **must-run** for Worker 2 — see
  `### Test additions / updates`. If the observed `bound` changes, stop and
  report: that is a finding about the charger, not a licence to widen the
  assertion set.
- `Client` stays imported (L1019); `SimpleUploadedFile` stays imported (used
  here); the deleted helper takes L914-915's `json.dumps` calls with it.

**D9 — `::test_sync_and_async_transports_share_one_typed_error_code`
(L1250-1256).** Same shape as D2 — a sync test awaiting one async post through
`_await_response`:

```python
    async_response = _await_response(
        AsyncTestClient().query(
            _NODES,
            variables=variables,
            assert_no_errors=False,
            url="/rp-values-async/",
        ),
    )
    async_payload = json.loads(async_response.response.content)
```

- `_rejection(async_payload) == sync_extensions` (L1257) is untouched; the
  decoded dict is what it compares.
- Keeping `json.loads(...content)` also keeps `import json` live after D8
  removes its other two uses — check with ruff rather than by reading.
- `_await_response`'s docstring (L1261) carries the same
  "``AsyncClient`` coroutine" wording as D2's; restate it the same way.
- Imports: `from django.test import AsyncClient, Client, override_settings` →
  `from django.test import Client, override_settings`; add
  `from django_strawberry_framework.testing import AsyncTestClient, TestClient`.
- **Module docstring left alone.** Its "over ``django.test.Client``" clause
  (L5-6) describes the sync rows, which already route
  `_post` → `graphql_payload` → `TestClient` → `django.test.Client` at HEAD;
  this cohort's diff does not falsify it, and rewriting it would be scope this
  cohort did not earn. Recorded so the omission reads as a decision.

#### Formatting and layout

- `AGENTS.md` rule 16 after every edit, **scoped to the four owned paths**:
  `uv run ruff format <four paths>` then `uv run ruff check --fix <four paths>`.
  Never a bare `.` — this tree carries a concurrent session's untracked work.
- `AGENTS.md` rule 17: line length 99, and the trailing-comma
  explode-at-threshold layout (threshold 4) means **any call with four or more
  arguments is written one-argument-per-line with a trailing comma** — D8 (six)
  and every `AsyncTestClient().query(...)` with three-plus arguments included.
  `uv run python scripts/check_trailing_commas.py <four paths>` with **explicit
  paths** is authoritative; its bare default is a repo-wide auto-fix that would
  rewrite the concurrent session's files.
- ASCII-only `.py` source: the conversions introduce no non-ASCII.

### Test additions / updates

**No new tests.** The spec's Slice-2 obligation is explicitly "verification, not
new tests": every converted file passes with assertions unchanged and
`CaptureQueriesContext` counts unchanged. Nine call sites move; 85 nodes must
still pass and must still be 85.

**Authorized runs, and why each.** `AGENTS.md` rule 15 and the spec both say the
implementation worker records the commands rather than running the suite. A
*focused* run confirming a conversion is inside the builder's normal latitude,
and this plan **authorizes** the following, all `--no-cov` (required:
`pytest.ini`'s `addopts` auto-applies `--cov`) and with no other coverage-shaped
flag anywhere:

1. **Baseline, before the first edit** — the four module runs below, recorded
   green (or with the failing node ids named). The tree is concurrently dirty;
   without a pre-edit baseline a pre-existing failure gets attributed to this
   conversion.
2. **The four module runs, after the edits:**
   ```shell
   uv run pytest --no-cov -n0 examples/fakeshop/test_query/test_error_policy_api.py
   uv run pytest --no-cov -n0 examples/fakeshop/test_query/test_products_visibility_api.py
   uv run pytest --no-cov -n0 examples/fakeshop/test_query/test_relations_async_api.py
   uv run pytest --no-cov -n0 examples/fakeshop/test_query/test_resource_policy_api.py
   ```
   Record the **collected count** from each, not only pass/fail. The plan-time
   reading was 18 / 8 / 3 / 56, already superseded for the second file (10 after
   the concurrent append). So the check is **not** "matches this plan": it is
   **the count from the baseline run in step 1 equals the count from the same
   command after the edits**. A count that drops between the two means a node
   vanished in this diff — a deleted or un-collected test reads as a green run.
3. **The must-run row — D8's multipart conversion**, the one escalation 3 left
   unverified by execution. Record the observed `extensions["bound"]`:
   ```shell
   uv run pytest --no-cov -n0 \
     "examples/fakeshop/test_query/test_resource_policy_api.py::test_an_oversized_upload_is_rejected_by_the_policy_not_by_the_body_cap"
   ```
4. **The must-run query-count row — D5's downstream assertion:**
   ```shell
   uv run pytest --no-cov -n0 \
     "examples/fakeshop/test_query/test_products_visibility_api.py::test_nested_connection_costs_one_query_per_parent_without_the_optimizer"
   ```
   `-n0` deliberately: the counts are read off one connection, and a
   single-process run is the unambiguous reading. Record that the row asserts
   2 at two parents and 5 at five, unchanged.
5. **One combined run under the repo's default parallel settings**, to catch a
   `--dist loadscope` / module-order effect a `-n0` run cannot see:
   ```shell
   uv run pytest --no-cov examples/fakeshop/test_query/test_error_policy_api.py \
     examples/fakeshop/test_query/test_products_visibility_api.py \
     examples/fakeshop/test_query/test_relations_async_api.py \
     examples/fakeshop/test_query/test_resource_policy_api.py
   ```
   Must collect the same total as the combined baseline run (87 at the end of
   this planning pass, and a moving number while the concurrent session works in
   this tier).

**Not authorized here:** the full `uv run pytest --no-cov` sweep. That is the
cycle's final gate (`docs/builder/bld-043-final.md`), and running it from this
cohort would produce a reading nobody owns while the concurrent session and
Cohort C are both writing.

**Temp tests:** none needed. Worker 3 may still write one under
`docs/builder/temp-tests/043/` to demonstrate that a converted assertion is
non-distinguishing — the likeliest candidate is D1's `"errors" not in payload`
at L530, where the decoded-dict reading is what makes the assertion real.

**Failability proofs:** none owed — this pass introduces no boundary. Worker 2
writes `None; this pass introduced no new boundary.` under
`### Failability proofs` and keeps the heading.

### Implementation discretion items

Assessed and delegated to Worker 2; none is architectural:

- Local variable names at the converted sites (`res` vs `response` vs
  `async_response`), as long as the assertions below them read unchanged.
- Where the new imports land in each file's import block — ruff's isort decides
  it; do not hand-place them.
- The `SimpleUploadedFile` filenames at D8 (`"attachment.bin"` /
  `"image.bin"`, or any pair). Nothing asserts on the filename; only the byte
  count and the file count reach the bound.
- Exact wording of the two `_await_response` docstring restatements and of
  `test_error_policy_api.py`'s module-docstring clause, provided each states
  what the code now does and neither narrates the change
  (`AGENTS.md` "No process provenance in code or standing prose": no
  "previously", no "converted in", no round or cohort attribution).

### Dispatched findings checklist

Nine conversion sites (D1-D9) from `bld-043-review-2-code_verification.md` M4 as
re-derived by `bld-043-escalation-3-exemption_declarations.md` `## 2` and decided
by `build-043-test_client-0_0_14.md` `### Decision 3`, plus four per-file closure
boxes (C1-C4). Boxes stay `- [ ]` at planning; Worker 2 ticks only what landed in
its diff and states any deferral in the build report; Worker 3 walks the list;
Worker 1 audits every tick at final verification.

- [x] **D1** — `examples/fakeshop/test_query/test_error_policy_api.py::_post`: route through `graphql_client.py::post_graphql` (`client=`, `variables=`, `url=mount`), keep the signature, the `status_code == 200, response.content` assert and the `(response, response.json())` return; all 17 callers untouched (the box read "15" until final verification re-derived the count); module-docstring client clause restated.
- [x] **D2** — `test_error_policy_api.py::test_the_sync_and_async_transports_produce_the_same_masked_entry`: `AsyncClient().post(...)` → `AsyncTestClient().query("{ boom fine }", assert_no_errors=False, url="/ep-async/")` inside `_await_response`; `json.loads(...response.content)` kept; `_await_response` docstring restated.
- [x] **D3** — `test_products_visibility_api.py::test_unoptimized_relation_hides_private_child_over_http`: inline `Client().post(...)` → `post_graphql("{ categories { items { name } } }", url="/graphql/")`; L66-69 assertions untouched.
- [x] **D4** — `test_products_visibility_api.py::_post_async_visibility_query`: `AsyncClient().post(...)` → `await AsyncTestClient().query(..., assert_no_errors=False, url="/graphql-async/")`, returning `res.response` so the caller is untouched; await stays inside the `override_settings` bracket.
- [x] **D5** — `test_products_visibility_api.py::_post_visibility_query`: `Client().post(...)` → `post_graphql(query, url="/graphql/")`; 5 callers untouched; the downstream `CaptureQueriesContext` counts (2 at two parents, 5 at five) re-verified by execution and recorded.
- [x] **D6** — `test_products_visibility_api.py::test_async_forward_fk_target_visibility_hides_a_private_target_over_http`: inline `AsyncClient().post(...)` → `await AsyncTestClient().query(..., assert_no_errors=False, url="/graphql-async/")`; the exact non-null-message list assertion untouched.
- [x] **D7** — `test_relations_async_api.py::_post_async`: `AsyncClient().post(...)` → `await AsyncTestClient().query(query, assert_no_errors=False, url="/graphql-async/")`; `errors is None` + exact `data` kept in all 3 callers; `import json` and the `AsyncClient` import dropped.
- [x] **D8** — `test_resource_policy_api.py::_multipart` **deleted**; its caller `::test_an_oversized_upload_is_rejected_by_the_policy_not_by_the_body_cap` rewritten onto `TestClient().query(_SPECIMEN, variables=..., files={"d.attachment": ..., "d.image": ...}, assert_no_errors=False, url="/rp-uploads/")`; the row **executed** and the observed `extensions["bound"]` recorded.
- [x] **D9** — `test_resource_policy_api.py::test_sync_and_async_transports_share_one_typed_error_code`: `async_client.post(...)` → `AsyncTestClient().query(_NODES, variables=variables, assert_no_errors=False, url="/rp-values-async/")` inside `_await_response`; `_rejection(async_payload) == sync_extensions` untouched; `_await_response` docstring restated.
- [x] **C1** — `test_error_policy_api.py` closure: imports swept (`AsyncClient` dropped, `post_graphql` / `AsyncTestClient` added, `json` and `Client` still used), ruff format + check clean, `check_trailing_commas.py` clean on the explicit path, module run passes and collects its own pre-edit baseline count (18 at plan time).
- [x] **C2** — `test_products_visibility_api.py` closure: imports swept (`AsyncClient` and `import json` dropped, `post_graphql` / `AsyncTestClient` added, `Client` still used at the `force_login` row), ruff + trailing-comma clean, module run passes and collects its own pre-edit baseline count (10 at the end of the planning pass, after the concurrent append), and the concurrent session's appended rows are untouched.
- [x] **C3** — `test_relations_async_api.py` closure: imports swept (`AsyncClient` and `import json` dropped, `AsyncTestClient` added), ruff + trailing-comma clean, module run passes and collects its own pre-edit baseline count (3 at plan time).
- [x] **C4** — `test_resource_policy_api.py` closure: imports swept (`AsyncClient` dropped, `TestClient` / `AsyncTestClient` added, `json` / `Client` / `SimpleUploadedFile` still used), ruff + trailing-comma clean, module run passes and collects its own pre-edit baseline count (56 at plan time); combined four-file parallel run passes and collects the combined baseline count (87 at the end of the planning pass).

### Notes for Worker 1 (spec reconciliation)

This cohort writes **no spec text** — the spec and its rationale are Cohort C's
alone. Everything below is routed to Cohort C's custodian or, where noted, to
Worker 0, because it falls outside every cohort's write set.

1. **`examples/fakeshop/test_query/README.md` is falsified by this cohort's diff,
   and belongs to no cohort.** Its `## Clients, transports, credentials`
   `Async` bullet reads: "`test_list_field_async_api.py`,
   `test_relations_async_api.py`: `django.test.AsyncClient` vs an
   `AsyncDjangoGraphQLView` mount. Async rows: `@pytest.mark.django_db(transaction=True)`,
   declare the helper exemption …". After D7, `test_relations_async_api.py`
   drives `AsyncTestClient` and declares no exemption; after D4/D6 the same is
   true of `test_products_visibility_api.py`'s async rows. The README is in
   **no** cohort's write set — the identical ownership gap escalation 3 found
   for these four `.py` files. **Worker 0 decision needed:** name an owner (fold
   it into the cross-cohort integration pass, or extend a cohort's write set).
   `START.md` `## Past mistakes` — an item routed forward without a named owner
   dies — and the README is the live tier's own manual, so a stale routing
   sentence there is what produces the next round of drift.
2. **Spec class (d) removal is Cohort C's, and it has more sites than Decision 3
   names.** The "`test_multi_db.py` custom-view plumbing" exemption class, and
   the surrounding exemption sentence, appear at the Slice-2 checklist
   (spec L318-325), in Decision 11's "switchover's own discipline" paragraph
   (L1435-1442), in `## Test plan` ("each retained raw `client.post(...)` carries
   the wire-shape-exemption comment", L1846-1848), and in the Definition of done
   (L2035-2040). Cohort C sweeps all four, not only Decision 11 and the
   checklist. After this cohort lands there is **no** retained raw
   `client.post(...)` in these four files, so the Test-plan and DoD sentences
   need to describe the exemption as one no live file currently claims outside
   `test_products_api.py`, `test_transport_api.py`, `test_auth_api.py` and
   `graphql_client.py::post_graphql_raw`.
3. **Node-count correction to escalation 3, and a warning about the correction.**
   Its "84 test nodes to re-run (`17 + 8 + 3 + 56`)" is a function count, not a
   node count: collected at census time it was 18 / 8 / 3 / 56 = **85**. By the
   end of this pass the concurrent spec-050 session had appended two rows to
   `test_products_visibility_api.py` and it was **87**. So the durable finding is
   not the number — it is that **this population is live and no artifact should
   publish a fixed total for it**. Any pass that needs one measures it with
   `--collect-only` and states when.
4. **Artifact-name discrepancy, recorded so nobody hunts the other file.**
   Escalation 3 `## Recommendation` step 1 names
   `bld-043-review-4-live_post_conversion.md`; the applied partition
   (`build-043-test_client-0_0_14.md` `## Ownership partition — correction
   applied`) and the dispatch name **`bld-043-review-4-live_conversion.md`**,
   which is this file. The partition table wins.
5. **A shared async live-tier post helper is the missing shape, and no cohort can
   author it.** After this pass, five near-identical
   `await AsyncTestClient().query(..., assert_no_errors=False, url=...)` bodies
   live in four live modules (D2, D4, D6, D7, D9), plus a sixth in
   `test_list_field_async_api.py` once the spec-050 cycle converts it. The right
   home is an async twin of `graphql_client.py::post_graphql` — but
   `graphql_client.py` is declared sync-only and sits in no cohort's write set,
   so this cohort deliberately does not extract it. **Condition that would
   justify extraction:** a sixth async site, or any change to the async call
   shape. Needs a named owner card (escalation 3 nominates
   `TODO-ALPHA-053-0.0.15` for the sibling gate item; the same card is the
   natural home).
6. **The root-cause fix is still a gate, still unowned.** Nothing in `scripts/`
   or `.pre-commit-config.yaml` fails a raw `.post(` / `.generic(` on a Django
   client in `test_query/` that carries no `spec-043` declaration. Five files
   drifted in two months precisely because no gate exists
   (`START.md` "Rule w/o gate rots"). Out of this cohort's fence; recorded again
   here because escalation 3's routing of it to a KANBAN card requires a DB edit
   no worker's fence covers.
7. **`test_resource_policy_api.py`'s module docstring keeps its "over
   ``django.test.Client``" clause**, deliberately: this cohort's diff does not
   falsify it (its sync rows already route through `TestClient` at HEAD via
   `graphql_payload`). Recorded so a later reader does not read the untouched
   clause as an oversight.
8. **The applied partition gives Cohorts C and D the same three memory files.**
   `docs/builder/worker-memory/043-worker-{1,2,3}.md` appear in **both** write
   sets, and C's Worker 1 planning entry landed in `043-worker-1.md` between this
   pass's read and its write. `BUILD.md` `### Parallel cohorts under a declared
   ownership partition` says one shared file is enough to serialize two cohorts —
   the partition survives only because these files are append-only scratch, never
   read by the other cohort. Two consequences, recorded rather than assumed:
   the ~50-line consolidation cap in `### Worker memory` is **unsafe** while two
   cohorts share the file (consolidating rewrites the other cohort's entry), so
   this pass appended and did not consolidate; and a future partition should give
   each cohort its own memory stem. Worker 0's call.

## Build report (Worker 2)

### Files touched

Grounded in `git status --short` after both ruff invocations.

- `examples/fakeshop/test_query/test_error_policy_api.py` — D1 (`::_post` routed through
  `graphql_client.py::post_graphql`), D2 (`AsyncTestClient` inside `_await_response`),
  `AsyncClient` import dropped, `post_graphql` / `AsyncTestClient` added, module-docstring
  client clause and `::_await_response` docstring restated.
- `examples/fakeshop/test_query/test_products_visibility_api.py` — D3 / D4 / D5 / D6;
  `import json` and the `AsyncClient` import dropped, `post_graphql` folded into the existing
  `graphql_client` import, `AsyncTestClient` added.
- `examples/fakeshop/test_query/test_relations_async_api.py` — D7; `import json` and the
  `AsyncClient` import dropped, `AsyncTestClient` added.
- `examples/fakeshop/test_query/test_resource_policy_api.py` — D8 (`::_multipart` **deleted**,
  its one caller rewritten onto `TestClient().query(..., files=...)`), D9;
  `AsyncClient` import dropped, `TestClient` / `AsyncTestClient` added,
  `::_await_response` docstring restated.
- `docs/builder/bld-043-review-4-live_conversion.md` — this report; D1-D9 and C1-C4 ticked.
- `docs/builder/worker-memory/043-worker-2.md` — memory entry appended.
- `docs/builder/temp-tests/043/test_upload_bound_probe.py`,
  `docs/builder/temp-tests/043/test_upload_bound_head_probe.py` — untracked scratch probes
  (see `### Notes for Worker 3`).

**Everything else in `git status --short` is concurrent work this pass did not cause**, left
exactly alone per `AGENTS.md` rule 34, attributed by diff content: Cohort C
(`django_strawberry_framework/conf.py`, `testing/client.py`, `tests/testing/test_client.py`,
`examples/fakeshop/test_query/test_client_api.py`, `docs/SPECS/spec-043-test_client-0_0_14.md`
and its untracked rationale companion); the live spec-050 cycle
(`connection.py`, `keyset.py`, `list_field.py`, `optimizer/nested_planner.py`,
`optimizer/walker.py`, `orders/sets.py`, `docs/spec-050-list_field_arguments-0_0_15.md`,
`tests/test_connection.py`, `tests/test_keyset_connection.py`, `tests/test_list_field.py`,
`tests/optimizer/test_walker.py`, `tests/orders/test_sets.py`,
`examples/fakeshop/test_query/test_keyset_api.py`, untracked
`examples/fakeshop/test_query/test_zz_probe_api.py`); and the baseline-dirty set
(`START.md`, `examples/fakeshop/apps/kanban/tests/test_mutations.py`,
`examples/fakeshop/db.sqlite3`, `docs/GLOSSARY.md`, `docs/TREE.md`, and the maintainer
review-input file `AGENTS.md` rule 4 forbids naming). No revert, no `git checkout`, no stash.

**The one owned file that was dirty against HEAD stayed dirty in someone else's hunk only.**
`git diff -U0` on `test_products_visibility_api.py` before the first edit showed exactly one
hunk, `@@ -383,0 +384,93 @@` — the concurrent session's two appended rows, outside every
region D3-D6 converts. After this pass the same file's hunk headers are the import block plus
D3 / D4 / D5 / D6, and that `+93` append is still present, byte-for-byte untouched. The other
three owned files were clean against HEAD at first edit.

### Tests added or updated

**None added.** The spec's Slice-2 obligation is verification, not new tests: nine call sites
moved, every assertion text, operator, value and owning line unchanged, and the collected node
count identical before and after. No assertion was weakened to land a conversion, and no site
took an exemption.

### Validation run

All four owned paths passed explicitly on every invocation; never a bare `.`, and no
`--cov*` flag anywhere.

- `uv run ruff format <the four owned paths>` — pass (`4 files left unchanged`).
- `uv run ruff check --fix <the four owned paths>` — pass (`All checks passed!`); no `F401`,
  which is the mechanical confirmation that the dropped `AsyncClient` / `json` imports were
  the last uses and that the surviving `Client` / `json` / `SimpleUploadedFile` still are.
- `uv run python scripts/check_trailing_commas.py <the four owned paths>` — pass
  (`Fixed 0 file(s).`), explicit paths so the concurrent session's untracked files were not
  rewritten.
- `git status --short` after both ruff invocations — classified above; every modified file is
  either slice-intended or pre-existing concurrent work. No stop-and-report.

**Node-count instrument — my own before-and-after pair, never a number quoted from an earlier
artifact.**

| Module | pre-edit collected | post-edit collected |
| --- | --- | --- |
| `test_error_policy_api.py` | 18 | 18 |
| `test_products_visibility_api.py` | 10 | 10 |
| `test_relations_async_api.py` | 3 | 3 |
| `test_resource_policy_api.py` | 56 | 56 |
| **combined** | **87** | **87** |

Pre-edit baseline, taken before the first edit:
`uv run pytest --no-cov -n0 <the four modules> -q` → `collected 87 items`, `87 passed`;
per-module `--collect-only` → 18 / 10 / 3 / 56. The count did not move across the pass, so no
node vanished into a green run.

Authorized runs, all `--no-cov`:

1. Pre-edit baseline (above) — 87 collected, 87 passed.
2. Per-module `uv run pytest --no-cov -n0 <module>` after the edits —
   18 / 10 / 3 / 56, **all passed**.
3. Must-run D8:
   `uv run pytest --no-cov -n0 "…/test_resource_policy_api.py::test_an_oversized_upload_is_rejected_by_the_policy_not_by_the_body_cap"`
   — **1 passed**. Observed rejection, read through a scratch probe because the live row
   asserts set membership and a green run does not say which bound tripped:
   `{'code': 'RESOURCE_LIMIT_EXCEEDED', 'bound': 'max_upload_file_bytes', 'limit': 64,
   'charged': 200}`. The HEAD-shaped hand-rolled envelope (numeric `"0"` / `"1"` labels, the
   same two map targets) reports the **identical** dict from the identical mount, so the bound
   is label-agnostic as measured, not as argued. Escalation 3's "unverified by execution" row
   is now verified, and nothing widened.
4. Must-run D5 query-count:
   `uv run pytest --no-cov -n0 "…/test_products_visibility_api.py::test_nested_connection_costs_one_query_per_parent_without_the_optimizer"`
   — **1 passed**. The row's assertions are absolute, not equality-only —
   `len(_nested_connection_item_queries(2)) == 2` and `… (5)) == 5` — and both hold unchanged,
   so the transport swap moved no query boundary.
5. Combined four-file run under the repo's default parallel settings
   (`uv run pytest --no-cov <the four modules>`) — `8 workers [87 items]`, **87 passed**. Same
   total as the combined baseline, so no `--dist loadscope` / module-order effect.

The full sweep was **not** run: it is the cycle's final gate.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **`res` for the typed `Response`, `response` for a raw `HttpResponse`.** Where a converted
  site kept a helper's raw-response contract (D4, D6) the typed result is bound to `res` and
  the raw one to `response`, so every assertion below reads exactly as it did. D7 needed no
  local at all — `res.response.status_code` / `res.response.json()` are the two uses.
- **D4's `return res.response` sits inside the `override_settings` bracket**, where the old
  `return await AsyncClient().post(...)` was. The mount only resolves while the override is
  active, and the `finally` that resets `_CURRENT["schema"]` is untouched.
- **D1 keeps `response.json()`.** `::test_a_field_error_envelope_is_untouched_because_it_is_data_not_an_error`
  asserts `"errors" not in payload` — a statement about a decoded dict key. Rebuilding the
  payload from the typed `Response` would invert it, since `Response` always carries an
  `errors` attribute.
- **D2 / D9 keep `json.loads(...content)`** rather than `.json()`: identical result, and
  `json` stays live in both modules for its other uses (three in `test_error_policy_api.py`,
  one in `test_resource_policy_api.py`), which ruff confirmed.
- **D8's uploads are named `attachment.bin` / `image.bin`.** Nothing asserts on the filename;
  only the file count and the 200-byte size reach the charger.
- Import placement was left to ruff's isort; nothing was hand-placed.

### Notes for Worker 3

- **Two scratch probes under `docs/builder/temp-tests/043/`, both kept for re-run:**
  `test_upload_bound_probe.py` (the converted `TestClient().query(..., files=...)` shape) and
  `test_upload_bound_head_probe.py` (the deleted helper's hand-rolled envelope, replicated).
  Each prints the observed rejection `extensions` under `-s`. They import
  `test_resource_policy_api` off an explicit `sys.path` insert and reuse its
  `pytest.mark.urls` mount, so they run standalone:
  `uv run pytest --no-cov -n0 -s docs/builder/temp-tests/043/<file>`. Neither is a candidate
  for promotion — the live row already asserts the property; these only make the *which bound*
  reading visible, which an assertion on set membership deliberately does not.
- **No shadow files or `review_inspect.py` output used.**
- **Control flow worth a second look:** D2 and D9 hand a coroutine to a module-local
  `_await_response` that `asyncio.run`s it from a *sync* test body. `AsyncTestClient().query()`
  is a coroutine exactly as `AsyncClient().post()` was, so the surrounding shape is unchanged —
  but the awaited value is now a typed `Response`, which is why both sites read
  `async_response.response.content` rather than `.content`.
- **`assert_no_errors=False` is on every converted call**, including the three sites that
  expect no errors (D3, D4, D7): each already carries its own
  `assert payload.get("errors") is None, payload`, and letting the client raise first would
  relocate that assertion into the helper and change what a failure reports. The three sync
  sites inherit it from `post_graphql`, which hard-codes it.
- **`force_login` left alone at all three sites** (`test_error_policy_api.py`,
  `test_products_visibility_api.py`, `test_resource_policy_api.py`): credential setup on a
  client the test then hands to a helper, not a request. `TestClient.login()` is a bracket, not
  a replacement for that.

### Notes for Worker 1 (spec reconciliation)

No plan-vs-implementation drift: all nine sites landed exactly as `### Dispatched findings
checklist` specifies, no structural call was made, and no assertion changed. Nothing below
needs a spec edit from this cohort's diff except where stated; each item carries its
recommended replacement so it is an amendment, not a complaint.

1. **The D8 bound is now measured, and the spec's exemption class (a) has no surviving
   exemplar.** Spec section: the Slice-2 checklist's exemption list, currently reading
   `hand-built multipart ``operations`` / ``map`` assertions`. Recommended replacement:
   `a hand-built multipart ``operations`` / ``map`` envelope whose field labels or map targets
   are themselves asserted — no live file currently claims this class`. Warrant: the one
   candidate, `test_resource_policy_api.py::_multipart`, is deleted, and two probes of the same
   mount (converted envelope, HEAD-shaped envelope) return the identical rejection
   `{'code': 'RESOURCE_LIMIT_EXCEEDED', 'bound': 'max_upload_file_bytes', 'limit': 64,
   'charged': 200}`, so the label change is not observable at the assertion.
2. **The plan's items 1-8 under its own `### Notes for Worker 1 (spec reconciliation)` all
   still stand after the build** — re-checked against the landed diff rather than inherited.
   Two of them are confirmed *by* this diff and are restated here so a reader of the build
   report alone does not miss them:
   - `examples/fakeshop/test_query/README.md` `## Clients, transports, credentials`, the
     `Async` bullet, is now **falsified**: `test_relations_async_api.py` drives
     `AsyncTestClient` and declares no helper exemption, and after D4 / D6 the same is true of
     `test_products_visibility_api.py`'s async rows. Current wording:
     ``test_list_field_async_api.py``, ``test_relations_async_api.py``:
     ``django.test.AsyncClient`` vs an ``AsyncDjangoGraphQLView`` mount. Async rows:
     ``@pytest.mark.django_db(transaction=True)``, declare the helper exemption …`.
     Recommended replacement: `` `test_list_field_async_api.py`, `test_relations_async_api.py`:
     the package's own `AsyncTestClient` against an `AsyncDjangoGraphQLView` mount. Async rows:
     `@pytest.mark.django_db(transaction=True)`, and a per-call `url=` naming the mount.``
     The file is in **no** cohort's write set and was left untouched; it still needs Worker 0
     to name an owner.
   - After this pass there is **no retained raw `client.post(...)` in these four files**, so
     the spec's `## Test plan` sentence `each retained raw ``client.post(...)`` carries the
     wire-shape-exemption comment` and the matching Definition-of-done sentence describe an
     empty population here. Recommended replacement for both:
     `outside ``test_products_api.py``, ``test_transport_api.py``, ``test_auth_api.py`` and
     ``graphql_client.py::post_graphql_raw``, no live file retains a raw ``client.post(...)``;
     any future one carries the wire-shape-exemption comment`. Cohort C's custodian owns the
     sweep, and it is four sites, not two.
3. **The node count is 87 as of this build, and that is a timestamp, not a constant.** My own
   pre-edit and post-edit readings agree at 18 / 10 / 3 / 56 = 87, which is the only claim this
   report makes about it. The plan's warning holds unchanged: no artifact should publish a fixed
   total for a population a concurrent session is editing. Any later pass measures it with
   `--collect-only` and says when.
4. **A shared async live-tier post helper is still the missing shape and still unowned.** This
   pass landed the fifth and sixth near-identical
   `await AsyncTestClient().query(..., assert_no_errors=False, url=...)` bodies (D2, D4, D6,
   D7, D9 — five sites across four modules), which is the plan's stated extraction condition
   minus one. `examples/fakeshop/graphql_client.py` is declared sync-only in its own module
   docstring and sits in no cohort's write set, so nothing was extracted. Recommended
   replacement, in `graphql_client.py`'s module docstring, once an owner exists: drop
   `sync-only` and add `` `post_graphql_async` is the awaited twin; async suites still owe
   `django_db(transaction=True)` and registered types``. Needs a named owner card before the
   cycle closes.

## Review (Worker 3)

Reviewed against HEAD `96b9e047` — the same HEAD the plan, escalation 3 and the
build report were written at (`git merge-base --is-ancestor` confirms the
session-start snapshot's `aadca5a2` is an ancestor, and `18f2446f`, which added
rows to two owned files, is already inside HEAD, so the build report's baseline
and mine are the same tree). HEAD copies of the four owned files were read with
`git show HEAD:<path>` into the session scratchpad; no stash, no checkout, no
worktree, nothing reverted.

The spec is dirty under Cohort C's custodian, so nothing below is graded against
the working copy of `docs/SPECS/spec-043-test_client-0_0_14.md`. Where a spec
comparison was needed the reference was the plan's and escalation 3's quoted
text plus `git show HEAD:` — stated because the two can diverge this week.

### High:

None.

### Medium:

#### Two stated counts in the Plan are falsified by measurement

`BUILD.md` `## Claims are proven mechanically, never accepted on prose` grades a
wrong stated count Medium, and both of these were published as measured. Neither
changes a line of the diff: the conclusions each supported survive
re-derivation by a second instrument. The defect is the instrument and the
number a later pass would inherit.

**(a) `### DRY analysis` → "Variables-truthiness check, measured not assumed …
Sweep of the four files for `variables={}` / `variables = {}` / `variables=dict()`:
**0 occurrences**."** There is one, and the sweep could not see it because it
enumerated the *keyword* spelling of an argument that is also passed
positionally:

```examples/fakeshop/test_query/test_resource_policy_api.py:522
    extensions = _rejection(_post("/rp-values/", query, {}))
```

`::_post`'s signature is `(mount, query, variables=None, *, client=None)`, so
that bare `{}` **is** `variables`. This is `START.md` `## Instruments that lie`
→ "Positive-vocabulary census" and `BUILD.md`'s "a long grep phrase samples a
claim's vocabulary rather than establishing its population", in a cycle whose
own memory already records eight census errors of this family.

Consequence: **none, re-derived rather than assumed.** I replaced the grep with
an AST enumeration of *every* `variables` argument — keyword and positional — at
every call site of `_post` / `post_graphql` / `graphql_payload` / `query` /
`assert_graphql_success` / `_post_async` / `_post_visibility_query` across all
four files. Exactly one empty-dict site exists, the one above, and it lives in
`test_resource_policy_api.py::_post`, which already delegated to
`graphql_client.py::graphql_payload` → `::post_graphql` → `TestClient` at HEAD.
The truthiness-vs-`is not None` semantics therefore already applied to it before
this cohort existed, this cohort's diff does not touch that helper, and the row
passes (`::test_variable_default_value_in_operation_header_is_rejected_when_omitted`,
green in every run below). The converted D1 helper's own callers all pass `None`
or a non-empty dict, so D1's posted body is byte-identical after conversion — the
plan's conclusion, reached through an instrument that can see the population.

Recommended change: correct the claim in the Plan to name the site and the
positional spelling, and state the conclusion the way the AST enumeration
establishes it. No source edit.

**(b) `### DRY analysis` / `### Implementation steps` / D1's checklist box →
"`test_error_policy_api.py::_post` (15 callers)" and "all 15 callers untouched".**
AST call count is **17**, at HEAD and in the working tree alike:

```
ast.Call → Name("_post")   HEAD: 17   worktree: 17
examples/fakeshop/test_query/test_error_policy_api.py:279,305,320,335,361,387,
400,420,439,454,473,511,546,576,589,604,613
```

The substance holds — no caller changed, proven mechanically below — but "15"
is wrong in the plan, in D1's ticked box, and in anything that later quotes
either. Recommended change: 17 in both places. No source edit.

Both are routed to Worker 1 under `### Notes for Worker 1 (spec reconciliation)`
below with an `Escalated:` prefix, because the text that carries them is the
Plan section and D1's checklist box, neither of which Worker 2 or Worker 3 owns.

### Low:

#### The build report's assertion claim is absolute where the diff is not

`### Tests added or updated` reads "every assertion text, operator, value and
owning line unchanged". Two assertions' text did change, by receiver rebinding:

```examples/fakeshop/test_query/test_relations_async_api.py:97
-        assert response.status_code == 200
+        assert res.response.status_code == 200
```

```examples/fakeshop/test_query/test_resource_policy_api.py:929
-    assert response.status_code == 200, response.content
+    assert res.response.status_code == 200, res.response.content
```

`res.response` **is** the `HttpResponse` the client stashed
(`django_strawberry_framework/testing/client.py::Response`), so operator, value
and semantics are identical, and `BUILD.md`'s relocation proof explicitly
normalizes a renamed receiver. The claim as written nonetheless invites the next
reader to treat "no assertion changed" as byte identity when two are not.
Recommended change: say "unchanged except two receiver rebindings, named".

#### D1 moves the decode ahead of the row's own status message

At HEAD `test_error_policy_api.py::_post` asserted
`status_code == 200, response.content` *before* touching the body. The converted
path decodes inside `TestClient._finish_response` first, so a non-200 carrying a
non-JSON body — a mis-spelled mount serving 404 HTML — now surfaces as Django's
`ValueError` naming the `Content-Type` rather than as the row's own
`response.content` message. This is the shipped client's documented behavior
(`testing/client.py::TestClient.query` docstring says so explicitly) and is
already how `test_resource_policy_api.py::_post` has behaved since before this
cohort. Recorded, not a requested change: the assertion still reports for every
JSON response, which is every response these mounts serve.

#### `examples/fakeshop/test_query/README.md` falsification confirmed, not fixed

Independently verified at `examples/fakeshop/test_query/README.md:918` — the
`## Clients, transports, credentials` `Async` bullet still names
`django.test.AsyncClient` for `test_relations_async_api.py`, which after D7
drives `AsyncTestClient` and declares no helper exemption. Correctly left alone:
the file is outside every cohort's write set. Still needs Worker 0 to name an
owner; see Notes below.

### DRY findings

- **The seam is honest, and I measured it rather than reading the report.** My
  own AST census — every `ast.Call` whose callee attribute is one of `post get
  put patch delete head options trace generic request login force_login logout`,
  over all 28 live-tier modules, printing non-HTTP receivers too so exclusions
  are visible — finds **zero** raw client posts left in the four owned files.
  The only surviving HTTP-verb calls there are the three `client.force_login`
  credential setups the plan declared. No fourth private post construction
  survived; `.generic(`, `RequestFactory`, and an operation riding a GET are all
  absent from these four.
- **No converted row became a near-duplicate of a sibling.** The four surviving
  per-file helpers (`_post` ×2, `_post_visibility_query`,
  `_post_async_visibility_query`, `_post_async`) are mount/schema brackets —
  `override_settings(ROOT_URLCONF=__name__)` + `clear_url_caches()` +
  `_CURRENT["schema"]` teardown — not copies of post boilerplate; each now
  delegates its one transport line. Two of them share a signature
  (`(mount, query, variables=None, *, client=None)`) and differ in return
  contract (`(response, payload)` vs `payload`); collapsing them would inline
  bracket handling into 17 and 59 call sites respectively. **Existence challenge
  not raised: they earn it.**
- **The five async near-copies are real and already routed.** D2, D4, D6, D7, D9
  now hold five `await AsyncTestClient().query(..., assert_no_errors=False,
  url=...)` bodies across four modules. The plan (its note 5) and the build
  report (its note 4) both raise this and both decline to extract, correctly:
  `examples/fakeshop/graphql_client.py` is sync-only by its own docstring and in
  no cohort's write set. One correction to the stated extraction condition — the
  plan waits for "a sixth async site", and the sixth **already exists**, as an
  unconverted raw post at `examples/fakeshop/test_query/test_list_field_async_api.py:79`
  (`http_client.post(`), which the spec-050 cycle owns. The condition is met
  today; only the owner is missing.
- No repeated literal, key, or error fragment is introduced. The one repeated
  string across converted sites is the mount path, and each mount is named once
  per site by construction (Decision 7's per-call `url=`).

### Claim verification (re-derived, not accepted)

- **Checklist walk, all 13 boxes.** D1-D9 each have a matching hunk in
  `git diff HEAD -- <path>`; I located every one and read it against the box's
  text. C1-C4 re-run below. No box is ticked without a fix, and no box the diff
  leaves unaddressed.
- **"No assertion's text, operator, value or owning line changed" — verified
  assertion by assertion, not by sampling.** Instrument: `ast.Assert` unparse of
  every assertion in each file, HEAD copy vs working tree, unified-diffed.
  Counts and deltas:

  | File | asserts at HEAD | asserts in worktree | delta |
  | --- | --- | --- | --- |
  | `test_error_policy_api.py` | 57 | 57 | none |
  | `test_products_visibility_api.py` | 41 | 50 | +9, all inside the concurrent session's `@@ -381,3 +377,96 @@` append |
  | `test_relations_async_api.py` | 8 | 8 | 1 receiver rebinding (Low, above) |
  | `test_resource_policy_api.py` | 103 | 103 | 1 receiver rebinding (Low, above) |

  Zero assertions removed, zero weakened, zero relocated to a different owning
  statement, in any file. The nine additions are attributed by diff content to
  the spec-050 session's two appended rows, not by "files this cohort touched" —
  they are `assert len(parent_pks) == 3`, `assert hidden, …`,
  `assert len(item_queries) == 1, item_queries` and the two rows' three
  assertions each. Untouched, as required.
- **`assert_no_errors` per converted call, both directions.** D2, D4, D6, D7,
  D8, D9 pass `assert_no_errors=False` explicitly; D1, D3, D5 inherit it from
  `graphql_client.py::post_graphql`, which hard-codes `assert_no_errors=False`.
  Nine of nine. The converse holds too: no converted site previously raised on a
  GraphQL `errors` key (a raw `client.post` cannot), so nothing that used to
  raise now passes silently — and had any site been left at the client's
  `True` default, the client's explicit `raise AssertionError(response.errors)`
  would have made the row fail loudly, not pass. No row is vacuous: the
  error-expecting rows funnel through `::_rejection` / `::_masked_error`, both
  of which assert `data is None`, exactly one error, and the typed code.
- **The deleted helper's caller sweep, spelling-independent.** Population: 658
  tracked `.py` + `.md` files (`KANBAN.md` excluded as a generated render),
  swept for the shortest distinctive token `_multipart` counting *occurrences*
  per file, plus all untracked `.py`. `test_resource_policy_api.py` scores
  **0** — the helper has no residual reference in its own file. Every nonzero
  file is a different symbol (`_build_multipart_file_map`, `_multipart_parser`,
  transport-security prose). A second, independent instrument: no file in any of
  the three test trees (294 `.py` files) imports any of the four owned modules,
  so no cross-module caller can exist either. `AsyncClient` has **0**
  occurrences left in the four files, and `json` survives only where it is used
  — `AGENTS.md` rule 14's orphan sweep is discharged.
- **995 citations resolve.** `uv run python scripts/check_citations.py --check`
  → `OK: 995 citations resolve (825 in 441 .py files, 170 in KANBAN.md)`. Run
  myself, whole tree.

### Node-count reading — my own pair, and a stronger instrument than a total

`uv run pytest --no-cov -n0 -q --collect-only <module>`:
**18 / 10 / 3 / 56 = 87**, identical to Worker 2's post-edit reading. Reported
as agreement, not as inheritance.

A bare total cannot distinguish "nothing lost" from "one lost, one gained", and
this population is being edited by a concurrent session, so I took a **node-id
set** reading as well: AST test-function names in `git show HEAD:<path>` vs the
working tree, per file.

| File | HEAD funcs | worktree funcs | lost | gained |
| --- | --- | --- | --- | --- |
| `test_error_policy_api.py` | 17 | 17 | none | none |
| `test_products_visibility_api.py` | 8 | 10 | none | `::test_a_planned_list_relation_hides_the_targets_private_rows`, `::test_a_planned_relation_connection_window_hides_the_targets_private_rows` |
| `test_relations_async_api.py` | 3 | 3 | none | none |
| `test_resource_policy_api.py` | 56 | 56 | none | none |
| **total** | **84** | **86** | **none** | **2** |

**Nothing was lost.** The two gained rows are the concurrent spec-050 session's
append, attributed by diff content (they are the `+93` hunk's contents, and both
drive `assert_graphql_success`). 86 functions collect as 87 nodes because
`test_error_policy_api.py::test_an_exception_surfaced_through_value_completion_is_masked_too`
is parametrized in two — which is also the arithmetic that settles escalation
3's "84": it was a function count, and at HEAD it is still exactly right as one.

Execution:

- `uv run pytest --no-cov <the four modules>` (repo default parallel) —
  `8 workers [87 items]`, **87 passed in 14.53s**.
- `uv run pytest --no-cov -q examples/fakeshop/test_query/` — the **whole live
  tier**, a deliberately wider selection than the build report's four-module
  run: `8 workers [807 items]`, **807 passed, 1 skipped in 117.99s**. Not the
  full sweep (that is the final gate's); wide enough to answer the
  order-independence question empirically rather than by reading.
- `uv run ruff format --check` / `ruff check` on the four explicit paths — `4
  files already formatted`, `All checks passed!`.
- `uv run python scripts/check_trailing_commas.py --check <the four paths>` —
  clean, explicit paths only.

### The two must-run nodes, measured here

**D8 — the multipart bound.**
`::test_an_oversized_upload_is_rejected_by_the_policy_not_by_the_body_cap`
→ **1 passed**. A green run is not the reading, because the row asserts
membership in a three-element set, so I re-ran both of Worker 2's probes after
checking the replica against the deleted helper's body in the diff line by line
(same `operations` / `map` JSON construction, same numeric `"0"` / `"1"` labels,
same two map targets, same `b"z" * 200` payloads, same `client.post(mount,
data=body)`):

```
test_upload_bound_probe.py       OBSERVED_BOUND= max_upload_file_bytes  {'code': 'RESOURCE_LIMIT_EXCEEDED', 'bound': 'max_upload_file_bytes', 'limit': 64, 'charged': 200}
test_upload_bound_head_probe.py  HEAD_OBSERVED_BOUND= max_upload_file_bytes  {'code': 'RESOURCE_LIMIT_EXCEEDED', 'bound': 'max_upload_file_bytes', 'limit': 64, 'charged': 200}
```

**Identical dicts**, converted envelope vs the deleted helper's envelope, from
the same mount. The label change is not observable at the assertion, as the plan
argued and as the charger's value-walk predicts. Escalation 3's one
"unverified by execution" row is verified, and nothing was widened to make it
pass. The conversion also *adds* a client-side assertion the hand-rolled
envelope never had — `TestClient._assert_file_placeholders` walks each `files=`
path to its `None` placeholder — so D8 is strictly better pinned than HEAD, not
equivalent.

**D5 — the query-count row.**
`::test_nested_connection_costs_one_query_per_parent_without_the_optimizer`
→ **1 passed**. The assertions are **absolute at two cardinalities**, which is
what `BUILD.md` `### Query-shape tests must pin the load-bearing property`
requires and what an equality-only pair would fail:

```examples/fakeshop/test_query/test_products_visibility_api.py:307
    assert len(_nested_connection_item_queries(2)) == 2
    assert len(_nested_connection_item_queries(5)) == 5
```

Both unchanged by the diff (they appear in neither side of the assert-level
diff above). The measured population is `[sql for … if "products_item" in sql]`
inside `CaptureQueriesContext`, and the conversion moved no query boundary: the
capture bracket, the schema holder and the `_CURRENT["schema"]` teardown are
byte-identical, and the transport swap replaces one `Client().post` with a
`TestClient(...)` construction plus the same `Client().post` — construction
touches no database, and any query it did add could not carry `products_item`.
2 at two parents, 5 at five, as recorded.

### Failability proofs — where the second pair of eyes landed

The diff introduces **no** boundary: no guard, cap, rejection path, validation
branch, or permission decision. Nine call sites move onto an already-shipped
client and one local helper is deleted. Worker 2's `None; this pass introduced
no new boundary.` is correct, so my mandatory re-run floor
(`worker-3.md` "every boundary whose recorded failing-row count is 3 or fewer,
and every security or data-isolation boundary") computes to the **empty set**,
which `worker-3.md` makes legal only in exactly this case. Named explicitly so
the empty subset reads as arithmetic rather than as a choice:

- **Re-run by me:** D8's multipart bound (both envelopes, above) and D5's
  query-count pair — not failability proofs, the plan's two must-run rows, and
  re-derived rather than accepted.
- **Accepted on Worker 2's record:** nothing. There is no proof record to
  accept, because there is no boundary.

The one thing worth stating that a boundary count does not: the *client's* own
guards (`_build_body`'s `"variables" not in body` raise, its reserved-field
guard, `_assert_file_placeholders`) are now on the path of these nine rows.
They are Cohort C's boundaries, pinned in Cohort C's tests, and this cohort
introduces none of them — but D8 is the first live row to exercise
`_assert_file_placeholders` in anger, which is a fact Cohort C's reviewer should
have rather than a finding here.

### Order independence

No cross-module state is introduced. Every converted site constructs its client
**inside** the row (`TestClient()`, `AsyncTestClient()`, or `post_graphql`'s
per-call `TestClient(client=client)`); nothing is bound at module level, nothing
is cached, and `AsyncTestClient` holds no loop or session across calls. The
`override_settings(ROOT_URLCONF=__name__)` / `clear_url_caches()` brackets and
the `finally: _CURRENT["schema"] = None` teardowns are untouched at every site.

The one shared-state seam a reader should check is the endpoint: `TestClient.
__init__` resolves `conf.py::testing_endpoint_setting()` into `self.path` at
construction. Every one of the nine sites passes a per-call `url=`, and
`TestClient.request` reads `url if url is not None else self.path`, so
`self.path` is never used by these rows — a project-wide `TESTING_ENDPOINT`
change from any other module cannot reach them. Cohort C's concurrent `conf.py`
edit is docstring-only (`git diff HEAD -- django_strawberry_framework/conf.py`
changes prose inside `::testing_endpoint_setting`'s docstring and no code), so
the seam is inert in both directions this week.

No schema module or example app is added, so `BUILD.md`
`### Example-project schema changes must sync every schema-module list` does not
bite. Confirmed empirically anyway by the 807-item live-tier parallel run above,
which is the selection that would expose a stranded registration.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty**.
`__all__` and the re-export list are unchanged. This cohort writes no package
source at all.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The
three docstring restatements it does make (the `test_error_policy_api.py` module
docstring and the two `::_await_response` docstrings) were read end to end: each
states what the code now does, none narrates the change, and none carries round
or cohort provenance. `examples/fakeshop/test_query/README.md` is correctly
untouched and correctly still falsified — see Low, above.

### What looks solid

- Nine of nine sites converted, with the load-bearing property — assertion
  identity — holding under an instrument that reads every assertion in all four
  files rather than sampling. This is the laundering the spec's exemption exists
  to prevent, and it did not happen.
- The one site that could have been laundered quietly, D8, was instead proven by
  two readings of the same instrument and came out byte-identical in the
  rejection payload. That is the right shape of evidence for a row whose
  assertion is set membership.
- The plan refusing every exemption, and the build landing without claiming one,
  leaves these four files with zero raw posts — confirmed by my own census, not
  by the report.
- The concurrent session's `+93` append is intact, unreverted, and correctly
  attributed by diff content on both sides.
- Deletion over extraction at D8 (`::_multipart` gone, not rewritten) is the
  right DRY instinct, and the declined async extraction is the right restraint
  given the write-set fence.

### Temp test verification

- Used, not written: `docs/builder/temp-tests/043/test_upload_bound_probe.py`
  and `docs/builder/temp-tests/043/test_upload_bound_head_probe.py` (Worker 2's),
  re-run by me after auditing the replica against the deleted helper's body.
  `uv run pytest --no-cov -n0 -s <both>` → 2 passed, output quoted above.
- Disposition: **kept as scratch, not promoted.** Correct call by Worker 2 — the
  live row already asserts the property; the probes only make the *which bound*
  reading visible, which the set-membership assertion deliberately does not.
- I wrote no temp test. My own instruments (the AST census, the assert-level
  differ, the call-site enumerator, the HEAD function-name comparator) are
  scratch scripts in the **session scratchpad outside the repository**, per
  `BUILD.md`'s scratch-path rule.
- `scripts/review_inspect.py` **not run**; recorded as a skip with its reason:
  its value is control-flow overview and repeated-literal evidence over package
  source, and this diff contains no package source and no repeated literal
  (the one repeated string, a mount path, is named once per site by the `url=`
  contract).

### Notes for Worker 1 (spec reconciliation)

The plan's items 1-8 and the build report's items 1-4 were re-checked against
the landed diff rather than inherited; all still stand, and item 1 of the plan
(the README falsification) is independently confirmed above. Three additions:

1. **`Escalated:` — the two wrong counts.** Both are Medium above, both are
   text-only, and both live in sections Worker 2 cannot edit. Resolution paths:
   (i) Worker 1 corrects them in place at final verification — the Plan's
   `### DRY analysis` variables-truthiness paragraph, and "15 callers" in
   `### DRY analysis`, `### Implementation steps` D1, and D1's checklist box;
   or (ii) the maintainer accepts the artifact as-is with this review section as
   the correction of record. I recommend (i): the "0 occurrences" sentence is
   the kind of measured-and-wrong claim the next cycle inherits verbatim, and
   the correct figures are 1 occurrence (positional, at
   `test_resource_policy_api.py:522`, already on the converted path at HEAD) and
   17 callers.
2. **`Escalated:` — the async-extraction condition is already met.** The plan's
   note 5 defers extraction until "a sixth async site". Five landed here and the
   sixth exists today as an unconverted raw post at
   `examples/fakeshop/test_query/test_list_field_async_api.py:79`. Resolution
   paths: (i) name the owner card now (escalation 3's nominee
   `TODO-ALPHA-053-0.0.15`) and let the spec-050 cycle's conversion land on the
   extracted helper rather than a seventh copy; or (ii) record the condition as
   met-but-deferred so the next reader does not re-derive it. Either way the
   decision is the maintainer's, not a worker's — `BUILD.md`
   `### Contract-level findings`.
3. **A boundary this cohort does not own but now exercises.** D8 is the first
   **live** row to drive `testing/client.py::TestClient._assert_file_placeholders`
   and the `"variables" not in body` guard. Cohort C owns both and is editing
   that file concurrently; worth one line in Cohort C's closure that a live row
   outside its write set now depends on those guards' behavior, so a later
   respell of either cannot be graded on `tests/testing/test_client.py` alone.

### Review outcome

`review-accepted`, with the two Medium findings transparently escalated to
Worker 1 under the clause in `worker-3.md` `### Acceptance gate` — both are
corrections to Plan text that Worker 2 does not own, neither implies a source
change, and the conclusions each wrong number supported have been re-derived
here by instruments that can see their populations. Every Low carries a recorded
disposition. The conversion itself holds on every question I could put to it:
nine of nine sites, assertion identity proven assertion by assertion, zero rows
lost, 87/87 and 807/807 green, both must-run rows re-measured rather than
accepted, and the deleted helper orphan-free across 658 files and three test
trees.

---

## Final verification (Worker 1)

- **Dispatched findings checklist:** all 13 boxes (D1–D9, C1–C4) are `- [x]`; every
  one re-derived against the diff below, none un-ticked, none left open, so no
  deferral reason is owed under `### Spec changes made (Worker 1 only)`.
- **DRY check across this cohort and the prior accepted cohorts:** no new
  duplication. This cohort authors no shape; the one shape it declines to author
  (an async twin of `graphql_client.py::post_graphql`) is escalated below rather
  than deferred silently.
- **Existing tests still pass:** `uv run pytest -n0 --no-cov` over the four owned
  modules — `collected 87 items`, **87 passed in 19.99s**. Run by me, no
  `--cov*` flag. Not the full sweep; that is `bld-043-final.md`'s.
- **Lint/layout, my own reading:** `uv run ruff format --check` → `4 files already
  formatted`; `uv run ruff check` → `All checks passed!`;
  `scripts/check_trailing_commas.py --check` → clean. All three on the four
  explicit paths, never a bare `.`.
- **Public surface:** `git diff HEAD -- django_strawberry_framework/__init__.py`
  is 0 lines. This cohort wrote no package source.
- **Staged anchors:** `grep -rn 'TODO(spec-043' .` finds no source anchor — the
  four hits are prose in the spec and in `bld-043-review-2-code_verification.md`.
- **Spec reconciliation:** no spec edit from this pass. The spec and its rationale
  are Cohort C's under the applied partition; everything this cohort's diff
  obliges the spec to say differently is consolidated in
  `### Notes for Worker 1 (spec reconciliation)` below, on disk, for Cohort C's
  custodian.
- **Final status:** `final-accepted`.

HEAD for every comparison in this pass: `96b9e047` — the same HEAD the plan, the
build report and the review were written at. HEAD copies were read with
`git show HEAD:<path>` into the session scratchpad outside the repository. No
stash, no `checkout --`, no `restore`, no worktree, nothing reverted.

### Tick audit — all 13 boxes, re-derived rather than inherited

Worker 3 reports a matching hunk for each. I located each independently in
`git diff HEAD -- <path>` and read it against the box's own text.

| Box | Landed | Evidence I took myself |
| --- | --- | --- |
| D1 | yes | `::_post` body is one `post_graphql(query, client=client, variables=variables, url=mount)`; signature, `assert response.status_code == 200, response.content`, and the `(response, response.json())` return all survive verbatim; module docstring restated to name the package's own clients. Caller count corrected to 17 (below); all 17 untouched by AST comparison of HEAD vs worktree. |
| D2 | yes | `AsyncTestClient().query("{ boom fine }", assert_no_errors=False, url="/ep-async/")` inside `_await_response`; `json.loads(async_response.response.content)` kept; `::_await_response` docstring restated. |
| D3 | yes | inline `Client().post(...)` replaced by `post_graphql("{ categories { items { name } } }", url="/graphql/")`; the three assertions below it appear on neither side of the assert-level diff. |
| D4 | yes | `await AsyncTestClient().query(..., assert_no_errors=False, url="/graphql-async/")` with `return res.response` **inside** the `override_settings` bracket; caller untouched. |
| D5 | yes | one-line body swap to `post_graphql(query, url="/graphql/")`; 5 callers, identical line-for-line at HEAD and worktree; the `CaptureQueriesContext` row's `== 2` / `== 5` pair is absent from both sides of the assert diff and passed in my run. |
| D6 | yes | inline async post converted; the exact non-null-message list assertion unchanged. |
| D7 | yes | `::_post_async` converted; `import json` and `AsyncClient` gone; the status assertion survives as a receiver rebinding (Low 1). |
| D8 | yes | `::_multipart` deleted (0 residual `ast.Call → Name("_multipart")` in the file, against 1 at HEAD); caller rewritten onto `TestClient().query(..., files={...})`; the row executed. |
| D9 | yes | `AsyncTestClient().query(_NODES, variables=variables, assert_no_errors=False, url="/rp-values-async/")`; `_rejection(async_payload) == sync_extensions` untouched; docstring restated. |
| C1 | yes | `AsyncClient` absent; `post_graphql` (L62) and `AsyncTestClient` (L71) present; `json` still used at L556/591/618 and `Client` at L508 — so the surviving imports are live, not residue. |
| C2 | yes | `import json` and `AsyncClient` both gone; `post_graphql` folded into the existing `graphql_client` import; `Client` still used at L327's `force_login` row; the concurrent session's `+93` append intact. |
| C3 | yes | `AsyncClient` and `import json` gone; `AsyncTestClient` at L43. |
| C4 | yes | `AsyncClient` gone; `AsyncTestClient, TestClient` at L65; `json` (L1245), `Client` (L1006) and `SimpleUploadedFile` (L924-925) all still used. |

The per-box run/lint claims (C1–C4) are confirmed by my own invocations in the
bullets above, not by re-reading the build report's.

**No over-tick.** D1's box carried a wrong *number* while its contract had fully
landed, which is a text correction to plan prose I own, not an over-tick: the
tick asserts the contract, and the contract is in the diff. Corrected in place
rather than un-ticked, per `BUILD.md` `### Dispatched findings checklist` — the
un-tick remedy is for a box whose fix is absent.

### The two Medium findings — corrections to my own plan, resolved in place

Both are now fixed in the Plan sections that carried them, because a plan
carrying a false measured claim is what the next reader trusts. Both were
re-derived rather than accepted from the review.

**(a) "0 occurrences of `variables={}`."** False, and false in the way this cycle
has now failed eight times: the sweep enumerated a keyword spelling of an
argument that is also passed positionally. Re-derived with an AST enumeration of
every empty-`ast.Dict` argument — keyword *and* positional — at every call in the
four files, run against `git show HEAD:` copies and the working tree: **one**
occurrence in each, `test_resource_policy_api.py:522` (`_post("/rp-values/",
query, {})`), the positional third argument. Consequence nil, because that helper
already routed through `TestClient` at HEAD by way of
`graphql_client.py::graphql_payload` and is byte-identical in the working tree —
so the truthiness semantics have governed that call since before this cohort, and
they are what the row's own subject (a variable *omitted* from the envelope)
requires. The corrected paragraph is in `### DRY analysis`, stated the way the
enumeration establishes it.

**A third wrong figure in the same paragraph, which the review did not reach.**
It also claimed "**two** helpers here forward `variables` under `is not None`
semantics". Grepping `is not None` across the four HEAD copies returns exactly
one such forwarder — `test_error_policy_api.py::_post` at HEAD L232 — and
thirteen unrelated `assert … is not None` rows. One helper, not two. Corrected in
the same edit. Three published figures in one paragraph, three wrong: the
paragraph's own headline was "measured not assumed", which is where the
`BUILD.md` rule about a count asserted in the same breath as the lesson it
illustrates bites hardest.

**(b) "15 callers" of `test_error_policy_api.py::_post`.** The AST call
enumeration returns **17** at HEAD and 17 in the working tree, same line set
modulo the diff's shift. Corrected in `### Census`, in `### Implementation steps`
D1, and in D1's checklist box. The substance is untouched — every one of the 17
is byte-identical across the diff — and the enumeration additionally shows why
the conversion is body-identical: 15 of the 17 pass no `variables` at all, 2 pass
a non-empty dict, none passes `{}`. The plan's "15" appears to have been the
count of the None-passing subset promoted to the count of the population, which
is `START.md`'s "count right in every digit, wrong in SUBJECT".

Neither correction implies a source edit, and neither changes a conclusion. What
they change is what a later pass inherits, which is the whole reason they were
escalated instead of being left in the review section.

### The three Low findings, graded

**Low 1 — "every assertion unchanged" is absolute where two receivers were
rebound. Accepted; the build report's sentence is corrected here rather than in
place** (`ARTIFACT.md` forbids editing a prior worker's entry). My own instrument
— an `ast.Assert` unparse **multiset** per file, HEAD copy against the working
tree, differenced both directions — returns exactly two removals and eleven
additions across the four files: `test_relations_async_api.py`'s
`assert response.status_code == 200` → `assert res.response.status_code == 200`,
and `test_resource_policy_api.py`'s `assert response.status_code == 200,
response.content` → `assert res.response.status_code == 200, res.response.content`.
`res.response` **is** the `HttpResponse` the client stashed
(`django_strawberry_framework/testing/client.py::Response`), so operator, operand
and semantics are identical and `BUILD.md`'s relocation proof normalizes exactly
this. The accurate sentence is "no assertion's text, operator, value or owning
line changed **except two receiver rebindings, both named**".

**Low 2 — D1 now decodes before its row's own `response.content` message.
Accepted, no change, and verified rather than read.**
`testing/client.py::TestClient.query` calls `_finish_response`, whose **first**
statement is `self._decode(resp, ...)`; the inherited
`strawberry.test.client.BaseGraphQLTestClient._decode` is `return response.json()`
for the JSON path, which raises on a non-JSON content type. So on a non-200
non-JSON body the decode's `ValueError` arrives before `::_post`'s
`assert response.status_code == 200, response.content`. Three points make this the
right disposition: it is the shipped client's documented behavior, it is already
how `test_resource_policy_api.py::_post` has behaved since before this cohort
(same mounts, same rows), and it fails **loudly** in both shapes — this is a
message-quality change on an error path, never a fail-open. Changing it would
mean re-hand-rolling the status check ahead of the client, which is the
duplication the conversion exists to remove.

**Low 3 — the live-tier `README.md` `Async` bullet falsification. Confirmed
independently, correctly left unfixed — and the recommended replacement text is
itself wrong.** `examples/fakeshop/test_query/README.md` is clean against HEAD
(`git diff --stat HEAD` empty) and its `## Clients, transports, credentials`
`Async` bullet names `django.test.AsyncClient` for both
`test_list_field_async_api.py` and `test_relations_async_api.py`. After D7 the
second is false. But the **first is still true**: `test_list_field_async_api.py`
imports `AsyncClient` (L26) and posts through `http_client.post(...)` (L79), and
its module docstring still declares the `graphql_client.py` sync-only exemption.
The replacement sentence recommended in the build report rewrites **both** halves
onto `AsyncTestClient` and drops the exemption clause, which would falsify the
half that is currently accurate and retire a declaration that is still load-
bearing. This is `START.md`'s partial-claim-fix hazard inverted — a blanket
rewrite hitting the one clause that was still right. Corrected wording is carried
in the notes below; the file still needs the owner Worker 0 already carried to
the maintainer.

### The cohort's load-bearing claim, and the basis on which I sign it

Everything this cohort claims rests on *no assertion was weakened*, and a green
suite cannot say that — a weakened assertion passes.

I did not re-run Worker 3's instrument; I wrote a different one and compared
outcomes. Worker 3 unparsed every `ast.Assert` and unified-diffed HEAD against
the working tree per file. I took the same population as a **multiset** and
differenced it both ways, which answers a question a unified diff does not: a
line-ordered diff can show an assertion as moved, while a multiset difference
shows whether the *set of claims the file makes* changed at all. Result, with the
counts printed per file: `test_error_policy_api.py` 57 → 57 with **zero**
membership change; `test_products_visibility_api.py` 41 → 50, every one of the 9
additions inside the concurrent spec-050 session's `+93` append (I attributed
them by reading that hunk, not by the dirty list: `assert len(parent_pks) == 3`,
`assert hidden, …`, `assert len(item_queries) == 1, item_queries`, and the two
new rows' three assertions each); `test_relations_async_api.py` 8 → 8 with one
receiver rebinding; `test_resource_policy_api.py` 103 → 103 with one receiver
rebinding. **Zero assertions removed, zero weakened, in any file.** Two
independent instruments, written by different workers against the same
population, agreeing to the member.

On top of that I re-ran, myself, the two rows where a green run is not the
reading:

- **D8's multipart bound.** `uv run pytest --no-cov -n0 -s` over both scratch
  probes → 2 passed, `max_upload_file_bytes` / `limit 64` / `charged 200` from
  **both** envelopes, converted and HEAD-shaped, identically. I audited the
  HEAD-shaped probe against the deleted helper's body in the diff before
  trusting it: same `operations` / `map` JSON construction, same numeric `"0"` /
  `"1"` labels, same two map targets, same `b"z" * 200` files, same
  `client.post(mount, data=body)`. A probe that did not replicate the helper
  would be a control that cannot fail.
- **D5's query-count pair.** Ran inside my four-module run; and the multiset
  differ shows its `== 2` / `== 5` assertions on neither side, which is a
  stronger statement than "it passed".

That is the basis: two independent assertion-level instruments agreeing, the one
set-membership row measured from both envelopes, and the query-shape row shown
untouched at the assertion rather than merely green.

### The async-helper deferral — escalated to Worker 0, not decided here

Worker 3 is right on the fact, and I confirmed it: the plan's note 5 defers
extracting an async twin of `graphql_client.py::post_graphql` until "a sixth
async site", and the sixth exists **today**, unconverted, at
`examples/fakeshop/test_query/test_list_field_async_api.py:79`
(`await http_client.post("/graphql-async/", …)`). The trigger was already met on
the day it was written, which makes it a condition that can never fire — the
plan-text half of that is my own defect and is recorded as such here.

**The remedy is not mine to choose.** Extracting the helper would reverse three
standing statements, none of them this cycle's: `graphql_client.py`'s own module
docstring ("sync-only by construction"), the live-tier `README.md`'s `Async`
bullet, and `AGENTS.md`'s rule that async suites owe a **stated exemption** from
`graphql_client.py`. A worker deciding to obsolete a rule in `AGENTS.md` is
exactly what `BUILD.md` `### Contract-level findings are escalated as maintainer
decisions before dispatch` forbids; and the build plan's own `### Decision 3`
already reads the sync-only regime as "a different regime this spec never names,
which is a note for a later card, not this cycle". So: **escalated to Worker 0
for the maintainer**, with the two options stated and neither taken.

- **Option (i) — extract now, under a named owner card.** The spec-050 cycle's
  conversion of `test_list_field_async_api.py` would then land on the shared
  helper rather than a seventh copy. Cost: reverses the sync-only contract and
  the `AGENTS.md` exemption rule for async suites, and needs a KANBAN DB edit no
  worker's fence in this cycle covers.
- **Option (ii) — record the condition as met-but-deferred, on a named card**
  (escalation 3 nominates `TODO-ALPHA-053-0.0.15`). Cost: a seventh copy lands
  first; benefit: the sync-only contract and its exemption rule change in one
  deliberate pass, with the README and the docstring swept together.

What I *do* decide, because it is a DRY reading and not a contract: five
near-identical `await AsyncTestClient().query(..., assert_no_errors=False,
url=...)` bodies across four modules is a real duplication, and the right home
is one shared async helper, not five. Only *when* and *by whom* is escalated.

### Notes for Worker 1 (spec reconciliation)

For **Cohort C's custodian**, consolidated on disk. This cohort writes no spec
text. Every population below is measured at HEAD `96b9e047` and dated: the spec
is dirty under Cohort C right now, so nothing here is graded against its working
copy, and a custodian folding these in should re-read the sentence it is about
to replace rather than trusting the line anchors.

1. **The exemption-class sentences are four sites, and I confirm the count**
   (`git show HEAD:docs/SPECS/spec-043-test_client-0_0_14.md`, enumerated, not
   grep-counted): the Slice-2 checklist's "documented exemption" sub-bullet
   (L434-441); Decision 11's "switchover's own discipline" paragraph
   (L1635-1641); `## Test plan`'s "each retained raw `client.post(...)` carries
   the wire-shape-exemption comment" (L1997); and the Definition of done's
   matching sentence (L2217). **Two further sites name the same class and are not
   in that four**, and a sweep that stops at four leaves them falsified:
   `## Delivery` / file-table row for `test_query/*.py` (L1710, "wire-shape
   exemptions commented", count column `2`), and `## Risks` → "The switchover's
   breadth" (L2093-2099), whose **fallback** clause ("any file whose conversion
   proves contentious stays unconverted with the exemption comment") now
   describes a fallback nothing took. A seventh site, L1803's "GET is not
   supported … one of the named wire-shape exemptions", stays **true** — see
   item 3 for why that matters.

2. **Do not write "no live file currently claims class (a)". It is false as
   measured.** The build report's recommended replacement for the hand-built
   multipart class ends "— no live file currently claims this class". That
   conclusion is sound for the four owned files and wrong for the live tier:
   `examples/fakeshop/test_query/test_products_api.py` carries **three** live
   raw-multipart exemptions, each with a comment naming spec-043 explicitly
   (L3805, L3872, L4624), each keeping a hand-built `{operations, map, "0"}`
   envelope because **the arbitrary file label is the subject** — the wire shape
   `TestClient`'s path-keyed `files=` builder never emits. Class (a) has three
   surviving exemplars; what this cohort emptied is class (a) *within its four
   files*, where the one candidate asserted nothing about labels or map targets.
   The maintainer's `### Decision 3` licenses dropping class **(d)** only; class
   (a) should keep its sentence, sharpened if anything to say that the label or
   the map target must itself be the subject.

3. **The measured population of retained raw client requests in the live tier,
   so whatever sentence replaces L1997 / L2217 is true on its own date.**
   Instrument: AST over all 28 `test_query/*.py` plus `graphql_client.py`, every
   `ast.Call` whose callee attribute is one of `post get put patch delete head
   options trace generic request`, receiver printed for every hit including the
   non-client ones so the exclusions are visible. Files retaining a raw Django-
   client request after this cohort: `test_products_api.py` (3 posts, 5 GETs),
   `test_transport_api.py` (2 posts incl. one `Client().post`, one
   `client.generic`, 12 GETs), `test_auth_api.py` (1 post, 1 GET),
   `test_debug_toolbar_api.py` (5 GETs), `test_list_field_async_api.py` (1 async
   post), and `graphql_client.py::post_graphql_raw` (1 post). The four owned
   files retain **zero** — only three `client.force_login` credential calls,
   which are not requests. So the build report's recommended replacement list
   (`test_products_api.py`, `test_transport_api.py`, `test_auth_api.py`,
   `graphql_client.py::post_graphql_raw`) is **short by two**:
   `test_list_field_async_api.py` and `test_debug_toolbar_api.py`. The second is
   GET-only and therefore outside a sentence spelled "raw `client.post(...)`" —
   which is itself the argument for not spelling the replacement that way, since
   L1803 already names GET as an exemption class and a post-only sentence cannot
   see it.

4. **A related fact the custodian should have, not fix.** Only
   `test_products_api.py`'s three sites carry an exemption comment naming
   spec-043; `test_transport_api.py`, `test_auth_api.py`,
   `test_debug_toolbar_api.py` and `test_list_field_async_api.py` declare their
   posture in a module docstring that names a *different* spec, or names the
   sync-only `graphql_client.py` exemption, or names nothing. Measured, dated,
   and **not this cohort's to discharge**: it was already the state at HEAD, it
   spans files in no cohort's write set, and it is the same undeclared-drift
   population `### Decision 3` identified. It matters here only because a DoD
   sentence rewritten to say "every retained raw `client.post(...)` carries the
   comment" would be a false completion claim on the day it is written.

5. **The live-tier `README.md` `Async` bullet, with corrected replacement text.**
   Worker 0 has already carried the ownership gap to the maintainer
   (`build-043-test_client-0_0_14.md` `## Items Cohort D routed to Worker 0`
   item 1), so this is the wording, not the routing. The bullet covers two files
   and only one of them changed. Accurate replacement:

   > **Async.** `test_list_field_async_api.py`: `django.test.AsyncClient` vs an
   > `AsyncDjangoGraphQLView` mount, declaring the `graphql_client.py` sync-only
   > exemption in its docstring. `test_relations_async_api.py`: the package's own
   > `AsyncTestClient` against the same mount shape, with a per-call `url=`; no
   > exemption owed, since the client is the house form. Async rows either way:
   > `@pytest.mark.django_db(transaction=True)`, relying on `tests/conftest.py`
   > to close per-task SQLite connections (else `ResourceWarning` = error here).

   `test_products_visibility_api.py`'s async rows (D4, D6) now drive
   `AsyncTestClient` too and the bullet names neither them nor the file; adding
   them is optional, but if the bullet is rewritten without them it stays an
   incomplete index of the async surface.

6. **The node-count warning, unchanged and now demonstrated twice.** 87 collected
   across the four modules at the time of this pass (my own `-n0` run), which
   matches Worker 2's and Worker 3's readings — and is a timestamp, not a
   constant. The population moved during the planning pass (85 → 87) because the
   concurrent spec-050 session appended two rows. No artifact should publish a
   fixed total for it; a pass that needs one measures it with `--collect-only`
   and says when.

7. **A boundary Cohort C owns that a live row outside its write set now
   exercises.** D8 is the first live row driving
   `testing/client.py::TestClient._assert_file_placeholders` and reaching the
   `"variables" not in body` guard's neighbourhood. Cohort C is respelling that
   guard concurrently. Its closure should record that a live row outside its
   write set now depends on these guards' behavior, so a later respell of either
   cannot be graded on `tests/testing/test_client.py` alone. (For this cohort the
   two spellings are equivalent: D8 passes a non-empty `variables=`, so neither
   `if not variables:` nor `if "variables" not in body:` can reject it.)

8. **Two items from the plan's own notes that stay exactly as written**, re-read
   against the landed diff: `test_resource_policy_api.py`'s module docstring
   keeps its "over `django.test.Client`" clause (its sync rows route through
   `TestClient` → `django.test.Client`, so the clause is true, and rewriting it
   would be unearned scope); and the artifact-name discrepancy with escalation 3
   (`bld-043-review-4-live_post_conversion.md` vs this file) is a naming note
   only — the applied partition table wins.

### Deferred work for the final gate

`bld-043-final.md`'s `### Deferred work catalog` is built from these. Each names
its owner or says explicitly that it has none yet.

- **The live-tier `README.md` `Async` bullet is falsified and unowned.** Source:
  this artifact's Plan note 1, build-report note 2, review Low 3, and item 5
  above (which corrects the recommended wording). Already carried to the
  maintainer by Worker 0 as the cycle's one undischargeable item; the `.md` is
  outside every cohort's fence and homing it needs a KANBAN DB edit the fence
  also excludes. Corrected replacement text is on disk above, so the item does
  not die with this artifact.
- **The shared async live-tier post helper.** Five near-identical
  `AsyncTestClient().query(...)` bodies across four modules, a sixth unconverted
  raw post in `test_list_field_async_api.py`. Escalated above as a contract-level
  decision (reverses `graphql_client.py`'s sync-only contract and `AGENTS.md`'s
  async-exemption rule); needs a named owner card, nominee
  `TODO-ALPHA-053-0.0.15`. **Not deferred on a trigger** — the plan's "a sixth
  async site" trigger was already met when written and is retired here.
- **No gate fails a raw `.post(` / `.generic(` on a Django client in
  `test_query/` that carries no declaration.** Nothing in `scripts/` or
  `.pre-commit-config.yaml` sees it; five files drifted in two months precisely
  because no gate exists. Out of every cohort's fence (a KANBAN DB edit). This is
  `START.md`'s "rule w/o gate rots" with a measured population behind it.
- **Undeclared raw-request posture in four live files** —
  `test_transport_api.py`, `test_auth_api.py`, `test_debug_toolbar_api.py`,
  `test_list_field_async_api.py` retain raw client requests without a spec-043
  exemption comment (item 4 above). Pre-existing at HEAD, spans files in no
  cohort's write set, same population as the missing gate. Named so a DoD
  sentence is not written as if it were discharged.
- **`test_list_field_async_api.py`'s conversion** belongs to the concurrent
  spec-050 cycle (`### Decision 3`), not to this one. Recorded so the final gate
  does not read its surviving raw post as this cohort's miss.

### Summary

Cohort D converted nine raw live-tier posts onto the package's own test clients
across four files — three sync sites through `graphql_client.py::post_graphql`,
five async sites through `AsyncTestClient`, one multipart site through
`TestClient(..., files=...)` with its hand-rolled helper deleted — took no
exemption, and changed no assertion. Every one of the 13 dispatched boxes landed
and was re-derived here against the diff. The two Medium findings were
corrections to my own plan's measured claims (a `variables={}` census blind to a
positional argument, and a caller count of 15 that is 17) and are fixed in place,
along with a third wrong figure in the same paragraph that the review did not
reach. The three Lows are graded and recorded, one of them with a correction to
the fix it recommended. The load-bearing claim — no assertion weakened — is
signed on two independent assertion-level instruments agreeing to the member,
plus my own re-measurement of the two rows a green run cannot speak for.

### Spec changes made (Worker 1 only)

**None.** Under the applied ownership partition
(`build-043-test_client-0_0_14.md` `## Ownership partition — correction
applied`) `docs/SPECS/spec-043-test_client-0_0_14.md` and its `-rationale.md` are
Cohort C's custodian's exclusively, and Cohort C's own final verification is
where this cohort's amendments land. They are consolidated on disk under
`### Notes for Worker 1 (spec reconciliation)` above — the mechanism
`BUILD.md` `### Cohorting, naming, and closure` names for exactly this case.

**Deferral reasons owed for un-ticked boxes: none.** All 13 boxes are `- [x]` and
all 13 were confirmed against the diff.

**Plan-text corrections made this pass** (this artifact only, no spec, no source):
`### Census` — `::_post` caller count 15 → 17, with the enumeration that
establishes it and a note that the paragraph's "enumerated rather than counted"
claim was false of itself; `### DRY analysis` — the variables-truthiness
paragraph rewritten around an AST enumeration that can see positional arguments,
correcting both "0 occurrences" → one (positional,
`test_resource_policy_api.py:522`, already on the converted path at HEAD) and
"two helpers" → one; `### Implementation steps` D1 and D1's checklist box — 15 →
17 callers.
