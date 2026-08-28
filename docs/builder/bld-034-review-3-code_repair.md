# Build: Review round 3 — code repair (the one SKIPPED contract)

Spec reference: `docs/SPECS/spec-034-permissions-0_0_10.md` — `## Slice checklist` Slice 4 box 2, `## Definition of done` item 10, and the `## User-facing API` user-read note `#"binds `None` for every request"`. **Cited by section and substring, not by line number, on purpose:** the concurrent R2 round is rewriting this file right now and its line numbers moved during this planning pass (the `## Test plan` staff row went 451 → 467 between two reads). R1c's raw `:NN` citations for the same sentences are its own record and are not re-used here.
Rationale companion: `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md` (read-only this round)
Build plan: `docs/builder/build-034-permissions-0_0_10.md`
Source cohort: `docs/builder/bld-034-review-1c-fakeshop_and_surface.md` (findings **B4a** and **H1**)
Status: final-accepted

---

## Round preamble (Worker 1 declarations)

**Scope: exactly one file of source-or-test.** `examples/fakeshop/test_query/test_products_api.py`. This round lands **no production code**. If implementation reveals the repair needs a change in `examples/fakeshop/apps/products/schema.py` or anywhere under `django_strawberry_framework/`, that is a contract change and not a repair: **stop and escalate to Worker 0**, do not widen the diff.

**Hot-path declaration: none.** Stated explicitly so the silence is not read as an omission. The build plan's amended preamble already declares `none` for R3, and this plan agrees: the change adds live test rows only, so nothing new runs per request, per resolver, per row, per connection, or per outbound message. Had the repair touched `django_strawberry_framework/permissions.py::apply_cascade_permissions` — the walk that runs inside every cascading `get_queryset` — the declaration would be hot-path. It does not. Worker 2 writes `Not applicable; plan declares no hot path.` in `### Hot-path budget`.

**Floor-verification scope: this round owns one run.** The focused scope is

```
examples/fakeshop/test_query/test_products_api.py -k cascade
```

re-run in an **isolated floor venv outside the repository**, at the versions stated canonically in `docs/builder/BUILD.md` `## Floor verification` — read them from that section at run time; this plan deliberately does not restate the numbers, and neither should the build report's prose. **Owning pass: R3's builder pass (Worker 2).** The final gate is the backstop that confirms it happened, not a second owner.

The rows drive live `/graphql/` requests through the Django request/response seam and the Strawberry schema/connection construction seam, which is why the seam test in `## Floor verification` `### When it is required` is met.

Procedure constraints, all non-waivable:

- Build the venv under a scratch path **outside** the repo and install with an explicit `--python <venv>/bin/python` on every `uv pip install`. `uv pip install` ignores `UV_PROJECT_ENVIRONMENT` and will install into the shared `.venv` if allowed to; the explicit `--python` is the only thing that keeps it out. **Never install into, downgrade, or otherwise mutate `.venv`** — a concurrent session shares this tree.
- Record the resolved versions as read by `uv pip list --python <venv>/bin/python`, the exact focused command, and pass/fail, in `### Floor verification`.
- No `--cov*` flags. `--no-cov` is required (`pytest.ini` `addopts` auto-applies `--cov`) and is the only coverage-shaped flag permitted.

**The new test names must keep the substring `cascade`**, or the declared floor scope silently stops covering them. This plan's names satisfy that; a Worker 2 rename that drops the substring is a plan violation, not discretion.

**Boundary count, and the split question, answered in writing.** `worker-1.md` `### Boundary count is a split trigger` obliges the count and the answer even when the answer is obvious.

- New production boundaries, guards, caps, rejection paths, validation branches this round adds: **zero.** The round adds test rows that pin an *existing* boundary (`schema.py::EntryType.get_queryset` / `::PropertyType.get_queryset` staff short-circuit) which shipped in `0.0.10`.
- Files touched: one. Cohorts: one.
- **Answer: do not split.** One file, one contract, one builder pass, zero new boundaries. Splitting would put the two halves of a single four-field matrix in two diffs that could not see each other, which is the failure mode `### Parallel cohorts under a declared ownership partition` exists to avoid, for no gain.

**Test staleness a focused run cannot see — checked, and the answer is no.** `docs/builder/BUILD.md` `### Test staleness a focused run cannot see` names two change shapes that strand test files a slice never mentions. Neither applies:

- **No example-model field set changes.** No field on `Category` / `Item` / `Property` / `Entry` is added, removed, or renamed; no `fields=` / `exclude=` list, editable-column expectation, `"__all__"` shorthand, or dedup/identity assertion anywhere is affected. The plan reads `models.<X>.objects` and `<model>._meta.label_lower` only.
- **No wire-shape conversion.** No root or relation field becomes a connection; the `edges` / `node` envelope and every argument stay exactly as shipped. The new rows query the four root connection fields that already exist, selecting `{ id }` only.

Consequence for Worker 2: the focused run may legitimately be the scope below and does **not** need the three-tree `grep -rn <field name>` sweep or the full `uv run pytest tests/ --no-cov` sweep those two shapes would compel. This sentence exists so the narrow scope is a recorded decision rather than an accident.

**Concurrency.** The tree is baseline-dirty with a concurrent session's kanban work (build plan `### Baseline-dirty out-of-scope files`) and a concurrent **R2 round is rewriting the spec and the rationale companion right now**. This round edits neither, and reads no spec text as settled. Never `git checkout` / `git restore` / `git stash` anything.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Refreshed **for the whole package** this pass — `docs/shadow/helper-inventory.md`, regenerated from `django_strawberry_framework/` (not `utils/` alone) with the AST script in `worker-1.md` `### Package-wide helper inventory before helper planning`; 1,953 lines. Shapes searched (grep over the inventory, not an end-to-end read): `staff`, `global_?id`, `login`, `client`, `page`, `relay_max`, `visib`, `cascade`, `seed`, `fixture`. **Relevant candidates: none in the package.** The only package-side test-facing surface is the `django_strawberry_framework/testing/` client family (`TestClient` / `AsyncTestClient` / `GraphQLTestCase`), which this module already routes through indirectly via `examples/fakeshop/graphql_client.py`; it is an HTTP-driving client, not a permissions fixture or an expectation builder, so it serves nothing this round needs. Nothing in the package provides — or should provide — a "log in a seeded fakeshop user", "encode a GlobalID for an expectation", or "root-field-to-model" helper: all three are example-project test concerns and are already solved in the test tree (below). A static-inspection overview of the target file was also produced this pass: `docs/shadow/examples__fakeshop__test_query__test_products_api.overview.md` (`scripts/review_inspect.py … --output-dir docs/shadow`), read for its **Repeated string literals** section, which is what drives the one new module constant below.

- **Existing patterns reused.** All four, in the target file; no new helper is written.
  - `examples/fakeshop/test_query/test_products_api.py::_login` (:2154) — `_login("staff_1")` / `_login("view_entry_1")`, the established one-line "log in a seeded `create_users(1)` user" helper the five existing cascade tests already use. Reused verbatim for all three actors.
  - `examples/fakeshop/test_query/test_products_api.py::_global_id` (:73) — `_global_id(type_name, pk)`, already the file's way of building a wire-form GlobalID for an expectation (see the depth-2 forward-FK pin, :1430-1460). Reused with `model._meta.label_lower` as the type name, which is the same idiom that pin uses, and which keeps the plan from hard-coding the `products.category` / `products.entry` literals the shadow overview counts at **40x** and rising.
  - `examples/fakeshop/test_query/test_products_api.py #"_RELAY_MAX_RESULTS = 100"` (:1394) — the existing module constant for Strawberry's default `relay_max_results`, already documented at its definition as being used by "the staff full-set cascade pin". Reused; **not** re-derived and **not** duplicated.
  - `apps.products.services::seed_cascade_split` (:459) and `::create_users` — the shipped fixtures. **No new fixture is authored.** `seed_cascade_split` is the deterministic private/public chain helper the other five live cascade tests share; `create_users(1)` is the mandatory first line under `AGENTS.md` rule 8. `seed_data(1)` supplies the `is_private=True` rows in all four models that the differential assertion needs — `seed_cascade_split` alone cannot serve, because it creates **no** `is_private=True` `Item` / `Property` / `Entry` (only a private `Category`), and a fixture with no private row in those three models makes the staff assertion non-distinguishing. That is the justification `worker-1.md` requires for the fixture choice; the answer is "reuse both, author neither".

- **New helpers justified: one module-level constant, no functions.** `_CASCADE_ROOT_FIELDS` — a module-level tuple of `pytest.param(<root field>, <model>, <view_<model>_1 username>, id=<root field>)` rows for the four root fields, living beside the cascade section. Single responsibility: **name the four-field matrix once** so the two staff tests parametrize off the same list and a fifth root field is a one-line addition. It serves exactly two call sites, both in this file, both added by this round. Without it the same four-row table is written twice, which is the near-copy this section exists to prevent. No new *function* is justified: every behavior the tests need already has a helper (above), and a fifth wrapper around `_post_graphql` + `json()` + `edges → ids` would be a private convenience with one shape and two readers — extract it later only if a **third** test needs the same id-list extraction.

- **Duplication risk avoided.** The dominant risk here is the one the brief names: **a seventh near-identical cascade test body.** Six live cascade tests already sit in this section and they are structurally similar by nature (seed, log in, post one query, assert on the payload). A naive repair writes four more copies of the staff body — one per root field — or copies `test_cascade_staff_sees_everything` wholesale and edits the field name. The plan prevents that structurally, not by exhortation:
  - **Parametrization, not sibling bodies.** The four root fields are parameters of two functions, so the four-field matrix costs **two** bodies rather than eight, and the field name appears once per body.
  - **The two bodies are not near-copies of each other.** They assert different properties against different actors: one is a single-client page-identity assertion, the other a three-client differential. Neither can be expressed as the other with a flag.
  - **The seeding trio is identical across both**, deliberately: same three calls in the same order, so a difference between the two tests can never be a fixture artifact.
  - **No fixture, no GlobalID encoder, and no login helper is re-authored** — see the reuse list above. The repeated string literals the shadow overview flags (`allItems` 16x, `allCategories` 11x, `products.category` 40x, `view_category_1` 5x) go **down**, not up: the four root-field names and the four usernames are stated once in `_CASCADE_ROOT_FIELDS`, and the type-name literals are derived from `_meta.label_lower` rather than written out.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing — this tree is worked on concurrently and the file may have shifted.

1. **`examples/fakeshop/test_query/test_products_api.py`** — add the module-level constant `_CASCADE_ROOT_FIELDS` immediately above the staff test (i.e. in the live-cascade section that opens near `#"def _login(username: str) -> Client:"`, :2154, and after `#"_RELAY_MAX_RESULTS = 100"`, :1394, which it depends on only by proximity of subject, not by import order). Shape:

   - one `pytest.param(<root field name>, <model class>, <view_<model>_1 username>, id=<root field name>)` per row, in the file's established `pytest.param(..., id=...)` style (see :2503, :2571, :2595);
   - the four rows, in the schema's declaration order: `("allCategories", models.Category, "view_category_1")`, `("allItems", models.Item, "view_item_1")`, `("allProperties", models.Property, "view_property_1")`, `("allEntries", models.Entry, "view_entry_1")`;
   - a short comment stating **why the tuple carries the `view_<model>` username**: the spec's matrix is three actors, and the `view_<model>` holder takes the hook's `elif user.has_perm(...)` branch rather than the fall-through.
   - Do **not** put the GraphQL type name in the tuple: derive it in-test as `model._meta.label_lower`, matching `_global_id`'s existing call sites.

2. **`examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_everything`** (:2270) — **keep the function name** (it is the spec-named row in `docs/SPECS/spec-034-permissions-0_0_10.md` `## Test plan`, and R1c census B4 grades it present under that name; parametrizing adds a `[allEntries]`-style suffix to the node ids without renaming the function). Replace the in-body `for field, model in (("allCategories", models.Category), ("allItems", models.Item)):` loop with `@pytest.mark.parametrize("field, model, view_username", _CASCADE_ROOT_FIELDS)`, and strengthen the assertion as `### Test additions / updates` pins below. `view_username` is unused in this test — accept it for a single shared parametrize table rather than splitting the constant in two (see `### Implementation discretion items` for the permitted spellings).

3. **`examples/fakeshop/test_query/test_products_api.py`** — add the sibling `test_cascade_staff_sees_private_rows_hidden_from_non_staff`, parametrized off the same `_CASCADE_ROOT_FIELDS`, directly after `::test_cascade_staff_sees_everything`. **The name must contain `cascade`** (the declared floor scope is `-k cascade`).

4. **Docstrings.** Both tests carry a docstring in the section's established voice, and each must state *what it pins that the other does not*. `::test_cascade_staff_sees_everything`: staff's page **is** the unfiltered page. The sibling: staff sees a specific row that both non-staff actors provably cannot. Neither docstring states process provenance (`AGENTS.md`; the standing ban on how a change came to be) — cite the contract, not the review round. A spec `Decision` pointer is permitted.

5. **Validation.** `uv run ruff format examples/fakeshop/test_query/test_products_api.py` then `uv run ruff check --fix examples/fakeshop/test_query/test_products_api.py` — **scoped to this one file, never `.`** — then `git status --short` and confirm the only modified file this round intends is that one. Anything else is a stop-and-report, never a revert: this tree carries a concurrent session's uncommitted work.

6. **Focused run.** `uv run pytest examples/fakeshop/test_query/test_products_api.py -k cascade --no-cov -q -p no:randomly`. Expect **13 rows** where R1c recorded 6: the five unchanged non-staff cascade tests, plus 4 + 4 parametrized staff rows. Record the actual number in the build report by listing the node ids the run reports, not by asserting the arithmetic.

7. **Failability proof** — `### Test additions / updates` and the dedicated subsection below specify it in full. Run it **before** setting `Status: built`, and leave no mutation live across the status transition.

8. **Floor verification** — the round preamble's declaration, owned by this pass.

### Test additions / updates

Both tests live in `examples/fakeshop/test_query/test_products_api.py`, both open with `create_users(1)` as their literal first statement (`AGENTS.md` rule 8), and both then call `seed_data(1)` and `seed_cascade_split()` in that order — the same trio the shipped `::test_cascade_staff_sees_everything` already uses.

**Why the assertion shapes below and not the obvious ones** — `docs/builder/BUILD.md` `### Query-shape tests must pin the load-bearing property, not observability` applies directly. A staff assertion reading "some rows came back" is non-distinguishing: the anonymous path returns rows too. The load-bearing property is that **staff sees rows a non-staff actor does not**, and the expectation is derived from a real run rather than guessed. The numbers quoted below were **measured** this pass against `HEAD`, driving the live `/graphql/` path through Django's in-memory test database (the tracked `examples/fakeshop/db.sqlite3` was never opened for writing), under the exact fixture trio, with the two mutations simulated in-process by rebinding the hook's user read to the broken `getattr(info.context, "user", None)` form:

| root field | rows in model | staff page | anonymous page | `view_<model>` page | staff page after the matching mutation |
|---|---|---|---|---|---|
| `allCategories` | 27 | 27 | 14 | 14 | 27 (unaffected) |
| `allItems` | 27 | 27 | 7 | 7 | 27 (unaffected) |
| `allProperties` | 180 | **100 (capped)** | 41 | 41 | **98** |
| `allEntries` | 180 | **100 (capped)** | 10 | 10 | **82** |

Two consequences the assertion shape must respect, both of which a naive extension gets wrong:

- **`allProperties` and `allEntries` sit at the `_RELAY_MAX_RESULTS` cap.** The shipped `expected = min(model.objects.count(), _RELAY_MAX_RESULTS)` therefore evaluates to the constant `100` for both, and the mutated staff page is `98` for `Property` — a two-row margin that a Faker upgrade could close silently, at which point the row would still pass while pinning nothing. **A count-equality assertion is not enough here.** The plan replaces it with an **id-list equality** against the model's own first-`_RELAY_MAX_RESULTS` rows in pk order, which distinguishes by membership rather than by cardinality and so does not degrade as the seeded volume grows.
- **A `set(anonymous) < set(staff)` subset assertion is rejected**, and deliberately: with 180 rows and a 100-row page, staff's page and the anonymous page are windows over *different* row sets, so an anonymous-visible row whose pk falls beyond the 100th pk would be in the anonymous page and absent from staff's. Subset is not a sound invariant at this volume. Do not add it.

**T1 — `::test_cascade_staff_sees_everything`** (existing name kept; parametrized over `_CASCADE_ROOT_FIELDS`). Pins: *staff's page is the unfiltered page.*

