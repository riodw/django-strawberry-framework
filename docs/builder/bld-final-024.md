# Build: Final test-run gate (card `DONE-024-0.0.7`)

Spec reference: `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md` and its companion
`docs/SPECS/appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md`
Status: final-accepted

HEAD at this pass: `ddf8bbaf` ("finish 23"), read with `git log -1` at pass start and re-read at
close; unchanged across the pass.

**The tree is legitimately dirty with a concurrent cycle's uncommitted work** — the `spec-021` /
`spec-022` / `spec-023` files, `KANBAN.md`, `KANBAN.html`, `CHANGELOG.md`, `docs/GLOSSARY.md`,
`examples/fakeshop/db.sqlite3`, the `docs/builder/*-023*` artifacts, and (appearing mid-pass)
`django_strawberry_framework/optimizer/hints.py`, `tests/optimizer/test_hints.py`,
`examples/fakeshop/apps/scalars/models.py`, `examples/fakeshop/test_query/test_scalars_api.py`. Every
result below is graded against **this cycle's diff**, which is exactly two Markdown files plus one
`.py` docstring line.

## Gate results

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** — `6179 passed, 40 skipped in 103.98s`, exit 0 |
| 2 | `FAKESHOP_SHARDED=1 uv run pytest --no-cov` | **PASS** — `6191 passed, 37 skipped in 108.84s`, exit 0 |
| 3 | `uv run python examples/fakeshop/manage.py check` | **PASS** — `System check identified no issues (0 silenced).`, exit 0 |
| 4 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — `No changes detected`, exit 0 |
| 5 | `uv run ruff format --check .` | **PASS** — `424 files already formatted`, exit 0 |
| 6 | `uv run ruff check .` | **PASS** — `All checks passed!`, exit 0 |
| 7 | `git diff --check` | **PASS** — no output, exit 0 |
| 8 | Floor verification | **PASS, cited not re-run** — see below |

No `--cov`, `--cov-report`, or `--cov-config` flag was used anywhere in this pass. `--no-cov` is
required because `pytest.ini`'s `addopts` auto-applies `--cov`, and it is the only coverage-shaped
flag used. No line-coverage figure was inspected or asserted.

### 1 and 2 — the two full sweeps

Both run to completion across all three test trees, both exit 0, **zero failures and zero collection
errors in either**. Raw output retained at `docs/builder/temp-tests/024-final/full-sweep.txt` and
`…/sharded-sweep.txt` (gitignored).

