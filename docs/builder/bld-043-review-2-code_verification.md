# Build: Review round 043 / cohort B — independent code verification (V1–V6)

Spec reference: `docs/SPECS/spec-043-test_client-0_0_14.md` (archived; `Status:` line 72)
Build plan: `docs/builder/build-043-test_client-0_0_14.md` `### Cohort B verification questions (V1–V6)`
Diff under review: post-ship commit range `653a3841..HEAD`, scoped to this card's files
Status: revision-needed

## Plan (Worker 1)

This cohort is **review-only** and had no separate Worker 1 planning pass: the
build plan is the plan, and its `### Cohort B verification questions (V1–V6)`
are this artifact's `### Dispatched findings checklist`. Recorded here so the
next reader is not looking for a missing section.

### Required-reading gap (recorded, not waived)

`docs/builder/BUILD.md` `## Required reading per worker` marks
`docs/spec-<NNN>-…-rationale.md` `yes` for Worker 3. **The spec-043 rationale
companion does not exist** — it is Cohort A's concurrent deliverable (build plan
finding F1), and this cohort is forbidden from reading Cohort A's in-flight
output. So the row is unsatisfiable this pass. Consequence for this review: the
"check the implementation against the recorded reasoning" half of the rationale
read was performed against the spec's own inline `Revision history` block and
its `Alternatives considered (and rejected)` sub-lists instead, which is where
that reasoning currently lives (and which is exactly what finding F2 moves out).

### Dispatched findings checklist

- [x] **V1** — did anything in the spec's Slice 1 checklist never land? Walk every sub-check: the settings key constant + accessor, the module's every named symbol (`Response`, `TestClient` with `__test__ = False`, the constructor, `_build_body`, the file-map builder, `request(..., *, url=None)`, the owned `query()`, `login()`, `AsyncTestClient` + async `query()` + async `login()`, `GraphQLTestMixin` with `GRAPHQL_URL`, both assertion helpers, `GraphQLTestCase`, `GraphQLTransactionTestCase`), the six `testing` root re-exports, and the docstring obligation. Report each as present / absent / divergent with a symbol-qualified citation.
- [x] **V2** — did anything in Slice 2 (the live-suite switchover) never land? State the population; classify every surviving raw `client.post(...)` as an honest wire-shape exemption or an unconverted file.
- [x] **V3** — is the per-call `url=` non-persistence contract actually held?
- [x] **V4** — is every branch F3 introduced actually pinned by a test? Name the node ids.
- [x] **V5** — does the mixin delegate's endpoint resolution match Decision 7's five-rung ladder end to end?
- [x] **V6** — is there any fail-open shape in the module?

---

## Review (Worker 3)

### Instruments used, and the population each ran on

Recorded before any result, per `START.md` `## Instruments that lie`.

- **Working tree vs HEAD.** `git status --short` at pass start: **7** entries —
  `START.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, `docs/feedback.md`,
  `examples/fakeshop/apps/kanban/tests/test_mutations.py`,
  `examples/fakeshop/db.sqlite3` (the plan's six baseline-dirty out-of-scope
  paths) plus the untracked `docs/builder/build-043-test_client-0_0_14.md`.
  **No file under review is dirty**, so every reading below is HEAD content read
  from the working tree; no `git show HEAD:` round trip was needed and none of
  `git stash` / `checkout` / `restore` / `worktree` was run.
- **Live-tier census population (V2).** Derived from the directory listing, not
  from a vocabulary guess: `examples/fakeshop/test_query/test_*.py` =
  **26** files, plus `conftest.py` = **27** files swept. Asserted in the sweep
  itself (`assert len(files) == 27`).
- **Post-ship commit range.**
  `git log --oneline 653a3841..HEAD -- django_strawberry_framework/testing/client.py django_strawberry_framework/conf.py django_strawberry_framework/testing/__init__.py tests/testing/test_client.py examples/fakeshop/test_query/test_client_api.py`
  → **25** commits.
- **Static inspection.** `uv run python scripts/review_inspect.py django_strawberry_framework/testing/client.py --output-dir <session scratchpad>/inspect` — exit 0, both outputs written. `--output-dir` is the session scratchpad, never `docs/shadow` (`AGENTS.md` rule 23; the build plan records the reconciliation against `BUILD.md` `### How to run`).
- **Failability proofs.** `uv run python scripts/prove_failability.py docs/builder/temp-tests/043/proofs.json` — 12 entries, scratch root outside the repository. Mutations recorded below **before** they were made.

### Mutations recorded before they were made

`worker-3.md` "Reading is necessary, not sufficient" requires the mutation to be
in the artifact before it is applied. The twelve entries and their exact
mutations are the manifest at `docs/builder/temp-tests/043/proofs.json`, written
before the tool was run in mutating mode; the tool was first run
`--check-anchors-only` (every anchor matched exactly once) so no entry could
stack on a pre-existing live mutation. Each mutation targets
`django_strawberry_framework/testing/client.py` only, one at a time, restored in
a `finally` and proved by byte comparison before the next entry starts. Results
in `### Failability proofs (independent re-run)` below.

### Recovery note: this pass was resumed, not restarted

A prior Worker 3 subagent of **this same cohort and this same pass** began this
artifact and died mid-run on a network error. This is the same pass finished by a
fresh subagent of the same role (`BUILD.md` `### Recovery from interrupted
subagent runs`), not a "pass 2": no rename, no restart, nothing above this line
rewritten. **Already on disk when this subagent picked it up:** the preamble and
`Status: planned` line, `## Plan (Worker 1)`, `### Required-reading gap`, the
six-box `### Dispatched findings checklist` (all ticked), `### Instruments used`,
and `### Mutations recorded before they were made`. **Not on disk:** everything
from this heading down — the V1–V6 findings, the failability-proof subsection,
the severity grading, the DRY / existence assessment, the notes for Worker 1, and
the `Status:` transition.

Also on disk and inherited: nine files of measured evidence under
`docs/builder/temp-tests/043/` (three completed `prove_failability.py` runs with
their manifests, stdout, and generated report blocks). They are reused, not
repeated, per the recovery dispatch — they are this pass's own measurements,
taken by this role.

### Safety re-verification before any other action

The prior pass ran failability proofs, so an interrupted run could have left a
transient production mutation in the tree (`BUILD.md` `### Mutations are
transient`). Re-verified independently at the start of this pass:

- `find . -name 'ACTIVE-MUTATION.json' -not -path './.git/*'` -> **no output**;
  no live-mutation marker anywhere in the tree.
- `git diff --quiet HEAD -- <path>` per file, all five files under review:
  **CLEAN** for `django_strawberry_framework/testing/client.py`,
  `django_strawberry_framework/testing/__init__.py`,
  `django_strawberry_framework/conf.py`, `tests/testing/test_client.py`,
  `examples/fakeshop/test_query/test_client_api.py`.
- Corroborated by a second instrument rather than accepted on one:
  `git hash-object <path>` == `git rev-parse HEAD:<path>` for all five.
  `client.py` = `fdb81cab10e1357ff082a23f364fa483c1723134` in both.
- Third corroboration, behavioural: `uv run pytest -n0 tests/testing/test_client.py --no-cov`
  -> `41 passed`, byte-identical to the pre-mutation baseline recorded in all
  three proof reports. A live mutation would have moved that number.

No mutation was found, so no restore was needed, and this pass made none of its
own (see `### Failability proofs` below for why none was required).

