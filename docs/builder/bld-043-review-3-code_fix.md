# Build: Review round 043 / cohort C — guard respell + contract text

Spec reference: `docs/SPECS/spec-043-test_client-0_0_14.md` (working tree; Cohort A's
reconciled rewrite, dirty and intended) and `docs/SPECS/appx/spec-043-test_client-0_0_14-rationale.md`
(new, untracked, Cohort A's deliverable)
Build plan: `docs/builder/build-043-test_client-0_0_14.md` `## Ownership partition — correction applied`
Status: final-accepted

## Plan (Worker 1)

### Cohort scope in one paragraph

Three maintainer decisions and five of Cohort B's findings. One production predicate is
respelled (`client.py::TestClient._build_body`, `if not variables:` →
`if "variables" not in body:`), one production docstring is restated
(`conf.py::testing_endpoint_setting`), and everything else is test-tier: six weakly pinned
boundaries get the rows `BUILD.md` `### Acceptance rule` demands, one live probe endpoint
becomes observably distinct so two rows named for the endpoint ladder can fail, one test
double that re-implements the production line it tests is deleted, and one `_safe_arg_repr`
argument position gains its containment row. The spec and rationale amendments are Worker 1's
and are **deferred to final verification** (`### Spec amendment timing — decided: deferred`).

### Spec status-line re-verification (this spawn)

`docs/SPECS/spec-043-test_client-0_0_14.md` line 72 reads
`Status: **COMPLETE (card DONE-043-0.0.14) — all three slices built and the card-wrap landed;
the 0.0.14 version release rode the joint cut.**` and the opening paragraph (lines 1-20)
still describes the shipped surface. This cycle is a post-ship reconciliation, not a rebuild:
nothing in Cohort C's scope falsifies either. **No header edit owed this pass.** Re-checked at
final verification against whatever Worker 2 landed.

### Working-tree baseline for this cohort

`git status --short` at plan time: 18 dirty paths tree-wide (the plan preamble recorded 6 on
2026-09-12; the concurrent session has moved, which is why the plan calls that number a
reading and not a constant). Of Cohort C's write set:

- `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/conf.py`,
  `tests/testing/test_client.py`, `examples/fakeshop/test_query/test_client_api.py` — all
  **clean against HEAD**. Every byte Worker 2 adds to them is this cohort's.
- `docs/SPECS/spec-043-test_client-0_0_14.md` — `M`, Cohort A's rewrite, intended.
- `docs/SPECS/appx/spec-043-test_client-0_0_14-rationale.md` — `??`, Cohort A's new file, intended.

Everything else dirty is the concurrent session's. **Never edit, never revert** (`AGENTS.md`
rule 34). Attribute by diff content, never by "files my task touched".

**This list moves while the cohort runs.** Between the first and last reading of this pass the
concurrent session began dirtying package source — `connection.py`, `keyset.py`,
`list_field.py`, `optimizer/nested_planner.py`, `optimizer/walker.py`, `orders/sets.py`,
`tests/test_connection.py`, `tests/test_keyset_connection.py` — none of it in Cohort C's write
set, and Cohort C's four files stayed clean throughout. So Worker 2's post-ruff
`git status --short` will show package `.py` files it never touched: that is a **stop-and-report
if it names a Cohort C file**, and otherwise nothing at all. It is also why the ruff runs must
be scoped to this cohort's own paths — a repo-wide `--fix` would rewrite that work.

Focused baseline, run at plan time:
`uv run pytest --no-cov -n0 -q -p no:cacheprovider tests/testing/test_client.py examples/fakeshop/test_query/test_client_api.py`
→ **52 passed**. This matches Cohort B's Run C pre-mutation reading exactly, so its recorded
measurements are still valid against this tree.

### What was re-derived rather than accepted

`BUILD.md` `## Claims are proven mechanically, never accepted on prose` and the dispatch both
require it, and three of Cohort B's premises were already overturned once this cycle. Every
claim this plan rests on was re-executed by this pass, in the session scratchpad, read-only
except where stated.

**1. The empty-`variables` guard is NOT redundant with the walker — confirmed.**
`<scratchpad>/probe_falsy.py`, run under `DJANGO_SETTINGS_MODULE=config.test_settings`,
`PYTHONPATH=examples/fakeshop`. Three columns over eight falsy-`variables` classes: the
builder as shipped, the walker called alone, and a re-implementation of the builder with the
guard removed and every other line kept.

| `variables` | `files` | builder (shipped) | walker alone | guard removed |
|---|---|---|---|---|
| `None` | `{"file": F}` | REJECT | REJECT `cannot descend into 'file'` | REJECT (walker) |
| `{}` | `{"file": F}` | REJECT | REJECT `no key 'file' at that level` | REJECT (walker) |
| `FalsyDict({"file": None})` | `{"file": F}` | REJECT | **ACCEPT** | **EMIT** `operations='{"query": "q"}'`, `map='{"file": ["variables.file"]}'` |
| `FalsyDict({"data": {"image": None}})` | `{"data.image": F}` | REJECT | **ACCEPT** | **EMIT**, same shape |
| `[]` | `{"0": F}` | REJECT | REJECT `not a valid index into a 0-item array` | REJECT (walker) |
| `FalsyList([None])` | `{"0": F}` | REJECT | **ACCEPT** | **EMIT** `map='{"0": ["variables.0"]}'` |
| `0` | `{"file": F}` | REJECT | REJECT `cannot descend` | REJECT (walker) |
| `""` | `{"file": F}` | REJECT | REJECT `cannot descend` | REJECT (walker) |

`FalsyDict` / `FalsyList` are `dict` / `list` subclasses whose `__bool__` returns `False`; a
`dict` subclass is inside the annotated domain `dict[str, Any] | None`. The three EMIT rows
are the boundary: `operations` carries **no** `variables` member while `map` points into
`variables.file`. That envelope is what escalation 1 traced to Strawberry's
`file_uploads/utils.py::replace_placeholders_with_files` → `KeyError` → HTTP 400
`"File(s) missing in form data"` — a message that blames the files, which are present.
**Cohort B's subsumption premise is false, and the guard decides a verdict.**

**2. The respelled predicate is verdict-identical — confirmed.** Same probe, fourth section:
the shipped `_build_body` and a `if "variables" not in body:` re-implementation were run over
all eight falsy classes plus four valid shapes (top-level file, nested input object,
`files={}` JSON post, no-files-no-variables). **12/12 identical outcome class, 0 mismatches.**

**3. `TESTING_ENDPOINT = ""` does not 404 — confirmed.** `<scratchpad>/probe_endpoint2.py`,
real fakeshop URLconf under `config.test_settings` with `ALLOWED_HOSTS` populated:

| posted path | status | `Content-Type` |
|---|---|---|
| `""` | **200** | `text/html; charset=utf-8` |
| `/None` | 404 | `text/html; charset=utf-8` |
| `/7` | 404 | `text/html; charset=utf-8` |
| `/missing-graphql-endpoint/` | 404 | `text/html; charset=utf-8` |

So the docstring's "a wrong endpoint **string** surfaces as an ordinary 404" is false for the
one string it most needs to cover, and true for the non-strings it excludes. The coercion that
makes the non-strings behave is present in the installed Django:
`inspect.getsource(django.test.client.RequestFactory.generic)` contains
`parsed = urlsplit(str(path))  # path can be lazy` (Django 6.1 as installed; escalation 2
swept every cached wheel 5.2.0 → 6.1.0 and found 2 sites per release). That same comment is
why `reverse_lazy(...)` works and why a `str` gate was rejected.

**4. "The traceback carries the failing status" is false — confirmed.** Same probe:
`response.json()` on the 404 raises
`ValueError: Content-Type header is "text/html; charset=utf-8", not "application/json"`.
The status appears nowhere in that message. It is visible only because pytest renders the
failing frame's locals under the default traceback style — an artefact of the runner, not a
property of the failure. Present at spec line 851 after Cohort A's rewrite, so it needs a
second custody touch exactly as escalation 2 says.

**5. `test_multi_db.py` was itself converted — confirmed.** `grep -c "TestClient"` → **9**;
`grep -n "client.post(\|\.generic("` → **0 hits**. It posts through
`TestClient(client=client).query(...)` at lines 1078, 1166, 1214 and `TestClient().query(...)`
at 1328, 1368, 1410. The "custom-view plumbing" exemption class named at spec line 321 and
line 1438 has **no surviving exemplar**.

**6. M1's probe is a transparent alias — confirmed by reading.**
`test_client_api.py::_alt_graphql_view` does `match = resolve("/graphql/")` then
`return match.func(request, ...)`, and the probe URLconf is
`[path("", include("config.urls")), path("alt/", _alt_graphql_view)]` — so `/graphql/` is
mounted under the probe URLconf too. Both rows
(`GraphQLTestCaseEndToEndTests::test_per_call_url_routes_to_the_probe_endpoint`,
`GraphQLTestCaseClassAttrEndpointTests::test_class_attr_endpoint_hits_the_real_view`) assert
only `assertResponseNoErrors(res)` plus `assertTrue(res.data["allItems"]["edges"])`. Both
assertions hold whether the request landed on `/alt/` or fell back to `/graphql/`. Cohort B
measured this rather than arguing it (Run B and Run C each added zero live rows), and the
reading confirms the mechanism.

**7. M3's double re-implements the line — confirmed.**
`tests/testing/test_client.py::_RecordingTestClient.request` body is
`self.seen_urls.append(url if url is not None else self.path)`, character-identical to the
expression in `client.py::TestClient.request #"url if url is not None else self.path"`.
`grep -n "_RecordingTestClient"` returns exactly two hits: the class definition (line 61) and
its single use (line 141, in `test_per_call_url_outranks_the_constructor_and_never_persists`).
**After the re-point, the class has zero callers.**

**8. L1's row is failable — confirmed.** `<scratchpad>/probe_key.py` passed a `str` subclass
key whose `__repr__` raises through `_assert_file_placeholders` at three rejection branches.
All three surfaced `AssertionError` with `files= path <unprintable HostileKey> …`. Without
`_safe_arg_repr(key)` the f-string would raise the consumer's `RuntimeError` instead, so the
row can fail.

### Two things in the dispatched scope this pass judges wrong

**A. L3's recorded reason is false.** Cohort B wrote that `Response.response`'s `None` default
"is load-bearing for dataclass field ordering against the engine base". It is not.
`strawberry.test.client.Response` declares three fields (`errors`, `data`, `extensions`) and
**none of them carries a default**, so a subclass appending a non-default field is a legal
dataclass. Executed:

```
@dataclass
class NoDefault(Base):
    response: Any
NoDefault(errors=None, data={}, extensions=None, response=1)  # constructs fine
```

The disposition (keep it; note, not change request) is right, but for a different reason:
`Response` is one of the six names on `django_strawberry_framework/testing/__init__.py`'s
`__all__`, so it is **shipped public surface on an `0.0.x` line**, and removing a default
narrows a constructor consumers may already be calling. Both in-repo construction sites
(`client.py::TestClient._finish_response` and `tests/testing/test_client.py` line 593) pass
`response=` explicitly, so the default is genuinely never exercised — which is what the
docstring already says. Recording the **correct** reason is the point of the finding:
`START.md` "Derived descriptions outlive sources" — a later reader who acts on the false
ordering rationale will conclude the constraint has evaporated and delete the default.

**B. M2's boundary count is wrong; it is six, not five.** Cohort B wrote "**Five boundaries**
(six entries; A1 and B1 are one boundary measured twice)" and then listed **six** numbered
items. Re-derived from its own three run tables: Run A's weakly pinned entries are #1 (0 rows),
#2, #6, #11, #12 (1 row each) = five boundaries; Run B adds no new boundary (B1 = A1,
B2 = A12); Run C's C1 is a **sixth, distinct** boundary that appears in no other run. So the
population is **six boundaries across eight entries**, not five across six. `BUILD.md`
`## Claims are proven mechanically`: a stated count reads as measured and propagates silently.
This plan dispatches all six.

### Boundary count, and the split question answered

`BUILD.md` `### Slice splitting` requires the answer in writing whether or not the split
happens.

Production boundaries this cohort **introduces**: **zero.** The guard respell replaces an
existing boundary with a verdict-identical predicate; the docstring restatement changes no
verdict at all. Boundaries whose failability Worker 2 must **measure**: **seven loops** —
one for the respelled guard (whose current 0-row reading is the whole reason item 1 exists)
and six re-measurements of the boundaries item 3 re-pins.

**Decided: do not split.** Two reasons, both load-bearing:

1. All six boundaries live in **one production module** behind **one contract** (spec-043's
   test-client family), and their rows live in one package-tier file plus one live-tier file.
   `### Slice splitting`: boundaries that cannot be separated — one contract making them a
   single decision — are one unit. Splitting would hand a second cohort the same module to
   re-derive from scratch, and re-derivation is where this cycle has already lost most of its
   time.
2. **Six of the seven loops are re-runs, not authored proofs.** Cohort B's manifests survive on
   disk at `docs/builder/temp-tests/043/` (`proofs.json`, `proofs-wide.json`,
   `proofs-mixin.json`, plus their reports and stdout), each carrying the exact anchor and the
   exact mutation for its boundary. Worker 2 copies each entry into its own manifest under
   `docs/builder/temp-tests/043/cohort-c/` and re-runs; the expensive half of a proof — deciding
   what mutation actually removes the boundary — is already done and recorded. Only entry 1's
   anchor changes, because the predicate it names is what item 1 rewrites.

**The escape hatch is named rather than assumed.** If the proof load turns out heavier than
this estimate — a re-measured mutation that no longer applies cleanly, or a boundary whose new
rows do not lift it above 1 — Worker 2 sets `revision-needed` under `ARTIFACT.md`'s
structural-drift pause (the Worker-2-set variant, routing back to **Worker 1** for a plan
revision) and says so in the build report, rather than folding boundaries into one mutation.
`### Slice splitting`: overload never surfaces as a refusal, it surfaces as thin proofs.

### Spec amendment timing — decided: deferred to final verification

`### Spec custody` gives Worker 1 the choice. **Every spec and rationale edit in this cohort's
scope is deferred to the final-verification pass**, for three reasons:

1. **The spec must describe what landed.** This whole cycle exists because spec-043 drifted
   from its tree. Writing Decision 9's and Decision 7's new contract text *before* Worker 2's
   diff exists would re-create that defect in the same pass that is supposed to close it — and
   the exact predicate, message, and row names are what the text has to quote.
2. **Cohort D is running concurrently and routes spec notes to me through its artifact's
   `### Notes for Worker 1`.** Those notes land in `test_query/` conversions, which is exactly
   the surface Decision 11's exemption-class edit touches. Making that edit now would mean
   opening Decision 11 twice and risking the second pass stranding the first.
3. **`START.md`: "Partial claim fix = dominant residual defect."** The endpoint claim alone has
   four spec sites plus a docstring; the guard claim has six. Doing each family once, in one
   pass, with the full site list enumerated before a byte is written
   (`START.md` "Enumerate, never grep-count, before writing") is what prevents the stranding
   this cycle has already hit twice.

Worker 2 loses nothing by the deferral: it implements this plan, never the spec, and never
reads the rationale (`BUILD.md` `### Who reads it, and when`).

### The spec and rationale sites enumerated now, so the deferred pass cannot miss one

Line numbers are pin-at-write-time navigational hints against the working-tree spec; every
site is re-located by content before editing.

**The endpoint-claim family (maintainer Decision 2) — four spec sites plus the docstring:**

- spec 202-205, the `ConfigurationError` "NOT used by this card" bullet —
  `#"endpoint value surfaces as an ordinary 404 at request time"`. Says *value*, which is the
  most accurate of the three spellings; still needs "ordinarily", because `""` is 200.
- spec 858-861, `### Error shapes` malformed-settings bullet —
  `#"*string* is a 404 at request time, which the previous bullet covers"`. The italicised
  *string* implies non-strings differ; they do not.
- spec 1198-1201, Decision 7 —
  `#"wrong endpoint string is an ordinary 404 at request time"`. Same defect.
