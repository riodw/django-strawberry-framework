# Build: final test-run gate — card 046 (transport_security / 0.0.15)

Spec reference: `docs/spec-046-transport_security-0_0_15.md` (whole file; rationale companion
`docs/spec-046-transport_security-0_0_15-rationale.md`)
Build plan: `docs/builder/build-046-transport_security-0_0_15.md`
Status: built

This is the `BUILD.md` `## Final test-run gate` pass. Every prior box in the plan's
`## Checklist` is ticked: slices 1-5, review rounds 1 and 2, the round-2 residual review, the
cross-slice integration pass and the concurrent spec-custodian pass are all `final-accepted`.

**This pass wrote exactly one file: this artifact.** No production code, no test, no spec, no
rationale, no generated doc, no DB, no `.venv`. No `git` write command of any kind ran — the only
`git` invocations were `status --short` and `diff --check`. No `--cov*` flag was used; no
write-mode `ruff` ran. `examples/fakeshop/db.sqlite3` was read by the four renderers and never
reset.

## Gate results

Run in the order the gate prescribes. Exit statuses were captured directly (not through a pipe),
so every `exit 0` below is the command's own status.

| # | Gate | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` (full sweep, all three test trees) | **5202 passed, 40 skipped** in 78.43s (0:01:18) — **exactly** the declared baseline. exit 0 |
| 2 | `cd examples/fakeshop && uv run python manage.py check` | `System check identified no issues (0 silenced).` exit **0** |
| 3 | `cd examples/fakeshop && uv run python manage.py makemigrations --check --dry-run` | `No changes detected` exit **0** |
| 4a | `uv run ruff format --check .` | `405 files already formatted` exit **0** (plus the standing `COM812`-vs-formatter advisory warning, which is configuration, not a finding) |
| 4b | `uv run ruff check .` | `All checks passed!` exit **0** |
| 5 | `git diff --check` | no output, exit **0** |
| 6 | `uv run python scripts/check_spec_glossary.py --spec docs/spec-046-transport_security-0_0_15.md` | `OK: 37 terms - all have glossary entries and at least one spec link.` exit **0** |
| 7a | ASCII-only scan of this build's six dirty `.py` files | **0** non-ASCII lines in each: `routers.py`, `views.py`, `exceptions.py`, `_strawberry_patches.py`, `tests/test_views.py`, `examples/fakeshop/test_query/test_transport_api.py` (`LC_ALL=C grep -c -P '[^\x00-\x7F]'` -> `0` per file) |
| 7b | `uv run python scripts/check_trailing_commas.py --check <those six exact paths>` | no output, exit **0** |
| 8a | `docs/GLOSSARY.md` two-consecutive-regenerate byte-stability, rendered to scratch | `build_glossary_md.py --md <scratch>/g1.md` and `--md <scratch>/g2.md`, both exit 0; `cmp g1 g2` **identical**; `cmp g1 docs/GLOSSARY.md` **identical** |
| 8b | `KANBAN.md` same | `build_kanban_md.py --md <scratch>/k1.md` / `k2.md`, both exit 0; `cmp k1 k2` **identical**; `cmp k1 KANBAN.md` **identical** |
| 8c | `KANBAN.html` same | `build_kanban_html.py` rewrites its target **in place** (it replaces the data block inside the hand-edited Vue shell and errors on a missing file), so the tracked file was **copied** to scratch and both regenerates ran on the copies: `cmp h1 h2` **identical**; `cmp h1 KANBAN.html` **identical**. Corroborated by `build_kanban_html.py --check` -> exit **0**. The tracked file was never written |
| 9a | `uv run python examples/fakeshop/manage.py import_spec_terms --check` (`--check` exists, confirmed via `--help`) | `OK: 46 done cards have glossary links.` exit **0** — holds Slice 5's `OK: 46` |
| 9b | `uv run python scripts/build_tree_md.py --check` (`--check` exists, confirmed via `--help`) | `docs/TREE.md is up to date.` exit **0** |
| — | `git status --short` | **33 lines**, byte-identical population to the integration pass's final verification. Nothing newly dirtied, added, removed, or reverted by this pass (this artifact is untracked and makes 34 once written) |