### The spec was graded against HEAD, not the working tree

Cohort A is concurrently rewriting `docs/SPECS/spec-043-test_client-0_0_14.md`
and authoring its `-rationale.md`. Grading a contract against a half-rewritten
file produces findings no later pass can reproduce, so the spec was read from
`git show HEAD:docs/SPECS/spec-043-test_client-0_0_14.md` written to this
session's scratchpad (2317 lines). `git diff --quiet HEAD` confirms the
working-tree spec **is** dirty, which is exactly why the HEAD copy was used.
Every spec citation below is a HEAD citation. Neither Cohort A file was read in
its in-flight state and no message was sent to Cohort A.

## Review (Worker 3)

### V1 — did anything in the spec's Slice 1 checklist never land?

Walked every sub-check of the spec's `## Slice checklist` Slice 1 against source.
**Verdict: everything named landed. No absence. Two divergences, both additive
and both already owned by Cohort A's finding list.**

| Slice-1 sub-check | State | Citation |
| --- | --- | --- |
| `TESTING_ENDPOINT_KEY = "TESTING_ENDPOINT"` constant | present | `django_strawberry_framework/conf.py #"TESTING_ENDPOINT_KEY = \"TESTING_ENDPOINT\""` (conf.py:101) |
| `testing_endpoint_setting()` accessor, default `"/graphql/"` | present | `django_strawberry_framework/conf.py::testing_endpoint_setting` (conf.py:503-515) |
| package `Response` subclassing the engine `Response`, adding raw `response` | present | `django_strawberry_framework/testing/client.py::Response` (client.py:60-77) |
| `TestClient(BaseGraphQLTestClient)` with `__test__ = False` | present | `client.py::TestClient #"__test__ = False"` (client.py:106) |
| endpoint-resolving constructor `TestClient(path=None, client=None)` | present | `client.py::TestClient.__init__` (client.py:108-114) |
| **owned** `_build_body` | present | `client.py::TestClient._build_body` (client.py:245-311) |
| path-keyed file-map builder | present | `client.py::TestClient._build_body #"file_map = {key: [f\"variables.{key}\"] for key in files}"` (client.py:310) |
| `request(body, headers=None, files=None, *, url=None)`, JSON via `content_type`, multipart by omission, `url` defaults to `self.path` | present, exact signature | `client.py::TestClient.request` (client.py:216-243) |
| **owned** `query()` with `operation_name=` + per-call `url=`, returning package `Response` | present | `client.py::TestClient.query` (client.py:121-184) |
| `login(user)` context manager (`force_login` / `logout`) | present | `client.py::TestClient.login` (client.py:398-411) |
| `AsyncTestClient(TestClient)` with the `AsyncClient` default | present | `client.py::AsyncTestClient.__init__` (client.py:424-425) |
| async `query()` override | present | `client.py::AsyncTestClient.query` (client.py:432-459) |
| async `login()` | present | `client.py::AsyncTestClient.login` (client.py:461-472) |
| `GraphQLTestMixin` with `GRAPHQL_URL = None` | present | `client.py::GraphQLTestMixin #"GRAPHQL_URL: str | None = None"` (client.py:498) |
| mixin `.query(...)` delegating to a `TestClient` over `self.client` | present | `client.py::GraphQLTestMixin.query` (client.py:500-531) |
| `assertResponseNoErrors` / `assertResponseHasErrors` | present, both | `client.py::GraphQLTestMixin.assertResponseNoErrors` / `.assertResponseHasErrors` (client.py:533-552) |
| `GraphQLTestCase(GraphQLTestMixin, TestCase)` | present | `client.py::GraphQLTestCase` (client.py:555) |
| `GraphQLTransactionTestCase(GraphQLTestMixin, TransactionTestCase)` | present | `client.py::GraphQLTransactionTestCase` (client.py:559) |
| six `testing` root re-exports, `__all__` extended | present, all six | `django_strawberry_framework/testing/__init__.py #"__all__"` — `AsyncTestClient`, `GraphQLTestCase`, `GraphQLTestMixin`, `GraphQLTransactionTestCase`, `Response`, `TestClient` (plus the pre-existing `safe_wrap_connection_method`) |
| nothing re-exported from the **package root** | held | pinned by `tests/testing/test_client.py::test_export_surface_is_the_testing_root_not_the_package_root`; `git diff -- django_strawberry_framework/__init__.py` is empty |
| every new symbol carries a docstring | held | every class, method, and the module itself carry one; read directly, and `scripts/build_tree_md.py` would fail the render otherwise |
| `strawberry.test.BaseGraphQLTestClient` importable at the floor | held in substance | the module imports it at HEAD and the focused suite runs green; the spec's *number* for that floor is stale — see `### Notes for Worker 1`, item confirming F6 |
| `TODO(spec-043 Slice N)` anchors for staged seams | none needed | `grep -rn 'TODO(spec-043' .` returns nothing; no seam was staged |

**Divergences (both additive, neither an absence):** `conf.py` also carries
`testing_endpoint_setting.__test__ = False` (conf.py:524), unnamed in Slice 1 —
Cohort A's F4; and `client.py` carries `_finish_response`, the
`_safe_arg_repr` import, and `_assert_file_placeholders`' post-ship branches,
unnamed in Slice 1 — Cohort A's F3. Both are **shipped contract absent from spec
text**, not code absent from the tree.

One item worth recording for the next reader because it reads as a gap and is
not: the `__test__ = False` guard on `conf.py::testing_endpoint_setting` **is**
pinned by a test — `tests/base/test_conf.py #"assert testing_endpoint_setting.__test__ is False"`
(test_conf.py:317). F4 is a spec-text gap only; the code and its pin both exist.

### V2 — did anything in Slice 2 (the live-suite switchover) never land?

**Population stated before any result was read**, per `START.md`
`## Instruments that lie`. Derived from the directory listing, not from a
vocabulary guess, in a `uv run python - <<'PY'` heredoc with the count asserted:
`examples/fakeshop/test_query/*.py` = **27** files, of which **26** are
`test_*.py` and one is `conftest.py` (`assert len(files) == len(tests) + 1`).
The prior pass's 26 + 1 = 27 reading is re-derived here, not inherited.

Both polarities were swept. Searching only for helpers spelled `_graphql_data`
would miss `_post_graphql_as_staff`, so the sweep classified **every one of the
27 files** on four independent axes: `.post(` occurrence count, module-level
helper definitions matching `_*(graphql|query|post)*`, `graphql_client.py`
helper use, and `TestClient` / mixin use. Counts are occurrences, not matching
lines.

**Result: the switchover landed. `.post(` total = 16 occurrences across 9 files;
every other file drives either the shared `graphql_client.py` helpers or the
package `TestClient` family.** Files now driving `TestClient` /
`AsyncTestClient` / the mixin: `test_client_api.py`, `test_debug_extension_api.py`,
`test_debug_toolbar_api.py`, `test_kanban_mutations_api.py`, `test_keyset_api.py`,
`test_library_api.py`, `test_multi_db.py`, `test_mutation_atomicity.py`,
`test_optimizer_auto_api.py`, `test_products_api.py`,
`test_single_parent_fastpath_api.py`, `test_uploads_api.py`. No surviving
per-file `_graphql_data`-shaped POST-and-decode helper was found in any file that
also uses the client.

**The sub-check that did NOT fully land is the exemption comment.** The spec
requires that every retained raw `client.post(...)` carry "a one-line comment
naming this exemption". Classifying all 16 sites:

| File | sites | exemption declared? | honest exemption? |
| --- | --- | --- | --- |
| `test_products_api.py` | 3 | **yes**, inline at each site (`# Raw-multipart exemption (spec-043)`) | yes — hand-built `{operations, map, "0"}` envelope with an arbitrary file label, a wire shape the path-keyed builder never emits |
| `test_transport_api.py` | 2 | **yes**, module docstring (`the documented raw-envelope exemption in README.md`) | yes — exact byte bodies, hostile `Host`, `secure=`, `enforce_csrf_checks=`, body-cap probes |
| `test_auth_api.py` | 1 | **yes**, test docstring (`the documented raw-envelope exemption`) | yes — `enforce_csrf_checks=True`, the subject is the request envelope |
| `test_list_field_async_api.py` | 1 | **partly** — the module docstring declares the *sync-helper* exemption (`intentionally exempt from graphql_client.py: that helper is synchronous`), not the spec-043 raw-post exemption | honest in substance (ad-hoc async mount via `_CURRENT["schema"]` + `ROOT_URLCONF=__name__`) |
| `test_error_policy_api.py` | 2 | **no** | honest in substance — ad-hoc probe mounts; one is a sync/async transport-parity comparison |
| `test_products_visibility_api.py` | 4 | **no** (1-line module docstring, no declaration anywhere) | honest in substance — ad-hoc `_CURRENT["schema"]` mounts under `ROOT_URLCONF=__name__` |
| `test_relations_async_api.py` | 1 | **no** | honest in substance — ad-hoc async mount |
| `test_resource_policy_api.py` | 2 | **no** | honest in substance — one hand-built multipart envelope, one async-mount parity comparison |

**Nine of the sixteen sites carry no exemption declaration in any form** (2 + 4 +
1 + 2), and a tenth declares a different exemption. All ten are *substantively*
within the exemption class the spec names — "the `test_multi_db.py` custom-view
plumbing" — so **none is an unconverted file**; what is missing is the written
declaration the spec's Slice-2 sub-check requires and that
`examples/fakeshop/test_query/README.md` #"Exemptions stated in the exempt
module's docstring, never inferred" independently demands. Graded **Medium** and
escalated: the five files involved are outside **every** cohort's declared write
set in `build-043-test_client-0_0_14.md` `## Ownership partition`, so no worker
in this cycle can close it (see `### Notes for Worker 1`).

The Slice-2 `CaptureQueriesContext` sub-check is satisfied by construction: the
client is transport-only and no query-count block moved (no such file is dirty
against HEAD).

### V3 — is the per-call `url=` non-persistence contract actually held?

**Held.** `self.path` is assigned in exactly one place in the whole module —
`client.py::TestClient.__init__ #"self.path = resolved"` (client.py:110). A
whole-module grep for `self.path` returns four hits: that assignment, two
docstring mentions, and the read at
`client.py::TestClient.request #"url if url is not None else self.path"`
(client.py:243). Nothing else writes it, and `self.url` (the base's attribute,
set once through `super().__init__`) is likewise never re-written per call. The
per-call override therefore cannot persist: `query()` forwards `url=url` to
`request()` (client.py:183 sync, client.py:458 async), and `request()` selects
the target as a local expression.

Pinned by `tests/testing/test_client.py::test_per_call_url_outranks_the_constructor_and_never_persists`,
which asserts the override routed, `client.path` unchanged afterwards, and the
next un-overridden call falling back — the full non-persistence claim.

**But that row cannot detect a defect in the transport seam it appears to
cover**, and this is a finding. It drives `_RecordingTestClient`, which
**overrides `request()` itself** (test_client.py:68-77) and reimplements the
production expression verbatim: `self.seen_urls.append(url if url is not None else self.path)`.
The double re-spells the very line under test, so `TestClient.request`'s own
selection is never executed. Mechanically confirmed, not argued: proof entry 12
(`docs/builder/temp-tests/043/proofs.json`) deletes the `url` term from
`TestClient.request` and this row **does not fail** — only one unrelated row
does. Graded Medium (see `### Medium`).

### V4 — is every branch F3 introduced actually pinned by a test?

Six behaviour families, each traced to the node ids that fail when the branch is
removed. Node ids are **listed**, not counted; the counts are `len()` of the
lists and come from the on-disk proofs at the scope recorded there.

1. **`_finish_response` extracted** (`8bac47be`). Not a boundary — a relocation.
   Pinned indirectly and in both colors: sync by every `tests/testing/test_client.py`
   row that reads `res.data` / `res.extensions` (e.g.
   `test_response_extensions_surface_decoded_or_none`), async by
   `examples/fakeshop/test_query/test_client_api.py::test_async_query_happy_path_and_raise_direction`.
   The `assert_no_errors` raise inside it is pinned live by that same async row and
   by `test_client_api.py::test_assert_no_errors_default_raises_with_the_errors_list`.
   **Pinned.**
2. **Falsy consumer-supplied client honored** (`f7fbead4`). Pinned by
   `tests/testing/test_client.py::test_clients_preserve_an_explicit_falsy_transport[TestClient]`
   and `...[AsyncTestClient]`. Sync boundary: 2 rows. Async boundary: **1 row**
   (only the `[AsyncTestClient]` param), because the sync mutation is upstream of
   both params while the async one is not. **Pinned sync; weakly pinned async** —
   see boundary 11.
3. **Diagnostics render through `_safe_arg_repr`** (`f7fbead4`). Pinned for the
   *leaf value* by
   `tests/testing/test_client.py::test_files_placeholder_hostile_repr_keeps_assertion_error_boundary`
   and, for the hostile-`__len__` sibling class, by
   `test_files_placeholder_hostile_len_container_fails_closed[list|tuple]`.
   **Not pinned for the `key` argument**: every `_safe_arg_repr(key)` call site is
   *executed* by the guard rows, but no row supplies a `files=` key whose own
   `__repr__` is hostile (a `str` subclass), so the containment property is pinned
   on one of two argument positions. Graded **Low** — the key is a `str` in every
   realistic call, so the unpinned half is a narrow shape. Recorded rather than
   waved through.
4. **Tuple variables walked as arrays** (`a8f31a2d`). Pinned by
   `test_files_placeholder_tuple_arrays_walk_and_map_like_lists` and
   `test_files_placeholder_hostile_len_container_fails_closed[tuple]` — 2 rows.
   **Pinned.**
5. **Empty-dotted-segment guard and unreadable-`__len__` guard** (`a8f31a2d`).
   Empty segment: 3 rows
   (`test_files_placeholder_empty_segment_raises_instead_of_emitting[variables0-]`,
   `[variables1-data.]`, `[variables2-data..image]`). Unreadable length: 2 rows
   (`test_files_placeholder_hostile_len_container_fails_closed[list]`, `[tuple]`).
   **Both pinned.**
6. **Canonical object-path index validation** (`b4d0c8ae`). 7 rows —
   `test_files_placeholder_noncanonical_list_index_raises` at six parameters
   (`x`, `\xb2`, `٣`, `01`, `-1`, and the 5000-digit decimal) plus
   `test_files_placeholder_out_of_range_list_index_raises`. The only boundary in
   the module **outside** Worker 3's mandatory re-run floor. **Pinned, strongly.**

**Verdict: all six families have a test owner. Two have owners too thin to
count** (family 2's async half, and family 3's key-argument half), and they are
carried as findings rather than as passes.