- spec 840, `### Error shapes` non-JSON bullet header — `#"wrong endpoint → 404 HTML page"`.
  A parenthetical example of a cause, not a universal claim; graded and left unless the
  rewrite of 851 disturbs it. Recorded so the next reader knows it was examined, not missed.
- `conf.py::testing_endpoint_setting` docstring, last two sentences. Escalation 2 section 6A
  carries the proposed replacement text; it is the mechanism, not the reviewer's narrowing to
  "a wrong endpoint *string*", which would make the sentence **less** true.

**The false-on-its-own-date clause (maintainer Decision 2, second defect):**

- spec 851, `### Error shapes` non-JSON bullet — `#"the traceback carries the failing"`.
  Rewritten to say what actually happens: pytest's default traceback shows the failing
  `HttpResponse` as a frame local of `_parse_json`, the `django.request` log names the path,
  and the exception message itself names only the `Content-Type`. Verified false at HEAD and
  in Cohort A's rewrite, so this is a **second custody touch**, not a regression of Cohort A's.

**The guard family (maintainer Decision 1) — six spec sites:**

- spec 862-866, `### Error shapes` `files=`-without-variables bullet —
  `#"if not variables: raise AssertionError(...)"`. Escalation 1 carries the replacement.
- spec 1256-1264, Decision 9 — `#"and then raises when variables is falsy"`.
- spec 1584-1588, `## Edge cases` —
  `#"with an explicit raise AssertionError when a truthy files arrives"`.
- spec 1415, Decision 11 — `#"the empty-variables guard, the per-path placeholder walker"`;
  the label stays accurate under the respell, confirm rather than edit.
- spec 1833, Test plan — `#"the empty-variables guard pins from the"`; same.
- spec 1863 and 2020, Test-plan coverage paragraph and DoD — `#"empty-variables"`; same.

The last four are the reason the label `empty-`variables` guard` is **kept** rather than
renamed: renaming it would strand four citers for no contract gain, and the respell does not
change what the guard rejects. `START.md`: stripping a label vocabulary is a rename that
strands every citer.

**The exemption-class drop (maintainer Decision 3) — two spec sites:**

- spec 318-322, Slice-2 checklist exemption sub-bullet — the clause
  `#"test_multi_db.py][test-multi-db] custom-view plumbing"` and its link use.
- spec 1436-1439, Decision 11 "switchover's own discipline" —
  `#"test_multi_db.py][test-multi-db]'s custom-view plumbing"`.

Both keep the surviving classes (the raw envelope is the test's subject: hand-built multipart
negatives, malformed-body tests, content-type probes). Dropping the class means the
`[test-multi-db]` reference may become unused — **audit refs-vs-defs after the edit** and
remove an orphaned definition, or keep it if another use survives. This is the exact failure
mode Cohort A hit (15 undefined references introduced by a move nobody re-audited), recorded
in `docs/builder/worker-memory/043-worker-1.md`.

**Test plan and DoD extension.** Cohort C adds named rows to branches the Test plan's
scenario-15 inventory enumerates and whose coverage paragraph claims "every branch has a named
owner". F7 was exactly this defect for the post-ship commits; re-creating it here would be
worse, since this cohort authored the rows. The deferred pass extends scenario 15's
package-tier inventory and scenarios 6-8's endpoint-ladder inventory with the rows Worker 2
actually landed, read off the diff, never off this plan.

**Rationale entries.** `docs/SPECS/appx/spec-043-test_client-0_0_14-rationale.md`, keyed to the
owning Decision by heading and anchor (`BUILD.md` `## Spec rationale extraction`: an entry
naming no decision cannot be looked up). One entry per maintainer decision, each carrying the
rejected alternatives **with the reason each lost**, taken from
`build-043-test_client-0_0_14.md` `## Maintainer decisions taken mid-cycle`:

- Decision 7's block — maintainer Decision 2: no validation added; rejected "reject a non-`str`
  at the accessor" (breaks `reverse_lazy`, a working spelling today, and Django's own
  `# path can be lazy` comment sits on the line that makes it work); rejected "leave both as
  they are" (the docstring is genuinely false, for `""`, not for the class anyone suspected).
- Decision 9's block — maintainer Decision 1: the guard is respelled, not deleted; rejected
  "delete it and let the walker own every rejection" (the walker does not catch the
  falsy-container class at all); rejected "keep `if not variables:` and only add rows"
  (smallest diff, but leaves a truthiness test where absent and empty differ —
  `BUILD.md` `### Fail-open shapes`' named suspect); superseded "Cohort B's own
  keep-and-pin reasoning" (conclusion survives, reasoning does not — it invoked "never a
  weaker boundary" while asserting the guard decides no verdict, which would forbid deleting
  any dead branch). Plus the falsy-container census as the evidence.