The sharded run is **load-bearing for this card, not optional**: `FAKESHOP_SHARDED=1` is the only
mode configuring more than one database alias, and this card's subject is a multi-database teardown
patch — Django wraps disallowed connection methods precisely on the aliases a test case does not
permit. The spec states the same reasoning at `### Decision 10` ("an extra run of the same tests, not
a separate suite") and `## Definition of done` item 9 names the sharded invocation explicitly. An
earlier pass ran the focused scope sharded; this is the full sweep.

The two runs differ by `6179 + 40` vs `6191 + 37` because the sharded mode collects its own gated
rows and skips the default-mode-only ones — the mutual exclusion `AGENTS.md` rule 29 describes.
Nothing in this card's 31 tests is gated either way; they run under both.

**No failing node id to record and nothing to escalate on this account.** Had a failure appeared in a
file outside this cycle's diff, `docs/builder/BUILD.md` `## Claims are proven mechanically, never
accepted on prose` would have made it not worker-verifiable at HEAD from this dirty tree and it would
have been recorded and escalated rather than fixed. No such case arose.

### 5, 6, 7 — lint / format / diff, all read-only

Never `--fix`, never a revert. All three came back clean over the **whole tree**, so no attribution
question arose: there is no hit to attribute to a concurrent session and none to this cycle. `ruff
format --check` emits its standing `COM812` formatter-conflict warning, which is a configuration
notice present on every run in this repo and not a failure (`AGENTS.md` rule 17 makes
`scripts/check_trailing_commas.py`, not ruff, the owner of single-line explosion).

Doc-side gates re-run after this pass's one spec edit:
`uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-024-…md` -> `OK: 2 terms`,
exit 0; `uv run python scripts/check_trailing_commas.py --check` over both permanent files ->
exit 0, silent.

### 8 — Floor verification, cited and confirmed

The build plan's `## Declarations` assigns the cycle's single floor run to **Slice 1b**, which owns
it; `docs/builder/BUILD.md` `## Final test-run gate` makes this gate the **backstop confirming it
happened**, not a second owner. It was performed by Slice 1b and **independently re-executed in full
by that slice's review** — venv resolution, focused scope, and the discriminator probe, the last
written separately by the reviewer.

Recorded in `docs/builder/bld-slice-1b-024-divergence_and_floor.md` `### Floor verification`:

- Scratch venv `/tmp/dsf-floor-024`, outside the repo; every install carried an explicit
  `--python /tmp/dsf-floor-024/bin/python`. The shared `.venv` was never installed into.
- Resolved versions as read with `uv pip list --python …`: **Python 3.10.19, Django 5.2.16,
  strawberry-graphql 0.316.0** — matching `docs/builder/BUILD.md` `## Floor verification`'s single
  canonical statement of the supported floor, which is where this pass read the floor triple from,
  never from memory or from another document.
- Focused scope `tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py` ->
  **36 passed**, exit 0. Same scope in the shared `.venv` -> 36 passed.
- The result the run exists to produce: at the floor the **class-attribute** audited body is the
  validated one (the shape covering `5.2.16`-`6.0.x`, i.e. most of the supported range); in the
  shared `.venv` the **connection-feature** body is. That branch is executed by no other run in this
  cycle.

**Plan scope discharged:** the declaration named one slice, one focused scope, and one owning pass;
all three are satisfied and the recorded scope is exactly the plan's. Not rebuilt here — rebuilding
would destroy the artifact a later reader re-derives from, and the run is already double-executed.

*Note for a later re-deriver:* `/tmp/dsf-floor-024` no longer exists on this machine (scratch under
`/tmp` is reaped). The recorded commands rebuild it in three steps; the recorded numbers stand as the
evidence of the run, which is what `docs/builder/BUILD.md` asks be preserved.

## Slice checklist audit

Card 024's archived spec was a stub with no `## Slice checklist`, so no cycle artifact carries a
`### Spec slice checklist (verbatim)` with boxes to audit. Slice 3 carries a
`### Dispatched findings checklist` instead; its five boxes were walked one by one against evidence
at that slice's final verification and all five upheld. Nothing is silently un-ticked anywhere in the
cycle, so nothing blocks `final-accepted` on that ground.

## Artifact status at close

| Artifact | `Status:` |
|---|---|
| `docs/builder/bld-slice-1a-024-planned_vs_head.md` | `final-accepted` |
| `docs/builder/bld-slice-1b-024-divergence_and_floor.md` | `final-accepted` |
| `docs/builder/bld-slice-2-024-spec_reconciliation.md` | `final-accepted` |
| `docs/builder/bld-slice-3-024-rename_rot_sweep.md` | `final-accepted` |
| `docs/builder/bld-integration-024.md` | `final-accepted` |
| `docs/builder/bld-final-024.md` (this file) | `final-accepted` |

## Spec changes made (Worker 1 only)

**One, made during the integration pass and recorded in full in
`docs/builder/bld-integration-024.md` `### Spec changes made (Worker 1 only)`.** Restated here
because this file is the gate's record:

`docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md` stated the `docs/TREE.md` regenerate
obligation over three modules at two sites (the `## Key glossary references` conventions bullet and
the `## Edge cases and constraints` downstream-consumer bullet). The measurement re-derived during
the consistency scan shows **six** of this card's own surface modules feed `docs/TREE.md` — the three
package modules plus `tests/test_django_patches.py`, `tests/testing/test_wrap.py`, and
`tests/test_apps.py`. Both sites now name all six. No other change was made to either permanent file
by this pass, and no `.py` file was written by it.

## Escalated to the maintainer

Two items, neither a worker's call, both also carried in the catalog below so the next spec author
sees them:

1. **No gate in this process resolves a symbol citation** (catalog item 5). Contract-level, three
   resolution paths, raised by Slice 3 on measured evidence rather than on a schedule.
2. **`spec-021` and `spec-024` disagree about who delivered the three `ready()` tests** (catalog
   item 7). Both sides are internally consistent; `spec-021` is baseline-dirty and outside this
   cycle's scope, and a correction applied only to the editable side would be worse than a stated
   disagreement.

Nothing was escalated on a gate failure: every gate passed.

## Deferred work catalog

The next spec author's reading list. This is the **union** of all four artifacts' deferred lists —
1a's, 1b's, and Slice 3's are near-disjoint (1a and 1b overlap only on `docs/GLOSSARY.md`; Slice 3's
is disjoint from both), and item 7 was raised by Slice 2's apply-changes pass, so **no single list is
complete**. Everything here is outside this cycle's maintainer-set scope (spec files and `.py` files
only; no closeout or agentflow edits) or outside card 024's ownership.

