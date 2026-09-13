# Escalation 043/3 — the live tier's undeclared raw posts (review-2 finding M4)

Raised by: `docs/builder/bld-043-review-2-code_verification.md` `### V2`, `M4`, `### Notes for Worker 1` item 4
Tree graded: HEAD `96b9e047` (the working tree's five files under question are clean against it; verified at write time)
Investigator posture: read-only on every `.py`, the spec, and every other worker's artifact; this memo is the only file written
Status: investigation-complete; maintainer decision pending

## Verdict in four lines

The reviewer's site count is right (16 `.post(` sites in the 27-file population) and its file count is off by one (8 files, not 9). Its classification is wrong in the direction that matters: **at least 9 of the 10 flagged sites are not exemptions — they are unconverted posts the package client already covers**, in files that did not exist when spec-043 shipped. Writing the nine one-line exemption comments would be the laundering the spec forbids. Recommendation: **fix here as conversions, not comments, under a recorded re-partition (Cohort D over four files); the fifth file belongs to the live spec-050 cycle and is not this cycle's to touch.** Counter-argument and deferral mechanism are in `## Recommendation`.

## 1. Census — instrument first, results second

### Instrument

Script: `<scratchpad>/census.py` (reproduced verbatim in `## Appendix A`). Run as `uv run python <path>` from the repo root; a heredoc-equivalent, no shell loops (`START.md` `## Instruments that lie`, zsh word-splitting).

- **Population** derived from `os.listdir("examples/fakeshop/test_query")` filtered to `*.py`, asserted `len(files) == len(test_*.py) + 1` (the `+1` is `conftest.py`). Not derived from any grep. `examples/fakeshop/graphql_client.py` is swept **separately** as the shared helper module because it sits outside the directory; it is reported but not counted in the population.
- **Sweep** is AST-based, not textual: every `ast.Call` whose callee is an `ast.Attribute` with `attr in {post, get, put, patch, delete, head, options, trace, generic, request}`, with the receiver's source segment recorded. A receiver is classed *http-looking* when its text contains `client` / `handler` / `communicator` or is a `Client(` / `AsyncClient(` construction. Every other match (`payload.get`, `Model.objects.get`, `sys.modules.get`) is printed too so the exclusion is visible, not silent.
- **Every spelling** the brief asked about is therefore covered by construction: `client.post(`, `self.client.post(`, `Client().post(`, `AsyncClient().post(`, `async_client.post(`, `http_client.post(`, a helper wrapping a post (the helper's own `.post(` is the site; its callers are counted in `## 2`), `.generic("POST", ...)`, and `.get(` where an operation rides a GET.
- **Declarations** are swept per file by regex `exempt|wire.shape|raw.envelope|raw.multipart|spec-043` (case-insensitive), then read in context (`## 2`).
- A **textual** `grep -o '\.post(' | wc -l` per file was run as a second instrument to reconcile against the reviewer's count.

### Results

Population: **27** files (26 `test_*.py` + `conftest.py`). Both instruments agree: **16 `.post(` sites on a Django test client, in 8 files.** Plus one raw POST the `.post(` vocabulary cannot see and 23 raw GETs the spec's vocabulary excludes.

| Instrument | Sites | Files | Notes |
| --- | --- | --- | --- |
| Reviewer (V2) | 16 `.post(` | **9** | table in V2 lists 8 files |
| This memo, AST | 16 `.post(` on a client | **8** | + `graphql_client.py::post_graphql_raw` (outside population) makes 17 / 9 |
| This memo, text grep `\.post(` | 16 | 8 | matches AST exactly; no docstring-only `.post(` mention exists |
| This memo, `.generic(` | **1** | 1 | `test_transport_api.py::_post_multipart` — a raw multipart POST spelled `client.generic("POST", ...)` |
| This memo, `.get(` on a client | **23** | 4 | `test_products_api.py` 5 (operations riding GET), `test_transport_api.py` 12, `test_debug_toolbar_api.py` 5, `test_auth_api.py` 1 |

**Where this differs from the reviewer:** the "9 files" figure is not reproducible from the population; it is 8, or 9 only if `graphql_client.py` is counted, and that file is outside the stated population. The `.generic(` POST is a 17th raw-post-in-substance site inside the population that a `.post(` grep is blind to; it is declared (module docstring, `test_transport_api.py`) so it changes no verdict, but it is the second blind spot in a census that claimed "every spelling". The 23 GETs are outside the spec's exemption vocabulary (`client.post(...)`) *and* outside the helper's contract (`TestClient` has no GET path), so they are not part of M4; they are listed so the population is honest.

Per-file `.post(` sites, both instruments: `test_auth_api.py` 1 · `test_error_policy_api.py` 2 · `test_list_field_async_api.py` 1 · `test_products_api.py` 3 · `test_products_visibility_api.py` 4 · `test_relations_async_api.py` 1 · `test_resource_policy_api.py` 2 · `test_transport_api.py` 2. Sum 16.

## 2. Per-site classification

Spec exemption classes (`docs/SPECS/spec-043-test_client-0_0_14.md` Slice-2 checklist and Decision 11, identical at HEAD and in the dirty rewrite): (a) hand-built multipart `operations` / `map` assertions, (b) malformed-body negatives, (c) content-type negotiation, (d) "the `test_multi_db.py` custom-view plumbing". The governing sentence: *"a test keeps raw `client.post(...)` only when the raw envelope is the test's subject … if a conversion would weaken one, that test takes the exemption instead."*

Two facts settle most rows below:

1. **Class (d) is empty.** Its only named exemplar, `test_multi_db.py`, drives `TestClient(client=client).query(...)` inside `override_settings(ROOT_URLCONF=__name__)` at HEAD (six call sites; converted in `653a3841` and extended in `18f2446f`). The spec's own exemplar disproves the class: a module-level `urlpatterns` + `_CURRENT["schema"]` mount is reached by `TestClient(...).query(..., url=<mount>)` — Decision 7's per-call `url=` exists for exactly this ("a one-call test mount", `graphql_client.py::post_graphql` docstring). Same file, `test_resource_policy_api.py::_post` already does it: `graphql_payload(query, client=client, variables=variables, url=mount)`.
2. **`AsyncTestClient` is live-proven** against the fakeshop mount (`test_client_api.py`; `test_kanban_mutations_api.py` L532) and accepts `client=`, `url=`, `assert_no_errors=False`. "Async" is therefore not a spec-043 exemption; it is the README's *graphql_client.py* exemption (sync-only helper module), a different regime (`## 3`).

| # | Site (`path::symbol`, HEAD line) | Receiver | What the row asserts | Spec class met? | Covered by | Declared? |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `test_error_policy_api.py::_post` L234 | `(client or Client()).post` | 18 callers; JSON envelope of a probe mount (`/ep/`, `/ep-off/`, …) via `pytest.mark.urls(__name__)` | **none** — a per-file hand-rolled POST-decode helper, the exact shape Slice 2 says to delete | `TestClient(client=client).query(q, variables=v, assert_no_errors=False, url=mount)`; `.response` / `.response.json()` | no |
| 2 | `test_error_policy_api.py::test_the_sync_and_async_transports_produce_the_same_masked_entry` L554 | `AsyncClient().post` + `_await_response` | masked-entry parity, correlation ids differ | **none** — subject is the entry, not the envelope | `_await_response(AsyncTestClient().query("{ boom fine }", assert_no_errors=False, url="/ep-async/"))` | no |
| 3 | `test_products_visibility_api.py::test_unoptimized_relation_hides_private_child_over_http` L61 | `Client().post` | `data == {"categories": [{"items": []}]}` via `_CURRENT` mount (upstream `GraphQLView`) | **none** — raw string body is well-formed JSON; subject is visibility | `TestClient().query(..., assert_no_errors=False)` (mount is at the default `/graphql/`) | no |
| 4 | `test_products_visibility_api.py::_post_async_visibility_query` L101 | `AsyncClient().post` | returns raw response; caller asserts status + data | **none** | `(await AsyncTestClient().query(..., assert_no_errors=False, url="/graphql-async/")).response` | no |
| 5 | `test_products_visibility_api.py::_post_visibility_query` L127 | `Client().post` | 5 callers; JSON payload against a per-test schema | **none** — hand-rolled helper | `TestClient().query(query, assert_no_errors=False).response.json()` after the status assert | no |
| 6 | `test_products_visibility_api.py::test_async_forward_fk_target_visibility_hides_a_private_target_over_http` L250 | `AsyncClient().post` | `data is None` + exact non-null message | **none** | as 4; keep `res.response.json()` so both assertions are untouched | no |
| 7 | `test_relations_async_api.py::_post_async` L95 | `AsyncClient().post` | 3 callers; `errors is None` + exact `data` (the regression assertion, per its docstring) | **none** — subject is the async lazy-load arms | `AsyncTestClient().query(query, assert_no_errors=False, url="/graphql-async/")`; `.response.json()` | no |
| 8 | `test_resource_policy_api.py::_multipart` L919 | `client.post(mount, data=body)` | 1 caller (`test_an_oversized_upload_is_rejected_by_the_policy_not_by_the_body_cap`): the rejection names one of three upload bounds | **arguable (a)** — hand-built `{operations, map, "0", "1"}` envelope; but the row never asserts on labels or map, and `extensions/resource_policy.py::_ValueBudget._charge_upload` charges each file value as it is walked, label-agnostic | `TestClient().query(_SPECIMEN, variables={"d": {...}}, files={"d.attachment": f0, "d.image": f1}, assert_no_errors=False, url="/rp-uploads/")` — unverified by execution; the one row a Worker 2 must run | no |
| 9 | `test_resource_policy_api.py::test_sync_and_async_transports_share_one_typed_error_code` L1251 | `async_client.post` + `_await_response` | typed code / bound / charge equal across transports | **none** — same shape as 2 | `_await_response(AsyncTestClient().query(_NODES, variables=variables, assert_no_errors=False, url="/rp-values-async/"))`; `json.loads(res.response.content)` unchanged | no |
| 10 | `test_list_field_async_api.py::_post_async` L79 | `http_client.post` (`client or AsyncClient()`) | 27 callers; `view_class=` and `extra_settings=` plumbing around the post | **none** under spec-043; declares the **README's** graphql_client.py exemption (true, different regime) | `AsyncTestClient(client=client).query(query, variables=variables, assert_no_errors=False, url="/graphql-async/")` — its sync twin `test_list_field_api.py::_post_raw` already routes `post_graphql(..., url="/graphql-test/")` → `TestClient` | module docstring, wrong regime |
| 11 | `test_products_api.py` L3812, L3875, L4631 | `client.post` | arbitrary-label `{operations, map, "0"}` envelope the path-keyed builder never emits; docstring says so | **(a) yes** | — | yes, inline per site |
| 12 | `test_transport_api.py::_post_bytes` L485, `::_post_multipart` L770 (`.generic`), L1441 | `client.post` / `client.generic` | exact byte bodies, body-cap, charset, hostile `Host`, `secure=`, `enforce_csrf_checks=` | **(a)(b)(c) yes** | — | yes, module docstring |
| 13 | `test_auth_api.py::test_login_and_logout_face_djangos_real_csrf_check::_raw_post` L644 | `client.post` (`Client(enforce_csrf_checks=True)`) | 403 without token, success with `HTTP_X_CSRFTOKEN` | **soft** — `client.py::TestClient` docstring names `client=Client(enforce_csrf_checks=True)` + `headers=` as the supported way to test CSRF; the exemption is declared and reads honestly, but the row is convertible | `TestClient(client=client).query(q, variables=v, headers={"X-CSRFToken": token}, assert_no_errors=False)` | yes, test docstring |
| — | `graphql_client.py::post_graphql_raw` L62 | `graphql_client.post` | shared raw-body helper (malformed bodies) | **(b) yes** | — | yes, function docstring (outside population) |

**Bottom line of the table:** of the reviewer's ten M4 sites, nine (rows 1–7, 9, 10) meet no spec exemption class and one (row 8) meets one only nominally. The reviewer's "honest in substance" verdict rested on class (d), which the spec's own exemplar no longer exercises. This is not a missing-comment defect; it is nine unconverted sites plus one arguable one.

## 3. What the two authorities actually require

**Spec** (`docs/SPECS/spec-043-test_client-0_0_14.md`, Slice-2 checklist; byte-identical at HEAD L434–440 and in the dirty rewrite L318–324):

> "… keeps its raw `client.post(...)` with a one-line comment naming this exemption — the helper exists to remove boilerplate, not to launder tests whose point is the wire shape"

Unit = **per site, inline comment**. Repeated in `## Test plan` ("each retained raw `client.post(...)` carries the wire-shape-exemption comment") and the DoD.

**Live-tier README** (`examples/fakeshop/test_query/README.md` `## Clients, transports, credentials`, first line):

> "`graphql_client.py` helpers = default for every ordinary JSON row. Exemptions stated in the exempt module's docstring, never inferred."

Unit = **per module, docstring**. Its subject is exemption from **`graphql_client.py`** (the sync shared helpers), not from `TestClient`. Its `Async` bullet then says async rows "declare the helper exemption" and routes them to `django.test.AsyncClient` — it never mentions `AsyncTestClient`, though the same section's `Test client family` bullet lists it.

So the two sources ask for **different units about different helpers**. They do not conflict on substance (both say: raw post only when the envelope is the subject, and say so in writing), but a module docstring satisfies the README and not the spec, and an inline comment satisfies the spec and not the README. **Stronger authority for M4:** the spec — the reviewer's finding is a spec-slice sub-check, the spec's Decision 11 is what `graphql_client.py::post_graphql_raw` and `test_products_api.py` cite, and the README itself defers ("this file vs a module docstring disagree → … fix the wrong one"; it is the index, the docstring/spec the description). The README's `Async` bullet is stale relative to `AsyncTestClient` and is out of this cycle's fence; noted for whoever next opens it.

## 4. The house form of the declarations that exist

Three forms are in use; none matches the spec's "one-line" spelling exactly, and they cite different exemption names:

- **Inline per-site comment** (spec form) — `test_products_api.py` L3805–3809, three sites, the only sites following the spec's unit:
  ```python
  # Raw-multipart exemption (spec-043): the subject is the
  # hand-built GraphQL-multipart {operations, map, "0"} envelope with an
  # arbitrary file label - the wire shape TestClient's path-keyed files=
  # builder never emits. The files= upload path is covered live in
  # test_uploads_api.py; keeping this raw pins the arbitrary-label envelope.
  ```
  (five lines, not one; states the class, the reason, and the sibling that covers the converted shape — the model to copy.)
- **Module-docstring paragraph** (README form) — `test_transport_api.py` L60–66: "Most rows drive a bare `django.test.Client` rather than the shared `graphql_client.py` helpers, because their subject IS the raw request envelope … which is the documented raw-envelope exemption in `README.md`." Names the README, not the spec.
- **Test-docstring sentence** — `test_auth_api.py` L634–636: "Raw `client.post` rather than the shared helpers because the subject is the request envelope itself (the documented raw-envelope exemption)." Names neither source.
- **Function docstring** — `graphql_client.py::post_graphql_raw`: "This is the documented raw-envelope exemption (spec-043)."

Vocabulary drift: "Raw-multipart exemption (spec-043)" vs "raw-envelope exemption" vs "wire-shape exemption" (spec prose) vs "helper exemption" (README `Async` bullet). If any new declaration is written, copy the `test_products_api.py` inline form and its `(spec-043)` anchor; it is the only one that states the class *and* names the converted sibling, which is what makes an exemption checkable.

## 5. Is this cycle the right place?

Facts bearing on it:

- **Dates.** Spec-043 shipped `2026-07-09` (`2db331cf`, `653a3841`). The five files were born `2026-08-04` (`test_error_policy_api.py`, `test_resource_policy_api.py`, `567cc6d0`), `2026-08-18` (`test_products_visibility_api.py`, `841e56d6`), `2026-08-23` (`test_relations_async_api.py`, `ddd5dbb9`), `2026-09-01` (`test_list_field_async_api.py`, `4d98ad98`). **Slice 2 could not have missed them; they did not exist.** M4 is therefore not a "silently-unaddressed spec slice sub-check" (`BUILD.md` `## Severity definitions`, the clause the reviewer graded on) — the sub-check was satisfied on the day the slice closed. It is standing-convention drift by later cards (047, 048, 050) and two fix commits against a rule that lives in spec-043 Decision 11 and the README. Severity stays Medium on a different clause ("unclear ownership … brittle"), and the reviewer's framing should be corrected before anything is built on it.
- **Fence.** All five are `.py` — inside "spec files and package `.py` source"? The fence says *package* `.py` source; these are example-project test files. The build plan's own Cohort C write set includes `examples/fakeshop/test_query/test_client_api.py`, so the plan already reads the fence as covering live-tier `.py`. Not a fence violation; a partition gap.
- **Dirty state.** None of the five is dirty at HEAD `96b9e047`. Two of them (`test_products_visibility_api.py`, `test_resource_policy_api.py`) were committed by the maintainer's concurrent sweep **yesterday** (`18f2446f`, 2026-09-12), which added rows calling `_post_visibility_query` and left the raw helper in place; the live-tier README was rewritten in `8b3b9ae1` the same day. The concurrent session is active in this exact tier.
- **Concurrent cycle ownership.** `test_list_field_async_api.py` is named 52 times in `docs/builder/bld-slice-4-live_acceptance.md` and `bld-final.md` reads `Status: review-fixes-applied … the final gate is NOT green`. **That file is inside the live spec-050 cycle's write set. No 043 cohort may touch it.** The tenth site is spec-050's to close (its sync twin already converted, `test_list_field_api.py::_post_raw`).
- **Size.** Four remaining files, 9 sites, 84 test nodes to re-run (`17 + 8 + 3 + 56`), one row (table row 8) whose conversion is unverified by execution. Every conversion has an in-tree precedent (`653a3841` on `test_mutation_atomicity.py`; `test_resource_policy_api.py::_post`; `test_multi_db.py`).
- **Gate.** Nothing gates this: `scripts/` and `.pre-commit-config.yaml` carry no check over raw posts in `test_query/` (grep: only `build_tree_md.py` mentions "exemption", unrelated). `START.md` `## Past mistakes` "Rule w/o gate rots" applies: five files drifted in two months. The root-cause fix is a gate, which is a `scripts/` + hook change — out of this cycle's fence.

## 6. Drafted text per site

**Do not write generic exemption comments on rows 1–7, 9.** No honest text exists: each would have to name a class ("custom-view plumbing" / "async") that `test_multi_db.py` and `AsyncTestClient` respectively disprove. What each site needs is the conversion in `## 2`'s "Covered by" column. Two representative drafts, assertions untouched:

Row 1 — `test_error_policy_api.py::_post` (mirrors `test_resource_policy_api.py::_post`):
```python
def _post(mount, query, variables=None, *, client=None):
    """POST one GraphQL document to a mount and return ``(response, parsed envelope)``."""
    res = TestClient(client=client).query(
        query, variables=variables, assert_no_errors=False, url=mount,
    )
    assert res.response.status_code == 200, res.response.content
    return res.response, res.response.json()
```
Semantics check: the raw helper sends `variables` when `is not None`; `TestClient._build_body` sends it when truthy. No caller in any of the five files passes `variables={}` (grep: 0), so the observable body is identical.

Row 7 — `test_relations_async_api.py::_post_async` (rows 4, 6, 10 are the same shape):
```python
async def _post_async(schema, query):
    """POST ``query`` against ``schema`` over the live async mount, returning the payload."""
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            clear_url_caches()
            res = await AsyncTestClient().query(
                query, assert_no_errors=False, url="/graphql-async/",
            )
        assert res.response.status_code == 200
        return res.response.json()
    finally:
        _CURRENT["schema"] = None
        clear_url_caches()
```

Row 8 — `test_resource_policy_api.py::_multipart`: convert (`files={"d.attachment": …, "d.image": …}`, `url="/rp-uploads/"`) **or**, if the maintainer wants the arbitrary-label envelope kept as a second vehicle for the upload bound, the only honest declaration is one that admits the label is not the subject:
```python
# Raw-multipart envelope (spec-043 exemption NOT claimed): the bound is charged
# per file value, label-agnostic, so this row would read the same through
# TestClient(files=...). Kept raw only so the arbitrary-label {operations, map,
# "0", "1"} shape also reaches the upload bounds; the path-keyed shape is
# test_uploads_api.py's.
```
That is a deliberate-duplication note, not an exemption. If neither wording is wanted, convert.

Row 10 — `test_list_field_async_api.py` module docstring: its declaration is **correct for the regime it names** (`graphql_client.py` is sync-only; the README's `Async` bullet requires exactly this sentence) and **silent on spec-043**. It is not "wrong"; it is a different exemption class the spec does not name, and under spec-043 the site is convertible. Owner: the live spec-050 cycle. Suggested amendment for its slice-4 owner, replacing the first docstring paragraph:
```
This suite is exempt from ``examples/fakeshop/graphql_client.py`` (synchronous by
construction) and drives the package's ``AsyncTestClient`` across a real
``AsyncClient`` -> ``AsyncDjangoGraphQLView`` -> graphql-core async-completion boundary.
```
plus the `_post_async` body change in `## 2` row 10.

**Spec text (Cohort A's fence, actionable now):** Decision 11 and the Slice-2 checklist name "the `test_multi_db.py` custom-view plumbing" as an exemption class. At HEAD that file is the counter-example. The class should be **removed** from both places (and from `## Test plan` if repeated), leaving (a)(b)(c); the rationale records why (per-call `url=`, Decision 7, is the mechanism for a test mount). Without this, the next author reads the spec, sees their `_CURRENT["schema"]` mount, and takes the exemption exactly as five did.

## Recommendation

**Fix here — as conversions, under a recorded re-partition.** Concretely:

1. Worker 0 adds **Cohort D** to `build-043-test_client-0_0_14.md` `## Ownership partition` (`BUILD.md` `### Parallel cohorts…`: "re-partitions, and records the correction in the plan"): Worker 2 writes, Worker 3 reviews; write set exactly `examples/fakeshop/test_query/test_error_policy_api.py`, `test_products_visibility_api.py`, `test_relations_async_api.py`, `test_resource_policy_api.py`, plus its artifact `bld-043-review-4-live_post_conversion.md`. Sequential after Cohort C if C is dispatched (it is not, per review-2), else concurrent with A — no file overlaps A.
2. Worker 2 converts the 9 sites per `## 2`, deletes nothing else, changes no assertion, and records the exact pytest commands for the 84 nodes; row 8 is the one that must be executed before its `Status:` moves.
3. Cohort A removes class (d) from the spec (Decision 11, Slice-2 checklist) and records the reason in the rationale — spec-file edits already in its fence.
4. `test_list_field_async_api.py`: hand row 10 to the spec-050 cycle through Worker 0 (a note into its integration pass), not through this cycle.
5. The gate (raw `.post(` / `.generic(` on a Django client in `test_query/` without a `spec-043` declaration → fail) is out of fence; home it on `TODO-ALPHA-053-0.0.15` (Boundary hardening and system-wide DRY squeeze — already owns `.pre-commit-config.yaml` / CI changes and carries live-tier debt, the `TODO(spec-035)` anchor in `test_library_api.py`). The DB edit is the maintainer's; no worker's fence covers it.

**Strongest counter-argument, stated fairly:** this is not spec-043's defect. Every undeclared file postdates the ship by a month or more; the reviewer's Medium was graded on a clause ("silently-unaddressed spec slice sub-check") that does not hold once the dates are read, and a *reconciliation* cycle exists to make the spec match the tree, not to sweep other cards' tests into compliance. The maintainer's own session swept this tier 24 hours ago, added rows through one of these raw helpers, and left it — so either the maintainer judged it fine or is mid-flight there, and a Cohort D lands nine edits in files that session may reopen. Under that reading the right move is: Cohort A fixes the spec's class (d) (in fence, zero risk), the reviewer's M4 is re-described as convention drift, and the conversions + gate go to 053 as one item with a named owner. That is a coherent position; it costs the two months' drift continuing until 053 lands, with no gate.

Why the recommendation still says fix here: the edits are mechanical with three in-tree precedents, the four files are clean, no cohort owns them, the fence covers `.py`, and the alternative (comment-only) is rejected by the spec's own sentence — so the only two honest outcomes are convert-now or defer-with-owner, and convert-now is a day's work whose risk is bounded by 84 re-runnable nodes.

**What does not settle from evidence:** whether row 8's conversion preserves the exact `bound in {max_upload_count, max_upload_file_bytes, max_upload_total_bytes}` outcome. The charger is label-agnostic by reading; it has not been executed here.

## Appendix A — census script (verbatim)

```python
"""Census of raw HTTP calls in the live tier (examples/fakeshop/test_query/)."""
import ast, os, re, sys
ROOT = "/Users/riordenweber/projects/django-strawberry-framework"
TQ = os.path.join(ROOT, "examples/fakeshop/test_query")
files = sorted(f for f in os.listdir(TQ) if f.endswith(".py"))
tests = [f for f in files if f.startswith("test_")]
assert "conftest.py" in files
assert len(files) == len(tests) + 1, files
print(f"POPULATION: {len(files)} .py files = {len(tests)} test_*.py + conftest.py")
extra = [os.path.join(ROOT, "examples/fakeshop/graphql_client.py")]
HTTP = {"post", "get", "put", "patch", "delete", "head", "options", "trace", "generic", "request"}
tot = {}
decl = {}
for path in [os.path.join(TQ, f) for f in files] + extra:
    src = open(path).read()
    tree = ast.parse(src)
    lines = src.splitlines()
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    def encl(n):
        while n in parents:
            n = parents[n]
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return n.name
        return "<module>"
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in HTTP:
            recv = ast.get_source_segment(src, node.func.value)
            recv_l = (recv or "").lower()
            looks_http = any(k in recv_l for k in ("client", "handler", "communicator")) or "Client(" in (recv or "") or "AsyncClient(" in (recv or "")
            hits.append((node.lineno, node.func.attr, recv, encl(node), looks_http, lines[node.lineno-1].strip()))
    rel = os.path.relpath(path, ROOT)
    tot[rel] = hits
    d = [(i+1, l.strip()) for i, l in enumerate(lines) if re.search(r"exempt|wire.shape|raw.envelope|raw.multipart|spec-043", l, re.I)]
    decl[rel] = d
n_http = 0
n_post = 0
files_with_post = set()
for rel, hits in tot.items():
    http = [h for h in hits if h[4]]
    nonhttp = [h for h in hits if not h[4]]
    if http or nonhttp:
        print(f"\n== {rel}: {len(http)} http-looking, {len(nonhttp)} other .{{get,post,...}}( calls")
    for h in http:
        n_http += 1
        if h[1] == "post":
            n_post += 1
            files_with_post.add(rel)
        print(f"  L{h[0]:>4} .{h[1]}( recv={h[2]!r:<40} in {h[3]}")
    for h in nonhttp:
        print(f"  L{h[0]:>4} [non-http?] .{h[1]}( recv={h[2]!r:<40} in {h[3]}: {h[5][:80]}")
    if decl[rel]:
        print("  -- declarations:")
        for ln, t in decl[rel]:
            print(f"     L{ln}: {t[:130]}")
print(f"\nTOTAL http-looking calls: {n_http}; .post( on a client: {n_post} across {len(files_with_post)} files")
print(sorted(files_with_post))
```

Output summary line as run against `96b9e047`: `TOTAL http-looking calls: 41; .post( on a client: 17 across 9 files` — the 17 / 9 includes `graphql_client.py`; inside the 27-file population it is 16 / 8.
