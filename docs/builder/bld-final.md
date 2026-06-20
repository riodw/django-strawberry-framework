# Build: Final test-run gate — upload_file_image_mapping / 0.0.11 (037)

Spec reference: `docs/spec-037-upload_file_image_mapping-0_0_11.md`
Build plan: `docs/builder/build-037-upload_file_image_mapping-0_0_11.md`
Status: final-accepted

> **Maintainer commit note (out-of-scope change bundled in this range).** The
> commit range `0273c869..HEAD` contains a one-line, unrelated baseline test
> repair — `tests/orders/test_sets.py` re-pinned from the stale `"OrderSet.apply"`
> assertion to `"OrderSet could not resolve"` (a substring of the committed,
> intentional `utils/permissions.py::request_from_info` message; the production
> helper was already correct and was NOT changed). No orders production file
> changed in the 037 range. This is a maintainer-authorized orders/permissions
> repair, not part of the upload/file feature — ideally committed separately from
> the 037 source/doc/version changes. Full provenance below
> (`## Failure ownership analysis`, `### Re-run disposition`, and the deferred-work
> catalog's RESOLVED entry).

Final test-run gate (Worker 1), run after the cross-slice integration pass
(`docs/builder/bld-integration.md`) reached `final-accepted`. This is the last
gate before the maintainer handoff. The gate is intentionally narrow: run the
fixed command set, record each command's verbatim pass/fail, catalog deferred
work. Worker 1 does NOT fix code in this pass — a failure routes back through the
owning slice loop.

## Gate baseline note

The build plan's pre-flight recorded a CLEAN working-tree baseline (no baseline
exceptions). Pre-flight ran `git status --short` (working tree), NOT a full
`pytest` sweep, so a committed-but-failing test in an unrelated subsystem was not
visible at pre-flight. The final gate is the first and only place the full
`pytest --no-cov` sweep runs — and it is where the pre-existing failure below
surfaced.

## Gate commands and verbatim results

### 1. Full test sweep — `uv run pytest --no-cov` — **FAIL**

```text
=================================== FAILURES ===================================
_____ test_orderset_request_from_info_raises_on_unrecognized_context_shape _____

    def test_orderset_request_from_info_raises_on_unrecognized_context_shape():
        """A non-HttpRequest context with no ``.request`` attribute raises."""

        class _PlainCtx:
            pass

        info = SimpleNamespace(context=_PlainCtx())
        with pytest.raises(ConfigurationError) as exc_info:
            OrderSet._request_from_info(info)
>       assert "OrderSet.apply" in str(exc_info.value)
E       AssertionError: assert 'OrderSet.apply' in 'OrderSet could not resolve a Django HttpRequest from `info.context` (got _PlainCtx). Expected `info.context.request` or a bare HttpRequest.'
E        +  where 'OrderSet could not resolve a Django HttpRequest from `info.context` (got _PlainCtx). Expected `info.context.request` or a bare HttpRequest.' = str(ConfigurationError('OrderSet could not resolve a Django HttpRequest from `info.context` (got _PlainCtx). Expected `info.context.request` or a bare HttpRequest.'))
E        +    where ConfigurationError('OrderSet could not resolve a Django HttpRequest from `info.context` (got _PlainCtx). Expected `info.context.request` or a bare HttpRequest.') = <ExceptionInfo ConfigurationError('OrderSet could not resolve a Django HttpRequest from `info.context` (got _PlainCtx). Expected `info.context.request` or a bare HttpRequest.') tblen=3>.value

tests/orders/test_sets.py:390: AssertionError
=========================== short test summary info ============================
FAILED tests/orders/test_sets.py::test_orderset_request_from_info_raises_on_unrecognized_context_shape
pytest summary: 1 failed, 2212 passed, 4 skipped, 4 xfailed in 199.34s (0:03:19)
```

(The pytest summary line above is reproduced WITHOUT pytest's `=======` border:
a line beginning with seven `=` is read by `git diff --check` as a leftover
conflict marker, so the border is dropped to keep the artifact diff-clean while
preserving the verbatim counts.)

Counts: **1 failed, 2212 passed, 4 skipped, 4 xfailed**.

### 2a. Django system check — `uv run python examples/fakeshop/manage.py check` — **PASS**

```text
System check identified no issues (0 silenced).
```

### 2b. Migration consistency — `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` — **PASS**

```text
No changes detected
```

Exit code 0 (migration state is consistent; no migration file would be produced).

### 3a. Format check — `uv run ruff format --check .` — **PASS**