**A catalog is a claim.** Every count below was re-derived at this pass rather than copied from the
artifact that raised it — the cycle has already moved several on re-derivation — and each bullet says
which artifact section owns it and what licenses the deferral.

1. **`CHANGELOG.md`'s `0.0.7` hardening entry carries two false claims and sits under the wrong
   heading.** *Source:* `bld-slice-1a` deferred item 20 and `bld-slice-2` catalog item 1.
   *Deferral licensed by:* the build plan's `## Cycle type and scope` (`CHANGELOG.md` excluded) and
   its baseline-dirty list. Re-measured at this pass: one bullet under `## [0.0.7]` -> `### Added`
   says consumers need "no settings key" (`APPLY_UPSTREAM_PATCHES` exists — `conf.py` defines it and
   the spec's Decision 6 states it) and that "a log-once sentinel suppresses repeated missing-symbol
   notices" (`grep -c logger django_strawberry_framework/_django_patches.py` -> **0**; the sentinel
   arrived at `744fd28d` and was deleted at `48f9f65d`). The `## [0.0.7]` section does carry a
   `### Fixed` heading, which is where the recovered plan's DoD item 9 asked for it. Low.
2. **`docs/GLOSSARY.md`'s `## Django Trac #37064 hardening` entry is stale.** *Source:* `bld-slice-1a`
   item 21 and `bld-slice-1b`'s escalations — the **only** item both cohorts found. *Deferral
   licensed by:* the same scope restriction. Re-read at this pass: it says "no `conftest.py`
   workaround, no base test class to inherit, no settings key required" — true only on that last word
   — and describes the patch as unconditional. `APPLY_UPSTREAM_PATCHES`, the audited-body pin, and the
   fail-loud `RuntimeError` are absent from the entry entirely. Note the sibling
   `## Django AppConfig` entry **is** current on the gate, so the staleness is local to this entry.
   The `safe_wrap_connection_method` entry was not audited by this cycle. `docs/GLOSSARY.md` is
   DB-generated: the fix is a DB edit plus `scripts/build_glossary_md.py`, never a hand edit.
3. **`docs/TREE.md` carries six of this card's module summary lines, twelve occurrences.** *Source:*
   `bld-slice-1b`'s escalations (which stated **two**) as corrected by `bld-slice-2` catalog item 3.
   *Deferral licensed by:* the scope restriction (`docs/TREE.md` excluded; it is script-rendered).
   Re-derived independently at this pass by extracting each module's docstring first line with
   `ast.get_docstring` and counting occurrences in `docs/TREE.md`: `_django_patches.py` 2, `apps.py`
   2, `testing/_wrap.py` 2, `tests/test_apps.py` 2, `tests/test_django_patches.py` 2,
   `tests/testing/test_wrap.py` 2 — **six distinct lines, twelve occurrences** (each renders twice,
   once per view). Provenance confirmed: `4a25bf42` set the three package modules' first lines,
   `7c2a63ed` the three test modules'. The **obligation** to regenerate is now stated in the spec for
   all six (see `### Spec changes made`); what remains deferred is any actual `docs/TREE.md` edit.