- `client = _login("staff_1")`; post `query { <field> { edges { node { id } } } }`.
- `assert response.status_code == 200` and `assert "errors" not in payload, payload`.
- Build `expected` as `[_global_id(model._meta.label_lower, pk) for pk in model.objects.order_by("pk").values_list("pk", flat=True)[:_RELAY_MAX_RESULTS]]` — the model's own rows, unfiltered, in the connection's default pk order, truncated to the page cap.
- **Fixture precondition, asserted:** `assert model.objects.filter(is_private=True).exists()` — there must *be* rows the cascade would hide, or the assertion below is vacuous. (This generalizes the shipped test's `Category`-only version of the same sanity check.) A control that cannot fail reads exactly like a passing proof; this line is what stops that.
- **The load-bearing assertion:** the returned node-id list **equals** `expected`, with a message naming the field and both lengths.
- **Drop** the shipped trailing `assert models.Category.objects.count() <= _RELAY_MAX_RESULTS`: it is false for `Property` / `Entry` at this fixture volume and is subsumed by the cap-aware `expected` above. Its replacement is the precondition line.
- The shipped `expected = min(model.objects.count(), _RELAY_MAX_RESULTS)` count comparison is **subsumed** by id-list equality (equal lists have equal lengths) — see `### Implementation discretion items` for whether it may survive as a diagnostic.

**T2 — `::test_cascade_staff_sees_private_rows_hidden_from_non_staff`** (new; parametrized over the same table). Pins: *staff sees a row both non-staff actors provably cannot.*

- `hidden = model.objects.filter(is_private=True).order_by("pk").first()`; `assert hidden is not None`; `hidden_gid = _global_id(model._meta.label_lower, hidden.pk)`.
- **Fixture precondition, asserted:** `hidden_gid` is inside the first `_RELAY_MAX_RESULTS` ids in pk order — otherwise the row is outside the page the query returns and "staff sees it" would fail for a reason that has nothing to do with permissions. Measured true for all four models at `HEAD`; asserting it makes a future fixture drift loud instead of silent.
- Post the same `{ id }` query three times: as `_login("staff_1")`, as an anonymous client, and as `_login(view_username)`.
- **Non-vacuity guards, asserted:** the anonymous page and the `view_<model>` page are each **non-empty**. Without these, "the anonymous page lacks the hidden row" is satisfied by an empty page and pins nothing — precisely the observability trap.
- **The load-bearing assertions:** `hidden_gid` is **in** the staff id list, **not in** the anonymous id list, and **not in** the `view_<model>` id list.
- Assert `"errors" not in payload` on all three responses (the `view_<model>` and anonymous requests must not error; no `filter:` / `orderBy:` argument is used anywhere in either test, so the `CategoryFilter::check_name_permission` staff gate is never reached and cannot mask a result).

**Temp/scratch tests: none are appropriate.** Everything this round needs is a permanent row; R1c already established (its `### Temp test verification`) that the instrument for this gap is a mutation against shipped code, not a new scratch file. Worker 3 may still write one under `docs/builder/temp-tests/034-r3/` to demonstrate that an assertion is non-distinguishing.

### Failability proof Worker 2 owes (this round is the exception to "no new boundary, no proof")

`docs/builder/BUILD.md` `### What needs a proof, and what does not` would ordinarily make this subsection read `None; this pass introduced no new boundary.` — the round adds no production code. **It does not read that here.** The entire point of the change is to convert a **measured 0-row** mutation result into a non-zero one, so the proof is the round's deliverable, not an incidental obligation.

- **Perform it through `scripts/prove_failability.py`** — the supported way to perform a proof (`### Mechanized`). Manifest at **`docs/builder/temp-tests/034-r3/proofs.json`**; emit with `--output docs/builder/temp-tests/034-r3/proofs-report.md` and transcribe into `### Failability proofs`. `--help` and the module docstring own the manifest schema and every flag; this plan does not restate them. Scratch root **outside the repository**.
- **Two entries, mirroring R1c's P2 and its untested twin:**
  - **E1 — `examples/fakeshop/apps/products/schema.py::EntryType.get_queryset`.** Mutation: replace `user = getattr(getattr(info.context, "request", None), "user", None)` with `user = getattr(info.context, "user", None)` — R1c's exact P2 mutation, the fail-open form the spec's `## User-facing API` note warns binds `None` for every request. Anchor on the unique `products.view_entry` block so exactly one hook is mutated.
  - **E2 — `examples/fakeshop/apps/products/schema.py::PropertyType.get_queryset`.** The same mutation, anchored on the unique `products.view_property` block. This round's shape covers `PropertyType`, so it owes the proof too.
- **Scope: R1c's exact scope, unchanged**, so the before and after are comparable:

  ```
  uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE \
    examples/fakeshop/test_query/test_products_api.py \
    examples/fakeshop/apps/products/tests/test_schema.py
  ```

- **Record the before and the after as node-id SETS, never a bare count** (`### What gets recorded`; a bare count rots and cannot distinguish "better pinned now" from "different scope" or "someone measured wrong").
  - **Before (E1), from R1c and cited as such:** failing node ids **none** — 0 rows, against a green pre-mutation baseline of `125 passed` with 0 collection/setup errors. There is no recorded before for E2; say so rather than inventing one.
  - **After:** list every failing node id. **Expected** (measured this pass, in-process): E1 fails `::test_cascade_staff_sees_everything[allEntries]` and `::test_cascade_staff_sees_private_rows_hidden_from_non_staff[allEntries]`; E2 fails the two `[allProperties]` rows. **2 rows each**, which clears `### Acceptance rule: weakly pinned is revision-needed` (0 or 1). Record what the tool actually reports; if either entry comes back at 0 or 1 rows, that is `revision-needed` on this plan's shape, not a recorded exception — say so and stop.
  - Record the **new** pre-mutation baseline for this scope (the row count moves from 125 as the parametrized rows land) and difference against it.
  - Record **collection / setup errors separately**; a proof carrying any is not a valid count. Resolve and re-run.
  - Prove each restore by **byte comparison**, and keep only one mutation live at a time — revert before starting the second, never at the end.
- Worker 3's mandatory re-run floor (`worker-3.md`, boundaries at 3 rows or fewer, and every boundary on a data-isolation decision) will catch both entries. That is expected and is a feature of a 2-row result, not a defect in it.

### Implementation discretion items

Choices Worker 1 has **assessed and decided** belong to Worker 2. None is an architectural question.

- **The unused `view_username` parameter in T1.** T1 does not use the third tuple element. Any of these is acceptable: accept and ignore it; spell it `_view_username`; or destructure it away. **Not** acceptable: splitting `_CASCADE_ROOT_FIELDS` into two constants to avoid it — one table for one matrix is the point of the constant. Follow whatever `ruff` accepts without a `noqa`.
- **Whether the subsumed count comparison survives as a diagnostic.** Id-list equality strictly subsumes `len(returned) == min(model.objects.count(), _RELAY_MAX_RESULTS)`. Worker 2 may keep the lengths in the assertion **message** for a readable first-line diagnostic, or drop them entirely. A second standalone `assert` that cannot fail independently of the first is noise — do not add one.
- **Where `_CASCADE_ROOT_FIELDS` sits** within the live-cascade section (immediately before `::test_cascade_staff_sees_everything`, or at the top of the section beside `_login`), and whether the four rows are written as `pytest.param(..., id=...)` or as bare tuples with a separate `ids=` list. The file's established style is `pytest.param(..., id=...)`; prefer it, but either reads correctly.
- **The exact assertion messages**, and whether T2 extracts its three id-list reads into a local closure inside the test body. A local closure inside one function is a style call; a new module-level helper is not — that is a plan decision and the plan says no (see `### DRY analysis`).
- **Docstring wording**, subject to step 4's two constraints (state what this row pins that its sibling does not; no process provenance).

### Dispatched findings checklist

One box per finding dispatched to this cohort, quoted as the cohort stated it, with the symbol-qualified path from R1c's verification. Boxes stay `- [ ]` at planning; **Worker 2 ticks `- [x]`** only a box whose fix actually landed in its diff this pass and states any deferral in the build report instead of ticking; **Worker 3 walks the list** during review; **Worker 1 audits every tick** at final verification.

- [x] **B4a (SKIPPED contract — the cycle's single one).** As R1c stated it: *"Slice 4 box 2: live coverage runs 'across the products 2-deep FK chain (`Entry → Item → Category` / `Entry → Property → Category`): … **staff sees everything**'; DoD 10's 'anonymous / per-`view_<model>` / staff matrix' over the same chain … `::test_cascade_staff_sees_everything` iterates only `#"for field, model in ((\"allCategories\", models.Category), (\"allItems\", models.Item)):"` — `allEntries` and `allProperties` are never queried as staff, in this file or anywhere."* Symbol-qualified: `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_everything`, against `examples/fakeshop/apps/products/schema.py::EntryType.get_queryset` and `examples/fakeshop/apps/products/schema.py::PropertyType.get_queryset`. **Tick only when all four root fields are covered by the staff matrix**, not when two of four are.

- [x] **H1 (High — the finding sharing B4a's remedy).** As R1c stated it: *"`EntryType.get_queryset`'s staff branch is pinned by nothing: removing it fails 0 rows."* Measured: replacing `EntryType`'s user read with the broken `getattr(info.context, "user", None)` form fails **0 of 125 rows** across `examples/fakeshop/test_query/test_products_api.py` and `examples/fakeshop/apps/products/tests/test_schema.py`, against a green pre-mutation baseline with 0 collection errors, while the control (removing `ItemType`'s cascade) fails **11** at the same scope — *"weakly pinned, not harness-impossible"*. Symbol-qualified: `examples/fakeshop/apps/products/schema.py::EntryType.get_queryset #"user = getattr(getattr(info.context, \"request\", None), \"user\", None)"`, pinned from `examples/fakeshop/test_query/test_products_api.py`. **Tick only when `### Failability proofs` records a non-zero, node-id-listed after-set for both E1 and E2** — the fix here is the measurement, not the presence of a test.

### Notes for Worker 1 (spec reconciliation)

Written by Worker 1 at plan time, for the **next** Worker 1 pass. **A concurrent R2 round is rewriting the spec and the rationale companion right now; this round acts on none of it and treats no current spec text as settled.**

- **The spec's `## Test plan` names one staff row.** `docs/SPECS/spec-034-permissions-0_0_10.md` `## Test plan` `#"- \`test_cascade_staff_sees_everything\`."` lists that name and nothing else for the staff half of the matrix. After this round that name survives (parametrized, four node ids) and a **sibling** row exists that the Test plan does not name. Whoever owns the spec next decides whether the Test plan gains the sibling; this round does not touch it.
- **Slice 4 box 2 and DoD 10 are correct and stay correct.** B4a is a *code* gap against a right contract, per R1c's grading. No spec sentence needs to change to accommodate this round — recorded so a later pass does not "reconcile" a contract that was never wrong.
- **R1c's M1 (the `view_<model>` branch that is the same expression as the fall-through) is a maintainer decision and is untouched here.** Note the ordering R1c recorded and this plan preserves: **H1's rows land before any M1 collapse**, so a collapse is performed against a suite that can detect a mistake in it. This round's T2 asserts the `view_<model>` actor explicitly, which is what makes a future collapse — or a future divergence — observable at all.
- **Not fixed here, by maintainer escalation:** the 18 rotted card ids in `examples/fakeshop/apps/products/schema.py` (beside one correct `TODO-BETA-062-0.1.5`). Disposition is coupled to `KANBAN.md`, outside this cycle's scope. This round writes no production file, so it does not even touch the file that carries them.

---

## Build report (Worker 2)

Plan implemented as written. The staff half of the spec-034 matrix now covers all four root fields, and the measurement the round exists to produce is non-zero on both previously-unpinned hooks: **2 rows each** for `EntryType` and `PropertyType`, against R1c's measured **0 of 125** for `EntryType`. No production file was written; the only source-or-test file in the diff is the one the plan's scope names.

### Files touched

Grounded in `git status --short`, not memory.

- `examples/fakeshop/test_query/test_products_api.py` — the round's only source-or-test edit (`+84 / -12`). Adds the module-level `_CASCADE_ROOT_FIELDS` matrix constant, parametrizes `::test_cascade_staff_sees_everything` over it (replacing the two-field in-body `for field, model in (...)` loop and strengthening its assertion to id-list equality), and adds the sibling `::test_cascade_staff_sees_private_rows_hidden_from_non_staff`.
- `docs/builder/bld-034-review-3-code_repair.md` — this build report, the `Status:` transition, and the two `### Dispatched findings checklist` ticks.
- `docs/builder/worker-memory/worker-2.md` — appended pass entry.
- `docs/builder/temp-tests/034-r3/proofs.json`, `docs/builder/temp-tests/034-r3/proofs-report.md` — the failability manifest and the tool's emitted report (gitignored scratch, cleared per cycle by `scripts/clean_up.py`).

Every other path reported dirty by `git status --short` is classified under `### Validation run` and none was edited or reverted.

### Tests added or updated

Both live at `examples/fakeshop/test_query/test_products_api.py`, both open with `create_users(1)` as the literal first statement (`AGENTS.md` rule 8) followed by `seed_data(1)` then `seed_cascade_split()` — the identical trio in both, so a difference between the two rows can never be a fixture artifact. Both names carry the `cascade` substring, so the declared `-k cascade` floor scope covers them.

- `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_everything` — name kept (the spec's `## Test plan` names it); now parametrized over `_CASCADE_ROOT_FIELDS`, node ids `[allCategories]` / `[allItems]` / `[allProperties]` / `[allEntries]`. **Pins: staff's page IS the unfiltered page.** The returned node-id list **equals** `[_global_id(model._meta.label_lower, pk) for pk in model.objects.order_by("pk").values_list("pk", flat=True)[:_RELAY_MAX_RESULTS]]` — membership and order against the model's own rows, not cardinality, so it does not degrade to the constant `100` for `Property` / `Entry`, which sit at the cap. Carries the asserted fixture precondition `model.objects.filter(is_private=True).exists()`: without rows the cascade would hide, the equality is satisfied by a queryset the cascade never had anything to narrow, and the control could not fail. The shipped `expected = min(model.objects.count(), _RELAY_MAX_RESULTS)` count comparison is subsumed (equal lists have equal lengths) and the shipped trailing `assert models.Category.objects.count() <= _RELAY_MAX_RESULTS` is dropped — it is false for `Property` / `Entry` at this fixture volume, and the cap-aware `expected` covers what it was standing in for.
- `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_private_rows_hidden_from_non_staff` — new, parametrized over the same table, same four node ids. **Pins: staff sees a specific private row that BOTH non-staff actors provably cannot.** Takes `hidden = model.objects.filter(is_private=True).order_by("pk").first()`, asserts it is not `None`, and asserts its GlobalID falls **inside** the first `_RELAY_MAX_RESULTS` pks — otherwise staff's half would fail for pagination reasons rather than permission ones. Posts the same `{ id }` query three times (`staff_1`, anonymous, `view_<model>_1`), asserts `status_code == 200` and `"errors" not in payload` on each, asserts **both non-staff pages are non-empty** (an empty page satisfies every `not in` below and pins nothing), then asserts `hidden_gid` **in** staff's list, **not in** the anonymous list, and **not in** the `view_<model>` list. No `filter:` / `orderBy:` argument appears in either test, so the `CategoryFilter::check_name_permission` staff gate is never reached and cannot mask a result.

Not added, deliberately: a `set(anonymous) < set(staff)` subset assertion. At 180 seeded `Property` / `Entry` rows over a 100-row page the three actors' pages are windows over different row sets, so subset is not a sound invariant — the plan records this and the docstring states it at the site.

**Temp/scratch tests: none written.** The plan states none is appropriate; the instrument for this gap is the mutation against shipped code, recorded below.

### Validation run

- `uv run ruff format examples/fakeshop/test_query/test_products_api.py` — **pass**, `1 file left unchanged`. Scoped to this pass's own file; never `.`.
- `uv run ruff check --fix examples/fakeshop/test_query/test_products_api.py` — **pass**, `All checks passed!`, no fixes applied.
- `uv run python scripts/check_trailing_commas.py --check examples/fakeshop/test_query/test_products_api.py` — **pass**, exit 0 (line length, explode-at-threshold layout, ASCII-only). Run as an author-side check, not as the maintainer's pre-commit step.
- `git status --short` after both ruff invocations — the only slice-intended modified path is `examples/fakeshop/test_query/test_products_api.py`. Classification of everything else, **reported not reverted**:
  - Baseline-dirty concurrent kanban work, exactly the build plan's `### Baseline-dirty out-of-scope files` list: `BACKLOG.md`, `KANBAN.html`, `KANBAN.md`, `README.md`, `examples/fakeshop/db.sqlite3`, `scripts/_kanban_lib.py`, `scripts/build_kanban_html.py`, `scripts/build_kanban_md.py`, `tests/test_build_kanban_html.py`, and the untracked `0_0_14.md`, `docs/DIVERGENCE.md`.
  - `docs/SPECS/spec-034-permissions-0_0_10.md` (modified) and the untracked `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md` — the **concurrent R2 round**, which the round preamble declares is rewriting both right now. Read-only for this pass; neither was edited.
  - Untracked cycle artifacts not written by this pass: `docs/builder/build-034-permissions-0_0_10.md`, `bld-034-slice-0-rationale_extraction.md`, `bld-034-review-1a-cascade_module.md`, `bld-034-review-1b-composition_pins.md`, `bld-034-review-1c-fakeshop_and_surface.md`.
  - `git checkout` / `git restore` / `git stash` were never invoked, on any path.
- Focused run — `uv run pytest examples/fakeshop/test_query/test_products_api.py -k cascade --no-cov -q -p no:randomly` → **13 passed**, exit 0. No `--cov*` flag anywhere; `--no-cov` only. The node ids the run reports, listed rather than arithmetically asserted (R1c recorded 6 at this scope):
  1. `::test_cascade_anonymous_sees_no_entries_under_private_categories`
  2. `::test_cascade_view_item_user_respects_category_visibility`
  3. `::test_cascade_view_entry_user_nested_selection_drops_hidden_targets`
  4. `::test_cascade_staff_sees_everything[allCategories]`
  5. `::test_cascade_staff_sees_everything[allItems]`
  6. `::test_cascade_staff_sees_everything[allProperties]`
  7. `::test_cascade_staff_sees_everything[allEntries]`
  8. `::test_cascade_staff_sees_private_rows_hidden_from_non_staff[allCategories]`
  9. `::test_cascade_staff_sees_private_rows_hidden_from_non_staff[allItems]`
  10. `::test_cascade_staff_sees_private_rows_hidden_from_non_staff[allProperties]`
  11. `::test_cascade_staff_sees_private_rows_hidden_from_non_staff[allEntries]`
  12. `::test_cascade_query_count_fixed`
  13. `::test_cascade_composes_with_filter_and_order_live`
- **Test-staleness full sweep: not owed.** The plan's round preamble records the determination (no example-model field-set change, no wire-shape conversion); this pass confirmed it against its own diff — the diff reads `models.<X>.objects`, `<model>._meta.label_lower` and the four already-existing root connection fields, and adds no `fields=` / `exclude=` list, no editable-column expectation, and no change to the `edges` / `node` envelope or any argument.

### Failability proofs

Performed through `uv run python scripts/prove_failability.py docs/builder/temp-tests/034-r3/proofs.json --output docs/builder/temp-tests/034-r3/proofs-report.md` (the `### Mechanized` supported way). Scratch root **outside the repository** at `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/e3a7bb93-0439-4447-b248-b5509e0f6d36/scratchpad/failability-034-r3`. The anchor check ran **first and standalone** (`--check-anchors-only`, exit 0): both anchors matched **exactly once**, which is also the evidence that the tree carried no prior live mutation — `ACTIVE-MUTATION.json` was checked for and absent before anything else. One boundary live at a time, each restored before the next started; the run's exit code was `0` (every entry proved, none weakly pinned).

This round adds **no new production boundary**, so `### What needs a proof` would ordinarily excuse the subsection. It does not here: converting R1c's measured **0-row** result into a non-zero one is the round's deliverable.

Scope as run, identical for both entries and for both baselines (R1c's exact scope, unchanged, so before and after are comparable):

```
uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE \
  examples/fakeshop/test_query/test_products_api.py \
  examples/fakeshop/apps/products/tests/test_schema.py
```

**E1 — `examples/fakeshop/apps/products/schema.py::EntryType.get_queryset`** (the fail-open user read; R1c's P2 mutation, verbatim)

- **Exact mutation applied:** `user = getattr(getattr(info.context, "request", None), "user", None)` replaced by `user = getattr(info.context, "user", None)` — the form the spec's `## User-facing API` note warns `#"binds `None` for every request"`, collapsing the staff and `view_<model>` branches to the anonymous public-only path. Anchored on the unique `products.view_entry` block (the surrounding `if user and user.is_staff: / return queryset / elif user and user.has_perm("products.view_entry"):` lines travel in the anchor) so exactly one of the four hooks is mutated.
- **Pre-mutation state of this scope, re-measured this pass rather than inherited:** `132 passed`, pytest exit 0. Pre-existing failing rows differenced out: **0**. (R1c's baseline was `125 passed`; the scope gained 7 rows — `::test_cascade_staff_sees_everything` went 1 row to 4, and the sibling adds 4.)
- **Collection / setup errors: 0.** Mutant pytest exit code: 1 (`2 failed, 130 passed`) — a valid count.
- **Failing node ids (2; the count is `len()` of this list):**
  - `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_everything[allEntries]`
  - `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_private_rows_hidden_from_non_staff[allEntries]`
- **Before, cited as R1c's own record:** failing node ids **none** — 0 rows, against a green `125 passed` baseline with 0 collection/setup errors. The set difference is therefore the two rows above, both landed by this pass.
- **Verdict: clears `### Acceptance rule`** (2 rows, not 0 or 1). Inside Worker 3's mandatory independent re-run floor (<= 3 rows), which is expected and is a property of a 2-row result, not a defect in it.
- **Revert proved by byte comparison:** `filecmp.cmp(shallow=False)` -> `True`; `sha256 cd91fe508c5fd8a2... == cd91fe508c5fd8a2...` against the pre-mutation copy. Performed by the tool in a `finally`, before entry E2 began.

**E2 — `examples/fakeshop/apps/products/schema.py::PropertyType.get_queryset`** (the `EntryType` twin; no prior measurement exists)

- **Exact mutation applied:** the same replacement, anchored on the unique `products.view_property` block.
- **Pre-mutation state of this scope:** `132 passed`, pytest exit 0. Pre-existing failing rows differenced out: **0**.
- **Collection / setup errors: 0.** Mutant pytest exit code: 1 (`2 failed, 130 passed`) — a valid count.
- **Failing node ids (2):**
  - `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_everything[allProperties]`
  - `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_private_rows_hidden_from_non_staff[allProperties]`
- **Before: there is no recorded before for E2.** R1c ran P1 (`ItemType`, the control) and P2 (`EntryType`); it never mutated `PropertyType`. Stated rather than invented.
- **Verdict: clears `### Acceptance rule`** (2 rows). Inside the re-run floor.
- **Revert proved by byte comparison:** `filecmp.cmp(shallow=False)` -> `True`; `sha256 cd91fe508c5fd8a2... == cd91fe508c5fd8a2...` against the pre-mutation copy.

**No zero-row entry, so no `why 0` judgement is owed.** Both entries cleared the acceptance rule at the plan's measured expectation of 2, so no `revision-needed` on the plan's shape.

**Tree state after both proofs**, verified independently of the tool: `git status --short examples/fakeshop/apps/products/schema.py` reports nothing and `git diff --stat -- examples/fakeshop/apps/products/schema.py` is empty, so the file is byte-identical to `HEAD`. The scratch root holds only `pristine/` — **no `ACTIVE-MUTATION.json`, no `RESTORE-FAILED.json`**. No mutation is live across this pass's `Status:` transition.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Owned by this pass per the plan's round-preamble declaration. Versions taken from `docs/builder/BUILD.md` `## Floor verification`, the single canonical statement, and **executed** rather than reasoned about.

- **Scratch venv path (outside the repo):** `/tmp/dsf-floor-034`, built with `uv venv /tmp/dsf-floor-034 --python 3.10`. Every install carried an explicit `--python /tmp/dsf-floor-034/bin/python`.
  - `uv pip install --python /tmp/dsf-floor-034/bin/python -e . --group dev`
  - `uv pip install --python /tmp/dsf-floor-034/bin/python 'django==5.2.16' 'strawberry-graphql==0.316.0'` (downgraded `django 5.2.17 -> 5.2.16` and `strawberry-graphql 0.324.0 -> 0.316.0` inside the scratch venv).
- **Resolved versions, as read by `uv pip list --python /tmp/dsf-floor-034/bin/python`:** `django 5.2.16`, `strawberry-graphql 0.316.0`, `django-strawberry-framework 0.0.14` (editable, from the repo), `channels 4.3.2`, `pytest 9.1.1`, `pytest-django 4.14.0`. Interpreter: `/tmp/dsf-floor-034/bin/python -V` -> `Python 3.10.19`.
- **Focused scope run:** `/tmp/dsf-floor-034/bin/python -m pytest examples/fakeshop/test_query/test_products_api.py -k cascade --no-cov`
- **Result: PASS — `13 passed`**, exit 0, all four `[allCategories]` / `[allItems]` / `[allProperties]` / `[allEntries]` node ids of both new/updated tests among them. No floor-only failure, so no production-compatible fix was needed.
- **Shared `.venv` untouched**, verified after the run: `uv pip list` still reports `django 6.1` / `strawberry-graphql 0.324.0` and `.venv/bin/python -V` is `Python 3.14.2` — none of the floor versions leaked into it.

### Implementation notes

- **Two module-level test functions were written, then removed.** The first draft extracted `_cascade_page_ids(model)` and `_cascade_root_field_ids(field, client)` as module-level helpers. That is exactly what `### DRY analysis` decides against (`New helpers justified: one module-level constant, no functions`), and `### Implementation discretion items` puts a module-level helper on the plan's side of the line rather than Worker 2's. Reverted to the plan's shape: T1 inlines its single post and its `expected` comprehension; T2 uses a **local closure** (`node_ids`), which the discretion list names as a permitted style call inside one function. Recorded so the diff's shape is not mistaken for an accident.
- **`_CASCADE_ROOT_FIELDS` uses `pytest.param(..., id=...)`**, the file's established style (`::test_post_multibyte_encoded_json_body_is_rejected_as_400` and the two non-object-body rows), with the `id` equal to the root field name so the node ids read `[allEntries]` rather than `[allEntries-Entry-view_entry_1]`. Placed immediately above `::test_cascade_staff_sees_everything`, inside the live-cascade section, which is the plan's first-listed option.
- **The unused third element in T1 is spelled `_view_username`.** `pytest.mark.parametrize` binds by the argnames string given at each call site, so one shared constant feeds `"field, model, _view_username"` in T1 and `"field, model, view_username"` in T2 with no split. Ruff accepts either without a `noqa` here (`ARG` is in the `examples/**/*.py` per-file ignore list), so the underscore is chosen purely to tell a reader the omission is deliberate — the plan's "accept and ignore it" would have linted clean too.
- **The GraphQL type name is derived, never written.** `_global_id(model._meta.label_lower, pk)` follows the existing depth-2 forward-FK pin's idiom and keeps the `products.category` / `products.entry` string literals (40x and rising in the file, per the shadow overview) from growing by eight more.
- **The fixture precondition in T1 is asserted after the response is read, not before the request.** Ordering is immaterial to what it proves — it is a statement about the seeded rows, and both orderings run under the same transaction — and reading it beside the `expected` it guards is what makes its purpose legible at the site.
- **T1's assertion message keeps the two lengths** (`(field, len(returned), len(expected))`) rather than the full lists: a length mismatch is the common first diagnostic and pytest's own comparison output already renders the list diff. No second standalone count `assert` was added; it could not fail independently of the equality and would be noise.

### Notes for Worker 3

- **Both boundaries sit at 2 rows, inside your mandatory independent re-run floor** (3 or fewer, and both are data-isolation decisions, so they qualify twice over). Re-run at the recorded scope — `examples/fakeshop/test_query/test_products_api.py` plus `examples/fakeshop/apps/products/tests/test_schema.py` — and compare node-id **sets**, not counts; the manifest is reusable as-is at `docs/builder/temp-tests/034-r3/proofs.json` and the tool's own emitted report is at `docs/builder/temp-tests/034-r3/proofs-report.md`.
- **The pre-mutation baseline for that scope moved from R1c's 125 to 132** because this pass's rows landed in it. Differencing against 125 would inflate any re-measurement by 7.
- **No shadow file was generated or consulted by this pass.** The plan's `### DRY analysis` cites `docs/shadow/examples__fakeshop__test_query__test_products_api.overview.md`, produced during planning; this pass read the plan's summary of it rather than regenerating it, so no `scripts/review_inspect.py` run belongs to this build.
- **Unusual control flow worth knowing:** T2's `node_ids` closure captures the parametrized `field` and issues three separate live `/graphql/` POSTs inside one test, one per actor. The anonymous read passes `client=None`, which is `graphql_client.post_graphql`'s own default path (a fresh unauthenticated `TestClient`) and matches how the other anonymous cascade rows drive the endpoint.
- **The two tests are not near-copies.** T1 is a single-actor page-identity assertion; T2 is a three-actor membership differential. Neither is expressible as the other with a flag, which is why the round is two bodies over four parameters rather than eight bodies.
- **`examples/fakeshop/apps/products/schema.py` is byte-identical to `HEAD`.** It appears in this report only as the transient, byte-compare-proved mutation target. The 18 rotted card ids it carries were **not** touched — maintainer-escalated, coupled to `KANBAN.md`, outside this cycle's scope.

### Notes for Worker 1 (spec reconciliation)

- **No plan-vs-implementation drift, structural or small.** The plan's shape was implementable exactly as written; the one deviation attempted (two module-level helpers) was reverted to the plan's decision inside this pass and is recorded in `### Implementation notes` rather than here, because nothing about the plan needed to change for it.
- **A spec `## Test plan` amendment is now available to take or decline** — the plan raised it at planning time and this pass confirms the name it predicted.
  - **Where it lives:** `docs/SPECS/spec-034-permissions-0_0_10.md`, `## Test plan`, the Slice 4 staff row.
  - **Current wording, quoted:** `- \`test_cascade_staff_sees_everything\`.`
  - **Recommended replacement:** `- \`test_cascade_staff_sees_everything\` (parametrized over the four root connection fields).` followed by a new sibling bullet `- \`test_cascade_staff_sees_private_rows_hidden_from_non_staff\` (the three-actor differential over the same four fields).`
  - Both names exist at `HEAD`-plus-this-diff under exactly those spellings; the first survives its parametrization (four node ids, unchanged function name). **A concurrent R2 round is rewriting this file, so the anchor plus quote — not a line number — is what will still resolve when this is read.**
- **Slice 4 box 2 and DoD 10 need no change.** B4a was a code gap against a correct contract; this pass closes it and leaves both sentences true for the first time. Recorded so a later pass does not "reconcile" a contract that was never wrong.
- **M1's ordering is preserved as R1c asked.** H1's rows are now on disk, so a future collapse of the `view_<model>` branch into the fall-through would be performed against a suite that can detect a mistake in it: `::test_cascade_staff_sees_private_rows_hidden_from_non_staff` asserts the `view_<model>` actor explicitly, for all four models, and is what makes a divergence observable at all. M1 itself remains the maintainer's decision and was not acted on.
- **Nothing in the spec, the rationale companion, or any other cycle artifact was read as settled or written by this pass.**

---

## Review (Worker 3)

### Independent failability re-run — mutations recorded BEFORE they are made

`worker-3.md` `### Reading is necessary, not sufficient` requires the mutation to be written into this
artifact before it is applied. Both of Worker 2's entries sit at **2 rows** and both are
data-isolation decisions, so both fall inside the mandatory floor and **both are re-run**; the
re-run set is not a sample. Nothing is accepted on Worker 2's record alone.

- **R-E1 — `examples/fakeshop/apps/products/schema.py::EntryType.get_queryset`.** Mutation to apply:
  replace `user = getattr(getattr(info.context, "request", None), "user", None)` with
  `user = getattr(info.context, "user", None)`, anchored on the four-line block whose fourth line is
  `elif user and user.has_perm("products.view_entry"):` so exactly one of the four hooks moves.
- **R-E2 — `examples/fakeshop/apps/products/schema.py::PropertyType.get_queryset`.** The same
  replacement, anchored on the `products.view_property` block.
- Scope: Worker 2's recorded scope verbatim (`examples/fakeshop/test_query/test_products_api.py`
  plus `examples/fakeshop/apps/products/tests/test_schema.py`), so the node-id sets are comparable.
- Manifest written fresh under `docs/builder/temp-tests/034-r3-review/proofs.json` (Worker 3's own
  temp-test directory), scratch root **outside** the repository. Anchors checked standalone first;
  one boundary live at a time; each restore proved by byte comparison.

#### Measurements — both boundaries re-run, neither accepted on Worker 2's record alone

Re-run through `uv run python scripts/prove_failability.py docs/builder/temp-tests/034-r3-review/proofs.json
--output docs/builder/temp-tests/034-r3-review/proofs-report.md`, scratch root
`/private/tmp/.../scratchpad/w3-failability-034-r3` (outside the repository). Run exit code `0`.

Anchor pre-check, standalone and first (`--check-anchors-only`, exit 0): both anchors matched **exactly
once**, which is also the evidence that the tree was carrying no live mutation from any earlier pass. No
`ACTIVE-MUTATION.json` existed before the run and none exists after it; only `pristine/` remains under the
scratch root.

**R-E1 — `examples/fakeshop/apps/products/schema.py::EntryType.get_queryset`**

- Scope as run, Worker 2's verbatim: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE examples/fakeshop/test_query/test_products_api.py examples/fakeshop/apps/products/tests/test_schema.py`
- Pre-mutation state of that scope, measured by this pass: `132 passed`, pytest exit 0; pre-existing failing rows differenced out: 0.
- Collection / setup errors: **0**. Mutant pytest exit code 1 (`2 failed, 130 passed`) — a valid count.
- Failing node ids (2):
  - `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_everything[allEntries]`
  - `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_private_rows_hidden_from_non_staff[allEntries]`
- Restore proved by byte comparison: `filecmp.cmp(shallow=False)` -> `True`, `sha256 cd91fe508c5fd8a2... == cd91fe508c5fd8a2...` against this pass's own pre-mutation copy.

**R-E2 — `examples/fakeshop/apps/products/schema.py::PropertyType.get_queryset`**

- Same scope, same pre-mutation state (`132 passed`, exit 0, 0 differenced rows), collection/setup errors **0**, mutant exit code 1 (`2 failed, 130 passed`).
- Failing node ids (2):
  - `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_everything[allProperties]`
  - `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_private_rows_hidden_from_non_staff[allProperties]`
- Restore proved by byte comparison: `filecmp.cmp(shallow=False)` -> `True`, matching sha256.

**Comparison with Worker 2's record: the node-id SETS are identical, boundary for boundary**, at the same
recorded scope and against the same `132 passed` pre-mutation baseline with 0 collection/setup errors on
both sides. Nothing here rests on a count.

**The mutation removes the boundary rather than perturbing code near it.** With
`user = getattr(info.context, "user", None)` the stock `StrawberryDjangoContext` binds `user` to `None`, so
`if user and user.is_staff` and `elif user and user.has_perm(...)` are both unreachable and every request
falls through to the public-only cascade — the staff short-circuit is *gone*, not merely reordered. The
failing rows corroborate it: exactly the staff rows of the mutated hook's own root field fail, and no
other row moves.

**Tree state after the re-run, verified independently of the tool:**
`git status --short examples/fakeshop/apps/products/schema.py` is empty, `git diff --stat --` on the same
path is empty, and `shasum -a 256` reports
`cd91fe508c5fd8a2a77ba03da4464bce7378ccb5a040834a4fe959b4974c4196` — the same digest both passes recorded,
so the file is byte-identical to `HEAD` and no mutation survives. `git checkout` / `git restore` /
`git stash` were never invoked on any path.

**Where the second pair of eyes landed:** both recorded boundaries were re-run; **none** was accepted on
Worker 2's record alone. The floor obliged both (2 rows each, and both are data-isolation decisions), so
the re-run set is the whole set rather than a sample.

### High:

None.

### Medium:

None.

### Low:

#### L1 — the build report's stated reason for dropping the trailing assertion is factually wrong (the drop itself is right)

`### Tests added or updated` and the plan both justify removing the shipped trailer as "it is false for
`Property` / `Entry` at this fixture volume". Re-derived against `HEAD`: the shipped line reads
`assert models.Category.objects.count() <= _RELAY_MAX_RESULTS` — hard-coded to `Category`, *not* to the
loop's `model` — so it was true (27 <= 100) and could not have been false for `Property` or `Entry`, which
it never named. What is true is the weaker statement: **generalized** to the parametrized `model` it would
be false, so it could not travel to a four-field matrix.

The code change is correct and nothing is lost. The trailer's real job was to keep the shipped
count-equality honest for `Category` by asserting the page was not truncated; the cap-aware
`expected` list subsumes that for every model. Severity is Low because only the report's prose is wrong.
Recommended change: restate the reason as "not generalizable to the parametrized model", in the build
report only — no code edit.

#### L2 — the plan's repeated-literal claim is falsified by re-measurement

`### DRY analysis` states the repeated string literals the shadow overview flags "go **down**, not up".
Re-running `scripts/review_inspect.py examples/fakeshop/test_query/test_products_api.py --output-dir
docs/shadow` against the landed diff:

| literal | plan's pre-diff count | measured post-diff |
|---|---|---|
| `allItems` | 16x | **17x** |
| `allCategories` | 11x | **12x** |
| `view_category_1` | 5x | **6x** |
| `products.category` | 40x | 40x (held, as predicted) |

Each root-field name went **up by one**, because `pytest.param("allCategories", ..., id="allCategories")`
writes it twice where the shipped in-body loop tuple wrote it once. The derived-type-name half of the
claim is correct: `products.category` did not grow, exactly as the plan argued.

The +1 buys the readable `[allCategories]` node ids the round depends on, so this is a wrong claim rather
than a wrong choice. No code change recommended; the finding exists because a stated count that nobody
re-derives propagates (`BUILD.md` `## Claims are proven mechanically, never accepted on prose`).

### DRY findings

- **D1 — the ORM page-expectation comprehension is duplicated verbatim across the two new tests.**
  `examples/fakeshop/test_query/test_products_api.py:2315-2318` (`expected`, in T1) and `:2343-2346`
  (`page_gids`, in T2) are the same four lines character-for-character:
  `_global_id(model._meta.label_lower, pk) for pk in model.objects.order_by("pk").values_list("pk", flat=True)[:_RELAY_MAX_RESULTS]`.
  It is the one place the pk-ordering and the page cap are coupled, so it is also the line most likely to
  drift out of step between the two rows. A module-level `_cascade_page_gids(model)` beside
  `_CASCADE_ROOT_FIELDS` would single-site it at two real call sites.
  **Not held against the pass.** `### DRY analysis` decided "one constant, no functions" at plan time and
  `### Implementation notes` records that Worker 2 wrote exactly this helper and reverted it to obey the
  plan — the correct behaviour. The plan's stated threshold ("extract when a **third** test needs the same
  id-list extraction") was written about the *response*-side `edges -> ids` extraction, which T2's local
  `node_ids` closure now owns and which genuinely has one reader; it did not rule on the *ORM*-side
  expectation, which has two. Routed to Worker 1 below as a plan-level call, not a build defect.
- **Existence challenge on `_CASCADE_ROOT_FIELDS`: raised and answered no.** It has two real callers, both
  in this file, and deleting it means writing the same four-row table twice in adjacent functions — the
  duplication the round was most at risk of. The tuple carries only data (field name, model, username), adds
  no indirection layer, and is the seam a fifth root field would be added at. It should exist.
- **Cross-cohort duplication review: not applicable.** The build plan declares `none; sequential` for R3 —
  one cohort, one file — so there is no sibling cohort diff to compare added guards or error shapes against.
- No other near-copy: the two bodies are a single-actor page-identity assertion and a three-actor membership
  differential. Neither collapses into the other behind a flag, so this is not the file's seventh
  near-identical cascade body — it is six plus two genuinely different ones.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` — **empty**. `__all__` and the re-export list are
unchanged, as the round preamble requires (this round lands no production code at all;
`git diff --name-only HEAD -- django_strawberry_framework/` is likewise empty).

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. This cycle edits no doc surface
at all — the maintainer-set scope in `docs/builder/build-034-permissions-0_0_10.md` confines it to spec
files and `.py` files, and R3's own scope narrows that to one test file.

### What looks solid

- **The assertion is distinguishing, and it is distinguishing for the reason the plan gave.** T1 pins an id
  **list** against `model.objects.order_by("pk")...[:_RELAY_MAX_RESULTS]`, not a count. Checked against the
  trap the plan named: `min(model.objects.count(), _RELAY_MAX_RESULTS)` really does collapse to the
  constant `100` for `Property` and `Entry`, and the mutated staff page really is a different *membership*
  at the same or near-same cardinality, so cardinality was the wrong subject. The landed code is not a
  count in disguise: no `len()` appears in any assertion expression — the two `len()` calls sit inside the
  failure **message** tuple, where they cannot pass or fail anything.
- **The ordered comparison is contractually grounded, not a SQLite accident.** No products model declares
  `Meta.ordering` and none is a keyset target, so `connection.py::_finalize_queryset` ->
  `optimizer/plans.py::effective_connection_order` -> `deterministic_order` resolves to `("id",)` and the
  connection issues `ORDER BY id`. `order_by("pk")` on the ORM side is the same order by construction.
- **No `set(anonymous) < set(staff)` subset assertion crept in**, and the docstring states at the site why
  subset is unsound at cap volume. Confirmed by reading: the only membership operators in T2 are
  `hidden_gid in / not in <list>` on a single row.
- **The non-vacuity guards are real and correctly directed.** T1 asserts
  `model.objects.filter(is_private=True).exists()` per model — strictly stronger than the shipped
  `Category`-only version. T2 asserts `hidden is not None`, asserts `hidden_gid in page_gids` so a
  pagination miss cannot masquerade as a permission result, and asserts both non-staff pages non-empty
  before it asserts anything is absent from them. Each of those failing is the safe direction.
- **The parametrization really does produce four node ids per test.** Verified in the focused run's own
  listing and independently in both failability re-runs, where the failing rows arrive suffixed
  `[allEntries]` / `[allProperties]` — a single-node-id shape could not have produced 2 failing rows per
  hook. The shipped one-node-id loop is gone.
- **Both names keep the `cascade` substring**, so the declared `-k cascade` floor scope still covers them
  (`test_cascade_staff_sees_everything`, `test_cascade_staff_sees_private_rows_hidden_from_non_staff`).
- **Fixtures follow `AGENTS.md`.** Both tests open with `create_users(1)` as the literal first statement,
  then `seed_data(1)`, then `seed_cascade_split()`; no user is hand-rolled. Read against
  `apps/products/services.py::create_users`: `staff_<n>` is created with `is_staff=True` and no
  `is_superuser`, and no assertion in either test reads `is_superuser` — the `staff_1` login goes through
  the shipped `_login` helper and the `is_staff` short-circuit only.
- **No fail-open shape in the diff.** Hunted for the `BUILD.md` catalogue: no clamp, no `getattr` default,
  no `or` fallback, no bare or broad `except`, no default reached on incoherent input. The two truthiness
  tests (`assert anonymous_ids`, `assert view_ids`) are non-vacuity guards whose falsy case *fails* the
  test; the page payload is read as `payload["data"][field]["edges"]` with no `.get()` default, so a missing
  key raises rather than yielding an empty list that would satisfy every `not in` below it.
- **Repo conventions.** `uv run ruff format --check` -> `1 file already formatted`; `uv run ruff check` ->
  `All checks passed!`; `scripts/check_trailing_commas.py --check` -> exit 0; the file is ASCII-only
  (`LC_ALL=C grep -n '[^ -~]'` returns nothing); no line the diff adds exceeds 99 columns (the file's five
  over-110 lines are all pre-existing and outside the hunks, and `E501` is in the `examples/**/*.py`
  per-file ignore list anyway). `_view_username` needs no `noqa` because `ARG` is in that same ignore list —
  Worker 2's implementation note states this and it re-derives correctly from `pyproject.toml`.
- **No process provenance in the new comments or docstrings.** Both docstrings state what the row pins and
  why the shape was chosen; the only external reference is `spec-034`, which is the permitted design
  pointer. No round id, finding id, revision number, or build-plan step appears.
- **Floor verification happened as recorded.** Corroborated rather than re-run: `/tmp/dsf-floor-034` exists,
  `/tmp/dsf-floor-034/bin/python -V` -> `Python 3.10.19`, and
  `uv pip list --python /tmp/dsf-floor-034/bin/python` reports `django 5.2.16`,
  `strawberry-graphql 0.316.0`, `django-strawberry-framework 0.0.14` (editable), `channels 4.3.2`,
  `pytest 9.1.1`. Those match `docs/builder/BUILD.md` `## Floor verification` read at review time — Django
  **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0** — taken from that section, not from the
  build report or from memory. The record carries the venv path, the versions as read by
  `uv pip list --python <venv>/bin/python`, the focused scope, and pass/fail (`13 passed`, exit 0). The
  shared `.venv` is untouched: it still reports `Python 3.14.2`, `django 6.1`, `strawberry-graphql 0.324.0`,
  so no floor version leaked into it.
- **Checklist audit.** Both `### Dispatched findings checklist` boxes are ticked and both ticks have a
  matching fix in the diff. **B4a** conditioned its tick on all four root fields being covered by the staff
  matrix: `_CASCADE_ROOT_FIELDS` carries `allCategories` / `allItems` / `allProperties` / `allEntries` and
  both tests parametrize over it, so the matrix is four-wide, not two. **H1** conditioned its tick on a
  non-zero node-id-listed after-set for both E1 and E2: recorded at 2 rows each and independently
  reproduced above. No box is ticked without a fix, and no box is unaddressed.
- **Churn classification is accurate.** `git diff --name-only HEAD -- django_strawberry_framework/ examples/
  tests/` returns `examples/fakeshop/db.sqlite3`, `examples/fakeshop/test_query/test_products_api.py`,
  `tests/test_build_kanban_html.py` — the first and third are on the build plan's baseline-dirty list, and
  the concurrent R2 round's `docs/SPECS/spec-034-permissions-0_0_10.md` plus the untracked rationale
  companion are dirty as the preamble predicts. None was edited or reverted by this review.
- **Test-staleness determination re-derived independently of the diff's file list.** The two shapes
  `BUILD.md` `### Test staleness a focused run cannot see` names are a model field-set change and a
  wire-shape conversion. Neither is present: the diff adds no `fields=` / `exclude=` list and no editable-
  column or identity expectation, and it queries the four root connection fields that already exist with
  the `edges { node { id } }` envelope unchanged. The narrow focused scope is legitimate.

### Temp test verification

- **No temp *test* was written by this review.** The instrument for this finding class is a mutation against
  shipped code, not a scratch test file, and no review suspicion needed one to settle.
- Worker 2's proof manifest and emitted report: `docs/builder/temp-tests/034-r3/proofs.json`,
  `docs/builder/temp-tests/034-r3/proofs-report.md`. **Disposition: kept for the cycle** as the build
  report's underlying record; gitignored scratch, cleared by `scripts/clean_up.py` at the next cycle's
  pre-flight. Nothing in them needs promotion — they are proof records, not tests.
- This review's own manifest and report: `docs/builder/temp-tests/034-r3-review/proofs.json`,
  `docs/builder/temp-tests/034-r3-review/proofs-report.md`. **Disposition: kept for the cycle**, same
  gitignored-scratch basis. Written fresh rather than reusing Worker 2's file so the re-run is independent
  in its inputs as well as its execution.
- Static helper: `scripts/review_inspect.py examples/fakeshop/test_query/test_products_api.py
  --output-dir docs/shadow` was **run** this pass (required — the diff adds 84 lines to a file outside
  `django_strawberry_framework/`, over the 50-line trigger), producing
  `docs/shadow/examples__fakeshop__test_query__test_products_api.overview.md` and its `.stripped.py`. Read
  for the **Repeated string literals** section, which is the evidence behind L2. No skip to record.

### Notes for Worker 1 (spec reconciliation)

- **The `## Test plan` amendment Worker 2 offers is correct and complete, and it is yours to take or
  decline — I did not touch the spec.** Verified against the current file: `## Test plan`, Slice 4 list,
  still reads exactly `- \`test_cascade_staff_sees_everything\`.` and names no sibling. Both proposed names
  exist on disk under exactly those spellings, the first survives parametrization with its function name
  unchanged, and the Slice 4 fixture note above that list already carries the staff-not-superuser caveat,
  so the amendment needs nothing added to it. **Whether the concurrent R2 round has already applied it is
  not determinable from this pass** — that artifact is outside my write and read scope for this round, and
  the file is dirty under R2 as I read it. Check R2's own record before applying, or the sibling bullet
  lands twice.
- **Slice 4 box 2 and Definition-of-done item 10 need no change**, confirmed by reading both: box 2's
  "staff sees everything" and item 10's "anonymous / per-`view_<model>` / staff matrix" are now true across
  all four root fields for the first time. Both were correct contracts describing an unlanded code half.
- **Escalated (DRY, plan-level): D1, the two-site ORM page-expectation comprehension.** Resolution paths:
  (a) accept as-is — two occurrences in adjacent bodies, the plan's "no functions" call stands;
  (b) extract `_cascade_page_gids(model)` as a module-level helper beside `_CASCADE_ROOT_FIELDS`, which
  single-sites the pk-order + page-cap coupling at its only two readers. Not held at `revision-needed`:
  Worker 2 implemented the plan as written, and reverting the helper it had drafted was the correct call
  for a builder, not a defect. This is the plan's decision to revisit, not the build's.
- **Observation, not a finding: T1's assertion is now coupled to the connection's default ORDER BY.** It is
  sound today by contract (`deterministic_order` resolves to `("id",)` with no `Meta.ordering` and no
  keyset target). If a later card gives any of the four models a `Meta.ordering`, all eight staff rows go
  red for an ordering reason rather than a permission one. Worth knowing, not worth weakening the pin for —
  a set comparison would not help, because at cap volume the *window* itself moves with the order.
- **R1c's M1 ordering held.** T2 asserts the `view_<model>` actor explicitly for all four models, so a
  future collapse of the `view_<model>` branch into the fall-through would be performed against a suite
  that can detect a mistake in it. M1 remains the maintainer's call and nothing here acts on it.
- **Not touched, as escalated:** the 18 rotted card ids in `examples/fakeshop/apps/products/schema.py`. The
  file is byte-identical to `HEAD` after this review's transient proofs, digest
  `cd91fe508c5fd8a2a77ba03da4464bce7378ccb5a040834a4fe959b4974c4196`.

### Review outcome

`review-accepted`. Both dispatched findings are closed by the diff and both are closed by a **measurement**
rather than by the presence of a test: the round converted R1c's 0-of-125 result on `EntryType` into 2
failing rows, produced the same for the previously unmeasured `PropertyType` twin, and my independent
re-run reproduces both node-id sets exactly at the recorded scope with 0 collection/setup errors and a
proved byte-identical revert. The two Low findings (L1, L2) are prose-only, are recorded here rather than
sent back, and neither affects the shipped assertions. The one DRY finding is escalated to Worker 1 as a
plan-level call, per `worker-3.md` `### The existence challenge`. No High or Medium finding was found.

---

## Final verification (Worker 1)

**Outcome: `revision-needed`, on one point only — the escalated DRY call, decided in favour of consolidation.** Everything else in this round verifies: both dispatched contracts landed, both failability proofs reproduce a third time at identical node-id sets, the focused scope runs green, no staged anchor survives, no mutation survives, and no fail-open shape is in the diff. The re-loop is a three-line mechanical change in one test file, named exactly below.

### Diff and plan conformance

The diff is one source-or-test file, `examples/fakeshop/test_query/test_products_api.py` (`+84 / -12`), read in full against the plan. Every numbered implementation step landed as written: the module constant, the parametrization of the kept function name, the sibling test, the two docstrings, the scoped `ruff` runs, the focused run, the failability proof, the floor run. Nothing was rejected, nothing silently dropped. The one attempted deviation (two module-level helpers) was reverted inside the build pass and is recorded in `### Implementation notes` rather than presented as plan drift, which is the correct disposition.

### Step 3 — `### Dispatched findings checklist` audit

Both boxes carry a `- [x]`, and I am no longer the original ticker. Each is audited against the diff, not against the build report's prose.

- **B4a — tick CONFIRMED, box stays `- [x]`.** Its stated tick condition is "all four root fields are covered by the staff matrix, not two of four". Verified in the diff: `_CASCADE_ROOT_FIELDS` carries four `pytest.param` rows (`allCategories`, `allItems`, `allProperties`, `allEntries`), both staff tests parametrize over that one tuple, and the shipped two-element in-body `for field, model in (("allCategories", models.Category), ("allItems", models.Item)):` loop is gone from the file. Corroborated by the node ids my own focused run reported: four `::test_cascade_staff_sees_everything[...]` rows and four `::test_cascade_staff_sees_private_rows_hidden_from_non_staff[...]` rows.
- **H1 — tick CONFIRMED, box stays `- [x]`.** Its stated tick condition is "`### Failability proofs` records a non-zero, node-id-listed after-set for both E1 and E2 — the fix here is the measurement, not the presence of a test". The record exists, carries both entries, and I re-ran it myself rather than reading Worker 3's acceptance as discharge (`worker-1.md` `### Verifying relocation / promotion claims`). Numbers below.
- **No box is left `- [ ]`**, so no deferral reason is owed under step 3.

### Failability record — existence check, and my own independent re-run

**The record EXISTS and carries every field `docs/builder/BUILD.md` `### What gets recorded` requires**, for both entries: the exact mutation applied, the scope as run, the pre-mutation state of that scope, the failing node ids listed one per row with the count read as their `len()`, the collection/setup error count recorded *separately* at 0, and the revert proved by byte comparison rather than asserted in prose. No entry is zero-row, so no `why 0` judgement is owed and none is missing.

**Third independent reproduction (mine), through `scripts/prove_failability.py` with a manifest and scratch root of my own, both outside the repository.** The anchor pre-check ran first and standalone (`--check-anchors-only`, exit 0): each anchor matched exactly once, which is independently the evidence that the tree carried no live mutation before I started.

| entry | boundary | pre-mutation scope state | collection/setup errors | failing node ids | restore |
|---|---|---|---|---|---|
| E1 | `examples/fakeshop/apps/products/schema.py::EntryType.get_queryset` | `132 passed`, pytest exit 0; pre-existing failing rows differenced out: 0 | 0 | `::test_cascade_staff_sees_everything[allEntries]`, `::test_cascade_staff_sees_private_rows_hidden_from_non_staff[allEntries]` | `filecmp.cmp(shallow=False)` -> `True`, `sha256 cd91fe508c5fd8a2... == cd91fe508c5fd8a2...` |
| E2 | `examples/fakeshop/apps/products/schema.py::PropertyType.get_queryset` | `132 passed`, pytest exit 0; differenced out: 0 | 0 | `::test_cascade_staff_sees_everything[allProperties]`, `::test_cascade_staff_sees_private_rows_hidden_from_non_staff[allProperties]` | same, matching digest |

Scope as run, byte-identical to Worker 2's and Worker 3's so the sets are comparable: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE examples/fakeshop/test_query/test_products_api.py examples/fakeshop/apps/products/tests/test_schema.py`. Mutant exit code 1 (`2 failed, 130 passed`) on both. **The node-id sets are identical to Worker 2's and to Worker 3's, boundary for boundary** — three independent runs, one set. Both clear `### Acceptance rule` at 2 rows; neither is weakly pinned. R1c's measured **0 of 125** on `EntryType` is now **2**, which is the round's deliverable and it is a measurement, not a claim.

**No mutation survives.** `git diff HEAD -- examples/fakeshop/apps/products/schema.py` is empty; `shasum -a 256` on that path reports `cd91fe508c5fd8a2a77ba03da4464bce7378ccb5a040834a4fe959b4974c4196`, the digest both prior passes recorded. No `ACTIVE-MUTATION.json` exists anywhere under the repository or under any of the four scratch roots this cycle used; each holds only `pristine/`. `git checkout` / `git restore` / `git stash` were never invoked, on any path.

### Fail-open shapes — the diff read for the catalogue

Confirmed absent, by reading the diff rather than by trusting the green run. The class the brief names — a truthiness test that silently passes on an empty page — is the one to look for, and it is inverted here in the safe direction: `assert anonymous_ids` and `assert view_ids` **fail** on an empty page, and they are placed *before* the three `not in` assertions precisely so an empty page cannot satisfy an absence. The page is read as `payload["data"][field]["edges"]` with direct indexing and no `.get()` default, so a missing key raises rather than yielding `[]`. T1's `assert model.objects.filter(is_private=True).exists()` is the same shape of guard against a vacuous equality. No clamp, no `getattr` default on a value that matters, no `or` fallback, no bare or broad `except`, no default reached on incoherent input. The two `len()` calls sit inside failure-message tuples, where they cannot pass or fail anything.

### Step 5 — focused run

`uv run pytest examples/fakeshop/test_query/test_products_api.py -k cascade --no-cov -q -p no:randomly` -> **`13 passed`**, exit 0. No `--cov*` flag; `--no-cov` only, as `pytest.ini`'s auto-applied `--cov` requires. It runs.

### Step 6 — staged-anchor sweep

`grep -rn 'TODO(spec-034' .` (`.git/` excluded) returns **one** hit and it is not an anchor: `docs/SPECS/spec-034-permissions-0_0_10.md` `## Implementation plan`, the sentence *describing* the staged-anchor discipline (`a source-site TODO(spec-034 Slice N) comment naming this spec and the owning slice`). No source or test file carries a `TODO(spec-034 ...)` anchor, so nothing this round shipped left one behind.

### Step 4 — DRY across this round and the prior accepted cohorts, and the escalated call

**The escalated D1 call is decided: consolidation IS warranted. This is what `revision-needed` is set for, and it is the only open item.**

Verified against current source first — Worker 3's `:2315-2318` / `:2343-2346` have shifted by one line under a later formatting-neutral read; the live sites are `examples/fakeshop/test_query/test_products_api.py:2315-2318` (`expected`, in T1) and `:2343-2346` (`page_gids`, in T2), and the two four-line comprehensions are character-for-character identical:

```python
    [
        _global_id(model._meta.label_lower, pk)
        for pk in model.objects.order_by("pk").values_list("pk", flat=True)[:_RELAY_MAX_RESULTS]
    ]
```

**Why the plan's rule does not reach it.** Worker 3 read the plan correctly. `### DRY analysis`'s "one constant, no functions" and its "extract only if a **third** test needs the same id-list extraction" threshold were argued about the **response**-side `edges -> ids` extractor, which has one reader and which T2's local `node_ids` closure now owns. The plan never ruled on the **ORM**-side window. So this is an open question, not a settled one, and it is mine.

**The existence challenge, run before the consolidation.** Per `worker-1.md` `## Integration pass` and `BUILD.md`'s DRY-first rule, the higher-quality fix is often a deletion, so I asked whether either site needs to exist at all:

- T1's `expected` is the assertion itself — staff's page **is** the unfiltered page. It cannot be deleted.
- T2's `page_gids` guards a real failure mode: the private row must fall inside the page the query returns, or the `hidden_gid in staff_ids` half fails for pagination reasons rather than permission ones. `hidden = ...filter(is_private=True).order_by("pk").first()` is **not** guaranteed to sit inside the first `_RELAY_MAX_RESULTS` pks in general, so the guard is load-bearing and cannot be deleted either.
- Nor can it be derived from the response: deriving the page window from staff's own returned list is circular against the assertion it guards.

So no deletion is available, and the window must be stated twice or once behind a name. **Consolidation is the only remaining route, which is what makes it the right one here.**

**Package-wide helper inventory, and the existing-helper check, both run before proposing the helper** (`worker-1.md` `### Package-wide helper inventory before helper planning`). Refreshed for the whole package this pass and grepped for the shapes this needs (`page`, `global_?id`, `relay_max`, `gid`, `pks`, `window`, `cap`): **no package-side candidate**, and none should exist — this is an example-project test concern. In the test file itself: `::_global_id` encodes **one** pk and is reused by the proposed helper, not replaced; `::_login` and `::_staff_client` are login helpers; `::_login_with_perm` grants model perms; nothing builds a page of ids. In `examples/fakeshop/apps/products/services.py`: `seed_data`, `create_users`, `delete_users`, `delete_data`, `seed_cascade_split` and three private seeding helpers — all fixture builders, none an expectation builder, and none serves this. **No existing fixture or helper serves it.**

**The shape I want** — name it, so the next pass has no design question left:

- **`_cascade_page_gids(model)`**, a module-level function in `examples/fakeshop/test_query/test_products_api.py`, placed in the live-cascade section immediately beside `_CASCADE_ROOT_FIELDS`.
- **Single responsibility:** return the model's own rows as wire GlobalID strings, in the connection's default pk order, truncated to `_RELAY_MAX_RESULTS` — i.e. the unfiltered page the connection would return for that root field. Nothing else: it takes no client, issues no request, and knows nothing about actors.
- **Its two readers, both in this file, both added by this round:** T1's `expected` becomes `expected = _cascade_page_gids(model)`; T2's `page_gids` local is deleted and its precondition becomes `assert hidden_gid in _cascade_page_gids(model), (field, hidden.pk)`.
- **Docstring** states why the order and the cap are the *connection's* and not the test's (no products model declares `Meta.ordering` and none is a keyset target, so `deterministic_order` resolves to `("id",)` and the connection issues `ORDER BY id`; the cap is `_RELAY_MAX_RESULTS`). No process provenance — no round id, no finding id, no build-plan step (`AGENTS.md`).
- **Nothing else changes.** Both assertion messages, both docstrings' substance, the parametrize tables, the fixture trio, the test names and their node ids all stay exactly as they are. The node-id sets the failability proofs difference against are therefore unchanged, and the re-review's re-run should reproduce the same 2-and-2.
- **Not acceptable as a substitute:** a pk-returning variant that leaves T1 writing the comprehension, which halves the duplication instead of removing it — the window expression `model.objects.order_by("pk").values_list("pk", flat=True)[:_RELAY_MAX_RESULTS]` is the thing that must exist once. Also not acceptable: splitting `_CASCADE_ROOT_FIELDS`, or promoting T2's `node_ids` closure to module level (it has one reader and the plan's rule *does* reach it).

**Why a named helper at two readers rather than the rule of three.** The duplicated lines are not a convenience wrapper; they are the single place where two independent facts about the connection — its default ordering and its page cap — are coupled into one expectation. Stated twice, they can be edited once, and the two staff tests then disagree about what "the page" is without either failing. That is a correctness coupling, and a correctness coupling earns a name at two sites where a convenience does not. Corroborating evidence rather than reasoning alone: Worker 2 wrote precisely this helper on its first draft and reverted it only to obey the plan (`### Implementation notes`) — the natural shape and the reviewer's independent reading both landed on it.

**No other duplication.** Checked across this round and the prior accepted cohorts: `_CASCADE_ROOT_FIELDS` survives its own existence challenge (two real callers, data only, no indirection layer, and the seam a fifth root field is added at); the two test bodies are a single-actor page-identity assertion and a three-actor membership differential and neither collapses into the other behind a flag; no fixture, login helper, or GlobalID encoder was re-authored; the `pytest.param(..., id=...)` shape matches the file's established style. R1a's own DRY finding (`permissions.py::_cascadable_edge_names` with zero production readers) is a different file, catalogued on R2, and untouched here.

### Worker 3's two Low findings — disposed

- **L1 — sustained, and the correction is recorded here** because `docs/builder/ARTIFACT.md` forbids editing a prior entry, so Worker 2's build report keeps its wording. Re-derived independently against `git show HEAD:`: the shipped trailer reads `assert models.Category.objects.count() <= _RELAY_MAX_RESULTS`, hard-coded to `Category` and not to the loop's `model`, and `Category` seeds 27 rows, so it was **true** and could never have been "false for `Property` / `Entry`" — it never named them. **The correct reason for the drop: the assertion is not generalizable to the parametrized `model`.** Generalized to `model` it would be false at this fixture volume, so it could not travel to a four-field matrix; its real job was keeping the shipped count-equality honest for `Category` by asserting the page was not truncated, and the cap-aware `expected` list subsumes that for every model. **The drop itself is correct and nothing is lost** — the code needs no change for L1.
- **L2 — sustained, and the falsified prediction is mine, so I own it.** `### DRY analysis` predicted the repeated string literals "go **down**, not up". Re-derived this pass by counting occurrences in the working file against `git show HEAD:` of the same file, independently of the tool Worker 3 used: `allItems` +1, `allCategories` +1, `view_category_1` +1, `products.category` unchanged. The deltas match Worker 3's re-measurement exactly. The cause is exactly as Worker 3 states: `pytest.param("allCategories", ..., id="allCategories")` writes the name twice where the shipped in-body loop tuple wrote it once. **It does not change the shape's justification.** The plan's justification for `_CASCADE_ROOT_FIELDS` was never the literal count — it was that the four-row table would otherwise be written twice in adjacent functions, which remains true and is why the constant survives its existence challenge above. The +1 per field buys the readable `[allCategories]` node ids that make the four-field matrix four *rows* rather than one, which is the entire point of the round. The half of the claim that was about the derived type names is correct and held: `products.category` did not grow. **This was a prediction, not a contract; it is corrected, not re-litigated.**

### Spec status-line re-verification (this spawn)

Read the spec's title, `Shipped in 0.0.10` identity paragraph, `Status:` line, `Owner:`, and `Predecessors:` end to end. **Nothing this cycle did falsifies any of them**, and R2 already corrected the two that were stale (the self-dating parenthetical, and the `## Slice checklist` preamble's "the work has not started"). The `Status:` line correctly reads SHIPPED (`0.0.10`) with all five slices final-accepted; this round adds live test rows to an already-shipped slice and changes no shipped behavior. **No header edit is owed and none was made.**

### Summary

R3 closes the cycle's single SKIPPED contract. The staff half of the spec-034 anonymous / `view_<model>` / staff matrix now covers all four products root connection fields instead of two: `::test_cascade_staff_sees_everything` is parametrized over a new `_CASCADE_ROOT_FIELDS` table and asserts staff's page as an id **list** against the model's own capped, pk-ordered rows (a count comparison collapses to the cap constant for `Property` and `Entry` and stops distinguishing), and a sibling `::test_cascade_staff_sees_private_rows_hidden_from_non_staff` pins the three-actor differential — one private row in staff's page, absent from both the anonymous and the `view_<model>` page, with both non-staff pages asserted non-empty first. R1c's High finding H1 is lifted out of weakly-pinned by measurement, not by the presence of a test: removing `EntryType.get_queryset`'s user read fails 2 rows where it failed 0 of 125 before, and the previously unmeasured `PropertyType` twin now fails 2 as well — reproduced identically by three independent passes. One item is open: the ORM page-expectation comprehension is duplicated verbatim at two sites and is consolidated behind `_cascade_page_gids(model)` in a follow-up build pass, which is why this round is `revision-needed` rather than `final-accepted`.

### Spec changes made (Worker 1 only)

One spec edit, in `docs/SPECS/spec-034-permissions-0_0_10.md`.

| Section | Trigger | Change and reason |
|---|---|---|
| `## Test plan` -> `### Slice 4 — examples/fakeshop/test_query/test_products_api.py (extend; live)`, the staff row | Worker 2's `### Notes for Worker 1`, confirmed by Worker 3 | The bare `- \`test_cascade_staff_sees_everything\`.` — the section's only bullet with no statement of what it pins — replaced by two bullets: the parametrized four-field staff row with the reason it is an id list rather than a count, and the sibling `test_cascade_staff_sees_private_rows_hidden_from_non_staff` with the membership-not-subset reason and its two non-vacuity guards. The Test plan named one staff row while the slice it describes now carries two, over four fields each. |

**The double-landing risk was checked before the edit, not after.** The concurrent R2 round (`docs/builder/bld-034-review-2-spec_reconciliation.md`, `final-accepted`) records 50 spec edits; its `## Test plan` edits are #35 (Slice 1 name census), #43 (Slice 1 harness note) and #50 (Slice 4 *last* bullet, the re-pin parenthetical). **None of them is the staff row**, and its `### Dispatched findings checklist` explicitly leaves B4a open as "not R2's — it routes to R3". Confirmed against the file itself rather than against R2's record alone: before this edit the Slice 4 list read exactly `- \`test_cascade_staff_sees_everything\`.` and `grep -rn 'sees_private_rows_hidden_from_non_staff' docs/` returned zero hits in either spec-family file. **The amendment was genuinely absent; it has now landed exactly once.**

**No history is narrated in the spec text.** The two bullets state the contract in the present tense — no `Post-ship`, no `Revision N`, no "as of", no amendment framing, matching R2's zero-occurrence baseline. (`grep` for those tokens returns two pre-existing hits, both the `## Current state` vintage-framing convention R2 deliberately kept, neither introduced here.)

**No rationale-companion bullet is owed.** `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md` was **not** edited. The edit records no rejected alternative, no retraction, and no derivation narrative — the spec's contract (`## Slice checklist` Slice 4 box 2, `## Definition of done` item 10) was correct all along and is untouched; only the Test plan's inventory of test names was incomplete against it. R2 set the precedent: its two Test-plan edits (#35, #50) likewise took no rationale bullet.

**Slice 4 box 2 and Definition-of-done item 10 need no change**, re-read end to end and confirmed: box 2's "staff sees everything" and item 10's "anonymous / per-`view_<model>` / staff matrix" describe the four-field contract correctly and are now true across all four root fields for the first time. Recorded so a later pass does not "reconcile" a contract that was never wrong.

**Not touched, as escalated:** the rotted card ids in `examples/fakeshop/apps/products/schema.py` and their coupled spec sites (the build plan's `## R1 outcome` routes every card-id spelling to the maintainer). Every `TODO-ALPHA-*` / `TODO-BETA-*` spelling in both spec-family files survives this pass byte-identical; this round writes no production file.

### Verification run

Every command below was run in this pass; the output is quoted as produced.

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-034-permissions-0_0_10.md
OK: 42 terms - all have glossary entries and at least one spec link.
# exit 0

$ uv run python scripts/check_citations.py --check
OK: 857 citations resolve (738 in 431 .py files, 119 in KANBAN.md).
# exit 0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-034-permissions-0_0_10.md
# no output, exit 0

$ uv run pytest examples/fakeshop/test_query/test_products_api.py -k cascade --no-cov -q -p no:randomly
13 passed in 6.96s
# exit 0

$ grep -rn 'TODO(spec-034' .          # .git/ excluded
docs/SPECS/spec-034-permissions-0_0_10.md:379:  # the sentence describing the anchor discipline; not an anchor
# no source or test anchor

$ git diff HEAD -- examples/fakeshop/apps/products/schema.py
# empty
$ shasum -a 256 examples/fakeshop/apps/products/schema.py
cd91fe508c5fd8a2a77ba03da4464bce7378ccb5a040834a4fe959b4974c4196
```

The glossary count is unchanged at 42, which is the expected result: this edit moved no term's only link, and the two new bullets introduce no project-specific term that was not already linked elsewhere in the file. The citation gate is likewise unchanged and expected — `scripts/check_citations.py` scopes to `path::Symbol` citations in `.py` files and `KANBAN.md`, and this pass wrote neither.

### Concurrent tree

Untouched and unreverted, exactly as it arrived: `BACKLOG.md`, `KANBAN.md`, `KANBAN.html`, `README.md`, `examples/fakeshop/db.sqlite3`, `scripts/_kanban_lib.py`, `scripts/build_kanban_html.py`, `scripts/build_kanban_md.py`, `tests/test_build_kanban_html.py`, and the untracked `0_0_14.md` / `docs/DIVERGENCE.md`. `git checkout` / `git restore` / `git stash` were never invoked, on any path, and `examples/fakeshop/db.sqlite3` was never reset — the focused run and every proof run used Django's in-memory test database.

### Final status

`revision-needed` — for the single named DRY consolidation and nothing else. Worker 0 dispatches Worker 2 for an apply-changes pass against `### Step 4` above (`_cascade_page_gids(model)`, its two readers, nothing else), followed by a Worker 3 re-review. Neither dispatched-finding box is un-ticked: B4a and H1 are both closed and stay `- [x]`, the spec edit is landed and gated, and the re-loop touches no assertion, no test name, and no node id.

---

## Build report (Worker 2, pass 2)

The one open item from `## Final verification (Worker 1)` `### Step 4` is landed: the ORM page-expectation comprehension now exists once, behind `_cascade_page_gids(model)`. Nothing else in the file changed. Both failability proofs were re-run against the consolidated tree and reproduce the **same node-id sets** three prior independent runs recorded — 2 rows for `EntryType`, 2 for `PropertyType`, at the same scope and the same `132 passed` baseline, which is the mechanical form of Worker 1's claim that this consolidation changes no behaviour. The floor run was re-run because this pass changes the code it covers: `13 passed`.

### Files touched

Grounded in `git status --short`, not memory.

- `examples/fakeshop/test_query/test_products_api.py` — the pass's only source-or-test edit. Adds the module-level `_cascade_page_gids(model)` beside `_CASCADE_ROOT_FIELDS`; `::test_cascade_staff_sees_everything`'s `expected` becomes `_cascade_page_gids(model)`; `::test_cascade_staff_sees_private_rows_hidden_from_non_staff`'s `page_gids` local is deleted and its precondition becomes `assert hidden_gid in _cascade_page_gids(model), (field, hidden.pk)`. Cumulative diff against `HEAD` for the whole round: `+95 / -12`.
- `docs/builder/bld-034-review-3-code_repair.md` — this build report and the `Status:` transition. No prior section was edited and neither `### Dispatched findings checklist` box was re-ticked or re-worded.
- `docs/builder/worker-memory/worker-2.md` — appended pass entry.
- `docs/builder/temp-tests/034-r3-pass2/proofs.json`, `docs/builder/temp-tests/034-r3-pass2/proofs-report.md` — this pass's fresh failability manifest and the tool's emitted report (gitignored scratch, cleared per cycle by `scripts/clean_up.py`). Written fresh rather than reusing `034-r3/proofs.json` so the re-measurement is independent in its inputs.

Every other path `git status --short` reports dirty is classified under `### Validation run`; none was edited or reverted.

### Tests added or updated

No test was added, renamed, or re-scoped. No assertion semantics changed, no parametrize id moved, no fixture moved, and both node-id sets are byte-identical to the ones the prior pass recorded — which the failability re-runs below prove rather than assert.

- `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_everything` — `expected` is now `_cascade_page_gids(model)`. The list it compares against is the same list; only the site that builds it moved.
- `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_private_rows_hidden_from_non_staff` — the `page_gids` local is gone; the pagination precondition reads `assert hidden_gid in _cascade_page_gids(model), (field, hidden.pk)`, same subject, same failure message tuple.

### Validation run

- `uv run ruff format examples/fakeshop/test_query/test_products_api.py` — **pass**, `1 file left unchanged`. Scoped to this pass's own file; never `.`.
- `uv run ruff check --fix examples/fakeshop/test_query/test_products_api.py` — **pass**, `All checks passed!`, no fixes applied.
- `uv run python scripts/check_trailing_commas.py --check examples/fakeshop/test_query/test_products_api.py` — **pass**, exit 0 (line length, explode-at-threshold layout, ASCII-only).
- `git status --short` after both ruff invocations — the only slice-intended modified path is `examples/fakeshop/test_query/test_products_api.py`. Classification of everything else, **reported not reverted**:
  - Baseline-dirty concurrent kanban work: `BACKLOG.md`, `KANBAN.html`, `KANBAN.md`, `README.md`, `examples/fakeshop/db.sqlite3`, `scripts/_kanban_lib.py`, `scripts/build_kanban_html.py`, `scripts/build_kanban_md.py`, `tests/test_build_kanban_html.py`, and the untracked `0_0_14.md`, `docs/DIVERGENCE.md`.
  - `docs/SPECS/spec-034-permissions-0_0_10.md` (modified) and the untracked `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md` — Worker 1's, this cycle's; read-only for this pass and not opened for writing.
  - Untracked cycle artifacts not written by this pass: `docs/builder/build-034-permissions-0_0_10.md`, `bld-034-slice-0-rationale_extraction.md`, `bld-034-review-1a-cascade_module.md`, `bld-034-review-1b-composition_pins.md`, `bld-034-review-1c-fakeshop_and_surface.md`, `bld-034-review-2-spec_reconciliation.md`.
  - `git checkout` / `git restore` / `git stash` were never invoked, on any path, and `examples/fakeshop/db.sqlite3` was never reset — every run used Django's in-memory test database.
- Focused run — `uv run pytest examples/fakeshop/test_query/test_products_api.py -k cascade --no-cov -q -p no:randomly` -> **`13 passed`**, exit 0. No `--cov*` flag anywhere; `--no-cov` only, as `pytest.ini`'s auto-applied `--cov` requires. The same 13 rows the prior pass listed; the four `[allCategories]` / `[allItems]` / `[allProperties]` / `[allEntries]` node ids of both staff tests are among them, unchanged.

### Failability proofs

Re-run in full because this pass changes the code the proofs' scope covers, and because Worker 1's acceptance of the consolidation rests on the claim that the node ids do not move — a claim of that shape is proven, never accepted on prose (`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`).

Performed through `uv run python scripts/prove_failability.py docs/builder/temp-tests/034-r3-pass2/proofs.json --output docs/builder/temp-tests/034-r3-pass2/proofs-report.md`. Scratch root **outside the repository** at `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/e3a7bb93-0439-4447-b248-b5509e0f6d36/scratchpad/failability-034-r3-pass2`. The anchor check ran **first and standalone** (`--check-anchors-only`, exit 0, nothing mutated and nothing run): both anchors matched **exactly once**, which is also the evidence that no prior pass left a mutation live. One boundary live at a time, each restored before the next started; run exit code `0` (every entry proved, none weakly pinned).

Scope as run, identical for both entries and both baselines, and byte-identical to the scope the three prior runs recorded so the sets are comparable:

```
uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE \
  examples/fakeshop/test_query/test_products_api.py \
  examples/fakeshop/apps/products/tests/test_schema.py
```

**E1 — `examples/fakeshop/apps/products/schema.py::EntryType.get_queryset`**

- **Exact mutation applied:** `user = getattr(getattr(info.context, "request", None), "user", None)` replaced by `user = getattr(info.context, "user", None)` — the form that binds `None` against the stock `StrawberryDjangoContext`, so `if user and user.is_staff` and `elif user and user.has_perm(...)` are both unreachable and every request falls through to the public-only cascade. The boundary is removed, not perturbed. Anchored on the four-line block ending `elif user and user.has_perm("products.view_entry"):` so exactly one of the four hooks moves.
- **Pre-mutation state of this scope, measured by this pass:** `132 passed`, pytest exit 0. Pre-existing failing rows differenced out: **0**.
- **Collection / setup errors: 0.** Mutant pytest exit code 1 (`2 failed, 130 passed`) — a valid count.
- **Failing node ids (2; the count is `len()` of this list):**
  - `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_everything[allEntries]`
  - `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_private_rows_hidden_from_non_staff[allEntries]`
- **Comparison with the expected set:** identical, node id for node id, to the set Worker 2 pass 1, Worker 3 and Worker 1 each recorded independently. Nothing to report as a difference.
- **Verdict: clears `### Acceptance rule`** (2 rows, not 0 or 1). Inside Worker 3's mandatory independent re-run floor (<= 3 rows).
- **Revert proved by byte comparison:** `filecmp.cmp(shallow=False)` -> `True`; `sha256 cd91fe508c5fd8a2... == cd91fe508c5fd8a2...` against this pass's own pre-mutation copy. Performed by the tool in a `finally`, before entry E2 began.

**E2 — `examples/fakeshop/apps/products/schema.py::PropertyType.get_queryset`**

- **Exact mutation applied:** the same replacement, anchored on the block ending `elif user and user.has_perm("products.view_property"):`.
- **Pre-mutation state of this scope:** `132 passed`, pytest exit 0. Pre-existing failing rows differenced out: **0**.
- **Collection / setup errors: 0.** Mutant pytest exit code 1 (`2 failed, 130 passed`) — a valid count.
- **Failing node ids (2):**
  - `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_everything[allProperties]`
  - `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_private_rows_hidden_from_non_staff[allProperties]`
- **Comparison with the expected set:** identical to all three prior runs.
- **Verdict: clears `### Acceptance rule`** (2 rows). Inside the re-run floor.
- **Revert proved by byte comparison:** `filecmp.cmp(shallow=False)` -> `True`; matching `sha256`.

**No zero-row entry, so no `why 0` judgement is owed.**

**What the unchanged sets establish.** The pre-mutation baseline is still `132 passed` and the failing sets are still the same four rows, so the consolidation moved no row into or out of the scope, split no node id, and changed no row's ability to detect the removed boundary. That is the mechanical form of Worker 1's `### Step 4` assertion that nothing but the site of the comprehension changes.

**Tree state after both proofs**, verified independently of the tool: `git status --short examples/fakeshop/apps/products/schema.py` prints nothing, `git diff --stat -- examples/fakeshop/apps/products/schema.py` is empty, and `shasum -a 256` reports `cd91fe508c5fd8a2a77ba03da4464bce7378ccb5a040834a4fe959b4974c4196` — the same digest every prior pass recorded, so the file is byte-identical to `HEAD`. The scratch root holds only `pristine/`: **no `ACTIVE-MUTATION.json`, no `RESTORE-FAILED.json`**. No mutation is live across this pass's `Status:` transition.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Re-run by this pass, not inherited: the floor run is the round's builder-pass obligation and this pass changes the code that run covers. Versions taken from `docs/builder/BUILD.md` `## Floor verification`, the single canonical statement, and **executed** rather than reasoned about.

- **Scratch venv path (outside the repo):** `/tmp/dsf-floor-034`, reused from the prior pass rather than rebuilt; every install it ever received carried an explicit `--python /tmp/dsf-floor-034/bin/python`. No install ran in this pass — the venv already resolved to the floor, verified by reading it rather than by assuming it.
- **Resolved versions, as read by `uv pip list --python /tmp/dsf-floor-034/bin/python`:** `django 5.2.16`, `strawberry-graphql 0.316.0`, `django-strawberry-framework 0.0.14` (editable, from the repo), `channels 4.3.2`, `pytest 9.1.1`, `pytest-django 4.14.0`. Interpreter: `/tmp/dsf-floor-034/bin/python -V` -> `Python 3.10.19`.
- **Focused scope run:** `/tmp/dsf-floor-034/bin/python -m pytest examples/fakeshop/test_query/test_products_api.py -k cascade --no-cov`
- **Result: PASS — `13 passed`**, exit 0, with all four `[allCategories]` / `[allItems]` / `[allProperties]` / `[allEntries]` node ids of both staff tests among the PASSED lines. No floor-only failure, so no production-compatible fix was needed.
- **Shared `.venv` untouched**, verified after the run: `uv pip list` still reports `django 6.1` / `strawberry-graphql 0.324.0` and `.venv/bin/python -V` is `Python 3.14.2`. No floor version leaked into it.

### Dispatched findings checklist

Both boxes were already `- [x]` and Worker 1's final verification audited and confirmed both. This pass adds no finding and closes none, so neither box was re-ticked or re-worded.

### Implementation notes

- **`_cascade_page_gids(model)` sits immediately after `_CASCADE_ROOT_FIELDS` and before the first staff test.** Both are the section's shared vocabulary — one names the matrix, the other names the window — so a reader arriving at either staff body has met both. Placing it after the constant rather than before it keeps the constant's `#:` comment adjacent to the tuple it documents.
- **The docstring states what the window IS and why the two facts are coupled there**, not that anything asked for it: the ordering and the cap belong to the connection (no `Meta.ordering`, no keyset target, so the deterministic order resolves to `("id",)`; an un-paginated page truncates at `_RELAY_MAX_RESULTS`), `order_by("pk")` is that same order by construction, and the two must move together or the two staff rows stop agreeing on what "the page" is. It also states the negative — the helper takes no client and issues no request — because that is what makes it an expectation rather than a second reading of the response.
- **Signature is `(model) -> list[str]`, annotated on the return only.** The parameter is a Django model class and annotating it would mean importing `django.db.models` into a module whose `models` name is already bound to `apps.products.models`; the return type is the load-bearing half and needs no import. `_global_id` above it is fully annotated because both its parameters are builtins.
- **T2's precondition calls the helper inline rather than keeping a named local.** The local existed only to be read once; with the window behind a name, `assert hidden_gid in _cascade_page_gids(model)` reads as the sentence the comment above it already states. The comment and the failure-message tuple `(field, hidden.pk)` are unchanged.
- **T1 keeps its `expected` local.** It is the assertion's subject and appears in the comparison and in the failure message's `len(expected)`; inlining it would make the assertion line read worse for no gain.

### Notes for Worker 3

- **The node-id sets are expected to be UNCHANGED, and that is the thing to check.** This pass consolidates a duplicated expression; Worker 1 accepted it on the explicit ground that behaviour does not move. Re-run at the recorded scope (`examples/fakeshop/test_query/test_products_api.py` plus `examples/fakeshop/apps/products/tests/test_schema.py`) and compare node-id **sets** against the four rows above — E1's two `[allEntries]` rows and E2's two `[allProperties]` rows. A set that differs would mean the consolidation changed behaviour, which is the finding; a set that matches is the confirmation. The pre-mutation baseline for that scope is still **132 passed** — unchanged by this pass, since no row was added or removed.
- **This pass's manifest is reusable as-is** at `docs/builder/temp-tests/034-r3-pass2/proofs.json`, and the tool's emitted report at `docs/builder/temp-tests/034-r3-pass2/proofs-report.md`. It is a fresh file, not the prior pass's, so a re-run against either is independent in its inputs.
- **Both boundaries are still at 2 rows, inside your mandatory re-run floor** (3 or fewer, and both are data-isolation decisions).
- **The diff is three sites in one file:** the new helper, T1's one-line `expected`, and T2's deleted local plus its rewritten precondition. Nothing else in the file moved — no test name, no parametrize id, no fixture, no assertion semantics, no docstring substance.
- **No shadow file was generated or consulted by this pass**, and `scripts/review_inspect.py` was not run: the diff is a three-site consolidation inside a section this cycle has already inspected twice.
- **`examples/fakeshop/apps/products/schema.py` is byte-identical to `HEAD`** (`cd91fe508c5fd8a2...`). It appears in this report only as the transient, byte-compare-proved mutation target.

### Notes for Worker 1 (spec reconciliation)

- **No plan-vs-implementation drift, structural or small.** `### Step 4`'s shape was implementable exactly as named — the helper, its two readers, and nothing else. No pause was triggered; the `worker-2.md` "Plan-vs-implementation drift" route was not taken.
- **The shape landed is Worker 1's, not the one drafted in pass 1.** Pass 1's reverted draft was a pair (`_cascade_page_ids(model)` returning pks, plus a response-side `_cascade_root_field_ids(field, client)` extractor). Only the ORM-side half exists now, it returns wire GlobalIDs rather than pks — the variant `### Step 4` explicitly rules out is the pk-returning one that would leave T1 writing the comprehension — and the response-side extractor stays as T2's local closure, whose one reader the plan's rule does reach.
- **No spec amendment is owed by this pass and none is offered.** The `## Test plan` amendment Worker 1 landed at final verification names both test functions; neither name, and no node id, changes here. The helper is a private test-file symbol the spec has no reason to name.
- **Nothing in the spec, the rationale companion, or any other cycle artifact was read as settled or written by this pass.**

---

## Review (Worker 3, pass 2)

Scope of this pass: the pass-2 diff only — the module-level `_cascade_page_gids(model)` helper beside
`_CASCADE_ROOT_FIELDS` and its two call sites. Everything accepted in pass 1 (the parametrization, the
id-list-equality assertion, the non-vacuity guards, the fixture trio) stays accepted and is re-opened only
where the pass-2 diff disturbs it; it does not.

**The pass-2 diff, derived here rather than taken from the build report.** The round's whole diff against
`HEAD` is one contiguous region of `examples/fakeshop/test_query/test_products_api.py`
(`git diff -U2 HEAD -- <path>`, three hunks, all inside the live-cascade section, `+95 / -12`). Pass 1
recorded `+84 / -12`, so pass 2 contributes `+11` net with the deletion count unmoved — arithmetically
consistent with exactly three sites and nothing else: the helper block (`+18`, two blank lines plus a
16-line `def`), T1's four-line `expected = [...]` comprehension collapsing to one line (`-3`), and T2's
four-line `page_gids = [...]` local plus its `assert hidden_gid in page_gids` collapsing to one inline
`assert` (`-4`). `18 - 3 - 4 = 11`. No test name, parametrize id, assertion operator, fixture call, or
docstring outside the two touched sentences moved.

### Independent failability re-run — mutations recorded BEFORE they are made

`worker-3.md` `### Reading is necessary, not sufficient` requires the mutation to be written into this
artifact before it is applied, and the mandatory floor obliges both entries again this pass (2 rows each,
and both are data-isolation decisions). **Both are re-run; nothing is accepted on Worker 2's pass-2
record.** Worker 1's acceptance of the consolidation rests on the claim that the node-id sets do not move,
which is exactly the shape `BUILD.md` `## Claims are proven mechanically, never accepted on prose` forbids
taking on prose.

- **R2-E1 — `examples/fakeshop/apps/products/schema.py::EntryType.get_queryset`.** Mutation to apply:
  replace `user = getattr(getattr(info.context, "request", None), "user", None)` with
  `user = getattr(info.context, "user", None)`, anchored on the four-line block whose fourth line is
  `elif user and user.has_perm("products.view_entry"):` so exactly one of the four hooks moves.
- **R2-E2 — `examples/fakeshop/apps/products/schema.py::PropertyType.get_queryset`.** The same
  replacement, anchored on the `products.view_property` block.
- Scope: the scope all three prior runs recorded, verbatim, so the sets are comparable.
- Manifest written fresh at `docs/builder/temp-tests/034-r3-review2/proofs.json` (this pass's own
  directory, not Worker 2's file and not my pass-1 file), scratch root **outside** the repository.
  Anchors checked standalone first; one boundary live at a time; each restore proved by byte comparison.

#### Measurements — both boundaries re-run, neither accepted on Worker 2's pass-2 record

Re-run through `uv run python scripts/prove_failability.py docs/builder/temp-tests/034-r3-review2/proofs.json
--output docs/builder/temp-tests/034-r3-review2/proofs-report.md`, scratch root
`/private/tmp/.../scratchpad/w3-pass2-failability-034-r3` (outside the repository). Run exit code `0`.

Anchor pre-check, standalone and first (`--check-anchors-only`, exit 0): both anchors matched **exactly
once**, which is the evidence that the consolidated tree carried no live mutation from any earlier pass. No
`ACTIVE-MUTATION.json` and no `RESTORE-FAILED.json` existed before the run or exists after it, anywhere in
the repository or under the scratch root, which holds only `pristine/`.

**R2-E1 — `examples/fakeshop/apps/products/schema.py::EntryType.get_queryset`**

- Scope as run, verbatim from the three prior records: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE examples/fakeshop/test_query/test_products_api.py examples/fakeshop/apps/products/tests/test_schema.py`
- Pre-mutation state of that scope, measured by this pass: `132 passed`, pytest exit 0; pre-existing failing rows differenced out: 0.
- Collection / setup errors: **0**. Mutant pytest exit code 1 (`2 failed, 130 passed`) — a valid count.
- Failing node ids (2):
  - `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_everything[allEntries]`
  - `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_private_rows_hidden_from_non_staff[allEntries]`
- Restore proved by byte comparison: `filecmp.cmp(shallow=False)` -> `True`, `sha256 cd91fe508c5fd8a2... == cd91fe508c5fd8a2...` against this pass's own pre-mutation copy.

**R2-E2 — `examples/fakeshop/apps/products/schema.py::PropertyType.get_queryset`**

- Same scope, same pre-mutation state (`132 passed`, exit 0, 0 differenced rows), collection/setup errors **0**, mutant exit code 1 (`2 failed, 130 passed`).
- Failing node ids (2):
  - `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_everything[allProperties]`
  - `examples/fakeshop/test_query/test_products_api.py::test_cascade_staff_sees_private_rows_hidden_from_non_staff[allProperties]`
- Restore proved by byte comparison: `filecmp.cmp(shallow=False)` -> `True`, matching sha256.

**The condition Worker 1's acceptance rests on holds, as a measurement.** The consolidation was accepted on
the explicit ground that the node-id sets do not move. They do not: **my sets are identical, node id for
node id, to the sets Worker 2 pass 1, my own pass 1, Worker 1's final verification, and Worker 2 pass 2
each recorded independently** — four prior runs plus this one, one set — at the same recorded scope, against
the same `132 passed` pre-mutation baseline, with 0 collection/setup errors on every side. The baseline is
also unmoved from pass 1's, so the consolidation added no row, removed none, and split no node id. Nothing
here rests on a count.

**The mutation still removes the boundary rather than perturbing code near it.** With
`user = getattr(info.context, "user", None)` the stock `StrawberryDjangoContext` binds `user` to `None`, so
`if user and user.is_staff` and `elif user and user.has_perm(...)` are both unreachable and every request
falls through to the public-only cascade. The failing rows corroborate it: exactly the staff rows of the
mutated hook's own root field fail, and no other row moves.

**Tree state after the re-run, verified independently of the tool:**
`git status --short examples/fakeshop/apps/products/schema.py` is empty, `git diff --stat --` on the same
path is empty, and `shasum -a 256` reports
`cd91fe508c5fd8a2a77ba03da4464bce7378ccb5a040834a4fe959b4974c4196` — the digest every prior pass recorded,
so the file is byte-identical to `HEAD` and no mutation survives. `git checkout` / `git restore` /
`git stash` were never invoked on any path, and `examples/fakeshop/db.sqlite3` was never reset.

**Where the second pair of eyes landed:** both boundaries re-run; **none** accepted on Worker 2's record.

### High:

None.

### Medium:

None.

### Low:

#### L3 — the recorded reason for leaving the helper's parameter unannotated does not hold as stated (the choice itself is right)

`### Implementation notes` (pass 2) states the signature is return-only-annotated because "annotating it
would mean importing `django.db.models` into a module whose `models` name is already bound to
`apps.products.models`". The obstacle as stated is avoidable: the annotation needs the **class**, not the
module, and `from django.db.models import Model` binds `Model` — there is no collision with the existing
`from apps.products import models`, and `model: type[Model]` is valid on the `py310` target.

**The choice is nonetheless correct and I am not asking for it to change.** `ANN` is in the
`"examples/**/*.py"` per-file ignore list in `pyproject.toml`, so nothing enforces it here, and the return
type is the load-bearing half for a reader. The only real evidence on the other side is local convention:
`_cascade_page_gids` is now the one module-level helper in this file whose parameter is unannotated —
`::_staff_client`, `::_global_id`, `::_login`, `::_login_with_perm` and `::_items_connection_page` all
annotate theirs.

Severity Low: report prose only, no behaviour and no lint consequence. Recommended change: restate the
reason as a convention/weight call (`type[Model]` costs an import for a rule this tree does not enforce),
or take the one-line import and annotate. Either is fine; no code edit is required to accept this round.

### DRY findings

- **D1 is genuinely resolved — the window is expressed once, and it was removed rather than relocated.**
  The four-line ordering-plus-cap comprehension that stood at two sites in pass 1 now exists at exactly one:
  `examples/fakeshop/test_query/test_products_api.py::_cascade_page_gids`. Verified by search rather than by
  reading the diff: `grep -rn '_RELAY_MAX_RESULTS\]' tests/ examples/` returns **one** line (`:2298`, inside
  the helper) and `grep -rn 'values_list("pk", flat=True)\[' tests/ examples/` returns three, of which the
  other two are `apps/products/services.py:403` and `:449` — seeding helpers slicing to a caller's `count`,
  a different subject with no page cap and no GlobalID, not a third near-copy. The helper's two readers are
  the two the plan named and nothing else (`:2333` T1's `expected`, `:2360` T2's inline precondition), so
  the duplication is gone and no third site was created to carry it.
- **The shape carries the coupling Worker 1 extracted it for.** `_cascade_page_gids` returns wire GlobalIDs,
  not pks, so T1 no longer writes any part of the window — the pk-returning variant Worker 1 explicitly
  ruled out (which would have halved the duplication instead of removing it) was not taken. Order and cap
  travel together inside the one function; neither reader can restate either.
- **Its docstring states the invariant, not the change's history.** It says what the window IS (the
  connection's own ordering and its `_RELAY_MAX_RESULTS` cap, coupled so the two staff rows cannot disagree
  about what "the page" is), why the order is contractual, and the negative that makes it an expectation
  rather than a second reading of the response (takes no client, issues no request). Grepped the added block
  for process provenance — round ids, pass numbers, `Revision N`, finding ids, worker names, build-plan
  steps: **zero hits**. It does not even take the permitted `spec-034` pointer.
- **The ordering grounding is preserved, not silently substituted.** The helper orders by `pk` and truncates
  to `_RELAY_MAX_RESULTS`, the same two facts pass 1 accepted. Re-derived at the framework rather than
  inherited: `examples/fakeshop/apps/products/models.py` declares no `Meta.ordering` on any of the four
  models (`grep -n ordering` returns nothing) and the app declares no keyset target, so
  `optimizer/plans.py::effective_connection_order` takes its second arm and
  `optimizer/plans.py::deterministic_order` returns `(model._meta.pk.attname,)` = `("id",)`. `order_by("pk")`
  is that order by construction. The docstring's claim re-derives correctly.
- **Existence challenge on `_cascade_page_gids`: raised and answered yes.** Two real readers, both live,
  neither deletable (T1's `expected` is the assertion; T2's precondition guards a pagination miss
  masquerading as a permission result, and cannot be derived from the response without circularity — Worker
  1 ran that check and it re-derives). What would break if it were inlined is exactly what it exists to
  prevent: two independently editable statements of one correctness coupling.
- **Existence challenge on `_CASCADE_ROOT_FIELDS`: unchanged from pass 1, still yes.** Two real callers,
  data only, no indirection layer, the seam a fifth root field is added at. Pass 2 did not disturb it.
- **Repeated-literal delta re-measured, and the consolidation moved none of it.** Re-ran
  `scripts/review_inspect.py examples/fakeshop/test_query/test_products_api.py --output-dir docs/shadow`
  against the consolidated file: `allItems` **17x**, `allCategories` **12x**, `view_category_1` **6x**,
  `products.category` **40x** — identical to my pass-1 measurement in every row. The `+1`-per-root-field
  delta L2 recorded belongs entirely to `pytest.param(..., id=...)` in pass 1; pass 2 added no literal and
  removed none.
- **Cross-cohort duplication review: not applicable.** The build plan declares `none; sequential` for R3 —
  one cohort, one file — so there is no sibling cohort diff to compare against.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` — **empty**. `__all__` and the re-export list are
unchanged. This round lands no production code at all: `git diff --name-only HEAD -- django_strawberry_framework/`
is likewise empty, and `examples/fakeshop/apps/products/schema.py` is byte-identical to `HEAD`
(`cd91fe508c5fd8a2a77ba03da4464bce7378ccb5a040834a4fe959b4974c4196`) after this pass's transient proofs.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. This cycle edits no doc surface
at all beyond the spec text Worker 1 owns; the pass-2 diff is one test file.

### What looks solid

- **The pass-2 diff is exactly the three sites Worker 1 named, and nothing else — derived, not taken on
  trust.** `git diff -U2 HEAD` on the test file is one contiguous region; the round total moved `+84/-12` to
  `+95/-12`, and the three sites account for `+18 - 3 - 4 = +11` exactly, with the deletion count unmoved.
  No test name, parametrize id, assertion operator, fixture call, or unrelated docstring changed.
- **No fail-open shape was introduced by the consolidation, and the guards that would catch one still fire
  first.** `_cascade_page_gids` returns `[]` for a model with no rows, which would make T1's
  `assert returned == expected` and T2's `not in` assertions vacuous — the exact shape to hunt. Both are
  closed **upstream of the helper**: T1 asserts `model.objects.filter(is_private=True).exists()` at `:2331`,
  *before* `expected` is built at `:2333`, so a model that could return `[]` fails the guard rather than the
  equality; T2's `assert hidden is not None` at `:2356` fires before the helper is called at all, and its
  precondition `assert hidden_gid in _cascade_page_gids(model)` **fails** on an empty list rather than
  passing. Every empty answer exits on the safe side. No clamp, no `getattr` default, no `or` fallback, no
  bare or broad `except` anywhere in the new code.
- **Still not a count in disguise.** `len()` appears twice in T1 and both occurrences sit inside the failure
  **message** tuple, where they cannot pass or fail anything. The assertion is `returned == expected` over
  id lists; moving the right-hand side behind a name did not turn it into a cardinality check.
- **The three-actor differential is intact.** T2 still asserts both non-staff pages non-empty before it
  asserts anything absent from them, and still reads the payload as `payload["data"][field]["edges"]` with
  direct indexing and no `.get()` default. Inlining the helper into the precondition changed the site that
  builds the window, not the order of the guards.
- **Repo conventions.** `uv run ruff format --check` -> `1 file already formatted`; `uv run ruff check` ->
  `All checks passed!`; `scripts/check_trailing_commas.py --check` -> exit 0; the file is ASCII-only
  (`LC_ALL=C grep -n '[^ -~]'` returns nothing); every line the round adds is <= 99 columns (measured over
  the added lines of `git diff HEAD`, longest is the 99-column comprehension line at `:2298`).
- **Floor verification is recorded as `docs/builder/BUILD.md` `## Floor verification` requires, and it was
  re-run rather than inherited.** Corroborated rather than re-executed: `/tmp/dsf-floor-034` exists,
  `/tmp/dsf-floor-034/bin/python -V` -> `Python 3.10.19`, and
  `uv pip list --python /tmp/dsf-floor-034/bin/python` reports `django 5.2.16`,
  `strawberry-graphql 0.316.0`, `django-strawberry-framework 0.0.14` (editable), `channels 4.3.2`,
  `pytest 9.1.1`, `pytest-django 4.14.0`. Those match the canonical numbers read from `BUILD.md`
  `## Floor verification` at review time — Django **5.2.16** on Python **3.10** with strawberry-graphql
  **0.316.0** — taken from that section, never from the build report or from memory. The record carries the
  venv path, the versions as read by `uv pip list --python <venv>/bin/python`, the focused scope
  (`-k cascade`), and pass/fail (`13 passed`, exit 0). The shared `.venv` is untouched: it still reports
  `Python 3.14.2`, `django 6.1`, `strawberry-graphql 0.324.0`, so no floor version leaked into it.
- **Checklist boxes untouched and still matched by the diff.** Both `### Dispatched findings checklist`
  boxes remain `- [x]` with their original wording (verified by reading them, not the build report's claim
  about them). B4a's tick condition — all four root fields in the staff matrix — still holds:
  `_CASCADE_ROOT_FIELDS` carries four rows and both tests parametrize over it. H1's — a non-zero,
  node-id-listed after-set for both entries — still holds and is now reproduced a fifth time. Pass 2 adds no
  finding and closes none, so nothing was owed here.
- **Churn classification is accurate.** `git status --short` reports only the build plan's baseline-dirty
  set (`BACKLOG.md`, `KANBAN.md`, `KANBAN.html`, `README.md`, `examples/fakeshop/db.sqlite3`,
  `scripts/_kanban_lib.py`, `scripts/build_kanban_html.py`, `scripts/build_kanban_md.py`,
  `tests/test_build_kanban_html.py`, untracked `0_0_14.md` / `docs/DIVERGENCE.md`), Worker 1's
  `docs/SPECS/spec-034-permissions-0_0_10.md` plus the untracked rationale companion, this cycle's untracked
  artifacts, and the one intended test file. None was edited or reverted by this review.

### Temp test verification

- **No temp *test* was written by this review.** The instrument for this class is a mutation against shipped
  code; no review suspicion needed a scratch test to settle, and the fail-open question was answered by the
  guard ordering at the two sites rather than by a demonstration.
- This pass's own manifest and emitted report: `docs/builder/temp-tests/034-r3-review2/proofs.json`,
  `docs/builder/temp-tests/034-r3-review2/proofs-report.md`. **Disposition: kept for the cycle**; gitignored
  scratch, cleared by `scripts/clean_up.py` at the next pre-flight. Written fresh rather than reusing Worker
  2's `034-r3-pass2/proofs.json` or my own pass-1 `034-r3-review/proofs.json`, so the re-run is independent
  in its inputs as well as its execution. Nothing in it needs promotion — it is a proof record, not a test.
- Worker 2's pass-2 manifest and report (`docs/builder/temp-tests/034-r3-pass2/`) and the three earlier
  cycle directories are left in place as the underlying records of their own passes.
- Static helper: `scripts/review_inspect.py examples/fakeshop/test_query/test_products_api.py
  --output-dir docs/shadow` was **run** this pass. Not required by `BUILD.md` `### When to run the helper
  during build` — the pass-2 diff adds 18 lines to a file outside `django_strawberry_framework/`, under the
  50-line trigger — but run anyway to re-measure the repeated-string-literal delta L2 recorded. No skip to
  record.

### Notes for Worker 1 (spec reconciliation)

- **D1 is closed. The escalation you decided in favour of consolidation is discharged as specified**, down
  to the two rejected variants: the helper returns wire GlobalIDs rather than pks (so T1 writes no part of
  the window), `_CASCADE_ROOT_FIELDS` was not split, and T2's `node_ids` closure stayed local. Nothing is
  escalated from this pass.
- **No spec amendment is owed and none is offered.** The `## Test plan` amendment you landed at final
  verification names both test functions; pass 2 changes neither name, no node id, and no assertion
  semantics, so the amendment stays true as written. `_cascade_page_gids` is a private test-file symbol the
  spec has no reason to name. I did not read the spec or the rationale companion as settled and wrote
  neither.
- **The observation from pass 1 stands and is now single-sited, which slightly improves it.** T1's assertion
  is coupled to the connection's default `ORDER BY`; sound today by contract (`deterministic_order` ->
  `("id",)`), and if a later card gives any of the four models a `Meta.ordering` all eight staff rows go red
  for an ordering reason rather than a permission one. After the consolidation that coupling has exactly one
  home, so a future card fixing it edits one docstring and one expression instead of two.
- **L3 is prose-only and yours to take or leave** (the recorded reason for the return-only annotation does
  not hold as stated; the choice it defends is right). No code change is recommended and the round does not
  hang on it.
- **R1c's M1 ordering still held.** T2 asserts the `view_<model>` actor explicitly for all four models; a
  future collapse of that branch into the fall-through would be performed against a suite that can detect a
  mistake in it. M1 remains the maintainer's call and nothing here acts on it.
- **Not touched, as escalated:** the rotted card ids in `examples/fakeshop/apps/products/schema.py`. The file
  is byte-identical to `HEAD` after this review's transient proofs.

### Review outcome

`review-accepted`. The one open item from your final verification is landed exactly as named and is closed
by measurement rather than by reading: the ORM page-expectation window now exists once, at
`::_cascade_page_gids`, grep-verified as the only occurrence in any of the three test trees, with its two
named readers and no third near-copy — the duplication is removed, not relocated. The condition your
acceptance rested on holds mechanically: my independent re-run of **both** boundaries reproduces the same
four node ids at the same recorded scope, against the same unmoved `132 passed` baseline, with 0
collection/setup errors and a byte-proved identical revert. No High and no Medium. The single Low (L3) is
report prose about a typing choice that is itself correct, is recorded rather than sent back, and touches no
shipped assertion.

---

## Final verification (Worker 1, pass 2)

**Outcome: `final-accepted`.** The single `revision-needed` item my first final verification set is discharged, it is the only thing that moved, and the condition the acceptance rested on holds as a measurement rather than as prose: my own independent re-run — the fifth for `EntryType`, the fourth for `PropertyType` — reproduces the same node-id sets against the same unmoved `132 passed` baseline. This pass is a single-item re-loop closure, not a re-verification of the round; everything accepted in pass 1 stays accepted and is re-opened only where the pass-2 diff disturbs it, which it does not.

### The `revision-needed` item, discharged — and nothing else moved

Read from the diff (`git diff -U6 HEAD -- examples/fakeshop/test_query/test_products_api.py`), not from the build report. The landed shape is the one I named, element for element:

- **Module-level, beside `_CASCADE_ROOT_FIELDS`.** `::_cascade_page_gids` is defined at `:2284`, immediately after the constant and before the first staff test — the first-listed placement in `### Step 4`.
- **Returns the model's rows as wire GlobalIDs in pk order truncated to `_RELAY_MAX_RESULTS`.** The body is `[_global_id(model._meta.label_lower, pk) for pk in model.objects.order_by("pk").values_list("pk", flat=True)[:_RELAY_MAX_RESULTS]]`. GlobalIDs, not pks — the variant `### Step 4` explicitly ruled out (which would leave T1 writing half the window) was not taken. It takes no client and issues no request.
- **T1's reader:** `expected = _cascade_page_gids(model)` at `:2333`.
- **T2's reader:** the `page_gids` local is gone; the precondition reads `assert hidden_gid in _cascade_page_gids(model), (field, hidden.pk)` at `:2360`, with the same failure-message tuple and the same comment above it.
- **Single-sited, verified by search rather than by reading the diff:** `grep -rn '_RELAY_MAX_RESULTS\]' tests/ examples/` returns exactly one line — `examples/fakeshop/test_query/test_products_api.py:2298`, inside the helper. The duplication is removed, not relocated, and no third site was created to carry it.

**Nothing else moved**, which is the condition my acceptance rested on and the reason a quietly-changed assertion would have falsified it whatever the proofs said:

- **Test names:** `::test_cascade_staff_sees_everything` and `::test_cascade_staff_sees_private_rows_hidden_from_non_staff`, both unchanged, both still carrying the `cascade` substring the declared floor scope selects on.
- **Parametrize table and ids:** the four `pytest.param(..., id=...)` rows of `_CASCADE_ROOT_FIELDS` are untouched; the argnames strings still differ only in the `_view_username` / `view_username` spelling pass 1 chose.
- **Assertion semantics:** T1 is still `assert returned == expected, (field, len(returned), len(expected))` over id lists, still preceded by `assert model.objects.filter(is_private=True).exists(), field` at `:2331`. T2 still asserts `hidden is not None` at `:2356`, then both non-staff pages non-empty, then `hidden_gid` in staff / not in anonymous / not in `view_<model>`. No operator, subject, or message tuple changed.
- **Fixtures:** `create_users(1)` remains the literal first statement of both, followed by `seed_data(1)` then `seed_cascade_split()`.
- **Arithmetic corroboration, re-derived rather than taken from the review:** the round's whole diff against `HEAD` is now `+95 / -12` where pass 1 recorded `+84 / -12`. The three sites account for `+18` (the helper block) `-3` (T1's four-line comprehension collapsing to one) `-4` (T2's four-line local plus its separate `assert` collapsing to one inline `assert`) `= +11`, with the deletion count unmoved. A fourth site would have to be line-count-neutral to hide in that; combined with reading the diff in full against what pass 1 recorded, and with the node-id reproduction below, the scoping holds.

### Failability record — existence check, and my own independent re-run

**The pass-2 record EXISTS and carries every field `docs/builder/BUILD.md` `### What gets recorded` requires**, for both entries: the boundary by symbol-qualified path, the exact mutation applied, the scope as run, the pre-mutation state of that same scope, the failing node ids listed one per row with the count read as their `len()`, the collection/setup error count recorded *separately* at 0, and the revert proved by byte comparison rather than asserted in prose. No entry is zero-row, so no `why 0` judgement is owed and none is missing. `### Hot-path budget` and `### Floor verification` are both present and neither is inherited — the floor run was re-executed because this pass changed the code it covers.

**My own re-run, through `scripts/prove_failability.py` with a manifest and a scratch root of my own, both outside the repository** (`worker-1.md` `### Verifying relocation / promotion claims`: run the proof yourself, never read Worker 3's acceptance as discharge). The anchor pre-check ran first and standalone (`--check-anchors-only`, exit 0): each anchor matched exactly once, which is independently the evidence that the tree carried no live mutation before I started. Run exit code `0`.

| entry | boundary | pre-mutation scope state | collection/setup errors | failing node ids | restore |
|---|---|---|---|---|---|
| E1 | `examples/fakeshop/apps/products/schema.py::EntryType.get_queryset` | `132 passed`, pytest exit 0; pre-existing failing rows differenced out: 0 | 0 | `::test_cascade_staff_sees_everything[allEntries]`, `::test_cascade_staff_sees_private_rows_hidden_from_non_staff[allEntries]` | `filecmp.cmp(shallow=False)` -> `True`, `sha256 cd91fe508c5fd8a2... == cd91fe508c5fd8a2...` |
| E2 | `examples/fakeshop/apps/products/schema.py::PropertyType.get_queryset` | `132 passed`, pytest exit 0; differenced out: 0 | 0 | `::test_cascade_staff_sees_everything[allProperties]`, `::test_cascade_staff_sees_private_rows_hidden_from_non_staff[allProperties]` | same, matching digest |

Scope as run, byte-identical to every prior record so the sets are comparable: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE examples/fakeshop/test_query/test_products_api.py examples/fakeshop/apps/products/tests/test_schema.py`. Mutant exit code 1 (`2 failed, 130 passed`) on both. **The node-id sets are identical, boundary for boundary, to every prior run** — Worker 2 pass 1, Worker 3 pass 1, my own pass 1, Worker 2 pass 2, Worker 3 pass 2, and now this one: **five independent runs producing one set per boundary**, against a `132 passed` pre-mutation baseline that has not moved since the rows landed. Both clear `### Acceptance rule` at 2 rows; neither is weakly pinned. The consolidation added no row, removed none, and split no node id — which is the mechanical form of the claim my acceptance rested on, and it is measured, not asserted.

**No mutation survives.** `git diff HEAD -- examples/fakeshop/apps/products/schema.py` is empty and `shasum -a 256` reports `cd91fe508c5fd8a2a77ba03da4464bce7378ccb5a040834a4fe959b4974c4196`, the digest every prior pass recorded. A sweep for `ACTIVE-MUTATION.json` and `RESTORE-FAILED.json` across the repository (excluding `.git/`), `/tmp`, and every scratch root this cycle used returns **nothing**; my own scratch root holds only `pristine/`. `git checkout` / `git restore` / `git stash` were never invoked, on any path, and `examples/fakeshop/db.sqlite3` was never reset.

### Fail-open shapes — the empty-model case verified, not accepted

`_cascade_page_gids` returns `[]` for a model with no rows, and a helper returning `[]` would make T1's equality and T2's membership pass vacuously. Worker 3 reports both non-vacuity guards fire upstream of the helper; I verified that reasoning against the source rather than accepting it, and it holds in both directions:

- **T1:** `assert model.objects.filter(is_private=True).exists(), field` sits at `:2331`, *two lines before* `expected = _cascade_page_gids(model)` at `:2333`. A model that could make the helper return `[]` has no rows at all, so it has no private rows either, so the guard fails before the equality is ever evaluated. The guard is upstream by line order, not merely by intent.
- **T2:** `assert hidden is not None` at `:2356` fires before the helper is called at `:2360` at all. And the direction matters independently: on an empty list `assert hidden_gid in _cascade_page_gids(model)` **fails**. An empty answer exits on the safe side whether or not the guard above it exists.

Read the pass-2 diff for the rest of the catalogue: no clamp, no `getattr` default standing in for a meaningful absence, no `or` fallback, no bare or over-broad `except`, no default reached because an input was incoherent. The page is still read as `payload["data"][field]["edges"]` with direct indexing and no `.get()` default, so a missing key raises rather than yielding `[]`. The two `len()` calls remain inside T1's failure-message tuple, where they cannot pass or fail anything — the assertion did not become a count when its right-hand side moved behind a name.

### Step 5 — focused run

`uv run pytest examples/fakeshop/test_query/test_products_api.py -k cascade --no-cov` -> **`13 passed`**, exit 0. No `--cov*` flag; `--no-cov` only, as `pytest.ini`'s auto-applied `--cov` requires. **It runs.**

### Step 6 — staged-anchor sweep

`grep -rn 'TODO(spec-034' .` (`.git/` excluded) returns **three** hits and **none is an anchor**. One is the population my first pass recorded, unchanged: `docs/SPECS/spec-034-permissions-0_0_10.md:379`, `## Implementation plan`, the sentence *describing* the anchor discipline. The other two are inside this artifact itself (`:666` and `:757`) — my own pass-1 record quoting the sweep and its output, which a `docs/builder/bld-*.md` per-cycle scratchpad is entitled to carry and which closes with the cycle. **No source or test file carries a `TODO(spec-034 ...)` anchor**, so nothing this round shipped left one behind; the sweep's population is unchanged in substance from pass 1.

### Worker 3's L3 — disposed, disposition sustained

**Sustained. The no-code-change disposition stands, and the correction is recorded here** because `docs/builder/ARTIFACT.md` forbids editing a prior entry, so Worker 2's pass-2 build report keeps its wording.

Re-derived independently rather than accepted from the review:

- **The stated obstacle does not hold.** `### Implementation notes` (pass 2) gives the reason for the return-only annotation as "annotating it would mean importing `django.db.models` into a module whose `models` name is already bound to `apps.products.models`". The annotation needs the **class**, not the module: `from django.db.models import Model` binds `Model`, and `grep` over the file confirms no `Model` name is bound anywhere in it (`from apps.products import models` binds `models`, and `get_user_model` is a function). `ruff`'s `target-version = "py310"` and `requires-python = ">=3.10,<4.0"` both admit `model: type[Model]`. So the collision the note names is avoidable.
- **The choice it defends is nonetheless right, and I sustain it.** `ANN` sits in the `"examples/**/*.py"` per-file ignore list in `pyproject.toml:190`, so nothing enforces the annotation here, and the return type is the load-bearing half for a reader. The one real argument on the other side is local convention, and Worker 3 stated it accurately: `::_cascade_page_gids` is now the only module-level helper in this file with an unannotated parameter — `::_staff_client` (no parameters), `::_global_id`, `::_login_with_perm`, `::_items_connection_page` and `::_login` all annotate theirs. That is a weight call, not a defect.
- **The correct reason for the shape:** `type[Model]` costs an import for a rule this tree does not enforce on `examples/**`, and the return type carries what a reader needs. **No code change is required and none is asked for.** L3 is report prose only; it touches no shipped assertion and no lint outcome.

For the record, the two Low findings from pass 1 remain disposed exactly as my first final verification recorded them: **L1** sustained (the drop is correct; the correct reason is "not generalizable to the parametrized `model`", not "false for `Property` / `Entry`"), **L2** sustained (my own plan's repeated-literal prediction was falsified at `+1` per root field; it does not touch the constant's justification). Neither is re-opened here.

### Spec reconciliation — pass 2 creates no new spec obligation

**Examined, and the answer is explicitly none.** `_cascade_page_gids` is a private test-file symbol; the spec's `## Test plan` names test functions, and pass 2 changed no test name, no node id, no assertion semantic, and no fixture. There is nothing for the spec to say about the site at which an expectation is built.

The `## Test plan` sibling-test amendment I applied in pass 1 is **present exactly once and still true as written**, confirmed against the file rather than against my own record: `grep -rn 'test_cascade_staff_sees_everything' docs/SPECS/` returns one line (`:467`) and `grep -rn 'sees_private_rows_hidden_from_non_staff' docs/SPECS/` returns one line (`:468`). Read end to end against the landed code, both bullets remain accurate after the consolidation — the first's "pinned as an id **list** … in pk order truncated to the connection page cap" and "carries the asserted precondition that rows the cascade would hide exist"; the second's "the row asserted to fall inside the returned page" and "both non-staff pages asserted non-empty". **No spec edit is owed and none was made.**

Consequently **no gate re-run is owed**: `check_spec_glossary.py`, `check_citations.py` and `check_trailing_commas.py` are conditional on a spec edit this pass did not make. Their pass-1 readings (`OK: 42 terms`; `OK: 857 citations resolve`; exit 0) stand as the last measured state of files this pass did not touch.

### Spec status-line re-verification (this spawn)

Read the spec's title, the `Shipped in 0.0.10` identity paragraph, the `Status:` line, `Owner:`, and `Predecessors:` end to end again this spawn. **Nothing this cycle did falsifies any of them.** The `Status:` line correctly reads SHIPPED (`0.0.10`) with all five slices final-accepted; this round adds live test rows to an already-shipped slice and changes no shipped behavior. R2's zero-occurrence baseline for history narration also holds: `post-ship` appears **0** times in the spec, and the only `as of` occurrences are the two pre-existing `## Current state` vintage-framing sites R2 deliberately kept. **No header edit is owed and none was made.**

### Summary

The one open item is closed. The ORM page-expectation window — the single place the connection's default ordering and its `_RELAY_MAX_RESULTS` page cap are coupled into one expectation — now exists exactly once, at `::_cascade_page_gids`, read by T1's `expected` and T2's pagination precondition and by nothing else. The consolidation is scoped as specified: no test name, parametrize id, assertion semantic, docstring subject, or fixture moved, and the failability proofs prove it rather than assert it — five independent runs now produce one node-id set per boundary, `[allEntries]` x2 for `EntryType` and `[allProperties]` x2 for `PropertyType`, against an unmoved `132 passed` baseline with 0 collection/setup errors and byte-compared reverts. The round as a whole closes the cycle's single SKIPPED contract (R1c B4a) and lifts its High finding (H1) out of weakly-pinned by measurement: `EntryType.get_queryset`'s staff branch went from 0 failing rows of 125 to 2, and the previously unmeasured `PropertyType` twin measures 2 as well.

### Spec changes made (Worker 1 only)

**None this pass.** The one spec edit of this round — the `## Test plan` Slice 4 staff-row amendment — was made and recorded in my first final-verification entry above, and is unchanged here; it landed once and is still true against the consolidated code. No `### Dispatched findings checklist` box is left `- [ ]`, so no deferral reason is owed under `## Final verification job` step 3: **B4a** and **H1** are both `- [x]`, both audited against the diff in pass 1, and both re-confirmed here (four-wide matrix in `_CASCADE_ROOT_FIELDS`; non-zero node-id-listed after-sets for E1 and E2, now reproduced a fifth time).

### Verification run

Every command below was run in this pass; the output is quoted as produced.

```shell
$ uv run python scripts/prove_failability.py <scratch>/w1-pass2-034-r3/proofs.json --output <scratch>/w1-pass2-034-r3/proofs-report.md
[1/2] examples/fakeshop/apps/products/schema.py::EntryType.get_queryset
    -> inside Worker 3's mandatory re-run floor (<= 3 rows)     # 2 rows, 0 errors
[2/2] examples/fakeshop/apps/products/schema.py::PropertyType.get_queryset
    -> inside Worker 3's mandatory re-run floor (<= 3 rows)     # 2 rows, 0 errors
# exit 0   (manifest and scratch root both OUTSIDE the repository)

$ uv run pytest examples/fakeshop/test_query/test_products_api.py -k cascade --no-cov
13 passed in 6.84s
# exit 0

$ grep -rn '_RELAY_MAX_RESULTS\]' tests/ examples/
examples/fakeshop/test_query/test_products_api.py:2298:        for pk in model.objects.order_by("pk").values_list("pk", flat=True)[:_RELAY_MAX_RESULTS]
# one line, inside the helper

$ grep -rn 'TODO(spec-034' .          # .git/ excluded
docs/SPECS/spec-034-permissions-0_0_10.md:379   # the sentence describing the anchor discipline
docs/builder/bld-034-review-3-code_repair.md:666, :757   # this artifact quoting the sweep
# no source or test anchor

$ git diff HEAD -- examples/fakeshop/apps/products/schema.py
# empty
$ shasum -a 256 examples/fakeshop/apps/products/schema.py
cd91fe508c5fd8a2a77ba03da4464bce7378ccb5a040834a4fe959b4974c4196

$ git diff --stat HEAD -- examples/fakeshop/test_query/test_products_api.py
 1 file changed, 95 insertions(+), 12 deletions(-)
```

### Concurrent tree

Untouched and unreverted, exactly as it arrived: `BACKLOG.md`, `KANBAN.md`, `KANBAN.html`, `README.md`, `examples/fakeshop/db.sqlite3`, `scripts/_kanban_lib.py`, `scripts/build_kanban_html.py`, `scripts/build_kanban_md.py`, `tests/test_build_kanban_html.py`, and the untracked `0_0_14.md` / `docs/DIVERGENCE.md`. `git checkout` / `git restore` / `git stash` were never invoked on any path, and the database was never reset — the focused run and both proof runs used Django's in-memory test database.

### Notes for Worker 1 (spec reconciliation)

Everything the cross-slice integration pass and the final gate's `### Deferred work catalog` must pick up from R3. Nothing here is a blocker on this round.

- **Temp-test directory disposition — four directories this round created, all keep-for-the-cycle, nothing to promote.** `docs/builder/temp-tests/034-r3/` (Worker 2 pass 1), `034-r3-review/` (Worker 3 pass 1), `034-r3-pass2/` (Worker 2 pass 2), `034-r3-review2/` (Worker 3 pass 2). Each holds exactly `proofs.json` + `proofs-report.md` and no test file; `docs/builder/temp-tests/` is gitignored (`.gitignore:192`) and cleared by `scripts/clean_up.py` at the next cycle's pre-flight. They are proof records, not tests, so none is a promotion candidate. My own two passes' manifests and reports live **outside** the repository and need no disposition. Note for completeness: `034-r1c/` and `review-1a/` predate this round and belong to their own cohorts; `review-1a/` is the only directory in the tree holding a `__pycache__` from an actual temp test.
- **Three unresolved Lows, all prose-only, all sustained with no code change, none re-openable as a defect.** **L1** — the pass-1 build report's reason for dropping the shipped trailing assertion is factually wrong; the correct reason is "not generalizable to the parametrized `model`". **L2** — my own plan's repeated-literal prediction ("they go down") is falsified at `+1` per root field, caused by `pytest.param` writing the name twice; it does not touch the constant's justification. **L3** — the pass-2 report's reason for the return-only annotation does not hold as stated (`from django.db.models import Model` binds `Model`, no collision); the choice is right on the per-file-`ANN`-ignore and weight grounds recorded above. All three corrections are recorded in Worker 1 sections because `ARTIFACT.md` forbids editing a prior entry; the integration pass should carry them as *recorded corrections*, not as open work.
- **Deferred to the maintainer, unchanged and untouched by this round: R1c's M2** — the 18 rotted card ids in `examples/fakeshop/apps/products/schema.py` beside one correct `TODO-BETA-062-0.1.5`, coupled to `KANBAN.md` which is outside this cycle's maintainer-set scope (build plan `## R1 outcome`). The file is byte-identical to `HEAD` after every transient proof in this round, so nothing here changed its disposition. It belongs in the `### Deferred work catalog` with the coupling stated.
- **Deferred to the maintainer, and this round deliberately preserved its ordering: R1c's M1** — the `view_<model>` branch that is the same expression as the fall-through. H1's rows are now on disk, so a future collapse would be performed against a suite that can detect a mistake in it: T2 asserts the `view_<model>` actor explicitly for all four models. M1 remains the maintainer's call and nothing in this round acts on it.
- **Standing observation, not a finding, now single-sited.** T1's assertion is coupled to the connection's default `ORDER BY`, sound today by contract (`optimizer/plans.py::deterministic_order` resolves to `("id",)` with no `Meta.ordering` on any products model and no keyset target). If a later card gives any of the four models a `Meta.ordering`, all eight staff rows go red for an ordering reason rather than a permission one. After the consolidation that coupling has exactly one home (`::_cascade_page_gids` and its docstring), so a future card fixing it edits one expression instead of two.
- **Floor verification is discharged by this round's builder pass and needs no second owner**, per the build plan's declaration: `/tmp/dsf-floor-034`, Python 3.10.19, Django 5.2.16, strawberry-graphql 0.316.0, focused scope `-k cascade` -> `13 passed`. It was re-run at pass 2 rather than inherited. The final gate confirms it happened; it does not re-own it.
- **No spec obligation is left open by R3.** The `## Test plan` amendment is landed once; Slice 4 box 2 and Definition-of-done item 10 were correct contracts all along and are now true for the first time; the rationale companion took no bullet, on the precedent R2 set for Test-plan edits.

### Final status

`final-accepted`
