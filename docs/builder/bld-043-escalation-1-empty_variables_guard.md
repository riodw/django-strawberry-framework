# Escalation 043-1 — the empty-`variables` guard in `TestClient._build_body`

Spec reference: `docs/SPECS/spec-043-test_client-0_0_14.md` (dirty in the working tree; Cohort A's rewrite, intended)
Build plan: `docs/builder/build-043-test_client-0_0_14.md`
Raised by: `docs/builder/bld-043-review-2-code_verification.md` `### DRY and existence findings`, `### Notes for Worker 1` item 3
Subject: `django_strawberry_framework/testing/client.py::TestClient._build_body #"if not variables:"` (client.py:284-291)
Status: investigation complete — maintainer decides

## Verdict

Keep the raise, change its predicate. `if not variables:` re-tests the truthiness the emission
line `if variables: body["variables"] = variables` (client.py:276) already decided; spell it as
`if "variables" not in body:` so the guard reads the envelope it protects instead of repeating the
predicate that built it. Verdict-identical on every input probed (10/10), same message, one edit
site for the emission rule. Then pin it with rows that match `requires variables=`, not
`placeholder`. Do **not** delete it: the reviewer's premise that deletion changes no verdict is
false for one in-domain input class, and with the guard gone the builder emits a spec-invalid
envelope the server rejects with a misleading 400.

## Verified facts

All read-only except one sanctioned transient mutation, restored and proved (fact 3). No `.py`, spec,
or other worker's artifact was edited. Scratch lives in the session scratchpad.

1. **Subject, as shipped (client.py, clean against HEAD — `git diff HEAD --stat -- django_strawberry_framework/testing/client.py` prints nothing).**
   Line 276 `if variables: body["variables"] = variables` (emission, truthiness). Line 281 `if not files: return body`.
   Line 284 `if not variables: raise AssertionError("query(..., files=...) requires variables= carrying a None placeholder at each file's variable path (e.g. variables={'data': {'image': None}} for files={'data.image': f}).")`.
   Line 300 reserved-key guard. Line 308 `self._assert_file_placeholders(variables, files)`. Walker at 314-396.
2. **Baseline.** `uv run pytest -n0 tests/testing/test_client.py --no-cov -q` → `41 passed`.
3. **Failability re-measured with the sanctioned tool.** Manifest in scratchpad; anchor `        if not variables:` matched once; mutation `if not variables:` → `if False:`; scope `tests/testing/test_client.py -n0`.
   `uv run python scripts/prove_failability.py <scratch>/proofs.json --output <scratch>/proof-report.md` → baseline 41 passed, mutant 41 passed, **0 rows**, 0 collection errors, exit 1 (weakly pinned). Restore proved: `filecmp.cmp(shallow=False) True; sha256 e40ea98a9b352eac... == e40ea98a9b352eac...`. Scratch `failability/` holds only `pristine/`, no `ACTIVE-MUTATION.json`. `git status --short django_strawberry_framework/` is empty afterwards.
   Confirms review-2 entries A1/B1. `why 0`: weakly pinned, not harness-impossible — a `match="requires variables="` row fails the instant the guard is gone.
4. **The only row on the guard** is `tests/testing/test_client.py::test_files_without_variables_raises_the_placeholder_guard` (test_client.py:160-173): two calls (`variables` omitted; `variables={}`) in one node id, both `pytest.raises(AssertionError, match="placeholder")`. Every walker message also contains `placeholder`.
5. **Verdict census over every falsy `variables` class** (probe `<scratch>/probe_guard.py`, `uv run python`, fakeshop settings; `F = object()`). Three columns: the builder as shipped; the walker called alone; the builder with the guard removed and everything else kept.

   | `variables` | `files` | builder (guard live) | walker alone | guard removed |
   |---|---|---|---|---|
   | `None` | `{"file": F}` | REJECT call-level | REJECT `cannot descend into 'file' (the value there is not a dict or list)` | REJECT (walker) |
   | `{}` | `{"file": F}` | REJECT call-level | REJECT `no key 'file' at that level` | REJECT (walker) |
   | `FalsyDict({"file": None})` | `{"file": F}` | REJECT call-level | **ACCEPT** | **EMIT** `operations={"query": ...}` (no `variables`), `map={"file": ["variables.file"]}` |
   | `FalsyDict({"data": {"image": None}})` | `{"data.image": F}` | REJECT call-level | **ACCEPT** | **EMIT**, same shape |
   | `[]` | `{"0": F}` | REJECT call-level | REJECT `not a valid index into a 0-item array` | REJECT (walker) |
   | `FalsyList([None])` | `{"0": F}` | REJECT call-level | **ACCEPT** | **EMIT** `map={"0": ["variables.0"]}` |
   | `0`, `""`, `FalsyObj()` | `{"file": F}` | REJECT call-level | REJECT `cannot descend` | REJECT (walker) |

   `FalsyDict` / `FalsyList` = `dict` / `list` subclass whose `__bool__` returns `False`. A dict subclass is inside the annotated domain `dict[str, Any] | None`.
6. **What the server does with the emitted envelope.** `strawberry/http/sync_base_view.py::parse_multipart` calls `strawberry/file_uploads/utils.py::replace_placeholders_with_files`, which does `operations["variables"]` → `KeyError` → `HTTPException(400, "File(s) missing in form data")`. The files are present; the message blames the wrong thing. Upstream carries `# TODO: test this with missing variables in operations_with_placeholders` on that exact hole.
7. **Upstream shape.** `strawberry.test.BaseGraphQLTestClient._build_body`: `if variables: body["variables"] = variables` then `if files: assert variables is not None`. Same emission truthiness, `is None` guard — so the base itself emits the incoherent envelope for `variables={}`. strawberry-django inherits it unchanged.
8. **Repo precedent for the falsy-`__bool__` class on this module.** Commit `f7fbead4` "Honor a falsy test client instead of replacing it" and `tests/testing/test_client.py::test_clients_preserve_an_explicit_falsy_transport`; the 0.0.15 bug hunt probed hostile `__len__` / `__repr__` on the walker (`docs/bug_hunt/bug_hunt-0_0_15.md` item "one owning guard `_assert_file_placeholders`"). This module already treats "falsy object with real content" as a test-input class, not a curiosity.
9. **Media carrying the guard's contract** (`rg -l -i 'None placeholder|placeholder at each'` outside shadow/bld: 4 files). Code comment + `query()` docstring (client.py:157-170, 285-287); spec `## Error shapes` (~865), Decision 9 (~1255-1262), `## Edge cases` (~1582-1588), Test plan (~1650), DoD (~2020); rationale F5 (appx rationale ~175-200); test docstring (test_client.py:161-168). Neither README nor GLOSSARY quotes the message; GLOSSARY:2052 states the placeholder contract generically.
10. **Nothing pins the wire omission of `variables` for `None`/`{}`** on the JSON path. `rg -F '"variables"' tests/testing/test_client.py` hits only lines 276, 388, 414, none asserting absence. `test_build_body_sends_empty_operation_name_instead_of_dropping_it` builds with `variables=None` and asserts only `operationName`.

## Q1 — Is the subsumption claim true?

**No, as stated.** The reviewer wrote "the only two inputs the guard intercepts" are `None` and `{}`. The guard intercepts every falsy value. For falsy non-containers and empty containers the walker agrees (table rows 1, 2, 5, 7). For a **falsy container that carries real placeholders** the verdicts split: guard rejects, walker accepts, and with the guard gone the builder emits `map` entries pointing into a `variables` member that `if variables:` never wrote (rows 3, 4, 6).

That split is not an accident of the walker; it is what the guard is actually for. The walker verifies the Python object. The emission at :276 decides the envelope by truthiness. The guard's predicate is the emission's predicate, so the guard is the one thing keeping `map` and `operations` coherent — its real invariant is "the map may not point into a member the envelope does not carry", and it happens to be spelled as a second copy of the emission test. Its comment ("the multipart map needs variable paths to point at") says the invariant; its spelling says the input.

This is the shape `BUILD.md` `### Fail-open shapes` names — "a truthiness test on a value that can be absent, where absent and empty mean different things" — except the divergence is between *falsy* and *empty*, and the guard is currently the thing failing it closed. Delete the guard and the envelope path fails open for that class (fact 6: server 400 blaming missing files).

How real is the class? Narrow, adversarial, and inside the annotated type; this module's own test vocabulary already contains it (fact 8). Grade it the way the bug hunt graded the hostile-`__len__` row: Low, fail-closed at the source, uniform type.

## Q2 — DRY matrix and single-edit-site test

Applied to the pair **guard ↔ walker**, then to the pair the reviewer did not look at, **guard ↔ emission**.

- **Axis 1, cross-flavor mirroring** — one builder serves `TestClient`, `AsyncTestClient`, and the mixin (`GraphQLTestMixin.query` constructs a `TestClient`). No second flavor of this rule. Inapplicable.
- **Axis 2, sync/async twins** — `_build_body` is shared; only `request()` is colored. Inapplicable.
- **Axis 3, derived rather than repeated knowledge** — **hit, but not where the escalation points.** The guard re-derives "the envelope has no `variables` member" by re-evaluating `not variables` instead of reading `body`. Guard ↔ walker: different facts ("envelope coherent" vs "path P resolves to `None`"); the guard's fact happens to imply the walker's for `None`/`{}`, which is why the messages overlap there.
- **Axis 4, round-trip pairs** — the builder emits `variables.<key>`; the server's `replace_placeholders_with_files` parses it. That pair is real and lives across packages; not this guard's concern.
- **Axis 5, contract restated in another medium** — fact 9: one code site, five spec homes, one rationale, one test docstring. The cost is symmetrical: keep, delete, or respell, every one of those moves once. It argues for making the prose state the invariant rather than the input spelling, so the next predicate change does not re-falsify it.

**Single-edit-site test.** Posited changes and the sites each forces:

| Posited change | Sites that must move | Count |
|---|---|---|
| Emit `variables` on `is not None` so `variables={}` travels as `"variables": {}` (the GraphQL-over-HTTP-legal spelling upstream chose not to use) | :276 emission **and** :284 guard (else `{}` is emitted yet refused) | **2** |
| Add a sixth walker rejection shape (e.g. a `Mapping` that is not a `dict`) | walker only | 1 |
| Change the placeholder sentinel from `None` to a marker object | walker :393-396 predicate; guard message text; five prose sites | 1 predicate, N wordings |
| Change the family's exception type | guard, reserved guard, five walker raises | family-wide, not this pair |

Verdict under `DRY.md`: **guard ↔ walker is not duplication** (no posited change to the placeholder rule forces the guard to move). **Guard ↔ emission is duplication** (count 2 on the first row). Deleting the guard takes the count to 1 by removing the check, not by consolidating it — `DRY.md` `## Ground rules`: "Consolidation deletes tests as well as code ... carry each distinct behavior forward"; the falsy-container rejection is a distinct behavior with nowhere to go. Deriving the guard from `body` takes the count to 1 and keeps the behavior.

## Q3 — What the error contract owes

For the exact call the guard exists for — `client.query(mutation, files={"file": f})`, `variables=` forgotten:

- guard: `AssertionError: query(..., files=...) requires variables= carrying a None placeholder at each file's variable path (e.g. variables={'data': {'image': None}} for files={'data.image': f}).`
- walker: `AssertionError: files= path 'file' has no matching placeholder in variables: cannot descend into 'file' (the value there is not a dict or list).`

The walker's message is **wrong about the fault**, not merely less specific: "the value there is not a dict or list" describes a mis-typed value at a path, but there is no value at any path — `variables` is `None`. A consumer reads that as "I shaped `variables` wrong" and goes looking inside a dict they never passed. For `variables={}` the walker's `no key 'file' at that level` is accurate but names no fix. The guard's message names the parameter, the fix, and an example. On the wire the delta is large for the `None` case and modest for `{}`. Alone this would not justify a second raise site; combined with Q1 it settles that the call-level message should stay.

## Q4 — Is the reviewer's `BUILD.md` argument sound?

`### Acceptance rule`: "A boundary is weakly pinned when removing it makes 0 or 1 test rows fail ... The fix is more (or better-targeted) rows — never a weaker boundary." `### What gets recorded`: "A mutation must remove the boundary, not merely perturb code near it." `### Harness-impossible interleavings`: "A wire-level assertion that still passes with the invariant removed is worthless. Deleting it loses nothing."

The rule's subject is a **boundary — code that decides a verdict**. Its purpose is to stop a builder answering "0 rows" by deleting the thing being measured. It presupposes the mutation removed a decision. On the reviewer's own premise ("changes no verdict; changes only the message") the mutated code was not a boundary, the 0-row result says the *message* is unpinned, and "never a weaker boundary" has nothing to bite on — the rule as cited would equally forbid deleting any dead branch someone happened to mutate. **The argument as written is unsound**: it borrowed the rule's conclusion while denying its premise.

The conclusion survives because the premise is false (Q1). The guard does decide a verdict for the falsy-container class; removing it fails that class open; 0 rows pin that verdict. So the rule applies, and its prescription is rows: parametrized `None` / `{}` rows matching `requires variables=`; one falsy-mapping row asserting rejection; one async-color row. That is the reviewer's resolution (a), reached for a reason the reviewer did not have.

## Q5 — A third option

**Option C — derive the guard from the envelope.** One line:

```python
if "variables" not in body:
    raise AssertionError("query(..., files=...) requires variables= carrying a None placeholder ...")
```

Simulated against all ten probe inputs, valid shapes included (`<scratch>/probe_third_option.py`): **0 mismatches** with today's verdicts and today's message classes. It is `BUILD.md`'s own prescription — "guard the ANSWER, not one spelling of the incoherent input" — and it collapses the guard ↔ emission edit-site count to 1: change :276 to `is not None` tomorrow and the guard follows without being touched (`{}` would then be emitted and the walker, correctly, would reject it path-by-path).

**The prompt's variant — walker emits call-level wording when the failure is call-level — is not an improvement.** A call-level check inside a per-path walker is `if not variables:` moved one frame down: the second truthiness site survives, the walker gains a pre-loop branch unrelated to walking, and the method signature `(variables, files)` no longer knows whether `variables` was emitted. Rejected.

**Option D — change the emission to `is not None`** so `{}` travels as `"variables": {}`. Legal on the wire, nothing pins the current omission (fact 10), but it changes the bytes of every JSON post with `variables={}` for no consumer benefit, diverges from the base and from the spec's stated shape, and the guard would still have to move with it (count 2 → this is exactly the change Option C makes free). Not recommended now; Option C is what makes it safe later.

## Recommendation

1. **Option C** in `client.py::TestClient._build_body`: predicate `if "variables" not in body:`; message unchanged; comment rewritten to state the invariant (below).
2. **Rows** in `tests/testing/test_client.py` (Cohort C's write set): parametrize `test_files_without_variables_raises_the_placeholder_guard` over `None` / `{}` with `match="requires variables="`; add a falsy-`dict`-subclass row (placeholders present, `__bool__` False) asserting the same match — this is the row that makes the boundary a boundary; add the async-color row review-2 named. Target ≥ 4 node ids.
3. **Spec** (Cohort A / Worker 1): one bullet and two sentences, text below.

**Strongest counter-argument, stated fairly.** The falsy-populated container is an adversarial input no real test author will pass; pinning it adds a row for a behavior nobody wants, and the derived spelling is a cleverness a reader has to decode ("why check the body instead of the argument?"). Keep-and-pin as the reviewer proposed is one edit fewer and reads plainly; the guard ↔ emission coupling is two adjacent lines in one method, which is the cheapest possible duplication to live with. If the maintainer weighs it that way, the fallback is the reviewer's (a) — keep-and-pin with the `requires variables=` rows — **not** deletion. Deletion is the one resolution the evidence rules out.

What the evidence does not settle: whether the maintainer wants the falsy-container row at all. Without it, Option C is still verdict-identical and still one edit site, but the class it protects stays unpinned.

## Exact change under Option C

`django_strawberry_framework/testing/client.py::TestClient._build_body`, replacing :284-291 and the comment above them:

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

Walker docstring's last sentence ("matching the empty-``variables`` guard above") still reads true.

**Spec `## Error shapes`, the `files=` bullet**, replacing "then `if not variables: raise AssertionError(...)` (so `variables={}` is refused exactly as `variables=None` is — the multipart `map` needs variable paths to point at)":

> then raises when the envelope just built carries no `variables` member (`if "variables" not in body`) — the multipart `map` points into `variables.<path>`, so a body with nothing at that member is refused before it is posted. Because `variables` is emitted on truthiness, `variables={}` is refused exactly as `variables=None` is, and so is any falsy mapping, whatever it contains.

**Decision 9**, the sentence "and then raises when `variables` is falsy, so `variables={}` is refused just as `variables=None` is":

> and then raises when the built body carries no `variables` member for the `map` to point into — with truthiness emission that is every falsy `variables`, `{}` and `None` alike.

**`## Edge cases`**, "guards this with an explicit `raise AssertionError` when a truthy `files` arrives with falsy `variables`": → "when a truthy `files` arrives and the built envelope carries no `variables` member (every falsy `variables`)". Test plan and DoD wording ("empty-`variables` guard") stays accurate. Rationale F5 gains one line naming the respelling and its reason (the falsy-container census above).

## Scratch and cleanliness

Scratchpad only: `probe_guard.py`, `probe_third_option.py`, `proofs.json`, `proof-report.md`, `failability/pristine/`. Repo: this file is the only addition; `client.py` byte-identical to its pre-mutation copy and to HEAD.