4. **Seven citation defects in `.py` docstrings and comments belonging to other cards.** *Source:*
   `bld-slice-3` `### Out-of-scope deferrals` and its review's Low 1, as carried by `bld-slice-2`
   catalog item 4. *Deferral licensed by:* `AGENTS.md` #"Source refs in docs and code comments use
   symbol paths never line numbers", which binds the sweep to the change that renamed the symbol —
   none of these renames is card 024's. All are `.py` files, so all are eligible work for a future
   cycle. Counts re-derived at this pass with `grep -ro` (occurrences, not matching lines) over
   `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`:
   - `django_strawberry_framework/utils/relations.py #"mutations/inputs.py::_select_editable_fields"`
     — **1**. Never defined at any revision.
   - `django_strawberry_framework/utils/relations.py #"mutations/resolvers.py::_index_relation_fields"`
     — **1**. Same shape.
   - `django_strawberry_framework/utils/querysets.py #"mutations/resolvers.py::_raw_pk_relation_error"`
     — **1**. Defined once, removed at `e9c13f55` without the sweep.
   - `django_strawberry_framework/utils/querysets.py #"mutations/resolvers.py::_relation_membership_error"`
     — **2**. Same commit, same omission.
   - `django_strawberry_framework/utils/querysets.py #"forms/resolvers.py::_visible_related_object"`
     — **1**. Wrong module: the symbol is
     `django_strawberry_framework/types/resolvers.py::_visible_related_object`.
   - `django_strawberry_framework/consumers.py #"auth/mutations.py::logout"` — **1**. The symbol is
     `logout_mutation`; there is no bare `logout`.
   - The renamed optimizer test
     (`tests/optimizer/test_extension.py::test_optimizer_elides_forward_fk_id_only_selection`) —
     **3 occurrences in 2 files** end-anchored: `tests/test_list_field.py` 2,
     `examples/fakeshop/test_query/test_scalars_api.py` 1. An **unanchored** sweep over the same
     corpus returns **7 occurrences in 4 files** (`tests/test_list_field.py` 2,
     `examples/fakeshop/test_query/test_scalars_api.py` 2, `tests/optimizer/test_extension.py` 2,
     `tests/test_permissions.py` 1), of which only the 3 are rot — the other 4 cite the live
     `…_selection_plan_shape` / `…_for_each_alias_plan_shape` names, both confirmed defined at
     `tests/optimizer/test_extension.py`. Anchoring at the identifier's **end** is what separates
     them; both figures re-derived at this pass and both reproduce exactly.
     **Re-measure before homing:** `examples/fakeshop/test_query/test_scalars_api.py` is under a
     concurrent session's uncommitted edit as of this pass.
5. **Contract-level, escalated to the maintainer — no gate in this process resolves a symbol
   citation.** *Source:* `bld-slice-3` `### Escalated to the maintainer` and `bld-slice-2` catalog
   item 5. *Deferral licensed by:* `docs/builder/BUILD.md` `### Contract-level findings are escalated
   as maintainer decisions before dispatch` — no worker may decide it. `eb2a1764` passed tests, ruff,
   and review and still shipped a dangling cross-module citation that survived four months;
   `AGENTS.md` rule 27 states the obligation and nothing mechanically enforces it. Three paths:
   (a) commit the reviewer's `scripts/check_citations.py` and wire it as a pre-commit hook, making
   the rule mechanical the way `check_trailing_commas.py` and `check_spec_glossary.py` already are —
   `scripts/` sits outside the coverage gate, so this adds no coverage obligation; (b) commit it
   CI-only, catching it before merge rather than before commit; (c) accept per-cycle re-derivation.
   **The measured cost of (c) in this cycle alone is nine citation defects in three kinds:** one
   in-scope repair (landed, Slice 3), seven out-of-scope findings (item 4), and one invented symbol
   name (`_PATCH_ORIGINAL`) produced *inside* this cycle by a pass whose subject was citation
   correctness — caught only by a throwaway resolver written for a review. Re-derived at this pass:
   1 + 7 + 1 = **9 defects**. That figure is a **defect** count and not an occurrence count, and the
   two must not be conflated: item 4's seven defects sum to **10 occurrences**
   (1 + 1 + 1 + 2 + 1 + 1 + 3), so the corpus-wide occurrence total is 12, not 9. The first draft of
   this bullet asserted the two coincided; they do not, and the arithmetic was re-run rather than
   read back. Stating both quantities with their jobs named is the fix, per `docs/builder/BUILD.md`
   `## Claims are proven mechanically, never accepted on prose`.