### V5 — does the mixin delegate's endpoint resolution match Decision 7's ladder?

**The five-rung ladder holds end to end; no rung is short-circuited.** Traced by
control flow, not by prose:

- **Rung 1, per-call.** `GraphQLTestMixin.query` forwards `url=url` unchanged
  (client.py:530) into `TestClient.query`, which forwards it into
  `request(..., url=url)` (client.py:183), which selects
  `url if url is not None else self.path` (client.py:243). Nothing between
  short-circuits it.
- **Rung 2, constructor.** `TestClient.__init__ #"path if path is not None else testing_endpoint_setting()"`
  (client.py:109).
- **Rung 3, class attr.** `GraphQLTestMixin.query #"TestClient(self.GRAPHQL_URL, client=self.client)"`
  (client.py:522) passes `GRAPHQL_URL` **as** the constructor's `path`. Worth
  naming for the next reader: through the mixin, rungs 2 and 3 are the *same
  parameter*, so the ladder is five rungs of precedence implemented by four
  mechanisms. `GRAPHQL_URL = None` (the default) therefore falls through
  `is not None` to the next rung exactly as Decision 7 requires — confirmed, that
  is what happens.
- **Rungs 4 and 5, settings then default.**
  `conf.py::testing_endpoint_setting #"return getattr(settings, TESTING_ENDPOINT_KEY, \"/graphql/\")"`
  (conf.py:515). Read at **construction**, and the mixin constructs its delegate
  per call, so an `override_settings` block observed mid-class is honored —
  pinned by `test_mixin_endpoint_rungs_class_attr_settings_and_per_call` and by
  `test_settings_key_sets_the_endpoint_and_the_default_restores_after_override`.

The delegate also honors the test case's own transport: it passes
`client=self.client`, and since `f7fbead4` that selection is presence-based, so a
case whose `self.client` is falsy is not silently swapped for a fresh one with a
different session.

**The defect V5 surfaces is in the live rows that claim to prove the ladder, not
in the ladder.** See the `### Medium` finding on the transparent probe endpoint.

### V6 — is there any fail-open shape in the module?

Hunted every shape `BUILD.md` `### Fail-open shapes` names, across the whole
module rather than a diff. **No fail-open shape survives on a decision path. No
High finding.** Per shape:

- **Broad `except` around a check** — `client.py::TestClient._assert_file_placeholders #"except Exception as exc:"`
  (client.py:358). The build plan asks explicitly which direction this converts.
  **It converts "the check blew up" into a REJECTION, not into a pass**: the
  handler's only statement is `raise AssertionError(...) from exc`, and control
  cannot reach `current = current[index]` from it. It is a containment, not a
  swallow — it stops a hostile `__len__` from *replacing* the uniform guard type
  with its own exception, which is a strictly stronger boundary than letting the
  raw error escape. Pinned by 2 rows and by the two extra assertions inside them
  (`assert not isinstance(excinfo.value, _HostileLen)`, `assert "hostile __len__" not in str(...)`).
  The sibling `except ValueError: index = None` (client.py:354-355) likewise
  routes into the rejection at client.py:368, never past it.
- **`or` fallback on a legitimately-falsy left operand** — the class that
  produced F3 item 2. **No sibling survives.** All three selections in the module
  are presence-based: `path if path is not None else ...` (client.py:109),
  `client if client is not None else Client()` (client.py:114),
  `client if client is not None else AsyncClient()` (client.py:425),
  `url if url is not None else self.path` (client.py:243). Swept the module for
  bare `or`-fallback assignments: none remain.
- **Clamps** (`max`/`min` on a decision value) — none in the module.
- **`getattr` default for a meaningful absence** — one:
  `conf.py::testing_endpoint_setting #"getattr(settings, TESTING_ENDPOINT_KEY, \"/graphql/\")"`.
  Absence here is *meaningful and its meaning is the default* (rung 5 of the
  documented ladder), so it is a documented default, not a fail-open. One residue
  recorded as **Low**: the accessor returns whatever the key holds with no type
  check, so a non-`str` value (`TESTING_ENDPOINT: None`) reaches
  `client.post(None, ...)` rather than the "ordinary 404 at request time" the
  accessor's own docstring promises.
- **Truthiness where absent and empty differ** — three sites, all deliberate and
  all documented in the code itself: `if not files` (client.py:240 and 282) and
  `type="multipart" if files else "json"` (client.py:202) make `files={}` a plain
  JSON post, pinned by `test_empty_files_dict_is_a_plain_json_post`; `if not variables`
  (client.py:285) rejects `{}` and `None` alike; `if variables:` (client.py:276)
  omits an empty `variables` key. Each is the spec's stated contract
  (`## Error shapes`, HEAD), each is the *stricter* direction, and none converts
  "cannot determine" into "permit". **Not findings** — but see the `### Medium`
  entry on `if not variables:`, whose problem is failability, not direction.
- **Default reached because input was incoherent** — `Response.response: Any = None`
  (client.py:77). The clients always populate it, and the docstring says so, but a
  `Response` constructed without it makes
  `assertResponseNoErrors` raise `AttributeError` on `resp.response.status_code`
  rather than a readable assertion. **Low.**

### Failability proofs

Assembled from the three completed `prove_failability.py` runs on disk. Recorded
per boundary, as `BUILD.md` `### What gets recorded` requires: symbol-qualified
boundary, exact mutation, failing node ids **listed**, focused scope as run,
collection/setup errors separately, pre-mutation state of that same scope, and
the revert proved by byte comparison.

**Procedure and its guarantees.** `scripts/prove_failability.py` copies the
target to a scratch path **outside** the repository before any mutation; locates
the mutation site by an anchor asserted to match **exactly once** (any other count
aborts the entry having written nothing — which is also what makes a pre-existing
live mutation impossible to stack on); runs the same focused scope **unmutated
first** so pre-existing failures are differenced out; reads both runs' pytest
exit codes so a run that collected nothing cannot be recorded as a measured zero;
restores from the pre-mutation copy in a `finally`; and proves the restore by
`filecmp.cmp(shallow=False)` plus SHA-256. One boundary at a time, restored before
the next. `git` is never invoked.

**Every restore proved.** All fifteen entries across the three runs report
`filecmp.cmp(shallow=False) True` and `sha256 e40ea98a9b352eac... == e40ea98a9b352eac...`
against the pre-mutation copy — the same digest in every entry, which is itself
the cross-entry evidence that no entry started from a mutated file. Independently
re-confirmed at the start of this pass by the three-instrument check in
`### Safety re-verification` above.

**Every entry's collection / setup error count is 0**, and every entry's
pre-mutation state is a recorded green run of the identical scope (41 passed at
package scope, 67 at package+live, 52 at the mixin scope), so no count is
inflated by a pre-existing failure.

**Where the second pair of eyes landed.** This cohort has no Worker 2 and no
builder record to audit: it is a post-ship verification cohort, so **every one of
the fifteen measurements below is Worker 3's own**, taken by this role with the
mechanized loop, at the scopes stated. Worker 3's mandatory re-run floor
(`worker-3.md`, boundaries at 3 rows or fewer) is therefore met by construction
for all fourteen in-floor boundaries; the one boundary above the floor (the
canonical index validation, 7 rows) was measured too. No boundary was accepted on
somebody else's record. This pass made **no new mutation**: the two findings it
adds beyond the prior measurements are provable without one (one from a read-only
call into the walker, one already decided by the wide-scope run below).

