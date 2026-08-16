# Package build plan: version_release_alignment / 0.0.4 (012) — residual-completion cycle

Spec source: `docs/SPECS/spec-012-version_release_alignment-0_0_4.md` (already archived; card `DONE-012-0.0.4`)
Rationale companion: `docs/SPECS/appx/spec-012-version_release_alignment-0_0_4-rationale.md` — **does not exist**; creating it is this cycle's first obligation.
Terms companion: `docs/SPECS/appx/spec-012-version_release_alignment-0_0_4-terms.csv` (exists, 1 row, one row per anchor, `check_spec_glossary` green: `OK: 1 terms`).
Target release: `0.0.4` (shipped; this cycle bumps no version and lands no feature).
Build rule: one item at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every item must justify shared/duplicated patterns before merging.
Ownership partition: none; sequential items. R1 and R2 both write the spec file, so they could not run concurrently even if the rest were disjoint.
Hot-path declaration: none. Both items write Markdown only; no package source and no test is in any item's writable set.
Floor-verification scope: **none.** No item touches a Django / Strawberry / channels integration seam — no item touches executable code at all.
Pre-flight: passed on 2026-08-15 with two recorded deviations (steps 3 and 5, below); baseline: **dirty with concurrent sessions' work — 93 paths, none of them this cycle's**; cleanup: **nothing deleted or cleared** (deviation, below); memory files namespaced per cycle.

## Why this cycle exists

Card `DONE-012-0.0.4` shipped at `0.0.4`, so the code is not in question as *new* work. Three obligations, in the maintainer's framing:

1. **Nothing was skipped in the code.** Everything spec-012 promised must be present at `HEAD`, and anything promised and never delivered is a defect this cycle fixes.
2. **Later work that changed the shipped shape is legitimate — but the spec must say so.** Where a later card corrected, superseded, or completed something spec-012 owns, the spec is rewritten to state the **current** contract directly. It never narrates the change (`docs/builder/BUILD.md` `## Spec rationale extraction`).
3. **The explanation goes in the rationale, not the spec.** What changed, why, which commit caused it, and what the spec may no longer claim — all of it lands in the rationale companion, keyed to the spec section it belongs to.

