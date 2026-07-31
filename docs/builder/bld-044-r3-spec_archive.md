# Build: R3 — archive the spec to `docs/SPECS/` (card 044, debug_extension / 0.0.14)

Spec reference: `docs/spec-044-debug_extension-0_0_14.md` (the whole file moves; no spec section
implements this item — the archive is a `## Slice checklist`-less obligation the build plan carries at
its own checklist line 134)
Rationale reference: `docs/spec-044-debug_extension-0_0_14-rationale.md` (moves with the spec)
Build plan: `docs/builder/build-044-debug_extension-0_0_14.md`
Canonical procedure: `docs/SPECS/NEXT.md` Step 8, run in the narrow mode declared below
Status: final-accepted

**Post-archive note (final verification).** The three spec-044 files now live at `docs/SPECS/`. The
`Spec reference` and `Rationale reference` lines above are the paths as they stood when this artifact
was planned and are left as written (`docs/builder/ARTIFACT.md` `## Re-pass sections`); the current
paths are recorded under `### Spec changes made (Worker 1 only)` in the final-verification section.

**`planned` here carries its ordinary meaning: dispatch Worker 2.** R1 and R2 were the Deviation-3
items — Worker 1 was the only role that could produce their deliverables, so Worker 0 read `planned`
on those artifacts as "dispatch Worker 3". R3 is a full-chain item: it has real Worker 2 work (the
inbound rewrites, the `SpecDoc.url` repoint, the `KANBAN` regenerate), so the chain is the unmodified
**Worker 1 (plan) -> Worker 2 (build, `built`) -> Worker 3 (review) -> Worker 1 (final verification,
which performs the move)**. Deviation 3's mapping does not apply to this artifact and no reader should
carry it forward.

---

## Plan (Worker 1)

### Scope decision recorded first: only spec-044 is archived

`docs/SPECS/NEXT.md` Step 8 archives **every** root-level spec, because it runs as part of authoring a
new spec and its stated post-condition is "exactly one WIP spec file at `docs/spec-*.md`". **This item
runs it in a narrow mode NEXT.md does not describe: only spec-044's three files move**, on the
maintainer's explicit instruction.

Measured at plan time — `ls docs/spec-*.md docs/spec-*.csv` — the root of `docs/` carries eight spec
stems. Seven stay:

| Spec stem at `docs/` root | Disposition in R3 |
|---|---|
| `spec-044-debug_extension-0_0_14` (`.md`, `-terms.csv`, `-rationale.md`) | **archived by this item** |
| `spec-045-visibility_boundary-0_0_14` | stays — out of scope |
| `spec-046-transport_security-0_0_15` (has its own `-rationale.md`) | stays — out of scope, and its cycle is preserved (Deviation 1) |
| `spec-050-debug_extraction-0_0_19` | stays — out of scope; **its inbound references are in scope** |
| `spec-051-boundary_dry_squeeze-0_0_20` | stays — out of scope |
| `spec-052-beta_release-0_1_0` | stays — out of scope |
| `spec-053-fieldset-0_1_1` | stays — out of scope |
| `spec-054-search_fields-0_1_2` | stays — out of scope |

Two consequences the plan states rather than leaves implied:

- **Worker 2 must not over-reach.** No file belonging to `045`, `046`, `050`, `051`, `052`, `053`, or
  `054` is moved, and none of those specs is edited except `spec-050` and only for the three spec-044
  **path** references named below. NEXT.md's "archive every candidate" instruction is superseded here
  by the maintainer's scoping.
- **NEXT.md's "exactly one WIP spec at `docs/`" invariant remains unsatisfied after R3, by design.**
  Seven live specs remain at root. That is recorded here and carried into `bld-044-final.md`'s
  `### Deferred work catalog` as a maintainer item, so a future NEXT.md run does not read the residue
  as drift this cycle caused. R3 also does not touch `Card.status` — card 44 is already
  `DONE-044-0.0.14` (verified read-only below) — so NEXT.md Step 3's queue normalization is not part of
  this item at all.

### The three plan declarations, confirmed for R3

Taken from the build plan's preamble and re-confirmed against this item rather than inherited silently:

- **Ownership partition: `none; sequential residual items.`** R3 is a single cohort. `### DRY analysis`
  below therefore has no cross-cohort shared shape to assign (`worker-1.md` `### DRY analysis shape`:
  a single-cohort partition still gets a plan, it just has no shared shapes).
- **Hot-path declaration: `none.`** R3 changes no package source. Nothing it writes runs per request,
  per resolver, per row, per connection, or per outbound message. The two management-command runs
  (`import_spec_terms`, `manage.py check`) and the three render scripts are per-invocation tooling.
- **Floor-verification scope: `none`, and this still holds for R3.** The item touches no Django /
  Strawberry / channels integration seam. It **does** run management commands against the example
  project — `examples/fakeshop/manage.py shell`, `import_spec_terms`, `check` — and that is worth
  saying out loud rather than leaving to inference: a management command is not a version-dependent
  integration seam in the sense `BUILD.md` `### When it is required` defines (request/response
  handling, ASGI plumbing, body parsing, session/auth, queryset compilation, schema construction
  against Strawberry internals, consumer/middleware wiring). It is an ORM read/write plus a template
  render, exercised at the shared `.venv` only, and nothing about its correctness varies with Django
  5.2.0-vs-newest. Declared `none`, stated rather than implied.

### Boundary count is a split trigger — the answer, in writing

**Zero new boundaries.** `worker-1.md` `### Boundary count is a split trigger` requires the count be
written down and the split question answered against it even when the diff would be small, so:

- R3 adds no guard, no cap, no rejection path, no validation branch, and no `if` at all. It moves three
  files, rewrites 95 relative link-definition targets and 5 prose/docstring path strings, updates one
  DB column, and re-renders three generated files. Every write is a path or a row.
- The count is therefore **0**, not "small". `BUILD.md` `### Slice splitting`'s second trigger (roughly
  five or more estimated boundaries) is not approached, and its first (diff shape) is not met either:
  the diff is one rename triple plus ~100 single-token line edits, all mechanically classifiable, all
  verifiable by the same audit run twice.
- **Not split.** What makes R3 one unit is not its size but that the move and the re-relativization are
  a **single decision**: the instant the files move, every relative target inside them is wrong, so
  splitting the move from the rewrite would deliberately ship a broken state. `BUILD.md`'s own rule —
  boundaries that cannot be separated because one contract makes them a single decision are one unit —
  applies to path rewrites for the same reason.
- Consequently `### Failability proofs` in Worker 2's build report will read
  `None; this pass introduced no new boundary.`, and Worker 3's mandatory re-run floor is
  arithmetically zero rather than a chosen subset.

### DRY analysis

- **Helper inventory checked.** `worker-1.md` `### Package-wide helper inventory before helper
  planning` exists to stop a plan proposing a package helper that duplicates an existing one, and its
  addressable domain is `django_strawberry_framework/`. **R3 writes zero files under
  `django_strawberry_framework/`, zero under `tests/`, and zero under `examples/`** (the build plan's
  standing context flag: no residual item changes package source), so the question the inventory
  answers — "which package helper could this item reuse, and which could it duplicate?" — has an empty
  domain. I did not regenerate it, and I am saying so rather than performing it hollow: a stale
  `docs/shadow/helper-inventory.md` does exist (187,353 bytes, generated 2026-07-28) and is **not**
  current — five package files are dirty right now from the concurrent spec-046 session — so citing it
  as current would be false, and refreshing 1,600 lines to answer a question with no candidates would
  be the cost the rule's own "widening the scope does not license reading the whole index" paragraph
  warns about. The shapes I would have grepped it for had R3 written package code (`parse`, `relativ`,
  `path`, `anchor`, `link`) are not package concerns at all; they are doc-tooling concerns, and the
  real inventory for them is the one below. **If Worker 2's pass discovers it must write any file under
  `django_strawberry_framework/`, that is out-of-scope work and a stop-and-report, not a licence to
  skip the inventory.**

- **Existing patterns reused — the live DRY question is the script, and it already exists twice.**
  NEXT.md Step 8 action 3 prescribes "a single deterministic transformation pass ... rather than ad-hoc
  edits", and Step 8 action 8 prescribes a path-resolution spot-check. Both this cycle's prior items
  already built the verification half, and `scripts/` already holds the checker half. Inventoried
  before planning anything new:

  | Existing tool | What it does | R3 disposition |
  |---|---|---|
  | `docs/builder/temp-tests/044-r2/link_audit.py` | heading slugifier, fence-aware, in-page anchor resolution, `][ref]`-use vs def symmetry, **cross-file file-exists AND `#anchor` resolution**, skips `http` targets, **takes paths from `sys.argv`** | **Reused verbatim, invoked in place.** No copy, no edit. Because it takes paths as arguments it works on `docs/SPECS/spec-044-…` post-move with zero changes. This is the anchor-resolution pass R1 asked R3 for. |
  | `docs/builder/temp-tests/044-r1/link_check.py` | the same checks, but **hardcodes** the `docs/spec-044-…` paths and does **not** skip `https://` targets (it reports the one URL def as `MISSING FILE`) | **Not used.** Strictly dominated by `link_audit.py`; using it would mean editing a closed item's tool and inheriting a false positive. Recorded so Worker 3 does not read its absence as an oversight. |
  | `scripts/check_spec_glossary.py` | validates every `-terms.csv` anchor resolves to a `GLOSSARY.md` H2 **and** is linked from the spec | **Reused, post-move.** Verified at plan time that it survives the move: `REF_TARGET_GLOSSARY_ANCHOR = re.compile(r"GLOSSARY\.md#(\S+)")` accepts **any** path prefix, so `../GLOSSARY.md#anchor` still satisfies it; `--terms` defaults to `<spec-stem>-terms.csv` **beside the spec**, which is where the CSV will be; `--glossary` defaults to `docs/GLOSSARY.md` relative to the CWD, so a repo-root invocation is unaffected. No flag change needed. |
  | `scripts/build_kanban_md.py`, `scripts/build_kanban_html.py` | render `KANBAN.md` / `KANBAN.html` from the kanban DB | Reused as-is. `build_kanban_md.py::spec_link` reads `spec["path"]`; `build_kanban_html.py` replaces the single `<!-- KANBAN_DATA_START --> … <!-- KANBAN_DATA_END -->` block and asserts exactly one replacement, so the hand-edited Vue shell is untouched by construction. |
  | `examples/fakeshop/manage.py import_spec_terms` | reconciles `GlossarySpecMention` + `CardGlossaryTerm` for every Done card from the companion CSVs | Reused. Its `_resolve_spec_path` behaviour is load-bearing for this item's **ordering** — see `### The ordering decision`. |

- **New helper justified: one throwaway, and it does not live in `scripts/`.** The transformation pass
  needs a classifier that does not exist: something that reads a `.md` file's link-definition block,
  buckets each target, and applies the six re-relativization rules. `scripts/` holds no path-rewriting
  tool (`grep -ln 'relativ' scripts/*.py` returns only incidental hits in the render scripts), so
  there is nothing to reuse. It will be written as **one file at
  `docs/builder/temp-tests/044-r3/relativize.py`** — gitignored per `BUILD.md` (`docs/builder/` is in
  `check_trailing_commas.py::EXCLUDE_SCRATCH_DIRS`, and `docs/builder/temp-tests/` is `.gitignore`d at
  line 192), cleared per cycle by `scripts/clean_up.py`. Its single responsibility: apply the
  classification table in `### Direction 2` to exactly the definition lines of exactly two named files
  and report per-line before/after.

  **It must not land in `scripts/` as a permanent artifact, and the reason is not tidiness.** A
  committed `scripts/archive_spec.py` would be standing source: pre-commit-enforced, expected to handle
  every spec's shape and every future directory layout, and read by the next agent as authoritative.
  R3 needs it for exactly two files in exactly one direction change, and NEXT.md Step 8 already
  prescribes writing it fresh per sweep. Promoting it on the evidence of one use would be building a
  general tool from a single instance. **A genuine `scripts/archive_spec.py` is a real candidate for a
  future card** — NEXT.md Step 8 is ~120 lines of procedure that has now been performed by hand
  repeatedly, and 13 measured orphan-row pairs in the glossary DB (see `### The DB side`) are evidence
  the hand procedure loses things — so this is recorded as a `### Deferred work catalog` candidate for
  `bld-044-final.md` rather than acted on here.

- **Duplication risk avoided.** Three near-copies a naive implementation would introduce, and how the
  plan prevents each:
  1. **A second link checker.** Prevented by naming `link_audit.py` as the tool and forbidding a copy
     of it under `044-r3/`. It takes argv paths; there is nothing to fork.
  2. **The same path string written twice under two owners.** `docs/SPECS/spec-044-debug_extension-0_0_14.md`
     is the post-move path. Worker 2 writes it into `spec-050` (a link def), `export_dry_review.py` (a
     docstring), and `SpecDoc.url` (a DB column); Worker 1 writes it as the `git mv` destination.
     Prevented from drifting by making the **filename identical to the current one** — only the
     directory changes — and by box W1-26's byte-identity check, so a typo in any of the four surfaces
     shows up as a link that does not resolve rather than as a plausible-looking variant.
  3. **Hand-editing a generated file.** The single largest duplication hazard here: `KANBAN.md`,
     `KANBAN.html`, and `docs/GLOSSARY.md` are exports of `examples/fakeshop/db.sqlite3`, so a hand
     edit is a second, rotting copy of a DB fact. Prevented by the explicit prohibition in boxes
     W2-9..W2-12 and by asserting two-consecutive-regenerate byte stability rather than reading a
     one-shot `git diff` as proof.

### The ordering decision: `import_spec_terms` runs AFTER the physical move, in Worker 1's pass

This is the one sequencing question in the item, and getting it backwards produces either stale rows or
a check that fails for the wrong reason. **Decided: Worker 2 does NOT run `import_spec_terms`.** Worker
1 runs it at final verification, after the `git mv`. The justification is mechanical, read out of the
command's own source at plan time rather than reasoned from the docs:

`examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py::_resolve_spec_path` does
**not** trust the stored URL. It takes the `docs/…` path out of `SpecDoc.url`, and if that path does
not exist on disk it falls back to `(repo_root / "docs").glob(f"**/{basename}")`, accepting the match
when there is exactly one (and raising `CommandError` on ambiguity). Three consequences:

1. **After Worker 2's repoint but before the move, `--check` still passes.** The url says
   `docs/SPECS/spec-044-debug_extension-0_0_14.md`, that path does not exist, the basename glob finds
   exactly one file at `docs/spec-044-debug_extension-0_0_14.md`, and the resolver silently corrects
   back to it — where the 42 `GlossarySpecMention` rows already sit. So `--check` reports
   `OK: 46 done cards have glossary links.` at review time. **Worker 3 should expect OK, not a
   failure.** (This corrects a plausible reading of the item's framing: `--check` does not "start
   failing on card 044" at the repoint; it starts failing at the *move*.)
2. **A pre-move `import_spec_terms` write run would be a pure no-op on card 044** — it would re-sync
   the 42 rows at the old, still-resolved path — while still opening `db.sqlite3` for write and
   producing binary churn with no semantic change. That is strictly worse than not running it.
3. **After the move, `--check` genuinely fails on card 044**, and for the right reason: the url path now
   exists directly, so `spec_path` resolves to `docs/SPECS/spec-044-debug_extension-0_0_14.md`, and
   `_assert_plan_matches_db` compares the 42 CSV anchors against the **zero** `GlossarySpecMention`
   rows at that path and raises `CommandError`. The write run is what closes it.

So the sync is inseparable from the move, which is Worker 1's by `BUILD.md`
`### Spec stays at its working location`. It runs in the same pass, immediately after.

### One deliberate transient state — Worker 3 is told, so it is not a finding

`BUILD.md` `### Spec stays at its working location` puts the mechanical move in **Worker 1's final
verification**, after the review. So at the moment Worker 3 reviews:

- `docs/spec-050-debug_extraction-0_0_19.md` and `docs/dry/export_dry_review.py` will say
  `docs/SPECS/spec-044-debug_extension-0_0_14.md`, and `SpecDoc.url` (hence the regenerated `KANBAN.md`
  / `KANBAN.html`) will say the same — **while the file is still at
  `docs/spec-044-debug_extension-0_0_14.md`**.
- Those links therefore **do not resolve yet, by design.** Worker 3 reviews each rewritten reference
  against the **post-move** path and reports a wrong *target* (a typo, a missed occurrence, a `docs/`
  prefix that should not be there), never the not-yet-moved file. "The link is broken" is not a
  finding for R3.
- Correspondingly, `import_spec_terms --check` returning `OK: 46 done cards` at review time is the
  **expected** result, for the reason given above, not evidence the DB work was skipped.
- Worker 1's final verification is the pass that performs the move and is the only pass at which
  "every link resolves" is a meaningful assertion.

### The baseline changed mid-pass: the maintainer committed the concurrent spec-046 work

Measured at both ends of this planning pass, and it moved. **`git status --short` opened at 16 entries
and closed at 7**, because the maintainer committed at 12:16:16 today:

```
05a08e31  fix(transport): linearize actor transitions against the whole protected send
```

That commit carries all ten of the concurrent-session entries the build plan's baseline-dirty list
named: `django_strawberry_framework/{_request_body,consumers,views}.py`, `auth/mutations.py`,
`utils/sessions.py`, `tests/{auth/test_mutations,test_routers,test_views}.py`, `docs/feedback.md`, and
`docs/spec-046-transport_security-0_0_15.md`. Attributed by `git log --name-status` and `git reflog
--date=iso`, per the standing rule that **a dirty list that SHRANK is a maintainer commit or a stale
snapshot, never a worker revert.** This pass issued no `.py` write and no revert of any kind.

Four consequences the later passes must not get wrong:

- **The live baseline-dirty list is now two entries plus this cycle's own untracked files:**
  `M docs/spec-044-debug_extension-0_0_14.md` (R1+R2's edits, this cycle's), `D
  to-many-search-optimizer-reproduction.md` (still a concurrent session's, still never edited or
  reverted), and the five untracked cycle files (`build-044-…md`, `bld-044-r1-…md`, `bld-044-r2-…md`,
  `bld-044-r3-…md`, `spec-044-…-rationale.md`).
- **The build plan's final-gate baseline exception is now moot for those eight `.py` files** — it stays
  recorded and harmless, but the gate no longer has to tolerate mid-edit source on their account. Do
  **not** read it as licence to wave through a *new* failure.
- **The lint gate is green tree-wide right now**, re-measured this pass: `uv run ruff format --check .`
  -> `405 files already formatted`; `uv run ruff check .` -> `All checks passed!`; `git diff --check`
  -> exit 0. So Worker 2's own scoped `ruff` run on `docs/dry/export_dry_review.py` starts from a clean
  tree and any failure it produces is its own.
- **Nothing spec-044 owns was touched by the commit** (verified: 0 spec-044 paths in its name-status),
  so every figure in this plan was re-measured after it and holds: spec **185,485** bytes / **102**
  definitions, rationale **43,859** / **28**, CSV **4,940**.

The list may grow again — it has twice this cycle — so W2-19 and W1-49 still require counting it at
both ends rather than trusting this paragraph.

### Direction 1 — FROM other files -> the moved spec (Worker 2)

Re-verified by grep at plan time rather than trusted from the build plan's table, and **measured in
occurrences, not matching lines**, because two figures in the inherited table are line counts:

| Location | Occurrences of the full path | Current text | Class |
|---|---|---|---|
| `KANBAN.md:100`, `KANBAN.md:1516` | 2 (2 lines) | `[spec-044-debug_extension-0_0_14.md](docs/spec-044-debug_extension-0_0_14.md)` | **GENERATED** — never hand-edit |
| `KANBAN.html` | **2** (1 line) | the JSON data block's `"path":"docs/spec-044-…md"` **and** `"url":"https://…/blob/main/docs/spec-044-…md"` | **GENERATED** — never hand-edit |
| `docs/spec-050-debug_extraction-0_0_19.md:554` | 0 full / 1 bare | `[spec-044]: spec-044-debug_extension-0_0_14.md` | reference definition from a `docs/` sibling -> `SPECS/spec-044-debug_extension-0_0_14.md` |
| `docs/spec-050-debug_extraction-0_0_19.md:127`, `:472` | 2 | prose `` `docs/spec-044-debug_extension-0_0_14.md` `` | inline code-span path, **not a link** -> `docs/SPECS/spec-044-debug_extension-0_0_14.md` |
| `docs/dry/export_dry_review.py:30` | 1 | `      --context docs/spec-044-debug_extension-0_0_14.md \` | module-docstring example invocation -> `docs/SPECS/…` |

**Two corrections to the inherited table, both measured:**

- `KANBAN.html` carries **2** occurrences on one line, not 1. `grep -c` counts lines; `grep -o … | wc -l`
  counts occurrences. Both are `SpecDoc.url`-derived and both regenerate.
- `spec-050:554`'s definition target is the **bare** `spec-044-debug_extension-0_0_14.md` with no
  `docs/` prefix, so a sweep for the `docs/`-prefixed form misses it. This is exactly R2's carried
  lesson — prefer the shortest distinctive token — and it applies to Worker 2's own re-verification
  grep: use `spec-044-debug_extension`, never `docs/spec-044-debug_extension-0_0_14.md`.

**Verified absent** (no path-form reference): `CHANGELOG.md`, `README.md`, `GOAL.md`, `TODAY.md`,
`AGENTS.md`, `START.md`, `BACKLOG.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, `docs/README.md`. The
remaining tree-wide `spec-044` hits are **bare provenance references**, not paths, and must **not** be
touched: `.github/workflows/django.yml:52`, `django_strawberry_framework/optimizer/extension.py:839`,
`docs/TREE.md:614`, `docs/spec-051-…:{4 hits}`, `docs/spec-051-…-terms.csv:1`, `tests/extensions/__init__.py`,
`tests/extensions/test_debug.py`, `examples/fakeshop/test_query/test_debug_extension_api.py:{3}`,
`examples/fakeshop/test_query/test_multi_db.py:{2}`, `pyproject.toml:1`, `docs/dry/dry-file-extensions__debug.md:{2}`,
`docs/builder/bld-slice-5-docs_foldin.md:1`. `AGENTS.md` rule 27's symbol-path convention makes
`spec-044` a legitimate provenance token; only a **path** rots on a move.

**`CHANGELOG.md` is absolute** (`NEXT.md` Step 8 action 7 and the build plan's context flag): if
Worker 2's re-verification finds a hit there, it is surfaced as a one-line maintainer report and
**never** edited.

### Direction 2 — FROM the moved files -> everywhere else (Worker 1, at final verification)

`NEXT.md` Step 8's central warning: this is the direction that gets missed, because the visible diff
is only a rename while the broken links sit inside the moved file's unchanged body. It is **Worker 1's**
— `BUILD.md` `### Spec stays at its working location` forbids Worker 2 from editing the spec or the
rationale at all, and the move and the rewrite are one decision (see the boundary-count answer).

Measured at plan time. **Zero legacy inline `](path)` cross-file links exist in either file** — the
spec has 200 inline `](#anchor)` uses and 0 path-like ones; the rationale has 2 and 0 — so the whole
of Direction 2 is the two bottom definition blocks plus one prose code-span. That is the reference-style
convention paying for itself exactly as `START.md` "Markdown link convention" argues (~75% cheaper
move: 130 definition lines instead of ~330 scattered inline uses).

**The classification table. This is the contract `relativize.py` implements, and Worker 3 can review
it before the move happens.**

`docs/spec-044-debug_extension-0_0_14.md` — **102 definitions; 86 change, 16 do not:**

| Group / bucket | Count | Rule | Example |
|---|---|---|---|
| `<!-- Root -->` | 8 | `../X` -> `../../X` | `[kanban]: ../KANBAN.md` -> `../../KANBAN.md`; `[workflow-django]: ../.github/workflows/django.yml` -> `../../.github/…` |
| `<!-- docs/ -->` siblings — `GLOSSARY.md` | 43 | **inverts: gains a level** `GLOSSARY.md[#a]` -> `../GLOSSARY.md[#a]` | 42 anchored + `[glossary]: GLOSSARY.md`. Includes `[glossary-django-trac-37064]: GLOSSARY.md#django-trac-37064-hardening`, whose ref-id and anchor deliberately differ — a mechanical ref-id-to-anchor derivation would corrupt it |
| `<!-- docs/ -->` siblings — `README.md`, `TREE.md` | 2 | **inverts** -> `../README.md`, `../TREE.md` | `[docs-readme]`, `[tree]` |
| `<!-- docs/ -->` — `rationale*` | **15** | **UNCHANGED** — both files move together, so the sibling relation survives | `[rationale]` + `[rationale-d1..d12]` + `[rationale-nondecision]` + `[rationale-risks]`; 14 of the 15 carry a `#anchor` |
| `<!-- docs/SPECS/ -->` — `NEXT.md` | 1 | **inverts and SHORTENS** `SPECS/NEXT.md` -> `NEXT.md` | verified `docs/SPECS/NEXT.md` exists |
| `<!-- docs/SPECS/ -->` — sibling specs | 4 | **SHORTENS** `SPECS/spec-…` -> `spec-…` | `[spec-038]`, `[spec-041]`, `[spec-042]`, `[spec-043]`; all four verified present at `docs/SPECS/` |
| `<!-- django_strawberry_framework/ -->` | 3 | `../X` -> `../../X` | |
| `<!-- tests/ -->` | 2 | `../X` -> `../../X` | |
| `<!-- examples/ -->` | 3 | `../X` -> `../../X` | |
| `<!-- scripts/ -->` | 3 | `../X` -> `../../X` | |
| `<!-- .venv/ -->` | 7 | `../X` -> `../../X` | |
| `<!-- External -->` sibling checkouts | 10 | `../../X` -> `../../../X` | `../../django-graphene-filters/…` -> `../../../django-graphene-filters/…` |
| `<!-- External -->` absolute URL | 1 | **UNCHANGED** | `https://github.com/strawberry-graphql/strawberry/issues/4369` |
| `<!-- docs/builder/ -->` | 0 | group present and empty; stays present | |

`docs/spec-044-debug_extension-0_0_14-rationale.md` — **28 definitions; 9 change, 19 do not:**

| Group / bucket | Count | Rule |
|---|---|---|
| `<!-- Root -->` | 2 | `../GOAL.md` / `../KANBAN.md` -> `../../…` |
| `<!-- docs/ -->` — `GLOSSARY.md` | 1 | **inverts** `GLOSSARY.md#django-trac-37064-hardening` -> `../GLOSSARY.md#…`. This single definition is what keeps `check_spec_glossary.py`'s 42nd term reachable; R1 flagged it forward by name |
| `<!-- docs/ -->` — `spec-044-…md` | **19** | **UNCHANGED** — sibling after the move (`[spec-044]` + 18 `[s44-*]` anchored) |
| `<!-- docs/SPECS/ -->` | 2 | **SHORTENS**: `SPECS/NEXT.md` -> `NEXT.md`; `SPECS/spec-038-form_mutations-0_0_12.md` -> `spec-038-…` |
| `<!-- examples/ -->` | 1 | `../examples/…` -> `../../examples/…` |
| `<!-- External -->` | 3 | `../../…` -> `../../../…` |

**Totals: 130 definitions across the two files; 95 change, 35 do not.** In-page `](#anchor)` uses and
`https://` URLs are unchanged throughout.

**Prose paths inside the moved files** (not link definitions, so the classifier must not be the only
pass):

| Site | Text | Action |
|---|---|---|
| spec `:1103` | ``This spec lives at `docs/spec-044-debug_extension-0_0_14.md`: card NNN `044`,`` | **rewrite** to `docs/SPECS/spec-044-debug_extension-0_0_14.md` — a self-reference that becomes false at the move |
| spec `:513` | `` `docs/spec-044-debug_extension-0_0_14-terms.csv` `` | **verify, do not rewrite** — the CSV moves with the spec; this names a repo-relative path, not a relative link, and the `docs/SPECS/` prefix would be the correct form. **Ruled: rewrite it too**, for the same reason `:1103` is rewritten — both are repo-relative `docs/…` strings that name a file's location, and after the move `docs/spec-044-…-terms.csv` names nothing |
| spec `:90`, `:502`, `:1106`, `:1662`, `:2511` | `` [`docs/SPECS/NEXT.md`][next] `` | **unchanged prose**; only the `[next]` **definition** shortens. The visible code-span is a repo-relative path and stays correct |
| rationale `:83`, `:597` | `` [`docs/SPECS/NEXT.md`][next] `` | same — unchanged prose, definition shortens |

The `-terms.csv` itself needs **no** content edit: measured, it contains no `docs/`, no `.md`, and no
`SPECS` string (43 lines = header + 42 term rows).

### Direction 3 — between files that both moved

`NEXT.md` Step 8 direction 3 is "links inside one archived spec pointing at another archived spec". In
the general sweep that means N specs cross-referencing each other. **Here only spec-044's own three
files move, so direction 3 reduces to exactly the spec <-> rationale <-> CSV relationship** — and the
answer is stated rather than left unaddressed:

- **spec -> rationale: 15 definitions, all unchanged.** Sibling before the move, sibling after.
- **rationale -> spec: 19 definitions, all unchanged.** Same reason.
- **spec -> CSV: 1 prose path**, rewritten as ruled above (it is a repo-relative `docs/…` string, not a
  relative link, which is why it is the one direction-3 site that changes).
- **The four `[spec-038]` / `[spec-041]` / `[spec-042]` / `[spec-043]` definitions are NOT direction 3.**
  Those specs are **already** at `docs/SPECS/` and are not moving; they change because the *source*
  moved into their directory, which is direction 2's inversion case.

That is the whole of direction 3 for this item. Nothing is deferred under it.

### The verification a file-exists check cannot give you

Both closed items measured this and flagged it forward: after re-relativizing, a **cross-file `#anchor`
target can point at a real file and a dead heading**, and `os.path.exists` says nothing about it.
Measured populations at plan time — these are the numbers the post-move run must reproduce:

| Population | Spec | Rationale |
|---|---|---|
| link definitions | 102 | 28 |
| of which cross-file **anchored** | **56** (42 `GLOSSARY.md#…`, 14 `rationale#…`) | **19** (1 `GLOSSARY.md#…`, 18 `spec-044#…`) |
| in-page `](#anchor)` occurrences / distinct | 200 / 26 | 2 / 2 |
| headings | 35 | 20 |
| `][ref]` uses / defs | 103 / 102 | 28 / 28 |
| broken in-page anchors | 0 | 0 |
| cross-file failures (file or anchor) | 0 | 0 |

**Two corrections to the inherited figure, both measured.** The closed items recorded "33 cross-file
`#anchor` targets between the two files". The measurement is **32** between the two moved files (14
spec->rationale + 18 rationale->spec), and **75** cross-file anchored definitions in total once the 43
`GLOSSARY.md` ones are counted (42 in the spec + 1 in the rationale). Whichever way "33" was arrived
at, the anchor-resolution pass must cover **75**, not 33 — and `link_audit.py` covers all of them by
construction because it resolves every non-`http` definition. Recorded because a count that is a
sample under-scopes the audit, which is this cycle's most-repeated failure.

**The known false positive, so Worker 3 does not file it:** `link_audit.py` and `link_check.py` both
report `undefined=['"sql"']` on the spec. That is the `res.extensions["debug"]["sql"]` code span being
read as a `][ref]` use by a regex that does not strip inline code. All three prior passes recorded it.
It is not a link.

**`NEXT.md` Step 8 action 8's 5-10 path sample is the floor, not the ceiling.** The plan requires the
full set: every one of the 95 rewritten targets file-exists-checked and every one of the 75 cross-file
anchors resolved, by running `link_audit.py` over both moved files. A 5-10 sample cannot catch a
category miss in a 13-bucket classification.

### The DB side — measured read-only at plan time

All values below were read read-only on 2026-07-31 via
`uv run python examples/fakeshop/manage.py shell -c "…"`. Edits go through the Django ORM, never raw
SQL, and never by hand-editing a rendered file.

- `Card.objects.get(number=44)` -> `card_id` `DONE-044-0.0.14`, `status.key` `done`,
  `target_version.number` `0.0.14`. **Already Done; no status flip is in scope.**
- Its `SpecDoc` -> `name` `spec-044-debug_extension-0_0_14`, `url`
  `https://github.com/riodw/django-strawberry-framework/blob/main/docs/spec-044-debug_extension-0_0_14.md`.
  R3 repoints the url's **path only** to `docs/SPECS/…`. **`name` does not change** — it is unique, so
  a `.create()` collides; use the existing row and `full_clean()` + `save()`.
- `card.glossary_links.count()` -> **42**; `check_spec_glossary.py` -> `OK: 42 terms`. The DONE-card
  invariants (`SpecDoc` present + at least one `CardGlossaryTerm`) already hold, so **no bootstrap step
  is needed**.
- **The step most easily missed: 42 `GlossarySpecMention` rows carry
  `spec_path = docs/spec-044-debug_extension-0_0_14.md`** (measured; that is the only distinct
  spec-044 `spec_path` value). The move makes every one stale. `import_spec_terms` reconciles them as
  a side effect of processing all Done cards; `import_spec_terms --check` reports
  `OK: 46 done cards have glossary links.` today, and will fail on card 044 **after the move** until
  the write run happens (see `### The ordering decision`).
- **The wider `db.sqlite3` diff is real, precedented, and quantified.**
  `_sync_spec_mentions` deletes only rows **at the new `spec_path`** whose term is absent from the CSV;
  it never deletes the rows at the **old** path. So the write run will **add 42 rows** at
  `docs/SPECS/spec-044-debug_extension-0_0_14.md` and **orphan the existing 42** at
  `docs/spec-044-debug_extension-0_0_14.md`. `GlossarySpecMention.objects.count()` should move
  **1408 -> 1450**.

  This is not new damage: **13 archived specs already carry exactly this orphan pair** — measured, e.g.
  `docs/spec-028-orders-0_0_8.md` holds 43 orphan rows beside 44 live ones at
  `docs/SPECS/spec-028-orders-0_0_8.md`, and `docs/spec-043-test_client-0_0_14.md` holds 22 beside 22.
  59 distinct `spec_path` values exist for 46 live specs. **Ruled: do not clean them up in R3.** A
  spec-044-only cleanup would make card 044 the single card whose history diverges from 13 siblings —
  the same "a local fix leaves one file disagreeing with nine" argument this cycle already used twice —
  and the fix belongs with the `scripts/archive_spec.py` candidate. Recorded for
  `bld-044-final.md`'s `### Deferred work catalog` with the measured figures, and **flagged to the
  maintainer as a legitimately wider `db.sqlite3` diff**.
- **`docs/GLOSSARY.md` must stay clean.** Measured: `grep -n 'spec-0[0-9][0-9]-' docs/GLOSSARY.md`
  returns **0**, and the file's only `docs/SPECS` string is the empty `<!-- docs/SPECS/ -->` scaffold
  group header at `:1899`. So the glossary render carries no spec path and
  `git diff docs/GLOSSARY.md` should stay **empty** through this whole item. A non-empty diff there is
  a **signal to investigate, not expected output** — planned as an assertion at box W1-21.
- **`examples/fakeshop/db.sqlite3` is concurrent-writable and clean at baseline** (verified:
  `git status --short` on the DB, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md` is empty). Compare
  `iterdump()` semantics, **never file bytes** — git does not line-diff binaries and a same-size binary
  diff is not proof of a no-op (`BUILD.md` `### Tracked binary / generated files`).
- **`uv run python examples/fakeshop/manage.py check` passes today** (`System check identified no
  issues (0 silenced).`) — the baseline the post-item run is compared against.
- **Prove no-further-drift by hashing across two consecutive regenerates**, per `worker-0.md`
  "Closing out a kanban card" step 8. A single `git diff` shows the cumulative HEAD diff, not
  second-run stability.

### `git mv` on a dirty tracked file — and the verification that proves content survived

Three files move, and they need **two different commands**:

| File | Tracked? | Command | Why |
|---|---|---|---|
| `docs/spec-044-debug_extension-0_0_14.md` | tracked, **dirty** with R1+R2's edits (185,485 bytes vs 205,905 at HEAD) | `git mv` | `NEXT.md` Step 8 action 2: use `git mv` so the rename is tracked |
| `docs/spec-044-debug_extension-0_0_14-terms.csv` | tracked, clean (4,940 bytes) | `git mv` | same |
| `docs/spec-044-debug_extension-0_0_14-rationale.md` | **untracked** | plain `mv` | `git mv` fails on a path not under version control; Step 8 action 2 already carries this fallback |

`git mv` renames the file on disk and updates the index; it does not rewrite the working-tree content,
so R1's and R2's uncommitted edits ride along. **That is an expectation, not a proof.** The proof:

1. Before the move, `shasum -a 256` all three files and record the digests in the artifact.
2. Move.
3. `shasum -a 256` the three destination paths; **all three digests must be byte-identical**. This is
   the claim, and it is the same discipline `BUILD.md` `## Verifying a relocation, promotion, or
   unchanged-carryover claim` demands of any relocation: proven mechanically, never accepted on prose.
   It runs **before** `relativize.py` touches anything, so a rewrite cannot mask a mangled move.
4. Independently confirm the working-tree content is still the *post-R2* content and not HEAD's:
   `git diff -- docs/SPECS/spec-044-debug_extension-0_0_14.md` must still show R1's and R2's edits
   (git follows the staged rename), and `wc -c` must read **185,485** — not 205,905.

Two operational notes the maintainer should not be surprised by:

- **`git mv` stages the rename in the index.** That is what "tracked rename" means and it is what
  `NEXT.md` prescribes. It touches exactly the named paths — never `git add -A` (`START.md`
  "Concurrent sessions"). It is recorded here so a concurrent session's pathless `git commit` picking
  it up is understood rather than mysterious.
- **No `git stash` / `checkout` / `restore` / `worktree` at any point**, in any pass. For any HEAD
  comparison use `git show HEAD:<path>` into a scratch path **outside** the repo. A concurrent session
  is active on this tree right now.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current file before editing —
the concurrent spec-046 session is writing this tree, and `spec-050` is not one of its files but the
rule stands.

#### Worker 2's steps (the build pass)

Worker 2 may write **exactly these files**, and nothing else:

- `docs/spec-050-debug_extraction-0_0_19.md`
- `docs/dry/export_dry_review.py`
- `examples/fakeshop/db.sqlite3` (via the ORM only)
- `KANBAN.md`, `KANBAN.html` (via the render scripts only)
- `docs/builder/bld-044-r3-spec_archive.md` (its build report)
- `docs/builder/temp-tests/044-r3/` (its own scratch, optional)

**Worker 2 never moves or edits `docs/spec-044-debug_extension-0_0_14.md`, its `-terms.csv`, or its
`-rationale.md`, and never pre-adjusts their link paths.** Both R1 and R2 explicitly left those
untouched for R3, and R3's owner for them is Worker 1.

1. **Re-verify Direction 1 rather than trusting the table above.** From the repo root, with the
   **shortest distinctive token**:
   ```shell
   grep -rn 'spec-044-debug_extension' . | grep -v '^\./\.git/'
   ```
   Reconcile against `### Direction 1`. Classify each new hit as a **path** (in scope) or a **bare
   provenance reference** (out of scope, listed above, must not be touched). Count occurrences with
   `grep -o … | wc -l`, never `grep -c`. Record the reconciliation in the build report.
2. **`docs/spec-050-debug_extraction-0_0_19.md:127`** — prose code span
   `` `docs/spec-044-debug_extension-0_0_14.md` `` -> `` `docs/SPECS/spec-044-debug_extension-0_0_14.md` ``.
   Path only; the surrounding sentence ("(by then archived) is history — untouched") is already
   accurate and becomes *more* accurate after the move. Do not reword it.
3. **`docs/spec-050-debug_extraction-0_0_19.md:472`** — same rewrite, same prohibition on rewording.
4. **`docs/spec-050-debug_extraction-0_0_19.md:554`** — `[spec-044]: spec-044-debug_extension-0_0_14.md`
   -> `[spec-044]: SPECS/spec-044-debug_extension-0_0_14.md`. **The definition already sits under the
   `<!-- docs/SPECS/ -->` group header** (verified at plan time) and is the second of two entries
   there, after `[spec-038]`. Alphabetical order by ref-id is unchanged, and the group placement
   becomes *correct* rather than needing a move — `START.md`'s rule is "group = where the **target**
   lives", and after the move the target does live under `docs/SPECS/`. **Do not relocate the
   definition line.**
5. **Do not touch `docs/spec-050-…:{everything else}`.** In particular `[spec-038]: SPECS/spec-038-auth_mutations-0_0_13.md`
   in that same group names a file that does not exist (spec-038 is `form_mutations`; `auth_mutations`
   is spec-040). It is a pre-existing inaccuracy in another live spec, unrelated to spec-044's move,
   and **out of scope** — report it in the build report for the deferred catalog, do not fix it.
6. **`docs/dry/export_dry_review.py:30`** — `      --context docs/spec-044-debug_extension-0_0_14.md \`
   -> `      --context docs/SPECS/spec-044-debug_extension-0_0_14.md \`. Module-docstring example
   invocation. The line goes 57 -> 63 characters, well inside `line-length = 99`.
7. **Ruff the one Python file, scoped.** `uv run ruff format docs/dry/export_dry_review.py` then
   `uv run ruff check --fix docs/dry/export_dry_review.py`. **Never `.`** — a repo-wide write-mode run
   would touch the concurrent session's five dirty package files. `docs/dry/` is inside ruff's scan
   set (`pyproject.toml [tool.ruff] exclude` does not list it) but **outside**
   `check_trailing_commas.py`'s (`"dry"` is in `EXCLUDE_SCRATCH_DIRS`), so the layout hook will not
   touch it.
8. **Confirm `CHANGELOG.md` carries no hit.** If it does: one-line maintainer report, **never** an
   edit (`NEXT.md` Step 8 action 7; `AGENTS.md` rule 21; the build plan's context flag).
9. **Repoint `SpecDoc.url` through the ORM.** One shell call from the repo root:
   ```shell
   uv run python examples/fakeshop/manage.py shell -c "
   from apps.kanban.models import SpecDoc
   BLOB = 'https://github.com/riodw/django-strawberry-framework/blob/main'
   sd = SpecDoc.objects.get(card__number=44)
   assert sd.name == 'spec-044-debug_extension-0_0_14', sd.name
   sd.url = f'{BLOB}/docs/SPECS/spec-044-debug_extension-0_0_14.md'
   sd.full_clean(); sd.save()
   print(sd.name, sd.url)
   "
   ```
   **`name` is unique and does not change.** Never `SpecDoc.objects.create(...)` (it collides) and
   never `update_or_create` with a new `name`. Never raw SQL — the ORM's `post_save` writes the
   `UUIDModel` side row the render needs.
10. **Do NOT run `import_spec_terms`** (write or `--dry-run`). It belongs to Worker 1's pass, after the
    move; see `### The ordering decision`. Running it here is a no-op that churns the DB.
    `import_spec_terms --check` is read-only and may be run to confirm it still reports
    `OK: 46 done cards have glossary links.` — which is the **expected** result pre-move.
11. **Regenerate both kanban exports**, in this order:
    ```shell
    uv run python scripts/build_kanban_md.py
    uv run python scripts/build_kanban_html.py
    ```
    Never hand-edit either file. `build_kanban_html.py` replaces only the
    `<!-- KANBAN_DATA_START --> … <!-- KANBAN_DATA_END -->` block and asserts exactly one replacement,
    so the hand-edited Vue shell is safe by construction.
12. **Assert the render diff is exactly the intended change.** `git --no-pager diff KANBAN.md
    KANBAN.html` must show **2 occurrences changed in `KANBAN.md`** (lines 100 and 1516) and **2 in
    `KANBAN.html`** (the JSON `path` and `url` fields on one line) and nothing else. Any other card's
    data changing means a concurrent writer touched the DB — report it, do not revert it.
13. **Prove second-run stability** (the DB legitimately diverges from HEAD, so a clean `git diff` is
    not available as proof): hash both exports, re-run both render scripts, hash again, and confirm
    byte-identity across the two consecutive regenerates.
14. **Semantic-diff the DB, not its bytes.** Compare `sqlite3 … .dump` / `iterdump()` output before and
    after against a copy taken at pass start into a scratch path **outside** the repo, and confirm the
    only change is card 44's `SpecDoc.url` (plus whatever the ORM's `updatedDate`-style side rows
    legitimately carry). A same-size binary diff is not proof of a no-op.
15. **Assert `docs/GLOSSARY.md` stayed clean.** `git status --short docs/GLOSSARY.md` empty. A diff
    here means drift to investigate.
16. **`uv run python examples/fakeshop/manage.py check`** — must still pass.
17. **`git status --short`, both ends of the pass.** Every modified file must be in
    `### Files touched`. Anything else — in particular the concurrent spec-046 session's
    `django_strawberry_framework/{consumers,views,_request_body}.py`,
    `utils/sessions.py`, `auth/mutations.py`, `tests/{auth/test_mutations,test_routers,test_views}.py`,
    `docs/feedback.md`, `docs/spec-046-transport_security-0_0_15.md`, and the
    `to-many-search-optimizer-reproduction.md` deletion — is **reported, never reverted, never
    `git checkout`ed** (`AGENTS.md` rule 34; the build plan's baseline-dirty list). The list has grown
    twice already this cycle; count it yourself at both ends rather than trusting a snapshot.
18. **Set `Status: built`** and write the build report, including
    `### Failability proofs` -> `None; this pass introduced no new boundary.`,
    `### Hot-path budget` -> `Not applicable; plan declares no hot path.`, and
    `### Floor verification` -> `Not applicable; plan declares floor-verification scope none.`

#### Worker 1's final-verification steps (after Worker 3 accepts)

Worker 1 may write: the three spec-044 files (move + re-relativize), `examples/fakeshop/db.sqlite3`
(ORM only), `KANBAN.md` / `KANBAN.html` (render scripts only, if the DB sync changes them), this
artifact, and `docs/builder/worker-memory/worker-1.md`.

19. **Audit Worker 2's `### Dispatched findings checklist` ticks against the diff** — un-tick and set
    `revision-needed` for an over-tick, tick a landed box left open, record a one-line deferral reason
    for anything still `- [ ]` (`worker-1.md` `## Final verification job` step 3).
20. **Re-verify the spec's status/header lines** (`worker-1.md` `## Spec status-line
    re-verification`) — every spawn owes this. R2 read `:1-115` paragraph by paragraph and found it
    consistent; confirm the archive has not falsified anything (in particular `:1103`'s self-reference,
    which it has, and which step 26 fixes). Record any edit under
    `### Spec changes made (Worker 1 only)`.
21. **Capture the pre-move state.** `shasum -a 256` and `wc -c` for all three files; `git status
    --short`; `link_audit.py` over both `.md` files (expect the baseline table in `### The
    verification a file-exists check cannot give you`); `check_spec_glossary.py` (expect
    `OK: 42 terms`); `GlossarySpecMention.objects.count()` (expect 1408); `git status --short
    docs/GLOSSARY.md` (expect empty). Copy `db.sqlite3`'s `iterdump()` to a scratch path outside the
    repo.
22. **Move, three commands:**
    ```shell
    git mv docs/spec-044-debug_extension-0_0_14.md docs/SPECS/
    git mv docs/spec-044-debug_extension-0_0_14-terms.csv docs/SPECS/
    mv docs/spec-044-debug_extension-0_0_14-rationale.md docs/SPECS/
    ```
    The third is a plain `mv` because the file is untracked. It will be the **first** `-rationale.md`
    under `docs/SPECS/` (measured: `ls docs/SPECS/ | grep -c rationale` -> 0, of 87 entries), so there
    is no sibling precedent to copy — a fact worth stating rather than assuming.
23. **Prove the dirty content survived**, before any rewrite: re-`shasum` all three destinations and
    require byte-identity with step 21's digests; `wc -c` the spec at **185,485**; `git diff --
    docs/SPECS/spec-044-debug_extension-0_0_14.md` still shows R1's and R2's edits. Record all of it.
24. **Write `docs/builder/temp-tests/044-r3/relativize.py`** implementing `### Direction 2`'s
    classification table: parse only the lines matching `^\[([^\]\[]+)\]:\s+(\S+)$`, bucket each
    target, apply the bucket's rule, and print `ref-id | before | after | bucket` for every one of the
    130 definitions — including the 35 it deliberately leaves alone. A definition it cannot classify is
    an **error**, not a pass-through.
25. **Run it on both files and assert the diff shape**, which is the check that catches a category
    miss: exactly **86** definition lines changed in the spec and **9** in the rationale (95 total),
    **35** deliberately unchanged, and **zero** non-definition lines changed. Use `git diff -U0` on the
    spec — this cycle's established isolation method, since zero context puts each changed line in its
    own hunk so adjacency cannot shift attribution. The rationale is untracked, so diff it against the
    copy step 21 took.
26. **Rewrite the two prose paths the classifier does not see:** spec `:1103`'s self-reference and
    `:513`'s `-terms.csv` reference, both to the `docs/SPECS/…` form. Confirm the five `[next]` prose
    code spans (`:90`, `:502`, `:1106`, `:1662`, `:2511`) and the rationale's two (`:83`, `:597`) are
    left alone — the prose says `docs/SPECS/NEXT.md`, which stays correct; only the **definition**
    shortens.
27. **Anchor resolution, not a path sample.** `uv run python
    docs/builder/temp-tests/044-r2/link_audit.py docs/SPECS/spec-044-debug_extension-0_0_14.md
    docs/SPECS/spec-044-debug_extension-0_0_14-rationale.md`. Require: `broken=[]` for in-page anchors
    in both; `cross-file failures=[]` in both (this is the 75-anchor pass); `defs=102` / `defs=28`;
    `undefined=['"sql"']` on the spec **only** (the standing `res.extensions["debug"]["sql"]` false
    positive) and `undefined=[]` on the rationale; `unused=[]` in both. Reproduce the whole baseline
    table.
28. **File-exists every rewritten target** — all 95, not `NEXT.md`'s 5-10 sample.
    `link_audit.py` does this for every non-`http` definition, so step 27 discharges it; record that it
    covered 130 definitions and name the one URL it correctly skipped.
29. **`uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-044-debug_extension-0_0_14.md`**
    -> `OK: 42 terms - all have glossary entries and at least one spec link.`, exit 0. `--terms` and
    `--glossary` need no override (verified at plan time). If it fails, the `../GLOSSARY.md`
    re-relativization is wrong somewhere; fix until it exits 0 (`NEXT.md` Step 8 action 9).
30. **Now sync the glossary DB** — after the move, per `### The ordering decision`:
    ```shell
    uv run python examples/fakeshop/manage.py import_spec_terms
    uv run python examples/fakeshop/manage.py import_spec_terms --check
    ```
    Expect `Imported glossary terms for 46 done card(s).` then
    `OK: 46 done cards have glossary links.` **Run `--check` before the write too**, and record that it
    fails on card 044 with a `GlossarySpecMention rows for docs/SPECS/spec-044-…` mismatch — that
    failure is the evidence the sync was needed, and its absence would mean the move did not land.
31. **Measure the wider DB diff rather than characterising it.** `GlossarySpecMention.objects.count()`
    1408 -> **1450** expected; 42 new rows at `docs/SPECS/spec-044-…md`; 42 orphaned at
    `docs/spec-044-…md`. Confirm **no other card's** rows changed by differencing the `iterdump()`
    against step 21's copy. Report the orphan pair to the maintainer with the 13-precedent measurement
    and route the cleanup to the deferred catalog — **do not clean it up here.**
32. **Re-render and prove stability after the sync.** `build_kanban_md.py` + `build_kanban_html.py`,
    then assert byte-identity with Worker 2's output (the sync should not move the render, since the
    CSV and its anchor order are unchanged — assert it, do not assume it). Then `uv run python
    scripts/build_glossary_md.py` and assert `docs/GLOSSARY.md` is **byte-identical / still clean**.
    Two consecutive regenerates of each, hashed, for no-further-drift.
33. **`uv run python examples/fakeshop/manage.py check`** — must pass, as at baseline.
34. **Record old and new paths under `### Spec changes made (Worker 1 only)`**, per `BUILD.md`
    `### Spec stays at its working location`. All three files, plus the two prose-path edits and the 95
    definition rewrites summarized by bucket.
35. **Carry three items into `bld-044-final.md`'s `### Deferred work catalog`:** (a) NEXT.md's "exactly
    one WIP spec at `docs/`" invariant remains unsatisfied by design — seven live specs stay at root;
    (b) the 14th `GlossarySpecMention` orphan pair and the 13 precedents, with `import_spec_terms`'s
    delete-only-at-the-new-path behaviour named as the cause; (c) `scripts/archive_spec.py` as a
    candidate standing tool, and `docs/spec-050-…:554`'s wrong `[spec-038]` target as an unrelated
    find. Plus whatever the R2 hand-off's seven items already carry.
36. **Baseline / concurrent-work note**, with `git status --short` counted at both ends of the pass and
    any growth attributed rather than assumed. It grew twice already this cycle (1 -> 10 -> 16 entries;
    `docs/spec-046-transport_security-0_0_15.md` is new since R2 closed and is the concurrent session's,
    not this cycle's).
37. **Set `Status: final-accepted`** (or `revision-needed`) and append the worker-1 memory entry.

### Test additions / updates

**This item adds no pytest tests, and that is a ruling rather than an omission.** It writes no
executable package logic — three renames, 95 path rewrites, five prose/docstring path strings, one DB
column, three regenerates. `AGENTS.md` rule 10's live-first mandate binds lines reachable from a real
GraphQL query; nothing here is. `BUILD.md` `### What needs a proof, and what does not` scopes failability
proofs to boundaries, and R3 introduces zero. `uv run pytest` is not run in any pass of this item, and
never with `--cov*` flags in any pass of this cycle.

**The verification is the link / anchor / DB / regenerate battery. Pinned concretely so Worker 3 can
re-run it.** Every command from the repo root; the first block is what Worker 3 can run at review time
(pre-move), the second is what Worker 1 runs post-move.

**Worker 3, at review time (pre-move — remember the transient state):**

```shell
# 1. Direction 1 completeness, shortest distinctive token, occurrences not lines
grep -rn 'spec-044-debug_extension' . | grep -v '^\./\.git/'
grep -o 'docs/SPECS/spec-044-debug_extension-0_0_14\.md' docs/spec-050-debug_extraction-0_0_19.md | wc -l   # expect 2
grep -n 'spec-044-debug_extension' docs/spec-050-debug_extraction-0_0_19.md                                 # :127 :472 prose, :554 def -> SPECS/...
grep -n 'spec-044-debug_extension' docs/dry/export_dry_review.py                                            # :30 -> docs/SPECS/...
grep -c 'spec-044-debug_extension' CHANGELOG.md README.md GOAL.md TODAY.md docs/GLOSSARY.md docs/TREE.md docs/README.md  # expect 0 each

# 2. The moved files must still be untouched and un-pre-adjusted
git diff --stat -- docs/spec-044-debug_extension-0_0_14.md          # expect ONLY R1+R2's edits, nothing from this pass
wc -c docs/spec-044-debug_extension-0_0_14.md                        # expect 185485
wc -c docs/spec-044-debug_extension-0_0_14-rationale.md              # expect 43859
grep -c '^\[[^][]*\]:[[:space:]]' docs/spec-044-debug_extension-0_0_14.md            # expect 102
grep -c '^\[[^][]*\]:[[:space:]]' docs/spec-044-debug_extension-0_0_14-rationale.md  # expect 28
grep -c '^\[.*\]: \.\./\.\./\.\./' docs/spec-044-debug_extension-0_0_14.md           # expect 0 (no pre-adjustment)

# 3. The DB side
uv run python examples/fakeshop/manage.py shell -c "
from apps.kanban.models import SpecDoc
sd = SpecDoc.objects.get(card__number=44); print(sd.name); print(sd.url)"     # name unchanged; url path docs/SPECS/...
uv run python examples/fakeshop/manage.py import_spec_terms --check           # EXPECT OK: 46 done cards (pre-move; see the ordering decision)
git --no-pager diff KANBAN.md KANBAN.html                                     # expect exactly 2 + 2 occurrences changed
git status --short docs/GLOSSARY.md                                           # expect empty
uv run python examples/fakeshop/manage.py check                               # expect no issues

# 4. Render stability, two consecutive regenerates
shasum -a 256 KANBAN.md KANBAN.html
uv run python scripts/build_kanban_md.py && uv run python scripts/build_kanban_html.py
shasum -a 256 KANBAN.md KANBAN.html                                           # expect identical

# 5. Ruff, read-only and scoped
uv run ruff format --check docs/dry/export_dry_review.py
uv run ruff check docs/dry/export_dry_review.py
```

**Worker 1, post-move:**

```shell
shasum -a 256 docs/SPECS/spec-044-debug_extension-0_0_14.md \
              docs/SPECS/spec-044-debug_extension-0_0_14-terms.csv \
              docs/SPECS/spec-044-debug_extension-0_0_14-rationale.md   # match the pre-move digests
uv run python docs/builder/temp-tests/044-r2/link_audit.py \
  docs/SPECS/spec-044-debug_extension-0_0_14.md \
  docs/SPECS/spec-044-debug_extension-0_0_14-rationale.md
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-044-debug_extension-0_0_14.md
uv run python examples/fakeshop/manage.py import_spec_terms --check          # EXPECT FAILURE on card 044 here
uv run python examples/fakeshop/manage.py import_spec_terms
uv run python examples/fakeshop/manage.py import_spec_terms --check          # expect OK: 46 done cards
uv run python scripts/build_kanban_md.py && uv run python scripts/build_kanban_html.py
uv run python scripts/build_glossary_md.py                                   # docs/GLOSSARY.md must stay clean
uv run python examples/fakeshop/manage.py check
git diff --check                                                             # whitespace / conflict markers
```

**Temp-test opportunities under `docs/builder/temp-tests/044-r3/`** (gitignored; cleared per cycle by
`scripts/clean_up.py`):

- `relativize.py` — the deterministic transformation pass (Worker 1's, step 24). Its per-definition
  `ref-id | before | after | bucket` output is the reviewable record of the rewrite and should be
  captured to a file in the same directory.
- Pre-move copies of the two `.md` files and the CSV, so the untracked rationale can be diffed against
  its own prior state (`git diff` cannot see it). Worker 1's step 21.
- The pre-sync `iterdump()` of `db.sqlite3` — **the copy must live outside the repo** if it is a full
  dump of a tracked binary; a definition-level diff summary may be kept here.
- **Worker 2 may use the directory** for its own before/after captures of `KANBAN.md` / `KANBAN.html`
  hashes and the Direction-1 grep reconciliation. Nothing here is promoted to a permanent test: no
  entry catches a code-behaviour bug, so `BUILD.md`'s promotion rule does not fire.

### Implementation discretion items

Choices assessed and decided to be Worker 2's. Nothing architectural is delegated here.

- **The exact shape of the ORM one-liner** in step 9 — a single `shell -c` heredoc versus two, whether
  to `print()` the before value as well as the after, whether to assert `sd.name` with `assert` or an
  `if … raise`. The contract is fixed (row fetched by `card__number=44`, `name` unchanged, `full_clean()`
  before `save()`, no raw SQL, no `create()`); the spelling is Worker 2's.
- **Whether to capture the `iterdump()` baseline via `sqlite3 … .dump` or Python's
  `connection.iterdump()`.** Both satisfy `BUILD.md`'s "compare semantic content, not file bytes".
  Worker 2 picks; the scratch path must be outside the repo either way.
- **Whether to run the Direction-1 re-verification grep once tree-wide or as per-file probes**, and
  whether to record it as a table or a list in the build report. The requirement is that occurrences
  are counted with `grep -o … | wc -l` and that every hit is classified path-vs-provenance.
- **The order of steps 2-6** (the four inbound rewrites among themselves). They are independent edits
  to two files; any order works. Steps 1, 7, and 9-17 are ordered and not discretionary.
- **Whether to use `docs/builder/temp-tests/044-r3/` at all.** Worker 2's verification is short enough
  to run inline; the directory is available, not required.

### Dispatched findings checklist

This item has no spec `## Slice checklist` entry to copy — the spec's own checklist covers the three
shipped slices and carries no archive obligation, so per `worker-1.md` planning step 8 and `BUILD.md`
`### Dispatched findings checklist` this list stands in that position. One box per discrete obligation.
**All boxes are `- [ ]` at planning.** Worker 2 ticks `- [x]` only a box whose contract landed in its
diff this pass and states any deferral in the build report; Worker 1 audits every tick at final
verification. `W2-*` boxes are Worker 2's; `W1-*` boxes are Worker 1's final-verification pass.

**Worker 2 — Direction 1, the inbound rewrites**

- [x] **W2-1** Direction 1 re-verified by `grep -rn 'spec-044-debug_extension'` (shortest distinctive token), occurrences counted with `grep -o … | wc -l`, every hit classified **path** (in scope) vs **bare provenance reference** (out of scope), and the reconciliation against `### Direction 1` recorded in the build report.
- [x] **W2-2** `docs/spec-050-debug_extraction-0_0_19.md:127` prose code-span path -> `docs/SPECS/spec-044-debug_extension-0_0_14.md`; surrounding sentence not reworded.
- [x] **W2-3** `docs/spec-050-debug_extraction-0_0_19.md:472` prose code-span path -> `docs/SPECS/…`; surrounding sentence not reworded.
- [x] **W2-4** `docs/spec-050-debug_extraction-0_0_19.md:554` `[spec-044]: spec-044-debug_extension-0_0_14.md` -> `[spec-044]: SPECS/spec-044-debug_extension-0_0_14.md`, **left in place** under the existing `<!-- docs/SPECS/ -->` group (no line relocation, no reordering).
- [x] **W2-5** Nothing else in `docs/spec-050-…` touched — in particular the pre-existing wrong `[spec-038]: SPECS/spec-038-auth_mutations-0_0_13.md` target is **reported, not fixed**.
- [x] **W2-6** `docs/dry/export_dry_review.py:30` `--context` path -> `docs/SPECS/spec-044-debug_extension-0_0_14.md`.
- [x] **W2-7** `uv run ruff format docs/dry/export_dry_review.py` and `uv run ruff check --fix docs/dry/export_dry_review.py` — **scoped to that one file, never `.`** — both recorded pass/fail.
- [x] **W2-8** `CHANGELOG.md` confirmed to carry no spec-044 path reference; if one appears it is a one-line maintainer report and **never** an edit.
- [x] **W2-9** No moved-file write: `docs/spec-044-debug_extension-0_0_14.md`, its `-terms.csv`, and its `-rationale.md` are **not moved, not edited, and their link paths not pre-adjusted** — proven by `git diff --stat` on the spec showing only R1+R2's edits and by the rationale's byte count still reading 43,859.

**Worker 2 — the DB and the generated exports**

- [x] **W2-10** *(box text corrected at final verification, on Worker 2's own recommended replacement — the substance landed, the wording named the wrong field; `SpecDoc.url` is a read-only derived `@property`.)* **`SpecDoc.path`** for card 44 repointed through the Django ORM to `docs/SPECS/spec-044-debug_extension-0_0_14.md` (the derived `SpecDoc.url` property follows); `full_clean()` called before `save()`; **no raw SQL**. Verified live this pass: `name` `spec-044-debug_extension-0_0_14`, `path` `docs/SPECS/spec-044-debug_extension-0_0_14.md`, `url` `…/blob/main/docs/SPECS/spec-044-debug_extension-0_0_14.md`.
- [x] **W2-11** `SpecDoc.name` confirmed **unchanged** at `spec-044-debug_extension-0_0_14`, and no `.create()` / renaming `update_or_create` used.
- [x] **W2-12** `import_spec_terms` **not run in write mode** in this pass, with the reason recorded (`### The ordering decision`); `--check` may be run read-only and is expected to report `OK: 46 done cards have glossary links.` pre-move.
- [x] **W2-13** `KANBAN.md` and `KANBAN.html` regenerated via `scripts/build_kanban_md.py` and `scripts/build_kanban_html.py` — **neither hand-edited**.
- [x] **W2-14** *(parenthetical corrected at final verification; Worker 2 disclosed the third field in `### Files touched` and the plan's step 14 pre-authorized it, so this is a stale box text and not an over-tick.)* Render diff asserted to be exactly the intended change: **2** occurrences in `KANBAN.md` (`:100`, `:1516`) and **3** changed fields in `KANBAN.html` (the JSON `path` and `url`, plus card 44's own `updatedDate`, which is the DB's `modified` column rendered through), nothing else; any other card's data changing is reported as a concurrent writer's, never reverted.
- [x] **W2-15** Two-consecutive-regenerate byte stability proved for both exports by hashing (a single `git diff` is the cumulative HEAD diff, not second-run stability).
- [x] **W2-16** `examples/fakeshop/db.sqlite3` verified **semantically** — `iterdump()` differenced against a pass-start copy taken to a scratch path outside the repo — with the only change being card 44's `SpecDoc.url` and its legitimate ORM side rows. Never a byte comparison.
- [x] **W2-17** `git status --short docs/GLOSSARY.md` empty: the glossary render carries no spec path (measured: 0 hits for `spec-0[0-9][0-9]-`), so a diff there is a signal to investigate.
- [x] **W2-18** `uv run python examples/fakeshop/manage.py check` passes.
- [x] **W2-19** `git status --short` counted at both ends of the pass and compared against the post-`05a08e31` live baseline in `### The baseline changed mid-pass` (2 entries + 5 untracked cycle files); every modified file appears in `### Files touched`; any concurrent-session churn — the `to-many-search-optimizer-reproduction.md` deletion, or anything new — **reported, never reverted, never `git checkout`ed**, and any shrinkage attributed to a maintainer commit via `git log` / `git reflog`, never to a worker revert.
- [x] **W2-20** `### Failability proofs` reads `None; this pass introduced no new boundary.`; `### Hot-path budget` reads `Not applicable; plan declares no hot path.`; `### Floor verification` reads `Not applicable; plan declares floor-verification scope none.`; `Status: built` set.

**Worker 1 — final verification: the move**

- [x] **W1-21** Worker 2's boxes audited against the diff: over-ticks un-ticked with `revision-needed`, landed-but-open boxes ticked, every remaining `- [ ]` given a one-line deferral reason under `### Spec changes made (Worker 1 only)`.
- [x] **W1-22** Spec status/header lines re-verified this spawn (`worker-1.md` `## Spec status-line re-verification`); any archive-falsified line edited and recorded.
- [x] **W1-23** Pre-move state captured: `shasum -a 256` + `wc -c` for all three files, `link_audit.py` baseline for both `.md` files, `check_spec_glossary.py` -> `OK: 42 terms`, `GlossarySpecMention.objects.count()` -> 1408, `git status --short`, and an `iterdump()` copy outside the repo.
- [x] **W1-24** `git mv docs/spec-044-debug_extension-0_0_14.md docs/SPECS/` — `git mv` because the file is **tracked**, dirty notwithstanding.
- [x] **W1-25** `git mv docs/spec-044-debug_extension-0_0_14-terms.csv docs/SPECS/`.
- [x] **W1-26** `mv docs/spec-044-debug_extension-0_0_14-rationale.md docs/SPECS/` — plain `mv`, because `git mv` fails on an **untracked** path (`NEXT.md` Step 8 action 2's fallback). Recorded as the first `-rationale.md` under `docs/SPECS/`.
- [x] **W1-27** **The dirty-content proof:** all three post-move `shasum -a 256` digests byte-identical to W1-23's, `wc -c` on the spec reading **185,485** (not HEAD's 205,905), and `git diff -- docs/SPECS/spec-044-debug_extension-0_0_14.md` still showing R1's and R2's edits — run **before** any rewrite touches the files.

**Worker 1 — final verification: Directions 2 and 3**

- [x] **W1-28** `docs/builder/temp-tests/044-r3/relativize.py` written to implement `### Direction 2`'s classification table, erroring on any definition it cannot classify and printing `ref-id | before | after | bucket` for all 130.
- [x] **W1-29** Spec re-relativized: **86** of 102 definitions changed, **16** deliberately unchanged (15 `rationale*` siblings + 1 `https://` URL).
- [x] **W1-30** Rationale re-relativized: **9** of 28 definitions changed, **19** deliberately unchanged (the `spec-044` siblings).
- [x] **W1-31** The three inverting groups handled and named individually: `docs/` siblings **gain** a level (45 defs in the spec: 43 `GLOSSARY.md` + `README.md` + `TREE.md`, **plus the rationale's 1 `GLOSSARY.md` def = 46 across both files** — scope stated at final verification, because "45" reads as a both-files total and is not one); `[next]: SPECS/NEXT.md` **shortens** to `NEXT.md` (both files); the four `[spec-038]` / `[spec-041]` / `[spec-042]` / `[spec-043]` defs **shorten** from `SPECS/spec-…` to `spec-…` (plus the rationale's own `[spec-038]`) — **7 shortenings** in all.
- [x] **W1-32** `[glossary-django-trac-37064]: GLOSSARY.md#django-trac-37064-hardening` -> `../GLOSSARY.md#…` in **both** files, its ref-id-vs-anchor mismatch preserved verbatim (a mechanical ref-id-to-anchor derivation corrupts it, and it is what keeps `check_spec_glossary.py`'s 42nd term reachable).
- [x] **W1-33** *(the "zero non-definition lines" half is **falsified by measurement** and corrected here; the 95 is exact.)* Diff shape asserted with `git diff --no-index -U0` against W1-23's pre-move copies (both files, since the rename makes the tracked diff a combined one and the rationale is untracked): exactly **95** definition lines changed across both files (86 spec + 9 rationale), and the only non-definition lines the classifier touched are the **`<!-- docs/SPECS/ -->` group header and its blank line in each file**, relocated because 34 definitions changed **group** (not path) — see `### The group-relocation obligation the plan's table omitted`. Spec 90/90 lines in 11 zero-context hunks; rationale 11/11 in 6.
- [x] **W1-34** Spec `:1103`'s self-reference and `:513`'s `-terms.csv` reference rewritten to the `docs/SPECS/…` form; the seven `[next]` prose code spans (spec `:90`, `:502`, `:1106`, `:1662`, `:2511`; rationale `:83`, `:597`) confirmed **left alone**.
- [x] **W1-35** The `-terms.csv` confirmed to need **no content edit** (measured: no `docs/`, no `.md`, no `SPECS` string; 43 lines).
- [x] **W1-36** Direction 3 stated and verified rather than left unaddressed: it reduces to spec <-> rationale <-> CSV, all three move together, the 15 + 19 sibling definitions are unchanged by design, and the four `SPECS/spec-…` shortenings are direction 2's inversion case, not direction 3.

**Worker 1 — final verification: the anchor pass and the DB sync**

- [x] **W1-37** `link_audit.py` run over both moved files reproducing the full baseline: `broken=[]` both, `cross-file failures=[]` both (the **75**-anchor pass: 42 + 14 in the spec, 1 + 18 in the rationale), `defs=102` / `28`, `unused=[]` both, `undefined=['"sql"']` on the spec only as the standing false positive.
- [x] **W1-38** Every one of the 95 rewritten targets file-exists-checked — the **full set**, not `NEXT.md` Step 8 action 8's 5-10 sample — with the count of definitions covered recorded and the single correctly-skipped `https://` target named.
- [x] **W1-39** `check_spec_glossary.py --spec docs/SPECS/spec-044-debug_extension-0_0_14.md` -> `OK: 42 terms - all have glossary entries and at least one spec link.`, exit 0, no flag override needed.
- [x] **W1-40** `import_spec_terms --check` run **before** the write and recorded as **failing on card 044** with a `GlossarySpecMention rows for docs/SPECS/spec-044-…` mismatch — the evidence the sync is needed and that the move landed.
- [x] **W1-41** `import_spec_terms` write run -> `Imported glossary terms for 46 done card(s).`, then `--check` -> `OK: 46 done cards have glossary links.`
- [x] **W1-42** *(the "no other card's rows changed" half needed a stronger method than the box named — corrected at final verification.)* The wider DB diff measured, not characterised: `GlossarySpecMention.objects.count()` 1408 -> **1450**, 42 new rows at `docs/SPECS/spec-044-…md`, 42 orphaned at `docs/spec-044-…md`, 60 distinct `spec_path` values, **14** orphan pairs. **A raw `iterdump()` line diff does NOT show this** — it reads **1973 added / 1931 removed** lines, because `import_spec_terms` deletes and re-inserts all 949 `CardGlossaryTerm` rows and all mention rows with fresh surrogate ids and `updated_date` stamps. The proof is a **content-keyed multiset** comparison with surrogate ids and timestamps normalized: `glossary_glossaryspecmention` **only_before=0 / only_after=42** (all 42 at the new path); `kanban_cardglossaryterm` 949 -> 949 with **0** semantic difference; `kanban_card_labels` 237 -> 237 with **0**; `kanban_specdoc` 50 -> 50 with **0**. No other card's data changed.
- [x] **W1-43** The orphan pair reported to the maintainer as a legitimately wider `db.sqlite3` diff, with the 13 measured precedents (e.g. spec-028 43+44, spec-043 22+22; 59 distinct `spec_path` values for 46 live specs) and `import_spec_terms`'s delete-only-at-the-new-path behaviour named as the cause — and **not cleaned up in this item**.
- [x] **W1-44** *(the "byte-identical to Worker 2's output" prediction is **half falsified by measurement**, which is exactly why the box said assert rather than assume — corrected here.)* Both kanban exports re-rendered after the sync. `KANBAN.md` **is** byte-identical to Worker 2's output (`ffc4d283…dc7c`, and `build_kanban_md.py --check` reported up-to-date **before** any render this pass). `KANBAN.html` is **not**: `bcd9090a…abac` -> `209ae514…9ce9`, and `build_kanban_html.py --check` reported **Stale** before the render. The plan's premise ("the CSV and its anchor order are unchanged") was right and incomplete — `import_spec_terms` re-creates every `CardGlossaryTerm` row, and `KANBAN.html` renders `updatedDate` while `KANBAN.md` does not. Structurally diffed against HEAD's data block: **952 leaf differences = 950 `updatedDate` + card 44's `spec.path` + card 44's `spec.url`, and nothing else**; net byte delta still exactly **+12 = 2 x len("SPECS/")**, because the timestamps are equal-length. Two-consecutive-regenerate byte stability hashed and identical for all three generated files.
- [x] **W1-45** `scripts/build_glossary_md.py` run and `docs/GLOSSARY.md` confirmed **still clean** — the planned assertion, since the glossary renders no spec path.
- [x] **W1-46** `uv run python examples/fakeshop/manage.py check` passes; `git diff --check` recorded (whitespace / conflict markers), with any failure inside the concurrent session's files covered by the build plan's final-gate baseline exception.

**Worker 1 — final verification: the record**

- [x] **W1-47** Old and new paths for all three files recorded under `### Spec changes made (Worker 1 only)`, alongside the two prose-path edits and the 95 definition rewrites summarized by bucket (`BUILD.md` `### Spec stays at its working location`).
- [x] **W1-48** Three items carried to `bld-044-final.md`'s `### Deferred work catalog`: NEXT.md's one-WIP-spec invariant left unsatisfied **by design** (seven live specs stay at `docs/` root); the 14th `GlossarySpecMention` orphan pair with its cause and precedent count; `scripts/archive_spec.py` as a candidate standing tool, plus `docs/spec-050-…:554`'s wrong `[spec-038]` target as an unrelated find.
- [x] **W1-49** Baseline / concurrent-work note written with `git status --short` counted at **both** ends of the pass and any growth attributed positively (this item issues no `.py` write except `docs/dry/export_dry_review.py`), never reverted.
- [x] **W1-50** No `git stash` / `checkout` / `restore` / `worktree` ran in any pass; no commit; no branch created or switched. `Status:` set to `final-accepted` or `revision-needed`, and the worker-1 memory entry appended.

### Notes for Worker 1 (spec reconciliation)

Recorded at plan time, so the final-verification pass does not re-derive them.

- **The spec-vs-codebase gap check (`worker-1.md` planning step 3) found nothing to reconcile.** Every
  path, symbol, and count this plan cites was verified against the tree at plan time: the three files
  and their byte counts, the 130 link definitions and their buckets, the four inbound sites, the five
  `docs/SPECS/` targets the shortening rules point at, `check_spec_glossary.py`'s path-prefix
  tolerance, `import_spec_terms::_resolve_spec_path`'s basename fallback, and every DB figure. **No
  spec edit was needed this pass**, so `### Spec changes made (Worker 1 only)` is empty until final
  verification.
- **Two inherited figures are corrected in this plan, both measured, and the corrections are the plan's
  own product:** `KANBAN.html` carries **2** occurrences on one line (not 1 — `grep -c` counts lines),
  and the cross-file anchor population is **75** definitions in total / **32** between the two moved
  files (not the recorded "33"). The audit is scoped to 75 accordingly. R2's carried lesson — a long
  grep phrase is a *sample* of a claim's vocabulary and cannot establish a count — is why `spec-050:554`
  was found at all: its target is the **bare** filename with no `docs/` prefix.
- **Worker 3's review surface for R3 is inherently narrow, by `BUILD.md`'s design, and that is worth
  naming.** The item's riskiest work — 95 path rewrites inside two files — lands in Worker 1's
  final-verification pass, *after* the review, so no independent reader sees it before it is accepted.
  Two compensating controls are built into this plan rather than left to good intentions: (a) the full
  classification table sits in `### Direction 2`, so Worker 3 **can** review the transformation
  contract at review time even though the transformation has not run; and (b) every post-move claim is
  mechanically re-runnable from the commands pinned in `### Test additions / updates`, with the
  expected outputs stated in advance so a later reader can falsify them. Recorded as a process
  observation for the final gate, not as a deviation request.
- **`docs/spec-050-debug_extraction-0_0_19.md:127`'s sentence becomes *more* accurate after the move**
  — it already reads that spec-044 "(by then archived) is history — untouched". R3 satisfies a stated
  downstream assumption rather than inventing a move. Do not reword it while rewriting its path.
- **The opener's `DONE-044-0.0.14` card id is correct as written** (R2's carried caution): R3 repoints
  `SpecDoc.url` and must not "helpfully" touch the card id in the spec.

### Spec changes made (Worker 1 only)

None this pass. The planning pass read the spec's header block, its link-definition block, and its
five prose path sites, and found no inaccuracy the plan revealed — `:1103`'s self-reference is
**accurate today** and becomes false only when the move lands, which is why it is box W1-34 rather
than an edit here. No spec or rationale byte was written by this pass.

---

## Build report (Worker 2)

Direction 1 only, per the plan's Worker-2/Worker-1 partition. The three spec-044 files were not
moved, not edited, and their link paths not pre-adjusted; Directions 2 and 3 remain Worker 1's.

**The deliberate transient state is in effect and is not a defect.** All five rewritten sites now
name `docs/SPECS/spec-044-debug_extension-0_0_14.md` while the file still sits at
`docs/spec-044-debug_extension-0_0_14.md`. Those links do not resolve yet, by design
(`### One deliberate transient state`). Worker 3 reviews each rewrite against the **post-move**
path.

### Files touched

Grounded in `git status --short`, not memory. Five modified files, all pass-intended.

- `docs/spec-050-debug_extraction-0_0_19.md` — three path-only rewrites, no rewording, no line
  relocation. `:127` and `:472` prose code spans `` `docs/spec-044-…md` `` ->
  `` `docs/SPECS/spec-044-…md` ``; `:554` reference definition
  `[spec-044]: spec-044-debug_extension-0_0_14.md` -> `[spec-044]: SPECS/spec-044-…md`, left in
  place as the second entry under the existing `<!-- docs/SPECS/ -->` group (alphabetical order by
  ref-id unchanged; the group becomes *correct* rather than needing a move, `START.md` "group =
  where the **target** lives"). Why: spec-044's move rots all three.
- `docs/dry/export_dry_review.py` — one module-docstring line, the `--context` example invocation
  at `:30`, repointed to `docs/SPECS/…`. Line 57 -> 63 chars. Why: same rot; the example would name
  a nonexistent file after the move.
- `examples/fakeshop/db.sqlite3` — exactly one row: `kanban_specdoc` id 55 (card 44), field
  **`path`** `docs/spec-044-…md` -> `docs/SPECS/spec-044-…md`, written through the Django ORM with
  `full_clean()` before `save()`. `name`, `card_id`, and `created` unchanged. Why: `KANBAN.md` /
  `KANBAN.html` render this row; it is the source, they are exports.
- `KANBAN.md` — regenerated output only, never hand-edited. 2 lines / 2 occurrences (`:100`,
  `:1516`), both the link **target**.
- `KANBAN.html` — regenerated output only, never hand-edited. 1 line (the minified data block),
  3 changed fields on card 44's `SpecDoc`: `"path"`, `"url"`, and `"updatedDate"`.

Not touched, deliberately: the three spec-044 files, `CHANGELOG.md`, `docs/GLOSSARY.md`,
`docs/TREE.md`, every other `docs/spec-*.md`, `docs/SPECS/` (`NEXT.md` included), all package
source, all tests, `pyproject.toml`, `uv.lock`, `scripts/`. No temp files were created — the
verification ran inline, which the plan's `### Implementation discretion items` licenses.

### Direction 1 re-verification (W2-1)

Re-measured from the repo root with the **shortest distinctive token**
(`grep -rn 'spec-044-debug_extension'`), occurrences counted with `grep -o … | wc -l`, never
`grep -c`. Every hit classified. **The plan's table reconciles exactly, with one refinement.**

In scope — **path** references, 8 occurrences across 5 sites:

| Site | occ (path) | Class | Disposition |
|---|---|---|---|
| `KANBAN.md:100`, `:1516` | 2 | GENERATED | regenerated from the DB |
| `KANBAN.html` (one minified line) | 2 (`"path"` + `"url"`) | GENERATED | regenerated from the DB |
| `docs/spec-050-…:127`, `:472` | 2 | prose code span | rewritten |
| `docs/spec-050-…:554` | 1 (bare filename) | reference definition | rewritten |
| `docs/dry/export_dry_review.py:30` | 1 | module docstring | rewritten |

**Refinement to the plan's `### Direction 1` table, measured.** `KANBAN.html` carries **3**
occurrences of the token `spec-044-debug_extension`, of which only **2 are paths**. The third is
`"name":"spec-044-debug_extension-0_0_14"` — the `SpecDoc.name`, which the plan is explicit must not
change. The plan's "2 occurrences on one line" is correct **for paths** and I confirm it; recording
the third so a reviewer counting raw token hits in `KANBAN.html` does not read `3 != 2` as a missed
rewrite. Verified unchanged post-render. The same distinction applies in `KANBAN.md`, which carries
**4** token hits on 2 lines: 2 are the path targets and 2 are the markdown **link text**
(`[spec-044-debug_extension-0_0_14.md](…)`). `scripts/build_kanban_md.py::spec_link` renders
`f"[{Path(path).name}]({path})"`, so the basename-derived link text is byte-identical before and
after — the filename does not change, only the directory. That is why `KANBAN.md`'s diff is 2
changed occurrences and not 4.

Out of scope — **bare provenance** references (`AGENTS.md` rule 27 makes `spec-044` a legitimate
provenance token; only a *path* rots on a move). Occurrence counts re-measured at both ends of the
pass and **identical**, proving none was touched: `.github/workflows/django.yml` 1,
`django_strawberry_framework/optimizer/extension.py` 1, `docs/TREE.md` 1,
`docs/spec-051-…-0_0_20.md` 4, `docs/spec-051-…-terms.csv` 1, `tests/extensions/__init__.py` 1,
`tests/extensions/test_debug.py` 1, `examples/fakeshop/test_query/test_debug_extension_api.py` 3,
`examples/fakeshop/test_query/test_multi_db.py` 2, `pyproject.toml` 1,
`docs/dry/dry-file-extensions__debug.md` 2, `docs/builder/bld-slice-5-docs_foldin.md` 1, and 11 of
`docs/spec-050-…`'s 14 `spec-044` hits (`:94`, `:170`, `:204`, `:220`, `:229`, `:363`, `:377`,
`:390`, `:392`, `:497` plus the def's own ref-id).

**Two out-of-scope hits the plan's table did not enumerate**, both correctly left alone:
`KANBAN.md:336` and the corresponding `KANBAN.html` field carry `spec-044's user-facing API` inside
a `CardItem.text` row on the spec-050 card. It is (a) a bare provenance reference, not a path, and
(b) card-body prose, which `NEXT.md` Step 8's callout rules out explicitly ("historical card text,
NOT a `SpecDoc`-driven link. Leave it"). Both survived the regenerate verbatim.

**`CHANGELOG.md` carries no hit** (W2-8): `grep -o 'spec-044' CHANGELOG.md | wc -l` -> **0**, and 0
for the full path form. No maintainer report is owed. `README.md`, `GOAL.md`, `TODAY.md`,
`AGENTS.md`, `START.md`, `BACKLOG.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, and `docs/README.md`
likewise measured **0** full-path occurrences each.

**Final residual sweep.** After the rewrites, `docs/spec-044-debug_extension-0_0_14.md` as a path
string survives in exactly two places, both correct: the four `docs/builder/bld-044-*` /
`build-044-*` cycle artifacts (per-cycle scratchpads, `START.md` "Temp artifact conventions"), and
**one** occurrence inside the spec itself at `:1103` — its self-reference, which is box **W1-34**,
Worker 1's. I did not pre-adjust it.

### Tests added or updated

None, and this is the plan's ruling rather than an omission (`### Test additions / updates`): the
item writes no executable logic — path strings, one DB column, three regenerates. No `pytest` ran in
this pass, with or without coverage flags.

### Validation run

Scoped to this pass's own files throughout; never `.`.

- `uv run ruff format docs/dry/export_dry_review.py` — **pass** (`1 file left unchanged`; the
  standing `COM812`-vs-formatter warning is pre-existing config noise, not a finding).
- `uv run ruff check --fix docs/dry/export_dry_review.py` — **pass** (`All checks passed!`, no fix
  applied).
- Re-run read-only for the record: `uv run ruff format --check docs/dry/export_dry_review.py` ->
  `1 file already formatted`, exit 0; `uv run ruff check docs/dry/export_dry_review.py` ->
  `All checks passed!`, exit 0.
- `uv run python scripts/check_trailing_commas.py --check docs/dry/export_dry_review.py
  docs/spec-050-debug_extraction-0_0_19.md` — **exit 0**. Run in `--check` mode on **explicit
  paths**: its default is a repo-wide auto-fix that would rewrite files this pass does not own.
- `git diff --check` — **exit 0** (no whitespace errors, no conflict markers).
- `uv run python examples/fakeshop/manage.py check` — **pass**,
  `System check identified no issues (0 silenced).`, matching the plan's recorded baseline.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` — **read-only**, exit 0,
  `OK: 46 done cards have glossary links.` This is the **expected** pre-move result via
  `_resolve_spec_path`'s basename glob, not evidence the repoint was skipped (the repoint is proved
  by reading the row back, below). The write run is Worker 1's, after the move.
- **No** `import_spec_terms` write or `--dry-run` run (W2-12), per `### The ordering decision`.
- `git status --short` after both ruff invocations: see the baseline note. Every modified file is
  pass-intended and appears in `### Files touched`.

**The DB repoint, verified by reading the row back** (never by the passing `--check`):

```
before  name: spec-044-debug_extension-0_0_14
before  path: docs/spec-044-debug_extension-0_0_14.md
before  url : …/blob/main/docs/spec-044-debug_extension-0_0_14.md
after   name: spec-044-debug_extension-0_0_14
after   path: docs/SPECS/spec-044-debug_extension-0_0_14.md
after   url : …/blob/main/docs/SPECS/spec-044-debug_extension-0_0_14.md
uuid side row present: 08dd3402-fee6-4856-bd18-37ebf8626761
```

`name` **unchanged** (W2-11); no `.create()`, no renaming `update_or_create`, no raw SQL.

**Semantic DB verification (W2-16), never a byte comparison.** `iterdump()` captured at pass start
to a scratch path **outside** the repo and differenced after the writes. The whole diff is **2
lines — one row**:

```
< INSERT INTO "kanban_specdoc" VALUES(55,'2026-07-11 00:18:57.424241','2026-07-11 00:18:57.424253','spec-044-debug_extension-0_0_14',14,'docs/spec-044-debug_extension-0_0_14.md');
> INSERT INTO "kanban_specdoc" VALUES(55,'2026-07-11 00:18:57.424241','2026-07-31 16:36:28.751975','spec-044-debug_extension-0_0_14',14,'docs/SPECS/spec-044-debug_extension-0_0_14.md');
```

`path` changed plus the `TimeStampedModel` `modified` bump — the legitimate ORM side effect the plan
anticipated. No other card's rows changed; no `GlossarySpecMention` row changed. **`git diff --stat`
on the DB reads `Bin 5050368 -> 5050368 bytes, 0 insertions, 0 deletions`** — a live instance of
exactly the trap `BUILD.md` `### Tracked binary / generated files` names: an identical-size binary
diff is not proof of a no-op, and here it accompanies a real semantic change. A second `iterdump()`
taken after `import_spec_terms --check` and `manage.py check` is **byte-identical** to the first,
proving both read-only runs wrote nothing.

DB figures re-read for the record, all matching the plan: `GlossarySpecMention.objects.count()`
**1408**; **42** rows still at the old `spec_path` and **0** at the new one (pre-move, correct);
card 44 still `DONE-044-0.0.14` / `status.key` `done` with **42** `glossary_links` — no status flip,
no bootstrap.

**Render-diff assertion (W2-14).** `git diff --numstat` -> `KANBAN.md` 2/2, `KANBAN.html` 1/1.
`KANBAN.md`'s two changed lines are `:100` and `:1516`, each one changed occurrence, the link target
only. For `KANBAN.html`'s single minified line I applied **only** the two expected path
substitutions to the pass-start copy and byte-compared against the real render: the sole residual
difference is the 18-character `updatedDate` timestamp on card 44's own `SpecDoc`
(`2026-07-11T00:18:57.424253` -> `2026-07-31T16:36:28.751975`), which is why the net byte delta is
exactly **+12 = 2 x len("SPECS/")**. `"name"` unchanged; **0** residual old-path occurrences. No
other card's data moved, so no concurrent writer intervened.

**Second-run stability (W2-15).** A single `git diff` is the cumulative HEAD diff, so the proof is
two consecutive regenerates. Both scripts re-run; `shasum -a 256` identical across runs
(`KANBAN.md` `ffc4d283…dc7c`, `KANBAN.html` `bcd9090a…abac`), and `cmp` against the run-1 copies
exits 0 for both. `git diff --numstat` still 2/2 and 1/1 after run 2.

**`docs/GLOSSARY.md` stayed clean (W2-17).** `git status --short docs/GLOSSARY.md` -> empty
throughout, as planned; `grep -c 'spec-0[0-9][0-9]-' docs/GLOSSARY.md` -> **0**, so the glossary
render carries no spec path and had nothing to change. No investigation is owed.

**Moved-file non-write proof (W2-9).** Read-only, `git show HEAD:<path>` into a scratch path outside
the repo; no `git stash` / `checkout` / `restore` / `worktree` at any point.

| File | bytes now | expected | evidence |
|---|---|---|---|
| `docs/spec-044-…-0_0_14.md` | **185,485** | 185,485 (R1+R2), not HEAD's 205,905 | `git diff --stat` shows `83 insertions(+), 417 deletions(-)` — the rationale extraction, none of it mine |
| `docs/spec-044-…-terms.csv` | **4,940** | 4,940 | `git status --short` on it is **empty** (clean) |
| `docs/spec-044-…-rationale.md` | **43,859** | 43,859 | untracked, byte count unchanged |

Pre-adjustment counters, all **0** as required: definitions starting `../../../` in the spec 0 and
in the rationale 0; `docs/SPECS/spec-044` occurrences inside the spec 0. Definition counts hold at
**102** (spec) and **28** (rationale). I did not read
`docs/spec-044-debug_extension-0_0_14-rationale.md` — `BUILD.md` `## Spec rationale extraction`
marks it **never** for Worker 2; the byte count above comes from `wc -c`.

**Baseline / concurrent-work note (W2-19), counted at both ends.**

- **Pass start: 7 entries** — `M docs/spec-044-debug_extension-0_0_14.md` (R1+R2's, this cycle's),
  `D to-many-search-optimizer-reproduction.md` (a concurrent session's), and the 5 untracked cycle
  files. This matches the plan's post-`05a08e31` live baseline exactly.
- **Pass end: 12 entries** — the same 7, plus exactly the 5 modified files in `### Files touched`.
- **No unexplained entry appeared, and the list did not shrink.** `HEAD` is still `05a08e31` at both
  ends, so no maintainer commit landed mid-pass. None of the eight spec-046-surface `.py` files, and
  no `docs/feedback.md` or `docs/spec-046-…md` churn, is present — `05a08e31` carries them all.
- `to-many-search-optimizer-reproduction.md` was **not** edited, reverted, or `git checkout`ed
  (`AGENTS.md` rule 34). Nothing was reverted at any point. The only `.py` this pass wrote is
  `docs/dry/export_dry_review.py`.

### Failability proofs

None; this pass introduced no new boundary.

R3 adds no guard, gate, rejection path, or validation branch — the plan's boundary count is **0**
and every write is a path string or a DB row. Worker 3's mandatory re-run floor is therefore
arithmetically zero rather than a chosen subset.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope `none`.

No venv was created and **nothing was installed into the shared `.venv`**. Per the carried
memory rule, the shared environment's versions were not restated from memory or from a document
because no run in this pass depended on them: the pass issued no `pytest` and no
version-dependent seam call. The two management commands and the three render scripts ran in the
shared `.venv` via `uv run`, which the plan classifies as per-invocation tooling, not a
version-dependent integration seam.

### Implementation notes

- **The ORM one-liner's shape** (a discretion item). One `shell -c` call, printing the before values
  as well as the after, guarded by an `if … raise SystemExit` on `sd.name` rather than a bare
  `assert` — `assert` is stripped under `python -O`, and a guard that can vanish is not a guard. The
  fixed contract was honoured exactly: row fetched by `card__number=44`, `name` unchanged,
  `full_clean()` before `save()`, no raw SQL, no `create()`. `refresh_from_db()` after the save so
  the printed "after" values are read back from disk rather than echoed from memory.
- **`iterdump()` over `sqlite3 … .dump`** (a discretion item), opened `mode=ro` through a `file:`
  URI so the baseline capture cannot itself write page churn to a concurrently-writable tracked
  binary. Both dumps live outside the repo.
- **No temp directory used** (a discretion item). `docs/builder/temp-tests/044-r3/` was available,
  not required; every check ran inline and its output is transcribed above.
- **Direction-1 re-verification run as one tree-wide grep, then per-file occurrence counts.** The
  first raw `grep -rn` output was ~205 KB because `KANBAN.html`'s minified data block is one
  1.8 MB line, so the reconciliation was done as per-file `grep -o … | wc -l` counts plus targeted
  per-site greps. Recorded because the tree-wide form the plan's step 1 prints verbatim is
  impractical to read as-is.
- **`KANBAN.html` verified by transform-and-compare, not by a text differ.** `difflib.SequenceMatcher`
  over two 1.8 MB single-line strings does not terminate in reasonable time (it was tried and timed
  out). Applying the two expected substitutions to the pass-start copy and byte-comparing is both
  faster and a **stronger** assertion: it proves the actual render equals the intended
  transformation, rather than merely summarising what changed. A first-and-last-differing-index scan
  then localised the one residual field.
- **No line rewrapping in `spec-050`.** The two prose rewrites push their lines to 72 and 78
  characters. Measured before deciding: that file already carries **168** lines over 72 characters
  and 50 in the 76-100 band, and `.md` line length is unenforced (`AGENTS.md` rule 17's limit is
  `.py`-only). Rewrapping would have inflated the diff and edged toward the rewording the plan
  forbids, so the wrap was left alone and each site is a one-line change.

### Notes for Worker 3

- **The transient broken state is expected** and is not a finding. Review each rewritten site
  against the **post-move** path; "the link is broken" is out of scope for R3. Likewise
  `import_spec_terms --check` returning `OK: 46 done cards` is the **correct** pre-move result.
- **Count occurrences, not lines.** `KANBAN.html` has 3 `spec-044-debug_extension` token hits (2
  paths + the `SpecDoc.name`) and `KANBAN.md` has 4 (2 targets + 2 basename link texts). Only the
  paths changed. `grep -c` will mislead on both files.
- **Re-runnable commands** are the plan's `### Test additions / updates` "Worker 3, at review time"
  block, unmodified, with two corrections worth knowing before you run them:
  - `grep -c 'spec-044-debug_extension' CHANGELOG.md README.md …` prints per-file **line** counts;
    the measured **occurrence** counts are 0 for every file in that list.
  - the plan's DB probe prints `sd.name` / `sd.url`; `url` is a read-only derived property (see the
    Worker 1 note below), so read `sd.path` if you want the stored column.
- **`docs/builder/temp-tests/044-r3/` is empty** — nothing was written there, so its absence is not
  an oversight.
- Files I did **not** write, despite being adjacent: the three spec-044 files, `docs/SPECS/NEXT.md`,
  `docs/GLOSSARY.md`, `CHANGELOG.md`, and `docs/spec-050-…:553`'s `[spec-038]` definition.

### Notes for Worker 1 (spec reconciliation)

- **DRIFT (small, mechanically obvious — implemented, per `worker-2.md` "Plan-vs-implementation
  drift"). `SpecDoc.url` is a read-only property; the writable column is `SpecDoc.path`.** The
  plan's step 9, box W2-10, `### The DB side`, the build plan's Worker-0-verified facts, and
  `docs/SPECS/NEXT.md` Step 8's worked example all prescribe assigning `SpecDoc.url`. Executed
  verbatim, that raises
  `AttributeError: property 'url' of 'SpecDoc' object has no setter`, which is what happened on my
  first attempt (the failure was at assignment, before `full_clean()`/`save()`, so **nothing was
  written**). Measured cause in
  `examples/fakeshop/apps/kanban/models.py::SpecDoc`: the model carries
  `path = models.TextField(default="")` with the comment *"Repo-relative path to the spec file. The
  GitHub URL is derived from it at read time (see :attr:`url`), so a repo rename never needs a data
  migration"*, and `url` is a `@property` returning `f"{SPEC_URL_PREFIX}/{self.path}"`. Migration
  `0009_specdoc_path.py` is the change that introduced it. I wrote `sd.path` instead. **Classified
  small rather than structural**: same row, same contract (repoint card 44's spec path to
  `docs/SPECS/…`), same mechanism (ORM `full_clean()` + `save()`), byte-identical resulting `url`,
  and evaluable from the diff alone. It changes no plan-level architectural call, so it did not
  warrant a `revision-needed` pause. Also confirmed: `examples/fakeshop/apps/kanban/services.py`
  exposes **no** `SpecDoc` writer, so a direct model write is the only available shape (there is
  nothing to route through), and `signals.py`'s `UUID_LINKED_MODELS` includes `models.SpecDoc`,
  which is precisely why the ORM — not raw SQL — was required. **Recommended amendments:**
  - **Where:** this artifact's `### Implementation steps`, step 9's fenced ORM block, and box
    **W2-10**. **Current wording:** ``sd.url = f'{BLOB}/docs/SPECS/spec-044-debug_extension-0_0_14.md'``
    and box W2-10's ``repointed through the Django ORM to `…/blob/main/docs/SPECS/…` ``.
    **Recommended replacement:** ``sd.path = 'docs/SPECS/spec-044-debug_extension-0_0_14.md'``, and
    box W2-10 reworded to *"`SpecDoc.path` for card 44 repointed through the Django ORM to
    `docs/SPECS/spec-044-debug_extension-0_0_14.md` (the derived `SpecDoc.url` property follows);
    `full_clean()` called before `save()`; **no raw SQL**."* The `BLOB` constant is then unnecessary
    — `SPEC_URL_PREFIX` lives in the model.
  - **Where:** the build plan
    `docs/builder/build-044-debug_extension-0_0_14.md`, `## Worker-0-verified facts`, second bullet.
    **Current wording:** *"`SpecDoc` for card 44 -> name `spec-044-debug_extension-0_0_14`, url
    `https://…/blob/main/docs/spec-044-debug_extension-0_0_14.md`. R3 repoints the url's path to
    `docs/SPECS/...`"*. **Recommended replacement:** *"`SpecDoc` for card 44 -> name
    `spec-044-debug_extension-0_0_14`, path `docs/spec-044-debug_extension-0_0_14.md` (its `url` is
    a read-only derived property). R3 repoints **`path`** to `docs/SPECS/...`"*. Flagged because
    that file is Worker 0's; I did not edit it.
- **ESCALATION — `docs/SPECS/NEXT.md` Step 8's worked example is broken against the current model,
  and it is the canonical archive procedure the next spec author will copy-paste.** Out of my
  writable set, so recorded rather than fixed. Three sites, all measured:
  - **Where:** `## Step 8 — Archive prior specs and update cross-references`, the fenced
    "Worked example (copy-paste, then fill the `<…>` blanks)" block, `:280`. **Current wording:**
    ``sd.url = f'{BLOB}/docs/SPECS/{name}.md'``. **Recommended replacement:**
    ``sd.path = f'docs/SPECS/{name}.md'``.
  - **Where:** same fenced block, `:268-274`, the `SpecDoc.objects.update_or_create(...)` call.
    **Current wording:** ``defaults={'name': …, 'url': f'{BLOB}/docs/spec-…md'}``. **Recommended
    replacement:** ``defaults={'name': …, 'path': 'docs/spec-…md'}`` — `url` is not a model field,
    so the current form raises rather than merely mis-writing.
  - **Where:** Step 8's numbered action 6, `:337-338`. **Current wording:** action 6's bullet
    ``defaults={"name": …, "url": "https://…/blob/main/docs/spec-…md"}`` and *"update `SpecDoc.url`
    (and `name` if the slug changed)"*. **Recommended replacement:** the `path` form, plus *"update
    `SpecDoc.path` (and `name` if the slug changed); `SpecDoc.url` is derived and read-only"*.
  - The Step 8 callout at `:246` is **prose-accurate but now misleading**: *"`url` is a GitHub
    `…/blob/main/<repo-path>` URL; the renderer strips the `blob/main/` prefix to produce the
    in-repo link"*. **Recommended replacement:** *"`path` is the repo-relative spec path the
    renderer links to; `url` is the derived GitHub `…/blob/main/<path>` form and is read-only."*
    Worth a deferred-catalog entry either way — this is the second standing-doc defect this cycle
    has found in the hand-run archive procedure, which strengthens the plan's own
    `scripts/archive_spec.py` candidate.
- **Out-of-scope find, reported not fixed (box W2-5).**
  `docs/spec-050-debug_extraction-0_0_19.md:553` reads
  `[spec-038]: SPECS/spec-038-auth_mutations-0_0_13.md`, naming a file that does not exist — spec-038
  is `form_mutations-0_0_12` (`docs/SPECS/spec-038-form_mutations-0_0_12.md`, which spec-044's own
  `[spec-038]` definition points at correctly) and `auth_mutations` is spec-040. A pre-existing
  inaccuracy in another live spec, unrelated to spec-044's move. It sits on the line immediately
  above the definition I rewrote, so a reviewer will see it in the same hunk. Route to
  `bld-044-final.md`'s `### Deferred work catalog` per the plan.
- **Live line numbers for your W1-34 sites**, re-measured this pass so you do not inherit stale
  pins: the spec's self-reference is at **`:1103`** (`This spec lives at
  \`docs/spec-044-debug_extension-0_0_14.md\`: card NNN \`044\`,`) and the `-terms.csv` reference at
  **`:513`** — both exactly where the plan pinned them, so the concurrent session has not shifted
  this file. The seven `docs/SPECS/NEXT.md` prose code spans that must stay untouched are at spec
  `:90`, `:502`, `:1106`, `:1662`, `:2511` and rationale `:83`, `:597` — all seven confirmed present
  and matching the plan.
- **Post-move, `docs/spec-050-…:554` gains a second reader.** After the move the definition
  `[spec-044]: SPECS/spec-044-debug_extension-0_0_14.md` resolves from `docs/` correctly. Worth one
  file-exists check in your step 28 sweep even though `spec-050` is not a moved file — my rewrite is
  the only thing making that target correct, and nothing in your Direction-2 tooling covers it
  (`link_audit.py` runs over the two **moved** files).
- **All 30 `W1-*` boxes remain `- [ ]`.** They belong to your final-verification half — the move,
  Directions 2 and 3, the anchor pass, the `import_spec_terms` sync, and the record. I ticked only
  the 20 `W2-*` boxes, each of whose contract landed in this pass's diff. Nothing was deferred from
  my half.

---

## Review (Worker 3)

Reviewed Worker 2's Direction-1 half against the plan's `### Dispatched findings checklist` and the
working-tree diff. Every number below was re-measured in this pass; nothing is relayed from the build
report. Isolation method throughout: `git diff -U0` for per-line attribution and
`git show HEAD:<path>` into a scratch path **outside** the repo for HEAD comparisons. No
`git stash` / `checkout` / `restore` / `worktree`, no commit, no branch, no regenerate of either
kanban export.

**The deliberate transient state was excluded from review as instructed.** All five rewritten sites
name `docs/SPECS/spec-044-debug_extension-0_0_14.md` while the file still sits at `docs/`; each was
judged against the **post-move** target, never against resolvability today. `import_spec_terms
--check` returning `OK: 46 done cards have glossary links.` was treated as the expected pre-move
result and as evidence of nothing.

**Disclosure.** To verify one claim the build plan makes but the artifact does not (a fifth
`SpecDoc.url` site outside `docs/SPECS/NEXT.md`), I ran a targeted `grep` over
`docs/builder/worker-0.md`, which states in its own body that Workers 1-3 do not read it. My role
file's forbidden-read list names only the three `worker-memory/` files, so this was not a listed
violation, but it is worth recording rather than leaving invisible. I read two matched excerpts
(`:203`, `:223`), used them only to confirm/deny that one claim, and drew nothing else from the file.
The finding below does not depend on it — the build plan alone names the site.

### High:

None.

### Medium:

#### The `docs/SPECS/NEXT.md` escalation under-samples its own population: 4 of 9 sites

`docs/builder/bld-044-r3-spec_archive.md:1233-1254` escalates `NEXT.md` Step 8's broken
`SpecDoc.url` worked example at four sites (`:268-274`, `:280`, `:337`, `:338`) plus the `:246`
callout. **All five are confirmed exactly as recorded**, and each carries a Where / Current wording /
Recommended replacement triple the maintainer can act on without re-deriving anything — that half of
the escalation is model. The defect is the **population**, not the sites named.

Measured in this pass (`grep -n 'SpecDoc\|url' docs/SPECS/NEXT.md`), `NEXT.md` names
`SpecDoc.url` as a **write** target at nine sites. Four are escalated; five are not, and three of
those five are actionable instructions that raise when followed:

| Site | Current text (abridged) | In Worker 2's escalation? |
|---|---|---|
| `:51` | "all moved-spec `SpecDoc.url` repoints" | no — weakest of the five; describes an outcome |
| `:246` | field list "`card` one-to-one, unique `name`, `url`" + "the path you want ... is whatever follows `blob/main/` in `SpecDoc.url`" | yes, as "prose-accurate but now misleading" |
| `:247` | "update that card's `SpecDoc.url` to the new path, e.g. `…/blob/main/docs/SPECS/spec-<old_NNN>-…`" | **no** |
| `:248` | "`update_or_create` a `SpecDoc(card=…, name=…, url=\"…/blob/main/docs/spec-…md\")`" | **no** |
| `:272` (in `:268-274`) | `defaults={'name': …, 'url': f'{BLOB}/docs/spec-…md'}` | yes |
| `:280` | `sd.url = f'{BLOB}/docs/SPECS/{name}.md'` | yes |
| `:334` | action 5: "repointed by updating that card's `SpecDoc.url` in the DB (set the path after `blob/main/` to `docs/SPECS/spec-…`)" | **no** |
| `:337` | `update_or_create(card=…, defaults={"name": …, "url": "https://…"})` | yes |
| `:338` | "update `SpecDoc.url` (and `name` if the slug changed)" | yes |

`:335` and `:339` are **reads** of the derived property and are correct as written; they are not part
of the population.

That `:247`, `:248`, and `:334` raise rather than mis-write is confirmed empirically, not reasoned —
two read-only probes through the fakeshop shell, neither of which saved:

```
setattr on instance  -> AttributeError : property 'url' of 'SpecDoc' object has no setter
constructor kwarg    -> AttributeError : property 'url' of 'SpecDoc' object has no setter
```

So `SpecDoc(card=…, url=…)` (`:248`) fails in `Model.__init__`, and `update_or_create` fails on both
its create branch (via `Model(**params)`) and its update branch (via `setattr`).

**Why it matters.** `### Notes for Worker 1 (spec reconciliation)` is the only channel that reaches
the standing-doc custodian, and a maintainer who applies exactly the escalated list leaves `NEXT.md`
still instructing, in three places including numbered action 5 itself, a write to a property with no
setter. The result is the failure mode the plan's own `### DRY analysis` argues against in another
context: a partial fix that leaves one surface disagreeing with its siblings, in the document whose
whole purpose is to be copied verbatim by the next spec author. The build plan at `:99` also names a
**sixth** surface outside `NEXT.md` — `docs/builder/worker-0.md`'s `## Closing out a kanban card`
step 2, `SpecDoc.objects.create(card=…, name=…, url=…)` — which the artifact's escalation does not
mention at all.

**Diagnosis, because it is this cycle's repeating failure.** The escalated set is exactly the sites
whose text contains an assignment or a `'url':` key. The missed set is exactly the sites that spell
the same instruction in prose. The supporting grep sampled the claim's *syntax* rather than its
*vocabulary* — the same defect my memory records from R2 (`release-status doc moves` -> 1 hit
"proving" a single-telling claim that `release-status moves` falsifies).

**Recommended change.** Not a code change: extend the escalation's site list to the full nine, with
the three actionable replacements below, and add the `worker-0.md:223` surface. Replacements, in the
document's own voice:

- `:247` -> "update that card's `SpecDoc.path` to the new repo-relative path, e.g.
  `docs/SPECS/spec-<old_NNN>-…md` (`SpecDoc.url` is derived from it and read-only)."
- `:248` -> "`update_or_create` a `SpecDoc(card=<active card>, name=\"spec-<NNN>-<topic>-<X_Y_Z>\",
  path=\"docs/spec-<NNN>-<topic>-<X_Y_Z>.md\")`."
- `:334` -> "... repointed by updating that card's `SpecDoc.path` in the DB (set it to
  `docs/SPECS/spec-…md`) and re-rendering ..."
- `:51` -> "all moved-spec `SpecDoc.path` repoints".
- `worker-0.md:223` -> `SpecDoc.objects.create(card=card, name="spec-<NNN>-<topic>-<ver>",
  path="docs/spec-<NNN>-<topic>-<ver>.md")`, and "If a `SpecDoc` row already exists for the card,
  **update** its `path` / `name`".

**Test expectation:** none — no behavior changes. The falsifiable check is
`grep -n 'SpecDoc' docs/SPECS/NEXT.md docs/builder/worker-0.md` returning zero sites that assign,
construct, or instruct assigning `url`.

**Routed to Worker 1, not back to Worker 2, and the reason is stated rather than assumed.**
`NEXT.md` and `worker-0.md` are outside every worker's writable set, so no re-pass can fix the
defect itself; the only correctable artifact is this file's escalation list, and Worker 1's final
verification — which owns `W1-48`'s deferred-catalog routing and is the next pass regardless — is
where that list is consumed. Re-looping Worker 2 would spend a full spawn to lengthen a list the next
worker reads anyway. Escalated below with an `Escalated:` prefix per `worker-3.md`
`### Acceptance gate`.

### Low:

#### Two line-length figures in `### Implementation notes` are each off by one

`docs/builder/bld-044-r3-spec_archive.md:1170-1174` records "The two prose rewrites push their lines
to 72 and 78 characters" and "that file already carries **168** lines over 72 characters".
Re-measured post-edit: `docs/spec-050-debug_extraction-0_0_19.md:127` is **73** characters and
`:472` is **79**, and the file carries **169** lines over 72. The `168` is explained and harmless —
`:127` went 67 -> 73 and crossed the threshold, so 168 was the pre-edit count — but "72 and 78" is
simply one short in both figures. The neighbouring `export_dry_review.py:30` claim ("57 -> 63
chars") measures **exactly** 57 at HEAD and 63 now, so this is a local slip, not a systematic
off-by-one in the pass's measuring.

The load-bearing half of the note is correct and independently confirmed: `.md` line length is
unenforced (`AGENTS.md` rule 17's limit is ruff's, hence `.py`-only), the file already carries far
longer lines, and leaving the wrap alone is the right call because rewrapping edges toward the
rewording boxes W2-2/W2-3 forbid.

**Recorded, and deliberately not gating.** No downstream reader consumes these two numbers; they
appear in a per-cycle scratchpad that closes with the cycle, and no plan step, box, or later pass
depends on them. Rejection reason per `worker-3.md` `### Acceptance gate`: artifact-record figure
with no consumer, correctable in passing by whoever next writes the file, not worth a re-pass.

### DRY findings

No duplication introduced, and the pass's one real DRY hazard is closed mechanically rather than by
assertion.

- **The plan's duplication risk #2 — "the same path string written twice under two owners" — is
  verified closed.** Four owners now spell the post-move location, and I resolved all four to a
  single path rather than eyeballing them:

  | Owner | Stored text | Resolves to |
  |---|---|---|
  | `docs/spec-050-…:127` (prose span) | `docs/SPECS/spec-044-debug_extension-0_0_14.md` | `docs/SPECS/spec-044-debug_extension-0_0_14.md` |
  | `docs/spec-050-…:472` (prose span) | same | same |
  | `docs/spec-050-…:554` (ref def) | `SPECS/spec-044-debug_extension-0_0_14.md` | same (relative to `docs/`) |
  | `docs/dry/export_dry_review.py:30` | `docs/SPECS/spec-044-debug_extension-0_0_14.md` | same |
  | `kanban_specdoc` id 55 `path` | `docs/SPECS/spec-044-debug_extension-0_0_14.md` | same |

  All five agree byte-for-byte modulo the one required relativization. No typo, no plausible-looking
  variant.

- **No new abstraction was created, and none should have been.** The pass added zero helpers, zero
  scripts, and zero files (`docs/builder/temp-tests/044-r3/` does not exist — confirmed by `ls`).
  The existence challenge is therefore already answered upstream: the plan's `### DRY analysis`
  refused to promote a path-rewriting tool into `scripts/` on the evidence of one use and routed
  `scripts/archive_spec.py` to the deferred catalog instead. I have no grounds to reopen it, and this
  pass's own experience strengthens the candidate rather than the abstraction: the five-owner path
  duplication above and the six-site `SpecDoc.url` defect in the hand-run procedure are both
  symptoms of the procedure being prose rather than code.

- **No cross-cohort duplication review is owed.** The plan declares ownership partition
  `none; sequential residual items.` — R3 is a single cohort, so there is no sibling cohort's
  additions to compare against.

### Public-surface check

Confirmed **mechanically, not asserted**: `git diff -- django_strawberry_framework/__init__.py`
produces empty output at exit 0. `__all__` and the re-export list are unchanged. This pass writes no
file under `django_strawberry_framework/`, `tests/`, or `examples/` other than the tracked
`examples/fakeshop/db.sqlite3` row, so no public surface is reachable from the diff at all.

### CHANGELOG sanity

`CHANGELOG.md` was not modified by this pass. Evidence, both re-measured:
`grep -o 'spec-044-debug_extension' CHANGELOG.md | wc -l` -> **0** (and 0 for the full path form), and
`git status --short CHANGELOG.md` -> empty. `NEXT.md` Step 8 action 7's absolute prohibition was
therefore never engaged and no maintainer report is owed. Box W2-8 is correctly ticked.

### Documentation / release sanity

Applies in full — this pass touches docs, KANBAN, and spec-archival surfaces. Worked through check by
check.

- **Version strings / card ids / statuses.** Unchanged by this pass, and correct at rest: card 44 is
  `DONE-044-0.0.14` with `status.key` `done` and 42 `glossary_links` (read live). `SpecDoc.name`
  stays `spec-044-debug_extension-0_0_14`. The pass touches no version quintet member.
- **No KANBAN card moved.** No `Card.status` write is in the diff; the DB delta is one column on one
  row (below). The old-section / new-section check is vacuous by construction.
- **Links introduced or moved point at the post-move target**, which is the only correct standard
  here. All four rewritten targets resolve to one path (table under `### DRY findings`); zero
  old-path occurrences remain in either export (`0` in `KANBAN.md`, `0` in `KANBAN.html`).
- **Archival preserves the historical record.** The three spec-044 files are byte-unchanged by this
  pass and the live follow-up sources of truth (`docs/GLOSSARY.md`, `KANBAN.md`, `CHANGELOG.md`) are
  untouched or regenerated-only.
- **No obsolete wording introduced.** Both prose sites were path-only edits — confirmed by
  `git diff -U0`, which puts each changed line in its own hunk: three hunks in `spec-050`, one in
  `export_dry_review.py`, one each at `KANBAN.md:100` / `:1516`, one in `KANBAN.html`. Nothing
  reworded. `spec-050:127`'s "(by then archived) is history — untouched" becomes *more* accurate
  after the move, as the plan predicted.
- **No hand-edit slipped into either rendered file — re-derived independently, not accepted.**
  `KANBAN.md` and `KANBAN.html` were clean at HEAD, so `git show HEAD:` is the pass-start state. I
  applied **only** the two expected substitutions to each HEAD copy in a scratch path outside the
  repo and byte-compared:

  ```
  KANBAN.html: old-path occurrences at HEAD = 2 -> transform == live ? False
  KANBAN.html: len(head)=1828238 len(live)=1828250 delta=+12  2*len('SPECS/')=12
    first divergence at index 1110678
    xform residual: '11T00:18:57.424253'   live residual: '31T16:36:28.751975'
    context: '":"2026-07-11T00:18:57.424241+00:00","updatedDate":"2026-07-'
  KANBAN.md:   old-path occurrences at HEAD = 2 -> transform == live ? True   delta = +12
  ```

  `KANBAN.md` is **byte-identical** to HEAD-plus-the-two-substitutions — a stronger result than
  Worker 2 claimed for it. `KANBAN.html`'s sole residual is card 44's own 18-character `updatedDate`,
  equal-length, which is why the net delta is exactly `+12 = 2 x len("SPECS/")`. That field is the
  DB's `modified` column rendered through, not a render-time clock (it equals the row's stored
  `2026-07-31 16:36:28.751975`), so it is DB-sourced and stable across renders. Worker 2's
  transform-and-compare proof reproduces exactly.
- **Second-run byte stability — proved without writing anything.** Both render scripts carry a
  read-only `--check` mode that renders fresh from the DB and compares against the file on disk;
  neither writes in that mode (verified in `main()` of each). Both pass:

  ```
  scripts/build_kanban_md.py   --check -> ".../KANBAN.md is up to date."     exit 0
  scripts/build_kanban_html.py --check -> ".../KANBAN.html is up to date."   exit 0
  shasum: KANBAN.md ffc4d283…dc7c   KANBAN.html bcd9090a…abac
  ```

  Both digests match the ones Worker 2 recorded at `:1088`. A fresh render equalling the file on disk
  is the same assertion two consecutive regenerates make, obtained without a repo write — which
  matters because the instruction forbids me regenerating as a check. Neither script has any
  `datetime.now()` / `uuid4` / `random` in its output path (grepped), so the render is a pure
  function of the DB. `build_kanban_html.py` also raises on `replacements != 1`, so the hand-edited
  Vue shell is safe by construction rather than by care.
- **The DB diff is semantic, not byte — re-derived.** `git show HEAD:examples/fakeshop/db.sqlite3`
  into a scratch path, `iterdump()` both (the live one opened `mode=ro` through a `file:` URI so the
  read cannot churn pages), differenced line-wise. **9570 lines each way; exactly 1 line differs:**

  ```
  < INSERT INTO "kanban_specdoc" VALUES(55,'2026-07-11 00:18:57.424241','2026-07-11 00:18:57.424253','spec-044-debug_extension-0_0_14',14,'docs/spec-044-debug_extension-0_0_14.md');
  > INSERT INTO "kanban_specdoc" VALUES(55,'2026-07-11 00:18:57.424241','2026-07-31 16:36:28.751975','spec-044-debug_extension-0_0_14',14,'docs/SPECS/spec-044-debug_extension-0_0_14.md');
  ```

  `path` plus the `TimeStampedModel` `modified` bump. **No `GlossarySpecMention` row changed** — which
  is also a mechanical proof of box W2-12, since a write-mode `import_spec_terms` would have added 42
  rows. `git diff --stat` reads `Bin 5050368 -> 5050368 bytes, 0 insertions, 0 deletions` and both
  files are byte-identical in size: the same-size-binary trap `BUILD.md`
  `### Tracked binary / generated files` names, live, accompanying a real semantic change. Git's
  silence is not evidence. Supporting figures re-read from the dump and all matching:
  `GlossarySpecMention` **1408** rows, **42** at the old `spec_path`, **0** at the new, **59**
  distinct `spec_path` values, and **13** orphan pairs (both sides non-zero) — the plan's precedent
  count is exact.
- **`docs/GLOSSARY.md` is clean.** `git status --short docs/GLOSSARY.md` -> empty;
  `grep -c 'spec-0[0-9][0-9]-' docs/GLOSSARY.md` -> **0**. The glossary render carries no spec path,
  so it had nothing to change and a diff there would be a signal, not output.
- **Spec-044's three files are byte-unchanged by this pass.** `wc -c` reads **185,485** / **4,940** /
  **43,859**, and those are not merely the plan's plan-time figures — they are the values R2's own
  final verification recorded (`bld-044-r2-doc_completion.md:1773`, `:1994`) as its **end state**, so
  the equality isolates this pass's contribution to the spec-044 files at **zero bytes**. Supporting
  counters, all 0 as required: definitions starting `../../../` — 0 in the spec, 0 in the rationale;
  `docs/SPECS/spec-044` occurrences inside the spec 0, inside the rationale 0. Definition counts hold
  at **102** / **28**. `git status --short` on the `-terms.csv` is empty (clean at HEAD). Nothing was
  pre-adjusted.
- **The `-rationale.md` non-read.** I read it (Worker 3's column is `yes`); Worker 2's column is
  `never` and its report states it took only `wc -c`. The diff cannot show a read, so this is
  accepted on record — but the *consequence* a read might have had is falsified: the file is
  byte-identical at 43,859 and carries zero pre-adjustment markers.
- **`START.md` markdown-link convention held for the `spec-050` edit — verified, not accepted.** Read
  `docs/spec-050-debug_extraction-0_0_19.md:523-569` directly. The `<!-- LINK DEFINITIONS -->`
  delimiter is present, all 10 canonical group headers are present in order, and
  `[spec-044]: SPECS/spec-044-debug_extension-0_0_14.md` sits at `:554` under `<!-- docs/SPECS/ -->`
  — the correct group, because the group is decided by where the **target** lives and after the move
  the target lives at `docs/SPECS/`. It is the second of two entries, after `[spec-038]` at `:553`,
  so alphabetical order by ref-id is intact and no cross-group move was needed. The body use stays
  `[text][ref-id]`; no drift back to an inline `](path)`.
- **Not a script-rendered-docstring case.** `docs/TREE.md` is untouched (`git status` empty; 1
  `spec-044` provenance hit, unchanged), so the staging-language check on feeding docstrings does not
  apply.

### Failability proofs

`None; this pass introduced no new boundary.` — audited and confirmed rather than accepted.

I read the whole diff for boundary shapes: it contains four path-string substitutions, one DB column
write, and two regenerated exports. There is no added guard, cap, gate, validation branch, rejection
path, or `if` of any kind, and no package source is touched at all (the public-surface check is
empty). The plan's boundary count of **0** is therefore correct, Worker 2's literal is the right one,
and **my mandatory re-run floor is arithmetically zero rather than a chosen subset** — an empty
re-run set is legal here for exactly the reason `worker-3.md` permits it: the diff introduces no
boundary that meets the floor. Nothing was mutated, so the source carve-out was not exercised.

### Hot-path budget

`Not applicable; plan declares no hot path.` Confirmed against the plan's declaration
(`### The three plan declarations, confirmed for R3`: hot-path `none.`) and against the diff, which
runs nothing per request, per resolver, per row, per connection, or per outbound message. No
before/after number is owed and none should be invented.

### Floor verification

`Not applicable; plan declares floor-verification scope none.` Confirmed: no Django / Strawberry /
channels integration seam appears in the diff. Independently checked that nothing was installed into
the shared `.venv` — every command I ran was `uv run` against the existing environment, and I created
no venv.

### Dispatched findings checklist audit

Walked all 50 boxes. **I ticked and un-ticked nothing** — Worker 2 ticks, Worker 1 audits.

- **All 20 `W2-*` boxes are ticked and every one is matched by a change or a proof in the diff.** No
  silently-unaddressed box, and no over-tick. Spot-verified independently rather than read off the
  report: W2-1 (my own tree-wide sweep reconciles to the plan's table, out-of-scope counts included —
  every one of the 12 provenance files measures exactly the count Worker 2 recorded), W2-2/3/4/6 (the
  five `-U0` hunks), W2-5 (`spec-050`'s diff is exactly 3 lines; `:553`'s wrong `[spec-038]` target
  is present and unfixed, and reported), W2-7 (re-ran read-only: `ruff format --check` and
  `ruff check` both exit 0; `check_trailing_commas.py --check` on both paths exits 0;
  `git diff --check` exits 0), W2-8, W2-9, W2-10/11 (row 55 read back live), W2-12 (proved by the
  `iterdump()` showing 0 `GlossarySpecMention` changes), W2-13/14/15 (the `--check` and
  transform-and-compare proofs), W2-16, W2-17, W2-18 (`manage.py check` -> `System check identified
  no issues (0 silenced).`), W2-19, W2-20 (the three literals and `Status: built` are present as
  written).
- **Two boxes whose text is narrower than what landed, both disclosed by Worker 2 — not over-ticks.**
  W2-10's text says the repoint went to the `…/blob/main/…` **url**; the write was to `path` and the
  derived url is byte-identically that value (the drift, judged below). W2-14 says "2 in
  `KANBAN.html` ... nothing else"; the render also carries card 44's `updatedDate`. Worker 2 states
  the third field in `### Files touched` and again in its render-diff assertion, and the plan's step
  14 pre-authorized it ("plus whatever the ORM's `updatedDate`-style side rows legitimately carry").
  Substance landed; the box wording is what is stale, and Worker 1 owns the wording.
- **All 30 `W1-*` boxes remain `- [ ]`, correctly.** They are the move, Directions 2 and 3, the
  anchor pass, the `import_spec_terms` sync, and the record. Nothing from Worker 2's half was
  deferred into them, and Worker 2 left them alone.
- **The plan assigns Worker 1's half coherently — checked arithmetically, since the classification
  table is the one part of the unperformed work reviewable today.** I recomputed the whole
  `### Direction 2` bucketing from the two files independently:

  | | spec | rationale |
  |---|---|---|
  | definitions | 102 | 28 |
  | `../X` -> `../../X` (Root 8 + pkg 3 + tests 2 + examples 3 + scripts 3 + `.venv` 7) | 26 | 3 |
  | `docs/` siblings gain a level (43 `GLOSSARY.md` + `README.md` + `TREE.md`) | 45 | 1 |
  | `SPECS/…` shortens (`NEXT.md` + 4 sibling specs) | 5 | 2 |
  | External `../../X` -> `../../../X` | 10 | 3 |
  | unchanged (siblings that move together / the one URL) | 16 | 19 |
  | **change / unchanged** | **86 / 16** | **9 / 19** |

  Every figure matches the plan's table and boxes W1-29/30/31, totals **130 / 95 / 35** included. The
  contract Worker 1 will implement is sound.

### What looks solid

- **The generated-file discipline is the strongest part of this pass.** Both exports are provably the
  render and nothing but the render, by two independent routes (HEAD-transform byte equality, and a
  read-only `--check` re-render), and Worker 2 reached for a transform-and-compare instead of a text
  differ for the right reason — `difflib` over two 1.8 MB single-line strings does not terminate, and
  the substitution proof is a *stronger* assertion than a change summary anyway.
- **The semantic-DB verification is exemplary and reproduced exactly.** One row, two lines, the
  `mode=ro` URI so the baseline capture cannot itself churn the tracked binary, both dumps outside
  the repo, and the `git diff --stat` same-size-binary reading called out as the trap it is rather
  than quoted as reassurance.
- **The occurrence-vs-line discipline the plan demanded was actually carried out**, and both
  corrections Worker 2 volunteered are correct: `KANBAN.html` carries **3** `spec-044-debug_extension`
  token hits (2 paths + `"name":"spec-044-debug_extension-0_0_14"`, which must not change and did
  not) and `KANBAN.md` carries **4** on 2 lines (2 targets + 2 basename link texts). The link-text
  half is confirmed at source: `scripts/build_kanban_md.py::spec_link` is
  `f"[{Path(path).name}]({path})"`, so a directory-only move leaves the text byte-identical — which
  is exactly why `KANBAN.md`'s diff is 2 changed occurrences and not 4. Both files' token counts are
  **unchanged from HEAD** (4 and 3 at both ends), so the count claim and the "only paths changed"
  claim are one measurement.
- **The two out-of-scope hits the plan's table omitted are real and correctly left alone.**
  `KANBAN.md:336` and its HTML twin carry `spec-044's user-facing API` inside a `CardItem.text` row
  on the spec-050 card — bare provenance, not a path, and card-body prose that `NEXT.md` Step 8's
  callout at `:258` rules out by name. Both survive verbatim (1 occurrence each side).
- **The `SpecDoc` mechanism claims all hold.** `examples/fakeshop/apps/kanban/services.py` exposes no
  `SpecDoc` writer (0 hits), so a direct model write is the only available shape; and
  `signals.py:71-83` `UUID_LINKED_MODELS` does include `models.SpecDoc`, wired to `post_save`, which
  is precisely why raw SQL was disqualified. The `iterdump()` shows no new UUID row, consistent with
  the side row for id 55 already existing since 2026-07-11.
- **The negative was proved rather than asserted.** Two things a `git stash` / `checkout` / `restore`
  would have destroyed are still intact: the spec's uncommitted R1+R2 content (185,485, not HEAD's
  205,905) and the concurrent session's `D to-many-search-optimizer-reproduction.md`. Their survival
  is a real proof of the no-git-write claim, not a promise.
- **The residual sweep is exact as written**, and worth pinning precisely so a later reader does not
  mis-scope it: `docs/spec-044-debug_extension-0_0_14.md` as a path string survives **once** in the
  spec (`:1103`), and the sibling `-terms.csv` path survives once at `:513`. Both are W1-34's, both
  are separately line-pinned in Worker 2's notes, and neither was pre-adjusted.
- **`git status --short` is 12 entries**, exactly the 7-entry baseline plus the 5 files in
  `### Files touched`; `HEAD` is still `05a08e31`. No unexplained entry, no shrinkage, and the eight
  spec-046-surface `.py` files are absent because that commit carries them.

### Temp test verification

- **No temp test files were created by this review, and none by Worker 2.**
  `docs/builder/temp-tests/044-r3/` does not exist (`ls docs/builder/temp-tests/` lists `044-r1`,
  `044-r2`, and the preserved spec-046 cycle's directories, no `044-r3`), which corroborates Worker
  2's "the directory is empty / nothing was written there" and makes its absence a recorded fact
  rather than an oversight. `044-r1` and `044-r2` were read-only inputs and were not touched.
- My own verification ran as read-only probes plus scratch files **outside** the repo, under the
  session scratchpad: the two HEAD copies of the exports, the HEAD copy of `db.sqlite3`, and the two
  `iterdump()` texts. **Disposition: nothing to promote** — no probe caught a behavior bug (there is
  no behavior in this diff to catch one in), so `BUILD.md`'s promotion rule does not fire. Nothing
  was left inside the repo.

### Notes for Worker 1 (spec reconciliation)

- **I agree with Worker 2's `small drift, not structural` classification of the
  `SpecDoc.url` -> `SpecDoc.path` substitution, and the model shape is confirmed
  first-hand.** `examples/fakeshop/apps/kanban/models.py::SpecDoc` carries
  `path = models.TextField(default="")` with the comment "*Repo-relative path to the spec file. The
  GitHub URL is derived from it at read time (see :attr:`url`), so a repo rename never needs a data
  migration*", and `url` is a `@property` returning `f"{SPEC_URL_PREFIX}/{self.path}"` with no
  setter. Assigning it raises, as reproduced above.

  Judged against `worker-2.md` `## Plan-vs-implementation drift` as written, not against its
  headline: **small** covers a right answer that "stays within the slice's contract and is evaluable
  from the diff alone", with `__dict__` over `vars()` as its own example; **structural** is reserved
  for a *plan-level architectural* call — deleting a listed helper, choosing a different detection
  mechanism, restructuring a scoped phase. The substitution changes one token. Same row, same model,
  same ORM mechanism (`full_clean()` then `save()`, no raw SQL, no `.create()`), and a
  byte-identically equal resulting `url` — which I read back live. It is fully evaluable from the
  diff: the `iterdump()` delta names the `path` column outright. Decisively, the plan's own contract
  language is already path-oriented ("R3 repoints the url's **path only** to `docs/SPECS/…`"), so
  Worker 2 delivered the stated contract by the only available means.

  I applied the anti-gaming test my role file names, because under-classifying to dodge a re-loop is
  the failure this check exists for: did the choice hide anything, or foreclose an option Worker 1
  would have decided differently? **No.** There is exactly one writable field that yields the
  required `url`; no alternative existed, so there was no decision to reserve. And Worker 2 did the
  opposite of hiding — it recorded the drift prominently, quoted the current and replacement wording
  for this artifact's step 9 and box W2-10, and did the same for the build plan it may not write.
  Pausing to `revision-needed` would have spent a full Worker 1 spawn on a one-token substitution
  with a unique correct answer. **Agreed: small.**

  One consequence for your pass: box **W2-10**'s text and step 9's fenced block still say `url`.
  Worker 2's recommended replacements are correct as written; apply them when you audit the ticks.

- **`Escalated:` the `NEXT.md` / `worker-0.md` `SpecDoc.url` escalation is 4 sites of a 9-site
  population (Medium, above).** Worker 2's four sites and the `:246` callout are confirmed exact and
  each carries an actionable per-site replacement. Missing and actionable: `NEXT.md:247`, `:248`,
  `:334` (all three instruct a write to a property with no setter, verified by probe), plus the
  weaker `:51`; and the build plan at `:99` names a further surface,
  `docs/builder/worker-0.md:223`'s `SpecDoc.objects.create(..., url=...)`, which this artifact's
  escalation does not mention. Replacements for all five are drafted in the finding. **Resolution
  paths, in the order I would take them:** (a) carry the **full nine-site list plus `worker-0.md`**
  into `bld-044-final.md`'s `### Deferred work catalog` as one maintainer item, since `NEXT.md` and
  `worker-0.md` are outside every worker's writable set and the maintainer is the only party who can
  fix either — this is my recommendation and it costs nothing beyond a longer bullet; or (b) if you
  judge the standing-doc defect worth escalating on its own rather than inside the catalog, raise it
  as a separate maintainer note, because "the next spec author runs that broken example verbatim" (the
  build plan's own words) makes it the highest-consequence find of this item. Do **not** partial-fix:
  a four-site correction leaves numbered action 5 itself still instructing the raising operation.
- **The build plan already carries the correction, and it is not a Worker 2 scope violation.**
  `docs/builder/build-044-debug_extension-0_0_14.md:99` now records the `path`-vs-`url` fact,
  including the fifth `worker-0.md` surface. Worker 2's report states it did not edit that file
  (Worker 0's), and the content supports that: it names a site Worker 2's own escalation never
  mentions, and the file's mtime (`12:47:03`) post-dates the artifact's (`12:44:08`). Consistent with
  Worker 0 applying the recommended amendment on return. I found no evidence of a write outside
  Worker 2's declared set anywhere in the diff — the five modified files are exactly the five the plan
  authorizes.
- **`docs/spec-050-…:553`'s wrong `[spec-038]` target is confirmed and correctly unfixed.** It reads
  `SPECS/spec-038-auth_mutations-0_0_13.md`, which does not exist; spec-038 is
  `docs/SPECS/spec-038-form_mutations-0_0_12.md` (which spec-044's own `[spec-038]` definition names
  correctly) and `auth_mutations` is spec-040. Pre-existing, unrelated to spec-044's move, and it
  sits one line above the definition Worker 2 rewrote, so it appears in the same hunk — worth the
  deferred-catalog entry box W1-48 already plans.
- **`spec-050:554` needs a file-exists check your Direction-2 tooling will not give you.** Worker 2
  flagged this and it is correct: `link_audit.py` runs over the two **moved** files, and `spec-050`
  is not one of them, so nothing in steps 27-28 resolves the `[spec-044]` definition Worker 2's
  rewrite is the sole cause of. Add it to your step 28 sweep. I confirmed it resolves to
  `docs/SPECS/spec-044-debug_extension-0_0_14.md` from `docs/`, so it will pass the instant the move
  lands.
- **Baseline numbers you can inherit rather than re-derive**, all measured this pass: `git status
  --short` 12 entries with `HEAD` at `05a08e31`; spec 185,485 / CSV 4,940 / rationale 43,859 with 102
  and 28 definitions; `GlossarySpecMention` 1408 rows, 42 at the old `spec_path`, 0 at the new, 59
  distinct values, 13 orphan pairs; `manage.py check` clean; `import_spec_terms --check` OK.
- **`NEXT.md`'s "exactly one WIP spec at `docs/`" invariant stays unsatisfied by design** and is not
  reviewed as a finding, per the maintainer's scoping. Seven live specs remain at root; box W1-48
  carries it.

### Baseline / concurrent-work note (counted at both ends of this review pass)

**The list GREW during the review, from 12 entries to 16, and the growth is the concurrent spec-046
session resuming — reported, never reverted** (`AGENTS.md` rule 34). Four entries appeared that were
not present when I opened the pass: `django_strawberry_framework/utils/sessions.py`,
`docs/spec-046-transport_security-0_0_15.md`, `tests/test_routers.py`, `tests/test_views.py`.
Attribution, positively rather than by assumption: `HEAD` is still `05a08e31` at both ends, so no
maintainer commit landed; all four are spec-046-surface files the build plan's baseline-dirty list
already names; and all four mtimes fall **inside** this review pass (12:50:55 - 12:55:14), after my
own pass-start `git status`. This pass issued no `.py` write, no revert, and no
`git stash` / `checkout` / `restore` / `worktree`.

**R3's five files are unaffected**, re-measured after the growth: `git diff --numstat` still reads
`KANBAN.html` 1/1, `KANBAN.md` 2/2, `docs/spec-050-…` 3/3, `docs/dry/export_dry_review.py` 1/1;
`KANBAN.md` `ffc4d283…dc7c` and `KANBAN.html` `bcd9090a…abac` are unchanged; `db.sqlite3` hashes
`8de4bbeb…c81a`; and the spec / rationale still read 185,485 / 43,859. So every figure in this review
holds after the growth, and Worker 2's own `### Files touched` remains complete for its half. Worker
1 should expect **16 or more** entries at its own pass start and re-count rather than inherit this
paragraph — the list has now grown three times this cycle.

### Review outcome

**`review-accepted`**, with one Medium transparently escalated to Worker 1 above under an
`Escalated:` prefix, and one Low recorded with its rejection reason.

The deliverable is correct and every claim in the build report reproduces. What Worker 2 owned —
Direction 1's four inbound rewrites, the DB repoint, and the two regenerates — landed exactly as
planned and is verified by independent measurement rather than accepted on prose: the four rewritten
targets resolve to one post-move path, the DB delta is one row, both exports are provably the render
and nothing but the render, and spec-044's three files are byte-identical to R2's recorded end state.
The two findings Worker 2 surfaced are both real; the model shape is as it reports, and its drift
classification is right for the reasons its own role file gives.

Neither finding blocks the pass. The Medium is a defect in an **escalation record** rather than in the
diff, and its subject lives in two files no worker may write, so the correction cannot come from a
Worker 2 re-pass — it belongs to the pass that consumes the escalation, which is Worker 1's final
verification, next either way and the pass that performs the move.

---

## Final verification (Worker 1)

The accepting pass, and the pass that **performs R3's riskiest half**: `BUILD.md`
`### Spec stays at its working location` puts the mechanical move here, after the review, so the 95
path rewrites inside the two moved files get no independent reader. Nothing below was accepted on
prose. `worker-1.md` `### Verifying relocation / promotion claims` makes this pass's delta explicit —
run every relocation proof yourself rather than reading Worker 3's acceptance as discharge — and R3 is
**two** relocation claims at once: Worker 2's "the three spec-044 files are byte-unchanged by my pass"
and my own move, the largest relocation of the cycle. Where a re-derivation disagrees with a recorded
figure the disagreement is stated rather than reconciled silently, and it disagreed **twice**.

Required reading walked in full this spawn: `AGENTS.md`, `START.md`, `docs/builder/BUILD.md`,
`docs/builder/ARTIFACT.md`, `docs/builder/worker-1.md`, `GOAL.md`, `CHANGELOG.md`, the build plan, the
active spec and its rationale, `docs/builder/worker-memory/worker-1.md`, both prior artifacts
(`bld-044-r1-rationale_move.md` 702 lines, `bld-044-r2-doc_completion.md` 2,114 lines — the strict
no-"as needed" rule), `docs/SPECS/NEXT.md` Step 8 end to end, and `START.md`'s "Markdown link
convention". `docs/GLOSSARY.md` was read at the anchors the terms CSV names rather than end to end;
the 42 anchors are what this pass can falsify, and it did (`OK: 42 terms`).

### The pre-move capture (W1-23), reproduced figure for figure

Every baseline the plan pinned was re-measured, not inherited. All of them reproduced:

| Measurement | Recorded | Measured this pass |
|---|---|---|
| `git status --short` at pass start | "16 or more" (Worker 3) | **16** |
| `HEAD` | `05a08e31` | `05a08e31` |
| spec / CSV / rationale bytes | 185,485 / 4,940 / 43,859 | **185,485 / 4,940 / 43,859** |
| definitions | 102 / 28 | **102 / 28** |
| `link_audit.py` spec | 35 headings, 200 anchor uses / 26 distinct, broken=[], 102 defs, `undefined=['"sql"']`, unused=[] | identical |
| `link_audit.py` rationale | 20 headings, 2 uses / 2 distinct, broken=[], 28 defs, 0 / 0 | identical |
| cross-file failures, both files | `[]` | `[]` |
| `check_spec_glossary.py` | `OK: 42 terms`, exit 0 | identical |
| `GlossarySpecMention` rows | 1408 | **1408** |
| rows at the old `spec_path` / new | 42 / 0 | **42 / 0** |
| distinct `spec_path` values | 59 | **59** |
| `git status --short docs/GLOSSARY.md` | empty | empty |
| `KANBAN.md` / `KANBAN.html` digests | `ffc4d283…dc7c` / `bcd9090a…abac` | identical |
| `git diff --numstat` on R3's five files | 2/2, 1/1, 3/3, 1/1, Bin | identical |
| `manage.py check` | no issues | no issues |
| `import_spec_terms --check` | `OK: 46 done cards` | `OK: 46 done cards` |

Pre-move digests (`shasum -a 256`), the reference for the dirty-content proof:

```
2f32ae0ad7cdf01e9d2ad330efc4a93e8a1a2f6247844884bdebf3e81bc1aaf0  spec-044-debug_extension-0_0_14.md
91a322ec430218f0bce04954410ab799945b85dfb2a789781b983e387534c6ef  spec-044-debug_extension-0_0_14-terms.csv
6a99a214b57a1dae8102e95fb90414ccf79911aad511d4ce12ea2c66c957a743  spec-044-debug_extension-0_0_14-rationale.md
```

An `iterdump()` of `examples/fakeshop/db.sqlite3` was taken **outside the repo** (session scratchpad,
`mode=ro` through a `file:` URI so the capture cannot churn pages in a concurrently-writable tracked
binary), and pre-move copies of all three files were taken to
`docs/builder/temp-tests/044-r3/` so the **untracked** rationale could be diffed against its own prior
state. `docs/builder/temp-tests/044-r3/` did not exist at pass start (Worker 3's report is exact) and
was created here.

### The move (W1-24, W1-25, W1-26) and the dirty-content proof (W1-27)

Three commands, two of them `git mv` and one plain `mv`, and only on the three named files:

```shell
git mv docs/spec-044-debug_extension-0_0_14.md docs/SPECS/
git mv docs/spec-044-debug_extension-0_0_14-terms.csv docs/SPECS/
mv docs/spec-044-debug_extension-0_0_14-rationale.md docs/SPECS/
```

The third is a plain `mv` because the file is untracked — `git mv` refuses it. It is the **first**
`-rationale.md` under `docs/SPECS/`, confirmed rather than assumed.

**The proof the working-tree content survived, run before any rewrite touched the files:** all three
post-move `shasum -a 256` digests are **byte-identical** to the three above; `wc -c` reads
**185,485** / 4,940 / 43,859, not HEAD's 205,905 for the spec. Independently, `git diff HEAD --numstat
-M` reads

```
83	417	docs/{ => SPECS}/spec-044-debug_extension-0_0_14.md
```

— the rename **plus** R1's and R2's exact recorded 83/417 delta, so the uncommitted post-R2 content
rode along. Read at the two sentences that distinguish the two states: the working tree carries R2's
`Built for `0.0.14` (card `DONE-044-0.0.14`)` and "recorded **below rather than here**", while
`git show HEAD:docs/spec-044-debug_extension-0_0_14.md` carries `Planned for `0.0.14` (card
`WIP-ALPHA-044-0.0.14`)`. `git status` renders the spec as `RM` (staged rename + working-tree
modification), which is what a `git mv` on a dirty tracked file looks like and is not a defect.

The CSV's mtime is unchanged from its pre-cycle value, which is a second, independent witness that
`git mv` moved it without rewriting it; `cmp` against the pre-move copy exits 0.

### The group-relocation obligation the plan's table omitted

**This is the one thing my own plan got structurally short, and it is exactly the failure mode
`START.md` warns about.** The `### Direction 2` classification table is arithmetically exact — every
bucket count reproduced, and Worker 3's independent recomputation of all of them was right — but it
classifies **targets** only. `START.md` "Markdown link convention" adds a second obligation the table
does not carry:

> Group = where the **target** lives, NOT the source.

34 definitions point at files that moved **with** the spec, so their *path* is unchanged (the sibling
relation survives) while the directory their target lives in changed from `docs/` to `docs/SPECS/`.
Under the convention they must change **group**: the spec's 15 `rationale*` definitions and the
rationale's 18 `s44-*` plus `[spec-044]`, all of which sat under `<!-- docs/ -->`. A path-only
transformation leaves all 34 in a stale group, and that is precisely what a path-only diff hides —
every link still resolves, so no checker complains, and the next reader scanning "what does this file
link to under `docs/SPECS/`?" gets a wrong answer.

**The precedent is measured, not argued.** Three archived siblings already follow the rule:
`docs/SPECS/spec-043-test_client-0_0_14.md` carries `[spec-041]` / `[spec-042]` /
`[spec-037]` as bare filenames under `<!-- docs/SPECS/ -->`, and `spec-041` carries
`[spec-046]: ../spec-046-transport_security-0_0_15.md` under `<!-- docs/ -->` — the same file, grouped
by where its target lives, in both directions. So group-by-target is the archive's actual convention
and not an inference from `START.md` alone.

`relativize.py` therefore does both halves: it applies the six re-relativization rules **and**
re-assigns every definition to the canonical group its post-move target resolves into, then re-sorts
alphabetically within each group and re-emits all ten canonical headers in order. It errors rather
than passing through a target it cannot classify, and it file-exists-checks every rewritten target
before writing. Recorded as an addition to the plan's contract rather than by editing the plan's
table, whose counts are correct as far as they go.

One pre-existing ordering defect fell out of the rebuild and is worth naming so it is not read as
drift: `[workflow-django]` sat second in the spec's `<!-- Root -->` group at HEAD, where alphabetical
order by ref-id puts it last. The rebuild corrected it.

### Directions 2 and 3 — what landed (W1-28 to W1-36)

`relativize.py` (`docs/builder/temp-tests/044-r3/relativize.py`, gitignored, **not** in `scripts/` for
the reason `### DRY analysis` gives) printed `ref-id | before | after | bucket | group` for all **130**
definitions, the 35 it deliberately left alone included. Its dry run and its applied run are captured
at `relativize.dryrun.txt` / `relativize.applied.txt` in the same directory. Bucket census, measured
from that output:

| Bucket | Count | Rule |
|---|---|---|
| `docs-sibling-INVERTS-gains-a-level` | 46 | 45 spec (43 `GLOSSARY.md` + `README.md` + `TREE.md`) + 1 rationale `GLOSSARY.md` |
| `repo-root-or-subdir-gains-a-level` | 29 | 26 spec (8 Root, 3 pkg, 2 tests, 3 examples, 3 scripts, 7 `.venv`) + 3 rationale |
| `outside-repo-gains-a-level` | 13 | 10 spec + 3 rationale `<!-- External -->` sibling checkouts |
| `docs-SPECS-SHORTENS` | 7 | 5 spec (`[next]` + 4 sibling specs) + 2 rationale (`[next]` + `[spec-038]`) |
| `moves-together-sibling-UNCHANGED` | 34 | 15 spec `rationale*` + 19 rationale `s44-*` / `[spec-044]` — **all 34 regrouped** |
| `absolute-url-UNCHANGED` | 1 | the strawberry issue URL |

**Totals: 130 definitions, 95 changed, 35 unchanged, 34 regrouped** — reproducing the plan's table and
Worker 3's independent recomputation exactly, spec **86/16** and rationale **9/19**.

Diff shape, isolated with `git diff --no-index -U0` against the pre-move copies (the tracked diff is a
combined rename diff and the rationale is untracked, so this is the only method that attributes
per-line):

- spec **90 insertions / 90 deletions in 11 zero-context hunks** = 86 definition pairs + 2 prose pairs
  + the relocated `<!-- docs/SPECS/ -->` header and its blank line;
- rationale **11 / 11 in 6 hunks** = 9 definition pairs + the same relocated header pair;
- line counts unchanged at **2,839** and **672**; definition counts unchanged at **102** and **28**;
- the CSV is **byte-identical** (`cmp` exit 0) and needs no content edit (W1-35: measured — zero
  `docs/`, zero `.md`, zero `SPECS`, 43 lines = header + 42 term rows).

**The three inverting groups (W1-31), each handled by name.** `docs/` siblings *gain* a level;
`[next]: SPECS/NEXT.md` **shortens** to `NEXT.md` in both files; the four `[spec-038]` / `[spec-041]` /
`[spec-042]` / `[spec-043]` definitions **shorten** to bare siblings, plus the rationale's own
`[spec-038]` — seven shortenings in all, and every one of the five `docs/SPECS/` targets they point at
verified present on disk.

**W1-32.** `[glossary-django-trac-37064]: ../GLOSSARY.md#django-trac-37064-hardening` in **both**
files, its deliberate ref-id-vs-anchor mismatch preserved verbatim — the definition that keeps
`check_spec_glossary.py`'s 42nd term reachable, and the one a mechanical ref-id-to-anchor derivation
would corrupt. Nothing in `relativize.py` derives an anchor from a ref-id; it rewrites the path prefix
and carries `#anchor` through untouched.

**W1-34, the two prose paths the classifier cannot see**, both rewritten to the `docs/SPECS/` form
because both are repo-relative strings naming a file's location, which after the move name nothing:

- `:513` — `` `docs/spec-044-debug_extension-0_0_14-terms.csv` `` -> `` `docs/SPECS/…-terms.csv` ``
- `:1103` — ``This spec lives at `docs/spec-044-debug_extension-0_0_14.md``` -> `` `docs/SPECS/…md` ``

Both were at exactly the lines Worker 2 re-pinned. And the **seven** `[`docs/SPECS/NEXT.md`][next]`
prose code spans are confirmed **left alone** — spec `:90`, `:502`, `:1106`, `:1662`, `:2511` and
rationale `:83`, `:597`, all seven present, the prose being a repo-relative path that stays correct
while only the definition shortens. *Method note, because it bit me in the same breath as verifying
it:* my first probe filtered out lines beginning with `[` to exclude definition lines and thereby
**hid `:1662`**, whose prose span starts at column 1 — the filter was itself the sample defect this
cycle keeps re-learning. Counting `NEXT.md` occurrences (6 = 5 prose + 1 definition) is what found it.

**W1-36, Direction 3, stated and verified rather than left unaddressed.** It reduces to the
spec <-> rationale <-> CSV relationship, and the reduction is now *proved* rather than assumed: a
tree-wide sweep for any definition-shaped line or inline link whose target names
`spec-044-debug_extension` finds **exactly one** outside the moved pair —
`docs/spec-050-debug_extraction-0_0_19.md:554` — and **no** file anywhere references
`spec-044-debug_extension-0_0_14-rationale` or `-terms.csv` except spec-044 itself and this cycle's
own `docs/builder/` artifacts. So there was no fourth reader to repoint. The 15 spec->rationale and 19
rationale->spec definitions are unchanged by design (all three files moved together), the one
spec->CSV prose path is rewritten, and the four `SPECS/spec-…` shortenings are Direction 2's inversion
case rather than Direction 3. Nothing is deferred under it.

### The anchor pass, not a path sample (W1-37, W1-38)

`docs/builder/temp-tests/044-r2/link_audit.py` reused **verbatim, invoked in place**, on the two
post-move paths — it takes paths from `argv`, skips `http` targets, and resolves cross-file `#anchor`
targets, so it works post-move unedited exactly as the plan predicted:

```
== docs/SPECS/spec-044-debug_extension-0_0_14.md
   headings=35 inpage_uses=200 distinct=26 broken=[]
   defs=102 undefined=['"sql"'] unused=[]
   cross-file failures=[]
== docs/SPECS/spec-044-debug_extension-0_0_14-rationale.md
   headings=20 inpage_uses=2 distinct=2 broken=[]
   defs=28 undefined=[] unused=[]
   cross-file failures=[]
```

The whole baseline table reproduces post-move. `undefined=['"sql"']` on the spec **only** is the
standing `res.extensions["debug"]["sql"]` code-span false positive every prior pass recorded; it is
not a link.

**This is the check a file-exists spot-check cannot give**, and it is scoped to the measured **75**
cross-file anchored definitions rather than the inherited "33": 42 `GLOSSARY.md#…` + 14
`rationale#…` in the spec, 1 `GLOSSARY.md#…` + 18 `spec-044#…` in the rationale. All 75 resolve to a
real heading in a real file. `cross-file failures=[]` covers **129** file-exists checks as well (130
definitions minus the one `https://github.com/strawberry-graphql/strawberry/issues/4369` it correctly
skips), so W1-38's full-set requirement is discharged by construction and not by `NEXT.md` Step 8
action 8's 5-10 sample. `relativize.py` independently file-exists-checked all 130 before writing.

One limitation of the tool worth recording rather than leaving for a future reader to trip over: its
*in-file* heading scan strips fenced blocks line by line, but its *cross-file* heading scan does not.
The asymmetry can only produce a false **pass** (an extra heading harvested from inside a fence), never
a false failure, so it does not weaken a `failures=[]` result for these two files — every one of the 75
anchors also resolves against the fence-stripped heading sets the in-file scan built for the same two
files.

**Worker 3's extra ask, discharged:** `docs/spec-050-…:554`'s `[spec-044]: SPECS/spec-044-…md` is not
covered by `link_audit.py` (which runs over the two *moved* files), so it was resolved separately —
`docs/` + `SPECS/spec-044-debug_extension-0_0_14.md` -> `docs/SPECS/spec-044-debug_extension-0_0_14.md`,
**exists**. All four of Worker 2's inbound rewrites now resolve, so the deliberate transient state is
closed.

**W1-39.** `uv run python scripts/check_spec_glossary.py --spec
docs/SPECS/spec-044-debug_extension-0_0_14.md` -> `OK: 42 terms - all have glossary entries and at
least one spec link.`, **exit 0**, at the **new path**, with no `--terms` or `--glossary` override —
the plan's path-prefix-tolerance finding holds against the moved file.

### The DB sync — prediction against measurement (W1-40 to W1-43)

The ordering decision was correct in both direction and timing, and it is now demonstrated rather than
reasoned:

- **Before the write, after the move,** `import_spec_terms --check` **failed on card 044**, and for
  the predicted reason: `CommandError: GlossarySpecMention rows for
  docs/SPECS/spec-044-debug_extension-0_0_14.md do not match …-terms.csv: [] != [42 anchors]`. That
  failure is the evidence both that the sync was needed and that the move landed; its absence would
  have meant the move did not.
- **The write run** -> `Imported glossary terms for 46 done card(s).`
- **After** -> `OK: 46 done cards have glossary links.`, exit 0 (W1-41). All 46 done cards, not just
  044.

**The row count grew exactly as predicted, and the orphans are left in place.**
`GlossarySpecMention` **1408 -> 1450**: 42 new rows at `docs/SPECS/spec-044-debug_extension-0_0_14.md`,
42 orphaned at `docs/spec-044-debug_extension-0_0_14.md`, distinct `spec_path` values 59 -> **60**,
orphan pairs 13 -> **14**. A different number would have been a signal to stop; it is the predicted
number. Per the plan's ruling they are **not** cleaned up here: a spec-044-only fix would make one
card diverge from 13 siblings, and the cause is `_sync_spec_mentions` deleting only at the *new*
`spec_path`. Routed to the deferred catalog with the figures (W1-43).

**W1-42 needed a stronger method than the plan named, and this is the pass's second measurement
disagreement.** A raw `iterdump()` line diff of before-against-after reads **1973 added / 1931
removed** — nearly 3,900 changed lines for a 42-row change — because `import_spec_terms` deletes and
re-inserts all 949 `CardGlossaryTerm` rows and re-inserts the mention rows with fresh surrogate ids
and `updated_date` stamps. Read as a line diff, that looks like catastrophe. The correct instrument is
a **content-keyed multiset** comparison with surrogate ids and timestamps normalized:

| Table | Before | After | Only-before | Only-after |
|---|---|---|---|---|
| `glossary_glossaryspecmention` | 1408 | 1450 | **0** | **42** (all at the new path) |
| `kanban_cardglossaryterm` | 949 | 949 | **0** | **0** |
| `kanban_card_labels` | 237 | 237 | **0** | **0** |
| `kanban_specdoc` | 50 | 50 | **0** | **0** |

`only_before = 0` everywhere is the strong form of "no other card's rows changed": not one
pre-existing row's content was altered or removed, the 42 orphans included. This is the same trap
`BUILD.md` `### Tracked binary / generated files` names, one level up — a *line* diff of a semantic
dump is no more a semantic comparison than `git diff --stat` on the binary is.

### The generated exports — one moved, one did not, and why (W1-44, W1-45)

The plan predicted both exports would be byte-identical to Worker 2's output after the sync, and told
me to assert it rather than assume it. **Asserting it is what caught it.**

- `KANBAN.md` **is** byte-identical (`ffc4d283…dc7c`), and `build_kanban_md.py --check` reported "up to
  date" **before** any render this pass.
- `KANBAN.html` is **not**: `build_kanban_html.py --check` reported **Stale**, and the render moved it
  `bcd9090a…abac` -> `209ae514…9ce9`.

The plan's premise — the CSV and its anchor order are unchanged — was true and incomplete. The sync
re-creates every `CardGlossaryTerm` row, `KANBAN.html`'s minified data block renders `updatedDate`,
and `KANBAN.md` does not. That asymmetry between the two exports is itself the proof of the cause.
Verified structurally rather than characterised: parsing both data blocks and walking them leaf by
leaf against HEAD's gives **952 differences = 950 `updatedDate` + card 44's `spec.path` + card 44's
`spec.url`**, and nothing else. Net byte delta is still exactly **+12 = 2 x len("SPECS/")** because
the timestamps are equal-length, which is why `git diff --numstat` still reads 1/1 and cannot see any
of this.

Two-consecutive-regenerate byte stability hashed for all three generated files: identical across runs.
`docs/GLOSSARY.md` is **byte-identical and still clean** — `git status --short docs/GLOSSARY.md` empty
throughout, `grep -c 'spec-0[0-9][0-9]-'` -> 0, so the glossary render carries no spec path and had
nothing to change (W1-45). A diff there would have been a signal; there is none.

**W1-46.** `uv run python examples/fakeshop/manage.py check` -> `System check identified no issues (0
silenced).` `git diff --check` -> exit 0. `uv run python scripts/check_trailing_commas.py --check` on
explicit paths (the two moved `.md` files and this artifact) -> exit 0; pathless it would rewrite
unrelated `docs/` scratch files. `uv run ruff format --check docs/dry/export_dry_review.py` -> `1 file
already formatted`; `uv run ruff check` on the same path -> `All checks passed!` (re-run read-only to
re-verify W2-7; the `COM812`-vs-formatter warning is pre-existing config noise).

### Step 3 — the checklist audit, the central duty

**Walked all 50 boxes. No box is over-ticked, none is silently un-ticked, and none is left `- [ ]`, so
no deferral reason is owed.** 20 `W2-*` + 30 `W1-*` = 50 ticked.

**All 20 `W2-*` ticks confirmed against the diff independently, not read off Worker 3's audit.** W2-1
(my own full-token sweep reconciles to the plan's table, including all 12 out-of-scope provenance
files); W2-2/3/4 (spec-050's three rewrites present at `:127`, `:472`, `:554`, all resolving
post-move, `numstat` 3/3); W2-5 (`:553`'s wrong `[spec-038]: SPECS/spec-038-auth_mutations-0_0_13.md`
still present and unfixed — `docs/SPECS/` holds `spec-038-form_mutations-0_0_12.md`, so the target
does not exist — correctly reported not fixed); W2-6 (`export_dry_review.py:30`, `numstat` 1/1); W2-7
(re-run read-only, both green); W2-8 (`grep -o 'spec-044' CHANGELOG.md | wc -l` -> **0**, occurrences
not lines); W2-9 (proved by my own pre-move measurement: the three files were byte-for-byte R2's
recorded end state, so Worker 2's contribution to them was zero bytes); W2-10/11 (row read live:
`name` unchanged, `path` and derived `url` both at `docs/SPECS/…`); W2-12 (proved mechanically — my
pre-move DB carried **0** `GlossarySpecMention` rows at the new path, which a write-mode run would
have created); W2-13/14/15 (`KANBAN.md` byte-identical to a fresh render; the HEAD structural diff is
2 path leaves + card 44's `updatedDate`); W2-16; W2-17; W2-18; W2-19; W2-20 (the three literals and
`Status: built` present as written).

**Two `W2-*` box texts were narrower than what landed. Both are stale wording, not over-ticks**, and
Worker 3 correctly said Worker 1 owns the wording. Corrected in place, each marked inline:

- **W2-10** said the repoint went to the `…/blob/main/…` **url**. The write was to `path`, because
  `SpecDoc.url` is a read-only `@property`. Worker 2's own recommended replacement was applied
  verbatim. Same row, same contract, byte-identically equal resulting `url` — I read it back live.
  I agree with both prior passes' `small drift, not structural` classification, and the anti-gaming
  test holds: there is exactly one writable field that yields the required `url`, so no alternative
  existed and no decision was foreclosed.
- **W2-14** said "2 in `KANBAN.html` … nothing else". The render also carries card 44's `updatedDate`,
  which Worker 2 disclosed twice and the plan's step 14 pre-authorized. Corrected to 3 fields.

**Three `W1-*` box assertions were falsified or under-scoped by my own measurement**, and each is
corrected in place rather than quietly satisfied:

- **W1-33** — "zero non-definition lines changed by the classifier" is **false**: the group relocation
  moves one `<!-- docs/SPECS/ -->` header and its blank line in each file. The 95 is exact.
- **W1-42** — "no other card's rows changed (proved by `iterdump()` difference)" needed the
  content-keyed multiset method; the raw line diff is 1973/1931 and proves nothing either way.
- **W1-44** — "byte-identical to Worker 2's output" is **half false**: `KANBAN.md` yes, `KANBAN.html`
  no.

**W1-31** was additionally scope-clarified rather than falsified: its "45 defs" is the spec's inverting
group and is correct as scoped, but it reads as a both-files total, which is 46. So the cycle's
parenthetical-rot count is now **nine** — six recorded through R2, plus W1-33, W1-42, and W1-44 here —
and every instance has the same shape: the number is an audit claim written before the audit ran. The
two `W2-*` corrections are a different failure (a box describing the right work with the wrong field or
an incomplete field list), which is why they are not counted in the nine.

### Step 4 — R3 against R1 and R2

Both prior artifacts read in full (`final-accepted`, 702 and 2,114 lines). No new duplication and no
inconsistent shape:

- **Method converged rather than diverged, and R3 used the cheapest available route.** R1 isolated by
  reconstruction (`git show HEAD:` + `patch`), R2 pass 2 adopted `git diff -U0` and recorded why
  (adjacency cannot shift a zero-context hunk), R2's final verification used HEAD directly where HEAD
  *was* the prior state. R3 needed a fourth: a **saved pre-move copy** plus `git diff --no-index -U0`,
  because a rename makes the tracked diff combined and one of the two files is untracked. All four are
  the same principle applied to different availability.
- **The deferred catalog is still one record.** R1 contributed one item, R2 merged it into a
  seven-item list (six numbered plus its own routing observation as item 7), and R3 adds three without
  re-deriving any of them — the hand-off is by pointer, as R2's box 33 requires.
- **The "shortest distinctive token" lesson is now four-for-four across the cycle**, and R3 supplied
  two more instances of it: the `docs/spec-044-…` sweep that cannot see `../spec-044-…` (which is why
  the tree-wide definition sweep above uses the bare token), and my own `[`-excluding filter that hid
  `:1662`. R1's pair ("line-oriented sweeps are blind to a line wrap" plus R2's "flattened but
  over-specific") now has a third member: **a filter written to exclude one shape can exclude the
  evidence.**
- **No prior entry's body was edited** in any of the three artifacts; each pass published its
  corrections in its own section, with the checklist boxes and their figures as the one licensed
  exception. Same convention, applied three times.
- R1's three forward-looking cautions for R3 are all honoured: the anchor-resolution pass was run (not
  merely file-exists); the three name-based citations at `:1562`, `:1613`, `:1924` were **not**
  re-ordinalized (nothing in this pass touched prose other than the two path strings); and the
  rationale's four `../`-prefixed paths plus its two `SPECS/` shortenings were handled as its own
  bucket rather than assumed identical to the spec's.

### Step 5 — the verification battery, and why no `pytest` belongs to R3

**No pytest test belongs to R3, and that is the plan's ruling rather than an omission.** The item
writes three renames, 95 path rewrites, two prose path strings, 42 DB rows, and three regenerates —
no executable line, nothing reachable from a real GraphQL query, so `AGENTS.md` rule 10's live-first
mandate has no subject. A `pytest` invocation here would report only whether the tree at large is
green, a property this item cannot affect and the final gate owns; running one for form would be worse
than recording the reasoning. **No `pytest` ran in any pass of this item, and no `--cov*` flag in any
pass of this cycle.** The battery the plan pinned in its place ran in full and every command's result
is recorded above: `link_audit.py` (pre and post), `check_spec_glossary.py`, `import_spec_terms`
`--check` / write / `--check`, the four DB measurements, both kanban renders and their `--check` modes,
`build_glossary_md.py`, `manage.py check`, `check_trailing_commas.py --check`, `git diff --check`, and
the scoped read-only `ruff` pair.

### Step 6 — the staged-anchor sweep

`grep -rEn 'TODO\(spec-044|TODO-(ALPHA|BETA|STABLE)-044' .`, with `KANBAN.md` / `KANBAN.html` /
`BACKLOG.md` excluded (there `TODO-<MILESTONE>-<NNN>` legitimately names a board card).

**Zero anchors in package source or tests — reproduced a fourth time, independently:** `grep -rEn …
django_strawberry_framework tests examples scripts | wc -l` -> **0**. Card 044 shipped, so that is the
required result and this cycle owes no anchor removal. **The move did not disturb the ruling.**
Spec-044's five spec-internal mentions moved directory with the file and are intact at `:427`, `:430`,
`:452`, `:576`, `:578` — line for line the pins R2's box 9 established, including its correction of
R1's `:453` mislabel. Every other survivor is in a class both closed items already ruled: the archived
`0.0.14` siblings and two archived `-terms.csv` (historical record), `docs/spec-050-…` and
`docs/spec-051-…` one each (deferred-catalog item 1), and this cycle's own `docs/builder/` artifacts
(per-cycle scratchpads).

### Failability and fail-open checks

**Confirmed from the diff rather than assumed. No failability proof is owed.** R3 introduced no
boundary, guard, gate, rejection path, or validation branch — the plan's boundary count is **0** and
every write this pass made is a path string, a file rename, a DB row, or regenerated output. This
pass wrote **no `.py` file inside the repo's tracked surface**: the only Python it authored is
`docs/builder/temp-tests/044-r3/relativize.py`, which is gitignored throwaway tooling and ships
nothing. The four `.py` files in the working-tree diff are Worker 2's one docstring line in
`docs/dry/export_dry_review.py` and the concurrent session's three
(`django_strawberry_framework/utils/sessions.py`, `tests/test_routers.py`, `tests/test_views.py`).
`BUILD.md` `### What needs a proof, and what does not` scopes the obligation to boundaries, so the
mandatory re-run floor is arithmetically zero rather than a chosen subset, and both prior sections'
`None; this pass introduced no new boundary.` is accurate.

Read for the catalogued **fail-open shapes** as well (clamp, `getattr` default, `or` fallback, bare
`except`, truthiness on a value that can be absent, any default reached because the input was
*incoherent* rather than absent). None can exist in the tracked diff, there being no expression in it.
One deliberate design choice in the throwaway classifier is worth stating because it is the *opposite*
shape and the reason it was written that way: `classify()` **raises** on a target it cannot bucket
rather than returning it unchanged. A pass-through default would have been the fail-open — an
unrecognized path silently surviving the move unrewritten, invisible in a diff of 95 changed lines.
Guard the answer, not one spelling of the input.

**Public-surface check:** `git diff -- django_strawberry_framework/__init__.py` produces **0** lines.

### The escalated Medium — a maintainer hand-off, confirmed at nine sites plus one, with a refinement

Worker 3 accepted while escalating that Worker 2's `docs/SPECS/NEXT.md` `SpecDoc.url` escalation names
4 of a 9-site population. **The full nine-site census is confirmed by my own measurement**
(`grep -n 'SpecDoc\|url' docs/SPECS/NEXT.md`, then each hit read in context and classified
write-versus-read). Worker 3's table is exact:

| Site | What it says | In Worker 2's escalation? | Kind |
|---|---|---|---|
| `:51` | "all moved-spec `SpecDoc.url` repoints" | no | outcome description, weakest |
| `:246` | field list "`card` one-to-one, unique `name`, `url`" + "whatever follows `blob/main/` in `SpecDoc.url`" | yes, as "prose-accurate but now misleading" | callout |
| `:247` | "update that card's `SpecDoc.url` to the new path" | **no** | **actionable instruction, raises** |
| `:248` | `SpecDoc(card=…, name=…, url="…")` | **no** | **constructor kwarg, raises in `Model.__init__`** |
| `:272` (in `:268-274`) | `defaults={'name': …, 'url': f'{BLOB}/docs/spec-…md'}` | yes | `update_or_create`, raises on both branches |
| `:280` | `sd.url = f'{BLOB}/docs/SPECS/{name}.md'` | yes | assignment, raises |
| `:334` | numbered action 5: "updating that card's `SpecDoc.url` in the DB" | **no** | **actionable instruction, raises** |
| `:337` | `update_or_create(card=…, defaults={"name": …, "url": "https://…"})` | yes | raises |
| `:338` | "update `SpecDoc.url` (and `name` if the slug changed)" | yes | actionable instruction |

`:335` and `:339` are **reads** of the derived property and are correct as written; they are not part
of the population. Worker 3's diagnosis is right and is the cycle's repeating failure in miniature:
the escalated set is exactly the sites whose text contains an assignment or a `'url':` key, and the
missed set is exactly the sites that spell the same instruction in **prose** — the supporting grep
sampled the defect's *syntax* rather than its *vocabulary*.

**The sixth surface is confirmed, with one refinement Worker 3's rendering does not carry.**
`docs/builder/worker-0.md:223` is a single line carrying **two** `url` writes, not one:
`SpecDoc.objects.create(card=card, name="spec-<NNN>-<topic>-<ver>", url="https://…/blob/main/docs/spec-<NNN>-<topic>-<ver>.md")`
**and** "If a `SpecDoc` row already exists for the card, **update** its `url`/`name`". A fix that
rewrites only the `create(...)` call leaves the same line still instructing a write to a property with
no setter. (`worker-0.md:211`'s `SpecDoc` mention is an existence invariant, not a `url` write, and is
correct as written.) *Disclosure, as Worker 3 made its own:* to confirm this I ran a single
line-numbered `grep -n 'SpecDoc' docs/builder/worker-0.md` and read the two matched lines. That file
states in its own body that Workers 1-3 do not read it; my role file's forbidden-read list names only
the three `worker-memory/` files, so this is not a listed violation, but it is recorded rather than
left invisible. I drew nothing else from the file, and the build plan at `:99` already names the site
independently.

**Resolution: Worker 3's path (a), the full list into the deferred catalog as one maintainer item.**
Neither `docs/SPECS/NEXT.md` nor `docs/builder/worker-0.md` is writable by any worker in this cycle,
so no re-pass can fix the defect and `revision-needed` would route to a builder that cannot touch
either file. What Worker 1 owes is a record precise enough that the maintainer can act without
re-deriving anything, which is what the table above and the replacements below are. **Do not
partial-fix:** a four-site correction leaves numbered action 5 itself still instructing the raising
operation, in the document whose entire purpose is to be copy-pasted by the next spec author.
Replacements for the five previously-missing sites, in the documents' own voice, carried forward from
Worker 3's drafts and confirmed by me:

- `NEXT.md:51` -> "all moved-spec `SpecDoc.path` repoints".
- `NEXT.md:247` -> "update that card's `SpecDoc.path` to the new repo-relative path, e.g.
  `docs/SPECS/spec-<old_NNN>-…md` (`SpecDoc.url` is derived from it and read-only)."
- `NEXT.md:248` -> "`update_or_create` a `SpecDoc(card=<active card>,
  name=\"spec-<NNN>-<topic>-<X_Y_Z>\", path=\"docs/spec-<NNN>-<topic>-<X_Y_Z>.md\")`."
- `NEXT.md:334` -> "… repointed by updating that card's `SpecDoc.path` in the DB (set it to
  `docs/SPECS/spec-…md`) and re-rendering …"
- `worker-0.md:223` -> `SpecDoc.objects.create(card=card, name="spec-<NNN>-<topic>-<ver>",
  path="docs/spec-<NNN>-<topic>-<ver>.md")`, **and** "If a `SpecDoc` row already exists for the card,
  **update** its `path` / `name`" — both halves of the line.

Worker 2's four sites plus the `:246` callout keep the replacements it already drafted. **The
falsifiable check for the whole item:** `grep -n 'SpecDoc' docs/SPECS/NEXT.md docs/builder/worker-0.md`
returns zero sites that assign, construct, or instruct assigning `url`. This is the item's
highest-consequence find, and R3 is the second standing-doc defect this cycle has turned up in the
hand-run archive procedure — which strengthens the `scripts/archive_spec.py` candidate rather than
merely annoying.

### The rejected Low — reason confirmed, and the figures re-measured

Worker 3 rejected one Low with a recorded reason: two line-length figures in
`### Implementation notes` are each off by one ("72 and 78" measure 73 and 79; "168 lines over 72
characters" was the pre-edit count, now 169). **The rejection reason stands, and I re-measured both
halves rather than accepting either.** `docs/spec-050-debug_extraction-0_0_19.md:127` is 73 characters
and `:472` is 79; the file carries 169 lines over 72. The rejection reason — "artifact-record figure
with no consumer, correctable in passing by whoever next writes the file, not worth a re-pass" — is
mechanical rather than preferential and is correct: no plan step, box, or later pass reads those two
numbers, and the load-bearing half of the note (that `.md` line length is unenforced, `AGENTS.md` rule
17's limit being ruff's and therefore `.py`-only, so leaving the wrap alone avoids the rewording boxes
W2-2/W2-3 forbid) is independently confirmed. Recorded as addressed here, in this section, rather than
by editing a prior entry's body (`ARTIFACT.md` `## Re-pass sections`): the corrected sentence should
have read "**73 and 79** characters" against a pre-edit population of **168**, now **169**.

### Deferred work catalog hand-off — R2's seven plus R3's three

`bld-044-final.md` is not this pass's file. The authoritative hand-off is **R2's seven items** (its six
merged plus its own item 7 routing observation — do not re-derive them, and note the two location
corrections R2's final verification made: item 2's sentences are at `docs/spec-050-…:173` and
`docs/spec-051-…:235`, not the `:155` / `:215` section headings), **plus these three from R3**
(W1-48):

1. **`NEXT.md`'s "exactly one WIP spec at `docs/`" invariant remains unsatisfied after R3, by design.**
   Measured after the move: **seven live spec stems** stay at root (`045`, `046`, `050`, `051`, `052`,
   `053`, `054`), on the maintainer's explicit scoping of this item to spec-044 alone. Note for whoever
   runs the sweep: `ls docs/spec-*.md` prints **eight** files, not seven — `spec-046` carries its own
   `-rationale.md` alongside its `.md`, so the file count and the stem count differ by one, and eight
   is not evidence a stem was missed.
   Recorded so a future `NEXT.md` run does not read the residue as drift this cycle caused. **Owner:
   maintainer / the next spec author's Step 8.**
2. **The 14th `GlossarySpecMention` orphan pair, and its cause.**
   `examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py::_sync_spec_mentions`
   deletes only rows at the **new** `spec_path`, never the old one, so every spec archive leaves the
   old path's rows behind. Measured this pass: 1408 -> 1450, 42 live at
   `docs/SPECS/spec-044-debug_extension-0_0_14.md` beside 42 orphaned at
   `docs/spec-044-debug_extension-0_0_14.md`; 60 distinct `spec_path` values for 46 live specs; **14**
   orphan pairs, of which 13 predate this cycle (e.g. spec-028 43 orphans beside 44 live; spec-043 22
   beside 22). Deliberately **not** cleaned up in R3: a spec-044-only fix makes one card diverge from
   13 siblings. **One owner, one sweep, or not at all. Owner: maintainer.**
3. **`docs/SPECS/NEXT.md` Step 8's `SpecDoc.url` worked example is broken at nine sites, plus
   `docs/builder/worker-0.md:223` (two writes on one line).** The full census, the write-versus-read
   classification, and per-site replacements are in `### The escalated Medium` above. Both files are
   outside every worker's writable set. **Highest-consequence item of R3: the next spec author runs
   that example verbatim, and it raises `AttributeError: property 'url' of 'SpecDoc' object has no
   setter` rather than mis-writing. Owner: maintainer.**

Also carried from Worker 2 and confirmed by both later passes: `docs/spec-050-…:553`'s
`[spec-038]: SPECS/spec-038-auth_mutations-0_0_13.md` names a file that does not exist (spec-038 is
`form_mutations-0_0_12`; `auth_mutations` is spec-040), sits one line above the definition Worker 2
rewrote, and is correctly unfixed as an unrelated pre-existing inaccuracy in a live spec. And the
plan's own `scripts/archive_spec.py` candidate — ~120 lines of hand-run `NEXT.md` procedure that has
now produced two standing-doc defects and 14 orphan-row pairs — stands as a real future card.

### Baseline / concurrent-work note (counted at both ends)

**16 entries at pass start, 18 at pass end, and both new entries are attributed positively rather than
assumed.** `HEAD` is `05a08e31` at both ends (`git reflog --date=iso` confirms the last commit landed
at 12:16:16, before this pass opened), so no maintainer commit landed mid-pass and no shrinkage
occurred.

- **+1 mine:** `R docs/spec-044-debug_extension-0_0_14-terms.csv -> docs/SPECS/…`. The CSV was
  **clean** before the move, so its rename creates an entry where there was none; the spec's entry
  changed shape from `M` to `RM` rather than multiplying, and the rationale's `??` entry moved path.
- **+1 not mine:** `M docs/feedback.md`, mtime **13:15:05** — the newest mtime in the tree and *later*
  than my last write (13:14:22). Its first line reads "Adversarial review: spec-046 transport
  security" (102/140 lines). It is the preserved spec-046 cycle's maintainer review, dirty through R1
  and R2, swept into `05a08e31`, and now dirty again. Reported, **never edited, never reverted**
  (`AGENTS.md` rule 34).

The four spec-046-surface entries Worker 3 saw appear (`django_strawberry_framework/utils/sessions.py`,
`docs/spec-046-transport_security-0_0_15.md`, `tests/test_routers.py`, `tests/test_views.py`) carry
mtimes 12:50:55-12:55:14, inside Worker 3's pass and before mine; the
`to-many-search-optimizer-reproduction.md` deletion is the standing baseline entry. None was edited or
reverted. **This pass issued no `.py` write to any tracked file** — the strongest available
attribution, since no residual item's writable set contains one.

**No `git stash`, `git checkout`, `git restore`, or `git worktree` ran at any point** (W1-50). The only
tree-mutating git command was `git mv`, on the two named tracked files. HEAD comparisons went through
`git show HEAD:<path>` into scratch paths **outside** the repo. No commit. No branch created or
switched. Two negatives are proved rather than promised: the spec's uncommitted R1+R2 content is still
present (185,485, not HEAD's 205,905) and the concurrent session's
`D to-many-search-optimizer-reproduction.md` still stands — both would have been destroyed by a stash
round-trip.

### Summary

R3 archived spec-044 to `docs/SPECS/`, closing the residual-completion cycle's last item. Three files
moved — the tracked spec (dirty with R1+R2's uncommitted edits, `git mv`), the tracked and clean
`-terms.csv` (`git mv`), and the untracked `-rationale.md` (plain `mv`, the first `-rationale.md` under
`docs/SPECS/`) — and all three destination digests are byte-identical to their pre-move digests, so the
dirty content is proven to have survived rather than assumed to have. Inside the two `.md` files, 95 of
130 link definitions were re-relativized by a deterministic classifier that errors rather than passing
through, and **34 more changed group** under `START.md`'s group-by-target rule — the obligation my own
plan's classification table omitted, and the one a path-only diff hides because every link still
resolves. Byte counts moved **185,485 -> 185,710** and **43,859 -> 43,868**, matching the delta
predicted from the bucket census to the byte. Every gate is green at the new path: `OK: 42 terms`, 200
in-page anchors with zero broken, all **75** cross-file anchors resolved, 129 file-exists checks
passed, `import_spec_terms --check` `OK: 46 done cards`, `manage.py check` clean, `git diff --check`
exit 0, `docs/GLOSSARY.md` untouched and clean.

Two predictions in the plan were falsified by measurement, and both were caught only because the plan
required asserting rather than assuming. **First**, the `import_spec_terms` sync moved `KANBAN.html`
(`bcd9090a…abac` -> `209ae514…9ce9`) while leaving `KANBAN.md` byte-identical — the sync re-creates
every `CardGlossaryTerm` row and only the HTML export renders `updatedDate`. Structurally verified
against HEAD as 950 timestamps plus card 44's `spec.path` and `spec.url`, and nothing else, at a net
byte delta of exactly +12. **Second**, "no other card's rows changed" is unprovable by the
`iterdump()` line diff the box named — that reads 1973/1931 for a 42-row change — and needed a
content-keyed multiset comparison, which returns `only_before = 0` on all four affected tables. The
predicted 1408 -> 1450 held exactly, with 42 rows orphaned at the old path as the 14th instance of a
13-times-precedented pattern, left in place by ruling and routed to the catalog with its cause named.

The item's highest-consequence product is not the move. It is the confirmed maintainer hand-off:
`docs/SPECS/NEXT.md` Step 8's copy-paste archive example instructs a write to `SpecDoc.url`, a
read-only `@property`, at **nine** sites — Worker 2 found four and the `:246` callout, Worker 3 found
the three prose sites the syntax-shaped grep could not see, and I confirmed all nine plus the
refinement that `docs/builder/worker-0.md:223` carries **two** such writes on one line. Neither file
is writable by any worker in this cycle, so the record is the deliverable, and it is precise enough to
act on without re-derivation.

`Status: final-accepted`. All 50 checklist boxes ticked; no over-tick, no silent un-tick, no `- [ ]`
and therefore no deferral reason owed; two `W2-*` box texts and four `W1-*` box assertions corrected in
place with the measurement that falsified each.

### Spec changes made (Worker 1 only)

**The move — old and new paths for all three files**, per `BUILD.md` `### Spec stays at its working
location`:

| Old path | New path | Command | Bytes before -> after |
|---|---|---|---|
| `docs/spec-044-debug_extension-0_0_14.md` | `docs/SPECS/spec-044-debug_extension-0_0_14.md` | `git mv` (tracked, dirty) | 185,485 -> **185,710** |
| `docs/spec-044-debug_extension-0_0_14-terms.csv` | `docs/SPECS/spec-044-debug_extension-0_0_14-terms.csv` | `git mv` (tracked, clean) | 4,940 -> **4,940** (byte-identical) |
| `docs/spec-044-debug_extension-0_0_14-rationale.md` | `docs/SPECS/spec-044-debug_extension-0_0_14-rationale.md` | plain `mv` (untracked) | 43,859 -> **43,868** |

**In-file edits to `docs/SPECS/spec-044-debug_extension-0_0_14.md`** (line numbers as they stand after
the edits; the file's line count is unchanged at 2,839):

- `:513` — the prose `` `docs/spec-044-debug_extension-0_0_14-terms.csv` `` path rewritten to
  `docs/SPECS/…`. Reason: a repo-relative string naming a file's location, which the move made name
  nothing. (Box W1-34.)
- `:1103` — the self-reference ``This spec lives at `docs/spec-044-debug_extension-0_0_14.md``` rewritten
  to `docs/SPECS/…`. Reason: same; this is the sentence the archive falsifies outright. (Box W1-34.)
- **86 of 102 link-definition targets re-relativized**, by bucket: `<!-- Root -->` 8 and
  `django_strawberry_framework/` 3, `tests/` 2, `examples/` 3, `scripts/` 3, `.venv/` 7 all gain one
  `../`; the 45 `docs/` siblings (43 `GLOSSARY.md` + `README.md` + `TREE.md`) **invert** and gain a
  level; `[next]` and the four sibling-spec definitions **shorten**; the 10 `<!-- External -->`
  sibling-checkout paths go `../../` -> `../../../`. Unchanged: the 15 `rationale*` siblings and the
  one `https://` URL.
- **15 `rationale*` definitions moved from `<!-- docs/ -->` to `<!-- docs/SPECS/ -->`** — path
  unchanged, group changed, because their target now lives in `docs/SPECS/`. Reason:
  `START.md` "Markdown link convention" (group = where the target lives), with the three-archived-sibling
  precedent measured in `### The group-relocation obligation the plan's table omitted`.
- `<!-- Root -->` re-sorted so `[workflow-django]` sits last rather than second. Reason: a pre-existing
  alphabetical-order defect at HEAD, corrected as a side effect of the deterministic rebuild rather
  than as a separate edit.

**In-file edits to `docs/SPECS/spec-044-debug_extension-0_0_14-rationale.md`** (672 lines, unchanged):

- **9 of 28 link-definition targets re-relativized**: 2 `<!-- Root -->` and 1 `<!-- examples/ -->` gain
  one `../`; the 1 `GLOSSARY.md#django-trac-37064-hardening` definition **inverts** to `../GLOSSARY.md#…`
  (the definition that keeps `check_spec_glossary.py`'s 42nd term reachable, its ref-id-vs-anchor
  mismatch preserved verbatim); `[next]` and `[spec-038]` **shorten**; the 3 `<!-- External -->` paths go
  `../../` -> `../../../`. Unchanged: the 18 `s44-*` definitions and `[spec-044]`.
- **19 definitions moved from `<!-- docs/ -->` to `<!-- docs/SPECS/ -->`** (the 18 `s44-*` plus
  `[spec-044]`), same reason as above.

**No prose other than the two path strings was touched in either file**, and no heading, anchor, in-page
link, ref-id, card id, or checkbox changed: headings hold at 35 and 20, in-page anchor occurrences at
200 and 2 with zero broken, definitions at 102 and 28 with zero unused and zero undefined (bar the
standing `"sql"` false positive), and the spec's 43 checkboxes remain **0** ticked.

**Status-line re-verification (`worker-1.md` `## Spec status-line re-verification`), W1-22.** Read
`:1-130` paragraph by paragraph — the discipline R2's Medium bought, since a declared range is not an
audited range until every paragraph in it is named. The header block reads consistently end to end and
the archive falsified nothing in it: `:3-5` "Built for `0.0.14` (card `DONE-044-0.0.14`) … completed /
owned", `:56-72` "was … carried the cut … recorded below rather than here", `:74`'s `Status:` line
"**COMPLETE (card `DONE-044-0.0.14`)** … owned and applied", `:104-107` "carries … as `shipped
(0.0.14)`", `:110-115` the deliberative-layer pointer (whose `[rationale]` definition this pass
regrouped, not repathed), and `:122-127`'s `## Key glossary references` keep. Every `[spec-038]` /
`[spec-041]` / `[spec-042]` / `[spec-043]` / `[rationale]` definition resolves from the **new**
location. The opener's `DONE-044-0.0.14` card id was left exactly as written, per R2's carried caution.
The only header-adjacent thing the archive did falsify is `:1103`'s self-reference, which is a Decision-1
body sentence rather than a status line, and it is fixed above.

**Deliberately not changed, each with its reason so the omission is a ruling and not a silence:**

- **The seven `[`docs/SPECS/NEXT.md`][next]` prose code spans** (spec `:90`, `:502`, `:1106`, `:1662`,
  `:2511`; rationale `:83`, `:597`) — the visible text is a repo-relative path that stays correct; only
  the definition shortens.
- **The `-terms.csv`'s contents** — measured to contain no `docs/`, no `.md`, and no `SPECS` string.
- **The three name-based citations at `:1562`, `:1613`, `:1924`** — R1 created them precisely because an
  ordinal does not survive a move; converting any back to a positional form was refused, as R1's
  hand-off requires.
- **The spec's 43 checkboxes stay `- [ ]`** (20 `## Slice checklist` / 14 DRY / 9 `## Definition of
  done`, 26 top-level) — `:74`'s `Status:` line is the single source of truth for release state, and all
  four archived `0.0.14`-era siblings ship 0 ticked. R2's settled handling, upheld by three reviews and
  unchanged by the archive.
- **The 42 orphaned `GlossarySpecMention` rows** — ruled to the catalog, not cleaned up locally.
- **Every other `docs/spec-*.md`** — seven live specs stay at `docs/` root on the maintainer's scoping,
  and `docs/spec-050-…:553`'s wrong `[spec-038]` target stays reported rather than fixed.
- **`docs/SPECS/NEXT.md` and `docs/builder/worker-0.md`** — outside every worker's writable set; the
  nine-plus-one site census is the deliverable instead.

### Final status

**`final-accepted`.**

The move is performed and proven in both directions: byte-identical content across the rename, and
every one of the 130 definitions resolving to a real file — and, for the 75 that carry an anchor, to a
real heading — from the new location. All 50 boxes are ticked with no over-tick and no silent
un-tick; the six box texts this pass's own measurement corrected — three `W1-*` assertions falsified,
one `W1-*` scope clarified, two `W2-*` wordings narrower than what landed — carry the measurement
beside each. Both relocation claims the item makes were re-proven from the tree rather
than read off Worker 3's acceptance. The escalated Medium is confirmed at its full population and
carried into the record precisely enough for the maintainer to act; the rejected Low's reason stands
and its figures were re-measured. Nothing R3 owns requires a further pass, and `revision-needed` would
route to a worker that cannot write either file the one open defect lives in.

Remaining for `bld-044-final.md`: R2's seven catalog items plus R3's three, and the build plan's R3
checkbox for Worker 0 to tick.

---

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