#### Run A — package-tier scope, 12 boundaries

Scope as run, identical for all twelve:
`uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/testing/test_client.py`.
Pre-mutation state of that scope: `41 passed`, exit 0, 0 pre-existing failing rows.
Manifest `docs/builder/temp-tests/043/proofs.json`; stdout `proofs-stdout.txt`.

| # | Boundary | Mutation applied | Rows | Errors | Failing node ids |
| --- | --- | --- | --- | --- | --- |
| 1 | `client.py::TestClient._build_body #"if not variables:"` | `if not variables:` -> `if False:` | **0** | 0 | *(none)* |
| 2 | `client.py::TestClient._build_body #"if reserved:"` | `if reserved:` -> `if False:` | **1** | 0 | `tests/testing/test_client.py::test_files_key_shadowing_a_reserved_envelope_field_raises` |
| 3 | `client.py::TestClient._assert_file_placeholders #"if not segment:"` | `if not segment:` -> `if False:` | 3 | 0 | `...::test_files_placeholder_empty_segment_raises_instead_of_emitting[variables0-]`; `[variables1-data.]`; `[variables2-data..image]` |
| 4 | `client.py::TestClient._assert_file_placeholders #"is not a valid index into a"` | the whole `if index is None or index < 0 or str(index) != segment or index >= size:` -> `if False:` | 7 | 0 | `...::test_files_placeholder_noncanonical_list_index_raises[x]`, `[\xb2]`, `[٣]`, `[01]`, `[-1]`, `[1*5000]`; `...::test_files_placeholder_out_of_range_list_index_raises` |
| 5 | `client.py::TestClient._assert_file_placeholders #"unreadable length"` | the `try/except` around `len(current)` deleted, `len()` called bare | 2 | 0 | `...::test_files_placeholder_hostile_len_container_fails_closed[list]`; `[tuple]` |
| 6 | `client.py::TestClient._assert_file_placeholders #"is not a dict or list"` | the `raise AssertionError(...)` replaced by `current = None` | **1** | 0 | `...::test_files_placeholder_cannot_descend_into_a_scalar_raises` |
| 7 | `client.py::TestClient._assert_file_placeholders #"if segment not in current:"` | `if segment not in current:` -> `if False:` | 2 | 0 | `...::test_files_placeholder_missing_top_level_path_raises`; `...::test_files_placeholder_missing_nested_key_raises` |
| 8 | `client.py::TestClient._assert_file_placeholders #"if current is not None:"` | `if current is not None:` -> `if False:` | 2 | 0 | `...::test_files_placeholder_present_but_not_none_raises`; `...::test_files_placeholder_hostile_repr_keeps_assertion_error_boundary` |
| 9 | `client.py::TestClient._assert_file_placeholders #"isinstance(current, (list, tuple))"` | `(list, tuple)` -> `list` (the pre-`a8f31a2d` shape) | 2 | 0 | `...::test_files_placeholder_tuple_arrays_walk_and_map_like_lists`; `...::test_files_placeholder_hostile_len_container_fails_closed[tuple]` |
| 10 | `client.py::TestClient.__init__ #"client if client is not None else Client()"` | -> `client or Client()` (the pre-`f7fbead4` shape) | 2 | 0 | `...::test_clients_preserve_an_explicit_falsy_transport[TestClient]`; `[AsyncTestClient]` |
| 11 | `client.py::AsyncTestClient.__init__ #"client if client is not None else AsyncClient()"` | -> `client or AsyncClient()` | **1** | 0 | `...::test_clients_preserve_an_explicit_falsy_transport[AsyncTestClient]` |
| 12 | `client.py::TestClient.request #"url if url is not None else self.path"` | -> `self.client.post(self.path, **kwargs)` | **1** | 0 | `...::test_mixin_endpoint_rungs_class_attr_settings_and_per_call` |

#### Run B — package+live scope, 2 boundaries re-measured

Scope as run:
`uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/testing/test_client.py examples/fakeshop/test_query/test_client_api.py examples/fakeshop/test_query/test_uploads_api.py`.
Pre-mutation: `67 passed`, exit 0, 0 pre-existing failing rows. Manifest
`proofs-wide.json`; report `proofs-wide-report.md`.

| # | Boundary | Mutation | Rows | Errors | Failing node ids |
| --- | --- | --- | --- | --- | --- |
| B1 | `client.py::TestClient._build_body #"if not variables:"` | `if not variables:` -> `if False:` | **0** | 0 | *(none)* |
| B2 | `client.py::TestClient.request #"url if url is not None else self.path"` | -> `self.client.post(self.path, **kwargs)` | **1** | 0 | `tests/testing/test_client.py::test_mixin_endpoint_rungs_class_attr_settings_and_per_call` |

**B2 is the load-bearing measurement of this pass.** Widening the scope to
include the live tier — where
`test_client_api.py::GraphQLTestCaseEndToEndTests::test_per_call_url_routes_to_the_probe_endpoint`
lives, the row *named* for rung 1 — added **zero** failing rows. The live row
passes with the per-call `url=` deleted from the transport.

#### Run C — the mixin's `GRAPHQL_URL` rung, 1 boundary

Scope as run:
`uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/testing/test_client.py examples/fakeshop/test_query/test_client_api.py`.
Pre-mutation: `52 passed`, exit 0, 0 pre-existing failing rows. Manifest
`proofs-mixin.json`; report `proofs-mixin-report.md`.

| # | Boundary | Mutation | Rows | Errors | Failing node ids |
| --- | --- | --- | --- | --- | --- |
| C1 | `client.py::GraphQLTestMixin.query #"TestClient(self.GRAPHQL_URL, client=self.client)"` | -> `TestClient(None, client=self.client)` (rung 3 dropped) | **1** | 0 | `tests/testing/test_client.py::test_mixin_endpoint_rungs_class_attr_settings_and_per_call` |

Same shape as B2: `test_client_api.py::GraphQLTestCaseClassAttrEndpointTests::test_class_attr_endpoint_hits_the_real_view`,
the row *named* for rung 3, was in scope and **did not fail**.

#### `why 0` — the judgement the tool cannot make, filled in

Two zero-row entries, A1 and B1, the same boundary at two scopes. The generated
reports emitted `why 0: <fill in ...>` placeholders for both. **Both are
WEAKLY PINNED, not harness-impossible**, and the evidence is direct rather than
inferred:

- **A1 / B1 — `client.py::TestClient._build_body #"if not variables:"` — weakly
  pinned.** The row that exists,
  `tests/testing/test_client.py::test_files_without_variables_raises_the_placeholder_guard`,
  is **non-distinguishing** on two counts. First, its assertion is
  `pytest.raises(AssertionError, match="placeholder")`, and *every* sibling guard
  in the walker also says "placeholder". Second, it puts both cases (`variables=None`
  and `variables={}`) in one function body, so it is **one node id**, not two
  (`START.md`: a loop or a repeated block inside one test is one row).
  Demonstrated read-only, with no mutation, by calling the walker directly with
  exactly the inputs the guard intercepts first:

  ```
  TestClient._assert_file_placeholders(None, {"file": object()})
    -> AssertionError: files= path 'file' has no matching placeholder in variables:
       cannot descend into 'file' (the value there is not a dict or list).
  TestClient._assert_file_placeholders({},   {"file": object()})
    -> AssertionError: files= path 'file' has no matching placeholder in variables:
       no key 'file' at that level.
  ```

  Both contain `placeholder`; so does the guard's own message. **The harness can
  exhibit the failure perfectly well** — a `match="requires variables="`
  assertion fails the moment the guard is removed — so this is not a
  harness-impossible interleaving and the remedy is emphatically *not* a
  production-call-site invariant assertion. It is more and better-targeted rows.

