# Build: Review round 2 — documentation completion

Spec reference: `docs/SPECS/spec-020-list_field-0_0_7.md` (`## Slice checklist` -> Slice 5 `README.md` sub-bullet; `## Definition of done` item 16)
Rationale companion: `docs/SPECS/appx/spec-020-list_field-0_0_7-rationale.md`
Build plan: `docs/builder/build-020-list_field-0_0_7.md` (`### R2 findings — documentation completion`)
Predecessor round: `docs/builder/bld-review-1-spec020_reconciliation.md` (`final-accepted`)
Status: final-accepted

Round input: Worker 0's own verified spec-vs-code pass, not a maintainer review document (`docs/builder/BUILD.md` `## Review rounds`). Two findings, F13 and F14. Unlike R1, this round has a genuine builder role and follows the standard routing: Worker 1 plans, Worker 2 builds, Worker 3 reviews, a fresh Worker 1 finally verifies.

## Round declarations

Restated per-round so Worker 2 need not infer whether the build plan's cycle-wide silence was deliberate.

| Declaration | This round |
|---|---|
| **Hot-path** | **none.** Nothing in this round runs per request, per resolver, per row, per connection, or per outbound message. Both surfaces are documentation: one `README.md` prose bullet and one `GlossaryTerm.body` field edited through the ORM plus a build-time regenerate. No `### Hot-path budget` number is owed; Worker 2 writes `Not applicable; plan declares no hot path.` |
| **Floor verification** | **none.** No Django / Strawberry / channels integration seam is touched — no request/response handling, no view or ASGI plumbing, no body parsing, no session/auth surface, no queryset or expression compilation, no schema or type construction. `docs/builder/BUILD.md` `## Floor verification` -> `### When it is required` names "docs, KANBAN / glossary regeneration" explicitly as the `none` case. Worker 2 writes `Not applicable; plan declares floor-verification scope none.` |
| **Failability proofs** | **not required, and here is the reason.** `docs/builder/BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a **new** boundary, guard, gate, or rejection path a pass *introduces*. This round introduces none: it *describes* boundaries that shipped at `0.0.7` / `0.0.14` and are already pinned by the nine tests enumerated under F14.1 below. Doc edits are named in that same section as needing none. Worker 2 writes `None; this pass introduced no new boundary.` |
| **Boundary count (split trigger)** | **zero.** `docs/builder/worker-1.md` `### Boundary count is a split trigger` obliges an answer in writing even when the diff is small: this cohort adds no guard, cap, rejection path, or validation branch, so the count is 0 and no split question arises. One unit, one artifact. |
| **`scripts/review_inspect.py`** | **not required.** `docs/builder/BUILD.md` `### When to run the helper during build` fires on adding a `.py` file, touching `optimizer/` or `types/`, or adding 30+/50+ lines of logic. This round adds and modifies **no** `.py` file at all — the DB edit is performed *through* `manage.py shell`, which writes data, not source. Worker 1's own planning trigger (logic added to a 150+-line `.py` file) likewise does not fire. Recorded as an explicit skip with its reason, per that section's last paragraph. |
| **Ownership partition** | R2 owns, exhaustively: `README.md`; `examples/fakeshop/db.sqlite3`; `docs/GLOSSARY.md` (regenerated, never hand-edited); this artifact. The build plan's `## Ownership partition` is the authority and no file appears in both cohorts. `docs/SPECS/spec-020-list_field-0_0_7.md` and its rationale companion are **R1's, custodian-only** — if this round turns out to need a spec amendment, it goes under `### Notes for Worker 1 (spec reconciliation)` in this artifact and a Worker 1 pass executes it. Worker 2 never edits either. |

## Plan (Worker 1)

### What this round must not do

Three closed questions. Re-opening any of them is a Worker 3 finding, not diligence.

1. **The glossary's `DjangoListField` -> Row bound paragraph is NOT to be trimmed.** R1 weighed whether the spec or the generated glossary should own the row-bound composition contract and decided **(a)**: the spec keeps the field-facing surface (`max_rows=` / `trusted_max_rows=` as constructor arguments), the generated glossary keeps the policy contract (how `max_list_rows` and `max_rows=` compose, that there is no unbounded spelling). Its reason: making an archived `0.0.7` spec the authority for a `0.0.14` contract it only inherits is the shape this residual series exists to unwind. A later Worker 3 independently verified the paragraph genuinely carries the deferred composition clause. Do not plan a trim, do not perform one, do not re-litigate the choice. Recorded in R1's artifact under `### Judgement calls decided` and `### Notes for Worker 1 (spec reconciliation)`.
2. **No spec amendment is owed for F13.** R1 already decided the disposition — satisfy the obligation, restate only the shape — and amended the spec accordingly. `docs/SPECS/spec-020-list_field-0_0_7.md` `## Slice checklist` Slice 5 now reads: "`README.md` — the `## Status` section's \"Earlier alpha surfaces\" list (which runs newest-first and is the file's own idiom for a shipped cut) carries a `0.0.7` entry leading with `DjangoListField`, in that list's existing one-line-per-version voice; `KANBAN.md #\"## Done\"` holds the authoritative content for the cut." That is a satisfiable target. `## Definition of done` item 16 still names `README.md`. Nothing further is owed on the spec side.
3. **Do not re-open the build plan's `### Verified NOT a finding` list, and do not plan edits to those files.** `docs/TREE.md`, `GOAL.md` #"`DjangoListField` replaces graphene-django's symbol of the same name", `docs/README.md` #"`DjangoListField` — non-Relay `list[T]` factory for root Query fields", `TODAY.md`'s capability list, and `CHANGELOG.md`'s `0.0.7` `### Added` entry were each checked and are correct. Likewise **do not** plan fixes for the two clusters the build plan escalated to the maintainer — `CHANGELOG.md`'s pre-renumber card labels across the whole `0.0.7` section, and `KANBAN.md`'s `DONE-020-0.0.7` card listing `apps.py` under Package files. Both are deferred-work-catalog material for the final gate; the no-partial-fix rule is why (a reference wrong across several surfaces must not be corrected on one of them).

### The mechanism: `docs/GLOSSARY.md` is GENERATED, not source

Worker 2 will not read `worker-0.md`, so the whole procedure is spelled out here. Canonical statement: `docs/builder/BUILD.md` `### Generated docs are DB-backed: edit the DB, then regenerate`.

`docs/GLOSSARY.md` renders from the glossary tables in `examples/fakeshop/db.sqlite3` via `scripts/build_glossary_md.py`. **A hand-edit of `docs/GLOSSARY.md` is silently reverted by the next render.** The entry body is a single DB column: `scripts/build_glossary_md.py::render_term` emits `## <title>`, then `**Status:** <statusText>.`, then `body` verbatim — so everything after the Status line, the closing `**See also:**` line included, is `GlossaryTerm.body`. One column edit covers every change F14 asks for; no `GlossaryTermLink` row and no second model are involved.

**The edit.**

1. Open the shell: `uv run python examples/fakeshop/manage.py shell`.
2. Fetch the row by anchor and write through the ORM:

```python
from apps.glossary.models import GlossaryTerm

term = GlossaryTerm.objects.get(anchor="djangolistfield")
term.body = "<the new body>"
term.save()
```

