# START.md — agent handbook

You're in `django-strawberry-framework`. For agents, not users. Read once, then [AGENTS.md][agents] (law; this file = terrain). Then go. [CLAUDE.md][claude-md] exists only to make you read both.

**Static reference.** Mechanisms, conventions, hazards that hold across releases. Never state: no version, no shipped list, no in-flight names, no counts a commit can change. State lives in [KANBAN.md][kanban], [TODAY.md][today], [docs/GLOSSARY.md][glossary]. Where a number matters, this file names where to read it. No session notes, cycle status, or "as of" facts here; a lesson lands only once release-independent.

## Reading order

1. [AGENTS.md][agents] — rules. Dense, numbered.
2. This file — repo, tooling, maintainer.
3. [docs/README.md][docs-readme] — consumer how-to.
4. [docs/TREE.md][tree] — module map + ownership.
5. [KANBAN.md][kanban] — in flight / next.
6. [GOAL.md][goal] — destination every card serves.

Also: [docs/GLOSSARY.md][glossary] = capability catalog w/ shipped/planned/deferred per anchor. [TODAY.md][today] = current capability via `products` app. [BACKLOG.md][backlog] = unscheduled ideas. [CHANGELOG.md][changelog] = maintainer-owned, never edit unless told. [README.md][readme] = public pitch.

## What this repo is

DRF-shaped Django integration for Strawberry GraphQL. Pre-`1.0`, one maintainer, fast iteration. Shipped surface = glossary's job, not this file's. Version single-sourced: `__version__` in `django_strawberry_framework/__init__.py` (hatchling reads it).

Upstream checkouts for cribbing (AGENTS.md L2): `~/projects/strawberry-django-main/strawberry_django`; `graphene_django` inside `~/projects/django-graphene-filters/.venv`. Behavior ← strawberry-graphql-django. Surface ← django-graphene-filters + DRF.

## How Rio communicates

Direct, decisive, reverses fast, expects same.

- Short imperatives. "Now do X." "Scratch that, Y." No hidden tone. Do the thing.
- Reverses decisions from a turn ago (moved example tests in, then straight back out; both right then). Roll with it; don't re-argue old reasoning.
- Pushback on a hidden flaw welcome, once. Surface, suggest better, defer. No lectures.
- No preamble, sycophancy, over-explanation. 12y Django + Vue.
- Status reply = result + what's broken + what's uncommitted. ≤3 sentences.

## Session rules you will forget