#### Acceptance verdict on every weakly pinned boundary

`BUILD.md` `### Acceptance rule`: 0 or 1 failing rows is weakly pinned and is
`revision-needed`. The fix is more or better-targeted rows — never a weaker
boundary, and never a recorded exception. **Five boundaries** (six entries; A1
and B1 are one boundary measured twice) fall under the rule. The additional rows
each requires, named:

1. **A1/B1 — `_build_body #"if not variables:"` (0 rows).** Split
   `test_files_without_variables_raises_the_placeholder_guard` into a
   `@pytest.mark.parametrize` over `variables=None` and `variables={}` — **two**
   node ids instead of one — and change the assertion to
   `match="requires variables="`, the guard's own distinctive phrase, which no
   sibling guard emits. Add a third row asserting the *async* color raises the
   same guard (`AsyncTestClient(...).query(..., files=...)` with no variables),
   since `_build_body` is shared but only the sync color is currently exercised
   here. Target: 3 rows.
2. **A2 — `_build_body #"if reserved:"` (1 row).** `test_files_key_shadowing_a_reserved_envelope_field_raises`
   is a `for reserved in ("operations", "map")` loop inside one test — one node
   id for two cases. Parametrize it (2 rows) and add a third for both reserved
   names supplied together, which also pins the `sorted(reserved)` rendering in
   the message. Target: 3 rows.
3. **A6 — `_assert_file_placeholders #"is not a dict or list"` (1 row).**
   Parametrize `test_files_placeholder_cannot_descend_into_a_scalar_raises` over
   the non-descendable mid-path shapes — a `str`, an `int`, a `None` — and add one
   row for a non-descendable value at a *nested* depth rather than the first
   segment, so the rejection is pinned inside the loop and not only on its first
   iteration. Target: 4 rows.
4. **A11 — `AsyncTestClient.__init__ #"client if client is not None else AsyncClient()"` (1 row).**
   The async half of `test_clients_preserve_an_explicit_falsy_transport` is the
   only row; the sync mutation kills both params only because it sits upstream.
   Add a row asserting `AsyncTestClient()` with no argument constructs a
   `django.test.AsyncClient` (not a sync `Client`), and a row driving one real
   `await client.query(...)` through an explicitly-supplied falsy async transport,
   so the selection is pinned behaviourally and not only by identity. Target: 3 rows.
5. **A12 / B2 — `TestClient.request #"url if url is not None else self.path"` (1 row
   at both scopes).** Two independent causes, both needing a fix:
   - `test_per_call_url_outranks_the_constructor_and_never_persists` drives
     `_RecordingTestClient`, which **overrides `request()`** and re-spells the
     expression under test. Re-point it at a `_RecordingDjangoClient` supplied as
     `client=` — the shape `test_empty_files_dict_is_a_plain_json_post` already
     uses — so the real `request()` executes and the recorded target is the one
     the production line chose. That alone converts a non-failing row into a
     failing one.
   - The live row is discussed in the Medium finding below; fixing the probe
     endpoint adds a second row.
   Target: 3 rows.
6. **C1 — `GraphQLTestMixin.query #"TestClient(self.GRAPHQL_URL, client=self.client)"` (1 row).**
   `test_mixin_endpoint_rungs_class_attr_settings_and_per_call` proves rungs 1, 3
   and 4 inside **one** function — one node id for three contracts, so any one of
   them failing is indistinguishable from the other two. Split it into three rows
   (one per rung), which by itself lifts this boundary to 1 distinct row and
   boundary A12 to 1, then add the live fix below. Target: 2 rows for C1.

None of these six fixes weakens a boundary, and none is recorded as an
exception.

### High:

None.

No production-source defect was found. Every finding below is a test-tier or
spec-text defect; the shipped `testing/client.py` holds the contract the spec
states at HEAD, on every question V1–V6 asked.

### Medium:

**M1 — the live endpoint-rung rows are structurally incapable of failing: the
probe endpoint is a transparent alias of the default one.**
Source: `examples/fakeshop/test_query/test_client_api.py::_alt_graphql_view`
(test_client_api.py:60-67) and `#"urlpatterns = [path(\"\", include(\"config.urls\")), path(\"alt/\", _alt_graphql_view)]"`
(test_client_api.py:70).
`_alt_graphql_view` resolves `/graphql/` at request time and delegates to it, so
a request that lands on `/alt/` and a request that lands on `/graphql/` produce
**identical** responses. The two rows that exist to prove endpoint selection —
`GraphQLTestCaseEndToEndTests::test_per_call_url_routes_to_the_probe_endpoint`
(rung 1) and `GraphQLTestCaseClassAttrEndpointTests::test_class_attr_endpoint_hits_the_real_view`
(rung 3) — assert a successful query, which succeeds whether or not the routing
they name actually happened. This is `START.md`'s "control that cannot fail":
the probe was deliberately built to give a *positive hit* rather than an
exception shape, and that design also removed the only signal distinguishing the
rung from the fallback.
**Not argued — measured.** Run B (scope including `test_client_api.py`) deleted
the per-call `url` term and the rung-1 live row passed; Run C dropped the
`GRAPHQL_URL` rung and the rung-3 live row passed. Both mutants were caught only
by one package-tier row.
Why it matters: rungs 1 and 3 of Decision 7's ladder have no live pin at all, and
the artifact of record for the live tier claims they are "proven by a POSITIVE hit
on the real schema view".
Recommended change: make `/alt/` **observably distinct** from `/graphql/` while
still serving the real schema — e.g. have `_alt_graphql_view` stamp a marker
header on the delegated response and have both rows assert
`res.response.headers[...]`, so a request that fell back to `/graphql/` fails.
Do not weaken to an exception-shape probe; keep the positive hit and add the
discriminator.
Test expectation: with the per-call `url=` removed from `TestClient.request`,
`test_per_call_url_routes_to_the_probe_endpoint` must FAIL; with
`TestClient(self.GRAPHQL_URL, ...)` reduced to `TestClient(None, ...)`,
`test_class_attr_endpoint_hits_the_real_view` must FAIL.

**M2 — five weakly pinned boundaries.** Enumerated with their required
additional rows in `#### Acceptance verdict on every weakly pinned boundary`
above. `BUILD.md` `### Acceptance rule` makes each of these `revision-needed` on
its own; collectively they are the reason this artifact does not return
`review-accepted`. Source: `django_strawberry_framework/testing/client.py` (the
boundaries) and `tests/testing/test_client.py` (the rows that must be added).
Why it matters: three of the five rest on a single assertion inside a single
node id, and one (the empty-`variables` guard) is pinned by **nothing** — the
suite cannot currently tell whether that guard exists. Each is one refactor or
one `match=` reword away from silent retirement.