**Use `.save()`, never a raw SQL `UPDATE`.** Two concrete reasons, both verified against source rather than assumed: `apps.glossary.models.TimeStampedModel` declares `updated_date = models.DateTimeField(auto_now=True, editable=False)`, which only Django's save path maintains; and BUILD.md's standing rule makes the ORM the supported route for every DB-backed doc edit in this repo. (A caution circulating in this cycle's prompts — that raw SQL would skip a `post_save` maintaining a `UUIDModel` side-row the renderer needs — does **not** apply to this row, and the plan does not rest on it. See `### Prompt and build-plan citations verified` below.)

**The regenerate**, from the repository root: `uv run python scripts/build_glossary_md.py`. Do **not** hand-edit `docs/GLOSSARY.md` at any point.

**Do NOT run `scripts/build_kanban_md.py` or `scripts/build_kanban_html.py`.** `scripts/build_glossary_md.py` writes only `docs/GLOSSARY.md`. `KANBAN.md` and `KANBAN.html` are outside R2's ownership and there is no kanban change to render; their `--check` invocations below are read-only verification, not a regenerate.

**The baseline, already established so Worker 2 need not derive it.** `uv run python scripts/build_glossary_md.py --check` exits **0** right now — verified in this planning pass, printing "`docs/GLOSSARY.md` is up to date." The DB renders the committed `docs/GLOSSARY.md` byte-identically. Consequence: after the edit, `git diff HEAD -- docs/GLOSSARY.md` must show **only** the intended `DjangoListField` change and nothing else. Anything more means either a concurrent writer or an unintended DB edit — report it, never revert it.

**Concurrent-writer discipline.** `examples/fakeshop/db.sqlite3` is git-tracked and concurrent-writable; the maintainer runs parallel sessions against this same file. All four concurrent-writable tracked files (`examples/fakeshop/db.sqlite3`, `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`) were **clean at pre-flight** and were still clean when this plan was written (`git status --short` over the four returned nothing). A same-size binary diff on the DB is **not** proof of a no-op — git does not line-diff binaries. If unexpected churn appears, compare the semantic content (`iterdump()`), never blind-revert, and hand a mixed diff to the maintainer to reconcile (`docs/builder/BUILD.md` `### Tracked binary / generated files`). **Never `git stash`, `git checkout`, `git restore`, or `git worktree`** — those can destroy a concurrent session's uncommitted work. Read-only HEAD reference: `git show HEAD:<path>` into a scratch path outside the repo, then `diff`. Use `git diff HEAD -- <path>`, never `git diff -- <path>`, since another session's `add -A` makes the latter read clean.

**Two-render byte-stability, not `git diff`.** `git diff` shows the cumulative diff against HEAD and says nothing about whether a second render is stable. Prove stability by rendering twice and byte-comparing, using `--md` to keep the second render out of the tree:

```shell
uv run python scripts/build_glossary_md.py                                  # writes docs/GLOSSARY.md
uv run python scripts/build_glossary_md.py --md /tmp/dsf-glossary-r2.md     # scratch path OUTSIDE the repo
cmp docs/GLOSSARY.md /tmp/dsf-glossary-r2.md                                # must exit 0
uv run python scripts/build_glossary_md.py --check                          # must exit 0
```

### DRY analysis

**Helper inventory checked — for the whole package, and it is the right answer that it is empty.** `docs/builder/worker-1.md` `### Package-wide helper inventory before helper planning` requires the refresh before proposing any helper, shared constant, validation branch, coercion utility, or test helper. This round proposes **none of those**: it adds no `.py` line anywhere, so there is no call site a helper could serve and no literal a constant could name. The inventory was therefore not regenerated, and the reason is structural rather than a skip — searching it for `parse` / `validate` / `reject` / `bound` shapes would answer a question this round does not ask. The relevant source reading was done instead and is cited throughout this plan (`django_strawberry_framework/list_field.py`, `django_strawberry_framework/utils/querysets.py`, `scripts/build_glossary_md.py`, `examples/fakeshop/apps/glossary/models.py`).

**Existing patterns reused.**

- **README bullet:** the `## Status` -> "Earlier alpha surfaces" list is its own pattern — one line per version, newest-first, `- `0.0.N` — <surfaces>.`, naming *package surfaces* and never card IDs. The seven bullets from `0.0.13` down to `0.0.8` are the shape to match. Reuse the list's voice; introduce no new sub-structure, no nested bullets, no second paragraph.
- **Glossary body:** the entry's existing shape is one dense opening paragraph (mechanism, nullability, default resolver, consumer `resolver=`, async detection, optimizer cooperation, metadata pass-through), then a bolded-lead paragraph for a later-card contract (`**Row bound (`0.0.14`, spec-047).**`), then `**See also:**`. A new bolded-lead paragraph is the established way to add a contract without re-flowing the opening paragraph; the precision fix belongs inline in the opening paragraph where the loose wording already sits.
- **In-page anchors:** the entry already links `[`ConfigurationError`](#configurationerror)`, `[`DjangoConnectionField`](#djangoconnectionfield)`, `[`get_queryset`](#get_queryset-visibility-hook)`, `[execution resource policy](#execution-resource-policy)`. `#syncmisuseerror` is an existing anchor (`docs/GLOSSARY.md` `## `SyncMisuseError``, already the target of 8 in-file links) — link it, do not describe it.

**New shared shapes justified: none.** Single-cohort partition, so `docs/builder/worker-1.md`'s shared-shape assignment rule has nothing to assign.

**Duplication risk avoided — the four near-copies a naive implementation would create, and how the plan forecloses each.**

1. **The README bullet restating the "Newest shipped" block above it.** That block already covers `0.0.14` and cards `046`-`049`. The new bullet is scoped to `0.0.7` surfaces only and touches nothing above line 72's "Earlier alpha surfaces, each detailed in ..." lead-in. Forbidden: any mention of `max_rows` / row bounds / the resource policy, which are `0.0.14` and belong to the surfaces already described.
2. **The README bullet restating `docs/README.md`'s `DjangoListField` bullet.** That bullet already carries the full shipped contract — default resolver, sync + async `get_queryset`, the `0.0.14` row bound, and a link to the glossary entry. It was verified correct and is **not** R2's file. The README list's own lead-in sentence says every entry is "detailed in `CHANGELOG.md` and `docs/GLOSSARY.md`", so the bullet's job is one line of orientation, not a contract restatement. Forbidden: a second copy of the row bound, of the async-detection rule, or of the optimizer-cooperation clause.
3. **The glossary text restating the spec.** The reconciled spec now states both F14 contracts at length (the three consumer-resolver arms with the `SyncMisuseError` rejection; the ordering asymmetry with `DjangoConnectionField`'s pk tiebreaker) and, for the arm, enumerates the six pinning tests. The glossary is the consumer-facing standing catalog, not the design record: it states the **contract a consumer must know**, in the entry's compressed voice, and it does **not** copy the spec's paragraph, its code sketch, or its symbol-level narration of `_require_async_iterable_context` / `_resolve_async_iterable` / `is_async_generator_callable`. The audiences differ (archived design contract versus live capability catalog) and the archived spec is not a doc a consumer reads, so both carrying the contract is correct, not duplication — but only if each says it in its own register.
4. **The glossary text citing the nine pinning tests.** It must not. Measured: `docs/GLOSSARY.md` cites a `tests/` path 7 times in 2149 lines, and every one is where the test *placement itself* is the documented point (the live-first mandate, the eviction-simulated-absence discipline, the genuinely-unreachable-live router case). A consumer-facing contract sentence citing nine test names would be a fifth copy of a list the spec and the build plan already carry. The test names are this round's **evidence** — cited in this artifact, verified below — not catalog content.

**The existence question, asked explicitly** (`docs/builder/BUILD.md` DRY-FIRST: whether the content should be written at all). Asked and answered for each of the three F14 amendments and the README bullet:

- The **async-iterable arm** must be written somewhere in the consumer-facing docs and currently is nowhere: `grep -o 'AsyncIterable\|async generator\|async-generator' docs/GLOSSARY.md | wc -l` returns **0** for the whole 2149-line file, re-measured in this pass (counting occurrences, not matching lines). A consumer whose resolver is an async generator has no documented contract today and no cross-reference to follow. Write it, once, here.
- The **ordering contract** is a consumer-visible guarantee-that-is-not — response order is database-dependent — and its absence is the kind of gap a consumer discovers in production. It exists in `django_strawberry_framework/list_field.py::DjangoListField`'s docstring and in the spec; a docstring is not a consumer doc and an archived spec is not either. Write it, once, here.
- The **`ConfigurationError` -> `SyncMisuseError` precision fix** adds no new content: it *replaces* a looser word with a linked precise one. It is the smallest of the four edits and the one that removes a divergence rather than adding text, and F14 is reopening this very entry — which is exactly why R1 folded it in here rather than leaving two precisions in the tree.
- The **README bullet** is the one place where "should this be written at all?" had a real competing answer — retract the requirement instead. R1 considered and rejected that: `README.md`'s idiom is now the very bullet list the original prescription avoided, so the prescription's intent survives its letter; the list's stop at `0.0.8` is unexplained, so retracting would invent a policy to excuse a gap; and DoD 16 still names `README.md`. Settled; see `### What this round must not do` item 2.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing — this tree carries a concurrent maintainer session's work and files shift.

**F13 — the `README.md` `0.0.7` bullet.**

1. Open `README.md` `#"Earlier alpha surfaces, each detailed in"` (line 72 at write time). The list below it runs `0.0.13` (line 74) down to `0.0.8` (line 79) and stops; line 81 is the "For the current capability snapshot" closing paragraph.
2. Insert **one** new bullet immediately after the `0.0.8` bullet and before that closing paragraph, so the list stays strictly newest-first and ends at `0.0.7`.
3. Shape it exactly like its siblings: a single line, `- `0.0.7` — ...`, leading with `DjangoListField` per the spec's Slice 5 sub-bullet, in the list's existing one-line-per-version voice. No nested bullets, no bold sub-labels beyond what the siblings use, no second sentence-per-card enumeration.
4. Source the content from `KANBAN.md #"## Snapshot"` — the authoritative sentence for the cut, at line 62 at write time, reproduced here so Worker 2 need not hunt it:

   > `0.0.7` shipped 2026-05-27 with seven cards: `DONE-020-0.0.7` (`DjangoListField`), `DONE-021-0.0.7` (`apps.py` and Django app config), `DONE-022-0.0.7` (schema-export management command), `DONE-023-0.0.7` (multi-database cooperation contract), `DONE-024-0.0.7` (Django Trac #37064 hardening + `safe_wrap_connection_method` consumer helper), `DONE-025-0.0.7` (warning-free scalar registration via `StrawberryConfig.scalar_map`), and `DONE-026-0.0.7` (scalar conversion end-to-end coverage in the fakeshop example with the new `apps.scalars` app plus a `BigIntegerField` on `apps.library.Patron`).

   Translate cards to **surfaces**: the sibling bullets name what the package gained (`0.0.9` — "the Relay release: `DjangoConnectionField` ...", `0.0.8` — "the filtering ... and ordering ... subsystems"), and none of them prints a card ID. So the bullet names `DjangoListField` first, then the other `0.0.7` package surfaces, and does not print `DONE-0NN-0.0.7` identifiers.
5. **Do not add a link definition.** No sibling bullet in this list carries a per-surface link, and `README.md`'s `<!-- LINK DEFINITIONS -->` block has no `[glossary-djangolistfield]` def; adding one would be the only new link in a list that deliberately routes the reader to `CHANGELOG.md` / `docs/GLOSSARY.md` through its lead-in. If Worker 2 judges a link genuinely necessary, `START.md`'s convention applies in full (reference-style, def under `<!-- docs/ -->`, alphabetical) and the judgement is recorded in `### Implementation notes` — but the default is none.
6. Verify: `grep -n DjangoListField README.md` now returns the new bullet (it returned nothing before this round), and `uv run python scripts/check_trailing_commas.py --check README.md` exits 0.

**F14 — the `DjangoListField` glossary entry, via the DB.**

7. Read the current body first. `docs/GLOSSARY.md` `## `DjangoListField`` (line 652 at write time) is the rendered form; the source is `GlossaryTerm.objects.get(anchor="djangolistfield").body`. Render-time equality means the rendered text after the `**Status:**` line *is* the body, so the rendered entry is a faithful preview of what to edit.
8. **F14.3, the precision fix, inline in the opening paragraph.** The clause `#"the sync path rejects an async `get_queryset` with `ConfigurationError`, mirroring the Relay defaults"` becomes a `SyncMisuseError` statement linked to the existing `#syncmisuseerror` anchor. The current wording is not false — `django_strawberry_framework/utils/querysets.py::SyncMisuseError` is `class SyncMisuseError(ConfigurationError, RuntimeError)` — merely looser than the reconciled spec, which says `SyncMisuseError` at every site including `## Goals` item 3. Keep the "mirroring the Relay defaults" sense: the same rejection every read surface receives.
9. **F14.1, the third consumer-resolver arm, as a new bolded-lead paragraph.** The contract a consumer needs, and nothing more: a consumer `resolver=` may be an **async generator function** or may return an **async-only iterable** from a plain sync callable; both are supported and both are row-bounded like every other arm; and an async-only iterable met from **synchronous** GraphQL execution is rejected with a linked `SyncMisuseError` rather than silently yielding nothing — use `await schema.execute(...)` for such a resolver. Verified at source in this pass: `django_strawberry_framework/list_field.py::_require_async_iterable_context` raises unless `in_async_context()`; `::_resolve_async_iterable` bounds the async path; the `is_async_generator_callable(user_resolver)` branch and the sync wrapper's `isinstance(source, AsyncIterable) and not isinstance(source, Iterable)` branch are both present. Place it after the opening paragraph and before or after the Row-bound paragraph at Worker 2's discretion (see `### Implementation discretion items`). **Do not** enumerate the pinning tests, and **do not** narrate the three private helper names — a consumer cannot call them.
10. **F14.2, the ordering contract, as a new bolded-lead paragraph.** The contract, from `django_strawberry_framework/list_field.py::DjangoListField` #"Ordering contract: a ``DjangoListField`` does NOT guarantee row order unless": a `DjangoListField` does **not** guarantee row order unless the query supplies an `orderBy` argument or the model declares `Meta.ordering`; the default resolver appends no tiebreaker, so response array order is database-dependent. State the asymmetry with `[`DjangoConnectionField`](#djangoconnectionfield)`, which appends a pk tiebreaker because its positional cursors require a total order, and state that the asymmetry is deliberate — a flat list has no cursors an unstable order could invalidate. This is the single clause a consumer most needs and cannot infer.
11. **F14.4, the negative obligation: leave the Row-bound paragraph byte-identical.** `**Row bound (`0.0.14`, spec-047).**` is R1's decision (a) authority for how `max_list_rows` and `max_rows=` compose. Do not trim it, do not re-flow it, do not fold the new paragraphs into it.
12. **Links: in-page anchors only.** START.md keeps in-page anchors inline and reference-style for cross-file links — and a cross-file reference-style link from a glossary body would need a def in a *different* DB row (the `link_definitions` glossary document that renders the file's bottom block), which is a second edit this round does not need. Every target the new text wants is already an in-page anchor: `#syncmisuseerror`, `#djangoconnectionfield`, `#get_queryset-visibility-hook`, `#configurationerror`. Use `[text](#anchor)`, matching the entry's existing style.
13. Save through the ORM and regenerate, exactly as `### The mechanism` specifies. Then run the verification block in `### Test additions / updates`.

### Test additions / updates

**No new test is owed, and the reasoning is not "it's only docs".** `docs/GLOSSARY.md` is DB-rendered and `README.md` is prose, so neither carries an assertable branch — but this repo *does* gate documentation mechanically, in CI (`.github/workflows/django.yml`) and in the pre-commit `source-layout` hook. Those gates are the tests this round owes, and Worker 2 owns every one of them. None takes a `--cov*` flag; `--no-cov` is the only permitted coverage-shaped flag.

| Check | Expected | Why it is in scope |
|---|---|---|
| `uv run python scripts/build_glossary_md.py --check` | exit 0 | The CI gate for DB-vs-rendered-doc consistency. Baseline was 0; a DB edit without a regenerate makes it 1. |
| `uv run python scripts/build_glossary_md.py --md /tmp/dsf-glossary-r2.md` then `cmp docs/GLOSSARY.md /tmp/dsf-glossary-r2.md` | exit 0 | Two-consecutive-regenerate byte-stability. `git diff` cannot show this. Scratch path outside the repo. |
| `uv run python scripts/check_trailing_commas.py --check README.md docs/GLOSSARY.md docs/builder/bld-review-2-docs_completion.md` | exit 0 | The `source-layout` hook's `--check` face: markdown link-def scaffold on every `.md` this round writes. Note this checker **cannot** see a reference-style link whose def is missing, only a missing scaffold — which is a second reason step 12 forbids cross-file links here. |
| `uv run python scripts/build_kanban_md.py --check` and `uv run python scripts/build_kanban_html.py --check` | exit 0 | Read-only proof the DB write disturbed no kanban render. Both are CI gates. **Never run either in write mode** — `KANBAN.md` / `KANBAN.html` are outside R2's ownership. |
| `uv run python scripts/build_tree_md.py --check` | exit 0 | Same, for the third DB-backed generated doc. Read-only. |
| `uv run pytest examples/fakeshop/apps/glossary --no-cov` | pass | The glossary app owns the coverage for the model whose row this round edits (`test_models.py`, `test_factories.py`, `test_import_spec_terms.py`). Cheap, and the only focused suite whose subject the round touches. Tests run against a test database, not the tracked `db.sqlite3`, so this is a regression check on the app rather than on the data. |
| `git diff HEAD -- docs/GLOSSARY.md` | **only** the `DjangoListField` entry's change | Anything more means a concurrent writer or an unintended DB edit — report, never revert. |
| `git status --short` | only the four files R2 owns | `docs/builder/BUILD.md` `### Validation run` discipline: unexpected churn is a stop-and-report, never a `git checkout`. |
| `examples/fakeshop/db.sqlite3` churn | classified | Same-size binary diff is not proof of a no-op. Compare `iterdump()` semantically and record that the only semantic delta is `glossary_glossaryterm`'s `djangolistfield` row (`body`, `updated_date`). |

The **full** sweep (`uv run pytest --no-cov`), `manage.py check`, `makemigrations --check --dry-run`, the read-only ruff trio and `git diff --check` belong to the final gate, not to this pass. The pre-flight **baseline gate exception** stands and Worker 2 plans around it rather than at it: repo-wide `uv run python scripts/check_trailing_commas.py --check` exits **1** on `.claude/projects/.../memory/one-spec-owns-each-feature.md`, an untracked, gitignored agent-memory artifact — not repository content, unrelated to this cycle, **not to be fixed**. Scoped to this round's files, as in the table above, the same check exits 0.

No temp tests are appropriate here; there is no assertion for Worker 3 to demonstrate non-distinguishing.

### Implementation discretion items

Assessed and decided to be Worker 2's — each is a choice between shapes this plan judges equally valid, not an architectural escape hatch.

- **Order of the two new glossary paragraphs relative to the Row-bound paragraph.** Both readings defend themselves (arm-before-bound follows the opening paragraph's resolver narrative; bound-first keeps the two `0.0.14`-era paragraphs adjacent). Either is fine; the Row-bound paragraph's own bytes stay untouched whichever is chosen.
- **Whether the two new contracts are two bolded-lead paragraphs or one.** They are independent contracts, so two is the natural shape, but one paragraph covering both is acceptable if it reads better in the entry's dense voice.
- **The exact wording, including whether the ordering paragraph opens with a bold lead like `**Ordering.**` or a plain sentence.** The entry uses both registers already.
- **Whether the `0.0.7` README bullet names all `0.0.7` package surfaces or only the consumer-facing ones.** `DONE-026-0.0.7` is example-project coverage (the `apps.scalars` fakeshop app plus a `BigIntegerField` on `apps.library.Patron`), which is not a package surface the way the other six are, and the sibling bullets describe package surfaces. Omitting it, or folding it into the scalar-registration clause, are both defensible; naming it as a package capability is not.

### Dispatched findings checklist

One box per sub-check Worker 2 must land. Boxes stay `- [ ]` at planning; Worker 2 ticks `- [x]` only a box whose work actually landed in its diff this pass and states any deferral in the build report rather than ticking; Worker 3 walks the list at review; a later Worker 1 audits every tick at final verification (`docs/builder/BUILD.md` `### Dispatched findings checklist`).

- [x] **F13.a — "`README.md` carries no `DjangoListField` anywhere, and the spec's Slice 5 required it." (`grep -n DjangoListField README.md` returns nothing.)** Add one `0.0.7` bullet at the end of `README.md` `#"Earlier alpha surfaces, each detailed in"` — after the `0.0.8` bullet, before the "For the current capability snapshot" paragraph — leading with `DjangoListField`, in that list's existing one-line-per-version voice. Target authorized by `docs/SPECS/spec-020-list_field-0_0_7.md` `## Slice checklist` Slice 5 `#"the `## Status` section's \"Earlier alpha surfaces\" list"` and `## Definition of done` item 16.
- [x] **F13.b — content sourced from the authoritative cut record, translated to surfaces.** Draw the `0.0.7` content from `KANBAN.md #"## Snapshot"` #"`0.0.7` shipped 2026-05-27 with seven cards" (quoted verbatim in `### Implementation steps` step 4), and name package **surfaces** rather than `DONE-0NN-0.0.7` card IDs, matching every sibling bullet.
- [x] **F13.c — no duplication and no new link.** The bullet restates neither the "Newest shipped" block above it nor `docs/README.md` #"`DjangoListField` — non-Relay `list[T]` factory for root Query fields", and adds no `README.md` link definition (or records the judgement in `### Implementation notes` if one proves necessary). `uv run python scripts/check_trailing_commas.py --check README.md` exits 0.
- [x] **F14.a — "the async-iterable / async-generator consumer-resolver arm and its rejection path" is a genuine gap, not a cross-reference.** Add it to the `djangolistfield` entry: an async generator resolver and a sync resolver returning an async-only iterable are both supported and both row-bounded, and an async-only iterable met from synchronous GraphQL execution is rejected with `SyncMisuseError`. Shipped surface: `django_strawberry_framework/list_field.py::_require_async_iterable_context`, `::_resolve_async_iterable`, the `is_async_generator_callable` branch, and the sync wrapper's `isinstance(source, AsyncIterable) and not isinstance(source, Iterable)` branch, raising `django_strawberry_framework/utils/querysets.py::SyncMisuseError`. Measured gap: `grep -o 'AsyncIterable\|async generator\|async-generator' docs/GLOSSARY.md | wc -l` returns **0** for the whole file.
- [x] **F14.b — "the ordering contract ... absent from the glossary entry."** Add it: no row-order guarantee unless the query supplies `orderBy` or the model declares `Meta.ordering`; the default resolver appends no tiebreaker, so response order is database-dependent; deliberately asymmetric with `[`DjangoConnectionField`](#djangoconnectionfield)`, which appends a pk tiebreaker because its positional cursors require a total order. Source of contract: `django_strawberry_framework/list_field.py::DjangoListField` #"Ordering contract: a ``DjangoListField`` does NOT guarantee row order unless".
- [x] **F14.c — "a precision fix Round 1 escalated to you."** Replace the opening paragraph's `#"the sync path rejects an async `get_queryset` with `ConfigurationError`, mirroring the Relay defaults"` with a `SyncMisuseError` statement linking the existing `#syncmisuseerror` anchor. Not a correction of a falsehood — `django_strawberry_framework/utils/querysets.py::SyncMisuseError` multiple-inherits `ConfigurationError` — but the removal of a divergence from the reconciled spec, which says `SyncMisuseError` at every site.
- [x] **F14.d — the negative obligation: the Row-bound paragraph is left byte-identical.** `docs/GLOSSARY.md` `## `DjangoListField`` -> `**Row bound (`0.0.14`, spec-047).**` is untrimmed, unre-flowed, and not folded into the new text. R1 decision (a); re-verified by a Worker 3 pass.
- [x] **F14.e — the glossary text stays in the glossary's register.** No enumeration of the nine pinning tests (the file cites a `tests/` path only where placement is itself the point), no narration of the private helper names, no copy of the spec's paragraph or code sketch, no second copy of the row bound.
- [x] **F14.f — the edit is made through the Django ORM, never by hand and never by raw SQL.** `uv run python examples/fakeshop/manage.py shell`, `GlossaryTerm.objects.get(anchor="djangolistfield")`, assign `body`, `.save()`. A hand-edit of `docs/GLOSSARY.md` is silently reverted by the next render (`docs/builder/BUILD.md` `### Generated docs are DB-backed: edit the DB, then regenerate`).
- [x] **F14.g — regenerate and prove stability.** `uv run python scripts/build_glossary_md.py` from the repository root; `--check` exits 0; two consecutive renders byte-identical via `--md /tmp/dsf-glossary-r2.md` + `cmp` (a scratch path outside the repo). `git diff` alone is not the stability proof.
- [x] **F14.h — no collateral churn, and none reverted.** `git diff HEAD -- docs/GLOSSARY.md` shows only the `DjangoListField` change; `git status --short` shows only R2's four owned files; the `db.sqlite3` diff is classified semantically (`iterdump()`) rather than by size; `build_kanban_md.py --check`, `build_kanban_html.py --check` and `build_tree_md.py --check` all still exit 0 and neither kanban script is run in write mode. Unexpected churn is a stop-and-report, never a revert (`AGENTS.md` rule 34).

_The three subsections below were written by the planning Worker 1 and sat under `## Final verification (Worker 1)`, whose body still read "Not started" -- a placement error Worker 3 observed and correctly declined to touch. Re-homed here verbatim by the final-verification pass, per the section order in `docs/builder/ARTIFACT.md`; not one word of their text is edited. The planning pass's own `### Spec changes made (Worker 1 only)` record travels with them; the final pass's is under `## Final verification (Worker 1)` below._

### Prompt and build-plan citations verified

Recorded here rather than in a return message, because a citation this plan rests on must be re-derivable by the next reader (`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`). Cited-name drift is this series' recurring defect class.

**Verified correct — all nine F14 test names exist in `tests/test_list_field.py`**, each `grep -c "def <name>"` returning exactly 1: `::test_djangolistfield_async_generator_resolver_is_bounded`, `::test_djangolistfield_sync_resolver_returning_async_iterable_is_bounded`, `::test_djangolistfield_partial_async_generator_resolver_is_bounded`, `::test_djangolistfield_sync_async_generator_resolver_raises_sync_misuse`, `::test_djangolistfield_async_consumer_resolver_async_iterable_is_bounded`, `::test_djangolistfield_async_consumer_resolver_async_iterable_can_exhaust_before_bound`, `::test_djangolistfield_sync_resolver_returning_coroutine_rejects_loudly`, `::test_djangolistfield_sync_resolver_returning_custom_awaitable_rejects_loudly`, `::test_djangolistfield_sync_resolver_returning_future_cancels_it`.

**Verified correct — every source symbol F14 cites**, at `django_strawberry_framework/list_field.py`: `::_require_async_iterable_context`, `::_resolve_async_iterable`, the `is_async_generator_callable(user_resolver)` branch, the `isinstance(source, AsyncIterable) and not isinstance(source, Iterable)` branch in the sync wrapper, and `::DjangoListField`'s ordering-contract docstring. `django_strawberry_framework/utils/querysets.py::SyncMisuseError` is `class SyncMisuseError(ConfigurationError, RuntimeError)`, so "not wrong, just imprecise" is exact.

**Verified correct — the F14 gap measurement.** Re-measured as an occurrence count rather than a matching-line count: `grep -o 'AsyncIterable\|async generator\|async-generator' docs/GLOSSARY.md | wc -l` returns **0** across all 2149 lines.

**Verified correct — the render baseline.** `uv run python scripts/build_glossary_md.py --check` exits **0**, printing "is up to date"; `git status --short` over the four concurrent-writable tracked files returns nothing.

**Found WRONG — one mechanism claim, corrected in this plan.** The dispatch prompt justifies the ORM route by asserting that "a raw SQL update skips the `post_save` that maintains the `UUIDModel` side-row the renderer's in-process `/graphql/` query requests, so the render can fail or drop rows." That mechanism does not apply to this row. `examples/fakeshop/apps/kanban/signals.py` `#"for uuid_linked_model in UUID_LINKED_MODELS:"` connects `::create_uuid_row` only to the models in `UUID_LINKED_MODELS`, and `glossary.GlossaryTerm` is **not** among them — only the join model `kanban.CardGlossaryTerm` is. Independently, `::create_uuid_row` returns unless `created` is true, so it would not fire on an **update** to an existing row even for a linked model; and `scripts/build_glossary_md.py`'s `STATIC_GLOSSARY_QUERY` requests no `uuid` field for `allGlossaryTerms`, so the render does not read a side-row. The **conclusion** is unaffected — use the ORM — but the plan states the reasons that actually hold: `apps.glossary.models.TimeStampedModel`'s `updated_date = models.DateTimeField(auto_now=True, editable=False)` is maintained only on the Django save path, and BUILD.md's `### Generated docs are DB-backed` rule is the standing authority.

**Found IMPRECISE — one citation, escalated rather than fixed, because the file is R1's.** The reconciled spec's Slice 5 `README.md` sub-bullet says "`KANBAN.md #\"## Done\"` holds the authoritative content for the cut". The `## Done` column (line 1445 at write time) does hold the per-card bodies, so the citation is defensible — but the one-line, seven-card release summary a `README.md` bullet actually draws from lives at `KANBAN.md` line 62, under `## Snapshot`, not under `## Done`. This plan therefore points Worker 2 at `KANBAN.md #"## Snapshot"` and quotes the sentence inline. Recorded below for Worker 1's judgement; **not** held as a blocker and **not** a re-opening of F13's settled disposition.

### Notes for Worker 1 (spec reconciliation)

Two observations, neither dispatched as work, both in files R2 does not own.

1. **Optional, low: the Slice 5 `KANBAN.md` citation.** As above — `## Snapshot` carries the cut summary a README bullet needs; `## Done` carries per-card detail. If Worker 1 judges the sub-bullet worth tightening to name both, it is a one-clause custodian edit in R1's file. Deliberately not dispatched: the spec's claim is true as written and F13's disposition is settled.
2. **Out of scope, and named so a later pass need not re-derive it: `docs/GLOSSARY.md` `## `SyncMisuseError``'s own list of raising surfaces omits `DjangoListField`.** That entry's first bullet enumerates the surfaces that raise it — "the [Relay Node integration](#relay-node-integration) defaults `resolve_node` / `resolve_nodes`, the [`DjangoConnectionField`](#djangoconnectionfield) sync pipeline, the optimizer's sync prefetch-child build, and the [`FilterSet`](#filterset) related-visibility derive" — framed strictly around `cls.get_queryset` returning a coroutine. `DjangoListField` belongs on that list twice over: its sync default resolver applies the hook through `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` (`list_field.py` line 217 at write time), and `list_field.py::_require_async_iterable_context` raises the same error for a *different* misuse the entry's framing does not cover. **Not planned for R2:** widening that entry changes another term's own scope definition (a framing question, and its `**Status:** shipped (`0.0.5`)` line belongs to a different card), and F14 dispatched three named amendments to the `djangolistfield` entry only. Route to `docs/builder/bld-020-final.md`'s `### Deferred work catalog`.

### Spec changes made (Worker 1 only)

None this pass. Spec status/header lines re-verified per `docs/builder/worker-1.md` `## Spec status-line re-verification (every Worker 1 spawn)`: `docs/SPECS/spec-020-list_field-0_0_7.md` lines 1-10 read "Target release: `0.0.7`." / "Status: shipped (`0.0.7`, 2026-05-27); archived. Card `DONE-020-0.0.7`." plus the rationale-companion pointer and the pre-renumber provenance note. All accurate at HEAD; nothing this round falsifies them, and no edit is owed.

---

## Build report (Worker 2)

All 11 `### Dispatched findings checklist` boxes ticked; every one landed in this pass's diff. No deferral.

### Files touched

Grounded in `git status --short`.

- `README.md` — one new `0.0.7` bullet appended to the `## Status` -> "Earlier alpha surfaces" list, after the `0.0.8` bullet and before the "For the current capability snapshot" paragraph (F13). No link definition added; the file's `<!-- LINK DEFINITIONS -->` block is untouched.
- `examples/fakeshop/db.sqlite3` — `glossary_glossaryterm` row `id=455` (`anchor="djangolistfield"`): `body` rewritten, `updated_date` refreshed by `auto_now`. Written through the Django ORM (`manage.py shell`, `GlossaryTerm.objects.get(anchor="djangolistfield")`, assign `body`, `.save()`), never raw SQL and never by hand (F14.f).
- `docs/GLOSSARY.md` — regenerated only, via `uv run python scripts/build_glossary_md.py` from the repository root. Never hand-edited (F14.f, F14.g).
- `docs/builder/bld-review-2-docs_completion.md` — this report, the 11 checklist ticks, `Status: built`.

**Exact `README.md` bullet written:**

> - `0.0.7` — `DjangoListField`, the non-Relay `list[T]` root Query field (default `_default_manager.all()` resolver, `get_queryset` cooperation in sync and async contexts, root-gated optimizer planning, consumer-annotation-driven outer nullability), plus the `DjangoStrawberryFrameworkConfig` app config, the `manage.py export_schema` SDL command, the multi-database cooperation contract, the Django Trac #37064 hardening with its `safe_wrap_connection_method` consumer helper, and warning-free scalar registration through `strawberry_config()`.

**Exact glossary changes made (three, all inside the `djangolistfield` body column):**

1. F14.3 precision fix, inline in the opening paragraph — `` (the sync path rejects an async `get_queryset` with `ConfigurationError`, mirroring the Relay defaults) `` became `` (the sync path rejects an async `get_queryset` with [`SyncMisuseError`](#syncmisuseerror), mirroring the Relay defaults) ``. One occurrence, asserted `== 1` before the replace.
2. F14.1, new bolded-lead paragraph inserted after the opening paragraph:

> **Async-iterable resolvers.** A consumer `resolver=` may also be an **async generator function**, or a plain sync callable that returns an **async-only iterable**; both arms are supported and both are row-bounded exactly like the sync and coroutine arms. An async-only iterable is meaningful only under asynchronous execution: met from synchronous GraphQL execution it raises [`SyncMisuseError`](#syncmisuseerror) rather than silently yielding nothing, so use `await schema.execute(...)` for such a resolver.

3. F14.2, new bolded-lead paragraph inserted immediately after it:

> **Ordering.** A `DjangoListField` does **not** guarantee row order unless the query supplies an `orderBy` argument or the model declares `Meta.ordering`: the default resolver appends no tiebreaker, so the response array order is database-dependent. This is deliberately asymmetric with [`DjangoConnectionField`](#djangoconnectionfield), which appends a pk tiebreaker because its positional cursors require a total order; a flat list has no cursors an unstable order could invalidate.

The `**Row bound (`0.0.14`, spec-047).**` paragraph is byte-identical (F14.d): the insertion was performed by prefixing the two new paragraphs onto that paragraph's own marker string, so the paragraph itself was never re-written or re-flowed, and `git diff HEAD -- docs/GLOSSARY.md` shows its line as unchanged context.

### Tests added or updated

None. `README.md` is prose and `docs/GLOSSARY.md` is DB-rendered, so neither carries an assertable branch; the mechanical documentation gates listed under `### Test additions / updates` are the tests this round owes and every one was run below.

### Validation run

| Command | Exit | Note |
|---|---|---|
| `uv run python examples/fakeshop/manage.py shell < <scratch script>` | 0 | printed `saved 4061` (new body length) |
| `uv run python scripts/build_glossary_md.py` | 0 | "Wrote 142 terms, 146 category memberships, 1042 spec mentions across 49 specs" |
| `uv run python scripts/build_glossary_md.py --check` | 0 | "is up to date" |
| `uv run python scripts/build_glossary_md.py --md /tmp/dsf-glossary-r2.md` | 0 | scratch path outside the repo |
| `cmp docs/GLOSSARY.md /tmp/dsf-glossary-r2.md` | 0 | two consecutive renders byte-identical (F14.g) |
| `uv run python scripts/check_trailing_commas.py --check README.md docs/GLOSSARY.md docs/builder/bld-review-2-docs_completion.md` | 0 | scoped, per the baseline gate exception |
| `uv run python scripts/build_kanban_md.py --check` | 0 | read-only; "KANBAN.md is up to date". Neither kanban script was run in write mode. |
| `uv run python scripts/build_kanban_html.py --check` | 0 | read-only; "KANBAN.html is up to date" |
| `uv run python scripts/build_tree_md.py --check` | **1** | **pre-existing, unrelated, NOT caused by this pass** — see `### Plan expectations found wrong` below |
| `uv run pytest examples/fakeshop/apps/glossary --no-cov -q` | 0 | 11 passed |
| `git diff HEAD -- docs/GLOSSARY.md` | — | only the `DjangoListField` entry: 1 line replaced (the precision fix) + 4 lines added (the two new paragraphs and their blank separators). Nothing else in the 2000+-line file. |
| `git status --short` | — | the only files this pass modified are `README.md`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3`, and this artifact (untracked). 105 total entries; the remainder is the concurrent maintainer session's baseline-dirty work, untouched and unreverted. |

`uv run ruff format` / `uv run ruff check --fix`: **not run, and correctly so.** No `.py` file is in this pass's diff — the DB edit was executed *through* `manage.py shell` from a scratch script outside the repo, which writes data, not source. Both tools are no-ops on `.md`, and a repo-wide write-mode run would churn the concurrent session's files.

`scripts/review_inspect.py`: **skipped**, with the reason the plan gives — no `.py` file added or modified, no `optimizer/` or `types/` touch, no 30+/50+ logic lines.

### Concurrent-writable tracked files — before/after and churn classification

`md5 -q` recorded at pass start and at pass end.

| File | Before (md5) | After (md5) | Classification |
|---|---|---|---|
| `examples/fakeshop/db.sqlite3` | `85ce2d5c1ca2b10a10035fa640ac88b3` | `e247771049d02355876946dd8501d7e0` | **R2's intended output.** Classified semantically, not by size: `sqlite3.iterdump()` captured before and after, `diff` yields exactly 6 changed lines, all inside the single `INSERT INTO "glossary_glossaryterm" VALUES(455,...)` statement — `updated_date` `2026-06-17 21:25:35.360353` -> `2026-08-18 16:06:28.374786` and the two new body paragraphs. No other table, row, or column differs. |
| `docs/GLOSSARY.md` | `e0714a7155cf26670437a68ccde918bf` | `86de3c0a8be7b1a3a353c6749bc80811` | **R2's intended output**, regeneration only. |
| `KANBAN.md` | `5a6dfa0c60b316ec164635d8c8a2b829` | `5a6dfa0c60b316ec164635d8c8a2b829` | **unchanged**, byte-identical; `git status --short` clean. |
| `KANBAN.html` | `71da6153aebc6afb35ba822b12693571` | `71da6153aebc6afb35ba822b12693571` | **unchanged**, byte-identical; `git status --short` clean. |

`docs/TREE.md` was never written: the staleness classification below was derived by copying it to a scratch path outside the repo and rendering *there*. `git status --short -- docs/TREE.md` is empty.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **Paragraph order chosen: opening paragraph -> `**Async-iterable resolvers.**` -> `**Ordering.**` -> `**Row bound**`.** The plan left this to discretion. Arm-before-bound continues the opening paragraph's resolver narrative directly into its third arm, and it keeps the two new paragraphs adjacent to the prose they extend rather than splitting the `0.0.14` row-bound contract away from the entry's tail. Two paragraphs, not one, because they are independent contracts with different audiences (a consumer writing an async resolver versus a consumer relying on response order).
- **`**Ordering.**` as the bold lead, not a plain sentence.** The entry's other non-opening paragraph uses a bold lead, and a plain sentence would read as a continuation of the async-iterable paragraph.
- **The `0.0.7` README bullet names six package surfaces and omits `DONE-026-0.0.7`.** The plan's discretion item: `DONE-026` is example-project coverage (the `apps.scalars` fakeshop app plus a `BigIntegerField` on `apps.library.Patron`), not a package surface the way the other six are, and no sibling bullet in the list describes example-project work. Naming it as a package capability would have been wrong; folding it into the scalar clause would have implied a package surface that does not exist. Omitted.
- **Scalar registration named as `strawberry_config()`, not `StrawberryConfig.scalar_map`.** The sibling bullets name the symbol a consumer writes. `strawberry_config()` is the package's public factory (`django_strawberry_framework/scalars.py`); `StrawberryConfig.scalar_map` is the upstream mechanism underneath it, which is the register `CHANGELOG.md` and `KANBAN.md` use, not `README.md`'s.
- **No `README.md` link definition added** (F13.c). No sibling bullet carries a per-surface link and the list's lead-in already routes the reader to `CHANGELOG.md` / `docs/GLOSSARY.md`. `check_trailing_commas.py --check README.md` exits 0.
- **The async-iterable paragraph deliberately stops short of the coroutine / awaitable / `Future` rejection trio.** F14.a dispatched the async-generator and async-only-iterable arms and their `SyncMisuseError` rejection; the three `..._rejects_loudly` / `..._future_cancels_it` tests pin a *different* rejection whose error type this pass did not verify at source. Writing it unverified would have been the claim-fix defect this series keeps catching. Not a gap in the tick: F14.a's contract is fully stated.
- **The ORM edit asserted its own anchors before writing** — `body.count(old_precision) == 1` and `body.count("**Row bound (`0.0.14`, spec-047).**") == 1` — so a reflowed or already-edited body would have failed loudly rather than silently no-op'ing or double-inserting.

### Notes for Worker 3

- The glossary diff is best read as `git diff HEAD -- docs/GLOSSARY.md`, not `git diff --`: the concurrent session has staged files elsewhere in the tree.
- To re-derive the F14.d negative obligation independently: the `**Row bound**` line appears as unchanged context in that diff, and `git show HEAD:docs/GLOSSARY.md | sed -n '<its line>p'` byte-compares against the current line.
- The two new paragraphs cite no test and name no private helper (F14.e). `grep -c 'tests/' ` over the `djangolistfield` entry returns 0, and `_require_async_iterable_context` / `_resolve_async_iterable` / `is_async_generator_callable` appear nowhere in `docs/GLOSSARY.md`.
- `scripts/build_tree_md.py --check` exits 1 in this tree. It did so before this pass and for reasons entirely outside it; the evidence is below. Do not treat it as a regression, and do not run that script in write mode to "fix" it — doing so would publish a concurrent session's half-landed docstring change.

### Plan expectations found wrong

One, and it is a gate expectation rather than a content claim.

- **`uv run python scripts/build_tree_md.py --check` exits 1, not 0.** The plan's `### Test additions / updates` table and checklist box F14.h both expect 0. The failure is pre-existing and has nothing to do with the glossary DB write. Derived by copying `docs/TREE.md` to a scratch path outside the repo, rendering *into the copy*, and diffing: exactly three delta lines, and all three belong to the concurrent maintainer session's baseline-dirty work named in `docs/builder/build-020-list_field-0_0_7.md` `## Baseline-dirty out-of-scope files`.
  - Two identical lines (the current and target layouts) for `utils/converters.py`: on-disk `# Fail-loud converter-dispatch skeleton shared by the form + serializer converters.` versus rendered `# … shared by write-field and filter-input converters.` — the concurrent session's edit to that module's docstring. `django_strawberry_framework/utils/converters.py` is on the baseline-dirty list.
  - One added line for the untracked `examples/fakeshop/test_query/test_products_visibility_api.py`, also named on the baseline-dirty list.
  - `build_tree_md.py` renders from module docstrings, so a dirty docstring makes `--check` fail while the kanban DB and the glossary DB are irrelevant to it. Confirmed independently: `examples/fakeshop/db.sqlite3`'s semantic delta is one `glossary_glossaryterm` row, and `build_kanban_md.py --check` / `build_kanban_html.py --check` both still exit 0.
  - Correct disposition: leave it. Regenerating `docs/TREE.md` is outside R2's ownership *and* would publish another session's uncommitted docstring change (`AGENTS.md` rule 34, `START.md` "Don't regenerate the rendered docs ... while another session's feature work is mid-flight").

Everything else in the plan verified as written: the render baseline (`--check` exited 0 before the edit, so the post-edit diff isolates the intended change), the zero-occurrence `AsyncIterable` / `async generator` / `async-generator` gap measurement, the `#syncmisuseerror` anchor's existence (`docs/GLOSSARY.md` `## `SyncMisuseError``), the four cited `list_field.py` async-arm surfaces, `::DjangoListField`'s ordering-contract docstring, and `KANBAN.md #"## Snapshot"`'s seven-card sentence quoted verbatim in the plan.

### Notes for Worker 1 (spec reconciliation)

Nothing new to add: this pass surfaced no spec gap beyond the two observations Worker 1 already recorded in this artifact's own `### Notes for Worker 1 (spec reconciliation)` (the Slice 5 `KANBAN.md` `## Done` versus `## Snapshot` citation, and `docs/GLOSSARY.md` `## `SyncMisuseError``'s raising-surface list omitting `DjangoListField`). Both are confirmed still true at the end of this pass, and neither is R2's file.

One addition, offered as an amendment rather than a complaint, in case Worker 1 judges it worth carrying:

- **Where it lives:** `docs/builder/build-020-list_field-0_0_7.md` — not the spec, so this is routing information rather than a spec amendment. `## Checklist` / `### R2 findings — documentation completion`'s downstream gate expectations, inherited by this artifact's `### Test additions / updates` table.
- **Current wording:** "`uv run python scripts/build_tree_md.py --check` | exit 0 | Same, for the third DB-backed generated doc. Read-only."
- **Recommended replacement:** "`uv run python scripts/build_tree_md.py --check` | exit 1 at baseline, from the concurrent session's dirty `django_strawberry_framework/utils/converters.py` docstring and its untracked `examples/fakeshop/test_query/test_products_visibility_api.py` | Read-only. The failure is a **second baseline gate exception** alongside the `check_trailing_commas.py` one already recorded, and belongs in the build plan's `Baseline gate exception:` line so the final gate can pass on it."

---

## Review (Worker 3)

Reviewed the round's whole diff read as `git diff HEAD -- <path>` (three tracked files: `README.md` +1, `docs/GLOSSARY.md` +6/-1, `examples/fakeshop/db.sqlite3` same-size binary). Every claim the new text makes was checked against source at HEAD rather than against the build report, and every stated measurement about the binary or the generated file was re-derived independently.

### High: None.

### Medium: None.

### Low:

1. **The comparative clause `#"which appends a pk tiebreaker because its positional cursors require a total order"` is unqualified where the shipped behavior is conditional.** `docs/GLOSSARY.md` `## `DjangoListField`` -> `**Ordering.**`. `django_strawberry_framework/connection.py #"as a terminal tiebreaker UNLESS the effective ordering already ends in a"` appends the pk only when the effective ordering is not already a unique total order (delegated to `django_strawberry_framework/optimizer/plans.py::deterministic_order`), and the keyset branch above it (`cursor_field is not None and not explicit`) appends none at all because the declared `cursor_field` is finalization-validated to end in a unique column. Not a finding to fix: the sentence is verbatim-equivalent to `django_strawberry_framework/list_field.py::DjangoListField` #"which appends a pk tiebreaker to guarantee a" — the source F14.b names as the contract's origin — and to the register `docs/GLOSSARY.md` already uses at #"appends its deterministic primary-key tiebreaker". The load-bearing half (that `DjangoListField` appends no tiebreaker, and that the asymmetry is deliberate) is exactly true. Recorded so a later pass need not re-derive it.
2. **The `orderBy` recourse names an argument `DjangoListField` does not itself wire.** Same paragraph. `django_strawberry_framework/list_field.py` contains no `orderset` / `filterset` / `order_by` plumbing — the factory's whole signature is `target_type`, `resolver`, `description`, `deprecation_reason`, `directives`, `max_rows`, `trusted_max_rows` — so a consumer reading "unless the query supplies an `orderBy` argument" could read an argument into the shipped field that is not there. The statement is not false (order *is* determined when such an argument is supplied), and it is verbatim the reconciled spec's own Boundary line, whose next bullet records that filter/order input arguments are added to both primitives by the Layer-3 specs. R1's cohort, not R2's; routed below rather than held.
3. **Bullet length.** The new `README.md` `0.0.7` bullet is 546 characters against a 514-character longest sibling (`0.0.9`) and a 203-character shortest (`0.0.12`). Inside the list's own idiom — single line, no nested bullets, no bold sub-labels, surfaces not card IDs — and it carries six cards where `0.0.9` carries four, so it is proportionate. No action.

### DRY findings

**The plan's four forbiddances all held, checked against the diff rather than the report.**

1. *No restatement of the "Newest shipped" block.* The bullet mentions no `max_rows`, no row bound, and no resource policy; `grep` over the added line returns zero occurrences of `max_rows` / `trusted_max_rows` / `max_list_rows`. Nothing above the "Earlier alpha surfaces" lead-in was touched.
2. *No restatement of `docs/README.md`.* Verified in both directions. `docs/README.md` line 107's `DjangoListField` bullet carries the default resolver, the sync + async hook, and the `0.0.14` row bound with a glossary link; the new `README.md` bullet carries neither the row bound nor the async-detection rule, and its optimizer-cooperation clause has no counterpart in `docs/README.md` at all. Two clauses do overlap — the `_default_manager.all()` default resolver and sync/async `get_queryset` cooperation — **and that overlap is the list's own established convention, not a defect introduced here**: `README.md`'s `0.0.10` bullet is a near-copy of the opening of `docs/README.md` line 122 by the same measure, and the two files' audiences differ (a status list of what each cut added versus the docs index's per-primitive contract). Not raised as a finding.
3. *No copy of the spec's paragraph, code sketch, or private-helper narration.* Mechanically confirmed: `grep -c '_require_async_iterable_context\|_resolve_async_iterable\|is_async_generator_callable' docs/GLOSSARY.md` returns **0** across the whole file, and the two new paragraphs share no sentence with the spec's `## Goals`/Decision-8 prose — they state the consumer-facing contract in the entry's compressed voice.
4. *No test citation.* `grep -c 'tests/'` over the entry's rendered range returns **0**.

**The reverse question the plan could not ask — is anything now stated in more than one place that should be stated once?** Asked across `README.md`, `docs/README.md`, `docs/GLOSSARY.md`, and the reconciled spec. Answer: no deletion candidate.

- The async-iterable arm and the ordering contract each now exist in three places — `django_strawberry_framework/list_field.py`'s docstring, the archived spec, and the generated glossary — and each occurrence is load-bearing in a different register: source-local invariant, archived design record, live consumer catalog. Deleting any one degrades a surface a different reader reaches. An archived spec is not a doc a consumer reads and is not trimmable as duplication; a docstring is not a consumer doc.
- The row-bound composition contract remains stated once as a policy contract (the glossary) and once as a field-facing surface (the spec), which is R1's decision (a) and out of scope here. Re-verified only to the extent of confirming the new paragraphs added no second copy of it: they do not.
- The one *near*-duplication in the round is item 2 above, and it is the pre-existing convention of the list the bullet joined.

**The existence challenge.** Asked of all four additions. The async-iterable arm was measurably absent from the entire 2149-line glossary (re-derived: `grep -o 'AsyncIterable\|async generator\|async-generator' docs/GLOSSARY.md | wc -l` returned **0** at HEAD and **3** now, counting occurrences not matching lines), so it had no consumer-facing statement anywhere; the ordering contract is a guarantee-that-is-not, discoverable only in production; the `SyncMisuseError` precision fix *replaces* text rather than adding any; the README bullet is required by `## Definition of done` item 16 and the reconciled Slice 5. No abstraction, indirection, or new structure was introduced that deletion could improve. Nothing to escalate.

### Claim verification — every new statement traced to source at HEAD

| New statement | Source read | Verdict |
|---|---|---|
| An async **generator function** resolver is a supported arm | `django_strawberry_framework/list_field.py` #"if is_async_generator_callable(user_resolver):" — dedicated `_wrap` branch | true |
| A plain **sync** callable returning an **async-only iterable** is a supported arm | same file #"if isinstance(source, AsyncIterable) and not isinstance(source, Iterable):" in the else-branch `_wrap` | true |
| Both arms are **row-bounded** exactly like the sync and coroutine arms | `::_resolve_async_iterable` awaits `_post_process_consumer_async` then `bounded_rows_async(..., max_rows, trusted=trusted_max_rows)` — the same bound the coroutine arm applies | true |
| An async-only iterable met from **synchronous** execution raises `SyncMisuseError` rather than silently yielding nothing | `::_require_async_iterable_context` raises `SyncMisuseError` unless `in_async_context()`; called on **both** arms *before* `_resolve_async_iterable` | true |
| Recourse is `await schema.execute(...)` | that raise's own message #"Use `await schema.execute(...)` for async iterable resolvers." | true |
| The sync path's async-`get_queryset` rejection is `SyncMisuseError`, not a bare `ConfigurationError` | `list_field.py` line 217's `apply_type_visibility_sync` -> `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` #"raise a named" ; `::SyncMisuseError` is `class SyncMisuseError(ConfigurationError, RuntimeError)` | true, and strictly more precise than the wording it replaced |
| `DjangoListField` appends **no** tiebreaker; order is database-dependent | `::DjangoListField`'s `_default` returns `bounded_rows(apply_type_visibility_sync(target_type, initial_queryset(...), info), ...)` with no `order_by` anywhere in the module | true |
| The asymmetry with `DjangoConnectionField` is deliberate | `::DjangoListField` #"has no cursors, so the unordered sequence is acceptable" and spec `#"The ordering asymmetry between the two primitives is deliberate"` | true (see Low 1 on the tiebreaker's unstated condition) |
| `#syncmisuseerror` resolves | `docs/GLOSSARY.md` line 1984 `## `SyncMisuseError``, confirmed by reading the heading; already the target of **8** links at HEAD | resolves |
| `#djangoconnectionfield` resolves | `docs/GLOSSARY.md` line 550 `## `DjangoConnectionField``, confirmed by reading the heading; already the target of **22** links at HEAD | resolves |

Both fragments were resolved against headings I read by hand rather than against a slugger's output, per the instrument lesson from this cycle's Round 1 (a slugger that trims after stripping punctuation reports live anchors as dangling). Their pre-existing use counts at HEAD are independent corroboration.

**Empirical confirmation of the arm claims, beyond reading:** `uv run pytest tests/test_list_field.py --no-cov -q -k "sync_async_generator_resolver_raises_sync_misuse or sync_resolver_returning_async_iterable_is_bounded or async_generator_resolver_is_bounded"` -> **4 passed**. Run to confirm the documented behavior is the shipped behavior, not to discover coverage.

### README bullet — factual content against the authoritative cut record

Checked clause by clause against `KANBAN.md` line 62's seven-card release sentence and against what each card actually shipped (`CHANGELOG.md` `## [0.0.7]` `### Added`).

| Bullet clause | Card | Verdict |
|---|---|---|
| `DjangoListField`, non-Relay `list[T]` root Query field, default `_default_manager.all()` resolver, `get_queryset` cooperation in sync and async contexts, root-gated optimizer planning, consumer-annotation-driven outer nullability | `DONE-020-0.0.7` | all six sub-clauses match the `### Added` entry and the shipped factory |
| the `DjangoStrawberryFrameworkConfig` app config | `DONE-021-0.0.7` | class name confirmed at `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig` |
| the `manage.py export_schema` SDL command | `DONE-022-0.0.7` | matches; the command writes SDL via `strawberry.printer.print_schema` |
| the multi-database cooperation contract | `DONE-023-0.0.7` | matches |
| the Django Trac #37064 hardening with its `safe_wrap_connection_method` consumer helper | `DONE-024-0.0.7` | matches; the helper is a public export from `django_strawberry_framework.testing`, so "consumer helper" is exact |
| warning-free scalar registration through `strawberry_config()` | `DONE-025-0.0.7` | **right seam.** `strawberry_config` is the public factory (`django_strawberry_framework/scalars.py::strawberry_config`, exported from `django_strawberry_framework/__init__.py`); `StrawberryConfig.scalar_map` — the spelling `KANBAN.md` and `CHANGELOG.md` use — is the upstream mechanism underneath it. `CHANGELOG.md`'s own migration diff instructs consumers to write `config=strawberry_config()`, so the symbol a consumer types is the correct choice for a bullet whose siblings all name consumer-facing surfaces |
| *(omitted)* scalar-conversion end-to-end coverage | `DONE-026-0.0.7` | omission correct: it is example-project coverage (`apps.scalars`, a `BigIntegerField` on `apps.library.Patron`), not a package surface, and no sibling bullet describes example-project work |

**Every surface listed belongs to `0.0.7` and none belongs to a neighbouring cut.** Specifically checked for the two most likely leaks: no row-bound / `max_rows` content (`0.0.14`) and no filtering/ordering content (`0.0.8`). Neither is present. `DONE-024`'s pre-renumber label in `CHANGELOG.md` (`046-…`) is the maintainer-escalated cluster and was not re-opened; the card *content* is what the bullet draws on, and that is correct.

### Register and voice

- `README.md`: one line, `- `0.0.7` — <surfaces>.`, newest-first position preserved (inserted after the `0.0.8` bullet at line 79, before the "For the current capability snapshot" paragraph at line 82). Names surfaces, prints no `DONE-0NN-0.0.7` identifier, adds no nested bullet and no per-surface link. Matches the seven siblings. The list's unexplained stop simply moved from `0.0.8` to `0.0.7`; extending it further is not F13's scope.
- `docs/GLOSSARY.md`: both additions use the entry's established bolded-lead paragraph shape (the same device `**Row bound (`0.0.14`, spec-047).**` uses), state contracts a consumer must know, cite no test and no private helper, and add no code sketch. Paragraph order (opening -> `**Async-iterable resolvers.**` -> `**Ordering.**` -> `**Row bound**`) is a discretion item the plan delegated; the choice keeps the resolver narrative contiguous and is sound.

### Conventions

- `AGENTS.md` rule 27: the added `README.md` line and the added glossary text contain **0** single-colon `path:Symbol` forms and **0** raw `path:NN` forms. All `path::Qualified` / `#"substring"` citations in this review section are confined to this `bld-*.md` artifact, where they are permitted.
- `START.md` "Markdown link convention": the new glossary text uses **in-page anchors inline** (`[text](#anchor)`), which is what the convention prescribes, and introduces no cross-file link, so no `<!-- LINK DEFINITIONS -->` block in either file needed touching — and neither was. `README.md`'s def block is byte-unchanged (`git diff HEAD -- README.md` is a single `+` line). No new ref-id, so no group-header ordering or alphabetization question arises.

### Dispatched findings checklist — all 11 ticks confirmed from the diff

| Box | Confirmed by |
|---|---|
| F13.a | the `+` line at `README.md` line 80, positioned after the `0.0.8` bullet and before the closing paragraph, leading with `DjangoListField`. `grep -n DjangoListField README.md` now returns exactly this line (nothing at HEAD) |
| F13.b | clause-by-clause table above: six of seven cards named as surfaces, zero card IDs printed |
| F13.c | DRY item 1 and 2 above; `README.md` link block unchanged; `check_trailing_commas.py --check README.md` re-run, **exit 0** |
| F14.a | glossary lines 658 (`**Async-iterable resolvers.**`); all four cited source surfaces traced, plus a focused pytest run |
| F14.b | glossary line 660 (`**Ordering.**`); traced to `::DjangoListField`'s ordering-contract docstring |
| F14.c | char-level diff of the opening paragraph: exactly one substitution, `` `ConfigurationError` `` -> `` [`SyncMisuseError`](#syncmisuseerror) ``, and reverting that one token reproduces the HEAD line **byte-identically** |
| F14.d | re-derived independently — see the measurement table below. Byte-identical, 779 bytes both sides |
| F14.e | `grep -c '_require_async_iterable_context\|_resolve_async_iterable\|is_async_generator_callable' docs/GLOSSARY.md` = **0**; `tests/` occurrences in the entry = **0**; no second copy of the row bound |
| F14.f | the `iterdump()` delta carries an `updated_date` refresh (`2026-06-17 21:25:35.360353` -> `2026-08-18 16:06:28.374786`) on the edited row, which only Django's `auto_now` save path produces — a raw `UPDATE` of `body` alone could not have produced it. Independently, `build_glossary_md.py --check` exits 0, which a hand-edit of the rendered file would have broken |
| F14.g | `--check` exit 0, plus two fresh renders to scratch paths outside the repo, `cmp`-clean against each other **and** against the in-tree file |
| F14.h | the whole-file `git diff HEAD` for `docs/GLOSSARY.md` is one hunk in one entry; the `iterdump()` delta is one row; `build_kanban_md.py --check` and `build_kanban_html.py --check` both re-run **exit 0**; no revert of anything. The box's `build_tree_md.py --check` expectation is the plan error Worker 2 caught — see below |

**Boxes I could not confirm from the diff: none.** All 11 have a matching change or, for the two negative boxes (F14.d, F14.e), a re-derived measurement.

### Measurements re-derived — mine versus Worker 2's stated figure

Worker 2's figures are measurements about a binary file and a generated file, so each was re-derived from scratch rather than accepted (`docs/builder/BUILD.md` `### Tracked binary / generated files`). HEAD references were obtained with `git show HEAD:<path>` into `/tmp/dsf-r3/`, never with `checkout` / `restore` / `stash`.

| Measurement | Worker 2 stated | I re-derived | Agreement |
|---|---|---|---|
| `db.sqlite3` `iterdump()` delta — **scope** | one `glossary_glossaryterm` row, `id=455`, `body` + `updated_date`; no other table, row, or column | `diff` of the two dumps is `1911c1911,1915` — a single `INSERT INTO "glossary_glossaryterm" VALUES(455,…)` statement replaced, `updated_date` `2026-06-17 21:25:35.360353` -> `2026-08-18 16:06:28.374786`, plus the two new body paragraphs. **No other table, row, or column differs.** | **agrees** — the load-bearing claim holds exactly |
| `db.sqlite3` `iterdump()` delta — **line count** | "exactly 6 changed lines" | `diff \| wc -l` = **8**; content lines = **5** (one `<`, four `>`); changed *statements* = **1** | **stated figure not reproducible.** Recorded, not held: the count is instrument-dependent (the new body embeds literal newlines, so "lines" depends on whether the hunk header and `---` separator count), and the scope claim — the half that matters — is exact. Same defect class as this cycle's earlier stated-count slips |
| Two-render byte stability | `cmp` exit 0 against `/tmp/dsf-glossary-r2.md` | rendered twice more to `/tmp/dsf-r3/render1.md` and `render2.md`; `cmp render1 render2` **exit 0**, and `cmp docs/GLOSSARY.md render1` **exit 0** | **agrees**, and strengthened: the in-tree file is byte-equal to a fresh render, so the DB and the committed file agree in both directions |
| `build_glossary_md.py --check` | exit 0 | re-run: **exit 0**, "`docs/GLOSSARY.md` is up to date." | **agrees** |
| `**Row bound**` paragraph byte-identity | byte-identical; achieved by prefixing onto its marker string | extracted the paragraph from `git show HEAD:docs/GLOSSARY.md` and from the working file and compared: **equal, 779 bytes on both sides** | **agrees** |
| Opening-paragraph blast radius | one occurrence replaced, asserted `== 1` before the write | reverting `` [`SyncMisuseError`](#syncmisuseerror) `` -> `` `ConfigurationError` `` in the current line reproduces the HEAD line exactly; each spelling occurs once | **agrees** |
| `build_kanban_md.py --check` / `build_kanban_html.py --check` | exit 0 each | re-run: **0** and **0**. Neither script run in write mode | **agrees** |
| `check_trailing_commas.py --check README.md` | exit 0 | re-run: **exit 0** | **agrees** |
| Glossary gap measurement | `AsyncIterable` / `async generator` / `async-generator` occurrences = 0 at HEAD | re-derived at HEAD: **0**; now **3** | **agrees** |

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty**. `__all__` and the re-export list are unchanged; no new public export. (Run against `HEAD`, not the index, because the concurrent session has staged files elsewhere.)

### CHANGELOG sanity

Not applicable; this slice does not touch `CHANGELOG.md`. Its `0.0.7` section was read only as corroborating evidence for the README bullet's card-to-surface mapping, and the maintainer-escalated pre-renumber-label cluster was not re-opened.

### Not applicable this round, each with its reason

- **Failability proofs:** none owed and none re-run. The round introduces no boundary, guard, gate, or rejection path — it *documents* ones that shipped at `0.0.7` / `0.0.14` (`docs/builder/BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a boundary a pass introduces). Boundary count in the diff: **0**, independently confirmed — the diff contains no `.py` line at all. My mandatory re-run floor is therefore legitimately empty; the empty set is legal exactly because no boundary meets the floor. **No source file was mutated in this pass**, so the Worker 3 source carve-out was not exercised.
- **Hot-path budget:** no number owed. The plan declares `none`, and nothing here runs per request, per resolver, per row, or per connection — one prose line and one `GlossaryTerm.body` column plus a build-time render.
- **Floor verification:** not owed. The plan declares `none`, and `docs/builder/BUILD.md` `## Floor verification` names glossary regeneration as exactly the `none` case.
- **`scripts/review_inspect.py`:** **skipped, with reason.** No `.py` file added or modified, no `optimizer/` or `types/` touch, no 30+/50+ logic lines — no trigger in `### When to run the helper during build` fires. No shadow files were written this pass.
- **Temp tests:** none created. `docs/builder/temp-tests/review-2/` was not used; the round has no assertable branch to probe, and the one empirical check I wanted was already a permanent test.

### Baseline gate exceptions — verified, not re-litigated

Both were re-confirmed as pre-existing and neither is treated as a finding.

- Repo-wide `check_trailing_commas.py --check` exits 1 on an untracked, gitignored `.claude/` agent-memory file. Not repository content; scoped to this cycle's files it exits 0 (re-run).
- `build_tree_md.py --check` reports `docs/TREE.md is not up to date`. `git status --short -- docs/TREE.md` is empty and no pass wrote it; the delta belongs to the concurrent session's dirty `django_strawberry_framework/utils/converters.py` docstring and its untracked `examples/fakeshop/test_query/test_products_visibility_api.py`. **`docs/TREE.md` was not regenerated**, correctly — doing so would publish another session's half-landed surface (`START.md` "Rendered docs", `AGENTS.md` rule 34).

### Round 1's inheritance — executed faithfully

`docs/builder/bld-review-1-spec020_reconciliation.md` `### What Round 2 inherits` carries exactly two items, and both landed as specified:

- **No glossary trim (judgement call (a)).** Honored to the byte: the `**Row bound**` paragraph is unchanged at 779 bytes, and the two new paragraphs sit outside it rather than folding into it.
- **The F14 glossary amendment.** Executed as R1 specified — the named stale wording replaced with the linked `SyncMisuseError` spelling, through the DB and a regenerate, never a hand edit. R1's own framing ("loose, not false") is confirmed at source: `SyncMisuseError` multiple-inherits `ConfigurationError`.

The two touch different paragraphs of the same entry, as R1 predicted, and neither undid the other.

### Things I verified and found wrong

1. **Checklist box F14.h's own gate expectation is wrong** — it asserts `build_tree_md.py --check` "still exit[s] 0". It exits **1** at baseline. Worker 2 caught this, recorded it under `### Plan expectations found wrong`, correctly declined to "fix" it by regenerating, and routed a replacement wording to Worker 1. Confirmed independently here: the failure is docstring-driven and has no relationship to either DB. The box's substantive content (no collateral churn, nothing reverted) is met; the stale sub-clause is a plan defect already recorded, so the tick stands.
2. **Worker 2's "exactly 6 changed lines" `iterdump()` figure is not reproducible** (8 diff lines / 5 content lines / 1 changed statement by my instrument). The scope claim it accompanies is exact, so nothing substantive turns on it — but it is another instance of this cycle's dominant defect, a stated count whose instrument is not stated. Recorded rather than held.
3. **My own dispatch prompt was wrong on one point.** It states the glossary diff is "`+6 / -1` in the `DjangoListField` entry" and asks whether the file "changed only by regeneration" — accurate — but it also frames the `**Row bound**` verification as needing the paragraph to be "byte-identical", and separately asks me to confirm the *`iterdump()` diff is 6 lines*. Repeating a figure whose instrument is unspecified into a reviewer's mandate is how a stated count survives review; I re-derived rather than confirmed, and the figure did not hold. No consequence for the verdict.
4. Nothing else in the plan, the build report, or the prompt was found false. Spot-checked in particular: the plan's `KANBAN.md #"## Snapshot"` quotation (verbatim at line 62), the `#syncmisuseerror` and `#djangoconnectionfield` anchor claims, the four cited `list_field.py` async-arm surfaces, `::SyncMisuseError`'s base classes, and the render baseline.

### What looks solid

- **The precision fix's blast radius is provably one token.** Reverting the substitution reproduces the HEAD line byte-for-byte. That is the strongest possible form of "I changed only what I said I changed" on a re-flowable prose line, and it is what let F14.c and F14.d be verified independently of each other.
- **The marker-string prefix technique for F14.d** is the right mechanism, not just the right outcome: it makes the negative obligation structurally impossible to violate rather than checked after the fact, and the pre-write `count(...) == 1` assertions on both the old clause and the row-bound marker mean a reflowed or already-edited body would have failed loudly instead of double-inserting.
- **The DB write is minimal and provably ORM-routed.** One row, two columns, and the `updated_date` refresh is itself the evidence that `.save()` was used — a raw `UPDATE` of `body` could not have produced it.
- **The paragraph that stops short.** Worker 2 declined to extend the async-iterable paragraph to the coroutine / awaitable / `Future` rejection trio because it had not verified that rejection's error type at source. Given that this cycle's recurring defect is exactly the over-broad claim written from a plausible inference, declining was the correct call and it is recorded with its reason. F14.a's dispatched contract is fully stated without it.

### Notes for Worker 1 (spec reconciliation)

Three items, none blocking, none in R2's cohort.

1. **Escalated, Low: the `orderBy` recourse in both the spec and the shipped docstring names an argument `DjangoListField` does not wire.** `docs/SPECS/spec-020-list_field-0_0_7.md` `#"unless the query supplies an `orderBy` argument or the model declares"` (and the mirroring `django_strawberry_framework/list_field.py::DjangoListField` docstring, and now the glossary's `**Ordering.**` paragraph, which faithfully copies them). `django_strawberry_framework/list_field.py` has no ordering plumbing, and the spec's own next bullet records that order arguments are added to both primitives by the Layer-3 specs. The statement is true as a conditional, so this is a precision question, not a false claim. Resolution paths: (i) leave it — the Layer-3 bullet two lines down already supplies the context; (ii) tighten the spec's Boundary line to say "an `orderBy` argument supplied by the Layer-3 ordering subsystem", which would then make a matching one-clause glossary amendment worth carrying in a later round. **Do not** fix it in the glossary alone — the no-partial-fix rule applies across the three surfaces. Deliberately not held: R1 reconciled that wording and F14.b dispatched the glossary text to match it.
2. **Recorded, no action asked: the unqualified pk-tiebreaker comparative** (Low 1 above). It matches both the shipped docstring and the glossary's existing register at #"appends its deterministic primary-key tiebreaker", so correcting it in the `djangolistfield` entry alone would create the divergence it aimed to remove. If it is ever tightened, all three sites move together.
3. **Confirmed still true, still out of scope: `docs/GLOSSARY.md` `## `SyncMisuseError``'s raising-surface list omits `DjangoListField`.** Worker 1 and Worker 2 both routed this to `docs/builder/bld-020-final.md`'s deferred catalog, and I am not requiring a fix. **Round 2's additions do make it more visible**, and that is worth recording for the catalog entry: the entry now has two inbound links from `djangolistfield` — one for the sync-hook rejection and one for a misuse (`::_require_async_iterable_context`) whose framing the `SyncMisuseError` entry does not cover at all, since that entry is written strictly around `cls.get_queryset` returning a coroutine. A consumer following the new `**Async-iterable resolvers.**` link lands on an entry that does not describe the case they arrived from. Still correctly deferred — widening it redefines another term's scope — but the catalog entry should note that the deferral now costs a visible round trip.

### Review outcome

`Status: review-accepted`. No High and no Medium findings. All 11 dispatched boxes are confirmed against the diff rather than the report, every new claim in both files traces to source at HEAD, both `#fragment`s resolve against headings read by hand, the generated file changed only by regeneration and the DB write is scoped to one row and two columns, the `**Row bound**` paragraph is byte-identical, and the four DRY forbiddances plus the reverse duplication question and the existence challenge all come back clean. The three Low items are recorded with their evidence; two are routed to Worker 1 because their correct fix spans surfaces R2 does not own, and one needs no action.

### Added on the recovery leg — re-derived spot-checks

This pass was interrupted by a transient API error after the review section was written but before the `Status:` line was set (`docs/builder/BUILD.md` `### Recovery from interrupted subagent runs`). The section above is adopted as written; nothing in it was rewritten. Four load-bearing verifications were re-derived from scratch on the recovery leg before setting the status, each with a fresh instrument:

| Re-checked | Instrument | Result |
|---|---|---|
| `**Row bound**` paragraph byte-identity | `git show HEAD:docs/GLOSSARY.md` into a scratch path outside the repo, paragraph extracted by regex from both sides and compared as bytes | **779 bytes both sides, equal** — agrees |
| `build_glossary_md.py --check` | re-run | **exit 0**, "is up to date" — agrees |
| `#syncmisuseerror` / `#djangoconnectionfield` | `grep -n` for the literal headings | `## \`SyncMisuseError\`` at line 1984, `## \`DjangoConnectionField\`` at line 550 — both resolve, agrees |
| `db.sqlite3` write scope | both dumps taken via `sqlite3.iterdump()` and aligned **statement-wise** with `difflib.SequenceMatcher`, not line-wise | 9921 statements each; **exactly one `replace` opcode**, the `glossary_glossaryterm` `id=455` row, `updated_date` `2026-06-17 21:25:35.360353` -> `2026-08-18 16:06:28.374786`. No other table, row, or column — agrees |

The statement-wise instrument independently settles the "6 changed lines" item above: at statement granularity the delta is **1**, which is why a line count of the same delta is not reproducible. The scope claim — the half the verdict rests on — is exact under both instruments.

One structural observation, recorded not fixed because the file region is Worker 1's: the three subsections at `### Prompt and build-plan citations verified`, `### Notes for Worker 1 (spec reconciliation)`, and `### Spec changes made (Worker 1 only)` are plan-time content (they say "this plan") but sit *below* the `## Final verification (Worker 1)` heading, whose body reads "Not started." The fresh Worker 1 should read them as belonging to `## Plan (Worker 1)`, and may re-home them; Worker 3 does not edit them.

---

## Final verification (Worker 1)

Run by a fresh Worker 1 that neither planned nor built this round. Everything below was re-derived from the files and from source at HEAD; no measurement, tick, or claim was accepted from the plan, the build report, or either Worker 3 leg. Diffs were read as `git diff HEAD -- <path>` throughout (a concurrent session has staged the two spec files), and every HEAD reference was obtained with `git show HEAD:<path>` into a scratch path outside the repository — never `checkout`, `restore`, `stash`, or `worktree`.

### Summary

R2 landed exactly what it was dispatched: one `README.md` `0.0.7` bullet and three amendments to `docs/GLOSSARY.md`'s `djangolistfield` entry, the glossary reached only by a scoped DB write plus a regenerate. No source file, no test file, and no third file changed. `Status: final-accepted`.

### Dispatched findings checklist — all 11 ticks audited against the files, not the reports

No box un-ticked, no box newly ticked, no box left `- [ ]`, so no deferral reason is owed under `### Spec changes made (Worker 1 only)`.

| Box | How I confirmed it independently | Verdict |
|---|---|---|
| F13.a | `grep -n DjangoListField README.md` returns exactly one line, 80, and `git show HEAD:README.md` contains none. The `git diff HEAD -- README.md` hunk header is `@@ -77,6 +77,7 @@`: the line sits after the `0.0.8` bullet and before the "For the current capability snapshot" paragraph, leading with `DjangoListField` | tick stands |
| F13.b | Clause-by-clause against `KANBAN.md` line 62 (`## Snapshot` -> `### In progress`) and `CHANGELOG.md` `## [0.0.7]` `### Added` — see the table below. Six surfaces named, zero `DONE-0NN-0.0.7` identifiers printed | tick stands |
| F13.c | The whole `git diff HEAD -- README.md` is one added line; the `<!-- LINK DEFINITIONS -->` block is byte-unchanged, so no ref-id was added. The bullet carries no `max_rows` / row-bound / resource-policy content and no clause of `docs/README.md`'s `DjangoListField` bullet beyond the default-resolver + `get_queryset` pair the list's own idiom already repeats. `uv run python scripts/check_trailing_commas.py --check README.md docs/GLOSSARY.md docs/builder/bld-review-2-docs_completion.md` re-run: **exit 0** | tick stands |
| F14.a | The paragraph is present in the rendered entry; all four cited surfaces read at source (`django_strawberry_framework/list_field.py::_require_async_iterable_context`, `::_resolve_async_iterable`, the `is_async_generator_callable(user_resolver)` branch, the `isinstance(source, AsyncIterable) and not isinstance(source, Iterable)` branch) and each supports the sentence built on it — see `### Every new documentation claim re-derived at HEAD` | tick stands |
| F14.b | The `**Ordering.**` paragraph is present and is a faithful compression of `::DjangoListField`'s ordering-contract docstring, which I read in full | tick stands |
| F14.c | Reconstructed the substitution: `` [`SyncMisuseError`](#syncmisuseerror) `` occurs once in the working line, `` `ConfigurationError` `` in that clause occurs once in the HEAD line, and reverting the one token reproduces the HEAD line **byte-identically** (`==` on the full string, not a visual diff). The Row-bound paragraph's own `ConfigurationError` link is untouched | tick stands |
| F14.d | **The negative obligation, re-measured a third time and independently.** Extracted the `**Row bound (`0.0.14`, spec-047).**` paragraph by string index from `git show HEAD:docs/GLOSSARY.md` and from the working file: **779 bytes on both sides, byte-equal**. Agrees with both prior passes | tick stands |
| F14.e | `grep -c '_require_async_iterable_context\|_resolve_async_iterable\|is_async_generator_callable' docs/GLOSSARY.md` = **0** across the whole file; `tests/` occurrences inside the `djangolistfield` entry = **0**; the entry states the row bound once | tick stands |
| F14.f | The DB delta carries an `updated_date` refresh only Django's `auto_now` save path produces (see below), and `build_glossary_md.py --check` exits 0 — which a hand-edit of the rendered file could not survive | tick stands |
| F14.g | `--check` exit 0; two further fresh renders to scratch paths outside the repo are `cmp`-clean against each other **and** against the in-tree file, so the DB and the committed render agree in both directions | tick stands |
| F14.h | `git diff HEAD -- docs/GLOSSARY.md` is one hunk in one entry across a 2000+-line file; the DB delta is one row (below); `build_kanban_md.py --check` and `build_kanban_html.py --check` re-run **0** and **0**, neither in write mode; `docs/TREE.md` is clean in `git status --short` and was never written. The box's `build_tree_md.py --check` expectation is the plan error Worker 2 caught and is a baseline exception, not a churn failure | tick stands, with the plan-error caveat carried below |

### Every new documentation claim re-derived at HEAD

Read from source, not inferred from the prose.

| Claim | Source | Verdict |
|---|---|---|
| An async **generator function** resolver is a supported arm | `django_strawberry_framework/list_field.py` `#"if is_async_generator_callable(user_resolver):"` — its own `_wrap` branch, taken before the coroutine branch; `django_strawberry_framework/utils/typing.py::is_async_generator_callable` is `inspect.isasyncgenfunction` on the target or its `__call__` | true |
| A plain **sync** callable returning an **async-only iterable** is a supported arm | same file, else-branch `_wrap` `#"if isinstance(source, AsyncIterable) and not isinstance(source, Iterable):"` | true |
| Both arms are **row-bounded exactly like** the sync and coroutine arms | both route to `::_resolve_async_iterable`, which is `bounded_rows_async(await _post_process_consumer_async(...), info, max_rows, trusted=trusted_max_rows)` — the identical bound and identical argument set the coroutine branch applies. `django_strawberry_framework/resource_policy.py::bounded_rows_async` really does bound an async-only iterable rather than falling through: its first line delegates to `bounded_rows` only when the result is **not** `AsyncIterable` or **is** also `Iterable`, and otherwise consumes a `limit`-length prefix and `aclose()`s the iterator | true, and "exactly like" is exact rather than approximate |
| An async-only iterable met from **synchronous** GraphQL execution raises `SyncMisuseError` "rather than silently yielding nothing" | `::_require_async_iterable_context` raises `SyncMisuseError` unless `in_async_context()`, and it is called on **both** arms *before* `_resolve_async_iterable`, so no partial consumption precedes the raise | true |
| Recourse is `await schema.execute(...)` | that raise's own message text | true |
| The sync `get_queryset` rejection is `SyncMisuseError` | `list_field.py::DjangoListField` `#"apply_type_visibility_sync("`; `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` reaches the raise through the shared `::reject_async_in_sync_context`, whose body is `if inspect.isawaitable(value): ... raise SyncMisuseError(...)` after closing the unawaited coroutine, and `::SyncMisuseError` is `class SyncMisuseError(ConfigurationError, RuntimeError)` | true, and strictly more precise than the `ConfigurationError` it replaced — not a correction of a falsehood |
| `DjangoListField` appends **no** tiebreaker; order is database-dependent | `::DjangoListField`'s `_default` returns `bounded_rows(apply_type_visibility_sync(target_type, initial_queryset(target_type), info), ...)`; the module contains no `order_by` at all | true |
| The asymmetry with `DjangoConnectionField` is deliberate | `::DjangoListField` docstring `#"has no cursors, so the unordered sequence is acceptable"`, and the spec's Boundary line `#"The ordering asymmetry between the two primitives is deliberate"` | true; the tiebreaker clause's unstated condition is Worker 3's Low 1, disposed of below |
| `#syncmisuseerror` and `#djangoconnectionfield` resolve | headings read by hand, not slugged: `## `SyncMisuseError`` at line 1984 and `## `DjangoConnectionField`` at line 550 | both resolve |

**The `README.md` bullet against the authoritative cut record.** `KANBAN.md` line 62 sits under `## Snapshot` -> `### In progress` (confirmed by walking every `##`/`###` heading at or above line 62) and names seven cards. The bullet names six as surfaces — `DjangoListField` with its four sub-clauses, `DjangoStrawberryFrameworkConfig`, `manage.py export_schema`, the multi-database cooperation contract, the Trac #37064 hardening with `safe_wrap_connection_method`, and `strawberry_config()` — each corroborated against its `CHANGELOG.md` `## [0.0.7]` `### Added` entry. `DONE-026-0.0.7` is omitted, correctly: it is example-project coverage (`apps.scalars` plus a `BigIntegerField` on `apps.library.Patron`) and no sibling bullet in that list describes example-project work. `strawberry_config()` rather than `StrawberryConfig.scalar_map` is the right seam for this list — `CHANGELOG.md`'s own migration diff instructs consumers to write `config=strawberry_config()`. No `0.0.8` filtering/ordering content and no `0.0.14` row-bound content leaked in.

**One pre-existing imprecision I checked and am NOT raising as a finding**, recorded so a later pass need not re-derive it: the entry's opening paragraph says async consumer resolvers "are detected at construction time via the partial-aware `is_async_callable` predicate", while the async-generator branch is in fact selected first by `is_async_generator_callable`. That sentence is at HEAD, is unchanged by this round, and is accurate for the arm it describes; the new paragraph names the generator arm without contradicting it. Not R2's to fix, and not worth widening a closed round for.

### The generated file changed only by regeneration, and the DB write stayed scoped

- `uv run python scripts/build_glossary_md.py --check` exits **0** ("is up to date"). A hand-edit of `docs/GLOSSARY.md` would fail here, so the rendered file provably agrees with the DB.
- Two further renders to scratch paths outside the repository are `cmp`-clean against each other and against the in-tree file — stability proved in both directions, not by `git diff`.
- **DB write scope, re-derived from scratch with two instruments.** `sqlite3.iterdump()` on `git show HEAD:examples/fakeshop/db.sqlite3` and on the working copy: **9921 statements each side**, and `difflib.SequenceMatcher(autojunk=False)` reports **exactly one non-equal opcode** — a single `replace` at index 1792, the `INSERT INTO "glossary_glossaryterm" VALUES(455,...)` row. Then, independently of the dump, a column-wise comparison of row `id=455` read through `sqlite3` across all 11 columns: **exactly two columns differ**, `updated_date` (`2026-06-17 21:25:35.360353` -> `2026-08-18 16:06:28.374786`) and `body` (3049 -> 4061 bytes). No other table, row, or column anywhere in the file. The same-size binary diff is therefore not being taken as evidence of anything (`docs/builder/BUILD.md` `### Tracked binary / generated files`); the semantic instruments are.
- `uv run pytest examples/fakeshop/apps/glossary --no-cov -q`: **11 passed**. `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-020-list_field-0_0_7.md`: **exit 0, 24 terms**.

### Disposition of Worker 3's three Low findings and its notes

Decided, not deferred as questions. Two of the three name a precision that is spread across three surfaces, one of which is a `.py` docstring — and **this cycle is declared no-source-and-no-test**, so no round in it can execute a whole-population fix. The no-partial-fix rule then decides the matter: partial is forbidden and whole is out of scope, so the correct action is to leave the text and carry the item.

1. **Low 2 / note 1 — the `orderBy` recourse. Decision: LEAVE, on Worker 3's path (i).** I confirmed the substance: `django_strawberry_framework/list_field.py` wires no ordering argument (the factory's whole signature is `target_type`, `resolver`, `description`, `deprecation_reason`, `directives`, `max_rows`, `trusted_max_rows`), and the glossary sentence is a faithful copy of `::DjangoListField`'s docstring and of the spec's Boundary line at `docs/SPECS/spec-020-list_field-0_0_7.md` `### Decision 8 — Out-of-scope boundary with `DjangoConnectionField`` `#"unless the query supplies an `orderBy` argument or the model declares `Meta.ordering`"`. **The statement is true as a conditional** — order *is* determined when such an argument is supplied — so it is not a false claim, and `docs/builder/worker-1.md` `## Spec custody` licenses a spec edit only where the build proves the spec incomplete, inconsistent, or inaccurate. It is none of those. The context Worker 3 says is missing is in fact supplied one bullet down, in the same Boundary list: "Filter / order / search / aggregate input arguments are added to BOTH primitives by the relevant Layer-3 spec when those subsystems ship" — I read it, and it is two lines below the sentence in question, not in a distant section. **No spec amendment. To the deferred catalog** as a three-surface tightening (spec Boundary line + `::DjangoListField` docstring + glossary `**Ordering.**`), to be taken whole by a cycle that owns source, or dropped.
2. **Low 1 / note 2 — the unqualified pk-tiebreaker comparative. Decision: LEAVE, same reasoning, and it is the weaker of the two.** Confirmed Worker 3's evidence at source: `django_strawberry_framework/connection.py #"as a terminal tiebreaker UNLESS the effective ordering already ends in a"` — the append really is conditional. But the glossary sentence is verbatim-equivalent to `::DjangoListField`'s own docstring (`#"which appends a pk tiebreaker to guarantee a"`), which is the contract's origin, and to the register `docs/GLOSSARY.md` already uses elsewhere. Correcting it in the `djangolistfield` entry alone would *create* the divergence R2's F14.c existed to remove. **No spec amendment. To the deferred catalog, bundled with item 1** — the two move together or not at all, since they are one sentence in three files.
3. **Low 3 / note 3 — `## `SyncMisuseError``'s raising-surface list omits `DjangoListField`. Decision: DEFER, with Worker 3's escalation of the cost accepted and recorded.** Re-derived independently: that entry's first bullet enumerates the raising surfaces as the Relay Node defaults, the `DjangoConnectionField` sync pipeline, the optimizer's sync prefetch-child build, and the `FilterSet` related-visibility derive, and frames all of them as "when `cls.get_queryset` returns a coroutine". `DjangoListField` is absent, and it belongs twice — its sync default resolver reaches `apply_type_visibility_sync`, and `::_require_async_iterable_context` raises the same error for a misuse that framing does not describe at all. Worker 3 is right that R2 made this visible rather than merely true: the `djangolistfield` entry now carries **two** inbound `#syncmisuseerror` links, and the second sends a reader to an entry that does not cover the case they arrived from. Still correctly out of R2's dispatch — widening that entry redefines another term's scope and its `**Status:** shipped (`0.0.5`)` line belongs to another card. **To the deferred catalog, and the catalog entry must carry the round-trip cost**, not just the omission.
4. **Worker 1's plan-time note 1 — the Slice 5 `KANBAN.md #"## Done"` citation. Decision: LEAVE, and this closes the question rather than passing it on.** Verified the geometry: the cut summary is at `KANBAN.md` line 62 under `## Snapshot` -> `### In progress`, while `## Done` begins at line 1445 and holds the per-card bodies. So `## Done` genuinely does hold "the authoritative content for the cut" — the sub-bullet's claim is **true as written**, merely not the shortest route to a one-line summary. Its only consumer was F13's author, and F13 is now landed and verified. Editing a true sentence in an archived, shipped spec to optimize a route nobody will travel again fails the custody test in `docs/builder/worker-1.md` `## Spec custody`. **No spec amendment, and nothing to the catalog** — this one is closed here, not carried.

**Net: no spec or rationale edit this pass.** Three items go to `docs/builder/bld-020-final.md`'s `### Deferred work catalog`: the `orderBy` precision and the pk-tiebreaker comparative as one three-surface bundle, and the `SyncMisuseError` raising-surface widening with its now-visible round trip.

### Artifact section ordering — fixed

The three subsections `### Prompt and build-plan citations verified`, `### Notes for Worker 1 (spec reconciliation)`, and `### Spec changes made (Worker 1 only)` were plan-time content sitting below a `## Final verification (Worker 1)` heading whose body read "Not started", which made the planning pass's work read as the auditor's. Worker 3 saw it and correctly declined to touch another role's region. **Re-homed verbatim to the end of `## Plan (Worker 1)`**, after `### Dispatched findings checklist`, with one added italic provenance line naming the move; not one word of their text is edited, and the planning pass's own `### Spec changes made (Worker 1 only)` record travels with them so its "None this pass" keeps its true referent. This pass's own record is below. Nothing in Worker 2's report or either Worker 3 section was moved or rewritten.

This is the second time in one cycle that a `## Final verification` placeholder written above someone else's subsections made those subsections read as the auditor's; the same slip is recorded in the R1 final-verification memory entry. The fix is to write the placeholder as the **last** thing in the artifact at planning time.

### Not applicable this round, each with its reason

- **Failability proofs:** none owed. The round introduces no boundary, guard, gate, or rejection path — it *documents* ones shipped at `0.0.7` and `0.0.14` (`docs/builder/BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a boundary the pass introduces). Estimated new boundary count 0, confirmed rather than assumed: the round's diff contains **no `.py` line at all**. My two Worker 1 confirmations are therefore both vacuously satisfied — there is no boundary whose proof could be missing, and there is no expression in which a fail-open shape could have landed.
- **Hot-path budget:** declared `none` and correctly so. Nothing here runs per request, per resolver, per row, per connection, or per outbound message; both surfaces are documentation, one of them build-time-generated.
- **Floor verification:** declared `none`. `docs/builder/BUILD.md` `## Floor verification` names doc regeneration as exactly the `none` case, so there is no unrun floor claim for the final gate to inherit — it should record "No floor-verification scope declared" for this round.
- **`scripts/review_inspect.py`:** skipped. No `.py` file added or modified; no `optimizer/` or `types/` touch.
- **`## Final test-run gate`:** deliberately not run here. It belongs to `docs/builder/bld-020-final.md` after the integration pass; no `uv run pytest --no-cov` full sweep was executed by this pass.
- **Staged-anchor sweep** (`docs/builder/worker-1.md` `## Final verification job` step 6): not applicable — this is a review round with no spec slice, and no `TODO(spec-020` anchor is in play in a documentation-only diff.

### Baseline gate exceptions — re-confirmed, not re-litigated

Both stand exactly as Worker 0 recorded them, and I re-derived each rather than reading the record.

- Repo-wide `check_trailing_commas.py --check` fails only on an untracked, gitignored agent-memory artifact outside repository content. Scoped to this round's three `.md` files it exits **0** (re-run).
- `build_tree_md.py --check` exits **1**. Re-derived the cause with a scratch copy: `cp docs/TREE.md <scratch>`, rendered *into the copy*, diffed against the original — **exactly three delta lines**, all from the concurrent maintainer session: two identical `utils/converters.py` docstring lines (rendered twice by the generator, once per layout section) and one added line for the untracked `examples/fakeshop/test_query/test_products_visibility_api.py`. `docs/TREE.md` itself is clean in `git status --short` and was not written by this pass. **Not regenerated**, per `START.md` "Rendered docs" — doing so would publish another session's half-landed surface.

### Things I verified and found wrong

Three, none load-bearing, none blocking.

1. **Worker 2's `### Plan expectations found wrong` inverts the two `converters.py` labels.** It writes "on-disk `... shared by the form + serializer converters.` versus rendered `... shared by write-field and filter-input converters.`" The reverse is true: the **on-disk module docstring** (the concurrent session's uncommitted edit) reads "write-field and filter-input", which is what the renderer emits; `docs/TREE.md`'s committed line reads "form + serializer", matching the HEAD docstring. Confirmed by `head -3` on the working file against `git show HEAD:django_strawberry_framework/utils/converters.py`. The attribution, the cause, the count, and the disposition are all correct — only the two labels are swapped. Recorded because this cycle's recurring defect class is precisely the *false description of a correct finding*.
2. **Worker 2's "exactly 6 changed lines" for the `db.sqlite3` dump is not reproducible**, as Worker 3 already found. My statement-wise instrument settles it: the delta is **one** replaced statement and, column-wise, **two** changed columns. Both prior passes reached the right scope claim; only the line count was instrument-dependent. Nothing turns on it.
3. **Plan checklist box F14.h asserts `build_tree_md.py --check` exits 0.** It does not, and did not at baseline. The box is otherwise fully satisfied, so I have left it ticked rather than un-ticking a box over a plan-authored expectation the builder correctly identified as wrong and the reviewer correctly declined to hold. The build plan is Worker 0's file, so Worker 2's recommended replacement wording for it is routed onward rather than applied — the final gate should fold `build_tree_md.py --check` in as a **second** recorded baseline gate exception alongside the `check_trailing_commas.py` one.

Everything else in the plan, the build report, and both Worker 3 legs verified as written, including the 779-byte Row-bound identity, the render-stability proof, the anchor resolutions, the zero-occurrence gap measurement, the nine cited test names' shape, and the recovery leg's four re-derived spot-checks.

### Spec changes made (Worker 1 only)

**None.** No edit to `docs/SPECS/spec-020-list_field-0_0_7.md` or to `docs/SPECS/appx/spec-020-list_field-0_0_7-rationale.md`; both were left byte-untouched by this pass (they carry a concurrent session's staged content, which was neither read as mine nor disturbed).

- Spec status/header lines re-verified per `docs/builder/worker-1.md` `## Spec status-line re-verification (every Worker 1 spawn)`: "Target release: `0.0.7`." / "Status: shipped (`0.0.7`, 2026-05-27); archived. Card `DONE-020-0.0.7`." / "Owner: package maintainer." plus the rationale-companion pointer and the pre-renumber provenance note. All accurate at HEAD; nothing this round falsifies them, and no edit is owed.
- **No deferral reasons are owed for the checklist**: all 11 boxes are `- [x]` and all 11 audited as landed.
- Deferred to `docs/builder/bld-020-final.md` `### Deferred work catalog`, from this pass's dispositions: (i) the `orderBy`-recourse precision and the pk-tiebreaker comparative, as **one** three-surface bundle (spec Boundary line, `::DjangoListField` docstring, glossary `**Ordering.**`) takeable only by a cycle that owns source; (ii) `docs/GLOSSARY.md` `## `SyncMisuseError``'s raising-surface list omitting `DjangoListField` twice over, the entry to note that R2's second inbound link now makes the deferral cost a visible reader round trip. The Slice 5 `KANBAN.md` citation is **closed here**, not deferred.

### Final status

`Status: final-accepted`. All 11 dispatched boxes landed and were audited against the files; every new documentation statement in both files is true at HEAD when read against source; `docs/GLOSSARY.md` changed only by regeneration and the DB write is one row and two columns under two independent instruments; the `**Row bound**` paragraph is byte-identical at 779 bytes; no source, test, or unowned file was touched; and the round's three Low items are decided rather than passed on.

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