```text
warning: The following rule may cause conflicts when used with the formatter: `COM812`. ...
287 files already formatted
```

Exit code 0. (The `COM812` warning is the standing repo-config note documented in
`AGENTS.md` #"COM812 only auto-adds to already-multi-line constructs", not a
format failure.)

### 3b. Lint check — `uv run ruff check .` — **PASS**

```text
All checks passed!
```

Exit code 0.

### 3c. Whitespace / conflict-marker check — `git diff --check` — **PASS**

No output; exit code 0. As the build plan's preamble anticipated, the binary
`examples/fakeshop/db.sqlite3` (modified by the Slice 4 card-close) does not trip
`git diff --check` (it only flags whitespace/conflict markers in text).

## Failure ownership analysis (the one FAIL)

The single failing test is **`tests/orders/test_sets.py::test_orderset_request_from_info_raises_on_unrecognized_context_shape`** — in the **orders** subsystem, which build-037 (upload_file_image_mapping) never touched.

- **Not owned by any 037 slice.** The 037 build's modified files are exactly the read/write/scalar/export source (`types/converters.py`, `types/base.py`, `types/resolvers.py`, `types/finalizer.py`, `mutations/inputs.py`, `mutations/resolvers.py`, `scalars.py`, `__init__.py`), their tests, and the Slice-4 docs/version/DB surfaces — per `git status --short`. The failing test file and its source dependency are NOT in that set.
- **Pre-existing on the committed baseline.** `git diff HEAD -- tests/orders/test_sets.py django_strawberry_framework/utils/permissions.py django_strawberry_framework/orders/sets.py` is **empty** — the three files are committed and unmodified by this build's uncommitted working tree. The failure exists in `HEAD`, not in any 037 diff.
- **Root cause (test lags committed source).** `tests/orders/test_sets.py::test_orderset_request_from_info_raises_on_unrecognized_context_shape` asserts `"OrderSet.apply" in str(exc_info.value)`. The message is produced by `django_strawberry_framework/utils/permissions.py::request_from_info`, which **deliberately dropped the `.apply` suffix** (its docstring #"hard-coding ``.apply`` would mis-describe the mutation caller (feedback CR-5)" — the shared helper now serves the filter/order `.apply` seam AND the mutation `check_permission` seam, which has no `.apply` method). The current message is `"OrderSet could not resolve a Django HttpRequest from `info.context` (got _PlainCtx). ..."` — correct behavior; the test's expected substring is stale. The `permissions.py` refactor landed in commit `bd998093` ("Refactor mutation input handling and error reporting"); the test was not re-pinned to the new message in the same change.
- **Out of scope for Worker 1 to fix here.** This gate forbids editing source/tests, and the fix belongs to the orders/permissions subsystem, not the upload_file_image_mapping spec. Worker 1 must NOT widen 037 scope to absorb an unrelated subsystem's stale assertion.

### Disposition / routing

Per the gate rule "If any command fails: do NOT mask it … set `revision-needed`, identify which slice owns the failing behavior", the honest finding is that **no 037 slice owns this failure** — it is a pre-existing baseline defect in the orders/permissions subsystem, surfaced (not caused) by this gate's full sweep. The 037 build itself is gate-clean: Django checks, format, lint, and `git diff --check` all pass, and all 037-scoped tests pass (the 2212 passing tests include every Slice 1–3 read/write/scalar/export test).

Recommended routing (Worker 0 / maintainer decision):

- **This is a maintainer-baseline call, not an 037 slice re-loop.** The 037 slice loops cannot fix a file outside their scope. Re-spawning a Worker 2 against an 037 slice would not touch `tests/orders/test_sets.py`. The correct fix — re-pin the stale assertion in `tests/orders/test_sets.py` line 390 from `"OrderSet.apply"` to a substring of the current `request_from_info` message (e.g. `"could not resolve a Django HttpRequest"` or just `"OrderSet"`) — is a one-line orders-subsystem test correction that belongs to whoever owns the `bd998093` `permissions.py` refactor, not to build-037.
- Worker 0 should escalate to the maintainer: build-037 is functionally complete and gate-clean within its own scope; the single red is a stale orders-subsystem test assertion that predates this build on the committed baseline. The maintainer either (a) fixes the one-line stale assertion as a separate concern, then Worker 1 re-runs this gate, or (b) explicitly authorizes the 037 commit despite the unrelated red with a follow-up card for the orders test.

The artifact `Status:` stays **`revision-needed`** because a `pytest` failure is present in the full sweep; `final-accepted` is gated on a green sweep regardless of ownership.

---

## Final gate re-run (Worker 1) — 2026-06-19

Re-run of the final test-run gate after the maintainer-authorized one-line
re-pin of the single stale orders-subsystem assertion landed. Per the prior
gate's `## Failure ownership analysis`, the lone red was
`tests/orders/test_sets.py::test_orderset_request_from_info_raises_on_unrecognized_context_shape`
asserting the stale substring `"OrderSet.apply"`. The maintainer authorized
re-pinning that assertion (as a separate out-of-scope concern) to
`"OrderSet could not resolve"` — a substring of the committed, intentional
`django_strawberry_framework/utils/permissions.py::request_from_info` message
(family-label + canonical phrasing). The production helper `request_from_info`
was **not** changed (it was already correct); only the stale test assertion was
aligned. Confirmed before re-running: `tests/orders/test_sets.py` line 390 now
reads `assert "OrderSet could not resolve" in str(exc_info.value)`. This is the
ONLY change since the prior gate. No source/test edits were made by Worker 1 in
this gate (the re-pin pre-dated this spawn).

### Re-run commands and verbatim results

#### 1. Full test sweep — `uv run pytest --no-cov` — **PASS**

```text
============ 2213 passed, 4 skipped, 4 xfailed in 197.70s (0:03:17) ============
```

Counts: **0 failed, 2213 passed, 4 skipped, 4 xfailed**. The previously-failing
orders test now PASSES (the passing count rose from 2212 → 2213, exactly the one
re-pinned test). Confirmed in isolation:

```text
tests/orders/test_sets.py::test_orderset_request_from_info_raises_on_unrecognized_context_shape PASSED [100%]
============================== 1 passed in 0.06s ===============================
```

ZERO failures across all three test trees.

#### 2a. Django system check — `uv run python examples/fakeshop/manage.py check` — **PASS**

```text
System check identified no issues (0 silenced).
```

#### 2b. Migration consistency — `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` — **PASS**

```text
No changes detected
```

Exit code 0 (migration state is consistent; no migration file would be produced).

#### 3a. Format check — `uv run ruff format --check .` — **PASS**

```text
287 files already formatted
```

Exit code 0. (The `COM812` warning is the standing repo-config note documented in
`AGENTS.md` #"COM812 only auto-adds to already-multi-line constructs", not a
format failure.)

#### 3b. Lint check — `uv run ruff check .` — **PASS**

```text
All checks passed!
```

Exit code 0.

#### 3c. Whitespace / conflict-marker check — `git diff --check` — **PASS**

No output; exit code 0. The binary `examples/fakeshop/db.sqlite3` (modified by the
Slice 4 card-close) does not trip `git diff --check` (it only flags
whitespace/conflict markers in text).

### Re-run disposition

All six gate commands PASS. The full `pytest --no-cov` sweep is green with ZERO
failures; the previously-flagged pre-existing orders-subsystem red is resolved by
the maintainer-authorized re-pin. The artifact `Status:` is set to
**`final-accepted`**. The gate closes; Worker 0 may mark the final checklist box
`- [x]`.

Note for the maintainer: the one-line `tests/orders/test_sets.py` re-pin is a
separate out-of-scope concern from the build-037 commit (it aligns a stale
orders/permissions-subsystem assertion that pre-dated this build on `HEAD`). The
maintainer may wish to commit that one-line test fix separately from the build-037
source/doc/version changes.

## Spec changes made (Worker 1 only)

None. The gate surfaced no 037-spec reconciliation need. The spec status header
(lines 38–65) still accurately describes the build state ("all four slices
final-accepted … the cross-slice integration pass + final gate still follow") —
the integration pass is now complete and this final gate is in flight; the header
is not stale and was not edited. `scripts/check_spec_glossary.py` was not re-run
(no spec edit). The single test failure is out-of-spec (orders subsystem) and is
not a 037 spec gap.

## Deferred work catalog

The next spec author's reading list. Walks every per-slice and integration
artifact's spec-reconciliation / `What looks solid` / `Notes for Worker 1`
sections plus the spec's own `## Risks and open questions` and
`## Out of scope`. One bullet per deferral, with source and the spec line that
licenses it (where applicable).

### Pre-existing baseline defect surfaced by this gate (RESOLVED — recorded for provenance)

- **Stale orders-subsystem test assertion — RESOLVED (maintainer-authorized re-pin).** `tests/orders/test_sets.py::test_orderset_request_from_info_raises_on_unrecognized_context_shape` (line 390) previously asserted the old `"OrderSet.apply"` substring against the post-`bd998093` `utils/permissions.py::request_from_info` message that deliberately dropped `.apply`. It was pre-existing on `HEAD`, unrelated to 037, and red the prior full sweep. The maintainer authorized a one-line re-pin to `"OrderSet could not resolve"` (a substring of the committed, intentional `request_from_info` message) — a separate out-of-scope concern from the build-037 commit. The production helper was NOT changed (already correct); only the stale assertion was aligned. As of the 2026-06-19 final gate re-run the assertion passes and the full sweep is green (2213 passed). Owner: maintainer / orders-permissions subsystem (NOT a 037 slice). The maintainer may wish to commit this one-line test fix separately from the build-037 changes.

### Build-cycle deferrals (per-slice + integration artifacts)

- **Pillow dev/test-only dependency** — Slice 1 (`bld-slice-1-read_output_objects.md` `### What looks solid`; integration `### 5`), licensed by spec `## Risks and open questions` #"Image dimension dependency + test strategy" ("Preferred answer: add Pillow as a dev/test-only dependency"). Pillow was added as a dev-only dep so the `width` / `height` image-dimension tests run against a real in-memory PNG; the package source never imports it (no runtime surface). Standing follow-up: keep the `uv.lock` 0.0.11 bump from disturbing it (noted in worker-1 memory). Not a defect; recorded as an intentional dev-dependency addition.
- **`DONE-037` card-body `planningState` renders "In progress"** — Slice 4 (`bld-slice-4-docs_version_cut.md`; integration `### 5`), no spec line (it is a `Card.planningState` free-text field distinct from the workflow `status` FK that the close procedure flips). Precedent-consistent with the freshly-closed `DONE-036` card. Flagged as an **optional maintainer follow-up**: a separate `planningState` pass would also re-touch `DONE-036`. Explicitly NOT a card-close defect.
- **Three Slice-4 DB drift-cluster reconciliations (reconciled UP, recorded for provenance)** — Slice 4 (`bld-slice-4-docs_version_cut.md`; integration `### 5`). These were fixed in this build but the next author should know they were pre-existing DB drift, not 037-introduced:
  - `036` `SpecDoc.url` was DB-stale at `docs/spec-036` and reconciled UP to `docs/SPECS/spec-036` (else KANBAN regen regressed two links).
  - `djangomodelpermission` `GlossaryTerm.body` lagged its committed file and was synced UP.
  - The `037` card body referenced a stale `034` and `"Pairs with 028"` and was reconciled to `036` (mutations = 036, 034 = permissions, 028 = ordering) — the spec `## Risks and open questions` #"Card conflict — stale `"Pairs with 028"` note" and #"Card conflict — stale `mutations/ (planned)` predicted file" license the read that the genuine pairing is `DONE-036-0.0.11`.

### Spec `## Risks and open questions` items deferred by design (the durable follow-up list)

- **Clearing an existing file via mutation input** — spec `## Risks` #"Clearing an existing file via mutation input". This card does NOT promise a clear-file path: omitted upload leaves the file unchanged, provided upload replaces, explicit `null` on a `null=False` column is a `FieldError` (`_explicit_null_error`). Fallback deferred to a future form/serializer flavor (an explicit clear-file sentinel) if real users need it — Decision 6.
- **Output subfield nullability vs upstream parity** — spec `## Risks` #"Output subfield nullability vs upstream parity". The deliberate, documented divergence (`path` / `size` / `url` / `width` / `height` nullable; `name` non-null) shipped as the preferred answer (Decision 4). The fallback (keep `path` nullable at minimum, document local-storage-only for the rest) is recorded only as a contingency if the nullable subfields prove awkward downstream — no action needed now.
- **Image-content validation** — spec `## Error shapes` / `## Risks` (the `forms.ImageField` content-sniffing note). The generated `DjangoMutation` does NOT reject arbitrary non-image bytes; model-field validation + declared validators run, not `forms.ImageField` content sniffing. Upload content validation is deferred to a future `DjangoFormMutation` (`0.0.12`, `TODO-ALPHA-038`) / `SerializerMutation` (`0.0.13`) flavor — the card does not promise validation it cannot honestly enforce.
- **Storage-metadata read cost (no batching / caching)** — spec `## Risks` #"Storage-metadata read cost". Selecting `size` / `url` / `width` / `height` asks Django storage per object/subfield; this card does NOT batch or cache, and the optimizer cannot prefetch object-store metadata. A batching / caching layer (or a storage-metadata dataloader) is a profiling-gated follow-up — Decision 4.
- **File-column filtering contract** — spec `## Risks` #"File-column filtering contract". File columns keep the scalar `str` filter mapping in `SCALAR_MAP` (filtering the stored name/path string, not file metadata). The fallback — rejecting file/image filters with a `ConfigurationError` once a deliberate file-filter contract is designed — is a future follow-up, not this card (Decision 3).
- **Path-safety exception policy (`SuspiciousFileOperation` propagates)** — spec `## Risks` #"Path-safety exception policy". `SuspiciousFileOperation` is deliberately NOT folded into the `_safe_file_attr` degrade-to-`null` catch (it propagates as a top-level error so path-traversal / hostile-name conditions stay visible). The fallback (add it to the catch set for graceful degradation) is operator-preference-gated — the default is visibility (Decision 4). Pinned by a test; not deferred work, recorded as a deliberate contract the next author should not silently change.

### Spec `## Out of scope (explicitly tracked elsewhere)` — downstream cards that build on this one

- **Multipart request helper** — `TestClient` (`TODO-ALPHA-043-0.0.14`). Depends on the `Upload` scalar this card ships; the transport helper itself is `0.0.14`.
- **Form-based mutations** — `DjangoFormMutation` (`TODO-ALPHA-038-0.0.12`). Reuses `Upload` through the same scalar-map helper.
- **DRF serializer mutations + auth mutations** — `SerializerMutation` (`0.0.13`). Serializer upload handling builds on this scalar.
- **A live fakeshop file-upload surface** — deferred to fakeshop activation (`TODO-BETA-051-0.1.5`). This card covers both directions with synthetic-model tests (Decision 9); no live `/graphql/` upload coverage exists because no fakeshop model carries a file column.
- **Field-level read gates** — `FieldSet` / per-field permission hooks in `0.1.1`. File-metadata permissions are not special-cased here.
- **Remote-storage adapters, thumbnailing, image validation, signed-URL policies** — consumer/storage concerns beyond a model-field conversion card.

## Summary

Build-037 (upload_file_image_mapping / 0.0.11) is functionally complete and
**fully gate-clean**. The final test-run gate was run twice:

- **Prior gate (revision-needed):** all six commands passed EXCEPT the full
  `pytest --no-cov` sweep, which red on **one** pre-existing, out-of-scope test —
  `tests/orders/test_sets.py::test_orderset_request_from_info_raises_on_unrecognized_context_shape`
  — whose stale `"OrderSet.apply"` assertion lagged the committed
  `utils/permissions.py::request_from_info` message (the `.apply` suffix was
  deliberately dropped in commit `bd998093`, an orders/mutation-permissions
  refactor unrelated to this build). No 037 slice owned or introduced the failure;
  the recommended fix was a one-line orders-subsystem test re-pin belonging to the
  maintainer, not an 037 slice re-loop.

- **Final gate re-run (final-accepted, 2026-06-19):** after the
  maintainer-authorized one-line re-pin of that stale assertion to
  `"OrderSet could not resolve"` (a substring of the committed, intentional
  `request_from_info` message; the production helper was NOT changed), all six gate
  commands PASS. Full sweep: **2213 passed, 4 skipped, 4 xfailed, 0 failed** (the
  passing count rose 2212 → 2213, exactly the one re-pinned test, confirmed passing
  in isolation). Django system check, migration consistency, `ruff format --check`,
  `ruff check`, and `git diff --check` all PASS. The cross-slice integration pass
  found no consolidation needed.

Worker 1 did not (and per the gate rules must not) edit source or tests in either
gate pass; the re-pin pre-dated this re-run spawn. The one-line
`tests/orders/test_sets.py` re-pin is a separate out-of-scope concern from the
build-037 commit — the maintainer may wish to commit it separately.

The `### Deferred work catalog` is written end-to-end — the prior pre-existing
baseline defect is now marked **RESOLVED**, and the catalog carries the build-cycle
deferrals (Pillow dev-dep, the `DONE-037` `planningState` render, the three DB
drift reconciliations), every spec `## Risks and open questions` follow-up
(file-clearing, subfield nullability, image-content validation, storage-metadata
cost, file-column filtering, path-safety policy), and the `## Out of scope`
downstream cards (`0.0.12` form mutations, `0.0.13` serializer mutations, `0.0.14`
multipart `TestClient`, `0.1.5` live fakeshop upload surface, `0.1.1` field-level
read gates).