6. **A pre-existing duplicated docstring fragment in a writable file.** *Source:* `bld-slice-3`
   `### Notes for Worker 1` item 4 and `bld-slice-2` catalog item 6. *Deferral licensed by:* nothing
   — it is in scope for this cycle's `.py` surface, and is deferred because it fell between two
   slices' contracts (Slice 3's is rename rot, Slice 2's is Markdown-only) and because a source edit
   at the gate would ship unreviewed. Confirmed at this pass **both at HEAD and in the working tree**:
   `django_strawberry_framework/_strawberry_patches.py #"Three lifecycles, and one that left"` is
   followed by the dangling truncated clause `independent upstream *bugs* that do not retire
   together:` standing alone immediately before the complete sentence that contains it — the fragment
   occurs **twice**, once orphaned and once in its sentence. A copy-paste artifact, not rename rot.
   The fix is a one-line deletion and it needs an owner: whichever pass next owns that docstring.
7. **`docs/SPECS/spec-021-apps-0_0_7.md` and `spec-024` disagree about who delivered the three
   `ready()` tests.** *Source:* `bld-slice-2`'s apply-changes pass (raised while fixing M1), upheld by
   its re-review. *Deferral licensed by:* the build plan's baseline-dirty list (`spec-021` is a
   concurrent cycle's, read-only here). Re-measured at this pass: `tests/test_apps.py` held **5**
   tests at `300e2811^` and holds **8** at HEAD; card 024's three surface commits added the three
   (`300e2811` -> `test_djangostrawberryframeworkconfig_defines_ready_for_django_patches`,
   `136c5476` -> `test_ready_dispatches_all_three_patch_appliers_and_refires_safely`,
   `18550f5d` -> `test_ready_reinstalls_patches_after_their_modules_reload`), all three already rows
   in the rationale's change record. `spec-021`'s Slice-2 step 2 ("Ship `tests/test_apps.py`
   containing … and the three tests pinning `ready()` and its dispatch") and its DoD item 4 ("the 8
   tests listed in the Test plan … and 3 pinning `ready()`") both read them as spec-021 deliverables,
   while `spec-024` now states its own population as **31** and names the other five as spec-021's.
   The same `spec-021` file already says at its KANBAN doc-update bullet that the `ready()` body
   "arrives with sibling card `DONE-024-0.0.7`", so the file is internally split too. The maintainer's
   call: either `spec-021` reframes the three as a file-content fact contributed by the sibling card,
   or `spec-024` gives them up. Nothing was changed on the editable side, because a one-sided
   correction is worse than a stated disagreement.

### Not deferred — items an artifact raised and this cycle discharged

Recorded so a later reader does not re-home work that is done:

- **`bld-slice-1a` item 19** — the `_strawberry_patches.py` dangling citation. **Repaired** by
  Slice 3 and `final-accepted`; the retired name has 0 whole-token occurrences tree-wide and the
  replacement resolves.
- **`bld-slice-1a` item 22** — the recovered planning documents' dead
  `django_strawberry_framework/test/…` and `tests/test/…` paths must not be inherited into spec text.
  **Discharged:** the spec's only `…test` path occurrence is the Decision 9 sentence saying the path
  is never that, and the rationale's are inside retired-claim bullets.
- **`bld-slice-1b`'s dispatch-framing corrections** (6 of 21 commits are in-tag, not 0; the
  `e145ba36` -> `7cc163db` -> `4a25bf42` order; 8 flips, not "at least one"). **Discharged:** all
  three are stated correctly in the rationale's change record and preamble.

Status: final-accepted.

---

## Final test-run gate, re-run after Slice 4

**This section is an append. Nothing above it was edited.** The record above is the gate as it stood
when the cycle first closed, and it stays the record of that run; this section is a second,
independent run of the same gate over a diff the first run never saw.

**What the earlier record covered versus what this one does.** The earlier record graded a cycle diff
of **two Markdown files plus one `.py` docstring line** — the spec and its rationale companion, plus
Slice 3's citation repair in `django_strawberry_framework/_strawberry_patches.py` (the module
docstring's `_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE` -> `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES`
rename-rot fix). Slice 4 was dispatched post-gate on the maintainer's instruction
(`docs/builder/build-024-django_trac_37064_hardening-0_0_7.md` `## Slice 4 dispatch (post-gate,
maintainer-directed)`, which states that the slice re-opens the gate) and adds a **second `.py`
docstring line** to that diff: the deletion of an orphaned standalone
`independent upstream *bugs* that do not retire together:` from the same file's
`Three lifecycles, and one that left` section. This run therefore grades the same file at
`git diff HEAD` = **two hunks, `1 insertion / 2 deletions`**, where the first run graded it at one
hunk. The earlier record is not read forward onto that larger diff.