**M3 — `_RecordingTestClient` re-implements the production line it is used to
test.** Source: `tests/testing/test_client.py::_RecordingTestClient.request`
(test_client.py:68-77), specifically
`#"self.seen_urls.append(url if url is not None else self.path)"` — a verbatim
copy of `client.py::TestClient.request #"url if url is not None else self.path"`
(client.py:243). A double that overrides the seam under test and re-spells its
logic cannot detect a change to that logic; it pins only that `query()` forwards
`url=` and that `self.path` is not mutated. Both DRY defect and failability
defect. Recommended change: as in acceptance item 5 — supply a recording
`client=` transport instead of overriding `request()`. The recording *Django
client* shape (`_RecordingDjangoClient`, test_client.py:80-88) is already in the
file and is the correct seam; `_RecordingTestClient` may then be deletable
entirely, which would be the better outcome (see `### DRY and existence
findings`).

**M4 — nine retained raw `client.post(...)` sites carry no exemption
declaration.** Source: `examples/fakeshop/test_query/test_error_policy_api.py`
(2 sites), `test_products_visibility_api.py` (4),
`test_relations_async_api.py` (1), `test_resource_policy_api.py` (2); plus
`test_list_field_async_api.py` (1) declaring a different exemption. Population and
classification in V2 above. The spec's Slice-2 sub-check requires "a one-line
comment naming this exemption" on every retained raw post, and
`examples/fakeshop/test_query/README.md` #"Exemptions stated in the exempt
module's docstring, never inferred" says the same thing independently. All ten
are honest exemptions in substance (ad-hoc `_CURRENT["schema"]` mounts and
hand-built multipart envelopes — the "custom-view plumbing" class the spec names),
so **no file is unconverted**; what is missing is the written declaration.
`BUILD.md` `## Severity definitions` grades a silently-unaddressed spec-slice
sub-check Medium.
**Ownership gap, stated plainly:** none of these five files appears in any
cohort's write set in `build-043-test_client-0_0_14.md` `## Ownership partition`,
so no worker in this cycle can close M4 without a re-partition. Escalated in
`### Notes for Worker 1`.

### Low:

**L1 — `_safe_arg_repr` containment is pinned for the value argument, not the key
argument.** Source: `client.py::TestClient._assert_file_placeholders` — every
`_safe_arg_repr(key)` call site (client.py:343, 364, 370, 378, 388, 394). The
hostile-`__repr__` row supplies the hostile object as a *variables value*; no row
supplies a `files=` key (a `str` subclass) whose `__repr__` raises. The call sites
execute, so the shape is exercised; the containment property is not pinned on that
argument position. Recommended change: one row with a `str` subclass key carrying
an exploding `__repr__`, asserting the guard's `AssertionError` still surfaces.

**L2 — `conf.py::testing_endpoint_setting` returns an unvalidated value.**
Source: `conf.py #"return getattr(settings, TESTING_ENDPOINT_KEY, \"/graphql/\")"`
(conf.py:515). Its own docstring promises that a wrong endpoint "surfaces as an
ordinary 404 at request time, where the failure names the actual response" — true
for a wrong *string*, false for a non-string: `TESTING_ENDPOINT: None` reaches
`client.post(None, ...)` and fails with something that names neither the setting
nor the endpoint. Not a fail-open (nothing is permitted that should be refused),
so Low. Either narrow the docstring's claim to "a wrong endpoint *string*", or
reject a non-`str` at the accessor. This is a **contract-level** choice (the
package's validation posture is "validation stays at the consumer", per Decision
7), so it is escalated rather than prescribed.

**L3 — `Response.response` defaults to `None` for a field the clients always
populate.** Source: `client.py::Response #"response: Any = None"` (client.py:77).
The docstring already says the default "is never observed in practice". A
`Response` built without it makes `assertResponseNoErrors` raise `AttributeError`
on `resp.response.status_code` rather than a readable assertion. The default is
load-bearing for dataclass field ordering against the engine base, so this is a
note, not a change request — recorded so a later reader does not re-derive it.

### DRY and existence findings

**Is `_finish_response` the right seam? Yes — keep it.**
`client.py::TestClient._finish_response` (client.py:186-214) owns the decode ->
`Response` construction -> `assert_no_errors` raise tail. It has exactly two
callers, `TestClient.query` (client.py:184) and `AsyncTestClient.query`
(client.py:459), and they are **genuinely different colors**: only
`request()` is sync/async-colored, so the async twin cannot call
`super().query()` and the tail is the largest sync-safe remainder. The extraction
is factored *below* Decision 5's not-calling-`super().query()` choice rather than
around it, which is the correct altitude — the alternative (async awaiting a sync
`query()`) does not exist, and the pre-`8bac47be` shape was a verbatim duplicate
of 13 lines. Existence challenge answered: it should exist; deleting it restores
a literal near-copy across two methods that must stay behaviourally identical.

**Is the placeholder walker the right shape? Yes — but one guard beside it is now
redundant.** `client.py::TestClient._assert_file_placeholders` is the only thing
that makes the path-keyed `files=` contract (Decision 9) enforceable: the client,
not the server, owns the multipart `map`, so the client must prove each path
resolves to a placeholder before emitting one. A single static method walking the
same closed shape set `json.dumps` serializes (dict -> object, list/tuple ->
array) is the right shape; the five rejection branches are five distinct
malformed-call classes, not a branchy accretion, and six of the eight strongest
pins in this module are on it.

**Existence challenge, raised and escalated (not acted on):
`client.py::TestClient._build_body #"if not variables:"` is fully subsumed by the
walker.** Demonstrated read-only above: for `variables=None` and for
`variables={}` — the only two inputs the guard intercepts — the walker *alone*
rejects, with an `AssertionError` whose message also contains "placeholder". So
the guard changes no verdict; it changes only the message. That has two possible
resolutions and **which one is right is a contract-level question, not a worker's
call** (`worker-3.md` `### The existence challenge`):

- **Keep and pin it.** The guard's message —
  `"query(..., files=...) requires variables= carrying a None placeholder at each file's variable path"` —
  names the *call-level* mistake, while the walker's message names a *path-level*
  one, and the spec's `## Error shapes` documents the call-level wording. Then
  acceptance item 1 applies: parametrize and match the distinctive phrase.
- **Delete it and let the walker own every rejection.** Removes a guard whose
  only effect is a better message, at the cost of that message and of the spec's
  `## Error shapes` text.

**Recommendation: keep and pin.** Deleting a guard in response to a
weakly-pinned finding is the shape `BUILD.md` `### Acceptance rule` forbids
("never a weaker boundary"), and the message is a documented contract. But the
redundancy is real and is escalated so the maintainer, not this cohort, settles
it.

**Should any of this exist at all? Yes.** The module is shipped, consumed by
twelve live-tier files and the whole of `test_uploads_api.py` /
`test_client_api.py`, re-exported under a stable path, and documented in
`docs/README.md` and `docs/GLOSSARY.md`. Its largest abstraction
(the walker) has one caller but that caller is the package's only emitter of a
multipart `map`, and inlining 60 lines of five-branch validation into
`_build_body` would make the builder unreadable without removing a line of logic.
No deletion candidate found in production source.

**One deletion candidate found in test source:**
`tests/testing/test_client.py::_RecordingTestClient`. If M3's fix lands — the
per-call-`url` rows re-pointed at a recording `client=` transport — the class has
no remaining caller, and the file already carries the better-shaped
`_RecordingDjangoClient`. Two recording doubles for one seam is the duplication;
deleting the one that overrides production logic is the fix.

### Temp-test verification