**Pre-commit is deliberately NOT invoked.** `pre-commit` performs a stash round-trip, and this
tree carries a concurrent maintainer session's uncommitted work plus two untracked maintainer
scoping notes (`drys.md`, `vulns.md`) — a stash round-trip here races those writes. Gates 4a, 4b,
7a and 7b are the direct evidence substituting for it: they are the underlying checks the
`source-layout` and `ruff` hooks run, scoped to this build's own files. `check_trailing_commas.py`
was given **explicit paths** on purpose: its default is repo-wide **auto-fix**, which would
rewrite the maintainer's untracked notes. **Full `pre-commit` remains the maintainer's to run at
the commit**, per `START.md` #"When asked to commit, run the pre-commit hooks first".

### Suite-count attribution

None owed: `5202 passed, 40 skipped` matches the plan's declared baseline
(`### Round 2 is CLOSED`) and the integration pass's own final-verification reading exactly, so
there is no delta to attribute to this build or to a concurrent writer.

### Floor verification — the backstop confirms it happened

`BUILD.md` `## Final test-run gate` makes this gate the backstop, not a second owner. The plan's
floor-verification **scope** is an open escalation (recorded under `## Open maintainer decisions`
as part of M5's family) and this pass does not settle it. What is on disk:

- `bld-integration.md` `### Floor verification` — **owned by that pass and run.** Scratch venv
  outside the repo, `uv venv --python 3.10`, then `uv pip install --python <venv>/bin/python`.
  Resolved: Python **3.10.19**, `django 5.2` (`django==5.2.0` prints as `5.2`),
  `strawberry-graphql 0.316.0`, `channels 4.3.2`, `asgiref 3.12.1`. Scope
  `examples/fakeshop/test_query/test_transport_api.py --no-cov -o addopts=""` -> **69 passed**,
  against a pre-edit floor baseline of **69 passed**. Shared `.venv` proved unmutated afterwards.
- `bld-review-2-http_boundary.md` and `bld-review-2-w3_residual.md` each ran their own floor
  verification for the multipart request/body seam; the residual review **re-executed** rather
  than spot-checking, in a floor venv of its own.
- `bld-slice-5-docs_foldin.md` declared `none` in both the build report and the review, with the
  reason recorded (docstring-text `.py` delta only; everything else Markdown, DB, or scripts).

No floor venv was built by this pass, and none is owed: this pass changed no `.py` file.

## Deferred work catalog

Twenty-six items, each with an owner and an evidence pointer. Nothing is summarised away — where
a source recorded an exact string or anchor set, it is carried verbatim so no future pass
re-derives it.

### From `bld-slice-5-docs_foldin.md` `### For bld-final.md's Deferred work catalog`

1. **2d — the seven glossary `status_text` stamps, at the joint `0.0.15` cut.** Owner: the joint
   `0.0.15` cut (card 050). Evidence: `bld-slice-5-docs_foldin.md` `### Rulings on 2b, 2c, 2d, 2e`
   #"2d — `status_text = \"shipped\"`". The exact instruction, carried: set
   `GlossaryTerm.status_text` to ``shipped (`0.0.15`).`` on the seven anchors
   `djangographqlview`, `request-body-cap`, `utf-8-wire-contract`,
   `websocket-consumer-injection-seam`, `websocket-host-boundary`,
   `websocket-revalidation-window`, `connection-scoped-revocation`, then regenerate. It travels
   with the `README.md` / `TODAY.md` "Coming next" -> "Shipped today" move and with the
   `djangographqlprotocolrouter` entry's own ``shipped (`0.0.14`)`` -> `0.0.15` question. Bare
   `shipped` was **upheld** for this card, not merely tolerated: stamping `0.0.15` now would name
   a version that exists in no released artifact (the quintet reads `0.0.14`) and would take a
   step Decision 15 assigns to the cut.
2. **The terms CSV stays at 37 rows.** Owner: the maintainer. Evidence: same section, plus
   `### Ruling 3`. If the maintainer wants card 046's link set to include the seven terms it
   authored, that is one Worker-1 pass editing the CSV **and** the spec's
   `## Key glossary references` + link-def block together, then re-running `import_spec_terms`
   and `build_glossary_md.py`. Gate 6 and gate 9a are both green at 37 / 46 as it stands.
3. **`definition_of_done` order 5 stays unticked.** Owner: the maintainer, **after this gate** —
   coverage is the maintainer's gate and the full-suite / lint / `manage.py check` sweep is the
   pass you are reading. Evidence: `### Ruling 4`'s deliberate non-tick, recorded as the slice's
   one-line deferral.
4. **L4 — the one clause `docs/README.md:360` could gain about body-reading project
   middleware.** Owner: the maintainer (path (a) if preferred). Ruling on record: **path (c) plus
   a nudge** — Decision 8 does not require it, `views.py::_run_after_csrf_check` already carries
   it in bold for a code reader, and the counted half of the same section already states its own
   honest boundary, so the code docstring is the authoritative statement.
5. **L2 — `README.md:62`'s `0.0.14` paragraph describes `main`'s router shape inside the released
   version's sentence.** Owner: the joint `0.0.15` cut, which rewrites that paragraph anyway for
   the "Shipped today" move. Chosen framing on record: lead with the marker, the shape
   `docs/README.md:128` and `TODAY.md:384` already use.
6. **L5 — `BACKLOG.md:1616` / `:1661` describe the router as serving HTTP + WebSocket in the
   present tense.** Owner: a future spec author. Deliberately outside spec-046's `## Doc updates`
   set.
7. **Do not act — closed `docs/review/`, `docs/dry/` and `docs/bug_hunt/` scratchpads still
   assert the old "UTF-16 succeeds" contract.** Owner: nobody; **leave them.** They are closed
   per-cycle records. Named here so a future sweep does not read them as live claims and does not
   "fix" them.

### From `bld-integration.md` `## Items routed OUT of this pass`

8. **L9 — the third fail-closed path logs nothing.** `consumers.py:787`, the `Host` denial, while
   the other two now log. Owner: the maintainer (contract-level, already routed as amendment A4).
   Recommendation from three separate passes, unchanged: **log all three, no wire change.** New
   evidence on record: Django's own `django.security.DisallowedHost` `error`-level logging of
   every `SuspiciousOperation`, read at the installed 6.0.5 and **unconfirmed at the 5.2.0
   floor**.
9. **`conf.py:117` `#"EXCEPT for a multipart request"` — the fifth L3 surface.** Owner: **the
   maintainer, sequenced only.** This is the maintainer's own concurrent dirty file:
   **never edited, never reverted by a worker.** The clause is quoted in `bld-integration.md` so
   it can be applied without re-deriving it. Confirmed still open at the integration pass's final
   verification (`grep "POST-scoped"` over `conf.py` -> no hit), and confirmed still open here —
   this pass did not touch the file.
10. **L-B — `tests/test_views.py:1320::_strawberry_patch_opted_out` lacks the live copy's
    `assert strawberry_patches._patch_is_installed() is False`.** Nothing pins that the
    package-tier simulation really un-installed the patch. Owner: a future test pass. Recorded,
    deliberately not dispatched.
11. **The cross-tree test-helper ruling** (`_capped_view`, `_strawberry_patch_opted_out`,
    `_multipart_body` / `_multipart_bytes`). Owner: nobody; the ruling **stands**. No shared home
    exists, creating one is the wrong trade, and the mechanical reasons are recorded in
    `bld-integration.md` so a future reviewer neither re-raises it per helper nor "fixes" it by
    adding an `__init__.py`.
12. **`auth/mutations.py`'s repeated literals** (`password` 7x, `register` 4x, `current_user`
    3x). Owner: the maintainer — **pre-existing** to this card (the build touched only that
    file's three transport strings) and a maintainer dirty file. Named so the shadow report's
    entry is not read as this build's residue.

### From `bld-custodian-3-claim_audit.md` `## Divergences noticed and NOT fixed` — still open after Worker 1's final verification

Worker 1's rulings are in `bld-integration.md` `### Rulings on the routed leftovers`.

13. **Item 1 — Decision 7 says the probe "reaches for **four** capabilities"; the code guards
    **six** call sites across **five** `try` blocks.** Owner: **its own dispatch** — the audit
    left it because fixing the number means editing the paragraph whose bolded opener four other
    sites cite by `#"substring"`. Evidence: `_declares_seekable`'s `seekable()`, the position
    `tell()`, `stream.seek(0, SEEK_END)`, `_position_restored`'s restoring `seek`, its verifying
    `tell()`, and the `end - position` subtraction; `_position_restored` guards two of them in one
    `try`. `## Edge cases`'s capability bullet repeats the same four-item list, so the fix has two
    sites. Both are internally consistent, which is why nothing is *false* — but the two omitted
    calls are precisely the ones correction 1 turns on. Worker 1's B-L1 spot-verification
    independently re-derived six-guarded-calls / five-`try`-blocks by reading `_request_body.py`
    end to end.
14. **Item 2 — `consumers.py::send_revalidated_operation_frame`'s docstring says the derived
    adapter stays a "two-line delegation"; `_RevocationGatedWebSocketAdapter.send_json`'s body is
    **four** statements.** Owner: the next pass that legitimately opens `consumers.py` — **not an
    opening of that file for its own sake.** Ruled **not a gate blocker** by Worker 1 for three
    reasons: `git status --short django_strawberry_framework/consumers.py` is **clean**, so the
    false clause is committed and **pre-existing** to round 3 rather than a regression this build
    introduced; it is a **private** module docstring with no consumer-facing surface, unlike M1's
    public constructor; and M1's corrected `routers.py` paragraph points at `consumers.py` for the
    **checkpoint** contract, not for the delegate's shape. **The replacement text is
    pre-measured — carry it verbatim rather than re-deriving it:** "a four-statement delegation -
    the frame-type test, the plain `super()` delegation for a non-information-bearing frame, its
    `return`, and the gated call".
15. **Item 5 — why the last-validated timestamp lives on the ASGI `scope` rather than beside the
    lock and the flag on the consumer instance is stated nowhere.** Owner: **the maintainer** —
    "it belongs to whoever decided it". Confirmed as a real spec gap by Worker 1, who verified the
    gap rather than the record: `consumers.py:209-214`'s comment on `_REVALIDATED_AT_SCOPE_KEY`
    explains only the key's collision-safe namespacing, and neither the spec nor the rationale
    states a reason. Correction 3 recorded the fact and correctly invented no reason.
16. **Item 6 — the spec nowhere states how the outbound gate reaches the consumer's lock.** The
    two hops are `websocket.ws_consumer` (the adapter seam) and `handler.view` (admission). Owner:
    the maintainer or a future custodian pass; it is a **one-clause addition to Decision 16**
    whenever a pass legitimately opens that decision. Verified mechanically by Worker 1:
    `grep -c "ws_consumer"` over the spec -> **0**. An omission, not a divergence, so nothing in
    the spec is false.
17. **Item 9's process proposal — "a downstream doc more accurate than the spec means the
    contract moved", as a first-class sweep.** Owner: **the maintainer, as a `BUILD.md` closeout
    candidate.** `BUILD.md` was not edited. The evidence is this build's own: the tell fired four
    times, and on corrections 8 and 9 the shipped docstring and `docs/README.md` were right while
    the spec was stale — it located two of the nine corrections before an auditor did. As a
    candidate step: at the integration pass, diff every consumer-facing or docstring telling of a
    contract against the spec's, and read a disagreement as **the spec being stale by default**.
    Bounded by the corpus ratchet.
18. **Item 8 — the DRY `parse_json` bullet attributes `_validate_upstream_shape` to "the
    upstream-mounted path".** That gate decides whether the patch installs at all, for **every**
    mount, so pairing it with the genuinely path-scoped `UnicodeDecodeError` translation under one
    prepositional phrase is loose. Owner: a future custodian pass. Explicitly **not** the same
    false scoping as correction 8 — it makes no "only mount" claim — which is why it was left.
19. **Item 3 — recorded no-op.** The DRY revalidation bullet prices the delegates by `await`
    count ("a single `await` and a `super()` call each"; the adapter "one type test, one `await`
    and a `super()` call"). Literally, each handler body has two `await` expressions and
    `send_json` has two `await`s and two `super()` references. On the natural reading it is not
    false, so it was left — but it is correction 4's shape and a reviewer counting literally will
    raise it.
20. **Item 4 — recorded no-op.** `## Implementation plan` row 4 reads "the adapter-level
    outbound-frame gate, **its** connection-local lock and **its** one close code". With
    corrections 2 and 3 landed, "its" invites the adapter reading the spec no longer makes
    anywhere else. The cell states no ownership location, so it is not false; it wants one word if
    a later pass touches the table.
21. **Item 10 — recorded no-op.** The rationale's Decision 19 historical block still contains
    "only a factory". Left **on purpose** — it is introduced as the prior spec wording. Recorded
    so a future grep for the phrase does not read it as a missed site.

**Custodian item 7 is CLOSED, not deferred**, and is listed here only so a sweep does not
re-raise it: Worker 1 ruled the two residual history-narrating phrases (spec `:1152`
#"This is the only new refusal" and `:1337` #"previously a Channels-routed deployment never
reached that adapter at") **no-change**, confirming Worker 3's recommendation — both describe
shipped `0.0.14` behavior, which the spec is entitled to state.

### Open maintainer decisions — recorded, not re-litigated

22. **M4 — whether the weakly-pinned rule is applied literally.** Twelve round-2 boundaries fail
    the 0-1-row test; the reviewer's own merit ruling is that M2 and M3 were genuine gaps (both
    remediated), four more deserve a second row on merit, and the remaining six are adequate on
    merit and fail only the rule as written. Applying it literally re-loops all twelve. Related:
    the rule says "never a recorded exception" while `bld-review-2-w3_review.md` Q7 records one
    ("weakly pinned but adequate"), so the rule needs either a narrow carve-out or that entry
    becomes `revision-needed`. Owner: the maintainer. Source: the build plan's
    `## Open maintainer decisions`.
23. **M5 — the plan carries no hot-path declaration, and the round owes a number.** The
    WS-revocation design holds one connection-local lock **through** the outbound send, which
    meets `BUILD.md` `## Hot-path budget`'s definition and which the spec itself calls a hot path.
    Options on record: (a) declare the slice hot-path and re-loop the cohort for a before/after
    number — `_instrument_revalidation`'s `probe.reads` is already the instrument; or (b) an
    explicit waiver naming the number as not required for this card. The plan's
    floor-verification **scope** line points at the same escalation. Owner: the maintainer.
24. **`AGENTS.md:15` vs. scoped `ruff`.** All four role files tell workers to scope
    `ruff format` / `ruff check --fix` to their own files, because this tree carries concurrent
    uncommitted work and a repo-wide write-mode run reformats it. `AGENTS.md:15` mandates the
    repo-wide form and the role files defer to `AGENTS.md` on conflict, so **the scoping
    instruction is inert until this is reconciled.** Also recorded in commit `84c6075b`'s message.
    Six-plus passes have raised it. Owner: the maintainer. (No write-mode `ruff` ran in this pass
    either; gates 4a/4b are the read-only repo-wide form, which is unambiguous.)
25. **B-L2's artifact-naming question.** The custodian artifact
    (`bld-custodian-3-claim_audit.md`) was absent from the plan's `## Artifact list`; Worker 0
    closed that by **correcting the list rather than renaming the file**, since the name predates
    the finding. What stays open is the underlying `BUILD.md` question — whether
    `## Build artifact naming` should admit a `bld-custodian-*` form at all. Owner: the
    maintainer.
26. **`bld-slice-4-ws_revalidation.md:9`'s `Status: planned` hygiene lapse — recorded, not
    repaired.** The slice is `final-accepted` in substance and closed and committed; the line was
    left alone deliberately, on the same reasoning as round 2's four `Status:` violations
    (`### Artifact Status: hygiene lapse in round 2 — recorded, not silently repaired`): Worker 0
    writing that line now would be writing `Status:`, which `worker-0.md` forbids, and the pass
    that owed it is closed. Owner: the maintainer. **This pass did not repair it** — this gate
    writes only `bld-final.md`.

## Version quintet

**Untouched by this build, and correctly so.**

- `pyproject.toml:4` — `version = "0.0.14"`
- `django_strawberry_framework/__init__.py:41` — `__version__ = "0.0.14"`
- `tests/base/test_init.py:21` — `assert __version__ == "0.0.14"` (the full suite's green at gate
  1 is the assertion of that pairing)
- `CHANGELOG.md` — no `0.0.15` entry, and no slice in this build edited it

Card `TODO-ALPHA-050-0.0.19` (Extract `DjangoDebugExtension` into the standalone
`django-strawberry-debug` package) is still `todo` on the `0.0.15` line — `KANBAN.md:150` renders
it under a `TODO-ALPHA-` id. Per `docs/SPECS/NEXT.md` Step 3 and **spec-046 Decision 15**, the
version quintet is owned by the **last card of the `0.0.15` line to land**, which is card 050.
**Card 045 owns the joint cut.** Catalog items 1, 3 and 5 are the work that travels with it.

## Verdict

Every gate is green on the declared numbers: the full suite at exactly **5202 passed, 40
skipped**, both Django consistency checks clean, both read-only `ruff` gates clean,
`git diff --check` clean, the spec-glossary check at `OK: 37 terms`, the pre-commit-equivalent
ASCII and trailing-comma checks clean on all six of this build's dirty `.py` files, all three
generated docs byte-stable across two consecutive scratch regenerates **and** byte-identical to
the tracked files, and both `--check` modes at gate 9 green. `git status --short` is unchanged at
33 lines. Floor verification is confirmed to have been run by the passes that owned it.

`Status: built`. Twenty-six deferred items are cataloged with an owner and an evidence pointer
each; five of them (items 1, 3, 5, 22, 23) plus the remaining maintainer items are what the
maintainer sees first at the handoff.