- Decision 11's block — maintainer Decision 3's spec half: the "custom-view plumbing" class is
  dropped because its only named exemplar was itself converted; rejected "write the nine
  exemption comments" (a false declaration forecloses the next reader's question); rejected
  "defer to a later card" (naming the card needs a KANBAN DB edit this cycle's fence excludes).
- L3's disposition, homed under Decision 6 (the typed `Response` + raw-response field), with
  the **corrected** reason from finding A above.

### DRY analysis

**Helper inventory checked.** Refreshed for the **whole package** this pass —
`django_strawberry_framework/`, not just `utils/` — with the AST walk from `worker-1.md`
`### Package-wide helper inventory before helper planning`, written to
`<scratchpad>/helper-inventory.md` (**2081 lines**, 84 modules). Grepped for the shapes this
cohort could need: `validate`, `guard`, `reject`, `endpoint`, `_safe_arg_repr`,
`_safe_type_name`, `marker`. Relevant candidates found and their disposition:

- `exceptions.py::_safe_arg_repr(value)` — already imported and already used at all six call
  sites in the walker. **Reused, not re-authored**; L1 adds a row on an argument position,
  no new code.
- `conf.py::_normalize_user_settings(value)` — validates the settings **dict**, not any key's
  value. Not a seam a per-key gate could ride, and maintainer Decision 2 adds no gate anyway.
- `conf.py::upstream_patches_enabled()` — the module's **only** in-accessor validator, and its
  own docstring gives the DRY reason (four consumer modules, one gate). `testing_endpoint_setting`
  has one consumer. Confirms Decision 7's posture rather than offering a shape to copy.
- `utils/strings.py::_plain_text` — the only shared "must be a string" body; its message
  ("String helper input must be a string") is for the naming helpers and would be a misuse here.

**No new helper, constant, validation branch, coercion utility, or test helper is justified,
and none is planned.** Every production change is an edit to an existing line or docstring.

**Existing patterns reused.**

- `tests/testing/test_client.py::_RecordingDjangoClient` (lines 80-88) — the correct recording
  seam: it stands in for `django.test.Client` and records the URL **the real `request()` chose**.
  Already used by `test_empty_files_dict_is_a_plain_json_post` (line 382), by
  `_MixinProbe` (line 95), and subclassed by `_ExtensionsTransport` (line 457). M3's re-point
  and item 12 both consume it; neither authors a second recorder.
- `_CannedJSONResponse` (lines ~50-58) — what `_RecordingDjangoClient.post` already returns, so
  the re-pointed row's existing `isinstance(res.response, _CannedJSONResponse)` assertion
  survives unchanged.
- `@pytest.mark.parametrize` — already the file's idiom for exactly this shape
  (`test_files_placeholder_noncanonical_list_index_raises` runs six index cases as six node
  ids, lines 212-223). Every "split one node id into N" item in this plan uses it rather than
  inventing a loop helper. `START.md`: a `for` loop inside one test is ONE node id; widening
  the loop never raises the failability count above 1.
- `override_settings(ROOT_URLCONF=__name__)` — already the live file's probe idiom at
  lines 333 and 345. M1 changes what `_alt_graphql_view` returns, not how it is mounted.

**New shared shapes, assigned.** Two cohorts run concurrently, so `worker-1.md`
`### DRY analysis shape` makes naming the shared shapes mandatory. Enumerated:

- **The endpoint-probe marker header** (item 8). Lives in
  `examples/fakeshop/test_query/test_client_api.py`, which is **Cohort C's exclusively**.
  Cohort D writes four other `test_query/` files and must not author a second marker. Nothing
  in Cohort D's scope needs one; recorded so a collision cannot happen silently.
- **The `TestClient(client=...)` conversion idiom.** Cohort D converts nine live sites to it;
  Cohort C re-points one package-tier row at a recording transport. Both **cite** the shape
  `client.py::TestClient.__init__` already offers; **neither authors it.** No shared helper is
  created by either cohort, so there is no owner to assign.
- **The spec.** `build-043-test_client-0_0_14.md` `## Ownership partition — correction applied`:
  the spec is Cohort C's alone, and Cohort D routes everything through its artifact's
  `### Notes for Worker 1`. Checked at final verification (`### Final-verification obligations`).

**Duplication risk avoided.** A naive implementation of item 8 would add a second recording
double in the live file to observe which URL was hit. The marker header avoids it: the live
tier observes the **response**, which is what a live test can see, and the package tier keeps
the transport-level observation it already has. A naive implementation of item 12 would keep
`_RecordingTestClient` "for the other rows" — item 14 measures that there are none.

### Fail-open shape review of the planned change

`BUILD.md` `### Fail-open shapes` — read at plan time, so none is planned.

- The respelled predicate `if "variables" not in body:` is a **membership test on a dict the
  method just built**, not a truthiness test on consumer input. It is `BUILD.md`'s own
  prescription — guard the ANSWER, not one spelling of the incoherent input — applied to the
  shape that section names first: "a truthiness test on a value that can be absent, where
  absent and empty mean different things". The shipped spelling is that suspect; the respell
  retires it.
- **No clamp, no `getattr` default, no `or` fallback, no broad `except`** is added anywhere in
  this cohort. The one `except Exception` in the module (around `len()` in the walker) is
  untouched; Cohort B verified it converts the blow-up into a **rejection**, and this plan
  neither widens nor narrows it.
- `conf.py::testing_endpoint_setting` keeps `getattr(settings, TESTING_ENDPOINT_KEY, "/graphql/")`
  **unchanged**. That `getattr` default stands in for an absent key whose absence is not
  meaningful (absent means "use the default"), so it is not the fail-open shape the catalogue
  names. Maintainer Decision 2 is explicit that no validation is added.

### Hot-path declaration

**None.** Inherited from `build-043-test_client-0_0_14.md`'s build-wide declaration and
re-verified for this cohort's scope rather than copied: every symbol Cohort C touches lives in
`django_strawberry_framework/testing/client.py`, `conf.py::testing_endpoint_setting` (read once
per `TestClient` construction), or a test file. No package module imports `testing.client`, so
nothing here runs per request, per resolver, per row, per connection, or per outbound message
in a deployed schema. The declaration rests on the module's **runtime position**, not on "no
executable code changed" — which matters, because this cohort does change executable code.

### Floor-verification scope

**None.** Inherited and re-verified. The cohort changes no Django / Strawberry / channels
integration seam: the respell is a dict-membership test inside the package's own body builder,
the docstring change is prose, and the test-tier work adds rows against seams that already
exist. Floor facts, from `BUILD.md` `## Floor verification` (the single canonical statement,
never restated from memory elsewhere): Django **5.2.16**, Python **3.10**,
strawberry-graphql **0.316.0**. No focused scope is assigned to any pass in this cohort.

One adjacent fact recorded so it is not mistaken for a floor obligation: the `str(path)`
coercion the endpoint docstring now describes was swept by escalation 2 across every cached
Django wheel from 5.2.0 through 6.1.0 (2 sites per release). That sweep is already done and
its conclusion is what the docstring states; it owes no re-run here.

### Static inspection

`uv run python scripts/review_inspect.py django_strawberry_framework/testing/client.py --output-dir <scratchpad>/inspect`
— exit 0, both outputs written. `--output-dir` points at the **session scratchpad**, never
`docs/shadow/` (`AGENTS.md` rule 23 over `BUILD.md` `### How to run`; the reconciliation the
build plan records). Required because the plan adds logic to an existing `.py` file well over
150 source lines (`client.py` is 565).

What the overview says, walked entry by entry:

- **Django / ORM markers: none.** Nothing to justify.
- **Repeated string literals: 2.** Neither is touched by this cohort.
- **Calls of interest: 4** — `set()` at 300 (the reserved-key guard, item 9's boundary),
  `isinstance()` at 347 and 375 (the walker's array / dict arms), `len()` at 357 (inside the
  guarded `try`). Each already carries a boundary and a row; none is a new finding.
- **Control-flow hotspots: 3** — `TestClient.query` (64 lines, 0 branch nodes),
  `_build_body` (67 lines, 5 branch nodes), `_assert_file_placeholders` (83 lines, 13 branch
  nodes). The respell changes one of `_build_body`'s five branch predicates and adds no
  branch; the branch count is unchanged after this cohort. Medium-tier complexity attention
  paid: the walker is the file's densest body and this cohort adds **no branch** to it (L1 is a
  row, not a branch).
- **Imports: 13**, one-way (`testing` → `conf`, `exceptions`), no cycle. Unchanged.

### Implementation steps

Ordered so each proof's scope is stable when it runs. Line numbers are pin-at-write-time
navigational hints — **verify against the current source before editing.**

**Step 1 — respell the guard** (`django_strawberry_framework/testing/client.py::TestClient._build_body`,
around lines 284-291, the block under `#"if not variables:"`).

Replace the predicate and the comment above it. The message text is **unchanged, byte for
byte** — six spec sites and one test docstring quote it, and this cohort changes the predicate,
not the contract. Escalation 1 `## Exact change under Option C` carries the exact block:

```python
        # Coherence, not truthiness: the multipart ``map`` points into
        # ``variables.<path>``, so the envelope must carry a ``variables``
        # member for it to point at. Read the member off the body just built
        # rather than re-testing ``variables`` - the emission above is the one
        # owner of when that member exists. Explicit raise (not a bare
        # ``assert``) so the guard survives ``python -O``.
        if "variables" not in body:
            raise AssertionError(
                "query(..., files=...) requires variables= carrying a None placeholder "
                "at each file's variable path (e.g. variables={'data': {'image': None}} "
                "for files={'data.image': f}).",
            )
```

Then confirm the walker's docstring tail `#"matching the empty-``variables`` guard above"`
still reads true — it does, and it is the reason the label is kept. Do **not** touch the
`if variables: body["variables"] = variables` emission at line ~276; the respell exists
precisely so that line becomes the single owner of when the member exists.

**Step 2 — restate the endpoint docstring** (`django_strawberry_framework/conf.py::testing_endpoint_setting`,
docstring lines ~504-514). The function **body is unchanged**:
`return getattr(settings, TESTING_ENDPOINT_KEY, "/graphql/")`. Replace only the last two
sentences (from `#"No validation beyond the shared"`). Escalation 2 section 6A carries the
text; it must say, in the module's own voice:

- no validation beyond the shared malformed-dict guard;
- the value is handed to `django.test.Client.post` unchanged, which coerces it with `str()`
  — so a `reverse_lazy()` endpoint works, and a `None` posts to `/None`;
- a wrong value surfaces at request time as **whatever the URLconf serves at that path** —
  ordinarily a 404 — through Django's non-JSON `ValueError` naming the response's
  `Content-Type`.

The third clause is the one that matters: "ordinarily a 404" is what makes the sentence true
for `TESTING_ENDPOINT = ""`, which routes to the URLconf root and returns 200. Do **not**
narrow to "a wrong endpoint *string*"; that is the reviewer's fix and it makes the sentence
less true, not more.

**Step 3 — item 8, the live probe marker** (`examples/fakeshop/test_query/test_client_api.py::_alt_graphql_view`,
lines 60-67). Keep the delegation and keep the positive hit. Stamp a distinctive header on the
delegated response and assert it in both rows:

```python
def _alt_graphql_view(request, *args, **kwargs):
    match = resolve("/graphql/")
    response = match.func(request, *args, **kwargs)
    response["X-Probe-Endpoint"] = "alt"
    return response
```

Then in `GraphQLTestCaseEndToEndTests::test_per_call_url_routes_to_the_probe_endpoint` and in
`GraphQLTestCaseClassAttrEndpointTests::test_class_attr_endpoint_hits_the_real_view`, keep
`assertResponseNoErrors(res)` and the data assertion, and add
`self.assertEqual(res.response.headers["X-Probe-Endpoint"], "alt")`. A request that fell back
to `/graphql/` through `path("", include("config.urls"))` carries no such header, so the row
fails. Update each row's comment to say what the marker proves. **Do not weaken either row to
an exception-shape probe** — the positive hit on the real schema view is the contract Decision
11 chose, and the marker is a discriminator added beside it, not a replacement for it.

Worker 2 verifies the assignment executes against whatever the GraphQL view returns (Django's
`HttpResponseBase.__setitem__`) rather than assuming it; if the view returns a response type
that refuses header assignment, report it under `### Notes for Worker 1` instead of working
around it.

**Step 4 — item 12 + item 14, the recording seam**
(`tests/testing/test_client.py::test_per_call_url_outranks_the_constructor_and_never_persists`,
lines 133-152). Drive the **real** `TestClient.request` by supplying a recording Django client:

- construct `TestClient("/constructor/", client=_RecordingDjangoClient())`;
- read the effective URL off `transport.posts[i][0]` instead of `client.seen_urls[i]`;
- keep every existing assertion's intent: `/percall/` for the overridden call, `client.path`
  still `/constructor/` afterwards (the non-persistence guarantee), `isinstance(res, Response)`,
  `res.data == {"ok": True}`, `isinstance(res.response, _CannedJSONResponse)` (still true —
  `_RecordingDjangoClient.post` returns one), and the second un-overridden call falling back to
  `/constructor/`;
- then **delete `_RecordingTestClient`** (lines 61-77). Re-grep first
  (`grep -n "_RecordingTestClient" tests/testing/test_client.py`) and confirm **zero**
  remaining references before deleting — `START.md`: enumerate, never grep-count, before
  writing.

**Step 5 — item 13, split the mixin rung row**
(`tests/testing/test_client.py::test_mixin_endpoint_rungs_class_attr_settings_and_per_call`,
lines 550-570). It proves rungs 3, 1 and 4 in **one** function body, so any one of the three
failing is indistinguishable from the other two. Split into three node ids — rung 3
(`GRAPHQL_URL` beats settings/default), rung 1 (per-call `url=` beats the class attr), rung 4
(settings key with `GRAPHQL_URL` unset). Keep `_MixinProbe` / `_AltProbe` exactly as they are;
this is a decomposition, not a new fixture. Preserve each assertion's comment so the rung each
row proves stays legible.

**Step 6 — item 2/3/4, the guard's rows**
(`tests/testing/test_client.py::test_files_without_variables_raises_the_placeholder_guard`,
lines 160-173). Currently two `pytest.raises` calls in one function body — **one node id** —
both matching `"placeholder"`, which **every** walker message also contains, so the assertion
is non-distinguishing on two counts at once.

- Parametrize over `variables=None` and `variables={}` → two node ids.
- Change every `match=` to `"requires variables="`, the guard's own distinctive phrase. Confirm
  no walker message contains it (`grep -c 'requires variables=' django_strawberry_framework/testing/client.py`
  must be 1).
- Add a **falsy-`dict`-subclass row**: a `dict` subclass whose `__bool__` returns `False`,
  carrying a real placeholder (`{"file": None}`), with `files={"file": object()}`. This is the
  row that makes the boundary a boundary — it is the one input class the walker **accepts**.
  Its docstring says why, in the code's own voice: the emission is truthiness, so a falsy
  container leaves the envelope with no `variables` member while the `map` points into it.
- Add an **async-color row**: `AsyncTestClient(...).query(..., files=...)` with no variables
  raises the same guard. `_build_body` is shared but only the sync color exercises it here.
  Follow the file's existing async idiom; the raise happens before any request, so no
  transport and no DB are involved.

Target: **4 node ids.**

**Step 7 — item 9, the reserved-key rows**
(`tests/testing/test_client.py::test_files_key_shadowing_a_reserved_envelope_field_raises`,
lines 356-372). `for reserved in ("operations", "map")` inside one test is one node id.
Parametrize it (2 rows) and add a third supplying **both** reserved names at once, which also
pins the `_safe_arg_repr(sorted(reserved))` rendering in the message. Target: **3 node ids.**

**Step 8 — item 10, the non-descendable rows**
(`tests/testing/test_client.py::test_files_placeholder_cannot_descend_into_a_scalar_raises`,
lines 202-209). Parametrize over the non-descendable mid-path shapes — a `str`, an `int`, a
`None` — and add one row where the non-descendable value sits at a **nested** depth rather
than the first segment, so the rejection is pinned inside the loop and not only on its first
iteration. Target: **4 node ids.**

**Step 9 — item 11, the async transport-selection rows**
(`tests/testing/test_client.py::test_clients_preserve_an_explicit_falsy_transport`, lines
~480-496). The async half is currently one parametrized case, and the sync mutation kills both
params only because `TestClient.__init__` sits upstream of `AsyncTestClient.__init__`. Add:

- a row asserting `AsyncTestClient()` with no argument constructs a `django.test.AsyncClient`
  (not a sync `Client`) — the selection's default arm;
- a row driving one real `await client.query(...)` through an explicitly supplied falsy **async**
  transport, so the selection is pinned behaviourally and not only by identity.

Target: **3 node ids** on `AsyncTestClient.__init__`.

**Step 10 — item 15, the `_safe_arg_repr` key row** (`tests/testing/test_client.py`, beside
`test_files_placeholder_hostile_repr_keeps_assertion_error_boundary` at lines 260-272). One row
supplying a `files=` **key** that is a `str` subclass whose `__repr__` raises, asserting the
guard's `AssertionError` still surfaces. Verified reachable this pass: the message renders
`files= path <unprintable HostileKey> …` at three different rejection branches, so any of them
is a valid subject — prefer the missing-key branch, which needs no other malformed input.
Without `_safe_arg_repr(key)` the f-string raises the consumer's `RuntimeError` instead, so the
row can fail.

**Step 11 — ruff, then the proofs.** `uv run ruff format <the four files this pass touched>` and
`uv run ruff check --fix <the same files>`, **scoped to Cohort C's own files, never `.`** — a
repo-wide write-mode run rewrites the concurrent session's and Cohort D's files. Then
`git status --short` and confirm every modified path is in `### Files touched`; anything else is
a **stop-and-report**, never a revert.

### Failability proofs Worker 2 owes

Seven entries in the build report's `### Failability proofs` subsection, each carrying every
field `BUILD.md` `### What gets recorded` requires — boundary by symbol-qualified path, the
exact mutation, the failing node ids **listed** (never a bare count), the focused scope as run,
the collection/setup error count **separately** (a valid count requires 0), the pre-mutation
state of that same scope, and the revert proved by byte comparison.

Use `scripts/prove_failability.py` — it is the supported way and it emits the subsection with
every measured field filled in. Manifest home: `docs/builder/temp-tests/043/cohort-c/proofs*.json`,
a **new** subdirectory, so Cohort B's manifests and reports survive as the before-reading.
Copy each entry's anchor and mutation from the matching Cohort B manifest; only entry 1's
anchor changes.

| # | Boundary | Mutation to apply | Before (Cohort B) | Target after |
|---|---|---|---|---|
| 1 | `client.py::TestClient._build_body #"if \"variables\" not in body:"` | predicate → `if False:` | 0 rows (A1/B1, on the old spelling) | ≥ 4 |
| 2 | `client.py::TestClient._build_body #"if reserved:"` | `if reserved:` → `if False:` | 1 row (A2) | ≥ 3 |
| 3 | `client.py::TestClient._assert_file_placeholders #"is not a dict or list"` | the `raise AssertionError(...)` → `current = None` | 1 row (A6) | ≥ 4 |
| 4 | `client.py::AsyncTestClient.__init__ #"client if client is not None else AsyncClient()"` | → `client or AsyncClient()` | 1 row (A11) | ≥ 3 |
| 5 | `client.py::TestClient.request #"url if url is not None else self.path"` | → `self.client.post(self.path, **kwargs)` | 1 row (A12/B2) | ≥ 3 |
| 6 | `client.py::GraphQLTestMixin.query #"TestClient(self.GRAPHQL_URL, client=self.client)"` | → `TestClient(None, client=self.client)` | 1 row (C1) | ≥ 2 |
| 7 | `test_client_api.py::_alt_graphql_view #"response[\"X-Probe-Endpoint\"]"` | delete the stamp line | n/a (new discriminator) | ≥ 2 |

Entries 5, 6 and 7 must be measured at a scope that **includes the live file**:
`tests/testing/test_client.py examples/fakeshop/test_query/test_client_api.py`. That is the
whole point of M1 — Cohort B's Run B and Run C proved that widening the scope added **zero**
live rows, and the target is that both live rows now appear in the failing set. Entry 7 is the
inverse check: removing the marker must fail the two rows that assert it, which is what proves
the discriminator is real rather than decorative.

Notes that keep these proofs honest:

- **Run the anchor check first.** `grep -c '<anchor>' <file>` must print exactly 1 **before**
  the pre-mutation copy. Nothing else in the loop can tell that its own reference is already
  mutated; `prove_failability.py` enforces this and aborts having written nothing.
- **One boundary, one mutation, reverted before the next.** Never fold two boundaries into one
  mutation to save a loop — that is the failure `### Slice splitting` names.
- **Never `git checkout` as the restore.** The tree is legitimately dirty with Cohort D's and a
  concurrent session's work.
- **A proof carrying any collection or setup error is not a valid count.** Resolve and re-run.
- **A boundary still at 0 or 1 rows after the new rows land is `revision-needed`**, not a
  recorded exception, and the fix is more or better-targeted rows — never a weaker boundary.

### Test additions / updates

Pinned by path and assertion shape. All package-tier rows land in
`tests/testing/test_client.py`; all live rows in `examples/fakeshop/test_query/test_client_api.py`.
`AGENTS.md` live-first: nothing here is reachable as a real GraphQL query that is not already
live — the guard and walker rows raise **before any request is posted**, which is the property
they pin, so the package tier is their correct and only home (Decision 11's split, unchanged).

| Row | File | Pins |
|---|---|---|
| `test_files_without_variables_raises_the_placeholder_guard[None]` / `[empty]` | package | the guard, `match="requires variables="` — distinguishes the call-level message from the walker's path-level one |
| `…_raises[falsy_dict_subclass]` (name Worker 2's) | package | the one input class the walker **accepts**; the row that makes the boundary a boundary |
| the async-color guard row | package | `_build_body` is shared, so the guard holds on `AsyncTestClient` too |
| `test_files_key_shadowing_a_reserved_envelope_field_raises[operations]` / `[map]` / both-at-once | package | the reserved-envelope-key guard, plus the `sorted(reserved)` rendering |
| `test_files_placeholder_cannot_descend_into_a_scalar_raises[str]` / `[int]` / `[none]` / nested-depth | package | the non-descendable rejection, inside the loop and not only on its first iteration |
| `AsyncTestClient()` default-transport row + awaited falsy-transport row | package | presence-not-truthiness selection on the async color, behaviourally |
| the mixin rung rows, one per rung (3, 1, 4) | package | each rung independently, so one failing is distinguishable from the others |
| `test_per_call_url_outranks_the_constructor_and_never_persists` (re-pointed) | package | the **real** `TestClient.request` line, via `_RecordingDjangoClient` |
| the hostile-`__repr__` **key** row | package | `_safe_arg_repr` containment on the key argument position |
| `test_per_call_url_routes_to_the_probe_endpoint` (+ marker assertion) | live | rung 1 actually routed to `/alt/`, not fell back to `/graphql/` |
| `test_class_attr_endpoint_hits_the_real_view` (+ marker assertion) | live | rung 3, same |

**Temp tests for Worker 3.** Worth writing under `docs/builder/temp-tests/043/cohort-c/` if
Worker 3 wants to demonstrate non-distinguishing assertions independently: a throwaway row
matching `"placeholder"` against the walker alone shows why the old `match=` could not tell the
guard from the walker. Not required; the re-run of entry 1 shows the same thing mechanically.

**Row counts are targets, not contracts.** `BUILD.md` counts a **node id**, so a parametrized
case is one row and a loop inside one function is one row however many cases it runs. If a
target is not reached, say so in the build report and set `revision-needed` rather than
widening the scope until the number looks right — a wider scope inflates the count and silently
shrinks Worker 3's mandatory re-run subset.

### Implementation discretion items

Assessed and decided as Worker 2's:

- **Every new test's name and its `@pytest.mark.parametrize` id strings.** The file's naming
  convention is established; match it.
- **The falsy-`dict`-subclass fixture's spelling** — a module-level class, a local class inside
  the test, or a parametrize argument. All three are equally valid; the file already uses local
  classes for hostile doubles (`_HostileRepr`) and module-level ones for recorders.
- **The marker header's exact name and value** (`X-Probe-Endpoint: alt` is this plan's
  suggestion, not a contract), provided it is distinctive enough that a fallback to `/graphql/`
  cannot supply it by accident.
- **Whether the three mixin rung rows are three functions or one parametrized function**, so
  long as the result is **three node ids**.
- **The order of the two new async rows** and whether they share a fixture.

Not discretionary, and not delegated: the respelled predicate's exact spelling, the guard
message's bytes, the `match="requires variables="` phrase, the decision to keep the positive
hit in both live rows, and the deletion of `_RecordingTestClient`.

### Dispatched findings checklist

One box per dispatched item. Boxes stay `- [ ]` at planning. **Worker 2 ticks `- [x]` only a box
whose fix actually landed in its diff**, and states any deferral in the build report rather than
ticking. Boxes marked **(W1)** are Worker 1's own, deferred to final verification per
`### Spec amendment timing`; **Worker 2 never ticks a (W1) box and never opens the spec or the
rationale.** Worker 1 audits every tick at final verification.

- [x] **1 — Guard respell.** `client.py::TestClient._build_body`: `if not variables:` →
      `if "variables" not in body:`, message unchanged byte for byte, comment rewritten to state
      the invariant (maintainer Decision 1; escalation 1 `## Exact change under Option C`).
- [x] **2 — Guard rows, parametrized.** `test_files_without_variables_raises_the_placeholder_guard`
      split over `variables=None` and `variables={}` into two node ids, every `match=` changed to
      `"requires variables="` — the phrase that distinguishes the call-level message from the
      walker's path-level one.
- [x] **3 — Guard row, falsy `dict` subclass.** A `dict` subclass whose `__bool__` returns
      `False`, holding `{"file": None}`, with `files={"file": object()}` — the class the walker
      **accepts** and the old spelling caught only by luck.
- [x] **4 — Guard row, async color.** `AsyncTestClient(...).query(..., files=...)` with no
      variables raises the same guard; `_build_body` is shared but only the sync color exercises
      it today.
- [x] **5 — Endpoint docstring restated.** `conf.py::testing_endpoint_setting` docstring only;
      the body stays `getattr(settings, TESTING_ENDPOINT_KEY, "/graphql/")` and **no validation
      is added** (maintainer Decision 2; escalation 2 section 6A).
- [x] **6 (W1) — spec `### Error shapes`, the false-on-its-own-date clause.** Spec line ~851
      `#"the traceback carries the failing"` rewritten to what actually happens: pytest frame
      locals show the `HttpResponse`, the `django.request` log names the path, the exception
      message names only the `Content-Type`.
- [x] **7 (W1) — spec, the endpoint-claim family.** All three sentences matching the docstring's
      claim (lines ~204, ~861, ~1199) corrected together, with line ~840's parenthetical graded
      and disposed of. `START.md`: partial claim fix = dominant residual defect.
- [x] **8 — M1, the live probe becomes observably distinct.** `_alt_graphql_view` stamps a marker
      header on the delegated response; both endpoint-rung rows assert it **in addition to** the
      existing positive hit. Not weakened to an exception-shape probe.
- [x] **9 — M2, boundary `_build_body #"if reserved:"`.** Parametrize the reserved-name loop and
      add a both-names-at-once row. Target ≥ 3 node ids.
- [x] **10 — M2, boundary `_assert_file_placeholders #"is not a dict or list"`.** Parametrize
      over `str` / `int` / `None` and add a nested-depth row. Target ≥ 4 node ids.
- [x] **11 — M2, boundary `AsyncTestClient.__init__`.** A default-transport row and an awaited
      falsy-transport row. Target ≥ 3 node ids.
- [x] **12 — M2, boundary `TestClient.request #"url if url is not None else self.path"`.**
      Re-point `test_per_call_url_outranks_the_constructor_and_never_persists` at a recording
      `client=` transport so the real `request()` executes.
- [x] **13 — M2, boundary `GraphQLTestMixin.query #"TestClient(self.GRAPHQL_URL, …)"`.** Split
      `test_mixin_endpoint_rungs_class_attr_settings_and_per_call` into three node ids, one per
      rung.
- [x] **14 — M3, delete `_RecordingTestClient`.** After item 12 it has zero callers; re-grep and
      confirm zero before deleting. Two recording doubles for one seam is the duplication;
      deleting the one that overrides production logic is the fix.
- [x] **15 — L1, `_safe_arg_repr` on the key argument.** One row with a `str`-subclass `files=`
      key whose `__repr__` raises, asserting the guard's `AssertionError` still surfaces.
- [x] **16 (W1) — L3 disposition recorded.** `Response.response`'s `None` default is **kept**;
      the recorded reason is corrected from "dataclass field ordering" (false — the engine base
      declares three fields, none defaulted) to "shipped public re-export on an `0.0.x` line;
      both in-repo construction sites pass `response=` explicitly". Homed in the rationale under
      Decision 6 so a later reader does not re-derive it.
- [x] **17 (W1) — spec, drop the "custom-view plumbing" exemption class.** Decision 11 (~1438)
      and the Slice-2 checklist (~321); its only named exemplar, `test_multi_db.py`, was itself
      converted. Re-audit reference uses vs definitions after the edit.
- [x] **18 (W1) — rationale entries.** One per maintainer decision, keyed to the owning Decision
      by heading and anchor, each carrying every rejected alternative with the reason it lost.
- [x] **19 (W1) — Test plan and DoD extension.** The rows this cohort lands get named owners, so
      the coverage paragraph's "every branch has a named owner" claim stays true. Read off
      Worker 2's diff, never off this plan.

### Final-verification obligations (Worker 1's own, recorded now so the pass cannot forget)

1. **Audit every `- [x]`** against the diff; un-tick and set `revision-needed` for an over-tick,
   tick a landed box Worker 2 left open, record a one-line deferral for anything still `- [ ]`.
2. **Confirm every failability record exists** with all seven fields, the byte-compared revert
   included, and that **no boundary remains at 0 or 1 rows**.
3. **Read the diff for fail-open shapes** rather than trusting a green suite.
4. **Check Cohort D's artifact `### Notes for Worker 1 (spec reconciliation)`** at
   `docs/builder/bld-043-review-4-live_conversion.md` and fold whatever it routes into the spec
   — this cohort owns the spec, Cohort D writes none of it, and that is what keeps the two
   partitions disjoint.
5. **Perform every deferred spec and rationale edit** against the enumerated site list above,
   enumerating each site's presence before writing any of it.
6. **Re-run the gates after the spec edits**:
   `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-043-test_client-0_0_14.md`;
   `uv run python scripts/check_citations.py --check`; `uv run python scripts/check_trailing_commas.py --check <explicit paths>`.
   A pre-edit green reading is no reading at all — the pre-flight's stale
   `check_spec_glossary` is the cycle's own recorded instrument failure.
7. **Audit refs-vs-defs and in-page anchors** after any link-bearing spec edit. Cohort A's
   recovery found 15 undefined references a prior pass introduced and nobody re-audited; the
   exemption-class drop at item 17 removes a `[test-multi-db]` use and is the same shape.
8. **Confirm the spec `Status:` line still reads COMPLETE** and still matches the tree.
9. **Run the focused scope** `uv run pytest --no-cov -n0 tests/testing/test_client.py examples/fakeshop/test_query/test_client_api.py`
   and record only whether it runs. **No `--cov*` flag in any pass.**

### Constraints restated for Worker 2

- **Worker 1 writes no `.py`; Worker 2 writes no spec and no rationale.** Isolation is
  non-waivable, and the spec is Cohort C's Worker 1's alone within this cohort.
- **Write set, exclusively:** `django_strawberry_framework/testing/client.py`,
  `django_strawberry_framework/conf.py`, `tests/testing/test_client.py`,
  `examples/fakeshop/test_query/test_client_api.py`, this artifact,
  `docs/builder/worker-memory/043-worker-2.md`, `docs/builder/temp-tests/043/cohort-c/`.
- **Do not touch:** Cohort D's four files (`test_error_policy_api.py`,
  `test_products_visibility_api.py`, `test_relations_async_api.py`,
  `test_resource_policy_api.py`); `examples/fakeshop/test_query/test_list_field_async_api.py`
  (spec-050 territory); `build-050-*`, `bld-slice-*`, `bld-integration.md`, `bld-final.md`
  (the live spec-050 cycle); `docs/GLOSSARY.md`, `docs/TREE.md`, `KANBAN.md`, `KANBAN.html`,
  `examples/fakeshop/db.sqlite3`; `START.md`, `docs/feedback.md`.
- **Never commit. Never `git stash` / `checkout --` / `restore` / `worktree`** — a concurrent
  session writes to this tree. Read HEAD via `git show HEAD:<path>` into the session scratchpad.
- **Coverage flags are forbidden in every pass.** `--no-cov` is the only coverage-shaped flag,
  and it is required because `pytest.ini`'s `addopts` auto-applies `--cov`.
- **`scripts/review_inspect.py`, if used, takes `--output-dir <session scratchpad>/inspect`**,
  never `docs/shadow`.
- **Cite by symbol path** (`path::QualifiedName`, `path #"unique substring"`) in source comments,
  docstrings, and the spec. Raw `path:NN` is fine inside this per-cycle artifact only.
- **`AGENTS.md` rule 4:** never name `docs/feedback.md` / `docs/feedback2.md` in spec, rationale,
  code, or commits.
- **No process provenance in code or standing prose.** No severity labels, no
  round/cohort/worker attribution, no "previously" — a new test docstring states the invariant,
  never how the row came to be written. Spec decision pointers (`spec-043 Decision 9`) are the
  kept form.

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short` after both ruff invocations; every path below
is in this cohort's declared write set and none is co-owned.

- `django_strawberry_framework/testing/client.py` — `TestClient._build_body`'s
  empty-`variables` guard respelled `if not variables:` → `if "variables" not in body:`,
  with the comment above it rewritten to state the invariant (the `map` points
  into `variables.<path>`, so the envelope must carry that member). The
  `AssertionError` message is byte-identical to HEAD's, and the
  `if variables: body["variables"] = variables` emission above is untouched —
  it is now the single owner of when the member exists. No other line changed.
- `django_strawberry_framework/conf.py` — `testing_endpoint_setting`'s docstring
  only; the body stays `return getattr(settings, TESTING_ENDPOINT_KEY, "/graphql/")`
  and **no validation was added**. The last sentence now states the mechanism:
  the value is handed to `django.test.Client.post` unchanged, which `str()`-coerces
  it (so `reverse_lazy()` works and `None` posts to `/None`), and a wrong value
  surfaces as whatever the URLconf serves at that path — **ordinarily** a 404 —
  through Django's non-JSON `ValueError` naming the response's `Content-Type`.
  The "ordinarily" is what makes the sentence true for `TESTING_ENDPOINT = ""`.
- `tests/testing/test_client.py` — `_RecordingTestClient` deleted; the per-call
  rung row re-pointed at the real `TestClient.request` over `_RecordingDjangoClient`;
  five boundaries re-pinned with parametrized rows; one hostile-`__repr__` **key**
  row added; the mixin rung row split into three node ids; the async transport
  selection pinned behaviourally. The module's transport-doubles comment block
  was rewritten because it described the deleted `request()` override.
- `examples/fakeshop/test_query/test_client_api.py` — `_alt_graphql_view` stamps
  `X-Probe-Endpoint: alt` on the delegated response (header name and value as
  two module constants, so the literal is named once and read three times), and
  both endpoint-rung rows assert it **in addition to** the existing positive hit
  on the real schema view. Neither row was weakened to an exception-shape probe.

Unexpected churn: none in this cohort's files. The tree carries a concurrent
session's work and Cohort D's four live files as `M`, plus an untracked
`examples/fakeshop/test_query/test_zz_probe_api.py` that is not this cohort's —
recorded, not touched, not reverted (`AGENTS.md` rule 34).

### Tests added or updated

`tests/testing/test_client.py`:

- `test_files_without_variables_raises_the_placeholder_guard[none]` / `[empty]` /
  `[falsy_dict_subclass]` — the guard, matched on `"requires variables="`, the
  call-level message's own phrase (every walker message also contains
  `"placeholder"`, which is what the old `match=` could not distinguish).
  `_FalsyDict` is a `dict` subclass whose `__bool__` is `False` holding
  `{"file": None}`: the one input class the per-path walker **accepts** while
  the envelope stays spec-invalid.
- `test_async_files_without_variables_raises_the_same_guard` — the async color of
  the same guard; `_build_body` is shared and the raise precedes any transport.
- `test_files_key_shadowing_a_reserved_envelope_field_raises[operations]` /
  `[map]` / `[both]` — was a `for` loop in one node id. The `[both]` row also
  asserts the message renders `sorted(reserved)`.
- `test_files_placeholder_cannot_descend_into_a_scalar_raises[str]` / `[int]` /
  `[none]` / `[nested]` — was one node id on `None` alone; `[nested]` puts the
  non-descendable value past the first segment so the rejection is pinned inside
  the walk.
- `test_async_client_defaults_to_djangos_async_transport` — the default arm of
  `AsyncTestClient.__init__` (an `AsyncClient`, not a sync `Client`).
- `test_async_client_posts_a_real_query_through_a_falsy_transport[bool_falsy]` /
  `[len_falsy]` — an awaited `query()` through an explicitly supplied falsy async
  transport, so the selection is pinned behaviourally; the two ids are the two
  spellings of falsiness a presence check ignores alike.
- `test_mixin_class_attr_rung_beats_the_settings_key_and_the_default`,
  `test_mixin_per_call_url_rung_beats_the_class_attr`,
  `test_mixin_settings_rung_applies_when_the_class_attr_is_unset` — the three
  rungs formerly proved in one function body, now one node id each. Rung 3's row
  is also strengthened: it now runs under a `TESTING_ENDPOINT` override, so it
  proves the class attribute beats the settings key as well as the default.
- `test_per_call_url_outranks_the_constructor_and_never_persists` — re-pointed at
  `TestClient("/constructor/", client=_RecordingDjangoClient())`, reading the
  effective URL off `transport.posts`. Every prior assertion's intent is kept
  (`/percall/` for the overridden call, `client.path` unchanged afterwards,
  `isinstance(res, Response)`, `res.data`, `isinstance(res.response, _CannedJSONResponse)`,
  and the fall-back on the second un-overridden call).
- `test_files_placeholder_hostile_repr_key_keeps_assertion_error_boundary` — a
  `str`-subclass `files=` **key** whose `__repr__` raises, on the missing-key
  branch; asserts the guard's `AssertionError` surfaces and that the consumer's
  `RuntimeError` text does not ride the message.

`examples/fakeshop/test_query/test_client_api.py`:

- `GraphQLTestCaseEndToEndTests::test_per_call_url_routes_to_the_probe_endpoint`
  and `GraphQLTestCaseClassAttrEndpointTests::test_class_attr_endpoint_hits_the_real_view`
  — each keeps `assertResponseNoErrors` + the data assertion and adds the marker
  assertion. Proof entry 7 measures that the marker is a real discriminator.

### Validation run

- `uv run ruff format <the four files>` — pass (4 files left unchanged on the
  final run).
- `uv run ruff check --fix <the same four files>` — pass ("All checks passed!").
- `uv run python scripts/check_trailing_commas.py --check <the same four files>` —
  pass. An intermediate `--fix` (explicit path, `tests/testing/test_client.py`
  only, never the repo-wide default) collapsed five over-exploded parametrize
  lists below the 4-element threshold.
- `git status --short` after both ruff invocations — the four files of this
  cohort's write set are `M`; everything else modified or untracked is the
  concurrent session's, Cohort A's, or Cohort D's, and none of it is co-owned.
- `uv run pytest --no-cov -n0 -q -p no:cacheprovider tests/testing/test_client.py examples/fakeshop/test_query/test_client_api.py`
  → **66 passed** (52 at plan time; +14 node ids). No `--cov*` flag in any run.
- `uv run python scripts/check_citations.py --check` → `OK: 995 citations resolve
  (825 in 442 .py files, 170 in KANBAN.md).` Run because item 14 deletes a class:
  the gate's corpus is `.py` files plus `KANBAN.md`, so the only surviving
  `_RecordingTestClient` mentions are prose inside this cycle's own `bld-043-*`
  artifacts, which are per-cycle scratch and outside the gate.

### Failability proofs

Mechanized by `scripts/prove_failability.py`; manifest at
`docs/builder/temp-tests/043/cohort-c/proofs.json`, full emitted record at
`docs/builder/temp-tests/043/cohort-c/proofs-report.md`, stdout at
`…/proofs-stdout.txt`. Scratch root is the **session scratchpad**
(`…/scratchpad/cohort-c-failability`), outside the repository. Anchors were
validated first with `--check-anchors-only`: all seven matched exactly once. The
whole manifest was then run twice — once after the code landed, and again after
a later comment-only edit to `tests/testing/test_client.py`, so the record below
describes the tree as handed over rather than an earlier one. **Exit code 0 on
the recorded run: every entry proved, none weakly pinned, zero collection or
setup errors.** No mutation is live; the scratch directory holds only `pristine/`
and no `ACTIVE-MUTATION.json`.

Row counts against the plan's `### Failability proofs Worker 2 owes` targets:
**4 / 3 / 4 / 3 / 3 / 2 / 2** against **≥4 / ≥3 / ≥4 / ≥3 / ≥3 / ≥2 / ≥2**. Every
target met; no entry is at 0 or 1 rows, so nothing here is weakly pinned and no
**why 0** judgement is owed. Entries 2, 4, 5, 6 and 7 sit at or below three rows
and are therefore inside Worker 3's mandatory independent re-run floor.

- `django_strawberry_framework/testing/client.py::TestClient._build_body #"if \"variables\" not in body:"`
  — mutation applied: the respelled guard's predicate replaced by `if False:`, so
  a `files=` call whose built envelope carries no `variables` member emits
  `operations` + `map` instead of raising; scope as run:
  `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/testing/test_client.py`;
  pre-mutation state of that scope: 55 passed, pytest exit 0, 0 pre-existing
  failing rows differenced out; failing node ids:
  `tests/testing/test_client.py::test_files_without_variables_raises_the_placeholder_guard[none]`,
  `tests/testing/test_client.py::test_files_without_variables_raises_the_placeholder_guard[empty]`,
  `tests/testing/test_client.py::test_files_without_variables_raises_the_placeholder_guard[falsy_dict_subclass]`,
  `tests/testing/test_client.py::test_async_files_without_variables_raises_the_same_guard`;
  collection/setup errors: 0; revert proved by byte comparison:
  `filecmp.cmp(shallow=False) True; sha256 a2da3f6342b93707… == a2da3f6342b93707…`.
  Cohort B measured **0** rows for this boundary on the old spelling; the four
  rows are the respell's pinning, and `[falsy_dict_subclass]` is the row that
  makes it a boundary rather than a redundant pre-check.
- `django_strawberry_framework/testing/client.py::TestClient._build_body #"if reserved:"`
  — mutation applied: predicate replaced by `if False:`, so a `files=` key named
  `operations` / `map` silently clobbers the envelope; scope as run:
  `… -n0 tests/testing/test_client.py`; pre-mutation state: 55 passed, exit 0, 0
  differenced out; failing node ids:
  `tests/testing/test_client.py::test_files_key_shadowing_a_reserved_envelope_field_raises[operations]`,
  `…[map]`, `…[both]`; collection/setup errors: 0; revert proved:
  `filecmp.cmp(shallow=False) True; sha256 a2da3f6342b93707… == a2da3f6342b93707…`.
  Before: 1 row (the `for` loop).
- `django_strawberry_framework/testing/client.py::TestClient._assert_file_placeholders #"is not a dict or list"`
  — mutation applied: the non-descendable-value `raise AssertionError(...)` block
  replaced by `current = None`, so a scalar mid-path resolves silently; scope as
  run: `… -n0 tests/testing/test_client.py`; pre-mutation state: 55 passed, exit
  0, 0 differenced out; failing node ids:
  `tests/testing/test_client.py::test_files_placeholder_cannot_descend_into_a_scalar_raises[str]`,
  `…[int]`, `…[none]`, `…[nested]`; collection/setup errors: 0; revert proved:
  `filecmp.cmp(shallow=False) True; sha256 a2da3f6342b93707… == a2da3f6342b93707…`.
  Before: 1 row.
- `django_strawberry_framework/testing/client.py::AsyncTestClient.__init__ #"client if client is not None else AsyncClient()"`
  — mutation applied: presence-based selection reverted to `client or AsyncClient()`,
  so an explicitly supplied falsy async transport is discarded; scope as run:
  `… -n0 tests/testing/test_client.py`; pre-mutation state: 55 passed, exit 0, 0
  differenced out; failing node ids:
  `tests/testing/test_client.py::test_clients_preserve_an_explicit_falsy_transport[AsyncTestClient]`,
  `tests/testing/test_client.py::test_async_client_posts_a_real_query_through_a_falsy_transport[bool_falsy]`,
  `tests/testing/test_client.py::test_async_client_posts_a_real_query_through_a_falsy_transport[len_falsy]`;
  collection/setup errors: 0; revert proved:
  `filecmp.cmp(shallow=False) True; sha256 a2da3f6342b93707… == a2da3f6342b93707…`.
  Before: 1 row, and that one only because `TestClient.__init__` sits upstream.
- `django_strawberry_framework/testing/client.py::TestClient.request #"url if url is not None else self.path"`
  — mutation applied: `return self.client.post(url if url is not None else self.path, **kwargs)`
  → `return self.client.post(self.path, **kwargs)`, dropping rung 1 at the
  transport seam; scope as run:
  `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/testing/test_client.py examples/fakeshop/test_query/test_client_api.py`;
  pre-mutation state of that scope: 66 passed, exit 0, 0 differenced out; failing
  node ids:
  `examples/fakeshop/test_query/test_client_api.py::GraphQLTestCaseEndToEndTests::test_per_call_url_routes_to_the_probe_endpoint`,
  `tests/testing/test_client.py::test_per_call_url_outranks_the_constructor_and_never_persists`,
  `tests/testing/test_client.py::test_mixin_per_call_url_rung_beats_the_class_attr`;
  collection/setup errors: 0; revert proved:
  `filecmp.cmp(shallow=False) True; sha256 a2da3f6342b93707… == a2da3f6342b93707…`.
  Cohort B measured 1 row here and its wide-scope re-run added **zero** live rows;
  the live row now appears, which is M1's whole purpose, and the package row is
  now the real `request()` rather than a double re-spelling it.
- `django_strawberry_framework/testing/client.py::GraphQLTestMixin.query #"TestClient(self.GRAPHQL_URL, client=self.client)"`
  — mutation applied: `TestClient(self.GRAPHQL_URL, client=self.client)` →
  `TestClient(None, client=self.client)`, dropping rung 3; scope as run: the same
  package + live scope as above; pre-mutation state: 66 passed, exit 0, 0
  differenced out; failing node ids:
  `examples/fakeshop/test_query/test_client_api.py::GraphQLTestCaseClassAttrEndpointTests::test_class_attr_endpoint_hits_the_real_view`,
  `tests/testing/test_client.py::test_mixin_class_attr_rung_beats_the_settings_key_and_the_default`;
  collection/setup errors: 0; revert proved:
  `filecmp.cmp(shallow=False) True; sha256 a2da3f6342b93707… == a2da3f6342b93707…`.
  Before: 1 row (Cohort B's Run C, live file included, live row absent).
- `examples/fakeshop/test_query/test_client_api.py::_alt_graphql_view #"response[_PROBE_MARKER_HEADER] = _PROBE_MARKER_VALUE"`
  — mutation applied: the marker stamp line deleted, so a response served by
  `/alt/` is indistinguishable from one served by `/graphql/` under the same
  probe URLconf; scope as run: the same package + live scope; pre-mutation state:
  66 passed, exit 0, 0 differenced out; failing node ids:
  `examples/fakeshop/test_query/test_client_api.py::GraphQLTestCaseEndToEndTests::test_per_call_url_routes_to_the_probe_endpoint`,
  `examples/fakeshop/test_query/test_client_api.py::GraphQLTestCaseClassAttrEndpointTests::test_class_attr_endpoint_hits_the_real_view`;
  collection/setup errors: 0; revert proved:
  `filecmp.cmp(shallow=False) True; sha256 db79448324113342… == db79448324113342…`.
  This is the inverse check the plan asked for: the discriminator is real, not
  decorative — without it both rows pass on a fall-back to `/graphql/`.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **The marker header is two module constants**, `_PROBE_MARKER_HEADER` /
  `_PROBE_MARKER_VALUE`, rather than three repetitions of a literal across the
  view and the two rows. The plan left the name and value to Worker 2's
  discretion; `X-Probe-Endpoint: alt` is distinctive enough that a fall-back to
  `/graphql/` cannot supply it by accident, and `config.urls`' GraphQL view sets
  no `X-` header of its own.
- **Header assignment on the delegated response was verified by execution, not
  assumed** — both live rows pass with the assertion, and proof entry 7 fails
  exactly those two rows when the stamp is removed, so the view's return value
  does accept `__setitem__`.
- **`_FalsyDict` is module-level, beside the guard's rows** rather than a local
  class: it is a parametrize argument, so it has to be constructed at collection
  time. The file's local-class idiom (`_HostileRepr`, `_HostileLen`) still holds
  for doubles built inside a single row.
- **The async recording transport is a three-class family**
  (`_RecordingAsyncTransport` + `_BoolFalsyAsyncTransport` + `_LenFalsyAsyncTransport`)
  so the recording body exists once and each subclass declares only how it is
  falsy. The second falsiness spelling is not decoration: a truthiness fallback
  discards a transport that is falsy by `__len__` exactly as it does one falsy by
  `__bool__`, and the two rows are what carry entry 4 above the weakly-pinned floor.
- **`_AltProbe` moved to module level** beside `_MixinProbe`, because splitting
  the mixin rung row into three node ids would otherwise have meant declaring the
  same probe class twice. Its body is unchanged.
- **Rung 3's row gained a settings override.** The old single-body test proved
  `GRAPHQL_URL` beat only the default; asserting it beats the settings key too is
  what makes the three rungs independently meaningful.
- **The reserved-key rows parametrize over tuples, not strings**, so the
  both-at-once case is the same shape as the single-name cases and the message's
  `sorted(reserved)` rendering is asserted uniformly.
- **The hostile-key row uses the missing-key branch**, which needs no other
  malformed input, and asserts the consumer's `RuntimeError` text is absent from
  the message rather than only that an `AssertionError` was raised.

### Notes for Worker 3

- **Every proof in the table above was re-run after the last edit to the tree.**
  The first run predated a comment-only rewrite of the transport-doubles block in
  `tests/testing/test_client.py`; rather than argue AST identity, the whole
  manifest was re-run. Node-id sets and counts were identical across both runs.
- **The manifest is reusable as written** for an independent re-run:
  `uv run python scripts/prove_failability.py docs/builder/temp-tests/043/cohort-c/proofs.json --only <N>`.
  Its `scratch_root` points at this session's scratchpad; a re-run from another
  session should pass `--scratch-root` into its own, still outside the repo.
- **Entries 6 and 7 sit at exactly 2 rows.** Both are above the weakly-pinned
  floor, and in both cases the two rows are the only two places the contract is
  observable (one package-tier rung row, one live row). More rows would mean
  duplicating one of them rather than pinning anything further.
- **`_RecordingTestClient` is gone and nothing references it** outside this
  cycle's own `bld-043-*` prose, which is per-cycle scratch describing the
  finding. `check_citations.py --check` is green and its corpus does not include
  `docs/builder/`.
- The plan's step 9 named `AsyncTestClient()`'s default arm as one of the three
  async rows. It is present
  (`test_async_client_defaults_to_djangos_async_transport`) but it does **not**
  fail under entry 4's mutation — `None or AsyncClient()` still yields an
  `AsyncClient` — so the three failing rows are the falsy-transport ones. The
  default-arm row is kept because it pins the arm itself, not because it carries
  the count; saying so here so the difference between the plan's row list and the
  proof's node-id list is not read as a miscount.
- No source file outside this cohort's write set was touched, and nothing was
  reverted.

### Notes for Worker 1 (spec reconciliation)

Everything below is for the deferred custody pass; Worker 2 opened neither the
spec nor the rationale.

1. **The guard family's replacement text is now exact, read off the diff.** The
   predicate that landed is `if "variables" not in body:` inside
   `django_strawberry_framework/testing/client.py::TestClient._build_body`, and
   the `AssertionError` message is **unchanged byte for byte** from HEAD. The
   label "empty-`variables` guard" stays accurate: the guard rejects exactly the
   same call shapes it rejected before, so the four citing spec sites
   (Decision 11, the Test plan, the coverage paragraph, the DoD) need no edit —
   confirm rather than rewrite, as the plan already decided.
2. **The walker docstring's tail still reads true.**
   `client.py::TestClient._assert_file_placeholders` ends with "matching the
   empty-``variables`` guard above"; the respell does not falsify it, and it was
   left untouched.
3. **The endpoint docstring's landed wording**, for quoting into the spec's three
   endpoint-claim sentences: "No validation beyond the shared malformed-dict
   guard: the value is handed to `django.test.Client.post` unchanged, which
   coerces it with `str()` (so a `reverse_lazy()` endpoint works and a `None`
   posts to `/None`), and a wrong value surfaces at request time as whatever the
   URLconf serves at that path - ordinarily a 404 - through Django's non-JSON
   `ValueError` naming the response's `Content-Type`." The reviewer's narrowing
   to "a wrong endpoint *string*" was **not** applied, per maintainer Decision 2.
4. **Item 19's row inventory, read off this diff.** The rows this cohort landed,
   for the Test plan's scenario-15 package-tier inventory and scenarios 6-8's
   endpoint-ladder inventory, are the full list in `### Tests added or updated`
   above. Two deletions to reconcile alongside them: the single-node-id
   `test_mixin_endpoint_rungs_class_attr_settings_and_per_call` no longer exists
   (three named rung rows replace it), and
   `test_files_placeholder_cannot_descend_into_a_scalar_raises` is now four
   parametrized ids rather than one. Any spec sentence naming either by its old
   single-row shape is stale.
5. **A spec sentence worth grading that the plan's site list does not carry.**
   `examples/fakeshop/test_query/test_client_api.py`'s module docstring lists
   what is covered live and describes the probe URLconf; the marker header is new
   behaviour there. The docstring was updated in this diff (the probe-URLconf
   comment block states why the marker exists). If the spec quotes that comment
   block anywhere, the quotation is stale — recommended check:
   grep the spec for `#"POSITIVE hit on the real schema view"`.
6. **Escalation 2 section 6A proposed two optional test rows** — a live
   parametrize of `test_wrong_configured_endpoint_surfaces_django_non_json_decode_error`
   over `None`, and a package row in `tests/base/test_conf.py` asserting the
   accessor returns a non-`str` verbatim. **Neither landed**: the dispatched
   checklist scopes item 5 to the docstring, and `tests/base/test_conf.py` is
   outside this cohort's write set. Recommended disposition: record them in the
   rationale under Decision 7 as considered-and-not-taken (the claim they would
   pin is a docstring statement about Django's own coercion, already swept across
   every cached wheel 5.2.0 → 6.1.0 by escalation 2), or home them on a named
   card. Flagged rather than silently dropped.

### Status

`built`.

---

## Review (Worker 3)

### Mutations pre-registered before they were made

`worker-3.md` `### Reading is necessary, not sufficient`: the mutation is recorded here
**before** it is applied. Nine transient production mutations were made in this pass, each
reverted inside it and each revert proved by byte comparison. No mutation crossed a `Status:`
transition; the tree carries none now.

Tree state before any of them, verified with three instruments:

- `find <scratchpad> -name 'ACTIVE-MUTATION*'` → **0** — no prior pass died mid-proof.
- `uv run python scripts/prove_failability.py docs/builder/temp-tests/043/cohort-c/proofs.json --check-anchors-only`
  → all seven anchors match **exactly once**, so no anchor was already mutated.
- The two recorded scopes re-run unmutated:
  `uv run pytest --no-cov --color=no -p no:cacheprovider -q -n0 tests/testing/test_client.py`
  → **55 passed**; the same plus `examples/fakeshop/test_query/test_client_api.py` → **66 passed**.
  Both match Worker 2's recorded pre-mutation states exactly, so its measurements were taken
  against this tree.

**Re-run set (1)** — all seven of Worker 2's entries, re-run from its own manifest at the scopes
it recorded, under my own `--scratch-root` so its `pristine/` directory is untouched. The
mandatory floor (`worker-3.md`: every boundary at **3 rows or fewer**) is entries **2, 4, 5, 6, 7**;
entries **1** and **3** (4 rows each) are above the floor and were re-run anyway — entry 1 because
the respell is this cohort's only production verdict change, entry 3 because it costs one run.
No boundary here sits on a security or data-isolation decision.

**Re-run set (2)** — two mutations of my own, not in Worker 2's manifest, both on
`django_strawberry_framework/testing/client.py`:

- `AsyncTestClient.__init__ #"AsyncClient()"` → `Client()` — asked because Worker 2's
  `### Notes for Worker 3` reports the async default-arm row does not fail under entry 4's
  mutation. This is the mutation that removes the arm that row names.
- `TestClient.__init__ #"client if client is not None else Client()"` → `client or Client()` —
  the sync twin of entry 4, to establish whether entry 4's three rows are the async selection's
  own pinning or ride on the sync constructor upstream of it.

### Failability audit, and the independent re-run

**Every one of Worker 2's seven records carries all seven fields** `BUILD.md`
`### What gets recorded` requires — boundary by symbol-qualified path, the exact mutation, the
failing node ids listed rather than counted, the focused scope as run, the collection/setup
error count separately, the pre-mutation state of that same scope, and the revert proved by
byte comparison. No entry is at 0 or 1 rows, so no **why 0** judgement is owed and none is
missing.

Re-run: `uv run python scripts/prove_failability.py docs/builder/temp-tests/043/cohort-c/proofs.json
--scratch-root <scratchpad>/w3-rerun --output <scratchpad>/w3-rerun/w3-rerun-report.md` →
**exit 0**. All seven entries, at the scopes Worker 2 recorded, compared as node-id **sets**:

| # | Boundary | Rows (W2 / W3) | Node-id sets | Errors | Restore |
|---|---|---|---|---|---|
| 1 | `client.py::TestClient._build_body #"if \"variables\" not in body:"` | 4 / 4 | identical | 0 | sha256 `a2da3f63…` == `a2da3f63…` |
| 2 | `client.py::TestClient._build_body #"if reserved:"` | 3 / 3 | identical | 0 | same |
| 3 | `client.py::TestClient._assert_file_placeholders #"is not a dict or list"` | 4 / 4 | identical | 0 | same |
| 4 | `client.py::AsyncTestClient.__init__ #"client if client is not None else AsyncClient()"` | 3 / 3 | identical | 0 | same |
| 5 | `client.py::TestClient.request #"url if url is not None else self.path"` | 3 / 3 | identical | 0 | same |
| 6 | `client.py::GraphQLTestMixin.query #"TestClient(self.GRAPHQL_URL, client=self.client)"` | 2 / 2 | identical | 0 | same |
| 7 | `test_client_api.py::_alt_graphql_view #"response[_PROBE_MARKER_HEADER] = _PROBE_MARKER_VALUE"` | 2 / 2 | identical | 0 | sha256 `db794483…` == `db794483…` |

Sets, not totals: entry 5's three rows are
`test_client_api.py::GraphQLTestCaseEndToEndTests::test_per_call_url_routes_to_the_probe_endpoint`,
`test_client.py::test_per_call_url_outranks_the_constructor_and_never_persists`,
`test_client.py::test_mixin_per_call_url_rung_beats_the_class_attr`; entry 6's two are
`test_client_api.py::GraphQLTestCaseClassAttrEndpointTests::test_class_attr_endpoint_hits_the_real_view`
and `test_client.py::test_mixin_class_attr_rung_beats_the_settings_key_and_the_default`; entry
7's two are the same pair of live rows. Every entry's pre-mutation state re-measured clean
here too (**55 passed** package-tier, **66 passed** package + live), matching Worker 2's
readings, so no pre-existing failing row is inflating any count.

**Nothing was accepted on Worker 2's record alone.** The mandatory floor was entries 2, 4, 5, 6
and 7 (≤ 3 rows); entries 1 and 3 were re-run above the floor as well.

#### The self-reported async default-arm discrepancy — verified, and completed

Worker 2's `### Notes for Worker 3` reports that
`test_async_client_defaults_to_djangos_async_transport` landed but does not fail under entry 4's
mutation, because `None or AsyncClient()` still yields an `AsyncClient`. **The reading is
correct, and it is not the whole answer.** Entry 4's mutation cannot reach the default arm by
construction — it rewrites only the *selection* between a supplied transport and the default,
and both spellings agree when nothing is supplied. That says nothing about whether the arm is
pinned; it says the mutation is orthogonal to it.

Measured, with the mutation that does remove the arm (pre-registered above, manifest at
`docs/builder/temp-tests/043/cohort-c-w3/proofs-w3.json`):

- `AsyncTestClient.__init__ #"AsyncClient()"` → `Client()`, scope
  `… -n0 tests/testing/test_client.py`, pre-mutation 55 passed / exit 0, collection errors 0 →
  **1 row**: `tests/testing/test_client.py::test_async_client_defaults_to_djangos_async_transport`.
  Revert proved: `filecmp.cmp(shallow=False) True; sha256 a2da3f63… == a2da3f63…`.

So the arm is **pinned, by exactly the row that names it** — not harness-impossible, and not
unpinnable. Recorded as Low 2 below rather than as a proof gap: that line is unchanged at HEAD,
this pass introduces no production boundary (`BUILD.md` `### What needs a proof, and what does
not`), and the plan's entry 4 named the presence check, which is at 3 rows.

The second pre-registered mutation answers the adjacent question — whether entry 4's three rows
are the async selection's own pinning or ride on the sync constructor upstream:

- `TestClient.__init__ #"client if client is not None else Client()"` → `client or Client()`,
  same scope, pre-mutation 55 passed / exit 0, collection errors 0 → **4 rows**:
  `test_clients_preserve_an_explicit_falsy_transport[TestClient]`, `…[AsyncTestClient]`,
  `test_async_client_posts_a_real_query_through_a_falsy_transport[bool_falsy]`, `…[len_falsy]`.
  Revert proved: `filecmp.cmp(shallow=False) True; sha256 a2da3f63… == a2da3f63…`.

Both selections are independently pinned: the async rows fail under the async mutation *and*
under the sync one, because each constructor performs its own presence check and either can
discard the supplied transport. The overlap strengthens the pinning rather than borrowing it.

**Tree after every mutation in this pass:** `django_strawberry_framework/testing/client.py`
sha256 `a2da3f6342b937073b842fa495f589326f705031307f3f3d9079edb22eb208a9`,
`examples/fakeshop/test_query/test_client_api.py` sha256
`db794483241133423e1a47cc9b52fc7200fa9a68436549b8f3d17e2a83be0f59` — the values Worker 2
recorded. No `ACTIVE-MUTATION.json` under either scratch root; the package-tier scope re-runs
**55 passed**.

### The guard respell, re-derived rather than accepted

Escalation 1's derivation was re-executed independently, in the session scratchpad
(`probe_w3_guard.py`), over 17 input classes and four builder spellings: as shipped, HEAD's
`if not variables:` re-implemented with every other line identical, the walker called alone, and
the builder with the guard deleted.

- **Verdict-identical: 0 mismatches in 17.** Every falsy `variables` (`None`, `{}`, `[]`, `0`,
  `""`, a falsy non-container, and three falsy containers carrying real placeholders) raises the
  call-level guard under both spellings; every valid shape emits identically; `files={}`,
  `files=None`, the reserved-key collision and a truthy-but-placeholder-less `variables` all
  resolve the same way under both.
- **The respell is provably equivalent, not merely equal on a sample.** `body` is a local dict
  the method just built; its only writers are `{"query": query}`, `body["operationName"]`, and
  `body["variables"] = variables` under `if variables:`. So `"variables" in body` ⟺
  `bool(variables)`, exactly. Probed the one input that could have broken that —
  `operation_name="variables"` with `variables=None`, which still raises, because the key
  written is `operationName`.
- **The motivating case closes.** `class FalsyDict(dict): __bool__ → False` holding
  `{"file": None}`, with `files={"file": f}`: the walker called **alone accepts** it, and the
  builder with the guard deleted **emits** `operations` carrying no `variables` member beside
  `map = {"file": ["variables.file"]}`. Two more falsy-container shapes behave the same. The
  walker does not catch this class, so the guard decides a verdict.
- **No new gap.** "Truthy `variables`, emission did not run" is unreachable: the emission is
  unconditional given truthiness and is the member's only writer. Nothing reaches
  `_assert_file_placeholders` that did not before — the guard passes under exactly the same
  input set as the old spelling, so the walker's domain is unchanged.
- **Not a relocated fail-open shape.** `"variables" not in body` is a membership test on a dict
  this method built one line earlier, not a truthiness test on consumer input; it is `BUILD.md`
  `### Fail-open shapes`' own prescription (guard the answer), applied to the suspect that
  section names first. The `AssertionError` message is byte-identical to HEAD's, confirmed by
  comparing the two files' `Raise`-constant sets.

### `conf.py` is docstring-only, and the new docstring is true

- **Inverse proof, per `START.md`'s "comment/docstring-only edit owes an INVERSE proof".**
  `git show HEAD:django_strawberry_framework/conf.py` into the scratchpad, both files parsed and
  every module / class / function docstring stripped, then `ast.dump` compared:
  **identical, 22457 == 22457 characters.** Positive control on the same instrument:
  `client.py` HEAD vs working tree under the same comparison reports **not identical**, first
  divergence at the guard predicate — so the check can fail.
- **The claim is true for `TESTING_ENDPOINT = ""`.** Executed against the real fakeshop URLconf:
  `""` → **200** `text/html`; `None` → `/None` 404; `7` → `/7` 404;
  `"/missing-endpoint/"` → 404; each raising the same
  `ValueError: Content-Type header is "text/html; charset=utf-8", not "application/json"`. The
  landed "ordinarily a 404" is exactly the hedge that makes the sentence true for the one string
  that does not 404; the reviewer's proposed narrowing to "a wrong endpoint *string*" would have
  made it false, and was correctly not applied.
- **The claim is true for a lazy value.** `reverse_lazy("index")` is a `__proxy__`
  (`isinstance(_, str)` is `False`); the accessor returns it verbatim, `TestClient().path` holds
  the proxy, and posting it routes and returns 200. The coercion is present in the installed
  Django (read, not remembered — `django 6.1`, `strawberry-graphql 0.324.0`, Python 3.14.2 via
  `uv pip list`): `inspect.getsource` of both `RequestFactory.generic` and
  `AsyncRequestFactory.generic` contains `parsed = urlsplit(str(path))  # path can be lazy`.
- **No validation was added**; the body is still
  `return getattr(settings, TESTING_ENDPOINT_KEY, "/graphql/")`, as maintainer Decision 2
  requires.

### M1's marker is a real discriminator

- Both endpoint-rung rows **keep the positive hit** — `assertResponseNoErrors(res)` plus
  `assertTrue(res.data["allItems"]["edges"])` — and add
  `assertEqual(res.response[_PROBE_MARKER_HEADER], _PROBE_MARKER_VALUE)` beside it. Neither was
  weakened to an exception-shape probe, which is what Decision 11 and Cohort B both asked for.
- Re-run entry 7 (marker stamp deleted): **exactly the two live rows fail**, and nothing else —
  so the marker is load-bearing rather than decorative, and a fall-back to `/graphql/` under the
  same probe URLconf cannot supply it.
- Re-run entries 5 and 6 (the production rungs dropped): each failing set now **contains its
  live row**. Cohort B measured both as adding zero live rows at this same wide scope; they now
  fail. The rows that previously could not fail now can, which is M1's whole claim.
- Mechanism confirmed read-only as well: `HttpResponse.__getitem__` raises `KeyError` on a
  missing header, so the assertion cannot pass vacuously on a response that never routed to
  `/alt/`.

### `_RecordingTestClient` deletion is complete

- Two instruments, both with their populations stated. Name sweep across the whole checkout
  (747 files under `rg`'s walk): **16 hits, all prose inside this cycle's own `bld-043-*`
  artifacts**, which are per-cycle scratch — zero in any source or test tree. Spelling-independent
  second instrument: `seen_urls`, the attribute only that class defined, swept with
  `--no-ignore --hidden` → **4 hits, in the same two artifacts, none in code.**
- The row it drove now constructs `TestClient("/constructor/", client=_RecordingDjangoClient())`
  and reads the target off `transport.posts`, so the real `TestClient.request` executes. It kept
  every prior assertion's intent (`/percall/`, `client.path` unchanged, `isinstance(res, Response)`,
  `res.data`, `isinstance(res.response, _CannedJSONResponse)`, the fall-back on the second call)
  and it now **fails under entry 5's mutation**, which it could not do before.
- `check_citations.py --check` → `OK: 995 citations resolve (825 in 441 .py files, 170 in
  KANBAN.md)`. Worker 2's own run read 442 `.py` files; the population moved between the two runs
  because the tree is shared, not because of anything in this cohort. Both green.

### High:

None.

### Medium:

None.

### Low:

#### L-W3-1 — the rationale's F5 entry quotes the retired predicate as present-tense HEAD fact, and the plan's enumerated site list omits it

`docs/SPECS/appx/spec-043-test_client-0_0_14-rationale.md:185` reads
`*HEAD:* the shipped code is ... followed by \`if not variables: raise AssertionError(...)\` —
**truthiness on both**`. That sentence is a factual claim about the shipped code, and it is false
the moment this cohort lands. The plan's `### The spec and rationale sites enumerated now, so the
deferred pass cannot miss one` enumerates six spec sites plus the docstring for the guard family,
and specifies the rationale work as "one entry per maintainer decision" — it does not name this
existing F5 line, so the instrument built to stop a partial fix does not cover the one rationale
site that already carries the old spelling. Escalation 1's fact 9 did name it ("rationale F5 (appx
rationale ~175-200)"), which is what makes the omission an enumeration gap rather than a discovery.

Why it matters: `START.md` "Partial claim fix = dominant residual defect", and the rationale is
the instrument a later Worker 3 reads to check an implementation against its reasoning — a stale
`*HEAD:*` line there reads as evidence, not as history. Recommended change: Worker 1 folds this
site into item 18's enumeration and rewrites the clause to name the respelled predicate while
keeping F5's finding intact (the finding — that the spec described `files is not None` /
`variables is None` and the code did not — is unaffected and must survive).

**Disposition: routed to Worker 1, not dispatched back to Worker 2.** The rationale is Cohort C's
custodian's file and Worker 2 is forbidden to open it (`BUILD.md` `### Who reads it, and when`),
so there is no Worker 2 action this could become. Recorded under `### Notes for Worker 1` below.

#### L-W3-2 — the async default-arm row is a one-row pin, and nothing in the record says so

`tests/testing/test_client.py::test_async_client_defaults_to_djangos_async_transport` is the only
row that fails when `AsyncTestClient.__init__`'s default arm is removed (measured above: 1 row).
Worker 2's note explains why the row does not appear in entry 4's list, which is correct, but the
note stops at "it pins the arm itself" without a number, so the record leaves the arm's pinning
unmeasured.

**Disposition: intentionally not dispatched, reason recorded.** The line is unchanged at HEAD and
this pass introduces no production boundary, so `BUILD.md` `### What needs a proof, and what does
not` asks for no proof on it and `### Acceptance rule`'s 0-or-1 threshold does not bite; the
boundary the plan named (the presence check) is at 3 rows, met. The measurement is recorded here
so a later pass has the number instead of re-deriving it, and a second row (for instance asserting
the default transport's `post` is awaitable) is a cheap option for whoever next touches that area.

### DRY findings

- **The respell adds one repeated executable literal, and it is the honest shape.** Measured, not
  eyeballed: `scripts/review_inspect.py` on the working tree reports **3** repeated string
  literals (`6x files= path`, `2x variables`, `2x operations`); the same helper on the HEAD copy
  reports **2** (`6x files= path`, `2x operations`). The delta is `"variables"`, now written
  twice inside `_build_body` — once by the emission that writes the member, once by the guard
  that reads it. A named constant would retire it, and is not worth it here: the two sites are
  eight lines apart in one method, and the drift the constant would prevent fails **closed** and
  loudly — rename the emitted key without the guard and every `files=` call raises, which four
  rows catch immediately. Two sites, one method, fail-closed on drift: the honest shape.
- **The guard no longer duplicates the emission's *condition*,** which was the actual duplication
  (escalation 1's single-edit-site test scored that pair at 2 sites). It is now 1: changing the
  emission rule moves the guard with it for free. This is a DRY improvement, not a new debt.
- **No new helper, constant, or validation branch was authored.** `_safe_arg_repr` is reused at
  its existing call sites; L1 adds a row, not code.
- **The new rows are not near-copies.** The three async transport classes
  (`_RecordingAsyncTransport` + `_BoolFalsyAsyncTransport` + `_LenFalsyAsyncTransport`) hold the
  recording body once and each subclass declares only how it is falsy; the two falsiness
  spellings are the load-bearing half of entry 4's count, not decoration. The marker header is
  two module constants read three times rather than a literal repeated three times.
- **Existence challenge: none raised.** The two things this cohort adds that could carry one —
  the marker header and the async recording family — each have a measured reason to exist
  (entry 7 fails exactly two rows without the marker; entry 4 drops to one row without the two
  falsiness spellings). `_RecordingTestClient`'s deletion is itself the cohort's existence win.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` → **empty**; `__all__` and the
re-export list are unchanged. `git diff HEAD -- django_strawberry_framework/testing/__init__.py`
→ **empty** as well, so the six exported testing names are untouched.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. Swept for partner-file
drift anyway, since the guard and endpoint claims live in more than one medium: `docs/README.md`
carries the endpoint ladder and the `APPEND_SLASH` note but **no** claim about the guard or about
a wrong endpoint's 404 (`rg 'variables' docs/README.md` → 0 hits);
`examples/fakeshop/test_query/README.md`'s suite map entry for `test_client_api.py`
(#"Request-driving half of the `TestClient` family's coverage") is unaffected, and the module
docstring it indexes is unchanged and still true. `docs/GLOSSARY.md` quotes neither message.

### What looks solid

- The respell is the smallest change that closes the class the escalation found, and it keeps the
  message bytes, so the six spec sites quoting the message do not move.
- Every one of the six previously weakly pinned boundaries clears the acceptance rule, and the
  rows added are decompositions of assertions that already existed rather than new claims — the
  `for`-loop-to-`parametrize` conversions in particular turn three one-node-id contracts into
  nine node ids without inventing a fixture.
- The re-pointed per-call row and the marker header both fix the same defect class from opposite
  ends: a double that re-implemented the seam, and a probe that destroyed its own discriminator.
- Rung 3's row gaining a `TESTING_ENDPOINT` override is a strengthening the plan did not ask for
  and is correct: it proves the class attribute beats the settings key, not merely the default.
- The build report's own near-miss disclosure (the async default arm) is the kind of thing that
  usually goes unwritten; it was accurate, and it is what made the completing measurement cheap.

### Temp test verification

No temp test was needed to demonstrate a non-distinguishing assertion: the seven re-runs plus the
two pre-registered mutations settle every question mechanically. Scratch artifacts, all outside
the repository except the manifest:

- `<scratchpad>/probe_w3_guard.py` — the 17-case verdict census (guard respell).
- `<scratchpad>/probe_w3_endpoint.py`, `<scratchpad>/probe_w3_lazy.py` — the endpoint docstring's
  truth conditions.
- `<scratchpad>/ast_ident.py` — the docstring-stripped AST comparison plus its positive control.
- `<scratchpad>/inspect/`, `<scratchpad>/inspect-head/` — `review_inspect.py` output for the
  working tree and the HEAD copy (**never** `docs/shadow/`, per `AGENTS.md` rule 23).
- `docs/builder/temp-tests/043/cohort-c-w3/proofs-w3.json` — the two Worker 3 mutations, kept so
  the measurement is reproducible; its scratch root is the session scratchpad.

Disposition: none promoted; nothing here caught a behavior bug. Worker 2's manifest at
`docs/builder/temp-tests/043/cohort-c/` was re-run, not modified.

### Static helper use

`uv run python scripts/review_inspect.py django_strawberry_framework/testing/client.py
--output-dir <scratchpad>/inspect` — exit 0. Required: the diff adds logic to an existing `.py`
file well over 150 source lines. Walked entry by entry:

- **Django / ORM markers: none.** Nothing to justify.
- **Calls of interest: 4.** `set()` (the reserved-key intersection) — boundary, 3 rows, re-run as
  entry 2. `isinstance()` twice (the walker's list / dict arms) — both exercised by entry 3's four
  rows. `len()` (inside the walker's guarded `try`) — pinned by the pre-existing hostile-`__len__`
  rows, untouched by this cohort. No finding.
- **Control-flow hotspots: 3.** `_build_body` is 70 lines / **5** branch nodes against HEAD's 67 /
  **5** — the respell replaces a predicate and adds no branch, confirmed by running the helper on
  the HEAD copy rather than trusting the plan's figure. `_assert_file_placeholders` (83 / 13) and
  `query` (64 / 0) are unchanged. Medium-tier complexity attention paid to the walker: this cohort
  adds no branch to it; L1 is a row.
- **Repeated string literals: 3**, up from 2 — see DRY findings, where the delta is named and
  disposed of.
- **Imports: 13**, one-way (`testing` → `conf`, `exceptions`), no cycle, unchanged.

Also run read-only: `ruff format --check` (4 files already formatted), `ruff check`
(All checks passed!), `check_trailing_commas.py --check` (pass), each over the four files as a
shell **array** — the unquoted-variable spelling collapses four paths into one argument and the
tools then report a missing file, which is `START.md`'s zsh word-splitting instrument exactly.

### Dispatched findings checklist walk

Walked all 19 boxes against the diff. The fifteen boxes Worker 2 ticked
(1-5, 8-15) each have matching work in the diff — no over-tick, and no landed-but-unticked box.
The six `- [ ]` boxes are all **(W1)** boxes deferred by the plan's
`### Spec amendment timing — decided: deferred`, and all six defects they name are still present,
so none was silently closed: spec `#"the traceback carries the failing"` (line 851),
`#"endpoint value surfaces as an ordinary 404 at request time"` (204),
`#"*string* is a 404 at request time"` (861),
`#"wrong endpoint string is an ordinary 404 at request time"` (1199), and the two
`custom-view plumbing` sites (321, 1438). Checked against the **working-tree** spec (dirty,
Cohort A's reconciled rewrite, which is the version this cohort's custodian will amend); `git show
HEAD:` used only to confirm the `traceback carries the failing` clause predates Cohort A's rewrite
and so is a second custody touch rather than a regression it introduced.

No overturned premise was re-raised: Cohort B's "the guard is redundant with the walker" is
contradicted by my own 17-case census, its "the accessor has a validation gap" by the executed
`str()` coercion, and its "all ten raw-post sites are honest exemptions" is Cohort D's territory
and outside this review.

### Notes for Worker 1 (spec reconciliation)

1. **Add `docs/SPECS/appx/spec-043-test_client-0_0_14-rationale.md:185` to item 18's enumerated
   site list** (Low finding L-W3-1 above). Its F5 entry states `*HEAD:* the shipped code is …
   \`if not variables: raise AssertionError(...)\` — **truthiness on both**`, which the respell
   falsifies. Rewrite the clause to name `if "variables" not in body:` while keeping F5's actual
   finding — that the spec described `files is not None` / `variables is None` and the code never
   did — intact, and keep the `files={}` half of the sentence, which is unchanged and still true.
2. **The guard's six citing spec sites need confirmation, not rewriting**, and I re-confirmed the
   basis for that plan decision independently: the respelled guard rejects exactly the same call
   shapes as before (0 mismatches in 17 input classes), so the label "empty-`variables` guard"
   stays accurate and renaming it would strand four citers for no contract gain.
3. **The endpoint docstring's landed wording is true as written**, including for
   `TESTING_ENDPOINT = ""` (200, not 404) and for `reverse_lazy(...)` — both executed here, not
   reasoned. Quote it into the three spec sentences verbatim; do not narrow it to "a wrong
   endpoint *string*".
4. **Item 19's row inventory should be read off the diff**, and two deletions travel with it:
   `test_mixin_endpoint_rungs_class_attr_settings_and_per_call` no longer exists (three named rung
   rows replace it) and `test_files_placeholder_cannot_descend_into_a_scalar_raises` is four
   parametrized ids. Any spec sentence naming either by its old single-row shape is stale. One
   addition Worker 2's list does not flag: rung 3's row now also asserts the class attribute beats
   the **settings key**, so a Test-plan sentence describing it as beating only the default is
   stale too.
5. **`Escalated:` — escalation 2's two optional rows** (a live parametrize of
   `test_wrong_configured_endpoint_surfaces_django_non_json_decode_error` over `None`, and a
   `tests/base/test_conf.py` row asserting the accessor returns a non-`str` verbatim) did not
   land, correctly: neither is in this cohort's write set. Resolution paths, for Worker 1 to pick
   between: record them in the rationale under Decision 7 as considered-and-not-taken (the claim
   they would pin is about Django's own coercion, already swept 5.2.0 → 6.1.0), or home them on a
   named card. They must not be dropped silently.
6. **The async default-arm measurement** (Low L-W3-2): 1 row, by the mutation that removes the
   arm. Nothing is owed; recorded so the number exists.

### Review outcome

`review-accepted`.

Every dispatched Worker 2 box landed; no High and no Medium finding; the two Low findings each
carry a disposition — L-W3-1 routed to Worker 1, whose file it is, and L-W3-2 intentionally not
dispatched with the reason recorded. Every recorded failability proof carries all seven fields,
none is weakly pinned, all seven were independently re-run at the recorded scopes with **identical
node-id sets** and zero collection or setup errors, and two further mutations of my own closed the
one question the build report left open. The tree carries no mutation: `client.py` and
`test_client_api.py` are byte-identical to Worker 2's recorded hashes and the focused scopes
re-run 55 / 66 passed.


---

## Final verification (Worker 1)

The deferred custody work this cohort's plan named
(`### Spec amendment timing — decided: deferred to final verification`) is done in this pass.
No `.py` was written here; the production diff is Worker 2's two hunks and nothing else.

### The enumeration was re-derived, not trusted — and it had three holes, not one

Worker 3's `L-W3-1` is a finding about the **instrument**, not about one line, so the site
population was rebuilt from scratch before anything was written, with spelling-independent
sweeps that count occurrences rather than matching lines (`BUILD.md`
`## Claims are proven mechanically`). Tokens swept across the spec and the rationale:
`404`, `ordinar`, `traceback`, `not variables`, `falsy`, `truthiness`, `custom-view`,
`plumbing`, `test_multi_db`, `exemption`, `retained raw`, `client.post`, `_build_body`,
`recording`. Counts, spec / rationale: `404` 7 / 0, `traceback` 1 / 0, `not variables` 1 / 1,
`falsy` 4 / 3, `truthiness` 5 / 6, `custom-view` 2 / 0, `test_multi_db` 3 / 0,
`client.post` 7 / 1, `retained raw` 2 / 0.

Two instruments the enumeration did not have were added and both paid:

- **Every `test_` identifier the spec and the rationale cite, resolved against the actual
  suites.** 34 distinct identifiers; the 5 that resolve to nothing are all illustrative names
  in fenced examples (`test_items`, `test_bad_selection`), a directory (`test_query`), and one
  naming alternative in a rationale entry (`test_client_helper`). So **no spec citation names a
  row this cohort renamed** — which is the claim the plan's item 19 rested on and never
  measured.
- **A refs-vs-defs + in-page-anchor + def-target auditor over both files**
  (`<scratchpad>/audit_links.py`). Before: spec 79 uses / 80 defs / 22 in-page links, one
  unused def; rationale 24 / 24 / 13, clean.

**Holes found, all three now closed:**

1. `docs/SPECS/appx/spec-043-test_client-0_0_14-rationale.md`'s F5 entry stated the retired
   predicate as present-tense HEAD fact (`L-W3-1`). Confirmed and rewritten.
2. **The exemption family is four sites, not the two the plan scoped** — confirmed
   independently rather than inherited from Cohort D: `custom-view` occurs **twice** (the
   Slice-2 checklist and Decision 11's "switchover's own discipline"), and `retained raw`
   occurs **twice more** (`## Test plan`'s Slice-2 verification paragraph and the matching
   `## Definition of done` row). 2 + 2 = 4, and a `client.post` sweep over the whole spec
   returns 7 occurrences of which the other three are unaffected framing.
3. **`## Test plan` scenario 8 described the deleted test double as the current mechanism** —
   "a tiny in-file `TestClient` subclass overrides `request(...)` to record the effective
   `url`". That is `_RecordingTestClient`, which item 14 deleted. No pass named this site:
   not the plan's enumeration, not Worker 2's notes, not Worker 3's walk. It is the exact
   failure `START.md` `## Reconciling a spec with the tree` names — a derived description
   outliving its source — and it was reachable only by sweeping for the *mechanism* rather
   than for the guard's or the endpoint's vocabulary.

### Two proposed replacement texts were rejected as false, and measured to say so

Both were routed here as recommended wordings; a recommended amendment is a hypothesis, not an
instruction.

- **"No live file currently claims the hand-built-multipart exemption class."** False.
  `examples/fakeshop/test_query/test_products_api.py` carries **three** raw posts, each with a
  `Raw-multipart exemption (spec-043)` comment keeping the envelope because the *arbitrary file
  label* is the assertion. The claim was measured on the converting cohort's own four files and
  promoted to the tree — a population error of exactly the kind this cycle has now hit six
  times. The spec keeps the class, restated with its actual warrant.
- **"Outside `test_products_api.py`, `test_transport_api.py`, `test_auth_api.py` and the shared
  live-tier helper, no live file retains a raw `client.post(...)`."** False on the day it was
  written: `examples/fakeshop/test_query/test_list_field_async_api.py` retains an awaited raw
  post with no exemption comment, and that file is the concurrent spec-050 cycle's territory —
  excluded from this cycle by the applied partition, so a census sentence naming it could not
  be discharged here either. Live-tier census as measured this pass: raw `.post(` survives in
  `test_auth_api.py` (1), `test_products_api.py` (3), `test_transport_api.py` (2, plus one
  `client.generic("POST", ...)` a `.post(` sweep cannot see), and
  `test_list_field_async_api.py` (1). **So the Test-plan and DoD sentences were rewritten as a
  rule about the switchover's own population** — a retained raw post names the class it claims;
  a call meeting no class converts rather than acquiring a declaration — rather than as a
  tree-wide census a file this cycle may not touch falsifies immediately.

### Dispatched findings checklist audit

All 19 boxes walked against the diff and against the two documents.

- **Boxes 1–5 and 8–15 (Worker 2's):** every one confirmed landed. No over-tick, and no
  landed-but-open box. Spot-verified rather than read off the build report: the respell and the
  docstring are the only two production hunks (`git diff HEAD` over `testing/client.py` +
  `conf.py` is exactly those two, message bytes unchanged); box 2's rows carry
  `match="requires variables="` with ids `none` / `empty` / `falsy_dict_subclass`; box 4's
  async row exists; box 8's marker is two module constants stamped once and asserted at two
  call sites; box 9 parametrizes over `("operations",)` / `("map",)` / both; box 10 over
  `str` / `int` / `none` / `nested`; boxes 11 and 13 are the named async and mixin-rung rows;
  box 14's `_RecordingTestClient` is absent from the tree.
- **Boxes 6, 7, 16, 17, 18, 19 (the `(W1)` boxes):** all six landed in this pass and are now
  `- [x]`. Details under `### Spec changes made (Worker 1 only)`.
- **Nothing remains `- [ ]`**, so no deferral reason is owed for a checklist item. The
  deferrals this cohort carries are of a different kind and are catalogued below.

### Failability and fail-open re-confirmation

- **Every record exists with every required field.** Seven entries, each carrying the
  symbol-qualified boundary, the mutation, the scope as run, the pre-mutation state of that same
  scope, the failing node ids **listed**, the collection/setup error count separately (0
  throughout), and the revert byte-compared. Row counts 4 / 3 / 4 / 3 / 3 / 2 / 2 — no entry at
  0 or 1, so no boundary is weakly pinned and no `why 0` judgement is owed. Worker 3 re-ran all
  seven independently at the recorded scopes with identical node-id **sets**.
- **No fail-open shape landed.** Read off the diff rather than inferred from a green suite: the
  new predicate is a membership test on a dict the method built one line earlier — `BUILD.md`
  `### Fail-open shapes`' own prescription applied to the suspect that section names first — and
  the diff adds no clamp, no `getattr` default, no `or` fallback, and no broadened `except`.
  `conf.py`'s body is untouched.
- **The docstring-only claim for `conf.py` was proven by inverse, not asserted**: Worker 3's
  docstring-stripped `ast.dump` comparison against HEAD is identical at 22,457 characters, with
  a positive control on `client.py` showing the same instrument reports *not* identical. That
  discharges `START.md`'s "comment/docstring-only edit owes an INVERSE proof".

### Gates, run after the edits

A pre-edit green reading is no reading at all — this cycle's own recorded instrument failure.
Baselines were taken before the first byte was written and are shown beside the post-edit runs.

| Gate | Before | After |
|---|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-043-test_client-0_0_14.md` | `OK: 22 terms`, exit 0 | `OK: 22 terms`, exit 0 |
| `uv run python scripts/check_citations.py --check` (whole tree) | `OK: 995 citations resolve (825 in 441 .py files, 170 in KANBAN.md)`, exit 0 | identical, exit 0 |
| `uv run python scripts/check_trailing_commas.py <the two documents> --check` | exit 0 | exit 0 |

`check_trailing_commas.py` was run with **explicit paths only** on both readings; its default is
a repo-wide auto-fix that would rewrite the concurrent session's files. No pre-existing failure
outside the diff surfaced, so nothing is attributed away.

**Link and anchor audit, after.** Spec 79 uses / 79 defs / 22 in-page links / 0 undefined refs /
0 unused defs / 0 broken in-page anchors / 0 missing def targets. Rationale 26 / 26 / 13, same
zeroes. Two repairs the edits themselves required:

- dropping the exemption class orphaned `[test-multi-db]`, whose only two uses were the two
  sites removed. The definition was removed in the same pass; `grep -n 'test-multi-db'` over the
  spec now returns **0**.
- the two new rationale entries introduced `[conf]` and `[test-products-api]` uses with no
  definitions. Both defined, in the correct group headers (`django_strawberry_framework/` and
  `examples/`), paths relative to `docs/SPECS/appx/`.

**Cross-file fragment check.** Every reference definition in either file whose target carries a
`#fragment` was resolved against the other file's actual heading slugs: **0 broken**, so the
twelve `[rationale-dN]` pointers and the rationale's twelve `[dN]` pointers all still land.
**No Decision heading was rewritten**, so no `](#decision-N--…)` link was stranded; the in-page
audit confirms it rather than assuming it.

**Cross-reference sweep.** `grep -rn 'spec-043' docs/` → 187 occurrences across 30 files. The
non-cycle citers (`spec-042` and its companion, `spec-044`, `spec-053`, `spec-060`, `NEXT.md`,
`docs/TREE.md`) reference the spec by path or by Decision ordinal, not by quoted prose; a sweep
for `spec-043-test_client-0_0_14.md #"` across the tree finds exactly one substring citation
anywhere — `KANBAN.md` #"This spec lives at" — which names text this pass did not touch. The
remaining citers are this cycle's own `bld-043-*` and `build-043-*` artifacts, which are
per-cycle scratch and carry raw `path:NN` legitimately.

### Byte counts, measured

| File | Before | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-043-test_client-0_0_14.md` | 142,356 | 147,170 | +4,814 |
| `docs/SPECS/appx/spec-043-test_client-0_0_14-rationale.md` | 51,290 | 63,984 | +12,694 |

The rationale grew about 2.6x more than the spec, which is the shape the move is supposed to
produce: three maintainer decisions, their rejected alternatives, and two corrected reasons are
deliberation, and the spec absorbed only the corrected contract text.

### No `pytest` this pass

The dispatch forbids it and this pass changed no code. The focused scope the plan's
`### Final-verification obligations` step 9 named was already run twice at the tree as handed
over — Worker 2 recorded 66 passed, Worker 3 re-measured 55 package-tier / 66 package + live —
and the production files are byte-identical to the hashes both recorded. Re-running it here
would measure the same bytes a third time; the two documents this pass edited are not executable.

### Dispositions

- **`L-W3-2` — the async default arm.** Closed, not dispatched. Worker 3 pre-registered and ran
  the mutation that actually removes the arm (`AsyncClient()` → `Client()`) and it failed
  exactly one row, the one named for that arm, so the arm **is** pinned; entry 4's mutation was
  simply orthogonal to it (`None or AsyncClient()` still yields an `AsyncClient`). The line is
  unchanged at HEAD and this pass introduced no production boundary there, so `BUILD.md`
  `### What needs a proof, and what does not` asks for nothing and the acceptance rule's 0-or-1
  threshold does not bite. The measurement is now recorded **durably**, in the rationale under
  Decision 8, rather than only in this artifact — the artifact closes with the cycle and the
  question would otherwise be re-derived by whoever next reads a row list beside a failing-node
  list and reads the difference as a miscount.
- **Escalation 2's two optional endpoint rows — deferred, with a reason, and homed.** Neither
  landed and neither should have: the package-tier row belongs in `tests/base/test_conf.py`,
  outside this cohort's write set, and the live parametrization is in Cohort C's live file but
  pins a statement about *Django's own* `str()` coercion, already established across the audited
  release range `5.2.0` → `6.1.0` by reading every cached wheel. They are recorded in the
  rationale under Decision 7 as **considered and not taken, with the reason**, so a later pass
  adding either knows they are absent by decision rather than by omission. Owner named in the
  deferred-work catalog below.
- **Cohort D's notes, discharged item by item.** Its exemption-class widening (four sites) is
  landed; its two recommended replacement sentences are rejected as measured above and replaced
  with true text; its conversions are reflected in Decision 11's new change record; its
  node-count warning needs no spec text (no spec sentence publishes a node total — verified:
  the `test_` identifier sweep found none). Three of its items cannot be closed inside the fence
  and are catalogued below.

### Deferred work catalog contributions (for `bld-043-final.md`)

Each with the reason it is deferred and, where one exists, a named owner.

1. **`examples/fakeshop/test_query/README.md`'s `Async` bullet is falsified and has no owner.**
   It names `django.test.AsyncClient` and a helper exemption for
   `test_relations_async_api.py`, which now drives `AsyncTestClient` and declares no exemption.
   The file is a `.md` and the cycle's fence is spec files plus package `.py` only, so no cohort
   could touch it; homing it on a card needs a board edit the same fence excludes. **Owner:
   maintainer** — the cycle's one genuinely undischargeable item. Independently re-confirmed
   this pass: the file is not in any write set and is not dirty.
2. **One undeclared raw async post remains in the live tier**,
   `examples/fakeshop/test_query/test_list_field_async_api.py`, excluded from this cycle as the
   concurrent spec-050 cycle's territory. It is the reason the Test-plan and DoD sentences are
   stated as a rule rather than a census. **Owner: the spec-050 cycle**, which is already
   converting that file; the spec text as now written does not need amending when it lands.
3. **No gate fails a raw `.post(` / `.generic(` in `test_query/` that carries no exemption
   declaration.** Five files drifted in two months because the rule has no gate
   (`START.md` "Rule w/o gate rots"). Naming the owning card needs a board edit outside the
   fence. **Owner: maintainer**, to home on a card.
4. **An awaited live-tier post helper.** Five near-identical awaited call bodies across four
   live modules, a sixth waiting in the concurrently-owned file. The natural home is the shared
   live-tier client module, declared sync-only and in no cohort's write set. The extraction
   condition the converting cohort set is met. **Owner: maintainer**, to home on a card;
   recorded in the rationale under Decision 11 so the shape is not re-derived.
5. **Escalation 2's package-tier endpoint row** (`tests/base/test_conf.py`, asserting the
   accessor returns a non-`str` verbatim). Outside every cohort's write set this cycle;
   `tests/base/` may grow rows but no files. **Owner: whichever card next opens
   `tests/base/test_conf.py`**; the rationale records why it is absent.
6. **Two cohorts shared the three `worker-memory/043-worker-{1,2,3}.md` files**, which made the
   ~50-line consolidation cap unsafe (consolidating would clobber a concurrent pass's entry) and
   made role memory a real cross-cohort channel. Both cohorts appended rather than consolidated.
   **Owner: Worker 0**, for the next partition's memory-stem naming.

### DRY check across this cohort and the prior accepted cohorts

No new duplication. The cohort authored no helper, constant, validation branch, or coercion
utility; the one new repeated executable literal (`"variables"`, twice in one method, eight lines
apart) was measured by running the static inspection helper against both the working tree and a
HEAD copy — 3 repeated literals against 2 — and it fails **closed** and loudly on drift, which
four rows catch. Against it, the respell **retires** a real duplication: the guard no longer
restates the emission's condition, so the single-edit-site count for that pair went from 2 to 1.
This pass adds no prose duplication either: the corrected contract text lives once in the spec
and its reasoning once in the rationale, keyed by decision heading and anchor.

### Summary

The cohort delivered. Two production hunks — a respelled guard predicate whose verdicts are
provably identical and a restated docstring whose every clause was executed rather than reasoned
— plus fourteen new node ids across its two test files (the focused scope moved 52 → 66), one
live discriminator, and one deleted test double
that re-implemented the line it tested. Six previously weakly pinned boundaries now clear the
acceptance rule, proved by seven failability loops and re-run independently with identical
node-id sets. The deferred custody work landed here: **15 spec edits and 8 rationale edits**
(counted as applied, not estimated — 14 prose sites plus one orphaned reference definition in the
spec; 7 entries plus one link-definition pair in the rationale),
against a site population re-derived from scratch that turned up three sites the plan's own
enumeration had missed. Every claim the three escalations overturned is recorded with the
alternatives it beat and the reason each lost, and two proposed replacement texts were measured,
found false, and replaced.

### Spec changes made (Worker 1 only)

All against `docs/SPECS/spec-043-test_client-0_0_14.md` and
`docs/SPECS/appx/spec-043-test_client-0_0_14-rationale.md`, the cohort's two custodian files.
Sites are named by content; every one was located by content before editing, and the whole
population was asserted present before a byte was written
(`START.md` "Enumerate, never grep-count, before writing").

**Spec — the endpoint-claim family (box 7, maintainer Decision 2).** Four sites graded, three
rewritten:

1. `## Key glossary references`, the `ConfigurationError` bullet
   #"key itself needs no new validation beyond that existing seam" — "surfaces as an ordinary
   404" → "surfaces at request time as whatever the URLconf serves at that path — ordinarily a
   404". The hedge is load-bearing: `TESTING_ENDPOINT = ""` routes to the URLconf root and
   returns 200.
2. `### Error shapes`, the malformed-settings bullet — the italicised *string* narrowing
   removed; the bullet now states that a wrong value of **any** type behaves alike, naming
   Django's `str()` path coercion and `/None` as the worked case.
3. `### Decision 7`'s closing paragraph #"No validation beyond" — restated to the mechanism,
   with the lazy-endpoint case named as the reason a type gate is not merely unnecessary but
   wrong.
4. `### Error shapes`, the non-JSON bullet's parenthetical #"wrong endpoint → 404 HTML page" —
   **examined and deliberately left**. It is an example of a cause, not a universal claim, and
   is true of the case it names. Recorded so the next reader knows it was graded, not missed.

**Spec — the false-on-its-own-date clause (box 6).** `### Error shapes`, the non-JSON bullet's
#"the traceback carries the failing status" → the three observable facts, each attributed to
what actually produces it: the runner renders the failing `HttpResponse` as a frame local of
Django's `_parse_json`, the captured `django.request` log names the path, and the exception
message names only the `Content-Type`. Verified false at HEAD as well as in the working tree, so
this is a second custody touch on that sentence and not a regression of the prior custody pass.

**Spec — the guard family (Decision 1's landed shape).** Three sites rewritten, four confirmed
unchanged:

5. `### Error shapes`, the `files=`-without-`variables` bullet — the quoted
   `if not variables: raise AssertionError(...)` and the "truthiness at both ends" framing
   replaced by the landed contract: truthiness enters the envelope, and the guard raises when
   the envelope just built carries no `variables` member for the `map` to point into.
6. `### Decision 9`'s "multipart envelope is entered on truthiness" paragraph — same correction,
   plus the one sentence a reader needs in order not to re-delete the guard: a falsy mapping
   carrying real placeholders is the class the per-path walker alone accepts while the `map`
   points into a member the envelope never wrote.
7. `## Edge cases and constraints`, the `files=`-requires-placeholder-variables bullet — same
   correction in that section's own voice.
8. The four label-only citers (`Decision 11`, `## Test plan`, the coverage paragraph, the
   `## Definition of done` row) name the **empty-`variables` guard** by label. The label stays
   accurate — the respelled guard rejects exactly the input set the old spelling did — so all
   four were **confirmed rather than rewritten**. Renaming the label would be a rename that
   strands four citers for no contract gain.

**Spec — the exemption class and its empty-population siblings (box 17, maintainer
Decision 3).** Four sites, not the two the plan scoped:

9. The Slice-2 checklist's documented-exemption sub-bullet and `### Decision 11`'s "switchover's
   own discipline" paragraph — the `test_multi_db.py` custom-view-plumbing class removed from
   both lists; the surviving classes restated with their actual warrant (an arbitrary-label
   `operations` / `map` envelope the path-keyed builder never emits, malformed-body negatives,
   content-type probes, queries via GET), and Decision 11 gains the one clause that stops the
   class being re-invented: a test whose only reason for posting raw was per-file plumbing does
   not meet the exemption and converts.
10. `## Test plan`'s Slice-2 verification paragraph and the matching `## Definition of done`
    row — "each retained raw `client.post(...)` carries the wire-shape-exemption comment"
    restated as a rule over the switchover's own population, naming **which** class a retained
    post claims and stating that a call meeting no class converts rather than acquiring a
    declaration, and that a class whose last exemplar converts leaves the list.
11. `[test-multi-db]` reference definition removed — orphaned by the two removals above.

**Spec — the Test plan and DoD extension (box 19), read off the diff and not off the plan:**

12. `## Test plan` scenario 8 — the deleted test double's mechanism replaced by the landed one
    (a recording stand-in supplied as the wrapped Django client, so the **real**
    `TestClient.request` selects the target the row reads), with the reason stated in one clause
    so the double is not reintroduced: a subclass overriding `request()` re-implements the line
    under test. The mixin's three rung rows are named, one node id each.
13. `## Test plan` scenario 11 — the probe URLconf's new discriminator stated, with the reason:
    the probe mount also mounts the project's own URLs, so without it a request that fell back
    to the real endpoint satisfies every other assertion.
14. `## Test plan` scenario 15's inventory — the nested-depth leg of the non-descendable
    rejection, the envelope-coherence guard's rows (including the falsy-`dict`-subclass case,
    named as the one the walker accepts), the async color, the reserved-envelope-key rows, the
    second `_safe_arg_repr` argument position, and the two async transport-selection rows all
    given named owners, so the coverage paragraph's "every branch has a named owner" claim stays
    true of the suite as it now is.

**Rationale — six entries (boxes 16 and 18), each keyed to its decision by heading and anchor:**

15. **F5's `*HEAD:*` clause** corrected (`L-W3-1`): it stated the retired predicate as
    present-tense shipped fact. Rewritten to name the landed predicate and cross-link the
    Decision 9 change record, with F5's actual finding — that the spec described
    `files is not None` / `variables is None` and the code never did — and the `files={}` half
    both left intact.
16. **Decision 9 — maintainer Decision 1.** The respell, the falsy-container evidence that
    overturned the finding, the DRY re-reading (the duplicated pair was guard-and-emission, not
    guard-and-walker), and three alternatives with the reason each lost: deletion (the walker
    does not catch the class at all), keep-and-only-add-rows (leaves a truthiness test where
    absent and empty differ), and the superseded keep-and-pin *reasoning* (it invoked "never a
    weaker boundary" while asserting the guard decides no verdict, which would forbid deleting
    any dead branch). Plus the claim the decision may no longer make.
17. **Decision 7 — maintainer Decision 2.** No validation added; the `str()` coercion evidence
    across the audited release range; the accessor census; two alternatives with the reason each
    lost (a type gate ships a concrete `reverse_lazy` regression and makes this key the module's
    first shape gate against four sibling docstrings; leaving both alone keeps a docstring that
    is false for `""`); the second, previously unknown defect (the traceback clause, false on its
    own date); and escalation 2's two optional rows recorded as considered-and-not-taken with
    the reason.
18. **Decision 11 — maintainer Decision 3's spec half.** The class drop and its warrant; two
    alternatives with the reason each lost (a false declaration forecloses the next reader's
    question; deferring needs a board edit the fence excludes and an unowned item dies); the two
    census corrections that travelled with it (16 sites across 8 files, not 9; a
    `client.generic("POST", ...)` is invisible to a `.post(` sweep); the measured surviving
    exemption list with the rejection of the "no live file claims this class" wording; and why
    the Test-plan and DoD sentences are a rule rather than a census.
19. **Decision 11 — the live-tier conversions.** Nine call sites across four live modules moved
    onto the package's own clients with assertions preserved, the two conversion traps that are
    invisible until a row inverts, and the unextracted awaited helper with its condition and its
    blocker.
20. **Decision 6 — `L3`'s corrected reason.** The recorded reason ("load-bearing for dataclass
    field ordering") is false: the engine `Response` declares three fields and none is defaulted,
    so a no-default subclass constructs fine. The disposition stands for a different reason —
    shipped public re-export on an `0.0.x` line — with both in-repo construction sites passing
    `response=` explicitly.
21. **Decision 8 — the async default arm.** The measurement recorded so it is not re-derived:
    the selection mutation cannot reach the default arm by construction, and the mutation that
    replaces the arm fails exactly the row named for it.
22. Two reference definitions added for the new entries' links (`[conf]`,
    `[test-products-api]`), in the correct group headers with paths relative to
    `docs/SPECS/appx/`.

**Not done, deliberately:** no amendment block, no retraction paragraph, no revision entry, and
no "as of" hedge anywhere in the spec; no severity label, cohort name, round number, or worker
attribution in it either. The spec reads as a clean current contract. All of that lives in the
rationale, keyed by decision, and in this artifact.

### Final status

`final-accepted`.