No temp test was written this pass. The two behavioural claims this pass adds
beyond the inherited proofs were both settled without one: the probe-endpoint
finding (M1) is decided by Run B / Run C, which are mutation measurements already
on disk, and the guard-redundancy finding is decided by a read-only call into
`TestClient._assert_file_placeholders` with no mutation and no file written.
Scratch under `docs/builder/temp-tests/043/` holds only the nine
`prove_failability.py` artifacts; nothing there is importable by the real suite.

### Static helper use

`scripts/review_inspect.py django_strawberry_framework/testing/client.py
--output-dir <session scratchpad>/inspect` was run (recorded in `### Instruments
used` above), exit 0, both outputs written. `--output-dir` pointed at the session
scratchpad, never `docs/shadow` — `AGENTS.md` rule 23 over `BUILD.md`
`### How to run`, the reconciliation the build plan records. Shadow line numbers
are not cited anywhere in this artifact; every citation is symbol-qualified, with
`path:NN` added only as a per-cycle-artifact convenience (`AGENTS.md` rule 27's
carve-out for `docs/builder/bld-*.md`).

`BUILD.md` `### When to run the helper during build` does not in fact require it
for this cohort — the cohort writes no `.py` file and there is no diff — so the
run was supererogatory and its output is corroboration, not evidence.

### Public-surface and CHANGELOG checks

- **Public surface:** `git diff -- django_strawberry_framework/__init__.py` is
  **empty**; `__all__` and the re-export list are unchanged at HEAD. The
  no-root-export contract (Decision 4) additionally holds behaviourally, pinned by
  `tests/testing/test_client.py::test_export_surface_is_the_testing_root_not_the_package_root`.
- **CHANGELOG sanity:** not applicable — this cohort touches no source and
  `git status --porcelain -- CHANGELOG.md` is empty.

### What looks solid

- The walker's rejection set is the best-pinned surface in the module: 7 rows on
  the canonical-index validation, 3 on the empty segment, 2 each on the missing
  key, the terminal placeholder check, the tuple arm, and the unreadable length.
  Every one of those mutants failed loudly and none of those counts came from a
  run carrying a collection error.
- The `except Exception` around `len()` fails **closed**, and does so
  deliberately: it exists to stop a hostile `__len__` substituting its own
  exception type for the guard's, and the rows assert that substitution did not
  happen rather than merely that *something* raised.
- Presence-based (`is not None`) selection is now uniform across all four
  selection sites in the module. The `or`-fallback class that produced F3 item 2
  has no survivor.
- `self.path` is written exactly once, in `__init__`. The non-persistence
  contract is a structural property of the module, not a discipline anyone has to
  maintain.
- The sync/async split is honest: only the transport await and the `login()`
  color differ, and everything else is shared through `_build_body` /
  `_finish_response`.

### Notes for Worker 1 (spec reconciliation)

Written here on disk, not only in the return report — `BUILD.md`
`### Cohorting, naming, and closure` records a prior round where two builders'
amendment lists never landed on disk and the custodian re-derived all of them.

1. **Confirming F6, not re-raising it.** The spec's Slice-1 checklist at HEAD
   names `strawberry-graphql==0.262.0` as "the package's pinned floor"; `BUILD.md`
   `## Floor verification` — the single canonical statement — pins **0.316.0**.
   Independently confirmed by reading both. The floor-*presence* question the item
   gates is settled: `client.py` imports `strawberry.test.BaseGraphQLTestClient`
   and `strawberry.test.client.Response` at HEAD and the focused suite runs green,
   so no floor re-run is owed. Correct the text to name the section, not the
   number. **No branch in this module depends on interpreter version** — swept for
   version-gated behaviour and found none, so the Python 3.10 divergence class
   (`SpooledTemporaryFile.seekable`, and similar) does not apply here.
2. **Hot-path declaration `none` is correct.** Verified against the module's
   runtime position rather than against "no executable code changed": every symbol
   in `testing/client.py` is reachable only from a test process. `TestClient` is
   constructed per test or per mixin call, `request()` posts through
   `django.test.Client`, and nothing in the module is imported by any request,
   resolver, row, or outbound-message path in a deployed schema — confirmed by the
   module's own import set (`django.test`, `strawberry.test`, `conf`,
   `exceptions`) and by no package module importing `testing.client`. No
   contrary finding.
3. **Escalated — the existence challenge on `_build_body`'s empty-`variables`
   guard.** Proven redundant with the walker for both inputs it intercepts (see
   `### DRY and existence findings`). Resolution paths: (a) keep it and add the
   distinguishing rows, which this cohort recommends and which the `## Error
   shapes` text supports; (b) delete it and let the walker own every rejection,
   which then requires the spec's `## Error shapes` to be rewritten to the
   walker's wording. **Not a worker's call** — it decides which error contract the
   package offers. Route to the maintainer through Worker 0.
4. **Escalated — M4's ownership gap.** The nine undeclared raw-`client.post(...)`
   sites live in five live-tier files that appear in **no** cohort's write set.
   Closing M4 needs either a re-partition adding those files to Cohort C, or a
   recorded deferral naming an owning card. `AGENTS.md` `## Past mistakes`: an item
   routed forward without a named owner dies.
5. **Escalated — L2's validation posture.** Whether
   `conf.py::testing_endpoint_setting` should reject a non-`str` value, or whether
   its docstring should narrow its promise, turns on Decision 7's "validation stays
   at the consumer" posture. Contract-level; maintainer's call.
6. **F5 is confirmed from the code side.** `## Error shapes` at HEAD describes
   `if files is not None and variables is None:`; the shipped code is
   `if not files: return body` then `if not variables: raise ...` (client.py:282,
   285). The shipped truthiness is the **correct** behaviour —
   `test_empty_files_dict_is_a_plain_json_post` pins that `files={}` is a JSON
   post, which the spec's spelling would break — so the spec text is the defect, as
   F5 already says. Recording the corroboration so Cohort A does not need to
   re-derive it.
7. **F3 item 3 introduces a cross-module dependency the spec's
   `## Helper-reuse obligations (DRY)` does not list**:
   `client.py` imports `django_strawberry_framework.exceptions::_safe_arg_repr`
   (client.py:43). Confirmed present. It is a one-way import (testing -> exceptions)
   with no cycle, so it is a spec-text gap only, not a structural finding.
8. **No `TODO(spec-043 ...)` anchor survives anywhere in the tree** —
   `grep -rn 'TODO(spec-043' .` returns nothing. The staged-anchor obligation is
   discharged.

### Review outcome

**`revision-needed`.** Not because the production code is wrong — it is not; V1
through V6 each resolve in the code's favour and no High finding exists — but
because five boundaries in the shipped module are **weakly pinned** and two live
rows named for the endpoint ladder are **structurally incapable of failing**.
`BUILD.md` `### Acceptance rule` makes weakly pinned `revision-needed` with no
exception available, and `worker-3.md`'s acceptance gate forbids
`review-accepted` while any recorded proof is weakly pinned.

This is the terminal verdict a pure verification cohort is supposed to reach when
it finds something real, and it is what dispatches **Cohort C**. Cohort C's work
is entirely in the test tier — `tests/testing/test_client.py` and
`examples/fakeshop/test_query/test_client_api.py`, both already in its declared
write set — plus whatever the maintainer decides on the two escalated
contract-level questions. **No production-source change is required or
recommended by this cohort**, with the single exception that item 3's resolution
(a) or (b) may touch `client.py`, and that decision is the maintainer's.

Status: revision-needed