Spec-012 is a **card-snapshot stub**: 1,651 bytes (the repository's second-smallest tracked spec, measured by the spec-007 cycle), no Decisions, no slice checklist, no rationale companion at all. So obligation 3 here is a creation, not a completion, and obligation 2 turns on one thing the stub gets structurally wrong: it states a **release-cut fact in the present tense**, which reads at `HEAD` as a standing invariant about a version the package left ten patches ago.

The board already anticipates this cycle. `KANBAN.md` records spec-012 among "five archived stubs [that] still carry the boilerplate 'expand it into the full builder-format spec' preamble the release falsified", each awaiting "its own residual-completion cycle of the spec-007 / spec-011 shape — no card of its own".

## Worker-0 verification pass (performed before any dispatch)

`docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching`. Every finding below was read against `HEAD` (`5851bb59`) before this plan was written; each cites its symbol-qualified path (`AGENTS.md` rule 27) or its commit. A finding is dispatched only if it holds.

### What the card actually did — recovered from history, because the stub does not say

The card's own commit is **`231911a8`** ("Release 0.0.4;", 2026-05-08), and it touched exactly **two** files: `CHANGELOG.md` and `KANBAN.md`. It performed one substantive edit — the changelog condensation:

| Edit | Before (`1d9ca597`, 2026-05-07) | After (`231911a8`, 2026-05-08) |
|---|---|---|
| release date | `## [0.0.4] - 2026-05-07` | `## [0.0.4] - 2026-05-08` |
| `[Unreleased]` | carried one `### Changed` bullet (docs consolidation) | emptied; the bullet folded into `0.0.4`'s `### Changed` as "User-facing docs were consolidated into code-first onboarding…" |
| `### Added` | 6 bullets | 5, condensed (two API bullets merged; the fakeshop restructure added) |
| `### Changed` | 4 bullets | 6, condensed and widened (optimizer-internals and test-expansion rows added) |
| `### Fixed` | absent | 4 bullets, one of which is the `GenericForeignKey` `ConfigurationError` row **reclassified out of `### Changed`** |
| `### Removed` | 1 bullet | unchanged |

**The four non-changelog surfaces the stub names were already on `0.0.4` before this card ran.** They landed a day earlier in `118f71a1` ("Complete spec-foundation.md - Slices 7-12 (v0.0.4)"), the commit that also carries card `DONE-010-0.0.4`'s and `DONE-011-0.0.4`'s work — its own message says "Updated version in `pyproject.toml`, `uv.lock`, and test assertions to 0.0.4."

This does not make the stub's `## Scope` bullet 1 false. It states an **end state at the release cut**, and that end state is verified below. It does make the stub's five-file list a board *prediction* rather than a record of the card's diff, which is F7.

### V1-V5: nothing was skipped in the code — verified, not assumed

| # | Claim to verify | At the stated point | Evidence |
|---|---|---|---|
| V1 | all five surfaces agreed on `0.0.4` at the release cut | agreed | at `231911a8`: `pyproject.toml:4` `version = "0.0.4"`; `django_strawberry_framework/__init__.py:14` `__version__ = "0.0.4"`; `tests/base/test_init.py:7` `assert __version__ == "0.0.4"`; `uv.lock` `name = "django-strawberry-framework"` / `version = "0.0.4"`; `CHANGELOG.md` `## [0.0.4] - 2026-05-08` |
| V2 | the same five-surface invariant holds at `HEAD`, on the current release | holds on `0.0.14` | `pyproject.toml:4`; `django_strawberry_framework/__init__.py:58`; `uv.lock:544`; `tests/base/test_init.py::test_version`; `CHANGELOG.md` `## [0.0.14] - 2026-07-20` |
| V3 | the `0.0.4` changelog entry the card shipped survives at `HEAD` | survives **byte-identical** | the `## [0.0.4]`-to-`## [0.0.3]` block extracted from `git show 231911a8:CHANGELOG.md` and from the working tree `diff`s clean. No later commit rewrote it |
| V4 | the condensation lost no substantive claim | lost none | the one bullet that changed section — `GenericForeignKey` raising `ConfigurationError` — survives in `### Fixed` with its consumer guidance ("with guidance to exclude or override the field"). The `[Unreleased]` bullet was folded in, not dropped |
| V5 | `AGENTS.md` rule 31's pyproject ↔ `__init__` pairing is mechanically enforced | **not enforced** | `tests/base/test_init.py::test_version` pins a **literal** (`assert __version__ == "0.0.14"`); nothing reads `pyproject.toml` to compare. A `grep -rn pyproject tests/` finds only `tests/test_bug_hunt.py` fixtures. A bump that edits one file and not the other is caught only if the literal is also edited |

**No code defect was found. No source or test file is in any item's writable set, so no Worker 2 pass is dispatched** — which is the disposition the maintainer's dispatch instruction anticipated.

**V5 is a gap, not a spec-012 defect.** The stub promised agreement at one release, and got it. A standing mechanical check is scope the card never claimed, and inventing it here would be this cycle widening a shipped card. It goes to the deferred-work catalog, framed as what it is: the invariant `AGENTS.md` rule 31 states in prose has no executable pin, and this card is the closest thing the board has to an owner for that.

### R1 findings — the spec's own text

Each is a stub-shaped defect or a claim later work falsified. None is a code defect.

| # | Finding | Evidence |
|---|---|---|
| F1 | No rationale companion exists. `docs/builder/BUILD.md` `## Spec rationale extraction` makes it the first substantive action of a build; specs 001-011 all have one. | `ls docs/SPECS/appx/spec-012-*` returns only the terms CSV |
| F2 | The preamble paragraph ("This file is intentionally lightweight… Before implementation work starts from this file, expand it into the full builder-format spec") is deliberation about the file, and its instruction is **counterfactual** at `HEAD`: implementation shipped ten patch versions ago and no expansion preceded it. | spec-012 line 7; the argument against re-litigating expand-it / delete-it is already made in `docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md` and cross-referenced, not repeated |
| F3 | `## Planning note` carries the single word `shipped` — a raw Kanban `planning_note` column render, not contract. | spec-012 lines 18-20 |
| F4 | `## Other` is an undifferentiated dump of six heterogeneous Kanban rows — two `#### Note` bullets and the five `#### Files likely touched` paths — under a heading that names none of them. | spec-012 lines 27-35 |
| F5 | `## Card snapshot` restates board fields that belong to the Kanban DB, **and drifts from them**: it lists Labels `release`, `versioning` where the card carries `internal`, `release`, `versioning`. A restatement that is also wrong is the argument against restating. | spec-012 lines 9-16 vs. `KANBAN.md` `### [DONE-012-0.0.4 …]` `- Labels:` |
| F6 | `## Scope` bullet 1 — "Package metadata … now agree on `0.0.4`" — is a **release-cut fact written in the present tense**. At `HEAD` the five surfaces agree on `0.0.14`, so the sentence reads as a standing invariant that is false. The fact itself is true and verified (V1); only the tense outlived it. | V1 / V2 above |
| F7 | `## Other`'s five-file list is the board's `#### Files likely touched` **prediction**, and the card's own diff touched two of the five (`CHANGELOG.md`, `KANBAN.md`). Rendered into a spec without that framing it reads as a record of what the card changed. | `git show --stat 231911a8` |
| F8 | The `[backlog]` link definition is unused (one occurrence in the file — the definition itself). | `grep -c '\[backlog\]'` -> 1 |

**F8 is recorded, not dispatched.** The board already owns it: `KANBAN.md` catalogues 71 unused link definitions across 23 files, "including an unused `[backlog]` definition in eight archived specs (`spec-011`, `spec-012`, `spec-013`, `spec-016`, `spec-024`, `spec-026`, `spec-036`, `spec-054`)", to be retired in one sweep by the checker card. `worker-0.md` `## Closing out a kanban card` forbids partial-fixing a pattern that spans surfaces. It goes to the deferred-work catalog.

### R2 findings — documentation completion and archive audit

| # | Finding | Evidence |
|---|---|---|
| F9 | **The release policy the card cut `0.0.4` under was rewritten a week later, and the spec's subject sits inside it.** At `231911a8` `CHANGELOG.md`'s header read "and this project adheres to [Semantic Versioning]". `27ed0b30` (2026-05-15) **deleted that line** and added the `## Versioning` milestone-cadence section, whose alpha row states that strict SemVer "does **not** apply" during `0.0.x`. A spec whose whole subject is release alignment must not leave a reader to infer which policy `0.0.4` was cut under. This is rationale material, not spec material — the spec states the aligned surfaces, the rationale records the policy change. | `git show 27ed0b30 -- CHANGELOG.md`; `CHANGELOG.md` `## Versioning` at `HEAD` |
| F10 | The spec is already at `docs/SPECS/` and every link definition resolves at that depth (`../../KANBAN.md`, `../GLOSSARY.md#djangotype`), and the file is already reference-style with all ten canonical group headers. **The archive move itself is therefore done**; what R2 owes is the audit and the new companion's own link hygiene. | path check; `uv run python scripts/check_spec_glossary.py --spec …` -> `OK: 1 terms` |
| F11 | The card's one glossary anchor resolves and carries the right shipped version: `#djangotype`. `KANBAN.md`'s `DONE-012-0.0.4` card renders it as shipped (`0.0.5`). The terms CSV is one row, one anchor — importable by `import_spec_terms` (`worker-0.md` `### DONE-card invariants`). | `docs/SPECS/appx/spec-012-…-terms.csv`; `KANBAN.md` `#### Glossary terms` |
| F12 | **No `[spec-012]` ref-id ambiguity exists.** Unlike the `[spec-011]` cluster the prior cycle catalogued, no file in the repository defines a `[spec-012]` ref-id at all, and every prose mention of `spec-012` (`KANBAN.md` lines 340-341, the spec-011 rationale, `bld-011-final.md`, `build-007…md`) means this card. Nothing to fix and nothing to defer. | `grep -rn '^\[spec-012\]:' .` -> 0 hits; the mention set enumerated |

**F9 is the cycle's substantive finding** and the reason R2 is not merely an audit: it is the "later work changed the shape" case the maintainer's dispatch names, and the change is to the policy frame rather than to any of the five surfaces — which is exactly the kind of change a spec silently outlives.

## Baseline-dirty out-of-scope files

`HEAD` at plan time: `5851bb5903e8edddeae4c7335529c37db775c212`. `git status --porcelain | wc -l` -> **93**, and **not one of them is this cycle's**. Every path belongs to a concurrent maintainer session (`START.md` `## Concurrent sessions`, `AGENTS.md` rule 34). **No worker edits, reverts, stages, or `git checkout`s any of them.** In particular:

- `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` and `docs/SPECS/appx/spec-009-…-rationale.md` are **modified right now** by a concurrent residual-completion cycle (`docs/builder/build-009-…md` and `docs/builder/bld-009-r1-…md`, both untracked). No worker of this cycle opens either for writing, and reads them only as shape precedent, never as authority on a moving claim.
- **`docs/GLOSSARY.md` is modified** while `examples/fakeshop/db.sqlite3` is **clean**. That combination means the committed generated file and the DB it renders from are out of step in a way this cycle did not cause and must not resolve: **no worker of this cycle runs `scripts/build_glossary_md.py`.** A regenerate would either publish unlanded DB state or clobber the concurrent session's edit.
- `docs/builder/bld-011-r1/r2/r3-*.md` are **staged deletions** (`D ` in the index) from the concurrent session's cleanup of the prior cycle. Left exactly as found.
- 20-odd modified package sources and a comparable number of modified tests belong to an in-flight `0.0.14` review cycle, along with its `docs/review/` scratchpads. `AGENTS.md` rule 22 forbids touching `docs/review/` regardless.

**The list is moving.** Any pass that needs the baseline re-derives it rather than quoting this section.

**Clean at `HEAD`, and therefore safe if an item turns out to need them:** `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `CHANGELOG.md`, `pyproject.toml`, `django_strawberry_framework/__init__.py`, `uv.lock`, `tests/base/test_init.py`, and both spec-012 companions.

## Pre-flight deviations, recorded

Two steps of `worker-0.md` `## Pre-flight procedure` did not run as written; both deviations protect concurrent sessions.

- **Step 3 (artifact reset).** **Nothing was deleted.** `docs/builder/build-009-…md`, `bld-009-r1-…md` are a concurrent session's live plan and artifact, and `build-010-…`, `build-011-…`, `bld-010-*`, `bld-011-*`, `bld-003-final.md` are committed records of closed cycles. Deleting a prior cycle's record is the one irreversible pre-flight mistake that step names; deleting a live concurrent plan would be worse. What the step protects — that this cycle overwrites no existing path — was verified directly: every path in `## Artifact list` was confirmed absent, as was the rationale companion.
- **Step 5 (scratch directories cleared).** **Nothing was cleared.** `docs/builder/worker-memory/` holds a concurrent session's `spec-009-worker-1.md` / `spec-009-worker-3.md` alongside four un-namespaced files, and `docs/shadow/` is that session's review substrate. Clearing either would destroy live work. This cycle instead uses **namespaced** memory files — `docs/builder/worker-memory/spec-012-worker-0.md` and `…/spec-012-worker-1.md` — following the `spec-009-worker-1.md` precedent the concurrent session set. No worker of this cycle reads or writes any other file in that directory.

Steps 1, 2, 4, 6 ran: the baseline is enumerated above and included per the maintainer's knowing dispatch onto this tree; `scripts/review_inspect.py` smoke-invoked OK against `django_strawberry_framework/conf.py`; `.gitignore` carries all three scratch paths (lines 174, 188, 192); `check_spec_glossary --spec docs/SPECS/spec-012-…md` exits 0. Step 7 (rationale extraction) is item R1.

## Artifact list

- `docs/builder/bld-012-r1-rationale_and_spec_reconciliation.md`
- `docs/builder/bld-012-r2-doc_completion_archive_audit.md`
- `docs/builder/bld-012-final.md`

**No `bld-integration.md`.** `docs/builder/BUILD.md` `## Cross-slice integration pass` scans landed source for cross-slice duplication; this cycle lands no source at all, so there is no cross-slice DRY surface. Both of the pass's live obligations are folded into the final gate and recorded there: the staged-anchor sweep, and the read of every closed artifact. Same disposition, and the same reason, as the spec-003, spec-010, and spec-011 cycles.

## Checklist

- [x] R1: create the rationale companion and reconcile the spec against `HEAD` (F1-F8) -> `docs/builder/bld-012-r1-rationale_and_spec_reconciliation.md`
- [x] R2: documentation completion and archive audit (F9-F12) -> `docs/builder/bld-012-r2-doc_completion_archive_audit.md`
- [x] Final test-run gate -> `docs/builder/bld-012-final.md`

**The gate carries one escalation, not a clean sweep.** `uv run pytest --no-cov` reported `1 failed, 5776 passed, 40 skipped`: `tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol`. It is **not this cycle's** — this cycle's whole diff is five Markdown paths, and both the failing test and `django_strawberry_framework/rest_framework/inputs.py` are byte-identical to `HEAD` (`git status --porcelain` over `tests/rest_framework/` and `django_strawberry_framework/rest_framework/inputs.py` is empty). It was introduced **committed** by the concurrent DRY-consolidation commit `5851bb59` and fails deterministically in isolation. Worker 0 root-caused it rather than merely flagging it: the test's own fixture `tests/rest_framework/test_inputs.py #"def _item_serializer"` defines `ItemSer` **inside the function**, so each call returns a distinct class object; `shape_a.serializer_class != shape_b.serializer_class` by construction and `assert shape_a == shape_b` cannot pass as written. The production cache protocol under test is not implicated. Escalated to the maintainer: the file belongs to a concurrent session's in-flight cycle and is outside every cohort's declared ownership here, so no worker of this cycle edits it.

## Corrections to this plan, recorded

`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` — a stated count reads as measured and propagates silently, so a figure that does not reproduce is corrected here rather than left standing.

- **F4's "six heterogeneous Kanban rows" is wrong; `## Other` carried seven.** R1 re-derived it. The error is arithmetic inside this plan rather than drift in the file: F4's own parenthetical ("two `#### Note` bullets and the five `#### Files likely touched` paths") sums to seven. The finding's substance and disposition are unchanged — an undifferentiated dump under a heading that names none of its rows, deleted outright by R1.
- **F5's label drift is a dimension rebuild, not a simple addition** — a nuance R1 verified from the blobs rather than inheriting from the spec-011 rationale's attribution. `KANBAN.md` rendered **no** `- Labels:` line for card 12 at all from `91f9db12` (2026-06-04) through `c8f03087` (2026-06-09), returning rebuilt with `internal` at `2baf93b5`. Same conclusion as F5 states, on stronger evidence.
- **F12's wording is wrong, though its substance holds.** "No file defines a `[spec-012]` ref-id at all" was true when this plan was written and false when R2 measured it — **four** are defined, and R1 wrote all four. The finding's point survives and is now *provable* rather than merely observed: `git log --all --diff-filter=A -- '*spec-012*'` shows the number never named any other file, so there is no `[spec-011]`-shaped ambiguity cluster here and nothing to defer. The correct statement is "every `[spec-012]` definition resolves to this card", not "none exists".
- **F9 was under-stated.** R2 established the sharper point: every edit to `CHANGELOG.md`'s policy frame — `27ed0b30`'s `## Versioning` addition and the three later revisions of it (`2bd7cb84`'s row relabelling, `24d11143`'s removal of `## [Unreleased]`) — sits **above** the release entries, so the `0.0.4` block stays byte-identical and the spec's "no later commit rewrites it" guarantee is true **and blind to the policy change**. That blindness is the argument for the rationale entry, and this plan did not state it.
- **`HEAD` moved mid-cycle**, from `5851bb59` to `c2b8622d` (concurrent session), which **landed** the `docs/builder/bld-011-r*.md` deletions this plan recorded as staged. R2 re-measured every figure at `c2b8622d`; the baseline section's caution that "the list is moving" held.
- **V5 over-stated the gap, and `docs/builder/bld-012-final.md`'s catalog inherited the over-statement.** Both say the pairing has no executable comparison at all. One exists: `scripts/bug_hunt.py::_package_release` reads `pyproject.toml` `[project].version` and `django_strawberry_framework/__init__.py` `__version__` and raises `#"bump them together"` when they differ — wording that mirrors `AGENTS.md` rule 31 itself. V5's evidence column is what produced the error: it grepped `pyproject` over `tests/` only, read the hits as fixtures, and never grepped `scripts/`. The **disposition is unchanged and the corrected claim is narrower**: the comparison is not a gate. It is absent from `.github/workflows/` and `.pre-commit-config.yaml`; `scripts/bug_hunt.py::main` reaches it only when `--target-release` is omitted, a bypass `tests/test_bug_hunt.py::test_target_release_overrides_mismatched_package_versions` pins as deliberate; and both of its tests build synthetic `tmp_path` trees, so the suite has never compared this repository's own two files. Carried onto `TODO-ALPHA-052-0.1.0` in the corrected form, with the over-statement named there so a later reader does not re-derive it from the sealed artifact. Instance of the rule this cycle's own R2 carry-forward states: a finding written as an absence is only as good as the population it was measured over.
- Twelve of the thirteen figures in `## Worker-0 verification pass` reproduced exactly when R1 measured them: V1-V5, the byte-identical `0.0.4` changelog block (2,621 bytes), `231911a8`'s two-file diff, the `118f71a1` pre-alignment, the 5/6/4/1 changelog-group counts, the label drift, and the 1,651-byte spec size.

## Dispatch record

| Item | Passes dispatched | Why |
|---|---|---|
| R1 | Worker 1 only | The maintainer's standing instruction for this cycle: an item that changes only the spec and its rationale is Worker 1's alone, and both files are Worker 1-owned by `docs/builder/BUILD.md` `## Spec reconciliation` in any case. |
| R2 | Worker 1 only unless it turns up a durable-doc or DB edit | Its findings are inside the spec and its companions. If the pass finds a `KANBAN.md` card-body or kanban-DB edit is owed, it **stops and reports** and Worker 0 re-partitions with a Worker 2 pass, because `KANBAN.md` / `KANBAN.html` are generated from `examples/fakeshop/db.sqlite3` and are never hand-edited. `docs/GLOSSARY.md` is off-limits to this cycle either way (see the baseline section). |
| Final | Worker 1 only | `worker-1.md` `## Final test-run gate` gives the whole gate to Worker 1. |
| (none) | Worker 2 / Worker 3 | The verification pass found no code defect and no code item to build. `### Isolation is non-waivable` binds a pass that writes code; this cycle writes none. |
| Deferred-work re-homing | Worker 0, after the final gate | On maintainer instruction, and it is board bookkeeping rather than a build item: two `CardItem` rows on `TODO-ALPHA-052-0.1.0`, written through the Django ORM against `examples/fakeshop/db.sqlite3` and re-rendered with `scripts/build_kanban_md.py` + `scripts/build_kanban_html.py`. (a) The five-stub bullet drops to **four** — this cycle moved `spec-012`'s boilerplate preamble into its rationale, so `spec-013` / `spec-016` / `spec-024` / `spec-026` are what remain; the bullet now names the discharge so a sweep measures four rather than re-deriving five. (b) A new bullet carries V5 in its corrected form. Card 052 is the owner three ways: its definition-of-done already holds the hand-run version-quintet box, its predicted files are exactly `django_strawberry_framework/__init__.py` and `tests/base/test_init.py`, and it already hosts the doc-tooling and checker family. `TODO-ALPHA-051-0.0.15` owns the chronologically nearer `0.0.15` quintet but its scope is a closed pre-audited DRY list. **No other catalog item moved**: F8 is already named on 052's unused-link-definition bullet, F9's onward reader problem sits under 052's CHANGELOG promotion, F12 is recorded-not-deferred, and the failing `tests/rest_framework/test_inputs.py` row belongs to the concurrent cycle that committed it. |

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