- **No `pytest` after edits.** Format only. Rio says "run tests" / "run the full pipeline" when wanted.
- After edits: `uv run ruff format .`, `uv run ruff check --fix .`, stop. No `pytest`, `manage.py check`, `uv build`.
- Rio commits. Never auto-commit unless explicitly asked. **NEVER `Co-Authored-By` or any attribution footer.** Message = change description only.
- **Commit auth covers ONE batch.** Doesn't carry to next batch/task, nor via a compaction summary. Rule is *no auto-commit*, not *never commit*; re-read AGENTS.md when a rule seems to forbid what Rio explicitly asks.
- **NEVER create/switch branches without explicit auth.** Commit request ≠ branch auth. Commit on current branch; flag oddities after. (Once branched "helpfully" → misrouted Rio's concurrent commit.)
- Before committing: `uvx pre-commit run --files <paths>`. Hooks check things ruff doesn't. See "Pre-commit and CI gates".
- Temp files → session scratchpad dir. Never repo, never bare `/tmp`.

## Concurrent sessions

Rio runs several sessions on this checkout, same branch, same time. Normal.

- Unexpected dirty/untracked files, commits you didn't make = other session. Never revert/"tidy". Never reset `examples/fakeshop/db.sqlite3` while another session may write it.
- `git add <path>` only; `-A` sweeps their WIP into your commit. Reverse too: your edits may land in THEIR commit; check `git log --stat` before assuming your work is unstaged. Swallowed file can be MIXED (their hunks + yours); back out hunk-wise, not file-wise.
- No `git stash` / `checkout --` / `restore` on shared tree. Diff your change vs `git show HEAD:<path>` written to scratchpad.
- `git mv` stages instantly; concurrent commit can adopt your rename while its content edits stay dirty. Rewrite content first vs plain `mv`, `git add` both together, verify `git log --stat` (swept rename vanishes from `git status`).
- Other session may rewrite main history (amend/rebase). Prove your commit landed: `git merge-base --is-ancestor <sha> HEAD`. Not memory.
- Commit out of a concurrently-dirty tree w/o touching their hunks: build intended blob (`git show HEAD:<path>` + your diff), `git hash-object -w`, `git update-index --cacheinfo`, commit index. Slow; stages only your bytes.
- `git diff --cached --name-status` before any `git add`: index may hold their staged work; one commit ships it under your message. If they staged whole tree, `git diff -- <path>` shows your file clean; use `git diff HEAD -- <path>`.
- Carve-out commit: first grep your new files' imports for symbols ABSENT at HEAD. Rewired onto their refactor → no standalone commit exists; leave dirty, say so.
- Before recommending push: `git rev-list --left-right --count origin/main...main`. "Tests failing" but local green → `gh run list` first; red job may not be a test job.
- Final-gate failure in committed code may be Rio's own rewrite of your fix. Diff your verified version vs HEAD before editing; broken test inside their in-flight refactor ≠ your regression. One collection ERROR in one test module drops coverage across every file its tests build schemas through → scattered misses usually = one broken module.
- Don't regenerate rendered docs while their feature work is mid-flight (publishes half-landed surface).
- Attribute dirty files by DIFF CONTENT, not "files my task touched". Regenerated doc/DB = CONSEQUENCE of a code change; belongs to whoever caused it.

## Toolchain

- **`uv`** owns env. `uv sync` = dev group; `uv sync --group pg` adds psycopg. Everything via `uv run`. Never `pip install` into `.venv`; `uv pip install` w/o `--python <path>` lands there.
- **`ruff`** format + lint (`pyproject.toml`: line 99, E501 graced 110, Google docstrings). `*.md` excluded from format: fenced blocks are verbatim examples.
- **`pytest`** + pytest-django/xdist/cov/asyncio. Config in `pytest.ini`, not pyproject. See "Tests".
- **`uvx pre-commit`**: `install` once per clone; `run --files <paths>` pre-commit; `--all-files` sweep.
- **`rg`** for search. Always print population size: empty grep ≡ grep that ran on nothing.
- **`gh`** for CI runs / Dependabot PRs. Workflows in `.github/workflows/`.
- **`docker compose -f docker-compose.postgres.yml up -d`** → local Postgres for `FAKESHOP_PG_DSN`.
- Interpreter pinned by `.python-version`. Shared `.venv` = NEWEST supported, not the floor.
- Subagents inherit plan mode → return a plan, not edits. Work inline or clear mode first.
- `ruff format`/`--fix` during a test run invalidates that run's coverage map. Format before/after, not during.

## Support matrix: floor and ceiling

Never state a version from memory. Read it:

| Axis | Floor | Ceiling |
|---|---|---|
| Python | `requires-python`, `pyproject.toml` | highest `Programming Language :: Python` classifier; CI "latest" cell |
| Django | `Django>=` pin, `[project].dependencies` | resolved `django` in `uv.lock`; `Framework :: Django` classifiers = tested majors |
| strawberry-graphql | `strawberry-graphql>=` pin (adjacent comment = why) | resolved entry, `uv.lock` |
| django-filter | `django-filter>=` pin | resolved entry, `uv.lock` |

Exact point a floor run installs = policy in [docs/builder/BUILD.md][build] "Floor verification"; moves together with `pyproject.toml`.

Django range spanning a Python-floor boundary → `uv.lock` carries TWO Django resolutions behind `python_full_version` markers. Check which one a given Python gets before claiming "latest Django".

Soft deps (never in `[project].dependencies`; tests cover present AND absent): `cryptography` (`Meta.cursor_field` keyset only), `channels[daphne]` (ASGI router), `django-debug-toolbar` (toolbar middleware), `djangorestframework` (`SerializerMutation`). Absence = `sys.modules[name] = None` sentinel via `tests/_soft_dependency.py`.

CI: exact-floor cell + latest cell every push/PR; latest owns coverage gate. Full matrix + sharded-DB variant = manual dispatch only. Floor cell = API-compat probe, never a deployment recommendation.

**Floor is executed, never reasoned.** Newer source / changelog / classifier ≠ answer. Throwaway venv outside repo, explicit interpreter, focused tests:

```shell
uv venv /tmp/dsf-floor --python <floor python>
uv pip install --python /tmp/dsf-floor/bin/python -e . --group dev
uv pip install --python /tmp/dsf-floor/bin/python 'django==<floor>' 'strawberry-graphql==<floor>'
/tmp/dsf-floor/bin/python -m pytest <focused scope> --no-cov
```

Floor values from BUILD.md "Floor verification" at run time.

Never mutate shared `.venv` for a matrix check; silently changes floor for every concurrent session (`UV_PROJECT_ENVIRONMENT` redirects `uv sync`/`uv run`, NOT `uv pip install`). Restore w/ `uv sync --frozen`. Launch pg tier as `uv run --group pg pytest` (group pinned at launch; a parallel `uv sync` strips psycopg mid-run). Postgres CI's `uv sync --upgrade-package Django` REWRITES `uv.lock` if copied locally → revert lock after.

Change depends on WHICH upstream attribute/body (wrapped seam, patch target)? Enumerate every published release floor→latest, fetch each wheel, grep the module. Installed version ≠ consumer's. Pin result as version→names table beside the contract + a SET of audited bodies so an unseen third fails closed. Upstream bump "regression": read WHICH assertion failed in a multi-assert test; stale SQL-text expectation looks identical to a broken boundary.

## Tests: where, how

Four trees, one `pytest.ini`, one command: `uv run pytest`.

| Tree | Target | Style |
|---|---|---|
| `tests/` | package | in-process; fakeshop models OK as fixtures; `tests/base/` = exactly `test_init.py` + `test_conf.py` |
| `examples/fakeshop/test_query/` | any package line reachable by a real query | live `/graphql/` HTTP via `examples/fakeshop/graphql_client.py`; **FIRST place to add a test** |
| `examples/fakeshop/apps/<app>/tests/` | one app's models/admin/services/commands | in-process `schema.execute_sync`; packages `apps.<app>.tests` |
| `examples/fakeshop/tests/` | project/config only (urls, settings guard, schema export) | not a package |

- **Live-first, both verdicts.** Reachable from a real query → MUST be in `test_query/`. Promoting to live DELETES the package-only stand-in, same change, after proving redundancy empirically. A plan can pin a predicate's rejection live and leave acceptance package-only: check which VERDICT each live row proves. "Fixture can't reach it" = fixture gap, not unreachability. Live-tier README under-enumerates its suites; silence ≠ "no such suite".
- **First line of every catalog/auth test:** `seed_data(N)` / `create_users(N)` from `apps.products.services`. Library acceptance tests: inline `Model.objects.create(...)`.
- **Parallel default.** `addopts = -v -n auto --dist loadscope --cov --cov-report=term-missing`. `loadscope` keeps a module on one worker (registry-isolation fixtures; expensive live schema rebuild). Worker = process w/ own registry + in-memory SQLite. Single test: `uv run pytest -n0 tests/test_x.py::test_name`.
- **Warnings are errors** (`filterwarnings = error`). Never weaken. `tests/conftest.py` closes async SQLite connections that would leak `ResourceWarning`; root `conftest.py` same for Postgres.
- **Coverage:** `fail_under = 100`, `django_strawberry_framework` only. Example apps/tests run, never count. `pragma: no cover` only for runner-unreachable branches. Statement coverage can't see fail-open EXPRESSIONS (`max(x, 0)`, `getattr(..., default)`, `x or fallback`, broad `except`); find by reading, BUILD.md "Fail-open shapes".
- **Order independence is a contract.** Fakeshop schema composes all apps; harness reloading one app after `registry.clear()` → order-dependent `LazyType KeyError` / `DuplicatedTypeName`. Use `examples/fakeshop/schema_reload.py`; adding an app → grep WHOLE test tree for private schema-module lists, sync each. Invisible in isolation, single-worker, `-n0`; verify w/ FULL parallel sweep.
- **Channels communicator tests:** `django_db`-marked + `wait()`, else order-dependent flake.
- **Postgres surfaces pk-magnitude bugs SQLite hides.** SQLite per-test DBs = single-digit pks forever; PG sequences never rewind. PG-tier test failing order-dependently but passing alone = pk-magnitude bug before pollution. Repro: `ALTER SEQUENCE ... RESTART WITH <big>` in one test.
- **Attribute a failing SELECTION at pristine HEAD.** Pollution rides the selection; rows failing in a 3-module run pass alone. Re-run same selection vs `git archive HEAD` in scratchpad, never by reverting files one at a time.
- **Uncovered line = claim nobody tested.** Read the claim before a test blesses it; branch may be uncovered because its reasoning is wrong. Two agents disagree on a boundary → settle vs live code, never average, never confidence.
- **Soft-dep absence:** `sys.modules[name] = None` via `tests/_soft_dependency.py`. Never patch `builtins.__import__` (guards use `importlib.import_module`; block silently passes).
- **Env knobs** (`examples/fakeshop/config/settings.py`): `FAKESHOP_SHARDED=1` → two shard DBs, un-skips sharded tests. `FAKESHOP_PG_DSN=postgres://...` → `default` = Postgres, un-skips `@pytest.mark.pg` (needs `--group pg`). `DJANGO_STRAWBERRY_KANBAN_DB=<path>` → render scripts read a COPY of board DB. Sharded ⊥ PG.
- **CI tiers:** `django.yml` sqlite, every push/PR, owns coverage. `postgres.yml` manual, path-disjoint shards, oversubscribed workers, no coverage. `kanban-pages.yml` republishes board to Pages when INPUTS change. `dependency-audit.yml` osv-scanner over `uv.lock`, daily. Dependabot rewrites `uv.lock` + action SHAs weekly; re-read its branch after every rebase (floor-raise vs lock-only can flip).

## Pre-commit and CI gates

Local hooks, `.pre-commit-config.yaml`, run order. All via `uv run` (shared ruff). Config file wins over this list.

1. **kanban-tracked-path-constants** (`scripts/build_kanban_tracked_path_constants.py`) — REWRITES constants module from `git ls-files`. Add/delete a tracked package/test file w/o regen → stale → hook rolls back EVERY later commit until a constants-only sync commit. `always_run` (deleted paths never in staged list). Sees a new file only once STAGED; `--all-files` before `git add` proves nothing. Unblock: commit the constants file alone (hook's `files:` doesn't match it).
2. **source-layout** (`scripts/check_trailing_commas.py --fix`) — trailing-comma explode-at-threshold (4; 2 in `models.py`), ASCII-only `.py`, `.md` link-def scaffold, JSON/GraphQL brace explosion. Auto-fixes; a rewrite fails the run so you re-stage. ASCII rule `.py`-only; em dashes fine in `.md`.
3. **ruff-format**, 4. **ruff-check --fix**.
5. **check-kanban-anchors** (`scripts/check_kanban_anchors.py`) — card↔card slug, card↔glossary anchor, render-id collisions. Reads DB → fires on a retitle no staged file names.
6. **check-citations** (`scripts/check_citations.py`) — every `path::Symbol` in first-party source + board must resolve. Runs last, whole tree (a rename rots citations in files you aren't committing). `path::Symbol` ONLY: `path #"substring"` + `docs/` prose out of scope; citation wrapped across two lines invisible.

CI `lint` job: source-layout + citations in `--check`, `ruff check` / `ruff format --check`, then `--check` on every generator (`build_kanban_md`, `build_kanban_html`, `build_glossary_md`, `build_tree_md`). Hand-edit to a rendered doc goes red THERE, not locally.

`--check` measures WORKING TREE. Passes in a dirty tree w/ stale HEAD → CI red, local green. Measure HEAD: copy `git show HEAD:examples/fakeshop/db.sqlite3` to scratchpad, run generator w/ `DJANGO_STRAWBERRY_KANBAN_DB` pointing at it.

## `scripts/`

`uv run python scripts/<name>.py`; `--help` = flags + defaults. Module docstring is the manual; this is the map.

| Script | Use |
|---|---|
| `build_kanban_md.py`, `build_kanban_html.py` | render `KANBAN.md` / `KANBAN.html` from kanban DB (`--check`; `--md`/`--html` write elsewhere). HTML Vue shell hand-edited; only data block regenerates |
| `build_glossary_md.py` | render `docs/GLOSSARY.md` from glossary DB |
| `build_tree_md.py` | render `docs/TREE.md` from module docstrings + board predicted-path rows; missing module docstring fails it |
| `build_kanban_tracked_path_constants.py` | hook 1; run after adding/removing any tracked package/test file |
| `check_trailing_commas.py` | hook 2; `--check` CI, `--fix` local; owns `EXEMPT_MD_SCAFFOLD_NAMES`, `LINK_DEF_CATEGORIES`. Default = repo-wide AUTO-FIX → always pass explicit paths (else rewrites other session's untracked files) |
| `check_citations.py` | hook 6; `--check` CI |
| `check_kanban_anchors.py` | hook 5 |
| `check_spec_glossary.py --spec <path>` | spec's `-terms.csv` → real glossary anchors; `--auto-link` rewrites inline mentions (NEXT.md) |
| `check_alpha_parity.py` | every non-internal Alpha card carries parity link + justification |
| `prove_failability.py <manifest.json>` | mutate boundary, run, restore, prove by byte compare. THE way to prove a test can fail |
| `review_inspect.py <file> --output-dir docs/shadow` | AST-only overview + stripped source (`--all` = package); never imports |
| `review_historical_package_snapshot_at_commit.py <sha>` | package snapshot at commit → `docs/shadow/current/` |
| `review_changed_python_diffs_against_head.py <sha>` | stripped per-file diffs commit→HEAD → `docs/shadow/old|new|diff/` |
| `bug_hunt.py` | generates `docs/bug_hunt/bug_hunt-<ver>.md` progress file (HUNT.md) |
| `list_package_python_changes_by_commit.py` | package `.py` files per commit, for spec attribution |
| `clean_up.py` | deletes cycle scratch (`docs/shadow/`, `temp-tests/`, `worker-memory/`, `bld-*.md`, `bug_hunt.*.md`). `bld-*.md` glob also eats deliberately-kept finals + other cycle's live artifacts → never use to tidy a cycle; delete by explicit path |
| `bench_plan_cache.py`, `bench_optimizer_walk.py`, `bench_nested_fetch.py` | optimizer benches (plan cache warm/cold; walker cold path; nested-fetch strategies on PG) |
| `capture_pg_predicate_explain.py` | row-preserving-predicate `EXPLAIN` artifact from actually emitted SQL |
| `_kanban_lib.py`, `_bench_common.py` | shared plumbing, not entry points |

## Rendered docs — fix the source

Generated; hand edits clobbered next render + CI generator `--check` red:

- [docs/TREE.md][tree] ← module docstrings + kanban DB predicted-path rows.
- [docs/GLOSSARY.md][glossary] ← fakeshop `glossary` app DB (`GlossaryTerm` bodies). Shipping slice folds behavior in via DB, then renders.
- [KANBAN.md][kanban] / `KANBAN.html` ← fakeshop `kanban` app DB: `BoardDoc` = prose, `Card` = identity, `CardItem`/`CardReference`/`ParityClaim` = bodies + links.

```shell
uv run python examples/fakeshop/manage.py shell -c "<ORM edit>"
uv run python scripts/build_kanban_md.py && uv run python scripts/build_kanban_html.py
uv run python scripts/build_glossary_md.py && uv run python scripts/build_tree_md.py
```

- `examples/fakeshop/db.sqlite3` = tracked source for both apps + concurrent-writer hotspot. Same-size binary diff ≠ no-op: compare `iterdump()` by table vs `git show HEAD:`, leave foreign rows, disclose what rode along. Never `git checkout` it as "tool drift". Hand-edited render? Re-render, compare bytes; never infer from dirty list.
- DB edits: script in scratchpad piped into `manage.py shell`. `shell -c '<single-quoted>'` can't carry apostrophes → mangled chars in render. Guard inserts w/ marker-absence assert (re-run can't duplicate).
- DB stores only each bullet's FIRST line; multi-paragraph items lost on import. A claim you expect on the board may never have been imported.
- Never write literal `{{card_ref:N}}` into stored prose, even in backticks (md render resolves server-side, HTML shell by numeric index). Card ids in prose = FK-backed placeholders, can't rot; only literal ids typed in text are a sweep population.
- `KANBAN.md` is in citation gate corpus: `path::Symbol` in a card item checked every render, must name DEFINING class, can't quote another doc's illustrative citation.
- Two glossary gates, different inputs: `check_spec_glossary.py` → RENDERED `GLOSSARY.md` headings; `manage.py import_spec_terms --check` → DB. A rendered H2 may be a section heading w/ no `GlossaryTerm` row; model forbids two terms per anchor → collapse CSV to one row per anchor before card closes.
- `Card.uuid` ROTATES on renumber; `card_id` = property, not column. Pre-map by pk/title, retarget refs in place, use `services.move_card_number`. Done cards always contiguous, completion order.
- Card numerals rot in 3 grammars: card ids, `spec-NNN` stems, bare prose numerals (incl. `CardReference.raw_text`, `Card.planning_note`). Renumber sweeps all 3 + regenerates `docs/TREE.md`.
- Board items cite docs by `path #"substring"`. Move/reword quoted text → broken, ungated (`check_citations.py` is `::Symbol`-only). Grep `spec-<NNN>` + quoted substrings across `docs/` BEFORE moving text. Cite stable neighbourhood, never the phrase a catalogued fix will rewrite.
- `is_blocked` ignores Done targets: `blocked_by` → shipped card renders unblocked. Retype to `dependency`, reword.
- `BigAutoField → Int` + duplicate GraphQL name in kanban schema: intentional, load-bearing. Don't "fix".

## Agentflows

Five standing process docs. Rio invokes by name ("run the builder on the active spec", "start a DRY cycle"); none self-starts. All re-read AGENTS.md + this file first, none commit, each closes own scratch.

| Flow | Doc | Does | Per-cycle artifacts |
|---|---|---|---|
| **Spec authoring** | [docs/SPECS/NEXT.md][next] | strict ordered steps: orient, summarize, normalize board to exactly one WIP card, write `docs/spec-<NNN>-<topic>-<0_0_X>.md` + `-terms.csv`, anchor terms to glossary, archive prior specs → `docs/SPECS/` (+`appx/` companions), rewrite every xref | new spec at `docs/` |
| **Builder** | [docs/builder/BUILD.md][build] + [ARTIFACT.md][artifact] + `worker-0..3.md` | spec slice by slice. W0 (main thread) dispatches fresh subagents per pass: W1 plans/owns spec/final-verifies, W2 implements, W3 reviews + DRY. Artifact `Status:` drives dispatch. Pre-flight moves spec rationale → `-rationale.md` (smaller spec per spawn). Failability proofs, floor verification, hot-path budget, review rounds under ownership partition, cross-slice integration, closeout | `docs/builder/build-<NNN>-*.md` (plan), `bld-*.md`, `temp-tests/`, `worker-memory/` |
| **Review** | [docs/review/REVIEW.md][review] | one package file at a time: understand, verify w/ scratch tests, improve; folder + project integration passes; final `uv run pytest` gate | `docs/review/review-<ver>.md`, `rev-*.md`, `temp-tests/` |
| **DRY** | [docs/dry/DRY.md][dry] | system-wide duplication hunt; mandatory probing matrix; single-edit-site test; `docs/dry/export_dry_review.py plan|audit` = plan + evidence dossier | `docs/dry/dry-<ver>.md`, `temp-tests/` |
| **Bug hunt** | [docs/bug_hunt/HUNT.md][hunt] | autonomous two-role (W0 verifies, W1 hunts/fixes) over shadow snapshot; `dicta.md` = maintainer probing questions | `docs/bug_hunt/bug_hunt-<ver>.md` |

Shared mechanics:

- **Isolation non-waivable.** Author never approves own code. Workers never read each other's `worker-memory/` mid-cycle; all info via artifact + diff.
- **Claims proven mechanically.** Passing suite = evidence only if it could fail (`prove_failability.py`). Review's prescribed fix = hypothesis. Finding's grep vocabulary ≠ its population; re-derive a catalog before acting.
- **Builder corpus may not grow net** (BUILD.md "corpus ratchet"): any edit to `BUILD.md`/`ARTIFACT.md`/`worker-*.md` names bytes retired, `wc -c`. Never edit a process doc while a worker is mid-pass. Role files = pointer + role delta, never restated procedure.
- **Failability aggregates OUTSIDE the guard under test.** Inside, guard absorbs the failures being measured; plausible-wrong count graded by nobody.
- **Harvesting items from a doc about to be deleted** = enumerate-and-tick over source's own numbering, then grep each item at destination w/ a NAMED owning card. Section sweep looks complete, leaves items unhomed.
- **Per-cycle scratch closes w/ cycle.** `review-*.md`, `rev-*.md`, `dry-*.md`, `bld-*.md`, `bug_hunt-*.md`: exempt from `path::Symbol` rule (raw `path:NN` OK), no style cleanup. Include in repo-wide greps for drift; edit only if cycle in flight. `clean_up.py` removes generated ones only.
- **Closeout consistency.** Shipped card: realign opener + `Status:` (boxes stay unticked; Status = truth); correct wrong Decision/Test-plan/DoD prose. Clean `git status` ≠ finished cycle; read artifact `Status:` chain.

## docs/

| Path | Purpose |
|---|---|
| `docs/README.md` | consumer how-to (install, quick start, read/write, transport, production profile) |
| `docs/GLOSSARY.md`, `docs/TREE.md` | rendered, see above |
| `docs/spec-*.md` (+`-terms.csv`, `-rationale.md`) | THE one in-flight spec + companions; invariant = exactly one WIP spec at top level |
| `docs/SPECS/` | archived specs + `NEXT.md`; `appx/` = their companions. Link defs for `appx/` still under `<!-- docs/SPECS/ -->` |
| `docs/builder/` | builder flow: `BUILD.md`, `ARTIFACT.md`, `worker-0..3.md` (tracked standing); active `build-*.md` + `bld-*.md` (tracked, active cycle only); `DONE/` (closed plans); `temp-tests/`, `worker-memory/` (untracked scratch) |
| `docs/review/` | `REVIEW.md` + per-release `review-<ver>.md`. Committed truth: never bulk-delete/overwrite; restore `git checkout HEAD -- docs/review/` |
| `docs/dry/` | `DRY.md`, `export_dry_review.py`, `dry-<ver>.md` |
| `docs/bug_hunt/` | `HUNT.md`, maintainer `dicta.md` (stays), generated `bug_hunt-<ver>.md`, `pbugs.md` |
| `docs/shadow/` | regenerable static-analysis output; sibling folders, one owning script each (`current/` ← snapshot; `old|new|diff/` ← diff). Read-only; never commit or cite its line numbers |
| `docs/feedback*.md` | maintainer review inputs for in-flight work. Staged WITH the work they drove; never named in commit message, code, or DB |
| other loose `docs/*.md` | standing design records for subsystems that outgrew a spec; each opens w/ its own purpose statement |

## Example project

`examples/fakeshop/` = acceptance fixture + board DB host. **Never deploy**: `DEBUG=True`, checked-in `SECRET_KEY`, GraphiQL, toolbar, deliberate `permission_classes = []` demos. Settings refuse to load w/ `DEBUG` off.

- Apps: `library` (primary acceptance: FK/reverse FK/O2O/M2M, Relay, optimizer hints, FilterSet/OrderSet on every type), `products` (canonical consumer app, TODAY.md; all mutation flavors), `scalars` (converter table, file/image, `Upload`), `accounts` (session auth), `kanban` + `glossary` (docs-as-data).
- Commands: `seed_data`, `create_users`, `delete_data`, `delete_users`, `seed_shards` (products); `import_card_files --kind changed|predicted` (kanban); `import_spec_terms` (glossary).
- `config/schema.py` composes all apps into one `DjangoSchema`. Change app list → sync every schema-module list harnesses carry (`schema_reload.py`, test READMEs).
- `graphql_client.py` sync-only; async suites owe stated exemption + `django_db(transaction=True)` + registered types.
- Choices = `TextChoices` (`library/models.py`); text columns = `TextField`.

## Instruments that lie

Each produced a clean-looking pass while measuring nothing. Check instrument before reading.

- **zsh word-splitting.** `for f in $FILES` = ONE iteration, whole string; grep errs to stderr; sweep prints nothing ≡ clean repo. Array: `files=(${(f)"$(...)"})`. Quote globs (unmatched glob aborts). Always print population size. No `timeout` here. Multi-file sweeps: `uv run python - <<'PY'` heredoc, assert the count.
- **Shared sqlite cursor.** One cursor for outer `sqlite_master` loop + inner query → outer result set discarded after table 1 → "no hits, 0 skipped". `.fetchall()` outer first; print tables/columns examined; positive control (rendered artifact carries the string ⇒ DB does).
- **Positive-vocabulary census.** Sweep for `only`/`sole`/`no other` misses `every`/`all`/`each`. Both polarities. Don't swap a rotted census for a fresh one: quantify over the file's own closed set (`_meta.local_fields`), not a population it can't see.
- **`git log -S<symbol>`** fail-open for "when did this ship" if symbol had an earlier name. Attribution from it = hypothesis.
- **`for` loop inside one test = ONE node id.** Widening loop never raises failability count above 1; parametrize. Never assert cardinality fixture size can satisfy by accident; assert id-list membership.
- **`--check` in dirty tree** measures working tree (see gates).
- **Control that cannot fail** ≡ passing proof; control that didn't run ≡ one that passed. Control mutation from EXECUTABLE code (docstring token can't move a docstring-stripped digest); break it, watch fail, restore. Comment/docstring-only edit owes INVERSE proof: AST identity w/ docstrings stripped.
- **Count right in every digit, wrong in SUBJECT.** Focused-run scope promoted to "what the card owns" passes arithmetic. State owned population + run scope separately. Stub's lost contract often in a deleted planning doc: `git show <commit>^:<path>`.
- **Round's self-reported deferral = claim.** Re-derive before homing.
- **Derived descriptions outlive sources.** Reconciliation defects = false descriptions of findings, not missed facts. Describe by content, never line number.
- **Partial claim fix = dominant residual defect.** One spelling fixed, parallel site (other README, glossary body, board item) still live → cycle reopens. Shortest DISTINCTIVE phrase, count occurrences (not lines: two hits/line read as one), prove retirement = 0.
- **Green checker = evidence only for what it reads.** Two gates agreeing ≠ corroboration when one can't see the other's failure. State instrument input before trusting output; state PATTERN as parameter of any published figure.
- **Enumerate, never grep-count, before writing.** Assert every site exists before touching any; partial match aborts w/ nothing written.
- **Retiring a per-cycle artifact strands inbound refs.** Same pass: de-link to code span keeping prose, or retarget standing pointer at `git show <commit>:<path>`. Re-audit orphaned defs / undefined refs.

## Style Rio cares about

- **Meta classes on every consumer surface.** Stacked Strawberry decorators on a consumer-facing class = strawberry-graphql-django API = the reason this package exists. Strawberry = engine; DRF = shape.
- Model text fields = `TextField`, never `CharField`, even short. Codified in example models.
- **No process provenance in code or standing prose.** Comments/docstrings/test names/error strings state the invariant, never how the change came to be. Banned: severity labels (High/P0/H1), review-round/worker attribution, DRY-pass/slice numbering, plan/commit banners, board residue, review-doc filenames, "as of 0.0.N", "previously". Removed attribution carried the WHY → restate as one plain clause from the code. Kept: spec decision pointers, glossary anchors, upstream tickets (Django Trac, Strawberry issues, RFCs, CVEs), audited-release-range vocabulary, live `TODO(spec-NNN slice N)` anchors. Verify a label vs its spec before deleting.
- Source refs: `path::QualifiedName`, `path::QualifiedName #"unique substring"`, `path #"unique substring"`. Never `path:NN` outside per-cycle scratch. `#"substring"` breaks on reflow AND reword, ungated: quote text on ONE source line; never wrap a `path::Symbol` across lines (shorten prose, not path); after editing a cited file, sweep every citer as POSTCONDITION. Rationale move breaks citations in OTHER specs while links still resolve: grep `spec-<NNN>` across `docs/` before, repair same pass. Cite contract by CONTENT, never ordinal ("shape 4"); heading rewrite strands every ordinal.

## Reconciling a spec with the tree

Specs = contracts concurrent work silently falsifies.

- **Verify `Status:` vs tree before building from it.** PLANNED spec can be half-shipped by concurrent DRY work. `Status:` line = truth; checkboxes stay unticked by convention.
- **Citation proves symbol, not sentence.** Open body, check the specific asserted property (query count, plan decision, SQL fragment, wire shape). Vanished test ≠ dropped deliverable until you grep live-tier docstrings; replacement usually names ancestor.
- **Five homes per contract:** Decision, slice checklist, `## Edge cases`, `## Test plan`, `## Definition of done`. Redundancy designed; two disagreeing = defect. Cross-checking them = the one instrument no single slice runs. Enumeration = count claim w/o number; count members.
- **Doc quotes a generated body → diff quotation vs render.** A "quotation" existing nowhere in the render can be sole warrant for a superseded framing.
- **Sweep both files of a pair.** Sweeping only the edited file leaves partner (other README, spec companion) falsified; blanket rewrite can hit the one sentence DESCRIBING the old spelling. Never write present-tense byte/line count of a file a later slice edits.
- **Gate's name ≠ its coverage.** `check_spec_glossary.py` compares term + anchor only; `notes` prose beside them drifts ungated. Read what a gate compares before trusting green.
- **Bare `Decision N` / `DoD N` = repo-wide convention, not defect.** Grade by ANCHOR presence, never distance: defect only when nothing on the reader's path establishes which spec.
- **Test plan can specify an unrunnable test** (`aclose()` on never-advanced async gen enters no `finally`). Check mechanism vs runtime before pinning a row. Later work falsifies a card's DoD → amend the CARD; spec silently reinterpreting it leaves board demanding the opposite.
- **Stale-sentence taxonomy:** code moved / doc moved / count's subject changed / FALSE ON ITS OWN DATE. Only the last needs no code change; check w/ `git show HEAD:` before blaming the move.

## Verified and rejected — don't re-raise

Investigated, explained, kept. Skip when sweeping.

- **`SCALAR_MAP[models.BigAutoField] = int`, not `BigInt`.** 32-bit `Int` cap → graphql-core rejects out-of-range pks at boundary, never reach DB / overflow param binding; M2M/FK existence path relies on it.
- **`finalize_django_types()` allows two types w/ one GraphQL name.** Finalize = process-global; collision = per-schema; Strawberry's own duplicate-name error at schema build is the accurate catch. Real broken case (two field names camel-casing to one) already fails loud in field audits.
- **`FilterSet._iter_visibility_steps` seeds child branch from child filterset's own `_default_manager`**, not connection field's `initial_queryset(target_type)`. Owner binding lets target model be strict SUBCLASS of filterset model; seeds differ in a visibility seam.
- **Generated `Prefetch` `to_attr` never contains `__`.** Django splits `prefetch_to` on it; descent silently breaks; only executing catches it. Grammar = `$` delimiter, `_`→`$` escape; read w/ `getattr`/`setattr`.
- **Cascade flips that look like bugs:** cycles raise, `fields=[]` = re-entry escape, MTI parents included, GFKs preflighted, unregistered relation target fails loud. Read glossary before "fixing".
- **Visibility boundary = sealed-execution queryset, not blacklist.** Prove-then-clone was whack-a-mole; never reintroduce a blacklist. Process-wide monkeypatching unsupported; fingerprint ≠ trust boundary.

## Markdown link convention

Every .md w/ cross-file links = **reference-style**: body `[text][ref-id]`; all defs in one bottom block. Exempt: [AGENTS.md][agents], [CLAUDE.md][claude-md] only (`EXEMPT_MD_SCAFFOLD_NAMES` in [scripts/check_trailing_commas.py][check-commas]); its `source-layout` hook enforces scaffold on every other .md + auto-appends missing markers. Don't hand-fight it. Specs additionally: [scripts/check_spec_glossary.py][check-spec-glossary] validates project terms → real `GLOSSARY.md` anchors, inline + reference forms.

Block opens `<!-- LINK DEFINITIONS -->`, then all 10 group headers, this order, present even empty:

`<!-- Root -->`, `<!-- docs/ -->`, `<!-- docs/SPECS/ -->`, `<!-- docs/builder/ -->`, `<!-- django_strawberry_framework/ -->`, `<!-- tests/ -->`, `<!-- examples/ -->`, `<!-- scripts/ -->`, `<!-- .venv/ -->`, `<!-- External -->`.

Defs alphabetical within group: `[ref-id]: path/from/this/file`.

Why: file moves → inline uses untouched; only bottom paths re-relativize. ~75% cheaper than scattered `](path)`.

Group = where TARGET lives, not source. `examples/fakeshop/README.md` → `docs/GLOSSARY.md` goes under `<!-- docs/ -->`. Empty groups stay (one-scan "links to nothing in `tests/`").

Ten headers = closed list (`LINK_DEF_CATEGORIES`); subdir shares parent's group. `docs/SPECS/appx/` defs under `<!-- docs/SPECS/ -->`.

Stays inline: URLs; in-page anchors (`](#heading)`); anything in fenced code.

New xref: `[text][ref-id]` inline + `[ref-id]: path` in correct group, alphabetical, path from source file's dir. No drift back to `](path)`.

Moving a .md: only bottom paths change. Disk-exists-check each path, but that alone is fail-open: same-named file one level up MASKS depth rot (`../README.md` from a subdir resolves to `docs/README.md`). Also check each def's group header + label vs intended target; every `][label]` has a def, every def a use; sweep bare backticked sibling filenames (a move into `DONE/`/archive breaks those too). GitHub slug: lowercase, drop backticks, strip non-word except hyphens, each surviving space → its OWN hyphen (dotted version → `007`; em-dash heading → double hyphen). Don't collapse whitespace runs in a verifier; strip fenced blocks + code spans before sweeping.

## AGENTS.md

Editing it: dense. No blank lines, no periods, no code blocks.

## Past mistakes

- **Don't pre-populate `conf.py` w/ future settings.** Rio trimmed it hard. Key lands with its feature.
- **Don't restore deleted files on assumption.** Ask. (Restored `schema.py` + `test_schema_smoke.py` Rio had removed on purpose.)
- **Don't add example-app coverage to the gate.** Rolled back once. Package = 100%; example exercises via real flows, doesn't gate.
- **Don't second-guess `field_name` patterns** in files translated from `django-graphene-filters`. Mirror old shape.
- **Don't over-harden a rule after context loss.** *No auto-commit* ≠ *never commit*. Re-read AGENTS.md when a rule seems to forbid what Rio asks.
- **Don't auto-revert a live-tree regression.** No-revert rule covers DIRTY files you didn't author; regression in COMMITTED code → root-cause fix, not checkout.
- **No defer-the-real-fix sequencing.** No test-only fix when prod code is the wrong abstraction, no `pragma: no cover` workaround, no follow-up card as substitute.
- **Rule w/o gate rots.** Repairing a forbidden form → root-cause fix = the missing gate, not the sites. Gate fails open one level up at every level: corpus silently empty (`git ls-files` in ignored dir exits 0, empty stdout), required-file list shrinks, region bounds unpinned. Ask for the next level up before the reviewer does.
- **Item routed forward w/o NAMED owner dies.** Home every deferred finding on a specific card, in DB, before closing.
- **Surface w/ no owning spec silently inverts the specs describing it.** Spec heading rewrite strands every prose citation.
- **Reconciliation slice introduces contradictions it can't see.** Integration pass owes the divergence INVENTORY, not the consistency of the discharging text.

## Strategic advice

- Package rebuilds the overlap of `graphene-django` ∩ `strawberry-graphql-django`, DRF-shaped. Both provide it = foundational. One = optional, later spec.
- Behavior ← `strawberry-graphql-django` (esp. optimizer's downgrade-to-`Prefetch` when target type has custom `get_queryset`). Surface ← `django-graphene-filters` Meta API. Be honest which side a decision falls.
- Build in slices; fork a subsystem to its own spec when a slice passes ~one module. Mechanics: [docs/builder/BUILD.md][build].
- Resist scope creep. Early versions of this file deferred filters, orders, aggregates, permissions, full connection field; each later shipped in its own slice. That's the point. What's still deferred = board's job. No "while I'm here".
- Coverage is a feature. Line uncoverable via the example = smell (too-clever code / wrong abstraction).
- Security: cancel request ≠ termination protocol; lock private to one layer ≠ synchronization contract. Boundary is transactional, not lexical; wrapper must PERMIT, not filter.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: AGENTS.md
[backlog]: BACKLOG.md
[changelog]: CHANGELOG.md
[claude-md]: CLAUDE.md
[goal]: GOAL.md
[kanban]: KANBAN.md
[readme]: README.md
[today]: TODAY.md

<!-- docs/ -->
[docs-readme]: docs/README.md
[dry]: docs/dry/DRY.md
[glossary]: docs/GLOSSARY.md
[hunt]: docs/bug_hunt/HUNT.md
[review]: docs/review/REVIEW.md
[tree]: docs/TREE.md

<!-- docs/SPECS/ -->
[next]: docs/SPECS/NEXT.md

<!-- docs/builder/ -->
[artifact]: docs/builder/ARTIFACT.md
[build]: docs/builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->
[check-commas]: scripts/check_trailing_commas.py
[check-spec-glossary]: scripts/check_spec_glossary.py

<!-- .venv/ -->

<!-- External -->