HEAD at this pass: `ddf8bbaf` ("finish 23") — `git log --oneline -1` read at pass start and again at
close, unchanged, and the same commit the earlier record names.

**The tree is still legitimately dirty with concurrent cycles' uncommitted work**, now including the
`spec-021` / `spec-022` / `spec-025` / `spec-026` files and their `docs/builder/*-025*` / `*-026*`
artifacts alongside `KANBAN.md`, `KANBAN.html`, `CHANGELOG.md`, `docs/GLOSSARY.md`,
`docs/feedback.md`, `examples/fakeshop/db.sqlite3`,
`django_strawberry_framework/optimizer/hints.py`, `tests/optimizer/test_hints.py`,
`examples/fakeshop/apps/scalars/models.py`, and `examples/fakeshop/test_query/test_scalars_api.py`.
None of it was reverted, stashed, or checked out. The dirty `.py` set is exactly five files;
**`django_strawberry_framework/_strawberry_patches.py` is the only one in this cycle's diff**, and
every result below is graded against that diff.

### Gate results

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** — `6179 passed, 40 skipped in 194.50s (0:03:14)`, exit 0 |
| 2 | `FAKESHOP_SHARDED=1 uv run pytest --no-cov` | **PASS** — `6191 passed, 37 skipped in 84.64s (0:01:24)`, exit 0 |
| 3 | `uv run python examples/fakeshop/manage.py check` | **PASS** — `System check identified no issues (0 silenced).`, exit 0 |
| 4 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — `No changes detected`, exit 0 |
| 5 | `uv run ruff format --check .` | **PASS** — `424 files already formatted`, exit 0 |
| 6 | `uv run ruff check .` | **PASS** — `All checks passed!`, exit 0 |
| 7 | `git diff --check` | **PASS** — no output, exit 0 |
| 8 | Floor verification | **NOT RE-RUN, and deliberately so** — see below |

Exit codes were captured with `echo "exit=$?"` immediately after each command; the two sweeps ran to a
file and their raw output is retained at
`…/scratchpad/gate-pytest-default-024.txt` and `…/scratchpad/gate-pytest-sharded-024.txt` (scratch
outside the repo). No `--cov`, `--cov-report`, or `--cov-config` was used anywhere in this pass;
`--no-cov` is required because `pytest.ini`'s `addopts` auto-applies `--cov`, and it is the only
coverage-shaped flag that appears. No line-coverage figure was inspected or asserted.

Command 5 also emits the repo's standing `COM812` formatter-conflict configuration warning, which is
present on every run in this repo and is not a failure (`AGENTS.md` rule 17 makes
`scripts/check_trailing_commas.py`, not ruff, the owner of single-line explosion).

### 1 and 2 — both full sweeps, and why the sharded one is load-bearing here

Both run to completion across all three test trees, both exit 0, **zero failures and zero collection
errors in either**. The counts reproduce the earlier record exactly — `6179 + 40` default and
`6191 + 37` sharded — which is the expected result for a diff that changes no executable line; the
wall-clock differs and the row counts do not.

`FAKESHOP_SHARDED=1` is **the only mode configuring more than one database alias**, and this card's
subject is a multi-database teardown patch: Django wraps disallowed connection methods precisely on
the aliases a test case does not permit. `spec-024` `## Definition of done` item 9 names the sharded
invocation explicitly. So the sharded sweep is not a duplicate of the default one for this card, and
running only the default sweep would leave the card's own subject unexercised at the gate.

**Nothing to escalate on this account.** No test failed, so no question arose of a failure sitting in
a file outside this cycle's diff — the case `docs/builder/BUILD.md` `## Claims are proven
mechanically, never accepted on prose` makes not worker-verifiable from a dirty tree, to be recorded
and escalated rather than fixed.

### 5, 6, 7 — lint / format / diff, all read-only

Never `--fix`, never a revert. All three came back clean over the **whole tree**, so no attribution
question arose: there is no hit to attribute to a concurrent session and none to this cycle. `git
diff --check` covering the whole tree is also what confirms this pass's own Markdown edits introduced
no trailing whitespace or conflict marker.

Two doc-side checks re-run because this pass edited a `.md` artifact:
`uv run python scripts/check_trailing_commas.py --check docs/builder/bld-slice-4-024-docstring_fragment.md`
-> silent, exit 0; the same checker over `docs/builder/bld-final-024.md` after this append -> silent,
exit 0.

### 8 — Floor verification: not re-run, and the reason stated rather than the omission left silent

**Floor verification is not re-run by this pass, and that is a decision, not a gap.** Three grounds,
each independently sufficient:

- **It is owned and recorded elsewhere.** The build plan's `## Declarations` assigns the cycle's
  single floor run to **Slice 1b**, which performed it; `docs/builder/BUILD.md` `## Final test-run
  gate` makes this gate the backstop that confirms it happened, not a second owner. The record —
  scratch venv `/tmp/dsf-floor-024` outside the repo, Python 3.10.19 / Django 5.2.16 /
  strawberry-graphql 0.316.0 as read with `uv pip list --python …`, focused scope
  `tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py` -> 36 passed, exit 0 —
  is in `docs/builder/bld-slice-1b-024-divergence_and_floor.md` `### Floor verification` and is
  restated in this file's `### 8 — Floor verification, cited and confirmed` above.
- **It was already double-executed.** That slice's Worker 3 review independently re-executed the run
  in full, venv resolution and discriminator probe included.
- **Slice 4's diff cannot change what a floor run measures.** The floor run exists to execute the
  class-attribute audited body — the shape covering `5.2.16`-`6.0.x` — which no other run in this
  cycle reaches. Slice 4 deletes one line of prose from a module docstring. It adds, removes, and
  alters no executable line, no boundary, and no Django / Strawberry / channels seam, so no audited
  upstream body's validation can differ before and after it. Re-running would re-measure Slice 1b's
  result, not Slice 4's.

The plan's floor-verification scope is therefore still discharged in full: one slice, one focused
scope, one owning pass, all satisfied.

### Slice 4 verification, independent of the artifact's own record

Re-derived at this pass rather than accepted from `docs/builder/bld-slice-4-024-docstring_fragment.md`.
HEAD read read-only into a scratch path outside the repo
(`git show HEAD:django_strawberry_framework/_strawberry_patches.py`); no `git stash`, `git checkout`,
`git restore`, or `git worktree` at any point.

- **The defect was real and pre-existing at `ddf8bbaf`.** Occurrences, not matching lines:
  `grep -o 'independent upstream \*bugs\* that do not retire together:' <HEAD copy> | wc -l` -> **2**;
  the same instrument on the working tree -> **1**.
- **The correct occurrence was deleted — established by reading, since a count of 1 is what either
  deletion produces.** HEAD's section reads heading / underline / blank / a subordinate clause with no
  subject / the complete two-line sentence / blank / the numbered list. The working tree reads
  heading / underline / blank / `Read the retirement question per concern, because this module carries
  three` + `independent upstream *bugs* that do not retire together:` / blank / the numbered list. The
  survivor is the second line of the complete sentence, and its "three" agrees with the three-item
  list it introduces.
- **Exactly two hunks, no reflow, no other file.** `git diff HEAD -- <path> | grep -c '^@@'` -> **2**;
  `git diff HEAD --numstat -- <path>` -> `1  2`, i.e. hunk 1's citation repair (1 insertion,
  1 deletion) plus hunk 2's single deletion with **zero** `+` lines. `ast.get_docstring` delta
  HEAD -> working tree = **-57**, exactly the deleted line's 56 characters plus its newline, which
  leaves no room for a hidden reflow inside either hunk.
- **`docs/TREE.md` owes no regenerate.** It renders module summary lines, i.e. the docstring's first
  line, and that line is byte-identical before and after
  (`Defensive patches for upstream Strawberry bugs, applied at app load.`). `docs/TREE.md` is clean in
  `git status`, and `_strawberry_patches.py` is in any case not among the six TREE-feeding surface
  modules `spec-024` enumerates.

### Spec and rationale: nothing owed, re-derived not accepted

The custodian call, made at this pass rather than inherited from the slice's review:

- Neither the deleted fragment's phrasing nor the section it sits in appears in `spec-024` or its
  rationale companion. Instrument: `grep -n -i 'Three lifecycles|independent upstream|retire
  together|docstring'` over both files — the only hits are unrelated uses of the word "docstring".
- `_strawberry_patches.py` is named nowhere in the spec, and twice in the rationale: once in the
  change record (`c7cb5f5c` turning `ready()` into three appliers) and once under **Decision 5**
  `### Changes this Decision underwent`, recording this cycle's rename-rot slice as the repair of
  "the one casualty of `eb2a1764`'s rename". That entry is scoped to the **citation**. The orphaned
  fragment is a copy-paste duplicate, not rename rot and not a casualty of any rename, so the entry is
  neither falsified nor made incomplete by this deletion.
- The fragment carried **no claim** — it was a byte-for-byte duplicate of a clause already stated in
  the sentence below it — so no Decision's contract, rejected alternative, change record, or retired
  claim changes. `docs/builder/BUILD.md` `## Spec rationale extraction` keys every rationale entry to
  a spec decision by heading and anchor; there is no decision this deletion belongs to, and an entry
  naming no decision is worthless by that rule.
- The spec's `## Implementation plan`, `## Doc updates`, and `## Definition of done` enumerate this
  card's own deliverables. `_strawberry_patches.py` was never one; it entered this cycle only through
  the rename-sweep obligation. None of the three is falsified.
- Per-spawn duty (`worker-1.md` `## Spec status-line re-verification`): the spec's lines 1-5 — title,
  target release `0.0.7`, `Status: shipped (0.0.7, 2026-05-27); archived`, owner, predecessors — were
  re-read and still describe the build's state. No status-line edit was owed.

**Conclusion: no spec edit and no rationale edit were made, because none is owed.**

### Artifact-side work performed by this pass

- `docs/builder/bld-slice-4-024-docstring_fragment.md` `### The defect` — one clause added to the
  *Population:* sentence, discharging the single open Low from that artifact's Worker 3 re-review: the
  build plan's `## Slice 4 dispatch (post-gate, maintainer-directed)` is now **explicitly** excluded
  from the population as this slice's own authorisation, with the reason stated (it authorises rather
  than records; it constitutes the "written before this slice" boundary). **No number changed** — the
  figure of 8 passages was already correct and the edit adds no count.
- `docs/builder/bld-slice-4-024-docstring_fragment.md` `Status:` set to `final-accepted`.
- This appended section. No other artifact's `Status:` was touched, and no build-plan checkbox was
  ticked — the plan is Worker 0's.

### Deferred work catalog — item 6 closed, the rest unchanged

The `## Deferred work catalog` above is the cycle's catalog and is **not edited**. One change of state
is recorded here instead:

- **Item 6 — the pre-existing duplicated docstring fragment in a writable file — is CLOSED.** It is
  the one catalog entry whose `*Deferral licensed by:*` clause read **nothing**, because it sat inside
  this cycle's `.py` scope. Slice 4 is the owner it was routed to, the fix landed, and it is verified
  above from an independent read-only HEAD reference. Recorded by content rather than by
  section-plus-number, per the standing correction in that slice's artifact: the two prior recordings
  of the defect are Worker 2's `bld-slice-3-024-rename_rot_sweep.md` #"One defect found in the writable
  file that is deliberately NOT repaired here" and Worker 3's `### Notes for Worker 1` item 4 in the
  same file. Item 6's own text conflates those two, which is why the closure does not cite it by
  number.
- **The other six items are unchanged**, including the two maintainer decisions escalated under
  `## Escalated to the maintainer`. Nothing in Slice 4 touches any of them.

### Gate outcome

**PASS.** All seven executed commands exit 0; floor verification is confirmed as owned, recorded, and
double-executed by Slice 1b, and correctly not re-run for a diff with no executable line. Nothing
failed anywhere, so nothing was escalated on a failure ground and nothing outside this cycle's diff
needed grading. `docs/builder/bld-slice-4-024-docstring_fragment.md` is `final-accepted`.

This file's own `Status:` line is unchanged at `final-accepted` — the earlier record closed the cycle
and this append re-confirms it over the larger diff rather than re-opening it.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
